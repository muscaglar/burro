/** @jest-environment node */
/**
 * How a town is laid out, read from its style sheets. jsdom lays nothing out, so what a
 * browser would draw is held here by what the sheets say. Every sheet of the folder is
 * read, so a sheet that is written next is held as well as the ones that are there.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { rulesOf, type Rule } from "../../../test/support/css";

type Found = Rule & { readonly file: string };

const SHEETS = readdirSync(__dirname)
  .filter((name) => name.endsWith(".module.css"))
  .sort();
const written = (file: string) => readFileSync(path.join(__dirname, file), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const RULES: readonly Found[] = SHEETS.flatMap((file) => rulesOf(written(file)).map((rule) => ({ ...rule, file })));
const where = (rule: Found) => `${rule.file}: ${rule.selector}`;
const FORCED = /forced-colors/;
const sets = (selector: string, file: string) =>
  RULES.filter((rule) => rule.file === file && rule.selector === selector && rule.under === null).map((rule) => rule.sets);

describe("how a town is laid out", () => {
  test("test_the_drawing_and_the_town_each_have_a_style_sheet", () => {
    expect(SHEETS).toEqual(expect.arrayContaining(["Drawing.module.css", "Town.module.css"]));
  });

  test("test_a_drawing_is_laid_at_its_own_size_times_one_pixel_never_stretched_and_never_at_a_percentage", () => {
    const [canvas] = sets(".drawing", "Drawing.module.css");
    const [piece] = sets(".piece", "Drawing.module.css");

    expect(canvas?.get("width")).toBe("calc(var(--size) * var(--across))");
    expect(canvas?.get("height")).toBe("calc(var(--size) * var(--down))");
    expect(piece?.get("width")).toBe("calc(var(--size) * var(--w))");
    expect(piece?.get("height")).toBe("calc(var(--size) * var(--h))");
    // One frame of a strip: the whole strip at its own size, moved by whole frames.
    expect((piece?.get("background") ?? "").replace(/\s+/g, " ")).toBe(
      "var(--art) calc(var(--size) * var(--w) * var(--frame) * -1) 0 / calc(var(--size) * var(--w) * var(--frames)) calc(var(--size) * var(--h)) no-repeat",
    );
    expect(piece?.get("image-rendering")).toBe("pixelated");
    // No length of a town is a share of anything: what says what is drawn of a part is no length.
    expect(RULES.flatMap((rule) => [...rule.sets].filter(([property]) => property !== "display").map(([, value]) => value)).filter((value) => value.includes("%"))).toEqual([]);
    // No other rule lays a picture, and none says how large one is but the rule that lays it.
    const laying = RULES.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(background-image|background-size|object-fit|border-image.*)$/.test(property)),
    );
    expect(laying.map(where)).toEqual([]);
    expect(SHEETS.flatMap((file) => written(file).match(/url\([^)]*\)/g) ?? [])).toEqual([]);
  });

  test("test_a_pixel_of_a_town_is_the_pixel_of_the_ground_and_the_art_pixel_only_beside_a_title", () => {
    const sized = RULES.filter((rule) => rule.sets.has("--size"));

    expect(sized.map((rule) => [rule.selector, rule.sets.get("--size")])).toEqual([
      [".drawing", "var(--px-ground)"],
      ['.drawing[data-size="large"]', "var(--px)"],
    ]);
  });

  test("test_nothing_but_the_drawing_has_a_height_so_that_its_words_can_be_made_larger", () => {
    const fixed = RULES.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(height|max-height|block-size|max-block-size)$/.test(property)),
    );

    expect(fixed.map(where).sort()).toEqual(["Drawing.module.css: .drawing", "Drawing.module.css: .piece"]);
  });

  test("test_every_colour_is_a_token_and_no_style_sheet_holds_one_of_its_own", () => {
    const writtenOut = SHEETS.flatMap((file) =>
      (written(file).match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).map((found) => `${file} ${found}`),
    );
    // What a rule draws in, but for what the part hands its own sheet of a drawing, and the width of an edge.
    const HANDED = /^var\(--(art|w|h|frames?|x|y|across|down|size|edge)\)$/;
    const colours = RULES.filter((rule) => !FORCED.test(rule.under ?? "")).flatMap((rule) =>
      [...rule.sets]
        .filter(([property]) => /^(color|background|background-color|border|border-color|border-block-start|outline)$/.test(property))
        .flatMap(([, value]) => value.match(/var\(--[a-z0-9-]+\)/g) ?? [])
        .filter((token) => !HANDED.test(token)),
    );
    // Words in the colour of words, on the cream they are read on, inside an edge of ink or on a rule of sand.
    const OF_THE_TOWN = ["var(--border)", "var(--page)", "var(--sand)", "var(--text)"];

    expect(writtenOut).toEqual([]);
    expect(colours.length).toBeGreaterThan(2);
    expect([...new Set(colours)].filter((colour) => !OF_THE_TOWN.includes(colour))).toEqual([]);
    expect(SHEETS.flatMap((file) => written(file).match(/var\(--(fur|earth)\)/g) ?? [])).toEqual([]);
  });

  test("test_every_word_is_set_in_the_reading_face_and_none_in_the_face_of_names", () => {
    // What a town says is a sentence, and a sentence is read: the face of names is for a name.
    const faces = RULES.flatMap((rule) =>
      [...rule.sets].filter(([property]) => property === "font" || property === "font-family").map(([, value]) => value),
    );

    expect(faces.length).toBeGreaterThan(0);
    expect(faces.filter((face) => !/var\(--font-say\)$/.test(face))).toEqual([]);
    expect(SHEETS.filter((file) => /var\(--font-name\)/.test(written(file)))).toEqual([]);
  });

  test("test_nothing_moves_nothing_is_dimmed_and_nothing_changes_under_the_pointer_a_press_or_the_focus", () => {
    const moving = RULES.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(animation|transition|transform|translate|rotate|scale|zoom)/.test(property)),
    );
    const dimmed = RULES.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(opacity|filter|backdrop-filter|mix-blend-mode)$/.test(property)),
    );
    const inAState = RULES.filter((rule) => /:(hover|focus|focus-within|focus-visible|active)\b/.test(rule.selector));

    expect(moving.map(where)).toEqual([]);
    expect(dimmed.map(where)).toEqual([]);
    expect(inAState.map(where)).toEqual([]);
    // A town is a drawing and no box: it throws no shadow, as a thing that can be pressed does.
    expect(RULES.filter((rule) => rule.sets.has("box-shadow")).map(where)).toEqual([]);
  });

  test("test_on_the_grass_its_words_stand_in_a_box_of_cream_with_an_edge_of_ink", () => {
    const [box] = sets('.town[data-on="grass"] > .says', "Town.module.css");

    expect(box?.get("background")).toBe("var(--page)");
    expect(box?.get("border")).toBe("var(--edge) solid var(--border)");
    expect(box?.get("padding")).toBeDefined();
  });

  test("test_its_words_stand_beside_the_drawing_where_there_is_room_and_under_it_where_there_is_not", () => {
    const [town] = sets(".town", "Town.module.css");
    const [says] = sets(".says", "Town.module.css");

    // It is laid out by the room it is given and not by the width of the screen, so it stands anywhere.
    expect(town?.get("display")).toBe("flex");
    expect(town?.get("flex-wrap")).toBe("wrap");
    expect(says?.get("min-width")).toBe("0");
    expect(SHEETS.filter((file) => /container-type/.test(written(file)))).toEqual([]);
    // One thing asks how wide the screen is: which of its two lines a town says at the head
    // of the page of an area, where what the area is like must come first on a phone. It
    // chooses what is said, and moves and sizes nothing of the drawing.
    const byTheScreen = RULES.filter((rule) => /@media\s*\((min|max)-width/.test(rule.under ?? ""));
    expect(byTheScreen.filter((rule) => !rule.selector.startsWith(":global(header[data-town]) > .town > ")).map(where)).toEqual([]);
    expect([...new Set(byTheScreen.map((rule) => rule.under))]).toEqual(["@media (max-width: 39.99rem)"]);
    expect(byTheScreen.filter((rule) => /\[role|\.drawing|\.piece/.test(rule.selector)).map(where)).toEqual([]);
  });
});
