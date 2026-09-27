/**
 * A stand-in for the routes of accounts, for a test to sign in and keep a search against.
 *
 * It answers as the contract says the service does, from what it holds in memory: who is
 * signed in, and what they keep. Every answer it gives is one the contract allows, and a
 * test holds each to it. It keeps every request it was sent, so that a test can say what
 * left the page and where it went. Nothing here reaches a network.
 *
 * The answers of the service itself were not recorded when this was written: the service
 * declared its routes and served none of them. Once they are recorded, a test answers
 * from the recording, as every other test of the website does.
 */

import { act } from "@testing-library/react";

import { createAccountClient, type AccountClient, type AccountDataOf } from "@/lib/account/client";
import { ACCOUNT_OPERATIONS, ACCOUNT_ROUTES, routeOf, type AccountOperation } from "@/lib/account/routes";
import { noteSignedOut } from "@/lib/account/who";
import { recordedAnswer } from "@/lib/api/recorded";
import type { ErrorCode, KeptSearch, Meta, PreferenceSpec, SignedInAt, Switch } from "@/lib/api/schema";

import { aMomentLater, landed } from "./api";

export const META: Meta = recordedAnswer("get_meta", "meta").body.meta;

/** A spec the service returned, which a search that is kept holds. */
export const SPEC: PreferenceSpec = recordedAnswer("rank", "rank-first").body.data.spec;
export const OTHER_SPEC: PreferenceSpec = recordedAnswer("rank", "rank-refined").body.data.spec;

/** An address nobody has, in a domain kept for examples. */
export const EMAIL = "rowan.ashdown@example.org";
/** A token of the shape the service makes, made up here: 43 characters of URL-safe text. */
export const TOKEN = "Zm9yLWEtdGVzdC1vZi10aGUtd2Vic2l0ZS0wMDAwMDA"; // public-only: allow

export interface AccountCall {
  readonly operation: AccountOperation | null;
  readonly method: string;
  readonly url: string;
  /** The body as it was sent, as text. `null` for a `GET`. */
  readonly sent: string | null;
  /** The body, read as JSON. */
  readonly body: unknown;
  readonly headers: Headers;
  readonly init: RequestInit;
}

/** What the stand-in holds, as a service would. A test sets it, and reads what became of it. */
export interface Held {
  signedIn: boolean;
  email: string;
  /** Whether the link was asked for in the browser that holds it. */
  sameBrowser: boolean;
  /** Whether signing in would make an account. */
  newAccount: boolean;
  /** Whether the person signed in a short while ago. */
  fresh: boolean;
  keepRecent: Switch;
  searches: KeptSearch[];
  recent: KeptSearch[];
  sessions: SignedInAt[];
}

export function kept(id: string, name: string, over: Partial<KeptSearch> = {}): KeptSearch {
  return {
    search_id: `N6BkBdeSvd7xEk0NJV${id}`.slice(0, 22).padEnd(22, "0"),
    name,
    spec: SPEC,
    release_id: META.release_id,
    kept_at: "2026-09-24T18:05:11Z",
    state: "ok",
    ...over,
  };
}

export function signedInAt(id: string, over: Partial<SignedInAt> = {}): SignedInAt {
  return {
    session_id: `N6BkBdeSvd7xEk0NJV${id}`.slice(0, 22).padEnd(22, "0"),
    browser: "chrome",
    made_at: "2026-09-26T19:20:00Z",
    seen_at: "2026-09-26T19:20:00Z",
    ends_at: "2026-10-26T19:20:00Z",
    current: false,
    revoked: false,
    ...over,
  };
}

export function held(over: Partial<Held> = {}): Held {
  return {
    signedIn: false,
    email: EMAIL,
    sameBrowser: true,
    newAccount: false,
    fresh: true,
    keepRecent: "on",
    searches: [
      kept("s001", "Renting a 1 bed up to £1,700 a month, Leafy, Quiet streets"),
      kept("s002", "Buying, Parks close by, Historic", { spec: OTHER_SPEC, kept_at: "2026-09-20T09:41:00Z" }),
      kept("s003", "Renting, Food and drink", { kept_at: "2026-08-02T12:00:00Z", state: "release_changed" }),
    ],
    recent: [
      kept("r001", "Renting, Leafy, Quiet streets", { kept_at: "2026-09-26T17:30:00Z" }),
      kept("r002", "Renting, Buzzy, Food and drink", { spec: OTHER_SPEC, kept_at: "2026-09-26T17:12:00Z" }),
    ],
    sessions: [
      signedInAt("c001", { current: true }),
      signedInAt("c002", { browser: "safari", made_at: "2026-09-12T08:02:00Z", seen_at: "2026-09-25T21:40:00Z", ends_at: "2026-10-25T21:40:00Z" }),
    ],
    ...over,
  };
}

