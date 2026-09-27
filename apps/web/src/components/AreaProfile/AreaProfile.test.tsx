/**
 * The look of the page of an area: what stands in a box, where the town of the area
 * stands, and what is never drawn. What the page says, and in which order, is held by
 * `test/area/`. jsdom lays nothing out, so how a part is drawn is held by `styles.test.ts`.
 */

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import AreaPage from "@/app/[city]/[area]/page";
import { Shell } from "@/components/Shell/Shell";
import { AREA, LOOK, PORTRAIT } from "@/content/area";
import { COMPARE, TRAY } from "@/content/compare";
import { TOWN } from "@/content/town";
import { recordedAnswer } from "@/lib/api/recorded";
import { saidOf } from "@/lib/town/said";

import { faultsIn } from "../../../test/support/axe";
import { TOWN_DRAWN, TOWN_STANDS } from "./look";

jest.mock("next/navigation", () => ({
  ...jest.requireActual("next/navigation"),
  usePathname: () => "/",
}));

const meta = recordedAnswer("get_meta", "meta").body;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const profile = (slug: string) => recordedAnswer("get_area", `area/${slug}`).body.data;
const [first = { slug: "", name: "" }] = areas;

/** The parts of a town that are left blank for an area. */
const blankOf = (slug: string) => saidOf(profile(slug).tags, meta.data).filter(({ state }) => state !== "drawn");
/** Areas that are hard to draw, each found by what is so of it and none by its name. */
const littleKnown = areas.find((area) => profile(area.slug).portrait.unplaced.length > 0 && blankOf(area.slug).length > 0);
const notRanked = areas.find((area) => !area.rankable);
const HARD = [first, littleKnown, notRanked].flatMap((area) => (area === undefined ? [] : [area.slug]));

async function show(slug: string) {
  const view = render(<Shell meta={meta.meta}>{await AreaPage({ params: Promise.resolve({ city: "synthetic", area: slug }) })}</Shell>);
  return { ...view, page: screen.getByRole("article") };
}

/**
 * The tray of areas to compare, which stands at the foot of the screen and not in the page:
 * it is another part's, and brings a ground of its own. It is found by what it is called.
 */
const trayOf = (page: HTMLElement) =>
  [...page.querySelectorAll<HTMLElement>("section[aria-labelledby], section[aria-label]")].find(
    // It is named by its heading once it holds an area, and without one until then.
    (part) => (part.getAttribute("aria-label") ?? document.getElementById(part.getAttribute("aria-labelledby") ?? "")?.textContent) === TRAY.title,
  ) ?? null;

/** Every piece of text the page draws, with the element that holds it. What is kept for a screen reader is not drawn. */
function drawnIn(page: HTMLElement): { readonly said: string; readonly held: HTMLElement }[] {
  const found: { said: string; held: HTMLElement }[] = [];
  const tray = trayOf(page);
  const walker = document.createTreeWalker(page, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node !== null; node = walker.nextNode()) {
    const said = node.textContent?.trim() ?? "";
    const held = node.parentElement;
    if (said === "" || held === null) continue;
    if (held.closest("script, style, noscript, .visually-hidden") !== null) continue;
    if (tray?.contains(held) === true) continue;
    found.push({ said, held });
  }
  return found;
}

/**
 * What brings the cream a thing is read on: a box or a slip of the kit, and a button of the
 * look, which is drawn on a ground of its own.
 */
const GROUND = "[data-kind], .press";

