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

import { screen, waitFor, within } from "@testing-library/react";

import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { CHIPS, NOTICE, PROMPT, RESULTS } from "@/content/search";
import { BUDGET, FEATURES, SETTINGS, SLIDER } from "@/content/settings";
import { recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { Operations } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { setOnline, standInApi } from "../support/api";
import { faultsIn } from "../support/axe";
import {
  arrived,
  everyChip,
  firstSearch,
  meta,
  openSearch,
  promptBox,
  removeChip,
  restOfTheList,
  results,
  search,
  settingsAt,
  settled,
  workingOf,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

/** The release a service moves to, after the page was built on the recorded one. */
const NEWER = "syn-2026-10-01-01";

const first = recordedAnswer("rank", "rank-first").body.data;
const second = recordedAnswer("interpret", "interpret-second-sentence").body.data;
/** The plain name of a feature, which is what a chip and a switch are named by. */
const labelOf = (featureId: string) =>
  meta.data.features.find((feature) => feature.feature_id === featureId)?.short_label ?? "";
const chips = () => within(screen.getByRole("region", { name: CHIPS.label }));
const skeletons = () => document.querySelectorAll(".skeleton").length;
const sources = (card: HTMLElement | undefined) =>
  card === undefined ? 0 : within(card).queryAllByRole("button", { name: /Source/ }).length;
/** What stands under the list: which results have reasons, and the release that ranked them. */
const footOfTheList = () => restOfTheList().parentElement?.querySelector("footer")?.textContent ?? "";
const editsSent = (body: unknown) => (body as { operations?: Operations }).operations;

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
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);
    await settingsAt(user, SETTINGS.money);
    const budget = () => screen.getAllByRole<HTMLInputElement>("textbox", { name: BUDGET.amount.rent })[0];

    await send(user, "leafy and quiet");
    await user.click(budget() as HTMLElement);
    await user.keyboard("18");
    // The words are read, and ranked, while the person is still typing the number.
    reading.release();
    await waitFor(() => expect(results()).toHaveLength(SHOWN_AT_FIRST));
    await arrived();

    // The reading named a budget of its own. It is not put in the field over the typing.
    expect(first.spec.budget.amount).toBe(1700);
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

    // The ranking stays, and each card says what it lacks.
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(within(results()[0] as HTMLElement).getByText(RESULTS.reasonsFailed)).toBeInTheDocument();
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(fault.body.error.message);
    expect(alert).toHaveTextContent(fault.headers["x-request-id"] ?? "no id");
    // The results were updated. It is their reasons that did not come.
    expect(alert).not.toHaveTextContent(NOTICE.notUpdated);

    api.on("explain_top", "explanations-first");
    await user.click(within(alert).getByRole("button", { name: PROMPT.tryAgain }));
    await settled();

    expect(screen.queryByRole("alert")).toBeNull();
    expect(results()[0]?.textContent?.includes(RESULTS.reasonsFailed)).toBe(false);
    // The reason and the trade-off of the answer, each with its source.
    expect(sources(results()[1])).toBeGreaterThanOrEqual(2);
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
    await user.click(screen.getByRole("button", { name: SETTINGS.title }));
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await waitFor(() => expect(results().length).toBeGreaterThan(0));
    await arrived();
    // Pubs and bars are a part of the recipe of Going out.
    await settingsAt(user, "Pace and food", FEATURES.madeOfName("Going out"));
    const pubs = labelOf("venue_evening");
    const number = screen.getAllByRole("textbox", { name: SLIDER.number(FEATURES.weight(pubs)) })[0] as HTMLElement;
    // No answer comes until all three have been done.
    api.calls.length = 0;
    const slow = api.hold("rank", "rank-nights-out");

    await user.clear(number);
    await user.type(number, "70{Enter}");
    await user.click(
      within(screen.getAllByRole("group", { name: FEATURES.direction(pubs) })[0] as HTMLElement).getByRole("radio", {
        name: "Lower is better",
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

/** The recorded profile of the area a path names, or `instead` where the path ends in `failing`. */
function recordedOr(path: string, failing: string, instead: ReturnType<typeof recordedError>) {
  const slug = path.split("/").pop() ?? "";
  return failing !== "" && slug === failing ? instead : recordedAnswer("get_area", `area/${slug}`);
}
