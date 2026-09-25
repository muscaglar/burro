/**
 * The API, as the browser calls it: one function for each route, named for
 * its operation id in the contract.
 *
 * Each takes what the route takes and a signal to stop it with. None throws:
 * each answers with `meta` and `data`, or with a failure that says why.
 * Nothing here logs, and nothing is kept: the caller holds the answer.
 */

import { apiBaseUrl } from "./config";
import type { Answer } from "./failure";
import type { BodyOf, DataOf, OperationId } from "./operations";
import { noteSaid } from "./said";
import { send, type SendSettings } from "./send";
import { noteSynthetic } from "./synthetic";

export type { Answer, ApiFailure, ClientFailure, ClientFailureKind, Failure } from "./failure";
export { hasCode, isApiFailure } from "./failure";

type Post<Op extends OperationId> = (
  body: BodyOf<Op>,
  signal?: AbortSignal,
) => Promise<Answer<DataOf<Op>>>;
type Get<Op extends OperationId> = (signal?: AbortSignal) => Promise<Answer<DataOf<Op>>>;
type GetOne<Op extends OperationId> = (
  id: string,
  signal?: AbortSignal,
) => Promise<Answer<DataOf<Op>>>;

export interface Client {
  /** Route 1. Reads a sentence into edits, and applies them to the spec sent with it. */
  readonly interpret: Post<"interpret">;
  /** Route 2. Ranks a spec, after applying any edits sent with it. */
  readonly rank: Post<"rank">;
  /** Route 3. Reasons and a trade-off for the first areas of a spec's ranking. */
  readonly explainTop: Post<"explain_top">;
  /** Route 7. Two to four areas, side by side. */
  readonly compare: Post<"compare">;
  /** Route 8. Places that match what is being typed. */
  readonly searchPlaces: Post<"search_places">;
  /** Route 9. Stores a spec and answers with the id of the share. */
  readonly createShare: Post<"create_share">;
  /** Route 10. A share, ranked now. */
  readonly getShare: GetOne<"get_share">;
  /** Route 4. Every area of the release. */
  readonly listAreas: Get<"list_areas">;
  /** Route 5. The boundary of every area. */
  readonly getGeometry: Get<"get_geometry">;
  /** Route 6. One area, by its id or its slug. */
  readonly getArea: GetOne<"get_area">;
  /** Route 11. What a form needs, and every source and method. */
  readonly getMeta: Get<"get_meta">;
  /** Route 13. The census figures of one area, by its id or its slug. Only an area's page asks. */
  readonly getCensus: GetOne<"get_census">;
  /** Route 14. The household income of one area, as its publisher estimates it. Only an area's page asks. */
  readonly getIncome: GetOne<"get_income">;
}

export interface ClientSettings extends Omit<SendSettings, "baseUrl"> {
  /** The address of the API. Left out, it is read from the one environment variable. */
  readonly baseUrl?: string | null;
}

export function createClient(settings: ClientSettings = {}): Client {
  const resolved = (): SendSettings => ({
    ...settings,
    baseUrl: settings.baseUrl === undefined ? apiBaseUrl() : settings.baseUrl,
  });
  const post =
    <Op extends OperationId>(operation: Op): Post<Op> =>
    (body, signal) =>
      send(operation, resolved(), { body, signal });
  const get =
    <Op extends OperationId>(operation: Op): Get<Op> =>
    (signal) =>
      send(operation, resolved(), { signal });
  const getOne =
    <Op extends OperationId>(operation: Op): GetOne<Op> =>
    (id, signal) =>
      send(operation, resolved(), { parameter: id, signal });

  return {
    interpret: post("interpret"),
    rank: post("rank"),
    explainTop: post("explain_top"),
    compare: post("compare"),
    searchPlaces: post("search_places"),
    createShare: post("create_share"),
    getShare: getOne("get_share"),
    listAreas: get("list_areas"),
    getGeometry: get("get_geometry"),
    getArea: getOne("get_area"),
    getMeta: get("get_meta"),
    getCensus: getOne("get_census"),
    getIncome: getOne("get_income"),
  };
}

/** The client the website uses. Every answer it reads is heard by the banner. */
export const api: Client = createClient({ onSynthetic: noteSynthetic, onSaid: noteSaid });
