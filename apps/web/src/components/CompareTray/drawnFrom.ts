"use client";

/**
 * What the towns of the bar are drawn from, kept while the tab is open.
 *
 * The bar stands at the foot of every page that fills it, and the page hands it nothing.
 * What draws a button that fills it holds what a town is drawn from: so it hands that
 * over here, and the bar reads it from here. It is where areas sit on the vibes of the
 * release, which is of the release and of no search, and nothing a person typed.
 *
 * It is kept with the session, in memory, and goes when the session goes: it touches no
 * storage, no address and no console. It is written when a part is drawn in the browser,
 * and never while a page is built, so that nothing is kept between one person and the next.
 */

import { useCallback, useSyncExternalStore } from "react";

import { useSessionIfAny, type Session } from "@/lib/session/session";

import type { Handed } from "./town";

type Listener = () => void;

interface Kept {
  readonly get: () => Handed | null;
  readonly hand: (more: Handed) => void;
  readonly subscribe: (listener: Listener) => () => void;
}

/** True where two lists hold the same things in the same order. */
const alike = (one: readonly unknown[], other: readonly unknown[]) =>
  one.length === other.length && one.every((held, at) => Object.is(held, other[at]));

/** True where a mark says of an area what another says. */
function says(one: Handed["marks"][string], other: Handed["marks"][string] | undefined): boolean {
  if (other === undefined || one.length !== other.length) return false;
  return one.every((mark, at) => {
    const beside = other[at];
    return (
      beside !== undefined &&
      mark.tag_id === beside.tag_id &&
      mark.band === beside.band &&
      mark.spread_low === beside.spread_low &&
      mark.spread_high === beside.spread_high
    );
  });
}

function createKept(): Kept {
  let held: Handed | null = null;
  const listeners = new Set<Listener>();
  return {
    get: () => held,
    hand(more) {
      const before = held;
      // What is handed of an area stands until the same is handed again: a page of another
      // area, or a list that does not hold it, takes nothing of it away.
      const marks = { ...(before?.marks ?? {}) };
      let moved = before === null;
      for (const [areaId, mark] of Object.entries(more.marks)) {
        if (says(mark, marks[areaId])) continue;
        marks[areaId] = mark;
        moved = true;
      }
      const bands = more.bands ?? before?.bands;
      if (bands !== before?.bands) moved = true;
      // A release is what a town reads of route 11. Handed again as it was, nothing has moved.
      const release =
        before !== null &&
        alike(before.release.tags, more.release.tags) &&
        alike(before.release.features, more.release.features)
          ? before.release
          : more.release;
      if (release !== before?.release) moved = true;
      if (!moved) return;
      held = { release, bands, marks };
      for (const listener of [...listeners]) listener();
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}

/** What each session keeps. It goes with its session, and is reached through no other. */
const bySession = new WeakMap<Session, Kept>();

function keptBy(session: Session | null): Kept | null {
  if (session === null) return null;
  const known = bySession.get(session);
  if (known !== undefined) return known;
  const made = createKept();
  bySession.set(session, made);
  return made;
}

const NOTHING = () => null;
const NOTHING_TO_HEAR = () => () => undefined;

/** What the towns of the bar are drawn from. `null` until something is handed over, and where there is no session. */
export function useDrawnFrom(): Handed | null {
  const kept = keptBy(useSessionIfAny());
  // A page is built with nothing handed over. What was handed is read once the page is in the browser.
  return useSyncExternalStore(kept?.subscribe ?? NOTHING_TO_HEAR, kept?.get ?? NOTHING, NOTHING);
}

/**
 * The way to hand over what a town is drawn from. It is called once a part is drawn in
 * the browser, from an effect, and never while a part is drawn.
 */
export function useHandOver(): (more: Handed) => void {
  const kept = keptBy(useSessionIfAny());
  return useCallback((more: Handed) => kept?.hand(more), [kept]);
}
