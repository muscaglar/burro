/**
 * Whether any answer, since the page was opened, has said the data is made up.
 *
 * A page is built on one release and may be read while the API serves
 * another. The banner must show as soon as either says the data is made up,
 * so every answer is heard here. It is held in memory, and it only ever turns on.
 */

type Listener = () => void;

let seen = false;
const listeners = new Set<Listener>();

export function noteSynthetic(synthetic: boolean): void {
  if (!synthetic || seen) return;
  seen = true;
  for (const listener of listeners) listener();
}

export function syntheticSeen(): boolean {
  return seen;
}

export function subscribeToSynthetic(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** For tests only: a page that has heard nothing yet. */
export function forgetSynthetic(): void {
  seen = false;
}
