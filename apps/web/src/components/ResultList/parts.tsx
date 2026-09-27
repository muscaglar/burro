"use client";

import Link from "next/link";

import { CARD } from "@/content/card";
import { MODE } from "@/content/labels";
import { BREAKDOWN, COMPLETENESS, JOURNEYS, UNTESTED } from "@/content/search";
import type {
  Combine,
  Commute,
  CommuteLeg,
  Contribution,
  Cutoffs,
  ExplainedSentence,
  Fact,
  JourneyBand,
  MetaData,
  PreferenceSpec,
  RankedArea,
} from "@/lib/api/schema";
import { outOfHundred } from "@/lib/format";
import { paths } from "@/lib/paths";
import {
  completenessOf,
  drivingLeg,
  estimateOf,
  factsForJourney,
  hundredths,
  journeysLeftOut,
  labelOf,
  withinLimit,
  type Facts,
} from "@/lib/search/card";

import { Disclosure } from "../Disclosure/Disclosure";
import { columnsOf } from "../FactRow/FactRow";
import { Approx } from "../kit/Approx/Approx";
import type { ThingOf } from "../kit/Thing/drawn";
import { factsCited, Sentence } from "../Sentence/Sentence";
import { Skeleton } from "../Skeleton/Skeleton";
import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./ResultList.module.css";

/** A thing that was asked for and is no vibe, which the area has no figure for. */
export interface Lacked {
  /** The name of the thing, as the page names it everywhere. */
  readonly name: string;
  /** What is drawn for it. */
  readonly thing: ThingOf;
}

/**
 * What a cell is of, for the eye. On a narrow screen a table's rows are
 * stacked and the headings of its columns are not drawn, so each cell says
 * its own. The heading says it to a screen reader, so this is kept from one.
 *
 * Every part of a table that is stacked says its role again: the table, its
 * two groups of rows, each row and each cell. The roles are their own, and
 * the lint rules that call one redundant, or out of place on a cell, are
 * switched off where it is said. A browser may forget that a table is one
 * when it is laid out as blocks, and is told again.
 */
function CellLabel({ children }: { readonly children: string }) {
  return (
    <span className={styles.cellLabel} aria-hidden="true">
      {children}
    </span>
  );
}

/**
 * What an area has no figure for, by the names the chips give: what the person asked for,
 * and then the settings nobody chose. A vibe is always asked for. A thing the page has no
 * name for is left out.
 *
 * A journey and a budget are among them only where no sentence of their own says so:
 * each is the name of no thing a person asks for, and "You asked for Budget" stood
 * directly over the sentence that said of the budget all there was to say.
 */
export function lackedBy(
  area: Pick<RankedArea, "contributions" | "legs">,
  meta: Pick<MetaData, "features" | "tags">,
  spec: Pick<PreferenceSpec, "weights">,
): { readonly asked: readonly string[]; readonly usual: readonly string[] } {
  const asked: string[] = [];
  const usual: string[] = [];
  for (const { component, present } of area.contributions) {
    if (present || component === "budget") continue;
    if (component === "commute" && journeysLeftOut(area) !== null) continue;
    const [kind, id] = component.split(":", 2);
    const name =
      component === "commute"
        ? BREAKDOWN.journey
        : kind === "feature"
          ? meta.features.find((one) => one.feature_id === id)?.short_label
          : meta.tags.find((one) => one.tag_id === id)?.label;
    if (name === undefined) continue;
    const byDefault =
      kind === "feature" &&
      spec.weights.find((weight) => weight.feature_id === id)?.provenance === "default";
    (byDefault ? usual : asked).push(name);
  }
  return { asked, usual };
}

/**
 * How many of the things that count for an area are usual settings, which nobody chose. A
 * vibe, a journey and a budget are always asked for.
 */
export function usualAmong(area: Pick<RankedArea, "contributions">, spec: Pick<PreferenceSpec, "weights">): number {
  return area.contributions.filter(({ component }) => {
    const [kind, id] = component.split(":", 2);
    return kind === "feature" && spec.weights.find((weight) => weight.feature_id === id)?.provenance === "default";
  }).length;
}

/**
 * What was asked for that an area has no figure for, as a result draws it: the vibes, by
 * the ids the API gives them, and whatever else, each by its name and with what is drawn
 * for it. What nobody chose is not among them. A thing the page has no name for is left out.
 *
 * What is drawn for a measurement is chosen by the family the API puts it in, and for a
 * journey and a budget by what they are. No name of a thing is written here.
 */
