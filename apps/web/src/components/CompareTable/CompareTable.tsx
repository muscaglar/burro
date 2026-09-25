"use client";

import Link from "next/link";

import { COMPARE_TABLE, statusWords } from "@/content/compare";
import { COMBINE } from "@/content/labels";
import { roughOf, saidOf } from "@/content/rough";
import { CRIME_CAVEAT } from "@/content/settings";
import type { Combine, CompareData, ComparedArea, RoughGuide, Tag } from "@/lib/api/schema";
import { placedBy } from "@/lib/area/portrait";
import type { Chosen } from "@/lib/compare/list";
import { drawnRows, type DrawnCell, type DrawnRow } from "@/lib/compare/rows";
import { outOfHundred } from "@/lib/format";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { hundredths } from "@/lib/search/card";

import { columnsOf } from "../FactRow/FactRow";
import { Skeleton } from "../Skeleton/Skeleton";
import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./CompareTable.module.css";
import { VibeMark } from "./VibeMark";

/** Where an area stands in the search that is open: its place in the order, and its fit. */
export interface Standing {
  readonly rank: number;
  /** The fit out of 100, rounded down. `null` when nothing is set to rank by. */
  readonly fit: number | null;
}

interface Props {
  readonly data: CompareData;
  /** Which journey counts where the search names two places or more: the spec's own choice. */
  readonly combine?: Combine;
  /** The vibes of the release, from route 11: the names of their ends. */
  readonly tags?: readonly Tag[];
  /** What each vibe that is a rough guide says of itself, from route 11. */
  readonly guides?: readonly RoughGuide[];
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

interface CellProps {
  readonly drawn: DrawnCell;
  readonly row: DrawnRow;
  readonly tags: readonly Tag[];
}

/**
 * What one area has for one thing that counts. Every figure is a slot of the
 * fact, as the API formatted it, under the name of its column. The number in
 * the cell itself is not shown: it is the same figure unformatted, and the
 * percentile beside it is never printed.
 */
function Cell({ drawn, row, tags }: CellProps) {
  const { area, cell, fact } = drawn;
  const adds = hundredths(cell?.contribution ?? null);
  // A vibe is drawn as it is everywhere: a mark on its line, and where the area sits in words.
  const tag = fact?.kind === "tag" ? tags.find((one) => one.tag_id === fact.key) : undefined;
  const placed = fact === undefined || tag === undefined ? null : placedBy(fact);
  // A fact that says a journey has no time holds no figure: it is said in words, with its source.
  const noTime = fact?.template === "missing_journey";
  const columns = fact === undefined || fact.template === "missing" || noTime ? [] : columnsOf(fact);
  const of = `${row.place === null ? row.row.label : `${row.row.label}, ${row.place}`}, ${area.name}`;
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
      {fact !== undefined && tag !== undefined ? (
        <>
          {placed === null ? (
            // It is said to be so, and is never put in the middle.
            <p className={styles.none}>{COMPARE_TABLE.character.notPlaced}</p>
          ) : (
            <VibeMark tag={tag} placed={placed} fact={fact} />
          )}
          {adds !== null ? <p className={styles.adds}>{COMPARE_TABLE.adds(adds)}</p> : null}
          <SourceNote facts={[fact]} of={of} />
        </>
      ) : columns.length > 0 && fact !== undefined ? (
        <>
          <dl className={styles.figures}>
            {columns
              // The row says where a journey is to, so its cells do not say it again.
              .filter(([, value]) => !(row.journey && value === row.place))
              .map(([column, value]) => (
                <div key={column}>
                  <dt>{column}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
          </dl>
          {adds !== null ? <p className={styles.adds}>{COMPARE_TABLE.adds(adds)}</p> : null}
          <SourceNote facts={[fact]} of={of} />
        </>
      ) : noTime && fact !== undefined ? (
        <>
          <p className={styles.none}>{COMPARE_TABLE.journeys.missing}</p>
          <SourceNote facts={[fact]} of={of} />
        </>
      ) : (
        <p className={styles.none}>
          {cell === undefined || (cell.fact_id === null && area.status !== "ranked")
            ? COMPARE_TABLE.notScored
            : row.journey
              ? COMPARE_TABLE.journeys.missing
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
              {/* A status the website has no words for is left out, and never shown as its code. */}
              {said !== undefined ? <p>{statusWords(said.status)}</p> : waiting ? <Skeleton /> : null}
              {said?.status === "ranked" && standing !== undefined ? (
                <p>{COMPARE_TABLE.standing(standing.rank, standing.fit)}</p>
              ) : null}
              {/* A fit never stands alone where it rests on part of what counts. The API says how much. */}
              {said?.status === "ranked" && said.present < said.counted ? (
                <p className={styles.part} data-part="true">
                  <span className={styles.partMark} aria-hidden="true" />
                  <span>
                    {COMPARE_TABLE.basedOn(said.present, said.counted)}
                    {/* Where there is a fit to trust the less for it, it is said so. */}
                    {standing !== undefined && standing.fit !== null ? `. ${COMPARE_TABLE.restsOnPart}` : null}
                  </span>
                </p>
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
 * low. One column for each area. A journey has a row for each place, with
 * the same destination across the row. The journeys count as one thing, so
 * what they count for, and which of them counts, is said once, under the
 * first of their rows.
 *
 * On a narrow screen each row is stacked: the thing that counts, and under it
 * each area by name. It stays a table to a screen reader either way.
 */
export function CompareTable({ data, combine, tags = [], guides = [] }: Props) {
  const rows = drawnRows(data);
  const journeys = rows.filter((row) => row.journey).length;
  return (
    <div className={styles.compare}>
      <p className={styles.weights}>{COMPARE_TABLE.weights}</p>
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
          {rows.map((row, at) => {
            const caveat = row.cells.some(({ fact }) => fact?.template === "feature_crime");
            // The first of the rows of journeys says which of them counts, where there are two or more.
            const firstJourney = row.journey && rows.findIndex((one) => one.journey) === at;
            const several = firstJourney && journeys > 1 && combine !== undefined;
            const notes = [
              // What the journeys count for is the weight of them all, and is said once.
              row.first ? COMPARE_TABLE.countsFor(Number(outOfHundred(row.row.weight))) : null,
              several ? COMBINE[combine] : null,
              // Where every journey counts, the API gives what they add for none of them.
              several && combine === "mean" ? COMPARE_TABLE.journeys.together : null,
            ].filter((note): note is string => note !== null);
            // A vibe that was asked for and is a rough guide says so in its row, and why.
            const vibe = tags.find((tag) => `tag:${tag.tag_id}` === row.row.component);
            const rough = vibe === undefined ? null : roughOf(vibe, { rough_guides: guides });
            return (
              <tr role="row" key={row.key} className={styles.row}>
                <th role="rowheader" scope="row" className={styles.thing}>
                  {/* Each is a line of its own to the eye. The full stops part them for a screen reader. */}
                  <span className={styles.label}>{row.row.label}</span>
                  {row.place === null ? null : (
                    <>
                      <span className="visually-hidden">. </span>
                      <span className={styles.place}>{COMPARE_TABLE.journeys.to(row.place)}</span>
                    </>
                  )}
                  {notes.map((note) => (
                    <span key={note}>
                      <span className="visually-hidden">. </span>
                      <span className={styles.weight}>{note}</span>
                    </span>
                  ))}
                  {caveat ? (
                    <>
                      <span className="visually-hidden">. </span>
                      <span className={styles.caveat}>{CRIME_CAVEAT}</span>
                    </>
                  ) : null}
                  {rough === null ? null : (
                    <>
                      <span className="visually-hidden">. </span>
                      <span className={styles.caveat} data-rough-guide="note">
                        {saidOf(rough)}
                      </span>
                    </>
                  )}
                </th>
                {row.cells.map((drawn) => (
                  <Cell key={drawn.area.area_id} drawn={drawn} row={row} tags={tags} />
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
