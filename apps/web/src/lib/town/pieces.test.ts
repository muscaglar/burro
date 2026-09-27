/** @jest-environment node */
/**
 * What is seen of a town: the rule, the drawings and where each piece is laid, held to each
 * other. The picture is put together here as a browser puts it together, from the text of
 * the drawings, and what the rule says is there is counted in it.
 */

import type { BandNumber } from "@/content/bands";
import { ART, type ArtName } from "@/lib/art/names";
import { VIBE_BANDS } from "@/lib/vibes";

import { themes } from "../../../test/support/contrast";
import { NOTHING_KNOWN, type Bands } from "./bands";
import { count, drawings, frameOf, laid, pictureOf } from "./picture";
import { CANVAS, framesIn, frameWidth, piecesOf, type Piece } from "./pieces";
import { planOf, WINDOWS, type Form } from "./plan";

const { light } = themes();
const colour = (token: string) => (light[token] ?? "").toLowerCase();
const AMBER = colour("--amber");
const INK = colour("--ink");
const SHADE = colour("--shade");
const SLATE = colour("--slate");
const POPPY = colour("--poppy");
const HEDGE = colour("--hedge");
const MEADOW = colour("--meadow");
const VERGE = colour("--verge");

/** A window is two art pixels by two. */
const WINDOW = 4;

const EVERY: readonly (BandNumber | null)[] = [null, ...VIBE_BANDS];
const TOWNS: readonly Bands[] = EVERY.flatMap((trees) =>
  EVERY.flatMap((height) => EVERY.flatMap((lit) => EVERY.map((roofs) => ({ trees, height, lit, roofs })))),
);
const MOST: Bands = { trees: 5, height: 5, lit: 5, roofs: 5 };
const LEAST: Bands = { trees: 1, height: 1, lit: 1, roofs: 1 };

const from = drawings();
const townOf = (bands: Bands) => piecesOf(planOf(bands));
const seen = (bands: Bands) => pictureOf(townOf(bands), from);
const named = (pieces: readonly Piece[], name: RegExp) => pieces.filter(({ drawing }) => name.test(drawing));
const WALLS: readonly [Form, ArtName][] = [
  ["low", "town-low"],
  ["mid", "town-mid"],
  ["tall", "town-tall"],
];

describe("where the pieces of a town are laid", () => {
  test("test_the_canvas_is_of_one_size_for_every_town_and_is_about_56_art_pixels_by_32", () => {
    expect(CANVAS).toEqual({ width: 56, height: 32 });
    for (const bands of TOWNS) expect(seen(bands).map((row) => row.length)).toEqual(Array.from({ length: 32 }, () => 56));
  });

  test("test_everything_that_is_drawn_of_every_town_lies_on_the_canvas_and_nothing_is_cut_off", () => {
    // A frame may stand a clear column past the edge of the canvas. What is drawn in it may not.
    const off = TOWNS.flatMap((bands) =>
      townOf(bands).flatMap((piece) =>
        laid(piece, from).filter(({ x, y }) => x < 0 || y < 0 || x >= CANVAS.width || y >= CANVAS.height),
      ),
    );

    expect(off).toEqual([]);
  });

  test("test_nothing_that_stands_on_the_plot_is_drawn_over_its_edge", () => {
    // The plot is a sod with an edge of ink. What is built stands in front of its far
    // edge, which is the first of its rows. Its sides and its foot are never drawn over.
    const plot = frameOf({ drawing: "town-plot", frame: 0 }, from);
    const first = plot.findIndex((row) => row.some((pixel) => pixel !== null));
    const edge = plot.flatMap((row, y) => row.flatMap((pixel, x) => (pixel === INK && y > first + 1 ? [{ x, y }] : [])));

    expect(edge.length).toBeGreaterThan(60);
    for (const bands of TOWNS) {
      const picture = seen(bands);
      expect([bands, edge.filter(({ x, y }) => picture[y]?.[x] !== INK)]).toEqual([bands, []]);
    }
  });

  test("test_a_frame_of_a_strip_has_a_clear_column_at_either_hand", () => {
    // Shown through a window of its own size, a frame must show nothing of the frame beside
    // it, where a screen sets a pixel of the drawing over a part of one of its own.
    const strips = (Object.keys(ART) as ArtName[]).filter((name) => name.startsWith("town-") && framesIn(name) > 1);

    expect(strips.length).toBeGreaterThanOrEqual(5);
    for (const strip of strips) {
      for (let frame = 0; frame < framesIn(strip); frame += 1) {
        const rows = frameOf({ drawing: strip, frame }, from);
        expect([strip, frame, rows.filter((row) => row[0] !== null || row.at(-1) !== null)]).toEqual([strip, frame, []]);
      }
    }
  });

  test("test_every_piece_is_a_frame_that_its_drawing_holds", () => {
    const beyond = TOWNS.flatMap((bands) => townOf(bands).filter(({ drawing, frame }) => frame < 0 || frame >= framesIn(drawing)));

    expect(beyond).toEqual([]);
  });

  test("test_two_towns_of_the_same_four_bands_are_the_same_picture_pixel_for_pixel", () => {
    for (const bands of [LEAST, MOST, NOTHING_KNOWN]) expect(seen({ ...bands })).toEqual(seen(bands));
  });

  test("test_towns_that_are_planned_apart_are_pictures_that_differ", () => {
    const pictures = new Set(TOWNS.map((bands) => JSON.stringify(seen(bands))));
    const plans = new Set(TOWNS.map((bands) => JSON.stringify(planOf(bands))));

    expect(pictures.size).toBe(plans.size);
  });
});

