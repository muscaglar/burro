/** @jest-environment node */
import { readdirSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, MetaData } from "@/lib/api/schema";

import {
  cannotSee,
  GROUPS,
  holdsRecordedCrime,
  inShort,
  IN_SHORT,
  marksOf,
  nearestStation,
  PICTURED,
  placedBy,
  portraitOf,
  restsOn,
  shownOn,
} from "./portrait";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const profiles: AreaData[] = readdirSync(path.join(recordedFolder(), "area")).map(
  (file) => (readRecorded(`area/${file.replace(/\.json$/, "")}`).body as { data: AreaData }).data,
);
const profile = (slug: string) => profiles.find((one) => one.area.slug === slug) as AreaData;

describe("the portrait of an area", () => {
  test("test_every_vibe_of_the_release_is_in_exactly_one_list_of_the_portrait", () => {
    for (const data of profiles) {
      const portrait = portraitOf(data, meta);
      const drawn = GROUPS.flatMap((group) => portrait[group].map((mark) => mark.tag.tag_id));

      expect([...drawn].sort()).toEqual(meta.tags.map((tag) => tag.tag_id).sort());
      expect(new Set(drawn).size).toBe(drawn.length);
    }
    expect(profiles).toHaveLength(24);
  });

  test("test_the_lists_and_their_order_are_the_apis", () => {
    for (const data of profiles) {
      for (const group of GROUPS) {
        expect(marksOf(data, meta, group).map((mark) => mark.tag.tag_id)).toEqual(
          data.portrait[group].map((mark) => mark.tag_id),
        );
      }
    }
  });

  test("test_where_an_area_sits_is_the_band_its_fact_holds", () => {
    const thrushcombe = portraitOf(profile("thrushcombe"), meta);
    const homes = thrushcombe.scales.find((mark) => mark.tag.tag_id === "homes");

    expect(homes?.fact.slots.band).toBe("1");
    expect(homes?.placed).toEqual({ band: 1, spread_low: 1, spread_high: 1 });
    // Every mark that is placed sits in a band its own fact names, from 1 to 5.
    for (const data of profiles) {
      for (const mark of shownOn(portraitOf(data, meta))) {
        expect(mark.placed).toEqual({
          band: Number(mark.fact.slots.band),
          spread_low: Number(mark.fact.slots.spread_low),
          spread_high: Number(mark.fact.slots.spread_high),
        });
        expect([1, 2, 3, 4, 5]).toContain(mark.placed?.band);
      }
    }
  });

  test("test_a_mixed_area_spans_the_bands_its_fact_names", () => {
    const pace = portraitOf(profile("foxholt"), meta).scales.find((mark) => mark.tag.tag_id === "pace");

    expect(pace?.fact.template).toBe("vibe_range");
    expect(pace?.placed).toEqual({ band: 4, spread_low: 3, spread_high: 5 });
  });

  test("test_a_vibe_the_area_cannot_be_placed_on_has_no_band_and_is_never_put_in_the_middle", () => {
    const otterby = portraitOf(profile("otterby-fields"), meta);

    expect(otterby.unplaced).toHaveLength(13);
    for (const mark of otterby.unplaced) {
      expect(mark.fact.template).toBe("vibe_unknown");
      expect(mark.placed).toBeNull();
    }
    expect(shownOn(otterby).map((mark) => mark.tag.tag_id)).toEqual(["homes"]);
  });

  test.each([
    ["a band that is no number", { band: "high", spread_low: "1", spread_high: "5" }],
    ["a band past the fifth", { band: "6", spread_low: "6", spread_high: "6" }],
    ["a band with no spread", { band: "3" }],
    ["a spread that does not hold the band", { band: "1", spread_low: "2", spread_high: "4" }],
    ["nothing", {}],
  ])("test_a_fact_that_does_not_say_a_band_places_nothing: %s", (_, slots) => {
    const fact = profile("thrushcombe").facts.find((one) => one.kind === "tag");
    if (!fact) throw new Error("The profile holds no fact of a vibe.");

    expect(placedBy({ ...fact, slots })).toBeNull();
  });

  test("test_the_plain_figure_of_a_mark_is_the_fact_the_api_names_for_it", () => {
    for (const data of profiles) {
      for (const group of GROUPS) {
        marksOf(data, meta, group).forEach((mark, at) => {
          expect(mark.figure?.fact_id ?? null).toBe(data.portrait[group][at]?.figure_fact_id ?? null);
        });
      }
    }
    // A vibe that cannot place the area may still hold a figure for a part. One with no such part holds none.
    for (const mark of portraitOf(profile("otterby-fields"), meta).unplaced) {
      expect(mark.figure === null).toBe(mark.parts.every((part) => part.fact === null));
    }
  });

  test("test_a_part_with_no_figure_has_no_fact_and_none_is_made_for_it", () => {
    for (const data of profiles) {
      const held = new Set(data.facts.map((fact) => fact.fact_id));
      for (const group of GROUPS) {
        marksOf(data, meta, group).forEach((mark, at) => {
          const served = data.portrait[group][at]?.parts ?? [];
          expect(mark.parts.map((part) => part.fact?.fact_id ?? null)).toEqual(served.map((part) => part.fact_id));
          expect(mark.parts.map((part) => part.term.hundredths)).toEqual(served.map((part) => part.hundredths));
          for (const part of mark.parts) if (part.fact !== null) expect(held.has(part.fact.fact_id)).toBe(true);
        });
      }
    }
  });

  test("test_a_part_the_release_does_not_carry_has_no_name_to_give", () => {
    const homes = portraitOf(profile("thrushcombe"), meta).scales.find((mark) => mark.tag.tag_id === "homes");

    const missing = homes?.parts.filter((part) => part.metric === null) ?? [];

    expect(missing.map((part) => part.term.feature_id)).toEqual(["private_outdoor_space"]);
    expect(missing.every((part) => part.fact === null)).toBe(true);
    // The shares of a recipe still add up to a hundred.
    expect(homes?.parts.reduce((sum, part) => sum + part.term.hundredths, 0)).toBe(100);
  });

  test("test_a_mark_whose_vibe_the_release_does_not_name_is_left_out", () => {
    const without = { ...meta, tags: meta.tags.filter((tag) => tag.tag_id !== "pace") };

    const drawn = GROUPS.flatMap((group) => marksOf(profile("thrushcombe"), without, group));

    expect(drawn.map((mark) => mark.tag.tag_id)).not.toContain("pace");
    expect(drawn).toHaveLength(13);
  });

  test("test_a_mark_whose_fact_did_not_come_is_left_out_because_nothing_can_be_said_of_it", () => {
    const thrushcombe = profile("thrushcombe");
    const without = { ...thrushcombe, facts: thrushcombe.facts.filter((fact) => fact.key !== "leafy") };

    const drawn = GROUPS.flatMap((group) => marksOf(without, meta, group));

    expect(drawn.map((mark) => mark.tag.tag_id)).not.toContain("leafy");
  });
});

