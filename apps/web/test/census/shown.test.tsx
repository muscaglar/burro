/**
 * How the census figures are shown, so that they are read as a description and
 * not a verdict. docs/design/web.md, section 2, gives the rules. Each is held
 * here: in what is drawn, in the style sheet, and in the words.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { render, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CensusPanel } from "@/components/CensusPanel/CensusPanel";
import { CENSUS_PART } from "@/components/CensusPanel/part";
import { CENSUS } from "@/content/census";
import { recordedAnswer } from "@/lib/api/recorded";

import { standInApi } from "../support/api";
import { rulesOf } from "../support/css";

const SRC = path.resolve(__dirname, "..", "..", "src");
const SHEET = path.join(SRC, "components", "CensusPanel", "CensusPanel.module.css");
const offer = recordedAnswer("get_meta", "meta").body.data.census;
const served = recordedAnswer("get_census", "census").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const SLUG = "foxholt";

const panel = () => document.getElementById(CENSUS_PART) as HTMLDetailsElement;

/** Opens the panel, and then every table in it. */
async function opened() {
  const api = standInApi().on("get_census", "census");
  const view = render(<CensusPanel offer={offer} area={{ slug: SLUG }} client={api.client} />);
  const user = userEvent.setup({ delay: null });
  await user.click(panel().querySelector("summary") as HTMLElement);
  await waitFor(() => expect(panel().querySelector("details[data-table]")).not.toBeNull());
  for (const table of panel().querySelectorAll("details[data-table] > summary")) await user.click(table);
  return view;
}

/** Words Burro would be choosing of a figure. The API's own words are held to the same in core. */
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

const wordsOf = (text: string) => new Set(text.toLowerCase().match(/[a-z]+/g) ?? []);

