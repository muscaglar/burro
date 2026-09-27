/**
 * Site copy for comparing areas: what says that it can be done, the button that
 * chooses an area, the bar that gathers the areas chosen, and the page that sets
 * them side by side.
 *
 * Nothing here says anything of a place. An area's name and every figure are
 * the API's. Where a line below has a gap in it, the gap is filled with a
 * name or a count.
 *
 * Nobody wins a comparison: no word here calls an area the best, a good one or
 * the better of two.
 */

import type { CompareStatus, Tenure } from "@/lib/api/schema";

import { FACT_COLUMNS } from "./facts";
import { JOURNEYS } from "./search";

/** What the button says before its area is chosen. What says that areas can be compared names it. */
const ADD = "Add to compare";
/** What it says once its area is chosen. It is amber then, and a press takes the area out again. */
const ADDED = "Added to compare";

export const COMPARE = {
  title: "Compare areas",
  lead: "These are the areas you chose, set side by side so that you can see how they differ. First comes what each area feels like, vibe by vibe, and after that how each one does on the things that count.",
  /**
   * In place of that line where one area is left, or named: one area is no comparison. It
   * says so, and what to do. The way on stands under it.
   */
  tooFew: `You have chosen one area, which is not enough to compare. Burro sets areas side by side, so it needs at least two, and it can take up to four. You can add more from the results of a search or from the page of any area, with "${ADD}".`,
  /** The same where no area is named. */
  none: `You have not chosen any areas to compare yet. Burro sets areas side by side, so it needs at least two, and it can take up to four. You can choose them from the results of a search or from the page of any area, with "${ADD}".`,
  /**
   * Over a list of results, before anybody has chosen anything: that areas can be
   * compared, and how. It names the button as the button names itself.
   */
  invite: `Choose two to four areas with "${ADD}", and Burro will put them side by side.`,
  /** The same on the page of one area, beside the button. */
  inviteHere: "Add this area and at least one other, and Burro will put them side by side.",
  /** What is seen on the button, wherever it stands: on a result, in the card of the map and on the page of an area. */
  addShort: ADD,
  removeShort: ADDED,
  /**
   * The name of the button: what is seen on it, and then the area, so that it can be spoken
   * to. Once the area is chosen the name says what a press does as well, which a person who
   * sees the page reads from the amber of the button.
   */
  addNamed: (area: string) => `${ADD}: ${area}`,
  removeNamed: (area: string) => `${ADDED}: ${area}. Press to take it out`,
  /**
   * Beside a button that can add no more, on the page of an area. Beside the name of an
   * area, as on a result, the bar of areas says why, at the foot of the screen, and the
   * button is described by what the bar says.
   */
  full: "You have already chosen four areas, which is the most Burro can compare at once. Take one out if you want to add this one.",
  comparing: "Burro is comparing the areas.",
  compared: (count: number) => `Burro has compared ${count} areas.`,
  unknown: (count: number) =>
    count === 1
      ? "This link names one area that Burro does not know, so it was left out."
      : `This link names ${count} areas that Burro does not know, so they were left out.`,
  dropped: (count: number) =>
    count === 1
      ? "Burro can compare four areas at most, and this link names more than that. Because of that, the last one was left out."
      : `Burro can compare four areas at most, and this link names more than that. Because of that, the last ${count} were left out.`,
  fromSearch:
    "Burro has compared these areas using your search. Under \"What counts\", the things that count the most in your search come first.",
  fromDefaults: {
    rent: "You have no search open, so Burro has compared these areas by the things it counts in every search for a home to rent. If you make a search first, the comparison will use that instead.",
    buy: "You have no search open, so Burro has compared these areas by the things it counts in every search for a home to buy. If you make a search first, the comparison will use that instead.",
    visit: "You have no search open, so Burro has compared these areas by the things it counts in every search for somewhere to stay. If you make a search first, the comparison will use that instead.",
  } satisfies Record<Tenure, string>,
  nothingCounts:
    "Nothing is set to count in this search, which means there is nothing to compare the areas on here. What each area feels like is still compared, vibe by vibe.",
  needsScripts:
    "Burro works the comparison out in your browser, which needs JavaScript to be switched on. Each area's own page can be read without it.",
  /**
   * The way back, at the head of the page before anything else, and again at its foot: it
   * leads to the search as it was left, with what was asked for, what was set, the results
   * and the areas that are chosen to compare.
   */
  back: "Back to your search",
  /**
   * The same where no search is open, as where a comparison was opened by its link alone:
   * there is none to go back to, so it says what it leads to, which is the first page.
   */
  start: "Start a search",
  /** The way on where too few areas are chosen and a search is open: the areas of the search are there to add. */
  chooseMore: "Choose more areas",
  failedTitle: "The areas could not be compared",
} as const;