describe("a band that rests on part of a recipe", () => {
  const mark = (slug: string, tagId: string) => {
    const found = GROUPS.flatMap((group) => portraitOf(profile(slug), meta)[group]).find((one) => one.tag.tag_id === tagId);
    if (!found) throw new Error("The portrait holds no such vibe.");
    return found;
  };

  test("test_a_band_worked_out_from_part_of_a_recipe_says_how_many_parts_and_which_are_missing", () => {
    // Marrowfen has no figure for transport noise, which is 30 of the 100 shares of Quiet streets.
    const quiet = mark("marrowfen", "quiet_residential");

    expect(quiet.placed?.band).toBe(2);
    expect(restsOn(quiet)).toMatchObject({
      known: "2",
      parts: "3",
      missing: ["Share of residents exposed to 55 dB or more of transport noise"],
      notCarried: 0,
    });
  });

  test("test_a_part_this_data_does_not_carry_is_named_as_the_api_names_it_and_never_by_its_code", () => {
    const foot = mark("thrushcombe", "everyday_on_foot");

    // Seen in a browser: "No figure for: 2 parts this data does not carry", which named neither.
    expect(restsOn(foot)).toMatchObject({
      known: "3",
      parts: "5",
      missing: [],
      waiting: [
        "Straight-line distance to the nearest GP practice, placed by its postcode",
        "Straight-line distance to the nearest pharmacy, placed by its postcode",
      ],
      notCarried: 0,
    });
    // Where the API says nothing of what a release holds, such a part is counted, as it was.
    const unnamed = portraitOf(profile("thrushcombe"), { tags: meta.tags, features: meta.features });
    const counted = GROUPS.flatMap((group) => unnamed[group]).find((one) => one.tag.tag_id === "everyday_on_foot");
    expect(counted && restsOn(counted)).toMatchObject({ missing: [], waiting: [], notCarried: 2 });
  });

  test("test_a_band_that_rests_on_the_whole_recipe_says_nothing_more", () => {
    expect(restsOn(mark("thrushcombe", "leafy"))).toBeNull();
    expect(restsOn(mark("thrushcombe", "village_feel"))).toBeNull();
  });

  test("test_both_counts_are_the_facts_own_and_agree_with_the_parts_served", () => {
    for (const data of profiles) {
      for (const one of GROUPS.flatMap((group) => portraitOf(data, meta)[group])) {
        const rests = restsOn(one);
        const without = one.parts.filter((part) => part.fact === null).length;
        expect(rests === null).toBe(without === 0);
        if (rests === null) continue;
        expect(rests.known).toBe(one.fact.slots.known);
        expect(rests.parts).toBe(one.fact.slots.parts);
        expect(rests.missing.length + rests.waiting.length + rests.notCarried).toBe(without);
        expect(Number(rests.parts) - Number(rests.known)).toBe(without);
      }
    }
  });

  test("test_a_fact_that_does_not_say_how_many_parts_it_rests_on_says_nothing", () => {
    const quiet = mark("marrowfen", "quiet_residential");
    const slots = Object.fromEntries(Object.entries(quiet.fact.slots).filter(([name]) => name !== "known"));

    expect(restsOn({ ...quiet, fact: { ...quiet.fact, slots } })).toBeNull();
  });

  test("test_the_share_of_the_recipe_is_the_facts_own_and_is_never_worked_out_here", () => {
    const quiet = mark("marrowfen", "quiet_residential");

    // The engine says what share of a recipe a band rests on, in the slot `share`, and in a
    // clause of its own, `partly`. A fact that holds neither shows none: the website adds up
    // no shares of its own.
    const counts = Object.fromEntries(
      Object.entries(quiet.fact.slots).filter(([slot]) => slot !== "share" && slot !== "partly"),
    );
    const bare = { ...quiet, fact: { ...quiet.fact, slots: counts } };
    expect(restsOn(bare)?.share).toBeNull();
    expect(restsOn(bare)?.partly).toBeNull();
    const clause = "Worked out from 2 of its 3 parts, 70 of 100 by weight.";
    const told = { ...quiet, fact: { ...quiet.fact, slots: { ...quiet.fact.slots, share: "70", partly: clause } } };
    expect(restsOn(told)).toMatchObject({ share: "70", partly: clause, known: "2", parts: "3" });
  });

  test("test_a_band_that_rests_on_the_whole_of_its_recipe_says_nothing_though_its_fact_holds_a_share", () => {
    const leafy = mark("thrushcombe", "leafy");
    const told = { ...leafy, fact: { ...leafy.fact, slots: { ...leafy.fact.slots, share: "100", partly: "" } } };

    expect(restsOn(told)).toBeNull();
  });
});

