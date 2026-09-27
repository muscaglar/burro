/**
 * Calls of the look of the page of an area, each built more ways than one and each chosen
 * in one line here. None changes what the page says, in which order, or what a press does.
 *
 * They are plain values in a file of their own: parts of the page run in the browser, and
 * what a page drawn on the server takes from such a file is a component and nothing else.
 */

/**
 * How large the town at the head of the page is drawn. `ground`: at the pixel of the
 * ground, two pixels of the screen to one of its own on every screen, so that it is 112 by
 * 64 and no higher than the name it stands beside is on a wide screen. `screen`: at the art
 * pixel of the screen, as every other drawing is, which is 168 by 96 on a wide screen and
 * higher than the name. On a narrow screen the two are one size.
 */
export type TownDrawn = "ground" | "screen";

/** This is the one line that chooses. */
export const TOWN_DRAWN: TownDrawn = "ground";

/**
 * Where the town stands in the box of the head, for the eye. `after`: at the far end of
 * the box from the name, so that the name is read first, as it is heard first. `before`:
 * at the near end, before the name, as Town Map drew a town beside the name of its area.
 * To whoever hears the page the name comes first either way.
 */
export type TownStands = "after" | "before";

/** This is the one line that chooses. */
export const TOWN_STANDS: TownStands = "after";
