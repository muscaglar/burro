/** @jest-environment node */
/**
 * The words the website sets round the census figures of an area. Every word about a figure
 * is the API's. These name a state or a control, and say nothing of what a figure means:
 * ADR 0014, and docs/design/web.md, section 2.1, rule 6.
 */

import { recordedAnswer } from "@/lib/api/recorded";

import { CENSUS } from "./census";

const served = recordedAnswer("get_census", "census").body.data;

/** Words Burro would be choosing of a figure of who lived somewhere. */
const NEVER_SAID = [
  "diverse",
  "diversity",
  "mixed",
  "multicultural",
  "vibrant",
  "main",
  "largest",
  "biggest",
  "majority",
  "minority",
  "dominant",
  "predominantly",
  "mostly",
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

const copy = Object.values(CENSUS).map((words) => (typeof words === "function" ? words("the area", "the city") : words));

describe("the words round the census figures of an area", () => {
  test("test_no_word_is_one_burro_would_be_choosing_of_a_figure", () => {
    for (const words of copy) {
      expect([words, [...wordsIn(words)].filter((word) => NEVER_SAID.includes(word))]).toEqual([words, []]);
    }
  });

  test("test_no_line_holds_a_figure_and_none_names_a_group_of_people", () => {
    const rows = served.tables.flatMap((table) => table.rows.map((row) => row.label.toLowerCase()));

    expect(rows.length).toBeGreaterThan(40);
    for (const words of copy) {
      expect([words, /[%\d]/.test(words)]).toEqual([words, false]);
      expect([words, rows.filter((row) => words.toLowerCase().includes(row))]).toEqual([words, []]);
    }
  });

  test("test_the_line_about_the_picture_says_what_is_drawn_and_nothing_of_what_it_shows", () => {
    const said = CENSUS.picture("Here", "The city");

    // The bar is the area and the line is the city: both are named, as the API names them.
    expect(said).toMatch(/\bbar\b.*\bHere\b/);
    expect(said).toMatch(/\bline\b.*\bThe city\b/);
    // Which is the greater is for the person to read off the two figures.
    expect(said).not.toMatch(/\b(than|greater|fewer|larger|smaller|bigger|compare[sd]?)\b/i);
  });

  test("test_with_scripts_off_it_says_why_no_figure_is_in_the_page_and_how_to_see_them", () => {
    // The figures are not in the page as it is built, so that nothing keeps them.
    expect(CENSUS.noScript).toMatch(/\bonly when you open\b/);
    expect(CENSUS.noScript).toMatch(/\bJavaScript\b/);
  });

  test("test_a_count_that_is_not_given_is_said_to_be_not_given_and_never_as_nought", () => {
    expect(CENSUS.noCount).toBe("Not given");
  });
});
