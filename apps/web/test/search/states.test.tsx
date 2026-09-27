/**
 * Every state of the search page, as docs/design/web.md section 3 lists
 * them, against the answers recorded from the API.
 */

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";

import { CARD } from "@/content/card";
import { HELPERS } from "@/content/helpers";
import { MAP, TABLE } from "@/content/map";
import {
  CHIPS,
  SHELF,
  FILTERED,
  LEFT_OUT,
  NOTHING_MATCHES,
  NOTICE,
  PROMPT,
  REJECTED,
  REJECTED_LABEL,
  REJECTED_PART,
  RESULTS,
  STATUS,
  SUGGEST,
  TENURE_CHOICE,
  UNMET,
  UNMET_LABEL,
  UNRANKED,
  FIND_AREA,
} from "@/content/search";
import { BUDGET, JOURNEY, SETTINGS } from "@/content/settings";
import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { BANNER } from "@/content/site";
import { UNREAD, WAYS } from "@/content/ways";
import { recordedAnswer, recordedError, responseFrom } from "@/lib/api/recorded";
import type { Operations, Span, UnmetCategory } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { reasonsFor, setOnline, standInApi, withTheSpecSent } from "../support/api";
import { faultsIn } from "../support/axe";
import {
  areas,
  chipInFull,
  everyChip,
  everyResult,
  firstSearch,
  groupsAre,
  helper,
  helpers,
  meta,
  openSearch,
  panelOf,
  promptBox,
  removeChip,
  resultList,
  results,
  search,
  settingsAt,
  settled,
  tabOf,
  theSettings,
  theSettingsIfAny,
  theTable,
  way,
  ways,
  waysIfAny,
  whatRefines,
  workingOf,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

/** The group of the settings that holds a family of vibes, by the name the service gives the family. */
const groupOf = (family: string) => meta.data.families.find((one) => one.family === family)?.label ?? "";

const first = {
  read: recordedAnswer("interpret", "interpret-first").body.data,
  rank: recordedAnswer("rank", "rank-first").body.data,
  explain: recordedAnswer("explain_top", "explanations-first").body.data,
};
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";
/** The sentence a reading was recorded of, so that what is typed is what was answered. */
const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", scenario).request.body as { text: string }).text;
const status = () => screen.getAllByRole("status").map((line) => line.textContent ?? "");
const banner = () => screen.getByRole("region", { name: BANNER.label });
/** True where the part that refines a search is open, and the settings are drawn under it. */
const settingsAreOpen = () => whatRefines()?.getAttribute("aria-expanded") === "true" && theSettingsIfAny() !== null;
/** The two tabs: what each says, and whether it says it is chosen. */
const waysAre = () =>
  within(ways())
    .getAllByRole("tab")
    .map((tab) => [tab.textContent, tab.getAttribute("aria-selected")]);
const THE_FIRST_WAY_CHOSEN = [
  [WAYS.quick, "true"],
  [WAYS.deep, "false"],
];
/** A pattern of these very words, whatever signs they hold. */
const wordFor = (words: string) => words.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
/** Moves the slider of a vibe that runs one way, as a drag that is let go does. */
const slide = (name: string, to: number) => {
  const slider = screen.getByRole("slider", { name });
  fireEvent.pointerDown(slider);
  fireEvent.change(slider, { target: { value: String(to) } });
  fireEvent.pointerUp(slider);
};
/**
 * Presses the button of the second way in, which makes a search of what was chosen in its
 * settings. What is chosen there is kept, and no search is made of it until this is pressed.
 */
const rankTheSettings = async (user: Awaited<ReturnType<typeof openSearch>>["user"]) => {
  await user.click(within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank }));
  await settled();
};

beforeEach(() => setOnline(true));
afterEach(() => jest.useRealTimers());

/** The helpers as they stand in their line: what each says, and whether it says it is open. */
const helpersAre = () =>
  within(helpers())
    .getAllByRole("button")
    .map((button) => [button.textContent, button.getAttribute("aria-expanded")]);
const EVERY_HELPER_CLOSED = [
  [HELPERS.example, "false"],
  [HELPERS.word, "false"],
];

