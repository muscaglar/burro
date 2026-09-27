import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen } from "@testing-library/react";

import { NAMED } from "@/content/area";
import { FIND_AREA, PLACE } from "@/content/search";
import { readRecorded, recordedAnswer, responseFrom } from "@/lib/api/recorded";

import { answersOnTheirWay, LATE_MS, standInApi } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { PlaceCombobox, WAIT_MS } from "./PlaceCombobox";

const found = recordedAnswer("search_places", "places-search").body.data.places;
const found_areas = recordedAnswer("search_places", "places-search").body.data.areas;

function show(api = standInApi().on("search_places", "places-search"), full: string | null = null) {
  const onPick = jest.fn();
  const view = render(
    <PlaceCombobox
      search={(text, signal) => api.client.searchPlaces({ q: text, limit: 8 }, signal)}
      onPick={onPick}
      full={full}
    />,
  );
  return { api, onPick, ...view };
}

const field = () => screen.getByRole<HTMLInputElement>("combobox", { name: PLACE.label });
const type = (text: string) => fireEvent.input(field(), { target: { value: text } });
/**
 * Moves the clock on, and then lets every answer that is on its way land. The clock is made
 * up, so an answer that is a moment late lands only when the clock is moved on for it.
 */
async function wait(ms: number): Promise<void> {
  await act(() => jest.advanceTimersByTimeAsync(ms));
  for (let turns = 0; answersOnTheirWay() > 0 && turns < 100; turns += 1) {
    await act(() => jest.advanceTimersByTimeAsync(Math.max(LATE_MS, 1)));
  }
}

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

