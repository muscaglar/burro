/**
 * Two calls of the look of the portrait, each built two ways and chosen in one line here.
 * Neither changes what the portrait says, in which order, or what a press does.
 *
 * They are plain values in a file of their own, so that a page drawn on the server and a
 * part drawn in the browser read the same ones.
 */

/**
 * How the lists of vibes stand. `apart`: what the area is like stands in a box, and each
 * list in a box of its own under it, with grass between one and the next, as the results of
 * a search stand. `together`: the portrait is one box, as Town Map drew the vibes of an
 * area, and each list stands in it under the name of the list on a plate. It is the calmer
 * of the two, and the shorter by the room four boxes take.
 */
export type ListsStand = "apart" | "together";

/** This is the one line that chooses. */
export const LISTS_STAND: ListsStand = "apart";

/**
 * Whether the small drawing of a vibe stands before its name on its line, as it stands on
 * a chip and beside a slider of the search. `beside`: it does, chosen by the id and the
 * family the service gives the vibe, and the plain one where neither is drawn. `nowhere`:
 * a line is its name, its steps and its words, which is the calmer of the two.
 */
export type ThingsStand = "beside" | "nowhere";

/** This is the one line that chooses. */
export const THINGS_STAND: ThingsStand = "beside";
