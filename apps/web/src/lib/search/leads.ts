/**
 * What counts most in a search, where it is not what the person asked of the
 * place.
 *
 * What is said of the place leads: a thing that is asked for in a word counts
 * for more than a journey and for more than a budget, until the person says
 * otherwise. A person may make a journey or a budget count for more, in the
 * settings. Where one then counts for more than anything that was asked of
 * the place, the first results are the nearest or the cheapest, and the leafy
 * and quiet ones may be further down. Nothing is wrong with the order, and
 * the page must say why it is so: a person who is not told reads the first
 * result as the leafiest.
 *
 * It is read off the spec the API returned, and says nothing of any place.
 */

import type { PreferenceSpec } from "@/lib/api/schema";

import { counts } from "./counts";

export interface Leads {
  /** True where the journeys count for more than anything that was asked of the place. */
  readonly journey: boolean;
  /** True where the budget does. */
  readonly budget: boolean;
  /** How many places the search names, to say "journey" or "journeys". */
  readonly journeys: number;
}

/** The most that anything asked of the place counts for: a vibe, or a thing nearby that a person chose. */
export function mostAskedOfThePlace(spec: Pick<PreferenceSpec, "tags" | "weights">): number {
  const asked = [
    ...spec.tags.filter(counts),
    ...spec.weights.filter((weight) => weight.provenance !== "default" && counts(weight)),
  ];
  return Math.max(0, ...asked.map((one) => one.weight));
}

/**
 * What outweighs everything that was asked of the place, or `null` where nothing does, or
 * nothing was asked of the place.
 */
export function leadsOf(spec: PreferenceSpec): Leads | null {
  const most = mostAskedOfThePlace(spec);
  if (most === 0) return null;
  const journey = spec.commutes.length > 0 && spec.commute_weight > most;
  const budget = spec.budget.amount !== null && spec.budget.weight > most;
  return journey || budget ? { journey, budget, journeys: spec.commutes.length } : null;
}
