"use client";

import Link from "next/link";

import { COMPARE_STATUS, COMPARE_TABLE } from "@/content/compare";
import { CRIME_CAVEAT } from "@/content/settings";
import type { CompareCell, CompareData, CompareRow, ComparedArea, Fact } from "@/lib/api/schema";
import type { Chosen } from "@/lib/compare/list";
import { outOfHundred } from "@/lib/format";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { hundredths } from "@/lib/search/card";

import { columnsOf } from "../FactRow/FactRow";
import { Skeleton } from "../Skeleton/Skeleton";
import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./CompareTable.module.css";

/** Where an area stands in the search that is open: its place in the order, and its fit. */
export interface Standing {
  readonly rank: number;
  /** The fit out of 100, rounded down. `null` when nothing is set to rank by. */
  readonly fit: number | null;
}

interface Props {
  readonly data: CompareData;
}

interface AreasProps {
  /** The areas being compared, as the address names them. */
  readonly chosen: readonly Chosen[];
  /** What the API said of each, once it has answered. */
  readonly compared?: readonly ComparedArea[];
  /** True while the API is being waited for. */
  readonly waiting?: boolean;
  /** Where each area stands in the search that is open, by area id. Empty when none is. */
  readonly standings?: ReadonlyMap<string, Standing>;
}

/** The standing of each area in a ranking, by its id. */
export function standingsOf(
  scores: readonly { readonly area_id: string; readonly score: number }[],
  noFit: boolean,
): ReadonlyMap<string, Standing> {
  return new Map(
    scores.map((score, at) => [score.area_id, { rank: at + 1, fit: noFit ? null : fitOf(score.score) }]),
  );
}

function factsById(facts: readonly Fact[]): ReadonlyMap<string, Fact> {
  return new Map(facts.map((fact) => [fact.fact_id, fact]));
}

interface CellProps {
  readonly cell: CompareCell | undefined;
  readonly fact: Fact | undefined;
  readonly row: CompareRow;
  readonly area: ComparedArea;
}

/**
 * What one area has for one thing that counts. Every figure is a slot of the
 * fact, as the API formatted it, under the name of its column. The number in
 * the cell itself is not shown: it is the same figure unformatted, and the
 * percentile beside it is never printed.
 */
function Cell({ cell, fact, row, area }: CellProps) {
  const adds = hundredths(cell?.contribution ?? null);
  const columns = fact === undefined || fact.template === "missing" ? [] : columnsOf(fact);
  return (
    // The role is the cell's own. It is said again because a narrow screen stacks the
    // rows, and a browser may then forget that a cell is a cell. The rule takes any
    // cell for one of a grid that can be pressed, which this is not.
    // eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role
    <td role="cell" className={styles.cell}>
      {/* On a narrow screen the rows are stacked, and each cell says whose it is. The
          column's heading says it to a screen reader, so this is kept from one. */}
      <span className={styles.cellName} aria-hidden="true">
        {area.name}
      </span>
      {columns.length > 0 && fact !== undefined ? (
        <>
          <dl className={styles.figures}>
            {columns.map(([column, value]) => (
              <div key={column}>
                <dt>{column}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          {adds !== null ? <p className={styles.adds}>{COMPARE_TABLE.adds(adds)}</p> : null}
          <SourceNote facts={[fact]} of={`${row.label}, ${area.name}`} />
        </>
      ) : (
        <p className={styles.none}>
          {cell === undefined || (cell.fact_id === null && area.status !== "ranked")
            ? COMPARE_TABLE.notScored
            : COMPARE_TABLE.noFigure}
        </p>
      )}
    </td>
  );
}

/**
 * The areas being compared, each with its status in words, where it stands
 * in the search that is open, a link to its page and a link that takes it
 * out. The names and the links are there before the API has answered, and
 * read with scripts off.
 */
export function CompareAreas({ chosen, compared = [], waiting = false, standings = new Map() }: AreasProps) {
  return (
    <ul className={styles.areas} aria-label={COMPARE_TABLE.areas}>
      {chosen.map((area) => {
        const said = compared.find((one) => one.area_id === area.area_id);
        const standing = standings.get(area.area_id);
        const others = chosen.filter((other) => other.area_id !== area.area_id);
        return (
          <li key={area.area_id} className={styles.area}>
            <p className={styles.areaName}>{area.name}</p>
            {/* The line has its place before it has its words, so that nothing moves when they come. */}
            <div className={styles.status}>
              {said !== undefined ? <p>{COMPARE_STATUS[said.status]}</p> : waiting ? <Skeleton /> : null}
              {said?.status === "ranked" && standing !== undefined ? (
                <p>{COMPARE_TABLE.standing(standing.rank, standing.fit)}</p>
              ) : null}
            </div>
            {/* A page is fetched when its link is pressed, and not before. */}
            <Link className={`${styles.link} target`} href={paths.area(area)} prefetch={false}>
              {COMPARE_TABLE.open(area.name)}
            </Link>
            {others.length > 0 ? (
              <Link
                className={`${styles.link} target`}
                href={paths.compare(others.map((other) => other.slug))}
                prefetch={false}
              >
                {COMPARE_TABLE.takeOut(area.name)}
              </Link>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

/**
 * Two to four areas side by side: one row for each thing that counts, in the
 * order the API gave them, which is the order of the weights from high to
 * low. One column for each area.
 *
 * On a narrow screen each row is stacked: the thing that counts, and under it
 * each area by name. It stays a table to a screen reader either way.
 */
export function CompareTable({ data }: Props) {
  const facts = factsById(data.facts);
  return (
    <div className={styles.compare}>
      <table role="table" className={styles.table}>
        <caption>{COMPARE_TABLE.caption}</caption>
        {/* The role is the group's own, said again as the rows' and the cells' are: stacked,
            a browser may forget what each part of a table is. */}
        {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
        <thead role="rowgroup" className={styles.head}>
          <tr role="row">
            <th role="columnheader" scope="col">
              {COMPARE_TABLE.what}
            </th>
            {data.areas.map((area) => (
              <th role="columnheader" key={area.area_id} scope="col">
                {area.name}
              </th>
            ))}
          </tr>
        </thead>
        {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
        <tbody role="rowgroup">
          {data.rows.map((row) => {
            const caveat = row.cells.some(
              (cell) => cell.fact_id !== null && facts.get(cell.fact_id)?.template === "feature_crime",
            );
            return (
              <tr role="row" key={row.component} className={styles.row}>
                <th role="rowheader" scope="row" className={styles.thing}>
                  {/* Each is a line of its own to the eye. The full stops part them for a screen reader. */}
                  <span className={styles.label}>{row.label}</span>
                  <span className="visually-hidden">. </span>
                  <span className={styles.weight}>
                    {COMPARE_TABLE.countsFor(Number(outOfHundred(row.weight)))}
                  </span>
                  {caveat ? (
                    <>
                      <span className="visually-hidden">. </span>
                      <span className={styles.caveat}>{CRIME_CAVEAT}</span>
                    </>
                  ) : null}
                </th>
                {data.areas.map((area) => {
                  const cell = row.cells.find((one) => one.area_id === area.area_id);
                  const fact = cell?.fact_id == null ? undefined : facts.get(cell.fact_id);
                  return <Cell key={area.area_id} cell={cell} fact={fact} row={row} area={area} />;
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
