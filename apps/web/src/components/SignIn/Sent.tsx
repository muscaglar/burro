"use client";

import { useLayoutEffect, useRef, useSyncExternalStore } from "react";

import { SENT } from "@/content/account";
import { subscribeToAsked, whatWasAsked } from "@/lib/account/asked";
import { accountPaths } from "@/lib/account/paths";
import { paths } from "@/lib/paths";

import { Box, Page } from "../AccountParts/parts";
import parts from "../AccountParts/parts.module.css";
import { Press } from "../kit/Press/Press";

/** While the page is built nothing was asked, so it is built with the words that name no address. */
const asBuilt = () => null;

/**
 * Says that a link to sign in was sent. It says the same whether or not the address has an
 * account: the service answers the same, and this page is handed nothing else.
 *
 * It shows the address the link was asked for, to the person who typed it, so that an
 * address typed wrongly is seen. The address is held in memory and drawn as words: it is
 * in no address of the website and in nothing the browser keeps. Where the page holds
 * none, as when it is loaded again, it says "the address you gave".
 *
 * It sends nothing. What a person was doing is kept for them where that can be done with
 * nothing kept in the browser: a search that is open in this tab stays open in it, and
 * the page says so, and leads back to it.
 *
 * Where a press led here, the button that was pressed went with the page it stood on: the
 * heading of this page takes the focus, so that it is never left on nothing. Opened
 * another way, the page takes the focus from nobody.
 */
export function Sent() {
  const asked = useSyncExternalStore(subscribeToAsked, whatWasAsked, asBuilt);
  const heading = useRef<HTMLHeadingElement>(null);

  // Before the page is drawn, so that the focus is never seen to be on nothing.
  useLayoutEffect(() => {
    if (whatWasAsked() !== null) heading.current?.focus();
  }, []);

  return (
    <Page lay="narrow">
      <Box title={SENT.title} rank={1} heading={heading}>
        {asked === null ? (
          <p className={parts.lead}>{SENT.toTheAddress}</p>
        ) : (
          // The address is what the person typed, and is drawn as words and as nothing else.
          <p className={parts.lead}>{SENT.to(asked.email)}</p>
        )}
        <p>{asked === null ? SENT.lastsAWhile : SENT.lasts(asked.minutes)}</p>
        <p>{SENT.here}</p>
        <p>{SENT.stays}</p>
        <p>{SENT.late}</p>
        <div className={parts.ways}>
          {/* Nothing is asked of a person here, so the way back to what they were doing is what matters most. */}
          <Press kind="go" href={paths.home()}>
            {SENT.back}
          </Press>
          <Press href={accountPaths.signIn()}>{SENT.again}</Press>
        </div>
      </Box>
    </Page>
  );
}
