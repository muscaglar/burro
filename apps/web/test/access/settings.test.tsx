/**
 * The settings, which are one stack of bars that fold, and the part that
 * holds them once a search is open, "Refine search", held to
 * docs/design/web.md section 9: every bar is a button that says whether its
 * group is open and names what it opens, a keyboard reaches each and opens
 * and closes it, and the focus is never left on nothing when what holds it is
 * folded.
 *
 * The tests beside the settings and beside the fold hold each alone. These
 * hold them in the whole page, where a person meets them: in the second way
 * in before a search, and under "Refine search" after one.
 *
 * axe runs here in jsdom and cannot judge contrast, size or layout.
 */

import { act, fireEvent, screen, within } from "@testing-library/react";

import { A_COUPLE, groupsOf } from "@/components/SettingsPanel/groups";
import { OPENS_AT_FIRST } from "@/components/SettingsPanel/look";
import { PLACE } from "@/content/search";
import { HIDDEN, JOURNEY, SETTINGS } from "@/content/settings";
import { REFINE } from "@/content/ways";
import { recordedAnswer, responseFrom } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { setOnline } from "../support/api";
import { faultsIn } from "../support/axe";
import {
  areas,
  firstSearch,
  meta,
  openSearch,
  results,
  search,
  settingsAt,
  settled,
  tabOf,
  theSettings,
  theSettingsIfAny,
  way,
  whatRefines,
} from "../support/search";
import { focusGoesOnlyToWhatIsDrawn, theFocusIsOnWhatIsDrawn } from "./drawn";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

type User = Awaited<ReturnType<typeof openSearch>>["user"];

const first = recordedAnswer("rank", "rank-first").body.data;
const CONTROLS = "a[href], button, input, select, textarea";

beforeEach(() => {
  setOnline(true);
  focusGoesOnlyToWhatIsDrawn();
});

/** Where the settings stand: in the second way in before a search, and under what refines one after it. */
const STAND = [
  { where: "before a search, in the second way in", searched: false },
  { where: "once a search is open, under what refines it", searched: true },
] as const;

/** Opens the page and brings the settings into sight where they stand, as they first stand. */
async function settingsWhere(searched: boolean) {
  const opened = await openSearch();
  if (searched) await search(opened.user);
  await settingsAt(opened.user);
  return opened;
}

/** The groups the settings hold, by name, in the order they stand in: of the search as it stands. */
const groups = (searched: boolean) =>
  groupsOf(searched ? first.spec : meta.data.defaults.rent, meta.data, areas, {}).map((group) => group.label);

/** The bar of a group, by the name of the group. */
const barOf = (group: string) => within(theSettings()).getByRole("button", { name: group });
/** What the bar of a group opens, which the bar names. */
const heldBy = (bar: HTMLElement) => document.getElementById(bar.getAttribute("aria-controls") ?? "") as HTMLElement;
const isOpen = (bar: HTMLElement) => bar.getAttribute("aria-expanded") === "true";

/** Presses Tab until the focus is on the element, and says how many presses it took. */
async function tabTo(user: User, wanted: () => Element | null) {
  for (let presses = 0; presses < 400; presses += 1) {
    if (document.activeElement !== null && document.activeElement === wanted()) return presses;
    await user.tab();
  }
  throw new Error("Tab never reached it.");
}

/** Every stop of the keyboard, from the head of the page to its foot, as Tab comes to them. */
async function everyStop(user: User): Promise<Element[]> {
  const stops: Element[] = [];
  act(() => (document.activeElement as HTMLElement | null)?.blur());
  for (let presses = 0; presses < 600; presses += 1) {
    await user.tab();
    if (document.activeElement === null || document.activeElement === document.body) return stops;
    stops.push(document.activeElement);
  }
  throw new Error("Tab never came to the foot of the page.");
}

/**
 * A press as a browser makes it that gives no focus to a button that is pressed, as some
 * do: what was pressed hears the press, and the focus is where it was.
 */
const pressWithNoFocus = (on: HTMLElement) => fireEvent.click(on);