describe("empty: before anything is asked for", () => {
  test("test_the_page_opens_on_two_ways_in_the_first_chosen_with_the_box_two_helpers_each_closed_and_every_area", async () => {
    const { api, user } = await openSearch();

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(promptBox()).toHaveValue("");
    expect(screen.getAllByRole("button", { name: /./ }).map((button) => button.textContent)).toEqual(
      expect.arrayContaining([PROMPT.submit]),
    );
    // The first screen offers two ways in, and the first is chosen: the box. Under it stands
    // one line of helpers, each closed, and what each opens is not on the page until it is
    // pressed. Nothing of the second way is drawn until it is chosen.
    expect(waysAre()).toEqual(THE_FIRST_WAY_CHOSEN);
    expect(helpersAre()).toEqual(EVERY_HELPER_CLOSED);
    expect(screen.queryByRole("heading", { name: PROMPT.examplesTitle })).toBeNull();
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(screen.queryByRole("group", { name: TENURE_CHOICE.legend })).toBeNull();
    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.queryByRole("textbox", { name: FIND_AREA.labelAlone })).toBeNull();
    expect(theSettingsIfAny()).toBeNull();
    expect(panelOf("deep")).toBeEmptyDOMElement();
    // Nothing opens and closes the settings before a search, under their old name or their new.
    expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();
    expect(whatRefines()).toBeNull();
    // The vibes are on the shelf, to look at and to add.
    await helper(user, "word");
    expect(screen.getByRole("region", { name: SHELF.title })).toBeInTheDocument();
    // The second way: the settings, which stand open and ask renting or buying first, the
    // button that makes a search of them, and the field that finds an area by its name.
    // The first way is kept as it was left, and is not drawn while the second is chosen.
    await way(user, "deep");
    expect(panelOf("quick")).not.toBeVisible();
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(screen.getAllByRole("radio", { name: TENURE_CHOICE.rent })[0]).toBeChecked();
    expect(screen.getByRole("textbox", { name: FIND_AREA.labelAlone })).toBeInTheDocument();
    expect(within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank })).toBeVisible();
    expect(theSettings()).toBeVisible();
    // A couple of their groups stand open, to show that a group opens and closes: the
    // first two, and no other.
    const standOpen = groupsAre().filter(([, open]) => open);
    expect(standOpen.map(([name]) => name)).toEqual([SETTINGS.money, SETTINGS.journeys]);
    expect(groupsAre().slice(0, 2)).toEqual(standOpen);
    expect(groupsAre().length).toBeGreaterThan(5);
    // Every area of the release is there by name, as a link to its page, one press from the map.
    await theTable(user);
    for (const area of areas) {
      expect(screen.getAllByRole("link", { name: area.name })[0]).toHaveAttribute(
        "href",
        `/synthetic/${area.slug}`,
      );
    }
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    // Nothing is sent until something is asked for, but the boundaries for the map, and the
    // form, which says who reads what is typed. Neither holds anything of the person.
    expect(api.calls.map((call) => call.operation)).toEqual(["get_geometry", "get_meta"]);
    expect(api.calls.map((call) => call.sent)).toEqual([null, null]);
  });

  test("test_the_synthetic_banner_is_present_in_every_state", async () => {
    const { user, api } = await openSearch();
    expect(banner()).toHaveTextContent(BANNER.text);

    await search(user);
    expect(banner()).toHaveTextContent(BANNER.text);

    api.on("rank", "rank-nothing-matches");
    await removeChip(user, "Leafy");
    await settled();
    expect(banner()).toHaveTextContent(BANNER.text);

    api.on("rank", "error-internal");
    await user.click(screen.getByRole("button", { name: NOTHING_MATCHES.budgetFlexible }));
    await screen.findByRole("alert");
    expect(banner()).toHaveTextContent(BANNER.text);
    expect(within(banner()).queryAllByRole("button")).toEqual([]);
  });

  test("test_an_example_fills_the_box_and_sends_nothing", async () => {
    const { user, api } = await openSearch();
    api.calls.length = 0;
    await helper(user, "example");

    await user.click(screen.getByRole("button", { name: /^Buying a terraced house/ }));

    expect(promptBox().value).toMatch(/^Buying a terraced house/);
    expect(promptBox()).toHaveFocus();
    expect(api.calls).toEqual([]);
    // The examples stay where they were opened, for another to be tried.
    expect(screen.getByRole("button", { name: HELPERS.example })).toHaveAttribute("aria-expanded", "true");
  });

  test("test_opening_a_helper_sends_nothing_and_the_open_one_closes_when_another_is_pressed", async () => {
    const { user, api } = await openSearch();
    api.calls.length = 0;

    for (const which of ["example", "word"] as const) {
      await helper(user, which);
      expect(helpersAre().filter(([, open]) => open === "true")).toEqual([[HELPERS[which], "true"]]);
      // The helper that was pressed keeps the focus: it is still there.
      expect(screen.getByRole("button", { name: HELPERS[which] })).toHaveFocus();
    }
    await user.click(screen.getByRole("button", { name: HELPERS.word }));

    expect(helpersAre()).toEqual(EVERY_HELPER_CLOSED);
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(api.calls).toEqual([]);
  });

  test("test_choosing_the_other_way_in_sends_nothing_and_the_tab_that_was_pressed_keeps_the_focus", async () => {
    const { user, api } = await openSearch();
    api.calls.length = 0;

    for (const which of ["deep", "quick"] as const) {
      await way(user, which);
      expect(waysAre().filter(([, chosen]) => chosen === "true")).toEqual([[WAYS[which], "true"]]);
      expect(tabOf(which)).toHaveFocus();
      expect(panelOf(which)).toBeVisible();
    }

    expect(waysAre()).toEqual(THE_FIRST_WAY_CHOSEN);
    expect(screen.queryByRole("group", { name: TENURE_CHOICE.legend })).toBeNull();
    expect(whatRefines()).toBeNull();
    expect(api.calls).toEqual([]);
  });

  test("test_rent_or_buy_swaps_the_defaults_and_sends_nothing", async () => {
    const { user, api } = await openSearch();
    api.calls.length = 0;
    await way(user, "deep");
    // It is what the second way asks first, over the settings, which ask it as well.
    const [buying] = screen.getAllByRole("radio", { name: TENURE_CHOICE.buy });

    await user.click(buying as HTMLElement);

    for (const asks of screen.getAllByRole("radio", { name: TENURE_CHOICE.buy })) expect(asks).toBeChecked();
    // Nothing has been asked for yet: the page is as it was, and the settings hold a buyer's.
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByRole("region", { name: CHIPS.label })).toBeNull();
    await settingsAt(user, SETTINGS.money);
    const budget = within(screen.getByRole("group", { name: BUDGET.legend }));
    expect(budget.getByRole("textbox", { name: BUDGET.amount.buy })).toHaveValue("");
    expect(api.calls).toEqual([]);
  });

  test("test_the_settings_hold_the_defaults_and_can_be_ranked_by_hand", async () => {
    const { user, api } = await openSearch(standInApi().on("rank", "rank-default-rent").on("explain_top", "explanations-first"));

    await settingsAt(user);
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    // The button goes as it is pressed, and the two ways in with it. The focus goes to what
    // opens the settings from now, and is never left on nothing. Seen in a browser: it was
    // left on the page as a whole.
    expect(whatRefines()).toHaveFocus();
    await settled();

    expect(api.callsTo("interpret")).toEqual([]);
    expect(api.lastCallTo("rank").body).toEqual({ spec: meta.data.defaults.rent, limit: 20 });
    expect(results().length).toBeGreaterThan(0);
    // A search is open, so the two ways in and the helpers have gone. The person asked for
    // the ranking, so the settings are closed over the answer, one press away.
    expect(waysIfAny()).toBeNull();
    expect(screen.queryByRole("group", { name: HELPERS.label })).toBeNull();
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
    expect(theSettingsIfAny()).toBeNull();
    expect(whatRefines()).toHaveFocus();
  });

  test("test_a_setting_moved_before_a_search_keeps_the_focus_and_its_group_and_no_search_opens_until_its_button_is_pressed", async () => {
    // The second way in is built by choosing and then searching. What is chosen is sent to
    // be applied, so that the settings are drawn from what the service holds, and is kept:
    // the tabs stay, and nothing is ranked for the page, until the button is pressed.
    const { user, api } = await openSearch();
    await settingsAt(user, groupOf("green"));
    const slider = screen.getByRole("slider", { name: "Leafy" });
    slider.focus();

    slide("Leafy", 50);
    await settled();

    expect(api.lastCallTo("rank").body).toEqual({
      spec: meta.data.defaults.rent,
      operations: edits.tagWeight("leafy", 0.5, "high"),
      limit: 1,
    });
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect(waysAre()).toEqual([
      [WAYS.quick, "false"],
      [WAYS.deep, "true"],
    ]);
    expect(screen.getByRole("slider", { name: "Leafy" })).toBe(slider);
    expect(slider).toHaveFocus();
    expect(screen.getByRole("button", { name: groupOf("green") })).toHaveAttribute("aria-expanded", "true");

    await rankTheSettings(user);

    // The search is made of what was gathered, with nothing more to apply.
    expect(api.lastCallTo("rank").body).toEqual({ spec: first.rank.spec, limit: 20 });
    expect(results().length).toBeGreaterThan(0);
    expect(screen.queryByRole("group", { name: HELPERS.label })).toBeNull();
    expect(waysIfAny()).toBeNull();
    expect(whatRefines()).toHaveFocus();
  });

  test("test_the_empty_page_has_no_accessibility_fault", async () => {
    const { container } = await openSearch();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("interpreting: a sentence was sent", () => {
  test("test_the_page_says_it_is_reading_at_once_and_keeps_the_text_in_the_box", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);

    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(screen.getByRole("button", { name: PROMPT.reading })).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByRole("button", { name: PROMPT.stop })).toBeInTheDocument();
    expect(status()).toContain(STATUS.reading);
    expect(promptBox()).toHaveValue("leafy and quiet");
    // Burro hops where the results will stand, centre stage, and says nothing to a reader:
    // the line under the box says what happens. No grey bar and no grey card holds the
    // place of the chips or of a result.
    expect(document.querySelectorAll(".skeleton")).toHaveLength(0);
    const wait = screen.getByRole("region", { name: RESULTS.title }).querySelector("[data-wait]");
    expect(wait?.querySelector("[data-pose='hops'][data-stage='true']")).not.toBeNull();
    expect(wait).toHaveAttribute("aria-busy", "true");
    expect([...(wait?.children ?? [])].map((part) => part.getAttribute("aria-hidden"))).toEqual(["true"]);
    expect(document.querySelectorAll("[aria-busy='true']")).toHaveLength(1);

    reading.release();
    await settled();
    expect(screen.getByRole("button", { name: PROMPT.submit })).not.toHaveAttribute("aria-disabled");
    expect(promptBox()).toHaveValue("leafy and quiet");
  });

  test("test_pressing_enter_sends_and_shift_enter_does_not", async () => {
    const { user, api } = await openSearch();

    await user.type(promptBox(), "leafy{Shift>}{Enter}{/Shift}and quiet");
    expect(api.callsTo("interpret")).toEqual([]);
    expect(promptBox().value).toBe("leafy\nand quiet");

    await user.type(promptBox(), "{Enter}");
    await settled();
    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(api.lastCallTo("interpret").body).toMatchObject({ text: "leafy\nand quiet" });
  });

  test("test_stop_ends_the_request_and_returns_to_the_state_before", async () => {
    const { user, api } = await openSearch(firstSearch().silent("interpret"));

    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await user.click(screen.getByRole("button", { name: PROMPT.stop }));

    expect(api.lastCallTo("interpret").init.signal?.aborted).toBe(true);
    expect(screen.getByRole("button", { name: PROMPT.submit })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: PROMPT.stop })).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(status()).not.toContain(STATUS.reading);
    expect(promptBox()).toHaveValue("leafy");
  });

  test("test_a_second_press_while_reading_sends_nothing_more", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);

    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await user.click(screen.getByRole("button", { name: PROMPT.reading }));
    await user.type(promptBox(), "{Enter}");

    expect(api.callsTo("interpret")).toHaveLength(1);
    reading.release();
    await settled();
  });

  test("test_an_empty_box_is_not_sent_and_says_what_to_do", async () => {
    const { user, api } = await openSearch();

    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(api.callsTo("interpret")).toEqual([]);
    expect(screen.getByRole("alert")).toHaveTextContent(PROMPT.empty);
    expect(promptBox()).toHaveAccessibleDescription(expect.stringContaining(PROMPT.empty));
    expect(promptBox()).toHaveFocus();
  });
});

