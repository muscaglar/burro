/**
 * The two ways into a search, which are two tabs, held to docs/design/web.md
 * section 9: a keyboard reaches the tab that is chosen and the arrow keys the
 * other, each says whether it is chosen and names the panel it shows, and the
 * focus is never left on nothing when a way is chosen, whatever had it.
 *
 * The tests beside the tabs hold them alone. These hold them in the whole
 * page, as a person meets them: from the head of the page, by keyboard, with
 * what was typed in hand.
 *
 * axe runs here in jsdom and cannot judge contrast, size or layout.
 */

import { act, screen, within } from "@testing-library/react";

import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { HELPERS } from "@/content/helpers";
import { FIND_AREA, PLACE, PROMPT, SHELF, TENURE_CHOICE } from "@/content/search";
import { BUDGET, SETTINGS } from "@/content/settings";
import { WAY_IDS, WAYS } from "@/content/ways";

import { setOnline, standInApi } from "../support/api";
import { faultsIn } from "../support/axe";
import {
  firstSearch,
  helper,
  helpers,
  openSearch,
  panelOf,
  promptBox,
  results,
  search,
  settingsAt,
  settled,
  tabOf,
  theSettings,
  way,
  ways,
  waysIfAny,
} from "../support/search";
import { focusGoesOnlyToWhatIsDrawn, theFocusIsOnWhatIsDrawn } from "./drawn";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

type User = Awaited<ReturnType<typeof openSearch>>["user"];

beforeEach(() => {
  setOnline(true);
  focusGoesOnlyToWhatIsDrawn();
});

/** Presses Tab until the focus is on the element, and says how many presses it took. */
async function tabTo(user: User, wanted: () => Element | null) {
  for (let presses = 0; presses < 200; presses += 1) {
    if (document.activeElement !== null && document.activeElement === wanted()) return presses;
    await user.tab();
  }
  throw new Error("Tab never reached it.");
}

/** Every stop of the keyboard, from the head of the page to its foot, as Tab comes to them. */
async function everyStop(user: User): Promise<Element[]> {
  const stops: Element[] = [];
  act(() => (document.activeElement as HTMLElement | null)?.blur());
  for (let presses = 0; presses < 400; presses += 1) {
    await user.tab();
    if (document.activeElement === null || document.activeElement === document.body) return stops;
    stops.push(document.activeElement);
  }
  throw new Error("Tab never came to the foot of the page.");
}

