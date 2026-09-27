/**
 * How a gauge is laid out, worked out from how much a thing counts. It is plain code with
 * no state, kept apart from the gauge so that a test can hold it to every count.
 */

/** How many steps a gauge has from nought to a hundred, where it is told nothing. */
export const STEPS = 10;

/** How much a thing counts, held between what a gauge can show: a whole number, no less than `least`. */
export function within(counts: number, least: 0 | -100 = 0): number {
  if (!Number.isFinite(counts)) return 0;
  return Math.min(100, Math.max(least, Math.round(counts)));
}

/**
 * How many steps are filled. None is, only at nought, and every one is, only at a
 * hundred: so a thing that counts a little is never drawn as one that counts for nothing,
 * and one that counts nearly all is never drawn as one that counts all.
 */
export function filledOf(counts: number, steps: number): number {
  const held = Math.abs(within(counts, -100));
  if (held === 0 || steps < 1) return 0;
  if (held === 100) return steps;
  return Math.min(Math.max(1, steps - 1), Math.max(1, Math.round((held * steps) / 100)));
}
