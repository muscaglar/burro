/**
 * Site copy for the map and for the table that says everything the map does.
 *
 * It names controls and states. An area's name, its rank and its fit are the
 * API's, and fill the gaps in the lines below.
 */

export const MAP = {
  label: "Map of the areas",
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
  noScore: "No fit yet",
  filtered: "Left out by a limit you set. Shown with lines.",
  unranked: "Not ranked. Shown with dots.",
  pin: "A numbered pin is the rank of one of the first ten.",
} as const;

export const MAP_CARD = {
  label: "The area chosen on the map",
  showInList: "Show in the list",
  close: "Close",
  notInList: "This area is not in the list.",
} as const;

export const TABLE = {
  caption: "Every area, in order of fit and then by name",
  captionEmpty: "Every area, by name",
  columns: { rank: "Rank", area: "Area", borough: "Borough", fit: "Fit", status: "Status" },
  ranked: "Ranked",
  notYet: "Not ranked yet",
  /** In place of a rank and of a fit, for an area that has none. Words, and never "None". */
  noRank: "Not ranked",
  noFit: "No fit",
  /**
   * Under the table, once there is a ranking that names more areas than the list holds. How
   * much of what counts a fit rests on is known for the areas of the list and for no other.
   */
  partNote:
    "Where a fit rests on only part of what counts in your search, the table says so for the areas in the list. It cannot yet say so for an area further down.",
  show: "Show",
  select: (area: string) => `Show ${area} on the map and in the list`,
} as const;