describe("results: the ranking came back", () => {
  test("test_the_chips_say_what_was_understood_and_mark_what_was_assumed", async () => {
    const { user } = await openSearch();
    await search(user);
    const chips = within(screen.getByRole("region", { name: CHIPS.label }));
    const said = () =>
      chips.getAllByRole("listitem").map((chip) => (chip.querySelector("[data-main]") ?? chip).textContent);
    // The words said "Renting", so the tenure is not marked as assumed: the spec says it was stated.
    expect(first.read.operations.budget_ops[0]).toMatchObject({ tenure: "rent", provenance: "stated" });
    expect(first.read.spec.tenure_from).toBe("stated");
    // What was asked for by way of character comes first. The settings nobody chose have no
    // chip: one that is not chosen moves no area, and "Usual settings: 6 assumed" told a
    // person nothing. Each stands with its value where the search is refined.
    expect(said()).toEqual([
      "Leafy",
      "Quiet streets",
      `Cindermoor Works, 35 minutes, ${CHIPS.restAssumed}`,
      "£1,700 a month, one bedroom, flexible assumed",
      "Renting",
    ]);
    // A chip that is opened opens the row out, and each chip then says every part of itself.
    await chipInFull(user, /^Cindermoor Works/);
    expect(said()).toEqual([
      "Leafy",
      "Quiet streets",
      "Cindermoor Works, public transport assumed, 35 minutes, flexible assumed",
      "£1,700 a month, one bedroom, flexible assumed",
      "Renting",
    ]);
    const understood = screen.getByRole("region", { name: CHIPS.label });
    expect(understood.textContent?.includes("Usual settings")).toBe(false);
    // Nothing beside the heading says who read the words: the line under the box says
    // whether a language model reads what is typed, before it is sent.
    expect(understood.textContent ?? "").not.toMatch(/\bAI\b|\bRead (by|with|without)\b/i);
    expect(chips.getAllByRole("heading").map((heading) => heading.textContent)).toEqual([CHIPS.label]);
    expect(chips.getByRole("heading").parentElement?.textContent).toBe(CHIPS.label);
    // What nobody said is still marked, in a word: it is said, and no edge says it.
    expect(understood.textContent?.includes(CHIPS.assumed)).toBe(true);
  });

  test("test_the_list_is_in_rank_order_with_five_cards_and_the_rest_as_rows", async () => {
    const { user } = await openSearch();
    await search(user);
    await settled();

    // Ten at first, and the other ten one press away.
    const shown = () => results().map((one) => within(one).getAllByRole("heading")[0]?.textContent);
    expect(shown()).toEqual(first.rank.ranked.slice(0, SHOWN_AT_FIRST).map((area) => nameOf(area.area_id)));
    await everyResult(user);
    expect(shown()).toEqual(first.rank.ranked.map((area) => nameOf(area.area_id)));
    expect(resultList().tagName).toBe("OL");
    // A card says what its area gives up, and a row does not: the first five are cards.
    const under = (heading: string) =>
      results().map((one) => within(one).queryByRole("heading", { name: heading }) !== null);
    const theFirstFive = first.rank.ranked.map((_, at) => at < 5);
    expect(theFirstFive.filter(Boolean)).toHaveLength(5);
    expect(under(RESULTS.tradeOffTitle)).toEqual(theFirstFive);
    // No result says why it fits until its working is opened. The working of a card then
    // does, and that of a row does not: the line under the list says where it is read.
    expect(under(RESULTS.reasonsTitle)).toEqual(theFirstFive.map(() => false));
    for (const area of first.rank.ranked) await workingOf(user, nameOf(area.area_id));
    expect(under(RESULTS.reasonsTitle)).toEqual(theFirstFive);
    expect(screen.getByText(RESULTS.firstFive)).toBeInTheDocument();
    expect(status()).toContain(`${STATUS.ranked(21, "Farrowmere")} ${STATUS.gaveWay}`);
  });

  test("test_unmet_requests_are_each_said_in_a_line", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-unmet"));
    await search(user);

    const unmet = within(screen.getByRole("region", { name: UNMET_LABEL }));
    expect(unmet.getAllByRole("listitem").map((line) => line.textContent)).toEqual([
      UNMET.broadband,
      UNMET.flood_risk,
      UNMET.community_amenities,
    ]);
  });

  test("test_an_edit_that_was_not_applied_is_said_with_what_it_was_about_and_why", async () => {
    const { user } = await openSearch(
      firstSearch().on("interpret", "interpret-rejected").on("rank", withTheSpecSent("rank-first")),
    );
    await search(user, "somewhere a bit cheaper, near a park");

    // No budget is set, so there is nothing to make cheaper. The line says what the edit
    // was about: "That changed nothing." alone says nothing of what did not change.
    const refused = within(screen.getByRole("region", { name: REJECTED_LABEL }));
    expect(refused.getAllByRole("listitem").map((line) => line.textContent)).toEqual([
      `${REJECTED_PART.budget}: ${REJECTED.nothing_to_change}`,
    ]);
    // The park was applied, and is a chip.
    await everyChip(user);
    const chips = within(screen.getByRole("region", { name: CHIPS.label }));
    expect(chips.getByRole("button", { name: /^Nearer a park/ })).toBeInTheDocument();
  });

  test("test_the_results_page_has_no_accessibility_fault", async () => {
    const { user, container } = await openSearch();
    await search(user);
    await settled();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("refining: a control changed something", () => {
  test("test_the_list_stays_and_is_marked_busy_and_the_control_shows_its_new_value_at_once", async () => {
    const api = firstSearch();
    const { user } = await openSearch(api);
    await search(user);
    await settled();
    const slow = api.hold("rank", "rank-refined");
    api.on("explain_top", "explanations-refined");
    await settingsAt(user, SETTINGS.journeys);
    const journey = within(screen.getByRole("group", { name: JOURNEY.place("Cindermoor Works") }));

    await user.click(journey.getByRole("checkbox", { name: JOURNEY.firm }));

    expect(journey.getByRole("checkbox", { name: JOURNEY.firm })).toBeChecked();
    expect(resultList()).toHaveAttribute("aria-busy", "true");
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(api.lastCallTo("rank").body).toEqual({
      spec: first.rank.spec,
      operations: edits.placeStrictness("syn-p0021", "hard"),
      limit: 20,
    });

    slow.release();
    await settled();
    const refined = recordedAnswer("rank", "rank-refined").body.data;
    await everyResult(user);
    expect(results()).toHaveLength(refined.ranked.length);
    // Every control is drawn again from the spec that came back.
    expect(journey.getByRole("textbox", { name: JOURNEY.longest })).toHaveValue("30");
    // Fewer areas are ranked than were: the line says so, and how many of the rest moved.
    expect(status().join(" ")).toMatch(new RegExp(`${wordFor(STATUS.rankedNow(10, -11))} \\d+ of the rest changed place\\.`));
  });

  test("test_a_chip_opens_the_same_control_the_settings_hold_in_place", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));
    const editor = within(screen.getByRole("group", { name: JOURNEY.place("Cindermoor Works") }));
    await user.click(editor.getByRole("radio", { name: "By bike" }));
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({
      operations: edits.placeMode("syn-p0021", "cycle"),
    });
  });

  test("test_removing_a_chip_sends_the_edit_that_takes_it_out", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();

    await removeChip(user, "Quiet streets");
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({
      operations: edits.tagOff("quiet_residential"),
    });
  });

  test("test_an_edit_the_api_refuses_puts_the_control_back_and_says_why_beside_it", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "rank-rejected-edit");
    await settingsAt(user, SETTINGS.money);
    const budget = within(screen.getByRole("group", { name: BUDGET.legend }));
    const amount = budget.getByRole("textbox", { name: BUDGET.amount.rent });

    await user.clear(amount);
    await user.type(amount, "1{Enter}");
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.budgetAmount(1) });
    expect(amount).toHaveValue("1700");
    expect(amount).toHaveAccessibleDescription(expect.stringContaining(REJECTED.out_of_range));
    expect(budget.getByRole("alert")).toHaveTextContent(REJECTED.out_of_range);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_hiding_an_area_from_its_card_sends_the_edit_that_hides_it", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();

    // Hiding an area is in the working of its result.
    await workingOf(user, "Farrowmere");
    await user.click(screen.getByRole("button", { name: RESULTS.hide("Farrowmere") }));
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.areaHide("syn-n0006") });
  });
});

