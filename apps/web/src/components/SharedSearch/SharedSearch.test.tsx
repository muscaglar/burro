/**
 * The page a shared link opens until the share is open, and what says of an open search
 * that it came from a link, as the look draws them. What opening a share asks for, shows
 * and says is held in test/share.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CHIPS, NOTICE, RESULTS } from "@/content/search";
import { SHARE, SHARED } from "@/content/share";
import { readRecorded, recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { Meta } from "@/lib/api/schema";

import { SessionProvider } from "@/lib/session/session";

import { reasonsFor, standInApi, type StandIn } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { arrived, settled } from "../../../test/support/search";
import { NOTICE_STANDS, NOTICE_STANDS_AT } from "./look";
import { SharedFold, toldBy } from "./SharedFold";
import { SharedHeader, SharedNotice } from "./SharedHeader";
import { SearchApp } from "../SearchApp/SearchApp";
import { SharedSearch } from "./SharedSearch";

const meta = recordedAnswer("get_meta", "meta").body;
const { areas } = recordedAnswer("list_areas", "areas").body.data;
const opened = recordedAnswer("get_share", "share-opened");
const ID = opened.request.path.split("/").pop() ?? "";

/** Puts the browser at the page a shared link opens, with what follows the `#` of the link. */
async function open(fragment: string, api: StandIn = standInApi()) {
  window.location.hash = fragment;
  const view = render(
    <main>
      <SharedSearch meta={meta.data} areas={areas} client={api.client} />
    </main>,
  );
  await arrived();
  return { api, ...view };
}

/** The service that answers a share, which names the release it holds in every answer it gives. */
const sharing = (scenario = "share-opened") =>
  standInApi()
    .movedTo((readRecorded(scenario).body as { meta: Meta }).meta.release_id)
    .on("get_share", scenario)
    .on("explain_top", reasonsFor(scenario, "explanations-share-opened"));

beforeEach(() => window.history.replaceState(null, "", "/s"));
afterEach(() => window.history.replaceState(null, "", "/"));

/**
 * What brings the cream a sentence is read on: a box or a plain frame of the kit, a notice,
 * a failure, a button, which has a ground of its own, and what holds the place of a search.
 */
const ON_CREAM = "[data-kind], .state, .opening, .error, .press, .card";

/** Every sentence in sight that stands in nothing which brings cream, and so would be read on the grass. */
function readOnTheGrass(page: Element): string[] {
  const found: string[] = [];
  const walker = page.ownerDocument.createTreeWalker(page, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node !== null; node = walker.nextNode()) {
    const text = node.textContent?.trim() ?? "";
    const held = node.parentElement;
    if (text === "" || held === null) continue;
    if (held.closest(".visually-hidden, noscript, script, style") !== null) continue;
    if (held.closest(ON_CREAM) === null) found.push(text);
  }
  return found;
}

const page = (container: HTMLElement) => container.querySelector("main")?.firstElementChild as HTMLElement;
/** What a button is drawn as: the kind its face bears. */
const drawnAs = (button: HTMLElement) => button.querySelector("[data-kind]")?.getAttribute("data-kind");

