/** @jest-environment node */
/**
 * Household income is apart from everything else the website does. Only the page of an
 * area asks for it, only when a person opens it, and nothing of it is in any other answer
 * the website reads. So no page ranks on it, compares on it or gives a reason from it.
 * These read the source and the recorded answers, so they hold whatever is written next
 * as well as what is there now.
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

const served = recordedAnswer("get_income", "income").body.data;

/** Every figure of the recorded estimate, as it is printed and with no mark of money. */
function canaries(): string[] {
  return [served.estimate, served.lower, served.upper]
    .filter((figure): figure is string => figure !== null)
    .flatMap((figure) => [figure.replace("£", ""), figure.replace(/[£,]/g, "")]);
}

describe("only the page of an area asks for household income", () => {
  test("test_one_component_calls_the_route_and_one_page_draws_it", () => {
    const calls = own.filter((file) => /\bgetIncome\b/.test(code(file))).map(named);
    const draws = own.filter((file) => /<IncomePanel\b/.test(code(file))).map(named);

    expect(calls.sort()).toEqual(["components/IncomePanel/IncomePanel.tsx", "lib/api/client.ts"]);
    expect(draws).toEqual(["components/AreaProfile/AreaProfile.tsx"]);
  });

  test("test_nothing_but_the_client_names_the_route", () => {
    const naming = own.filter((file) => /get_income|\}\/income\b/.test(code(file))).map(named);

    expect(naming.sort()).toEqual(["lib/api/client.ts", "lib/api/operations.ts"]);
    expect(ROUTES.get_income).toEqual({
      method: "GET",
      path: "/v1/areas/{id_or_slug}/income",
      timeoutMs: 5_000,
      neverKept: true,
    });
  });

  test("test_the_page_takes_nothing_but_the_panel_itself_from_a_file_that_runs_in_the_browser", () => {
    const page = code(path.join(SRC, "components", "AreaProfile", "AreaProfile.tsx"));
    const taken = [...page.matchAll(/import \{([^}]+)\} from "\.\.\/IncomePanel\/IncomePanel"/g)].flatMap(
      ([, names]) => (names ?? "").split(",").map((name) => name.trim()),
    );
    const panel = readFileSync(path.join(SRC, "components", "IncomePanel", "IncomePanel.tsx"), "utf8");

    expect(panel.trimStart().startsWith('"use client"')).toBe(true);
    expect(taken).toEqual(["IncomePanel"]);
    expect(readFileSync(path.join(SRC, "components", "IncomePanel", "part.ts"), "utf8").includes("use client")).toBe(false);
  });

  test("test_a_build_never_reads_household_income", () => {
    // A page is built from routes 4, 5, 6 and 11. The figure is in no page as it is built.
    const build = code(path.join(SRC, "lib", "api", "server.ts"));

    expect(/income/i.test(build)).toBe(false);
    for (const page of own.filter((file) => named(file).startsWith("app/"))) {
      expect(/income/i.test(code(page))).toBe(false);
    }
  });

  test("test_the_panel_reads_nothing_of_a_search_a_comparison_a_vibe_or_the_map", () => {
    const panel = code(path.join(SRC, "components", "IncomePanel", "IncomePanel.tsx"));
    const imports = [...panel.matchAll(/from "([^"]+)"/g)].map(([, from]) => from ?? "");

    expect(imports.sort()).toEqual([
      "../AreaProfile/AreaProfile.module.css",
      "../ErrorBlock/ErrorBlock",
      "./IncomePanel.module.css",
      "./part",
      "@/content/income",
      "@/lib/api/client",
      "@/lib/api/schema",
      "react",
    ]);
    for (const never of ["search", "session", "compare", "vibes", "map", "storage", "localStorage"]) {
      expect(imports.some((from) => from.includes(`/${never}`))).toBe(false);
    }
  });

  test("test_nothing_of_household_income_is_handed_to_a_search_a_comparison_or_a_share", () => {
    // No file that ranks, compares, explains or shares names a record of it, or a field of it.
    const reading = own
      .filter((file) => /Income(Panel|Offer|Shown)\b|\.income\b|getIncome|INCOME\b/.test(code(file)))
      .map(named);

    expect(reading.sort()).toEqual([
      "components/AreaProfile/AreaProfile.tsx",
      "components/IncomePanel/IncomePanel.tsx",
      "content/income.ts",
      "lib/api/client.ts",
    ]);
    for (const folder of ["lib/search/", "lib/compare/", "lib/session/", "lib/map/", "lib/area/"]) {
      for (const file of own.filter((one) => named(one).startsWith(folder))) {
        expect(/income/i.test(code(file))).toBe(false);
      }
    }
  });
});

describe("no other answer holds a figure of household income", () => {
  const recorded = filesUnder(RECORDED)
    .filter((file) => file.endsWith(".json"))
    .map((file) => path.relative(RECORDED, file).replace(/\.json$/, ""));
  const ofIncome = recorded.filter((scenario) => /^income(-|$)/.test(scenario));

  test("test_it_is_recorded_and_its_figures_bite", () => {
    expect(ofIncome.sort()).toEqual(["income", "income-none-given", "income-not-found", "income-off"]);
    const said = JSON.stringify(readRecorded("income").body);
    expect(canaries()).toHaveLength(6);
    expect(canaries().filter((mark, at) => at % 2 === 0 && !said.includes(mark))).toEqual([]);
  });

  test("test_no_ranking_no_comparison_and_no_reasons_hold_a_figure_of_it_or_a_word_for_it", () => {
    // What routes 2, 3 and 7 answered, in every recording there is of them.
    const others = recorded.filter((scenario) => !ofIncome.includes(scenario) && scenario !== "index");
    expect(others.length).toBeGreaterThan(150);
    const ranks = others.filter((scenario) => /(^|\/)(rank|compare|explanations|shared?|share)(-|$)/.test(scenario));
    expect(ranks.length).toBeGreaterThan(30);

    const marks = canaries();
    const met = others.filter((scenario) => {
      const said = readFileSync(path.join(RECORDED, `${scenario}.json`), "utf8");
      return marks.some((mark) => new RegExp(`(?<![\\d,.])${mark}(?![\\d,])`).test(said));
    });
    expect(met).toEqual([]);

    const named = ranks.filter((scenario) =>
      /income|earn|salar/i.test(readFileSync(path.join(RECORDED, `${scenario}.json`), "utf8")),
    );
    expect(named).toEqual([]);
  });

  test("test_what_offers_it_holds_no_figure_and_names_no_area", () => {
    const { income } = recordedAnswer("get_meta", "meta").body.data;
    const areas = recordedAnswer("list_areas", "areas").body.data.areas;
    const said = `${income.heading} ${income.intro}`;

    expect(income.available).toBe(true);
    expect(/[£%\d]/.test(said)).toBe(false);
    expect(areas.filter((area) => said.includes(area.name))).toEqual([]);
  });

  test("test_the_profile_of_an_area_holds_nothing_of_it", () => {
    const profile = recordedAnswer("get_area", "area/foxholt").body.data;

    expect(Object.keys(profile).filter((field) => /income|earn/i.test(field))).toEqual([]);
    expect(profile.facts.filter((fact) => /income/i.test(JSON.stringify(fact)))).toEqual([]);
    expect(profile.features.filter((row) => /income/i.test(row.feature_id))).toEqual([]);
  });
});
