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
  lead: "Two to four areas side by side: where each sits on each vibe, and then how each does on what counts.",
  add: (area: string) => `Add ${area} to compare`,
  remove: (area: string) => `Remove ${area} from compare`,
  /** On a result, where the area is named beside the button. */
  addShort: "Compare",
  removeShort: "Remove from compare",
  /** The name of the short button: what is seen on it, and then the area, so that it can be spoken to. */
  addNamed: (area: string) => `Compare: ${area}`,
  removeNamed: (area: string) => `Remove from compare: ${area}`,
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
  one: "One area chosen. Choose at least one more.",
  full: "Four areas is the most. Remove one to add another.",
  go: (count: number) => `Compare ${count} areas`,
  clear: "Clear",
  remove: (area: string) => `Remove ${area}`,
} as const;

export const COMPARE_TABLE = {
  areas: "The areas compared",
  /** The vibes of each area, side by side. They come before the measured parts. */
  character: {
    title: "Character",
    caption: "Where each area sits on each vibe, in one of five bands",
    what: "Vibe",
    /**
     * Said once over the vibes, of each area that some of them cannot place. The name is the
     * API's, and both counts are of the marks the API sent.
     */
    unplaced: (area: string, count: number, of: number) =>
      count === of
        ? `Burro cannot place ${area} on any vibe.`
        : `Burro cannot place ${area} on ${count} of the ${of} vibes.`,
    /** Why, said once for all of them. */
    unplacedWhy:
      "Too few parts of each recipe have a figure for it. An area is never put in the middle for want of data.",
    /** In the cell of a vibe that cannot place the area. Why is said once, over the vibes. */
    notPlaced: "Not placed",
  },
  /** The rows of journeys, where a search names places to reach. The name of a place is the API's. */
  journeys: {
    /** Under the name of the row: where the journey is to. */
    to: (place: string) => `To ${place}`,
    /**
     * Under the first row of journeys, where the average of them counts: why no cell says what
     * a journey adds to the fit. The API works out one figure for them all.
     */
    together: "What the journeys add to the fit is worked out for all of them together, so no journey says its own.",
    /** In the cell of an area that has no time for this journey in the data. */
    missing: "No journey time in this data",
  },
  /** The heading over the things that count, each with how each area does on it. */
  counts: "What counts",
  caption: "Each thing that counts, and how each area does on it",
  what: "What counts",
  /**
   * How much a thing counts, under its name. It is a weight and no share: "Counts for 100 of
   * 100" stood over "Counts for 10 of 100", and read as parts of one hundred.
   */
  countsFor: (weight: number) => `Weight ${weight}`,
  /** Over the table, once: what a weight is. */
  weights:
    "A weight says how much a thing counts beside the others, from 0 to 100, as its slider is set. The weights are not shares, and do not add up to 100.",
  adds: (points: number) => `Adds ${points} of 100 to the fit`,
  noFigure: "No figure in this data",
  notScored: "Not worked out: this area was left out before it was scored",
  /** Beside an area that has a figure for part of what counts. It says nothing of a search: none may be open. */
  basedOn: (present: number, counted: number) => `It has a figure for ${present} of the ${counted} things that count`,
  /** Under it, where there is a fit to trust the less for it. */
  restsOnPart: "So its fit rests on part of what counts, and what each thing adds is a larger share of it.",
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
  commute_likely_beyond:
    "Left out: a journey is likely beyond a firm limit. Estimated from distance, not from a timetable.",
  not_rankable: "Not ranked in this data",
  insufficient_data: "Not ranked: too little data for what counts",
  // A default counts as character too, so the words say what counts and not what was asked for.
  character_unknown: "Not ranked: too little is known of the character that counts",
};

/** The words for a status. A status the website has no words for is said in none. */
export function statusWords(status: string): string | null {
  const known: Readonly<Record<string, string | undefined>> = COMPARE_STATUS;
  return known[status] ?? null;
}
