/**
 * Generated from contracts/openapi.json by `npm run gen:api`.
 * Never edited by hand: change the contract and generate again.
 */

/** What the contract requires in the `data` of each operation's answer. */
export const REQUIRED_IN_DATA = {
  compare: ["areas", "character", "facts", "rows"],
  create_share: ["coarsened", "places", "share_id", "spec"],
  delete_me: ["email", "signed_in"],
  end_sessions: ["sessions", "signed_in"],
  explain_top: ["explanations", "facts", "spec_hash"],
  export_me: ["adult_at", "email", "events", "exported_at", "links", "made_at", "preferences", "recent", "searches", "sessions"],
  forget_recent: ["kept", "most", "searches"],
  forget_search: ["most", "searches"],
  get_area: ["area", "cost", "facts", "features", "neighbours", "portrait", "similar", "stations", "tags"],
  get_census: ["area_id", "city", "date_line", "derivation_line", "heading", "licence_line", "notes", "output_areas", "source_line", "tables"],
  get_geometry: ["features", "type"],
  get_income: ["area_id", "definition", "estimate", "heading", "kind", "licence_line", "limits", "limits_label", "lower", "modelled", "none_given", "notes", "open_source", "source_line", "source_url", "upper", "year_line"],
  get_me: ["email", "fresh", "made_at", "preferences"],
  get_meta: ["attributions", "built_at", "catalogue_version", "census", "counts", "defaults", "engine_version", "families", "features", "gritty_variant", "holds", "income", "limits", "preview", "reader", "recipes", "release_id", "synthetic", "tags"],
  get_session: ["email", "signed_in"],
  get_share: ["areas_listed", "areas_ranked", "coarsened", "empty_spec", "filtered", "original_release_id", "places", "ranked", "scores", "spec", "spec_hash", "stale", "unranked"],
  interpret: ["applied", "assumptions", "clarify", "degraded", "interpreter", "model_pending", "model_refused", "not_in_release", "notice", "notice_text", "operations", "places", "rejected", "rests_on", "spec", "spec_hash", "status", "suggestions", "unmet", "unmet_at", "unread"],
  keep_recent: ["kept", "most", "searches"],
  keep_search: ["kept_at", "name", "release_id", "search_id", "spec", "state"],
  list_areas: ["areas", "bands"],
  list_recent: ["kept", "most", "searches"],
  list_searches: ["most", "searches"],
  list_sessions: ["sessions", "signed_in"],
  rank: ["applied", "areas_listed", "areas_ranked", "empty_spec", "filtered", "places", "ranked", "rejected", "scores", "spec", "spec_hash", "unranked"],
  search_places: ["areas", "places"],
  set_preferences: ["keep_recent"],
  sign_in: ["email", "new_account"],
  sign_out: ["email", "signed_in"],
  whose_link: ["email", "new_account", "same_browser"],
} as const;
