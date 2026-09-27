/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { validateStyleMin } from "@maplibre/maplibre-gl-style-spec";

import { recordedAnswer } from "@/lib/api/recorded";

import { contrast, themes } from "../../../test/support/contrast";
import { bandOf, BANDS, fillFor, fitOf, idsBy, type Band } from "./fill";
import { boundsOf, pathOf, projector, ringsOf } from "./project";
import {
  addPatterns,
  buildStyle,
  DRAWN,
  FAR,
  fillColour,
  FINENESS,
  GRAIN_IMAGE,
  grainColour,
  grainFilter,
  grainOf,
  IMAGES,
  imagesOf,
  landPixels,
  LAYER,
  NEAR,
  OUTLINE,
  PATTERN_IMAGE,
  patternFilter,
  patternPixels,
  PIXEL_TOKEN,
  ratioFor,
  SOURCE,
  THEME_TOKENS,
  themeFrom,
  waterPixels,
  zoomOf,
  type PatternPixels,
} from "./style";

const geometry = recordedAnswer("get_geometry", "geometry").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data;
const refined = recordedAnswer("rank", "rank-refined").body.data;
const nothing = recordedAnswer("rank", "rank-nothing-matches").body.data;

const { light, dark } = themes();
const LIGHT = themeFrom((token) => light[token]);
const DARK = themeFrom((token) => dark[token]);

/** A drawing of the website, as its text has it: a character a pixel. */
function drawingOf(file: string, name: string): string[] {
  const lines = readFileSync(path.resolve(__dirname, "../../../art", file), "utf8").split("\n");
  const from = lines.findIndex((line) => line.startsWith("==") && line.slice(2).trim() === name);
  if (from < 0) throw new Error(`${file} holds no drawing named ${name}`);
  const until = lines.findIndex((line, at) => at > from && line.startsWith("=="));
  return lines.slice(from + 1, until < 0 ? undefined : until).filter((line) => line.trim() !== "" && !line.startsWith("#"));
}

/** What a drawing has on its ground: every pixel that is not of the colour most of it is. */
function grainOfDrawing(rows: readonly string[]): string[] {
  const counted = new Map<string, number>();
  for (const pixel of rows.join("")) counted.set(pixel, (counted.get(pixel) ?? 0) + 1);
  const [ground] = [...counted].sort((one, other) => other[1] - one[1])[0] ?? [""];
  return rows.map((row) => [...row].map((pixel) => (pixel === ground ? "." : "x")).join(""));
}

/** The pixels of a picture, each as its four parts. */
const pixelsOf = ({ data }: PatternPixels) =>
  Array.from({ length: data.length / 4 }, (_, at) => [...data.slice(at * 4, at * 4 + 4)].join(","));
const partsOf = (colour: string) => [1, 3, 5].map((at) => parseInt(colour.slice(at, at + 2), 16)).join(",");

describe("what the map shows of each area", () => {
  test("test_every_area_of_the_release_is_filled_once", () => {
    for (const ranking of [first, refined, nothing]) {
      const fills = fillFor(ranking.scores, ranking.filtered, ranking.unranked);

      expect([...fills.keys()].sort()).toEqual(areas.map((area) => area.area_id).sort());
    }
  });

  test("test_a_ranked_area_takes_the_band_of_its_fit_and_no_pattern", () => {
    const fills = fillFor(first.scores, first.filtered, first.unranked);

    for (const { area_id: areaId, score } of first.scores) {
      expect(fills.get(areaId)).toEqual({ band: bandOf(score), pattern: "none" });
    }
    // Recorded: a fit of 71.38 is in the fourth band, and one of 51.66 is in the band below it.
    expect(fills.get("syn-n0006")).toEqual({ band: 4, pattern: "none" });
    expect(fills.get("syn-n0014")).toEqual({ band: 3, pattern: "none" });
  });

  test("test_an_area_with_no_rank_is_told_apart_by_a_pattern_and_not_by_a_colour", () => {
    const fills = fillFor(refined.scores, refined.filtered, refined.unranked);

    for (const { area_id: areaId } of refined.filtered) {
      expect(fills.get(areaId)).toEqual({ band: 0, pattern: "filtered" });
    }
    for (const { area_id: areaId } of refined.unranked) {
      expect(fills.get(areaId)).toEqual({ band: 0, pattern: "unranked" });
    }
    expect(idsBy(fills).patterns.filtered).toHaveLength(refined.filtered.length);
  });

  test("test_with_nothing_to_rank_by_no_area_is_given_a_band", () => {
    const empty = recordedAnswer("rank", "rank-empty-spec").body.data;

    const fills = fillFor(empty.scores, empty.filtered, empty.unranked, empty.empty_spec);

    expect(idsBy(fills).bands[0]).toHaveLength(areas.length);
  });

  test("test_the_bands_cover_every_fit_from_0_to_100_once", () => {
    for (let fit = 0; fit <= 100; fit += 1) {
      expect(BANDS.filter(({ from, to }) => fit >= from && fit <= to)).toHaveLength(1);
    }
    expect([0, 19.99, 20, 59.9, 60, 79.99, 80, 100].map(bandOf)).toEqual([1, 1, 2, 3, 4, 4, 5, 5]);
  });

  test("test_a_fit_is_rounded_down_so_it_is_never_said_to_be_more_than_it_is", () => {
    expect([78.78, 79.99, 0.4, 100, 54.81].map(fitOf)).toEqual([78, 79, 0, 100, 54]);
    // The figure shown always falls in the band the legend gives for it.
    for (const { score } of first.scores) {
      const { from, to } = BANDS[bandOf(score) - 1] ?? { from: -1, to: -1 };
      expect(fitOf(score)).toBeGreaterThanOrEqual(from);
      expect(fitOf(score)).toBeLessThanOrEqual(to);
    }
  });
});

