/**
 * What a person set by hand is never set back by words the search has already read.
 *
 * Seen in a browser, against the service: a person typed a sentence and searched, set the
 * budget, the journey and a vibe by hand, typed more after the sentence in the same box,
 * and searched again. The box is labelled "Add to this search", and all that it held was
 * sent, with the search as it stood. So the first sentence was read a second time, onto
 * the search that had been set by hand: the budget, the journey and the vibe were as the
 * sentence says again, a vibe nobody had touched counted for more, and nothing said so.
 *
 * The first test answers a request only if it is, to the letter, a request the service
 * was sent when the walk was recorded (`record_what_was_added` in `test/record.py`), where
 * each request is made of the answer before it. So what it shows is what the service
 * said of that very search.
 */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useEffect } from "react";

import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { ADDED } from "@/content/added";
import { CHIPS, EXAMPLES, FAILURE, NOTICE, PROMPT, SUGGEST } from "@/content/search";
import { BUDGET, JOURNEY, SLIDER } from "@/content/settings";
import { recordedAnswer, responseFrom } from "@/lib/api/recorded";
import type { InterpretBody, InterpretData, RankData } from "@/lib/api/schema";
import { inTheBox } from "@/lib/search/spans";
import type { SearchState } from "@/lib/search/state";
import { useSessionIfAny } from "@/lib/session/session";

import { setOnline, type Responder, type StandIn } from "../support/api";
import {
  areas,
  arrived,
  bands,
  CANARY,
  firstSearch,
  helper,
  meta,
  openSearch,
  promptBox,
  results,
  search,
  settled,
} from "../support/search";
import { stepOf, walkApi } from "../support/visit";
import { watch } from "../support/watch";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

type User = ReturnType<typeof userEvent.setup>;

