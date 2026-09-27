/**
 * The way from a search that came from a link to a search of one's own.
 *
 * The search that is open is kept while the website is open, so that it is still there when
 * a person comes back to the search page. So the way to a search of one's own led to the
 * shared search once more. And begun again on the page a link opens, the search is opened
 * again as the link holds it. So that the way is taken is noted here as it is pressed, and
 * the search is begun again as the page a link opens is left: the search page then opens
 * as it first stands.
 *
 * It is one mark in memory, which holds nothing of a search, a place or a person. It is
 * taken back the moment it is read, and is good for as long as a page may take to come:
 * a press that led nowhere begins nothing again when the page is left later, another way.
 */

/** How long after the press the page it leads to may still come, in milliseconds. */
export const GOOD_FOR_MS = 10_000;

/** When the way was last pressed, by the clock of the page. `null` where it was not, or was read since. */
let taken: number | null = null;

/** Notes that the way to a search of one's own was pressed, in this tab. */
export function takeTheWay(): void {
  taken = performance.now();
}

/** True once, where the way was pressed since this was last asked, and not long ago. */
export function wasTaken(): boolean {
  const at = taken;
  taken = null;
  return at !== null && performance.now() - at <= GOOD_FOR_MS;
}
