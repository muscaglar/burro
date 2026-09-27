/**
 * Site copy for what the page says while a search is open and holds no ranking: that a
 * first ranking is being worked out, where a control asked for it and no sentence is read,
 * and that nothing is ranked yet.
 *
 * It names states of the search. It says nothing of a place.
 */

export const WAIT = {
  /**
   * While a first ranking that a control asked for is on its way. The line under the box
   * says it, and it stands under Burro where the results will be. Nothing is read there, so
   * it does not say that a search is.
   */
  ranking: "Working out the ranking",
  /**
   * A search is open, and nothing is ranked: nothing was read, or what Burro noticed is
   * not applied until it is chosen, or the ranking did not come. The line under the box
   * says it, where it said nothing and kept the room of a line.
   */
  notYet: "Burro has not ranked any areas yet.",
} as const;
