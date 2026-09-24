"use client";

import Link from "next/link";
import { useId, type ReactNode } from "react";

import { COST, JOURNEYS, RESULTS } from "@/content/search";
import type {
  AreaData,
  AreaSummary,
  ExplainedSentence,
  Explanation,
  GeometryData,
  MetaData,
  Operations,
  PreferenceSpec,
  RankedArea,
  StripMark,
} from "@/lib/api/schema";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { costFor, nearestStation, withinLimit, type Facts } from "@/lib/search/card";
import { edits } from "@/lib/search/edits";

import { CompareButton } from "../CompareTray/CompareButton";
import { CostRange, type Scale } from "../CostRange/CostRange";
import { Disclosure } from "../Disclosure/Disclosure";
import { FactRow } from "../FactRow/FactRow";
import { saysItsBorough } from "@/lib/area/named";

import { LocatorMap } from "../LocatorMap/LocatorMap";
import { Sentence } from "../Sentence/Sentence";
import { Skeleton } from "../Skeleton/Skeleton";
import { Picture, Strip } from "../Strip/Strip";
import stripStyles from "../Strip/Strip.module.css";
import { Completeness, JourneyList, Missing, ScoreBreakdown } from "./parts";
import styles from "./ResultList.module.css";
import { isGivenUp, legOf } from "./tradeoff";

/** How many reasons the API writes for a result, at most. The first is in the short form. */
const REASONS = 3;

interface Shared {
  readonly area: RankedArea;
  readonly summary: AreaSummary;
  readonly facts: Facts;
  readonly spec: PreferenceSpec;
  readonly meta: MetaData;
  /** The name of each place of the search, by place id. */
  readonly names: ReadonlyMap<string, string>;
  /** True when nothing is set to rank by, so the fit says nothing. */
  readonly noFit: boolean;
  readonly selected: boolean;
  readonly onSelect: (areaId: string) => void;
  readonly onHover: (areaId: string | null) => void;
  readonly onEdit: (operations: Operations) => void;
}

interface HeadingProps extends Pick<Shared, "area" | "summary" | "noFit"> {
  readonly id: string;
  /** True on a row, which gives the rank, the name and the fit. The borough is in the table and on the area's page. */
  readonly short?: boolean;
}

function Heading({ area, summary, noFit, id, short = false }: HeadingProps) {
  return (
    <header className={styles.heading}>
      <p className={styles.rank}>
        <span className="visually-hidden">{RESULTS.rank(area.rank)}</span>
        <span aria-hidden="true">{area.rank}</span>
      </p>
      <h3 id={id} className={styles.name}>
        {/* One press from the name of a result to the page of its area. The page is fetched
            when the link is pressed, and not before: which areas a search led to is not told
            to anyone by fetching their pages ahead of time. */}
        <Link className={`${styles.toArea} target-min`} href={paths.area(summary)} prefetch={false}>
          {summary.name}
        </Link>
      </h3>
      {/* A name that begins with its borough says it already. */}
      {short || saysItsBorough(summary) ? null : <p className={styles.borough}>{summary.borough}</p>}
      {noFit ? null : (
        <p className={styles.fit}>
          <span className={styles.fitLabel}>{RESULTS.fit} </span>
          <span className={styles.fitFigure}>{RESULTS.fitOf(fitOf(area.score))}</span>
        </p>
      )}
    </header>
  );
}

/** What is one press away, inside the working: the area's page, the map, and hiding the area. */
function Actions({ summary, onSelect, onEdit }: Pick<Shared, "summary" | "onSelect" | "onEdit">) {
  return (
    <ul className={styles.actions} aria-label={RESULTS.actions}>
      <li>
        {/* The page is fetched when the link is pressed, and not before: which areas a search
            led to is not told to anyone by fetching their pages ahead of time. */}
        <Link className={`${styles.action} target`} href={paths.area(summary)} prefetch={false}>
          {RESULTS.openArea(summary.name)}
        </Link>
      </li>
      <li>
        <button type="button" className="target" onClick={() => onSelect(summary.area_id)}>
          {RESULTS.showOnMap(summary.name)}
        </button>
      </li>
      <li>
        <button type="button" className="target" onClick={() => onEdit(edits.areaHide(summary.area_id))}>
          {RESULTS.hide(summary.name)}
        </button>
      </li>
    </ul>
  );
}

