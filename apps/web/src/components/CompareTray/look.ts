/**
 * What is a matter of taste in how comparing is drawn, each in one line. It is plain code
 * with no state, kept apart from the parts that draw it, which run in the browser.
 */

import type { Drawing } from "../kit/drawings";
import type { PressKind } from "../kit/Press/kinds";

/**
 * How the way to the comparison is drawn in the bar. `go`: in cobalt, as the one button of
 * the bar, which is what matters most once two areas are chosen: comparing is a thing the
 * website makes much of, and among the many buttons of a page that are drawn in page the
 * one that compares was not seen. A page then holds two cobalt buttons, the one that sends
 * a search at its head and this one at the foot of the screen, and never side by side.
 * `plain`: in page, so that a page holds one cobalt button with the bar in sight.
 */
export const WAY_TO_COMPARE: PressKind = "go";

/**
 * Where what says that areas can be compared stands, where a result has the room of a town.
 * `over`: before the first result. The search page then says it beside what refines the
 * search, on its line, where it stands the first result 26 px lower: measured at 1440 by
 * 900. A list that is told to stand a slip over itself says it in the slip. `under`: under
 * the first result, on every screen, so that nothing more stands between the box and the
 * answer. `none`: nowhere. On a narrow result it stands under the first result whichever
 * of the first two is chosen: the first result is whole on the first screen there.
 */
export type InviteStands = "over" | "under" | "none";

/** This is the one line that chooses. */
export const INVITE_STANDS: InviteStands = "over";

/**
 * The drawing of two towns that stands beside what says that areas can be compared: two
 * drawings of the look, side by side, one of lower homes and one of taller. They are
 * dress, and say nothing of any area.
 */
export const TWO_TOWNS: readonly [Drawing, Drawing] = ["key-houses", "key-flats"];

/**
 * Whether the bar has the way to take every area out of it at once. `small`: "Clear", once
 * two areas or more are chosen: the drawing of a cross and the word, in the line of what
 * the bar says, so that the bar still has one button of the size of a main control, which
 * is the way to the comparison. It was in the bar as the founder walked the website, and
 * nobody asked for it to go. It is not drawn on a narrow screen, where the bar has no line
 * to spare: measured at 390 by 844 with it, the bar was 179 px high with four areas
 * chosen, where it is 160, and the page clears 176 for it. `none`: no such way on any
 * screen. Each area is taken out by its own cross, and "Start again" empties the bar with
 * the search.
 */
export type ClearStands = "small" | "none";

export const CLEAR_MAY_STAND: readonly ClearStands[] = ["small", "none"];

/** This is the one line that chooses. */
export const CLEAR_STANDS: ClearStands = "small";

/**
 * What the bar says of its towns, where it draws any. `nothing`: nothing. The founder, who
 * had walked the website twice, asked for the line that says what a town is to go from the
 * results, and the bar stands at the foot of the page of them: what a town is, is said in
 * the key to the drawings and at the head of the page of an area. `line`: once, in short,
 * under what the bar is called, of every town of it, as it was.
 */
export type BarSaysOfItsTowns = "nothing" | "line";

export const BAR_MAY_SAY_OF_ITS_TOWNS: readonly BarSaysOfItsTowns[] = ["nothing", "line"];

/** This is the one line that chooses. */
export const BAR_SAYS_OF_ITS_TOWNS: BarSaysOfItsTowns = "nothing";

/**
 * The id of what the bar says of how many areas are chosen. A button that can add no more
 * is described by it: the bar stands at the foot of the screen, and says why in sight.
 */
export const BAR_SAYS = "areas-to-compare-say";
