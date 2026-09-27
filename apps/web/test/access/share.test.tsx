/**
 * Comparing and sharing from the search page, held to docs/design/web.md
 * section 9: both work by keyboard alone, nothing is told by colour alone,
 * and what happens is said once to a screen reader.
 *
 * axe runs here in jsdom and cannot judge contrast, size or layout.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { act, screen, within } from "@testing-library/react";

import { WAY_TO_COMPARE } from "@/components/CompareTray/look";
import { COMPARE, TRAY } from "@/content/compare";
import { PROMPT, RESULTS, SEARCH } from "@/content/search";
import { SHARE } from "@/content/share";
import { recordedAnswer } from "@/lib/api/recorded";

import { setOnline } from "../support/api";
import { faultsIn } from "../support/axe";
import { rulesOf } from "../support/css";
import { areas, everyResult, firstSearch, openSearch, results, search, settled } from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const ranked = recordedAnswer("rank", "rank-first").body.data;
const made = recordedAnswer("create_share", "share-made").body.data;
const nameAt = (place: number) =>
  areas.find((area) => area.area_id === ranked.ranked[place]?.area_id)?.name ?? "";

type User = Awaited<ReturnType<typeof openSearch>>["user"];

/** Presses Tab until the focus is on the element. */
async function tabTo(user: User, wanted: () => Element | null) {
  for (let presses = 0; presses < 600; presses += 1) {
    if (document.activeElement !== null && document.activeElement === wanted()) return;
    await user.tab();
  }
  throw new Error("Tab never reached it.");
}

async function searched() {
  const opened = await openSearch(firstSearch().on("create_share", "share-made"));
  await search(opened.user);
  return opened;
}

/**
 * Follows "Skip to results", as a person at a keyboard does to get past the
 * form. jsdom does not move the focus when a link within the page is
 * followed, so the focus is put where a browser would put it.
 */
async function skipToResults(user: User) {
  const skip = screen.getByRole("link", { name: SEARCH.skipToResults });
  await tabTo(user, () => skip);
  await user.keyboard("{Enter}");
  const results = document.getElementById((skip.getAttribute("href") ?? "").slice(1));
  if (results === null) throw new Error("The skip link leads nowhere.");
  act(() => results.focus());
}

const tray = () => screen.getByRole("region", { name: TRAY.title });

beforeEach(() => setOnline(true));

