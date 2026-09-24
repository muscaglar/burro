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

  test("test_a_built_page_is_built_again_each_hour_and_the_api_is_asked_each_time_by_a_browser", () => {
    // The API tells a browser to ask each time whether an answer still stands, and names the
    // release in the answer's tag. A built page is built again each hour, and a browser that
    // is answered by a newer release reads the form again: docs/design/web.md, section 2.
    const { headers, body } = recordedAnswer("list_areas", "areas");
    const form = recordedAnswer("get_meta", "meta");
    const readByAModel = recordedAnswer("get_meta", "meta-model-reads");

    expect(headers["cache-control"]).toBe("no-cache");
    expect(headers.etag).toBe(`"${body.meta.release_id}"`);
    // The form also says who reads what is typed, which is no part of the release. Its tag
    // names both, so that an answer which tells of another reader is never kept.
    expect(form.headers["cache-control"]).toBe("no-cache");
    expect(form.headers.etag).toMatch(new RegExp(`^"${body.meta.release_id}\\.[0-9a-f]{8}"$`));
    expect(readByAModel.body.meta.release_id).toBe(body.meta.release_id);
    expect(readByAModel.headers.etag).not.toBe(form.headers.etag);
    expect(REVALIDATE_SECONDS).toBe(3_600);
    expect(revalidate).toBe(REVALIDATE_SECONDS);
  });
});
