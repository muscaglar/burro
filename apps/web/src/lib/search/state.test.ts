import { recordedAnswer } from "@/lib/api/recorded";
import type { Failure } from "@/lib/api/failure";
import type { BudgetEdit, Operations } from "@/lib/api/schema";

import { edits, merged, NO_EDITS } from "./edits";
import { refusals, refusedByPart } from "./refusals";
import { leftOutOf } from "./said";
import { NO_BOX, type Change } from "./mark";
import {
  changedTheSearch,
  failureOfTheCards,
  gaveWayBetween,
  initialState,
  isBeforeASearch,
  movedBetween,
  nothingCameOf,
  readApart,
  reasonsAreIn,
  reasonsFailure,
  reduce,
  wasStopped,
  type SearchEvent,
  type SearchState,
} from "./state";
import { createStore } from "./store";
import {
  A_LIMIT_THE_WORDS_MAKE_FIRM,
  OF_A_WORD_READ_SEVERAL_WAYS,
  restsOn,
  settledOf,
  takenOfAll,
  thingOf,
  WHAT_THE_WORDS_TURN_AWAY,
  WHERE_BURRO_CANNOT_TELL,
  type Worded,
} from "./takes";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const read = recordedAnswer("interpret", "interpret-first").body.data;
const ranked = recordedAnswer("rank", "rank-first").body.data;
const refined = recordedAnswer("rank", "rank-refined").body.data;
const shared = recordedAnswer("get_share", "share-opened").body.data;
const SHARE_ID = "KwduC18xc41r0W0schExDw";

/** What every recording was served by, and the same service once it holds a newer release. */
const A = recordedAnswer("rank", "rank-first").body.meta;
const B = { ...A, release_id: "syn-2026-10-01-01" };

const opened = () => initialState(meta, areas);
const after = (...events: SearchEvent[]) => events.reduce(reduce, opened());
const timeout: Failure = { kind: "timeout", status: null, synthetic: null, requestId: null };

describe("the state of a search", () => {
  test("test_a_search_opens_empty_on_a_renters_defaults_as_the_api_served_them", () => {
    const state = opened();

    expect(state.phase).toBe("empty");
    expect(state.spec).toBe(meta.defaults.rent);
    expect(state.untouched).toBe(true);
    expect(state.pending).toEqual(NO_EDITS);
    expect([state.read, state.ranking, state.failure]).toEqual([null, null, null]);
  });

  test("test_the_state_has_no_field_for_a_sentence", () => {
    const fields = Object.keys(opened());

    expect(fields.filter((field) => /text|prompt|sentence|query|typed|words/i.test(field))).toEqual([]);
  });

  test("test_moving_the_state_on_never_changes_the_state_that_was", () => {
    const before = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: read, meta: A });
    const copy = JSON.stringify(before);

    reduce(before, { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A });
    reduce(before, { type: "queued", operations: edits.tagOn("parks_close_by") });
    reduce(before, { type: "failed", step: "rank", failure: timeout });

    expect(JSON.stringify(before)).toBe(copy);
  });

  test("test_the_spec_changes_only_when_the_api_returns_one", () => {
    const changing = new Set<SearchEvent["type"]>();
    const events: SearchEvent[] = [
      { type: "tenure_swapped", tenure: "buy" },
      { type: "queued", operations: edits.tagOn("leafy") },
      { type: "queued", operations: edits.tagOn("leafy"), gathers: true },
      { type: "gather_started" },
      { type: "gathered", data: refined, sent: NO_EDITS, meta: A },
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: read, meta: A },
      { type: "rank_started", seq: 2 },
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A },
      { type: "share_answered", id: SHARE_ID, data: shared, meta: A },
      { type: "explain_failed", hash: ranked.spec_hash, failure: timeout },
      { type: "settled" },
      { type: "failed", step: "rank", failure: timeout },
      { type: "stopped" },
      // What Burro takes of what it noticed waits to be sent, as the edits of a control do.
      { type: "offers_taken", taken: [{ at: 0, operations: edits.tagOn("leafy"), marks: [], thing: "tag:leafy" }], left: [] },
      { type: "questions_settled", settled: [] },
      { type: "box_changed" },
      { type: "box_edited", change: { at: 0, out: 0, into: 5, holds: 5 } },
      { type: "box_found", holds: 0 },
      { type: "online_changed", online: false },
      { type: "settings_opened", open: true },
      { type: "geometry_failed" },
      { type: "selected", areaId: "syn-n0006" },
      { type: "hovered", areaId: "syn-n0006" },
      { type: "started_again" },
    ];
    for (const event of events) {
      const second = recordedAnswer("interpret", "interpret-second-sentence").body.data;
      const before = after({ type: "read_answered", data: second, meta: A });
      // An answer to what was gathered is taken while the second way in gathers, and at no other time.
      const held = { ...before, untouched: event.type === "tenure_swapped", gathering: event.type === "gathered" };
      const next = reduce(held, event);
      if (next.spec !== before.spec) changing.add(event.type);
    }

    // A default the API served is swapped in before anything is asked for, and on starting again.
    expect([...changing].sort()).toEqual(
      ["gathered", "rank_answered", "read_answered", "share_answered", "started_again", "tenure_swapped"].sort(),
    );
  });

  test("test_the_tenure_is_swapped_only_before_anything_is_asked_for", () => {
    const asked = after({ type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A });

    expect(reduce(opened(), { type: "tenure_swapped", tenure: "buy" }).spec).toBe(meta.defaults.buy);
    expect(reduce(asked, { type: "tenure_swapped", tenure: "buy" })).toBe(asked);
  });

  test("test_a_failure_returns_to_the_phase_before_and_keeps_what_was_on_screen", () => {
    const state = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "queued", operations: edits.tagOn("parks_close_by") },
      { type: "rank_started", seq: 2 },
      { type: "failed", step: "rank", failure: timeout },
    );

    expect(state.phase).toBe("results");
    expect(state.ranking?.ranked).toBe(ranked.ranked);
    expect(state.pending).toEqual(edits.tagOn("parks_close_by"));
    expect(state.degraded).toBe(false);
  });

  test("test_only_a_failure_to_read_the_words_leaves_the_form_as_the_way_in", () => {
    const of = (step: "read" | "rank", failure: Failure) =>
      after({ type: "read_started", seq: 1 }, { type: "failed", step, failure }).degraded;
    const refusal = { kind: "api", status: 422, code: "invalid_text" } as unknown as Failure;
    const fault = { kind: "api", status: 500, code: "internal_error" } as unknown as Failure;
    const offline: Failure = { ...timeout, kind: "offline" };

    expect(of("read", timeout)).toBe(true);
    expect(of("read", fault)).toBe(true);
    expect(of("read", refusal)).toBe(false);
    expect(of("read", offline)).toBe(false);
    expect(of("rank", timeout)).toBe(false);
  });

  test("test_the_answers_are_counted_so_that_a_control_knows_to_draw_itself_again", () => {
    const counts = [
      opened(),
      after({ type: "read_answered", data: read, meta: A }),
      after({ type: "read_answered", data: read, meta: A }, { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A }),
      after({ type: "tenure_swapped", tenure: "buy" }),
      after({ type: "queued", operations: edits.tagOn("leafy") }),
      after({ type: "failed", step: "rank", failure: timeout }),
    ].map((state) => state.answers);

    expect(counts).toEqual([0, 1, 2, 1, 0, 0]);
  });

  test("test_starting_again_keeps_the_release_and_forgets_the_search", () => {
    const geometry = recordedAnswer("get_geometry", "geometry").body.data;
    const state = after(
      { type: "geometry_loaded", geometry },
      { type: "read_answered", data: read, meta: A },
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "selected", areaId: "syn-n0006" },
      { type: "started_again" },
    );

    expect(state).toEqual({ ...initialState(meta, areas, geometry), answers: 3 });
  });

  test("test_reading_the_form_again_leaves_the_ranking_on_screen_its_reasons_its_facts_and_its_profiles", () => {
    const explained = recordedAnswer("explain_top", "explanations-first").body.data;
    const profile = recordedAnswer("get_area", "area/farrowmere").body.data;
    // The page was built on an older release. Every answer of the search came from the newer one.
    const before = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: B },
      { type: "explain_answered", data: explained, meta: B },
      { type: "detail_answered", data: profile, meta: B },
    );
    expect(Object.keys(before.facts).length).toBeGreaterThan(50);

    // The form of the newer release comes last, as it may: it is the largest thing asked for.
    const state = reduce(before, { type: "release_changed", meta: { ...meta, release_id: B.release_id }, areas });

    expect(state.meta.release_id).toBe(B.release_id);
    expect(state.explanations).toBe(before.explanations);
    expect(state.facts).toBe(before.facts);
    expect(state.details).toBe(before.details);
    expect(reasonsAreIn(state)).toBe(true);
  });

  test("test_what_is_of_the_old_release_goes_when_a_ranking_of_the_new_one_comes", () => {
    const explained = recordedAnswer("explain_top", "explanations-first").body.data;
    const profile = recordedAnswer("get_area", "area/farrowmere").body.data;
    const before = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: explained, meta: A },
      { type: "detail_answered", data: profile, meta: A },
    );
    expect(reasonsAreIn(before)).toBe(true);

    const state = reduce(before, { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: B });

    // Facts and profiles are of the release that made them, so they go with it.
    expect([state.facts, state.details, state.explanations, state.explainedHash]).toEqual([{}, {}, [], null]);
    expect([state.factsBy, state.detailsBy, state.explainedBy]).toEqual([{}, {}, null]);
    expect(reasonsAreIn(state)).toBe(false);
    expect(state.rankedBy).toEqual({ release_id: B.release_id, engine_version: B.engine_version });
  });

  test("test_a_ranking_of_the_same_release_leaves_the_profiles_and_the_facts_in_hand", () => {
    const profile = recordedAnswer("get_area", "area/farrowmere").body.data;
    const before = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "detail_answered", data: profile, meta: A },
    );

    const state = reduce(before, { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A });

    expect(state.details).toBe(before.details);
    expect(state.facts).toBe(before.facts);
  });

  test("test_a_place_is_named_by_the_answer_that_brought_the_spec_that_names_it", () => {
    const two = recordedAnswer("interpret", "interpret-two-journeys").body.data;
    const names = { "syn-p0019": "Foxholt Market", "syn-p0026": "Wexmoor University" };

    const readTwo = after({ type: "read_answered", data: two, meta: A });
    const then = reduce(readTwo, { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A });

    expect(readTwo.placeNames).toEqual(names);
    // The names are of the places the spec on screen holds, and of no other.
    expect(then.placeNames).toEqual({ "syn-p0021": "Cindermoor Works" });
    expect(after({ type: "share_answered", id: SHARE_ID, data: shared, meta: A }).placeNames).toEqual(
      Object.fromEntries(shared.places.map((place) => [place.place_id, place.name])),
    );
  });

  test("test_the_reasons_are_for_the_spec_their_own_answer_names", () => {
    const explained = recordedAnswer("explain_top", "explanations-first").body.data;

    const state = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: explained, meta: A },
    );

    expect(explained.spec_hash).toBe(ranked.spec_hash);
    expect(state.explainedHash).toBe(explained.spec_hash);
    expect(reasonsAreIn(state)).toBe(true);
  });
});

