/**
 * The website stands between the browser and the service for the routes of accounts.
 *
 * A browser asks `/v1/auth/*` and `/v1/me/*` of the website's own origin, and this passes
 * each on to the service. So the cookie that holds a session is the website's own, and no
 * browser sends it across sites.
 *
 * What is passed on is a closed list: of routes, of headers and of cookies. Nothing else
 * of a request reaches the service, and nothing else of its answer reaches the browser.
 * The address that is asked of the service is the route of the list, and never the path
 * as it was sent.
 *
 * The website says who it is by a secret, which it reads from its environment and sends
 * to the service and to nobody else. It says what the address of the client is, as the
 * website's host gave it, in one header, with every request it passes on. A header of
 * that name from a client is never passed on, because no header is passed on that is not
 * of the list. Where the host gave no one address, nothing is passed on: the service
 * counts what each client asks, and those of whom nothing is said would be counted as one.
 * Nor is anything passed on to a service that is not reached over TLS, but on a machine
 * of one's own.
 *
 * It writes nothing down: no line of a log, and nothing to the console. What it refuses
 * it refuses with a status and no body, so that nothing that was sent is ever repeated.
 *
 * This file runs on the server alone. Nothing that runs in a browser may take from it.
 */

import { isIP } from "node:net";

import { apiBaseUrl } from "@/lib/api/config";

import { CLIENT_HEADER, COOKIES, COOKIES_IN_THE_CLEAR, REQUEST_HEADER, REQUEST_VALUE, WEBSITE_HEADER } from "./names";
import { accountsOn } from "./on";
import { ACCOUNT_ROUTES, routeOf } from "./routes";

export const SECRET_VARIABLE = "BURRO_WEBSITE_SECRET";
export const ADDRESS_VARIABLE = "BURRO_CLIENT_ADDRESS_HEADER";
export const DEVELOPMENT_VARIABLE = "BURRO_ACCOUNTS_DEVELOPMENT";

/** The one value that says the website is being developed. Anything else says that it is not. */
export const IN_DEVELOPMENT = "yes";

/** The fewest characters a secret may be. One that is shorter could be found by trying. */
export const SHORTEST_SECRET = 32;

/**
 * A secret, as the service takes one: so many characters of those that may stand in a
 * header, and no space among them. What the service would not take the website does not send.
 */
const A_SECRET = new RegExp(`^[\\x21-\\x7e]{${SHORTEST_SECRET},512}$`);

/** The most a body may hold, in bytes: what the service takes, and no more. */
export const LARGEST_BODY = 16 * 1024;

/** The most an answer may hold, in bytes. A copy of everything an account holds is the largest of them. */
export const LARGEST_ANSWER = 4 * 1024 * 1024;

/** How long the service is waited for, in milliseconds. A browser stops waiting sooner. */
export const WAIT_MS = 20_000;

export interface PassSettings {
  /** Whether accounts are on. With them off nothing is passed on. */
  readonly on: boolean;
  /** The address of the service, with no slash at its end. `null` where none is set. */
  readonly service: string | null;
  /** The secret the website says who it is by. `null` where none is set, or it is too short. */
  readonly secret: string | null;
  /**
   * The name of the header in which the website's host gives the address of a client.
   * It must be one that the host writes over whatever a client sent under that name.
   * `null` where none is named, and `false` where what was named is no name of a header.
   * With either nothing at all is passed on, since every client would else be counted
   * as one and nobody told. On a machine of one's own no host stands before the website,
   * so there, and nowhere else, a request is passed on with no address.
   */
  readonly addressFrom: string | null | false;
  /**
   * That the website is being developed. It changes two things, and only for a request
   * that reached the website in the clear on the machine it runs on: the two cookies are
   * let by under their plain names, as the service names them there, and a request is
   * passed on though no host said whose it is.
   */
  readonly development: boolean;
  /** The `fetch` to ask the service with. A test passes its own. */
  readonly fetch?: typeof fetch;
}

/** The name of a header, as one is written. */
const A_HEADER = /^[A-Za-z0-9-]{1,64}$/;

/**
 * A secret as it was set, where it is one. It is compared by the service, and is never
 * shown. It is not mended: a space at the end of a secret is a fault, and not one to mend quietly.
 */
function secretOf(value: string | null | undefined): string | null {
  return value !== undefined && value !== null && A_SECRET.test(value) ? value : null;
}

function headerOf(value: string | undefined): string | null | false {
  if (value === undefined || value.trim() === "") return null;
  return A_HEADER.test(value) ? value.toLowerCase() : false;
}

