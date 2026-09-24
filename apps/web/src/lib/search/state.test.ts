import { recordedAnswer } from "@/lib/api/recorded";
import type { Failure } from "@/lib/api/failure";

import { edits, merged, NO_EDITS } from "./edits";
import { refusals, refusedByPart } from "./refusals";
import {
  failureOfTheCards,
  gaveWayBetween,
  initialState,
  movedBetween,
  reasonsAreIn,
  reasonsFailure,
  reduce,
  type SearchEvent,
  type SearchState,
} from "./state";
import { createStore } from "./store";

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
    reduce(before, { type: "queued", operations: edits.tagOn("waterside") });
    reduce(before, { type: "failed", step: "rank", failure: timeout });

    expect(JSON.stringify(before)).toBe(copy);
  });

  test("test_the_spec_changes_only_when_the_api_returns_one", () => {
    const changing = new Set<SearchEvent["type"]>();
    const events: SearchEvent[] = [
      { type: "tenure_swapped", tenure: "buy" },
      { type: "queued", operations: edits.tagOn("leafy") },
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: read, meta: A },
      { type: "rank_started", seq: 2 },
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A },
      { type: "share_answered", id: SHARE_ID, data: shared, meta: A },
      { type: "explain_failed", hash: ranked.spec_hash, failure: timeout },
      { type: "settled" },
      { type: "failed", step: "rank", failure: timeout },
      { type: "stopped" },
      { type: "place_named", placeId: "syn-p0021", name: "Cindermoor Works" },
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
      const next = reduce({ ...before, untouched: event.type === "tenure_swapped" }, event);
      if (next.spec !== before.spec) changing.add(event.type);
    }

    // A default the API served is swapped in before anything is asked for, and on starting again.
    expect([...changing].sort()).toEqual(
      ["rank_answered", "read_answered", "share_answered", "started_again", "tenure_swapped"].sort(),
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
      { type: "queued", operations: edits.tagOn("waterside") },
      { type: "rank_started", seq: 2 },
      { type: "failed", step: "rank", failure: timeout },
    );

    expect(state.phase).toBe("results");
    expect(state.ranking?.ranked).toBe(ranked.ranked);
    expect(state.pending).toEqual(edits.tagOn("waterside"));
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
      { type: "place_named", placeId: "syn-p0021", name: "Cindermoor Works" },
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
      { type: "explain_answered", data: explained, hash: ranked.spec_hash, meta: B },
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
      { type: "explain_answered", data: explained, hash: ranked.spec_hash, meta: A },
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

  test("test_a_place_is_named_from_the_fact_of_its_journey", () => {
    const explained = recordedAnswer("explain_top", "explanations-first").body.data;

    const state = after({ type: "explain_answered", data: explained, hash: ranked.spec_hash, meta: A });

    expect(state.placeNames).toEqual({ "syn-p0021": "Cindermoor Works" });
  });
});

