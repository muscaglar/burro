"use client";

import { useLayoutEffect, useRef, useState } from "react";

import { ACCOUNT } from "@/content/account";
import type { Failure } from "@/lib/api/failure";
import type { AccountClient } from "@/lib/account/client";
import { accountPaths } from "@/lib/account/paths";

import { Box, Failed, Notice } from "../AccountParts/parts";
import parts from "../AccountParts/parts.module.css";
import { Press } from "../kit/Press/Press";

interface Props {
  readonly client: Pick<AccountClient, "deleteMe">;
  /** Whether the person signed in a short while ago, as the service says: it deletes an account for nobody else. */
  readonly fresh: boolean;
  /** Told that the account is gone, and the person signed out with it. */
  readonly onDeleted: () => void;
}

/** What the service refuses with where the person signed in too long ago. */
const SIGN_IN_AGAIN = "sign_in_again";

/**
 * Deletes the account, and everything of it.
 *
 * It says what goes before anything is pressed, and asks a second time before it asks
 * the service: what is deleted cannot be brought back. The service deletes an account
 * only for a person who signed in a short while ago. Where it says they did not, the
 * page says so, in its own words before a press and in the service's after one, and
 * leads to signing in.
 *
 * What is pressed and then goes hands the focus on: to what is asked the second time,
 * and from there back to the button that asked. While the service is asked, what was
 * pressed says that it is off and keeps the focus.
 */
export function Remove({ client, fresh, onDeleted }: Props) {
  const [asked, setAsked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  const question = useRef<HTMLParagraphElement>(null);
  const asks = useRef<HTMLButtonElement>(null);
  // Where the focus is handed as the page is next drawn: a press took away what had it.
  const handsTo = useRef<"question" | "asks" | null>(null);

  // Before the page is drawn, so that the focus is never seen to be on nothing.
  useLayoutEffect(() => {
    const to = handsTo.current;
    handsTo.current = null;
    if (to === "question") question.current?.focus();
    if (to === "asks") asks.current?.focus();
  }, [asked]);

  const remove = async () => {
    if (busy) return;
    setBusy(true);
    setFailure(null);
    const answer = await client.deleteMe();
    setBusy(false);
    if (answer.ok) {
      onDeleted();
      return;
    }
    // A call that was stopped has nothing to report.
    if (answer.failure.kind !== "aborted") setFailure(answer.failure);
  };

  const signInAgain = <Press href={accountPaths.signIn()}>{ACCOUNT.remove.signIn}</Press>;
  const mustSignIn = failure !== null && failure.kind === "api" && failure.code === SIGN_IN_AGAIN;

  return (
    <Box title={ACCOUNT.remove.title}>
      <p>{ACCOUNT.remove.text}</p>
      <p>{ACCOUNT.remove.shares}</p>
      {!fresh ? (
        <Notice>
          <p>{ACCOUNT.remove.again}</p>
          <div className={parts.ways}>{signInAgain}</div>
        </Notice>
      ) : asked ? (
        <Notice>
          <p ref={question} className={`${parts.noticeTitle} ${parts.lands}`} tabIndex={-1}>
            {ACCOUNT.remove.sure}
          </p>
          <div className={parts.ways}>
            <Press kind="stop" off={busy} onPress={() => void remove()}>
              {ACCOUNT.remove.yes}
            </Press>
            <Press
              off={busy}
              onPress={() => {
                handsTo.current = "asks";
                setFailure(null);
                setAsked(false);
              }}
            >
              {ACCOUNT.remove.no}
            </Press>
          </div>
        </Notice>
      ) : (
        <div className={parts.ways}>
          <Press
            ref={asks}
            kind="stop"
            onPress={() => {
              handsTo.current = "question";
              setAsked(true);
            }}
          >
            {ACCOUNT.remove.ask}
          </Press>
        </div>
      )}
      <p className={parts.said} role="status">
        {busy ? ACCOUNT.remove.deleting : ""}
      </p>
      {failure === null ? null : (
        <Failed title={ACCOUNT.remove.failed} failure={failure}>
          {mustSignIn ? signInAgain : undefined}
        </Failed>
      )}
    </Box>
  );
}
