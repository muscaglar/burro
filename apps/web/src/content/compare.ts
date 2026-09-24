/**
 * Site copy for comparing areas: the tray that holds the areas chosen, and
 * the page that sets them side by side.
 *
 * Nothing here says anything of a place. An area's name and every figure are
 * the API's. Where a line below has a gap in it, the gap is filled with a
 * name or a count.
 */

import type { CompareStatus, Tenure } from "@/lib/api/schema";

export const COMPARE = {
  title: "Compare areas",
  lead: "Two to four areas side by side. The rows are in the order of what counts most.",
  add: (area: string) => `Add ${area} to compare`,
  remove: (area: string) => `Remove ${area} from compare`,
  comparing: "Comparing the areas",
  compared: (count: number) => `${count} areas compared.`,
  tooFew: "A comparison takes two to four areas. Choose areas from the search or from an area's page.",
  unknown: (count: number) =>
    count === 1
      ? "One area in this link is not in this data, and was left out."
      : `${count} areas in this link are not in this data, and were left out.`,
  dropped: (count: number) =>
    count === 1
      ? "This link names more than four areas. One was left out."
      : `This link names more than four areas. ${count} were left out.`,
  fromSearch: "These areas are compared on your search. The rows are in the order of what counts most in it.",
  fromDefaults: {
    rent: "No search is open, so these areas are compared on the usual settings for renting. A search of your own puts the rows in the order of what counts most to you.",
    buy: "No search is open, so these areas are compared on the usual settings for buying. A search of your own puts the rows in the order of what counts most to you.",
  } satisfies Record<Tenure, string>,
  nothingCounts: "Nothing is set to count in this search, so there is nothing to compare the areas on.",
  needsScripts: "The comparison is worked out in your browser, and needs scripts. Each area's own page reads without them.",
  toSearch: "Go to the search",
  chooseOthers: "Choose other areas",
  failedTitle: "The areas could not be compared",
} as const;

export const TRAY = {
  title: "Areas to compare",
  none: "No area chosen yet. Choose two to four.",
  one: "One area chosen. Choose at least one more.",
  full: "Four areas is the most. Remove one to add another.",
  go: (count: number) => `Compare ${count} areas`,
  clear: "Clear",
  remove: (area: string) => `Remove ${area}`,
} as const;

export const COMPARE_TABLE = {
  areas: "The areas compared",
  caption: "Each thing that counts, and how each area does on it",
  what: "What counts",
  countsFor: (weight: number) => `Counts for ${weight} of 100`,
  adds: (points: number) => `Adds ${points} of 100 to the fit`,
  noFigure: "No figure in this data",
  notScored: "Not worked out: this area was left out before it was scored",
  /** Where an area stands in the search that is open. The fit is left out when nothing is set to rank by. */
  standing: (rank: number, fit: number | null) =>
    fit === null ? `Rank ${rank}` : `Rank ${rank}. Fit ${fit} of 100`,
  open: (area: string) => `Open the page for ${area}`,
  takeOut: (area: string) => `Take ${area} out of this comparison`,
} as const;

/** What an area's status is called. The reasons are the ones the result list gives. */
export const COMPARE_STATUS: Readonly<Record<CompareStatus, string>> = {
  ranked: "Ranked",
  excluded: "Left out: hidden by you",
  not_selected: "Left out: not one of the areas you chose",
  over_budget: "Left out: over your budget, which is a firm limit",
  commute_cap: "Left out: a journey is longer than a firm limit",
  not_rankable: "Not ranked in this data",
  insufficient_data: "Not ranked: too little data for what counts",
};
