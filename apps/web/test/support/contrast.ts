/**
 * The contrast ratio of two colours, by the WCAG formula, and the tokens of
 * a theme as tokens.css states them.
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

/** The tokens of the light theme and of the dark one, each whole. */
export function themes(): { light: Theme; dark: Theme } {
  const css = readFileSync(TOKENS, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const light = declarations(blockAfter(css, /:root\s*\{/));
  const dark = declarations(blockAfter(css, /@media\s*\(prefers-color-scheme:\s*dark\)\s*\{/));
  return { light, dark: { ...light, ...dark } };
}

export function isColour(value: string): boolean {
  return /^#[0-9a-f]{6}$/i.test(value);
}
