"use client";

import Link from "next/link";

import { TABLE } from "@/content/map";
import { COMPLETENESS, FILTERED, RESULTS, UNRANKED } from "@/content/search";
import type { AreaSummary, Filtered, RankedArea, Score, Unranked } from "@/lib/api/schema";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { completenessOf } from "@/lib/search/card";

import styles from "./AreaTable.module.css";

interface Props {
  readonly areas: readonly AreaSummary[];
  /** Every ranked area, in rank order. Empty before a search. */
  readonly scores: readonly Score[];
  /**
   * The areas of the list, which say how much of what counts each has a figure for. A
   * score alone does not (docs/design/web.md, section 13, gap 18).
   */
  readonly ranked?: readonly RankedArea[];
  readonly filtered: readonly Filtered[];
  readonly unranked: readonly Unranked[];
  /** True when nothing is set to rank by, so a fit says nothing. */
  readonly emptySpec?: boolean;
  /** True once there is a ranking. Before it, no area has a status but "not ranked yet". */
  readonly searched: boolean;
  readonly selectedId: string | null;
  readonly onSelect: (areaId: string) => void;
  readonly onHover: (areaId: string | null) => void;
}

export interface TableRow {
  readonly area: AreaSummary;
  readonly rank: number | null;
  readonly fit: number | null;
  /** Said beside the fit where it rests on only part of what counts. `null` where it rests on all, or is not known. */
  readonly based: string | null;
  readonly status: string;
}

/** How much of what counts a fit rests on, in words, where that is known and is not all of it. */
export function basedOn(area: Pick<RankedArea, "contributions"> | undefined): string | null {
  if (area === undefined) return null;
  const { asked, present, complete } = completenessOf(area);
  return asked === 0 || complete ? null : COMPLETENESS.some(present, asked);
}

/**
 * Every area of the release, with everything the map says of it: its rank,
 * its fit, and in words why it has none. In rank order, and then by name.
 */
export function rowsOf({
  areas,
  scores,
  ranked = [],
  filtered,
  unranked,
  emptySpec = false,
  searched,
}: Pick<Props, "areas" | "scores" | "ranked" | "filtered" | "unranked" | "emptySpec" | "searched">): TableRow[] {
  const rows = areas.map((area): TableRow => {
    const at = scores.findIndex((score) => score.area_id === area.area_id);
    const score = scores[at];
    if (score !== undefined) {
      const fit = emptySpec ? null : fitOf(score.score);
      const based = fit === null ? null : basedOn(ranked.find((one) => one.area_id === area.area_id));
      return { area, rank: at + 1, fit, based, status: TABLE.ranked };
    }
    const none = { area, rank: null, fit: null, based: null };
    const left = filtered.find((one) => one.area_id === area.area_id);
    if (left) return { ...none, status: FILTERED[left.reason] };
    const not = unranked.find((one) => one.area_id === area.area_id);
    if (not) return { ...none, status: UNRANKED[not.reason] };
    return {
      ...none,
      status: !area.rankable ? UNRANKED.not_rankable : searched ? TABLE.noRank : TABLE.notYet,
    };
  });
  return rows.sort(
    (one, other) =>
      (one.rank ?? Infinity) - (other.rank ?? Infinity) ||
      one.area.name.localeCompare(other.area.name, "en-GB"),
  );
}

/**
 * The table that says everything the map does. It is always one tab away
 * from the map, and it is what is shown where the map cannot be drawn.
 */
export function AreaTable(props: Props) {
  const { selectedId, onSelect, onHover, searched, scores, ranked = [], emptySpec = false } = props;
  const rows = rowsOf(props);
  // How much of what counts a fit rests on is known for the areas of the list and for no other.
  const cannotSay = searched && !emptySpec && scores.length > ranked.length;
  return (
    <div className={styles.whole}>
      <div className="scroll-x">
        <table className={styles.table}>
          <caption>{searched ? TABLE.caption : TABLE.captionEmpty}</caption>
          <thead>
            <tr>
              <th scope="col">{TABLE.columns.rank}</th>
              <th scope="col">{TABLE.columns.area}</th>
              <th scope="col">{TABLE.columns.borough}</th>
              <th scope="col">{TABLE.columns.fit}</th>
              <th scope="col">{TABLE.columns.status}</th>
              <th scope="col">
                <span className="visually-hidden">{RESULTS.actions}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ area, rank, fit, based, status }) => (
              <tr
                key={area.area_id}
                aria-current={selectedId === area.area_id ? "true" : undefined}
                onMouseEnter={() => onHover(area.area_id)}
                onMouseLeave={() => onHover(null)}
                onFocus={() => onHover(area.area_id)}
                onBlur={() => onHover(null)}
              >
                <td className={styles.number}>{rank ?? TABLE.noRank}</td>
                <th scope="row">
                  <Link className={`${styles.link} target-min`} href={paths.area(area)} prefetch={false}>
                    {area.name}
                  </Link>
                </th>
                <td>{area.borough}</td>
                <td>
                  <span className={styles.number}>{fit === null ? TABLE.noFit : RESULTS.fitOf(fit)}</span>
                  {based !== null ? <span className={styles.based}> {based}</span> : null}
                </td>
                <td>{status}</td>
                <td>
                  <button
                    type="button"
                    className={`${styles.show} target-min`}
                    aria-label={TABLE.select(area.name)}
                    aria-pressed={selectedId === area.area_id}
                    onClick={() => onSelect(area.area_id)}
                  >
                    {TABLE.show}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {cannotSay ? <p className={styles.note}>{TABLE.partNote}</p> : null}
    </div>
  );
}