interface WayOnProps extends Pick<Shared, "summary"> {
  /** The full working of the result, which "Show the working" opens in place. */
  readonly children: ReactNode;
}

/**
 * The three things a result leads to, in one row: its full working, which
 * opens in place, the areas most like it, which are on its own page, and the
 * comparison. The button that fills the comparison says beside itself what
 * the tray would, and leads to the comparison.
 */
function WaysOn({ summary, children }: WayOnProps) {
  return (
    <div className={styles.waysOn}>
      <Disclosure
        label={RESULTS.showWorking}
        name={RESULTS.workingOf(summary.name)}
        size="small"
        className={styles.working}
      >
        {children}
      </Disclosure>
      {/* Which page a person reads next is told to no server ahead of time. */}
      <Link
        className={`${styles.way} target-min`}
        href={paths.area(summary, "alike")}
        aria-label={RESULTS.moreLikeOf(summary.name)}
        prefetch={false}
      >
        {RESULTS.moreLike}
      </Link>
      <CompareButton area={summary} small />
    </div>
  );
}

interface CardProps extends Shared {
  /** The reasons for this area, where the API gave any. */
  readonly explanation?: Explanation;
  /** True once the reasons for this ranking are in, whether or not this area has any. */
  readonly explained: boolean;
  /** True when the reasons could not be loaded. */
  readonly explainFailed?: boolean;
  /** The area's profile, once it is in. */
  readonly detail?: AreaData;
  readonly detailFailed?: boolean;
  /** The boundary of every area, once it has come. The working draws where the area is from it. */
  readonly geometry: GeometryData | null;
  /** The scale the cost of every card of the list is drawn on. */
  readonly scale?: Scale | null;
}

/**
 * The mark of the strip that a sentence is about: the one whose fact the sentence cites.
 * It is drawn beside its sentence, and not a second time in the strip above it.
 */
function markOf(area: RankedArea, sentence: ExplainedSentence | null | undefined): StripMark | undefined {
  if (sentence === null || sentence === undefined) return undefined;
  return area.strip.find((mark) => sentence.fact_ids.includes(mark.fact_id));
}

/** The trade-off as the card shows it: the API's, where the ranking says the area does that thing badly. */
function tradeOffOf(
  area: RankedArea,
  explanation: Explanation | undefined,
  spec: PreferenceSpec,
  meta: MetaData,
): ExplainedSentence | null {
  const given = explanation?.trade_off ?? null;
  return given !== null && isGivenUp(area, given, spec.commutes, meta.limits.trade_off_max_utility) ? given : null;
}

interface BesideProps {
  readonly mark: StripMark | undefined;
  readonly meta: MetaData;
}

/** The picture of the vibe a sentence is about, on the line of the sentence and before it. */
function Beside({ mark, meta }: BesideProps) {
  const tag = mark === undefined ? undefined : meta.tags.find((one) => one.tag_id === mark.tag_id);
  if (mark === undefined || tag === undefined) return null;
  return (
    <span className={stripStyles.beside}>
      <Picture mark={mark} tag={tag} />
    </span>
  );
}

interface TradeOffProps extends Pick<Shared, "area" | "summary" | "facts" | "spec" | "meta"> {
  readonly explanation?: Explanation;
  readonly waiting: boolean;
}

/**
 * What the area gives up, under the word "Trade-off". The sentence is the
 * API's, word for word. It is shown only if the ranking itself says the area
 * does that thing badly, so that a strength is never put under the word.
 * With none to show, the card says that none was found.
 *
 * Beside a sentence about a journey the card says which way it falls against
 * the limit the person set, in the words the table of journeys uses.
 */
