/**
 * What puts right a search that names something the data no longer has.
 *
 * The API refuses such a spec with the path of each thing that is wrong, and
 * accepts it when it comes with the edit that takes that thing out. The
 * website still builds no spec: it reads the path, finds what sits there in
 * the spec the API last returned, and offers the edit that removes it.
 */

import type { Failure } from "@/lib/api/failure";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";

import { edits, isEmpty, type ChipKey } from "./edits";

export interface Repair {
  readonly what: "place" | "area" | "setting";
  /** The part to take out, as the chips name it. It holds an id, never anything a person typed. */
  readonly key: ChipKey;
  readonly operations: Operations;
}

const CODES: readonly string[] = ["unknown_place", "unknown_area", "invalid_spec"];
const AT = /^spec\.(commutes|areas|weights|tags)\[(\d+)\]/;

/**
 * The repairs a failure allows. None when the failure is of another kind, or
 * when edits are waiting: a position in a path is a position in the spec as
 * those edits leave it, which the website does not hold.
 */
export function repairsFor(
  failure: Failure | null,
  spec: PreferenceSpec,
  pending: Operations,
): readonly Repair[] {
  if (failure === null || failure.kind !== "api" || !CODES.includes(failure.code)) return [];
  if (!isEmpty(pending)) return [];
  const repairs: Repair[] = [];
  for (const { path } of failure.fields) {
    const found = AT.exec(path);
    if (!found) continue;
    const at = Number(found[2]);
    const repair = ((): Repair | null => {
      switch (found[1]) {
        case "commutes": {
          const id = spec.commutes[at]?.place_id;
          return id === undefined
            ? null
            : { what: "place", key: `place:${id}`, operations: edits.placeRemove(id) };
        }
        case "areas": {
          const id = spec.areas[at]?.area_id;
          return id === undefined
            ? null
            : { what: "area", key: `area:${id}`, operations: edits.areaClear(id) };
        }
        case "weights": {
          const id = spec.weights[at]?.feature_id;
          return id === undefined
            ? null
            : { what: "setting", key: `feature:${id}`, operations: edits.featureOff(id) };
        }
        case "tags": {
          const id = spec.tags[at]?.tag_id;
          return id === undefined
            ? null
            : { what: "setting", key: `tag:${id}`, operations: edits.tagOff(id) };
        }
        default:
          return null;
      }
    })();
    if (repair !== null && !repairs.some((one) => one.key === repair.key)) repairs.push(repair);
  }
  return repairs;
}

/** True when the failure says the search names something the data no longer has. */
export function isStale(failure: Failure | null): boolean {
  return (
    failure !== null &&
    failure.kind === "api" &&
    CODES.includes(failure.code) &&
    failure.fields.some(({ path }) => path.startsWith("spec."))
  );
}
