"use client";

import { useLayoutEffect, useState, type RefObject } from "react";

import { screenSaidBy, type Screen } from "./order";

/** The word of the style sheet that says which screen there is. */
const SAID_IN = "--screen";

/**
 * Which screen there is, as the style sheet of the page says it of the page. It is `null`
 * while the page is built, and until the sheet has been asked, which is before the page is
 * first drawn in a browser. It is asked again when the window changes size, as when a
 * phone is turned on its side or a desk is zoomed.
 */
export function useScreen(page: RefObject<HTMLElement | null>): Screen | null {
  const [screen, setScreen] = useState<Screen | null>(null);
  useLayoutEffect(() => {
    const ask = () => {
      if (page.current !== null) setScreen(screenSaidBy(getComputedStyle(page.current).getPropertyValue(SAID_IN)));
    };
    ask();
    window.addEventListener("resize", ask);
    return () => window.removeEventListener("resize", ask);
  }, [page]);
  return screen;
}

/**
 * Keeps the focus where it was when a part of the page is put elsewhere in it. A browser
 * takes the focus from what is taken out of the page, though it is put back at once: so
 * what had the focus as the order changed is given it again, where it has gone to nothing.
 * The page is not moved for it. `order` is whatever says the order of the page.
 *
 * Where the focus is, is asked of the page as it is drawn, and kept nowhere: what had the
 * focus some time before is not given it again, and what went with a press stays gone.
 */
export function useFocusKept(page: RefObject<HTMLElement | null>, order: string): void {
  const on = typeof document === "undefined" ? null : document.activeElement;
  useLayoutEffect(() => {
    if (!(on instanceof HTMLElement) || on === document.body || !on.isConnected) return;
    if (page.current?.contains(on) !== true) return;
    const now = document.activeElement;
    if (now === null || now === document.body) on.focus({ preventScroll: true });
    // It is for the drawing in which the order changed, and for what had the focus then.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [order]);
}
