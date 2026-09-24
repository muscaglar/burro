/**
 * The search page, held to docs/design/web.md section 9: everything works by
 * keyboard, colour is never the only signal, every map has its table, a
 * slider never needs dragging, and each state is said once.
 *
 * axe runs here in jsdom and cannot judge contrast, size or layout. Those
 * are in test/tokens.test.ts and in a browser, by hand.
 */

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";

import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { MAP, TABLE } from "@/content/map";
import {
  APART,
  BREAKDOWN,
  CHIPS,
  COMPLETENESS,
  CONFIDENCE,
  COST,
  JOURNEYS,
  PROMPT,
  RESULTS,
  SEARCH,
  SHELF,
  SOURCE,
  STATUS,
  UNRANKED,
} from "@/content/search";
import { BUDGET, FEATURES, JOURNEY, SETTINGS, SLIDER } from "@/content/settings";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { setOnline } from "../support/api";
import { faultsIn } from "../support/axe";
import { lastMap } from "../support/maplibre";
import {
  areas,
  arrived,
  everyChip,
  firstSearch,
  meta,
  openSearch,
  promptBox,
  removeChip,
  results,
  saidIn,
  search,
  settingsAt,
  settled,
  setWebGL,
  theTable,
  theWholeOfIt,
  workingOf,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const first = recordedAnswer("rank", "rank-first").body.data;
const refined = recordedAnswer("rank", "rank-refined").body.data;
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";
const sentEdits = (body: unknown) => (body as { operations: Operations }).operations;

beforeEach(() => setOnline(true));
afterEach(() => setWebGL(false));

async function searched(api = firstSearch()) {
  const opened = await openSearch(api);
  await search(opened.user);
  return opened;
}

/** Presses Tab until the focus is on the element, and says how many presses it took. */
async function tabTo(user: Awaited<ReturnType<typeof openSearch>>["user"], wanted: () => Element | null) {
  for (let presses = 0; presses < 400; presses += 1) {
    if (document.activeElement !== null && document.activeElement === wanted()) return presses;
    await user.tab();
  }
  throw new Error("Tab never reached it.");
}

describe("the keyboard", () => {
  test("test_a_search_can_be_made_and_refined_by_keyboard_alone", async () => {
    const { user, api } = await openSearch();

    // Make a search: reach the box, type, press Enter.
    await tabTo(user, promptBox);
    await user.keyboard("leafy and quiet{Enter}");
    await settled();
    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);

    // Refine it: open the settings and the group of the journeys, reach a checkbox, press Space.
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await tabTo(user, () => screen.getByRole("button", { name: SETTINGS.title }));
    await user.keyboard("{Enter}");
    await tabTo(user, () => screen.getByRole("button", { name: SETTINGS.journeys }));
    await user.keyboard("{Enter}");
    await tabTo(user, () => screen.queryAllByRole("checkbox", { name: JOURNEY.firm })[0] ?? null);
    await user.keyboard(" ");
    await settled();
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeStrictness("syn-p0021", "hard"));
    // Every area that is still ranked is listed, and no button is left that would show more.
    expect(results()).toHaveLength(refined.ranked.length);
    expect(screen.queryByRole("button", { name: /^Show \d+ more$/ })).toBeNull();

    // Open the working of a result: reach "Show the working", press Enter, close it with Escape.
    const working = () => within(results()[1] as HTMLElement).getByRole("button", { name: /^Show the working: / });
    await tabTo(user, working);
    await user.keyboard("{Enter}");
    expect(working()).toHaveAttribute("aria-expanded", "true");
    await user.keyboard("{Escape}");
    expect(working()).toHaveAttribute("aria-expanded", "false");
    expect(working()).toHaveFocus();

    // Read a source: reach the first "Source" of the first card, open it, close it with Escape.
    const source = () => within(results()[0] as HTMLElement).getAllByRole("button", { name: /^Source/ })[0] ?? null;
    await tabTo(user, source);
    await user.keyboard("{Enter}");
    expect(source()).toHaveAttribute("aria-expanded", "true");
    expect(within(results()[0] as HTMLElement).getByText(SOURCE.madeUp)).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(source()).toHaveAttribute("aria-expanded", "false");
    expect(source()).toHaveFocus();
  });

  test("test_the_rest_of_the_list_can_be_shown_by_keyboard_alone", async () => {
    const { user } = await searched();
    expect(results()).toHaveLength(SHOWN_AT_FIRST);

    // Reach "Show 10 more", press Enter. The focus goes to the list it added to.
    await tabTo(user, () => screen.queryByRole("button", { name: RESULTS.showMore(10) }));
    await user.keyboard("{Enter}");

    expect(results()).toHaveLength(first.ranked.length);
    // The focus goes to the part of the list that the button added to: the rest, from the second.
    expect(screen.getByRole("list", { name: RESULTS.restLabel }) === document.activeElement).toBe(true);
    // The areas that are not ranked open with Enter and close with Escape, which puts the focus back.
    const apart = screen.getByRole("button", { name: APART.title(first.unranked.length) });
    act(() => apart.focus());
    await user.keyboard("{Enter}");
    expect(apart).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("list", { name: APART.label })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(apart).toHaveAttribute("aria-expanded", "false");
    expect(apart).toHaveFocus();
  });

  test("test_a_place_can_be_found_and_picked_by_keyboard_alone", async () => {
    const { user, api } = await openSearch();
    const field = screen.getByRole("combobox", { name: /place you need to reach/i });

    await tabTo(user, () => field);
    await user.keyboard("pel");
    const options = await screen.findAllByRole("option");
    expect(field).toHaveAttribute("aria-expanded", "true");
    expect(options.map((option) => option.textContent)).toEqual([
      "Pellam CrossStation",
      "Pellam ExchangeDistrict",
      "Pellam InfirmaryHospital, in Coracle Row",
    ]);

    await user.keyboard("{ArrowDown}{ArrowDown}");
    expect(field).toHaveAttribute("aria-activedescendant", options[1]?.id);
    expect(options[1]).toHaveAttribute("aria-selected", "true");
    await user.keyboard("{ArrowUp}{ArrowUp}");
    expect(options[2]).toHaveAttribute("aria-selected", "true");
    await user.keyboard("{Home}{Enter}");
    await settled();

    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeAdd("syn-p0012"));
    // The field was for a first search, and has gone with the shelf now that one is open.
    // The focus is on what Burro understood, and never on nothing.
    expect(field).not.toBeInTheDocument();
    expect(document.activeElement).not.toBe(document.body);
    expect(screen.getByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel})$`) })).toHaveFocus();
  });

  test("test_a_place_picked_from_the_settings_leaves_the_focus_in_its_field", async () => {
    const { user, api } = await searched();
    await settingsAt(user, SETTINGS.journeys);
    const field = screen.getByRole("combobox", { name: /place you need to reach/i });

    await user.type(field, "pel");
    await screen.findAllByRole("option");
    await user.keyboard("{Home}{Enter}");
    await settled();

    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeAdd("syn-p0012"));
    expect(field).toHaveValue("");
    expect(field).toHaveFocus();
    expect(field).toHaveAttribute("aria-expanded", "false");
  });

  test("test_a_vibe_added_from_the_shelf_leaves_the_focus_on_what_was_understood", async () => {
    const { user, api } = await openSearch(firstSearch().on("rank", "rank-shelf").on("explain_top", "explanations-shelf"));
    const shelf = within(screen.getByRole("region", { name: SHELF.title }));

    await tabTo(user, () => shelf.getAllByRole("button")[0] ?? null);
    await user.keyboard("{Enter}");
    await tabTo(user, () => screen.queryByRole("button", { name: /^Add to my search/ }));
    await user.keyboard("{Enter}");
    await settled();

    expect(api.lastCallTo("rank").body).toEqual(recordedAnswer("rank", "rank-shelf").request.body);
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(screen.getByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel})$`) })).toHaveFocus();
  });

  test("test_escape_closes_the_list_of_places_and_keeps_what_was_typed", async () => {
    const { user } = await openSearch();
    const field = screen.getByRole("combobox", { name: /place you need to reach/i });

    await user.type(field, "pel");
    await screen.findAllByRole("option");
    await user.keyboard("{Escape}");

    expect(field).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryAllByRole("option")).toEqual([]);
    expect(field).toHaveValue("pel");
  });

  test("test_every_control_can_be_reached_with_tab_and_none_is_taken_out_of_the_order", async () => {
    const { user } = await searched();
    await settingsAt(user, SETTINGS.money, SETTINGS.journeys, ...meta.data.families.map((one) => one.label));
    await theWholeOfIt();

    const controls = [...document.querySelectorAll<HTMLElement>("a[href], button, input, select, textarea")];
    const out = controls.filter((control) => control.tabIndex < 0 || control.hasAttribute("disabled") === false && control.getAttribute("tabindex") === "-1");
    const madeUp = document.querySelectorAll("[role='button'], [role='link'], [onclick]");

    expect(controls.length).toBeGreaterThan(150);
    expect(out).toEqual([]);
    expect([...madeUp]).toEqual([]);
  });

  test("test_the_skip_links_lead_to_the_results_and_past_the_map", async () => {
    await searched();

    const toResults = screen.getByRole("link", { name: SEARCH.skipToResults });
    const pastMap = screen.getByRole("link", { name: SEARCH.skipMap });

    for (const link of [toResults, pastMap]) {
      const target = document.getElementById((link.getAttribute("href") ?? "").slice(1));
      expect(target).not.toBeNull();
      expect(target?.tabIndex).toBe(-1);
      expect(link).toHaveClass("target");
    }
    expect(toResults.getAttribute("href")).toBe("#results");
    expect(document.getElementById("results")).toContainElement(results()[0] as HTMLElement);
    // The link past the map comes before the map, and its target after it.
    const panel = screen.getByRole("region", { name: MAP.label });
    expect(panel.firstElementChild).toBe(pastMap);
    expect(panel.lastElementChild?.id).toBe("after-map");
  });

  test("test_the_list_the_map_and_the_table_are_on_one_page_at_every_width_with_no_tabs", async () => {
    // The answer comes first at every width. Nothing is behind a tab: the map is a strip on a
    // narrow screen, and the table is one press from it.
    const { user } = await searched();

    expect(screen.queryByRole("tablist")).toBeNull();
    expect(screen.queryAllByRole("tab")).toEqual([]);
    expect(screen.getByRole("region", { name: MAP.label })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: RESULTS.listLabel })).toBeInTheDocument();
    const table = screen.getByRole("button", { name: TABLE.title });
    await tabTo(user, () => table);
    await user.keyboard("{Enter}");
    expect(screen.getByRole("table", { name: TABLE.caption })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(table).toHaveFocus();
  });

  test("test_moving_a_control_does_not_move_focus", async () => {
    const { user, api } = await searched();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await settingsAt(user, SETTINGS.journeys, SETTINGS.airAndNoise, "Green");
    const at = window.scrollY;

    const firm = screen.getAllByRole("checkbox", { name: JOURNEY.firm })[0] as HTMLElement;
    await user.click(firm);
    await settled();
    expect(firm).toHaveFocus();

    const air = screen.getByRole("switch", { name: "Cleaner air" });
    await user.click(air);
    await settled();
    expect(air).toHaveFocus();

    // A slider moved with the keyboard keeps the focus when its answer comes.
    const leafy = screen.getByRole("slider", { name: "Leafy" });
    leafy.focus();
    fireEvent.change(leafy, { target: { value: "70" } });
    await settled();
    expect(leafy).toHaveFocus();

    const how = screen.getByRole("radio", { name: "On foot" });
    await user.click(how);
    await settled();
    expect(how).toHaveFocus();
    expect(window.scrollY).toBe(at);
    expect(window.location.href).toBe("http://localhost/");
  });
});

