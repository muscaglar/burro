"use client";

import { COMPARE_TABLE } from "@/content/compare";
import { CRIME_ACCOUNT, type CrimeVibe } from "@/content/crime";
import { STRIP } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import type { CharacterMark, CompareData, ComparedArea, Fact, Tag } from "@/lib/api/schema";
import { endsOf, type Placed } from "@/lib/vibes";

import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./CompareTable.module.css";
import { VibeMark } from "./VibeMark";

interface Props {
  /** The comparison, from route 7: the band of each area on each vibe, and the fact behind each. */
  readonly data: Pick<CompareData, "areas" | "character" | "facts">;
  /** The vibes of the release, from route 11: their names and the names of their ends. */
  readonly tags: readonly Tag[];
  /** The vibes whose recipe holds recorded crime, with the parts of it that are of crime. */
  readonly crime?: readonly CrimeVibe[];
}

/** Where a mark says the area sits. `null` for an area the vibe cannot place. */
function placedBy({ band, spread_low: low, spread_high: high }: CharacterMark): Placed | null {
  return band === null || low === null || high === null ? null : { band, spread_low: low, spread_high: high };
}

interface CellProps {
  readonly mark: CharacterMark | undefined;
  readonly fact: Fact | undefined;
  readonly tag: Tag;
  readonly area: ComparedArea;
}

/**
 * Where one area sits on one vibe: a mark on the line, where it sits in words
 * a person would use, the band, and the source of both. An area the vibe
 * cannot place says so in two words: why is said once, over the table.
 */
function Cell({ mark, fact, tag, area }: CellProps) {
  const placed = mark === undefined ? null : placedBy(mark);
  return (
    // The role is the cell's own, said again because a narrow screen stacks the rows. The
    // rule takes any cell for one of a grid that can be pressed, which this is not.
    // eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role
    <td role="cell" className={`${styles.cell} ${styles.mark}`} data-placed={placed !== null}>
      <span className={styles.cellName} aria-hidden="true">
        {area.name}
      </span>
      {fact === undefined ? (
        // A mark with no fact behind it has no source and no date, and is not drawn.
        <p className={styles.none}>{COMPARE_TABLE.noFigure}</p>
      ) : (
        placed === null ? (
          // It is said to be so, and is never put in the middle. It holds no figure, so it has
          // no source to give: what is known of the area is on its own page.
          <p className={styles.none}>{COMPARE_TABLE.character.notPlaced}</p>
        ) : (
          <>
            <VibeMark tag={tag} placed={placed} fact={fact} />
            <SourceNote facts={[fact]} of={`${tag.label}, ${area.name}`} />
          </>
        )
      )}
    </td>
  );
}

/**
 * The vibes of each area, side by side: one row for each vibe the API
 * compares, in its order, and one column for each area. A scale is one line
 * with a mark for each area. It comes before the measured parts.
 *
 * Every band is the API's, and is shown as a band between two named ends,
 * never as a score. On a narrow screen each row is stacked, as the rows of
 * what counts are, and it stays a table to a screen reader either way.
 */
export function CharacterTable({ data, tags, crime = [] }: Props) {
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
      {unplaced.length === 0 ? null : (
        <div className={styles.unplaced}>
          {unplaced.map(({ area, count }) => (
            <p key={area.area_id}>{COMPARE_TABLE.character.unplaced(area.name, count, rows.length)}</p>
          ))}
          <p className={styles.why}>{COMPARE_TABLE.character.unplacedWhy}</p>
        </div>
      )}
      <Rows data={data} rows={rows} facts={facts} crime={crime} />
    </>
  );
}

interface RowsProps extends Pick<Props, "data"> {
  readonly rows: readonly { readonly row: CompareData["character"][number]; readonly tag: Tag }[];
  readonly facts: ReadonlyMap<string, Fact>;
  readonly crime: readonly CrimeVibe[];
}

function Rows({ data, rows, facts, crime }: RowsProps) {
  return (
    <table role="table" className={`${styles.table} ${styles.character}`}>
      <caption>{COMPARE_TABLE.character.caption}</caption>
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
          return (
            <tr role="row" key={row.tag_id} className={styles.row}>
              <th role="rowheader" scope="row" className={styles.thing}>
                <span className={styles.label}>{tag.label}</span>
                <span className="visually-hidden">. </span>
                <span className={styles.weight}>{STRIP.from(low, high)}</span>
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
                return <Cell key={area.area_id} mark={mark} fact={fact} tag={tag} area={area} />;
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