/** The settings as the environment of the website has them now. */
export function settingsNow(): Omit<PassSettings, "fetch"> {
  return {
    on: accountsOn(),
    service: apiBaseUrl(),
    secret: secretOf(process.env.BURRO_WEBSITE_SECRET),
    addressFrom: headerOf(process.env.BURRO_CLIENT_ADDRESS_HEADER),
    development: process.env.BURRO_ACCOUNTS_DEVELOPMENT === IN_DEVELOPMENT,
  };
}

/** The headers of a request that are passed on to the service, and no other. */
const PASSED_ON = ["accept", "content-type", "origin", "user-agent", REQUEST_HEADER.toLowerCase()] as const;

/** The headers of an answer that are passed back to the browser, and no other. */
const PASSED_BACK = ["content-type", "retry-after", "x-burro-preview", "x-burro-synthetic", "x-request-id"] as const;

/** What every answer of the route says, whatever became of the request. */
const ALWAYS: readonly (readonly [string, string])[] = [
  // An answer of accounts is one person's, and no browser and nothing between may keep it.
  ["Cache-Control", "no-store"],
  ["X-Content-Type-Options", "nosniff"],
];

/** An answer of the website's own: a status, and no body. */
function refused(status: number): Response {
  return new Response(null, { status, headers: new Headers(ALWAYS.map(([name, value]): [string, string] => [name, value])) });
}

function isJson(type: string | null): boolean {
  return (type ?? "").split(";", 1)[0]?.trim().toLowerCase() === "application/json";
}

/** True where a request that changes something came from a page of the website itself. */
function cameFromAPage(request: Request): boolean {
  if (request.headers.get(REQUEST_HEADER) !== REQUEST_VALUE) return false;
  if (!isJson(request.headers.get("content-type"))) return false;
  // A browser says where a request came from. One that does not is held to the header above.
  const from = request.headers.get("sec-fetch-site");
  return from === null || from === "same-origin";
}

/** The machine the website runs on, as a browser on it names it. */
const THIS_MACHINE = ["127.0.0.1", "localhost", "[::1]"];

/** True of a request that reached the website in the clear, on the machine it runs on. */
function isInTheClearHere(asked: URL): boolean {
  return asked.protocol === "http:" && THIS_MACHINE.includes(asked.hostname);
}

/** The cookies of accounts among those a browser sent, as one header. Empty where it sent none of them. */
function cookiesOf(sent: string | null, inTheClear: boolean): string {
  if (sent === null) return "";
  const letBy = inTheClear ? [...COOKIES, ...COOKIES_IN_THE_CLEAR] : COOKIES;
  return sent
    .split(";")
    .map((pair) => pair.trim())
    .filter((pair) => letBy.includes(pair.split("=", 1)[0] ?? ""))
    .join("; ");
}

/**
 * True of a cookie that is one of the two and is set as each must be: for this host alone,
 * for the whole of it, sent only where the connection is kept from others, read by no
 * script, and not sent from a page of another site.
 *
 * In development, in the clear, a cookie under its plain name need not say that it is
 * kept from the clear: it could not be given to the page if it did. It is held to all else.
 */
function isLetBy(cookie: string, inTheClear: boolean): boolean {
  const [pair = "", ...rest] = cookie.split(";").map((part) => part.trim());
  const name = pair.includes("=") ? pair.slice(0, pair.indexOf("=")) : "";
  const plain = inTheClear && COOKIES_IN_THE_CLEAR.includes(name);
  if (!COOKIES.includes(name) && !plain) return false;
  const said = new Map(
    rest.map((part): [string, string] => {
      const at = part.indexOf("=");
      return at === -1 ? [part.toLowerCase(), ""] : [part.slice(0, at).trim().toLowerCase(), part.slice(at + 1).trim()];
    }),
  );
  const from = (said.get("samesite") ?? "").toLowerCase();
  return (
    (plain || said.has("secure")) &&
    said.has("httponly") &&
    !said.has("domain") &&
    said.get("path") === "/" &&
    (from === "lax" || from === "strict")
  );
}

/** The address of the client, as the website's host gave it. `null` where it gave none, or gave what is no one address. */
function addressOf(request: Request, from: string | null): string | null {
  if (from === null) return null;
  const given = (request.headers.get(from) ?? "").trim();
  return isIP(given) === 0 ? null : given;
}

