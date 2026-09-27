import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { NAMED } from "@/content/area";
import { TABLE } from "@/content/map";
import { COMPLETENESS, FILTERED, STRIP, UNRANKED } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { RankData } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { ROUGH } from "../../../test/support/rough";
import { inWords, type Lens } from "@/lib/vibes";

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
    /** What the row of an area says under the name of the vibe: the cell after its rank and its borough. */
    const under = (name: string) => said(within(rowOf(name)).getAllByRole("cell")[2] as HTMLElement);

    expect(screen.getByRole("columnheader", { name: "Going out" })).toBeInTheDocument();
    expect(marks).toHaveLength(areas.length);
    for (const { area_id: areaId, band, spread_low: low, spread_high: high } of marks) {
      // An area the vibe cannot place is said to be so, and is never put in the middle. Every
      // other says its band, in the words every part of the website says a band in.
      const placed = band === null || low === null || high === null ? TABLE.notPlaced : inWords({ band, spread_low: low, spread_high: high });
      expect([nameOf(areaId), under(nameOf(areaId))]).toEqual([nameOf(areaId), placed]);
    }
    expect(marks.some((mark) => mark.band === null)).toBe(true);
    expect(under(nameOf(marks.find((mark) => mark.band === null)?.area_id ?? ""))).toBe(TABLE.notPlaced);
    expect(marks.some((mark) => mark.band !== null && mark.spread_low === mark.spread_high)).toBe(true);
    // A mixed area is said to vary, as its mark on the map cannot say, between the two bands
    // the service says it spans. The words were "from band 3 to band 5", and "from" and "to"
    // now say which way the bands of a vibe run.
    const mixed = marks.find((mark) => nameOf(mark.area_id) === "Foxholt");
    expect([mixed?.band, mixed?.spread_low, mixed?.spread_high]).toEqual([4, 3, 5]);
    expect(under("Foxholt")).toBe("varies within this area, between band 3 and band 5 of 5");
    expect(under("Foxholt")).toBe(STRIP.bands(3, 5));
  });

  test("test_coloured_by_a_vibe_the_service_calls_a_rough_guide_the_table_names_it_as_any_other_and_nothing_says_that_it_is_one", () => {
    // The founder, who had walked the website twice: "remove the concept of rough guide, we
    // don't want to pass this on to a user". The table named such a vibe over its column
    // with its label. It names it by its name alone, and is handed nothing of what a
    // service says of it: so it is held to write neither the label a service gave such a
    // vibe nor the sentence that said why.
    const meta = recordedAnswer("get_meta", "meta").body.data;
    const bands = recordedAnswer("list_areas", "areas").body.data.bands;
    const tag = meta.tags.find((one) => one.tag_id === ROUGH.tag_id);
    const marks = bands.find((one) => one.tag_id === ROUGH.tag_id)?.marks;
    if (tag === undefined || marks === undefined) throw new Error("the recording holds no bands for the vibe the service holds less sure");
    const { container } = show(null, null, { tag, marks });

    expect(tag.sureness).toBe("rough_guide");
    const column = screen.getByRole("columnheader", { name: tag.label });
    expect(column.textContent).toBe(tag.label);
    expect(column.children).toHaveLength(0);
    const heard = [...container.querySelectorAll("*")].flatMap((part) =>
      ["aria-label", "aria-description", "title", "alt"].flatMap((name) => part.getAttribute(name) ?? []),
    );
    const all = [container.textContent ?? "", ...heard].join("\n");
    expect(container.querySelector("[data-rough-guide]")).toBeNull();
    expect(all.includes(ROUGH.label)).toBe(false);
    expect(all.includes(ROUGH.why)).toBe(false);
    expect(/rough guide|less sure/i.test(all)).toBe(false);
    // Every area says where it sits on it all the same, as it does of any vibe.
    const placed = screen
      .getAllByRole("row")
      .slice(1)
      .map((row) => said(within(row).getAllByRole("cell")[2] as HTMLElement));
    expect(placed).toHaveLength(areas.length);
    expect(placed.filter((words) => words !== TABLE.notPlaced && !/^(band \d of 5|varies within this area, between band \d and band \d of 5)$/.test(words))).toEqual([]);
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

  test("test_under_the_name_of_an_area_is_the_label_its_publisher_gives_it", () => {
    show(null);

    for (const area of areas) {
      const header = screen.getByRole("link", { name: area.name }).closest("th") as HTMLElement;
      // The name comes first, and is the link. The label is under it, and is no link.
      expect(header.firstElementChild?.tagName).toBe("A");
      expect(header.textContent).toBe(`${area.name}${area.named?.label ?? ""}`);
      expect(header.querySelectorAll("a")).toHaveLength(1);
    }
    // An area that bears no name but its label has nothing under its name.
    expect(areas.filter((area) => area.named === null).map((area) => area.name)).toEqual([
      "Grapnel Dock",
      "Otterby Fields",
    ]);
    // The table says of no name that it is a draft: the card and the page of an area do.
    expect(document.body.textContent?.includes(NAMED.draft)).toBe(false);
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

  test("test_the_name_of_an_area_and_what_a_column_is_of_are_set_in_the_face_of_names", () => {
    const NAME = "400 var(--name-1) / 1 var(--font-name)";
    const fontOf = (selector: string) =>
      STYLES.filter((rule) => rule.selector === selector && rule.under === null).map((rule) => [rule.sets.get("font"), rule.sets.get("font-synthesis")]);

    // The name of an area, the head of a column, and what a cell is of where the rows are stacked.
    for (const selector of [".link", ".head th", ".cellLabel"]) expect([selector, fontOf(selector)]).toEqual([selector, [[NAME, "none"]]]);
    // A figure is read, and a sentence is: neither is set in the face of names.
    for (const selector of [".number", ".based", ".label"]) {
      expect(STYLES.filter((rule) => rule.selector === selector).some((rule) => /font-name/.test(rule.sets.get("font") ?? ""))).toBe(false);
    }
  });

  test("test_the_name_of_an_area_leads_to_its_page_and_is_drawn_as_a_result_draws_the_name_of_its_area", () => {
    // Seen side by side, on one page: the name of a result in ink with a hard line under it,
    // and the names of the table in cobalt with a soft one.
    const result = rulesOf(readFileSync(path.join(__dirname, "..", "ResultList", "ResultList.module.css"), "utf8"));
    const theirs = result.find((rule) => rule.selector === ".toArea" && rule.under === null);
    const mine = new Map(STYLES.filter((rule) => rule.selector === ".link" && rule.under === null).flatMap((rule) => [...rule.sets]));

    expect(theirs).toBeDefined();
    for (const [property, value] of theirs?.sets ?? []) expect([property, mine.get(property)]).toEqual([property, value]);
    expect(mine.get("color")).toBe("inherit");
  });

  test("test_the_small_button_of_a_row_is_a_native_button_whose_face_is_drawn_inside_it", () => {
    show(recordedAnswer("rank", "rank-first").body.data, "syn-n0003");
    const chosen = screen.getByRole("button", { name: TABLE.select("Cindermoor") });
    const other = screen.getByRole("button", { name: TABLE.select("Farrowmere") });

    for (const button of [chosen, other]) {
      expect(button.tagName).toBe("BUTTON");
      expect(button).toHaveClass("target-min");
      // What is seen on it is the start of its name.
      expect(button).toHaveTextContent(TABLE.show);
      expect(button.firstElementChild).toHaveClass("face");
      expect(button.querySelectorAll("img, svg")).toHaveLength(0);
    }
    // The button of the area that is chosen is the amber one, and the others are plain.
    expect([chosen, other].map((button) => button.style.getPropertyValue("--art"))).toEqual([
      'url("/art/ui-button-on.png")',
      'url("/art/ui-button.png")',
    ]);
    expect([chosen, other].map((button) => button.style.getPropertyValue("--art-down"))).toEqual([
      'url("/art/ui-button-on-down.png")',
      'url("/art/ui-button-down.png")',
    ]);
    // Nothing is drawn on the button itself, and nothing under a press moves it or what it holds but its words.
    const itself = new Map(STYLES.filter((rule) => rule.selector === ".show").flatMap((rule) => [...rule.sets]));
    expect([itself.get("padding"), itself.get("border"), itself.get("background")]).toEqual(["0", "0", "none"]);
    const pressed = STYLES.filter((rule) => /:active/.test(rule.selector) && !/forced-colors/.test(rule.under ?? ""));
    expect(pressed.map((rule) => [rule.selector, [...rule.sets.keys()], rule.under])).toEqual([
      [".show:active > .face", ["border-image-source"], null],
      [".show:active > .face > .says", ["transform"], "@media (prefers-reduced-motion: no-preference)"],
    ]);
  });

  test("test_the_chosen_row_is_marked_inside_itself_and_takes_the_room_it_took", () => {
    const chosen = STYLES.filter((rule) => /aria-(current|pressed)="true"/.test(rule.selector) && !/forced-colors/.test(rule.under ?? ""));
    /** What sets the room a thing takes. A row that is chosen sets none of them. */
    const ROOM = /^(width|height|min-.*|max-.*|padding.*|margin.*|border.*|font.*|line-height|display|position|inset.*|gap|grid.*|flex.*)$/;

    expect(chosen.map((rule) => rule.selector)).toEqual(['.table tr[aria-current="true"]', '.show[aria-pressed="true"] > .face']);
    expect(chosen.flatMap((rule) => [...rule.sets.keys()]).filter((property) => ROOM.test(property))).toEqual([]);
    // An edge of ink, drawn inside the row, and a band of amber at its head: amber is not told from the page without it.
    const row = chosen[0]?.sets;
    expect([row?.get("outline"), row?.get("outline-offset")]).toEqual([
      "var(--focus-ring) solid var(--map-line)",
      "calc(-1 * var(--focus-ring))",
    ]);
    expect(row?.get("box-shadow")).toMatch(/^inset .+ var\(--chosen\)$/);
    // Every row keeps the room of the band, so that a row does not move when it is chosen.
    const head = STYLES.filter((rule) => /:first-child$/.test(rule.selector) && rule.under === null);
    expect(head.map((rule) => rule.sets.get("padding-inline-start"))).toEqual(["var(--space-3)", "var(--space-3)"]);
  });

  test("test_the_style_sheet_names_no_colour_no_face_and_no_picture_of_its_own", () => {
    const written = readFileSync(path.join(__dirname, "AreaTable.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

    expect(written.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(written.match(/url\(/g) ?? []).toEqual([]);
    expect(written.match(/font(-family)?:[^;]*["'][^;]*;/g) ?? []).toEqual([]);
  });

  test("test_the_table_has_header_cells_and_no_accessibility_fault", async () => {
    const { container } = show(recordedAnswer("rank", "rank-refined").body.data);

    expect(screen.getAllByRole("columnheader")).toHaveLength(6);
    expect(screen.getAllByRole("rowheader")).toHaveLength(areas.length);
    expect(await faultsIn(container)).toEqual([]);
  });
});