describe("the figure that stands beside a vibe", () => {
  const pictured = (slug: string, tagId: string) =>
    GROUPS.flatMap((group) => portraitOf(profile(slug), meta)[group]).find((one) => one.tag.tag_id === tagId)?.pictured ?? null;

  test("test_it_is_one_a_person_can_picture_where_the_recipe_holds_one", () => {
    // The heaviest part of Food and drink is a count for each 1,000 homes. Beside it in the
    // recipe, and as heavy, is a share of the places within reach.
    expect(pictured("thrushcombe", "foodie")?.key).toBe("independents_nearby");
    expect(pictured("thrushcombe", "foodie")?.slots.value).toBe("84%");
    expect(pictured("thrushcombe", "everyday_on_foot")?.key).toBe("grocery_walk");
    // A walk in metres, and of the two walks the one that sits nearest the band of the vibe.
    expect(pictured("thrushcombe", "parks_close_by")?.key).toBe("park_large_proximity");
  });

  test("test_it_is_always_a_fact_of_a_part_of_that_vibe_with_its_source_and_date", () => {
    for (const data of profiles) {
      for (const one of GROUPS.flatMap((group) => portraitOf(data, meta)[group])) {
        if (one.pictured === null) continue;
        expect(one.parts.map((part) => part.fact?.fact_id)).toContain(one.pictured.fact_id);
        expect(one.pictured.sources.length).toBeGreaterThan(0);
        expect(one.pictured.as_of).not.toBe("");
      }
    }
  });

  test("test_where_no_part_is_easier_to_picture_it_is_the_one_the_api_names", () => {
    // Every part of Leafy is a share of land, and the API names the heaviest.
    expect(pictured("thrushcombe", "leafy")?.fact_id).toBe(
      profile("thrushcombe").portrait.others.find((one) => one.tag_id === "leafy")?.figure_fact_id,
    );
  });

  test("test_it_is_the_part_that_sits_nearest_the_band_of_the_vibe_so_that_it_never_reads_against_it", () => {
    // Seen in a browser: Quiet streets, "among the most here", beside 27% of homes near a main
    // road, where an area "around the middle" showed 22%. The band rests on three parts, and
    // the heaviest was shown whatever it said.
    expect(pictured("gorsebeck", "quiet_residential")?.key).toBe("evening_cluster_exposure");
    expect(pictured("gorsebeck", "quiet_residential")?.slots.value).toBe("1%");
    expect(pictured("foxholt", "quiet_residential")?.slots.value).toBe("14%");

    /** Where a part sits, read the way its recipe reads it: a part read from its low end is turned round. */
    const read = (part: { term: { reading: string }; fact: { slots: Record<string, string | undefined> } | null }) => {
      const band = Number(part.fact?.slots.band);
      return part.term.reading === "low" ? 6 - band : band;
    };
    let held = 0;
    for (const data of profiles) {
      for (const one of GROUPS.flatMap((group) => portraitOf(data, meta)[group])) {
        const shown = one.parts.find((part) => part.fact !== null && part.fact.fact_id === one.pictured?.fact_id);
        if (one.placed === null || shown === undefined || Number.isNaN(read(shown))) continue;
        const band = one.placed.band;
        const plain = (part: (typeof one.parts)[number]) => PICTURED.has(part.metric?.unit ?? "");
        const others = one.parts.filter(
          (part) =>
            part.fact !== null &&
            part.fact.template !== "feature_crime" &&
            plain(part) === plain(shown) &&
            !Number.isNaN(read(part)),
        );
        // No part that is as easy to picture sits nearer the band than the one that is shown.
        for (const other of others) expect(Math.abs(read(shown) - band)).toBeLessThanOrEqual(Math.abs(read(other) - band));
        held += 1;
      }
    }
    expect(held).toBeGreaterThan(100);
  });

  test("test_it_is_never_a_figure_of_recorded_crime_which_nobody_asked_for", () => {
    let held = 0;
    for (const data of profiles) {
      for (const one of GROUPS.flatMap((group) => portraitOf(data, meta)[group])) {
        if (one.figure?.template === "feature_crime") held += 1;
        expect(one.pictured?.template === "feature_crime").toBe(false);
      }
    }
    // The API does name one, for the vibe whose heaviest part it is.
    expect(held).toBeGreaterThan(0);
  });
});

