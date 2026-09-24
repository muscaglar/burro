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
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";

import { api, type Client } from "@/lib/api/client";
import type { AreaSummary, GeometryData, MetaData } from "@/lib/api/schema";
import { useSessionIfAny } from "@/lib/session/session";

import { createFlow, type Flow } from "./flow";
import { initialState, reduce, type SearchEvent, type SearchState } from "./state";

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
  readonly meta: MetaData;
  readonly areas: readonly AreaSummary[];
  readonly geometry?: GeometryData | null;
  /** The API to call. A test passes its own. */
  readonly client?: Client;
  readonly children: ReactNode;
}

function open(meta: MetaData, areas: readonly AreaSummary[], geometry: GeometryData | null, client: Client): Held {
  const store = createStore(initialState(meta, areas, geometry));
  return { store, flow: createFlow({ client, getState: store.getState, dispatch: store.dispatch }) };
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

/** What can be done to the search, for a part of the page that shows none of it. */
export function useFlow(): Flow {
  return useHeld().flow;
}

const NOTHING_TO_HEAR = () => () => undefined;
const NO_SEARCH = () => null;

/**
 * The search the session holds, for a page that is not the search page. `null`
 * when none has been opened since the page was loaded, and while a page is built.
 */
export function useOpenSearch(): SearchState | null {
  const store = useSessionIfAny()?.search()?.store ?? null;
  return useSyncExternalStore(store?.subscribe ?? NOTHING_TO_HEAR, store?.getState ?? NO_SEARCH, NO_SEARCH);
}
