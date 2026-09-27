/** @jest-environment node */
/**
 * The routes of accounts are a closed list, which the browser's client and the route that
 * passes on both read. It is held here to the contract: every route the contract has
 * under `/v1/auth` and `/v1/me` is on the list, and nothing else is.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { ROUTES } from "@/lib/api/operations";
import { REQUIRED_IN_DATA } from "@/lib/api/required";

import { REQUIRED_OF_A_LINK } from "./client";
import { ACCOUNT_OPERATIONS, ACCOUNT_ROUTES, routeOf, STEMS } from "./routes";

interface Operation {
  readonly operationId: string;
  readonly parameters?: readonly unknown[];
  readonly requestBody?: { readonly content: Record<string, { readonly schema: { readonly $ref?: string } }> };
  readonly responses: Record<string, { readonly content?: Record<string, { readonly schema: { readonly $ref?: string } }> }>;
}

interface Contract {
  readonly paths: Record<string, Record<string, Operation>>;
  readonly components: { readonly schemas: Record<string, { readonly required?: readonly string[]; readonly properties?: Record<string, { readonly $ref?: string }> }> };
}

const contract = JSON.parse(
  readFileSync(path.resolve(__dirname, "..", "..", "..", "..", "..", "contracts", "openapi.json"), "utf8"),
) as Contract;

const isOfAccounts = (route: string) => STEMS.some((stem) => route === stem || route.startsWith(`${stem}/`));

/** Every route of accounts in the contract, as the list writes one. */
const inContract = Object.entries(contract.paths)
  .filter(([route]) => isOfAccounts(route))
  .flatMap(([route, methods]) =>
    Object.entries(methods).map(([method, operation]) => ({ id: operation.operationId, method: method.toUpperCase(), path: route, operation })),
  );

describe("the routes of accounts", () => {
  test("test_the_list_is_every_route_of_accounts_in_the_contract_and_nothing_else", () => {
    const listed = ACCOUNT_OPERATIONS.map((id) => [id, ACCOUNT_ROUTES[id].method, ACCOUNT_ROUTES[id].path]).sort();

    expect(inContract.length).toBeGreaterThanOrEqual(17);
    expect(listed).toEqual(inContract.map(({ id, method, path: route }) => [id, method, route]).sort());
  });

  test("test_no_route_of_accounts_is_called_of_the_api_itself_and_every_other_route_is", () => {
    // A route of accounts is asked of the website's own origin, which holds the cookie.
    const ofTheApi = Object.keys(ROUTES);
    const every = Object.values(contract.paths).flatMap((methods) => Object.values(methods).map((operation) => operation.operationId));

    expect(ofTheApi.filter((id) => (ACCOUNT_OPERATIONS as string[]).includes(id))).toEqual([]);
    expect([...ofTheApi, ...ACCOUNT_OPERATIONS, "healthz"].sort()).toEqual([...every].sort());
  });

  test("test_no_route_takes_anything_in_its_path_or_after_a_question_mark", () => {
    // What a request is about travels in its body, so that no id, address or token is in
    // the log of whatever serves the website, which holds the path of a request.
    for (const { id, path: route, operation } of inContract) {
      expect([id, /[{}?#]/.test(route), operation.parameters ?? []]).toEqual([id, false, []]);
    }
    for (const id of ACCOUNT_OPERATIONS) expect(ACCOUNT_ROUTES[id].path).toMatch(/^\/v1\/(auth|me)(\/[a-z]+)*$/);
  });

  test("test_a_get_takes_no_body_and_whatever_takes_one_is_no_get", () => {
    const withABody = inContract.filter(({ operation }) => operation.requestBody !== undefined);

    expect(withABody.length).toBeGreaterThan(5);
    expect(withABody.filter(({ method }) => method === "GET").map(({ id }) => id)).toEqual([]);
  });

  test("test_a_route_is_found_by_its_method_and_its_path_to_the_letter", () => {
    expect(routeOf("GET", "/v1/me")).toBe("get_me");
    expect(routeOf("DELETE", "/v1/me")).toBe("delete_me");
    expect(routeOf("POST", "/v1/auth/link/whose")).toBe("whose_link");
    for (const [method, route] of [
      ["get", "/v1/me"],
      ["GET", "/v1/me/"],
      ["GET", "/v1/Me"],
      ["GET", "v1/me"],
      ["POST", "/v1/me"],
      ["GET", "/v1/me/searches/N6BkBdeSvd7xEk0NJVZNzw"],
      ["GET", ""],
    ] as const) {
      expect([method, route, routeOf(method, route)]).toEqual([method, route, null]);
    }
  });

  test("test_what_an_answer_must_hold_is_known_for_every_route_of_the_list", () => {
    const required = REQUIRED_IN_DATA as Readonly<Record<string, readonly string[]>>;
    // What is generated lists what an answer of 200 must hold. Asking for a link is answered 202.
    const unlisted = ACCOUNT_OPERATIONS.filter((id) => required[id] === undefined);

    expect(unlisted).toEqual(["ask_for_link"]);
    const asked = inContract.find(({ id }) => id === "ask_for_link");
    const envelope = asked?.operation.responses["202"]?.content?.["application/json"]?.schema.$ref?.split("/").pop() ?? "";
    const data = contract.components.schemas[envelope]?.properties?.data?.$ref?.split("/").pop() ?? "";
    expect(contract.components.schemas[data]?.required).toEqual([...REQUIRED_OF_A_LINK]);
  });
});
