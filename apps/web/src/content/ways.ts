/**
 * Site copy for the two ways into a search, and for the settings once a search is open.
 *
 * Before a search the page offers two ways in, as two tabs: a box to type in, and the
 * settings to choose from, with the button that makes a search of them. Once a search is
 * open the two have become one search, and the settings are one part that is closed until
 * it is pressed.
 *
 * It names controls and says what each is for. It says nothing of a place.
 */

import { SETTINGS } from "./settings";

export const WAYS = {
  /** What the two tabs are, to whoever hears the page. A sighted person reads it from where they stand. */
  label: "Ways to search",
  /** The box, with the examples and the words to start from. It is the one chosen at first. */
  quick: "Quick search",
  /** What it is, the settings, and the button that ranks by them. */
  deep: "Deep search",
} as const;

/** The two ways in, in the order they stand in. */
export type WayId = Exclude<keyof typeof WAYS, "label">;

export const WAY_IDS: readonly WayId[] = ["quick", "deep"];

/**
 * What the second way says of itself, at its head, to whoever has not used it before: what
 * it is, and what makes the search. The settings under it are its questions, and it names
 * them and their button as each names itself.
 */
export const DEEP = {
  lead:
    "Deep search lets you build your search step by step, without typing a description. " +
    `Choose what matters to you under ${SETTINGS.title} below, then press "${SETTINGS.rank}", ` +
    "and Burro will rank the areas by how well they match.",
  /**
   * Under the field at its foot, which finds an area by its name. An area that is found is
   * a link to its page, and is no part of a search.
   */
  finds:
    "If you already have an area in mind, type its name here. Burro starts looking once you have typed " +
    "two letters, and each area it finds is a link to the page about that area.",
} as const;

/** The settings once a search is open: one part, closed until it is pressed. */
export const REFINE = {
  label: "Refine search",
} as const;

/**
 * What the page says where the words could not be read and no search is open yet. The
 * settings do the same job, and before a search they stand under the second tab, which
 * the line names so that a person can find them.
 */
export const UNREAD = {
  before:
    "Burro could not read your words just now. You can try again, or use Deep search, " +
    "which lets you choose what you want without typing.",
} as const;
