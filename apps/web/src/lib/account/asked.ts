/**
 * What a link was last asked for, so that the page which says a link was sent can say
 * where to: the address, as the person typed it, and how long the service says a link
 * works for.
 *
 * It is held in memory, for as long as the page is open in this tab. It is in no address,
 * in nothing the browser keeps and in no line of the console, and it goes when the page
 * is loaded again: the page then says "the address you gave". It is shown to the person
 * who typed it, so that an address typed wrongly is seen, and to nobody else.
 */

export interface Asked {
  /** The address a link was asked for, as it was typed. */
  readonly email: string;
  /** How long the link works for, in minutes, as the service said. */
  readonly minutes: number;
}

type Listener = () => void;

let asked: Asked | null = null;
const listeners = new Set<Listener>();

function say(next: Asked | null): void {
  asked = next;
  for (const listener of [...listeners]) listener();
}

/** Told that a link was asked for, by the answer that said so. */
export function noteAsked(next: Asked): void {
  say(next);
}

/** Told to let go of it: the person signed in, or asks for a link to another address. */
export function forgetAsked(): void {
  if (asked !== null) say(null);
}

export function whatWasAsked(): Asked | null {
  return asked;
}

export function subscribeToAsked(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