describe("the groups of the settings, to whoever hears the page", () => {
  test.each(STAND)("test_every_bar_is_a_button_that_says_whether_its_group_is_open_and_names_what_it_opens: $where", async ({ searched }) => {
    await settingsWhere(searched);

    expect(groups(searched).length).toBeGreaterThanOrEqual(8);
    for (const group of groups(searched)) {
      const bar = barOf(group);
      // A native button, named for its group and for nothing else, which says in so many
      // words whether the group is open, and which part of the page it opens.
      expect([group, bar.tagName, bar.getAttribute("type")]).toEqual([group, "BUTTON", "button"]);
      expect(bar).toHaveAccessibleName(group);
      expect([group, ["true", "false"].includes(bar.getAttribute("aria-expanded") ?? "")]).toEqual([group, true]);
      expect([group, heldBy(bar) !== null, theSettings().contains(heldBy(bar))]).toEqual([group, true, true]);
      expect(bar).toHaveClass("target");
      // What it says is so: an open group is drawn, and holds what is pressed or typed in.
      // A closed one is not drawn, and holds nothing that a keyboard could come to.
      const held = heldBy(bar).querySelectorAll(CONTROLS).length;
      if (isOpen(bar)) {
        expect(heldBy(bar)).toBeVisible();
        expect([group, held > 0]).toEqual([group, true]);
      } else {
        expect(heldBy(bar)).not.toBeVisible();
        expect([group, held]).toEqual([group, 0]);
      }
    }
  });

  test.each(STAND)("test_the_groups_that_stand_open_at_first_say_so_and_every_other_says_that_it_is_closed: $where", async ({ searched }) => {
    await settingsWhere(searched);

    const open = groups(searched).filter((group) => isOpen(barOf(group)));

    // Before a search the first two, so that it is seen that a group opens and closes.
    // Once one is open, as the website is left, none: the bar of each says what it holds.
    // By one line a couple stand open then, of which those that hold what was asked for
    // come first: this search holds a budget and a journey, which are the first two as well.
    if (!searched || OPENS_AT_FIRST === "a-couple") {
      expect(open).toEqual(groups(searched).slice(0, A_COUPLE));
      expect(open).toEqual([SETTINGS.money, SETTINGS.journeys]);
    } else if (OPENS_AT_FIRST === "none") {
      expect(open).toEqual([]);
    } else {
      expect(open.length).toBeGreaterThanOrEqual(A_COUPLE);
    }
    expect(open.length).toBeLessThan(groups(searched).length);
    // Each says which it is, in so many words, whichever it is.
    for (const group of groups(searched)) {
      expect([group, barOf(group).getAttribute("aria-expanded")]).toEqual([group, String(open.includes(group))]);
    }
  });

  test("test_what_a_bar_says_its_group_holds_describes_the_bar_and_is_no_part_of_its_name", async () => {
    await settingsWhere(true);
    const said = groupsOf(first.spec, meta.data, areas, {}).filter((group) => group.holds !== null);

    // This search holds a budget, a journey and two vibes: the bars of their groups say so.
    expect(said.length).toBeGreaterThanOrEqual(3);
    for (const group of said) {
      expect(barOf(group.label)).toHaveAccessibleName(group.label);
      expect([group.label, (barOf(group.label).getAttribute("aria-describedby") ?? "") !== ""]).toEqual([group.label, true]);
      const described = document.getElementById(barOf(group.label).getAttribute("aria-describedby") ?? "");
      expect([group.label, (described?.textContent ?? "").length > 0]).toEqual([group.label, true]);
      expect(barOf(group.label)).toContainElement(described);
    }
    // A bar of a group that holds nothing a person asked for says nothing of what it holds.
    const silent = groupsOf(first.spec, meta.data, areas, {}).filter((group) => group.holds === null);
    expect(silent.length).toBeGreaterThan(0);
    for (const group of silent) expect(barOf(group.label)).not.toHaveAttribute("aria-describedby");
  });

  test("test_before_a_search_a_bar_says_nothing_that_was_asked_for_and_only_what_is_counted_in_every_search", async () => {
    await settingsWhere(false);
    const held = groupsOf(meta.data.defaults.rent, meta.data, areas, {});

    // Nobody has asked for anything: what a bar says, where it says anything, is what
    // Burro counts in every search, which nobody chose. It describes the bar, and the bar
    // is still found by the name of its group and by nothing else.
    expect(held.filter((group) => group.asked)).toEqual([]);
    expect(held.filter((group) => group.usual.length > 0).length).toBeGreaterThan(0);
    for (const group of held) {
      expect(barOf(group.label)).toHaveAccessibleName(group.label);
      expect([group.label, barOf(group.label).textContent]).toEqual([group.label, `${group.label}${group.holds ?? ""}`]);
      if (group.usual.length === 0) {
        expect(barOf(group.label)).not.toHaveAttribute("aria-describedby");
        expect([group.label, group.holds]).toEqual([group.label, null]);
      } else {
        expect(barOf(group.label)).toHaveAccessibleDescription(group.holds ?? "");
        for (const name of group.usual) expect([group.label, name, (group.holds ?? "").includes(name)]).toEqual([group.label, name, true]);
      }
    }
  });

  test.each(STAND)("test_the_settings_as_they_first_stand_have_no_fault: $where", async ({ searched }) => {
    const { container } = await settingsWhere(searched);

    // Before a search a couple of groups stand open, and once one is open none need.
    const open = groups(searched).filter((group) => isOpen(barOf(group)));
    if (!searched) expect(open.length).toBeGreaterThan(0);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test.each(STAND)("test_the_settings_with_a_couple_of_groups_open_have_no_fault: $where", async ({ searched }) => {
    // Whatever stands open at first, a person opens what they came for: the first two, as
    // they stand before a search, are held open after one too.
    const { container, user } = await settingsWhere(searched);
    for (const group of groups(searched).slice(0, A_COUPLE)) if (!isOpen(barOf(group))) await user.click(barOf(group));

    expect(groups(searched).filter((group) => isOpen(barOf(group))).length).toBeGreaterThanOrEqual(A_COUPLE);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test.each(STAND)("test_the_settings_with_every_group_closed_have_no_fault: $where", async ({ searched }) => {
    const { container, user } = await settingsWhere(searched);
    for (const group of groups(searched)) if (isOpen(barOf(group))) await user.click(barOf(group));

    expect(groups(searched).filter((group) => isOpen(barOf(group)))).toEqual([]);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("the groups of the settings, by keyboard", () => {
  test.each(STAND)("test_tab_comes_to_every_bar_in_the_order_the_groups_stand_in: $where", async ({ searched }) => {
    const { user } = await settingsWhere(searched);

    const stops = await everyStop(user);
    const bars = groups(searched).map(barOf);

    expect(stops.filter((stop) => bars.includes(stop as HTMLElement))).toEqual(bars);
    // No bar is taken out of the order of the keyboard, open or closed.
    for (const bar of bars) expect(bar).not.toHaveAttribute("tabindex");
  });

  test.each(STAND)("test_enter_and_space_open_and_close_a_group_and_the_focus_stays_on_its_bar: $where", async ({ searched }) => {
    const { user, api } = await settingsWhere(searched);
    const sent = api.calls.length;
    const [closed] = groups(searched).filter((group) => !isOpen(barOf(group)));
    const bar = barOf(closed as string);
    await tabTo(user, () => bar);

    await user.keyboard("{Enter}");
    expect(bar).toHaveAttribute("aria-expanded", "true");
    expect(bar).toHaveFocus();
    // What it opened is the next stop of the keyboard, and the bar is the stop before it.
    await user.tab();
    expect(heldBy(bar)).toContainElement(document.activeElement as HTMLElement);
    await user.tab({ shift: true });
    expect(bar).toHaveFocus();

    await user.keyboard(" ");
    expect(bar).toHaveAttribute("aria-expanded", "false");
    expect(bar).toHaveFocus();
    expect(heldBy(bar).querySelectorAll(CONTROLS)).toHaveLength(0);
    // Closed, the next stop is the bar of the group after it.
    await user.tab();
    const after = groups(searched)[groups(searched).indexOf(closed as string) + 1];
    expect(document.activeElement).toBe(barOf(after as string));
    // To open a group and to close it asks nothing of the service, and ranks nothing.
    expect(api.calls).toHaveLength(sent);
  });

  test.each(STAND)("test_a_group_opened_or_closed_moves_no_other_group: $where", async ({ searched }) => {
    const { user } = await settingsWhere(searched);
    const was = groups(searched).map((group) => isOpen(barOf(group)));
    const at = was.indexOf(false);

    await tabTo(user, () => barOf(groups(searched)[at] as string));
    await user.keyboard("{Enter}");

    expect(groups(searched).map((group) => isOpen(barOf(group)))).toEqual(was.map((open, other) => (other === at ? true : open)));
  });
});

describe("the focus, when a group is folded over it", () => {
  /** The bar of the money, with its group open: it stands open before a search, and is opened once one is open. */
  async function theMoneyOpen(user: User) {
    const bar = barOf(SETTINGS.money);
    if (!isOpen(bar)) await user.click(bar);
    expect(bar).toHaveAttribute("aria-expanded", "true");
    return bar;
  }

  test.each(STAND)("test_a_bar_pressed_while_the_focus_is_in_its_group_has_the_focus_as_the_group_goes: $where", async ({ searched }) => {
    const { user } = await settingsWhere(searched);
    const bar = await theMoneyOpen(user);
    await tabTo(user, () => bar);
    await user.tab();
    expect(heldBy(bar)).toContainElement(document.activeElement as HTMLElement);

    await user.click(bar);

    expect(bar).toHaveAttribute("aria-expanded", "false");
    expect(bar).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
  });

  test.each(STAND)(
    "test_it_has_the_focus_in_a_browser_that_gives_none_to_a_button_that_is_pressed_too: $where",
    async ({ searched }) => {
      // Not every browser gives the focus to a button that is pressed. What had the focus
      // goes with the group, and in such a browser the focus was left on nothing.
      const { user } = await settingsWhere(searched);
      const bar = await theMoneyOpen(user);
      await tabTo(user, () => bar);
      await user.tab();
      expect(heldBy(bar)).toContainElement(document.activeElement as HTMLElement);

      pressWithNoFocus(bar);

      expect(bar).toHaveAttribute("aria-expanded", "false");
      expect(theFocusIsOnWhatIsDrawn()).toBe(true);
      expect(bar).toHaveFocus();
    },
  );
});

describe("the focus, when what is pressed in a group goes with the press", () => {
  // Seen in a browser, by keyboard, once a search was open: a journey was removed from the
  // settings, and an area that was hidden was shown again. The button that was pressed went
  // when the answer came, and the focus was left on nothing. What goes hands the focus to
  // what stays beside it: here the bar of its group, or where the group itself goes with
  // what it held, the bar of the group before it.
  const ranked = recordedAnswer("rank", "rank-first");
  const sentEdits = (body: unknown) => (body as { operations: Operations }).operations;
  /** The first ranking, as the service would answer it for a search that holds this. */
  const rankedWith = (holds: Partial<PreferenceSpec>, places = ranked.body.data.places) => () =>
    responseFrom({
      ...ranked,
      body: { ...ranked.body, data: { ...ranked.body.data, spec: { ...ranked.body.data.spec, ...holds }, places } },
    });
  const [journey] = first.spec.commutes;
  const PLACES: typeof ranked.body.data.places = [
    ...ranked.body.data.places,
    { place_id: "syn-p0017", name: "Pellam Exchange", kind: "district" },
    { place_id: "syn-p0012", name: "Pellam Cross", kind: "station" },
  ];
  const journeyTo = (placeId: string) => ({ ...(journey as (typeof first.spec.commutes)[number]), place_id: placeId });
  const hidden = (at: number) => ({ area_id: first.ranked[at]?.area_id ?? "", rule: "exclude" as const, provenance: "ui_edit" as const });
  const nameAt = (at: number) => areas.find((area) => area.area_id === first.ranked[at]?.area_id)?.name ?? "";

  test("test_the_only_journey_hands_the_focus_to_the_bar_of_the_journeys_which_stays", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.journeys);
    const answer = api.hold("rank", rankedWith({ commutes: [] }, []));
    const remove = () => within(theSettings()).queryByRole("button", { name: JOURNEY.remove("Cindermoor Works") });
    await tabTo(user, remove);

    await user.keyboard("{Enter}");

    // At the press, before the answer: the button is there still, and will go.
    expect(remove()).not.toBeNull();
    expect(barOf(SETTINGS.journeys)).toHaveFocus();
    answer.release();
    await settled();

    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeRemove(journey?.place_id ?? ""));
    expect(remove()).toBeNull();
    expect(barOf(SETTINGS.journeys)).toHaveFocus();
    expect(barOf(SETTINGS.journeys)).toHaveAttribute("aria-expanded", "true");
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
  });

  test("test_one_journey_of_several_hands_the_focus_to_what_removes_the_journey_beside_it", async () => {
    const three = [journey?.place_id ?? "", "syn-p0017", "syn-p0012"].map(journeyTo);
    const { user, api } = await openSearch(firstSearch().on("rank", rankedWith({ commutes: three }, PLACES)));
    await search(user);
    await settingsAt(user, SETTINGS.journeys);
    const remove = (place: string) => within(theSettings()).queryByRole("button", { name: JOURNEY.remove(place) });

    // The first of three: the next one along comes to stand where it stood.
    const two = api.hold("rank", rankedWith({ commutes: three.slice(1) }, PLACES));
    await tabTo(user, () => remove("Cindermoor Works"));
    await user.keyboard("{Enter}");
    expect(remove("Pellam Exchange")).toHaveFocus();
    two.release();
    await settled();
    expect(remove("Cindermoor Works")).toBeNull();
    expect(remove("Pellam Exchange")).toHaveFocus();

    // The last of those that are left: the one before it.
    const one = api.hold("rank", rankedWith({ commutes: three.slice(1, 2) }, PLACES));
    await tabTo(user, () => remove("Pellam Cross"));
    await user.keyboard("{Enter}");
    expect(remove("Pellam Exchange")).toHaveFocus();
    one.release();
    await settled();

    expect(remove("Pellam Cross")).toBeNull();
    expect(remove("Pellam Exchange")).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    // No journey says which place it is to in anything but its words.
    const marked = [...theSettings().querySelectorAll("[data-journey], [data-removes]")].flatMap((one) => [
      one.getAttribute("data-journey"),
      one.getAttribute("data-removes"),
    ]);
    expect(marked.filter((mark) => mark !== null && mark !== "")).toEqual([]);
  });

  test("test_the_last_place_that_can_be_named_hands_the_focus_to_the_bar_of_the_journeys_as_its_field_goes", async () => {
    // The field gives way to the line that says no more places can be named.
    const most = meta.data.limits.max_commutes;
    const two = [journey?.place_id ?? "", "syn-p0017"].map(journeyTo);
    expect(most).toBe(two.length + 1);
    const { user, api } = await openSearch(firstSearch().on("rank", rankedWith({ commutes: two }, PLACES)));
    await search(user);
    await settingsAt(user, SETTINGS.journeys);
    const answer = api.hold("rank", rankedWith({ commutes: [...two, journeyTo("syn-p0012")] }, PLACES));
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });
    await tabTo(user, () => field);

    await user.keyboard("pel");
    await within(document.getElementById(field.getAttribute("aria-controls") ?? "") as HTMLElement).findAllByRole("option");
    await user.keyboard("{Home}{Enter}");
    expect(barOf(SETTINGS.journeys)).toHaveFocus();
    answer.release();
    await settled();

    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.placeAdd("syn-p0012"));
    expect(within(theSettings()).queryByRole("combobox", { name: PLACE.label })).toBeNull();
    expect(within(heldBy(barOf(SETTINGS.journeys))).getByText(PLACE.full(most))).toBeVisible();
    expect(barOf(SETTINGS.journeys)).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
  });

  test("test_a_place_that_is_not_the_last_leaves_the_focus_in_the_field_as_it_did", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.journeys);
    api.on("rank", rankedWith({ commutes: [journey?.place_id ?? "", "syn-p0012"].map(journeyTo) }, PLACES));
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });

    await user.type(field, "pel");
    await within(document.getElementById(field.getAttribute("aria-controls") ?? "") as HTMLElement).findAllByRole("option");
    await user.keyboard("{Home}{Enter}");
    await settled();

    expect(within(theSettings()).getByRole("combobox", { name: PLACE.label })).toBe(field);
    expect(field).toHaveFocus();
  });

  test("test_an_area_that_is_shown_again_hands_the_focus_to_the_one_beside_it_and_the_last_of_them_to_the_bar_before", async () => {
    const { user, api } = await openSearch(firstSearch().on("rank", rankedWith({ areas: [hidden(0), hidden(1)] })));
    await search(user);
    await settingsAt(user, HIDDEN.legend);
    const show = (at: number) => within(theSettings()).queryByRole("button", { name: HIDDEN.show(nameAt(at)) });
    const before = groups(true).at(-1) as string;

    // One of two: the focus goes to the other, which stays.
    const one = api.hold("rank", rankedWith({ areas: [hidden(1)] }));
    await tabTo(user, () => show(0));
    await user.keyboard("{Enter}");
    expect(show(1)).toHaveFocus();
    one.release();
    await settled();
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.areaClear(first.ranked[0]?.area_id ?? ""));
    expect(show(0)).toBeNull();
    expect(show(1)).toHaveFocus();

    // The last of them: its group goes with it, and the focus goes to the bar of the group before.
    const none = api.hold("rank", rankedWith({ areas: [] }));
    await user.keyboard("{Enter}");
    expect(barOf(before)).toHaveFocus();
    none.release();
    await settled();

    expect(within(theSettings()).queryByRole("button", { name: HIDDEN.legend })).toBeNull();
    expect(barOf(before)).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
  });
});

