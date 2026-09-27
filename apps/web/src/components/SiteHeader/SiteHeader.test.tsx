import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { SITE } from "@/content/site";

import { faultsIn } from "../../../test/support/axe";
import { asWritten } from "../../../test/support/contrast";
import { isFor, rulesOf, type Rule } from "../../../test/support/css";
import { isDrawn } from "../kit/drawings";
import { boardOnANarrowScreen, BURRO_IN_THE_BOARD, BURRO_ON_A_NARROW_SCREEN, overTheFoot } from "./look";
import { SiteHeader } from "./SiteHeader";

let pathname = "/";
jest.mock("next/navigation", () => ({ usePathname: () => pathname }));

const RULES = rulesOf(readFileSync(path.join(__dirname, "SiteHeader.module.css"), "utf8"));
const NARROW = /max-width:\s*40rem/;
const ROOMY = /min-width:\s*40rem/;
const FORCED = /forced-colors:\s*active/;
/** What holds only where the header is handed the other way to draw a narrow screen. */
const OTHER_WAY = '.inner[data-narrow="keys"]';
const of = (selector: string, under: RegExp | null) =>
  RULES.filter((rule) => rule.selector === selector && (under === null ? rule.under === null : under.test(rule.under ?? "")));
const sets = (rules: readonly Rule[]) => new Map(rules.flatMap((rule) => [...rule.sets]));

/** The drawing a link is handed, as the page names it: `url("/art/ui-button.png")` gives `ui-button`. */
const drawingOf = (link: HTMLElement, token: string) => /\/art\/([a-z0-9-]+)\.png/.exec(link.style.getPropertyValue(token))?.[1] ?? "";

beforeEach(() => {
  pathname = "/";
});