describe("what is seen of a town", () => {
  test("test_every_window_the_rule_lights_is_lit_in_the_picture_and_no_other_and_none_is_hidden", () => {
    // Amber is the colour of a lit window, and of nothing else in a town. A tree that stood
    // over a window would hide it, and fewer would be counted here than the rule lit.
    for (const bands of TOWNS) {
      const lit = (planOf(bands).buildings ?? []).reduce((sum, building) => sum + (building.lit ?? 0), 0);
      expect([bands, count(seen(bands), AMBER)]).toEqual([bands, lit * WINDOW]);
    }
  });

  test("test_no_tree_stands_over_a_window_lit_or_dark", () => {
    for (const bands of [MOST, LEAST, { ...MOST, height: 1 as const }, { ...MOST, lit: 1 as const }]) {
      const pieces = townOf(bands);
      // Where the windows of a wall are: where its last frame, with all of them lit, is amber.
      const windows = named(pieces, /^town-(low|mid|tall)$/).flatMap((wall) =>
        laid({ ...wall, frame: framesIn(wall.drawing) - 1 }, from).filter((pixel) => pixel.colour === AMBER),
      );
      const trees = named(pieces, /^town-trees$/).flatMap((tree) => laid(tree, from));
      const hidden = windows.filter((window) => trees.some((tree) => tree.x === window.x && tree.y === window.y));

      expect(windows.length).toBeGreaterThan(0);
      expect(trees.length).toBeGreaterThan(0);
      expect(hidden).toEqual([]);
    }
  });

  test.each(VIBE_BANDS)("test_as_many_trees_stand_in_front_as_the_rule_says: band %i", (band) => {
    const trees = named(townOf({ ...MOST, trees: band }), /^town-trees$/);

    expect(trees).toHaveLength(band);
    // Each is a tree, and none is the ring that marks where one would stand.
    expect(trees.filter(({ frame }) => frame === 0)).toEqual([]);
    // And each stands in a place of its own.
    expect(new Set(trees.map(({ left }) => left)).size).toBe(band);
  });

  test("test_the_trees_of_a_band_stand_where_they_stood_in_the_band_before_with_one_more", () => {
    for (const band of VIBE_BANDS.slice(1)) {
      const places = (of: BandNumber) => named(townOf({ ...MOST, trees: of }), /^town-trees$/).map(({ left, frame }) => `${left} ${frame}`);
      const before = places((band - 1) as BandNumber);

      expect(places(band).filter((place) => before.includes(place))).toEqual(before);
    }
  });

  test("test_a_roof_stands_on_its_wall_and_a_wall_on_the_ground", () => {
    for (const bands of [MOST, LEAST, { ...MOST, height: 3 as const, roofs: null }]) {
      const pieces = townOf(bands);
      const walls = named(pieces, /^town-(low|mid|tall)$/);
      const roofs = named(pieces, /^town-roofs$/);

      expect(walls).toHaveLength(4);
      expect(roofs).toHaveLength(4);
      walls.forEach((wall, lot) => {
        // The line every wall stands on is one row, whatever its height.
        expect(wall.top + ART[wall.drawing].height).toBe((walls[0]?.top ?? 0) + ART[walls[0]?.drawing ?? "town-low"].height);
        // The roof ends on the row over the wall, and stands one art pixel past it at either hand.
        expect(roofs[lot]?.top).toBe(wall.top - ART["town-roofs"].height);
        expect(roofs[lot]?.left).toBe(wall.left - 1);
      });
    }
  });
});

