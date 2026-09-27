/**
 * What the town of an area in the bar is drawn from. It is plain code with no state, so
 * that a page drawn on the server and the bar, which runs in the browser, read it one way.
 *
 * The bar stands at the foot of every page that fills it, and is handed nothing by the
 * page it stands on. So whatever draws the button that fills it hands over what it holds
 * already of the towns: the list of results where every area sits, and the page of an
 * area where that area sits. Nothing is asked of the service for a town.
 */

import { crimeParts } from "@/content/crime";
import type { VibeBands } from "@/lib/api/schema";
import { marksOf, type Mark } from "@/lib/town/bands";
import { vibesOf, type Release } from "@/lib/town/release";

/** What is handed over of the towns: what a town reads of the release, and where areas sit. */
export interface Handed {
  readonly release: Release;
  /** Where every area sits on every vibe, where the page holds it. */
  readonly bands?: readonly VibeBands[] | undefined;
  /** Where single areas sit, by the id of the area. It comes before what `bands` says of the area. */
  readonly marks: Readonly<Record<string, readonly Mark[]>>;
}

/** What the button of one area hands over: where its own area sits, and what a town reads of the release. */
export interface TownOf {
  readonly release: Release;
  readonly marks: readonly Mark[];
}

/**
 * What a town reads of a release, and no more: the vibes it is drawn from, and the
 * measures of recorded crime in their recipes. A release holds a hundred measures, and a
 * page that hands all of them to the browser hands it what no town reads.
 *
 * What the service says of a vibe it holds to be less sure than the rest is no part of it:
 * a town says of its vibes what the release it is handed says of them, and no town of a
 * result, of the bar or of a comparison says that.
 */
export function ofATown(release: Release): Release {
  const tags = vibesOf(release).flatMap(({ tag }) => (tag === undefined ? [] : [tag]));
  return { tags, features: tags.flatMap((tag) => crimeParts(tag, release.features)) };
}

/**
 * Where one area sits, of all that was handed over. `null` of an area nothing was handed
 * of: no town is drawn of it, since a town that is left blank says its parts are not known.
 */
export function marksIn(handed: Handed | null, areaId: string): readonly Mark[] | null {
  if (handed === null) return null;
  const own = Object.hasOwn(handed.marks, areaId) ? handed.marks[areaId] : undefined;
  if (own !== undefined) return own;
  const held = marksOf(handed.bands ?? [], areaId);
  return held.length === 0 ? null : held;
}
