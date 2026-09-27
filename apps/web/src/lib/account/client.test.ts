/**
 * The routes of accounts, as the browser calls them. Each is asked of the website's own
 * origin, carries what is sent in its body and never in its address, and never throws.
 */

import { EMAIL, EVERY_ROUTE, held, META, SPEC, standInAccounts, TOKEN } from "../../../test/support/account";
import { createAccountClient, type AccountClient } from "./client";
import { REQUEST_HEADER } from "./names";
import type { AccountOperation } from "./routes";

const CANARY = "zqxcanary7431";

/** Calls every route once, with a body where it takes one. */
const EVERY_CALL: Record<AccountOperation, (client: AccountClient) => Promise<unknown>> = {
  ask_for_link: (client) => client.askForLink({ email: EMAIL }),
  whose_link: (client) => client.whoseLink({ token: TOKEN }),
  sign_in: (client) => client.signIn({ token: TOKEN, adult: false, other_browser: false }),
  get_session: (client) => client.getSession(),
  sign_out: (client) => client.signOut(),
  get_me: (client) => client.getMe(),
  delete_me: (client) => client.deleteMe(),
  keep_search: (client) => client.keepSearch({ spec: SPEC }),
  list_searches: (client) => client.listSearches(),
  forget_search: (client) => client.forgetSearch({ search_id: "N6BkBdeSvd7xEk0NJVs001" }),
  keep_recent: (client) => client.keepRecent({ spec: SPEC }),
  list_recent: (client) => client.listRecent(),
  forget_recent: (client) => client.forgetRecent(),
  set_preferences: (client) => client.setPreferences({ keep_recent: "off" }),
  list_sessions: (client) => client.listSessions(),
  end_sessions: (client) => client.endSessions({ session_id: "N6BkBdeSvd7xEk0NJVc002", everywhere: false }),
  export_me: (client) => client.exportMe(),
};

