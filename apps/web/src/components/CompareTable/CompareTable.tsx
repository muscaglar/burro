"use client";

import Link from "next/link";
import { useId, type MouseEvent, type RefObject } from "react";

import { COMPARE_TABLE, statusWords } from "@/content/compare";
import { COMBINE } from "@/content/labels";
import { CRIME_CAVEAT } from "@/content/settings";
import { TOWNS } from "@/content/towns";
import type { Combine, CompareData, ComparedArea, Tag } from "@/lib/api/schema";
import { placedBy } from "@/lib/area/portrait";
import type { Chosen } from "@/lib/compare/list";
import { drawnRows, type DrawnCell, type DrawnRow } from "@/lib/compare/rows";
import { outOfHundred } from "@/lib/format";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { hundredths } from "@/lib/search/card";

import { columnsOf } from "../FactRow/FactRow";
import { Approx } from "../kit/Approx/Approx";
import { Art } from "../kit/Art/Art";
import { Frame } from "../kit/Frame/Frame";
import { holdsAFigure } from "../kit/reads";
import { Thing } from "../kit/Thing/Thing";
import { Skeleton } from "../Skeleton/Skeleton";
import { SourceNote } from "../SourceNote/SourceNote";
import { Town } from "../Town/Town";
import styles from "./CompareTable.module.css";
import { HEADS_SAY_OF_THEIR_TOWNS, type HeadsSayOfTheirTowns } from "./look";
import { marksFor, type Towns } from "./towns";
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
  /**
   * True where the areas are given a fit, as they are where a search is open that ranks
   * them. Where one of them then has a figure for part of what counts, what follows from
   * that for its fit is said once, over the table.
   */
  readonly fits?: boolean;
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
  /**
   * What the town of each area is drawn from. With it in hand every area has its town at
   * its head, under its name, all of one size. Left out, no town is drawn.
   */
  readonly towns?: Towns;
  /** Where each area sits on each vibe, as the comparison says it, once it has answered. */
  readonly character?: CompareData["character"];
  /**
   * The head of the page, which takes the focus where an area is taken out and none is
   * left to take it. It is no stop of its own.
   */
  readonly head?: RefObject<HTMLElement | null>;
  /** What is said of the towns, where any is drawn. Left out, it is what `look.ts` chooses, which is nothing. */
  readonly saysOfTowns?: HeadsSayOfTheirTowns;
}

/**
 * The name of the area that takes the focus when this one is taken out: of the area that
 * stood after it, or else of the one before. `null` where it was the only area.
 */
function nameBeside(item: HTMLElement | null): HTMLElement | null {
  const all = [...(item?.parentElement?.children ?? [])];
  const at = item === null ? -1 : all.indexOf(item);
  if (at < 0) return null;
  for (const other of [...all.slice(at + 1), ...all.slice(0, at).reverse()]) {
    // The first way on of an area is its name, which leads to its page.
    const name = other.querySelector<HTMLElement>("a");
    if (name !== null) return name;
  }
  return null;
}

/** True of a press that opens what a link leads to elsewhere, in another tab or window: this page then stays as it is. */
const opensElsewhere = (event: MouseEvent) =>
  event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;

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
 * The areas being compared, at the head of the comparison: each with its name, its town,
 * its status in words, where it stands in the search that is open, and the way that takes
 * it out. The name of an area leads to its page. The names and the links are there before
 * the API has answered, and read with scripts off.
 *
 * They stand side by side in one plain edge of ink, each in a column of its own, and on a
 * wide screen over the column the area has in the tables under them: so the eye goes down
 * from a town to where its area sits on each vibe. What a town is, is not said here: it is
 * said in the key to the drawings and at the head of the page of an area. One line of the
 * look has it said once, of every town of the comparison, before the first of them.
 *
 * Every area is drawn as the next is: its name in the face of names, its town under it, of
 * one size, and its way out. Nobody wins a comparison. Where an area stands in a search is
 * said in words, the same way of each, and nothing marks one area out: no colour, no size,
 * no pennant, and no order but the order the address names them in.
 *
 * The way that takes an area out goes with its area, once the comparison of the others has
 * come. So it hands the focus on as it is pressed, to the name of the area beside it, which
 * stays: the focus is never left on nothing. The page is not moved under the press.
 *
 * Where no area is chosen nothing is drawn: a frame with nothing in it says nothing.
 */
