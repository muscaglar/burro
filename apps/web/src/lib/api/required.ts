/**
 * Generated from contracts/openapi.json by `npm run gen:api`.
 * Never edited by hand: change the contract and generate again.
 */

/** What the contract requires in the `data` of each operation's answer. */
export const REQUIRED_IN_DATA = {
  compare: ["areas", "character", "facts", "rows"],
  create_share: ["coarsened", "places", "share_id", "spec"],
  explain_top: ["explanations", "facts", "spec_hash"],
  get_area: ["area", "cost", "facts", "features", "neighbours", "portrait", "similar", "stations", "tags"],
  get_census: ["area_id", "city", "date_line", "derivation_line", "heading", "licence_line", "notes", "output_areas", "source_line", "tables"],
  get_geometry: ["features", "type"],
  get_meta: ["attributions", "built_at", "catalogue_version", "census", "counts", "defaults", "engine_version", "families", "features", "gritty_variant", "holds", "limits", "preview", "reader", "recipes", "release_id", "synthetic", "tags"],
  get_share: ["areas_listed", "areas_ranked", "coarsened", "empty_spec", "filtered", "original_release_id", "places", "ranked", "scores", "spec", "spec_hash", "stale", "unranked"],
  interpret: ["applied", "assumptions", "clarify", "degraded", "interpreter", "model_pending", "model_refused", "not_in_release", "notice", "notice_text", "operations", "places", "rejected", "rests_on", "spec", "spec_hash", "status", "suggestions", "unmet", "unmet_at", "unread"],
  list_areas: ["areas", "bands"],
  rank: ["applied", "areas_listed", "areas_ranked", "empty_spec", "filtered", "places", "ranked", "rejected", "scores", "spec", "spec_hash", "unranked"],
  search_places: ["places"],
} as const;