describe("the part that refines a search", () => {
  test("test_it_is_a_button_that_says_whether_the_settings_are_open_and_names_what_it_opens", async () => {
    const { user } = await openSearch();
    await search(user);
    const refine = whatRefines() as HTMLElement;

    expect([refine.tagName, refine.getAttribute("type")]).toEqual(["BUTTON", "button"]);
    expect(refine).toHaveAccessibleName(REFINE.label);
    expect(refine).toHaveClass("target");
    expect(refine).not.toHaveAttribute("tabindex");
    // Closed at first: it says so, and what it would open is on the page, not drawn, and holds nothing.
    expect(refine).toHaveAttribute("aria-expanded", "false");
    expect(heldBy(refine)).not.toBeVisible();
    expect(heldBy(refine).querySelectorAll(CONTROLS)).toHaveLength(0);
    expect(theSettingsIfAny()).toBeNull();

    await tabTo(user, () => refine);
    await user.keyboard("{Enter}");

    expect(refine).toHaveAttribute("aria-expanded", "true");
    expect(refine).toHaveFocus();
    expect(heldBy(refine)).toBeVisible();
    expect(heldBy(refine)).toContainElement(theSettings());
    // The settings are the next stop of the keyboard, and what opened them the stop before.
    await user.tab();
    expect(theSettings()).toContainElement(document.activeElement as HTMLElement);
    await user.tab({ shift: true });
    expect(refine).toHaveFocus();

    await user.keyboard(" ");
    expect(refine).toHaveAttribute("aria-expanded", "false");
    expect(refine).toHaveFocus();
    expect(theSettingsIfAny()).toBeNull();
  });

  test("test_closed_it_is_one_stop_of_the_keyboard_after_what_was_understood_and_before_the_first_result", async () => {
    const { user } = await openSearch();
    await search(user);
    const refine = whatRefines() as HTMLElement;

    const stops = await everyStop(user);
    const at = stops.indexOf(refine);
    const inTheResult = stops.findIndex((stop) => results()[0]?.contains(stop));
    const inTheSearch = stops.map((stop) => screen.getByRole("region", { name: /^Your search$/ }).contains(stop)).lastIndexOf(true);

    expect(stops.filter((stop) => stop === refine)).toHaveLength(1);
    expect(inTheSearch).toBeGreaterThan(0);
    expect(at).toBeGreaterThan(inTheSearch);
    expect(at).toBeLessThan(inTheResult);
    // Nothing of what it holds is a stop while it is closed.
    expect(stops.filter((stop) => heldBy(refine).contains(stop))).toEqual([]);
  });

  test("test_pressed_while_the_focus_is_in_the_settings_it_has_the_focus_as_they_go", async () => {
    const { user } = await openSearch();
    await search(user);
    await settingsAt(user);
    const refine = whatRefines() as HTMLElement;
    await tabTo(user, () => barOf(SETTINGS.journeys));

    await user.click(refine);

    expect(refine).toHaveAttribute("aria-expanded", "false");
    expect(refine).toHaveFocus();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
  });

  test("test_it_has_the_focus_in_a_browser_that_gives_none_to_a_button_that_is_pressed_too", async () => {
    const { user } = await openSearch();
    await search(user);
    await settingsAt(user);
    const refine = whatRefines() as HTMLElement;
    await tabTo(user, () => barOf(SETTINGS.journeys));

    pressWithNoFocus(refine);

    expect(refine).toHaveAttribute("aria-expanded", "false");
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    expect(refine).toHaveFocus();
  });

  test("test_before_a_search_what_would_open_and_close_the_settings_is_no_stop_and_is_heard_by_nobody", async () => {
    // The settings stand open in the second way in, and nothing opens or closes them.
    const { user } = await openSearch();
    await way(user, "deep");

    expect(whatRefines()).toBeNull();
    expect(screen.queryByText(REFINE.label)).not.toBeVisible();
    const stops = await everyStop(user);
    expect(stops.filter((stop) => (stop.textContent ?? "").includes(REFINE.label))).toEqual([]);
    expect(stops).toContain(tabOf("deep"));
    expect(stops.filter((stop) => theSettings().contains(stop)).length).toBeGreaterThan(10);
  });
});
