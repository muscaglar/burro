/**
 * What a chip says, in the row and in full. It is plain code with no state, kept apart from
 * the chip so that what draws the words and what lays the row out read them one way.
 *
 * In the row a chip says what was said, and says once that the rest was assumed. In full it
 * says every part of itself, and which of them nobody chose.
 */

import { CHIPS } from "@/content/search";
import type { Chip, ChipPart } from "@/lib/search/chips";

export interface Said {
  readonly label: string;
  /** True where the word "assumed" stands after the name: the chip as a whole was assumed and no one part of it, or the thing itself was taken for the person. */
  readonly whole: boolean;
  /** The parts that are said, in the order the chip holds them. */
  readonly parts: readonly ChipPart[];
  /** True where parts nobody said are left out, and are said once: "rest assumed". */
  readonly rest: boolean;
}

export function saidBy(chip: Pick<Chip, "label" | "parts" | "assumed" | "taken">, full: boolean): Said {
  const some = chip.parts.some((part) => part.assumed);
  // A word that was read one way of two is said in the row as well.
  const unsaid = chip.parts.filter((part) => part.assumed && part.always !== true);
  // One part that nobody said is named, with the word "assumed" on it and on nothing else:
  // "rest assumed" stood beside the very words the person typed, and read as if they were.
  const named = !full && unsaid.length === 1;
  return {
    label: chip.label,
    // A thing that was taken for the person says so after its name, whatever its parts say.
    whole: chip.taken === true || (chip.assumed && !some),
    parts: full || named ? chip.parts : chip.parts.filter((part) => !part.assumed || part.always === true),
    rest: !full && !named && unsaid.length > 0,
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
