import type { Metadata } from "next";

import { About } from "@/components/About/About";
import { SourceList } from "@/components/SourceList/SourceList";
import { SOURCES } from "@/content/sources";
import { loadMeta } from "@/lib/api/server";

export const revalidate = 3600;

export const metadata: Metadata = { title: SOURCES.title, description: SOURCES.lead };

/**
 * Every source of the release, plainly, as a list: who published it, under which licence,
 * with its link and the credit its publisher asks for, all of it in sight. It stands on the
 * meadow: its heading in a box, with the key the look draws a source by beside it, and
 * under it the list, in a box of its own.
 */
export default async function SourcesPage() {
  const { data } = await loadMeta();
  return (
    <About title={SOURCES.title} lead={SOURCES.lead} art="ui-key">
      <SourceList sources={data.attributions} features={data.features} />
    </About>
  );
}
