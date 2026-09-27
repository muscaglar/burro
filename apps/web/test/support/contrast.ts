/**
 * The contrast ratio of two colours, by the WCAG formula, and the tokens as
 * tokens.css states them.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

export type Theme = Readonly<Record<string, string>>;

const TOKENS = path.resolve(__dirname, "..", "..", "src", "styles", "tokens.css");

function channel(value: number): number {
  const share = value / 255;
  return share <= 0.04045 ? share / 12.92 : ((share + 0.055) / 1.055) ** 2.4;
}

export function luminance(hex: string): number {
  const match = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex);
  if (!match) throw new Error(`Not a colour in six hex digits: ${hex}`);
  const [red, green, blue] = match.slice(1).map((pair) => channel(parseInt(pair, 16)));
  return 0.2126 * (red ?? 0) + 0.7152 * (green ?? 0) + 0.0722 * (blue ?? 0);
}

export function contrast(one: string, other: string): number {
  const [lighter, darker] = [luminance(one), luminance(other)].sort((a, b) => b - a);
  return ((lighter ?? 0) + 0.05) / ((darker ?? 0) + 0.05);
}

/** Rounded down to one decimal, so that a ratio is never said to be more than it is. */
export function roundedDown(ratio: number): number {
  return Math.floor(ratio * 10) / 10;
}

function declarations(block: string): Record<string, string> {
  const found: Record<string, string> = {};
  for (const [, name, value] of block.matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)) {
    if (name && value) found[name] = value.trim();
  }
  return found;
}

function blockAfter(css: string, opening: RegExp): string {
  const start = opening.exec(css);
  if (!start) throw new Error(`tokens.css has no block matching ${opening}`);
  const from = start.index + start[0].length;
  let depth = 1;
  for (let at = from; at < css.length; at += 1) {
    if (css[at] === "{") depth += 1;
    if (css[at] === "}") depth -= 1;
    if (depth === 0) return css.slice(from, at);
  }
  throw new Error("tokens.css has a block that is never closed");
}

/** What each token comes to: one that names another, as `var(--chalk)` does, takes its value. */
function followed(found: Theme): Theme {
  const valueOf = (value: string, seen: readonly string[] = []): string => {
    const named = /^var\((--[a-z0-9-]+)\)$/.exec(value)?.[1];
    if (named === undefined || seen.includes(named)) return value;
    const next = found[named];
    return next === undefined ? value : valueOf(next, [...seen, named]);
  };
  return Object.fromEntries(Object.entries(found).map(([name, value]) => [name, valueOf(value)]));
}

const withoutComments = () => readFileSync(TOKENS, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const FOR_DARK = /@media\s*\(prefers-color-scheme:\s*dark\)\s*\{/;

/** The tokens as tokens.css writes them: one that names another still names it. */
export function asWritten(): Theme {
  return declarations(blockAfter(withoutComments(), /:root\s*\{/));
}

/** What tokens.css writes anew for a screen that is 60rem wide or wider. */
export function writtenForAWideScreen(): Theme {
  return declarations(blockAfter(withoutComments(), /@media\s*\(min-width:\s*60rem\)\s*\{/));
}

/** What tokens.css writes anew where the system says that movement is welcome. */
export function writtenWhereMovementIsWelcome(): Theme {
  return declarations(blockAfter(withoutComments(), /@media\s*\(prefers-reduced-motion:\s*no-preference\)\s*\{/));
}

/**
 * The tokens as a page has them where the system asks for light, and where it asks for
 * dark, each whole and each with its value. The website has one look, so the two are the
 * same: they differ only if tokens.css is given values for dark again.
 */
export function themes(): { light: Theme; dark: Theme } {
  const css = withoutComments();
  const light = asWritten();
  const dark = FOR_DARK.test(css) ? declarations(blockAfter(css, FOR_DARK)) : {};
  return { light: followed(light), dark: followed({ ...light, ...dark }) };
}

export function isColour(value: string): boolean {
  return /^#[0-9a-f]{6}$/i.test(value);
}
