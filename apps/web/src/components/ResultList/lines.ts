/**
 * The lines of a result, as it is first shown: which of the vibes the service gave with
 * the result are drawn, what was asked for and has no figure, and which names stand in the
 * column of names of a list. It is plain code with no state.
 *
 * A result holds a line for each thing that was asked for, and no more: a person who
 * walked the website asked for less on it. The vibes nobody asked for, of which the
 * service gives two at the most, are in the working of the result.
 */

import type { MetaData, PreferenceSpec, RankedArea, StripMark } from "@/lib/api/schema";

import { namesOf } from "../Strip/column";
import type { FitSaid, OthersStand } from "./look";
import { thingsLacked } from "./parts";

/** What a result draws of its area, line by line. */
export interface Lines {
  /** The marks that are drawn, in the order the service gave them. */
  readonly marks: readonly StripMark[];
  /** The vibes that were asked for and could not be worked out for the area, by their ids. */
  readonly unplaced: readonly string[];
  /** What else was asked for that the area has no figure for. */
  readonly lacked: ReturnType<typeof thingsLacked>["others"];
}

/**
 * The lines of one result. The marks are those that were asked for, and every mark the
 * service gave where no vibe was asked for, so that a result is never without a gauge:
 * unless the look has the others stand beside what was asked for, or on no result. What
 * has no figure has a line only where what a fit is based on is said in the working: said
 * in full on the result, the sentence names it.
 */
export function linesOf(
  area: Pick<RankedArea, "strip" | "contributions">,
  meta: Pick<MetaData, "features" | "tags">,
  spec: Pick<PreferenceSpec, "weights">,
  others: OthersStand,
  fitSaid: FitSaid,
): Lines {
  const { vibes, others: lacked } = thingsLacked(area, meta, spec);
  const asked = area.strip.filter((mark) => mark.asked);
  const alone = others === "never" || (others === "alone" && (asked.length > 0 || vibes.length > 0));
  const inShort = fitSaid === "working";
  return { marks: alone ? asked : area.strip, unplaced: inShort ? vibes : [], lacked: inShort ? lacked : [] };
}

/**
 * Every name that stands in the column of names of a list: of each line that a result of
 * the ranking draws, once, in the order it is first met. The column is then as wide in
 * one result as in the next, and no wider than the names that are drawn ask for.
 */
export function columnOf(
  ranked: readonly Pick<RankedArea, "strip" | "contributions">[],
  meta: Pick<MetaData, "features" | "tags">,
  spec: Pick<PreferenceSpec, "weights">,
  others: OthersStand,
  fitSaid: FitSaid,
): readonly string[] {
  const lines = ranked.map((area) => linesOf(area, meta, spec, others, fitSaid));
  const unplaced = lines.flatMap((one) => one.unplaced).flatMap((id) => meta.tags.find((tag) => tag.tag_id === id)?.label ?? []);
  const lacked = lines.flatMap((one) => one.lacked.map(({ name }) => name));
  return [...new Set([...namesOf(lines.map((one) => one.marks), meta.tags), ...unplaced, ...lacked])];
}
