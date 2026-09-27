/**
 * The routes of accounts, as the browser calls them: one function for each, named for
 * its operation id in the contract.
 *
 * Each is asked of the website's own origin, which passes it on to the service. So the
 * cookie that holds a session goes with it and goes nowhere else: it is the website's
 * own, no script can read it, and nothing here tries.
 *
 * None throws: each answers with `meta` and `data`, or with a failure that says why.
 * Nothing here logs, and nothing is kept: the caller holds the answer. An address, a
 * token, a search and the id of a session each travel in the body of a request, and
 * never in its address.
 */

import { failed, type Answer } from "@/lib/api/failure";
import { REQUIRED_IN_DATA } from "@/lib/api/required";
import type { Said } from "@/lib/api/said";
import type { ErrorBody, FieldProblem, Meta, operations } from "@/lib/api/schema";

import { REQUEST_HEADER, REQUEST_VALUE } from "./names";
import { accountsOn } from "./on";
import { ACCOUNT_ROUTES, type AccountOperation, type AccountRoute } from "./routes";

type JsonOf<T> = T extends { readonly content: { readonly "application/json": infer Body } } ? Body : never;

/** The answer of an operation that went well. Asking for a link is answered 202, and every other 200. */
type WentWell<Op extends AccountOperation> = operations[Op]["responses"] extends { readonly 200: infer Answered }
  ? Answered
  : operations[Op]["responses"] extends { readonly 202: infer Answered }
    ? Answered
    : never;

/** The `data` of an operation that went well. */
export type AccountDataOf<Op extends AccountOperation> =
  JsonOf<WentWell<Op>> extends { readonly data: infer Data } ? Data : never;

/** The body an operation is sent. `never` for one that takes none. */
export type AccountBodyOf<Op extends AccountOperation> = operations[Op] extends { readonly requestBody: infer Request }
  ? JsonOf<NonNullable<Request>>
  : never;

type Sent<Op extends AccountOperation> = (
  body: AccountBodyOf<Op>,
  signal?: AbortSignal,
) => Promise<Answer<AccountDataOf<Op>>>;
type Asked<Op extends AccountOperation> = (signal?: AbortSignal) => Promise<Answer<AccountDataOf<Op>>>;

export interface AccountClient {
  /** Route 15. Asks for a link to sign in with. The answer is the same whether or not the address is known. */
  readonly askForLink: Sent<"ask_for_link">;
  /** Route 16. Whose link a token is. It uses nothing up, and signs nobody in. */
  readonly whoseLink: Sent<"whose_link">;
  /** Route 17. Uses a link up and signs the browser in. It is called by a press, and by nothing else. */
  readonly signIn: Sent<"sign_in">;
  /** Route 18. Whether the browser is signed in, and as whom. */
  readonly getSession: Asked<"get_session">;
  /** Route 19. Signs the browser out. */
  readonly signOut: Asked<"sign_out">;
  /** Route 20. The address of the account, and its preferences. */
  readonly getMe: Asked<"get_me">;
  /** Route 21. Deletes the account, and everything of it. */
  readonly deleteMe: Asked<"delete_me">;
  /** Route 22. Keeps a search: the spec the page holds, which is the last one the API returned. */
  readonly keepSearch: Sent<"keep_search">;
  /** Route 23. The searches that are kept. */
  readonly listSearches: Asked<"list_searches">;
  /** Route 24. Takes one search away. */
  readonly forgetSearch: Sent<"forget_search">;
  /** Route 25. Puts a search among the last ones, where the person lets Burro keep them. */
  readonly keepRecent: Sent<"keep_recent">;
  /** Route 26. The last searches. */
  readonly listRecent: Asked<"list_recent">;
  /** Route 27. Takes every one of the last searches away. */
  readonly forgetRecent: Asked<"forget_recent">;
  /** Route 28. Sets a preference. */
  readonly setPreferences: Sent<"set_preferences">;
  /** Route 29. Where the person is signed in. */
  readonly listSessions: Asked<"list_sessions">;
  /** Route 30. Signs out of one browser, or of every one. */
  readonly endSessions: Sent<"end_sessions">;
  /** Route 31. Everything Burro holds of the account. */
  readonly exportMe: Asked<"export_me">;
}

export interface AccountSettings {
  /** The `fetch` to call with. A test passes its own. */
  readonly fetch?: typeof fetch;
  /** Told what each answer says of the data, as soon as it says it. */
  readonly onSynthetic?: (synthetic: boolean) => void;
  /** Told what each answer says of itself, once for every answer. */
  readonly onSaid?: (said: Said) => void;
  /** Told when an answer says that nobody is signed in, whatever was asked. */
  readonly onSignedOut?: () => void;
  /** Whether accounts are on. Left out, it is what the one setting says. With them off nothing is sent. */
  readonly on?: boolean;
}

interface Request {
  readonly body?: unknown;
  readonly signal?: AbortSignal;
}

const SYNTHETIC_HEADER = "X-Burro-Synthetic";
const PREVIEW_HEADER = "X-Burro-Preview";
const REQUEST_ID_HEADER = "X-Request-Id";

/**
 * What the `data` of an answer must hold, by name, for the one answer of accounts that
 * what is generated from the contract leaves out: it lists what an answer of 200 must
 * hold, and asking for a link is answered 202. A test holds this to the contract.
 */
export const REQUIRED_OF_A_LINK = ["lasts_minutes"] as const;

