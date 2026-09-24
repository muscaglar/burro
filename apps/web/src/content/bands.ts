/**
 * Site copy for a band, in words a person would use. A band is a code the API
 * sends, from 1 to 5: where an area sits among the areas compared, in fifths,
 * counted from the low end. The word for it is site copy, as "within" and
 * "over" are for a journey.
 *
 * Each word is true of the band as the contract counts it (section 2.4), by
 * how many areas sit strictly below: under one in five for band 1, and four
 * in five or more for band 5. None says how many sit above, which a band does
 * not say where areas are level. "Here" is the areas compared in this data.
 *
 * No word here names a place, and none is a figure.
 */

export type BandNumber = 1 | 2 | 3 | 4 | 5;

/** Where an area sits on a vibe that runs one way, from least to most. */
export const BAND_ONE_WAY: Readonly<Record<BandNumber, string>> = {
  1: "among the least here",
  2: "on the low side here",
  3: "around the middle here",
  4: "on the high side here",
  5: "among the most here",
};

/** Where an area sits on a scale. The names of the two ends are the API's. */
export const BAND_ON_A_SCALE: Readonly<Record<BandNumber, (low: string, high: string) => string>> = {
  1: (low) => `at the ${low} end`,
  2: (low) => `towards ${low}`,
  3: (low, high) => `between ${low} and ${high}`,
  4: (_low, high) => `towards ${high}`,
  5: (_low, high) => `at the ${high} end`,
};

/** Said of a mixed area, which spans three bands or more and is no one point. */
export const BAND_VARIES = "varies within this area";

/**
 * Beside a band that rests on part of a recipe: how many of its parts have a
 * figure for the area, of how many. Both counts are the API's.
 */
export const RESTS_ON = {
  /** Short, beside the band on the line of a vibe. */
  short: (known: string, parts: string) => `from ${known} of its ${parts} parts`,
  /** In full, where the vibe is opened. */
  full: (known: string, parts: string) =>
    `This band rests on ${known} of the ${parts} parts of the recipe. The rest have no figure for this area, and nothing is filled in for them.`,
  /** Before the names of the parts that have no figure. The names are the API's. */
  without: "No figure for",
  /** A part this data does not carry, where the API gives no name for it. It is counted, and never shown by its code. */
  notCarried: (count: number) =>
    count === 1 ? "one part this data does not carry" : `${count} parts this data does not carry`,
  /** After the name of a part that this data does not carry at all. The name is the API's. */
  waits: (name: string) => `${name}, which is not in this data yet`,
} as const;

/**
 * What a band rests on, in the words to show for it: the API's own clause where the fact
 * holds one, and otherwise the website's, from the two counts the fact does hold.
 */
export function restsOnWords(
  rests: { readonly known: string; readonly parts: string; readonly partly: string | null },
  length: "short" | "full",
): string {
  return rests.partly ?? RESTS_ON[length](rests.known, rests.parts);
}
