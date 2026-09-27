/**
 * What a chip says, in the row and in full. It is plain code with no state, kept apart from
 * the chip so that what draws the words and what lays the row out read them one way.
 *
 * A chip says what was taken, and marks what was assumed of it: every part of itself, with
 * the word "assumed" on each part that nobody said. It says so in the row as it does in
 * full, so that nothing of a search waits for a press to be read: least of all whether a
 * limit is firm, which decides which areas are left out.
 */

import { CHIPS } from "@/content/search";
import type { Chip, ChipPart } from "@/lib/search/chips";

/**
 * What a chip says in the row of the parts that nobody said. It is the founder's to choose.
 *
 * `each`: every part, with the word "assumed" on each that nobody said, as it says them in
 * full. `rest`: what was said, and once that the rest was assumed, as it was: the parts
 * nobody said are one press away. Whether a limit is firm is said in the row either way.
 * It is shorter where two parts or more were assumed beside that, and says less: a journey
 * that Burro gave its minutes says "flexible assumed, Burro assumed the rest", and not how
 * many minutes those are.
 */
export type InTheRow = "each" | "rest";

export const WAYS_IN_THE_ROW: readonly InTheRow[] = ["each", "rest"];

/** This is the one line that chooses. */
export const IN_THE_ROW: InTheRow = "each";

export interface Said {
  readonly label: string;
  /** True where the word "assumed" stands after the name: the chip as a whole was assumed and no one part of it, or the thing itself was taken for the person. */
  readonly whole: boolean;
  /** The parts that are said, in the order the chip holds them. */
  readonly parts: readonly ChipPart[];
  /** True where parts nobody said are left out, and are said once: "rest assumed". */
  readonly rest: boolean;
}

export function saidBy(
  chip: Pick<Chip, "label" | "parts" | "assumed" | "taken">,
  full: boolean,
  row: InTheRow = IN_THE_ROW,
): Said {
  const some = chip.parts.some((part) => part.assumed);
  // What is left for a press, where the look has the row say less than the chip in full. A
  // part that is never left for one is said in the row, and one part alone is named: "rest
  // assumed" stood beside the very words the person typed, and read as if they were.
  const unsaid = full || row === "each" ? [] : chip.parts.filter((part) => part.assumed && part.always !== true);
  const left = unsaid.length > 1 ? unsaid : [];
  return {
    label: chip.label,
    // A thing that was taken for the person says so after its name, whatever its parts say.
    whole: chip.taken === true || (chip.assumed && !some),
    parts: chip.parts.filter((part) => !left.includes(part)),
    rest: left.length > 0,
  };
}

/** The same as one line, word for word as it is drawn. */
export function inOneLine(said: Said): string {
  return [
    said.label,
    said.whole ? ` ${CHIPS.assumed}` : "",
    ...said.parts.map((part) => `, ${part.text}${part.assumed ? ` ${CHIPS.assumed}` : ""}`),
    said.rest ? `, ${CHIPS.restAssumed}` : "",
  ].join("");
}
