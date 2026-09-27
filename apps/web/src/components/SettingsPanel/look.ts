/**
 * What is a matter of taste in how the settings are drawn, in one line. It is plain code
 * with no state, kept apart from the settings, which run in the browser.
 */

/** Which groups of the settings stand open at first, once a search is open. */
export type OpensAtFirst = "none" | "a-couple" | "all-asked";

export const OPENS_AT_FIRST_ARE: readonly OpensAtFirst[] = ["none", "a-couple", "all-asked"];

/**
 * Before a search the first two groups stand open, whichever is chosen here: it is then
 * seen that a group opens and closes. Once a search is open:
 *
 * `none`: every group is closed. A person has the answer before them and came to change
 * one thing: the bar of every group says what it holds, so all that is set is read on one
 * screen, and the group that is wanted is one press away. Measured in a browser at 1440
 * by 900, after a plain search of a budget, a journey and two vibes: the settings were
 * 2,404 px high with two groups open, and the first result stood that far under the fold.
 *
 * `a-couple`: two groups stand open, and no more. Those that hold something the person
 * asked for come first, and the first of the rest make up the two. The bar of every other
 * group says what it holds, so what was asked for is read though its group is closed.
 *
 * `all-asked`: every group that holds something the person asked for stands open, and the
 * first two where none does. Measured in a browser at 390 by 844, after a plain search of
 * a budget, a journey and two vibes: the settings were 5,187 px high and drew 79
 * controls, where with two groups open they were 2,701 px high and drew 39.
 */
export const OPENS_AT_FIRST: OpensAtFirst = "none";

/** What the settings say at their head, under their name and over their groups. */
export type SaysAtTheirHead = "nothing" | "what-counts";

export const SAYS_AT_THEIR_HEAD_ARE: readonly SaysAtTheirHead[] = ["nothing", "what-counts"];

/**
 * The founder, of Deep search: "you have duplicated the explainer text, remove the explainer
 * copy from the settings section". The tab says what Deep search is and which button makes
 * the search, and the settings said it again under it. That is gone whichever is chosen
 * here, before a search and once one is open.
 *
 * `nothing`: their name, and then their groups. What Burro counts in every search, which
 * nobody chose, is named on the bar of the group that holds each, where it can be changed.
 *
 * `what-counts`: one sentence, which names what Burro counts in every search and says
 * where each can be changed. The tab does not say it. A result says how many things its
 * fit is based on, and these are the rest of them.
 */
export const SAYS_AT_THEIR_HEAD: SaysAtTheirHead = "nothing";

/** Where the name of the settings is drawn over them, where they stand open. */
export type NamedInSight = "always" | "before-a-search";

export const NAMED_IN_SIGHT_ARE: readonly NamedInSight[] = ["always", "before-a-search"];

/**
 * The founder named the settings "Space requirements". Whoever hears the page finds them
 * by that name wherever they stand, whichever is chosen here.
 *
 * `always`: their name stands over them in Deep search and under "Refine search", as a band
 * of ink at the head of their box. They are one thing, and have one name wherever they are met.
 *
 * `before-a-search`: in Deep search alone. Under "Refine search" the button that opened
 * them is all that names them in sight, as it was before they had a name of the founder's:
 * walked then, "Refine search" opened onto a box headed "Settings".
 */
export const NAMED_IN_SIGHT: NamedInSight = "always";

/** Where the slider of a thing stands, in a box wide enough for it to stand beside the name of the thing. */
export type SliderStands = "beside" | "under";

export const SLIDER_STANDS_ARE: readonly SliderStands[] = ["beside", "under"];

/**
 * What a switch shows keeps its room while the switch is off, so that nothing moves as it
 * is turned on. A group is then as long as if every thing of it were on. Measured in a
 * browser at 1440 by 900, of the seven other things that count of the first family: they
 * were 480 px high while no slider was drawn, and are 1,440 with each slider under its thing.
 *
 * `beside`: in a box 34rem wide or wider the slider of a thing stands at the far side of
 * its row, beside its switch and its name, and its two ways under it there. Every slider
 * of a group then stands in one column, and the eye runs down them. In a narrower box, as
 * on a phone, it stands under its thing.
 *
 * `under`: under its thing in a box of any width, as it was drawn when it was turned on.
 */
export const SLIDER_STANDS: SliderStands = "beside";