describe("the search for a place", () => {
  test("test_the_search_is_sent_once_250_ms_after_the_last_key", async () => {
    const { api } = show();

    for (const text of ["p", "pe", "pel"]) {
      type(text);
      await wait(WAIT_MS - 1);
    }
    expect(api.calls).toEqual([]);
    await wait(1);

    expect(api.callsTo("search_places")).toHaveLength(1);
    expect(api.lastCallTo("search_places").body).toEqual({ q: "pel", limit: 8 });
    expect(problemsWith("PlaceSearchBody", api.lastCallTo("search_places").body)).toEqual([]);
    expect(WAIT_MS).toBe(250);
  });

  test("test_fewer_than_two_characters_are_not_sent", async () => {
    const { api } = show();

    type("p");
    await wait(WAIT_MS * 4);
    type("  p  ");
    await wait(WAIT_MS * 4);

    expect(api.calls).toEqual([]);
    expect(screen.getByRole("status")).toHaveTextContent("");
  });

  test("test_the_field_takes_no_more_than_the_api_does", () => {
    show();

    expect(field()).toHaveAttribute("maxlength", "80");
  });

  test("test_the_places_found_are_offered_by_name_and_kind", async () => {
    show();

    type("pel");
    await wait(WAIT_MS);

    expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual([
      "Pellam CrossStation",
      "Pellam ExchangeDistrict",
      "Pellam InfirmaryHospital, in Coracle Row",
    ]);
    expect(field()).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("status")).toHaveTextContent(PLACE.found(3));
  });

  test("test_an_answer_to_what_was_typed_before_is_dropped", async () => {
    const api = standInApi();
    const old = api.late("search_places", "places-search", "places-search-one-kind");
    show(api);

    type("pel");
    await wait(WAIT_MS);
    type("school");
    await wait(WAIT_MS);
    expect(api.callsTo("search_places")[0]?.init.signal?.aborted).toBe(true);
    old.release();
    await wait(0);

    expect(screen.getAllByRole("option")[0]).toHaveTextContent("Kindlewharf School of Art");
    expect(screen.getAllByRole("option")).toHaveLength(5);
  });

  test("test_typing_again_ends_the_search_that_was_on_its_way", async () => {
    const api = standInApi().silent("search_places");
    show(api);

    type("pel");
    await wait(WAIT_MS);
    type("pell");

    expect(api.callsTo("search_places")).toHaveLength(1);
    expect(api.lastCallTo("search_places").init.signal?.aborted).toBe(true);
  });

  test("test_picking_a_place_hands_it_over_and_empties_the_field", async () => {
    const { onPick } = show();
    type("pel");
    await wait(WAIT_MS);

    fireEvent.click(screen.getAllByRole("option")[1] as HTMLElement);

    expect(onPick).toHaveBeenCalledWith(found[1]);
    expect(field()).toHaveValue("");
    expect(screen.queryAllByRole("option")).toEqual([]);
    expect(field()).toHaveAttribute("aria-expanded", "false");
  });

  test("test_pressing_an_option_does_not_take_the_focus_from_the_field", async () => {
    show();
    field().focus();
    type("pel");
    await wait(WAIT_MS);

    const pressed = fireEvent.mouseDown(screen.getAllByRole("option")[0] as HTMLElement);

    // The press is stopped from moving the focus, so the list does not close under the pointer.
    expect(pressed).toBe(false);
    expect(field()).toHaveFocus();
  });

  test("test_nothing_found_is_said_in_words", async () => {
    show(standInApi().on("search_places", "places-search-none"));

    type("zzzz");
    await wait(WAIT_MS);

    expect(screen.getByRole("status")).toHaveTextContent(PLACE.none);
    expect(field()).toHaveAttribute("aria-expanded", "false");
  });

  test("test_a_search_that_fails_is_said_in_words_and_typing_again_tries_again", async () => {
    const api = standInApi().unreachable("search_places");
    show(api);

    type("pel");
    await wait(WAIT_MS);
    expect(screen.getByRole("status")).toHaveTextContent(PLACE.failed);

    api.on("search_places", "places-search");
    type("pell");
    await wait(WAIT_MS);
    expect(screen.getAllByRole("option")).toHaveLength(3);
  });

  test("test_enter_asks_again_once_the_search_has_failed_as_the_line_tells_a_person_to", async () => {
    // Seen in a browser: the line said "Please try again in a moment", and with the service
    // back Enter did nothing. Only another letter asked again.
    const api = standInApi().unreachable("search_places");
    const { onPick } = show(api);
    type("pel");
    await wait(WAIT_MS);
    expect(screen.getByRole("status")).toHaveTextContent(PLACE.failed);

    api.on("search_places", "places-search");
    const pressed = fireEvent.keyDown(field(), { key: "Enter" });
    await wait(0);

    // It sends no form and picks nothing: it looks again for what the field holds, at once.
    expect(pressed).toBe(false);
    expect(onPick).not.toHaveBeenCalled();
    expect(api.callsTo("search_places")).toHaveLength(2);
    expect(api.lastCallTo("search_places").body).toEqual({ q: "pel", limit: 8 });
    expect(screen.getAllByRole("option")).toHaveLength(3);
    expect(screen.getByRole("status")).toHaveTextContent(PLACE.found(3));
  });

  test("test_enter_asks_nothing_where_the_search_did_not_fail", async () => {
    const { api } = show();
    type("pel");
    await wait(WAIT_MS);

    fireEvent.keyDown(field(), { key: "Escape" });
    fireEvent.keyDown(field(), { key: "Enter" });
    await wait(WAIT_MS);

    expect(api.callsTo("search_places")).toHaveLength(1);
  });

  test("test_enter_with_nothing_chosen_picks_nothing_and_sends_no_form", async () => {
    const { onPick } = show();
    type("pel");
    await wait(WAIT_MS);

    const pressed = fireEvent.keyDown(field(), { key: "Enter" });

    expect(pressed).toBe(false);
    expect(onPick).not.toHaveBeenCalled();
  });

  test("test_no_option_carries_the_id_of_its_place_in_the_markup", async () => {
    const { container } = show();
    type("pel");
    await wait(WAIT_MS);

    expect(/syn-p\d+/.test(container.innerHTML)).toBe(false);
    expect(screen.getAllByRole("option").map((option) => option.id)).toEqual(
      expect.arrayContaining([expect.stringMatching(/-option-0$/)]),
    );
  });

  test("test_when_no_more_places_can_be_named_the_field_gives_way_to_a_line_saying_so", () => {
    show(standInApi(), PLACE.full(3));

    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent(PLACE.full(3));
  });

  test("test_the_search_is_ended_when_the_page_is_left", async () => {
    const api = standInApi().silent("search_places");
    const { unmount } = show(api);
    type("pel");
    await wait(WAIT_MS);

    unmount();

    expect(api.lastCallTo("search_places").init.signal?.aborted).toBe(true);
  });

  test("test_the_box_that_finds_places_alone_offers_no_area_though_the_api_found_one", async () => {
    show();

    type("pel");
    await wait(WAIT_MS);

    expect(found_areas).toHaveLength(1);
    expect(screen.queryByRole("group", { name: FIND_AREA.title })).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent(PLACE.found(3));
  });

  test("test_the_open_list_has_no_accessibility_fault", async () => {
    const { container } = show();
    type("pel");
    await wait(WAIT_MS);
    fireEvent.keyDown(field(), { key: "ArrowDown" });
    jest.useRealTimers();

    expect(await faultsIn(container)).toEqual([]);
  });
});