describe("sliders", () => {
  test("test_every_slider_can_be_set_without_dragging", async () => {
    const { user, api } = await searched();
    await settingsAt(
      user,
      SETTINGS.money,
      SETTINGS.journeys,
      ...meta.data.families.map((one) => one.label),
      SETTINGS.airAndNoise,
    );
    const scales = meta.data.tags.filter((tag) => tag.shape === "scale");

    const sliders = screen.getAllByRole("slider");
    expect(sliders.length).toBeGreaterThan(10);
    for (const slider of sliders) {
      const label = slider.getAttribute("aria-label") ?? document.querySelector(`label[for="${slider.id}"]`)?.textContent ?? "";
      const row = within(slider.parentElement as HTMLElement);
      const scale = scales.find((tag) => tag.label === label);
      expect(label).not.toBe("");
      if (scale === undefined) {
        expect(row.getByRole("button", { name: SLIDER.less(label) })).toBeInTheDocument();
        expect(row.getByRole("button", { name: SLIDER.more(label) })).toBeInTheDocument();
        expect(row.getByRole("textbox", { name: SLIDER.number(label) })).toBeInTheDocument();
      } else {
        // A scale has a button at each end, named for the end, that moves it a step that way.
        expect(row.getByRole("button", { name: SLIDER.toward(label, scale.low_end ?? "") })).toBeInTheDocument();
        expect(row.getByRole("button", { name: SLIDER.toward(label, scale.high_end ?? "") })).toBeInTheDocument();
      }
    }
    expect(sliders.filter((slider) => slider.getAttribute("min") === "-100")).toHaveLength(scales.length);

    // With the button.
    api.calls.length = 0;
    await user.click(screen.getByRole("button", { name: SLIDER.less("Leafy") }));
    await waitFor(() => expect(api.callsTo("rank")).toHaveLength(1));
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.tagWeight("leafy", 0.4, "high"));
    await settled();

    // With the number field.
    const field = screen.getByRole("textbox", { name: SLIDER.number("Leafy") });
    await user.clear(field);
    await user.type(field, "73{Enter}");
    await settled();
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.tagWeight("leafy", 0.75, "high"));

    // With the arrow keys.
    const slider = screen.getByRole("slider", { name: "Leafy" });
    slider.focus();
    fireEvent.change(slider, { target: { value: "55" } });
    await waitFor(() =>
      expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.tagWeight("leafy", 0.55, "high")),
    );
    await settled();

    // A scale, with the button at one of its ends.
    api.calls.length = 0;
    await user.click(screen.getByRole("button", { name: SLIDER.toward("Going out", "Calm") }));
    await waitFor(() => expect(api.callsTo("rank")).toHaveLength(1));
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.tagWeight("pace", 0.1, "low"));
    await settled();
  });

  test("test_the_budget_and_the_longest_journey_have_buttons_and_a_field_too", async () => {
    const { user, api } = await searched();
    await settingsAt(user, SETTINGS.money, SETTINGS.journeys);

    await user.click(screen.getByRole("button", { name: BUDGET.more }));
    await settled();
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.budgetStep("up_small"));

    await user.click(screen.getByRole("button", { name: JOURNEY.shorter }));
    await settled();
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeStep("syn-p0021", "down_small"));

    const longest = screen.getByRole("textbox", { name: JOURNEY.longest });
    await user.clear(longest);
    await user.type(longest, "500");
    await user.tab();
    await settled();
    // A journey is kept within what the data holds, so the form never offers what would be refused.
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeMinutes("syn-p0021", 90));
  });
});