interface Enveloped<Data> {
  readonly data: Data;
}
const answerOf = <Data,>(name: string) => stepOf<Enveloped<Data>>("added", name).body.data;
const sentenceOf = (name: string) => (stepOf("added", name).request.body as InterpretBody).text;
const nameOf = (areaId: string | undefined) => areas.find((area) => area.area_id === areaId)?.name ?? "no such area";
/** What the search holds, as it is drawn under the box. */
const understood = () => within(screen.getByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel})$`) }));
const chip = (name: RegExp) => understood().getByRole("button", { name });

const status = () => screen.getAllByRole("status").map((line) => line.textContent ?? "");
/** What was sent to be read, in the order it was sent: the body of each call to route 1. */
const sentToBeRead = (api: StandIn) => api.callsTo("interpret").map((call) => call.body as InterpretBody);
/** What is selected in the box, cut from the box. */
const selected = () => promptBox().value.slice(promptBox().selectionStart, promptBox().selectionEnd);
const searchButton = () => screen.getByRole("button", { name: PROMPT.submit });

/** Where the words stand in the text, counted as the API counts: in code points, from its start. */
function where(text: string, words: string) {
  const start = Array.from(text.slice(0, text.indexOf(words))).length;
  return { start, end: start + Array.from(words).length };
}

/** A reading as it was recorded, with some of what it holds changed, as the service answers other words. */
function reading(scenario: string, change: (data: InterpretData) => Partial<InterpretData>): Responder {
  const recorded = recordedAnswer("interpret", scenario);
  return () =>
    responseFrom({ ...recorded, body: { ...recorded.body, data: { ...recorded.body.data, ...change(recorded.body.data) } } });
}

/** Answers what is sent next as a second sentence was answered when it was recorded, with its ranking and its reasons. */
const answersASecond = (api: StandIn) =>
  api
    .on("interpret", "interpret-second-sentence")
    .on("rank", "rank-second-sentence")
    .on("explain_top", "explanations-second-sentence");

/** Puts words in the box where the caret stands, all at once, as a paste does. The caret is put at the end first. */
async function addToTheBox(user: User, words: string) {
  await user.click(promptBox());
  await user.paste(words);
}

/** How much a vibe counts in a search, of 100, as its field says it. */
const countsFor = (spec: InterpretData["spec"], tagId: string) =>
  String(Math.round((spec.tags.find((tag) => tag.tag_id === tagId)?.weight ?? 0) * 100));

/**
 * Sets a number by hand: in the control that the chip opens, where the chip stands. The
 * control is shut again, by the chip as it is then named.
 */
async function setByHand(user: User, opens: RegExp, field: string, value: number, then = opens) {
  await user.click(chip(opens));
  const number = screen.getByRole("textbox", { name: field });
  await user.clear(number);
  await user.type(number, `${value}{Enter}`);
  await settled();
  await user.click(chip(then));
}

/** What the number field of a chip says, which is what the search holds. */
async function standsAt(user: User, opens: RegExp, field: string): Promise<string> {
  await user.click(chip(opens));
  const stands = screen.getByRole<HTMLInputElement>("textbox", { name: field }).value;
  await user.click(chip(opens));
  return stands;
}

/**
 * True where the page says these words to whoever hears it, and says them once: in a line
 * of their own, or in a notice that says of itself what changes in it.
 */
const isHeardOnce = (words: string) =>
  screen.getAllByRole("status").filter((line) => line.textContent?.includes(words)).length === 1 &&
  (document.body.textContent?.split(words).length ?? 0) === 2;

beforeEach(() => setOnline(true));

describe("words added to a search that was set by hand", () => {
  test("test_what_was_set_by_hand_stands_when_more_is_typed_after_a_sentence_that_was_read", async () => {
    const api = walkApi("added");
    const user = userEvent.setup({ delay: null });
    render(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} />
      </Shell>,
    );
    await arrived();
    const first = sentenceOf("first");
    const more = sentenceOf("more");
    const read = answerOf<InterpretData>("first").spec;
    const set = answerOf<RankData>("leafy-rank").spec;

    // A sentence is typed and read: a budget that is a firm limit, two vibes and a journey.
    await user.type(promptBox(), first);
    await user.keyboard("{Enter}");
    await settled();
    expect([read.budget.amount, read.commutes.map((one) => one.max_minutes)]).toEqual([1700, [35]]);
    expect([countsFor(read, "leafy"), countsFor(read, "quiet_residential")]).toEqual(["50", "50"]);
    expect(chip(/^£1,700 a month/)).toBeInTheDocument();

    // Three things are set by hand: the budget, the longest the journey may take, and a vibe.
    await setByHand(user, /^£1,700 a month/, BUDGET.amount.rent, 1800, /^£1,800 a month/);
    await setByHand(user, /^Cindermoor Works/, JOURNEY.longest, 30);
    await setByHand(user, /^Leafy/, SLIDER.number("Leafy"), 80);
    expect([set.budget.amount, set.commutes.map((one) => one.max_minutes)]).toEqual([1800, [30]]);
    expect([countsFor(set, "leafy"), countsFor(set, "quiet_residential")]).toEqual(["80", "50"]);

    // More is typed after the sentence, in the box that says "Add to this search".
    await user.type(promptBox(), more);
    expect(promptBox().value === `${first}${more}`).toBe(true);
    await user.keyboard("{Enter}");
    await settled();

    // Every request was one the service answered when the walk was recorded. What was sent
    // to be read is what was added, with the search as it was set by hand: a request that
    // holds the first sentence again is no step of the walk, and is not answered.
    expect(api.unanswered).toEqual([]);
    expect(api.unused()).toEqual([]);
    expect(more.includes(first)).toBe(false);

    // What was set by hand stands, and what nobody touched is as it was.
    const added = answerOf<RankData>("more-rank");
    expect(chip(/^£1,800 a month/)).toBeInTheDocument();
    expect(understood().queryByRole("button", { name: /^£1,700 a month/ })).toBeNull();
    expect(chip(/^Cindermoor Works/).textContent?.includes("30 minutes")).toBe(true);
    expect(chip(/^Cindermoor Works/).textContent?.includes("35 minutes")).toBe(false);
    expect(await standsAt(user, /^£1,800 a month/, BUDGET.amount.rent)).toBe("1800");
    expect(await standsAt(user, /^Cindermoor Works/, JOURNEY.longest)).toBe("30");
    expect(await standsAt(user, /^Leafy/, SLIDER.number("Leafy"))).toBe("80");
    expect(await standsAt(user, /^Quiet streets/, SLIDER.number("Quiet streets"))).toBe("50");
    expect([added.spec.budget.amount, added.spec.commutes.map((one) => one.max_minutes)]).toEqual([1800, [30]]);

    // What was added is in the search: one thing more, and one taken off.
    const highStreet = meta.data.features.find((one) => one.feature_id === "highstreet_access")?.short_label ?? "";
    expect(chip(new RegExp(`^${highStreet}`)).textContent?.includes(CHIPS.off)).toBe(true);
    expect(results()[0]).toHaveTextContent(nameOf(added.ranked[0]?.area_id));
    // The box holds all that was typed, as it was typed.
    expect(promptBox().value === `${first}${more}`).toBe(true);
  }, 120_000);
});

describe("what is sent to be read once the search has read what the box holds", () => {
  const first = "leafy and quiet";

  test("test_search_with_nothing_new_in_the_box_sends_nothing_and_the_page_says_why", async () => {
    // It sent all that the box held again. Sent twice, a sentence made what it names count for more.
    const { user, api } = await openSearch();
    await search(user, first);
    const before = { calls: api.calls.length, results: results().length };

    await user.click(searchButton());
    await arrived();

    expect(api.calls).toHaveLength(before.calls);
    expect(screen.getByRole("alert")).toHaveTextContent(ADDED.nothingNew);
    expect(promptBox()).toHaveAccessibleDescription(ADDED.nothingNew);
    // The focus is in the box, and the answer is as it was.
    expect(promptBox()).toHaveFocus();
    expect(results()).toHaveLength(before.results);
    // It goes when something is typed.
    await user.type(promptBox(), " ");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("test_a_change_among_the_words_that_were_read_is_not_read_and_the_page_says_so", async () => {
    // Nothing holds the words as they were, so nobody can say what was changed to what. To
    // read the sentence again is to set back what was set by hand since.
    const { user, api } = await openSearch();
    await search(user, first);

    // "and" is typed over with "but".
    await user.type(promptBox(), "but", { initialSelectionStart: 6, initialSelectionEnd: 9 });
    await user.click(searchButton());
    await arrived();

    expect(promptBox().value === "leafy but quiet").toBe(true);
    expect(sentToBeRead(api)).toHaveLength(1);
    expect(screen.getByRole("alert")).toHaveTextContent(ADDED.changed);
    expect(promptBox()).toHaveFocus();

    // What is then added at the end is read, by itself, and the change is said not to have been.
    answersASecond(api);
    await user.type(promptBox(), ", more green space");
    await user.keyboard("{Enter}");
    await settled();

    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, ", more green space"]);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(status()).toContain(ADDED.changedToo);
    // Once it has been said it is not said again.
    await user.type(promptBox(), " and a park");
    expect(status()).not.toContain(ADDED.changedToo);
    await user.keyboard("{Enter}");
    await settled();
    expect(sentToBeRead(api).at(-1)?.text).toBe("and a park");
    expect(status()).not.toContain(ADDED.changedToo);
  });

  test("test_what_is_typed_over_the_end_of_what_was_read_is_new", async () => {
    const { user, api } = await openSearch();
    await search(user, first);
    answersASecond(api);

    // The last word is taken out, and another typed where it stood.
    await user.type(promptBox(), "{Backspace}{Backspace}{Backspace}{Backspace}{Backspace}lively");
    await user.keyboard("{Enter}");
    await settled();

    expect(promptBox().value === "leafy and lively").toBe(true);
    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, "lively"]);
  });

  test("test_a_box_that_is_emptied_by_hand_adds_what_is_typed_next_to_the_search_as_it_stands", async () => {
    const { user, api } = await openSearch();
    await search(user, first);
    const asItStands = recordedAnswer("rank", "rank-first").body.data.spec;
    answersASecond(api);

    await user.clear(promptBox());
    await search(user, "more green space");

    expect(sentToBeRead(api).at(-1)).toEqual({ text: "more green space", spec: asItStands, ask_model: false });
    expect(screen.queryByRole("alert")).toBeNull();
    // And so does a sentence typed over all that the box holds.
    await user.type(promptBox(), "near a park", { initialSelectionStart: 0, initialSelectionEnd: promptBox().value.length });
    await user.keyboard("{Enter}");
    await settled();
    expect(sentToBeRead(api).at(-1)?.text).toBe("near a park");
  });

  test("test_start_again_begins_a_search_that_has_read_nothing_and_an_example_is_sent_whole", async () => {
    const { user, api } = await openSearch();
    await search(user, first);

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    // The helpers are back, every one closed as it first stood: an example is one press
    // away. It fills the box, in place of what is there, and sends nothing.
    await user.type(promptBox(), "quiet");
    const example = EXAMPLES[0] as string;
    expect(screen.queryByRole("button", { name: example })).toBeNull();
    await helper(user, "example");
    await user.click(screen.getByRole("button", { name: example }));
    expect(promptBox().value === example).toBe(true);
    expect(sentToBeRead(api)).toHaveLength(1);
    await user.click(searchButton());
    await settled();

    expect(sentToBeRead(api).at(-1)).toEqual({ text: example, spec: meta.data.defaults.rent, ask_model: false });
  });

  test("test_start_again_beside_a_failure_leaves_the_box_and_the_new_search_reads_all_of_it", async () => {
    // It begins the search again and leaves the box as it is. What the box holds was read
    // by the search before, and not by this one.
    const { user, api } = await openSearch(firstSearch().on("rank", "error-internal"));
    await user.type(promptBox(), first);
    await user.click(searchButton());
    const failure = within(await screen.findByRole("alert"));
    await arrived();

    await user.click(failure.getByRole("button", { name: PROMPT.startAgain }));
    api.on("rank", "rank-first");
    await user.click(searchButton());
    await settled();

    expect(promptBox().value === first).toBe(true);
    expect(sentToBeRead(api)).toEqual([
      { text: first, spec: meta.data.defaults.rent, ask_model: false },
      { text: first, spec: meta.data.defaults.rent, ask_model: false },
    ]);
  });

  test("test_words_that_could_not_be_sent_are_sent_again_by_try_again_and_by_search", async () => {
    const { user, api } = await openSearch();
    await search(user, first);
    api.unreachable("interpret");

    await user.type(promptBox(), ", more green space");
    await user.click(searchButton());
    const failure = within(await screen.findByRole("alert"));
    await arrived();
    expect(failure.getByText(FAILURE.network)).toBeInTheDocument();

    // They were not read, so they are what is sent: by "Try again", and by Search.
    await user.click(failure.getByRole("button", { name: PROMPT.tryAgain }));
    await screen.findByRole("alert");
    await arrived();
    answersASecond(api);
    await user.click(searchButton());
    await settled();

    expect(sentToBeRead(api).map((body) => body.text)).toEqual([
      first,
      ", more green space",
      ", more green space",
      ", more green space",
    ]);
    // Now they are read, and are not sent again.
    await user.click(searchButton());
    expect(sentToBeRead(api)).toHaveLength(4);
    expect(screen.getByRole("alert")).toHaveTextContent(ADDED.nothingNew);
  });

  test("test_words_that_were_stopped_were_not_read_and_are_sent_again", async () => {
    const { user, api } = await openSearch();
    await search(user, first);
    api.silent("interpret");

    await user.type(promptBox(), ", more green space");
    await user.click(searchButton());
    await user.click(await screen.findByRole("button", { name: PROMPT.stop }));
    answersASecond(api);
    await user.click(searchButton());
    await settled();

    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, ", more green space", ", more green space"]);
  });

  test("test_where_a_model_reads_it_is_asked_of_what_was_added_and_of_nothing_before_it", async () => {
    const { user, api } = await openSearch();
    await search(user, `${first} ${CANARY}`);
    api.inTurn("interpret", "interpret-rules-at-once", "interpret-by-model-long");

    await user.type(promptBox(), ", quiet, honestly");
    await user.click(searchButton());
    await waitFor(() => expect(sentToBeRead(api)).toHaveLength(3));
    await settled();

    const sent = sentToBeRead(api).slice(1);
    expect(sent.map((body) => [body.text, body.ask_model])).toEqual([
      [", quiet, honestly", false],
      [", quiet, honestly", true],
    ]);
    expect(sent.some((body) => body.text.includes(CANARY))).toBe(false);
  });

  test("test_a_box_that_is_drawn_again_is_empty_and_what_is_typed_in_it_is_sent_whole", async () => {
    // A person who goes to another page and comes back finds the search and an empty box:
    // what was typed was nowhere else.
    const api = firstSearch();
    const user = userEvent.setup({ delay: null });
    const page = () => <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} />;
    const view = render(<Shell meta={meta.meta}>{page()}</Shell>);
    await arrived();
    await search(user, first);
    const asItStands = recordedAnswer("rank", "rank-first").body.data.spec;

    view.rerender(
      <Shell meta={meta.meta}>
        <p>Another page</p>
      </Shell>,
    );
    view.rerender(<Shell meta={meta.meta}>{page()}</Shell>);
    await settled();
    expect(promptBox()).toHaveValue("");
    expect(results().length).toBeGreaterThan(0);
    answersASecond(api);
    // Longer than what was read before, so that a count kept from the box before would cut it.
    const next = "more green space, and ignore the high street";
    await search(user, next);

    expect(next.length).toBeGreaterThan(first.length);
    expect(sentToBeRead(api).at(-1)).toEqual({ text: next, spec: asItStands, ask_model: false });
  });
});

describe("words that were read and come back into the box", () => {
  // Seen in a browser, against the service, on a search that had been set by hand: the
  // whole of the box was selected and a letter typed over it, by accident, and the keys
  // that undo put the sentence back. Search sent the sentence again, and the budget, the
  // journey and a vibe were as it says again. So with the end of it taken out and put back.
  const first = "leafy and quiet";

  /**
   * What a browser does when the keys that undo are pressed: the box holds what it held at
   * another time, with what came back selected, and says that it was undone.
   */
  function undoTo(holds: string, selected = { start: 0, end: holds.length }, how = "historyUndo") {
    promptBox().value = holds;
    promptBox().setSelectionRange(selected.start, selected.end);
    fireEvent.input(promptBox(), { inputType: how });
  }

  /** Selects so much of the box, as a person does with the keys or by dragging over it. */
  async function select(user: User, start: number, end: number) {
    await user.click(promptBox());
    promptBox().setSelectionRange(start, end);
    fireEvent.select(promptBox());
  }

  async function nothingIsSent(api: StandIn, user: User, says: string) {
    const sent = sentToBeRead(api).length;
    await user.click(searchButton());
    await arrived();
    expect(sentToBeRead(api)).toHaveLength(sent);
    expect(screen.getByRole("alert")).toHaveTextContent(says);
  }

  test("test_words_that_the_keys_that_undo_put_back_are_not_read_a_second_time", async () => {
    const { user, api } = await openSearch();
    await search(user, first);

    // " quiet" is selected and taken out, and the keys that undo put it back.
    await user.type(promptBox(), "{Backspace}", { initialSelectionStart: 9, initialSelectionEnd: 15 });
    expect(promptBox().value === "leafy and").toBe(true);
    undoTo(first, { start: 9, end: 15 });
    await nothingIsSent(api, user, ADDED.nothingNew);

    // All of it is typed over with one letter, and put back.
    await user.type(promptBox(), "x", { initialSelectionStart: 0, initialSelectionEnd: 15 });
    expect(promptBox().value === "x").toBe(true);
    undoTo(first);
    await nothingIsSent(api, user, ADDED.nothingNew);

    // All of it is taken out, and put back.
    await user.clear(promptBox());
    undoTo(first);
    await nothingIsSent(api, user, ADDED.nothingNew);

    // What is then typed after it is what is sent, with the search as it stands.
    const asItStands = recordedAnswer("rank", "rank-first").body.data.spec;
    answersASecond(api);
    await user.type(promptBox(), ", more green space");
    await user.keyboard("{Enter}");
    await settled();
    expect(sentToBeRead(api)).toEqual([
      { text: first, spec: meta.data.defaults.rent, ask_model: false },
      { text: ", more green space", spec: asItStands, ask_model: false },
    ]);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(status()).not.toContain(ADDED.changedToo);
  });

  test("test_what_is_put_back_after_more_was_done_to_the_box_is_not_read_and_the_page_says_so", async () => {
    // " quiet" is taken out and "near" typed where it stood. The keys that undo are pressed
    // twice: "near" goes, and " quiet" comes back. Nobody can tell it from what was read.
    const { user, api } = await openSearch();
    await search(user, first);
    await user.type(promptBox(), "{Backspace}near", { initialSelectionStart: 9, initialSelectionEnd: 15 });
    expect(promptBox().value === "leafy andnear").toBe(true);

    undoTo("leafy and", { start: 9, end: 9 });
    undoTo(first, { start: 9, end: 15 });

    await nothingIsSent(api, user, ADDED.changed);
    // What is added at the end is read, and that the words before it were not is said once.
    answersASecond(api);
    await user.type(promptBox(), ", more green space");
    await user.keyboard("{Enter}");
    await settled();
    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, ", more green space"]);
    expect(status()).toContain(ADDED.changedToo);
  });

  test("test_words_that_were_typed_over_and_read_bring_nothing_back_to_be_read_when_they_are_undone", async () => {
    // " quiet" is typed over with " calm", which is sent and read. The keys that undo then
    // put " quiet" back where " calm" stood: it stands after the place the search had read to.
    const { user, api } = await openSearch();
    await search(user, first);
    answersASecond(api);
    await user.type(promptBox(), " calm", { initialSelectionStart: 9, initialSelectionEnd: 15 });
    await user.keyboard("{Enter}");
    await settled();
    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, "calm"]);

    undoTo(first, { start: 9, end: 15 });

    await nothingIsSent(api, user, ADDED.changed);
  });

  test("test_what_was_typed_and_not_read_is_sent_still_when_it_is_undone_and_done_again", async () => {
    const { user, api } = await openSearch();
    await search(user, first);
    answersASecond(api);
    await user.type(promptBox(), ", more green space");

    undoTo(first, { start: 15, end: 15 });
    undoTo(`${first}, more green space`, { start: 33, end: 33 }, "historyRedo");
    await user.keyboard("{Enter}");
    await settled();

    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, ", more green space"]);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(status()).not.toContain(ADDED.changedToo);
  });

  test("test_the_keys_that_undo_pressed_again_bring_back_no_word_to_be_read_a_second_time", async () => {
    // Found by changing many boxes at random. "leafy and quiet" is read. " and quiet" is
    // taken out, " by a park" typed where it stood and read, and "ok" typed after it: the
    // box holds seventeen letters, of which fifteen were read. The keys that undo take out
    // all that was typed, and pressed again they put " and quiet" back. The box is as long
    // as it was, and all that it holds was read.
    const { user, api } = await openSearch();
    await search(user, first);
    answersASecond(api);
    await user.type(promptBox(), "{Backspace} by a park", { initialSelectionStart: 5, initialSelectionEnd: 15 });
    await user.keyboard("{Enter}");
    await settled();
    await user.type(promptBox(), "ok");
    expect(promptBox().value === "leafy by a parkok").toBe(true);
    expect(promptBox().value).toHaveLength(17);

    undoTo("leafy", { start: 5, end: 5 });
    undoTo("leafy and quietok".slice(0, 15) + "ok", { start: 5, end: 15 });

    expect(promptBox().value).toHaveLength(17);
    await user.click(searchButton());
    await arrived();
    // "ok" was never read, and is all that is sent. No word of the sentence is.
    const texts = sentToBeRead(api).map((body) => body.text);
    expect(texts.slice(0, 2)).toEqual([first, "by a park"]);
    expect(texts.slice(2).join(" ").includes("quiet")).toBe(false);
    expect(texts.slice(2).join(" ").includes("leafy")).toBe(false);
  });

  test("test_what_the_keys_that_do_again_put_back_is_read_where_none_of_it_was", async () => {
    // A sentence from elsewhere is pasted over all of the box. The keys that undo put back
    // what was read, and the keys that do again the sentence, of which nothing was read.
    const { user, api } = await openSearch();
    await search(user, first);
    answersASecond(api);
    await select(user, 0, 15);
    await user.paste("more green space");

    undoTo(first);
    await nothingIsSent(api, user, ADDED.nothingNew);
    undoTo("more green space", { start: 16, end: 16 }, "historyRedo");
    await user.click(searchButton());
    await settled();

    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, "more green space"]);
  });

  test("test_what_was_copied_before_it_was_read_is_not_read_again_once_the_box_is_typed_over", async () => {
    // Found by changing many boxes at random. The sentence is copied, and then sent. All
    // of the box is typed over with a letter, and the sentence pasted after the letter.
    const { user, api } = await openSearch();
    await user.type(promptBox(), first);
    await select(user, 0, 15);
    await user.copy();
    promptBox().setSelectionRange(15, 15);
    await user.keyboard("{Enter}");
    await settled();
    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first]);

    await user.type(promptBox(), "x", { initialSelectionStart: 0, initialSelectionEnd: 15 });
    await user.paste();
    expect(promptBox().value === `x${first}`).toBe(true);

    await nothingIsSent(api, user, ADDED.changed);
  });

  test("test_a_copy_of_what_was_read_that_is_pasted_into_the_box_is_not_read_again", async () => {
    // All of it selected, copied and pasted over itself leaves the box as it was.
    const { user, api } = await openSearch();
    await search(user, first);

    await select(user, 0, 15);
    await user.copy();
    await user.paste();
    expect(promptBox().value === first).toBe(true);
    await nothingIsSent(api, user, ADDED.changed);

    // Pasted after itself.
    promptBox().setSelectionRange(15, 15);
    await user.paste();
    expect(promptBox().value === `${first}${first}`).toBe(true);
    await nothingIsSent(api, user, ADDED.changed);

    // Cut out to be pasted elsewhere, and pasted back.
    await select(user, 0, 30);
    await user.cut();
    expect(promptBox()).toHaveValue("");
    await user.paste();
    await nothingIsSent(api, user, ADDED.changed);

    // Words that come from elsewhere are new, and are sent.
    answersASecond(api);
    promptBox().setSelectionRange(30, 30);
    await user.paste(", more green space");
    await user.keyboard("{Enter}");
    await settled();
    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, ", more green space"]);
  });

  test("test_what_was_copied_from_a_search_is_new_to_the_search_that_begins_after_it", async () => {
    // A person copies their sentence, starts again, and pastes it to begin from.
    const { user, api } = await openSearch();
    await search(user, first);
    await select(user, 0, 15);
    await user.copy();

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    await user.paste();
    await user.keyboard("{Enter}");
    await settled();

    expect(sentToBeRead(api)).toEqual([
      { text: first, spec: meta.data.defaults.rent, ask_model: false },
      { text: first, spec: meta.data.defaults.rent, ask_model: false },
    ]);
  });
});

describe("where the words stand when what was added was sent without the words before it", () => {
  // A character that a browser counts as two and the service as one, in the words that
  // were read and again in those that are added.
  const first = "Leafy \u{1F333} and quiet";
  const more = ". Pubs \u{1F37A} are so noisy";
  const sent = more.trim();
  const noticed = reading("interpret-suggest", (data) => ({
    unread: [where(sent, "are so")],
    suggestions: data.suggestions.map((one, at) => ({
      ...one,
      spans: [where(sent, at === 0 ? "Pubs" : "noisy")],
      shown: where(sent, sent.slice(2)),
    })),
  }));

  async function added() {
    const opened = await openSearch();
    await addToTheBox(opened.user, first);
    await opened.user.keyboard("{Enter}");
    await settled();
    opened.api.on("interpret", noticed);
    await addToTheBox(opened.user, more);
    await opened.user.keyboard("{Enter}");
    await waitFor(() => expect(sentToBeRead(opened.api)).toHaveLength(2));
    await settled();
    return opened;
  }

  test("test_the_service_counts_from_the_start_of_what_it_was_sent_and_not_of_the_box", async () => {
    const { api } = await added();

    expect(promptBox().value === `${first}${more}`).toBe(true);
    expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, sent]);
    // Counted from the start of the box, the same place falls on other words.
    expect(where(sent, "Pubs")).toEqual({ start: 2, end: 6 });
    const counted = inTheBox(promptBox().value, [where(sent, "Pubs")]).map(({ start, end }) => promptBox().value.slice(start, end));
    expect(counted).toEqual(["afy "]);
  });

  test("test_no_word_of_the_box_is_drawn_beside_what_burro_took_of_it", async () => {
    // The words an offer rested on were cut from the box and drawn beside it. Nothing is
    // offered now, and what Burro took is a chip that holds the name the service gives
    // the thing: the words are in the box, and nowhere else on the page.
    const { container } = await added();

    expect(container.querySelectorAll("q")).toHaveLength(0);
    const page = container.textContent ?? "";
    for (const words of ["Pubs \u{1F37A}", "are so", "noisy"]) expect(page.includes(words)).toBe(false);
    expect(promptBox().value.includes("Pubs \u{1F37A} are so noisy")).toBe(true);
  });

  test("test_show_in_the_box_selects_the_words_that_were_not_read_where_they_stand_in_the_box", async () => {
    const { user } = await added();

    await user.click(screen.getByRole("button", { name: SUGGEST.showUnread }));

    expect(selected()).toBe("are so");
    expect(promptBox()).toHaveFocus();
    expect(isHeardOnce(NOTICE.partShown(1, 1))).toBe(true);
    expect(document.body.textContent?.includes(NOTICE.partNotFound)).toBe(false);
  });

  test("test_space_before_what_was_added_moves_every_place_along", async () => {
    const { user, api } = await openSearch();
    await addToTheBox(user, `${first}  `);
    await user.keyboard("{Enter}");
    await settled();
    api.on("interpret", noticed);
    await addToTheBox(user, `\n  ${more} `);
    await user.keyboard("{Enter}");
    await waitFor(() => expect(sentToBeRead(api)).toHaveLength(2));
    await settled();

    expect(sentToBeRead(api).at(-1)?.text).toBe(sent);
    await user.click(screen.getByRole("button", { name: SUGGEST.showUnread }));
    expect(selected()).toBe("are so");
  });
});

describe("words that rest on what was typed before them", () => {
  const first = "leafy and quiet, 35 minutes to work";

  test("test_they_are_read_by_themselves_and_the_page_says_that_they_were", async () => {
    // "by bike" says nothing by itself. The reader is the service's, and cannot tell what
    // the words before it were: it is sent what was added, and keeps nothing.
    const { user, api } = await openSearch();
    await search(user, first);
    const more = ", by bike";
    api.on(
      "interpret",
      reading("interpret-nothing-read", () => ({ unread: [where(more.trim(), "by bike")] })),
    );

    await user.type(promptBox(), more);
    await user.keyboard("{Enter}");
    await settled();

    expect(sentToBeRead(api).at(-1)?.text).toBe(more);
    // What the page says of words of which nothing was read, as it did before.
    expect(status()).toContain(NOTICE.nothingRead);
    // And that they were read without the words before them, which is why.
    expect(status()).toContain(ADDED.apart);
    expect(promptBox()).toHaveAccessibleDescription(ADDED.apart);
    await user.click(screen.getByRole("button", { name: SUGGEST.showUnread }));
    expect(selected()).toBe("by bike");

    // Nothing came of them, so they are still to be read. The words they rest on are put
    // before them, where they stand, and all of it is sent: the whole of a thing.
    answersASecond(api);
    const before = promptBox().value.indexOf("by bike");
    await user.type(promptBox(), "35 minutes to work ", { initialSelectionStart: before, initialSelectionEnd: before });
    // It goes when the box changes, as where the words stand does.
    expect(status()).not.toContain(ADDED.apart);
    await user.keyboard("{Enter}");
    await settled();

    expect(promptBox().value === `${first}, 35 minutes to work by bike`).toBe(true);
    expect(sentToBeRead(api).at(-1)?.text).toBe(", 35 minutes to work by bike");
    expect(screen.queryByRole("alert")).toBeNull();
    // Something came of them, so they are read, and are not sent again.
    await user.click(searchButton());
    expect(screen.getByRole("alert")).toHaveTextContent(ADDED.nothingNew);
    expect(sentToBeRead(api)).toHaveLength(3);
  });

  test("test_words_that_nothing_came_of_are_sent_again_as_they_are_changed_where_they_stand", async () => {
    // "Nothing in that could be read. Say it another way": said another way where it stands,
    // it is sent. Nothing of it was made part of the search, so nothing of it is read twice.
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-nothing-read"));
    await search(user, "leefy and quite");
    expect(status()).toContain(NOTICE.nothingRead);

    api.on("interpret", "interpret-first");
    await user.type(promptBox(), "a", { initialSelectionStart: 2, initialSelectionEnd: 3 });
    await user.keyboard("{Enter}");
    await settled();

    expect(sentToBeRead(api).map((body) => body.text)).toEqual(["leefy and quite", "leafy and quite"]);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(results().length).toBeGreaterThan(0);
  });

  test("test_it_is_not_said_of_a_first_sentence_nor_of_words_that_were_all_read", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-nothing-read"));
    await search(user, "by bike");
    expect(status()).toContain(NOTICE.nothingRead);
    expect(status()).not.toContain(ADDED.apart);

    // Nothing came of the first, so it is sent with what is added after it.
    answersASecond(api);
    await user.type(promptBox(), ", more green space");
    await user.keyboard("{Enter}");
    await settled();
    expect(sentToBeRead(api).at(-1)?.text).toBe("by bike, more green space");
    expect(status()).not.toContain(ADDED.apart);
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("what is kept of how far the search has read", () => {
  /** Every state the store of the page has been in, from the session that holds it. */
  function Watched({ seen }: { readonly seen: SearchState[] }) {
    const session = useSessionIfAny();
    useEffect(() => {
      const store = session?.search()?.store;
      if (store === undefined) return undefined;
      seen.push(store.getState());
      return store.subscribe(() => seen.push(store.getState()));
    }, [session, seen]);
    return null;
  }

  test("test_it_is_kept_as_counts_in_the_store_and_no_word_of_the_box_is_kept_anywhere", async () => {
    const watching = watch();
    const seen: SearchState[] = [];
    const api = firstSearch();
    const user = userEvent.setup({ delay: null });
    try {
      const { container } = render(
        <Shell meta={meta.meta}>
          <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} />
          <Watched seen={seen} />
        </Shell>,
      );
      await arrived();
      const first = `leafy and quiet near ${CANARY}`;
      const more = `, and a park by ${CANARY}`;

      // A sentence is read, a word of it is changed, more is added, Search is pressed with
      // nothing new, and words that could not be sent are tried again.
      await search(user, first);
      await user.type(promptBox(), "or", { initialSelectionStart: 6, initialSelectionEnd: 9 });
      await user.click(searchButton());
      api.on("interpret", "interpret-suggest");
      await user.type(promptBox(), more);
      await user.keyboard("{Enter}");
      await waitFor(() => expect(sentToBeRead(api)).toHaveLength(2));
      await settled();
      await user.click(searchButton());
      // The end of what the box holds is taken out, and the keys that undo put it back.
      const all = promptBox().value;
      await user.type(promptBox(), "{Backspace}", { initialSelectionStart: 6, initialSelectionEnd: all.length });
      promptBox().value = all;
      promptBox().setSelectionRange(6, all.length);
      fireEvent.input(promptBox(), { inputType: "historyUndo" });
      // All of it is copied, and pasted over itself.
      promptBox().setSelectionRange(0, all.length);
      await user.copy();
      await user.paste();
      expect(promptBox().value === all).toBe(true);
      await user.click(searchButton());
      expect(sentToBeRead(api)).toHaveLength(2);
      api.unreachable("interpret");
      await user.type(promptBox(), ` ${CANARY}`);
      await user.click(searchButton());
      await user.click(within(await screen.findByRole("alert")).getByRole("button", { name: PROMPT.tryAgain }));
      await waitFor(() => expect(sentToBeRead(api)).toHaveLength(4));
      await arrived();

      // What was typed left the page in the body of the call that reads it, as `text`.
      const holding = api.calls.filter((call) => JSON.stringify([call.url, call.sent, call.init.headers]).includes(CANARY));
      expect(new Set(holding.map((call) => `${call.method} ${call.path}`))).toEqual(new Set(["POST /v1/interpret"]));
      expect(sentToBeRead(api).map((body) => body.text)).toEqual([first, more, ` ${CANARY}`.trim(), ` ${CANARY}`.trim()]);
      for (const call of holding) {
        const body = call.body as Record<string, unknown>;
        expect(Object.keys(body).filter((key) => JSON.stringify(body[key]).includes(CANARY))).toEqual(["text"]);
        expect(call.url.includes(CANARY)).toBe(false);
      }
      // The store held counts of the box, in every state it was in, and no word of it.
      expect(seen.length).toBeGreaterThan(20);
      expect(JSON.stringify(seen).includes(CANARY)).toBe(false);
      const leaves = (value: unknown): unknown[] =>
        value !== null && typeof value === "object" ? Object.values(value).flatMap(leaves) : [value];
      const held = seen.flatMap((state) => leaves(state.box));
      expect(held.filter((leaf) => leaf !== null && typeof leaf !== "number" && typeof leaf !== "boolean")).toEqual([]);
      expect(new Set(seen.map((state) => state.box.read.to)).size).toBeGreaterThan(2);
      // What was kept while words were out of the box, to know them by when they came back, is counts too.
      expect(seen.some((state) => state.box.back.length > 0 && state.box.gone > 0)).toBe(true);
      expect(seen.some((state) => state.box.again.length > 0)).toBe(true);
      // Nor is it in an address, in storage, in the console, in an attribute or anywhere on
      // the page but in the box.
      expect(watching.everythingOutsideThePage().includes(CANARY)).toBe(false);
      expect(watching.storage).toEqual([]);
      expect(watching.console).toEqual([]);
      expect(watching.history).toEqual([]);
      const attributes = [...document.querySelectorAll("*")].flatMap((element) =>
        [...element.attributes].map((attribute) => attribute.value),
      );
      expect(attributes.length).toBeGreaterThan(300);
      expect(attributes.filter((value) => value.includes(CANARY))).toEqual([]);
      expect(promptBox().value.includes(CANARY)).toBe(true);
      expect(container.innerHTML.includes(CANARY)).toBe(false);
    } finally {
      watching.stop();
    }
  }, 60_000);
});

