/**
 * Site copy for the helpers: the two aids to a quick search, which stand in one line
 * under the box before a search, each closed until it is pressed.
 *
 * It names controls. What a helper opens has words of its own: an example is in
 * `search.ts`, and a word of the shelf and the name of a vibe are the API's.
 */

export const HELPERS = {
  /** What the line is, to whoever hears the page. A sighted person reads it from where the line stands. */
  label: "Help with what to type",
  /** Opens the examples. One fills the box, and sends nothing. */
  example: "Try an example",
  /** Opens the shelf of words. A word opens the card of its vibe, which is where it is added. */
  word: "Start from a word",
} as const;

/** The helpers that are drawn, in the order they stand in. */
export type HelperId = Exclude<keyof typeof HELPERS, "label">;
