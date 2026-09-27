import type { Bounds } from "@/lib/map/project";

import { fitFor, isStrip, PADDING, PADDING_OF_A_STRIP } from "./strip";

/** A city wider than it is high, as the made-up one is. */
const CITY: Bounds = [
  [-0.4, 51.3],
  [0.2, 51.7],
];

describe("the map as a strip", () => {
  test("test_a_window_lower_than_half_its_width_is_a_strip_and_no_other_is", () => {
    // Over the two ways in, on a phone: 358 wide and 120 high.
    expect(isStrip({ width: 358, height: 120 })).toBe(true);
    // After a search on a phone, and beside the answer on a desk.
    expect(isStrip({ width: 358, height: 300 })).toBe(false);
    expect(isStrip({ width: 519, height: 386 })).toBe(false);
    expect(isStrip({ width: 358, height: 179 })).toBe(false);
    expect(isStrip({ width: 358, height: 178 })).toBe(true);
  });

  test("test_a_window_that_is_not_laid_out_is_no_strip", () => {
    // A browser that lays nothing out, as the browser of a test, and a window that is not drawn.
    expect(isStrip({ width: 0, height: 0 })).toBe(false);
    expect(isStrip({ width: 358, height: 0 })).toBe(false);
  });

  test("test_in_a_strip_the_city_is_drawn_as_wide_as_the_window", () => {
    const { bounds, padding } = fitFor(CITY, { width: 358, height: 120 });
    const [[west, south], [east, north]] = bounds;

    // From its west to its east, about its middle, and so little of its height that the width decides.
    expect([west, east]).toEqual([-0.4, 0.2]);
    expect((south + north) / 2).toBeCloseTo(51.5, 10);
    expect(north - south).toBeGreaterThan(0);
    expect(north - south).toBeLessThan((0.4 * 120) / 358 / 4);
    expect(padding).toBe(PADDING_OF_A_STRIP);
    expect(PADDING_OF_A_STRIP).toBeLessThan(PADDING);
  });

  test("test_in_any_other_window_the_whole_city_is_shown_with_room_round_it", () => {
    for (const window of [
      { width: 358, height: 300 },
      { width: 519, height: 386 },
      { width: 0, height: 0 },
    ]) {
      expect(fitFor(CITY, window)).toEqual({ bounds: CITY, padding: PADDING });
    }
  });
});
