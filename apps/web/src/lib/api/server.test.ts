/** @jest-environment node */
import { readRecorded, recordedAnswer, recordedError, responseFrom } from "./recorded";
import { BuildReadError, loadArea, loadAreas, loadGeometry, loadMeta } from "./server";

const BASE = "https://api.example.test";

function answerWith(response: () => Response) {
  const calls: { url: string; init: RequestInit }[] = [];
  globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return response();
  }) as typeof fetch;
  return calls;
}

afterEach(() => {
  delete process.env.NEXT_PUBLIC_BURRO_API_URL;
});

describe("what a page is built from", () => {
  test("test_with_no_address_set_a_build_reads_the_recorded_answers", async () => {
    const [meta, areas, geometry, area] = await Promise.all([
      loadMeta(),
      loadAreas(),
      loadGeometry(),
      loadArea("alderwick"),
    ]);

    expect(meta).toEqual(readRecorded("meta").body);
    expect(areas).toEqual(readRecorded("areas").body);
    expect(geometry).toEqual(readRecorded("geometry").body);
    expect(area).toEqual(readRecorded("area/alderwick").body);
    expect(meta.meta.synthetic).toBe(true);
  });

  test("test_every_area_the_release_lists_can_be_built_with_no_api", async () => {
    const { data } = await loadAreas();

    const built = await Promise.all(data.areas.map(({ slug }) => loadArea(slug)));

    expect(data.areas).toHaveLength(24);
    expect(built.map((area) => area?.data.area.slug)).toEqual(data.areas.map(({ slug }) => slug));
  });

  test.each(["nowhere-at-all", "../meta", "Alderwick", "alderwick/../../meta", ""])(
    "test_a_slug_the_release_lacks_is_no_page_and_not_a_fault: %s",
    async (slug) => {
      expect(await loadArea(slug)).toBeNull();
    },
  );

  test("test_with_an_address_set_a_build_asks_the_api_and_keeps_the_page_an_hour", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = BASE;
    const calls = answerWith(() => responseFrom(recordedAnswer("get_meta", "meta")));

    const meta = await loadMeta();

    expect(meta).toEqual(readRecorded("meta").body);
    expect(calls.map(({ url }) => url)).toEqual([`${BASE}/v1/meta`]);
    expect(calls[0]?.init).toMatchObject({ method: "GET", next: { revalidate: 3600 } });
    expect(calls[0]?.init.body).toBeUndefined();
  });

  test("test_an_area_the_api_does_not_have_is_no_page_and_not_a_fault", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = BASE;
    const calls = answerWith(() => responseFrom(recordedError("area-not-found")));

    expect(await loadArea("alderwick")).toBeNull();
    expect(calls.map(({ url }) => url)).toEqual([`${BASE}/v1/areas/alderwick`]);
  });

  test("test_a_build_stops_when_the_api_cannot_be_read_and_says_only_the_code", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = `${BASE}/secret-path`;
    answerWith(() => responseFrom(recordedError("error-internal")));

    const failure = await loadMeta().catch((error: unknown) => error);

    expect(failure).toBeInstanceOf(BuildReadError);
    expect((failure as Error).message).toBe("The API could not be read for get_meta: internal_error.");
  });

  test("test_a_build_stops_when_the_answer_is_not_the_apis", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = BASE;
    answerWith(() => new Response("<html></html>", { status: 502 }));

    await expect(loadAreas()).rejects.toThrow(
      "The API could not be read for list_areas: unreadable.",
    );
  });
});
