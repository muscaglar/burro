"use client";

import { useCallback, useLayoutEffect, useRef, useState } from "react";

import { CONFIRM, SIGN_IN } from "@/content/account";
import type { Failure } from "@/lib/api/failure";
import type { SignedIn, WhoseLink } from "@/lib/api/schema";
import { account } from "@/lib/account/account";
import { forgetAsked } from "@/lib/account/asked";
import type { AccountClient } from "@/lib/account/client";
import { accountPaths } from "@/lib/account/paths";
import { takeToken, type Found } from "@/lib/account/token";
import { noteSignedIn } from "@/lib/account/who";
import { paths } from "@/lib/paths";

import { Box, Failed, Notice, Page, Tick } from "../AccountParts/parts";
import parts from "../AccountParts/parts.module.css";
import { Press } from "../kit/Press/Press";
import { Skeleton } from "../Skeleton/Skeleton";

interface Props {
  /** The routes of accounts to call. A test passes its own. */
  readonly client?: Pick<AccountClient, "whoseLink" | "signIn">;
}

type Stage =
  /** The page as it is built, before the address has been read. */
  | { readonly kind: "reading" }
  /** The address holds no link, or what it holds is no link that Burro makes. */
  | { readonly kind: "none" }
  | { readonly kind: "not_one" }
  /** The service is asked whose link it is. Nothing is used up by asking. */
  | { readonly kind: "checking" }
  | { readonly kind: "unchecked"; readonly failure: Failure }
  /** The page says whose link it is, and waits for a press. */
  | { readonly kind: "ready"; readonly whose: WhoseLink; readonly failure: Failure | null }
  /** The link was asked for in another browser, the button was pressed, and the page asks a second time. */
  | { readonly kind: "asked_again"; readonly whose: WhoseLink; readonly failure: Failure | null }
  /** The person chose not to go on. */
  | { readonly kind: "stopped" }
  /** The link can no longer be used: it ran out, was used, or is not known. */
  | { readonly kind: "spent"; readonly failure: Failure }
  | { readonly kind: "done"; readonly signedIn: SignedIn };

/** What the service refuses a link with that no press can mend: a new link is the way on. */
const SPENT = new Set(["link_expired", "link_used", "link_not_valid"]);
/** What it refuses with where the link was asked for in another browser, and the page has yet to ask a second time. */
const ELSEWHERE = "other_browser";
/** What it refuses with where an account would be made and the person has not said that they are 18 or over. */
const NOT_SAID = "age_not_confirmed";

const isSpent = (failure: Failure) => failure.kind === "api" && SPENT.has(failure.code);
const codeOf = (failure: Failure) => (failure.kind === "api" ? failure.code : null);

/**
 * The page a link to sign in opens.
 *
 * The link holds its token after the `#`, which a browser sends to no server, and the
 * page sends no referrer. As it opens, the page reads the token, takes it out of the
 * address bar at once, and holds it in memory alone: it is drawn nowhere, put in no
 * attribute and kept in nothing. It goes when the page does.
 *
 * It asks the service whose link it is, which uses nothing up, and says so: "Sign in as",
 * and the address. The token is sent to sign in only when the button is pressed. So a
 * program that opens the links of a mailbox signs nobody in, and a link that somebody
 * else sent cannot sign a person in to that somebody's account unseen.
 *
 * Where the link was asked for in another browser the page says so plainly from the
 * start, and once the button is pressed it shows the address again and asks a second
 * time. Only then is the token sent, with that the person was asked.
 *
 * Where signing in would make an account, it asks the person to say that they are 18 or
 * over, and makes none until they have.
 *
 * A page that opens of itself takes the focus from nobody. What is pressed and then goes
 * hands the focus to the heading of the page, which says what became of the press: so it
 * is never left on nothing. A button that waits on an answer says that it is off, and
 * keeps the focus.
 *
 * What is not a link as Burro makes one is never sent anywhere and never shown.
 */
