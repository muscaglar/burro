import Link from "next/link";

import { CANNOT_PLACE, FACT_COLUMNS, FACT_KIND, ONE_NUMBER } from "@/content/facts";
import { CRIME_CAVEAT } from "@/content/settings";
import type { Fact } from "@/lib/api/schema";

import { SourceLine } from "../SourceLine/SourceLine";
import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./FactRow.module.css";

interface Props {
  readonly fact: Fact;
  /** False where the row's source is given by what holds it. */
  readonly withSource?: boolean;
  /**
   * How the source is given. `button` opens it in place, and needs scripts.
   * `line` writes it out under the row, for a page that must read without them.
   */
  readonly source?: "button" | "line";
  /** A name for the row where the fact's own label is not the one wanted. */
  readonly name?: string;
  /** Where the name leads, where the row is of something that has a page of its own. */
  readonly href?: string;
  /**
   * What is said of the fact before its own columns, where the row stands for more than
   * the fact: a part of a recipe says its share first.
   */
  readonly lead?: readonly Column[];
}

export type Column = readonly [name: string, value: string | undefined];

const pounds = (value: string | undefined) => (value === undefined ? undefined : `£${value}`);

/** From one slot to another: a range, where the fact holds both its ends. */
const range = (from: string | undefined, to: string | undefined) =>
  from === undefined || to === undefined ? undefined : `${from} ${FACT_COLUMNS.to} ${to}`;

/** Where a journey stands against the limit the person set, where the fact holds one. */
const againstTheLimit = ({ template, slots }: Fact): readonly Column[] => [
  [FACT_COLUMNS.limit, slots.limit],
  [
    template === "travel_pt_over" || template === "travel_other_over"
      ? FACT_COLUMNS.overLimit
      : FACT_COLUMNS.underLimit,
    slots.margin,
  ],
];

/**
 * How many parts of its recipe a band rests on, where that is not all of them. A band
 * worked out from part of a recipe is not shown as any other: the fact says how many
 * parts have a figure, and the row says it after the band. Both counts are the API's.
 */
const restsOnPart = ({ slots }: Fact): readonly Column[] =>
  slots.known === undefined || slots.parts === undefined || slots.known === slots.parts
    ? []
    : [
        [FACT_COLUMNS.partsKnown, slots.known],
        [FACT_COLUMNS.parts, slots.parts],
        // What those parts carry of the recipe, where the fact says it. It is never added up here.
        [FACT_COLUMNS.share, slots.share],
      ];

/**
 * The columns of a fact, left to right, chosen by its template. Each value
 * is a slot of the fact as the API formatted it. A column whose slot the
 * fact does not hold is left out: nothing is filled in.
 */