export function thingsLacked(
  area: Pick<RankedArea, "contributions">,
  meta: Pick<MetaData, "features" | "tags">,
  spec: Pick<PreferenceSpec, "weights">,
): { readonly vibes: readonly string[]; readonly others: readonly Lacked[] } {
  const vibes: string[] = [];
  const others: Lacked[] = [];
  for (const { component, present } of area.contributions) {
    if (present) continue;
    const [kind, id] = component.split(":", 2);
    if (component === "commute") others.push({ name: BREAKDOWN.journey, thing: { kind: "place" } });
    else if (component === "budget") others.push({ name: BREAKDOWN.budget, thing: { kind: "budget" } });
    else if (kind === "tag" && id !== undefined && meta.tags.some((one) => one.tag_id === id)) vibes.push(id);
    else if (kind === "feature") {
      const feature = meta.features.find((one) => one.feature_id === id);
      const byDefault = spec.weights.find((weight) => weight.feature_id === id)?.provenance === "default";
      if (feature === undefined || byDefault) continue;
      others.push({ name: feature.short_label, thing: { kind: "feature", id: feature.feature_id, family: feature.family } });
    }
  }
  return { vibes, others };
}

/**
 * True where the fit of an area is not whole: it was worked out from some of what counts,
 * or its journeys count for nothing in it, or a firm limit could not be held against it. A
 * fit is never given alone where that is so.
 */
export function isNotWhole(area: Pick<RankedArea, "contributions" | "legs" | "untested_filters">): boolean {
  const { asked, complete } = completenessOf(area);
  if (asked === 0) return false;
  // A code the website has no word for is left out.
  const untested = area.untested_filters.filter((reason) => Boolean(UNTESTED[reason]));
  return !complete || journeysLeftOut(area) !== null || untested.length > 0;
}

interface CompletenessProps {
  readonly area: RankedArea;
  /**
   * The names the API gives what counts, and the spec that was ranked. With both in hand
   * the result names what the area has no figure for, where it has none for something.
   */
  readonly meta?: Pick<MetaData, "features" | "tags">;
  readonly spec?: Pick<PreferenceSpec, "weights">;
  /**
   * True where nothing is said of a fit that rests on everything that counts, which is
   * on every result. Where a fit rests on part of what counts, it is always said.
   */
  readonly quiet?: boolean;
}

/**
 * How much of what counts the area has a figure for, in words. Under it, each
 * firm limit that could not be held against the area: it is the one thing the
 * person called firm, and it was not applied.
 *
 * So is it said when the journeys count for nothing in the fit, because none
 * of them has a time: the person named the places, and the fit did not weigh
 * them.
 *
 * It says how far to trust the fit. On a result two words say that the fit is
 * not whole, beside the fit, and this says why, in the working: unless the
 * look has it said on the result itself, under the fit, as it was. Where the
 * fit is whole nothing is said of it: it was said on most results, and told a
 * person nothing to act on.
 *
 * Where the things that count are counted, it says how many of them nobody
 * chose: a person who asked for four things was told that ten count.
 */
export function Completeness({ area, quiet = true, meta, spec }: CompletenessProps) {
  const { asked, present, complete } = completenessOf(area);
  if (asked === 0) return null;
  const lacked = meta === undefined || spec === undefined ? null : lackedBy(area, meta, spec);
  const usual = spec === undefined ? 0 : usualAmong(area, spec);
  const leftOut = journeysLeftOut(area);
  // A code the website has no word for is left out.
  const untested = area.untested_filters.filter((reason) => Boolean(UNTESTED[reason]));
  // A firm budget that could not be checked says of itself that the area has no cost figure.
  const noCost = area.contributions.some((part) => part.component === "budget" && !part.present) && !untested.includes("over_budget");
  if (quiet && complete && leftOut === null && untested.length === 0) return null;
  return (
    <div className={styles.completeness}>
      {quiet && complete ? null : (
        <p className={styles.based}>
          <span>{complete ? COMPLETENESS.all : COMPLETENESS.some(present, asked)}</span>
          {usual > 0 ? <span> {COMPLETENESS.usual(usual)}</span> : null}
        </p>
      )}
      {/* What is dropped is said, and by name. What was asked for is said first, and
          heavier: the person asked for it, and the fit does not hold it. */}
      {lacked !== null && lacked.asked.length > 0 ? (
        <p className={styles.untested}>{COMPLETENESS.lacksAsked(lacked.asked)}</p>
      ) : null}
      {lacked !== null && lacked.usual.length > 0 ? (
        <p className={styles.based}>{COMPLETENESS.lacks(lacked.usual)}</p>
      ) : null}
      {leftOut !== null ? <p className={styles.untested}>{JOURNEYS.notCounted(leftOut)}</p> : null}
      {noCost ? <p className={styles.untested}>{CARD.noCost}</p> : null}
      {untested.map((reason) => (
        <p key={reason} className={styles.untested}>
          {UNTESTED[reason]}
        </p>
      ))}
    </div>
  );
}

