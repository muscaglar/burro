"use client";

/**
 * The client the website uses for the routes of accounts, and who is signed in as a page
 * reads it.
 *
 * Every answer the client reads is heard by the banners, as every answer of the API is,
 * and an answer that says nobody is signed in is heard by whatever shows who is.
 */

import { useEffect, useSyncExternalStore } from "react";

import { noteSaid } from "@/lib/api/said";
import { noteSynthetic } from "@/lib/api/synthetic";

import { whatWasAsked } from "./asked";
import { watchForAway } from "./away";
import { createAccountClient, type AccountClient } from "./client";
import { askWho, noteSignedOut, subscribeToWho, UNKNOWN, whoIs, type Who } from "./who";

export const account: AccountClient = createAccountClient({
  onSynthetic: noteSynthetic,
  onSaid: noteSaid,
  onSignedOut: noteSignedOut,
});

/** While a page is built nobody has asked, so it is built as for a person of whom nothing is known. */
const asBuilt = () => UNKNOWN;

/**
 * True where the service is worth asking again as a person comes back to the tab. It is
 * where a link was asked for in this tab and nobody is known to be signed in, since a link
 * is most often opened in another tab: where somebody is signed in, since they may have
 * signed out meanwhile, in another tab or of every browser from another one: and where
 * the service could not say when it was asked. A person who never signed in and never
 * asked for a link is asked about once, as the page opens.
 */
function isWorthAsking(who: Who): boolean {
  if (who.kind === "unsaid" || who.kind === "in") return true;
  return whatWasAsked() !== null;
}

/**
 * Who is signed in. The service is asked as the page opens, if nothing has asked yet. It
 * is asked again when a person comes back to the tab they asked for a link in, or are
 * signed in at: they may have signed in meanwhile, in the tab the link opened, or signed
 * out. And it is asked again when the browser shows a page that it had put away, which
 * let go of who was signed in as it went.
 */
export function useWho(client: Pick<AccountClient, "getSession"> = account): Who {
  const who = useSyncExternalStore(subscribeToWho, whoIs, asBuilt);

  useEffect(() => {
    watchForAway();
    if (whoIs().kind === "unknown") void askWho(client);
    const cameBack = () => {
      if (document.visibilityState === "visible" && isWorthAsking(whoIs())) void askWho(client);
    };
    const shownAgain = (event: PageTransitionEvent) => {
      if (event.persisted) void askWho(client);
    };
    document.addEventListener("visibilitychange", cameBack);
    window.addEventListener("focus", cameBack);
    window.addEventListener("pageshow", shownAgain);
    return () => {
      document.removeEventListener("visibilitychange", cameBack);
      window.removeEventListener("focus", cameBack);
      window.removeEventListener("pageshow", shownAgain);
    };
  }, [client]);

  return who;
}
