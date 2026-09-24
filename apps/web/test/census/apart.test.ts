/** @jest-environment node */
/**
 * The census is apart from everything else the website does. Only the page of
 * an area asks for it, only when a person opens it, and nothing of it is in
 * any other answer the website reads. These read the source and the recorded
 * answers, so they hold whatever is written next as well as what is there now.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { ROUTES } from "@/lib/api/operations";
import { readRecorded, recordedAnswer } from "@/lib/api/recorded";

const ROOT = path.resolve(__dirname, "..", "..");
const SRC = path.join(ROOT, "src");
const RECORDED = path.join(ROOT, "test", "recorded");

function filesUnder(folder: string, found: string[] = []): string[] {
  for (const entry of readdirSync(folder, { withFileTypes: true })) {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) filesUnder(file, found);
    else found.push(file);
  }
  return found;
}

const source = filesUnder(SRC).filter((file) => /\.tsx?$/.test(file) && !/\.test\.tsx?$/.test(file));
const named = (file: string) => path.relative(SRC, file);
/** The code of a file, with what is said in comments taken out. */
const code = (file: string) => readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\/|(?<![:"'`])\/\/.*$/gm, "");
const GENERATED = ["lib/api/schema.d.ts", "lib/api/required.ts"];
const own = source.filter((file) => !GENERATED.includes(named(file)));

const served = recordedAnswer("get_census", "census").body.data;

/** What is in the census and nowhere else: every code, every heading of a row, every title of a table. */
function canaries(): string[] {
  const rows = served.tables.flatMap((table) => table.rows);
  return [
    ...served.tables.flatMap((table) => [table.table_code, table.title, table.caption]),
    ...rows.map((row) => row.code),
    ...rows.map((row) => row.heading).filter((heading) => /made-up/i.test(heading)),
  ].map((mark) => mark.toLowerCase());
}

describe("only the page of an area asks for the census", () => {
  test("test_one_component_calls_the_route_and_one_page_draws_it", () => {
    const calls = own.filter((file) => /\bgetCensus\b/.test(code(file))).map(named);
    const draws = own.filter((file) => /<CensusPanel\b/.test(code(file))).map(named);

    expect(calls.sort()).toEqual(["components/CensusPanel/CensusPanel.tsx", "lib/api/client.ts"]);
    expect(draws).toEqual(["components/AreaProfile/AreaProfile.tsx"]);
  });

  test("test_the_area_page_is_the_only_page_that_draws_the_profile", () => {
    const pages = own.filter((file) => /<AreaProfile\b/.test(code(file))).map(named);

    expect(pages).toEqual(["app/[city]/[area]/page.tsx"]);
  });

  test("test_nothing_but_the_client_names_the_route", () => {
    const naming = own.filter((file) => /get_census|\}\/census\b/.test(code(file))).map(named);

    expect(naming.sort()).toEqual(["lib/api/client.ts", "lib/api/operations.ts"]);
    expect(ROUTES.get_census).toEqual({
      method: "GET",
      path: "/v1/areas/{id_or_slug}/census",
      timeoutMs: 5_000,
      neverKept: true,
    });
  });

  test("test_the_page_takes_nothing_but_the_panel_itself_from_a_file_that_runs_in_the_browser", () => {
    // Seen in a built page: the id of the part was taken from the panel's own file, which
    // runs in the browser, and a page drawn on the server was handed a function in its place.
    const page = code(path.join(SRC, "components", "AreaProfile", "AreaProfile.tsx"));
    const taken = [...page.matchAll(/import \{([^}]+)\} from "\.\.\/CensusPanel\/CensusPanel"/g)].flatMap(
      ([, names]) => (names ?? "").split(",").map((name) => name.trim()),
    );
    const panel = readFileSync(path.join(SRC, "components", "CensusPanel", "CensusPanel.tsx"), "utf8");

    expect(panel.trimStart().startsWith('"use client"')).toBe(true);
    expect(taken).toEqual(["CensusPanel"]);
    expect(readFileSync(path.join(SRC, "components", "CensusPanel", "part.ts"), "utf8").includes("use client")).toBe(false);
  });

  test("test_a_build_never_reads_the_census", () => {
    // A page is built from routes 4, 5, 6 and 11. The figures are in no page as it is built.
    const build = code(path.join(SRC, "lib", "api", "server.ts"));

    expect(/census/i.test(build)).toBe(false);
    for (const page of own.filter((file) => named(file).startsWith("app/"))) {
      expect(/census/i.test(code(page))).toBe(false);
    }
  });

  test("test_the_panel_reads_nothing_of_a_search_a_comparison_a_vibe_or_the_map", () => {
    const panel = code(path.join(SRC, "components", "CensusPanel", "CensusPanel.tsx"));
    const imports = [...panel.matchAll(/from "([^"]+)"/g)].map(([, from]) => from ?? "");

    expect(imports.sort()).toEqual([
      "../AreaProfile/AreaProfile.module.css",
      "../ErrorBlock/ErrorBlock",
      "./CensusPanel.module.css",
      "./part",
      "@/content/census",
      "@/lib/api/client",
      "@/lib/api/schema",
      "@/lib/paths",
      "next/link",
      "react",
    ]);
    for (const never of ["search", "session", "compare", "vibes", "map", "storage", "localStorage"]) {
      expect(imports.some((from) => from.includes(`/${never}`))).toBe(false);
    }
  });

  test("test_nothing_of_the_census_is_handed_to_a_search_a_comparison_or_a_share", () => {
    const reading = own
      .filter((file) => /Census(Panel|Offer|PanelRow|PanelTable|Kind)\b|\.census\b/.test(code(file)))
      .map(named);

    expect(reading.sort()).toEqual([
      "components/AreaProfile/AreaProfile.tsx",
      "components/CensusPanel/CensusPanel.tsx",
    ]);
  });
});