describe("reasons that come before the ranking they are for", () => {
  const reasons = recordedAnswer("explain_top", "explanations-first").body.data;
  const later = recordedAnswer("explain_top", "explanations-refined").body.data;
  const shown = () =>
    after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A },
    );

  test("test_the_reasons_on_screen_stay_until_the_ranking_the_new_ones_are_for_has_come", () => {
    const state = reduce(shown(), { type: "explain_answered", data: later, hash: refined.spec_hash, meta: A });

    expect(state.explanations).toBe(reasons.explanations);
    expect(state.explainedHash).toBe(ranked.spec_hash);
    expect(state.explainedHash).toBe(state.rankedHash);
    // What the new reasons cite is kept, so that they have their sources when their turn comes.
    for (const fact of later.facts) expect(state.facts[fact.fact_id]).toBe(fact);
  });

  test("test_the_reasons_that_waited_are_the_rankings_when_it_comes", () => {
    const state = reduce(
      reduce(shown(), { type: "explain_answered", data: later, hash: refined.spec_hash, meta: A }),
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A },
    );

    expect(state.explanations).toBe(later.explanations);
    expect(state.explainedHash).toBe(refined.spec_hash);
    expect(state.explanationsAhead).toBeNull();
  });

  test("test_a_ranking_that_fails_leaves_the_list_the_reasons_it_has", () => {
    const state = reduce(
      reduce(shown(), { type: "explain_answered", data: later, hash: refined.spec_hash, meta: A }),
      { type: "failed", step: "rank", failure: timeout },
    );

    expect(state.explanations).toBe(reasons.explanations);
    expect(state.explainedHash).toBe(state.rankedHash);
  });

  test("test_reasons_that_waited_for_another_ranking_are_not_given_to_this_one", () => {
    const state = reduce(
      reduce(shown(), { type: "explain_answered", data: later, hash: "a".repeat(64), meta: A }),
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A },
    );

    expect(state.explanations).toBe(reasons.explanations);
    expect(state.explainedHash).not.toBe(state.rankedHash);
    expect(state.explanationsAhead).toBeNull();
  });

  test("test_the_first_reasons_of_a_search_are_shown_as_soon_as_they_come", () => {
    const state = after({ type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A });

    expect(state.explanations).toBe(reasons.explanations);
    expect(state.explanationsAhead).toBeNull();
  });

  test("test_reasons_for_the_ranking_on_screen_take_the_place_of_ones_that_were_not", () => {
    const mismatched = after(
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A },
    );

    const state = reduce(mismatched, { type: "explain_answered", data: later, hash: refined.spec_hash, meta: A });

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
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A },
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
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: other },
    );

    expect(state.explainedHash).toBe(state.rankedHash);
    expect(reasonsAreIn(state)).toBe(false);
  });

  test("test_reasons_that_came_first_are_not_the_reasons_of_a_ranking_another_release_made", () => {
    const state = after(
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A },
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: B },
    );

    expect(reasonsAreIn(state)).toBe(false);
    expect(state.explanations).toEqual([]);
  });

  test("test_reasons_of_another_release_wait_and_the_reasons_on_screen_stay", () => {
    const later = recordedAnswer("explain_top", "explanations-refined").body.data;
    const shown = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A },
    );

    const waiting = reduce(shown, { type: "explain_answered", data: later, hash: refined.spec_hash, meta: B });
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
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A },
      { type: "explain_answered", data: later, hash: refined.spec_hash, meta: A },
      { type: "rank_answered", data: refined, sent: NO_EDITS, meta: B },
    );

    expect(reasonsAreIn(state)).toBe(false);
    expect(state.explanationsAhead).toBeNull();
  });

  test("test_a_fact_of_the_rankings_release_is_not_given_up_for_one_of_another", () => {
    const shown = after(
      { type: "rank_answered", data: ranked, sent: NO_EDITS, meta: A },
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A },
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
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A },
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
      { type: "explain_answered", data: reasons, hash: ranked.spec_hash, meta: A },
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
      hash: second.spec_hash,
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
    });
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
      { type: "place_named", placeId: "syn-p0021", name: "Cindermoor Works" },
      { type: "queued", operations: edits.tagOn("waterside") },
      { type: "selected", areaId: "syn-n0006" },
    );

    const state = reduce(before, { type: "share_answered", id: SHARE_ID, data: shared, meta: A });

    expect(state.read).toBeNull();
    expect(state.placeNames).toEqual({});
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
  test("test_a_tenure_said_in_words_is_said_though_the_spec_still_calls_it_a_default", () => {
    // Seen in a browser: "Renting assumed" after the person typed "Renting". The API leaves
    // `tenure_from` at `default` when the tenure said is the one the spec already had.
    const state = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: read, meta: A });

    expect(read.operations.budget_ops[0]).toMatchObject({ tenure: "rent", provenance: "stated" });
    expect(read.spec.tenure_from).toBe("default");
    expect(opened().tenureSaid).toBe(false);
    expect(state.tenureSaid).toBe(true);
  });

  test("test_a_tenure_nobody_said_is_not_said", () => {
    const notice = recordedAnswer("interpret", "interpret-notice").body.data;
    const state = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: notice, meta: A });

    expect(notice.operations.budget_ops).toEqual([]);
    expect(state.tenureSaid).toBe(false);
  });

  test("test_a_tenure_chosen_with_a_control_is_said", () => {
    expect(reduce(opened(), { type: "tenure_swapped", tenure: "buy" }).tenureSaid).toBe(true);
    expect(reduce(opened(), { type: "queued", operations: edits.tenure("buy") }).tenureSaid).toBe(true);
    expect(reduce(opened(), { type: "queued", operations: edits.budgetAmount(1500) }).tenureSaid).toBe(false);
  });

  test("test_a_tenure_that_words_changed_without_saying_it_is_no_longer_said", () => {
    const said = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: read, meta: A });
    const inferred = {
      ...read,
      operations: { ...NO_EDITS, budget_ops: [{ ...edits.tenure("buy").budget_ops[0]!, provenance: "inferred" as const }] },
      spec: { ...meta.defaults.buy, tenure_from: "inferred" as const },
    };

    const state = reduce(said, { type: "read_answered", data: inferred, meta: A });

    expect(state.tenureSaid).toBe(false);
  });

  test("test_stop_puts_back_whether_the_tenure_was_said", () => {
    const state = after(
      { type: "read_started", seq: 1 },
      { type: "read_answered", data: read, meta: A },
      { type: "stopped" },
    );

    expect(state.tenureSaid).toBe(false);
  });

  test("test_starting_again_and_a_shared_search_say_nothing_of_the_tenure", () => {
    const said = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: read, meta: A });

    expect(reduce(said, { type: "started_again" }).tenureSaid).toBe(false);
    expect(reduce(said, { type: "share_answered", id: SHARE_ID, data: shared, meta: A }).tenureSaid).toBe(false);
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
});

