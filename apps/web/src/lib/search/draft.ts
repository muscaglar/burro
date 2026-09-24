"use client";

import { useState } from "react";

/**
 * What a control shows between being changed and being answered.
 *
 * A control is drawn from the spec the API returned. When a person changes
 * it, it shows the new value at once, and keeps showing it until an answer
 * comes back. Then it is drawn from the returned spec again, whatever that
 * says: if the edit was refused, the control goes back.
 *
 * `version` is a number that changes with every answer.
 */
export function useDraft<Value>(
  value: Value,
  version: number,
): readonly [shown: Value, change: (next: Value) => void] {
  const [held, setHeld] = useState<{ version: number; draft: { value: Value } | null }>({
    version,
    draft: null,
  });
  // What was set before the last answer is passed over: the answer is what stands.
  const shown = held.version === version && held.draft !== null ? held.draft.value : value;
  return [shown, (next) => setHeld({ version, draft: { value: next } })];
}
