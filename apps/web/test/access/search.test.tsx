/**
 * The search page, held to docs/design/web.md section 9: everything works by
 * keyboard, colour is never the only signal, every map has its table, a
 * slider never needs dragging, and each state is said once.
 *
 * axe runs here in jsdom and cannot judge contrast, size or layout. Those
 * are in test/tokens.test.ts and in a browser, by hand.
 */

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";

import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { HELPERS } from "@/content/helpers";
import { MAP, MAP_CARD, TABLE } from "@/content/map";
import {
  APART,
  BREAKDOWN,
  CHIPS,
  COMPLETENESS,
  CONFIDENCE,
  COST,
  FIND_AREA,
  JOURNEYS,
  LEFT_OUT,
  NOTHING_MATCHES,
  NOTICE,
  PLACE,
  PROMPT,
  RESULTS,
  SEARCH,
  SHELF,
  SOURCE,
  STATUS,
  SUGGEST,
  TENURE_CHOICE,
  UNRANKED,
} from "@/content/search";
import { BUDGET, FEATURES, JOURNEY, SETTINGS, SLIDER } from "@/content/settings";
import { UNREAD, WAY_IDS, WAYS } from "@/content/ways";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { setOnline } from "../support/api";
import { faultsIn } from "../support/axe";
import { lastMap } from "../support/maplibre";
import {
  areas,
  arrived,
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
  saidIn,
  search,
  settingsAt,
  settled,
  setWebGL,
  tabOf,
  theSettings,
  theLine,
  theSettingsIfAny,
  theTable,
  theWholeOfIt,
  way,
  waysIfAny,
  whatRefines,
  workingOf,
} from "../support/search";
import { focusGoesOnlyToWhatIsDrawn } from "./drawn";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

/** The group of the settings that holds a family of vibes, by the name the service gives the family. */
const groupOf = (family: string) => meta.data.families.find((one) => one.family === family)?.label ?? "";

const first = recordedAnswer("rank", "rank-first").body.data;
const refined = recordedAnswer("rank", "rank-refined").body.data;
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";
const sentEdits = (body: unknown) => (body as { operations: Operations }).operations;

beforeEach(() => {
  setOnline(true);
  focusGoesOnlyToWhatIsDrawn();
});
afterEach(() => setWebGL(false));

async function searched(api = firstSearch()) {
  const opened = await openSearch(api);
  await search(opened.user);
  return opened;
}

/** Presses Tab until the focus is on the element, and says how many presses it took. */
async function tabTo(user: Awaited<ReturnType<typeof openSearch>>["user"], wanted: () => Element | null) {
  for (let presses = 0; presses < 400; presses += 1) {
    if (document.activeElement !== null && document.activeElement === wanted()) return presses;
    await user.tab();
  }
  throw new Error("Tab never reached it.");
}

/** The list a field that finds a place names as its own. What it found is in it, and nothing else is. */
const listOf = (field: HTMLElement) => document.getElementById(field.getAttribute("aria-controls") ?? "") as HTMLElement;

