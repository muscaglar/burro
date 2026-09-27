import { readFileSync } from "node:fs";
import path from "node:path";

import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { BANNER, DISAGREES, PREVIEW_BANNER, SITE } from "@/content/site";
import { recordedAnswer } from "@/lib/api/recorded";
import { forgetWhatWasSaid, noteSaid } from "@/lib/api/said";
import { forgetSynthetic, noteSynthetic } from "@/lib/api/synthetic";

import { faultsIn } from "../../../test/support/axe";
import { asWritten } from "../../../test/support/contrast";
import { rulesOf } from "../../../test/support/css";
import { Burro } from "../kit/Burro/Burro";
import { Shell } from "./Shell";

let pathname = "/";
jest.mock("next/navigation", () => ({ usePathname: () => pathname }));

const { meta } = recordedAnswer("get_meta", "meta").body;
const real = { ...meta, release_id: "lon-2027-01-20-01", synthetic: false };
const preview = { ...real, preview: true };

function page(of = meta) {
  return render(
    <Shell meta={of}>
      <h1>A page</h1>
      <p>What the page says.</p>
    </Shell>,
  );
}

beforeEach(() => {
  pathname = "/";
  forgetSynthetic();
  forgetWhatWasSaid();
});

/** An answer of the API arrives, and says this of its data. */
function anAnswerSays(said: { synthetic: boolean; preview: boolean }) {
  act(() => {
    noteSynthetic(said.synthetic);
    noteSaid(said);
  });
}

