import type { Metadata } from "next";

import { About } from "@/components/About/About";
import { OpenToAddress } from "@/components/About/OpenToAddress";
import { MethodsTables } from "@/components/MethodsTables/MethodsTables";
import { METHODS } from "@/content/methods";
import { loadMeta } from "@/lib/api/server";

export const revalidate = 3600;

export const metadata: Metadata = { title: METHODS.title, description: METHODS.lead };

/**
 * How Burro works. It stands on the meadow: its heading in a box, a short account in a box
 * under it, and then all of the rest, folded. Another page leads to a part of the rest by
 * its id: the fold is opened for whoever comes by such a link.
 */
export default async function MethodsPage() {
  const { data } = await loadMeta();
  return (
    <About title={METHODS.title} lead={METHODS.lead} art="ui-weight">
      <OpenToAddress />
      <MethodsTables meta={data} />
    </About>
  );
}
