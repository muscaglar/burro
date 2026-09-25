/** @jest-environment node */
import { readdirSync } from "node:fs";
import path from "node:path";

import { DIMENSION_ORDER } from "@/content/labels";
import { SEGMENTS } from "@/content/settings";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData } from "@/lib/api/schema";

import {
  alikeRows,
  areaFact,
  costFacts,
  factsShown,
  featuresByDimension,
  sharedVibes,
  stationFacts,
} from "./profile";

const meta = recordedAnswer("get_meta", "meta").body.data;
const profiles: AreaData[] = readdirSync(path.join(recordedFolder(), "area")).map(
  (file) => (readRecorded(`area/${file.replace(/\.json$/, "")}`).body as { data: AreaData }).data,
);
const alderwick = profiles.find((profile) => profile.area.slug === "alderwick") as AreaData;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;

describe("how an area's profile is laid out", () => {
  test("test_every_fact_of_every_area_is_laid_out_once_and_none_is_made", () => {
    for (const profile of profiles) {
      const shown = factsShown(profile, meta).map((fact) => fact.fact_id);

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

  test("test_the_brands_are_in_the_order_of_the_table_of_tiers_with_the_mix_first_and_the_chains_last", () => {
    const brands = featuresByDimension(alderwick, meta.features).find((group) => group.dimension === "brands");
    const ids = (brands?.rows ?? []).map((row) => row.metric.feature_id);

    expect(ids).toHaveLength(48);
    expect(ids.slice(0, 7)).toEqual([
      "brand_mix",
      "grocer_premium_nearby",
      "grocer_premium_distance",
      "grocer_mid_nearby",
      "grocer_mid_distance",
      "grocer_value_nearby",
      "grocer_value_distance",
    ]);
    expect(ids.slice(7, 19).map((id) => id.split("_")[0])).toEqual([...Array(6).fill("gym"), ...Array(6).fill("coffee")]);
    // Every chain, by its name, in the order the API gives them.
    const chains = ids.slice(19);
    expect(chains).toHaveLength(29);
    expect(chains.every((id) => id.startsWith("brand_"))).toBe(true);
    expect(chains).toEqual(meta.features.map((metric) => metric.feature_id).filter((id) => chains.includes(id)));
    // No other group is moved: each is in the order the API gives.
    for (const group of featuresByDimension(alderwick, meta.features)) {
      if (group.dimension === "brands") continue;
      const held = group.rows.map((row) => row.metric.feature_id);
      expect(held).toEqual(meta.features.map((metric) => metric.feature_id).filter((id) => held.includes(id)));
    }
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

  test("test_the_figure_of_a_part_of_a_recipe_is_a_features_fact_and_is_listed_once", () => {
    const shown = factsShown(alderwick, meta);
    const parts = alderwick.portrait.scales.flatMap((mark) => mark.parts.flatMap((part) => part.fact_id ?? []));

    // The page lays such a fact out twice: under what is measured, and in what a vibe is made of.
    expect(parts.length).toBeGreaterThan(0);
    for (const id of parts) expect(shown.filter((fact) => fact.fact_id === id)).toHaveLength(1);
  });

  test("test_the_fact_that_names_the_area_is_the_one_of_kind_area", () => {
    // It holds the label its publisher gives the area, who wrote the name, and that it is a draft.
    expect(areaFact(alderwick)?.slots).toEqual({
      name: "Alderwick",
      borough: "Quillhaven",
      label: "Quillhaven 001",
      written_by: "Burro",
      state: "draft",
    });
    expect(areaFact({ ...alderwick, facts: [] })).toBeNull();
  });
});

describe("the areas most like an area", () => {
  test("test_they_are_the_ones_the_api_names_in_its_order_each_with_its_own_fact", () => {
    for (const profile of profiles) {
      const rows = alikeRows(profile, areas);

      expect(rows.map((row) => row.area?.area_id)).toEqual(profile.similar.map((one) => one.area_id));
      expect(rows.map((row) => row.fact.fact_id)).toEqual(profile.similar.map((one) => one.fact_id));
      for (const { area, fact } of rows) {
        expect(fact.kind).toBe("likeness");
        // The name on the row is the fact's, and is the name of the area it leads to.
        expect(fact.slots.other).toBe(area?.name);
        expect(area?.area_id).not.toBe(profile.area.area_id);
      }
      expect(rows.length).toBeLessThanOrEqual(5);
    }
  });

  test("test_where_too_little_is_known_of_an_area_none_is_said_to_be_like_it", () => {
    const unknown = profiles.filter((profile) => profile.similar.length === 0);

    // Recorded: one area has a figure for 8 of the 40 features, which is too few to compare it on.
    expect(unknown.map((profile) => profile.area.name)).toEqual(["Otterby Fields"]);
    expect(unknown[0]?.features.filter((feature) => feature.value !== null)).toHaveLength(8);
    for (const profile of unknown) {
      expect(alikeRows(profile, areas)).toEqual([]);
      expect(profile.facts.filter((fact) => fact.kind === "likeness")).toEqual([]);
    }
  });

  test("test_an_area_whose_fact_did_not_come_is_left_out_and_nothing_is_made_up_for_it", () => {
    const without = { ...alderwick, facts: alderwick.facts.filter((fact) => fact.kind !== "likeness") };

    expect(alderwick.similar.length).toBeGreaterThan(0);
    expect(alikeRows(without, areas)).toEqual([]);
  });

  test("test_an_area_the_list_does_not_hold_keeps_its_fact_and_leads_nowhere", () => {
    const rows = alikeRows(alderwick, []);

    expect(rows.map((row) => row.area)).toEqual(rows.map(() => null));
    expect(rows).toHaveLength(alderwick.similar.length);
  });
});

describe("what two areas share", () => {
  const bands = recordedAnswer("list_areas", "areas").body.data.bands;
  const idOf = (slug: string) => areas.find((area) => area.slug === slug)?.area_id ?? "";
  const shared = (one: string, other: string) =>
    sharedVibes(idOf(one), idOf(other), bands, meta).map((tag) => tag.tag_id);

  test("test_it_is_the_vibes_both_areas_sit_in_the_same_band_on_as_the_api_bands_them", () => {
    const found = shared("thrushcombe", "wickerford");

    expect(found.length).toBeGreaterThan(0);
    for (const tagId of found) {
      const marks = bands.find((one) => one.tag_id === tagId)?.marks ?? [];
      const one = marks.find((mark) => mark.area_id === idOf("thrushcombe"));
      const other = marks.find((mark) => mark.area_id === idOf("wickerford"));
      expect(one?.band).not.toBeNull();
      expect(one?.band).toBe(other?.band);
    }
    // In the order the API lists the vibes, and the same whichever area is asked of.
    const order = meta.tags.map((tag) => tag.tag_id);
    expect(found).toEqual([...found].sort((one, other) => order.indexOf(one) - order.indexOf(other)));
    expect(shared("wickerford", "thrushcombe")).toEqual(found);
  });

  test("test_a_vibe_that_cannot_place_either_area_is_shared_by_neither", () => {
    // Burro places Otterby Fields on one vibe of eleven. Nothing is shared on the ten it cannot place.
    for (const area of areas) {
      const found = shared("otterby-fields", area.slug);
      expect(found.filter((tagId) => tagId !== "homes")).toEqual([]);
    }
  });

  test("test_a_mixed_area_shares_a_band_with_none_because_it_sits_at_no_one_point", () => {
    // Foxholt spans bands 3 to 5 on Going out.
    for (const area of areas) expect(shared("foxholt", area.slug)).not.toContain("pace");
  });

  test("test_a_vibe_that_holds_recorded_crime_is_never_among_what_is_shared", () => {
    for (const one of areas) {
      for (const other of areas) expect(shared(one.slug, other.slug)).not.toContain("street_character");
    }
  });

  test("test_a_vibe_that_is_a_rough_guide_is_never_among_what_two_areas_share", () => {
    // Thrushcombe and Wickerford are the two made-up villages, and sit in one band of it.
    const marks = bands.find((one) => one.tag_id === "village_feel")?.marks ?? [];
    const [one, other] = ["thrushcombe", "wickerford"].map((slug) => marks.find((mark) => mark.area_id === idOf(slug)));
    expect(one?.band).toBe(5);
    expect(other?.band).toBe(5);
    expect(shared("thrushcombe", "wickerford")).not.toContain("village_feel");
    for (const area of areas) expect(shared("thrushcombe", area.slug)).not.toContain("village_feel");
    // It is the API that says which vibe is one. Said of none, it is shared as any vibe is.
    const sure = { ...meta, tags: meta.tags.map((tag) => ({ ...tag, sureness: "as_the_rest" as const })) };
    expect(sharedVibes(idOf("thrushcombe"), idOf("wickerford"), bands, sure).map((tag) => tag.tag_id)).toContain(
      "village_feel",
    );
  });

  test("test_an_area_shares_nothing_with_itself_and_nothing_with_an_area_the_bands_do_not_hold", () => {
    expect(shared("thrushcombe", "thrushcombe")).toEqual([]);
    expect(sharedVibes(idOf("thrushcombe"), "syn-n9999", bands, meta)).toEqual([]);
    expect(sharedVibes(idOf("thrushcombe"), idOf("wickerford"), [], meta)).toEqual([]);
  });
});