describe("what an area is like, in short", () => {
  const short = (slug: string) => inShort(portraitOf(profile(slug), meta), meta.features);
  const ids = (slug: string) => short(slug).map((mark) => mark.tag.tag_id);

  test("test_it_holds_five_vibes_at_most_and_the_furthest_from_the_middle_are_chosen_first", () => {
    expect(IN_SHORT).toBe(5);
    for (const data of profiles) {
      const portrait = portraitOf(data, meta);
      const lines = inShort(portrait, meta.features);
      expect(lines.length).toBeLessThanOrEqual(IN_SHORT);
      // No vibe at an end is left out for one that is nearer the middle.
      const leftOut = shownOn(portrait)
        .filter((mark) => !lines.includes(mark) && !holdsRecordedCrime(mark.tag, meta.features))
        .filter((mark) => mark.placed !== null && mark.placed.spread_high - mark.placed.spread_low < 2);
      const nearest = Math.min(...lines.map((mark) => Math.abs((mark.placed?.band ?? 3) - 3)), 2);
      if (lines.length === IN_SHORT) {
        for (const mark of leftOut) expect(Math.abs((mark.placed?.band ?? 3) - 3)).toBeLessThanOrEqual(nearest);
      } else {
        // With room to spare, every vibe that is not in the middle is in it.
        for (const mark of leftOut) expect(mark.placed?.band).toBe(3);
      }
    }
  });

  test("test_it_reads_what_an_area_has_most_of_then_where_it_sits_between_two_ends_then_what_it_has_least_of", () => {
    expect(ids("thrushcombe")).toEqual(["village_feel", "foodie", "parks_close_by", "homes", "built_age"]);
    expect(short("thrushcombe").map((mark) => mark.placed?.band)).toEqual([5, 5, 5, 1, 5]);
  });

  test("test_it_says_what_an_area_has_least_of_as_well_as_what_it_has_most_of", () => {
    // Pellam Cross sits at an end of many vibes. What it has least of is not crowded out.
    expect(ids("pellam-cross")).toEqual(["well_connected", "everyday_on_foot", "homes", "family_amenities", "leafy"]);
    for (const data of profiles) {
      const portrait = portraitOf(data, meta);
      const lines = inShort(portrait, meta.features);
      const oneWay = shownOn(portrait).filter((mark) => mark.tag.shape === "one_way");
      const has = (from: number, to: number) => (mark: { placed: { band: number } | null }) =>
        (mark.placed?.band ?? 3) >= from && (mark.placed?.band ?? 3) <= to;
      if (oneWay.some(has(1, 1)) && lines.length === IN_SHORT) expect(lines.some(has(1, 1))).toBe(true);
      if (oneWay.some(has(5, 5)) && lines.length === IN_SHORT) expect(lines.some(has(5, 5))).toBe(true);
    }
  });

  test("test_every_vibe_in_it_is_one_the_api_placed_and_none_sits_in_the_middle", () => {
    for (const data of profiles) {
      const portrait = portraitOf(data, meta);
      const placed = shownOn(portrait).map((mark) => mark.tag.tag_id);
      for (const mark of inShort(portrait, meta.features)) {
        expect(placed).toContain(mark.tag.tag_id);
        expect(mark.placed?.band).not.toBe(3);
        // A mixed area sits at no one point, and is said in full where its line is.
        expect((mark.placed?.spread_high ?? 0) - (mark.placed?.spread_low ?? 0)).toBeLessThan(2);
      }
    }
  });

  test("test_a_vibe_that_holds_recorded_crime_is_in_no_line_of_it", () => {
    const street = meta.tags.find((tag) => tag.tag_id === "street_character");
    if (!street) throw new Error("The release holds no such vibe.");

    expect(holdsRecordedCrime(street, meta.features)).toBe(true);
    expect(meta.tags.filter((tag) => holdsRecordedCrime(tag, meta.features)).map((tag) => tag.tag_id)).toEqual([
      "street_character",
    ]);
    // Pellam Cross sits at the far end of it, and the summary does not say so: nobody asked.
    const pellam = portraitOf(profile("pellam-cross"), meta);
    expect(pellam.scales.find((mark) => mark.tag.tag_id === "street_character")?.placed?.band).toBe(5);
    for (const data of profiles) {
      expect(inShort(portraitOf(data, meta), meta.features).map((mark) => mark.tag.tag_id)).not.toContain(
        "street_character",
      );
    }
  });

  test("test_an_area_burro_can_place_on_one_vibe_has_one_line", () => {
    expect(ids("otterby-fields")).toEqual(["homes"]);
  });
});