export const TRAY = {
  title: "Areas to compare",
  one: "You have chosen one area. Choose at least one more, and Burro will put them side by side.",
  full: "Four areas is the most Burro can compare.",
  go: (count: number) => `Compare ${count} areas`,
  /** The name of the cross that takes an area out of the bar. */
  remove: (area: string) => `Remove ${area}`,
  /**
   * What takes every area out of the bar at once: what is seen on it, and its whole name,
   * of which what is seen is the start.
   */
  clear: "Clear",
  clearNamed: "Clear the areas to compare",
  /**
   * How many more areas the bar has room for, beside its button. It is said while the areas
   * chosen are enough to compare and fewer than the most.
   */
  room: (left: number) => (left === 1 ? "You can add one more area." : `You can add ${left} more areas.`),
} as const;

/**
 * How much a thing counts, as a comparison says it under the name of the thing, and what
 * the line over the table says of that figure. It was built two ways, for the founder to
 * choose between.
 *
 * `weight` names the figure a weight, and the line over the table says what a weight is.
 * It is what the comparison said before: "Counts for 100 of 100" stood over "Counts for 10
 * of 100" once, and was read as shares of one hundred.
 *
 * `counts` says it as the settings and the working of a result say it, "how much it counts",
 * so that one thing has one name on every page. It is a figure "of 100" again, and the line
 * over the table has to say that the figures are no shares of a whole.
 *
 * Each line is said with a search open and with none, so it speaks of where a slider stands
 * and not of who set it.
 */
export const COUNTS_FOR = {
  weight: {
    says: (weight: number) => `Weight ${weight}`,
    means:
      "The weight of a thing says how much it counts, from 0 to 100, and is where its slider stands under Space requirements. Weights are not shares of a whole, so they do not add up to 100.",
  },
  counts: {
    says: (weight: number) => `Counts ${weight} of 100`,
    means:
      "Under the name of each thing you can see how much it counts, from 0 to 100, which is where its slider stands under Space requirements. These figures are not shares of a whole, so they do not add up to 100.",
  },
} as const;

/** The one line that chooses: `weight` or `counts`. */
export const COUNTS_SAID: keyof typeof COUNTS_FOR = "weight";

