import { FACT_COLUMNS, FACT_KIND } from "@/content/facts";
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
}

type Column = readonly [name: string, value: string | undefined];

const pounds = (value: string | undefined) => (value === undefined ? undefined : `£${value}`);

/**
 * The columns of a fact, left to right, chosen by its template. Each value
 * is a slot of the fact as the API formatted it. A column whose slot the
 * fact does not hold is left out: nothing is filled in.
 */
export function columnsOf(fact: Fact): readonly Column[] {
  const { slots } = fact;
  const columns = ((): readonly Column[] => {
    switch (fact.template) {
      case "feature":
      case "feature_crime":
        return [
          [FACT_COLUMNS.value, slots.value],
          [FACT_COLUMNS.standing, slots.standing],
        ];
      case "tag":
        return [[FACT_COLUMNS.standing, slots.standing]];
      case "cost_rent":
      case "cost_buy":
        return [
          [FACT_COLUMNS.segment, slots.segment],
          [
            FACT_COLUMNS.range,
            slots.lower !== undefined && slots.upper !== undefined
              ? `${pounds(slots.lower)} ${FACT_COLUMNS.to} ${pounds(slots.upper)}`
              : undefined,
          ],
          [FACT_COLUMNS.median, pounds(slots.median)],
          [FACT_COLUMNS.asOf, slots.as_of],
          [FACT_COLUMNS.confidence, slots.confidence],
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
      case "travel_pt":
        return [
          [FACT_COLUMNS.place, slots.place],
          [FACT_COLUMNS.mode, slots.mode],
          [FACT_COLUMNS.typical, slots.typical],
          [FACT_COLUMNS.missed, slots.missed],
        ];
      case "travel_other":
        return [
          [FACT_COLUMNS.place, slots.place],
          [FACT_COLUMNS.mode, slots.mode],
          [FACT_COLUMNS.minutes, slots.minutes],
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
    }
  })();
  return columns.filter(([, value]) => value !== undefined && value !== "");
}

/**
 * One fact with no sentence of its own, laid out in fixed columns. The row
 * is named by the fact's own label, and ends in its source and date.
 */
export function FactRow({ fact, withSource = true, source = "button", name: given }: Props) {
  // Which station is the nearest is said by the template, and by nothing else in the fact.
  const ofAStation = fact.template === "station" || fact.template === "station_nearby";
  const name =
    given ?? (ofAStation ? FACT_KIND[fact.template] : fact.label || FACT_KIND[fact.template]);
  return (
    <div className={styles.row} role="group" aria-label={name}>
      <p className={styles.name}>{name}</p>
      <dl className={styles.columns}>
        {columnsOf(fact)
          // A column that only repeats the row's name is left out: it says nothing new.
          .filter(([, value]) => value !== name)
          .map(([column, value]) => (
            <div key={column}>
              <dt>{column}</dt>
              <dd>{value}</dd>
            </div>
          ))}
      </dl>
      {fact.template === "feature_crime" ? <p className={styles.caveat}>{CRIME_CAVEAT}</p> : null}
      {!withSource ? null : source === "line" ? (
        <SourceLine facts={[fact]} />
      ) : (
        <SourceNote facts={[fact]} of={name} />
      )}
    </div>
  );
}
