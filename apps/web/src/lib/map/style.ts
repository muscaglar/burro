/**
 * The style of the map. This is the only file that holds a colour, a layer
 * or a source of the map. A basemap is added here and nowhere else.
 *
 * There is no basemap yet: the areas are drawn from the API's own geometry
 * on a plain background, which stands for the water between them. The map
 * library draws no text, because a label needs glyph files from a host, so
 * the style names no glyphs and no sprite, and asks no host for anything.
 * Every name is in the page itself.
 *
 * Colours are the design tokens. They are read from the page when the map
 * starts, so that tokens.css stays the one place a colour is given.
 */

import type {
  FilterSpecification,
  GeoJSONSourceSpecification,
  LayerSpecification,
  SourceSpecification,
  StyleSpecification,
} from "maplibre-gl";

import type { GeometryData } from "@/lib/api/schema";

import { idsBy, type Band, type Fill, type Pattern } from "./fill";

export interface MapTheme {
  readonly water: string;
  readonly land: string;
  readonly line: string;
  /** The five bands of fit, low to high. */
  readonly bands: readonly [string, string, string, string, string];
}

/** The token each colour of the map comes from. */
export const THEME_TOKENS = {
  water: "--map-water",
  land: "--map-land",
  line: "--map-line",
  bands: ["--map-1", "--map-2", "--map-3", "--map-4", "--map-5"],
} as const;

/**
 * What is drawn if a token cannot be read, as where a style sheet failed to
 * load: greys, so that the outlines and the patterns still show. The figures
 * beside the map do not depend on them.
 */
const WITHOUT_TOKENS: MapTheme = {
  water: "#dddddd",
  land: "#f2f2f2",
  line: "#222222",
  bands: ["#eeeeee", "#dddddd", "#cccccc", "#bbbbbb", "#aaaaaa"],
};

/** The theme, from a function that reads a token's value. A test passes its own. */
export function themeFrom(read: (token: string) => string | undefined): MapTheme {
  const colour = (token: string, otherwise: string) => read(token)?.trim() || otherwise;
  const [one, two, three, four, five] = THEME_TOKENS.bands;
  const [a, b, c, d, e] = WITHOUT_TOKENS.bands;
  return {
    water: colour(THEME_TOKENS.water, WITHOUT_TOKENS.water),
    land: colour(THEME_TOKENS.land, WITHOUT_TOKENS.land),
    line: colour(THEME_TOKENS.line, WITHOUT_TOKENS.line),
    bands: [colour(one, a), colour(two, b), colour(three, c), colour(four, d), colour(five, e)],
  };
}

/** The theme as the page has it now, light or dark as the system asks. */
export function themeOfPage(element: Element): MapTheme {
  const computed = getComputedStyle(element);
  return themeFrom((token) => computed.getPropertyValue(token));
}

export const SOURCE = "areas";

export const LAYER = {
  water: "water",
  fill: "areas-fill",
  filtered: "areas-filtered",
  unranked: "areas-unranked",
  outline: "areas-outline",
} as const;

/** The image each pattern is drawn with. */
export const PATTERN_IMAGE: Readonly<Record<Exclude<Pattern, "none">, string>> = {
  filtered: "lines",
  unranked: "dots",
};

/** The widths of an outline: as it is, under the pointer or the focus, and when chosen. */
export const OUTLINE = { plain: 1, hovered: 2, selected: 3 } as const;

/** What a basemap adds, when there is one: its sources, and its layers under the areas. */
export interface Basemap {
  readonly sources: Readonly<Record<string, SourceSpecification>>;
  readonly layers: readonly LayerSpecification[];
  readonly glyphs?: string;
}

const NO_AREAS: GeometryData = { type: "FeatureCollection", features: [] };

function matching(ids: readonly string[]): FilterSpecification {
  // With no area to match, a filter that matches nothing.
  return ["in", ["get", "area_id"], ["literal", [...ids]]];
}

/** The colour of each area: the band of its fit, or land where it has none. */
export function fillColour(fills: ReadonlyMap<string, Fill>, theme: MapTheme) {
  const { bands } = idsBy(fills);
  const cases: (string | string[])[] = [];
  for (const band of [1, 2, 3, 4, 5] as const satisfies readonly Band[]) {
    const ids = bands[band];
    const colour = theme.bands[band - 1];
    if (ids.length > 0 && colour !== undefined) cases.push(ids, colour);
  }
  if (cases.length === 0) return theme.land;
  return ["match", ["get", "area_id"], ...cases, theme.land] as unknown as NonNullable<
    Extract<LayerSpecification, { type: "fill" }>["paint"]
  >["fill-color"];
}

/** The areas drawn with a pattern. */
export function patternFilter(
  fills: ReadonlyMap<string, Fill>,
  pattern: Exclude<Pattern, "none">,
): FilterSpecification {
  return matching(idsBy(fills).patterns[pattern]);
}

/**
 * The whole style: water, the areas filled, the two patterns, the outlines.
 * It names no address, so drawing it asks nothing of any host.
 */
