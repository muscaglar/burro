/**
 * Three calls of the look of the name board and the foot, each built more ways than one and
 * each chosen in one line here.
 *
 * They are plain values in a file of their own: a part of the board runs in the browser,
 * and what a page takes from such a file is a component and nothing else.
 */

/**
 * Whether Burro is drawn by what every page stands in, and so on every page.
 * `beside-the-name`: he sits in the name board, behind the rule at its foot, after the
 * name, and is seen from his back up. He stirs there as he does wherever he rests.
 * `nowhere`: he is drawn where he was until a person who walked the
 * website asked for him on every page: beside the heading before a search, where he asks,
 * and where he hops.
 *
 * He is one rabbit. Where he is drawn on the page itself he is not drawn in the board as
 * well, and the board keeps his room.
 */
export type InTheBoard = "nowhere" | "beside-the-name";

/** This is the one line that chooses. */
export const BURRO_IN_THE_BOARD: InTheBoard = "beside-the-name";

/**
 * Where he is drawn on a screen narrower than 40rem, as a phone is. There the board is one
 * line. While it held four pages they and the name left 15 px of it on a phone 390 wide,
 * and he is 48 wide. With three it has room for him on that phone, and none on a narrower.
 *
 * `over-the-foot`: he sits behind the rule at the head of the foot, on the grass, and is
 * seen from his back up. He takes no room of his own, so the head of every page is as it
 * was and the first result of a search stands where it stood. He is seen by whoever reads
 * a page to its end.
 *
 * `in-the-board`: the board is two lines, the name with him beside it and under them the
 * three pages as buttons. He is then at the head of every page, and everything under the
 * board stands lower by the height of a line.
 *
 * `nowhere`: he is drawn on a narrow screen where the page itself draws him, and nowhere else.
 */
export type OnANarrowScreen = "over-the-foot" | "in-the-board" | "nowhere";

/** This is the one line that chooses. */
export const BURRO_ON_A_NARROW_SCREEN: OnANarrowScreen = "over-the-foot";

/** Whether the look draws him over the foot of a page, on a narrow screen. */
export const overTheFoot = (board: InTheBoard = BURRO_IN_THE_BOARD, narrow: OnANarrowScreen = BURRO_ON_A_NARROW_SCREEN): boolean =>
  board === "beside-the-name" && narrow === "over-the-foot";

/** How the look draws the board on a narrow screen: in two lines where he is in it, and in one where he is not. */
export const boardOnANarrowScreen = (
  board: InTheBoard = BURRO_IN_THE_BOARD,
  narrow: OnANarrowScreen = BURRO_ON_A_NARROW_SCREEN,
): "labels" | "keys" => (board === "beside-the-name" && narrow === "in-the-board" ? "keys" : "labels");

/**
 * By what name the foot of every page leads to what is said of what a person types: where
 * it goes, and that it is not kept. It is said among the methods, under a heading of its own.
 *
 * `privacy`: by the word a person looks for at the foot of a page. It is short, so the
 * links of the foot are one line on a phone as they were. To whoever hears the page it says
 * the heading of the part it leads to as well, after the word.
 *
 * `as-headed`: by the heading of the part it leads to, word for word. It is longer than the
 * other three links together, so on a phone the links of the foot take a second line.
 */
export type WordsInTheFoot = "privacy" | "as-headed";

/** This is the one line that chooses. */
export const WORDS_IN_THE_FOOT: WordsInTheFoot = "privacy";
