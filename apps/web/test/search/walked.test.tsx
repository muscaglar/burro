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
import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { COMPARE, TRAY } from "@/content/compare";
import { MAP, MAP_CARD, TABLE } from "@/content/map";
import {
  CHIPS,
  CLARIFY,
  COMPLETENESS,
  FAILURE,
  FILTERED,
  NOTICE,
  PLACE,
  PROMPT,
  RESULTS,
  SEARCH,
  SHELF,
  STATUS,
  SUGGEST,
  TENURE_CHOICE,
  UNMET,
  FIND_AREA,
} from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { SHARE } from "@/content/share";
import { recordedAnswer, responseFrom } from "@/lib/api/recorded";
import type { InterpretData, Operations } from "@/lib/api/schema";
import { NO_EDITS } from "@/lib/search/edits";

import { reasonsFor, setOnline, withTheSpecSent, type Responder } from "../support/api";
import { lastMap } from "../support/maplibre";
import {
  areas,
  arrived,
  bands,
  CANARY,
  everyChip,
  firstSearch,
  meta,
  openSearch,
  promptBox,
  removeChip,
  results,
  search,
  settingsAt,
  setWebGL,
  settled,
  theTable,
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
    const settings = screen.getByRole("button", { name: SETTINGS.title });

    expect(line).toBeDefined();
    expect(comesBefore(promptBox(), line as HTMLElement)).toBe(true);
    expect(comesBefore(line as HTMLElement, settings)).toBe(true);
    expect(comesBefore(chips, settings)).toBe(true);
    // Renting or buying and the place field are in the settings now, so that the answer comes first.
    expect(screen.queryByRole("group", { name: TENURE_CHOICE.legend })).toBeNull();
    expect(screen.queryByRole("combobox", { name: PLACE.label })).toBeNull();
    expect(screen.queryByRole("combobox", { name: FIND_AREA.label })).toBeNull();
    // Nothing a person must act on stands between the box and what Burro says of the search.
    const between = [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main textarea")]
      .filter((control) => comesBefore(promptBox(), control) && comesBefore(control, line as HTMLElement))
      .map((control) => control.textContent || control.getAttribute("aria-label"));
    expect(between).toEqual([PROMPT.startAgain, PROMPT.submit]);
  });

  test("test_a_question_a_notice_and_a_failure_stand_directly_under_the_box_too", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");
    /** What comes after everything Burro says: the way to the settings. */
    const after = () => screen.getByRole("button", { name: SETTINGS.title });

    expect(comesBefore(screen.getByRole("region", { name: CLARIFY.question }), after())).toBe(true);

    api.on("interpret", "interpret-notice");
    await user.clear(promptBox());
    await search(user, sentenceOf("interpret-notice"));
    expect(comesBefore(screen.getByRole("status", { name: NOTICE.label }), after())).toBe(true);

    api.on("rank", "error-internal");
    await removeChip(user, "Leafy");
    expect(comesBefore(await screen.findByRole("alert"), after())).toBe(true);
  });

  test("test_before_a_search_no_link_leads_to_results_that_are_not_there", async () => {
    // Found by reading the page as it was built: "Skip to results" led to nothing.
    const { user } = await openSearch();
    const leadingNowhere = () =>
      [...document.querySelectorAll<HTMLAnchorElement>("a[href^='#']")]
        .map((link) => link.getAttribute("href") ?? "")
        .filter((href) => href.length > 1 && document.getElementById(href.slice(1)) === null);

    expect(screen.queryByRole("link", { name: SEARCH.skipToResults })).toBeNull();
    expect(leadingNowhere()).toEqual([]);

    await search(user);

    expect(screen.getByRole("link", { name: SEARCH.skipToResults })).toHaveAttribute("href", "#results");
    expect(leadingNowhere()).toEqual([]);
  });

  test("test_before_a_search_the_shelf_comes_first_and_nothing_is_said_of_a_search", async () => {
    await openSearch();

    const shelf = screen.getByRole("region", { name: SHELF.title });
    const tenure = screen.getByRole("group", { name: TENURE_CHOICE.legend });
    const examples = screen.getByRole("heading", { name: PROMPT.examplesTitle });

    expect(comesBefore(promptBox(), shelf)).toBe(true);
    expect(comesBefore(shelf, tenure)).toBe(true);
    expect(comesBefore(tenure, examples)).toBe(true);
    expect(comesBefore(examples, screen.getByRole("button", { name: SETTINGS.title }))).toBe(true);
    // Nothing is understood of anything yet, so there are no chips, no list and nothing to start again.
    expect(screen.queryByRole("region", { name: CHIPS.startLabel })).toBeNull();
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    expect(screen.queryByRole("button", { name: PROMPT.startAgain })).toBeNull();
  });

  test("test_the_results_come_directly_after_what_was_understood_and_the_ways_to_change_it", async () => {
    // Seen on a phone: the first result was 2,100 pixels down, and 6,425 with the settings open.
    // Now every group of the settings is closed at first, and nothing else stands in between.
    const { user } = await openSearch();
    await search(user);
    const list = screen.getByRole("list", { name: RESULTS.listLabel });
    const toResults = screen.getByRole("link", { name: SEARCH.skipToResults });

    expect(toResults).toHaveAttribute("href", "#results");
    expect(document.getElementById("results")?.contains(list)).toBe(true);
    const between = [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main a[href]")]
      .filter((control) => comesBefore(chipsRegion(), control) && comesBefore(control, list))
      .filter((control) => !chipsRegion().contains(control))
      .map((control) => control.textContent || control.getAttribute("aria-label"));
    // Nothing: the ways to the settings and to sharing, and the map, stand after the first result.
    expect(between).toEqual([]);
    const [one, two] = results();
    for (const name of [SETTINGS.title, SHARE.open]) {
      const way = screen.getByRole("button", { name });
      expect(comesBefore(one as HTMLElement, way)).toBe(true);
      expect(comesBefore(way, two as HTMLElement)).toBe(true);
      expect(comesBefore(way, screen.getByRole("region", { name: MAP.label }))).toBe(true);
    }
  });
});

