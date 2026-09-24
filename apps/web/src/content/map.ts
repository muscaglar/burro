/**
 * Site copy for the map and for the table that says everything the map does.
 *
 * It names controls and states. An area's name, its rank and its fit are the
 * API's, and fill the gaps in the lines below.
 */

export const MAP = {
  label: "Map of the areas",
  /** On a narrow screen the map is a strip above the list. This button shows the whole of it. */
  taller: "Show the whole map",
  shorter: "Show less of the map",
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
  /** Where the map is coloured by one vibe. The name of the vibe and of each end are the API's. */
  vibe: (vibe: string) => `Coloured by ${vibe}, in five bands`,
  vibeBand: (band: number) => `Band ${band}`,
  vibeEnd: (band: number, end: string) => `Band ${band}, ${end}`,
  notPlaced: "Burro cannot place it. Shown with dots.",
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
  /** The button that opens the table, which says everything the map does. */
  title: "Table of all areas",
  caption: "Every area, in order of fit and then by name",
  captionEmpty: "Every area, by name",
  columns: { rank: "Rank", area: "Area", borough: "Borough", fit: "Fit", status: "Status" },
  /** In the column of the vibe the map is coloured by, for an area the vibe cannot place. */
  notPlaced: "Cannot be placed",
  ranked: "Ranked",
  notYet: "Not ranked yet",
  /** In place of a rank and of a fit, for an area that has none. Words, and never "None". */
  noRank: "Not ranked",
  noFit: "No fit",
  /** After why an area is not ranked: what it has no figure for, by the names the API gives. */
  lacks: "No figure for:",
  show: "Show",
  select: (area: string) => `Show ${area} on the map and in the list`,
} as const;
