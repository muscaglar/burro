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

import { ON_A_WIDE_SCREEN } from "@/components/ChipRow/drawn";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { COMPARE, TRAY } from "@/content/compare";
import { HELPERS } from "@/content/helpers";
import { MAP, MAP_CARD, TABLE } from "@/content/map";
import {
  CHIPS,
  COMPLETENESS,
  FAILURE,
  FILTERED,
  LEFT_OUT,
  NOTICE,
  PLACE,
  PROMPT,
  REJECTED,
  REJECTED_LABEL,
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
import { WAIT } from "@/content/wait";
import { REFINE, UNREAD, WAYS } from "@/content/ways";
import { recordedAnswer, responseFrom } from "@/lib/api/recorded";
import type { InterpretData, Operations } from "@/lib/api/schema";
import { merged, NO_EDITS } from "@/lib/search/edits";
import { takenOfAll as madeOfAll } from "@/lib/search/takes";

import { reasonsFor, setOnline, withTheSpecSent, type Responder } from "../support/api";
import { lastMap } from "../support/maplibre";
import { offeringSo, ROUGH, ROUGH_NOTE, sayingSo } from "../support/rough";
import {
  areas,
  arrived,
  bands,
  CANARY,
  chipInFull,
  everyChip,
  firstSearch,
  helper,
  helpers,
  meta,
  openSearch,
  panelOf,
  promptBox,
  removeChip,
  results,
  search,
  settingsAt,
  setWebGL,
  settled,
  tabOf,
  theLine,
  theSettings,
  theSettingsIfAny,
  theTable,
  way,
  ways,
  waysIfAny,
  whatRefines,
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

/**
 * What can be pressed or typed in between what Burro understood and a part of the page
 * that follows it, by what each says or is named. The chips themselves are left out.
 */
const betweenTheChipsAnd = (part: Element) =>
  [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main a[href]")]
    .filter((control) => comesBefore(chipsRegion(), control) && comesBefore(control, part))
    .filter((control) => !chipsRegion().contains(control))
    .map((control) => control.textContent || control.getAttribute("aria-label"));

/** Where the words stand in the text, counted as the API counts. */
function where(text: string, words: string) {
  const start = Array.from(text.slice(0, text.indexOf(words))).length;
  return { start, end: start + Array.from(words).length };
}

/**
 * True where the page says these words to whoever hears it, and says them once: in a line
 * of their own, or in a notice that says of itself what changes in it.
 */
const isHeardOnce = (words: string) =>
  screen.getAllByRole("status").filter((line) => line.textContent?.includes(words)).length === 1 &&
  (document.body.textContent?.split(words).length ?? 0) === 2;

beforeEach(() => setOnline(true));
afterEach(() => setWebGL(false));

describe("after Search is pressed", () => {
  test("test_what_burro_understood_stands_directly_under_the_box_and_before_everything_else", async () => {
    // Seen in a browser: after Search nothing on screen changed. On a phone what was
    // understood began a screen and a half down, under the examples, the tenure and the
    // place field, and the first result two and a half screens down.
    const { user } = await openSearch();
    await search(user);

    const line = theLine();
    const chips = chipsRegion();
    const settings = whatRefines() as HTMLElement;

    expect(line.textContent?.startsWith(STATUS.rankedUnnamed(21))).toBe(true);
    expect(comesBefore(promptBox(), line)).toBe(true);
    expect(comesBefore(line, chips)).toBe(true);
    expect(comesBefore(line, settings)).toBe(true);
    expect(comesBefore(chips, settings)).toBe(true);
    // Renting, buying or visiting and the place field are in the settings, which are closed,
    // so that the answer comes first. The two ways in were for beginning, and have gone.
    expect(settings).toHaveAttribute("aria-expanded", "false");
    expect(waysIfAny()).toBeNull();
    expect(screen.queryByRole("group", { name: TENURE_CHOICE.legend })).toBeNull();
    expect(screen.queryByRole("combobox", { name: PLACE.label })).toBeNull();
    expect(screen.queryByRole("combobox", { name: FIND_AREA.label })).toBeNull();
    // Nothing a person must act on stands between the box and what Burro says of the search.
    const between = [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main textarea")]
      .filter((control) => comesBefore(promptBox(), control) && comesBefore(control, line))
      .map((control) => control.textContent || control.getAttribute("aria-label"));
    expect(between).toEqual([PROMPT.startAgain, PROMPT.submit]);
  });

  test("test_where_a_name_is_borne_by_several_places_no_question_stands_over_the_first_result_and_the_chips_are_as_the_look_draws_them", async () => {
    // Measured at 1440 by 900 with the look: the question was 443 px high and the chips
    // under it 178, and the first result began at 1,040, under the foot of the window. On
    // a phone it began at 811 of 844. Nothing is asked now: the first place the service
    // gave is taken, and nothing stands between what was understood and the answer.
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");

    expect(screen.queryByRole("region", { name: /Which (place|area) did you mean/ })).toBeNull();
    expect(chipsRegion()).toHaveAttribute("data-art", ON_A_WIDE_SCREEN);
    expect(results().length).toBeGreaterThan(0);
    expect(betweenTheChipsAnd(results()[0] as HTMLElement)).toEqual([REFINE.label]);
  });

  test("test_on_a_phone_a_search_of_many_things_folds_its_chips_so_that_the_first_result_comes_first", async () => {
    // Measured on a phone 390 wide: a search of seven things stood seven chips in six rows
    // over the first result, which then ran from 590 to 1,118 of 844. With the chips folded
    // to two rows and a line that opens the rest it begins at 402.
    const asked = recordedAnswer("interpret", "interpret-first").body.data;
    const many = {
      ...asked.spec,
      tags: [
        ...asked.spec.tags,
        ...(["village_feel", "parks_close_by", "foodie"] as const).map((tag_id) => ({
          tag_id,
          weight: 0.5,
          toward: "high" as const,
          provenance: "stated" as const,
        })),
      ],
    };
    // jsdom lays nothing out: the row of chips says how wide it is, as on a phone.
    jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function measured(this: HTMLElement) {
      const wide = this.id === "understood" ? 338 : 0;
      return { width: wide, height: 0, top: 0, left: 0, right: wide, bottom: 0, x: 0, y: 0, toJSON: () => ({}) };
    });
    const api = firstSearch()
      .on("interpret", reading("interpret-first", () => ({ spec: many })))
      .on("rank", withTheSpecSent("rank-first"));
    const { user } = await openSearch(api);
    await search(user);

    const chips = () => within(chipsRegion()).getAllByRole("listitem");
    expect(chips().length).toBeLessThan(5);
    expect(results().length).toBeGreaterThan(0);
    // The line says how many it holds, and what it holds is one press away. The search
    // holds eight things that were asked for: the five of the sentence, and three vibes
    // more. The settings nobody chose have no chip.
    const folded = 8 - chips().length;
    const rest = within(chipsRegion()).getByRole("button", { name: CHIPS.rest(folded) });
    expect(comesBefore(rest, results()[0] as HTMLElement)).toBe(true);
    await user.click(rest);
    expect(chips()).toHaveLength(8);
    expect(chipsRegion().textContent?.includes("Usual settings")).toBe(false);
  });

  test("test_the_line_under_the_box_says_that_nothing_is_ranked_yet_where_it_kept_an_empty_band", async () => {
    // Seen in a browser, where nothing was read: an empty band in the box, 72 px high on a
    // desk and 44 on a phone, kept for a line that said nothing.
    const line = () => screen.getAllByRole("status").find((one) => one.getAttribute("aria-live") === "polite") as HTMLElement;
    const least = recordedAnswer("interpret", "interpret-by-model-least");
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-by-model-least"));
    // Before a search it says nothing, and the page gives it no room.
    expect(line()).toBeEmptyDOMElement();

    // What Burro noticed and could take no way of: nothing is ranked, and nothing is offered.
    await search(user, (least.request.body as { text: string }).text);

    expect(screen.queryByRole("region", { name: "Choose what to add" })).toBeNull();
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect(line().textContent).toBe(WAIT.notYet);
    // It stands where it stood: directly under the box, over what the search starts from.
    expect(comesBefore(promptBox(), line())).toBe(true);
    expect(comesBefore(line(), screen.getByRole("region", { name: CHIPS.startLabel }))).toBe(true);

    api.on("interpret", "interpret-nothing-read");
    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    expect(line()).toBeEmptyDOMElement();
    await search(user, "What is the best way to learn the piano");

    expect(status().join(" ")).toContain(NOTICE.nothingRead);
    expect(line().textContent).toBe(WAIT.notYet);
  });

  test("test_what_was_not_applied_a_notice_and_a_failure_stand_directly_under_the_box_too", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-clarify-no-options"));
    await search(user, sentenceOf("interpret-clarify-no-options"));
    /** What comes after everything Burro says: the part that refines the search. */
    const after = () => whatRefines() as HTMLElement;

    // That Burro does not know a place is said in the line of what was left out.
    const leftOut = screen.getByRole("status", { name: LEFT_OUT.title });
    expect(comesBefore(promptBox(), leftOut)).toBe(true);
    expect(comesBefore(leftOut, after())).toBe(true);

    // What was not applied is said in a line, with what was understood.
    api.on("interpret", "interpret-rejected").on("rank", withTheSpecSent("rank-first"));
    await user.clear(promptBox());
    await search(user, sentenceOf("interpret-rejected"));
    const notApplied = screen.getByRole("region", { name: REJECTED_LABEL });
    expect(within(notApplied).getAllByRole("listitem")).toHaveLength(1);
    expect(comesBefore(promptBox(), notApplied)).toBe(true);
    expect(comesBefore(notApplied, after())).toBe(true);

    api.on("interpret", "interpret-notice").on("rank", "rank-first");
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

  test("test_before_a_search_the_two_ways_in_stand_under_the_heading_and_nothing_is_said_of_a_search", async () => {
    // The first screen held seven things that each asked to be used first. It says who
    // Burro is for and offers two ways in: the heading, the two tabs, and under the first
    // the box and one line of helpers. Nothing stands between the box and the helpers.
    const { user } = await openSearch();
    const line = helpers();
    const map = screen.getByRole("region", { name: MAP.label });

    expect(comesBefore(screen.getByRole("heading", { level: 1 }), ways())).toBe(true);
    expect(comesBefore(ways(), promptBox())).toBe(true);
    expect(comesBefore(promptBox(), line)).toBe(true);
    expect(screen.queryByRole("group", { name: /who (else )?reads/i })).toBeNull();
    expect(comesBefore(line, map)).toBe(true);
    expect(within(ways()).getAllByRole("tab").map((tab) => tab.textContent)).toEqual([WAYS.quick, WAYS.deep]);
    expect(within(line).getAllByRole("button").map((button) => button.textContent)).toEqual([
      HELPERS.example,
      HELPERS.word,
    ]);
    // Between the tabs and the box stands nothing to press, and between the box and the
    // helpers nothing but Search.
    const pressed = (from: Element, to: Element) =>
      [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main textarea")]
        .filter((control) => comesBefore(from, control) && comesBefore(control, to))
        .filter((control) => !from.contains(control))
        .map((control) => control.textContent);
    expect(pressed(ways(), promptBox())).toEqual([]);
    expect(pressed(promptBox(), line)).toEqual([PROMPT.submit]);

    // What a helper opens stands under the whole line, and before the map.
    const opened = {
      example: () => screen.getByRole("heading", { name: PROMPT.examplesTitle }),
      word: () => screen.getByRole("region", { name: SHELF.title }),
    };
    for (const which of ["example", "word"] as const) {
      await helper(user, which);
      expect(line.contains(opened[which]())).toBe(false);
      expect(comesBefore(line, opened[which]())).toBe(true);
      expect(comesBefore(opened[which](), map)).toBe(true);
    }
    // The second way holds the settings, which ask renting, buying or visiting first, what
    // ranks by them, and the field that finds an area by its name, in that order. The map
    // comes after them.
    await way(user, "deep");
    const asks = screen.getAllByRole("group", { name: TENURE_CHOICE.legend })[0] as HTMLElement;
    expect(theSettings()).toContainElement(asks);
    expect(within(theSettings()).getAllByRole("radio")[0]).toBe(within(asks).getAllByRole("radio")[0]);
    const parts = [
      ways(),
      theSettings(),
      screen.getByRole("button", { name: SETTINGS.rank }),
      screen.getByRole("textbox", { name: FIND_AREA.labelAlone }),
      map,
    ];
    parts.slice(1).forEach((part, at) => expect(comesBefore(parts[at] as HTMLElement, part)).toBe(true));
    for (const part of parts.slice(1, -1)) expect(panelOf("deep")).toContainElement(part);
    // No button stands over the settings there: nothing opens or closes them before a search.
    expect(whatRefines()).toBeNull();
    expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();
    // Nothing is understood of anything yet, so there are no chips, no list and nothing to start again.
    expect(screen.queryByRole("region", { name: CHIPS.startLabel })).toBeNull();
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    expect(screen.queryByRole("button", { name: PROMPT.startAgain })).toBeNull();
  });

  test("test_the_results_come_directly_after_what_was_understood_and_the_one_way_to_refine_it", async () => {
    // Seen on a phone: the first result was 2,100 pixels down, and 6,425 with the settings open.
    // The settings are one part, closed until it is pressed, and nothing else stands in between.
    const { user } = await openSearch();
    await search(user);
    const list = screen.getByRole("list", { name: RESULTS.listLabel });
    const toResults = screen.getByRole("link", { name: SEARCH.skipToResults });

    expect(toResults).toHaveAttribute("href", "#results");
    expect(document.getElementById("results")?.contains(list)).toBe(true);
    // One control and no more: what opens the settings, which holds none of them until it is pressed.
    expect(betweenTheChipsAnd(list)).toEqual([REFINE.label]);
    expect(betweenTheChipsAnd(results()[0] as HTMLElement)).toEqual([REFINE.label]);
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
    expect(theSettingsIfAny()).toBeNull();
    expect(document.getElementById(whatRefines()?.getAttribute("aria-controls") ?? "")).toBeEmptyDOMElement();
    // No button of the old name is left, at the old place or any other.
    expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();
    // The way to sharing, and the map, stand after the first result.
    const [one, two] = results();
    const share = screen.getByRole("button", { name: SHARE.open });
    expect(comesBefore(one as HTMLElement, share)).toBe(true);
    expect(comesBefore(share, two as HTMLElement)).toBe(true);
    expect(comesBefore(share, screen.getByRole("region", { name: MAP.label }))).toBe(true);
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
    // A numbered list of areas directly under the line that says how many were ranked says what it is.
    const { user } = await openSearch();
    await search(user);

    const heading = screen.getByRole("heading", { level: 2, name: RESULTS.title });
    expect(heading.classList.contains("visually-hidden")).toBe(true);
    expect(screen.getByRole("region", { name: RESULTS.title })).toBe(document.getElementById("results"));
  });

  test("test_what_happened_is_said_in_two_lines_of_a_phone_at_the_most_and_the_first_result_is_named_by_its_card", async () => {
    // Seen on a phone: "22 areas ranked. First: Otterby Fields. Settings you did not choose
    // now count for less." took two lines above the chips, and named the card under it.
    const { user } = await openSearch();
    await search(user);
    const line = theLine();
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
    // It is written as a person would say it, and is two lines of a phone and no more.
    // Measured at 390 wide, in the reading face at 15 px: 89 letters stood in two lines and
    // 96 in three, and a third line puts the foot of the first result under the first screen.
    expect(seen.length).toBeLessThanOrEqual(89);
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

  /** The one line that names what was left out of the search, and what it opens to. */
  const leftOut = () => screen.getByRole("status", { name: LEFT_OUT.title });
  const opened = async (user: Awaited<ReturnType<typeof openSearch>>["user"]) => {
    const opens = leftOut().querySelector("details") as HTMLDetailsElement;
    if (!opens.open) await user.click(leftOut().querySelector("summary") as HTMLElement);
    return within(leftOut());
  };

  test("test_that_a_part_was_not_read_is_said_beside_the_box_and_not_under_the_chips", async () => {
    // Seen in a browser: the budget and the workplace were not read, 21 areas were ranked
    // as if they had been, and the one sign was a grey line under the chips, off the screen.
    const { user } = await typedIt();

    // One line says that words were left out of the search, where it is seen: it is a
    // notice, and stands beside the box, over what was understood.
    const said = leftOut();
    expect(said.querySelector("summary")?.textContent).toBe(`${LEFT_OUT.title}: ${LEFT_OUT.words}`);
    expect(comesBefore(promptBox(), said)).toBe(true);
    expect(comesBefore(said, chipsRegion())).toBe(true);
    // It is said once: the line under the chips that said it is not drawn as well.
    expect(screen.queryByText(UNMET.other)).toBeNull();
    // It is not small print: it is drawn as a note of its own, and not as a hint.
    expect(said.className).not.toMatch(/hint|muted/);
    expect(said.className).toMatch(/left/);
    // What follows for the ranking is one press away, in whole sentences.
    expect((await opened(user)).getByRole("listitem")).toHaveTextContent(NOTICE.partUnread);
    expect(NOTICE.partUnread).toMatch(/ranking/);
  });

  test("test_the_page_shows_which_part_by_selecting_it_in_the_box", async () => {
    const { user } = await typedIt();
    const show = (await opened(user)).getByRole("button", { name: SUGGEST.showUnread });

    await user.click(show);

    expect(promptBox()).toHaveFocus();
    expect(promptBox().value.slice(promptBox().selectionStart, promptBox().selectionEnd)).toBe(UNREAD);
    expect(isHeardOnce(NOTICE.partShown(1, 1))).toBe(true);
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
    expect(isHeardOnce(NOTICE.partShown(1, 2))).toBe(true);

    await user.click(screen.getByRole("button", { name: SUGGEST.showNextUnread }));
    expect(selected()).toBe("And a nice vibe please!");
    expect(isHeardOnce(NOTICE.partShown(2, 2))).toBe(true);

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
    expect(leftOut().querySelector("summary")?.textContent).toBe(`${LEFT_OUT.title}: ${LEFT_OUT.words}`);
    expect((await opened(user)).getByRole("listitem")).toHaveTextContent(NOTICE.partUnread);
    expect((await opened(user)).queryAllByRole("button")).toEqual([]);
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
    const nothingNoticed = reading("interpret-suggest-notice", () => ({ suggestions: [] }));
    const { user, api } = await openSearch(firstSearch().on("interpret", nothingNoticed));
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

  test("test_once_burro_has_taken_what_it_noticed_the_page_does_not_say_that_nothing_typed_changed_the_search", async () => {
    // Seen in a browser, when a thing was chosen: 21 areas were ranked, and directly under
    // "21 areas ranked" the page read "Nothing you typed has changed your search." Burro
    // takes what it noticed of itself now, so the sentence is untrue as soon as it is read.
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-suggest-notice"));
    await user.type(promptBox(), sentenceOf("interpret-suggest-notice"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(alone.suggestions.map((one) => one.label)).toEqual(["Leafy", "Less transport noise"]);
    expect(results().length).toBeGreaterThan(0);
    expect(document.body.textContent?.includes("Nothing you typed has changed your search")).toBe(false);
    // What the notice is there to say is said still, whole and as it came: what Burro ranks
    // by, and that nobody can ask for fewer of any group of people. The page adds no line
    // of its own to it.
    const notice = screen.getByRole("status", { name: NOTICE.label }).textContent ?? "";
    expect(alone.notice_text.startsWith(notice)).toBe(true);
    expect(notice).toMatch(/^Burro ranks places by what is there\./);
    expect(notice).toMatch(/you cannot ask for fewer of any group of people\.$/);
    expect(alone.notice_text.slice(notice.length)).toBe(" Nothing you typed has changed your search.");
    expect(document.body.textContent?.includes("has been applied")).toBe(false);
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
    const api = firstSearch();
    const model = api.gate(() => as({ interpreter: "model" }));
    const { user } = await openSearch(api.inTurn("interpret", () => as({ model_pending: true }), model.answers));
    const says = (words: string) => document.body.textContent?.includes(words) ?? false;
    await user.type(promptBox(), sentenceOf("interpret-nothing-read"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(model.waiting()).toBe(1);
    expect(says(SUGGEST.reading)).toBe(true);
    expect(says(NOTICE.nothingRead)).toBe(false);

    await act(async () => model.release());
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
  // The founder walked the page and wrote: "When running a search, don't ask the user to add
  // anything, assume they want it to be added and just present the results."
  const atOnce = recordedAnswer("interpret", "interpret-rules-at-once").body.data;
  const long = recordedAnswer("interpret", "interpret-by-model-long").body.data;
  /**
   * A service with a model behind it: the rules answer at once, and then the model. What
   * Burro takes is answered with the ranking the service gave to the things of that sentence.
   */
  const reading = () =>
    firstSearch()
      .inTurn("interpret", "interpret-rules-at-once", "interpret-by-model-long")
      .on("rank", "rank-one-press")
      .on("explain_top", "explanations-one-press");
  /** The edits of the way Burro takes of each offer of a reading, in the order they were noticed. */
  const takenOfAll = (offers: InterpretData["suggestions"]) =>
    madeOfAll(offers, meta.data).reduce((all, made) => (made.way === null ? all : merged(all, made.operations)), NO_EDITS);

  test("test_one_press_of_search_ranks_a_sentence_of_many_things_and_asks_nothing", async () => {
    // Seen in a browser: a sentence of five things cost five presses on a desk and six on a
    // phone, with no way to take them all. And once there was one, the budget that was typed
    // was not among what it took: the search still assumed renting, and held no budget.
    const { user, api } = await openSearch(reading());
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    // Nothing is offered to be pressed, and nothing asks.
    expect(screen.queryByRole("region", { name: "Choose what to add" })).toBeNull();
    expect(document.body.textContent?.includes("only when you press it")).toBe(false);
    expect(
      screen.queryAllByRole("button", { name: /^(Add (all|the) \d|Add$|Skip|Take it all back|Show all \d|Show the \w+ left)/ }),
    ).toEqual([]);
    // One ranking was asked for, of everything the rules noticed: the budget as it was
    // worded, renting, the home, the journey as a guide, and every wish.
    const [ranked] = api.callsTo("rank").map((call) => call.body as { operations: Operations; spec: unknown });
    expect(api.callsTo("rank")).toHaveLength(1);
    expect(ranked?.spec).toEqual(atOnce.spec);
    expect(ranked?.operations).toEqual(takenOfAll(atOnce.suggestions));
    expect(ranked?.operations.budget_ops.map((edit) => [edit.tenure, edit.amount, edit.segment, edit.strictness])).toEqual(
      expect.arrayContaining([
        ["rent", 0, "unchanged", "unchanged"],
        ["unchanged", 1900, "unchanged", "hard"],
        ["unchanged", 0, "bed_1", "unchanged"],
      ]),
    );
    expect(ranked?.operations.commute_ops.map((edit) => [edit.max_minutes, edit.strictness])).toEqual([[40, "soft"]]);
    expect(results().length).toBeGreaterThan(0);
    // What the ranking left out is listed where every area is: each area the budget left out.
    const rows = within(await theTable(user)).getAllByRole("row");
    expect(rows.filter((row) => row.textContent?.includes(FILTERED.over_budget))).toHaveLength(13);
  });

  test("test_after_a_natural_sentence_the_first_result_stands_directly_after_what_was_understood_and_what_refines_it", async () => {
    // Seen in a browser, on a build of a real city: after the press the page said what was
    // added and listed seven more offers, each several lines long. The name of the first
    // result was 1,626 px down a desk's screen of 900, and 2,149 px down a phone's of 844.
    const { user } = await openSearch(reading());
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    const [first] = results();
    // One control and no more stands between what Burro understood and the first result:
    // what opens the settings, closed.
    expect(betweenTheChipsAnd(first as HTMLElement)).toEqual([REFINE.label]);
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
    // Nothing was made of how each wish is led in to, "I want to live somewhere". It asks
    // for nothing, so the page does not say that words were not read.
    expect(screen.queryByText(SUGGEST.unread)).toBeNull();
    expect(screen.queryByRole("button", { name: SUGGEST.showUnread })).toBeNull();
    expect(document.body.textContent?.includes(NOTICE.partUnread)).toBe(false);
  });

  test("test_what_counts_recorded_crime_is_not_taken_and_the_page_says_so_with_the_one_account_of_when_it_counts", async () => {
    // Recorded crime counts only when a person asks for it by name. A word for how well off
    // a place is was read, among other things, as a vibe that counts it: that is no asking.
    const { user, api } = await openSearch(reading());
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    for (const call of api.callsTo("rank")) {
      const sent = (call.body as { operations?: Operations }).operations;
      expect(sent?.tag_ops.map((edit) => edit.tag_id)).not.toContain("street_character");
    }
    // It is named in the line of what was left out, which opens to the one account.
    const left = screen.getByRole("status", { name: LEFT_OUT.title });
    expect(left.querySelector("summary")?.textContent?.startsWith(`${LEFT_OUT.title}: Gritty; `)).toBe(true);
    const why = within(left).getAllByRole("listitem").map((line) => line.textContent);
    expect(why[0]).toBe(`Gritty. ${REJECTED.crime_needs_explicit_request}`);
    // Nothing else of what was left out is said to be of recorded crime.
    expect(why.filter((line) => line?.includes("recorded crime"))).toHaveLength(1);
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
    expect(chipsRegion().textContent?.includes("Gritty")).toBe(false);
    expect(chipsRegion().textContent?.includes("recorded crime")).toBe(false);
  });

  test("test_a_vibe_the_service_holds_less_sure_is_taken_as_any_other_and_nothing_of_the_search_says_how_sure_it_is", async () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a
    // user". One press never took such a vibe, and its offer said why with its label. It is
    // taken as every other thing is now, and is a chip as any other. The service says
    // neither the label nor why since, in the release or in an offer, and one may again: so
    // the page is handed the release, and is answered with the reading, as a service gave
    // them that said both.
    const told = sayingSo(meta.data);
    const offered = recordedAnswer("interpret", "interpret-suggest-rough-guide");
    const noticed = offeringSo(offered.body.data);
    const { user, api } = await openSearch(
      firstSearch()
        .on("interpret", () => responseFrom({ ...offered, body: { ...offered.body, data: noticed } }))
        .on("rank", "rank-rough-guide-with-the-rest")
        .on("explain_top", reasonsFor("rank-rough-guide-with-the-rest", "explanations-rough-guide")),
      told,
    );
    await user.type(promptBox(), sentenceOf("interpret-suggest-rough-guide"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(told.rough_guides).toEqual([ROUGH]);
    expect(noticed.suggestions.map((one) => one.note)).toEqual(["", "", ROUGH_NOTE]);
    expect(noticed.suggestions.map((one) => one.label)).toEqual(["Leafy", "Quiet streets", "Village feel"]);
    expect(api.callsTo("rank")).toHaveLength(1);
    expect((api.lastCallTo("rank").body as { operations: Operations }).operations.tag_ops.map((edit) => edit.tag_id)).toEqual([
      "leafy",
      "quiet_residential",
      "village_feel",
    ]);
    // Nobody said "village feel" in so many words that one press took it: it is assumed.
    const chip = within(chipsRegion()).getByRole("button", { name: /^Village feel/ });
    expect(chip.textContent).toBe(`Village feel ${CHIPS.assumed}`);
    const search_ = screen.getByRole("region", { name: SEARCH.formLabel });
    expect(search_.querySelectorAll("[data-rough-guide]")).toHaveLength(0);
    expect(search_.textContent?.includes(ROUGH.label)).toBe(false);
    expect(search_.textContent?.includes(ROUGH.why)).toBe(false);
    // Nor anywhere else on the page, in sight or out of it.
    expect(/rough guide|less sure/i.test(document.body.textContent ?? "")).toBe(false);
  });

  test("test_everything_burro_took_is_a_chip_that_can_be_taken_off_and_the_search_is_ranked_without_it", async () => {
    // One press took back all that one press had added. Nothing is added at a press now:
    // each thing Burro took is a chip of what it understood, and each chip can be taken off.
    const pressed = recordedAnswer("rank", "rank-one-press").body.data;
    const { user, api } = await openSearch(reading());
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    await everyChip(user);

    const names = pressed.spec.tags.map((tag) => meta.data.tags.find((one) => one.tag_id === tag.tag_id)?.label ?? "");
    expect(names.length).toBeGreaterThan(0);
    for (const name of names) {
      expect(within(chipsRegion()).getByRole("button", { name: `${CHIPS.remove}: ${name}` })).toBeInTheDocument();
    }
    const calls = api.callsTo("rank").length;

    await removeChip(user, names[0] as string);
    await settled();

    expect(api.callsTo("rank")).toHaveLength(calls + 1);
    expect(api.lastCallTo("rank").body).toMatchObject({
      spec: pressed.spec,
      operations: { tag_ops: [{ action: "remove", tag_id: pressed.spec.tags[0]?.tag_id }] },
    });
  });

  test("test_nothing_a_person_typed_is_drawn_anywhere_but_in_the_box", async () => {
    // Each offer showed the person's own words beside it, cut from the box. No offer is
    // drawn now, and what was typed is in the box and nowhere else on the page.
    const typed = sentenceOf("interpret-by-model-long");
    const { user } = await openSearch(reading());
    await user.type(promptBox(), typed);
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(promptBox()).toHaveValue(typed);
    expect(document.querySelectorAll("q")).toHaveLength(0);
    const said = document.body.textContent ?? "";
    for (const words of ["I want to live somewhere quiet", "slightly affluent", "35-40min", "If I'm renting"]) {
      expect(typed.includes(words)).toBe(true);
      expect(said.includes(words)).toBe(false);
    }
  });

  test("test_the_page_does_not_go_on_saying_that_burro_reads_once_nothing_does", async () => {
    // Seen in a browser: Search was pressed a second time, with the box as it was, while the
    // model read. That call could not leave. The page said that Burro could not be reached,
    // and went on saying that Burro was still reading the rest of the words.
    const reads = firstSearch();
    const { user, api } = await openSearch(
      reads
        .inTurn("interpret", "interpret-rules-at-once", reads.never, () => {
          throw new TypeError("Failed to fetch");
        })
        .on("rank", "rank-one-press")
        .on("explain_top", "explanations-one-press"),
    );
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    expect(document.body.textContent?.includes(SUGGEST.reading)).toBe(true);
    // What the rules read is ranked meanwhile: it never waits on a model.
    expect(results().length).toBeGreaterThan(0);

    // Since 2026-09-26 a box that holds nothing the search has not read sends nothing. The
    // model reads on, and the page goes on saying so.
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    expect(api.callsTo("interpret")).toHaveLength(2);
    expect(document.body.textContent?.includes(SUGGEST.reading)).toBe(true);

    // Words are added and sent, which stops the model's reading, and that call cannot leave.
    await user.type(promptBox(), " and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(api.callsTo("interpret")).toHaveLength(3);
    expect(document.body.textContent?.includes(FAILURE.network)).toBe(true);
    expect(document.body.textContent?.includes(SUGGEST.reading)).toBe(false);
  });

  test("test_what_a_model_reads_once_the_answer_is_shown_changes_nothing_that_the_rules_read_the_same", async () => {
    // Seen in a browser: the one button was pressed before the model had answered, and the
    // model then marked its guesses. Nothing is pressed now, and the model reads the same
    // things the rules read: nothing is taken twice, and the ranking is not asked for again.
    const api = firstSearch();
    const model = api.gate("interpret-by-model-long");
    const { user } = await openSearch(
      api
        .inTurn("interpret", "interpret-rules-at-once", model.answers)
        .on("rank", "rank-one-press")
        .on("explain_top", "explanations-one-press"),
    );
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    const before = { chips: chipsRegion().textContent, first: results()[0]?.textContent, calls: api.callsTo("rank").length };
    expect(model.waiting()).toBe(1);

    await act(async () => model.release());
    await settled();

    expect(long.suggestions.length).toBeGreaterThan(0);
    expect(api.callsTo("rank")).toHaveLength(before.calls);
    expect(chipsRegion().textContent).toBe(before.chips);
    expect(results()[0]?.textContent).toBe(before.first);
    expect(document.body.textContent?.includes(SUGGEST.reading)).toBe(false);
  });

  test("test_after_a_sentence_of_which_burro_took_a_thing_the_focus_is_where_the_press_left_it_and_never_on_nothing", async () => {
    // The last offer took its block with it when it was chosen, and the focus went to what
    // Burro understood. Nothing goes from under a press now: Search was pressed, and stays.
    const { user } = await openSearch(
      firstSearch().on("interpret", "interpret-suggest-place").on("rank", "rank-first").on("explain_top", "explanations-first"),
    );
    await user.type(promptBox(), sentenceOf("interpret-suggest-place"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(results().length).toBeGreaterThan(0);
    expect(document.activeElement === document.body).toBe(false);
    expect(screen.getByRole("button", { name: PROMPT.submit })).toHaveFocus();
  });
});

describe("starting a new search", () => {
  test("test_once_a_search_is_open_start_again_is_beside_the_box_and_the_helpers_are_gone", async () => {
    // Seen in a browser: a second example was added to the first search, and the only
    // "Start again" was inside the block that a failure draws.
    const { user } = await openSearch();
    await helper(user, "example");
    expect(screen.getByRole("button", { name: /^Buying a terraced house/ })).toBeInTheDocument();

    await search(user);

    // The helpers go with what the open one held, as the shelf and the examples went.
    expect(screen.queryByRole("button", { name: /^Buying a terraced house/ })).toBeNull();
    expect(screen.queryByRole("group", { name: HELPERS.label })).toBeNull();
    for (const which of [HELPERS.example, HELPERS.word]) {
      expect(screen.queryByRole("button", { name: which })).toBeNull();
    }
    // The two ways in were for beginning, and go as the helpers do.
    expect(waysIfAny()).toBeNull();
    expect(screen.queryAllByRole("tab")).toEqual([]);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("button", { name: PROMPT.startAgain })).toBeInTheDocument();
    // The label of the box says that what is typed now is added to the search that is open.
    expect(promptBox()).toHaveAccessibleName(PROMPT.labelOpen);
  });

  test("test_start_again_goes_back_to_an_empty_box_the_defaults_and_the_helpers_each_closed", async () => {
    const { user, api } = await openSearch();
    // A helper was open when the search began.
    await helper(user, "word");
    await search(user);
    api.calls.length = 0;

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));

    expect(promptBox()).toHaveValue("");
    expect(promptBox()).toHaveFocus();
    expect(promptBox()).toHaveAccessibleName(PROMPT.label);
    // The two ways in come back as they first stood, with the first chosen. Its helpers are
    // each closed, with what each opens one press away.
    expect(within(ways()).getAllByRole("tab").map((tab) => [tab.textContent, tab.getAttribute("aria-selected")])).toEqual([
      [WAYS.quick, "true"],
      [WAYS.deep, "false"],
    ]);
    expect(
      within(helpers())
        .getAllByRole("button")
        .map((button) => [button.textContent, button.getAttribute("aria-expanded")]),
    ).toEqual([
      [HELPERS.example, "false"],
      [HELPERS.word, "false"],
    ]);
    expect(whatRefines()).toBeNull();
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    await helper(user, "example");
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
    // settings do the same job." The settings could not reach it either.
    const api = firstSearch().unreachable("interpret");
    const { user } = await openSearch(api);

    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent(FAILURE.network);
    // The words are not blamed, and the person is not sent to the settings, before a search
    // or with one open: the settings could not reach Burro either.
    for (const blames of [NOTICE.degraded, UNREAD.before]) {
      expect(status()).not.toContain(blames);
      expect(document.body.textContent?.includes(blames)).toBe(false);
    }
    // The page has not opened the settings: no search is open, so they are in the second
    // way in, which is not chosen, and nothing of them is drawn.
    expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "false");
    expect(theSettingsIfAny()).toBeNull();
    expect(whatRefines()).toBeNull();
    expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();
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
    // No search is open, so the line names the second way in, where the settings are.
    await waitFor(() => expect(status()).toContain(UNREAD.before));
    const line = () => screen.getByText(UNREAD.before).closest("div")?.parentElement as HTMLElement;
    expect(within(line()).getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();

    // The person goes where the line sends them, and it is said there with its way to try again.
    await settingsAt(user, SETTINGS.airAndNoise);
    expect(within(line()).getByRole("button", { name: PROMPT.tryAgain })).toBeVisible();
    expect(screen.getAllByRole("button", { name: PROMPT.tryAgain })).toHaveLength(1);

    // A control is used: the person has done something about it, and the line goes. What
    // was chosen in the second way in is kept, and its button makes the search of it.
    await user.click(screen.getByRole("switch", { name: "Cleaner air" }));
    await settled();

    for (const gone of [UNREAD.before, NOTICE.degraded]) expect(status()).not.toContain(gone);
    expect(screen.queryByRole("button", { name: PROMPT.tryAgain })).toBeNull();
    await user.click(within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank }));
    await settled();
    for (const gone of [UNREAD.before, NOTICE.degraded]) expect(status()).not.toContain(gone);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_with_a_search_open_that_words_could_not_be_read_has_its_way_to_try_them_again_beside_it_too", async () => {
    // With a search open the settings are the part that refines it, and the line says that
    // they do the same job. It goes once one of them is used, with its way to try again.
    const api = firstSearch();
    const { user } = await openSearch(api);
    await search(user);
    api.on("interpret", "error-internal");
    await user.clear(promptBox());
    await user.type(promptBox(), "somewhere by the river");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(NOTICE.degraded));
    const line = () => screen.getByText(NOTICE.degraded).closest("div")?.parentElement as HTMLElement;

    expect(status()).not.toContain(UNREAD.before);
    expect(within(line()).getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();
    expect(results()).toHaveLength(SHOWN_AT_FIRST);

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await settingsAt(user, SETTINGS.airAndNoise);
    await user.click(screen.getByRole("switch", { name: "Cleaner air" }));
    await settled();

    expect(status()).not.toContain(NOTICE.degraded);
    expect(screen.queryByRole("button", { name: PROMPT.tryAgain })).toBeNull();
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

  test("test_what_a_person_said_of_the_home_is_not_marked_assumed_and_what_burro_chose_of_the_journey_is", async () => {
    // Seen in a browser, on the founder's sentence: "£400,000, A flat assumed, firm limit". The
    // person wrote "a 1 bed flat" and "max", and both are theirs. The way of travelling was
    // not said, and is rightly marked. Nor was it said that the journey is a guide: the
    // person wrote "at most", and Burro took the guide so that no area is left out on a
    // journey that is estimated. That is Burro's choosing, and the chip says so.
    const api = firstSearch();
    const { user } = await openSearch(
      api
        .inTurn("interpret", "interpret-rules-at-once", api.never)
        .on("rank", "rank-one-press")
        .on("explain_top", "explanations-one-press"),
    );
    await user.type(promptBox(), sentenceOf("interpret-by-model-long"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    // A chip that is opened opens the row out, and every chip then says every part of itself.
    await chipInFull(user, /^Pellam Exchange/);

    const budget = within(chipsRegion()).getByRole("button", { name: /^£1,900 a month/ });
    expect(budget.textContent).toBe(`£1,900 a month, one bedroom, ${CHIPS.firm}`);
    const journey = within(chipsRegion()).getByRole("button", { name: /^Pellam Exchange/ });
    expect(journey.textContent).toBe(
      `Pellam Exchange, public transport ${CHIPS.assumed}, 40 minutes, ${CHIPS.flexible} ${CHIPS.assumed}`,
    );
    expect(within(chipsRegion()).getByRole("button", { name: /^Renting/ }).textContent).toBe("Renting");
    // What was said in a word that one press took is not marked. What Burro read into a
    // word for something else is its own reading, and says so.
    expect(within(chipsRegion()).getByRole("button", { name: /^Quiet streets/ }).textContent).toBe("Quiet streets");
  });

  test("test_the_kind_of_house_that_burro_took_is_marked_assumed", async () => {
    // The person wrote "a house" and no kind of house. The budget is held against a
    // terraced house, and the search says that the kind is assumed.
    const { user, api } = await openSearch(
      firstSearch().on("interpret", "interpret-suggest-house").on("rank", "rank-house-one-press"),
    );
    await search(user, sentenceOf("interpret-suggest-house"));

    // What is sent is what one press sent, which the service was recorded taking.
    expect(api.lastCallTo("rank").body).toEqual(recordedAnswer("rank", "rank-house-one-press").request.body);
    const budget = within(chipsRegion()).getByRole("button", { name: /^£400,000/ });
    expect(budget.textContent).toBe(`£400,000, a terraced house ${CHIPS.assumed}, ${CHIPS.firm}`);
    expect(within(chipsRegion()).getByRole("button", { name: /^Buying/ }).textContent).toBe("Buying");
  });

  test("test_the_kind_of_house_of_a_plain_sentence_is_marked_assumed_as_the_api_says", async () => {
    const { user } = await openSearch(
      firstSearch().on("interpret", "interpret-house").on("rank", withTheSpecSent("rank-first")),
    );
    await search(user, sentenceOf("interpret-house"));

    const budget = within(chipsRegion()).getByRole("button", { name: /^£600,000/ });
    expect(budget.textContent).toBe(`£600,000, a terraced house ${CHIPS.assumed}, ${CHIPS.flexible} ${CHIPS.assumed}`);
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
    // The field that finds a place to reach stands in the settings of the second way in,
    // under the journeys. What is chosen there is kept, and its button makes the search.
    await settingsAt(user, SETTINGS.journeys);

    await user.type(within(theSettings()).getByRole("combobox", { name: PLACE.label }), "cin");
    await user.click(await screen.findByRole("option", { name: new RegExp(`^${place.name}`) }));
    await settled();
    await user.click(within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank }));
    await settled();

    // In the row the chip says the name and every part, and which of them was assumed.
    // Opened, it says the same. The person picked the place: nothing says that the place
    // was assumed.
    const chip = within(chipsRegion()).getByRole("button", { name: new RegExp(`^${place.name}`) });
    const said = `${place.name}, public transport ${CHIPS.assumed}, 45 minutes ${CHIPS.assumed}, flexible ${CHIPS.assumed}`;
    expect(chip.textContent).toBe(said);
    await user.click(chip);
    expect(chip.textContent).toBe(said);
  });
});

describe("where the focus is left", () => {
  test("test_where_a_name_is_borne_by_several_places_nothing_goes_from_under_the_press_and_the_focus_stays", async () => {
    // Seen in a browser: the question went when it was answered, and the focus went with
    // it. No question is drawn now, so nothing goes: Search was pressed, and keeps the focus.
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");

    expect(document.activeElement).not.toBe(document.body);
    expect(screen.getByRole("button", { name: PROMPT.submit })).toHaveFocus();
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
    // The map is on the page at every width, so the link has nothing to bring forward: no
    // tab holds the map. The two tabs of the page are the two ways in, which the map stands
    // outside, and they have gone with the search open.
    expect(screen.queryByRole("tablist")).toBeNull();
    expect(screen.queryAllByRole("tabpanel")).toEqual([]);
    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    for (const which of ["quick", "deep"] as const) expect(panelOf(which).contains(target)).toBe(false);
    expect(screen.getByRole("link", { name: SEARCH.skipToMap })).toHaveAttribute("href", `#${target?.id}`);
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
    await settingsAt(user);
    expect(theSettings()).toBeVisible();

    const hidden = [...document.querySelectorAll<HTMLElement>("main .visually-hidden")]
      .filter((one) => one.closest("[role='status'], [aria-live]") === null)
      .map((one) => (one.textContent ?? "").trim())
      .filter((text) => text.split(/\s+/).length > 4);

    expect(hidden).toEqual([]);
  });
});