describe("a place whose name several places bear", () => {
  const asked = recordedAnswer("interpret", "interpret-clarify").body.data;
  const [first] = asked.clarify[0]?.options ?? [];
  const chipsSay = () =>
    within(screen.getByRole("region", { name: CHIPS.label }))
      .getAllByRole("listitem")
      .map((chip) => (chip.querySelector("[data-main]") ?? chip).textContent);

  test("test_nothing_is_asked_and_the_journey_is_to_the_first_place_the_service_gave", async () => {
    const { user, api } = await openSearch(
      firstSearch().on("interpret", "interpret-clarify").on("rank", "rank-two-places").on("explain_top", "explanations-two-places"),
    );
    await search(user, "Leafy, renting, 30 minutes to Pellam");

    expect(asked.clarify[0]?.options.map((option) => option.name)).toEqual([
      "Pellam Cross",
      "Pellam Exchange",
      "Pellam Infirmary",
    ]);
    // No question is drawn, no place is offered to be pressed, and no field finds another.
    expect(document.body.textContent).not.toMatch(/Which (place|area) did you mean/);
    expect(screen.queryAllByRole("combobox")).toEqual([]);
    expect(status().join(" ")).not.toContain("Burro has a question about a place.");
    // One ranking, with the edit that was read and the first place in it.
    expect(api.callsTo("rank")).toHaveLength(1);
    const sent = (api.lastCallTo("rank").body as { operations: Operations }).operations;
    expect(sent.commute_ops).toEqual([{ ...asked.operations.commute_ops[0], place_id: first?.id }]);
    expect(results().length).toBeGreaterThan(0);
    // The refusal the question stood for is not said: the place is known now.
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
    // Nothing on the page repeats what was typed.
    expect(screen.getByRole("main").textContent).not.toMatch(/30 minutes to Pellam\b/);
  });

  test("test_the_chip_of_the_place_says_that_it_was_assumed_and_it_can_be_taken_off_or_changed", async () => {
    // No ranking was recorded of a journey to the first of them. The service answers as it
    // was recorded answering of the second, with the place that was sent in its place.
    const recorded = recordedAnswer("rank", "rank-nights-out");
    const toTheFirst = () => {
      const { data } = recorded.body;
      const [journey] = data.spec.commutes;
      if (!journey || !first) throw new Error("the recording holds no journey, or the question no place");
      return {
        ...recorded,
        body: {
          ...recorded.body,
          data: {
            ...data,
            spec: { ...data.spec, commutes: [{ ...journey, place_id: first.id }] },
            places: [{ place_id: first.id, name: first.name, kind: first.kind }],
          },
        },
      };
    };
    const { user, api } = await openSearch(
      firstSearch().on("interpret", "interpret-clarify").on("rank", toTheFirst).on("explain_top", "explanations-nights-out"),
    );
    await search(user, "Leafy, renting, 30 minutes to Pellam");

    const place = chipsSay().find((words) => words?.startsWith(first?.name ?? "no place"));
    expect(place?.startsWith(`${first?.name} ${CHIPS.assumed}`)).toBe(true);

    api.on("rank", "rank-first").on("explain_top", "explanations-first");
    await removeChip(user, first?.name ?? "");
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.placeRemove(first?.id ?? "") });
  });

  test("test_a_place_burro_does_not_know_is_left_out_and_said_in_a_line_with_nothing_to_press", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-clarify-no-options"));
    await search(user, sentenceOf("interpret-clarify-no-options"));

    expect(document.body.textContent).not.toMatch(/Which (place|area) did you mean/);
    // It is named in the one line of what was left out, with why one press away: said in a
    // line of its own under the chips it read "Burro does not know that place.", of nothing.
    const leftOut = screen.getByRole("status", { name: LEFT_OUT.title });
    expect(leftOut.querySelector("summary")?.textContent).toBe(`${LEFT_OUT.title}: ${LEFT_OUT.named_by_the_page.commute}`);
    expect(within(leftOut).getAllByRole("listitem").map((line) => line.textContent)).toEqual([
      `${LEFT_OUT.named_by_the_page.commute}. ${LEFT_OUT.why.place}`,
    ]);
    expect(leftOut.querySelectorAll("button, a, input")).toHaveLength(0);
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
    expect(document.body.textContent?.includes(REJECTED.unknown_place)).toBe(false);
    expect(screen.queryAllByRole("combobox")).toEqual([]);
    // The rest of the sentence is ranked, with no edit of a journey.
    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).not.toHaveProperty("operations");
    expect(results().length).toBeGreaterThan(0);
  });
});

