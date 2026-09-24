/**
 * The areas a person has chosen to compare: two to four, in the order they
 * were chosen. docs/design/web.md, section 2.
 *
 * It is held in memory and nowhere else. It holds what the API said of an
 * area, its id, its slug and its name, and nothing a person typed.
 */

import type { AreaSummary } from "@/lib/api/schema";

/** The fewest and the most areas a comparison takes. The API refuses any other number. */
export const LEAST_COMPARED = 2;
export const MOST_COMPARED = 4;

/** What is kept of an area that was chosen: enough to name it, to link to it and to ask for it. */
export type Chosen = Pick<AreaSummary, "area_id" | "slug" | "name">;

export function isChosen(list: readonly Chosen[], areaId: string): boolean {
  return list.some((area) => area.area_id === areaId);
}

/** True when the list holds as many areas as a comparison takes. */
export function isFull(list: readonly Chosen[]): boolean {
  return list.length >= MOST_COMPARED;
}

/** True when the list holds enough areas to compare. */
export function isEnough(list: readonly Chosen[]): boolean {
  return list.length >= LEAST_COMPARED && list.length <= MOST_COMPARED;
}

/** The list with the area taken out if it was in, and put in if it was not and there is room. */
export function toggled(list: readonly Chosen[], area: Chosen): readonly Chosen[] {
  if (isChosen(list, area.area_id)) return list.filter((one) => one.area_id !== area.area_id);
  if (isFull(list)) return list;
  // Only what is needed is kept: a whole summary holds more.
  return [...list, { area_id: area.area_id, slug: area.slug, name: area.name }];
}

/**
 * The slugs a comparison's address names, as the areas they are: in the order
 * given, with no repeat, none the release lacks, and no more than four. A
 * slug that names no area is counted and never kept.
 */
export function chosenFrom(
  slugs: readonly string[],
  areas: readonly AreaSummary[],
): { readonly chosen: readonly Chosen[]; readonly unknown: number; readonly dropped: number } {
  const chosen: Chosen[] = [];
  let unknown = 0;
  let dropped = 0;
  for (const slug of slugs) {
    const area = areas.find((one) => one.slug === slug);
    if (area === undefined) unknown += 1;
    else if (isChosen(chosen, area.area_id)) continue;
    else if (isFull(chosen)) dropped += 1;
    else chosen.push({ area_id: area.area_id, slug: area.slug, name: area.name });
  }
  return { chosen, unknown, dropped };
}
