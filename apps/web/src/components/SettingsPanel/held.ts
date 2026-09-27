"use client";

/**
 * What is pressed in the settings is held where it stands.
 *
 * A setting that is changed is answered, and the answer changes what stands over the
 * setting: the bar of its group comes to name it, on a line more where the bar is narrow,
 * and once a search is open the results over the settings are ranked again. All that
 * stands under what changed goes up or down the page by as much, what was pressed among
 * it. Measured in a browser at 390 by 844: a thing was turned on, and its switch went
 * 21.5 px down from under the press. "Visiting" did the same as it was chosen.
 *
 * A browser holds a page where a person reads while something grows over it, but by the
 * first thing in sight and not by what was pressed, and not every browser does. So the
 * settings hold what was pressed themselves. Where it stood in the window is kept as the
 * press lands. As the page is drawn again, and before it is seen, the page goes by as much
 * as what was pressed went: it stands where it stood, and so does all that stands under it.
 *
 * It is held from a press that changes the search until the answer to it is drawn, and no
 * longer: what changes the page after that is not of the press, and a person may be
 * reading elsewhere. A press that changes nothing of the search holds nothing. Where a
 * person scrolls before the answer comes, the page goes where they take it, and what was
 * pressed is held where that leaves it.
 *
 * WHERE NO ANSWER COMES IT IS LET GO AS THE ASKING ENDS. A ranking that fails leaves the
 * count of answers where it was, and what was pressed was held for as long as the page
 * stayed open: seen in a browser, with the pointer over a result, the wheel could not take
 * the page on, since every drawing of the page took it back to the setting.
 *
 * AS A SEARCH OPENS OF THE PRESS, THE PAGE HOLDS WHAT WAS PRESSED, AND THIS ASKS NOTHING.
 * Where the look has a setting make the search, the heading and the tabs over the settings
 * go as it opens, and the page goes by as much, or brings the answer into sight instead:
 * which of the two is the page's to choose. Asked of both, the page went twice. Before a
 * search nobody knows whether one opens of a press until the answer to it comes, so
 * nothing is asked until then, and then only where none has opened: what was chosen was
 * gathered, and the button under the settings makes the search.
 *
 * Nothing is kept of what was pressed but the element and a figure, for as long as the
 * answer is on its way.
 */

import { useEffect, useLayoutEffect, useRef, type SyntheticEvent } from "react";

/** Less than this is how a browser rounds where a thing stands, and is not seen. */
export const SEEN = 0.5;

/** What is in a person's hand, and where it stood in the window when it was last known. */
interface InHand {
  readonly part: Element;
  top: number;
  /** The count of answers when it changed the search. `null` until it has. */
  sent: number | null;
  /** Whether a search was open as it was pressed. */
  readonly begun: boolean;
  /** Whether the search has been seen to work out what it changed. */
  asked: boolean;
}

export interface Held {
  /** Heard of every press and every key in the settings, on its way to what it was made on. */
  readonly took: (event: SyntheticEvent) => void;
  /** Told that a control of the settings changed the search: what was pressed is held until it is answered. */
  readonly sent: () => void;
}

const topOf = (part: Element) => part.getBoundingClientRect().top;

/**
 * Holds what was pressed where it stands. It is told the count of answers, whether a
 * search is open, and whether the search is being worked out, as the settings are drawn.
 */
export function useHeldInPlace(version: number, begun: boolean, busy = false): Held {
  const hand = useRef<InHand | null>(null);
  const drawn = useRef({ version, begun });

  useEffect(() => {
    drawn.current = { version, begun };
  });

  // The page goes where a person takes it: what was pressed is held where that leaves it.
  useEffect(() => {
    const scrolled = () => {
      const held = hand.current;
      if (held !== null && held.part.isConnected) held.top = topOf(held.part);
    };
    window.addEventListener("scroll", scrolled, { passive: true });
    return () => window.removeEventListener("scroll", scrolled);
  }, []);

  // Before the page is drawn, so that what was pressed is never seen anywhere but where it stood.
  useLayoutEffect(() => {
    const held = hand.current;
    if (held === null || held.sent === null) return;
    if (!held.part.isConnected) {
      // It went from the page with its press, and what takes its place is handed the focus.
      hand.current = null;
      return;
    }
    const answered = held.sent !== version;
    // A search opened of the press: the page holds what was pressed, or brings the answer into sight.
    const opened = begun && !held.begun;
    if (opened) {
      hand.current = null;
      return;
    }
    // Before a search nobody knows whether one opens of the press, until the answer comes.
    if (held.begun || answered) {
      const by = topOf(held.part) - held.top;
      // At once, whatever the page says of how it scrolls: a page that glided back would be seen to go and to come.
      if (Math.abs(by) >= SEEN) window.scrollBy({ top: by, left: 0, behavior: "instant" });
    }
    // The answer to the press is drawn: it is let go. So it is where the asking has ended
    // and no answer came of it, which leaves the count of answers where it was.
    if (busy) held.asked = true;
    if (answered || (held.asked && !busy)) hand.current = null;
  });

  return {
    took(event) {
      const on = event.target;
      hand.current =
        on instanceof Element ? { part: on, top: topOf(on), sent: null, begun: drawn.current.begun, asked: false } : null;
    },
    sent() {
      if (hand.current !== null) hand.current.sent = drawn.current.version;
    },
  };
}
