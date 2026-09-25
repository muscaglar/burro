import { EXAMPLE_POOL } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";

import { bandsToDraw, canAnswer, examplesFor, isPlaced, placedOf, recipeOf, waitingOf } from "./holds";

const whole = recordedAnswer("get_meta", "meta").body.data;
const preview = recordedAnswer("get_meta", "preview/meta").body.data;
const listed = recordedAnswer("list_areas", "preview/areas").body.data;

describe("what the release of a page can answer", () => {
  test("test_a_vibe_is_placed_where_the_api_says_some_area_has_a_band_for_it", () => {
    expect(placedOf(preview, preview.tags).map((tag) => tag.tag_id)).toEqual([
      "quiet_residential",
      "parks_close_by",
      "homes",
    ]);
    expect(waitingOf(preview, preview.tags)).toHaveLength(11);
    expect(waitingOf(whole, whole.tags)).toEqual([]);
    expect(recipeOf(preview, "leafy")).toMatchObject({ held: 30, needed: 60, placed: false });
    // A vibe the API says nothing of is taken to be placed: the API answers for it.
    expect(isPlaced({ recipes: [] }, "leafy")).toBe(true);
  });

  test("test_a_thing_can_be_answered_only_where_the_release_holds_it", () => {
    const asked = ["budget", "commute", "tag:leafy", "tag:homes", "feature:air_no2", "feature:station_walk"];

    expect(asked.map((target) => canAnswer(whole, target))).toEqual([true, true, true, true, true, true]);
    expect(asked.map((target) => canAnswer(preview, target))).toEqual([false, false, false, true, true, false]);
    // A measure that is shown and ranked on alone in no search cannot be asked for.
    expect(preview.features.find((one) => one.feature_id === "road_major_exposure")?.rankable).toBe(false);
    expect(canAnswer(preview, "feature:road_major_exposure")).toBe(false);
  });

  test("test_the_examples_are_the_first_three_the_release_can_answer_the_whole_of", () => {
    expect(examplesFor(whole)).toEqual(EXAMPLE_POOL.slice(0, 3).map((example) => example.text));
    expect(examplesFor(preview)).toEqual(EXAMPLE_POOL.slice(3, 6).map((example) => example.text));
    // Where nothing can be answered, nothing is offered.
    expect(examplesFor({ ...preview, recipes: preview.recipes.map((held) => ({ ...held, placed: false })), features: [] })).toEqual([]);
  });

  test("test_only_the_bands_a_map_can_be_coloured_by_go_to_the_browser", () => {
    // Seen on a release of a thousand areas: the first page held eleven thousand rows of
    // bands, of which eight thousand said that an area could not be placed.
    const drawn = bandsToDraw(preview, listed.bands);

    expect(listed.bands).toHaveLength(14);
    expect(drawn.map((one) => one.tag_id)).toEqual(["quiet_residential", "parks_close_by", "homes"]);
    for (const one of listed.bands.filter((band) => !drawn.includes(band))) {
      expect(one.marks.every((mark) => mark.band === null)).toBe(true);
    }
  });
});