describe("the name board", () => {
  test("test_the_name_and_the_three_links_stand_in_one_box", () => {
    render(<SiteHeader />);

    const board = screen.getByRole("banner").firstElementChild as HTMLElement;

    expect(board).toHaveAttribute("data-kind", "box");
    expect(within(board).getByRole("link", { name: SITE.name })).toHaveAttribute("href", "/");
    expect(within(board).getByRole("navigation", { name: SITE.navLabel })).toBeInTheDocument();
    expect(within(board).getAllByRole("link").map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      [SITE.name, "/"],
      [SITE.nav.vibes, "/vibes"],
      [SITE.nav.methods, "/methods"],
      [SITE.nav.sources, "/sources"],
    ]);
    // The founder: "get rid of the accessibility tab". The board holds three, and none of them leads to a statement.
    expect(within(board).queryByRole("link", { name: /accessib/i })).toBeNull();
    // Nothing of the header is read on the grass: all of it is in the box.
    expect(screen.getByRole("banner").children).toHaveLength(1);
  });

  test("test_the_box_brings_its_own_ground_and_the_header_lays_none_over_it", () => {
    // The ground and the shadow of a box are drawn behind it. A ground laid on the box, or on
    // what holds it, would lie over the notch of each corner, or over the grass.
    const laid = RULES.filter((rule) => /^\.(header|inner)$/.test(rule.selector) && (rule.sets.has("background") || rule.sets.has("overflow")));

    expect(laid.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_every_link_of_the_board_is_a_native_link_of_the_size_of_a_main_control", () => {
    render(<SiteHeader />);

    for (const link of within(screen.getByRole("banner")).getAllByRole("link")) {
      expect(link.tagName).toBe("A");
      expect(link).toHaveClass("target");
      expect(link).toHaveAttribute("data-prefetch", "false");
    }
  });

  test("test_a_link_is_a_short_label_and_is_set_in_the_face_of_names", () => {
    const link = sets(of(".link", null));

    expect(link.get("font")).toBe("400 var(--name-1) / 1 var(--font-name)");
    // The face has one weight and stands upright: a browser that thickens it smears it.
    expect(link.get("font-synthesis")).toBe("none");
    // No word of the board holds a figure, which would be set in the reading face.
    for (const label of Object.values(SITE.nav)) expect([label, /\d/.test(label)]).toEqual([label, false]);
  });

  test("test_where_there_is_room_a_link_is_drawn_as_town_map_draws_a_button", () => {
    render(<SiteHeader />);
    const link = screen.getByRole("link", { name: SITE.nav.methods });
    const drawn = sets(of(".link", ROOMY));

    expect([drawingOf(link, "--art"), drawingOf(link, "--art-down")]).toEqual(["ui-button", "ui-button-down"]);
    expect(isDrawn(drawingOf(link, "--art")) && isDrawn(drawingOf(link, "--art-down"))).toBe(true);
    // The picture is cut in nine where the drawing is cut, and its sides are laid end to end.
    expect(drawn.get("border-image")).toBe(
      "var(--art) 3 3 4 3 fill / calc(var(--px) * 3) calc(var(--px) * 3) calc(var(--px) * 4) repeat",
    );
    expect(drawn.get("border-width")).toBe("calc(var(--px) * 3) calc(var(--px) * 3) calc(var(--px) * 4)");
    expect(drawn.get("image-rendering")).toBe("pixelated");
    // Under the picture is an edge of ink and the ground of a button, for a picture that has not come.
    expect([drawn.get("border-color"), drawn.get("background")]).toEqual(["var(--ink)", "var(--page) padding-box"]);
    expect(drawn.get("color")).toBe("var(--ink)");
  });

  test("test_on_a_narrow_screen_a_link_is_a_label_so_that_the_board_is_one_line", () => {
    // Buttons and the name were wider than a phone. There a link is its words, in the
    // colour of a link and underlined, and the board is as high as one control.
    const always = sets(of(".link", null));

    expect(always.has("border-image")).toBe(false);
    expect(always.has("border-width")).toBe(false);
    expect(always.get("color")).toBe("var(--accent)");
    // What draws a link as a button is under the width from which there is room, and nowhere
    // else, but where the header is handed the other way to draw a narrow screen.
    const pictured = RULES.filter((rule) => [...rule.sets.values()].some((value) => /var\(--art(-down)?\)/.test(value)));
    expect(pictured.length).toBeGreaterThan(0);
    expect(pictured.filter((rule) => !ROOMY.test(rule.under ?? "") && !rule.selector.includes(OTHER_WAY)).map((rule) => rule.selector)).toEqual([]);
    expect(NARROW.test(RULES.map((rule) => rule.under ?? "").join(" "))).toBe(true);
    // Left to itself the header draws labels, and says so on its board.
    render(<SiteHeader />);
    expect(screen.getByRole("banner").firstElementChild).toHaveAttribute("data-narrow", "labels");
  });

  test("test_the_header_may_be_handed_the_other_way_to_draw_a_narrow_screen_with_its_links_as_buttons", () => {
    render(<SiteHeader narrow="keys" />);
    const otherWay = RULES.filter((rule) => rule.selector.includes(OTHER_WAY) && !FORCED.test(rule.under ?? ""));
    const link = sets(otherWay.filter((rule) => rule.selector === `${OTHER_WAY} .link`));

    expect(screen.getByRole("banner").firstElementChild).toHaveAttribute("data-narrow", "keys");
    // It changes nothing of what the header holds or says: the same four links, in their order.
    expect(within(screen.getByRole("banner")).getAllByRole("link").map((one) => one.textContent)).toEqual([
      SITE.name,
      SITE.nav.vibes,
      SITE.nav.methods,
      SITE.nav.sources,
    ]);
    // It is for a narrow screen and no other: on a wide one the links are buttons whatever is handed.
    expect(otherWay.length).toBeGreaterThan(3);
    expect(otherWay.filter((rule) => !NARROW.test(rule.under ?? "")).map((rule) => rule.selector)).toEqual([]);
    // A button there is the button of a wide screen, cut and laid the same way.
    const wide = sets(of(".link", ROOMY));
    for (const property of ["border-image", "border-width", "border-color", "background", "color", "image-rendering"]) {
      expect([property, link.get(property)]).toEqual([property, wide.get(property)]);
    }
    // The three have a line of their own under the name, so the board is two lines high.
    expect(sets(otherWay.filter((rule) => rule.selector === `${OTHER_WAY} .links`)).get("flex")).toBe("1 0 100%");
  });

  test("test_no_control_of_the_board_lies_over_another_where_the_links_go_under_the_name", () => {
    // Seen in a browser 320 wide: the links went under the name, and the foot of the name
    // lay over the head of the first link, because each line lies over the room of the
    // rules of the box. So two lines stand as far apart as both lie over.
    const board = sets(of(".inner", null));

    expect(board.get("--lies-over")).toBe("calc(var(--px) * -2)");
    expect(board.get("flex-wrap")).toBe("wrap");
    expect(board.get("gap")).toBe("calc(var(--lies-over) * -2) var(--space-1)");
    for (const part of [".name", ".links"]) {
      const margins = sets(of(part, null));
      expect([part, margins.get("margin-block") ?? margins.get("margin")]).toEqual([
        part,
        part === ".name" ? "var(--lies-over)" : "var(--lies-over) 0",
      ]);
    }
    // Where a link is a button the line lies over nothing: a length of nought, which a sum can be made of.
    expect(sets(of(".inner", ROOMY)).get("--lies-over")).toBe("0px");
  });

  test("test_once_a_search_is_open_the_board_of_a_narrow_screen_is_lower_and_its_controls_are_as_high_as_they_were", () => {
    // Measured on a phone 390 wide, with every part dressed: the first result ended 150 px
    // under the foot of the first screen. What stands over the answer gives way: the room
    // between two boxes, the height of a chip, and then the height of the name board. Its
    // line lies one art pixel further over the room of its rules, above and below, so the
    // board is 52 px where it was 56, and every control of it is 44 px high as it was.
    const lower = RULES.filter((rule) => rule.selector === ':global(body):has([data-search="open"]) .inner[data-narrow="labels"]');

    expect(lower.map((rule) => [rule.under, [...rule.sets]])).toEqual([
      ["@media (max-width: 40rem)", [["--lies-over", "calc(var(--px) * -3)"]]],
    ]);
    // It lies over the room of the rules and never past the box: the rule at the top is
    // four art pixels wide, and the line lies over three of them.
    const wide = (asWritten()["--frame-box-cut"] ?? "").split(" ").map(Number);
    expect(Math.min(wide[0] ?? 0, wide[2] ?? 0)).toBeGreaterThan(3);
    // No height is set on a control or on the board: a control is as high as a main control is.
    expect(RULES.filter((rule) => /max-width:\s*40rem/.test(rule.under ?? "") && [...rule.sets.keys()].some((property) => /^(min-|max-)?height$/.test(property))).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_page_being_read_is_amber_with_an_edge_of_ink_and_says_so", () => {
    pathname = "/sources";
    render(<SiteHeader />);
    const here = screen.getByRole("link", { name: SITE.nav.sources });
    const other = screen.getByRole("link", { name: SITE.nav.vibes });

    expect(here).toHaveAttribute("aria-current", "page");
    expect(other).not.toHaveAttribute("aria-current");
    // As a button it is the button of what is on, and pressed it is that button pressed.
    expect([drawingOf(here, "--art"), drawingOf(here, "--art-down")]).toEqual(["ui-button-on", "ui-button-on-down"]);
    expect([drawingOf(other, "--art"), drawingOf(other, "--art-down")]).toEqual(["ui-button", "ui-button-down"]);
    // As a label it stands on a plate of amber inside a rule of ink: amber is not told from cream.
    const plate = sets(of('.link[aria-current="page"]', null));
    expect(plate.get("color")).toBe("var(--on-chosen)");
    expect(plate.get("background")).toContain("var(--chosen)");
    expect(plate.get("background")).toContain("var(--border)");
    expect(sets(of('.link[aria-current="page"]', ROOMY)).get("background")).toBe("var(--chosen) padding-box");
  });

  test("test_a_press_changes_the_picture_of_a_link_and_moves_nothing", () => {
    const pressed = RULES.filter((rule) => /:active\b/.test(rule.selector) && !FORCED.test(rule.under ?? ""));

    expect(pressed.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [`${OTHER_WAY} .link:active`, [["border-image-source", "var(--art-down)"]]],
      [".link:active", [["border-image-source", "var(--art-down)"]]],
    ]);
    // It is a button only where there is room, or where the header is handed the other way:
    // so only there has it a picture to change.
    expect(pressed.map((rule) => (ROOMY.test(rule.under ?? "") ? "wide" : "narrow"))).toEqual(["narrow", "wide"]);
  });

  test("test_where_the_system_draws_in_its_own_colours_no_picture_is_laid_over_them", () => {
    const forced = RULES.filter((rule) => FORCED.test(rule.under ?? ""));

    expect(forced.filter((rule) => /^\.link\b/.test(rule.selector)).map((rule) => rule.sets.get("border-image-source"))).toEqual(
      expect.arrayContaining(["none"]),
    );
    // A picture is taken away by its source: written whole, the build makes nothing of it.
    expect(RULES.filter((rule) => (rule.sets.get("border-image") ?? "").trim() === "none")).toEqual([]);
  });

  test("test_the_header_has_no_accessibility_fault", async () => {
    pathname = "/vibes";
    const { container } = render(<SiteHeader burro="nowhere" />);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("Burro in the name board", () => {
  const WIDE = /min-width:\s*60rem/;
  const UNDER_WIDE = /max-width:\s*59\.99rem/;
  const his = () => [...screen.getByRole("banner").querySelectorAll<HTMLElement>("[data-pose]")];
  const names = () => within(screen.getByRole("banner")).getAllByRole("link").map((link) => link.textContent);
  const FOUR = [SITE.name, SITE.nav.vibes, SITE.nav.methods, SITE.nav.sources];
  /** Every rule that lays him out or draws him, whatever it is under. */
  const OF_HIM = RULES.filter((rule) => /\.burro\b/.test(rule.selector));

  test("test_left_to_itself_the_board_draws_him_beside_the_name_so_that_he_is_on_every_page", () => {
    // A person who walked the website asked for him to be always moving, and found him on
    // one page in three states and on no other. The board is on every page: so the look
    // says that he is in it.
    expect(BURRO_IN_THE_BOARD).toBe("beside-the-name");
    render(<SiteHeader />);
    const board = screen.getByRole("banner").firstElementChild as HTMLElement;

    expect(his()).toHaveLength(1);
    expect(his()[0]).toHaveAttribute("data-pose", "sits");
    expect([...board.children].map((one) => one.tagName)).toEqual(["A", "SPAN", "NAV"]);
    // Nothing stands by him to be pressed: the board holds its links and no button.
    expect(within(board).queryByRole("button")).toBeNull();
    expect(names()).toEqual(FOUR);
  });

  test("test_one_line_takes_him_out_of_the_board_which_then_holds_what_it_held", () => {
    render(<SiteHeader burro="nowhere" />);
    const board = screen.getByRole("banner").firstElementChild as HTMLElement;

    expect(his()).toEqual([]);
    expect(within(board).queryByRole("button")).toBeNull();
    expect(names()).toEqual(FOUR);
    // The name and the three are what the board holds, and nothing stands between the board and either.
    expect([...board.children].map((one) => one.tagName)).toEqual(["A", "NAV"]);
    expect(board.firstElementChild).toBe(within(board).getByRole("link", { name: SITE.name }));
  });

  test("test_he_is_drawn_beside_the_name_from_his_back_up_and_nothing_of_him_is_heard_or_pressed", () => {
    render(<SiteHeader burro="beside-the-name" />);
    const board = screen.getByRole("banner").firstElementChild as HTMLElement;
    const [he, ...others] = his();
    const name = within(board).getByRole("link", { name: SITE.name });

    expect(others).toEqual([]);
    expect([he?.getAttribute("data-pose"), he?.getAttribute("data-peeps"), he?.getAttribute("data-stage")]).toEqual(["sits", "true", "false"]);
    // The name comes first, as it did: the shell sets the first thing the board holds in
    // the face of names. He stands after it, and the three pages after him.
    expect([...board.children].map((one) => one.tagName)).toEqual(["A", "SPAN", "NAV"]);
    expect(board.firstElementChild).toBe(name);
    expect(he?.parentElement).toBe(board.children[1]);
    // He is no part of the name: a press on him leads nowhere, and the name is the name alone.
    expect(he?.closest("a")).toBeNull();
    expect(name.textContent).toBe(SITE.name);
    expect(names()).toEqual(FOUR);
    // He stirs there, and nothing stops him but what a person has set in their system: no
    // button stands by him, and a keyboard comes to the name and then to the pages.
    expect(he?.querySelector("[data-moves]")).toHaveAttribute("data-moves", "true");
    expect(within(board).queryByRole("button")).toBeNull();
    const reached = [...board.querySelectorAll("a, button, input, [tabindex]")].map((one) => one.getAttribute("aria-label") ?? one.textContent);
    expect(reached).toEqual(FOUR);
    // The whole of him is kept from a screen reader: the board is heard as it was without him.
    expect(he?.textContent).toBe("");
    expect(he).toHaveAttribute("aria-hidden", "true");
  });

  test("test_he_sits_on_the_rule_at_the_foot_of_the_board_and_the_board_is_no_higher_for_him", () => {
    const roomy = sets(of(".burro", ROOMY));

    // The line of the board is as high as a control. He is higher than that on a wide
    // screen, so he lies over the room of the board above the line and under it, and takes
    // none of his own: the board is as high with him as without him. Measured in a browser
    // at thirteen widths from 320 to 1440: the board, the name, its pages, the page and
    // the foot each stood where they stood without him, to the tenth of a pixel.
    expect(roomy.get("align-self")).toBe("flex-end");
    expect(roomy.get("margin-block-start")).toBe("calc(var(--under) * -1)");
    // Under the line are the room of the board and one art pixel of page, and then its rule: he sits on the rule.
    expect(roomy.get("margin-block-end")).toBe("calc((var(--under) + var(--px)) * -1)");
    expect([roomy.get("--under"), sets(of(".burro", WIDE)).get("--under")]).toEqual(["var(--space-1)", "var(--space-2)"]);
    // Which is the room the board keeps under its line, on each screen.
    expect(sets(of(".inner", ROOMY)).get("padding")).toBe("var(--space-1) var(--space-3)");
    expect(sets(of(".inner", WIDE)).get("padding")).toBe("var(--space-2) var(--space-4)");
    // No height is set for him, and none on the board: he is as large as he is drawn.
    const sized = OF_HIM.filter((rule) => [...rule.sets.keys()].some((property) => /^((min|max)-)?(width|height)$/.test(property)));
    expect(sized.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_on_a_narrow_screen_the_board_is_one_line_with_no_room_for_him_and_he_is_not_drawn_in_it", () => {
    // Measured on a phone 390 wide, while the board held four links: they and the name left
    // 15 px of the line, and he is 48 wide. With three it has the room, and he is drawn over
    // the foot all the same: a second line would stand the first result of a search lower
    // at a narrower width, and the answer comes first.
    expect(BURRO_ON_A_NARROW_SCREEN).toBe("over-the-foot");
    expect([boardOnANarrowScreen(), overTheFoot()]).toEqual(["labels", true]);
    expect([...sets(of(".burro", null))]).toEqual([["display", "none"]]);
    expect(sets(of(".burro", ROOMY)).get("display")).toBe("block");
    render(<SiteHeader />);
    expect(screen.getByRole("banner").firstElementChild).toHaveAttribute("data-narrow", "labels");
    // Under 40rem nothing draws him in a board of one line: what does is of the board of two.
    const narrow = OF_HIM.filter((rule) => NARROW.test(rule.under ?? "") && rule.sets.get("display") === "block");
    expect(narrow.map((rule) => rule.selector)).toEqual([`${OTHER_WAY} .burro`]);
  });

  test("test_one_line_draws_him_in_the_board_of_a_narrow_screen_too_which_is_then_two_lines", () => {
    // The other way, for the founder to choose: he is at the head of every page of a phone,
    // and everything under the board stands lower by the height of a line.
    expect(boardOnANarrowScreen("beside-the-name", "in-the-board")).toBe("keys");
    expect(overTheFoot("beside-the-name", "in-the-board")).toBe(false);
    // Taken out of the board, he is over no foot and the board of a phone is one line.
    expect([boardOnANarrowScreen("nowhere", "in-the-board"), overTheFoot("nowhere", "over-the-foot")]).toEqual(["labels", false]);
    expect([boardOnANarrowScreen("beside-the-name", "nowhere"), overTheFoot("beside-the-name", "nowhere")]).toEqual(["labels", false]);

    render(<SiteHeader narrow="keys" />);
    expect(his()).toHaveLength(1);
    const drawn = sets(of(`${OTHER_WAY} .burro`, NARROW));
    // He sits beside the name, behind the row of the three pages, and lies over the room
    // between the two lines: the board of two lines is as high with him as without him.
    expect([...drawn]).toEqual([
      ["display", "block"],
      ["align-self", "flex-end"],
      ["margin-block-end", "calc(var(--space-1) * -1)"],
    ]);
    expect(sets(of(OTHER_WAY, NARROW)).get("gap")).toBe("var(--space-1)");
  });

  test("test_he_stands_with_the_name_at_the_start_of_the_board_and_the_three_pages_at_its_end", () => {
    // The board parts what it holds to its two ends. With him in it there are three things
    // and not two: so the pages take all the room that is left before them, whether he is
    // laid out or not.
    expect(sets(of(".inner", null)).get("justify-content")).toBe("space-between");
    expect([...sets(of(".burro + nav", ROOMY))]).toEqual([["margin-inline-start", "auto"]]);
  });

  test("test_where_he_is_drawn_on_the_page_he_is_not_drawn_in_the_board_as_well_and_nothing_of_him_runs_unseen", () => {
    // He is one rabbit. Before a search he sits beside the heading, and while a search is
    // read he hops where the answer will stand: he is then not in the board. He is not
    // laid out there at all. Hidden and kept in his place he went on stirring where nobody
    // saw him: seen in a browser, fourteen movements ran on the first page where seven were
    // in sight.
    const gone = OF_HIM.filter((rule) => /:has\(main\b/.test(rule.selector));

    expect(gone.map((rule) => [rule.under, rule.selector, [...rule.sets]])).toEqual([
      ["@media (min-width: 60rem)", ":global(body):has(main [data-pose]) .inner > .burro", [["display", "none"]]],
      [
        "@media (max-width: 59.99rem)",
        ':global(body):has(main :not([data-room="wide"]) > [data-pose]) .inner > .burro',
        [["display", "none"]],
      ],
    ]);
    expect(UNDER_WIDE.test(gone[1]?.under ?? "")).toBe(true);
    // Nothing hides him and keeps his room: what is not drawn of him is not laid out.
    expect(OF_HIM.filter((rule) => rule.sets.has("visibility") || rule.sets.has("opacity")).map((rule) => rule.selector)).toEqual([]);
    // It weighs more than whatever draws him, in a board of one line or of two.
    expect(gone.every((rule) => rule.selector.includes(".inner > .burro"))).toBe(true);
  });

  test("test_the_board_knows_a_rabbit_that_is_in_the_page_and_not_drawn_by_what_holds_him_there", () => {
    // Where he asked and no offer was in sight, what held him was drawn only where there
    // was room: it said `data-room="wide"`, and its own sheet drew it from 60rem. Under that
    // he was in the page and was not seen, and the board drew him. Burro asks nothing now,
    // and what held him there is gone with its sheet. The page holds him beside its heading
    // and where a search is read, and draws him wherever it holds him: so the board knows
    // of no rabbit that is in the page and is not drawn, and there is none. If a part comes
    // to hold him where it does not draw him, the board must be told of it: this fails.
    const source = path.join(__dirname, "..", "..");
    const written = (readdirSync(source, { recursive: true }) as string[])
      .map((file) => file.split(path.sep).join("/"))
      .filter((file) => /\.(tsx?|css)$/.test(file) && !/\.test\.tsx?$/.test(file))
      .sort()
      .map((file) => ({ file, text: readFileSync(path.join(source, file), "utf8") }));
    // What every page stands in and the part of the kit that draws him are not the page's.
    const ofAPage = written.filter(({ file }) => !/^components\/(SiteHeader|SiteFooter|kit\/Burro)\//.test(file));
    expect(written.length).toBeGreaterThan(ofAPage.length);

    // Two parts of the page draw him, and both are of the search page.
    const draw = ofAPage.filter(({ file, text }) => file.endsWith(".tsx") && /<Burro\b/.test(text));
    expect(draw.map(({ file }) => file)).toEqual(["components/SearchApp/SearchApp.tsx", "components/SearchApp/Wait.tsx"]);
    // No part says that what holds him is drawn only where there is room for him.
    expect(ofAPage.filter(({ text }) => /data-room[^\n]*\bwide\b/.test(text)).map(({ file }) => file)).toEqual([]);
    // A sheet of the page names him where it says where he lies and how large he is drawn,
    // and in naming him names what holds him there.
    const sheets = ofAPage.filter(({ file }) => file.endsWith(".css")).flatMap(({ file, text }) => rulesOf(text).map((rule) => ({ file, ...rule })));
    const ofHim = sheets.filter((rule) => /\[data-pose\b/.test(rule.selector));
    const holds = ofHim.map(({ file, selector }) => ({ file, part: /\.([\w-]+)\s*>\s*\[data-pose\b/.exec(selector)?.[1] ?? "" }));
    expect(ofHim.map((rule, at) => [rule.file, rule.selector, holds[at]?.part])).toEqual([
      ["components/SearchApp/SearchApp.module.css", '.search[data-open="false"] .head > [data-pose]', "head"],
      ["components/SearchApp/Wait.module.css", ".meadow > [data-pose]", "meadow"],
    ]);
    // Every rule that says whether he is drawn, or whether what holds him is: each of the
    // two that hold him is laid out in a grid, always, and nothing takes either from sight.
    const SEEN = ["display", "visibility", "content-visibility", "opacity", "clip", "clip-path"];
    const drawnBy = sheets.filter(
      (rule) =>
        SEEN.some((property) => rule.sets.has(property)) &&
        (ofHim.includes(rule) || holds.some(({ file, part }) => file === rule.file && isFor(rule.selector, part))),
    );
    expect(drawnBy.map((rule) => [rule.file, rule.under, rule.selector, SEEN.flatMap((property) => rule.sets.get(property) ?? [])])).toEqual([
      ["components/SearchApp/SearchApp.module.css", null, ".head", ["grid"]],
      ["components/SearchApp/Wait.module.css", null, ".meadow", ["grid"]],
    ]);
  });

  test("test_the_board_has_no_accessibility_fault_with_him_in_it", async () => {
    const { container } = render(<SiteHeader />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
