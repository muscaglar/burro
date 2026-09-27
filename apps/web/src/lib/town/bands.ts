/**
 * The four bands a town is drawn from, read off what the service sent.
 *
 * A band is one of five, counted from the low end of its vibe. It is known only where the
 * service gives one. A release that does not hold the vibe, an area the vibe cannot place
 * and a band that would rest on too little of its recipe all come with no band, and are
 * all read as not known. Nothing is worked out here, and nothing is filled in.
 */

import type { BandNumber } from "@/content/bands";
import type { TagValue, VibeBands } from "@/lib/api/schema";
import { VIBE_BANDS } from "@/lib/vibes";

import { DRAWN_FROM, type Part } from "./vibes";

/**
 * Where an area sits on one vibe, as the service sends it: with the page of an area, with
 * the bands of every area, or in the strip of a result. Any of the three may be handed over.
 */
export type Mark = Pick<TagValue, "tag_id" | "band" | "spread_low" | "spread_high">;

/** The band of each part of a town. `null` where it is not known. */
export type Bands = Readonly<Record<Part, BandNumber | null>>;

/** A town of which nothing is known. */
export const NOTHING_KNOWN: Bands = { trees: null, height: null, lit: null, roofs: null };

const isBand = (band: number | null | undefined): band is BandNumber =>
  (VIBE_BANDS as readonly (number | null | undefined)[]).includes(band);

/** Where the area sits on the vibe a part is drawn from. `undefined` where the service said nothing of it. */
export function markOf(marks: readonly Mark[], part: Part): Mark | undefined {
  return marks.find((mark) => mark.tag_id === DRAWN_FROM[part]);
}

/**
 * The four bands of an area, of all that the service sent of it. Whatever else it sent is
 * not read: a town is drawn from these four and from nothing more.
 */
export function bandsOf(marks: readonly Mark[]): Bands {
  const bandOf = (part: Part) => {
    const band = markOf(marks, part)?.band;
    return isBand(band) ? band : null;
  };
  return { trees: bandOf("trees"), height: bandOf("height"), lit: bandOf("lit"), roofs: bandOf("roofs") };
}

/**
 * Where one area sits on each vibe, from the bands of every area, which the service sends
 * with the search page. A vibe that says nothing of the area is left out.
 */
export function marksOf(bands: readonly VibeBands[], areaId: string): readonly Mark[] {
  return bands.flatMap(({ tag_id, marks }) => {
    const mark = marks.find((one) => one.area_id === areaId);
    if (mark === undefined) return [];
    return [{ tag_id, band: mark.band, spread_low: mark.spread_low, spread_high: mark.spread_high }];
  });
}
