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
 * than no page. A read that a busy service was late with is no failure until
 * it has been asked for a few times, each waited for longer than the last.
 */

import { apiBaseUrl } from "./config";
import { failed, type Answer, type Failure } from "./failure";
import { ROUTES, type DataOf, type OperationId } from "./operations";
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

/**
 * How many times a read is asked for before it stops the build. A build of a thousand
 * pages asks one service from every worker at once, and an answer that takes a tenth of
 * a second alone then stands behind a hundred others.
 */
const TRIES = 4;

/** How long the service is left alone before it is asked again. It doubles each time. */
const PAUSE_MS = 1_000;

/** What stands in front of a service says these of one that has fallen behind. */
const BUSY = new Set([429, 503, 504]);

/**
 * True of a read that may go well if it is asked for again: one that was not waited for
 * long enough, one that brought no answer, and one the service was too busy to take.
 * What the API refused is an answer, and asking again would bring the same one.
 */
function isWorthAnotherTry(failure: Failure): boolean {
  if (failure.kind === "timeout" || failure.kind === "network") return true;
  return failure.kind === "unreadable" && failure.status !== null && BUSY.has(failure.status);
}

/** An answer, and how many times it was asked for. */
interface Asked<Op extends OperationId> {
  readonly answer: Answer<DataOf<Op>>;
  readonly tries: number;
}

async function read<Op extends OperationId>(
  operation: Op,
  scenario: string,
  parameter?: string,
): Promise<Asked<Op>> {
  const baseUrl = apiBaseUrl();
  if (baseUrl === null) return { answer: fromRecorded<Op>(findRecorded(scenario)), tries: 1 };
  for (let tries = 1; ; tries += 1) {
    const answer = await send(
      operation,
      { baseUrl, init: { next: { revalidate: REVALIDATE_SECONDS } } as RequestInit },
      // Only a build waits longer. The wait of a person's browser is the route's own.
      { parameter, timeoutMs: ROUTES[operation].timeoutMs * 2 ** (tries - 1) },
    );
    if (answer.ok || tries === TRIES || !isWorthAnotherTry(answer.failure)) return { answer, tries };
    await new Promise((resolve) => setTimeout(resolve, PAUSE_MS * 2 ** (tries - 1)));
  }
}

function orStop<Op extends OperationId>(operation: Op, { answer, tries }: Asked<Op>): Loaded<DataOf<Op>> {
  if (answer.ok) return { meta: answer.meta, data: answer.data };
  const { failure } = answer;
  const why = failure.kind === "api" ? failure.code : failure.kind;
  throw new BuildReadError(operation, tries > 1 ? `${why}, after ${tries} tries` : why);
}

/** Route 11. */
export async function loadMeta(): Promise<Loaded<MetaData>> {
  return orStop("get_meta", await read("get_meta", "meta"));
}

/** Route 4. */
export async function loadAreas(): Promise<Loaded<AreasData>> {
  return orStop("list_areas", await read("list_areas", "areas"));
}

/**
 * The outlines as they were last read, by the address they were read from, and when.
 *
 * The answer of route 5 is larger than the framework will keep, so every page that draws
 * the areas asked for it again: a thousand times in one build of a thousand areas. It is
 * kept here for as long as a built page is kept, and no longer, so a page that is built
 * again in an hour is built on what the service holds then. An answer that failed is never
 * kept.
 */
const outlines = new Map<string, { readonly at: number; readonly read: Promise<Asked<"get_geometry">> }>();

/** Lets go of the outlines that were read. For a test, which answers each call its own way. */
export function forgetTheOutlines(): void {
  outlines.clear();
}

/** Route 5. */
export async function loadGeometry(): Promise<Loaded<GeometryData>> {
  const from = apiBaseUrl() ?? "";
  const held = outlines.get(from);
  if (held !== undefined && Date.now() - held.at < REVALIDATE_SECONDS * 1000) {
    return orStop("get_geometry", await held.read);
  }
  const asked = read("get_geometry", "geometry");
  outlines.set(from, { at: Date.now(), read: asked });
  const came = await asked;
  if (!came.answer.ok && outlines.get(from)?.read === asked) outlines.delete(from);
  return orStop("get_geometry", came);
}

/** Route 6, by slug. `null` when the release has no such area, which is a 404 and not a fault. */
export async function loadArea(slug: string): Promise<Loaded<AreaData> | null> {
  if (!SLUG.test(slug)) return null;
  // With no API to ask, an area with no recording is an area the release lacks.
  if (apiBaseUrl() === null && findRecorded(`area/${slug}`) === null) return null;
  const asked = await read("get_area", `area/${slug}`, slug);
  const { answer } = asked;
  if (!answer.ok && answer.failure.kind === "api" && answer.failure.code === "area_not_found") {
    return null;
  }
  return orStop("get_area", asked);
}
