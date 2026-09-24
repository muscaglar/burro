/** @jest-environment node */
/**
 * What the website tells a search engine, held to one rule: a page may be
 * indexed only when the release is real and the website knows its own
 * address. The pages, the header every answer carries, the robots file and
 * the sitemap must all agree.
 *
 * A crawler is always let in. One that is kept out by the robots file never
 * reads the page that asks to be left out, and may list its address anyway.
 */

import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import AreaPage, { generateMetadata as describeArea } from "@/app/[city]/[area]/page";
import { metadata as compareMetadata } from "@/app/compare/page";
import { generateMetadata as describeSite } from "@/app/layout";
import robots from "@/app/robots";
import { metadata as sharedMetadata } from "@/app/s/page";
import sitemap from "@/app/sitemap";
import { KEEP_OUT_HEADER } from "@/lib/indexing";
import { recordedAnswer } from "@/lib/api/recorded";
import type { AreaData, Meta } from "@/lib/api/schema";

import config from "../next.config";

const recorded = {
  meta: recordedAnswer("get_meta", "meta").body,
  areas: recordedAnswer("list_areas", "areas").body,
};
const SITE = "https://burro.example";
const REAL: Meta = { ...recorded.meta.meta, release_id: "lon-2027-01-20-01", synthetic: false };

/** What the release says of itself. `null` when it cannot be read. */
let meta: Meta | null = recorded.meta.meta;

function read(): Meta {
  if (meta === null) throw new Error("The release could not be read.");
  return meta;
}

jest.mock("@/lib/api/server", () => {
  const actual = jest.requireActual<typeof import("@/lib/api/server")>("@/lib/api/server");
  return {
    ...actual,
    loadMeta: async () => ({ meta: read(), data: { ...recorded.meta.data, synthetic: read().synthetic } }),
    loadAreas: async () => ({ meta: read(), data: recorded.areas.data }),
    loadArea: async (slug: string) => {
      const loaded = await actual.loadArea(slug);
      return loaded === null ? null : { ...loaded, meta: read() };
    },
  };
});

const at = (area: string) => ({ params: Promise.resolve({ city: "synthetic", area }) });

interface Told {
  readonly pagesAskToBeLeftOut: boolean;
  /** True when every answer, a page or not, carries the header that asks to be left out. */
  readonly headerAsksToBeLeftOut: boolean;
  /** True when a crawler may fetch every page, and so can read what the page asks of it. */
  readonly crawlersAreLetIn: boolean;
  readonly sitemapNamed: boolean;
  readonly listed: number;
  readonly canonical: boolean;
  readonly structured: boolean;
}

/** The paths whose answers carry the header that asks a search engine to leave them out. */
async function keptOutByHeader(): Promise<string[]> {
  const served = (await config.headers?.()) ?? [];
  return served
    .filter(({ headers }) =>
      headers.some(({ key, value }) => key === KEEP_OUT_HEADER.key && value === KEEP_OUT_HEADER.value),
    )
    .map(({ source }) => source)
    .sort();
}

/** Everything the website tells a search engine, as it stands. */
async function told(): Promise<Told> {
  const [site, area, file, map, page, byHeader] = await Promise.all([
    describeSite(),
    describeArea(at("alderwick")),
    robots(),
    sitemap(),
    AreaPage(at("alderwick")),
    keptOutByHeader(),
  ]);
  const rules = Array.isArray(file.rules) ? file.rules : [file.rules];
  return {
    pagesAskToBeLeftOut: site.robots !== undefined && site.robots !== null,
    headerAsksToBeLeftOut: byHeader.includes("/:path*"),
    crawlersAreLetIn:
      rules.some((rule) => rule.userAgent === "*" && rule.allow === "/") &&
      rules.every((rule) => rule.disallow === undefined),
    sitemapNamed: file.sitemap !== undefined,
    listed: map.length,
    canonical: area.alternates?.canonical !== undefined,
    structured: renderToStaticMarkup(page as ReactElement).includes("application/ld+json"),
  };
}

const KEPT_OUT: Told = {
  pagesAskToBeLeftOut: true,
  headerAsksToBeLeftOut: true,
  crawlersAreLetIn: true,
  sitemapNamed: false,
  listed: 0,
  canonical: false,
  structured: false,
};

beforeEach(() => {
  meta = recorded.meta.meta;
});

afterEach(() => {
  delete process.env.BURRO_SITE_URL;
});

describe("while the release is made up", () => {
  test("test_a_made_up_place_is_kept_from_search_engines_everywhere_at_once", async () => {
    expect(await told()).toEqual(KEPT_OUT);
  });

  test("test_knowing_the_websites_address_does_not_let_a_made_up_place_be_found", async () => {
    process.env.BURRO_SITE_URL = SITE;

    expect(await told()).toEqual(KEPT_OUT);
  });

  test("test_the_robots_file_lets_a_crawler_in_to_read_that_the_page_asks_to_be_left_out", async () => {
    // Kept out by the robots file, a crawler never fetches the page, so it never reads
    // `noindex`, and may still list the address of a made-up place from a link elsewhere.
    expect(await robots()).toEqual({ rules: { userAgent: "*", allow: "/" } });
  });

  test("test_what_is_not_a_page_asks_to_be_left_out_as_well", async () => {
    // The robots file, the icon and a script can carry no `robots` of their own. The header does it.
    expect(await keptOutByHeader()).toEqual(["/:path*"]);
  });
});