describe("the answer comes first", () => {
  test("test_the_first_result_stands_before_the_map_and_the_rest_of_them_after_it", async () => {
    // Seen on a phone: after a search the first screen was the banner, the header, the title,
    // the box, a line, the chips, two buttons, a strip of map and two more buttons. The first
    // result began at 750 px and ended at 1,110, on a screen of 844.
    const { user } = await openSearch();
    await search(user);
    const [one, two] = results();
    const map = screen.getByRole("region", { name: MAP.label });

    expect(comesBefore(chipsRegion(), one as HTMLElement)).toBe(true);
    expect(comesBefore(one as HTMLElement, map)).toBe(true);
    expect(comesBefore(map, two as HTMLElement)).toBe(true);
    // They are one list to whoever reads the page: the first, and then the rest from the second.
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(screen.getByRole("list", { name: RESULTS.listLabel }).tagName).toBe("OL");
    expect(screen.getByRole("list", { name: RESULTS.restLabel })).toHaveAttribute("start", "2");
  });

  test("test_before_a_search_the_map_stands_where_it_did_and_is_the_same_map_after_one", async () => {
    // The map is not drawn a second time when the results come: it is moved by nothing.
    const { user } = await openSearch();
    const before = screen.getByRole("region", { name: MAP.label });

    await search(user);

    expect(screen.getByRole("region", { name: MAP.label })).toBe(before);
  });

  test("test_once_a_search_is_open_the_title_takes_no_room_and_is_still_the_heading_of_the_page", async () => {
    const { user } = await openSearch();
    const title = () => screen.getByRole("heading", { level: 1 });
    expect(title()).toHaveTextContent(SEARCH.title);
    expect(title().classList.contains("visually-hidden")).toBe(false);

    await search(user);

    expect(title()).toHaveTextContent(SEARCH.title);
    expect(title().classList.contains("visually-hidden")).toBe(true);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  test("test_the_heading_of_the_results_is_kept_for_a_screen_reader_and_takes_no_room", async () => {
    // A numbered list of areas directly under "21 areas ranked" says what it is.
    const { user } = await openSearch();
    await search(user);

    const heading = screen.getByRole("heading", { level: 2, name: RESULTS.title });
    expect(heading.classList.contains("visually-hidden")).toBe(true);
    expect(screen.getByRole("region", { name: RESULTS.title })).toBe(document.getElementById("results"));
  });

  test("test_what_happened_is_one_short_line_and_the_first_result_is_named_by_its_card", async () => {
    // Seen on a phone: "22 areas ranked. First: Otterby Fields. Settings you did not choose
    // now count for less." took two lines above the chips, and named the card under it.
    const { user } = await openSearch();
    await search(user);
    const line = screen.getAllByRole("status").find((one) => one.textContent?.includes("areas ranked")) as HTMLElement;
    const name = within(results()[0] as HTMLElement).getByRole("heading", { level: 3 }).textContent ?? "";
    const seen = [...line.childNodes]
      .filter((part) => !(part instanceof HTMLElement && part.classList.contains("visually-hidden")))
      .map((part) => part.textContent ?? "")
      .join("")
      .replace(/\s+/g, " ")
      .trim();

    // Said whole to a screen reader, which is told when it changes.
    // The search names a workplace and a budget, and leafy and quiet count for more than either.
    expect(line.textContent?.replace(/\s+/g, " ").trim()).toBe(`${STATUS.ranked(21, name)} ${STATUS.gaveWay}`);
    // Drawn without the name, which the first card gives directly under it.
    expect(seen).toBe(`${STATUS.rankedUnnamed(21)} ${STATUS.gaveWay}`);
    expect(seen.includes(name)).toBe(false);
    expect(seen.length).toBeLessThanOrEqual(50);
  });

  test("test_the_page_says_that_a_search_is_open_so_that_the_banner_can_give_way", async () => {
    const { user } = await openSearch();
    const page = () => document.querySelector("[data-search]");
    expect(page()).toHaveAttribute("data-search", "closed");

    await search(user);

    expect(page()).toHaveAttribute("data-search", "open");
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
        // The API says which stretches it made nothing of. The website works none of it out.
        unread: [where(TYPED, UNREAD)],
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
    const show = screen.getByRole("button", { name: SUGGEST.showUnread });

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
        unread: [where(text, "Somewhere with llamas."), where(text, "And a nice vibe please!")],
      })),
    );
    const { user } = await openSearch(api);
    fireEvent.input(promptBox(), { target: { value: text } });
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    const selected = () => promptBox().value.slice(promptBox().selectionStart, promptBox().selectionEnd);

    await user.click(screen.getByRole("button", { name: SUGGEST.showUnread }));
    expect(selected()).toBe("Somewhere with llamas.");
    expect(status()).toContain(NOTICE.partShown(1, 2));

    await user.click(screen.getByRole("button", { name: SUGGEST.showNextUnread }));
    expect(selected()).toBe("And a nice vibe please!");
    expect(status()).toContain(NOTICE.partShown(2, 2));

    await user.click(screen.getByRole("button", { name: SUGGEST.showNextUnread }));
    expect(selected()).toBe("Somewhere with llamas.");
  });

  test("test_once_the_box_is_changed_the_page_no_longer_offers_to_show_a_part_of_it", async () => {
    // Where the words stand is known for the text that was sent. Once the box holds
    // something else, the same offsets would select the wrong words.
    const { user } = await typedIt();
    expect(screen.getByRole("button", { name: SUGGEST.showUnread })).toBeInTheDocument();

    await user.type(promptBox(), " x");

    expect(screen.queryByRole("button", { name: SUGGEST.showUnread })).toBeNull();
    // That a part was left out of the ranking is still true of the ranking, and is still said.
    expect(screen.getByRole("status", { name: NOTICE.partLabel })).toHaveTextContent(NOTICE.partUnread);
  });

  test("test_trying_a_ranking_again_does_not_bring_the_offer_back_over_a_box_that_has_changed", async () => {
    // "Try again" sends the box again only where it was the words that failed. Where it was
    // the ranking, the box may hold anything by then, and the offsets are of what was sent.
    const { user, api } = await typedIt();
    await user.type(promptBox(), " and more");
    expect(screen.queryByRole("button", { name: SUGGEST.showUnread })).toBeNull();
    api.on("rank", "error-internal");
    await everyChip(user);
    await user.click(within(chipsRegion()).getAllByRole("button", { name: new RegExp(`^${CHIPS.remove}`) })[0] as HTMLElement);
    const alert = await screen.findByRole("alert");
    api.on("rank", "rank-first");

    await user.click(within(alert).getByRole("button", { name: PROMPT.tryAgain }));
    await settled();

    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: SUGGEST.showUnread })).toBeNull();
  });

  test("test_what_was_typed_is_written_nowhere_outside_the_box", async () => {
    const opened = await openSearch(partly());
    fireEvent.input(promptBox(), { target: { value: TYPED.replace("Cindermoor Works", CANARY) } });
    await opened.user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    await opened.user.click(screen.getByRole("button", { name: SUGGEST.showUnread }));

    const page = opened.container.cloneNode(true) as HTMLElement;
    page.querySelectorAll("textarea").forEach((box) => box.remove());
    expect(page.innerHTML.includes(CANARY)).toBe(false);
    expect(page.innerHTML.includes("one bed flat")).toBe(false);
  });

  test("test_a_sentence_read_in_full_says_nothing_of_a_part", async () => {
    const { user } = await openSearch();
    await search(user, sentenceOf("interpret-first"));

    expect(first.body.data.unmet).toEqual([]);
    expect(first.body.data.unread).toEqual([]);
    expect(screen.queryByRole("status", { name: NOTICE.partLabel })).toBeNull();
    expect(screen.queryByRole("button", { name: SUGGEST.showUnread })).toBeNull();
  });
});

