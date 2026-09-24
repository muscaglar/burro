import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { COMPARE_STATUS, COMPARE_TABLE, statusWords } from "@/content/compare";
import { COMBINE } from "@/content/labels";
import { recordedAnswer } from "@/lib/api/recorded";
import type { CompareData, CompareRow, ComparedArea, Fact } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { CompareAreas, CompareTable } from "./CompareTable";

/** A search with one journey. */
const three: CompareData = recordedAnswer("compare", "compare-three").body.data;
/** A search with two: one area has no time for one of them, and one area is listed apart. */
const two: CompareData = recordedAnswer("compare", "compare-two-journeys").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;

const [WORKS, CAMPUS] = two.rows.flatMap((row) => (row.place === null ? [] : [row.place.name]));
if (WORKS === undefined || CAMPUS === undefined) throw new Error("the recorded comparison holds one journey");

const counts = () => screen.getByRole("table", { name: COMPARE_TABLE.caption });
const rowsOf = () => within(counts()).getAllByRole("row").slice(1);
const journeys = () => rowsOf().filter((row) => within(row).getByRole("rowheader").textContent?.startsWith("Journey"));
const headOf = (row: HTMLElement | undefined) => within(row as HTMLElement).getByRole("rowheader");
const cellOf = (row: HTMLElement | undefined, name: string) =>
  within(row as HTMLElement).getAllByRole("cell")[two.areas.findIndex((area) => area.name === name)] as HTMLElement;

