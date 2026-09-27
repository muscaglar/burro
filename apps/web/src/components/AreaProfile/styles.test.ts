/** @jest-environment node */
/**
 * How the page of an area is drawn, read from its style sheets. jsdom lays nothing out, so
 * what a browser would draw is held here by what the sheets say. Every sheet of the page
 * is read: its own, the portrait's, those of a fact and of its source, of the list of
 * sources, and of the census and the household income.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { rulesOf, subjectOf, type Rule } from "../../../test/support/css";

type Found = Rule & { readonly file: string };

const COMPONENTS = path.resolve(__dirname, "..");
/** The sheets that are dressed in the look. */
const DRESSED = [
  "AreaProfile/AreaProfile.module.css",
  "Portrait/Portrait.module.css",
  "FactRow/FactRow.module.css",
  "SourceLine/SourceLine.module.css",
  "SourceList/SourceList.module.css",
];
/**
 * The two that are held apart: their colours are those of the text of the page and no
 * other, and `test/census` and `test/income` hold them to it. They name no token of the look.
 */
const APART = ["CensusPanel/CensusPanel.module.css", "IncomePanel/IncomePanel.module.css"];
const SHEETS = [...DRESSED, ...APART];

const written = (file: string) => readFileSync(path.join(COMPONENTS, file), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const RULES: readonly Found[] = SHEETS.flatMap((file) => rulesOf(written(file)).map((rule) => ({ ...rule, file })));
const where = (rule: Found) => `${rule.file}: ${rule.selector}`;
const FORCED = /forced-colors/;
const dressed = (rule: Found) => DRESSED.includes(rule.file);
const atRest = RULES.filter((rule) => !FORCED.test(rule.under ?? ""));
/** True of a rule for what a style sheet draws before an element: a mark, which is no element and holds no word. */
const isAMark = (rule: Rule) => /::before$/.test(subjectOf(rule.selector));
const squeezed = (value: string | undefined) => (value ?? "").replace(/\s+/g, " ").trim();

describe("how the page of an area is drawn", () => {
  test("test_every_sheet_of_the_page_is_read", () => {
    expect(SHEETS).toHaveLength(7);
    expect(SHEETS.map((file) => [file, RULES.filter((rule) => rule.file === file).length > 3])).toEqual(
      SHEETS.map((file) => [file, true]),
    );
  });

  test("test_every_colour_is_a_token_and_no_style_sheet_writes_one_out", () => {
    const writtenOut = SHEETS.flatMap((file) =>
      (written(file).match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).map((found) => `${file} ${found}`),
    );

    expect(writtenOut).toEqual([]);
  });

  test("test_a_drawing_is_handed_to_a_sheet_by_name_and_laid_at_its_own_size_times_the_art_pixel", () => {
    // No sheet names a picture: it is handed each one by the part it dresses.
    expect(SHEETS.flatMap((file) => (written(file).match(/url\([^)]*\)|\/art\//g) ?? []).map((found) => `${file} ${found}`))).toEqual([]);

    const laid = atRest.filter((rule) => /var\(--(arrow|key)\)/.test(rule.sets.get("background") ?? ""));
    // The arrow of a part that opens is laid by the fold, which draws every bar of the website.
    expect(laid.map(where).sort()).toEqual([
      "Portrait/Portrait.module.css: .shortSources > summary::before",
      "SourceLine/SourceLine.module.css: .line::before",
      "SourceList/SourceList.module.css: .name::before",
    ]);
    for (const rule of laid) {
      const [, drawing = ""] = /var\(--(arrow|key)\)/.exec(rule.sets.get("background") ?? "") ?? [];
      const size = `calc(var(--px) * var(--${drawing}-w)) calc(var(--px) * var(--${drawing}-h))`;
      // The whole of it, once, at its own size: never stretched, and never at a share of its room.
      expect([where(rule), squeezed(rule.sets.get("background")).endsWith(`/ ${size} no-repeat`)]).toEqual([where(rule), true]);
      expect([where(rule), rule.sets.get("image-rendering")]).toEqual([where(rule), "pixelated"]);
      expect([where(rule), /%/.test(rule.sets.get("background") ?? "")]).toEqual([where(rule), false]);
      // The room it stands in is a count of art pixels too.
      for (const side of ["width", "height"]) {
        expect([where(rule), side, /^calc\(var\(--px\) \* var\(--[a-z]+-[wh]\)\)$/.test(rule.sets.get(side) ?? "")]).toEqual([
          where(rule),
          side,
          true,
        ]);
      }
    }
    expect(RULES.filter((rule) => rule.sets.has("background-size") || rule.sets.has("object-fit")).map(where)).toEqual([]);
  });

  test("test_the_picture_of_a_button_is_cut_where_its_drawing_says_and_is_laid_again_and_never_stretched", () => {
    const framed = atRest.filter((rule) => rule.sets.has("border-image"));
    const width = (side: string) => `calc(var(--px) * var(--button-${side}))`;
    const widths = ["top", "right", "foot", "left"].map(width).join(" ");

    expect(framed.map(where)).toEqual(["AreaProfile/AreaProfile.module.css: .again"]);
    for (const rule of framed) {
      expect(squeezed(rule.sets.get("border-image"))).toBe(
        `var(--button) var(--button-top) var(--button-right) var(--button-foot) var(--button-left) fill / ${widths} repeat`,
      );
      expect(squeezed(rule.sets.get("border-width"))).toBe(widths);
      expect(rule.sets.get("image-rendering")).toBe("pixelated");
    }
    // Under a press the picture gives way to the picture of the button pressed, and nothing else of it changes.
    const pressed = RULES.filter((rule) => rule.selector === ".again:active" && !FORCED.test(rule.under ?? ""));
    expect(pressed.map((rule) => [...rule.sets])).toEqual([[["border-image-source", "var(--button-down)"]]]);
    // With forced colours the picture is taken away by its source.
    const forced = RULES.filter((rule) => rule.selector === ".again" && FORCED.test(rule.under ?? ""));
    expect(forced.map((rule) => rule.sets.get("border-image-source"))).toEqual(["none"]);
    expect(RULES.filter((rule) => squeezed(rule.sets.get("border-image")) === "none").map(where)).toEqual([]);
  });

  test("test_every_word_is_set_in_a_face_of_the_look_and_the_face_of_names_at_a_size_of_its_own", () => {
    const faces = RULES.flatMap((rule) =>
      [...rule.sets].filter(([property]) => property === "font").map(([, value]) => ({ rule, value: squeezed(value) })),
    );
    const families = RULES.filter((rule) => rule.sets.has("font-family"));

    expect(faces.length).toBeGreaterThan(8);
    expect(families.map(where)).toEqual([]);
    for (const { rule, value } of faces) {
      // A name, a heading and a short label: at one of the four sizes of the face of names, with
      // its one weight, and never thickened by the browser.
      if (value.endsWith("var(--font-name)")) {
        expect([where(rule), /^400 var\(--name-[1-4]\) \/ [\d.]+ var\(--font-name\)$/.test(value)]).toEqual([where(rule), true]);
        expect([where(rule), rule.sets.get("font-synthesis")]).toEqual([where(rule), "none"]);
      } else {
        expect([where(rule), /^(400|700) var\(--size-(small|body|lead|h3)\) \/ \S+ var\(--font-say\)$/.test(value)]).toEqual([
          where(rule),
          true,
        ]);
      }
    }
    // A size that is set alone is a size of the reading face, by its token.
    const sizes = RULES.flatMap((rule) => (rule.sets.has("font-size") ? [[where(rule), rule.sets.get("font-size") ?? ""]] : []));
    expect(sizes.filter(([, size]) => !/^var\(--size-(small|body|lead|h3)\)$/.test(size ?? ""))).toEqual([]);
  });

  test("test_nothing_that_holds_text_has_a_height_of_its_own_so_that_text_can_be_made_larger", () => {
    const fixed = RULES.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(height|max-height|block-size|max-block-size)$/.test(property)),
    );
    // A mark, which holds no word. The picture of a share in the census, which is a drawing. And
    // the headings of a table that are kept for a screen reader where its rows are stacked.
    const holdsNoText = (rule: Found) =>
      isAMark(rule) ||
      (rule.file === "CensusPanel/CensusPanel.module.css" && [".picture", ".head"].includes(rule.selector));

    expect(fixed.length).toBeGreaterThan(5);
    expect(fixed.filter((rule) => !holdsNoText(rule)).map(where)).toEqual([]);
    // Nor is a line of text cut off, or kept to one line where it would run out of its box.
    expect(RULES.filter((rule) => /hidden|clip/.test(rule.sets.get("overflow") ?? "") && rule.selector !== ".head").map(where)).toEqual([]);
    expect(RULES.filter((rule) => rule.sets.has("text-overflow") || rule.sets.has("line-clamp")).map(where)).toEqual([]);
  });

  test("test_the_page_draws_nothing_of_a_bar_that_folds_which_the_fold_draws_as_it_draws_every_bar", () => {
    // Walked: the long parts of the page stood on sand with the arrow before their words,
    // which is what the founder asked to be changed of the settings. A fold was drawn four
    // ways on the website. The page says where a bar stands, and nothing of how it is drawn.
    const ofThePage = RULES.filter((rule) => [...APART, "AreaProfile/AreaProfile.module.css"].includes(rule.file));
    // A bar is named here only to be left out of what is said of what a group holds.
    const ofABar = ofThePage.filter((rule) => /\bsummary\b/.test(rule.selector.replace(/:not\(summary\)/g, "")));

    expect(ofABar.map(where)).toEqual([]);
    expect(ofThePage.filter((rule) => [...rule.sets.values()].some((value) => /var\(--arrow/.test(value))).map(where)).toEqual([]);
    // What it says of a bar is where what the bar says begins: as far from the sides of
    // the box as what a part opened to stands, of the parts of the stack and of no fold inside one.
    const begins = (under: string | null) =>
      ofThePage.filter((rule) => rule.sets.has("--bar-begins") && rule.under === under).map((rule) => `${rule.selector}: ${rule.sets.get("--bar-begins")}`);
    const opened = (under: string | null) =>
      ofThePage.filter((rule) => rule.selector === ".closed > .part" && rule.under === under).map((rule) => rule.sets.get("padding"));
    expect([begins(null), opened(null)]).toEqual([
      [".closedParts > .closed: var(--space-4)", ".group: var(--space-2)"],
      ["var(--space-3) var(--space-4) var(--space-4)"],
    ]);
    // A group inside a part holds what it holds as far in as its bar says its name.
    expect(ofThePage.filter((rule) => rule.selector === ".group > :not(summary)").map((rule) => rule.sets.get("padding-inline"))).toEqual([
      "var(--space-2)",
    ]);
    expect([begins("@media (min-width: 60rem)"), opened("@media (min-width: 60rem)")]).toEqual([
      [".closedParts > .closed: var(--space-5)"],
      ["var(--space-4) var(--space-5) var(--space-5)"],
    ]);
    // The fold says it with no weight, so that what the page says is what holds, whichever sheet is read last.
    const ofTheFold = rulesOf(written("Disclosure/Disclosure.module.css")).filter((rule) => rule.sets.has("--bar-begins"));
    expect(ofTheFold.map((rule) => rule.selector)).toEqual([":where(.disclosure)", ":where(.fold)"]);
  });

  test("test_the_first_row_of_a_group_stands_under_the_rule_of_what_was_opened_and_has_none_of_its_own", () => {
    // Seen in a browser: a rule of ink under the bar, and directly under it the rule of sand of the first row.
    const sheet = RULES.filter((rule) => rule.file === "AreaProfile/AreaProfile.module.css" && rule.under === null);
    const of = (selector: string) => sheet.filter((rule) => rule.selector === selector).map((rule) => [...rule.sets]);

    expect(of(".group > .rows > li:first-child")).toEqual([[["border-block-start", "0"]]]);
    // What a group holds stands in from the ends of its bar, and its bar does not.
    expect(of(".group > :not(summary)")).toEqual([[["padding-inline", "var(--space-2)"]]]);
  });

  test("test_the_stack_of_parts_fills_its_box_and_has_no_rule_of_its_own_against_the_rule_of_the_box", () => {
    const sheet = RULES.filter((rule) => rule.file === "AreaProfile/AreaProfile.module.css" && rule.under === null);
    const of = (selector: string) => sheet.filter((rule) => rule.selector === selector).map((rule) => [...rule.sets]);

    expect(of(".closedParts > .closed:first-child")).toEqual([[["border-block-start", "0"]]]);
    expect(of(".closedParts > .closed:last-child")).toEqual([[["border-block-end", "0"]]]);
  });

  test("test_nothing_moves_and_a_mark_turns_in_one_step", () => {
    const moving = RULES.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(animation|transition|translate|rotate|scale|zoom)/.test(property)),
    );
    const turned = RULES.filter((rule) => rule.sets.has("transform"));
    // The face of the one button of a part steps into its shadow under a press: `test/styles` holds how far.
    const steps = (rule: Found) => rule.selector === ".again:active > span" && /no-preference/.test(rule.under ?? "");

    expect(moving.map(where)).toEqual([]);
    // The arrow of a part that opens is turned by the fold, whose own test holds how. What
    // is left here is the mark of the sources of the portrait, and the face of the button.
    expect(turned.length).toBeGreaterThan(1);
    for (const rule of turned.filter((one) => !steps(one))) {
      // A mark is turned to point at what it opens, or down at what it opened, and is a mark and nothing else.
      expect([where(rule), isAMark(rule)]).toEqual([where(rule), true]);
      expect([where(rule), /^(rotate\((90|180)deg\)|none)$/.test(rule.sets.get("transform") ?? "")]).toEqual([where(rule), true]);
    }
    // It turns because a part was opened, which is a press that has landed, and never for the pointer or the focus.
    expect(turned.filter((rule) => !steps(rule) && /:(hover|focus|focus-visible|focus-within|active)\b/.test(rule.selector)).map(where)).toEqual(
      [],
    );
  });

  test("test_a_rule_is_a_hard_line_as_wide_as_a_pixel_of_a_drawing_in_a_colour_of_the_look", () => {
    const EDGES = /^border(-block|-inline)?(-start|-end)?$/;
    const ruled = atRest
      .filter(dressed)
      .flatMap((rule) => [...rule.sets].filter(([property, value]) => EDGES.test(property) && value !== "0").map(([, value]) => ({ rule, value })));

    expect(ruled.length).toBeGreaterThan(15);
    expect(
      ruled
        // The sheets of other parts are held here too, and are made solid by whoever holds them:
        // the sheet of the page itself is held to a whole edge by the test after this one.
        .filter(({ value }) => !/^var\(--edge\) (solid|dashed) var\(--(border|ink|sand|notice-edge)\)$/.test(value))
        .map(({ rule, value }) => `${where(rule)} ${value}`),
    ).toEqual([]);
    // No corner is rounded: a corner has no radius, or the radius of the tokens, which is nought.
    // And nothing throws a shadow but a box of the kit: a band is drawn inside.
    expect(RULES.filter((rule) => !/^(0|var\(--radius(-card)?\))$/.test(rule.sets.get("border-radius") ?? "0")).map(where)).toEqual([]);
    expect(RULES.filter((rule) => rule.sets.has("box-shadow") && !/^(none|inset )/.test(rule.sets.get("box-shadow") ?? "")).map(where)).toEqual(
      [],
    );
  });

  test("test_no_edge_of_the_page_of_an_area_is_dashed_or_dotted", () => {
    // The founder: "The dashed border is not understood to a user, please make solid". A
    // dashed rule stood over the journeys of the search that is open, and said nothing that
    // a person could read from it.
    const OF_THE_PAGE = "AreaProfile/AreaProfile.module.css";
    const drawn = RULES.filter((rule) => rule.file === OF_THE_PAGE).flatMap((rule) =>
      [...rule.sets].map(([property, value]) => ({ rule, property, value })),
    );

    expect(drawn.filter(({ value }) => /\b(dashed|dotted)\b/.test(value)).map(({ rule, property }) => `${where(rule)} ${property}`)).toEqual([]);
    // What is said next in a box stands under a rule of sand, as a row of the page does.
    expect(drawn.length).toBeGreaterThan(100);
    const journeys = atRest.filter((rule) => rule.file === OF_THE_PAGE && rule.selector === ".journeys");
    expect(journeys.map((rule) => rule.sets.get("border-block-start"))).toEqual(["var(--edge) solid var(--sand)"]);
  });

  test("test_what_stands_on_a_ground_of_the_look_is_read_in_the_colour_that_is_read_on_it", () => {
    // Ink alone is read on sand and on amber, and page on ink and on hedge.
    const READ_ON: Readonly<Record<string, string>> = {
      "var(--sand)": "var(--ink)",
      "var(--chosen)": "var(--on-chosen)",
      "var(--ink)": "var(--page)",
      "var(--hedge)": "var(--page)",
    };
    const grounds = atRest.flatMap((rule) =>
      ["background", "background-color"].flatMap((property) => {
        const ground = rule.sets.get(property) ?? "";
        return ground in READ_ON ? [{ rule, ground }] : [];
      }),
    );

    expect(grounds.length).toBeGreaterThan(8);
    expect(grounds.filter(({ rule, ground }) => rule.sets.get("color") !== READ_ON[ground]).map(({ rule }) => where(rule))).toEqual([]);
    // No link and no quieter line stands on either: a fold holds its heading, and a plate its label.
    const quiet = atRest.filter((rule) => /var\(--(muted|accent|shade|cobalt)\)/.test(rule.sets.get("color") ?? ""));
    expect(quiet.filter((rule) => ["background", "background-color"].some((property) => (rule.sets.get(property) ?? "") in READ_ON)).map(where)).toEqual([]);
  });

  test("test_with_forced_colours_the_systems_own_colours_carry_every_edge_and_every_plate", () => {
    const forced = RULES.filter((rule) => FORCED.test(rule.under ?? ""));
    const SYSTEM = /^(Canvas|CanvasText|ButtonFace|ButtonText|Highlight|LinkText|GrayText|Mark|none)$/;

    for (const file of DRESSED.filter((one) => one !== "FactRow/FactRow.module.css")) {
      expect([file, forced.some((rule) => rule.file === file)]).toEqual([file, true]);
    }
    for (const rule of forced) {
      for (const [property, value] of rule.sets) {
        if (/color$|^background$/.test(property)) expect([where(rule), property, SYSTEM.test(value)]).toEqual([where(rule), property, true]);
      }
    }
    // A plate of ink or of hedge gives way to the ground of the system, with its words in the system's.
    const plates = atRest.filter(dressed).filter((rule) => /^var\(--(ink|hedge)\)$/.test(rule.sets.get("background") ?? ""));
    expect(plates.length).toBeGreaterThan(4);
    for (const plate of plates) {
      const again = forced.filter((rule) => rule.file === plate.file && rule.selector === plate.selector);
      expect([where(plate), again.map((rule) => [rule.sets.get("background"), rule.sets.get("color")])]).toEqual([
        where(plate),
        [["Canvas", "CanvasText"]],
      ]);
    }
  });

  test("test_the_line_of_a_vibe_is_laid_out_by_the_width_of_its_list_in_the_size_of_the_text", () => {
    // Seen in a browser, at 1024 wide and with text twice as large on a desk: a line that took
    // the width of the screen for its own left where the area sits a column one word wide.
    const portrait = RULES.filter((rule) => rule.file === "Portrait/Portrait.module.css");
    const ofALine = (rule: Found) => /\.(line|name|picture|end|endName|words|figure|opens)\b/.test(rule.selector) && !/\.unplaced/.test(rule.selector);
    const byTheScreen = portrait.filter((rule) => /@media[^{]*(min|max)-width/.test(rule.under ?? ""));
    const byTheList = portrait.filter((rule) => /^@container\b/.test(rule.under ?? ""));

    const lists = portrait.filter((rule) => rule.selector === ".marks" && rule.under === null);
    expect(lists.flatMap((rule) => rule.sets.get("container-type") ?? [])).toEqual(["inline-size"]);
    expect(byTheScreen.filter(ofALine).map(where)).toEqual([]);
    expect(byTheList.filter(ofALine).length).toBeGreaterThan(15);
    // The width is asked in the size of the text, so that larger text is given the narrower way to stand.
    const asked = [...new Set(byTheList.map((rule) => rule.under ?? ""))];
    expect(asked.length).toBeGreaterThan(2);
    expect(asked.filter((one) => !/^@container(( and)? \((min|max)-width: [\d.]+rem\))+$/.test(one))).toEqual([]);
  });

  test("test_the_census_and_the_household_income_name_no_token_of_the_look", () => {
    // What is drawn of their fold, of a failure and of their one button is the page's, by
    // the names it lends them. Their own sheets are as plain as the text of the page.
    const named = APART.flatMap((file) => (written(file).match(/var\(--[a-z0-9-]+\)/g) ?? []).map((token) => `${file} ${token}`));
    const OF_THE_LOOK = /--(px|edge|frame|box-shadow|font|name-|ink|page|sand|amber|poppy|hedge|cobalt|chosen|notice|arrow|key|button)/;

    expect(named.length).toBeGreaterThan(20);
    expect(named.filter((token) => OF_THE_LOOK.test(token))).toEqual([]);
  });
});
