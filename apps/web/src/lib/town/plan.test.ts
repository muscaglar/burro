/** @jest-environment node */
import type { BandNumber } from "@/content/bands";
import { recordedAnswer } from "@/lib/api/recorded";
import { VIBE_BANDS } from "@/lib/vibes";

import { bandsOf, NOTHING_KNOWN, type Bands } from "./bands";
import { FLOORS, litOf, LOTS, planOf, stateOf, WINDOWS, type Building, type Plan } from "./plan";
import { PARTS, type Part } from "./vibes";

const { areas } = recordedAnswer("list_areas", "areas").body.data;
const pageOf = (slug: string) => recordedAnswer("get_area", `area/${slug}`).body.data;

/** A band, or that there is none. */
const EVERY: readonly (BandNumber | null)[] = [null, ...VIBE_BANDS];
/** Every town there is: six ways for each of four parts. */
const TOWNS: readonly Bands[] = EVERY.flatMap((trees) =>
  EVERY.flatMap((height) => EVERY.flatMap((lit) => EVERY.map((roofs) => ({ trees, height, lit, roofs })))),
);
const MIDDLE: Bands = { trees: 3, height: 3, lit: 3, roofs: 3 };
const with_ = (part: Part, band: BandNumber | null, of: Bands = MIDDLE): Bands => ({ ...of, [part]: band });

const built = (plan: Plan): readonly Building[] => plan.buildings ?? [];
const sum = (counts: readonly number[]) => counts.reduce((total, count) => total + count, 0);
const floorsOf = (plan: Plan) => sum(built(plan).map(({ form }) => FLOORS[form]));
const windowsOf = (plan: Plan) => sum(built(plan).map(({ form }) => WINDOWS[form]));
const litIn = (plan: Plan) => sum(built(plan).map(({ lit }) => lit ?? 0));
const olderIn = (plan: Plan) => built(plan).filter(({ roof }) => roof === "older").length;
const rises = (counts: readonly number[]) => counts.every((count, at) => at === 0 || count > (counts[at - 1] ?? 0));

