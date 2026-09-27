/**
 * The rabbit in the whole page, for whoever uses a keyboard or hears the page.
 *
 * Burro moves for as long as he is drawn, beside what is read. A button stood by him that
 * stopped him. The founder asked for it to go, and relies on what a person has set in their
 * system: where it asks for less movement he is drawn still. That is held beside him, in
 * his style sheet, since jsdom cannot be asked for less movement.
 *
 * So he is dress, and these hold that he is nothing more: no keyboard stops at him, no
 * screen reader hears him, a press on him moves nothing and asks for nothing, and nothing
 * the page says or does is said or done by him alone.
 *
 * He stood beside what Burro asked, too, up on his hind legs. The founder asked that Burro
 * ask nothing, so no dialogue is drawn and he stands beside none. What was held of him
 * there is held wherever he is drawn: beside the heading, where a search is read, and in
 * what every page stands in once the answer is in.
 *
 * axe runs here in jsdom and cannot judge contrast, size or layout.
 */

import { act, screen, within } from "@testing-library/react";

import { PROMPT, SEARCH } from "@/content/search";
import { SITE } from "@/content/site";

import { setOnline } from "../support/api";
import { faultsIn } from "../support/axe";
import { firstSearch, openSearch, promptBox, results, search, settled, tabOf } from "../support/search";
import { focusGoesOnlyToWhatIsDrawn, theFocusIsOnWhatIsDrawn } from "./drawn";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

type User = Awaited<ReturnType<typeof openSearch>>["user"];

beforeEach(() => {
  setOnline(true);
  focusGoesOnlyToWhatIsDrawn();
});

/** Presses Tab until the focus is on the element, and says everything the focus stopped at on its way. */
async function tabTo(user: User, wanted: () => Element | null): Promise<Element[]> {
  const stops: Element[] = [];
  for (let presses = 0; presses < 200; presses += 1) {
    if (document.activeElement !== null && document.activeElement === wanted()) return stops;
    await user.tab();
    if (document.activeElement !== null) stops.push(document.activeElement);
  }
  throw new Error("Tab never reached it.");
}

/** Every drawing of him on the page, and whether what is drawn of each moves. */
const drawn = () => [...document.querySelectorAll<HTMLElement>("[data-pose]")];
const moves = () => drawn().map((he) => `${he.dataset.pose}: ${he.querySelector("[data-moves]")?.getAttribute("data-moves")}`);
const whereOf = (he: HTMLElement) => (he.closest("header") ? "board" : he.closest("footer") ? "foot" : he.closest("main") ? "page" : "grass");
/** Whatever of the page might be a button of his: one that stands in him, or that names him. */
const hisButtons = () =>
  screen.queryAllByRole("button").filter((button) => button.closest("[data-pose]") !== null || /\brabbit\b/i.test(button.getAttribute("aria-label") ?? ""));
/** Everything in him that a keyboard could stop at or a screen reader could hear. */
const heardOrReached = (he: HTMLElement) => [
  ...he.querySelectorAll("button, a, input, select, textarea, summary, [tabindex], [role], [aria-label], [aria-labelledby], [aria-live]"),
];

/**
 * Every stop of a keyboard from the head of the page to its foot, in the order it comes to
 * them. It begins where a page that has just been opened begins: before its first stop.
 */
async function everyStop(user: User): Promise<Element[]> {
  const had = document.activeElement;
  if (had instanceof HTMLElement) act(() => had.blur());
  const stops: Element[] = [];
  for (let presses = 0; presses < 1000; presses += 1) {
    await user.tab();
    if (document.activeElement === null || document.activeElement === document.body) return stops;
    stops.push(document.activeElement);
  }
  throw new Error("Tab never came to the foot of the page.");
}

/**
 * A search of a sentence that is no plain list of wishes. Burro asked of such a one: what
 * he noticed was offered in a dialogue, and he stood beside it. The page now takes what he
 * noticed of itself, and shows the answer.
 */
async function noticed() {
  const opened = await openSearch(
    firstSearch()
      .on("interpret", "interpret-suggest-who-is-counted")
      .on("rank", "rank-suggestion-chosen")
      .on("explain_top", "explanations-suggestion-chosen"),
  );
  await opened.user.type(promptBox(), "young professionals, lively, near a station");
  await opened.user.click(screen.getByRole("button", { name: PROMPT.submit }));
  await settled();
  return opened;
}