describe("the keyboard", () => {
  test("test_a_search_can_be_made_and_refined_by_keyboard_alone", async () => {
    const { user, api } = await openSearch();

    // Make a search: reach the box, type, press Enter.
    await tabTo(user, promptBox);
    await user.keyboard("leafy and quiet{Enter}");
    await settled();
    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);

    // Refine it: open the part that refines the search, go to the group of the journeys,
    // reach a checkbox, press Space.
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await tabTo(user, whatRefines);
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
    await user.keyboard("{Enter}");
    expect(whatRefines()).toHaveAttribute("aria-expanded", "true");
    expect(whatRefines()).toHaveFocus();
    // The bar of each group says whether it stands open, and which do at first is the
    // settings' to choose. Whoever hears that the group of the journeys is closed presses
    // its bar, and whoever hears that it is open goes on into it: a press would close it.
    const journeys = () => within(theSettings()).getByRole("button", { name: SETTINGS.journeys });
    await tabTo(user, journeys);
    if (journeys().getAttribute("aria-expanded") === "false") await user.keyboard("{Enter}");
    expect(journeys()).toHaveAttribute("aria-expanded", "true");
    expect(journeys()).toHaveFocus();
    await tabTo(user, () => screen.queryAllByRole("checkbox", { name: JOURNEY.firm })[0] ?? null);
    await user.keyboard(" ");
    await settled();
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeStrictness("syn-p0021", "hard"));
    // Every area that is still ranked is listed, and no button is left that would show more.
    expect(results()).toHaveLength(refined.ranked.length);
    expect(screen.queryByRole("button", { name: /^Show \d+ more$/ })).toBeNull();

    // Open the working of a result: reach "Show the working", press Enter, close it with Escape.
    const working = () => within(results()[1] as HTMLElement).getByRole("button", { name: /^Show the working: / });
    await tabTo(user, working);
    await user.keyboard("{Enter}");
    expect(working()).toHaveAttribute("aria-expanded", "true");
    await user.keyboard("{Escape}");
    expect(working()).toHaveAttribute("aria-expanded", "false");
    expect(working()).toHaveFocus();

    // Read a source. No key of a source stands on a result until its working is opened: so
    // reach "Show the working" of the first card and press Enter, reach the first "Source"
    // of its working, open it, and close it with Escape, which leaves the working open.
    const card = () => within(results()[0] as HTMLElement);
    const opens = () => card().getByRole("button", { name: /^Show the working: / });
    const source = () => card().queryAllByRole("button", { name: /^Source/ })[0] ?? null;
    expect(source()).toBeNull();
    await tabTo(user, opens);
    await user.keyboard("{Enter}");
    expect(opens()).toHaveAttribute("aria-expanded", "true");
    // The working follows what opened it, with nothing between them but the other way on.
    expect(await tabTo(user, source)).toBe(2);
    await user.keyboard("{Enter}");
    expect(source()).toHaveAttribute("aria-expanded", "true");
    expect(card().getByText(SOURCE.madeUp)).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(source()).toHaveAttribute("aria-expanded", "false");
    expect(source()).toHaveFocus();
    expect(opens()).toHaveAttribute("aria-expanded", "true");
  });

  test("test_the_rest_of_the_list_can_be_shown_by_keyboard_alone", async () => {
    const { user } = await searched();
    expect(results()).toHaveLength(SHOWN_AT_FIRST);

    // Reach "Show 10 more", press Enter. The focus goes to the list it added to.
    await tabTo(user, () => screen.queryByRole("button", { name: RESULTS.showMore(10) }));
    await user.keyboard("{Enter}");

    expect(results()).toHaveLength(first.ranked.length);
    // The focus goes to the part of the list that the button added to: the rest, from the second.
    expect(screen.getByRole("list", { name: RESULTS.restLabel }) === document.activeElement).toBe(true);
    // The areas that are not ranked open with Enter and close with Escape, which puts the focus back.
    const apart = screen.getByRole("button", { name: APART.title(first.unranked.length) });
    act(() => apart.focus());
    await user.keyboard("{Enter}");
    expect(apart).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("list", { name: APART.label })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(apart).toHaveAttribute("aria-expanded", "false");
    expect(apart).toHaveFocus();
  });

  test("test_a_helper_is_opened_and_closed_by_keyboard_alone_and_the_focus_is_never_left_on_nothing", async () => {
    const { user, api } = await openSearch();
    api.calls.length = 0;
    const held = (name: string) => within(helpers()).getByRole("button", { name });

    // The helpers are the next stops after the box and Search: nothing stands between them.
    await tabTo(user, promptBox);
    const presses = await tabTo(user, () => held(HELPERS.example));
    expect(presses).toBe(2);

    // Enter opens one, and Space another: each is a button. The one that was open closes.
    await user.keyboard("{Enter}");
    expect(held(HELPERS.example)).toHaveAttribute("aria-expanded", "true");
    expect(held(HELPERS.example)).toHaveFocus();
    await user.tab();
    await user.keyboard(" ");
    expect(held(HELPERS.word)).toHaveAttribute("aria-expanded", "true");
    expect(held(HELPERS.example)).toHaveAttribute("aria-expanded", "false");
    expect(held(HELPERS.word)).toHaveFocus();

    // What it opened is reached with Tab, after the last helper of the line, which this one is.
    expect(within(helpers()).getAllByRole("button").at(-1)).toBe(held(HELPERS.word));
    await user.tab();
    const shelf = screen.getByRole("region", { name: SHELF.title });
    expect(shelf).toContainElement(document.activeElement as HTMLElement);

    // Escape closes the helper from inside what it holds, and the focus goes back to its button.
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(held(HELPERS.word)).toHaveAttribute("aria-expanded", "false");
    expect(held(HELPERS.word)).toHaveFocus();
    expect(api.calls).toEqual([]);
  });

  test("test_an_example_is_reached_and_used_by_keyboard_alone_and_the_focus_goes_to_the_box", async () => {
    const { user, api } = await openSearch();
    api.calls.length = 0;

    await tabTo(user, () => within(helpers()).getByRole("button", { name: HELPERS.example }));
    await user.keyboard("{Enter}");
    await tabTo(user, () => screen.getByRole("button", { name: /^Buying a terraced house/ }));
    await user.keyboard("{Enter}");

    expect(promptBox().value).toMatch(/^Buying a terraced house/);
    expect(promptBox()).toHaveFocus();
    expect(api.calls).toEqual([]);
  });

  test("test_a_place_can_be_found_and_picked_by_keyboard_alone", async () => {
    const { user, api } = await openSearch(
      firstSearch().on("rank", "rank-default-rent").on("explain_top", "explanations-first"),
    );

    // The field is in the second way in, among its settings, under the journeys: reach the
    // tab that is chosen, go to the other with an arrow key, which chooses it, and go on
    // into its panel to the field.
    await tabTo(user, () => tabOf("quick"));
    await user.keyboard("{ArrowRight}");
    expect(tabOf("deep")).toHaveFocus();
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });
    const presses = await tabTo(user, () => field);
    // The money stands open over it, with all it holds. It is reached all the same, by Tab alone.
    expect(presses).toBeLessThan(30);
    await user.keyboard("pel");
    const options = await within(listOf(field)).findAllByRole("option");
    expect(field).toHaveAttribute("aria-expanded", "true");
    expect(options.map((option) => option.textContent)).toEqual([
      "Pellam CrossStation",
      "Pellam ExchangeDistrict",
      "Pellam InfirmaryHospital, in Coracle Row",
    ]);

    await user.keyboard("{ArrowDown}{ArrowDown}");
    expect(field).toHaveAttribute("aria-activedescendant", options[1]?.id);
    expect(options[1]).toHaveAttribute("aria-selected", "true");
    await user.keyboard("{ArrowUp}{ArrowUp}");
    expect(options[2]).toHaveAttribute("aria-selected", "true");
    await user.keyboard("{Home}{Enter}");
    await settled();

    // What is chosen in the second way in is kept until its button makes the search: the
    // place was sent to be applied, no search opened, and the focus is in the field still.
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeAdd("syn-p0012"));
    expect((api.lastCallTo("rank").body as { limit: number }).limit).toBe(1);
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    expect(field).toBeInTheDocument();
    expect(field).toHaveFocus();
    expect(document.activeElement).not.toBe(document.body);

    // The button that makes the search is reached by Tab, and pressed by Enter. The two
    // ways in go as the search opens, and the focus is on what opens the settings.
    await tabTo(user, () => within(panelOf("deep")).queryByRole("button", { name: SETTINGS.rank }));
    await user.keyboard("{Enter}");
    await settled();
    expect(waysIfAny()).toBeNull();
    expect(screen.queryByRole("group", { name: HELPERS.label })).toBeNull();
    expect(results().length).toBeGreaterThan(0);
    expect(document.activeElement).not.toBe(document.body);
    expect(whatRefines()).toHaveFocus();
  });

  test("test_a_place_picked_from_the_settings_leaves_the_focus_in_its_field", async () => {
    const { user, api } = await searched();
    await settingsAt(user, SETTINGS.journeys);
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });

    await user.type(field, "pel");
    // The places the field found, in the list it names: a group that stands open beside it
    // holds a list of kinds of home, whose choices are options too.
    await within(listOf(field)).findAllByRole("option");
    await user.keyboard("{Home}{Enter}");
    await settled();

    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeAdd("syn-p0012"));
    expect(field).toHaveValue("");
    expect(field).toHaveFocus();
    expect(field).toHaveAttribute("aria-expanded", "false");
  });

  test("test_a_vibe_added_from_the_shelf_leaves_the_focus_on_what_was_understood", async () => {
    const { user, api } = await openSearch(firstSearch().on("rank", "rank-shelf").on("explain_top", "explanations-shelf"));

    // The shelf is behind a helper: reach it, press Enter, and go on to the first word.
    await tabTo(user, () => within(helpers()).getByRole("button", { name: HELPERS.word }));
    await user.keyboard("{Enter}");
    const shelf = within(screen.getByRole("region", { name: SHELF.title }));
    await tabTo(user, () => shelf.getAllByRole("button")[0] ?? null);
    await user.keyboard("{Enter}");
    await tabTo(user, () => screen.queryByRole("button", { name: /^Add to my search/ }));
    await user.keyboard("{Enter}");
    await settled();

    expect(api.lastCallTo("rank").body).toEqual(recordedAnswer("rank", "rank-shelf").request.body);
    // The shelf was for a first search, and has gone with the helpers and the two ways in.
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(screen.queryByRole("group", { name: HELPERS.label })).toBeNull();
    expect(waysIfAny()).toBeNull();
    expect(screen.getByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel})$`) })).toHaveFocus();
  });

  test("test_escape_closes_the_list_of_places_and_keeps_what_was_typed", async () => {
    const { user } = await openSearch();
    await way(user, "deep");
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });
    const open = within(theSettings())
      .getAllByRole("button", { expanded: true })
      .map((bar) => bar.getAttribute("aria-controls"));

    await user.type(field, "pel");
    await within(listOf(field)).findAllByRole("option");
    await user.keyboard("{Escape}");

    expect(field).toHaveAttribute("aria-expanded", "false");
    expect(within(listOf(field)).queryAllByRole("option")).toEqual([]);
    expect(field).toHaveValue("pel");
    // The list closed, and what holds the field did not: the innermost thing that is open
    // closes. The way in that holds the field is chosen still, and its panel is drawn, with
    // every group of the settings as it stood.
    expect(field).toHaveFocus();
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    expect(panelOf("deep")).toBeVisible();
    expect(open.length).toBeGreaterThan(0);
    expect(
      within(theSettings())
        .getAllByRole("button", { expanded: true })
        .map((bar) => bar.getAttribute("aria-controls")),
    ).toEqual(open);
  });

  test("test_escape_closes_the_card_of_a_word_before_the_helper_that_holds_the_shelf", async () => {
    const { user } = await openSearch();
    await helper(user, "word");
    const word = within(screen.getByRole("region", { name: SHELF.title })).getAllByRole("button")[0] as HTMLElement;
    await user.click(word);
    expect(word).toHaveAttribute("aria-expanded", "true");

    await user.keyboard("{Escape}");
    expect(word).toHaveAttribute("aria-expanded", "false");
    expect(word).toHaveFocus();
    expect(screen.getByRole("button", { name: HELPERS.word })).toHaveAttribute("aria-expanded", "true");

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(screen.getByRole("button", { name: HELPERS.word })).toHaveFocus();
  });

  test.each(["example", "word"] as const)(
    "test_escape_from_the_last_thing_a_helper_holds_closes_the_helper_as_it_does_from_the_first: %s",
    async (which) => {
      // Seen in a browser, by keyboard: from the last thing the last helper opened, which was
      // the way to the settings, Escape did nothing, where from the field beside it it closed
      // the helper. The settings stand in the second way in since. What a helper opens ends
      // at an example or at a word of the shelf, and Escape closes the helper from there.
      const { user } = await openSearch();
      const button = () => within(helpers()).getByRole("button", { name: HELPERS[which] });
      const stops = () =>
        [
          ...(document.getElementById(button().getAttribute("aria-controls") ?? "") as HTMLElement).querySelectorAll<HTMLElement>(
            "a[href], button, input, select, textarea",
          ),
        ];

      for (const at of [0, -1]) {
        await helper(user, which);
        expect(stops().length).toBeGreaterThan(1);
        await tabTo(user, () => stops().at(at) ?? null);

        await user.keyboard("{Escape}");

        expect(button()).toHaveAttribute("aria-expanded", "false");
        expect(button()).toHaveFocus();
        expect(stops()).toEqual([]);
      }
    },
  );

  test("test_before_a_search_escape_closes_a_group_of_the_settings_and_nothing_else_for_nothing_holds_them", async () => {
    // A helper held the settings, and Escape closed the group that was open, then the
    // settings, then the helper: the innermost first. They stand open in the second way in
    // since, under no button, and nothing holds them that Escape could close.
    const { user } = await openSearch();
    await settingsAt(user, SETTINGS.money);
    const money = within(theSettings()).getByRole("button", { name: SETTINGS.money });
    const tenure = within(within(theSettings()).getByRole("group", { name: TENURE_CHOICE.legend }));
    await user.click(tenure.getByRole("radio", { name: TENURE_CHOICE.buy }));

    // The group that is open closes, and its bar has the focus.
    await user.keyboard("{Escape}");
    expect(money).toHaveAttribute("aria-expanded", "false");
    expect(money).toHaveFocus();
    // A second closes nothing: the settings stand, their way in is chosen still, and the
    // focus is where it was, never on nothing.
    await user.keyboard("{Escape}");
    expect(theSettings()).toBeVisible();
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    expect(panelOf("deep")).toBeVisible();
    expect(money).toHaveFocus();
    expect(whatRefines()).toBeNull();
  });

  test("test_once_a_search_is_open_escape_closes_a_group_and_then_the_part_that_refines_the_search", async () => {
    const { user, api } = await searched();
    await settingsAt(user, SETTINGS.money);
    const sent = api.calls.length;
    const money = within(theSettings()).getByRole("button", { name: SETTINGS.money });
    await tabTo(user, () => within(theSettings()).getByRole("radio", { name: TENURE_CHOICE.rent }));

    // The innermost thing that is open closes first, and what opened it has the focus.
    await user.keyboard("{Escape}");
    expect(money).toHaveAttribute("aria-expanded", "false");
    expect(money).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
    expect(whatRefines()).toHaveFocus();
    expect(theSettingsIfAny()).toBeNull();
    // Nothing is left to close, and the answer stands as it stood.
    await user.keyboard("{Escape}");
    expect(whatRefines()).toHaveFocus();
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(api.calls).toHaveLength(sent);
  });

  test("test_once_a_search_is_open_escape_from_the_way_to_the_settings_moves_nothing", async () => {
    const { user } = await searched();
    const refine = whatRefines() as HTMLElement;
    act(() => refine.focus());

    await user.keyboard("{Escape}");

    expect(refine).toHaveFocus();
    expect(refine).toHaveAttribute("aria-expanded", "false");
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_the_other_way_chosen_from_inside_the_settings_leaves_the_focus_on_its_tab_and_keeps_what_was_chosen", async () => {
    // A helper held the settings, and another helper pressed while the focus was in them
    // closed them and took the focus. A way in holds them since: the other is chosen while
    // the focus is in them, and they go from sight with what had the focus.
    const { user, api } = await openSearch();
    await settingsAt(user, SETTINGS.money, SETTINGS.airAndNoise);
    const tenure = within(within(theSettings()).getByRole("group", { name: TENURE_CHOICE.legend }));
    await user.click(tenure.getByRole("radio", { name: TENURE_CHOICE.buy }));
    expect(theSettings()).toContainElement(document.activeElement as HTMLElement);

    await user.click(tabOf("quick"));

    expect(panelOf("deep")).not.toBeVisible();
    expect(theSettingsIfAny()).toBeNull();
    expect(tabOf("quick")).toHaveFocus();
    expect(document.body).not.toHaveFocus();
    // Chosen again, the settings are as they were left, and hold what was chosen.
    await way(user, "deep");
    const bar = (name: string) => within(theSettings()).getByRole("button", { name });
    expect(bar(SETTINGS.money)).toHaveAttribute("aria-expanded", "true");
    expect(bar(SETTINGS.airAndNoise)).toHaveAttribute("aria-expanded", "true");
    expect(within(theSettings()).getByRole("radio", { name: TENURE_CHOICE.buy })).toBeChecked();
    // No search opened of any of it, and nothing was asked of the service.
    expect(api.callsTo("rank")).toEqual([]);
    expect(api.callsTo("interpret")).toEqual([]);
  });

  test("test_another_helper_pressed_from_inside_what_one_holds_closes_it_and_has_the_focus", async () => {
    const { user } = await openSearch();
    await helper(user, "word");
    const shelf = screen.getByRole("region", { name: SHELF.title });
    await tabTo(user, () => within(shelf).getAllByRole("button")[0] ?? null);

    // Another helper is pressed while the focus is in what this one holds.
    await user.click(within(helpers()).getByRole("button", { name: HELPERS.example }));

    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(within(helpers()).getByRole("button", { name: HELPERS.word })).toHaveAttribute("aria-expanded", "false");
    expect(within(helpers()).getByRole("button", { name: HELPERS.example })).toHaveAttribute("aria-expanded", "true");
    expect(within(helpers()).getByRole("button", { name: HELPERS.example })).toHaveFocus();
  });

  test("test_before_a_search_tab_reaches_every_control_but_the_tab_that_is_not_chosen_which_an_arrow_key_reaches", async () => {
    const { user } = await openSearch();
    const controls = () => [...document.querySelectorAll<HTMLElement>("a[href], button, input, select, textarea")];
    const out = () =>
      controls()
        // What is not drawn is no stop: the panel of the way that is not chosen, and what is kept for a browser with scripts off.
        .filter((control) => control.closest("[hidden], noscript") === null)
        .filter((control) => control.tabIndex < 0)
        .map((control) => control.textContent);

    for (const [chosen, other] of [
      ["quick", "deep"],
      ["deep", "quick"],
    ] as const) {
      await way(user, chosen);
      expect(out()).toEqual([WAYS[other]]);
      expect(tabOf(chosen).tabIndex).toBe(0);
      // The arrow keys lead from the tab that is a stop to the one that is not, either way.
      act(() => tabOf(chosen).focus());
      await user.keyboard(chosen === "quick" ? "{ArrowRight}" : "{ArrowLeft}");
      expect(tabOf(other)).toHaveFocus();
      expect(out()).toEqual([WAYS[chosen]]);
    }
    expect(document.querySelectorAll("main [role='button'], main [role='link'], main [onclick]")).toHaveLength(0);
  });

  test("test_every_control_can_be_reached_with_tab_and_none_is_taken_out_of_the_order", async () => {
    const { user } = await searched();
    await settingsAt(user, SETTINGS.money, SETTINGS.journeys, ...meta.data.families.map((one) => one.label));
    await theWholeOfIt();

    const controls = [...document.querySelectorAll<HTMLElement>("a[href], button, input, select, textarea")];
    const out = controls.filter((control) => control.tabIndex < 0 || control.hasAttribute("disabled") === false && control.getAttribute("tabindex") === "-1");
    const madeUp = document.querySelectorAll("[role='button'], [role='link'], [onclick]");

    expect(controls.length).toBeGreaterThan(150);
    expect(out).toEqual([]);
    expect([...madeUp]).toEqual([]);
  });

  test("test_the_skip_links_lead_to_the_results_and_past_the_map", async () => {
    await searched();

    const toResults = screen.getByRole("link", { name: SEARCH.skipToResults });
    const pastMap = screen.getByRole("link", { name: SEARCH.skipMap });

    for (const link of [toResults, pastMap]) {
      const target = document.getElementById((link.getAttribute("href") ?? "").slice(1));
      expect(target).not.toBeNull();
      expect(target?.tabIndex).toBe(-1);
      expect(link).toHaveClass("target");
    }
    expect(toResults.getAttribute("href")).toBe("#results");
    expect(document.getElementById("results")).toContainElement(results()[0] as HTMLElement);
    // The link past the map comes before the map, and its target after it.
    const panel = screen.getByRole("region", { name: MAP.label });
    expect(panel.firstElementChild).toBe(pastMap);
    expect(panel.lastElementChild?.id).toBe("after-map");
  });

  test("test_what_a_skip_link_leads_to_says_what_it_is_to_whoever_hears_the_page", async () => {
    // Heard in a browser: "Skip the map" left the focus on a thing with no name, no role and
    // no words, and a screen reader had nothing to say as it landed.
    await searched();
    const landsOn = (name: string) =>
      document.getElementById((screen.getByRole("link", { name }).getAttribute("href") ?? "").slice(1)) as HTMLElement;

    expect(landsOn(SEARCH.skipToResults)).toHaveAccessibleName(RESULTS.title);
    expect(landsOn(SEARCH.skipToMap)).toHaveAccessibleName(MAP.label);
    const past = landsOn(SEARCH.skipMap);
    expect(past.textContent).toBe(SEARCH.pastMap);
    expect(SEARCH.pastMap).toBe("End of the map");
    // It is said, and not drawn: a person who sees the page sees where the map ends.
    expect(past.firstElementChild).toHaveClass("visually-hidden");
    expect(past.querySelectorAll("a, button, input")).toHaveLength(0);
  });

  test("test_the_list_the_map_and_the_table_are_on_one_page_at_every_width_with_no_tabs", async () => {
    // The answer comes first at every width. Nothing of it is behind a tab: the two tabs are
    // for beginning a search, and go as one opens. The map is a strip on a narrow screen, and
    // the table is one press from it.
    const { user } = await searched();

    expect(screen.queryByRole("tablist")).toBeNull();
    expect(screen.queryAllByRole("tab")).toEqual([]);
    expect(screen.getByRole("region", { name: MAP.label })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: RESULTS.listLabel })).toBeInTheDocument();
    const table = screen.getByRole("button", { name: TABLE.title });
    await tabTo(user, () => table);
    await user.keyboard("{Enter}");
    expect(screen.getByRole("table", { name: TABLE.caption })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(table).toHaveFocus();
  });

  test("test_moving_a_control_does_not_move_focus", async () => {
    const { user, api } = await searched();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await settingsAt(user, SETTINGS.journeys, SETTINGS.airAndNoise, groupOf("green"));
    const at = window.scrollY;

    const firm = screen.getAllByRole("checkbox", { name: JOURNEY.firm })[0] as HTMLElement;
    await user.click(firm);
    await settled();
    expect(firm).toHaveFocus();

    const air = screen.getByRole("switch", { name: "Cleaner air" });
    await user.click(air);
    await settled();
    expect(air).toHaveFocus();

    // A slider moved with the keyboard keeps the focus when its answer comes.
    const leafy = screen.getByRole("slider", { name: "Leafy" });
    leafy.focus();
    fireEvent.change(leafy, { target: { value: "70" } });
    await settled();
    expect(leafy).toHaveFocus();

    const how = screen.getByRole("radio", { name: "On foot" });
    await user.click(how);
    await settled();
    expect(how).toHaveFocus();
    expect(window.scrollY).toBe(at);
    expect(window.location.href).toBe("http://localhost/");
  });
});

describe("the focus, when what was pressed goes with the press", () => {
  const theChips = () => screen.getByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel})$`) });
  const theSearchButton = () => screen.getByRole("button", { name: new RegExp(`^(${PROMPT.submit}|${PROMPT.reading})$`) });

  test("test_a_way_out_of_no_area_passes_hands_the_focus_to_what_burro_understood", async () => {
    // Seen in a browser, at both sizes: the block goes with the press, once areas pass, and
    // the focus fell to the page as a whole. What the press changes is what Burro understood.
    const { user, api } = await openSearch(
      firstSearch().on("interpret", "interpret-two-journeys").on("rank", "rank-nothing-matches"),
    );
    await search(user, "at most 10 minutes, no more than £400");
    const block = within(screen.getByRole("region", { name: NOTHING_MATCHES.title }));

    api.on("rank", "rank-first");
    await user.click(block.getByRole("button", { name: NOTHING_MATCHES.budgetFlexible }));
    expect(theChips()).toHaveFocus();
    await settled();

    expect(screen.queryByRole("region", { name: NOTHING_MATCHES.title })).toBeNull();
    expect(results().length).toBeGreaterThan(0);
    expect(theChips()).toHaveFocus();
  });

  test("test_an_area_hidden_from_its_working_hands_the_focus_to_what_burro_understood", async () => {
    // Seen in a browser, at both sizes, by pointer and by keyboard: the result goes with
    // the press, and the focus fell to the page as a whole. The area that was hidden is
    // then among what Burro understood, where it can be shown again.
    const { user, api } = await searched();
    const [one] = first.ranked;
    const name = nameOf(one?.area_id ?? "");
    const working = await workingOf(user, name);

    api.on("rank", "rank-refined");
    await user.click(within(working).getByRole("button", { name: RESULTS.hide(name) }));
    expect(theChips()).toHaveFocus();
    await settled();

    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.areaHide(one?.area_id ?? ""));
    expect(theChips()).toHaveFocus();
  });

  test("test_try_again_beside_a_failure_hands_the_focus_to_search_which_is_what_it_presses_again", async () => {
    // Seen in a browser: the failure goes as it is tried again, and the focus was left on
    // nothing. Search stands over every failure of a search, and is what is tried again.
    const { user, api } = await openSearch(firstSearch().on("rank", "error-internal"));
    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    const failure = within(await screen.findByRole("alert"));
    await arrived();

    api.on("rank", "rank-first");
    await user.click(failure.getByRole("button", { name: PROMPT.tryAgain }));
    expect(theSearchButton()).toHaveFocus();
    await settled();

    expect(screen.queryByRole("alert")).toBeNull();
    expect(results().length).toBeGreaterThan(0);
    expect(theSearchButton()).toHaveFocus();
  });

  test("test_start_again_beside_a_failure_hands_the_focus_to_the_box_which_it_leaves_as_it_is", async () => {
    const { user } = await openSearch(firstSearch().on("rank", "error-internal"));
    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    const failure = within(await screen.findByRole("alert"));
    await arrived();

    await user.click(failure.getByRole("button", { name: PROMPT.startAgain }));
    await arrived();

    expect(screen.queryByRole("alert")).toBeNull();
    expect(promptBox().value === "leafy and quiet").toBe(true);
    expect(promptBox()).toHaveFocus();
  });

  test("test_stop_on_a_first_sentence_hands_the_focus_to_search_which_stands_beside_it", async () => {
    // Seen in a browser, at both sizes, and on the trunk: a first sentence was stopped while
    // it was read. No search was open, so Start again did not take the place of Stop, as it
    // does over a search that is: Stop went with the press, and the focus fell to the page
    // as a whole. Search stands beside it, and sends the words again.
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);
    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    await user.click(screen.getByRole("button", { name: PROMPT.stop }));

    expect(screen.queryByRole("button", { name: PROMPT.stop })).toBeNull();
    expect(screen.queryByRole("button", { name: PROMPT.startAgain })).toBeNull();
    expect(screen.getByRole("button", { name: PROMPT.submit })).toHaveFocus();
    expect(document.body).not.toHaveFocus();
    // The words are in the box still, to be sent again or changed.
    expect(promptBox().value === "leafy and quiet").toBe(true);
    reading.release();
    await settled();
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect(screen.getByRole("button", { name: PROMPT.submit })).toHaveFocus();
  });

  test("test_stop_over_a_search_that_is_open_leaves_the_focus_where_start_again_takes_its_place", async () => {
    const { user, api } = await searched();
    const more = api.hold("interpret", "interpret-second-sentence");
    await user.type(promptBox(), ", a bit more green space");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    await user.click(screen.getByRole("button", { name: PROMPT.stop }));

    expect(screen.getByRole("button", { name: PROMPT.startAgain })).toHaveFocus();
    more.release();
    await settled();
    expect(screen.getByRole("button", { name: PROMPT.startAgain })).toHaveFocus();
  });

  test("test_try_again_beside_words_that_were_not_read_hands_the_focus_to_search", async () => {
    const api = firstSearch().on("interpret", "error-internal");
    const { user } = await openSearch(api);
    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    // No search is open yet, so the line names the second way in, where the settings stand.
    await waitFor(() => expect(screen.getAllByRole("status").map((line) => line.textContent)).toContain(UNREAD.before));
    api.on("interpret", "interpret-first");

    await user.click(screen.getByRole("button", { name: PROMPT.tryAgain }));
    expect(theSearchButton()).toHaveFocus();
    await settled();

    expect(screen.queryByRole("button", { name: PROMPT.tryAgain })).toBeNull();
    expect(theSearchButton()).toHaveFocus();
  });

  test("test_try_again_beside_words_that_were_not_read_hands_the_focus_to_search_once_a_search_is_open_too", async () => {
    const { user, api } = await searched();
    api.on("interpret", "error-internal");
    await user.type(promptBox(), ", a bit more green space");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    // A search is open, so the line speaks of the settings, which the page has opened.
    await waitFor(() => expect(screen.getAllByRole("status").map((line) => line.textContent)).toContain(NOTICE.degraded));
    api.on("interpret", "interpret-second-sentence");

    await user.click(screen.getByRole("button", { name: PROMPT.tryAgain }));
    expect(theSearchButton()).toHaveFocus();
    await settled();

    expect(screen.queryByRole("button", { name: PROMPT.tryAgain })).toBeNull();
    expect(document.body).not.toHaveFocus();
  });
});

