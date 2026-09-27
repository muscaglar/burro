"use client";

import { useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";

import { NOTICE } from "@/content/search";
import { SHARED } from "@/content/share";
import type { Client, Failure } from "@/lib/api/client";
import type { Handed } from "@/lib/api/handed";
import type { AreaSummary, VibeBands } from "@/lib/api/schema";
import { isShareId, paths } from "@/lib/paths";
import { SearchProvider, useSearch } from "@/lib/search/store";
import { SessionBoundary, useSessionIfAny } from "@/lib/session/session";

import { wordsFor } from "../ErrorBlock/ErrorBlock";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
import { SearchView } from "../SearchApp/SearchApp";
import { Skeleton } from "../Skeleton/Skeleton";
import { wasTaken } from "./own";
import styles from "./SharedSearch.module.css";

interface Props {
  /** What a form needs: the vocabulary, both defaults and the limits. From route 11, at build. */
  readonly meta: Handed;
  /** Every area of the release, from route 4, at build. */
  readonly areas: readonly AreaSummary[];
  /**
   * Where every area sits on every vibe that some area is placed on, from route 4, at build.
   * The town of each result is drawn from them, as it is on the search page: they are of
   * the release, and say nothing of the search a link holds.
   */
  readonly bands?: readonly VibeBands[];
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

/**
 * What the search holds, as the search page names it on the page: where that page hands
 * the focus when what was pressed goes. It is no stop of its own.
 */
const HOLDS = "understood";

/** What follows the `#` of the address. A browser sends it to no server. */
const theFragment = () => window.location.hash.replace(/^#/, "");
/** While the page is built there is no address to read. */
const noFragmentYet = () => null;

/**
 * The page a shared link opens. The id is read from the fragment of the
 * address, in the browser, and is sent in one place only: the path of the
 * one call that opens the share. If it is not an id the API makes, nothing
 * is sent at all.
 *
 * Until the share is open the page stands boxes of its own on the grass: what the page is
 * and what a share holds in a box of the look, and under it what became of the link, as a
 * notice or as a failure. The way on is a button of the look, and the one that matters
 * most is cobalt.
 *
 * Once it is open the page is the search page, and the answer comes first as it does
 * there: the title gives way to it, and is kept for whoever hears the page. The search
 * page keeps it so itself, as it keeps its own.
 *
 * What is pressed and then goes hands the focus on, so that it is never left on nothing.
 * "Try again" goes with the failure it stands in, and "Start again" with the search it
 * begins again, which is then opened once more as the link holds it: each leaves the
 * focus where the share is being opened, and what the search holds has it once the search
 * is open, which is what the press changed. The box of the search is not given it: it
 * makes room while it has the focus, and the answer would stand lower for it. A share
 * that opens of itself, as the page does, takes the focus from nobody.
 *
 * Where the way to a search of one's own was pressed, the search is begun again as the
 * page is left, with the areas that were chosen from it to compare: the search page keeps
 * the search that is open, and would else open on the shared one. Left by any other way,
 * the search is kept as it is.
 */
export function SharedSearch({ meta, areas, bands = [], client }: Props) {
  return (
    <SessionBoundary>
      <SearchProvider meta={meta} areas={areas} client={client}>
        <Opened bands={bands} />
      </SearchProvider>
    </SessionBoundary>
  );
}

interface Tried {
  readonly id: string;
  readonly attempt: number;
  readonly failure: Failure;
}

function Opened({ bands }: { readonly bands: readonly VibeBands[] }) {
  const { state, flow } = useSearch();
  const session = useSessionIfAny();
  const fragment = useSyncExternalStore(hearTheFragment, theFragment, noFragmentYet);
  const became = useRef<HTMLDivElement>(null);
  const opened = useRef<HTMLDivElement>(null);
  const [attempt, setAttempt] = useState(0);
  const [tried, setTried] = useState<Tried | null>(null);
  // The link that was open as the page was last drawn, to tell a search that was begun
  // again from another link that was followed.
  const wasOpen = useRef<string | null>(null);
  // The link whose search is to be handed the focus as it opens: a press took away what had it.
  const handsOn = useRef<string | null>(null);

  const id = fragment !== null && isShareId(fragment) ? fragment : null;
  // A link that is already open is not opened again over what the person has changed since.
  const isOpen = id !== null && state.shared?.id === id;

  // Before the page is drawn, so that the focus is never seen to be on nothing.
  useLayoutEffect(() => {
    const was = wasOpen.current;
    wasOpen.current = isOpen ? id : null;
    if (isOpen) {
      const mine = handsOn.current === id;
      handsOn.current = null;
      if (mine) opened.current?.querySelector<HTMLElement>(`[id="${HOLDS}"]`)?.focus({ preventScroll: true });
      return;
    }
    // The search was begun again, and went with the press: the box that had taken the focus
    // went with it. The focus is left where the share is opened again.
    if (was !== null && was === id) {
      handsOn.current = id;
      became.current?.focus({ preventScroll: true });
    }
  }, [isOpen, id]);

  // As the page is left, and before the page it leads to is drawn.
  useLayoutEffect(
    () => () => {
      if (!wasTaken()) return;
      session?.compare.clear();
      flow.startAgain();
    },
    [flow, session],
  );

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

  if (isOpen) {
    return (
      // It holds the search page, which stands boxes of its own on the grass, and says so for it.
      <div ref={opened} data-dressed="">
        <SearchView shared bands={bands} />
      </div>
    );
  }

  const failure = tried !== null && tried.id === id && tried.attempt === attempt ? tried.failure : null;
  // The one way on, where nothing can be opened: it is the button that matters most in sight.
  const own = (
    <p>
      <Press kind="go" href={paths.home()}>
        {SHARED.own}
      </Press>
    </p>
  );
  // The API has said the link leads nowhere. Asking again would be told the same.
  const leadsNowhere = failure !== null && failure.kind === "api" && failure.status < 500;

  return (
    // It stands boxes of its own on the grass, so the shell draws none round it.
    <div className={styles.page} data-dressed="">
      <Frame kind="box" className={styles.head}>
        <h1>{SHARED.title}</h1>
        <p className={styles.holds}>{SHARED.holds}</p>
      </Frame>
      {/* What became of the link. It can be given the focus, and is no stop of its own: what is
          pressed in it and goes leaves the focus here. */}
      <div ref={became} className={styles.became} tabIndex={-1}>
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
              {leadsNowhere ? null : (
                <Press
                  kind="go"
                  onPress={() => {
                    // The button goes with the failure it stands in, and the focus must not go with it.
                    became.current?.focus({ preventScroll: true });
                    // What holds the place of the search goes in its turn, as the search opens.
                    handsOn.current = id;
                    setAttempt((last) => last + 1);
                  }}
                >
                  {SHARED.tryAgain}
                </Press>
              )}
              {/* Where the link can be tried again, that is what matters most, and this is the other way on. */}
              <Press kind={leadsNowhere ? "go" : "plain"} href={paths.home()}>
                {SHARED.own}
              </Press>
            </div>
          </div>
        ) : (
          <>
            <p className={styles.opening} role="status" aria-live="polite">
              {SHARED.opening}
            </p>
            <div aria-busy="true">
              <Skeleton shape="card" lines={4} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
