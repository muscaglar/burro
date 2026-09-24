import type { Metadata } from "next";

import { MethodsTables } from "@/components/MethodsTables/MethodsTables";
import { METHODS } from "@/content/methods";
import { loadMeta } from "@/lib/api/server";

export const revalidate = 3600;

export const metadata: Metadata = { title: METHODS.title, description: METHODS.lead };

export default async function MethodsPage() {
  const { data } = await loadMeta();
  return (
    <>
      <h1>{METHODS.title}</h1>
      <p>{METHODS.lead}</p>
      <MethodsTables meta={data} />
    </>
  );
}
