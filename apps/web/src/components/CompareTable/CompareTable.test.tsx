import { readFileSync } from "node:fs";
import path from "node:path";

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";

import { COMPARE_STATUS, COMPARE_TABLE, statusWords } from "@/content/compare";
import { crimeVibes } from "@/content/crime";
import { FACT_COLUMNS } from "@/content/facts";
import { KNOWN } from "@/content/kit";
import { COMBINE } from "@/content/labels";
import { JOURNEYS } from "@/content/search";
import { TOWN } from "@/content/town";
import { TOWNS } from "@/content/towns";
import { recordedAnswer } from "@/lib/api/recorded";
import type { CompareData, CompareRow, ComparedArea, Fact } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { holdsAFigure } from "../kit/reads";
import { CompareAreas, CompareTable } from "./CompareTable";
import { HEADS_MAY_SAY_OF_THEIR_TOWNS, HEADS_SAY_OF_THEIR_TOWNS } from "./look";
import { marksOfTheChosen, releaseOf, type Towns } from "./towns";

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
/**
 * A column of a fact with a figure under it. The column is named by its key: what its name
 * says is held beside the names, and may be written again.
 */
const figureUnder = (column: string) => new RegExp(`${column.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\d+`);

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
      expect(cells.some((cell) => figureUnder(FACT_COLUMNS.typical).test(cell.textContent ?? ""))).toBe(true);
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
    expect(cellOf(toTheWorks, "Gorsebeck")).toHaveTextContent(figureUnder(FACT_COLUMNS.overLimit));
  });

  test("test_an_area_that_is_listed_apart_is_timed_in_every_row_and_adds_nothing", () => {
    render(<CompareTable data={two} combine="slowest" />);
    const apart = two.areas.find((area) => area.status === "character_unknown");

    for (const row of journeys()) {
      const cell = cellOf(row, apart?.name ?? "");
      expect(figureUnder(FACT_COLUMNS.typical).test(cell.textContent ?? "")).toBe(true);
      // It was not scored, so its journeys add nothing to a fit it does not have.
      expect(/Adds \d+ of 100 to the fit/.test(cell.textContent ?? "")).toBe(false);
      expect(cell.textContent?.includes(COMPARE_TABLE.notScored)).toBe(false);
    }
  });

  test("test_what_the_journeys_add_stands_once_for_each_area_beside_the_journey_that_decided_it", () => {
    render(<CompareTable data={two} combine="slowest" />);

    for (const area of two.areas) {
      const said = journeys().filter((row) => /Adds \d+ of 100 to the fit/.test(cellOf(row, area.name).textContent ?? ""));
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
    expect(journeys().some((row) => /Adds \d+ of 100 to the fit/.test(row.textContent ?? ""))).toBe(false);
    unmount();
    // Where one journey decides it, that journey says what the journeys add.
    render(<CompareTable data={two} combine="slowest" />);
    expect(counts().textContent?.includes(COMPARE_TABLE.journeys.together)).toBe(false);
  });

  test("test_the_head_of_a_row_is_named_by_what_counts_and_where_a_journey_is_to_and_by_no_note", () => {
    // Every cell of a row is read under the name of its head. Named by all that it holds, the
    // head of the journeys was its weight, which journey counts and why none says what it adds.
    render(<CompareTable data={two} combine="slowest" />);

    expect(rowsOf().map((row) => headOf(row))).toHaveLength(two.rows.length);
    for (const [at, row] of rowsOf().entries()) {
      const { label, place } = two.rows[at] as CompareRow;
      const named = place === null ? label : `${label} ${COMPARE_TABLE.journeys.to(place.name)}`;
      expect(headOf(row)).toHaveAccessibleName(named);
    }
    // The weight and which journey counts are read in the head, where they stand.
    expect(headOf(journeys()[0])).toHaveTextContent(COMBINE.slowest);
    expect(headOf(journeys()[0])).toHaveTextContent(/Weight \d+/);
    const names = rowsOf().map((row) => headOf(row).getAttribute("aria-labelledby"));
    expect(new Set(names).size).toBe(names.length);
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

describe("a journey that was estimated, in a comparison", () => {
  /** Three areas on a firm limit, in a release that holds no journey time: one of each band. */
  const estimated: CompareData = recordedAnswer("compare", "estimate/compare").body.data;
  const theJourney = () => journeys()[0] as HTMLElement;
  const cellsOf = () => within(theJourney()).getAllByRole("cell");

  test("test_each_cell_says_the_band_in_the_apis_words_and_that_it_is_an_estimate", () => {
    render(<CompareTable data={estimated} combine="slowest" />);
    const row = estimated.rows.find((one) => one.place !== null);
    if (!row) throw new Error("the recording compares no journey");

    expect(row.cells.map((cell) => cell.estimate)).toEqual(["likely_within", "borderline", "likely_beyond"]);
    for (const [at, cell] of row.cells.entries()) {
      const fact = estimated.facts.find((one) => one.fact_id === cell.fact_id);
      if (!fact || !cell.estimate) throw new Error("the cell cites no fact of an estimate");
      const drawn = cellsOf()[at] as HTMLElement;

      expect(fact.template).toBe("travel_estimated");
      expect(drawn).toHaveTextContent(`${FACT_COLUMNS.estimate}${fact.slots.verdict}`);
      expect(fact.slots.verdict).toBe(JOURNEYS.estimated[cell.estimate]);
      // That it is an estimate, and what it was worked out from, is the line of the fact, as
      // it came: a whole sentence, which names the distance and says that no timetable stands
      // behind it. The cell draws it and writes none of its own.
      expect(fact.slots.estimated).toMatch(/^This is an estimate\b.*\bdistance\b.*\bnot\b.*\btimetable\.$/);
      expect(drawn).toHaveTextContent(`${FACT_COLUMNS.howKnown}${fact.slots.estimated}`);
      expect(drawn.textContent?.split(fact.slots.estimated ?? "no line")).toHaveLength(2);
      // It is never given in minutes: the one number of the cell is the limit that was set.
      expect(cell.value).toBeNull();
      expect(drawn).toHaveTextContent(`${FACT_COLUMNS.limit}${fact.slots.limit}`);
      expect(drawn.textContent?.includes(COMPARE_TABLE.journeys.missing)).toBe(false);
      expect(within(drawn).getByRole("button", { name: /^Source for / })).toBeInTheDocument();
    }
  });

  test("test_an_area_a_firm_limit_leaves_out_says_that_the_journey_is_likely_beyond_it_and_estimated", () => {
    const left = estimated.areas.filter((area) => area.status === "commute_likely_beyond");

    expect(left).toHaveLength(1);
    expect(estimated.areas.filter((area) => area.status === "ranked")).toHaveLength(2);
    expect(statusWords("commute_likely_beyond")).toBe(COMPARE_STATUS.commute_likely_beyond);
    expect(COMPARE_STATUS.commute_likely_beyond).toContain("likely beyond a firm limit");
    expect(COMPARE_STATUS.commute_likely_beyond).toContain(JOURNEYS.estimatedFrom);
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
      // Where the area sits is said in words by the name of its picture, as where the vibes are compared.
      expect(within(cells[at] as HTMLElement).getByRole("img").getAttribute("aria-label")?.includes(`band ${band} of 5`)).toBe(true);
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

    // Beside the fit, in a sentence: how much of what counts the area has a figure for.
    expect(item(part.name)).toHaveTextContent(COMPARE_TABLE.standing(1 + defaults.areas.indexOf(part), 86 - defaults.areas.indexOf(part)));
    expect(item(part.name)).toHaveTextContent(`${COMPARE_TABLE.basedOn(part.present, part.counted)}.`);
    // It is marked as a trade-off is, and the mark is not the only sign of it.
    expect(item(part.name).querySelector("[data-part='true']")).not.toBeNull();
    expect(item(whole.name).textContent?.includes("things that count")).toBe(false);
    expect(item(whole.name).querySelector("[data-part='true']")).toBeNull();
    // What follows from it is said once, over what counts, and not at the head of every
    // such area: in the column of an area it ran to seven lines, and stood the vibes lower.
    expect(item(part.name).textContent?.includes(COMPARE_TABLE.restsOnPart)).toBe(false);
  });

  test("test_what_follows_from_a_fit_that_rests_on_part_is_said_once_over_what_counts_where_an_area_has_such_a_fit", () => {
    const { unmount } = render(<CompareTable data={defaults} combine="slowest" fits />);
    const part = defaults.areas.filter((area) => area.status === "ranked" && area.present < area.counted);

    expect(part.length).toBeGreaterThan(0);
    const said = screen.getAllByText(COMPARE_TABLE.restsOnPart);
    expect(said).toHaveLength(1);
    expect(said[0]?.closest(".visually-hidden, [hidden], [aria-hidden='true'], details")).toBeNull();
    expect(Boolean((said[0] as HTMLElement).compareDocumentPosition(counts()) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    unmount();

    // With no fit to show, nothing is said of what a fit rests on.
    const bare = render(<CompareTable data={defaults} combine="slowest" />);
    expect(screen.queryByText(COMPARE_TABLE.restsOnPart)).toBeNull();
    bare.unmount();
    // Nor where every area that is ranked has a figure for everything that counts.
    const whole: CompareData = { ...defaults, areas: defaults.areas.map((area) => ({ ...area, present: area.counted })) };
    render(<CompareTable data={whole} combine="slowest" fits />);
    expect(screen.queryByText(COMPARE_TABLE.restsOnPart)).toBeNull();
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

describe("the head of each area, as the look draws it", () => {
  const release = recordedAnswer("get_meta", "meta").body.data;
  const { bands } = recordedAnswer("list_areas", "areas").body.data;
  const chosenOf = (data: CompareData) =>
    data.areas.map((area) => {
      const found = areas.find((one) => one.area_id === area.area_id);
      if (!found) throw new Error("the release holds no such area");
      return { area_id: found.area_id, slug: found.slug, name: found.name };
    });
  const townsOf = (data: CompareData): Towns => ({
    meta: releaseOf(release.tags, crimeVibes(release)),
    marks: marksOfTheChosen(bands, data.areas),
  });
  /** A search in which the areas stand first, second and third, and the first of them is not the first that was chosen. */
  const standings = new Map(three.areas.map((area, at) => [area.area_id, { rank: three.areas.length - at, fit: 60 + at }]));
  const heads = () => within(screen.getByRole("list", { name: COMPARE_TABLE.areas })).getAllByRole("listitem");
  /** What an element is drawn as, and everything in it: each element by what it is, its classes and the marks it bears. */
  const drawnAs = (head: HTMLElement, leaving: string) =>
    [head, ...head.querySelectorAll<HTMLElement>("*")]
      .filter((one) => one.closest(leaving) === null)
      .map((one) => `${one.tagName} ${one.className} ${one.getAttribute("data-kind") ?? ""}`.trim());

  test("test_the_areas_stand_side_by_side_within_one_plain_edge_each_with_its_name_first_in_the_face_of_names", () => {
    render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} />);
    const holds = screen.getByRole("list", { name: COMPARE_TABLE.areas }).parentElement as HTMLElement;

    // One plain edge of ink holds them all: a box with a shadow round each of four areas was noise,
    // and stood the vibes a screen lower.
    expect(holds).toHaveAttribute("data-kind", "plain");
    expect(holds).toHaveAttribute("data-areas", String(three.areas.length));
    expect(heads()).toHaveLength(three.areas.length);
    for (const [at, head] of heads().entries()) {
      expect(head).not.toHaveAttribute("data-kind");
      expect(head.firstElementChild).toHaveClass("areaName");
      expect(head.firstElementChild?.textContent).toBe(three.areas[at]?.name);
    }
    const name = STYLES.filter((rule) => rule.selector === ".areaName" && rule.under === null).flatMap((rule) => rule.sets.get("font") ?? []);
    expect(name).toEqual(["400 var(--name-2) / 1.1 var(--font-name)"]);
  });

  test("test_every_area_has_its_town_under_its_name_all_of_one_size_and_nothing_says_there_what_a_town_is", () => {
    // The founder asked for the line that says what a town is to go from the results. It
    // stood at the head of a comparison in the same words, of the same towns, before the
    // first of them: a person who compares areas has come from the results.
    render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} />);
    const holds = screen.getByRole("list", { name: COMPARE_TABLE.areas }).parentElement as HTMLElement;

    expect(HEADS_SAY_OF_THEIR_TOWNS).toBe("nothing");
    expect(HEADS_MAY_SAY_OF_THEIR_TOWNS).toEqual(["nothing", "line"]);
    expect(within(holds).queryByText(TOWNS.line)).toBeNull();
    // What holds the areas holds them and no more: the areas are the first thing of it.
    expect([...holds.children].map((part) => part.tagName)).toEqual(["UL"]);
    expect(holds).toHaveAttribute("data-says", "nothing");
    for (const [at, head] of heads().entries()) {
      const town = within(head).getByRole("img");
      expect(head.children[1]?.tagName).toBe("FIGURE");
      expect(town).toHaveAttribute("data-size", "small");
      expect(town.getAttribute("aria-label")).toContain(three.areas[at]?.name);
    }
    // No town says it of itself either: the line is the first thing a town says, and is not drawn.
    const notDrawn = STYLES.filter((rule) => /figcaption/.test(rule.selector) && rule.sets.get("display") === "none");
    expect(notDrawn.map((rule) => rule.selector)).toEqual([
      ".area > .town > figcaption > :first-child",
      ".area > .town > figcaption:not(:has(> :not(:first-child)))",
    ]);
    for (const head of heads()) expect(head.querySelector("figcaption > :first-child")?.textContent).toBe(TOWN.line);
  });

  test("test_one_line_of_the_look_has_what_a_town_is_said_once_over_the_towns_of_a_comparison", () => {
    // As it was before the founder asked for it to go from the results.
    render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} saysOfTowns="line" />);
    const holds = screen.getByRole("list", { name: COMPARE_TABLE.areas }).parentElement as HTMLElement;

    expect(holds).toHaveAttribute("data-says", "line");
    for (const [at, head] of heads().entries()) {
      const town = within(head).getByRole("img");
      // It comes after the name, and never before it.
      const after = (head.firstElementChild?.compareDocumentPosition(town) ?? 0) & Node.DOCUMENT_POSITION_FOLLOWING;
      expect(after).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
      expect(head.children[1]?.tagName).toBe("FIGURE");
      expect(head.children[1]).toContainElement(town);
      expect(town).toHaveAttribute("data-size", "small");
      expect(town.getAttribute("aria-label")).toContain(three.areas[at]?.name);
    }
    expect(new Set(heads().map((head) => within(head).getByRole("img").getAttribute("data-size"))).size).toBe(1);
    // A town never stands without the line that says it is no picture of the place. Under
    // each of four towns it was the same words four times: it is said once, in sight,
    // before the first of them, and no town says it again.
    const lines = within(holds).getAllByText(TOWNS.line);
    expect(lines).toHaveLength(1);
    expect(lines[0]?.closest(".visually-hidden, [hidden], [aria-hidden='true'], li")).toBeNull();
    expect(Boolean((lines[0] as HTMLElement).compareDocumentPosition(heads()[0] as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    const notDrawn = STYLES.filter((rule) => /figcaption/.test(rule.selector) && rule.sets.get("display") === "none");
    expect(notDrawn.map((rule) => rule.selector)).toEqual([
      ".area > .town > figcaption > :first-child",
      ".area > .town > figcaption:not(:has(> :not(:first-child)))",
    ]);
    // What is not drawn is the line and nothing else: the line is the first thing a town says.
    for (const head of heads()) expect(head.querySelector("figcaption > :first-child")?.textContent).toBe(TOWN.line);
  });

  test("test_on_a_wide_screen_each_area_stands_over_the_column_it_has_in_the_tables_under_it", () => {
    // A table has a column for what a row is of, and then one for each area, all of one
    // width. So the heads have as many, and the areas begin in the second.
    const WIDE = "@media (min-width: 60rem)";
    const wide = (selector: string) =>
      new Map(STYLES.filter((rule) => rule.under === WIDE && rule.selector === selector).flatMap((rule) => [...rule.sets]));

    for (const count of [2, 3, 4]) {
      expect([count, wide(`.heads[data-areas="${count}"]`).get("grid-template-columns")]).toEqual([
        count,
        `repeat(${count + 1}, minmax(0, 1fr))`,
      ]);
    }
    expect([wide(".heads > .areas").get("grid-template-columns"), wide(".heads > .areas").get("grid-column")]).toEqual([
      "subgrid",
      "2 / -1",
    ]);
    expect(STYLES.filter((rule) => rule.selector === ".table" && rule.under === null).map((rule) => rule.sets.get("table-layout"))).toEqual(["fixed"]);
    // A rule of ink stands before each area there, as before each column of an area in a table.
    expect(wide(".heads .area").get("border-inline-start")).toBe("var(--edge) solid var(--border)");
    expect(wide(".table th + td").get("border-inline-start")).toBe("var(--edge) solid var(--border)");
    expect(wide(".heads .area").get("padding-inline")).toBe(wide(".table th + td").get("padding-inline-start"));
    // The room at either side of the heads is the room at either side of a table.
    const page = rulesOf(readFileSync(path.join(__dirname, "CompareView.module.css"), "utf8"));
    const ofATable = page.find((rule) => rule.selector === ".part" && rule.under === null)?.sets;
    const ofTheHeads = STYLES.find((rule) => rule.selector === ".heads" && rule.under === null)?.sets;
    expect(ofTheHeads?.get("--within")).toBe(ofATable?.get("--within"));
    expect(ofATable?.get("padding")).toContain("var(--within)");
    expect(ofTheHeads?.get("padding")).toContain("var(--within)");
  });

  test("test_the_parts_of_each_area_stand_on_the_lines_of_the_area_beside_it_where_a_browser_can_lay_them_so", () => {
    // Seen in a browser: a name that ran to three lines put its town lower than the towns beside it.
    const SUBGRID = "@supports (grid-template-rows: subgrid)";
    const laid = STYLES.filter((rule) => rule.under === SUBGRID);
    const setsOf = (selector: string) => laid.find((rule) => rule.selector === selector)?.sets;

    expect(setsOf(".area")?.get("grid-template-rows")).toBe("subgrid");
    // With its town an area has four parts, and without it three: a box has no line that holds nothing.
    expect([setsOf(".area")?.get("grid-row"), setsOf(".area:has(> .town)")?.get("grid-row")]).toEqual(["span 3", "span 4"]);
    render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} />);
    for (const head of heads()) expect([...head.children].map((part) => part.className.split(" ").pop())).toEqual(["areaName", "town", "status", "ways"]);
    cleanup();
    render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} />);
    for (const head of heads()) expect([...head.children].map((part) => part.className.split(" ").pop())).toEqual(["areaName", "status", "ways"]);
    // A town is as high as what it holds: one that says less than the town beside it is not pulled apart.
    expect(setsOf(".area > .town")?.get("align-self")).toBe("start");
    expect(laid.filter((rule) => rule.selector === ".area > .ways").map((rule) => rule.sets.get("align-self"))).toEqual(["start", "end"]);
    // Where a browser cannot, each box is laid out by itself, and the ways on stand at its foot.
    const alone = STYLES.filter((rule) => rule.under === null);
    expect(alone.find((rule) => rule.selector === ".area")?.sets.get("display")).toBe("flex");
    expect(alone.find((rule) => rule.selector === ".ways")?.sets.get("margin-block-start")).toBe("auto");
  });

  test("test_with_nothing_to_draw_a_town_from_no_town_is_drawn_and_nothing_stands_in_for_one", () => {
    render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} />);

    for (const head of heads()) {
      expect(within(head).queryByRole("img")).toBeNull();
      expect(head.querySelector("figure")).toBeNull();
      expect(head.textContent?.includes(TOWN.line)).toBe(false);
    }
  });

  test("test_a_town_is_there_before_the_comparison_is_answered_and_follows_the_table_once_it_is", () => {
    const towns = townsOf(three);
    const { rerender } = render(<CompareAreas chosen={chosenOf(three)} waiting towns={towns} />);
    const before = heads().map((head) => within(head).getByRole("img").getAttribute("aria-label"));

    expect(before.every((said) => said !== null && said !== "")).toBe(true);

    // The answer says the same of the release the page was built on, so no town changes.
    rerender(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={towns} character={three.character} />);
    expect(heads().map((head) => within(head).getByRole("img").getAttribute("aria-label"))).toEqual(before);

    // Where it says otherwise, as of a release that moved on, a town says what the table says.
    const moved = three.character.map((row) => ({
      ...row,
      marks: row.marks.map((mark) => {
        const band = mark.band === null ? null : (mark.band % 5) + 1;
        return { ...mark, band, spread_low: band, spread_high: band };
      }),
    }));
    rerender(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={towns} character={moved} />);
    const after = heads().map((head) => within(head).getByRole("img").getAttribute("aria-label"));
    expect(after.filter((said, at) => said === before[at])).toEqual([]);
  });

  test("test_nobody_wins_a_comparison_every_area_is_drawn_as_the_next_is_whatever_its_rank", () => {
    render(
      <CompareAreas chosen={chosenOf(three)} compared={three.areas} standings={standings} towns={townsOf(three)} />,
    );

    // Its town and what is said of it differ, as the areas do. All else of an area is drawn one way.
    const drawn = heads().map((head) => drawnAs(head, "figure, .status"));
    expect(drawn[0]?.length).toBeGreaterThan(5);
    for (const one of drawn) expect(one).toEqual(drawn[0]);
    // What is said of an area is said in lines that are drawn alike, of the first as of the last.
    const said = heads().map((head) => [...(head.querySelector(".status")?.children ?? [])].map((line) => `${line.tagName} ${line.className}`));
    const ofTheRanked = said.filter((_, at) => three.areas[at]?.status === "ranked");
    expect(ofTheRanked.length).toBeGreaterThan(1);
    expect(new Set(ofTheRanked.map((lines) => JSON.stringify(lines))).size).toBe(1);
    for (const head of heads()) {
      // No pennant, no box in hand, nothing amber and nothing cobalt: nothing marks an area out.
      expect(head.querySelector(".pennant, [data-kind='box-on'], [data-kind='on'], [data-kind='go']")).toBeNull();
      expect(head.querySelector("[aria-current], [aria-pressed], [aria-selected]")).toBeNull();
    }
  });

  test("test_the_areas_stand_in_the_order_they_were_given_in_and_never_in_the_order_of_their_rank", () => {
    render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} standings={standings} />);

    // The last that was chosen stands first in the search, and is drawn last all the same.
    expect([...standings.values()].map((standing) => standing.rank)).toEqual([3, 2, 1]);
    expect(heads().map((head) => head.firstElementChild?.textContent)).toEqual(three.areas.map((area) => area.name));
    const order = STYLES.filter((rule) => [...rule.sets.keys()].some((property) => /^(order|flex-direction|grid-auto-flow|direction)$/.test(property)));
    expect(order.map((rule) => [rule.selector, rule.sets.get("flex-direction")])).toEqual([[".area", "column"]]);
  });

  test("test_the_name_of_an_area_leads_to_its_page_and_a_small_way_out_takes_it_from_the_comparison", () => {
    // Two buttons from edge to edge under every area stood the vibes 120 px lower on a
    // desk, and four times that on a phone. The name leads to the page, as the name of a
    // result does, and the way out is the quietest thing at the head of an area.
    render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} />);

    for (const [at, head] of heads().entries()) {
      const name = three.areas[at]?.name ?? "";
      const others = chosenOf(three).filter((one) => one.name !== name);
      const open = within(head).getByRole("link", { name: COMPARE_TABLE.open(name) });
      const out = within(head).getByRole("link", { name: COMPARE_TABLE.takeOut(name) });

      expect(within(head).getAllByRole("link")).toEqual([open, out]);
      expect(open.closest("p")).toBe(head.firstElementChild);
      expect(open).toHaveAttribute("href", `/synthetic/${chosenOf(three)[at]?.slug}`);
      expect(out).toHaveAttribute("href", `/compare?${others.map((one) => `a=${one.slug}`).join("&")}`);
      // What is seen of each is in the name a person speaks to press it, as it is seen.
      expect(open.textContent).toBe(name);
      expect(COMPARE_TABLE.open(name)).toContain(name);
      expect(out.textContent).toBe(COMPARE_TABLE.takeOutShort);
      expect(COMPARE_TABLE.takeOut(name).startsWith(COMPARE_TABLE.takeOutShort)).toBe(true);
      for (const way of [open, out]) {
        expect(way).toHaveClass("target-min");
        // Which page a person reads next is told to no server ahead of time.
        expect(way).toHaveAttribute("data-prefetch", "false");
        // Neither is drawn as a button, and so neither as the button that matters most.
        expect(way.querySelector("[data-kind]")).toBeNull();
      }
      // The cross before the way out is a drawing, and is dress: the words say what it does.
      const cross = out.querySelector("[aria-hidden='true']") as HTMLElement;
      expect(cross.style.getPropertyValue("--art")).toBe('url("/art/ui-cross.png")');
      expect(cross.textContent).toBe("");
    }
  });

  describe("an area that is taken out", () => {
    /** jsdom follows no link, and says so loudly: the press is made, and leads nowhere. */
    const leadsNowhere = (event: Event) => event.preventDefault();
    beforeEach(() => document.addEventListener("click", leadsNowhere));
    afterEach(() => document.removeEventListener("click", leadsNowhere));

    const open = (name: string) => screen.getByRole("link", { name: COMPARE_TABLE.open(name) });
    const out = (name: string) => screen.getByRole("link", { name: COMPARE_TABLE.takeOut(name) });
    const [first = "", second = "", third = ""] = three.areas.map((area) => area.name);

    test("test_it_hands_the_focus_to_the_area_that_stood_after_it_and_never_leaves_it_on_nothing", () => {
      // Seen in a browser, by keyboard: Enter on "Take out Gorsebeck" left the focus on nothing,
      // and the next Tab began again at the head of the page. The way out goes with its area.
      render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} />);
      out(second).focus();

      fireEvent.click(out(second));

      // The name of the area beside it, which stays, and which is a stop of the keyboard.
      expect(open(third)).toHaveFocus();
      expect(open(third).tagName).toBe("A");
    });

    test("test_the_last_of_them_hands_it_to_the_area_before_it", () => {
      render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} />);
      out(third).focus();

      fireEvent.click(out(third));

      expect(open(second)).toHaveFocus();
    });

    test("test_the_page_is_not_moved_under_the_press", () => {
      render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} />);
      const given = jest.spyOn(open(second), "focus");

      fireEvent.click(out(first));

      expect(given.mock.calls).toEqual([[{ preventScroll: true }]]);
    });

    test("test_where_no_area_would_be_left_it_is_handed_to_the_head_of_the_page", () => {
      const [one] = chosenOf(three);
      if (!one) throw new Error("the recording compares no area");
      const head = { current: document.createElement("h1") };
      head.current.tabIndex = -1;
      document.body.append(head.current);
      render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} head={head} />);
      // Every area but one is off the page, as it would be had they been taken out.
      for (const item of heads().slice(1)) item.remove();

      fireEvent.click(out(one.name));

      expect(head.current).toHaveFocus();
      head.current.remove();
    });

    test("test_a_press_that_opens_the_comparison_of_the_others_elsewhere_moves_no_focus", () => {
      // With a key held down a link is opened in another tab or window, and this page stays as it is.
      render(<CompareAreas chosen={chosenOf(three)} compared={three.areas} towns={townsOf(three)} />);
      out(second).focus();

      for (const held of [{ metaKey: true }, { ctrlKey: true }, { shiftKey: true }, { button: 1 }]) fireEvent.click(out(second), held);

      expect(out(second)).toHaveFocus();
    });
  });

  test("test_a_comparison_of_no_area_draws_no_frame_with_nothing_in_it", () => {
    // Seen in a browser: an empty box some 600 px wide and 12 high stood under the head of the page.
    const { container } = render(<CompareAreas chosen={[]} towns={townsOf(three)} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_one_area_alone_has_the_way_to_its_page_and_no_way_out_of_a_comparison_of_one", () => {
    const [one] = chosenOf(three);
    if (!one) throw new Error("the recording compares no area");
    render(<CompareAreas chosen={[one]} towns={townsOf(three)} />);

    expect(within(heads()[0] as HTMLElement).getAllByRole("link").map((link) => link.getAttribute("aria-label"))).toEqual([
      COMPARE_TABLE.open(one.name),
    ]);
    expect(within(heads()[0] as HTMLElement).getByRole("img")).toBeInTheDocument();
  });

  test("test_a_fit_that_rests_on_part_says_approx_data_after_the_mark_of_what_is_not_whole_and_nothing_of_it_warns", () => {
    // It was marked as a trade-off was, with a warning sign in poppy. A fit that rests on
    // part of what counts is no fault and no danger: it says so as a result does, in the
    // two words after the mark of what is not whole, and then how much it rests on.
    const defaults: CompareData = recordedAnswer("compare", "compare-two-defaults").body.data;
    const chosen = defaults.areas.flatMap((area) => areas.find((one) => one.area_id === area.area_id) ?? []);
    render(<CompareAreas chosen={chosen} compared={defaults.areas} />);
    const onPart = defaults.areas.filter((area) => area.status === "ranked" && area.present < area.counted);
    const said = [...document.querySelectorAll<HTMLElement>("[data-part='true']")];

    expect(onPart.length).toBeGreaterThan(0);
    expect(said).toHaveLength(onPart.length);
    said.forEach((one, at) => {
      const area = onPart[at];
      if (area === undefined) throw new Error("More is said than there are areas whose fit rests on part.");
      expect(one.textContent).toBe(`${KNOWN.some}. ${COMPARE_TABLE.basedOn(area.present, area.counted)}.`);
      const mark = one.querySelector<HTMLElement>("[style*='/art/']");
      expect(mark?.style.getPropertyValue("--art")).toBe('url("/art/ui-approx.png")');
      expect(mark).toHaveAttribute("aria-hidden", "true");
    });
    // Nothing of it is poppy, and its words are ink and the quieter colour.
    const written = readFileSync(path.join(__dirname, "CompareTable.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    expect(/tradeoff|poppy/.test(written)).toBe(false);
    expect(STYLES.filter((rule) => rule.selector === ".partMark")).toEqual([]);
    const colours = (selector: string) => STYLES.filter((rule) => rule.selector === selector && rule.under === null).map((rule) => rule.sets.get("color"));
    expect([colours(".part"), colours(".onPart")]).toEqual([["var(--text)"], ["var(--muted)"]]);
  });

  test("test_the_heads_of_the_areas_have_no_accessibility_fault", async () => {
    const { container } = render(
      <CompareAreas chosen={chosenOf(three)} compared={three.areas} standings={standings} towns={townsOf(three)} />,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the tables of a comparison, as the look draws them", () => {
  const { tags } = recordedAnswer("get_meta", "meta").body.data;
  /** What a row is of: its name, which stands after the small drawing of its vibe where the row is of one. */
  const labelOf = (row: HTMLElement) => within(row).getByRole("rowheader").querySelector("[data-reads]") as HTMLElement;

  test("test_the_name_of_a_vibe_is_a_short_label_and_the_name_of_a_measure_is_read", () => {
    render(<CompareTable data={three} combine="slowest" tags={tags} />);

    const drawn = rowsOf().map((row) => labelOf(row).getAttribute("data-reads"));

    expect(drawn).toEqual(
      three.rows.map((row) => String(row.component.startsWith("feature:") || holdsAFigure(row.label))),
    );
    // Both kinds are in the recording, so both are held.
    expect(new Set(drawn)).toEqual(new Set(["true", "false"]));
    const faces = STYLES.filter(
      (rule) => rule.under === null && /^\.label(\[|$)/.test(rule.selector) && rule.sets.has("font"),
    ).map((rule) => [rule.selector, rule.sets.get("font")]);
    expect(faces).toEqual([
      [".label", "400 var(--name-1) / 1.1 var(--font-name)"],
      ['.label[data-reads="true"]', "700 var(--size-body) / 1.3 var(--font-say)"],
    ]);
  });

  test("test_every_area_has_as_much_room_as_the_next_and_the_table_says_how_many_they_are", () => {
    render(<CompareTable data={three} combine="slowest" tags={tags} />);

    expect(counts()).toHaveAttribute("data-areas", String(three.areas.length));
    const laid = STYLES.filter((rule) => rule.selector === ".table" && rule.under === null).flatMap((rule) => rule.sets.get("table-layout") ?? []);
    expect(laid).toEqual(["fixed"]);
    // No rule gives one column of an area a width, a ground or a weight that another has not.
    // What a town says first is its line, which is said once over the towns: that is of what
    // a town says, in every column alike, and of no column.
    const ofOne = STYLES.filter(
      (rule) =>
        /:(nth-child|nth-of-type|first-child|first-of-type|last-of-type|only-child)\b/.test(rule.selector) &&
        !/^\.area > \.town > figcaption/.test(rule.selector),
    );
    expect(ofOne.map((rule) => rule.selector)).toEqual([]);
    // The last row of a table has no rule under it, and that is all that is said of a last thing.
    const last = STYLES.filter((rule) => /:last-child\b/.test(rule.selector));
    expect(last.map((rule) => rule.selector).every((selector) => /(tr|\.row):last-child/.test(selector))).toBe(true);
    expect(last.flatMap((rule) => [...rule.sets.keys()]).filter((property) => !/^(border-block-end|padding-block-end)$/.test(property))).toEqual([]);
  });

  test("test_a_row_stands_on_a_rule_and_no_row_and_no_cell_is_a_box", () => {
    const boxed = STYLES.filter(
      (rule) => rule.sets.has("border-image") || /var\(--(frame-box|box-shadow)/.test([...rule.sets.values()].join(" ")),
    );
    // A notice has a band inside its edge, which is drawn as a shadow that falls nowhere:
    // what is said once over the vibes, and what a vibe says of itself in its row.
    const shadows = STYLES.filter((rule) => rule.sets.has("box-shadow") && !/forced-colors/.test(rule.under ?? ""));

    expect(boxed.map((rule) => rule.selector)).toEqual([]);
    expect(shadows.map((rule) => [rule.selector, /^inset /.test(rule.sets.get("box-shadow") ?? "")])).toEqual([
      [".unplaced", true],
      [".caveat", true],
    ]);
    const rules = STYLES.filter((rule) => /(^|\s)(\.row|\.table \.cell)$/.test(rule.selector) && !/forced-colors/.test(rule.under ?? ""));
    expect(rules.flatMap((rule) => [...rule.sets.keys()]).filter((property) => /^(background|box-shadow|outline)/.test(property))).toEqual([]);
  });

  test("test_the_steps_of_a_vibe_that_counts_are_the_first_thing_drawn_in_their_cell_as_they_are_where_the_vibes_are_compared", () => {
    // Wherever five steps stand in rows they stand in one column, so that the eye runs down
    // them. In the table of what counts a vibe is a row among figures, and its steps begin
    // where the cell begins, as every line of steps under them does.
    render(<CompareTable data={three} combine="slowest" tags={tags} />);
    const lines = [...counts().querySelectorAll<HTMLElement>("td [data-placed='true']")];

    expect(lines.length).toBeGreaterThan(2);
    for (const line of lines) {
      const gauge = line.parentElement as HTMLElement;
      const holds = gauge.parentElement as HTMLElement;
      expect([holds.tagName, holds.className, holds.firstElementChild === gauge]).toEqual(["P", "placed", true]);
      // Before its steps stands the picture of its low end alone, which is as wide whatever the vibe.
      const before = [...gauge.children].slice(0, [...gauge.children].indexOf(line)) as HTMLElement[];
      expect(before.map((one) => one.style.getPropertyValue("--w"))).toEqual(["16"]);
    }
    const placed = new Map(STYLES.filter((rule) => rule.selector === ".placed" && rule.under === null).flatMap((rule) => [...rule.sets]));
    // The gauge, and under it what is said of it, each from where the cell begins.
    expect([placed.get("display"), placed.get("grid-template-columns"), placed.get("justify-items")]).toEqual([
      "grid",
      "minmax(0, 1fr)",
      "start",
    ]);
    expect([placed.get("justify-content"), placed.get("flex-direction"), placed.get("margin")]).toEqual([undefined, undefined, "0"]);
  });

  test("test_the_small_drawing_of_a_vibe_that_counts_stands_with_its_name_and_no_other_row_has_one", () => {
    render(<CompareTable data={three} combine="slowest" tags={tags} />);

    const drawn = rowsOf().map((row) =>
      [...within(row).getByRole("rowheader").querySelectorAll<HTMLElement>("[style*='/art/']")].map((one) => one.style.getPropertyValue("--art")),
    );

    // A row of a vibe is a row of gauges: it is told by the fact its cells cite, and no vibe is named here.
    const ofAVibe = three.rows.map((row) =>
      row.cells.some((cell) => three.facts.find((one) => one.fact_id === cell.fact_id)?.kind === "tag"),
    );
    expect(drawn.map((one) => one.length)).toEqual(ofAVibe.map((is) => (is ? 1 : 0)));
    expect(new Set(ofAVibe)).toEqual(new Set([true, false]));
    for (const one of drawn.flat()) expect(/^url\("\/art\/thing-[a-z-]+\.png"\)$/.test(one)).toBe(true);
    // The drawing is dress: the head of a row is named as it was.
    for (const [at, row] of rowsOf().entries()) expect(labelOf(row).textContent).toBe(three.rows[at]?.label);
  });

  test("test_what_is_drawn_in_a_cell_and_in_the_head_of_a_row_is_drawn_as_on_a_phone_on_every_screen", () => {
    const small = STYLES.filter((rule) => rule.sets.has("--px"));

    // A cell is small, and the head of a row is a narrow column. The cross of the way out
    // stands in a line of words. Each is drawn as small on every screen, by the token of
    // the look and by no length of its own.
    expect(small.map((rule) => [rule.selector, rule.sets.get("--px"), rule.under])).toEqual([
      [".cross", "var(--px-small)", null],
      [".named", "var(--px-ground)", null],
      [".ends", "var(--px-ground)", null],
      [".part", "var(--px-ground)", null],
      [".placed", "var(--px-ground)", null],
    ]);
  });
});

describe("the style sheet of the comparison", () => {
  const CSS = readFileSync(path.join(__dirname, "CompareTable.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

  test("test_every_colour_a_face_and_a_size_is_a_token_and_nothing_is_dimmed_or_moves", () => {
    expect(CSS.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(CSS.match(/url\([^)]*\)/g) ?? []).toEqual([]);
    const faces = STYLES.flatMap((rule) =>
      [...rule.sets].filter(([property]) => property === "font" || property === "font-family").map(([, value]) => value),
    );
    expect(faces.length).toBeGreaterThan(3);
    expect(faces.filter((face) => !/var\(--font-(say|name)\)$/.test(face))).toEqual([]);
    const moving = STYLES.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(animation|transition|transform|translate|rotate|scale|zoom|opacity|filter)/.test(property)),
    );
    expect(moving.map((rule) => rule.selector)).toEqual([]);
    expect(STYLES.filter((rule) => /:(hover|focus|focus-within|focus-visible|active)\b/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_what_is_said_of_a_row_in_its_head_is_a_notice_as_a_notice_is_drawn_wherever_one_is_said", () => {
    // Seen side by side: that a vibe counts recorded crime stood in a comparison in quiet
    // words with no band, where a notice of the website stands on cream beside a band of
    // amber. It is drawn as a notice is: cream, its words in ink and in the reading face, a
    // rule of ink at its start and a band of amber inside the rule.
    const mine = new Map(STYLES.filter((rule) => rule.selector === ".caveat" && rule.under === null).flatMap((rule) => [...rule.sets]));

    // Where it stands in the head, and how wide a line of it is, are the head's own to say.
    const laidOut = ["display", "max-width", "margin"];
    expect([...mine].filter(([property]) => !laidOut.includes(property))).toEqual([
      ["padding", "var(--space-1) var(--space-2) var(--space-1) calc(var(--space-3) + var(--px) * 2)"],
      ["border-inline-start", "var(--edge) solid var(--notice-edge)"],
      ["background", "var(--notice-bg)"],
      ["box-shadow", "inset calc(var(--px) * 2) 0 0 var(--notice-mark)"],
      ["color", "var(--notice-text)"],
      ["font", "400 var(--size-small) / var(--leading-text) var(--font-say)"],
    ]);
    // It is a notice: its words are ink, on the cream it brings, and never the quieter colour.
    expect(mine.get("color")).toBe("var(--notice-text)");
    expect(STYLES.filter((rule) => /\.caveat\b/.test(rule.selector) && rule.sets.get("color") === "var(--muted)")).toEqual([]);
    // With forced colours the system's own colours carry its edge, and the band is no second one.
    const forced = STYLES.filter((rule) => /forced-colors/.test(rule.under ?? "") && /\.caveat\b/.test(rule.selector));
    expect(forced.map((rule) => [rule.sets.get("border-inline-start-color"), rule.sets.get("box-shadow")])).toEqual([["CanvasText", "none"]]);
  });

  test("test_nothing_that_holds_words_has_a_height_of_its_own_so_that_text_can_be_made_larger", () => {
    const fixed = STYLES.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(height|max-height|block-size|max-block-size)$/.test(property)),
    );

    // The headings that are kept for a screen reader are cut to a pixel. Nothing that is
    // read has a height, and no drawing of the comparison is sized by its sheet.
    expect(fixed.map((rule) => rule.selector).sort()).toEqual([".head"]);
  });
});