describe("what the second way in gathers", () => {
  const place = edits.placeAdd("syn-p0021");
  const gathers: SearchEvent = { type: "queued", operations: place, gathers: true };
  const gathered: SearchEvent = { type: "gathered", data: ranked, sent: place, meta: A };

  test("test_what_is_chosen_there_is_gathered_while_no_search_is_open_and_at_no_other_time", () => {
    expect(opened().gathering).toBe(false);
    expect(after(gathers).gathering).toBe(true);
    expect(after(gathers, gathered, gathers).gathering).toBe(true);
    // Renting or buying was chosen first, which swaps a default in and sends nothing.
    expect(after({ type: "tenure_swapped", tenure: "buy" }, gathers).gathering).toBe(true);

    const searched = after({ type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A });
    expect(reduce(searched, gathers).gathering).toBe(false);
    const asked = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: read, meta: A });
    expect(reduce(asked, gathers).gathering).toBe(false);
    const waited = after({ type: "rank_started", seq: 1 });
    expect(reduce(waited, gathers).gathering).toBe(false);
  });

  test("test_the_answer_brings_the_spec_and_the_names_of_its_places_and_no_ranking", () => {
    const state = after(gathers, gathered);

    expect(state.spec).toBe(ranked.spec);
    expect(state.specHash).toBe(ranked.spec_hash);
    expect(state.placeNames).toEqual({ "syn-p0021": "Cindermoor Works" });
    expect(state.pending).toEqual(NO_EDITS);
    expect([state.ranking, state.rankedHash, state.rankedBy, state.read]).toEqual([null, null, null, null]);
    expect(state.phase).toBe("empty");
    expect(state.untouched).toBe(false);
    expect(state.answers).toBe(opened().answers + 1);
    expect(isBeforeASearch(state)).toBe(true);
  });

  test("test_an_answer_that_comes_once_a_search_was_made_changes_nothing", () => {
    // A sentence was sent while what was chosen was on its way: its answer is what stands.
    const made = after(gathers, { type: "read_started", seq: 1 });

    expect(reduce(made, gathered)).toBe(made);
  });

  test("test_whatever_makes_a_search_ends_it", () => {
    const held = after(gathers, gathered);
    const ends: SearchEvent[] = [
      { type: "read_started", seq: 1 },
      { type: "rank_started", seq: 1 },
      { type: "queued", operations: edits.tagOn("parks_close_by") },
      { type: "share_answered", id: SHARE_ID, data: shared, meta: A },
      { type: "started_again" },
    ];

    expect(held.gathering).toBe(true);
    for (const event of ends) expect([event.type, reduce(held, event).gathering]).toEqual([event.type, false]);
    // What is chosen on the map, and whether the settings are open, make no search.
    const not: SearchEvent[] = [
      { type: "selected", areaId: "syn-n0006" },
      { type: "settings_opened", open: true },
      { type: "online_changed", online: false },
      { type: "failed", step: "rank", failure: timeout },
    ];
    for (const event of not) expect([event.type, reduce(held, event).gathering]).toEqual([event.type, true]);
  });

  test("test_what_is_refused_is_kept_with_the_edits_it_points_into", () => {
    const low = edits.budgetAmount(1);
    const refusing = recordedAnswer("rank", "rank-rejected-edit").body.data;
    const state = after({ type: "queued", operations: low, gathers: true }, { type: "gathered", data: refusing, sent: low, meta: A });

    expect(state.refused).toEqual({ operations: low, rejected: refusing.rejected });
    expect(state.ranking).toBeNull();
  });

  test("test_a_failure_to_send_it_is_said_and_goes_when_it_is_sent_again", () => {
    const failed = after(gathers, { type: "failed", step: "rank", failure: timeout });

    expect(failed.failure).toBe(timeout);
    expect(failed.pending).toEqual(place);
    expect(failed.phase).toBe("empty");
    const again = reduce(failed, { type: "gather_started" });
    expect([again.failure, again.failedStep]).toEqual([null, null]);
    expect(again.pending).toEqual(place);
    // Where nothing failed, sending changes nothing.
    const held = after(gathers);
    expect(reduce(held, { type: "gather_started" })).toBe(held);
  });

  test("test_before_a_search_is_said_of_a_default_and_of_what_was_gathered_and_of_nothing_else", () => {
    expect(isBeforeASearch(opened())).toBe(true);
    expect(isBeforeASearch(after({ type: "tenure_swapped", tenure: "buy" }))).toBe(true);
    expect(isBeforeASearch(after(gathers, gathered))).toBe(true);
    expect(isBeforeASearch(after({ type: "read_started", seq: 1 }))).toBe(false);
    expect(isBeforeASearch(after({ type: "rank_started", seq: 1 }))).toBe(false);
    expect(isBeforeASearch(after({ type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A }))).toBe(false);
    expect(isBeforeASearch(after(gathers, gathered, { type: "rank_started", seq: 1 }))).toBe(false);
  });
});

describe("reasons that come before the ranking they are for", () => {
  const reasons = recordedAnswer("explain_top", "explanations-first").body.data;
  const later = recordedAnswer("explain_top", "explanations-refined").body.data;
  const shown = () =>
    after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, meta: A },
    );

  test("test_the_reasons_on_screen_stay_until_the_ranking_the_new_ones_are_for_has_come", () => {
    const state = reduce(shown(), { type: "explain_answered", data: later, meta: A });

    expect(state.explanations).toBe(reasons.explanations);
    expect(state.explainedHash).toBe(ranked.spec_hash);
    expect(state.explainedHash).toBe(state.rankedHash);
    // What the new reasons cite is kept, so that they have their sources when their turn comes.
    for (const fact of later.facts) expect(state.facts[fact.fact_id]).toBe(fact);
  });

  test("test_the_reasons_that_waited_are_the_rankings_when_it_comes", () => {
    const state = reduce(
      reduce(shown(), { type: "explain_answered", data: later, meta: A }),
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A },
    );

    expect(state.explanations).toBe(later.explanations);
    expect(state.explainedHash).toBe(refined.spec_hash);
    expect(state.explanationsAhead).toBeNull();
  });

  test("test_a_ranking_that_fails_leaves_the_list_the_reasons_it_has", () => {
    const state = reduce(
      reduce(shown(), { type: "explain_answered", data: later, meta: A }),
      { type: "failed", step: "rank", failure: timeout },
    );

    expect(state.explanations).toBe(reasons.explanations);
    expect(state.explainedHash).toBe(state.rankedHash);
  });

  test("test_reasons_that_waited_for_another_ranking_are_not_given_to_this_one", () => {
    const state = reduce(
      reduce(shown(), { type: "explain_answered", data: { ...later, spec_hash: "a".repeat(64) }, meta: A }),
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A },
    );

    expect(state.explanations).toBe(reasons.explanations);
    expect(state.explainedHash).not.toBe(state.rankedHash);
    expect(state.explanationsAhead).toBeNull();
  });

  test("test_the_first_reasons_of_a_search_are_shown_as_soon_as_they_come", () => {
    const state = after({ type: "explain_answered", data: reasons, meta: A });

    expect(state.explanations).toBe(reasons.explanations);
    expect(state.explanationsAhead).toBeNull();
  });

  test("test_reasons_for_the_ranking_on_screen_take_the_place_of_ones_that_were_not", () => {
    const mismatched = after(
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, meta: A },
    );

    const state = reduce(mismatched, { type: "explain_answered", data: later, meta: A });

    expect(state.explanations).toBe(later.explanations);
    expect(state.explainedHash).toBe(state.rankedHash);
  });
});

describe("which release made what is on screen", () => {
  const reasons = recordedAnswer("explain_top", "explanations-first").body.data;
  const profile = recordedAnswer("get_area", "area/farrowmere").body.data;
  const newerEngine = { ...A, engine_version: "9.9.9" };
  const by = ({ release_id, engine_version }: typeof A) => ({ release_id, engine_version });

  test("test_the_release_and_the_engine_of_each_answer_are_kept_with_what_it_brought", () => {
    const state = after(
      { type: "read_answered", data: read, meta: A },
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, meta: A },
      { type: "detail_answered", data: profile, meta: A },
    );

    expect(state.read?.by).toEqual(by(A));
    expect(state.rankedBy).toEqual(by(A));
    expect(state.explainedBy).toEqual(by(A));
    expect(state.detailsBy).toEqual({ [profile.area.area_id]: by(A) });
    expect(Object.keys(state.factsBy).sort()).toEqual(Object.keys(state.facts).sort());
    expect(new Set(Object.values(state.factsBy).map((one) => one.release_id))).toEqual(new Set([A.release_id]));
    // Whether the data is made up is the banner's to say, and is not kept a second time here.
    expect(JSON.stringify([state.rankedBy, state.explainedBy]).includes("synthetic")).toBe(false);
  });

  test("test_a_shared_search_keeps_the_release_that_ranked_it", () => {
    const state = after({ type: "share_answered", id: SHARE_ID, data: shared, meta: B });

    expect(state.rankedBy).toEqual(by(B));
    // Not the release the page was built on, which is another.
    expect(state.meta.release_id).toBe(A.release_id);
  });

  test.each([
    ["another release", B],
    ["another engine", newerEngine],
  ])("test_reasons_made_by_%s_than_the_ranking_are_not_its_reasons", (_, other) => {
    // A hash is of the spec alone, so the two hashes agree whatever release made each answer.
    const state = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, meta: other },
    );

    expect(state.explainedHash).toBe(state.rankedHash);
    expect(reasonsAreIn(state)).toBe(false);
  });

  test("test_reasons_that_came_first_are_not_the_reasons_of_a_ranking_another_release_made", () => {
    const state = after(
      { type: "explain_answered", data: reasons, meta: A },
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: B },
    );

    expect(reasonsAreIn(state)).toBe(false);
    expect(state.explanations).toEqual([]);
  });

  test("test_reasons_of_another_release_wait_and_the_reasons_on_screen_stay", () => {
    const later = recordedAnswer("explain_top", "explanations-refined").body.data;
    const shown = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, meta: A },
    );

    const waiting = reduce(shown, { type: "explain_answered", data: later, meta: B });
    expect(waiting.explanations).toBe(reasons.explanations);
    expect(reasonsAreIn(waiting)).toBe(true);

    // The ranking they are for comes from the same release, and they are its reasons.
    const state = reduce(waiting, { type: "rank_answered", data: refined, sent: NO_EDITS, meta: B });
    expect(state.explanations).toBe(later.explanations);
    expect(state.explainedBy).toEqual(by(B));
    expect(reasonsAreIn(state)).toBe(true);
    for (const fact of later.facts) expect(state.factsBy[fact.fact_id]).toEqual(by(B));
  });

  test("test_reasons_that_waited_are_not_given_to_a_ranking_another_release_made", () => {
    const later = recordedAnswer("explain_top", "explanations-refined").body.data;
    const state = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, meta: A },
      { type: "explain_answered", data: later, meta: A },
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: B },
    );

    expect(reasonsAreIn(state)).toBe(false);
    expect(state.explanationsAhead).toBeNull();
  });

  test("test_a_fact_of_the_rankings_release_is_not_given_up_for_one_of_another", () => {
    const shown = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, meta: A },
    );
    const [cited] = reasons.facts;
    if (cited === undefined) throw new Error("the recording cites no fact");
    const stale = { ...profile, facts: [{ ...cited, as_of: "1999-01" }] };

    // A browser may answer a profile from its own cache for an hour after the release has moved.
    const state = reduce(shown, { type: "detail_answered", data: stale, meta: B });

    expect(state.facts[cited.fact_id]).toBe(cited);
    expect(state.factsBy[cited.fact_id]).toEqual(by(A));
    // The profile itself is kept, with the release that made it.
    expect(state.detailsBy[profile.area.area_id]).toEqual(by(B));
  });
});

