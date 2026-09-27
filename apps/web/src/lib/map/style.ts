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
 * It is drawn as the map of a gentle game is: green land on blue water, each
 * with the grain of its tile. The grain is a grain. It is the same on every
 * area of one colour, and says nothing of the place it lies on. No hill, no
 * tree, no boat and no building is drawn, because the data holds none.
 *
 * Colours are the design tokens. They are read from the page when the map
 * starts, so that tokens.css stays the one place a colour is given.
 */

import type { ExpressionSpecification, FilterSpecification, GeoJSONSourceSpecification, LayerSpecification, SourceSpecification, StyleSpecification } from "maplibre-gl";

import type { GeometryData } from "@/lib/api/schema";

import { idsBy, type Band, type Fill, type Pattern } from "./fill";

export interface MapTheme {
  readonly water: string;
  /** The second blue, in which the glints of the water are drawn. */
  readonly glint: string;
  readonly land: string;
  readonly line: string;
  /** The five bands of fit, low to high. */
  readonly bands: readonly [string, string, string, string, string];
}

/** The token each colour of the map comes from. */
export const THEME_TOKENS = {
  water: "--map-water",
  glint: "--map-glint",
  land: "--map-land",
  line: "--map-line",
  bands: ["--map-1", "--map-2", "--map-3", "--map-4", "--map-5"],
} as const;

/**
 * What is drawn if a token cannot be read, as where a style sheet failed to
 * load: the colours of the look, as tokens.css gives them. A test holds each
 * to its token, so that the map is one map whether or not it could be asked.
 */
const WITHOUT_TOKENS: MapTheme = {
  water: "#86dde2",
  glint: "#2f9fd0",
  land: "#e9cf94",
  line: "#2a2140",
  bands: ["#e6f1c5", "#a8d85e", "#63b34a", "#3c9952", "#317e5d"],
};

/** The theme, from a function that reads a token's value. A test passes its own. */
export function themeFrom(read: (token: string) => string | undefined): MapTheme {
  const colour = (token: string, otherwise: string) => read(token)?.trim() || otherwise;
  const [one, two, three, four, five] = THEME_TOKENS.bands;
  const [a, b, c, d, e] = WITHOUT_TOKENS.bands;
  return {
    water: colour(THEME_TOKENS.water, WITHOUT_TOKENS.water),
    glint: colour(THEME_TOKENS.glint, WITHOUT_TOKENS.glint),
    land: colour(THEME_TOKENS.land, WITHOUT_TOKENS.land),
    line: colour(THEME_TOKENS.line, WITHOUT_TOKENS.line),
    bands: [colour(one, a), colour(two, b), colour(three, c), colour(four, d), colour(five, e)],
  };
}

/** The theme as the page has it. The look is one, whatever the system asks. */
export function themeOfPage(element: Element): MapTheme {
  const computed = getComputedStyle(element);
  return themeFrom((token) => computed.getPropertyValue(token));
}

/** The token that says how many pixels of the screen one pixel of the ground takes. */
export const PIXEL_TOKEN = "--px-ground";
/** What it is where it cannot be read. */
const PIXEL = 2;

/**
 * How many pixels of the screen one pixel of the grain takes: what one pixel
 * of the meadow takes that the page stands on, so that the grass of the map
 * is the grass of the page.
 */
export function pixelOfPage(element: Element): number {
  const said = Number.parseFloat(getComputedStyle(element).getPropertyValue(PIXEL_TOKEN));
  return Number.isFinite(said) && said > 0 ? said : PIXEL;
}

export const SOURCE = "areas";

export const LAYER = {
  water: "water",
  fill: "areas-fill",
  grain: "areas-grain",
  filtered: "areas-filtered",
  unranked: "areas-unranked",
  outline: "areas-outline",
} as const;

/** The image each pattern is drawn with. */
export const PATTERN_IMAGE: Readonly<Record<Exclude<Pattern, "none">, string>> = {
  filtered: "lines",
  unranked: "dots",
};

/** The image the grain of the water is drawn with, and that of the land of each band. */
export const GRAIN_IMAGE = {
  water: "water",
  land: ["land-0", "land-1", "land-2", "land-3", "land-4", "land-5"],
} as const satisfies { water: string; land: Readonly<Record<Band, string>> };