export function columnsOf(fact: Fact): readonly Column[] {
  const { slots } = fact;
  // A newer API may send a template the website was not built with. It has no columns here.
  const columns = ((): readonly Column[] | undefined => {
    switch (fact.template) {
      case "feature":
      case "feature_crime":
        return [
          [FACT_COLUMNS.value, slots.value],
          [FACT_COLUMNS.standing, slots.standing],
        ];
      case "vibe":
        return [
          [FACT_COLUMNS.band, slots.band],
          [FACT_COLUMNS.ends, range(slots.low_end, slots.high_end)],
          [FACT_COLUMNS.compared, slots.compared],
          [FACT_COLUMNS.partsDated, slots.span],
          ...restsOnPart(fact),
        ];
      case "vibe_range":
        return [
          [FACT_COLUMNS.bands, range(slots.spread_low, slots.spread_high)],
          [FACT_COLUMNS.ends, range(slots.low_end, slots.high_end)],
          [FACT_COLUMNS.partsDated, slots.span],
          ...restsOnPart(fact),
        ];
      case "vibe_unknown":
        return [
          [FACT_COLUMNS.partsKnown, slots.known],
          [FACT_COLUMNS.parts, slots.parts],
        ];
      case "cost_rent":
      case "cost_buy":
        return [
          [FACT_COLUMNS.segment, slots.segment],
          [
            FACT_COLUMNS.range,
            range(pounds(slots.lower), pounds(slots.upper)),
          ],
          [FACT_COLUMNS.median, pounds(slots.median)],
          [FACT_COLUMNS.asOf, slots.as_of],
          [FACT_COLUMNS.confidence, slots.confidence],
        ];
      case "cost_buy_median":
        // One number, as a publisher gives it. No range stands beside it, and no word for
        // how sure it is: the row says under its columns what is not known of it.
        return [
          [FACT_COLUMNS.segment, slots.segment],
          [FACT_COLUMNS.middleOfAll, pounds(slots.median)],
          [FACT_COLUMNS.soldIn, slots.period],
        ];
      case "budget_under":
      case "budget_over":
        return [
          [FACT_COLUMNS.upper, pounds(slots.upper)],
          [FACT_COLUMNS.amount, pounds(slots.amount)],
          [
            fact.template === "budget_under" ? FACT_COLUMNS.under : FACT_COLUMNS.over,
            pounds(slots.margin),
          ],
        ];
      case "budget_under_median":
      case "budget_over_median":
        // The budget is held against the one number there is, and the row names it.
        return [
          [FACT_COLUMNS.middleOfAll, pounds(slots.median)],
          [FACT_COLUMNS.amount, pounds(slots.amount)],
          [
            fact.template === "budget_under_median" ? FACT_COLUMNS.under : FACT_COLUMNS.over,
            pounds(slots.margin),
          ],
        ];
      case "travel_pt":
      case "travel_pt_over":
        return [
          [FACT_COLUMNS.place, slots.place],
          [FACT_COLUMNS.mode, slots.mode],
          [FACT_COLUMNS.typical, slots.typical],
          [FACT_COLUMNS.missed, slots.missed],
          ...againstTheLimit(fact),
        ];
      case "travel_other":
      case "travel_other_over":
        return [
          [FACT_COLUMNS.place, slots.place],
          [FACT_COLUMNS.mode, slots.mode],
          [FACT_COLUMNS.minutes, slots.minutes],
          ...againstTheLimit(fact),
        ];
      case "travel_beyond":
        return [
          [FACT_COLUMNS.place, slots.place],
          [FACT_COLUMNS.mode, slots.mode],
          [FACT_COLUMNS.moreThan, slots.cutoff],
        ];
      case "station":
      case "station_nearby":
        return [
          [FACT_COLUMNS.station, slots.name],
          [FACT_COLUMNS.walk, slots.walk],
          [FACT_COLUMNS.lines, slots.lines],
        ];
      case "area":
      case "missing":
        return [
          [FACT_COLUMNS.name, slots.name],
          [FACT_COLUMNS.borough, slots.borough],
        ];
      case "missing_journey":
        return [
          [FACT_COLUMNS.name, slots.name],
          [FACT_COLUMNS.place, slots.place],
        ];
      case "likeness":
      case "likeness_same":
        return [
          [FACT_COLUMNS.other, slots.other],
          // Where two areas differ in nothing, every measure compared is in the same band.
          [FACT_COLUMNS.same, slots.same ?? slots.measures],
          [FACT_COLUMNS.measures, slots.measures],
          [FACT_COLUMNS.leastAlike, slots.family],
        ];
    }
  })();
  return (columns ?? []).filter(([, value]) => value !== undefined && value !== "");
}

/**
 * One fact with no sentence of its own, laid out in fixed columns. The row
 * is named by the fact's own label, and ends in its source and date.
 */
export function FactRow({ fact, withSource = true, source = "button", name: given, href, lead = [] }: Props) {
  // Which station is the nearest is said by the template, and by nothing else in the fact.
  const ofAStation = fact.template === "station" || fact.template === "station_nearby";
  const name =
    given ?? (ofAStation ? FACT_KIND[fact.template] : fact.label || FACT_KIND[fact.template]);
  return (
    <div className={styles.row} role="group" aria-label={name}>
      <p className={styles.name}>
        {href === undefined ? (
          name
        ) : (
          // Which page a person reads next is told to no server ahead of time.
          <Link className="target-min" href={href} prefetch={false}>
            {name}
          </Link>
        )}
      </p>
      <dl className={styles.columns}>
        {[...lead, ...columnsOf(fact)]
          // A column that only repeats the row's name is left out: it says nothing new.
          .filter(([, value]) => value !== undefined && value !== name)
          .map(([column, value]) => (
            <div key={column}>
              <dt>{column}</dt>
              <dd>{value}</dd>
            </div>
          ))}
      </dl>
      {fact.template === "feature_crime" ? <p className={styles.caveat}>{CRIME_CAVEAT}</p> : null}
      {fact.template === "vibe_unknown" ? <p className={styles.caveat}>{CANNOT_PLACE}</p> : null}
      {fact.template === "cost_buy_median" ? <p className={styles.caveat}>{ONE_NUMBER}</p> : null}
      {/* What every sentence about a vibe ends in, as the API holds it: that the recipe is a judgement. */}
      {fact.kind === "tag" && fact.slots.judgement ? (
        <p className={styles.caveat}>{fact.slots.judgement}</p>
      ) : null}
      {!withSource ? null : source === "line" ? (
        <SourceLine facts={[fact]} />
      ) : (
        // The row says above that the recipe is a judgement, so its source does not say it again.
        <SourceNote facts={[fact]} of={name} judgementSaid />
      )}
    </div>
  );
}
