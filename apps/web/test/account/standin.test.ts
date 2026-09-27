/** @jest-environment node */
/**
 * The stand-in for the routes of accounts is held to the contract: what it answers is
 * what the contract says the service answers, for every route, and what it refuses with
 * is a refusal of the contract. So a page that is tested against it is tested against the
 * service as it is promised, until the service's own answers are recorded.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import Ajv2020 from "ajv/dist/2020";

import { ACCOUNT, KEEP } from "@/content/account";
import { ACCOUNT_OPERATIONS, ACCOUNT_ROUTES, type AccountOperation } from "@/lib/account/routes";

import { EMAIL, held, messageOf, SPEC, standInAccounts, TOKEN } from "../support/account";

interface Contract {
  readonly paths: Record<string, Record<string, { readonly operationId: string; readonly responses: Record<string, unknown> }>>;
  readonly components: { readonly schemas: { readonly ErrorCode: { readonly enum: readonly string[] } } };
}

const FILE = path.resolve(__dirname, "..", "..", "..", "..", "contracts", "openapi.json");
const contract = JSON.parse(readFileSync(FILE, "utf8")) as Contract;
const ajv = new Ajv2020({ strict: false, allErrors: true, validateFormats: false });
ajv.addSchema(contract, "contract");

const escaped = (part: string) => part.replace(/~/g, "~0").replace(/\//g, "~1");

/** What is wrong with an answer as the contract has it for that route and status: where and what kind, and never the value. */
function problemsWith(operation: AccountOperation, status: number, body: unknown): string[] {
  const { method, path: route } = ACCOUNT_ROUTES[operation];
  const at = ["paths", route, method.toLowerCase(), "responses", String(status), "content", "application/json", "schema"];
  const validate = ajv.getSchema(`contract#/${at.map(escaped).join("/")}`);
  if (!validate) return [`the contract has no answer of ${status} for ${operation}`];
  validate(body);
  return (validate.errors ?? []).map((error) => `${error.instancePath} ${error.keyword}`);
}

/** What each route is sent, where it takes a body. */
const SENT: Partial<Record<AccountOperation, unknown>> = {
  ask_for_link: { email: EMAIL },
  whose_link: { token: TOKEN },
  sign_in: { token: TOKEN, adult: false, other_browser: false },
  keep_search: { spec: SPEC },
  keep_recent: { spec: SPEC },
  set_preferences: { keep_recent: "off" },
};

async function asked(operation: AccountOperation, state = held({ signedIn: true })) {
  const to = standInAccounts(state);
  const { method, path: route } = ACCOUNT_ROUTES[operation];
  const body =
    operation === "forget_search"
      ? { search_id: state.searches[0]?.search_id }
      : operation === "end_sessions"
        ? { session_id: state.sessions[1]?.session_id, everywhere: false }
        : SENT[operation];
  const answer = await to.fetch(route, { method, ...(method === "GET" ? {} : { body: JSON.stringify(body ?? {}) }) });
  return { status: answer.status, body: (await answer.json()) as unknown };
}

describe("the stand-in for the routes of accounts", () => {
  test.each(ACCOUNT_OPERATIONS)("test_what_it_answers_is_what_the_contract_says_the_service_answers: %s", async (operation) => {
    const { status, body } = await asked(operation);

    expect([operation, status]).toEqual([operation, operation === "ask_for_link" ? 202 : 200]);
    expect([operation, problemsWith(operation, status, body)]).toEqual([operation, []]);
  });

  test("test_what_it_refuses_with_is_a_refusal_of_the_contract", async () => {
    const signedOut = ACCOUNT_OPERATIONS.filter((operation) => ACCOUNT_ROUTES[operation].path.startsWith("/v1/me"));

    expect(signedOut.length).toBeGreaterThan(10);
    for (const operation of signedOut) {
      const { status, body } = await asked(operation, held({ signedIn: false }));
      expect([operation, status, problemsWith(operation, status, body)]).toEqual([operation, 401, []]);
      expect(contract.components.schemas.ErrorCode.enum).toContain((body as { error: { code: string } }).error.code);
    }
  });

  test("test_what_it_refuses_a_search_with_says_of_it_what_the_page_beside_it_says", () => {
    // A page shows a refusal as it came, under words of its own, so the two are read as one.
    expect([KEEP.save, ACCOUNT.searches.title, ACCOUNT.searches.remove]).toEqual(["Save this search", "Saved searches", "Remove"]);
    for (const refused of ["too_many_searches", "search_not_found"] as const) {
      expect(messageOf(refused)).toMatch(/\bsaved\b/);
      // The website says "keep" of another thing: a person's last searches.
      expect(messageOf(refused)).not.toMatch(/\b(keep|kept|take|taken)\b/i);
    }
    expect(messageOf("too_many_searches")).toContain("Remove one and you can save this one.");
  });

  test("test_a_link_that_was_asked_for_elsewhere_is_not_taken_without_being_asked_and_no_account_is_made_unsaid", async () => {
    const elsewhere = standInAccounts(held({ sameBrowser: false }));
    const first = standInAccounts(held({ newAccount: true }));
    const send = (to: typeof elsewhere, body: unknown) =>
      to.fetch("/v1/auth/session", { method: "POST", body: JSON.stringify(body) }).then((answer) => answer.status);

    expect(await send(elsewhere, { token: TOKEN, adult: false, other_browser: false })).toBe(409);
    expect(elsewhere.held.signedIn).toBe(false);
    expect(await send(elsewhere, { token: TOKEN, adult: false, other_browser: true })).toBe(200);
    expect(await send(first, { token: TOKEN, adult: false, other_browser: false })).toBe(409);
    expect(first.held.signedIn).toBe(false);
    expect(await send(first, { token: TOKEN, adult: true, other_browser: false })).toBe(200);
  });

  test("test_asking_changes_nothing_of_what_is_held", async () => {
    const state = held({ signedIn: true });
    const before = JSON.stringify(state);

    for (const operation of ACCOUNT_OPERATIONS.filter((one) => ACCOUNT_ROUTES[one].method === "GET" || one === "whose_link")) {
      await asked(operation, state);
      expect([operation, JSON.stringify(state) === before]).toEqual([operation, true]);
    }
  });
});