describe("what every page has", () => {
  test("test_every_page_says_the_data_is_made_up_while_it_is", () => {
    page();

    expect(screen.getByRole("region", { name: BANNER.label })).toHaveTextContent(BANNER.text);
  });

  test("test_a_page_built_on_real_data_has_no_banner", () => {
    page(real);

    expect(screen.queryByRole("region", { name: BANNER.label })).toBeNull();
  });

  test("test_a_page_built_on_a_preview_of_real_data_says_it_is_a_preview_and_not_that_it_is_made_up", () => {
    const { container } = page(preview);

    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).toHaveTextContent(PREVIEW_BANNER.text);
    expect(screen.queryByRole("region", { name: BANNER.label })).toBeNull();
    // It stands where the other banner stands: before everything but the skip link.
    const order = [...container.querySelectorAll("a[href='#main'], section, header, main, footer")];
    expect(order.map((element) => element.tagName.toLowerCase())).toEqual([
      "a",
      "section",
      "header",
      "main",
      "footer",
    ]);
  });

  test("test_a_finished_release_has_no_banner_of_either_kind", () => {
    page(real);

    expect(screen.queryByRole("region", { name: PREVIEW_BANNER.label })).toBeNull();
    expect(screen.queryByRole("region", { name: BANNER.label })).toBeNull();
  });

  test("test_a_made_up_preview_says_both", () => {
    page({ ...meta, preview: true });

    expect(screen.getByRole("region", { name: BANNER.label })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).toBeInTheDocument();
  });

  test("test_the_first_thing_a_keyboard_reaches_skips_to_the_page_itself", async () => {
    page();

    await userEvent.tab();

    const skip = screen.getByRole("link", { name: SITE.skipToContent });
    expect(skip).toHaveFocus();
    expect(skip).toHaveAttribute("href", "#main");
    expect(screen.getByRole("main")).toHaveAttribute("id", "main");
    // A region that is skipped to must be able to take focus.
    expect(screen.getByRole("main")).toHaveAttribute("tabindex", "-1");
  });

  test("test_no_link_of_the_header_or_the_footer_is_fetched_ahead_of_time", () => {
    // Seen in a browser: every page that was opened asked for the three pages about the
    // website four times over, before anyone had pressed a link to one.
    const { container } = page();

    const links = [...container.querySelectorAll<HTMLAnchorElement>("header a[href], footer a[href]")];
    expect(links.length).toBeGreaterThanOrEqual(7);
    expect(links.filter((link) => link.getAttribute("data-prefetch") !== "false").map((link) => link.href)).toEqual(
      [],
    );
  });

  test("test_the_banner_comes_before_everything_but_the_skip_link", () => {
    const { container } = page();

    const order = [...container.querySelectorAll("a[href='#main'], section, header, main, footer")];

    expect(order.map((element) => element.tagName.toLowerCase())).toEqual([
      "a",
      "section",
      "header",
      "main",
      "footer",
    ]);
  });

  test.each(["banner", "contentinfo"] as const)(
    "test_vibes_methods_and_sources_are_linked_from_the_%s_and_no_statement_of_accessibility_is",
    (landmark) => {
      page();

      const links = within(screen.getByRole(landmark)).getAllByRole("link");

      expect(
        links.map((link) => [link.textContent, link.getAttribute("href")]),
      ).toEqual(
        expect.arrayContaining([
          ["Vibes", "/vibes"],
          ["Methods", "/methods"],
          ["Sources", "/sources"],
        ]),
      );
      // The page of the statement is gone, and nothing every page stands in leads to one.
      expect(links.filter((link) => /accessib/i.test(`${link.textContent} ${link.getAttribute("href")}`))).toEqual([]);
    },
  );

  test("test_the_foot_of_the_shell_leads_to_how_a_persons_words_are_handled_and_the_name_board_does_not", () => {
    page();

    const leads = (landmark: "banner" | "contentinfo") =>
      within(screen.getByRole(landmark))
        .getAllByRole("link")
        .filter((link) => link.getAttribute("href") === "/methods#words");

    expect(leads("contentinfo").map((link) => [link.textContent, link.getAttribute("aria-label")])).toEqual([
      ["Privacy", "Privacy: How your words are handled"],
    ]);
    expect(leads("banner")).toEqual([]);
  });

  test("test_the_name_of_the_site_leads_to_the_search", () => {
    page();

    expect(
      within(screen.getByRole("banner")).getByRole("link", { name: SITE.name }),
    ).toHaveAttribute("href", "/");
  });

  test("test_the_page_being_read_is_marked_in_the_navigation_in_more_than_colour", () => {
    pathname = "/sources";
    page();

    const nav = within(screen.getByRole("navigation", { name: SITE.navLabel }));

    expect(nav.getByRole("link", { name: "Sources" })).toHaveAttribute("aria-current", "page");
    expect(nav.getByRole("link", { name: "Methods" })).not.toHaveAttribute("aria-current");
  });

  test("test_the_footer_names_the_release_and_the_engine_behind_every_figure", () => {
    page();

    const footer = screen.getByRole("contentinfo");
    expect(footer).toHaveTextContent(meta.release_id);
    expect(footer).toHaveTextContent(meta.engine_version);
  });

  test("test_every_link_in_the_shell_takes_a_target_size", () => {
    page();

    for (const landmark of ["banner", "contentinfo"] as const) {
      for (const link of within(screen.getByRole(landmark)).getAllByRole("link")) {
        expect(link).toHaveClass("target");
      }
    }
    expect(screen.getByRole("link", { name: SITE.skipToContent })).toHaveClass("target");
  });

  test("test_the_two_navigations_can_be_told_apart_by_name", () => {
    page();

    const names = screen.getAllByRole("navigation").map((nav) => nav.getAttribute("aria-label"));

    expect(names).toEqual([SITE.navLabel, SITE.footerLabel]);
    expect(new Set(names).size).toBe(2);
  });

  test("test_the_shell_has_no_accessibility_fault", async () => {
    const { container } = page();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("the rabbit of every page", () => {
  const his = (container: HTMLElement) => [...container.querySelectorAll<HTMLElement>("[data-pose]")];
  const whereOf = (he: HTMLElement) => (he.closest("header") ? "board" : he.closest("footer") ? "foot" : he.closest("main") ? "page" : "grass");

  test("test_every_page_has_him_in_the_name_board_and_over_the_foot_and_a_style_sheet_draws_one_of_the_two", () => {
    // A person who walked the website asked for him to be always moving, and found him on
    // the search page and on no other. What every page stands in draws him: in the name
    // board where it has room for him, and over the foot where it has not.
    const { container } = page();

    expect(his(container).map(whereOf)).toEqual(["board", "foot"]);
    // Each is seen from his back up, from behind a rule, and stirs. Nothing stands by him
    // to be pressed, and the whole of him is kept from a screen reader.
    for (const he of his(container)) {
      expect([he.getAttribute("data-pose"), he.getAttribute("data-peeps")]).toEqual(["sits", "true"]);
      expect(he.querySelector("[data-moves]")).toHaveAttribute("data-moves", "true");
      expect(he).toHaveAttribute("aria-hidden", "true");
      expect(he.querySelectorAll("button, a, input, [tabindex]")).toHaveLength(0);
    }
    // Nothing of him is on the grass, outside what a screen reader knows as a part of the page.
    expect(his(container).filter((he) => he.closest("header, main, footer") === null)).toEqual([]);
  });

  test("test_he_moves_on_the_next_page_as_he_moved_and_nothing_of_him_is_kept_by_the_browser", () => {
    const { container, rerender } = page();
    const moves = () => his(container).map((he) => he.querySelector("[data-moves]")?.getAttribute("data-moves"));

    expect(moves()).toEqual(["true", "true"]);
    // The shell stays while one page gives way to the next, and so does he.
    pathname = "/methods";
    rerender(
      <Shell meta={meta}>
        <h1>Another page</h1>
      </Shell>,
    );
    expect(moves()).toEqual(["true", "true"]);
    expect([window.localStorage.length, window.sessionStorage.length, document.cookie, window.location.search, window.location.hash]).toEqual([
      0,
      0,
      "",
      "",
      "",
    ]);
  });

  test("test_where_the_page_draws_him_he_is_on_the_page_once_and_comes_to_the_board_as_the_page_lets_him_go", async () => {
    // A style sheet lays nothing of him out in the board or over the foot where the page
    // holds him, which is all a page that has not run has. Once it runs he is in the page
    // once: nothing of him is in the board to be heard or to stop a keyboard.
    const user = userEvent.setup();
    const { container, rerender } = render(
      <Shell meta={meta}>
        <h1>The search</h1>
        <Burro pose="sits" />
      </Shell>,
    );

    expect(his(container).map(whereOf)).toEqual(["page"]);
    expect(screen.queryAllByRole("button")).toEqual([]);
    // The name, and then the first of the pages: nothing of him is a stop between them.
    await user.tab();
    await user.tab();
    expect(screen.getByRole("link", { name: SITE.name })).toHaveFocus();
    await user.tab();
    expect(document.activeElement?.tagName).toBe("A");
    expect(document.activeElement?.closest("nav")).not.toBeNull();

    // The answer is in, and the page draws him no more.
    rerender(
      <Shell meta={meta}>
        <h1>The search</h1>
        <p>The answer</p>
      </Shell>,
    );
    expect(his(container).map(whereOf)).toEqual(["board", "foot"]);
  });

  test("test_a_keyboard_goes_from_the_name_to_the_pages_and_stops_at_nothing_of_him", async () => {
    const user = userEvent.setup();
    page();

    await user.tab();
    await user.tab();
    expect(screen.getByRole("link", { name: SITE.name })).toHaveFocus();
    await user.tab();
    expect(within(screen.getByRole("banner")).getByRole("link", { name: SITE.nav.vibes })).toHaveFocus();

    // Over the foot too: what a keyboard comes to there is its links, and nothing before them.
    const foot = [...screen.getByRole("contentinfo").querySelectorAll("a, button, input, [tabindex]")];
    expect(foot.map((one) => one.tagName)).toEqual(foot.map(() => "A"));
    expect(foot[0]).toHaveTextContent(SITE.nav.vibes);
  });
});

describe("a page read while the service answers with another kind of data than it was built on", () => {
  const WHAT_THE_PAGE_SAYS = "What the page says.";

  test("test_a_page_built_on_made_up_data_shows_no_real_figure_under_the_words_made_up", () => {
    // Read in the code, by a checker: a website built while the service held the made-up
    // release, and read once it held a preview of real data, said "made-up" over London.
    page(meta);
    expect(screen.getByRole("main")).toHaveTextContent(WHAT_THE_PAGE_SAYS);

    anAnswerSays({ synthetic: false, preview: true });

    const main = screen.getByRole("main");
    expect(main).not.toHaveTextContent(WHAT_THE_PAGE_SAYS);
    expect(within(main).getByRole("alert")).toHaveTextContent(DISAGREES.text);
    expect(screen.queryByRole("heading", { name: "A page" })).toBeNull();
  });

  test("test_a_page_built_on_real_data_shows_no_made_up_figure_as_real", () => {
    page(preview);

    anAnswerSays({ synthetic: true, preview: true });

    expect(screen.getByRole("main")).not.toHaveTextContent(WHAT_THE_PAGE_SAYS);
    expect(screen.getByRole("alert")).toHaveTextContent(DISAGREES.text);
    expect(screen.getByRole("region", { name: BANNER.label })).toBeInTheDocument();
  });

  test("test_a_page_built_on_a_finished_release_says_so_when_an_answer_is_of_a_preview", () => {
    page(real);
    expect(screen.queryByRole("region", { name: PREVIEW_BANNER.label })).toBeNull();

    anAnswerSays({ synthetic: false, preview: true });

    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).toHaveTextContent(
      PREVIEW_BANNER.text,
    );
    expect(screen.getByRole("main")).not.toHaveTextContent(WHAT_THE_PAGE_SAYS);
    expect(screen.getByRole("alert")).toHaveTextContent(DISAGREES.text);
  });

  test("test_a_page_built_on_a_preview_shows_nothing_when_an_answer_is_of_a_finished_release", () => {
    page(preview);

    anAnswerSays({ synthetic: false, preview: false });

    expect(screen.getByRole("main")).not.toHaveTextContent(WHAT_THE_PAGE_SAYS);
    // The banner stays: the page was built on a preview, and says so still.
    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).toBeInTheDocument();
  });

  test.each([
    ["made up", meta, { synthetic: true, preview: false }],
    ["a preview of real data", preview, { synthetic: false, preview: true }],
    ["finished", real, { synthetic: false, preview: false }],
  ])("test_a_page_and_an_answer_that_are_both_%s_show_the_page", (_, built, said) => {
    page(built);

    anAnswerSays(said);

    expect(screen.getByRole("main")).toHaveTextContent(WHAT_THE_PAGE_SAYS);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("test_a_release_that_moved_on_to_another_of_the_same_kind_changes_nothing_here", () => {
    // Every answer names its release, and the search keeps what each release made apart.
    page(preview);

    anAnswerSays({ synthetic: false, preview: true });
    anAnswerSays({ synthetic: false, preview: true });

    expect(screen.getByRole("main")).toHaveTextContent(WHAT_THE_PAGE_SAYS);
  });

  test("test_what_is_said_in_place_of_the_page_holds_no_figure_and_names_no_place", () => {
    expect(/\d/.test(DISAGREES.text)).toBe(false);
    expect(DISAGREES.text.includes("London")).toBe(false);
  });

  test("test_what_is_said_in_place_of_the_page_has_no_accessibility_fault", async () => {
    const { container } = page(meta);

    anAnswerSays({ synthetic: false, preview: true });

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("where the name board, the page and the foot stand", () => {
  const RULES = rulesOf(readFileSync(path.join(__dirname, "Shell.module.css"), "utf8"));
  const WIDTHS = [null, /min-width:\s*40rem/, /min-width:\s*60rem/] as const;
  /** What the shell says of a part by a property, at a width: `null` is what it says always. */
  const said = (selector: string, property: string, under: RegExp | null = null) =>
    RULES.filter((rule) => rule.selector === selector && (under === null ? rule.under === null : under.test(rule.under ?? ""))).flatMap(
      (rule) => rule.sets.get(property) ?? [],
    );
  const DRESSED = ".shell:has(> main > [data-dressed])";

  test("test_the_three_stand_on_the_grass_in_the_order_they_are_read_each_in_a_box", () => {
    const { container } = page();
    const shell = container.firstElementChild as HTMLElement;
    const boxes = [...shell.children].filter((one) => ["HEADER", "MAIN", "FOOTER"].includes(one.tagName));

    expect(boxes.map((one) => one.tagName.toLowerCase())).toEqual(["header", "main", "footer"]);
    // The board and the foot are boxes of the kit. The page is a box the shell draws, until it is dressed.
    expect([boxes[0]?.firstElementChild?.getAttribute("data-kind"), boxes[2]?.firstElementChild?.getAttribute("data-kind")]).toEqual([
      "box",
      "box",
    ]);
    expect(said(".main", "border-image").length).toBe(1);
  });

  test("test_the_grass_at_either_hand_and_the_room_of_a_box_are_the_same_for_the_board_the_page_and_the_foot", () => {
    // The page says both for itself, where a test of every page reads them. The shell says
    // them for the board and the foot, and the two must agree at every width.
    for (const under of WIDTHS) {
      for (const token of ["--gutter", "--room"]) {
        const [ofTheShell, ofThePage] = [said(".shell", token, under), said(".main", token, under)];
        expect([String(under), token, ofTheShell]).toEqual([String(under), token, ofThePage]);
      }
    }
    expect(said(".shell", "--gutter")).toEqual(["var(--space-2)"]);
  });

  test("test_beside_a_page_nobody_has_dressed_the_board_and_the_foot_are_as_wide_as_its_box_and_its_shadow", () => {
    for (const part of [".shell > header", ".shell > footer"]) {
      expect([part, said(part, "width"), said(part, "max-width")]).toEqual([part, said(".main", "width"), said(".main", "max-width")]);
      expect([part, said(part, "margin-inline")]).toEqual([part, ["auto"]]);
    }
    // The shadow of the page's box falls past it. The shadow of a box of the kit is inside the
    // room the box takes: so the box is wider than what holds it, by as far as the shadow falls.
    const falls = /^(calc\(var\(--px\) \* \d+\)) /.exec(asWritten()["--box-shadow"] ?? "")?.[1] ?? "no shadow";
    const past = falls.replace("* ", "* -");
    expect(falls).toBe("calc(var(--px) * 2)");
    expect([said(".shell > header > *", "margin-inline-end"), said(".shell > footer > *", "margin-inline-end")]).toEqual([[past], [past]]);
  });

  test("test_beside_a_page_that_is_dressed_they_are_as_wide_as_the_page_and_stand_in_line_with_its_boxes", () => {
    const ofThePage = said(".main:has(> [data-dressed])", "max-width");

    expect(ofThePage).toHaveLength(1);
    for (const part of ["header", "footer"]) {
      expect([part, said(`${DRESSED} > ${part}`, "max-width")]).toEqual([part, ofThePage]);
      // Its shadow is inside it, as the shadow of every box of the page is.
      expect([part, said(`${DRESSED} > ${part} > *`, "margin-inline-end")]).toEqual([part, ["0"]]);
    }
  });

  test("test_the_grass_shows_between_the_banner_the_board_the_page_and_the_foot", () => {
    const gaps = [...said(".shell > header", "margin-block-start"), ...said(".main", "margin"), ...said(".shell > footer", "margin-block")];

    expect(gaps).toEqual(["var(--space-2)", "var(--space-2) auto 0", "var(--space-7) var(--space-4)"]);
    // On a wider screen there is more of it, and as much over the page as over the board.
    for (const under of [WIDTHS[1], WIDTHS[2]]) {
      expect([String(under), said(".shell > header", "margin-block-start", under)]).toEqual([
        String(under),
        said(".main", "margin-block-start", under),
      ]);
    }
  });

  test("test_less_grass_shows_between_them_on_a_narrow_screen_once_a_search_is_open", () => {
    // Measured on a phone, with every part dressed: the first result ended 150 px under the
    // foot of the first screen. What stands over the answer gives way, and the room between
    // two boxes is the first to: half of it, which is as far as a hard shadow falls.
    const NARROW = /max-width:\s*40rem/;
    const OPEN = '.shell:has([data-search="open"])';
    const gaps = [said(`${OPEN} > header`, "margin-block-start", NARROW), said(`${OPEN} > .main`, "margin-block-start", NARROW)];

    expect(gaps).toEqual([["var(--space-1)"], ["var(--space-1)"]]);
    // It is so where a search is open, and nowhere else: no rule for a narrow screen sets it of every page.
    expect([said(".shell > header", "margin-block-start", NARROW), said(".main", "margin-block-start", NARROW)]).toEqual([[], []]);
    // As far as the shadow of the look falls, so that the grass still shows between two boxes.
    expect(asWritten()["--space-1"]).toBe("4px");
    expect(asWritten()["--box-shadow"]?.startsWith("calc(var(--px) * 2) calc(var(--px) * 2)")).toBe(true);
    expect(asWritten()["--px"]).toBe("2px");
  });

  test("test_the_name_of_the_website_is_a_size_larger_where_the_board_has_room_and_is_never_higher_than_a_control", () => {
    const name = ".shell > header > div > a:first-child";
    const tokens = asWritten();
    const pixels = (size: string | undefined) => Number.parseFloat(tokens[/^var\((--[a-z0-9-]+)\)$/.exec(size ?? "")?.[1] ?? ""] ?? "") * 16;

    expect([said(name, "font-size"), said(name, "font-size", WIDTHS[1])]).toEqual([["var(--name-2)"], ["var(--name-3)"]]);
    expect(said(name, "line-height")).toEqual(["1"]);
    for (const size of [...said(name, "font-size"), ...said(name, "font-size", WIDTHS[1])]) {
      expect(pixels(size)).toBeLessThanOrEqual(Number.parseInt(tokens["--target"] ?? "", 10));
    }
    // The name is the first thing in the box of the board, which is what the rule is written for.
    page();
    const board = screen.getByRole("banner").firstElementChild as HTMLElement;
    expect(board.tagName).toBe("DIV");
    expect(board.firstElementChild).toBe(within(board).getByRole("link", { name: SITE.name }));
  });
});

describe("what stands in place of a page that is held back", () => {
  test("test_it_is_one_box_on_the_grass_and_the_shell_draws_no_box_round_it", () => {
    page(meta);

    anAnswerSays({ synthetic: false, preview: true });

    const main = screen.getByRole("main");
    expect(main.children).toHaveLength(1);
    expect(main.firstElementChild).toHaveAttribute("data-dressed");
    expect(within(main).getByRole("alert")).toHaveAttribute("data-kind", "box");
    expect(within(main).getByRole("heading", { level: 1, name: DISAGREES.heading })).toBeInTheDocument();
    // It offers nothing to press: the website must be built again, which no press does.
    expect(within(main).queryAllByRole("button")).toEqual([]);
    expect(within(main).queryAllByRole("link")).toEqual([]);
  });
});
