/**
 * What the page of an area is drawn with: the drawings its style sheet lays, each with its
 * size in art pixels, as the list of drawings gives it. A style sheet names no picture of
 * its own: it is handed each by name, and lays it at its own size times the art pixel.
 *
 * It is handed once, on the page itself, and everything the page holds has it from there:
 * the parts that are closed until they are pressed, and the census and the household income
 * among them, which take the look of their fold and of their one button from the page.
 */

import type { CSSProperties } from "react";

import { cutOf, pictureOf, sizeOf, type Drawing } from "../kit/drawings";
import { picturesOf } from "../kit/Press/kinds";

/** The arrow of a fold. It is drawn pointing up, and the style sheet turns it. */
const ARROW: Drawing = "ui-arrow";

export function drawnWith(): CSSProperties {
  const arrow = sizeOf(ARROW);
  // A button that tries again is a plain button of the look, and holds no state.
  const { up, down } = picturesOf("plain", false);
  // Where the picture of a button is cut in nine, as the drawing says it: top, right, foot, left.
  const [top = 0, right = 0, foot = 0, left = 0] = cutOf(up) ?? [];
  return {
    "--arrow": `url("${pictureOf(ARROW)}")`,
    "--arrow-w": arrow.width,
    "--arrow-h": arrow.height,
    "--button": `url("${pictureOf(up)}")`,
    "--button-down": `url("${pictureOf(down)}")`,
    "--button-top": top,
    "--button-right": right,
    "--button-foot": foot,
    "--button-left": left,
  } as CSSProperties;
}
