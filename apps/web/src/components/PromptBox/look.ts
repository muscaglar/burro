/**
 * A call of where a part of the box stands, built two ways and chosen in one line here. It
 * changes nothing of what the box says, or of what a press does.
 *
 * It is a plain value in a file of its own, kept apart from the box, which runs in the
 * browser.
 */

/**
 * Where the sentences that say what a useful sentence holds stand on a narrow screen,
 * before a search. On a wider screen they stand over the field, under the heading, where
 * there is room for them.
 *
 * `under`: under the field, so that the field is in sight on the first screen of a phone.
 * Measured at 390 by 844: the field stands from 708 to 779. `over`: over the field, as on
 * a wider screen. The field then stands from 896 to 967, under the foot of the first
 * screen, and a person scrolls to it before they can type.
 */
export type HelpStands = "under" | "over";

export const HELP_STANDS: readonly HelpStands[] = ["under", "over"];

/** This is the one line that chooses. */
export const HELP_ON_A_NARROW_SCREEN: HelpStands = "under";
