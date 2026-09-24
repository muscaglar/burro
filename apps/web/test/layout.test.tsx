/** @jest-environment node */
import type { ReactElement } from "react";

import RootLayout, { generateMetadata, revalidate, viewport } from "@/app/layout";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Meta } from "@/lib/api/schema";
import { REVALIDATE_SECONDS } from "@/lib/api/server";

const recorded = recordedAnswer("get_meta", "meta").body;
let meta: Meta = recorded.meta;

jest.mock("@/lib/api/server", () => ({
  ...jest.requireActual("@/lib/api/server"),
  loadMeta: async () => ({ meta, data: recorded.data }),
}));

beforeEach(() => {
  meta = recorded.meta;
});

afterEach(() => {
  delete process.env.BURRO_SITE_URL;
});

describe("the layout every page is laid out in", () => {
  test("test_a_made_up_place_is_kept_from_search_engines", async () => {
    expect((await generateMetadata()).robots).toEqual({ index: false, follow: false });
  });

  test("test_a_page_built_on_real_data_may_be_indexed", async () => {
    meta = { ...recorded.meta, release_id: "lon-2027-01-20-01", synthetic: false };
    process.env.BURRO_SITE_URL = "https://burro.example";

    expect((await generateMetadata()).robots).toBeUndefined();
  });

  test("test_a_page_that_cannot_say_where_it_lives_is_kept_from_search_engines", async () => {
    meta = { ...recorded.meta, release_id: "lon-2027-01-20-01", synthetic: false };

    expect((await generateMetadata()).robots).toEqual({ index: false, follow: false });
  });

  test("test_a_made_up_place_is_kept_from_search_engines_whatever_the_address", async () => {
    process.env.BURRO_SITE_URL = "https://burro.example";

    expect((await generateMetadata()).robots).toEqual({ index: false, follow: false });
  });

  test("test_no_page_tells_another_site_where_a_person_came_from", async () => {
    expect((await generateMetadata()).referrer).toBe("no-referrer");
  });

  test("test_the_page_says_what_language_it_is_in", async () => {
    const html = (await RootLayout({ children: null })) as ReactElement<{ lang: string }>;

    expect(html.type).toBe("html");
    expect(html.props.lang).toBe("en-GB");
  });

  test("test_the_page_may_be_zoomed_and_follows_the_systems_light_or_dark", () => {
    expect(viewport).toEqual({ width: "device-width", initialScale: 1, colorScheme: "light dark" });
    expect(viewport).not.toHaveProperty("maximumScale");
    expect(viewport).not.toHaveProperty("userScalable");
  });

  test("test_a_built_page_is_kept_no_longer_than_the_api_says_its_answer_may_be", () => {
    const sent = recordedAnswer("get_meta", "meta").headers["cache-control"];

    expect(sent).toBe(`public, max-age=${REVALIDATE_SECONDS}`);
    expect(revalidate).toBe(REVALIDATE_SECONDS);
  });
});
