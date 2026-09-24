import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { cache } from "react";

import { AreaProfile } from "@/components/AreaProfile/AreaProfile";
import { loadArea, loadAreas, loadGeometry, loadMeta } from "@/lib/api/server";
import { asScriptText, metadataFor, structuredDataFor } from "@/lib/area/describe";
import { cityOf, isCity } from "@/lib/city";
import { isSlug } from "@/lib/paths";

// A built page is kept for an hour at most: the `max-age` the API sends.
export const revalidate = 3600;

interface Props {
  readonly params: Promise<{ readonly city: string; readonly area: string }>;
}

/** One page for each area of the release, from route 4. */
export async function generateStaticParams() {
  const { data } = await loadAreas();
  return data.areas.flatMap((area) => {
    const city = cityOf(area.area_id);
    return city === null ? [] : [{ city, area: area.slug }];
  });
}

/** Read once for a page, though its title and its body both ask. */
const areaOf = cache(async (city: string, slug: string) => {
  if (!isCity(city) || !isSlug(slug)) return null;
  const loaded = await loadArea(slug);
  // An area is found under its own city, and its own slug, and nowhere else.
  if (loaded === null || cityOf(loaded.data.area.area_id) !== city) return null;
  return loaded.data.area.slug === slug ? loaded : null;
});

/** The area at this address, or `null` when the release has none there. */
async function areaAt({ params }: Props) {
  const { city, area } = await params;
  return areaOf(city, area);
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const loaded = await areaAt(props);
  return loaded === null ? {} : metadataFor(loaded.data, loaded.meta);
}

/**
 * One area's page. It is built ahead of time from the API, and reads with
 * scripts off. A slug the release lacks is a page not found.
 */
export default async function AreaPage(props: Props) {
  const loaded = await areaAt(props);
  if (loaded === null) notFound();
  const [meta, geometry] = await Promise.all([loadMeta(), loadGeometry()]);
  const structured = structuredDataFor(loaded.data, loaded.meta);
  return (
    <>
      {structured === null ? null : (
        // Data for a search engine to read. It is no program, and nothing runs it.
        <script type="application/ld+json">{asScriptText(structured)}</script>
      )}
      <AreaProfile data={loaded.data} meta={meta.data} geometry={geometry.data} />
    </>
  );
}
