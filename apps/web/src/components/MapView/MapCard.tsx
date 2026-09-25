"use client";

import Link from "next/link";

import { MAP_CARD } from "@/content/map";
import { FILTERED, RESULTS, UNRANKED } from "@/content/search";
import type { AreaSummary, Filtered, Score, Unranked } from "@/lib/api/schema";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { basedOn } from "@/lib/search/card";
import { placedOn, type Lens } from "@/lib/vibes";

import { BesideName } from "../BesideName/BesideName";
import { CompareButton } from "../CompareTray/CompareButton";
import { RoughLabel } from "../RoughGuide/RoughGuide";
import styles from "./MapView.module.css";

interface Props {
  readonly summary: AreaSummary;
  readonly scores: readonly Score[];
  readonly filtered: readonly Filtered[];
  readonly unranked: readonly Unranked[];
  readonly emptySpec?: boolean;
  /** True when the area is among the results the list holds. */
  readonly inList?: boolean;
  /** The vibe the map is coloured by, before a search. */
  readonly lens?: Lens | null;
  readonly onShowInList: () => void;
  readonly onClose: () => void;
}

/**
 * What the map says of the area chosen on it, in words: its name, its
 * borough, its rank and its fit, or the reason it has no rank. Under the fit,
 * how much of what counts it rests on, as the list says it: a fit with
 * nothing beside it reads as one that rests on everything. Where the map is
 * coloured by a vibe, the band the colour stands for.
 *
 * Its name is the way to the page of the area, in one press, and the area can
 * be put among those to compare from here: an area pressed on the map once
 * led nowhere.
 */
export function MapCard({
  summary,
  scores,
  filtered,
  unranked,
  emptySpec = false,
  inList = false,
  lens = null,
  onShowInList,
  onClose,
}: Props) {
  const at = scores.findIndex((score) => score.area_id === summary.area_id);
  const score = scores[at];
  const rests = score === undefined || emptySpec ? null : basedOn(score, true);
  const left = filtered.find((one) => one.area_id === summary.area_id);
  const apart = unranked.find((one) => one.area_id === summary.area_id);
  // A reason the page has no words for is left out, and never shown as its code or as a blank.
  const words: Readonly<Record<string, string | undefined>> = left !== undefined ? FILTERED : UNRANKED;
  const why = words[left?.reason ?? apart?.reason ?? ""] ?? null;
  const placed = lens === null ? null : placedOn(lens, summary.area_id);

  return (
    <section className={styles.card} aria-label={MAP_CARD.label}>
      <div>
        <p className={styles.cardName}>
          {/* Which page a person reads next is told to no server ahead of time. */}
          <Link className="target-min" href={paths.area(summary)} prefetch={false}>
            {summary.name}
          </Link>
        </p>
        {/* Beside the name: the label its publisher gives the area, and that the name is a draft. */}
        <BesideName area={summary} className={styles.cardBorough} />
      </div>
      {lens !== null && placed !== null ? (
        <p>
          {lens.tag.label}
          <RoughLabel told={lens.rough ?? null} />: {placed}
        </p>
      ) : null}
      {score !== undefined ? (
        <p>
          {RESULTS.rank(at + 1)}
          {emptySpec ? null : `, ${RESULTS.fit.toLowerCase()} ${RESULTS.fitOf(fitOf(score.score))}`}
        </p>
      ) : why !== null ? (
        <p>{why}</p>
      ) : null}
      {rests !== null ? <p className={styles.cardNote}>{rests}</p> : null}
      <div className={styles.cardActions}>
        {inList ? (
          <button type="button" className="target" onClick={onShowInList}>
            {MAP_CARD.showInList}
          </button>
        ) : score !== undefined ? (
          <p className={styles.cardNote}>{MAP_CARD.notInList}</p>
        ) : null}
        <CompareButton area={summary} small />
        <button type="button" className="target" onClick={onClose}>
          {MAP_CARD.close}
        </button>
      </div>
    </section>
  );
}
