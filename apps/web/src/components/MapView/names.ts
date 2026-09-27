/**
 * How the name of an area is drawn on the map, and which areas are named.
 *
 * On a `plate` of the colour that is read on, with an edge, so that nothing is read on
 * the land itself: a name then reads the same on every band and on every pattern. Or with
 * a `halo` of that colour about every letter and nothing under it, as Town Map drew the
 * names of its towns: more of the map is seen, a name needs less room and so more areas
 * are named, and a name is read on the land.
 *
 * It is kept apart from the map, which runs in the browser: what a page drawn on the
 * server takes from a file that runs in the browser is a component and nothing else.
 */

import type { NamedBy, NamesAs } from "@/lib/map/labels";

/** This is the one line that chooses how a name is drawn. */
export const NAMES: NamesAs = "plate";

/**
 * Which areas are named. By `pins`: those of the first ten, under their pins, wherever the
 * window of the map has room for the name, the better ranked first: and every other area
 * where its own area has room for the whole of its name. By `room`: every area where its
 * own area has room for its name and for its pin, and no other. A map that holds the whole
 * city then names nothing, since no area has the room: measured at 1440 by 900, in a
 * window 248 px wide, and of a thousand areas at any width.
 *
 * This is the one line that chooses which areas are named.
 */
export const NAMED: NamedBy = "pins";
