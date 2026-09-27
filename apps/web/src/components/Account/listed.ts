"use client";

/**
 * What a box of the page of an account holds of the service: a list that is asked for as
 * the box is drawn, and is then what the service last said.
 *
 * It is held in memory while the page is open, and nowhere else. A failure is kept whole,
 * never as a yes or a no: its message and the id of its request are what a person reports.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import type { Answer, Failure } from "@/lib/api/failure";

export type Listed<Data> =
  /** Asked for, and not yet answered. */
  | { readonly kind: "opening" }
  | { readonly kind: "failed"; readonly failure: Failure }
  | { readonly kind: "listed"; readonly data: Data };

export interface Held<Data> {
  readonly listed: Listed<Data>;
  /**
   * Asks the service again. Asked quietly, what is held stays on the page until the answer
   * is in, so that nothing a person is using goes from under them, and a failure leaves
   * what was held where it was.
   */
  readonly ask: (quietly?: boolean) => Promise<void>;
  /** Puts what an answer brought in the place of what was held: the service gives the list back with what changed it. */
  readonly set: (data: Data) => void;
}

/** Asks for a list as the box is drawn, and holds what came. */
export function useListed<Data>(load: (signal?: AbortSignal) => Promise<Answer<Data>>): Held<Data> {
  const [listed, setListed] = useState<Listed<Data>>({ kind: "opening" });
  // The asking that is under way. An answer to one before it is let go.
  const latest = useRef(0);

  const ask = useCallback(
    async (quietly = false) => {
      latest.current += 1;
      const mine = latest.current;
      if (!quietly) setListed({ kind: "opening" });
      const answer = await load();
      if (mine !== latest.current) return;
      if (answer.ok) setListed({ kind: "listed", data: answer.data });
      // A call that was stopped has nothing to report.
      else if (answer.failure.kind !== "aborted" && !quietly) setListed({ kind: "failed", failure: answer.failure });
    },
    [load],
  );

  useEffect(() => {
    // Asked for once, as the box is first drawn: what it holds is the service's to say.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void ask();
    return () => {
      latest.current += 1;
    };
  }, [ask]);

  const set = useCallback((data: Data) => {
    latest.current += 1;
    setListed({ kind: "listed", data });
  }, []);

  return { listed, ask, set };
}
