/**
 * A vibe the service says is less sure than the rest, which it calls a rough guide.
 *
 * The founder decided on 2026-09-25 that Village feel is served though it did not reach
 * the bar they had set, and the website said so wherever such a vibe was shown: a short
 * label beside its name, and a sentence that said why. On 2026-09-26 the founder walked
 * the website and asked for that to go: "remove the concept of rough guide, we don't want
 * to pass this on to a user".
 *
 * So the service still says which vibe is less sure, in `sureness` of the vibe, and what
 * such a vibe says of itself, in a part of route 11 that the website reads nowhere and
 * hands to no page (`lib/api/handed.ts`).
 *
 * What the website still does with a vibe that is less sure is said by nothing:
 * `LESS_SURE` chooses.
 */

import type { Tag } from "@/lib/api/schema";

/**
 * What becomes of a vibe the service says is less sure, where the website says a thing in
 * short. `held-back`: it is in no line of what an area is like in short, in no list of what
 * two areas share, and is not named as an example of what a vibe is. It has its own line on
 * the page of an area and its own box on the page of vibes, as every vibe has. `as-the-rest`:
 * it is held back from nothing, and may lead what an area is said to be like.
 *
 * Neither says anything to a visitor. It is the founder's to choose.
 */
export type LessSure = "held-back" | "as-the-rest";

/** This is the one line that chooses. */
export const LESS_SURE: LessSure = "held-back";

/** Whether a vibe would be held back from what is said in short, were the look to choose so. */
export function heldBack(tag: Partial<Pick<Tag, "sureness">>, lessSure: LessSure): boolean {
  return lessSure === "held-back" && tag.sureness === "rough_guide";
}

/** Whether a vibe is held back from what is said in short, because the service says it is less sure. */
export function isRough(tag: Partial<Pick<Tag, "sureness">>): boolean {
  return heldBack(tag, LESS_SURE);
}

