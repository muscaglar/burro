/** @jest-environment node */
/**
 * The map of the website, as a search engine is handed it: the search, the pages about the
 * website, and a page for each area. What a search engine is told of any page, and when it
 * is told nothing, is held with the rule of indexing, under test/indexing.test.tsx.
 *
 * This holds which pages the map names. A statement of accessibility was one of them. The
 * page is gone, and an address that leads nowhere is handed to nobody.
 */

import { recordedAnswer } from "@/lib/api/recorded";
import type { Meta } from "@/lib/api/schema";
import { paths } from "@/lib/paths";

import sitemap from "./sitemap";

const recorded = {
  meta: recordedAnswer("get_meta", "meta").body,
  areas: recordedAnswer("list_areas", "areas").body,
};
const SITE = "https://burro.example";
/** A release that is not made up: a made-up place is listed nowhere. */
const REAL: Meta = { ...recorded.meta.meta, release_id: "lon-2027-01-20-01", synthetic: false };

jest.mock("@/lib/api/server", () => {
  const actual = jest.requireActual<typeof import("@/lib/api/server")>("@/lib/api/server");
  return {
    ...actual,
    loadMeta: async () => ({ meta: REAL, data: { ...recorded.meta.data, synthetic: false } }),
    loadAreas: async () => ({ meta: REAL, data: recorded.areas.data }),
  };
});

beforeEach(() => {
  process.env.BURRO_SITE_URL = SITE;
});

afterEach(() => {
  delete process.env.BURRO_SITE_URL;
});

describe("the map of the website", () => {
  test("test_it_names_the_search_the_three_pages_about_the_website_and_every_area_and_no_other_page", async () => {
    const listed = (await sitemap()).map((entry) => entry.url);

    expect(listed).toEqual([
      `${SITE}/`,
      `${SITE}/vibes`,
      `${SITE}/methods`,
      `${SITE}/sources`,
      ...recorded.areas.data.areas.map((area) => `${SITE}/synthetic/${area.slug}`),
    ]);
    expect(new Set(listed).size).toBe(listed.length);
  });

  test("test_it_names_no_statement_of_accessibility_since_the_website_has_none", async () => {
    const listed = (await sitemap()).map((entry) => new URL(entry.url).pathname);

    expect(listed.filter((path) => /accessib/i.test(path))).toEqual([]);
    // Every page about the website that it names is one the website builds an address for.
    const about = listed.filter((path) => path !== "/" && !path.startsWith("/synthetic/"));
    expect(about).toEqual([paths.vibes(), paths.methods(), paths.sources()]);
  });
});
