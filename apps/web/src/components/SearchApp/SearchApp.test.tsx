/**
 * The search page as it is dressed: which box each part stands in, where Burro
 * is drawn, and the wait while a sentence is read. What a press does, what is
 * sent and what is said are held by the tests of the page, under `test/search`.
 *
 * jsdom lays nothing out. Where a thing stands was measured in a browser: what
 * is held here is what is drawn, and what the style sheet says of it.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { COMPARE } from "@/content/compare";
import { HELPERS } from "@/content/helpers";
import {
  CHIPS,
  FIND_AREA,
  LEFT_OUT,
  NOTICE,
  PROMPT,
  REJECTED,
  REJECTED_LABEL,
  RESULTS,
  SEARCH,
  SHELF,
  STATUS,
  SUGGEST,
  TENURE_CHOICE,
} from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { SHARED } from "@/content/share";
import { TOWNS } from "@/content/towns";
import { DEEP, REFINE } from "@/content/ways";
import { WAIT } from "@/content/wait";
import { recordedAnswer } from "@/lib/api/recorded";
import { SearchProvider } from "@/lib/search/store";
import { ROUND, ROUNDS } from "@/lib/search/wait";
import { SessionBoundary } from "@/lib/session/session";

import { setOnline, standInApi } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { asWritten } from "../../../test/support/contrast";
import { heavier, isFor, rulesOf, weightOf } from "../../../test/support/css";
import {
  areas,
  arrived,
  firstSearch,
  helper,
  meta,
  narrowAgain,
  noisyAtHome,
  openSearch,
  panelOf,
  promptBox,
  removeChip,
  restOfTheList,
  results,
  search,
  settingsAt,
  settled,
  theSettings,
  way,
  ways,
  whatRefines,
  workingOf,
} from "../../../test/support/search";
import { INVITE_STANDS } from "../CompareTray/look";
import { LINE_STANDS, OVER_THE_LIST } from "../ResultList/look";
import { Shell } from "../Shell/Shell";
import { GIVES_WAY, OVER_THE_ANSWER_GIVES_WAY } from "./look";
import { SearchApp, SearchView } from "./SearchApp";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const RULES = rulesOf(readFileSync(path.join(__dirname, "SearchApp.module.css"), "utf8"));
const ALWAYS = RULES.filter((rule) => rule.under === null);
/** What the sheet of the list of results says, which the page lays out and does not draw. */
const OF_THE_LIST = rulesOf(readFileSync(path.join(__dirname, "..", "ResultList", "ResultList.module.css"), "utf8"));

