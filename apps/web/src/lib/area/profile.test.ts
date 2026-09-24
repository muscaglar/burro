/** @jest-environment node */
import { readdirSync } from "node:fs";
import path from "node:path";

import { DIMENSION_ORDER } from "@/content/labels";
import { SEGMENTS } from "@/content/settings";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData } from "@/lib/api/schema";

import { areaFact, costFacts, factsShown, featuresByDimension, stationFacts, tagRows } from "./profile";

const meta = recordedAnswer("get_meta", "meta").body.data;
const profiles: AreaData[] = readdirSync(path.join(recordedFolder(), "area")).map(
  (file) => (readRecorded(`area/${file.replace(/\.json$/, "")}`).body as { data: AreaData }).data,
);
const alderwick = profiles.find((profile) => profile.area.slug === "alderwick") as AreaData;

describe("how an area's profile is laid out", () => {
  test("test_every_fact_of_every_area_is_laid_out_once_and_none_is_made", () => {
    for (const profile of profiles) {
      const shown = factsShown(profile, meta.features, meta.tags).map((fact) => fact.fact_id);

      expect([...shown].sort()).toEqual(profile.facts.map((fact) => fact.fact_id).sort());
      expect(new Set(shown).size).toBe(shown.length);
    }
    expect(profiles).toHaveLength(24);
  });

  test("test_every_feature_of_the_release_has_a_row_whether_or_not_the_area_has_a_figure", () => {
    for (const profile of profiles) {
      const rows = featuresByDimension(profile, meta.features).flatMap((group) => group.rows);
      const without = profile.features.filter((feature) => feature.value === null).map((feature) => feature.feature_id);

      expect(rows.map((row) => row.metric.feature_id).sort()).toEqual(
        meta.features.map((metric) => metric.feature_id).sort(),
      );
      // A feature with no value has no fact, and none is made for it.
      expect(rows.filter((row) => row.fact === null).map((row) => row.metric.feature_id).sort()).toEqual(
        [...without].sort(),
      );
    }
  });

  test("test_a_fact_is_under_the_heading_of_what_its_feature_is_about", () => {
    for (const group of featuresByDimension(alderwick, meta.features)) {
      for (const { metric, fact } of group.rows) {
        expect(metric.dimension).toBe(group.dimension);
        if (fact !== null) expect(fact.key).toBe(metric.feature_id);
      }
    }
  });

  test("test_the_groups_are_in_the_order_the_website_shows_them_with_crime_last", () => {
    const order = featuresByDimension(alderwick, meta.features).map((group) => group.dimension);

    expect(order).toEqual(DIMENSION_ORDER.filter((dimension) => order.includes(dimension)));
    expect(order.at(-1)).toBe("crime");
  });

  test("test_a_group_the_release_has_no_feature_in_is_left_out", () => {
    const withoutSchools = meta.features.filter((metric) => metric.dimension !== "schools");

    const order = featuresByDimension(alderwick, withoutSchools).map((group) => group.dimension);

    expect(order).not.toContain("schools");
    expect(order).toHaveLength(DIMENSION_ORDER.length - 1);
  });

  test("test_the_cost_of_each_kind_of_home_is_in_the_order_a_form_lists_them", () => {
    for (const tenure of ["rent", "buy"] as const) {
      expect(costFacts(alderwick, tenure).map((fact) => fact.key)).toEqual(
        SEGMENTS[tenure].map((segment) => `${tenure}.${segment}`),
      );
    }
  });

  test("test_a_kind_of_home_with_no_figure_has_no_row_and_none_is_filled_in", () => {
    const thin: AreaData = { ...alderwick, facts: alderwick.facts.filter((fact) => fact.key !== "rent.studio") };

    expect(costFacts(thin, "rent").map((fact) => fact.key)).not.toContain("rent.studio");
    expect(costFacts(thin, "rent")).toHaveLength(5);
  });

  test("test_the_nearest_station_is_first_and_the_rest_follow_by_the_walk", () => {
    for (const profile of profiles) {
      const facts = stationFacts(profile);
      const walks = facts.map(
        (fact) => profile.stations.find((station) => station.station_id === fact.key)?.walk_minutes ?? -1,
      );

      expect(facts).toHaveLength(profile.stations.length);
      if (facts.length > 0) expect(facts[0]?.template).toBe("station");
      expect(facts.slice(1).every((fact) => fact.template === "station_nearby")).toBe(true);
      expect(walks.slice(1)).toEqual([...walks.slice(1)].sort((one, other) => one - other));
    }
  });

  test("test_every_tag_of_the_release_has_a_row", () => {
    expect(tagRows(alderwick, meta.tags).map((row) => row.tag.tag_id)).toEqual(meta.tags.map((tag) => tag.tag_id));
    expect(tagRows({ ...alderwick, facts: [] }, meta.tags).every((row) => row.fact === null)).toBe(true);
  });

  test("test_the_fact_that_names_the_area_is_the_one_of_kind_area", () => {
    expect(areaFact(alderwick)?.slots).toEqual({ name: "Alderwick", borough: "Quillhaven" });
    expect(areaFact({ ...alderwick, facts: [] })).toBeNull();
  });
});
