/**
 * What the style sheet of the settings is handed of a drawing, so that it names none
 * itself. It is plain code with no state, kept apart from the parts that run in the
 * browser: what a page drawn on the server takes from a file that runs in the browser is
 * a component and nothing else.
 *
 * A drawing is named here only where it is the one of its kind: the button a choice is
 * drawn as, and the arrow of a list. The drawing of a vibe, a family, a group of measures
 * or an end of a gauge is chosen by the id the API gives, by the kit.
 */

import type { CSSProperties } from "react";

import type { Family, Metric } from "@/lib/api/schema";

import { cutOf, pictureOf, sizeOf, type Drawing } from "../kit/drawings";
import { picturesOf } from "../kit/Press/kinds";
import type { ThingOf } from "../kit/Thing/drawn";

const served = (name: Drawing) => `url("${pictureOf(name)}")`;

/**
 * A choice that is drawn as a button: its picture at rest and chosen, each of them
 * pressed, and where they are cut in nine. What is chosen is amber, as what is on is.
 */
export function ofAChoice(): CSSProperties {
  const rest = picturesOf("plain", false);
  const chosen = picturesOf("plain", true);
  const [top, right, foot, left] = cutOf(rest.up) ?? [0, 0, 0, 0];
  return {
    "--art": served(rest.up),
    "--art-down": served(rest.down),
    "--art-on": served(chosen.up),
    "--art-on-down": served(chosen.down),
    "--cut-top": top,
    "--cut-right": right,
    "--cut-foot": foot,
    "--cut-left": left,
  } as CSSProperties;
}

/** The arrow of a list that opens, which the style sheet turns to point down: its picture and its size. */
export function ofTheArrow(): CSSProperties {
  const { width, height } = sizeOf("ui-arrow");
  return { "--art": served("ui-arrow"), "--w": width, "--h": height } as CSSProperties;
}

/** The thing a family of vibes is drawn by: the drawing of the family, and the plain one where it has none. */
export function ofAFamily(family: Family | null): ThingOf {
  return { kind: "feature", family };
}

/**
 * The thing a group of measures is drawn by, where it is the group of no family of vibes:
 * the measures the API puts in none, and those the settings show apart from theirs. It is
 * drawn as a family is, by the dimension the API gives what it holds, which is read off
 * the measures and written nowhere. Measures of more dimensions than one have no one
 * drawing between them, and their group is drawn by the plain one.
 */
export function ofADimension(measures: readonly Pick<Metric, "dimension">[]): ThingOf {
  const [one, ...others] = [...new Set(measures.map((metric) => metric.dimension))];
  return { kind: "feature", family: one !== undefined && others.length === 0 ? one : null };
}