describe("no other answer holds a figure of the census", () => {
  const recorded = filesUnder(RECORDED)
    .filter((file) => file.endsWith(".json"))
    .map((file) => path.relative(RECORDED, file).replace(/\.json$/, ""));
  const ofTheCensus = recorded.filter((scenario) => /^census(-|$)/.test(scenario));

  test("test_the_census_is_recorded_and_its_canaries_bite", () => {
    expect(ofTheCensus.sort()).toEqual([
      "census",
      "census-not-found",
      "census-not-held",
      "census-off",
      "census-too-few",
    ]);
    const said = JSON.stringify(readRecorded("census").body).toLowerCase();
    expect(canaries().length).toBeGreaterThan(100);
    expect(canaries().filter((mark) => !said.includes(mark))).toEqual([]);
  });

  test("test_a_visit_to_every_other_page_never_meets_the_canary", () => {
    const others = recorded.filter((scenario) => !ofTheCensus.includes(scenario) && scenario !== "index");
    expect(others.length).toBeGreaterThan(150);
    expect(others.filter((scenario) => scenario.startsWith("visit/")).length).toBeGreaterThan(5);

    const marks = canaries();
    const met = others.filter((scenario) => {
      const said = readFileSync(path.join(RECORDED, `${scenario}.json`), "utf8").toLowerCase();
      return marks.some((mark) => said.includes(mark));
    });

    expect(met).toEqual([]);
  });

  test("test_what_offers_the_census_holds_no_figure_and_names_no_area", () => {
    const { census } = recordedAnswer("get_meta", "meta").body.data;
    const areas = recordedAnswer("list_areas", "areas").body.data.areas;
    const said = `${census.heading} ${census.intro}`;

    expect(census.available).toBe(true);
    expect(/%|\d{3}/.test(said.replace(/\b\d{4}\b/g, ""))).toBe(false);
    expect(areas.filter((area) => said.includes(area.name))).toEqual([]);
    expect(canaries().filter((mark) => said.toLowerCase().includes(mark))).toEqual([]);
  });

  test("test_the_profile_of_an_area_holds_nothing_of_the_census", () => {
    const profile = recordedAnswer("get_area", "area/foxholt").body.data;

    expect(Object.keys(profile).filter((field) => /census|resident/i.test(field))).toEqual([]);
    const kinds = new Set(profile.facts.map((fact) => fact.kind as string));
    for (const table of served.tables) expect(kinds.has(table.kind)).toBe(false);
  });
});
