/**
 * What a release lets a town be drawn from, read off route 11.
 *
 * A part is drawn from its vibe where the release names the vibe, and only where the vibe
 * may be shown unasked. A vibe whose recipe holds recorded crime may not: recorded crime is
 * shown only where a person asked for it, and nobody asked for a town. Its part is left
 * blank, and says why. Which vibe that is, is the release's to say, and is written nowhere.
 */

import { crimeParts } from "@/content/crime";
import type { MetaData, Tag } from "@/lib/api/schema";

import type { Mark } from "./bands";
import { DRAWN_FROM, PARTS, type Part } from "./vibes";

/** What a town reads of route 11: the vibes, and the measures their recipes are made of. */
export type Release = Pick<MetaData, "tags" | "features">;

/** The vibe a part is drawn from, as a release holds it. */
export interface Vibe {
  readonly part: Part;
  /** The vibe, with its name and the names of its ends. `undefined` where the release does not hold it. */
  readonly tag: Tag | undefined;
  /** True where its recipe holds recorded crime, so that a town draws nothing of it. */
  readonly crime: boolean;
}

/** The vibe of each part, in the order the parts are said in. */
export function vibesOf(release: Release): readonly Vibe[] {
  return PARTS.map((part) => {
    const tag = release.tags.find((one) => one.tag_id === DRAWN_FROM[part]);
    if (tag === undefined) return { part, tag, crime: false };
    return { part, tag, crime: crimeParts(tag, release.features).length > 0 };
  });
}

/** True where a town may draw the part from its vibe: the release names the vibe, and it holds no recorded crime. */
export function mayBeDrawn(vibe: Vibe): boolean {
  return vibe.tag !== undefined && !vibe.crime;
}

/**
 * What the service sent of the vibes a town may draw. What it sent of any other is not
 * read: of a vibe the release does not name nothing could be said, and of one that holds
 * recorded crime nothing may be shown.
 */
export function heldBy(marks: readonly Mark[], release: Release): readonly Mark[] {
  const drawn = vibesOf(release).filter(mayBeDrawn);
  return marks.filter((mark) => drawn.some(({ tag }) => tag?.tag_id === mark.tag_id));
}