describe("reasons and profiles that could not be loaded", () => {
  const fault = {
    kind: "api",
    status: 500,
    code: "internal_error",
    message: "Something went wrong.",
    fields: [],
    meta: A,
    synthetic: true,
    requestId: "5ec56e42",
  } as const satisfies Failure;
  const reasons = recordedAnswer("explain_top", "explanations-first").body.data;
  const profile = recordedAnswer("get_area", "area/farrowmere").body.data;
  const shown = () => after({ type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A });

  test("test_a_failure_of_the_reasons_is_kept_whole_with_its_message_and_the_id_to_quote", () => {
    const state = reduce(shown(), { type: "explain_failed", hash: ranked.spec_hash, failure: fault });

    expect(reasonsFailure(state)).toBe(fault);
    expect(failureOfTheCards(state)).toBe(fault);
    // It is not a failure of the search: the ranking is in, and the page is in no other state.
    expect([state.failure, state.failedStep, state.phase]).toEqual([null, null, "results"]);
  });

  test("test_a_failure_of_the_reasons_of_another_search_is_not_a_failure_of_the_one_on_screen", () => {
    const state = reduce(shown(), { type: "explain_failed", hash: refined.spec_hash, failure: fault });

    expect(reasonsFailure(state)).toBeNull();
    expect(failureOfTheCards(state)).toBeNull();
  });

  test("test_the_failure_goes_when_the_reasons_come", () => {
    const state = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_failed", hash: ranked.spec_hash, failure: fault },
      { type: "explain_answered", data: reasons, meta: A },
    );

    expect(reasonsFailure(state)).toBeNull();
    expect(reasonsAreIn(state)).toBe(true);
  });

  test("test_a_failure_of_a_profile_is_kept_by_its_area_and_goes_when_the_profile_comes", () => {
    const areaId = profile.area.area_id;
    const failed = reduce(shown(), { type: "detail_failed", areaId, failure: timeout });

    expect(failed.detailFailures).toEqual({ [areaId]: timeout });
    expect(failureOfTheCards(failed)).toBe(timeout);

    const state = reduce(failed, { type: "detail_answered", data: profile, meta: A });
    expect(state.detailFailures).toEqual({});
    expect(failureOfTheCards(state)).toBeNull();
  });

  test("test_a_failure_of_the_profile_of_an_area_that_has_no_card_is_not_said", () => {
    const sixth = ranked.ranked[5]?.area_id ?? "";
    const state = reduce(shown(), { type: "detail_failed", areaId: sixth, failure: timeout });

    expect(sixth).not.toBe("");
    expect(failureOfTheCards(state)).toBeNull();
  });

  test("test_the_failure_of_the_search_itself_is_said_before_that_of_its_cards", () => {
    const state = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_failed", hash: ranked.spec_hash, failure: fault },
      { type: "failed", step: "rank", failure: timeout },
    );

    // One failure is shown in one place: the error block says the one that stopped the search.
    expect(state.failure).toBe(timeout);
    expect(failureOfTheCards(state)).toBeNull();
  });

  test("test_reasons_that_could_not_leave_say_that_the_browser_is_offline", () => {
    const offline: Failure = { ...timeout, kind: "offline" };
    const state = reduce(shown(), { type: "explain_failed", hash: ranked.spec_hash, failure: offline });

    expect(state.online).toBe(false);
  });
});

describe("stopping after the words were read", () => {
  const second = recordedAnswer("interpret", "interpret-second-sentence").body.data;
  const reasons = recordedAnswer("explain_top", "explanations-first").body.data;
  const searched = () =>
    after(
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: read, meta: A },
      { type: "rank_started", seq: 1 },
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, meta: A },
    );
  const readAgain = (from: SearchState) =>
    [
      { type: "read_started", seq: 2 },
      { type: "read_answered", data: second, meta: A },
      { type: "rank_started", seq: 2 },
    ].reduce((state, event) => reduce(state, event as SearchEvent), from);

  test("test_stop_puts_the_search_back_as_it_was_when_the_sentence_was_sent", () => {
    const before = searched();
    const reading = readAgain(before);
    // The chips already show the second sentence, over the ranking of the first.
    expect(reading.specHash).toBe(second.spec_hash);
    expect(reading.rankedHash).toBe(ranked.spec_hash);

    const state = reduce(reading, { type: "stopped" });

    expect(state.phase).toBe("results");
    expect(state.spec).toBe(before.spec);
    expect(state.specHash).toBe(state.rankedHash);
    expect(state.read).toBe(before.read);
    expect(state.assumed).toBe(before.assumed);
    expect(state.gaveWay).toBe(before.gaveWay);
    expect(state.ranking).toBe(before.ranking);
    expect(reasonsAreIn(state)).toBe(true);
    // Every control is drawn again, from the spec that was put back.
    expect(state.answers).toBeGreaterThan(reading.answers);
  });

  test("test_reasons_that_came_for_the_ranking_that_was_stopped_are_let_go", () => {
    const later = recordedAnswer("explain_top", "explanations-second-sentence").body.data;
    const reading = reduce(readAgain(searched()), {
      type: "explain_answered",
      data: later,
      meta: A,
    });
    expect(reading.explanationsAhead?.hash).toBe(second.spec_hash);

    expect(reduce(reading, { type: "stopped" }).explanationsAhead).toBeNull();
  });

  test("test_stop_on_a_first_search_goes_back_to_the_defaults_as_served", () => {
    const reading = after(
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: read, meta: A },
      { type: "rank_started", seq: 1 },
    );

    const state = reduce(reading, { type: "stopped" });

    expect(state.phase).toBe("empty");
    expect(state.spec).toBe(meta.defaults.rent);
    expect([state.specHash, state.read, state.ranking]).toEqual([null, null, null]);
    expect(state.untouched).toBe(true);
    expect(state.assumed).toEqual({});
  });

  test("test_a_search_that_was_stopped_says_so_until_it_next_moves", () => {
    // Seen in a browser: after Stop the line under the box said nothing, and nothing was
    // heard. A person who cannot see the page could not tell whether the press had landed.
    const before = searched();
    expect(wasStopped(before)).toBe(false);
    expect(wasStopped(readAgain(before))).toBe(false);

    const state = reduce(readAgain(before), { type: "stopped" });
    expect(wasStopped(state)).toBe(true);
    // What changes nothing of the search leaves it said.
    const still = [
      { type: "selected", areaId: "syn-n0006" },
      { type: "hovered", areaId: "syn-n0006" },
      { type: "box_changed" },
      { type: "settings_opened", open: true },
    ].reduce((held, event) => reduce(held, event as SearchEvent), state);
    expect(wasStopped(still)).toBe(true);
    // The next sentence is read, and the line says that: and then what came of it.
    const reading = reduce(state, { type: "read_started", seq: 3 });
    expect(wasStopped(reading)).toBe(false);
    expect(wasStopped(reduce(reading, { type: "read_answered", data: second, meta: A }))).toBe(false);
    // A control is moved, and its ranking is asked for and comes.
    const moved = reduce(reduce(state, { type: "queued", operations: edits.tagOn("leafy") }), { type: "rank_started", seq: 3 });
    expect(wasStopped(moved)).toBe(false);
    expect(wasStopped(reduce(moved, { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A }))).toBe(false);
    // A search that fails says that, and one that begins again has never been stopped.
    expect(wasStopped(reduce(reading, { type: "failed", step: "read", failure: timeout }))).toBe(false);
    expect(wasStopped(reduce(state, { type: "started_again" }))).toBe(false);
  });

  test("test_a_first_search_that_was_stopped_says_so_though_nothing_of_it_is_left", () => {
    const reading = after({ type: "read_started", seq: 1 });
    const state = reduce(reading, { type: "stopped" });

    expect([state.phase, state.read, state.ranking]).toEqual(["empty", null, null]);
    expect(wasStopped(state)).toBe(true);
    // And where the words had been read, and their ranking was on its way.
    const read_ = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: read, meta: A }, { type: "rank_started", seq: 1 });
    expect(wasStopped(reduce(read_, { type: "stopped" }))).toBe(true);
    // The other kind of search is chosen: the search has moved.
    expect(wasStopped(reduce(state, { type: "tenure_swapped", tenure: "buy" }))).toBe(false);
  });

  test("test_stop_while_the_words_are_still_being_read_changes_nothing_of_the_search", () => {
    const before = searched();
    const state = reduce(reduce(before, { type: "read_started", seq: 2 }), { type: "stopped" });

    expect(state.spec).toBe(before.spec);
    expect(state.read).toBe(before.read);
    expect(state.answers).toBe(before.answers);
    expect(state.phase).toBe("results");
  });

  test("test_an_edit_made_meanwhile_still_waits_after_stop_and_what_it_says_is_no_longer_assumed", () => {
    const before = searched();
    expect(before.assumed["place:syn-p0021"]).toEqual(["mode", "strictness"]);
    const edit = edits.placeStrictness("syn-p0021", "hard");
    const reading = readAgain(reduce(reduce(before, { type: "read_started", seq: 2 }), { type: "queued", operations: edit }));

    const state = reduce(reading, { type: "stopped" });

    expect(state.spec).toBe(before.spec);
    expect(state.pending).toEqual(edit);
    expect(state.assumed["place:syn-p0021"]).toEqual(["mode"]);
    // The control that was moved keeps showing what it was set to: its edit is on its way.
    expect(state.answers).toBe(reading.answers);
  });

  test("test_a_second_sentence_sent_before_the_first_is_ranked_is_undone_with_it", () => {
    const before = searched();
    const twice = readAgain(readAgain(before));

    expect(reduce(twice, { type: "stopped" }).spec).toBe(before.spec);
  });

  test("test_a_sentence_whose_ranking_failed_is_undone_by_stop_on_the_next_one", () => {
    const before = searched();
    const failed = reduce(readAgain(before), { type: "failed", step: "rank", failure: timeout });
    // The failure is on screen, with the new spec over the old ranking, and says "not updated".
    expect(failed.specHash).not.toBe(failed.rankedHash);

    const state = reduce(readAgain(failed), { type: "stopped" });

    // Stop takes the failure line away, so it must not leave the two apart in silence.
    expect(state.failure).toBeNull();
    expect(state.specHash).toBe(state.rankedHash);
  });

  test("test_words_that_could_not_be_read_leave_nothing_to_put_back", () => {
    const failed = after({ type: "read_started", seq: 1 }, { type: "failed", step: "read", failure: timeout });
    expect(failed.kept).toBeNull();

    // The person chooses to buy, which swaps the default in. That is the search a later Stop goes back to.
    const swapped = reduce(failed, { type: "tenure_swapped", tenure: "buy" });
    const state = reduce(
      [
        { type: "read_started", seq: 2 },
        { type: "read_answered", data: read, meta: A },
        { type: "rank_started", seq: 2 },
      ].reduce((held, event) => reduce(held, event as SearchEvent), swapped),
      { type: "stopped" },
    );

    expect(state.spec).toBe(meta.defaults.buy);
  });

  test("test_once_the_ranking_is_in_there_is_nothing_to_put_back", () => {
    const ranked2 = recordedAnswer("rank", "rank-second-sentence").body.data;
    const done = reduce(readAgain(searched()), { type: "rank_answered", data: ranked2, sent: NO_EDITS, meta: A });

    const state = reduce(done, { type: "stopped" });

    expect(state.spec).toBe(ranked2.spec);
    expect(state.kept).toBeNull();
  });
});

