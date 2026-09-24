/**
 * Room for the case for other names, on the page of vibes. The name of a vibe
 * and of each of its ends is the engine's, and is the founder's to choose.
 * Where another name was weighed for one, it may be set down here, under the
 * id of the vibe, with the case for it in three lines at most. The page of
 * vibes draws it under the name the engine gives.
 *
 * It holds no vibe: a name here changes nothing the engine does, and one set
 * down for a vibe the release does not carry is not drawn. It is empty until
 * the cases are written.
 */

export interface OtherName {
  /** The name that was weighed, and for a scale the names of its two ends. */
  readonly name: string;
  /** The case for it, in three lines at most. */
  readonly lines: readonly string[];
}

/** The most lines a case is made in. */
export const CASE_LINES = 3;

/** The other names weighed for each vibe, by the id of the vibe. */
export const OTHER_NAMES: Readonly<Record<string, readonly OtherName[]>> = {};
