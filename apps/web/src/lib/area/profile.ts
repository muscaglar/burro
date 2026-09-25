/**
 * How an area's profile is laid out on its page: which facts go under which
 * heading, and in what order. docs/design/web.md, section 2.
 *
 * Nothing here writes a word about a place, and nothing is filled in. A
 * feature with no figure has no fact, and the page says so in site copy.
 * What the API serves with no fact behind it, such as whether a station is
 * step-free, has no source and no date, and is not laid out at all.
 */

import { DIMENSION_ORDER } from "@/content/labels";
import { SEGMENTS } from "@/content/settings";
import type {
  AreaData,
  AreaSummary,
  Dimension,
  Fact,
  MetaData,
  Metric,
  Tag,
  Tenure,
  VibeBands,
} from "@/lib/api/schema";
import { isRange } from "@/lib/vibes";

import { isRough } from "@/content/rough";

import { factsOf, holdsRecordedCrime, portraitOf } from "./portrait";

/** A feature of the release, with the fact the area has for it, if it has one. */
export interface FeatureRow {
  readonly metric: Metric;
  readonly fact: Fact | null;
}

export interface DimensionGroup {
  readonly dimension: Dimension;
  readonly rows: readonly FeatureRow[];
}

const factOf = (data: AreaData, kind: Fact["kind"], key: string): Fact | null =>
  data.facts.find((fact) => fact.kind === kind && fact.key === key) ?? null;

/** The fact that names the area and its borough. */
export function areaFact(data: AreaData): Fact | null {
  return data.facts.find((fact) => fact.kind === "area") ?? null;
}

/**
 * The area's features, grouped by what they are about, in the order the
 * website shows the groups. Every feature of the release has a row, so that
 * one with no figure is seen to have none. A group the release has no
 * feature in is left out.
 */
export function featuresByDimension(data: AreaData, features: readonly Metric[]): readonly DimensionGroup[] {
  return DIMENSION_ORDER.map((dimension) => ({
    dimension,
    rows: inOrder(features.filter((metric) => metric.dimension === dimension)).map((metric) => ({
      metric,
      fact: factOf(data, "feature", metric.feature_id),
    })),
  })).filter((group) => group.rows.length > 0);
}

/** The kinds of place and the tiers of the brands, in the order the table of tiers lists them. */
const KINDS_OF_BRAND = ["grocer", "gym", "coffee"];
const TIERS_OF_BRAND = ["premium", "mid", "value"];

/**
 * Where a measure of a tier stands among its like: by its kind, then its tier, as the table
 * of tiers reads, and the places within reach before the distance to the nearest. The id of
 * such a measure is its kind, its tier and what is measured, and the contract holds it so.
 */
function amongTiers(metric: Metric): number {
  const [kind = "", tier = "", what = ""] = metric.feature_id.split("_");
  const at = [KINDS_OF_BRAND.indexOf(kind), TIERS_OF_BRAND.indexOf(tier)];
  if (at.includes(-1)) return Infinity;
  return ((at[0] ?? 0) * TIERS_OF_BRAND.length + (at[1] ?? 0)) * 2 + (what === "nearby" ? 0 : 1);
}

/**
 * The features of one group, in the order its rows are drawn: the API's, but for the brands.
 * There the measure that is ranked on comes first, then what is counted of each tier, and
 * then the chains, each of which a person asks for by name.
 */
export function inOrder(features: readonly Metric[]): readonly Metric[] {
  const place = (metric: Metric) => {
    if (metric.dimension !== "brands") return 0;
    if (metric.kind === "on_request") return 2;
    return metric.rankable ? 0 : 1;
  };
  // A sort keeps the order of what it finds equal, so the API's order stands wherever
  // nothing here says otherwise.
  return [...features].sort(
    (one, other) =>
      place(one) - place(other) || (place(one) === 1 ? amongTiers(one) - amongTiers(other) : 0),
  );
}