function TradeOff({ area, summary, explanation, facts, spec, meta, waiting }: TradeOffProps) {
  const sentence = tradeOffOf(area, explanation, spec, meta);
  const leg = sentence === null ? null : legOf(area, sentence);
  const commute = leg === null ? undefined : spec.commutes.find((one) => one.place_id === leg.place_id);
  const within = leg === null ? null : withinLimit(leg, commute);
  return (
    <div className={`${styles.part} ${styles.runIn}`}>
      {/* The mark warns of something. Where no trade-off was found there is nothing to warn of. */}
      {explanation && sentence === null ? (
        <h4>{RESULTS.tradeOffTitle}</h4>
      ) : (
        <h4 className={styles.tradeOff}>
          <span className={styles.tradeOffMark} aria-hidden="true" />
          {RESULTS.tradeOffTitle}
        </h4>
      )}
      {explanation ? (
        sentence !== null ? (
          <>
            <Beside mark={markOf(area, sentence)} meta={meta} />
            <Sentence sentence={sentence} facts={facts} of={`${summary.name}, ${RESULTS.tradeOffTitle}`} meta={meta} />
            {commute !== undefined && within !== null ? (
              <p className={within ? styles.within : styles.over}>
                {within
                  ? JOURNEYS.withinLimit(commute.max_minutes)
                  : JOURNEYS.overLimit(commute.max_minutes)}
              </p>
            ) : null}
          </>
        ) : (
          <p>{RESULTS.noTradeOff}</p>
        )
      ) : waiting ? (
        <Skeleton />
      ) : null}
    </div>
  );
}

/**
 * One of the first five results. Its short form is the answer: rank, name and
 * borough, the fit and how much of what counts it rests on, where the area
 * sits on the vibes, one reason and the trade-off. Everything else is the
 * working, one press away: where the area is, the other reasons, what has no
 * figure, each journey, the cost, and how the fit is worked out.
 *
 * Every sentence is the API's, and every line ends in its source. Opening
 * one result closes no other.
 */
export function ResultCard({
  area,
  summary,
  explanation,
  explained,
  explainFailed = false,
  detail,
  detailFailed = false,
  facts,
  spec,
  meta,
  names,
  noFit,
  geometry,
  scale = null,
  selected,
  onSelect,
  onHover,
  onEdit,
}: CardProps) {
  const id = useId();
  const station = nearestStation(detail);
  const cost = costFor(detail, spec);
  const waitingForDetail = detail === undefined && !detailFailed;
  const waitingForReasons = !explained && !explainFailed;
  const { area_id: areaId } = area;
  const [reason, ...others] = explanation?.reasons.slice(0, REASONS) ?? [];
  // A vibe that is the reason, or the trade-off, is drawn beside its sentence. The strip
  // holds the rest: the same vibe twice, one directly under the other, said nothing more.
  const beside = [markOf(area, reason), markOf(area, tradeOffOf(area, explanation, spec, meta))].filter(
    (mark): mark is StripMark => mark !== undefined,
  );
  const inStrip = area.strip.filter((mark) => !beside.includes(mark));

  return (
    <li
      className={styles.item}
      data-area={areaId}
      onMouseEnter={() => onHover(areaId)}
      onMouseLeave={() => onHover(null)}
      onFocus={() => onHover(areaId)}
      onBlur={() => onHover(null)}
    >
      <article
        className={styles.card}
        aria-labelledby={`${id}-name`}
        aria-current={selected ? "true" : undefined}
        // It can be given the focus by "Show in the list", and is no stop of its own.
        tabIndex={-1}
      >
        {/* Directly after the fit, on its line where there is room: it says how far the fit is to be trusted. */}
        <div className={styles.top}>
          <Heading area={area} summary={summary} noFit={noFit} id={`${id}-name`} />
          <Completeness area={area} meta={meta} spec={spec} />
        </div>
        <Strip
          marks={inStrip}
          tags={meta.tags}
          facts={facts}
          of={summary.name}
          also={beside.some((mark) => mark.asked)}
        />

        <div className={`${styles.part} ${styles.runIn}`}>
          <h4>{RESULTS.reasonsTitle}</h4>
          {explanation ? (
            reason !== undefined ? (
              <>
                <Beside mark={markOf(area, reason)} meta={meta} />
                <Sentence sentence={reason} facts={facts} of={`${summary.name}, 1`} meta={meta} />
              </>
            ) : (
              <p>{RESULTS.noReasons}</p>
            )
          ) : waitingForReasons ? (
            <Skeleton />
          ) : null}
          {explainFailed && !explanation ? <p className={styles.failed}>{RESULTS.reasonsFailed}</p> : null}
        </div>

        <TradeOff
          area={area}
          summary={summary}
          explanation={explanation}
          facts={facts}
          spec={spec}
          meta={meta}
          waiting={waitingForReasons}
        />

        <WaysOn summary={summary}>
          <div className={styles.opened}>
            <div className={styles.part}>
              <h4>{RESULTS.whereTitle}</h4>
              <div className={styles.where}>
                <div className={styles.whereWords}>
                  {explanation ? (
                    <Sentence sentence={explanation.orientation} facts={facts} of={summary.name} />
                  ) : waitingForReasons ? (
                    <Skeleton />
                  ) : null}
                  {station ? <FactRow fact={station} /> : waitingForDetail ? <Skeleton /> : null}
                </div>
                <LocatorMap geometry={geometry} areaId={areaId} name={summary.name} />
              </div>
            </div>

            {others.length > 0 ? (
              <div className={styles.part}>
                <h4>{RESULTS.moreReasons}</h4>
                <ol className={styles.reasons} start={2}>
                  {others.map((other, at) => (
                    <li key={other.fact_ids.join(" ")}>
                      <Sentence sentence={other} facts={facts} of={`${summary.name}, ${at + 2}`} meta={meta} />
                    </li>
                  ))}
                </ol>
              </div>
            ) : null}

            <Missing area={area} missing={explanation?.missing} waiting={waitingForReasons} facts={facts} />

            {area.legs.length > 0 ? (
              <div className={styles.part}>
                <h4>{JOURNEYS.title}</h4>
                <JourneyList
                  area={area}
                  commutes={spec.commutes}
                  combine={spec.commute_combine}
                  cutoffs={meta.limits.cutoff_minutes}
                  names={names}
                  facts={facts}
                />
              </div>
            ) : null}

            <div className={styles.part}>
              <h4>{COST.title}</h4>
              {cost ? (
                <CostRange fact={cost.fact} estimate={cost.estimate} budget={spec.budget} scale={scale} />
              ) : waitingForDetail ? (
                <Skeleton lines={2} />
              ) : detailFailed ? (
                <p className={styles.failed}>{RESULTS.detailsFailed}</p>
              ) : (
                <p>{COST.none}</p>
              )}
            </div>

            <ScoreBreakdown area={area} meta={meta} name={summary.name} facts={facts} />
            <Actions summary={summary} onSelect={onSelect} onEdit={onEdit} />
          </div>
        </WaysOn>
      </article>
    </li>
  );
}

