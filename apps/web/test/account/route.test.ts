/** @jest-environment node */
/**
 * The two routes of the website that pass the routes of accounts on. Each hands every
 * method to the one function that passes on, and is asked for each time.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import * as auth from "@/app/v1/auth/[...path]/route";
import * as me from "@/app/v1/me/[[...path]]/route";

const APP = path.resolve(__dirname, "..", "..", "src", "app");
const METHODS = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"] as const;
const SITE = "https://burro.example";

function routesUnder(folder: string, found: string[] = []): string[] {
  for (const entry of readdirSync(folder, { withFileTypes: true })) {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) routesUnder(file, found);
    else if (/^route\.(ts|tsx|js)$/.test(entry.name)) found.push(path.relative(APP, file));
  }
  return found;
}

afterEach(() => {
  delete process.env.NEXT_PUBLIC_BURRO_ACCOUNTS;
  delete process.env.NEXT_PUBLIC_BURRO_API_URL;
  delete process.env.BURRO_WEBSITE_SECRET;
  delete process.env.BURRO_CLIENT_ADDRESS_HEADER;
});

describe("the routes of the website", () => {
  test("test_the_website_has_two_routes_and_both_pass_the_routes_of_accounts_on", () => {
    expect(routesUnder(APP).sort()).toEqual([path.join("v1", "auth", "[...path]", "route.ts"), path.join("v1", "me", "[[...path]]", "route.ts")]);
    // The two are one file written twice: a route is found by where its file stands.
    const written = routesUnder(APP).map((route) => readFileSync(path.join(APP, route), "utf8"));
    expect(written[0]).toBe(written[1]);
  });

  test.each([
    ["auth", auth],
    ["me", me],
  ] as const)("test_every_method_is_answered_by_the_one_function_that_passes_on: %s", (_, route) => {
    const handed = Object.keys(route).filter((name) => name !== "dynamic").sort();

    expect(handed).toEqual([...METHODS]);
    expect(new Set(METHODS.map((method) => route[method])).size).toBe(1);
    // It is asked for each time, and nothing of an answer is kept.
    expect(route.dynamic).toBe("force-dynamic");
  });

  test.each(METHODS)("test_with_accounts_off_every_method_is_answered_that_there_is_nothing_at_the_address: %s", async (method) => {
    const sent = jest.fn();
    globalThis.fetch = sent as unknown as typeof fetch;

    for (const [route, at] of [
      [auth, "/v1/auth/session"],
      [me, "/v1/me"],
    ] as const) {
      const answer = await route[method](new Request(`${SITE}${at}`, { method }));

      expect([at, answer.status, await answer.text(), answer.headers.has("allow")]).toEqual([at, 404, "", false]);
    }
    expect(sent).not.toHaveBeenCalled();
  });

  test.each(["HEAD", "OPTIONS", "PATCH"] as const)("test_a_method_no_route_of_the_list_takes_is_passed_nowhere_with_accounts_on: %s", async (method) => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";
    process.env.NEXT_PUBLIC_BURRO_API_URL = "https://api.burro.example";
    process.env.BURRO_WEBSITE_SECRET = "made-up-in-a-test-".padEnd(40, "x");
    const sent = jest.fn();
    globalThis.fetch = sent as unknown as typeof fetch;

    const answer = await me[method](new Request(`${SITE}/v1/me`, { method }));

    expect([answer.status, await answer.text()]).toEqual([404, ""]);
    expect(sent).not.toHaveBeenCalled();
  });

  test("test_with_accounts_on_a_route_of_the_list_is_passed_on_with_the_settings_of_the_environment", async () => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";
    process.env.NEXT_PUBLIC_BURRO_API_URL = "https://api.burro.example/";
    process.env.BURRO_WEBSITE_SECRET = "made-up-in-a-test-".padEnd(40, "x");
    process.env.BURRO_CLIENT_ADDRESS_HEADER = "x-real-ip";
    const reached: [string, RequestInit][] = [];
    globalThis.fetch = (async (input: RequestInfo | URL, init: RequestInit = {}) => {
      reached.push([String(input), init]);
      return Response.json({ meta: {}, data: {} });
    }) as typeof fetch;

    const answer = await auth.GET(new Request(`${SITE}/v1/auth/session`, { headers: { "x-real-ip": "203.0.113.9" } }));

    expect(answer.status).toBe(200);
    expect(reached.map(([url]) => url)).toEqual(["https://api.burro.example/v1/auth/session"]);
  });

  test("test_with_accounts_on_and_nothing_said_of_whose_request_it_is_nothing_is_passed_on", async () => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";
    process.env.NEXT_PUBLIC_BURRO_API_URL = "https://api.burro.example/";
    process.env.BURRO_WEBSITE_SECRET = "made-up-in-a-test-".padEnd(40, "x");
    const sent = jest.fn();
    globalThis.fetch = sent as unknown as typeof fetch;

    // The header of the host is not named, as it is not where it was forgotten.
    const answer = await auth.GET(new Request(`${SITE}/v1/auth/session`, { headers: { "x-real-ip": "203.0.113.9" } }));

    expect([answer.status, await answer.text()]).toEqual([503, ""]);
    expect(sent).not.toHaveBeenCalled();
  });
});
