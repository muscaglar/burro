import { recordedAnswer, recordedError, responseFrom } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";

import { setOnline, standInApi, withTheSpecSent, type StandIn } from "../../../test/support/api";
import { problemsWith } from "../../../test/support/contract";
import { edits, merged, NO_EDITS } from "./edits";
import { createFlow } from "./flow";
import { failureOfTheCards, initialState, reasonsAreIn, reasonsFailure, type SearchState } from "./state";
import { createStore } from "./store";

// A string found nowhere else, planted in what a person types.
const CANARY = "zqxcanary7431";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = {
  read: recordedAnswer("interpret", "interpret-first").body.data,
  rank: recordedAnswer("rank", "rank-first").body.data,
  explain: recordedAnswer("explain_top", "explanations-first").body.data,
};

function open(api: StandIn) {
  const store = createStore(initialState(meta, areas));
  const seen: SearchState[] = [store.getState()];
  store.subscribe(() => seen.push(store.getState()));
  const flow = createFlow({ client: api.client, ...store });
  return { store, flow, seen, state: () => store.getState() };
}

/** A stand-in that answers a first search as it was recorded. */
function firstSearch(): StandIn {
  return standInApi()
    .on("interpret", "interpret-first")
    .on("rank", "rank-first")
    .on("explain_top", "explanations-first");
}

/** Lets what is already on its way arrive. */
const arrived = async (turns = 20) => {
  for (let turn = 0; turn < turns; turn += 1) await new Promise((resolve) => setTimeout(resolve, 0));
};

/** The release a service moves to, after the page was built on the recorded one. */
const NEWER = "syn-2026-10-01-01";

/** Every spec found anywhere in a value. */
function specsIn(value: unknown, found: PreferenceSpec[] = []): PreferenceSpec[] {
  if (Array.isArray(value)) value.forEach((part) => specsIn(part, found));
  else if (typeof value === "object" && value !== null) {
    if ("schema_version" in value) found.push(value as PreferenceSpec);
    else Object.values(value).forEach((part) => specsIn(part, found));
  }
  return found;
}

beforeEach(() => setOnline(true));
afterEach(() => jest.useRealTimers());

describe("sending a sentence", () => {
  test("test_a_sentence_is_read_then_ranked_and_explained_and_the_first_five_are_fetched", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);

    await flow.submitText("Renting a 1 bed, leafy and quiet");

    expect(api.calls.map((call) => call.operation)).toEqual([
      "interpret",
      "explain_top",
      "rank",
      ...Array<string>(5).fill("get_area"),
    ]);
    expect(api.lastCallTo("rank").body).toEqual({ spec: first.read.spec, limit: 20 });
    expect(api.lastCallTo("explain_top").body).toEqual({ spec: first.read.spec, limit: 5 });
    expect(api.callsTo("get_area").map((call) => call.path)).toEqual(
      first.rank.ranked.slice(0, 5).map((area) => {
        const slug = areas.find((known) => known.area_id === area.area_id)?.slug;
        return `/v1/areas/${slug}`;
      }),
    );
    expect(state().phase).toBe("results");
    expect(state().spec).toEqual(first.read.spec);
    expect(state().ranking?.ranked).toEqual(first.rank.ranked);
    expect(state().explanations).toEqual(first.explain.explanations);
    expect(state().explainedHash).toBe(state().rankedHash);
    expect(Object.keys(state().details)).toHaveLength(5);
    expect(api.unexpected).toEqual([]);
  });

  test("test_a_first_sentence_is_sent_with_the_default_the_api_served", async () => {
    const api = firstSearch();
    const { flow } = open(api);

    await flow.submitText("leafy");

    expect(api.lastCallTo("interpret").body).toEqual({ text: "leafy", spec: meta.defaults.rent });
    expect(problemsWith("InterpretBody", api.lastCallTo("interpret").body)).toEqual([]);
    expect(problemsWith("RankBody", api.lastCallTo("rank").body)).toEqual([]);
    expect(problemsWith("ExplanationsBody", api.lastCallTo("explain_top").body)).toEqual([]);
  });

  test("test_a_second_sentence_is_sent_with_the_spec_the_first_one_left", async () => {
    const api = firstSearch();
    const { flow } = open(api);
    await flow.submitText("leafy and quiet");
    api.on("interpret", "interpret-second-sentence");

    await flow.submitText("a bit more green space");

    expect(api.lastCallTo("interpret").body).toMatchObject({ spec: first.rank.spec });
  });

  test("test_a_line_of_spaces_is_not_sent", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);

    await flow.submitText("   ");

    expect(api.calls).toEqual([]);
    expect(state().phase).toBe("empty");
  });

  test("test_the_page_says_it_is_reading_until_the_ranking_is_in", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { flow, state, seen } = open(api);

    const sent = flow.submitText("leafy");
    expect(state().phase).toBe("interpreting");
    reading.release();
    await sent;

    expect(seen.map((one) => one.phase).filter((phase, at, all) => phase !== all[at - 1])).toEqual([
      "empty",
      "interpreting",
      "results",
    ]);
  });

  test("test_the_chips_can_be_drawn_before_the_ranking_is_in", async () => {
    const api = firstSearch();
    const ranking = api.hold("rank", "rank-first");
    const { flow, state } = open(api);

    const sent = flow.submitText("leafy");
    while (ranking.waiting() === 0) await new Promise((resolve) => setTimeout(resolve, 0));

    expect(state().spec).toEqual(first.read.spec);
    expect(state().read?.interpreter).toBe("rule");
    expect(state().ranking).toBeNull();
    ranking.release();
    await sent;
    expect(state().ranking).not.toBeNull();
  });
});

describe("what is kept of what a person typed", () => {
  test("test_the_store_holds_no_sentence", async () => {
    const api = firstSearch();
    const { flow, seen } = open(api);

    await flow.submitText(`leafy and quiet near ${CANARY}`);
    await flow.searchPlaces(CANARY);

    expect(seen.length).toBeGreaterThan(5);
    expect(JSON.stringify(seen)).not.toContain(CANARY);
  });

  test("test_typed_text_travels_only_in_a_post_body", async () => {
    const api = firstSearch().on("search_places", "places-search");
    const { flow } = open(api);

    await flow.submitText(`leafy and quiet near ${CANARY}`);
    await flow.searchPlaces(CANARY);
    await flow.applyEdits(edits.tagOn("waterside"));

    const holding = api.calls.filter((call) => JSON.stringify([call.url, call.sent, call.init.headers]).includes(CANARY));
    expect(holding.map((call) => [call.operation, call.method])).toEqual([
      ["interpret", "POST"],
      ["search_places", "POST"],
    ]);
    for (const call of api.calls) {
      expect(call.url).not.toContain(CANARY);
      expect(JSON.stringify(call.init.headers)).not.toContain(CANARY);
    }
  });

  test("test_the_spec_is_only_ever_one_the_api_returned", async () => {
    const api = firstSearch();
    const { flow, seen } = open(api);
    await flow.submitText("leafy and quiet");
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await flow.applyEdits(edits.placeStrictness("syn-p0021", "hard"));
    api.on("rank", "rank-rejected-edit");
    await flow.applyEdits(edits.budgetAmount(1));

    const served = [
      meta.defaults.rent,
      meta.defaults.buy,
      ...["interpret-first", "rank-first", "rank-refined", "rank-rejected-edit"].flatMap(
        (scenario) => specsIn(recordedAnswer(scenario.startsWith("rank") ? "rank" : "interpret", scenario).body),
      ),
    ].map((spec) => JSON.stringify(spec));

    const held = seen.map((state) => JSON.stringify(state.spec));
    expect(new Set(held).size).toBeGreaterThan(2);
    expect(held.filter((spec) => !served.includes(spec))).toEqual([]);
    // And every spec that was sent is one that was held.
    const sent = api.calls.flatMap((call) => specsIn(call.body)).map((spec) => JSON.stringify(spec));
    expect(sent.filter((spec) => !held.includes(spec))).toEqual([]);
  });
});

