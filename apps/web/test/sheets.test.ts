/** @jest-environment node */
/**
 * The style sheet of a part and the part that reads it, held to each other: every class a
 * part asks of its sheet is in that sheet, and nothing stands in a sheet that no part wears
 * and nothing reads.
 *
 * A style sheet of a part gives each of its classes a name of its own, and a part asks for
 * a class by the name it has in the sheet. A class the sheet does not have has no such
 * name: the part is handed nothing, and draws an element with no class. No compiler says
 * so. Nor does a test that draws the part, where every class bears the name it was asked
 * by, whether or not its sheet has it.
 *
 * Seen in a browser: the label of every trade-off bore the class "undefined", and ten
 * other classes were asked of sheets that had lost them as the look was built again.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { rulesOf } from "./support/css";

const SRC = path.resolve(__dirname, "..", "src");

/** Every file under a folder, by its path. */
function filesUnder(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(folder, entry.name);
    return entry.isDirectory() ? filesUnder(file) : [file];
  });
}

/** The classes of a sheet: each class a selector of it names. */
function classesOf(sheet: string): ReadonlySet<string> {
  const names = new Set<string>();
  for (const rule of rulesOf(readFileSync(sheet, "utf8"))) {
    // What is wrapped as a class of the whole website is none of the sheet's own.
    const own = rule.selector.replace(/:global\([^()]*\)/g, " ");
    for (const [, name] of own.matchAll(/\.(-?[_a-zA-Z][\w-]*)/g)) if (name !== undefined) names.add(name);
  }
  return names;
}

/** Every name a sheet gives a part that asks: of each of its classes, and of each run of frames. */
function namesOf(sheet: string): ReadonlySet<string> {
  const frames = [...readFileSync(sheet, "utf8").matchAll(/@keyframes\s+([\w-]+)/g)].flatMap(([, name]) => name ?? []);
  return new Set([...classesOf(sheet), ...frames]);
}

describe("a name that is one long word", () => {
  const at = (sheet: string, selector: string) =>
    new Map(
      rulesOf(readFileSync(path.join(SRC, "components", sheet), "utf8"))
        .filter((rule) => rule.selector === selector && rule.under === null)
        .flatMap((rule) => [...rule.sets]),
    );

  test("test_it_is_broken_in_the_bar_of_areas_and_pushes_nothing_of_the_page_of_an_area_past_the_window", () => {
    // Seen in a browser 390 px wide, with a name of sixty letters in one word: the bar of
    // areas to compare was 568 px wide, and the cross of its chip lay over the name. The
    // page of an area was 564 px wide, by the name of its nearest station and by the areas
    // most like it. A word that may be broken only where it runs past its line is as wide
    // as it is to whatever asks how narrow it can be, and a row or a column is as wide as
    // what it holds unless it is told otherwise.
    expect(at("CompareTray/CompareTray.module.css", ".name").get("overflow-wrap")).toBe("anywhere");
    for (const part of [".station", ".alike", ".alike > li"]) {
      expect([part, at("AreaProfile/AreaProfile.module.css", part).get("grid-template-columns")]).toEqual([part, "minmax(0, 1fr)"]);
    }
    // A link that is laid out as a box is as wide as a word it may not break.
    expect(at("AreaProfile/AreaProfile.module.css", ".alike a").get("overflow-wrap")).toBe("anywhere");
    // A fact in its columns: the row is one column, and a column is no wider than the row.
    expect(at("FactRow/FactRow.module.css", ".row").get("grid-template-columns")).toBe("minmax(0, 1fr)");
    expect(at("FactRow/FactRow.module.css", ".columns > div").get("min-width")).toBe("0");
    expect(at("FactRow/FactRow.module.css", ".columns dd").get("overflow-wrap")).toBe("anywhere");
  });
});

