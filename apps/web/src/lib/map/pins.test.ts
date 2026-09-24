import { apart, PIN_ROOM } from "./pins";

const distance = (one: readonly [number, number], other: readonly [number, number]) =>
  Math.hypot(one[0] - other[0], one[1] - other[1]);

/** Where each pin is drawn: where its area is, moved by what it was told to move by. */
function drawn(points: readonly { id: string; x: number; y: number }[]) {
  const moved = apart(points);
  return points.map((point) => {
    const [dx, dy] = moved.get(point.id) ?? [0, 0];
    return { id: point.id, at: [point.x + dx, point.y + dy] as const, by: [dx, dy] as const };
  });
}

describe("pins that would stand on top of each other", () => {
  test("test_pins_with_room_between_them_stay_where_their_areas_are", () => {
    const pins = drawn([
      { id: "a", x: 0, y: 0 },
      { id: "b", x: 100, y: 0 },
      { id: "c", x: 0, y: 100 },
    ]);

    expect(pins.map((pin) => pin.by)).toEqual([
      [0, 0],
      [0, 0],
      [0, 0],
    ]);
  });

  test("test_no_two_pins_are_drawn_nearer_than_a_pin_is_wide", () => {
    // Seen in a browser, on a map of a thousand areas: three of the first ten areas were
    // next to each other, and their pins stood on top of each other.
    const pins = drawn([
      { id: "1", x: 50, y: 50 },
      { id: "2", x: 52, y: 51 },
      { id: "3", x: 49, y: 53 },
      { id: "4", x: 51, y: 48 },
      { id: "5", x: 200, y: 200 },
    ]);

    for (const one of pins) {
      for (const other of pins) {
        if (one.id !== other.id) expect(distance(one.at, other.at)).toBeGreaterThanOrEqual(PIN_ROOM);
      }
    }
  });

  test("test_the_better_ranked_pin_keeps_its_place_and_the_other_moves_no_further_than_it_must", () => {
    const [first, second] = drawn([
      { id: "1", x: 50, y: 50 },
      { id: "2", x: 52, y: 51 },
    ]);

    expect(first?.by).toEqual([0, 0]);
    expect(distance(second?.by ?? [0, 0], [0, 0])).toBeGreaterThan(0);
    expect(distance(second?.by ?? [0, 0], [0, 0])).toBeLessThanOrEqual(PIN_ROOM * 1.5);
  });

  test("test_the_same_pins_are_always_moved_the_same_way", () => {
    const points = [
      { id: "1", x: 10, y: 10 },
      { id: "2", x: 11, y: 10 },
      { id: "3", x: 10, y: 11 },
    ];

    expect([...apart(points)]).toEqual([...apart(points)]);
    expect(apart([]).size).toBe(0);
  });
});
