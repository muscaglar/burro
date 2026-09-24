"use client";

import { FAILURE, NOTICE, PROMPT } from "@/content/search";
import type { Failure } from "@/lib/api/failure";
import type { Operations } from "@/lib/api/schema";
import { isStale, type Repair } from "@/lib/search/repairs";

import styles from "./ErrorBlock.module.css";

interface Props {
  readonly failure: Failure;
  /** True when results from before the failure are still on screen. */
  readonly notUpdated: boolean;
  readonly repairs?: readonly Repair[];
  /** The name of what a repair takes out, by its part, where one is in hand. */
  readonly nameOf?: (key: string) => string | null;
  readonly onRetry: () => void;
  readonly onStartAgain: () => void;
  readonly onEdit: (operations: Operations) => void;
}

/** What is said of a failure: the API's own words for it, or site copy where the failure is not the API's. */
export function wordsFor(failure: Failure): string {
  if (failure.kind === "api") return isStale(failure) ? NOTICE.stale : failure.message;
  return FAILURE[failure.kind];
}

/**
 * Says that a call failed, in words, and what can be done. It is an alert,
 * so a screen reader says it at once.
 *
 * It shows the API's fixed text, and the id of the request to quote. It
 * shows nothing that was sent, because it is given nothing that was sent.
 */
export function ErrorBlock({
  failure,
  notUpdated,
  repairs = [],
  nameOf = () => null,
  onRetry,
  onStartAgain,
  onEdit,
}: Props) {
  const what = { place: NOTICE.thePlace, area: NOTICE.theArea, setting: NOTICE.theSetting };
  return (
    <div className={styles.error} role="alert">
      <p className={styles.message}>{wordsFor(failure)}</p>
      {notUpdated ? <p>{NOTICE.notUpdated}</p> : null}
      {failure.requestId !== null ? (
        <p className={styles.request}>
          {NOTICE.requestId} <code>{failure.requestId}</code>
        </p>
      ) : null}
      <div className={styles.actions}>
        {repairs.map((repair) => (
          <button
            key={repair.key}
            type="button"
            className="target"
            onClick={() => onEdit(repair.operations)}
          >
            {NOTICE.takeOut(nameOf(repair.key) ?? what[repair.what])}
          </button>
        ))}
        <button type="button" className="target" onClick={onRetry}>
          {PROMPT.tryAgain}
        </button>
        <button type="button" className="target" onClick={onStartAgain}>
          {PROMPT.startAgain}
        </button>
      </div>
    </div>
  );
}
