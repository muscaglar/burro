import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TABLE } from "@/content/map";
import { COMPLETENESS, FILTERED, UNRANKED } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { RankData } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { AreaTable, rowsOf } from "./AreaTable";

const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";

function show(ranking: RankData | null, selectedId: string | null = null) {
  const onSelect = jest.fn();
  const onHover = jest.fn();
  const view = render(
    <AreaTable
      areas={areas}
      scores={ranking?.scores ?? []}
      ranked={ranking?.ranked ?? []}
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

/** What the table says beside a fit that rests on part of what counts, for an area the ranking says it of. */
function basedOn(ranking: RankData, areaId: string): string {
  const area = ranking.ranked.find((one) => one.area_id === areaId);
  if (area === undefined) return "";
  const present = area.contributions.filter((part) => part.present).length;
  return present === area.contributions.length ? "" : ` ${COMPLETENESS.some(present, area.contributions.length)}`;
}

const RANKINGS = ["rank-first", "rank-refined", "rank-nothing-matches", "rank-two-journeys", "rank-nights-out"];

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
        .map((cell) => cell.textContent);

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

    const cells = screen.getAllByRole("cell").map((cell) => cell.textContent);
    expect(cells.filter((text) => text === "None")).toEqual([]);
    expect(cells.filter((text) => text === TABLE.noRank)).toHaveLength(2);
    expect(cells.filter((text) => text === TABLE.noFit)).toHaveLength(2);
  });

  test("test_a_fit_that_rests_on_part_of_what_counts_says_so_beside_the_fit", () => {
    // Seen in a browser: an area ranked first on 4 of the 8 things that count stood in the
    // table with its fit and nothing beside it. The list said it, and the table did not.
    const ranking = recordedAnswer("rank", "rank-first").body.data;
    show(ranking);
    const rowOf = (name: string) =>
      screen.getAllByRole("row").find((row) => within(row).queryByRole("link", { name })) as HTMLElement;

    // Recorded: the area ranked second has a figure for 5 of the 10 things that count.
    expect(nameOf("syn-n0017")).toBe("Otterby Fields");
    expect(within(rowOf("Otterby Fields")).getByText(COMPLETENESS.some(5, 10))).toBeInTheDocument();
    // One that has a figure for everything says nothing more than its fit.
    expect(rowOf("Farrowmere").textContent?.includes("Based on")).toBe(false);
    // The ranking names more areas than it says this of, and the table says that it cannot say.
    expect(ranking.scores.length).toBeGreaterThan(ranking.ranked.length);
    expect(screen.getByText(TABLE.partNote)).toBeInTheDocument();
  });

  test("test_the_table_does_not_say_what_it_cannot_say_of_a_fit_before_a_search", () => {
    show(null);

    expect(screen.queryByText(TABLE.partNote)).toBeNull();
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

  test("test_the_table_has_header_cells_and_no_accessibility_fault", async () => {
    const { container } = show(recordedAnswer("rank", "rank-refined").body.data);

    expect(screen.getAllByRole("columnheader")).toHaveLength(6);
    expect(screen.getAllByRole("rowheader")).toHaveLength(areas.length);
    expect(await faultsIn(container)).toEqual([]);
  });
});
