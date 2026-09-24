import type { Metadata } from "next";

import { SearchApp } from "@/components/SearchApp/SearchApp";
import { SEARCH } from "@/content/search";
import { SITE } from "@/content/site";
import { loadAreas, loadMeta } from "@/lib/api/server";
import { bandsToDraw } from "@/lib/holds";

// A built page is kept for an hour at most: the `max-age` the API sends.
export const revalidate = 3600;

// The title says what the page is for, as its heading does, and not the name of the website
// alone. It is written out whole: the layout's pattern is for the pages under it, and this
// page is beside it.
export const metadata: Metadata = { title: { absolute: `${SEARCH.title} · ${SITE.name}` } };

/**
 * The search page. The server builds the form from route 11 and names every
 * area from route 4. Everything a person does after that is between their
 * browser and the API: nothing they type passes through this server.
 */
export default async function HomePage() {
  const [meta, areas] = await Promise.all([loadMeta(), loadAreas()]);
  // Only the bands a map can be coloured by go to the browser with the page.
  return (
    <SearchApp meta={meta.data} areas={areas.data.areas} bands={bandsToDraw(meta.data, areas.data.bands)} />
  );
}