function showWithAreas(api = standInApi().on("search_places", "places-search"), noPlaces = false) {
  const onPick = jest.fn();
  const view = render(
    <PlaceCombobox
      search={(text, signal) => api.client.searchPlaces({ q: text, limit: 8 }, signal)}
      onPick={onPick}
      noPlaces={noPlaces}
      areas
    />,
  );
  return { api, onPick, ...view };
}

const areaField = (name: string = FIND_AREA.label) => screen.getByRole<HTMLInputElement>("combobox", { name });
const typeIn = (name: string, text: string) => fireEvent.input(areaField(name), { target: { value: text } });
const areasFound = () => screen.getByRole("group", { name: FIND_AREA.title });
/** The field where it finds areas alone: a plain field, which opens no list. */
const fieldAlone = () => screen.getByRole<HTMLInputElement>("textbox", { name: FIND_AREA.labelAlone });
const typeAlone = (text: string) => fireEvent.input(fieldAlone(), { target: { value: text } });

describe("the search for an area by its name", () => {
  test("test_every_area_that_bears_the_name_is_a_link_to_its_page_with_its_label_beside_it", async () => {
    showWithAreas();

    typeIn(FIND_AREA.label, "pel");
    await wait(WAIT_MS);

    const links = Array.from(areasFound().querySelectorAll("a"));
    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      ["Pellam Cross", "/synthetic/pellam-cross"],
    ]);
    // The label its publisher gives the area stands beside the name. A person has checked
    // this name, so nothing says it is a draft.
    expect(areasFound()).toHaveTextContent("Quillhaven 018");
    expect(areasFound()).not.toHaveTextContent(NAMED.draft);
    // The places are offered as they were, and the line says how many of each were found.
    expect(screen.getAllByRole("option")).toHaveLength(3);
    expect(screen.getByRole("status")).toHaveTextContent(FIND_AREA.found(3, 1));
    expect(FIND_AREA.found(3, 1)).toBe("3 places found, 1 area found");
  });

  test("test_a_name_no_person_has_checked_says_beside_the_area_that_it_is_a_draft", async () => {
    showWithAreas(standInApi().on("search_places", "places-search-area"));

    typeIn(FIND_AREA.label, "ostrel");
    await wait(WAIT_MS);

    expect(areasFound()).toHaveTextContent(`Ostrel ValeQuillhaven 016${NAMED.between}${NAMED.draft}`);
    // No place bears the name, so no list of places opens.
    expect(screen.queryAllByRole("option")).toEqual([]);
    expect(areaField()).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("status")).toHaveTextContent(FIND_AREA.found(0, 1));
    expect(FIND_AREA.found(0, 1)).toBe("1 area found");
  });

  test("test_an_area_is_no_place_to_reach_so_it_is_never_handed_over_as_one", async () => {
    const { onPick } = showWithAreas(standInApi().on("search_places", "places-search-area"));
    typeIn(FIND_AREA.label, "ostrel");
    await wait(WAIT_MS);

    fireEvent.keyDown(areaField(), { key: "ArrowDown" });
    fireEvent.keyDown(areaField(), { key: "Enter" });

    expect(onPick).not.toHaveBeenCalled();
    expect(areasFound()).toBeInTheDocument();
  });

  test("test_no_page_of_an_area_is_fetched_before_its_link_is_pressed", async () => {
    const { api } = showWithAreas();
    typeIn(FIND_AREA.label, "pel");
    await wait(WAIT_MS);

    // The one call is the search itself: a link to an area asks for nothing until it is pressed.
    expect(api.calls.map((call) => call.operation)).toEqual(["search_places"]);
    for (const link of areasFound().querySelectorAll("a")) expect(link).not.toHaveAttribute("rel", "prefetch");
  });

  test("test_no_area_carries_its_id_in_the_markup_and_what_was_typed_is_in_no_address", async () => {
    const { container } = showWithAreas();
    typeIn(FIND_AREA.label, "pel");
    await wait(WAIT_MS);

    expect(/syn-[np]\d+/.test(container.innerHTML)).toBe(false);
    for (const link of container.querySelectorAll("a")) expect(link.getAttribute("href")).not.toContain("pel?");
    expect(container.innerHTML).not.toContain('value="pel"');
  });

  test("test_where_the_data_names_no_place_the_box_finds_areas_and_says_why_it_finds_no_place", async () => {
    const preview = readRecorded("preview/places-search");
    showWithAreas(
      standInApi().on("search_places", () => responseFrom(preview)),
      true,
    );

    expect(fieldAlone()).toBeInTheDocument();
    expect(screen.getByText(FIND_AREA.hintAlone)).toBeInTheDocument();
    typeAlone("alder");
    await wait(WAIT_MS);

    expect(Array.from(areasFound().querySelectorAll("a")).map((link) => link.textContent)).toEqual([
      "Alderwick",
    ]);
    expect(screen.queryAllByRole("option")).toEqual([]);
    expect(screen.getByRole("status")).toHaveTextContent(FIND_AREA.found(0, 1));
  });

  test("test_a_field_that_finds_areas_alone_is_a_plain_field_and_promises_no_list", async () => {
    // Heard in a browser: "combobox, list", of a field whose list was hidden and empty
    // whatever was typed. The down arrow did nothing, and the area was a link at the next Tab.
    const { container, onPick } = showWithAreas(standInApi().on("search_places", "places-search"), true);

    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.queryByRole("listbox", { hidden: true })).toBeNull();
    for (const promise of ["role", "aria-expanded", "aria-controls", "aria-autocomplete", "aria-activedescendant", "aria-haspopup"]) {
      expect([promise, fieldAlone().hasAttribute(promise)]).toEqual([promise, false]);
    }
    // It is named and described as it was, and keeps nothing of what is typed.
    expect(fieldAlone()).toHaveAccessibleDescription(FIND_AREA.hintAlone);
    expect(fieldAlone()).toHaveAttribute("autocomplete", "off");

    typeAlone("pel");
    await wait(WAIT_MS);

    // The service found three places too. None is offered, and no list is drawn for them.
    expect(screen.queryByRole("listbox", { hidden: true })).toBeNull();
    expect(screen.queryAllByRole("option", { hidden: true })).toEqual([]);
    expect(Array.from(areasFound().querySelectorAll("a")).map((link) => link.textContent)).toEqual(["Pellam Cross"]);
    expect(screen.getByRole("status")).toHaveTextContent(FIND_AREA.found(0, 1));
    // The keys of a list do nothing, and Enter sends no form.
    for (const key of ["ArrowDown", "ArrowUp", "Home", "End"]) expect(fireEvent.keyDown(fieldAlone(), { key })).toBe(true);
    expect(fireEvent.keyDown(fieldAlone(), { key: "Enter" })).toBe(false);
    expect(onPick).not.toHaveBeenCalled();
    jest.useRealTimers();
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_nothing_found_is_said_in_words_of_places_and_of_areas", async () => {
    showWithAreas(standInApi().on("search_places", "places-search-none"));
    typeIn(FIND_AREA.label, "zzzz");
    await wait(WAIT_MS);

    expect(screen.getByRole("status")).toHaveTextContent(FIND_AREA.none);
    expect(screen.queryByRole("group", { name: FIND_AREA.title })).toBeNull();
  });

  test("test_the_areas_found_go_when_the_words_change_and_when_a_place_is_picked", async () => {
    const { onPick } = showWithAreas();
    typeIn(FIND_AREA.label, "pel");
    await wait(WAIT_MS);
    expect(areasFound()).toBeInTheDocument();

    typeIn(FIND_AREA.label, "p");
    expect(screen.queryByRole("group", { name: FIND_AREA.title })).toBeNull();

    typeIn(FIND_AREA.label, "pel");
    await wait(WAIT_MS);
    fireEvent.keyDown(areaField(), { key: "ArrowDown" });
    fireEvent.keyDown(areaField(), { key: "Enter" });
    expect(onPick).toHaveBeenCalledWith(found[0]);
    expect(screen.queryByRole("group", { name: FIND_AREA.title })).toBeNull();
  });

  test("test_the_areas_found_have_no_accessibility_fault", async () => {
    const { container } = showWithAreas();
    typeIn(FIND_AREA.label, "pel");
    await wait(WAIT_MS);
    jest.useRealTimers();

    expect(await faultsIn(container)).toEqual([]);
  });
});

