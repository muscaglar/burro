import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { COMPARE, TRAY } from "@/content/compare";
import { TOWN } from "@/content/town";
import { TOWNS } from "@/content/towns";
import { recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";
import { MOST_COMPARED } from "@/lib/compare/list";
import { SessionProvider } from "@/lib/session/session";
import { marksOf } from "@/lib/town/bands";

import { faultsIn } from "../../../test/support/axe";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { watch } from "../../../test/support/watch";
import { ART } from "@/lib/art/names";

import { OVER_THE_BAR } from "./clear";
import { CompareButton } from "./CompareButton";
import { CompareTray, trayStatus } from "./CompareTray";
import {
  BAR_MAY_SAY_OF_ITS_TOWNS,
  BAR_SAYS,
  BAR_SAYS_OF_ITS_TOWNS,
  CLEAR_MAY_STAND,
  CLEAR_ON_A_NARROW_SCREEN,
  CLEAR_ON_A_NARROW_SCREEN_MAY_BE,
  CLEAR_STANDS,
  WAY_TO_COMPARE,
  type BarSaysOfItsTowns,
  type ClearOnANarrowScreen,
  type ClearStands,
} from "./look";
import { ofATown } from "./town";
import { DOUBLE_PRESS_MS } from "@/lib/sight";

const { areas, bands } = recordedAnswer("list_areas", "areas").body.data;
const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const release = ofATown(meta);
const nameAt = (at: number) => areas[at]?.name ?? "";
/** What the button of an area hands over of its town, as a result and the page of an area do. */
const townAt = (at: number) => ({ release, marks: marksOf(bands, areas[at]?.area_id ?? "") });

interface Shown {
  /** True where each button hands over what the town of its area is drawn from. */
  readonly towns?: boolean;
  /** True where the buttons stand as they do on a result. */
  readonly small?: boolean;
  /** True where each button says beside itself what comparing is, as on the page of an area. */
  readonly invites?: boolean;
  /** Whether the bar has the way to take every area out at once, where a test makes the call the look does not. */
  readonly clears?: ClearStands;
  readonly narrow?: ClearOnANarrowScreen;
  /** What the bar says of its towns, where a test makes the call the look does not. */
  readonly says?: BarSaysOfItsTowns;
}

function show(count = 5, { towns = false, small = false, invites = false, clears, narrow, says }: Shown = {}) {
  const user = userEvent.setup({ delay: null });
  const view = render(
    <SessionProvider>
      <CompareTray
        {...(clears === undefined ? {} : { clears })}
        {...(narrow === undefined ? {} : { narrow })}
        {...(says === undefined ? {} : { says })}
      />
      <ul>
        {areas.slice(0, count).map((area, at) => (
          <li key={area.area_id}>
            <CompareButton area={area} small={small} invites={invites} {...(towns ? { town: townAt(at) } : {})} />
          </li>
        ))}
      </ul>
    </SessionProvider>,
  );
  return { user, ...view };
}

const tray = () => screen.getByRole("region", { name: TRAY.title });
const add = (at: number) => screen.getByRole("button", { name: COMPARE.addNamed(nameAt(at)) });
const added = (at: number) => screen.getByRole("button", { name: COMPARE.removeNamed(nameAt(at)) });
const link = () => within(tray()).queryByRole("link");
const cross = (at: number) => within(tray()).getByRole("button", { name: TRAY.remove(nameAt(at)) });
const clear = () => within(tray()).queryByRole("button", { name: TRAY.clearNamed });
/** What holds the button of an area, with whatever stands beside it. */
const besideOf = (button: HTMLElement) => button.parentElement as HTMLElement;
const chosen = () => within(tray()).queryAllByRole("listitem");
/** The places the bar keeps empty. They are drawn for the eye, and are no part of what is read. */
const empty = () => [...tray().querySelectorAll("[data-place='empty']")];

describe("the words of comparing", () => {
  test("test_the_button_says_add_to_compare_and_once_chosen_added_to_compare", () => {
    // The founder's words. What is seen on the button is the start of its name.
    expect(COMPARE.addShort).toBe("Add to compare");
    expect(COMPARE.removeShort).toBe("Added to compare");
    expect(COMPARE.addNamed("Farrowmere").startsWith(`${COMPARE.addShort}: `)).toBe(true);
    expect(COMPARE.removeNamed("Farrowmere").startsWith(`${COMPARE.removeShort}: `)).toBe(true);
    // Once chosen the name says what a press does as well: a person who sees the page reads it from the amber.
    expect(COMPARE.removeNamed("Farrowmere")).toMatch(/take it out/);
    expect(TRAY.go(2)).toBe("Compare 2 areas");
  });

  test("test_what_says_that_areas_can_be_compared_names_the_button_as_the_button_names_itself", () => {
    expect(COMPARE.invite).toContain(`"${COMPARE.addShort}"`);
    expect(COMPARE.invite).toMatch(/two to four areas/);
    expect(COMPARE.invite).toMatch(/side by side/);
  });

  test("test_what_is_read_of_the_invitation_stands_beside_its_two_towns_and_no_word_of_it_under_them", () => {
    // Seen at 390 by 844: the sentence ran round the two towns, which are as high as two
    // lines of it, and took four. Its last word stood alone under the towns.
    const sheet = rulesOf(readFileSync(path.join(__dirname, "CompareTray.module.css"), "utf8")).filter((rule) => rule.under === null);
    const setsOf = (selector: string) => new Map(sheet.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

    // The towns and the sentence are laid side by side, from their heads.
    expect([setsOf(".invite").get("display"), setsOf(".invite").get("align-items")]).toEqual(["flex", "flex-start"]);
    expect(setsOf(".invite").get("gap")).toBe("var(--space-3)");
    // The towns keep their width, and nothing runs round them.
    expect(setsOf(".twoTowns").get("flex")).toBe("none");
    expect([setsOf(".twoTowns").get("float"), setsOf(".twoTowns").get("margin-inline-end")]).toEqual([undefined, undefined]);
    expect(setsOf(".invite > :last-child").get("min-width")).toBe("0");
  });

  test("test_no_word_of_comparing_calls_an_area_the_best_or_says_that_one_has_won", () => {
    const said = [
      ...Object.values(COMPARE).map((words) => (typeof words === "function" ? words("Farrowmere" as never) : words)),
      ...Object.values(TRAY).map((words) => (typeof words === "function" ? words(2 as never) : words)),
    ].map((words) => (typeof words === "string" ? words : Object.values(words).join(" ")));

    expect(said.length).toBeGreaterThan(20);
    expect(said.filter((words) => /\b(best|better|worse|worst|winner|wins?|won|beats?|top pick|good area)\b/i.test(words))).toEqual([]);
  });
});

describe("the tray of areas to compare", () => {
  test("test_before_anything_is_chosen_the_tray_holds_no_area_and_no_link", () => {
    show();

    expect(tray()).toHaveAttribute("data-closed", "true");
    expect(link()).toBeNull();
    expect(within(tray()).queryByRole("list")).toBeNull();
    expect(empty()).toEqual([]);
  });

  test("test_one_area_is_not_enough_to_compare_and_the_tray_says_what_to_do_next", async () => {
    const { user } = show();

    await user.click(add(0));

    expect(within(tray()).getByRole("status")).toHaveTextContent(TRAY.one);
    expect(TRAY.one).toMatch(/at least one more/);
    expect(link()).toBeNull();
  });

  test("test_two_areas_can_be_compared_and_the_link_holds_their_slugs_and_nothing_else", async () => {
    const { user } = show();

    await user.click(add(0));
    await user.click(add(1));

    expect(link()).toHaveTextContent(TRAY.go(2));
    expect(link()).toHaveAttribute("href", `/compare?a=${areas[0]?.slug}&a=${areas[1]?.slug}`);
    // It is followed when it is pressed, and not fetched before.
    expect(link()).toHaveAttribute("data-prefetch", "false");
  });

  test("test_the_areas_are_in_the_order_they_were_chosen_and_in_no_other", async () => {
    const { user } = show();

    await user.click(add(2));
    await user.click(add(0));

    expect(chosen().map((item) => within(item).getByText(/./, { selector: "[data-says='name']" }).textContent)).toEqual([
      nameAt(2),
      nameAt(0),
    ]);
    expect(link()).toHaveAttribute("href", `/compare?a=${areas[2]?.slug}&a=${areas[0]?.slug}`);
  });

  test("test_a_fifth_area_cannot_be_added_and_the_tray_says_why", async () => {
    const { user } = show();
    for (const at of [0, 1, 2, 3]) await user.click(add(at));

    expect(add(4)).toBeDisabled();
    expect(within(tray()).getByRole("status")).toHaveTextContent(TRAY.full);
    expect(link()).toHaveTextContent(TRAY.go(4));
    // One that is chosen can still be taken out.
    expect(added(0)).toBeEnabled();
  });

  test("test_a_button_that_is_switched_off_says_why_in_the_words_of_the_bar_which_is_in_sight", async () => {
    // Seen in a browser, first: with four areas chosen the button of a fifth was switched
    // off, and the reason was in the tray, 5,570 pixels up the page. The bar now stays at the
    // foot of the screen, wherever the button is. Seen in a browser since: said under the
    // button as well, the reason made the head of every other result of a phone 142 px high
    // where it was 69, as the fourth area was added.
    const { user } = show(5, { small: true });
    for (const at of [0, 1, 2, 3]) await user.click(add(at));

    const fifth = add(4);
    expect(fifth).toBeDisabled();
    expect(fifth).toHaveAccessibleDescription(TRAY.full);
    expect(fifth).toHaveAttribute("aria-describedby", BAR_SAYS);
    // The bar says it where it can be seen, and nothing stands beside the button.
    const says = within(tray()).getByRole("status");
    expect(says).toHaveAttribute("id", BAR_SAYS);
    expect(says.closest(".visually-hidden, [aria-hidden='true'], [hidden]")).toBeNull();
    expect([...besideOf(fifth).children]).toEqual([fifth]);
    // A button that can be pressed says nothing of it.
    await user.click(added(0));
    expect(add(4)).not.toHaveAccessibleDescription();
  });

  test("test_on_the_page_of_an_area_a_button_that_is_switched_off_says_why_beside_itself_too", async () => {
    const { user } = show(5, { invites: true });
    for (const at of [0, 1, 2, 3]) await user.click(add(at));

    const fifth = add(4);
    expect(fifth).toBeDisabled();
    expect(fifth).toHaveAccessibleDescription(COMPARE.full);
    const why = within(besideOf(fifth)).getByText(COMPARE.full);
    expect(why.closest(".visually-hidden, [aria-hidden='true'], [hidden]")).toBeNull();
    // It says what to do about it.
    expect(COMPARE.full).toMatch(/Take one out/);
    // What comparing is, is not said of a button that cannot add.
    expect(within(besideOf(fifth)).queryByText(COMPARE.inviteHere)).toBeNull();
  });

  test("test_the_way_to_the_comparison_is_beside_the_button_of_an_area_that_is_chosen", async () => {
    // Seen in a browser: the link that compares the areas was in the tray alone, thousands
    // of pixels from the buttons that fill it.
    const { user } = show(3);
    const item = (at: number) =>
      within(screen.getByRole("button", { name: new RegExp(`: ${nameAt(at)}(\\.|$)`) }).closest("li") as HTMLElement);

    await user.click(add(0));
    // One area is not enough. The bar says what to do next, and the button holds no way on.
    expect(within(tray()).getByRole("status")).toHaveTextContent(TRAY.one);
    expect(item(0).queryByText(TRAY.one)).toBeNull();
    expect(item(0).queryByRole("link")).toBeNull();

    await user.click(add(1));
    for (const at of [0, 1]) {
      const near = item(at).getByRole("link", { name: TRAY.go(2) });
      expect(near).toHaveAttribute("href", `/compare?a=${areas[0]?.slug}&a=${areas[1]?.slug}`);
      expect(near).toHaveAttribute("data-prefetch", "false");
      expect(near).toHaveClass("target");
    }
    // An area that is not chosen has the button and nothing more.
    expect(item(2).queryByRole("link")).toBeNull();
  });

  test("test_what_holds_the_button_holds_nothing_more_once_its_area_is_the_only_one_chosen", async () => {
    // Seen in a browser, on a phone: "Now choose at least one more." was drawn under the
    // button and took the room of what stands beside the name of the area, which broke into
    // four lines of a word each. The result grew by 39 px under the press.
    const { user } = show(3, { small: true });
    const first = add(0);
    expect([...besideOf(first).children]).toEqual([first]);

    await user.click(first);

    // The same button, and nothing beside it: what holds it is as high as it was.
    expect(added(0)).toBe(first);
    expect([...besideOf(first).children]).toEqual([first]);
    // What to do next is said by the bar, where the areas are gathered, in sight and aloud.
    expect(within(tray()).getByRole("status")).toHaveTextContent(TRAY.one);
    expect(TRAY.one).toMatch(/at least one more/);
  });

  test("test_on_the_page_of_an_area_what_is_said_beside_the_button_keeps_its_room_as_the_button_is_pressed", async () => {
    // Seen in a browser, on a phone: what was said beside the button went from two lines to
    // three as the area was chosen, and all that stood under it went 23 px down under the press.
    const { user } = show(2, { invites: true });
    const first = add(0);
    const place = besideOf(first).lastElementChild as HTMLElement;

    expect(within(place).getByText(COMPARE.inviteHere)).toBeVisible();
    expect(COMPARE.inviteHere).toMatch(/side by side/);
    // The place keeps the room of what it says before the area is chosen and of what it says
    // after, from the start: the style sheet lays both out in it, undrawn.
    expect([place.dataset.before, place.dataset.after]).toEqual([COMPARE.inviteHere, TRAY.one]);

    await user.click(first);

    // Once it is chosen it says what to do next, as the bar does, which is at the foot of the screen.
    expect(besideOf(first).lastElementChild).toBe(place);
    expect(within(place).getByText(TRAY.one)).toBeVisible();
    expect(within(place).queryByText(COMPARE.inviteHere)).toBeNull();
    expect([place.dataset.before, place.dataset.after]).toEqual([COMPARE.inviteHere, TRAY.one]);
  });

  test("test_on_the_page_of_an_area_the_way_to_the_comparison_stands_in_the_same_place", async () => {
    const { user } = show(2, { invites: true });
    const place = besideOf(add(0)).lastElementChild as HTMLElement;
    await user.click(add(0));
    await user.click(add(1));

    const near = within(besideOf(added(0))).getByRole("link", { name: TRAY.go(2) });
    expect(near.parentElement).toBe(place);
    expect([...place.children]).toEqual([near]);
    expect([place.dataset.before, place.dataset.after]).toEqual([COMPARE.inviteHere, TRAY.one]);
    // The way on is the next stop of the keyboard after the button.
    expect(added(0).compareDocumentPosition(near) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("test_whether_an_area_is_chosen_is_said_in_words_and_never_by_colour_alone", async () => {
    const { user } = show();

    await user.click(add(0));

    expect(screen.queryByRole("button", { name: COMPARE.addNamed(nameAt(0)) })).toBeNull();
    expect(added(0)).toHaveTextContent(new RegExp(`^${COMPARE.removeShort}$`));
    // A press takes it out again.
    await user.click(added(0));
    expect(add(0)).toHaveTextContent(new RegExp(`^${COMPARE.addShort}$`));
    expect(tray()).toHaveAttribute("data-closed", "true");
  });

  test("test_an_area_can_be_taken_out_of_the_bar_by_its_cross", async () => {
    const { user } = show();
    for (const at of [0, 1, 2]) await user.click(add(at));

    await user.click(cross(1));

    expect(link()).toHaveAttribute("href", `/compare?a=${areas[0]?.slug}&a=${areas[2]?.slug}`);
    expect(add(1)).toBeInTheDocument();
  });

  test("test_the_bar_holds_one_button_of_the_size_of_a_main_control_which_is_the_way_to_the_comparison", async () => {
    // A bar with two buttons of one size asked which of them to press. It has one, and what
    // takes an area out is small: the cross of that area, and "Clear" for all of them.
    const { user } = show();
    for (const at of [0, 1, 2]) await user.click(add(at));

    expect(within(tray()).getAllByRole("link")).toHaveLength(1);
    expect(
      within(tray())
        .getAllByRole("button")
        .map((button) => button.getAttribute("aria-label")),
    ).toEqual([...[0, 1, 2].map((at) => TRAY.remove(nameAt(at))), TRAY.clearNamed]);
    const main = [...tray().querySelectorAll("a, button")].filter((control) => control.classList.contains("target"));
    expect(main).toEqual([link()]);
  });

  test("test_clear_takes_every_area_out_at_once_and_says_what_it_does", async () => {
    // It was in the bar as the founder walked the website, and nobody asked for it to go:
    // with four areas chosen, emptying the bar took four presses, or "Start again", which
    // throws the search away with it.
    const { user } = show();
    for (const at of [0, 1, 2, 3]) await user.click(add(at));

    expect(clear()).toHaveTextContent(new RegExp(`^${TRAY.clear}$`));
    // It stands in the line of what the bar says, after it, and is no part of what is said aloud.
    expect(clear()?.previousElementSibling).toBe(within(tray()).getByRole("status"));
    // What is seen on it is the start of its name.
    expect(TRAY.clearNamed.startsWith(TRAY.clear)).toBe(true);
    expect(clear()?.tagName).toBe("BUTTON");
    expect(clear()).toHaveClass("target-min");
    // It comes after the areas, in the page as on the screen.
    expect(cross(3).compareDocumentPosition(clear() as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    await user.click(clear() as HTMLElement);

    expect(tray()).toHaveAttribute("data-closed", "true");
    expect(chosen()).toEqual([]);
    for (const at of [0, 1, 2, 3, 4]) expect(add(at)).toBeEnabled();
    // It went with its press. The focus is on the bar, and never on nothing.
    expect(tray()).toHaveFocus();
  });

  test("test_one_area_is_taken_out_by_its_own_cross_and_there_is_nothing_to_clear_until_there_are_two", async () => {
    const { user } = show();

    await user.click(add(0));
    expect(clear()).toBeNull();
    await user.click(add(1));
    expect(clear()).not.toBeNull();
    // With one taken out again it goes, and the focus with the cross that was pressed goes to the cross beside it.
    await user.click(cross(1));
    expect(clear()).toBeNull();
    expect(cross(0)).toHaveFocus();
  });

  test("test_on_a_narrow_screen_clear_is_drawn_in_the_line_of_what_the_bar_says_and_the_bar_is_no_higher_than_the_page_clears", async () => {
    // Seen at 390 by 844: the bar had no "Clear", which it has on a wide screen. Measured
    // there with "Clear" in the line of what the bar says, as that line was set: 179 px
    // with four areas chosen, and the page clears 176 px for the bar. So the lines of what
    // the bar says are set closer there.
    const sheet = rulesOf(readFileSync(path.join(__dirname, "CompareTray.module.css"), "utf8"));
    const NARROW = "@media (max-width: 40rem)";
    const narrow = (selector: string) => sheet.filter((rule) => rule.under === NARROW && rule.selector === selector).map((rule) => [...rule.sets]);
    expect(CLEAR_ON_A_NARROW_SCREEN).toBe("drawn");
    const { user } = show(5);
    for (const at of [0, 1]) await user.click(add(at));

    expect(tray()).toHaveAttribute("data-clear-narrow", "true");
    expect(clear()).not.toBeNull();
    // Nothing takes it off a narrow screen but the one line of the look.
    expect(narrow(".says > .clear")).toEqual([]);
    expect(narrow('.tray[data-clear-narrow="false"] .says > .clear')).toEqual([[["display", "none"]]]);
    expect(narrow('.tray[data-clear-narrow="true"] .says')).toEqual([[["line-height", "1.2"]]]);
    // Wherever it is drawn it is in the line, and takes no line of its own.
    const drawn = sheet.filter((rule) => rule.under === null && rule.selector === ".says > .clear");
    expect(drawn.map((rule) => rule.sets.get("display"))).toEqual(["inline-flex"]);
    expect(sheet.filter((rule) => rule.under === null && rule.selector === ".status").map((rule) => rule.sets.get("display"))).toEqual(["inline"]);
  });

  test("test_one_line_of_the_look_leaves_clear_off_a_narrow_screen_as_it_was", async () => {
    expect(CLEAR_ON_A_NARROW_SCREEN_MAY_BE).toEqual(["drawn", "not"]);
    const { user } = show(5, { narrow: "not" });
    for (const at of [0, 1]) await user.click(add(at));

    // It is in the page, for a wide screen: the style sheet does not draw it on a narrow one.
    expect(tray()).toHaveAttribute("data-clear-narrow", "false");
    expect(clear()).not.toBeNull();
  });

  test("test_one_line_of_the_look_takes_clear_out_of_the_bar", async () => {
    expect(CLEAR_MAY_STAND).toEqual(["small", "none"]);
    expect(CLEAR_STANDS).toBe("small");
    const { user } = show(5, { clears: "none" });
    for (const at of [0, 1, 2]) await user.click(add(at));

    expect(clear()).toBeNull();
    expect(
      within(tray())
        .getAllByRole("button")
        .map((button) => button.getAttribute("aria-label")),
    ).toEqual([0, 1, 2].map((at) => TRAY.remove(nameAt(at))));
  });

  test("test_the_tray_can_be_used_by_keyboard_alone", async () => {
    const { user } = show(2);

    await user.tab();
    await user.keyboard("{Enter}");
    await user.tab();
    await user.keyboard(" ");

    expect(link()).toHaveTextContent(TRAY.go(2));
    // The focus stays on the button that was pressed.
    expect(added(1)).toHaveFocus();
  });

  test("test_every_control_of_the_tray_takes_a_target_size", async () => {
    const { user, container } = show();
    for (const at of [0, 1]) await user.click(add(at));

    const controls = [...container.querySelectorAll("a, button")];

    expect(controls.length).toBeGreaterThan(6);
    expect(
      controls.filter((control) => !control.classList.contains("target") && !control.classList.contains("target-min")),
    ).toEqual([]);
    // The one button of the bar is a main control.
    expect(link()).toHaveClass("target");
  });

  test.each([0, 1, 2, 4])("test_the_tray_has_no_accessibility_fault_with_%i_chosen", async (count) => {
    const { user, container } = show(5, { towns: true });
    for (let at = 0; at < count; at += 1) await user.click(add(at));

    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_choosing_areas_writes_nothing_to_the_address_storage_or_the_console", async () => {
    const watching = watch();
    try {
      const { user } = show(5, { towns: true });
      for (const at of [0, 1, 2]) await user.click(add(at));
      for (const at of [0, 1, 2]) await user.click(cross(at));

      expect(tray()).toHaveAttribute("data-closed", "true");
      expect(watching.storage).toEqual([]);
      expect(watching.history).toEqual([]);
      expect(watching.console).toEqual([]);
    } finally {
      watching.stop();
    }
  });

  test("test_what_the_tray_says_of_each_count", () => {
    // With nothing chosen it says nothing: it takes no room until an area is chosen.
    expect([0, 1, 2, 3].map((count) => trayStatus(count, false))).toEqual(["", TRAY.one, TRAY.room(2), TRAY.room(1)]);
    expect(trayStatus(4, true)).toBe(TRAY.full);
    expect(MOST_COMPARED).toBe(4);
  });
});

describe("the places of the bar", () => {
  test("test_a_place_is_kept_empty_for_each_area_there_is_still_room_for", async () => {
    const { user } = show();

    for (const at of [0, 1, 2, 3]) {
      await user.click(add(at));
      // Four places in all, so that the bar is as wide with one area as with four, and nothing in it moves.
      expect([chosen().length, empty().length]).toEqual([at + 1, MOST_COMPARED - at - 1]);
    }
  });

  test("test_an_empty_place_is_drawn_for_the_eye_and_says_nothing_so_that_the_count_is_said_once", async () => {
    const { user } = show();
    await user.click(add(0));

    for (const place of empty()) {
      expect(place).toHaveAttribute("aria-hidden", "true");
      expect(place.textContent).toBe("");
      expect(place.closest("li")).toBeNull();
    }
    // How much room is left is said in words, in sight, where the bar says what it says.
    await user.click(add(1));
    expect(within(tray()).getByRole("status")).toHaveTextContent(TRAY.room(2));
  });

  test("test_with_what_a_town_is_drawn_from_in_hand_each_area_of_the_bar_has_its_town_and_its_name", async () => {
    const { user } = show(5, { towns: true });

    for (const at of [0, 1]) await user.click(add(at));

    chosen().forEach((item, at) => {
      const town = within(item).getByRole("img");
      expect(town.getAttribute("aria-label")?.startsWith(`${TOWN.nameOf(nameAt(at))}.`)).toBe(true);
      expect(within(item).getByText(nameAt(at), { selector: "[data-says='name']" })).toBeInTheDocument();
    });
  });

  test("test_the_bar_says_nothing_of_what_a_town_is_and_no_town_of_it_says_it_of_itself", async () => {
    // The founder, who had walked the website twice: "remove the 'each little town'
    // disclaimer on the ranking cards". The bar stands at the foot of the page of them, and
    // said the same in short, under what it is called.
    const { user } = show(5, { towns: true });
    for (const at of [0, 1, 2]) await user.click(add(at));

    expect(BAR_SAYS_OF_ITS_TOWNS).toBe("nothing");
    expect(BAR_MAY_SAY_OF_ITS_TOWNS).toEqual(["nothing", "line"]);
    expect(within(tray()).queryByText(TOWNS.short)).toBeNull();
    expect(tray().querySelector("[data-says='towns']")).toBeNull();
    // Its towns are drawn all the same, each with the name of its area.
    expect(within(tray()).getAllByRole("img")).toHaveLength(3);
    // What a town says under its drawing is not drawn in the bar, which lies over the page:
    // so no town says there what a town is, in whole or in short.
    const WIDE = "@media (min-width: 72rem)";
    const sheet = rulesOf(readFileSync(path.join(__dirname, "CompareTray.module.css"), "utf8"));
    const under = sheet.filter((rule) => /figcaption/.test(rule.selector));
    expect(under.map((rule) => [rule.under, rule.selector, [...rule.sets]])).toEqual([
      [WIDE, '.tray[data-towns="true"] .area > .town > figcaption', [["display", "none"]]],
    ]);
    for (const item of chosen()) {
      const short = item.querySelector("[data-line='short']") as HTMLElement;
      expect(short.textContent).toBe(TOWN.short);
      // The line in short is drawn at the head of the page of an area, and nowhere else.
      expect(short.closest("header[data-town]")).toBeNull();
    }
  });

  test("test_one_line_of_the_look_has_the_bar_say_once_what_a_town_is_and_only_where_a_town_stands", async () => {
    // As it was before the founder asked for it to go.
    const { user, unmount } = show(5, { towns: true, says: "line" });
    for (const at of [0, 1, 2]) await user.click(add(at));

    expect(within(tray()).getAllByText(TOWNS.short, { selector: "[data-says='towns']" })).toHaveLength(1);
    // The bar lies over the page, and says it in fewer words than a list does: that a town
    // is a drawing made of vibes, and that it is no picture of the place.
    expect(TOWNS.short.length).toBeLessThan(TOWNS.line.length);
    expect(TOWNS.short).toMatch(/four of the area's vibes/);
    expect(TOWNS.short).toMatch(/not a picture of the place/);
    unmount();

    // With nothing handed over no town is drawn, and no line says what a town is.
    const bare = show(5, { says: "line" });
    await bare.user.click(add(0));
    expect(within(tray()).queryByRole("img")).toBeNull();
    expect(within(tray()).queryByText(TOWNS.short)).toBeNull();
    // The area is there by its name all the same.
    expect(within(tray()).getByText(nameAt(0))).toBeInTheDocument();
  });

  test("test_an_area_nothing_was_handed_of_has_no_town_beside_areas_that_have_theirs", async () => {
    const user = userEvent.setup({ delay: null });
    render(
      <SessionProvider>
        <CompareTray />
        <CompareButton area={areas[0] as (typeof areas)[number]} town={townAt(0)} />
        <CompareButton area={areas[1] as (typeof areas)[number]} />
      </SessionProvider>,
    );

    for (const at of [0, 1]) await user.click(add(at));

    expect(chosen().map((item) => within(item).queryAllByRole("img").length)).toEqual([1, 0]);
  });

  test("test_every_area_of_the_bar_is_drawn_as_the_next_is_because_nobody_wins", async () => {
    const { user } = show(5, { towns: true });
    for (const at of [0, 1, 2, 3]) await user.click(add(at));

    const drawn = chosen().map((item) => ({
      classes: item.className,
      marks: [...item.attributes].map((one) => one.name).sort(),
      parts: [...item.children].map((part) => `${part.tagName} ${part.className}`),
    }));

    expect(new Set(drawn.map((one) => JSON.stringify(one))).size).toBe(1);
    // Nothing of the bar says that one area is chosen above another, in hand, or the first.
    expect(tray().querySelector("li [aria-current], li [aria-selected], li [aria-pressed], li [data-kind='box-on']")).toBeNull();
    expect(tray().textContent).not.toMatch(/\b(rank|fit|best|first|1st)\b/i);
  });
});

describe("the tray, where it stays within reach", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "CompareTray.module.css"), "utf8"));

  function showOnASearch(count = 5) {
    const user = userEvent.setup({ delay: null });
    const view = render(
      <SessionProvider>
        <ul>
          {areas.slice(0, count).map((area) => (
            <li key={area.area_id}>
              <CompareButton area={area} small />
            </li>
          ))}
        </ul>
        <CompareTray />
      </SessionProvider>,
    );
    return { user, ...view };
  }

  test("test_it_takes_no_room_until_an_area_is_chosen_and_is_still_there_to_be_told_of", () => {
    showOnASearch();

    // The answer comes first. The region is on the page, so that a reader is told when it first speaks.
    expect(tray()).toHaveAttribute("data-closed", "true");
    expect(within(tray()).getByRole("status")).toBeEmptyDOMElement();
    // It holds no heading until it holds an area: a person who goes by headings was led to
    // one with nothing under it, which on the first page was the only one under the first.
    expect(tray().textContent).toBe("");
    expect(screen.queryAllByRole("heading")).toEqual([]);
    expect(within(tray()).queryAllByRole("button")).toEqual([]);
    const closed = STYLES.filter((rule) => /data-closed="true"/.test(rule.selector));
    expect(closed.map((rule) => rule.sets.get("padding"))).toContain("0");
    expect(closed.map((rule) => rule.sets.get("border"))).toContain("0");
  });

  test("test_once_an_area_is_chosen_it_stays_at_the_foot_of_the_screen", async () => {
    const { user } = showOnASearch();

    await user.click(add(0));

    expect(tray()).toHaveAttribute("data-closed", "false");
    expect(within(tray()).getByRole("status")).toHaveTextContent(TRAY.one);
    expect(within(tray()).getByText(nameAt(0))).toBeInTheDocument();
    // It is named by its heading once it holds something to head.
    expect(within(tray()).getByRole("heading", { level: 2, name: TRAY.title })).toHaveAttribute("id", tray().getAttribute("aria-labelledby"));
    const sticks = STYLES.filter((rule) => rule.sets.get("position") === "sticky");
    expect(sticks.map((rule) => rule.selector)).toEqual(['.tray[data-closed="false"]']);
    expect(sticks.map((rule) => rule.sets.get("inset-block-end"))).toEqual(["0"]);
  });

  test("test_where_the_bar_stands_is_said_more_heavily_than_the_kit_says_where_a_box_stands", () => {
    // The bar is a box of the kit, and the kit says of every box that it is positioned where
    // it lies. Which of two style sheets is read last is not the website's to decide: so what
    // the bar says of where it stands weighs more than what the kit says, open and closed.
    const KIT = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Frame", "Frame.module.css"), "utf8"));
    const ofTheKit = KIT.filter((rule) => rule.under === null && rule.sets.has("position") && !/::/.test(rule.selector));
    const ofTheBar = STYLES.filter((rule) => rule.under === null && rule.sets.has("position") && /^\.tray\b/.test(rule.selector));

    expect(ofTheKit.map((rule) => rule.selector)).toEqual([".frame"]);
    expect(ofTheBar.map((rule) => rule.sets.get("position")).sort()).toEqual(["static", "sticky"]);
    for (const rule of ofTheBar) {
      expect([rule.selector, heavier(weightOf(rule.selector), weightOf(".frame"))]).toEqual([rule.selector, true]);
    }
  });

  test("test_the_button_on_a_result_says_what_it_does_and_names_its_area", async () => {
    const { user } = showOnASearch();

    expect(add(0)).toHaveTextContent(new RegExp(`^${COMPARE.addShort}$`));
    expect(add(0)).toHaveClass("target-min");
    await user.click(add(0));

    expect(added(0)).toHaveTextContent(new RegExp(`^${COMPARE.removeShort}$`));
    expect(added(0)).toHaveFocus();
    // Its words say that the area is chosen, and its name what a press does: it says neither twice.
    expect(added(0)).not.toHaveAttribute("aria-pressed");
  });

  test("test_with_two_chosen_the_way_to_the_comparison_is_in_the_tray_and_beside_the_button", async () => {
    const { user } = showOnASearch();

    await user.click(add(0));
    await user.click(add(1));

    const ways = screen.getAllByRole("link", { name: TRAY.go(2) });
    expect(ways.length).toBeGreaterThanOrEqual(2);
    for (const way of ways) {
      expect(way).toHaveAttribute("href", `/compare?a=${areas[0]?.slug}&a=${areas[1]?.slug}`);
      expect(way).toHaveAttribute("data-prefetch", "false");
    }
    expect(within(tray()).getByRole("link", { name: TRAY.go(2) })).toHaveClass("target");
  });

  test("test_the_tray_where_it_sticks_has_no_accessibility_fault", async () => {
    const { user, container } = showOnASearch();
    await user.click(add(0));
    await user.click(add(1));

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the bar and its button, as the look draws them", () => {
  const CSS = readFileSync(path.join(__dirname, "CompareTray.module.css"), "utf8");
  const ALL = rulesOf(CSS);
  const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
  const FORCED = ALL.filter((rule) => /forced-colors/.test(rule.under ?? ""));
  /** What the sheet sets of a selector, where it holds on every screen. */
  const setsOf = (selector: string) =>
    new Map(STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));
  /** What a button is drawn as: the kind its face bears. */
  const drawnAs = (button: HTMLElement) => button.querySelector("[data-kind]")?.getAttribute("data-kind");
  /** The pictures a button is drawn with, as the page names them on its face. */
  const picturesOn = (button: HTMLElement) => {
    const face = button.firstElementChild as HTMLElement;
    return [face.style.getPropertyValue("--art"), face.style.getPropertyValue("--art-down")];
  };

  test("test_the_bar_is_a_box_of_the_look_once_an_area_is_chosen_and_draws_nothing_until_then", async () => {
    const { user } = show();

    // Closed, it is the frame that has no picture and no shadow, and the sheet takes its edge and its ground.
    expect(tray()).toHaveAttribute("data-kind", "plain");
    const closed = setsOf('.tray[data-closed="true"]');
    expect([closed.get("border"), closed.get("background"), closed.get("padding")]).toEqual(["0", "transparent", "0"]);

    await user.click(add(0));

    // It is the same element, so that what it says when it first speaks is heard.
    expect(tray()).toHaveAttribute("data-kind", "box");
    expect(tray().tagName).toBe("SECTION");
    // The box brings its own ground and its own shadow: the sheet lays neither.
    const open = setsOf('.tray[data-closed="false"]');
    expect([open.has("background"), open.has("box-shadow"), open.has("border"), open.has("overflow")]).toEqual([
      false,
      false,
      false,
      false,
    ]);
  });

  test("test_the_same_bar_is_there_before_and_after_an_area_is_chosen", async () => {
    const { user } = show();
    const before = tray();
    const said = within(before).getByRole("status");

    await user.click(add(0));

    expect(tray()).toBe(before);
    expect(within(tray()).getByRole("status")).toBe(said);
  });

  test("test_the_way_to_the_comparison_is_a_button_of_the_look", async () => {
    const { user } = show();
    await user.click(add(0));
    await user.click(add(1));

    const go = within(tray()).getByRole("link", { name: TRAY.go(2) });

    expect(drawnAs(go)).toBe(WAY_TO_COMPARE);
    // It does not say that it is pressed, and is not switched off.
    expect(go).not.toHaveAttribute("aria-pressed");
    expect(go).not.toHaveAttribute("aria-disabled");
    expect(["go", "plain"]).toContain(WAY_TO_COMPARE);
    // It is the one thing of the bar that is drawn as a button that matters most, whichever way is chosen.
    expect([...tray().querySelectorAll("[data-kind='go']")].length).toBe(WAY_TO_COMPARE === "go" ? 1 : 0);
    // And the button that chooses an area is never drawn so: a list of ten results holds ten of them.
    for (const at of [0, 1, 2]) {
      const button = screen.getByRole("button", { name: new RegExp(`: ${nameAt(at)}(\\.|$)`) });
      expect(["plain", "on"]).toContain(drawnAs(button));
    }
  });

  test("test_the_cross_of_an_area_is_the_drawing_of_a_cross_and_its_letter_is_kept_from_a_screen_reader", async () => {
    const { user } = show();
    await user.click(add(0));

    const drawn = cross(0).firstElementChild as HTMLElement;

    expect(cross(0).children).toHaveLength(1);
    expect(drawn).toHaveAttribute("aria-hidden", "true");
    expect(drawn.style.getPropertyValue("--art")).toBe('url("/art/ui-cross.png")');
    expect([drawn.style.getPropertyValue("--w"), drawn.style.getPropertyValue("--h")]).toEqual([
      String(ART["ui-cross"].width),
      String(ART["ui-cross"].height),
    ]);
    // It is shown at its own size times an art pixel, with a hard edge, and never stretched.
    const sets = setsOf(".cross");
    expect(sets.get("width")).toBe("calc(var(--px-small) * var(--w))");
    expect(sets.get("height")).toBe("calc(var(--px-small) * var(--h))");
    expect(sets.get("image-rendering")).toBe("pixelated");
    // The letter is under the drawing, and is not drawn over it.
    expect([sets.get("overflow"), sets.get("text-indent"), sets.get("white-space")]).toEqual(["hidden", "100%", "nowrap"]);
  });

  test("test_the_button_of_an_area_that_is_chosen_is_amber_and_never_says_that_it_is_pressed", async () => {
    const { user } = show();
    const button = add(0);

    expect(drawnAs(button)).toBe("plain");
    expect(picturesOn(button)).toEqual(['url("/art/ui-button.png")', 'url("/art/ui-button-down.png")']);

    await user.click(button);

    expect(drawnAs(added(0))).toBe("on");
    expect(picturesOn(added(0))).toEqual(['url("/art/ui-button-on.png")', 'url("/art/ui-button-on-down.png")']);
    expect(added(0)).not.toHaveAttribute("aria-pressed");
  });

  test("test_what_is_drawn_of_the_button_is_its_face_which_is_inside_the_button_that_takes_the_press", () => {
    show();
    const button = add(0);

    expect(button.tagName).toBe("BUTTON");
    expect(button).toHaveClass("press");
    expect(button.children).toHaveLength(1);
    expect(button.firstElementChild).toHaveClass("face");
    expect(button.firstElementChild?.children).toHaveLength(1);
    expect(button.firstElementChild?.firstElementChild).toHaveClass("says");
    expect(button.firstElementChild?.firstElementChild).toHaveTextContent(COMPARE.addShort);
  });

  test("test_the_button_is_as_wide_chosen_as_not_so_that_nothing_beside_it_moves_when_it_is_pressed", async () => {
    // "Added to compare" is the longer of the two. The button keeps the room of it from the
    // start, by a line that is laid out and not drawn: the words of the button are the words
    // that are seen, and no others.
    const { user } = show();
    const button = () => screen.queryByRole("button", { name: COMPARE.addNamed(nameAt(0)) }) ?? added(0);
    const says = () => button().querySelector("[data-widest]") as HTMLElement;

    expect(says().getAttribute("data-widest")).toBe(COMPARE.removeShort);
    expect(says().textContent).toBe(COMPARE.addShort);
    await user.click(add(0));
    expect(says().getAttribute("data-widest")).toBe(COMPARE.removeShort);
    expect(says().textContent).toBe(COMPARE.removeShort);

    const room = STYLES.filter((rule) => rule.selector === ".fills [data-widest]::after" && rule.under === null);
    expect(room.map((rule) => [rule.sets.get("content"), rule.sets.get("height"), rule.sets.get("visibility")])).toEqual([
      ["attr(data-widest)", "0", "hidden"],
    ]);
  });

  test("test_the_words_of_the_button_are_a_short_label_wherever_it_stands", () => {
    render(
      <SessionProvider>
        <CompareButton area={areas[0] as (typeof areas)[number]} />
        <CompareButton area={areas[1] as (typeof areas)[number]} small />
      </SessionProvider>,
    );

    for (const at of [0, 1]) {
      expect(add(at)).toHaveTextContent(new RegExp(`^${COMPARE.addShort}$`));
      expect(add(at).querySelector("[data-reads]")).toHaveAttribute("data-reads", "false");
    }
  });

  test("test_beside_a_result_it_is_as_high_as_a_main_control_where_there_is_room", () => {
    // It bears the class of the smallest size a control may be, which says 24 pixels. Where
    // a result has room its own sheet says 44, and says it more heavily.
    const small = STYLES.filter(
      (rule) => rule.sets.get("min-height") === "var(--target)" && /\.small\b/.test(rule.selector) && rule.under === null,
    );

    expect(small.map((rule) => rule.selector)).toEqual([".fills.small"]);
    expect(heavier(weightOf(".fills.small"), weightOf(".target-min"))).toBe(true);
  });

  test("test_a_button_that_can_add_no_more_is_drawn_down_and_keeps_its_ink", async () => {
    const { user } = show();
    for (const at of [0, 1, 2, 3]) await user.click(add(at));

    expect(add(4)).toBeDisabled();
    // Nothing is dimmed: it is down, as far as a press would take it, in the ink it had.
    expect(setsOf(".fills:disabled").get("color")).toBe("var(--ink)");
    expect(setsOf(".fills:disabled > span").get("border-image-source")).toBe("var(--art-down)");
    // It weighs more than what the page says of every button that is switched off.
    expect(heavier(weightOf(".fills:disabled"), weightOf("button:disabled"))).toBe(true);
    // With forced colours no picture is drawn over the system's own.
    expect(FORCED.filter((rule) => rule.selector === ".fills:disabled > span").map((rule) => rule.sets.get("border-image-source"))).toEqual([
      "none",
    ]);
  });

  test("test_the_way_to_the_comparison_beside_a_button_is_set_no_further_from_it_than_the_two_are_laid_out", () => {
    // Measured in a browser, at both sizes: beside the button the way to the comparison was
    // set in 8 px from its start, as the page sets the second of two small controls, and so
    // ran 8 px past the end of what held it.
    const base = rulesOf(readFileSync(path.join(__dirname, "..", "..", "styles", "base.css"), "utf8"));
    const theirs = base.find((rule) => rule.selector === ".target-min + .target-min" && rule.under === null);
    const mine = STYLES.find((rule) => rule.selector === ".beside > .fills + .near" && rule.under === null);

    // If the page stops setting it, this has nothing to take back and should be looked at again.
    expect(theirs?.sets.get("margin-inline-start")).toBe("var(--target-gap)");
    expect([...(mine?.sets ?? [])]).toEqual([["margin-inline-start", "0"]]);
    // Which sheet is read last is not the website's to decide, so the rule that must win weighs more.
    expect(heavier(weightOf(mine?.selector ?? ""), weightOf(theirs?.selector ?? ""))).toBe(true);
  });

  test("test_no_edge_of_the_bar_or_of_its_button_is_dashed_or_dotted", () => {
    // The founder: "The dashed border is not understood to a user, please make solid".
    const written = CSS.replace(/\/\*[\s\S]*?\*\//g, "");

    expect(written.match(/\b(dashed|dotted)\b/g) ?? []).toEqual([]);
    // A place that is kept empty is told from one that is taken by its ground and by what it holds.
    expect(setsOf(".plot").get("border")).toBe("var(--edge) solid var(--border)");
  });

  test("test_every_colour_a_face_and_a_size_is_a_token_and_nothing_is_dimmed_or_moves", () => {
    const written = CSS.replace(/\/\*[\s\S]*?\*\//g, "");

    expect(written.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(written.match(/url\([^)]*\)/g) ?? []).toEqual([]);
    expect(written.match(/["'][^"']*["']/g)?.filter((quoted) => !/^"(true|false|over|under)"$/.test(quoted)) ?? []).toEqual([]);
    const faces = STYLES.flatMap((rule) =>
      [...rule.sets].filter(([property]) => property === "font" || property === "font-family").map(([, value]) => value),
    );
    expect(faces.filter((face) => !/var\(--font-(say|name)\)$/.test(face))).toEqual([]);
    const moving = ALL.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(animation|transition|transform|translate|rotate|scale|zoom|opacity|filter)/.test(property)),
    );
    // One thing is set down by the focus, and moves nothing: the way to the comparison beside
    // the button of an area's page, where a narrow screen has no room to draw it.
    expect(moving.map((rule) => [rule.under, rule.selector, [...rule.sets.keys()].filter((property) => /^transform/.test(property))])).toEqual([
      ["@media (max-width: 40rem)", '.beside[data-invites="true"] .near', ["transform"]],
      ["@media (max-width: 40rem)", '.beside[data-invites="true"] .near:focus-visible', ["transform"]],
      [null, '.beside[data-small="true"] > .near', ["transform"]],
      [null, '.beside[data-small="true"] > .near:focus-visible', ["transform"]],
    ]);
  });

  test("test_beside_the_name_of_an_area_the_way_to_the_comparison_takes_no_room_and_is_kept_for_a_keyboard", async () => {
    // Seen in a browser: in the card of the map the row of buttons broke in two as the second
    // area was added, and the button that was pressed went 52 px down from under the
    // pointer. On a phone the card grew by 80 px under the press.
    const { user } = show(3, { small: true });
    await user.click(add(0));
    await user.click(add(1));

    // It is a link all the same, and the next stop of a keyboard after the button.
    const near = within(besideOf(added(1))).getByRole("link", { name: TRAY.go(2) });
    expect(near).toHaveClass("near", "target-min");
    expect(added(1).nextElementSibling).toBe(near);
    const atRest = setsOf('.beside[data-small="true"] > .near');
    expect([atRest.get("position"), atRest.get("transform"), atRest.get("inset-block-start")]).toEqual(["absolute", "translateY(-9999px)", "100%"]);
    expect([atRest.get("background"), atRest.get("border")]).toEqual(["var(--page)", "var(--edge) solid var(--border)"]);
    expect([...setsOf('.beside[data-small="true"] > .near:focus-visible')]).toEqual([["transform", "none"]]);
  });

  test("test_the_way_to_the_comparison_that_has_no_room_is_kept_for_a_keyboard_and_set_down_under_the_button", () => {
    // On a narrow screen the page of an area draws the button alone: the bar has the way on in
    // sight. Beside the button it is the next stop of a keyboard all the same, and is seen
    // while it has the focus. It is laid over the page, so nothing moves as it comes or goes.
    const narrow = (selector: string) =>
      new Map(
        STYLES.filter((rule) => rule.selector === selector && rule.under === "@media (max-width: 40rem)").flatMap((rule) => [...rule.sets]),
      );
    const atRest = narrow('.beside[data-invites="true"] .near');

    expect([atRest.get("position"), atRest.get("transform")]).toEqual(["absolute", "translateY(-9999px)"]);
    expect(atRest.get("inset-block-start")).toBe("100%");
    // It is read on cream, within an edge of ink, over whatever it is set down on.
    expect([atRest.get("background"), atRest.get("border")]).toEqual(["var(--page)", "var(--edge) solid var(--border)"]);
    expect([...narrow('.beside[data-invites="true"] .near:focus-visible')]).toEqual([["transform", "none"]]);
    // What it is laid out from is the button's own holder.
    expect(setsOf(".beside").get("position")).toBe("relative");
    // What is said beside the button gives way there, with the room kept for it, and the button stands alone.
    const gone = STYLES.filter((rule) => rule.under === "@media (max-width: 40rem)" && rule.sets.get("display") === "none").map((rule) => rule.selector);
    expect(gone).toEqual(
      expect.arrayContaining([
        '.beside[data-invites="true"] > .under > .why',
        '.beside[data-invites="true"] > .under::before',
        '.beside[data-invites="true"] > .under::after',
      ]),
    );
    expect(narrow('.beside[data-invites="true"] > .under').get("display")).toBe("contents");
  });

  test("test_what_is_said_beside_the_button_of_an_areas_page_stands_in_a_place_as_high_as_the_highest_of_what_it_may_say", () => {
    expect(setsOf(".under").get("display")).toBe("grid");
    // What it holds, and what it may hold, lie in one place of the grid, one over the other.
    const one = STYLES.filter((rule) => rule.under === null && rule.sets.get("grid-area") === "1 / 1");
    expect(one.map((rule) => rule.selector)).toEqual([".under > *", ".under::before", ".under::after"]);
    // What it may hold is laid out and not drawn, in the size of what is drawn there.
    expect([...setsOf(".under::before")]).toEqual([
      ["grid-area", "1 / 1"],
      ["content", "attr(data-before)"],
      ["visibility", "hidden"],
    ]);
    expect([...setsOf(".under::after")]).toEqual([
      ["grid-area", "1 / 1"],
      ["content", "attr(data-after)"],
      ["visibility", "hidden"],
    ]);
    expect(setsOf(".under").get("font-size")).toBe("var(--size-small)");
  });

  test("test_nothing_that_holds_words_has_a_height_of_its_own_so_that_text_can_be_made_larger", () => {
    const fixed = ALL.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(height|max-height|block-size|max-block-size)$/.test(property)),
    );

    // The drawing of the cross has the size it is drawn at, and a place that is kept empty the
    // size of the town that will stand in it. The line that keeps the room of the longer
    // words of the button has no height at all, and what the bar is called is kept for
    // whoever hears the page where a narrow screen does not draw it. Nothing else has a height.
    expect(fixed.map((rule) => rule.selector).sort()).toEqual([
      ".cross",
      ".fills [data-widest]::after",
      ".plot",
      ".tray .title",
    ]);
  });

  test("test_what_changes_under_the_pointer_or_the_focus_is_what_is_drawn_and_never_where", () => {
    const inHand = ALL.filter((rule) => /:(hover|focus|focus-within|focus-visible|active)\b/.test(rule.selector));
    /** What is laid over the page and kept off the screen until a keyboard reaches it: it is set down, and moves nothing. */
    const setDown = (selector: string) => /\.near:focus-visible$/.test(selector);
    const SET_DOWN = 2;

    expect(inHand.length).toBeGreaterThan(0);
    // A ground, and the ring of the focus: each is drawn, and neither moves a thing or changes its size.
    const DRAWN = ["background-color", "box-shadow", "outline"];
    expect(
      inHand
        .filter((rule) => !setDown(rule.selector))
        .flatMap((rule) => [...rule.sets.keys()])
        .filter((property) => !DRAWN.includes(property)),
    ).toEqual([]);
    expect(inHand.filter((rule) => setDown(rule.selector)).map((rule) => [...rule.sets])).toEqual(
      Array.from({ length: SET_DOWN }, () => [["transform", "none"]]),
    );
  });

  test("test_the_towns_of_the_bar_are_drawn_where_a_screen_has_the_width_for_four_places_and_the_button_on_one_line", () => {
    // Seen in a browser, 800 px wide: the four places and the button had no room on one
    // line, what the bar is called was set one letter to a line, and the bar was 600 px
    // high. The bar lies over the page: so where a screen has not the width, no town is
    // drawn in it, as none is drawn on a narrow result, and an area is its name and its cross.
    const WIDE = "@media (min-width: 72rem)";
    const wide = (selector: string) =>
      new Map(ALL.filter((rule) => rule.under === WIDE && rule.selector === selector).flatMap((rule) => [...rule.sets]));

    for (const part of [".towns", ".area > .town", ".plot"]) expect([part, setsOf(part).get("display")]).toEqual([part, "none"]);
    expect(wide('.tray[data-towns="true"] .towns').get("display")).toBe("block");
    expect(wide('.tray[data-towns="true"] .area > .town').get("display")).toBe("flex");
    expect(wide('.tray[data-towns="true"] .plot').get("display")).toBe("block");
    // What the bar is, the four places and what to do next: three columns, on one line.
    expect(wide('.tray[data-closed="false"][data-towns="true"]').get("grid-template-columns")).toBe(
      "minmax(0, 1fr) auto minmax(0, 13rem)",
    );
    // A place is as wide with an area in it as kept empty: a town, and the room of its cross.
    expect(wide('.tray[data-towns="true"] .area').get("grid-template-columns")).toBe(
      "calc(var(--px-ground) * 56) calc(var(--px-small) * 14)",
    );
    expect([setsOf(".plot").get("width"), setsOf(".plot").get("margin-inline-end")]).toEqual([
      "calc(var(--px-ground) * 56)",
      "calc(var(--px-small) * 16)",
    ]);
    // Each of these weighs more than the rule it takes the place of, whichever is read last.
    for (const [mine, theirs] of [
      ['.tray[data-towns="true"] .towns', ".towns"],
      ['.tray[data-towns="true"] .area > .town', ".area > .town"],
      ['.tray[data-towns="true"] .plot', ".plot"],
      ['.tray[data-towns="true"] .area', ".area"],
    ] as const) {
      expect([mine, heavier(weightOf(mine), weightOf(theirs))]).toEqual([mine, true]);
    }
  });

  test("test_a_place_that_is_kept_empty_is_the_size_of_the_town_that_will_stand_in_it", () => {
    // The size of a town is the size of its plot, which the list of drawings holds.
    const plot = Object.entries(ART).find(([name]) => name === ["town", "plot"].join("-"))?.[1];

    expect(plot).toBeDefined();
    expect([setsOf(".plot").get("width"), setsOf(".plot").get("height")]).toEqual([
      `calc(var(--px-ground) * ${plot?.width})`,
      `calc(var(--px-ground) * ${plot?.height})`,
    ]);
  });

  test("test_a_town_of_the_bar_is_drawn_at_its_own_size_and_no_rule_of_the_bar_gives_it_another", () => {
    // A town is of one size wherever it stands. The bar lays it out, and hides what it says
    // under itself, which the bar says once: it sets no width, no height and no pixel of it.
    const ofATown = ALL.filter((rule) => /figure|\[role="img"\]|figcaption/.test(rule.selector));

    expect(ofATown.length).toBeGreaterThan(0);
    expect(
      ofATown.flatMap((rule) => [...rule.sets.keys()]).filter((property) => /^(width|height|--size|--px|zoom|scale|transform)/.test(property)),
    ).toEqual([]);
  });
});

describe("what is pressed in the bar and then goes", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "CompareTray.module.css"), "utf8"));

  test("test_an_area_taken_out_by_its_cross_hands_the_focus_to_the_cross_beside_it", async () => {
    // Seen in a browser: the cross went with its area, and the focus was left on nothing.
    const { user } = show();
    for (const at of [0, 1, 2]) await user.click(add(at));

    act(() => cross(1).focus());
    await user.keyboard("{Enter}");

    // The area that stood after it has taken its place, and its cross has the focus.
    expect(chosen()).toHaveLength(2);
    expect(cross(2)).toHaveFocus();

    await user.keyboard("{Enter}");

    // Nothing stood after that one, so the cross of the one before it has the focus.
    expect(chosen()).toHaveLength(1);
    expect(cross(0)).toHaveFocus();
  });

  test("test_the_last_cross_hands_the_focus_to_the_bar_itself_and_never_leaves_it_on_nothing", async () => {
    const { user } = show();
    await user.click(add(0));

    act(() => cross(0).focus());
    await user.keyboard("{Enter}");

    expect(tray()).toHaveAttribute("data-closed", "true");
    expect(tray()).toHaveFocus();
    expect(document.body).not.toHaveFocus();
    // The way on from it is the way on from where the bar stands: the next stop is what follows it.
    await user.tab();
    expect(add(0)).toHaveFocus();
  });

  test("test_the_bar_takes_the_focus_when_it_is_handed_it_and_is_no_stop_of_the_keyboard", async () => {
    const { user } = show(2);

    expect(tray()).toHaveAttribute("tabindex", "-1");
    await user.tab();
    // The first stop is the first button of the page, and never the bar.
    expect(add(0)).toHaveFocus();
    // It is no stop of its own, so it draws no ring: what it sets with the focus is what is drawn, and no more.
    const withTheFocus = STYLES.filter((rule) => /:focus\b/.test(rule.selector) && /^\.tray\b/.test(rule.selector));
    expect(withTheFocus.map((rule) => [rule.selector, [...rule.sets.keys()].sort()])).toEqual([
      [".tray:focus", ["box-shadow", "outline"]],
    ]);
  });

  test("test_the_focus_is_handed_on_without_the_page_being_moved_under_the_person", async () => {
    const { user } = show();
    await user.click(add(0));
    const moved: (FocusOptions | undefined)[] = [];
    const focus = jest.spyOn(HTMLElement.prototype, "focus").mockImplementation((options) => void moved.push(options));

    await user.click(cross(0));
    focus.mockRestore();

    // The bar that is closed stands at the foot of the page, and the person may be anywhere on it.
    expect(moved).toContainEqual({ preventScroll: true });
  });
});