describe("sliders", () => {
  test("test_every_slider_can_be_set_without_dragging", async () => {
    const { user, api } = await searched();
    await settingsAt(
      user,
      SETTINGS.money,
      SETTINGS.journeys,
      ...meta.data.families.map((one) => one.label),
      SETTINGS.airAndNoise,
    );
    const scales = meta.data.tags.filter((tag) => tag.shape === "scale");

    const sliders = screen.getAllByRole("slider");
    expect(sliders.length).toBeGreaterThan(10);
    for (const slider of sliders) {
      const label = slider.getAttribute("aria-label") ?? document.querySelector(`label[for="${slider.id}"]`)?.textContent ?? "";
      // The slider lies over the gauge that draws it, in a holder that holds the two and
      // nothing else. What sets it without dragging stands beside that holder, in the row
      // of the slider, which says whether it runs one way or between two ends.
      const held = slider.closest<HTMLElement>("[data-ends]");
      const row = within(held as HTMLElement);
      const scale = scales.find((tag) => tag.label === label);
      expect(label).not.toBe("");
      expect([label, held?.getAttribute("data-ends")]).toEqual([label, scale === undefined ? "false" : "true"]);
      expect(within(held as HTMLElement).getAllByRole("slider")).toEqual([slider]);
      if (scale === undefined) {
        expect(row.getByRole("button", { name: SLIDER.less(label) })).toBeInTheDocument();
        expect(row.getByRole("button", { name: SLIDER.more(label) })).toBeInTheDocument();
        expect(row.getByRole("textbox", { name: SLIDER.number(label) })).toBeInTheDocument();
      } else {
        // A scale has a button at each end, named for the end, that moves it a step that way.
        expect(row.getByRole("button", { name: SLIDER.toward(label, scale.low_end ?? "") })).toBeInTheDocument();
        expect(row.getByRole("button", { name: SLIDER.toward(label, scale.high_end ?? "") })).toBeInTheDocument();
      }
    }
    expect(sliders.filter((slider) => slider.getAttribute("min") === "-100")).toHaveLength(scales.length);

    // With the button.
    api.calls.length = 0;
    await user.click(screen.getByRole("button", { name: SLIDER.less("Leafy") }));
    await waitFor(() => expect(api.callsTo("rank")).toHaveLength(1));
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.tagWeight("leafy", 0.4, "high"));
    await settled();

    // With the number field.
    const field = screen.getByRole("textbox", { name: SLIDER.number("Leafy") });
    await user.clear(field);
    await user.type(field, "73{Enter}");
    await settled();
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.tagWeight("leafy", 0.75, "high"));

    // With the arrow keys.
    const slider = screen.getByRole("slider", { name: "Leafy" });
    slider.focus();
    fireEvent.change(slider, { target: { value: "55" } });
    await waitFor(() =>
      expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.tagWeight("leafy", 0.55, "high")),
    );
    await settled();

    // A scale, with the button at one of its ends.
    api.calls.length = 0;
    await user.click(screen.getByRole("button", { name: SLIDER.toward("Going out", "Calm") }));
    await waitFor(() => expect(api.callsTo("rank")).toHaveLength(1));
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.tagWeight("pace", 0.1, "low"));
    await settled();
  });

  test("test_the_budget_and_the_longest_journey_have_buttons_and_a_field_too", async () => {
    const { user, api } = await searched();
    await settingsAt(user, SETTINGS.money, SETTINGS.journeys);

    await user.click(screen.getByRole("button", { name: BUDGET.more }));
    await settled();
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.budgetStep("up_small"));

    await user.click(screen.getByRole("button", { name: JOURNEY.shorter }));
    await settled();
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeStep("syn-p0021", "down_small"));

    const longest = screen.getByRole("textbox", { name: JOURNEY.longest });
    await user.clear(longest);
    await user.type(longest, "500");
    await user.tab();
    await settled();
    // A journey is kept within what the data holds, so the form never offers what would be refused.
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeMinutes("syn-p0021", 90));
  });
});