/**
 * One of results 6 to 20, in one line: rank, name, fit, how much of what
 * counts the fit rests on, and the strip. The API writes reasons for the
 * first five only, so a row has none. Its working is one press away: the
 * journeys, and how the fit is worked out.
 */
export function ResultRow({
  area,
  summary,
  facts,
  spec,
  meta,
  names,
  noFit,
  selected,
  onSelect,
  onHover,
  onEdit,
}: Shared) {
  const id = useId();
  const { area_id: areaId } = area;
  return (
    <li
      className={styles.item}
      data-area={areaId}
      onMouseEnter={() => onHover(areaId)}
      onMouseLeave={() => onHover(null)}
      onFocus={() => onHover(areaId)}
      onBlur={() => onHover(null)}
    >
      <article
        className={styles.row}
        aria-labelledby={`${id}-name`}
        aria-current={selected ? "true" : undefined}
        // It can be given the focus by "Show in the list", and is no stop of its own.
        tabIndex={-1}
      >
        <Heading area={area} summary={summary} noFit={noFit} id={`${id}-name`} short />
        <Completeness area={area} meta={meta} spec={spec} />
        <Strip marks={area.strip} tags={meta.tags} facts={facts} of={summary.name} />
        <WaysOn summary={summary}>
          <div className={styles.opened}>
            {area.legs.length > 0 ? (
              <div className={styles.part}>
                <h4>{JOURNEYS.title}</h4>
                <JourneyList
                  area={area}
                  commutes={spec.commutes}
                  combine={spec.commute_combine}
                  cutoffs={meta.limits.cutoff_minutes}
                  names={names}
                  facts={facts}
                />
              </div>
            ) : null}
            <ScoreBreakdown area={area} meta={meta} name={summary.name} facts={facts} />
            <Actions summary={summary} onSelect={onSelect} onEdit={onEdit} />
          </div>
        </WaysOn>
      </article>
    </li>
  );
}