interface MissingProps {
  readonly area: RankedArea;
  /** One sentence from the API for each thing that has no figure here. */
  readonly missing?: readonly ExplainedSentence[];
  /** True while the sentences are waited for. */
  readonly waiting: boolean;
  readonly facts: Facts;
  /**
   * The names the API gives what counts, and the spec that was ranked. With both in hand
   * the part says first what the fit is based on, where that is not everything: what two
   * words say on the result.
   */
  readonly meta?: Pick<MetaData, "features" | "tags">;
  readonly spec?: Pick<PreferenceSpec, "weights">;
}

/**
 * What the area has no figure for, in the working of a result. First what that
 * means for the fit, after the mark and the two words that stand beside the
 * fit on the result: how much of what counts the fit is based on, what it
 * leaves out, and each firm limit that could not be held against the area.
 * Then the API's sentence for each thing the area has no figure for, each with
 * its source. How many of those there will be is known from the ranking, so
 * their place is held while they are waited for.
 */
export function Missing({ area, missing = [], waiting, facts, meta, spec }: MissingProps) {
  const { asked, present } = completenessOf(area);
  const held = missing.length === 0 && waiting ? asked - present : 0;
  const ofTheFit = meta !== undefined && spec !== undefined && isNotWhole(area);
  if (missing.length === 0 && held === 0 && !ofTheFit) return null;
  return (
    <div className={styles.part}>
      <h4 className={styles.tag}>{COMPLETENESS.missingTitle}</h4>
      {ofTheFit ? (
        <>
          <p className={styles.marked}>
            <Approx />
          </p>
          <Completeness area={area} meta={meta} spec={spec} />
        </>
      ) : null}
      {held > 0 ? <Skeleton lines={held} /> : null}
      {missing.map((sentence) => (
        <Sentence
          key={sentence.fact_ids.join(" ")}
          sentence={sentence}
          facts={facts}
          // Named by what has no figure, so that no two "Source" buttons of a card are alike.
          of={factsCited(sentence, facts)[0]?.label}
        />
      ))}
    </div>
  );
}

/**
 * What is said of a journey that was estimated: the band as it is said where it stands
 * alone, and the line that says it is an estimate and what it was worked out from.
 *
 * The band is the journey's own. It is said in the words of its fact where that fact is in
 * hand and says the band the ranking does, and else in the words the website keeps for
 * the band: the fact of another journey says nothing of this one, and the fact of an older
 * answer may say another band.
 *
 * The line is one line, which the service says of every journey it estimated. So it is
 * taken from the fact of any such journey that is in hand, as the source and the date of a
 * journey are: seen in a browser, of five results three said it in the words of the
 * service and two in words of the website. With none in hand the website says its own.
 */
function toldOfTheEstimate(
  facts: Facts,
  area: Pick<RankedArea, "area_id">,
  leg: Pick<CommuteLeg, "place_id" | "mode">,
  band: JourneyBand,
): { readonly verdict: string; readonly estimated: string } {
  const estimated = Object.values(facts).filter((fact) => fact.kind === "travel" && fact.template === "travel_estimated");
  const own = estimated.find(
    (fact) => fact.area_id === area.area_id && fact.key === `${leg.place_id}.${leg.mode}` && fact.slots.band === band,
  );
  const line = [own, ...estimated].flatMap((fact) => fact?.slots.estimated ?? [])[0];
  return { verdict: own?.slots.verdict ?? JOURNEYS.estimated[band], estimated: line ?? JOURNEYS.estimatedFrom };
}

interface JourneyProps {
  readonly area: RankedArea;
  readonly commutes: readonly Commute[];
  /** Which journey counts: the one that does worst, or the average. */
  readonly combine: Combine;
  readonly cutoffs: Cutoffs;
  /** The name of each place, by place id. */
  readonly names: ReadonlyMap<string, string>;
  readonly facts: Facts;
}

