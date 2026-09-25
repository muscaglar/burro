"use client";

import Link from "next/link";

import { TABLE } from "@/content/map";
import { BREAKDOWN, FILTERED, RESULTS, UNRANKED } from "@/content/search";
import type { AreaSummary, Filtered, MetaData, Score, Unranked } from "@/lib/api/schema";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { basedOn } from "@/lib/search/card";
import { placedOn, type Lens } from "@/lib/vibes";

import { BesideName } from "../BesideName/BesideName";
import styles from "./AreaTable.module.css";

interface Props {
  readonly areas: readonly AreaSummary[];
  /** Every ranked area, in rank order, each with how much of what counts it has a figure for. Empty before a search. */
  readonly scores: readonly Score[];
  readonly filtered: readonly Filtered[];
  readonly unranked: readonly Unranked[];
  /** True when nothing is set to rank by, so a fit says nothing. */
  readonly emptySpec?: boolean;
  /** True once there is a ranking. Before it, no area has a status but "not ranked yet". */
  readonly searched: boolean;
  /** The vibe the map is coloured by, before a search. The table then says the band of every area. */
  readonly lens?: Lens | null;
  /**
   * The names the API gives what counts. With them in hand, an area that is not ranked says
   * what it has no figure for: every row said "Too little data", and none said of what.
   */
  readonly meta?: Pick<MetaData, "features" | "tags">;
  readonly selectedId: string | null;
  readonly onSelect: (areaId: string) => void;
  readonly onHover: (areaId: string | null) => void;
}

export interface TableRow {
  readonly area: AreaSummary;
  readonly rank: number | null;
  readonly fit: number | null;
  /** Said beside the fit where it rests on only part of what counts. `null` where it rests on all. */
  readonly based: string | null;
  /** Where the area sits on the vibe the map is coloured by. `null` where the map is coloured by none. */
  readonly placed: string | null;
  readonly status: string;
}

/** Why an area is not ranked, and then what it has no figure for, by the names the API gives. */
function whyNot(not: Unranked, meta: Props["meta"]): string {
  // A newer service may give a reason the page has no words for. It is left as it was.
  const why = UNRANKED[not.reason];
  if ((why as string | undefined) === undefined) return why;
  const lacks = ((not.missing as readonly string[] | undefined) ?? []).flatMap((component) => {
    if (component === "commute") return [BREAKDOWN.journey];
    if (component === "budget") return [BREAKDOWN.budget];
    const [kind, id] = component.split(":", 2);
    const name =
      kind === "feature"
        ? meta?.features.find((one) => one.feature_id === id)?.label
        : meta?.tags.find((one) => one.tag_id === id)?.label;
    return name === undefined ? [] : [name];
  });
  return meta === undefined || lacks.length === 0 ? why : `${why}. ${TABLE.lacks} ${lacks.join(", ")}`;
}

/**
 * Every area of the release, with everything the map says of it: its rank,
 * its fit, and in words why it has none. In rank order, and then by name.
 */
