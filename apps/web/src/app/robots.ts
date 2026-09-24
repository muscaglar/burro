import type { MetadataRoute } from "next";

import { loadMeta } from "@/lib/api/server";
import { mayBeIndexed, SITEMAP_PATH, wholeAddress } from "@/lib/indexing";

// Kept for an hour at most, as every page built from the API is.
export const revalidate = 3600;

/**
 * What the website asks of a crawler. It is let in either way, and the
 * sitemap is named only when there is something to find.
 *
 * While the release is made up, or the website does not know its own
 * address, every page asks to be left out, in its markup and in a header. A
 * crawler must be let in to read that: kept out here, it would never fetch
 * the page, and could still list its address from a link found elsewhere.
 * The same holds for a comparison and an opened share, which are one
 * person's and say so themselves.
 */
export default async function robots(): Promise<MetadataRoute.Robots> {
  const { meta } = await loadMeta();
  const rules = { userAgent: "*", allow: "/" };
  const sitemap = mayBeIndexed(meta) ? wholeAddress(SITEMAP_PATH) : null;
  return sitemap === null ? { rules } : { rules, sitemap };
}
