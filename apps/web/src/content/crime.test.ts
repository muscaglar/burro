/** @jest-environment node */
import { readFileSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";

import { askingFor, CRIME_ACCOUNT, CRIME_RULE, crimeParts, crimeVibes, ruleIn } from "./crime";
import { METHODS } from "./methods";
import { REJECTED, whyRefused } from "./search";
import { CRIME } from "./settings";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
/** The release where gritty is built from land use alone, and holds no figure of crime. */
const variantA: MetaData = (readRecorded("variant-a/meta").body as { data: MetaData }).data;

const contract = readFileSync(path.resolve(__dirname, "../../../../docs/design/contract.md"), "utf8").replace(
  /\s+/g,
  " ",
);

describe("when recorded crime counts", () => {
  test("test_every_page_that_speaks_of_it_says_the_one_rule_word_for_word", () => {
    // The search, where an edit is refused. The settings. The methods.
    expect(REJECTED.crime_needs_explicit_request).toBe(CRIME_RULE);
    expect(CRIME.lead.startsWith(CRIME_RULE)).toBe(true);
    // Among the points of the ranking it stands in the one that says what is never taken for a person.
    expect(METHODS.ranking.points.filter((point) => point.includes(CRIME_RULE))).toHaveLength(1);
    expect(CRIME_ACCOUNT.rule).toBe(CRIME_RULE);
  });

  test("test_no_page_says_it_another_way", () => {
    const said = [
      ...Object.values(REJECTED),
      CRIME.lead,
      ...METHODS.ranking.points,
      ...METHODS.words.points,
      METHODS.vibes.lead,
    ].filter((text) => /crime/i.test(text));

    expect(said.length).toBeGreaterThanOrEqual(3);
    for (const text of said) expect(text.includes(CRIME_RULE)).toBe(true);
  });

  test("test_the_rule_says_what_the_contract_says", () => {
    expect(contract).toContain("Crime is weighted only when the user asks for it or moves its control.");
    // Only when it is asked for, and the three ways of asking, each in words a person follows.
    expect(CRIME_RULE).toMatch(/\bonly when you ask for it\b/);
    for (const way of ["ask for it by name", "switch it on under Space requirements", "ask for a vibe that includes it"]) {
      expect(CRIME_RULE).toContain(way);
    }
    // It names no vibe, so that it is true of either way gritty is built.
    for (const tag of [...meta.tags, ...variantA.tags]) expect(CRIME_RULE.includes(tag.label)).toBe(false);
    expect(/\b(safe|unsafe|dangerous)\b/i.test(Object.values(CRIME_ACCOUNT).join(" "))).toBe(false);
  });

  test("test_the_rule_is_said_of_what_was_recorded_and_in_no_word_of_the_design", () => {
    const said = Object.values(CRIME_ACCOUNT).join(" ");

    // What is counted is what was recorded, and every line that names it says "recorded".
    expect(said.match(/\bcrime\b/g)?.length).toBe(said.match(/\brecorded crime\b/gi)?.length);
    expect(/\b(recipe|this data|release)\b/i.test(said)).toBe(false);
  });

  test("test_where_no_vibe_holds_recorded_crime_the_rule_is_followed_by_a_line_that_says_so", () => {
    // Seen in a browser, where gritty is built from land use: the rule named "a vibe whose
    // recipe holds it", and none does. The rule is one sentence on every release, so the
    // line that follows it says what is true of this one.
    expect(ruleIn(meta)).toBe(CRIME_RULE);
    expect(ruleIn(variantA)).toBe(`${CRIME_RULE} ${CRIME_ACCOUNT.noVibe}`);
    expect(whyRefused("crime_needs_explicit_request", variantA)).toBe(ruleIn(variantA));
    expect(whyRefused("crime_needs_explicit_request", meta)).toBe(CRIME_RULE);
    // Every other refusal is said as it was.
    expect(whyRefused("out_of_range", variantA)).toBe(REJECTED.out_of_range);
  });

  test("test_which_vibe_holds_recorded_crime_is_read_from_the_release_and_never_written_down", () => {
    const held = crimeVibes(meta);

    expect(held.map(({ tag }) => tag.tag_id)).toEqual(["street_character"]);
    expect(held[0]?.parts.map((part) => part.label)).toEqual([
      "Recorded criminal damage and arson",
      "Recorded anti-social behaviour",
    ]);
    // Built the other way, gritty is land use alone, and no vibe holds recorded crime.
    expect(crimeVibes(variantA)).toEqual([]);
    expect(variantA.tags.map((tag) => tag.tag_id)).toContain("works_warehouses");
  });

  test("test_what_asking_for_such_a_vibe_is_speaks_of_two_ends_only_where_the_vibe_has_two", () => {
    expect(askingFor({ low_end: "Polished", high_end: "Gritty" })).toBe(CRIME_ACCOUNT.asking);
    expect(askingFor({ low_end: null, high_end: null })).toBe(CRIME_ACCOUNT.askingOneWay);
    expect(CRIME_ACCOUNT.asking).toMatch(/\beither end\b/);
    expect(CRIME_ACCOUNT.askingOneWay.includes("end")).toBe(false);
  });

  test("test_to_ask_for_such_a_vibe_is_to_ask_for_recorded_crime_by_name_and_both_lines_say_so", () => {
    // ADR 0013: to ask for the vibe is to ask for recorded crime by name, and then it counts.
    for (const said of [CRIME_ACCOUNT.asking, CRIME_ACCOUNT.askingOneWay]) {
      expect(said).toMatch(/\bask for this vibe\b/);
      expect(said).toMatch(/\basking for recorded crime by name\b/);
      expect(said).toMatch(/\bcount\b/);
    }
  });

  test("test_the_parts_of_crime_are_those_the_release_files_under_crime_and_no_other", () => {
    for (const tag of meta.tags) {
      for (const part of crimeParts(tag, meta.features)) {
        expect(part.dimension).toBe("crime");
        expect(tag.terms.map((term) => term.feature_id)).toContain(part.feature_id);
      }
    }
    expect(crimeParts({ terms: [] }, meta.features)).toEqual([]);
  });
});
