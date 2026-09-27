/**
 * How the chips lie where the row is narrow, as on a phone. It is plain code with no
 * state, and it measures nothing: it is run where the page is built as it is in a browser.
 *
 * A chip has its thing at one end and a cross 44 px square at the other, so on a phone two
 * chips stand side by side only where both say little. Left to wrap as they fall, the
 * chips of a plain search took six rows, and the first result left the first screen. So
 * two chips that follow one another share a row where they fit, and where one of them
 * must set its words on two lines to fit, that one gives way. Every other chip has a row
 * to itself.
 *
 * Room is counted in letters of the reading face, which is near enough. Where the count is
 * wrong the second chip of two goes to a row of its own: a chip that keeps its width is
 * never made narrower than its words, so no word is broken to make a pair.
 */

export interface Sized {
  /** What the chip says, as one line. */
  readonly words: string;
  /** True where it has a cross, which takes it off. */
  readonly cross: boolean;
  /** True where it has a second button, which turns a scale. */
  readonly turn: boolean;
  /** True where it must have a row to itself whatever it says, as a chip that is open has. */
  readonly alone?: boolean;
}

/**
 * How a chip lies in a narrow row. `alone`: it has the row. `fills`: it shares the row, as
 * wide as its words and what is left over. `keeps`: it shares the row as wide as its words,
 * beside one that gives way. `gives`: it shares the row, and its words may run to a second
 * line to let the other in.
 */
export type Lies = "alone" | "fills" | "keeps" | "gives";

export interface Laid {
  readonly lies: Lies;
  /** How many buttons stand beside its words. */
  readonly beside: number;
  /** The longer of its two lines, in letters, where its words are set on two. */
  readonly letters: number;
  /** Which row it stands in, counted from the first, which is 1. Two that share a row stand in one. */
  readonly row: number;
}

/**
 * How many letters a narrow row holds from edge to edge. A phone 390 wide holds 44 at the
 * size a chip's words are set there: two fewer are counted on, for a phone that is narrower.
 */
export const NARROW_ROW = 42;

/** The width a row is narrow from, in rem. It is the width the style sheet lays a narrow row out by. */
export const NARROW_REM = 26;

/**
 * How many rows of chips stand over the answer on a narrow row. Up to `most` of them, every
 * chip is in sight. With more, the chips fold to `folded` rows and a line that opens the
 * rest and says how many it holds: a search of seven things stood in six rows, and its
 * first result began at 590 of 844.
 *
 * These two figures choose. `most` was 4 until a chip came to say every part that was
 * taken: the chip of a journey then took three lines, a plain search stood in four rows
 * that were higher than before, and its first result ended 9 px under the first screen of
 * a phone 390 by 844. With `most` at 3 a plain search folds: three of its five chips stand
 * in sight, and its first result stands from 394 to 777, whole. Measured on 2026-09-27.
 */
export const NARROW_ROWS = { most: 3, folded: 2 } as const;

/** What a chip takes beside its words, in letters: its edge, its thing and the room round them. And each button. */
const ROOM = { chip: 8, button: 6, between: 1 } as const;

/** The longer of the two lines, where the words are set on two as evenly as their spaces allow. */
function onTwoLines(words: string): number {
  const parts = words.trim().split(/\s+/);
  let best = words.trim().length;
  for (let at = 1; at < parts.length; at += 1) {
    const above = parts.slice(0, at).join(" ").length;
    const below = parts.slice(at).join(" ").length;
    best = Math.min(best, Math.max(above, below));
  }
  return best;
}

const besideOf = (chip: Sized) => (chip.cross ? 1 : 0) + (chip.turn ? 1 : 0);
const beyondWords = (chip: Sized) => ROOM.chip + besideOf(chip) * ROOM.button;

/** The room a chip takes with its words on one line, in letters. */
export function roomOf(chip: Sized): number {
  return beyondWords(chip) + chip.words.trim().length;
}

