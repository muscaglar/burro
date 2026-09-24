/**
 * The city an id belongs to, as it appears in an area's address.
 *
 * An id begins with its city: `syn` for the synthetic city and `lon` for
 * London. This file holds the pair, and nothing else does.
 */

const CITY_FOR_PREFIX = {
  syn: "synthetic",
  lon: "london",
} as const;

export type CityPrefix = keyof typeof CITY_FOR_PREFIX;
export type City = (typeof CITY_FOR_PREFIX)[CityPrefix];

export const CITIES: readonly City[] = Object.values(CITY_FOR_PREFIX);

/** The city of an area id, a place id or a release id. `null` for an id of neither city. */
export function cityOf(id: string): City | null {
  const prefix = id.split("-", 1)[0];
  return prefix === "syn" || prefix === "lon" ? CITY_FOR_PREFIX[prefix] : null;
}

export function isCity(value: string): value is City {
  return (CITIES as readonly string[]).includes(value);
}