/** What a stream holds, where that is no more than it may hold. `null` where it holds more. */
async function atMost(stream: ReadableStream<Uint8Array> | null, most: number): Promise<Uint8Array<ArrayBuffer> | null> {
  if (stream === null) return new Uint8Array(0);
  const reader = stream.getReader();
  const parts: Uint8Array[] = [];
  let held = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    held += value.byteLength;
    if (held > most) {
      await reader.cancel();
      return null;
    }
    parts.push(value);
  }
  const whole = new Uint8Array(held);
  let at = 0;
  for (const part of parts) {
    whole.set(part, at);
    at += part.byteLength;
  }
  return whole;
}

/**
 * Passes one request on to the service, and its answer back.
 *
 * It answers 404 with accounts off, and for whatever is not a route of the list: there is
 * then nothing at the address. It answers 403 to a request that changes something and did
 * not come from a page of the website, 413 to a body larger than the service takes, 503
 * where the website has not been given what it needs to say who it is or whose request
 * this is, or would reach the service in the clear, 502 where the service could not be
 * reached or answered with what is not its own, and 504 where it did not answer in time.
 * None of them has a body.
 */
export async function pass(request: Request, settings: PassSettings = settingsNow()): Promise<Response> {
  if (!settings.on) return refused(404);

  const asked = new URL(request.url);
  // No route takes anything after a `?`, so whatever stands there is passed nowhere.
  if (asked.search !== "") return refused(404);
  const operation = routeOf(request.method, asked.pathname);
  if (operation === null) return refused(404);
  const route = ACCOUNT_ROUTES[operation];

  const changes = route.method !== "GET";
  if (changes && !cameFromAPage(request)) return refused(403);

  // Held to its length here too, whoever handed the settings over.
  const secret = secretOf(settings.secret);
  if (settings.service === null || secret === null || settings.addressFrom === false) return refused(503);

  const inTheClear = settings.development && isInTheClearHere(asked);
  // What is passed on holds the secret, the cookie of a session and the body. So the service
  // is reached over TLS, as the service asks of the website: but on a machine of one's own.
  if (!inTheClear && !settings.service.startsWith("https://")) return refused(503);
  const address = addressOf(request, settings.addressFrom);
  // Whose request it is, is said with whatever is passed on. The service counts what
  // each client asks, so those of whom nothing was said would be counted as one client,
  // whom ten requests from anybody would stop from signing in.
  if (address === null && !inTheClear) return refused(503);

  let body: Uint8Array<ArrayBuffer> | null = null;
  if (changes) {
    body = await atMost(request.body, LARGEST_BODY).catch(() => null);
    if (body === null) return refused(413);
  }

  const headers = new Headers();
  for (const name of PASSED_ON) {
    const value = request.headers.get(name);
    if (value !== null) headers.set(name, value);
  }
  const cookies = cookiesOf(request.headers.get("cookie"), inTheClear);
  if (cookies !== "") headers.set("cookie", cookies);
  headers.set(WEBSITE_HEADER, secret);
  if (address !== null) headers.set(CLIENT_HEADER, address);

  let answer: Response;
  try {
    answer = await (settings.fetch ?? globalThis.fetch)(`${settings.service}${route.path}`, {
      method: route.method,
      headers,
      ...(body === null ? {} : { body }),
      // The service never leads elsewhere. Whatever does is not the service, and is not followed.
      redirect: "manual",
      cache: "no-store",
      signal: AbortSignal.timeout(WAIT_MS),
    });
  } catch (fault) {
    // What went wrong is not read beyond its kind: its message may hold an address.
    return refused(fault instanceof DOMException && fault.name === "TimeoutError" ? 504 : 502);
  }

  // The service answers in JSON, whatever it answers. What is not JSON is not its answer.
  if ((answer.status >= 300 && answer.status < 400) || !isJson(answer.headers.get("content-type"))) return refused(502);
  const held = await atMost(answer.body, LARGEST_ANSWER).catch(() => null);
  if (held === null) return refused(502);

  const back = new Headers(ALWAYS.map(([name, value]): [string, string] => [name, value]));
  for (const name of PASSED_BACK) {
    const value = answer.headers.get(name);
    if (value !== null) back.set(name, value);
  }
  for (const cookie of answer.headers.getSetCookie()) {
    if (isLetBy(cookie, inTheClear)) back.append("set-cookie", cookie);
  }
  // An answer that may hold nothing is passed back holding nothing.
  const bare = answer.status === 204 || answer.status === 205 || answer.status === 304;
  return new Response(bare ? null : held, { status: answer.status, headers: back });
}
