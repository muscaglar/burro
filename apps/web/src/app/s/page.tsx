import type { Metadata } from "next";

import { SharedSearch } from "@/components/SharedSearch/SharedSearch";
import { SHARED } from "@/content/share";
import { loadAreas, loadMeta } from "@/lib/api/server";
import { KEEP_OUT } from "@/lib/indexing";

// A built page is kept for an hour at most: the `max-age` the API sends.
export const revalidate = 3600;

export const metadata: Metadata = {
  title: SHARED.pageTitle,
  description: SHARED.pageDescription,
  // The page is the same for every link, and holds nothing until one is opened.
  robots: KEEP_OUT,
};

/**
 * The page a shared link opens. The id of the share is in the fragment of
 * the address, which a browser sends to no server, so this page is built
 * once and is the same for every link. The browser reads the id and asks the
 * API for the share.
 */
export default async function SharedPage() {
  const [meta, areas] = await Promise.all([loadMeta(), loadAreas()]);
  return <SharedSearch meta={meta.data} areas={areas.data.areas} />;
}
