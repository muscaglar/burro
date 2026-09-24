/** @jest-environment node */
/**
 * What a browser showed of the layout, held in the style sheets. jsdom lays
 * nothing out, so a test of layout reads the styles: `support/css.ts`.
 *
 * Each test here is of something seen in a browser that no test had caught.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { isFor, rulesOf, subjectOf, type Rule } from "./support/css";

const SRC = path.resolve(__dirname, "..", "src");

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
const scrolls = (rule: Rule) =>
  ["overflow", "overflow-x", "overflow-y"].some((property) =>
    /\b(auto|scroll)\b/.test(rule.sets.get(property) ?? ""),
  );

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

  test("test_that_a_part_was_not_read_and_the_way_to_see_it_are_one_line", () => {
    const line = SEARCH.filter((rule) => isFor(rule.selector, "unread") && rule.under === null);

    expect(line.map((rule) => rule.sets.get("display"))).toContain("flex");
    expect(line.map((rule) => rule.sets.get("flex-wrap"))).toContain("wrap");
    expect(line.map((rule) => rule.sets.get("font-size"))).toContain("var(--size-small)");
  });
});

describe("what stays at the foot of the screen", () => {
  test("test_what_takes_the_focus_is_not_left_under_the_tray_that_sticks", () => {
    // The tray of areas to compare stays at the foot of the screen once an area is chosen.
    // A browser brings what takes the focus into view, and must bring it clear of the tray.
    const sticks = RULES.filter(
      (rule) => rule.sets.get("position") === "sticky" && rule.sets.has("inset-block-end"),
    );
    const page = sheet("styles/base.css").filter((rule) => rule.selector.trim() === "html");

    expect(sticks.map((rule) => rule.file)).toEqual(["components/CompareTray/CompareTray.module.css"]);
    // 176 px. The tray was measured at 160 at its highest, on a phone with four areas chosen.
    expect(page.map((rule) => rule.sets.get("scroll-padding-bottom")).filter(Boolean)).toEqual([
      "calc(2 * var(--space-8) + var(--space-7))",
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
   * resizes anything in the flow of the page.
   */
  const DRAWN_ONLY = new Set([
    "background",
    "background-color",
    "border-color",
    "box-shadow",
    "color",
    "cursor",
    "outline",
    "outline-color",
    "outline-offset",
    "text-decoration",
    "text-decoration-thickness",
    "text-underline-offset",
    // Of a skip link, which is laid out `absolute`: it is moved over the page, and moves nothing.
    "transform",
  ]);
  /** True of a selector that holds only with the focus, the pointer or a press, or only without. */
  const comesAndGoes = (selector: string) => /:(focus|focus-within|focus-visible|hover|active)\b/.test(selector);

  test("test_nothing_moves_or_changes_size_because_the_focus_or_the_pointer_came_or_went", () => {
    // Seen in a browser: with the focus the box was three lines high. A press anywhere else
    // took the focus, the box dropped to one line, and everything under it jumped up between
    // the button going down and coming up, so the press landed on nothing. The first press
    // after every typed search was lost.
    const moved = RULES.filter((rule) => comesAndGoes(rule.selector)).flatMap((rule) =>
      [...rule.sets.keys()]
        .filter((property) => !DRAWN_ONLY.has(property))
        .map((property) => `${rule.file}: ${rule.selector} sets ${property}`),
    );

    expect(RULES.some((rule) => comesAndGoes(rule.selector))).toBe(true);
    expect(moved).toEqual([]);
  });
});
