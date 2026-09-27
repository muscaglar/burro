/**
 * The order of the page: which part of the search page comes after which, for the screen
 * there is. It is plain code with no state, kept apart from the page, which runs in the
 * browser.
 *
 * THE ORDER OF THE PAGE IS THE ORDER IT IS DRAWN IN. A keyboard and a screen reader go
 * through the page in the order its parts come in, and a person who sees goes through it
 * in the order they are drawn in: where the two differ, the focus goes down the page and
 * back up. Seen on a phone, by keyboard: from the last chip the keys went 610 px down to
 * "Refine search", which was drawn after the first result and came before it in the page,
 * and then 477 px back up to the name of the first result. So no part is drawn out of the
 * order of the page, by any rule of the style sheet: the page puts its parts in the order
 * the screen draws them in.
 *
 * Where each part stands is still the style sheet's to say. It says which of three
 * screens there is, in one word, and the page asks it, and never the browser.
 */

import type { Stands } from "./look";

/**
 * The screen, as the style sheet of the page says it. `narrow`: one column, as narrow as a
 * phone, where the first result is whole on the first screen. `middle`: one column, and
 * wider. `wide`: two columns, the answer and the map beside it.
 */
export type Screen = "narrow" | "middle" | "wide";

export const SCREENS: readonly Screen[] = ["narrow", "middle", "wide"];

/** The parts of the page that the order is of. */
export type Part = "form" | "refine" | "unscripted" | "results" | "tools" | "map" | "rest";

/**
 * What the style sheet says of the screen, read from what it says of the page. Where no
 * sheet says anything, as in a browser that lays nothing out, the screen is a wide one.
 */
export function screenSaidBy(said: string): Screen {
  const word = said.trim();
  return word === "narrow" || word === "middle" ? word : "wide";
}

/**
 * The parts, in the order they come in the page. `screen` is `null` while the page is
 * built, and until the style sheet has been asked: a page is built with no screen to ask,
 * so it is built as for one column, and a browser that draws two says so once it has the
 * page. Nothing moves then: on a wide screen every part has its column and its row by name.
 *
 * Before a search, in one column, the map stands over the two ways in, so that it is in
 * sight whichever is chosen. On a wide screen it stands beside them, and comes after them
 * in the page: a keyboard reaches the box before the map.
 *
 * Once a search is open the answer comes first. On a narrow screen the part that refines
 * the search stands after the first result, so that the first result is whole on the
 * first screen, unless the look has it stand before. The way to share, the map and the
 * rest of the results follow.
 */
export function orderOf(screen: Screen | null, open: boolean, refines: Stands): readonly Part[] {
  if (!open) {
    return screen === "wide" ? ["form", "refine", "unscripted", "map"] : ["map", "form", "refine", "unscripted"];
  }
  return screen === "narrow" && refines === "after"
    ? ["form", "results", "refine", "tools", "map", "rest"]
    : ["form", "refine", "results", "tools", "map", "rest"];
}
