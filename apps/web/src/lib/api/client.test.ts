import { createClient } from "./client";
import { isApiFailure } from "./failure";
import { recordedAnswer, recordedError, responseFrom } from "./recorded";
import { send } from "./send";
import { forgetWhatWasSaid, whatWasSaid, type Said } from "./said";
import { forgetSynthetic, syntheticSeen } from "./synthetic";

const BASE = "https://api.example.test";
// A string found nowhere else, planted in everything a person could type.
const CANARY = "zqxcanary7431";

type Call = { url: string; init: RequestInit };

/** A `fetch` that answers with what it is given, and keeps what it was asked. */
function standIn(answer: Response | Error | (() => Promise<Response>)) {
  const calls: Call[] = [];
  const fetch = jest.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    if (typeof answer === "function") return answer();
    if (answer instanceof Error) throw answer;
    return answer;
  }) as unknown as typeof globalThis.fetch;
  return { fetch, calls };
}

/** A `fetch` that never answers, and gives up when it is told to stop. */
function neverAnswers() {
  const calls: Call[] = [];
  const fetch = ((url: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return new Promise<Response>((_, reject) => {
      init?.signal?.addEventListener("abort", () => reject(new DOMException("stopped", "AbortError")));
    });
  }) as typeof globalThis.fetch;
  return { fetch, calls };
}

function json(body: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...headers },
  });
}

const META = { release_id: "syn-2026-09-23-01", engine_version: "1.1.0", synthetic: true, preview: false };

function setOnline(online: boolean) {
  Object.defineProperty(window.navigator, "onLine", { configurable: true, get: () => online });
}

beforeEach(() => {
  forgetSynthetic();
  forgetWhatWasSaid();
  setOnline(true);
});

afterEach(() => {
  jest.useRealTimers();
  delete process.env.NEXT_PUBLIC_BURRO_API_URL;
});