/** Every image the map is handed, by name. */
export const IMAGES: readonly string[] = [GRAIN_IMAGE.water, ...GRAIN_IMAGE.land, ...Object.values(PATTERN_IMAGE)];

/** The widths of an outline: as it is, under the pointer or the focus, and when chosen. */
export const OUTLINE = { plain: 1, hovered: 2, selected: 3 } as const;
/**
 * How an outline thins as the map is seen from further off. At the width of a city of a
 * thousand areas the outlines of the small areas met, and hid the colour of each. From
 * `NEAR` inwards an outline is as wide as it was.
 */
export const FAR = { zoom: 9, width: 0.3 } as const;
export const NEAR = { zoom: 12 } as const;

/** The width of an outline, where a plain one is this wide. The chosen and the pointed at keep theirs. */
const outlineWidth = (plain: number): ExpressionSpecification => [
  "case",
  ["boolean", ["feature-state", "selected"], false],
  OUTLINE.selected,
  ["boolean", ["feature-state", "hovered"], false],
  OUTLINE.hovered,
  plain,
];

/** What a basemap adds, when there is one: its sources, and its layers under the areas. */
export interface Basemap {
  readonly sources: Readonly<Record<string, SourceSpecification>>;
  readonly layers: readonly LayerSpecification[];
  readonly glyphs?: string;
}

const NO_AREAS: GeometryData = { type: "FeatureCollection", features: [] };

const EVERY_BAND = [1, 2, 3, 4, 5] as const satisfies readonly Band[];

/** True of an area that is one of these. With no area to match, it is true of none. */
function among(ids: readonly string[]): ExpressionSpecification {
  return ["in", ["get", "area_id"], ["literal", [...ids]]];
}

/** One thing for the areas of each band that has any, and another for every other area. */
function byBand<Value extends string>(
  fills: ReadonlyMap<string, Fill>,
  of: (band: Band) => Value | undefined,
): Value | unknown[] {
  const { bands } = idsBy(fills);
  const cases: (string | string[])[] = [];
  for (const band of EVERY_BAND) {
    const ids = bands[band];
    const value = of(band);
    if (ids.length > 0 && value !== undefined) cases.push(ids, value);
  }
  const otherwise = of(0) as Value;
  return cases.length === 0 ? otherwise : ["match", ["get", "area_id"], ...cases, otherwise];
}

/** The colour of each area: the band of its fit, or land where it has none. */
export function fillColour(fills: ReadonlyMap<string, Fill>, theme: MapTheme) {
  return byBand(fills, (band) => (band === 0 ? theme.land : theme.bands[band - 1])) as unknown as NonNullable<
    Extract<LayerSpecification, { type: "fill" }>["paint"]
  >["fill-color"];
}

/** The grain of each area: that of its band, which is drawn in a colour that shows on the band. */
export function grainOf(fills: ReadonlyMap<string, Fill>) {
  return byBand(fills, (band) => GRAIN_IMAGE.land[band]) as unknown as NonNullable<
    Extract<LayerSpecification, { type: "fill" }>["paint"]
  >["fill-pattern"];
}

/** The areas drawn with a pattern. */
export function patternFilter(
  fills: ReadonlyMap<string, Fill>,
  pattern: Exclude<Pattern, "none">,
): FilterSpecification {
  return among(idsBy(fills).patterns[pattern]);
}

/**
 * The areas that bear the grain: every area but those drawn with a pattern. Lines and
 * dots each go with a reason that is given in words, and nothing is laid under them that
 * would make either harder to tell.
 */
export function grainFilter(fills: ReadonlyMap<string, Fill>): FilterSpecification {
  const { patterns } = idsBy(fills);
  return ["!", among([...patterns.filtered, ...patterns.unranked])];
}

