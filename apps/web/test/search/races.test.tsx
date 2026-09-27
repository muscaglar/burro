/**
 * What becomes of the search page when answers come in an order nobody
 * planned, or do not come: the form of a new release after the search it was
 * read beside, an answer while a number is half typed, "Stop" once the words
 * are read, reasons that fail, and a control moved twice before its answer.
 *
 * Each began as a review finding, reproduced on the whole page. None may
 * leave a card waiting for ever, send what nobody typed, or show one search
 * over the ranking of another.
 */

import { act, screen, waitFor, within } from "@testing-library/react";

import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { OPENS_AT_FIRST } from "@/components/SettingsPanel/look";
import { CARD } from "@/content/card";
import { DIRECTION } from "@/content/labels";
import { CHIPS, NOTICE, PROMPT, RESULTS, SOURCE } from "@/content/search";
import { BUDGET, FEATURES, JOURNEY, SETTINGS, SLIDER } from "@/content/settings";
import { recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { Operations } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { setOnline, standInApi } from "../support/api";
import { faultsIn } from "../support/axe";
import {
  areas,
  arrived,
  everyChip,
  firstSearch,
  groupsAre,
  meta,
  openSearch,
  promptBox,
  removeChip,
  restOfTheList,
  results,
  search,
  settingsAt,
  settled,
  theSettings,
  workingOf,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

/** The group of the settings that holds a family of vibes, by the name the service gives the family. */
const groupOf = (family: string) => meta.data.families.find((one) => one.family === family)?.label ?? "";

/** The release a service moves to, after the page was built on the recorded one. */
const NEWER = "syn-2026-10-01-01";

const first = recordedAnswer("rank", "rank-first").body.data;
/** What Burro wrote of the first results of the first search: of each of the five that are cards. */
const written = recordedAnswer("explain_top", "explanations-first").body.data.explanations;
const second = recordedAnswer("interpret", "interpret-second-sentence").body.data;
const nameOf = (areaId: string | undefined) => areas.find((area) => area.area_id === areaId)?.name ?? "";
/** The plain name of a feature, which is what a chip and a switch are named by. */
const labelOf = (featureId: string) =>
  meta.data.features.find((feature) => feature.feature_id === featureId)?.short_label ?? "";
const chips = () => within(screen.getByRole("region", { name: CHIPS.label }));
const skeletons = () => document.querySelectorAll(".skeleton").length;
const sources = (card: HTMLElement | undefined) =>
  card === undefined ? 0 : within(card).queryAllByRole("button", { name: /Source/ }).length;
/** The keys of the sources a result holds, each by what it says it is the source of. */
const keysIn = (result: HTMLElement) =>
  within(result)
    .queryAllByRole("button", { name: /^Source for / })
    .map((key) => key.getAttribute("aria-label") ?? "");
/** What a result says under one of its headings: the words of that part, after the heading. */
const saidUnder = (result: HTMLElement, heading: string) => {
  const head = within(result).getByRole("heading", { name: heading });
  return (head.parentElement?.textContent ?? "").slice((head.textContent ?? "").length);
};
/** What stands under the list: which results have reasons, and the release that ranked them. */
const footOfTheList = () => restOfTheList().parentElement?.querySelector("footer")?.textContent ?? "";
const editsSent = (body: unknown) => (body as { operations?: Operations }).operations;
/** The groups of the settings that stand open, by the name on the bar of each. */
const standOpen = () =>
  groupsAre()
    .filter(([, open]) => open)
    .map(([name]) => name);

async function send(user: Awaited<ReturnType<typeof openSearch>>["user"], text: string) {
  await user.clear(promptBox());
  await user.type(promptBox(), text);
  await user.click(screen.getByRole("button", { name: PROMPT.submit }));
}

beforeEach(() => setOnline(true));

describe("a first search on a page built on an older release", () => {
  test("test_the_cards_keep_their_reasons_and_profiles_when_the_form_of_the_new_release_comes_last", async () => {
    const api = firstSearch().movedTo(NEWER);
    const { user } = await openSearch(api);
    // From now on the form is slow to come. It is the largest thing the page asks for.
    const slow = api.hold("get_meta", "meta");

    await search(user);
    // The working of the first result holds its reasons and its profile.
    await workingOf(user, "Farrowmere");
    const before = { cards: results().length, sources: sources(results()[0]) };
    expect(before.cards).toBe(SHOWN_AT_FIRST);
    expect(before.sources).toBeGreaterThan(3);
    expect(slow.waiting()).toBe(1);

    slow.release();
    await arrived();
    await arrived();

    expect(skeletons()).toBe(0);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(sources(results()[0])).toBe(before.sources);
    expect(results()[0]?.textContent?.includes(RESULTS.reasonsFailed)).toBe(false);
    expect(screen.queryByRole("alert")).toBeNull();
    // Nothing was asked for twice.
    expect(api.callsTo("explain_top")).toHaveLength(1);
    expect(api.callsTo("get_area")).toHaveLength(5);
  });

  test("test_the_foot_of_the_list_names_the_release_that_made_the_ranking_and_not_the_one_the_page_was_built_on", async () => {
    // The form is read as the page opens, to hear who reads what is typed. It cannot be
    // read again after that, so the page keeps the release it was built on.
    const api = firstSearch().movedTo(NEWER).inTurn("get_meta", "meta", "error-internal");
    const { user } = await openSearch(api);

    await search(user);

    expect(meta.meta.release_id).not.toBe(NEWER);
    expect(footOfTheList().includes(NEWER)).toBe(true);
    expect(footOfTheList().includes(meta.meta.release_id)).toBe(false);
  });
});

describe("an answer that arrives while a number is being typed", () => {
  test("test_a_budget_typed_while_a_sentence_is_read_is_sent_as_it_was_typed", async () => {
    // While the first sentence of a search is read nothing is understood yet, and what
    // opens the settings is not drawn. So it is a sentence added to an open search that a
    // person may be in the settings for: they refine the search while its words are read.
    const api = firstSearch();
    const { user } = await openSearch(api);
    await search(user);
    api.on("rank", "rank-second-sentence").on("explain_top", "explanations-second-sentence");
    const reading = api.hold("interpret", "interpret-second-sentence");
    const budget = () => screen.getAllByRole<HTMLInputElement>("textbox", { name: BUDGET.amount.rent })[0];

    await send(user, "leafy and quiet, a bit more green space");
    await settingsAt(user, SETTINGS.money);
    await user.click(budget() as HTMLElement);
    await user.clear(budget() as HTMLElement);
    await user.keyboard("18");
    // The words are read, and ranked, while the person is still typing the number.
    reading.release();
    await waitFor(() => expect(api.callsTo("rank")).toHaveLength(2));
    await arrived();

    // The reading named a budget of its own. It is not put in the field over the typing.
    expect(second.spec.budget.amount).toBe(1700);
    expect(budget()?.value).toBe("18");
    await user.keyboard("00");
    expect(budget()?.value).toBe("1800");
    await user.tab();
    await settled();

    expect(editsSent(api.lastCallTo("rank").body)).toEqual(edits.budgetAmount(1800));
    const amounts = api.callsTo("rank").flatMap((call) => editsSent(call.body)?.budget_ops ?? []);
    expect(amounts.map((edit) => edit.amount)).toEqual([1800]);
  });
});

describe("an answer that arrives while a person is in a group of the settings", () => {
  test("test_a_group_that_a_person_types_in_is_not_closed_under_them_by_the_answer_to_a_sentence", async () => {
    // The sentence here asks for two places and the age of the buildings, and nothing of
    // what can be paid. A person who is typing a budget as its answer comes must find the
    // field where it was, with what they typed and the focus in it: whatever the look has
    // stand open of the settings, nothing closes under a person who is in a group.
    const api = firstSearch();
    const { user } = await openSearch(api);
    await search(user);
    api.on("rank", "rank-two-places").on("explain_top", "explanations-two-places");
    const reading = api.hold("interpret", "interpret-two-places");
    const asks = recordedAnswer("interpret", "interpret-two-places").body.data.spec;
    const asked = asks.tags.filter((tag) => tag.provenance !== "default");
    expect([asks.budget.amount, asks.commutes.length, asked.length]).toEqual([null, 2, 1]);
    const budget = () => screen.queryAllByRole<HTMLInputElement>("textbox", { name: BUDGET.amount.rent })[0];

    await send(user, "leafy and quiet, and near my two places of work");
    await settingsAt(user, SETTINGS.money);
    const stoodOpen = standOpen();
    expect(stoodOpen).toContain(SETTINGS.money);
    const field = budget() as HTMLInputElement;
    await user.click(field);
    await user.clear(field);
    await user.keyboard("18");
    reading.release();
    await waitFor(() => expect(api.callsTo("rank")).toHaveLength(2));
    await arrived();

    // The field is the field it was: it was not taken off the page and drawn again.
    expect(budget() === field).toBe(true);
    expect(field.value).toBe("18");
    expect(document.activeElement === field).toBe(true);
    // Nothing opened or closed under the person: the groups that stood open stand open.
    expect(standOpen()).toEqual(stoodOpen);
    await user.keyboard("00");
    await user.tab();
    await settled();

    expect(editsSent(api.lastCallTo("rank").body)).toEqual(edits.budgetAmount(1800));
  });

  test("test_what_a_person_opened_stays_open_when_an_answer_comes_while_they_are_elsewhere_and_a_look_of_none_opens_nothing_else", async () => {
    // A group a person opened stays open, and one they closed stays closed, until they
    // start again. Once a search is open the look opens none for them: a person has the
    // answer before them and came to change one thing.
    const api = firstSearch();
    const { user } = await openSearch(api);
    await search(user);
    await settingsAt(user, SETTINGS.money);
    api.on("rank", "rank-two-places").on("explain_top", "explanations-two-places");
    const reading = api.hold("interpret", "interpret-two-places");

    await send(user, "leafy and quiet, and near my two places of work");
    // The focus is on Search, which is none of the groups of the settings.
    expect(theSettings().contains(document.activeElement)).toBe(false);
    reading.release();
    await waitFor(() => expect(api.callsTo("rank")).toHaveLength(2));
    await arrived();

    expect(standOpen()).toContain(SETTINGS.money);
    if (OPENS_AT_FIRST === "none") expect(standOpen()).toEqual([SETTINGS.money]);
  });

  test("test_nothing_opens_or_closes_once_what_a_person_pressed_in_a_group_has_gone_from_the_page", async () => {
    // A journey is taken out of the search in the settings, and the button that took it out
    // goes with it. A browser does not say that what had the focus has gone: so whether a
    // person is in a group is asked of the page as the search changes, and kept nowhere.
    const api = firstSearch();
    const { user } = await openSearch(api);
    await search(user);
    await settingsAt(user, SETTINGS.journeys);
    const stoodOpen = standOpen();
    expect(stoodOpen).toContain(SETTINGS.journeys);
    api.on("rank", "rank-scale").on("explain_top", "explanations-scale");
    await user.click(within(theSettings()).getByRole("button", { name: JOURNEY.remove("Cindermoor Works") }));
    await settled();
    // It was the settings' own change, and nothing opened or closed for it.
    expect(standOpen()).toEqual(stoodOpen);

    api
      .on("interpret", "interpret-two-places")
      .on("rank", "rank-two-places")
      .on("explain_top", "explanations-two-places");
    await user.click(promptBox());
    await user.keyboard(", and near my two places of work{Enter}");
    await settled();

    // The group the person opened stands open still, with the two places in it.
    expect(standOpen()).toContain(SETTINGS.journeys);
    if (OPENS_AT_FIRST === "none") expect(standOpen()).toEqual([SETTINGS.journeys]);
  });
});

describe("stop, once the words are read", () => {
  async function stoppedWhileRanking() {
    const api = firstSearch();
    const view = await openSearch(api);
    await search(view.user);
    await everyChip(view.user);
    const before = {
      chips: chips().getAllByRole("listitem").map((chip) => chip.textContent),
      cards: results().map((card) => card.textContent),
    };
    api.on("interpret", "interpret-second-sentence").on("explain_top", "explanations-second-sentence");
    const ranking = api.late("rank", "rank-second-sentence", "rank-second-sentence");
    await send(view.user, "a bit more green space");
    await waitFor(() => expect(ranking.waiting()).toBe(1));
    return { ...view, api, before, ranking };
  }

  test("test_the_chips_already_show_the_new_sentence_while_its_ranking_is_worked_out", async () => {
    const { ranking } = await stoppedWhileRanking();

    // This is what Stop must undo: the chips say one search, and the list is of another.
    const added = second.spec.weights.find(
      (weight) => weight.weight > 0 && !first.spec.weights.some((one) => one.feature_id === weight.feature_id),
    );
    expect(added).toBeDefined();
    expect(chips().getByRole("button", { name: new RegExp(`^${labelOf(added?.feature_id ?? "")}`) })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: PROMPT.stop })).toBeInTheDocument();
    ranking.release();
    await settled();
  });

  test("test_stop_puts_the_chips_back_so_that_they_say_the_search_the_list_is_of", async () => {
    const { user, api, before, ranking } = await stoppedWhileRanking();

    await user.click(screen.getByRole("button", { name: PROMPT.stop }));
    // The ranking was already on its way, and comes after all.
    ranking.release();
    await settled();

    expect(chips().getAllByRole("listitem").map((chip) => chip.textContent)).toEqual(before.chips);
    expect(results().map((card) => card.textContent)).toEqual(before.cards);
    expect(skeletons()).toBe(0);
    expect(screen.queryByRole("alert")).toBeNull();
    // What was typed stays in its box, to be sent again or changed.
    expect(promptBox()).toHaveValue("a bit more green space");
    expect(api.unexpected).toEqual([]);
  });

  test("test_a_second_press_on_stop_lands_on_start_again_and_does_nothing", async () => {
    // Seen in a browser: Start again is drawn where Stop stood as soon as the reading has
    // ended, so the second press of a double press landed on it. The box was emptied and the
    // whole search was gone, with all that was set by hand.
    const { user, api, before, ranking } = await stoppedWhileRanking();

    await user.dblClick(screen.getByRole("button", { name: PROMPT.stop }));
    ranking.release();
    await settled();

    expect(screen.getByRole("button", { name: PROMPT.startAgain })).toBeInTheDocument();
    expect(promptBox()).toHaveValue("a bit more green space");
    expect(chips().getAllByRole("listitem").map((chip) => chip.textContent)).toEqual(before.chips);
    expect(results().map((card) => card.textContent)).toEqual(before.cards);
    expect(api.unexpected).toEqual([]);

    // A press of its own begins again, as it did: by pointer, and by keyboard.
    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    await settled();
    expect(promptBox()).toHaveValue("");
    expect(screen.queryAllByRole("article")).toEqual([]);
  });

  test("test_start_again_pressed_by_keyboard_begins_again_whatever_was_pressed_before", async () => {
    const { user, ranking } = await stoppedWhileRanking();
    await user.click(screen.getByRole("button", { name: PROMPT.stop }));
    ranking.release();
    await settled();

    screen.getByRole("button", { name: PROMPT.startAgain }).focus();
    await user.keyboard("{Enter}");
    await settled();

    expect(promptBox()).toHaveValue("");
    expect(screen.queryAllByRole("article")).toEqual([]);
  });

  test("test_a_control_used_after_stop_is_sent_with_the_spec_of_the_ranking_on_screen", async () => {
    const { user, api, ranking } = await stoppedWhileRanking();
    await user.click(screen.getByRole("button", { name: PROMPT.stop }));
    ranking.release();
    await settled();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await removeChip(user, "Leafy");
    await settled();

    expect(api.lastCallTo("rank").body).toEqual({ spec: first.spec, operations: edits.tagOff("leafy"), limit: 20 });
  });
});