describe("moving a control", () => {
  async function searched() {
    const api = firstSearch();
    const opened = open(api);
    await opened.flow.submitText("leafy and quiet");
    api.calls.length = 0;
    return { api, ...opened };
  }

  test("test_a_control_sends_its_one_edit_with_the_last_spec_returned", async () => {
    const { api, flow, state } = await searched();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    const edit = edits.placeStrictness("syn-p0021", "hard");

    await flow.applyEdits(edit);

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toEqual({
      spec: first.rank.spec,
      operations: edit,
      limit: 20,
    });
    const refined = recordedAnswer("rank", "rank-refined").body.data;
    expect(state().spec).toEqual(refined.spec);
    expect(state().pending).toEqual(NO_EDITS);
    // The reasons are asked for again, for the spec that came back.
    expect(api.lastCallTo("explain_top").body).toEqual({ spec: refined.spec, limit: 5 });
    expect(state().explainedHash).toBe(refined.spec_hash);
    expect(api.unexpected).toEqual([]);
  });

  test("test_the_reasons_are_not_asked_for_again_when_the_spec_did_not_change", async () => {
    const { api, flow } = await searched();
    api.on("rank", "rank-rejected-edit");

    await flow.applyEdits(edits.budgetAmount(1));

    expect(api.callsTo("explain_top")).toEqual([]);
    expect(api.callsTo("get_area")).toEqual([]);
  });

  test("test_a_refused_edit_leaves_the_spec_as_it_was_and_says_why", async () => {
    const { api, flow, state } = await searched();
    api.on("rank", "rank-rejected-edit");
    const edit = edits.budgetAmount(1);

    await flow.applyEdits(edit);

    expect(state().spec).toEqual(first.rank.spec);
    expect(state().refused).toEqual({
      operations: edit,
      rejected: [{ group: "budget_ops", index: 0, reason: "out_of_range" }],
    });
    expect(state().phase).toBe("results");
  });

  test("test_edits_made_while_a_call_is_out_are_sent_together_so_none_is_lost", async () => {
    const { api, flow, state } = await searched();
    const slow = api.hold("rank", "rank-refined");
    const one = edits.tagWeight("leafy", 0.4);
    const two = edits.placeStrictness("syn-p0021", "hard");

    const firstEdit = flow.applyEdits(one);
    while (slow.waiting() === 0) await Promise.resolve();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    const secondEdit = flow.applyEdits(two);
    slow.release();
    await Promise.all([firstEdit, secondEdit]);

    const sent = api.callsTo("rank").map((call) => (call.body as { operations: Operations }).operations);
    expect(sent).toEqual([one, merged(one, two)]);
    // Both were sent with the spec the API last returned: the website applied neither.
    for (const call of api.callsTo("rank")) expect(call.body).toMatchObject({ spec: first.rank.spec });
    expect(api.callsTo("rank")[0]?.init.signal?.aborted).toBe(true);
    expect(state().pending).toEqual(NO_EDITS);
    expect(state().phase).toBe("results");
  });

  test("test_an_older_answer_is_dropped_when_a_later_request_was_made", async () => {
    const { api, flow, state } = await searched();
    // The first answer was already on its way when it was stopped, and comes in last.
    const old = api.late("rank", "rank-nothing-matches", "rank-refined");
    api.on("explain_top", "explanations-refined");

    const firstEdit = flow.applyEdits(edits.tagWeight("leafy", 0.4));
    await flow.applyEdits(edits.placeStrictness("syn-p0021", "hard"));
    expect(old.waiting()).toBe(1);
    old.release();
    await firstEdit;

    expect(api.callsTo("rank")).toHaveLength(2);
    expect(state().ranking?.ranked).toEqual(recordedAnswer("rank", "rank-refined").body.data.ranked);
    expect(state().seq).toBe(3);
  });

  test("test_an_edit_made_while_a_sentence_is_read_is_sent_with_the_spec_the_reading_returns", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { flow, state } = open(api);
    const edit = edits.tagOn("waterside");

    const sent = flow.submitText("leafy and quiet");
    const edited = flow.applyEdits(edit);
    expect(api.callsTo("rank")).toEqual([]);
    reading.release();
    await Promise.all([sent, edited]);

    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toEqual({
      spec: first.read.spec,
      operations: edit,
      limit: 20,
    });
    expect(state().pending).toEqual(NO_EDITS);
  });

  test("test_the_live_region_is_told_how_many_areas_changed_place", async () => {
    const { api, flow, state } = await searched();
    expect(state().moved).toBeNull();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await flow.applyEdits(edits.placeStrictness("syn-p0021", "hard"));

    const before = first.rank.scores.map((score) => score.area_id);
    const after = recordedAnswer("rank", "rank-refined").body.data.scores.map((score) => score.area_id);
    // An area that went moves no other. What moved is counted among the areas ranked both times.
    const stayed = before.filter((id) => after.includes(id));
    const moved = after.filter((id) => before.includes(id)).filter((id, at) => stayed[at] !== id).length;
    expect(before.length - after.length).toBe(11);
    expect(moved).toBeGreaterThan(0);
    expect(state().moved).toBe(moved);
    expect(state().rankedBefore).toBe(before.length);
  });

  test("test_the_first_wish_makes_the_settings_nobody_chose_count_for_less", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);

    await flow.submitText("leafy and quiet");

    expect(state().gaveWay).toBe(true);
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await flow.applyEdits(edits.placeStrictness("syn-p0021", "hard"));
    // They give way once. A later edit does not say so again.
    expect(state().gaveWay).toBe(false);
  });
});

