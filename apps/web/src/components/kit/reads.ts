/**
 * Which words are read. The pixel face is for a name, a heading and a short label. A figure
 * is read exactly, whatever it stands in: so words that hold one are set in the reading
 * face, and no part waits to be told.
 *
 * It is plain code with no state, kept in a file of its own so that a part that runs in
 * the browser and a page drawn on the server ask the same thing.
 */

/** True of words that hold a figure: a count, a sum of money, a number of minutes. */
export function holdsAFigure(words: unknown): boolean {
  return (typeof words === "string" || typeof words === "number") && /\d/.test(String(words));
}
