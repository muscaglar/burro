import { act, fireEvent, render, screen } from "@testing-library/react";

import { NAMED } from "@/content/area";
import { FIND_AREA, PLACE } from "@/content/search";
import { readRecorded, recordedAnswer, responseFrom } from "@/lib/api/recorded";

import { answersOnTheirWay, LATE_MS, standInApi } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
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

    expect(areaField(FIND_AREA.labelAlone)).toBeInTheDocument();
    expect(screen.getByText(FIND_AREA.hintAlone)).toBeInTheDocument();
    typeIn(FIND_AREA.labelAlone, "alder");
    await wait(WAIT_MS);

    expect(Array.from(areasFound().querySelectorAll("a")).map((link) => link.textContent)).toEqual([
      "Alderwick",
    ]);
    expect(screen.queryAllByRole("option")).toEqual([]);
    expect(screen.getByRole("status")).toHaveTextContent(FIND_AREA.found(0, 1));
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