describe("before anything is asked for", () => {
  test("test_rent_or_buy_swaps_the_default_and_sends_nothing", async () => {
    const api = standInApi();
    const { flow, state } = open(api);

    await flow.setTenure("buy");

    expect(api.calls).toEqual([]);
    expect(state().spec).toBe(meta.defaults.buy);
    await flow.setTenure("rent");
    expect(state().spec).toBe(meta.defaults.rent);
    expect(state().phase).toBe("empty");
  });

  test("test_after_a_search_rent_or_buy_is_an_edit_like_any_other", async () => {
    const api = firstSearch();
    const { flow } = open(api);
    await flow.submitText("leafy");
    api.on("rank", "rank-buyer-family").on("explain_top", "explanations-buyer-family");

    await flow.setTenure("buy");

    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.tenure("buy") });
  });

  test("test_the_settings_can_be_ranked_as_they_stand_with_no_words", async () => {
    const api = standInApi().on("rank", "rank-default-rent").on("explain_top", "explanations-first");
    const { flow, state } = open(api);

    await flow.rankNow();

    expect(api.callsTo("interpret")).toEqual([]);
    expect(api.lastCallTo("rank").body).toEqual({ spec: meta.defaults.rent, limit: 20 });
    expect(state().phase).toBe("results");
    expect(state().untouched).toBe(false);
  });

  test("test_a_place_added_by_hand_is_an_edit_and_its_name_is_kept_for_the_chip", async () => {
    const api = standInApi().on("rank", "rank-first").on("explain_top", "explanations-first");
    const { flow, state } = open(api);

    await flow.addPlace({ place_id: "syn-p0012", name: "Pellam Cross" });

    expect(api.lastCallTo("rank").body).toEqual({
      spec: meta.defaults.rent,
      operations: edits.placeAdd("syn-p0012"),
      limit: 20,
    });
    expect(state().placeNames["syn-p0012"]).toBe("Pellam Cross");
  });
});

describe("when the words cannot be read", () => {
  test("test_a_reading_that_takes_too_long_leaves_the_form_with_the_defaults", async () => {
    jest.useFakeTimers();
    const api = standInApi().silent("interpret");
    const { flow, state } = open(api);

    const sent = flow.submitText("leafy");
    await jest.advanceTimersByTimeAsync(8_000);
    await sent;

    expect(state().failure?.kind).toBe("timeout");
    expect(state().failedStep).toBe("read");
    expect(state().degraded).toBe(true);
    expect(state().settingsOpen).toBe(true);
    expect(state().phase).toBe("empty");
    expect(state().spec).toBe(meta.defaults.rent);
  });

  test("test_words_that_never_reached_burro_are_not_said_to_be_unreadable_and_can_be_sent_again", async () => {
    // Seen in a browser, with the API stopped: the page blamed the words and pointed at the
    // settings, which could not reach Burro either.
    const api = standInApi().unreachable("interpret").on("rank", "rank-first").on("explain_top", "explanations-first");
    const { flow, state } = open(api);

    await flow.submitText("leafy");

    expect(state().failure?.kind).toBe("network");
    expect(state().failedStep).toBe("read");
    expect(state().degraded).toBe(false);
    expect(state().settingsOpen).toBe(false);

    // Once Burro can be reached, "Try again" sends the same words from the box.
    api.on("interpret", "interpret-first");
    await flow.retry("leafy");
    expect(api.callsTo("interpret").map((call) => (call.body as { text: string }).text)).toEqual(["leafy", "leafy"]);
    expect(state().failure).toBeNull();
    expect(state().phase).toBe("results");
  });

  test.each([
    ["the service has a fault", (api: StandIn) => api.on("interpret", "error-internal"), "api"],
    ["the answer is not the api's", (api: StandIn) => api.on("interpret", () => new Response("<html>")), "unreadable"],
  ])("test_the_form_works_when_interpretation_fails: %s", async (_, breakIt, kind) => {
    const api = breakIt(standInApi()).on("rank", "rank-first").on("explain_top", "explanations-first");
    const { flow, state } = open(api);

    await flow.submitText("leafy");

    expect(state().failure?.kind).toBe(kind);
    expect(state().degraded).toBe(true);
    expect(state().settingsOpen).toBe(true);

    // The same controls still work, with no model and no words.
    await flow.applyEdits(edits.tagOn("leafy"));
    expect(state().phase).toBe("results");
    expect(state().failure).toBeNull();
    expect(state().ranking?.ranked.length).toBeGreaterThan(0);
  });

  test("test_words_read_by_the_rules_when_the_model_fails_are_ranked_as_usual", async () => {
    const api = firstSearch().on("interpret", "interpret-degraded");
    const { flow, state } = open(api);

    await flow.submitText("leafy");

    expect(state().degraded).toBe(true);
    expect(state().settingsOpen).toBe(true);
    expect(state().failure).toBeNull();
    expect(state().phase).toBe("results");
  });

  test("test_trying_again_sends_the_sentence_it_is_given_because_none_is_kept", async () => {
    const api = standInApi().unreachable("interpret");
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    api.on("interpret", "interpret-first").on("rank", "rank-first").on("explain_top", "explanations-first");

    await flow.retry("leafy");

    expect(api.callsTo("interpret")).toHaveLength(2);
    expect(state().phase).toBe("results");
    expect(state().failure).toBeNull();
  });

  test("test_a_refusal_of_the_words_is_shown_as_the_apis_own_and_is_not_a_failure_to_read", async () => {
    const api = standInApi().on("interpret", "interpret-invalid-text");
    const { flow, state } = open(api);

    await flow.submitText("x");

    const refusal = recordedError("interpret-invalid-text").body.error;
    expect(state().failure).toMatchObject({ kind: "api", code: "invalid_text", message: refusal.message });
    expect(state().degraded).toBe(false);
  });

  test("test_nothing_read_asks_for_no_new_ranking_and_keeps_what_is_on_screen", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    const before = state().ranking;
    api.calls.length = 0;
    api.on("interpret", "interpret-nothing-read");

    await flow.submitText("what is the best way to learn the piano");

    expect(api.calls.map((call) => call.operation)).toEqual(["interpret"]);
    expect(state().ranking).toBe(before);
    expect(state().phase).toBe("results");
    expect(state().read?.unmet).toEqual(["other"]);
    expect(state().settingsOpen).toBe(true);
  });
});

describe("stopping", () => {
  test("test_stop_ends_the_request_and_returns_to_the_state_before", async () => {
    const api = standInApi().silent("interpret");
    const { flow, state } = open(api);

    const sent = flow.submitText("leafy");
    expect(state().phase).toBe("interpreting");
    flow.stop();
    await sent;

    expect(api.lastCallTo("interpret").init.signal?.aborted).toBe(true);
    expect(state().phase).toBe("empty");
    expect(state().failure).toBeNull();
    expect(state().degraded).toBe(false);
  });

  test("test_stop_after_a_search_leaves_its_results_on_screen", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    api.silent("interpret");

    const sent = flow.submitText("and quiet");
    flow.stop();
    await sent;

    expect(state().phase).toBe("results");
    expect(state().ranking?.ranked).toEqual(first.rank.ranked);
  });
});