describe("what a control is drawn from while an edit waits", () => {
  test("test_a_reading_that_comes_while_an_edit_waits_does_not_take_the_control_back", () => {
    const edit = edits.tagWeight("leafy", 0.7);
    const waiting = after({ type: "read_started", seq: 1 }, { type: "queued", operations: edit });

    const state = reduce(waiting, { type: "read_answered", data: read, meta: A });

    // The count of answers is what a control holds its own value against. The edit has
    // not been answered, so the count stands, and the control shows what it was set to.
    expect(state.answers).toBe(waiting.answers);
    expect(state.read?.at).toBe(state.answers);
    expect(reduce(state, { type: "rank_answered", data: ranked, sent: edit, meta: A }).answers).toBe(
      waiting.answers + 1,
    );
  });
});

describe("a search opened from a shared link", () => {
  test("test_the_spec_and_the_ranking_are_the_ones_the_api_returned_for_the_share", () => {
    const state = after({ type: "share_answered", id: SHARE_ID, data: shared, meta: A });

    expect(state.spec).toBe(shared.spec);
    expect(state.specHash).toBe(shared.spec_hash);
    expect(state.ranking).toEqual({
      scores: shared.scores,
      ranked: shared.ranked,
      filtered: shared.filtered,
      unranked: shared.unranked,
      empty_spec: shared.empty_spec,
      // How many areas are ranked, and how many of them the answer holds in full.
      areas_ranked: shared.areas_ranked,
      areas_listed: shared.areas_listed,
    });
    expect([state.ranking?.areas_ranked, state.ranking?.areas_listed]).toEqual([21, 20]);
    expect(state.phase).toBe("results");
  });

  test("test_a_search_the_person_began_did_not_come_from_a_link", () => {
    expect(opened().shared).toBeNull();
    expect(after({ type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A }).shared).toBeNull();
  });

  test("test_nothing_of_the_search_before_is_carried_into_the_shared_one", () => {
    const before = after(
      { type: "read_answered", data: read, meta: A },
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "queued", operations: edits.tagOn("pace") },
      { type: "selected", areaId: "syn-n0006" },
    );

    const state = reduce(before, { type: "share_answered", id: SHARE_ID, data: shared, meta: A });

    expect(state.read).toBeNull();
    // The places are the ones the share names, and none of the search before.
    expect(Object.keys(state.placeNames)).toEqual(shared.spec.commutes.map((commute) => commute.place_id));
    expect(state.pending).toEqual(NO_EDITS);
    expect(state.selectedId).toBeNull();
    expect(state.explanations).toEqual([]);
    // What the page was built on stays: the release is the same one.
    expect(state.meta).toBe(before.meta);
    expect(state.areas).toBe(before.areas);
    // Every control is drawn again from the spec that came.
    expect(state.answers).toBeGreaterThan(before.answers);
  });
});

describe("what the person said, and what was assumed for them", () => {
  test("test_a_tenure_said_in_words_is_stated_by_the_spec_itself", () => {
    // Seen in a browser: "Renting assumed" after the person typed "Renting". The API now
    // says that the tenure was stated, whether or not it moved, and the page keeps no
    // record of its own.
    const state = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: read, meta: A });

    expect(read.operations.budget_ops[0]).toMatchObject({ tenure: "rent", provenance: "stated" });
    expect(state.spec.tenure_from).toBe("stated");
    expect(state.tenurePicked).toBe(false);
  });

  test("test_a_tenure_picked_before_anything_was_sent_is_known_to_be_picked", () => {
    // The page then shows the default the API served for that tenure, which no edit made.
    const picked = reduce(opened(), { type: "tenure_swapped", tenure: "buy" });

    expect(opened().tenurePicked).toBe(false);
    expect(picked.spec).toBe(meta.defaults.buy);
    expect(picked.tenurePicked).toBe(true);
    // An edit that states the tenure is answered with a spec that says so itself.
    expect(reduce(opened(), { type: "queued", operations: edits.tenure("buy") }).tenurePicked).toBe(false);
  });

  test("test_starting_again_and_a_shared_search_forget_that_a_tenure_was_picked", () => {
    const picked = reduce(opened(), { type: "tenure_swapped", tenure: "buy" });

    expect(reduce(picked, { type: "started_again" }).tenurePicked).toBe(false);
    expect(reduce(picked, { type: "share_answered", id: SHARE_ID, data: shared, meta: A }).tenurePicked).toBe(false);
  });

  test("test_a_place_added_with_a_control_has_everything_nobody_chose_marked_assumed", () => {
    // Seen in a browser: a place read from a sentence said "Public transport assumed", and
    // the same place picked from the field said "Public transport", as if it had been chosen.
    const state = reduce(opened(), { type: "queued", operations: edits.placeAdd("syn-p0026") });

    expect(state.assumed["place:syn-p0026"]).toEqual(["mode", "max_minutes", "strictness"]);
  });

  test("test_a_part_of_a_place_the_person_then_sets_is_no_longer_assumed", () => {
    const added = reduce(opened(), { type: "queued", operations: edits.placeAdd("syn-p0026") });

    const state = reduce(added, { type: "queued", operations: edits.placeMode("syn-p0026", "cycle") });

    expect(state.assumed["place:syn-p0026"]).toEqual(["max_minutes", "strictness"]);
  });

  test("test_a_budget_set_by_its_amount_alone_has_the_rest_marked_assumed", () => {
    // Seen in a browser: a budget chosen from an offer read "One bedroom, flexible" after its
    // amount, as if both had been chosen. The edit held the amount and nothing else.
    expect(opened().spec.budget).toMatchObject({ amount: null, provenance: "default" });

    const state = reduce(opened(), { type: "queued", operations: edits.budgetAmount(1800) });

    expect(state.assumed.budget).toEqual(["segment", "strictness"]);
  });

  test("test_a_part_of_a_budget_that_its_edit_states_is_not_marked_assumed", () => {
    const sized: Operations = {
      ...NO_EDITS,
      budget_ops: [{ ...(edits.budgetAmount(1800).budget_ops[0] as BudgetEdit), segment: "bed_2" }],
    };

    expect(reduce(opened(), { type: "queued", operations: sized }).assumed.budget).toEqual(["strictness"]);
    // What the person sets afterwards is theirs.
    const set = reduce(opened(), { type: "queued", operations: edits.budgetAmount(1800) });
    const firm = reduce(set, { type: "queued", operations: edits.budgetStrictness("hard") });
    expect(firm.assumed.budget).toEqual(["segment"]);
  });

  test("test_what_one_press_says_of_a_budget_in_an_edit_of_its_own_is_not_marked_assumed", () => {
    // Seen in a browser: "£400,000, A flat assumed, firm limit" after one press on a sentence
    // that said "max £400k for a 1 bed flat". One press sends the amount and the kind of home
    // in an edit each, as they were offered, and the kind of home is the person's own words.
    const amount = { ...(edits.budgetAmount(400000).budget_ops[0] as BudgetEdit), tenure: "buy" as const };
    const pressed: Operations = {
      ...NO_EDITS,
      budget_ops: [
        { ...amount, amount: 0 },
        { ...amount, strictness: "hard" },
        { ...amount, amount: 0, segment: "flat" },
      ],
    };

    expect(reduce(opened(), { type: "queued", operations: pressed }).assumed.budget).toBeUndefined();
    // In whichever order the edits stand.
    const turned = { ...pressed, budget_ops: [...pressed.budget_ops].reverse() };
    expect(reduce(opened(), { type: "queued", operations: turned }).assumed.budget).toBeUndefined();
    // What no edit of the press says is still marked: here the kind of home.
    const unsized = { ...pressed, budget_ops: pressed.budget_ops.slice(0, 2) };
    expect(reduce(opened(), { type: "queued", operations: unsized }).assumed.budget).toEqual(["segment"]);
  });

  test("test_the_kind_of_house_that_burro_took_is_marked_assumed_and_one_a_person_pressed_is_not", () => {
    // A person named a house and no kind of house. One press holds the budget against a
    // terraced house, in an edit that says the kind is Burro's.
    const amount = { ...(edits.budgetAmount(400000).budget_ops[0] as BudgetEdit), tenure: "buy" as const };
    const kind = (segment: BudgetEdit["segment"], provenance: BudgetEdit["provenance"]): Operations => ({
      ...NO_EDITS,
      budget_ops: [
        { ...amount, amount: 0, segment, provenance },
        { ...amount, strictness: "hard" },
      ],
    });

    const taken = reduce(opened(), { type: "queued", operations: kind("terraced", "inferred") });
    expect(taken.assumed.budget).toEqual(["segment"]);
    // Whatever was set before: the kind is still Burro's.
    const set = { ...opened(), spec: { ...opened().spec, budget: { ...opened().spec.budget, provenance: "ui_edit" as const } } };
    expect(reduce(set, { type: "queued", operations: kind("terraced", "inferred") }).assumed.budget).toEqual(["segment"]);
    // Another kind, pressed by the person, is theirs. It takes the mark off.
    const pressed = reduce(taken, { type: "queued", operations: kind("semi_detached", "ui_edit") });
    expect(pressed.assumed.budget).toBeUndefined();
  });

  test("test_a_budget_the_person_had_already_set_a_part_of_is_not_marked_again", () => {
    // The size of home was chosen in the settings, and then an amount was given.
    const chosen = { ...opened(), spec: { ...opened().spec, budget: { ...opened().spec.budget, provenance: "ui_edit" as const } } };

    const state = reduce(chosen, { type: "queued", operations: edits.budgetAmount(1800) });

    expect(state.assumed.budget).toBeUndefined();
  });
});