describe("the rule a town is built by", () => {
  test("test_two_areas_with_the_same_four_bands_are_drawn_the_same", () => {
    for (const bands of TOWNS) expect(planOf({ ...bands })).toEqual(planOf(bands));
    expect(TOWNS).toHaveLength(6 ** 4);
  });

  test("test_the_rule_takes_the_four_bands_and_nothing_else_so_no_name_rank_or_fit_can_move_it", () => {
    const told = { ...MIDDLE, name: "a name", rank: 1, fit: 99, score: 0.99 };

    expect(planOf.length).toBe(1);
    expect(planOf(told)).toEqual(planOf(MIDDLE));
  });

  test("test_every_band_draws_more_trees_than_the_band_before_it_and_the_least_draws_one", () => {
    const trees = VIBE_BANDS.map((band) => planOf(with_("trees", band)).trees ?? 0);

    expect(trees[0]).toBe(1);
    expect(rises(trees)).toBe(true);
  });

  test("test_a_town_is_taller_with_every_band_and_is_all_houses_at_one_end_and_all_blocks_at_the_other", () => {
    const plans = VIBE_BANDS.map((band) => planOf(with_("height", band)));

    expect(plans.map((plan) => built(plan).length)).toEqual(VIBE_BANDS.map(() => LOTS));
    expect(rises(plans.map(floorsOf))).toBe(true);
    expect(built(plans[0] ?? planOf(NOTHING_KNOWN)).map(({ form }) => form)).toEqual(["low", "low", "low", "low"]);
    expect(built(plans[4] ?? planOf(NOTHING_KNOWN)).map(({ form }) => form)).toEqual(["tall", "tall", "tall", "tall"]);
    // No building is lower than it was in the band before.
    for (const [at, plan] of plans.entries()) {
      const before = plans[at - 1];
      if (before === undefined) continue;
      built(plan).forEach(({ form }, lot) => {
        expect(FLOORS[form]).toBeGreaterThanOrEqual(FLOORS[built(before)[lot]?.form ?? "low"]);
      });
    }
  });

  test.each(VIBE_BANDS)(
    "test_more_windows_are_lit_with_every_band_one_at_the_least_and_all_at_the_most: a town of height %i",
    (height) => {
      const plans = VIBE_BANDS.map((band) => planOf({ ...MIDDLE, height, lit: band }));
      const windows = windowsOf(plans[0] ?? planOf(NOTHING_KNOWN));

      expect(rises(plans.map(litIn))).toBe(true);
      expect(litIn(plans[0] ?? planOf(NOTHING_KNOWN))).toBe(1);
      expect(litIn(plans[4] ?? planOf(NOTHING_KNOWN))).toBe(windows);
      expect(VIBE_BANDS.map((band) => litOf(band, windows))).toEqual(plans.map(litIn));
      for (const [at, plan] of plans.entries()) {
        built(plan).forEach(({ form, lit }, lot) => {
          // No building has more lit than it has windows, nor fewer than in the band before.
          expect(lit ?? -1).toBeLessThanOrEqual(WINDOWS[form]);
          expect(lit ?? -1).toBeGreaterThanOrEqual(built(plans[at - 1] ?? plan)[lot]?.lit ?? 0);
        });
      }
    },
  );

  test("test_the_lit_windows_of_a_town_are_shared_among_its_buildings_and_not_given_to_one", () => {
    // Half of the windows of every town are lit in the middle band, and no building is
    // more than a window from half of its own.
    for (const height of VIBE_BANDS) {
      for (const { form, lit } of built(planOf({ ...MIDDLE, height, lit: 3 }))) {
        expect(Math.abs((lit ?? 0) - WINDOWS[form] / 2)).toBeLessThanOrEqual(1);
      }
    }
  });

  test("test_every_roof_is_newer_at_one_end_and_older_at_the_other_with_one_more_older_at_each_band", () => {
    const plans = VIBE_BANDS.map((band) => planOf(with_("roofs", band)));

    expect(plans.map(olderIn)).toEqual([0, 1, 2, 3, 4]);
    expect(plans.every((plan) => built(plan).every(({ roof }) => roof !== null))).toBe(true);
    // A roof that is older stays older in every band after.
    for (const [at, plan] of plans.entries()) {
      built(plans[at - 1] ?? plan).forEach(({ roof }, lot) => {
        if (roof === "older") expect(built(plan)[lot]?.roof).toBe("older");
      });
    }
  });

  test("test_a_part_is_drawn_from_its_own_vibe_and_from_no_other", () => {
    // The trees of a town are the same whatever its buildings are, and its buildings are
    // as tall whatever is lit, and whatever roofs they have.
    for (const bands of TOWNS) {
      expect(planOf(bands).trees).toBe(planOf({ ...NOTHING_KNOWN, trees: bands.trees }).trees);
      expect(built(planOf(bands)).map(({ form }) => form)).toEqual(
        built(planOf({ ...NOTHING_KNOWN, height: bands.height })).map(({ form }) => form),
      );
      expect(built(planOf(bands)).map(({ roof }) => roof)).toEqual(
        built(planOf({ ...NOTHING_KNOWN, height: bands.height, roofs: bands.roofs })).map(({ roof }) => roof),
      );
      expect(built(planOf(bands)).map(({ lit }) => lit)).toEqual(
        built(planOf({ ...NOTHING_KNOWN, height: bands.height, lit: bands.lit })).map(({ lit }) => lit),
      );
    }
  });
});