describe("a press that was aimed at what the bar came over", () => {
  // The bar comes at the foot of the screen, which is where the button that was pressed may
  // stand: on a phone the ways on of the first result stand there. What the browser counts as
  // the second press of a double press was aimed at that button, and lands on the bar.

  test("test_the_second_press_of_a_double_press_lands_on_nothing_of_the_bar_that_came_under_it", async () => {
    const { user } = show();
    await user.click(add(0));

    fireEvent.click(cross(0), { detail: 2 });

    // Nothing was taken out: the area that was chosen is still chosen.
    expect(tray()).toHaveAttribute("data-closed", "false");
    expect(chosen()).toHaveLength(1);

    await user.click(add(1));
    const followed = jest.fn((event: Event) => event.preventDefault());
    const go = within(tray()).getByRole("link", { name: TRAY.go(2) });
    go.addEventListener("click", followed);
    fireEvent.click(go, { detail: 2 });
    fireEvent.click(cross(0), { detail: 3 });

    // Nor was the way to the comparison followed, or an area taken out by its cross.
    expect(followed).not.toHaveBeenCalled();
    expect(chosen()).toHaveLength(2);
  });

  test("test_a_press_of_its_own_lands_at_once_and_so_does_a_key", async () => {
    const { user } = show();
    await user.click(add(0));

    fireEvent.click(cross(0), { detail: 1 });
    expect(tray()).toHaveAttribute("data-closed", "true");

    await user.click(add(0));
    act(() => cross(0).focus());
    // A press by keyboard is counted as none.
    await user.keyboard("{Enter}");
    expect(tray()).toHaveAttribute("data-closed", "true");
  });

  /** The bar and the buttons that fill it, on a clock that the test moves on. */
  function onAClock(count: number) {
    jest.useFakeTimers();
    const user = userEvent.setup({ delay: null, advanceTimers: jest.advanceTimersByTime });
    render(
      <SessionProvider>
        <CompareTray />
        {areas.slice(0, count).map((area) => (
          <CompareButton key={area.area_id} area={area} />
        ))}
      </SessionProvider>,
    );
    return user;
  }
  /** As long as a browser may count the next press as the second of a double press, and a moment more. */
  const aMomentLater = () => act(() => void jest.advanceTimersByTime(DOUBLE_PRESS_MS + 1));

  test("test_once_the_bar_has_stood_a_moment_a_double_press_on_it_is_a_press", async () => {
    try {
      const user = onAClock(1);
      await user.click(add(0));

      aMomentLater();
      fireEvent.click(cross(0), { detail: 2 });

      expect(tray()).toHaveAttribute("data-closed", "true");
    } finally {
      jest.useRealTimers();
    }
  });

  test("test_a_bar_that_grew_no_larger_holds_no_press_off", async () => {
    try {
      const user = onAClock(3);
      for (const at of [0, 1, 2]) await user.click(add(at));
      aMomentLater();

      // An area is taken out: the bar is no larger than it was, and nothing came under the pointer.
      await user.click(added(2));
      fireEvent.click(cross(0), { detail: 2 });

      expect(chosen()).toHaveLength(1);
    } finally {
      jest.useRealTimers();
    }
  });
});

