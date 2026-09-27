/** @jest-environment node */
/**
 * What a browser showed of the layout, held in the style sheets. jsdom lays
 * nothing out, so a test of layout reads the styles: `support/css.ts`.
 *
 * Each test here is of something seen in a browser that no test had caught.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { HEIGHT_OF_THE_BAR } from "@/components/SearchApp/bar";

import { asWritten, writtenForAWideScreen, type Theme } from "./support/contrast";
import { isFor, rulesOf, subjectOf, weightOf, type Rule } from "./support/css";

const SRC = path.resolve(__dirname, "..", "src");
const DRAWINGS = path.resolve(__dirname, "..", "art");

type Found = Rule & { readonly file: string };

/** Every rule of every style sheet of the website, with the file it is in. */
function everyRule(folder = SRC): Found[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry): Found[] => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return everyRule(file);
    if (!entry.name.endsWith(".css")) return [];
    return rulesOf(readFileSync(file, "utf8")).map((rule) => ({ ...rule, file: path.relative(SRC, file) }));
  });
}

const RULES = everyRule();
const sheet = (file: string) => RULES.filter((rule) => rule.file === file);
const where = (rule: Found) => `${rule.file}: ${rule.selector}`;

/** The tokens as a phone has them, and as a wide screen has them. */
const NARROW: Theme = asWritten();
const WIDE: Theme = { ...NARROW, ...writtenForAWideScreen() };

/** A value parted where it has a gap or a comma that is not inside brackets. */
function partsOf(value: string, at: " " | ","): string[] {
  const found: string[] = [];
  let depth = 0;
  let from = 0;
  [...value].forEach((character, index) => {
    if (character === "(") depth += 1;
    if (character === ")") depth -= 1;
    if (character === at && depth === 0) {
      found.push(value.slice(from, index));
      from = index + 1;
    }
  });
  found.push(value.slice(from));
  return found.map((part) => part.trim()).filter(Boolean);
}

/**
 * How many pixels of the screen a length comes to, where it is written as a figure, as a
 * token, or as a count of art pixels. Anything else is no length that can be held to a rule.
 */
function pixelsOf(length: string, tokens: Theme): number {
  const text = length.trim();
  if (text === "0") return 0;
  const figure = /^(-?\d+(?:\.\d+)?)px$/.exec(text);
  if (figure) return Number(figure[1]);
  const named = /^var\((--[a-z0-9-]+)\)$/.exec(text);
  if (named) return pixelsOf(tokens[named[1] ?? ""] ?? "not given", tokens);
  const times = /^calc\((.+) \* (-?\d+(?:\.\d+)?)\)$/.exec(text);
  if (times) return pixelsOf(times[1] ?? "", tokens) * Number(times[2]);
  return Number.NaN;
}

/** How far the hard shadow of the look falls, to the right and down. */
function shadowOf(tokens: Theme): { right: number; down: number } {
  const [right = "", down = ""] = partsOf(tokens["--box-shadow"] ?? "", " ");
  return { right: pixelsOf(right, tokens), down: pixelsOf(down, tokens) };
}

const scrolls = (rule: Rule) =>
  ["overflow", "overflow-x", "overflow-y"].some((property) =>
    /\b(auto|scroll)\b/.test(rule.sets.get(property) ?? ""),
  );

/**
 * A drawing of the website, by name: its rows, a character a pixel, which characters are
 * clear, and what it says of itself on the lines before its first row.
 */
function drawingOf(name: string): { rows: string[]; clear: Set<string>; notes: string[] } | null {
  for (const file of existsSync(DRAWINGS) ? readdirSync(DRAWINGS).filter((one) => one.endsWith(".sprite.txt")) : []) {
    const lines = readFileSync(path.join(DRAWINGS, file), "utf8").split("\n");
    const from = lines.findIndex((line) => line.startsWith("==") && line.slice(2).trim() === name);
    if (from < 0) continue;
    const palette = lines.slice(0, lines.findIndex((line) => line.startsWith("==")));
    const clear = new Set(palette.filter((line) => /^\S (transparent|clear)\s*$/.test(line.trim())).map((line) => line.trim().charAt(0)));
    const until = lines.findIndex((line, at) => at > from && line.startsWith("=="));
    const own = lines.slice(from + 1, until < 0 ? undefined : until).filter((line) => line.trim() !== "");
    return { rows: own.filter((line) => !line.startsWith("# ")), clear, notes: own.filter((line) => line.startsWith("# ")) };
  }
  return null;
}

