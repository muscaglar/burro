/**
 * What a page that runs in the browser is handed of what the service says of a release.
 *
 * Whatever the server hands such a page is written into the page as it is sent, whether or
 * not anything draws it, and whoever reads what they were sent reads it. So a page is
 * handed what it may draw, and no more.
 *
 * The service says which vibes it calls a rough guide, each with a label and a sentence
 * that says why. The founder asked that neither is passed on, and no page draws either:
 * so no page is handed them. Which vibe is less sure is still said of each vibe, in a
 * code, and chooses what a page that is drawn on the server says in short.
 */

import type { MetaData } from "./schema";

/** What the service says of a release, less what no page is handed. */
export type Handed = Omit<MetaData, "rough_guides">;

/** What a page is handed of an answer of route 11. The rest of it is the service's, as it came. */
export function handed(meta: MetaData): Handed {
  const { rough_guides: left, ...rest } = meta;
  void left;
  return rest;
}
