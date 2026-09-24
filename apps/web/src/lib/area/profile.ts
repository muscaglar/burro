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
import type { AreaData, Dimension, Fact, Metric, Tag, Tenure } from "@/lib/api/schema";

/** A feature of the release, with the fact the area has for it, if it has one. */
export interface FeatureRow {
  readonly metric: Metric;
  readonly fact: Fact | null;
}

export interface TagRow {
  readonly tag: Tag;
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
    rows: features
      .filter((metric) => metric.dimension === dimension)
      .map((metric) => ({ metric, fact: factOf(data, "feature", metric.feature_id) })),
  })).filter((group) => group.rows.length > 0);
}

/** The area's tags, in the order the release lists them. */
export function tagRows(data: AreaData, tags: readonly Tag[]): readonly TagRow[] {
  return tags.map((tag) => ({ tag, fact: factOf(data, "tag", tag.tag_id) }));
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

/** Every fact the page lays out, for the list of sources at its foot. */
export function factsShown(data: AreaData, features: readonly Metric[], tags: readonly Tag[]): readonly Fact[] {
  const area = areaFact(data);
  return [
    ...(area === null ? [] : [area]),
    ...stationFacts(data),
    ...costFacts(data, "rent"),
    ...costFacts(data, "buy"),
    ...featuresByDimension(data, features).flatMap((group) =>
      group.rows.flatMap((row) => (row.fact === null ? [] : [row.fact])),
    ),
    ...tagRows(data, tags).flatMap((row) => (row.fact === null ? [] : [row.fact])),
  ];
}
