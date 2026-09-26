import { AREAS_BUILT_AHEAD, builtAhead } from "@/lib/area/ahead";

const release = (count: number) => Array.from({ length: count }, (_, n) => ({ slug: `area-${n + 1}` }));

describe("which areas have their page built ahead of time", () => {
  test("test_a_build_makes_no_more_pages_of_areas_than_a_small_machine_can_answer_for", () => {
    const built = builtAhead(release(1002));

    expect(built).toHaveLength(AREAS_BUILT_AHEAD);
    expect(AREAS_BUILT_AHEAD).toBeLessThanOrEqual(50);
  });

  test("test_the_pages_that_are_built_are_the_first_of_the_release_in_its_own_order", () => {
    const areas = release(40);

    expect(builtAhead(areas)).toEqual(areas.slice(0, AREAS_BUILT_AHEAD));
  });

  test("test_a_release_with_fewer_areas_has_every_page_built", () => {
    const areas = release(7);

    expect(builtAhead(areas)).toEqual(areas);
  });

  test("test_the_list_it_was_given_is_left_as_it_was", () => {
    const areas = release(30);

    builtAhead(areas);

    expect(areas).toHaveLength(30);
  });
});