describe("the style of the map", () => {
  const fills = fillFor(refined.scores, refined.filtered, refined.unranked);

  test.each([
    ["light", LIGHT],
    ["dark", DARK],
  ])("test_the_style_is_one_the_map_library_accepts: %s", (_, theme) => {
    expect(validateStyleMin(buildStyle(theme))).toEqual([]);
    expect(validateStyleMin(buildStyle(theme, geometry))).toEqual([]);
    expect(validateStyleMin(buildStyle(theme, geometry, fills))).toEqual([]);
  });

  test("test_the_check_these_tests_rely_on_catches_a_style_that_is_wrong", () => {
    const style = buildStyle(LIGHT, geometry, fills);
    const broken = { ...style, layers: [...style.layers, { id: "x", type: "fill", source: "nowhere" }] };

    expect(validateStyleMin(broken as never).length).toBeGreaterThan(0);
  });

  test("test_the_style_asks_no_host_for_anything", () => {
    const written = JSON.stringify(buildStyle(LIGHT, geometry, fills));

    expect(written).not.toMatch(/https?:|\/\/|mapbox:|glyphs|sprite|tiles|"url"/);
    expect(Object.keys(buildStyle(LIGHT).sources)).toEqual([SOURCE]);
  });

  test("test_the_map_draws_no_text", () => {
    const style = buildStyle(LIGHT, geometry, fills);

    // Water, the areas filled, their grain, the two patterns, and the outlines.
    expect(style.layers.map((layer) => [layer.id, layer.type])).toEqual([
      [LAYER.water, "background"],
      [LAYER.fill, "fill"],
      [LAYER.grain, "fill"],
      [LAYER.filtered, "fill"],
      [LAYER.unranked, "fill"],
      [LAYER.outline, "line"],
    ]);
    expect(style.layers.some((layer) => layer.type === "symbol")).toBe(false);
  });

  test("test_the_background_stands_for_water_and_an_area_with_no_fit_is_land", () => {
    const style = buildStyle(LIGHT, geometry);

    expect(style.layers[0]).toMatchObject({ paint: { "background-color": light["--map-water"] } });
    expect(style.layers[1]).toMatchObject({ paint: { "fill-color": light["--map-land"] } });
  });

  test("test_the_water_and_the_land_each_bear_the_grain_of_their_tile", () => {
    const style = buildStyle(LIGHT, geometry);

    expect(style.layers[0]).toMatchObject({ paint: { "background-pattern": GRAIN_IMAGE.water } });
    // Before a search every area is land with no fit, and bears the grain of such land.
    expect(style.layers[2]).toMatchObject({ id: LAYER.grain, paint: { "fill-pattern": GRAIN_IMAGE.land[0] } });
    // Every image the style names is one the map is handed, and the map is handed no other.
    expect([...imagesOf(LIGHT).keys()].sort()).toEqual([...IMAGES].sort());
    expect(new Set(IMAGES).size).toBe(IMAGES.length);
    const named = JSON.stringify(style.layers.map((layer) => layer.paint)).match(/"(?:fill|background)-pattern":"[^"]+"/g) ?? [];
    expect(named.map((found) => found.split(":")[1]?.replace(/"/g, "")).every((name) => IMAGES.includes(name ?? ""))).toBe(true);
  });

  test("test_each_area_bears_the_grain_of_its_band_and_an_area_with_a_pattern_bears_none", () => {
    const grain = grainOf(fills) as unknown as unknown[];
    const { bands, patterns } = idsBy(fills);

    expect(grain.slice(0, 2)).toEqual(["match", ["get", "area_id"]]);
    expect(grain[grain.length - 1]).toBe(GRAIN_IMAGE.land[0]);
    for (const band of [1, 2, 3, 4, 5] as const) {
      const at = grain.findIndex((part) => part === GRAIN_IMAGE.land[band]);
      if (bands[band].length === 0) expect(at).toBe(-1);
      else expect(grain[at - 1]).toEqual(bands[band]);
    }
    // Lines and dots each go with a reason given in words. Nothing is laid under them.
    expect(patterns.filtered.length + patterns.unranked.length).toBeGreaterThan(0);
    expect(grainFilter(fills)).toEqual([
      "!",
      ["in", ["get", "area_id"], ["literal", [...patterns.filtered, ...patterns.unranked]]],
    ]);
    expect(buildStyle(LIGHT, geometry, fills).layers.find((layer) => layer.id === LAYER.grain)).toMatchObject({
      filter: grainFilter(fills),
      paint: { "fill-pattern": grain },
    });
  });

  test("test_each_area_is_coloured_by_the_band_of_its_fit", () => {
    const colour = fillColour(fills, LIGHT) as unknown as unknown[];

    expect(colour.slice(0, 2)).toEqual(["match", ["get", "area_id"]]);
    expect(colour[colour.length - 1]).toBe(light["--map-land"]);
    const { bands } = idsBy(fills);
    for (const band of [1, 2, 3, 4, 5] as const) {
      const at = colour.findIndex((part) => part === light[`--map-${band}`]);
      if (bands[band].length === 0) expect(at).toBe(-1);
      else expect(colour[at - 1]).toEqual(bands[band]);
    }
  });

  test("test_the_patterns_are_drawn_on_the_areas_with_no_rank", () => {
    expect(patternFilter(fills, "filtered")).toEqual([
      "in",
      ["get", "area_id"],
      ["literal", refined.filtered.map((area) => area.area_id)],
    ]);
    expect(patternFilter(fills, "unranked")).toEqual([
      "in",
      ["get", "area_id"],
      ["literal", refined.unranked.map((area) => area.area_id)],
    ]);
    const style = buildStyle(LIGHT, geometry, fills);
    expect(style.layers.find((layer) => layer.id === LAYER.filtered)).toMatchObject({
      paint: { "fill-pattern": PATTERN_IMAGE.filtered },
    });
  });

  test("test_the_outline_is_wider_on_the_area_under_the_pointer_and_widest_on_the_one_chosen", () => {
    const outline = buildStyle(LIGHT).layers.find((layer) => layer.id === LAYER.outline);

    const width = (plain: number) => [
      "case",
      ["boolean", ["feature-state", "selected"], false],
      3,
      ["boolean", ["feature-state", "hovered"], false],
      2,
      plain,
    ];
    expect(outline).toMatchObject({
      paint: {
        "line-color": light["--map-line"],
        "line-width": ["interpolate", ["linear"], ["zoom"], FAR.zoom, width(FAR.width), NEAR.zoom, width(1)],
      },
    });
  });

  test("test_seen_from_far_off_an_outline_is_thin_so_that_the_colour_of_a_small_area_shows", () => {
    // Seen in a browser, on a map of a thousand areas: at the width of the city the outlines
    // of the small areas in the middle met, and hid the colour that says how well each fits.
    expect(FAR.zoom).toBeLessThan(NEAR.zoom);
    expect(FAR.width).toBeLessThanOrEqual(0.4);
    expect(FAR.width).toBeGreaterThan(0);
    expect(OUTLINE.plain).toBe(1);
  });

  test("test_each_feature_is_known_to_the_map_by_its_area_id", () => {
    expect(buildStyle(LIGHT, geometry).sources[SOURCE]).toMatchObject({
      type: "geojson",
      promoteId: "area_id",
    });
    expect(geometry.features.every((feature) => feature.properties.area_id === feature.id)).toBe(true);
  });

  test("test_every_colour_of_the_map_is_a_design_token", () => {
    const tokens = [THEME_TOKENS.water, THEME_TOKENS.glint, THEME_TOKENS.land, THEME_TOKENS.line, ...THEME_TOKENS.bands];

    for (const token of tokens) {
      expect(light[token]).toMatch(/^#[0-9a-f]{6}$/);
      expect(dark[token]).toMatch(/^#[0-9a-f]{6}$/);
    }
    // The look is one: the map is drawn in the same colours whatever the system asks.
    expect(DARK).toEqual(LIGHT);
    // With no style sheet to read, the map is still drawn, and in the colours of the look:
    // what it falls back on is what the tokens give, colour for colour, and no grey.
    expect(themeFrom(() => undefined)).toEqual(LIGHT);
    expect(themeFrom(() => "  ")).toEqual(LIGHT);
    expect(validateStyleMin(buildStyle(themeFrom(() => undefined), geometry, fills))).toEqual([]);
  });

  test("test_a_pixel_of_the_grain_is_as_large_as_a_pixel_of_the_meadow_the_page_stands_on", () => {
    expect(PIXEL_TOKEN).toBe("--px-ground");
    expect(light[PIXEL_TOKEN]).toBe("2px");
  });

  test("test_a_basemap_goes_under_the_areas_and_over_the_water", () => {
    const style = buildStyle(LIGHT, geometry, fills, {
      sources: { base: { type: "geojson", data: { type: "FeatureCollection", features: [] } } },
      layers: [{ id: "base-fill", type: "fill", source: "base" }],
    });

    expect(style.layers.map((layer) => layer.id).slice(0, 3)).toEqual([
      LAYER.water,
      "base-fill",
      LAYER.fill,
    ]);
    expect(validateStyleMin(style)).toEqual([]);
  });

  test("test_no_other_file_holds_a_colour_a_layer_or_a_source_of_the_map", () => {
    const src = path.resolve(__dirname, "..", "..");
    const holding: string[] = [];
    const walk = (folder: string) => {
      for (const entry of readdirSync(folder, { withFileTypes: true })) {
        const file = path.join(folder, entry.name);
        if (entry.isDirectory()) walk(file);
        else if (/\.tsx?$/.test(entry.name) && !/\.test\.tsx?$/.test(entry.name)) {
          if (file.endsWith(path.join("lib", "map", "style.ts"))) continue;
          const text = readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\/|\/\/.*$/gm, "");
          if (/addLayer\(|addSource\(|"(fill|line|background)-(color|pattern|width)"|#[0-9a-f]{6}\b/i.test(text)) {
            holding.push(path.relative(src, file));
          }
        }
      }
    };
    walk(src);

    expect(holding).toEqual([]);
  });
});

describe("the patterns", () => {
  test("test_a_pattern_is_worked_out_here_and_not_loaded", () => {
    for (const pattern of ["filtered", "unranked"] as const) {
      const { width, height, data } = patternPixels(pattern, light["--map-line"] ?? "");
      const size = DRAWN[pattern].length * FINENESS;

      expect([width, height]).toEqual([size, size]);
      expect(data).toHaveLength(size * size * 4);
    }
    // A tile is square, whatever is drawn on it.
    for (const rows of Object.values(DRAWN)) expect(rows.map((row) => row.length)).toEqual(rows.map(() => rows.length));
  });

  test("test_a_pattern_is_in_the_colour_of_the_outline_and_clear_between", () => {
    const pixels = pixelsOf(patternPixels("filtered", "#1b1f23")).map((pixel) => pixel.split(",").map(Number));
    const inked = pixels.filter(([, , , alpha]) => alpha === 255);

    expect(inked.length).toBeGreaterThan(0);
    expect(inked.length).toBeLessThan(pixels.length / 2);
    expect(new Set(inked.map((pixel) => pixel.join(",")))).toEqual(new Set(["27,31,35,255"]));
    expect(pixels.filter(([, , , alpha]) => alpha === 0)).toHaveLength(pixels.length - inked.length);
  });

  test("test_lines_and_dots_are_not_the_same_picture", () => {
    const lines = patternPixels("filtered", "#000000");
    const dots = patternPixels("unranked", "#000000");

    expect([...lines.data]).not.toEqual([...dots.data]);
    // Lines run from edge to edge, so a tile joins the next. Dots touch no edge.
    const alphaAt = ({ width, data }: PatternPixels, x: number, y: number) => data[(y * width + x) * 4 + 3];
    const edgeOf = ({ width }: PatternPixels) => [...Array(width).keys()];
    expect(edgeOf(lines).some((at) => alphaAt(lines, at, 0) === 255)).toBe(true);
    expect(edgeOf(dots).every((at) => alphaAt(dots, at, 0) === 0 && alphaAt(dots, 0, at) === 0)).toBe(true);
    // A line runs up to the right, a pixel at a time, and joins itself at the edge of its tile.
    const size = DRAWN.filtered.length;
    expect(DRAWN.filtered.map((row) => row.indexOf("x"))).toEqual(
      Array.from({ length: size }, (_, y) => (size - y) % size),
    );
    expect(DRAWN.filtered.every((row) => row.replace(/\./g, "") === "x")).toBe(true);
  });

  test("test_a_pattern_is_near_enough_to_itself_that_a_small_area_bears_some_of_it", () => {
    // A release of a whole city has about a thousand areas, and from far off one is some
    // 15 pixels of the screen across. A pattern that is laid further apart than that would leave a small
    // area bare, and an area with no rank is told apart by its pattern. A line that runs
    // aslant crosses every area that is as far across as its tile is wide, less a third:
    // so lines may lie further apart than dots.
    const pixel = Number.parseFloat(light[PIXEL_TOKEN] ?? "");

    expect(DRAWN.filtered.length * pixel).toBeLessThanOrEqual(16);
    expect(DRAWN.unranked.length * pixel).toBeLessThanOrEqual(12);
    // Two dots to a tile, which stand corner to corner and never side by side.
    const dots = DRAWN.unranked.flatMap((row, y) => [...row].flatMap((pixel, x) => (pixel === "x" ? [[x, y] as const] : [])));
    expect(dots).toHaveLength(2);
    expect(dots.map(([x, y]) => x - y)).toEqual([0, 0]);
  });
});

describe("the grain of the land and of the water", () => {
  test("test_the_grain_of_the_land_is_the_tufts_of_its_tile_point_for_point", () => {
    expect([...DRAWN.land]).toEqual(grainOfDrawing(drawingOf("tiles.sprite.txt", "tile-grass-a")));
    // Three tufts, of three pixels each.
    expect(DRAWN.land.join("").replace(/\./g, "")).toHaveLength(9);
  });

  test("test_the_grain_of_the_water_is_the_glints_of_its_tile_point_for_point", () => {
    expect([...DRAWN.water]).toEqual(grainOfDrawing(drawingOf("tiles.sprite.txt", "tile-water-1")));
    expect(DRAWN.water.join("").replace(/\./g, "")).toHaveLength(12);
  });

  test("test_nothing_of_a_grain_touches_the_edge_of_its_tile_so_that_a_tile_joins_the_next", () => {
    for (const rows of [DRAWN.land, DRAWN.water]) {
      const edge = [rows[0], rows[rows.length - 1], ...rows.map((row) => `${row[0]}${row[row.length - 1]}`)];

      expect(edge.join("").includes("x")).toBe(false);
    }
  });

  test("test_the_land_is_clear_between_its_tufts_so_that_the_colour_of_its_band_shows", () => {
    for (const band of [0, 1, 2, 3, 4, 5] as const satisfies readonly Band[]) {
      const pixels = pixelsOf(landPixels(band, LIGHT));
      const drawn = pixels.filter((pixel) => pixel !== "0,0,0,0");

      expect(new Set(drawn)).toEqual(new Set([`${partsOf(grainColour(band, LIGHT))},255`]));
      // Nine pixels of a drawing of 256: what is between them is the band itself.
      expect(drawn).toHaveLength(9 * FINENESS * FINENESS);
    }
  });

  test("test_the_water_is_its_own_blue_with_glints_of_the_second_blue_and_is_nowhere_clear", () => {
    const pixels = pixelsOf(waterPixels(LIGHT));

    expect(new Set(pixels)).toEqual(new Set([`${partsOf(LIGHT.water)},255`, `${partsOf(LIGHT.glint)},255`]));
    expect(pixels.filter((pixel) => pixel === `${partsOf(LIGHT.glint)},255`)).toHaveLength(12 * FINENESS * FINENESS);
    expect([light[THEME_TOKENS.water], light[THEME_TOKENS.glint]]).toEqual([light["--shallows"], light["--haven"]]);
    // Each is the map's by name: no file of the map names a colour of the look for its water.
    expect([THEME_TOKENS.water, THEME_TOKENS.glint]).toEqual(["--map-water", "--map-glint"]);
  });

  test("test_a_grain_is_faint_enough_that_a_name_and_a_border_read_on_it", () => {
    // A grain is told from its ground, and by less than one band is told from the band
    // two from it: it is never taken for a border, which is 3 to 1 on every band.
    const grounds = [LIGHT.land, ...LIGHT.bands];

    for (const band of [0, 1, 2, 3, 4, 5] as const satisfies readonly Band[]) {
      const faint = contrast(grainColour(band, LIGHT), grounds[band] ?? "");

      expect([band, faint >= 1.35, faint < 2]).toEqual([band, true, true]);
      // The border reads on the grain as it reads on the land.
      expect(contrast(LIGHT.line, grainColour(band, LIGHT))).toBeGreaterThanOrEqual(3);
    }
    const glint = contrast(LIGHT.glint, LIGHT.water);
    expect([glint >= 1.35, glint < 2]).toEqual([true, true]);
    expect(contrast(LIGHT.line, LIGHT.glint)).toBeGreaterThanOrEqual(3);
  });

  test("test_the_grain_of_a_band_is_the_colour_of_the_band_beside_it_and_never_its_own", () => {
    const grounds = [LIGHT.land, ...LIGHT.bands];

    for (const band of [0, 1, 2, 3, 4, 5] as const satisfies readonly Band[]) {
      expect(grainColour(band, LIGHT)).not.toBe(grounds[band]);
      expect(LIGHT.bands).toContain(grainColour(band, LIGHT));
    }
    // One band deeper, but for the deepest, which has none deeper and takes the one before it.
    expect([1, 2, 3, 4, 5].map((band) => LIGHT.bands.indexOf(grainColour(band as Band, LIGHT)) + 1)).toEqual([2, 3, 4, 5, 4]);
  });

  test("test_a_pixel_of_a_drawing_is_a_square_of_one_colour_with_a_hard_edge", () => {
    for (const [name, picture] of imagesOf(LIGHT)) {
      const size = picture.width / FINENESS;
      const mixed = Array.from({ length: size * size }, (_, at) => squareAt(picture, at % size, Math.floor(at / size))).filter(
        (square) => new Set(square).size !== 1,
      );

      expect([name, picture.width === picture.height, Number.isInteger(size), mixed.length]).toEqual([name, true, true, 0]);
    }
    expect(FINENESS).toBeGreaterThanOrEqual(4);
  });

  test("test_a_pixel_of_the_grain_is_of_one_size_on_the_screen_however_near_the_map_is_drawn", () => {
    // The map library draws a pattern at its own size where the zoom is a whole number,
    // and larger by the part that is over, up to twice. It is told how many pixels of the
    // picture make one of the screen, so that a pixel of the drawing comes out as it should.
    const onTheScreen = (zoom: number, pixel: number) => (FINENESS / ratioFor({ zoom, pixel })) * 2 ** (zoom - Math.floor(zoom));

    for (const zoom of [0, 8, 9.25, 10.5, 11.999, 12, 13.0001]) {
      expect(onTheScreen(zoom, 2)).toBeCloseTo(2, 6);
      expect(onTheScreen(zoom, 3)).toBeCloseTo(3, 6);
    }
    expect(ratioFor({ zoom: 10, pixel: 2 })).toBe(FINENESS / 2);
  });

  test("test_how_near_the_map_is_drawn_is_read_from_where_it_puts_two_places", () => {
    // At zoom 0 the whole world, 360 degrees, is 512 pixels wide, and twice that at each zoom after.
    const mapAt = (zoom: number) => ({ project: ([longitude]: [number, number]) => ({ x: (longitude * 512 * 2 ** zoom) / 360 + 40, y: 0 }) });

    for (const zoom of [0, 3, 9.5, 11.25, 14]) expect(zoomOf(mapAt(zoom))).toBeCloseTo(zoom, 6);
    expect(zoomOf({ project: () => ({ x: 0, y: 0 }) })).toBe(0);
  });

  test("test_the_map_is_handed_every_image_with_how_many_of_its_pixels_make_one_of_the_screen", () => {
    const held = new Map<string, { pixelRatio?: number } | undefined>();
    const map = {
      hasImage: (name: string) => held.has(name),
      addImage: (name: string, _: PatternPixels, options?: { pixelRatio?: number }) => held.set(name, options),
      removeImage: (name: string) => held.delete(name),
      setPaintProperty: () => undefined,
      setFilter: () => undefined,
      setFeatureState: () => undefined,
      project: ([longitude]: [number, number]) => ({ x: longitude, y: 0 }),
    };

    addPatterns(map, LIGHT, { zoom: 10.5, pixel: 2 });
    expect([...held.keys()].sort()).toEqual([...IMAGES].sort());
    expect([...held.values()].map((options) => options?.pixelRatio)).toEqual(IMAGES.map(() => ratioFor({ zoom: 10.5, pixel: 2 })));

    // One the map has is left as it is, unless it is to be drawn again.
    addPatterns(map, LIGHT, { zoom: 11, pixel: 2 });
    expect(new Set([...held.values()].map((options) => options?.pixelRatio))).toEqual(new Set([ratioFor({ zoom: 10.5, pixel: 2 })]));
    addPatterns(map, LIGHT, { zoom: 11, pixel: 2 }, true);
    expect(new Set([...held.values()].map((options) => options?.pixelRatio))).toEqual(new Set([FINENESS / 2]));
  });

  /** The pixels of a picture that stand for one pixel of its drawing. */
  function squareAt({ width, data }: PatternPixels, x: number, y: number): string[] {
    return Array.from({ length: FINENESS * FINENESS }, (_, at) => {
      const from = ((y * FINENESS + Math.floor(at / FINENESS)) * width + x * FINENESS + (at % FINENESS)) * 4;
      return [...data.slice(from, from + 4)].join(",");
    });
  }
});

describe("where things are", () => {
  test("test_the_bounds_hold_every_area", () => {
    const bounds = boundsOf(geometry);
    if (bounds === null) throw new Error("the recorded geometry holds nothing");
    const [[west, south], [east, north]] = bounds;

    for (const area of areas) {
      const [longitude, latitude] = area.centroid;
      expect(longitude).toBeGreaterThan(west);
      expect(longitude).toBeLessThan(east);
      expect(latitude).toBeGreaterThan(south);
      expect(latitude).toBeLessThan(north);
    }
    expect(boundsOf({ features: [] })).toBeNull();
  });

  test("test_everything_drawn_flat_falls_inside_its_frame_with_north_up", () => {
    const bounds = boundsOf(geometry);
    if (bounds === null) throw new Error("the recorded geometry holds nothing");
    const frame = { width: 120, height: 80, padding: 4 };
    const project = projector(bounds, frame);

    for (const feature of geometry.features) {
      for (const ring of ringsOf(feature.geometry)) {
        for (const position of ring) {
          const [x, y] = project(position);
          expect(x).toBeGreaterThanOrEqual(frame.padding - 0.001);
          expect(x).toBeLessThanOrEqual(frame.width - frame.padding + 0.001);
          expect(y).toBeGreaterThanOrEqual(frame.padding - 0.001);
          expect(y).toBeLessThanOrEqual(frame.height - frame.padding + 0.001);
        }
      }
    }
    const [[west, south], [, north]] = bounds;
    expect(project([west, north])[1]).toBeLessThan(project([west, south])[1]);
  });

  test("test_an_outline_is_a_closed_path_for_each_ring", () => {
    const bounds = boundsOf(geometry);
    const feature = geometry.features[0];
    if (bounds === null || !feature) throw new Error("the recorded geometry holds nothing");

    const drawn = pathOf(feature.geometry, projector(bounds, { width: 100, height: 100, padding: 0 }));

    expect(drawn).toMatch(/^M[\d. -]+(L[\d. -]+)+Z$/);
    expect(drawn.split("L")).toHaveLength(ringsOf(feature.geometry)[0]?.length ?? 0);
  });

  test("test_a_multipolygon_is_drawn_ring_by_ring", () => {
    const square = [
      [0, 0],
      [1, 0],
      [1, 1],
      [0, 0],
    ] as const;
    const two = { type: "MultiPolygon", coordinates: [[square], [square]] } as const;

    expect(ringsOf(two)).toHaveLength(2);
    expect(pathOf(two, ([x, y]) => [x, y]).match(/M/g)).toHaveLength(2);
  });
});
