/**
 * Which areas have their page built ahead of time.
 *
 * A build asks the API for every area it builds a page for. London has a
 * thousand, and a build that asked for each of them left a small machine so
 * far behind that it stopped answering, and the build failed with it. So a
 * build makes the first few pages, and the page of any other area is made the
 * first time it is asked for, and kept for as long as a built page is kept.
 */

/** How many pages of areas a build makes. The made-up city has as many areas, so all of its are built. */
export const AREAS_BUILT_AHEAD = 24;

/** The areas whose page a build makes: the first of the release, in the order the API gives them. */
export function builtAhead<Area>(areas: readonly Area[]): readonly Area[] {
  return areas.slice(0, AREAS_BUILT_AHEAD);
}
