/**
 * What the page of vibes is for, in the sentence that stands under its heading. It is plain
 * code with no state, so that the page and what a search engine is told say the same.
 */

import { crimeParts } from "@/content/crime";
import { isRough } from "@/content/rough";
import { VIBES } from "@/content/vibes";
import type { MetaData } from "@/lib/api/schema";

import { EXAMPLES, type Examples } from "./look";

/**
 * What a vibe is, with two vibes named as examples. They are the first two of the data that
 * may be named in passing: a vibe that counts recorded crime says that it does wherever it
 * is shown, and one the service says is less sure is held back from what is said in short,
 * so neither is an example. With fewer than two to name, none is named.
 */
export function leadOf(meta: Pick<MetaData, "tags" | "features">, examples: Examples = EXAMPLES): string {
  if (examples === "written") return VIBES.leadAsWritten;
  const plain = meta.tags.filter((tag) => !isRough(tag) && crimeParts(tag, meta.features).length === 0);
  return VIBES.lead(plain.slice(0, 2).map((tag) => tag.label));
}
