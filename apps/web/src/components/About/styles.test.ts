/** @jest-environment node */
/**
 * How the pages that explain are laid out, read from their style sheets. jsdom lays nothing
 * out, so what a browser would draw is held here by what the sheets say.
 *
 * It reads the sheet of what the four pages share, and the sheet of each part that stands
 * on one of them, so that a rule written next is held as the ones that are there.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { heavier, rulesOf, weightOf, type Rule } from "../../../test/support/css";

type Found = Rule & { readonly file: string };

const COMPONENTS = path.resolve(__dirname, "..");
const SHEETS = [
  "About/About.module.css",
  "About/Fold.module.css",
  "About/KeyRows.module.css",
  "VibesList/VibesList.module.css",
  "VibesList/Key.module.css",
  "VibesList/BandKey.module.css",
  "Town/TownKey.module.css",
  "MethodsTables/MethodsTables.module.css",
  "SourceList/SourceList.module.css",
];
const written = (file: string) => readFileSync(path.join(COMPONENTS, file), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const RULES: readonly Found[] = SHEETS.flatMap((file) => rulesOf(written(file)).map((rule) => ({ ...rule, file })));
const where = (rule: Found) => `${rule.file}: ${rule.selector}`;
const FORCED = /forced-colors/;
const setsOf = (file: string, selector: string) =>
  new Map(RULES.filter((rule) => rule.file === file && rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

/**
 * What is a drawing, or a mark that a sheet draws in whole art pixels: it has a size, and holds
 * no words. The pin of the key is one, with the figure that is set on it: the figure is sized
 * as the drawing is, as the map sizes it, and what it says is said in words beside the pin.
 * So is the edge of a note and of a fault, which the key draws and which holds no word.
 */
const DRAWN = /(swatch|noteEdge|drawnPin|drawnFigure|::before|::after|::marker)/;

