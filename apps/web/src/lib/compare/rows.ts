/**
 * The rows of what counts in a comparison, as they are drawn. docs/design/web.md, section 2.
 *
 * A row is the API's, and is drawn as it came. A search may name two places or more, and the
 * API sends one row for each journey, with the same destination across the row: every area
 * has a cell in it, which cites the time of that journey or the fact that says there is none.
 * The journeys count as one thing, so each of their rows holds the same weight, and it is
 * said once, under the first of them.
 *
 * Nothing here writes a word about a place. The name of a place is the API's.
 */

import type { CompareCell, CompareData, ComparedArea, CompareRow, Fact } from "@/lib/api/schema";

export interface DrawnCell {
  readonly area: ComparedArea;
  /** The cell the API sent for the area in this row. */
  readonly cell: CompareCell | undefined;
  /** The fact the cell cites, where it cites one and the fact came. */
  readonly fact: Fact | undefined;
}

export interface DrawnRow {
  /** A name of its own, so that no row is drawn over another. It is never shown. */
  readonly key: string;
  readonly row: CompareRow;
  readonly journey: boolean;
  /** The place a journey is to, by the name the API gives it. `null` for any other row. */
  readonly place: string | null;
  /** False for a row of journeys after the first: what the journeys count for was said over it. */
  readonly first: boolean;
  readonly cells: readonly DrawnCell[];
}

/** True for the row of a journey: it is the one kind of row that names a place. */
export function isJourney(row: Pick<CompareRow, "place">): boolean {
  return row.place !== null;
}

/** The rows of a comparison, in the order the API gave them, each with a cell for each area. */
export function drawnRows(data: Pick<CompareData, "areas" | "rows" | "facts">): readonly DrawnRow[] {
  const facts = new Map(data.facts.map((fact) => [fact.fact_id, fact]));
  const firstJourney = data.rows.findIndex(isJourney);
  return data.rows.map((row, at) => ({
    key: `${at} ${row.component}`,
    row,
    journey: isJourney(row),
    place: row.place?.name ?? null,
    first: !isJourney(row) || at === firstJourney,
    cells: data.areas.map((area) => {
      const cell = row.cells.find((one) => one.area_id === area.area_id);
      return { area, cell, fact: cell?.fact_id == null ? undefined : facts.get(cell.fact_id) };
    }),
  }));
}
