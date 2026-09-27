/**
 * Who is signed in, as the service last said. It is held in memory, for as long as the
 * page is open in this tab, and in nothing the browser keeps: what holds a session is a
 * cookie that no script can read, so the page asks the service and is told.
 *
 * It is asked once as a page opens. It is asked again when a person comes back to the
 * tab they asked for a link in: a link to sign in is opened from an email, which is most
 * often in another tab. It is asked again when somebody who is signed in comes back to
 * the tab: they may have signed out since, in another tab, or of every browser from
 * another one. And whatever the service answers, to anything, that says nobody is signed
 * in is heard here.
 *
 * What is held is the address the person signed in with, which the service gave, and
 * nothing else of the account. Whether a person lets Burro keep their last searches was
 * learned of whoever was signed in, so it is let go of as who is signed in changes. And
 * the search that stands in the tab was made before they were signed in, so it is not
 * theirs to have kept.
 */

import type { Failure } from "@/lib/api/failure";

import type { AccountClient } from "./client";
import { noteKeeps, noteMadeBefore } from "./recent";

export type Who =
  /** Nobody has asked yet. */
  | { readonly kind: "unknown" }
  /** Nobody is signed in. */
  | { readonly kind: "out" }
  /** Somebody is, with this address. */
  | { readonly kind: "in"; readonly email: string }
  /** The service was asked, and could not say. */
  | { readonly kind: "unsaid"; readonly failure: Failure };

type Listener = () => void;

export const UNKNOWN: Who = { kind: "unknown" };
const OUT: Who = { kind: "out" };

let who: Who = UNKNOWN;
/** The asking that is under way, so that two parts of a page that ask at once are one request. */
let asking: Promise<Who> | null = null;
/** Counts what was said, so that an answer which was asked for before something was said does not unsay it. */
let said = 0;
const listeners = new Set<Listener>();

function say(next: Who): void {
  said += 1;
  const same = next.kind === who.kind && (next.kind !== "in" || (who.kind === "in" && who.email === next.email));
  if (same && next.kind !== "unsaid") return;
  if (!same) {
    noteKeeps(null);
    noteMadeBefore();
  }
  who = next;
  for (const listener of [...listeners]) listener();
}

export function whoIs(): Who {
  return who;
}

export function subscribeToWho(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Told that a person has signed in, by the answer that signed them in. */
export function noteSignedIn(email: string): void {
  say({ kind: "in", email });
}

/** Told that nobody is signed in: a person signed out, or an answer said so. */
export function noteSignedOut(): void {
  say(OUT);
}

/**
 * Told that the browser is putting the page away, to show it again as it stood. Who is
 * signed in is then not known, until the service has been asked again: the person may
 * have signed out before the page is shown again. An answer that is on its way is of
 * the page as it was, and is let go.
 */
export function notePutAway(): void {
  asking = null;
  say(UNKNOWN);
}

/**
 * Asks the service who is signed in, and answers with what it said. While it is being
 * asked it is not asked a second time. A failure is no answer that nobody is signed in:
 * it is kept as what it is, and asked about again.
 */
export function askWho(client: Pick<AccountClient, "getSession">): Promise<Who> {
  if (asking !== null) return asking;
  const before = said;
  const mine: Promise<Who> = client.getSession().then((answer) => {
    if (asking === mine) asking = null;
    // Something was said while this was on its way, by a sign-in or a sign-out: that stands.
    if (said !== before) return who;
    if (!answer.ok) {
      // A call that was stopped has nothing to report.
      if (answer.failure.kind !== "aborted") say({ kind: "unsaid", failure: answer.failure });
      return who;
    }
    const { signed_in: signedIn, email } = answer.data;
    say(signedIn && email !== null ? { kind: "in", email } : OUT);
    return who;
  });
  asking = mine;
  return mine;
}

/** For tests only: a page that has asked nothing yet. */
export function forgetWho(): void {
  who = UNKNOWN;
  asking = null;
  said = 0;
  listeners.clear();
}