describe("what was pressed where the bar then came", () => {
  // The bar comes at the foot of the window, 124 px high at 1440 by 900 and 111 at 390 by
  // 844. Measured in a browser: "Add to compare" stood from 775 to 819 as it was pressed,
  // and the bar came from 776.5: the button that held the focus was under it.

  /** Where a thing stands in the window, from its top to its foot. */
  type Stands = readonly [top: number, foot: number];
  const NOWHERE: Stands = [0, 0];

  /**
   * Lays the page out as a browser would, which jsdom does not: each button where it is
   * said to stand, less what the page was scrolled by, and the bar at the foot of the
   * window once it is open, which stays there as the page goes.
   */
  function laidOut(buttons: (at: HTMLElement) => Stands, bar: Stands = [776.5, 900]) {
    const asked: number[] = [];
    let gone = 0;
    jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
      asked.push(y);
      gone += y;
    }) as typeof window.scrollBy);
    jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
      const isTheBar = this.tagName === "SECTION" && this.hasAttribute("data-closed");
      const [top, foot] = isTheBar
        ? this.getAttribute("data-closed") === "false"
          ? bar
          : NOWHERE
        : this.tagName === "BUTTON" && !this.closest("section")
          ? buttons(this).map((at) => at - gone)
          : NOWHERE;
      return {
        top: top ?? 0,
        bottom: foot ?? 0,
        left: 0,
        right: 300,
        x: 0,
        y: top ?? 0,
        width: 300,
        height: (foot ?? 0) - (top ?? 0),
        toJSON: () => ({}),
      };
    });
    return asked;
  }

  afterEach(() => jest.restoreAllMocks());

  test("test_the_button_that_chose_an_area_is_brought_clear_of_the_bar_that_came_over_it", async () => {
    const asked = laidOut(() => [775, 819]);
    const { user } = show(2);

    await user.click(add(0));

    expect(tray()).toHaveAttribute("data-closed", "false");
    expect(asked).toEqual([819 + OVER_THE_BAR - 776.5]);
    // It keeps the focus, and says what it now does.
    expect(added(0)).toHaveFocus();
  });

  test("test_a_button_pressed_by_keyboard_is_brought_clear_of_the_bar_as_one_pressed_by_hand_is", async () => {
    const asked = laidOut(() => [775, 819]);
    const { user } = show(2);

    act(() => add(1).focus());
    await user.keyboard("{Enter}");

    expect(asked).toEqual([819 + OVER_THE_BAR - 776.5]);
    expect(added(1)).toHaveFocus();
  });

  test("test_a_button_the_bar_did_not_come_over_is_left_where_it_is_and_nothing_moves_under_the_press", async () => {
    const asked = laidOut(() => [300, 344]);
    const { user } = show(2);

    await user.click(add(0));
    await user.click(add(1));

    expect(chosen()).toHaveLength(2);
    expect(asked).toEqual([]);
  });

  test("test_the_press_that_takes_an_area_out_moves_nothing_and_neither_does_a_press_in_the_bar", async () => {
    const asked = laidOut(() => [775, 819]);
    const { user } = show(3);
    for (const at of [0, 1]) await user.click(add(at));
    asked.length = 0;

    await user.click(added(0));
    await user.click(cross(1));

    expect(chosen()).toHaveLength(0);
    expect(asked).toEqual([]);
  });

  test("test_only_the_button_that_was_pressed_is_brought_clear_and_no_other_button_of_the_page", async () => {
    // Every button of the page hears that an area was chosen: one of them was pressed.
    // A button is of its area whatever it says of it: it names the area before the press and after.
    const ofTheSecond = (at: HTMLElement) =>
      [COMPARE.addNamed(nameAt(1)), COMPARE.removeNamed(nameAt(1))].includes(at.getAttribute("aria-label") ?? "");
    const asked = laidOut((at) => (ofTheSecond(at) ? [775, 819] : [300, 344]));
    const { user } = show(3);

    // The button that stands low is not the one that is pressed.
    await user.click(add(0));
    expect(asked).toEqual([]);

    await user.click(add(1));
    expect(asked).toEqual([819 + OVER_THE_BAR - 776.5]);
  });

  test("test_an_area_that_was_chosen_on_another_page_brings_nothing_up_as_this_page_opens", () => {
    const asked = laidOut(() => [775, 819]);
    const first = show(2);
    fireEvent.click(add(0));
    asked.length = 0;
    first.unmount();

    // The page is drawn again with the area chosen already: nothing was pressed on it.
    show(2);

    expect(asked).toEqual([]);
  });
});
