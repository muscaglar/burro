"use client";

import { FAILURE, NOTICE, PROMPT } from "@/content/search";
import type { Failure } from "@/lib/api/failure";
import type { Operations } from "@/lib/api/schema";
import { isStale, type Repair } from "@/lib/search/repairs";

import { Press } from "../kit/Press/Press";
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
  // An answer that is not the API's own has no words to show, and its status says why none
  // came: said to be an answer the page could not understand, it sent a person to try
  // again at once, which is what an answer of 429 refuses.
  if (failure.kind === "unreadable" && failure.status === 429) return FAILURE.busy;
  if (failure.kind === "unreadable" && failure.status !== null && failure.status >= 500) return FAILURE.fault;
  return FAILURE[failure.kind];
}

/**
 * Says that a call failed, in words, and what can be done. It is an alert,
 * so a screen reader says it at once.
 *
 * It shows the API's fixed text, and the id of the request to quote. It
 * shows nothing that was sent, because it is given nothing that was sent.
 *
 * What can be done is a row of buttons. None is the button that matters most in sight,
 * which is the one that sends a search. The one that starts again keeps nothing, and is
 * drawn as what takes away is drawn.
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
          // It names what it takes out, which is a name the service gives and may be long: it is read.
          <Press key={repair.key} reads onPress={() => onEdit(repair.operations)}>
            {NOTICE.takeOut(nameOf(repair.key) ?? what[repair.what])}
          </Press>
        ))}
        <Press onPress={onRetry}>{PROMPT.tryAgain}</Press>
        <Press kind="stop" onPress={onStartAgain}>
          {PROMPT.startAgain}
        </Press>
      </div>
    </div>
  );
}