describe("sharing, by keyboard", () => {
  test("test_a_search_can_be_shared_by_keyboard_alone", async () => {
    const { user, api } = await searched();

    await skipToResults(user);
    await tabTo(user, () => screen.queryByRole("button", { name: SHARE.open }));
    await user.keyboard("{Enter}");
    await tabTo(user, () => screen.queryByRole("checkbox", { name: SHARE.exact.label }));
    await tabTo(user, () => screen.queryByRole("button", { name: SHARE.make }));
    await user.keyboard(" ");

    const field = await screen.findByRole<HTMLInputElement>("textbox", { name: SHARE.link });
    expect(field.value.endsWith(`/s#${made.share_id}`)).toBe(true);
    expect(api.callsTo("create_share")).toHaveLength(1);
    // The link and the button that copies it come next in the order of the page.
    await tabTo(user, () => field);
    await user.tab();
    expect(screen.getByRole("button", { name: SHARE.copy })).toHaveFocus();
  });

  test("test_making_a_link_does_not_move_the_focus", async () => {
    const { user } = await searched();
    await user.click(screen.getByRole("button", { name: SHARE.open }));
    const make = screen.getByRole("button", { name: SHARE.make });
    act(() => make.focus());

    await user.keyboard("{Enter}");
    await screen.findByRole("textbox", { name: SHARE.link });

    expect(screen.getByRole("button", { name: SHARE.makeAgain })).toHaveFocus();
  });

  test("test_escape_closes_the_panel_and_puts_the_focus_back_on_its_button", async () => {
    const { user } = await searched();
    const open = screen.getByRole("button", { name: SHARE.open });
    await user.click(open);
    await user.tab();

    await user.keyboard("{Escape}");

    expect(open).toHaveAttribute("aria-expanded", "false");
    expect(open).toHaveFocus();
    expect(screen.queryByRole("button", { name: SHARE.make })).toBeNull();
  });

  test("test_that_a_link_was_made_is_said_once_and_politely", async () => {
    const { user } = await searched();
    await user.click(screen.getByRole("button", { name: SHARE.open }));
    const panel = screen.getByRole("region", { name: SHARE.holds.title });

    await user.click(screen.getByRole("button", { name: SHARE.make }));
    await screen.findByRole("textbox", { name: SHARE.link });

    const said = within(panel).getAllByRole("status");
    expect(said).toHaveLength(1);
    expect(said[0]).toHaveTextContent(SHARE.made);
    expect(within(panel).queryByRole("alert")).toBeNull();
  });

  test("test_there_is_nothing_to_share_before_there_is_a_ranking", async () => {
    await openSearch();

    expect(screen.queryByRole("button", { name: SHARE.open })).toBeNull();
  });

  test("test_the_search_page_with_a_link_made_has_no_accessibility_fault", async () => {
    const { user, container } = await searched();
    await user.click(screen.getByRole("button", { name: SHARE.open }));
    await user.click(screen.getByRole("button", { name: SHARE.make }));
    await screen.findByRole("textbox", { name: SHARE.link });

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("comparing, by keyboard", () => {
  test("test_areas_can_be_chosen_and_the_comparison_reached_by_keyboard_alone", async () => {
    const { user } = await searched();

    await skipToResults(user);
    await tabTo(user, () => screen.queryByRole("button", { name: COMPARE.addNamed(nameAt(0)) }));
    await user.keyboard("{Enter}");
    await tabTo(user, () => screen.queryByRole("button", { name: COMPARE.addNamed(nameAt(1)) }));
    await user.keyboard(" ");

    const link = within(tray()).getByRole("link", { name: TRAY.go(2) });
    expect(link.getAttribute("href")).toMatch(/^\/compare\?a=[a-z-]+&a=[a-z-]+$/);
    // The link is a link like any other, in the order of the page. The tray stays at the foot
    // of the screen, and the way on is beside the button that was just pressed as well.
    expect(link.getAttribute("tabindex")).toBeNull();
    const beside = within(screen.getAllByRole("article")[1] as HTMLElement).getByRole("link", { name: TRAY.go(2) });
    expect(beside.getAttribute("href")).toBe(link.getAttribute("href"));
    await user.tab();
    expect(beside).toHaveFocus();
  });

  test("test_every_result_can_be_chosen_to_compare_the_rows_among_them", async () => {
    const { user } = await searched();
    await everyResult(user);

    const add = screen.getAllByRole("button", { name: new RegExp(`^${COMPARE.addShort}: `) });

    expect(add).toHaveLength(ranked.ranked.length);
    expect(add.filter((button) => !button.classList.contains("target-min"))).toEqual([]);
  });

  test("test_choosing_an_area_does_not_move_the_focus_or_ask_the_api_for_anything", async () => {
    const { user, api } = await searched();
    const calls = api.calls.length;
    const add = screen.getByRole("button", { name: COMPARE.addNamed(nameAt(0)) });
    act(() => add.focus());

    await user.keyboard("{Enter}");
    await settled();

    expect(screen.getByRole("button", { name: COMPARE.removeNamed(nameAt(0)) })).toHaveFocus();
    expect(api.calls).toHaveLength(calls);
  });

  test("test_how_many_areas_are_chosen_is_said_in_words", async () => {
    const { user } = await searched();
    // Before anything is chosen the tray says nothing, and is there to be heard when it does.
    expect(within(tray()).getByRole("status")).toBeEmptyDOMElement();

    await user.click(screen.getByRole("button", { name: COMPARE.addNamed(nameAt(0)) }));

    expect(within(tray()).getByRole("status")).toHaveTextContent(TRAY.one);
    expect(within(tray()).getByText(nameAt(0))).toBeInTheDocument();
  });

  test("test_the_tray_takes_no_room_before_anything_is_chosen_and_comes_after_the_results", async () => {
    const { user } = await searched();

    expect(tray()).toHaveAttribute("data-closed", "true");
    expect(
      screen.getByRole("heading", { name: RESULTS.title }).compareDocumentPosition(tray()) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    await user.click(screen.getByRole("button", { name: COMPARE.addNamed(nameAt(0)) }));
    expect(tray()).toHaveAttribute("data-closed", "false");
  });

  test("test_the_search_page_with_areas_chosen_has_no_accessibility_fault", async () => {
    const { user, container } = await searched();
    for (const place of [0, 1, 2, 3]) {
      await user.click(screen.getByRole("button", { name: COMPARE.addNamed(nameAt(place)) }));
    }

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("the button that matters most, with the bar or the panel on the page", () => {
  /** Every button and link of a part that is drawn in cobalt, by what it says. */
  const cobalt = (part: Element) =>
    [...part.querySelectorAll("[data-kind='go']")].map((face) => face.closest("a, button")?.textContent ?? "");
  /** What the bar holds in cobalt, as the one line of the look has it: its one button, or nothing. */
  const ofTheBar = (chosen: number) => (WAY_TO_COMPARE === "go" ? [TRAY.go(chosen)] : []);
  const comesBefore = (one: Element, other: Element) =>
    Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);

  test("test_with_areas_chosen_search_and_the_way_to_compare_are_the_cobalt_buttons_and_never_stand_side_by_side", async () => {
    // Seen in a browser, at both sizes: with two areas chosen, Search at the head of the page
    // and the way to the comparison at its foot were both cobalt, and both in sight. Comparing
    // is a headline since, and its one button is cobalt by one line of the look: the page then
    // holds two, and no more, one at its head and one at the foot of the screen.
    const { user } = await searched();
    for (const place of [0, 1]) await user.click(screen.getByRole("button", { name: COMPARE.addNamed(nameAt(place)) }));

    const go = within(tray()).getByRole("link", { name: TRAY.go(2) });
    expect(cobalt(tray())).toEqual(ofTheBar(2));
    expect(cobalt(screen.getByRole("main"))).toEqual([PROMPT.submit, ...ofTheBar(2)]);
    // Never side by side: Search is of the form at the head of the page, the way to the
    // comparison is of the bar, neither part holds the other, and the results stand between.
    const form = screen.getByRole("region", { name: SEARCH.formLabel });
    const search = within(form).getByRole("button", { name: PROMPT.submit });
    expect([form.contains(tray()), tray().contains(form)]).toEqual([false, false]);
    expect(comesBefore(search, results()[0] as HTMLElement)).toBe(true);
    expect(comesBefore(results().at(-1) as HTMLElement, go)).toBe(true);
    // No result holds one: the way on beside a button that was pressed is a plain link.
    for (const result of results()) expect(cobalt(result)).toEqual([]);
    expect(results().filter((result) => within(result).queryByRole("link", { name: TRAY.go(2) }) !== null)).toHaveLength(2);
  });

  test("test_the_bar_is_held_at_the_foot_of_the_screen_which_is_what_keeps_its_button_from_search", async () => {
    // jsdom lays nothing out, so where the bar stands is read from its style sheet: by what
    // the bar says of itself once an area is chosen, which is what the page draws it with.
    const { user } = await searched();
    await user.click(screen.getByRole("button", { name: COMPARE.addNamed(nameAt(0)) }));
    expect(tray()).toHaveAttribute("data-closed", "false");

    const sheet = readFileSync(path.resolve(__dirname, "../../src/components/CompareTray/CompareTray.module.css"), "utf8");
    const ofTheBarInUse = rulesOf(sheet).filter((rule) => rule.selector === '.tray[data-closed="false"]');
    const placed = ofTheBarInUse.filter((rule) => rule.sets.has("position") || rule.sets.has("inset-block-end"));

    // One rule places it, on a screen of any width, and no other takes it from the foot.
    expect(placed.map((rule) => [rule.under, rule.sets.get("position"), rule.sets.get("inset-block-end")])).toEqual([
      [null, "sticky", "0"],
    ]);
  });

  test("test_the_panel_that_shares_a_search_holds_one_cobalt_button_and_the_bar_under_it_no_more_than_its_own", async () => {
    // What makes the link is the one button of the panel that matters most. Search stands
    // a screen and more over it, and the bar stands under it, at the foot of the screen.
    const { user } = await searched();
    for (const place of [0, 1]) await user.click(screen.getByRole("button", { name: COMPARE.addNamed(nameAt(place)) }));
    await user.click(screen.getByRole("button", { name: SHARE.open }));

    const panel = screen.getByRole("region", { name: SHARE.holds.title });
    expect(cobalt(panel)).toEqual([SHARE.make]);
    expect(cobalt(tray())).toEqual(ofTheBar(2));
    // The panel is no part of the bar, and comes before it in the page.
    expect([panel.contains(tray()), tray().contains(panel)]).toEqual([false, false]);
    expect(comesBefore(panel, tray())).toBe(true);
    expect(cobalt(screen.getByRole("main"))).toEqual([PROMPT.submit, SHARE.make, ...ofTheBar(2)]);
  });

  test("test_before_an_area_is_chosen_the_bar_holds_no_button_and_search_is_the_one_in_cobalt", async () => {
    await searched();

    expect(within(tray()).queryAllByRole("link")).toEqual([]);
    expect(within(tray()).queryAllByRole("button")).toEqual([]);
    expect(cobalt(screen.getByRole("main"))).toEqual([PROMPT.submit]);
  });
});