describe("stopping after the words were read", () => {
  async function readAndHeld() {
    const api = firstSearch();
    const opened = open(api);
    await opened.flow.submitText("leafy and quiet");
    const before = opened.state();
    api.on("interpret", "interpret-second-sentence").on("explain_top", "explanations-second-sentence");
    const ranking = api.late("rank", "rank-second-sentence", "rank-second-sentence");
    const sent = opened.flow.submitText("a bit more green space");
    while (ranking.waiting() === 0) await arrived(1);
    return { api, ...opened, before, ranking, sent };
  }

  test("test_stop_is_still_offered_while_the_ranking_of_the_words_is_worked_out", async () => {
    const { state, ranking, sent } = await readAndHeld();

    // The words are read, and the chips are drawn from them already.
    expect(state().phase).toBe("interpreting");
    expect(state().specHash).toBe(recordedAnswer("interpret", "interpret-second-sentence").body.data.spec_hash);
    ranking.release();
    await sent;
  });

  test("test_stop_puts_the_search_back_as_it_was_and_the_late_ranking_changes_nothing", async () => {
    const { api, flow, state, before, ranking, sent } = await readAndHeld();

    flow.stop();
    // The ranking was already on its way, and comes after all.
    ranking.release();
    await sent;
    await arrived();

    expect(state().phase).toBe("results");
    expect(state().spec).toBe(before.spec);
    expect(state().specHash).toBe(state().rankedHash);
    expect(state().rankedHash).toBe(first.rank.spec_hash);
    expect(state().read).toBe(before.read);
    expect(state().assumed).toBe(before.assumed);
    expect(state().ranking).toBe(before.ranking);
    expect(reasonsAreIn(state())).toBe(true);
    expect(state().explanationsAhead).toBeNull();
    expect([state().failure, state().pending]).toEqual([null, NO_EDITS]);
    expect(api.callsTo("rank")).toHaveLength(2);
    expect(api.unexpected).toEqual([]);
  });

  test("test_the_next_sentence_after_stop_is_sent_with_the_spec_that_was_put_back", async () => {
    const { api, flow, before, ranking, sent } = await readAndHeld();
    flow.stop();
    ranking.release();
    await sent;
    api.on("rank", "rank-second-sentence");

    await flow.submitText("a bit more green space");

    expect(api.lastCallTo("interpret").body).toMatchObject({ spec: before.spec });
  });

  test("test_an_edit_made_meanwhile_is_sent_after_stop_with_the_spec_that_was_put_back", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy and quiet");
    const before = state();
    const reading = api.hold("interpret", "interpret-second-sentence");
    api.on("explain_top", "explanations-second-sentence");
    const ranking = api.late("rank", "rank-second-sentence", "rank-refined");
    const edit = edits.placeStrictness("syn-p0021", "hard");

    const sent = flow.submitText("a bit more green space");
    const edited = flow.applyEdits(edit);
    reading.release();
    while (ranking.waiting() === 0) await arrived(1);
    api.on("explain_top", "explanations-refined");
    flow.stop();
    ranking.release();
    await Promise.all([sent, edited]);
    await arrived();

    // The sentence is undone, and the control that was moved is not.
    expect(api.callsTo("rank").at(-1)?.body).toEqual({ spec: before.spec, operations: edit, limit: 20 });
    expect(state().spec).toEqual(recordedAnswer("rank", "rank-refined").body.data.spec);
    expect(state().specHash).toBe(state().rankedHash);
    expect(state().pending).toEqual(NO_EDITS);
  });

  test("test_stop_on_a_first_search_leaves_the_page_as_it_opened", async () => {
    const api = firstSearch();
    const ranking = api.late("rank", "rank-first", "rank-first");
    const { flow, state } = open(api);

    const sent = flow.submitText("leafy");
    while (ranking.waiting() === 0) await arrived(1);
    flow.stop();
    ranking.release();
    await sent;
    await arrived();

    expect(state().phase).toBe("empty");
    expect(state().spec).toBe(meta.defaults.rent);
    expect([state().read, state().ranking, state().specHash]).toEqual([null, null, null]);
    expect(state().explanations).toEqual([]);
  });
});

describe("a control moved while a sentence is being read", () => {
  test("test_the_edit_is_sent_when_the_reading_fails_so_it_is_not_lost_with_the_words", async () => {
    const api = standInApi().on("rank", "rank-first").on("explain_top", "explanations-first");
    const reading = api.hold("interpret", "error-internal");
    const { flow, state } = open(api);
    const edit = edits.tagOn("leafy");

    const sent = flow.submitText("leafy");
    await flow.applyEdits(edit);
    expect(api.callsTo("rank")).toEqual([]);
    reading.release();
    await sent;

    expect(api.lastCallTo("rank").body).toEqual({ spec: meta.defaults.rent, operations: edit, limit: 20 });
    expect(state().pending).toEqual(NO_EDITS);
    expect(state().phase).toBe("results");
    // The words were still not read, and the page still says so.
    expect(state().degraded).toBe(true);
  });

  test("test_the_edit_is_sent_when_the_reading_is_stopped", async () => {
    const api = standInApi().silent("interpret").on("rank", "rank-first").on("explain_top", "explanations-first");
    const { flow, state } = open(api);
    const edit = edits.tagOn("leafy");

    const sent = flow.submitText("leafy");
    await flow.applyEdits(edit);
    flow.stop();
    await sent;
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edit });
    expect(state().pending).toEqual(NO_EDITS);
  });

  test("test_stopping_with_nothing_waiting_sends_nothing", async () => {
    const api = standInApi().silent("interpret");
    const { flow } = open(api);

    const sent = flow.submitText("leafy");
    flow.stop();
    await sent;

    expect(api.callsTo("rank")).toEqual([]);
  });
});

describe("a question about a place", () => {
  const asked = recordedAnswer("interpret", "interpret-clarify").body.data;

  test("test_the_rest_is_ranked_while_the_question_stands", async () => {
    const api = firstSearch().on("interpret", "interpret-clarify");
    const { flow, state } = open(api);

    await flow.submitText("leafy, 30 minutes to somewhere");

    expect(state().read?.clarify).toEqual(asked.clarify);
    expect(state().phase).toBe("results");
    expect(api.lastCallTo("rank").body).toEqual({ spec: asked.spec, limit: 20 });
  });

  test("test_the_answer_sends_the_edit_asked_about_with_the_place_picked", async () => {
    const api = firstSearch().on("interpret", "interpret-clarify");
    const { flow, state } = open(api);
    await flow.submitText("leafy, 30 minutes to somewhere");
    const [question] = asked.clarify;
    const option = question?.options[0];
    if (!question || !option) throw new Error("the recording holds no question");

    await flow.answerClarify(question, option);

    expect(api.lastCallTo("rank").body).toMatchObject({
      operations: {
        ...NO_EDITS,
        commute_ops: [{ ...asked.operations.commute_ops[0], place_id: option.id }],
      },
    });
    expect(state().read?.clarify).toEqual([]);
    // The refusal the question stood for goes with it.
    expect(state().read?.rejected).toEqual([]);
    expect(state().placeNames[option.id]).toBe(option.name);
    // What was assumed of the journey is assumed of the place chosen.
    expect(state().assumed[`place:${option.id}`]).toEqual(["mode", "strictness"]);
  });

  test("test_leaving_it_out_sends_nothing", async () => {
    const api = firstSearch().on("interpret", "interpret-clarify");
    const { flow, state } = open(api);
    await flow.submitText("leafy, 30 minutes to somewhere");
    api.calls.length = 0;
    const [question] = asked.clarify;
    if (!question) throw new Error("the recording holds no question");

    flow.leaveOut(question);

    expect(api.calls).toEqual([]);
    expect(state().read?.clarify).toEqual([]);
  });

  test("test_a_question_with_nothing_else_read_shows_the_question_and_ranks_nothing", async () => {
    const onlyAQuestion = recordedAnswer("interpret", "interpret-clarify-no-options");
    const body = {
      ...onlyAQuestion.body,
      data: {
        ...onlyAQuestion.body.data,
        applied: onlyAQuestion.body.data.applied.map((edit) => ({ ...edit, changed: false })),
        spec: meta.defaults.rent,
      },
    };
    const api = standInApi().on("interpret", () => responseFrom({ ...onlyAQuestion, body }));
    const { flow, state } = open(api);

    await flow.submitText("I work somewhere");

    expect(api.callsTo("rank")).toEqual([]);
    expect(state().phase).toBe("empty");
    expect(state().read?.clarify).toHaveLength(1);
    expect(state().settingsOpen).toBe(false);
  });
});

