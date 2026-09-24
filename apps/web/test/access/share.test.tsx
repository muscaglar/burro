/**
 * Comparing and sharing from the search page, held to docs/design/web.md
 * section 9: both work by keyboard alone, nothing is told by colour alone,
 * and what happens is said once to a screen reader.
 *
 * axe runs here in jsdom and cannot judge contrast, size or layout.
 */

import { act, screen, within } from "@testing-library/react";

import { COMPARE, TRAY } from "@/content/compare";
import { RESULTS, SEARCH } from "@/content/search";
import { SHARE } from "@/content/share";
import { recordedAnswer } from "@/lib/api/recorded";

import { setOnline } from "../support/api";
import { faultsIn } from "../support/axe";
import { areas, everyResult, firstSearch, openSearch, search, settled } from "../support/search";

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
