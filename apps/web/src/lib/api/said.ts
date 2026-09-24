/**
 * What the answers of the API have said of their data, since the page was opened.
 *
 * A page is built on one release and may be read while the API serves another.
 * Each answer says whether its data is made up and whether its release is a
 * preview. Every answer is heard here, so that a page can tell when the
 * service answers with another kind of data than the page was built on: a
 * figure is never to be read under a notice that is not true of it.
 *
 * It is held in memory. Nothing heard is forgotten while the tab is open.
 */

type Listener = () => void;

/** What one answer says of itself. `null` where it does not say. */
export interface Said {
  readonly synthetic: boolean | null;
  readonly preview: boolean | null;
}

/** What has been said by any answer so far. */
export interface Heard {
  /** Some answer said its data is made up. */
  readonly madeUp: boolean;
  /** Some answer said its data is not made up. */
  readonly real: boolean;
  /** Some answer said its release is a preview. */
  readonly preview: boolean;
  /** Some answer said its release is not a preview. */
  readonly finished: boolean;
}

export const NOTHING_SAID: Heard = { madeUp: false, real: false, preview: false, finished: false };

let heard: Heard = NOTHING_SAID;
const listeners = new Set<Listener>();

export function noteSaid(said: Said): void {
  const next: Heard = {
    madeUp: heard.madeUp || said.synthetic === true,
    real: heard.real || said.synthetic === false,
    preview: heard.preview || said.preview === true,
    finished: heard.finished || said.preview === false,
  };
  const same =
    next.madeUp === heard.madeUp &&
    next.real === heard.real &&
    next.preview === heard.preview &&
    next.finished === heard.finished;
  if (same) return;
  heard = next;
  for (const listener of listeners) listener();
}

export function whatWasSaid(): Heard {
  return heard;
}

export function subscribeToWhatWasSaid(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/**
 * Whether any answer is of another kind of data than the page was built on:
 * made up where the page is real, real where the page is made up, a preview
 * where the page is finished, or finished where the page is a preview.
 */
export function disagrees(
  built: { readonly synthetic: boolean; readonly preview: boolean },
  said: Heard,
): boolean {
  const kind = built.synthetic ? said.real : said.madeUp;
  const state = built.preview ? said.finished : said.preview;
  return kind || state;
}

/** For tests only: a page that has heard nothing yet. */
export function forgetWhatWasSaid(): void {
  heard = NOTHING_SAID;
}