describe("what the API reads and does not apply", () => {
  test("test_the_neutral_notice_is_kept_word_for_word_and_the_rest_is_ranked", async () => {
    const notice = recordedAnswer("interpret", "interpret-notice").body.data;
    const api = firstSearch().on("interpret", "interpret-notice");
    const { flow, state } = open(api);

    await flow.submitText("quiet and leafy");

    expect(state().read?.notice).toBe("neutral_places");
    expect(state().read?.notice_text).toBe(notice.notice_text);
    expect(state().phase).toBe("results");
    expect(api.lastCallTo("rank").body).toMatchObject({ spec: notice.spec });
  });

  test("test_what_was_assumed_is_kept_by_the_part_it_was_assumed_of", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);

    await flow.submitText("leafy and quiet");

    expect(state().assumed).toEqual({
      budget: ["strictness"],
      "place:syn-p0021": ["mode", "strictness"],
    });
  });

  test("test_an_assumption_goes_when_the_person_sets_that_part_themselves", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy and quiet");
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await flow.applyEdits(edits.placeStrictness("syn-p0021", "hard"));

    expect(state().assumed).toEqual({
      budget: ["strictness"],
      "place:syn-p0021": ["mode"],
    });
  });
});

describe("when ranking fails", () => {
  test("test_a_fault_keeps_the_last_results_and_the_edit_that_was_not_applied", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    api.on("rank", "error-internal");
    const edit = edits.tagOn("waterside");

    await flow.applyEdits(edit);

    const fault = recordedError("error-internal");
    expect(state().failure).toMatchObject({
      kind: "api",
      status: 500,
      message: fault.body.error.message,
      requestId: fault.headers["x-request-id"],
    });
    expect(state().failedStep).toBe("rank");
    expect(state().phase).toBe("results");
    expect(state().ranking?.ranked).toEqual(first.rank.ranked);
    expect(state().pending).toEqual(edit);

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await flow.retry();
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edit });
    expect(state().failure).toBeNull();
    expect(state().pending).toEqual(NO_EDITS);
  });

  test("test_a_spec_that_names_something_gone_is_told_apart_by_its_code_and_paths", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    api.on("rank", "rank-stale-spec");

    await flow.applyEdits(edits.tagOn("waterside"));

    expect(state().failure).toMatchObject({
      kind: "api",
      code: "unknown_place",
      fields: [{ path: "spec.commutes[1].place_id", problem: "unknown_place" }],
    });
  });

  test("test_reasons_that_cannot_be_loaded_do_not_take_the_ranking_away", async () => {
    const api = firstSearch().on("explain_top", "error-internal");
    const { flow, state } = open(api);

    await flow.submitText("leafy");

    expect(state().phase).toBe("results");
    expect(state().failure).toBeNull();
    expect(reasonsFailure(state())).not.toBeNull();
    expect(state().ranking?.ranked).toEqual(first.rank.ranked);
  });

  test("test_reasons_that_cannot_be_loaded_keep_the_apis_message_and_the_id_to_quote", async () => {
    const api = firstSearch().on("explain_top", "error-internal");
    const { flow, state } = open(api);

    await flow.submitText("leafy");

    const fault = recordedError("error-internal");
    expect(fault.headers["x-request-id"]).toBeTruthy();
    expect(failureOfTheCards(state())).toMatchObject({
      kind: "api",
      status: 500,
      code: "internal_error",
      message: fault.body.error.message,
      requestId: fault.headers["x-request-id"],
    });
    // It was asked for once. A failure is said, and is not tried again behind the person's back.
    expect(api.callsTo("explain_top")).toHaveLength(1);
  });

  test("test_trying_again_brings_the_reasons_that_could_not_be_loaded", async () => {
    const api = firstSearch().on("explain_top", "error-internal");
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    api.calls.length = 0;
    api.on("explain_top", "explanations-first");

    await flow.retry();

    expect(api.callsTo("explain_top")).toHaveLength(1);
    expect(api.lastCallTo("explain_top").body).toEqual({ spec: first.rank.spec, limit: 5 });
    expect(reasonsAreIn(state())).toBe(true);
    expect(state().explanations).toEqual(first.explain.explanations);
    expect(failureOfTheCards(state())).toBeNull();
    // The profiles were in hand, and are not asked for again.
    expect(api.callsTo("get_area")).toEqual([]);
    expect(state().phase).toBe("results");
    expect(api.unexpected).toEqual([]);
  });

  test("test_a_profile_that_cannot_be_loaded_is_marked_and_the_rest_are_kept", async () => {
    const api = firstSearch().on("get_area", (call) =>
      call.path.endsWith("/farrowmere")
        ? responseFrom(recordedError("area-not-found"))
        : responseFrom(recordedAnswer("get_area", `area/${call.path.split("/").pop()}`)),
    );
    const { flow, state } = open(api);

    await flow.submitText("leafy");

    expect(Object.keys(state().detailFailures)).toEqual(["syn-n0006"]);
    expect(Object.keys(state().details)).toHaveLength(4);
    // The failure is kept whole, with the API's own words for it.
    const refusal = recordedError("area-not-found");
    expect(failureOfTheCards(state())).toMatchObject({
      kind: "api",
      code: "area_not_found",
      message: refusal.body.error.message,
      requestId: refusal.headers["x-request-id"],
    });
  });

  test("test_trying_again_asks_for_the_profile_that_failed_and_for_no_other", async () => {
    const api = firstSearch().on("get_area", (call) =>
      call.path.endsWith("/farrowmere")
        ? responseFrom(recordedError("error-internal"))
        : responseFrom(recordedAnswer("get_area", `area/${call.path.split("/").pop()}`)),
    );
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    expect(Object.keys(state().detailFailures)).toEqual(["syn-n0006"]);
    api.calls.length = 0;
    api.on("get_area", (call) => responseFrom(recordedAnswer("get_area", `area/${call.path.split("/").pop()}`)));

    await flow.retry();

    expect(api.callsTo("get_area").map((call) => call.path)).toEqual(["/v1/areas/farrowmere"]);
    expect(state().detailFailures).toEqual({});
    expect(Object.keys(state().details)).toHaveLength(5);
    expect(failureOfTheCards(state())).toBeNull();
  });

  test("test_reasons_that_could_not_leave_are_asked_for_again_when_the_browser_is_back", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    // The connection goes between a ranking and its reasons.
    api.on("rank", "rank-refined").on("explain_top", () => {
      setOnline(false);
      throw new TypeError("Failed to fetch");
    });
    await flow.applyEdits(edits.placeStrictness("syn-p0021", "hard"));
    expect(state().rankedHash).toBe(recordedAnswer("rank", "rank-refined").body.data.spec_hash);
    expect(reasonsFailure(state())).toMatchObject({ kind: "offline" });
    expect(state().online).toBe(false);

    setOnline(true);
    api.on("rank", withTheSpecSent("rank-refined")).on("explain_top", "explanations-refined");
    await flow.wentOnline();

    expect(state().online).toBe(true);
    expect(reasonsAreIn(state())).toBe(true);
    expect(failureOfTheCards(state())).toBeNull();
  });

  test("test_nothing_matches_is_a_ranking_with_nobody_in_it_and_no_reasons_are_asked_for", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    api.calls.length = 0;
    api.on("rank", "rank-nothing-matches");

    await flow.applyEdits(edits.budgetStrictness("hard"));

    expect(state().phase).toBe("results");
    expect(state().ranking?.ranked).toEqual([]);
    expect(state().ranking?.filtered.length).toBeGreaterThan(0);
    expect(api.callsTo("explain_top")).toEqual([]);
    expect(api.callsTo("get_area")).toEqual([]);
  });
});