const RULES = rulesOf(readFileSync(path.join(__dirname, "PlaceCombobox.module.css"), "utf8"));
const setsOf = (selector: string, under: string | null = null) =>
  new Map(RULES.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));
const BY_HAND = "@media (hover: hover) and (pointer: fine)";

describe("the place in hand, in a list that scrolls", () => {
  const listbox = () => screen.getByRole("listbox", { hidden: true });

  /** A page that draws nothing measures nothing: the list is said to show so much, and each place to be so high. */
  function laidOut(shows: number, each: number): void {
    Object.defineProperty(listbox(), "clientHeight", { configurable: true, value: shows });
    screen.getAllByRole("option", { hidden: true }).forEach((one, at) => {
      Object.defineProperty(one, "offsetTop", { configurable: true, value: at * each });
      Object.defineProperty(one, "offsetHeight", { configurable: true, value: each });
    });
  }

  test("test_the_place_in_hand_is_brought_into_sight_in_the_list_by_no_more_than_it_must_be", async () => {
    // Seen in a browser, of eight places in a list that shows five: the keys went on to the
    // sixth, and Enter then added a place nobody could see.
    show();
    type("pel");
    await wait(WAIT_MS);
    // Three places of 44 px in a list that shows 100: the third begins at 88.
    expect(screen.getAllByRole("option")).toHaveLength(3);
    laidOut(100, 44);

    fireEvent.keyDown(field(), { key: "ArrowDown" });
    expect(listbox().scrollTop).toBe(0);
    fireEvent.keyDown(field(), { key: "ArrowDown" });
    expect(listbox().scrollTop).toBe(0);
    fireEvent.keyDown(field(), { key: "ArrowDown" });
    expect(listbox().scrollTop).toBe(32);
    // Up to the second, which is whole in sight: nothing is moved.
    fireEvent.keyDown(field(), { key: "ArrowUp" });
    expect(listbox().scrollTop).toBe(32);
    fireEvent.keyDown(field(), { key: "Home" });
    expect(listbox().scrollTop).toBe(0);
    fireEvent.keyDown(field(), { key: "End" });
    expect(listbox().scrollTop).toBe(32);
    // Round to the first.
    fireEvent.keyDown(field(), { key: "ArrowDown" });
    expect(listbox().scrollTop).toBe(0);
  });

  test("test_a_list_opened_by_a_key_on_its_last_place_shows_that_place", async () => {
    show();
    type("pel");
    await wait(WAIT_MS);
    laidOut(100, 44);
    fireEvent.keyDown(field(), { key: "Escape" });
    expect(listbox()).not.toBeVisible();

    fireEvent.keyDown(field(), { key: "ArrowUp" });

    expect(listbox()).toBeVisible();
    expect(screen.getAllByRole("option").at(-1)).toHaveAttribute("aria-selected", "true");
    expect(listbox().scrollTop).toBe(32);
  });

  test("test_the_list_is_read_from_its_top_when_the_next_answer_comes", async () => {
    show();
    type("pel");
    await wait(WAIT_MS);
    laidOut(100, 44);
    fireEvent.keyDown(field(), { key: "End" });
    expect(listbox().scrollTop).toBe(32);

    type("pell");
    await wait(WAIT_MS);

    expect(screen.getAllByRole("option").length).toBeGreaterThan(0);
    expect(listbox().scrollTop).toBe(0);
  });

  test("test_the_page_is_never_asked_to_bring_a_place_into_sight", async () => {
    // Asked of the browser, the page went with the list: by 44 px a press, where the list
    // stood in the room the page keeps clear at the foot of the window.
    const asked = jest.fn();
    Element.prototype.scrollIntoView = asked;
    try {
      show();
      type("pel");
      await wait(WAIT_MS);
      laidOut(100, 44);

      for (const key of ["ArrowDown", "ArrowDown", "ArrowDown", "End", "Home"]) fireEvent.keyDown(field(), { key });

      expect(asked).not.toHaveBeenCalled();
    } finally {
      delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
    }
  });
});