describe("nothing matches", () => {
  async function nothingMatches() {
    const opened = await openSearch(firstSearch().on("interpret", "interpret-two-journeys").on("rank", "rank-nothing-matches"));
    await search(opened.user, "at most 10 minutes, no more than £400");
    await settled();
    return opened;
  }

  test("test_the_page_says_so_with_a_count_for_each_reason", async () => {
    await nothingMatches();

    const block = within(screen.getByRole("region", { name: NOTHING_MATCHES.title }));
    expect(block.getByText(FILTERED.over_budget).nextSibling).toHaveTextContent("21 areas");
    expect(block.getByText(FILTERED.commute_cap).nextSibling).toHaveTextContent("1 area");
    expect(block.getByText(UNRANKED.not_rankable).nextSibling).toHaveTextContent("2 areas");
    expect(status()).toContain(STATUS.nothingMatches);
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
  });

  test("test_there_is_one_button_for_each_firm_limit_and_it_sends_that_one_edit", async () => {
    const { user, api } = await nothingMatches();
    const block = within(screen.getByRole("region", { name: NOTHING_MATCHES.title }));

    expect(
      within(block.getByRole("list", { name: NOTHING_MATCHES.loosen }))
        .getAllByRole("button")
        .map((button) => button.textContent),
    ).toEqual([NOTHING_MATCHES.budgetFlexible, NOTHING_MATCHES.journeyFlexible("Cindermoor Works")]);

    api.on("rank", "rank-first");
    await user.click(block.getByRole("button", { name: NOTHING_MATCHES.budgetFlexible }));
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.budgetStrictness("soft") });
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_the_table_gives_each_area_its_reason_in_words", async () => {
    const { user } = await nothingMatches();
    const nothing = recordedAnswer("rank", "rank-nothing-matches").body.data;

    const table = within(await theTable(user));
    expect(screen.getByRole("table", { name: TABLE.caption })).toBeInTheDocument();
    for (const { area_id: areaId, reason } of nothing.filtered) {
      const row = table.getByRole("row", { name: new RegExp(`^${TABLE.noRank} ${nameOf(areaId)} `) });
      expect(row).toHaveTextContent(FILTERED[reason]);
    }
  });

  test("test_nothing_matches_has_no_accessibility_fault", async () => {
    const { container } = await nothingMatches();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

/**
 * The answer to a sentence of which no edit, no offer and no question came, and in which
 * these things were heard that Burro has no data on, with these words not read. It is the
 * recorded answer of a sentence nothing was read of, with `unmet` and `unread` as the
 * service gives them for such a sentence.
 */
const heardAndUnmet = (unmet: readonly UnmetCategory[], unread: readonly Span[]) => {
  const said = recordedAnswer("interpret", "interpret-nothing-read");
  const body = { ...said.body, data: { ...said.body.data, unmet, unread } };
  return () => responseFrom({ ...said, body });
};

describe("nothing read", () => {
  test("test_the_page_says_so_opens_the_settings_and_keeps_the_results_on_screen", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.calls.length = 0;
    api.on("interpret", "interpret-nothing-read");

    await user.clear(promptBox());
    await search(user, "What is the best way to learn the piano");

    expect(status()).toContain(NOTICE.nothingRead);
    // The settings do the same job, and the page opens the part that holds them.
    expect(settingsAreOpen()).toBe(true);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(api.calls.map((call) => call.operation)).toEqual(["interpret"]);
  });

  test("test_the_line_says_what_burro_can_read_so_that_a_person_knows_what_to_try", () => {
    // Seen in a browser: a sentence in Spanish was met with "Nothing in that could be read as
    // a setting", which led nowhere. Burro cannot tell one language from another. It can say
    // what it reads, and give a sentence that it does read.
    expect(NOTICE.nothingRead).toContain("plain English");
    // The sentence it gives is one the reader applies whole. It names no place.
    expect(NOTICE.nothingRead).toContain(`such as "${sentenceOf("interpret-plain-list")}".`);
    expect(recordedAnswer("interpret", "interpret-plain-list").body.data).toMatchObject({ status: "ok", unread: [] });
  });

  test("test_that_nothing_was_read_is_said_once_and_not_again_as_a_part_that_was_not", async () => {
    const unread = recordedAnswer("interpret", "interpret-nothing-read").body.data;
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-nothing-read"));

    await search(user, "What is the best way to learn the piano");

    // The API says `other` could not be met. With nothing read at all, the one line covers it.
    expect(unread.unmet).toEqual(["other"]);
    expect(status().filter((line) => line === NOTICE.nothingRead)).toHaveLength(1);
    expect(screen.queryByRole("region", { name: UNMET_LABEL })).toBeNull();
    expect(screen.queryByText(UNMET.other)).toBeNull();

    // Nor does it come up when the line goes.
    await settingsAt(user, groupOf("green"));
    slide("Leafy", 50);
    await settled();
    expect(status()).not.toContain(NOTICE.nothingRead);
    expect(screen.queryByText(UNMET.other)).toBeNull();
  });

  test("test_a_wish_burro_has_no_data_on_was_heard_and_is_not_said_to_be_unreadable", async () => {
    // Seen in a browser: "Burro could not read anything in what you typed" stood over "Burro
    // has no data on broadband, so it has left that out of your search", and both cannot be
    // so. The service says no word of "somewhere cheap" went unread.
    const { user, api } = await openSearch(
      firstSearch().on("interpret", heardAndUnmet(["affordability_verdict"], [])),
    );

    await search(user, "somewhere cheap");

    const unmet = within(screen.getByRole("region", { name: UNMET_LABEL }));
    expect(unmet.getAllByRole("listitem").map((line) => line.textContent)).toEqual([UNMET.affordability_verdict]);
    expect(status()).not.toContain(NOTICE.nothingRead);
    // Nothing is ranked of it, and the space requirements open as they do where nothing was read.
    expect(settingsAreOpen()).toBe(true);
    expect(api.callsTo("rank")).toEqual([]);
  });

  test("test_words_beside_such_a_wish_that_were_not_read_can_be_shown_in_the_box", async () => {
    // "fast broadband": broadband was heard, and "fast" was not read. Said by nobody, the
    // words that were not read would be lost with the line that nothing could be read.
    const { user } = await openSearch(
      firstSearch().on("interpret", heardAndUnmet(["broadband", "other"], [{ start: 0, end: 4 }])),
    );

    await search(user, "fast broadband");

    const unmet = within(screen.getByRole("region", { name: UNMET_LABEL }));
    expect(unmet.getAllByRole("listitem").map((line) => line.textContent)).toEqual([UNMET.broadband]);
    expect(status()).not.toContain(NOTICE.nothingRead);
    expect(screen.getByText(SUGGEST.unread)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: SUGGEST.showUnread }));
    expect([promptBox().selectionStart, promptBox().selectionEnd]).toEqual([0, 4]);
  });

  test("test_a_part_that_was_not_read_is_still_said_when_the_rest_was", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-unmet"));

    await search(user, sentenceOf("interpret-unmet"));

    const unmet = within(screen.getByRole("region", { name: UNMET_LABEL }));
    for (const category of recordedAnswer("interpret", "interpret-unmet").body.data.unmet) {
      expect(unmet.getByText(UNMET[category])).toBeInTheDocument();
    }
  });

  test("test_words_that_change_nothing_are_not_called_unreadable", async () => {
    const said = recordedAnswer("interpret", "interpret-clarify");
    const body = {
      ...said.body,
      data: {
        ...said.body.data,
        status: "ok",
        clarify: [],
        rejected: [],
        operations: { ...said.body.data.operations, commute_ops: [], tag_ops: [] },
        applied: [{ group: "budget_ops", index: 0, changed: false }],
        spec: meta.data.defaults.rent,
      },
    };
    const { user } = await openSearch(firstSearch().on("interpret", () => responseFrom({ ...said, body })));

    await user.type(promptBox(), "renting");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    await waitFor(() => expect(status()).toContain(NOTICE.nothingChanged));
    expect(status()).not.toContain(NOTICE.nothingRead);
  });

  test("test_a_sentence_that_is_off_the_subject_gets_the_apis_own_words_once", async () => {
    // A model can tell a sentence that is about something else. The rules cannot. This is
    // recorded from the service with a stand-in for the model that answers "off the subject".
    const unread = recordedAnswer("interpret", "interpret-off-topic").body.data;
    const words = unread.notice_text;
    expect(unread).toMatchObject({ status: "off_topic", notice: "off_topic", interpreter: "model" });
    expect(words).not.toBe("");
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-off-topic"));

    await user.type(promptBox(), "piano");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(settingsAreOpen()).toBe(true));

    expect(status().filter((line) => line === words)).toHaveLength(1);
    expect(status()).not.toContain(NOTICE.nothingRead);
    expect(api.callsTo("rank")).toEqual([]);
  });

  test("test_the_line_goes_once_a_control_is_used", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-nothing-read"));
    await user.type(promptBox(), "piano");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(NOTICE.nothingRead));

    await settingsAt(user, groupOf("green"));
    slide("Leafy", 50);
    await settled();

    expect(status()).not.toContain(NOTICE.nothingRead);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });
});

