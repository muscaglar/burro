/** @jest-environment node */
/**
 * The words the website sets round the household income of an area. Every word about the
 * figure is the API's. These name a state or a control, and say nothing of what the figure
 * means or of how well off anybody is: ADR 0028, and docs/design/web.md, section 2.2.
 */

import { INCOME } from "./income";

/** Words Burro would be choosing of the figure. */
const NEVER_SAID = [
  "affluent",
  "rich",
  "poor",
  "wealthy",
  "deprived",
  "typical",
  "average",
  "high",
  "low",
  "higher",
  "lower",
  "above",
  "below",
  "more",
  "less",
];

const wordsIn = (text: string) => new Set(text.toLowerCase().match(/[a-z]+/g) ?? []);

const copy: string[] = Object.values(INCOME);

describe("the words round the household income of an area", () => {
  test("test_no_word_is_one_burro_would_be_choosing_of_the_figure", () => {
    for (const words of copy) {
      expect([words, [...wordsIn(words)].filter((word) => NEVER_SAID.includes(word))]).toEqual([words, []]);
    }
  });

  test("test_no_line_holds_a_figure_or_a_sum_of_money", () => {
    for (const words of copy) expect([words, /[£%\d]/.test(words)]).toEqual([words, false]);
  });

  test("test_with_scripts_off_it_says_why_the_figure_is_not_in_the_page_and_how_to_see_it", () => {
    // The figure is not in the page as it is built, so that nothing keeps it.
    expect(INCOME.noScript).toMatch(/\bonly when you open\b/);
    expect(INCOME.noScript).toMatch(/\bJavaScript\b/);
  });

  test("test_it_speaks_of_one_figure_where_the_census_speaks_of_many", () => {
    // One estimate is served for an area, and the words say "the figure" of it.
    for (const words of [INCOME.loading, INCOME.failed, INCOME.noScript, INCOME.notes]) {
      expect([words, /\bfigures\b/.test(words)]).toEqual([words, false]);
      expect([words, /\bfigure\b/.test(words)]).toEqual([words, true]);
    }
  });
});
