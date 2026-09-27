/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import {
  asWritten,
  contrast,
  isColour,
  luminance,
  roundedDown,
  themes,
  writtenForAWideScreen,
  writtenWhereMovementIsWelcome,
} from "./support/contrast";

const SRC = path.resolve(__dirname, "..", "src");
const TOKENS = path.resolve(SRC, "styles", "tokens.css");
const withoutComments = (css: string) => css.replace(/\/\*[\s\S]*?\*\//g, "");

/** Every style sheet of the website, with what is said in comments taken out. */
function styleSheets(folder = SRC): [file: string, css: string][] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry): [string, string][] => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return styleSheets(file);
    if (!entry.name.endsWith(".css")) return [];
    return [[path.relative(SRC, file), withoutComments(readFileSync(file, "utf8"))]];
  });
}

/** The seventeen colours of the look, by the names every style sheet calls them. */
const SEVENTEEN: Readonly<Record<string, string>> = {
  "--ink": "#2a2140",
  "--page": "#f7f1de",
  "--lea": "#dbe8b1",
  "--sand": "#e9cf94",
  "--meadow": "#a8d85e",
  "--verge": "#63b34a",
  "--hedge": "#2b7a5a",
  "--shallows": "#86dde2",
  "--haven": "#2f9fd0",
  "--cobalt": "#3453d1",
  "--amber": "#f6b426",
  "--poppy": "#db533b",
  "--heath": "#b87bc6",
  "--fur": "#9b8a7f",
  "--shade": "#65566a",
  "--slate": "#6d7fa6",
  "--earth": "#a9683d",
};

/**
 * What was added to them, and may be three at the most: each because a rule of contrast
 * cannot be met without it. All three are greens of the map, which has five bands and
 * found four greens among the seventeen, of which two are too near and one is too deep.
 */
const ADDED: Readonly<Record<string, string>> = {
  "--dew": "#e6f1c5",
  "--fern": "#3c9952",
  "--ivy": "#317e5d",
};

const THE_LOOK: Readonly<Record<string, string>> = { ...SEVENTEEN, ...ADDED };
/** The greens of the look: what a band of the map may be. */
const GREENS = ["--dew", "--lea", "--meadow", "--verge", "--fern", "--hedge", "--ivy"];

/** The colours of the account before this one, which was in browns. None is left, by name or by value. */
const OF_THE_BROWNS: Readonly<Record<string, string>> = {
  "--tar": "#2a1b1f",
  "--bark": "#5e3a2b",
  "--timber": "#96603a",
  "--plank": "#c9925a",
  "--straw": "#edc76b",
  "--parchment": "#f2e2b6",
  "--chalk": "#fdf6dd",
  "--flint": "#54474a",
  "--dun": "#8a7a72",
  "--oat": "#bcab98",
  "--pine": "#274b41",
  "--leaf": "#4f8a45",
  "--sprout": "#a3c755",
  "--damson": "#6e2438",
  "--berry": "#b5404a",
  "--rosehip": "#e27d5a",
  "--dusk": "#2a3655",
  // Cobalt keeps its name and is another blue.
  "--cobalt of the browns": "#4a78b0",
  "--sky": "#86b9d8",
  "--mist": "#cfe6e2",
  // There is no wall: the ground of a page is a meadow.
  "--wall": "",
};

/**
 * What each colour is read against, and the ratio it needs: 4.5 for text and
 * 3 for an edge, a ring or a filled shape. From docs/design/web.md, section 8.
 */
