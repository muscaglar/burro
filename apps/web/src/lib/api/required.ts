/**
 * Generated from contracts/openapi.json by `npm run gen:api`.
 * Never edited by hand: change the contract and generate again.
 */

/** What the contract requires in the `data` of each operation's answer. */
export const REQUIRED_IN_DATA = {
  compare: ["areas", "facts", "rows"],
  create_share: ["coarsened", "share_id", "spec"],
  explain_top: ["explanations", "facts"],
  get_area: ["area", "cost", "facts", "features", "neighbours", "stations", "tags"],
  get_geometry: ["features", "type"],
  get_meta: ["attributions", "built_at", "catalogue_version", "counts", "defaults", "engine_version", "features", "limits", "release_id", "synthetic", "tags"],
  get_share: ["coarsened", "empty_spec", "filtered", "original_release_id", "ranked", "scores", "spec", "spec_hash", "stale", "unranked"],
  interpret: ["applied", "assumptions", "clarify", "degraded", "interpreter", "notice", "notice_text", "operations", "rejected", "rests_on", "spec", "spec_hash", "status", "unmet"],
  list_areas: ["areas"],
  rank: ["applied", "empty_spec", "filtered", "ranked", "rejected", "scores", "spec", "spec_hash", "unranked"],
  search_places: ["places"],
} as const;
