/**
 * Whether a sentence may stand under the word "Trade-off".
 *
 * A trade-off is something the area does badly: contract 7.5. The API picks
 * it, and since engine 1.3.0 it gives none where an area does nothing badly.
 * The website checks it all the same, against the ranking it already holds,
 * because the heading is the website's own word. An engine before 1.3.0 gave
 * the least good thing as the trade-off even when it was good, and the card
 * then read "Trade-off: a 2 minute walk, closer than 77% of areas".
 *
 * Nothing here writes or rewords a sentence. It says whether one is shown
 * under that heading. One that is not is left out, and the card says that no
 * trade-off was found.
 */

import type { Commute, CommuteLeg, Contribution, ExplainedSentence, RankedArea } from "@/lib/api/schema";
import { withinLimit } from "@/lib/search/card";

/**
 * The least a thing must be worth to an area to be something the area does
 * well: `REASON_MIN_UTILITY` of contract 7.5. A test holds it to the contract.
 */
export const DOES_WELL_FROM = 0.5;

/** The thing that counts which a sentence is about: the one whose fact it cites first. */
export function partOf(
  area: Pick<RankedArea, "contributions">,
  sentence: Pick<ExplainedSentence, "fact_ids">,
): Contribution | null {
  const [about] = sentence.fact_ids;
  if (about === undefined) return null;
  return area.contributions.find((part) => part.fact_ids.includes(about)) ?? null;
}

/** The journey a sentence is about, where it is about one. */
export function legOf(
  area: Pick<RankedArea, "area_id" | "legs">,
  sentence: Pick<ExplainedSentence, "fact_ids">,
): CommuteLeg | null {
  const [about] = sentence.fact_ids;
  return area.legs.find((leg) => `${area.area_id}/travel/${leg.place_id}.${leg.mode}` === about) ?? null;
}

/**
 * True when the area falls short of what was asked for, whatever that is
 * worth: a home over the budget, or a journey over the longest that was set.
 */
function fallsShort(
  area: Pick<RankedArea, "budget" | "legs">,
  part: Pick<Contribution, "component">,
  commutes: readonly Commute[],
): boolean {
  if (part.component === "budget") return area.budget !== null && area.budget.margin < 0;
  if (part.component !== "commute") return false;
  return area.legs.some(
    (leg) => withinLimit(leg, commutes.find((one) => one.place_id === leg.place_id)) === false,
  );
}

/**
 * True when the sentence is about something that counts in the search and
 * that the area does badly: it is worth less than a half, or it falls short.
 * Anything else is no trade-off, and is not shown as one.
 */
export function isGivenUp(
  area: Pick<RankedArea, "contributions" | "budget" | "legs">,
  sentence: Pick<ExplainedSentence, "fact_ids">,
  commutes: readonly Commute[],
): boolean {
  const part = partOf(area, sentence);
  if (part === null || !part.present) return false;
  if (fallsShort(area, part, commutes)) return true;
  return part.utility !== null && part.utility < DOES_WELL_FROM;
}
