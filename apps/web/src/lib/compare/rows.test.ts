/** @jest-environment node */
import { recordedAnswer } from "@/lib/api/recorded";
import type { CompareData } from "@/lib/api/schema";

import { drawnRows, isJourney } from "./rows";

/** A search with one journey. */
const three: CompareData = recordedAnswer("compare", "compare-three").body.data;
/** A search with two: one area has no time for one of them, and one area is listed apart. */
const two: CompareData = recordedAnswer("compare", "compare-two-journeys").body.data;

const journeysOf = (data: CompareData) => drawnRows(data).filter((row) => row.journey);

describe("the rows of what counts, as they are drawn", () => {
  test("test_every_row_is_drawn_as_the_api_gave_it_and_in_its_order", () => {
    for (const data of [three, two]) {
      const drawn = drawnRows(data);

      expect(drawn.map((one) => one.row)).toEqual(data.rows);
      for (const one of drawn) {
        expect(one.cells.map((cell) => cell.cell)).toEqual(
          data.areas.map((area) => one.row.cells.find((cell) => cell.area_id === area.area_id)),
        );
      }
    }
  });

  test("test_a_row_that_is_no_journey_names_no_place", () => {
    const others = drawnRows(two).filter((row) => !row.journey);

    expect(others.length).toBeGreaterThan(3);
    expect(others.map((row) => row.place)).toEqual(others.map(() => null));
  });

  test("test_a_row_of_one_journey_names_the_place_every_area_is_timed_to", () => {
    const drawn = journeysOf(three);

    expect(drawn).toHaveLength(1);
    expect(drawn[0]?.place).toBe(drawn[0]?.row.place?.name);
    expect(drawn[0]?.place).toBe("Cindermoor Works");
  });

  test("test_with_two_journeys_there_is_one_row_for_each_and_the_same_destination_across_a_row", () => {
    const drawn = journeysOf(two);

    expect(drawn.map((row) => row.place)).toEqual(["Cindermoor Works", "Wexmoor University"]);
    for (const row of drawn) {
      // Every area is in the row, and the fact of each cell is of a journey to the row's place.
      expect(row.cells.map((cell) => cell.area.area_id)).toEqual(two.areas.map((area) => area.area_id));
      for (const cell of row.cells) expect(cell.fact?.slots.place).toBe(row.place);
    }
  });

  test("test_a_journey_with_no_time_has_a_cell_that_cites_the_fact_that_says_so", () => {
    const [, toTheCampus] = journeysOf(two);
    const none = toTheCampus?.cells.filter((cell) => cell.fact?.template === "missing_journey") ?? [];

    expect(none.map((cell) => cell.area.name)).toEqual(["Gorsebeck"]);
    expect(none[0]?.cell?.value).toBeNull();
    // An area that is listed apart is timed all the same, in every row of a journey.
    const apart = two.areas.find((area) => area.status === "character_unknown");
    for (const row of journeysOf(two)) {
      const cell = row.cells.find((one) => one.area.area_id === apart?.area_id);
      expect(cell?.fact?.kind).toBe("travel");
    }
  });

  test("test_a_journey_is_known_by_the_place_of_its_row_and_not_by_what_the_row_is_called", () => {
    const [journey] = two.rows.filter((row) => row.place !== null);
    if (journey === undefined) throw new Error("the recorded comparison holds no journey");

    expect(isJourney(journey)).toBe(true);
    // The name of a row is the API's to change. A row that names no place is no journey.
    expect(isJourney({ place: journey.place })).toBe(true);
    expect(isJourney({ ...journey, place: null })).toBe(false);
    expect(two.rows.filter((row) => row.component === "commute")).toEqual([]);
  });

  test("test_every_row_has_a_name_of_its_own_so_that_none_is_drawn_over_another", () => {
    for (const data of [three, two]) {
      const keys = drawnRows(data).map((row) => row.key);
      expect(new Set(keys).size).toBe(keys.length);
    }
    // Two rows the API gave one name are still two rows.
    const twice = { ...three, rows: [...three.rows, ...three.rows] };
    expect(new Set(drawnRows(twice).map((row) => row.key)).size).toBe(twice.rows.length);
  });

  test("test_only_the_first_row_of_the_journeys_says_what_the_journeys_count_for", () => {
    // The journeys count as one thing, and each of their rows holds the weight of them all.
    expect(new Set(two.rows.filter(isJourney).map((row) => row.weight)).size).toBe(1);
    expect(journeysOf(two).map((row) => row.first)).toEqual([true, false]);
    expect(journeysOf(three).map((row) => row.first)).toEqual([true]);
    // Every other row says its own weight.
    expect(drawnRows(two).filter((row) => !row.journey).every((row) => row.first)).toBe(true);
  });
});
