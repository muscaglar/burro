/** @jest-environment node */
/**
 * The words for the codes the API sends. A code is the API's and the word for it is the
 * website's, so each word must be true of what the code does.
 */

import { COMBINE, DIMENSION, DIMENSION_ORDER, DIRECTION, POLARITY, PT_BASIS, READING, READING_TOWARDS } from "./labels";

describe("how a measurement of a vibe is read", () => {
  test("test_it_says_which_way_a_figure_counts_in_words_that_name_the_vibe_as_a_vibe", () => {
    // "Counts towards the vibe" was read twice: towards it from where. A figure that is
    // higher, or lower, means more of the vibe, and the words say so.
    expect(READING.high).toMatch(/^A higher figure\b.*\bmore of this vibe\b/);
    expect(READING.low).toMatch(/^A lower figure\b.*\bmore of this vibe\b/);
  });

  test("test_a_scale_names_the_end_a_figure_counts_towards_and_never_calls_an_end_more", () => {
    // Neither end of a scale is more of anything: it is one end or the other, by its name.
    expect(READING_TOWARDS.high("Flats")).toBe("A higher figure counts towards Flats");
    expect(READING_TOWARDS.low("Buzzy")).toBe("A lower figure counts towards Buzzy");
  });
});

describe("which way a measurement counts", () => {
  test("test_it_says_whether_a_higher_or_a_lower_figure_ranks_an_area_higher_and_calls_neither_better", () => {
    // "A higher figure counts as better" stood under a measurement of who lives somewhere,
    // and read as a judgement of them. Which way a figure counts is kept to the letter.
    expect(POLARITY.more).toMatch(/^A higher figure ranks an area higher$/);
    expect(POLARITY.less).toMatch(/^A lower figure ranks an area higher$/);
    expect(POLARITY.either).toMatch(/^You choose whether a higher or a lower figure\b/);
    expect(DIRECTION.more).toMatch(/^A higher figure\b/);
    expect(DIRECTION.less).toMatch(/^A lower figure\b/);
    for (const words of [...Object.values(POLARITY), ...Object.values(DIRECTION)]) {
      expect(words).not.toMatch(/\b(better|best|worse|worst|good|bad)\b/i);
    }
  });
});

describe("which journey counts, and which time", () => {
  test("test_the_journey_that_counts_is_the_one_that_does_least_well_against_its_limit_and_not_the_slowest", () => {
    // The API's `slowest` is the journey worth least against its own limit, which need not
    // be the one that takes the most minutes (contract, section 6.4). "Worst" is a word of
    // verdict, and the line under the journeys of a result says "least well".
    expect(COMBINE.slowest).toMatch(/does least well against its limit/);
    expect(COMBINE.slowest).not.toMatch(/slowest|longest|worst/);
    expect(COMBINE.mean).toMatch(/\baverage\b/);
  });

  test("test_each_way_of_timing_a_journey_says_which_time_counts", () => {
    expect(PT_BASIS.typical).toMatch(/\btypical\b/);
    expect(PT_BASIS.just_missed).toMatch(/\bjust miss\b/);
  });
});

describe("the groups of what is measured", () => {
  test("test_every_group_has_a_name_and_recorded_crime_is_the_last_of_them", () => {
    expect([...DIMENSION_ORDER].sort()).toEqual(Object.keys(DIMENSION).sort());
    expect(DIMENSION_ORDER.at(-1)).toBe("crime");
    // Who lived there comes after what is there.
    expect(DIMENSION_ORDER.indexOf("residents")).toBeGreaterThan(DIMENSION_ORDER.indexOf("homes"));
    // What was recorded is said to be recorded, and who was counted is said to have lived there.
    expect(DIMENSION.crime).toBe("Recorded crime");
    expect(DIMENSION.residents).toMatch(/\bat the census\b/);
  });

  test("test_the_group_that_holds_the_bus_stops_of_an_area_names_them", () => {
    // Seen in a browser: under "Stations" the first two figures were of bus routes and bus stops.
    expect(DIMENSION.station_access).toMatch(/\bStations\b/);
    expect(DIMENSION.station_access).toMatch(/\bbus stops\b/);
  });
});
