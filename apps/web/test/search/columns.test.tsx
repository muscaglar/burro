/**
 * Where the parts of the search page stand on a wide screen. From 60rem the
 * page has two columns: the answer, and the map beside it, which stays in
 * sight as the answer scrolls. No column of settings stands open, on a
 * screen of any width: before a search the settings are the second of the two
 * ways in, and once one is open they are the part that refines it.
 *
 * jsdom lays nothing out, so where a column stands is read from the style
 * sheet, and what is drawn is read from the page. Where the first result
 * stands at 1440 by 900, and how wide the map is, were measured in a browser:
 * no test measures either.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { screen } from "@testing-library/react";

import { MAP } from "@/content/map";
import { CHIPS, PROMPT, STATUS } from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { SHARE } from "@/content/share";

import { setOnline } from "../support/api";
import { faultsIn } from "../support/axe";
import { asWritten } from "../support/contrast";
import { isFor, rulesOf, type Rule } from "../support/css";
import {
  narrowAgain,
  openSearch,
  promptBox,
  results,
  search,
  settingsAt,
  setWide,
  tabOf,
  theLine,
  theSettings,
  theSettingsIfAny,
  way,
  whatRefines,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const COMPONENTS = path.resolve(__dirname, "..", "..", "src", "components");
const sheetOf = (component: string) =>
  readdirSync(path.join(COMPONENTS, component))
    .filter((name) => name.endsWith(".css"))
    .flatMap((name) => rulesOf(readFileSync(path.join(COMPONENTS, component, name), "utf8")));
const PAGE = rulesOf(readFileSync(path.join(COMPONENTS, "SearchApp", "SearchApp.module.css"), "utf8"));

/** The width from which there are two columns. A breakpoint cannot be a token, so the style sheet says it. */
const BESIDE = "@media (min-width: 60rem)";
const beside = PAGE.filter((rule) => rule.under === BESIDE);
const always = PAGE.filter((rule) => rule.under === null);
/** What the rules for a part set, of those given: a later rule sets over an earlier one. */
const setFor = (rules: readonly Rule[], part: string) =>
  new Map(rules.filter((rule) => isFor(rule.selector, part)).flatMap((rule) => [...rule.sets]));
/** The parts of the answer, in the order they stand in. */
const ANSWER = ["form", "refine", "results", "tools", "rest"];
/** The tokens, as they are written. */
const TOKENS = asWritten();
/** How wide the two columns are: one token says, and the page names it. */
const COLUMNS = TOKENS["--columns"] ?? "";
/** The two columns, each as the token writes it. */
const TRACKS = COLUMNS.match(/minmax\([^()]*\)/g) ?? [];
const px = (token: string) => Number(/^(\d+)px$/.exec(TOKENS[token] ?? "")?.[1]);
const rem = (length: string) => Number(/^([\d.]+)rem$/.exec(length)?.[1]) * 16;
/** The shares of the page the two columns take, as the token writes them. */
const SHARES = TRACKS.map((track) => Number(/^minmax\(0, (\d+)fr\)$/.exec(track)?.[1]));

const comesBefore = (one: Element, other: Element) =>
  Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);
