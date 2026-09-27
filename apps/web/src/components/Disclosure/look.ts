/**
 * What is a matter of taste in how a fold is drawn, in one line. It is plain code with no
 * state, kept apart from the fold, which runs in the browser.
 *
 * Where the arrow of a fold stands is no matter of taste: the founder asked for it at the
 * far end, and every bar that folds has it there, in its cell. It was built both ways for a
 * fold that was drawn as a button, and the line that chose is gone with that button.
 */

/** What a bar stands on while it is closed. */
export type BarAtRest = "page" | "sand";

export const BAR_AT_REST_ON: readonly BarAtRest[] = ["page", "sand"];

/**
 * `page`: cream, with its shade in sand, as the plain button of the look is. A bar that is
 * open is amber, and amber is told from cream more easily than from sand. `sand`: as Town
 * Map drew its drawers, which stand out more from the box that holds them.
 *
 * It is said of every bar that folds, on every page: of a stack and alone, a button and the
 * browser's own.
 */
export const BAR_AT_REST: BarAtRest = "page";