describe("a service that cannot be reached", () => {
  const network: Failure = { ...timeout, kind: "network" };
  const notSet: Failure = { ...timeout, kind: "not_configured" };

  test("test_words_that_never_reached_burro_are_not_said_to_be_unreadable", () => {
    // Seen in a browser, with the API stopped: "Your words could not be read just now. The
    // settings do the same job." The settings could not work either.
    for (const failure of [network, notSet]) {
      const state = after({ type: "read_started", seq: 1 }, { type: "failed", step: "read", failure });

      expect(state.degraded).toBe(false);
      expect(state.settingsOpen).toBe(false);
      expect(state.failure).toBe(failure);
    }
  });

  test("test_words_that_burro_was_too_slow_to_read_still_leave_the_form_as_the_way_in", () => {
    const state = after({ type: "read_started", seq: 1 }, { type: "failed", step: "read", failure: timeout });

    expect(state.degraded).toBe(true);
    expect(state.settingsOpen).toBe(true);
  });

  test("test_that_the_words_could_not_be_read_is_no_longer_said_once_a_control_is_used", () => {
    // Seen in a browser: the line stayed on screen after a control had been used and answered,
    // with nothing beside it to try the words again.
    const failed = after({ type: "read_started", seq: 1 }, { type: "failed", step: "read", failure: timeout });

    const state = reduce(failed, { type: "queued", operations: edits.tagOn("leafy") });

    expect(failed.degraded).toBe(true);
    expect(state.degraded).toBe(false);
  });

  test("test_that_the_words_could_not_be_read_is_still_said_when_an_edit_made_before_is_ranked", () => {
    // The control was moved while the words were being read. The person has not yet been
    // told that the words were not read, so the ranking of their edit does not take the line away.
    const state = after(
      { type: "read_started", seq: 1 },
      { type: "queued", operations: edits.tagOn("leafy") },
      { type: "failed", step: "read", failure: timeout },
      { type: "rank_answered", data: ranked, sent: edits.tagOn("leafy"), meta: A },
    );

    expect(state.degraded).toBe(true);
  });

  test("test_words_the_rules_read_in_place_of_a_model_are_said_so_until_the_next_sentence", () => {
    const degraded = recordedAnswer("interpret", "interpret-degraded").body.data;
    const state = after(
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: degraded, meta: A },
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "queued", operations: edits.tagOn("leafy") },
      { type: "rank_answered", data: refined, sent: edits.tagOn("leafy"), meta: A },
    );

    expect(degraded.degraded).toBe(true);
    expect(state.degraded).toBe(true);
    expect(reduce(state, { type: "read_answered", data: read, meta: A }).degraded).toBe(false);
  });
});

describe("settings the page opened for the person", () => {
  const unread = recordedAnswer("interpret", "interpret-nothing-read").body.data;

  test("test_settings_the_page_opened_close_again_when_the_next_sentence_is_read", () => {
    // Seen on a phone: a sentence that could not be read opened the settings, which are six
    // screens tall, and the results of the next sentence were then 6,425 pixels down.
    const opens = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: unread, meta: A });

    const state = reduce(reduce(opens, { type: "read_started", seq: 2 }), { type: "read_answered", data: read, meta: A });

    expect(opens.settingsOpen).toBe(true);
    expect(state.settingsOpen).toBe(false);
  });

  test("test_settings_the_person_opened_stay_open", () => {
    const state = after(
      { type: "settings_opened", open: true },
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: unread, meta: A },
      { type: "read_started", seq: 2 },
      { type: "read_answered", data: read, meta: A },
    );

    expect(state.settingsOpen).toBe(true);
  });

  test("test_settings_the_page_opened_and_the_person_used_stay_open", () => {
    const state = after(
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: unread, meta: A },
      { type: "queued", operations: edits.tagOn("leafy") },
      { type: "rank_answered", data: ranked, sent: edits.tagOn("leafy"), meta: A },
      { type: "read_started", seq: 2 },
      { type: "read_answered", data: read, meta: A },
    );

    expect(state.settingsOpen).toBe(true);
  });

  test("test_settings_the_person_closed_are_not_opened_by_a_sentence_that_was_read", () => {
    const state = after(
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: unread, meta: A },
      { type: "settings_opened", open: false },
      { type: "read_started", seq: 2 },
      { type: "read_answered", data: read, meta: A },
    );

    expect(state.settingsOpen).toBe(false);
  });
});

