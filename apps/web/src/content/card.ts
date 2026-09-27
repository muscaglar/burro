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
   * The name of the list of what was asked for and has no figure, to whoever hears the
   * page. The name of the area is the API's.
   */
  lacked: (area: string) => `What you asked for that Burro has no figure for in ${area}`,
  /** In the working, over the figures behind each gauge of the result, each with its source. */
  vibes: "The figures behind each vibe",
  /**
   * In the working, under the figures behind each vibe, where the search page does not hold
   * the source of every one of them: the whole of a link, which leads to the page of the
   * area, where each figure stands with its source and its date. The name of the area is
   * the API's.
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
