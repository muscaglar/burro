/**
 * A vibe that is a rough guide: what it says of itself wherever it is shown.
 *
 * The founder decided on 2026-09-25 that Village feel is served though it did
 * not reach the bar they had set, and that it says it is less sure than the
 * other vibes. So wherever such a vibe is shown it says so, in sight and not
 * behind a press: one short label, and one sentence that says why.
 *
 * No vibe is written here, and no word. Which vibe is a rough guide is the
 * API's to say, in `sureness` of the vibe, and the label and the sentence are
 * route 11's, in `rough_guides`. A vibe that does not say is as sure as the
 * rest, and so is one the API gives no label for: nothing is said of it.
 */

import type { MetaData, RoughGuide, Tag } from "@/lib/api/schema";

/** What a page is given of route 11 to say it with. An answer recorded before the field holds none. */
export type Guides = Partial<Pick<MetaData, "rough_guides">>;

/** The label and the sentence of one rough guide, as the API serves them. */
export type Told = Pick<RoughGuide, "label" | "why">;

/** Whether the API says a vibe is a rough guide. */
export function isRough(tag: Partial<Pick<Tag, "sureness">>): boolean {
  return tag.sureness === "rough_guide";
}

/** What a vibe that is a rough guide says of itself, or `null` of a vibe that is as sure as the rest. */
export function roughOf(tag: Pick<Tag, "tag_id"> & Partial<Pick<Tag, "sureness">>, meta: Guides): Told | null {
  if (!isRough(tag)) return null;
  return meta.rough_guides?.find((one) => one.tag_id === tag.tag_id) ?? null;
}

/** The label and the sentence in one line, as a note says them: the label, a full stop, the sentence. */
export function saidOf(told: Told): string {
  return `${told.label}. ${told.why}`;
}