const PAIRS: readonly (readonly [token: string, against: string, needs: number])[] = [
  ["--text", "--bg", 4.5],
  ["--text", "--surface", 4.5],
  ["--muted", "--bg", 4.5],
  ["--muted", "--surface", 4.5],
  ["--accent", "--bg", 4.5],
  ["--accent", "--surface", 4.5],
  ["--on-accent", "--accent", 4.5],
  ["--border", "--bg", 3],
  ["--border", "--surface", 3],
  ["--focus", "--bg", 3],
  // A box stands on the grass, and is told from it by its edge: on the tile, and on the
  // flat ground that is drawn where no tile is.
  ["--border", "--meadow", 3],
  ["--border", "--lea", 3],
  // What is on is amber. Amber is not told from cream, so what is on has an edge of ink.
  ["--on-chosen", "--chosen", 4.5],
  ["--border", "--chosen", 3],
  // A notice is cream, its words are ink, and its edge is a band of amber beside a rule
  // of ink. The rule is what tells it from the page, and the band is told from the rule.
  ["--notice-text", "--notice-bg", 4.5],
  ["--notice-edge", "--notice-bg", 3],
  ["--notice-edge", "--notice-mark", 3],
  ["--info-text", "--info-bg", 4.5],
  // What Burro asks stands on the ground of a notice, with a link and a quieter line in it.
  ["--accent", "--info-bg", 4.5],
  ["--muted", "--info-bg", 4.5],
  // A trade-off and a fault are said in ink. Poppy is their mark and their edge, and is
  // never the colour of small words: on cream it is 3.5 to 1.
  ["--tradeoff", "--bg", 4.5],
  ["--tradeoff", "--surface", 4.5],
  ["--tradeoff-mark", "--bg", 3],
  ["--tradeoff-mark", "--surface", 3],
  ["--good", "--bg", 4.5],
  ["--good", "--surface", 4.5],
  ["--error", "--bg", 4.5],
  ["--error", "--surface", 4.5],
  ["--error-edge", "--bg", 3],
  ["--error-edge", "--surface", 3],
  // The line of a border, and the outline of a pin, which is ink as the line is: both read
  // on the water, on land that has no fit and on every one of the five bands. The head of a
  // pin is cream with its number in ink, and amber where the pin is chosen: those are the
  // words of a page on its ground and the words of what is chosen on theirs, held above.
  ["--map-line", "--bg", 4.5],
  ["--map-line", "--map-water", 3],
  // The glints of the water are its second blue, and a line crosses them as it crosses the water.
  ["--map-line", "--map-glint", 3],
  ["--map-line", "--map-land", 3],
  ["--map-line", "--map-1", 3],
  ["--map-line", "--map-2", 3],
  ["--map-line", "--map-3", 3],
  ["--map-line", "--map-4", 3],
  ["--map-line", "--map-5", 3],
];

/** How far one band must be from the next, by the same formula. */
const NEXT_BAND = 1.35;

const { light, dark } = themes();
const written = asWritten();
const wide = writtenForAWideScreen();
const welcome = writtenWhereMovementIsWelcome();
const BANDS = [1, 2, 3, 4, 5].map((band) => `--map-${band}`);
/** The colour a token names, where it names one of the look: `var(--page)` gives `--page`. */
const named = (value: string | undefined) => /^var\((--[a-z]+)\)$/.exec(value ?? "")?.[1] ?? "";

/** True of five colours that may be the five bands, under a line of that colour. */
function mayBeTheBands(five: readonly string[], line: string): boolean {
  return five.every(
    (band, at) =>
      roundedDown(contrast(line, band)) >= 3 &&
      (at === 0 ||
        (contrast(five[at - 1] ?? "", band) >= NEXT_BAND && luminance(band) < luminance(five[at - 1] ?? ""))),
  );
}

/** Every way to take so many of a list, in the order of the list. */
const runs = (from: readonly string[], length: number): string[][] =>
  length === 0 ? [[]] : from.flatMap((first, at) => runs(from.slice(at + 1), length - 1).map((rest) => [first, ...rest]));

