/**
 * Where one area is: the whole of the city drawn small as one shape, with a
 * mark where the area stands, and the area drawn close among the areas
 * around it.
 *
 * The picture once drew the outline of every area, each as a shape of its
 * own. On a release of a thousand areas that was a thousand shapes in every
 * page of an area, and the area could not be found among them. The city is
 * now one shape, drawn to the whole pixel, and the area is drawn close.
 */

import type { GeometryData } from "@/lib/api/schema";

import { boundsOf, pathOf, projector, type Bounds, type Frame, type Position } from "./project";

/** The size the area is drawn close at, and the size the city is drawn small at. */
export const CLOSE_FRAME: Frame = { width: 160, height: 120, padding: 12 };
export const CITY_FRAME: Frame = { width: 80, height: 60, padding: 3 };
/** How far about the area the close picture looks, as a share of the area's own width and height. */
const ABOUT = 0.9;
/** The least the close picture looks about an area, in degrees, so that a small area is not drawn alone. */
const LEAST_ABOUT = 0.004;

export interface Drawn {
  readonly areaId: string;
  /** The outline of the area, as the path of an SVG. */
  readonly path: string;
}

export interface Located {
  /** Every area of the city as one shape, in `CITY_FRAME`. */
  readonly city: string;
  /** Where the area stands in the city, in `CITY_FRAME`. */
  readonly at: readonly [x: number, y: number];
  /** The areas around the area, in `CLOSE_FRAME`, and then the area itself, which is drawn last. */
  readonly around: readonly Drawn[];
  readonly here: Drawn;
}

/** The outer ring of every part of a shape. A hole is not drawn in a shape this small. */
function outerRings(geometry: GeometryData["features"][number]["geometry"]): readonly (readonly Position[])[] {
  if (geometry.type === "Polygon") return (geometry.coordinates as readonly (readonly Position[])[]).slice(0, 1);
  return (geometry.coordinates as readonly (readonly (readonly Position[])[])[]).flatMap((part) => part.slice(0, 1));
}

/**
 * Every area as one shape, drawn to the whole pixel. A point that falls where the one
 * before it fell is left out, and an area too small to have a shape is one pixel, so that
 * the city has no hole where its smallest areas stand.
 */
function shapeOfTheCity(geometry: GeometryData, frame: Frame): string {
  const bounds = boundsOf(geometry);
  if (bounds === null) return "";
  const project = projector(bounds, frame);
  const drawn: string[] = [];
  for (const feature of geometry.features) {
    for (const ring of outerRings(feature.geometry)) {
      const points: string[] = [];
      for (const position of ring) {
        const [x, y] = project(position);
        const point = `${Math.round(x)} ${Math.round(y)}`;
        if (points[points.length - 1] !== point) points.push(point);
      }
      if (points.length > 1 && points[0] === points[points.length - 1]) points.pop();
      const [first] = points;
      if (first === undefined) continue;
      drawn.push(new Set(points).size >= 3 ? `M${points.join("L")}Z` : `M${first}h1v1h-1Z`);
    }
  }
  return drawn.join("");
}

/** The shape of the city, worked out once for the boundaries in hand. */
const cities = new WeakMap<GeometryData, string>();

function cityOf(geometry: GeometryData): string {
  const held = cities.get(geometry);
  if (held !== undefined) return held;
  const shape = shapeOfTheCity(geometry, CITY_FRAME);
  cities.set(geometry, shape);
  return shape;
}

/** The box of each area, worked out once for the boundaries in hand. */
const boxes = new WeakMap<GeometryData, readonly (Bounds | null)[]>();

function boxesOf(geometry: GeometryData): readonly (Bounds | null)[] {
  const held = boxes.get(geometry);
  if (held !== undefined) return held;
  const found = geometry.features.map((feature) => boundsOf({ features: [feature] }));
  boxes.set(geometry, found);
  return found;
}

const overlap = ([[west, south], [east, north]]: Bounds, [[w, s], [e, n]]: Bounds): boolean =>
  west <= e && w <= east && south <= n && s <= north;

/** Where an area is. `null` for an area the boundaries do not hold. */
export function locate(geometry: GeometryData, areaId: string): Located | null {
  const at = geometry.features.findIndex((feature) => feature.properties.area_id === areaId);
  const feature = geometry.features[at];
  const own = boxesOf(geometry)[at];
  const whole = boundsOf(geometry);
  if (feature === undefined || own === undefined || own === null || whole === null) return null;
  const [[west, south], [east, north]] = own;
  const across = Math.max((east - west) * ABOUT, LEAST_ABOUT);
  const up = Math.max((north - south) * ABOUT, LEAST_ABOUT);
  const about: Bounds = [
    [west - across, south - up],
    [east + across, north + up],
  ];
  const close = projector(about, CLOSE_FRAME);
  const around = geometry.features.flatMap((other, index) => {
    const box = boxesOf(geometry)[index];
    if (index === at || box === undefined || box === null || !overlap(box, about)) return [];
    return [{ areaId: other.properties.area_id, path: pathOf(other.geometry, close) }];
  });
  const [x, y] = projector(whole, CITY_FRAME)([(west + east) / 2, (south + north) / 2]);
  return {
    city: cityOf(geometry),
    at: [Math.round(x * 10) / 10, Math.round(y * 10) / 10],
    around,
    here: { areaId, path: pathOf(feature.geometry, close) },
  };
}