describe("the API client", () => {
  test("test_an_answer_comes_back_as_meta_and_data", async () => {
    const recorded = recordedAnswer("rank", "rank-first");
    const { fetch, calls } = standIn(responseFrom(recorded));

    const answer = await createClient({ baseUrl: BASE, fetch }).rank({
      spec: recorded.body.data.spec,
      limit: 20,
    });

    expect(answer.ok).toBe(true);
    if (!answer.ok) return;
    expect(answer.meta).toEqual(recorded.body.meta);
    expect(answer.data).toEqual(recorded.body.data);
    expect(answer.requestId).toBe(recorded.headers["x-request-id"]);
    expect(calls).toHaveLength(1);
    expect(calls[0]?.url).toBe(`${BASE}/v1/rank`);
    expect(calls[0]?.init.method).toBe("POST");
  });

  test("test_an_error_envelope_becomes_a_typed_failure_with_its_code_and_paths", async () => {
    const recorded = recordedError("rank-stale-spec");
    const { fetch } = standIn(responseFrom(recorded));

    const answer = await createClient({ baseUrl: BASE, fetch }).rank({
      spec: recordedAnswer("rank", "rank-first").body.data.spec,
      limit: 20,
    });

    expect(answer.ok).toBe(false);
    if (answer.ok || !isApiFailure(answer.failure)) throw new Error("not the API's own failure");
    expect(answer.failure).toEqual({
      kind: "api",
      status: 422,
      code: "unknown_place",
      message: recorded.body.error.message,
      fields: [{ path: "spec.commutes[1].place_id", problem: "unknown_place" }],
      meta: recorded.body.meta,
      synthetic: true,
      requestId: recorded.headers["x-request-id"],
    });
  });

  test.each([
    ["a field that is not a record", ["spec.budget"]],
    ["a field that is nothing", [null]],
    ["a field with no path", [{ problem: "unknown_place" }]],
    ["a field whose path is a number", [{ path: 7, problem: "unknown_place" }]],
    ["a field with no problem", [{ path: "spec.budget" }]],
    ["a field whose problem is a record", [{ path: "spec.budget", problem: { code: "x" } }]],
    ["more fields than any refusal could hold", Array.from({ length: 201 }, () => ({ path: "spec", problem: "x" }))],
  ])("test_an_error_whose_fields_are_not_what_the_contract_says_is_unreadable: %s", async (_, fields) => {
    const recorded = recordedError("rank-stale-spec");
    const error = { ...recorded.body.error, fields };
    const { fetch } = standIn(json({ meta: recorded.body.meta, error }, 422));

    const answer = await createClient({ baseUrl: BASE, fetch }).getMeta();

    // Let through, a field with no path would stop the page where its path is first read.
    expect(answer).toMatchObject({ ok: false, failure: { kind: "unreadable", status: 422, synthetic: true } });
  });

  test("test_an_error_that_cannot_be_read_is_not_passed_over_for_the_data_beside_it", async () => {
    const recorded = recordedAnswer("rank", "rank-first");
    const error = { code: "invalid_spec", message: "refused", fields: [{ path: 7 }] };
    const { fetch } = standIn(json({ ...recorded.body, error }));

    const answer = await createClient({ baseUrl: BASE, fetch }).rank({ spec: recorded.body.data.spec, limit: 20 });

    expect(answer).toMatchObject({ ok: false, failure: { kind: "unreadable", status: 200 } });
  });

  test("test_an_error_is_handed_on_as_a_new_record_that_holds_only_what_the_contract_names", async () => {
    const recorded = recordedError("rank-stale-spec");
    const error = {
      ...recorded.body.error,
      surprise: CANARY,
      fields: [{ path: "spec.commutes[1].place_id", problem: "unknown_place", surprise: CANARY }],
    };
    const { fetch } = standIn(json({ meta: recorded.body.meta, error }, 422));

    const answer = await createClient({ baseUrl: BASE, fetch }).getMeta();

    if (answer.ok || !isApiFailure(answer.failure)) throw new Error("not the API's own failure");
    expect(answer.failure.fields).toEqual([{ path: "spec.commutes[1].place_id", problem: "unknown_place" }]);
    expect(JSON.stringify(answer.failure).includes(CANARY)).toBe(false);
  });

  test.each([
    ["area-not-found", 404, "area_not_found"],
    ["share-not-found", 404, "share_not_found"],
    ["share-gone", 410, "release_changed"],
    ["interpret-invalid-text", 422, "invalid_text"],
    ["error-internal", 500, "internal_error"],
    ["not-found", 404, "not_found"],
  ] as const)(
    "test_every_kind_of_refusal_is_told_apart_by_its_code: %s",
    async (scenario, status, code) => {
      const { fetch } = standIn(responseFrom(recordedError(scenario)));

      const answer = await createClient({ baseUrl: BASE, fetch }).getMeta();

      expect(answer.ok).toBe(false);
      if (answer.ok) return;
      expect([answer.failure.kind, answer.failure.status]).toEqual(["api", status]);
      expect(isApiFailure(answer.failure) && answer.failure.code).toBe(code);
      expect(answer.failure.requestId).toMatch(/^[0-9a-f-]{36}$/);
    },
  );

  test("test_a_call_that_takes_too_long_is_stopped_and_called_a_timeout", async () => {
    jest.useFakeTimers();
    const { fetch, calls } = neverAnswers();

    const waiting = createClient({ baseUrl: BASE, fetch }).interpret({ text: "leafy", ask_model: true });
    // Reading a sentence is given 8 seconds, and no longer.
    await jest.advanceTimersByTimeAsync(7_999);
    expect(calls[0]?.init.signal?.aborted).toBe(false);
    await jest.advanceTimersByTimeAsync(1);

    expect(await waiting).toEqual({
      ok: false,
      failure: { kind: "timeout", status: null, synthetic: null, requestId: null },
    });
    expect(calls[0]?.init.signal?.aborted).toBe(true);
  });

  test.each([
    ["search_places", 3_000],
    ["rank", 5_000],
    ["explain_top", 5_000],
    ["compare", 5_000],
    ["create_share", 5_000],
    ["get_share", 5_000],
    ["get_meta", 10_000],
    ["get_area", 10_000],
  ] as const)("test_each_route_waits_as_long_as_the_design_says: %s", async (operation, wait) => {
    jest.useFakeTimers();
    const { fetch } = neverAnswers();
    let settled = false;

    const waiting = send(operation, { baseUrl: BASE, fetch }, { body: {}, parameter: "x" }).then(
      (answer) => {
        settled = true;
        return answer;
      },
    );
    await jest.advanceTimersByTimeAsync(wait - 1);
    expect(settled).toBe(false);
    await jest.advanceTimersByTimeAsync(1);

    expect(await waiting).toMatchObject({ ok: false, failure: { kind: "timeout" } });
  });

  test("test_a_call_the_person_stops_is_called_aborted_and_not_a_timeout", async () => {
    const { fetch, calls } = neverAnswers();
    const stop = new AbortController();

    const waiting = createClient({ baseUrl: BASE, fetch }).interpret({ text: "leafy", ask_model: true }, stop.signal);
    stop.abort();

    expect(await waiting).toMatchObject({ ok: false, failure: { kind: "aborted" } });
    expect(calls[0]?.init.signal?.aborted).toBe(true);
  });

  test("test_a_call_that_was_stopped_before_it_began_sends_nothing", async () => {
    const { fetch, calls } = standIn(json({ meta: META, data: {} }));
    const stop = new AbortController();
    stop.abort();

    const answer = await createClient({ baseUrl: BASE, fetch }).interpret(
      { text: CANARY, ask_model: true },
      stop.signal,
    );

    expect(answer).toMatchObject({ ok: false, failure: { kind: "aborted" } });
    expect(calls).toHaveLength(0);
  });

  test("test_a_request_that_cannot_leave_is_a_network_failure_and_never_thrown", async () => {
    const { fetch } = standIn(new TypeError(`could not send ${CANARY}`));

    const answer = await createClient({ baseUrl: BASE, fetch }).interpret({ text: CANARY, ask_model: true });

    expect(answer).toEqual({
      ok: false,
      failure: { kind: "network", status: null, synthetic: null, requestId: null },
    });
    expect(JSON.stringify(answer)).not.toContain(CANARY);
  });

  test("test_with_no_connection_nothing_is_sent_and_the_failure_says_offline", async () => {
    setOnline(false);
    const { fetch, calls } = standIn(json({ meta: META, data: {} }));

    const answer = await createClient({ baseUrl: BASE, fetch }).rank({
      spec: recordedAnswer("rank", "rank-first").body.data.spec,
      limit: 20,
    });

    expect(answer).toMatchObject({ ok: false, failure: { kind: "offline" } });
    expect(calls).toHaveLength(0);
  });

  test.each([
    ["not JSON at all", new Response("<html>Bad gateway</html>", { status: 502 })],
    ["JSON that is no envelope", json({ detail: "Not Found" }, 404)],
    ["an envelope with no meta", json({ data: { areas: [] } })],
    ["meta with no flag", json({ meta: { ...META, synthetic: undefined }, data: {} })],
    ["meta that does not say whether it is a preview", json({ meta: { ...META, preview: undefined }, data: {} })],
    ["a 200 with no data", json({ meta: META })],
    ["a 500 that holds data", json({ meta: META, data: {} }, 500)],
  ])("test_an_answer_that_is_not_the_apis_envelope_is_unreadable: %s", async (_, response) => {
    const { fetch } = standIn(response);

    const answer = await createClient({ baseUrl: BASE, fetch }).listAreas();

    expect(answer).toMatchObject({ ok: false, failure: { kind: "unreadable" } });
    expect(!answer.ok && answer.failure.status).toBe(response.status);
  });

  test.each(["ranked", "scores", "spec", "spec_hash", "filtered", "unranked", "applied", "rejected", "empty_spec"])(
    "test_an_answer_that_lacks_what_the_contract_requires_of_it_is_unreadable: %s",
    async (field) => {
      const recorded = recordedAnswer("rank", "rank-first");
      const data: Record<string, unknown> = { ...recorded.body.data };
      delete data[field];
      const { fetch } = standIn(json({ meta: recorded.body.meta, data }));

      const answer = await createClient({ baseUrl: BASE, fetch }).rank({ spec: recorded.body.data.spec, limit: 20 });

      // Left to be read, it would stop the page where the field is first looked for.
      expect(answer).toMatchObject({ ok: false, failure: { kind: "unreadable", status: 200, synthetic: true } });
    },
  );

  test("test_an_answer_with_nothing_in_it_is_unreadable_for_every_route", async () => {
    const { fetch } = standIn(async () => json({ meta: META, data: {} }));
    const client = createClient({ baseUrl: BASE, fetch });
    const spec = recordedAnswer("rank", "rank-first").body.data.spec;

    const answers = await Promise.all([
      client.interpret({ text: "leafy", ask_model: true }),
      client.rank({ spec, limit: 20 }),
      client.explainTop({ spec, limit: 5 }),
      client.compare({ area_ids: ["syn-n0001", "syn-n0002"], spec }),
      client.searchPlaces({ q: "pel", limit: 8 }),
      client.createShare({ spec, exact_destinations: false }),
      client.getShare("AAAAAAAAAAAAAAAAAAAAAA"),
      client.listAreas(),
      client.getGeometry(),
      client.getArea("alderwick"),
      client.getMeta(),
    ]);

    expect(answers.map((answer) => !answer.ok && answer.failure.kind)).toEqual(answers.map(() => "unreadable"));
  });

  test("test_a_field_the_website_does_not_know_is_let_through_and_breaks_nothing", async () => {
    const recorded = recordedAnswer("rank", "rank-first");
    const { fetch } = standIn(
      json({
        meta: { ...recorded.body.meta, region: "north" },
        data: { ...recorded.body.data, new_thing: { a: 1 } },
        also: "this",
      }),
    );

    const answer = await createClient({ baseUrl: BASE, fetch }).rank({ spec: recorded.body.data.spec, limit: 20 });

    expect(answer.ok).toBe(true);
    expect(answer.ok && answer.data.ranked).toEqual(recorded.body.data.ranked);
  });
});