describe("offline", () => {
  test("test_an_edit_made_offline_waits_and_is_sent_once_when_the_browser_is_back", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    api.calls.length = 0;
    const edit = edits.tagOn("waterside");

    setOnline(false);
    flow.wentOffline();
    await flow.applyEdits(edit);

    expect(api.calls).toEqual([]);
    expect(state().online).toBe(false);
    expect(state().failure?.kind).toBe("offline");
    expect(state().pending).toEqual(edit);
    expect(state().ranking?.ranked).toEqual(first.rank.ranked);

    setOnline(true);
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await flow.wentOnline();
    await flow.wentOnline();

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edit });
    expect(state().online).toBe(true);
    expect(state().failure).toBeNull();
    expect(state().pending).toEqual(NO_EDITS);
  });

  test("test_coming_back_online_with_nothing_waiting_sends_nothing", async () => {
    const api = firstSearch();
    const { flow } = open(api);
    await flow.submitText("leafy");
    api.calls.length = 0;

    flow.wentOffline();
    await flow.wentOnline();

    expect(api.calls).toEqual([]);
  });
});

describe("a release that changes while the page is open", () => {
  test("test_the_form_and_the_areas_are_read_again_once", async () => {
    const api = firstSearch().movedTo(NEWER).on("interpret", () => responseFrom(recordedAnswer("interpret", "interpret-first")));
    const { flow, state } = open(api);

    await flow.submitText("leafy");
    await flow.rankNow();
    await arrived();

    expect(api.callsTo("get_meta")).toHaveLength(1);
    expect(api.callsTo("list_areas")).toHaveLength(1);
    expect(state().meta.release_id).toBe(NEWER);
  });

  test("test_a_first_search_after_a_release_keeps_its_reasons_and_profiles_when_the_form_comes_last", async () => {
    // Every static page is kept for an hour, so after each release every visitor's first
    // search finds a newer release than its page was built on. The form is read again
    // beside the search, and is the largest thing asked for: it may well come last.
    const api = firstSearch().movedTo(NEWER);
    const slow = api.hold("get_meta", "meta");
    const { flow, state } = open(api);

    await flow.submitText("leafy");
    expect(state().explanations).toHaveLength(5);
    expect(Object.keys(state().details)).toHaveLength(5);
    const facts = Object.keys(state().facts).length;
    expect(facts).toBeGreaterThan(50);

    slow.release();
    await arrived();

    expect(state().meta.release_id).toBe(NEWER);
    expect(state().explanations).toHaveLength(5);
    expect(reasonsAreIn(state())).toBe(true);
    expect(Object.keys(state().details)).toHaveLength(5);
    expect(Object.keys(state().facts)).toHaveLength(facts);
    expect(failureOfTheCards(state())).toBeNull();
    // Nothing had to be asked for a second time.
    expect(api.callsTo("explain_top")).toHaveLength(1);
    expect(api.callsTo("get_area")).toHaveLength(5);
    expect(api.unexpected).toEqual([]);
  });

  test("test_a_first_search_after_a_release_has_its_reasons_and_profiles_when_the_form_comes_first", async () => {
    const api = firstSearch().movedTo(NEWER);
    const ranking = api.hold("rank", "rank-first");
    const { flow, state } = open(api);

    const sent = flow.submitText("leafy");
    while (ranking.waiting() === 0) await arrived(1);
    await arrived();
    expect(state().meta.release_id).toBe(NEWER);
    ranking.release();
    await sent;

    expect(state().explanations).toHaveLength(5);
    expect(reasonsAreIn(state())).toBe(true);
    expect(Object.keys(state().details)).toHaveLength(5);
  });

  test("test_a_search_on_screen_gets_the_profiles_of_the_new_release_when_its_ranking_moves_to_it", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    expect(Object.values(state().detailsBy).map((by) => by.release_id)).toEqual(Array(5).fill(meta.release_id));
    api.calls.length = 0;

    // The service moves to a newer release. The next edit is answered by it.
    api.movedTo(NEWER).on("rank", "rank-rejected-edit");
    await flow.applyEdits(edits.budgetAmount(1));
    await arrived();

    // The spec did not change, so neither did its hash. The release did, and what the cards hold with it.
    expect(state().rankedHash).toBe(first.rank.spec_hash);
    expect(api.callsTo("explain_top")).toHaveLength(1);
    expect(api.callsTo("get_area")).toHaveLength(5);
    expect(reasonsAreIn(state())).toBe(true);
    expect(state().explainedBy?.release_id).toBe(NEWER);
    expect(Object.values(state().detailsBy).map((by) => by.release_id)).toEqual(Array(5).fill(NEWER));
    expect(new Set(Object.values(state().factsBy).map((by) => by.release_id))).toEqual(new Set([NEWER]));
  });

  test("test_the_form_is_read_again_on_the_next_answer_when_reading_it_failed", async () => {
    const api = firstSearch().movedTo(NEWER).on("get_meta", "error-internal");
    const { flow, state } = open(api);

    await flow.submitText("leafy");
    await arrived();
    expect(state().meta.release_id).toBe(meta.release_id);
    // The search is whole all the same: nothing of it waits on the form.
    expect(reasonsAreIn(state())).toBe(true);

    api.on("get_meta", "meta");
    await flow.rankNow();
    await arrived();

    expect(api.callsTo("get_meta")).toHaveLength(2);
    expect(state().meta.release_id).toBe(NEWER);
  });

  test("test_the_form_is_not_asked_for_twice_while_it_is_being_read", async () => {
    const api = firstSearch().movedTo(NEWER);
    const slow = api.hold("get_meta", "meta");
    const { flow, state } = open(api);

    // Two answers name the newer release before the form has come: the reading, and the ranking.
    await flow.submitText("leafy");
    expect(slow.waiting()).toBe(1);
    slow.release();
    await arrived();

    expect(api.callsTo("get_meta")).toHaveLength(1);
    expect(state().meta.release_id).toBe(NEWER);
  });

  test("test_boundaries_that_could_not_be_read_again_are_asked_for_on_the_next_answer", async () => {
    const api = firstSearch().movedTo(NEWER).on("get_geometry", "error-internal");
    const { flow, state } = open(api);
    await flow.submitText("leafy");
    await arrived();
    expect(state().meta.release_id).toBe(NEWER);
    expect(state().geometry).toBeNull();

    api.on("get_geometry", "geometry");
    await flow.rankNow();
    await arrived();

    expect(state().geometry?.features).toHaveLength(areas.length);
  });
});

