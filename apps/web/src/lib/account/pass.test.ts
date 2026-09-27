/** @jest-environment node */
/**
 * The website stands between the browser and the service for the routes of accounts.
 * What it passes on is a closed list of paths and of headers, it says who it is by a
 * secret that reaches the service and nobody else, and it says what the address of the
 * client is, as its host gave it and never as a client did.
 *
 * Each test hands it a request and a stand-in for the service, and reads what reached
 * the service and what came back.
 */

import { CLIENT_HEADER, COOKIES_IN_THE_CLEAR, LINK_COOKIE, REQUEST_HEADER, SESSION_COOKIE, WEBSITE_HEADER } from "./names";
import { ACCOUNTS_VARIABLE } from "./on";
import {
  ADDRESS_VARIABLE,
  DEVELOPMENT_VARIABLE,
  LARGEST_BODY,
  pass,
  SECRET_VARIABLE,
  settingsNow,
  SHORTEST_SECRET,
  type PassSettings,
} from "./pass";
import { ACCOUNT_OPERATIONS, ACCOUNT_ROUTES } from "./routes";

const SITE = "https://burro.example";
const SERVICE = "https://api.burro.example";
// Made up here, and no secret of anything: it is as long as a secret must be.
const SECRET = "made-up-in-a-test-".padEnd(SHORTEST_SECRET + 4, "x");
const CANARY = "zqxcanary7431";
/** The header a made-up host gives the address of a client in. */
const FROM_THE_HOST = "x-real-ip";

interface Reached {
  readonly url: string;
  readonly method: string;
  readonly headers: Headers;
  readonly body: string | null;
  readonly init: RequestInit;
}

interface Service {
  readonly fetch: typeof fetch;
  readonly reached: Reached[];
}

