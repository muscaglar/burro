/**
 * What is a matter of taste in how a search is shared, in one line. It is plain code with
 * no state, kept apart from the part that draws it, which runs in the browser.
 */

/**
 * What becomes of the page as the way to share a search is pressed, where what it opens
 * would begin under the foot of the window. Two promises meet there, and both cannot be
 * kept: that what a press opens is seen, and that what was pressed stays under the hand.
 *
 * `held`: the page is not moved. What was pressed stays where it stood, turns amber and
 * says that it is open, and what it opened begins under it: where that is under the foot
 * of the window, a person scrolls to it. `brought`: what it opened is brought into sight,
 * until the whole of it is in sight or the button stands at the top of the window. Measured
 * with the button at the foot of the window: it went 616 px up a phone and 514 up a desk,
 * and something else lay under the pointer.
 *
 * It is said of the way to what says that a search came from a link as well, which stands
 * beside the way to share a search.
 */
export type WhatItOpens = "held" | "brought";

export const WHAT_IT_OPENS_MAY_BE: readonly WhatItOpens[] = ["held", "brought"];

/** This is the one line that chooses. */
export const WHAT_IT_OPENS: WhatItOpens = "held";
