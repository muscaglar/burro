/**
 * Site copy for the towns that stand together: beside the names of a list of results, at
 * the heads of the areas of a comparison, and in the bar of areas to compare.
 *
 * What a town is, and that it is no picture of the place, is said where one town stands,
 * at the head of the page of an area, and in the key to the drawings: `TOWN.line`, in
 * `town.ts`, and the key's own. Where towns stand together it is said nowhere. The founder,
 * who had walked the website twice, asked for that line to go from the results, and it
 * went from the bar of areas and from the head of a comparison with it.
 *
 * It was said once there, of every one of the towns: under every one of ten it would be
 * the same words ten times. The words are kept for the line of the look that puts them
 * back: `LINE_STANDS` of a list of results, `BAR_SAYS_OF_ITS_TOWNS` of the bar, and
 * `HEADS_SAY_OF_THEIR_TOWNS` of a comparison.
 *
 * No word here names a vibe or a place, and none says anything of a place.
 */

export const TOWNS = {
  /** Once, in sight, where the look has it said of towns that stand together: what each of them is, and is not. */
  line: "Each little town is a drawing based on four of the area's vibes. This means it shows the character of the area, and is not a picture of what the place looks like.",
  /**
   * The same in fewer words, for a place with little room, as the bar of areas to compare
   * is, which lies over the page. It says both things the line says: what a town is drawn
   * from, and that it is no picture of the place.
   */
  short: "Each little town is a drawing based on four of the area's vibes, and not a picture of the place.",
} as const;
