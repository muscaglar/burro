/** @jest-environment node */
import { WAY_OF_ENDS, WAYS_OF_ENDS } from "./look";
import { BLANK, ENDS, NO_PICTURE, pictureAtEnd, pictureOfEnd, picturesAtEnds } from "./picture";

// The drawings there are, for this test: few, so that what has none can be told from what has.
jest.mock("@/lib/art/names", () => ({
  ART: Object.fromEntries(
    [
      ...["key-houses", "key-flats", "key-least", "key-most", "key-blank", "key-a-b", "thing-leafy"],
      ...["end-blank", "end-leafy-low", "end-leafy-high", "end-quiet-residential-low", "end-quiet-residential-high"],
      // A vibe of which one end alone was drawn, and what is no end of any vibe.
      ...["end-half-drawn-low", "end-of-the-line"],
      // A vibe of which one end was drawn a second way, and one of which a second way alone was drawn.
      ...["end-leafy-low-b", "end-only-second-low-b", "end-only-second-high-b"],
    ].map((name) => [name, { width: 16, height: 16 }]),
  ),
}));

describe("which picture stands at an end of the gauge of a vibe", () => {
  test("test_an_end_is_drawn_by_the_picture_named_for_the_id_of_its_vibe_and_for_which_end_it_is", () => {
    expect(ENDS).toEqual(["low", "high"]);
    expect(pictureAtEnd("leafy", "low")).toBe("end-leafy-low");
    expect(pictureAtEnd("leafy", "high")).toBe("end-leafy-high");
    expect(picturesAtEnds("leafy")).toEqual(["end-leafy-low", "end-leafy-high"]);
  });

  test("test_an_id_is_read_as_a_drawing_is_named_with_every_underscore_a_hyphen", () => {
    expect(picturesAtEnds("quiet_residential")).toEqual(["end-quiet-residential-low", "end-quiet-residential-high"]);
    expect(picturesAtEnds("QUIET_RESIDENTIAL")).toEqual(["end-quiet-residential-low", "end-quiet-residential-high"]);
  });

  test("test_a_vibe_with_no_picture_has_the_blank_one_at_both_ends_and_is_never_drawn_as_nothing", () => {
    expect(NO_PICTURE).toBe("end-blank");
    expect(picturesAtEnds("a_vibe_of_a_later_release")).toEqual([NO_PICTURE, NO_PICTURE]);
    for (const none of ["", null, undefined]) expect(picturesAtEnds(none)).toEqual([NO_PICTURE, NO_PICTURE]);
  });

  test("test_the_two_are_opposites_so_a_vibe_with_one_of_them_has_the_blank_one_at_both_ends", () => {
    // One picture says nothing without the other: little of a thing is known by much of it.
    expect(picturesAtEnds("half_drawn")).toEqual([NO_PICTURE, NO_PICTURE]);
    expect(pictureAtEnd("half_drawn", "low")).toBe(NO_PICTURE);
  });

  test("test_an_end_that_was_drawn_two_ways_is_drawn_the_way_that_is_chosen_and_the_first_where_it_has_no_second", () => {
    expect(WAYS_OF_ENDS).toEqual(["first", "second"]);
    // What the website is left on.
    expect(WAY_OF_ENDS).toBe("first");
    expect(picturesAtEnds("leafy")).toEqual(picturesAtEnds("leafy", "first"));
    expect(picturesAtEnds("leafy", "first")).toEqual(["end-leafy-low", "end-leafy-high"]);
    // The second way of the one end, and the first of the other, which has no second.
    expect(picturesAtEnds("leafy", "second")).toEqual(["end-leafy-low-b", "end-leafy-high"]);
    expect(pictureAtEnd("leafy", "low", "second")).toBe("end-leafy-low-b");
    expect(picturesAtEnds("quiet_residential", "second")).toEqual(["end-quiet-residential-low", "end-quiet-residential-high"]);
  });

  test("test_a_second_way_stands_for_a_first_and_never_by_itself", () => {
    // A vibe has its pictures, of which some may be drawn a second way. One that has a
    // second way and no first has the blank one, whichever way is chosen.
    expect(picturesAtEnds("only_second", "second")).toEqual([NO_PICTURE, NO_PICTURE]);
    expect(picturesAtEnds("only_second", "first")).toEqual([NO_PICTURE, NO_PICTURE]);
    // And no vibe is drawn by the second way of another by being named as one is.
    expect(picturesAtEnds("leafy_low", "first")).toEqual([NO_PICTURE, NO_PICTURE]);
  });

  test("test_nothing_but_the_two_ends_of_a_vibe_is_taken_for_one", () => {
    // Whatever an id holds, what is chosen is named for a vibe and an end, or is the blank one.
    expect(pictureAtEnd("of_the", "line" as never)).toBe(NO_PICTURE);
    expect(picturesAtEnds("blank")).toEqual([NO_PICTURE, NO_PICTURE]);
    expect(picturesAtEnds("../key-houses")).toEqual([NO_PICTURE, NO_PICTURE]);
    expect(picturesAtEnds("leafy-low")).toEqual([NO_PICTURE, NO_PICTURE]);
  });
});

describe("which picture stands at an end of a scale", () => {
  test("test_an_end_is_drawn_by_the_picture_named_for_what_the_service_calls_it", () => {
    expect(pictureOfEnd("Houses")).toBe("key-houses");
    expect(pictureOfEnd("Flats")).toBe("key-flats");
    // The ends of a vibe that runs one way, as the website names them.
    expect(pictureOfEnd("least")).toBe("key-least");
    expect(pictureOfEnd("most")).toBe("key-most");
  });

  test("test_a_name_is_read_as_a_drawing_is_named_whatever_it_is_written_with", () => {
    expect(pictureOfEnd("  HOUSES ")).toBe("key-houses");
    expect(pictureOfEnd("A, b")).toBe("key-a-b");
    expect(pictureOfEnd("a_b")).toBe("key-a-b");
  });

  test("test_an_end_with_no_picture_takes_the_blank_one_and_is_never_drawn_as_nothing", () => {
    expect(BLANK).toBe("key-blank");
    expect(pictureOfEnd("An end of a later release")).toBe(BLANK);
    expect(pictureOfEnd("")).toBe(BLANK);
    // A picture that is no picture of an end is not taken for one, whatever the end is called.
    expect(pictureOfEnd("leafy")).toBe(BLANK);
    expect(pictureOfEnd("blank")).toBe(BLANK);
  });
});
