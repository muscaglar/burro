/**
 * The one call of the look of the two ends of a gauge, which was built two ways and is
 * chosen in one line here. It changes which picture stands at an end, and nothing of what
 * an end is called, of where an area sits or of what a press does.
 *
 * It is a plain value in a file of its own, so that a page built on the server and a part
 * drawn in the browser read the same one.
 */

/**
 * Which way an end is drawn, where it was drawn two ways. `first`: what there is little
 * of is the thing itself, small or alone, and what there is much of is the thing, large:
 * a young tree and two grown ones, a kite far off and a kite near. `second`: what there is
 * little of is what stands in its place, and what there is much of is the place it makes:
 * a lamp on a bare street where little is green, a bench on bare paving where few parks
 * are close by, and a bench under a tree where they are.
 *
 * An end that was drawn one way is drawn that way, whichever is chosen. Neither way marks
 * an end as the better one.
 */
export type WayOfEnds = "first" | "second";

export const WAYS_OF_ENDS: readonly WayOfEnds[] = ["first", "second"];

/** This is the one line that chooses. */
export const WAY_OF_ENDS: WayOfEnds = "first";
