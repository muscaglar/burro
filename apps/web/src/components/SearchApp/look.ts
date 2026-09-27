/**
 * Calls of where the parts of the search page stand, each built more ways than one and
 * each chosen in one line here. None changes what the page says, or what a press does.
 *
 * They are plain values in a file of their own, kept apart from the page, which runs in
 * the browser.
 */

/**
 * Where the part that refines a search stands on a narrow screen, once a search is open.
 * It is one part, closed until it is pressed. Wherever it stands, it comes in the page
 * where it is drawn: a keyboard and a screen reader reach it there.
 *
 * `after`: directly after the first result, so that the first result is whole on the
 * first screen of a phone. `before`: over the first result, as it is on a wide screen. The
 * first result then stands lower by as much as the part is high, and on a phone it ends
 * under the foot of the first screen.
 */
export type Stands = "after" | "before";

export const STANDS: readonly Stands[] = ["after", "before"];

/** This is the one line that chooses. */
export const ON_A_NARROW_SCREEN: Stands = "after";

/**
 * When what stands over the answer gives way further, on a screen wider than a narrow one.
 * It gives way as it does on a narrow screen whatever the search: what Burro says of the
 * search stands in no frame of its own, the parts of the page stand closer, and what says
 * that areas can be compared stands under the first result.
 *
 * `asked`: while Burro asks which place was meant. His question stands over the answer,
 * and measured at 1440 by 900 the first result then began at 964 of 900, out of sight.
 * `always`: whatever the search, once one is open. The line that says what happened then
 * stands in its frame on no screen.
 */
export type GivesWay = "asked" | "always";

export const GIVES_WAY: readonly GivesWay[] = ["asked", "always"];

/** This is the one line that chooses. */
export const OVER_THE_ANSWER_GIVES_WAY: GivesWay = "asked";

/**
 * What makes a search of the second of the two ways in, "Deep search", before a search.
 * The founder drew two ways in, and the second is built by choosing and then searching.
 *
 * `button`: its button, "Search with these settings", and nothing else. What is chosen in
 * the settings is kept: each thing is sent to be applied, so that the settings are drawn
 * from what the API holds, and no search is made of it. The tabs stay, no result is
 * drawn, and the map is as it is before a search, until the button is pressed.
 *
 * `setting`: the first setting that is moved, or the first place that is chosen, as it was
 * before the look. Seen in a browser by three people: the tabs went and the page became a
 * page of results, under a person who was told to choose and then to search, and by
 * keyboard one press of an arrow key on a slider did it.
 *
 * Once a search is open a setting that is moved is ranked at once, whichever is chosen: a
 * person is then refining an answer they can see.
 */
export type Ranks = "button" | "setting";

export const RANKS: readonly Ranks[] = ["button", "setting"];

/** This is the one line that chooses. */
export const DEEP_SEARCH_RANKS_BY: Ranks = "button";

/**
 * Where an area is found by its name, on the first page. The second way in asked renting
 * or buying and a place to reach at its head, which its settings ask too: it asks once
 * now, in the settings. The field that stood with those two questions found an area by
 * its name as well, and was the one way to on the page.
 *
 * `foot`: a field of its own at the foot of the second way in, under its button. It finds
 * areas alone, each a link to its page, and adds nothing to a search. `nowhere`: no field.
 * An area is then found on the map, or in the table of all areas under it.
 */
export type FindsAnArea = "foot" | "nowhere";

export const FINDS_AN_AREA: readonly FindsAnArea[] = ["foot", "nowhere"];

/** This is the one line that chooses. */
export const AN_AREA_BY_NAME: FindsAnArea = "foot";

/**
 * Where the button that makes a search of the second way in stands, before a search. It
 * stood at the foot of the space requirements, under ten groups of them: measured with
 * the way chosen and nothing scrolled, 2,213 px down a desk's window of 900 and 2,641 px
 * down a phone's of 844. A person who had chosen did not find it.
 *
 * `held`: one button, held at the foot of the window for as long as its own place is
 * under it, and at rest there once the page is scrolled to it. What Burro says of what
 * could not be sent stands over it, in sight wherever a person is among the groups.
 *
 * `both`: two of it, one at the head of the way, under what the way says of itself, and
 * one at the foot of the space requirements. What Burro says stands at the head.
 *
 * `foot`: at the foot alone, as it stood.
 */
export type ButtonStands = "held" | "both" | "foot";

export const BUTTON_STANDS: readonly ButtonStands[] = ["held", "both", "foot"];

/** This is the one line that chooses. */
export const THE_BUTTON_OF_DEEP_SEARCH: ButtonStands = "held";
