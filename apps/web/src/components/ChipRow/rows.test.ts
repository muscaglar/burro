/** @jest-environment node */

import { readFileSync } from "node:fs";
import path from "node:path";

import {
  inSight,
  leastRoomOf,
  lying,
  NARROW_REM,
  NARROW_ROW,
  NARROW_ROWS,
  roomOf,
  standing,
  WIDE_ROWS,
  type Sized,
} from "./rows";

const chip = (words: string, { cross = true, turn = false, alone = false } = {}): Sized => ({ words, cross, turn, alone });
const lies = (chips: readonly Sized[]) => lying(chips).map((one) => one.lies);

describe("how the chips lie on a narrow row", () => {
  test("test_two_chips_that_say_little_share_a_row_and_one_that_says_much_has_its_own", () => {
    // Seen in a browser, on a phone: each chip on a row of its own, six rows for a plain
    // search, and the first result below the first screen.
    const row = [
      chip("Short"),
      chip("Tiny"),
      chip("A name of some length, with a part, and a second part"),
      chip("A sum of money, a kind of home, a limit"),
      chip("Choice", { cross: false }),
      chip("A few settings: 6 assumed", { cross: false }),
    ];

    expect(lies(row)).toEqual(["fills", "fills", "alone", "alone", "keeps", "gives"]);
  });

  test("test_where_two_fit_only_with_the_words_of_one_on_two_lines_that_one_gives_way_and_the_other_keeps_its_width", () => {
    // Seen in a browser: two chips were given a half of the row each, and the name of an
    // area was broken in the middle of a word to fit its half.
    expect(lies([chip("Longername, hidden"), chip("Choice", { cross: false })])).toEqual(["gives", "keeps"]);
    expect(lies([chip("Choice", { cross: false }), chip("Longername, hidden")])).toEqual(["keeps", "gives"]);
    // Where either could, the second does: what is read first is then whole.
    expect(lies([chip("One two"), chip("Four six")])).toEqual(["keeps", "gives"]);
    // Where both must, both do.
    expect(lies([chip("Seven eight"), chip("Seven eight")])).toEqual(["gives", "gives"]);
    // And where they fit with every word on one line, neither gives way.
    expect(lies([chip("One"), chip("Four six")])).toEqual(["fills", "fills"]);
  });

  test("test_a_chip_of_one_word_is_never_asked_to_give_way", () => {
    const word = chip("Word");

    expect(leastRoomOf(word)).toBe(roomOf(word));
    expect(lies([word, chip("Two words here")])).toEqual(["keeps", "gives"]);
    expect(lies([chip("Two words here"), word])).toEqual(["gives", "keeps"]);
    for (const beside of [chip("A name of some length"), chip("Two words here"), chip("Unbreakable"), word]) {
      const [first, second] = lies([word, beside]);
      expect([beside.words, first === "gives"]).toEqual([beside.words, false]);
      const [third, fourth] = lies([beside, word]);
      expect([beside.words, fourth === "gives"]).toEqual([beside.words, false]);
      // Both share or neither does.
      expect([first === "alone", third === "alone"]).toEqual([second === "alone", fourth === "alone"]);
    }
  });

  test("test_they_share_in_twos_in_the_order_they_stand_in_and_no_row_is_left_half_empty", () => {
    // Three that say little: the first two share, and the third has the row that follows.
    expect(lies([chip("One"), chip("Two"), chip("Three")])).toEqual(["fills", "fills", "alone"]);
    // One that says little before one that says much has a row to itself, whole.
    expect(lies([chip("One"), chip("A name of some length, with a part, and a second part"), chip("Two"), chip("Three")])).toEqual([
      "alone",
      "alone",
      "fills",
      "fills",
    ]);
    expect(lies([chip("One")])).toEqual(["alone"]);
    expect(lies([])).toEqual([]);
  });

  test("test_every_chip_that_shares_has_one_beside_it_that_shares", () => {
    const words = ["One", "Two words", "Three words here", "A name of some length, with a part", "Four", "Five is here", "Six"];
    const shares = lies(words.map((one) => chip(one))).map((one) => one !== "alone");

    expect(shares).toContain(true);
    shares.forEach((share, at) => {
      const before = shares.slice(0, at).filter(Boolean).length;
      // The first of two is followed by the second, and the second follows the first.
      if (share) expect([at, before % 2 === 0 ? shares[at + 1] : shares[at - 1]]).toEqual([at, true]);
    });
  });

  test("test_a_chip_that_is_open_has_a_row_to_itself_and_so_has_the_one_that_stood_beside_it", () => {
    expect(lies([chip("One"), chip("Two")])).toEqual(["fills", "fills"]);
    expect(lies([chip("One", { alone: true }), chip("Two")])).toEqual(["alone", "alone"]);
    expect(lies([chip("One"), chip("Two", { alone: true }), chip("Three")])).toEqual(["alone", "alone", "alone"]);
  });

  test("test_a_button_takes_room_from_the_words_beside_it", () => {
    expect(roomOf(chip("Two words"))).toBeGreaterThan(roomOf(chip("Two words", { cross: false })));
    expect(roomOf(chip("Two words", { turn: true }))).toBeGreaterThan(roomOf(chip("Two words")));
    expect(lying([chip("Two words", { turn: true }), chip("Two words"), chip("Two words", { cross: false })]).map((one) => one.beside)).toEqual([
      2, 1, 0,
    ]);
    // A scale, with the button that turns it, says too much to stand beside another.
    expect(lies([chip("A scale: towards an end", { turn: true }), chip("Short")])).toEqual(["alone", "alone"]);
  });

  test("test_words_are_counted_as_they_would_stand_on_two_lines_broken_at_a_space", () => {
    const bare = roomOf(chip("", { cross: false }));
    const letters = (words: string) => lying([chip(words, { cross: false })])[0]?.letters;

    expect(leastRoomOf(chip("Word", { cross: false })) - bare).toBe(4);
    // "A few settings:" over "6 assumed", which is the most even they can be set.
    expect(leastRoomOf(chip("A few settings: 6 assumed", { cross: false })) - bare).toBe(15);
    expect(letters("A few settings: 6 assumed")).toBe(15);
    expect(roomOf(chip("A few settings: 6 assumed", { cross: false })) - bare).toBe(25);
    // A word is never broken to make it fit.
    expect(letters("Incomprehensibilities")).toBe(21);
    expect(NARROW_ROW).toBeGreaterThan(2 * bare);
  });
});

