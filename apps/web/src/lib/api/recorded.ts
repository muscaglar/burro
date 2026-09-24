/**
 * Reads the answers recorded from the real API, in `test/recorded/`.
 *
 * A test reads them in place of a server, and so does a build when no address
 * is set for the API. They are written by `test/record.py` and never edited.
 * This file reads from disk, so it is for tests and for the server only.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import type { EnvelopeOf, OperationId } from "./operations";
import type { ErrorEnvelope } from "./schema";

export interface Recorded<Body = unknown> {
  readonly scenario: string;
  /** What the scenario is there to show, in a line. */
  readonly shows: string;
  /** False for a file made by hand. There is none, and a test says so. */
  readonly captured: boolean;
  readonly request: {
    /** `null` for a request to a path that is no route. */
    readonly operation_id: OperationId | "healthz" | null;
    readonly method: "GET" | "POST";
    /** The route as the contract writes it, with its parameter unfilled. */
    readonly route: string;
    readonly path: string;
    readonly body?: unknown;
  };
  readonly status: number;
  readonly headers: Readonly<Record<string, string>>;
  readonly body: Body;
}

/** A scenario is a file name with no ending, or one inside the `area` folder. */
const SCENARIO = /^[a-z0-9]+(-[a-z0-9]+)*(\/[a-z0-9]+(-[a-z0-9]+)*)?$/;

export function recordedFolder(): string {
  return path.join(process.cwd(), "test", "recorded");
}

/** The recording of a scenario, or `null` when there is none of that name. */
export function findRecorded(scenario: string): Recorded | null {
  // A name that is not a scenario's could climb out of the folder.
  if (!SCENARIO.test(scenario)) return null;
  try {
    const text = readFileSync(path.join(recordedFolder(), `${scenario}.json`), "utf8");
    return JSON.parse(text) as Recorded;
  } catch {
    return null;
  }
}

export function readRecorded(scenario: string): Recorded {
  const found = findRecorded(scenario);
  if (found === null) throw new Error(`There is no recorded answer named ${scenario}.`);
  return found;
}

/**
 * The recorded answer of an operation that went well, with the type the
 * contract gives it. It checks that the recording is of that operation, so
 * the type cannot be claimed for another route's answer.
 */
export function recordedAnswer<Op extends OperationId>(
  operation: Op,
  scenario: string,
): Recorded<EnvelopeOf<Op>> {
  const found = readRecorded(scenario);
  if (found.request.operation_id !== operation || found.status !== 200) {
    throw new Error(`The recording ${scenario} is not an answer of ${operation} that went well.`);
  }
  return found as Recorded<EnvelopeOf<Op>>;
}

/** A recorded error, in the API's error envelope. */
export function recordedError(scenario: string): Recorded<ErrorEnvelope> {
  const found = readRecorded(scenario);
  const body = found.body as { error?: unknown } | null;
  if (found.status < 400 || typeof body?.error !== "object" || body.error === null) {
    throw new Error(`The recording ${scenario} is not an error.`);
  }
  return found as Recorded<ErrorEnvelope>;
}

/** A `Response` holding a recording, for a test to answer a `fetch` with. */
export function responseFrom(recorded: Recorded): Response {
  return new Response(JSON.stringify(recorded.body), {
    status: recorded.status,
    headers: recorded.headers,
  });
}
