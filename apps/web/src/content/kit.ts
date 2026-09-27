/**
 * Site copy for the kit of parts: what a part says of its own state, where no file of site
 * copy held the word already. "does not count", "assumed", "Source" and the words for a
 * band are older than the kit, and a part takes them from the file that has them.
 *
 * Nothing here says anything of a place.
 */

import { CHIPS } from "./search";

/** How much a thing counts, said beside its gauge. At nought it says `CHIPS.off`. */
export const GAUGE = {
  counts: (hundredths: number) => `counts ${hundredths} of 100`,
} as const;

/**
 * The name of the five steps of a vibe where they hold no peg, to whoever hears the page.
 * It names what is drawn, as the key to the drawings names it. What that means stands in
 * words beside the steps, so the name does not say it a second time.
 */
export const PEG = {
  empty: "Five empty steps, with no peg",
} as const;

/**
 * What is said of a figure after its mark, in two words, by how much of it is known. They
 * are said the same wherever a gauge is drawn, and are written here and nowhere else.
 *
 * `some`: beside a band or a fit that was worked out from some of what goes into it, or
 * that is an estimate, after the mark of what is not whole. The two words are the
 * founder's. What the figure was worked out from is said beside them where a page has the
 * room for it, and where the figure is opened.
 *
 * `none`: beside the name of a thing that was asked for, where Burro has no figure for it
 * in the area. What is not known is said to be not known, in as few words.
 */
export const KNOWN = {
  some: "approx data",
  none: "no data",
} as const;

/** What a chip says that had no word. */
export const LABEL = {
  /** Between the word for a state and what it is said of: "assumed: 45 minutes". */
  of: (state: string, what: string) => `${state}: ${what}`,
  /** The name of the cross of a chip: what it does, and to what. */
  takeOff: (what: string) => (what === "" ? CHIPS.remove : `${CHIPS.remove}: ${what}`),
} as const;