describe("reasons and profiles that could not be loaded", () => {
  test("test_a_failure_of_the_reasons_is_said_in_the_apis_words_with_the_id_to_quote_and_can_be_tried_again", async () => {
    const api = firstSearch().on("explain_top", "error-internal");
    const { user } = await openSearch(api);
    const fault = recordedError("error-internal");

    await search(user);

    // The ranking stays, and each card says what it lacks: on the card the trade-off, and
    // in its working the reasons.
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    const cards = results().slice(0, written.length);
    expect(cards.map((card) => saidUnder(card, RESULTS.tradeOffTitle))).toEqual(cards.map(() => CARD.tradeOffFailed));
    const second = await workingOf(user, nameOf(first.ranked[1]?.area_id));
    expect(second === cards[1]).toBe(true);
    expect(saidUnder(second, RESULTS.reasonsTitle)).toBe(RESULTS.reasonsFailed);
    // What did not come has no source to give. What the working holds of the area itself has.
    const given = written[1]?.reasons ?? [];
    const ofWhatBurroWrote = [
      ...given.map((_, at) => SOURCE.buttonFor(RESULTS.sourceOfReason(at + 1, nameOf(written[1]?.area_id)))),
      SOURCE.buttonFor(RESULTS.sourceOfTradeOff(nameOf(written[1]?.area_id))),
    ];
    expect(ofWhatBurroWrote.length).toBeGreaterThanOrEqual(2);
    expect(keysIn(second).filter((key) => ofWhatBurroWrote.includes(key))).toEqual([]);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(fault.body.error.message);
    expect(alert).toHaveTextContent(fault.headers["x-request-id"] ?? "no id");
    // The results were updated. It is their reasons that did not come.
    expect(alert).not.toHaveTextContent(NOTICE.notUpdated);

    api.on("explain_top", "explanations-first");
    await user.click(within(alert).getByRole("button", { name: PROMPT.tryAgain }));
    await settled();

    expect(screen.queryByRole("alert")).toBeNull();
    expect(results().some((one) => one.textContent?.includes(CARD.tradeOffFailed))).toBe(false);
    expect(results().some((one) => one.textContent?.includes(RESULTS.reasonsFailed))).toBe(false);
    // Each card says the trade-off of the answer, in the API's words.
    expect(cards.map((card) => saidUnder(card, RESULTS.tradeOffTitle))).toEqual(
      written.map((one) => one.trade_off?.text ?? RESULTS.noTradeOff),
    );
    // The working that stood open holds what came: every reason with its source, and the
    // source of the trade-off.
    expect(given.filter((reason) => !second.textContent?.includes(reason.text))).toEqual([]);
    expect(ofWhatBurroWrote.filter((key) => !keysIn(second).includes(key))).toEqual([]);
  });

  test("test_a_failure_of_a_profile_is_said_and_trying_again_asks_for_that_profile", async () => {
    const api = firstSearch().on("get_area", (call) =>
      recordedOr(call.path, "farrowmere", recordedError("error-internal")),
    );
    const { user } = await openSearch(api);
    const fault = recordedError("error-internal");

    await search(user);

    // What a profile holds is in the working of a result, and the working says what it lacks.
    const card = await workingOf(user, "Farrowmere");
    expect(card.textContent?.includes(RESULTS.detailsFailed)).toBe(true);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(fault.body.error.message);
    expect(alert).toHaveTextContent(fault.headers["x-request-id"] ?? "no id");

    api.calls.length = 0;
    api.on("get_area", (call) => recordedOr(call.path, "", fault));
    await user.click(within(alert).getByRole("button", { name: PROMPT.tryAgain }));
    await settled();

    expect(api.callsTo("get_area").map((call) => call.path)).toEqual(["/v1/areas/farrowmere"]);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(results().some((one) => one.textContent?.includes(RESULTS.detailsFailed))).toBe(false);
  });

  test("test_the_page_with_reasons_that_failed_has_no_accessibility_fault", async () => {
    const { user, container } = await openSearch(firstSearch().on("explain_top", "error-internal"));
    await search(user);
    await screen.findByRole("alert");

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("a control moved twice before its answer", () => {
  test("test_a_weight_put_back_and_a_direction_chosen_meanwhile_leave_the_api_what_the_person_last_set", async () => {
    const api = standInApi()
      .on("interpret", "interpret-first")
      .on("rank", "rank-nights-out")
      .on("explain_top", "explanations-first")
      .on("search_places", "places-search");
    const { user } = await openSearch(api);
    // Before a search the settings stand open in the second way in.
    await settingsAt(user);
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await waitFor(() => expect(results().length).toBeGreaterThan(0));
    await arrived();
    // Pubs and bars are a part of the recipe of Going out.
    await settingsAt(user, groupOf("pace_food"), FEATURES.madeOfName("Going out"));
    const pubs = labelOf("venue_evening_per_homes");
    const number = screen.getAllByRole("textbox", { name: SLIDER.number(FEATURES.weight(pubs)) })[0] as HTMLElement;
    // No answer comes until all three have been done.
    api.calls.length = 0;
    const slow = api.hold("rank", "rank-nights-out");

    await user.clear(number);
    await user.type(number, "70{Enter}");
    await user.click(
      within(screen.getAllByRole("group", { name: FEATURES.direction(pubs) })[0] as HTMLElement).getByRole("radio", {
        name: DIRECTION.less,
      }),
    );
    await user.clear(number);
    await user.type(number, "50{Enter}");
    slow.release();
    await arrived();

    // Each edit is sent with those still waiting. As the API applies them, the last wins.
    const sent = editsSent(api.lastCallTo("rank").body)?.weight_ops ?? [];
    expect(sent.map(({ action, value, direction }) => ({ action, value, direction }))).toEqual([
      { action: "set", value: 0.7, direction: "default" },
      { action: "set", value: 0.7, direction: "less" },
      { action: "set", value: 0.5, direction: "default" },
    ]);
  });
});

describe("a space requirement that is changed while no answer can come", () => {
  const AIR = labelOf("air_no2");
  const NOISE = labelOf("noise_exposure");
  const thing = (name: string) => within(theSettings()).getByRole("group", { name });
  const more = (name: string) => within(thing(name)).getByRole("button", { name: SLIDER.more(FEATURES.weight(name)) });
  const counts = (name: string) =>
    within(thing(name)).getByRole<HTMLInputElement>("slider", { name: FEATURES.weight(name) }).value;
  /** What the space requirements say at once to whoever hears the page: each line under a control. */
  const saidAmongThem = () => within(theSettings()).queryAllByRole("alert").map((line) => line.textContent);
  /** A slider sends what it was set to a moment after it was last moved: so what comes of a press is waited for. */
  const said = async (lines: readonly string[]) => {
    await waitFor(() => expect(saidAmongThem()).toEqual(lines));
    await settled();
    expect(saidAmongThem()).toEqual(lines);
  };

  test("test_the_control_says_where_it_stands_that_its_change_is_not_in_the_results", async () => {
    // Seen in a browser: "More: Village feel" drew 10 and then 20, and each ranking failed.
    // What said so stood in the box at the head of the page, 667 px over a window of 900
    // and 1,303 px over a window of 844, and nothing in sight said the change was not made.
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.airAndNoise);
    expect(saidAmongThem()).toEqual([]);
    const before = Number(counts(AIR));
    api.unreachable("rank");

    await user.click(more(AIR));
    await said([NOTICE.unsent]);

    // What failed is said once, at the head of the page, with the buttons.
    const failed = screen.getAllByRole("alert").filter((line) => !theSettings().contains(line));
    expect(failed).toHaveLength(1);
    expect(failed[0]).toHaveTextContent(NOTICE.notUpdated);
    expect(within(failed[0] as HTMLElement).getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();
    // The control shows what it was set to, and says that the results do not show it.
    expect(Number(counts(AIR))).toBeGreaterThan(before);
    expect(within(thing(AIR)).getByRole("alert")).toHaveTextContent(NOTICE.unsent);
    expect(NOTICE.unsent).toContain(`"${PROMPT.tryAgain}"`);

    // A second change waits with the first, and each says so where it stands.
    await user.click(more(NOISE));
    await said([NOTICE.unsent, NOTICE.unsent]);
    expect(within(thing(NOISE)).getByRole("alert")).toHaveTextContent(NOTICE.unsent);

    // The next change that is answered carries both, and nothing is left to say.
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await user.click(more(NOISE));
    await said([]);
    expect(editsSent(api.lastCallTo("rank").body)?.weight_ops.map((one) => one.feature_id)).toEqual([
      "air_no2",
      "noise_exposure",
      "noise_exposure",
    ]);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("test_the_line_stays_while_the_change_is_tried_again_and_goes_with_the_answer", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.airAndNoise);
    api.unreachable("rank");
    await user.click(more(AIR));
    await said([NOTICE.unsent]);

    // Tried again, and the answer is slow: until it comes the change is still not in the results.
    const slow = api.hold("rank", "rank-refined");
    api.on("explain_top", "explanations-refined");
    await user.click(screen.getByRole("button", { name: PROMPT.tryAgain }));
    await waitFor(() => expect(slow.waiting()).toBe(1));
    expect(saidAmongThem()).toEqual([NOTICE.unsent]);

    slow.release();
    await said([]);
  });

  test("test_with_no_connection_the_control_says_that_its_change_goes_when_the_connection_is_back", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.airAndNoise);
    api.calls.length = 0;
    setOnline(false);
    act(() => void window.dispatchEvent(new Event("offline")));

    await user.click(more(AIR));
    await said([NOTICE.unsentOffline]);
    expect(api.calls).toEqual([]);

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    setOnline(true);
    act(() => void window.dispatchEvent(new Event("online")));
    await said([]);

    expect(api.callsTo("rank")).toHaveLength(1);
  });

  test("test_a_change_that_is_on_its_way_for_the_first_time_is_not_said_to_have_failed", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.airAndNoise);
    const slow = api.hold("rank", "rank-refined");
    api.on("explain_top", "explanations-refined");

    await user.click(more(AIR));
    await waitFor(() => expect(slow.waiting()).toBe(1));

    expect(saidAmongThem()).toEqual([]);
    slow.release();
    await said([]);
  });

  test("test_the_page_with_a_change_that_waits_has_no_accessibility_fault", async () => {
    const { user, api, container } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.airAndNoise);
    api.unreachable("rank");
    await user.click(more(AIR));
    await said([NOTICE.unsent]);

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

/** The recorded profile of the area a path names, or `instead` where the path ends in `failing`. */
function recordedOr(path: string, failing: string, instead: ReturnType<typeof recordedError>) {
  const slug = path.split("/").pop() ?? "";
  return failing !== "" && slug === failing ? instead : recordedAnswer("get_area", `area/${slug}`);
}
