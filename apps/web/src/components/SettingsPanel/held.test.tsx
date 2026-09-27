import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DIMENSION } from "@/content/labels";
import { KIND_OF_SEARCH, SETTINGS } from "@/content/settings";
import { failed } from "@/lib/api/failure";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { SEEN } from "./held";
import { SettingsPanel } from "./SettingsPanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** "Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works", as it was ranked. */
const first = recordedAnswer("rank", "rank-first").body.data.spec;
/** The same, with recorded burglary and theft switched on, as the service answered the switch. */
const theftOn = recordedAnswer("rank", "rank-crime-switched-on").body.data.spec;
const NAMED = { "syn-p0021": "Cindermoor Works" } as const;
const THEFT = "Less recorded burglary and theft";

/**
 * A browser, as far as the settings ask one: where each thing stands in the window, and
 * how far the page was told to go. jsdom lays nothing out, so a test says where things
 * stand. Everything stands `at` down the window, and what stands under the bars that
 * grew stands lower by as much as they grew.
 */
function aBrowser() {
  const page = { at: 300, grew: 0, scrolled: 0 };
  const moved: number[] = [];
  const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
    // A bar stands over what it opens: it does not go down the page as it grows.
    const top = page.at + (this.matches("button[data-rest]") ? 0 : page.grew) - page.scrolled;
    return { top, bottom: top + 44, left: 0, right: 0, x: 0, y: top, width: 0, height: 44, toJSON: () => ({}) };
  });
  const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((to: ScrollToOptions | number, by?: number) => {
    const went = typeof to === "number" ? (by ?? 0) : (to.top ?? 0);
    moved.push(went);
    page.scrolled += went;
  }) as typeof window.scrollBy);
  return {
    page,
    moved,
    /** A person scrolls the page by so much, as with a wheel. */
    scrolls: (by: number) => {
      page.scrolled += by;
      act(() => void fireEvent.scroll(window));
    },
    putBack: () => {
      measure.mockRestore();
      scroll.mockRestore();
    },
  };
}

/**
 * The settings, of a search that is open unless it is said that none is. Before a search
 * the page says so: what was chosen there is gathered, and is a search the API returned.
 */
function show(spec: PreferenceSpec = first, begun = true) {
  const sent: Operations[] = [];
  const panel = (shown: PreferenceSpec, at: number, open = begun, busy = false) => (
    <SettingsPanel
      spec={shown}
      meta={meta}
      areas={areas}
      placeNames={NAMED}
      onEdit={(operations) => sent.push(operations)}
      onTenure={() => undefined}
      searchPlaces={() => Promise.resolve(failed("offline"))}
      onAddPlace={() => undefined}
      version={at}
      open
      onToggle={() => undefined}
      standing
      begun={open}
      busy={busy}
    />
  );
  const view = render(panel(spec, 1));
  const user = userEvent.setup({ delay: null });
  const open = async (...names: string[]) => {
    for (const name of names) {
      const button = screen.getByRole("button", { name });
      if (button.getAttribute("aria-expanded") !== "true") await user.click(button);
    }
  };
  return {
    ...view,
    sent,
    user,
    open,
    /** The settings are drawn again: with the answer to a press, or as the search changed elsewhere. */
    again: (next: PreferenceSpec, at: number, open = begun, busy = false) => view.rerender(panel(next, at, open, busy)),
  };
}

