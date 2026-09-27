/**
 * Where each piece of a town is drawn, on a canvas of one size for every town.
 *
 * The rule says what is drawn, in `plan.ts`. This says where: every length here is in art
 * pixels, counted from the top left of the canvas, and nothing here knows a band. A town
 * is the plot, then what is built on it from the left, then what stands in front.
 *
 * Nothing that stands in front hides a window. A tree is lower than the lowest window of
 * the lowest building, so every window that is lit is in sight, and can be counted.
 */

import { ART, type ArtName, type Drawn } from "@/lib/art/names";

import { LOTS, type Form, type Plan, type Roof } from "./plan";

/** One drawing, or one frame of a strip, and where its top left stands on the canvas. */
export interface Piece {
  readonly drawing: ArtName;
  /** Which frame of the drawing, counted from nought. */
  readonly frame: number;
  readonly left: number;
  readonly top: number;
}

const PLOT = "town-plot" satisfies ArtName;
/** A plot that is marked out and not built on. */
const LOT = "town-lot" satisfies ArtName;
const ROOFS = "town-roofs" satisfies ArtName;
const TREES = "town-trees" satisfies ArtName;
/** A wall, by how tall it is. The first frame is the wall with dark windows, and then one for each count that is lit, from none. */
const WALL = { low: "town-low", mid: "town-mid", tall: "town-tall" } as const satisfies Record<Form, ArtName>;

/**
 * The frames of each roof. There are two of a kind, and which one a building has is by
 * where it stands, so that a row of them is no row of one stamp. The first frame of the
 * strip is no roof: the wall closed by a line of dashes.
 */
const ROOF_FRAMES: Readonly<Record<Roof, readonly number[]>> = { newer: [1, 2], older: [3, 4] };
const NO_ROOF = 0;
/** The frames of the two trees, by where a tree stands. The first frame of the strip is the ring where a tree would stand. */
const TREE_FRAMES: readonly number[] = [1, 2];

/** One of a kind, by where a thing stands: the first, then the second, and round again. */
const byPlace = (frames: readonly number[], place: number): number => frames[place % frames.length] ?? 0;

/** The canvas of a town, which is the size of its plot. */
export const CANVAS = { width: ART[PLOT].width, height: ART[PLOT].height } as const;

/** The row the buildings stand on, and the row the trees stand on, in front of them. */
const GROUND = 21;
const FOOT = 28;

/** Where each building begins, from the left: its roof, which stands one art pixel past its wall. */
const LOT_AT: readonly number[] = [2, 15, 28, 41];

/**
 * The places a tree may stand in, from the left, and the order they are taken in. The
 * first and the last stand as near the edge of the plot as a tree and its shade may, and
 * no nearer: nothing that stands on the plot is drawn over its edge.
 */
const PLACE_AT: readonly number[] = [1, 12, 23, 34, 44];
const TAKEN: readonly number[] = [0, 3, 1, 4, 2];
/** Where the ring stands that marks a tree that is not drawn: in the middle. */
const RING_AT = 2;

/**
 * A frame of a strip has a clear column at either hand, so that nothing of the frame beside
 * it shows at its edge. So a frame begins one art pixel before what is drawn in it.
 */
const CLEAR = 1;

const drawn = (name: ArtName): Drawn => ART[name];

/** How wide one frame of a drawing is, in art pixels. */
export function frameWidth(name: ArtName): number {
  return drawn(name).width / (drawn(name).frames ?? 1);
}

/** How many frames a drawing holds. One, of a drawing that is no strip. */
export function framesIn(name: ArtName): number {
  return drawn(name).frames ?? 1;
}

/** The pieces of what is built, or of the plots that are marked out where nothing is. */
function built(plan: Plan): readonly Piece[] {
  return LOT_AT.slice(0, LOTS).flatMap((left, lot): Piece[] => {
    const building = plan.buildings?.[lot];
    // A bare plot lies on the meadow, about the line a building would stand on.
    if (building === undefined) return [{ drawing: LOT, frame: 0, left: left + 2, top: GROUND - 1 }];
    const wall = WALL[building.form];
    // The last row of a wall is the shade it throws. The row before it is the line it stands on.
    const top = GROUND - (ART[wall].height - 2);
    return [
      { drawing: wall, frame: building.lit === null ? 0 : building.lit + 1, left: left + 1 - CLEAR, top },
      // A roof ends in the line that closes the wall under it.
      {
        drawing: ROOFS,
        frame: building.roof === null ? NO_ROOF : byPlace(ROOF_FRAMES[building.roof], lot),
        left: left - CLEAR,
        top: top - ART[ROOFS].height,
      },
    ];
  });
}

/** The pieces of what stands in front: the trees, or the ring where one would stand. */
function inFront(plan: Plan): readonly Piece[] {
  // The last row of a tree is the shade it throws. The row before it is the line it stands on.
  const top = FOOT - (ART[TREES].height - 2);
  const at = (place: number) => (PLACE_AT[place] ?? 0) - CLEAR;
  if (plan.trees === null) return [{ drawing: TREES, frame: 0, left: at(RING_AT), top }];
  return TAKEN.slice(0, plan.trees)
    .sort((one, other) => one - other)
    .map((place) => ({ drawing: TREES, frame: byPlace(TREE_FRAMES, place), left: at(place), top }));
}

/** Every piece of a town, in the order they are drawn in: what comes later lies over what came before. */
export function piecesOf(plan: Plan): readonly Piece[] {
  return [{ drawing: PLOT, frame: 0, left: 0, top: 0 }, ...built(plan), ...inFront(plan)];
}
