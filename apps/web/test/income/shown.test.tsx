/**
 * How household income is shown, so that it is read as its publisher's estimate and not
 * as a verdict of Burro's. Held here: in the style sheet, and in the words.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { INCOME } from "@/content/income";
import { recordedAnswer } from "@/lib/api/recorded";

import { rulesOf } from "../support/css";

const SRC = path.resolve(__dirname, "..", "..", "src");
const SHEET = path.join(SRC, "components", "IncomePanel", "IncomePanel.module.css");
const offer = recordedAnswer("get_meta", "meta").body.data.income;
const served = recordedAnswer("get_income", "income").body.data;

/** Words Burro would be choosing of the figure. The API's own words are held to the same in core. */
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
  "above",
  "below",
  "more",
  "less",
];

const wordsOf = (text: string) => new Set(text.toLowerCase().match(/[a-z]+/g) ?? []);

describe("no colour and no size says much or little", () => {
  const rules = rulesOf(readFileSync(SHEET, "utf8"));

  test("test_every_colour_is_one_the_text_of_the_page_is_drawn_in", () => {
    const colours = rules.flatMap((rule) =>
      [...rule.sets].filter(([, value]) => /var\(--|#[0-9a-f]{3,8}\b|rgb|hsl/i.test(value)).map(([, value]) => value),
    );
    const tokens = new Set(colours.flatMap((value) => value.match(/--[a-z0-9-]+/g) ?? []));
    const ofColour = [...tokens].filter((token) => !/^--(space|size|radius|target|motion|leading)/.test(token));

    expect(ofColour.sort()).toEqual(["--muted"]);
    expect(colours.filter((value) => /#[0-9a-f]{3,8}\b|rgb|hsl/i.test(value))).toEqual([]);
  });

  test("test_the_figure_is_set_in_the_type_of_the_page", () => {
    const ofTheFigure = rules.filter((rule) => /\bdd\b/.test(rule.selector));
    for (const rule of ofTheFigure) {
      expect([...rule.sets.keys()].filter((property) => /font|color|background/.test(property))).toEqual([]);
    }
    expect(rules.some((rule) => [...rule.sets.keys()].some((property) => /^background/.test(property)))).toBe(false);
  });
});

describe("no word is one Burro would be choosing", () => {
  test("test_the_site_copy_names_controls_and_states_and_says_nothing_of_a_figure", () => {
    const said = Object.values(INCOME).join(" ");

    expect([...wordsOf(said)].filter((word) => NEVER_SAID.includes(word))).toEqual([]);
    expect(/[£%\d]/.test(said)).toBe(false);
  });

  test("test_what_the_api_says_of_the_figure_is_the_publishers_and_holds_none_either", () => {
    const ours = [offer.heading, offer.intro, served.kind, served.modelled, served.year_line, served.limits_label];
    const found = ours.flatMap((said) => [...wordsOf(said)].filter((word) => NEVER_SAID.includes(word)));

    expect(found).toEqual([]);
    expect(offer.intro).toMatch(/never ranks, filters or compares areas by it/);
  });
});