/**
 * The whole style: water, the areas filled, their grain, the two patterns, the outlines.
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
      {
        id: LAYER.water,
        type: "background",
        // The colour is what is drawn until the grain is in hand, and where it cannot be drawn.
        paint: { "background-color": theme.water, "background-pattern": GRAIN_IMAGE.water },
      },
      ...(basemap?.layers ?? []),
      {
        id: LAYER.fill,
        type: "fill",
        source: SOURCE,
        paint: { "fill-color": fillColour(fills, theme), "fill-antialias": true },
      },
      {
        id: LAYER.grain,
        type: "fill",
        source: SOURCE,
        filter: grainFilter(fills),
        paint: { "fill-pattern": grainOf(fills) },
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
            "interpolate",
            ["linear"],
            ["zoom"],
            FAR.zoom,
            outlineWidth(FAR.width),
            NEAR.zoom,
            outlineWidth(OUTLINE.plain),
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
  if (!hex) return channels(WITHOUT_TOKENS.line);
  return [parseInt(hex[1] ?? "0", 16), parseInt(hex[2] ?? "0", 16), parseInt(hex[3] ?? "0", 16)];
}

/**
 * What is drawn in pixels on the map, a character a pixel, as a drawing of the website
 * is written: `x` is a pixel that is drawn, and `.` one that is not.
 *
 * The grain of the land is the three tufts of the drawing `tile-grass-a`, and the grain
 * of the water the four glints of `tile-water-1`, point for point: a test holds each to
 * its drawing. Nothing of either touches the edge of its tile, so a tile lies edge to
 * edge with the next.
 *
 * Lines that run up to the right are for an area a limit left out, and dots for one that
 * is not ranked. A line runs from edge to edge, so that a tile joins the next.
 */
export const DRAWN = {
  land: [
    "................",
    "................",
    "..x.x...........",
    "...x............",
    "................",
    "................",
    "...........x.x..",
    "............x...",
    "................",
    "................",
    "................",
    "....x.x.........",
    ".....x..........",
    "................",
    "................",
    "................",
  ],
  water: [
    "................",
    "................",
    "..xxx...........",
    "................",
    "................",
    "..........xxx...",
    "................",
    "................",
    "................",
    "....xxx.........",
    "................",
    "................",
    "............xxx.",
    "................",
    "................",
    "................",
  ],
  filtered: ["x.......", ".......x", "......x.", ".....x..", "....x...", "...x....", "..x.....", ".x......"],
  unranked: ["......", ".x....", "......", "......", "....x.", "......"],
} as const;

/**
 * How many pixels of a picture stand for one pixel of its drawing, each way. The map
 * library draws a pattern larger the nearer the map is drawn, by any amount from once
 * to twice, and smooths what it makes larger. So a picture is handed over with more
 * pixels than it is drawn with, and the library is told how many of them make one of the
 * screen: what it then draws is a pixel of the drawing as a square with a hard edge, of
 * the size the look gives it, however near the map is drawn.
 */
export const FINENESS = 8;

/** A drawing as pixels: what is drawn in one colour, on a ground of another or on none. */
function painted(rows: readonly string[], ink: string, ground: string | null): PatternPixels {
  const size = rows.length * FINENESS;
  const inked = [...channels(ink), 255];
  // Where nothing is drawn and there is no ground the pixel is clear, and what lies under it shows.
  const bare = ground === null ? [0, 0, 0, 0] : [...channels(ground), 255];
  const data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y += 1) {
    const row = rows[Math.floor(y / FINENESS)] ?? "";
    for (let x = 0; x < size; x += 1) {
      data.set(row[Math.floor(x / FINENESS)] === "x" ? inked : bare, (y * size + x) * 4);
    }
  }
  return { width: size, height: size, data };
}

/**
 * The colour the grain of a band is drawn in: that of the band above it, which is one
 * step deeper, so that the grain is as faint on every band as the tufts of the meadow
 * are on the page. The deepest band has none above it, and takes the one below. Land
 * with no fit is no green, and its tufts are the green of the middle band.
 */
export function grainColour(band: Band, theme: MapTheme): string {
  const [, second, middle, fourth, deepest] = theme.bands;
  return ([middle, second, middle, fourth, deepest, fourth] as const)[band];
}

/**
 * One tile of a pattern, as pixels: lines that run up to the right for an
 * area a limit left out, and dots for one that is not ranked. It is worked
 * out here and not loaded, so no image comes from anywhere. Where nothing is
 * drawn the tile is clear, so the area's own colour shows through.
 */