describe("what is not known of a town", () => {
  test("test_nothing_known_draws_no_tree_and_no_building", () => {
    expect(planOf(NOTHING_KNOWN)).toEqual({ trees: null, buildings: null });
  });

  test.each(PARTS)("test_a_part_that_is_not_known_is_drawn_as_no_band_of_it_is_never_the_least_and_never_the_middle: %s", (part) => {
    const blank = planOf(with_(part, null));
    const known = VIBE_BANDS.map((band) => planOf(with_(part, band)));

    expect(known.filter((plan) => JSON.stringify(plan) === JSON.stringify(blank))).toEqual([]);
    expect(stateOf(with_(part, null), part)).toBe("blank");
    for (const band of VIBE_BANDS) expect(stateOf(with_(part, band), part)).toBe("drawn");
  });

  test("test_no_tree_is_drawn_where_trees_are_not_known_and_one_at_the_least_where_they_are", () => {
    expect(planOf(with_("trees", null)).trees).toBeNull();
    expect(VIBE_BANDS.map((band) => planOf(with_("trees", band)).trees).every((trees) => (trees ?? 0) >= 1)).toBe(true);
  });

  test("test_every_window_is_dark_where_lit_windows_are_not_known_and_one_is_lit_where_they_are", () => {
    expect(built(planOf(with_("lit", null))).map(({ lit }) => lit)).toEqual([null, null, null, null]);
    for (const band of VIBE_BANDS) expect(litIn(planOf(with_("lit", band)))).toBeGreaterThanOrEqual(1);
  });

  test("test_no_roof_is_drawn_where_roofs_are_not_known", () => {
    expect(built(planOf(with_("roofs", null))).map(({ roof }) => roof)).toEqual([null, null, null, null]);
  });

  test("test_where_height_is_not_known_no_building_is_drawn_whatever_is_known_of_windows_and_roofs", () => {
    for (const bands of TOWNS.filter(({ height }) => height === null)) {
      expect(planOf(bands).buildings).toBeNull();
      expect(stateOf(bands, "height")).toBe("blank");
      expect(stateOf(bands, "lit")).toBe(bands.lit === null ? "blank" : "unbuilt");
      expect(stateOf(bands, "roofs")).toBe(bands.roofs === null ? "blank" : "unbuilt");
      // The trees stand on the plot, and need no building.
      expect(stateOf(bands, "trees")).toBe(bands.trees === null ? "blank" : "drawn");
    }
  });

  test("test_towns_differ_wherever_what_can_be_drawn_of_them_differs", () => {
    const drawn = new Set(TOWNS.map((bands) => JSON.stringify(planOf(bands))));
    // Six ways for the trees. Then five heights, each with six ways for its windows and six
    // for its roofs, and one way where no building is drawn.
    expect(drawn.size).toBe(6 * (5 * 6 * 6 + 1));
  });
});

describe("the towns of the recorded release", () => {
  const towns = areas.map(({ slug, name }) => ({ name, bands: bandsOf(pageOf(slug).tags) }));
  const same = (one: Bands, other: Bands) => PARTS.every((part) => one[part] === other[part]);

  test("test_areas_are_drawn_alike_where_their_four_bands_are_alike_and_differ_where_they_differ", () => {
    for (const one of towns) {
      for (const other of towns) {
        const alike = JSON.stringify(planOf(one.bands)) === JSON.stringify(planOf(other.bands));
        expect([one.name, other.name, alike]).toEqual([one.name, other.name, same(one.bands, other.bands)]);
      }
    }
  });

  test("test_the_release_holds_the_hard_cases_an_area_with_one_part_known_and_areas_at_both_ends", () => {
    const known = towns.map(({ bands }) => PARTS.filter((part) => bands[part] !== null).length);

    expect(known.filter((count) => count === 1).length).toBeGreaterThan(0);
    expect(known.filter((count) => count === 4).length).toBeGreaterThan(10);
    for (const part of PARTS) {
      expect([part, towns.some(({ bands }) => bands[part] === 1), towns.some(({ bands }) => bands[part] === 5)]).toEqual([part, true, true]);
    }
  });
});