describe("what is left blank", () => {
  test("test_a_town_of_which_nothing_is_known_is_a_bare_plot_with_its_marks_and_nothing_built_or_grown", () => {
    const picture = seen(NOTHING_KNOWN);
    const colours = new Set(picture.flat().filter((pixel) => pixel !== null));
    const plot = new Set(frameOf({ drawing: "town-plot", frame: 0 }, from).flat().filter((pixel) => pixel !== null));

    // The plot, and the dots that mark what is not drawn, which are in shade.
    expect([...colours].filter((one) => !plot.has(one))).toEqual([SHADE]);
    for (const built of [AMBER, SLATE, POPPY]) expect(count(picture, built)).toBe(0);
    expect(named(townOf(NOTHING_KNOWN), /^town-(low|mid|tall|roofs)$/)).toEqual([]);
    expect(named(townOf(NOTHING_KNOWN), /^town-lot$/)).toHaveLength(4);
    expect(named(townOf(NOTHING_KNOWN), /^town-trees$/).map(({ frame }) => frame)).toEqual([0]);
  });

  test("test_what_marks_a_blank_is_drawn_in_shade_alone_and_is_one_line_with_no_pixel_apart_from_the_rest", () => {
    // Each was drawn in dots, no two of which touched, and a person who walked the website
    // did not know what an edge in pieces was for. The test beside the part that draws a
    // town holds the shape of each line.
    const marks: Piece[] = [
      { drawing: "town-lot", frame: 0, left: 0, top: 0 },
      { drawing: "town-trees", frame: 0, left: 0, top: 0 },
    ];
    for (const mark of marks) {
      const line = laid(mark, from);
      const beside = (one: (typeof line)[number]) =>
        line.filter((other) => other !== one && Math.abs(other.x - one.x) <= 1 && Math.abs(other.y - one.y) <= 1);

      expect(line.length).toBeGreaterThanOrEqual(8);
      // It is in the colour of no building and of nothing that grows: it is taken for neither.
      expect(line.every((pixel) => pixel.colour === SHADE)).toBe(true);
      expect(line.filter((pixel) => beside(pixel).length < 2)).toEqual([]);
    }
  });

  test("test_the_least_of_every_part_is_drawn_and_is_no_blank", () => {
    // One tree, four houses, one window lit, and every roof newer: each is something.
    const least = seen(LEAST);
    const blank = seen(NOTHING_KNOWN);

    expect(count(least, HEDGE)).toBeGreaterThan(count(blank, HEDGE));
    expect(count(least, AMBER)).toBe(WINDOW);
    expect(count(least, SLATE)).toBeGreaterThan(0);
    expect(named(townOf(LEAST), /^town-low$/)).toHaveLength(4);
  });

  test("test_where_roofs_are_not_known_no_roof_is_drawn_and_the_wall_is_closed_by_one_whole_line", () => {
    const picture = seen({ ...MOST, roofs: null });
    const bare = frameOf({ drawing: "town-roofs", frame: 0 }, from);
    const drawn = bare.filter((row) => row.some((pixel) => pixel !== null));

    expect(count(picture, POPPY)).toBe(0);
    expect(count(picture, SLATE)).toBe(count(seen({ ...MOST, roofs: null, height: 5 }), SLATE));
    // One row, the last: shade between the corners of the wall, which are ink. It is in the
    // colour of no roof, and no pixel of it is the page showing through.
    expect(bare.indexOf(drawn[0] ?? [])).toBe(bare.length - 1);
    expect(drawn).toHaveLength(1);
    expect(new Set(drawn[0]?.filter((pixel) => pixel !== null))).toEqual(new Set([INK, SHADE]));
  });

  test("test_where_lit_windows_are_not_known_every_window_is_dark_and_none_is_lit", () => {
    expect(count(seen({ ...MOST, lit: null }), AMBER)).toBe(0);
    for (const [, wall] of WALLS) {
      const dark = frameOf({ drawing: wall, frame: 0 }, from);
      const unlit = frameOf({ drawing: wall, frame: 1 }, from);
      const lit = frameOf({ drawing: wall, frame: framesIn(wall) - 1 }, from);

      // Where a window is lit in the last frame, it is ink in the first, and shade in the second.
      lit.forEach((row, y) =>
        row.forEach((pixel, x) => {
          if (pixel !== AMBER) return;
          expect([wall, x, y, dark[y]?.[x], unlit[y]?.[x]]).toEqual([wall, x, y, INK, SHADE]);
        }),
      );
    }
  });
});

