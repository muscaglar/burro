/** @jest-environment node */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import type { ReactElement } from "react";
import { preload } from "react-dom";

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

// What the layout asks a browser to fetch with the page is written down, and not asked of anything.
jest.mock("react-dom", () => ({ ...jest.requireActual("react-dom"), preload: jest.fn() }));

const WEB = path.resolve(__dirname, "..");

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

  test("test_the_face_of_names_is_asked_for_with_the_page_so_that_the_page_does_not_move_as_it_comes", async () => {
    // Seen in a browser, on a phone: asked for once the style sheets had come, the face came
    // after the page was first painted. Its stand-in is far wider, so the links of the name
    // board stood under the name and the heading over the box took a line more, and the
    // whole page jumped up as the face came.
    jest.mocked(preload).mockClear();

    await RootLayout({ children: null });

    const asked = jest.mocked(preload).mock.calls;
    // As a face, and as a style sheet asks for one: asked any other way it is fetched twice.
    expect(asked.map(([, how]) => how)).toEqual([{ as: "font", type: "font/woff2", crossOrigin: "anonymous" }]);
    const [file] = asked.map(([address]) => address);
    expect(existsSync(path.join(WEB, "public", file ?? ""))).toBe(true);

    // It is the file that holds the letters of English in the face of names, and no other:
    // the face of a sentence moves nothing as it comes, and is seven times the size.
    const sheet = (name: string) => readFileSync(path.join(WEB, "src", "styles", name), "utf8");
    const declared = [...sheet("base.css").matchAll(/@font-face\s*\{([^}]*)\}/g)].map(([, block]) => block ?? "");
    const ofNames = /--font-name:\s*("[^"]+")/.exec(sheet("tokens.css"))?.[1] ?? "";
    const holdsTheLetters = declared.filter(
      (block) => block.includes(`font-family: ${ofNames};`) && /unicode-range:\s*U\+0000-00FF/.test(block),
    );
    expect(ofNames).not.toBe("");
    expect(holdsTheLetters).toHaveLength(1);
    expect(holdsTheLetters[0]).toContain(`src: url("${file}") format("woff2");`);
  });

  test("test_the_page_may_be_zoomed_and_is_light_whatever_the_system_asks", () => {
    // The look has no dark colours, so the page does not follow the system to dark.
    expect(viewport).toEqual({ width: "device-width", initialScale: 1, colorScheme: "only light" });
    expect(viewport).not.toHaveProperty("maximumScale");
    expect(viewport).not.toHaveProperty("userScalable");
  });

  test("test_a_built_page_is_built_again_each_hour_and_the_api_is_asked_each_time_by_a_browser", () => {
    // The API tells a browser to ask each time whether an answer still stands, and names the
    // release in the answer's tag, with eight characters of what made the answer. A built
    // page is built again each hour, and a browser that is answered by a newer release
    // reads the form again: docs/design/web.md, section 2.
    const { headers, body } = recordedAnswer("list_areas", "areas");
    const form = recordedAnswer("get_meta", "meta");
    const readByAModel = recordedAnswer("get_meta", "meta-model-reads");

    expect(headers["cache-control"]).toBe("no-cache");
    expect(headers.etag).toMatch(new RegExp(`^"${body.meta.release_id}\\.[0-9a-f]{8}"$`));
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
