/**
 * Site copy for the answer as the look draws it: what names a part of a result that the
 * look added. Every other word of a result is in `search.ts`, and every word about a
 * place is the API's.
 *
 * Nothing here says anything of a place. The name of an area is handed in, as the API
 * gives it.
 */

export const CARD = {
  /**
   * At the head of the box that "Show the working" opens under a result: whose working
   * it is. A page may hold the working of several results, each a long way down.
   */
  workingOf: (area: string) => `The working for ${area}`,
  /**
   * On the line of a budget: what a home of the kind that is looked for costs in the area.
   * The amount is the API's, and a rent is by the month.
   */
  cost: (pounds: string, rented: boolean) => (rented ? `£${pounds} a month` : `£${pounds}`),
  /**
   * After the figure of a journey or of a budget: on which side of what the person set the
   * figure falls. It is one word, and the working says it of every journey in the same two.
   */
  side: { within: "within", over: "over" },
  /**
   * On the press that stands under the first lines of a narrow result which holds more of
   * them than it has room for: how many more there are, and what puts them away again.
   */
  more: (count: number) => `+${count} more`,
  fewer: "Show fewer",
  /**
   * The whole name of that press, of which what is seen is the start: whose lines they
   * are, as every short button of a result says it. The name of the area is the API's.
   */
  moreOf: (seen: string, area: string) => `${seen}: ${area}`,
  /**
   * Under the fit of a result whose area has no figure for a thing that was asked for. Such
   * an area stands below every area that has one, so a higher fit may stand under a lower:
   * the line of the thing says "no data", and this says what follows from it.
   */
  listedLower: "This area is listed lower because it has no data for something you asked for.",
  /** In the working, over the figures behind each gauge of the result, each with its source. */
  vibes: "The figures behind each gauge",
  /**
   * In the working, under the figures behind each gauge, where the search page does not hold
   * the source of every figure the result shows: the whole of a link, which leads to the
   * page of the area, where each figure stands with its source and its date. The name of
   * the area is the API's.
   */
  sourcesOn: (area: string) => `See the source and the date of each figure on the page for ${area}`,
  /**
   * In the working, over what the trade-off of the result is about, with the key of its
   * source. The sentence of the trade-off stands on the result, under "Trade-off", and is
   * said once.
   */
  sourceOfTheTradeOff: "The source of the trade-off",
  /**
   * In the working, where a fit is not whole: the area has no cost figure, so the budget
   * counts for nothing in its fit. It is said of a budget that is a guide. Of a firm one the
   * line that says the limit could not be checked says all of it. It is said as a journey
   * with no time is, and is one sentence.
   */
  noCost: "Your budget does not count towards this fit, because Burro has no cost figure for this area.",
  /** Under "Trade-off" on a result, where what Burro wrote of the result could not be loaded. */
  tradeOffFailed: "Burro could not load the trade-off for this area this time.",
  /**
   * Under "Show on the map", once it is pressed: what the press did. It is said to whoever
   * cannot see the map too, and the box it names is what the press leads to.
   */
  shownOnMap: (area: string) => `${area} is now marked on the map, and the box under the map says more about it.`,
  /** The same, where the page draws no map: as in a browser that cannot draw one. */
  notOnMap: (area: string) => `Burro could not show ${area} on the map, because the map is not drawn on this page.`,
} as const;
