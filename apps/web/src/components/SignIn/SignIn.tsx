"use client";

import { useId, useRef, useState } from "react";

import { SIGN_IN } from "@/content/account";
import type { Failure } from "@/lib/api/failure";
import { account, useWho } from "@/lib/account/account";
import { noteAsked } from "@/lib/account/asked";
import type { AccountClient } from "@/lib/account/client";
import { useGo } from "@/lib/account/go";
import { accountPaths } from "@/lib/account/paths";
import { useOpenSearch } from "@/lib/search/store";

import { Box, Failed, Notice, Page } from "../AccountParts/parts";
import parts from "../AccountParts/parts.module.css";
import { Press } from "../kit/Press/Press";

interface Props {
  /** The routes of accounts to call. A test passes its own. */
  readonly client?: Pick<AccountClient, "askForLink" | "getSession">;
}

/** The code the service refuses an address with that is not one. It is said at the field. */
const NOT_AN_ADDRESS = "invalid_email";

/**
 * Where a person asks for a link to sign in with: one field for an address, and one button.
 *
 * What the address is for, and what is kept of it, is said beside the field before
 * anything is typed, and all that is kept is listed under the form.
 *
 * What is typed stays in the field. The page holds no copy of it while it is typed: it is
 * read from the field as the button is pressed, and goes in the body of the one request
 * that asks for the link. It is then held in memory for the page that says a link was
 * sent, which shows it to the person who typed it, and nowhere else.
 *
 * The answer is the same whether or not the address has an account, and so is what the
 * page does with it: it leads to the page that says a link was sent.
 *
 * Where a search is open in the tab, the page says that it will still be open when the
 * person comes back: the button that keeps a search led them here, and what they were
 * doing is held in memory, in the tab, and in nothing the browser keeps.
 *
 * The button is never switched off: a button that is switched off while it has the focus
 * leaves the focus on nothing. It says that it is busy, and a press while it is asks for
 * nothing more. What the service refuses an address with is said at the field, which
 * takes the focus. Any other failure is said under the button, which keeps it.
 */
export function SignIn({ client = account }: Props) {
  const who = useWho(client);
  const go = useGo();
  const id = useId();
  // The search the tab holds, where one has been ranked since the page was loaded.
  const searching = useOpenSearch()?.ranking != null;
  const field = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [empty, setEmpty] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);

  const ofTheField = failure !== null && failure.kind === "api" && failure.code === NOT_AN_ADDRESS ? failure : null;
  const wrong = empty ? SIGN_IN.empty : (ofTheField?.message ?? null);

  const send = async () => {
    if (busy) return;
    const email = (field.current?.value ?? "").trim();
    setFailure(null);
    if (email === "") {
      setEmpty(true);
      field.current?.focus();
      return;
    }
    setEmpty(false);
    setBusy(true);
    const answer = await client.askForLink({ email });
    setBusy(false);
    if (!answer.ok) {
      // A call that was stopped has nothing to report.
      if (answer.failure.kind === "aborted") return;
      setFailure(answer.failure);
      if (answer.failure.kind === "api" && answer.failure.code === NOT_AN_ADDRESS) field.current?.focus();
      return;
    }
    noteAsked({ email, minutes: answer.data.lasts_minutes });
    go("sent");
  };

  return (
    <Page lay="narrow">
      <Box title={SIGN_IN.title} rank={1}>
        <p className={parts.lead}>{SIGN_IN.lead}</p>
        {who.kind === "in" ? (
          <>
            <p>
              {/* The address is the service's answer, and is drawn as words. */}
              {SIGN_IN.already(who.email)}
            </p>
            <div className={parts.ways}>
              <Press kind="go" href={accountPaths.account()}>
                {SIGN_IN.toAccount}
              </Press>
            </div>
          </>
        ) : (
          <>
            <noscript>
              <p>{SIGN_IN.noScript}</p>
            </noscript>
            {searching ? (
              <Notice>
                <p>{SIGN_IN.stays}</p>
              </Notice>
            ) : null}
            {/* It is sent by the page. Were it ever sent by the browser, it would be sent as a
                `POST`, and the field has no name: so nothing of it could reach an address. */}
            <form
              className={parts.holds}
              method="post"
              noValidate
              onSubmit={(event) => {
                event.preventDefault();
                void send();
              }}
            >
              <div className={parts.field}>
                <label className={parts.label} htmlFor={`${id}-email`}>
                  {SIGN_IN.field}
                </label>
                <p id={`${id}-hint`} className={parts.quiet}>
                  {SIGN_IN.hint}
                </p>
                <input
                  ref={field}
                  id={`${id}-email`}
                  className={`${parts.input} target`}
                  type="email"
                  inputMode="email"
                  // A browser may fill in the address it knows to be the person's own.
                  autoComplete="email"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                  required
                  aria-describedby={wrong === null ? `${id}-hint` : `${id}-hint ${id}-wrong`}
                  aria-invalid={wrong === null ? undefined : true}
                />
                {wrong === null ? null : (
                  <p id={`${id}-wrong`} className={parts.failedTitle} role="alert">
                    {wrong}
                  </p>
                )}
              </div>
              <div className={parts.ways}>
                {/* While it waits it is off, keeps the focus and says what it said: so it is of one size. */}
                <Press kind="go" submits off={busy}>
                  {SIGN_IN.send}
                </Press>
              </div>
              <p className={parts.said} role="status">
                {busy ? SIGN_IN.sending : ""}
              </p>
            </form>
            {failure !== null && ofTheField === null ? <Failed title={SIGN_IN.failed} failure={failure} /> : null}
          </>
        )}
      </Box>
      <Box title={SIGN_IN.kept.title}>
        <ul className={parts.points}>
          {SIGN_IN.kept.points.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </Box>
    </Page>
  );
}