describe("a service that cannot be reached", () => {
  const network: Failure = { ...timeout, kind: "network" };
  const notSet: Failure = { ...timeout, kind: "not_configured" };

  test("test_words_that_never_reached_burro_are_not_said_to_be_unreadable", () => {
    // Seen in a browser, with the API stopped: "Your words could not be read just now. The
    // settings below do the same job." The settings could not work either.
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

describe("where the words of a sentence stand", () => {
  test("test_which_words_each_edit_rests_on_is_kept_as_offsets_and_never_as_words", () => {
    const state = after({ type: "read_started", seq: 1 }, { type: "read_answered", data: read, meta: A });

    expect(state.read?.rests_on).toBe(read.rests_on);
    expect(read.rests_on.length).toBeGreaterThan(0);
    for (const where of state.read?.rests_on ?? []) {
      expect(Object.keys(where).sort()).toEqual(["end", "group", "index", "start"]);
      expect(typeof where.start).toBe("number");
      expect(typeof where.end).toBe("number");
    }
  });
});

describe("how much a ranking moved", () => {
  const scores = (...ids: string[]) => ({ ...ranked, scores: ids.map((area_id) => ({ area_id, score: 1 })) });

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
  const safe = recordedAnswer("interpret", "interpret-rejected").body.data;
  const asked = recordedAnswer("interpret", "interpret-clarify").body.data;
  const readOf = (data: typeof safe) => after({ type: "read_answered", data, meta: A }).read;

  test("test_each_refusal_is_tied_to_the_part_its_edit_was_about", () => {
    expect(refusals(readOf(safe), null)).toEqual([
      { key: "feature:crime_violence_robbery", reason: "crime_needs_explicit_request" },
      { key: "feature:crime_burglary_theft", reason: "crime_needs_explicit_request" },
    ]);
  });

  test("test_a_refusal_that_a_question_stands_for_is_not_said_twice", () => {
    expect(asked.rejected).toEqual([{ group: "commute_ops", index: 0, reason: "unknown_place" }]);
    expect(refusals(readOf(asked), null)).toEqual([]);
  });

  test("test_what_a_control_sent_is_said_at_the_control_and_what_words_made_is_not", () => {
    const refused = {
      operations: merged(edits.tagOn("leafy"), edits.budgetAmount(1)),
      rejected: [{ group: "budget_ops", index: 0, reason: "out_of_range" }] as const,
    };

    expect([...refusedByPart(refused)]).toEqual([["budget", "out_of_range"]]);
    expect([...refusedByPart(null)]).toEqual([]);
    expect(refusals(readOf(safe), refused)).toHaveLength(3);
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
