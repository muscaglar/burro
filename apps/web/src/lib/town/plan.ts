/**
 * The rule a town is built by: from four bands to what is drawn.
 *
 * It takes the four bands and nothing else: no name, no rank and no fit. So two areas with
 * the same four bands are drawn the same, and nothing in a town says that one area is
 * better than another. A tall town is not a better town, and a town with its lights on is
 * not a better town.
 *
 * | Part | Band 1 | Band 5 | Not known |
 * |---|---|---|---|
 * | Trees | one tree | five | no tree, and a ring of dots where one would stand |
 * | Height | four houses | four blocks | no building: four plots, marked out and bare |
 * | Lit windows | one window of the town | every window | every window dark |
 * | Roofs | every roof newer | every roof older | no roof, and every wall closed by a line of dashes |
 *
 * What is not known is left blank. It is never drawn as the middle band, and never as the
 * least: every band draws something of its part, the first among them, so that a part
 * with nothing in it can only say that nothing is known of it.
 *
 * A window and a roof are drawn on a building. Where the height is not known there is no
 * building, and neither is drawn, whatever is known of them. `stateOf` says so, and the
 * words of the drawing say it after it.
 */

import type { BandNumber } from "@/content/bands";

import type { Bands } from "./bands";
import type { Part } from "./vibes";

/** How tall a building is: a house, a terrace, or a block of flats. */
export type Form = "low" | "mid" | "tall";

/** What roof a building has: flat and newer, or pitched and older. */
export type Roof = "newer" | "older";

export interface Building {
  readonly form: Form;
  /** `null` where nothing is known of the roofs: it has none. */
  readonly roof: Roof | null;
  /** How many of its windows are lit. `null` where nothing is known of the windows: all are dark. */
  readonly lit: number | null;
}

/** What is drawn of a town. */
export interface Plan {
  /** How many trees stand in front of the buildings. `null` where nothing is known of trees. */
  readonly trees: number | null;
  /** The buildings, from the left. `null` where nothing is known of their height. */
  readonly buildings: readonly Building[] | null;
}

/**
 * Whether a part is drawn. `blank`: nothing is known of it, and it is left blank. `unbuilt`:
 * it is known, and is drawn on a building, and there is no building to draw it on.
 */
export type State = "drawn" | "blank" | "unbuilt";

/** How many buildings a town has. It is the same for every town. */
export const LOTS = 4;

/** How many floors a building has, its ground floor among them. */
export const FLOORS: Readonly<Record<Form, number>> = { low: 2, mid: 3, tall: 5 };

/** How many windows a building has: two to each floor over its door. `pieces.test.ts` holds it to the drawings. */
export const WINDOWS: Readonly<Record<Form, number>> = { low: 2, mid: 4, tall: 8 };

/** How many trees, for each band of the vibe that is trees. Never none. */
const TREES: Readonly<Record<BandNumber, number>> = { 1: 1, 2: 2, 3: 3, 4: 4, 5: 5 };

/**
 * How tall each building is, from the left, for each band of the vibe that is height. The
 * two ends are all of one kind. Between them a town is mixed, as such an area is, and with
 * every band some building is taller and none is lower.
 */
const FORMS: Readonly<Record<BandNumber, readonly Form[]>> = {
  1: ["low", "low", "low", "low"],
  2: ["low", "mid", "low", "mid"],
  3: ["low", "tall", "mid", "mid"],
  4: ["mid", "tall", "mid", "tall"],
  5: ["tall", "tall", "tall", "tall"],
};

/** How many roofs are older, for each band of the vibe that is roofs. The rest are newer. */
const OLDER: Readonly<Record<BandNumber, number>> = { 1: 0, 2: 1, 3: 2, 4: 3, 5: 4 };

/**
 * The buildings in the order they take what is shared out: an older roof, and a lit
 * window. Never from the left, so that a town half of whose roofs are older is not a town
 * with an old end and a new one.
 */
const TURNS: readonly number[] = [1, 3, 0, 2];

const sum = (counts: readonly number[]) => counts.reduce((total, count) => total + count, 0);

/**
 * How many windows of a town are lit. One at the least, which is the least that can be
 * drawn and is not none. Then a quarter, a half, three quarters, and all of them.
 */
export function litOf(band: BandNumber, windows: number): number {
  return Math.max(1, Math.round((windows * (band - 1)) / 4));
}

/**
 * The lit windows of a town, shared among its buildings. Every window of the town is put
 * in one order, by how far through the windows of its own building it is, and the first
 * so many are lit. So each building is lit about as far as the town is, and with every
 * window more no building has fewer.
 */
function shared(lit: number, windows: readonly number[]): readonly number[] {
  const every = windows.flatMap((count, lot) =>
    Array.from({ length: count }, (_, at) => ({ lot, through: (at + 0.5) / count })),
  );
  every.sort((one, other) => one.through - other.through || TURNS.indexOf(one.lot) - TURNS.indexOf(other.lot));
  const taken = windows.map(() => 0);
  for (const { lot } of every.slice(0, lit)) taken[lot] = (taken[lot] ?? 0) + 1;
  return taken;
}

/** What is drawn of a town, from its four bands. */
export function planOf(bands: Bands): Plan {
  const forms = bands.height === null ? null : FORMS[bands.height];
  if (forms === null) return { trees: bands.trees === null ? null : TREES[bands.trees], buildings: null };

  const windows = forms.map((form) => WINDOWS[form]);
  const lit = bands.lit === null ? null : shared(litOf(bands.lit, sum(windows)), windows);
  const older = bands.roofs === null ? null : TURNS.slice(0, OLDER[bands.roofs]);
  return {
    trees: bands.trees === null ? null : TREES[bands.trees],
    buildings: forms.map((form, lot) => ({
      form,
      roof: older === null ? null : older.includes(lot) ? "older" : "newer",
      lit: lit === null ? null : (lit[lot] ?? 0),
    })),
  };
}

/** Whether a part of a town is drawn, left blank, or has no building to be drawn on. */
export function stateOf(bands: Bands, part: Part): State {
  if (bands[part] === null) return "blank";
  if ((part === "lit" || part === "roofs") && bands.height === null) return "unbuilt";
  return "drawn";
}
