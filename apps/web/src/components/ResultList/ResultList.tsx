"use client";

import { useEffect, useMemo, useRef } from "react";

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
} from "@/lib/api/schema";
import { costFor, type Facts } from "@/lib/search/card";
import { namesOfPlaces } from "@/lib/search/chips";
import { EXPLAINED } from "@/lib/search/flow";

import { scaleOf } from "../CostRange/CostRange";
import { outlinesOf } from "../LocatorMap/LocatorMap";
import { Skeleton } from "../Skeleton/Skeleton";
import { ResultCard, ResultRow } from "./ResultCard";
import styles from "./ResultList.module.css";

interface Props {
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
 * cards in full, and the rest are rows.
 *
 * When an area is chosen on the map, its card is brought into view. The
 * focus stays where it was.
 *
 * While a new ranking is worked out the list stays as it was, at full
 * strength, under a line that says so.
 */
export function ResultList({
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
  busy,
  selectedId,
  onSelect,
  onHover,
  onEdit,
}: Props) {
  const list = useRef<HTMLOListElement>(null);
  const outlines = useMemo(() => (geometry ? outlinesOf(geometry) : []), [geometry]);
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
    return (
      <div className={styles.list} aria-busy={busy}>
        {busy ? (
          Array.from({ length: EXPLAINED }, (_, at) => <Skeleton key={at} shape="card" lines={4} />)
        ) : (
          <p className={styles.waiting}>{RESULTS.waiting}</p>
        )}
      </div>
    );
  }

  const shared = { facts, spec, meta, names, noFit, onSelect, onHover, onEdit };
  return (
    <>
      {/* That the list is being worked out again is said in words, and the list is not dimmed:
          dimmed, its text falls below the contrast it needs. The line keeps its place when it
          says nothing, so that the list stays where it is. The line in the form is the one
          that is announced, so this one is not. */}
      <p className={styles.working}>{busy ? RESULTS.working : null}</p>
      <ol ref={list} className={styles.list} aria-label={RESULTS.listLabel} aria-busy={busy}>
        {ranked.map((area, at) => {
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
              outlines={outlines}
              scale={scale}
              served={served}
            />
          );
        })}
      </ol>
    </>
  );
}