describe("degraded to a form", () => {
  test("test_when_the_rules_read_the_words_the_page_says_so_and_shows_their_results", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-degraded"));
    await search(user);
    await settled();

    expect(status()).toContain(NOTICE.degraded);
    expect(settingsAreOpen()).toBe(true);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("test_when_the_language_model_would_not_read_the_words_one_line_says_so_and_that_the_rules_have", async () => {
    const refused = recordedAnswer("interpret", "interpret-refused").body.data;
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-refused"));
    await search(user);
    await settled();

    expect([refused.model_refused, refused.degraded, refused.interpreter]).toEqual([true, true, "rule"]);
    expect(status()).toContain(NOTICE.refused);
    expect(status()).not.toContain(NOTICE.degraded);
    // The rules read the words as they would with no model, so their results show as usual.
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("test_words_the_rules_read_for_any_other_reason_are_not_said_to_have_been_refused", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-degraded"));
    await search(user);
    await settled();

    expect(status()).toContain(NOTICE.degraded);
    expect(status()).not.toContain(NOTICE.refused);
  });

  test("test_words_that_nothing_read_are_not_said_to_have_been_refused", async () => {
    // Found by reading the page's code: the reading before is still held when a read fails,
    // so a sentence that nothing read was said to have been refused by the language model.
    const api = firstSearch().on("interpret", "interpret-refused");
    const { user } = await openSearch(api);
    await search(user);
    await settled();
    expect(status()).toContain(NOTICE.refused);
    api.on("interpret", "error-internal");

    await user.clear(promptBox());
    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(NOTICE.degraded));

    expect(status()).not.toContain(NOTICE.refused);
    expect(screen.getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();
  });

  test("test_when_reading_takes_too_long_the_page_names_the_second_way_in_and_the_settings_still_work", async () => {
    const api = firstSearch().silent("interpret");
    const { user } = await openSearch(api);
    jest.useFakeTimers();

    fireEvent.input(promptBox(), { target: { value: "leafy and quiet" } });
    fireEvent.click(screen.getByRole("button", { name: PROMPT.submit }));
    await act(() => jest.advanceTimersByTimeAsync(8_000));
    jest.useRealTimers();

    // No search is open, so the two ways in are there. The settings do the same job, and
    // they stand in the second: the line names it. The page chooses no tab for the person,
    // which would hide the box, their words and the way to try them again.
    expect(status()).toContain(UNREAD.before);
    expect(UNREAD.before).toContain(WAYS.deep);
    expect(status()).not.toContain(NOTICE.degraded);
    expect(waysAre()).toEqual(THE_FIRST_WAY_CHOSEN);
    expect(helpersAre()).toEqual(EVERY_HELPER_CLOSED);
    expect(theSettingsIfAny()).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(promptBox()).toHaveValue("leafy and quiet");
    expect(promptBox()).toBeVisible();
    expect(screen.getByRole("button", { name: PROMPT.tryAgain })).toBeVisible();

    // The same controls work as a form, with no words read at all: what is chosen in the
    // second way in is kept, and its button makes the search of it.
    await settingsAt(user, groupOf("green"));
    slide("Leafy", 50);
    await settled();
    expect(api.lastCallTo("rank").body).toEqual({
      spec: meta.data.defaults.rent,
      operations: edits.tagWeight("leafy", 0.5, "high"),
      limit: 1,
    });
    await rankTheSettings(user);
    expect(api.lastCallTo("rank").body).toEqual({ spec: first.rank.spec, limit: 20 });
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });

  // A request that cannot leave is another thing: the settings could not reach Burro either.
  // `test/search/walked.test.tsx` holds what the page says then.
  test.each([
    ["the service has a fault", "error-internal"],
    ["the answer is not the api's", "not-the-apis"],
  ] as const)("test_the_form_works_when_interpretation_fails: %s", async (_, how) => {
    const api = firstSearch();
    if (how === "not-the-apis") api.on("interpret", () => new Response("<html>"));
    else api.on("interpret", how);
    const { user } = await openSearch(api);

    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(UNREAD.before));

    // The first way stays chosen, with the words in the box, and the second holds the settings.
    expect(waysAre()).toEqual(THE_FIRST_WAY_CHOSEN);
    expect(theSettingsIfAny()).toBeNull();
    await settingsAt(user, SETTINGS.money);
    const budget = within(screen.getByRole("group", { name: BUDGET.legend }));
    await user.type(budget.getByRole("textbox", { name: BUDGET.amount.rent }), "1700{Enter}");
    await settled();
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.budgetAmount(1700), limit: 1 });
    await rankTheSettings(user);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_try_again_sends_the_same_text_from_the_box", async () => {
    const api = firstSearch().on("interpret", "error-internal");
    const { user } = await openSearch(api);
    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(UNREAD.before));
    api.on("interpret", "interpret-first");

    await user.click(screen.getByRole("button", { name: PROMPT.tryAgain }));
    await settled();

    expect(api.callsTo("interpret").map((call) => (call.body as { text: string }).text)).toEqual([
      "leafy and quiet",
      "leafy and quiet",
    ]);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    for (const gone of [UNREAD.before, NOTICE.degraded]) expect(status()).not.toContain(gone);
  });

  test("test_in_the_second_way_in_that_words_were_not_read_is_said_in_sight_and_they_can_be_tried_again_from_there", async () => {
    // What Burro says of a search stands in the box, which is in the first way in. A person
    // who goes to the settings, as the line tells them they may, is told the same where
    // they are, with the way to try the words again beside it: over the button that makes
    // a search of that way, which is held in sight wherever they are among the groups.
    const api = firstSearch().on("interpret", "error-internal");
    const { user } = await openSearch(api);
    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(UNREAD.before));

    await way(user, "deep");

    expect(status().filter((line) => line === UNREAD.before)).toHaveLength(1);
    const said = screen.getByText(UNREAD.before);
    expect(panelOf("deep")).toContainElement(said);
    expect(said).toBeVisible();
    const again = screen.getByRole("button", { name: PROMPT.tryAgain });
    expect(panelOf("deep")).toContainElement(again);
    // It stands with the button of the way, over it, and after the settings in the page.
    const before = (one: Element, other: Element) =>
      Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);
    const makes = within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank });
    expect(makes.parentElement).toContainElement(again);
    expect(before(again, makes)).toBe(true);
    expect(before(theSettings(), again)).toBe(true);

    api.on("interpret", "interpret-first");
    await user.click(again);
    await settled();

    // The words are in the box still, though it was not in sight, and are sent as they were.
    expect(api.callsTo("interpret").map((call) => (call.body as { text: string }).text)).toEqual([
      "leafy and quiet",
      "leafy and quiet",
    ]);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(promptBox()).toHaveValue("leafy and quiet");
    expect(promptBox()).toBeVisible();
    // The button went with the line it stood beside. The focus is on Search, and never on nothing.
    expect(screen.getByRole("button", { name: PROMPT.submit })).toHaveFocus();
  });

  test("test_the_degraded_form_has_no_accessibility_fault", async () => {
    const { user, container } = await openSearch(firstSearch().on("interpret", "error-internal"));
    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(UNREAD.before));

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    // Nor where the line stands at the head of the second way in, over the settings.
    await way(user, "deep");
    expect(panelOf("deep")).toContainElement(screen.getByText(UNREAD.before));
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("the neutral notice", () => {
  const notice = recordedAnswer("interpret", "interpret-notice").body.data;

  test("test_the_apis_one_sentence_is_shown_word_for_word_and_the_rest_is_served", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-notice"));
    await search(user, "Quiet and leafy, 30 minutes to work");

    const block = screen.getByRole("status", { name: NOTICE.label });
    expect(block.textContent).toBe(notice.notice_text);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_nothing_on_the_page_says_what_was_left_out", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-notice"));
    await search(user, "Quiet and leafy, not too many students, 30 minutes to work");
    await settled();

    const page = document.querySelector("main")?.textContent ?? "";
    expect(page.replace(promptBox().value, "")).not.toMatch(/student/i);
    expect(screen.queryByRole("region", { name: UNMET_LABEL })).toBeNull();
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(status()).not.toContain(NOTICE.nothingRead);
  });

  test("test_the_notice_stays_while_controls_are_used_and_goes_with_the_next_sentence", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-notice"));
    await search(user, "Quiet and leafy");
    await settled();

    await removeChip(user, "Leafy");
    await settled();
    expect(screen.getByRole("status", { name: NOTICE.label })).toBeInTheDocument();

    api.on("interpret", "interpret-second-sentence");
    await search(user, " and more green space");
    await settled();
    expect(screen.queryByRole("status", { name: NOTICE.label })).toBeNull();
  });
});