/** The least room it takes with its words on two lines. */
export function leastRoomOf(chip: Sized): number {
  return beyondWords(chip) + onTwoLines(chip.words);
}

/** How two chips that follow one another share a row, or `null` where they do not fit on one. */
function together(one: Sized, next: Sized): readonly [Lies, Lies] | null {
  if (one.alone === true || next.alone === true) return null;
  const fits = (first: number, second: number) => first + ROOM.between + second <= NARROW_ROW;
  if (fits(roomOf(one), roomOf(next))) return ["fills", "fills"];
  // One of the two gives way: the second where it can, since what a person reads first is
  // then whole. A chip of one word cannot give way, and is never asked to.
  if (leastRoomOf(next) < roomOf(next) && fits(roomOf(one), leastRoomOf(next))) return ["keeps", "gives"];
  if (leastRoomOf(one) < roomOf(one) && fits(leastRoomOf(one), roomOf(next))) return ["gives", "keeps"];
  if (leastRoomOf(one) < roomOf(one) && leastRoomOf(next) < roomOf(next) && fits(leastRoomOf(one), leastRoomOf(next))) {
    return ["gives", "gives"];
  }
  return null;
}

/**
 * How each chip lies, in the order they stand in. They share in twos: a chip shares with
 * the one after it, or has a row to itself, so that the order a person reads them in is
 * the order they were drawn in, and no row is left half empty.
 */
export function lying(chips: readonly Sized[]): Laid[] {
  const lies: Lies[] = chips.map(() => "alone");
  let at = 0;
  while (at < chips.length) {
    const [one, next] = [chips[at], chips[at + 1]];
    const shared = one === undefined || next === undefined ? null : together(one, next);
    if (shared !== null) {
      lies[at] = shared[0];
      lies[at + 1] = shared[1];
    }
    at += shared === null ? 1 : 2;
  }
  // A chip that is the second of two stands in the row of the first: they share in twos,
  // in the order they stand in, so the second follows the first directly.
  let row = 0;
  let second = false;
  return chips.map((chip, index) => {
    const how = lies[index] ?? "alone";
    if (how === "alone" || !second) row += 1;
    second = how !== "alone" && !second;
    return { lies: how, beside: besideOf(chip), letters: onTwoLines(chip.words), row };
  });
}

/**
 * How many of the chips stand in sight on a narrow row, counted from the first of them:
 * every one where they stand in few rows enough, and else those of the first rows. What
 * is not in sight is one press away, and nothing of it is lost.
 */
export function inSight(laid: readonly Laid[], rows: { readonly most: number; readonly folded: number } = NARROW_ROWS): number {
  const last = laid.at(-1)?.row ?? 0;
  return last <= rows.most ? laid.length : laid.filter((one) => one.row <= rows.folded).length;
}

/**
 * How many rows of chips stand over the answer on a wide row, as `NARROW_ROWS` says it of
 * a narrow one. Up to `most` of them, every chip of the row is in sight: measured at 1440
 * by 900, the five chips of a plain search stand in three rows, and its first result
 * begins at 687 of 900. With more, the chips fold to `folded` rows and the line that opens
 * the rest, which is three rows again: Burro takes what it noticed in a sentence of
 * itself, and after a sentence of a dozen things six chips stood in five rows, and the
 * first result began at 909 of 900, out of sight.
 */
export const WIDE_ROWS = { most: 3, folded: 2 } as const;

/**
 * How many of the chips stand in sight on a wide row, counted from the first of them, by
 * where each stands from the top of the row once the row is laid out. A wide row lays its
 * chips as they fall, as many to a row as fit, so how they lie is read and not counted.
 */
export function standing(
  tops: readonly number[],
  rows: { readonly most: number; readonly folded: number } = WIDE_ROWS,
): number {
  const stand = [...new Set(tops)].sort((one, other) => one - other);
  if (stand.length <= rows.most) return tops.length;
  const last = stand[rows.folded - 1] ?? Number.POSITIVE_INFINITY;
  return tops.filter((top) => top <= last).length;
}
