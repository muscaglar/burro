/**
 * A search that was kept is opened by loading its spec into the search of the tab and
 * ranking it now, as the search of a shared link is. The search that was open is left
 * alone until the ranking has come, and gives way to it whole.
 */

import { recordedAnswer } from "@/lib/api/recorded";
import { LIST_LENGTH, createFlow } from "@/lib/search/flow";
import { initialState, reasonsAreIn } from "@/lib/search/state";
import { createStore, type Held } from "@/lib/search/store";

import { landed, reasonsFor, standInApi, withTheSpecSent, type StandIn } from "../../../test/support/api";
import { OTHER_SPEC, SPEC } from "../../../test/support/account";
import { openKept } from "./open";

const meta = recordedAnswer("get_meta", "meta").body;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data;
const refined = recordedAnswer("rank", "rank-refined").body.data;

function search(api: StandIn): Held {
  const store = createStore(initialState(meta.data, areas));
  return { store, flow: createFlow({ client: api.client, getState: store.getState, dispatch: store.dispatch }) };
}

/** A service that ranks the search that was kept, and gives its reasons. */
function ranks(): StandIn {
  return standInApi()
    .on("interpret", "interpret-first")
    .on("rank", "rank-first")
    .on("explain_top", "explanations-first");
}

describe("opening a search that was kept", () => {
  test("test_what_is_sent_to_be_ranked_is_the_spec_that_was_kept_and_nothing_else", async () => {
    const api = ranks();

    await openKept(search(api), api.client, SPEC);
    await landed();

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toEqual({ spec: SPEC, limit: LIST_LENGTH });
    // It goes to the API as any ranking does, and nothing of it is in an address.
    expect(api.lastCallTo("rank").url).toMatch(/\/v1\/rank$/);
    expect(api.unexpected).toEqual([]);
  });

  test("test_the_search_is_open_on_the_ranking_of_the_spec_that_was_kept", async () => {
    const api = ranks();
    const held = search(api);

    const opened = await openKept(held, api.client, SPEC);

    const state = held.store.getState();
    expect(opened.failure).toBeNull();
    expect(state.phase).toBe("results");
    expect(state.spec).toEqual(first.spec);
    expect(state.specHash).toBe(first.spec_hash);
    expect(state.rankedHash).toBe(first.spec_hash);
    expect(state.ranking?.ranked.map((area) => area.area_id)).toEqual(first.ranked.map((area) => area.area_id));
    // It is a first ranking: nothing is said to have changed place.
    expect([state.moved, state.rankedBefore]).toEqual([null, null]);
    // It is the person's own search, and came from no link.
    expect(state.shared).toBeNull();
    expect(state.untouched).toBe(false);
  });

  test("test_it_takes_the_place_of_the_search_that_was_open_whole", async () => {
    const api = ranks();
    const held = search(api);
    await held.flow.submitText("leafy and quiet, 30 minutes to somewhere");
    await landed();
    const before = held.store.getState();
    expect(before.read).not.toBeNull();

    api.on("rank", withTheSpecSent("rank-refined")).on("explain_top", reasonsFor("rank-refined", "explanations-first"));
    await openKept(held, api.client, OTHER_SPEC);

    const state = held.store.getState();
    // No question, no name and no edit of the search before is carried into it.
    expect(state.read).toBeNull();
    expect(state.refused).toBeNull();
    expect(state.assumed).toEqual({});
    expect(state.kept).toBeNull();
    expect(state.spec).toEqual(OTHER_SPEC);
    expect(state.ranking?.ranked.map((area) => area.area_id)).toEqual(refined.ranked.map((area) => area.area_id));
    expect(state.moved).toBeNull();
    // The search has read nothing of the box, whatever the box holds.
    expect(state.box.read.to).toBe(0);
  });

  test("test_a_search_that_cannot_be_ranked_leaves_the_search_that_was_open_as_it_was", async () => {
    const api = ranks();
    const held = search(api);
    await held.flow.submitText("leafy and quiet, 30 minutes to somewhere");
    await landed();
    const before = held.store.getState();

    api.on("rank", "rank-stale-spec");
    const opened = await openKept(held, api.client, OTHER_SPEC);

    expect(opened.failure).toMatchObject({ kind: "api", status: 422 });
    expect(held.store.getState()).toBe(before);

    api.unreachable("rank");
    expect((await openKept(held, api.client, OTHER_SPEC)).failure).toMatchObject({ kind: "network" });
    expect(held.store.getState()).toBe(before);
  });

  test("test_the_cards_of_the_ranking_come_to_hold_its_reasons_and_the_profiles_of_its_first_areas", async () => {
    const api = ranks();
    const held = search(api);

    const opened = await openKept(held, api.client, SPEC);
    // The search is open before its cards are filled.
    expect(held.store.getState().ranking).not.toBeNull();
    await opened.filled;

    const state = held.store.getState();
    expect(reasonsAreIn(state)).toBe(true);
    expect(api.callsTo("explain_top")).toHaveLength(1);
    expect(api.lastCallTo("explain_top").body).toMatchObject({ spec: first.spec });
    const firstAreas = first.ranked.slice(0, 5).map((area) => area.area_id);
    expect(Object.keys(state.details).sort()).toEqual([...firstAreas].sort());
    // A profile is asked for by the slug of its area, which is no word of a person's.
    expect(api.callsTo("get_area").map((call) => call.path.split("/").pop()).sort()).toEqual(
      areas.filter((area) => firstAreas.includes(area.area_id)).map((area) => area.slug).sort(),
    );
  });

  test("test_reasons_that_could_not_be_had_are_said_not_to_have_come_and_the_search_is_open_all_the_same", async () => {
    const api = ranks().unreachable("explain_top");
    const held = search(api);

    const opened = await openKept(held, api.client, SPEC);
    await opened.filled;

    const state = held.store.getState();
    expect(opened.failure).toBeNull();
    expect(state.ranking).not.toBeNull();
    expect(state.explainFailure).toMatchObject({ hash: first.spec_hash, failure: { kind: "network" } });
  });

  test("test_what_was_on_its_way_for_the_search_before_is_let_go", async () => {
    const api = ranks();
    const held = search(api);
    // A ranking of the search before is on its way, and lands after the kept search is open.
    const late = api.late("rank", "rank-refined", "rank-first");
    const edited = held.flow.rankNow();

    const opened = await openKept(held, api.client, SPEC);
    await opened.filled;
    late.release();
    await edited;
    await landed();

    const state = held.store.getState();
    expect(state.rankedHash).toBe(first.spec_hash);
    expect(state.ranking?.ranked.map((area) => area.area_id)).toEqual(first.ranked.map((area) => area.area_id));
  });

  test("test_where_the_data_has_moved_on_the_form_is_read_again_so_that_the_search_is_drawn_with_its_names", async () => {
    const api = ranks().movedTo("syn-2026-10-01-01");
    const held = search(api);
    expect(held.store.getState().meta.release_id).toBe(meta.data.release_id);

    const opened = await openKept(held, api.client, SPEC);
    await opened.filled;

    const state = held.store.getState();
    expect(state.meta.release_id).toBe("syn-2026-10-01-01");
    expect(state.rankedBy?.release_id).toBe("syn-2026-10-01-01");
    expect(api.callsTo("get_meta").length).toBeGreaterThanOrEqual(1);
    expect(api.callsTo("list_areas")).toHaveLength(1);
  });
});