describe("the field that finds by name, as the look draws it", () => {
  test("test_the_place_the_keys_are_on_is_the_one_in_hand_and_says_so", async () => {
    show();
    type("pel");
    await wait(WAIT_MS);

    fireEvent.keyDown(field(), { key: "ArrowDown" });

    const [first, ...others] = screen.getAllByRole("option");
    expect(first).toHaveAttribute("aria-selected", "true");
    for (const other of others) expect(other).toHaveAttribute("aria-selected", "false");
    expect(field()).toHaveAttribute("aria-activedescendant", first?.id);
    // The focus is on no place of the list: the field says which one the keys are on.
    expect(document.activeElement?.tagName).not.toBe("LI");
  });

  test("test_the_carrot_lies_beside_the_place_in_hand_and_its_room_stands_before_every_one", async () => {
    show();
    type("pel");
    await wait(WAIT_MS);
    const list = screen.getByRole("listbox");

    expect(list.style.getPropertyValue("--carrot")).toBe('url("/art/ui-carrot.png")');
    expect([list.style.getPropertyValue("--carrot-w"), list.style.getPropertyValue("--carrot-h")]).toEqual(["16", "9"]);
    // Its room is the room of every place, always: nothing moves when it comes or goes.
    expect(setsOf(".option").get("padding")).toContain("calc(var(--px) * (var(--carrot-w) + 6))");
    expect(setsOf(".option::before").has("background")).toBe(false);
    expect(setsOf('.option[aria-selected="true"]::before').get("background")).toContain("var(--carrot)");
    expect(setsOf(".option:hover::before", BY_HAND).get("background")).toContain("var(--carrot)");
    // In hand: ink, and its words in the colour that is read on.
    expect([...setsOf('.option[aria-selected="true"]')]).toEqual([
      ["background", "var(--ink)"],
      ["color", "var(--page)"],
    ]);
  });

  test("test_nothing_of_the_field_or_its_list_moves_or_changes_size_under_the_pointer_or_the_focus", () => {
    const keyed = RULES.filter((rule) => /:(hover|focus|active)/.test(rule.selector));

    expect(keyed.map((rule) => [rule.selector, rule.under])).toEqual([
      [".option:hover", BY_HAND],
      [".option:hover::before", BY_HAND],
      [".option:hover .kind", BY_HAND],
    ]);
    expect([...new Set(keyed.flatMap((rule) => [...rule.sets.keys()]))].sort()).toEqual(["background", "color"]);
    // The edge of the field is solid, and quieter than ink until the field is in hand. While
    // its list is open it is ink, and as wide as it was.
    expect([...setsOf('.combobox .field[aria-expanded="true"]')]).toEqual([["border-color", "var(--border)"]]);
    expect(setsOf(".combobox .field").get("border")).toBe("var(--edge) solid var(--muted)");
  });

  test("test_no_edge_of_the_field_or_of_its_list_is_drawn_in_dashes_or_in_dots", () => {
    // A person who walked the website did not know what a dashed edge was for. The field
    // had one, as a line to write on.
    const written = readFileSync(path.join(__dirname, "PlaceCombobox.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

    expect(/dashed|dotted|repeating-linear-gradient/.test(written)).toBe(false);
    expect(RULES.filter((rule) => rule.sets.has("border-style") || rule.sets.has("outline-style")).map((rule) => rule.selector)).toEqual([]);
    expect(RULES.filter((rule) => /transparent/.test(rule.sets.get("border-color") ?? "")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_what_is_said_of_the_field_weighs_more_than_what_the_page_says_of_every_field", () => {
    // Seen in a browser: the edge of the field was whole. The page gives every field an
    // edge of ink by a rule that names the element, which weighed more than a class alone.
    const ofEveryField = rulesOf(readFileSync(path.join(__dirname, "..", "..", "styles", "base.css"), "utf8")).filter(
      (rule) => /^input\b/.test(rule.selector) && rule.sets.has("border"),
    );

    expect(ofEveryField).toHaveLength(1);
    for (const rule of ofEveryField) {
      expect(heavier(weightOf(".combobox .field"), weightOf(rule.selector))).toBe(true);
    }
  });

  test("test_the_list_is_laid_over_what_is_under_it_with_the_hard_shadow_of_the_look", () => {
    const list = setsOf(".list");

    // Opening it moves nothing, as it did.
    expect([list.get("position"), list.get("overflow-y")]).toEqual(["absolute", "auto"]);
    expect([list.get("background"), list.get("border"), list.get("box-shadow")]).toEqual([
      "var(--page)",
      "var(--edge) solid var(--border)",
      "var(--box-shadow)",
    ]);
  });

  test("test_the_field_asks_the_width_of_no_screen_for_it_stands_in_boxes_of_every_width", () => {
    const byTheScreen = RULES.filter((rule) => /@media[^{]*\b(width|height)\b/.test(rule.under ?? ""));

    expect(byTheScreen.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_what_is_typed_and_every_name_is_read_in_the_face_of_sentences", () => {
    const faces = RULES.filter((rule) => rule.sets.has("font") || rule.sets.has("font-family"));

    expect(faces.map((rule) => rule.selector)).toEqual([]);
  });
});