/** What the service refuses with, in its own fixed words, by its code. */
const REFUSALS = {
  not_signed_in: [401, "You are not signed in, so please sign in and try again."],
  sign_in_again: [
    403,
    "Please sign in again before you delete your account. Burro asks for this so that nobody else can delete it from a browser you left signed in.",
  ],
  rate_limited: [429, "Burro has been asked to sign in too many times from here, so please wait a quarter of an hour and then try again."],
  sign_in_busy: [429, "Burro has sent as many sign-in emails as it may for now, so please try again in an hour."],
  sign_in_unavailable: [503, "Burro cannot send sign-in emails at the moment, so please try again later."],
  invalid_email: [422, "That does not look like an email address, so please check it and try again."],
  link_not_valid: [422, "Burro does not recognise this sign-in link. It may be incomplete, so please ask for a new one."],
  link_expired: [410, "This sign-in link has run out, because a link only works for 15 minutes. Please ask for a new one."],
  link_used: [
    410,
    "This sign-in link no longer works, because it has been used or a newer one has. Each link works once, so please ask for a new one.",
  ],
  other_browser: [409, "This link was asked for in a different browser, so Burro needs you to confirm that you want to sign in here."],
  age_not_confirmed: [409, "Burro can only make an account for you once you have confirmed that you are 18 or over."],
  too_many_searches: [
    409,
    "You have saved 100 searches, which is the most Burro holds for one account. Remove one and you can save this one.",
  ],
  search_not_found: [404, "Burro could not find that search among the ones you have saved."],
  session_not_found: [404, "Burro could not find that sign-in, so it may have ended already."],
  internal_error: [500, "Something went wrong at Burro's end."],
} as const satisfies Partial<Record<ErrorCode, readonly [number, string]>>;

export type Refusal = keyof typeof REFUSALS;

const HEADERS = {
  "Content-Type": "application/json",
  "Cache-Control": "no-store",
  "X-Burro-Synthetic": String(META.synthetic),
  "X-Burro-Preview": String(META.preview),
} as const;

let answered = 0;

/** The answer of a route that went well, in the envelope of the service. */
export function answerOf<Op extends AccountOperation>(operation: Op, data: AccountDataOf<Op>): Response {
  answered += 1;
  return new Response(JSON.stringify({ meta: META, data }), {
    status: operation === "ask_for_link" ? 202 : 200,
    headers: { ...HEADERS, "X-Request-Id": `req-made-up-${answered}` },
  });
}

/** What the service refuses with, in its envelope. */
export function refusalOf(code: Refusal): Response {
  answered += 1;
  const [status, message] = REFUSALS[code];
  return new Response(JSON.stringify({ meta: META, error: { code, message, fields: [] } }), {
    status,
    headers: { ...HEADERS, "X-Request-Id": `req-made-up-${answered}` },
  });
}

export const messageOf = (code: Refusal): string => REFUSALS[code][1];

export type AccountResponder = Refusal | ((call: AccountCall, held: Held) => Response | Promise<Response>);

export interface AccountStandIn {
  readonly fetch: typeof fetch;
  readonly client: AccountClient;
  readonly calls: AccountCall[];
  /** Calls to what is no route of accounts. A test expects none. */
  readonly unexpected: AccountCall[];
  /** What is held. A test changes it as a service would be changed from elsewhere. */
  readonly held: Held;
  /** Sets how an operation answers from now on: with a refusal by its code, or with whatever a function makes of the call. */
  on(operation: AccountOperation, responder: AccountResponder): AccountStandIn;
  /** Sets the answers of an operation's next calls, in order. After them it answers from what is held. */
  inTurn(operation: AccountOperation, ...responders: AccountResponder[]): AccountStandIn;
  /** Answers an operation from what is held again. */
  asHeld(operation: AccountOperation): AccountStandIn;
  /** Makes an operation fail as a request that could not leave. */
  unreachable(operation: AccountOperation): AccountStandIn;
  /** Makes an operation wait until it is released, and then answer from what is held. */
  hold(operation: AccountOperation): { release(): void; waiting(): number };
  callsTo(operation: AccountOperation): AccountCall[];
  lastCallTo(operation: AccountOperation): AccountCall;
}

