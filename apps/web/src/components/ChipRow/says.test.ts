/** @jest-environment node */

import { CHIPS } from "@/content/search";
import type { ChipPart } from "@/lib/search/chips";

import { inOneLine, saidBy } from "./says";

const part = (text: string, assumed = false, always?: boolean): ChipPart => ({ text, assumed, always });

describe("what a chip says", () => {
  test("test_in_the_row_it_says_what_was_said_and_once_that_the_rest_was_assumed", () => {
    const chip = { label: "A place", assumed: true, parts: [part("by a way", true), part("within a time"), part("flexible", true)] };

    expect(inOneLine(saidBy(chip, false))).toBe(`A place, within a time, ${CHIPS.restAssumed}`);
    expect(inOneLine(saidBy(chip, true))).toBe(
      `A place, by a way ${CHIPS.assumed}, within a time, flexible ${CHIPS.assumed}`,
    );
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
