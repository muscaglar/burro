"use client";

import Link from "next/link";
import { useEffect, useState, useSyncExternalStore } from "react";

import { NOTICE } from "@/content/search";
import { SHARED } from "@/content/share";
import type { Client, Failure } from "@/lib/api/client";
import type { AreaSummary, MetaData } from "@/lib/api/schema";
import { isShareId, paths } from "@/lib/paths";
import { SearchProvider, useSearch } from "@/lib/search/store";
import { SessionBoundary } from "@/lib/session/session";

import { wordsFor } from "../ErrorBlock/ErrorBlock";
import { SearchView } from "../SearchApp/SearchApp";
import { Skeleton } from "../Skeleton/Skeleton";
import styles from "./SharedSearch.module.css";

interface Props {
  /** What a form needs: the vocabulary, both defaults and the limits. From route 11, at build. */
  readonly meta: MetaData;
  /** Every area of the release, from route 4, at build. */
  readonly areas: readonly AreaSummary[];
  /** The API to call. A test passes its own. */
  readonly client?: Client;
}

/** Hears of another link followed in the same tab, and of going back or forward to one. */
function hearTheFragment(heard: () => void): () => void {
  window.addEventListener("hashchange", heard);
  window.addEventListener("popstate", heard);
  return () => {
    window.removeEventListener("hashchange", heard);
    window.removeEventListener("popstate", heard);
  };
}

/** What follows the `#` of the address. A browser sends it to no server. */
const theFragment = () => window.location.hash.replace(/^#/, "");
/** While the page is built there is no address to read. */
const noFragmentYet = () => null;

/**
 * The page a shared link opens. The id is read from the fragment of the
 * address, in the browser, and is sent in one place only: the path of the
 * one call that opens the share. If it is not an id the API makes, nothing
 * is sent at all.
 */
export function SharedSearch({ meta, areas, client }: Props) {
  return (
    <SessionBoundary>
      <SearchProvider meta={meta} areas={areas} client={client}>
        <Opened />
      </SearchProvider>
    </SessionBoundary>
  );
}

interface Tried {
  readonly id: string;
  readonly attempt: number;
  readonly failure: Failure;
}

function Opened() {
  const { state, flow } = useSearch();
  const fragment = useSyncExternalStore(hearTheFragment, theFragment, noFragmentYet);
  const [attempt, setAttempt] = useState(0);
  const [tried, setTried] = useState<Tried | null>(null);

  const id = fragment !== null && isShareId(fragment) ? fragment : null;
  // A link that is already open is not opened again over what the person has changed since.
  const isOpen = id !== null && state.shared?.id === id;

  useEffect(() => {
    if (id === null || isOpen) return;
    let stopped = false;
    void flow.openShare(id).then((failure) => {
      // A call that was stopped has nothing to report.
      if (stopped || failure === null || failure.kind === "aborted") return;
      setTried({ id, attempt, failure });
    });
    return () => {
      stopped = true;
    };
  }, [id, isOpen, attempt, flow]);

  if (isOpen) return <SearchView shared />;

  const failure = tried !== null && tried.id === id && tried.attempt === attempt ? tried.failure : null;
  const own = (
    <p>
      <Link className={`${styles.link} target`} href={paths.home()}>
        {SHARED.own}
      </Link>
    </p>
  );

  return (
    <div className={styles.page}>
      <h1>{SHARED.title}</h1>
      <p className={styles.holds}>{SHARED.holds}</p>
      {fragment === null ? (
        <Skeleton shape="card" lines={4} />
      ) : fragment === "" ? (
        <div className={styles.state} role="status">
          <p className={styles.stateTitle}>{SHARED.none.title}</p>
          <p>{SHARED.none.text}</p>
          {own}
        </div>
      ) : id === null ? (
        <div className={styles.state} role="status">
          <p className={styles.stateTitle}>{SHARED.notOne.title}</p>
          <p>{SHARED.notOne.text}</p>
          {own}
        </div>
      ) : failure !== null ? (
        <div className={styles.error} role="alert">
          <p className={styles.errorTitle}>{SHARED.failedTitle}</p>
          <p>{wordsFor(failure)}</p>
          {failure.requestId !== null ? (
            <p className={styles.request}>
              {NOTICE.requestId} <code>{failure.requestId}</code>
            </p>
          ) : null}
          <div className={styles.actions}>
            {/* The API has said the link leads nowhere. Asking again would be told the same. */}
            {failure.kind === "api" && failure.status < 500 ? null : (
              <button type="button" className="target" onClick={() => setAttempt((last) => last + 1)}>
                {SHARED.tryAgain}
              </button>
            )}
            <Link className={`${styles.link} target`} href={paths.home()}>
              {SHARED.own}
            </Link>
          </div>
        </div>
      ) : (
        <>
          <p role="status" aria-live="polite">
            {SHARED.opening}
          </p>
          <div aria-busy="true">
            <Skeleton shape="card" lines={4} />
          </div>
        </>
      )}
    </div>
  );
}
