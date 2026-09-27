import type { Metadata } from "next";

import { About } from "@/components/About/About";
import { OpenToAddress } from "@/components/About/OpenToAddress";
import { Key } from "@/components/VibesList/Key";
import { leadOf } from "@/components/VibesList/lead";
import { VibesList } from "@/components/VibesList/VibesList";
import { VIBES } from "@/content/vibes";
import { loadAreas, loadGeometry, loadMeta } from "@/lib/api/server";

export const revalidate = 3600;

/** What a search engine is told of the page is what the page says under its heading. */
export async function generateMetadata(): Promise<Metadata> {
  const { data } = await loadMeta();
  return { title: VIBES.title, description: leadOf(data) };
}

/**
 * The key to the drawings, and then every vibe of the release in short: what it means and
 * the city coloured by it, with how Burro works it out one press away. It is built from
 * routes 11, 4 and 5 and from nothing else, so it says of a vibe what the engine ranks by.
 *
 * It stands on the meadow: its heading in a box, the key in a box, and each vibe in a box
 * of its own. The key comes first: it is what a person who has seen a drawing came for.
 */
export default async function VibesPage() {
  const [{ data }, areas, geometry] = await Promise.all([loadMeta(), loadAreas(), loadGeometry()]);
  return (
    <About title={VIBES.title} lead={`${leadOf(data)} ${VIBES.order}`} art="ui-peg">
      <OpenToAddress />
      <Key meta={data} />
      <VibesList
        meta={data}
        // Only what a link to an area needs is handed on.
        areas={areas.data.areas.map(({ area_id, slug, name }) => ({ area_id, slug, name }))}
        bands={areas.data.bands}
        geometry={geometry.data}
      />
    </About>
  );
}
