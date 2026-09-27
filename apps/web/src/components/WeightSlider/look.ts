/**
 * The one call of the look of a slider, which was built two ways and is chosen in one line
 * here. It changes what is drawn on two buttons, and nothing of what a press does, of what
 * a button is called or of what is sent.
 *
 * It is a plain value in a file of its own, so that a page built on the server and a part
 * drawn in the browser read the same one.
 */

/**
 * What the two buttons of the slider of a vibe that runs one way bear. `pictured`: the
 * picture of each end of the vibe, as the two buttons of a scale bear the pictures of its
 * two ends: what there is little of at the low end of the slider, and what there is much
 * of at its high end. They are the pictures the gauge of a result has at its ends, so that
 * one pair of pictures stands for one vibe on every page. `signs`: a minus and a plus, as
 * the buttons of every other slider bear, and as these did.
 *
 * At its low end a slider that runs one way makes its vibe count for nothing: an area with
 * little of the thing then ranks as well as any other, and none is asked for. The line over
 * the sliders of a group says so, whichever is chosen.
 *
 * A slider that is of no vibe, as the slider of a measurement or of the budget is, bears
 * the two signs whichever is chosen, and so does the slider of a vibe whose ends nobody
 * has drawn.
 */
export type EndsOfOneWay = "pictured" | "signs";

export const ENDS_OF_ONE_WAY_MAY_BE: readonly EndsOfOneWay[] = ["pictured", "signs"];

/** This is the one line that chooses. */
export const ENDS_OF_ONE_WAY: EndsOfOneWay = "pictured";