describe("the rabbit, before a search", () => {
  test("test_tab_goes_from_the_head_of_the_page_to_the_two_ways_in_and_stops_at_nothing_of_him", async () => {
    const { user } = await openSearch();

    const stops = await tabTo(user, () => tabOf("quick"));

    // After the links of the head of the page and the link that skips to the map.
    expect(stops.length).toBeLessThanOrEqual(9);
    expect(stops.filter((stop) => stop.closest("[data-pose]") !== null)).toEqual([]);
    expect(stops.filter((stop) => /\brabbit\b/i.test(stop.getAttribute("aria-label") ?? ""))).toEqual([]);
    // Of the page itself, the link that skips to the map and then the tab: no stop of his stands between them.
    const inThePage = stops.filter((stop) => screen.getByRole("main").contains(stop));
    expect(inThePage.map((stop) => (stop === tabOf("quick") ? "the tab" : stop.classList.contains("skip") ? "skips" : stop.tagName))).toEqual([
      "skips",
      "the tab",
    ]);
  });

  test("test_nothing_of_him_is_heard_and_no_button_stands_by_him", async () => {
    await openSearch();

    // He sits beside the heading, and is drawn nowhere else.
    expect(moves()).toEqual(["sits: true"]);
    const [he] = drawn();
    expect(he?.closest("[data-kind='box']")).toContainElement(screen.getByRole("heading", { level: 1, name: SEARCH.title }));
    // The whole of him is kept from whoever hears the page, and holds no word.
    expect(he).toHaveAttribute("aria-hidden", "true");
    expect(he?.textContent).toBe("");
    expect(heardOrReached(he as HTMLElement).filter((one) => one.getAttribute("aria-hidden") !== "true")).toEqual([]);
    expect(within(he as HTMLElement).queryAllByRole("img", { hidden: true })).toEqual([]);
    expect(hisButtons()).toEqual([]);
  });

  test("test_a_press_on_him_moves_nothing_of_the_page_and_asks_nothing_of_the_service", async () => {
    const { user, api, container } = await openSearch();
    await user.type(promptBox(), "leafy and quiet");
    const box = promptBox();
    // The focus is taken from the box first: the box is drawn in hand while it has the
    // focus, and at rest once it has not, whatever took the focus from it.
    await user.click(tabOf("quick"));
    const sent = api.calls.length;
    const was = container.innerHTML;
    const [he] = drawn();

    await user.click(he as HTMLElement);
    await user.dblClick(he as HTMLElement);
    await user.keyboard("{Enter}");
    await user.keyboard(" ");

    // He moves as he moved, and the page is to the letter what it was.
    expect(moves()).toEqual(["sits: true"]);
    expect(container.innerHTML === was).toBe(true);
    expect(api.calls).toHaveLength(sent);
    expect(promptBox()).toBe(box);
    expect(box).toHaveValue("leafy and quiet");
    expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
    expect(document.querySelector("[data-search]")).toHaveAttribute("data-search", "closed");
  });

  test("test_the_page_has_no_fault_with_him_moving", async () => {
    const { container } = await openSearch();

    expect(moves()).toEqual(["sits: true"]);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("the rabbit, where Burro asked and asks nothing now", () => {
  test("test_he_stands_beside_no_question_and_a_keyboard_goes_from_the_head_of_the_page_to_its_foot_with_no_stop_at_him", async () => {
    const { user } = await noticed();

    // No dialogue is drawn, and he stands on his hind legs nowhere. The answer is in, so
    // what every page stands in draws him: in the name board, or over the foot.
    expect(screen.queryByRole("region", { name: "Choose what to add" })).toBeNull();
    expect(results().length).toBeGreaterThan(0);
    expect(drawn().map((he) => [whereOf(he), he.dataset.pose])).toEqual([
      ["board", "sits"],
      ["foot", "sits"],
    ]);
    expect(moves()).toEqual(["sits: true", "sits: true"]);
    for (const he of drawn()) {
      expect(he).toHaveAttribute("aria-hidden", "true");
      expect(he.textContent).toBe("");
      expect(heardOrReached(he).filter((one) => one.getAttribute("aria-hidden") !== "true")).toEqual([]);
    }
    expect(hisButtons()).toEqual([]);
    const [board, foot] = [drawn()[0]?.closest("header"), drawn()[1]?.closest("footer")];
    // A keyboard goes through the board, the answer and the foot, and none of its stops is his.
    const stops = await everyStop(user);
    expect(stops.filter((stop) => stop.closest("[data-pose]") !== null)).toEqual([]);
    expect(stops.filter((stop) => /\brabbit\b/i.test(stop.getAttribute("aria-label") ?? ""))).toEqual([]);
    // In the board he stands after the name and before the pages: a keyboard goes from the one to the others.
    expect(stops.filter((stop) => board?.contains(stop)).map((stop) => stop.textContent)).toEqual([
      SITE.name,
      SITE.nav.vibes,
      SITE.nav.methods,
      SITE.nav.sources,
    ]);
    // It comes to the answer, and to the foot he sits over, where every stop is a link of the foot.
    expect(stops.some((stop) => results()[0]?.contains(stop))).toBe(true);
    const inTheFoot = stops.filter((stop) => foot?.contains(stop));
    expect(inTheFoot.length).toBeGreaterThan(0);
    expect(inTheFoot.filter((stop) => stop.tagName !== "A")).toEqual([]);
    expect(await faultsIn(document.body, { wholePage: true })).toEqual([]);
  });

  test("test_a_press_on_him_in_the_name_board_or_over_the_foot_changes_nothing_of_the_search_and_ranks_nothing", async () => {
    const { user, api, container } = await noticed();
    /** Everything of the search that can be pressed: what was understood, what refines it, and the answer. */
    const pressed = () => within(screen.getByRole("main")).getAllByRole("button").map((button) => button.textContent);
    const were = pressed();
    const sent = api.calls.length;
    const ranked = api.callsTo("rank").length;
    const was = container.innerHTML;

    for (const he of drawn()) {
      await user.click(he);
      await user.dblClick(he);
      await user.keyboard("{Enter}");
      await user.keyboard(" ");
    }

    // He moves as he moved, and the search is to the letter what it was.
    expect(moves()).toEqual(["sits: true", "sits: true"]);
    expect(pressed()).toEqual(were);
    expect(container.innerHTML === was).toBe(true);
    expect(api.calls).toHaveLength(sent);
    expect(api.callsTo("rank")).toHaveLength(ranked);
    expect(document.querySelector("[data-search]")).toHaveAttribute("data-search", "open");
  });

  test("test_where_a_search_is_read_a_keyboard_makes_no_stop_at_him_and_a_press_on_him_neither_ends_the_wait_nor_asks_anything", async () => {
    const api = firstSearch().on("rank", "rank-suggestion-chosen").on("explain_top", "explanations-suggestion-chosen");
    const reading = api.hold("interpret", "interpret-suggest-who-is-counted");
    const { user, container } = await openSearch(api);
    await user.type(promptBox(), "young professionals, lively, near a station");
    await user.keyboard("{Enter}");
    expect(moves()).toEqual(["hops: true"]);
    // A keyboard goes from the head of the page to its foot while he hops. It comes to what
    // ends the wait, which is said in words beside Search, and none of its stops is his.
    // The walk takes the focus from the box, too: the box is drawn in hand while it has the
    // focus, and at rest once it has not, whatever took the focus from it.
    const stop = screen.getByRole("button", { name: PROMPT.stop });
    const stops = await everyStop(user);
    expect(stops).toContain(stop);
    expect(stops.filter((one) => one.closest("[data-pose]") !== null)).toEqual([]);
    expect(stops.filter((one) => /\brabbit\b/i.test(one.getAttribute("aria-label") ?? ""))).toEqual([]);
    expect(heardOrReached(drawn()[0] as HTMLElement).filter((one) => one.getAttribute("aria-hidden") !== "true")).toEqual([]);
    const sent = api.calls.length;
    const was = container.innerHTML;
    const [he] = drawn();

    await user.click(he as HTMLElement);
    await user.dblClick(he as HTMLElement);
    await user.keyboard("{Enter}");
    await user.keyboard(" ");

    // He hops as he hopped, the search is read still, and the page is to the letter what it was.
    expect(moves()).toEqual(["hops: true"]);
    expect(whereOf(drawn()[0] as HTMLElement)).toBe("page");
    expect(container.innerHTML === was).toBe(true);
    expect(api.calls).toHaveLength(sent);
    expect(reading.waiting()).toBe(1);
    expect(screen.getByRole("button", { name: PROMPT.stop })).toBe(stop);
    expect(api.callsTo("rank")).toEqual([]);
    // The answer comes when the search has been read, as it would have come.
    reading.release();
    await settled();
    expect(results().length).toBeGreaterThan(0);
    expect(drawn().map(whereOf)).toEqual(["board", "foot"]);
  });

  test("test_he_sits_beside_the_heading_and_moves_when_the_search_begins_again", async () => {
    const { user, api } = await noticed();
    expect(drawn().map(whereOf)).toEqual(["board", "foot"]);

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    await settled();

    // He is one rabbit: the page draws him again, beside its heading, and what every page
    // stands in draws him no more.
    expect(drawn().map(whereOf)).toEqual(["page"]);
    expect(moves()).toEqual(["sits: true"]);
    expect(drawn()[0]?.closest("[data-kind='box']")).toContainElement(screen.getByRole("heading", { level: 1, name: SEARCH.title }));
    expect(drawn()[0]).toHaveAttribute("aria-hidden", "true");
    expect(hisButtons()).toEqual([]);
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    // And he hops where the search that begins is read, until its answer is in.
    const reading = api.hold("interpret", "interpret-first");
    api.on("rank", "rank-first").on("explain_top", "explanations-first");
    await user.type(promptBox(), "leafy and quiet");
    await user.keyboard("{Enter}");
    expect(drawn().map(whereOf)).toEqual(["page"]);
    expect(moves()).toEqual(["hops: true"]);
    expect(hisButtons()).toEqual([]);
    reading.release();
    await settled();
    expect(drawn().map(whereOf)).toEqual(["board", "foot"]);
    expect(moves()).toEqual(["sits: true", "sits: true"]);
  });
});

describe("the rabbit, while a person waits and once the answer is in", () => {
  test("test_while_a_search_is_read_nothing_of_him_takes_a_press_and_stop_beside_search_is_what_ends_the_wait", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);
    await user.type(promptBox(), "leafy and quiet");
    await user.keyboard("{Enter}");

    // He hops where the results will stand, kept from whoever hears the page, and nothing
    // of him takes a press: what stops the wait is said in words, beside Search.
    expect(moves()).toEqual(["hops: true"]);
    expect(hisButtons()).toEqual([]);
    expect(drawn()[0]?.closest("[aria-hidden='true']")).not.toBeNull();
    expect(drawn()[0]?.querySelectorAll("button, a, input")).toHaveLength(0);
    const stop = screen.getByRole("button", { name: PROMPT.stop });
    await tabTo(user, () => stop);

    await user.keyboard("{Enter}");

    expect(drawn().map((he) => he.dataset.pose)).not.toContain("hops");
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    reading.release();
    await settled();
  });

  test("test_once_the_answer_is_in_the_page_draws_him_no_more_and_what_every_page_stands_in_does", async () => {
    const { user } = await openSearch();
    await search(user);

    // He is one rabbit. While the page drew him he was nowhere else. It draws him no more,
    // so he is seen from his back up in the name board, or over the foot where the board
    // has no room for him: a style sheet draws one of the two.
    expect(drawn().map(whereOf)).toEqual(["board", "foot"]);
    expect(drawn().map((he) => [he.dataset.pose, he.dataset.peeps])).toEqual([
      ["sits", "true"],
      ["sits", "true"],
    ]);
    for (const he of drawn()) {
      expect(he).toHaveAttribute("aria-hidden", "true");
      expect(heardOrReached(he).filter((one) => one.getAttribute("aria-hidden") !== "true")).toEqual([]);
    }
    expect(hisButtons()).toEqual([]);
    // Nothing of him stands among the results, or anywhere in the answer.
    expect(screen.getByRole("main").querySelectorAll("[data-pose]")).toHaveLength(0);
  });
});
