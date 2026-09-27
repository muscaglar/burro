/**
 * One call of the look of the entry of accounts in the name board, built two ways and
 * chosen in one line here.
 *
 * It is a plain value in a file of its own: the entry runs in the browser, and what a page
 * takes from such a file is a component and nothing else.
 */

/**
 * What becomes of the entry on a screen narrower than 40rem, as a phone is, once a search
 * is open. There the board is one line. While it held four pages they and the name filled
 * the line, and the entry took a second: the board was 96 px high where it was 52, and the
 * first result of a phone 390 wide ended under the foot of the first screen. Two promises
 * met, and both could not be kept: that the way to an account stands in the name board, and
 * that the first result is whole on the first screen. So the entry was built to give way.
 *
 * The board holds three pages now, and has room. Measured with accounts on, after a plain
 * search, in a window 844 high: on a phone 360 wide or wider the entry stands on the one
 * line, the board is 52 px high with it and without it, and the first result stands where
 * it stood, from 452 to 838 at 390 wide. On a phone 320 wide the entry takes a second
 * line: the board is 96 px high where it is 52, and the first result begins at 630 where it
 * began at 586. Before a search the board is 56 px high at 360 and wider, as it is with
 * accounts off, and 100 at 320.
 *
 * `gives-way`: once a search is open the entry is not drawn in the board of a narrow
 * screen. The board is one line, as it is with accounts off, and the first result stands
 * where it stood, on the narrowest phone too. The way to signing in, and to an account,
 * then stands after the first result, with the button that keeps a search. Before a
 * search, and on every other page, the entry is in the board.
 *
 * `stays`: the entry is in the board on every page and in every state. It costs nothing
 * on a phone 360 wide or wider. On a narrower one the board is two lines, and once a
 * search is open everything under it stands lower by the height of a line.
 */
export type OnANarrowScreen = "gives-way" | "stays";

export const ON_A_NARROW_SCREEN_MAY: readonly OnANarrowScreen[] = ["gives-way", "stays"];

/** This is the one line that chooses. */
export const ENTRY_ON_A_NARROW_SCREEN: OnANarrowScreen = "gives-way";