export const COMPARE_TABLE = {
  areas: "The areas compared",
  /** The vibes of each area, side by side. They come before the measured parts. */
  character: {
    title: "What each area feels like",
    caption: "Where each area sits on each vibe, in one of five bands",
    /**
     * Over the vibes, once: what a vibe is, and how a line of five steps is read. It is
     * said where a person first meets a vibe on the page.
     */
    lead: "A vibe is a way of describing what an area feels like. Each line below has five steps, which run from the least at the left to the most at the right, or from one named end to the other, and the dark step is where the area sits. Neither end is the better one, so no area comes out on top here.",
    what: "Vibe",
    /**
     * Under the name of a vibe: the two ends its bands run between, as the page of an area
     * says it. The names of the ends are the API's.
     */
    ends: (low: string, high: string) => `${FACT_COLUMNS.ends} ${low} ${FACT_COLUMNS.to} ${high}`,
    /**
     * Said once under the vibes, of each area that some of them cannot place. The name is the
     * API's, and both counts are of the marks the API sent.
     */
    unplaced: (area: string, count: number, of: number) =>
      count === of
        ? `Burro could not work out any of the vibes for ${area}.`
        : `Burro could not work out ${count} of the ${of} vibes for ${area}.`,
    /** Why, said once for all of them. */
    unplacedWhy:
      "This happens when too many of the measurements a vibe needs are missing for an area. Rather than guess, or put the area in the middle, Burro leaves it blank.",
    /**
     * In the cell of a vibe that Burro could not work out for the area, as the line under the
     * vibes says it. Why is said once, there.
     */
    notPlaced: "Not worked out",
  },
  /** The rows of journeys, where a search names places to reach. The name of a place is the API's. */
  journeys: {
    /** Under the name of the row: where the journey is to. */
    to: (place: string) => `To ${place}`,
    /**
     * Under the first row of journeys, where the average of them counts: why no cell says what
     * a journey adds to the fit. The API works out one figure for them all.
     */
    together:
      "Burro works out what the journeys add to the fit for all of them together, which is why no single journey says its own.",
    /** In the cell of an area that has no time for this journey in the data. */
    missing: "Burro has no journey time for this.",
  },
  /** The heading over the things that count, each with how each area does on it. */
  counts: "What counts",
  caption: "Each thing that counts, and how each area does on it",
  what: "What counts",
  /** How much a thing counts, under its name. `COUNTS_SAID` chooses how it is said. */
  countsFor: COUNTS_FOR[COUNTS_SAID].says,
  /** Over the table, once: what the figure under each thing is. */
  weights: COUNTS_FOR[COUNTS_SAID].means,
  /** In a cell, under how the area does: a test of the whole holds that no cell says it where nothing is added. */
  adds: (points: number) => `Adds ${points} of 100 to the fit`,
  noFigure: "Burro has no figure for this.",
  notScored: "Burro did not work this out, because the area was left out before its fit was worked out.",
  /** Beside an area that has a figure for part of what counts. It says nothing of a search: none may be open. */
  basedOn: (present: number, counted: number) => `It has a figure for ${present} of the ${counted} things that count`,
  /**
   * Over what counts, once, where an area has such a fit: what follows from it. At the
   * head of every such area it ran to seven lines, and stood the vibes lower.
   */
  restsOnPart:
    "Where an area has a figure for only some of the things that count, its fit is based on those alone. This means that each of them adds a larger share of its fit than it would otherwise.",
  /** Where an area stands in the search that is open. The fit is left out when nothing is set to rank by. */
  standing: (rank: number, fit: number | null) =>
    fit === null
      ? `In your search this area is rank ${rank}.`
      : `In your search this area is rank ${rank}, with a fit of ${fit} of 100.`,
  open: (area: string) => `Open the page for ${area}`,
  /** What is seen on the way that takes an area out of a comparison, and its whole name. */
  takeOutShort: "Take out",
  takeOut: (area: string) => `Take out ${area}, and compare the others`,
} as const;

/**
 * Whether an area is ranked, and why where it is not. The reasons are the ones the list of
 * results gives. Each is said of one area, at its head, so each is a sentence. It is said
 * with a search open and with none, so none speaks of "your search".
 */
export const COMPARE_STATUS: Readonly<Record<CompareStatus, string>> = {
  ranked: "Burro has ranked this area.",
  excluded: "This area was left out, because you hid it.",
  not_selected: "This area was left out, because it is not one of the areas you chose.",
  over_budget: "This area was left out, because it is over your budget, which is a firm limit.",
  commute_cap: "This area was left out, because a journey from it is longer than a firm limit.",
  // What is said wherever an estimate is shown follows it, in the words it is said in there.
  commute_likely_beyond: `This area was left out, because a journey from it is likely beyond a firm limit. ${JOURNEYS.estimatedFrom}`,
  not_rankable: "Burro does not rank this area.",
  insufficient_data: "Burro could not rank this area, because it has too few figures for what counts.",
  // A default counts as character too, so the words say what counts and not what was asked for.
  character_unknown:
    "Burro could not rank this area, because it knows too little of the character that counts.",
};

/** The words for a status. A status the website has no words for is said in none. */
export function statusWords(status: string): string | null {
  const known: Readonly<Record<string, string | undefined>> = COMPARE_STATUS;
  return known[status] ?? null;
}
