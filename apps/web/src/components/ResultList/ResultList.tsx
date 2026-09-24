"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { RESULTS } from "@/content/search";
import type {
  AreaData,
  AreaSummary,
  Explanation,
  GeometryData,
  Meta,
  MetaData,
  Operations,
  PreferenceSpec,
  RankedArea,
  Unranked,
} from "@/lib/api/schema";
import { costFor, type Facts } from "@/lib/search/card";
import { namesOfPlaces } from "@/lib/search/chips";
import { EXPLAINED } from "@/lib/search/flow";

import { scaleOf } from "../CostRange/CostRange";
import { Skeleton } from "../Skeleton/Skeleton";
import { NotRanked } from "./NotRanked";
import { ResultCard, ResultRow } from "./ResultCard";
import styles from "./ResultList.module.css";

/** How many results are on the page before "Show 10 more" is pressed. */
export const SHOWN_AT_FIRST = 10;

/**
 * Which part of the list is drawn. The first result stands before the map and the rest
 * after it, so that on a narrow screen the answer is whole on the first screen and the map
 * comes next. To whoever reads the page they are one list: the first, and then the rest
 * from the second.
 */
export type Part = "first" | "rest";

interface Props {
  readonly part: Part;
  /** The first twenty, in rank order. `null` while the first ranking is waited for. */
  readonly ranked: readonly RankedArea[] | null;
  readonly areas: readonly AreaSummary[];
  /** The reasons for the ranking on screen. Empty while they are waited for. */
  readonly explanations: readonly Explanation[];
  /** True once the reasons for the ranking on screen are in. */
  readonly explained: boolean;
  readonly explainFailed: boolean;
  readonly facts: Facts;
  readonly details: Readonly<Record<string, AreaData>>;
  readonly detailsFailed: readonly string[];
  readonly geometry: GeometryData | null;
  readonly spec: PreferenceSpec;
  readonly meta: MetaData;
  readonly served: Pick<Meta, "release_id" | "engine_version">;
  readonly placeNames: Readonly<Record<string, string>>;
  readonly noFit: boolean;
  /** The areas the ranking could not place. They are listed apart, under the list. */
  readonly unranked: readonly Unranked[];
  /** How many areas are ranked, and how many of them the answer holds in full. Both are the API's. */
  readonly areasRanked: number;
  readonly areasListed: number;
  /** True while a new ranking is being worked out. The list stays where it is. */
  readonly busy: boolean;
  readonly selectedId: string | null;
  readonly onSelect: (areaId: string) => void;
  readonly onHover: (areaId: string | null) => void;
  readonly onEdit: (operations: Operations) => void;
}

function reducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * The results, as an ordered list: the order is the rank. The first five are
 * cards, each the answer in a few lines, and the rest are rows of one line.
 * Ten are shown at first, and "Show 10 more" shows the rest.
 *
 * The list is drawn in two parts, the first result and the rest, with the map
 * between them. What says that the list is being worked out again stands over
 * the first part, and what shows more and names the release under the rest.
 *
 * Under the rest stand two things that say what the list does not hold. Where
 * areas are ranked below the last one listed, a line says so once every
 * listed area is on the page: until then the button that shows more says it.
 * And the areas that are not ranked are listed apart, closed at first.
 *
 * When an area is chosen on the map, its card is brought into view. The
 * focus stays where it was.
 *
 * While a new ranking is worked out the list stays as it was, at full
 * strength, under a line that says so.
 */
