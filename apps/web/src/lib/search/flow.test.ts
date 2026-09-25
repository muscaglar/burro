import { recordedAnswer, recordedError, responseFrom } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";

import { landed, setOnline, standInApi, withTheSpecSent, type StandIn } from "../../../test/support/api";
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

/** A search whose page has opened: the service has said who reads what is typed. */
function open(api: StandIn, reader: SearchState["reader"] = meta.reader) {
  const store = createStore(initialState(meta, areas, null, reader));
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

/**
 * Lets what is already on its way arrive: so many turns, and then every answer that the
 * stand-in has been asked for and has not yet given. An answer that a test holds back is
 * not waited for.
 */
const arrived = async (turns = 20) => {
  for (let turn = 0; turn < turns; turn += 1) await new Promise((resolve) => setTimeout(resolve, 0));
  await landed();
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

describe("who reads what is typed", () => {
  const byAModel = recordedAnswer("get_meta", "meta-model-reads").body.data.reader;

  test("test_the_page_asks_the_service_who_reads_and_takes_nothing_from_what_it_was_built_on", async () => {
    // The page was built while the rules read. The service has since been set to a model.
    const api = standInApi().on("get_meta", "meta-model-reads");
    const { flow, state } = open(api, null);

    expect(meta.reader.model_reads).toBe(false);
    expect(state().reader).toBeNull();
    await flow.loadReader();

    expect(state().reader).toEqual(byAModel);
    expect(state().reader?.model_reads).toBe(true);
    // It is asked for once. What it said stands until the service says otherwise.
    await flow.loadReader();
    expect(api.callsTo("get_meta")).toHaveLength(1);
    expect(api.calls.map((call) => call.sent)).toEqual([null]);
  });

  test("test_no_sentence_is_sent_before_the_service_has_said_who_reads_it", async () => {
    const api = firstSearch();
    const asked = api.hold("get_meta", "meta-model-reads");
    const { flow, state } = open(api, null);

    const sent = flow.submitText(`leafy ${CANARY}`);
    await arrived();

    // The sentence waits. Nothing that holds it has left.
    expect(api.calls.map((call) => call.operation)).toEqual(["get_meta"]);
    expect(api.calls.some((call) => call.sent?.includes(CANARY))).toBe(false);
    asked.release();
    await sent;

    expect(state().reader).toEqual(byAModel);
    expect(api.calls.map((call) => call.operation).slice(0, 2)).toEqual(["get_meta", "interpret"]);
    expect(api.callsTo("interpret")).toHaveLength(1);
  });

  test("test_a_sentence_is_not_sent_where_the_service_cannot_say_who_reads_it", async () => {
    const api = firstSearch().unreachable("get_meta");
    const { flow, state } = open(api, null);

    await flow.submitText(`leafy ${CANARY}`);

    expect(api.callsTo("interpret")).toEqual([]);
    expect(api.calls.some((call) => call.sent?.includes(CANARY))).toBe(false);
    expect(state().reader).toBeNull();
    expect(state().readerFailed).toBe(true);
    // The page says that Burro could not be reached, and does not blame the words.
    expect(state().failure?.kind).toBe("network");
    expect(state().failedStep).toBe("read");
    expect(state().phase).toBe("empty");
  });

  test("test_the_service_is_asked_again_by_the_next_sentence_once_it_can_say", async () => {
    const api = firstSearch().inTurn("get_meta", "error-internal", "meta");
    const { flow, state } = open(api, null);

    await flow.submitText("leafy");
    expect(api.callsTo("interpret")).toEqual([]);
    await flow.submitText("leafy");

    expect(state().reader).toEqual(meta.reader);
    expect(state().readerFailed).toBe(false);
    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(state().phase).toBe("results");
  });

  test("test_a_sentence_that_is_stopped_while_the_service_is_asked_is_never_sent", async () => {
    const api = firstSearch();
    const asked = api.hold("get_meta", "meta");
    const { flow, state } = open(api, null);

    const sent = flow.submitText(`leafy ${CANARY}`);
    await arrived();
    flow.stop();
    asked.release();
    await sent;
    await arrived();

    expect(api.callsTo("interpret")).toEqual([]);
    expect(state().phase).toBe("empty");
    expect(state().failure).toBeNull();
  });

  test("test_what_the_service_said_is_kept_when_the_search_is_started_again", async () => {
    const { flow, state } = open(firstSearch().on("get_meta", "meta-model-reads"), null);
    await flow.loadReader();
    await flow.submitText("leafy");

    flow.startAgain();

    expect(state().phase).toBe("empty");
    expect(state().reader).toEqual(byAModel);
  });

  test("test_a_form_read_again_for_a_newer_release_says_who_reads_now", async () => {
    // A service that moved to another release was started again, and may be set otherwise.
    const api = firstSearch().movedTo(NEWER).on("get_meta", "meta-model-reads");
    const { flow, state } = open(api);

    expect(state().reader?.model_reads).toBe(false);
    await flow.submitText("leafy");
    await arrived();

    expect(state().meta.release_id).toBe(NEWER);
    expect(state().reader?.model_reads).toBe(true);
  });
});

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

    // The rules are asked first, and answer at once. "leafy" is plain, so no model is asked at all.
    expect(api.callsTo("interpret").map((call) => call.body)).toEqual([
      { text: "leafy", spec: meta.defaults.rent, ask_model: false },
    ]);
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
    await flow.applyEdits(edits.tagOn("parks_close_by"));

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
    const edit = edits.tagOn("parks_close_by");

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

  test("test_a_place_added_by_hand_is_an_edit_and_the_answer_names_the_place", async () => {
    const api = standInApi().on("rank", "rank-first").on("explain_top", "explanations-first");
    const { flow, state } = open(api);

    await flow.addPlace({ place_id: "syn-p0021" });

    expect(api.lastCallTo("rank").body).toEqual({
      spec: meta.defaults.rent,
      operations: edits.placeAdd("syn-p0021"),
      limit: 20,
    });
    // The name on the chip is the release's own, from the answer that brought the spec.
    expect(first.rank.places).toEqual([{ place_id: "syn-p0021", name: "Cindermoor Works", kind: "district" }]);
    expect(state().placeNames).toEqual({ "syn-p0021": "Cindermoor Works" });
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
    // The edit waits until the ranking it was sent with has been answered.
    await arrived();

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
    const edit = edits.tagOn("parks_close_by");

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

    await flow.applyEdits(edits.tagOn("parks_close_by"));

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
    const edit = edits.tagOn("parks_close_by");

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
    // The form was asked for, and could not be read. How often turns on which answer of the
    // search came after the failure, which is no part of what is held here.
    const failed = api.callsTo("get_meta").length;
    expect(failed).toBeGreaterThanOrEqual(1);

    api.on("get_meta", "meta");
    await flow.rankNow();
    await arrived();

    expect(api.callsTo("get_meta")).toHaveLength(failed + 1);
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
    api
      .on("interpret", "interpret-second-sentence")
      .on("explain_top", "explanations-second-sentence")
      .on("rank", "error-internal");

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
  const sharing = () =>
    standInApi().on("get_share", "share-opened").on("explain_top", "explanations-share-opened");

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
    // The ranking names a place, as the release names it: here, by a name found nowhere else.
    api.on("rank", () => {
      const ranked = recordedAnswer("rank", "rank-first");
      const places = [{ place_id: "syn-p0021", name: `${CANARY} Works`, kind: "district" }];
      return { ...ranked, body: { ...ranked.body, data: { ...ranked.body.data, places } } };
    });
    await flow.addPlace({ place_id: "syn-p0021" });
    flow.select("syn-n0006");
    expect(state().read).not.toBeNull();
    expect(state().placeNames["syn-p0021"]).toBe(`${CANARY} Works`);
    api.on("explain_top", "explanations-share-opened");

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

    await flow.applyEdits(edits.tagOn("parks_close_by"));

    expect(api.lastCallTo("rank").body).toEqual({
      spec: opened.body.data.spec,
      operations: edits.tagOn("parks_close_by"),
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
    await flow.applyEdits(edits.tagOn("parks_close_by"));

    const naming = api.calls.filter((call) => `${call.url} ${call.sent ?? ""}`.includes(ID));
    expect(naming.map((call) => call.operation)).toEqual(["get_share"]);
  });
});

describe("a prompt that is not plain", () => {
  const noticed = recordedAnswer("interpret", "interpret-suggest").body.data;
  const chosen = recordedAnswer("rank", "rank-suggestion-chosen");
  const long = recordedAnswer("interpret", "interpret-by-model-long");
  // The long sentence holds eleven offers. One press may add five of them: two wishes, the culture,
  // the journey and the budget. The six readings of two words are the person's to choose.
  const EVERY_OFFER = long.body.data.suggestions.map((_, at) => at);
  const ONE_PRESS_ADDS = [0, 1, 6, 10, 11];
  const LEFT_TO_CHOOSE = [
    "Mix of brands",
    "Gritty",
    "What homes sell for",
    "Homes in the higher council tax bands",
    "Village feel",
    "Age of buildings",
    "Nearer a town centre",
  ];
  const typedOf = (recorded: { request: { body?: unknown } }) => (recorded.request.body as { text: string }).text;
  const suggesting = () =>
    standInApi()
      .on("interpret", "interpret-suggest")
      .on("rank", "rank-suggestion-chosen")
      .on("explain_top", "explanations-suggestion-chosen");
  /** A service with a model behind it: the rules answer at once, and then the model. */
  const reading = () =>
    standInApi()
      .inTurn("interpret", "interpret-rules-at-once", "interpret-by-model-long")
      .on("rank", "rank-suggestion-chosen")
      .on("explain_top", "explanations-suggestion-chosen");

  test("test_the_rules_are_asked_first_and_then_the_model_with_the_same_words_and_the_same_search", async () => {
    const api = reading();
    const { flow, state } = open(api);

    await flow.submitText(typedOf(long));

    const sent = api.callsTo("interpret").map((call) => call.body as { ask_model: boolean; text: string });
    expect(sent.map((body) => body.ask_model)).toEqual([false, true]);
    expect(sent[1]).toEqual({ ...sent[0], ask_model: true });
    expect(sent.map((body) => problemsWith("InterpretBody", body))).toEqual([[], []]);
    // What the model read has joined what is offered, and nothing of it is applied.
    expect(state().read?.more).toBe(false);
    expect(state().read?.suggestions).toEqual(long.body.data.suggestions);
    expect(state().spec).toEqual(meta.defaults.rent);
    expect(api.callsTo("rank")).toEqual([]);
  });

  test("test_what_the_rules_offer_is_on_the_page_while_the_model_reads", async () => {
    const atOnce = recordedAnswer("interpret", "interpret-rules-at-once").body.data;
    // A model that never answers.
    const api = standInApi().inTurn("interpret", "interpret-rules-at-once", () => new Promise(() => undefined));
    const { flow, state } = open(api);

    void flow.submitText(typedOf(long));
    await arrived();

    expect(state().read?.more).toBe(true);
    expect(state().read?.suggestions).toEqual(atOnce.suggestions);
    expect(state().read?.suggestions.some((one) => one.choices.some((way) => way.guess))).toBe(false);
    expect(state().phase).not.toBe("interpreting");
  });

  test("test_a_model_that_does_not_answer_leaves_what_the_rules_offered", async () => {
    const atOnce = recordedAnswer("interpret", "interpret-rules-at-once").body.data;
    const api = standInApi().inTurn("interpret", "interpret-rules-at-once", () => {
      throw new TypeError("Failed to fetch");
    });
    const { flow, state } = open(api);

    await flow.submitText(typedOf(long));

    expect(state().read?.more).toBe(false);
    expect(state().read?.suggestions).toEqual(atOnce.suggestions);
    expect(state().failure).toBeNull();
  });

  test("test_an_offer_chosen_while_the_model_reads_is_not_offered_again", async () => {
    const api = standInApi()
      .on("rank", "rank-suggestion-chosen")
      .on("explain_top", "explanations-suggestion-chosen");
    let answer: (() => void) | null = null;
    api.inTurn("interpret", "interpret-rules-at-once", async () => {
      await new Promise<void>((resolve) => (answer = resolve));
      return recordedAnswer("interpret", "interpret-by-model-long");
    });
    const { flow, state } = open(api);
    const read = flow.submitText(typedOf(long));
    await arrived();

    // "Quiet streets" is added while the model reads. A control that is moved does not stop the reading.
    await flow.choose(0, "more");
    expect(state().read?.more).toBe(true);
    (answer as (() => void) | null)?.();
    await read;

    expect(state().read?.suggestions.map((one) => one.target)).toEqual(
      long.body.data.suggestions.slice(1).map((one) => one.target),
    );
  });

  test("test_the_models_reading_is_let_go_when_the_box_changes", async () => {
    const api = standInApi().inTurn("interpret", "interpret-rules-at-once", () => new Promise(() => undefined));
    const { flow, state } = open(api);
    void flow.submitText(typedOf(long));
    await arrived();
    expect(state().read?.more).toBe(true);

    flow.boxChanged();

    expect(state().read).toMatchObject({ more: false, suggestions: [], unread: [], added: null });
  });

  test("test_a_reading_that_a_second_search_stopped_is_not_said_to_go_on_when_that_search_fails", async () => {
    // Seen in a browser: Search was pressed again, with the box as it was, while the model
    // read. The second call could not leave, and the page said for good that Burro was still
    // reading the rest of the words, though nothing read them.
    const atOnce = recordedAnswer("interpret", "interpret-rules-at-once").body.data;
    const api = standInApi().inTurn(
      "interpret",
      "interpret-rules-at-once",
      () => new Promise(() => undefined),
      () => {
        throw new TypeError("Failed to fetch");
      },
    );
    const { flow, state } = open(api);
    void flow.submitText(typedOf(long));
    await arrived();
    expect(state().read?.more).toBe(true);

    await flow.submitText(typedOf(long));

    expect(state().failure?.kind).toBe("network");
    expect(state().read?.more).toBe(false);
    // What the rules offered is still there to choose from.
    expect(state().read?.suggestions).toEqual(atOnce.suggestions);
  });

  test("test_a_reading_that_a_second_search_stopped_is_not_said_to_go_on_when_that_search_is_stopped", async () => {
    const never = () => new Promise<Response>(() => undefined);
    const api = standInApi().inTurn("interpret", "interpret-rules-at-once", never, never);
    const { flow, state } = open(api);
    void flow.submitText(typedOf(long));
    await arrived();
    expect(state().read?.more).toBe(true);
    void flow.submitText(typedOf(long));
    await arrived();
    expect(state().phase).toBe("interpreting");

    flow.stop();

    expect(state().phase).not.toBe("interpreting");
    expect(state().read?.more).toBe(false);
  });

  test("test_a_second_search_that_is_read_asks_the_model_again_and_says_so", async () => {
    // The mend must not take away what is true: a second search that the rules answer is
    // read by the model once more, and the page says so while it is.
    const api = standInApi().inTurn(
      "interpret",
      "interpret-rules-at-once",
      () => new Promise(() => undefined),
      "interpret-rules-at-once",
      () => new Promise(() => undefined),
    );
    const { flow, state } = open(api);
    void flow.submitText(typedOf(long));
    await arrived();

    void flow.submitText(typedOf(long));
    await arrived();

    expect(api.callsTo("interpret").map((call) => (call.body as { ask_model: boolean }).ask_model)).toEqual([
      false,
      true,
      false,
      true,
    ]);
    expect(state().read?.more).toBe(true);
  });

  test("test_nothing_is_ranked_from_what_was_noticed_until_the_person_chooses", async () => {
    const api = suggesting();
    const { flow, state } = open(api);

    await flow.submitText(`Pubs are so noisy ${CANARY}`);

    expect(api.calls.map((call) => call.operation)).toEqual(["interpret"]);
    expect(state().phase).toBe("empty");
    expect(state().ranking).toBeNull();
    expect(state().spec).toEqual(meta.defaults.rent);
    expect(state().read?.suggestions.map((one) => one.label)).toEqual(["Pubs and bars", "Less transport noise"]);
  });

  test("test_a_choice_sends_the_edits_the_api_gave_it_and_nothing_of_what_was_typed", async () => {
    const api = suggesting();
    const { flow, state } = open(api);
    await flow.submitText(`Pubs are so noisy ${CANARY}`);

    await flow.choose(0, "less");

    // What is sent is what the API was recorded taking: the spec it returned, and the choice's own edits.
    expect(api.lastCallTo("rank").body).toEqual(chosen.request.body);
    expect(api.lastCallTo("rank").sent?.includes(CANARY)).toBe(false);
    expect(state().phase).toBe("results");
    expect(state().spec).toEqual(chosen.body.data.spec);
    // The suggestion that was chosen of has gone, and the other is still offered.
    expect(state().read?.suggestions.map((one) => one.label)).toEqual(["Less transport noise"]);
    expect(api.unexpected).toEqual([]);
  });

  test("test_every_offer_one_press_may_add_is_added_in_one_request_with_the_edits_the_api_gave", async () => {
    const api = reading();
    const { flow, state } = open(api);
    await flow.submitText(`${typedOf(long)} ${CANARY}`);
    const offered = state().read?.suggestions ?? [];
    expect(offered.flatMap((one, at) => (one.add_all === "" ? [] : [at]))).toEqual(ONE_PRESS_ADDS);
    expect(ONE_PRESS_ADDS.map((at) => offered[at]?.add_all)).toEqual(["more", "more", "more", "guide", "guide"]);

    await flow.chooseAll(ONE_PRESS_ADDS);

    // One request, which holds the edits of each way as the API gave them, in their order.
    expect(api.callsTo("rank")).toHaveLength(1);
    const sent = api.lastCallTo("rank").body as { operations: Operations; spec: PreferenceSpec };
    const ways = offered.map((one) => one.choices.find((way) => way.id === one.add_all)?.operations ?? NO_EDITS);
    expect(sent.operations).toEqual(ways.reduce(merged, NO_EDITS));
    expect(sent.spec).toEqual(long.body.data.spec);
    expect(problemsWith("Operations", sent.operations)).toEqual([]);
    expect(api.lastCallTo("rank").sent?.includes(CANARY)).toBe(false);
    // What one press may not add is still offered.
    expect(state().read?.suggestions.map((one) => one.label)).toEqual(LEFT_TO_CHOOSE);
  });

  test("test_one_press_never_adds_what_leaves_areas_out_though_it_is_the_guess", async () => {
    const api = reading();
    const { flow, state } = open(api);
    await flow.submitText(typedOf(long));
    const journey = state().read?.suggestions.find((one) => one.target === "commute");
    expect(journey?.choices.find((way) => way.guess)?.id).toBe("firm");

    await flow.chooseAll(EVERY_OFFER);

    const sent = api.lastCallTo("rank").body as { operations: Operations };
    expect(sent.operations.commute_ops.map((edit) => edit.strictness)).toEqual(["soft"]);
    expect(sent.operations.budget_ops.map((edit) => edit.strictness)).toEqual(["soft"]);
    expect(sent.operations.area_ops).toEqual([]);
  });

  test("test_what_one_press_added_is_said_with_what_still_needs_the_person", async () => {
    const { flow, state } = open(reading());
    await flow.submitText(typedOf(long));

    await flow.chooseAll(EVERY_OFFER);

    expect(state().read?.added).toMatchObject({
      count: 5,
      needs: [
        "the journey can be made a firm limit",
        "the budget can be made a firm limit",
        "mix of brands",
        "recorded crime, which is added under its own name",
        "what homes sell for",
        "homes in the higher council tax bands",
        "Village feel",
        "Age of buildings",
        "nearer a town centre",
      ],
    });
  });

  test("test_one_press_takes_it_all_back_and_the_search_is_as_it_was", async () => {
    const api = reading();
    const { flow, state } = open(api);
    await flow.submitText(typedOf(long));
    const before = { spec: state().spec, offered: state().read?.suggestions };
    await flow.chooseAll(EVERY_OFFER);

    await flow.takeBack();

    // The search that is ranked is the one that stood before the press, with no edit.
    const again = api.lastCallTo("rank").body as { operations?: Operations; spec: PreferenceSpec };
    expect(again.spec).toEqual(before.spec);
    expect(again.operations).toBeUndefined();
    expect(state().read?.suggestions).toEqual(before.offered);
    expect(state().read?.added).toBeNull();
    // There is nothing more to take back.
    const calls = api.calls.length;
    await flow.takeBack();
    expect(api.calls).toHaveLength(calls);
  });

  describe("one press made while the model reads", () => {
    /** A service whose model answers when the test lets it. */
    function readingUntilLetGo() {
      const api = standInApi()
        .on("rank", "rank-suggestion-chosen")
        .on("explain_top", "explanations-suggestion-chosen");
      let letGo: () => void = () => undefined;
      api.inTurn("interpret", "interpret-rules-at-once", async () => {
        await new Promise<void>((resolve) => (letGo = resolve));
        return recordedAnswer("interpret", "interpret-by-model-long");
      });
      return { api, answer: () => letGo() };
    }
    type Offered = NonNullable<SearchState["read"]>["suggestions"];
    const guessed = (offers: Offered | undefined) =>
      (offers ?? []).filter((one) => one.choices.some((way) => way.guess)).length;
    /** An offer in a line: what it would do, each of its ways, and which of them is the guess. */
    const inALine = (offers: Offered | undefined) =>
      (offers ?? []).map((one) => `${one.does} ${one.choices.map((way) => (way.guess ? `[${way.id}]` : way.id)).join(" ")}`);

    test("test_taking_it_all_back_keeps_what_the_model_read_since_the_press", async () => {
      // Seen in a browser: one press added three things before the model had answered. The
      // model then marked its guesses and gave two offers a way more. "Take it all back" put
      // back what the rules had offered: no guess, and none of the ways the model added.
      const { api, answer } = readingUntilLetGo();
      const { flow, state } = open(api);
      const read = flow.submitText(typedOf(long));
      await arrived();
      const before = state().spec;
      const atOnce = state().read?.suggestions ?? [];
      expect(guessed(atOnce)).toBe(0);
      await flow.chooseAll(atOnce.map((_, at) => at));
      expect(state().read?.added).not.toBeNull();
      answer();
      await read;

      await flow.takeBack();

      expect(guessed(long.body.data.suggestions)).toBeGreaterThan(0);
      expect(inALine(state().read?.suggestions)).toEqual(inALine(long.body.data.suggestions));
      expect(state().read?.suggestions === undefined).toBe(false);
      expect(state().read?.added).toBeNull();
      expect(state().read?.chosen).toEqual([]);
      // The search that is ranked again is the one that stood before the press.
      const again = api.lastCallTo("rank").body as { operations?: Operations; spec: PreferenceSpec };
      expect(again.spec).toEqual(before);
      expect(again.operations).toBeUndefined();
    });

    test("test_what_was_chosen_before_the_press_is_not_offered_again_when_it_is_taken_back", async () => {
      const { api, answer } = readingUntilLetGo();
      const { flow, state } = open(api);
      const read = flow.submitText(typedOf(long));
      await arrived();
      // "Quiet streets" is left out by its own button, and then the rest is added at one press.
      const [first] = state().read?.suggestions ?? [];
      await flow.choose(0, "ignore");
      await flow.chooseAll((state().read?.suggestions ?? []).map((_, at) => at));
      answer();
      await read;

      await flow.takeBack();

      const offered = state().read?.suggestions.map((one) => one.target) ?? [];
      expect(offered).toEqual(long.body.data.suggestions.slice(1).map((one) => one.target));
      expect(offered).not.toContain(first?.target);
    });

    test("test_taking_it_all_back_before_the_model_answers_puts_back_what_the_rules_offered", async () => {
      // Nothing has been read since the press, so what comes back is what stood there.
      const { api } = readingUntilLetGo();
      const { flow, state } = open(api);
      void flow.submitText(typedOf(long));
      await arrived();
      const atOnce = state().read?.suggestions ?? [];
      await flow.chooseAll(atOnce.map((_, at) => at));

      await flow.takeBack();

      expect(inALine(state().read?.suggestions)).toEqual(inALine(atOnce));
      expect(state().read?.more).toBe(true);
    });
  });

  test("test_what_the_api_names_no_way_for_is_never_added_with_the_rest", async () => {
    const api = suggesting();
    const { flow, state } = open(api);
    await flow.submitText("Pubs are so noisy");

    // Pubs and bars run two ways, and the noise stands in doubt. Asked to add both, the flow adds neither.
    expect(noticed.suggestions.map((one) => one.add_all)).toEqual(["", ""]);
    await flow.chooseAll([0, 1]);

    expect(api.callsTo("rank")).toEqual([]);
    expect(state().read?.suggestions).toHaveLength(2);
    expect(state().read?.added).toBeNull();
  });

  test("test_with_nothing_one_press_may_add_nothing_is_sent", async () => {
    const api = suggesting();
    const { flow, state } = open(api);
    await flow.submitText("Pubs are so noisy");

    await flow.chooseAll([0]);
    await flow.chooseAll([]);
    await flow.chooseAll([9]);

    expect(api.callsTo("rank")).toEqual([]);
    expect(state().read?.suggestions).toHaveLength(2);
  });

  test("test_a_journey_with_no_place_is_not_sent_until_a_place_is_chosen_for_it", async () => {
    const api = standInApi()
      .on("interpret", "interpret-by-model-place")
      .on("rank", "rank-suggestion-chosen")
      .on("explain_top", "explanations-suggestion-chosen");
    const { flow, state } = open(api);
    await flow.submitText("At most 40 minutes from Mirrowick Basin, ideally");

    await flow.choose(0, "guide");
    await flow.chooseAll([0]);
    expect(api.callsTo("rank")).toEqual([]);
    expect(state().read?.suggestions).toHaveLength(1);

    await flow.choose(0, "guide", "syn-p0021");

    const sent = api.lastCallTo("rank").body as { operations: Operations };
    expect(sent.operations.commute_ops).toMatchObject([
      { action: "add", place_id: "syn-p0021", max_minutes: 40, strictness: "soft" },
    ]);
    expect(problemsWith("Operations", sent.operations)).toEqual([]);
    expect(state().read?.suggestions).toEqual([]);
  });

  test("test_leaving_a_thing_out_sends_nothing_and_the_suggestion_goes", async () => {
    const api = suggesting();
    const { flow, state } = open(api);
    await flow.submitText("Pubs are so noisy");

    await flow.choose(0, "ignore");

    expect(api.callsTo("rank")).toEqual([]);
    expect(state().ranking).toBeNull();
    expect(state().read?.suggestions.map((one) => one.label)).toEqual(["Less transport noise"]);
  });

  test("test_a_way_the_api_did_not_offer_is_not_sent", async () => {
    const api = suggesting();
    const { flow, state } = open(api);
    await flow.submitText("Pubs are so noisy");

    // Transport noise is offered as less, or not at all.
    expect(noticed.suggestions[1]?.choices.map((choice) => choice.id)).toEqual(["less", "ignore"]);
    await flow.choose(1, "more");
    await flow.choose(7, "less");

    expect(api.callsTo("rank")).toEqual([]);
    expect(state().read?.suggestions).toHaveLength(2);
  });

  test("test_every_suggestion_goes_when_the_box_changes", async () => {
    const { flow, state } = open(suggesting());
    await flow.submitText("Pubs are so noisy");

    flow.boxChanged();

    expect(state().read?.suggestions).toEqual([]);
    expect(state().read?.unread).toEqual([]);
  });
});
