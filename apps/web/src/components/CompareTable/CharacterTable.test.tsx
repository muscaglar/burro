import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RESTS_ON } from "@/content/bands";
import { COMPARE_TABLE } from "@/content/compare";
import { CANNOT_PLACE } from "@/content/facts";
import { SOURCE, STRIP } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { CompareData } from "@/lib/api/schema";

import { CRIME_ACCOUNT, crimeVibes } from "@/content/crime";
import { CRIME_CAVEAT } from "@/content/settings";
import { plainly } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { CharacterTable } from "./CharacterTable";

const { tags, features } = recordedAnswer("get_meta", "meta").body.data;
const crime = crimeVibes({ tags, features });
const three: CompareData = recordedAnswer("compare", "compare-three").body.data;
const two: CompareData = recordedAnswer("compare", "compare-two-defaults").body.data;
/** Four areas, of which the last can be placed on one vibe of the fourteen. */
const four: CompareData = recordedAnswer("compare", "compare-two-journeys").body.data;
const LAST = four.areas.length - 1;

const table = () => screen.getByRole("table", { name: COMPARE_TABLE.character.caption });
const rows = () => within(table()).getAllByRole("row").slice(1);
const labelOf = (tagId: string) => tags.find((tag) => tag.tag_id === tagId)?.label ?? "";
/** Which of the five cells of a mark are filled, from the low end to the high end. */
const filled = (cell: HTMLElement) =>
  [...cell.querySelectorAll("[data-on]")].map((one) => one.getAttribute("data-on") === "true");