export function buildStyle(
  theme: MapTheme,
  geometry: GeometryData = NO_AREAS,
  fills: ReadonlyMap<string, Fill> = new Map(),
  basemap?: Basemap,
): StyleSpecification {
  return {
    version: 8,
    ...(basemap?.glyphs === undefined ? {} : { glyphs: basemap.glyphs }),
    sources: {
      ...basemap?.sources,
      [SOURCE]: {
        type: "geojson",
        // The API's own collection. Each feature is known by its area id.
        data: geometry as unknown as GeoJSONSourceSpecification["data"],
        promoteId: "area_id",
      },
    },
    layers: [
      { id: LAYER.water, type: "background", paint: { "background-color": theme.water } },
      ...(basemap?.layers ?? []),
      {
        id: LAYER.fill,
        type: "fill",
        source: SOURCE,
        paint: { "fill-color": fillColour(fills, theme), "fill-antialias": true },
      },
      {
        id: LAYER.filtered,
        type: "fill",
        source: SOURCE,
        filter: patternFilter(fills, "filtered"),
        paint: { "fill-pattern": PATTERN_IMAGE.filtered },
      },
      {
        id: LAYER.unranked,
        type: "fill",
        source: SOURCE,
        filter: patternFilter(fills, "unranked"),
        paint: { "fill-pattern": PATTERN_IMAGE.unranked },
      },
      {
        id: LAYER.outline,
        type: "line",
        source: SOURCE,
        layout: { "line-join": "round" },
        paint: {
          "line-color": theme.line,
          "line-width": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            OUTLINE.selected,
            ["boolean", ["feature-state", "hovered"], false],
            OUTLINE.hovered,
            OUTLINE.plain,
          ],
        },
      },
    ],
  };
}

export interface PatternPixels {
  readonly width: number;
  readonly height: number;
  readonly data: Uint8Array;
}

function channels(colour: string): [number, number, number] {
  const hex = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(colour.trim());
  if (!hex) return [34, 34, 34];
  return [parseInt(hex[1] ?? "0", 16), parseInt(hex[2] ?? "0", 16), parseInt(hex[3] ?? "0", 16)];
}

/** How big one tile of a pattern is, in pixels. */
export const PATTERN_SIZE = 8;

/**
 * One tile of a pattern, as pixels: lines that run up to the right for an
 * area a limit left out, and dots for one that is not ranked. It is worked
 * out here and not loaded, so no image comes from anywhere. Where nothing is
 * drawn the tile is clear, so the area's own colour shows through.
 */
export function patternPixels(pattern: Exclude<Pattern, "none">, colour: string): PatternPixels {
  const size = PATTERN_SIZE;
  const [red, green, blue] = channels(colour);
  const data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const inked =
        pattern === "filtered"
          ? (x + y) % size === 0
          : (x % 4 === 1 || x % 4 === 2) && (y % 4 === 1 || y % 4 === 2) && (x < 4) === (y < 4);
      if (!inked) continue;
      data.set([red, green, blue, 255], (y * size + x) * 4);
    }
  }
  return { width: size, height: size, data };
}

/** What this file asks of a map: the few calls that change how it looks. */
export interface StyledMap {
  hasImage(name: string): boolean;
  addImage(name: string, image: PatternPixels, options?: { pixelRatio?: number }): unknown;
  removeImage?(name: string): unknown;
  setPaintProperty(layer: string, name: string, value: unknown): unknown;
  setFilter(layer: string, filter: FilterSpecification): unknown;
  setFeatureState(feature: { source: string; id: string }, state: Record<string, boolean>): unknown;
}

/**
 * Draws the two patterns in the colour of the outlines, and hands them to the
 * map. One the map already has is left as it is, unless it is to be drawn
 * again, as when the colours have changed.
 */
export function addPatterns(map: StyledMap, theme: MapTheme, again = false): void {
  for (const pattern of ["filtered", "unranked"] as const) {
    const name = PATTERN_IMAGE[pattern];
    if (again && map.hasImage(name)) map.removeImage?.(name);
    if (!map.hasImage(name)) map.addImage(name, patternPixels(pattern, theme.line));
  }
}

/** Colours each area by the band of its fit, and puts the patterns on the areas with no rank. */
export function applyFills(map: StyledMap, fills: ReadonlyMap<string, Fill>, theme: MapTheme): void {
  map.setPaintProperty(LAYER.fill, "fill-color", fillColour(fills, theme));
  map.setFilter(LAYER.filtered, patternFilter(fills, "filtered"));
  map.setFilter(LAYER.unranked, patternFilter(fills, "unranked"));
}

/** Draws the map again in another theme, as when the system turns dark. */
export function applyTheme(map: StyledMap, fills: ReadonlyMap<string, Fill>, theme: MapTheme): void {
  map.setPaintProperty(LAYER.water, "background-color", theme.water);
  map.setPaintProperty(LAYER.outline, "line-color", theme.line);
  addPatterns(map, theme, true);
  applyFills(map, fills, theme);
}

/** Marks an area as chosen or as under the pointer, or takes the mark off. */
export function markArea(
  map: StyledMap,
  areaId: string,
  mark: "selected" | "hovered",
  on: boolean,
): void {
  map.setFeatureState({ source: SOURCE, id: areaId }, { [mark]: on });
}
