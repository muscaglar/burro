/**
 * What a call to the API comes back as: an answer, or a failure that says why.
 *
 * A call never throws. A failure holds codes and fixed words from the API,
 * and never anything that was sent.
 */

import type { ErrorCode, FieldProblem, Meta } from "./schema";

/**
 * Why a call gave no answer, when the reason is not the API's own.
 *
 * - `timeout`: the website stopped waiting.
 * - `aborted`: the caller stopped it, as "Stop" does.
 * - `offline`: the browser says it has no connection.
 * - `network`: the request could not leave, or no answer came back.
 * - `not_configured`: no address is set for the API.
 * - `unreadable`: an answer came back that is not the API's envelope.
 */
export type ClientFailureKind =
  | "timeout"
  | "aborted"
  | "offline"
  | "network"
  | "not_configured"
  | "unreadable";

/** The API's error envelope, as a value. `message` is the API's fixed text for the code. */
export interface ApiFailure {
  readonly kind: "api";
  readonly status: number;
  readonly code: ErrorCode;
  readonly message: string;
  readonly fields: readonly FieldProblem[];
  readonly meta: Meta;
  readonly synthetic: boolean;
  /** `X-Request-Id`, to quote when reporting a fault. */
  readonly requestId: string | null;
}

export interface ClientFailure {
  readonly kind: ClientFailureKind;
  /** The status of the answer, where one came back. */
  readonly status: number | null;
  /** What the answer said of the data, where it said anything. */
  readonly synthetic: boolean | null;
  readonly requestId: string | null;
}

export type Failure = ApiFailure | ClientFailure;

export interface Success<Data> {
  readonly ok: true;
  readonly status: number;
  readonly meta: Meta;
  readonly data: Data;
  /** True if the body or the header says the data is made up. */
  readonly synthetic: boolean;
  readonly requestId: string | null;
}

export interface Failed {
  readonly ok: false;
  readonly failure: Failure;
}

export type Answer<Data> = Success<Data> | Failed;

export function isApiFailure(failure: Failure): failure is ApiFailure {
  return failure.kind === "api";
}

/** True when the API answered with this code. */
export function hasCode(answer: Answer<unknown>, code: ErrorCode): boolean {
  return !answer.ok && isApiFailure(answer.failure) && answer.failure.code === code;
}

export function failed(
  kind: ClientFailureKind,
  seen: { status?: number; synthetic?: boolean | null; requestId?: string | null } = {},
): Failed {
  return {
    ok: false,
    failure: {
      kind,
      status: seen.status ?? null,
      synthetic: seen.synthetic ?? null,
      requestId: seen.requestId ?? null,
    },
  };
}