describe("the character of the areas compared", () => {
  test("test_there_is_one_row_for_each_vibe_the_api_compares_in_the_order_it_gave", () => {
    render(<CharacterTable data={three} tags={tags} />);

    expect(rows().map((row) => within(row).getByRole("rowheader").querySelector("span")?.textContent)).toEqual(
      three.character.map((row) => labelOf(row.tag_id)),
    );
    expect(three.character).toHaveLength(14);
  });

  test("test_there_is_one_column_for_each_area_under_its_name", () => {
    render(<CharacterTable data={three} tags={tags} />);

    const headers = within(table()).getAllByRole("columnheader").map((header) => header.textContent);

    expect(headers).toEqual([COMPARE_TABLE.character.what, ...three.areas.map((area) => area.name)]);
    for (const row of rows()) expect(within(row).getAllByRole("cell")).toHaveLength(three.areas.length);
  });

  test("test_each_area_is_marked_on_the_line_of_each_vibe_and_its_band_is_said_in_words", () => {
    render(<CharacterTable data={two} tags={tags} />);

    two.character.forEach((vibe, at) => {
      const cells = within(rows()[at] as HTMLElement).getAllByRole("cell");
      vibe.marks.forEach((mark, column) => {
        const cell = cells[column] as HTMLElement;
        if (mark.band === null) throw new Error("Both areas are placed on every vibe.");
        expect(cell).toHaveTextContent(STRIP.band(mark.band));
        expect(filled(cell).map((on, band) => (on ? band + 1 : 0)).filter(Boolean)).toEqual([mark.band]);
      });
    });
  });

  test("test_a_scale_names_its_two_ends_and_a_vibe_that_runs_one_way_runs_from_least_to_most", () => {
    render(<CharacterTable data={two} tags={tags} />);

    const header = (label: string) =>
      within(table())
        .getAllByRole("rowheader")
        .find((one) => one.querySelector("span")?.textContent === label);

    expect(header("Going out")).toHaveTextContent(STRIP.from("Calm", "Buzzy"));
    expect(header("Leafy")).toHaveTextContent(STRIP.from(STRIP.least, STRIP.most));
  });

  test("test_an_area_a_vibe_cannot_place_says_so_and_is_never_put_in_the_middle", () => {
    render(<CharacterTable data={four} tags={tags} />);
    const pace = four.character.findIndex((row) => row.tag_id === "pace");

    const cells = within(rows()[pace] as HTMLElement).getAllByRole("cell");

    expect(four.character[pace]?.marks.map((mark) => mark.band)).toEqual([5, 1, 1, null]);
    expect(cells[LAST]).toHaveTextContent(COMPARE_TABLE.character.notPlaced);
    expect(filled(cells[LAST] as HTMLElement)).toEqual([]);
    expect(/band \d/.test(cells[LAST]?.textContent ?? "")).toBe(false);
    expect(cells[1]).toHaveTextContent(STRIP.band(1));
  });

  test("test_an_area_that_cannot_be_placed_says_so_once_with_why_and_not_in_every_row", () => {
    const { container } = render(<CharacterTable data={four} tags={tags} />);
    const last = four.areas[LAST];
    const unplaced = four.character.filter((row) => row.marks[LAST]?.band === null).length;

    // Burro places the last area on one vibe of the fourteen.
    expect(unplaced).toBe(13);
    expect(container.textContent?.split(COMPARE_TABLE.character.unplaced(last?.name ?? "", 13, 14))).toHaveLength(2);
    expect(container.textContent?.split(COMPARE_TABLE.character.unplacedWhy)).toHaveLength(2);
    // It is said over the table, before any row of it.
    const note = screen.getByText(COMPARE_TABLE.character.unplaced(last?.name ?? "", 13, 14));
    expect(note.compareDocumentPosition(table()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // The long line is in no cell. A cell says in two words that the area is not placed.
    expect(table().textContent?.includes(CANNOT_PLACE)).toBe(false);
    const cells = rows().flatMap((row) => within(row).getAllByRole("cell")[LAST] as HTMLElement);
    expect(cells.filter((cell) => cell.textContent?.includes(COMPARE_TABLE.character.notPlaced))).toHaveLength(13);
    // The areas Burro places on every vibe are said nothing of.
    for (const area of four.areas.slice(0, LAST)) expect(container.textContent?.includes(`cannot place ${area.name}`)).toBe(false);
  });

  test("test_with_every_area_placed_on_every_vibe_nothing_is_said_of_placing", () => {
    const { container } = render(<CharacterTable data={two} tags={tags} />);

    expect(container.textContent?.includes("cannot place")).toBe(false);
    expect(container.textContent?.includes(COMPARE_TABLE.character.unplacedWhy)).toBe(false);
  });

  test("test_where_an_area_sits_is_said_in_words_a_person_would_use_beside_the_band", () => {
    render(<CharacterTable data={two} tags={tags} />);

    two.character.forEach((vibe, at) => {
      const tag = tags.find((one) => one.tag_id === vibe.tag_id);
      const cells = within(rows()[at] as HTMLElement).getAllByRole("cell");
      vibe.marks.forEach((mark, column) => {
        if (mark.band === null || tag === undefined) throw new Error("Both areas are placed on every vibe.");
        const words = plainly(tag, { band: mark.band, spread_low: mark.band, spread_high: mark.band });
        expect(cells[column]?.textContent?.includes(words ?? "no words")).toBe(true);
        expect(cells[column]?.textContent?.includes(STRIP.band(mark.band))).toBe(true);
      });
    });
  });

  test("test_what_a_band_rests_on_is_said_in_the_apis_own_clause_where_the_fact_holds_one", () => {
    const clause = "Worked out from 2 of its 3 parts, 75 of 100 by weight.";
    const told: CompareData = {
      ...two,
      facts: two.facts.map((fact) =>
        fact.kind === "tag" && fact.key === "homes" ? { ...fact, slots: { ...fact.slots, share: "75", partly: clause } } : fact,
      ),
    };
    render(<CharacterTable data={told} tags={tags} />);
    const homes = told.character.findIndex((row) => row.tag_id === "homes");

    for (const cell of within(rows()[homes] as HTMLElement).getAllByRole("cell")) {
      expect(cell.textContent?.includes(clause)).toBe(true);
      // The website's own words for it give way to the API's, and it is said once.
      expect([...cell.querySelectorAll("span")].filter((one) => one.textContent === RESTS_ON.short("2", "3"))).toEqual([]);
      expect(cell.textContent?.split("of its 3 parts")).toHaveLength(2);
    }
  });

  test("test_a_band_that_rests_on_part_of_a_recipe_says_so_in_its_cell", () => {
    render(<CharacterTable data={two} tags={tags} />);
    const homes = two.character.findIndex((row) => row.tag_id === "homes");
    const leafy = two.character.findIndex((row) => row.tag_id === "leafy");

    // No release carries private outdoor space, so Homes rests on two parts of three for every area.
    for (const cell of within(rows()[homes] as HTMLElement).getAllByRole("cell")) {
      expect(cell.textContent?.includes(RESTS_ON.short("2", "3"))).toBe(true);
    }
    for (const cell of within(rows()[leafy] as HTMLElement).getAllByRole("cell")) {
      expect(cell.textContent?.includes("of its")).toBe(false);
    }
  });

  test("test_a_mixed_area_is_drawn_as_a_range_and_said_to_vary", () => {
    const mixed: CompareData = {
      ...two,
      character: two.character.map((row) =>
        row.tag_id !== "pace"
          ? row
          : { ...row, marks: row.marks.map((mark, at) => (at === 0 ? { ...mark, band: 4, spread_low: 3, spread_high: 5 } : mark)) },
      ),
    };
    render(<CharacterTable data={mixed} tags={tags} />);
    const pace = mixed.character.findIndex((row) => row.tag_id === "pace");

    const cell = within(rows()[pace] as HTMLElement).getAllByRole("cell")[0] as HTMLElement;

    expect(cell).toHaveTextContent(STRIP.bands(3, 5));
    expect(filled(cell)).toEqual([false, false, true, true, true]);
  });

  test("test_no_vibe_is_shown_as_a_percentage_a_score_or_a_rank", () => {
    render(<CharacterTable data={three} tags={tags} />);

    expect(/%|percent|score|rank/i.test(table().textContent ?? "")).toBe(false);
  });

  test("test_a_vibe_that_cannot_place_an_area_has_nothing_to_press_in_its_cell", () => {
    render(<CharacterTable data={four} tags={tags} />);

    const cells = rows().flatMap((row) => within(row).getAllByRole("cell"));
    const unplaced = cells.filter((cell) => cell.textContent?.includes(COMPARE_TABLE.character.notPlaced));

    expect(unplaced).toHaveLength(13);
    for (const cell of unplaced) expect(within(cell).queryByRole("button")).toBeNull();
  });

  test("test_every_mark_ends_in_its_source_and_its_date", async () => {
    const user = userEvent.setup({ delay: null });
    render(<CharacterTable data={two} tags={tags} />);

    const buttons = within(table()).getAllByRole("button", { name: /^Source for / });

    // One for each area on each vibe it is placed on, and no two of one name.
    expect(buttons).toHaveLength(two.character.length * two.areas.length);
    expect(new Set(buttons.map((button) => button.getAttribute("aria-label"))).size).toBe(buttons.length);
    await user.click(buttons[0] as HTMLElement);
    const mark = two.character[0]?.marks[0];
    const fact = two.facts.find((one) => one.fact_id === mark?.fact_id);
    const cell = (buttons[0] as HTMLElement).closest("td") as HTMLElement;
    expect(within(cell).getByRole("link", { name: fact?.sources[0]?.name })).toHaveAttribute(
      "href",
      `/sources#${fact?.sources[0]?.source_id}`,
    );
    expect(cell).toHaveTextContent(`${SOURCE.dataFrom} ${fact?.as_of}`);
    expect(cell).toHaveTextContent(SOURCE.madeUp);
  });

  test("test_a_mark_whose_fact_did_not_come_is_not_drawn_because_it_would_have_no_source", () => {
    const without: CompareData = { ...two, facts: two.facts.filter((fact) => fact.kind !== "tag") };
    render(<CharacterTable data={without} tags={tags} />);

    for (const row of rows()) {
      for (const cell of within(row).getAllByRole("cell")) {
        expect(filled(cell)).toEqual([]);
        expect(cell).toHaveTextContent(COMPARE_TABLE.noFigure);
      }
    }
  });

  test("test_a_vibe_that_counts_recorded_crime_says_so_in_its_row_with_the_caveat", () => {
    render(<CharacterTable data={two} tags={tags} crime={crime} />);
    const header = (label: string) =>
      within(table())
        .getAllByRole("rowheader")
        .find((one) => one.querySelector("span")?.textContent === label) as HTMLElement;

    expect(header("Gritty")).toHaveTextContent(CRIME_ACCOUNT.counts);
    expect(header("Gritty")).toHaveTextContent("Recorded criminal damage");
    expect(header("Gritty")).toHaveTextContent(CRIME_CAVEAT);
    // No other vibe holds recorded crime, and none says it does.
    expect(table().textContent?.split(CRIME_ACCOUNT.counts)).toHaveLength(2);
    expect(header("Leafy").textContent?.includes(CRIME_CAVEAT)).toBe(false);
  });

  test("test_a_vibe_the_release_does_not_name_has_no_row", () => {
    render(<CharacterTable data={three} tags={tags.filter((tag) => tag.tag_id !== "pace")} />);

    expect(rows()).toHaveLength(13);
    expect(table()).not.toHaveTextContent("Going out");
  });

  test("test_with_no_vibe_to_compare_there_is_no_table", () => {
    const { container } = render(<CharacterTable data={{ ...three, character: [] }} tags={tags} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_every_part_of_the_table_says_its_role_so_that_it_stays_a_table_when_stacked", () => {
    render(<CharacterTable data={three} tags={tags} />);

    expect(table()).toHaveAttribute("role", "table");
    expect([...table().querySelectorAll("thead, tbody")].map((group) => group.getAttribute("role"))).toEqual([
      "rowgroup",
      "rowgroup",
    ]);
    for (const row of table().querySelectorAll("tr")) expect(row).toHaveAttribute("role", "row");
    for (const cell of table().querySelectorAll("td")) expect(cell).toHaveAttribute("role", "cell");
    for (const header of table().querySelectorAll("thead th")) expect(header).toHaveAttribute("role", "columnheader");
    for (const header of table().querySelectorAll("tbody th")) expect(header).toHaveAttribute("role", "rowheader");
  });

  test("test_each_cell_says_whose_it_is_for_the_eye_and_the_column_says_it_to_a_reader", () => {
    render(<CharacterTable data={three} tags={tags} />);

    for (const row of rows()) {
      const whose = [...row.querySelectorAll("td")].map((cell) => cell.querySelector("[aria-hidden='true']")?.textContent);
      expect(whose).toEqual(three.areas.map((area) => area.name));
    }
  });

  test("test_the_table_has_no_accessibility_fault", async () => {
    const { container } = render(<CharacterTable data={three} tags={tags} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