describe("a notice, when nothing else was read", () => {
  /** Recorded: a sentence in part about who lives somewhere, of which nothing was applied. */
  const alone = recordedAnswer("interpret", "interpret-suggest-notice").body.data;

  test("test_the_page_does_not_leave_it_said_that_the_rest_was_applied_when_nothing_was", async () => {
    // Seen in a browser: "The rest of your search has been applied." over chips that read
    // "What a search starts from", with no result. The API now says which is true, and the
    // page shows its sentence as it came and adds no line of its own.
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-suggest-notice"));
    await user.type(promptBox(), sentenceOf("interpret-suggest-notice"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    const notice = screen.getByRole("status", { name: NOTICE.label });
    expect(alone.applied.filter((edit) => edit.changed)).toEqual([]);
    expect(alone.notice_text).toMatch(/Nothing you typed has changed your search\.$/);
    expect(notice.textContent).toBe(alone.notice_text);
    expect(document.body.textContent?.includes("has been applied")).toBe(false);
    expect(status()).not.toContain(NOTICE.nothingRead);
    expect(api.callsTo("rank")).toEqual([]);
  });

  test("test_once_a_thing_is_chosen_the_page_no_longer_says_that_nothing_typed_changed_the_search", async () => {
    // Seen in a browser: "More pubs and bars" was pressed, 21 areas were ranked, and directly
    // under "21 areas ranked" the page read "Nothing you typed has changed your search."
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-suggest-notice"));
    await user.type(promptBox(), sentenceOf("interpret-suggest-notice"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    const said = () => document.body.textContent?.includes("Nothing you typed has changed your search") ?? false;
    expect(said()).toBe(true);

    // Leaving a thing out changes nothing, and what was said still holds.
    await user.click(screen.getByRole("button", { name: SUGGEST.named("Skip", "Less transport noise") }));
    expect(said()).toBe(true);

    await user.click(screen.getByRole("button", { name: SUGGEST.named("Add", "Leafy") }));
    await settled();

    expect(results().length).toBeGreaterThan(0);
    expect(said()).toBe(false);
    expect(screen.queryByRole("status", { name: NOTICE.label })).toBeNull();
  });

  test("test_a_notice_with_the_rest_applied_says_that_it_was", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-notice"));
    await search(user, sentenceOf("interpret-notice"));

    const said = recordedAnswer("interpret", "interpret-notice").body.data.notice_text;
    expect(said).toMatch(/The rest of your search has been applied\.$/);
    expect(screen.getByRole("status", { name: NOTICE.label }).textContent).toBe(said);
  });
});

describe("a sentence the rules noticed nothing in, while a model reads it", () => {
  const nothing = recordedAnswer("interpret", "interpret-nothing-read");
  /** What the service answered: the rules at once, with a model still to read, and then the model. */
  const as = (change: Partial<InterpretData>) =>
    responseFrom({ ...nothing, body: { ...nothing.body, data: { ...nothing.body.data, ...change } } });

  test("test_the_page_does_not_say_that_nothing_could_be_read_while_burro_is_still_reading", async () => {
    // Seen in a browser: the rules noticed nothing, and a model was asked. For as long as it
    // read, the page said that nothing in the words could be read, and under that that Burro
    // was still reading the rest of them.
    let letGo: () => void = () => undefined;
    const { user } = await openSearch(
      firstSearch().inTurn(
        "interpret",
        () => as({ model_pending: true }),
        async () => {
          await new Promise<void>((resolve) => (letGo = resolve));
          return as({ interpreter: "model" });
        },
      ),
    );
    const says = (words: string) => document.body.textContent?.includes(words) ?? false;
    await user.type(promptBox(), sentenceOf("interpret-nothing-read"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(says(SUGGEST.reading)).toBe(true);
    expect(says(NOTICE.nothingRead)).toBe(false);

    await act(async () => letGo());
    await settled();

    // Once the model has read the words and made nothing of them either, the page says so.
    expect(says(SUGGEST.reading)).toBe(false);
    expect(status()).toContain(NOTICE.nothingRead);
  });

  test("test_the_page_says_that_nothing_could_be_read_once_the_model_could_not_be_asked", async () => {
    const { user } = await openSearch(
      firstSearch().inTurn(
        "interpret",
        () => as({ model_pending: true }),
        () => {
          throw new TypeError("Failed to fetch");
        },
      ),
    );
    await user.type(promptBox(), sentenceOf("interpret-nothing-read"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(document.body.textContent?.includes(SUGGEST.reading)).toBe(false);
    expect(status()).toContain(NOTICE.nothingRead);
  });
});

describe("a natural sentence", () => {
  /**
   * A service with a model behind it: the rules answer at once, and then the model. One
   * press is answered with the ranking the service gave to it.
   */
  const reading = () =>
    firstSearch()
      .inTurn("interpret", "interpret-rules-at-once", "interpret-by-model-long")
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");

  test("test_one_press_adds_every_offer_that_one_press_may_add_and_says_what_it_did_in_full", async () => {
    // Seen in a browser: a sentence of five things cost five presses on a desk and six on a
    // phone, with no way to take them all. And once there was one, the budget that was typed
    // was not among what it took: the search still assumed renting, and held no budget.
    const { user, api } = await openSearch(reading());
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    expect(api.callsTo("rank")).toEqual([]);
    expect(screen.getByText(SUGGEST.why)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));
    await settled();

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toEqual(recordedAnswer("rank", "rank-one-press").request.body);
    expect(results().length).toBeGreaterThan(0);
    const block = screen.getByRole("region", { name: SUGGEST.title });
    expect(within(block).getByRole("status").textContent).toBe(
      [
        "5 added. Your budget is a firm limit and left out 13 areas: the table of all areas lists each. " +
          "8 need you: the journey can be made a firm limit",
        "mix of brands",
        "recorded crime, which is added under its own name",
        "what homes sell for",
        "homes in the higher council tax bands",
        "Village feel",
        "Age of buildings",
        "nearer a town centre.",
      ].join("; "),
    );
    // What one press may not add is still offered: the four readings of a word for how well off
    // a place is, and the three of a word for its identity. None has a guess. They wait behind
    // one line, so that the answer is in sight.
    expect(within(block).queryAllByRole("listitem")).toHaveLength(0);
    expect(within(block).getByRole("button", { name: SUGGEST.showLeft(7) })).toBeVisible();
    // The button went with what it added. The focus is on the block that says so, and not on nothing.
    expect(block === document.activeElement).toBe(true);
    // What the line says is so: the table of all areas lists each area the budget left out.
    const rows = within(await theTable(user)).getAllByRole("row");
    expect(rows.filter((row) => row.textContent?.includes(FILTERED.over_budget))).toHaveLength(13);
  });

  test("test_after_one_press_the_first_result_stands_directly_after_the_line_that_says_what_it_did", async () => {
    // Seen in a browser, on a build of a real city: after the press the page said what was
    // added and listed seven more offers, each several lines long. The name of the first
    // result was 1,626 px down a desk's screen of 900, and 2,149 px down a phone's of 844.
    const { user } = await openSearch(reading());
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));
    await settled();

    const [first] = results();
    const block = screen.getByRole("region", { name: SUGGEST.title });
    const line = within(block).getByRole("status");
    const back = within(block).getByRole("button", { name: SUGGEST.takeBack });
    // What the press did and how to take it back stand before the first result.
    expect(line.textContent?.startsWith("5 added.")).toBe(true);
    expect(comesBefore(line, back)).toBe(true);
    expect(comesBefore(back, first as HTMLElement)).toBe(true);
    // No offer stands between them: what is left is one button, and nothing of an offer is drawn.
    expect(block.querySelectorAll("li")).toHaveLength(0);
    const between = [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main a[href]")]
      .filter((control) => comesBefore(chipsRegion(), control) && comesBefore(control, first as HTMLElement))
      .filter((control) => !chipsRegion().contains(control))
      .map((control) => control.textContent || control.getAttribute("aria-label"));
    expect(between).toEqual([SUGGEST.takeBack, SUGGEST.showLeft(7)]);
    // Nothing was made of how each wish is led in to, "I want to live somewhere". It asks
    // for nothing, so the page does not say that words were not read.
    expect(screen.queryByText(SUGGEST.unread)).toBeNull();
    expect(screen.queryByRole("button", { name: SUGGEST.showUnread })).toBeNull();

    // Each offer that is left is one press away, and the press adds nothing.
    const ranked = document.body.textContent?.includes("5 added.");
    await user.click(within(block).getByRole("button", { name: SUGGEST.showLeft(7) }));
    expect(within(block).getAllByRole("listitem")).toHaveLength(7);
    expect(ranked).toBe(true);
    expect(within(block).getByRole("status").textContent?.startsWith("5 added.")).toBe(true);
  });

  test("test_after_an_offer_is_added_from_the_open_fold_the_first_result_stands_directly_after_the_line_again", async () => {
    // Seen in a browser, on a build of a real city: the fold was opened and one offer was
    // added from it. The fold stayed open, with the seven that were left drawn whole, and the
    // name of the first result was 1,925 px down a desk's screen of 900 and 2,569 px down a
    // phone's of 844.
    const { user, api } = await openSearch(reading());
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));
    await settled();
    const block = screen.getByRole("region", { name: SUGGEST.title });
    await user.click(within(block).getByRole("button", { name: SUGGEST.showLeft(7) }));
    const left = recordedAnswer("interpret", "interpret-by-model-long").body.data.suggestions.filter(
      (one) => one.add_all === "",
    );
    const offered = within(block).getAllByRole("listitem");
    expect(offered.map((offer) => offer.querySelector("p")?.textContent)).toEqual(left.map((one) => one.does));

    // The first way of the first of them is pressed.
    await user.click(within(offered[0] as HTMLElement).getAllByRole("button")[0] as HTMLElement);
    await settled();

    // What was pressed is ranked, and nothing else: the edits the API gave with that way.
    expect(api.callsTo("rank")).toHaveLength(2);
    expect((api.lastCallTo("rank").body as { operations?: Operations }).operations).toEqual(
      left[0]?.choices[0]?.operations,
    );
    // What is left is one line again, and the first result stands directly after it.
    const [first] = results();
    expect(block.querySelectorAll("li")).toHaveLength(0);
    const between = [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main a[href]")]
      .filter((control) => comesBefore(chipsRegion(), control) && comesBefore(control, first as HTMLElement))
      .filter((control) => !chipsRegion().contains(control))
      .map((control) => control.textContent || control.getAttribute("aria-label"));
    expect(between).toEqual([SUGGEST.takeBack, SUGGEST.showLeft(6)]);
    // The line says what one press added, and that one more was added since. What was
    // chosen of is no longer named as left for the person.
    const line = within(block).getByRole("status").textContent ?? "";
    expect(line.startsWith("5 added. Then 1 more added. Your budget is a firm limit and left out 13 areas")).toBe(true);
    expect(line.includes("7 need you: the journey can be made a firm limit; recorded crime")).toBe(true);
    expect(line.includes(left[0]?.needs ?? "no name")).toBe(false);
    // The line that opens what is left has the focus: one more press opens it, and the
    // press adds nothing.
    const fold = within(block).getByRole("button", { name: SUGGEST.showLeft(6) });
    expect(fold === document.activeElement).toBe(true);
    await user.keyboard("{Enter}");
    expect(within(block).getAllByRole("listitem")).toHaveLength(6);
    expect(api.callsTo("rank")).toHaveLength(2);
  });

  test("test_the_fold_never_hides_that_a_vibe_is_a_rough_guide", async () => {
    // A vibe that is a rough guide says so wherever it is shown, in sight: its label, and the
    // sentence that says why. One press never takes it, so it is among what one press leaves,
    // and what one press leaves folds to one line. The fold takes nothing from its offer, and
    // hides nothing of the vibe once it has been added.
    const [told] = meta.data.rough_guides;
    const said = `${told?.label}. ${told?.why}`;
    const { user, api } = await openSearch(
      firstSearch()
        .on("interpret", "interpret-suggest-rough-guide")
        .inTurn("rank", "rank-rough-guide-one-press", "rank-rough-guide-with-the-rest")
        .inTurn(
          "explain_top",
          reasonsFor("rank-rough-guide-one-press", "explanations-rough-guide"),
          reasonsFor("rank-rough-guide-with-the-rest", "explanations-rough-guide"),
        ),
    );
    await user.type(promptBox(), sentenceOf("interpret-suggest-rough-guide"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    const block = screen.getByRole("region", { name: SUGGEST.title });
    const offers = () => within(block).queryAllByRole("listitem");
    const ofTheGuide = () => offers().find((offer) => offer.textContent?.includes("Add Village feel."));
    const hidden = "[hidden], [aria-hidden='true'], .visually-hidden, details:not([open])";

    // Open, before any press: the offer says its label and its sentence, and nothing hides them.
    expect(told?.label).toBe("Rough guide");
    expect(offers()).toHaveLength(3);
    expect(ofTheGuide()).toHaveTextContent(said);
    expect(ofTheGuide()?.querySelector("[class*='note']")?.closest(hidden)).toBeNull();

    // One press adds the two that need no choice. What is left is the rough guide, behind
    // one line, and the first result stands directly after the line and the fold.
    await user.click(within(block).getByRole("button", { name: SUGGEST.addThese(2) }));
    await settled();
    expect(api.lastCallTo("rank").body).toEqual(recordedAnswer("rank", "rank-rough-guide-one-press").request.body);
    expect(within(block).getByRole("status").textContent).toBe("2 added. 1 needs you: Village feel.");
    expect(offers()).toHaveLength(0);
    const fold = within(block).getByRole("button", { name: SUGGEST.showLeft(1) });
    const [first] = results();
    expect(comesBefore(fold, first as HTMLElement)).toBe(true);
    const between = [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main a[href]")]
      .filter((control) => comesBefore(chipsRegion(), control) && comesBefore(control, first as HTMLElement))
      .filter((control) => !chipsRegion().contains(control))
      .map((control) => control.textContent || control.getAttribute("aria-label"));
    expect(between).toEqual([SUGGEST.takeBack, SUGGEST.showLeft(1)]);
    // It was not added, so the search does not hold it, and no chip is of it.
    expect(chipsRegion().textContent?.includes("Village feel")).toBe(false);

    // Opened, the offer is whole: the label and the sentence are in sight as they were, and
    // to open the fold added nothing.
    await user.click(fold);
    expect(offers()).toHaveLength(1);
    expect(ofTheGuide()).toHaveTextContent(said);
    expect(ofTheGuide()?.querySelector("[class*='note']")?.closest(hidden)).toBeNull();
    expect(api.callsTo("rank")).toHaveLength(1);

    // Pressed by a press of its own, it is added. Wherever the page now names it, it says
    // that it is a rough guide, and why: under the chips, in sight, with nothing to press.
    await user.click(within(ofTheGuide() as HTMLElement).getAllByRole("button")[0] as HTMLElement);
    await settled();
    expect(api.callsTo("rank")).toHaveLength(2);
    expect(api.lastCallTo("rank").body).toEqual(
      recordedAnswer("rank", "rank-rough-guide-with-the-rest").request.body,
    );
    expect(chipsRegion().textContent?.includes("Village feel")).toBe(true);
    const notes = [...chipsRegion().querySelectorAll<HTMLElement>("[data-rough-guide='note']")];
    expect(notes.map((note) => note.textContent)).toEqual([`Village feel: ${said}`]);
    expect(notes[0]?.closest(hidden)).toBeNull();
    // The line of what one press did still stands, and nothing is left to fold.
    expect(within(block).getByRole("status").textContent?.startsWith("2 added.")).toBe(true);
    expect(within(block).queryByRole("button", { name: SUGGEST.showLeft(1) })).toBeNull();
    // The first result names the vibe, as it was asked for, and says beside its name that
    // it is a rough guide.
    const [now] = results();
    const labels = [...(now as HTMLElement).querySelectorAll<HTMLElement>("[data-rough-guide]")];
    expect((now as HTMLElement).textContent?.includes("Village feel")).toBe(true);
    expect(labels.length).toBeGreaterThan(0);
    expect(labels.every((label) => label.textContent?.includes(told?.label ?? "no label"))).toBe(true);
    expect(labels.some((label) => label.closest(hidden) !== null)).toBe(false);
  });

  test("test_one_press_takes_back_all_that_was_added_and_the_offers_are_as_they_were", async () => {
    const { user, api } = await openSearch(reading());
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    const before = within(screen.getByRole("region", { name: SUGGEST.title }))
      .getAllByRole("listitem")
      .map((item) => item.textContent);
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));
    await settled();

    await user.click(screen.getByRole("button", { name: SUGGEST.takeBack }));
    await settled();

    const block = within(screen.getByRole("region", { name: SUGGEST.title }));
    expect(block.getAllByRole("listitem").map((item) => item.textContent)).toEqual(before);
    expect(block.queryByRole("button", { name: SUGGEST.takeBack })).toBeNull();
    // The search that is ranked again is the one that stood before the press.
    const [added, back] = api.callsTo("rank").map((call) => call.body as { operations?: unknown; spec: unknown });
    expect(back?.operations).toBeUndefined();
    expect(back?.spec).toEqual(added?.spec);
  });

  test("test_each_offer_shows_the_persons_own_words_and_burros_guess", async () => {
    const { user, api } = await openSearch(reading());
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    const offers = within(screen.getByRole("region", { name: SUGGEST.title })).getAllByRole("listitem");
    // What carries Burro's guess comes first, in the order its words stand in the sentence:
    // quiet, the park, the culture, the journey and the budget.
    expect(offers.map((offer) => offer.querySelector("q")?.textContent)).toEqual([
      "I want to live somewhere quiet",
      "with access to parks",
      "slightly affluent but with some culture around it",
      "At most 35-40min commute from Pellam Exchange",
      "If I'm renting, max \u00a31,900 a month for a 1 bed flat",
      "slightly affluent but with some culture around it",
      "slightly affluent but with some culture around it",
    ]);
    // The last two have no guess: they are the first two of the four readings of a word for
    // how well off a place is, which are the rules' to offer.
    expect(offers.map((offer) => offer.querySelectorAll("[data-guess]").length)).toEqual([1, 1, 1, 1, 1, 0, 0]);
    // The other two of them, and three readings of a word for the identity of a place, wait
    // behind one press.
    expect(screen.getByRole("button", { name: SUGGEST.showAll(12) })).toBeVisible();
    // Nothing is ranked until a choice is pressed.
    expect(api.callsTo("rank")).toEqual([]);
  });

  test("test_the_page_does_not_go_on_saying_that_burro_reads_once_nothing_does", async () => {
    // Seen in a browser: Search was pressed a second time, with the box as it was, while the
    // model read. That call could not leave. The page said that Burro could not be reached,
    // and went on saying that Burro was still reading the rest of the words.
    const { user } = await openSearch(
      firstSearch().inTurn(
        "interpret",
        "interpret-rules-at-once",
        () => new Promise(() => undefined),
        () => {
          throw new TypeError("Failed to fetch");
        },
      ),
    );
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    expect(document.body.textContent?.includes(SUGGEST.reading)).toBe(true);

    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(document.body.textContent?.includes(FAILURE.network)).toBe(true);
    expect(document.body.textContent?.includes(SUGGEST.reading)).toBe(false);
    // What the rules offered is still there to choose from.
    expect(within(screen.getByRole("region", { name: SUGGEST.title })).getAllByRole("listitem").length).toBeGreaterThan(0);
  });

  test("test_taking_it_all_back_shows_what_the_model_read_since_the_press", async () => {
    // Seen in a browser: the one button was pressed before the model had answered. The model
    // then marked its guesses. "Take it all back" showed what the rules had offered at the
    // press, with no guess marked and without the ways the model had added.
    let letGo: () => void = () => undefined;
    const { user } = await openSearch(
      firstSearch()
        .inTurn("interpret", "interpret-rules-at-once", async () => {
          await new Promise<void>((resolve) => (letGo = resolve));
          return recordedAnswer("interpret", "interpret-by-model-long");
        })
        .on("rank", "rank-suggestion-chosen")
        .on("explain_top", "explanations-suggestion-chosen"),
    );
    const guesses = () => document.querySelectorAll("button[data-guess]").length;
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    // The rules guess at what was plainly said: the journey, renting, the budget and the size.
    expect(guesses()).toBe(4);
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(6) }));
    await settled();
    await act(async () => letGo());
    await settled();

    await user.click(screen.getByRole("button", { name: SUGGEST.takeBack }));
    await settled();

    const offered = recordedAnswer("interpret", "interpret-by-model-long").body.data.suggestions;
    expect(guesses()).toBeGreaterThan(0);
    expect(guesses()).toBe(
      // Four are in sight, and with them every other thing that one press may add.
      offered.filter((one, at) => (at < 4 || one.add_all !== "") && one.choices.some((way) => way.guess)).length,
    );
    expect(screen.queryByRole("button", { name: SUGGEST.takeBack })).toBeNull();
  });

  test("test_choosing_the_last_thing_burro_noticed_leaves_the_focus_on_what_burro_understood", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-suggest-place"));
    await user.type(promptBox(), sentenceOf("interpret-suggest-place"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    await user.click(screen.getByRole("button", { name: SUGGEST.named("Add", "Pellam Infirmary") }));

    // What Burro understood is drawn once the service has answered, a moment later.
    await waitFor(() => expect(chipsRegion() === document.activeElement).toBe(true));
    await settled();
    expect(document.activeElement === document.body).toBe(false);
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
    // The label of the box says that what is typed now is added to the search that is open.
    expect(promptBox()).toHaveAccessibleName(PROMPT.labelOpen);
  });

  test("test_start_again_goes_back_to_an_empty_box_the_defaults_and_the_examples", async () => {
    const { user, api } = await openSearch();
    await search(user);
    api.calls.length = 0;

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));

    expect(promptBox()).toHaveValue("");
    expect(promptBox()).toHaveFocus();
    expect(promptBox()).toHaveAccessibleName(PROMPT.label);
    expect(screen.getByRole("region", { name: SHELF.title })).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    expect(screen.getByRole("button", { name: /^Buying a terraced house/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: PROMPT.startAgain })).toBeNull();
    expect(api.calls).toEqual([]);
  });

  test("test_start_again_leaves_nothing_of_the_search_before_neither_in_the_tray_nor_on_the_map", async () => {
    // Seen in a browser: after "Start again" the tray still held three areas of the first
    // search, and the card of the map still named an area that was chosen in it.
    setWebGL(true);
    const { user } = await openSearch();
    await search(user);
    const [one, two] = results().map((result) => within(result).getByRole("heading", { level: 3 }).textContent ?? "");
    await user.click(screen.getByRole("button", { name: COMPARE.addNamed(one as string) }));
    await user.click(screen.getByRole("button", { name: COMPARE.addNamed(two as string) }));
    await theTable(user);
    await user.click(screen.getByRole("button", { name: TABLE.select(one as string) }));
    const tray = () => within(screen.getByRole("region", { name: TRAY.title }));
    expect(tray().getAllByRole("listitem").map((item) => item.textContent?.includes(one as string))).toContain(true);
    expect(screen.getByRole("region", { name: MAP_CARD.label })).toHaveTextContent(one as string);

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));

    expect(tray().queryAllByRole("listitem").length).toBe(0);
    expect(tray().queryByRole("link", { name: TRAY.go(2) })).toBeNull();
    expect(screen.queryByRole("region", { name: MAP_CARD.label })).toBeNull();
    // Nor does the next search bring either back.
    await search(user);
    expect(tray().queryAllByRole("listitem").length).toBe(0);
    expect(screen.queryByRole("region", { name: MAP_CARD.label })).toBeNull();
    expect(screen.getByRole("button", { name: COMPARE.addNamed(one as string) })).toBeInTheDocument();
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
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
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
    await settingsAt(user, SETTINGS.airAndNoise);
    await user.click(screen.getByRole("switch", { name: "Cleaner air" }));
    await settled();

    expect(status()).not.toContain(NOTICE.degraded);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });
});

