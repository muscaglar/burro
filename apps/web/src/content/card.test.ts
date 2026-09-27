/** @jest-environment node */
/**
 * The words a result says on a line and under its fit, which the look added. They stand on
 * a result before anything is opened, where the first result is whole on the first screen
 * of a phone: so each is as short as it can be and still be understood.
 */

import { CARD } from "./card";
import { KNOWN } from "./kit";
import { CHIPS, JOURNEYS } from "./search";

/** A name that stands in a gap, where a line is filled with a name the API sent. */
const GAP = "Somewhere";

describe("what a line of a journey and of a budget says", () => {
  test("test_the_side_a_figure_falls_on_is_one_word_and_is_the_word_the_working_says_it_in", () => {
    expect(CARD.side).toEqual({ within: "within", over: "over" });
    expect([CARD.side.within, CARD.side.over]).toEqual([JOURNEYS.within, JOURNEYS.over]);
    for (const word of Object.values(CARD.side)) expect(/^[a-z]+$/.test(word)).toBe(true);
  });

  test("test_no_side_is_said_as_the_better_one", () => {
    const verdict = /\b(best|better|worst|worse|good|bad|cheap|dear|expensive|affordable|too)\b/i;

    expect(Object.values(CARD.side).filter((word) => verdict.test(word))).toEqual([]);
    expect(verdict.test(CARD.listedLower)).toBe(false);
  });

  test("test_what_a_home_costs_keeps_its_unit_and_a_rent_is_by_the_month", () => {
    // The amount is the API's, as it formatted it: nothing of it is rounded or left out.
    expect(CARD.cost("1,300", true)).toBe("£1,300 a month");
    expect(CARD.cost("415,000", false)).toBe("£415,000");
    expect(CARD.cost(GAP, true)).toContain(GAP);
  });
});

describe("the press that shows the rest of the lines of a result", () => {
  test("test_it_says_how_many_more_there_are_as_the_press_of_the_chips_does", () => {
    expect(CARD.more(3)).toBe("+3 more");
    expect(CARD.more(1)).toBe("+1 more");
    expect([CARD.more(4), CARD.fewer]).toEqual([CHIPS.rest(4), CHIPS.showFewer]);
  });

  test("test_what_is_seen_on_it_is_the_start_of_its_name", () => {
    for (const seen of [CARD.more(3), CARD.fewer]) {
      expect(CARD.moreOf(seen, GAP)).toBe(`${seen}: ${GAP}`);
      expect(CARD.moreOf(seen, GAP).startsWith(seen)).toBe(true);
    }
  });
});

describe("what a result says under its fit of an area that lacks a figure", () => {
  test("test_it_is_one_whole_sentence_that_says_what_follows_and_why", () => {
    expect(CARD.listedLower).toBe("This area is listed lower because it has no data for something you asked for.");
    expect(CARD.listedLower.split(/(?<=[.?])\s+/)).toHaveLength(1);
    expect(CARD.listedLower).toMatch(/\bbecause\b/);
    // It says it in the two words of the line that names what the area lacks.
    expect(CARD.listedLower).toContain(KNOWN.none);
    // It names no place and holds no figure.
    expect(/\d/.test(CARD.listedLower)).toBe(false);
  });

  test("test_the_heading_over_the_figures_of_the_working_names_the_gauges_of_a_vibe_and_of_a_measure", () => {
    expect(CARD.vibes).toBe("The figures behind each gauge");
  });
});