describe("which release made what is on screen", () => {
  test("test_the_release_of_every_answer_of_a_search_is_kept_with_it", async () => {
    const { flow, state } = open(firstSearch());

    await flow.submitText("leafy");

    const by = { release_id: meta.release_id, engine_version: meta.engine_version };
    expect(state().read?.by).toEqual(by);
    expect(state().rankedBy).toEqual(by);
    expect(state().explainedBy).toEqual(by);
    expect(Object.values(state().detailsBy)).toEqual(Array(5).fill(by));
  });

  test("test_reasons_made_by_another_release_than_the_ranking_are_asked_for_once_more", async () => {
    // The release moved between the ranking and its reasons, as it can while a service is replaced.
    const onTheNewer = standInApi().movedTo(NEWER).on("explain_top", "explanations-first");
    const api = firstSearch().inTurn("explain_top", (call) => onTheNewer.fetch(call.url, call.init), "explanations-first");
    const { flow, state } = open(api);

    await flow.submitText("leafy");

    expect(api.callsTo("explain_top")).toHaveLength(2);
    expect(reasonsAreIn(state())).toBe(true);
    expect(state().explainedBy).toEqual(state().rankedBy);
    expect(failureOfTheCards(state())).toBeNull();
  });

  test("test_reasons_that_are_still_another_releases_are_said_to_have_failed_and_never_shown", async () => {
    const onTheNewer = standInApi().movedTo(NEWER).on("explain_top", "explanations-first");
    const api = firstSearch().on("explain_top", (call) => onTheNewer.fetch(call.url, call.init));
    const { flow, state } = open(api);

    await flow.submitText("leafy");

    // The hashes agree, as they must: a hash is of the spec alone.
    expect(state().explainedHash).toBe(state().rankedHash);
    expect(reasonsAreIn(state())).toBe(false);
    // The cards are not left waiting for ever: the reasons are said not to have come.
    expect(failureOfTheCards(state())).toMatchObject({ kind: "unreadable" });
    expect(api.callsTo("explain_top")).toHaveLength(2);

    // Trying again ranks again, so that the ranking and its reasons come from one release.
    api.movedTo(NEWER).on("explain_top", "explanations-first");
    api.calls.length = 0;
    await flow.retry();
    await arrived();

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(state().rankedBy?.release_id).toBe(NEWER);
    expect(reasonsAreIn(state())).toBe(true);
    expect(failureOfTheCards(state())).toBeNull();
  });
});

describe("the list and the map", () => {
  test("test_an_area_chosen_in_one_is_chosen_in_the_other", () => {
    const { flow, state } = open(standInApi());

    flow.select("syn-n0006");
    flow.hover("syn-n0003");

    expect(state().selectedId).toBe("syn-n0006");
    expect(state().hoveredId).toBe("syn-n0003");
    flow.hover(null);
    flow.select(null);
    expect([state().selectedId, state().hoveredId]).toEqual([null, null]);
  });

  test("test_the_boundaries_are_fetched_once_and_a_failure_is_said", async () => {
    const api = standInApi();
    const { flow, state } = open(api);

    await flow.loadGeometry();
    await flow.loadGeometry();

    expect(api.callsTo("get_geometry")).toHaveLength(1);
    expect(state().geometry?.features).toHaveLength(areas.length);

    const broken = open(standInApi().unreachable("get_geometry"));
    await broken.flow.loadGeometry();
    expect(broken.state().geometryFailed).toBe(true);
  });
});

describe("a second sentence whose ranking fails", () => {
  test("test_the_first_rankings_reasons_stay_on_the_cards", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy and quiet");
    const shown = state().explanations;
    api.on("interpret", "interpret-second-sentence").on("rank", "error-internal");

    await flow.submitText("and near the water");

    // The ranking on screen is the first one's, and so are its reasons.
    expect(state().failure).toMatchObject({ kind: "api", code: "internal_error" });
    expect(state().ranking?.ranked).toEqual(first.rank.ranked);
    expect(state().explanations).toBe(shown);
    expect(state().explainedHash).toBe(state().rankedHash);
  });

  test("test_trying_again_brings_the_second_rankings_own_reasons", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy and quiet");
    api.on("interpret", "interpret-second-sentence").on("rank", "error-internal");
    await flow.submitText("and near the water");
    const second = recordedAnswer("interpret", "interpret-second-sentence").body.data;

    api.on("rank", withTheSpecSent("rank-refined")).on("explain_top", "explanations-refined");
    await flow.retry();

    expect(state().failure).toBeNull();
    expect(state().rankedHash).toBe(recordedAnswer("rank", "rank-refined").body.data.spec_hash);
    expect(state().explainedHash).toBe(state().rankedHash);
    expect(api.lastCallTo("rank").body).toMatchObject({ spec: second.spec });
  });
});

describe("sharing a search", () => {
  const made = recordedAnswer("create_share", "share-made");

  test("test_a_share_is_made_of_the_spec_the_api_last_returned_and_nothing_else", async () => {
    const api = firstSearch().on("create_share", "share-made");
    const { flow, state } = open(api);
    await flow.submitText(`leafy and quiet ${CANARY}`);

    const answer = await flow.createShare(false);

    expect(api.lastCallTo("create_share").body).toEqual({ spec: state().spec, exact_destinations: false });
    expect(problemsWith("ShareBody", api.lastCallTo("create_share").body)).toEqual([]);
    expect(api.lastCallTo("create_share").sent?.includes(CANARY)).toBe(false);
    expect(answer.ok && answer.data.share_id).toBe(made.body.data.share_id);
  });

  test("test_the_exact_places_are_shared_only_when_the_person_asks", async () => {
    const api = firstSearch().on("create_share", "share-made-exact");
    const { flow } = open(api);

    await flow.createShare(false);
    await flow.createShare(true);

    expect(api.callsTo("create_share").map((call) => (call.body as { exact_destinations: boolean }).exact_destinations)).toEqual([
      false,
      true,
    ]);
  });

  test("test_making_a_share_changes_nothing_of_the_search", async () => {
    const api = firstSearch().on("create_share", "share-made");
    const { flow, state } = open(api);
    await flow.submitText("leafy and quiet");
    const before = JSON.stringify(state());

    await flow.createShare(false);

    // The stored spec may name other places than the search does. The search keeps its own.
    expect(JSON.stringify(state())).toBe(before);
    expect(JSON.stringify(state()).includes(made.body.data.share_id)).toBe(false);
  });

  test("test_a_share_that_cannot_be_made_is_a_failure_and_never_a_throw", async () => {
    const { flow } = open(standInApi().on("create_share", "error-internal"));

    const answer = await flow.createShare(false);

    expect(answer.ok).toBe(false);
    expect(!answer.ok && answer.failure.kind === "api" && answer.failure.code).toBe("internal_error");
  });
});

