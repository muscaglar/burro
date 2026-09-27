"use client";

import { useId } from "react";

import { COMPARE_TABLE } from "@/content/compare";
import { CRIME_ACCOUNT, type CrimeVibe } from "@/content/crime";
import { FACT_COLUMNS } from "@/content/facts";
import { CRIME_CAVEAT } from "@/content/settings";
import type { CharacterMark, CompareData, ComparedArea, Fact, Tag } from "@/lib/api/schema";
import { endsOf, type Placed } from "@/lib/vibes";

import { Ends } from "../kit/Ends/Ends";
import { holdsAFigure } from "../kit/reads";
import { Thing } from "../kit/Thing/Thing";
import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./CompareTable.module.css";
import { ENDS_STAND, UNDER_A_GAUGE, type EndsStand, type UnderAGauge } from "./look";
import { VibeMark } from "./VibeMark";

interface Props {
  /** The comparison, from route 7: the band of each area on each vibe, and the fact behind each. */
  readonly data: Pick<CompareData, "areas" | "character" | "facts">;
  /** The vibes of the release, from route 11: their names and the names of their ends. */
  readonly tags: readonly Tag[];
  /** The vibes whose recipe holds recorded crime, with the parts of it that are of crime. */
  readonly crime?: readonly CrimeVibe[];
  /** What is said under the gauge of an area. Left out, it is what `look.ts` chooses. */
  readonly under?: UnderAGauge;
  /** Where the pictures of the two ends of a vibe stand. Left out, it is what `look.ts` chooses. */
  readonly ends?: EndsStand;
}

/** Where a mark says the area sits. `null` for an area the vibe cannot place. */
function placedBy({ band, spread_low: low, spread_high: high }: CharacterMark): Placed | null {
  return band === null || low === null || high === null ? null : { band, spread_low: low, spread_high: high };
}

interface CellProps extends Required<Pick<Props, "under" | "ends">> {
  readonly mark: CharacterMark | undefined;
  readonly fact: Fact | undefined;
  readonly tag: Tag;
  readonly area: ComparedArea;
}

/**
 * Where one area sits on one vibe: its gauge, and where it sits in words, which
 * are drawn under the gauge or are the name of its picture. An area the vibe
 * cannot place says so in two words: why is said once, over the table. The
 * source of a vibe is given once, in its row, for every area it places.
 */
function Cell({ mark, fact, tag, area, under, ends }: CellProps) {
  const placed = mark === undefined ? null : placedBy(mark);
  return (
    // The role is the cell's own, said again because a narrow screen lays the rows out as
    // blocks. The rule takes any cell for one of a grid that can be pressed, which this is not.
    // eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role
    <td role="cell" className={`${styles.cell} ${styles.mark}`} data-placed={placed !== null}>
      <span className={styles.cellName} aria-hidden="true">
        {area.name}
      </span>
      {fact === undefined ? (
        // A mark with no fact behind it has no source and no date, and is not drawn.
        <p className={styles.none}>{COMPARE_TABLE.noFigure}</p>
      ) : placed === null ? (
        // It is said to be so, and is never put in the middle. It holds no figure, so it has
        // no source to give: what is known of the area is on its own page.
        <p className={styles.none}>{COMPARE_TABLE.character.notPlaced}</p>
      ) : (
        <VibeMark tag={tag} placed={placed} fact={fact} under={under} ends={ends} />
      )}
    </td>
  );
}

/**
 * The vibes of each area, side by side: one row for each vibe the API
 * compares, in its order, and one column for each area. It is what a person
 * came to a comparison for, and comes before the measured parts.
 *
 * Every band is the API's, and is shown as a band between two named ends,
 * never as a score. No end is the better one, and no area is marked out: a
 * cell is drawn as the next is, whatever it holds.
 *
 * The small drawing of a vibe stands with its name, at the head of its row.
 * Each end of a gauge has its one picture, and the two are opposites: at
 * either end of every gauge, or once at the head of the row, over the names
 * of the two ends. `look.ts` has the line that chooses.
 *
 * The areas stand side by side on a narrow screen too: the vibe has a line of
 * its own, and under it each area has a column, under its own name. It stays
 * a table to a screen reader either way. The source of a vibe is given once
 * in its row, of every area it places: their facts are of one recipe and one
 * date. Every vibe is drawn as the next is.
 *
 * The head of a row is named by its vibe and by nothing else, so that a cell
 * is read under the name of its vibe: named by all that it holds, a head was
 * its ends, its source and its notes as well, before every cell of its row.
 * What else it holds is read in it.
 *
 * What the table is called is kept for whoever hears the page: the heading
 * over it and the line under the heading say it to whoever sees it.
 */
