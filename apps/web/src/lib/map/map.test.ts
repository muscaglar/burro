/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { validateStyleMin } from "@maplibre/maplibre-gl-style-spec";

import { recordedAnswer } from "@/lib/api/recorded";

import { themes } from "../../../test/support/contrast";
import { bandOf, BANDS, fillFor, fitOf, idsBy } from "./fill";
import { boundsOf, pathOf, projector, ringsOf } from "./project";
import {
  buildStyle,
  fillColour,
  LAYER,
  PATTERN_IMAGE,
  PATTERN_SIZE,
  patternFilter,
  patternPixels,
  SOURCE,
  THEME_TOKENS,
  themeFrom,
} from "./style";

const geometry = recordedAnswer("get_geometry", "geometry").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data;
const refined = recordedAnswer("rank", "rank-refined").body.data;
const nothing = recordedAnswer("rank", "rank-nothing-matches").body.data;

const { light, dark } = themes();
const LIGHT = themeFrom((token) => light[token]);
const DARK = themeFrom((token) => dark[token]);

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
    // Recorded: a fit of 80.99 is in the highest band, and one of 78.37 is in the band below it.
    expect(fills.get("syn-n0006")).toEqual({ band: 5, pattern: "none" });
    expect(fills.get("syn-n0003")).toEqual({ band: 4, pattern: "none" });
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

    expect(style.layers.map((layer) => layer.type)).toEqual([
      "background",
      "fill",
      "fill",
      "fill",
      "line",
    ]);
    expect(style.layers.some((layer) => layer.type === "symbol")).toBe(false);
  });

  test("test_the_background_stands_for_water_and_an_area_with_no_fit_is_land", () => {
    const style = buildStyle(LIGHT, geometry);

    expect(style.layers[0]).toMatchObject({ paint: { "background-color": light["--map-water"] } });
    expect(style.layers[1]).toMatchObject({ paint: { "fill-color": light["--map-land"] } });
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

    expect(outline).toMatchObject({
      paint: {
        "line-color": light["--map-line"],
        "line-width": [
          "case",
          ["boolean", ["feature-state", "selected"], false],
          3,
          ["boolean", ["feature-state", "hovered"], false],
          2,
          1,
        ],
      },
    });
  });

  test("test_each_feature_is_known_to_the_map_by_its_area_id", () => {
    expect(buildStyle(LIGHT, geometry).sources[SOURCE]).toMatchObject({
      type: "geojson",
      promoteId: "area_id",
    });
    expect(geometry.features.every((feature) => feature.properties.area_id === feature.id)).toBe(true);
  });

  test("test_every_colour_of_the_map_is_a_design_token", () => {
    const tokens = [THEME_TOKENS.water, THEME_TOKENS.land, THEME_TOKENS.line, ...THEME_TOKENS.bands];

    for (const token of tokens) {
      expect(light[token]).toMatch(/^#[0-9a-f]{6}$/);
      expect(dark[token]).toMatch(/^#[0-9a-f]{6}$/);
    }
    expect(LIGHT).not.toEqual(DARK);
    // With no style sheet to read, the map is still drawn, in greys.
    expect(validateStyleMin(buildStyle(themeFrom(() => undefined), geometry, fills))).toEqual([]);
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

      expect([width, height]).toEqual([PATTERN_SIZE, PATTERN_SIZE]);
      expect(data).toHaveLength(PATTERN_SIZE * PATTERN_SIZE * 4);
    }
  });

  test("test_a_pattern_is_in_the_colour_of_the_outline_and_clear_between", () => {
    const { data } = patternPixels("filtered", "#1b1f23");

    const pixels = Array.from({ length: PATTERN_SIZE * PATTERN_SIZE }, (_, at) => [
      ...data.slice(at * 4, at * 4 + 4),
    ]);
    const inked = pixels.filter(([, , , alpha]) => alpha === 255);

    expect(inked.length).toBeGreaterThan(0);
    expect(inked.length).toBeLessThan(pixels.length / 2);
    expect(new Set(inked.map((pixel) => pixel.join(",")))).toEqual(new Set(["27,31,35,255"]));
    expect(pixels.filter(([, , , alpha]) => alpha === 0)).toHaveLength(pixels.length - inked.length);
  });

  test("test_lines_and_dots_are_not_the_same_picture", () => {
    const lines = patternPixels("filtered", "#000000").data;
    const dots = patternPixels("unranked", "#000000").data;

    expect([...lines]).not.toEqual([...dots]);
    // Lines run from edge to edge, so a tile joins the next. Dots touch no edge.
    const alphaAt = (data: Uint8Array, x: number, y: number) => data[(y * PATTERN_SIZE + x) * 4 + 3];
    const edge = [...Array(PATTERN_SIZE).keys()];
    expect(edge.some((at) => alphaAt(lines, at, 0) === 255)).toBe(true);
    expect(edge.every((at) => alphaAt(dots, at, 0) === 0 && alphaAt(dots, 0, at) === 0)).toBe(true);
  });
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
