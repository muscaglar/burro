"use client";

import { useSyncExternalStore } from "react";

import { SHARED } from "@/content/share";
import { servedTheRanking, type SearchState } from "@/lib/search/state";
import { useSessionIfAny } from "@/lib/session/session";

import { Disclosure } from "../Disclosure/Disclosure";
import { WHAT_IT_OPENS, type WhatItOpens } from "../SharePanel/look";
import { NOTICE_STANDS, type NoticeStands } from "./look";
import { SharedNotice, type Told } from "./SharedHeader";
import styles from "./SharedSearch.module.css";

const NOTHING_TO_HEAR = () => () => undefined;
const NO_SEARCH = () => null;

/** What the search that is open says of the link it came from. `null` where it came from none, or none is open. */
export function toldBy(state: SearchState | null): Told | null {
  if (state === null || state.shared === null) return null;
  return {
    shared: state.shared,
    release: servedTheRanking(state).release_id,
    hasPlaces: state.spec.commutes.length > 0,
  };
}

interface Props {
  /** Where what says a search came from a link stands. Left out, where the one line of `look.ts` says. */
  readonly stands?: NoticeStands;
  /** What becomes of the page as it opens, which is as the way to share a search has it. */
  readonly opens?: WhatItOpens;
}

/**
 * The way to what says that the search came from a link, where that stands after the first
 * result: a fold, closed until it is pressed, which says what the search is and opens in
 * place to all that is said of it. It stands beside the way to share a search, which
 * draws it, and is drawn as that is.
 *
 * It asks the session for the search that is open, and draws nothing where none is, or
 * where the search that is open came from no link.
 *
 * The page is not moved as it opens, so that what was pressed stays under the hand: one
 * line of the look of sharing has what it opens brought into sight, as it was.
 */
export function SharedFold({ stands = NOTICE_STANDS, opens = WHAT_IT_OPENS }: Props) {
  const held = useSessionIfAny()?.search() ?? null;
  const state = useSyncExternalStore(
    held?.store.subscribe ?? NOTHING_TO_HEAR,
    held?.store.getState ?? NO_SEARCH,
    held?.store.getState ?? NO_SEARCH,
  );
  const told = toldBy(state);
  if (stands !== "after" || told === null) return null;
  return (
    <Disclosure label={SHARED.title} className={styles.fold} bring={opens === "brought"}>
      <SharedNotice {...told} />
    </Disclosure>
  );
}