describe("what every page has before a part is dressed", () => {
  const base = sheet("styles/base.css");
  /** What the base says of an element, by a property, wherever it says it. */
  const said = (selector: string, property: string) =>
    base.filter((rule) => rule.selector === selector).flatMap((rule) => rule.sets.get(property) ?? []);

  test("test_the_ground_is_a_meadow_and_what_is_read_stands_on_cream", () => {
    // Nothing is read on the grass. What a page says is in `main`, and `main` brings the
    // cream that is read on.
    const read = base.filter((rule) => /\bmain\b/.test(rule.selector) && rule.sets.has("background"));

    expect(said("body", "color")).toEqual(["var(--text)"]);
    expect(read.map((rule) => [rule.selector, rule.sets.get("background")])).toEqual([[":where(main)", "var(--bg)"]]);
    // It is a box where no shell makes it one, as on the page for a fault in the layout.
    expect(read.map((rule) => [rule.sets.get("border"), rule.sets.get("box-shadow")])).toEqual([
      ["var(--edge) solid var(--border)", "var(--box-shadow)"],
    ]);
    // It weighs nothing, so that a page which stands boxes of its own on the grass may say otherwise.
    expect(read.map((rule) => weightOf(rule.selector))).toEqual([[0, 0, 0]]);
  });

  test("test_the_meadow_is_laid_in_tiles_sharp_from_edge_to_edge_and_goes_with_the_page", () => {
    // Twelve tiles of sixteen pixels each way: the picture, which is laid again and again.
    const size = "calc(var(--px-ground) * 192)";

    // Under the tiles is the flat ground, which is all there is where `--ground` is `none`.
    expect(said("body", "background")).toEqual(["var(--lea)"]);
    expect(said("body::before", "background")).toEqual([`var(--ground) 0 0 / ${size} ${size}`]);
    expect(said("body::before", "image-rendering")).toEqual(["pixelated"]);
    // How a picture is drawn is handed down, so it is not said of the body: the map is in it.
    expect(said("body", "image-rendering")).toEqual([]);
    // From edge to edge and as high as the page, under everything, and in the way of no press.
    expect(said("body", "position")).toEqual(["relative"]);
    expect([said("body::before", "position"), said("body::before", "inset"), said("body::before", "z-index")]).toEqual([
      ["absolute"],
      ["0"],
      ["-1"],
    ]);
    expect(said("body::before", "pointer-events")).toEqual(["none"]);
    // No style sheet names the picture itself: the token does, so that one line turns it off.
    const naming = RULES.filter((rule) => rule.file !== "styles/tokens.css" && [...rule.sets.values()].some((value) => /\/art\/ground/.test(value)));
    expect(naming.map(where)).toEqual([]);
  });

  test("test_the_browser_does_not_hold_the_page_by_the_ground", () => {
    // Seen on a phone: after the one button of a long sentence the chips grew from two to
    // six, over what had the focus, and all that stood under them went 229 px down the
    // screen, the first result with it. A browser holds what is in sight where it is while
    // what is over it grows, and holds it by the first thing in sight. The ground is the
    // first thing in the page, is always in sight and never moves: held by it, nothing is held.
    expect(said("body::before", "overflow-anchor")).toEqual(["none"]);
    // Nothing else is kept from the browser: what a person reads is what it holds the page by.
    const kept = RULES.filter((rule) => rule.sets.has("overflow-anchor") && rule.selector !== "body::before");
    expect(kept.map(where)).toEqual([]);
  });

  test("test_a_sentence_is_set_in_one_face_and_a_name_in_the_other", () => {
    expect(said("body", "font-family")).toEqual(["var(--font-say)"]);
    for (const heading of ["h1", "h2"]) {
      expect([heading, base.filter((rule) => rule.selector === heading).flatMap((rule) => rule.sets.get("font-family") ?? [])]).toEqual([
        heading,
        ["var(--font-name)"],
      ]);
      // The face of a name has one weight and stands upright. Seen in a browser: one that
      // thickens it, because a part asked for a heavy heading, smears every letter.
      expect([heading, said(heading, "font-weight"), said(heading, "font-synthesis")]).toEqual([heading, ["400"], ["none"]]);
    }
    // No style sheet but the tokens and the base names a face, so that a face is changed in one place.
    const naming = RULES.filter(
      (rule) => !rule.file.startsWith("styles/") && [...rule.sets].some(([property, value]) => /^font(-family)?$/.test(property) && /["']/.test(value)),
    );
    expect(naming.map(where)).toEqual([]);
  });

  test("test_a_heading_is_never_lighter_than_what_it_heads", () => {
    // Seen in a browser: at 20 pixels the face of a name reads as small as a sentence at 13,
    // and a heading set so was lighter to the eye than the label of a field beside it. So the
    // face of a name is set at 30 pixels or more, whatever a part asks for.
    const FROM_THIRTY = /^var\(--(name-[2-4]|size-h[12])\)$/;

    for (const heading of ["h1", "h2"]) {
      expect([heading, said(heading, "font-size").map((size) => FROM_THIRTY.test(size))]).toEqual([heading, [true]]);
      // A part that is not yet dressed asks for the size of a sentence, or of a small
      // heading, by its token. In these two each of those tokens is 30 pixels.
      for (const asked of ["--size-small", "--size-body", "--size-lead", "--size-h3"]) {
        expect([heading, asked, said(heading, asked)]).toEqual([heading, asked, ["var(--name-2)"]]);
      }
    }
    expect([NARROW["--size-h1"], NARROW["--size-h2"]].map((size) => FROM_THIRTY.test(size ?? ""))).toEqual([true, true]);
    expect([WIDE["--size-h1"], WIDE["--size-h2"]].map((size) => FROM_THIRTY.test(size ?? ""))).toEqual([true, true]);

    // Seen in a browser, the other way: a small heading at 30 pixels stood over its sentence
    // like a shout, and the first result no longer stood whole on the first screen of a
    // phone. So a small heading is set in the face of a sentence, heavy, at the size asked.
    for (const heading of ["h3", "h4"]) {
      expect([heading, said(heading, "font-family"), said(heading, "font-weight")]).toEqual([heading, ["var(--font-say)"], ["700"]]);
      for (const asked of ["--size-small", "--size-body", "--size-lead", "--size-h3"]) {
        expect([heading, asked, said(heading, asked)]).toEqual([heading, asked, []]);
      }
    }
    // It is no smaller than the sentence under it.
    expect([said("h3", "font-size"), said("h4", "font-size")]).toEqual([["var(--size-h3)"], ["var(--size-lead)"]]);
    expect([NARROW["--size-h3"], NARROW["--size-lead"]]).toEqual(["1.25rem", "1.0625rem"]);
    expect(Object.keys(writtenForAWideScreen())).not.toContain("--size-h3");
  });

  test("test_a_rule_is_a_hard_line_as_wide_as_a_pixel_of_a_drawing", () => {
    expect(said("hr", "border-block-start")).toEqual(["var(--edge) solid var(--border)"]);
    expect(said("thead th", "border-bottom")).toEqual(["var(--edge) solid var(--text)"]);
    expect(NARROW["--edge"]).toBe("var(--px)");
    // No corner is rounded and nothing is shaded off: the base sets no radius of its own, and
    // no shadow but the ring of the focus and the hard shadow of the look, which has no blur.
    const soft = base.filter((rule) =>
      [...rule.sets].some(
        ([property, value]) =>
          (property === "border-radius" && !/^var\(--radius(-card)?\)$/.test(value)) ||
          (property === "box-shadow" &&
            partsOf(value, ",").some((shadow) => !/^(inset\s+)?0 0 0 /.test(shadow) && !/^(none|var\(--box-shadow\))$/.test(shadow))),
      ),
    );

    expect(soft.map((rule) => rule.selector)).toEqual([]);
    expect(partsOf(NARROW["--box-shadow"] ?? "", " ")[2]).toBe("0");
  });

  test("test_no_edge_and_no_rule_of_the_website_is_dashed_or_dotted", () => {
    // A person who walked the website did not know what a dashed edge was for. It said that
    // a thing was assumed, which the word beside it says. So every edge is whole wherever
    // one is drawn, with forced colours as without: round a chip, a field and what a source
    // opens to, round what holds the place of a chip that is coming, and round a step of a band.
    const broken = RULES.flatMap((rule) =>
      [...rule.sets].filter(([, value]) => /\b(dashed|dotted)\b/.test(value)).map(([property]) => `${where(rule)} sets ${property}`),
    );

    expect(RULES.length).toBeGreaterThan(1000);
    expect(broken).toEqual([]);
    // Nor is an edge drawn in pieces to the same end: taken away, with strokes laid where it
    // stood. The steps of an area that cannot be placed were drawn so, each as its two sides
    // and the ends of its top and its foot.
    const inPieces = RULES.filter(
      (rule) =>
        /\btransparent\b/.test(`${rule.sets.get("border") ?? ""} ${rule.sets.get("border-color") ?? ""}`) &&
        /\bborder-box\b/.test(rule.sets.get("background") ?? ""),
    );
    expect(inPieces.map(where)).toEqual([]);
  });
});

describe("what every page stands in", () => {
  const shell = sheet("components/Shell/Shell.module.css");
  /** What the shell says of a part, by a property, where no condition is set on it. */
  const said = (selector: string, property: string) =>
    shell.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => rule.sets.get(property) ?? []);
  /** The token a part of the shell takes its ground from, as its own style sheet says. */
  const groundOf = (file: string, className: string) =>
    sheet(file)
      .filter((rule) => rule.selector === `.${className}` && rule.under === null)
      .flatMap((rule) => rule.sets.get("background") ?? []);

  test("test_nothing_of_the_shell_is_read_on_the_grass", () => {
    // The banners and the page: each brings cream to be read on.
    const grounds = [
      ...groundOf("components/SyntheticBanner/SyntheticBanner.module.css", "banner"),
      ...groundOf("components/PreviewBanner/PreviewBanner.module.css", "banner"),
      ...said(".main", "background"),
    ];

    expect(grounds).toEqual(["var(--notice-bg)", "var(--notice-bg)", "var(--bg)"]);
    expect([...new Set(grounds)].map((ground) => NARROW[/^var\((--[a-z-]+)\)$/.exec(ground)?.[1] ?? ""])).toEqual([
      "var(--page)",
      "var(--page)",
    ]);
    // The name board and the foot are no strips of cream: each stands in a box of the kit,
    // which is the one child of its landmark and brings the cream it is read on.
    for (const [part, landmark] of [
      ["SiteHeader", "header"],
      ["SiteFooter", "footer"],
    ] as const) {
      const drawn = readFileSync(path.join(SRC, "components", part, `${part}.tsx`), "utf8");
      const held = new RegExp(`<${landmark} className=\\{styles\\.${landmark}\\}>\\s*<Frame kind="box"[^>]*>[\\s\\S]*</Frame>\\s*</${landmark}>`);
      expect([part, held.test(drawn)]).toEqual([part, true]);
      // Its own sheet lays no ground of its own on the landmark or on the box, and cuts
      // nothing off at their edge: a ground laid there would lie over the notch of each
      // corner, and over the grass where the shadow of the box falls.
      const laid = sheet(`components/${part}/${part}.module.css`).filter(
        (rule) => /^\.(header|footer|inner)(\[[^\]]*\])?$/.test(rule.selector) && (rule.sets.has("background") || rule.sets.has("overflow")),
      );
      expect([part, laid.map(where)]).toEqual([part, []]);
    }
    const box = sheet("components/kit/Frame/Frame.module.css").filter((rule) => rule.selector === ".box::before" && rule.under === null);
    expect(box.map((rule) => rule.sets.get("background-color"))).toEqual(["var(--page)"]);
  });

  test("test_a_page_nobody_has_dressed_stands_whole_in_one_box", () => {
    expect(said(".main", "border")).toEqual(["var(--edge) solid var(--border)"]);
    expect(said(".main", "box-shadow")).toEqual(["var(--box-shadow)"]);
    expect(said(".main", "border-image").map((value) => value.startsWith("var(--frame-box) "))).toEqual([true]);
    // The grass shows on either hand, and the box is as wide inside as the page was: what
    // the box takes of its edge and of the room inside it, it is given in width.
    expect(said(".main", "width")).toEqual(["calc(100% - 2 * var(--gutter))"]);
    expect(said(".main", "max-width")).toEqual(["calc(var(--page-width) - 2 * var(--space-4) + 2 * (var(--room) + var(--edge)))"]);
    expect(said(".main", "padding").map((padding) => partsOf(padding, " ")[1])).toEqual(["var(--room)"]);
    // The picture is laid over the room inside the box. What is read stands clear of it.
    const wide = partsOf(NARROW["--frame-box-wide"] ?? "", " ").map((length) => pixelsOf(length, NARROW));
    const room = pixelsOf(said(".main", "--room")[0] ?? "", NARROW) + pixelsOf("var(--edge)", NARROW);
    expect(room).toBeGreaterThan(Math.max(...wide.slice(0, 1), ...wide.slice(3)));
  });

  test("test_a_page_that_is_dressed_stands_boxes_of_its_own_on_the_grass", () => {
    const dressed = ".main:has(> [data-dressed])";

    expect([said(dressed, "background"), said(dressed, "border"), said(dressed, "box-shadow")]).toEqual([["none"], ["0"], ["none"]]);
    // The picture of the box is as wide as the tokens say whatever the edge is, so it is taken away by name.
    expect(said(dressed, "border-image-source")).toEqual(["none"]);
    // It keeps the grass at either hand, and is as wide as the page was.
    expect(said(dressed, "max-width")).toEqual(["calc(var(--page-width) - 2 * var(--space-4) + 2 * var(--gutter))"]);
    expect(said(dressed, "width")).toEqual([]);
  });

  test("test_the_page_of_a_fault_in_the_layout_is_laid_out_by_the_sheet_of_the_shell_and_has_none_of_its_own", () => {
    // The framework has every page fetch ahead what the page of a fault in the layout is
    // drawn with. A sheet of its own was fetched by every page and laid by none, and the
    // browser said so in the console of each. The sheet of the shell is laid by every page.
    const app = path.join(SRC, "app");
    expect(readdirSync(app).filter((name) => name.endsWith(".css"))).toEqual([]);
    expect(/\.css"/.test(readFileSync(path.join(app, "global-error.tsx"), "utf8").replace(/^import "@\/styles\/(tokens|base)\.css";$/gm, ""))).toBe(false);
    // It has no shell, so it takes the width of the shell and its grass at either hand for
    // itself. What it says stands in a box of its own, so no box is drawn round that one.
    const alone = ".alone";
    expect(said(alone, "width")).toEqual(said(".main", "width"));
    expect(said(alone, "max-width")).toEqual(said(".main:has(> [data-dressed])", "max-width"));
    expect([said(alone, "background"), said(alone, "border"), said(alone, "box-shadow")]).toEqual([["none"], ["0"], ["none"]]);
  });

  test("test_a_banner_is_cream_with_its_words_in_ink_and_an_edge_of_amber_over_a_rule_of_ink", () => {
    for (const file of ["components/SyntheticBanner/SyntheticBanner.module.css", "components/PreviewBanner/PreviewBanner.module.css"]) {
      const banner = sheet(file).filter((rule) => rule.selector === ".banner" && rule.under === null);
      expect([file, banner.map((rule) => [rule.sets.get("color"), rule.sets.get("border-block-end")])]).toEqual([
        file,
        [["var(--notice-text)", "2px solid var(--notice-edge)"]],
      ]);
    }
    expect([NARROW["--notice-bg"], NARROW["--notice-text"], NARROW["--notice-edge"], NARROW["--notice-mark"]]).toEqual([
      "var(--page)",
      "var(--ink)",
      "var(--ink)",
      "var(--amber)",
    ]);
    // The band is drawn inside the banner and takes no room: a banner is as high as it was,
    // but for its rule, which is one art pixel.
    expect(said(".shell > section", "box-shadow")).toEqual(["inset 0 calc(var(--px) * -2) 0 var(--notice-mark)"]);
    expect(said(".shell > section", "border-block-end-width")).toEqual(["var(--edge)"]);
    expect(shell.filter((rule) => rule.selector === ".shell > section").flatMap((rule) => [...rule.sets.keys()])).toEqual([
      "border-block-end-width",
      "box-shadow",
      "box-shadow",
    ]);
  });

  test("test_the_name_of_the_website_is_set_in_the_face_of_names_and_the_header_is_no_higher_for_it", () => {
    const name = ".shell > header > div > a:first-child";

    expect([said(name, "font-family"), said(name, "font-size"), said(name, "font-weight"), said(name, "font-synthesis")]).toEqual([
      ["var(--font-name)"],
      ["var(--name-2)"],
      ["400"],
      ["none"],
    ]);
    // The name is a target, which is 44 pixels high. At one line of 30 it is inside it.
    expect(said(name, "line-height")).toEqual(["1"]);
    expect(parseFloat(NARROW["--name-2"] ?? "") * 16).toBeLessThan(parseInt(NARROW["--target"] ?? "", 10));
  });
});

describe("a box that scrolls", () => {
  test("test_what_is_hidden_inside_a_box_that_scrolls_cannot_make_the_page_wider", () => {
    // Seen on a phone: the table of every area scrolled inside its own box, and the page
    // scrolled sideways as well. A name kept for a screen reader is laid out `absolute`. In a
    // box that scrolls and is not itself positioned, it is laid out against the page, is not
    // cut off with the rest, and the page grows to hold it.
    const boxes = RULES.filter(scrolls);
    const loose = boxes.filter(
      (rule) => !/^(relative|absolute|sticky|fixed)$/.test(rule.sets.get("position") ?? ""),
    );

    expect(boxes.some((rule) => isFor(rule.selector, "scroll-x"))).toBe(true);
    expect(loose.map((rule) => `${rule.file}: ${rule.selector}`)).toEqual([]);
  });
});

describe("the keys that move the map", () => {
  test("test_a_screen_with_no_keyboard_is_not_told_to_use_the_arrow_keys", () => {
    // Seen on a phone: "Use the arrow keys to move the map", where there are no keys.
    const keys = sheet("components/MapView/MapView.module.css").filter((rule) => isFor(rule.selector, "keys"));
    const onTouch = keys.filter((rule) => /hover:\s*none/.test(rule.under ?? "") && /pointer:\s*coarse/.test(rule.under ?? ""));

    expect(onTouch.map((rule) => rule.sets.get("display"))).toEqual(["none"]);
    // Where there may be a keyboard, the line is drawn.
    expect(keys.filter((rule) => rule.under === null && rule.sets.get("display") === "none")).toEqual([]);
  });
});

describe("the links of an area's page", () => {
  test("test_two_small_links_one_under_the_other_have_the_space_between_them_the_design_asks", () => {
    // Seen on a phone: the links under "On this page" were 24 pixels high and 4 apart.
    // docs/design/web.md, section 8: 8 pixels between two small targets.
    const lists = sheet("components/AreaProfile/AreaProfile.module.css").filter(
      (rule) => /\.contents\b/.test(rule.selector) && rule.sets.has("gap"),
    );

    expect(lists.length).toBeGreaterThan(0);
    // The first figure of a gap is the space between two rows.
    for (const rule of lists) {
      expect((rule.sets.get("gap") ?? "").split(/\s+/)[0]).toMatch(/^var\(--(target-gap|space-[2-8])\)$/);
    }
  });
});

describe("a sentence and its source", () => {
  const rules = sheet("components/Sentence/Sentence.module.css");
  /** True when the rule is for whatever holds a "Source" button, which is what is laid out beside the sentence. */
  const holdsTheButton = (rule: Rule) => /:has\(\s*>\s*button/.test(subjectOf(rule.selector));

  test("test_opening_a_source_leaves_its_button_where_it_was", () => {
    // Seen in a browser: the button stood to the right of its sentence, and went under it
    // when it was pressed, because what held it was then made as wide as the card.
    const widened = rules.filter((rule) => holdsTheButton(rule) && rule.sets.has("flex-basis"));

    expect(widened.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_what_a_source_opens_goes_under_the_sentence_and_the_button", () => {
    const opened = rules.filter((rule) => /button\[aria-expanded[^\]]*\]\s*\+\s*\S+$/.test(rule.selector.trim()));

    expect(opened.map((rule) => rule.sets.get("flex-basis"))).toEqual(["100%"]);
    // What holds the two is no box of its own, so that each is laid out beside the sentence.
    expect(rules.filter(holdsTheButton).map((rule) => rule.sets.get("display"))).toEqual(["contents"]);
  });
});

describe("what stands between what Burro understood and the first result", () => {
  const SEARCH = rulesOf(readFileSync(path.join(SRC, "components/SearchApp/SearchApp.module.css"), "utf8"));

  test("test_the_line_that_says_which_words_are_selected_takes_no_room_until_it_says_something", () => {
    // Seen on a phone: once every thing Burro noticed was chosen, the first result was still
    // cut off at the foot of the screen. An empty line was held above it, for words that are
    // said only when "Show in the box" is pressed.
    const held = SEARCH.filter((rule) => isFor(rule.selector, "shown") && (rule.sets.has("min-height") || rule.sets.has("height")));

    expect(held.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_on_a_narrow_screen_the_parts_of_an_open_search_stand_closer_and_the_grass_still_shows_between_them", () => {
    // Measured on a phone 390 wide, with every part dressed: the first result ended 150 px
    // under the foot of the first screen, where on the trunk it ended 131 px over it. What
    // stands over the answer gives way, and the room between two boxes is the first to.
    const narrow = SEARCH.filter((rule) => rule.under === "@media (max-width: 40rem)");
    const gapOf = (selector: string) => narrow.filter((rule) => rule.selector === selector).map((rule) => rule.sets.get("gap"));
    const OPEN = '.search[data-open="true"]';

    // Between the box, what Burro asks, the first result and what follows: 8 px of grass.
    expect([gapOf(`${OPEN} .columns`), gapOf(`${OPEN} .form`)]).toEqual([["var(--space-2)"], ["var(--space-2)"]]);
    // In the box, between what Burro says of the search and what he understood: 4 px of cream.
    expect(gapOf(`${OPEN} .says`)).toEqual(["var(--space-1)"]);
    // Before a search nothing stands closer than it did.
    expect(narrow.filter((rule) => rule.sets.has("gap") && !rule.selector.startsWith(OPEN)).map((rule) => rule.selector)).toEqual([]);
    // No two boxes touch: the least of them is as far as the shadow of the look falls, twice over.
    expect(pixelsOf("var(--space-2)", NARROW)).toBe(2 * shadowOf(NARROW).down);
  });

  test("test_that_a_part_was_not_read_and_the_way_to_see_it_are_one_line", () => {
    const line = SEARCH.filter((rule) => isFor(rule.selector, "unread") && rule.under === null);

    expect(line.map((rule) => rule.sets.get("display"))).toContain("flex");
    expect(line.map((rule) => rule.sets.get("flex-wrap"))).toContain("wrap");
    expect(line.map((rule) => rule.sets.get("font-size"))).toContain("var(--size-small)");
  });
});

describe("what stays at the foot of the screen", () => {
  /** The room the page keeps clear at its foot: 176 px. */
  const KEPT = "calc(2 * var(--space-8) + var(--space-7))";
  const SEARCH_PAGE = "components/SearchApp/SearchApp.module.css";
  const WITH_AREAS_CHOSEN = '.search:has(.tray > [data-closed="false"])';
  /** Whatever takes the focus among the space requirements, while they stand in the second way in. */
  const TAKES_THE_FOCUS = '.refine[data-standing="true"] > .fold :is(a, button, input, select, textarea, summary, [tabindex])';
  const held = (selector: string) => sheet(SEARCH_PAGE).filter((rule) => rule.under === null && rule.selector === selector);

  test("test_what_takes_the_focus_is_not_left_under_the_tray_that_sticks", () => {
    // Two things stay at the foot of the screen: the tray of areas to compare, once an area
    // is chosen, and the button that makes a search of the second way in, while its own
    // place is under it. A browser brings what takes the focus into view, and must bring it
    // clear of the tray.
    const sticks = RULES.filter(
      (rule) => rule.sets.get("position") === "sticky" && rule.sets.has("inset-block-end"),
    );
    const page = sheet("styles/base.css").filter((rule) => rule.selector.trim() === "html");

    expect(sticks.map((rule) => [rule.file, rule.selector])).toEqual([
      ["components/CompareTray/CompareTray.module.css", '.tray[data-closed="false"]'],
      [SEARCH_PAGE, ".held"],
    ]);
    expect(sticks.map((rule) => rule.sets.get("inset-block-end"))).toEqual(["0", "0"]);
    // 176 px. The tray was measured at 161 at its highest, on a phone with four areas chosen.
    expect(page.map((rule) => rule.sets.get("scroll-padding-bottom")).filter(Boolean)).toEqual([KEPT]);
    expect(2 * pixelsOf("var(--space-8)", NARROW) + pixelsOf("var(--space-7)", NARROW)).toBe(176);
  });

  test("test_what_takes_the_focus_is_not_left_under_the_button_that_is_held_over_the_space_requirements", () => {
    // Seen in a browser, with areas chosen and the second way in: of 21 things that take
    // the focus by the keyboard, 5 stood under the button at 1440 by 900 and 9 at 390 by
    // 844. The page kept the room of the tray, and the button stands where that room ends.
    expect(held(`${WITH_AREAS_CHOSEN} .held`).map((rule) => rule.sets.get("inset-block-end"))).toEqual([KEPT]);

    // How high the bar of the button is, until the page has measured it: 76 px. With
    // nothing said in it, it was measured at 74 at 1440 by 900 and at 72 at 390 by 844.
    const part = held('.refine[data-standing="true"]').flatMap((rule) => [...rule.sets]);
    expect(part).toEqual([
      ["--bar-high", "calc(var(--space-8) + var(--space-3))"],
      ["--bar-clear", "calc(var(--bar-high) + var(--space-3))"],
    ]);
    expect(pixelsOf("var(--space-8)", NARROW) + pixelsOf("var(--space-3)", NARROW)).toBeGreaterThanOrEqual(74);
    // The page says how high it is by that name, since it grows with what Burro says in it.
    expect(HEIGHT_OF_THE_BAR).toBe("--bar-high");

    // Over the tray, what takes the focus is brought clear of the whole of the bar. Held
    // alone the bar stands in the room the page keeps, and what takes the focus is brought
    // further by what the bar is higher than that room, and never back.
    expect(held(`${WITH_AREAS_CHOSEN} ${TAKES_THE_FOCUS}`).map((rule) => [...rule.sets])).toEqual([
      [["scroll-margin-block-end", "var(--bar-clear)"]],
    ]);
    expect(held(TAKES_THE_FOCUS).map((rule) => [...rule.sets])).toEqual([
      [["scroll-margin-block-end", "max(0px, calc(var(--bar-clear) - 2 * var(--space-8) - var(--space-7)))"]],
    ]);
  });

  test("test_the_tray_takes_no_room_and_does_not_stick_until_an_area_is_chosen", () => {
    const closed = sheet("components/CompareTray/CompareTray.module.css").filter((rule) =>
      /data-closed="true"/.test(rule.selector),
    );

    expect(closed.map((rule) => rule.sets.get("position"))).toEqual(["static"]);
  });
});

describe("a press lands where it was aimed", () => {
  /**
   * What a rule may set when it holds only while an element has the focus, is under the
   * pointer or is being pressed: what is drawn, and never where. None of these moves or
   * resizes anything in the flow of the page. A picture may give way to another of its
   * size, as the picture of a button does to the picture of the button pressed.
   */
  const DRAWN_ONLY = new Set([
    "background",
    "background-color",
    "background-image",
    "border-color",
    "border-image-source",
    "box-shadow",
    "color",
    "cursor",
    "outline",
    "outline-color",
    "outline-offset",
    "text-decoration",
    "text-decoration-thickness",
    "text-underline-offset",
  ]);
  const STATE = /:(focus-within|focus-visible|focus|hover|active)\b/g;
  const statesOf = (selector: string) => [...selector.matchAll(STATE)].map(([, state]) => state ?? "");
  /** True of a selector that holds only with the focus, the pointer or a press, or only without. */
  const comesAndGoes = (selector: string) => statesOf(selector).length > 0;
  /** The element a rule is for, with what is drawn before or after it taken off. */
  const itself = (selector: string) => subjectOf(selector).replace(/::[\w-]+$/, "");
  /** True where the rule is for the very element that has the focus, is under the pointer or is pressed. */
  const isWhatIsPressed = (selector: string) => comesAndGoes(itself(selector)) && itself(selector) === subjectOf(selector);

  /** What takes a press by being what it is. None of these is the face of anything. */
  const TAKES_A_PRESS = /^(a|button|input|label|select|summary|textarea)(?![\w-])|\[role\b/;

  /**
   * The face of a button, under a press: what is inside the button, or drawn before or after
   * it, stepped down and to the right by no more than the shadow is wide, where the system
   * says that movement is welcome. The button is what takes the press, and is not moved.
   *
   * A style sheet says which element is pressed and which is moved, and not what either is.
   * So this holds what a selector can say: that what is moved is not what is pressed, and
   * is no control of the browser's own.
   */
  function isTheFaceSteppingIntoItsShadow(rule: Rule, value: string): boolean {
    const selector = rule.selector;
    const step = /^translate\((.+)\)$/.exec(value.trim());
    if (step === null) return false;
    const [right = "", down = ""] = partsOf(step[1] ?? "", ",");
    const within = [NARROW, WIDE].every((tokens) => {
      const [x, y, shadow] = [pixelsOf(right, tokens), pixelsOf(down, tokens), shadowOf(tokens)];
      return x >= 0 && y >= 0 && x + y > 0 && x <= shadow.right && y <= shadow.down;
    });
    return (
      within &&
      statesOf(selector).every((state) => state === "active") &&
      // While it is pressed, and not while it is not: a face that stands in its shadow at rest steps out of it.
      !/:not\(/.test(selector) &&
      !isWhatIsPressed(selector) &&
      !TAKES_A_PRESS.test(itself(selector)) &&
      /prefers-reduced-motion:\s*no-preference/.test(rule.under ?? "")
    );
  }

  /**
   * A skip link, with the focus: it is laid out `absolute` and kept off the screen until a
   * keyboard reaches it, and is then set down where it is laid out. It is moved over the
   * page, and moves nothing.
   */
  function isASkipLinkSetDown(rule: Rule, value: string, itsSheet: readonly Rule[]): boolean {
    const selector = rule.selector;
    const atRest = itsSheet.filter((other) => other.selector === selector.replace(STATE, "") && other.under === rule.under);
    return (
      value.trim() === "none" &&
      isWhatIsPressed(selector) &&
      statesOf(selector).every((state) => state === "focus" || state === "focus-visible") &&
      atRest.some((other) => other.sets.get("position") === "absolute" && /^translateY\(-/.test(other.sets.get("transform") ?? ""))
    );
  }

  /** What a style sheet sets that moves a thing, or changes the room it takes, as the focus or the pointer comes or goes. */
  function moved(rules: readonly Rule[]): string[] {
    return rules
      .filter((rule) => comesAndGoes(rule.selector))
      .flatMap((rule) =>
        [...rule.sets]
          .filter(
            ([property, value]) =>
              !DRAWN_ONLY.has(property) &&
              !(property === "transform" && (isTheFaceSteppingIntoItsShadow(rule, value) || isASkipLinkSetDown(rule, value, rules))),
          )
          .map(([property]) => `${rule.selector} sets ${property}`),
      );
  }

  const WELCOME = "@media (prefers-reduced-motion: no-preference)";
  /** What a style sheet, written out here, would be refused for. */
  const refusedIn = (css: string) => moved(rulesOf(css));

  test("test_nothing_moves_or_changes_size_because_the_focus_or_the_pointer_came_or_went", () => {
    // Seen in a browser: with the focus the box was three lines high. A press anywhere else
    // took the focus, the box dropped to one line, and everything under it jumped up between
    // the button going down and coming up, so the press landed on nothing. The first press
    // after every typed search was lost.
    const files = [...new Set(RULES.map((rule) => rule.file))];

    expect(RULES.some((rule) => comesAndGoes(rule.selector))).toBe(true);
    expect(files.flatMap((file) => moved(sheet(file)).map((found) => `${file}: ${found}`))).toEqual([]);
  });

  test("test_a_button_that_itself_moves_under_a_press_is_refused", () => {
    // The founder asked for the button of a game: "Pressed, its face steps two pixels down
    // and to the right, into its own shadow." A button that steps is a button that has moved
    // from under the finger by the time the press is let go. So the button stands, and its
    // face steps inside it.
    expect(refusedIn(`${WELCOME} { .button:active { transform: translate(2px, 2px); } }`)).toEqual([".button:active sets transform"]);
    expect(refusedIn(`${WELCOME} { .button:active { translate: 2px 2px; } }`)).toEqual([".button:active sets translate"]);
    expect(refusedIn(`${WELCOME} { button:active, .key:active { transform: translate(var(--px), var(--px)); } }`)).toEqual([
      "button:active sets transform",
      ".key:active sets transform",
    ]);
    for (const room of ["margin-top: 2px", "top: 2px", "padding: 2px 0 0 2px", "border-width: 4px", "inset: 2px auto auto 2px", "scale: 0.98"]) {
      expect(refusedIn(`${WELCOME} { .button:active { ${room}; } }`)).toHaveLength(1);
      expect(refusedIn(`${WELCOME} { .button:active > .face { ${room}; } }`)).toHaveLength(1);
    }
  });

  test("test_the_face_inside_a_button_may_step_into_its_shadow_and_no_further", () => {
    const shadow = [shadowOf(NARROW), shadowOf(WIDE)];

    // Two art pixels down and two to the right, which are four pixels of a phone and six of a desk.
    expect(shadow).toEqual([
      { right: 4, down: 4 },
      { right: 6, down: 6 },
    ]);
    for (const step of ["2px, 2px", "var(--px), var(--px)", "var(--edge), var(--edge)", "calc(var(--px) * 2), calc(var(--px) * 2)", "4px, 4px", "0, 2px"]) {
      expect([step, refusedIn(`${WELCOME} { .button:active > .face { transform: translate(${step}); } }`)]).toEqual([step, []]);
      // What is drawn before or after the button is inside it too.
      expect([step, refusedIn(`${WELCOME} { .button:active::before { transform: translate(${step}); } }`)]).toEqual([step, []]);
    }
    for (const step of ["6px, 6px", "calc(var(--px) * 3), calc(var(--px) * 3)", "-2px, -2px", "0, 0", "2px, 50%", "1em, 1em", "var(--space-2), 0"]) {
      expect([step, refusedIn(`${WELCOME} { .button:active > .face { transform: translate(${step}); } }`)]).toEqual([
        step,
        [".button:active > .face sets transform"],
      ]);
    }
    // What is moved is the face, and no button inside a thing that is pressed with it.
    for (const moved of ["button", "a.link", ".row > input", '[role="button"]', "summary"]) {
      expect(refusedIn(`${WELCOME} { .card:active ${moved} { transform: translate(2px, 2px); } }`)).toHaveLength(1);
    }
    // It steps while the button is pressed, and not back from where it stood while it was not.
    expect(refusedIn(`${WELCOME} { .button:not(:active) > .face { transform: translate(2px, 2px); } }`)).toHaveLength(1);
    // It steps, and does nothing else: it is not turned, made larger or taken away by being made nothing.
    for (const other of ["scale(0)", "scale(0.98)", "rotate(2deg)", "translateY(2px) scale(0.98)", "translate3d(2px, 2px, 0)", "none"]) {
      expect(refusedIn(`${WELCOME} { .button:active > .face { transform: ${other}; } }`)).toEqual([".button:active > .face sets transform"]);
    }
  });

  test("test_the_face_steps_under_a_press_alone_and_only_where_movement_is_welcome", () => {
    const face = "transform: translate(var(--px), var(--px));";

    // Not under the pointer, and not with the focus: those come and go without a press.
    expect(refusedIn(`${WELCOME} { .button:hover > .face { ${face} } }`)).toEqual([".button:hover > .face sets transform"]);
    expect(refusedIn(`${WELCOME} { .button:focus-visible > .face { ${face} } }`)).toEqual([".button:focus-visible > .face sets transform"]);
    expect(refusedIn(`${WELCOME} { .button:hover:active > .face { ${face} } }`)).toEqual([".button:hover:active > .face sets transform"]);
    // Nothing moves unless the system says that movement is welcome.
    expect(refusedIn(`.button:active > .face { ${face} }`)).toEqual([".button:active > .face sets transform"]);
    expect(refusedIn(`@media (min-width: 40rem) { .button:active > .face { ${face} } }`)).toEqual([".button:active > .face sets transform"]);
    expect(refusedIn(`${WELCOME} { @media (min-width: 40rem) { .button:active > .face { ${face} } } }`)).toEqual([]);
  });

  test("test_a_shadow_may_be_taken_away_under_a_press_and_a_picture_may_give_way_to_another", () => {
    expect(refusedIn(".button:active { box-shadow: none; }")).toEqual([]);
    expect(refusedIn(".button:active > .face { box-shadow: none; }")).toEqual([]);
    expect(refusedIn('.button:active > .face { border-image-source: url("/art/pressed.png"); }')).toEqual([]);
    expect(refusedIn('.button:active { background-image: url("/art/pressed.png"); }')).toEqual([]);
    // The picture is changed, and not where it is cut or how wide it is drawn.
    expect(refusedIn('.button:active > .face { border-image: url("/art/pressed.png") 4 / 8px; }')).toHaveLength(1);
    expect(refusedIn(".button:active > .face { border-image-width: 8px; }")).toHaveLength(1);
    expect(refusedIn(".button:active > .face { background-size: 8px 8px; }")).toHaveLength(1);
  });

  test("test_a_skip_link_is_set_down_where_it_is_laid_out_and_nothing_else_is_moved_by_the_focus", () => {
    const skip = ".skip { position: absolute; transform: translateY(-200%); }";

    expect(refusedIn(`${skip} .skip:focus, .skip:focus-visible { transform: none; }`)).toEqual([]);
    // What is in the flow of the page is not moved by the focus, whatever it is called.
    expect(refusedIn(".skip { transform: translateY(-200%); } .skip:focus { transform: none; }")).toEqual([".skip:focus sets transform"]);
    expect(refusedIn(`${skip} .skip:focus { transform: translateY(4px); }`)).toEqual([".skip:focus sets transform"]);
    expect(refusedIn(`${skip} .skip:hover { transform: none; }`)).toEqual([".skip:hover sets transform"]);
    expect(refusedIn(`${skip} .other:focus { transform: none; }`)).toEqual([".other:focus sets transform"]);
  });
});

describe("the look can be turned down in one place", () => {
  /** The layers of a shadow that fall to one side: not a ring, which has no side, and not what is drawn inside. */
  const thrown = (value: string) =>
    partsOf(value, ",").filter((layer) => {
      const [right = "", down = ""] = partsOf(layer, " ");
      return !/^inset\b/.test(layer) && !/^(none|var\(--box-shadow\))$/.test(layer) && !(right === "0" && down === "0");
    });

  test("test_whatever_throws_a_hard_shadow_names_the_shadow_of_the_look_so_that_it_goes_with_it", () => {
    // Set to `none`, the token makes the whole of what names it mean nothing: a list of
    // shadows with `none` among them is no list. So what throws a shadow beside the look's
    // own, as a strip from edge to edge does to its left, loses both.
    const throwing = RULES.filter((rule) => thrown(rule.sets.get("box-shadow") ?? "").length > 0);
    const naming = RULES.filter((rule) => /var\(--box-shadow\)/.test(rule.sets.get("box-shadow") ?? ""));

    expect(naming.length).toBeGreaterThan(0);
    expect(throwing.filter((rule) => !naming.includes(rule)).map(where)).toEqual([]);
    // It is named in a shadow and nowhere else, and never worked on: `calc` of `none` is nothing.
    const misnaming = RULES.filter((rule) =>
      [...rule.sets].some(([property, value]) => property !== "box-shadow" && /var\(--box-shadow\)/.test(value)),
    );
    expect(misnaming.map(where)).toEqual([]);
  });

  test("test_a_box_is_a_plain_edge_of_ink_under_its_picture", () => {
    // The picture of a box is laid over an edge of ink, one art pixel wide. Where the picture
    // is `none`, or has not come, or the system draws in colours of its own, the edge is the box.
    const framed = RULES.filter((rule) => /var\(--frame-box(-on)?\)/.test(rule.sets.get("border-image") ?? ""));
    const FORCED = /forced-colors:\s*active/;

    expect(framed.length).toBeGreaterThan(0);
    for (const rule of framed) {
      expect([where(rule), rule.sets.get("border")]).toEqual([where(rule), "var(--edge) solid var(--border)"]);
      // It is cut and laid as the tokens say, so that a drawing that changes is changed in one place.
      expect([where(rule), rule.sets.get("border-image")]).toEqual([
        where(rule),
        expect.stringMatching(/^var\(--frame-box(-on)?\) var\(--frame-box-cut\)( fill)? \/ var\(--frame-box-wide\) \/ var\(--frame-box-out\) repeat$/),
      ]);
      // The cream is laid inside the edge, so that the grass shows where a corner is notched.
      expect([where(rule), rule.sets.get("background-clip")]).toEqual([where(rule), "padding-box"]);
      expect([where(rule), rule.sets.get("image-rendering")]).toEqual([where(rule), "pixelated"]);
      const forced = RULES.filter((other) => other.file === rule.file && other.selector === rule.selector && FORCED.test(other.under ?? ""));
      expect([where(rule), forced.map((other) => other.sets.get("border-image-source"))]).toEqual([where(rule), ["none"]]);
    }
    // A picture is taken away by its source. Seen in a browser, with the system drawing in
    // colours of its own: the picture of the box was still there. Written as
    // `border-image: none`, the build had made nothing of it.
    const takenAway = RULES.filter((rule) => (rule.sets.get("border-image") ?? "").trim() === "none");
    expect(takenAway.map(where)).toEqual([]);
    // No style sheet names the picture itself.
    const naming = RULES.filter((rule) => rule.file !== "styles/tokens.css" && [...rule.sets.values()].some((value) => /\/art\/frame-box/.test(value)));
    expect(naming.map(where)).toEqual([]);
  });

  test("test_the_shadow_in_the_picture_of_a_box_lies_where_the_shadow_of_the_look_falls", () => {
    // Four numbers, as `border-image-slice` is written: top, right, foot, left.
    const cut = partsOf(NARROW["--frame-box-cut"] ?? "", " ").map(Number);
    const wide = partsOf(NARROW["--frame-box-wide"] ?? "", " ");
    const out = partsOf(NARROW["--frame-box-out"] ?? "", " ");

    expect(cut).toHaveLength(4);
    expect(wide).toEqual(cut.map((pixels) => `calc(var(--px) * ${pixels})`));
    // Its shadow is what the right and the foot have more than the left and the top, and
    // stands out past the box as far as the shadow of the look falls. So a box has one
    // shadow, in one place, with its picture and without.
    const [top = 0, right = 0, foot = 0, left = 0] = cut;
    expect(out.map((length) => pixelsOf(length, NARROW))).toEqual([0, (right - left) * 2, (foot - top) * 2, 0]);
    expect([pixelsOf(out[1] ?? "", NARROW), pixelsOf(out[2] ?? "", NARROW)]).toEqual([shadowOf(NARROW).right, shadowOf(NARROW).down]);
    expect([pixelsOf(out[1] ?? "", WIDE), pixelsOf(out[2] ?? "", WIDE)]).toEqual([shadowOf(WIDE).right, shadowOf(WIDE).down]);
  });

  test("test_every_picture_a_token_names_is_a_drawing_of_the_websites_and_is_laid_as_it_is_drawn", () => {
    // A token names a picture by where it is served. The picture is made from a drawing,
    // which is text: so what the style sheets count on is read from the drawing itself.
    const nameOf = (token: string) => /^url\("\/art\/([a-z0-9-]+)\.png"\)$/.exec(NARROW[token] ?? "")?.[1] ?? `${token} names no picture`;
    const drawn = Object.fromEntries(["--ground", "--frame-box", "--frame-box-on"].map((token) => [token, drawingOf(nameOf(token))]));
    const cut = partsOf(NARROW["--frame-box-cut"] ?? "", " ").map(Number);

    expect(Object.entries(drawn).filter(([, drawing]) => drawing === null).map(([token]) => `${nameOf(token)} is not drawn`)).toEqual([]);

    // The ground is laid at the size it is drawn, and is whole: a pixel left clear would
    // show the flat ground under it, which is paler than the meadow.
    const ground = drawn["--ground"];
    const laid = sheet("styles/base.css")
      .filter((rule) => rule.selector === "body::before")
      .flatMap((rule) => [...(rule.sets.get("background") ?? "").matchAll(/calc\(var\(--px-ground\) \* (\d+)\)/g)].map(([, pixels]) => Number(pixels)));
    expect(laid).toHaveLength(2);
    expect([ground?.rows.length, ...new Set(ground?.rows.map((row) => row.length))]).toEqual(laid);
    expect(ground?.rows.filter((row) => [...row].some((pixel) => ground.clear.has(pixel)))).toEqual([]);

    // A box is cut where its drawing says, on a line of its own before its first row.
    for (const token of ["--frame-box", "--frame-box-on"]) {
      const said = /^# @cut (\d+(?: \d+){0,3})$/m.exec(drawn[token]?.notes.join("\n") ?? "")?.[1]?.split(" ").map(Number) ?? [];
      const [saidTop = 0, saidRight = saidTop, saidFoot = saidTop, saidLeft = saidRight] = said;
      expect([token, [saidTop, saidRight, saidFoot, saidLeft]]).toEqual([token, cut]);
    }
  });
});

describe("what moves", () => {
  const moving = RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition)/.test(property)));
  /**
   * What a rule writes where the length of a movement stands: a figure, or a name. The
   * name of a timing, `--motion-step`, is no length.
   */
  const lengthsOf = (rule: Rule) =>
    ["animation", "animation-duration", "transition", "transition-duration"].flatMap((property) =>
      partsOf(rule.sets.get(property) ?? "", ",").flatMap((one) => partsOf(one, " ").filter((part) => /^(var\(--(?!motion-step\))|-?[\d.]+m?s$)/.test(part))),
    );
  /**
   * The clocks of a style sheet: each a length it makes for itself of the length of the
   * rabbit's hop, as so many rounds of it. Where the length of a hop is nought, as it is
   * unless the system says that movement is welcome, so many rounds of it are nought too.
   */
  const clocksOf = (file: string) =>
    sheet(file).flatMap((rule) =>
      [...rule.sets]
        .filter(([name, value]) => name.startsWith("--") && /^calc\(var\(--motion-hop\) \* \d+(\.\d+)?\)$/.test(value))
        .map(([name]) => `var(${name})`),
    );
  const BURRO = path.join("components", "kit", "Burro", "Burro.module.css");

  test("test_the_length_of_every_movement_is_a_token_which_is_nought_until_movement_is_welcome", () => {
    // But what stops every movement for a person who asked for less of it, which is no length of one.
    const written = moving
      .filter((rule) => !/prefers-reduced-motion:\s*reduce/.test(rule.under ?? ""))
      .flatMap((rule) =>
        lengthsOf(rule)
          .filter((length) => !/^var\(--motion-[a-z]+\)$/.test(length) && !clocksOf(rule.file).includes(length))
          .map((length) => `${where(rule)} ${length}`),
      );

    expect(moving.length).toBeGreaterThan(4);
    // Every movement names a length, so that none runs for a length nobody chose.
    expect(moving.filter((rule) => rule.sets.get("animation") !== "none" && lengthsOf(rule).length === 0).map(where)).toEqual([]);
    expect(written).toEqual([]);
    // The rabbit alone has clocks, one for each part of him that stirs.
    expect([...new Set(RULES.map((rule) => rule.file))].filter((file) => clocksOf(file).length > 0)).toEqual([BURRO]);
    expect(clocksOf(BURRO)).toHaveLength(4);
  });

  test("test_nothing_moves_without_end_but_the_rabbit_whom_the_system_alone_stills", () => {
    // Each movement runs once and ends, but the rabbit's. He hops until the answer is in, by
    // the length of his hop, and where he rests he stirs for as long as he is drawn, by the
    // clocks that are made of it. Nothing else may run without end.
    const endless = moving.filter((rule) =>
      ["animation", "animation-iteration-count"].some((property) => /\binfinite\b/.test(rule.sets.get(property) ?? "")),
    );
    const his = ["var(--motion-hop)", ...clocksOf(BURRO)];

    expect(endless.length).toBeGreaterThan(0);
    expect(endless.filter((rule) => rule.file !== BURRO).map(where)).toEqual([]);
    expect(endless.filter((rule) => !lengthsOf(rule).every((length) => his.includes(length)) || lengthsOf(rule).length === 0).map(where)).toEqual([]);
    // Nothing on a page stops what moves without end. A button stood by him that did, and
    // the founder asked for it to go: what a person has set in their system is relied on.
    // So his sheet draws no button, and no sheet of the website draws one for him.
    expect(RULES.filter((rule) => /\.stop(?![\w-])/.test(rule.selector) && (rule.file === BURRO || /burro/i.test(rule.selector))).map(where)).toEqual([]);
    // The system stills him, and outright. For a person who asked for less movement every
    // movement of his is taken away, and none is left to its first moment.
    const still = sheet(BURRO).filter((rule) => /prefers-reduced-motion:\s*reduce/.test(rule.under ?? ""));
    const stilled = still.filter((rule) => rule.sets.get("animation") === "none");
    expect(stilled.map((rule) => rule.selector).sort()).toEqual(endless.map((rule) => rule.selector).sort());
    // What stills him sets nothing else, and nothing of his is drawn for such a person alone.
    expect(still.filter((rule) => !stilled.includes(rule)).map(where)).toEqual([]);
    expect(stilled.filter((rule) => rule.sets.size !== 1).map(where)).toEqual([]);
  });

  test("test_where_less_movement_is_asked_for_nothing_moves_at_all", () => {
    // What moves, in whatever sheet, and whether it runs once or without end: the sheet that
    // moves it takes the movement away for a person who asked for less, under the same name.
    const asked = (rule: Rule) => /prefers-reduced-motion:\s*reduce/.test(rule.under ?? "");
    const moves = moving.filter((rule) => !asked(rule) && (rule.sets.get("animation") ?? "none") !== "none");
    const left = moves.filter(
      (rule) => !sheet(rule.file).some((other) => asked(other) && other.selector === rule.selector && other.sets.get("animation") === "none"),
    );

    expect(moves.length).toBeGreaterThan(4);
    expect(new Set(moves.map((rule) => rule.file)).size).toBeGreaterThan(1);
    expect(left.map(where)).toEqual([]);
    // Nothing is eased from one state to the next, so there is no movement of that kind to take away.
    expect(moving.filter((rule) => !asked(rule) && [...rule.sets.keys()].some((property) => /^transition/.test(property))).map(where)).toEqual([]);
    // And whatever a later sheet may write, the length of every movement is brought to
    // nothing for such a person and none runs twice, by a rule for everything on the page.
    const everything = RULES.filter((rule) => asked(rule) && rule.selector === "*");
    expect(everything.map((rule) => [rule.sets.get("animation-iteration-count"), /^0?\.0*1ms !important$/.test(rule.sets.get("animation-duration") ?? "")])).toEqual([
      ["1 !important", true],
    ]);
  });
});
