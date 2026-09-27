/** @jest-environment node */

import { CHIPS } from "@/content/search";
import type { ChipPart } from "@/lib/search/chips";

import { IN_THE_ROW, inOneLine, saidBy, WAYS_IN_THE_ROW } from "./says";

const part = (text: string, assumed = false, always?: boolean): ChipPart => ({ text, assumed, always });

describe("what a chip says", () => {
  test("test_in_the_row_it_says_every_part_that_was_taken_and_marks_each_that_was_assumed", () => {
    // Seen in a browser: "40 minutes, Burro assumed the rest", of a journey that was taken
    // as a guide. Whether a limit is firm decides which areas are left out, and the chip
    // did not say it until it was pressed.
    const chip = { label: "A place", assumed: true, parts: [part("by a way", true), part("within a time"), part("flexible", true)] };
    const said = `A place, by a way ${CHIPS.assumed}, within a time, flexible ${CHIPS.assumed}`;

    expect(inOneLine(saidBy(chip, false))).toBe(said);
    expect(saidBy(chip, false).rest).toBe(false);
    // In full it says the same: nothing of a chip waits for a press.
    expect(inOneLine(saidBy(chip, true))).toBe(said);
    // However many parts nobody said.
    const none = { label: "A place", assumed: true, parts: [part("by a way", true), part("within a time", true), part("flexible", true)] };
    expect(inOneLine(saidBy(none, false))).toBe(
      `A place, by a way ${CHIPS.assumed}, within a time ${CHIPS.assumed}, flexible ${CHIPS.assumed}`,
    );
  });

  test("test_one_line_of_the_look_has_the_row_say_once_that_the_rest_was_assumed_as_it_did", () => {
    expect(WAYS_IN_THE_ROW).toEqual(["each", "rest"]);
    expect(IN_THE_ROW).toBe("each");

    // The other way it was built: what was said, and once that the rest was assumed.
    const chip = { label: "A place", assumed: true, parts: [part("by a way", true), part("within a time", true), part("flexible")] };
    expect(inOneLine(saidBy(chip, false, "rest"))).toBe(`A place, flexible, ${CHIPS.restAssumed}`);
    expect(inOneLine(saidBy(chip, true, "rest"))).toBe(
      `A place, by a way ${CHIPS.assumed}, within a time ${CHIPS.assumed}, flexible`,
    );
    // One part that nobody said is named there too, and so is a part that is never left for a press.
    const one = { label: "A sum", assumed: true, parts: [part("a kind of home"), part("flexible", true)] };
    expect(inOneLine(saidBy(one, false, "rest"))).toBe(`A sum, a kind of home, flexible ${CHIPS.assumed}`);
    const always = { label: "A place", assumed: true, parts: [part("by a way", true), part("within a time", true), part("flexible", true, true)] };
    expect(inOneLine(saidBy(always, false, "rest"))).toBe(`A place, flexible ${CHIPS.assumed}, ${CHIPS.restAssumed}`);
  });

  test("test_one_part_nobody_said_is_named_and_the_word_stands_on_it_alone", () => {
    const chip = { label: "A sum", assumed: true, parts: [part("a kind of home"), part("flexible", true)] };

    expect(inOneLine(saidBy(chip, false))).toBe(`A sum, a kind of home, flexible ${CHIPS.assumed}`);
    expect(saidBy(chip, false).rest).toBe(false);
  });

  test("test_a_chip_nobody_said_the_whole_of_says_so_after_its_name", () => {
    const chip = { label: "A choice", assumed: true, parts: [] };

    expect(saidBy(chip, false).whole).toBe(true);
    expect(inOneLine(saidBy(chip, false))).toBe(`A choice ${CHIPS.assumed}`);
    expect(inOneLine(saidBy(chip, true))).toBe(`A choice ${CHIPS.assumed}`);
  });

  test("test_a_part_that_is_never_left_for_a_press_is_said_in_the_row_though_nobody_said_it", () => {
    const chip = { label: "A vibe", assumed: true, parts: [part("read one way of two", true, true)] };

    expect(inOneLine(saidBy(chip, false))).toBe(`A vibe, read one way of two ${CHIPS.assumed}`);
    expect(saidBy(chip, false).rest).toBe(false);
  });

  test("test_what_a_person_said_the_whole_of_says_no_more_than_that", () => {
    const chip = { label: "A vibe", assumed: false, parts: [part("a mark of it")] };

    expect(inOneLine(saidBy(chip, false))).toBe("A vibe, a mark of it");
    expect(inOneLine(saidBy(chip, false))).toBe(inOneLine(saidBy(chip, true)));
  });
});