/** How each route answers from what is held, as the contract says the service does. */
function fromWhatIsHeld(call: AccountCall, state: Held): Response {
  const body = (call.body ?? {}) as Record<string, unknown>;
  const session = () => ({ signed_in: state.signedIn, email: state.signedIn ? state.email : null });
  const recent = () => ({
    kept: state.keepRecent === "on",
    searches: state.keepRecent === "on" ? state.recent : [],
    most: 10,
  });
  switch (call.operation) {
    case null:
      return new Response(null, { status: 404 });
    case "get_session":
      return answerOf("get_session", session());
    case "ask_for_link":
      if (typeof body.email !== "string" || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(body.email)) return refusalOf("invalid_email");
      state.email = body.email;
      return answerOf("ask_for_link", { lasts_minutes: 15 });
    case "whose_link":
      return answerOf("whose_link", { email: state.email, same_browser: state.sameBrowser, new_account: state.newAccount });
    case "sign_in":
      if (!state.sameBrowser && body.other_browser !== true) return refusalOf("other_browser");
      if (state.newAccount && body.adult !== true) return refusalOf("age_not_confirmed");
      state.signedIn = true;
      return answerOf("sign_in", { email: state.email, new_account: state.newAccount });
    case "sign_out":
      state.signedIn = false;
      return answerOf("sign_out", session());
    default:
      break;
  }
  if (!state.signedIn) return refusalOf("not_signed_in");
  switch (call.operation) {
    case "get_me":
      return answerOf("get_me", {
        email: state.email,
        made_at: "2026-09-12T08:02:00Z",
        preferences: { keep_recent: state.keepRecent },
        fresh: state.fresh,
      });
    case "delete_me":
      if (!state.fresh) return refusalOf("sign_in_again");
      state.signedIn = false;
      return answerOf("delete_me", session());
    case "list_searches":
      return answerOf("list_searches", { searches: state.searches, most: 100 });
    case "keep_search": {
      const made = kept(`k${String(state.searches.length).padStart(3, "0")}`, "Renting, Leafy, Quiet streets", {
        spec: body.spec as PreferenceSpec,
        kept_at: "2026-09-26T19:25:00Z",
      });
      state.searches = [made, ...state.searches];
      return answerOf("keep_search", made);
    }
    case "forget_search": {
      if (!state.searches.some((one) => one.search_id === body.search_id)) return refusalOf("search_not_found");
      state.searches = state.searches.filter((one) => one.search_id !== body.search_id);
      return answerOf("forget_search", { searches: state.searches, most: 100 });
    }
    case "list_recent":
      return answerOf("list_recent", recent());
    case "keep_recent": {
      if (state.keepRecent === "on") {
        const made = kept(`q${String(state.recent.length).padStart(3, "0")}`, "Renting, Leafy, Quiet streets", {
          spec: body.spec as PreferenceSpec,
          kept_at: "2026-09-26T19:26:00Z",
        });
        state.recent = [made, ...state.recent].slice(0, 10);
      }
      return answerOf("keep_recent", recent());
    }
    case "forget_recent":
      state.recent = [];
      return answerOf("forget_recent", recent());
    case "set_preferences":
      if (body.keep_recent === "on" || body.keep_recent === "off") state.keepRecent = body.keep_recent;
      if (state.keepRecent === "off") state.recent = [];
      return answerOf("set_preferences", { keep_recent: state.keepRecent });
    case "list_sessions":
      return answerOf("list_sessions", { sessions: state.sessions, signed_in: state.signedIn });
    case "end_sessions": {
      if (body.everywhere === true) {
        state.sessions = [];
        state.signedIn = false;
      } else {
        const gone = state.sessions.find((one) => one.session_id === body.session_id);
        if (gone === undefined) return refusalOf("session_not_found");
        state.sessions = state.sessions.filter((one) => one !== gone);
        if (gone.current) state.signedIn = false;
      }
      return answerOf("end_sessions", { sessions: state.sessions, signed_in: state.signedIn });
    }
    case "export_me":
      return answerOf("export_me", {
        exported_at: "2026-09-26T19:30:00Z",
        email: state.email,
        made_at: "2026-09-12T08:02:00Z",
        adult_at: "2026-09-12T08:02:00Z",
        preferences: { keep_recent: state.keepRecent },
        searches: state.searches,
        recent: state.recent,
        sessions: state.sessions,
        events: [
          { event: "link_requested", outcome: "ok", at: "2026-09-26T19:19:00Z" },
          { event: "session_created", outcome: "ok", at: "2026-09-26T19:20:00Z" },
        ],
        links: [{ asked_at: "2026-09-26T19:19:00Z", ends_at: "2026-09-26T19:34:00Z", used: true }],
      });
    default:
      return new Response(null, { status: 404 });
  }
}