describe("target sizes", () => {
  const SIZED = ".target, .target-min";

  function unsized(): string[] {
    const controls = [
      ...document.querySelectorAll<HTMLElement>(
        "button, input, select, textarea, a[href], [role='option'], [role='tab'], [role='switch']",
      ),
    ];
    return controls
      .filter((control) => {
        if (control.matches(SIZED) || control.closest(`label:is(${SIZED})`)) return false;
        // A link in a sentence is sized by its line, as the guidelines allow.
        if (control.tagName === "A" && control.closest("p") !== null) return false;
        // The shell is another part's, and has its own test.
        return control.closest("main") !== null;
      })
      .map((control) => `${control.tagName.toLowerCase()} ${control.textContent?.slice(0, 40) ?? ""}`);
  }

  test("test_every_control_takes_a_target_size", async () => {
    setWebGL(true);
    const { user } = await searched(firstSearch().on("interpret", "interpret-clarify"));
    act(() => lastMap().fire("load"));
    await arrived();
    await settingsAt(
      user,
      SETTINGS.money,
      SETTINGS.journeys,
      ...meta.data.families.map((one) => one.label),
      SETTINGS.airAndNoise,
    );
    await theWholeOfIt();
    await user.click(screen.getAllByRole("button", { name: /^Source/ })[0] as HTMLElement);
    await user.click(within(screen.getByRole("region", { name: CHIPS.label })).getByRole("button", { name: /^Leafy/ }));
    await user.type(screen.getAllByRole("combobox")[0] as HTMLElement, "pel");
    await screen.findAllByRole("option");

    expect(document.querySelectorAll(`main :is(${SIZED})`).length).toBeGreaterThan(200);
    expect(unsized()).toEqual([]);
  });

  test("test_every_control_of_the_page_before_a_search_takes_a_target_size", async () => {
    const { user } = await openSearch();
    const shelf = within(screen.getByRole("region", { name: SHELF.title }));
    await user.click(shelf.getAllByRole("button")[0] as HTMLElement);

    expect(shelf.getAllByRole("button").length).toBeGreaterThan(5);
    expect(unsized()).toEqual([]);
  });

  test("test_every_control_of_what_the_reader_noticed_takes_a_target_size", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-suggest-many"));
    await user.type(promptBox(), "My sister wants pubs");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(screen.getAllByRole("button", { name: /^Skip: / }).length).toBeGreaterThan(3);
    expect(unsized()).toEqual([]);
  });

  test("test_the_controls_of_a_failure_take_a_target_size", async () => {
    const { user, api } = await searched();
    api.on("rank", "error-internal");
    await removeChip(user, "Leafy");
    await screen.findByRole("alert");

    expect(unsized()).toEqual([]);
  });
});

