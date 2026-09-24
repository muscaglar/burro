/** @jest-environment node */
import { renderToStaticMarkup } from "react-dom/server";

import { AREA } from "@/content/area";
import { recordedAnswer } from "@/lib/api/recorded";
import type { AreaData, Meta } from "@/lib/api/schema";

import { asScriptText, metadataFor, namedBy, structuredDataFor } from "./describe";

const recorded = recordedAnswer("get_area", "area/alderwick").body;
const data: AreaData = recorded.data;
const madeUp: Meta = recorded.meta;
const real: Meta = { ...recorded.meta, release_id: "lon-2027-01-20-01", synthetic: false };
const SITE = "https://burro.example";

/** Every string the API said of the area that is not its name or its borough. */
function everythingElseSaidOf(area: AreaData): string[] {
  const named = new Set(["Alderwick", "Quillhaven"]);
  return area.facts
    .flatMap((fact) => [...Object.values(fact.slots), ...fact.numbers, ...fact.names])
    .filter((text) => text.length > 1 && !named.has(text));
}

afterEach(() => {
  delete process.env.BURRO_SITE_URL;
});

describe("what an area's page tells a search engine", () => {
  test("test_the_title_and_the_description_say_only_what_the_areas_fact_says", () => {
    const { title, description } = metadataFor(data, madeUp);

    expect(title).toBe("Alderwick, Quillhaven");
    expect(description).toBe(AREA.description("Alderwick", "Quillhaven"));
    // No figure, and nothing else the API said of the place.
    expect(/\d/.test(`${String(title)} ${String(description)}`)).toBe(false);
    expect(everythingElseSaidOf(data).filter((text) => String(description).includes(text))).toEqual([]);
  });

  test("test_the_description_describes_the_page_and_passes_no_judgement_on_the_place", () => {
    const description = AREA.description("", "");

    expect(/\b(best|great|good|bad|safe|unsafe|popular|vibrant|desirable|sought|lovely|quiet|leafy)\b/i.test(description)).toBe(false);
    expect(description).not.toMatch(/!/);
  });

  test("test_the_name_and_the_borough_are_the_facts_and_not_the_records", () => {
    const renamed: AreaData = { ...data, area: { ...data.area, name: "Not the fact", borough: "Nor this" } };

    expect(namedBy(renamed)).toEqual({ name: "Alderwick", borough: "Quillhaven" });
    expect(metadataFor(renamed, madeUp).title).toBe("Alderwick, Quillhaven");
  });

  test("test_an_area_with_no_fact_to_name_it_says_nothing_of_itself", () => {
    const unnamed: AreaData = { ...data, facts: data.facts.filter((fact) => fact.kind !== "area") };
    process.env.BURRO_SITE_URL = SITE;

    expect(metadataFor(unnamed, real)).toEqual({ robots: { index: false, follow: false } });
    expect(structuredDataFor(unnamed, real)).toBeNull();
  });

  test("test_a_made_up_place_has_no_canonical_address_and_asks_not_to_be_indexed", () => {
    process.env.BURRO_SITE_URL = SITE;

    const described = metadataFor(data, madeUp);

    expect(described.alternates).toBeUndefined();
    expect(described.robots).toEqual({ index: false, follow: false });
  });

  test("test_a_real_place_at_a_known_address_has_a_canonical_address", () => {
    process.env.BURRO_SITE_URL = SITE;

    const described = metadataFor(data, real);

    expect(described.alternates).toEqual({ canonical: `${SITE}/synthetic/alderwick` });
    expect(described.robots).toBeUndefined();
  });

  test("test_a_page_that_cannot_say_where_it_lives_has_no_canonical_address", () => {
    const described = metadataFor(data, real);

    expect(described.alternates).toBeUndefined();
    expect(described.robots).toEqual({ index: false, follow: false });
  });
});

describe("the structured data of an area's page", () => {
  test("test_a_made_up_place_has_no_structured_data", () => {
    process.env.BURRO_SITE_URL = SITE;

    expect(structuredDataFor(data, madeUp)).toBeNull();
  });

  test("test_structured_data_holds_the_name_the_borough_and_the_address_and_nothing_else", () => {
    process.env.BURRO_SITE_URL = SITE;

    const structured = structuredDataFor(data, real);

    expect(structured).toEqual({
      "@context": "https://schema.org",
      "@type": "Place",
      name: "Alderwick",
      url: `${SITE}/synthetic/alderwick`,
      containedInPlace: { "@type": "AdministrativeArea", name: "Quillhaven" },
    });
    const written = JSON.stringify(structured);
    expect(everythingElseSaidOf(data).filter((text) => written.includes(text))).toEqual([]);
    // Where a place is on the map is served, and no fact holds it, so it is not said.
    expect(written).not.toContain(String(data.area.centroid[0]));
  });

  test("test_a_name_cannot_close_the_script_it_is_written_in", () => {
    const hostile = { name: '</script><script>alert("x")</script>', note: "<!-- -->" };

    const text = asScriptText(hostile);
    const html = renderToStaticMarkup(<script type="application/ld+json">{text}</script>);

    expect(text).not.toContain("<");
    expect(html.match(/<\/script>/g)).toHaveLength(1);
    expect(JSON.parse(text)).toEqual(hostile);
  });

  test("test_the_script_holds_the_data_as_it_was_written_and_not_as_markup", () => {
    process.env.BURRO_SITE_URL = SITE;
    const text = asScriptText(structuredDataFor(data, real));

    const html = renderToStaticMarkup(<script type="application/ld+json">{text}</script>);
    const inside = /^<script type="application\/ld\+json">(.*)<\/script>$/s.exec(html)?.[1] ?? "";

    // What is inside the script is read as it is, so a quote must still be a quote.
    expect(inside).not.toContain("&quot;");
    expect(JSON.parse(inside)).toEqual(structuredDataFor(data, real));
  });
});
