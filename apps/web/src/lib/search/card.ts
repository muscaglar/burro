/**
 * What a result card is filled from: the joins between a ranked area and the
 * facts that stand behind it. docs/design/web.md, section 4.
 *
 * Nothing here writes a word about a place. It finds what the API sent.
 */

import type {
  AreaData,
  Commute,
  CommuteLeg,
  Contribution,
  CostEstimate,
  Fact,
  MetaData,
  PreferenceSpec,
  RankedArea,
} from "@/lib/api/schema";

export type Facts = Readonly<Record<string, Fact>>;

/** The fact of the nearest station, from the area's profile. */
export function nearestStation(detail: AreaData | undefined): Fact | null {
  return detail?.facts.find((fact) => fact.kind === "station" && fact.template === "station") ?? null;
}

/** The cost of the kind of home the search is for: the fact, and the figures that place the bar. */
export function costFor(
  detail: AreaData | undefined,
  spec: Pick<PreferenceSpec, "tenure" | "budget">,
): { readonly fact: Fact; readonly estimate: CostEstimate } | null {
  if (detail === undefined) return null;
  const key = `${spec.tenure}.${spec.budget.segment}`;
  const fact = detail.facts.find((one) => one.kind === "cost" && one.key === key);
  const estimate = detail.cost.find(
    (one) => one.tenure === spec.tenure && one.segment === spec.budget.segment,
  );
  return fact && estimate ? { fact, estimate } : null;
}

/** The id of a journey's fact: the area, then the place and the way of travelling. */
const journeyFactId = (areaId: string, leg: Pick<CommuteLeg, "place_id" | "mode">) =>
  `${areaId}/travel/${leg.place_id}.${leg.mode}`;

/** The journey the fit is worked out from: the leg named first by the journey's contribution. */
export function drivingLeg(area: RankedArea): CommuteLeg | null {
  const journey = area.contributions.find((contribution) => contribution.component === "commute");
  const first = journey?.fact_ids[0];
  if (first === undefined) return null;
  return area.legs.find((leg) => journeyFactId(area.area_id, leg) === first) ?? null;
}

/**
 * The facts that give a journey its source and date. The journey's own fact
 * where it is in hand. Otherwise any journey's: a release states the source
 * and the date of its journeys once, for all of them. With none in hand,
 * none, and the page links to the sources instead.
 */
export function factsForJourney(area: RankedArea, leg: CommuteLeg, facts: Facts): readonly Fact[] {
  const own = facts[journeyFactId(area.area_id, leg)];
  if (own !== undefined) return [own];
  const any = Object.values(facts).find((fact) => fact.kind === "travel");
  return any === undefined ? [] : [any];
}

/** Whether a journey is within the longest the person set. `null` when there is no time to compare. */
export function withinLimit(leg: CommuteLeg, commute: Commute | undefined): boolean | null {
  if (commute === undefined || leg.status === "missing") return null;
  if (leg.status === "beyond_cutoff" || leg.minutes === null) return false;
  return leg.minutes <= commute.max_minutes;
}

/**
 * Whether the journeys of an area count for nothing in its fit, though the search names
 * places to reach: the ranking gave their part of the fit no figure. It does so when a
 * journey has no time in the data, whatever the others take. `null` when they count, or
 * when the search sets nothing by them. `over` is true when a journey that has a time is
 * over the longest the person set for it.
 */
export function journeysLeftOut(
  area: Pick<RankedArea, "contributions" | "legs">,
  commutes: readonly Commute[],
): { readonly journeys: number; readonly over: boolean } | null {
  const part = area.contributions.find((contribution) => contribution.component === "commute");
  if (part === undefined || part.present || area.legs.length === 0) return null;
  const over = area.legs.some(
    (leg) => withinLimit(leg, commutes.find((one) => one.place_id === leg.place_id)) === false,
  );
  return { journeys: area.legs.length, over };
}

/** The name of what a contribution is for: the API's label for a feature or a tag. */
export function labelOf(
  contribution: Pick<Contribution, "component">,
  meta: Pick<MetaData, "features" | "tags">,
  words: { readonly journey: string; readonly budget: string },
): string {
  const { component } = contribution;
  if (component === "commute") return words.journey;
  if (component === "budget") return words.budget;
  const [kind, id] = component.split(":", 2);
  if (kind === "feature") {
    return meta.features.find((feature) => feature.feature_id === id)?.label ?? component;
  }
  if (kind === "tag") return meta.tags.find((tag) => tag.tag_id === id)?.label ?? component;
  return component;
}

/** A share from 0 to 1 as a whole number out of 100, rounded down: never more than is so. */
export function hundredths(share: number | null): number | null {
  if (share === null || !Number.isFinite(share)) return null;
  return Math.min(100, Math.max(0, Math.floor(share * 100 + 1e-9)));
}

/** How many of the things asked for have data for this area, and how many were asked for. */
export function completenessOf(area: Pick<RankedArea, "contributions">) {
  const asked = area.contributions.length;
  const present = area.contributions.filter((contribution) => contribution.present).length;
  return { asked, present, complete: present === asked };
}