describe("colour is never the only signal", () => {
  test("test_everything_the_map_shows_is_in_the_table", async () => {
    const { user, api } = await searched();
    await theTable(user);
    const table = () => within(screen.getAllByRole("table", { name: TABLE.caption })[0] as HTMLElement);
    const rowOf = (areaId: string) =>
      table()
        .getAllByRole("row")
        .find((row) => within(row).queryByRole("link", { name: nameOf(areaId) })) as HTMLElement;

    first.scores.forEach(({ area_id: areaId, score }, at) => {
      const cells = within(rowOf(areaId)).getAllByRole("cell").map(saidIn);
      // A fit that rests on part of what counts says so beside the fit, as its card does.
      const counts = first.scores.find((one) => one.area_id === areaId);
      const based =
        counts === undefined || counts.present === counts.counted
          ? ""
          : ` ${COMPLETENESS.some(counts.present, counts.counted)}`;
      expect(cells.slice(0, 4)).toEqual([
        String(at + 1),
        "Quillhaven",
        `${Math.floor(score)} of 100${based}`,
        TABLE.ranked,
      ]);
    });
    // An area with no rank says why in words: the data does not rank it, or too little is known of it.
    for (const { area_id: areaId, reason } of first.unranked) {
      expect(rowOf(areaId)).toHaveTextContent(UNRANKED[reason]);
    }
    expect(new Set(first.unranked.map((area) => area.reason))).toEqual(new Set(["not_rankable", "insufficient_data"]));
    expect(table().getAllByRole("row")).toHaveLength(areas.length + 1);

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await removeChip(user, "Leafy");
    await settled();
    for (const { area_id: areaId } of refined.filtered) {
      expect(rowOf(areaId)).toHaveTextContent("A journey is longer than a firm limit");
    }
    // In rank order, and then by name.
    const names = table().getAllByRole("rowheader").map((cell) => cell.textContent);
    const ranked = refined.scores.map((score) => nameOf(score.area_id));
    expect(names.slice(0, ranked.length)).toEqual(ranked);
    expect(names.slice(ranked.length)).toEqual([...names.slice(ranked.length)].sort());
  });

  test("test_rank_and_status_are_in_words_wherever_they_are_in_colour", async () => {
    setWebGL(true);
    const { user, api } = await searched();
    act(() => lastMap().fire("load"));
    await arrived();

    // Rank: a number in the card, in the pin and in the table.
    const card = await workingOf(user, "Farrowmere");
    await everyChip(user);
    expect(within(card as HTMLElement).getByText(RESULTS.rank(1))).toBeInTheDocument();
    expect(within(card as HTMLElement).getByText(`${RESULTS.fitOf(71)}`)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: MAP.pin(1, "Farrowmere", RESULTS.fitOf(71)) })).toBeInTheDocument();
    // Within and over: words.
    expect(within(card as HTMLElement).getByText(JOURNEYS.within)).toBeInTheDocument();
    // Assumed, and flexible or firm: words. In the row a chip says that the rest was assumed,
    // and opened it says which part.
    const chips = screen.getByRole("region", { name: CHIPS.label });
    expect(chips).toHaveTextContent(CHIPS.restAssumed);
    await user.click(within(chips).getByRole("button", { name: /^Cindermoor Works/ }));
    expect(chips).toHaveTextContent(`${CHIPS.flexible} ${CHIPS.assumed}`);
    await user.click(within(chips).getByRole("button", { name: /^Cindermoor Works/ }));
    // Where an area sits on a vibe: a band, in words, on the picture that draws it.
    for (const picture of within(card).getAllByRole("img", { name: /^band/ })) {
      expect(picture.getAttribute("aria-label")).toMatch(/^bands? \d/);
    }
    // Confidence: a word. The pips are hidden from a reader.
    const cost = within(card as HTMLElement).getByRole("heading", { name: COST.title }).parentElement as HTMLElement;
    expect(within(cost).getByText(CONFIDENCE.high, { exact: false })).toBeInTheDocument();
    for (const pips of document.querySelectorAll("[class*='pips']")) {
      expect(pips).toHaveAttribute("aria-hidden", "true");
    }
    // The trade-off is under a heading that says so.
    expect(within(card as HTMLElement).getByRole("heading", { name: RESULTS.tradeOffTitle })).toBeInTheDocument();

    // Chosen: said to a reader on the card, the pin and the table row.
    await user.click(screen.getByRole("button", { name: RESULTS.showOnMap("Farrowmere") }));
    expect(card).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("button", { name: MAP.pin(1, "Farrowmere", RESULTS.fitOf(71)) })).toHaveAttribute(
      "aria-current",
      "true",
    );
    await theTable(user);
    expect(document.querySelectorAll("tr[aria-current='true']").length).toBeGreaterThan(0);

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await removeChip(user, "Leafy");
    await settled();
    expect(screen.getByRole("region", { name: CHIPS.label })).toBeInTheDocument();
  });

  test("test_the_list_and_the_map_are_in_step_in_both_directions", async () => {
    setWebGL(true);
    const { user } = await searched();
    act(() => lastMap().fire("load"));
    await arrived();
    const cards = results();

    // From the list to the map: the card under the pointer or the focus is outlined on the map.
    await user.hover(cards[1] as HTMLElement);
    expect(lastMap().states.get("syn-n0005")).toMatchObject({ hovered: true });
    await user.unhover(cards[1] as HTMLElement);
    expect(lastMap().states.get("syn-n0005")).toMatchObject({ hovered: false });
    act(() => within(cards[0] as HTMLElement).getAllByRole("button")[0]?.focus());
    expect(lastMap().states.get("syn-n0006")).toMatchObject({ hovered: true });

    // From the map to the list: pressing a pin chooses the card, and the focus stays on the
    // pin that was pressed. It is not taken to the card, and it is never left on nothing.
    const pin = screen.getByRole("button", { name: /^Rank 4,/ });
    fireEvent.click(pin);
    expect(cards[3]).toHaveAttribute("aria-current", "true");
    expect(cards.filter((card) => card.hasAttribute("aria-current"))).toHaveLength(1);
    expect(pin).toHaveFocus();
    expect(lastMap().states.get("syn-n0003")).toMatchObject({ selected: true });

    // "Show in the list" gives the card the focus.
    await user.click(screen.getByRole("button", { name: "Show in the list" }));
    expect(cards[3]).toHaveFocus();
  });

  test("test_an_area_chosen_on_the_map_that_is_past_the_first_ten_is_shown_in_the_list", async () => {
    setWebGL(true);
    const { user } = await searched();
    act(() => lastMap().fire("load"));
    await arrived();
    const far = first.ranked[14];
    expect(results()).toHaveLength(SHOWN_AT_FIRST);

    act(() => lastMap().fire("click", { features: [{ id: far?.area_id }] }, "areas-fill"));
    await user.click(screen.getByRole("button", { name: "Show in the list" }));

    expect(results()).toHaveLength(first.ranked.length);
    expect(results()[14]).toHaveAttribute("aria-current", "true");
    expect(results()[14]).toHaveFocus();
  });
});

