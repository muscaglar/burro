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
  loading: "Burro is loading the figures.",
  /** Where the figures could not be read. What went wrong is said in the API's words above it. */
  failed: "Burro could not load the figures this time.",
  again: "Try again",
  /** With scripts off: the figures are not in the page, so that nothing keeps them. */
  noScript:
    "Burro loads these figures only when you open this section, and it needs JavaScript to do that. To see them, switch JavaScript on in your browser and open the section again.",
  /** In the place of a count that is not given. The share beside it says why, in the API's words. */
  noCount: "Not given",
  /** What the picture beside a share is. Both names are the API's. */
  picture: (area: string, city: string) =>
    `Beside each share there is a small picture of it. The bar shows the share in ${area}, and the upright line shows the share in ${city}, so that you can see the two together.`,
  /** The way to where the figures came from, on the page of sources. */
  source: "Where these figures came from",
  notes: "About these figures",
} as const;