describe("no colour says good or bad", () => {
  const rules = rulesOf(readFileSync(SHEET, "utf8"));
  const colours = rules.flatMap((rule) =>
    [...rule.sets].filter(([, value]) => /var\(--|#[0-9a-f]{3,8}\b|rgb|hsl/i.test(value)).map(([, value]) => value),
  );

  test("test_every_colour_is_one_the_text_of_the_page_is_drawn_in", () => {
    const tokens = new Set(colours.flatMap((value) => value.match(/--[a-z0-9-]+/g) ?? []));
    const ofColour = [...tokens].filter((token) => !/^--(space|size|radius|target|motion|leading)/.test(token));

    expect(ofColour.sort()).toEqual(["--border", "--muted", "--surface", "--text"]);
    // None that says good, bad, better or worse, and none of the map's five shades.
    for (const never of ["--good", "--error", "--tradeoff", "--accent", "--notice", "--map"]) {
      expect(ofColour.some((token) => token.startsWith(never))).toBe(false);
    }
    expect(colours.some((value) => /#[0-9a-f]{3,8}\b|rgb|hsl/i.test(value))).toBe(false);
  });

  test("test_no_rule_draws_one_row_or_one_table_unlike_another", () => {
    // A step in is the only mark of a row that stands under a group: the depth sets how far in, and nothing else.
    const keyed = rules.filter((rule) => /\[data-|:nth-|:first-|:last-|:has\(/.test(rule.selector));
    const byDepth = keyed.filter((rule) => /\[data-depth="[12]"\]$/.test(rule.selector));

    // The headings of the columns say how wide each column is, and set nothing else.
    const widths = keyed.filter((rule) => !byDepth.includes(rule));
    expect(widths.map((rule) => rule.selector)).toEqual([
      ".figures thead th:nth-child(2)",
      ".figures thead th:nth-child(n + 3)",
    ]);
    for (const rule of widths) expect([...rule.sets.keys()]).toEqual(["width"]);
    for (const rule of byDepth) expect([...rule.sets.keys()]).toEqual(["padding-inline-start"]);
    for (const drawn of [".bar", ".mark", ".line", ".picture"]) {
      expect(rules.filter((rule) => rule.selector === drawn)).toHaveLength(1);
    }
  });

  test("test_every_bar_is_drawn_alike_whatever_it_holds", async () => {
    await opened();
    const pictures = [...panel().querySelectorAll("svg")];
    const rows = served.tables.flatMap((table) => table.rows);

    // Where neither share is a figure there is nothing to draw, and nothing is drawn.
    const drawn = rows.filter((row) => row.percent !== null || row.city_percent !== null);
    expect(drawn.length).toBeLessThan(rows.length);
    expect(pictures).toHaveLength(drawn.length);
    expect(new Set(pictures.map((picture) => picture.getAttribute("class"))).size).toBe(1);
    const bars = [...panel().querySelectorAll("svg rect")];
    expect(new Set(bars.map((bar) => `${bar.getAttribute("class")} ${bar.getAttribute("height")}`)).size).toBe(1);
    // The width of a bar is its share, and nothing else of it follows the figure.
    expect(bars.map((bar) => bar.getAttribute("width"))).toEqual(
      rows.filter((row) => row.percent !== null).map((row) => String(row.percent)),
    );
    expect(panel().querySelectorAll("[style], [data-kind], [data-percent], [data-share]")).toHaveLength(0);
  });

  test("test_the_picture_says_nothing_the_table_does_not", async () => {
    await opened();

    for (const picture of panel().querySelectorAll("svg")) {
      expect(picture).toHaveAttribute("aria-hidden", "true");
      expect(picture.closest("td")?.textContent).toMatch(/%|fewer than 1 in 100/);
      // It stands after the words, so that the words are read first where both are read.
      expect(picture.previousElementSibling?.textContent).toMatch(/%|fewer than 1 in 100/);
      expect(picture.querySelectorAll("title, desc, text")).toHaveLength(0);
    }
    const drawn = served.tables.find((table) => table.rows.length > 0);
    expect(panel()).toHaveTextContent(CENSUS.picture(drawn?.columns.share ?? "", served.city));
  });
});

describe("a figure stands beside the city's figure and nothing else", () => {
  test("test_every_table_has_four_columns_and_no_more", async () => {
    await opened();

    for (const table of within(panel()).getAllByRole("table")) {
      expect(within(table).getAllByRole("columnheader")).toHaveLength(4);
      for (const row of within(table).getAllByRole("row").slice(1)) {
        expect(within(row).getAllByRole("cell")).toHaveLength(3);
      }
    }
  });

  test("test_no_other_area_is_named_and_none_is_linked_to", async () => {
    await opened();
    const said = panel().textContent ?? "";
    const others = areas.filter((area) => area.slug !== SLUG);

    expect(others.filter((area) => said.includes(area.name)).map((area) => area.name)).toEqual([]);
    const links = [...panel().querySelectorAll("a")].map((link) => link.getAttribute("href") ?? "");
    expect(links.length).toBeGreaterThan(0);
    // Every link leads to where the figures came from. None leads to an area, a search or a comparison.
    expect(links.filter((href) => !href.startsWith("/sources#"))).toEqual([]);
  });

  test("test_nothing_of_a_search_stands_in_it", async () => {
    await opened();
    const said = (panel().textContent ?? "").toLowerCase();

    for (const never of ["rank", "fit", "journey", "budget", "band ", "score", "minutes", "£"]) {
      // The one place a word of ranking stands is where the API says that Burro never does it.
      const left = said.replaceAll(served.notes.join(" ").toLowerCase(), "").replaceAll(offer.intro.toLowerCase(), "");
      const without = served.tables.reduce(
        (text, table) => text.replaceAll((table.shown_only ?? "").toLowerCase() || "\u0000", ""),
        left,
      );
      expect(without.includes(never)).toBe(false);
    }
  });
});

describe("nothing puts one row before another", () => {
  test("test_there_is_nothing_to_sort_filter_or_switch_by", async () => {
    await opened();

    // What opens a table is the browser's own, and is the one thing in it to press but a link to a source.
    expect(panel().querySelectorAll("button, select, input, textarea, [role='button'], [aria-sort]")).toHaveLength(0);
    expect(panel().querySelectorAll("table summary, table a, table button")).toHaveLength(0);
    expect(panel().querySelectorAll("th[aria-sort], th button, th a")).toHaveLength(0);
  });

  test("test_the_rows_are_not_in_the_order_of_their_figures", async () => {
    await opened();

    for (const table of served.tables) {
      const shares = table.rows.map((row) => row.percent ?? 0);
      expect(shares).not.toEqual([...shares].sort((a, b) => b - a));
      expect(shares).not.toEqual([...shares].sort((a, b) => a - b));
    }
    const drawn = [...panel().querySelectorAll("th[scope='row']")].map(
      (row) => row.querySelector("[aria-hidden='true']")?.textContent ?? row.textContent,
    );
    expect(drawn).toEqual(served.tables.flatMap((table) => table.rows.map((row) => row.label)));
  });
});

describe("no word is one Burro would be choosing", () => {
  const copy = Object.values(CENSUS).map((words) =>
    typeof words === "function" ? words("the area", "the city") : words,
  );

  test("test_the_site_copy_says_nothing_of_what_a_figure_means", () => {
    for (const words of copy) {
      expect([...wordsOf(words)].filter((word) => NEVER_SAID.includes(word))).toEqual([]);
    }
  });

  test("test_the_site_copy_holds_no_figure_and_names_no_group", () => {
    for (const words of copy) expect(/\d/.test(words)).toBe(false);
    const labels = served.tables.flatMap((table) => table.rows.map((row) => row.label.toLowerCase()));
    for (const words of copy) {
      expect(labels.filter((label) => words.toLowerCase().includes(label))).toEqual([]);
    }
  });

  test("test_what_the_api_sent_is_drawn_as_it_came_and_holds_no_such_word", async () => {
    await opened();
    // Every string but a publisher's own heading. The made-up count's headings are its own.
    const said = [
      offer.heading,
      offer.intro,
      served.date_line,
      ...served.notes,
      served.source_line,
      served.derivation_line,
      served.licence_line,
      ...served.tables.flatMap((table) => [table.shown_only ?? "", table.note ?? ""]),
    ];

    for (const words of said) {
      expect([...wordsOf(words)].filter((word) => NEVER_SAID.includes(word))).toEqual([]);
      if (words !== "") expect(panel().textContent?.includes(words)).toBe(true);
    }
  });
});

describe("on a narrow screen", () => {
  const rules = rulesOf(readFileSync(SHEET, "utf8"));
  const narrow = rules.filter((rule) => /max-width:\s*39\.99rem/.test(rule.under ?? ""));

  test("test_each_row_is_stacked_and_each_figure_says_whose_it_is", () => {
    const blocks = narrow.filter((rule) => rule.sets.get("display") === "block").map((rule) => rule.selector);

    expect(blocks).toEqual(
      expect.arrayContaining([".figures", ".figures caption", ".figures tbody", ".figures th", ".figures td", ".cellName"]),
    );
    expect(rules.find((rule) => rule.under === null && rule.selector === ".cellName")?.sets.get("display")).toBe("none");
    // The headings of the columns are kept for a screen reader, and not drawn.
    expect(narrow.find((rule) => rule.selector === ".head")?.sets.get("clip-path")).toBe("inset(50%)");
  });

  test("test_a_figure_in_words_may_wrap_inside_its_column", () => {
    // Seen in a browser: "fewer than 1 in 100" ran out of the last column and past the table.
    const said = rules.find((rule) => rule.under === null && rule.selector === ".said");

    expect(said?.sets.get("flex")).toBe("0 1 auto");
    expect(rules.filter((rule) => rule.sets.get("white-space") === "nowrap" && rule.selector !== ".head")).toEqual([]);
  });

  test("test_the_table_is_no_wider_than_the_page_and_is_put_in_no_box_that_scrolls", () => {
    expect(rules.filter((rule) => /overflow(-x)?$/.test([...rule.sets.keys()].join(" ")) && rule.selector !== ".picture")).toEqual([]);
    expect(rules.find((rule) => rule.selector === ".figures th")?.sets.get("overflow-wrap")).toBe("anywhere");
    expect(narrow.find((rule) => rule.selector === ".row")?.sets.get("grid-template-columns")).toBe(
      "repeat(3, minmax(0, 1fr))",
    );
  });

  test("test_every_part_of_the_table_says_its_role_again", async () => {
    await opened();
    const table = panel().querySelector("table") as HTMLElement;

    expect(table).toHaveAttribute("role", "table");
    expect([...table.querySelectorAll("thead, tbody")].every((group) => group.getAttribute("role") === "rowgroup")).toBe(true);
    expect([...table.querySelectorAll("tr")].every((row) => row.getAttribute("role") === "row")).toBe(true);
    expect([...table.querySelectorAll("td")].every((cell) => cell.getAttribute("role") === "cell")).toBe(true);
    expect([...table.querySelectorAll("tbody th")].every((cell) => cell.getAttribute("role") === "rowheader")).toBe(true);
  });
});