/** The settings the website would read, were its environment this one. */
function settingsFrom(environment: Readonly<Record<string, string>>): Omit<PassSettings, "fetch"> {
  const SET = [ACCOUNTS_VARIABLE, "NEXT_PUBLIC_BURRO_API_URL", SECRET_VARIABLE, ADDRESS_VARIABLE, DEVELOPMENT_VARIABLE];
  const before = SET.map((name): [string, string | undefined] => [name, process.env[name]]);
  for (const name of SET) delete process.env[name];
  Object.assign(process.env, environment);
  try {
    return settingsNow();
  } finally {
    for (const [name, value] of before) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

const ENVELOPE = JSON.stringify({
  meta: { release_id: "syn-2026-09-23-01", engine_version: "1.16.0", synthetic: true, preview: false },
  data: { signed_in: false, email: null },
});

/** A stand-in for the service, which keeps what it was sent and answers as it is told to. */
function service(answer: () => Response | Promise<Response> = () => answered()): Service {
  const reached: Reached[] = [];
  return {
    reached,
    fetch: (async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const body = init.body === undefined || init.body === null ? null : Buffer.from(init.body as Uint8Array).toString("utf8");
      reached.push({ url: String(input), method: init.method ?? "GET", headers: new Headers(init.headers), body, init });
      return answer();
    }) as typeof fetch,
  };
}

function answered(status = 200, headers: [string, string][] = [], body: string | null = ENVELOPE): Response {
  const all = new Headers([["Content-Type", "application/json"], ["X-Request-Id", "req-1"], ["X-Burro-Synthetic", "true"], ["X-Burro-Preview", "false"]]);
  for (const [name, value] of headers) all.append(name, value);
  return new Response(body, { status, headers: all });
}

function settings(to: Service, over: Partial<PassSettings> = {}): PassSettings {
  return { on: true, service: SERVICE, secret: SECRET, addressFrom: FROM_THE_HOST, development: false, fetch: to.fetch, ...over };
}

/** A request as a page of the website sends one that changes something. */
function changing(path: string, method = "POST", body: unknown = {}, headers: Record<string, string> = {}): Request {
  return new Request(`${SITE}${path}`, {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Origin: SITE,
      [REQUEST_HEADER]: "1",
      "Sec-Fetch-Site": "same-origin",
      [FROM_THE_HOST]: "203.0.113.9",
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

function asking(path: string, headers: Record<string, string> = {}): Request {
  return new Request(`${SITE}${path}`, {
    method: "GET",
    headers: { Accept: "application/json", [FROM_THE_HOST]: "203.0.113.9", ...headers },
  });
}

/** Everything of an answer that a browser is served: its status, every header and its body. */
async function served(answer: Response): Promise<string> {
  return JSON.stringify([answer.status, [...answer.headers], answer.headers.getSetCookie(), await answer.clone().text()]);
}

describe("with accounts off", () => {
  test("test_nothing_is_passed_on_and_the_answer_is_that_there_is_nothing_at_the_address", async () => {
    const to = service();

    for (const operation of ACCOUNT_OPERATIONS) {
      const { method, path } = ACCOUNT_ROUTES[operation];
      const request = method === "GET" ? asking(path) : changing(path, method);
      const answer = await pass(request, settings(to, { on: false }));

      expect([operation, answer.status, await answer.text()]).toEqual([operation, 404, ""]);
    }
    expect(to.reached).toEqual([]);
  });

  test("test_they_are_off_unless_the_one_setting_says_on", () => {
    const secret = { BURRO_WEBSITE_SECRET: SECRET, NEXT_PUBLIC_BURRO_API_URL: SERVICE };

    expect(settingsFrom({ ...secret }).on).toBe(false);
    for (const value of ["", "off", "true", "1", "yes", "ON", " on"]) {
      expect([value, settingsFrom({ ...secret, NEXT_PUBLIC_BURRO_ACCOUNTS: value }).on]).toEqual([value, false]);
    }
    expect(settingsFrom({ ...secret, NEXT_PUBLIC_BURRO_ACCOUNTS: "on" }).on).toBe(true);
  });
});

describe("what is passed on", () => {
  test("test_every_route_of_the_list_is_passed_to_the_same_route_of_the_service", async () => {
    for (const operation of ACCOUNT_OPERATIONS) {
      const to = service();
      const { method, path } = ACCOUNT_ROUTES[operation];
      const request = method === "GET" ? asking(path) : changing(path, method, { made: "up" });

      const answer = await pass(request, settings(to));

      expect([operation, answer.status]).toEqual([operation, 200]);
      expect(to.reached.map((one) => [one.method, one.url])).toEqual([[method, `${SERVICE}${path}`]]);
      expect(to.reached[0]?.body).toBe(method === "GET" ? null : JSON.stringify({ made: "up" }));
    }
  });

  test.each([
    ["GET", "/v1/me/searches/N6BkBdeSvd7xEk0NJVZNzw"],
    ["GET", "/v1/me/"],
    ["GET", "/v1/ME"],
    ["GET", "/v1/me/export/"],
    ["GET", "/v1/auth"],
    ["GET", "/v1/auth/link"],
    ["PUT", "/v1/auth/session"],
    ["POST", "/v1/me"],
    ["POST", "/v1/rank"],
    ["POST", "/v1/interpret"],
    ["GET", "/v1/meta"],
    ["GET", "/healthz"],
    ["GET", "/v1/me/%2e%2e/meta"],
    ["GET", "/v1/me/..%2fmeta"],
    ["GET", "//v1/me"],
    ["PATCH", "/v1/me/preferences"],
  ])("test_what_is_not_a_route_of_the_list_is_passed_nowhere: %s %s", async (method, path) => {
    const to = service();
    const request = method === "GET" ? asking(path) : changing(path, method);

    const answer = await pass(request, settings(to));

    expect([answer.status, await answer.text()]).toEqual([404, ""]);
    expect(to.reached).toEqual([]);
  });

  test("test_a_request_with_anything_after_a_question_mark_is_passed_nowhere", async () => {
    const to = service();

    const asked = await pass(asking(`/v1/me?as=${CANARY}`), settings(to));
    const changed = await pass(changing(`/v1/auth/link?email=${CANARY}`), settings(to));
    const bare = await pass(asking("/v1/me?"), settings(to));

    expect([asked.status, changed.status, bare.status]).toEqual([404, 404, 200]);
    // A bare question mark holds nothing, and nothing of it is passed on.
    expect(to.reached.map((one) => one.url)).toEqual([`${SERVICE}/v1/me`]);
  });

  test("test_only_the_headers_of_the_list_are_passed_on", async () => {
    const to = service();

    await pass(
      changing("/v1/auth/link", "POST", { email: "a@example.org" }, {
        Authorization: `Bearer ${CANARY}`,
        "X-Forwarded-For": "198.51.100.7",
        "X-Forwarded-Host": "elsewhere.example",
        Forwarded: "for=198.51.100.7",
        Referer: `${SITE}/sign-in?${CANARY}`,
        "X-Made-Up": CANARY,
        "If-None-Match": `"${CANARY}"`,
        "Accept-Language": "en-GB",
        "User-Agent": "Mozilla/5.0 (made up)",
      }),
      settings(to),
    );

    const passed = [...(to.reached[0]?.headers.keys() ?? [])].sort();
    expect(passed).toEqual(
      ["accept", "content-type", "origin", "user-agent", CLIENT_HEADER, REQUEST_HEADER, WEBSITE_HEADER].map((name) => name.toLowerCase()).sort(),
    );
    expect(JSON.stringify([...(to.reached[0]?.headers ?? [])]).includes(CANARY)).toBe(false);
  });

  test("test_the_service_is_never_asked_to_keep_an_answer_or_followed_elsewhere", async () => {
    const to = service();

    await pass(asking("/v1/me"), settings(to));

    expect(to.reached[0]?.init.redirect).toBe("manual");
    expect(to.reached[0]?.init.cache).toBe("no-store");
    expect(to.reached[0]?.init.signal).toBeInstanceOf(AbortSignal);
  });
});

describe("who the website says it is", () => {
  test("test_the_secret_reaches_the_service_and_is_in_nothing_a_browser_is_served", async () => {
    // The service answers with everything it was sent, as a service that was written wrongly might.
    const reached: Reached[] = [];
    const echoing: Service = {
      reached,
      fetch: (async (input: RequestInfo | URL, init: RequestInit = {}) => {
        const headers = new Headers(init.headers);
        reached.push({ url: String(input), method: init.method ?? "GET", headers, body: null, init });
        return answered(200, [...headers].map(([name, value]): [string, string] => [name, value]));
      }) as typeof fetch,
    };

    const answer = await pass(asking("/v1/auth/session"), settings(echoing));

    expect(reached[0]?.headers.get(WEBSITE_HEADER)).toBe(SECRET);
    expect((await served(answer)).includes(SECRET)).toBe(false);
    expect(answer.headers.has(WEBSITE_HEADER)).toBe(false);
  });

  test("test_a_secret_that_a_client_sent_is_not_passed_on_in_the_place_of_the_websites_own", async () => {
    const to = service();

    await pass(asking("/v1/me", { [WEBSITE_HEADER]: CANARY }), settings(to));

    expect(to.reached[0]?.headers.get(WEBSITE_HEADER)).toBe(SECRET);
  });

  test.each([
    null,
    "",
    "short",
    "x".repeat(SHORTEST_SECRET - 1),
    " ".repeat(SHORTEST_SECRET + 8),
    `${"x".repeat(SHORTEST_SECRET)} `,
    ` ${"x".repeat(SHORTEST_SECRET)}`,
    `${"x".repeat(SHORTEST_SECRET)}\n`,
    `${"x".repeat(SHORTEST_SECRET - 1)}\u00e9`,
    "x".repeat(513),
  ])(
    "test_with_no_secret_or_one_the_service_would_not_take_nothing_is_passed_on: %#",
    async (secret) => {
      const to = service();

      const answer = await pass(asking("/v1/me"), settings(to, { secret }));

      expect([answer.status, await answer.text()]).toEqual([503, ""]);
      expect(to.reached).toEqual([]);
    },
  );

  test("test_with_no_address_for_the_service_nothing_is_passed_on", async () => {
    const to = service();

    const answer = await pass(asking("/v1/me"), settings(to, { service: null }));

    expect([answer.status, await answer.text()]).toEqual([503, ""]);
    expect(to.reached).toEqual([]);
  });

  test.each([
    ["at another machine", "http://api.burro.example"],
    ["on the machine the website runs on", "http://127.0.0.1:8000"],
  ])("test_a_service_that_is_reached_in_the_clear_%s_is_passed_nothing", async (_, inTheClear) => {
    const to = service();
    const request = changing("/v1/auth/link/whose", "POST", { token: CANARY }, { Cookie: `${SESSION_COOKIE}=made-up-session` });

    const answer = await pass(request, settings(to, { service: inTheClear }));

    // Neither the secret, nor the cookie of a session, nor the body leaves the website in the clear.
    expect([answer.status, await answer.text()]).toEqual([503, ""]);
    expect(to.reached).toEqual([]);
  });

  test("test_on_a_machine_of_ones_own_the_service_is_reached_in_the_clear_as_the_website_is", async () => {
    const to = service();
    const here = new Request("http://127.0.0.1:3000/v1/auth/session");

    const answer = await pass(here, settings(to, { service: "http://127.0.0.1:8000", development: true, addressFrom: null }));

    expect(answer.status).toBe(200);
    expect(to.reached.map((one) => one.url)).toEqual(["http://127.0.0.1:8000/v1/auth/session"]);
    // Being developed lets nothing by that reached the website any other way.
    const elsewhere = await pass(asking("/v1/auth/session"), settings(to, { service: "http://127.0.0.1:8000", development: true }));
    expect(elsewhere.status).toBe(503);
    expect(to.reached).toHaveLength(1);
  });

  test("test_the_settings_are_read_from_the_environment_and_a_secret_is_held_to_its_length", () => {
    const read = settingsFrom({
      NEXT_PUBLIC_BURRO_ACCOUNTS: "on",
      NEXT_PUBLIC_BURRO_API_URL: `${SERVICE}/`,
      BURRO_WEBSITE_SECRET: SECRET,
      BURRO_CLIENT_ADDRESS_HEADER: "X-Real-IP",
    });

    expect(read).toEqual({ on: true, service: SERVICE, secret: SECRET, addressFrom: "x-real-ip", development: false });
    expect(settingsFrom({ BURRO_WEBSITE_SECRET: "short" }).secret).toBeNull();
    expect(settingsFrom({}).secret).toBeNull();
    expect(settingsFrom({}).addressFrom).toBeNull();
  });
});

describe("the address of the client", () => {
  test("test_it_is_what_the_websites_host_says_and_never_what_a_client_said", async () => {
    const to = service();

    await pass(
      asking("/v1/me", {
        [FROM_THE_HOST]: "203.0.113.9",
        [CLIENT_HEADER]: "198.51.100.7",
        "X-Forwarded-For": "198.51.100.8",
      }),
      settings(to),
    );

    expect(to.reached[0]?.headers.get(CLIENT_HEADER)).toBe("203.0.113.9");
    expect(JSON.stringify([...(to.reached[0]?.headers ?? [])]).includes("198.51.100")).toBe(false);
  });

  test.each([
    ["203.0.113.9", "203.0.113.9"],
    [" 203.0.113.9 ", "203.0.113.9"],
    ["2001:db8::7", "2001:db8::7"],
  ])("test_one_address_is_passed_on_as_the_host_gave_it: %s", async (given, passed) => {
    const to = service();

    await pass(asking("/v1/me", { [FROM_THE_HOST]: given }), settings(to));

    expect(to.reached[0]?.headers.get(CLIENT_HEADER) ?? null).toBe(passed);
  });

  test.each([
    ["two addresses", "203.0.113.9, 198.51.100.7"],
    ["words", "not an address"],
    ["an address and a port", "203.0.113.9:8080"],
    ["nothing", ""],
    ["what a client wrote before what the host wrote", `${CANARY}, 203.0.113.9`],
  ])("test_where_the_host_gave_what_is_no_one_address_nothing_is_passed_on: %s", async (_what, given) => {
    const to = service();

    const asked = await pass(asking("/v1/me", { [FROM_THE_HOST]: given }), settings(to));
    const changed = await pass(changing("/v1/auth/link", "POST", { email: "a@example.org" }, { [FROM_THE_HOST]: given }), settings(to));

    // Passed on with no address, each would be counted with every other of whom the
    // host said nothing: and ten requests from anybody would stop them all from signing in.
    expect([asked.status, await asked.text(), changed.status, await changed.text()]).toEqual([503, "", 503, ""]);
    expect(to.reached).toEqual([]);
  });

  test("test_where_the_host_gave_none_nothing_is_passed_on_whatever_a_client_said", async () => {
    const to = service();
    const said = { [CLIENT_HEADER]: "198.51.100.7", "X-Forwarded-For": "198.51.100.8" };

    const answer = await pass(new Request(`${SITE}/v1/me`, { headers: said }), settings(to));

    expect([answer.status, await answer.text()]).toEqual([503, ""]);
    expect(to.reached).toEqual([]);
  });

  test("test_with_no_header_of_the_host_named_nothing_is_passed_on", async () => {
    const to = service();

    // Left unset on a host, every client would be counted as one, and nobody would be told.
    for (const request of [asking("/v1/me", { [CLIENT_HEADER]: "198.51.100.7" }), changing("/v1/auth/link")]) {
      const answer = await pass(request, settings(to, { addressFrom: null }));
      expect([answer.status, await answer.text()]).toEqual([503, ""]);
    }
    expect(to.reached).toEqual([]);
    expect(settingsFrom({ BURRO_WEBSITE_SECRET: SECRET }).addressFrom).toBeNull();
  });

  test.each([
    ["with no header of the host named", null, {}],
    ["where the host gave none", FROM_THE_HOST, {}],
    ["where what it gave is no address", FROM_THE_HOST, { [FROM_THE_HOST]: "not an address" }],
  ])("test_on_a_machine_of_ones_own_a_request_is_passed_on_with_no_address: %s", async (_what, addressFrom, given) => {
    const to = service();
    const here = "http://127.0.0.1:3000";
    const request = new Request(`${here}/v1/me`, { headers: { [CLIENT_HEADER]: "198.51.100.7", ...given } });

    // No host stands before a website that is being developed, to say who asks.
    const answer = await pass(request, settings(to, { addressFrom, development: true }));

    expect(answer.status).toBe(200);
    expect(to.reached.map((one) => one.headers.has(CLIENT_HEADER))).toEqual([false]);
  });

  test.each([
    ["over TLS", "https://burro.example", true],
    ["at another machine", "http://192.0.2.4:3000", true],
    ["where it is not being developed", "http://127.0.0.1:3000", false],
  ])("test_anywhere_else_a_request_with_no_address_is_passed_nowhere: %s", async (_what, at, development) => {
    const to = service();

    const answer = await pass(new Request(`${at}/v1/me`), settings(to, { development }));

    expect([answer.status, await answer.text()]).toEqual([503, ""]);
    expect(to.reached).toEqual([]);
  });

  test.each(["x real ip", "x-real-ip: 1", "", "  ", "x".repeat(65), "x_real_ip\n"])(
    "test_a_setting_that_is_no_name_of_a_header_stops_everything_and_is_not_taken_for_none: %#",
    (value) => {
      // Taken for none, every client would be counted as one, and nobody would be told.
      const read = settingsFrom({ BURRO_WEBSITE_SECRET: SECRET, BURRO_CLIENT_ADDRESS_HEADER: value });

      expect(read.addressFrom).toBe(value.trim() === "" ? null : false);
    },
  );

  test("test_with_the_header_of_the_host_named_wrongly_nothing_is_passed_on", async () => {
    const to = service();

    const answer = await pass(asking("/v1/me"), settings(to, { addressFrom: false }));

    expect([answer.status, await answer.text()]).toEqual([503, ""]);
    expect(to.reached).toEqual([]);
  });
});

describe("the cookies", () => {
  test("test_only_the_two_cookies_of_accounts_are_passed_on", async () => {
    const to = service();

    await pass(
      asking("/v1/me", {
        Cookie: `theme=dark; ${SESSION_COOKIE}=made-up-session; other=${CANARY}; ${LINK_COOKIE}=made-up-binding; __Host-burro_sessionx=no`,
      }),
      settings(to),
    );

    expect(to.reached[0]?.headers.get("cookie")).toBe(`${SESSION_COOKIE}=made-up-session; ${LINK_COOKIE}=made-up-binding`);
  });

  test("test_with_no_cookie_of_accounts_none_is_passed_on", async () => {
    const to = service();

    await pass(asking("/v1/me", { Cookie: `theme=dark; other=${CANARY}` }), settings(to));
    await pass(asking("/v1/me"), settings(to));

    expect(to.reached.map((one) => one.headers.has("cookie"))).toEqual([false, false]);
  });

  test("test_a_cookie_the_service_sets_is_let_by_where_it_is_one_of_the_two_and_is_set_as_it_must_be", async () => {
    const session = `${SESSION_COOKIE}=made-up-session; Max-Age=2592000; Path=/; Secure; HttpOnly; SameSite=Lax`;
    const binding = `${LINK_COOKIE}=made-up-binding; Max-Age=900; Path=/; Secure; HttpOnly; SameSite=Lax`;
    const to = service(() => answered(200, [["Set-Cookie", session], ["Set-Cookie", binding]]));

    const answer = await pass(changing("/v1/auth/session"), settings(to));

    expect(answer.headers.getSetCookie()).toEqual([session, binding]);
  });

  test.each([
    ["of another name", `tracker=${CANARY}; Path=/; Secure; HttpOnly; SameSite=Lax`],
    ["for a domain", `${SESSION_COOKIE}=s; Domain=burro.example; Path=/; Secure; HttpOnly; SameSite=Lax`],
    ["that a script can read", `${SESSION_COOKIE}=s; Path=/; Secure; SameSite=Lax`],
    ["that is sent in the clear", `${SESSION_COOKIE}=s; Path=/; HttpOnly; SameSite=Lax`],
    ["that is sent across sites", `${SESSION_COOKIE}=s; Path=/; Secure; HttpOnly; SameSite=None`],
    ["that does not say where it is sent from", `${SESSION_COOKIE}=s; Path=/; Secure; HttpOnly`],
    ["for a part of the website", `${SESSION_COOKIE}=s; Path=/account; Secure; HttpOnly; SameSite=Lax`],
    ["with no path", `${SESSION_COOKIE}=s; Secure; HttpOnly; SameSite=Lax`],
    ["with no name", `=s; Path=/; Secure; HttpOnly; SameSite=Lax`],
    ["of a name that begins as one of the two", `${SESSION_COOKIE}2=s; Path=/; Secure; HttpOnly; SameSite=Lax`],
  ])("test_a_cookie_is_dropped_and_the_answer_is_passed_back_without_it: %s", async (_, cookie) => {
    const to = service(() => answered(200, [["Set-Cookie", cookie]]));

    const answer = await pass(changing("/v1/auth/session"), settings(to));

    expect(answer.status).toBe(200);
    expect(answer.headers.getSetCookie()).toEqual([]);
    expect(await answer.text()).toBe(ENVELOPE);
  });

  test("test_a_cookie_that_is_taken_away_is_let_by_as_one_that_is_set", async () => {
    const gone = `${SESSION_COOKIE}=; Max-Age=0; Path=/; Secure; HttpOnly; SameSite=Lax`;
    const to = service(() => answered(200, [["Set-Cookie", gone]]));

    const answer = await pass(changing("/v1/auth/session", "DELETE"), settings(to));

    expect(answer.headers.getSetCookie()).toEqual([gone]);
  });
});

describe("the cookies, where the website is being developed", () => {
  const HERE = "http://127.0.0.1:3000";
  const [session = "", binding = ""] = COOKIES_IN_THE_CLEAR;
  const plain = `${session}=made-up-session; Max-Age=2592000; Path=/; HttpOnly; SameSite=Lax`;
  const bound = `${binding}=made-up-binding; Max-Age=900; Path=/; HttpOnly; SameSite=Lax`;
  const here = (headers: Record<string, string> = {}) => new Request(`${HERE}/v1/auth/session`, { headers });

  test("test_it_is_being_developed_only_where_the_one_setting_says_yes", () => {
    expect(settingsFrom({}).development).toBe(false);
    for (const value of ["", "no", "on", "true", "1", "YES", " yes"]) {
      expect([value, settingsFrom({ BURRO_ACCOUNTS_DEVELOPMENT: value }).development]).toEqual([value, false]);
    }
    expect(settingsFrom({ BURRO_ACCOUNTS_DEVELOPMENT: "yes" }).development).toBe(true);
  });

  test("test_in_the_clear_on_this_machine_the_two_are_let_by_under_their_plain_names", async () => {
    expect(COOKIES_IN_THE_CLEAR).toEqual(["burro_session", "burro_link"]);
    const to = service(() => answered(200, [["Set-Cookie", plain], ["Set-Cookie", bound]]));

    const answer = await pass(here({ Cookie: `${session}=s; other=${CANARY}; ${binding}=b` }), settings(to, { development: true }));

    expect(answer.headers.getSetCookie()).toEqual([plain, bound]);
    expect(to.reached[0]?.headers.get("cookie")).toBe(`${session}=s; ${binding}=b`);
  });

  test.each(["http://localhost:3000", "http://[::1]:3000", "http://127.0.0.1"])("test_this_machine_is_known_by_each_of_its_names: %s", async (at) => {
    const to = service(() => answered(200, [["Set-Cookie", plain]]));

    const answer = await pass(new Request(`${at}/v1/auth/session`), settings(to, { development: true }));

    expect(answer.headers.getSetCookie()).toEqual([plain]);
  });

  test.each([
    ["it is not being developed", HERE, false],
    ["the website is reached over TLS", "https://127.0.0.1:3000", true],
    ["the website is reached at another machine", "http://burro.example", true],
    ["the website is reached at an address of the network", "http://192.168.1.20:3000", true],
    ["the name of the machine only begins as this one's", "http://localhost.elsewhere.example", true],
  ])("test_a_cookie_under_a_plain_name_is_dropped_both_ways_where_%s", async (_, at, development) => {
    const to = service(() => answered(200, [["Set-Cookie", plain], ["Set-Cookie", bound]]));

    // The host says whose request it is, as a host does: what is tried here is the cookies.
    const sent = { Cookie: `${session}=s; ${binding}=b`, [FROM_THE_HOST]: "203.0.113.9" };
    const answer = await pass(new Request(`${at}/v1/auth/session`, { headers: sent }), settings(to, { development }));

    expect(answer.status).toBe(200);
    expect(answer.headers.getSetCookie()).toEqual([]);
    expect(to.reached[0]?.headers.has("cookie")).toBe(false);
  });

  test.each([
    ["that a script can read", `${session}=s; Path=/; SameSite=Lax`],
    ["for a domain", `${session}=s; Domain=127.0.0.1; Path=/; HttpOnly; SameSite=Lax`],
    ["that is sent across sites", `${session}=s; Path=/; HttpOnly; SameSite=None`],
    ["for a part of the website", `${session}=s; Path=/account; HttpOnly; SameSite=Lax`],
    ["of another name", `burro_other=s; Path=/; HttpOnly; SameSite=Lax`],
  ])("test_in_development_a_cookie_is_held_to_all_else_that_it_is_held_to: %s", async (_, cookie) => {
    const to = service(() => answered(200, [["Set-Cookie", cookie]]));

    const answer = await pass(here(), settings(to, { development: true }));

    expect(answer.headers.getSetCookie()).toEqual([]);
  });

  test("test_the_two_are_let_by_under_their_own_names_in_development_as_anywhere", async () => {
    const held = `${SESSION_COOKIE}=made-up-session; Path=/; Secure; HttpOnly; SameSite=Lax`;
    const to = service(() => answered(200, [["Set-Cookie", held]]));

    const answer = await pass(here({ Cookie: `${SESSION_COOKIE}=s` }), settings(to, { development: true }));

    expect(answer.headers.getSetCookie()).toEqual([held]);
    expect(to.reached[0]?.headers.get("cookie")).toBe(`${SESSION_COOKIE}=s`);
  });
});

describe("a request that changes something", () => {
  test.each([
    ["without the header a page sends", { [REQUEST_HEADER]: "" }],
    ["with the header set to another value", { [REQUEST_HEADER]: "true" }],
    ["as a form sends it", { "Content-Type": "application/x-www-form-urlencoded" }],
    ["as plain text", { "Content-Type": "text/plain" }],
    ["from a page of another site", { "Sec-Fetch-Site": "cross-site" }],
    ["from a page of another part of the same site", { "Sec-Fetch-Site": "same-site" }],
    ["from the address bar", { "Sec-Fetch-Site": "none" }],
  ] as [string, Record<string, string>][])("test_it_is_passed_nowhere: %s", async (_, headers) => {
    for (const [path, method] of [["/v1/auth/link", "POST"], ["/v1/auth/session", "POST"], ["/v1/me", "DELETE"], ["/v1/me/preferences", "PUT"]] as const) {
      const to = service();
      const request = changing(path, method, {}, headers);
      if (headers[REQUEST_HEADER] === "") request.headers.delete(REQUEST_HEADER);

      const answer = await pass(request, settings(to));

      expect([path, answer.status, await answer.text()]).toEqual([path, 403, ""]);
      expect(to.reached).toEqual([]);
    }
  });

  test("test_a_browser_that_does_not_say_where_a_request_came_from_is_still_held_to_the_header", async () => {
    const to = service();
    const request = changing("/v1/auth/link");
    request.headers.delete("Sec-Fetch-Site");

    const answer = await pass(request, settings(to));

    expect(answer.status).toBe(200);
    expect(to.reached).toHaveLength(1);
  });

  test("test_json_with_its_character_set_named_is_json", async () => {
    const to = service();

    const answer = await pass(changing("/v1/auth/link", "POST", {}, { "Content-Type": "application/json; charset=utf-8" }), settings(to));

    expect(answer.status).toBe(200);
  });

  test("test_a_body_larger_than_the_service_takes_is_passed_nowhere", async () => {
    const to = service();
    const large = { email: "a".repeat(LARGEST_BODY) };

    const answer = await pass(changing("/v1/auth/link", "POST", large), settings(to));
    const within = await pass(changing("/v1/auth/link", "POST", { email: "a".repeat(LARGEST_BODY - 64) }), settings(to));

    expect([answer.status, await answer.text()]).toEqual([413, ""]);
    expect(within.status).toBe(200);
    expect(to.reached).toHaveLength(1);
  });

  test("test_a_body_that_says_it_is_shorter_than_it_is_is_held_to_what_it_holds", async () => {
    const to = service();
    const request = changing("/v1/auth/link", "POST", { email: "a".repeat(LARGEST_BODY) });
    request.headers.set("Content-Length", "12");

    const answer = await pass(request, settings(to));

    expect(answer.status).toBe(413);
    expect(to.reached).toEqual([]);
  });

  test("test_asking_changes_nothing_and_needs_neither", async () => {
    const to = service();

    const answer = await pass(new Request(`${SITE}/v1/auth/session`, { headers: { [FROM_THE_HOST]: "203.0.113.9" } }), settings(to));

    expect(answer.status).toBe(200);
    expect(to.reached[0]?.body).toBeNull();
  });
});

describe("what is passed back", () => {
  test("test_the_answer_of_the_service_is_passed_back_as_it_came", async () => {
    const refused = JSON.stringify({
      meta: { release_id: "syn-2026-09-23-01", engine_version: "1.16.0", synthetic: true, preview: false },
      error: { code: "rate_limited", message: "Burro has been asked to sign in too many times from here.", fields: [] },
    });
    const to = service(() => answered(429, [["Retry-After", "900"]], refused));

    const answer = await pass(changing("/v1/auth/link"), settings(to));

    expect(answer.status).toBe(429);
    expect(await answer.text()).toBe(refused);
    expect(Object.fromEntries(answer.headers)).toEqual({
      "cache-control": "no-store",
      "content-type": "application/json",
      "retry-after": "900",
      "x-burro-preview": "false",
      "x-burro-synthetic": "true",
      "x-content-type-options": "nosniff",
      "x-request-id": "req-1",
    });
  });

  test("test_only_the_headers_of_the_list_are_passed_back", async () => {
    const to = service(() =>
      answered(200, [
        ["Server", "made-up/1.0"],
        ["Access-Control-Allow-Origin", "*"],
        ["Access-Control-Allow-Credentials", "true"],
        ["Cache-Control", "public, max-age=3600"],
        ["ETag", `"${CANARY}"`],
        ["Location", `https://elsewhere.example/${CANARY}`],
        ["X-Made-Up", CANARY],
        ["Vary", "Origin"],
      ]),
    );

    const answer = await pass(asking("/v1/me"), settings(to));

    expect([...answer.headers.keys()].sort()).toEqual([
      "cache-control",
      "content-type",
      "x-burro-preview",
      "x-burro-synthetic",
      "x-content-type-options",
      "x-request-id",
    ]);
    // No browser may keep an answer of accounts, whatever the service said of it.
    expect(answer.headers.get("cache-control")).toBe("no-store");
    expect((await served(answer)).includes(CANARY)).toBe(false);
  });

  test.each([301, 302, 303, 307, 308])("test_the_service_is_never_followed_elsewhere: %s", async (status) => {
    const to = service(() => answered(status, [["Location", `https://elsewhere.example/${CANARY}`]], null));

    const answer = await pass(changing("/v1/auth/session"), settings(to));

    expect([answer.status, await answer.text()]).toEqual([502, ""]);
    expect(answer.headers.has("location")).toBe(false);
  });

  test("test_an_answer_that_is_not_json_is_not_passed_back", async () => {
    const to = service(() => new Response(`<html>${CANARY}</html>`, { status: 200, headers: { "Content-Type": "text/html" } }));

    const answer = await pass(asking("/v1/me"), settings(to));

    expect([answer.status, await answer.text()]).toEqual([502, ""]);
  });

  test("test_a_service_that_cannot_be_reached_is_answered_for_and_nothing_of_the_fault_is_said", async () => {
    const unreachable: Service = {
      reached: [],
      fetch: (async () => {
        throw new Error(`connect ECONNREFUSED ${CANARY}`);
      }) as typeof fetch,
    };

    const answer = await pass(changing("/v1/auth/link", "POST", { email: `${CANARY}@example.org` }), settings(unreachable));

    expect([answer.status, await answer.text()]).toEqual([502, ""]);
    expect((await served(answer)).includes(CANARY)).toBe(false);
  });

  test("test_a_service_that_does_not_answer_in_time_is_answered_for", async () => {
    const late: Service = {
      reached: [],
      fetch: (async () => {
        throw new DOMException("The operation timed out.", "TimeoutError");
      }) as typeof fetch,
    };

    const answer = await pass(asking("/v1/me"), settings(late));

    expect([answer.status, await answer.text()]).toEqual([504, ""]);
  });

  test("test_every_answer_of_the_route_says_that_no_browser_may_keep_it", async () => {
    const to = service();
    const answers = await Promise.all([
      pass(asking("/v1/me"), settings(to)),
      pass(asking("/v1/me"), settings(to, { on: false })),
      pass(asking("/v1/nothing"), settings(to)),
      pass(asking("/v1/me"), settings(to, { secret: null })),
      pass(changing("/v1/auth/link", "POST", {}, { "Sec-Fetch-Site": "cross-site" }), settings(to)),
    ]);

    for (const answer of answers) {
      expect([answer.status, answer.headers.get("cache-control"), answer.headers.get("x-content-type-options")]).toEqual([
        answer.status,
        "no-store",
        "nosniff",
      ]);
    }
  });
});

describe("what is written down", () => {
  test("test_nothing_is_written_to_the_console_whatever_becomes_of_a_request", async () => {
    const lines: unknown[][] = [];
    const spies = (["log", "info", "warn", "error", "debug"] as const).map((method) =>
      jest.spyOn(console, method).mockImplementation((...said: unknown[]) => {
        lines.push(said);
      }),
    );
    const failing: Service = {
      reached: [],
      fetch: (async () => {
        throw new Error(CANARY);
      }) as typeof fetch,
    };

    await pass(changing("/v1/auth/link", "POST", { email: `${CANARY}@example.org` }), settings(service()));
    await pass(changing("/v1/auth/link", "POST", { email: `${CANARY}@example.org` }), settings(failing));
    await pass(asking(`/v1/me?${CANARY}`), settings(service()));
    await pass(asking("/v1/me"), settings(service(), { secret: null }));

    spies.forEach((spy) => spy.mockRestore());
    expect(lines).toEqual([]);
  });
});
