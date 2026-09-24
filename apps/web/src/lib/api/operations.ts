/**
 * The routes of the contract, by operation id, with the types the contract gives them.
 *
 * Every type here is worked out from the generated schema. None is written by hand.
 */

import type { operations } from "./schema";

/** Every operation the website calls. `healthz` is left out: no page needs it. */
export type OperationId = Exclude<keyof operations, "healthz">;

type JsonOf<T> = T extends { readonly content: { readonly "application/json": infer Body } }
  ? Body
  : never;

/** The whole answer of an operation that went well: `meta` and `data`. */
export type EnvelopeOf<Op extends OperationId> = JsonOf<operations[Op]["responses"][200]>;

/** The `data` of an operation that went well. */
export type DataOf<Op extends OperationId> =
  EnvelopeOf<Op> extends { readonly data: infer Data } ? Data : never;

/** The body an operation is sent. `never` for a `GET`. */
export type BodyOf<Op extends OperationId> = operations[Op] extends {
  readonly requestBody: infer Request;
}
  ? JsonOf<NonNullable<Request>>
  : never;

type Route = {
  readonly method: "GET" | "POST";
  readonly path: string;
  readonly timeoutMs: number;
  /** True for an answer no browser may keep, though it is asked for with a `GET`. */
  readonly neverKept?: true;
};

/**
 * Where each operation is served, and how long the website waits for it:
 * 8 seconds for reading a sentence, which may wait on a model, 3 for place
 * search, which runs as a person types, 5 for the rest that depend on a
 * search, and 10 for what a page is built from.
 */
export const ROUTES = {
  interpret: { method: "POST", path: "/v1/interpret", timeoutMs: 8_000 },
  rank: { method: "POST", path: "/v1/rank", timeoutMs: 5_000 },
  explain_top: { method: "POST", path: "/v1/explanations", timeoutMs: 5_000 },
  compare: { method: "POST", path: "/v1/compare", timeoutMs: 5_000 },
  search_places: { method: "POST", path: "/v1/places/search", timeoutMs: 3_000 },
  create_share: { method: "POST", path: "/v1/shares", timeoutMs: 5_000 },
  get_share: { method: "GET", path: "/v1/shares/{share_id}", timeoutMs: 5_000 },
  list_areas: { method: "GET", path: "/v1/areas", timeoutMs: 10_000 },
  get_geometry: { method: "GET", path: "/v1/areas/geometry", timeoutMs: 10_000 },
  get_area: { method: "GET", path: "/v1/areas/{id_or_slug}", timeoutMs: 10_000 },
  // The census of one area. It is asked for when a person opens it, and is never kept.
  get_census: {
    method: "GET",
    path: "/v1/areas/{id_or_slug}/census",
    timeoutMs: 5_000,
    neverKept: true,
  },
  get_meta: { method: "GET", path: "/v1/meta", timeoutMs: 10_000 },
} as const satisfies Record<OperationId, Route>;

/** The path of a route, with its one parameter filled in where it has one. */
export function pathOf(operation: OperationId, parameter?: string): string {
  const template: string = ROUTES[operation].path;
  if (!template.includes("{")) return template;
  // An id from the release or from a share. It is never something a person typed.
  return template.replace(/\{[a-z_]+\}/, encodeURIComponent(parameter ?? ""));
}