export function Confirm({ client = account }: Props) {
  const [stage, setStage] = useState<Stage>({ kind: "reading" });
  const [adult, setAdult] = useState(false);
  const [unsaid, setUnsaid] = useState(false);
  const [busy, setBusy] = useState(false);
  // What the address held, read once: a page that is drawn a second time reads nothing of it again.
  const found = useRef<Found | null>(null);
  // The token, in memory, from the moment it is read until it is used or let go.
  const token = useRef<string | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  // What the page asks the second time, which is what a press on the first button leads to.
  const question = useRef<HTMLHeadingElement>(null);
  const tick = useRef<HTMLInputElement>(null);
  // True once a press took away what was pressed: what says what became of it then takes the focus.
  const handsOn = useRef(false);
  // Counts the links that were opened and the askings of each. An answer to one before the last is let go.
  const round = useRef(0);

  const check = useCallback(async () => {
    const held = token.current;
    if (held === null) return;
    round.current += 1;
    const mine = round.current;
    setStage({ kind: "checking" });
    const answer = await client.whoseLink({ token: held });
    if (mine !== round.current) return;
    if (answer.ok) {
      setStage({ kind: "ready", whose: answer.data, failure: null });
      return;
    }
    // A call that was stopped has nothing to report.
    if (answer.failure.kind === "aborted") return;
    if (isSpent(answer.failure)) token.current = null;
    setStage(isSpent(answer.failure) ? { kind: "spent", failure: answer.failure } : { kind: "unchecked", failure: answer.failure });
  }, [client]);

  /** Takes in hand what the address held. What was held of a link before it is let go, with all that was said of it. */
  const takeInHand = useCallback(
    (read: Found) => {
      round.current += 1;
      token.current = read.kind === "token" ? read.token : null;
      setAdult(false);
      setUnsaid(false);
      setBusy(false);
      if (read.kind === "token") void check();
      else setStage({ kind: read.kind });
    },
    [check],
  );

  // Before the page is drawn, so that the token is never seen in the address bar.
  useLayoutEffect(() => {
    if (found.current === null) {
      found.current = takeToken();
      // Once, as the page opens: what the address held is known only in the browser.
      takeInHand(found.current);
    }
    // A link that is opened in a tab where this page stands is the same page at another
    // address, and the page is not loaded again for it: it is told, and reads the link.
    const another = () => {
      const read = takeToken();
      // An address with nothing after its `#` is no other link: what is in hand stays.
      if (read.kind !== "none") takeInHand(read);
    };
    window.addEventListener("hashchange", another);
    return () => window.removeEventListener("hashchange", another);
  }, [takeInHand]);

  // Before the page is drawn, so that the focus is never seen to be on nothing.
  useLayoutEffect(() => {
    if (!handsOn.current) return;
    handsOn.current = false;
    (stage.kind === "asked_again" ? question : heading).current?.focus();
  }, [stage]);

  const signIn = async (whose: WhoseLink, askedAgain: boolean) => {
    const held = token.current;
    if (busy || held === null) return;
    if (whose.new_account && !adult) {
      setUnsaid(true);
      tick.current?.focus();
      return;
    }
    setUnsaid(false);
    // The page asks a second time before anything is sent, and the button goes as it does.
    if (!whose.same_browser && !askedAgain) {
      handsOn.current = true;
      setStage({ kind: "asked_again", whose, failure: null });
      return;
    }
    setBusy(true);
    const mine = round.current;
    const answer = await client.signIn({
      token: held,
      adult: whose.new_account && adult,
      // True only where the person was told so, was shown the address again, and chose to go on.
      other_browser: askedAgain,
    });
    // Whoever shows who is signed in is told, whatever the page has gone on to since.
    if (answer.ok) noteSignedIn(answer.data.email);
    // Another link was opened meanwhile, and is the one in hand: this answer is of the one before it.
    if (mine !== round.current) return;
    setBusy(false);
    if (answer.ok) {
      // The link is used up, and so is what the page held of it and of what was asked.
      token.current = null;
      forgetAsked();
      handsOn.current = true;
      setStage({ kind: "done", signedIn: answer.data });
      return;
    }
    const { failure } = answer;
    if (failure.kind === "aborted") return;
    if (isSpent(failure)) {
      token.current = null;
      handsOn.current = true;
      setStage({ kind: "spent", failure });
      return;
    }
    // The service says the link was asked for elsewhere, and the page had not asked a second time: it asks now.
    if (codeOf(failure) === ELSEWHERE && !askedAgain) {
      handsOn.current = true;
      setStage({ kind: "asked_again", whose: { ...whose, same_browser: false }, failure: null });
      return;
    }
    if (codeOf(failure) === NOT_SAID) {
      handsOn.current = askedAgain;
      setUnsaid(true);
      setStage({ kind: "ready", whose: { ...whose, new_account: true }, failure: null });
      return;
    }
    // The button stays, and keeps the focus: the failure is said under it, at once.
    setStage(askedAgain ? { kind: "asked_again", whose, failure } : { kind: "ready", whose, failure });
  };

  const stop = () => {
    // The link is let go unused: nothing was sent, and nothing of it is held.
    token.current = null;
    handsOn.current = true;
    setStage({ kind: "stopped" });
  };

  const askForOne = (again: boolean) => (
    <Press kind="go" href={accountPaths.signIn()}>
      {again ? CONFIRM.askAgain : CONFIRM.ask}
    </Press>
  );

  const title =
    stage.kind === "none"
      ? CONFIRM.none.title
      : stage.kind === "not_one"
        ? CONFIRM.notOne.title
        : stage.kind === "stopped"
          ? CONFIRM.elsewhere.stopped.title
          : stage.kind === "done"
            ? CONFIRM.done.title
            : CONFIRM.title;

  return (
    <Page lay="narrow">
      <Box title={title} rank={1} heading={heading}>
        {stage.kind === "reading" || stage.kind === "checking" ? (
          <>
            {/* The link is read by the page, and a browser with JavaScript off reads none. */}
            <noscript>
              <p>{SIGN_IN.noScript}</p>
            </noscript>
            <p role="status" aria-live="polite">
              {CONFIRM.checking}
            </p>
            <div aria-busy="true">
              <Skeleton lines={3} />
            </div>
          </>
        ) : null}

        {stage.kind === "none" ? (
          <>
            <p className={parts.lead}>{CONFIRM.none.text}</p>
            <div className={parts.ways}>{askForOne(false)}</div>
          </>
        ) : null}

        {stage.kind === "not_one" ? (
          <>
            <p className={parts.lead}>{CONFIRM.notOne.text}</p>
            <div className={parts.ways}>{askForOne(true)}</div>
          </>
        ) : null}

        {stage.kind === "unchecked" ? (
          <Failed title={CONFIRM.couldNotCheck} failure={stage.failure}>
            <Press
              kind="go"
              onPress={() => {
                // The button goes with the failure it stands in, and the focus must not go with it.
                handsOn.current = true;
                void check();
              }}
            >
              {CONFIRM.tryAgain}
            </Press>
            <Press href={accountPaths.signIn()}>{CONFIRM.askAgain}</Press>
          </Failed>
        ) : null}

        {stage.kind === "spent" ? (
          <Failed title={CONFIRM.failed} failure={stage.failure}>
            {askForOne(true)}
          </Failed>
        ) : null}

        {stage.kind === "ready" ? (
          <>
            {stage.whose.same_browser ? null : (
              <Notice title={CONFIRM.elsewhere.title}>
                <p>{CONFIRM.elsewhere.text}</p>
              </Notice>
            )}
            <p className={parts.lead}>{CONFIRM.ready.lead}</p>
            {/* The address is the service's answer, and is drawn as words. */}
            <p className={`${parts.lead} ${parts.address}`}>{stage.whose.email}</p>
            <p>{CONFIRM.ready.check}</p>
            {stage.whose.new_account ? (
              <>
                <p>{CONFIRM.first.text}</p>
                <Tick
                  box={tick}
                  says={CONFIRM.first.tick}
                  ticked={adult}
                  off={busy}
                  missing={unsaid && !adult ? CONFIRM.first.needed : null}
                  onTick={(ticked) => {
                    setAdult(ticked);
                    if (ticked) setUnsaid(false);
                  }}
                />
              </>
            ) : null}
            <div className={parts.ways}>
              {/* It says whom it signs in. While it waits it is off, keeps the focus and says what it said. */}
              <Press kind="go" reads off={busy} onPress={() => void signIn(stage.whose, false)}>
                {CONFIRM.ready.signIn(stage.whose.email)}
              </Press>
            </div>
            <p className={parts.said} role="status">
              {busy ? CONFIRM.signingIn : ""}
            </p>
            {stage.failure === null ? null : (
              <Failed title={CONFIRM.failed} failure={stage.failure}>
                <Press href={accountPaths.signIn()}>{CONFIRM.askAgain}</Press>
              </Failed>
            )}
          </>
        ) : null}

        {stage.kind === "asked_again" ? (
          <>
            <Notice title={CONFIRM.elsewhere.title}>
              <p>{CONFIRM.elsewhere.text}</p>
            </Notice>
            <h2 ref={question} className={`${parts.heading} ${parts.lands}`} tabIndex={-1}>
              {CONFIRM.elsewhere.again}
            </h2>
            <p>{CONFIRM.elsewhere.as}</p>
            {/* The address, shown again. */}
            <p className={`${parts.lead} ${parts.address}`}>{stage.whose.email}</p>
            <div className={parts.ways}>
              <Press kind="go" reads off={busy} onPress={() => void signIn(stage.whose, true)}>
                {CONFIRM.elsewhere.yes(stage.whose.email)}
              </Press>
              <Press off={busy} onPress={stop}>
                {CONFIRM.elsewhere.no}
              </Press>
            </div>
            <p className={parts.said} role="status">
              {busy ? CONFIRM.signingIn : ""}
            </p>
            {stage.failure === null ? null : (
              <Failed title={CONFIRM.failed} failure={stage.failure}>
                <Press href={accountPaths.signIn()}>{CONFIRM.askAgain}</Press>
              </Failed>
            )}
          </>
        ) : null}

        {stage.kind === "stopped" ? (
          <>
            <p className={parts.lead}>{CONFIRM.elsewhere.stopped.text}</p>
            <div className={parts.ways}>
              <Press kind="go" href={paths.home()}>
                {CONFIRM.elsewhere.stopped.toSearch}
              </Press>
            </div>
          </>
        ) : null}

        {stage.kind === "done" ? (
          <>
            <p className={parts.lead}>{CONFIRM.done.text(stage.signedIn.email)}</p>
            {stage.signedIn.new_account ? <p>{CONFIRM.done.made}</p> : null}
            <p>{CONFIRM.done.lasts}</p>
            <p>{CONFIRM.done.elsewhere}</p>
            <div className={parts.ways}>
              <Press kind="go" href={paths.home()}>
                {CONFIRM.done.toSearch}
              </Press>
              <Press href={accountPaths.account()}>{CONFIRM.done.toAccount}</Press>
            </div>
          </>
        ) : null}
      </Box>
    </Page>
  );
}