/** Fails as a request does that was stopped, once it is. */
function stopped(signal: AbortSignal | null | undefined): Promise<never> {
  return new Promise((_, reject) => {
    const fail = () => reject(new DOMException("stopped", "AbortError"));
    if (signal?.aborted) fail();
    else signal?.addEventListener("abort", fail, { once: true });
  });
}

let onTheirWay = 0;

if (typeof beforeEach === "function") {
  beforeEach(() => {
    onTheirWay = 0;
  });
}

/** How many turns in a row nothing must be on its way, so that an answer that leads to a call is seen. */
const QUIET_TURNS = 5;
/** How long answers that are on their way are waited for, in milliseconds, before a test goes on. */
const WITHIN_MS = 2_000;

/**
 * Lets what is on its way arrive, of the routes of accounts and of the API alike: an answer
 * read, a state set, a page drawn. An answer that a test holds back is not waited for.
 */
export async function arrived(): Promise<void> {
  await act(async () => {
    const until = Date.now() + WITHIN_MS;
    for (let quiet = 0; quiet < QUIET_TURNS && Date.now() < until; ) {
      await new Promise((resolve) => setTimeout(resolve, 0));
      quiet = onTheirWay === 0 ? quiet + 1 : 0;
    }
    await landed();
  });
}

export function standInAccounts(state: Held = held()): AccountStandIn {
  const calls: AccountCall[] = [];
  const unexpected: AccountCall[] = [];
  const responders = new Map<AccountOperation, AccountResponder[]>();
  const held = new Map<AccountOperation, { gate: Promise<void>; waiting: number }>();

  const answer = async (call: AccountCall): Promise<Response> => {
    const { operation } = call;
    const waits = operation === null ? undefined : held.get(operation);
    if (waits !== undefined) {
      waits.waiting += 1;
      await waits.gate;
      waits.waiting -= 1;
    }
    onTheirWay += 1;
    try {
      await aMomentLater();
      const queue = operation === null ? undefined : responders.get(operation);
      const responder = queue === undefined ? undefined : queue.length > 1 ? queue.shift() : queue[0];
      if (responder === undefined) return fromWhatIsHeld(call, state);
      return typeof responder === "string" ? refusalOf(responder) : await responder(call, state);
    } finally {
      onTheirWay -= 1;
    }
  };

  const fetch = (async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input);
    const { pathname } = new URL(url, "https://burro.example");
    const method = init.method ?? "GET";
    const sent = typeof init.body === "string" ? init.body : null;
    const call: AccountCall = {
      operation: routeOf(method, pathname),
      method,
      url,
      sent,
      body: sent === null ? undefined : (JSON.parse(sent) as unknown),
      headers: new Headers(init.headers),
      init,
    };
    calls.push(call);
    if (call.operation === null) unexpected.push(call);
    if (init.signal?.aborted) return stopped(init.signal);
    return Promise.race([answer(call), stopped(init.signal)]);
  }) as typeof globalThis.fetch;

  const standIn: AccountStandIn = {
    fetch,
    // As the website makes its own: an answer that says nobody is signed in is heard.
    client: createAccountClient({ fetch, on: true, onSignedOut: noteSignedOut }),
    calls,
    unexpected,
    held: state,
    on(operation, responder) {
      responders.set(operation, [responder]);
      return standIn;
    },
    inTurn(operation, ...inOrder) {
      // The last of them gives way to what is held once it has answered.
      const last = inOrder.at(-1);
      const then: AccountResponder = (call, now) => fromWhatIsHeld(call, now);
      responders.set(operation, last === undefined ? [] : [...inOrder, then]);
      return standIn;
    },
    asHeld(operation) {
      responders.delete(operation);
      return standIn;
    },
    unreachable(operation) {
      responders.set(operation, [
        () => {
          throw new TypeError("Failed to fetch");
        },
      ]);
      return standIn;
    },
    hold(operation) {
      let open: () => void = () => undefined;
      const gate = new Promise<void>((resolve) => {
        open = resolve;
      });
      const waits = { gate, waiting: 0 };
      held.set(operation, waits);
      return {
        release() {
          held.delete(operation);
          open();
        },
        waiting: () => waits.waiting,
      };
    },
    callsTo: (operation) => calls.filter((call) => call.operation === operation),
    lastCallTo(operation) {
      const last = calls.filter((call) => call.operation === operation).pop();
      if (!last) throw new Error(`No call was made to ${operation}.`);
      return last;
    },
  };
  return standIn;
}

/** Every route of the list, for a test that holds something of them all. */
export const EVERY_ROUTE = ACCOUNT_OPERATIONS.map((operation) => ({ operation, ...ACCOUNT_ROUTES[operation] }));