describe("how a page that explains is laid out", () => {
  test("test_nothing_that_holds_words_has_a_height_so_that_the_words_can_be_made_larger", () => {
    // What is kept for a screen reader and not drawn is cut to nothing, and holds no words that are seen.
    const fixed = RULES.filter(
      (rule) =>
        !DRAWN.test(rule.selector) &&
        rule.sets.get("clip-path") !== "inset(50%)" &&
        [...rule.sets.keys()].some((property) => /^(height|max-height|block-size|max-block-size)$/.test(property)),
    );

    expect(RULES.length).toBeGreaterThan(40);
    expect(fixed.map(where)).toEqual([]);
    // And no line is cut short, or kept on one line where it has no room.
    const cut = RULES.filter((rule) => rule.sets.has("text-overflow") || /clamp/.test(rule.sets.get("-webkit-line-clamp") ?? ""));
    expect(cut.map(where)).toEqual([]);
  });

  test("test_every_colour_is_a_token_of_the_look_and_what_is_read_is_ink_on_cream", () => {
    const writtenOut = SHEETS.flatMap((file) =>
      (written(file).match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).map((found) => `${file} ${found}`),
    );
    const grounds = RULES.filter((rule) => !FORCED.test(rule.under ?? "") && !DRAWN.test(rule.selector)).flatMap((rule) =>
      [...rule.sets]
        .filter(([property]) => property === "background" || property === "background-color")
        .flatMap(([, value]) => (value.match(/var\(--[a-z0-9-]+\)/g) ?? []).map((token) => `${where(rule)} ${token}`)),
    );
    // Cream to be read on. Ink under a label, whose words are cream. Sand under a figure in
    // ink, and amber under what is open, which are the two other grounds ink is read on.
    const READ_ON = /var\(--(page|bg|surface|notice-bg|info-bg|ink|sand|chosen)\)$/;

    expect(writtenOut).toEqual([]);
    expect(grounds.length).toBeGreaterThan(3);
    expect(grounds.filter((ground) => !READ_ON.test(ground))).toEqual([]);
    // Brown is the rabbit's, and he is not drawn on these pages.
    expect(SHEETS.filter((file) => /var\(--(fur|earth)\)/.test(written(file)))).toEqual([]);
  });

  test("test_words_on_sand_on_amber_and_on_ink_are_in_the_one_colour_that_is_read_on_each", () => {
    // Only ink is read on sand and on amber, and only cream on ink: a quieter colour and the
    // colour of a link fall short on all three.
    const on = (ground: RegExp) =>
      RULES.filter(
        (rule) =>
          !FORCED.test(rule.under ?? "") &&
          !DRAWN.test(rule.selector) &&
          ground.test(rule.sets.get("background") ?? rule.sets.get("background-color") ?? ""),
      );

    for (const rule of on(/var\(--(sand|chosen)\)$/)) {
      expect([where(rule), rule.sets.get("color")]).toEqual([where(rule), expect.stringMatching(/^var\(--(ink|text|on-chosen)\)$/)]);
    }
    for (const rule of on(/^var\(--ink\)$/)) {
      expect([where(rule), rule.sets.get("color")]).toEqual([where(rule), "var(--page)"]);
    }
  });

  test("test_the_face_of_names_is_for_a_name_a_heading_and_a_short_label_and_no_sheet_names_a_face_itself", () => {
    const faces = RULES.flatMap((rule) =>
      [...rule.sets].filter(([property]) => property === "font" || property === "font-family").map(([, value]) => ({ rule, value })),
    );

    expect(faces.length).toBeGreaterThan(2);
    expect(faces.filter(({ value }) => /["']/.test(value)).map(({ rule }) => where(rule))).toEqual([]);
    expect(faces.filter(({ value }) => !/var\(--font-(name|say)\)$/.test(value)).map(({ rule }) => where(rule))).toEqual([]);
    // In the face of names a pixel of a letter is a whole number of pixels of the screen
    // only at its own sizes, and it has one weight, which no browser may thicken.
    for (const { rule, value } of faces.filter((face) => /var\(--font-name\)$/.test(face.value))) {
      expect([where(rule), value]).toEqual([where(rule), expect.stringMatching(/^400 var\(--name-[1-4]\) \/ [\d.]+ var\(--font-name\)$/)]);
      expect([where(rule), rule.sets.get("font-synthesis")]).toEqual([where(rule), "none"]);
    }
  });

  test("test_nothing_moves_nothing_is_dimmed_and_nothing_changes_size_under_the_pointer_or_the_focus", () => {
    const moving = RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition)/.test(property)));
    const dimmed = RULES.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(opacity|filter|backdrop-filter|mix-blend-mode)$/.test(property)),
    );
    const inHand = RULES.filter((rule) => /:(hover|focus|focus-within|focus-visible|active)\b/.test(rule.selector));
    const DRAWN_ONLY = /^(background|background-color|color|outline|outline-color|outline-offset|text-decoration|text-decoration-thickness)$/;

    expect(moving.map(where)).toEqual([]);
    expect(dimmed.map(where)).toEqual([]);
    expect(inHand.flatMap((rule) => [...rule.sets.keys()].filter((property) => !DRAWN_ONLY.test(property)).map((property) => `${where(rule)} sets ${property}`))).toEqual([]);
  });

  test("test_a_box_of_the_kit_is_given_room_and_a_place_and_never_a_ground_or_an_edge_of_its_own", () => {
    // A box brings its ground, its rule and its shadow, which lie behind what it holds. What
    // lays it out gives it none, and cuts nothing off at its edge.
    const boxes = [".head", ".part", ".boxed", ".slip", ".edged"].map((selector) => setsOf("About/About.module.css", selector));

    for (const sets of boxes) {
      expect([...sets.keys()].filter((property) => /^(background|border|box-shadow|overflow)/.test(property))).toEqual([]);
    }
    expect(RULES.filter((rule) => rule.sets.has("box-shadow") && !FORCED.test(rule.under ?? "")).map((rule) => [where(rule), rule.sets.get("box-shadow")]).filter(([, shadow]) => !/^inset /.test(shadow ?? ""))).toEqual([]);
  });

  test("test_how_much_room_a_box_keeps_does_not_hang_on_which_style_sheet_is_read_last", () => {
    // Every box of these pages is told that it brings its own room, so the kit gives it
    // none and the room is said once. A rule of the kit that set it would have to be outweighed.
    const kit = rulesOf(readFileSync(path.join(COMPONENTS, "kit", "Frame", "Frame.module.css"), "utf8"));
    const ofTheKit = kit.filter((rule) => rule.sets.has("padding")).map((rule) => rule.selector);

    expect(ofTheKit).toEqual([".roomy"]);
    // Where a box of these pages is as wide as it is told, the rule that tells it outweighs the kit's.
    const widths = kit.filter((rule) => rule.sets.has("max-width")).map((rule) => weightOf(rule.selector));
    const own = RULES.filter((rule) => rule.sets.has("max-width") && /\.(head|part|boxed|slip|edged|vibe|contents)$/.test(rule.selector));
    for (const rule of own) {
      expect([where(rule), widths.every((weight) => heavier(weightOf(rule.selector), weight))]).toEqual([where(rule), true]);
    }
  });

  test("test_the_heading_of_a_part_stands_beside_what_is_read_only_where_there_is_room", () => {
    const beside = RULES.filter((rule) => rule.file === "About/About.module.css" && rule.selector === '.part[data-lay="beside"]');

    expect(setsOf("About/About.module.css", ".part").get("grid-template-columns")).toBe("minmax(0, 1fr)");
    expect(beside.map((rule) => [rule.under, rule.sets.get("grid-template-columns")])).toEqual([
      ["@media (min-width: 60rem)", "minmax(0, 20rem) minmax(0, 1fr)"],
    ]);
  });

  test("test_a_part_keeps_its_room_where_no_page_gives_it_one", () => {
    // A part is drawn inside a page that says how much room a box keeps. Drawn anywhere
    // else, a room that nothing gave would leave it none, and its words against its rule.
    const about = readFileSync(path.join(COMPONENTS, "About/About.module.css"), "utf8");
    const asked = [...about.matchAll(/var\(--room([^)]*)\)/g)].map((found) => found[1]?.trim());

    expect(asked.length).toBeGreaterThan(5);
    expect([...new Set(asked)]).toEqual([", var(--space-3"]);
  });

  test("test_the_drawing_beside_a_heading_keeps_its_place_where_the_heading_takes_a_second_line", () => {
    // Seen on a phone: the heading of the sources took two lines, and the key stood on a line of its own over it.
    expect(setsOf("About/About.module.css", ".titled").get("grid-template-columns")).toBe("minmax(0, 1fr)");
    expect(setsOf("About/About.module.css", '.titled[data-drawn="true"]').get("grid-template-columns")).toBe("auto minmax(0, 1fr)");
    expect(setsOf("About/About.module.css", ".titled").has("flex-wrap")).toBe(false);
  });

  test("test_a_small_heading_is_a_board_of_ink_with_its_words_in_the_colour_that_is_read_on", () => {
    const board = setsOf("About/About.module.css", ".board");

    expect([board.get("background"), board.get("color")]).toEqual(["var(--ink)", "var(--page)"]);
    expect(board.get("font")).toBe("400 var(--name-1) / 1.1 var(--font-name)");
    // It is as wide as its words, and a label too long for its line takes a second.
    expect([board.get("width"), board.get("max-width")]).toEqual(["fit-content", "100%"]);
    expect(board.has("white-space")).toBe(false);
  });

  test("test_a_table_has_a_plain_edge_and_its_last_row_stands_on_the_edge_itself", () => {
    const last = RULES.filter((rule) => rule.file === "About/About.module.css" && /^\.edged tbody > tr:last-child > t[hd]$/.test(rule.selector));

    expect(last.map((rule) => rule.sets.get("border-bottom"))).toEqual(["0", "0"]);
    expect(setsOf("About/About.module.css", ".edged th").get("padding-inline")).toBe("var(--space-3)");
  });

  test("test_what_another_hand_draws_is_given_cream_under_a_loose_sentence_by_a_rule_that_weighs_nothing", () => {
    const loose = RULES.filter((rule) => rule.file === "About/About.module.css" && rule.selector === ":where(.loose) > :where(p)" && rule.under === null);

    expect(loose.map((rule) => [rule.sets.get("background"), rule.sets.get("border")])).toEqual([
      ["var(--page)", "var(--edge) solid var(--border)"],
    ]);
    expect(loose.map((rule) => weightOf(rule.selector))).toEqual([[0, 0, 0]]);
    expect([...setsOf("About/About.module.css", ".loose").keys()].filter((property) => /^(background|border|padding)/.test(property))).toEqual([]);
  });
});
