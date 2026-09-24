/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { contrast, isColour, roundedDown, themes } from "./support/contrast";

const SRC = path.resolve(__dirname, "..", "src");

/** Every style sheet of the website, with what is said in comments taken out. */
function styleSheets(folder = SRC): [file: string, css: string][] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry): [string, string][] => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return styleSheets(file);
    if (!entry.name.endsWith(".css")) return [];
    return [[path.relative(SRC, file), readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\//g, "")]];
  });
}

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
  ["--notice-text", "--notice-bg", 4.5],
  ["--notice-edge", "--notice-bg", 3],
  ["--info-text", "--info-bg", 4.5],
  ["--tradeoff", "--bg", 4.5],
  ["--tradeoff", "--surface", 4.5],
  ["--good", "--bg", 4.5],
  ["--good", "--surface", 4.5],
  ["--error", "--bg", 4.5],
  ["--error", "--surface", 4.5],
  ["--map-line", "--bg", 4.5],
  ["--map-line", "--map-water", 3],
  ["--map-line", "--map-land", 3],
  ["--map-line", "--map-1", 3],
  ["--map-line", "--map-2", 3],
  ["--map-line", "--map-3", 3],
  ["--map-line", "--map-4", 3],
  ["--map-line", "--map-5", 3],
];

const { light, dark } = themes();
const CASES = (["light", "dark"] as const).flatMap((theme) =>
  PAIRS.map(([token, against, needs]) => [theme, token, against, needs] as const),
);

describe("the design tokens", () => {
  test("test_the_contrast_formula_gives_the_known_answers", () => {
    expect(contrast("#000000", "#ffffff")).toBeCloseTo(21, 5);
    expect(contrast("#ffffff", "#ffffff")).toBe(1);
    // The grey that only just passes for text on white.
    expect(roundedDown(contrast("#767676", "#ffffff"))).toBe(4.5);
    expect(roundedDown(contrast("#777777", "#ffffff"))).toBe(4.4);
  });

  test.each(CASES)(
    "test_every_colour_pair_has_the_contrast_it_needs: %s %s on %s needs %s",
    (theme, token, against, needs) => {
      const tokens = theme === "light" ? light : dark;
      const [one, other] = [tokens[token], tokens[against]];

      expect([token, isColour(one ?? "")]).toEqual([token, true]);
      expect([against, isColour(other ?? "")]).toEqual([against, true]);
      expect(roundedDown(contrast(one ?? "", other ?? ""))).toBeGreaterThanOrEqual(needs);
    },
  );

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

  test("test_every_colour_has_a_dark_value_of_its_own", () => {
    const css = readFileSync(
      path.resolve(__dirname, "..", "src", "styles", "tokens.css"),
      "utf8",
    );
    const darkBlock = css.slice(css.indexOf("prefers-color-scheme: dark"));
    const colours = Object.entries(light).filter(([, value]) => isColour(value));

    const missing = colours.filter(([name]) => !darkBlock.includes(`${name}:`));

    expect(colours.length).toBeGreaterThan(20);
    expect(missing.map(([name]) => name)).toEqual([]);
  });

  test("test_every_colour_that_is_used_is_checked_against_something", () => {
    const checked = new Set(PAIRS.flatMap(([token, against]) => [token, against]));
    const colours = Object.entries(light).filter(([, value]) => isColour(value));

    expect(colours.map(([name]) => name).filter((name) => !checked.has(name))).toEqual([]);
  });

  test("test_one_score_band_can_be_told_from_the_next_in_both_themes", () => {
    // The bands are never the only signal, and still each must differ from the next.
    for (const tokens of [light, dark]) {
      const bands = [1, 2, 3, 4, 5].map((band) => tokens[`--map-${band}`] ?? "");
      for (let at = 1; at < bands.length; at += 1) {
        expect(contrast(bands[at - 1] ?? "", bands[at] ?? "")).toBeGreaterThanOrEqual(1.15);
      }
    }
  });

  test("test_nothing_moves_unless_the_system_says_motion_is_welcome", () => {
    expect([light["--motion-fast"], light["--motion-slow"]]).toEqual(["0ms", "0ms"]);
    const css = readFileSync(
      path.resolve(__dirname, "..", "src", "styles", "tokens.css"),
      "utf8",
    );
    const welcome = css.slice(css.indexOf("prefers-reduced-motion: no-preference"));
    expect(welcome).toContain("--motion-fast: 120ms");
    expect(welcome).toContain("--motion-slow: 200ms");
  });

  test("test_a_control_is_never_smaller_than_twenty_four_pixels", () => {
    expect(parseInt(light["--target-min"] ?? "0", 10)).toBeGreaterThanOrEqual(24);
    expect(parseInt(light["--target"] ?? "0", 10)).toBeGreaterThanOrEqual(44);
  });
});