describe("the two ways in, to whoever hears the page", () => {
  test("test_they_are_one_list_of_two_tabs_and_each_says_whether_it_is_chosen", async () => {
    const { user } = await openSearch();

    expect(screen.getAllByRole("tablist")).toEqual([ways()]);
    expect(ways()).toHaveAccessibleName(WAYS.label);
    expect(within(ways()).getAllByRole("tab").map((tab) => tab.textContent)).toEqual(WAY_IDS.map((id) => WAYS[id]));
    expect(screen.getAllByRole("tab")).toEqual(within(ways()).getAllByRole("tab"));
    for (const id of WAY_IDS) {
      // A native button, which says that it is a tab and whether it is chosen, in so many words.
      expect([id, tabOf(id).tagName, tabOf(id).getAttribute("type")]).toEqual([id, "BUTTON", "button"]);
      expect(tabOf(id)).toHaveAccessibleName(WAYS[id]);
      expect(["true", "false"]).toContain(tabOf(id).getAttribute("aria-selected"));
      expect(tabOf(id)).toHaveClass("target");
    }
    expect(WAY_IDS.map((id) => tabOf(id).getAttribute("aria-selected"))).toEqual(["true", "false"]);

    await way(user, "deep");
    expect(WAY_IDS.map((id) => tabOf(id).getAttribute("aria-selected"))).toEqual(["false", "true"]);
    await way(user, "quick");
    expect(WAY_IDS.map((id) => tabOf(id).getAttribute("aria-selected"))).toEqual(["true", "false"]);
  });

  test("test_each_tab_names_the_panel_it_shows_and_the_panel_that_is_not_chosen_is_heard_by_nobody", async () => {
    const { user } = await openSearch();

    for (const [chosen, other] of [
      ["quick", "deep"],
      ["deep", "quick"],
    ] as const) {
      await way(user, chosen);

      // One panel is heard, and it is named by its tab.
      const heard = screen.getAllByRole("tabpanel");
      expect(heard).toEqual([panelOf(chosen)]);
      expect(panelOf(chosen)).toHaveAccessibleName(WAYS[chosen]);
      expect(panelOf(chosen).getAttribute("aria-labelledby")).toBe(tabOf(chosen).id);
      expect(panelOf(chosen)).toBeVisible();
      // The other is on the page, so that what it holds is kept, and is not drawn: nothing of
      // it is heard, and nothing of it is a stop of the keyboard.
      expect(panelOf(other)).toBeInTheDocument();
      expect(panelOf(other)).not.toBeVisible();
      expect(panelOf(other)).toHaveAttribute("hidden");
      expect((await everyStop(user)).filter((stop) => panelOf(other).contains(stop))).toEqual([]);
    }
  });

  test("test_once_a_search_is_open_there_is_no_tab_and_no_panel_and_start_again_brings_both_back", async () => {
    const { user } = await openSearch();
    await search(user);

    expect(waysIfAny()).toBeNull();
    expect(screen.queryAllByRole("tab")).toEqual([]);
    expect(screen.queryAllByRole("tabpanel")).toEqual([]);
    expect(document.querySelectorAll("[role='tab'], [role='tabpanel'], [role='tablist']")).toHaveLength(0);

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    await settled();

    expect(WAY_IDS.map((id) => tabOf(id).getAttribute("aria-selected"))).toEqual(["true", "false"]);
    expect(screen.getAllByRole("tabpanel")).toEqual([panelOf("quick")]);
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
  });

  test.each(WAY_IDS)("test_the_page_has_no_fault_with_the_way_chosen_by_keyboard: %s", async (id) => {
    const { user, container } = await openSearch();
    await user.type(promptBox(), "leafy and quiet");

    act(() => tabOf("quick").focus());
    if (id === "deep") await user.keyboard("{ArrowRight}");

    expect(tabOf(id)).toHaveFocus();
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("the two ways in, by keyboard", () => {
  test("test_tab_reaches_the_way_that_is_chosen_from_the_head_of_the_page_and_never_the_other", async () => {
    const { user } = await openSearch();

    const presses = await tabTo(user, () => tabOf("quick"));

    // After the links of the head of the page, the link that skips to the map and the
    // button beside Burro. The box is the next stop, and the other tab is none.
    expect(presses).toBeLessThanOrEqual(10);
    expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
    await user.tab();
    expect(promptBox()).toHaveFocus();
    await user.tab({ shift: true });
    expect(tabOf("quick")).toHaveFocus();
    expect((await everyStop(user)).filter((stop) => stop.getAttribute("role") === "tab")).toEqual([tabOf("quick")]);
  });

  test("test_an_arrow_key_chooses_the_other_way_and_tab_goes_on_into_its_panel", async () => {
    const { user, api } = await openSearch();
    const sent = api.calls.length;
    await tabTo(user, () => tabOf("quick"));

    await user.keyboard("{ArrowRight}");

    expect(tabOf("deep")).toHaveFocus();
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    expect(panelOf("deep")).toBeVisible();
    // Tab goes into the panel, to the first thing its settings hold. Back is the tab.
    await user.tab();
    expect(panelOf("deep")).toContainElement(document.activeElement as HTMLElement);
    expect(document.activeElement).toBe(theSettings().querySelector("button, input, select, textarea, a[href]"));
    await user.tab({ shift: true });
    expect(tabOf("deep")).toHaveFocus();
    // The keyboard stops at the one that is chosen now, and at no other.
    expect((await everyStop(user)).filter((stop) => stop.getAttribute("role") === "tab")).toEqual([tabOf("deep")]);
    // Choosing a way asks nothing of the service.
    expect(api.calls).toHaveLength(sent);
  });

  test("test_the_arrow_keys_go_round_and_home_and_end_go_to_the_first_and_the_last_with_the_focus_on_the_tab_chosen", async () => {
    const { user } = await openSearch();
    await tabTo(user, () => tabOf("quick"));

    for (const [key, chosen] of [
      ["{ArrowRight}", "deep"],
      ["{ArrowRight}", "quick"],
      ["{ArrowLeft}", "deep"],
      ["{ArrowLeft}", "quick"],
      ["{End}", "deep"],
      ["{End}", "deep"],
      ["{Home}", "quick"],
      ["{Home}", "quick"],
    ] as const) {
      await user.keyboard(key);

      expect([key, tabOf(chosen) === document.activeElement]).toEqual([key, true]);
      expect([key, ...WAY_IDS.map((id) => tabOf(id).getAttribute("aria-selected"))]).toEqual([
        key,
        ...WAY_IDS.map((id) => String(id === chosen)),
      ]);
      expect([key, panelOf(chosen).hidden]).toEqual([key, false]);
    }
  });

  test("test_enter_and_space_on_a_tab_leave_it_chosen_and_send_nothing", async () => {
    // A tab is chosen as it takes the focus, so there is nothing for a press to do: it must
    // not send the box, which stands in the same part of the page.
    const { user, api } = await openSearch();
    await user.type(promptBox(), "leafy and quiet");
    const sent = api.calls.length;
    await tabTo(user, () => tabOf("quick"));

    await user.keyboard("{Enter} ");
    await user.keyboard("{ArrowRight}{Enter} ");

    expect(tabOf("deep")).toHaveFocus();
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    expect(waysIfAny()).not.toBeNull();
    expect(api.calls).toHaveLength(sent);
  });
});

describe("the focus, when a way is chosen", () => {
  test("test_a_way_chosen_while_the_box_has_the_focus_takes_the_focus_to_its_tab", async () => {
    // The box goes from sight with its panel. What had the focus is not drawn any more, and
    // a browser would leave the focus on the page as a whole.
    const { user } = await openSearch();
    await user.type(promptBox(), "leafy and quiet");
    expect(promptBox()).toHaveFocus();

    await user.click(tabOf("deep"));

    expect(tabOf("deep")).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    // Back, what was typed is in the box it was typed in, to be gone on with.
    await user.click(tabOf("quick"));
    expect(tabOf("quick")).toHaveFocus();
    expect(promptBox()).toHaveValue("leafy and quiet");
    await user.tab();
    expect(promptBox()).toHaveFocus();
  });

  test("test_a_way_chosen_while_the_focus_is_in_what_a_helper_opened_takes_the_focus_to_its_tab_and_the_helper_is_as_it_was", async () => {
    const { user } = await openSearch();
    await helper(user, "example");
    await tabTo(user, () => screen.getAllByRole("button", { name: /^(Renting|Buying|Somewhere) / })[0] ?? null);

    await user.click(tabOf("deep"));
    expect(tabOf("deep")).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);

    await user.keyboard("{Home}");
    expect(tabOf("quick")).toHaveFocus();
    expect(within(helpers()).getByRole("button", { name: HELPERS.example })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getAllByRole("button", { name: /^(Renting|Buying|Somewhere) / })).toHaveLength(3);
  });

  test("test_a_way_chosen_while_a_list_of_places_is_open_closes_nothing_by_force_and_loses_no_focus", async () => {
    const { user } = await openSearch();
    await way(user, "deep");
    // The field of the journeys, among the settings, which finds a place to reach.
    const theField = () => within(theSettings()).getByRole("combobox", { name: PLACE.label });
    const field = theField();
    await user.type(field, "pel");
    await within(document.getElementById(field.getAttribute("aria-controls") ?? "") as HTMLElement).findAllByRole("option");

    await user.click(tabOf("quick"));

    expect(tabOf("quick")).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    expect(screen.queryAllByRole("option")).toEqual([]);
    // What was typed in the field is there when its way is chosen again. So is what was
    // typed in the field at the foot of the way, which finds an area.
    await way(user, "deep");
    expect(theField()).toHaveValue("pel");
    const area = () => within(panelOf("deep")).getByRole("textbox", { name: FIND_AREA.labelAlone });
    await user.type(area(), "pel");
    await screen.findByRole("group", { name: FIND_AREA.title });
    await user.click(tabOf("quick"));
    expect(tabOf("quick")).toHaveFocus();
    await way(user, "deep");
    expect(area()).toHaveValue("pel");
  });

  test("test_a_search_that_opens_of_the_second_way_hands_the_focus_to_what_is_drawn_and_never_to_nothing", async () => {
    // The tabs go as the search opens, and the button that ranked the settings with them.
    const api = standInApi().on("rank", "rank-default-rent").on("explain_top", "explanations-first");
    const { user } = await openSearch(api);
    await way(user, "deep");
    await tabTo(user, () => within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank }));

    await user.keyboard("{Enter}");
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    await settled();

    expect(waysIfAny()).toBeNull();
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
  });

});

describe("the focus, when a first ranking does not come", () => {
  // A search opens of the press that asks for a first ranking: the two ways in go, and what
  // was pressed may go with them, so the focus is handed on. Where the ranking does not
  // come the search closes again, the two ways in are back, and what was handed the focus
  // goes in its turn. The failure is said in the way the person is in. The focus is on what
  // was pressed, where that is drawn again where it stood, as the button that ranks the
  // settings is, and else on the tab of that way: never on nothing.
  const failing = () => standInApi().on("rank", "error-internal").on("search_places", "places-search");
  const failure = () => screen.getByRole("alert");
  const listOf = (field: HTMLElement) => document.getElementById(field.getAttribute("aria-controls") ?? "") as HTMLElement;

  /**
   * Each way a first ranking is asked for by a control, with the way in it is asked from,
   * and what has the focus once the search has closed again.
   */
  const ASKED = [
    {
      by: "the button that ranks the settings",
      from: "deep",
      ask: async (user: User) => {
        await way(user, "deep");
        await user.click(within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank }));
      },
      // It is held in sight, and is drawn again where it stood.
      then: () => within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank }),
    },
    {
      by: "a word added from the shelf",
      from: "quick",
      ask: async (user: User) => {
        await helper(user, "word");
        await user.click(within(screen.getByRole("region", { name: SHELF.title })).getAllByRole("button")[0] as HTMLElement);
        await user.click(screen.getByRole("button", { name: new RegExp(`^${SHELF.add}`) }));
      },
      // The card of the word went with the press.
      then: () => tabOf("quick"),
    },
  ] as const;

  test.each(ASKED)("test_the_focus_is_on_what_was_pressed_or_on_the_tab_of_the_way_the_person_is_in_when_it_was_asked_for_by_$by", async ({ from, ask, then }) => {
    const { user, api } = await openSearch(failing());

    await ask(user);
    await settled();

    // No search opened of the press: the two ways in stand, with the one it was asked from chosen.
    expect(api.callsTo("rank")).toHaveLength(1);
    expect(tabOf(from)).toHaveAttribute("aria-selected", "true");
    expect(panelOf(from)).toContainElement(failure());
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    expect(then()).toHaveFocus();
  });

  test.each(ASKED)("test_tried_again_and_again_the_focus_is_never_left_on_nothing_when_it_was_asked_for_by_$by", async ({ from, ask }) => {
    const { user, api } = await openSearch(failing());
    await ask(user);
    await settled();

    // What is pressed goes with the press each time, and what takes the focus from it, Search,
    // goes when the search closes again where the second way in is chosen.
    for (const time of [1, 2]) {
      await user.click(within(failure()).getByRole("button", { name: PROMPT.tryAgain }));
      await settled();

      expect([time, api.callsTo("rank").length]).toEqual([time, time + 1]);
      expect([time, waysIfAny() !== null, tabOf(from).getAttribute("aria-selected")]).toEqual([time, true, "true"]);
      expect([time, panelOf(from).contains(failure())]).toEqual([time, true]);
      expect([time, theFocusIsOnWhatIsDrawn()]).toEqual([time, true]);
    }
  });

  test.each(ASKED)("test_tried_again_by_keyboard_once_the_service_answers_the_search_opens_with_the_focus_on_search_when_it_was_asked_for_by_$by", async ({ ask }) => {
    const { user, api } = await openSearch(failing());
    await ask(user);
    await settled();
    api.on("rank", "rank-default-rent").on("explain_top", "explanations-first");

    await tabTo(user, () => within(failure()).getByRole("button", { name: PROMPT.tryAgain }));
    await user.keyboard("{Enter}");
    await settled();

    expect(waysIfAny()).toBeNull();
    expect(results().length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: PROMPT.submit })).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
  });

  test("test_a_place_picked_in_the_settings_before_a_search_asks_for_no_ranking_of_the_page_and_the_focus_is_never_left_on_nothing", async () => {
    // A place was picked from the field the second way in asked first, and a search opened
    // of it. The field that finds a place stands among the settings now, under the
    // journeys: what is chosen there is kept until the button makes the search, and where
    // the service cannot take it the failure is said in the way the person is in.
    const { user, api } = await openSearch(failing());
    await way(user, "deep");
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });
    await user.type(field, "pel");
    await within(listOf(field)).findAllByRole("option");

    await user.keyboard("{Home}{Enter}");
    await settled();

    expect(api.callsTo("rank").map((call) => (call.body as { limit: number }).limit)).toEqual([1]);
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    expect(panelOf("deep")).toContainElement(failure());
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    expect(document.activeElement).not.toBe(document.body);
  });

  test("test_a_setting_that_was_moved_keeps_the_focus_when_its_ranking_does_not_come", async () => {
    // The settings stay where they are as a search opens of one, and as it closes again.
    const { user, api } = await openSearch(failing());
    await settingsAt(user, SETTINGS.money);
    const firm = within(theSettings()).getByRole("checkbox", { name: BUDGET.firm });

    await user.click(firm);
    await settled();

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    expect(panelOf("deep")).toContainElement(failure());
    expect(within(theSettings()).getByRole("checkbox", { name: BUDGET.firm })).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
  });

  test.each(["deep", "quick"] as const)(
    "test_start_again_beside_the_failure_brings_the_first_way_back_with_the_focus_in_the_box: asked from %s",
    async (from) => {
      const { user } = await openSearch(failing());
      await (ASKED.find((one) => one.from === from) ?? ASKED[0]).ask(user);
      await settled();

      await user.click(within(failure()).getByRole("button", { name: PROMPT.startAgain }));
      await settled();

      expect(screen.queryByRole("alert")).toBeNull();
      expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
      expect(promptBox()).toHaveFocus();
      expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    },
  );

  test("test_a_page_that_opens_takes_no_focus_whichever_way_is_chosen_after", async () => {
    // What hands the focus on as a search closes is for a search that was open. A page
    // that has only opened had none, and a person begins at its head, as on any page.
    await openSearch();

    expect(document.body).toHaveFocus();
  });
});

