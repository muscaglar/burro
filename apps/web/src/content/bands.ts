/**
 * Site copy for a band, in words a person would use. A band is a code the API
 * sends, from 1 to 5: where an area sits among the areas compared, in fifths,
 * counted from the low end. The word for it is site copy, as "within" and
 * "over" are for a journey.
 *
 * Each word is true of the band as the contract counts it (section 2.4), by
 * how many areas sit strictly below: under one in five for band 1, and four
 * in five or more for band 5. None says how many sit above, which a band does
 * not say where areas are level. Each is said of an area among all the areas
 * that were compared, and says so by no word of its own: "here" was read as
 * the area itself.
 *
 * No word here names a place, and none is a figure.
 */

export type BandNumber = 1 | 2 | 3 | 4 | 5;

/** Where an area sits on a vibe that runs one way, from least to most. */
export const BAND_ONE_WAY: Readonly<Record<BandNumber, string>> = {
  1: "among the least",
  2: "on the low side",
  3: "around the middle",
  4: "on the high side",
  5: "among the most",
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
 * Beside a band that was worked out from some of the measurements of its vibe: how many of
 * them have a figure for the area, of how many. Both counts are the API's.
 */
export const RESTS_ON = {
  /** Short, beside the band on the line of a vibe. */
  short: (known: string, parts: string) => `from ${known} of its ${parts} measurements`,
  /** In full, where the vibe is opened. */
  full: (known: string, parts: string) =>
    `Burro worked this out from ${known} of the ${parts} measurements that go into the vibe. It has no figure for the rest in this area, and it fills nothing in for them.`,
  /** Before the names of the measurements that have no figure. The names are the API's. */
  without: "Burro has no figure for",
  /**
   * A measurement Burro has for no area, where the API gives no name for it. It is counted,
   * and never shown by its code. It stands in the list that `without` begins, as `waits` does.
   */
  notCarried: (count: number) =>
    count === 1
      ? "one measurement that it does not have for any area yet"
      : `${count} measurements that it does not have for any area yet`,
  /** After the name of a measurement that Burro has for no area. The name is the API's. */
  waits: (name: string) => `${name}, which it does not have for any area yet`,
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
