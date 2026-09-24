/**
 * A stand-in for the API that answers one person's whole visit, and nothing else.
 *
 * `test/record.py` records the visit from the real service, each request made
 * of the answer before it. This stand-in answers a request only if it is one
 * of those, to the letter: the same route and the same body. Anything else is
 * kept as unanswered, and the test that uses it expects none. So a visit that
 * passes here is a visit the service answered, request for request.
 *
 * What is a function of the release alone is answered from the recordings
 * every test uses: an area's profile and the boundaries. So is the form, which
 * the page asks for as it opens, to hear from the service who reads what is typed.
 */

import { createClient, type Client } from "@/lib/api/client";
import { readRecorded, recordedFolder, responseFrom, type Recorded } from "@/lib/api/recorded";

import { readdirSync } from "node:fs";
import path from "node:path";

import { aMomentLater, BASE } from "./api";

/** The steps of the visit, in the order they were recorded. */
export function stepsOfTheVisit(): readonly Recorded[] {
  return readdirSync(path.join(recordedFolder(), "visit"))
    .sort()
    .map((file) => readRecorded(`visit/${file.replace(/\.json$/, "")}`));
}

/** One step by its name, which is its file's name with no number: `first-rank`. */
export function stepOfTheVisit<Body = unknown>(name: string): Recorded<Body> {
  const found = stepsOfTheVisit().find((step) => step.scenario.replace(/^visit\/\d+-/, "") === name);
  if (found === undefined) throw new Error(`The visit has no step named ${name}.`);
  return found as Recorded<Body>;
}

/** The same whatever order the keys of an object were written in. */
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value !== null && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const fields = Object.keys(record)
      .sort()
      .map((name) => `${JSON.stringify(name)}:${canonical(record[name])}`);
    return `{${fields.join(",")}}`;
  }
  return JSON.stringify(value) ?? "null";
}

const keyOf = (method: string, route: string, body: unknown) =>
  `${method} ${route} ${body === undefined ? "" : canonical(body)}`;

export interface VisitApi {
  readonly client: Client;
  /** The route of each request that was no step of the visit. Never what was sent. */
  readonly unanswered: string[];
  /** The steps no request has asked for yet. */
  unused(): string[];
}

export function visitApi(): VisitApi {
  const steps = stepsOfTheVisit();
  // Two steps may be one request: the reasons of a search, asked for again when its link is
  // opened. The service answers both alike, so either answer will do for both.
  const byKey = new Map<string, Recorded[]>();
  for (const step of steps) {
    const key = keyOf(step.request.method, step.request.path, step.request.body);
    byKey.set(key, [...(byKey.get(key) ?? []), step]);
  }
  const used = new Set<string>();
  const unanswered: string[] = [];

  const fetch = (async (input: RequestInfo | URL, init: RequestInit = {}) => {
    await aMomentLater();
    const { pathname } = new URL(String(input));
    const method = init.method ?? "GET";
    const body = typeof init.body === "string" ? (JSON.parse(init.body) as unknown) : undefined;
    const [step, ...same] = byKey.get(keyOf(method, pathname, body)) ?? [];
    if (step !== undefined) {
      for (const one of [step, ...same]) used.add(one.scenario);
      return responseFrom(step);
    }
    if (method === "GET" && pathname === "/v1/areas/geometry") return responseFrom(readRecorded("geometry"));
    if (method === "GET" && pathname === "/v1/meta") return responseFrom(readRecorded("meta"));
    const area = /^\/v1\/areas\/([a-z0-9-]+)$/.exec(pathname);
    if (method === "GET" && area !== null) return responseFrom(readRecorded(`area/${area[1] ?? ""}`));
    unanswered.push(`${method} ${pathname.replace(/^(\/v1\/shares)\/.+$/, "$1/{share_id}")}`);
    throw new TypeError("This request is no step of the recorded visit.");
  }) as typeof globalThis.fetch;

  return {
    client: createClient({ baseUrl: BASE, fetch }),
    unanswered,
    unused: () => steps.map((step) => step.scenario).filter((scenario) => !used.has(scenario)),
  };
}
