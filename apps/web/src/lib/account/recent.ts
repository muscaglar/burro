/**
 * Whether a person lets Burro keep their last searches, as the service last said, and
 * whether the search that stands on the search page is theirs to have kept.
 *
 * The search page asks here before it sends a search to be kept among the last ones, so
 * that nothing of a search is sent to be kept where the person has not let it be. It is
 * held in memory while the page is open in this tab, and is `null` until the service has
 * said, and again once nobody is signed in.
 *
 * A search is kept among the last ones of the person who was signed in as it was made,
 * and of nobody else. The search of a tab outlasts whoever made it: it stands until the
 * tab is closed, while one person signs out and another signs in. Sent to be kept for
 * whoever is signed in now, it would put where one person must get to into the account of
 * another. And a person who was not signed in was told that a search is gone as the page
 * is closed, so theirs is kept for nobody who signs in after.
 */

type Listener = () => void;

let keeps: boolean | null = null;
const listeners = new Set<Listener>();

/**
 * The ranking that stands, and whether it is of whoever is signed in. It holds nothing of
 * who they are: that somebody was signed in as it was first seen, and that nobody has
 * taken their place since.
 */
let stands: { readonly ranking: object; readonly theirs: boolean } | null = null;

/** Told what the service said: by the preferences of an account, by the list of the last searches, or by a tick. */
export function noteKeeps(next: boolean | null): void {
  if (next === keeps) return;
  keeps = next;
  for (const listener of [...listeners]) listener();
}

export function keepsRecent(): boolean | null {
  return keeps;
}

export function subscribeToKeeps(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Told of the ranking that stands, as the search page first sees it, and whether somebody is signed in. */
export function noteStands(ranking: object, signedIn: boolean): void {
  if (stands?.ranking !== ranking) stands = { ranking, theirs: signedIn };
}

/** Told that who is signed in has changed. What stands was made before they were, so it is not theirs. */
export function noteMadeBefore(): void {
  if (stands?.theirs === true) stands = { ranking: stands.ranking, theirs: false };
}

/** True where the ranking is of a search that whoever is signed in made while they were signed in. */
export function isTheirs(ranking: object): boolean {
  return stands?.ranking === ranking && stands.theirs;
}

/** For tests only: a page on which no search stands. */
export function forgetStands(): void {
  stands = null;
}