describe("target sizes", () => {
  const SIZED = ".target, .target-min";

  function unsized(): string[] {
    const controls = [
      ...document.querySelectorAll<HTMLElement>(
        "button, input, select, textarea, a[href], [role='option'], [role='tab'], [role='switch']",
      ),
    ];
    return controls
      .filter((control) => {
        if (control.matches(SIZED) || control.closest(`label:is(${SIZED})`)) return false;
        // A link in a sentence is sized by its line, as the guidelines allow.
        if (control.tagName === "A" && control.closest("p") !== null) return false;
        // The shell is another part's, and has its own test.
        return control.closest("main") !== null;
      })
      .map((control) => `${control.tagName.toLowerCase()} ${control.textContent?.slice(0, 40) ?? ""}`);
  }

  test("test_every_control_takes_a_target_size", async () => {
    setWebGL(true);
    const { user } = await searched(firstSearch().on("interpret", "interpret-clarify"));
    act(() => lastMap().fire("load"));
    await arrived();
    await settingsAt(
      user,
      SETTINGS.money,
      SETTINGS.journeys,
      ...meta.data.families.map((one) => one.label),
      SETTINGS.airAndNoise,
    );
    await theWholeOfIt();
    await user.click(screen.getAllByRole("button", { name: /^Source/ })[0] as HTMLElement);
    await user.click(within(screen.getByRole("region", { name: CHIPS.label })).getByRole("button", { name: /^Leafy/ }));
    // The list of the field that finds a place, among the settings.
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });
    await user.type(field, "pel");
    await within(listOf(field)).findAllByRole("option");

    expect(document.querySelectorAll(`main :is(${SIZED})`).length).toBeGreaterThan(200);
    expect(unsized()).toEqual([]);
  });

  test("test_every_control_of_the_page_before_a_search_takes_a_target_size", async () => {
    const { user } = await openSearch();
    expect(unsized()).toEqual([]);
    for (const one of within(helpers()).getAllByRole("button")) expect(one).toHaveClass("target");
    // The two tabs are main controls, the one that is not chosen as the one that is.
    for (const way of WAY_IDS) expect(tabOf(way)).toHaveClass("target");

    // With each helper open in turn, and with what it holds opened.
    await helper(user, "example");
    expect(screen.getAllByRole("button", { name: /^(Renting|Buying|Somewhere) / }).length).toBe(3);
    expect(unsized()).toEqual([]);

    await helper(user, "word");
    const shelf = within(screen.getByRole("region", { name: SHELF.title }));
    await user.click(shelf.getAllByRole("button")[0] as HTMLElement);
    expect(shelf.getAllByRole("button").length).toBeGreaterThan(5);
    expect(unsized()).toEqual([]);

    // The second way in, with two groups of its settings open, and the bar of every group.
    await settingsAt(user, SETTINGS.money, SETTINGS.journeys);
    expect(screen.getAllByRole("radio").length).toBeGreaterThanOrEqual(2);
    expect(within(panelOf("deep")).getByRole("textbox", { name: FIND_AREA.labelAlone })).toBeInTheDocument();
    expect(unsized()).toEqual([]);
    const bars = within(theSettings()).getAllByRole("button", { expanded: false });
    expect(bars.length).toBeGreaterThan(5);
    for (const bar of bars) expect(bar).toHaveClass("target");
  });

  test("test_every_control_of_a_search_of_which_burro_took_what_it_noticed_takes_a_target_size", async () => {
    // What the reader noticed was offered, each thing with its buttons. Nothing is offered
    // now: what is drawn of such a sentence is the chips of what Burro took, and the way to
    // see the words it did not read.
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-suggest-newcomer"));
    await user.type(promptBox(), "I am moving to the city for a job");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    await everyChip(user);

    expect(screen.queryAllByRole("button", { name: /^Skip: / })).toEqual([]);
    expect(screen.getByRole("button", { name: SUGGEST.showUnread })).toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: CHIPS.label })).getAllByRole("button").length).toBeGreaterThan(3);
    expect(unsized()).toEqual([]);
  });

  test("test_the_controls_of_a_failure_take_a_target_size", async () => {
    const { user, api } = await searched();
    api.on("rank", "error-internal");
    await removeChip(user, "Leafy");
    await screen.findByRole("alert");

    expect(unsized()).toEqual([]);
  });
});

