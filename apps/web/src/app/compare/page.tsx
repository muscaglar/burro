import type { Metadata } from "next";

import { CompareView } from "@/components/CompareTable/CompareView";
import { COMPARE } from "@/content/compare";
import { loadAreas, loadMeta } from "@/lib/api/server";
import { chosenFrom } from "@/lib/compare/list";
import { KEEP_OUT } from "@/lib/indexing";

export const metadata: Metadata = {
  title: COMPARE.title,
  description: COMPARE.lead,
  // A comparison is one person's choice of areas. It is never a page to index.
  robots: KEEP_OUT,
};

interface Props {
  readonly searchParams: Promise<{ readonly a?: string | readonly string[] }>;
}

/** The most values of the address that are read at all. A comparison takes four. */
const MOST_READ = 16;

/**
 * The comparison page. The address holds the slugs of the areas and nothing
 * else: a slug is reached by pressing, never by typing. Whatever in it is not
 * the slug of an area of the release is counted and dropped, and is never
 * shown or sent on.
 *
 * The server names the areas. The comparison itself is asked for by the
 * browser, with the search it holds in memory, which this server never sees.
 */
export default async function ComparePage({ searchParams }: Props) {
  const [{ a }, meta, areas] = await Promise.all([searchParams, loadMeta(), loadAreas()]);
  const given = (a === undefined ? [] : typeof a === "string" ? [a] : a).slice(0, MOST_READ);
  // Only what is the slug of an area of the release is kept. The rest is counted, and gone.
  const { chosen, unknown, dropped } = chosenFrom(given, areas.data.areas);
  return <CompareView chosen={chosen} defaults={meta.data.defaults} unknown={unknown} dropped={dropped} />;
}
