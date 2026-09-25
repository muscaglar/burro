/**
 * What a result card is filled from: the joins between a ranked area and the
 * facts that stand behind it. docs/design/web.md, section 4.
 *
 * Nothing here writes a word about a place. It finds what the API sent.
 */

import { COMPLETENESS } from "@/content/search";
import type {
  AreaData,
  Commute,
  CommuteLeg,
  Contribution,
  CostEstimate,
  Fact,
  JourneyBand,
  MetaData,
  PreferenceSpec,
  RankedArea,
  Score,
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

/**
 * Where a journey that was estimated stands against its limit, or `null` for any other. The
 * release holds no time for it, so it has a band and no minutes.
 */
export function estimateOf(leg: Pick<CommuteLeg, "status" | "estimate">): JourneyBand | null {
  return leg.status === "estimated" ? (leg.estimate ?? null) : null;
}

/**
 * Whether a journey is within the longest the person set. `null` when there is no time to
 * compare: one that was estimated has a band, and is never said to be within or over.
 */
export function withinLimit(leg: CommuteLeg, commute: Commute | undefined): boolean | null {
  if (commute === undefined || leg.status === "missing" || leg.status === "estimated") return null;
  if (leg.status === "beyond_cutoff" || leg.minutes === null) return false;
  return leg.minutes <= commute.max_minutes;
}

/**
 * How many journeys an area has, where they count for nothing in its fit though the
 * search names places to reach: the ranking gave their part of the fit no figure. It does
 * so only when no journey has a time in the data. One that has none is left out, and the
 * rest still count. `null` when the journeys count, or when the search sets nothing by them.
 */
export function journeysLeftOut(area: Pick<RankedArea, "contributions" | "legs">): number | null {
  const part = area.contributions.find((contribution) => contribution.component === "commute");
  if (part === undefined || part.present || area.legs.length === 0) return null;
  return area.legs.length;
}

/** The name of what a contribution is for: the API's label for a feature or a vibe. */
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

/**
 * How much of what counts a fit rests on, in words. The API says it of every
 * ranked area: how many things count, and for how many the area has a
 * figure. Where the fit rests on all of it nothing is said, unless `always`.
 */
export function basedOn(
  score: Pick<Score, "counted" | "present"> | undefined,
  always = false,
): string | null {
  if (score === undefined || score.counted === 0) return null;
  if (score.present >= score.counted) return always ? COMPLETENESS.all : null;
  return COMPLETENESS.some(score.present, score.counted);
}

/** How many of the things asked for have data for this area, and how many were asked for. */
export function completenessOf(area: Pick<RankedArea, "contributions">) {
  const asked = area.contributions.length;
  const present = area.contributions.filter((contribution) => contribution.present).length;
  return { asked, present, complete: present === asked };
}
