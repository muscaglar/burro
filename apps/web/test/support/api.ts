/**
 * A stand-in for the API, for a test to run a whole search against.
 *
 * It answers from the recorded answers in `test/recorded/`, and keeps every
 * request it was sent, so that a test can say what left the page and where
 * it went. Nothing here reaches a network.
 */

import { createClient, type Client } from "@/lib/api/client";
import { ROUTES, type OperationId } from "@/lib/api/operations";
import { readRecorded, responseFrom, type Recorded } from "@/lib/api/recorded";

export const BASE = "https://api.example.test";

export interface Call {
  readonly operation: OperationId | null;
  readonly method: string;
  readonly url: string;
  readonly path: string;
  /** The body as it was sent, as text. `null` for a `GET`. */
  readonly sent: string | null;
  /** The body, read as JSON. */
  readonly body: unknown;
  readonly init: RequestInit;
}

/** What an operation answers with: a recording by name, or whatever a function makes of the call. */
export type Responder = string | ((call: Call) => Recorded | Response | Promise<Recorded | Response>);

export interface Held {
  /** Lets the answer that was held go. */
  release(): void;
  /** How many calls are waiting on it. */
  waiting(): number;
}

export interface StandIn {
  readonly fetch: typeof fetch;
  readonly client: Client;
  readonly calls: Call[];
  /** Calls that no responder was set for. A test expects none. */
  readonly unexpected: Call[];
  /** Sets how an operation answers from now on. */
  on(operation: OperationId, responder: Responder): StandIn;
  /** Sets the answers of an operation's next calls, in order. The last one stays. */
  inTurn(operation: OperationId, ...responders: Responder[]): StandIn;
  /** Makes an operation wait until it is released, then answer. */
  hold(operation: OperationId, responder: Responder): Held;
  /**
   * Makes the next call to an operation wait until it is released, and answer
   * even if it was stopped meanwhile, as an answer already on its way does.
   * Calls after it are answered by `then`.
   */
  late(operation: OperationId, responder: Responder, then: Responder): Held;
  /** Makes an operation fail as a request that could not leave. */
  unreachable(operation: OperationId): StandIn;
  /** Makes an operation never answer, until it is stopped. */
  silent(operation: OperationId): StandIn;
  /**
   * From now on every recording is answered as a service holding this release answers
   * it: a service names the release it holds in every answer, whatever the route.
   */
  movedTo(release: string): StandIn;
  callsTo(operation: OperationId): Call[];
  lastCallTo(operation: OperationId): Call;
}

function operationOf(method: string, path: string): OperationId | null {
  const routes = (Object.keys(ROUTES) as OperationId[]).filter(
    (operation) => ROUTES[operation].method === method,
  );
  // A route with nothing to fill in comes first: `/v1/areas/geometry` is not an area.
  const exact = routes.find((operation) => ROUTES[operation].path === path);
  if (exact !== undefined) return exact;
  const filled = routes.find((operation) => {
    const template: string = ROUTES[operation].path;
    if (!template.includes("{")) return false;
    return new RegExp(`^${template.replace(/\{[a-z_]+\}/g, "[^/]+")}$`).test(path);
  });
  return filled ?? null;
}

function stopped(signal: AbortSignal | null | undefined): Promise<never> {
  return new Promise((_, reject) => {
    const fail = () => reject(new DOMException("stopped", "AbortError"));
    if (signal?.aborted) fail();
    else signal?.addEventListener("abort", fail, { once: true });
  });
}

/** What is served with nothing set: the routes that are a function of the release alone. */
const OF_THE_RELEASE: Partial<Record<OperationId, Responder>> = {
  get_meta: "meta",
  list_areas: "areas",
  get_geometry: "geometry",
  get_area: (call) => readRecorded(`area/${call.path.split("/").pop() ?? ""}`),
};