describe("the journeys of a comparison", () => {
  test("test_with_two_journeys_there_is_one_row_for_each_and_the_same_destination_across_a_row", () => {
    render(<CompareTable data={two} combine="slowest" />);

    const rows = journeys();

    expect(rows).toHaveLength(2);
    expect(headOf(rows[0])).toHaveTextContent(COMPARE_TABLE.journeys.to(WORKS));
    expect(headOf(rows[1])).toHaveTextContent(COMPARE_TABLE.journeys.to(CAMPUS));
    // No cell of a row names another place than the row's.
    for (const [row, place, not] of [
      [rows[0], WORKS, CAMPUS],
      [rows[1], CAMPUS, WORKS],
    ] as const) {
      const cells = within(row as HTMLElement).getAllByRole("cell");
      expect(cells).toHaveLength(two.areas.length);
      expect(cells.filter((cell) => cell.textContent?.includes(not))).toEqual([]);
      // The row says where the journey is to, once, and its cells do not say it again.
      expect(headOf(row).textContent?.includes(place)).toBe(true);
      expect(cells.filter((cell) => cell.textContent?.includes(place))).toEqual([]);
      expect(cells.some((cell) => /Typical minutes\d+/.test(cell.textContent ?? ""))).toBe(true);
    }
  });

  test("test_a_journey_with_no_time_in_the_data_is_shown_as_having_none_with_its_source", () => {
    render(<CompareTable data={two} combine="slowest" />);
    const [toTheWorks, toTheCampus] = journeys();

    const none = cellOf(toTheCampus, "Gorsebeck");

    // The area is ranked, and the API says it has no time for this journey.
    expect(two.areas.find((area) => area.name === "Gorsebeck")?.status).toBe("ranked");
    expect(none).toHaveTextContent(COMPARE_TABLE.journeys.missing);
    expect(within(none).getByRole("button", { name: /^Source for / })).toBeInTheDocument();
    expect(/\d/.test(none.textContent?.replace(COMPARE_TABLE.journeys.missing, "") ?? "")).toBe(false);
    // Its journey to the other place is over the limit, and says by how much.
    expect(cellOf(toTheWorks, "Gorsebeck")).toHaveTextContent(/Over your limit by, in minutes\d+/);
  });

  test("test_an_area_that_is_listed_apart_is_timed_in_every_row_and_adds_nothing", () => {
    render(<CompareTable data={two} combine="slowest" />);
    const apart = two.areas.find((area) => area.status === "character_unknown");

    for (const row of journeys()) {
      const cell = cellOf(row, apart?.name ?? "");
      expect(/Typical minutes\d+/.test(cell.textContent ?? "")).toBe(true);
      // It was not scored, so its journeys add nothing to a fit it does not have.
      expect(/Adds \d+ of 100/.test(cell.textContent ?? "")).toBe(false);
      expect(cell.textContent?.includes(COMPARE_TABLE.notScored)).toBe(false);
    }
  });

  test("test_what_the_journeys_add_stands_once_for_each_area_beside_the_journey_that_decided_it", () => {
    render(<CompareTable data={two} combine="slowest" />);

    for (const area of two.areas) {
      const said = journeys().filter((row) => /Adds \d+ of 100/.test(cellOf(row, area.name).textContent ?? ""));
      expect(said).toHaveLength(area.status === "ranked" ? 1 : 0);
    }
  });

  test.each(["slowest", "mean"] as const)(
    "test_with_two_journeys_the_table_says_once_which_of_them_counts: %s",
    (combine) => {
      render(<CompareTable data={two} combine={combine} />);

      expect(counts().textContent?.split(COMBINE[combine])).toHaveLength(2);
      expect(headOf(journeys()[0])).toHaveTextContent(COMBINE[combine]);
      // What the journeys count for is the weight of all of them, and is said once.
      expect(journeys().map((row) => /Weight \d+/.test(row.textContent ?? ""))).toEqual([true, false]);
    },
  );

  test("test_how_much_a_thing_counts_is_said_as_a_weight_and_never_as_a_share", () => {
    // Seen in a browser: "Counts for 100 of 100" stood over "Counts for 10 of 100" and five
    // things at 5 each. They read as shares of one hundred, and came to 135.
    const { container } = render(<CompareTable data={two} combine="slowest" />);
    const said = container.textContent ?? "";

    expect(/\d+ of 100(?! to the fit)/.test(said.replace(COMPARE_TABLE.weights, ""))).toBe(false);
    expect(COMPARE_TABLE.countsFor(100)).toBe("Weight 100");
    // What a weight is, is said once, over the table.
    expect(said.split(COMPARE_TABLE.weights)).toHaveLength(2);
    expect(said.indexOf(COMPARE_TABLE.weights)).toBeLessThan(said.indexOf(COMPARE_TABLE.countsFor(100)));
    expect(COMPARE_TABLE.weights).toContain("do not add up");
  });

  test("test_where_every_journey_counts_the_table_says_why_no_journey_says_what_it_adds", () => {
    // With the average, the API gives what the journeys add for none of them.
    const averaged: CompareData = {
      ...two,
      rows: two.rows.map((row) =>
        row.place === null ? row : { ...row, cells: row.cells.map((cell) => ({ ...cell, contribution: null })) },
      ),
    };
    const { unmount } = render(<CompareTable data={averaged} combine="mean" />);

    expect(headOf(journeys()[0])).toHaveTextContent(COMPARE_TABLE.journeys.together);
    expect(counts().textContent?.split(COMPARE_TABLE.journeys.together)).toHaveLength(2);
    expect(journeys().some((row) => /Adds \d+ of 100/.test(row.textContent ?? ""))).toBe(false);
    unmount();
    // Where one journey decides it, that journey says what the journeys add.
    render(<CompareTable data={two} combine="slowest" />);
    expect(counts().textContent?.includes(COMPARE_TABLE.journeys.together)).toBe(false);
  });

  test("test_with_one_journey_the_row_names_its_destination_and_says_nothing_of_which_counts", () => {
    render(<CompareTable data={three} combine="slowest" />);

    expect(journeys()).toHaveLength(1);
    expect(headOf(journeys()[0])).toHaveTextContent(COMPARE_TABLE.journeys.to(WORKS));
    expect(counts().textContent?.includes(COMBINE.slowest)).toBe(false);
    expect(counts().textContent?.includes(COMPARE_TABLE.journeys.together)).toBe(false);
  });

  test("test_every_row_the_api_sent_is_drawn_and_in_its_order", () => {
    render(<CompareTable data={two} combine="slowest" />);

    expect(rowsOf()).toHaveLength(two.rows.length);
    expect(rowsOf().map((row) => headOf(row).querySelector("span")?.textContent)).toEqual(
      two.rows.map((row) => row.label),
    );
  });

  test("test_two_rows_the_api_gave_one_name_are_both_drawn_and_nothing_is_written_to_the_console", () => {
    const complaints = jest.spyOn(console, "error").mockImplementation(() => undefined);
    const twice: CompareData = { ...three, rows: [...three.rows, ...three.rows] };

    render(<CompareTable data={twice} combine="slowest" />);

    expect(rowsOf()).toHaveLength(twice.rows.length);
    expect(complaints).not.toHaveBeenCalled();
  });

  test.each([
    ["one journey", three],
    ["two journeys, one with no time", two],
  ])("test_the_journeys_have_no_accessibility_fault: %s", async (_, data) => {
    const { container } = render(<CompareTable data={data} combine="slowest" />);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a vibe that counts in the search", () => {
  const { tags } = recordedAnswer("get_meta", "meta").body.data;
  const row = (label: string) =>
    rowsOf().find((one) => within(one).getByRole("rowheader").querySelector("span")?.textContent === label) as HTMLElement;

  test("test_it_is_drawn_as_a_mark_on_its_line_with_where_the_area_sits_in_words_and_not_as_columns", () => {
    render(<CompareTable data={three} combine="slowest" tags={tags} />);
    const leafy = three.rows.find((one) => one.component === "tag:leafy") as CompareRow;

    const cells = within(row("Leafy")).getAllByRole("cell");

    leafy.cells.forEach((cell, at) => {
      const fact = three.facts.find((one) => one.fact_id === cell.fact_id);
      if (fact === undefined || fact.slots.band === undefined) return;
      const band = Number(fact.slots.band);
      expect(cells[at]?.textContent?.includes(`band ${band} of 5`)).toBe(true);
      expect([...(cells[at]?.querySelectorAll("[data-on]") ?? [])].map((one) => one.getAttribute("data-on") === "true")).toEqual(
        [1, 2, 3, 4, 5].map((one) => one === band),
      );
      // What it adds to the fit, where the area is ranked, and its source stay where they were.
      expect(/Adds \d+ of 100 to the fit/.test(cells[at]?.textContent ?? "")).toBe(cell.contribution !== null);
      expect(within(cells[at] as HTMLElement).getByRole("button", { name: /^Source for / })).toBeInTheDocument();
      // No column of the fact is drawn: how many areas were compared is behind its source.
      expect(cells[at]?.querySelectorAll("dt")).toHaveLength(0);
    });
    expect(leafy.cells.some((cell) => cell.fact_id !== null)).toBe(true);
  });

  test("test_an_area_with_no_figure_for_the_vibe_says_so_and_is_never_put_in_the_middle", () => {
    // The fact of the cell says that there is no figure, as it does for anything that counts.
    const placed = three.facts.find((fact) => fact.fact_id === "syn-n0006/tag/leafy") as Fact;
    const none: CompareData = {
      ...three,
      facts: three.facts.map((fact) =>
        fact === placed ? { ...fact, kind: "missing", template: "missing", slots: { label: "Leafy", name: "Farrowmere" } } : fact,
      ),
    };
    render(<CompareTable data={none} combine="slowest" tags={tags} />);
    const leafy = three.rows.find((one) => one.component === "tag:leafy") as CompareRow;
    const at = leafy.cells.findIndex((cell) => cell.fact_id === placed.fact_id);

    const cell = within(row("Leafy")).getAllByRole("cell")[at] as HTMLElement;

    expect(at).toBeGreaterThanOrEqual(0);
    expect(cell).toHaveTextContent(COMPARE_TABLE.noFigure);
    expect(cell.querySelectorAll("[data-on]")).toHaveLength(0);
    expect(/band \d/.test(cell.textContent ?? "")).toBe(false);
  });

  test("test_a_thing_the_area_has_no_figure_for_says_so_as_the_api_recorded_it", () => {
    render(<CompareTable data={three} combine="slowest" tags={tags} />);
    const air = three.rows.find((one) => one.component === "feature:air_no2") as CompareRow;
    const at = air.cells.findIndex((cell) => three.facts.find((one) => one.fact_id === cell.fact_id)?.kind === "missing");

    const cell = within(row(air.label)).getAllByRole("cell")[at] as HTMLElement;

    expect(at).toBeGreaterThanOrEqual(0);
    expect(cell).toHaveTextContent(COMPARE_TABLE.noFigure);
    expect(/\d/.test(cell.textContent?.replace(three.areas[at]?.name ?? "", "") ?? "")).toBe(false);
  });

  test("test_a_fact_that_says_the_vibe_cannot_place_the_area_is_said_in_two_words", () => {
    const placed = three.facts.find((fact) => fact.fact_id === "syn-n0006/tag/leafy") as Fact;
    const { band: _band, spread_low: _low, spread_high: _high, ...slots } = placed.slots;
    void [_band, _low, _high];
    const unknown: CompareData = {
      ...three,
      facts: three.facts.map((fact) =>
        fact === placed ? { ...fact, template: "vibe_unknown", slots: { ...slots, known: "1", parts: "3" } } : fact,
      ),
    };
    render(<CompareTable data={unknown} combine="slowest" tags={tags} />);
    const leafy = three.rows.find((one) => one.component === "tag:leafy") as CompareRow;
    const at = leafy.cells.findIndex((one) => one.fact_id === placed.fact_id);

    const cell = within(row("Leafy")).getAllByRole("cell")[at] as HTMLElement;

    expect(at).toBeGreaterThanOrEqual(0);
    expect(cell).toHaveTextContent(COMPARE_TABLE.character.notPlaced);
    expect(cell.querySelectorAll("[data-on]")).toHaveLength(0);
    expect(/band \d/.test(cell.textContent ?? "")).toBe(false);
  });

  test("test_a_vibe_the_release_does_not_name_is_laid_out_as_its_fact_gives_it", () => {
    render(<CompareTable data={three} combine="slowest" tags={[]} />);

    // With no name for its ends, nothing is said of where it sits in words of the website's own.
    expect(within(row("Leafy")).getAllByRole("cell").some((cell) => cell.querySelectorAll("dt").length > 0)).toBe(true);
  });
});

describe("the areas compared, and what a fit rests on", () => {
  /** Two areas on the usual settings: the fit of one rests on part of what counts. */
  const defaults: CompareData = recordedAnswer("compare", "compare-two-defaults").body.data;
  const chosenOf = (data: CompareData) =>
    data.areas.map((area) => {
      const found = areas.find((one) => one.area_id === area.area_id);
      if (!found) throw new Error("the release holds no such area");
      return { area_id: found.area_id, slug: found.slug, name: found.name };
    });
  const chosen = chosenOf(three);
  const list = () => screen.getByRole("list", { name: COMPARE_TABLE.areas });
  const item = (name: string) =>
    within(list())
      .getAllByRole("listitem")
      .find((one) => one.textContent?.startsWith(name)) as HTMLElement;

  test("test_a_fit_that_rests_on_part_of_the_data_says_so_where_the_fit_is", () => {
    const standings = new Map(defaults.areas.map((area, at) => [area.area_id, { rank: at + 1, fit: 86 - at }]));
    render(<CompareAreas chosen={chosenOf(defaults)} compared={defaults.areas} standings={standings} />);
    const part = defaults.areas.find((area) => area.status === "ranked" && area.present < area.counted) as ComparedArea;
    const whole = defaults.areas.find((area) => area.status === "ranked" && area.present === area.counted) as ComparedArea;

    expect(item(part.name)).toHaveTextContent(COMPARE_TABLE.basedOn(part.present, part.counted));
    expect(item(part.name)).toHaveTextContent(COMPARE_TABLE.restsOnPart);
    // It is marked as a trade-off is, and the mark is not the only sign of it.
    expect(item(part.name).querySelector("[data-part='true']")).not.toBeNull();
    expect(item(whole.name).textContent?.includes(COMPARE_TABLE.restsOnPart)).toBe(false);
    expect(item(whole.name).querySelector("[data-part='true']")).toBeNull();
  });

  test("test_with_no_fit_to_show_it_still_says_how_much_there_is_a_figure_for_and_no_more", () => {
    render(<CompareAreas chosen={chosenOf(defaults)} compared={defaults.areas} />);
    const part = defaults.areas.find((area) => area.status === "ranked" && area.present < area.counted) as ComparedArea;

    expect(item(part.name)).toHaveTextContent(COMPARE_TABLE.basedOn(part.present, part.counted));
    expect(item(part.name).textContent?.includes(COMPARE_TABLE.restsOnPart)).toBe(false);
  });

  test("test_an_area_that_is_not_ranked_for_want_of_character_says_so_in_words", () => {
    const unknown = two.areas.find((area) => area.status === "character_unknown") as ComparedArea;
    render(<CompareAreas chosen={chosenOf(two)} compared={two.areas} />);

    expect(item(unknown.name)).toHaveTextContent(COMPARE_STATUS.character_unknown);
    expect(item(unknown.name).textContent?.includes("character_unknown")).toBe(false);
    // It has no fit, so nothing is said of what a fit rests on.
    expect(item(unknown.name).querySelector("[data-part='true']")).toBeNull();
  });

  test("test_a_status_the_website_has_no_words_for_is_left_out_and_never_shown_as_its_code", () => {
    const newer = { ...(three.areas[0] as ComparedArea), status: "held_for_review" };
    render(<CompareAreas chosen={chosen} compared={[newer as unknown as ComparedArea, ...three.areas.slice(1)]} />);

    expect(statusWords("held_for_review")).toBeNull();
    expect(item(newer.name).textContent?.includes("held_for_review")).toBe(false);
    expect(item(newer.name).textContent?.includes("undefined")).toBe(false);
    for (const status of Object.keys(COMPARE_STATUS)) expect(statusWords(status)).not.toBeNull();
  });
});
const STYLES = rulesOf(readFileSync(path.join(__dirname, "CompareTable.module.css"), "utf8"));

describe("the comparison, stacked on a narrow screen", () => {
  test("test_every_part_of_the_table_says_its_role_so_that_it_stays_a_table_when_stacked", () => {
    render(<CompareTable data={three} combine="slowest" />);
    const table = screen.getByRole("table", { name: COMPARE_TABLE.caption });

    // Laid out as blocks, a browser may forget that a table is one. Each part that is
    // laid out so says its role again: the two groups of rows were the ones that did not.
    expect(table).toHaveAttribute("role", "table");
    expect([...table.querySelectorAll("thead, tbody")].map((group) => group.getAttribute("role"))).toEqual([
      "rowgroup",
      "rowgroup",
    ]);
    for (const row of table.querySelectorAll("tr")) expect(row).toHaveAttribute("role", "row");
    for (const cell of table.querySelectorAll("td")) expect(cell).toHaveAttribute("role", "cell");
    for (const header of table.querySelectorAll("thead th")) expect(header).toHaveAttribute("role", "columnheader");
    for (const header of table.querySelectorAll("tbody th")) expect(header).toHaveAttribute("role", "rowheader");
  });

  test("test_every_element_that_is_laid_out_as_a_block_is_one_that_says_its_role", () => {
    const stacked = STYLES.filter(
      (rule) => rule.under !== null && rule.sets.get("display") === "block" && rule.selector.startsWith(".table"),
    );
    const elements = stacked.map((rule) => rule.selector.split(/\s+/).pop());

    expect(elements.sort()).toEqual([".table", "caption", "tbody", "td", "th", "tr"]);
    // The headings of the columns are kept for a screen reader, and not drawn.
    expect(STYLES.some((rule) => rule.under !== null && isFor(rule.selector, "head") && rule.sets.has("clip-path"))).toBe(
      true,
    );
  });

  test("test_each_cell_says_whose_it_is_for_the_eye_and_the_column_says_it_to_a_reader", () => {
    render(<CompareTable data={three} combine="slowest" />);
    const rows = within(screen.getByRole("table", { name: COMPARE_TABLE.caption })).getAllByRole("row").slice(1);

    for (const row of rows) {
      const whose = [...row.querySelectorAll("td")].map(
        (cell) => cell.querySelector("[aria-hidden='true']")?.textContent,
      );
      expect(whose).toEqual(three.areas.map((area) => area.name));
    }
  });

  test("test_the_comparison_has_no_accessibility_fault", async () => {
    const { container } = render(<CompareTable data={three} combine="slowest" />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
