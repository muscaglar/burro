/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, AreasData, PlacesData } from "@/lib/api/schema";

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

  test("test_the_line_about_a_persons_words_says_what_the_record_says_of_the_provider", () => {
    const line = copy.find(([where]) => where === "site.ts.WORDS_LINE")?.[1] ?? "";

    // ADR 0005 is where the project says what becomes of the words. The website may not
    // promise more than it does: the provider keeps them for 30 days, and longer if flagged.
    expect(decision("0005-raw-prompts-are-never-stored.md")).toContain(
      "The provider retains inputs for up to 30 days, longer if flagged.",
    );
    expect(line).toContain("Burro does not keep it");
    expect(line).toContain("for up to 30 days, or longer if it is flagged");
    // The same line is on the methods page, and is not written a second time there.
    expect(copy.filter(([, text]) => /30 days/.test(text)).map(([where]) => where)).toEqual([
      "methods.ts.METHODS.words.points[0]",
      "site.ts.WORDS_LINE",
    ]);
  });

  test("test_a_range_of_cost_is_explained_in_words_a_newcomer_knows", () => {
    const lead = copy.find(([where]) => where === "area.ts.AREA.cost.lead")?.[1] ?? "";

    // It read "the lower and the upper quartile", and "the median".
    expect(copy.filter(([, text]) => /\b(quartile|median|percentile)s?\b/i.test(text))).toEqual([]);
    expect(lead).toContain("Half of homes of this kind cost between these two figures.");
  });

  test("test_the_banner_says_the_three_things_it_must", () => {
    const banner = copy.find(([where]) => where === "site.ts.BANNER.text")?.[1];

    expect(banner).toBe(
      "This is made-up test data. The city, its places and every figure are invented. " +
        "Nothing here describes a real place.",
    );
  });
});
