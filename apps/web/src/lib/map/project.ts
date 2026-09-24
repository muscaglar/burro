/**
 * Where things are: the bounds of the areas, and a way to draw them flat.
 *
 * The map itself is projected by the map library. This is for what is drawn
 * without it: the small picture that says where one area is among the rest.
 */

import type { Geometry, GeometryData } from "@/lib/api/schema";

export type Position = readonly [longitude: number, latitude: number];
export type Ring = readonly Position[];
/** West and south, then east and north. */
export type Bounds = readonly [Position, Position];

/** Every ring of a polygon or of a multipolygon, outer and inner alike. */
export function ringsOf(geometry: Geometry): readonly Ring[] {
  if (geometry.type === "Polygon") return geometry.coordinates as readonly Ring[];
  return (geometry.coordinates as readonly (readonly Ring[])[]).flat();
}

/** The box that holds every area. `null` when there is nothing to hold. */
export function boundsOf(geometry: Pick<GeometryData, "features">): Bounds | null {
  let [west, south, east, north] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const feature of geometry.features) {
    for (const ring of ringsOf(feature.geometry)) {
      for (const [longitude, latitude] of ring) {
        if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) continue;
        west = Math.min(west, longitude);
        east = Math.max(east, longitude);
        south = Math.min(south, latitude);
        north = Math.max(north, latitude);
      }
    }
  }
  if (west > east || south > north) return null;
  return [
    [west, south],
    [east, north],
  ];
}

export interface Frame {
  readonly width: number;
  readonly height: number;
  readonly padding: number;
}

/**
 * A way to place a position in a frame, keeping shapes as they are on the
 * ground at that latitude: a degree of longitude is drawn narrower than one
 * of latitude, by the cosine of the latitude. North is up.
 */
export function projector(bounds: Bounds, frame: Frame): (position: Position) => [number, number] {
  const [[west, south], [east, north]] = bounds;
  const squeeze = Math.cos((((south + north) / 2) * Math.PI) / 180);
  const across = Math.max((east - west) * squeeze, Number.EPSILON);
  const up = Math.max(north - south, Number.EPSILON);
  const room = { width: frame.width - 2 * frame.padding, height: frame.height - 2 * frame.padding };
  const scale = Math.min(room.width / across, room.height / up);
  const left = frame.padding + (room.width - across * scale) / 2;
  const top = frame.padding + (room.height - up * scale) / 2;
  return ([longitude, latitude]) => [
    left + (longitude - west) * squeeze * scale,
    top + (north - latitude) * scale,
  ];
}

const rounded = (value: number) => String(Math.round(value * 10) / 10);

/** The outline of a shape as the path of an SVG. */
export function pathOf(geometry: Geometry, project: (position: Position) => [number, number]): string {
  return ringsOf(geometry)
    .filter((ring) => ring.length > 2)
    .map((ring) => {
      const points = ring.map((position) => project(position).map(rounded).join(" "));
      return `M${points.join("L")}Z`;
    })
    .join("");
}