/** What the `data` of each answer must hold. An answer that lacks one is not the service's answer. */
function requiredOf(operation: AccountOperation): readonly string[] {
  return operation === "ask_for_link" ? REQUIRED_OF_A_LINK : REQUIRED_IN_DATA[operation];
}

/** The code the service refuses with where nobody is signed in. */
export const NOT_SIGNED_IN = "not_signed_in";

/** More fields than any refusal of the service's could name. An error that holds more is not the service's. */
const MOST_FIELDS = 200;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readMeta(value: unknown): Meta | null {
  if (!isRecord(value)) return null;
  const { release_id, engine_version, synthetic, preview } = value;
  if (typeof release_id !== "string" || typeof engine_version !== "string") return null;
  if (typeof synthetic !== "boolean" || typeof preview !== "boolean") return null;
  return { release_id, engine_version, synthetic, preview };
}

/** The error of an envelope, as a new record that holds what the contract names and nothing else. */
function readError(value: unknown): ErrorBody | null {
  if (!isRecord(value)) return null;
  const { code, message, fields } = value;
  if (typeof code !== "string" || typeof message !== "string" || !Array.isArray(fields)) return null;
  if (fields.length > MOST_FIELDS) return null;
  const read: FieldProblem[] = [];
  for (const field of fields) {
    if (!isRecord(field) || typeof field.path !== "string" || typeof field.problem !== "string") return null;
    read.push({ path: field.path, problem: field.problem as FieldProblem["problem"] });
  }
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

async function ask<Op extends AccountOperation>(
  operation: Op,
  settings: AccountSettings,
  request: Request = {},
): Promise<Answer<AccountDataOf<Op>>> {
  if (!(settings.on ?? accountsOn())) return failed("not_configured");
  if (request.signal?.aborted) return failed("aborted");
  if (isOffline()) return failed("offline");

  const route: AccountRoute = ACCOUNT_ROUTES[operation];
  const doFetch = settings.fetch ?? globalThis.fetch;
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, route.timeoutMs);
  const stop = () => controller.abort();
  request.signal?.addEventListener("abort", stop, { once: true });

  const whyItStopped = () => {
    if (timedOut) return failed("timeout");
    if (request.signal?.aborted) return failed("aborted");
    return failed(isOffline() ? "offline" : "network");
  };

  try {
    const changes = route.method !== "GET";
    let response: Response;
    try {
      // The path of the list, on the website's own origin. It holds nothing of the request.
      response = await doFetch(route.path, {
        method: route.method,
        headers: changes
          ? { Accept: "application/json", "Content-Type": "application/json", [REQUEST_HEADER]: REQUEST_VALUE }
          : { Accept: "application/json" },
        // What changes something says so in a body, which holds nothing where there is nothing to say.
        ...(changes ? { body: JSON.stringify(request.body ?? {}) } : {}),
        // The cookie is the website's own, and goes to the website's own origin alone.
        credentials: "same-origin",
        // An answer of accounts is one person's. It is held in memory, and nowhere else.
        cache: "no-store",
        referrerPolicy: "no-referrer",
        // The website never leads elsewhere. Whatever does is not the website, and a body
        // that followed it would carry an address or a token somewhere else.
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
    const previewHeader = readFlag(response.headers.get(PREVIEW_HEADER));
    const unreadable = () => {
      if (seen.synthetic !== null) settings.onSynthetic?.(seen.synthetic);
      settings.onSaid?.({ synthetic: seen.synthetic, preview: previewHeader });
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
    const synthetic = meta.synthetic || seen.synthetic === true;
    settings.onSynthetic?.(synthetic);
    settings.onSaid?.({ synthetic, preview: meta.preview || previewHeader === true });

    const error = readError(body.error);
    if (error !== null) {
      if (error.code === NOT_SIGNED_IN) settings.onSignedOut?.();
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
    const { data } = body;
    if (requiredOf(operation).some((name) => !(name in data))) {
      return failed("unreadable", { ...seen, synthetic });
    }
    return {
      ok: true,
      status: response.status,
      meta,
      data: data as AccountDataOf<Op>,
      synthetic,
      requestId: seen.requestId,
    };
  } finally {
    clearTimeout(timer);
    request.signal?.removeEventListener("abort", stop);
  }
}

export function createAccountClient(settings: AccountSettings = {}): AccountClient {
  const sent =
    <Op extends AccountOperation>(operation: Op): Sent<Op> =>
    (body, signal) =>
      ask(operation, settings, { body, signal });
  const asked =
    <Op extends AccountOperation>(operation: Op): Asked<Op> =>
    (signal) =>
      ask(operation, settings, { signal });

  return {
    askForLink: sent("ask_for_link"),
    whoseLink: sent("whose_link"),
    signIn: sent("sign_in"),
    getSession: asked("get_session"),
    signOut: asked("sign_out"),
    getMe: asked("get_me"),
    deleteMe: asked("delete_me"),
    keepSearch: sent("keep_search"),
    listSearches: asked("list_searches"),
    forgetSearch: sent("forget_search"),
    keepRecent: sent("keep_recent"),
    listRecent: asked("list_recent"),
    forgetRecent: asked("forget_recent"),
    setPreferences: sent("set_preferences"),
    listSessions: asked("list_sessions"),
    endSessions: sent("end_sessions"),
    exportMe: asked("export_me"),
  };
}
