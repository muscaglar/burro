/**
 * Which part of the search each refused edit was about, so that the reason
 * can be said beside the control or the chip it concerns.
 */

import type { Operations, Rejected, RejectReason } from "@/lib/api/schema";

import { saidBy, type ChipKey } from "./edits";
import type { Read, Refused } from "./state";

export interface Refusal {
  /** The part the edit was about. `null` when the edit names none. */
  readonly key: ChipKey | null;
  readonly reason: RejectReason;
}

function refusalsOf(operations: Operations, rejected: readonly Rejected[]): Refusal[] {
  return rejected.map(({ group, index, reason }) => ({
    key: saidBy(operations, group, index)[0]?.key ?? null,
    reason,
  }));
}

/**
 * Every edit that was not applied: the ones a sentence made, and the ones a
 * control made since. An edit that a question is being asked about is left
 * out, because the question stands for it.
 */
export function refusals(read: Read | null, refused: Refused | null): readonly Refusal[] {
  const fromWords =
    read === null
      ? []
      : refusalsOf(
          read.operations,
          read.rejected.filter(
            (refusal) =>
              !read.clarify.some(
                (asked) => asked.group === refusal.group && asked.index === refusal.index,
              ),
          ),
        );
  const fromControls = refused === null ? [] : refusalsOf(refused.operations, refused.rejected);
  return [...fromWords, ...fromControls];
}

/** A thing that was asked for and that the data does not hold, as the page names it under the box. */
export interface Missing {
  /** `budget`, `commute`, `feature:<id>` or `tag:<id>`, as the API names the target of a suggestion. */
  readonly target: string;
  /** The API's label for it. */
  readonly label: string;
}

/** The target an edit of a control was about, from the key of its chip. */
function targetOf(key: ChipKey | null): string | null {
  if (key === null) return null;
  if (key === "budget") return "budget";
  if (key === "journeys" || key.startsWith("place:")) return "commute";
  return key.startsWith("tag:") || key.startsWith("feature:") ? key : null;
}

/**
 * Everything that was asked for and that the data holds for no area, each thing once:
 * what the API named of the words that were read, and what a control asked for since
 * and was turned away as not in the release.
 */
export function missingFrom(
  read: Read | null,
  refused: Refused | null,
  nameOf: (key: string) => string | null,
): readonly Missing[] {
  const found = new Map<string, Missing>();
  for (const { target, label } of read?.not_in_release ?? []) found.set(target, { target, label });
  const fromControls = refused === null ? [] : refusalsOf(refused.operations, refused.rejected);
  for (const { key, reason } of fromControls) {
    const target = reason === "not_in_release" ? targetOf(key) : null;
    if (target !== null && !found.has(target)) found.set(target, { target, label: nameOf(key ?? "") ?? "" });
  }
  return [...found.values()];
}

/** True when a refusal is one the page says under the box, as a thing the data does not hold. */
export function isSaidAsMissing(refusal: Refusal, missing: readonly Missing[]): boolean {
  if (refusal.reason !== "not_in_release") return false;
  // An edit that names no part is a budget's or a journey's, which the API names by its target.
  const target = targetOf(refusal.key);
  return target === null ? missing.length > 0 : missing.some((one) => one.target === target);
}

/** The reasons by part, for the controls. Only what a control sent is said at the control. */
export function refusedByPart(refused: Refused | null): ReadonlyMap<string, RejectReason> {
  const byPart = new Map<string, RejectReason>();
  if (refused === null) return byPart;
  for (const { key, reason } of refusalsOf(refused.operations, refused.rejected)) {
    if (key !== null) byPart.set(key, reason);
  }
  return byPart;
}
