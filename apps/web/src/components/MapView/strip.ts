/**
 * The map as a strip: what of the city it is fitted to, and whether it is one.
 *
 * On a screen of one column the map stands over the two ways in, before a search, so that
 * it is in sight whichever is chosen. It is low there, so that the box is on the first
 * screen too, and as wide as the page. A city drawn whole in a window that low is a small
 * thing in a great deal of water: measured at 390 wide, in a window 120 px high, it would
 * be 96 px across. So in a strip the city is drawn as wide as the window, and what lies
 * over and under its middle is out of sight, one press away.
 *
 * It is plain code with no state, kept apart from the map, which runs in the browser.
 */

import type { Bounds } from "@/lib/map/project";

/** The room left round the areas when the whole city is shown, in pixels. */
export const PADDING = 24;

/** The room left at either side of the city in a strip, which is as wide as the page. */
export const PADDING_OF_A_STRIP = 8;

/** How much of the height of the city a strip is fitted to, about its middle: so little that its width decides. */
const OF_ITS_HEIGHT = 1 / 50;

/** How wide and how high the window of the map is, in pixels. Nought where it is not laid out. */
export interface Window {
  readonly width: number;
  readonly height: number;
}

/** True of a window that is a strip: lower than half its width. One that is not laid out is none. */
export function isStrip({ width, height }: Window): boolean {
  return width > 0 && height > 0 && height * 2 < width;
}

/**
 * What the map is fitted to in a window, and the room left round it. In a strip it is a
 * band across the middle of the city, from its west to its east: fitted to that, the city
 * is as wide as the strip. In any other window it is the whole city.
 */
export function fitFor(city: Bounds, window: Window): { readonly bounds: Bounds; readonly padding: number } {
  if (!isStrip(window)) return { bounds: city, padding: PADDING };
  const [[west, south], [east, north]] = city;
  const middle = (south + north) / 2;
  const half = ((north - south) * OF_ITS_HEIGHT) / 2;
  return {
    bounds: [
      [west, middle - half],
      [east, middle + half],
    ],
    padding: PADDING_OF_A_STRIP,
  };
}
