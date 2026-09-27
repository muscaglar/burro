/**
 * An offer, read as the service gave it: a thing that was noticed in the words and that
 * the service did not apply, with the ways it may be taken.
 *
 * The page asks nothing. It takes one way of every offer as soon as the reading is in,
 * and `takes.ts` says which. What it chooses by is read here. Where the service reads a
 * thing one way, that way is marked as its guess. Which way one press may add with
 * others is the API's to say, in `add_all`: a budget as the person worded it, which may
 * be a firm limit, and a journey as a guide. It never names a journey as a firm limit, a
 * thing with two ways and no guess, a rule for an area, a journey to a place that is yet
 * to be chosen, or recorded crime. docs/design/contract.md, 8.2.
 *
 * An offer says two things of itself, for a page that asks nothing: whether the person's
 * own words name what it counts (`by_name`), and whether it waits for a person to choose
 * it (`only_by_choice`). A service that says neither is read as one that says the more
 * careful of each: that the words name nothing, and that nothing is known to wait.
 */

import type { Operations, Suggestion, SuggestionChoice } from "@/lib/api/schema";

/** The id of the choice that does nothing. Its words are the API's: "Skip". */
export const SKIP = "ignore";

/** The ways a thing may be taken: every choice of it but doing nothing. */
export function waysOf(suggestion: Pick<Suggestion, "choices">): readonly SuggestionChoice[] {
  return suggestion.choices.filter((choice) => choice.id !== SKIP);
}

/** The way the service reads the words, where it reads them one way. It is a mark on a way, and what is made of it is `takes.ts`'s to say. */
export function guessOf(suggestion: Pick<Suggestion, "choices">): SuggestionChoice | null {
  return waysOf(suggestion).find((choice) => choice.guess) ?? null;
}

/**
 * True where the service says that the person's own words name what the offer counts:
 * "gritty" names the vibe it is offered as, and "posh" names nothing, though the same
 * vibe is read into it. It is read from the answer as it came: a service that does not
 * say has not said that they do.
 */
export function namedByThePerson(suggestion: object): boolean {
  return "by_name" in suggestion && suggestion.by_name === true;
}

/**
 * True where the service says that what is offered waits for a person to choose it: what
 * counts who lived somewhere, what counts recorded crime where the words do not name it,
 * and a measure that a decision holds to be offered and never applied. Which thing is of
 * which kind is the service's to say, and no name of one is written here.
 */
export function waitsForAPerson(suggestion: object): boolean {
  return "only_by_choice" in suggestion && suggestion.only_by_choice === true;
}

/** True of an offer of a measure or of a vibe: a wish, and no limit, journey, home or area. */
export function isAWish(suggestion: Pick<Suggestion, "target">): boolean {
  return suggestion.target.startsWith("feature:") || suggestion.target.startsWith("tag:");
}

/** The way of a thing that one press may add with others, or `null` where the API names none. */
export function addedWithOthers(suggestion: Pick<Suggestion, "choices" | "add_all">): SuggestionChoice | null {
  if (suggestion.add_all === "" || suggestion.add_all === SKIP) return null;
  return waysOf(suggestion).find((choice) => choice.id === suggestion.add_all) ?? null;
}

/**
 * The edits of a way, with a place put into each journey that holds none. A
 * journey to a place the release does not hold is offered with no place, and
 * with the places whose names are like it: `takes.ts` says which is taken.
 */
export function withPlace(operations: Operations, placeId: string): Operations {
  return {
    ...operations,
    commute_ops: operations.commute_ops.map((edit) =>
      edit.place_id === "" ? { ...edit, place_id: placeId } : edit,
    ),
  };
}

/**
 * By what an offer is told from every other of one answer: its thing, its name, and where
 * the clause it stands in begins. The rules and a model give the same thing the same three,
 * though a model may rest it on more of the words.
 */
export function keyOf(suggestion: Pick<Suggestion, "target" | "label" | "shown">): string {
  return `${suggestion.target} ${suggestion.label} ${suggestion.shown.start}`;
}