const chips = () => screen.getByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel})$`) });
const theMap = () => screen.getByRole("region", { name: MAP.label });

/** A browser that says it is as wide as can be, whatever it is asked, and keeps what it was asked. */
const aWideBrowser = () => setWide(true);

beforeEach(() => setOnline(true));
afterEach(narrowAgain);

describe("two columns, from 60rem", () => {
  test("test_the_answer_is_in_the_first_and_the_map_in_the_second_beside_it", () => {
    const page = setFor(beside, "search");

    expect(page.get("grid-template-columns")).toBe("var(--columns)");
    expect(TRACKS).toHaveLength(2);
    for (const part of ANSWER) expect([part, setFor(beside, part).get("grid-column")]).toEqual([part, "1"]);
    expect(setFor(beside, "map").get("grid-column")).toBe("2");
    // The heading of the page and what it is for stand in one box, with Burro beside the
    // heading. The box is what the page places: it stands over the two ways in, in the
    // column of the answer, so that the map stands beside it from the head of the page.
    expect(setFor(beside, "head").get("grid-column")).toBe("1");
    for (const part of ["title", "lead"]) expect([part, setFor(beside, part).has("grid-row")]).toEqual([part, false]);
  });

  test("test_no_column_of_settings_stands_open_and_nothing_is_said_of_a_wider_screen", () => {
    // The founder, of the page after a search: "Settings should be a 'refine search'
    // collapsed section." The three columns from 80rem are gone.
    expect(PAGE.filter((rule) => isFor(rule.selector, "settings"))).toEqual([]);
    expect(PAGE.filter((rule) => /80rem|79\.99rem/.test(rule.under ?? "")).map((rule) => rule.under)).toEqual([]);
    expect(COLUMNS).not.toMatch(/rem/);
    // The page asks the browser for no width: what stands where is the style sheet's to say.
    const script = readFileSync(path.join(COMPONENTS, "SearchApp", "SearchApp.tsx"), "utf8");
    expect(script).not.toMatch(/useWide|matchMedia|innerWidth/);
  });

  test("test_the_two_columns_are_as_wide_as_one_token_says_whatever_is_drawn_in_them", () => {
    // The columns are the page's own, and are as wide as the token says: neither is as wide
    // as what stands in it, so a column with nothing in it yet is kept all the same.
    expect(TRACKS.join(" ")).toBe(COLUMNS);
    for (const track of TRACKS) expect(track).toMatch(/^minmax\(0, \d+fr\)$/);
    // No rule makes them otherwise for a state of the page: one rule sets them, for the page
    // as it always is, and one line of the tokens says what they are.
    const setters = PAGE.filter((rule) => rule.sets.has("grid-template-columns") && /columns|search/.test(rule.selector));
    expect(setters.map((rule) => [rule.under, rule.selector, rule.sets.get("grid-template-columns")])).toEqual([
      [null, ".columns", "minmax(0, 1fr)"],
      [BESIDE, ".search", "var(--columns)"],
    ]);
    const written = readFileSync(path.resolve(COMPONENTS, "..", "styles", "tokens.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    expect(written.match(/--columns\s*:/g)).toHaveLength(1);
  });

  test("test_the_map_is_twice_as_wide_as_it_was_and_the_answer_keeps_the_width_a_card_was_measured_to_read_in", () => {
    // The founder: "Map should be larger on the search result". It stood in a column of
    // 17rem, 272 px, where its window was 248 px wide and named three areas. Before the look
    // it had 440 px at 1440 wide, and named thirteen, in a smaller hand than the look's.
    // Measured in a browser at 1440 by 900, after a plain search, at seven to six: the box
    // of the map is 543 px and its window 519, it names nine areas, and the answer has
    // 633, which is the width a card was measured to read in. At eight to five the map
    // has 452 and names four. At one to one it has 588 and names twelve, and the answer
    // has 588. The first result began at 820 of 900 in all three, on the page of the two
    // ways in alone. Measured again on the whole page, with every part of it drawn, at seven
    // to six: the map is 543 px as it was, and the first result begins at 899.5 of 900, under
    // a line of two lines, five chips in five rows, the part that refines and what says
    // that areas can be compared. It is what stands over it that stands it there, and not
    // the width of a column. jsdom lays nothing out, so the widths are worked out from what
    // they depend on. Measure before changing the token.
    const shell = sheetOf("Shell").filter((rule) => rule.under === null);
    const dressed = new Map(shell.filter((rule) => rule.selector.trim() === ".main:has(> [data-dressed])").flatMap((rule) => [...rule.sets]));
    const page = setFor(beside, "search");

    // A page that is dressed is as wide as the token says, and the shell gives it no room at
    // its sides: what it keeps clear is the grass at either hand, which it adds to the width.
    expect(dressed.get("padding")).toBe("0 0 var(--space-5)");
    expect(dressed.get("max-width")).toBe("calc(var(--page-width) - 2 * var(--space-4) + 2 * var(--gutter))");
    expect(page.get("gap")).toBe("0 var(--space-5)");
    const wide = rem(TOKENS["--page-width"] ?? "");
    const shared = wide - px("--space-5");
    const [answer = 0, map = 0] = SHARES.map((share) => (shared * share) / SHARES.reduce((sum, one) => sum + one, 0));

    expect(wide).toBe(1200);
    expect(SHARES).toEqual([7, 6]);
    expect(Math.round(map)).toBe(543);
    expect(map).toBeGreaterThanOrEqual(440);
    expect(map).toBeGreaterThanOrEqual(272 * 1.99);
    // The answer is no narrower than it was between the settings and the map, where every
    // card was measured: 624 px. A result is laid out as for a desk in it, whichever way
    // the columns are chosen: in the widest of them each column has half the page.
    expect(Math.round(answer)).toBe(633);
    expect(answer).toBeGreaterThanOrEqual(624);
    expect(Math.min(answer, shared / 2)).toBeGreaterThanOrEqual(30 * 16);
    const card = sheetOf("ResultList").filter((rule) => /^@container \(max-width: 30rem\)$/.test(rule.under ?? ""));
    expect(card.some((rule) => rule.selector === ".card")).toBe(true);
    // The window of the map is as high as three parts in four of its width there, and no
    // lower than 18rem: it is the map's own sheet that says so, by the width of its own box.
    const window = sheetOf("MapView").filter((rule) => rule.under === BESIDE && rule.selector === ".view .window");
    expect(window.map((rule) => [rule.sets.get("aspect-ratio"), rule.sets.get("min-height")])).toEqual([["4 / 3", "18rem"]]);
  });

  test("test_every_part_has_its_column_and_its_row_by_name_so_that_none_is_placed_by_what_else_is_drawn", () => {
    // A part that is placed wherever there is room moves when another part comes or goes.
    const rows = ["head", ...ANSWER].map((part) => setFor(beside, part).get("grid-row"));

    expect(rows).toEqual(["1", "3", "4", "5", "6", "7"]);
    expect(setFor(beside, "map").get("grid-row")).toBe("1 / 8");
    // What says a search came from a link stands between what the page is for and the box.
    // It and the tray are another part's, held by one of the page's: each is what that holds.
    const heldBy = (part: string) =>
      new Map(
        beside
          .filter((rule) => new RegExp(`^\\.${part}\\s*>\\s*\\*$`).test(rule.selector.trim()))
          .flatMap((rule) => [...rule.sets]),
      );
    expect([heldBy("shared").get("grid-column"), heldBy("shared").get("grid-row")]).toEqual(["1", "2"]);
    // The tray is as wide as the page, under both columns.
    expect([heldBy("tray").get("grid-column"), heldBy("tray").get("grid-row")]).toEqual(["1 / -1", "8"]);
    // What holds the parts is no box of its own there, so that each is placed by the page.
    expect(setFor(beside, "columns").get("display")).toBe("contents");
  });

  test("test_no_row_of_the_answer_is_made_higher_for_the_map_beside_it", () => {
    // The map may be the taller. What is over goes to the last row of the answer, which
    // takes what is left, and never between the tabs and the way in that is chosen, or
    // between the box and the first result.
    const page = setFor(beside, "search");

    expect(page.get("grid-template-rows")).toBe("repeat(6, auto) 1fr auto");
    expect(page.get("align-items")).toBe("start");
    // A row with nothing in it holds no space before the next: what is between two parts is
    // set on the part above.
    expect(page.get("gap")).toMatch(/^0 /);
    const parted = beside.filter((rule) => rule.sets.get("margin-block-end") === "var(--space-3)").map((rule) => rule.selector);
    expect(parted).toEqual([".head", ".shared > *", ".form", ".refine", ".results", ".tools"]);
  });

  test("test_the_tabs_join_the_second_way_in_though_it_is_a_part_of_its_own", () => {
    // The second way in stands after what holds the tabs, as the part that refines a search
    // does. What parts two parts of the page is taken back between these two, at every width.
    const joined = always.filter((rule) => rule.selector === '.refine[role="tabpanel"]');

    expect(joined.map((rule) => rule.sets.get("margin-block-start"))).toEqual(["calc(-1 * var(--space-3))"]);
    expect(setFor(always, "columns").get("gap")).toBe("var(--space-3)");
    // Nothing parts the tabs from the first way in, which stands in one part with them.
    expect(setFor(always, "form").has("gap")).toBe(false);
  });

  test("test_the_map_stays_in_sight_as_the_answer_scrolls_and_scrolls_in_its_own_box", () => {
    const sets = setFor(beside, "map");

    expect([sets.get("position"), sets.get("overflow-y")]).toEqual(["sticky", "auto"]);
    expect(sets.get("max-height")).toBe("calc(100vh - 2 * var(--space-4))");
    expect(sets.has("inset-block-start")).toBe(true);
    // It does not stick to the foot of the screen: only the tray of areas to compare does.
    expect(sets.has("inset-block-end")).toBe(false);
  });

  test("test_what_takes_the_focus_in_the_map_is_not_left_under_the_tray_that_sticks", () => {
    // The page clears room for the tray, and the map, which scrolls in its own box, clears
    // the same, once an area is chosen.
    const page = rulesOf(readFileSync(path.resolve(COMPONENTS, "..", "styles", "base.css"), "utf8"))
      .filter((rule) => rule.selector.trim() === "html")
      .map((rule) => rule.sets.get("scroll-padding-bottom"))
      .filter(Boolean);
    const chosen = beside.filter((rule) => /:has\(\.tray > \[data-closed="false"\]\)/.test(rule.selector));

    expect(page).toHaveLength(1);
    expect(chosen.map((rule) => rule.selector.trim().split(/\s+/).pop())).toEqual([".map"]);
    for (const rule of chosen) {
      expect(rule.sets.get("scroll-padding-block-end")).toBe(page[0]);
      // What stands at the foot of the map can be scrolled as far up as the tray is high.
      expect(rule.sets.get("padding-block-end")).toBe(page[0]);
    }
    // The tray says whether an area is chosen, and is held by the part the rule names.
    const tray = rulesOf(readFileSync(path.join(COMPONENTS, "CompareTray", "CompareTray.module.css"), "utf8"));
    expect(tray.some((rule) => /\[data-closed="true"\]/.test(rule.selector))).toBe(true);
  });

  test("test_the_settings_are_laid_out_by_the_width_of_their_own_box_and_never_by_that_of_the_screen", () => {
    // Under their fold they are as wide as the answer, which on a phone is as wide as the
    // screen and on a desk is not. What holds them says how wide it is.
    expect(setFor(always, "fold").get("container-type")).toBe("inline-size");
    // Nothing the settings hold asks how wide the screen is. What asks a width asks its own box.
    const held = ["SettingsPanel", "WeightSlider", "NumberStepper", "PlaceCombobox", "Disclosure"].flatMap((component) =>
      sheetOf(component).map((rule) => ({ ...rule, component })),
    );
    const byTheScreen = held.filter((rule) => /@media[^{]*\b(width|height)\b/.test(rule.under ?? ""));

    expect(held.length).toBeGreaterThan(40);
    expect(byTheScreen.map((rule) => `${rule.component}: ${rule.selector} under ${rule.under}`)).toEqual([]);
  });

  test("test_under_60rem_the_page_is_one_column_in_the_order_of_the_page", () => {
    expect(setFor(always, "columns").get("grid-template-columns")).toBe("minmax(0, 1fr)");
    expect(setFor(always, "columns").get("display")).toBe("grid");
    expect(setFor(always, "search").has("grid-template-columns")).toBe(false);
    // No part is placed by column or by row there, and the map does not stick.
    const placed = always.filter((rule) => ["grid-column", "grid-row"].some((property) => rule.sets.has(property)));
    expect(placed.filter((rule) => !/^\.(title|lead)/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    expect(setFor(always, "map").has("position")).toBe(false);
    // What holds the tray, and what says a search was shared, are no boxes of their own at
    // any width, so each is laid out as it was.
    for (const part of ["shared", "tray"]) expect(setFor(always, part).get("display")).toBe("contents");
  });
});

describe("the page, on a screen as wide as can be", () => {
  test("test_before_a_search_no_settings_stand_open_and_the_two_ways_in_are_as_on_any_screen", async () => {
    const asked = aWideBrowser();
    const { user } = await openSearch();

    expect(theSettingsIfAny()).toBeNull();
    expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();
    expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
    // The page asked the browser for no width.
    expect(asked.filter((query) => /width/.test(query))).toEqual([]);

    await way(user, "deep");
    expect(theSettings()).toBeVisible();
    expect(screen.getByRole("button", { name: SETTINGS.rank })).toBeInTheDocument();
  });

  test("test_after_a_search_the_page_is_the_answer_and_the_map_and_the_settings_are_folded", async () => {
    aWideBrowser();
    const { user } = await openSearch();
    await search(user);

    expect(theSettingsIfAny()).toBeNull();
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
    // The way to share is where it was, after the first result.
    const [one, two] = results();
    const share = screen.getByRole("button", { name: SHARE.open });
    expect(comesBefore(one as HTMLElement, share)).toBe(true);
    expect(comesBefore(share, two as HTMLElement)).toBe(true);
  });

  test("test_the_box_what_burro_understood_the_part_that_refines_and_the_first_result_come_before_the_map_in_the_page", async () => {
    // The map is at the right for the eye. A keyboard and a screen reader reach the box,
    // what Burro says, the part that refines and the first result before it.
    aWideBrowser();
    const { user } = await openSearch();
    expect(comesBefore(promptBox(), theMap())).toBe(true);

    await search(user);

    const [one, two] = results();
    const order = [promptBox(), chips(), whatRefines() as HTMLElement, one as HTMLElement, theMap(), two as HTMLElement];
    order.slice(1).forEach((part, at) => expect(comesBefore(order[at] as HTMLElement, part)).toBe(true));
    // Nothing a person must act on stands between the box and what Burro says of the search.
    const line = theLine();
    expect(line.textContent?.startsWith(STATUS.rankedUnnamed(21))).toBe(true);
    const between = [...document.querySelectorAll<HTMLElement>("main button, main input, main select, main textarea")]
      .filter((control) => comesBefore(promptBox(), control) && comesBefore(control, line))
      .map((control) => control.textContent);
    expect(between).toEqual([PROMPT.startAgain, PROMPT.submit]);
  });

  test("test_with_the_settings_open_under_their_fold_the_page_has_no_accessibility_fault", async () => {
    aWideBrowser();
    const { user, container } = await openSearch();
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    await search(user);
    await settingsAt(user, SETTINGS.money);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});