describe("what the reader noticed and did not apply", () => {
  const noticed = recordedAnswer("interpret", "interpret-suggest").body.data;
  const offered = () => after({ type: "read_started", seq: 1 }, { type: "read_answered", data: noticed, meta: A });

  test("test_nothing_of_a_prompt_that_is_not_plain_is_applied", () => {
    const state = offered();

    expect(noticed.status).toBe("suggest");
    expect(state.spec).toEqual(meta.defaults.rent);
    expect(state.untouched).toBe(true);
    expect(state.read?.changed).toBe(false);
    expect(state.read?.suggestions).toBe(noticed.suggestions);
    expect(state.read?.unread).toBe(noticed.unread);
  });

  test("test_where_words_stand_is_kept_as_offsets_and_never_as_words", () => {
    const where = [...(offered().read?.unread ?? []), ...noticed.suggestions.flatMap((one) => one.spans)];

    expect(where.length).toBeGreaterThan(0);
    for (const span of where) {
      expect(Object.keys(span).sort()).toEqual(["end", "start"]);
      expect([typeof span.start, typeof span.end]).toEqual(["number", "number"]);
    }
    // What is said of a thing that was noticed is the API's name for it, and never the words typed.
    const names = new Set([...meta.features.map((one) => one.short_label), ...meta.tags.map((one) => one.label)]);
    expect(noticed.suggestions.map((one) => names.has(one.label))).toEqual([true, true]);
  });

  test("test_where_something_was_noticed_the_settings_are_not_opened_for_the_person", () => {
    const nothing = recordedAnswer("interpret", "interpret-nothing-read").body.data;

    expect(offered().settingsOpen).toBe(false);
    // Where nothing was noticed at all, the settings are the way in, as before.
    expect(after({ type: "read_answered", data: nothing, meta: A }).settingsOpen).toBe(true);
  });

  /**
   * What the flow makes of every offer of a reading, as it hands it to the store. `worded`
   * is the way of a journey whose words make its limit firm, by its name: left out, it is
   * as the look has chosen.
   */
  const takingAll = (data: typeof noticed, worded: Worded = A_LIMIT_THE_WORDS_MAKE_FIRM): SearchEvent => {
    const all = takenOfAll(
      data.suggestions,
      meta,
      WHERE_BURRO_CANNOT_TELL,
      OF_A_WORD_READ_SEVERAL_WAYS,
      [],
      WHAT_THE_WORDS_TURN_AWAY,
      worded,
    );
    const made = data.suggestions.flatMap((offer, at) => {
      const one = all[at];
      return one === undefined ? [] : [{ at, offer, made: one }];
    });
    return {
      type: "offers_taken",
      taken: made.flatMap(({ at, offer, made: one }) =>
        one.way === null
          ? []
          : [{ at, operations: one.operations, marks: one.marks, thing: thingOf(offer, one.operations), words: restsOn(offer) }],
      ),
      left: made.flatMap(({ at, made: one }) => (one.way === null ? [{ at, why: one.why }] : [])),
    };
  };

  /** The same, where the service marks one way of the first thing as its guess. */
  const guessing = (way: string): typeof noticed => ({
    ...noticed,
    suggestions: noticed.suggestions.map((offer, at) =>
      at === 0 ? { ...offer, choices: offer.choices.map((one) => ({ ...one, guess: one.id === way })) } : offer,
    ),
  });

  /** The same again, where nothing of the second thing waits for a person: it is said of the person's own home. */
  const wanted = (data: typeof noticed): typeof noticed => ({
    ...data,
    suggestions: data.suggestions.map((offer, at) => (at === 1 ? { ...offer, only_by_choice: false, note: "" } : offer)),
  });

  test("test_what_burro_takes_goes_from_what_was_noticed_and_its_edits_wait_to_be_sent", () => {
    const [pubs, noise] = wanted(guessing("less")).suggestions;
    const read = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: wanted(guessing("less")), meta: A });
    const state = reduce(read, takingAll(wanted(guessing("less"))));

    expect(state.read?.suggestions).toEqual([]);
    expect(state.read?.took).toBe(2);
    expect(state.read?.left).toEqual([]);
    expect(state.read?.things).toEqual(["feature:venue_evening_per_homes", "feature:noise_exposure"]);
    // The edits are the ones the service gave with the way that was taken, in the order
    // the things were noticed. The spec is as the service last returned it.
    const fewer = pubs?.choices.find((way) => way.id === "less")?.operations ?? NO_EDITS;
    const less = noise?.choices.find((way) => way.id === "less")?.operations ?? NO_EDITS;
    expect(state.pending).toEqual(merged(fewer, less));
    expect(state.spec).toBe(offered().spec);
    // The reading itself changed nothing. What Burro took of it changes the search.
    expect(state.read?.changed).toBe(false);
    expect(changedTheSearch(state.read ?? { changed: false, took: 0 })).toBe(true);
    expect(nothingCameOf(state.read ?? offered().read!)).toBe(false);
    // An offer that is not there changes nothing.
    const again = reduce(state, { type: "offers_taken", taken: [], left: [{ at: 5, why: "no_way" }] });
    expect(again).toBe(state);
  });

  test("test_a_thing_that_runs_two_ways_where_the_words_give_neither_is_left_and_what_stands_beside_it_waits_to_be_sent", () => {
    const [pubs, noise] = wanted(noticed).suggestions;
    const state = reduce(
      after({ type: "read_started", seq: 1 }, { type: "read_answered", data: wanted(noticed), meta: A }),
      takingAll(wanted(noticed)),
    );

    expect(state.read?.suggestions).toEqual([]);
    expect(state.read?.took).toBe(1);
    expect(state.read?.left.map((one) => [one.label, one.why])).toEqual([[pubs?.label, "two_ways"]]);
    expect(state.read?.things).toEqual(["feature:noise_exposure"]);
    expect(state.pending).toEqual(noise?.choices.find((way) => way.id === "less")?.operations);
    // Nothing of pubs is assumed, since nothing of them was taken. Less noise is what the
    // person said: the words name it, and it runs the one way.
    expect(state.assumed).toEqual({ "feature:noise_exposure": ["weight"] });
  });

  test("test_where_the_one_waits_for_the_person_and_the_words_give_no_way_of_the_other_nothing_waits_to_be_sent", () => {
    // "Pubs are so noisy", as the service answers it: that it is noisy is said of the pubs.
    const [pubs, noise] = noticed.suggestions;
    const state = reduce(offered(), takingAll(noticed));

    expect(state.read?.suggestions).toEqual([]);
    expect(state.read?.took).toBe(0);
    expect(state.read?.left.map((one) => [one.label, one.why])).toEqual([
      [pubs?.label, "two_ways"],
      [noise?.label, "not_said"],
    ]);
    expect(state.read?.things).toEqual([]);
    expect(state.pending).toEqual(NO_EDITS);
    expect(state.assumed).toEqual({});
    // Something came of the words, which the line names, and the search is as it was.
    expect(nothingCameOf(state.read ?? offered().read!)).toBe(false);
    expect(changedTheSearch(state.read ?? { changed: false, took: 0 })).toBe(false);
  });

  test("test_what_burro_chose_for_the_person_is_assumed_and_what_they_said_is_not", () => {
    // Read into words that name neither thing, as a word is that is read into a measure.
    const readIn: typeof noticed = {
      ...wanted(guessing("less")),
      suggestions: wanted(guessing("less")).suggestions.map((offer) => ({ ...offer, by_name: false })),
    };
    const read = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: readIn, meta: A });
    const state = reduce(read, takingAll(readIn));

    // Pubs run two ways, and the way is the service's guess: the thing and the way are
    // Burro's. Less noise runs one way, and that it counts at all is Burro's.
    expect(state.assumed).toEqual({
      "feature:venue_evening_per_homes": ["weight", "direction"],
      "feature:noise_exposure": ["weight"],
    });
    // Where the words name the thing and give its way, it is what the person said.
    const said = wanted(guessing("less"));
    const named = reduce(
      after({ type: "read_started", seq: 1 }, { type: "read_answered", data: said, meta: A }),
      takingAll(said),
    );
    expect(named.assumed["feature:venue_evening_per_homes"]).toBeUndefined();
    // A person who then sets the way themselves has chosen it: it is assumed no longer.
    const set = reduce(state, {
      type: "queued",
      operations: edits.featureDirection("venue_evening_per_homes", 0.5, "less"),
    });
    expect(set.assumed["feature:venue_evening_per_homes"]).toBeUndefined();
    expect(set.assumed["feature:noise_exposure"]).toEqual(["weight"]);
  });

  test("test_what_one_press_would_have_taken_as_it_was_said_is_marked_as_the_press_marked_it", () => {
    const long = recordedAnswer("interpret", "interpret-by-model-long").body.data;
    const read = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: long, meta: A });

    // As the look has chosen, and by the name of each way of a journey.
    const ways: readonly (readonly [Worded | undefined, string, readonly string[]])[] = [
      // Nobody said how to travel. And the words gave a firm limit where a guide was taken.
      [undefined, "soft", ["mode", "strictness"]],
      ["guide", "soft", ["mode", "strictness"]],
      // The other way it was built: the words make the limit firm, and it is taken as they
      // make it. That it is firm is then what the person said.
      ["as_worded", "hard", ["mode"]],
    ];
    for (const [worded, limit, assumed] of ways) {
      const state = reduce(read, takingAll(long, worded));

      // Quiet streets, the park and the culture were said, and nothing of them is assumed.
      expect(state.assumed["tag:quiet_residential"]).toBeUndefined();
      expect(state.assumed["feature:park_proximity"]).toBeUndefined();
      expect(state.assumed["feature:culture_venues_per_homes"]).toBeUndefined();
      // The budget was taken as it was worded, a firm limit for a home of one bedroom.
      expect(state.assumed.budget).toBeUndefined();
      expect([worded, state.pending.commute_ops.map((edit) => edit.strictness)]).toEqual([worded, [limit]]);
      expect([worded, state.assumed["place:syn-p0017"]]).toEqual([worded, assumed]);
      // What Burro read into two words is its own reading, and says so. A word counts once:
      // of what is read into the same words one thing is taken, and nothing is assumed of
      // what was left.
      for (const key of ["feature:brand_mix", "tag:village_feel"]) {
        expect([key, state.assumed[key]]).toEqual([key, ["weight"]]);
      }
      for (const key of ["feature:price_median", "feature:homes_higher_bands", "tag:built_age", "feature:highstreet_access"]) {
        expect([key, state.assumed[key]]).toEqual([key, undefined]);
      }
    }
  });

  test("test_what_burro_took_nothing_of_is_kept_with_why_in_the_services_own_words", () => {
    const long = recordedAnswer("interpret", "interpret-by-model-long").body.data;
    const read = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: long, meta: A });
    const state = reduce(read, takingAll(long));
    const gritty = long.suggestions.find((one) => one.label === "Gritty");

    expect(state.read?.suggestions).toEqual([]);
    expect((state.read?.took ?? 0) + (state.read?.left.length ?? 0)).toBe(long.suggestions.length);
    expect(state.read?.left[0]).toEqual({
      why: "crime",
      target: gritty?.target,
      label: "Gritty",
      does: gritty?.does,
      follows: gritty?.follows,
      note: gritty?.note,
    });
    // No edit of it waits to be sent: recorded crime is not set counting.
    expect(state.pending.tag_ops.map((edit) => edit.tag_id)).not.toContain("street_character");
    expect(state.assumed["tag:street_character"]).toBeUndefined();
    // It is named among what was left out, and is no edit that the service turned away.
    // With it stand the readings of words that were taken another way, each with why.
    expect(leftOutOf(state.read).map((thing) => [thing.name, thing.why])).toEqual([
      ["Gritty", "crime"],
      ["What homes sell for", "otherwise"],
      ["Homes in the higher council tax bands", "by_choice"],
      ["Age of buildings", "otherwise"],
      ["Nearer a town centre", "otherwise"],
    ]);
    expect(refusals(state.read, null)).toEqual([]);
  });

  test("test_what_was_taken_of_a_thing_as_the_rules_read_it_is_not_taken_again_as_a_model_did", () => {
    const atOnce = recordedAnswer("interpret", "interpret-rules-at-once").body.data;
    const long = recordedAnswer("interpret", "interpret-by-model-long").body.data;
    const byTheRules = reduce(
      after({ type: "read_started", seq: 1 }, { type: "read_answered", data: atOnce, meta: A }),
      takingAll(atOnce),
    );
    expect(byTheRules.read?.more).toBe(true);
    const waiting = byTheRules.pending;

    const byAModel = reduce(byTheRules, { type: "read_more_answered", data: long });

    // What a model read joins what the rules read. Of what was taken or left already, by
    // the same name and the same words, nothing is held to be made anything of again.
    expect(byAModel.read?.more).toBe(false);
    expect(byAModel.read?.suggestions.map((one) => one.label)).toEqual(["A budget of £1,900"]);
    expect(byAModel.read?.took).toBe(byTheRules.read?.took);
    expect(byAModel.pending).toBe(waiting);
    // The budget is one thing, whichever named it: the offer goes, and no edit is made of it.
    const [budget] = byAModel.read?.suggestions ?? [];
    expect(byTheRules.read?.things).toContain(budget?.target);
    const gone = reduce(byAModel, { type: "offers_taken", taken: [], left: [], again: [0] });
    expect(gone.read?.suggestions).toEqual([]);
    expect(gone.read?.took).toBe(byTheRules.read?.took);
    expect(gone.pending).toBe(waiting);
    expect(gone.assumed).toBe(byAModel.assumed);
  });

  test("test_the_notice_is_kept_as_it_came_whatever_burro_takes", () => {
    // The notice is the service's. What the page shows of it is the page's to say, and
    // nothing of it is changed where it is kept.
    const beside = recordedAnswer("interpret", "interpret-suggest-notice").body.data;
    const told = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: beside, meta: A });
    const state = reduce(told, takingAll(beside));

    // Leafy is taken. That a street is noisy is not said to be what the person wants less of.
    expect(state.read?.took).toBe(1);
    expect(state.read?.notice).toBe("neutral_places");
    expect(state.read?.notice_text).toBe(beside.notice_text);
  });

  test("test_every_suggestion_goes_when_the_box_changes", () => {
    // Where the words stand is known for the text that was sent, and for no other.
    const state = reduce(offered(), { type: "box_changed" });

    expect(state.read?.suggestions).toEqual([]);
    expect(state.read?.unread).toEqual([]);
    expect(reduce(state, { type: "box_changed" })).toBe(state);
    expect(reduce(opened(), { type: "box_changed" })).toEqual(opened());
  });

  test("test_that_a_part_was_not_read_is_still_known_when_the_box_has_changed", () => {
    // Where the stretch stood goes with the text. That the ranking left something out is
    // true of the ranking, and stays until another sentence is read.
    expect(offered().read?.partUnread).toBe(true);
    expect(reduce(offered(), { type: "box_changed" }).read?.partUnread).toBe(true);
    // A sentence that was read in full leaves nothing out.
    const inFull = recordedAnswer("interpret", "interpret-first").body.data;
    const read = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: inFull, meta: A });
    expect(inFull.unread).toEqual([]);
    expect(read.read?.partUnread).toBe(false);
  });

  test("test_stop_puts_back_what_was_offered_before_the_sentence_that_was_stopped", () => {
    const state = after(
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: noticed, meta: A },
      { type: "settled" },
      { type: "read_started", seq: 2 },
      { type: "read_answered", data: read, meta: A },
      { type: "stopped" },
    );

    expect(state.read?.suggestions).toBe(noticed.suggestions);
    expect(state.placeNames).toEqual({});
  });
});

describe("a word with two meanings", () => {
  const gritty = recordedAnswer("interpret", "variant-a/interpret-gritty").body.data;
  const key = "tag:works_warehouses";

  test("test_the_word_a_vibe_was_read_from_is_kept_with_the_vibe", () => {
    const state = after({ type: "read_answered", data: gritty, meta: A });

    expect(state.quoted).toEqual({ [key]: "gritty" });
    expect(state.assumed[key]).toEqual(["weight", "word"]);
  });

  test("test_a_vibe_the_person_then_sets_is_no_longer_said_to_be_read_from_the_word", () => {
    const state = after(
      { type: "read_answered", data: gritty, meta: A },
      { type: "queued", operations: edits.tagWeight("works_warehouses", 0.7) },
    );

    expect(state.assumed[key]).toBeUndefined();
  });

  test("test_a_word_is_forgotten_with_the_vibe_it_was_read_as", () => {
    const state = after(
      { type: "read_answered", data: gritty, meta: A },
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
    );

    expect(ranked.spec.tags.map((tag) => tag.tag_id)).not.toContain("works_warehouses");
    expect(state.quoted).toEqual({});
  });
});

describe("how much a ranking moved", () => {
  const scores = (...ids: string[]) => ({
    ...ranked,
    scores: ids.map((area_id) => ({ area_id, score: 1, counted: 1, present: 1 })),
  });

  test("test_an_area_has_changed_place_when_it_stands_elsewhere_among_those_ranked_both_times", () => {
    expect(movedBetween(scores("a", "b", "c"), scores("a", "b", "c"))).toBe(0);
    expect(movedBetween(scores("a", "b", "c"), scores("b", "a", "c"))).toBe(2);
    expect(movedBetween(scores("a", "b", "c", "d"), scores("d", "b", "c"))).toBe(3);
  });

  test("test_an_area_that_went_or_came_moves_no_other_area", () => {
    // Seen in a browser: a list of 20 became a list of 15, and the page said that 21 areas
    // had changed place. The areas that were left stood in the order they had stood in.
    expect(movedBetween(scores("a", "b", "c"), scores("a", "b"))).toBe(0);
    expect(movedBetween(scores("a", "b"), scores("a", "b", "c"))).toBe(0);
    expect(movedBetween(scores("a", "b", "c"), scores("b", "c"))).toBe(0);
    expect(movedBetween(scores("a", "b", "c"), scores("c", "b"))).toBe(2);
    const twenty = Array.from({ length: 22 }, (_, at) => `n${at}`);
    expect(movedBetween(scores(...twenty), scores(...twenty.filter((_, at) => at % 4 !== 0)))).toBe(0);
  });

  test("test_how_many_areas_were_ranked_before_is_kept_with_how_many_changed_place", () => {
    const before = after({ type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A });
    const fewer = { ...ranked, scores: ranked.scores.slice(0, 15), ranked: ranked.ranked.slice(0, 15) };

    const then = reduce(before, { type: "rank_answered", data: fewer, sent: NO_EDITS, meta: A });

    expect(before.rankedBefore).toBeNull();
    expect(then.rankedBefore).toBe(ranked.scores.length);
    expect(then.moved).toBe(0);
  });

  test("test_defaults_gave_way_when_a_setting_nobody_chose_counts_for_less_than_it_did", () => {
    expect(gaveWayBetween(meta.defaults.rent, read.spec)).toBe(true);
    expect(gaveWayBetween(read.spec, refined.spec)).toBe(false);
    expect(gaveWayBetween(meta.defaults.rent, meta.defaults.rent)).toBe(false);
  });
});