describe("the synthetic flag", () => {
  test.each([
    ["body and header agree", true, "true", true],
    ["only the body says so", true, "false", true],
    ["only the header says so", false, "true", true],
    ["the header is missing", true, null, true],
    ["neither says so", false, "false", false],
    ["the body says not and the header is missing", false, null, false],
  ] as const)(
    "test_made_up_data_is_never_shown_as_real: %s",
    async (_, inBody, inHeader, expected) => {
      const headers: Record<string, string> =
        inHeader === null ? {} : { "x-burro-synthetic": inHeader };
      const { fetch } = standIn(
        json({ meta: { ...META, synthetic: inBody }, data: { areas: [], bands: [] } }, 200, headers),
      );

      const answer = await createClient({ baseUrl: BASE, fetch }).listAreas();

      expect(answer.ok && answer.synthetic).toBe(expected);
    },
  );

  test("test_the_flag_is_read_from_an_error_as_from_any_answer", async () => {
    const { fetch } = standIn(responseFrom(recordedError("error-internal")));

    const answer = await createClient({ baseUrl: BASE, fetch }).explainTop({
      spec: recordedAnswer("rank", "rank-first").body.data.spec,
      limit: 5,
    });

    expect(!answer.ok && answer.failure.synthetic).toBe(true);
  });

  test("test_the_flag_is_read_from_the_header_when_the_body_cannot_be_read", async () => {
    const { fetch } = standIn(
      new Response("not json", { status: 502, headers: { "x-burro-synthetic": "true" } }),
    );

    const answer = await createClient({ baseUrl: BASE, fetch }).getMeta();

    expect(answer).toMatchObject({ ok: false, failure: { kind: "unreadable", synthetic: true } });
  });

  test("test_every_answer_is_heard_by_whoever_shows_the_banner", async () => {
    const heard: boolean[] = [];
    const onSynthetic = (synthetic: boolean) => heard.push(synthetic);
    const real = json({ meta: { ...META, synthetic: false }, data: { areas: [] } }, 200, {
      "x-burro-synthetic": "false",
    });

    await createClient({
      baseUrl: BASE,
      fetch: standIn(real).fetch,
      onSynthetic,
    }).listAreas();
    await createClient({
      baseUrl: BASE,
      fetch: standIn(responseFrom(recordedError("share-gone"))).fetch,
      onSynthetic,
    }).getShare("AAAAAAAAAAAAAAAAAAAAAA");

    expect(heard).toEqual([false, true]);
  });

  test("test_what_each_answer_says_of_its_data_is_heard_whatever_became_of_the_answer", async () => {
    const heard: Said[] = [];
    const onSaid = (said: Said) => heard.push(said);
    const preview = json({ meta: { ...META, synthetic: false, preview: true }, data: { areas: [] } });
    const unreadable = new Response("not json", {
      status: 502,
      headers: { "x-burro-synthetic": "false", "x-burro-preview": "true" },
    });
    const silent = new Response("not json", { status: 502 });

    await createClient({ baseUrl: BASE, fetch: standIn(preview).fetch, onSaid }).listAreas();
    await createClient({
      baseUrl: BASE,
      fetch: standIn(responseFrom(recordedError("share-gone"))).fetch,
      onSaid,
    }).getShare("AAAAAAAAAAAAAAAAAAAAAA");
    await createClient({ baseUrl: BASE, fetch: standIn(unreadable).fetch, onSaid }).getMeta();
    await createClient({ baseUrl: BASE, fetch: standIn(silent).fetch, onSaid }).getMeta();

    expect(heard).toEqual([
      { synthetic: false, preview: true },
      { synthetic: true, preview: false },
      { synthetic: false, preview: true },
      { synthetic: null, preview: null },
    ]);
  });

  test("test_a_preview_is_heard_when_the_body_or_the_header_says_so", async () => {
    const heard: Said[] = [];
    const body = json({ meta: { ...META, preview: false }, data: { areas: [] } }, 200, {
      "x-burro-preview": "true",
    });

    await createClient({ baseUrl: BASE, fetch: standIn(body).fetch, onSaid: (said) => heard.push(said) }).listAreas();

    // An unfinished release is never shown as a finished one.
    expect(heard).toEqual([{ synthetic: true, preview: true }]);
  });

  test("test_the_websites_own_client_hears_what_every_answer_says", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = BASE;
    const { api } = await import("./client");
    expect(whatWasSaid()).toEqual({ madeUp: false, real: false, preview: false, finished: false });

    globalThis.fetch = standIn(
      json({ meta: { ...META, synthetic: false, preview: true }, data: { areas: [] } }),
    ).fetch;
    await api.listAreas();

    expect(whatWasSaid()).toEqual({ madeUp: false, real: true, preview: true, finished: false });
  });

  test("test_the_websites_own_client_turns_the_banner_on_and_never_off", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = BASE;
    const { api } = await import("./client");
    const real = () =>
      json({ meta: { ...META, synthetic: false }, data: { areas: [] } }, 200, {
        "x-burro-synthetic": "false",
      });

    globalThis.fetch = standIn(real()).fetch;
    await api.listAreas();
    expect(syntheticSeen()).toBe(false);

    globalThis.fetch = standIn(responseFrom(recordedAnswer("list_areas", "areas"))).fetch;
    await api.listAreas();
    expect(syntheticSeen()).toBe(true);

    globalThis.fetch = standIn(real()).fetch;
    await api.listAreas();
    expect(syntheticSeen()).toBe(true);
  });
});

