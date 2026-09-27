/**
 * What the town at the head of each area of a comparison is drawn from. It is plain code
 * with no state, so that the page which is built on the server and the comparison which
 * is drawn in the browser read it one way.
 *
 * A town is drawn from where an area sits on the vibes of the release, which is of the
 * release and of no search. The page hands it over as it is built, so that every area has
 * its town before the comparison is answered, and with scripts off. Once the comparison is
 * answered it says where each area sits as well, in the table under the towns: a town then
 * follows the table, so that the two never say two things of one area.
 */

import type { CrimeVibe } from "@/content/crime";
import type { CharacterRow, Tag, VibeBands } from "@/lib/api/schema";
import { marksOf, type Mark } from "@/lib/town/bands";
import type { Release } from "@/lib/town/release";

/** Where each area sits on each vibe of the release, by the id of the area. */
export type MarksOf = Readonly<Record<string, readonly Mark[]>>;

/** What the towns of a comparison are drawn from: what the release says of its vibes, and where each area sits on them. */
export interface Towns {
  readonly meta: Release;
  readonly marks: MarksOf;
}

/**
 * What a town reads of the release, made of what a comparison is handed of it already:
 * the vibes, and the vibes whose recipe holds recorded crime, each with the measures of it
 * that are of crime.
 *
 * Of the measures of a release a town reads one thing: which of those in the recipe of a
 * vibe are of recorded crime, so that it draws nothing of such a vibe. The measures of
 * crime that the recipes hold are all of that, and are handed over in place of every
 * measure of the release, which a page of a comparison has no other use for.
 */
export function releaseOf(tags: readonly Tag[], crime: readonly CrimeVibe[]): Release {
  return { tags, features: crime.flatMap((vibe) => vibe.parts) };
}

/**
 * Where the areas that were chosen sit on each vibe, of the bands of every area. It holds
 * the areas of the comparison and no other: a release may hold a thousand.
 */
export function marksOfTheChosen(
  bands: readonly VibeBands[],
  chosen: readonly { readonly area_id: string }[],
): MarksOf {
  return Object.fromEntries(chosen.map(({ area_id }) => [area_id, marksOf(bands, area_id)]));
}

/**
 * Where one area sits on each vibe: as the comparison says it of every vibe it compares,
 * and as the page was built for a vibe it says nothing of.
 */
export function marksFor(
  areaId: string,
  built: MarksOf,
  character: readonly CharacterRow[] | undefined,
): readonly Mark[] {
  const before = built[areaId] ?? [];
  if (character === undefined) return before;
  const said = marksOf(character, areaId);
  return [...said, ...before.filter((one) => !said.some((other) => other.tag_id === one.tag_id))];
}