describe("what was not applied", () => {
  /** A cheaper home where no budget is set: the edit to the budget is refused, and the park is applied. */
  const cheaper = recordedAnswer("interpret", "interpret-rejected").body.data;
  const asked = recordedAnswer("interpret", "interpret-clarify").body.data;
  const readOf = (data: typeof cheaper) => after({ type: "read_answered", data, meta: A }).read;

  test("test_each_refusal_is_tied_to_the_part_its_edit_was_about", () => {
    expect(refusals(readOf(cheaper), null)).toEqual([{ key: "budget", reason: "nothing_to_change" }]);
    // An edit to a feature is tied to that feature, whichever its place among the edits.
    const two = {
      ...cheaper,
      operations: { ...cheaper.operations, weight_ops: edits.featureOn("crime_burglary_theft").weight_ops },
      rejected: [{ group: "weight_ops", index: 0, reason: "crime_needs_explicit_request" }] as const,
    };
    expect(refusals(readOf(two), null)).toEqual([
      { key: "feature:crime_burglary_theft", reason: "crime_needs_explicit_request" },
    ]);
  });

  test("test_a_refusal_that_a_question_stands_for_is_not_said_twice", () => {
    expect(asked.rejected).toEqual([{ group: "commute_ops", index: 0, reason: "unknown_place" }]);
    expect(refusals(readOf(asked), null)).toEqual([]);
  });
});

describe("a question that is settled with no person asked", () => {
  const asked = recordedAnswer("interpret", "interpret-clarify").body.data;
  const notFound = recordedAnswer("interpret", "interpret-clarify-no-options").body.data;
  /** What the flow makes of every question of a reading, as it hands it to the store. */
  const settling = (data: typeof asked): SearchEvent => ({
    type: "questions_settled",
    settled: data.clarify.map((question) => {
      const made = settledOf(data.operations, question);
      return { question, id: made.option?.id ?? null, operations: made.operations };
    }),
  });
  const readOf = (data: typeof asked) => after({ type: "read_started", seq: 1 }, { type: "read_answered", data, meta: A });

  test("test_a_name_that_several_places_bear_is_the_first_the_service_gave_and_its_edit_waits_to_be_sent", () => {
    const [first] = asked.clarify[0]?.options ?? [];
    const state = reduce(readOf(asked), settling(asked));

    expect(asked.clarify[0]?.options.length).toBeGreaterThan(1);
    expect(state.read?.clarify).toEqual([]);
    // The refusal the question stood for goes with it: the place is known now.
    expect(state.read?.rejected).toEqual([]);
    expect(refusals(state.read, null)).toEqual([]);
    expect(state.pending).toEqual({
      ...NO_EDITS,
      commute_ops: [{ ...asked.operations.commute_ops[0], place_id: first?.id }],
    });
    // What was assumed of the journey asked about is assumed of the place that was taken,
    // and so is the place itself: nobody chose it.
    expect(state.assumed[`place:${first?.id}`]).toEqual(["mode", "strictness", "place"]);
    expect(state.assumed["place:"]).toBeUndefined();
  });

  test("test_a_place_the_person_then_sets_a_part_of_is_still_one_that_burro_took", () => {
    const [first] = asked.clarify[0]?.options ?? [];
    const settled = reduce(readOf(asked), settling(asked));

    const set = reduce(settled, { type: "queued", operations: edits.placeMode(first?.id ?? "", "cycle") });

    expect(set.assumed[`place:${first?.id}`]).toEqual(["strictness", "place"]);
    // Taken out, it leaves nothing assumed behind it.
    const out = reduce(set, { type: "queued", operations: edits.placeRemove(first?.id ?? "") });
    expect(out.assumed[`place:${first?.id}`]).toBeUndefined();
  });

  test("test_where_the_service_gives_no_place_nothing_is_taken_and_the_refusal_is_what_is_said", () => {
    const state = reduce(readOf(notFound), settling(notFound));

    expect(notFound.clarify[0]?.options).toEqual([]);
    expect(state.read?.clarify).toEqual([]);
    expect(state.pending).toEqual(NO_EDITS);
    expect(state.read?.rejected).toEqual(notFound.rejected);
    expect(refusals(state.read, null)).toEqual([{ key: "place:", reason: "unknown_place" }]);
  });

  test("test_a_question_that_is_settled_already_and_one_of_no_reading_change_nothing", () => {
    const settled = reduce(readOf(notFound), settling(notFound));

    expect(reduce(settled, settling(notFound))).toBe(settled);
    expect(reduce(opened(), settling(asked))).toEqual(opened());
  });
});

describe("what was not applied, of what a control sent", () => {
  const cheaper = recordedAnswer("interpret", "interpret-rejected").body.data;
  const readOf = (data: typeof cheaper) => after({ type: "read_answered", data, meta: A }).read;

  test("test_what_a_control_sent_is_said_at_the_control_and_what_words_made_is_not", () => {
    const refused = {
      operations: merged(edits.tagOn("leafy"), edits.budgetAmount(1)),
      rejected: [{ group: "budget_ops", index: 0, reason: "out_of_range" }] as const,
    };

    expect([...refusedByPart(refused)]).toEqual([["budget", "out_of_range"]]);
    expect([...refusedByPart(null)]).toEqual([]);
    expect(refusals(readOf(cheaper), refused)).toHaveLength(2);
  });
});

