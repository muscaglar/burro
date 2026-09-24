/**
 * What the search page did when a person used it in a browser, against the
 * service, and no test had caught. Each test here is of one thing that was
 * seen, and would have caught it.
 *
 * jsdom lays nothing out, so where a thing stands on the page is held here
 * by the order it stands in: what comes directly under the box is what a
 * person sees when they press Search.
 */

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";

import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { MAP, MAP_CARD } from "@/content/map";
import {
  CHIPS,
  CLARIFY,
  COMPLETENESS,
  FAILURE,
  NOTICE,
  PLACE,
  PROMPT,
  RESULTS,
  SEARCH,
  STATUS,
  TENURE_CHOICE,
  UNMET,
  VIEWS,
} from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { SHARE } from "@/content/share";
import { recordedAnswer, responseFrom } from "@/lib/api/recorded";
import type { InterpretData, Operations } from "@/lib/api/schema";
import { NO_EDITS } from "@/lib/search/edits";

import { setOnline, type Responder } from "../support/api";
import { lastMap } from "../support/maplibre";
import {
  areas,
  arrived,
  CANARY,
  firstSearch,
  meta,
  openSearch,
  promptBox,
  results,
  search,
  setWebGL,
  settled,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const first = recordedAnswer("interpret", "interpret-first");
const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", scenario).request.body as { text: string }).text;
const status = () => screen.getAllByRole("status").map((line) => line.textContent ?? "");
const chipsRegion = () => screen.getByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel})$`) });

/** A reading as it was recorded, with some of what it holds changed, as the service answered in the browser. */
function reading(scenario: string, change: (data: InterpretData) => Partial<InterpretData>): Responder {
  const recorded = recordedAnswer("interpret", scenario);
  return () =>
    responseFrom({ ...recorded, body: { ...recorded.body, data: { ...recorded.body.data, ...change(recorded.body.data) } } });
}

/** True when `one` stands before `other` on the page, as it is read from the top. */
const comesBefore = (one: Element, other: Element) =>
  Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);

/** Where the words stand in the text, counted as the API counts. */
function where(text: string, words: string) {
  const start = Array.from(text.slice(0, text.indexOf(words))).length;
  return { start, end: start + Array.from(words).length };
}

beforeEach(() => setOnline(true));
afterEach(() => setWebGL(false));

describe("after Search is pressed", () => {
  test("test_what_burro_understood_stands_directly_under_the_box_and_before_everything_else", async () => {
    // Seen in a browser: after Search nothing on screen changed. On a phone what was
    // understood began a screen and a half down, under the examples, the tenure and the
    // place field, and the first result two and a half screens down.
    const { user } = await openSearch();
    await search(user);

    const line = screen.getAllByRole("status").find((one) => one.textContent?.includes("areas ranked"));
    const chips = chipsRegion();
    const tenure = screen.getAllByRole("group", { name: TENURE_CHOICE.legend })[0] as HTMLElement;
    const place = screen.getAllByRole("combobox", { name: PLACE.label })[0] as HTMLElement;
    const settings = screen.getByRole("button", { name: SETTINGS.title });

    expect(line).toBeDefined();
    expect(comesBefore(promptBox(), line as HTMLElement)).toBe(true);
    for (const lower of [tenure, place, settings]) {
      expect(comesBefore(line as HTMLElement, lower)).toBe(true);
      expect(comesBefore(chips, lower)).toBe(true);
    }
    // Nothing a person must act on stands between the box and what Burro says of the search.
    const between = [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main textarea")]
      .filter((control) => comesBefore(promptBox(), control) && comesBefore(control, line as HTMLElement))
      .map((control) => control.textContent || control.getAttribute("aria-label"));
    expect(between).toEqual([PROMPT.startAgain, PROMPT.submit]);
  });

  test("test_a_question_a_notice_and_a_failure_stand_directly_under_the_box_too", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");
    const tenure = () => screen.getAllByRole("group", { name: TENURE_CHOICE.legend })[0] as HTMLElement;

    expect(comesBefore(screen.getByRole("region", { name: CLARIFY.question }), tenure())).toBe(true);

    api.on("interpret", "interpret-notice");
    await user.clear(promptBox());
    await search(user, sentenceOf("interpret-notice"));
    expect(comesBefore(screen.getByRole("status", { name: NOTICE.label }), tenure())).toBe(true);

    api.on("rank", "error-internal");
    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));
    expect(comesBefore(await screen.findByRole("alert"), tenure())).toBe(true);
  });

  test("test_before_a_search_the_examples_come_first_and_the_page_is_as_it_was", async () => {
    await openSearch();

    const examples = screen.getByRole("heading", { name: PROMPT.examplesTitle });
    const starts = screen.getByRole("region", { name: CHIPS.startLabel });
    const tenure = screen.getAllByRole("group", { name: TENURE_CHOICE.legend })[0] as HTMLElement;

    expect(comesBefore(examples, tenure)).toBe(true);
    expect(comesBefore(tenure, starts)).toBe(true);
    expect(screen.queryByRole("button", { name: PROMPT.startAgain })).toBeNull();
  });

  test("test_there_is_a_way_from_what_was_understood_to_the_results", async () => {
    // Seen on a phone: the first result was 2,100 pixels down, and 6,425 with the settings open.
    const { user } = await openSearch();
    await search(user);

    const toResults = screen.getByRole("link", { name: RESULTS.goTo });
    expect(toResults).toHaveAttribute("href", "#results");
    expect(toResults).toHaveClass("target-min");
    expect(comesBefore(toResults, screen.getByRole("button", { name: SETTINGS.title }))).toBe(true);
    // On a narrow screen the results may be behind a tab, so the link brings them forward.
    await user.click(within(screen.getByRole("tablist", { name: VIEWS.label })).getByRole("tab", { name: VIEWS.table }));
    await user.click(toResults);
    expect(document.getElementById("results")).toHaveAttribute("data-narrow", "true");
  });
});

describe("a sentence of which only a part was read", () => {
  // What was typed in the browser. The reader made one edit of it, from the last sentence.
  const TYPED =
    "I rent and can pay up to £1,500 a month for a one bed flat. I work at Cindermoor Works and want to get there within 35 minutes. A park nearby would be good.";
  const UNREAD =
    "I rent and can pay up to £1,500 a month for a one bed flat. I work at Cindermoor Works and want to get there within 35 minutes.";
  const park: Operations = {
    ...NO_EDITS,
    weight_ops: [
      { action: "nudge", feature_id: "park_proximity", value: 0, step: "up_large", direction: "default", provenance: "stated" },
    ],
  };
  const partly = () =>
    firstSearch().on(
      "interpret",
      reading("interpret-unmet", () => ({
        operations: park,
        applied: [{ group: "weight_ops", index: 0, changed: true }],
        assumptions: [],
        unmet: ["other"],
        rests_on: [{ group: "weight_ops", index: 0, ...where(TYPED, "park nearby") }],
      })),
    );

  async function typedIt() {
    const opened = await openSearch(partly());
    fireEvent.input(promptBox(), { target: { value: TYPED } });
    await opened.user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    return opened;
  }

  test("test_that_a_part_was_not_read_is_said_beside_the_box_and_not_under_the_chips", async () => {
    // Seen in a browser: the budget and the workplace were not read, 21 areas were ranked
    // as if they had been, and the one sign was a grey line under the chips, off the screen.
    await typedIt();

    const said = screen.getByRole("status", { name: NOTICE.partLabel });
    expect(said).toHaveTextContent(NOTICE.partUnread);
    expect(NOTICE.partUnread).toMatch(/ranking/);
    expect(comesBefore(promptBox(), said)).toBe(true);
    expect(comesBefore(said, chipsRegion())).toBe(true);
    // It is said once: the line under the chips that said it is not drawn as well.
    expect(screen.queryByText(UNMET.other)).toBeNull();
    // It is not small print: it is drawn as the notice is, and not as a hint.
    expect(said.className).not.toMatch(/hint|muted/);
  });

  test("test_the_page_shows_which_part_by_selecting_it_in_the_box", async () => {
    const { user } = await typedIt();
    const show = screen.getByRole("button", { name: NOTICE.showPart });

    await user.click(show);

    expect(promptBox()).toHaveFocus();
    expect(promptBox().value.slice(promptBox().selectionStart, promptBox().selectionEnd)).toBe(UNREAD);
    expect(status()).toContain(NOTICE.partShown(1, 1));
  });

  test("test_with_two_parts_each_press_shows_the_next", async () => {
    const text = "Somewhere with llamas. A park nearby. And a nice vibe please!";
    const api = firstSearch().on(
      "interpret",
      reading("interpret-unmet", () => ({
        operations: park,
        applied: [{ group: "weight_ops", index: 0, changed: true }],
        assumptions: [],
        unmet: ["other"],
        rests_on: [{ group: "weight_ops", index: 0, ...where(text, "park nearby") }],
      })),
    );
    const { user } = await openSearch(api);
    fireEvent.input(promptBox(), { target: { value: text } });
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    const selected = () => promptBox().value.slice(promptBox().selectionStart, promptBox().selectionEnd);

    await user.click(screen.getByRole("button", { name: NOTICE.showPart }));
    expect(selected()).toBe("Somewhere with llamas.");
    expect(status()).toContain(NOTICE.partShown(1, 2));

    await user.click(screen.getByRole("button", { name: NOTICE.showNextPart }));
    expect(selected()).toBe("And a nice vibe please!");
    expect(status()).toContain(NOTICE.partShown(2, 2));

    await user.click(screen.getByRole("button", { name: NOTICE.showNextPart }));
    expect(selected()).toBe("Somewhere with llamas.");
  });

  test("test_once_the_box_is_changed_the_page_no_longer_offers_to_show_a_part_of_it", async () => {
    // Where the words stand is known for the text that was sent. Once the box holds
    // something else, the same offsets would select the wrong words.
    const { user } = await typedIt();
    expect(screen.getByRole("button", { name: NOTICE.showPart })).toBeInTheDocument();

    await user.type(promptBox(), " x");

    expect(screen.queryByRole("button", { name: NOTICE.showPart })).toBeNull();
    expect(screen.getByRole("status", { name: NOTICE.partLabel })).toHaveTextContent(NOTICE.partUnread);
  });

  test("test_trying_a_ranking_again_does_not_bring_the_offer_back_over_a_box_that_has_changed", async () => {
    // "Try again" sends the box again only where it was the words that failed. Where it was
    // the ranking, the box may hold anything by then, and the offsets are of what was sent.
    const { user, api } = await typedIt();
    await user.type(promptBox(), " and more");
    expect(screen.queryByRole("button", { name: NOTICE.showPart })).toBeNull();
    api.on("rank", "error-internal");
    await user.click(within(chipsRegion()).getAllByRole("button", { name: new RegExp(`^${CHIPS.remove}`) })[0] as HTMLElement);
    const alert = await screen.findByRole("alert");
    api.on("rank", "rank-first");

    await user.click(within(alert).getByRole("button", { name: PROMPT.tryAgain }));
    await settled();

    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: NOTICE.showPart })).toBeNull();
  });

  test("test_what_was_typed_is_written_nowhere_outside_the_box", async () => {
    const opened = await openSearch(partly());
    fireEvent.input(promptBox(), { target: { value: TYPED.replace("Cindermoor Works", CANARY) } });
    await opened.user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    await opened.user.click(screen.getByRole("button", { name: NOTICE.showPart }));

    const page = opened.container.cloneNode(true) as HTMLElement;
    page.querySelectorAll("textarea").forEach((box) => box.remove());
    expect(page.innerHTML.includes(CANARY)).toBe(false);
    expect(page.innerHTML.includes("one bed flat")).toBe(false);
  });

  test("test_a_sentence_read_in_full_says_nothing_of_a_part", async () => {
    const { user } = await openSearch();
    await search(user, sentenceOf("interpret-first"));

    expect(first.body.data.unmet).toEqual([]);
    expect(screen.queryByRole("status", { name: NOTICE.partLabel })).toBeNull();
    expect(screen.queryByRole("button", { name: NOTICE.showPart })).toBeNull();
  });
});

describe("a notice, when nothing else was read", () => {
  const onlyTheNotice = () =>
    firstSearch().on(
      "interpret",
      reading("interpret-notice", () => ({
        operations: NO_EDITS,
        applied: [],
        assumptions: [],
        rests_on: [],
        unmet: ["other"],
        spec: meta.data.defaults.rent,
      })),
    );

  test("test_the_page_does_not_leave_it_said_that_the_rest_was_applied_when_nothing_was", async () => {
    // Seen in a browser: "The rest of your search has been applied." over chips that read
    // "What a search starts from", with no result. The sentence is the API's, and is shown
    // as it came. The page says under it, in its own words, that nothing was changed.
    const { user, api } = await openSearch(onlyTheNotice());
    await user.type(promptBox(), "Somewhere leafy with lots of people like me");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    const notice = screen.getByRole("status", { name: NOTICE.label });
    expect(notice).toHaveTextContent(recordedAnswer("interpret", "interpret-notice").body.data.notice_text);
    expect(status()).toContain(NOTICE.nothingElse);
    expect(NOTICE.nothingElse).toMatch(/has not changed/);
    expect(comesBefore(notice, screen.getByText(NOTICE.nothingElse))).toBe(true);
    expect(api.callsTo("rank")).toEqual([]);
  });

  test("test_a_notice_with_the_rest_applied_says_nothing_more", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-notice"));
    await search(user, sentenceOf("interpret-notice"));

    expect(status()).not.toContain(NOTICE.nothingElse);
  });
});

describe("starting a new search", () => {
  test("test_once_a_search_is_open_start_again_is_beside_the_box_and_the_examples_are_gone", async () => {
    // Seen in a browser: a second example was added to the first search, and the only
    // "Start again" was inside the block that a failure draws.
    const { user } = await openSearch();
    expect(screen.getByRole("button", { name: /^Buying a terraced house/ })).toBeInTheDocument();

    await search(user);

    expect(screen.queryByRole("button", { name: /^Buying a terraced house/ })).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("button", { name: PROMPT.startAgain })).toBeInTheDocument();
    expect(promptBox()).toHaveAccessibleDescription(PROMPT.hintOpen);
  });

  test("test_start_again_goes_back_to_an_empty_box_the_defaults_and_the_examples", async () => {
    const { user, api } = await openSearch();
    await search(user);
    api.calls.length = 0;

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));

    expect(promptBox()).toHaveValue("");
    expect(promptBox()).toHaveFocus();
    expect(screen.getByRole("region", { name: CHIPS.startLabel })).toBeInTheDocument();
    expect(screen.getByText(RESULTS.waiting)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Buying a terraced house/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: PROMPT.startAgain })).toBeNull();
    expect(api.calls).toEqual([]);
  });

  test("test_a_budget_that_goes_when_the_tenure_changes_is_said_to_have_gone", async () => {
    // Seen in a browser: a budget of £1,700 a month vanished without a word when the next
    // sentence said "Buying". A rent is not a price, so the API takes it off (contract 5.3).
    const buyer = recordedAnswer("interpret", "interpret-buyer-family").body.data;
    const { user, api } = await openSearch();
    await search(user, sentenceOf("interpret-first"));
    expect(first.body.data.spec.budget.amount).toBe(1700);
    api
      .on("interpret", reading("interpret-buyer-family", () => ({ spec: { ...buyer.spec, budget: { ...buyer.spec.budget, amount: null } } })))
      .on("rank", "rank-buyer-family")
      .on("explain_top", "explanations-buyer-family");

    await user.clear(promptBox());
    await search(user, "Buying a terraced house");

    expect(status().join(" ")).toContain(STATUS.budgetWent);
    expect(STATUS.budgetWent).toMatch(/budget/i);
  });

  test("test_a_budget_that_stays_is_not_said_to_have_gone", async () => {
    const { user, api } = await openSearch();
    await search(user, sentenceOf("interpret-first"));
    api.on("interpret", "interpret-second-sentence").on("rank", "rank-second-sentence");

    await search(user, " and more green space");

    expect(status().join(" ")).not.toContain(STATUS.budgetWent);
  });
});

describe("when Burro cannot be reached", () => {
  test("test_a_sentence_is_answered_as_a_control_is_and_the_words_are_not_blamed", async () => {
    // Seen in a browser, with the API stopped: "Your words could not be read just now. The
    // settings below do the same job." The settings could not reach it either.
    const api = firstSearch().unreachable("interpret");
    const { user } = await openSearch(api);

    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent(FAILURE.network);
    expect(status()).not.toContain(NOTICE.degraded);
    expect(document.body.textContent?.includes(NOTICE.degraded)).toBe(false);
    expect(screen.getByRole("button", { name: SETTINGS.title })).toHaveAttribute("aria-expanded", "false");
    expect(promptBox()).toHaveValue("leafy and quiet");

    // "Try again" sends the same words from the box, once Burro can be reached.
    api.on("interpret", "interpret-first");
    await user.click(within(alert).getByRole("button", { name: PROMPT.tryAgain }));
    await settled();
    expect(api.callsTo("interpret").map((call) => (call.body as { text: string }).text)).toEqual([
      "leafy and quiet",
      "leafy and quiet",
    ]);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(results()).toHaveLength(20);
  });

  test("test_that_words_could_not_be_read_always_has_a_way_to_try_them_again_beside_it", async () => {
    // Seen in a browser: the line stayed on screen after a control had been used, with its
    // "Try again" gone.
    const api = firstSearch().on("interpret", "error-internal");
    const { user } = await openSearch(api);
    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(NOTICE.degraded));
    const line = () => screen.getByText(NOTICE.degraded).closest("div")?.parentElement as HTMLElement;
    expect(within(line()).getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();

    // A control is used: the person has done something about it, and the line goes.
    await user.click(screen.getByRole("switch", { name: "Leafy" }));
    await settled();

    expect(status()).not.toContain(NOTICE.degraded);
    expect(results()).toHaveLength(20);
  });
});

describe("what is marked as assumed", () => {
  test("test_a_tenure_the_person_typed_is_not_marked_assumed", async () => {
    // Seen in a browser: "Renting assumed" after "Renting a one bed for up to £1,500 a month".
    const { user } = await openSearch();
    await search(user, sentenceOf("interpret-first"));

    expect(sentenceOf("interpret-first")).toMatch(/^Renting/);
    const tenure = within(chipsRegion()).getAllByRole("listitem")[0] as HTMLElement;
    expect(tenure.textContent).toBe("Renting");
  });

  test("test_a_tenure_nobody_said_is_marked_assumed", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-notice"));
    await search(user, sentenceOf("interpret-notice"));

    expect(within(chipsRegion()).getAllByRole("listitem")[0]?.textContent).toBe(`Renting ${CHIPS.assumed}`);
  });

  test("test_a_place_added_from_the_field_is_marked_as_one_read_from_a_sentence_is", async () => {
    // Seen in a browser: picked from the field, "Public transport, within 45 minutes,
    // flexible". Read from a sentence, "Public transport assumed, ... flexible assumed".
    const place = recordedAnswer("search_places", "places-search").body.data.places[0];
    if (!place) throw new Error("the recording holds no place");
    const withThePlace: Responder = () => {
      const ranked = recordedAnswer("rank", "rank-first");
      const spec = {
        ...ranked.body.data.spec,
        commutes: [{ place_id: place.place_id, mode: "pt", max_minutes: 45, strictness: "soft", provenance: "ui_edit" }],
      };
      return responseFrom({ ...ranked, body: { ...ranked.body, data: { ...ranked.body.data, spec } } });
    };
    const { user } = await openSearch(firstSearch().on("rank", withThePlace));

    await user.type(screen.getAllByRole("combobox", { name: PLACE.label })[0] as HTMLElement, "cin");
    await user.click(await screen.findByRole("option", { name: new RegExp(`^${place.name}`) }));
    await settled();

    const chip = within(chipsRegion()).getByRole("button", { name: new RegExp(`^${place.name}`) });
    expect(chip.textContent).toBe(
      `${place.name}, Public transport ${CHIPS.assumed}, within 45 minutes ${CHIPS.assumed}, flexible ${CHIPS.assumed}`,
    );
  });
});

describe("where the focus is left", () => {
  test("test_answering_a_question_leaves_the_focus_on_what_burro_understood", async () => {
    // Seen in a browser: the question goes when it is answered, and the focus went with it.
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");
    api.on("rank", "rank-nights-out").on("explain_top", "explanations-nights-out");

    await user.click(screen.getByRole("button", { name: /^Pellam Exchange/ }));

    expect(document.activeElement).not.toBe(document.body);
    expect(chipsRegion()).toHaveFocus();
    await settled();
    expect(chipsRegion()).toHaveFocus();
  });

  test("test_leaving_a_question_out_leaves_the_focus_on_what_burro_understood", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");

    await user.click(screen.getByRole("button", { name: CLARIFY.leaveOut }));

    expect(chipsRegion()).toHaveFocus();
  });

  test("test_show_in_the_list_opens_the_list_at_the_top_of_the_card", async () => {
    // Seen on a phone: the list opened at the middle of the card, 1,056 pixels past its
    // heading. A card is taller than the screen, and was brought to the nearest edge.
    setWebGL(true);
    const scrolled: [Element, unknown][] = [];
    const before = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function (this: Element, how?: unknown) {
      scrolled.push([this, how]);
    };
    try {
      const { user } = await openSearch();
      await search(user);
      act(() => lastMap().fire("load"));
      await arrived();
      fireEvent.click(screen.getByRole("button", { name: /^Rank 4,/ }));
      scrolled.length = 0;

      await user.click(screen.getByRole("button", { name: MAP_CARD.showInList }));

      const card = results()[3] as HTMLElement;
      expect(card).toHaveFocus();
      const [where_, how] = scrolled.at(-1) ?? [];
      expect(where_).toBe(card);
      expect(how).toMatchObject({ block: "start" });
    } finally {
      Element.prototype.scrollIntoView = before;
    }
  });
});

describe("reaching the map", () => {
  test("test_there_is_a_link_that_skips_to_the_map", async () => {
    // Seen in a browser: by keyboard the map was 122 presses of Tab after the box.
    const { user } = await openSearch();
    await search(user);

    const toMap = screen.getByRole("link", { name: SEARCH.skipToMap });
    const target = document.getElementById((toMap.getAttribute("href") ?? "").slice(1));
    expect(toMap).toHaveClass("target");
    expect(target).toBe(screen.getByRole("tabpanel", { name: MAP.label }));
    expect(target?.tabIndex).toBe(-1);
    // It stands beside the link that skips to the results, before the box.
    expect(comesBefore(toMap, promptBox())).toBe(true);
    // On a narrow screen the map is behind a tab, so the link brings it forward.
    await user.click(toMap);
    expect(target).toHaveAttribute("data-narrow", "true");
  });
});

describe("how far a fit is to be trusted, wherever it is given", () => {
  test("test_the_table_says_when_a_fit_rests_on_part_of_what_counts", async () => {
    const { user } = await openSearch();
    await search(user);

    const table = screen.getByRole("tabpanel", { name: VIEWS.table, hidden: true });
    const row = within(table)
      .getAllByRole("row", { hidden: true })
      .find((one) => one.textContent?.includes("Otterby Fields")) as HTMLElement;
    expect(row.textContent?.includes(COMPLETENESS.some(5, 10))).toBe(true);
  });

  test("test_the_line_says_how_many_areas_went_when_fewer_are_ranked", async () => {
    // Seen in a browser: "21 areas changed place" when a list of 20 became a list of 15.
    const { user, api } = await openSearch();
    await search(user);
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));
    await settled();

    const said = status().join(" ");
    expect(said).toContain(STATUS.rankedNow(11, -11));
    expect(said).not.toMatch(/2[0-9] areas changed place/);
  });
});

describe("a link that was made", () => {
  test("test_the_link_is_still_there_when_the_person_comes_back_from_another_page", async () => {
    // Seen in a browser: the link was gone after the page of an area was read and left.
    const api = firstSearch().on("create_share", "share-made");
    const page = (
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} client={api.client} />
      </Shell>
    );
    const { user, rerender } = await openSearch(api);
    await search(user);
    await user.click(screen.getByRole("button", { name: SHARE.open }));
    await user.click(screen.getByRole("button", { name: SHARE.make }));
    const link = (await screen.findByRole<HTMLInputElement>("textbox", { name: SHARE.link })).value;

    // Another page, and back: the shell stays, as it does in a browser.
    rerender(
      <Shell meta={meta.meta}>
        <h1>The page of an area</h1>
      </Shell>,
    );
    rerender(page);
    await arrived();

    expect(screen.getByRole<HTMLInputElement>("textbox", { name: SHARE.link }).value).toBe(link);
    expect(api.callsTo("create_share")).toHaveLength(1);
  });
});

describe("what explains the page", () => {
  test("test_nothing_that_explains_the_page_is_kept_for_a_screen_reader_alone", async () => {
    // Seen in a browser: the line that says what 0 and 100 mean on a slider was 1 pixel by 1.
    // What is hidden from the eye is a name that the layout gives to one who sees it, or
    // something said aloud when it changes. It is never a sentence that explains.
    const { user } = await openSearch();
    await search(user);
    await user.click(screen.getByRole("button", { name: SETTINGS.title }));

    const hidden = [...document.querySelectorAll<HTMLElement>("main .visually-hidden")]
      .filter((one) => one.closest("[role='status'], [aria-live]") === null)
      .map((one) => (one.textContent ?? "").trim())
      .filter((text) => text.split(/\s+/).length > 4);

    expect(hidden).toEqual([]);
  });
});
