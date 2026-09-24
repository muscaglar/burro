/**
 * Sends one request to the API and reads the answer. Shared by the browser's
 * client and by the build.
 *
 * It never throws, and it never writes anywhere but to the API: no log, no
 * console, no storage. What a person typed is in the body of a `POST` and in
 * no other place, the address included.
 */

import { failed, type Answer } from "./failure";
import { pathOf, ROUTES, type DataOf, type OperationId } from "./operations";
import { REQUIRED_IN_DATA } from "./required";
import type { ErrorBody, FieldProblem, Meta } from "./schema";

export interface SendSettings {
  /** The address of the API, with no slash at the end. `null` when none is set. */
  readonly baseUrl: string | null;
  /** The `fetch` to call with. A test passes its own. */
  readonly fetch?: typeof fetch;
  /** Told what each answer says of the data, as soon as it says it. */
  readonly onSynthetic?: (synthetic: boolean) => void;
  /** Settings added to every request, as a build adds how long a page may be kept. */
  readonly init?: RequestInit;
}

export interface SendRequest {
  readonly body?: unknown;
  /** The one value in the path, for the two routes that have one. */
  readonly parameter?: string;
  readonly signal?: AbortSignal;
  readonly timeoutMs?: number;
}

const SYNTHETIC_HEADER = "X-Burro-Synthetic";
const REQUEST_ID_HEADER = "X-Request-Id";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readMeta(value: unknown): Meta | null {
  if (!isRecord(value)) return null;
  const { release_id, engine_version, synthetic } = value;
  if (typeof release_id !== "string" || typeof engine_version !== "string") return null;
  if (typeof synthetic !== "boolean") return null;
  return { release_id, engine_version, synthetic };
}

/** More fields than any refusal of the API's could name. An error that holds more is not the API's. */
const MOST_FIELDS = 200;

function readField(value: unknown): FieldProblem | null {
  if (!isRecord(value)) return null;
  const { path, problem } = value;
  if (typeof path !== "string" || typeof problem !== "string") return null;
  // That the problem is one the contract lists is the contract's promise.
  return { path, problem: problem as FieldProblem["problem"] };
}

/**
 * The error of an envelope, as a new record that holds what the contract names
 * and nothing else. An error that is not of that shape, in any of its fields,
 * is not read at all: read in part, it would stop the page where a field is
 * first looked at.
 */
function readError(value: unknown): ErrorBody | null {
  if (!isRecord(value)) return null;
  const { code, message, fields } = value;
  if (typeof code !== "string" || typeof message !== "string" || !Array.isArray(fields)) {
    return null;
  }
  if (fields.length > MOST_FIELDS) return null;
  const read: FieldProblem[] = [];
  for (const field of fields) {
    const one = readField(field);
    if (one === null) return null;
    read.push(one);
  }
  // That the code is one the contract lists is the contract's promise, and the
  // recorded answers hold the API to it.
  return { code: code as ErrorBody["code"], message, fields: read };
}

function readFlag(header: string | null): boolean | null {
  if (header === "true") return true;
  if (header === "false") return false;
  return null;
}

function isOffline(): boolean {
  return typeof navigator !== "undefined" && navigator.onLine === false;
}

/**
 * Made-up data is never shown as real. If the body and the header disagree,
 * or only one of them speaks, the answer counts as made up when either says so.
 */
function eitherSaysSynthetic(meta: Meta, header: boolean | null): boolean {
  return meta.synthetic || header === true;
}

export async function send<Op extends OperationId>(
  operation: Op,
  settings: SendSettings,
  request: SendRequest = {},
): Promise<Answer<DataOf<Op>>> {
  if (settings.baseUrl === null) return failed("not_configured");
  if (request.signal?.aborted) return failed("aborted");
  if (isOffline()) return failed("offline");

  const route = ROUTES[operation];
  const doFetch = settings.fetch ?? globalThis.fetch;
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, request.timeoutMs ?? route.timeoutMs);
  const stop = () => controller.abort();
  request.signal?.addEventListener("abort", stop, { once: true });

  const whyItStopped = () => {
    if (timedOut) return failed("timeout");
    if (request.signal?.aborted) return failed("aborted");
    return failed(isOffline() ? "offline" : "network");
  };

  try {
    const posting = route.method === "POST";
    let response: Response;
    try {
      response = await doFetch(`${settings.baseUrl}${pathOf(operation, request.parameter)}`, {
        // An answer to a search is kept in memory and nowhere else.
        ...(posting ? { cache: "no-store" as const } : {}),
        ...settings.init,
        method: route.method,
        headers: posting
          ? { Accept: "application/json", "Content-Type": "application/json" }
          : { Accept: "application/json" },
        ...(posting ? { body: JSON.stringify(request.body ?? {}) } : {}),
        // The API sets no cookie and reads none, and is told nothing of the page.
        credentials: "omit",
        referrerPolicy: "no-referrer",
        // The API never redirects. Whatever does is not the API, and a body
        // that followed it would carry what was typed somewhere else.
        redirect: "error",
        signal: controller.signal,
      });
    } catch {
      return whyItStopped();
    }

    const seen = {
      status: response.status,
      synthetic: readFlag(response.headers.get(SYNTHETIC_HEADER)),
      requestId: response.headers.get(REQUEST_ID_HEADER),
    };
    // Whoever shows the banner hears of each answer once, whatever became of it.
    const unreadable = () => {
      if (seen.synthetic !== null) settings.onSynthetic?.(seen.synthetic);
      return failed("unreadable", seen);
    };

    let body: unknown;
    try {
      body = JSON.parse(await response.text());
    } catch {
      return timedOut || request.signal?.aborted ? whyItStopped() : unreadable();
    }

    const meta = isRecord(body) ? readMeta(body.meta) : null;
    if (!isRecord(body) || meta === null) return unreadable();
    const synthetic = eitherSaysSynthetic(meta, seen.synthetic);
    settings.onSynthetic?.(synthetic);

    const error = readError(body.error);
    if (error !== null) {
      return {
        ok: false,
        failure: {
          kind: "api",
          status: response.status,
          code: error.code,
          message: error.message,
          fields: error.fields,
          meta,
          synthetic,
          requestId: seen.requestId,
        },
      };
    }
    // An error that could not be read is never passed over for the data beside it.
    if (!response.ok || "error" in body || !("data" in body) || !isRecord(body.data)) {
      return failed("unreadable", { ...seen, synthetic });
    }
    // An answer that lacks what the contract requires of it is not the API's answer.
    // It is refused here, where it can be said in words, and not where it would be read.
    const { data } = body;
    if (REQUIRED_IN_DATA[operation].some((name) => !(name in data))) {
      return failed("unreadable", { ...seen, synthetic });
    }
    return {
      ok: true,
      status: response.status,
      meta,
      data: data as DataOf<Op>,
      synthetic,
      requestId: seen.requestId,
    };
  } finally {
    clearTimeout(timer);
    request.signal?.removeEventListener("abort", stop);
  }
}