const sentenceOf = (scenario: string) => (recordedAnswer("interpret", scenario).request.body as { text: string }).text;
const theResults = () => screen.getByRole("region", { name: RESULTS.title });
/** The search page itself, without the shell it stands in: the name board of every page is the shell's. */
const thePage = () => document.querySelector("main > [data-dressed]") as HTMLElement;
/** Every drawing of Burro on the search page. */
const burros = () => [...thePage().querySelectorAll<HTMLElement>("[data-pose]")];
const theWait = () => document.querySelector("[data-wait]");
const theBox = () => promptBox().closest("[data-kind]") as HTMLElement;
const chips = () => screen.queryByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel}|${CHIPS.startLabel})$`) });
const status = () =>
  screen
    .getAllByRole("status")
    .filter((line) => line.getAttribute("aria-live") === "polite")
    .map((line) => line.textContent ?? "");
const comesBefore = (one: Element, other: Element) =>
  Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);

type User = Awaited<ReturnType<typeof openSearch>>["user"];

/** Types a sentence after what the box holds and presses Search, and waits for nothing. */
async function send(user: User, text: string) {
  await user.type(promptBox(), text);
  await user.click(screen.getByRole("button", { name: PROMPT.submit }));
}

beforeEach(() => setOnline(true));
afterEach(narrowAgain);

describe("the page on the meadow", () => {
  test("test_the_page_says_that_it_stands_boxes_of_its_own_so_that_the_shell_draws_none_round_it", async () => {
    const { user } = await openSearch();
    const page = () => document.querySelector("main > [data-dressed]");

    expect(page()).toHaveAttribute("data-search", "closed");
    await search(user);
    expect(page()).toHaveAttribute("data-search", "open");
  });

  test("test_before_a_search_the_heading_stands_in_a_box_with_burro_sitting_beside_it", async () => {
    await openSearch();
    const heading = screen.getByRole("heading", { level: 1, name: SEARCH.title });
    const box = heading.closest("[data-kind]") as HTMLElement;

    expect(box).toHaveAttribute("data-kind", "box");
    expect(box.querySelector("[data-pose]")).toHaveAttribute("data-pose", "sits");
    // He sits, at the size of every drawing, and is drawn nowhere else on the page.
    expect(box.querySelector("[data-pose]")).toHaveAttribute("data-stage", "false");
    expect(burros()).toHaveLength(1);
    // What the page is for is read in the box, and he says nothing of it: what is drawn of
    // him is kept from whoever hears the page, and holds no word.
    expect(within(box).getByText(/./, { selector: "p" })).toBeInTheDocument();
    const drawn = box.querySelector("[data-pose] > [aria-hidden='true'], [data-pose][aria-hidden='true']");
    expect(drawn).not.toBeNull();
    expect(drawn?.textContent).toBe("");
    expect((box.querySelector("[data-pose]") as HTMLElement).textContent).toBe("");
  });

  test("test_once_a_search_is_open_the_title_gives_way_and_burro_sits_nowhere", async () => {
    const { user } = await openSearch();
    await search(user);

    const heading = screen.getByRole("heading", { level: 1, name: SEARCH.title });
    expect(heading).toHaveClass("visually-hidden");
    expect(heading.closest("[data-kind]")).toBeNull();
    // Not on a result, not in the list, not on the map. Where the shell draws him in the
    // name board of every page is the shell's to say, and is no part of the search page.
    expect(burros()).toHaveLength(0);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  test("test_the_title_of_a_shared_search_gives_way_to_the_answer_as_the_title_of_the_search_page_does_and_burro_sits_beside_no_open_search", async () => {
    // Measured in a browser: under its title in a box, the first result of a shared search
    // began at 868 of 844 on a phone and at 1,051 of 900 on a desk. So the title of a
    // shared search gives way as the title of the search page does, and says what the page
    // is to whoever hears it. Burro sits before a search, and beside no search that is open.
    const user = userEvent.setup({ delay: null });
    render(
      <Shell meta={meta.meta}>
        <SessionBoundary>
          <SearchProvider meta={meta.data} areas={areas} client={firstSearch().client}>
            <SearchView shared />
          </SearchProvider>
        </SessionBoundary>
      </Shell>,
    );
    await arrived();
    const heading = () => screen.getByRole("heading", { level: 1, name: SHARED.title });
    expect(heading().closest("[data-kind]")?.querySelector("[data-pose]")).toHaveAttribute("data-pose", "sits");

    await search(user);

    // The page keeps it so itself, as it keeps its own: it bears the one class that keeps a
    // thing for a screen reader, and stands in no box, so no sheet of a page draws it.
    expect(heading().className).toBe("visually-hidden");
    expect(heading().closest("[data-kind]")).toBeNull();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.queryByRole("heading", { level: 1, name: SEARCH.title })).toBeNull();
    expect(burros()).toHaveLength(0);
  });

  test("test_the_field_and_what_burro_says_of_the_search_stand_in_one_box", async () => {
    const { user } = await openSearch();
    await search(user);
    const line = screen.getAllByRole("status").find((one) => one.getAttribute("aria-live") === "polite") as HTMLElement;

    expect(theBox()).toHaveAttribute("data-kind", "box");
    expect(theBox()).toContainElement(line);
    expect(theBox()).toContainElement(chips());
    // The answer stands in boxes of its own, under the box.
    expect(theBox()).not.toContainElement(theResults());
    expect(comesBefore(theBox(), theResults())).toBe(true);
  });

  test("test_burro_asks_nothing_and_what_he_noticed_is_what_he_understood_with_the_answer_under_it", async () => {
    // The founder walked the page and wrote: "When running a search, don't ask the user to
    // add anything, assume they want it to be added and just present the results."
    const api = firstSearch()
      .on("interpret", "interpret-suggest-newcomer")
      .on("rank", "rank-suggestion-chosen")
      .on("explain_top", "explanations-suggestion-chosen");
    const { user } = await openSearch(api);
    await search(user, sentenceOf("interpret-suggest-newcomer"));

    // Nothing is offered to be pressed, no dialogue asks, and he stands beside no question.
    expect(screen.queryByRole("heading", { name: "Choose what to add" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Choose what to add" })).toBeNull();
    expect(thePage().textContent?.includes("only when you press it")).toBe(false);
    expect(thePage().querySelectorAll("[data-way], [data-guess]")).toHaveLength(0);
    expect(burros()).toHaveLength(0);
    // The answer is on the page, under what he understood.
    expect(results().length).toBeGreaterThan(0);
    expect(theBox()).toContainElement(chips());
    expect(comesBefore(chips() as HTMLElement, theResults())).toBe(true);
    // All that the search can be pressed by, between what was understood and the answer,
    // is what refines the search. The way to see the words that were not read is held by
    // the line that says some were left out, which stands over what was understood.
    const between = [...thePage().querySelectorAll<HTMLElement>("button, a, input, summary")].filter(
      (control) =>
        !chips()?.contains(control) &&
        comesBefore(chips() as HTMLElement, control) &&
        comesBefore(control, results()[0] as HTMLElement),
    );
    expect(between.map((control) => control.getAttribute("aria-label") ?? control.textContent)).toEqual([REFINE.label]);
    const left = screen.getByRole("status", { name: LEFT_OUT.title });
    expect(comesBefore(left, chips() as HTMLElement)).toBe(true);
    expect(within(left).getAllByRole("button").map((button) => button.textContent)).toEqual([SUGGEST.showUnread]);
  });

  test("test_what_the_second_way_in_says_of_itself_stands_in_a_box_and_the_settings_in_the_next", async () => {
    const { user } = await openSearch();
    await way(user, "deep");

    // The way says what it is, in a box that holds nothing to answer: renting or buying and
    // a place to reach are asked once, by the settings, which stand in the next box.
    const says = within(panelOf("deep")).getByText(DEEP.lead).closest("[data-kind]") as HTMLElement;
    expect(says).toHaveAttribute("data-kind", "box");
    expect(within(says).queryAllByRole("radio")).toEqual([]);
    expect(within(says).queryAllByRole("combobox")).toEqual([]);
    const tenure = screen.getAllByRole("radio", { name: TENURE_CHOICE.rent });
    expect(tenure).toHaveLength(1);
    expect(theSettings()).toContainElement(tenure[0] as HTMLElement);
    expect(theSettings()).toHaveAttribute("data-kind", "box");
    expect(says).not.toBe(theSettings());
    expect(comesBefore(says, theSettings())).toBe(true);
    // What finds an area by its name is no question of a search: it stands in a box of its
    // own, after the settings and the button that ranks by them.
    const finds = screen.getByRole("textbox", { name: FIND_AREA.labelAlone }).closest("[data-kind]") as HTMLElement;
    expect(finds).toHaveAttribute("data-kind", "box");
    expect(comesBefore(theSettings(), finds)).toBe(true);
    expect(comesBefore(screen.getByRole("button", { name: SETTINGS.rank }), finds)).toBe(true);
  });

  test("test_what_burro_says_stands_where_the_person_is_and_takes_no_place_until_it_says_something", async () => {
    // What he says of a search stands in the box, which is in the first way in. While the
    // second is chosen it stands with the button that makes a search of that way, which
    // is held in sight: so a failure is said in sight, wherever a person is among the groups.
    const { user } = await openSearch();
    const line = () => screen.getAllByRole("status").find((one) => one.getAttribute("aria-live") === "polite") as HTMLElement;
    expect(theBox()).toContainElement(line());

    await way(user, "deep");
    expect(panelOf("deep")).toContainElement(line());
    expect(within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank }).parentElement).toContainElement(line());
    expect(screen.getAllByRole("status").filter((one) => one.getAttribute("aria-live") === "polite")).toHaveLength(1);

    await way(user, "quick");
    expect(theBox()).toContainElement(line());
    // Seen in a browser: while it said nothing it still held a row of the second way, and
    // the chosen tab stood 12 px clear of the box it is laid over. It takes no place there,
    // and is on the page all the same, so that it is heard when it first speaks.
    const silent = ALWAYS.filter((rule) => rule.selector === ".told:not(:has(.says > :not(:empty)))");
    expect(silent.map((rule) => [rule.sets.get("position"), rule.sets.get("display") ?? "as it was"])).toEqual([
      ["absolute", "as it was"],
    ]);
    expect(silent.flatMap((rule) => [...rule.sets.keys()]).filter((property) => /^margin/.test(property))).toEqual([]);
  });

  test("test_no_edge_of_the_page_or_of_what_it_lays_out_is_dashed", () => {
    // The founder: "The dashed border is not understood to a user, please make solid".
    for (const part of ["SearchApp", "Helpers", "PromptBox", "Shelf", "MapView"]) {
      const folder = path.join(__dirname, "..", part);
      const sheets = readdirSync(folder).filter((name) => name.endsWith(".css"));
      expect(sheets.length).toBeGreaterThan(0);
      for (const sheet of sheets) {
        expect([`${part}/${sheet}`, /dashed|dotted/.test(readFileSync(path.join(folder, sheet), "utf8"))]).toEqual([`${part}/${sheet}`, false]);
      }
    }
  });

  test("test_a_part_that_brings_no_box_is_given_a_slip_of_cream_which_weighs_nothing", () => {
    // Nothing is read on the grass. What another component draws loose in the page is laid
    // on cream by the page, by a rule that weighs nothing: whatever the part says of its
    // own ground or its own edge is what is drawn.
    const slips = ALWAYS.filter((rule) => rule.sets.get("background") === "var(--page)" && /:where\(/.test(rule.selector));

    expect(slips.map((rule) => rule.selector)).toEqual([
      ":where(.slip)",
      ":where(.shared, .first, .rest, .noticed) > :where(*)",
    ]);
    for (const rule of slips) {
      expect([rule.selector, weightOf(rule.selector)]).toEqual([rule.selector, [0, 0, 0]]);
      expect([rule.selector, rule.sets.get("border")]).toEqual([rule.selector, "var(--edge) solid var(--border)"]);
    }
  });

  test("test_a_list_of_results_is_given_no_slip_so_that_the_grass_shows_between_one_result_and_the_next", () => {
    const without = ALWAYS.filter((rule) => /> :where\(ol, /.test(rule.selector));

    expect(without.map((rule) => rule.selector)).toEqual([
      ":where(.shared, .first, .rest, .noticed) > :where(ol, ul, [data-kind], [data-wait])",
    ]);
    expect(without.map((rule) => [rule.sets.get("background"), rule.sets.get("border"), rule.sets.get("padding")])).toEqual([
      ["none", "0", "0"],
    ]);
    // It weighs nothing, and takes back the rule before it by coming after it.
    expect(without.map((rule) => weightOf(rule.selector))).toEqual([[0, 0, 0]]);
    const order = ALWAYS.map((rule) => rule.selector);
    expect(order.indexOf(without[0]?.selector ?? "")).toBeGreaterThan(
      order.indexOf(":where(.shared, .first, .rest, .noticed) > :where(*)"),
    );
  });

  test("test_a_part_that_is_a_box_of_the_kit_is_not_boxed_a_second_time", () => {
    // A box of the kit says what kind of box it is. The page lays no slip under one, and a
    // slip that holds nothing but boxes of the kit is no slip.
    const gaveWay = ALWAYS.filter((rule) => rule.selector === ":where(.slip):not(:has(> :not([data-kind])))");

    expect(gaveWay.map((rule) => [rule.sets.get("background"), rule.sets.get("border"), rule.sets.get("padding")])).toEqual([
      ["none", "0", "0"],
    ]);
  });

  test("test_the_place_of_a_result_is_not_boxed_a_second_time", async () => {
    // Seen in a browser: where no area is ranked yet, "Results will show here." stood in an
    // edge twice as thick as the slip over it, and while a ranking that a control asked for
    // was on its way the place of each card was a box inside a second edge, with its shadow
    // on cream. What holds them is no list, so the page laid a slip under it.
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-nothing-read"));
    await search(user, sentenceOf("interpret-nothing-read"));
    const waiting = within(theResults()).getByText(RESULTS.waiting);
    const box = waiting.closest("[data-kind]") as HTMLElement;
    const holds = box.parentElement as HTMLElement;

    expect(box).toHaveAttribute("data-kind", "plain");
    // What holds the box is a part of the page, which holds the box and nothing else.
    expect(holds.parentElement?.className).toBe("first");
    expect([...holds.children].map((part) => part.hasAttribute("data-kind"))).toEqual([true]);
    const gaveWay = ALWAYS.filter(
      (rule) =>
        rule.selector ===
        ":where(.shared, .first, .rest, .noticed) > :where(*):has(> [data-kind]):not(:has(> :not([data-kind])))",
    );
    expect(gaveWay.map((rule) => [rule.sets.get("background"), rule.sets.get("border"), rule.sets.get("padding")])).toEqual([
      ["none", "0", "0"],
    ]);
    // It holds a box, and so is never a part that holds words alone: those keep their slip.
    const order = ALWAYS.map((rule) => rule.selector);
    expect(order.indexOf(gaveWay[0]?.selector ?? "")).toBeGreaterThan(
      order.indexOf(":where(.shared, .first, .rest, .noticed) > :where(*)"),
    );
  });

  test("test_a_list_of_results_stands_on_the_grass_and_each_result_brings_its_own_ground", async () => {
    const { user } = await openSearch();
    await search(user);
    const first = screen.getByRole("list", { name: RESULTS.listLabel });
    const rest = restOfTheList();

    for (const list of [first, rest]) expect(list.tagName).toBe("OL");
    // The rest of the list is a direct part of what the page lays out, and is given no slip.
    expect(rest.parentElement?.className).toBe("rest");
    // The first stands in a part of the list's own, with what the list says under its first
    // result where a result is narrow: what is said there goes where the towns go, by the
    // width of a result, and only what holds both can say how wide that is. That part is
    // the direct part of the page. Nothing stands over the list in it: the first result is
    // the first thing of it.
    const holds = first.parentElement as HTMLElement;
    expect(holds.className).toBe("listed");
    expect(holds.parentElement?.className).toBe("first");
    expect([...holds.children].map((part) => [part.tagName, part.className])).toEqual([
      ["OL", "list"],
      ["P", "underFirst"],
    ]);
    expect(holds.lastElementChild?.textContent).toBe(COMPARE.invite);
    // The page lays a slip under whatever stands loose in it, which that part does. It has
    // none: the list stands on the grass, and what is said under its first result brings
    // the cream it is read on. Its own sheet says so and weighs more than the rule of the
    // page, whichever is read last.
    const slip = ALWAYS.filter((rule) => rule.selector === ":where(.shared, .first, .rest, .noticed) > :where(*)");
    const own = OF_THE_LIST.filter((rule) => rule.selector === ".listed" && rule.under === null);
    expect(slip.map((rule) => [...rule.sets.keys()].sort())).toEqual([["background", "border", "min-width", "padding"]]);
    expect(own.map((rule) => [rule.sets.get("background"), rule.sets.get("border"), rule.sets.get("padding")])).toEqual([
      ["none", "0", "0"],
    ]);
    expect(own.map((rule) => heavier(weightOf(rule.selector), weightOf(slip[0]?.selector ?? "")))).toEqual([true]);
    const said = OF_THE_LIST.filter((rule) => rule.selector === ".underFirst" && rule.under === null);
    expect(said.map((rule) => [rule.sets.get("background"), rule.sets.get("border")])).toEqual([
      ["var(--page)", "var(--edge) solid var(--border)"],
    ]);
    // A result is boxes of the kit and nothing beside them, and a box of the kit is cream:
    // whatever a result says is read on the ground of its own box. The first is a card.
    expect(results().length).toBeGreaterThan(1);
    for (const result of results()) {
      expect(result.children.length).toBeGreaterThan(0);
      expect([...result.children].filter((part) => !part.hasAttribute("data-kind"))).toEqual([]);
    }
    const name = within(results()[0] as HTMLElement).getByRole("heading", { level: 3 });
    expect(name.closest("[data-kind]")).toHaveAttribute("data-kind", "box");
    // What a town is was said in the first result, and was what this saw the ground of a
    // result by. The founder asked for that line to go from the results, so no result says
    // it and nothing of the page does. Where one line of the look puts it back, the rule
    // of it lays no ground of its own: it is read on the ground of its box.
    expect(LINE_STANDS).toBe("none");
    expect(screen.queryByText(TOWNS.line)).toBeNull();
    expect([TOWNS.line, TOWNS.short].filter((said) => thePage().textContent?.includes(said))).toEqual([]);
    expect(OF_THE_LIST.filter((rule) => /\.towns$/.test(rule.selector) && rule.sets.has("background"))).toEqual([]);
  });

  test("test_nothing_of_the_page_moves_or_changes_size_with_the_focus_but_a_link_that_skips", () => {
    const keyed = RULES.filter((rule) => /:(focus|hover|active)/.test(rule.selector));

    expect(keyed.map((rule) => rule.selector).sort()).toEqual([".map:focus", ".results:focus", ".skip:focus-visible"]);
    expect(keyed.filter((rule) => !isFor(rule.selector, "skip")).flatMap((rule) => [...rule.sets.keys()])).toEqual([
      "outline",
      "outline",
    ]);
  });

  test("test_the_first_screen_has_no_accessibility_fault", async () => {
    const { container, user } = await openSearch();
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    await helper(user, "word");
    await user.click(within(screen.getByRole("region", { name: SHELF.title })).getAllByRole("button")[0] as HTMLElement);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("what stands over the first result", () => {
  // The answer comes first. Once a ranking follows a press the first result is in sight
  // without scrolling at 1440 by 900, and whole on the first screen at 390 by 844. Each
  // part of the page had room to spare where it was measured alone. On the whole page, at
  // 1440 by 900 after a plain search, the first result began at 899 of 900: every line that
  // stands over it is taken from it. So what stands there is held here, line by line and in
  // its order. A line that is added fails this, and whoever adds one measures in a browser first.
  //
  // Burro asks nothing, so what stands over the first result is the same whatever the
  // sentence: no offer and no question stands between a press and the answer.
  const page = () => document.querySelector("main > [data-dressed]") as HTMLElement;
  const theLine = () => screen.getAllByRole("status").find((one) => one.getAttribute("aria-live") === "polite") as HTMLElement;
  const theInvitation = () => page().querySelector<HTMLElement>(":scope .refine > .compares");
  const CONTROL = "a[href], button, input, select, textarea";
  /** What a paragraph, a heading or a line is said in: each is one thing said, where it holds no control. */
  const SAID = "p, h1, h2, h3, h4, h5, h6, [role='heading'], [role='status'], [role='alert'], legend, li, dt, dd, figcaption";

  /** What a control is called: its own name, the words of its label, or its words. */
  function nameOf(control: Element): string {
    const named = control.getAttribute("aria-label");
    if (named !== null) return named;
    const labelled = (control.getAttribute("aria-labelledby") ?? "")
      .split(/\s+/)
      .map((id) => document.getElementById(id)?.textContent ?? "")
      .join(" ")
      .trim();
    if (labelled !== "") return labelled;
    const label = control.id === "" ? null : document.querySelector(`label[for="${control.id}"]`);
    return (label?.textContent ?? control.textContent ?? "").trim();
  }

  /** The part of the page a thing stands in, by the name this test gives it. */
  function partOf(thing: Element): string {
    if (thing.matches("a.skip")) return "a way past";
    if (thing.matches("h1")) return "the title";
    if (theLine().contains(thing)) return "the line";
    if (chips()?.contains(thing)) return "understood";
    if (theBox().contains(thing)) return "the box";
    if (thing.closest(".noticed") !== null) return "noticed";
    if (thing.closest(".compares") !== null) return "compares";
    if (thing.closest(".refine") !== null) return "refines";
    if (theResults().contains(thing)) return "the results";
    return "nothing this test knows";
  }

  /**
   * Everything the page says or offers before a part of it, in the order of the page: each
   * control by its name, and every other thing by its words. What is not drawn is left
   * out: what is hidden, what is kept for a browser with scripts off, a drawing, a label,
   * which names its field, what a button that says it is closed would open, and what a
   * line that opens by the browser's own element holds while it is closed.
   */
  function saidBefore(part: Element): { readonly of: string; readonly says: string }[] {
    const closed = new Set(
      [...page().querySelectorAll("[aria-expanded='false'][aria-controls]")].map((button) => button.getAttribute("aria-controls")),
    );
    const found: { of: string; says: string }[] = [];
    const say = (thing: Element, says: string) => found.push({ of: partOf(thing), says: says.replace(/\s+/g, " ").trim() });
    /** True once the part is reached, where the reading ends. */
    const read = (thing: Element): boolean => {
      if (thing === part) return true;
      if (thing.matches("[hidden], [aria-hidden='true'], noscript, label") || closed.has(thing.id)) return false;
      if (thing.matches(CONTROL)) {
        say(thing, nameOf(thing));
        return false;
      }
      if (thing instanceof HTMLDetailsElement) {
        const line = thing.querySelector(":scope > summary");
        if (line !== null) say(line, line.textContent ?? "");
        return thing.open ? [...thing.children].filter((child) => child !== line).some(read) : false;
      }
      const words = [...thing.childNodes].some((child) => child.nodeType === Node.TEXT_NODE && (child.textContent ?? "").trim() !== "");
      const whole = thing.matches(SAID) && !thing.contains(part) && thing.querySelector(`${CONTROL}, details`) === null;
      if ((words || whole) && (thing.textContent ?? "").trim() !== "") {
        say(thing, thing.textContent ?? "");
        return false;
      }
      return [...thing.children].some(read);
    };
    read(page());
    return found;
  }

  /** The parts that stand over a part of the page, each once, in the order they stand in. */
  const partsBefore = (part: Element) =>
    saidBefore(part)
      .map((one) => one.of)
      .filter((of, at, all) => of !== all[at - 1]);

  test("test_after_a_plain_search_every_line_that_stands_over_the_first_result_is_one_of_these_in_this_order", async () => {
    const { user } = await openSearch();
    await search(user);
    const understood = within(chips() as HTMLElement).getAllByRole("button").map(nameOf);

    expect(understood.length).toBeGreaterThan(0);
    expect(saidBefore(results()[0] as HTMLElement)).toEqual([
      // Drawn only while a keyboard is on them, and laid over the page: they take no room.
      { of: "a way past", says: SEARCH.skipToResults },
      { of: "a way past", says: SEARCH.skipToMap },
      // Kept for whoever hears the page. It gave way to the answer, and takes no room.
      { of: "the title", says: SEARCH.title },
      // The box: its label, and the field on one line with its two buttons. Nothing of how
      // words are handled stands beside it.
      { of: "the box", says: PROMPT.labelOpen },
      { of: "the box", says: PROMPT.startAgain },
      { of: "the box", says: PROMPT.submit },
      // What happened, in the box: two lines on a desk, in a frame of their own.
      { of: "the line", says: status()[0] ?? "" },
      // What Burro understood, in the box: its plate, and the chips and nothing else.
      { of: "understood", says: CHIPS.label },
      ...understood.map((says) => ({ of: "understood", says })),
      // One line on the grass: what refines the search, and beside it that areas can be compared.
      { of: "refines", says: REFINE.label },
      { of: "compares", says: COMPARE.invite },
      // Kept for whoever hears the page: it takes no room.
      { of: "the results", says: RESULTS.title },
    ]);
    expect(status()).toEqual([`${STATUS.rankedUnnamed(21)} ${STATUS.first("Farrowmere")} ${STATUS.gaveWay}`]);
    // The box, with what Burro says of the search and what he understood in it. One line for
    // what refines the search and what says that areas can be compared. And the answer.
    expect(partsBefore(results()[0] as HTMLElement)).toEqual([
      "a way past",
      "the title",
      "the box",
      "the line",
      "understood",
      "refines",
      "compares",
      "the results",
    ]);
    // Of those, what takes no room is kept for whoever hears the page, or is a link that skips.
    expect(screen.getByRole("heading", { level: 1 })).toHaveClass("visually-hidden");
    expect(screen.getByRole("heading", { level: 2, name: RESULTS.title })).toHaveClass("visually-hidden");
    for (const skips of page().querySelectorAll(":scope > a")) expect(skips).toHaveClass("skip");
  });

  test("test_after_a_long_sentence_nothing_is_offered_and_what_stands_over_the_first_result_is_what_stands_there_after_a_plain_one", async () => {
    // What Burro noticed he took of himself: it is among what he understood, and no box of
    // offers stands between the press and the answer.
    const { user } = await openSearch(
      firstSearch().on("interpret", "interpret-suggest-newcomer").on("rank", "rank-first").on("explain_top", "explanations-first"),
    );
    await send(user, "somewhere I might like, I think");
    await settled();
    const understood = within(chips() as HTMLElement).getAllByRole("button").map(nameOf);

    expect(saidBefore(results()[0] as HTMLElement)).toEqual([
      { of: "a way past", says: SEARCH.skipToResults },
      { of: "a way past", says: SEARCH.skipToMap },
      { of: "the title", says: SEARCH.title },
      { of: "the box", says: PROMPT.labelOpen },
      { of: "the box", says: PROMPT.startAgain },
      { of: "the box", says: PROMPT.submit },
      { of: "the line", says: theLine().textContent ?? "" },
      // One line, which names what was left out of the search: here, that some of the
      // words were not read, which changes what the ranking means. Why, and the way to see
      // which words they were, are one press away.
      { of: "the box", says: `${LEFT_OUT.title}: ${LEFT_OUT.words}` },
      { of: "understood", says: CHIPS.label },
      ...understood.map((says) => ({ of: "understood", says })),
      { of: "refines", says: REFINE.label },
      { of: "compares", says: COMPARE.invite },
      { of: "the results", says: RESULTS.title },
    ]);
    expect(page().textContent?.includes("Choose what to add")).toBe(false);
  });

  test("test_where_a_name_is_borne_by_several_places_nothing_is_asked_and_the_answer_stands_where_it_stands_after_any_search", async () => {
    // His question stood over the answer, 304 px high on a desk, and the first result
    // began at 776 of 900. Nothing is asked now: the first place the service gave is taken.
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");
    const understood = within(chips() as HTMLElement).getAllByRole("button").map(nameOf);

    expect(screen.queryByRole("region", { name: /Which (place|area) did you mean/ })).toBeNull();
    expect(page().textContent).not.toMatch(/Which (place|area) did you mean/);
    expect(saidBefore(results()[0] as HTMLElement)).toEqual([
      { of: "a way past", says: SEARCH.skipToResults },
      { of: "a way past", says: SEARCH.skipToMap },
      { of: "the title", says: SEARCH.title },
      { of: "the box", says: PROMPT.labelOpen },
      { of: "the box", says: PROMPT.startAgain },
      { of: "the box", says: PROMPT.submit },
      { of: "the line", says: theLine().textContent ?? "" },
      { of: "understood", says: CHIPS.label },
      ...understood.map((says) => ({ of: "understood", says })),
      { of: "refines", says: REFINE.label },
      { of: "compares", says: COMPARE.invite },
      { of: "the results", says: RESULTS.title },
    ]);
    expect(theLine().textContent?.includes("Burro has a question about a place.")).toBe(false);
  });

  test("test_nothing_stands_between_the_line_of_what_refines_the_search_and_the_first_result", async () => {
    // Measured at 1440 by 900: a slip of four lines stood there, 92 px high, and the first
    // result began at 899 of 900.
    const { user } = await openSearch();
    await search(user);
    const first = results()[0] as HTMLElement;
    const said = saidBefore(first);
    const from = said.findIndex((one) => one.of === "refines");

    expect(said.slice(from).map((one) => one.of)).toEqual(["refines", "compares", "the results"]);
    // What holds the first result holds nothing before it that is drawn: no paragraph, no
    // slip and no control. The list is the first thing of its part, and the first result of the list.
    expect(OVER_THE_LIST).toBe("nothing");
    const list = screen.getByRole("list", { name: RESULTS.listLabel });
    expect(list.previousElementSibling).toBeNull();
    expect(list.firstElementChild).toContainElement(first);
    expect(list.parentElement?.previousElementSibling).toBeNull();
    expect([...theResults().children].map((part) => [part.tagName, part.className])).toEqual([
      ["H2", "visually-hidden"],
      ["DIV", "first"],
    ]);
    // And nothing of the page stands between the part that refines and the results.
    expect(page().querySelector(".refine")?.nextElementSibling).toBe(theResults());
  });

  test("test_that_areas_can_be_compared_is_said_beside_what_refines_the_search_on_its_line_once_there_is_a_list", async () => {
    // The founder: "Compare function is great, make this more of a highlighted feature".
    // It is said before anybody has chosen an area, in sight, and takes nothing from the answer.
    const { user } = await openSearch();
    expect(theInvitation()).toBeNull();
    await search(user);
    const said = theInvitation() as HTMLElement;

    expect([INVITE_STANDS, OVER_THE_LIST]).toEqual(["over", "nothing"]);
    expect(said.tagName).toBe("P");
    expect(said.textContent).toBe(COMPARE.invite);
    // It stands in the part that refines, after the fold, and is no part of what the fold opens.
    expect(said.parentElement).toBe(whatRefines()?.closest(".refine"));
    expect(said.previousElementSibling).toContainElement(whatRefines());
    expect(said.closest(".visually-hidden, [hidden], [aria-hidden='true']")).toBeNull();
    // It holds nothing that can be pressed: one control stands between what Burro
    // understood and the first result, which is what opens the settings.
    expect(said.querySelectorAll("a, button, input, [tabindex]")).toHaveLength(0);
    const between = [...page().querySelectorAll<HTMLElement>(CONTROL)].filter(
      (control) =>
        !chips()?.contains(control) &&
        control.closest("[hidden]") === null &&
        comesBefore(chips() as HTMLElement, control) &&
        comesBefore(control, results()[0] as HTMLElement),
    );
    expect(between.map(nameOf)).toEqual([REFINE.label]);
    // It says the same whatever is chosen, and does not go when the settings are opened.
    await user.click(whatRefines() as HTMLElement);
    expect(theInvitation()).toBe(said);
    expect(theSettings().contains(said)).toBe(false);
    // The list says it too, under its first result, which is drawn where a result is narrow.
    expect(within(theResults()).getAllByText(COMPARE.invite)).toHaveLength(1);
  });

  test("test_there_is_no_invitation_where_there_is_no_list_to_say_it_of", async () => {
    // Nothing is ranked of words that nothing came of.
    const unread = await openSearch(firstSearch().on("interpret", "interpret-nothing-read"));
    await send(unread.user, sentenceOf("interpret-nothing-read"));
    await settled();
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect(theInvitation()).toBeNull();
    expect(screen.queryByText(COMPARE.invite)).toBeNull();
    unread.unmount();

    // Before a search the part holds the second way in, and says nothing of comparing.
    const before = await openSearch();
    await way(before.user, "deep");
    expect(theInvitation()).toBeNull();
    expect(screen.queryByText(COMPARE.invite)).toBeNull();
  });

  test("test_the_fold_and_what_stands_beside_it_are_one_line_where_a_result_has_room_for_a_town", () => {
    const REFINES = '.refine[data-standing="false"]';
    const WIDE = "@container refines (width > 36rem)";
    const NARROW = "@container refines (max-width: 36rem)";
    const always = (selector: string) => new Map(ALWAYS.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));
    const wide = (selector: string) =>
      new Map(RULES.filter((rule) => rule.under === WIDE && rule.selector === selector).flatMap((rule) => [...rule.sets]));

    // The part says how wide it is, under a name of its own, and only once a search is
    // open: before one it holds the second way in, which is laid out as it was.
    expect(always(REFINES).get("container")).toBe("refines / inline-size");
    expect(RULES.filter((rule) => rule.sets.has("container") || rule.sets.has("container-name")).map((rule) => rule.selector)).toEqual([REFINES]);
    // It goes by the width of the part, which is as wide as a result is, and at the width a
    // result has room for a town from. What the list says under its first result goes by
    // the same width, so that one of the two is drawn and never both.
    expect([...new Set(RULES.filter((rule) => /\.compares\b/.test(rule.selector)).map((rule) => rule.under))]).toEqual([
      null,
      WIDE,
      "@media (forced-colors: active)",
    ]);
    expect([...new Set(RULES.map((rule) => rule.under).filter((under) => /^@container/.test(under ?? "")))]).toEqual([NARROW, WIDE]);
    const narrow = OF_THE_LIST.filter((rule) => rule.selector === '.listed[data-invite="over"] > .underFirst');
    expect(narrow.map((rule) => [rule.under, rule.sets.get("display")])).toEqual([
      [null, "none"],
      ["@container (max-width: 36rem)", "flow-root"],
    ]);
    // Where a result is narrow it is not drawn, and what is not drawn is not read out.
    expect(always(".compares").get("display")).toBe("none");
    expect(wide(`${REFINES} > .compares`).get("display")).toBe("flow-root");
    // Two columns: what opens the fold, as wide as its words, and what stands beside it.
    // Where a result is narrow the fold has the line from edge to edge, as it had.
    expect(always(REFINES).get("grid-template-columns")).toBe("auto minmax(0, 1fr)");
    expect(RULES.filter((rule) => rule.under === NARROW).map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [`${REFINES} > .fold`, [["grid-column", "1 / -1"]]],
    ]);
    expect([wide(`${REFINES} > .fold`).get("display")]).toEqual(["contents"]);
    // Nothing is placed by column or by row but by the width of the part: on a screen of
    // any width the page itself is laid out as it was.
    const placed = ALWAYS.filter((rule) => /\.(refine|fold|compares)\b/.test(rule.selector) && ["grid-column", "grid-row"].some((set) => rule.sets.has(set)));
    expect(placed.map((rule) => rule.selector)).toEqual([]);
    const opens = wide(`${REFINES} > .fold > [aria-expanded][aria-controls]`);
    expect([opens.get("grid-column"), opens.get("grid-row"), opens.get("justify-self")]).toEqual(["1", "1", "start"]);
    const beside = wide(`${REFINES} > .compares`);
    expect([beside.get("grid-column"), beside.get("grid-row")]).toEqual(["2", "1"]);
    // Both stand from the top of the line: what opens the fold is brought to the top of the
    // window as it is pressed, and what stands beside it is then in sight from its top too.
    expect([opens.get("align-self"), beside.get("align-self")]).toEqual(["start", "start"]);
    // What the fold opens stands under both, from edge to edge. Seen in a browser: in a
    // column of its own it took the width, and what stood beside the fold was 30 px wide
    // and 1,359 high.
    const opened = wide(`${REFINES} > .fold > [id]`);
    expect([opened.get("grid-column"), opened.get("grid-row")]).toEqual(["1 / -1", "2"]);
    // It is read on cream within an edge of ink, which ends where the edge of a card ends.
    expect([always(".compares").get("background"), always(".compares").get("border"), always(".compares").get("margin-inline-end")]).toEqual([
      "var(--page)",
      "var(--edge) solid var(--border)",
      "calc(var(--px) * 2)",
    ]);
    // No part of the page is drawn out of the order of the page for it.
    expect(RULES.filter((rule) => rule.under === WIDE && rule.sets.has("order"))).toEqual([]);
  });

  test("test_nothing_over_the_answer_gives_way_for_a_question_since_none_is_asked_and_one_line_of_the_look_has_it_give_way_always", async () => {
    // What stood over the answer gave way while Burro asked which place was meant: his
    // question was 304 px high there. He asks nothing now, so it gives way only where the
    // look has it give way whatever the search.
    const { user, unmount } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    expect(page()).toHaveAttribute("data-closer", "false");
    await search(user, "Leafy, renting, 30 minutes to Pellam");

    expect([GIVES_WAY, OVER_THE_ANSWER_GIVES_WAY]).toEqual([["asked", "always"], "asked"]);
    expect(page()).toHaveAttribute("data-closer", "false");
    expect(theLine()).toHaveAttribute("data-frame", "box");
    expect(theInvitation()?.textContent).toBe(COMPARE.invite);
    expect(within(theResults()).getByText(COMPARE.invite).closest("[data-invite]")).toHaveAttribute("data-invite", "over");
    unmount();

    const always = userEvent.setup({ delay: null });
    render(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} client={firstSearch().client} gives="always" />
      </Shell>,
    );
    await arrived();
    expect(page()).toHaveAttribute("data-closer", "false");
    await search(always);

    expect(page()).toHaveAttribute("data-closer", "true");
    expect(theLine()).toHaveAttribute("data-frame", "none");
    expect(theInvitation()).toBeNull();
    // The list says that areas can be compared, under its first result, however wide a result is.
    const said = within(theResults()).getByText(COMPARE.invite);
    expect(said.closest("[data-invite]")).toHaveAttribute("data-invite", "under");
    expect(comesBefore(results()[0] as HTMLElement, said)).toBe(true);
  });

  test("test_where_it_gives_way_the_parts_of_an_open_search_stand_closer_on_a_screen_that_is_wider_than_a_narrow_one_too", () => {
    const CLOSER = '.search[data-closer="true"]';
    const WIDER = "@media (min-width: 40rem)";
    const NARROW = "@media (max-width: 40rem)";
    const OPEN = '.search[data-open="true"]';
    const gapOf = (under: string, selector: string) =>
      RULES.filter((rule) => rule.under === under && rule.selector === selector).map((rule) => rule.sets.get("gap"));

    // Between the box, what Burro asks and what follows: 8 px of grass. In the box, between
    // what Burro says of the search, his question and what he understood: 4 px of cream.
    expect([gapOf(WIDER, `${CLOSER} .columns`), gapOf(WIDER, `${CLOSER} .form`), gapOf(WIDER, `${CLOSER} .says`)]).toEqual([
      ["var(--space-2)"],
      ["var(--space-2)"],
      ["var(--space-1)"],
    ]);
    // Which is what parts them on a narrow screen, whatever the search.
    expect([gapOf(NARROW, `${OPEN} .columns`), gapOf(NARROW, `${OPEN} .form`), gapOf(NARROW, `${OPEN} .says`)]).toEqual([
      ["var(--space-2)"],
      ["var(--space-2)"],
      ["var(--space-1)"],
    ]);
    // Of the page as it always is, nothing is said: it stands as it stood.
    expect(ALWAYS.filter((rule) => /data-closer/.test(rule.selector))).toEqual([]);
    // From 60rem the rows of the page are parted by what is set on the part above.
    const wide = RULES.filter((rule) => rule.under === "@media (min-width: 60rem)" && rule.selector.startsWith(CLOSER));
    expect(wide.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [`${CLOSER} :is(.form, .refine)`, [["margin-block-end", "var(--space-2)"]]],
    ]);
    // Each outweighs what it takes the place of, whichever sheet is read last.
    expect(heavier(weightOf(`${CLOSER} .says`), weightOf(".says"))).toBe(true);
    expect(heavier(weightOf(`${CLOSER} :is(.form, .refine)`), weightOf(".refine"))).toBe(true);
    // No two boxes touch: the least of them is as far as the shadow of the look falls, and more.
    const pixels = (token: string) => Number.parseInt(asWritten()[token] ?? "", 10);
    expect(pixels("--space-2")).toBeGreaterThan(2 * pixels("--px"));
    // Nothing else is keyed on it: no size of type, no colour, and nothing that is hidden.
    const keyed = RULES.filter((rule) => /data-closer/.test(rule.selector)).flatMap((rule) => [...rule.sets.keys()]);
    expect([...new Set(keyed)].sort()).toEqual(["gap", "margin-block-end"]);
  });

  test("test_one_line_has_it_give_way_whatever_the_search_and_another_puts_a_slip_back_over_the_list", async () => {
    const user = userEvent.setup({ delay: null });
    const always = render(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} client={firstSearch().client} gives="always" />
      </Shell>,
    );
    await arrived();
    // Before a search there is no answer for anything to give way to.
    expect(page()).toHaveAttribute("data-closer", "false");
    await search(user);
    expect(page()).toHaveAttribute("data-closer", "true");
    expect(theLine()).toHaveAttribute("data-frame", "none");
    expect(theInvitation()).toBeNull();
    always.unmount();

    render(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} client={firstSearch().client} over="slip" />
      </Shell>,
    );
    await arrived();
    await search(user);
    // As it was first built: one slip over the list, and nothing beside the fold. The slip said
    // two things, that areas can be compared and what a town is. The founder asked for the
    // second to go from the results: the slip says the first alone, and nothing of the
    // page says the second, over the list or in a result.
    expect(LINE_STANDS).toBe("none");
    expect(theInvitation()).toBeNull();
    const list = screen.getByRole("list", { name: RESULTS.listLabel });
    expect(list.previousElementSibling?.tagName).toBe("P");
    expect(list.previousElementSibling?.textContent).toBe(COMPARE.invite);
    expect(list.previousElementSibling?.previousElementSibling ?? null).toBeNull();
    expect(screen.queryByText(TOWNS.line)).toBeNull();
    expect([TOWNS.line, TOWNS.short].filter((said) => thePage().textContent?.includes(said))).toEqual([]);
  });

  test("test_the_page_has_no_accessibility_fault_with_the_invitation_beside_the_fold_or_where_burro_asks", async () => {
    const plain = await openSearch();
    await search(plain.user);
    expect(await faultsIn(plain.container, { wholePage: true })).toEqual([]);
    await plain.user.click(whatRefines() as HTMLElement);
    expect(await faultsIn(plain.container, { wholePage: true })).toEqual([]);
    plain.unmount();

    const which = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(which.user, "Leafy, renting, 30 minutes to Pellam");
    expect(await faultsIn(which.container, { wholePage: true })).toEqual([]);
  });
});

/**
 * True where the page says these words to whoever hears it, and says them once: in a line
 * of their own, or in a notice that says of itself what changes in it.
 */
const isHeardOnce = (words: string) =>
  screen.getAllByRole("status").filter((line) => line.textContent?.includes(words)).length === 1 &&
  (document.body.textContent?.split(words).length ?? 0) === 2;

describe("what is said of words that were not read", () => {
  /** Everything the page says of itself as it changes, each as it is heard. */
  const said = () => screen.getAllByRole("status").map((line) => line.textContent ?? "");

  test("test_where_nothing_was_read_the_page_does_not_say_that_some_of_the_words_were_not", async () => {
    // Seen in a browser by three people: "Nothing in that could be read." stood over "Some
    // of your words were not read." Nothing and some cannot both be so.
    const nothing = recordedAnswer("interpret", "interpret-nothing-read").body.data;
    expect(nothing.unread.length).toBeGreaterThan(0);
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-nothing-read"));

    await search(user, sentenceOf("interpret-nothing-read"));

    expect(said()).toContain(NOTICE.nothingRead);
    expect(screen.queryByText(SUGGEST.unread)).toBeNull();
    // What would be shown in the box is all that the box holds: nothing offers to show it.
    expect(screen.queryByRole("button", { name: SUGGEST.showUnread })).toBeNull();
    expect(document.body.textContent?.includes(NOTICE.partUnread)).toBe(false);
  });

  test("test_nor_where_the_api_says_in_its_own_words_that_the_sentence_is_about_something_else", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-off-topic"));

    await search(user, sentenceOf("interpret-off-topic"));

    expect(said()).toContain(recordedAnswer("interpret", "interpret-off-topic").body.data.notice_text);
    expect(screen.queryByText(SUGGEST.unread)).toBeNull();
    expect(screen.queryByRole("button", { name: SUGGEST.showUnread })).toBeNull();
  });

  /** The one line that names what Burro left out of the search, and what it opens to. */
  const leftOut = () => screen.getByRole("status", { name: LEFT_OUT.title });
  const theLineOf = (notice: HTMLElement) => notice.querySelector("summary") as HTMLElement;
  const whyOf = (notice: HTMLElement) => within(notice).getAllByRole("listitem").map((item) => item.textContent);

  test("test_where_something_was_taken_and_a_stretch_was_not_read_one_line_says_so_and_opens_to_the_way_to_see_it", async () => {
    // What Burro could not read is said as it was, in a line: that is no question.
    const { user } = await openSearch(
      firstSearch()
        .on("interpret", noisyAtHome)
        .on("rank", "rank-suggestion-chosen")
        .on("explain_top", "explanations-suggestion-chosen"),
    );

    await search(user, sentenceOf("interpret-suggest"));

    // The ranking leaves the stretch out, and the line says so beside the box, over what
    // was understood: under the chips it was once missed. Before it the line names pubs,
    // of which the words give neither more nor fewer.
    expect(theLineOf(leftOut()).textContent).toBe(`${LEFT_OUT.title}: Pubs and bars; ${LEFT_OUT.words}`);
    expect((leftOut().querySelector("details") as HTMLDetailsElement).open).toBe(false);
    expect(comesBefore(promptBox(), leftOut())).toBe(true);
    expect(comesBefore(leftOut(), chips() as HTMLElement)).toBe(true);
    expect(said()).not.toContain(NOTICE.nothingRead);
    expect(results().length).toBeGreaterThan(0);

    // Opened, it says what follows for the ranking, and holds the way to see the words.
    await user.click(theLineOf(leftOut()));
    expect(whyOf(leftOut())[0]).toBe(`Pubs and bars. ${LEFT_OUT.why.two_ways}`);
    expect(whyOf(leftOut())[1]?.startsWith(`${LEFT_OUT.words}. ${NOTICE.partUnread}`)).toBe(true);
    await user.click(within(leftOut()).getByRole("button", { name: SUGGEST.showUnread }));
    expect(promptBox().selectionEnd).toBeGreaterThan(promptBox().selectionStart);
    expect(isHeardOnce(NOTICE.partShown(1, 1))).toBe(true);
  });

  test("test_the_line_is_closed_at_every_new_search_and_start_again_closes_it", async () => {
    // Seen in a browser: opened once, it stood open in every search after it until the page
    // was loaded anew, and put the first result 180 px lower on a phone.
    const suggesting = () =>
      firstSearch()
        .on("interpret", "interpret-suggest-who-is-counted")
        .on("rank", "rank-suggestion-chosen")
        .on("explain_top", "explanations-suggestion-chosen");
    const opens = () => leftOut().querySelector("details") as HTMLDetailsElement;
    const { user } = await openSearch(suggesting());
    await search(user, sentenceOf("interpret-suggest-who-is-counted"));
    await user.click(theLineOf(leftOut()));
    expect(opens().open).toBe(true);

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    await settled();
    expect(screen.queryByRole("status", { name: LEFT_OUT.title })).toBeNull();
    await search(user, sentenceOf("interpret-suggest-who-is-counted"));

    expect(opens().open).toBe(false);

    // A sentence that is added to the search is a new search too: what it left out is its own.
    await user.click(theLineOf(leftOut()));
    expect(opens().open).toBe(true);
    await user.click(promptBox());
    await user.keyboard(" and more of the same");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(opens().open).toBe(false);
  });

  test("test_the_line_stays_as_a_person_left_it_while_the_search_it_is_of_is_refined", async () => {
    const { user } = await openSearch(
      firstSearch()
        .on("interpret", "interpret-suggest-who-is-counted")
        .on("rank", "rank-suggestion-chosen")
        .on("explain_top", "explanations-suggestion-chosen"),
    );
    await search(user, sentenceOf("interpret-suggest-who-is-counted"));
    await user.click(theLineOf(leftOut()));

    // A chip is taken off: the search is ranked again, and is the search it was.
    await user.click(screen.getAllByRole("button", { name: /^Remove: / })[0] as HTMLElement);
    await settled();

    expect((leftOut().querySelector("details") as HTMLDetailsElement).open).toBe(true);
  });

  test("test_what_counts_recorded_crime_is_not_taken_and_the_line_names_it_with_the_one_account_of_when_it_counts", async () => {
    const long = recordedAnswer("interpret", "interpret-rules-at-once");
    const { user } = await openSearch(
      firstSearch()
        .inTurn("interpret", "interpret-rules-at-once", "interpret-by-model-long")
        .on("rank", "rank-one-press")
        .on("explain_top", "explanations-one-press"),
    );

    await search(user, (long.request.body as { text: string }).text);

    // A vibe that counts recorded crime is not taken: recorded crime counts only where a
    // person asks for it by name. The line names it first, as it was noticed first, and
    // opens to the one account the page gives of when recorded crime counts.
    expect(theLineOf(leftOut()).textContent?.startsWith(`${LEFT_OUT.title}: Gritty; `)).toBe(true);
    expect(whyOf(leftOut())[0]).toBe(`Gritty. ${REJECTED.crime_needs_explicit_request}`);
    // After it stand the readings of words that were taken another way: a word counts
    // once. One of them waits for the person, and says that of itself.
    expect(theLineOf(leftOut()).textContent).toBe(
      `${LEFT_OUT.title}: Gritty; What homes sell for; Homes in the higher council tax bands; Age of buildings; Nearer a town centre`,
    );
    expect(whyOf(leftOut()).slice(1)).toEqual([
      `What homes sell for. ${LEFT_OUT.why.otherwise}`,
      `Homes in the higher council tax bands. ${LEFT_OUT.why.by_choice}`,
      `Age of buildings. ${LEFT_OUT.why.otherwise}`,
      `Nearer a town centre. ${LEFT_OUT.why.otherwise}`,
    ]);
    expect(whyOf(leftOut()).filter((why) => why?.includes(REJECTED.crime_needs_explicit_request))).toHaveLength(1);
    expect(within(leftOut()).queryAllByRole("button")).toEqual([]);
    expect(within(leftOut()).queryAllByRole("link")).toEqual([]);
    // It is no chip of what Burro understood, and no edit that was turned away.
    expect(within(chips() as HTMLElement).queryByRole("button", { name: /Gritty/ })).toBeNull();
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
  });

  test("test_what_counts_who_lived_somewhere_is_not_taken_and_the_line_names_it_and_says_where_it_is_added", async () => {
    // Of who lives somewhere Burro counts two things, and only where a person chooses
    // them: a word in a sentence is no such choice. What stands beside it is taken, each
    // the way the words give.
    const counted = recordedAnswer("interpret", "interpret-suggest-who-is-counted");
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-suggest-who-is-counted"));

    await search(user, (counted.request.body as { text: string }).text);

    expect(counted.body.data.suggestions.map((one) => one.label)).toEqual(["Young professionals", "Going out", "Nearer a station"]);
    expect(api.callsTo("rank")).toHaveLength(1);
    const sent = api.lastCallTo("rank").body as { operations: { tag_ops: { tag_id: string }[]; weight_ops: { feature_id: string }[] } };
    expect(sent.operations.tag_ops.map((edit) => edit.tag_id)).toEqual(["pace"]);
    expect(sent.operations.weight_ops.map((edit) => edit.feature_id)).toEqual(["station_walk"]);
    expect(theLineOf(leftOut()).textContent).toBe(`${LEFT_OUT.title}: Young professionals`);
    expect(whyOf(leftOut())).toEqual([`Young professionals. ${LEFT_OUT.why.residents}`]);
    expect(thePage().querySelectorAll("[data-way], [data-guess]")).toHaveLength(0);
    expect(results().length).toBeGreaterThan(0);
  });

  test("test_where_every_thing_that_was_noticed_waits_for_the_person_nothing_is_ranked_and_the_line_stands_open_with_each", async () => {
    // "My sister wants pubs, a station, a high street": each may be the sister's wish, and
    // none is said to be the person's own. The service says that each waits, and Burro
    // takes none on a guess.
    const many = recordedAnswer("interpret", "interpret-suggest-many");
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-suggest-many"));

    await search(user, (many.request.body as { text: string }).text);

    expect(many.body.data.suggestions.every((offer) => offer.only_by_choice)).toBe(true);
    expect(api.callsTo("rank")).toEqual([]);
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect((leftOut().querySelector("details") as HTMLDetailsElement).open).toBe(true);
    expect(theLineOf(leftOut()).textContent).toBe(
      `${LEFT_OUT.title}: ${many.body.data.suggestions.map((offer) => offer.label).join("; ")}`,
    );
    expect(whyOf(leftOut())).toEqual(many.body.data.suggestions.map((offer) => `${offer.label}. ${LEFT_OUT.why.not_said}`));
    expect(thePage().querySelectorAll("[data-way], [data-guess]")).toHaveLength(0);
  });

  test("test_where_the_words_give_no_way_of_one_thing_and_the_other_waits_nothing_is_ranked_and_the_line_says_why_of_each", async () => {
    // "Pubs are so noisy", as the founder typed it.
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-suggest"));

    await search(user, sentenceOf("interpret-suggest"));

    expect(api.callsTo("rank")).toEqual([]);
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect((leftOut().querySelector("details") as HTMLDetailsElement).open).toBe(true);
    expect(theLineOf(leftOut()).textContent).toBe(`${LEFT_OUT.title}: Pubs and bars; Less transport noise`);
    expect(whyOf(leftOut())).toEqual([
      `Pubs and bars. ${LEFT_OUT.why.two_ways}`,
      `Less transport noise. ${LEFT_OUT.why.not_said}`,
    ]);
  });

  test("test_a_place_burro_does_not_know_is_said_in_a_line_and_the_rest_of_the_sentence_is_ranked", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-clarify-no-options"));

    await search(user, sentenceOf("interpret-clarify-no-options"));

    expect(theLineOf(leftOut()).textContent).toBe(`${LEFT_OUT.title}: ${LEFT_OUT.named_by_the_page.commute}`);
    expect(whyOf(leftOut())).toEqual([`${LEFT_OUT.named_by_the_page.commute}. ${LEFT_OUT.why.place}`]);
    // It is said once, and the answer stands under one line of it.
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
    expect((leftOut().querySelector("details") as HTMLDetailsElement).open).toBe(false);
    expect(thePage().querySelectorAll("[role='combobox']")).toHaveLength(0);
    expect(results().length).toBeGreaterThan(0);
  });

  test("test_what_the_service_gave_no_way_to_take_is_said_in_the_services_own_words_and_stands_open_where_nothing_is_ranked", async () => {
    const least = recordedAnswer("interpret", "interpret-by-model-least");
    const [offer] = least.body.data.suggestions;
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-by-model-least"));

    await search(user, (least.request.body as { text: string }).text);

    // Nothing is ranked, so no answer waits under the line: it stands open, and why is read.
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect((leftOut().querySelector("details") as HTMLDetailsElement).open).toBe(true);
    expect(theLineOf(leftOut()).textContent).toBe(`${LEFT_OUT.title}: ${offer?.label}`);
    expect(whyOf(leftOut())).toEqual([`${offer?.label}. ${offer?.does} ${offer?.follows}`]);
    expect(said()).not.toContain(NOTICE.nothingRead);
    expect(screen.queryByRole("button", { name: /^Skip/ })).toBeNull();
  });

  test("test_while_a_model_reads_the_rest_of_the_words_the_page_says_so_under_the_answer_of_what_the_rules_read", async () => {
    const long = recordedAnswer("interpret", "interpret-rules-at-once");
    const api = firstSearch().on("rank", "rank-one-press").on("explain_top", "explanations-one-press");
    const model = api.gate("interpret-by-model-long");
    api.inTurn("interpret", "interpret-rules-at-once", model.answers);
    const { user } = await openSearch(api);

    await search(user, (long.request.body as { text: string }).text);

    expect(results().length).toBeGreaterThan(0);
    expect(said()).toContain(SUGGEST.reading);

    model.release();
    await settled();

    expect(said()).not.toContain(SUGGEST.reading);
    expect(results().length).toBeGreaterThan(0);
  });
});

describe("the first screen, in a window that is wide and not high", () => {
  // Measured at 1280 by 720, before a search: the helpers stood at the very foot of the
  // first screen and under it. What stands over them gives way.
  const SHORT = "@media (min-width: 60rem) and (max-height: 47.99rem)";
  const low = RULES.filter((rule) => /max-height/.test(rule.under ?? ""));
  const setsOf = (under: string, selector: string) => [
    ...(low.find((rule) => rule.under === under && rule.selector === selector)?.sets ?? []),
  ];
  const BEFORE = '.search[data-open="false"]';
  const pixels = (token: string) => Number.parseInt(asWritten()[token] ?? "", 10);

  test("test_the_room_between_two_boxes_gives_way_first_and_the_grass_still_shows_between_them", () => {
    // Between the box and the helpers under it.
    expect(setsOf(SHORT, `${BEFORE} .panel`)).toEqual([["gap", "var(--space-2)"]]);
    // Between the heading and the two ways in: the rows of the page are parted by nothing,
    // so it is set on the heading.
    expect(setsOf(SHORT, `${BEFORE} .head`)).toContainEqual(["margin-block-end", "var(--space-2)"]);
    // What parts the columns is left as it is: nothing is made wider or narrower.
    expect(low.flatMap((rule) => [...rule.sets.keys()]).filter((property) => /^(gap|column-gap)$/.test(property))).toEqual(["gap"]);
    expect(low.filter((rule) => rule.sets.has("gap")).map((rule) => rule.selector)).toEqual([`${BEFORE} .panel`]);
    // No two boxes touch: the least of them is as far as the shadow of the look falls, and more.
    expect(pixels("--space-2")).toBeGreaterThan(2 * pixels("--px"));
  });

  test("test_the_drawing_beside_the_heading_is_drawn_as_on_a_phone_and_the_heading_keeps_its_size", () => {
    // The size of a drawing beside words is the last thing of the look to give way. Burro
    // is drawn at two pixels of the screen to one of his drawing, and sits on the line the
    // heading stands on, as he did.
    expect(setsOf(SHORT, `${BEFORE} .head > [data-pose]`)).toEqual([["--px", "var(--px-small)"]]);
    expect(setsOf(SHORT, `${BEFORE} .head`)).toEqual([
      ["row-gap", "var(--space-1)"],
      ["margin-block-end", "var(--space-2)"],
      ["padding-block", "var(--space-2)"],
    ]);
    // The heading is what it was, at the size it was: no rule here names it, or the face of anything.
    expect(low.filter((rule) => /\.(title|lead)\b/.test(rule.selector))).toEqual([]);
    expect(low.flatMap((rule) => [...rule.sets.keys()]).filter((property) => /^font/.test(property))).toEqual([]);
  });

  test("test_nothing_gives_way_once_a_search_is_open_nor_in_a_window_that_is_high_nor_on_a_narrow_screen", () => {
    // Every rule of it is of the page before a search: once one is open the heading is gone,
    // and the parts of the page stand as the answer needs them to.
    expect(low.length).toBeGreaterThan(0);
    expect(low.filter((rule) => !rule.selector.startsWith(BEFORE)).map((rule) => rule.selector)).toEqual([]);
    // It is said of a window under 768 px high and from 60rem wide, and of no other.
    expect([...new Set(low.map((rule) => rule.under))]).toEqual([SHORT]);
    // Each outweighs what it takes the place of, whichever sheet is read last.
    expect(weightOf(`${BEFORE} .head`)[1]).toBeGreaterThan(weightOf(".roomy")[1]);
    expect(weightOf(`${BEFORE} .panel`)[1]).toBeGreaterThan(weightOf(".panel")[1]);
  });

  test("test_the_page_says_whether_a_search_is_open_so_that_the_sheet_can_tell", async () => {
    const { user } = await openSearch();
    const page = () => document.querySelector("main > [data-dressed]") as HTMLElement;

    expect(page()).toHaveAttribute("data-open", "false");
    expect(page().querySelector(":scope > [data-kind] > [data-pose]")).toHaveAttribute("data-pose", "sits");

    await search(user);
    expect(page()).toHaveAttribute("data-open", "true");
  });
});

describe("the one button that is cobalt", () => {
  /** Every button of the page that is drawn filled and is in sight, by what it says. */
  const filled = () =>
    [...document.querySelectorAll("main button, main a")]
      .filter((button) => button.querySelector(":scope > [data-kind='go']") !== null)
      .filter((button) => button.closest("[hidden]") === null)
      .map((button) => button.textContent);

  test("test_before_a_search_it_is_search_in_the_first_way_in", async () => {
    await openSearch();

    expect(filled()).toEqual([PROMPT.submit]);
  });

  test("test_in_the_second_way_in_it_is_the_button_that_ranks_the_settings_for_search_is_not_in_sight", async () => {
    // The settings stand open there, and the button that ranks by them is the one that
    // matters most in sight. It stands under the settings, as Search stands by the box.
    const { user } = await openSearch();
    await way(user, "deep");
    const ranks = within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank });

    expect(filled()).toEqual([SETTINGS.rank]);
    expect(theSettings()).not.toContainElement(ranks);
    expect(theSettings().compareDocumentPosition(ranks) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(panelOf("deep")).getAllByRole("button", { name: SETTINGS.rank })).toHaveLength(1);

    await way(user, "quick");
    expect(filled()).toEqual([PROMPT.submit]);
  });

  test("test_after_a_sentence_that_is_no_plain_list_it_is_search_for_nothing_else_is_offered_to_be_pressed", async () => {
    // While Burro asked, the one press that added what he noticed was the cobalt one, and
    // Search was drawn plain. Nothing is offered now, and Search is the one it was.
    const { user } = await openSearch(
      firstSearch().on("interpret", "interpret-suggest-many").on("rank", "rank-first").on("explain_top", "explanations-first"),
    );
    await send(user, "somewhere I might like, I think");
    await settled();
    await settingsAt(user);

    expect(filled()).toEqual([PROMPT.submit]);
    expect(screen.getByRole("button", { name: PROMPT.submit }).firstElementChild).toHaveAttribute("data-kind", "go");
    expect(screen.queryByRole("button", { name: /^Add (all|the) \d+/ })).toBeNull();
  });

  test("test_where_a_name_is_borne_by_several_places_it_is_search", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");

    expect(filled()).toEqual([PROMPT.submit]);
  });
});

describe("the wait, while a sentence is read", () => {
  test("test_while_a_first_sentence_is_read_burro_hops_where_the_results_will_stand", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);

    await send(user, "leafy and quiet");

    expect(theResults()).toContainElement(theWait() as HTMLElement);
    expect(theWait()?.querySelector("[data-pose]")).toHaveAttribute("data-pose", "hops");
    expect(theWait()?.querySelector("[data-pose]")).toHaveAttribute("data-stage", "true");
    expect(burros()).toHaveLength(1);
    // The words under him are the words the line under the box says.
    expect(theWait()?.textContent).toBe(STATUS.reading);
    expect(status()).toEqual([STATUS.reading]);
    // Everything else of that moment is as it was.
    expect(screen.getByRole("button", { name: PROMPT.reading })).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByRole("button", { name: PROMPT.stop })).toBeInTheDocument();
    expect(promptBox()).toHaveValue("leafy and quiet");

    reading.release();
    await settled();
  });

  test("test_he_takes_the_place_of_the_grey_bars_and_cards_and_nothing_holds_the_place_of_what_is_not_yet_understood", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);

    await send(user, "leafy and quiet");

    expect(document.querySelectorAll(".skeleton")).toHaveLength(0);
    expect(chips()).toBeNull();
    expect(screen.queryAllByRole("list", { name: new RegExp(`^${RESULTS.listLabel}`) })).toEqual([]);
    // That the answer is on its way is said of where it will stand, as it was.
    expect(theResults().querySelectorAll("[aria-busy='true']")).toHaveLength(1);

    reading.release();
    await settled();
  });

  test("test_when_the_answer_is_in_the_results_stand_where_he_was", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);
    await send(user, "leafy and quiet");
    const where = theWait()?.parentElement;

    reading.release();
    await settled();

    expect(theWait()).toBeNull();
    expect(burros()).toHaveLength(0);
    expect(where).toBe(theResults());
    expect(theResults()).toContainElement(results()[0] as HTMLElement);
    expect(chips()).not.toBeNull();
  });

  test("test_he_hops_until_the_ranking_is_in_and_not_only_until_the_words_are_read", async () => {
    // The words are read, and what was understood is drawn. The ranking of it is still on
    // its way: the page still calls that reading, and the button still says so.
    const api = firstSearch();
    const ranking = api.hold("rank", "rank-first");
    const { user } = await openSearch(api);

    await send(user, "leafy and quiet");
    await screen.findByRole("region", { name: CHIPS.label });

    expect(ranking.waiting()).toBe(1);
    expect(theWait()).not.toBeNull();
    expect(screen.getByRole("button", { name: PROMPT.reading })).toBeInTheDocument();

    ranking.release();
    await settled();
    expect(theWait()).toBeNull();
  });

  test("test_a_sentence_sent_with_results_on_the_page_has_him_hop_in_the_place_of_the_first_and_the_rest_stay", async () => {
    const { user, api } = await openSearch();
    await search(user);
    const before = { rest: restOfTheList(), second: results()[1], chips: chips() };
    api.on("rank", "rank-second-sentence").on("explain_top", "explanations-second-sentence");
    const reading = api.hold("interpret", "interpret-second-sentence");

    await send(user, ", a bit more green space");

    expect(theResults()).toContainElement(theWait() as HTMLElement);
    // The first result gives way to him. It is kept, and is not drawn.
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    expect(theResults().querySelector("ol")?.closest("[hidden]")).not.toBeNull();
    // What was understood and the rest of the list stay where they are, as they are.
    expect(chips()).toBe(before.chips);
    expect(restOfTheList()).toBe(before.rest);
    expect(results()[0]).toBe(before.second);
    expect(document.querySelectorAll(".skeleton")).toHaveLength(0);

    reading.release();
    await settled();

    expect(theWait()).toBeNull();
    expect(screen.getByRole("list", { name: RESULTS.listLabel })).toBeVisible();
    expect(results().length).toBeGreaterThan(1);
  });

  test("test_what_was_opened_in_the_first_result_is_open_still_when_a_sentence_leaves_it_first", async () => {
    // He takes its place and it is kept, with whatever of it was opened. Drawn anew, its
    // working would be closed under the person who had opened it.
    const { user, api } = await openSearch();
    await search(user);
    const first = results()[0] as HTMLElement;
    const area = first.querySelector("h3 a")?.textContent ?? "";
    await workingOf(user, area);
    expect(screen.getByRole("button", { name: RESULTS.workingOf(area) })).toHaveAttribute("aria-expanded", "true");
    // The sentence is read, and the ranking that follows has the same area first.
    api.on("interpret", "interpret-second-sentence").on("rank", "rank-first");

    await send(user, ", a bit more green space");
    await settled();

    expect(results()[0]).toBe(first);
    expect(screen.getByRole("button", { name: RESULTS.workingOf(area) })).toHaveAttribute("aria-expanded", "true");
  });

  test("test_he_does_not_hop_while_a_ranking_is_worked_out_again_and_the_list_stays_where_it_is", async () => {
    const { user, api } = await openSearch();
    await search(user);
    const before = results();
    api.on("explain_top", "explanations-refined");
    const ranking = api.hold("rank", "rank-refined");

    await removeChip(user, "Leafy");

    expect(ranking.waiting()).toBe(1);
    expect(theWait()).toBeNull();
    expect(burros()).toHaveLength(0);
    expect(results()).toEqual(before);
    expect(screen.getByText(RESULTS.working)).toBeVisible();
    expect(screen.getByRole("list", { name: RESULTS.listLabel })).toHaveAttribute("aria-busy", "true");

    ranking.release();
    await settled();
  });

  test("test_a_first_ranking_that_a_word_of_the_shelf_asks_for_has_him_hop_where_the_results_will_stand", async () => {
    // A person waits there for a first answer as they do after a sentence. Seen in a
    // browser: the wait was drawn as dashes, under the card of the word, out of sight, and
    // the search opened only when the answer was in. Nothing is read, so neither he nor the
    // line under the box says that a search is: both say that the ranking is worked out.
    const api = firstSearch().on("explain_top", "explanations-shelf");
    const ranking = api.hold("rank", "rank-shelf");
    const { user } = await openSearch(api);
    await helper(user, "word");
    // The first word of the shelf, whichever the API gives.
    await user.click(within(screen.getByRole("region", { name: SHELF.title })).getAllByRole("button")[0] as HTMLElement);

    await user.click(screen.getByRole("button", { name: SHELF.add }));

    expect(ranking.waiting()).toBe(1);
    expect(theResults()).toContainElement(theWait() as HTMLElement);
    expect(theWait()?.querySelector("[data-pose]")).toHaveAttribute("data-pose", "hops");
    expect(theWait()?.querySelector("[data-pose]")).toHaveAttribute("data-stage", "true");
    expect(burros()).toHaveLength(1);
    expect(theWait()?.textContent).toBe(WAIT.ranking);
    expect(status()).toEqual([WAIT.ranking]);
    expect(status()).not.toContain(STATUS.reading);
    // No grey bar and no grey card holds the place of a result.
    expect(document.querySelectorAll(".skeleton")).toHaveLength(0);
    expect(screen.queryAllByRole("list", { name: new RegExp(`^${RESULTS.listLabel}`) })).toEqual([]);
    // The search is open from the press, as it is from the press that sends a sentence: the
    // shelf has gone with the word that was pressed, and what the search holds has the focus.
    expect(document.querySelector("main > [data-dressed]")).toHaveAttribute("data-search", "open");
    expect(screen.queryByRole("group", { name: HELPERS.label })).toBeNull();
    expect(chips()).toHaveFocus();
    // Nothing is read, so nothing can be stopped: the box is as it is once a search is open.
    expect(screen.getByRole("button", { name: PROMPT.submit })).not.toHaveAttribute("aria-disabled");
    expect(screen.queryByRole("button", { name: PROMPT.stop })).toBeNull();

    ranking.release();
    await settled();
    expect(theWait()).toBeNull();
    expect(burros()).toHaveLength(0);
    expect(results().length).toBeGreaterThan(0);
    expect(status()).not.toContain(WAIT.ranking);
  });

  test("test_the_settings_ranked_as_they_stand_have_him_hop_too", async () => {
    const api = standInApi().on("explain_top", "explanations-first");
    const ranking = api.hold("rank", "rank-default-rent");
    const { user } = await openSearch(api);
    await settingsAt(user);

    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));

    expect(ranking.waiting()).toBe(1);
    // The search is open from the press: the two ways in have gone, and the settings are
    // closed over where the answer will stand, with the focus on what opens them.
    expect(screen.queryByRole("tablist")).toBeNull();
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
    expect(whatRefines()).toHaveFocus();
    expect(theWait()?.querySelector("[data-pose]")).toHaveAttribute("data-pose", "hops");
    expect(theWait()?.textContent).toBe(WAIT.ranking);
    expect(status()).toEqual([WAIT.ranking]);
    // His box holds the room of a first result and no more: what the search holds is drawn over it.
    expect(theWait()).toHaveAttribute("data-room", "result");
    expect(chips()).not.toBeNull();
    expect(comesBefore(chips() as HTMLElement, theWait() as HTMLElement)).toBe(true);

    ranking.release();
    await settled();
    expect(theWait()).toBeNull();
    expect(results().length).toBeGreaterThan(0);
  });

  test("test_what_burro_took_of_a_sentence_has_him_hop_until_its_ranking_is_in_and_what_was_understood_comes_with_the_answer", async () => {
    // The sentence is read, and what Burro noticed in it is taken and sent to be ranked. The
    // search the service last returned holds none of it yet: drawn then, what he understood
    // was one chip that nobody had said, which gave way to a dozen as the ranking came.
    const api = firstSearch()
      .on("interpret", "interpret-suggest-who-is-counted")
      .on("explain_top", "explanations-suggestion-chosen");
    const ranking = api.hold("rank", "rank-suggestion-chosen");
    const { user } = await openSearch(api);

    await send(user, sentenceOf("interpret-suggest-who-is-counted"));
    await arrived();

    expect(ranking.waiting()).toBe(1);
    expect(theResults()).toContainElement(theWait() as HTMLElement);
    expect(theWait()?.querySelector("[data-pose]")).toHaveAttribute("data-pose", "hops");
    expect(burros()).toHaveLength(1);
    expect(chips()).toBeNull();
    expect(whatRefines()).toBeNull();
    expect(status()).toEqual([STATUS.reading]);
    expect(screen.queryAllByRole("article")).toEqual([]);

    ranking.release();
    await settled();

    expect(theWait()).toBeNull();
    expect(results().length).toBeGreaterThan(0);
    expect(within(chips() as HTMLElement).getAllByRole("button").length).toBeGreaterThan(1);
  });

  describe("for as long as he takes to be seen", () => {
    // The founder: "even if not needed, create a few seconds load time to allow the bunny
    // jumping into a hole animation to appear and take center stage".
    /** A browser whose look says how long a round of his hop is. A test lays no sheet, so it says so itself. */
    function aRoundOf(length: string): () => void {
      const sheet = document.createElement("style");
      sheet.textContent = `:root { ${ROUND}: ${length}; }`;
      document.head.append(sheet);
      return () => sheet.remove();
    }
    /** A round that a test can wait out: the look's own is a second. */
    const SHORT = 120;
    let taken: () => void = () => undefined;
    afterEach(() => taken());

    test("test_a_first_search_shows_him_alone_until_he_has_been_down_his_hole_and_up_again_twice_however_fast_the_service", async () => {
      taken = aRoundOf(`${SHORT}ms`);
      const { user, api } = await openSearch();
      const began = Date.now();

      await send(user, "leafy and quiet");
      await arrived();

      // The service has answered. He hops where the results will stand, and nothing of the
      // answer is on the page: not what was understood, and not a result.
      expect(api.callsTo("interpret")).toHaveLength(1);
      expect(theResults()).toContainElement(theWait() as HTMLElement);
      expect(theWait()?.querySelector("[data-pose]")).toHaveAttribute("data-pose", "hops");
      expect(burros()).toHaveLength(1);
      expect(chips()).toBeNull();
      expect(screen.queryAllByRole("article")).toEqual([]);
      expect(status()).toEqual([STATUS.reading]);
      // What he takes the place of can be stopped, as any reading can.
      expect(screen.getByRole("button", { name: PROMPT.stop })).toBeInTheDocument();

      await waitFor(() => expect(results().length).toBeGreaterThan(0));

      expect(Date.now() - began).toBeGreaterThanOrEqual(ROUNDS * SHORT);
      expect(theWait()).toBeNull();
      expect(burros()).toHaveLength(0);
      expect(chips()).not.toBeNull();
    });

    test("test_a_search_that_is_refined_with_its_results_in_sight_is_answered_as_soon_as_the_service_answers", async () => {
      const { user, api } = await openSearch();
      await search(user);
      // The look says that a round is long: a refined search that waited for it would not be in yet.
      taken = aRoundOf("60000ms");
      api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
      const before = results().map((card) => card.textContent);

      await removeChip(user, "Leafy");
      await settled();

      expect(results().map((card) => card.textContent)).not.toEqual(before);
      expect(theWait()).toBeNull();
    });

    test("test_where_less_movement_is_asked_for_nothing_is_added_to_what_the_service_took", async () => {
      // The look says a round is nought there, and he is still: there is nothing to watch.
      taken = aRoundOf("0ms");
      const { user } = await openSearch();

      await search(user);

      expect(results().length).toBeGreaterThan(0);
      expect(theWait()).toBeNull();
    });

    test("test_a_failure_is_said_at_once_and_he_is_not_watched_first", async () => {
      taken = aRoundOf("60000ms");
      const { user } = await openSearch(firstSearch().unreachable("interpret"));

      await send(user, "leafy and quiet");
      await settled();

      expect(theWait()).toBeNull();
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  test("test_a_first_ranking_that_fails_ends_the_wait_and_the_page_is_as_it_was_with_the_failure_said", async () => {
    const api = standInApi().on("rank", "error-internal");
    const { user } = await openSearch(api);
    await settingsAt(user);

    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await settled();

    expect(theWait()).toBeNull();
    expect(burros().filter((one) => one.dataset.pose === "hops")).toHaveLength(0);
    expect(status()).not.toContain(WAIT.ranking);
    // No search opened of the press: the two ways in stand as they stood, with the second
    // chosen, and Burro sits by the heading.
    expect(document.querySelector("main > [data-dressed]")).toHaveAttribute("data-search", "closed");
    expect(within(ways()).getAllByRole("tab").map((tab) => tab.getAttribute("aria-selected"))).toEqual(["false", "true"]);
    expect(burros().filter((one) => one.dataset.pose === "sits")).toHaveLength(1);
    // The failure is said where the person is: in the way they are in, over the button
    // they pressed, which is held in sight, and not in the box of the other. The button
    // is where it was, and has the focus it had.
    expect(screen.getByRole("alert")).toBeVisible();
    expect(panelOf("deep")).toContainElement(screen.getByRole("alert"));
    const pressed = within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank });
    expect(pressed).toBeVisible();
    expect(pressed).toHaveFocus();
    expect(pressed.parentElement).toContainElement(screen.getByRole("alert"));
  });

  test("test_a_failure_that_is_tried_again_from_the_second_way_in_leaves_the_focus_on_search_once_it_is_drawn", async () => {
    // "Try again" goes as it is pressed, and hands the focus to Search, which is what is
    // tried again. While the second way in is chosen Search is not drawn: it is once the
    // search opens of the press, and takes the focus then. It is never left on nothing.
    const api = standInApi().on("rank", "error-internal");
    const { user } = await openSearch(api);
    await settingsAt(user);
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await settled();
    api.on("rank", "rank-default-rent").on("explain_top", "explanations-first");

    await user.click(within(screen.getByRole("alert")).getByRole("button", { name: PROMPT.tryAgain }));
    await settled();

    expect(results().length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: PROMPT.submit })).toHaveFocus();
  });

  test("test_stop_ends_the_reading_and_he_goes_with_it", async () => {
    const { user } = await openSearch(firstSearch().silent("interpret"));
    await send(user, "leafy");
    expect(theWait()).not.toBeNull();

    await user.click(screen.getByRole("button", { name: PROMPT.stop }));

    expect(theWait()).toBeNull();
    expect(burros().filter((one) => one.dataset.pose === "hops")).toHaveLength(0);
    expect(status()).not.toContain(STATUS.reading);
  });

  test("test_words_that_could_not_be_read_end_the_wait_as_an_answer_does", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "error-internal"));
    await send(user, "leafy");

    await screen.findByRole("button", { name: PROMPT.tryAgain });

    expect(theWait()).toBeNull();
    expect(burros().filter((one) => one.dataset.pose === "hops")).toHaveLength(0);
  });

  test("test_what_stood_in_the_place_of_the_first_result_is_not_drawn_while_he_hops_and_takes_no_room", () => {
    const kept = RULES.filter((rule) => rule.selector === ".first[hidden]");

    expect(kept.map((rule) => [rule.under, rule.sets.get("display")])).toEqual([[null, "none"]]);
  });

  test("test_the_page_has_no_accessibility_fault_while_he_hops", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user, container } = await openSearch(api);
    await send(user, "leafy and quiet");

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    reading.release();
    await settled();
  });
});
