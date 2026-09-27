/**
 * Words for the codes the API sends. A code is the API's; the word for it is
 * site copy. Each table is typed by the generated enum, so a code the
 * contract gains is a type error here until it has a word.
 *
 * No word here says anything of a place.
 */

import type {
  Combine,
  Dimension,
  Direction,
  Mode,
  Polarity,
  PtBasis,
  Segment,
  Strictness,
  Tenure,
  TermReading,
} from "@/lib/api/schema";

export const DIMENSION: Readonly<Record<Dimension, string>> = {
  crime: "Recorded crime",
  schools: "Schools",
  green_water: "Green space and water",
  air_noise: "Air and noise",
  venues_culture: "Venues and culture",
  homes: "Homes",
  // It holds the bus stops and the bus routes near a home, beside the stations.
  station_access: "Stations and bus stops",
  services: "Shops and services",
  brands: "Brands nearby",
  residents: "Who lived there at the census",
};

/**
 * The order the dimensions are shown in. What is there comes first, and who lived there
 * after it. Recorded crime is last: it is off unless asked for.
 */
export const DIMENSION_ORDER: readonly Dimension[] = [
  "station_access",
  "green_water",
  "air_noise",
  "venues_culture",
  "services",
  "brands",
  "schools",
  "homes",
  "residents",
  "crime",
];

/**
 * Which way a measurement counts, under its switch in the settings and in the methods. It
 * says what follows for the ranking and no more: "A higher figure counts as better" stood
 * under measurements of who lives somewhere, and read as a judgement of them. Nothing is
 * better. A figure is higher or lower, and an area ranks higher for it or does not.
 */
export const POLARITY: Readonly<Record<Polarity, string>> = {
  more: "A higher figure ranks an area higher",
  less: "A lower figure ranks an area higher",
  either: "You choose whether a higher or a lower figure ranks an area higher",
};

/** The two ways a measurement can count, where a person chooses between them. */
export const DIRECTION: Readonly<Record<Direction, string>> = {
  more: "A higher figure ranks higher",
  less: "A lower figure ranks higher",
};

/**
 * How a measurement of a vibe is read, where the vibe runs one way. "Counts towards the
 * vibe" was read twice by somebody who had never seen Burro: a figure that is higher, or
 * lower, means more of the vibe, and the words say so.
 */
export const READING: Readonly<Record<TermReading, string>> = {
  high: "A higher figure means more of this vibe",
  low: "A lower figure means more of this vibe",
};

/**
 * How a measurement of a scale is read. The name of the end is the API's. Neither end of a
 * scale is more of anything, so a figure counts towards one end, by its name.
 */
export const READING_TOWARDS: Readonly<Record<TermReading, (end: string) => string>> = {
  high: (end) => `A higher figure counts towards ${end}`,
  low: (end) => `A lower figure counts towards ${end}`,
};

export const TENURE: Readonly<Record<Tenure, string>> = {
  rent: "Renting",
  buy: "Buying",
  visit: "Visiting",
};

export const SEGMENT: Readonly<Record<Segment, string>> = {
  room: "A room",
  studio: "A studio",
  bed_1: "One bedroom",
  bed_2: "Two bedrooms",
  bed_3: "Three bedrooms",
  bed_4plus: "Four bedrooms or more",
  flat: "A flat",
  terraced: "A terraced house",
  semi_detached: "A semi-detached house",
  detached: "A detached house",
};

export const MODE: Readonly<Record<Mode, string>> = {
  pt: "Public transport",
  cycle: "By bike",
  walk: "On foot",
};

export const STRICTNESS: Readonly<Record<Strictness, string>> = {
  soft: "Flexible",
  hard: "Firm limit",
};

/**
 * Which journey counts, where there are two or more. The first is the API's
 * `slowest`: the journey that is worth least against its own limit, which
 * need not be the one that takes the most minutes (contract 6.4). It is said
 * as the line under the journeys of a result says it: "does least well".
 */
export const COMBINE: Readonly<Record<Combine, string>> = {
  slowest: "Only the journey that does least well against its limit counts",
  mean: "The average of the journeys counts",
};

export const PT_BASIS: Readonly<Record<PtBasis, string>> = {
  typical: "The typical time counts",
  just_missed: "The time if you just miss a service counts",
};
