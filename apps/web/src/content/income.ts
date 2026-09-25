/**
 * Site copy for the household income of an area's page: the names of its
 * controls and its states, and nothing else.
 *
 * Every word about the figure is the API's: the heading, the name of the kind
 * of income, the figure and its limits, the year, and the publisher's own
 * caveats. Nothing here says what the figure means, and no word here is one
 * Burro would be choosing of it. A test reads this file for such words.
 */

export const INCOME = {
  /** While the figure is asked for. */
  loading: "Loading the figure.",
  /** Where the figure could not be read. What went wrong is said in the API's words above it. */
  failed: "The figure could not be loaded.",
  again: "Try again",
  /** With scripts off: the figure is not in the page, so that nothing keeps it. */
  noScript: "The figure is loaded when you ask for it, which needs scripts to be on.",
  notes: "About this figure",
} as const;
