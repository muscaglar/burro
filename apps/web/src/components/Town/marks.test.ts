/** @jest-environment node */
/**
 * What marks a blank in a town is drawn whole. Where a building would stand, where a tree
 * would, and the top of a wall whose roof is not known were each drawn in dots or in
 * dashes, as Town Map drew them. A person who walked the website did not know what an edge
 * in pieces was for, and asked for none: so each is one line, with no gap in it.
 *
 * It reads the drawings as they are written, one character a pixel.
 */

import { drawings, frameOf, type Frame } from "@/lib/town/picture";

import { themes } from "../../../test/support/contrast";

const { light } = themes();
const colour = (token: string) => (light[token] ?? "").toLowerCase();
const SHADE = colour("--shade");
const INK = colour("--ink");

const from = drawings();

interface Pixel {
  readonly x: number;
  readonly y: number;
}

const BY_A_SIDE = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
] as const;
const BY_A_CORNER = [
  [1, 1],
  [1, -1],
  [-1, 1],
  [-1, -1],
] as const;

/** Every pixel of a frame that is drawn, with the colour it is drawn in. */
const drawnOf = (frame: Frame) =>
  frame.flatMap((row, y) => row.flatMap((pixel, x) => (pixel === null ? [] : [{ x, y, colour: pixel }])));

/** How many pixels of a line touch a pixel of it, by one of the ways given. */
const touching = (line: readonly Pixel[], one: Pixel, how: readonly (readonly [number, number])[]) =>
  line.filter((other) => how.some(([across, down]) => other.x === one.x + across && other.y === one.y + down)).length;

describe("what marks a blank in a town", () => {
  test("test_where_a_building_would_stand_is_marked_out_by_one_whole_line", () => {
    // It was a rectangle of dots, no two of which touched. It is the same rectangle, whole:
    // every pixel of it touches two others by a side, so the line has no gap and no end.
    const lot = frameOf({ drawing: "town-lot", frame: 0 }, from);
    const line = drawnOf(lot);

    expect(line.length).toBeGreaterThanOrEqual(8);
    expect(new Set(line.map((pixel) => pixel.colour))).toEqual(new Set([SHADE]));
    expect(line.filter((one) => touching(line, one, BY_A_SIDE) !== 2)).toEqual([]);
    // It is an edge and no slab: the meadow shows inside it.
    expect(lot[1]?.[1]).toBeNull();
    expect(lot[Math.floor(lot.length / 2)]?.[Math.floor((lot[0]?.length ?? 0) / 2)]).toBeNull();
  });

  test("test_where_a_tree_would_stand_is_marked_out_by_one_whole_ring", () => {
    const place = frameOf({ drawing: "town-trees", frame: 0 }, from);
    const ring = drawnOf(place);

    expect(ring.length).toBeGreaterThanOrEqual(8);
    expect(new Set(ring.map((pixel) => pixel.colour))).toEqual(new Set([SHADE]));
    // A ring is round, so it turns by a corner: every pixel of it touches two others, by a
    // side or by a corner, and none stands alone.
    expect(ring.filter((one) => touching(ring, one, [...BY_A_SIDE, ...BY_A_CORNER]) !== 2)).toEqual([]);
    // Along its length it runs by a side. Only where it turns, at either hand, does a
    // pixel touch the two beside it by a corner.
    const turns = ring.filter((one) => touching(ring, one, BY_A_SIDE) === 0);
    expect(turns).toHaveLength(2);
    expect(turns.filter((one) => touching(ring, one, BY_A_CORNER) !== 2)).toEqual([]);
    // The meadow shows inside it.
    const rows = [...new Set(ring.map((pixel) => pixel.y))].sort((one, other) => one - other);
    expect(rows).toHaveLength(3);
    expect(place[rows[1] ?? 0]?.filter((pixel) => pixel !== null)).toHaveLength(2);
  });

  test("test_a_wall_whose_roof_is_not_known_is_closed_by_one_whole_line", () => {
    const bare = frameOf({ drawing: "town-roofs", frame: 0 }, from);
    const drawn = bare.filter((row) => row.some((pixel) => pixel !== null));

    // One row, the last: nothing is drawn over the wall.
    expect(drawn).toHaveLength(1);
    expect(bare.indexOf(drawn[0] ?? [])).toBe(bare.length - 1);
    // From one corner of the wall to the other with no gap: ink at each corner, and one
    // colour between them. It was shade and page by turns, which is a line of dashes.
    const row = drawn[0] ?? [];
    const first = row.findIndex((pixel) => pixel !== null);
    const last = row.length - 1 - [...row].reverse().findIndex((pixel) => pixel !== null);
    const line = row.slice(first, last + 1);
    expect(line.includes(null)).toBe(false);
    expect([line[0], line[line.length - 1]]).toEqual([INK, INK]);
    expect(new Set(line.slice(1, -1))).toEqual(new Set([SHADE]));
    expect(line.length).toBeGreaterThanOrEqual(8);
  });

  test("test_no_other_frame_of_a_town_is_changed_by_what_marks_a_blank", () => {
    // The least of every part is drawn, and is no blank: a tree, a roof. Each is as it was.
    const tree = drawnOf(frameOf({ drawing: "town-trees", frame: 1 }, from));
    const roof = drawnOf(frameOf({ drawing: "town-roofs", frame: 1 }, from));

    expect(tree.length).toBeGreaterThan(30);
    expect(roof.length).toBeGreaterThan(30);
    expect(tree.some((pixel) => pixel.colour === colour("--hedge"))).toBe(true);
    expect(roof.some((pixel) => pixel.colour === colour("--slate"))).toBe(true);
  });
});
