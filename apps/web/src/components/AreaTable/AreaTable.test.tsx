import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TABLE } from "@/content/map";
import { COMPLETENESS, FILTERED, UNRANKED } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { RankData } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import type { Lens } from "@/lib/vibes";

import { AreaTable, rowsOf } from "./AreaTable";

const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";

function show(ranking: RankData | null, selectedId: string | null = null, lens: Lens | null = null) {
  const onSelect = jest.fn();
  const onHover = jest.fn();
  const view = render(
    <AreaTable
      areas={areas}
      scores={ranking?.scores ?? []}
      lens={lens}
      filtered={ranking?.filtered ?? []}
      unranked={ranking?.unranked ?? []}
      emptySpec={ranking?.empty_spec ?? false}
      searched={ranking !== null}
      selectedId={selectedId}
      onSelect={onSelect}
      onHover={onHover}
    />,
  );
  return { onSelect, onHover, user: userEvent.setup({ delay: null }), ...view };
}

/** What the table says beside a fit that rests on part of what counts. The API says it of every ranked area. */
function basedOn(ranking: RankData, areaId: string): string {
  const score = ranking.scores.find((one) => one.area_id === areaId);
  if (score === undefined || score.present === score.counted) return "";
  return ` ${COMPLETENESS.some(score.present, score.counted)}`;
}

const RANKINGS = ["rank-first", "rank-refined", "rank-nothing-matches", "rank-two-journeys", "rank-nights-out"];

const STYLES = rulesOf(readFileSync(path.join(__dirname, "AreaTable.module.css"), "utf8"));
/** The rules for a class that hold on a narrow screen and not on a wide one. */
const onANarrowScreen = (className: string) =>
  STYLES.filter((rule) => isFor(rule.selector, className) && /max-width:\s*40rem/.test(rule.under ?? ""));
/** What a cell says to a reader: its text, without what is drawn only for the eye. */
function said(cell: Element): string {
  const copy = cell.cloneNode(true) as Element;
  copy.querySelectorAll("[aria-hidden='true']").forEach((drawn) => drawn.remove());
  return copy.textContent ?? "";
}

