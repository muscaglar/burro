/**
 * That a search which was kept was opened by a press, on the page of an account, and that
 * the press led to the search page.
 *
 * What was pressed went with the page it stood on. So the search page hands the focus to
 * what the search holds, which is what the press changed, as it does where a shared link
 * is opened by a press: the focus is never left on nothing.
 *
 * It is one mark in memory, which holds nothing of a search or of a person. It is taken
 * back the moment it is read, and is good for as long as a page may take to come: a press
 * that led nowhere moves no focus when the search page is opened later, another way.
 */

/** How long after the press the page it leads to may still come, in milliseconds. */
export const GOOD_FOR_MS = 10_000;

/** When a kept search was last opened, by the clock of the page. `null` where none was, or it was read since. */
let opened: number | null = null;

/** Notes that a search which was kept was opened by a press, in this tab. */
export function noteOpened(): void {
  opened = performance.now();
}

/** True once, where a kept search was opened since this was last asked, and not long ago. */
export function wasOpened(): boolean {
  const at = opened;
  opened = null;
  return at !== null && performance.now() - at <= GOOD_FOR_MS;
}
