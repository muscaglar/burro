import { recordedAnswer } from "@/lib/api/recorded";
import { NO_EDITS } from "@/lib/search/edits";
import { initialState } from "@/lib/search/state";
import { createStore } from "@/lib/search/store";

import { createKept } from "./opened";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const ranked = recordedAnswer("rank", "rank-first").body;

/** A search as the page opens it, and the two things that are done to it here. */
function aSearch() {
  const search = createStore(initialState(meta, areas));
  return {
    search,
    begin: () => search.dispatch({ type: "rank_answered", data: ranked.data, sent: NO_EDITS, meta: ranked.meta }),
    startAgain: () => search.dispatch({ type: "started_again" }),
  };
}

describe("what a person opened and closed of the settings", () => {
  test("test_it_keeps_each_group_a_person_pressed_and_says_nothing_of_one_they_did_not", () => {
    const kept = createKept();

    kept.choose("family:green", true);
    kept.choose("money", false);

    expect([...kept.get()]).toEqual([
      ["family:green", true],
      ["money", false],
    ]);
    expect(kept.get().has("journeys")).toBe(false);
    // A second press is the last word on a group.
    kept.choose("money", true);
    expect(kept.get().get("money")).toBe(true);
  });

  test("test_it_tells_whoever_listens_when_something_changed_and_not_when_nothing_did", () => {
    const kept = createKept();
    const told = jest.fn();
    const stop = kept.subscribe(told);

    kept.choose("money", false);
    kept.choose("money", false);
    expect(told).toHaveBeenCalledTimes(1);

    stop();
    kept.choose("money", true);
    expect(told).toHaveBeenCalledTimes(1);
  });

  test("test_what_it_holds_is_never_changed_under_whoever_reads_it", () => {
    const kept = createKept();
    kept.choose("money", false);
    const read = kept.get();

    kept.choose("journeys", false);

    expect([...read]).toEqual([["money", false]]);
    expect(kept.get()).not.toBe(read);
  });

  test("test_it_forgets_what_was_chosen_once_a_search_that_was_open_is_open_no_longer", () => {
    const kept = createKept();
    const told = jest.fn();
    kept.subscribe(told);

    kept.seen(true);
    kept.choose("brands", true);
    kept.seen(true);
    expect(kept.get().get("brands")).toBe(true);

    kept.seen(false);
    expect([...kept.get()]).toEqual([]);
    expect(told).toHaveBeenCalledTimes(2);
  });

  test("test_what_was_chosen_before_a_search_is_kept_into_the_search", () => {
    const kept = createKept();

    kept.seen(false);
    kept.choose("family:green", true);
    kept.seen(false);
    kept.seen(true);

    expect(kept.get().get("family:green")).toBe(true);
  });

  test("test_it_hears_the_search_itself_so_that_starting_again_is_heard_with_the_settings_off_the_page", () => {
    const kept = createKept();
    const { search, begin, startAgain } = aSearch();
    kept.hear(search);
    kept.choose("family:green", true);

    begin();
    expect(kept.get().get("family:green")).toBe(true);
    kept.choose("brands", true);

    startAgain();
    expect([...kept.get()]).toEqual([]);
  });

  test("test_a_search_that_is_open_when_it_is_first_heard_is_known_to_be_open", () => {
    const kept = createKept();
    const { search, begin, startAgain } = aSearch();
    begin();

    kept.hear(search);
    kept.choose("brands", true);
    startAgain();

    expect([...kept.get()]).toEqual([]);
  });

  test("test_a_search_is_heard_once_however_often_the_settings_are_drawn", () => {
    const kept = createKept();
    const { search } = aSearch();
    const heard = jest.spyOn(search, "subscribe");

    kept.hear(search);
    kept.hear(search);
    kept.hear(search);

    expect(heard).toHaveBeenCalledTimes(1);
  });

  test("test_what_moves_in_a_search_that_stays_open_forgets_nothing", () => {
    const kept = createKept();
    const { search, begin } = aSearch();
    kept.hear(search);
    begin();
    kept.choose("brands", true);

    // A pin is pressed, the settings are opened, another ranking comes.
    search.dispatch({ type: "selected", areaId: areas[0]?.area_id ?? null });
    search.dispatch({ type: "settings_opened", open: true });
    begin();

    expect(kept.get().get("brands")).toBe(true);
  });
});
