"use client";

import { MAP_CARD } from "@/content/map";
import { COMPLETENESS, FILTERED, RESULTS, UNRANKED } from "@/content/search";
import type { AreaSummary, Filtered, RankedArea, Score, Unranked } from "@/lib/api/schema";
import { fitOf } from "@/lib/map/fill";
import { completenessOf } from "@/lib/search/card";

import styles from "./MapView.module.css";

interface Props {
  readonly summary: AreaSummary;
  readonly scores: readonly Score[];
  readonly filtered: readonly Filtered[];
  readonly unranked: readonly Unranked[];
  readonly emptySpec?: boolean;
  /** The area as the list holds it, where it is among the results in the list. */
  readonly ranked?: RankedArea;
  readonly onShowInList: () => void;
  readonly onClose: () => void;
}

/**
 * What the map says of the area chosen on it, in words: its name, its
 * borough, its rank and its fit, or the reason it has no rank. Under the fit,
 * how much of what counts it rests on, as the list says it: a fit with
 * nothing beside it reads as one that rests on everything.
 */
export function MapCard({
  summary,
  scores,
  filtered,
  unranked,
  emptySpec = false,
  ranked,
  onShowInList,
  onClose,
}: Props) {
  const at = scores.findIndex((score) => score.area_id === summary.area_id);
  const score = scores[at];
  const reason =
    filtered.find((one) => one.area_id === summary.area_id)?.reason ??
    unranked.find((one) => one.area_id === summary.area_id)?.reason;
  const inList = ranked !== undefined;
  const rests = ranked === undefined || emptySpec ? null : completenessOf(ranked);
  const why =
    reason === undefined
      ? null
      : reason === "not_rankable" || reason === "insufficient_data"
        ? UNRANKED[reason]
        : FILTERED[reason];

  return (
    <section className={styles.card} aria-label={MAP_CARD.label}>
      <div>
        <p className={styles.cardName}>{summary.name}</p>
        <p className={styles.cardBorough}>{summary.borough}</p>
      </div>
      {score !== undefined ? (
        <p>
          {RESULTS.rank(at + 1)}
          {emptySpec ? null : `, ${RESULTS.fit.toLowerCase()} ${RESULTS.fitOf(fitOf(score.score))}`}
        </p>
      ) : why !== null ? (
        <p>{why}</p>
      ) : null}
      {score !== undefined && rests !== null && rests.asked > 0 ? (
        <p className={styles.cardNote}>
          {rests.complete ? COMPLETENESS.all : COMPLETENESS.some(rests.present, rests.asked)}
        </p>
      ) : null}
      <div className={styles.cardActions}>
        {inList ? (
          <button type="button" className="target" onClick={onShowInList}>
            {MAP_CARD.showInList}
          </button>
        ) : score !== undefined ? (
          <p className={styles.cardNote}>{MAP_CARD.notInList}</p>
        ) : null}
        <button type="button" className="target" onClick={onClose}>
          {MAP_CARD.close}
        </button>
      </div>
    </section>
  );
}