describe("when the release is real", () => {
  beforeEach(() => {
    meta = REAL;
  });

  test("test_a_website_that_does_not_know_its_address_is_still_kept_out", async () => {
    expect(await told()).toEqual(KEPT_OUT);
  });

  test("test_the_pages_the_robots_file_and_the_sitemap_all_let_a_search_engine_in", async () => {
    process.env.BURRO_SITE_URL = SITE;

    expect(await told()).toEqual({
      pagesAskToBeLeftOut: false,
      headerAsksToBeLeftOut: false,
      crawlersAreLetIn: true,
      sitemapNamed: true,
      listed: 4 + recorded.areas.data.areas.length,
      canonical: true,
      structured: true,
    });
  });

  test("test_the_robots_file_names_the_sitemap_at_the_websites_own_address", async () => {
    process.env.BURRO_SITE_URL = `${SITE}/`;

    expect(await robots()).toEqual({
      rules: { userAgent: "*", allow: "/" },
      sitemap: `${SITE}/sitemap.xml`,
    });
  });

  test("test_the_sitemap_lists_the_search_the_pages_about_the_website_and_every_area", async () => {
    process.env.BURRO_SITE_URL = SITE;

    const listed = (await sitemap()).map((entry) => entry.url);

    expect(listed).toEqual([
      `${SITE}/`,
      `${SITE}/methods`,
      `${SITE}/sources`,
      `${SITE}/accessibility`,
      ...recorded.areas.data.areas.map((area) => `${SITE}/synthetic/${area.slug}`),
    ]);
    expect(new Set(listed).size).toBe(listed.length);
  });

  test("test_the_sitemap_lists_no_comparison_and_no_shared_search", async () => {
    process.env.BURRO_SITE_URL = SITE;

    const listed = (await sitemap()).map((entry) => new URL(entry.url));

    expect(listed.filter((url) => url.pathname.startsWith("/compare") || url.pathname === "/s")).toEqual([]);
    expect(listed.filter((url) => url.search !== "" || url.hash !== "")).toEqual([]);
  });

  test("test_the_structured_data_on_the_page_is_what_the_areas_fact_says", async () => {
    process.env.BURRO_SITE_URL = SITE;

    const html = renderToStaticMarkup((await AreaPage(at("alderwick"))) as ReactElement);
    const written = /<script type="application\/ld\+json">(.*?)<\/script>/s.exec(html)?.[1] ?? "";

    expect(JSON.parse(written)).toEqual({
      "@context": "https://schema.org",
      "@type": "Place",
      name: "Alderwick",
      url: `${SITE}/synthetic/alderwick`,
      containedInPlace: { "@type": "AdministrativeArea", name: "Quillhaven" },
    });
  });
});

describe("the pages that are one person's", () => {
  test.each([
    ["a comparison", compareMetadata],
    ["an opened share", sharedMetadata],
  ])("test_%s_is_never_a_page_to_index", (_, described) => {
    expect(described.robots).toEqual({ index: false, follow: false });
  });

  test("test_they_carry_the_header_too_when_every_other_page_may_be_indexed", async () => {
    meta = REAL;
    process.env.BURRO_SITE_URL = SITE;

    expect(await keptOutByHeader()).toEqual(["/compare", "/s"]);
  });
});

describe("when the release cannot be read", () => {
  test("test_nothing_may_be_indexed_and_the_build_is_not_stopped_by_the_header", async () => {
    process.env.BURRO_SITE_URL = SITE;
    meta = null;

    expect(await keptOutByHeader()).toEqual(["/:path*"]);
  });
});

describe("an area's page with scripts off", () => {
  test("test_the_page_as_it_is_built_holds_every_fact_with_its_source_and_its_date", async () => {
    const data: AreaData = recordedAnswer("get_area", "area/alderwick").body.data;

    const html = renderToStaticMarkup((await AreaPage(at("alderwick"))) as ReactElement);
    const text = html.replace(/<[^>]+>/g, "").replace(/&#x27;/g, "'").replace(/&amp;/g, "&");

    for (const fact of data.facts) {
      const slot = fact.slots.standing ?? fact.slots.median ?? fact.slots.name ?? "";
      expect(text.includes(slot)).toBe(true);
    }
    // One written-out source for each fact, and no button that must be pressed to read it.
    expect(html.match(/href="\/sources#synthetic"/g)?.length).toBeGreaterThanOrEqual(data.facts.length);
    expect(html).not.toContain("aria-expanded");
  });
});