describe("what is said, and when", () => {
  test("test_each_state_is_announced_once", async () => {
    const api = firstSearch();
    const { user } = await openSearch(api);
    const line = screen.getAllByRole("status").find((one) => one.getAttribute("aria-live") === "polite") as HTMLElement;
    const said: string[] = [];
    const watcher = new MutationObserver(() => {
      const text = line.textContent ?? "";
      if (text !== said[said.length - 1]) said.push(text);
    });
    watcher.observe(line, { childList: true, characterData: true, subtree: true });

    await search(user);
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await removeChip(user, "Leafy");
    await settled();
    api.on("rank", "rank-nothing-matches");
    await removeChip(user, "Quiet streets");
    await settled();
    watcher.disconnect();

    expect(said).toEqual([
      STATUS.reading,
      `${STATUS.ranked(21, "Farrowmere")} ${STATUS.gaveWay}`,
      // Eleven areas went, which moves no other. It is said that they went, and how many of the rest moved.
      expect.stringMatching(
        /^10 areas ranked, 11 fewer than before\. (The rest are in the order they were|\d+ of the rest changed place)\.$/,
      ),
      STATUS.nothingMatches,
    ]);
    // There is one polite line for the state of the search.
    expect(screen.getAllByRole("status").filter((one) => one.getAttribute("aria-live") === "polite")).toHaveLength(1);
  });

  test("test_a_failure_is_an_alert_and_a_notice_is_a_status", async () => {
    const { user, api } = await searched(firstSearch().on("interpret", "interpret-notice"));

    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("status", { name: "About your search" })).toBeInTheDocument();

    api.on("rank", "error-internal");
    await removeChip(user, "Leafy");
    expect(await screen.findAllByRole("alert")).toHaveLength(1);
  });
});

