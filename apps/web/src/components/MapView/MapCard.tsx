"use client";

import Link from "next/link";
import type { FocusEvent, KeyboardEvent, Ref } from "react";

import { MAP_CARD } from "@/content/map";
import { FILTERED, RESULTS, UNRANKED } from "@/content/search";
import type { AreaSummary, Filtered, Score, Unranked } from "@/lib/api/schema";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { basedOn } from "@/lib/search/card";
import { placedOn, type Lens } from "@/lib/vibes";

import { BesideName } from "../BesideName/BesideName";
import { CompareButton } from "../CompareTray/CompareButton";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
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
  /** The id of the card, by which the pin that opens it names it. */
  readonly id?: string;
  /** The card itself, for the map to give it the focus as it opens. */
  readonly ref?: Ref<HTMLElement>;
  /** Hears the keys from inside the card: Escape closes it. */
  readonly onKeyDown?: (event: KeyboardEvent<HTMLElement>) => void;
  /** Hears the focus as it comes to the card, or to what it holds. */
  readonly onFocus?: (event: FocusEvent<HTMLElement>) => void;
}

/**
 * The box of the area that is chosen, which the map draws under itself. It is found as a
 * person finds it, by what it is and by its name. `null` where the map is not drawn, or no
 * area is chosen.
 */
export function cardOfTheMap(): HTMLElement | null {
  const boxes = [...document.querySelectorAll<HTMLElement>("section[aria-label]")];
  return boxes.find((one) => one.getAttribute("aria-label") === MAP_CARD.label) ?? null;
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
 *
 * It is the box of the area in hand, so its inner rule is amber, as the pin of
 * the area is.
 *
 * It can be given the focus, and is no stop of its own: the map gives it the
 * focus as it opens of a press on the map, so that what it holds is the next
 * stop of a keyboard. It is then heard by its name, and by what it says of the
 * area: its name, and its rank and fit or why it has none.
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
  id,
  ref,
  onKeyDown,
  onFocus,
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

  const said = id === undefined ? undefined : `${id}-name ${id}-says`;

  return (
    <Frame
      kind="box-on"
      as="section"
      ref={ref}
      id={id}
      className={styles.card}
      aria-label={MAP_CARD.label}
      aria-describedby={said}
      tabIndex={-1}
      onKeyDown={onKeyDown}
      onFocus={onFocus}
    >
      <div>
        <p id={id === undefined ? undefined : `${id}-name`} className={styles.cardName}>
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
          {lens.tag.label}: {placed}
        </p>
      ) : null}
      {score !== undefined ? (
        <p id={id === undefined ? undefined : `${id}-says`}>
          {RESULTS.rank(at + 1)}
          {emptySpec ? null : `, ${RESULTS.fit.toLowerCase()} ${RESULTS.fitOf(fitOf(score.score))}`}
        </p>
      ) : why !== null ? (
        <p id={id === undefined ? undefined : `${id}-says`}>{why}</p>
      ) : null}
      {rests !== null ? <p className={styles.cardNote}>{rests}</p> : null}
      <div className={styles.cardActions}>
        {inList ? (
          <Press onPress={onShowInList}>{MAP_CARD.showInList}</Press>
        ) : score !== undefined ? (
          <p className={styles.cardNote}>{MAP_CARD.notInList}</p>
        ) : null}
        <CompareButton area={summary} small />
        <Press onPress={onClose}>{MAP_CARD.close}</Press>
      </div>
    </Frame>
  );
}