describe("the page a shared link opens, until the share is open", () => {
  test.each([
    ["with no id", "", standInApi()],
    ["with what is no id", "nothing-like-an-id", standInApi()],
    ["that leads nowhere", ID, standInApi().on("get_share", "share-not-found")],
    ["that cannot be reached", ID, standInApi().unreachable("get_share")],
  ] as const)("test_nothing_is_read_on_the_grass_of_a_link_%s", async (_, fragment, api) => {
    const { container } = await open(fragment, api);

    expect(page(container)).toHaveAttribute("data-dressed");
    expect(container.textContent?.length).toBeGreaterThan(100);
    expect(readOnTheGrass(page(container))).toEqual([]);
  });

  test("test_nothing_is_read_on_the_grass_while_a_share_is_being_opened", async () => {
    const api = standInApi();
    api.hold("get_share", "share-opened");
    const { container } = await open(ID, api);

    expect(screen.getByRole("status")).toHaveTextContent(SHARED.opening);
    expect(screen.getByRole("status")).toHaveClass("opening");
    expect(container.querySelector("[aria-busy='true']")).not.toBeNull();
    expect(readOnTheGrass(page(container))).toEqual([]);
  });

  test("test_what_the_page_is_and_what_a_share_holds_stand_in_one_box_at_its_head", async () => {
    const { container } = await open("");
    const head = page(container).firstElementChild as HTMLElement;

    expect(head).toHaveAttribute("data-kind", "box");
    expect([...head.children].map((part) => part.textContent)).toEqual([SHARED.title, SHARED.holds]);
    expect(within(head).getByRole("heading", { level: 1 })).toHaveTextContent(SHARED.title);
  });

  test.each([
    ["no id", "", SHARED.none],
    ["what is no id", "nothing-like-an-id", SHARED.notOne],
  ] as const)("test_an_address_with_%s_is_answered_with_a_notice_and_the_one_way_on_is_the_button_that_matters_most", async (_, fragment, says) => {
    await open(fragment);
    const notice = screen.getByRole("status");

    expect(notice).toHaveClass("state");
    expect([...notice.children].map((part) => part.textContent)).toEqual([says.title, says.text, SHARED.own]);
    const own = within(notice).getByRole("link", { name: SHARED.own });
    expect(own).toHaveAttribute("href", "/");
    expect(own).toHaveClass("press", "target");
    expect(drawnAs(own)).toBe("go");
    expect(screen.getAllByRole("link")).toEqual([own]);
    expect(screen.queryByRole("button")).toBeNull();
  });

  test("test_a_link_that_leads_nowhere_is_a_failure_and_the_one_way_on_is_the_button_that_matters_most", async () => {
    const failure = recordedError("share-not-found");
    await open(ID, standInApi().on("get_share", "share-not-found"));
    const alert = await screen.findByRole("alert");

    expect(alert).toHaveClass("error");
    expect([...alert.children].slice(0, 3).map((part) => part.textContent)).toEqual([
      SHARED.failedTitle,
      failure.body.error.message,
      `${NOTICE.requestId} ${failure.headers["x-request-id"]}`,
    ]);
    // Asking again would be told the same, so it is not offered.
    expect(within(alert).queryByRole("button")).toBeNull();
    expect(drawnAs(within(alert).getByRole("link", { name: SHARED.own }))).toBe("go");
  });

  test("test_a_share_that_cannot_be_reached_can_be_tried_again_and_that_is_the_button_that_matters_most", async () => {
    await open(ID, standInApi().unreachable("get_share"));
    const alert = await screen.findByRole("alert");

    const again = within(alert).getByRole("button", { name: SHARED.tryAgain });
    const own = within(alert).getByRole("link", { name: SHARED.own });

    expect([drawnAs(again), drawnAs(own)]).toEqual(["go", "plain"]);
    for (const way of [again, own]) expect(way).toHaveClass("press", "target");
    // They are in the order they had: the way to try again, and then the other way on.
    expect(again.compareDocumentPosition(own) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(alert.querySelectorAll("[data-kind='go']")).toHaveLength(1);
  });

  test("test_trying_again_leaves_the_focus_where_the_share_is_being_opened_and_never_on_nothing", async () => {
    // Seen in a browser: the button went with the failure it stood in, and the focus was left on nothing.
    const api = standInApi().unreachable("get_share");
    const { container } = await open(ID, api);
    const user = userEvent.setup({ delay: null });
    const became = page(container).querySelector(".became") as HTMLElement;
    api.hold("get_share", "share-opened");

    act(() => within(screen.getByRole("alert")).getByRole("button", { name: SHARED.tryAgain }).focus());
    await user.keyboard("{Enter}");

    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent(SHARED.opening);
    expect(became).toContainElement(screen.getByRole("status"));
    expect(became).toHaveFocus();
    expect(became).toHaveAttribute("tabindex", "-1");
  });

  test.each([
    ["with no id", "", standInApi()],
    ["that leads nowhere", ID, standInApi().on("get_share", "share-gone")],
    ["that cannot be reached", ID, standInApi().unreachable("get_share")],
  ] as const)("test_the_page_of_a_link_%s_has_no_accessibility_fault", async (_, fragment, api) => {
    const { container } = await open(fragment, api);

    expect(await faultsIn(container)).toEqual([]);
  });
});

const CSS = readFileSync(path.join(__dirname, "SharedSearch.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
const setsOf = (selector: string) =>
  new Map(STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));
/** Whatever rule of this sheet sets a thing out of sight. There is none: the search page keeps its title so itself. */
const OUT_OF_SIGHT = STYLES.filter((rule) => rule.sets.has("clip-path") || rule.sets.has("clip"));

describe("the page a shared link opens, once the share is open", () => {
  const chips = () => screen.getByRole("region", { name: CHIPS.setLabel });
  const firstResult = () => within(screen.getByRole("list", { name: RESULTS.listLabel })).getAllByRole("article")[0] as HTMLElement;
  const comesBefore = (one: Element, other: Element) =>
    Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);

  test("test_the_title_gives_way_to_the_answer_and_is_kept_for_whoever_hears_the_page", async () => {
    // Measured in a browser: the first result of a shared search began at 868 of 844 on a
    // phone and at 1,051 of 900 on a desk, under the title in its box and what says of the
    // search that it was shared.
    const { container } = await open(ID, sharing());
    await settled();
    const held = page(container);

    expect(held).toHaveAttribute("data-dressed");
    // It is still the one heading of the page, and says what the page is.
    const titles = screen.getAllByRole("heading", { level: 1 });
    expect(titles.map((title) => title.textContent)).toEqual([SHARED.title]);
    // The search page keeps it for whoever hears the page, as it keeps its own title: it
    // stands in no box, and nothing of it is drawn over the box of the search.
    expect(titles.map((title) => [title.className, title.closest("[data-kind]")])).toEqual([["visually-hidden", null]]);
    expect(held.querySelectorAll("[data-kind='box'] h1")).toHaveLength(0);
    // The box of the search and the first result are in sight, and come after it.
    expect(comesBefore(titles[0] as HTMLElement, chips())).toBe(true);
    expect(comesBefore(chips(), firstResult())).toBe(true);
    expect([chips(), firstResult()].map((part) => part.closest(".visually-hidden, [hidden]"))).toEqual([null, null]);
  });

  test("test_the_title_is_set_out_of_sight_as_whatever_is_kept_for_a_screen_reader_is_and_is_not_taken_off_the_page", async () => {
    const base = rulesOf(readFileSync(path.join(__dirname, "..", "..", "styles", "base.css"), "utf8"));
    const kept = base.find((rule) => rule.selector === ".visually-hidden" && rule.under === null);
    await open(ID, sharing());
    await settled();

    // What keeps it is the one rule of the website that keeps a thing for a screen reader:
    // it is cut to nothing and takes no room, and is not taken off the page.
    expect(kept).toBeDefined();
    expect(kept?.sets.get("clip-path")).toBe("inset(50%)");
    expect([kept?.sets.has("display"), kept?.sets.has("visibility")]).toEqual([false, false]);
    expect(screen.getByRole("heading", { level: 1, name: SHARED.title })).not.toHaveAttribute("hidden");
    // What is not drawn at all is not heard either. Nothing of the page is taken off it so:
    // only the mark a browser draws of its own beside a line that opens.
    const takenOff = STYLES.filter((rule) => rule.sets.get("display") === "none" || rule.sets.has("visibility"));
    expect(takenOff.map((rule) => rule.selector)).toEqual([".opens > summary::-webkit-details-marker"]);
  });

  test("test_no_rule_of_this_sheet_reaches_into_the_search_page_to_set_its_title_out_of_sight", () => {
    // The title was set out of sight from here, by a rule that named the box the search page
    // drew it in and had to weigh more than what the kit and that page said of the box. The
    // search page keeps the title itself now, so nothing here names what that page draws:
    // whichever sheet is read last, the title is out of sight.
    expect(OUT_OF_SIGHT.map((rule) => rule.selector)).toEqual([]);
    expect(ALL.filter((rule) => /h1/.test(rule.selector) && !/^\.page/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    expect(ALL.filter((rule) => /:has\(/.test(rule.selector) || /\[data-kind/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_what_says_that_the_search_was_shared_stands_where_the_one_line_says_and_the_answer_comes_first", async () => {
    await open(ID, sharing());
    await settled();
    const way = screen.queryByRole("button", { name: SHARED.title });

    if (NOTICE_STANDS === "after") {
      // Nothing of it stands over the answer: the way to it is a fold, closed, after the
      // first result and directly after the way to share a search.
      expect(screen.queryByRole("region", { name: SHARED.title })).toBeNull();
      expect(way).not.toBeNull();
      expect(way?.getAttribute("aria-expanded")).toBe("false");
      expect(comesBefore(chips(), firstResult())).toBe(true);
      expect(comesBefore(firstResult(), way as HTMLElement)).toBe(true);
      const share = screen.getByRole("button", { name: SHARE.open });
      expect(share.parentElement?.nextElementSibling === way?.parentElement).toBe(true);
    } else {
      // It is one line over the box, which opens in place.
      const notice = screen.getByRole("region", { name: SHARED.title });
      expect(comesBefore(notice, chips())).toBe(true);
      expect(notice.querySelector("details")?.open).toBe(false);
    }
  });

  test.each([...NOTICE_STANDS_AT])("test_an_open_share_has_no_accessibility_fault_whichever_way_it_says_that_it_was_shared: %s", async (stands) => {
    const { container } = await open(ID, sharing());
    await settled();
    if (stands === NOTICE_STANDS) {
      const way = screen.queryByRole("button", { name: SHARED.title });
      if (way !== null) await userEvent.setup({ delay: null }).click(way);
    }

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the way from a shared search to a search of one's own", () => {
  /** jsdom follows no link, and says so loudly: the press is made, and the test draws the page it leads to. */
  const leadsNowhere = (event: Event) => event.preventDefault();
  beforeEach(() => document.addEventListener("click", leadsNowhere));
  afterEach(() => document.removeEventListener("click", leadsNowhere));

  /** The page a shared link opens and the search page, in one session, as the shell of the website holds them. */
  const shared = (api: StandIn) => (
    <SessionProvider>
      <main>
        <SharedSearch meta={meta.data} areas={areas} client={api.client} />
      </main>
    </SessionProvider>
  );
  const searchPage = (api: StandIn) => (
    <SessionProvider>
      <main>
        <SearchApp meta={meta.data} areas={areas} client={api.client} />
      </main>
    </SessionProvider>
  );
  async function opened() {
    const api = sharing();
    window.location.hash = ID;
    const view = render(shared(api));
    await arrived();
    await settled();
    return { api, user: userEvent.setup({ delay: null }), ...view };
  }

  test("test_it_begins_a_search_of_ones_own_and_leaves_nothing_of_the_shared_one_open", async () => {
    // Walked by keyboard: "Start again" on the page a shared link opens starts nothing again,
    // since the search a link holds is opened again as the link holds it. And the search
    // page keeps the search that is open, so the way to it led to the shared search once more.
    const { api, user, rerender } = await opened();
    expect(screen.getAllByRole("article").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: SHARED.title }));
    await user.click(screen.getByRole("link", { name: SHARED.own }));
    // The page the link leads to is drawn in place of this one, in the same session.
    window.history.replaceState(null, "", "/");
    rerender(searchPage(api));
    await arrived();

    // As the search page first stands: two ways in, no result, and nothing that says a search came from a link.
    expect(screen.getAllByRole("tab")).toHaveLength(2);
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect(screen.queryByRole("button", { name: SHARED.title })).toBeNull();
    expect(screen.queryByRole("region", { name: CHIPS.setLabel })).toBeNull();
    // Nothing more was asked of the service for it: the share is not opened again.
    expect(api.callsTo("get_share")).toHaveLength(1);
  });

  test("test_left_by_any_other_way_the_search_is_kept_as_it_is_for_whoever_comes_back", async () => {
    const { api, rerender } = await opened();
    const results = screen.getAllByRole("article").length;

    window.history.replaceState(null, "", "/");
    rerender(searchPage(api));
    await arrived();

    expect(screen.getAllByRole("article")).toHaveLength(results);
    expect(screen.queryAllByRole("tab")).toEqual([]);
  });

  test("test_opened_in_another_tab_it_leaves_this_page_as_it_is", async () => {
    // With a key held down a link is opened elsewhere, where the search page begins afresh.
    const { api, user, rerender } = await opened();
    const results = screen.getAllByRole("article").length;
    await user.click(screen.getByRole("button", { name: SHARED.title }));

    fireEvent.click(screen.getByRole("link", { name: SHARED.own }), { metaKey: true });
    rerender(shared(api));
    await arrived();

    expect(screen.getAllByRole("article")).toHaveLength(results);
    // Should this page be left later by another way, the search is kept.
    window.history.replaceState(null, "", "/");
    rerender(searchPage(api));
    await arrived();
    expect(screen.getAllByRole("article")).toHaveLength(results);
  });
});

describe("what says that a search came from a link", () => {
  const shared = { coarsened: true, stale: true, original_release_id: opened.body.data.original_release_id };
  const release = opened.body.meta.release_id;
  const ALL_OF_IT = [
    SHARED.text,
    SHARED.holds,
    SHARED.coarsened,
    `${SHARED.stale} ${SHARED.madeOn} ${shared.original_release_id}. ${SHARED.shownOn} ${release}.`,
    // The way to a search of one's own, which is the last thing of it.
    SHARED.own,
  ];
  /** What can be pressed in it: the way to a search of one's own, and nothing else. */
  const pressedIn = (notice: HTMLElement) =>
    [...notice.querySelectorAll("a, button, input")].map((way) => `${way.tagName} ${way.getAttribute("href")} ${way.textContent}`);

  test("test_over_the_box_it_is_a_notice_of_one_line_in_a_plain_frame_of_the_kit_which_opens_in_place", () => {
    render(<SharedHeader shared={shared} release={release} hasPlaces stands="over" />);
    const header = screen.getByRole("region", { name: SHARED.title });

    expect(header.tagName).toBe("SECTION");
    expect(header).toHaveAttribute("data-kind", "plain");
    expect(header).toHaveClass("header");
    // It is flat: a box with a shadow is for what a person acts on, and this is read.
    expect(header.querySelector("[data-kind='box'], [data-kind='box-on']")).toBeNull();
    expect(pressedIn(header)).toEqual([`A / ${SHARED.own}`]);
    // The browser's own element, closed: what is in sight is the line that says what the search is.
    const opens = header.firstElementChild as HTMLDetailsElement;
    expect([header.children.length, opens.tagName, opens.open]).toEqual([1, "DETAILS", false]);
    const line = opens.querySelector("summary") as HTMLElement;
    expect(line).toHaveClass("target-min");
    expect(line.textContent).toBe(SHARED.title);
    // The arrow is dress, and says nothing.
    expect([...line.children].map((part) => part.getAttribute("class"))).toEqual(["mark", "title"]);
    expect(line.querySelector(".mark [aria-hidden='true']")).not.toBeNull();
  });

  test("test_over_the_box_it_says_what_it_said_in_the_order_it_said_it", () => {
    const { rerender } = render(<SharedHeader shared={shared} release={release} hasPlaces stands="over" />);
    const header = () => screen.getByRole("region", { name: SHARED.title });
    const said = () => [...(header().querySelector("details > div")?.children ?? [])].map((part) => part.textContent);

    expect(said()).toEqual(ALL_OF_IT);
    expect(within(header()).getByRole("heading", { level: 2 })).toHaveTextContent(SHARED.title);

    // Where the heading of the page says it is a shared search, the line is no heading of its own.
    rerender(
      <SharedHeader shared={{ ...shared, coarsened: false, stale: false }} release={release} hasPlaces titled={false} stands="over" />,
    );
    expect(said()).toEqual([SHARED.text, SHARED.holds, SHARED.exact, SHARED.own]);
    expect(within(header()).queryByRole("heading")).toBeNull();
    expect(header().querySelector("summary")?.textContent).toBe(SHARED.title);
  });

  test("test_where_it_stands_after_the_first_result_nothing_of_it_is_drawn_over_the_box", () => {
    const { container } = render(<SharedHeader shared={shared} release={release} hasPlaces stands="after" />);

    expect(container.innerHTML).toBe("");
  });

  test("test_what_a_fold_opens_to_is_a_notice_that_says_all_of_it_in_the_order_it_was_said", () => {
    render(<SharedNotice shared={shared} release={release} hasPlaces />);
    const notice = screen.getByRole("region", { name: SHARED.title });

    expect([notice.tagName, notice.getAttribute("data-kind")]).toEqual(["SECTION", "plain"]);
    expect(notice).toHaveClass("header");
    expect([...notice.children].map((part) => part.textContent)).toEqual(ALL_OF_IT);
    // What opened it says what it is, so it has no heading.
    expect(notice.querySelector("h1, h2, h3, details")).toBeNull();
    expect(pressedIn(notice)).toEqual([`A / ${SHARED.own}`]);
  });

  test("test_it_ends_in_the_way_to_a_search_of_ones_own", () => {
    // Walked by keyboard: "Start again" on the page a shared link opens starts nothing
    // again, since the search a link holds is opened again as the link holds it. A person who
    // was sent a link and wanted a search of their own had to find the name of the website
    // in the name board. The way to it stands where the page says the search came from a link.
    render(<SharedNotice shared={{ ...shared, coarsened: false, stale: false }} release={release} hasPlaces={false} />);
    const own = screen.getByRole("link", { name: SHARED.own });

    expect(own).toHaveAttribute("href", "/");
    expect(own).toHaveClass("press", "target");
    // It is no button that matters most: what matters most on a search is Search.
    expect(own.querySelector("[data-kind]")).toHaveAttribute("data-kind", "plain");
    expect(own.closest("p")).toBe(screen.getByRole("region", { name: SHARED.title }).lastElementChild);
    expect(SHARED.own).toMatch(/search of your own/);
  });

  test("test_the_way_to_it_is_a_fold_that_is_closed_until_it_is_pressed_and_opens_in_place", async () => {
    await open(ID, sharing());
    await settled();
    if (NOTICE_STANDS !== "after") return;
    const user = userEvent.setup({ delay: null });
    const way = screen.getByRole("button", { name: SHARED.title });

    expect(way).toHaveClass("target");
    expect(way).toHaveAttribute("aria-expanded", "false");
    expect(document.getElementById(way.getAttribute("aria-controls") ?? "")?.hidden).toBe(true);

    await user.click(way);

    expect(way).toHaveAttribute("aria-expanded", "true");
    const notice = screen.getByRole("region", { name: SHARED.title });
    expect(document.getElementById(way.getAttribute("aria-controls") ?? "")?.contains(notice)).toBe(true);
    expect([...notice.children].map((part) => part.textContent)).toEqual([
      SHARED.text,
      SHARED.holds,
      SHARED.coarsened,
      SHARED.own,
    ]);
    // The focus stays on what was pressed, and Escape closes what it opened.
    expect(document.activeElement === way).toBe(true);
    await user.keyboard("{Escape}");
    expect(way).toHaveAttribute("aria-expanded", "false");
    expect(document.activeElement === way).toBe(true);
  });

  test("test_a_search_that_came_from_no_link_has_no_way_to_what_says_that_it_did", () => {
    // Drawn where no search is open at all, as a part shown on its own is.
    const { container } = render(<SharedFold stands="after" />);

    expect(container.innerHTML).toBe("");
    expect(toldBy(null)).toBeNull();
  });

  test.each([...NOTICE_STANDS_AT])("test_it_has_no_accessibility_fault: %s", async (stands) => {
    const { container } = render(
      stands === "over" ? (
        <SharedHeader shared={shared} release={release} hasPlaces stands="over" />
      ) : (
        <SharedNotice shared={shared} release={release} hasPlaces />
      ),
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the style sheet of a shared search", () => {
  test("test_a_notice_is_cream_inside_a_rule_of_ink_with_a_band_of_amber_and_its_words_in_ink", () => {
    for (const selector of [".header", ".state", ".opening"]) {
      const sets = setsOf(selector);
      expect([selector, sets.get("background"), sets.get("border"), sets.get("color"), sets.get("box-shadow")]).toEqual([
        selector,
        "var(--notice-bg)",
        "var(--edge) solid var(--notice-edge)",
        "var(--notice-text)",
        "inset var(--band) 0 0 var(--notice-mark)",
      ]);
    }
  });

  test("test_a_failure_is_cream_inside_a_rule_of_ink_with_a_band_of_poppy_and_its_words_in_ink", () => {
    const sets = setsOf(".error");

    expect([sets.get("background"), sets.get("border"), sets.get("color"), sets.get("box-shadow")]).toEqual([
      "var(--bg)",
      "var(--edge) solid var(--border)",
      "var(--text)",
      "inset var(--band) 0 0 var(--error-edge)",
    ]);
    expect(setsOf(".errorTitle").get("color")).toBe("var(--error)");
    expect(STYLES.filter((rule) => rule.sets.get("color") === "var(--error-edge)").map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_notice_ends_where_the_edge_of_ink_of_a_box_ends", () => {
    // Measured in a browser, at 1440 by 900: the edge of ink of the box at the head of the
    // page ended at 1,314, and the edge of the notice under it at 1,320. A box of the kit
    // keeps the room of its shadow inside itself, two art pixels at its far side.
    const kit = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Frame", "Frame.module.css"), "utf8"));
    expect(kit.find((rule) => rule.selector === ".box::before" && rule.under === null)?.sets.get("inset")).toBe("calc(var(--px) * -4)");

    // What became of a link stands under the box at the head of the page, and what says a
    // search came from a link among the boxes of the search page.
    expect(setsOf(".became").get("padding-inline-end")).toBe("calc(var(--px) * 2)");
    expect(setsOf(".header").get("margin-inline-end")).toBe("calc(var(--px) * 2)");
  });

  test("test_the_line_of_a_notice_that_opens_is_as_the_search_page_draws_one", () => {
    // What was asked for and is not in the data is such a line, under the box of the search.
    const theirs = rulesOf(readFileSync(path.join(__dirname, "..", "NotInData", "NotInData.module.css"), "utf8"));
    const of = (rules: typeof theirs, selector: string) =>
      rules.find((rule) => rule.selector === selector && rule.under === null)?.sets;

    // The arrow has the room it has there.
    expect([...(of(STYLES, ".mark") ?? [])].filter(([property]) => /^(width|height)$/.test(property))).toEqual(
      [...(of(theirs, ".mark") ?? [])].filter(([property]) => /^(width|height)$/.test(property)),
    );
  });

  test("test_the_arrow_of_the_line_stands_at_its_far_end_and_points_down_while_it_is_closed_and_up_while_it_is_open", () => {
    // The founder, of the settings: "place the arrow to the right of the button and make it
    // clearer that they are collapsable". Walked since: what folds was drawn four ways, and
    // this line had its arrow before its words, pointing at them. It is drawn as every fold
    // of the look is: the drawing points up, and is turned half way round while the line is closed.
    const fold = rulesOf(readFileSync(path.join(__dirname, "..", "Disclosure", "Disclosure.module.css"), "utf8"));
    const of = (rules: typeof fold, selector: string) =>
      rules.find((rule) => rule.selector === selector && rule.under === null)?.sets;

    // It comes first in the page and is laid out last, as the arrow of a bar that folds is.
    expect(of(fold, ".bar .mark")?.get("order")).toBe("1");
    expect(of(STYLES, ".mark")?.get("order")).toBe(of(fold, ".bar .mark")?.get("order"));
    // What a bar says is as wide as the bar, which stands its arrow at its far end. This line
    // says as much as it says and no more, so the room that is left stands before its arrow.
    expect(of(STYLES, ".mark")?.get("margin-inline-start")).toBe("auto");
    expect(of(fold, ".bar .mark::before")?.get("transform")).toBe("rotate(180deg)");
    expect(of(STYLES, ".mark")?.get("transform")).toBe(of(fold, ".bar .mark::before")?.get("transform"));
    expect(of(fold, '.bar[aria-expanded="true"] .mark::before')?.get("transform")).toBe("none");
    expect(of(STYLES, ".opens[open] > summary > .mark")?.get("transform")).toBe(
      of(fold, '.bar[aria-expanded="true"] .mark::before')?.get("transform"),
    );
  });

  test("test_what_the_line_opens_to_stands_under_a_whole_rule_and_the_browsers_own_mark_is_not_drawn", () => {
    const theirs = rulesOf(readFileSync(path.join(__dirname, "..", "NotInData", "NotInData.module.css"), "utf8"));
    const of = (rules: typeof theirs, selector: string) =>
      rules.find((rule) => rule.selector === selector && rule.under === null)?.sets;

    // What it is, is a short label in the face of names, and what it opens to stands under a
    // rule of ink that is whole: the founder asked that no edge be dashed.
    expect(of(STYLES, ".opens > summary > .title")?.get("font")).toBe(of(theirs, ".title")?.get("font"));
    expect(of(STYLES, ".says")?.get("border-block-start")).toBe("var(--edge) solid var(--border)");
    expect(CSS.replace(/\/\*[\s\S]*?\*\//g, "").match(/\b(dashed|dotted)\b/g) ?? []).toEqual([]);
    // The browser's own mark is not drawn beside the arrow of the look.
    expect(of(STYLES, ".opens > summary")?.get("list-style")).toBe("none");
    expect(of(STYLES, ".opens > summary::-webkit-details-marker")?.get("display")).toBe("none");
  });

  test("test_every_colour_a_face_and_a_size_is_a_token_and_nothing_is_dimmed_or_moves", () => {
    expect(CSS.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(CSS.match(/url\([^)]*\)/g) ?? []).toEqual([]);
    expect(CSS).not.toMatch(/var\(--(frame-box|box-shadow)/);
    const faces = STYLES.flatMap((rule) =>
      [...rule.sets].filter(([property]) => property === "font" || property === "font-family").map(([, value]) => value),
    );
    expect(faces.filter((face) => !/var\(--font-(say|name)\)$/.test(face))).toEqual([]);
    // The arrow of a line that opens is turned to point at it, in one step: nothing moves over time.
    const moving = ALL.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(animation|transition|translate|rotate|scale|zoom|opacity|filter)/.test(property)),
    );
    expect(moving.map((rule) => rule.selector)).toEqual([]);
    const turned = ALL.filter((rule) => rule.sets.has("transform"));
    expect(turned.map((rule) => [rule.selector, rule.sets.get("transform")])).toEqual([
      [".mark", "rotate(180deg)"],
      [".opens[open] > summary > .mark", "none"],
    ]);
    // Nothing that holds words has a height of its own, so that text can be made larger:
    // but the square the arrow turns in, which holds none.
    const fixed = ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(height|max-height|block-size|max-block-size)$/.test(property)));
    expect(fixed.map((rule) => rule.selector)).toEqual([".mark"]);
  });

  test("test_what_became_of_a_link_takes_the_focus_when_it_is_handed_it_and_draws_no_ring", () => {
    // It is no stop of its own. What it sets with the focus is what is drawn, and no more.
    const withTheFocus = ALL.filter((rule) => /:(hover|focus|focus-within|focus-visible|active)\b/.test(rule.selector));

    expect(withTheFocus.map((rule) => [rule.selector, [...rule.sets.keys()].sort()])).toEqual([
      [".became:focus", ["box-shadow", "outline"]],
    ]);
  });
});