export function rowsOf({
  areas,
  scores,
  filtered,
  unranked,
  emptySpec = false,
  searched,
  lens = null,
  meta,
}: Pick<
  Props,
  "areas" | "scores" | "filtered" | "unranked" | "emptySpec" | "searched" | "lens" | "meta"
>): TableRow[] {
  const rows = areas.map((area): TableRow => {
    const placed = lens === null ? null : placedOn(lens, area.area_id);
    const at = scores.findIndex((score) => score.area_id === area.area_id);
    const score = scores[at];
    if (score !== undefined) {
      const fit = emptySpec ? null : fitOf(score.score);
      return { area, rank: at + 1, fit, based: fit === null ? null : basedOn(score), placed, status: TABLE.ranked };
    }
    const none = { area, rank: null, fit: null, based: null, placed };
    const left = filtered.find((one) => one.area_id === area.area_id);
    if (left) return { ...none, status: FILTERED[left.reason] };
    const not = unranked.find((one) => one.area_id === area.area_id);
    if (not) return { ...none, status: whyNot(not, meta) };
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
 * What a cell is of, for the eye. On a narrow screen each area is a block and
 * the headings of the columns are not drawn, so each cell says its own. The
 * heading says it to a screen reader, so this is kept from one.
 */
function CellLabel({ children }: { readonly children: string }) {
  return (
    <span className={styles.cellLabel} aria-hidden="true">
      {children}
    </span>
  );
}

/**
 * The table that says everything the map does. It is one press away from
 * the map, and it is what there is where the map cannot be drawn.
 *
 * On a narrow screen each area is a block: its rank, its name and the way to
 * show it, and under them its borough, its fit and its status, each under its
 * own name. It was one wide table there, in a box that scrolled sideways, and
 * the fit was cut off at the edge of the screen. It is one table either way,
 * and every part says its role again, so that a browser which forgets a table
 * when it is laid out as blocks is told.
 */
export function AreaTable(props: Props) {
  const { selectedId, onSelect, onHover, searched, lens = null } = props;
  const rows = rowsOf(props);
  return (
    <div className={styles.whole}>
      <div className="scroll-x">
        <table role="table" className={styles.table}>
          <caption>{searched ? TABLE.caption : TABLE.captionEmpty}</caption>
          {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
          <thead role="rowgroup" className={styles.head}>
            <tr role="row">
              <th role="columnheader" scope="col">
                {TABLE.columns.rank}
              </th>
              <th role="columnheader" scope="col">
                {TABLE.columns.area}
              </th>
              <th role="columnheader" scope="col">
                {TABLE.columns.borough}
              </th>
              {lens !== null ? (
                <th role="columnheader" scope="col">
                  {lens.tag.label}
                </th>
              ) : null}
              <th role="columnheader" scope="col">
                {TABLE.columns.fit}
              </th>
              <th role="columnheader" scope="col">
                {TABLE.columns.status}
              </th>
              <th role="columnheader" scope="col">
                <span className="visually-hidden">{RESULTS.actions}</span>
              </th>
            </tr>
          </thead>
          {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
          <tbody role="rowgroup">
            {rows.map(({ area, rank, fit, based, placed, status }) => (
              <tr
                role="row"
                key={area.area_id}
                aria-current={selectedId === area.area_id ? "true" : undefined}
                onMouseEnter={() => onHover(area.area_id)}
                onMouseLeave={() => onHover(null)}
                onFocus={() => onHover(area.area_id)}
                onBlur={() => onHover(null)}
              >
                {/* The roles are the cells' own. They are said again because a narrow screen
                    stacks the rows, and a browser may then forget that a cell is a cell. */}
                {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                <td role="cell" className={`${styles.number} ${styles.rank}`}>
                  <CellLabel>{TABLE.columns.rank}</CellLabel>
                  {rank ?? TABLE.noRank}
                </td>
                <th role="rowheader" scope="row" className={styles.area}>
                  <Link className={`${styles.link} target-min`} href={paths.area(area)} prefetch={false}>
                    {area.name}
                  </Link>
                  {/* Under a name, the label its publisher gives the area. */}
                  <BesideName area={area} className={styles.label} labelOnly />
                </th>
                {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                <td role="cell">
                  <CellLabel>{TABLE.columns.borough}</CellLabel>
                  {area.borough}
                </td>
                {lens !== null ? (
                  // eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role
                  <td role="cell">
                    <CellLabel>{lens.tag.label}</CellLabel>
                    {placed}
                  </td>
                ) : null}
                {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                <td role="cell">
                  <CellLabel>{TABLE.columns.fit}</CellLabel>
                  <span className={styles.number}>{fit === null ? TABLE.noFit : RESULTS.fitOf(fit)}</span>
                  {based !== null ? <span className={styles.based}> {based}</span> : null}
                </td>
                {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                <td role="cell">
                  <CellLabel>{TABLE.columns.status}</CellLabel>
                  {status}
                </td>
                {/* eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role */}
                <td role="cell" className={styles.act}>
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
    </div>
  );
}
