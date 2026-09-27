/** @jest-environment node */

import { begun, following, landed, nowDrawn, settled, wasDrawn } from "./arrives";

const fresh = (row: { fresh: ReadonlySet<string> }) => [...row.fresh];

describe("which chips have just been added", () => {
  test("test_a_chip_that_is_added_arrives_and_every_chip_that_was_there_stays_where_it_is", () => {
    const row = settled(begun(["vibe:a", "tenure", "usual"], false));

    expect(fresh(following(row, ["vibe:a", "place:b", "tenure", "usual"]))).toEqual(["place:b"]);
    // Two at once, as when one press adds all that needs no choice.
    expect(fresh(following(row, ["vibe:a", "vibe:c", "place:b", "tenure", "usual"]))).toEqual(["vibe:c", "place:b"]);
  });

  test("test_a_chip_that_is_taken_off_brings_nothing_down", () => {
    const row = begun(["vibe:a", "place:b", "tenure"], true);

    expect(fresh(following(row, ["place:b", "tenure"]))).toEqual([]);
  });

  test("test_the_chips_of_a_search_that_was_not_drawn_before_all_arrive", () => {
    expect(fresh(begun(["vibe:a", "tenure"], false))).toEqual(["vibe:a", "tenure"]);
  });

  test("test_the_chips_of_a_search_that_was_drawn_before_are_there_and_none_arrives", () => {
    expect(fresh(begun(["vibe:a", "tenure"], true))).toEqual([]);
  });

  test("test_while_the_row_holds_the_place_of_chips_that_are_on_their_way_every_one_of_them_is_new", () => {
    // While a first sentence is read the row draws no chip. What comes of the words arrives.
    const holding = begun([], true);

    expect(fresh(following(holding, ["vibe:a", "place:b", "tenure", "usual"]))).toEqual([
      "vibe:a",
      "place:b",
      "tenure",
      "usual",
    ]);
  });

  test("test_with_the_chips_it_had_the_row_is_the_row_it_was_so_nothing_arrives_a_second_time", () => {
    const row = following(begun(["tenure"], true), ["vibe:a", "tenure"]);

    // The very row, so that what draws it is not made to draw again.
    expect(following(row, ["vibe:a", "tenure"])).toBe(row);
    expect(fresh(following(row, ["vibe:a", "tenure"]))).toEqual(["vibe:a"]);
  });

  test("test_what_arrived_has_settled_once_it_has_dropped_and_is_new_no_longer", () => {
    const row = following(begun(["tenure"], true), ["vibe:a", "tenure"]);

    const still = settled(row);

    expect(fresh(still)).toEqual([]);
    expect(still.keys).toEqual(["vibe:a", "tenure"]);
    // A row in which nothing is new is the row it was, so that it is not drawn again for nothing.
    expect(settled(still)).toBe(still);
    // What is added after that arrives, and what had settled stays.
    expect(fresh(following(still, ["vibe:a", "vibe:c", "tenure"]))).toEqual(["vibe:c"]);
  });

  test("test_a_chip_that_has_landed_is_new_no_longer_and_one_that_is_still_on_its_way_goes_on", () => {
    const row = following(begun(["tenure"], true), ["vibe:a", "place:b", "tenure"]);

    expect(fresh(landed(row, "vibe:a"))).toEqual(["place:b"]);
    expect(fresh(landed(landed(row, "vibe:a"), "place:b"))).toEqual([]);
    // What was there says nothing by ending a movement of its own: the row is the row it was.
    expect(landed(row, "tenure")).toBe(row);
    // Nor does one that had settled already, by a press that was made while it dropped.
    const still = settled(row);
    expect(landed(still, "vibe:a")).toBe(still);
  });

  test("test_a_search_is_known_by_being_the_very_search_and_by_nothing_it_holds", () => {
    const search = { holds: "a vibe" };
    const alike = { holds: "a vibe" };

    expect(wasDrawn(search)).toBe(false);
    nowDrawn(search);
    expect(wasDrawn(search)).toBe(true);
    // One that holds the same is another search, as the answer to the next press is.
    expect(wasDrawn(alike)).toBe(false);
  });
});