describe("the routes of accounts, as the browser calls them", () => {
  test.each(EVERY_ROUTE)("test_a_route_is_asked_of_the_websites_own_origin_by_its_path_alone: $operation", async ({ operation, method, path }) => {
    const to = standInAccounts(held({ signedIn: true }));

    await EVERY_CALL[operation](to.client);

    expect(to.calls.map((call) => [call.method, call.url])).toEqual([[method, path]]);
    // The address holds the path of the list and nothing else: no origin, no query, no fragment.
    expect(to.calls[0]?.url).toMatch(/^\/v1\/(auth|me)(\/[a-z]+)*$/);
  });

  test.each(EVERY_ROUTE)("test_the_cookie_goes_to_the_websites_own_origin_and_nothing_is_kept_or_followed: $operation", async ({ operation }) => {
    const to = standInAccounts(held({ signedIn: true }));

    await EVERY_CALL[operation](to.client);

    const { init } = to.lastCallTo(operation);
    expect([init.credentials, init.cache, init.redirect, init.referrerPolicy]).toEqual([
      "same-origin",
      "no-store",
      "error",
      "no-referrer",
    ]);
    expect(init.signal).toBeInstanceOf(AbortSignal);
  });

  test.each(EVERY_ROUTE)("test_what_changes_something_says_so_and_what_asks_does_not: $operation", async ({ operation, method }) => {
    const to = standInAccounts(held({ signedIn: true }));

    await EVERY_CALL[operation](to.client);

    const call = to.lastCallTo(operation);
    const changes = method !== "GET";
    expect(call.headers.get(REQUEST_HEADER)).toBe(changes ? "1" : null);
    expect(call.headers.get("content-type")).toBe(changes ? "application/json" : null);
    expect(call.headers.get("accept")).toBe("application/json");
    // A body is JSON, and holds nothing where there is nothing to say. A `GET` has none.
    expect(call.sent === null).toBe(!changes);
    if (changes) expect(typeof call.body).toBe("object");
    // No header holds a cookie, a token or a secret: the browser adds the cookie itself.
    expect([...call.headers.keys()].sort()).toEqual(
      changes ? ["accept", "content-type", REQUEST_HEADER.toLowerCase()] : ["accept"],
    );
  });

  test("test_an_address_a_token_and_a_search_travel_in_a_body_and_never_in_an_address", async () => {
    const to = standInAccounts(held({ signedIn: true }));

    await to.client.askForLink({ email: `${CANARY}@example.org` });
    await to.client.whoseLink({ token: CANARY });
    await to.client.signIn({ token: CANARY, adult: true, other_browser: false });
    await to.client.forgetSearch({ search_id: CANARY });
    await to.client.endSessions({ session_id: CANARY, everywhere: false });

    expect(to.calls).toHaveLength(5);
    for (const call of to.calls) {
      expect([call.url.includes(CANARY), JSON.stringify([...call.headers]).includes(CANARY)]).toEqual([false, false]);
      expect(call.sent?.includes(CANARY)).toBe(true);
    }
  });

  test("test_an_answer_that_went_well_brings_what_the_service_said", async () => {
    const to = standInAccounts(held({ signedIn: true }));

    const session = await to.client.getSession();
    const link = await to.client.askForLink({ email: EMAIL });

    expect(session).toMatchObject({ ok: true, status: 200, data: { signed_in: true, email: EMAIL }, meta: META });
    expect(link).toMatchObject({ ok: true, status: 202, data: { lasts_minutes: 15 } });
  });

  test("test_a_refusal_is_a_value_with_the_services_own_words_and_the_id_to_quote", async () => {
    const to = standInAccounts().on("ask_for_link", "rate_limited");

    const answer = await to.client.askForLink({ email: `${CANARY}@example.org` });

    expect(answer.ok).toBe(false);
    if (answer.ok) return;
    expect(answer.failure).toMatchObject({ kind: "api", status: 429, code: "rate_limited" });
    expect(answer.failure.requestId).toMatch(/^req-/);
    expect(JSON.stringify(answer).includes(CANARY)).toBe(false);
  });

  test("test_an_answer_that_says_nobody_is_signed_in_is_heard_whatever_was_asked", async () => {
    const heard: string[] = [];
    const to = standInAccounts(held({ signedIn: false }));
    const client = createAccountClient({ fetch: to.fetch, on: true, onSignedOut: () => heard.push("out") });

    await client.getSession();
    expect(heard).toEqual([]);
    await client.getMe();
    await client.keepSearch({ spec: SPEC });
    await client.listSessions();

    expect(heard).toEqual(["out", "out", "out"]);
  });

  test("test_what_every_answer_says_of_its_data_is_told_to_the_banners", async () => {
    const synthetic: boolean[] = [];
    const said: unknown[] = [];
    const to = standInAccounts();
    const client = createAccountClient({
      fetch: to.fetch,
      on: true,
      onSynthetic: (made) => synthetic.push(made),
      onSaid: (one) => said.push(one),
    });

    await client.getSession();
    await client.getMe();

    expect(synthetic).toEqual([true, true]);
    expect(said).toEqual([
      { synthetic: true, preview: false },
      { synthetic: true, preview: false },
    ]);
  });

  test("test_with_accounts_off_nothing_is_sent", async () => {
    const to = standInAccounts();
    const client = createAccountClient({ fetch: to.fetch, on: false });

    for (const call of Object.values(EVERY_CALL)) {
      expect(await call(client)).toMatchObject({ ok: false, failure: { kind: "not_configured" } });
    }
    expect(to.calls).toEqual([]);
  });

  test("test_whether_accounts_are_on_is_what_the_one_setting_says_where_nothing_else_is_said", async () => {
    const to = standInAccounts();
    const client = createAccountClient({ fetch: to.fetch });

    expect(await client.getSession()).toMatchObject({ ok: false, failure: { kind: "not_configured" } });
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";
    try {
      expect(await client.getSession()).toMatchObject({ ok: true });
    } finally {
      delete process.env.NEXT_PUBLIC_BURRO_ACCOUNTS;
    }
    expect(to.calls).toHaveLength(1);
  });

  test.each([
    ["a request that could not leave", () => Promise.reject(new TypeError(`Failed to fetch ${CANARY}`)), "network"],
    ["an answer that is no JSON", () => Promise.resolve(new Response(`<html>${CANARY}</html>`, { status: 502 })), "unreadable"],
    ["an answer with no body", () => Promise.resolve(new Response(null, { status: 503 })), "unreadable"],
    ["an answer that is not the envelope of the service", () => Promise.resolve(Response.json({ signed_in: true, email: CANARY })), "unreadable"],
    [
      "an answer that lacks what the contract requires of it",
      () => Promise.resolve(Response.json({ meta: META, data: { signed_in: true } })),
      "unreadable",
    ],
    [
      "an error that is not of the shape of one",
      () => Promise.resolve(Response.json({ meta: META, error: { code: 7, message: CANARY } }, { status: 500 })),
      "unreadable",
    ],
    [
      "data beside an error",
      () => Promise.resolve(Response.json({ meta: META, error: CANARY, data: { signed_in: true, email: CANARY } })),
      "unreadable",
    ],
  ])("test_a_call_never_throws_and_says_why_it_gave_no_answer: %s", async (_, answers, kind) => {
    const client = createAccountClient({ fetch: answers as unknown as typeof fetch, on: true });

    const answer = await client.getSession();

    expect(answer).toMatchObject({ ok: false, failure: { kind } });
    // A failure holds codes and fixed words, and never anything that was sent or answered.
    expect(JSON.stringify(answer).includes(CANARY)).toBe(false);
  });

  test("test_a_call_that_was_stopped_says_so_and_one_that_is_stopped_before_it_leaves_sends_nothing", async () => {
    const to = standInAccounts();
    const stopped = new AbortController();
    stopped.abort();

    expect(await to.client.getSession(stopped.signal)).toMatchObject({ ok: false, failure: { kind: "aborted" } });
    expect(to.calls).toEqual([]);

    const waits = to.hold("get_session");
    const stops = new AbortController();
    const asked = to.client.getSession(stops.signal);
    stops.abort();
    waits.release();

    expect(await asked).toMatchObject({ ok: false, failure: { kind: "aborted" } });
  });

  test("test_nothing_is_written_to_the_console_or_kept_in_the_browser", async () => {
    const lines: unknown[][] = [];
    const spies = (["log", "info", "warn", "error", "debug"] as const).map((method) =>
      jest.spyOn(console, method).mockImplementation((...said: unknown[]) => {
        lines.push(said);
      }),
    );
    const kept = jest.spyOn(Storage.prototype, "setItem");
    const to = standInAccounts().on("ask_for_link", "sign_in_unavailable").unreachable("get_me");

    await to.client.askForLink({ email: `${CANARY}@example.org` });
    await to.client.getMe();
    await to.client.whoseLink({ token: TOKEN });

    spies.forEach((spy) => spy.mockRestore());
    expect(lines).toEqual([]);
    expect(kept).not.toHaveBeenCalled();
  });
});