describe("what the client sends, and where", () => {
  test("test_typed_text_travels_only_in_a_post_body", async () => {
    const { fetch, calls } = standIn(() =>
      Promise.resolve(responseFrom(recordedAnswer("interpret", "interpret-first"))),
    );
    const client = createClient({ baseUrl: BASE, fetch });

    await client.interpret({ text: `leafy, near ${CANARY}`, ask_model: true });
    await client.searchPlaces({ q: CANARY, limit: 8 });

    expect(calls).toHaveLength(2);
    for (const { url, init } of calls) {
      expect(url).not.toContain(CANARY);
      expect(JSON.stringify(init.headers)).not.toContain(CANARY);
      expect(init.method).toBe("POST");
      expect(String(init.body)).toContain(CANARY);
    }
  });

  test("test_a_post_is_never_kept_by_the_browser_and_carries_no_cookie_or_referrer", async () => {
    const { fetch, calls } = standIn(responseFrom(recordedAnswer("rank", "rank-first")));

    await createClient({ baseUrl: BASE, fetch }).rank({
      spec: recordedAnswer("rank", "rank-first").body.data.spec,
      limit: 20,
    });

    expect(calls[0]?.init).toMatchObject({
      cache: "no-store",
      credentials: "omit",
      referrerPolicy: "no-referrer",
      redirect: "error",
    });
  });

  test("test_an_id_in_a_path_cannot_reach_another_route", async () => {
    const { fetch, calls } = standIn(() =>
      Promise.resolve(responseFrom(recordedError("area-not-found"))),
    );
    const client = createClient({ baseUrl: BASE, fetch });

    await client.getArea("../meta?x=1#y");
    await client.getShare("a/b");

    expect(calls.map(({ url }) => url)).toEqual([
      `${BASE}/v1/areas/..%2Fmeta%3Fx%3D1%23y`,
      `${BASE}/v1/shares/a%2Fb`,
    ]);
  });

  test("test_the_client_never_writes_to_the_console_or_to_storage", async () => {
    const written: unknown[][] = [];
    for (const method of ["log", "info", "warn", "error", "debug", "trace"] as const) {
      jest.spyOn(console, method).mockImplementation((...args) => void written.push(args));
    }
    const stored = jest.spyOn(Storage.prototype, "setItem");
    const spec = recordedAnswer("rank", "rank-first").body.data.spec;
    const answers = [
      responseFrom(recordedAnswer("interpret", "interpret-first")),
      responseFrom(recordedError("error-internal")),
      responseFrom(recordedError("interpret-invalid-text")),
      new Response(`<html>${CANARY}</html>`, { status: 502 }),
      new TypeError(CANARY),
    ];

    for (const answer of answers) {
      const client = createClient({ baseUrl: BASE, fetch: standIn(answer).fetch });
      await client.interpret({ text: CANARY, spec, ask_model: true });
      await client.searchPlaces({ q: CANARY, limit: 8 });
    }

    expect(written).toEqual([]);
    expect(stored).not.toHaveBeenCalled();
    expect(document.cookie).toBe("");
  });
});

describe("where the API is", () => {
  test("test_the_address_comes_from_one_environment_variable", async () => {
    process.env.NEXT_PUBLIC_BURRO_API_URL = "https://api.burro.example/";
    const { fetch, calls } = standIn(responseFrom(recordedAnswer("get_meta", "meta")));

    const answer = await createClient({ fetch }).getMeta();

    expect(answer.ok).toBe(true);
    expect(calls[0]?.url).toBe("https://api.burro.example/v1/meta");
  });

  test("test_with_no_address_set_nothing_is_sent", async () => {
    const { fetch, calls } = standIn(responseFrom(recordedAnswer("get_meta", "meta")));

    const answer = await createClient({ fetch }).interpret({ text: CANARY, ask_model: true });

    expect(answer).toEqual({
      ok: false,
      failure: { kind: "not_configured", status: null, synthetic: null, requestId: null },
    });
    expect(calls).toHaveLength(0);
  });
});