describe("what a way in holds, while the other is chosen", () => {
  test("test_changing_way_keeps_what_was_typed_what_was_chosen_and_what_was_opened", async () => {
    const { user, api } = await openSearch(firstSearch());
    const box = promptBox();
    await user.type(box, "leafy and quiet, near a par");
    box.setSelectionRange(5, 9);

    await way(user, "deep");
    await user.click(within(panelOf("deep")).getAllByRole("radio", { name: TENURE_CHOICE.buy })[0] as HTMLElement);
    const closed = within(theSettings()).getAllByRole("button", { expanded: false })[0] as HTMLElement;
    await user.click(closed);
    await way(user, "quick");

    // It is the box it was, with what was typed in it, and what was selected is selected.
    expect(promptBox()).toBe(box);
    expect(box).toHaveValue("leafy and quiet, near a par");
    expect([box.selectionStart, box.selectionEnd]).toEqual([5, 9]);

    await way(user, "deep");
    expect(within(panelOf("deep")).getAllByRole("radio", { name: TENURE_CHOICE.buy })[0]).toBeChecked();
    expect(closed).toHaveAttribute("aria-expanded", "true");
    expect(api.callsTo("interpret")).toEqual([]);
    expect(api.callsTo("rank")).toEqual([]);
  });
});
