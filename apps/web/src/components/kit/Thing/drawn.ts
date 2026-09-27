/**
 * Which drawing stands for a thing of a search. It is plain code with no state, so a page
 * built on the server and a part drawn in the browser choose the same one.
 *
 * A thing is never drawn as nothing. A vibe has a drawing named for the id the service
 * gives it. Whatever has no drawing of its own is drawn by its family, which the service
 * names, and whatever has no family that is drawn, by the plain one. Each name below that
 * is written out is held to the list of drawings by its type: one that is not drawn is a
 * fault when the website is built, and not a gap on the page.
 *
 * A group of measures that the service puts in no family of vibes is drawn as a family is,
 * by the dimension the service gives its measures: whatever draws the group hands that on
 * as its family.
 *
 * The drawing is dress. The name beside it is the service's, and no name of a vibe, a
 * measure or a place is written here.
 */

import { inAName, isDrawn, type Drawing } from "../drawings";

/**
 * What a thing of a search is. The first seven are the kinds of a chip, by the same names.
 * `home` is the kind of home that is looked for, and `alike` is an area to be like.
 */
export type ThingKind = "place" | "budget" | "tenure" | "tag" | "feature" | "area" | "usual" | "home" | "alike";

export const THING_KINDS: readonly ThingKind[] = [
  "place",
  "budget",
  "tenure",
  "tag",
  "feature",
  "area",
  "usual",
  "home",
  "alike",
];

/**
 * `said`: a person said it. `assumed`: it is in the search, and nobody said it, or not the
 * whole of it. `off`: it is in the search and counts for nothing.
 */
export type ThingState = "said" | "assumed" | "off";

export const THING_STATES: readonly ThingState[] = ["said", "assumed", "off"];

export interface ThingOf {
  readonly kind: ThingKind;
  /** The id the service gives, of a vibe or a measure. Left out of a thing that is the one of its kind. */
  readonly id?: string | null;
  /**
   * The family the service puts a vibe or a measure in. `null` where it names none. Of a
   * group of measures that is of no family of vibes, the dimension the service gives them.
   */
  readonly family?: string | null;
}

/** What is drawn for whatever has no drawing of its own and no family that has one. */
export const PLAIN: Drawing = "thing-plain";

const OF_A_KIND: Readonly<Record<Exclude<ThingKind, "tag" | "feature">, Drawing>> = {
  place: "thing-journey",
  budget: "thing-budget",
  tenure: "thing-tenure",
  area: "thing-area",
  usual: "thing-usual",
  home: "thing-home",
  alike: "thing-alike",
};

/** What follows the name of a drawing in the name of the same drawing in outline. */
const OFF = "-off";

/** The names that are those of a kind, and of what stands for a family. No vibe is drawn by one, whatever it is called. */
const KEPT = new Set<string>([...Object.values(OF_A_KIND), PLAIN]);

const named = (name: string): Drawing | null => (isDrawn(name) ? name : null);

/** What begins the name of the thing of a family, and of a group of measures that is drawn as one. */
const OF_A_FAMILY = "thing-family-";

/** What begins the name of the drawing of a vibe, where the name its id gives stands for something else. */
const OF_A_VIBE = "thing-vibe-";

/**
 * The drawing of a vibe, by the id the service gives it: `thing-leafy` for `leafy`. `null`
 * where it has none of its own.
 *
 * It is never the drawing of a kind, of a family or of another vibe, whatever the vibe is
 * called. Where the name its id gives would be one of those, its own drawing is named for
 * a vibe outright, `thing-vibe-` and its id: so a vibe whose id begins as the thing of a
 * family does is drawn by its own drawing, and not by its family's.
 */
function ofVibe(id: string | null): Drawing | null {
  if (id === null || id === "") return null;
  const name = `thing-${inAName(id)}`;
  // Nor is it drawn by the outline of another thing, which is a drawing too.
  if (name.endsWith(OFF)) return null;
  const isAnothers = KEPT.has(name) || name.startsWith(OF_A_FAMILY) || name.startsWith(OF_A_VIBE);
  return named(isAnothers ? `${OF_A_VIBE}${inAName(id)}` : name);
}

/** The drawing of a family. `null` where the family is not drawn, or there is none. */
function ofFamily(family: string | null): Drawing | null {
  return family === null || family === "" ? null : named(`${OF_A_FAMILY}${inAName(family)}`);
}

/**
 * The drawing of a thing in outline, its colour taken off it, which is what is drawn for a
 * thing that counts for nothing. `null` of a drawing that has none: the style sheet then
 * cuts the outline out of the drawing itself.
 */
export function outlineOf(drawing: Drawing): Drawing | null {
  return named(`${drawing}${OFF}`);
}

/** The drawing that stands for a thing: its own, or its family's, or the plain one, and never nothing. */
export function drawingOf({ kind, id = null, family = null }: ThingOf): Drawing {
  switch (kind) {
    case "tag":
      return ofVibe(id) ?? ofFamily(family) ?? PLAIN;
    case "feature":
      // A measure is drawn by its family, and never by a drawing that happens to bear its id.
      return ofFamily(family) ?? PLAIN;
    default:
      return OF_A_KIND[kind];
  }
}