describe("colour is never the only signal", () => {
  test("test_everything_the_map_shows_is_in_the_table", async () => {
    const { user, api } = await searched();
    await theTable(user);
    const table = () => within(screen.getAllByRole("table", { name: TABLE.caption })[0] as HTMLElement);
    const rowOf = (areaId: string) =>
      table()
        .getAllByRole("row")
        .find((row) => within(row).queryByRole("link", { name: nameOf(areaId) })) as HTMLElement;

    first.scores.forEach(({ area_id: areaId, score }, at) => {
      const cells = within(rowOf(areaId)).getAllByRole("cell").map(saidIn);
      // A fit that rests on part of what counts says so beside the fit, as its card does.
      const counts = first.scores.find((one) => one.area_id === areaId);
      const based =
        counts === undefined || counts.present === counts.counted
          ? ""
          : ` ${COMPLETENESS.some(counts.present, counts.counted)}`;
      expect(cells.slice(0, 4)).toEqual([
        String(at + 1),
        "Quillhaven",
        `${Math.floor(score)} of 100${based}`,
        TABLE.ranked,
      ]);
    });
    // An area with no rank says why in words: the data does not rank it, or too little is known of it.
    for (const { area_id: areaId, reason } of first.unranked) {
      expect(rowOf(areaId)).toHaveTextContent(UNRANKED[reason]);
    }
    expect(new Set(first.unranked.map((area) => area.reason))).toEqual(new Set(["not_rankable", "insufficient_data"]));
    expect(table().getAllByRole("row")).toHaveLength(areas.length + 1);

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await removeChip(user, "Leafy");
    await settled();
    for (const { area_id: areaId } of refined.filtered) {
      expect(rowOf(areaId)).toHaveTextContent("A journey is longer than a firm limit");
    }
    // In rank order, and then by name. Under a name is the label its publisher gives the area.
    const names = table()
      .getAllByRole("rowheader")
      .map((cell) => cell.querySelector("a")?.textContent);
    const ranked = refined.scores.map((score) => nameOf(score.area_id));
    expect(names.slice(0, ranked.length)).toEqual(ranked);
    expect(names.slice(ranked.length)).toEqual([...names.slice(ranked.length)].sort());
  });

  test("test_rank_and_status_are_in_words_wherever_they_are_in_colour", async () => {
    setWebGL(true);
    const { user, api } = await searched();
    act(() => lastMap().fire("load"));
    await arrived();

    // Rank: a number in the card, in the pin and in the table.
    const card = await workingOf(user, "Farrowmere");
    await everyChip(user);
    expect(within(card as HTMLElement).getByText(RESULTS.rank(1))).toBeInTheDocument();
    expect(within(card as HTMLElement).getByText(`${RESULTS.fitOf(71)}`)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: MAP.pin(1, "Farrowmere", RESULTS.fitOf(71)) })).toBeInTheDocument();
    // Within and over: words.
    expect(within(card as HTMLElement).getByText(JOURNEYS.within)).toBeInTheDocument();
    // Assumed, and flexible or firm: words. In the row a chip says that the rest was assumed,
    // and opened it says which part.
    const chips = screen.getByRole("region", { name: CHIPS.label });
    expect(chips).toHaveTextContent(CHIPS.restAssumed);
    await user.click(within(chips).getByRole("button", { name: /^Cindermoor Works/ }));
    expect(chips).toHaveTextContent(`${CHIPS.flexible} ${CHIPS.assumed}`);
    await user.click(within(chips).getByRole("button", { name: /^Cindermoor Works/ }));
    // Where an area sits on a vibe: a band, in words, on the picture that draws it.
    for (const picture of within(card).getAllByRole("img", { name: /^band/ })) {
      expect(picture.getAttribute("aria-label")).toMatch(/^bands? \d/);
    }
    // Confidence: a word. The pips are hidden from a reader.
    const cost = within(card as HTMLElement).getByRole("heading", { name: COST.title }).parentElement as HTMLElement;
    expect(within(cost).getByText(CONFIDENCE.high, { exact: false })).toBeInTheDocument();
    for (const pips of document.querySelectorAll("[class*='pips']")) {
      expect(pips).toHaveAttribute("aria-hidden", "true");
    }
    // The trade-off is under a heading that says so.
    expect(within(card as HTMLElement).getByRole("heading", { name: RESULTS.tradeOffTitle })).toBeInTheDocument();

    // Chosen: said to a reader on the card, the pin and the table row.
    await user.click(screen.getByRole("button", { name: RESULTS.showOnMap("Farrowmere") }));
    expect(card).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("button", { name: MAP.pin(1, "Farrowmere", RESULTS.fitOf(71)) })).toHaveAttribute(
      "aria-current",
      "true",
    );
    await theTable(user);
    expect(document.querySelectorAll("tr[aria-current='true']").length).toBeGreaterThan(0);

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await removeChip(user, "Leafy");
    await settled();
    expect(screen.getByRole("region", { name: CHIPS.label })).toBeInTheDocument();
  });

  test("test_the_list_and_the_map_are_in_step_in_both_directions", async () => {
    setWebGL(true);
    const { user } = await searched();
    act(() => lastMap().fire("load"));
    await arrived();
    const cards = results();

    // From the list to the map: the card under the pointer or the focus is outlined on the map.
    await user.hover(cards[1] as HTMLElement);
    expect(lastMap().states.get("syn-n0005")).toMatchObject({ hovered: true });
    await user.unhover(cards[1] as HTMLElement);
    expect(lastMap().states.get("syn-n0005")).toMatchObject({ hovered: false });
    act(() => within(cards[0] as HTMLElement).getAllByRole("button")[0]?.focus());
    expect(lastMap().states.get("syn-n0006")).toMatchObject({ hovered: true });

    // From the map to the list: pressing a pin chooses the area on the map, and its card
    // opens by the map. The pin says that it is the one chosen and that it opened the card,
    // in a way that is heard, and the focus is on the card it opened: never on nothing. The
    // list is not told yet: told, it brought the result into sight, and the page went from
    // under the pin that was pressed.
    const pin = screen.getByRole("button", { name: /^Rank 4,/ });
    fireEvent.click(pin);
    const card = screen.getByRole("region", { name: MAP_CARD.label });
    expect(card).toHaveTextContent(nameOf("syn-n0003"));
    expect(pin).toHaveAttribute("aria-current", "true");
    expect(pin).toHaveAttribute("aria-expanded", "true");
    expect(pin).toHaveAttribute("aria-controls", card.id);
    expect(card).toHaveFocus();
    expect(lastMap().states.get("syn-n0003")).toMatchObject({ selected: true });
    expect(cards.filter((one) => one.hasAttribute("aria-current"))).toHaveLength(0);

    // "Show in the list" tells the list: the card says that it is the one chosen, in a way
    // that is heard, and has the focus.
    await user.click(screen.getByRole("button", { name: MAP_CARD.showInList }));
    expect(cards[3]).toHaveAttribute("aria-current", "true");
    expect(cards.filter((card) => card.hasAttribute("aria-current"))).toHaveLength(1);
    expect(cards[3]).toHaveFocus();
  });

  test("test_an_area_chosen_on_the_map_that_is_past_the_first_ten_is_shown_in_the_list", async () => {
    setWebGL(true);
    const { user } = await searched();
    act(() => lastMap().fire("load"));
    await arrived();
    const far = first.ranked[14];
    expect(results()).toHaveLength(SHOWN_AT_FIRST);

    act(() => lastMap().fire("click", { features: [{ id: far?.area_id }] }, "areas-fill"));
    await user.click(screen.getByRole("button", { name: "Show in the list" }));

    expect(results()).toHaveLength(first.ranked.length);
    expect(results()[14]).toHaveAttribute("aria-current", "true");
    expect(results()[14]).toHaveFocus();
  });
});

