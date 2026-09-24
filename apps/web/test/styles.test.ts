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