export function standInApi(): StandIn {
  const calls: Call[] = [];
  const unexpected: Call[] = [];
  const responders = new Map<OperationId, Responder[]>();
  /** Responders that answer even when the call was stopped. */
  const deaf = new Set<Responder>();
  /** The release every answer names, once the service has moved to another. */
  let release: string | null = null;
  for (const [operation, responder] of Object.entries(OF_THE_RELEASE)) {
    responders.set(operation as OperationId, [responder]);
  }

  function asTheReleaseNow(made: Recorded, call: Call): Recorded {
    if (release === null) return made;
    const body = JSON.parse(JSON.stringify(made.body)) as {
      meta?: { release_id?: string };
      data?: { release_id?: string };
    };
    if (body.meta !== undefined) body.meta.release_id = release;
    if (call.operation === "get_meta" && body.data !== undefined) body.data.release_id = release;
    return { ...made, body };
  }

  async function answer(responder: Responder, call: Call): Promise<Response> {
    const made = typeof responder === "string" ? readRecorded(responder) : await responder(call);
    return made instanceof Response ? made : responseFrom(asTheReleaseNow(made, call));
  }

  const fetch = (async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input);
    const { pathname } = new URL(url);
    const method = init.method ?? "GET";
    const sent = typeof init.body === "string" ? init.body : null;
    const call: Call = {
      operation: operationOf(method, pathname),
      method,
      url,
      path: pathname,
      sent,
      body: sent === null ? undefined : (JSON.parse(sent) as unknown),
      init,
    };
    calls.push(call);
    const queue = call.operation === null ? undefined : responders.get(call.operation);
    const responder = queue && (queue.length > 1 ? queue.shift() : queue[0]);
    if (responder === undefined) {
      unexpected.push(call);
      throw new TypeError("No answer was set for this call.");
    }
    if (deaf.has(responder)) return answer(responder, call);
    if (init.signal?.aborted) return stopped(init.signal);
    return Promise.race([answer(responder, call), stopped(init.signal)]);
  }) as typeof globalThis.fetch;

  function gated(responder: Responder) {
    let open: () => void = () => undefined;
    let waiting = 0;
    const gate = new Promise<void>((resolve) => {
      open = resolve;
    });
    const held: Responder = async (call) => {
      waiting += 1;
      await gate;
      waiting -= 1;
      return answer(responder, call);
    };
    return { held, handle: { release: () => open(), waiting: () => waiting } };
  }

  const standIn: StandIn = {
    fetch,
    client: createClient({ baseUrl: BASE, fetch }),
    calls,
    unexpected,
    on(operation, responder) {
      responders.set(operation, [responder]);
      return standIn;
    },
    inTurn(operation, ...inOrder) {
      responders.set(operation, [...inOrder]);
      return standIn;
    },
    hold(operation, responder) {
      const { held, handle } = gated(responder);
      responders.set(operation, [held]);
      return handle;
    },
    late(operation, responder, then) {
      const { held, handle } = gated(responder);
      deaf.add(held);
      responders.set(operation, [held, then]);
      return handle;
    },
    unreachable(operation) {
      responders.set(operation, [
        () => {
          throw new TypeError("Failed to fetch");
        },
      ]);
      return standIn;
    },
    silent(operation) {
      responders.set(operation, [() => new Promise<Response>(() => undefined)]);
      return standIn;
    },
    movedTo(next) {
      release = next;
      return standIn;
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

/**
 * Answers as a recording does, but with the spec that was sent, as the API
 * does when it is sent no edit. It is for a test whose recorded sentence and
 * recorded ranking are of two different searches.
 */
export function withTheSpecSent(scenario: string): Responder {
  return (call) => {
    const recorded = readRecorded(scenario);
    const sent = (call.body as { spec?: unknown } | undefined)?.spec;
    const body = recorded.body as { data: Record<string, unknown> };
    return { ...recorded, body: { ...body, data: { ...body.data, spec: sent ?? body.data.spec } } };
  };
}

/** Whether the browser says it has a connection. */
export function setOnline(online: boolean): void {
  Object.defineProperty(window.navigator, "onLine", { configurable: true, get: () => online });
}