describe("the page of an area, on the meadow", () => {
  test("test_the_page_says_that_it_is_dressed_so_that_the_shell_draws_no_box_round_it", async () => {
    const { page } = await show(first.slug);

    expect(page).toHaveAttribute("data-dressed");
    // The shell looks for it on what stands directly in `main`.
    expect(page.parentElement).toBe(screen.getByRole("main"));
  });

  test.each(areas.map((area) => area.slug))(
    "test_every_sentence_figure_and_link_stands_in_a_box_and_nothing_is_read_on_the_grass: %s",
    async (slug) => {
      const { page } = await show(slug);

      const drawn = drawnIn(page);
      const onTheGrass = drawn.filter(({ held }) => held.closest(GROUND) === null || !page.contains(held.closest(GROUND)));

      expect(drawn.length).toBeGreaterThan(100);
      expect(onTheGrass.map(({ said }) => said.slice(0, 40))).toEqual([]);
      // Nor does a link or a fold stand on it, whatever it says.
      const tray = trayOf(page);
      const pressed = [...page.querySelectorAll<HTMLElement>("a, button, summary")].filter((one) => tray?.contains(one) !== true);
      expect(pressed.length).toBeGreaterThan(20);
      expect(pressed.filter((one) => one.closest(GROUND) === null).map((one) => one.textContent)).toEqual([]);
    },
  );

  test("test_each_part_of_the_page_is_a_box_of_its_own_and_the_page_itself_is_none", async () => {
    const { page } = await show(first.slug);
    const portrait = screen.getByRole("region", { name: PORTRAIT.title });
    // The tray of areas to compare is no part of the page: it is another's, at the foot of the screen.
    const parts = [...page.children].filter((part) => part.matches("[data-kind]") && part !== portrait && part !== trayOf(page));

    expect(page).not.toHaveAttribute("data-kind");
    // The head, the list of what follows, the parts that open, and where to go and look.
    expect(parts.map((part) => [part.tagName, part.getAttribute("data-kind")])).toEqual([
      ["HEADER", "box"],
      ["NAV", "plain"],
      ["DIV", "box"],
      ["SECTION", "box"],
    ]);
    expect(within(parts[0] as HTMLElement).getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(parts[1]).toHaveAccessibleName(AREA.contents);
    expect(within(parts[3] as HTMLElement).getByRole("heading", { level: 2 })).toHaveTextContent(LOOK.title);
    // The portrait stands between the head and the list: it is a box, or brings boxes of its own.
    expect(portrait.parentElement).toBe(page);
    expect([parts[0], portrait, parts[1]].map((part) => [...page.children].indexOf(part as Element))).toEqual([0, 1, 2]);
    expect(portrait.matches("[data-kind]") || portrait.querySelector(":scope > [data-kind]") !== null).toBe(true);
  });

  test.each(["alike", "cost", "measured", "sources", "census", "income"])(
    "test_a_part_that_opens_is_the_browsers_own_fold_and_stands_in_the_one_box_of_such_parts: %s",
    async (id) => {
      await show(first.slug);
      const part = document.getElementById(id);

      expect(part?.tagName).toBe("DETAILS");
      expect(part?.parentElement).toHaveAttribute("data-kind", "box");
      expect(part?.parentElement?.parentElement).toBe(screen.getByRole("article"));
      // It is one of a stack, and what opens it is the bar of every fold of the website: its
      // arrow, which says nothing, and the heading of the part.
      const bar = part?.querySelector(":scope > summary");
      expect(part).toHaveClass("fold", "stacked", "closed");
      expect(bar).toHaveClass("button", "bar", "target");
      expect(bar).not.toHaveClass("alone");
      expect([...(bar?.children ?? [])].map((child) => child.tagName)).toEqual(["SPAN", "H2"]);
      expect(bar?.firstElementChild).toHaveAttribute("aria-hidden", "true");
      expect(bar?.firstElementChild).toBeEmptyDOMElement();
      // The page hands the arrow to all it holds, once: a bar bears no style of its own.
      expect(bar).not.toHaveAttribute("style");
    },
  );

  test("test_the_groups_inside_a_part_are_a_stack_of_bars_of_their_own_each_under_a_small_heading", async () => {
    await show(first.slug);
    const groups = [...(document.getElementById("measured")?.querySelectorAll("details") ?? [])];

    expect(groups.length).toBeGreaterThan(5);
    for (const group of groups) {
      const bar = group.querySelector(":scope > summary");
      expect(group).toHaveClass("fold", "stacked");
      expect(bar).toHaveClass("button", "bar", "target");
      expect([...(bar?.children ?? [])].map((child) => child.tagName)).toEqual(["SPAN", "H3"]);
      expect(group.open).toBe(false);
      // What it holds stands in it, with nothing between: its rows are found where they were.
      expect(group.querySelectorAll(":scope > ul > li").length).toBeGreaterThan(0);
    }
    // They stand together, with nothing between two of them: one stack.
    expect(new Set(groups.map((group) => group.parentElement)).size).toBe(1);
    expect([...(groups[0]?.parentElement?.children ?? [])]).toEqual(groups);
  });

  test("test_what_the_style_sheet_draws_with_is_handed_to_it_once_on_the_page_by_name", async () => {
    const { page } = await show(first.slug);
    const handed = (name: string) => page.style.getPropertyValue(name);

    expect(handed("--arrow")).toBe('url("/art/ui-arrow.png")');
    expect(handed("--button")).toBe('url("/art/ui-button.png")');
    expect(handed("--button-down")).toBe('url("/art/ui-button-down.png")');
    for (const length of ["--arrow-w", "--arrow-h", "--button-top", "--button-right", "--button-foot", "--button-left"]) {
      expect([length, /^[1-9]\d*$/.test(handed(length))]).toEqual([length, true]);
    }
  });

  test("test_the_way_back_is_a_button_of_the_look_and_is_the_link_it_was", async () => {
    const { page } = await show(first.slug);
    const back = within(page).getByRole("link", { name: AREA.search });

    expect(back).toHaveAttribute("href", "/");
    expect(back).toHaveClass("press", "target");
    // It is in the colour of what matters most, and what starts a search from a list of vibes is plain.
    expect(back.querySelector("[data-kind]")).toHaveAttribute("data-kind", "go");
    const from = within(page).getByRole("link", { name: PORTRAIT.search.button });
    expect(from).toHaveClass("press", "target");
    expect(from.querySelector("[data-kind]")).toHaveAttribute("data-kind", "plain");
  });

  test("test_burro_is_not_drawn_on_the_page_of_an_area", async () => {
    const { page } = await show(first.slug);
    const drawings = [...page.querySelectorAll<HTMLElement>("[style]")].map((one) => one.getAttribute("style") ?? "");

    expect(drawings.length).toBeGreaterThan(20);
    expect(drawings.filter((style) => /\/art\/burro/.test(style))).toEqual([]);
  });

  test("test_the_page_has_no_accessibility_fault_whatever_is_known_of_the_area", async () => {
    // The first area, one that some vibe cannot place, and one that the release does not rank.
    expect(HARD).toHaveLength(3);
    for (const slug of HARD) {
      const { container, unmount } = await show(slug);
      expect([slug, await faultsIn(container, { wholePage: true })]).toEqual([slug, []]);
      unmount();
    }
  });
});

describe("the town of the area, at the head of its page", () => {
  const head = () => screen.getByRole("heading", { level: 1 }).closest("header") as HTMLElement;
  const town = () => head().querySelector("figure") as HTMLElement;

  test.each(areas.map((area) => [area.name, area.slug]))(
    "test_it_stands_in_the_box_of_the_head_with_its_line_in_sight: %s",
    async (_, slug) => {
      await show(slug);

      expect(head()).toHaveAttribute("data-kind", "box");
      expect(head().querySelectorAll("figure").length).toBe(1);
      const line = within(town()).getByText(TOWN.line);
      expect(line).toBeVisible();
      expect(line.closest(".visually-hidden, [hidden], [aria-hidden='true'], details") === null).toBe(true);
      // No other town is drawn on the page: the line is said once, by the one at its head.
      const said = (screen.getByRole("article").textContent ?? "").split(TOWN.line).length - 1;
      expect(said).toBe(1);
    },
  );

  test("test_the_name_comes_before_it_for_whoever_hears_the_page_whichever_side_it_stands_at", async () => {
    await show(first.slug);
    const name = screen.getByRole("heading", { level: 1 });

    expect(name.compareDocumentPosition(town()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // What stands beside the name is heard before the town too: it is of the name.
    expect((name.parentElement as HTMLElement).compareDocumentPosition(town()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(name.parentElement).not.toContainElement(town());
    expect(head()).toHaveAttribute("data-town", TOWN_STANDS);
  });

  test("test_it_is_drawn_from_the_vibes_of_the_area_and_says_so_band_by_band_to_a_screen_reader", async () => {
    for (const { slug, name } of areas.slice(0, 6)) {
      const { unmount } = await show(slug);
      const said = saidOf(profile(slug).tags, meta.data);

      expect(within(town()).getByRole("img")).toHaveAccessibleName(
        [`${TOWN.nameOf(name)}.`, ...said.map((part) => `${part.name}: ${part.says}.`)].join(" "),
      );
      unmount();
    }
  });

  test("test_it_is_never_drawn_larger_than_the_line_that_chooses_says", async () => {
    await show(first.slug);

    expect(within(town()).getByRole("img")).toHaveAttribute("data-size", TOWN_DRAWN === "screen" ? "large" : "small");
  });

  test("test_it_draws_no_name_no_rank_and_no_fit_and_nothing_of_it_can_be_pressed", async () => {
    await show(first.slug);
    const inSight = (town().textContent ?? "").replace(/\s+/g, " ").trim();

    expect(inSight.includes(first.name)).toBe(false);
    expect(/\d/.test(inSight)).toBe(false);
    expect(town().querySelectorAll("a, button, input, summary, [tabindex], [role='button']")).toHaveLength(0);
  });

  test("test_an_area_that_cannot_be_placed_has_its_town_left_blank_and_says_which_part_in_sight", async () => {
    if (littleKnown === undefined) throw new Error("Every recorded area is placed on all four vibes of a town.");
    await show(littleKnown.slug);
    const blank = blankOf(littleKnown.slug);

    expect(blank.length).toBeGreaterThan(0);
    expect(within(town()).getByText(TOWN.leftBlank(blank.map(({ part }) => TOWN.listed[part])), { exact: false })).toBeVisible();
  });
});

describe("the way to compare, at the head of the page of an area", () => {
  const head = () => screen.getByRole("heading", { level: 1 }).closest("header") as HTMLElement;
  const town = () => head().querySelector("figure") as HTMLElement;
  const group = () => within(head()).getByRole("group", { name: AREA.compare });
  /** What each piece of a drawing is handed: its picture, its frame and where it stands. */
  const piecesOf = (drawing: Element) =>
    [...drawing.children].map((piece) =>
      ["--art", "--w", "--h", "--frames", "--frame", "--x", "--y"]
        .map((name) => (piece as HTMLElement).style.getPropertyValue(name))
        .join(" "),
    );

  test("test_it_stands_at_the_head_by_the_town_and_says_what_the_button_of_a_result_says", async () => {
    // The founder: "Compare function is great, make this more of a highlighted feature".
    await show(first.slug);
    const way = within(group()).getByRole("button", { name: COMPARE.addNamed(first.name) });

    // In the box of the head, and the next thing after the town.
    expect(head()).toContainElement(way);
    expect(town().nextElementSibling).toBe(group());
    // As plain as on a result: the same words, on a button of the browser's own.
    expect(way.tagName).toBe("BUTTON");
    expect(way).toHaveTextContent(new RegExp(`^${COMPARE.addShort}$`));
    expect(way.querySelector("[data-kind]")).toHaveAttribute("data-kind", "plain");
    expect(way).toHaveClass("target");
  });

  test("test_beside_it_is_said_what_comparing_is_until_the_area_is_chosen", async () => {
    // No list stands over this page to say so, and a person may come to it from anywhere.
    await show(first.slug);
    const user = userEvent.setup({ delay: null });

    expect(within(group()).getByText(COMPARE.inviteHere)).toBeVisible();
    expect(COMPARE.inviteHere).toMatch(/side by side/);

    await user.click(within(group()).getByRole("button", { name: COMPARE.addNamed(first.name) }));

    // Once it is chosen the button says so, and beside it what to do next.
    const chosen = within(group()).getByRole("button", { name: COMPARE.removeNamed(first.name) });
    expect(chosen).toHaveTextContent(new RegExp(`^${COMPARE.removeShort}$`));
    expect(chosen.querySelector("[data-kind]")).toHaveAttribute("data-kind", "on");
    expect(within(group()).queryByText(COMPARE.inviteHere)).toBeNull();
    expect(within(group()).getByText(TRAY.one)).toBeVisible();
  });

  test("test_the_bar_draws_the_town_that_stands_at_the_head_of_the_page_and_the_page_hands_the_browser_little_for_it", async () => {
    const { page } = await show(first.slug);
    const user = userEvent.setup({ delay: null });

    await user.click(within(group()).getByRole("button", { name: COMPARE.addNamed(first.name) }));

    const bar = trayOf(page) as HTMLElement;
    const inTheBar = within(bar).getByRole("img");
    const atTheHead = within(town()).getByRole("img");
    expect(piecesOf(inTheBar)).toEqual(piecesOf(atTheHead));
    expect(inTheBar.getAttribute("aria-label")).toBe(atTheHead.getAttribute("aria-label"));
    expect(within(bar).getByText(first.name)).toBeInTheDocument();
  });

  test("test_nothing_at_the_head_says_how_the_area_did_or_marks_it_out", async () => {
    await show(first.slug);

    expect(group().textContent).not.toMatch(/\b(rank|fit|best|better|winner)\b/i);
    expect(/\d/.test(group().textContent ?? "")).toBe(false);
  });
});
