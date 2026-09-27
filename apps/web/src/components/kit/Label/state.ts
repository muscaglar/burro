/**
 * What a chip says of its state, in words. It is kept apart from the chip, which runs in
 * the browser, so that a page drawn on the server can say the same.
 */

import { LABEL } from "@/content/kit";

import type { ThingState } from "../Thing/drawn";
import { STATE_WORD } from "../Thing/Thing";

/** The words for a state, and what it is said of where it is said of a part. `null` where the state has no word. */
export function stateOf(state: ThingState, of?: string): string | null {
  const word = STATE_WORD[state];
  if (word === null) return null;
  return of === undefined || of === "" ? word : LABEL.of(word, of);
}
