/** @jest-environment node */
import { drawingOf, outlineOf, PLAIN, THING_KINDS, type ThingKind } from "./drawn";

// The drawings there are, for this test: few, so that what has none can be told from what has.
jest.mock("@/lib/art/names", () => ({
  ART: Object.fromEntries(
    [
      "thing-leafy",
      "thing-leafy-off",
      "thing-quiet-residential",
      "thing-plain",
      "thing-family-green",
      "thing-family-daily-life",
      // The drawing of a vibe whose id begins as the name of the thing of a family does.
      "thing-vibe-family-amenities",
      // And what stands for a group of measures, by the dimension the service gives them.
      "thing-family-crime",
      "thing-journey",
      "thing-budget",
      "thing-tenure",
      "thing-home",
      "thing-area",
      "thing-alike",
      "thing-usual",
    ].map((name) => [name, { width: 16, height: 16 }]),
  ),
}));

describe("which drawing stands for a thing", () => {
  test("test_a_vibe_is_drawn_by_the_drawing_named_for_the_id_the_service_gives", () => {
    expect(drawingOf({ kind: "tag", id: "leafy", family: "green" })).toBe("thing-leafy");
    // An id is written with underscores, and the name of a drawing with hyphens.
    expect(drawingOf({ kind: "tag", id: "quiet_residential", family: "streets_homes" })).toBe("thing-quiet-residential");
  });

  test("test_a_vibe_with_no_drawing_of_its_own_is_drawn_by_its_family", () => {
    expect(drawingOf({ kind: "tag", id: "parks_close_by", family: "green" })).toBe("thing-family-green");
    expect(drawingOf({ kind: "tag", id: "well_connected", family: "daily_life" })).toBe("thing-family-daily-life");
  });

  test("test_what_has_no_drawing_and_no_family_that_is_drawn_is_the_plain_one_and_never_nothing", () => {
    expect(PLAIN).toBe("thing-plain");
    expect(drawingOf({ kind: "tag", id: "built_age", family: "streets_homes" })).toBe(PLAIN);
    expect(drawingOf({ kind: "tag", id: "a_vibe_of_a_later_release", family: "a_family_of_a_later_release" })).toBe(PLAIN);
    expect(drawingOf({ kind: "feature", id: "homes_flats", family: "streets_homes" })).toBe(PLAIN);
    // A vibe that comes with no id and no family at all is drawn too, and so is a measure.
    expect(drawingOf({ kind: "tag" })).toBe(PLAIN);
    expect(drawingOf({ kind: "feature", id: "air_no2", family: null })).toBe(PLAIN);
    expect(drawingOf({ kind: "feature" })).toBe(PLAIN);
  });

  test("test_a_measure_is_drawn_by_its_family_and_never_by_a_drawing_that_happens_to_bear_its_id", () => {
    expect(drawingOf({ kind: "feature", id: "park_proximity", family: "green" })).toBe("thing-family-green");
    // `thing-leafy` is the drawing of a vibe, whatever a measure may come to be called.
    expect(drawingOf({ kind: "feature", id: "leafy", family: "green" })).toBe("thing-family-green");
    expect(drawingOf({ kind: "feature", id: "journey", family: "green" })).toBe("thing-family-green");
  });

  test("test_a_vibe_is_never_drawn_by_the_drawing_of_a_kind_or_of_a_family_whatever_it_is_called", () => {
    // A later release may call a vibe `budget`, or `family_green`. The purse is the budget's.
    expect(drawingOf({ kind: "tag", id: "budget", family: "green" })).toBe("thing-family-green");
    expect(drawingOf({ kind: "tag", id: "journey", family: null })).toBe(PLAIN);
    expect(drawingOf({ kind: "tag", id: "plain", family: "green" })).toBe("thing-family-green");
    expect(drawingOf({ kind: "tag", id: "family_green", family: "daily_life" })).toBe("thing-family-daily-life");
  });

  test("test_a_vibe_whose_id_begins_as_the_thing_of_a_family_does_is_drawn_by_a_drawing_of_its_own", () => {
    // `thing-family-amenities` would be the thing of a family called amenities. So the
    // drawing of such a vibe is named for a vibe outright, and is its own: it was drawn, and
    // the vibe stood under the drawing of its family.
    expect(drawingOf({ kind: "tag", id: "family_amenities", family: "daily_life" })).toBe("thing-vibe-family-amenities");
    // One that nobody has drawn falls to its family still, and never to the family it is named like.
    expect(drawingOf({ kind: "tag", id: "family_green", family: "daily_life" })).toBe("thing-family-daily-life");
    expect(drawingOf({ kind: "tag", id: "family_crime", family: null })).toBe(PLAIN);
    // No id leads to the drawing of another vibe by being written as the name of one is.
    expect(drawingOf({ kind: "tag", id: "vibe_family_amenities", family: "green" })).toBe("thing-family-green");
    // And a measure is drawn by its family, whatever it is called.
    expect(drawingOf({ kind: "feature", id: "family_amenities", family: "green" })).toBe("thing-family-green");
    expect(drawingOf({ kind: "feature", id: "vibe_family_amenities", family: null })).toBe(PLAIN);
  });

  test("test_a_group_of_measures_that_is_of_no_family_is_drawn_by_the_dimension_it_is_handed_as_a_family_is", () => {
    // The service puts recorded crime in no family, and says of each measure what dimension
    // it is of. A group of such measures hands that on, and is drawn as a family is.
    expect(drawingOf({ kind: "feature", family: "crime" })).toBe("thing-family-crime");
    expect(drawingOf({ kind: "feature", id: "crime_burglary_theft", family: "crime" })).toBe("thing-family-crime");
    // A dimension with no drawing is drawn plain, as a family with none is.
    expect(drawingOf({ kind: "feature", family: "air_noise" })).toBe(PLAIN);
  });

  test("test_a_thing_in_outline_is_drawn_by_the_drawing_of_its_outline_where_it_has_one", () => {
    expect(outlineOf("thing-leafy")).toBe("thing-leafy-off");
    // A thing that has none has its outline cut from its own drawing, by the style sheet.
    expect(outlineOf("thing-quiet-residential")).toBeNull();
    expect(outlineOf(PLAIN)).toBeNull();
  });

  test("test_a_vibe_is_never_drawn_by_the_outline_of_another_whatever_it_is_called", () => {
    // A later release may call a vibe `leafy_off`. The outline of leafy is leafy's.
    expect(drawingOf({ kind: "tag", id: "leafy_off", family: "green" })).toBe("thing-family-green");
    expect(drawingOf({ kind: "tag", id: "leafy_off", family: null })).toBe(PLAIN);
  });

  test("test_each_kind_that_is_one_thing_has_its_own_drawing_by_the_name_that_was_promised", () => {
    const one: readonly [ThingKind, string][] = [
      ["place", "thing-journey"],
      ["budget", "thing-budget"],
      ["tenure", "thing-tenure"],
      ["home", "thing-home"],
      ["area", "thing-area"],
      ["alike", "thing-alike"],
      ["usual", "thing-usual"],
    ];

    expect(one.map(([kind]) => [kind, drawingOf({ kind, id: "whatever_it_is_handed", family: "green" })])).toEqual(one);
    // Every kind but a vibe and a measure is one of these.
    expect(THING_KINDS.filter((kind) => kind !== "tag" && kind !== "feature").sort()).toEqual(one.map(([kind]) => kind).sort());
  });
});
