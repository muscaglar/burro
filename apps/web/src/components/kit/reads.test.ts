/** @jest-environment node */
import { holdsAFigure } from "./reads";

describe("which words are read", () => {
  test("test_words_that_hold_a_figure_are_read_whatever_they_stand_in", () => {
    expect(["Add the 4 that need no choice", "A budget of £400,000", "Within 35 minutes", "Show 3 more", 8].map(holdsAFigure)).toEqual([
      true,
      true,
      true,
      true,
      true,
    ]);
  });

  test("test_a_short_label_with_no_figure_in_it_is_a_name", () => {
    expect(["Search", "Start again", "Pubs and bars", "Done", ""].map(holdsAFigure)).toEqual([false, false, false, false, false]);
  });

  test("test_what_is_no_line_of_words_is_not_read_for_a_figure", () => {
    // Words the page has set itself are the page's to say: it hands `reads` where they are read.
    expect([null, undefined, ["Add the 4"], { says: "4" }].map(holdsAFigure)).toEqual([false, false, false, false]);
  });
});