describe("the design tokens", () => {
  test("test_the_contrast_formula_gives_the_known_answers", () => {
    expect(contrast("#000000", "#ffffff")).toBeCloseTo(21, 5);
    expect(contrast("#ffffff", "#ffffff")).toBe(1);
    // The grey that only just passes for text on white.
    expect(roundedDown(contrast("#767676", "#ffffff"))).toBe(4.5);
    expect(roundedDown(contrast("#777777", "#ffffff"))).toBe(4.4);
  });

  test.each(PAIRS)(
    "test_every_colour_pair_has_the_contrast_it_needs: %s on %s needs %s",
    (token, against, needs) => {
      const [one, other] = [light[token], light[against]];

      expect([token, isColour(one ?? "")]).toEqual([token, true]);
      expect([against, isColour(other ?? "")]).toEqual([against, true]);
      expect(roundedDown(contrast(one ?? "", other ?? ""))).toBeGreaterThanOrEqual(needs);
    },
  );

  test("test_the_look_has_the_seventeen_colours_of_town_map_and_three_at_the_most_beside_them", () => {
    // A colour is written once, as one of the look. Everything else that is a colour names
    // one of them, so that no other can come in by another name.
    const writtenOut = Object.entries(written).filter(([, value]) => isColour(value));
    const others = Object.entries(written).filter(([name]) => isColour(light[name] ?? "") && !(name in THE_LOOK));

    expect(Object.keys(SEVENTEEN)).toHaveLength(17);
    expect(Object.keys(ADDED).length).toBeLessThanOrEqual(3);
    expect(Object.fromEntries(writtenOut)).toEqual(THE_LOOK);
    expect(others.length).toBeGreaterThan(20);
    expect(others.filter(([, value]) => !(named(value) in THE_LOOK)).map(([name]) => name)).toEqual([]);
  });

  test("test_each_colour_that_was_added_is_one_a_rule_of_contrast_cannot_be_met_without", () => {
    // The map has five bands of green, palest to deepest. Each is 1.35 from the next, and
    // the line of a border is 3 from every one. Of the greens of the seventeen, the two
    // palest are 1.28 apart and the line is 2.9 from the deepest: so no five of them do.
    const line = light["--map-line"] ?? "";
    const deepestFirst = (names: readonly string[]) =>
      names.map((name) => THE_LOOK[name] ?? "").sort((one, other) => luminance(other) - luminance(one));
    const fives = (names: readonly string[]) => runs(deepestFirst(names), 5).filter((five) => mayBeTheBands(five, line));
    const ofTheSeventeen = GREENS.filter((name) => name in SEVENTEEN);

    expect(GREENS.every((name) => name in THE_LOOK)).toBe(true);
    expect(roundedDown(contrast(SEVENTEEN["--lea"] ?? "", SEVENTEEN["--meadow"] ?? ""))).toBe(1.2);
    expect(roundedDown(contrast(line, SEVENTEEN["--hedge"] ?? ""))).toBe(2.9);
    expect(fives(ofTheSeventeen)).toEqual([]);
    // Nor do they with any two of the three that were added. With all three, one five does.
    for (const left of Object.keys(ADDED)) {
      expect([left, fives(GREENS.filter((name) => name !== left))]).toEqual([left, []]);
    }
    expect(fives(GREENS)).toEqual([BANDS.map((band) => light[band])]);
    // A colour that is added is for what it was added for: no token but a band of the map takes one.
    const taking = Object.entries(written).filter(([, value]) => named(value) in ADDED).map(([name]) => name);
    expect(taking.filter((name) => !BANDS.includes(name))).toEqual([]);
  });

  test("test_the_browns_are_gone_by_name_and_by_value_and_there_is_no_wall", () => {
    const css = withoutComments(readFileSync(TOKENS, "utf8"));
    const names = Object.keys(OF_THE_BROWNS).filter((name) => /^--[a-z]+$/.test(name));
    const values = Object.values(OF_THE_BROWNS).filter(isColour);

    expect([names.length, values.length]).toEqual([20, 20]);
    expect(names.filter((name) => new RegExp(`${name}(?![\\w-])`).test(css))).toEqual([]);
    expect(values.filter((value) => css.toLowerCase().includes(value))).toEqual([]);
  });

  test("test_brown_is_in_the_rabbit_and_his_burrow_and_nowhere_else", () => {
    // Fur and earth are drawn with. No token takes either, and no style sheet names either
    // but the one that draws the rabbit.
    const BROWN = ["--fur", "--earth"];
    const taking = Object.entries(written).filter(([, value]) => BROWN.includes(named(value)));
    const naming = styleSheets().filter(
      ([file, css]) => file !== "styles/tokens.css" && !/\/Burro\//.test(file) && BROWN.some((name) => css.includes(`var(${name})`)),
    );

    expect(taking.map(([name]) => name)).toEqual([]);
    expect(naming.map(([file]) => file)).toEqual([]);
  });

  test("test_no_style_sheet_writes_a_colour_that_is_not_one_of_the_look", () => {
    // A style sheet names a token. Where it writes a colour out, as the fill of a drawing
    // may, the colour is one of the look.
    const strays = styleSheets().flatMap(([file, css]) =>
      (css.match(/#[0-9a-f]{6}\b|#[0-9a-f]{3}\b/gi) ?? [])
        .filter((found) => !Object.values(THE_LOOK).includes(found.toLowerCase()))
        .map((found) => `${file} ${found}`),
    );

    expect(strays).toEqual([]);
  });

  test("test_every_token_a_page_names_is_one_that_is_given", () => {
    // A token that is named and not given draws nothing, and says nothing of it: words with
    // no colour of their own, an edge of no width. What a part hands its own style sheet
    // from its script is given there, by name. The parts of the kit are held by their own test.
    const given = new Set(
      styleSheets()
        .filter(([file]) => file.startsWith("styles/"))
        .flatMap(([, css]) => [...css.matchAll(/(?:^|[\s;{])(--[a-z0-9-]+)\s*:/g)].map(([, name]) => name ?? "")),
    );
    const lost = styleSheets()
      .filter(([file]) => !file.startsWith("components/kit/"))
      .flatMap(([file, css]) => {
        const own = new Set([...css.matchAll(/(?:^|[\s;{])(--[a-z0-9-]+)\s*:/g)].map(([, name]) => name ?? ""));
        const folder = path.dirname(path.join(SRC, file));
        const handed = readdirSync(folder)
          .filter((name) => /\.tsx?$/.test(name))
          .map((name) => readFileSync(path.join(folder, name), "utf8"))
          .join("\n");
        return [...css.matchAll(/var\(\s*(--[a-z0-9-]+)/g)]
          .map(([, name]) => name ?? "")
          .filter((name) => !given.has(name) && !own.has(name) && !handed.includes(`"${name}"`))
          .map((name) => `${file} ${name}`);
      });

    expect(given.size).toBeGreaterThan(60);
    expect([...new Set(lost)]).toEqual([]);
  });

  test("test_nothing_is_dimmed_because_a_dimmed_colour_is_not_the_colour_that_was_checked", () => {
    // Every pair above is worked out at full strength. Drawn at 70%, muted text on white
    // falls from 7.4 to 3.5 to 1, and an edge from 4.3 to 2.5. So nothing is drawn see-through:
    // a state is said in words. What must not be seen at all is hidden, not faded.
    const dimmed = styleSheets().flatMap(([file, css]) =>
      [...css.matchAll(/(^|[\s;{])(opacity|filter|backdrop-filter)\s*:\s*([^;}]+)/g)]
        .filter(([, , property, value]) => property !== "opacity" || Number.parseFloat(value ?? "") !== 1)
        .map(([, , property, value]) => `${file} ${property}: ${(value ?? "").trim()}`),
    );
    const seeThrough = styleSheets().flatMap(([file, css]) =>
      // A colour with a fourth part, in any of the ways of writing one.
      (css.match(/#[0-9a-f]{8}\b|#[0-9a-f]{4}\b|\b(rgba|hsla)\(|\b(rgb|hsl|oklch|lab)\([^)]*\/|color-mix\(/gi) ?? []).map(
        (found) => `${file} ${found}`,
      ),
    );

    expect(styleSheets().length).toBeGreaterThan(30);
    expect(dimmed).toEqual([]);
    expect(seeThrough).toEqual([]);
  });

  test("test_the_look_is_one_whatever_the_system_asks", () => {
    // The look has no dark colours. A page that followed the system would be drawn, where
    // the system asks for dark, in colours nobody chose and no test had checked.
    const asking = styleSheets().filter(([, css]) => /prefers-color-scheme|light-dark\(/.test(css));
    const told = [...readFileSync(TOKENS, "utf8").matchAll(/(?:^|[\s;{])color-scheme\s*:\s*([^;}]+)/g)].map(
      ([, value]) => (value ?? "").trim(),
    );

    expect(asking.map(([file]) => file)).toEqual([]);
    expect(dark).toEqual(light);
    // The browser is told the page is light, and only light: it draws its own parts light,
    // and is asked not to darken the page for a system that asks for dark.
    expect(told).toEqual(["only light"]);
    expect(styleSheets().filter(([file, css]) => file !== "styles/tokens.css" && /color-scheme\s*:/.test(css))).toEqual([]);
  });

  test("test_every_colour_that_is_used_is_checked_against_something", () => {
    const checked = new Set(PAIRS.flatMap(([token, against]) => [token, against]));
    const colours = Object.entries(light).filter(([name, value]) => isColour(value) && !(name in THE_LOOK));

    expect(colours.length).toBeGreaterThan(20);
    expect(colours.map(([name]) => name).filter((name) => !checked.has(name))).toEqual([]);
  });

  test("test_what_is_read_is_read_on_cream_and_never_on_the_grass", () => {
    // The ground of a page is a meadow. What is read on is not the ground: it is the cream
    // of a box, whichever token a part asks for it by.
    for (const token of ["--bg", "--surface", "--notice-bg", "--info-bg"]) {
      expect([token, written[token]]).toEqual([token, "var(--page)"]);
    }
    // Sand is a chip at rest and land with no fit. Of the colours words are set in, ink
    // alone reads on it, so no token that words are laid on takes it.
    expect(roundedDown(contrast(light["--muted"] ?? "", SEVENTEEN["--sand"] ?? ""))).toBeLessThan(4.5);
    expect(roundedDown(contrast(light["--accent"] ?? "", SEVENTEEN["--sand"] ?? ""))).toBeLessThan(4.5);
    expect(roundedDown(contrast(light["--text"] ?? "", SEVENTEEN["--sand"] ?? ""))).toBeGreaterThanOrEqual(4.5);
  });

  test("test_a_link_the_main_button_what_is_on_a_fault_and_a_trade_off_are_told_apart", () => {
    // Each is known by what is drawn and in which colour: no two are drawn the same way in
    // the same colour. A fault and a trade-off are both said in ink, as every sentence is,
    // so neither is known by its words: the one has an edge and the other a mark.
    const five = {
      "a link": ["words", written["--accent"]],
      "the main button": ["ground", written["--accent"]],
      "what is on": ["ground", written["--chosen"]],
      "a fault": ["edge", written["--error-edge"]],
      "a trade-off": ["mark", written["--tradeoff-mark"]],
    };
    const drawn = Object.values(five).map(([what, colour]) => `${what} ${colour}`);

    expect(five).toEqual({
      "a link": ["words", "var(--cobalt)"],
      "the main button": ["ground", "var(--cobalt)"],
      "what is on": ["ground", "var(--amber)"],
      "a fault": ["edge", "var(--poppy)"],
      "a trade-off": ["mark", "var(--poppy)"],
    });
    expect(new Set(drawn).size).toBe(5);
    // The two grounds are told apart by more than their hue.
    expect(roundedDown(contrast(light["--accent"] ?? "", light["--chosen"] ?? ""))).toBeGreaterThanOrEqual(3);
    // Poppy cannot be small words, so what is said of a fault and of a trade-off is in ink.
    expect(roundedDown(contrast(SEVENTEEN["--poppy"] ?? "", light["--bg"] ?? ""))).toBeLessThan(4.5);
    expect([written["--error"], written["--tradeoff"]]).toEqual(["var(--ink)", "var(--ink)"]);
  });

  test("test_land_is_green_and_water_is_blue", () => {
    expect(written["--map-water"]).toBe("var(--shallows)");
    expect(written["--map-land"]).toBe("var(--sand)");
    expect(BANDS.map((band) => named(written[band]))).toEqual(["--dew", "--meadow", "--verge", "--fern", "--ivy"]);
    expect(BANDS.map((band) => GREENS.includes(named(written[band])))).toEqual([true, true, true, true, true]);
    // Green and blue, by which of the three lights is the strongest in each.
    const strongest = (colour: string) => {
      const [red = 0, green = 0, blue = 0] = [1, 3, 5].map((at) => parseInt(colour.slice(at, at + 2), 16));
      return green >= red && green >= blue ? "green" : blue > red ? "blue" : "red";
    };
    expect(BANDS.map((band) => strongest(light[band] ?? ""))).toEqual(["green", "green", "green", "green", "green"]);
    expect(luminance(light["--map-water"] ?? "")).toBeGreaterThan(0);
    const [red = 0, , blue = 0] = [1, 3, 5].map((at) => parseInt((light["--map-water"] ?? "").slice(at, at + 2), 16));
    expect(blue).toBeGreaterThan(red);
  });

  test("test_one_band_can_be_told_from_the_next_and_each_is_darker_than_the_one_before", () => {
    // The bands are never the only signal, and still each must differ from the next. Seen
    // in a browser: the three in the middle were so near in tone that a map read as one colour.
    const bands = BANDS.map((band) => light[band] ?? "");

    for (let at = 1; at < bands.length; at += 1) {
      expect(contrast(bands[at - 1] ?? "", bands[at] ?? "")).toBeGreaterThanOrEqual(NEXT_BAND);
      // The page says that the darker an area is, the nearer it is to the high end.
      expect(luminance(bands[at] ?? "")).toBeLessThan(luminance(bands[at - 1] ?? ""));
    }
    expect(mayBeTheBands(bands, light["--map-line"] ?? "")).toBe(true);
  });

  test("test_the_ground_is_a_picture_of_the_websites_own_laid_at_two_pixels_to_one_of_its_own", () => {
    expect(written["--ground"]).toBe('url("/art/ground.png")');
    expect(written["--px-ground"]).toBe("2px");
    // It is the same on a wide screen: a tile is as large there as on a phone.
    expect(Object.keys(wide).filter((name) => /ground/.test(name))).toEqual([]);
  });

  test("test_a_box_is_a_picture_cut_in_nine_a_hard_shadow_and_under_them_a_plain_edge_of_ink", () => {
    expect(written["--frame-box"]).toBe('url("/art/frame-box.png")');
    expect(written["--frame-box-on"]).toBe('url("/art/frame-box-on.png")');
    // Two art pixels down and two to the right, with no blur and nothing spread.
    expect(written["--box-shadow"]).toBe("calc(var(--px) * 2) calc(var(--px) * 2) 0 var(--shade)");
    expect(written["--edge"]).toBe("var(--px)");
  });

  test("test_a_name_is_set_at_one_of_four_sizes_and_a_sentence_at_fifteen_to_seventeen_pixels", () => {
    // In pixels, where the size of type in the browser is as it came: 16 to the rem. The
    // face of a name is drawn on a grid of ten, so at a size that ten divides a pixel of it
    // is a whole number of pixels of the screen.
    const pixels = (token: string) => Number.parseFloat(light[token] ?? "") * (/rem$/.test(light[token] ?? "") ? 16 : Number.NaN);

    expect(["--name-1", "--name-2", "--name-3", "--name-4"].map(pixels)).toEqual([20, 30, 40, 60]);
    expect(["--size-small", "--size-body", "--size-lead"].map(pixels)).toEqual([15, 16, 17]);
  });

  test("test_a_heading_in_the_face_of_names_is_never_smaller_than_thirty_pixels", () => {
    // Seen in a browser: at 20 pixels the face of a name reads as small as a sentence at
    // 13, and a heading set so was lighter to the eye than the label of a field beside it.
    const HEADINGS = ["--size-h2", "--size-h1"];

    expect(HEADINGS.map((token) => written[token])).toEqual(["var(--name-2)", "var(--name-3)"]);
    expect(HEADINGS.map((token) => wide[token])).toEqual(["var(--name-3)", "var(--name-4)"]);
    for (const size of [...HEADINGS.map((token) => light[token]), ...HEADINGS.map((token) => wide[token])]) {
      expect(size).not.toBe("var(--name-1)");
    }
  });

  test("test_there_are_two_faces_and_each_falls_back_to_one_the_system_has", () => {
    // Which face a sentence is set in is said in the style sheets and nowhere else, so
    // that it may be changed there: no test names it.
    expect(light["--font-name"]).toMatch(/^"Jersey 10", .+, monospace$/);
    expect(light["--font-say"]).toMatch(/^"[A-Z][A-Za-z0-9 ]+", .+, sans-serif$/);
    expect(light["--font-say"]).not.toContain("Jersey");
    // What the style sheets of the website name today is the face of a sentence, and what
    // they name for an id is too: there is no third face.
    expect([written["--font"], written["--font-mono"]]).toEqual(["var(--font-say)", "var(--font-say)"]);
    expect(light["--font"]).toBe(light["--font-say"]);
    expect(Object.entries(written).filter(([name]) => name.startsWith("--font")).map(([name]) => name).sort()).toEqual([
      "--font",
      "--font-mono",
      "--font-name",
      "--font-say",
    ]);
  });

  test("test_one_pixel_of_a_drawing_is_two_of_the_screen_and_three_on_a_wide_one", () => {
    expect([light["--px"], wide["--px"]]).toEqual(["2px", "3px"]);
    // Never a fraction, and nowhere a third figure: a drawing shown at a fraction is blurred.
    expect([...readFileSync(TOKENS, "utf8").matchAll(/--px:\s*([^;]+);/g)].map(([, value]) => value)).toEqual(["2px", "3px"]);
    // Burro centre stage is larger than any other drawing, at every width.
    expect([written["--px-stage"], wide["--px-stage"]]).toEqual(["5px", undefined]);
  });

  test("test_no_corner_is_rounded", () => {
    expect([light["--radius"], light["--radius-card"]]).toEqual(["0px", "0px"]);
  });

  test("test_nothing_moves_unless_the_system_says_motion_is_welcome", () => {
    // Every length of a movement is a token, and every one is nought until the system says
    // that movement is welcome. A movement that is given no length there never runs.
    const lengths = Object.keys(written).filter((name) => name.startsWith("--motion-") && name !== "--motion-step");

    expect(lengths.sort()).toEqual(["--motion-drop", "--motion-fast", "--motion-hop", "--motion-press", "--motion-slow"]);
    expect(lengths.map((name) => written[name])).toEqual(lengths.map(() => "0ms"));
    expect(Object.keys(welcome).sort()).toEqual(lengths);
    expect(welcome).toMatchObject({ "--motion-fast": "120ms", "--motion-slow": "200ms" });
    for (const name of lengths) expect([name, /^[1-9]\d*ms$/.test(welcome[name] ?? "")]).toEqual([name, true]);
  });

  test("test_the_rabbit_hops_in_about_a_second_and_a_quarter_a_chip_drops_in_four_steps_and_a_press_is_felt_at_once", () => {
    const length = (name: string) => Number.parseInt(welcome[name] ?? "", 10);

    // The founder asked for the hop to be slowed a little: a round was a second.
    expect(length("--motion-hop")).toBeGreaterThanOrEqual(1200);
    expect(length("--motion-hop")).toBeLessThanOrEqual(1350);
    // Four steps, each held as long as a frame of the rabbit is: a tenth of a second.
    expect(length("--motion-drop") % 4).toBe(0);
    expect(length("--motion-drop")).toBeLessThanOrEqual(400);
    // What answers a press within a tenth of a second is felt as the press itself.
    expect(length("--motion-press")).toBeLessThanOrEqual(100);
  });

  test("test_what_moves_moves_in_held_frames_and_is_never_eased", () => {
    expect(light["--motion-step"]).toMatch(/^steps\(\d+, (end|start|jump-[a-z]+)\)$/);
  });

  test("test_a_control_is_never_smaller_than_twenty_four_pixels", () => {
    expect(parseInt(light["--target-min"] ?? "0", 10)).toBeGreaterThanOrEqual(24);
    expect(parseInt(light["--target"] ?? "0", 10)).toBeGreaterThanOrEqual(44);
  });
});
