/**
 * What may be done with an offer: a thing Burro read in the words and did not apply.
 *
 * Nothing is applied until a person presses it. Where Burro reads a thing one
 * way, that way is marked as its guess, and the mark applies nothing. Which
 * way one press may add with others is the API's to say, in `add_all`: it
 * never names a way that leaves areas out, a thing with two ways and no
 * guess, a journey to a place that is yet to be chosen, or recorded crime.
 * docs/design/contract.md, 8.2.
 */

import type { Operations, Suggestion, SuggestionChoice } from "@/lib/api/schema";

/** The id of the choice that does nothing. Its words are the API's: "Skip". */
export const SKIP = "ignore";

/** The ways a thing may be taken: every choice of it but doing nothing. */
export function waysOf(suggestion: Pick<Suggestion, "choices">): readonly SuggestionChoice[] {
  return suggestion.choices.filter((choice) => choice.id !== SKIP);
}

/** The way Burro reads the words, where it reads them one way. It is a mark, and applies nothing. */
export function guessOf(suggestion: Pick<Suggestion, "choices">): SuggestionChoice | null {
  return waysOf(suggestion).find((choice) => choice.guess) ?? null;
}

/**
 * What a person should know before they choose, in the API's words, or `null`
 * where the suggestion carries nothing. It is read from the answer as it
 * came, so an answer from a service that sends no note is read as well.
 */
export function noteOf(suggestion: object): string | null {
  const note: unknown = "note" in suggestion ? suggestion.note : null;
  return typeof note === "string" && note.trim() !== "" ? note : null;
}

/** The way of a thing that one press may add with others, or `null` where the API names none. */
export function addedWithOthers(suggestion: Pick<Suggestion, "choices" | "add_all">): SuggestionChoice | null {
  if (suggestion.add_all === "" || suggestion.add_all === SKIP) return null;
  return waysOf(suggestion).find((choice) => choice.id === suggestion.add_all) ?? null;
}

/**
 * The edits of a way, with the place a person chose put into each journey
 * that holds none. A journey to a place the release does not hold is offered
 * with no place: the person says which.
 */
export function withPlace(operations: Operations, placeId: string): Operations {
  return {
    ...operations,
    commute_ops: operations.commute_ops.map((edit) =>
      edit.place_id === "" ? { ...edit, place_id: placeId } : edit,
    ),
  };
}

/** Whether every journey of these edits says where it leads. One that does not cannot be sent. */
export function namesItsPlaces(operations: Operations): boolean {
  return operations.commute_ops.every((edit) => edit.place_id !== "");
}

/**
 * By what an offer is told from every other of one answer: its thing, its name, and where
 * the clause it stands in begins. The rules and a model give the same thing the same three,
 * though a model may rest it on more of the words.
 */
export function keyOf(suggestion: Pick<Suggestion, "target" | "label" | "shown">): string {
  return `${suggestion.target} ${suggestion.label} ${suggestion.shown.start}`;
}