export function patternPixels(pattern: Exclude<Pattern, "none">, colour: string): PatternPixels {
  return painted(DRAWN[pattern], colour, null);
}

/**
 * One tile of the grain of the land of a band, as pixels: its tufts, and nothing
 * between them, so that the colour of the band shows through.
 */
export function landPixels(band: Band, theme: MapTheme): PatternPixels {
  return painted(DRAWN.land, grainColour(band, theme), null);
}

/** One tile of the water, as pixels: its glints in the second blue, on the blue of the water. */
export function waterPixels(theme: MapTheme): PatternPixels {
  return painted(DRAWN.water, theme.glint, theme.water);
}

/** The images of a theme, which are worked out once: the map asks for them again whenever it is drawn nearer or further. */
const made = new WeakMap<MapTheme, ReadonlyMap<string, PatternPixels>>();

/** Every image of the map, by the name it is handed over under. */
export function imagesOf(theme: MapTheme): ReadonlyMap<string, PatternPixels> {
  const held = made.get(theme);
  if (held !== undefined) return held;
  const images = new Map<string, PatternPixels>([
    [GRAIN_IMAGE.water, waterPixels(theme)],
    ...GRAIN_IMAGE.land.map((name, band): [string, PatternPixels] => [name, landPixels(band as Band, theme)]),
    [PATTERN_IMAGE.filtered, patternPixels("filtered", theme.line)],
    [PATTERN_IMAGE.unranked, patternPixels("unranked", theme.line)],
  ]);
  made.set(theme, images);
  return images;
}

/** How the map is drawn just now: how near, and how many pixels of the screen a pixel of a drawing takes. */
export interface Scale {
  /** The zoom of the map, as the map library counts it. */
  readonly zoom: number;
  /** From `pixelOfPage`. */
  readonly pixel: number;
}

/** How near the map is drawn, from where it puts two places a degree apart. */
export function zoomOf(map: Pick<StyledMap, "project">): number {
  const across = Math.abs(map.project([1, 0]).x - map.project([0, 0]).x);
  // At zoom 0 the whole world is 512 pixels wide.
  return across > 0 ? Math.log2((across * 360) / 512) : 0;
}

/**
 * How many pixels of a picture the library is to take for one of the screen. It draws a
 * pattern at its own size where the zoom is a whole number, and larger by the part that
 * is over, up to twice.
 */
export function ratioFor({ zoom, pixel }: Scale): number {
  const over = zoom - Math.floor(zoom);
  return (FINENESS * 2 ** over) / pixel;
}

/** What this file asks of a map: the few calls that change how it looks. */
export interface StyledMap {
  hasImage(name: string): boolean;
  addImage(name: string, image: PatternPixels, options?: { pixelRatio?: number }): unknown;
  removeImage?(name: string): unknown;
  setPaintProperty(layer: string, name: string, value: unknown): unknown;
  setFilter(layer: string, filter: FilterSpecification): unknown;
  setFeatureState(feature: { source: string; id: string }, state: Record<string, boolean>): unknown;
  project(position: [number, number]): { x: number; y: number };
}

/**
 * Draws the grain and the two patterns, and hands them to the map. One the map
 * already has is left as it is, unless it is to be drawn again, as when the map
 * is drawn nearer or further.
 */
export function addPatterns(map: StyledMap, theme: MapTheme, scale: Scale, again = false): void {
  const pixelRatio = ratioFor(scale);
  for (const [name, image] of imagesOf(theme)) {
    if (again && map.hasImage(name)) map.removeImage?.(name);
    if (!map.hasImage(name)) map.addImage(name, image, { pixelRatio });
  }
}

/** Colours each area by the band of its fit, and puts the patterns on the areas with no rank. */
export function applyFills(map: StyledMap, fills: ReadonlyMap<string, Fill>, theme: MapTheme): void {
  map.setPaintProperty(LAYER.fill, "fill-color", fillColour(fills, theme));
  map.setPaintProperty(LAYER.grain, "fill-pattern", grainOf(fills));
  map.setFilter(LAYER.grain, grainFilter(fills));
  map.setFilter(LAYER.filtered, patternFilter(fills, "filtered"));
  map.setFilter(LAYER.unranked, patternFilter(fills, "unranked"));
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
