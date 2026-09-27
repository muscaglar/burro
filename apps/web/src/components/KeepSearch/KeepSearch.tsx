"use client";

import { useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";

import { ACCOUNT_NAV, KEEP } from "@/content/account";
import type { Failure } from "@/lib/api/failure";
import { account, useWho } from "@/lib/account/account";
import type { AccountClient } from "@/lib/account/client";
import { accountsOn } from "@/lib/account/on";
import { wasOpened } from "@/lib/account/opened";
import { accountPaths } from "@/lib/account/paths";
import { isTheirs, keepsRecent, noteKeeps, noteStands, subscribeToKeeps } from "@/lib/account/recent";
import { whoIs } from "@/lib/account/who";
import { useSearch } from "@/lib/search/store";

import { ENTRY_ON_A_NARROW_SCREEN, type OnANarrowScreen } from "../AccountEntry/look";
import { Failed } from "../AccountParts/parts";
import { Press } from "../kit/Press/Press";
import styles from "./KeepSearch.module.css";

interface Props {
  /** The routes of accounts to call. A test passes its own. */
  readonly client?: Pick<AccountClient, "keepSearch" | "keepRecent" | "getMe" | "getSession">;
  /** Whether accounts are on. Left out, it is what the one setting says. */
  readonly on?: boolean;
  /** How long a ranking stands before its search is put among the last ones, in milliseconds. A test passes its own. */
  readonly after?: number;
  /** What becomes of the entry of the name board on a narrow screen once a search is open. Left out, what the look says. */
  readonly narrow?: OnANarrowScreen;
}

/**
 * What the search holds, as the search page names it on the page: where that page hands
 * the focus when what was pressed goes.
 */
const HOLDS = "understood";

/**
 * How long a ranking stands on the page before its search is sent to be kept among the
 * last ones. A setting that is moved ranks again at every step, and a person who moves
 * one is not making a search at each: what is kept is what they stopped at.
 */
export const RECENT_AFTER_MS = 5_000;

const notKnown = () => null;

/**
 * The button on the search page that keeps a search, which stands beside the way to share
 * one, after the first result. With accounts off it draws nothing, and asks nothing.
 *
 * What is kept is the spec the page holds, which is the last one the API returned: what
 * Burro understood, and never the words a person typed. It goes in the body of the
 * request, to the website's own origin.
 *
 * For a person who has not signed in it is a link to signing in, and says so. The search
 * they were making is not lost by it: it is held in memory, in this tab, and is still
 * open when they come back to the page. Nothing of it is put in an address or in anything
 * the browser keeps.
 *
 * Once the search on the page is kept the button says so and is off, until the search
 * changes. It is never switched off: it says that it is off, and keeps the focus.
 *
 * Where the person lets Burro keep their last searches, a search that has stood on the
 * page a while is sent to be kept among them. Whether they do is asked of the service
 * first, and nothing is sent where they do not. A search that came from a link somebody
 * shared is not the person's own, and is not sent. Nor is one that was made before they
 * were signed in, by whoever sat at the tab then: it can be saved by a press, and is
 * sent by nothing else.
 *
 * On a narrow screen the entry of the name board gives way to the answer once a search is
 * open, where the look says so. The way to the account of a person who is signed in then
 * stands here, beside the button, and is drawn on a narrow screen alone.
 *
 * Where a press on the page of an account opened the search that is drawn, what was
 * pressed went with that page: what the search holds takes the focus.
 */
export function KeepSearch({
  client = account,
  on = accountsOn(),
  after = RECENT_AFTER_MS,
  narrow = ENTRY_ON_A_NARROW_SCREEN,
}: Props) {
  if (!on) return null;
  return <Keeps client={client} after={after} narrow={narrow} />;
}

function Keeps({ client, after, narrow }: Required<Pick<Props, "client" | "after" | "narrow">>) {
  const { state } = useSearch();
  const who = useWho(client);
  const keeps = useSyncExternalStore(subscribeToKeeps, keepsRecent, notKnown);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  // The hash of the search that was kept here, which tells it from the search that follows it.
  const [kept, setKept] = useState<string | null>(null);
  // The search that was last sent to be kept among the last ones, so that none is sent twice.
  const sent = useRef<string | null>(null);

  // Before the page is drawn, so that the focus is never seen to be on nothing.
  useLayoutEffect(() => {
    if (wasOpened()) document.getElementById(HOLDS)?.focus({ preventScroll: true });
  }, []);

  const signedIn = who.kind === "in";
  // Who is asked about: an answer that was asked for of one person is never taken for the next.
  const whose = who.kind === "in" ? who.email : null;
  // Nor is what was saved, or what failed, said to whoever signs in after the one who pressed:
  // their account holds no such search. It holds who is signed in, as the page does, and no longer.
  const [saidTo, setSaidTo] = useState(whose);
  if (saidTo !== whose) {
    setSaidTo(whose);
    setKept(null);
    setFailure(null);
  }
  // The ranking on the page is of the spec the page holds, and nothing waits to change it.
  const settled = state.phase === "results" && state.ranking !== null && state.specHash === state.rankedHash;
  const hash = settled ? state.specHash : null;
  const isKept = hash !== null && kept === hash;
  const { spec, ranking } = state;
  const own = state.shared === null;

  // Whether the person lets Burro keep their last searches is asked once they are known to be
  // signed in, and again once it is let go of: it was learned of the person before them.
  useEffect(() => {
    if (whose === null) {
      noteKeeps(null);
      return;
    }
    if (keeps !== null) return;
    let stopped = false;
    void client.getMe().then((answer) => {
      if (!stopped && answer.ok) noteKeeps(answer.data.preferences.keep_recent === "on");
    });
    return () => {
      stopped = true;
    };
  }, [whose, keeps, client]);

  // Whose the search is, is settled as its ranking is first seen, and before anything is sent.
  useEffect(() => {
    if (hash !== null && ranking !== null) noteStands(ranking, signedIn);
  }, [hash, ranking, signedIn]);

  useEffect(() => {
    if (!signedIn || keeps !== true || !own || hash === null || ranking === null || sent.current === hash) return;
    // What somebody else made, or anybody who was not signed in, is not this person's to have kept.
    if (!isTheirs(ranking)) return;
    const timer = setTimeout(() => {
      // Asked again as it is sent: somebody else may have signed in while it stood.
      if (!isTheirs(ranking)) return;
      sent.current = hash;
      void client.keepRecent({ spec }).then((answer) => {
        // The service says whether it kept it, and is believed.
        if (answer.ok) noteKeeps(answer.data.kept);
      });
    }, after);
    return () => clearTimeout(timer);
  }, [signedIn, keeps, own, hash, ranking, spec, client, after]);

  const save = async () => {
    if (busy || hash === null || isKept) return;
    setBusy(true);
    setFailure(null);
    const answer = await client.keepSearch({ spec });
    setBusy(false);
    // Somebody else may have signed in while it was asked. What it came to is not theirs to be told.
    const now = whoIs();
    if ((now.kind === "in" ? now.email : null) !== whose) return;
    if (answer.ok) {
      setKept(hash);
      return;
    }
    // A call that was stopped has nothing to report.
    if (answer.failure.kind !== "aborted") setFailure(answer.failure);
  };

  return (
    // What holds it is laid out by the page, as what holds the way to share a search is:
    // the button stands in the row, and what it says goes under the row, as wide as it.
    <div className={styles.keep}>
      {signedIn ? (
        <Press off={busy || isKept || hash === null} onPress={() => void save()}>
          {isKept ? KEEP.saved : KEEP.save}
        </Press>
      ) : (
        // Which page a person reads next is told to no server ahead of time.
        <Press href={accountPaths.signIn()}>{KEEP.signIn}</Press>
      )}
      {signedIn && narrow === "gives-way" ? (
        <Press className={styles.account} href={accountPaths.account()}>
          {ACCOUNT_NAV.account}
        </Press>
      ) : null}
      <div className={styles.says} data-says={signedIn && (busy || isKept || failure !== null)}>
        {signedIn ? (
          <p className={styles.said} role="status">
            {busy ? KEEP.saving : isKept ? `${KEEP.done} ${KEEP.what}` : ""}
          </p>
        ) : null}
        {signedIn && isKept ? (
          <p className={styles.way}>
            <Press href={accountPaths.account()}>{KEEP.toAccount}</Press>
          </p>
        ) : null}
        {signedIn && failure !== null ? <Failed title={KEEP.failed} failure={failure} /> : null}
      </div>
    </div>
  );
}
