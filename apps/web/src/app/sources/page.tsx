import type { Metadata } from "next";

import { SourceList } from "@/components/SourceList/SourceList";
import { SOURCES } from "@/content/sources";
import { loadMeta } from "@/lib/api/server";

export const revalidate = 3600;

export const metadata: Metadata = { title: SOURCES.title, description: SOURCES.lead };

export default async function SourcesPage() {
  const { data } = await loadMeta();
  return (
    <>
      <h1>{SOURCES.title}</h1>
      <p>{SOURCES.lead}</p>
      <SourceList sources={data.attributions} features={data.features} />
    </>
  );
}
