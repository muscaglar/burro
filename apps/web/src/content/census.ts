/**
 * Site copy for the census figures of an area's page: the names of its
 * controls and its states, and nothing else.
 *
 * Every word about the figures is the API's: the heading, the day, the notes,
 * each caption and each row. Nothing here says what a figure means, and no
 * word here is one Burro would be choosing of a figure. A test reads this
 * file for such words.
 */

export const CENSUS = {
  /** While the figures are asked for. */
  loading: "Loading the figures.",
  /** Where the figures could not be read. What went wrong is said in the API's words above it. */
  failed: "The figures could not be loaded.",
  again: "Try again",
  /** With scripts off: the figures are not in the page, so that nothing keeps them. */
  noScript: "The figures are loaded when you ask for them, which needs scripts to be on.",
  /** In the place of a count that is not given. The share beside it says why, in the API's words. */
  noCount: "Not given",
  /** What the picture beside a share is. Both names are the API's. */
  picture: (area: string, city: string) =>
    `Beside each share is the same share, drawn. The bar is ${area}. The mark is ${city}.`,
  /** The way to where the figures came from, on the page of sources. */
  source: "Where these figures came from",
  notes: "About these figures",
} as const;
