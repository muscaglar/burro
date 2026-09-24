/**
 * What the map shows of each area: the band its fit falls in, and the pattern
 * that says it has no rank. docs/design/web.md, section 6.
 *
 * Colour is never the only signal. A band is a range of fit that the legend
 * gives in figures; a pattern goes with a reason given in words; and the rank
 * itself is a number, in the pin and in the order of the list.
 */

import type { Filtered, Score, Unranked } from "@/lib/api/schema";

/** 0 is an area with no fit to show. 1 to 5 are the bands, from low to high. */
export type Band = 0 | 1 | 2 | 3 | 4 | 5;

/** Lines on an area a limit left out, dots on one that is not ranked. */
export type Pattern = "none" | "filtered" | "unranked";

export interface Fill {
  readonly band: Band;
  readonly pattern: Pattern;
}

/** How wide a band is, in points of fit. */
export const BAND_WIDTH = 20;

/** The five bands, low to high, each with the range of fit it stands for. */
export const BANDS: readonly { readonly band: Exclude<Band, 0>; readonly from: number; readonly to: number }[] = [
  { band: 1, from: 0, to: 19 },
  { band: 2, from: 20, to: 39 },
  { band: 3, from: 40, to: 59 },
  { band: 4, from: 60, to: 79 },
  { band: 5, from: 80, to: 100 },
];

/**
 * A fit as the page shows it: a whole number from 0 to 100, rounded down, so
 * that a fit is never said to be more than it is and always falls in the
 * band the legend gives for it.
 */
export function fitOf(score: number): number {
  if (!Number.isFinite(score)) return 0;
  return Math.min(100, Math.max(0, Math.floor(score)));
}

export function bandOf(score: number): Exclude<Band, 0> {
  const fit = fitOf(score);
  const found = BANDS.find(({ from, to }) => fit >= from && fit <= to);
  return found?.band ?? 1;
}

/** How many areas a pin is drawn for. */
export const PINS = 10;

/**
 * The fill of every area the ranking speaks of, by area id. An area it says
 * nothing of has no entry, and is drawn as land with no fit.
 *
 * With nothing set to rank by every area scores 0, which is no fit at all,
 * so none is given a band.
 */
export function fillFor(
  scores: readonly Score[],
  filtered: readonly Filtered[],
  unranked: readonly Unranked[],
  emptySpec = false,
): ReadonlyMap<string, Fill> {
  const fills = new Map<string, Fill>();
  for (const { area_id: areaId, score } of scores) {
    fills.set(areaId, { band: emptySpec ? 0 : bandOf(score), pattern: "none" });
  }
  for (const { area_id: areaId } of filtered) fills.set(areaId, { band: 0, pattern: "filtered" });
  for (const { area_id: areaId } of unranked) fills.set(areaId, { band: 0, pattern: "unranked" });
  return fills;
}

/** The ids of the areas drawn with each band, and with each pattern. */
export function idsBy(fills: ReadonlyMap<string, Fill>) {
  const bands: Record<Band, string[]> = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [] };
  const patterns: Record<Pattern, string[]> = { none: [], filtered: [], unranked: [] };
  for (const [areaId, { band, pattern }] of fills) {
    bands[band].push(areaId);
    patterns[pattern].push(areaId);
  }
  return { bands, patterns };
}