describe("an error from the API", () => {
  test.each([
    ["not-found", "an address that is no route, as a wrong setting of the API's address gives"],
    ["rank-invalid-operations", "a request the API will not take"],
  ])("test_a_sentence_the_api_refuses_for_anything_but_its_words_is_never_met_with_silence: %s", async (scenario) => {
    const refused = recordedError(scenario);
    const { user } = await openSearch(firstSearch().on("interpret", scenario));

    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    const alert = await screen.findByRole("alert");
    expect(refused.status).toBeLessThan(500);
    expect(alert).toHaveTextContent(refused.body.error.message);
    expect(alert).toHaveTextContent(refused.headers["x-request-id"] ?? "no id");
    expect(within(alert).getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();
    // It is not said to be words that could not be read: the API did not get as far as reading.
    expect(status()).not.toContain(NOTICE.degraded);
    expect(promptBox()).toHaveValue("leafy and quiet");
  });

  test("test_a_refusal_of_the_text_is_said_under_the_box_in_the_apis_words", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-invalid-text"));
    const refusal = recordedError("interpret-invalid-text").body.error.message;

    await user.type(promptBox(), "x");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(await screen.findByRole("alert")).toHaveTextContent(refusal);
    expect(promptBox()).toHaveAccessibleDescription(expect.stringContaining(refusal));
    expect(promptBox()).toHaveAttribute("aria-invalid", "true");
    expect(status()).not.toContain(NOTICE.degraded);
  });

  test("test_a_fault_keeps_the_last_results_marked_not_updated_with_the_id_to_quote", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "error-internal");
    const fault = recordedError("error-internal");

    await removeChip(user, "Leafy");
    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent(fault.body.error.message);
    expect(alert).toHaveTextContent(NOTICE.notUpdated);
    expect(alert).toHaveTextContent(fault.headers["x-request-id"] ?? "no id");
    expect(results()).toHaveLength(SHOWN_AT_FIRST);

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await user.click(within(alert).getByRole("button", { name: PROMPT.tryAgain }));
    await settled();
    expect(screen.queryByRole("alert")).toBeNull();
    // The edit that failed was kept, and sent again.
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.tagOff("leafy") });
  });

  test("test_a_search_that_names_something_gone_offers_the_edit_that_takes_it_out", async () => {
    const stale = recordedAnswer("rank", "rank-stale-spec-repaired").request.body as {
      spec: typeof first.rank.spec;
    };
    const read = recordedAnswer("interpret", "interpret-first");
    const holdingAGonePlace = { ...read, body: { ...read.body, data: { ...read.body.data, spec: stale.spec } } };
    const { user, api } = await openSearch(
      firstSearch()
        .on("interpret", () => responseFrom(holdingAGonePlace))
        .on("rank", "rank-stale-spec"),
    );

    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent(NOTICE.stale);
    api
      .on("rank", "rank-stale-spec-repaired")
      .on("explain_top", reasonsFor("rank-stale-spec-repaired", "explanations-first"));
    // The place is gone from the data, so no answer names it. It is spoken of as the place.
    await user.click(within(alert).getByRole("button", { name: NOTICE.takeOut(NOTICE.thePlace) }));
    await settled();

    expect(api.lastCallTo("rank").body).toEqual(recordedAnswer("rank", "rank-stale-spec-repaired").request.body && {
      spec: stale.spec,
      operations: edits.placeRemove("syn-p9999"),
      limit: 20,
    });
    expect(screen.queryByRole("alert")).toBeNull();
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_start_again_returns_to_the_page_as_it_first_stood", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "error-internal");
    await removeChip(user, "Leafy");

    await user.click(within(await screen.findByRole("alert")).getByRole("button", { name: PROMPT.startAgain }));

    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    // Nothing is understood of anything: the two ways in are back with the first chosen,
    // its helpers each closed, and the box asks for a search.
    expect(screen.queryByRole("region", { name: CHIPS.label })).toBeNull();
    expect(waysAre()).toEqual(THE_FIRST_WAY_CHOSEN);
    expect(helpersAre()).toEqual(EVERY_HELPER_CLOSED);
    expect(whatRefines()).toBeNull();
    expect(promptBox()).toHaveAccessibleName(PROMPT.label);
  });

  test("test_reasons_that_cannot_be_loaded_are_said_on_the_card_and_the_ranking_stays", async () => {
    const { user } = await openSearch(firstSearch().on("explain_top", "error-internal"));
    await search(user);
    await settled();
    const fault = recordedError("error-internal");

    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    // A card says what it lacks where it would stand: under "Trade-off", which is what a
    // card says of what Burro wrote, that the trade-off could not be loaded.
    const card = results()[0] as HTMLElement;
    const under = (heading: string) =>
      within(within(card).getByRole("heading", { name: heading }).parentElement as HTMLElement);
    expect(under(RESULTS.tradeOffTitle).getByText(CARD.tradeOffFailed)).toBeInTheDocument();
    // Why they could not be loaded is never met with silence: the API's words, the id to
    // quote and "Try again". The results themselves were updated, and are not said not to be.
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(fault.body.error.message);
    expect(alert).toHaveTextContent(fault.headers["x-request-id"] ?? "no id");
    expect(alert).not.toHaveTextContent(NOTICE.notUpdated);
    expect(within(alert).getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();
    // The reasons stand in the working of a card, and the working says that they could not
    // be loaded, under "Why it fits". Nothing of it is left waiting.
    await workingOf(user, nameOf(first.rank.ranked[0]?.area_id ?? ""));
    expect(under(RESULTS.reasonsTitle).getByText(RESULTS.reasonsFailed)).toBeInTheDocument();
    expect(card.querySelectorAll(".skeleton")).toHaveLength(0);
  });

  test("test_the_error_state_has_no_accessibility_fault", async () => {
    const { user, api, container } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "error-internal");
    await removeChip(user, "Leafy");
    await screen.findByRole("alert");

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("offline", () => {
  test("test_the_page_says_so_keeps_the_results_and_sends_the_edit_once_when_back", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.calls.length = 0;

    setOnline(false);
    act(() => void window.dispatchEvent(new Event("offline")));
    expect(status()).toContain(NOTICE.offline);

    await removeChip(user, "Leafy");
    await waitFor(() => expect(status()).toContain(`${NOTICE.offline} ${NOTICE.offlineWaiting}`));
    expect(api.calls).toEqual([]);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(screen.queryByRole("alert")).toBeNull();

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    setOnline(true);
    act(() => void window.dispatchEvent(new Event("online")));
    await settled();

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.tagOff("leafy") });
    expect(status().join(" ")).not.toContain(NOTICE.offline);
  });
});

describe("the map, where it cannot be drawn", () => {
  test("test_the_table_stands_in_for_the_map_with_a_line_saying_why", async () => {
    const { user } = await openSearch();
    await search(user);

    expect(status()).toContain(MAP.noWebGL);
    // It is one press away, as it is where the map can be drawn, so that the answer comes first.
    await theTable(user);
    expect(screen.getByRole("table", { name: TABLE.caption })).toBeInTheDocument();
  });
});
