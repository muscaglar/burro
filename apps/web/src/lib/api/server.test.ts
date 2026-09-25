/** @jest-environment node */
import { ROUTES } from "./operations";
import { readRecorded, recordedAnswer, recordedError, responseFrom } from "./recorded";
import type { AreaData, GeometryData } from "./schema";
import {
  BuildReadError,
  forgetTheOutlines,
  loadArea,
  loadAreas,
  loadGeometry,
  loadMeta,
  type Loaded,
} from "./server";

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
  forgetTheOutlines();
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

  test("test_the_outlines_are_asked_for_once_however_many_pages_are_built", async () => {
    // Seen in a build of a thousand areas: the outlines were asked for once for every page,
    // a thousand times over, because the answer is too large for the framework to keep.
    // The service fell behind, and the build stopped on a page that waited too long.
    process.env.NEXT_PUBLIC_BURRO_API_URL = BASE;
    const calls = answerWith(() => responseFrom(recordedAnswer("get_geometry", "geometry")));

    const read = await Promise.all([loadGeometry(), loadGeometry(), loadGeometry()]);
    const again = await loadGeometry();

    expect(calls.map(({ url }) => url)).toEqual([`${BASE}/v1/areas/geometry`]);
    for (const one of [...read, again]) expect(one).toEqual(readRecorded("geometry").body);
  });

  test("test_outlines_that_could_not_be_read_are_asked_for_again", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = BASE;
    const failing = answerWith(() => responseFrom(recordedError("error-internal")));
    await expect(loadGeometry()).rejects.toBeInstanceOf(BuildReadError);
    expect(failing).toHaveLength(1);

    const calls = answerWith(() => responseFrom(recordedAnswer("get_geometry", "geometry")));
    expect(await loadGeometry()).toEqual(readRecorded("geometry").body);
    expect(calls).toHaveLength(1);
  });

  test("test_the_outlines_are_kept_no_longer_than_a_built_page_is", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = BASE;
    const calls = answerWith(() => responseFrom(recordedAnswer("get_geometry", "geometry")));
    const clock = jest.spyOn(Date, "now");
    try {
      clock.mockReturnValue(1_000_000);
      await loadGeometry();
      clock.mockReturnValue(1_000_000 + 3_599_000);
      await loadGeometry();
      expect(calls).toHaveLength(1);
      clock.mockReturnValue(1_000_000 + 3_601_000);
      await loadGeometry();
      expect(calls).toHaveLength(2);
    } finally {
      clock.mockRestore();
    }
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

/**
 * Seen in a build of a thousand areas: every worker asked one service at once, the service
 * fell behind, and the one answer that came after ten seconds stopped the whole build.
 */
describe("a read that a busy service was late with", () => {
  /** Answers each call in turn, and says how long each call that never answered was waited for. */
  function answerInTurn(turns: readonly (() => Response | "never")[]) {
    const waited: number[] = [];
    const asked: number[] = [];
    globalThis.fetch = (async (_url: RequestInfo | URL, init?: RequestInit) => {
      const at = Date.now();
      asked.push(at);
      const turn = turns[Math.min(asked.length, turns.length) - 1];
      const answer = turn === undefined ? "never" : turn();
      if (answer !== "never") return answer;
      return new Promise<Response>((_, reject) => {
        init?.signal?.addEventListener("abort", () => {
          waited.push(Date.now() - at);
          reject(new Error("stopped"));
        });
      });
    }) as typeof fetch;
    return { asked, waited };
  }

  const never = () => "never" as const;
  const busy = () => new Response("Service Unavailable", { status: 503 });
  const area = () => responseFrom(recordedAnswer("get_area", "area/alderwick"));

  /** The area an answer is of. A whole answer is never printed by a test that fails. */
  const areaOf = (read: unknown) => (read as Loaded<AreaData> | null)?.data?.area?.slug;
  const outlinesOf = (read: unknown) => (read as Loaded<GeometryData> | null)?.data?.features?.length;

  /** Lets the clock run until the read has ended, however it ends. */
  async function ended<T>(reading: Promise<T>): Promise<T | Error> {
    const result = reading.catch((error: unknown) => error as Error);
    await jest.advanceTimersByTimeAsync(10 * 60_000);
    return result;
  }

  beforeEach(() => {
    jest.useFakeTimers();
    process.env.NEXT_PUBLIC_BURRO_API_URL = BASE;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("test_a_read_that_timed_out_is_tried_again_and_waited_for_longer_each_time", async () => {
    const calls = answerInTurn([never, never, area]);

    const read = await ended(loadArea("alderwick"));

    expect(areaOf(read)).toBe("alderwick");
    expect(calls.asked).toHaveLength(3);
    expect(calls.waited).toEqual([10_000, 20_000]);
  });

  test("test_a_read_is_not_tried_again_until_the_service_has_had_a_moment", async () => {
    const calls = answerInTurn([busy, busy, area]);

    const read = await ended(loadArea("alderwick"));

    expect(areaOf(read)).toBe("alderwick");
    const [first = 0, second = 0, third = 0] = calls.asked;
    expect(second - first).toBeGreaterThanOrEqual(1_000);
    expect(third - second).toBeGreaterThan(second - first);
  });

  test.each([
    ["too many requests", 429],
    ["not there just now", 503],
    ["late behind what stands before it", 504],
  ])("test_a_read_is_tried_again_when_the_service_says_it_is_%s", async (_, status) => {
    const calls = answerInTurn([() => new Response("", { status }), area]);

    const read = await ended(loadArea("alderwick"));

    expect(areaOf(read)).toBe("alderwick");
    expect(calls.asked).toHaveLength(2);
  });

  test("test_a_read_whose_answer_never_came_back_is_tried_again", async () => {
    const calls = answerInTurn([
      () => {
        throw new TypeError("fetch failed");
      },
      area,
    ]);

    const read = await ended(loadArea("alderwick"));

    expect(areaOf(read)).toBe("alderwick");
    expect(calls.asked).toHaveLength(2);
  });

  test("test_a_build_stops_after_the_last_try_and_says_which_read_failed", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = `${BASE}/secret-path`;
    const calls = answerInTurn([never]);

    const failure = await ended(loadArea("alderwick"));

    expect(failure).toBeInstanceOf(BuildReadError);
    expect((failure as Error).message).toBe(
      "The API could not be read for get_area: timeout, after 4 tries.",
    );
    expect(calls.waited).toEqual([10_000, 20_000, 40_000, 80_000]);
  });

  test("test_a_busy_service_that_stays_busy_stops_the_build_and_says_which_read_failed", async () => {
    const calls = answerInTurn([busy]);

    const failure = await ended(loadMeta());

    expect(failure).toBeInstanceOf(BuildReadError);
    expect((failure as Error).message).toBe(
      "The API could not be read for get_meta: unreadable, after 4 tries.",
    );
    expect(calls.asked).toHaveLength(4);
  });

  test("test_what_the_api_refused_is_asked_for_once", async () => {
    // A refusal is an answer. Asking again would bring the same one, later.
    const calls = answerInTurn([() => responseFrom(recordedError("error-internal"))]);

    const failure = await ended(loadMeta());

    expect((failure as Error).message).toBe("The API could not be read for get_meta: internal_error.");
    expect(calls.asked).toHaveLength(1);
  });

  test("test_an_area_the_api_does_not_have_is_asked_for_once", async () => {
    const calls = answerInTurn([() => responseFrom(recordedError("area-not-found"))]);

    expect(await ended(loadArea("alderwick"))).toBeNull();
    expect(calls.asked).toHaveLength(1);
  });

  test("test_outlines_that_came_at_the_second_try_are_kept_as_any_are", async () => {
    const calls = answerInTurn([busy, () => responseFrom(recordedAnswer("get_geometry", "geometry"))]);

    const first = await ended(loadGeometry());
    const again = await ended(loadGeometry());

    expect(outlinesOf(first)).toBe(24);
    expect(outlinesOf(again)).toBe(24);
    expect(calls.asked).toHaveLength(2);
  });

  test("test_a_persons_browser_waits_as_long_as_it_did", () => {
    // What is tried again is a read made while building. The waits of the browser's client
    // are the routes' own, and a build that waits longer leaves them as they were.
    expect(ROUTES.get_area.timeoutMs).toBe(10_000);
    expect(ROUTES.get_geometry.timeoutMs).toBe(10_000);
    expect(ROUTES.list_areas.timeoutMs).toBe(10_000);
    expect(ROUTES.get_meta.timeoutMs).toBe(10_000);
  });
});
