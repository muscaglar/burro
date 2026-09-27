/**
 * What a page holds of an account is let go of as the browser puts the page away.
 *
 * A browser keeps a page that a person has left, whole and as it stood, so that it can
 * show it again at once when they go back to it. It asks no server as it does. So a page
 * that showed an account would show it again to whoever pressed Back, though the person
 * had signed out since: their address, and the searches they kept, which say where they go.
 *
 * So as a page is put away, whatever it holds of an account is let go of, before the
 * browser keeps it: who is signed in, the address a link was asked for, whether the last
 * searches are kept, and everything a page of accounts has drawn, the token of a link
 * among it. When the page is shown again it begins again, and asks the service who is
 * signed in before it draws anything of anybody.
 *
 * Nothing is kept anywhere by this, the page is not loaded again, and its address is not touched.
 */

import { flushSync } from "react-dom";

import { forgetAsked } from "./asked";
import { noteKeeps } from "./recent";
import { notePutAway } from "./who";

type Listener = () => void;

/** True from when the browser puts the page away until it shows it again. */
let away = false;
let watching = false;
const listeners = new Set<Listener>();

function say(next: boolean): void {
  if (next === away) return;
  away = next;
  for (const listener of [...listeners]) listener();
}

function letGo(): void {
  notePutAway();
  forgetAsked();
  noteKeeps(null);
  say(true);
}

/**
 * Watches for the browser putting the page away, and showing it again. It is asked for by
 * whatever holds something of an account, and watches once however often it is asked.
 */
export function watchForAway(): void {
  if (watching || typeof window === "undefined") return;
  watching = true;
  window.addEventListener("pagehide", (event) => {
    // Only a page that the browser keeps is shown again as it stood. One that it lets go of is loaded anew.
    if (!event.persisted) return;
    // At once, and not when the page next has a moment: what is drawn now is what the browser keeps.
    flushSync(letGo);
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) say(false);
  });
}

export function isAway(): boolean {
  return away;
}

export function subscribeToAway(listener: Listener): () => void {
  watchForAway();
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** For tests only: a page that was never put away. */
export function forgetAway(): void {
  away = false;
  listeners.clear();
}