export function CompareAreas({
  chosen,
  compared = [],
  waiting = false,
  standings = new Map(),
  towns,
  character,
  head,
  saysOfTowns = HEADS_SAY_OF_THEIR_TOWNS,
}: AreasProps) {
  if (chosen.length === 0) return null;
  /** Gives the focus to what stays, before what has it goes. */
  const handOn = (event: MouseEvent<HTMLElement>) => {
    if (opensElsewhere(event)) return;
    (nameBeside(event.currentTarget.closest("li")) ?? head?.current)?.focus({ preventScroll: true });
  };
  return (
    <Frame
      kind="plain"
      bare
      className={styles.heads}
      data-areas={chosen.length}
      data-towns={towns !== undefined}
      data-says={saysOfTowns}
    >
      {/* Where the look has it said: what a town is, and that it is no picture of the place,
          once, before the first of them. */}
      {towns === undefined || saysOfTowns !== "line" ? null : <p className={styles.towns}>{TOWNS.line}</p>}
      <ul className={styles.areas} aria-label={COMPARE_TABLE.areas}>
        {chosen.map((area) => {
          const said = compared.find((one) => one.area_id === area.area_id);
          const standing = standings.get(area.area_id);
          const others = chosen.filter((other) => other.area_id !== area.area_id);
          return (
            <li key={area.area_id} className={styles.area}>
              <p className={styles.areaName}>
                {/* One press from the name of an area to its page, as from the name of a result.
                    The page is fetched when the link is pressed, and not before. */}
                <Link
                  className={`${styles.toArea} target-min`}
                  href={paths.area(area)}
                  prefetch={false}
                  aria-label={COMPARE_TABLE.open(area.name)}
                >
                  {area.name}
                </Link>
              </p>
              {/* The town comes after the name. */}
              {towns === undefined ? null : (
                <Town
                  marks={marksFor(area.area_id, towns.marks, character)}
                  meta={towns.meta}
                  of={area.name}
                  className={styles.town}
                />
              )}
              {/* The line has its place before it has its words, so that nothing moves when they come. */}
              <div className={styles.status}>
                {/* A status the website has no words for is left out, and never shown as its code. */}
                {said !== undefined ? <p>{statusWords(said.status)}</p> : waiting ? <Skeleton /> : null}
                {said?.status === "ranked" && standing !== undefined ? (
                  <p>{COMPARE_TABLE.standing(standing.rank, standing.fit)}</p>
                ) : null}
                {/* A fit never stands alone where it rests on part of what counts. It says so as
                    a result does, in the two words after the mark of what is not whole, and the
                    API says how much. */}
                {said?.status === "ranked" && said.present < said.counted ? (
                  <p className={styles.part} data-part="true">
                    <Approx />
                    <span className="visually-hidden">. </span>
                    {/* What follows from it for a fit is said once, over what counts. */}
                    <span className={styles.onPart}>{COMPARE_TABLE.basedOn(said.present, said.counted)}.</span>
                  </p>
                ) : null}
              </div>
              {others.length > 0 ? (
                <p className={styles.ways}>
                  {/* It leads to the comparison of the others, which is fetched when it is pressed. */}
                  <Link
                    className={`${styles.takeOut} target-min`}
                    href={paths.compare(others.map((other) => other.slug))}
                    prefetch={false}
                    aria-label={COMPARE_TABLE.takeOut(area.name)}
                    onClick={handOn}
                  >
                    <span className={styles.cross}>
                      <Art name="ui-cross" alt="" />
                    </span>
                    {COMPARE_TABLE.takeOutShort}
                  </Link>
                </p>
              ) : null}
            </li>
          );
        })}
      </ul>
    </Frame>
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
 *
 * The head of a row is named by what counts, and by where a journey is to:
 * a cell is read under that name. What else the head holds, how much the
 * thing counts and what is said of it, is read in the head.
 */
export function CompareTable({ data, combine, tags = [], fits = false }: Props) {
  const id = useId();
  const rows = drawnRows(data);
  const journeys = rows.filter((row) => row.journey).length;
  // A fit never stands alone where it rests on part of what counts: the head of the area
  // says how much, and what follows from it is said here, once for all of them.
  const onPart = fits && data.areas.some((area) => area.status === "ranked" && area.present < area.counted);
  return (
    <div className={styles.compare}>
      <p className={styles.weights}>{COMPARE_TABLE.weights}</p>
      {onPart ? <p className={styles.weights}>{COMPARE_TABLE.restsOnPart}</p> : null}
      {/* It says how many areas stand side by side, so that what is drawn in a cell has room where they are four. */}
      <table role="table" className={styles.table} data-areas={data.areas.length}>
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
            // The name of a measure runs to a sentence, and words that hold a figure are read exactly.
            const reads = row.row.component.startsWith("feature:") || holdsAFigure(row.row.label);
            const named = `${id}-${at}`;
            // A row of a vibe is a row of gauges, and the small drawing of the vibe stands with its name.
            const vibe = tags.find((tag) => row.cells.some(({ fact }) => fact?.kind === "tag" && fact.key === tag.tag_id));
            return (
              <tr role="row" key={row.key} className={styles.row}>
                <th
                  role="rowheader"
                  scope="row"
                  className={styles.thing}
                  aria-labelledby={row.place === null ? named : `${named} ${named}-to`}
                >
                  {/* Each is a line of its own to the eye. The full stops part them for a screen reader. */}
                  <span className={styles.named}>
                    {/* The drawing is dress, and says nothing: the name beside it is the API's. */}
                    {vibe === undefined ? null : <Thing kind="tag" id={vibe.tag_id} family={vibe.family} />}
                    <span id={named} className={styles.label} data-reads={reads}>
                      {row.row.label}
                    </span>
                  </span>
                  {row.place === null ? null : (
                    <>
                      <span className="visually-hidden">. </span>
                      <span id={`${named}-to`} className={styles.place}>
                        {COMPARE_TABLE.journeys.to(row.place)}
                      </span>
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
