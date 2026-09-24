/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, Fact } from "@/lib/api/schema";

import { sentenceOf, TEMPLATES } from "./templates";

const contract = readFileSync(path.resolve(__dirname, "../../../../docs/design/contract.md"), "utf8").replace(
  /[ \t]+/g,
  " ",
);
const facts: Fact[] = readdirSync(path.join(recordedFolder(), "area")).flatMap(
  (file) => (readRecorded(`area/${file.replace(/\.json$/, "")}`).body as { data: AreaData }).data.facts,
);

describe("a sentence filled from the slots of a fact", () => {
  test.each(Object.entries(TEMPLATES))(
    "test_the_template_is_the_contracts_own_word_for_word: %s",
    (template, words) => {
      // The row of the contract's table of templates: its id, and then its words.
      expect(contract.includes(`| \`${template}\` | ${words}`)).toBe(true);
    },
  );

  test("test_every_recorded_fact_of_these_templates_makes_a_whole_sentence_of_its_own_slots", () => {
    const held = facts.filter((fact) => fact.template in TEMPLATES);

    expect(held.length).toBeGreaterThan(100);
    for (const fact of held) {
      const said = sentenceOf(fact);
      expect(said).not.toBeNull();
      expect(said?.includes("{")).toBe(false);
      expect(said?.includes("undefined")).toBe(false);
      // Every figure and every name in it is a slot of the fact.
      for (const figure of said?.match(/\d+/g) ?? []) {
        expect(Object.values(fact.slots).some((value) => value.includes(figure))).toBe(true);
      }
    }
  });

  test("test_a_sentence_is_what_the_contract_says_of_a_likeness", () => {
    const fact = facts.find((one) => one.fact_id === "syn-n0022/likeness/syn-n0024");

    expect(fact && sentenceOf(fact)).toBe(
      "Thrushcombe is in the same band as Wickerford on 7 of the 23 measures compared, and least alike in Daily life.",
    );
  });

  test("test_a_fact_that_lacks_a_slot_makes_no_sentence_and_nothing_is_filled_in", () => {
    const fact = facts.find((one) => one.template === "likeness");
    if (!fact) throw new Error("no recorded likeness");
    const slots = Object.fromEntries(Object.entries(fact.slots).filter(([name]) => name !== "family"));

    expect(sentenceOf({ ...fact, slots })).toBeNull();
    expect(sentenceOf({ ...fact, slots: { ...fact.slots, same: "" } })).toBeNull();
  });

  test("test_a_template_that_is_not_held_here_makes_no_sentence", () => {
    const fact = facts.find((one) => one.template === "feature");
    if (!fact) throw new Error("no recorded feature");

    expect(sentenceOf(fact)).toBeNull();
  });

  test("test_a_sentence_the_api_sends_with_a_fact_is_shown_in_place_of_the_template", () => {
    const fact = facts.find((one) => one.template === "likeness");
    if (!fact) throw new Error("no recorded likeness");

    expect(sentenceOf({ ...fact, text: "The API's own words." } as Fact)).toBe("The API's own words.");
  });
});
