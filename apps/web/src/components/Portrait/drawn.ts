/**
 * What the portrait is drawn with: the drawings its style sheet lays, each with its size in
 * art pixels, as the list of drawings gives it. A style sheet names no picture of its own:
 * it is handed each by name, and lays it at its own size times the art pixel.
 */

import type { CSSProperties } from "react";

import { pictureOf, sizeOf, type Drawing } from "../kit/drawings";

/** The arrow of what opens. It is drawn pointing up, and the style sheet turns it. */
const ARROW: Drawing = "ui-arrow";
/** The key of a source, before what opens the sources of what is said in short. */
const KEY: Drawing = "ui-key";

export function drawnWith(): CSSProperties {
  const arrow = sizeOf(ARROW);
  const key = sizeOf(KEY);
  return {
    "--arrow": `url("${pictureOf(ARROW)}")`,
    "--arrow-w": arrow.width,
    "--arrow-h": arrow.height,
    "--key": `url("${pictureOf(KEY)}")`,
    "--key-w": key.width,
    "--key-h": key.height,
  } as CSSProperties;
}