describe("the classes a part asks of its style sheet", () => {
  const parts = filesUnder(SRC).filter((file) => /\.tsx?$/.test(file) && !/\.test\.tsx?$/.test(file));
  /** Each sheet a part reads, with the name the part reads it by and every class it asks of it by name. */
  const asked = parts.flatMap((file) => {
    const source = readFileSync(file, "utf8");
    return [...source.matchAll(/import\s+(\w+)\s+from\s+"(\.{1,2}\/[^"]+\.module\.css)"/g)].map(([, as, from]) => ({
      part: path.relative(SRC, file),
      sheet: path.resolve(path.dirname(file), from ?? ""),
      /** True where the part asks for a class by a name it was handed, which no reading of the part can tell. */
      byAName: new RegExp(`(?<![\\w./"-])${as}\\[`).test(source),
      // Where the sheet is read by a name that is in its address too, the address asks for nothing.
      classes: [...new Set([...source.matchAll(new RegExp(`(?<![\\w./"-])${as}\\.([A-Za-z_]\\w*)`, "g"))].map(([, name]) => name ?? ""))],
    }));
  });

  test("test_every_class_a_part_asks_of_its_style_sheet_is_in_that_sheet", () => {
    const missing = asked.flatMap(({ part, sheet, classes }) => {
      const has = namesOf(sheet);
      return classes.filter((name) => !has.has(name)).map((name) => `${part} asks ${path.relative(SRC, sheet)} for "${name}"`);
    });

    expect(missing).toEqual([]);
  });

  test("test_every_class_of_a_style_sheet_is_worn_by_a_part_that_reads_it", () => {
    // Seen in the sheet of the search page: a rule drew a notice that a part of a search was
    // not read, which no part of the page had drawn since the page was built again.
    const sheets = [...new Set(asked.map((one) => one.sheet))];
    const loose = sheets.flatMap((sheet) => {
      const readers = asked.filter((one) => one.sheet === sheet);
      // A part that asks for a class by a name it was handed may ask for any: its sheet is left alone.
      if (readers.some((one) => one.byAName)) return [];
      const worn = new Set(readers.flatMap((one) => one.classes));
      return [...classesOf(sheet)].filter((name) => !worn.has(name)).map((name) => `${path.relative(SRC, sheet)} has "${name}"`);
    });

    expect(loose).toEqual([]);
  });

  test("test_every_property_a_sheet_of_a_part_sets_for_itself_is_read_by_a_sheet_or_a_part", () => {
    // Seen in the sheet of the space requirements: the light of a lever was set on a tick,
    // and read by nothing since the lever became a button. The tokens of the website are
    // the look's to name, and their own test holds them.
    const written = filesUnder(SRC).filter((file) => !/\.test\.tsx?$/.test(file) && /\.(css|tsx?)$/.test(file));
    // Read by a sheet, as a value, or by a part, which names it to ask the browser what it holds.
    const read = new Set(
      written.flatMap((file) =>
        [...readFileSync(file, "utf8").matchAll(/var\(\s*(--[\w-]+)|["'`](--[\w-]+)["'`](?!\s*:)/g)].map(([, inASheet, byAPart]) => inASheet ?? byAPart),
      ),
    );
    const set = [...new Set(asked.map((one) => one.sheet))].flatMap((sheet) =>
      rulesOf(readFileSync(sheet, "utf8")).flatMap((rule) =>
        [...rule.sets.keys()].filter((name) => name.startsWith("--")).map((name) => ({ sheet: path.relative(SRC, sheet), name })),
      ),
    );

    expect(set.length).toBeGreaterThan(100);
    expect([...new Set(set.filter(({ name }) => !read.has(name)).map(({ sheet, name }) => `${sheet} sets ${name}`))]).toEqual([]);
  });

  test("test_the_parts_of_the_website_and_their_sheets_are_read", () => {
    // A rule that reads nothing holds nothing.
    expect(asked.length).toBeGreaterThan(70);
    expect(asked.flatMap((one) => one.classes).length).toBeGreaterThan(800);
    expect(asked.find((one) => one.part === "components/ResultList/ResultCard.tsx")?.classes).toContain("tradeOffTitle");
  });
});
