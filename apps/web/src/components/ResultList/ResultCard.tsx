"use client";

import Link from "next/link";
import { useId } from "react";

import { COST, JOURNEYS, RESULTS } from "@/content/search";
import type {
  AreaData,
  AreaSummary,
  Explanation,
  Meta,
  MetaData,
  Operations,
  PreferenceSpec,
  RankedArea,
} from "@/lib/api/schema";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { costFor, nearestStation, withinLimit, type Facts } from "@/lib/search/card";
import { edits } from "@/lib/search/edits";

import { CompareButton } from "../CompareTray/CompareButton";
import { CostRange, type Scale } from "../CostRange/CostRange";
import { Disclosure } from "../Disclosure/Disclosure";
import { FactRow } from "../FactRow/FactRow";
import { LocatorMap, type Outline } from "../LocatorMap/LocatorMap";
import { Sentence } from "../Sentence/Sentence";
import { Skeleton } from "../Skeleton/Skeleton";
import { Completeness, JourneyList, Missing, ScoreBreakdown } from "./parts";
import styles from "./ResultList.module.css";
import { isGivenUp, legOf } from "./tradeoff";

/** How many reasons a card keeps room for. */
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

function Heading({ area, summary, noFit, id }: Pick<Shared, "area" | "summary" | "noFit"> & { id: string }) {
  const fit = fitOf(area.score);
  return (
    <header className={styles.heading}>
      <p className={styles.rank}>
        <span className="visually-hidden">{RESULTS.rank(area.rank)}</span>
        <span aria-hidden="true">{area.rank}</span>
      </p>
      <div className={styles.names}>
        <h3 id={id} className={styles.name}>
          {summary.name}
        </h3>
        <p className={styles.borough}>{summary.borough}</p>
      </div>
      {noFit ? null : (
        <div className={styles.fit}>
          <p>
            <span className={styles.fitLabel}>{RESULTS.fit} </span>
            <span className={styles.fitFigure}>{RESULTS.fitOf(fit)}</span>
          </p>
          {/* The bar repeats the figure beside it, so it is kept from a screen reader. */}
          <div className={styles.meter} aria-hidden="true">
            <span style={{ width: `${fit}%` }} />
          </div>
        </div>
      )}
    </header>
  );
}

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
        {/* The tray is above the results, which may be a long way up from this card. */}
        <CompareButton area={summary} far />
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
  readonly outlines: readonly Outline[];
  /** The scale the cost of every card of the list is drawn on. */
  readonly scale?: Scale | null;
  /** The release and the engine behind the card. */
  readonly served: Pick<Meta, "release_id" | "engine_version">;
}

interface TradeOffProps extends Pick<Shared, "area" | "summary" | "facts" | "spec"> {
  readonly explanation?: Explanation;
  readonly waiting: boolean;
}

/**
 * What the area gives up, under the word "Trade-off". The sentence is the
 * API's, word for word. It is shown only if the ranking itself says the area
 * does that thing badly, so that a strength is never put under the word.
 * With none to show, the card says that none was found.
 *
 * A sentence about a journey gives the minutes and not the limit the person
 * set. The card holds both, and says beside the sentence which way it falls,
 * in the words the table of journeys uses.
 */
function TradeOff({ area, summary, explanation, facts, spec, waiting }: TradeOffProps) {
  const given = explanation?.trade_off ?? null;
  const sentence = given !== null && isGivenUp(area, given, spec.commutes) ? given : null;
  const leg = sentence === null ? null : legOf(area, sentence);
  const commute = leg === null ? undefined : spec.commutes.find((one) => one.place_id === leg.place_id);
  const within = leg === null ? null : withinLimit(leg, commute);
  return (
    <div className={styles.part}>
      <h4 className={styles.tradeOff}>
        <span className={styles.tradeOffMark} aria-hidden="true" />
        {RESULTS.tradeOffTitle}
      </h4>
      {explanation ? (
        sentence !== null ? (
          <>
            <Sentence sentence={sentence} facts={facts} of={`${summary.name}, ${RESULTS.tradeOffTitle}`} />
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
 * One of the first five results, in full: how complete the data is, where
 * the area is, three reasons, one trade-off, what has no figure, each
 * journey, the cost, and how the fit is worked out. Every sentence is the
 * API's, and every line ends in its source.
 *
 * Each part has its size before it has its content, so text that comes late
 * moves nothing.
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
  outlines,
  scale = null,
  served,
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
        <Heading area={area} summary={summary} noFit={noFit} id={`${id}-name`} />
        {/* Directly under the fit, as on a row: it says how far the fit is to be trusted. */}
        <Completeness area={area} commutes={spec.commutes} />

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
            <LocatorMap outlines={outlines} areaId={areaId} name={summary.name} />
          </div>
        </div>

        <div className={styles.part}>
          <h4>{RESULTS.reasonsTitle}</h4>
          {/* Room for three is kept whether there are three or not. */}
          <div className={styles.reasons}>
            {explanation ? (
              explanation.reasons.length > 0 ? (
                <ol>
                  {explanation.reasons.slice(0, REASONS).map((reason, at) => (
                    <li key={reason.fact_ids.join(" ")}>
                      <Sentence sentence={reason} facts={facts} of={`${summary.name}, ${at + 1}`} />
                    </li>
                  ))}
                </ol>
              ) : (
                <p>{RESULTS.noReasons}</p>
              )
            ) : waitingForReasons ? (
              <Skeleton lines={REASONS} />
            ) : null}
          </div>
          {explainFailed && !explanation ? <p className={styles.failed}>{RESULTS.reasonsFailed}</p> : null}
        </div>

        <TradeOff
          area={area}
          summary={summary}
          explanation={explanation}
          facts={facts}
          spec={spec}
          waiting={waitingForReasons}
        />

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

        <footer className={styles.foot}>
          <span>
            {RESULTS.foot.release} <code>{served.release_id}</code>
          </span>
          <span>
            {RESULTS.foot.engine} <code>{served.engine_version}</code>
          </span>
        </footer>
      </article>
    </li>
  );
}

/**
 * One of results 6 to 20: rank, name, borough, fit and how complete, opening
 * to the journeys and to how the fit is worked out. The API writes reasons
 * for the first five only, so a row has none.
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
        <Heading area={area} summary={summary} noFit={noFit} id={`${id}-name`} />
        <Completeness area={area} commutes={spec.commutes} />
        <Disclosure label={RESULTS.more} name={`${RESULTS.more}: ${summary.name}`}>
          <div className={styles.more}>
            <JourneyList
              area={area}
              commutes={spec.commutes}
              combine={spec.commute_combine}
              cutoffs={meta.limits.cutoff_minutes}
              names={names}
              facts={facts}
            />
            <ScoreBreakdown area={area} meta={meta} name={summary.name} facts={facts} />
            <Actions summary={summary} onSelect={onSelect} onEdit={onEdit} />
          </div>
        </Disclosure>
      </article>
    </li>
  );
}
