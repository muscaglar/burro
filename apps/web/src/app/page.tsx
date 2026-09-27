import type { Metadata } from "next";

import { SearchApp } from "@/components/SearchApp/SearchApp";
import { SEARCH } from "@/content/search";
import { SITE } from "@/content/site";
import { handed } from "@/lib/api/handed";
import { loadAreas, loadMeta } from "@/lib/api/server";
import { bandsToDraw } from "@/lib/holds";

// A built page is kept for an hour at most: the `max-age` the API sends.
export const revalidate = 3600;

// The title says what the page is for, as its heading does, and not the name of the website
// alone. It is written out whole: the layout's pattern is for the pages under it, and this
// page is beside it.
const TITLE = `${SEARCH.title} · ${SITE.name}`;

// What a search engine shows of the website, and what is shown of a link to it where one is
// shared, say what the first page says: who Burro is for, and then what it does.
export const metadata: Metadata = {
  title: { absolute: TITLE },
  description: SITE.description,
  openGraph: { type: "website", siteName: SITE.name, title: TITLE, description: SITE.description },
  twitter: { card: "summary", title: TITLE, description: SITE.description },
};

/**
 * The search page. The server builds the form from route 11 and names every
 * area from route 4. Everything a person does after that is between their
 * browser and the API: nothing they type passes through this server.
 */
export default async function HomePage() {
  const [meta, areas] = await Promise.all([loadMeta(), loadAreas()]);
  // Only the bands a map can be coloured by go to the browser with the page, and of what
  // the service says of the release, no more than a page draws.
  return (
    <SearchApp meta={handed(meta.data)} areas={areas.data.areas} bands={bandsToDraw(meta.data, areas.data.bands)} />
  );
}
