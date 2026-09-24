/**
 * The API, as a build reads it: routes 4, 5, 6 and 11, which are functions
 * of the release alone. Nothing a person typed is ever sent from here.
 *
 * With an address set for the API it is called, and a page built from the
 * answer is kept for an hour at most, which is how long the API says its
 * answer may be kept. With none set the recorded answers are read, which is
 * how a build runs where no API can.
 *
 * A failure here stops the build. A page with nothing behind it is worse
 * than no page.
 */

import { apiBaseUrl } from "./config";
import { failed, type Answer } from "./failure";
import type { DataOf, OperationId } from "./operations";
import { findRecorded, type Recorded } from "./recorded";
import type { AreaData, AreasData, GeometryData, Meta, MetaData } from "./schema";
import { send } from "./send";

/** How long a built page may be kept, in seconds: the `max-age` the API sends. */
export const REVALIDATE_SECONDS = 3_600;

/** An area's slug, as the contract writes one. Anything else is no area. */
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export interface Loaded<Data> {
  readonly meta: Meta;
  readonly data: Data;
}

export class BuildReadError extends Error {
  constructor(operation: OperationId, why: string) {
    // The operation and a code. Never an address, and never what was sent.
    super(`The API could not be read for ${operation}: ${why}.`);
    this.name = "BuildReadError";
  }
}

function fromRecorded<Op extends OperationId>(recorded: Recorded | null): Answer<DataOf<Op>> {
  if (recorded === null) return failed("unreadable");
  const body = recorded.body as Partial<Loaded<DataOf<Op>>> | null;
  if (recorded.status !== 200 || !body?.meta || body.data === undefined) {
    return failed("unreadable", { status: recorded.status });
  }
  return {
    ok: true,
    status: recorded.status,
    meta: body.meta,
    data: body.data,
    synthetic: body.meta.synthetic,
    requestId: recorded.headers["x-request-id"] ?? null,
  };
}

async function read<Op extends OperationId>(
  operation: Op,
  scenario: string,
  parameter?: string,
): Promise<Answer<DataOf<Op>>> {
  const baseUrl = apiBaseUrl();
  if (baseUrl === null) return fromRecorded<Op>(findRecorded(scenario));
  return send(
    operation,
    { baseUrl, init: { next: { revalidate: REVALIDATE_SECONDS } } as RequestInit },
    { parameter },
  );
}

function orStop<Op extends OperationId>(
  operation: Op,
  answer: Answer<DataOf<Op>>,
): Loaded<DataOf<Op>> {
  if (answer.ok) return { meta: answer.meta, data: answer.data };
  const { failure: why } = answer;
  throw new BuildReadError(operation, why.kind === "api" ? why.code : why.kind);
}

/** Route 11. */
export async function loadMeta(): Promise<Loaded<MetaData>> {
  return orStop("get_meta", await read("get_meta", "meta"));
}

/** Route 4. */
export async function loadAreas(): Promise<Loaded<AreasData>> {
  return orStop("list_areas", await read("list_areas", "areas"));
}

/** Route 5. */
export async function loadGeometry(): Promise<Loaded<GeometryData>> {
  return orStop("get_geometry", await read("get_geometry", "geometry"));
}

/** Route 6, by slug. `null` when the release has no such area, which is a 404 and not a fault. */
export async function loadArea(slug: string): Promise<Loaded<AreaData> | null> {
  if (!SLUG.test(slug)) return null;
  // With no API to ask, an area with no recording is an area the release lacks.
  if (apiBaseUrl() === null && findRecorded(`area/${slug}`) === null) return null;
  const answer = await read("get_area", `area/${slug}`, slug);
  if (!answer.ok && answer.failure.kind === "api" && answer.failure.code === "area_not_found") {
    return null;
  }
  return orStop("get_area", answer);
}