describe("what is said, and when", () => {
  test("test_each_state_is_announced_once", async () => {
    const api = firstSearch();
    const { user } = await openSearch(api);
    const line = screen.getAllByRole("status").find((one) => one.getAttribute("aria-live") === "polite") as HTMLElement;
    const said: string[] = [];
    const watcher = new MutationObserver(() => {
      const text = line.textContent ?? "";
      if (text !== said[said.length - 1]) said.push(text);
    });
    watcher.observe(line, { childList: true, characterData: true, subtree: true });

    await search(user);
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await removeChip(user, "Leafy");
    await settled();
    api.on("rank", "rank-nothing-matches");
    await removeChip(user, "Quiet streets");
    await settled();
    watcher.disconnect();

    // Eleven areas went, which moves no other. It is said that they went, and how many of the
    // rest moved: none, or so many, in the words the line has for each.
    const went = STATUS.rankedNow(refined.scores.length, refined.scores.length - first.scores.length);
    const ofTheRest = Array.from({ length: refined.scores.length + 1 }, (_, moved) => STATUS.movedOfTheRest(moved));
    expect([first.scores.length, refined.scores.length]).toEqual([21, 10]);
    expect(said).toHaveLength(4);
    expect(said.slice(0, 2)).toEqual([STATUS.reading, `${STATUS.ranked(21, "Farrowmere")} ${STATUS.gaveWay}`]);
    expect(ofTheRest.map((rest) => `${went} ${rest}`)).toContain(said[2]);
    expect(said[3]).toBe(STATUS.nothingMatches);
    // There is one polite line for the state of the search.
    expect(screen.getAllByRole("status").filter((one) => one.getAttribute("aria-live") === "polite")).toHaveLength(1);
  });

  test("test_an_answer_that_is_said_in_the_words_of_the_last_is_said_again", async () => {
    // Seen in a browser: a budget was set and cleared three times, and the first ten results
    // changed each of the six times. The line was changed once, to "20 areas changed place.",
    // and no node of it was touched the five times after: what it had to say was what it
    // said already, so a screen reader was told nothing of five answers.
    const api = firstSearch();
    const { user } = await openSearch(api);
    const line = theLine();
    // Every time the line is touched, with what it then says. Nothing is left out for
    // saying what was said before: that is what is asked here.
    const touched: string[] = [];
    const watcher = new MutationObserver(() => touched.push(line.textContent ?? ""));
    watcher.observe(line, { childList: true, characterData: true, subtree: true });

    await search(user);
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await removeChip(user, "Leafy");
    await settled();
    // The service answers as it did: the list is the list it was, and no area moved.
    await removeChip(user, "Quiet streets");
    await settled();
    // And again. The line says of it what it said of the last.
    await removeChip(user, "Quiet streets");
    await settled();
    watcher.disconnect();

    expect(api.callsTo("rank")).toHaveLength(4);
    const went = STATUS.rankedNow(refined.scores.length, refined.scores.length - first.scores.length);
    expect(touched[0]).toBe(STATUS.reading);
    expect(touched.slice(-3).map((said) => said.replace(went, "WENT"))).toEqual([
      expect.stringMatching(/^WENT /),
      STATUS.moved(0),
      STATUS.moved(0),
    ]);
    // Nothing is said twice that happened once: a search is read once, and ranked once.
    expect(touched.filter((said) => said === STATUS.reading)).toHaveLength(1);
    expect(touched).toHaveLength(5);
    // It is the same line all the while, and the one polite line of the search.
    expect(theLine()).toBe(line);
    expect(screen.getAllByRole("status").filter((one) => one.getAttribute("aria-live") === "polite")).toHaveLength(1);
  });

  test("test_a_failure_is_an_alert_and_a_notice_is_a_status", async () => {
    const { user, api } = await searched(firstSearch().on("interpret", "interpret-notice"));

    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("status", { name: "About your search" })).toBeInTheDocument();

    api.on("rank", "error-internal");
    await removeChip(user, "Leafy");
    expect(await screen.findAllByRole("alert")).toHaveLength(1);
  });
});

