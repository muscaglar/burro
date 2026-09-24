/**
 * The names of the areas on the map: where each area is on the ground, and
 * whether its name has room where the area is drawn. docs/design/web.md, section 6.
 *
 * A name is drawn over its own area, whole, or not at all. It is never cut,
 * and never laid over another area. Every name is the release's own: nothing
 * here comes from a basemap, and nothing is fetched.
 *
 * The map library draws no text, because a label needs glyph files from a
 * host. So a name is an element of the page, tied to the centre of its area,
 * and how wide it is drawn is worked out here from its letters.
 */

import type { GeometryData } from "@/lib/api/schema";

import { ringsOf } from "./project";

/** The box that holds one area, in degrees. */
export interface Extent {
  readonly west: number;
  readonly south: number;
  readonly east: number;
  readonly north: number;
}

/** What something takes on the screen, in pixels. */
export interface Room {
  readonly width: number;
  readonly height: number;
}

/** How a name is drawn: the width of a letter of it, the height of a line, and the room round it. */
export const LETTERING = { letter: 6.8, line: 15, around: 8 } as const;

/** The room a pin takes over the name that stands under it, in pixels. */
export const UNDER_A_PIN = 32;

/** A name of more letters than this, and more than one word, is drawn in two lines. */
const ONE_LINE = 10;

/** The box that holds each area of the release, by area id. */
export function extentsOf(geometry: Pick<GeometryData, "features">): ReadonlyMap<string, Extent> {
  const extents = new Map<string, Extent>();
  for (const feature of geometry.features) {
    let [west, south, east, north] = [Infinity, Infinity, -Infinity, -Infinity];
    for (const ring of ringsOf(feature.geometry)) {
      for (const [longitude, latitude] of ring) {
        if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) continue;
        west = Math.min(west, longitude);
        east = Math.max(east, longitude);
        south = Math.min(south, latitude);
        north = Math.max(north, latitude);
      }
    }
    if (west <= east && south <= north) extents.set(feature.properties.area_id, { west, south, east, north });
  }
  return extents;
}

/**
 * The lines a name is drawn in. A short name, or a name of one word, is one
 * line. A longer name is parted between two of its words, where the two lines
 * are nearest in length. No word is ever cut.
 */
export function linesOf(name: string): readonly string[] {
  const words = name.trim().split(/\s+/);
  if (words.length < 2 || name.length <= ONE_LINE) return [name.trim()];
  const parted = words.slice(1).map((_, at) => [words.slice(0, at + 1).join(" "), words.slice(at + 1).join(" ")] as const);
  const longest = ([one, other]: readonly [string, string]) => Math.max(one.length, other.length);
  const [best] = [...parted].sort((one, other) => longest(one) - longest(other));
  return best ?? [name.trim()];
}

/** The room a name needs where it is drawn: that of its lines, and of the pin over it where it has one. */
export function roomFor(name: string, pinned: boolean): Room {
  const lines = linesOf(name);
  const widest = Math.max(...lines.map((line) => line.length));
  return {
    width: widest * LETTERING.letter + LETTERING.around,
    height: lines.length * LETTERING.line + LETTERING.around + (pinned ? UNDER_A_PIN : 0),
  };
}

/** True where the area has room for the whole of its name. */
export function fits(name: string, room: Room, pinned: boolean): boolean {
  const needs = roomFor(name, pinned);
  return needs.width <= room.width && needs.height <= room.height;
}
