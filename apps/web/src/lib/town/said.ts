/**
 * What a town says of itself, part by part: the vibe each part is drawn from and where the
 * area sits on it, or that the part is left blank and why.
 *
 * The name of a vibe and the names of its ends are the service's, from route 11. The words
 * for a band are the ones every page uses. Nothing here says anything of a place that the
 * service did not: a town that is handed a band says that band, and no more.
 */

import { STRIP } from "@/content/search";
import { TOWN } from "@/content/town";
import type { Tag } from "@/lib/api/schema";
import { inWords, isRange, plainly, type Placed } from "@/lib/vibes";

import { bandsOf, markOf, type Mark } from "./bands";
import { stateOf, type State } from "./plan";
import { heldBy, vibesOf, type Release } from "./release";
import type { Part } from "./vibes";

/**
 * Why a part is not drawn. `unknown`: the area has no band for its vibe, or the release
 * does not hold the vibe. `unbuilt`: there is no building to draw it on. `crime`: its vibe
 * counts recorded crime, which is shown only where a person asks for it.
 */
export type Why = "unknown" | "unbuilt" | "crime";

/** One part of a town, in words. */
export interface Said {
  readonly part: Part;
  readonly state: State;
  /** Why it is not drawn. `null` of a part that is. */
  readonly why: Why | null;
  /** What the part is: its name, which heads what is said of it. */
  readonly name: string;
  /** What it is drawn from and where the area sits on it, or what is left blank and why. It ends in no full stop. */
  readonly says: string;
}

type Named = Pick<Tag, "tag_id" | "label" | "low_end" | "high_end">;

/** Where the area sits, as the words for a band read it. A spread the service left out is the band itself. */
function placedBy(mark: Mark, band: number): Placed {
  return { band, spread_low: mark.spread_low ?? band, spread_high: mark.spread_high ?? band };
}

/** A part that is drawn: its vibe, the band, and where that is in words a person would use. */
function drawn(tag: Named, mark: Mark, band: number): string {
  const placed = placedBy(mark, band);
  // A mixed area sits at no one point. Its town is drawn from its band, and says that it is.
  if (isRange(placed)) return TOWN.mixed(tag.label, inWords(placed), STRIP.band(band));
  const plain = plainly(tag, placed);
  return TOWN.drawn(tag.label, plain === null ? inWords(placed) : `${inWords(placed)}, ${plain}`);
}

/**
 * What is left blank of a part. A window and a roof are drawn on a building: where there
 * is none, what is blank of them is the whole of them, and not their light alone.
 */
export function blankOf(part: Part, built: boolean): string {
  return !built && (part === "lit" || part === "roofs") ? TOWN.blankUnbuilt[part] : TOWN.blank[part];
}

/**
 * What each part of a town says, in the order the parts are said in. `marks` is what the
 * service sent of the area, and `release` what route 11 says of the vibes.
 */
export function saidOf(marks: readonly Mark[], release: Release): readonly Said[] {
  const held = heldBy(marks, release);
  const bands = bandsOf(held);
  return vibesOf(release).map(({ part, tag, crime }) => {
    const mark = markOf(held, part);
    const band = bands[part];
    const state = stateOf(bands, part);
    const name = TOWN.parts[part];
    const blank = blankOf(part, bands.height !== null);
    // A vibe the release does not hold has no name to be said by.
    if (tag === undefined) return { part, state: "blank", why: "unknown", name, says: TOWN.because(blank, TOWN.notHeld) };
    // Whatever band it has, a vibe that counts recorded crime is not drawn, and its band is not said.
    if (crime) return { part, state: "blank", why: "crime", name, says: TOWN.because(blank, TOWN.countsCrime(tag.label)) };
    if (band === null || mark === undefined) {
      return { part, state, why: "unknown", name, says: TOWN.because(blank, TOWN.notKnown(tag.label)) };
    }
    if (state === "unbuilt") return { part, state, why: "unbuilt", name, says: TOWN.because(blank, TOWN.unbuilt(tag.label)) };
    return { part, state, why: null, name, says: drawn(tag, mark, band) };
  });
}

/** The parts that are not drawn, as a list names them. Empty where the whole town is drawn. */
export function notDrawn(said: readonly Said[]): readonly string[] {
  return said.filter(({ state }) => state !== "drawn").map(({ part }) => TOWN.listed[part]);
}

/**
 * What stands under the line, in sight, where any part is not drawn: which parts, and in
 * a sentence each why a part may be blank. `null` where the whole town is drawn.
 */
export function blankSaid(said: readonly Said[]): string | null {
  const parts = notDrawn(said);
  if (parts.length === 0) return null;
  const whys = new Set(said.map(({ why }) => why));
  const ORDER = ["unknown", "crime", "unbuilt"] as const;
  return [TOWN.leftBlank(parts), ...ORDER.filter((why) => whys.has(why)).map((why) => TOWN.whyBlank[why])].join(" ");
}
