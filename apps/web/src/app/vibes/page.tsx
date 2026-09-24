import type { Metadata } from "next";

import { VibesList } from "@/components/VibesList/VibesList";
import { VIBES } from "@/content/vibes";
import { loadAreas, loadGeometry, loadMeta } from "@/lib/api/server";

export const revalidate = 3600;

export const metadata: Metadata = { title: VIBES.title, description: VIBES.lead };

/**
 * Every vibe of the release, each with what it means, the city coloured by
 * it, its recipe and what it cannot see. It is built from routes 11, 4 and 5
 * and from nothing else, so it says of a vibe what the engine ranks by.
 */
export default async function VibesPage() {
  const [{ data }, areas, geometry] = await Promise.all([loadMeta(), loadAreas(), loadGeometry()]);
  return (
    <>
      <h1>{VIBES.title}</h1>
      <p>{VIBES.lead}</p>
      <VibesList
        meta={data}
        // Only what a link to an area needs is handed on.
        areas={areas.data.areas.map(({ area_id, slug, name }) => ({ area_id, slug, name }))}
        bands={areas.data.bands}
        geometry={geometry.data}
      />
    </>
  );
}
