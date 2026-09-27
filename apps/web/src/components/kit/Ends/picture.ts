/**
 * Which picture stands at an end of a gauge. It is plain code with no state, so a page
 * built on the server and a part drawn in the browser choose the same one.
 *
 * A picture is chosen by the id the service gives a vibe, and by which of its two ends it
 * is: `end-leafy-low` and `end-leafy-high` for the vibe `leafy`. Each end has one picture,
 * and the two are opposites. No name of a vibe is written here.
 *
 * An end may be drawn a second way, under its name with `-b` after it. `look.ts` chooses
 * which way is drawn.
 */

import { inAName, isDrawn, type Drawing } from "../drawings";
import { WAY_OF_ENDS, type WayOfEnds } from "./look";

/** Which end of a gauge. The low one is at its left. */
export type End = "low" | "high";

/** The two ends of a gauge, in the order they are drawn in. */
export const ENDS: readonly End[] = ["low", "high"];

/** What stands at an end of a gauge that has no picture of its own. */
export const NO_PICTURE: Drawing = "end-blank";

/** What follows the name of the picture of an end in the name of the same end, drawn a second way. */
const SECOND = "-b";

/** The picture that is named for an end of a vibe. `null` where none is drawn by that name. */
function named(id: string, end: End): Drawing | null {
  const name = `end-${inAName(id)}-${end}`;
  return isDrawn(name) ? name : null;
}

/** The same end drawn the second way, where it was drawn so. Its picture as it is, where it was not. */
function secondOf(first: Drawing): Drawing {
  const name = `${first}${SECOND}`;
  return isDrawn(name) ? name : first;
}

/**
 * The pictures at the two ends of the gauge of a vibe, by the id the service gives the
 * vibe: the low end first. A vibe that has no picture has the blank one at both ends, and
 * so has one of which a single end was drawn: the two are opposites, and one says nothing
 * without the other.
 *
 * Each is drawn the way `look.ts` chooses, where none is asked for. A second way stands
 * for a first: an end with no first has none.
 */
export function picturesAtEnds(
  id: string | null | undefined,
  way: WayOfEnds = WAY_OF_ENDS,
): readonly [low: Drawing, high: Drawing] {
  const [low, high] = id === null || id === undefined || id === "" ? [null, null] : [named(id, "low"), named(id, "high")];
  if (low === null || high === null) return [NO_PICTURE, NO_PICTURE];
  return way === "second" ? [secondOf(low), secondOf(high)] : [low, high];
}

/** The picture at one end of the gauge of a vibe. The blank one, and never nothing, where the vibe has none. */
export function pictureAtEnd(id: string | null | undefined, end: End, way: WayOfEnds = WAY_OF_ENDS): Drawing {
  const at = ENDS.indexOf(end);
  return picturesAtEnds(id, way)[at] ?? NO_PICTURE;
}

/**
 * What stands at an end that is drawn by its name and has no picture by that name. It is
 * also what stands beside the heading of the page that is not there.
 */
export const BLANK: Drawing = "key-blank";

/** The name of an end as a drawing names it: "Houses" is `houses`. */
const ofAName = (end: string) =>
  end
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

/**
 * The picture of an end, by the name the service gives the end: `key-houses` for "Houses".
 * An end with no picture takes the blank one, and is never drawn as nothing.
 *
 * It knows the ends of a scale alone, and draws every vibe that runs one way alike. A part
 * that holds the id of its vibe asks `pictureAtEnd`, which has a pair for every vibe.
 */
export function pictureOfEnd(end: string): Drawing {
  const name = `key-${ofAName(end)}`;
  return isDrawn(name) && name !== BLANK ? name : BLANK;
}
