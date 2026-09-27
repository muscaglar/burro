/**
 * What Burro is drawn from, in each pose. It is kept apart from the parts that draw him,
 * which run in the browser: what a page drawn on the server takes from a file that runs in
 * the browser is a component and nothing else.
 */

import type { Drawing } from "../drawings";

/**
 * He sits, before a search and in what every page stands in. He hops in and out of his
 * hole while a search is read, until the answer is in. He asks nothing, so he has no pose
 * in which he asks.
 */
export type Pose = "sits" | "hops";

export const POSES: readonly Pose[] = ["sits", "hops"];

/** A pose in which nothing is asked of him: he rests, and stirs as he does. */
export type Resting = Exclude<Pose, "hops">;

/** The pose in which he hops in and out of his hole. */
export type Hopping = Extract<Pose, "hops">;

export const RESTING: readonly Resting[] = ["sits"];

/** The drawing of each pose. `hops` is a strip of frames side by side, and the rest are one frame. */
export const DRAWING: Readonly<Record<Pose, Drawing>> = {
  sits: "burro-sits",
  hops: "burro-hops",
};

/** What is drawn in place of his hopping where nothing is to move: he sits beside his hole, still. */
export const STILL: Drawing = "burro-waits";

/** Him drawn still, in each pose: where nothing may move. */
export const STILL_OF: Readonly<Record<Pose, Drawing>> = {
  sits: DRAWING.sits,
  hops: STILL,
};

/**
 * What he does in each frame of his hop, counted from nought, in the order of the strip.
 * The hole is alone in the first and in the last, which is the first again, so that the
 * strip comes round with no jump. He comes up: his ears, his head and his forepaws, and he
 * climbs out. He is out: he springs, sits up, looks about and turns. He goes down: head
 * first, his haunch and his scut, and his scut last.
 */
export const HOP = {
  alone: [0, 11],
  up: [1, 2, 3],
  out: [4, 5, 6, 7],
  down: [8, 9, 10],
} as const;

/**
 * The soil that flicks up from his hole as he goes down it, and as he comes up: a strip of
 * its own, which lies over the strip of his hop and holds a frame for each frame of it. It
 * is named by rule, for the drawing of his hop: a strip that has not been drawn is a fault
 * when the website is built.
 */
export function soilOf(pose: Hopping): Drawing {
  return `burro-${pose}-soil`;
}

/**
 * The strip of what he does as he rests in a pose. It is named by rule, for the drawing of
 * the pose: a strip that has not been drawn is a fault when the website is built.
 */
export function stirsOf(pose: Resting): Drawing {
  return `burro-${pose}-stirs`;
}

/**
 * Where each of his movements stands in a strip of what he does at rest, counted from
 * nought. The strips of every pose stand in this order, so that one style sheet moves him
 * in all of them: it names these frames by their number.
 *
 * `body` is him with what moves taken out. The three after it are each a part of him
 * alone, and lie over it: the first frame of each is that part at rest. `now` is what he
 * does now and then, which is the whole of him: he shifts his weight, he looks round, he
 * sits up and washes an ear.
 */
export const FRAMES = {
  body: [0],
  ears: [1, 2, 3],
  eye: [4, 5],
  nose: [6, 7],
  now: [8, 9, 10, 11, 12, 13, 14],
} as const;