describe("how many chips stand in sight on a narrow row", () => {
  const rowsOf = (chips: readonly Sized[]) => lying(chips).map((one) => one.row);
  /** A chip that says too much to share a row. */
  const long = (name: string) => chip(`${name}, a name of some length, with a part, and a second part`);

  test("test_each_chip_says_which_row_it_stands_in_and_two_that_share_stand_in_one", () => {
    expect(rowsOf([chip("One"), chip("Two"), long("Three"), chip("Four"), chip("Five"), chip("Six")])).toEqual([
      1, 1, 2, 3, 3, 4,
    ]);
    expect(rowsOf([long("One"), long("Two")])).toEqual([1, 2]);
    expect(rowsOf([])).toEqual([]);
  });

  test("test_a_search_whose_chips_stand_in_four_rows_is_all_in_sight", () => {
    // Measured on a phone 390 wide, on a plain search: six chips in four rows, 202 px, and
    // the first result whole on the first screen, from 454 to 828 of 844.
    const plain = [chip("Short"), chip("Tiny"), long("A place"), long("A sum"), chip("Choice", { cross: false }), chip("A few settings: 6 assumed", { cross: false })];

    expect(NARROW_ROWS).toEqual({ most: 4, folded: 2 });
    expect(rowsOf(plain).at(-1)).toBe(4);
    expect(inSight(lying(plain))).toBe(plain.length);
  });

  test("test_with_more_rows_than_four_the_chips_fold_to_two_rows_whatever_the_number_of_things", () => {
    // Measured on a phone 390 wide, on a search of seven things: seven chips in six rows,
    // 338 px, and the first result from 590 to 1,118 of 844. What stands over the answer
    // is said in short, and what is long is one press away.
    const seven = [chip("Short words"), chip("Tiny"), long("One"), long("Two"), long("Three"), long("Four"), chip("A few settings: 6 assumed", { cross: false })];

    expect(rowsOf(seven)).toEqual([1, 1, 2, 3, 4, 5, 6]);
    expect(inSight(lying(seven))).toBe(3);
    // However many there are, no more than two rows of them stand over the answer.
    for (const many of [7, 12, 40]) {
      const chips = Array.from({ length: many }, (_, at) => long(`Thing ${at}`));
      expect([many, inSight(lying(chips))]).toEqual([many, NARROW_ROWS.folded]);
    }
    // What stands in sight is the first of them, in the order they were drawn in.
    expect(inSight(lying([long("One"), chip("Two"), chip("Three"), long("Four"), long("Five"), long("Six")]))).toBe(3);
  });

  test("test_the_row_is_narrow_at_the_width_its_style_sheet_lays_it_out_by", () => {
    const sheet = readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8");
    const widths = [...sheet.matchAll(/@container \(max-width: ([\d.]+)rem\)/g)].map((found) => Number(found[1]));

    expect(widths.length).toBeGreaterThan(0);
    expect([...new Set(widths)]).toEqual([NARROW_REM]);
  });
});

describe("how many chips stand in sight on a wide row", () => {
  // A wide row lays its chips as they fall, as many to a row as fit, so how they lie is
  // not counted in letters: it is read from where each stands once the row is laid out.
  test("test_up_to_three_rows_every_chip_is_in_sight", () => {
    expect(WIDE_ROWS).toEqual({ most: 3, folded: 2 });
    expect(standing([0, 0, 56, 112, 112])).toBe(5);
    expect(standing([0, 56, 112])).toBe(3);
    expect(standing([0, 0, 0, 0, 0, 0])).toBe(6);
  });

  test("test_with_more_rows_the_chips_of_the_first_two_stand_and_the_rest_waits", () => {
    // Measured at 1440 by 900 after a sentence of a dozen things: six chips in five rows.
    expect(standing([0, 56, 56, 112, 168, 224])).toBe(3);
    expect(standing([0, 56, 112, 168])).toBe(2);
    expect(standing([0, 0, 0, 56, 112, 168])).toBe(4);
  });

  test("test_rows_are_told_apart_by_where_they_stand_whatever_a_row_is_high", () => {
    expect(standing([4, 4, 70, 136, 202, 202])).toBe(3);
    expect(standing([0, 48, 96, 144], { most: 2, folded: 1 })).toBe(1);
  });

  test("test_a_row_that_was_not_laid_out_folds_nothing", () => {
    // A browser that lays nothing out says that every chip stands at nought.
    expect(standing([0, 0, 0, 0, 0, 0, 0, 0])).toBe(8);
    expect(standing([])).toBe(0);
  });
});
