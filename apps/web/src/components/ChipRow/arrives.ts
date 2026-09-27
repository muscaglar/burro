/**
 * Which chips have this moment been added to the search, so that each drops into its place
 * once, and no chip that was there moves.
 *
 * A chip is known by its key, which is the search's own. What is held here is which keys
 * the row last drew, and which searches it has drawn: no word, and nothing that was typed.
 */

/** What the row last drew: the chips of the search, and those among them that had this moment been added. */
export interface Row {
  /** The key of every chip of the search that was drawn, whether it stood in sight or waited to be asked for. */
  readonly keys: readonly string[];
  /** Those that were not there the time before. */
  readonly fresh: ReadonlySet<string>;
}

const NONE: ReadonlySet<string> = new Set();

/**
 * The searches whose chips have been drawn, each known by being the very search the page
 * holds. A search that is drawn a second time, as when a person comes back to the page from
 * the page of an area, brings nothing new: its chips were there, and none of them drops.
 *
 * It is held here and not by the row, because the row is made anew each time the page is.
 * It keeps no search from being forgotten: what nothing else holds is let go.
 */
const drawn = new WeakSet<object>();

export const wasDrawn = (search: object): boolean => drawn.has(search);

export function nowDrawn(search: object): void {
  drawn.add(search);
}

/**
 * The row as it is first drawn. Every chip of a search that was not drawn before has this
 * moment been added: the whole of it arrives. A row that holds the place of chips that are
 * on their way has drawn none.
 */
export function begun(keys: readonly string[], before: boolean): Row {
  return { keys, fresh: before ? NONE : new Set(keys) };
}

const same = (one: readonly string[], other: readonly string[]) =>
  one.length === other.length && one.every((key, at) => key === other[at]);

/**
 * The row as it is drawn next. With the chips it had, it is the row it was. With others,
 * those it did not have arrive, and those it had stay where they are.
 */
export function following(row: Row, keys: readonly string[]): Row {
  if (same(row.keys, keys)) return row;
  const had = new Set(row.keys);
  return { keys, fresh: new Set(keys.filter((key) => !had.has(key))) };
}

/**
 * The row once one chip has dropped into its place: that chip is new no longer. Any other
 * that is still on its way goes on, so that a chip which was added a moment after another
 * is not cut short when the first lands.
 */
export function landed(row: Row, key: string): Row {
  if (!row.fresh.has(key)) return row;
  const fresh = new Set(row.fresh);
  fresh.delete(key);
  return { keys: row.keys, fresh: fresh.size === 0 ? NONE : fresh };
}

/** The row once a press has been made in it: nothing in it is new, whether or not it was seen to drop. */
export function settled(row: Row): Row {
  return row.fresh.size === 0 ? row : { keys: row.keys, fresh: NONE };
}
