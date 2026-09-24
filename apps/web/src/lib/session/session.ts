"use client";

/**
 * What is kept while the website is open in one tab: the search that is
 * open, the areas chosen to compare, and the link that was last made of a
 * search. docs/design/web.md, section 10.
 *
 * It is a plain object in memory, handed down through React. It lives as
 * long as the page does: following a link inside the website keeps it, and
 * loading a page afresh or closing the tab loses it. Nothing here touches
 * browser storage, an address or the console.
 */

import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";

import type { ShareCreated } from "@/lib/api/schema";
import { isChosen, isEnough, isFull, toggled, type Chosen } from "@/lib/compare/list";
import type { Held } from "@/lib/search/store";

type Listener = () => void;

export interface CompareList {
  readonly get: () => readonly Chosen[];
  readonly toggle: (area: Chosen) => void;
  /** Puts these areas in place of what was chosen, as opening a comparison does. */
  readonly set: (areas: readonly Chosen[]) => void;
  readonly clear: () => void;
  readonly subscribe: (listener: Listener) => () => void;
}

/**
 * A link that was made: the search it was made of, what was asked of it, and what the API
 * answered. It is kept apart from the search, which making a link leaves as it was.
 */
export interface MadeShare {
  /** The hash of the spec the link was made of. A link is shown only for the search it was made of. */
  readonly of: string | null;
  /** True when the person asked for the exact places to be shared. */
  readonly exact: boolean;
  readonly share: ShareCreated;
}

export interface MadeLink {
  readonly get: () => MadeShare | null;
  readonly set: (made: MadeShare | null) => void;
  readonly subscribe: (listener: Listener) => () => void;
}

export interface Session {
  /** The search that is open, or `null` when none has been opened since the page was loaded. */
  readonly search: () => Held | null;
  /** The search that is open. If none is, the one that `make` makes is opened and kept. */
  readonly searchOr: (make: () => Held) => Held;
  readonly compare: CompareList;
  /** The link the person last made, so that it is still there when they come back to the search. */
  readonly link: MadeLink;
}

function createMadeLink(): MadeLink {
  let made: MadeShare | null = null;
  const listeners = new Set<Listener>();
  return {
    get: () => made,
    set(next) {
      if (next === made) return;
      made = next;
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

function createCompareList(): CompareList {
  let list: readonly Chosen[] = [];
  const listeners = new Set<Listener>();
  const set = (next: readonly Chosen[]) => {
    if (next === list) return;
    list = next;
    for (const listener of [...listeners]) listener();
  };
  return {
    get: () => list,
    toggle: (area) => set(toggled(list, area)),
    set(areas) {
      const next = areas.reduce<readonly Chosen[]>((held, area) => (isChosen(held, area.area_id) ? held : toggled(held, area)), []);
      const same = next.length === list.length && next.every((area, at) => area.area_id === list[at]?.area_id);
      set(same ? list : next);
    },
    clear: () => set(list.length === 0 ? list : []),
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}

export function createSession(): Session {
  let open: Held | null = null;
  return {
    search: () => open,
    searchOr(make) {
      open ??= make();
      return open;
    },
    compare: createCompareList(),
    link: createMadeLink(),
  };
}

const SessionContext = createContext<Session | null>(null);

/** Holds one session for everything inside it. The shell of every page holds one. */
export function SessionProvider({ children }: { readonly children: ReactNode }) {
  // Made once. It outlives any one page, and no longer than the tab.
  const [session] = useState(createSession);
  return createElement(SessionContext.Provider, { value: session }, children);
}

/**
 * Hands down the session it is inside. Where it is inside none, as a part
 * shown on its own is, it holds one of its own.
 */
export function SessionBoundary({ children }: { readonly children: ReactNode }) {
  const outer = useContext(SessionContext);
  const [own] = useState(() => outer ?? createSession());
  return createElement(SessionContext.Provider, { value: outer ?? own }, children);
}

/** The session, or `null` where there is none. */
export function useSessionIfAny(): Session | null {
  return useContext(SessionContext);
}

const NONE: readonly Chosen[] = [];
const NOTHING_TO_HEAR = () => () => undefined;

export interface Comparing {
  /** The areas chosen, in the order they were chosen. */
  readonly chosen: readonly Chosen[];
  /** True when no more can be added. */
  readonly full: boolean;
  /** True when there are enough to compare. */
  readonly enough: boolean;
  readonly has: (areaId: string) => boolean;
  /** Takes the area out if it is in, and puts it in if it is not and there is room. */
  readonly toggle: (area: Chosen) => void;
  /** Puts these areas in place of what was chosen. */
  readonly set: (areas: readonly Chosen[]) => void;
  readonly clear: () => void;
}

const NO_LINK = () => null;

/** The link the person last made, and the way to keep one. Outside a session there is none, and none is kept. */
export function useMadeLink(): readonly [MadeShare | null, (made: MadeShare | null) => void] {
  const link = useContext(SessionContext)?.link ?? null;
  const made = useSyncExternalStore(link?.subscribe ?? NOTHING_TO_HEAR, link?.get ?? NO_LINK, NO_LINK);
  const keep = useCallback((next: MadeShare | null) => link?.set(next), [link]);
  return [made, keep];
}

/** The areas chosen to compare, and what can be done to them. */
export function useCompare(): Comparing {
  const session = useContext(SessionContext);
  const list = session?.compare ?? null;
  const chosen = useSyncExternalStore(
    list?.subscribe ?? NOTHING_TO_HEAR,
    list?.get ?? (() => NONE),
    // A page is built with nothing chosen. What was chosen is drawn once the page is in the browser.
    () => NONE,
  );
  const toggle = useCallback((area: Chosen) => list?.toggle(area), [list]);
  const set = useCallback((areas: readonly Chosen[]) => list?.set(areas), [list]);
  const clear = useCallback(() => list?.clear(), [list]);
  return useMemo(
    () => ({
      chosen,
      full: isFull(chosen),
      enough: isEnough(chosen),
      has: (areaId: string) => isChosen(chosen, areaId),
      toggle,
      set,
      clear,
    }),
    [chosen, toggle, set, clear],
  );
}
