/** @jest-environment node */
/**
 * The names of the columns a fact is laid out under. A name says what the figure under it
 * is a figure of, and in what it is counted. It holds no figure, passes no judgement, and
 * takes nothing from what the figure says.
 */

import { readdirSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, Fact } from "@/lib/api/schema";

import { CANNOT_PLACE, FACT_COLUMNS, FACT_KIND, ONE_NUMBER } from "./facts";

const facts: Fact[] = readdirSync(path.join(recordedFolder(), "area")).flatMap(
  (file) => (readRecorded(`area/${file.replace(/\.json$/, "")}`).body as { data: AreaData }).data.facts,
);

type Column = keyof typeof FACT_COLUMNS;

describe("the name of a column", () => {
  test("test_no_figure_stands_in_the_name_of_a_column_or_of_a_row", () => {
    const names = [...Object.values(FACT_COLUMNS), ...Object.values(FACT_KIND), CANNOT_PLACE, ONE_NUMBER];

    expect(names.filter((name) => /\d/.test(name))).toEqual([]);
  });

  test("test_no_two_columns_bear_one_name", () => {
    // A row is laid out by the names of its columns, so two of one name would be one column.
    const names = Object.values(FACT_COLUMNS);

    expect(names.filter((name, at) => names.indexOf(name) !== at)).toEqual([]);
  });

  test("test_a_column_of_minutes_says_minutes_because_the_figure_under_it_is_a_bare_number", () => {
    const ofMinutes: Column[] = ["typical", "missed", "minutes", "moreThan", "walk", "limit", "underLimit", "overLimit"];

    for (const column of ofMinutes) expect([column, /\bminutes\b/i.test(FACT_COLUMNS[column])]).toEqual([column, true]);
    // And the slots they are filled from hold a number and no unit, in every recorded fact.
    const walks = facts.filter((fact) => fact.template === "station").map((fact) => fact.slots.walk ?? "");
    expect(walks.length).toBeGreaterThan(20);
    expect(walks.filter((walk) => !/^\d+$/.test(walk))).toEqual([]);
  });

  test("test_a_column_that_counts_out_of_a_whole_says_the_whole", () => {
    // A band is one of five, and what a band rests on is counted out of a hundred. Neither
    // slot says so, so the name of its column does, in words.
    expect(FACT_COLUMNS.band).toMatch(/\bfive\b/);
    expect(FACT_COLUMNS.share).toMatch(/\bhundred\b/);
    expect(FACT_COLUMNS.rents).toMatch(/to the nearest ten/);
    const bands = facts.filter((fact) => fact.template === "vibe").map((fact) => fact.slots.band ?? "");
    expect(bands.filter((band) => !/^[1-5]$/.test(band))).toEqual([]);
  });

  test("test_the_columns_of_what_a_band_rests_on_say_whose_figures_are_counted", () => {
    // How many measurements Burro has for the area, of how many the vibe uses: the first
    // is of the area, the second of the vibe, and each name says which.
    expect(FACT_COLUMNS.partsKnown).toMatch(/\bthis area\b/);
    expect(FACT_COLUMNS.parts).toMatch(/\bvibe\b/);
    expect(FACT_COLUMNS.partsDated).toMatch(/\bmeasurements\b/);
  });

  test("test_a_name_passes_no_judgement_and_softens_nothing", () => {
    const names = [...Object.values(FACT_COLUMNS), ...Object.values(FACT_KIND), CANNOT_PLACE, ONE_NUMBER];
    const judged = /\b(good|bad|best|worst|better|worse|only|just|about|around|roughly|nearly|almost)\b/i;
    // "If you just miss a service" is the time the service gives, and is the one place the word stands.
    const said = names.filter((name) => judged.test(name) && name !== FACT_COLUMNS.missed);

    expect(said).toEqual([]);
  });

  test("test_every_row_has_a_name_where_nothing_else_names_it", () => {
    const templates = new Set(facts.map((fact) => fact.template));

    expect(templates.size).toBeGreaterThan(8);
    for (const template of templates) expect([template, FACT_KIND[template].length > 0]).toEqual([template, true]);
  });
});

describe("what is said in the place of a figure", () => {
  test("test_a_vibe_that_was_not_worked_out_says_so_and_names_no_band", () => {
    expect(CANNOT_PLACE).toMatch(/\bBurro could not work out\b/);
    expect(CANNOT_PLACE).not.toMatch(/\bband\b|\bmiddle\b/);
  });

  test("test_a_price_that_is_one_number_says_what_its_publisher_does_not_give", () => {
    // No range, and no count of the sales it rests on: both are said, and neither is guessed.
    expect(ONE_NUMBER).toMatch(/\bno range\b/);
    expect(ONE_NUMBER).toMatch(/\bhow many sales\b/);
    expect(ONE_NUMBER).toMatch(/\bpublisher\b/);
  });
});
