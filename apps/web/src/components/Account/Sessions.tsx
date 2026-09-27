"use client";

import { useLayoutEffect, useRef, useState } from "react";

import { ACCOUNT } from "@/content/account";
import type { Failure } from "@/lib/api/failure";
import type { SignedInAt } from "@/lib/api/schema";
import type { AccountClient } from "@/lib/account/client";
import { readableDate } from "@/lib/format";

import { Box, Failed } from "../AccountParts/parts";
import parts from "../AccountParts/parts.module.css";
import { Press } from "../kit/Press/Press";
import { Skeleton } from "../Skeleton/Skeleton";
import styles from "./Account.module.css";
import { useListed } from "./listed";

interface Props {
  readonly client: Pick<AccountClient, "listSessions" | "endSessions" | "signOut">;
  /** Told that the browser a person is using is signed out: of itself alone, or with every other. */
  readonly onSignedOut: (everywhere: boolean) => void;
}

/** What is being ended: one browser by the id the service names it by, this one, or every one. */
type Ending = { readonly id: string } | "here" | "everywhere";

/** What can be pressed in the list, in the order a keyboard comes to it. */
const PRESSED = "button";

/**
 * Where a person is signed in, and the ways to sign out: of one browser, of the one they
 * are using, and of every one at once.
 *
 * Of a browser the service keeps its family and no more, and three dates. It names each
 * by an id that is not the session and says nothing of it, which travels in the body of
 * the request that ends it, and never in an address.
 *
 * Signing out revokes the session at the service. Once the browser a person is using is
 * signed out, the page says so in the place of the account.
 *
 * One thing is done at a time. What is pressed says that it is off while it waits, and
 * keeps the focus. A line that goes with the press hands the focus on, to the line that
 * now stands where it stood, or to the heading of the box.
 */
export function Sessions({ client, onSignedOut }: Props) {
  const { listed, ask, set } = useListed(client.listSessions);
  const [ending, setEnding] = useState<Ending | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [said, setSaid] = useState("");
  const list = useRef<HTMLDivElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const went = useRef<number | null>(null);

  // Before the page is drawn, so that the focus is never seen to be on nothing.
  useLayoutEffect(() => {
    const at = went.current;
    if (at === null) return;
    went.current = null;
    const rows = [...(list.current?.querySelectorAll<HTMLElement>(":scope > ul > li") ?? [])];
    const next = rows[Math.min(at, rows.length - 1)]?.querySelector<HTMLElement>(PRESSED);
    (next ?? heading.current)?.focus();
  }, [listed]);

  const begin = (what: Ending) => {
    setEnding(what);
    setFailure(null);
    setSaid("");
  };

  const failed = (why: Failure) => {
    // A call that was stopped has nothing to report.
    if (why.kind !== "aborted") setFailure(why);
  };

  const endOne = async (session: SignedInAt, at: number) => {
    if (ending !== null) return;
    begin({ id: session.session_id });
    const answer = await client.endSessions({ session_id: session.session_id, everywhere: false });
    setEnding(null);
    if (!answer.ok) return failed(answer.failure);
    if (!answer.data.signed_in) return onSignedOut(false);
    went.current = at;
    set(answer.data);
    setSaid(ACCOUNT.sessions.out);
  };

  const endHere = async () => {
    if (ending !== null) return;
    begin("here");
    const answer = await client.signOut();
    setEnding(null);
    if (!answer.ok) return failed(answer.failure);
    onSignedOut(false);
  };

  const endAll = async () => {
    if (ending !== null) return;
    begin("everywhere");
    const answer = await client.endSessions({ everywhere: true });
    setEnding(null);
    if (!answer.ok) return failed(answer.failure);
    onSignedOut(true);
  };

  const waits = ending !== null;

  return (
    <Box title={ACCOUNT.sessions.title} heading={heading}>
      <p>{ACCOUNT.sessions.lead}</p>
      {listed.kind === "opening" ? (
        <div aria-busy="true">
          <Skeleton lines={3} />
        </div>
      ) : listed.kind === "failed" ? (
        <Failed title={ACCOUNT.sessions.couldNotList} failure={listed.failure}>
          <Press onPress={() => void ask()}>{ACCOUNT.tryAgain}</Press>
        </Failed>
      ) : (
        <div ref={list} className={styles.list}>
          <ul className={styles.rows} aria-label={ACCOUNT.sessions.list}>
            {listed.data.sessions.map((session, at) => {
              const browser = ACCOUNT.sessions.browser[session.browser];
              return (
                <li key={session.session_id}>
                  <div className={styles.row}>
                    <div className={styles.of}>
                      <p className={styles.name}>{browser}</p>
                      {session.current ? <p>{ACCOUNT.sessions.here}</p> : null}
                      <p className={parts.quiet}>{ACCOUNT.sessions.made(readableDate(session.made_at))}</p>
                      <p className={parts.quiet}>{ACCOUNT.sessions.seen(readableDate(session.seen_at))}</p>
                      <p className={parts.quiet}>{ACCOUNT.sessions.ends(readableDate(session.ends_at))}</p>
                    </div>
                    <div className={styles.does}>
                      {session.current ? (
                        <Press off={waits} onPress={() => void endHere()}>
                          {ACCOUNT.sessions.signOutHere}
                        </Press>
                      ) : (
                        <Press
                          // Two browsers of one family are told apart by when each signed in.
                          name={ACCOUNT.searches.of(
                            ACCOUNT.sessions.signOut,
                            `${browser}, ${ACCOUNT.sessions.made(readableDate(session.made_at))}`,
                          )}
                          off={waits}
                          onPress={() => void endOne(session, at)}
                        >
                          {ACCOUNT.sessions.signOut}
                        </Press>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
      <div className={parts.ways}>
        <Press kind="stop" off={waits} onPress={() => void endAll()}>
          {ACCOUNT.sessions.everywhere}
        </Press>
      </div>
      <p className={parts.quiet}>{ACCOUNT.sessions.everywhereHint}</p>
      <p className={parts.said} role="status">
        {waits ? ACCOUNT.sessions.signingOut : said}
      </p>
      {failure === null ? null : <Failed title={ACCOUNT.sessions.couldNotSignOut} failure={failure} />}
    </Box>
  );
}
