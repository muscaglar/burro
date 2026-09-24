/** @jest-environment node */
import { recordedAnswer, recordedError } from "@/lib/api/recorded";

import { chosenFrom, isEnough, isFull, LEAST_COMPARED, MOST_COMPARED, toggled, type Chosen } from "./list";

const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const pick = (count: number): Chosen[] =>
  areas.slice(0, count).map(({ area_id, slug, name }) => ({ area_id, slug, name }));

describe("the areas chosen to compare", () => {
  test("test_a_comparison_takes_two_to_four_areas_as_the_api_does", () => {
    // The API refuses one area, and says how many it takes.
    const refusal = recordedError("compare-invalid").body.error;

    expect(refusal.message).toBe(`A comparison takes ${LEAST_COMPARED} to ${MOST_COMPARED} different areas.`);
    expect(refusal.fields).toEqual([{ path: "area_ids", problem: "out_of_range" }]);
    expect([0, 1, 2, 3, 4].map((count) => isEnough(pick(count)))).toEqual([false, false, true, true, true]);
    expect([3, 4].map((count) => isFull(pick(count)))).toEqual([false, true]);
  });

  test("test_no_more_than_four_areas_are_held_to_compare", () => {
    const held = pick(6).reduce<readonly Chosen[]>((list, area) => toggled(list, area), []);

    expect(held.map((area) => area.area_id)).toEqual(pick(4).map((area) => area.area_id));
  });

  test("test_choosing_an_area_twice_takes_it_out", () => {
    const [first, second] = pick(2) as [Chosen, Chosen];

    const held = toggled(toggled(toggled([], first), second), first);

    expect(held).toEqual([second]);
  });

  test("test_only_the_id_the_slug_and_the_name_of_an_area_are_kept", () => {
    const whole = areas[0];
    if (!whole) throw new Error("The release has no area.");

    const [kept] = toggled([], whole);

    expect(Object.keys(kept ?? {}).sort()).toEqual(["area_id", "name", "slug"]);
  });
});

describe("the areas a comparison's address names", () => {
  test("test_the_areas_are_the_ones_the_slugs_name_in_the_order_given", () => {
    const { chosen, unknown, dropped } = chosenFrom(["pellam-cross", "alderwick"], areas);

    expect(chosen.map((area) => area.name)).toEqual(["Pellam Cross", "Alderwick"]);
    expect([unknown, dropped]).toEqual([0, 0]);
  });

  test("test_a_slug_the_release_lacks_is_counted_and_never_kept", () => {
    const { chosen, unknown } = chosenFrom(["alderwick", "nowhere-at-all", "zqxcanary7431"], areas);

    expect(chosen.map((area) => area.slug)).toEqual(["alderwick"]);
    expect(unknown).toBe(2);
    expect(JSON.stringify(chosen)).not.toContain("zqxcanary7431");
  });

  test("test_an_area_named_twice_is_compared_once", () => {
    const { chosen, unknown, dropped } = chosenFrom(["alderwick", "alderwick", "cindermoor"], areas);

    expect(chosen.map((area) => area.slug)).toEqual(["alderwick", "cindermoor"]);
    expect([unknown, dropped]).toEqual([0, 0]);
  });

  test("test_areas_beyond_the_fourth_are_left_out_and_counted", () => {
    const slugs = areas.slice(0, 6).map((area) => area.slug);

    const { chosen, dropped } = chosenFrom(slugs, areas);

    expect(chosen.map((area) => area.slug)).toEqual(slugs.slice(0, 4));
    expect(dropped).toBe(2);
  });
});
