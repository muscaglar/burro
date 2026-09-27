"use client";

/**
 * Which groups of the settings a person opened, and which they closed. A group a person
 * closed stays closed, and one they opened stays open, until they start again. What a
 * vibe is made of opens under the vibe, and is kept as a group is.
 *
 * It is kept in memory, by the session the page stands in, so that it is there again when
 * the settings are: they are taken off the page while the fold that holds them is closed,
 * and they stand in one place before a search and in another after it. It holds the keys
 * of groups and whether each is open, and nothing a person typed. Nothing here touches
 * browser storage, an address or the console. When the page is closed it is gone.
 *
 * Where the settings stand in no session, as a part shown on its own does, they keep it
 * themselves, for as long as they are on the page.
 */

import { useLayoutEffect, useState, useSyncExternalStore } from "react";

import { useSessionIfAny, type Session } from "@/lib/session/session";
import type { Store } from "@/lib/search/store";

import type { FoldKey } from "./groups";

/** What a person chose of each group they pressed: true where they opened it. */
export type Chosen = ReadonlyMap<FoldKey, boolean>;

const NOTHING: Chosen = new Map();

export interface Kept {
  readonly get: () => Chosen;
  /** A person opened a group, or closed it. */
  readonly choose: (key: FoldKey, open: boolean) => void;
  /**
   * Told whether a search is open, as the settings are drawn. What was chosen in a search
   * is forgotten once no search is open: the person started again.
   */
  readonly seen: (begun: boolean) => void;
  /** Hears the search itself, so that starting again is heard while the settings are off the page. */
  readonly hear: (search: Store) => void;
  readonly subscribe: (listener: () => void) => () => void;
}

/** True of a search that is open: something was read or asked for, or the areas are ranked. */
const isOpen = (search: Store) => {
  const { untouched, read, ranking } = search.getState();
  return !untouched || read !== null || ranking !== null;
};

export function createKept(): Kept {
  let chosen: Chosen = NOTHING;
  let inASearch = false;
  let heard: Store | null = null;
  const listeners = new Set<() => void>();
  const set = (next: Chosen) => {
    if (next === chosen) return;
    chosen = next;
    for (const listener of [...listeners]) listener();
  };
  const seen = (begun: boolean) => {
    if (inASearch && !begun) set(NOTHING);
    inASearch = begun;
  };
  return {
    get: () => chosen,
    choose(key, open) {
      if (chosen.get(key) === open) return;
      set(new Map(chosen).set(key, open));
    },
    seen,
    hear(search) {
      if (heard === search) return;
      heard = search;
      if (isOpen(search)) inASearch = true;
      // It is heard for as long as the search is there, which is as long as this is kept.
      search.subscribe(() => seen(isOpen(search)));
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}

/** What each session keeps. It goes with the session, which goes with the page. */
const BY_SESSION = new WeakMap<Session, Kept>();

function keptBy(session: Session): Kept {
  const held = BY_SESSION.get(session) ?? createKept();
  BY_SESSION.set(session, held);
  return held;
}

/**
 * What a person chose of the groups, and the way to choose. It is told whether a search
 * is open, and forgets what was chosen once one that was open is open no longer.
 */
export function useChosen(begun: boolean): readonly [Chosen, (key: FoldKey, open: boolean) => void] {
  const session = useSessionIfAny();
  const [own] = useState(createKept);
  const kept = session === null ? own : keptBy(session);
  const chosen = useSyncExternalStore(kept.subscribe, kept.get, () => NOTHING);

  // Before the page is drawn, so that what was forgotten is never seen. Where the session
  // holds the search, the search itself says whether it is open: it is heard while the
  // settings are off the page, and what the settings are handed is not asked as well.
  useLayoutEffect(() => {
    const search = session?.search()?.store ?? null;
    if (search === null) kept.seen(begun);
    else kept.hear(search);
  }, [kept, session, begun]);

  return [chosen, kept.choose];
}
