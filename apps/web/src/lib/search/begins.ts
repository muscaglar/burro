/**
 * What the settings are told a search starts from, while the second way in gathers.
 *
 * The settings tell a search that has begun from one that has not by the spec they are
 * handed: before a search it is a default, as the API served it. While the second way in
 * gathers, the spec is one the API returned, so that a place is named and every control is
 * drawn from what the API holds, and no search has been made of it. What a search will
 * start from is then what was gathered. So the settings are handed that as the default of
 * its tenure, and draw themselves as they do before a search: a couple of groups open, to
 * show that a group folds, and nothing said of a ranking that nobody has asked for.
 *
 * It is plain code with no state. Nothing else of the form is changed, and nothing is
 * handed to any other part: the chips, the list and the map are drawn once a search is made.
 */

import type { Handed } from "@/lib/api/handed";
import type { PreferenceSpec } from "@/lib/api/schema";

export function startsFrom(meta: Handed, spec: PreferenceSpec, gathering: boolean): Handed {
  if (!gathering || meta.defaults[spec.tenure] === spec) return meta;
  return { ...meta, defaults: { ...meta.defaults, [spec.tenure]: spec } };
}
