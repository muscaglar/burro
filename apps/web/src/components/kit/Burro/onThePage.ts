/**
 * Whether the page itself draws Burro: beside its heading, or where he
 * hops. He is one rabbit, and what every page stands in draws him only where the page
 * does not.
 *
 * A style sheet says so first, for a page that has not yet run and for one that never
 * runs. This is the second hand: once the page runs, every drawing of him on the page
 * says here that it is drawn, and what every page stands in holds him only while none is.
 *
 * It is held in memory, and nowhere else.
 */

import { useSyncExternalStore } from "react";

let drawn = 0;
const told = new Set<() => void>();

function count(by: 1 | -1): void {
  drawn += by;
  for (const tell of told) tell();
}

/**
 * Whether a browser lays it out. One that is held by the page and drawn nowhere, as where
 * a style sheet draws the other of two, is laid out nowhere. Where nothing at all is laid
 * out, as in a test that reads no style sheet, it is taken to be drawn.
 */
function isLaidOut(he: Element): boolean {
  if (document.documentElement.getClientRects().length === 0) return true;
  return he.getClientRects().length > 0;
}

/**
 * Watches a drawing of him on the page, from when it is in the page until what is handed
 * back is called. It counts while a browser draws it, and is asked again whenever its box
 * changes: as when the window is made wider, and the other of two is drawn.
 */
export function watch(he: Element | null): () => void {
  if (he === null) return () => undefined;
  let counted = false;
  const look = () => {
    const now = isLaidOut(he);
    if (now === counted) return;
    counted = now;
    count(now ? 1 : -1);
  };
  look();
  const watcher = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(look);
  watcher?.observe(he);
  return () => {
    watcher?.disconnect();
    if (counted) count(-1);
    counted = false;
  };
}

function listen(tell: () => void): () => void {
  told.add(tell);
  return () => {
    told.delete(tell);
  };
}

const isOnThePage = () => drawn > 0;
/** A page is drawn on the server before any of it has run: nothing has said that it draws him. */
const asBuilt = () => false;

/** True while the page itself draws him. */
export function useOnThePage(): boolean {
  return useSyncExternalStore(listen, isOnThePage, asBuilt);
}
