/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, AreasData, MetaData, PlacesData } from "@/lib/api/schema";

const CONTENT = path.resolve(__dirname, "..", "src", "content");

/** Every string of every file of site copy, with where it was found. */
function siteCopy(): [where: string, text: string][] {
  const found: [string, string][] = [];
  const walk = (where: string, value: unknown) => {
    if (typeof value === "string") found.push([where, value]);
    else if (Array.isArray(value)) value.forEach((part, at) => walk(`${where}[${at}]`, part));
    else if (typeof value === "object" && value !== null) {
      for (const [key, part] of Object.entries(value)) walk(`${where}.${key}`, part);
    }
  };
  for (const file of readdirSync(CONTENT).filter((name) => /\.tsx?$/.test(name)).sort()) {
    if (/\.test\.tsx?$/.test(file)) continue;
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    walk(file, require(path.join(CONTENT, file)));
  }
  return found;
}

/** Every name of the recorded release: areas, boroughs, stations, lines and places. */
function namesOfPlaces(): string[] {
  const names = new Set<string>();
  const areas = (readRecorded("areas").body as { data: AreasData }).data.areas;
  for (const area of areas) {
    names.add(area.name);
    names.add(area.borough);
    const profile = (readRecorded(`area/${area.slug}`).body as { data: AreaData }).data;
    for (const station of profile.stations) {
      names.add(station.name);
      station.lines.forEach((line) => names.add(line));
    }
    for (const fact of profile.facts) fact.names.forEach((name) => names.add(name));
  }
  for (const file of readdirSync(recordedFolder())) {
    if (!file.startsWith("places-search") || !file.endsWith(".json")) continue;
    const body = readRecorded(file.slice(0, -".json".length)).body as { data?: PlacesData };
    body.data?.places.forEach((place) => names.add(place.name));
  }
  return [...names].filter((name) => name.trim().length > 2);
}

const copy = siteCopy();

/** Every provider the contract names, read from the contract itself. */
const PROVIDERS: string[] = (
  JSON.parse(
    readFileSync(path.resolve(__dirname, "..", "..", "..", "contracts", "openapi.json"), "utf8"),
  ) as { components: { schemas: { Provider: { enum: string[] } } } }
).components.schemas.Provider.enum;

/** A decision of the project, as its record states it. */
const decision = (file: string) =>
  readFileSync(path.resolve(__dirname, "..", "..", "..", "docs", "adr", file), "utf8").replace(/\s+/g, " ");

describe("site copy", () => {
  test("test_site_copy_names_no_place", () => {
    const names = namesOfPlaces();

    const naming = copy.filter(([, text]) =>
      names.some((name) => new RegExp(`\\b${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(text)),
    );

    expect(names.length).toBeGreaterThan(30);
    expect(copy.length).toBeGreaterThan(80);
    expect(naming).toEqual([]);
  });

  test("test_site_copy_never_calls_a_place_safe_or_unsafe", () => {
    // The words the verifier bans from any sentence about a place.
    const banned = /\b(safe|safer|safest|unsafe|dangerous|rough|rougher|dodgy|sketchy)\b/i;

    expect(copy.filter(([, text]) => banned.test(text))).toEqual([]);
  });

  test("test_site_copy_is_plain_with_no_exclamation_mark_and_no_emoji", () => {
    const loud = copy.filter(([, text]) => /!|\p{Extended_Pictographic}/u.test(text));

    expect(loud).toEqual([]);
  });

  test("test_the_line_about_a_persons_words_says_what_burro_does_and_nothing_of_a_provider", () => {
    const line = copy.find(([where]) => where === "site.ts.WORDS_LINE")?.[1] ?? "";

    // ADR 0005 is where the project says what becomes of the words in Burro's own hands.
    // What a provider keeps is no longer said there, for it differs by provider.
    const record = decision("0005-raw-prompts-are-never-stored.md");
    expect(record).toContain(
      "Raw prompt text and destination strings are never written to any log, error report or database table.",
    );
    expect(record).not.toContain("The provider retains inputs for up to 30 days");
    expect(line).toBe("What you type is sent to Burro to be read, and Burro does not keep it.");
    // The same line is on the methods page, and is not written a second time there.
    expect(copy.filter(([, text]) => text === line).map(([where]) => where)).toEqual([
      "methods.ts.METHODS.words.points[0]",
      "site.ts.WORDS_LINE",
    ]);
  });

  test("test_site_copy_names_no_provider_and_states_none_of_its_terms", () => {
    // Who reads what is typed, how long it is kept, whether it is used to train and where
    // it is handled differ by provider, and are the service's to say. Every provider the
    // service can tell of is in its contract and its recorded answers, and none is in site copy.
    const told = ["meta-model-reads", "meta-model-reads-with-settings"].map(
      (recorded) => (readRecorded(recorded).body as { data: MetaData }).data.reader,
    );
    const names = [...PROVIDERS, ...told.flatMap((reader) => [reader.provider, reader.company])]
      .filter((name): name is string => typeof name === "string")
      .map((name) => name.toLowerCase());
    const terms = /\b\d+ (days?|years?|months?)\b|\bretain|\btrain(s|ed|ing)? (its|their|a|the) models?\b/i;

    expect(new Set(names).size).toBeGreaterThanOrEqual(PROVIDERS.length);
    expect(copy.filter(([, text]) => names.some((name) => text.toLowerCase().includes(name)))).toEqual([]);
    expect(copy.filter(([, text]) => terms.test(text))).toEqual([]);
    expect(copy.filter(([, text]) => told.some((reader) => text.includes(reader.notice)))).toEqual([]);
  });

  test("test_a_range_of_cost_is_explained_in_words_a_newcomer_knows", () => {
    const lead = copy.find(([where]) => where === "area.ts.AREA.cost.lead")?.[1] ?? "";

    // It read "the lower and the upper quartile", and "the median".
    expect(copy.filter(([, text]) => /\b(quartile|median|percentile)s?\b/i.test(text))).toEqual([]);
    expect(lead).toContain("Half of homes of this kind cost between these two figures.");
  });

  test("test_the_accessibility_statement_does_not_say_what_kind_of_data_is_shown", () => {
    // Seen on a build of a real city: under the banner that says the figures are of real
    // places, the statement said "This is a test release on made-up data." The statement is
    // drawn on every release, and only an answer knows whether its data is made up.
    const said = copy.filter(([where, text]) => where.startsWith("accessibility.ts") && /made.up/i.test(text));

    expect(said.map(([where]) => where)).toEqual([]);
  });

  test("test_the_banner_says_the_three_things_it_must", () => {
    const banner = copy.find(([where]) => where === "site.ts.BANNER.text")?.[1];

    expect(banner).toBe(
      "This is made-up test data. The city, its places and every figure are invented. " +
        "Nothing here describes a real place.",
    );
  });
});
