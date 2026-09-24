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

/** The reasons by part, for the controls. Only what a control sent is said at the control. */
export function refusedByPart(refused: Refused | null): ReadonlyMap<string, RejectReason> {
  const byPart = new Map<string, RejectReason>();
  if (refused === null) return byPart;
  for (const { key, reason } of refusalsOf(refused.operations, refused.rejected)) {
    if (key !== null) byPart.set(key, reason);
  }
  return byPart;
}