describe("what is pressed in the settings is held where it stands", () => {
  let browser: ReturnType<typeof aBrowser>;
  beforeEach(() => {
    browser = aBrowser();
  });
  afterEach(() => browser.putBack());

  test("test_as_the_answer_to_a_press_moves_what_stands_over_it_the_page_goes_by_as_much", async () => {
    // Measured in a browser at 390 by 844: a thing was turned on, the bar of its group came
    // to name it on a line more, and the switch went 21.5 px down from under the press.
    const { open, user, sent, again } = show();
    await open(DIMENSION.crime);

    await user.click(screen.getByRole("switch", { name: THEFT }));
    expect(sent).toEqual([edits.featureOn("crime_burglary_theft")]);
    expect(browser.moved).toEqual([]);
    browser.page.grew = 21.5;
    again(theftOn, 2);

    expect(browser.moved).toEqual([21.5]);
    // It stands in the window where it stood as it was pressed.
    expect(screen.getByRole("switch", { name: THEFT }).getBoundingClientRect().top).toBe(300);
  });

  test("test_it_is_held_as_it_is_turned_off_and_what_stood_over_it_gives_room_back", async () => {
    const { open, user, again } = show(theftOn);
    await open(DIMENSION.crime);
    browser.page.grew = 21.5;

    await user.click(screen.getByRole("switch", { name: THEFT }));
    browser.page.grew = 0;
    again(first, 2);

    expect(browser.moved).toEqual([-21.5]);
  });

  test("test_the_page_stays_where_it_is_where_nothing_moved_what_was_pressed", async () => {
    const { open, user, again } = show();
    await open(DIMENSION.crime);

    await user.click(screen.getByRole("switch", { name: THEFT }));
    again(theftOn, 2);

    expect(browser.moved).toEqual([]);
    // Nor for what a browser rounds, which is not seen.
    expect(SEEN).toBe(0.5);
    await user.click(screen.getByRole("switch", { name: THEFT }));
    browser.page.grew = 0.25;
    again(first, 3);
    expect(browser.moved).toEqual([]);
  });

  test("test_it_is_held_by_keyboard_as_by_a_press", async () => {
    const { open, user, again } = show();
    await open(DIMENSION.crime);
    screen.getByRole("switch", { name: THEFT }).focus();

    await user.keyboard(" ");
    browser.page.grew = 43;
    again(theftOn, 2);

    expect(browser.moved).toEqual([43]);
  });

  test("test_before_a_search_it_is_held_as_what_was_chosen_is_gathered_and_the_bar_of_its_group_comes_to_say_so", async () => {
    // Measured in a browser at 390 by 844, in Deep search: "Visiting" went 21.5 px down
    // from under the press, and so did a thing that was turned on.
    const { open, user, again } = show(meta.defaults.rent, false);
    await open(SETTINGS.money);

    await user.click(screen.getByRole("radio", { name: KIND_OF_SEARCH.visit }));
    browser.page.grew = 21.5;
    again({ ...meta.defaults.rent, tenure: "visit", tenure_from: "ui_edit" }, 2);

    expect(browser.moved).toEqual([21.5]);
  });

  test("test_as_a_search_opens_of_the_press_the_page_holds_what_was_pressed_and_the_settings_ask_nothing", async () => {
    // Where the look has a setting make the search, the heading and the tabs over the
    // settings go as it opens, and the page goes by as much, or brings the answer into sight
    // instead: which of the two is the page's to choose. Asked of both, the page went twice.
    const { open, user, again } = show(meta.defaults.rent, false);
    await open(SETTINGS.money);

    await user.click(screen.getByRole("radio", { name: KIND_OF_SEARCH.visit }));
    // The search opens of the press, and what stood over the settings goes.
    browser.page.grew = -478;
    again(meta.defaults.rent, 1, true);
    expect(browser.moved).toEqual([]);
    // And the answer is drawn.
    again({ ...meta.defaults.rent, tenure: "visit", tenure_from: "ui_edit" }, 2, true);
    expect(browser.moved).toEqual([]);

    // Once it is open, a press is held as any is.
    await user.click(screen.getByRole("radio", { name: "Buying" }));
    browser.page.grew = -450;
    again({ ...meta.defaults.buy }, 3, true);
    expect(browser.moved).toEqual([28]);
  });

  test("test_before_a_search_nothing_is_asked_of_the_page_until_what_was_chosen_has_been_gathered", async () => {
    // Until the answer comes nobody knows whether a search opens of the press.
    const { open, user, again } = show(meta.defaults.rent, false);
    await open(SETTINGS.money);

    await user.click(screen.getByRole("radio", { name: KIND_OF_SEARCH.visit }));
    browser.page.grew = 12;
    again(meta.defaults.rent, 1, false);

    expect(browser.moved).toEqual([]);
    again({ ...meta.defaults.rent, tenure: "visit", tenure_from: "ui_edit" }, 2, false);
    expect(browser.moved).toEqual([12]);
  });

  test("test_once_the_answer_is_drawn_it_is_let_go_and_what_changes_later_moves_nothing", async () => {
    const { open, user, again } = show();
    await open(DIMENSION.crime);
    await user.click(screen.getByRole("switch", { name: THEFT }));
    browser.page.grew = 21.5;
    again(theftOn, 2);
    expect(browser.moved).toEqual([21.5]);

    // The search changes elsewhere, as when a sentence is read: the hand is no longer on the switch.
    browser.page.grew = 80;
    again({ ...theftOn, tags: [] }, 3);

    expect(browser.moved).toEqual([21.5]);
  });

  test("test_a_press_that_changes_nothing_of_the_search_holds_nothing", async () => {
    const { open, user, again } = show();
    await open(DIMENSION.crime);

    // A group is opened, and the search then changes elsewhere.
    await user.click(screen.getByRole("button", { name: SETTINGS.airAndNoise }));
    browser.page.grew = 60;
    again(theftOn, 2);

    expect(browser.moved).toEqual([]);
  });

  test("test_where_a_person_scrolls_before_the_answer_comes_it_is_held_where_that_left_it", async () => {
    // The answer may be slow. The page goes where a person takes it, and they are not brought back.
    const { open, user, again } = show();
    await open(DIMENSION.crime);
    await user.click(screen.getByRole("switch", { name: THEFT }));

    browser.scrolls(120);
    again(theftOn, 2);
    expect(browser.moved).toEqual([]);

    await user.click(screen.getByRole("switch", { name: THEFT }));
    browser.scrolls(-40);
    browser.page.grew = 21.5;
    again(first, 3);
    expect(browser.moved).toEqual([21.5]);
  });

  test("test_where_no_answer_comes_it_is_let_go_as_the_asking_ends_and_the_page_is_taken_back_no_more", async () => {
    // Seen in a browser while every ranking failed: with the pointer over a result the wheel
    // could not take the page on. The count of answers stays where it was when a ranking
    // fails, so what was pressed was held at every drawing of the page, for as long as it was open.
    const { open, user, again } = show();
    await open(DIMENSION.crime);
    await user.click(screen.getByRole("switch", { name: THEFT }));

    // The ranking is asked for, and fails: the search is as it was, and what says so is drawn.
    again(first, 1, true, true);
    browser.page.grew = 30;
    again(first, 1, true, false);
    // It is held through the drawing in which the asking ended.
    expect(browser.moved).toEqual([30]);

    // A person takes the page on, and it is drawn again before the browser has said so.
    browser.page.scrolled += 300;
    again(first, 1, true, false);
    expect(browser.moved).toEqual([30]);
  });

  test("test_while_the_answer_is_on_its_way_it_is_held_however_often_the_page_is_drawn", async () => {
    const { open, user, again } = show();
    await open(DIMENSION.crime);
    await user.click(screen.getByRole("switch", { name: THEFT }));

    again(first, 1, true, true);
    browser.page.grew = 12;
    again(first, 1, true, true);
    expect(browser.moved).toEqual([12]);
    browser.page.grew = 21.5;
    again(theftOn, 2, true, false);

    expect(browser.moved).toEqual([12, 9.5]);
  });

  test("test_what_went_from_the_page_with_its_press_holds_nothing", async () => {
    const { open, user, again } = show();
    await open(SETTINGS.journeys);

    await user.click(screen.getByRole("button", { name: /^Remove Cindermoor Works$/ }));
    browser.page.grew = -300;
    again({ ...first, commutes: [] }, 2);

    expect(screen.queryByRole("button", { name: /^Remove Cindermoor Works$/ })).toBeNull();
    expect(browser.moved).toEqual([]);
  });
});
