/**
 * Opens a search that was kept: its spec is loaded into the search that is open in the
 * tab, ranked now, as the spec of a shared link is.
 *
 * What was kept is a spec that the service returned, and the ranking is asked of the API
 * with it, as any ranking is. The search that was open is left alone until the ranking has
 * come. If it does not come, the page that asked says what went wrong, and the search
 * before is as it was. When it comes, it takes the place of the search whole: no
 * question, no name and no edit of the search before is carried into it.
 *
 * It goes by what the store and the flow of a search hand to any part of the website: it
 * begins the search again, and tells the store of a ranking, of its reasons and of the
 * profiles of its first areas, each as the answer that brought it.
 */

import type { Client } from "@/lib/api/client";
import type { Failure } from "@/lib/api/failure";
import type { PreferenceSpec, RankData } from "@/lib/api/schema";
import { NO_EDITS } from "@/lib/search/edits";
import { EXPLAINED, LIST_LENGTH } from "@/lib/search/flow";
import { reasonsAreIn } from "@/lib/search/state";
import type { Held } from "@/lib/search/store";

/** True while the search on screen is still the one that was opened here. */
const isStillOpen = (held: Held, ranked: RankData) => held.store.getState().rankedHash === ranked.spec_hash;

/** Where the release has moved on, the form is read again, so that the search is drawn with the names of the release that ranked it. */
async function catchUp(held: Held, client: Client, release: string): Promise<void> {
  if (held.store.getState().meta.release_id === release) return;
  const [meta, areas, geometry] = await Promise.all([client.getMeta(), client.listAreas(), client.getGeometry()]);
  if (!meta.ok || !areas.ok) return;
  held.store.dispatch({ type: "release_changed", meta: meta.data, areas: areas.data.areas });
  if (geometry.ok) held.store.dispatch({ type: "geometry_loaded", geometry: geometry.data });
}

/** What the cards of the ranking hold: its reasons, and the profiles of its first areas. */
async function fill(held: Held, client: Client, ranked: RankData): Promise<void> {
  const first = ranked.ranked.slice(0, EXPLAINED).map((area) => area.area_id);
  if (first.length === 0) return;
  const { areas, details } = held.store.getState();
  const profiles = first
    .filter((areaId) => !(areaId in details))
    .flatMap((areaId) => areas.filter((area) => area.area_id === areaId))
    .map(async (area) => {
      const answer = await client.getArea(area.slug);
      // A profile is of the release and not of the search, so a late one is still right.
      if (answer.ok) held.store.dispatch({ type: "detail_answered", data: answer.data, meta: answer.meta });
      else if (answer.failure.kind !== "aborted") {
        held.store.dispatch({ type: "detail_failed", areaId: area.area_id, failure: answer.failure });
      }
    });
  const reasons = (async () => {
    const answer = await client.explainTop({ spec: ranked.spec, limit: EXPLAINED });
    // The search may have moved on meanwhile. The store holds reasons against the ranking
    // they are for, and these are told to it only while that ranking is on screen.
    if (!isStillOpen(held, ranked) || reasonsAreIn(held.store.getState())) return;
    if (answer.ok) held.store.dispatch({ type: "explain_answered", data: answer.data, meta: answer.meta });
    else if (answer.failure.kind !== "aborted") {
      held.store.dispatch({ type: "explain_failed", hash: ranked.spec_hash, failure: answer.failure });
    }
  })();
  await Promise.all([...profiles, reasons]);
}

export interface Opened {
  /** Why the search could not be opened. `null` where it is open. */
  readonly failure: Failure | null;
  /** Done once the cards of the ranking hold what they hold. The search is open before it is. */
  readonly filled: Promise<void>;
}

const NOTHING_TO_FILL = Promise.resolve();

/**
 * Opens a spec that was kept in the search that is handed over. It answers once the
 * ranking is in, or with why it is not. What the cards of the ranking hold comes after.
 */
export async function openKept(held: Held, client: Client, spec: PreferenceSpec): Promise<Opened> {
  const answer = await client.rank({ spec, limit: LIST_LENGTH });
  // The page that asked says what went wrong. The search that was open is left as it was.
  if (!answer.ok) return { failure: answer.failure, filled: NOTHING_TO_FILL };
  await catchUp(held, client, answer.meta.release_id);
  // Whatever was on its way for the search before is stopped, and nothing of that search is kept.
  held.flow.startAgain();
  held.store.dispatch({ type: "rank_answered", data: answer.data, sent: NO_EDITS, meta: answer.meta });
  return { failure: null, filled: fill(held, client, answer.data) };
}
