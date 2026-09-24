import { act, fireEvent, render, screen } from "@testing-library/react";

import { PLACE } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";

import { standInApi } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
import { PlaceCombobox, WAIT_MS } from "./PlaceCombobox";

const found = recordedAnswer("search_places", "places-search").body.data.places;

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
const wait = (ms: number) => act(() => jest.advanceTimersByTimeAsync(ms));

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

  test("test_the_open_list_has_no_accessibility_fault", async () => {
    const { container } = show();
    type("pel");
    await wait(WAIT_MS);
    fireEvent.keyDown(field(), { key: "ArrowDown" });
    jest.useRealTimers();

    expect(await faultsIn(container)).toEqual([]);
  });
});