describe("the drawings of a town", () => {
  test.each(WALLS)("test_a_wall_has_a_frame_for_every_count_of_its_windows_that_may_be_lit: %s", (form, wall) => {
    // The first frame is the wall with dark windows. Then none lit, one, and so on to all.
    expect(framesIn(wall)).toBe(WINDOWS[form] + 2);
    for (let lit = 0; lit <= WINDOWS[form]; lit += 1) {
      expect([wall, lit, count(frameOf({ drawing: wall, frame: lit + 1 }, from), AMBER)]).toEqual([wall, lit, lit * WINDOW]);
    }
    expect(count(frameOf({ drawing: wall, frame: 0 }, from), AMBER)).toBe(0);
  });

  test.each(WALLS)("test_a_window_that_is_lit_stays_lit_as_more_are_and_nothing_else_of_the_wall_changes: %s", (form, wall) => {
    for (let lit = 1; lit <= WINDOWS[form]; lit += 1) {
      const before = frameOf({ drawing: wall, frame: lit }, from);
      const after = frameOf({ drawing: wall, frame: lit + 1 }, from);
      const changed = after.flatMap((row, y) => row.flatMap((pixel, x) => (pixel === before[y]?.[x] ? [] : [[before[y]?.[x], pixel]])));

      // One window more, which was shade and is amber.
      expect(changed).toEqual(Array.from({ length: WINDOW }, () => [SHADE, AMBER]));
    }
  });

  test("test_a_taller_wall_is_the_lower_wall_with_floors_more_so_that_height_is_all_that_differs", () => {
    const tops = WALLS.map(([, wall]) => ART[wall].height);

    expect(tops).toEqual([...tops].sort((one, other) => one - other));
    expect(new Set(tops).size).toBe(3);
    expect(new Set(WALLS.map(([, wall]) => frameWidth(wall))).size).toBe(1);
  });

  test("test_a_roof_is_none_or_newer_in_slate_or_older_in_poppy_and_there_are_two_of_a_kind", () => {
    const roofs = Array.from({ length: framesIn("town-roofs") }, (_, frame) => frameOf({ drawing: "town-roofs", frame }, from));
    const kindOf = (roof: (typeof roofs)[number]) =>
      count(roof, SLATE) > 0 && count(roof, POPPY) === 0 ? "newer" : count(roof, POPPY) > 0 && count(roof, SLATE) === 0 ? "older" : "none";

    expect(roofs.map(kindOf)).toEqual(["none", "newer", "newer", "older", "older"]);
    expect(new Set(roofs.map((roof) => JSON.stringify(roof))).size).toBe(5);
  });

  test("test_which_of_two_roofs_a_building_has_is_by_where_it_stands_and_by_nothing_of_the_area", () => {
    const newer = (bands: Bands) => named(townOf(bands), /^town-roofs$/).map(({ frame }) => frame);

    // Every roof newer: the two of the kind by turns, from the left. And so for the older.
    expect(newer({ ...MOST, roofs: 1 })).toEqual([1, 2, 1, 2]);
    expect(newer({ ...MOST, roofs: 5 })).toEqual([3, 4, 3, 4]);
    // Whatever else is known of the area, a roof of a kind in a place is one drawing.
    for (const bands of TOWNS.filter(({ height, roofs }) => height !== null && roofs === 5)) expect(newer(bands)).toEqual([3, 4, 3, 4]);
  });

  test("test_the_plot_is_meadow_and_holds_nothing_that_stands_for_a_measure", () => {
    const plot = frameOf({ drawing: "town-plot", frame: 0 }, from);
    const colours = new Set(plot.flat().filter((pixel) => pixel !== null));

    expect(colours).toEqual(new Set([INK, MEADOW, VERGE, HEDGE]));
    // It lies in the lower part of the canvas: what is built stands up from it into the clear.
    expect(plot.slice(0, 16).flat().filter((pixel) => pixel !== null)).toEqual([]);
  });
});
