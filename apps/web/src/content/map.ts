/**
 * Site copy for the map and for the table that says everything the map does.
 *
 * It names controls and states. An area's name, its rank and its fit are the
 * API's, and fill the gaps in the lines below.
 *
 * What a pin, the dots and the lines mean is said as the key to the drawings says it, on
 * the page of vibes: each stands beside its drawing in both places. Under the map each is
 * one line where the map stands beside the answer, since the box of the map must stand
 * whole in a window 900 px high: the key has the room to say why.
 */

import { ABOUT } from "./about";

export const MAP = {
  label: "Map of the areas",
  /**
   * On a narrow screen the map is a strip above the list. This button shows the whole of
   * it, and is on while it does: pressed again, the map is a strip again.
   */
  taller: "Show the whole map",
  keys: "Use the arrow keys to move the map, and plus and minus to zoom.",
  loading: "The map is loading.",
  noWebGL: "The map cannot be drawn in this browser. The table below says everything the map would.",
  noGeometry: "The boundaries of the areas could not be loaded. The table below says everything the map would.",
  zoomIn: "Zoom in",
  zoomOut: "Zoom out",
  whole: "Show every area",
  controls: "Map controls",
  /** `based` is how much of what counts the fit rests on, where that is not all of it. */
  pin: (rank: number, area: string, fit: string, based: string | null = null) =>
    based === null ? `Rank ${rank}, ${area}, fit ${fit}` : `Rank ${rank}, ${area}, fit ${fit}. ${based}`,
} as const;

export const LEGEND = {
  title: "What the map shows",
  fit: "Fit",
  band: (from: number, to: number) => `${from} to ${to}`,
  noScore: "Not ranked yet",
  /** Where the map is coloured by one vibe. The name of the vibe and of each end are the API's. */
  vibe: (vibe: string) => `Coloured by ${vibe}, in five bands`,
  vibeBand: (band: number) => `Band ${band}`,
  vibeEnd: (band: number, end: string) => `Band ${band}, ${end}`,
  /**
   * What the gauge under that line shows, to whoever hears the page: five shades between
   * the two ends of the vibe, and which end is which. Whoever sees it reads it from the
   * gauge, which has the picture and the name of an end at either side of its shades.
   */
  vibeRuns: (low: string, high: string) =>
    `The five shades of green run from ${low}, which is the palest, to ${high}, which is the darkest.`,
  notPlaced: "Dots mean that Burro could not work out this vibe here.",
  filtered: "Slanted lines mean that the area was left out.",
  unranked: "Dots mean that Burro could not rank the area.",
  /** The sentence of the key, word for word: one drawing is said one way. */
  pin: ABOUT.key.map.pin,
} as const;

export const MAP_CARD = {
  label: "The area chosen on the map",
  showInList: "Show in the list",
  close: "Close",
  notInList: "This area is not in the list.",
} as const;

export const TABLE = {
  /** The button that opens the table, which says everything the map does. */
  title: "Table of all areas",
  /**
   * The table is in the order of the ranking, which is not the order of the fit from top to
   * foot: an area with no figure for a thing that was asked for stands below every area
   * that has one, whatever its fit. The list of results names its order in the same words.
   */
  caption: "Every area, in the order Burro ranked them and then by name",
  captionEmpty: "Every area, by name",
  columns: { rank: "Rank", area: "Area", borough: "Borough", fit: "Fit", status: "Status" },
  /** In the column of the vibe the map is coloured by, for an area Burro could not work the vibe out for. */
  notPlaced: "Not worked out",
  ranked: "Ranked",
  notYet: "Not ranked yet",
  /** In place of a rank and of a fit, for an area that has none. Words, and never "None". */
  noRank: "Not ranked",
  noFit: "No fit",
  /** After why an area is not ranked: what it has no figure for, by the names the API gives. */
  lacks: "Burro has no figure for:",
  show: "Show",
  select: (area: string) => `Show ${area} on the map and in the list`,
} as const;