describe("the table of every area", () => {
  test.each(RANKINGS)("test_everything_the_map_shows_is_in_the_table: %s", (scenario) => {
    const ranking = recordedAnswer("rank", scenario).body.data;
    show(ranking);
    const rowOf = (areaId: string) =>
      screen.getAllByRole("row").find((row) => within(row).queryByRole("link", { name: nameOf(areaId) }));
    const cellsOf = (areaId: string) =>
      within(rowOf(areaId) as HTMLElement)
        .getAllByRole("cell")
        .slice(0, 4)
        .map(said);

    // Every area of the release is there once, whatever became of it.
    expect(screen.getAllByRole("row")).toHaveLength(areas.length + 1);
    ranking.scores.forEach(({ area_id: areaId, score }, at) => {
      expect(cellsOf(areaId)).toEqual([
        String(at + 1),
        "Quillhaven",
        `${Math.floor(score)} of 100${basedOn(ranking, areaId)}`,
        TABLE.ranked,
      ]);
    });
    for (const { area_id: areaId, reason } of ranking.filtered) {
      expect(cellsOf(areaId)).toEqual([TABLE.noRank, "Quillhaven", TABLE.noFit, FILTERED[reason]]);
    }
    for (const { area_id: areaId, reason } of ranking.unranked) {
      expect(cellsOf(areaId)).toEqual([TABLE.noRank, "Quillhaven", TABLE.noFit, UNRANKED[reason]]);
    }
  });

  test("test_an_area_with_no_rank_says_so_in_words_and_never_as_none", () => {
    // Seen in a browser: "None" in the rank and the fit of an area that is not ranked,
    // which reads as something the program left behind.
    show(recordedAnswer("rank", "rank-first").body.data);

    const cells = screen.getAllByRole("cell").map(said);
    expect(cells.filter((text) => text === "None")).toEqual([]);
    // Two areas the data does not rank, and one that too little is known of for this search.
    expect(cells.filter((text) => text === TABLE.noRank)).toHaveLength(3);
    expect(cells.filter((text) => text === TABLE.noFit)).toHaveLength(3);
  });

  test("test_an_area_that_is_not_ranked_says_what_it_has_no_figure_for_by_name", () => {
    // Seen in a browser: every row said "Too little data for what counts in your search",
    // and none said what was missing, though the API says it of every area.
    const ranking = recordedAnswer("rank", "rank-first").body.data;
    const form = recordedAnswer("get_meta", "meta").body.data;
    const lacking = ranking.unranked.filter((one) => one.missing.length > 0);
    expect(lacking.length).toBeGreaterThan(0);

    const rows = rowsOf({ areas, ...ranking, searched: true, meta: form });

    for (const { area_id: areaId, reason, missing } of lacking) {
      const row = rows.find((one) => one.area.area_id === areaId);
      expect(row?.status.startsWith(UNRANKED[reason])).toBe(true);
      for (const component of missing) {
        const [kind, id] = component.split(":", 2);
        const name =
          kind === "feature"
            ? form.features.find((one) => one.feature_id === id)?.label
            : form.tags.find((one) => one.tag_id === id)?.label;
        if (name !== undefined) expect(row?.status.includes(name)).toBe(true);
      }
      expect(row?.status.includes(TABLE.lacks)).toBe(true);
    }
    // Without the names in hand the reason stands alone, as it did.
    const bare = rowsOf({ areas, ...ranking, searched: true });
    expect(bare.find((one) => one.area.area_id === lacking[0]?.area_id)?.status).toBe(
      UNRANKED[lacking[0]?.reason ?? "insufficient_data"],
    );
  });

  test("test_a_fit_that_rests_on_part_of_what_counts_says_so_beside_the_fit", () => {
    // Seen in a browser: an area ranked first on 4 of the 8 things that count stood in the
    // table with its fit and nothing beside it. The list said it, and the table did not.
    const ranking = recordedAnswer("rank", "rank-first").body.data;
    show(ranking);
    const rowOf = (name: string) =>
      screen.getAllByRole("row").find((row) => within(row).queryByRole("link", { name })) as HTMLElement;

    // Recorded: the area ranked sixth has a figure for 9 of the 10 things that count.
    expect(nameOf("syn-n0014")).toBe("Marrowfen");
    expect(within(rowOf("Marrowfen")).getByText(COMPLETENESS.some(9, 10))).toBeInTheDocument();
    // One that has a figure for everything says nothing more than its fit.
    expect(rowOf("Farrowmere").textContent?.includes("Based on")).toBe(false);
  });

  test("test_it_is_said_of_every_ranked_area_and_not_of_the_first_twenty_alone", () => {
    // The list holds twenty. The API says how much a fit rests on of every area it ranks.
    const ranking = recordedAnswer("rank", "rank-first").body.data;
    const beyond = ranking.scores.slice(ranking.ranked.length);
    const partial = { ...ranking, scores: ranking.scores.map((score) => ({ ...score, present: score.counted - 1 })) };
    show(partial);

    expect(beyond.length).toBeGreaterThan(0);
    for (const { area_id: areaId, counted } of beyond) {
      const row = screen.getAllByRole("row").find((one) => within(one).queryByRole("link", { name: nameOf(areaId) }));
      expect(row?.textContent?.includes(COMPLETENESS.some(counted - 1, counted))).toBe(true);
    }
  });

  test("test_where_the_map_is_coloured_by_a_vibe_the_table_says_the_band_of_every_area", () => {
    const meta = recordedAnswer("get_meta", "meta").body.data;
    const bands = recordedAnswer("list_areas", "areas").body.data.bands;
    const tag = meta.tags.find((one) => one.tag_id === "pace");
    const marks = bands.find((one) => one.tag_id === "pace")?.marks;
    if (tag === undefined || marks === undefined) throw new Error("the recording holds no bands for Going out");
    show(null, null, { tag, marks });
    const rowOf = (name: string) =>
      screen.getAllByRole("row").find((row) => within(row).queryByRole("link", { name })) as HTMLElement;

    expect(screen.getByRole("columnheader", { name: "Going out" })).toBeInTheDocument();
    for (const mark of marks) {
      const said = rowOf(nameOf(mark.area_id)).textContent ?? "";
      // An area the vibe cannot place is said to be so, and is never put in the middle.
      expect(said.includes(mark.band === null ? TABLE.notPlaced : `band`)).toBe(true);
    }
    expect(marks.some((mark) => mark.band === null)).toBe(true);
    // A mixed area is said to vary, as its mark on the map cannot say.
    expect(rowOf("Foxholt").textContent).toContain("varies within this area, from band 3 to band 5 of 5");
  });

  test("test_the_rows_are_in_rank_order_and_then_by_name", () => {
    const ranking = recordedAnswer("rank", "rank-refined").body.data;

    const names = rowsOf({ areas, ...ranking, searched: true }).map((row) => row.area.name);

    const ranked = ranking.scores.map((score) => nameOf(score.area_id));
    expect(names.slice(0, ranked.length)).toEqual(ranked);
    expect(names.slice(ranked.length)).toEqual([...names.slice(ranked.length)].sort());
    expect(names).toHaveLength(areas.length);
  });

  test("test_before_a_search_every_area_is_there_by_name_with_a_link_to_its_page", () => {
    show(null);

    expect(screen.getByRole("table", { name: TABLE.captionEmpty })).toBeInTheDocument();
    for (const area of areas) {
      expect(screen.getByRole("link", { name: area.name })).toHaveAttribute("href", `/synthetic/${area.slug}`);
    }
    const rows = screen.getAllByRole("row").slice(1);
    expect(rows.filter((row) => row.textContent?.includes(TABLE.notYet))).toHaveLength(22);
    expect(rows.filter((row) => row.textContent?.includes(UNRANKED.not_rankable))).toHaveLength(2);
  });

  test("test_with_nothing_to_rank_by_no_fit_is_shown", () => {
    show(recordedAnswer("rank", "rank-empty-spec").body.data);

    expect(screen.queryByText(/of 100/)).toBeNull();
    expect(screen.getAllByText(TABLE.ranked)).toHaveLength(22);
  });

  test("test_an_area_can_be_chosen_from_its_row_and_the_chosen_row_says_so", async () => {
    const { user, onSelect } = show(recordedAnswer("rank", "rank-first").body.data, "syn-n0003");

    await user.click(screen.getByRole("button", { name: TABLE.select("Farrowmere") }));

    expect(onSelect).toHaveBeenCalledWith("syn-n0006");
    const chosen = screen.getAllByRole("row").filter((row) => row.getAttribute("aria-current") === "true");
    expect(chosen).toHaveLength(1);
    expect(within(chosen[0] as HTMLElement).getByRole("link")).toHaveTextContent("Cindermoor");
    expect(screen.getByRole("button", { name: TABLE.select("Cindermoor") })).toHaveAttribute("aria-pressed", "true");
  });

  test("test_the_row_under_the_pointer_is_told_to_the_map", async () => {
    const { user, onHover } = show(recordedAnswer("rank", "rank-first").body.data);
    const row = screen.getAllByRole("row")[1] as HTMLElement;

    await user.hover(row);
    await user.unhover(row);

    expect(onHover.mock.calls.map(([areaId]) => areaId)).toEqual(["syn-n0006", null]);
  });

  test("test_the_table_is_stacked_wherever_its_own_box_is_narrow_and_not_only_on_a_narrow_screen", () => {
    // Seen on a desk: beside the list the table was 527 px wide in a box of 440. The last
    // column, with the way to show an area on the map, was out of sight, and nothing said that
    // the box scrolls. How the table is laid out follows the width of its own box.
    const stacked = STYLES.filter((rule) => /max-width:\s*40rem/.test(rule.under ?? ""));
    const box = STYLES.filter((rule) => isFor(rule.selector, "whole") && rule.under === null);

    expect(stacked.length).toBeGreaterThan(5);
    expect(stacked.filter((rule) => !/^@container\b/.test(rule.under ?? "")).map((rule) => rule.selector)).toEqual([]);
    expect(box.map((rule) => rule.sets.get("container-type"))).toEqual(["inline-size"]);
  });

  test("test_on_a_narrow_screen_each_area_is_a_block_so_that_no_figure_is_cut", () => {
    // Seen on a phone: the table was 512 px wide in a box of 358, so the fit read "83 of 10".
    show(recordedAnswer("rank", "rank-first").body.data);
    const table = screen.getByRole("table");
    const columns = screen.getAllByRole("columnheader").map((header) => header.textContent);

    // Each row is laid out as a block, and the table is no wider than the screen.
    expect(onANarrowScreen("table").some((rule) => rule.sets.get("display") === "block")).toBe(true);
    expect(STYLES.filter((rule) => /max-width:\s*40rem/.test(rule.under ?? "") && /\btr\b/.test(rule.selector)).map((rule) => rule.sets.get("display"))).toContain("grid");
    // No figure is kept on one line where there is no room for it.
    expect(onANarrowScreen("number").map((rule) => rule.sets.get("white-space"))).toContain("normal");
    // Stacked, a browser may forget that a table is one. Each part says its role again.
    expect(table).toHaveAttribute("role", "table");
    expect([...table.querySelectorAll("thead, tbody")].map((group) => group.getAttribute("role"))).toEqual([
      "rowgroup",
      "rowgroup",
    ]);
    for (const row of table.querySelectorAll("tr")) expect(row).toHaveAttribute("role", "row");
    for (const cell of table.querySelectorAll("tbody td")) expect(cell).toHaveAttribute("role", "cell");
    for (const cell of table.querySelectorAll("tbody th")) expect(cell).toHaveAttribute("role", "rowheader");
    // Each cell says what it is of, for the eye, because the headings are not drawn when stacked.
    const [, first] = screen.getAllByRole("row");
    const labels = [...(first as HTMLElement).querySelectorAll("td")].map(
      (cell) => cell.querySelector("[aria-hidden='true'][class*='cellLabel']")?.textContent ?? null,
    );
    expect(labels).toEqual([columns[0], columns[2], columns[3], columns[4], null]);
  });

  test("test_the_table_has_header_cells_and_no_accessibility_fault", async () => {
    const { container } = show(recordedAnswer("rank", "rank-refined").body.data);

    expect(screen.getAllByRole("columnheader")).toHaveLength(6);
    expect(screen.getAllByRole("rowheader")).toHaveLength(areas.length);
    expect(await faultsIn(container)).toEqual([]);
  });
});
