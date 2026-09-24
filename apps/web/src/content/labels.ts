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
  station_access: "Stations",
  services: "Shops and services",
};

/** The order the dimensions are shown in. Recorded crime is last: it is off unless asked for. */
export const DIMENSION_ORDER: readonly Dimension[] = [
  "station_access",
  "green_water",
  "air_noise",
  "venues_culture",
  "services",
  "schools",
  "homes",
  "crime",
];

export const POLARITY: Readonly<Record<Polarity, string>> = {
  more: "A higher figure counts as better",
  less: "A lower figure counts as better",
  either: "You choose whether higher or lower is better",
};

export const DIRECTION: Readonly<Record<Direction, string>> = {
  more: "Higher is better",
  less: "Lower is better",
};

export const READING: Readonly<Record<TermReading, string>> = {
  high: "A higher figure counts towards the vibe",
  low: "A lower figure counts towards the vibe",
};

/** How a part of a scale is read. The name of the end is the API's. */
export const READING_TOWARDS: Readonly<Record<TermReading, (end: string) => string>> = {
  high: (end) => `A higher figure counts towards ${end}`,
  low: (end) => `A lower figure counts towards ${end}`,
};

export const TENURE: Readonly<Record<Tenure, string>> = {
  rent: "Renting",
  buy: "Buying",
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
 * need not be the one that takes the most minutes (contract 6.4).
 */
export const COMBINE: Readonly<Record<Combine, string>> = {
  slowest: "Only the journey that does worst against its limit counts",
  mean: "The average of the journeys counts",
};

export const PT_BASIS: Readonly<Record<PtBasis, string>> = {
  typical: "The typical time counts",
  just_missed: "The time if you just miss a service counts",
};