/** What homes cost, for renting or for buying: one fact for each kind of home that has a figure. */
export function costFacts(data: AreaData, tenure: Tenure): readonly Fact[] {
  return SEGMENTS[tenure].flatMap((segment) => {
    const fact = factOf(data, "cost", `${tenure}.${segment}`);
    return fact === null ? [] : [fact];
  });
}

/** The stations near the area: the nearest first, then the rest by how long the walk is. */
export function stationFacts(data: AreaData): readonly Fact[] {
  const walk = new Map(data.stations.map((station) => [station.station_id, station.walk_minutes]));
  return data.facts
    .filter((fact) => fact.kind === "station")
    .sort((one, other) => {
      const nearest = Number(other.template === "station") - Number(one.template === "station");
      if (nearest !== 0) return nearest;
      return (walk.get(one.key) ?? Infinity) - (walk.get(other.key) ?? Infinity) || one.key.localeCompare(other.key);
    });
}

/** An area that is like this one, with the fact that says how far. */
export interface AlikeRow {
  /** The other area, to link to its page. `null` when the list of areas does not hold it. */
  readonly area: Pick<AreaSummary, "area_id" | "slug" | "name"> | null;
  readonly fact: Fact;
}

/**
 * The areas most like this one, in the order the API gives them: five at
 * most, and none where too little is known of the area to say. One whose
 * fact did not come is left out, because nothing can be said of it.
 */
export function alikeRows(
  data: AreaData,
  areas: readonly Pick<AreaSummary, "area_id" | "slug" | "name">[],
): readonly AlikeRow[] {
  return data.similar.flatMap((one) => {
    const fact = data.facts.find((held) => held.fact_id === one.fact_id);
    if (fact === undefined) return [];
    return [{ area: areas.find((area) => area.area_id === one.area_id) ?? null, fact }];
  });
}

/**
 * The vibes two areas sit in the same band on, in the order the API lists the vibes. Every
 * band is the API's, from route 4. A vibe that cannot place one of the two is shared by
 * neither, and nor is one on which either is mixed, which sits at no one point.
 *
 * A vibe whose recipe holds recorded crime is never among them: likeness is never counted on
 * recorded crime, and nobody asked for it here. Nor is a vibe that is a rough guide: it is
 * used to work out nothing else, and what two areas share is worked out.
 */
export function sharedVibes(
  areaId: string,
  otherId: string,
  bands: readonly VibeBands[],
  meta: Pick<MetaData, "tags" | "features">,
): readonly Tag[] {
  if (areaId === otherId) return [];
  return meta.tags.filter((tag) => {
    if (holdsRecordedCrime(tag, meta.features) || isRough(tag)) return false;
    const marks = bands.find((one) => one.tag_id === tag.tag_id)?.marks ?? [];
    const [one, other] = [areaId, otherId].map((id) => marks.find((mark) => mark.area_id === id));
    if (one === undefined || other === undefined) return false;
    return [one, other].every(sitsAtOnePoint) && one.band === other.band;
  });
}

function sitsAtOnePoint({ band, spread_low: low, spread_high: high }: VibeBands["marks"][number]): boolean {
  return band !== null && low !== null && high !== null && !isRange({ band, spread_low: low, spread_high: high });
}

/**
 * Every fact the page lays out, once each, for the list of sources at its
 * foot. The figure of a part of a recipe is a feature's fact, which the page
 * also lays out under what is measured: it is one fact, and is listed once.
 */
export function factsShown(data: AreaData, meta: Pick<MetaData, "features" | "tags">): readonly Fact[] {
  const area = areaFact(data);
  const shown = [
    ...(area === null ? [] : [area]),
    ...factsOf(portraitOf(data, meta)),
    ...stationFacts(data),
    ...costFacts(data, "rent"),
    ...costFacts(data, "buy"),
    ...featuresByDimension(data, meta.features).flatMap((group) =>
      group.rows.flatMap((row) => (row.fact === null ? [] : [row.fact])),
    ),
    ...alikeRows(data, []).map((row) => row.fact),
  ];
  return [...new Map(shown.map((fact) => [fact.fact_id, fact])).values()];
}
