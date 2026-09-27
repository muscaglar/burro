/**
 * The column of names: what stands in it, and how a style sheet is told.
 *
 * In a result each thing is a line: what it is, where the area sits on it, drawn as five
 * steps, and what that means in words. The steps of every line stand in one column, so
 * that the eye runs down them: in every line of a result, and from one result to the next.
 * So the names before them have a column of one width, which is as wide as the longest
 * name needs and no wider than it can be given.
 *
 * A style sheet cannot be told how wide a name is. It is told the names, and lays each of
 * them in the column of every line, where none is drawn and none is heard: so the column
 * is as wide in one line as in the next. The names are the service's, of the vibes that
 * are drawn, and are handed over in one declaration, of which a name can be no more than a
 * word. It is plain code with no state.
 */

import type { CSSProperties } from "react";

import type { StripMark, Tag } from "@/lib/api/schema";

/**
 * The name of each vibe that any of the strips draws, once, in the order it is first met.
 * A vibe the release does not name has none, and is drawn by no strip.
 */
export function namesOf(
  strips: readonly (readonly Pick<StripMark, "tag_id">[])[],
  tags: readonly Pick<Tag, "tag_id" | "label">[],
): readonly string[] {
  const names: string[] = [];
  for (const strip of strips) {
    for (const mark of strip) {
      const name = tags.find((tag) => tag.tag_id === mark.tag_id)?.label;
      if (name !== undefined && !names.includes(name)) names.push(name);
    }
  }
  return names;
}

/** A sign of a name as a string of a style sheet holds it: by its number, where it would end or break the string. */
const asASign = (sign: string) => `\\${sign.codePointAt(0)?.toString(16)} `;

/**
 * The lines as one string of a style sheet, each on a line of its own. A line is the
 * service's, so nothing in it is taken for more than a word: what would end the string or
 * begin an escape is written by its number, and what would break a line is a space.
 */
export function asLines(lines: readonly string[]): string {
  const written = lines.map((line) => line.replace(/\s+/g, " ").replace(/["\\]/g, asASign));
  return `"${written.join("\\a ")}"`;
}

/** What else stands in the column of names: a label on a board, as what a sentence of a result is. */
export interface Beside {
  /** The words of the label. */
  readonly says: string;
  /**
   * The room its board has about its words, in art pixels: its edge, the room inside it,
   * and a mark before the words where it has one. It is a whole number, and none or more.
   */
  readonly more: number;
}

interface Stands {
  /** The names that stand in the column: of every vibe that is drawn where the column runs. */
  readonly names?: readonly string[];
  /** What is said once over a run of names, in the column: "Asked for". */
  readonly groups?: readonly string[];
  /** What else stands in the column, which has room of its own about it: two at the most. */
  readonly beside?: readonly Beside[];
}

/** A count of art pixels, as a style sheet multiplies by it: a whole number, and none or more. */
const counted = (more: number) => String(Number.isInteger(more) && more > 0 ? more : 0);

/** What a style sheet reads of the column, as the custom properties of whatever holds it. What is left out is not set. */
export function withThePlaceOf({ names, groups, beside = [] }: Stands): CSSProperties {
  const [one, two] = beside;
  return {
    ...(names === undefined ? {} : { "--names": asLines(names) }),
    ...(groups === undefined ? {} : { "--groups": asLines(groups) }),
    ...(one === undefined ? {} : { "--beside-1": asLines([one.says]), "--beside-1-more": counted(one.more) }),
    ...(two === undefined ? {} : { "--beside-2": asLines([two.says]), "--beside-2-more": counted(two.more) }),
  } as CSSProperties;
}