/**
 * Each journey: where to, how, how long, and whether that is within the
 * longest the person set. "Within" and "over" are words. With two journeys
 * or more, a line under them says which the fit is worked out from.
 *
 * On a narrow screen each journey is stacked: the place, then whether it is
 * within the limit, then how and how long. It is one table either way, and
 * every part says its role, so that a browser which forgets a table when it
 * is laid out as blocks is told again.
 */
export function JourneyList({ area, commutes, combine, cutoffs, names, facts }: JourneyProps) {
  if (area.legs.length === 0) return null;
  const { columns } = JOURNEYS;
  const driver = combine === "slowest" ? drivingLeg(area) : null;
  const leftOut = journeysLeftOut(area);
  const uses =
    leftOut !== null
      ? JOURNEYS.usesNone(leftOut)
      : area.legs.length < 2
        ? null
        : combine === "mean"
          ? JOURNEYS.usesMean
          : driver !== null
            ? JOURNEYS.usesOne(names.get(driver.place_id) ?? "")
            : null;
  return (
    <div className={styles.journeysPart}>
      <table role="table" className={styles.journeys}>
        <caption className="visually-hidden">{JOURNEYS.title}</caption>
        {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
        <thead role="rowgroup" className={styles.head}>
          <tr role="row">
            <th role="columnheader" scope="col">
              {columns.place}
            </th>
            <th role="columnheader" scope="col">
              {columns.how}
            </th>
            <th role="columnheader" scope="col">
              {columns.typical}
            </th>
            <th role="columnheader" scope="col">
              {columns.missed}
            </th>
            <th role="columnheader" scope="col">
              {columns.limit}
            </th>
          </tr>
        </thead>
        {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
        <tbody role="rowgroup">
          {area.legs.map((leg) => {
            const commute = commutes.find((one) => one.place_id === leg.place_id);
            const within = withinLimit(leg, commute);
            const band = estimateOf(leg);
            const told = band === null ? null : toldOfTheEstimate(facts, area, leg, band);
            const name = names.get(leg.place_id) ?? "";
            // By bike and on foot there is one time, and no service to miss.
            const oneTime = leg.mode !== "pt";
            return (
              <tr role="row" key={`${leg.place_id}.${leg.mode}`}>
                <th role="rowheader" scope="row">
                  {name}
                </th>
                {/* The roles are the cells' own. They are said again because a narrow screen
                    stacks the rows, and a browser may then forget that a cell is a cell. */}
                {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                <td role="cell">
                  <CellLabel>{columns.how}</CellLabel>
                  {MODE[leg.mode]}
                </td>
                {leg.status === "ok" ? (
                  <>
                    {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                    <td role="cell">
                      <CellLabel>{columns.typical}</CellLabel>
                      {leg.minutes_typical === null
                        ? JOURNEYS.notGiven
                        : JOURNEYS.minutes(leg.minutes_typical)}
                    </td>
                    {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                    <td role="cell">
                      <CellLabel>{columns.missed}</CellLabel>
                      {oneTime
                        ? JOURNEYS.notApply
                        : leg.minutes_just_missed === null
                          ? JOURNEYS.notGiven
                          : JOURNEYS.minutes(leg.minutes_just_missed)}
                    </td>
                  </>
                ) : (
                  // eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role
                  <td role="cell" colSpan={2}>
                    <CellLabel>{columns.time}</CellLabel>
                    {band !== null ? (
                      // No time is held. The band is said, and that it is an estimate, and no minutes.
                      <>
                        <strong>{told?.verdict}</strong>. {told?.estimated}
                      </>
                    ) : leg.status === "beyond_cutoff" ? (
                      JOURNEYS.beyond(cutoffs[leg.mode])
                    ) : (
                      JOURNEYS.missing
                    )}
                  </td>
                )}
                {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                <td role="cell" className={styles.verdict}>
                  <CellLabel>{columns.limit}</CellLabel>
                  {commute ? (
                    <>
                      {within === null ? null : (
                        <strong className={within ? styles.within : styles.over}>
                          {within ? JOURNEYS.within : JOURNEYS.over}{" "}
                        </strong>
                      )}
                      {JOURNEYS.limit(commute.max_minutes)}
                    </>
                  ) : null}{" "}
                  <SourceNote facts={factsForJourney(area, leg, facts)} of={name} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {uses !== null ? <p className={styles.uses}>{uses}</p> : null}
      <p className={styles.timed}>
        {/* Which page a person reads next is told to no server ahead of time. */}
        <Link className="target-min" href={paths.methods("journeys")} prefetch={false}>
          {JOURNEYS.timed}
        </Link>
      </p>
    </div>
  );
}

interface SaysProps {
  readonly contribution: Contribution;
  /** The fact the contribution names first, where it is in hand. */
  readonly fact: Fact | undefined;
  /** What the row is of, to tell its "Source" from the next. */
  readonly label: string;
}

/**
 * What the data says of one thing that counts: the slots of its fact, as the
 * API formatted them, and the fact's source. Where there is a figure and its
 * fact is not in hand, it says only that there is one.
 *
 * How the area scores on the thing is never shown. For a feature that score
 * is the percentile it is ranked by, which the contract says is never
 * printed: where areas tie it is untrue of the release. The fact's own
 * standing is the literal truth, and has a source.
 */
function Says({ contribution, fact, label }: SaysProps) {
  if (!contribution.present) return BREAKDOWN.hasNot;
  const columns = fact === undefined || fact.kind === "missing" ? [] : columnsOf(fact);
  if (fact === undefined || columns.length === 0) return BREAKDOWN.has;
  return (
    <>
      <dl className={styles.says}>
        {columns.map(([column, value]) => (
          <div key={column}>
            <dt>{column}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <SourceNote facts={[fact]} of={`${BREAKDOWN.title}: ${label}`} />
    </>
  );
}

interface BreakdownProps {
  readonly area: RankedArea;
  readonly meta: Pick<MetaData, "features" | "tags">;
  /** The area's name, to tell one breakdown's button from the next. */
  readonly name: string;
  readonly facts: Facts;
}

/**
 * How the fit is worked out: each thing that counts, how much it counts, its
 * share of the fit, what it adds, and what the data says of it. Closed at
 * first. Every figure of the ranking is rounded down, and a line under the
 * table says so, because what the things add can then come to less than the
 * fit.
 */
export function ScoreBreakdown({ area, meta, name, facts }: BreakdownProps) {
  if (area.contributions.length === 0) return null;
  const { columns } = BREAKDOWN;
  return (
    <Disclosure label={BREAKDOWN.title} name={`${BREAKDOWN.title}: ${name}`}>
      <div className={styles.breakdownPart}>
        <table role="table" className={styles.breakdown}>
          <caption>{BREAKDOWN.caption}</caption>
          {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
          <thead role="rowgroup" className={styles.head}>
            <tr role="row">
              <th role="columnheader" scope="col">
                {columns.thing}
              </th>
              <th role="columnheader" scope="col">
                {columns.weight}
              </th>
              <th role="columnheader" scope="col">
                {columns.share}
              </th>
              <th role="columnheader" scope="col">
                {columns.adds}
              </th>
              <th role="columnheader" scope="col">
                {columns.says}
              </th>
            </tr>
          </thead>
          {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
          <tbody role="rowgroup">
            {area.contributions.map((contribution) => {
              const label = labelOf(contribution, meta, {
                journey: BREAKDOWN.journey,
                budget: BREAKDOWN.budget,
              });
              const [first] = contribution.fact_ids;
              return (
                <tr role="row" key={contribution.component}>
                  <th role="rowheader" scope="row">
                    {label}
                  </th>
                  {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                  <td role="cell">
                    <CellLabel>{columns.weight}</CellLabel>
                    {BREAKDOWN.outOf(Number(outOfHundred(contribution.weight)))}
                  </td>
                  {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                  <td role="cell">
                    <CellLabel>{columns.share}</CellLabel>
                    {BREAKDOWN.percent(hundredths(contribution.share) ?? 0)}
                  </td>
                  {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                  <td role="cell">
                    <CellLabel>{columns.adds}</CellLabel>
                    {BREAKDOWN.outOf(hundredths(contribution.contribution) ?? 0)}
                  </td>
                  {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                  <td role="cell">
                    <CellLabel>{columns.says}</CellLabel>
                    <Says
                      contribution={contribution}
                      fact={first === undefined ? undefined : facts[first]}
                      label={label}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className={styles.rounded}>{BREAKDOWN.roundedDown}</p>
      </div>
    </Disclosure>
  );
}