describe("what a vibe cannot see", () => {
  test("test_what_every_vibe_cannot_see_is_said_once_and_the_rest_is_each_vibes_own", () => {
    const { common, own } = cannotSee(meta.tags, meta.tags);

    expect(common).toEqual(["One street or one home. An area is many streets."]);
    expect(own.map((one) => one.tag.tag_id)).toEqual(meta.tags.map((tag) => tag.tag_id));
    for (const { tag, lines } of own) {
      // Every line is the API's, word for word, and in its order.
      expect([...common, ...lines]).toEqual(tag.cannot_see);
      expect(lines.length).toBeGreaterThan(0);
    }
  });

  test("test_only_the_vibes_that_are_shown_say_what_they_cannot_see", () => {
    const shown = shownOn(portraitOf(profile("otterby-fields"), meta)).map((mark) => mark.tag);

    const { common, own } = cannotSee(shown, meta.tags);

    expect(common).toHaveLength(1);
    expect(own.map((one) => one.tag.label)).toEqual(["Houses or flats"]);
  });

  test("test_a_release_with_one_vibe_says_all_of_what_it_cannot_see_as_its_own", () => {
    const one = meta.tags.slice(0, 1);

    const { common, own } = cannotSee(one, one);

    // With nothing to hold it against, no line is known to be said of every vibe.
    expect(common).toEqual([]);
    expect(own[0]?.lines).toEqual(one[0]?.cannot_see);
  });
});

describe("where to start", () => {
  test("test_the_station_to_start_from_is_the_one_the_api_says_is_nearest", () => {
    const pellam = profile("pellam-cross");

    expect(pellam.stations.length).toBeGreaterThan(1);
    expect(nearestStation(pellam)?.template).toBe("station");
    expect(nearestStation(pellam)?.key).toBe(pellam.stations.find((station) => station.nearest)?.station_id);
  });

  test("test_an_area_with_no_station_fact_has_none_to_start_from", () => {
    const thrushcombe = profile("thrushcombe");

    expect(nearestStation({ ...thrushcombe, facts: thrushcombe.facts.filter((fact) => fact.kind !== "station") })).toBeNull();
  });
});
