/**
 * The four vibes a town is drawn from, by the ids the service gives them.
 *
 * This is the one table that names them, in the one file that does. Every other file of
 * the town asks it by the part that is drawn, and `vibes.test.ts` reads them all for an id.
 * What a vibe is called, and what its ends are called, are the service's to say: nothing
 * here is shown to anyone.
 */

import type { TagId } from "@/lib/api/schema";

/** What is drawn of a town. Each part is drawn from one vibe, and from nothing else. */
export type Part = "trees" | "height" | "lit" | "roofs";

/**
 * The parts, in the order they are said in: what stands on the plot, and then what is on it
 * and in it. The windows and the roofs come after the buildings they are drawn on.
 */
export const PARTS: readonly Part[] = ["trees", "height", "lit", "roofs"];

/** The vibe each part is drawn from. */
export const DRAWN_FROM: Readonly<Record<Part, TagId>> = {
  trees: "leafy",
  height: "homes",
  lit: "pace",
  roofs: "built_age",
};
