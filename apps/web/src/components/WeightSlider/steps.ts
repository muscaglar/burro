/**
 * How many steps the gauge under a slider has. It is plain code with no state, kept apart
 * from the slider, which runs in the browser: what a page drawn on the server takes from a
 * file that runs in the browser is a component and nothing else.
 */

import { VIBE_BANDS } from "@/lib/vibes";

import { STEPS } from "../kit/Gauge/filled";

/**
 * How many steps a gauge has from nought to a hundred: one for each press of its plus, by
 * the small step the API serves, so that a press fills a step.
 *
 * A gauge is never to be taken for where an area sits on a vibe, which is five steps. So
 * it has more steps than that, and no more than the row of them has room for: where the
 * small step gives fewer or more, it has as many as a gauge has where it is told nothing.
 */
export function stepsOf(small: number): number {
  const presses = Number.isFinite(small) && small > 0 ? Math.round(100 / small) : STEPS;
  return presses > VIBE_BANDS.length && presses <= STEPS ? presses : STEPS;
}

/**
 * Of a scale, how many steps run each way from its middle: half as many, so that a scale
 * with its two ends beside it is no wider than a phone. The two runs and the middle
 * between them are never taken for a band either.
 */
export function eachWay(steps: number): number {
  return Math.max(1, Math.ceil(steps / 2));
}
