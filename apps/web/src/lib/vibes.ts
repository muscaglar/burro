/**
 * Where an area sits on a vibe, read off what the API sent. docs/design/web.md, section 4.
 *
 * A vibe is said as a band, one of five, counted from its low end, and never
 * as a percentage, a score or a rank. Nothing here writes a sentence about a
 * place: it says a band in the words the page uses for one, and names the
 * ends of a vibe as the API names them.
 */

import { BAND_ON_A_SCALE, BAND_ONE_WAY, BAND_VARIES, type BandNumber } from "@/content/bands";
import { READING, READING_TOWARDS } from "@/content/labels";
import { TABLE } from "@/content/map";
import { STRIP } from "@/content/search";
import type { BandMark, StripMark, Tag, TermReading } from "@/lib/api/schema";

/** The bands a vibe is counted in, from its low end to its high end. */
export const VIBE_BANDS = [1, 2, 3, 4, 5] as const;

/** Where an area sits on a vibe: a band, and the bands it spans. All three are the API's. */
export type Placed = Pick<StripMark, "band" | "spread_low" | "spread_high">;

/** One vibe, and the band of every area on it, as route 4 served them with the page. */
export interface Lens {
  readonly tag: Tag;
  readonly marks: readonly BandMark[];
}

/** True when the area is drawn as a range: it spans three bands or more, and is no one point. */
export function isRange({ spread_low: low, spread_high: high }: Placed): boolean {
  return high - low >= 2;
}

/** The names of the two ends of a vibe: the API's for a scale, and "least" and "most" for one that runs one way. */
export function endsOf(tag: Pick<Tag, "low_end" | "high_end">): readonly [low: string, high: string] {
  return [tag.low_end ?? STRIP.least, tag.high_end ?? STRIP.most];
}

/**
 * How a part of a recipe is read, in words. A recipe places an area towards
 * the high end of its vibe, so a part of a scale says which end that is.
 */
export function readingOf(tag: Pick<Tag, "high_end">, reading: TermReading): string {
  return tag.high_end === null ? READING[reading] : READING_TOWARDS[reading](tag.high_end);
}

/** Where a mark sits, in words: what a person who sees the page reads from the track. */
export function inWords(placed: Placed): string {
  return isRange(placed) ? STRIP.bands(placed.spread_low, placed.spread_high) : STRIP.band(placed.band);
}

const isBandNumber = (band: number): band is BandNumber => (VIBE_BANDS as readonly number[]).includes(band);

/**
 * Where a mark sits, in words a person would use: "among the most here" for a
 * vibe that runs one way, and "towards Flats" for a scale, by the names the
 * API gives its ends. A mixed area is said to vary, and is never put at a
 * point. The band itself is said beside it, as `inWords` says it.
 *
 * `null` for what is no band, of which nothing is said.
 */
export function plainly(tag: Pick<Tag, "low_end" | "high_end">, placed: Placed): string | null {
  if (isRange(placed)) return BAND_VARIES;
  if (!isBandNumber(placed.band)) return null;
  return tag.low_end === null || tag.high_end === null
    ? BAND_ONE_WAY[placed.band]
    : BAND_ON_A_SCALE[placed.band](tag.low_end, tag.high_end);
}

/** How far a mark sits from the middle band, from 0 to 2. A mixed area is at no one point, and is 0. */
export function fromTheMiddle(placed: Placed): number {
  return isRange(placed) ? 0 : Math.abs(placed.band - 3);
}

/**
 * Where an area sits on the vibe the map is coloured by, in words. An area
 * the vibe cannot place is said to be so, and is never put in the middle.
 * `null` where the vibe says nothing of the area.
 */
export function placedOn(lens: Lens, areaId: string): string | null {
  const mark = lens.marks.find((one) => one.area_id === areaId);
  if (mark === undefined) return null;
  const { band, spread_low: low, spread_high: high } = mark;
  if (band === null || low === null || high === null) return TABLE.notPlaced;
  return inWords({ band, spread_low: low, spread_high: high });
}
