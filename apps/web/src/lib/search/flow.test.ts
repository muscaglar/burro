import { recordedAnswer, recordedError, responseFrom } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";

import { landed, setOnline, standInApi, withTheSpecSent, type StandIn } from "../../../test/support/api";
import { problemsWith } from "../../../test/support/contract";
import { edits, merged, NO_EDITS } from "./edits";
import { createFlow, type FlowDeps } from "./flow";
import { NO_BOX } from "./mark";
import { refusals } from "./refusals";
import { leftOutOf } from "./said";
import { failureOfTheCards, initialState, reasonsAreIn, reasonsFailure, type SearchState } from "./state";
import { createStore } from "./store";
import { LIMITS, takenOf, takenOfAll as madeOfAll } from "./takes";

// A string found nowhere else, planted in what a person types.
const CANARY = "zqxcanary7431";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = {
  read: recordedAnswer("interpret", "interpret-first").body.data,
  rank: recordedAnswer("rank", "rank-first").body.data,
  explain: recordedAnswer("explain_top", "explanations-first").body.data,
};

/**
 * A search whose page has opened: the service has said who reads what is typed. `with_` is
 * what else the flow is handed: how long a first search waits, where a test is of that.
 */
function open(
  api: StandIn,
  reader: SearchState["reader"] = meta.reader,
  with_: Partial<Pick<FlowDeps, "rests" | "doubt" | "readings" | "turned" | "worded">> = {},
) {
  const store = createStore(initialState(meta, areas, null, reader));
  const seen: SearchState[] = [store.getState()];
  store.subscribe(() => seen.push(store.getState()));
  const flow = createFlow({ client: api.client, ...store, ...with_ });
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

describe("what the search is told of the box", () => {
  const FIRST = `leafy and quiet near ${CANARY}`;
  const MORE = `, and a park by ${CANARY}`;

  test("test_the_search_has_read_what_it_was_handed_once_the_words_are_answered", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);

    expect(state().box.read).toEqual({ to: 0, changed: false });
    await flow.submitText(FIRST);

    expect(state().box).toEqual({ ...NO_BOX, read: { to: FIRST.length, changed: false }, shown: 0 });
  });

  test("test_the_words_it_is_handed_are_sent_as_they_are_with_the_search_as_it_stands", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText(FIRST);
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await flow.applyEdits(edits.placeStrictness("syn-p0021", "hard"));
    const setByHand = state().spec;
    api.on("interpret", "interpret-second-sentence");

    // The box hands over what it holds that the search has not read, and that is what is sent.
    await flow.submitText(` ${MORE}  `);

    expect(api.lastCallTo("interpret").body).toEqual({ text: MORE, spec: setByHand, ask_model: false });
    // The search has read as far as the box was handed over, with the space about the words.
    expect(state().box.read.to).toBe(FIRST.length + MORE.length + 3);
    expect(state().box.shown).toBe(FIRST.length);
  });

  test("test_words_that_never_reached_burro_are_not_said_to_be_read", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText(FIRST);
    api.unreachable("interpret");

    await flow.submitText(MORE);

    expect(state().failedStep).toBe("read");
    expect(state().box.read.to).toBe(FIRST.length);
    // Stopped, they are not read either.
    api.silent("interpret");
    const sent = flow.submitText(MORE);
    flow.stop();
    await sent;
    expect(state().box.read.to).toBe(FIRST.length);
    expect(state().box.sending).toBeNull();
  });

  test("test_the_search_is_told_where_the_box_was_changed_and_how_much_it_holds_in_counts_alone", async () => {
    const api = firstSearch();
    const { flow, state, seen } = open(api);
    await flow.submitText(FIRST);
    const told = seen.length;

    // What is typed after the words that were read is nothing the store keeps.
    flow.boxEdited({ at: FIRST.length, out: 0, into: 1, holds: FIRST.length + 1 });
    flow.boxEdited({ at: FIRST.length + 1, out: 0, into: 1, holds: FIRST.length + 2 });
    expect(seen).toHaveLength(told + 1);
    flow.boxEdited({ at: 6, out: 3, into: 2, holds: FIRST.length + 1 });
    expect(state().box.read).toEqual({ to: FIRST.length - 1, changed: true });
    flow.boxFound(0);
    expect(state().box.read).toEqual({ to: 0, changed: false });

    expect(api.calls.filter((call) => call.operation !== "interpret").some((call) => call.sent?.includes(CANARY))).toBe(false);
    expect(JSON.stringify(seen).includes(CANARY)).toBe(false);
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

describe("what the second way in gathers, before a search", () => {
  const edit = edits.placeAdd("syn-p0021");

  test("test_what_is_chosen_is_sent_to_be_applied_and_no_search_is_made_of_it", async () => {
    // The founder drew two ways in, and the second is built by choosing and then searching.
    // Seen in a browser: the first place that was chosen made the search by itself, the tabs
    // went, and the button the tab ends with was gone when a person reached for it.
    const api = standInApi().on("rank", "rank-first");
    const { flow, state, seen } = open(api);

    await flow.addPlace({ place_id: "syn-p0021" }, "gather");

    // It is sent with the last spec returned, as every edit is, and the fewest results are
    // asked for: none of them is kept.
    expect(api.calls.map((call) => call.operation)).toEqual(["rank"]);
    expect(api.lastCallTo("rank").body).toEqual({ spec: meta.defaults.rent, operations: edit, limit: 1 });
    expect(state().gathering).toBe(true);
    expect(state().ranking).toBeNull();
    expect(state().rankedHash).toBeNull();
    expect(seen.every((one) => one.phase === "empty" && one.ranking === null)).toBe(true);
    // The settings are drawn from the spec the API returned, and the place by its name.
    expect(state().spec).toEqual(first.rank.spec);
    expect(state().specHash).toBe(first.rank.spec_hash);
    expect(state().placeNames).toEqual({ "syn-p0021": "Cindermoor Works" });
    expect(state().pending).toEqual(NO_EDITS);
    expect(state().untouched).toBe(false);
    // Neither its reasons nor a profile is asked for.
    expect(api.callsTo("explain_top")).toEqual([]);
    expect(api.callsTo("get_area")).toEqual([]);
    expect(api.unexpected).toEqual([]);
  });

  test("test_every_answer_moves_the_count_a_control_holds_its_value_against", async () => {
    const api = standInApi().on("rank", "rank-first");
    const { flow, state } = open(api);
    const before = state().answers;

    await flow.applyEdits(edit, "gather");

    expect(state().answers).toBe(before + 1);
  });

  test("test_the_next_thing_chosen_is_sent_with_the_spec_the_last_one_left", async () => {
    const api = standInApi().on("rank", "rank-first");
    const { flow, state } = open(api);
    await flow.applyEdits(edit, "gather");
    api.on("rank", "rank-refined");
    const firmer = edits.placeStrictness("syn-p0021", "hard");

    await flow.applyEdits(firmer, "gather");

    expect(api.lastCallTo("rank").body).toEqual({ spec: first.rank.spec, operations: firmer, limit: 1 });
    expect(state().spec).toEqual(recordedAnswer("rank", "rank-refined").body.data.spec);
    expect(state().gathering).toBe(true);
    expect(state().ranking).toBeNull();
  });

  test("test_renting_or_buying_swaps_the_default_until_something_is_gathered_and_is_gathered_after", async () => {
    const api = standInApi().on("rank", "rank-first");
    const { flow, state } = open(api);

    await flow.setTenure("buy", "gather");
    expect(api.calls).toEqual([]);
    expect(state().spec).toBe(meta.defaults.buy);
    expect(state().gathering).toBe(false);

    await flow.setTenure("rent", "gather");
    await flow.applyEdits(edit, "gather");
    api.on("rank", "rank-buyer-family");
    await flow.setTenure("buy", "gather");

    expect(api.lastCallTo("rank").body).toEqual({ spec: first.rank.spec, operations: edits.tenure("buy"), limit: 1 });
    expect(state().gathering).toBe(true);
    expect(state().ranking).toBeNull();
  });

  test("test_the_button_makes_the_search_of_what_was_gathered_with_nothing_more_to_apply", async () => {
    const api = standInApi().on("rank", "rank-first").on("explain_top", "explanations-first");
    const { flow, state } = open(api);
    await flow.applyEdits(edit, "gather");
    api.calls.length = 0;

    await flow.rankNow();

    expect(api.lastCallTo("rank").body).toEqual({ spec: first.rank.spec, limit: 20 });
    expect(state().gathering).toBe(false);
    expect(state().phase).toBe("results");
    expect(state().ranking?.ranked).toEqual(first.rank.ranked);
    // Its reasons are asked for, and the profiles of its first areas.
    expect(api.callsTo("explain_top")).toHaveLength(1);
    expect(api.callsTo("get_area").length).toBeGreaterThan(0);
    expect(api.unexpected).toEqual([]);
  });

  test("test_a_sentence_sent_from_the_box_makes_the_search_of_what_was_gathered_and_what_it_says", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.applyEdits(edit, "gather");

    await flow.submitText("leafy and quiet");

    expect(api.lastCallTo("interpret").body).toMatchObject({ spec: first.rank.spec });
    expect(state().gathering).toBe(false);
    expect(state().phase).toBe("results");
  });

  test("test_an_edit_that_ranks_makes_the_search_of_what_was_gathered_with_it", async () => {
    // A word of the shelf is added from the first way in: that press says what it does.
    const api = standInApi().on("rank", "rank-first").on("explain_top", "explanations-first");
    const { flow, state } = open(api);
    await flow.applyEdits(edit, "gather");
    const word = edits.tagOn("parks_close_by");

    await flow.applyEdits(word);

    expect(api.lastCallTo("rank").body).toEqual({ spec: first.rank.spec, operations: word, limit: 20 });
    expect(state().gathering).toBe(false);
    expect(state().ranking).not.toBeNull();
  });

  test("test_what_is_refused_is_said_and_the_search_is_as_it_was", async () => {
    const api = standInApi().on("rank", "rank-rejected-edit");
    const { flow, state } = open(api);
    const low = edits.budgetAmount(1);

    await flow.applyEdits(low, "gather");

    expect(state().refused).toEqual({
      operations: low,
      rejected: [{ group: "budget_ops", index: 0, reason: "out_of_range" }],
    });
    expect(state().ranking).toBeNull();
    expect(state().phase).toBe("empty");
  });

  test("test_what_could_not_be_sent_waits_and_is_sent_again_with_no_search_made_of_it", async () => {
    const api = standInApi().on("rank", "error-internal");
    const { flow, state } = open(api);

    await flow.applyEdits(edit, "gather");

    expect(state().failure?.kind).toBe("api");
    expect(state().failedStep).toBe("rank");
    expect(state().pending).toEqual(edit);
    expect(state().gathering).toBe(true);
    expect(state().phase).toBe("empty");

    api.on("rank", "rank-first");
    await flow.retry();

    expect(api.lastCallTo("rank").body).toEqual({ spec: meta.defaults.rent, operations: edit, limit: 1 });
    expect(state().failure).toBeNull();
    expect(state().spec).toEqual(first.rank.spec);
    expect(state().ranking).toBeNull();
    expect(state().gathering).toBe(true);
    expect(api.callsTo("explain_top")).toEqual([]);
  });

  test("test_what_is_chosen_offline_waits_and_is_gathered_when_the_browser_is_back", async () => {
    const api = standInApi().on("rank", "rank-first");
    const { flow, state } = open(api);

    setOnline(false);
    flow.wentOffline();
    await flow.applyEdits(edit, "gather");
    expect(api.calls).toEqual([]);
    expect(state().pending).toEqual(edit);

    setOnline(true);
    await flow.wentOnline();

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edit, limit: 1 });
    expect(state().ranking).toBeNull();
    expect(state().gathering).toBe(true);
  });

  test("test_two_things_chosen_one_upon_the_other_are_sent_together_and_the_older_answer_is_dropped", async () => {
    const api = standInApi();
    const slow = api.hold("rank", "rank-first");
    const { flow, state } = open(api);
    const firmer = edits.placeStrictness("syn-p0021", "hard");

    const one = flow.applyEdits(edit, "gather");
    await arrived();
    api.on("rank", "rank-refined");
    const two = flow.applyEdits(firmer, "gather");
    slow.release();
    await Promise.all([one, two]);

    expect(api.lastCallTo("rank").body).toEqual({
      spec: meta.defaults.rent,
      operations: merged(edit, firmer),
      limit: 1,
    });
    expect(state().spec).toEqual(recordedAnswer("rank", "rank-refined").body.data.spec);
    expect(state().pending).toEqual(NO_EDITS);
  });

  test("test_with_a_search_open_nothing_is_gathered_and_an_edit_ranks_as_it_did", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.submitText("leafy and quiet");
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await flow.applyEdits(edits.placeStrictness("syn-p0021", "hard"), "gather");

    expect(state().gathering).toBe(false);
    expect(api.lastCallTo("rank").body).toMatchObject({ limit: 20 });
    expect(state().ranking?.ranked).toEqual(recordedAnswer("rank", "rank-refined").body.data.ranked);
  });

  test("test_starting_again_forgets_what_was_gathered", async () => {
    const api = standInApi().on("rank", "rank-first");
    const { flow, state } = open(api);
    await flow.applyEdits(edit, "gather");

    flow.startAgain();

    expect(state().gathering).toBe(false);
    expect(state().spec).toBe(meta.defaults.rent);
    expect(state().untouched).toBe(true);
    expect(state().placeNames).toEqual({});
  });

  test("test_nothing_of_it_is_kept_but_what_the_api_returned", async () => {
    const api = standInApi().on("rank", "rank-first");
    const { flow, seen } = open(api);

    await flow.applyEdits(edit, "gather");

    const known = [meta.defaults.rent, meta.defaults.buy, first.rank.spec];
    for (const state of seen) {
      for (const spec of specsIn({ spec: state.spec, kept: state.kept })) {
        expect(known.some((one) => JSON.stringify(one) === JSON.stringify(spec))).toBe(true);
      }
    }
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

describe("a place whose name several places bear", () => {
  const asked = recordedAnswer("interpret", "interpret-clarify").body.data;
  const [question] = asked.clarify;
  const [first] = question?.options ?? [];
  if (!question || !first) throw new Error("the recording holds no question");

  test("test_nothing_is_asked_and_the_journey_is_ranked_to_the_first_place_the_service_gave", async () => {
    const api = firstSearch().on("interpret", "interpret-clarify");
    const { flow, state } = open(api);

    await flow.submitText(`leafy, 30 minutes to somewhere ${CANARY}`);

    expect(question.options.length).toBeGreaterThan(1);
    expect(state().read?.clarify).toEqual([]);
    expect(state().phase).toBe("results");
    // One ranking, of the spec the reading returned, with the edit that was asked about
    // and the place that was taken in it. Nothing else of the edit is touched.
    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toEqual({
      spec: asked.spec,
      limit: 20,
      operations: { ...NO_EDITS, commute_ops: [{ ...asked.operations.commute_ops[0], place_id: first.id }] },
    });
    expect(problemsWith("RankBody", api.lastCallTo("rank").body)).toEqual([]);
    expect(api.lastCallTo("rank").sent?.includes(CANARY)).toBe(false);
    // The refusal the question stood for goes with it.
    expect(state().read?.rejected).toEqual([]);
    // What was assumed of the journey is assumed of the place, and so is the place itself.
    expect(state().assumed[`place:${first.id}`]).toEqual(["mode", "strictness", "place"]);
  });

  test("test_a_place_burro_does_not_know_is_left_out_and_said_and_the_rest_is_ranked", async () => {
    const notFound = recordedAnswer("interpret", "interpret-clarify-no-options").body.data;
    const api = firstSearch().on("interpret", "interpret-clarify-no-options");
    const { flow, state } = open(api);

    await flow.submitText("Quiet, and I work somewhere");

    expect(notFound.clarify[0]?.options).toEqual([]);
    expect(state().read?.clarify).toEqual([]);
    // The rest of the sentence was applied as it was read, and is ranked with no edit more.
    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toEqual({ spec: notFound.spec, limit: 20 });
    expect(refusals(state().read, null)).toEqual([{ key: "place:", reason: "unknown_place" }]);
  });

  test("test_a_place_burro_does_not_know_with_nothing_else_read_ranks_nothing_and_opens_no_settings", async () => {
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
    expect(state().read?.clarify).toEqual([]);
    expect(refusals(state().read, null)).toEqual([{ key: "place:", reason: "unknown_place" }]);
    expect(state().settingsOpen).toBe(false);
  });

  test("test_a_rule_for_an_area_is_never_set_on_a_guess", async () => {
    // A name that two areas bear, in a sentence that hides one or keeps to one. To take the
    // first would leave areas out on a guess: nothing is taken, and the refusal is said.
    const recorded = recordedAnswer("interpret", "interpret-clarify");
    const ofAnArea = {
      ...recorded.body.data,
      operations: { ...NO_EDITS, area_ops: [{ action: "only" as const, area_id: "", provenance: "stated" as const }] },
      clarify: [
        {
          group: "area_ops" as const,
          index: 0,
          options: areas.slice(0, 2).map((area) => ({ id: area.area_id, name: area.name, kind: "area" as const })),
        },
      ],
      rejected: [{ group: "area_ops" as const, index: 0, reason: "unknown_area" as const }],
      applied: [],
      spec: meta.defaults.rent,
    };
    const api = standInApi().on("interpret", () =>
      responseFrom({ ...recorded, body: { ...recorded.body, data: ofAnArea } }),
    );
    const { flow, state } = open(api);

    await flow.submitText("only in a place of that name");

    expect(api.callsTo("rank")).toEqual([]);
    expect(state().pending).toEqual(NO_EDITS);
    expect(state().read?.clarify).toEqual([]);
    expect(refusals(state().read, null)).toEqual([{ key: "area:", reason: "unknown_area" }]);
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

  test("test_boundaries_that_could_not_be_read_as_the_page_opened_are_asked_for_again_by_the_next_answer", async () => {
    const api = firstSearch().unreachable("get_geometry");
    const { flow, state } = open(api);
    await flow.loadGeometry();
    expect(state().geometryFailed).toBe(true);

    // The service can be reached again, and a person searches.
    api.on("get_geometry", "geometry");
    await flow.submitText("leafy");
    await arrived();

    expect(state().ranking).not.toBeNull();
    expect(api.callsTo("get_geometry")).toHaveLength(2);
    expect(state().geometry?.features).toHaveLength(areas.length);
    expect(state().geometryFailed).toBe(false);
    // Once they are in hand they are asked for no more.
    await flow.rankNow();
    await arrived();
    expect(api.callsTo("get_geometry")).toHaveLength(2);
  });

  test("test_boundaries_that_are_in_hand_are_never_asked_for_again_and_nor_is_the_form", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);
    await flow.loadGeometry();

    await flow.submitText("leafy");
    await arrived();
    await flow.rankNow();
    await arrived();

    expect(api.callsTo("get_geometry")).toHaveLength(1);
    expect(state().geometry?.features).toHaveLength(areas.length);
    expect(api.callsTo("get_meta")).toEqual([]);
    expect(api.callsTo("list_areas")).toEqual([]);
  });

  test("test_a_search_is_whole_where_the_boundaries_still_cannot_be_read", async () => {
    const api = firstSearch().unreachable("get_geometry");
    const { flow, state } = open(api);
    await flow.loadGeometry();

    await flow.submitText("leafy");
    await arrived();

    expect(state().ranking).not.toBeNull();
    expect(reasonsAreIn(state())).toBe(true);
    expect(state().failure).toBeNull();
    expect(state().geometry).toBeNull();
    expect(state().geometryFailed).toBe(true);
    // They are owed still, and the next answer asks once more.
    api.on("get_geometry", "geometry");
    await flow.rankNow();
    await arrived();
    expect(state().geometry?.features).toHaveLength(areas.length);
  });

  test("test_boundaries_that_came_another_way_meanwhile_are_not_owed_by_a_first_call_that_fails_late", async () => {
    // The page asks for them as it opens. Where a release moved meanwhile they came with its
    // form, and the first call may fail after that: nothing is owed then, and nothing asked again.
    const api = firstSearch().movedTo(NEWER);
    const late = api.gate("error-internal");
    api.inTurn("get_geometry", late.answers, "geometry");
    const { flow, state } = open(api);
    const first = flow.loadGeometry();

    await flow.submitText("leafy");
    await arrived();
    expect(state().geometry?.features).toHaveLength(areas.length);
    late.release();
    await first;
    expect(state().geometryFailed).toBe(false);

    api.calls.length = 0;
    await flow.rankNow();
    await arrived();
    expect(api.callsTo("get_geometry")).toEqual([]);
    expect(api.callsTo("get_meta")).toEqual([]);
  });

  test("test_boundaries_that_could_not_leave_are_asked_for_again_as_the_connection_comes_back", async () => {
    const api = standInApi().unreachable("get_geometry");
    const { flow, state } = open(api);
    await flow.loadGeometry();
    expect(state().geometryFailed).toBe(true);

    flow.wentOffline();
    api.on("get_geometry", "geometry");
    await flow.wentOnline();
    await arrived();

    // Nothing waited to be sent, so nothing is ranked: the boundaries are asked for alone.
    expect(api.callsTo("rank")).toEqual([]);
    expect(state().geometry?.features).toHaveLength(areas.length);
    expect(state().geometryFailed).toBe(false);
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
  const long = recordedAnswer("interpret", "interpret-by-model-long");
  const atOnce = recordedAnswer("interpret", "interpret-rules-at-once").body.data;
  const typedOf = (recorded: { request: { body?: unknown } }) => (recorded.request.body as { text: string }).text;
  type Offered = typeof atOnce.suggestions;
  /** The edits of the way Burro takes of each of these offers, in the order they were noticed. */
  const takenOfAll = (offers: Offered) =>
    madeOfAll(offers, meta).reduce((all, made) => (made.way === null ? all : merged(all, made.operations)), NO_EDITS);
  /** The offers that Burro takes, or those it leaves, by the name the service gives each. */
  const labelled = (offers: Offered, take: boolean) => {
    const made = madeOfAll(offers, meta);
    return offers.filter((_, at) => (made[at]?.way !== null) === take).map((offer) => offer.label);
  };
  const suggesting = () =>
    standInApi()
      .on("interpret", "interpret-suggest")
      .on("rank", "rank-suggestion-chosen")
      .on("explain_top", "explanations-suggestion-chosen");
  /** "Young professionals, lively, near a station": two things of it are taken, and one waits for the person. */
  const counted = recordedAnswer("interpret", "interpret-suggest-who-is-counted").body.data;
  const counting = () => suggesting().on("interpret", "interpret-suggest-who-is-counted");
  /** The less noise that "Pubs are so noisy" offers, as a sentence offers it that says it of the person's own home. */
  const lessNoise = () => {
    const [, noise] = noticed.suggestions;
    if (!noise) throw new Error("the recording holds too little");
    return { ...noise, only_by_choice: false, note: "" };
  };
  /** A service with a model behind it: the rules answer at once, and then the model. */
  const reading = () =>
    standInApi()
      .inTurn("interpret", "interpret-rules-at-once", "interpret-by-model-long")
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");
  const sentTo = (api: StandIn) =>
    api.callsTo("rank").map((call) => call.body as { operations?: Operations; spec: PreferenceSpec });

  test("test_nothing_is_offered_and_what_burro_takes_of_what_was_noticed_is_ranked_at_once", async () => {
    const api = counting();
    const { flow, state, seen } = open(api);

    await flow.submitText(`young professionals, lively, near a station ${CANARY}`);

    expect(api.calls.map((call) => call.operation).slice(0, 2)).toEqual(["interpret", "rank"]);
    expect(state().phase).toBe("results");
    expect(state().ranking).not.toBeNull();
    // Nothing waits on a press: what was noticed is held for no longer than it takes to take it.
    expect(state().read?.suggestions).toEqual([]);
    // The words give the way of going out and of a station, and both are taken. What
    // counts who lived somewhere waits for the person.
    expect(state().read?.took).toBe(2);
    expect(state().read?.left.map((one) => [one.label, one.why])).toEqual([["Young professionals", "residents"]]);
    expect(sentTo(api)[0]?.operations?.tag_ops.map((edit) => edit.tag_id)).toEqual(["pace"]);
    expect(sentTo(api)[0]?.operations?.weight_ops.map((edit) => edit.feature_id)).toEqual(["station_walk"]);
    expect(seen.filter((one) => one.phase !== "interpreting" && (one.read?.suggestions.length ?? 0) > 0)).toEqual([]);
    // One request, with the spec the reading returned and the edits the service gave with
    // each way, in the order the things were noticed. Nothing of what was typed goes with it.
    expect(sentTo(api)).toEqual([{ spec: counted.spec, limit: 20, operations: takenOfAll(counted.suggestions) }]);
    expect(problemsWith("RankBody", api.lastCallTo("rank").body)).toEqual([]);
    expect(api.lastCallTo("rank").sent?.includes(CANARY)).toBe(false);
    expect(api.unexpected).toEqual([]);
  });

  test("test_where_the_words_give_no_way_of_one_thing_and_the_other_waits_nothing_is_taken_and_nothing_is_ranked", async () => {
    // "Pubs are so noisy" says neither more pubs nor fewer, and does not say that the
    // person wants less noise for themselves. More pubs was taken of it once, and areas
    // with more of them came first for a person who may have wanted fewer.
    const api = suggesting();
    const { flow, state } = open(api);

    await flow.submitText(`Pubs are so noisy ${CANARY}`);

    expect(api.calls.map((call) => call.operation)).toEqual(["interpret"]);
    expect(state().ranking).toBeNull();
    expect(state().read?.suggestions).toEqual([]);
    expect(state().read?.took).toBe(0);
    expect(state().read?.left.map((one) => [one.label, one.why])).toEqual([
      ["Pubs and bars", "two_ways"],
      ["Less transport noise", "not_said"],
    ]);
    expect(api.unexpected).toEqual([]);
  });

  test("test_the_spec_on_screen_is_still_only_ever_one_the_service_returned", async () => {
    const api = counting();
    const { flow, seen } = open(api);
    const chosen = recordedAnswer("rank", "rank-suggestion-chosen").body.data;

    await flow.submitText("young professionals, lively, near a station");

    // The website builds edits, and never a spec: what it took is in no spec until the
    // service has applied it and returned one.
    const held = new Set(seen.map((one) => JSON.stringify(one.spec)));
    expect([...held].sort()).toEqual([JSON.stringify(meta.defaults.rent), JSON.stringify(chosen.spec)].sort());
  });

  test("test_every_offer_is_taken_in_one_request_by_the_way_that_is_chosen_for_it", async () => {
    const api = reading();
    const { flow, state } = open(api);

    await flow.submitText(`${typedOf(long)} ${CANARY}`);

    const [first] = sentTo(api);
    expect(first?.spec).toEqual(atOnce.spec);
    expect(first?.operations).toEqual(takenOfAll(atOnce.suggestions));
    expect(problemsWith("Operations", first?.operations)).toEqual([]);
    for (const call of api.callsTo("rank")) expect(call.sent?.includes(CANARY)).toBe(false);
    // What one press would have added is among it, as one press added it.
    const onePress = atOnce.suggestions.flatMap((one) => one.choices.filter((way) => way.id === one.add_all));
    expect(onePress.length).toBeGreaterThan(4);
    for (const way of onePress) {
      for (const edit of way.operations.tag_ops) expect(first?.operations?.tag_ops).toContainEqual(edit);
      for (const edit of way.operations.budget_ops) expect(first?.operations?.budget_ops).toContainEqual(edit);
      for (const edit of way.operations.commute_ops) expect(first?.operations?.commute_ops).toContainEqual(edit);
    }
    // The journey among it: as the guide that one press adds, and nothing else of a journey.
    const journey = atOnce.suggestions.find((one) => one.target === "commute");
    expect(journey?.add_all).toBe("guide");
    expect(first?.operations?.commute_ops).toEqual(
      journey?.choices.find((way) => way.id === journey.add_all)?.operations.commute_ops,
    );
    expect(state().read?.suggestions).toEqual([]);
  });

  test("test_a_journey_is_taken_as_a_guide_though_the_words_give_a_firm_limit_and_a_budget_as_it_was_worded", async () => {
    const api = reading();
    const { flow, state } = open(api);
    const journey = atOnce.suggestions.find((one) => one.target === "commute");
    expect(journey?.choices.find((way) => way.guess)?.id).toBe("firm");
    expect(journey?.add_all).toBe("guide");

    await flow.submitText(typedOf(long));

    // A journey is estimated from distance, so no area is left out on one without a press.
    expect(sentTo(api).length).toBeGreaterThan(0);
    for (const sent of sentTo(api)) {
      expect(sent.operations?.commute_ops.map((edit) => edit.strictness)).toEqual(["soft"]);
      expect(sent.operations?.area_ops).toEqual([]);
    }
    // The person wrote "at most": that the limit is flexible was Burro's to choose, and the search says so.
    expect(state().assumed["place:syn-p0017"]).toContain("strictness");
    // "Max" makes the budget a firm limit, and it is taken as it was worded.
    expect(sentTo(api)[0]?.operations?.budget_ops.map((edit) => edit.strictness)).toContain("hard");
  });

  test("test_one_line_of_the_look_has_a_journey_sent_as_the_firm_limit_its_words_make_it_and_a_budget_as_it_was_worded", async () => {
    // The other way it was built, by its name.
    const api = reading();
    const { flow, state } = open(api, meta.reader, { worded: "as_worded" });

    await flow.submitText(typedOf(long));

    // "At most" makes the minutes firm, and the journey is sent as the words make it.
    expect(sentTo(api).length).toBeGreaterThan(0);
    for (const sent of sentTo(api)) {
      expect(sent.operations?.commute_ops.map((edit) => edit.strictness)).toEqual(["hard"]);
      expect(sent.operations?.area_ops).toEqual([]);
    }
    expect(sentTo(api)[0]?.operations?.commute_ops).toEqual(
      atOnce.suggestions.find((one) => one.target === "commute")?.choices.find((way) => way.guess)?.operations.commute_ops,
    );
    // That the limit is firm is what the person said, and nothing says that it was assumed.
    expect(state().assumed["place:syn-p0017"] ?? []).not.toContain("strictness");
    // "Max" makes the budget a firm limit, and it is taken as it was worded either way.
    expect(sentTo(api)[0]?.operations?.budget_ops.map((edit) => edit.strictness)).toContain("hard");
  });

  test("test_a_journey_whose_words_give_no_way_is_sent_as_a_guide_so_that_no_area_is_left_out_on_a_guess", async () => {
    // The same sentence, as a service answers that could not tell which way the journey was meant.
    const recorded = recordedAnswer("interpret", "interpret-rules-at-once");
    const suggestions = atOnce.suggestions.map((one) =>
      one.target === "commute"
        ? { ...one, add_all: "", choices: one.choices.map((way) => ({ ...way, guess: false })) }
        : one,
    );
    const unmarked = { ...recorded, body: { ...recorded.body, data: { ...atOnce, suggestions } } };

    // Whichever way the line of the look has a journey taken whose words make its limit firm.
    for (const with_ of [{}, ...LIMITS.map((worded) => ({ worded }))]) {
      const api = reading().inTurn("interpret", () => unmarked, "interpret-by-model-long");
      const { flow, state } = open(api, meta.reader, with_);

      await flow.submitText(typedOf(long));

      expect(sentTo(api)[0]?.operations?.commute_ops.map((edit) => edit.strictness)).toEqual(["soft"]);
      // That the limit is flexible was Burro's to choose, and the search says so.
      expect(state().assumed["place:syn-p0017"]).toContain("strictness");
    }
  });

  test("test_what_counts_recorded_crime_is_never_sent_and_is_named_among_what_was_left_out", async () => {
    const api = reading();
    const { flow, state } = open(api);

    await flow.submitText(typedOf(long));

    expect(labelled(atOnce.suggestions, false)).toContain("Gritty");
    for (const sent of sentTo(api)) {
      expect(sent.operations?.tag_ops.map((edit) => edit.tag_id)).not.toContain("street_character");
      expect(sent.operations?.weight_ops.filter((edit) => /^crime_/.test(edit.feature_id))).toEqual([]);
    }
    const ofCrime = <Thing extends { readonly why: string }>(things: readonly Thing[]) =>
      things.filter((one) => one.why === "crime");
    expect(ofCrime(state().read?.left ?? []).map((one) => one.label)).toEqual(["Gritty"]);
    expect(ofCrime(leftOutOf(state().read)).map((thing) => thing.name)).toEqual(["Gritty"]);
    expect(refusals(state().read, null)).toEqual([]);
  });

  test("test_the_rules_are_asked_first_and_then_the_model_with_the_same_words_and_the_same_search", async () => {
    const api = reading();
    const { flow, state } = open(api);

    await flow.submitText(typedOf(long));

    const sent = api.callsTo("interpret").map((call) => call.body as { ask_model: boolean; text: string });
    expect(sent.map((body) => body.ask_model)).toEqual([false, true]);
    expect(sent[1]).toEqual({ ...sent[0], ask_model: true });
    expect(sent.map((body) => problemsWith("InterpretBody", body))).toEqual([[], []]);
    expect(state().read?.more).toBe(false);
    expect(state().read?.suggestions).toEqual([]);
  });

  test("test_what_the_rules_read_is_ranked_while_the_model_reads", async () => {
    // A model that never answers.
    const api = standInApi()
      .inTurn("interpret", "interpret-rules-at-once", () => new Promise(() => undefined))
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");
    const { flow, state } = open(api);

    void flow.submitText(typedOf(long));
    await arrived();

    expect(state().read?.more).toBe(true);
    expect(state().phase).toBe("results");
    expect(state().ranking).not.toBeNull();
    expect(sentTo(api)).toEqual([{ spec: atOnce.spec, limit: 20, operations: takenOfAll(atOnce.suggestions) }]);
  });

  test("test_what_a_model_read_beyond_the_rules_is_taken_as_well_and_nothing_is_taken_twice", async () => {
    const api = reading();
    const { flow, state } = open(api);

    await flow.submitText(typedOf(long));
    await arrived();

    // The model names the budget in another way than the rules did, and reads nothing the
    // rules did not: the budget is one thing, and is taken once. So is every wish.
    const byAModelAlone = long.body.data.suggestions.filter(
      (one) => !atOnce.suggestions.some((other) => other.target === one.target && other.label === one.label),
    );
    expect(byAModelAlone.map((one) => one.label)).toEqual(["A budget of £1,900"]);
    const rankings = sentTo(api);
    expect(rankings).toHaveLength(1);
    const wishes = [...(rankings[0]?.operations?.tag_ops ?? []), ...(rankings[0]?.operations?.weight_ops ?? [])];
    const things = wishes.map((edit) => ("tag_id" in edit ? edit.tag_id : edit.feature_id));
    expect(new Set(things).size).toBe(things.length);
    expect(state().read?.suggestions).toEqual([]);
    expect(state().read?.took).toBe(labelled(atOnce.suggestions, true).length);
  });

  test("test_a_thing_that_only_a_model_read_is_taken_and_ranked_with_what_the_rules_read", async () => {
    // A model that reads one thing the rules did not: a river nearby.
    const river = recordedAnswer("interpret", "visit/21-slow").body.data.suggestions[0];
    if (!river) throw new Error("the recording holds no offer");
    const andTheRiver = {
      ...long,
      body: { ...long.body, data: { ...long.body.data, suggestions: [...long.body.data.suggestions, river] } },
    };
    const model = standInApi().gate(() => responseFrom(andTheRiver));
    const api = standInApi()
      .inTurn("interpret", "interpret-rules-at-once", model.answers)
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");
    const { flow, state } = open(api);
    const read = flow.submitText(typedOf(long));
    await arrived();
    expect(sentTo(api)).toHaveLength(1);
    const ranked = state().spec;

    model.release();
    await read;
    await arrived();

    // What waits is what the model read beyond the rules, and it is sent with the spec
    // the first ranking returned: nothing that the rules read is sent a second time.
    const [, second] = sentTo(api);
    expect(sentTo(api)).toHaveLength(2);
    expect(second?.spec).toEqual(ranked);
    expect(second?.operations).toEqual(takenOf(river, meta).way === null ? NO_EDITS : river.choices[0]?.operations);
    expect(state().read?.took).toBe(labelled(atOnce.suggestions, true).length + 1);
  });

  test("test_what_a_model_read_while_the_first_ranking_was_out_is_sent_with_what_the_rules_read_so_none_is_lost", async () => {
    const river = recordedAnswer("interpret", "visit/21-slow").body.data.suggestions[0];
    if (!river) throw new Error("the recording holds no offer");
    const andTheRiver = {
      ...long,
      body: { ...long.body, data: { ...long.body.data, suggestions: [...long.body.data.suggestions, river] } },
    };
    const api = standInApi().inTurn("interpret", "interpret-rules-at-once", () => responseFrom(andTheRiver));
    // The first ranking does not come until the model has read.
    const ranking = api.hold("rank", "rank-one-press");
    api.on("explain_top", "explanations-one-press");
    const { flow, state } = open(api);

    const read = flow.submitText(typedOf(long));
    await arrived();
    ranking.release();
    await read;
    await arrived();

    const last = sentTo(api).at(-1);
    expect(last?.spec).toEqual(atOnce.spec);
    expect(last?.operations).toEqual(merged(takenOfAll(atOnce.suggestions), river.choices[0]?.operations ?? NO_EDITS));
    expect(state().pending).toEqual(NO_EDITS);
    expect(state().phase).toBe("results");
  });

  test("test_a_model_that_does_not_answer_leaves_what_the_rules_read", async () => {
    const api = standInApi()
      .inTurn("interpret", "interpret-rules-at-once", () => {
        throw new TypeError("Failed to fetch");
      })
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");
    const { flow, state } = open(api);

    await flow.submitText(typedOf(long));

    expect(state().read?.more).toBe(false);
    expect(state().read?.took).toBe(labelled(atOnce.suggestions, true).length);
    expect(sentTo(api)).toHaveLength(1);
    expect(state().failure).toBeNull();
  });

  test("test_the_models_reading_is_let_go_when_the_box_changes", async () => {
    const api = standInApi()
      .inTurn("interpret", "interpret-rules-at-once", () => new Promise(() => undefined))
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");
    const { flow, state } = open(api);
    void flow.submitText(typedOf(long));
    await arrived();
    expect(state().read?.more).toBe(true);

    flow.boxChanged();

    expect(state().read).toMatchObject({ more: false, suggestions: [], unread: [] });
    // What was taken stays taken, and what was left is still said.
    expect(state().read?.took).toBe(labelled(atOnce.suggestions, true).length);
    expect(state().read?.left.map((one) => one.label)).toEqual(labelled(atOnce.suggestions, false));
    expect(state().read?.left.map((one) => one.label)).toContain("Gritty");
    // Where the words of a wish stand is known for the text that was sent, and for no other.
    expect(state().read?.words).toEqual([]);
  });

  test("test_a_reading_that_a_second_search_stopped_is_not_said_to_go_on_when_that_search_fails", async () => {
    // Seen in a browser: Search was pressed again, with the box as it was, while the model
    // read. The second call could not leave, and the page said for good that Burro was still
    // reading the rest of the words, though nothing read them.
    const api = standInApi()
      .inTurn(
        "interpret",
        "interpret-rules-at-once",
        () => new Promise(() => undefined),
        () => {
          throw new TypeError("Failed to fetch");
        },
      )
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");
    const { flow, state } = open(api);
    void flow.submitText(typedOf(long));
    await arrived();
    expect(state().read?.more).toBe(true);

    await flow.submitText(typedOf(long));

    expect(state().failure?.kind).toBe("network");
    expect(state().read?.more).toBe(false);
    // What the rules read of the first is ranked still.
    expect(state().ranking).not.toBeNull();
  });

  test("test_a_reading_that_a_second_search_stopped_is_not_said_to_go_on_when_that_search_is_stopped", async () => {
    const never = () => new Promise<Response>(() => undefined);
    const api = standInApi()
      .inTurn("interpret", "interpret-rules-at-once", never, never)
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");
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
    const api = standInApi()
      .inTurn(
        "interpret",
        "interpret-rules-at-once",
        () => new Promise(() => undefined),
        "interpret-rules-at-once",
        () => new Promise(() => undefined),
      )
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");
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

  test("test_a_journey_to_a_place_burro_does_not_know_is_not_sent_and_is_named_among_what_was_left_out", async () => {
    const api = standInApi()
      .on("interpret", "interpret-by-model-place")
      .on("rank", "rank-suggestion-chosen")
      .on("explain_top", "explanations-suggestion-chosen");
    const { flow, state } = open(api);

    await flow.submitText("At most 40 minutes from Mirrowick Basin, ideally");

    expect(api.callsTo("rank")).toEqual([]);
    expect(state().read?.suggestions).toEqual([]);
    expect(state().read?.left.map((one) => one.why)).toEqual(["place"]);
    expect(leftOutOf(state().read).map((thing) => thing.why)).toEqual(["place"]);
    expect(refusals(state().read, null)).toEqual([]);
  });

  test("test_what_the_service_gives_no_way_to_take_is_left_and_nothing_is_sent_of_it", async () => {
    const least = recordedAnswer("interpret", "interpret-by-model-least").body.data;
    const api = standInApi().on("interpret", "interpret-by-model-least");
    const { flow, state } = open(api);

    await flow.submitText("Minimum 45 minutes from Mirrowick Basin, ideally");

    expect(api.callsTo("rank")).toEqual([]);
    expect(state().phase).toBe("empty");
    expect(state().read?.left).toEqual([
      {
        why: "no_way",
        target: least.suggestions[0]?.target,
        label: least.suggestions[0]?.label,
        does: least.suggestions[0]?.does,
        follows: least.suggestions[0]?.follows,
        note: least.suggestions[0]?.note,
      },
    ]);
    expect(refusals(state().read, null)).toEqual([]);
  });

  test("test_one_line_of_the_look_has_more_of_a_thing_that_runs_two_ways_taken_with_the_rest", async () => {
    const api = suggesting();
    const { flow, state } = open(api, meta.reader, { doubt: "more" });

    await flow.submitText("Pubs are so noisy");

    const [pubs] = noticed.suggestions;
    const more = pubs?.choices.find((way) => way.id === "more")?.operations ?? NO_EDITS;
    expect(sentTo(api)).toEqual([{ spec: noticed.spec, limit: 20, operations: merged(NO_EDITS, more) }]);
    // What waits for a person waits whichever way that line is set.
    expect(state().read?.left.map((one) => [one.label, one.why])).toEqual([["Less transport noise", "not_said"]]);
    expect(state().read?.took).toBe(1);
  });

  test("test_a_rule_for_an_area_is_left_whichever_way_that_line_is_set_and_nothing_of_it_is_sent", async () => {
    // What the service gave on 2026-09-26 of an area that was named beside somebody
    // else, edit for edit, laid on an offer that was recorded.
    const [pubs] = noticed.suggestions;
    const noise = lessNoise();
    const ruled = (rule: "only" | "exclude") => ({
      ...NO_EDITS,
      area_ops: [{ action: rule, area_id: "syn-n0018", provenance: "ui_edit" as const }],
    });
    const area = {
      ...pubs!,
      target: "area",
      label: "Pellam Cross",
      choices: [
        { id: "more", direction: "more" as const, label: "Look only in Pellam Cross", guess: false, operations: ruled("only") },
        { id: "less", direction: "less" as const, label: "Leave it out of the results", guess: false, operations: ruled("exclude") },
        ...pubs!.choices.filter((way) => way.id === "ignore"),
      ],
    };
    const recorded = recordedAnswer("interpret", "interpret-suggest");
    const answer = { ...recorded, body: { ...recorded.body, data: { ...noticed, suggestions: [area, noise] } } };

    for (const doubt of ["more", "left"] as const) {
      const api = suggesting().on("interpret", () => responseFrom(answer));
      const { flow, state } = open(api, meta.reader, { doubt });

      await flow.submitText("visiting my mother in a place that is an area, where it is not noisy");

      expect(sentTo(api).map((one) => one.operations?.area_ops)).toEqual([[]]);
      expect(sentTo(api).map((one) => one.operations?.weight_ops.map((edit) => edit.feature_id))).toEqual([["noise_exposure"]]);
      expect(state().read?.left.map((one) => [one.label, one.why])).toEqual([["Pellam Cross", "area"]]);
      expect(leftOutOf(state().read).map((thing) => thing.name)).toEqual(["What to do with Pellam Cross"]);
    }
  });

  /** A sentence of many things, of which two stretches of words are each read three ways or four. */
  const ofManyThings = () =>
    standInApi()
      .on("interpret", "interpret-rules-at-once")
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");

  test("test_as_the_look_is_set_a_word_that_is_read_several_ways_counts_once_and_the_other_readings_are_named", async () => {
    // "Slightly affluent" and "a real identity" are each read more ways than one. Every
    // reading was taken, so a person who wrote "slightly affluent" had three things ranked
    // on. One is, the first the service gives, and its chip says that it was assumed.
    const api = ofManyThings();
    const { flow, state } = open(api);

    await flow.submitText("a sentence of many things, some read more ways than one");

    const [sent] = sentTo(api) as { operations: Operations }[];
    expect(sent?.operations.weight_ops.map((edit) => edit.feature_id)).toEqual([
      "park_proximity",
      "brand_mix",
      "culture_venues_per_homes",
    ]);
    expect(sent?.operations.tag_ops.map((edit) => edit.tag_id)).toEqual(["quiet_residential", "village_feel"]);
    expect(state().read?.left.map((one) => [one.label, one.why])).toEqual([
      ["Gritty", "crime"],
      ["What homes sell for", "otherwise"],
      // What waits for a person says that of itself, and not that the words were read otherwise.
      ["Homes in the higher council tax bands", "by_choice"],
      ["Age of buildings", "otherwise"],
      ["Nearer a town centre", "otherwise"],
    ]);
    for (const key of ["feature:brand_mix", "tag:village_feel"]) {
      expect([key, state().assumed[key]]).toEqual([key, expect.arrayContaining(["weight"])]);
    }
    // Where the words of each wish that was taken stand is kept, as offsets and no word.
    expect(state().read?.words.every((words) => /^\d+-\d+( \d+-\d+)*$/.test(words))).toBe(true);
    expect(state().read?.words).toHaveLength(5);
  });

  test("test_what_the_service_says_waits_for_a_person_is_never_sent_and_is_named_among_what_was_left_out", async () => {
    // What counts recorded crime where the words do not name it, and the share of homes in
    // the higher council tax bands, each wait for a person: the service says so of each.
    const recorded = recordedAnswer("interpret", "interpret-rules-at-once");
    const waits = recorded.body.data.suggestions.filter((offer) => offer.only_by_choice).map((offer) => offer.label);
    expect(waits).toEqual(["Gritty", "Homes in the higher council tax bands"]);

    for (const readings of ["every", "first", "none"] as const) {
      const api = ofManyThings();
      const { flow, state } = open(api, meta.reader, { readings });

      await flow.submitText("a sentence of many things, some read more ways than one");

      const [sent] = sentTo(api) as { operations: Operations }[];
      expect(sent?.operations.weight_ops.map((edit) => edit.feature_id)).not.toContain("homes_higher_bands");
      expect(sent?.operations.tag_ops.map((edit) => edit.tag_id)).not.toContain("street_character");
      const left = new Map(state().read?.left.map((one) => [one.label, one.why]));
      expect([left.get("Gritty"), left.get("Homes in the higher council tax bands")]).toEqual(["crime", "by_choice"]);
    }
  });

  test("test_one_line_of_the_look_has_every_reading_of_such_words_left_out_and_the_rest_taken", async () => {
    const atOnce = recordedAnswer("interpret", "interpret-rules-at-once").body.data;
    const api = ofManyThings();
    const { flow, state } = open(api, meta.reader, { readings: "none" });

    await flow.submitText("a sentence of many things, some read more ways than one");

    const [sent] = sentTo(api) as { operations: Operations }[];
    expect(sent?.operations.weight_ops.map((edit) => edit.feature_id)).toEqual(["park_proximity", "culture_venues_per_homes"]);
    expect(sent?.operations.tag_ops.map((edit) => edit.tag_id)).toEqual(["quiet_residential"]);
    expect(sent?.operations.commute_ops).toHaveLength(1);
    expect(sent?.operations.budget_ops.length).toBeGreaterThan(0);
    // Each reading is named among what was left out, and what counts recorded crime says
    // that of itself, whichever way the line of the look is set.
    expect(state().read?.left.map((one) => [one.label, one.why])).toEqual([
      ["Mix of brands", "several"],
      ["Gritty", "crime"],
      ["What homes sell for", "several"],
      ["Homes in the higher council tax bands", "by_choice"],
      ["Village feel", "several"],
      ["Age of buildings", "several"],
      ["Nearer a town centre", "several"],
    ]);
    expect(state().read?.took).toBe(atOnce.suggestions.length - 7);
  });

  test("test_one_line_of_the_look_has_every_reading_of_such_words_taken_as_it_was", async () => {
    const api = ofManyThings();
    const { flow, state } = open(api, meta.reader, { readings: "every" });

    await flow.submitText("a sentence of many things, some read more ways than one");

    const [sent] = sentTo(api) as { operations: Operations }[];
    expect(sent?.operations.weight_ops.map((edit) => edit.feature_id)).toEqual([
      "park_proximity",
      "brand_mix",
      "price_median",
      "culture_venues_per_homes",
      "highstreet_access",
    ]);
    expect(sent?.operations.tag_ops.map((edit) => edit.tag_id)).toEqual(["quiet_residential", "village_feel", "built_age"]);
    // What waits for a person is no reading that the look may have taken.
    expect(state().read?.left.map((one) => [one.label, one.why])).toEqual([
      ["Gritty", "crime"],
      ["Homes in the higher council tax bands", "by_choice"],
    ]);
    for (const key of ["feature:brand_mix", "feature:price_median", "tag:village_feel", "tag:built_age"]) {
      expect([key, state().assumed[key]]).toEqual([key, expect.arrayContaining(["weight"])]);
    }
  });

  test("test_recorded_crime_that_was_asked_for_by_name_is_sent_with_the_rest_and_its_chip_will_say_what_it_counts", async () => {
    // "Somewhere gritty, I think", and the noise of transport beside it: the service says
    // that the person's own words name the vibe, and marks the way they give.
    const recorded = recordedAnswer("interpret", "interpret-rules-at-once");
    const gritty = recorded.body.data.suggestions.find((offer) => offer.label === "Gritty");
    const noise = lessNoise();
    if (!gritty) throw new Error("a recording holds too little");
    const named = {
      ...gritty,
      by_name: true,
      only_by_choice: false,
      choices: gritty.choices.map((way) => ({ ...way, guess: way.id !== "ignore" })),
    };
    const answer = { ...recorded, body: { ...recorded.body, data: { ...noticed, suggestions: [named, noise] } } };
    const api = suggesting().on("interpret", () => responseFrom(answer));
    const { flow, state } = open(api);

    await flow.submitText("somewhere gritty, I think, where it is not noisy");

    const [sent] = sentTo(api) as { operations: Operations }[];
    expect(sent?.operations.tag_ops.map((edit) => edit.tag_id)).toEqual(["street_character"]);
    expect(sent?.operations.weight_ops.map((edit) => edit.feature_id)).toEqual(["noise_exposure"]);
    expect(state().read?.left).toEqual([]);
    expect(state().read?.took).toBe(2);
    // It is what the person said: nothing of it is said to be assumed.
    expect(state().assumed["tag:street_character"]).toBeUndefined();
    // The same offer, of a service that says that the words name nothing, is left.
    const unnamed = { ...answer, body: { ...answer.body, data: { ...answer.body.data, suggestions: [{ ...named, by_name: false, only_by_choice: true }, noise] } } };
    const other = suggesting().on("interpret", () => responseFrom(unnamed));
    const second = open(other);
    await second.flow.submitText("somewhere posh, where it is not noisy");
    expect((sentTo(other)[0] as { operations: Operations }).operations.tag_ops).toEqual([]);
    expect(second.state().read?.left.map((one) => [one.label, one.why])).toEqual([["Gritty", "crime"]]);
  });

  test("test_a_rule_for_an_area_that_the_service_guesses_at_is_sent_and_is_said_to_be_assumed", async () => {
    const [pubs] = noticed.suggestions;
    const noise = lessNoise();
    const ruled = (rule: "only" | "exclude") => ({
      ...NO_EDITS,
      area_ops: [{ action: rule, area_id: "syn-n0018", provenance: "ui_edit" as const }],
    });
    const area = {
      ...pubs!,
      target: "area",
      label: "Pellam Cross",
      by_name: true,
      choices: [
        { id: "more", direction: "more" as const, label: "Look only in Pellam Cross", guess: false, operations: ruled("only") },
        { id: "less", direction: "less" as const, label: "Leave it out of the results", guess: true, operations: ruled("exclude") },
        ...pubs!.choices.filter((way) => way.id === "ignore"),
      ],
    };
    const recorded = recordedAnswer("interpret", "interpret-suggest");
    const answer = { ...recorded, body: { ...recorded.body, data: { ...noticed, suggestions: [area, noise] } } };
    const api = suggesting().on("interpret", () => responseFrom(answer));
    const { flow, state } = open(api);

    await flow.submitText("anywhere but an area that is named, honestly, where it is not noisy");

    expect(sentTo(api).map((one) => one.operations?.area_ops)).toEqual([ruled("exclude").area_ops]);
    expect(state().read?.left).toEqual([]);
    expect(state().assumed["area:syn-n0018"]).toEqual(["rule"]);
    // A rule that a person then sets by hand is theirs, and says nothing of the kind.
    await flow.applyEdits(edits.areaHide("syn-n0018"));
    expect(state().assumed["area:syn-n0018"]).toBeUndefined();
  });

  test("test_a_thing_the_words_turn_away_is_counted_no_longer_where_the_service_marks_that_as_its_guess", async () => {
    // "Honestly, no station": the station counts a little in every search until a person
    // says otherwise. All that is offered of it is to stop counting it.
    const station = counted.suggestions.find((offer) => offer.label === "Nearer a station");
    const stop = station?.choices.find((way) => way.id === "off");
    if (!station || !stop) throw new Error("the recording holds too little");
    const turnedAway = {
      ...station,
      add_all: "",
      choices: station.choices.filter((way) => way.id !== "more").map((way) => ({ ...way, guess: way.id === "off" })),
    };
    const recorded = recordedAnswer("interpret", "interpret-suggest-who-is-counted");
    const answer = { ...recorded, body: { ...recorded.body, data: { ...counted, suggestions: [turnedAway] } } };
    const api = suggesting().on("interpret", () => responseFrom(answer));
    const { flow, state } = open(api);

    await flow.submitText("honestly, no station");

    expect(sentTo(api)).toEqual([{ spec: counted.spec, limit: 20, operations: merged(NO_EDITS, stop.operations) }]);
    expect(stop.operations.weight_ops.map((edit) => [edit.action, edit.feature_id])).toEqual([["remove", "station_walk"]]);
    expect(state().read?.left).toEqual([]);
    expect(state().assumed["feature:station_walk"]).toBeUndefined();

    // The other way it was built leaves it, and says why in the service's words.
    const other = suggesting().on("interpret", () => responseFrom(answer));
    const left = open(other, meta.reader, { turned: "left" });
    await left.flow.submitText("honestly, no station");
    expect(sentTo(other)).toEqual([]);
    expect(left.state().read?.left.map((one) => [one.label, one.why])).toEqual([["Nearer a station", "no_way"]]);
  });

  test("test_what_was_not_read_goes_when_the_box_changes", async () => {
    const { flow, state } = open(suggesting());
    await flow.submitText("Pubs are so noisy");
    expect(state().read?.unread.length).toBeGreaterThan(0);

    flow.boxChanged();

    expect(state().read?.suggestions).toEqual([]);
    expect(state().read?.unread).toEqual([]);
  });
});

describe("a first search waits for Burro to be seen", () => {
  /** How long the search is told to wait, in a test of the wait: a round of two seconds. */
  const WAIT = 2_000;
  const waiting = { rests: () => WAIT };
  /** Lets the clock of the test run on by so much, and what it set going arrive. */
  const later = async (milliseconds: number) => {
    await jest.advanceTimersByTimeAsync(milliseconds);
  };

  beforeEach(() => {
    jest.useFakeTimers();
  });

  test("test_the_answer_to_a_first_sentence_is_shown_no_sooner_than_the_wait_is_over_however_fast_the_service", async () => {
    const api = firstSearch();
    const { flow, state } = open(api, meta.reader, waiting);

    const sent = flow.submitText("leafy and quiet");
    await later(WAIT - 1);

    // The service has answered. Nothing of its answer is on the page: Burro hops.
    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(state().phase).toBe("interpreting");
    expect(state().read).toBeNull();
    expect(state().ranking).toBeNull();
    expect(state().spec).toEqual(meta.defaults.rent);

    await later(1);
    await sent;

    expect(state().phase).toBe("results");
    expect(state().read).not.toBeNull();
    expect(state().ranking).not.toBeNull();
  });

  test("test_a_service_that_takes_longer_than_the_wait_is_waited_for_and_no_longer", async () => {
    const api = firstSearch();
    const slow = api.hold("interpret", "interpret-first");
    const { flow, state } = open(api, meta.reader, waiting);

    const sent = flow.submitText("leafy and quiet");
    await later(WAIT * 3);
    expect(state().phase).toBe("interpreting");

    slow.release();
    await later(0);
    await sent;

    // Nothing is added to what the service took: the wait was over before it answered.
    expect(state().phase).toBe("results");
    expect(state().ranking).not.toBeNull();
  });

  test("test_a_first_ranking_that_a_control_asked_for_waits_as_a_first_sentence_does", async () => {
    const api = firstSearch();
    const { flow, state } = open(api, meta.reader, waiting);

    const ranked = flow.applyEdits(edits.tagOn("leafy"));
    await later(WAIT - 1);

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(state().phase).toBe("refining");
    expect(state().ranking).toBeNull();

    await later(1);
    await ranked;

    expect(state().ranking).not.toBeNull();
  });

  test("test_a_search_that_is_refined_with_its_results_in_sight_waits_for_nothing", async () => {
    const api = firstSearch();
    const { flow, state } = open(api, meta.reader, waiting);
    const first = flow.submitText("leafy and quiet");
    await later(WAIT);
    await first;
    expect(state().ranking).not.toBeNull();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    const refined = recordedAnswer("rank", "rank-refined").body.data;

    const moved = flow.applyEdits(edits.tagOn("parks_close_by"));
    await later(0);
    await moved;

    expect(state().spec).toEqual(refined.spec);
    // Nor does a second sentence, sent with the results of the first in sight.
    api.on("interpret", "interpret-second-sentence").on("rank", "rank-second-sentence");
    const second = flow.submitText("and near a park");
    await later(0);
    await second;
    expect(state().spec).toEqual(recordedAnswer("rank", "rank-second-sentence").body.data.spec);
  });

  test("test_a_failure_is_said_at_once_and_nobody_waits_to_be_told_that_nothing_came", async () => {
    const api = firstSearch().unreachable("interpret");
    const { flow, state } = open(api, meta.reader, waiting);

    const sent = flow.submitText("leafy and quiet");
    await later(0);
    await sent;

    expect(state().failure?.kind).toBe("network");
    expect(state().phase).toBe("empty");
  });

  test("test_a_search_that_is_stopped_waits_no_longer_and_the_next_one_waits_as_a_first_one_does", async () => {
    const api = firstSearch();
    const { flow, state } = open(api, meta.reader, waiting);
    const stoppedOne = flow.submitText("leafy and quiet");
    await later(WAIT / 2);

    flow.stop();
    await later(0);
    await stoppedOne;

    expect(state().phase).toBe("empty");
    expect(state().read).toBeNull();
    // What was held back is never shown, however long the clock runs on.
    await later(WAIT * 2);
    expect(state().ranking).toBeNull();

    const next = flow.submitText("leafy and quiet");
    await later(WAIT - 1);
    expect(state().ranking).toBeNull();
    await later(1);
    await next;
    expect(state().ranking).not.toBeNull();
  });

  test("test_a_sentence_sent_again_before_its_answer_is_shown_waits_no_longer_for_it", async () => {
    const api = firstSearch();
    const { flow, state } = open(api, meta.reader, waiting);
    void flow.submitText("leafy");
    await later(WAIT - 500);

    const again = flow.submitText("leafy and quiet");
    await later(500);
    await again;

    expect(state().ranking).not.toBeNull();
  });

  test("test_what_the_second_way_in_gathers_waits_for_nothing_and_the_search_made_of_it_does", async () => {
    const api = firstSearch();
    const { flow, state } = open(api, meta.reader, waiting);

    const gathered = flow.applyEdits(edits.tagOn("leafy"), "gather");
    await later(0);
    await gathered;
    expect(state().gathering).toBe(true);
    expect(state().untouched).toBe(false);
    // Long after, its button is pressed: the search that opens of it is a first search.
    await later(WAIT * 5);

    const ranked = flow.rankNow();
    await later(WAIT - 1);
    expect(state().ranking).toBeNull();
    await later(1);
    await ranked;
    expect(state().ranking).not.toBeNull();
  });

  test("test_words_of_which_nothing_came_are_answered_after_the_wait_and_the_next_search_waits_again", async () => {
    const api = firstSearch().on("interpret", "interpret-nothing-read");
    const { flow, state } = open(api, meta.reader, waiting);

    const sent = flow.submitText("asdf qwer zxcv");
    await later(WAIT - 1);
    expect(state().read).toBeNull();
    await later(1);
    await sent;
    expect(state().read).not.toBeNull();
    expect(state().ranking).toBeNull();

    api.on("interpret", "interpret-first");
    const next = flow.submitText("leafy and quiet");
    await later(WAIT - 1);
    expect(state().ranking).toBeNull();
    await later(1);
    await next;
    expect(state().ranking).not.toBeNull();
  });

  test("test_with_nothing_said_of_how_long_nothing_is_waited_for", async () => {
    const api = firstSearch();
    const { flow, state } = open(api);

    const sent = flow.submitText("leafy and quiet");
    await later(0);
    await sent;

    expect(state().ranking).not.toBeNull();
  });
});
