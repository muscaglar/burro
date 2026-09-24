import type { MetadataRoute } from "next";

import { loadAreas, loadMeta } from "@/lib/api/server";
import { mayBeIndexed, wholeAddress } from "@/lib/indexing";
import { paths } from "@/lib/paths";

// Kept for an hour at most, as every page built from the API is.
export const revalidate = 3600;

/**
 * Every page a search engine may index: the search, the three pages about
 * the website, and one page for each area of the release, from route 4.
 *
 * While the release is made up, or the website does not know its own
 * address, it lists nothing: a made-up place must not be found.
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [{ meta }, areas] = await Promise.all([loadMeta(), loadAreas()]);
  if (!mayBeIndexed(meta)) return [];
  const pages = [
    paths.home(),
    paths.methods(),
    paths.sources(),
    paths.accessibility(),
    ...areas.data.areas.map((area) => paths.area(area)),
  ];
  return pages.flatMap((page) => {
    const url = wholeAddress(page);
    return url === null ? [] : [{ url }];
  });
}