describe("how far into the box the search has read", () => {
  const second = recordedAnswer("interpret", "interpret-second-sentence").body.data;
  const unread = recordedAnswer("interpret", "interpret-nothing-read").body.data;
  const noticed = recordedAnswer("interpret", "interpret-suggest").body.data;
  // A string found nowhere else, planted in what a person types.
  const CANARY = "zqxcanary7431";

  /** What the box tells of letters typed at its end: how many, and how many it then holds. */
  const typed = (letters: number, held: number): SearchEvent => ({
    type: "box_edited",
    change: { at: held, out: 0, into: letters, holds: held + letters },
  });
  const changedAt = (change: Change): SearchEvent => ({ type: "box_edited", change });
  /** So many letters are sent to be read: all that stands in the box after what was read. */
  const sent = (letters: number, seq: number): SearchEvent => ({ type: "read_started", seq, letters });
  /** A first sentence of 15 letters, typed, sent, read and ranked. */
  const first: SearchEvent[] = [
    typed(15, 0),
    sent(15, 1),
    { type: "read_answered", data: read, meta: A },
    { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
  ];
  /** Then 12 letters more typed after it, and sent. */
  const more: SearchEvent[] = [typed(12, 15), sent(12, 2)];

  test("test_a_search_that_opens_has_read_nothing_of_the_box", () => {
    expect(opened().box).toEqual(NO_BOX);
    expect(opened().box.read).toEqual({ to: 0, changed: false });
  });

  test("test_the_search_has_read_what_was_sent_once_something_came_of_it", () => {
    const sending = after(typed(15, 0), sent(15, 1));
    expect(sending.box.read.to).toBe(0);

    // Read in full, read into things to choose from, and read into a question and no more.
    const asked = recordedAnswer("interpret", "visit/09-place").body.data;
    expect([asked.applied.filter((edit) => edit.changed), asked.clarify.length]).toEqual([[], 1]);
    for (const data of [read, noticed, asked]) {
      const state = reduce(sending, { type: "read_answered", data, meta: A });
      expect(state.box.read).toEqual({ to: 15, changed: false });
    }
    // An edit that was read and turned away came of the words too, and was said.
    const refused = recordedAnswer("interpret", "interpret-rejected").body.data;
    expect(refused.rejected.length).toBeGreaterThan(0);
    expect(reduce(sending, { type: "read_answered", data: refused, meta: A }).box.read.to).toBe(15);
  });

  test("test_words_that_nothing_came_of_are_still_to_be_read", () => {
    // The page says that nothing could be read, and to say it another way. Said another way
    // where it stands, or with words put before it, all of it is sent.
    const state = after(...first, ...more, { type: "read_answered", data: unread, meta: A }, { type: "settled" });

    expect([unread.applied, unread.suggestions, unread.clarify]).toEqual([[], [], []]);
    expect(state.box.read).toEqual({ to: 15, changed: false });
    expect(state.box.sending).toBeNull();
    // Where they stand is known, so that they can be shown in the box.
    expect(state.box.shown).toBe(15);
    // A change among them is no change to words that were read.
    expect(reduce(state, changedAt({ at: 17, out: 2, into: 6, holds: 31 })).box.read).toEqual({ to: 15, changed: false });
  });

  test("test_words_that_a_model_goes_on_reading_are_read_once_it_makes_something_of_them", () => {
    const pending = { ...unread, model_pending: true };
    const reading = after(...first, ...more, { type: "read_answered", data: pending, meta: A }, { type: "settled" });

    expect(reading.box.read.to).toBe(15);
    expect(reduce(reading, { type: "read_more_answered", data: noticed }).box.read.to).toBe(27);
    // It made nothing of them either, could not be asked, or was stopped by a change to the box.
    expect(reduce(reading, { type: "read_more_answered", data: unread }).box).toMatchObject({ read: { to: 15 }, sending: null });
    expect(reduce(reading, { type: "read_more_failed" }).box).toMatchObject({ read: { to: 15 }, sending: null });
  });

  test("test_what_is_added_is_read_from_where_the_search_had_read_to", () => {
    const state = after(...first, ...more, { type: "read_answered", data: second, meta: A });

    expect(state.box.read).toEqual({ to: 27, changed: false });
    // The service counts where words stand from the start of what it was sent.
    expect(state.box.shown).toBe(15);
  });

  test("test_typing_what_is_added_tells_nobody_anything", () => {
    // A person types after what was read, letter by letter. The store is as it was, so
    // nothing of the page is drawn again for it.
    const state = after(...first, typed(1, 15));

    expect(reduce(state, typed(1, 16))).toBe(state);
    expect(reduce(state, changedAt({ at: 15, out: 2, into: 0, holds: 15 }))).toBe(state);
    expect(reduce(opened(), typed(1, 0))).toEqual(opened());
  });

  test("test_words_that_could_not_be_read_are_still_to_be_read", () => {
    const state = after(...first, ...more, { type: "failed", step: "read", failure: timeout });

    expect(state.box.read).toEqual({ to: 15, changed: false });
    expect(state.box.sending).toBeNull();
    // So trying again sends them, with whatever was typed after them since.
    const again = after(...first, ...more, { type: "failed", step: "read", failure: timeout }, typed(4, 27), sent(16, 3));
    expect(again.box.sending).toEqual({ to: 31, changed: false });
    expect(reduce(again, { type: "read_answered", data: second, meta: A }).box.read.to).toBe(31);
  });

  test("test_words_that_were_read_and_not_ranked_were_read_all_the_same", () => {
    const state = after(...first, ...more, { type: "read_answered", data: second, meta: A }, {
      type: "failed",
      step: "rank",
      failure: timeout,
    });

    // The search holds what they said, so they are not sent again.
    expect(state.spec).toBe(second.spec);
    expect(state.box.read.to).toBe(27);
  });

  test("test_stop_puts_back_how_far_the_search_had_read_with_the_search", () => {
    const stopped = after(...first, ...more, { type: "read_answered", data: second, meta: A }, { type: "stopped" });

    expect(stopped.spec).toBe(ranked.spec);
    expect(stopped.box.read).toEqual({ to: 15, changed: false });
    expect(stopped.box.shown).toBeNull();
    // Stopped before the words were read, it had read no further.
    expect(after(...first, ...more, { type: "stopped" }).box.read.to).toBe(15);
    // Once the ranking of the words is in there is nothing to put back.
    const ranking = after(...first, ...more, { type: "read_answered", data: second, meta: A }, {
      type: "rank_answered",
      data: refined,
      sent: NO_EDITS,
      meta: A,
    });
    expect(reduce(ranking, { type: "stopped" }).box.read.to).toBe(27);
  });

  test("test_a_search_that_begins_again_has_read_nothing_of_a_box_that_still_holds_words", () => {
    // "Start again" beside a failure leaves the box as it is. What it holds was read by the
    // search before, and not by this one.
    expect(after(...first).box.read.to).toBe(15);
    expect(after(...first, { type: "started_again" }).box).toEqual(NO_BOX);
    expect(after(...first, { type: "share_answered", id: SHARE_ID, data: shared, meta: A }).box).toEqual(NO_BOX);
  });

  test("test_a_box_that_is_emptied_or_typed_over_whole_has_nothing_in_it_that_was_read", () => {
    const emptied = after(...first, changedAt({ at: 0, out: 15, into: 0, holds: 0 }));
    const typedOver = after(...first, changedAt({ at: 0, out: 15, into: 1, holds: 1 }));

    expect(emptied.box.read).toEqual({ to: 0, changed: false });
    expect(typedOver.box.read).toEqual({ to: 0, changed: false });
    // The search is as it was: what is typed next is added to it.
    expect(emptied.spec).toBe(ranked.spec);
    expect(emptied.ranking).not.toBeNull();
  });

  test("test_a_change_among_the_words_that_were_read_is_known_and_the_words_are_not", () => {
    const state = after(...first, changedAt({ at: 6, out: 3, into: 2, holds: 14 }));

    expect(state.box.read).toEqual({ to: 14, changed: true });
    // Once what was added after them is read, it is not said again.
    const added = after(...first, changedAt({ at: 6, out: 3, into: 2, holds: 14 }), typed(12, 14), sent(12, 2));
    expect(added.box.read.changed).toBe(true);
    expect(reduce(added, { type: "read_answered", data: second, meta: A }).box.read).toEqual({ to: 26, changed: false });
  });

  test("test_a_box_that_is_drawn_again_is_empty_and_the_search_is_as_it_was", () => {
    const back = after(...first, { type: "box_found", holds: 0 });

    expect(back.box).toEqual(NO_BOX);
    expect(back.spec).toBe(ranked.spec);
    // A box that is found as the search knows it tells nobody anything.
    const state = after(...first);
    expect(reduce(state, { type: "box_found", holds: 15 })).toBe(state);
  });

  test("test_where_the_words_stand_is_known_until_the_box_changes", () => {
    const state = after(...first);

    expect(state.box.shown).toBe(0);
    expect(reduce(state, typed(1, 15)).box.shown).toBeNull();
  });

  test("test_words_that_were_read_are_read_still_when_the_keys_that_undo_put_them_back", () => {
    // Seen in a browser: the whole of the box was typed over by accident and put back, and
    // the sentence was sent again, onto a search that had been set by hand.
    const typedOver = after(...first, changedAt({ at: 0, out: 15, into: 1, holds: 1 }));
    expect(typedOver.box.read.to).toBe(0);

    // The keys that undo take the letter out and leave the sentence selected.
    const back = reduce(typedOver, changedAt({ at: 0, out: 1, into: 15, holds: 15, how: "undone" }));

    expect(back.box.read).toEqual({ to: 15, changed: false });
    expect([back.box.gone, back.box.back]).toEqual([0, []]);
    // The keys that do again put the letter back, of which nothing was read, and the keys that undo the sentence.
    const again = reduce(back, changedAt({ at: 1, out: 14, into: 0, holds: 1, how: "redone" }));
    expect(again.box.read.to).toBe(0);
    expect(reduce(again, changedAt({ at: 0, out: 1, into: 15, holds: 15, how: "undone" })).box.read).toEqual({ to: 15, changed: false });
    // Where a browser leaves no more than a caret, the sentence is taken as read, and that is said.
    const unsure = reduce(typedOver, changedAt({ at: 1, out: 0, into: 14, holds: 15, how: "undone" }));
    expect(unsure.box.read).toEqual({ to: 15, changed: true });
    // Put back after more was done to the box, it is taken as read, and that is said.
    const later = after(
      ...first,
      changedAt({ at: 9, out: 6, into: 0, holds: 9 }),
      typed(4, 9),
      changedAt({ at: 9, out: 4, into: 0, holds: 9, how: "undone" }),
      changedAt({ at: 9, out: 0, into: 6, holds: 15, how: "undone" }),
    );
    expect(later.box.read).toEqual({ to: 15, changed: true });
    // The search is as it was all the while.
    expect([back.spec, again.spec, unsure.spec, later.spec]).toEqual([ranked.spec, ranked.spec, ranked.spec, ranked.spec]);
  });

  test("test_a_search_that_begins_again_keeps_nothing_of_what_was_taken_out_of_the_box", () => {
    const out = after(...first, changedAt({ at: 9, out: 6, into: 0, holds: 9 }));
    expect([out.box.gone, out.box.back.map((was) => was.held)]).toEqual([6, [15]]);

    expect(reduce(out, { type: "started_again" }).box).toEqual(NO_BOX);
    expect(reduce(out, { type: "share_answered", id: SHARE_ID, data: shared, meta: A }).box).toEqual(NO_BOX);
    expect(reduce(out, { type: "box_found", holds: 0 }).box).toEqual(NO_BOX);
    // What the search knew before is let go once words are sent. What was taken out may be put back yet.
    const sending = reduce(reduce(out, typed(4, 9)), sent(4, 2));
    expect([sending.box.gone, sending.box.back, sending.box.again]).toEqual([6, [], []]);
    expect(reduce(sending, { type: "read_answered", data: second, meta: A }).box.gone).toBe(6);
  });

  test("test_a_sentence_that_says_nothing_of_how_much_was_sent_moves_nothing", () => {
    const state = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: read, meta: A });

    expect(state.box.read).toEqual({ to: 0, changed: false });
  });

  test("test_what_the_store_holds_of_the_box_is_counts_and_whether_a_thing_is_so", () => {
    const leaves = (value: unknown): unknown[] =>
      value !== null && typeof value === "object" ? Object.values(value).flatMap(leaves) : [value];
    const sentence = `leafy and quiet ${CANARY}`;
    const states = [
      after(typed(sentence.length, 0), sent(sentence.length, 1)),
      after(typed(sentence.length, 0), sent(sentence.length, 1), { type: "read_answered", data: read, meta: A }),
      after(...first, changedAt({ at: 6, out: 3, into: 2, holds: 14 })),
      after(...first, ...more, { type: "read_answered", data: second, meta: A }, { type: "stopped" }),
    ];

    for (const state of states) {
      const held = leaves(state.box);
      expect(held.length).toBeGreaterThan(3);
      expect(held.filter((leaf) => leaf !== null && typeof leaf !== "number" && typeof leaf !== "boolean")).toEqual([]);
      expect(JSON.stringify(state.box).includes(CANARY)).toBe(false);
    }
  });

  test("test_that_what_was_added_was_read_by_itself_is_said_only_where_words_of_it_were_not_read", () => {
    // A reading that asks for no new ranking ends where it is answered.
    const added = (data: typeof read) =>
      after(...first, ...more, { type: "read_answered", data, meta: A }, { type: "settled" });

    // Nothing of what was added could be read, or a part of it could not.
    expect(unread.unread.length).toBeGreaterThan(0);
    expect(readApart(added(unread))).toBe(true);
    expect(noticed.unread.length).toBeGreaterThan(0);
    expect(readApart(added(noticed))).toBe(true);
    // All of it was read: there is nothing to explain.
    expect(second.unread).toEqual([]);
    expect(readApart(added(second))).toBe(false);
  });

  test("test_it_is_not_said_of_a_first_sentence_nor_once_the_box_has_changed_nor_while_words_are_read", () => {
    const answered = (data: typeof read): SearchEvent[] => [{ type: "read_answered", data, meta: A }, { type: "settled" }];
    const alone = after(typed(15, 0), sent(15, 1), ...answered(unread));
    const added = after(...first, ...more, ...answered(unread));

    // Nothing stood before a first sentence.
    expect(readApart(alone)).toBe(false);
    expect(readApart(added)).toBe(true);
    expect(readApart(reduce(added, typed(1, 27)))).toBe(false);
    expect(readApart(after(...first, ...more))).toBe(false);
    // Nor while a model still reads what the rules left unread.
    const pending = { ...unread, model_pending: true };
    expect(readApart(after(...first, ...more, ...answered(pending)))).toBe(false);
    expect(readApart(opened())).toBe(false);
  });
});

describe("the store", () => {
  test("test_an_event_is_applied_at_once_so_the_next_read_sees_it", () => {
    const store = createStore(opened());
    const seen: SearchState[] = [];
    store.subscribe(() => seen.push(store.getState()));

    store.dispatch({ type: "selected", areaId: "syn-n0006" });

    expect(store.getState().selectedId).toBe("syn-n0006");
    expect(seen).toHaveLength(1);
  });

  test("test_an_event_that_changes_nothing_tells_nobody", () => {
    const store = createStore(opened());
    const told = jest.fn();
    store.subscribe(told);

    store.dispatch({ type: "hovered", areaId: null });
    store.dispatch({ type: "settled" });

    expect(told).not.toHaveBeenCalled();
  });

  test("test_a_listener_that_has_left_is_told_no_more", () => {
    const store = createStore(opened());
    const told = jest.fn();
    const leave = store.subscribe(told);

    leave();
    store.dispatch({ type: "selected", areaId: "syn-n0006" });

    expect(told).not.toHaveBeenCalled();
  });
});