describe("opening a shared search", () => {
  const opened = recordedAnswer("get_share", "share-opened");
  const ID = opened.request.path.split("/").pop() ?? "";
  const sharing = () => standInApi().on("get_share", "share-opened").on("explain_top", "explanations-first");

  test("test_a_share_is_opened_by_its_id_then_explained_and_the_first_five_are_fetched", async () => {
    const api = sharing();
    const { flow, state } = open(api);

    const failure = await flow.openShare(ID);

    expect(failure).toBeNull();
    expect(api.calls.map((call) => call.operation)).toEqual([
      "get_share",
      ...Array<string>(5).fill("get_area"),
      "explain_top",
    ]);
    expect(api.lastCallTo("get_share").path).toBe(`/v1/shares/${ID}`);
    expect(api.lastCallTo("get_share").sent).toBeNull();
    expect(api.lastCallTo("explain_top").body).toEqual({ spec: opened.body.data.spec, limit: 5 });
    expect(state().phase).toBe("results");
    expect(state().spec).toEqual(opened.body.data.spec);
    expect(state().specHash).toBe(opened.body.data.spec_hash);
    expect(state().ranking?.ranked).toEqual(opened.body.data.ranked);
    expect(state().rankedHash).toBe(opened.body.data.spec_hash);
    expect(state().untouched).toBe(false);
    expect(api.unexpected).toEqual([]);
  });

  test("test_what_the_api_said_of_the_share_is_kept_with_the_search", async () => {
    const { flow, state } = open(sharing());

    await flow.openShare(ID);

    expect(state().shared).toEqual({
      id: ID,
      coarsened: true,
      stale: false,
      original_release_id: opened.body.data.original_release_id,
    });
  });

  test("test_the_search_that_was_open_gives_way_whole_to_the_one_the_link_holds", async () => {
    const api = firstSearch().on("interpret", "interpret-clarify").on("get_share", "share-opened");
    const { flow, state } = open(api);
    await flow.submitText("leafy and quiet, 30 minutes to the works");
    await flow.addPlace({ place_id: "syn-p0777", name: `${CANARY} Works` });
    flow.select("syn-n0006");
    expect(state().read).not.toBeNull();
    expect(state().placeNames["syn-p0777"]).toBe(`${CANARY} Works`);

    await flow.openShare(ID);

    // Not a question, not an assumption and not a name of the search before is carried over.
    expect(state().read).toBeNull();
    expect(state().assumed).toEqual({});
    expect(JSON.stringify(state()).includes(CANARY)).toBe(false);
    expect(state().selectedId).toBeNull();
    expect(state().pending).toEqual(NO_EDITS);
    expect(state().moved).toBeNull();
  });

  test("test_a_share_that_is_opened_can_be_refined_like_any_search", async () => {
    const api = sharing().on("rank", "rank-refined").on("explain_top", "explanations-refined");
    const { flow, state } = open(api);
    await flow.openShare(ID);

    await flow.applyEdits(edits.tagOn("waterside"));

    expect(api.lastCallTo("rank").body).toEqual({
      spec: opened.body.data.spec,
      operations: edits.tagOn("waterside"),
      limit: 20,
    });
    // It came from a link, and still says so after it is changed.
    expect(state().shared?.id).toBe(ID);
  });

  test("test_starting_again_forgets_that_the_search_came_from_a_link", async () => {
    const { flow, state } = open(sharing());
    await flow.openShare(ID);

    flow.startAgain();

    expect(state().shared).toBeNull();
    expect(state().spec).toBe(meta.defaults.rent);
  });

  test.each([
    ["share-not-found", "share_not_found", 404],
    ["share-gone", "release_changed", 410],
    ["error-internal", "internal_error", 500],
  ])("test_a_share_that_cannot_be_opened_answers_with_the_apis_failure: %s", async (scenario, code, status) => {
    const api = firstSearch().on("get_share", scenario);
    const { flow, state } = open(api);
    await flow.submitText("leafy and quiet");
    const before = state();

    const failure = await flow.openShare(ID);

    expect(failure).toMatchObject({ kind: "api", code, status, message: recordedError(scenario).body.error.message });
    // The search that was open is left exactly as it was.
    expect(state()).toBe(before);
  });

  test("test_a_share_that_cannot_be_reached_answers_with_why", async () => {
    const { flow, state } = open(standInApi().unreachable("get_share"));

    expect(await flow.openShare(ID)).toMatchObject({ kind: "network" });
    expect(state().shared).toBeNull();
    expect(state().phase).toBe("empty");
  });

  test("test_a_stale_share_is_ranked_again_and_says_it_is_stale", async () => {
    const stale = recordedAnswer("get_share", "share-opened-stale");
    const { flow, state } = open(standInApi().on("get_share", "share-opened-stale").on("explain_top", "explanations-first"));

    await flow.openShare(stale.request.path.split("/").pop() ?? "");

    expect(state().shared).toMatchObject({ stale: true, coarsened: false });
    expect(state().ranking?.ranked).toHaveLength(20);
  });

  test("test_a_share_opened_on_a_release_that_has_moved_on_still_gets_its_reasons", async () => {
    const stale = recordedAnswer("get_share", "share-opened-stale");
    // The service that holds the newer release answers every call as that release.
    const api = standInApi()
      .movedTo(stale.body.meta.release_id)
      .on("get_share", "share-opened-stale")
      .on("explain_top", "explanations-first");
    const { flow, state } = open(api);

    await flow.openShare(stale.request.path.split("/").pop() ?? "");

    // The answer names another release than the page was built on, so the form is read again.
    expect(stale.body.meta.release_id).not.toBe(meta.release_id);
    expect(api.callsTo("get_meta")).toHaveLength(1);
    expect(state().meta.release_id).toBe(stale.body.meta.release_id);
    // The share's own reasons come, and stay.
    expect(reasonsAreIn(state())).toBe(true);
    expect(state().explanations).toHaveLength(5);
    expect(Object.keys(state().details)).toHaveLength(5);
    expect(state().rankedBy?.release_id).toBe(stale.body.meta.release_id);
  });

  test("test_the_id_of_a_share_is_sent_in_the_path_of_one_call_and_in_no_other", async () => {
    const api = sharing().on("rank", "rank-refined").on("explain_top", "explanations-refined");
    const { flow } = open(api);

    await flow.openShare(ID);
    await flow.applyEdits(edits.tagOn("waterside"));

    const naming = api.calls.filter((call) => `${call.url} ${call.sent ?? ""}`.includes(ID));
    expect(naming.map((call) => call.operation)).toEqual(["get_share"]);
  });
});