describe("what is marked as assumed", () => {
  test("test_a_tenure_the_person_typed_is_not_marked_assumed", async () => {
    // Seen in a browser: "Renting assumed" after "Renting a one bed for up to £1,500 a month".
    const { user } = await openSearch();
    await search(user, sentenceOf("interpret-first"));

    expect(sentenceOf("interpret-first")).toMatch(/^Renting/);
    const tenure = within(chipsRegion()).getByRole("button", { name: /^Renting/ });
    expect(tenure.textContent).toBe("Renting");
  });

  test("test_a_tenure_nobody_said_is_marked_assumed", async () => {
    // The ranking is of the spec that was read, as the API's is.
    const { user } = await openSearch(
      firstSearch().on("interpret", "interpret-notice").on("rank", withTheSpecSent("rank-first")),
    );
    await search(user, sentenceOf("interpret-notice"));

    expect(recordedAnswer("interpret", "interpret-notice").body.data.spec.tenure_from).toBe("default");
    expect(within(chipsRegion()).getByRole("button", { name: /^Renting/ }).textContent).toBe(`Renting ${CHIPS.assumed}`);
  });

  test("test_the_kind_of_home_that_one_press_took_is_not_marked_assumed", async () => {
    // Seen in a browser, on the founder's sentence: "£400,000, A flat assumed, firm limit". The
    // person wrote "a 1 bed flat", Burro offered the kind of home with its guess, and one press
    // took it. The way of travelling was not said, and is rightly marked.
    const { user } = await openSearch(
      firstSearch()
        .inTurn("interpret", "interpret-rules-at-once", () => new Promise(() => undefined))
        .on("rank", "rank-one-press")
        .on("explain_top", "explanations-one-press"),
    );
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(6) }));
    await settled();

    const budget = within(chipsRegion()).getByRole("button", { name: /^£1,900 a month/ });
    expect(budget.textContent).toBe(`£1,900 a month, One bedroom, ${CHIPS.firm}`);
    const journey = within(chipsRegion()).getByRole("button", { name: /^Pellam Exchange/ });
    expect(journey.textContent).toBe(
      `Pellam Exchange, Public transport ${CHIPS.assumed}, within 40 minutes, ${CHIPS.flexible}`,
    );
    expect(within(chipsRegion()).getByRole("button", { name: /^Renting/ }).textContent).toBe("Renting");
  });

  test("test_the_kind_of_house_that_burro_took_is_marked_assumed_after_one_press", async () => {
    // The person wrote "a house" and no kind of house. One press holds the budget against a
    // terraced house, and the search says that the kind is assumed.
    const { user } = await openSearch(
      firstSearch().on("interpret", "interpret-suggest-house").on("rank", "rank-house-one-press"),
    );
    await search(user, sentenceOf("interpret-suggest-house"));

    await user.click(screen.getByRole("button", { name: SUGGEST.addAll(2) }));
    await settled();

    const budget = within(chipsRegion()).getByRole("button", { name: /^£400,000/ });
    expect(budget.textContent).toBe(`£400,000, A terraced house ${CHIPS.assumed}, ${CHIPS.firm}`);
    expect(within(chipsRegion()).getByRole("button", { name: /^Buying/ }).textContent).toBe("Buying");
  });

  test("test_the_kind_of_house_of_a_plain_sentence_is_marked_assumed_as_the_api_says", async () => {
    const { user } = await openSearch(
      firstSearch().on("interpret", "interpret-house").on("rank", withTheSpecSent("rank-first")),
    );
    await search(user, sentenceOf("interpret-house"));

    const budget = within(chipsRegion()).getByRole("button", { name: /^£600,000/ });
    expect(budget.textContent).toBe(`£600,000, A terraced house ${CHIPS.assumed}, ${CHIPS.flexible} ${CHIPS.assumed}`);
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
      // An answer names every place of the spec it returns.
      const places = [{ place_id: place.place_id, name: place.name, kind: place.kind }];
      return responseFrom({ ...ranked, body: { ...ranked.body, data: { ...ranked.body.data, spec, places } } });
    };
    const { user } = await openSearch(firstSearch().on("rank", withThePlace));

    await user.type(screen.getAllByRole("combobox", { name: FIND_AREA.label })[0] as HTMLElement, "cin");
    await user.click(await screen.findByRole("option", { name: new RegExp(`^${place.name}`) }));
    await settled();

    // In the row the chip says the name, and that the rest was assumed. Opened, it says every part.
    const chip = within(chipsRegion()).getByRole("button", { name: new RegExp(`^${place.name}`) });
    expect(chip.textContent).toBe(`${place.name}, ${CHIPS.restAssumed}`);
    await user.click(chip);
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
    expect(target).toBe(screen.getByRole("region", { name: MAP.label }));
    expect(target?.tabIndex).toBe(-1);
    // It stands beside the link that skips to the results, before the box.
    expect(comesBefore(toMap, promptBox())).toBe(true);
    // The map is on the page at every width, so the link has nothing to bring forward.
    expect(screen.queryByRole("tablist")).toBeNull();
    expect(user).toBeDefined();
  });

  test("test_there_is_a_link_that_skips_the_map", async () => {
    // The map stands before the results at every width. By keyboard it is a stop, and its
    // controls are more: one link passes all of them.
    const { user } = await openSearch();
    await search(user);
    const map = screen.getByRole("region", { name: MAP.label });

    const past = within(map).getByRole("link", { name: SEARCH.skipMap });
    const target = document.getElementById((past.getAttribute("href") ?? "").slice(1));
    expect(past).toHaveClass("target");
    expect(target).not.toBeNull();
    expect(map.contains(target)).toBe(true);
    for (const control of map.querySelectorAll("button")) {
      expect(comesBefore(past, control)).toBe(true);
      expect(comesBefore(control, target as HTMLElement)).toBe(true);
    }
  });
});

describe("how far a fit is to be trusted, wherever it is given", () => {
  test("test_the_table_says_when_a_fit_rests_on_part_of_what_counts", async () => {
    const { user } = await openSearch();
    await search(user);

    const table = await theTable(user);
    const row = within(table)
      .getAllByRole("row")
      .find((one) => one.textContent?.includes("Marrowfen")) as HTMLElement;
    expect(row.textContent?.includes(COMPLETENESS.some(9, 10))).toBe(true);
  });

  test("test_the_line_says_how_many_areas_went_when_fewer_are_ranked", async () => {
    // Seen in a browser: "21 areas changed place" when a list of 20 became a list of 15.
    const { user, api } = await openSearch();
    await search(user);
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await removeChip(user, "Leafy");
    await settled();

    const said = status().join(" ");
    expect(said).toContain(STATUS.rankedNow(10, -11));
    expect(said).not.toMatch(/2[0-9] areas changed place/);
  });
});

describe("a link that was made", () => {
  test("test_the_link_is_still_there_when_the_person_comes_back_from_another_page", async () => {
    // Seen in a browser: the link was gone after the page of an area was read and left.
    const api = firstSearch().on("create_share", "share-made");
    const page = (
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} />
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
