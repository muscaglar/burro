/**
 * The routes of accounts: a closed list, by the id the contract gives each.
 *
 * The browser asks them of the website's own origin, and the website passes them on to
 * the service. Both read this one list. What is not on it is asked by no page, and is
 * passed on by nothing. A test holds the list to the contract: every route the contract
 * has under `/v1/auth` and `/v1/me` is here, and nothing else is.
 *
 * No route takes anything in its path or after a `?`. What a request is about travels in
 * its body: an address, a token, a search, the id of a session. So none of them can reach
 * the log of whatever serves the website, which holds the path of a request.
 */

export type AccountMethod = "GET" | "POST" | "PUT" | "DELETE";

export interface AccountRoute {
  readonly method: AccountMethod;
  readonly path: string;
  /** How long the browser waits for it, in milliseconds. */
  readonly timeoutMs: number;
}

/**
 * Where each is served, and how long the browser waits for it. Asking for a link waits
 * on a sender of email, which is another company's service, so it is given longest.
 */
export const ACCOUNT_ROUTES = {
  ask_for_link: { method: "POST", path: "/v1/auth/link", timeoutMs: 15_000 },
  whose_link: { method: "POST", path: "/v1/auth/link/whose", timeoutMs: 8_000 },
  sign_in: { method: "POST", path: "/v1/auth/session", timeoutMs: 8_000 },
  get_session: { method: "GET", path: "/v1/auth/session", timeoutMs: 8_000 },
  sign_out: { method: "DELETE", path: "/v1/auth/session", timeoutMs: 8_000 },
  get_me: { method: "GET", path: "/v1/me", timeoutMs: 8_000 },
  delete_me: { method: "DELETE", path: "/v1/me", timeoutMs: 8_000 },
  keep_search: { method: "POST", path: "/v1/me/searches", timeoutMs: 8_000 },
  list_searches: { method: "GET", path: "/v1/me/searches", timeoutMs: 8_000 },
  forget_search: { method: "DELETE", path: "/v1/me/searches", timeoutMs: 8_000 },
  keep_recent: { method: "POST", path: "/v1/me/recent", timeoutMs: 8_000 },
  list_recent: { method: "GET", path: "/v1/me/recent", timeoutMs: 8_000 },
  forget_recent: { method: "DELETE", path: "/v1/me/recent", timeoutMs: 8_000 },
  set_preferences: { method: "PUT", path: "/v1/me/preferences", timeoutMs: 8_000 },
  list_sessions: { method: "GET", path: "/v1/me/sessions", timeoutMs: 8_000 },
  end_sessions: { method: "DELETE", path: "/v1/me/sessions", timeoutMs: 8_000 },
  export_me: { method: "GET", path: "/v1/me/export", timeoutMs: 15_000 },
} as const satisfies Record<string, AccountRoute>;

export type AccountOperation = keyof typeof ACCOUNT_ROUTES;

export const ACCOUNT_OPERATIONS = Object.keys(ACCOUNT_ROUTES) as AccountOperation[];

/** The two stems every route of accounts begins with. The website passes on nothing that begins otherwise. */
export const STEMS = ["/v1/auth", "/v1/me"] as const;

/**
 * The route a request is for, or `null` where it is for none of the list. A path is held
 * to a route whole and to the letter: one with a slash too many is no route, and nor is
 * one that differs in a capital.
 */
export function routeOf(method: string, path: string): AccountOperation | null {
  return (
    ACCOUNT_OPERATIONS.find((operation) => {
      const route: AccountRoute = ACCOUNT_ROUTES[operation];
      return route.method === method && route.path === path;
    }) ?? null
  );
}
