"use client";

/**
 * The store: one plain object in memory that holds a search, and the React
 * context that hands it to the page. No library.
 *
 * Nothing here touches browser storage, a URL or the console. When the page
 * is closed the search is gone. While it is open the search is kept by the
 * session, so that following a link to a comparison and back does not lose it.
 */

import {
  createContext,
  createElement,
  useContext,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";

import { api, type Client } from "@/lib/api/client";
import type { Handed } from "@/lib/api/handed";
import type { AreaSummary, GeometryData } from "@/lib/api/schema";
import { useSessionIfAny } from "@/lib/session/session";

import { createFlow, type Flow } from "./flow";
import { NOTHING_READ, type Change, type Mark } from "./mark";
import { initialState, readApart, reduce, type SearchEvent, type SearchState } from "./state";
import { leastWait } from "./wait";

export interface Store {
  readonly getState: () => SearchState;
  readonly dispatch: (event: SearchEvent) => void;
  readonly subscribe: (listener: () => void) => () => void;
}

/** A holder of one state. An event is applied at once, so the next read sees it. */
export function createStore(initial: SearchState): Store {
  let state = initial;
  const listeners = new Set<() => void>();
  return {
    getState: () => state,
    dispatch(event) {
      const next = reduce(state, event);
      if (next === state) return;
      state = next;
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

/** A search that is open: what it holds, and what can be done to it. */
export interface Held {
  readonly store: Store;
  readonly flow: Flow;
}

const SearchContext = createContext<Held | null>(null);

interface ProviderProps {
  readonly meta: Handed;
  readonly areas: readonly AreaSummary[];
  readonly geometry?: GeometryData | null;
  /** The API to call. A test passes its own. */
  readonly client?: Client;
  readonly children: ReactNode;
}

function open(meta: Handed, areas: readonly AreaSummary[], geometry: GeometryData | null, client: Client): Held {
  const store = createStore(initialState(meta, areas, geometry));
  // A first search waits for as long as Burro takes to be seen, which the look says.
  return { store, flow: createFlow({ client, getState: store.getState, dispatch: store.dispatch, rests: leastWait }) };
}

export function SearchProvider({ meta, areas, geometry = null, client = api, children }: ProviderProps) {
  const session = useSessionIfAny();
  // Made once. A search outlives any one drawing of the page. Inside a session it is the
  // session's, and is there again when the person comes back to the page.
  const [held] = useState<Held>(() => {
    const make = () => open(meta, areas, geometry, client);
    return session === null ? make() : session.searchOr(make);
  });
  return createElement(SearchContext.Provider, { value: held }, children);
}

function useHeld(): Held {
  const held = useContext(SearchContext);
  if (held === null) throw new Error("There is no search open here.");
  return held;
}

/** The search as it stands, and what can be done to it. */
export function useSearch(): { readonly state: SearchState; readonly flow: Flow } {
  const { store, flow } = useHeld();
  const state = useSyncExternalStore(store.subscribe, store.getState, store.getState);
  return { state, flow };
}

const NOTHING_TO_HEAR = () => () => undefined;
const NO_SEARCH = () => null;

/**
 * What the box is told of the search, and what it tells the search of itself. All of it is
 * counts: the box holds what was typed, and hands none of it over here.
 */
export interface Marks {
  /** How far into the box the search has read. What stands after it is what is sent. */
  readonly read: Mark;
  /**
   * Where the words begin that the page may ask the box for: those that were last read,
   * while the box holds them as they were sent, and else those the search has not read.
   */
  readonly from: number;
  /** True when what was added was read without the words before it, and not all of it was read. */
  readonly apart: boolean;
  /** True while a model reads what the rules left unread of the words that were sent. */
  readonly reading: boolean;
  /** Told where the box was changed, and by how much. */
  readonly edited: (change: Change) => void;
  /** Told how much the box holds as it is drawn. */
  readonly found: (holds: number) => void;
}

/** What a box is told where no search is open around it: nothing of it has been read. */
export const NO_MARKS: Marks = {
  read: NOTHING_READ,
  from: 0,
  apart: false,
  reading: false,
  edited: () => undefined,
  found: () => undefined,
};

/** What the box is told of the search that is open around it, where one is. */
export function useMarks(): Marks {
  const held = useContext(SearchContext);
  const state = useSyncExternalStore(
    held?.store.subscribe ?? NOTHING_TO_HEAR,
    held?.store.getState ?? NO_SEARCH,
    held?.store.getState ?? NO_SEARCH,
  );
  const flow = held?.flow ?? null;
  const read = state?.box.read ?? NOTHING_READ;
  const from = state === null ? 0 : (state.box.shown ?? state.box.read.to);
  const apart = state !== null && readApart(state);
  const reading = state !== null && state.phase !== "interpreting" && (state.read?.more ?? false);
  return useMemo(
    () =>
      flow === null ? NO_MARKS : { read, from, apart, reading, edited: flow.boxEdited, found: flow.boxFound },
    [flow, read, from, apart, reading],
  );
}

/**
 * The search the session holds, for a page that is not the search page. `null`
 * when none has been opened since the page was loaded, and while a page is built.
 */
export function useOpenSearch(): SearchState | null {
  const store = useSessionIfAny()?.search()?.store ?? null;
  return useSyncExternalStore(store?.subscribe ?? NOTHING_TO_HEAR, store?.getState ?? NO_SEARCH, NO_SEARCH);
}