describe("automated checks of each state with everything open", () => {
  test("test_the_results_with_the_settings_a_chip_and_a_source_open_have_no_fault", async () => {
    const { user, container } = await searched();
    await settingsAt(
      user,
      SETTINGS.money,
      SETTINGS.journeys,
      ...meta.data.families.map((one) => one.label),
      SETTINGS.airAndNoise,
      "Recorded crime",
      FEATURES.madeOfName("Going out"),
    );
    await theWholeOfIt();
    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));
    await user.click(within(results()[0] as HTMLElement).getAllByRole("button", { name: /^Source/ })[0] as HTMLElement);
    expect(within(results()[1] as HTMLElement).getByRole("table", { name: BREAKDOWN.caption })).toBeInTheDocument();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_results_as_they_first_stand_have_no_fault", async () => {
    const { container } = await searched();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_before_a_search_with_a_vibe_open_has_no_fault", async () => {
    const { user, container } = await openSearch();
    await helper(user, "word");
    await user.click(within(screen.getByRole("region", { name: SHELF.title })).getAllByRole("button")[0] as HTMLElement);

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_before_a_search_with_the_examples_open_has_no_fault", async () => {
    const { user, container } = await openSearch();

    await helper(user, "example");
    expect(screen.getAllByRole("button", { name: /^(Renting|Buying|Somewhere) / })).toHaveLength(3);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_before_a_search_with_the_second_way_chosen_and_every_group_open_has_no_fault", async () => {
    const { user, container } = await openSearch();

    // As it stands when it is first chosen, with a couple of groups open.
    await way(user, "deep");
    expect(within(theSettings()).getAllByRole("button", { expanded: true }).length).toBeGreaterThan(0);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    // With every group open, and the list of the field that finds a place.
    await settingsAt(
      user,
      SETTINGS.money,
      SETTINGS.journeys,
      ...meta.data.families.map((one) => one.label),
      SETTINGS.airAndNoise,
      "Recorded crime",
    );
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });
    await user.type(field, "pel");
    await within(listOf(field)).findAllByRole("option");
    expect(within(theSettings()).getAllByRole("button", { expanded: true }).length).toBeGreaterThanOrEqual(
      4 + meta.data.families.length,
    );
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
    // And with the areas that the field at the foot of the way found, each a link to its page.
    await user.keyboard("{Escape}");
    await user.type(within(panelOf("deep")).getByRole("textbox", { name: FIND_AREA.labelAlone }), "pel");
    await screen.findByRole("group", { name: FIND_AREA.title });
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_of_a_sentence_that_is_no_plain_list_has_no_fault_with_its_notice_and_what_burro_took", async () => {
    const { user, container } = await openSearch(firstSearch().on("interpret", "interpret-suggest-notice"));
    await user.type(promptBox(), "leafy with lots of students. My street is noisy.");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_with_a_map_and_a_chosen_area_has_no_fault", async () => {
    setWebGL(true);
    const { container } = await searched();
    act(() => lastMap().fire("load"));
    await arrived();
    fireEvent.click(screen.getByRole("button", { name: /^Rank 2,/ }));

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_where_a_name_is_borne_by_several_places_has_no_fault_nor_with_a_list_of_places_open", async () => {
    // Nothing is asked: the first of the places is taken, and its chip says so.
    const { user, container } = await searched(firstSearch().on("interpret", "interpret-clarify"));
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    // The place is changed where the search is refined, by the field of the journeys.
    await settingsAt(user, SETTINGS.journeys);
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });
    await user.type(field, "pel");
    await within(listOf(field)).findAllByRole("option");
    await user.keyboard("{ArrowDown}");

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_that_says_what_burro_left_out_has_no_fault_with_its_line_closed_or_open", async () => {
    // What counts who lived somewhere is left out, and named in one line that opens to why.
    // A place Burro does not know is said among what was not applied.
    const counted = recordedAnswer("interpret", "interpret-suggest-who-is-counted");
    const opened = await openSearch(firstSearch().on("interpret", "interpret-suggest-who-is-counted"));
    await search(opened.user, (counted.request.body as { text: string }).text);
    const left = screen.getByRole("status", { name: LEFT_OUT.title });
    const line = left.querySelector("summary") as HTMLElement;
    expect(line.textContent).toBe(`${LEFT_OUT.title}: Young professionals`);
    expect(await faultsIn(opened.container, { wholePage: true })).toEqual([]);
    // The line is the browser's own element, which a keyboard stops at and opens. Here it
    // is pressed: the stand-in for a browser opens one by a press and by no key.
    expect(line.tagName).toBe("SUMMARY");
    expect(line.parentElement?.tagName).toBe("DETAILS");
    act(() => line.focus());
    expect(line).toHaveFocus();
    await opened.user.click(line);
    expect((left.querySelector("details") as HTMLDetailsElement).open).toBe(true);
    expect(line).toHaveFocus();
    expect(left).toHaveTextContent(LEFT_OUT.why.residents);
    expect(await faultsIn(opened.container, { wholePage: true })).toEqual([]);
    opened.unmount();

    // A thing whose way the words do not give, and one that waits for the person, with
    // nothing ranked: the line stands open, and names each with why.
    const noisy = await openSearch(firstSearch().on("interpret", "interpret-suggest"));
    await search(noisy.user, "Pubs are so noisy");
    const open = screen.getByRole("status", { name: LEFT_OUT.title });
    expect(open).toHaveTextContent(LEFT_OUT.why.two_ways);
    expect(open).toHaveTextContent(LEFT_OUT.why.by_choice);
    expect(await faultsIn(noisy.container, { wholePage: true })).toEqual([]);
    noisy.unmount();

    const unknown = recordedAnswer("interpret", "interpret-clarify-no-options");
    const { user, container } = await openSearch(firstSearch().on("interpret", "interpret-clarify-no-options"));
    await search(user, (unknown.request.body as { text: string }).text);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_the_page_while_it_is_reading_has_no_fault", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user, container } = await openSearch(api);
    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
    reading.release();
    await settled();
  });
});