describe("automated checks of each state with everything open", () => {
  test("test_the_results_with_the_settings_a_chip_and_a_source_open_have_no_fault", async () => {
    const { user, container } = await searched();
    await settingsAt(
      user,
      SETTINGS.money,
      SETTINGS.journeys,
      ...meta.data.families.map((one) => one.label),
      SETTINGS.airAndNoise,
      "Recorded crime",
      FEATURES.madeOfName("Going out"),
    );
    await theWholeOfIt();
    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));
    await user.click(within(results()[0] as HTMLElement).getAllByRole("button", { name: /^Source/ })[0] as HTMLElement);
    expect(within(results()[1] as HTMLElement).getByRole("table", { name: BREAKDOWN.caption })).toBeInTheDocument();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_results_as_they_first_stand_have_no_fault", async () => {
    const { container } = await searched();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_before_a_search_with_a_vibe_open_has_no_fault", async () => {
    const { user, container } = await openSearch();
    await user.click(within(screen.getByRole("region", { name: SHELF.title })).getAllByRole("button")[0] as HTMLElement);

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_with_what_the_reader_noticed_has_no_fault", async () => {
    const { user, container } = await openSearch(firstSearch().on("interpret", "interpret-suggest-notice"));
    await user.type(promptBox(), "leafy with lots of students. My street is noisy.");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_with_a_map_and_a_chosen_area_has_no_fault", async () => {
    setWebGL(true);
    const { container } = await searched();
    act(() => lastMap().fire("load"));
    await arrived();
    fireEvent.click(screen.getByRole("button", { name: /^Rank 2,/ }));

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_with_a_question_and_a_list_of_places_open_has_no_fault", async () => {
    const { user, container } = await searched(firstSearch().on("interpret", "interpret-clarify"));
    await user.type(screen.getAllByRole("combobox")[0] as HTMLElement, "pel");
    await screen.findAllByRole("option");
    await user.keyboard("{ArrowDown}");

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_while_it_is_reading_has_no_fault", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user, container } = await openSearch(api);
    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
    reading.release();
    await settled();
  });
});
