/**
 * The names of the areas on the map: where each area is on the ground, which
 * areas are named, and where each name stands. docs/design/web.md, section 6.
 *
 * A name is drawn whole, or not at all. It is never cut, by the edge of its
 * area or by the edge of the window of the map, and it never lies over a pin
 * or over another name. The name of an area that has a pin stands under the
 * pin. The name of an area that has none lies over its own area, and over no
 * other: where it lies is all that says which area it is of. Every name is
 * the release's own: nothing here comes from a basemap, and nothing is fetched.
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

/**
 * The two ways a name may be drawn. On a `plate` of the colour that is read on, with an
 * edge. Or with a `halo` of that colour about every letter, and nothing under it.
 */
export type NamesAs = "plate" | "halo";

/**
 * How a name is drawn: the width of a letter of it, the height of a line, and the room
 * round it, in pixels. A name is set in the face of names at 20 pixels. Measured in a
 * browser: the names of the release come to 6.4 to 8.6 pixels a letter, and the widest is
 * what room is kept for, so that no name is wider than the room it was given.
 *
 * A plate has an edge and room inside it, which a name with a halo has not: so a name with
 * a halo has room where a name on a plate has none, and more areas are named.
 */
export const LETTERING = { letter: 8.6, line: 16, around: { plate: 14, halo: 6 } } as const;

/** How far under the point of its pin a name stands, in pixels. */
export const BELOW_A_PIN = 4;

/**
 * The room a pin takes on the screen, in pixels: its drawing, at two pixels of the screen
 * to one of its own on every screen. It stands on its place by its point, which is the
 * middle of its foot.
 */
export const PIN: Room = { width: 26, height: 32 };

/**
 * The room a pin takes over the name that stands under it, in pixels: the pin, which
 * stands on its place by its point, and the gap between its point and the name.
 */
export const UNDER_A_PIN = PIN.height + BELOW_A_PIN;

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

/** The size of type the sizes of the website are written for, in pixels: what a browser starts from. */
const TYPE = 16;

/**
 * How many times larger the type of the page is than the website sets it. A person may
 * make the type of the browser larger, and a name is then drawn larger with it.
 */
export function typeOfPage(): number {
  if (typeof document === "undefined") return 1;
  const size = Number.parseFloat(getComputedStyle(document.documentElement).fontSize);
  return Number.isFinite(size) && size > 0 ? size / TYPE : 1;
}

/**
 * The room a name needs where it is drawn: that of its lines, and of the pin over it where
 * it has one. Its letters take more where the type of the page was made `larger`. What is
 * round them, and the pin, are drawn in pixels of the screen and take what they took.
 */
export function roomFor(name: string, pinned: boolean, drawn: NamesAs = "plate", larger = 1): Room {
  const lines = linesOf(name);
  const widest = Math.max(...lines.map((line) => line.length));
  const around = LETTERING.around[drawn];
  return {
    width: widest * LETTERING.letter * larger + around,
    height: lines.length * LETTERING.line * larger + around + (pinned ? UNDER_A_PIN : 0),
  };
}

/** True where the area has room for the whole of its name. */
export function fits(name: string, room: Room, pinned: boolean, drawn: NamesAs = "plate", larger = 1): boolean {
  const needs = roomFor(name, pinned, drawn, larger);
  return needs.width <= room.width && needs.height <= room.height;
}

/** A place on the screen, in pixels, from the top left of the window of the map. */
export interface Point {
  readonly x: number;
  readonly y: number;
}

/** The edges of what is drawn on the screen, in pixels, from the top left of the window of the map. */
export interface Box {
  readonly left: number;
  readonly top: number;
  readonly right: number;
  readonly bottom: number;
}

/**
 * The two ways the areas to name may be chosen. By `room`: an area is named where its own
 * area has room for the whole of its name, and of its pin where it has one. By `pins`: an
 * area of the first ten is named under its pin wherever the window has room for the name,
 * the better ranked first, and every other area where its own area has room.
 *
 * By room, a map that holds the whole city names nothing: of a thousand areas none has
 * room for its name until the map is drawn a long way nearer. By pins it names the areas
 * a person is reading of in the list beside it.
 */
export type NamedBy = "room" | "pins";

/** An area that may be named, as it is drawn on the screen now. */
export interface ToName {
  readonly id: string;
  readonly name: string;
  /** Where the middle of the area is. */
  readonly at: Point;
  /** What the area takes on the screen. */
  readonly room: Room;
  /** Where the point of its pin stands, which may be beside the area. `null` for an area that has no pin. */
  readonly pin: Point | null;
}

/** A name that is drawn: whose it is, and where it stands. */
export interface Name {
  readonly id: string;
  /** True where it stands under the pin of its area, and false where it lies over the middle of the area. */
  readonly under: boolean;
  /** How far from the middle of its area it is tied, in pixels: to its middle, or to the middle of its top under a pin. */
  readonly offset: readonly [number, number];
  /** What it takes on the screen. */
  readonly box: Box;
}

/** True where the whole of a thing stands in the window. A window that is not laid out yet cuts nothing. */
export function whole(box: Box, window: Room | null): boolean {
  if (window === null) return true;
  return box.left >= 0 && box.top >= 0 && box.right <= window.width && box.bottom <= window.height;
}

const over = (one: Box, other: Box) =>
  one.left < other.right && other.left < one.right && one.top < other.bottom && other.top < one.bottom;

/** What a pin takes on the screen, from where its point stands. */
const pinAt = ({ x, y }: Point): Box => ({
  left: x - PIN.width / 2,
  top: y - PIN.height,
  right: x + PIN.width / 2,
  bottom: y,
});

/**
 * The names to draw, and where each stands. The areas are given in the order they are to
 * be named in: those of the first ten in the order of their ranks, and then the rest. A
 * name that is drawn is never given up for one that comes after it.
 *
 * `window` is the room of the window of the map, or `null` where it is not laid out yet.
 */
export function named(
  areas: readonly ToName[],
  window: Room | null,
  how: { readonly drawn: NamesAs; readonly by: NamedBy; readonly larger: number },
): readonly Name[] {
  const pins = areas.flatMap((area) => (area.pin === null ? [] : [pinAt(area.pin)]));
  const names: Name[] = [];
  for (const area of areas) {
    const { pin } = area;
    const under = pin !== null;
    // Where it lies is all that says whose a name with no pin is, so it lies over its own
    // area and no other. So does every name, where the areas to name are chosen by room.
    if ((how.by === "room" || !under) && !fits(area.name, area.room, under, how.drawn, how.larger)) continue;
    const { width, height } = roomFor(area.name, false, how.drawn, how.larger);
    // Where its middle would stand: over the middle of its area, or under the point of its pin.
    let middle = pin === null ? area.at.x : pin.x;
    if (pin !== null && window !== null) {
      // Near an edge of the window a name under a pin stands against the edge, whole: as
      // far to one side as leaves the whole of the pin over it, and no further.
      const within = Math.min(Math.max(middle, width / 2), window.width - width / 2);
      if (Math.abs(within - middle) > (width - PIN.width) / 2) continue;
      middle = within;
    }
    const top = pin === null ? area.at.y - height / 2 : pin.y + BELOW_A_PIN;
    const box: Box = { left: middle - width / 2, top, right: middle + width / 2, bottom: top + height };
    if (!whole(box, window)) continue;
    if (pins.some((other) => over(box, other)) || names.some((other) => over(box, other.box))) continue;
    names.push({
      id: area.id,
      under,
      offset: pin === null ? [0, 0] : [middle - area.at.x, pin.y - area.at.y + BELOW_A_PIN],
      box,
    });
  }
  return names;
}