export function CharacterTable({ data, tags, crime = [], under = UNDER_A_GAUGE, ends = ENDS_STAND }: Props) {
  const facts = new Map(data.facts.map((fact) => [fact.fact_id, fact]));
  const rows = data.character.flatMap((row) => {
    const tag = tags.find((one) => one.tag_id === row.tag_id);
    return tag === undefined ? [] : [{ row, tag }];
  });
  if (rows.length === 0) return null;
  // What Burro cannot place an area on is said once for the area, and not in every row.
  const unplaced = data.areas.flatMap((area) => {
    const count = rows.filter(({ row }) => {
      const mark = row.marks.find((one) => one.area_id === area.area_id);
      return mark !== undefined && facts.has(mark.fact_id) && placedBy(mark) === null;
    }).length;
    return count === 0 ? [] : [{ area, count }];
  });
  return (
    <>
      {/* What a vibe is, and how a line of five steps is read: said once, where a person first meets one. */}
      <p className={styles.lead}>{COMPARE_TABLE.character.lead}</p>
      <Rows data={data} rows={rows} facts={facts} crime={crime} under={under} ends={ends} />
      {/* Under the vibes, so that where the areas sit comes first: a cell says in two words
          that an area is not placed, and why is said here, once for all of them. */}
      {unplaced.length === 0 ? null : (
        <div className={styles.unplaced}>
          {unplaced.map(({ area, count }) => (
            <p key={area.area_id}>{COMPARE_TABLE.character.unplaced(area.name, count, rows.length)}</p>
          ))}
          <p className={styles.why}>{COMPARE_TABLE.character.unplacedWhy}</p>
        </div>
      )}
    </>
  );
}

interface RowsProps extends Pick<Props, "data">, Required<Pick<Props, "under" | "ends">> {
  readonly rows: readonly { readonly row: CompareData["character"][number]; readonly tag: Tag }[];
  readonly facts: ReadonlyMap<string, Fact>;
  readonly crime: readonly CrimeVibe[];
}

function Rows({ data, rows, facts, crime, under, ends }: RowsProps) {
  const id = useId();
  return (
    // It says how many areas stand side by side, so that what is drawn in a cell has room where they are four.
    <table
      role="table"
      className={`${styles.table} ${styles.character}`}
      data-areas={data.areas.length}
      data-under={under}
      data-ends={ends}
    >
      <caption className="visually-hidden">{COMPARE_TABLE.character.caption}</caption>
      {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
      <thead role="rowgroup" className={styles.head}>
        <tr role="row">
          <th role="columnheader" scope="col">
            {COMPARE_TABLE.character.what}
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
        {rows.map(({ row, tag }) => {
          const [low, high] = endsOf(tag);
          const counted = crime.find((one) => one.tag.tag_id === tag.tag_id)?.parts ?? [];
          // The facts behind the marks of the row, of each area the vibe places: a mark that
          // places no area holds no figure, and has no source to give.
          const behind = row.marks.flatMap((mark) => {
            const fact = facts.get(mark.fact_id);
            return fact === undefined || placedBy(mark) === null ? [] : [fact];
          });
          return (
            <tr role="row" key={row.tag_id} className={styles.row}>
              <th role="rowheader" scope="row" className={styles.thing} aria-labelledby={`${id}-${row.tag_id}`}>
                <span className={styles.named}>
                  {/* The drawing of the vibe is dress, and says nothing: its name is beside it. */}
                  <Thing kind="tag" id={tag.tag_id} family={tag.family} />
                  {/* The name of a vibe is a short label. One that holds a figure is read exactly. */}
                  <span id={`${id}-${row.tag_id}`} className={styles.label} data-reads={holdsAFigure(tag.label)}>
                    {tag.label}
                  </span>
                </span>
                <span className="visually-hidden">. </span>
                {ends === "row" ? (
                  // Its two ends, each under its picture, the low end first as the steps run.
                  <span className={styles.ends}>
                    <span className="visually-hidden">{FACT_COLUMNS.ends} </span>
                    <Ends id={tag.tag_id} low={tag.low_end} high={tag.high_end}>
                      {/* The spaces are for whoever hears the page: the three are laid out apart. */}
                      <span className={styles.to}> {FACT_COLUMNS.to} </span>
                    </Ends>
                  </span>
                ) : (
                  <span className={styles.weight}>{COMPARE_TABLE.character.ends(low, high)}</span>
                )}
                {behind.length === 0 ? null : (
                  // Once for the row: the recipe, its sources and the date of the bands of the row.
                  <div className={styles.source}>
                    <SourceNote facts={behind} of={tag.label} />
                  </div>
                )}
                {counted.length === 0 ? null : (
                  // A vibe that counts recorded crime says so, with the caveat of every such figure.
                  <>
                    <span className="visually-hidden">. </span>
                    <span className={styles.caveat}>
                      {CRIME_ACCOUNT.counts}: {counted.map((part) => part.label).join("; ")}. {CRIME_CAVEAT}
                    </span>
                  </>
                )}
              </th>
              {data.areas.map((area) => {
                const mark = row.marks.find((one) => one.area_id === area.area_id);
                const fact = mark === undefined ? undefined : facts.get(mark.fact_id);
                return <Cell key={area.area_id} mark={mark} fact={fact} tag={tag} area={area} under={under} ends={ends} />;
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
