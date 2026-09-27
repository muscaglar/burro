"use client";

import { useLayoutEffect, useRef, useState, type RefObject } from "react";

import {
  bringIntoSight,
  bringWholeIntoSight,
  keepInPlace,
  sideWithRoom,
  WHAT_A_PRESS_OPENS,
  type Opens,
  type Side,
} from "@/lib/sight";

/** A press that opens or closes something: what was pressed, where its line stood, whether a hand pressed it, and when. */
interface Press {
  readonly on: HTMLElement;
  readonly top: number;
  readonly bottom: number;
  readonly byHand: boolean;
  readonly at: number;
}

/**
 * For how long a press is taken to be what opened or closed something, in milliseconds.
 * What opens or closes later than that was opened or closed by the page, and the line may
 * stand elsewhere by then.
 */
const A_PRESS_AGO = 1000;

export interface Where {
  /** The side of the line that what is open stands on. The part draws it there, in the order of the page. */
  readonly side: Side;
  /**
   * Told of a press that opens or closes something, before it does: what was pressed, and
   * whether a hand pressed it. A press by the keys is counted as none by a browser.
   */
  readonly pressed: (on: HTMLElement, byHand: boolean) => void;
}

/**
 * Where what a press opens stands, for a part that opens something in place: a line
 * that holds what is pressed, and one thing open at a time.
 *
 * What a hand opens stands where the whole of it has room, under the line or over it, and
 * the line stays where it was pressed: what is put over the line, or taken from over it,
 * moves the page by as much, before anything is drawn. Where it has room neither way it
 * stands under, and its head is brought into sight. What the keys open stands under, and
 * the whole of it is brought into sight. What the page opens of itself stands under, and
 * nothing is moved for it.
 *
 * `line` is what holds what is pressed, `opened` the id of what is open, and `open` says
 * which thing that is, or `null` while nothing is.
 */
export function useWhereItOpens(
  line: RefObject<HTMLElement | null>,
  opened: string,
  open: string | null,
  opens: Opens = WHAT_A_PRESS_OPENS,
): Where {
  const [side, setSide] = useState<Side>("under");
  const press = useRef<Press | null>(null);

  // Before the page is drawn, so that what was opened is first seen where it will stand.
  // What is open is measured where it was drawn, which is the one way to know how high it
  // is: where the other side is the one with room, it is drawn there before anything is seen.
  useLayoutEffect(() => {
    const place = () => {
      const held = line.current;
      const made = press.current !== null && performance.now() - press.current.at < A_PRESS_AGO ? press.current : null;
      // Nobody pressed: the page drew it, under the line, and nothing is moved.
      if (made === null || held === null) {
        press.current = null;
        return setSide("under");
      }
      const panel = open === null ? null : held.ownerDocument.getElementById(opened);
      const free = opens === "room" && made.byHand && panel !== null;
      const wanted = free ? sideWithRoom(made, held, panel, side) : "under";
      // It is drawn on the other side first, and this is done again once it is.
      if (wanted !== side) return setSide(wanted);
      press.current = null;
      keepInPlace(held, made.top);
      if (panel === null || side === "over") return;
      if (made.byHand || opens === "under") bringIntoSight(panel, made.on);
      else bringWholeIntoSight(panel, made.on);
    };
    place();
  }, [line, opened, open, opens, side]);

  return {
    side,
    pressed(on, byHand) {
      const at = line.current?.getBoundingClientRect();
      press.current = at === undefined ? null : { on, top: at.top, bottom: at.bottom, byHand, at: performance.now() };
    },
  };
}