export function ResultList({
  part,
  ranked,
  areas,
  explanations,
  explained,
  explainFailed,
  facts,
  details,
  detailsFailed,
  geometry,
  spec,
  meta,
  served,
  placeNames,
  noFit,
  unranked,
  areasRanked,
  areasListed,
  busy,
  selectedId,
  onSelect,
  onHover,
  onEdit,
}: Props) {
  const list = useRef<HTMLOListElement>(null);
  const [all, setAll] = useState(false);
  const names = useMemo(() => namesOfPlaces(spec, placeNames), [spec, placeNames]);
  // One scale for the cost of every card, so that the budget is in one place on all of
  // them and a dearer home is drawn further along. It is worked out from the costs in hand.
  const scale = useMemo(() => {
    const costs = (ranked ?? []).slice(0, EXPLAINED).flatMap((area) => {
      const cost = costFor(details[area.area_id], spec);
      return cost === null ? [] : [cost.estimate];
    });
    return scaleOf(costs, spec.budget.amount);
  }, [ranked, details, spec]);
  // An area chosen on the map or in the table is shown in the list, wherever it stands in it.
  const chosenAt = selectedId === null ? -1 : (ranked ?? []).findIndex((area) => area.area_id === selectedId);
  const upTo = all || chosenAt >= SHOWN_AT_FIRST ? (ranked?.length ?? 0) : SHOWN_AT_FIRST;
  // Where this part begins in the ranking: the first result is one part, and the rest another.
  const from = part === "first" ? 0 : 1;
  const shown = (ranked ?? []).slice(from, part === "first" ? 1 : upTo);
  const more = part === "first" ? 0 : Math.max(0, (ranked?.length ?? 0) - upTo);

  useEffect(() => {
    if (selectedId === null) return;
    const chosen = [...(list.current?.children ?? [])].find(
      (item) => item.getAttribute("data-area") === selectedId,
    );
    if (chosen && typeof chosen.scrollIntoView === "function") {
      chosen.scrollIntoView({ block: "nearest", behavior: reducedMotion() ? "auto" : "smooth" });
    }
  }, [selectedId]);

  if (ranked === null) {
    // The place of each card is held while the first ranking is waited for: one before the
    // map, and the rest after it, so that the map does not move when they come.
    if (!busy && part === "rest") return null;
    return (
      <div className={styles.list} aria-busy={busy}>
        {busy ? (
          Array.from({ length: part === "first" ? 1 : EXPLAINED - 1 }, (_, at) => (
            <Skeleton key={at} shape="card" lines={4} />
          ))
        ) : (
          <p className={styles.waiting}>{RESULTS.waiting}</p>
        )}
      </div>
    );
  }

  const showTheRest = () => {
    setAll(true);
    // The button goes once it is pressed. The focus goes to the list it added to, and not to nothing.
    list.current?.focus({ preventScroll: true });
  };

  const shared = { facts, spec, meta, names, noFit, onSelect, onHover, onEdit };
  return (
    <>
      {/* That the list is being worked out again is said in words, and the list is not dimmed:
          dimmed, its text falls below the contrast it needs. The line in the form is the one
          that is announced, so this one is not. */}
      {busy && part === "first" ? <p className={styles.workingOut}>{RESULTS.working}</p> : null}
      {/* A search that ranks one area has no rest of a list to draw. */}
      {shown.length > 0 ? (
        <ol
          ref={list}
          className={styles.list}
          // The rest of the list begins at the second result, and says so.
          start={part === "rest" ? 2 : undefined}
          aria-label={part === "first" ? RESULTS.listLabel : RESULTS.restLabel}
          aria-busy={busy}
          // It can be given the focus by "Show 10 more", and is no stop of its own.
          tabIndex={-1}
        >
          {shown.map((area, within) => {
            const at = from + within;
            const summary = areas.find((known) => known.area_id === area.area_id);
            if (!summary) return null;
            const selected = selectedId === area.area_id;
            if (at >= EXPLAINED) {
              return (
                <ResultRow key={area.area_id} {...shared} area={area} summary={summary} selected={selected} />
              );
            }
            return (
              <ResultCard
                key={area.area_id}
                {...shared}
                area={area}
                summary={summary}
                selected={selected}
                explanation={explanations.find((one) => one.area_id === area.area_id)}
                explained={explained}
                explainFailed={explainFailed}
                detail={details[area.area_id]}
                detailFailed={detailsFailed.includes(area.area_id)}
                geometry={geometry ?? null}
                scale={scale}
              />
            );
          })}
        </ol>
      ) : null}
      {part === "rest" ? (
        // On one line where there is room, so that what the list does not hold costs the page
        // no height before it is opened.
        <div className={styles.under}>
          {more > 0 ? (
            <button type="button" className={`${styles.showMore} target`} onClick={showTheRest}>
              {RESULTS.showMore(more)}
            </button>
          ) : areasListed < areasRanked ? (
            // Areas stand below the last one listed. A list once stopped at 20 of 22 and said nothing.
            <p className={styles.below}>{RESULTS.listed(areasListed, areasRanked)}</p>
          ) : null}
          <NotRanked unranked={unranked} areas={areas} meta={meta} spec={spec} />
        </div>
      ) : null}
      {part === "rest" ? (
        <footer className={styles.foot}>
          {ranked.length > EXPLAINED ? <span>{RESULTS.firstFive}</span> : null}
          <span>
            {RESULTS.foot.release} <code>{served.release_id}</code>
          </span>
          <span>
            {RESULTS.foot.engine} <code>{served.engine_version}</code>
          </span>
        </footer>
      ) : null}
    </>
  );
}
