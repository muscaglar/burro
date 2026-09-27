/**
 * One call of the look of a chip, built two ways and chosen in one line here. Neither
 * changes what a chip says or what a press does: what nobody said is said in the words of
 * the chip, "assumed", whichever is chosen.
 *
 * It is a plain value in a file of its own, so that a page drawn on the server and a part
 * drawn in the browser read the same one.
 */

/**
 * What a chip stands on that holds what nobody said, or not the whole of it. Every chip has
 * the same solid edge of ink: a dashed one was not understood. `page`: on cream, as every
 * chip does, and the word alone tells it from what was said. `sand`: on sand, so that the
 * eye tells the two apart before the word is read. Sand is also the ground of land with no
 * fit and of a button in hand, so a chip on sand may be taken for one that is switched off.
 */
export type AssumedStandsOn = "page" | "sand";

export const GROUNDS: readonly AssumedStandsOn[] = ["page", "sand"];

/** This is the one line that chooses. */
export const ASSUMED_STANDS_ON: AssumedStandsOn = "page";
