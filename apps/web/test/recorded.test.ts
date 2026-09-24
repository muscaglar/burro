/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import Ajv2020 from "ajv/dist/2020";

import { ROUTES } from "@/lib/api/operations";
import { readRecorded, recordedFolder, type Recorded } from "@/lib/api/recorded";

const FOLDER = recordedFolder();
const CONTRACT_FILE = path.resolve(__dirname, "..", "..", "..", "contracts", "openapi.json");

interface Contract {
  readonly paths: Record<
    string,
    Record<
      string,
      {
        readonly operationId: string;
        readonly requestBody?: { content: { "application/json": { schema: object } } };
        readonly responses: Record<string, { content?: { "application/json": { schema: object } } }>;
      }
    >
  >;
  readonly components: { readonly schemas: Record<string, object> };
}

const contract = JSON.parse(readFileSync(CONTRACT_FILE, "utf8")) as Contract;

function scenariosOnDisk(folder = FOLDER, prefix = ""): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    if (entry.isDirectory()) {
      return scenariosOnDisk(path.join(folder, entry.name), `${prefix}${entry.name}/`);
    }
    if (!entry.name.endsWith(".json") || entry.name === "index.json") return [];
    return [`${prefix}${entry.name.slice(0, -".json".length)}`];
  });
}

const scenarios = scenariosOnDisk().sort();
const recordings: readonly Recorded[] = scenarios.map(readRecorded);

// The contract is one document, and every schema in it points at another by
// its place in that document. It is given to the validator whole.
const ajv = new Ajv2020({ strict: false, allErrors: true, validateFormats: false });
ajv.addSchema(contract, "contract");

function operationOf(id: string) {
  for (const [route, methods] of Object.entries(contract.paths)) {
    for (const [method, operation] of Object.entries(methods)) {
      if (operation.operationId === id) return { route, method: method.toUpperCase(), operation };
    }
  }
  throw new Error(`The contract has no operation ${id}.`);
}

function pointer(...parts: string[]): string {
  return `contract#/${parts.map((part) => part.replace(/~/g, "~0").replace(/\//g, "~1")).join("/")}`;
}

function problemsWith(schemaAt: string, value: unknown): string[] {
  const validate = ajv.getSchema(schemaAt);
  if (!validate) return [`no schema at ${schemaAt}`];
  validate(value);
  // Where and what kind, and never the value: a failure prints no place.
  return (validate.errors ?? []).map((error) => `${error.instancePath} ${error.keyword}`);
}

describe("the recorded answers", () => {
  test("test_there_is_a_recorded_answer_for_every_route_of_the_contract", () => {
    const recorded = new Set(recordings.map((recording) => recording.request.operation_id));
    const inContract = Object.values(contract.paths).flatMap((methods) =>
      Object.values(methods).map((operation) => operation.operationId),
    );

    expect(inContract.filter((id) => !recorded.has(id as never))).toEqual([]);
    // And the client calls every route but the one that says the service is up.
    expect(Object.keys(ROUTES).sort()).toEqual(inContract.filter((id) => id !== "healthz").sort());
  });

  test("test_every_state_the_search_page_has_is_recorded", () => {
    // The scenarios docs/design/web.md, section 11, asks for.
    const needed = [
      "meta",
      "areas",
      "geometry",
      "area",
      "area-not-found",
      "interpret-first",
      "interpret-clarify",
      "interpret-notice",
      "interpret-nothing-read",
      "interpret-degraded",
      "interpret-rejected",
      "interpret-unmet",
      "rank-first",
      "rank-refined",
      "rank-nothing-matches",
      "rank-stale-spec",
      "explanations-first",
      "compare-three",
      "places-search",
      "share-made",
      "share-opened",
      "share-not-found",
      "share-gone",
      "error-internal",
    ];

    expect(needed.filter((scenario) => !scenarios.includes(scenario))).toEqual([]);
  });

  test("test_every_area_of_the_release_has_a_recorded_profile", () => {
    const areas = readRecorded("areas").body as { data: { areas: { slug: string }[] } };

    const missing = areas.data.areas.filter(({ slug }) => !scenarios.includes(`area/${slug}`));

    expect(missing).toEqual([]);
  });

  test("test_the_index_lists_exactly_the_recordings_that_are_there", () => {
    const index = JSON.parse(readFileSync(path.join(FOLDER, "index.json"), "utf8")) as {
      scenarios: { scenario: string; operation_id: string | null; status: number }[];
    };

    expect(index.scenarios.map((entry) => entry.scenario).sort()).toEqual(scenarios);
    for (const entry of index.scenarios) {
      const recording = readRecorded(entry.scenario);
      expect([entry.scenario, entry.operation_id, entry.status]).toEqual([
        recording.scenario,
        recording.request.operation_id,
        recording.status,
      ]);
    }
  });

  test("test_every_recording_was_captured_from_the_api_and_none_was_made_by_hand", () => {
    expect(recordings.filter((recording) => recording.captured !== true)).toEqual([]);
  });

  test.each(scenarios)("test_a_recorded_answer_fits_the_contract: %s", (scenario) => {
    const recording = readRecorded(scenario);
    const id = recording.request.operation_id;
    if (id === null) {
      // A path that is no route is answered in the error envelope all the same.
      expect(problemsWith(pointer("components", "schemas", "ErrorEnvelope"), recording.body)).toEqual(
        [],
      );
      return;
    }
    const { route, method, operation } = operationOf(id);

    expect([recording.request.method, recording.request.route]).toEqual([method, route]);
    expect(Object.keys(operation.responses)).toContain(String(recording.status));
    expect(
      problemsWith(
        pointer(
          "paths",
          route,
          method.toLowerCase(),
          "responses",
          String(recording.status),
          "content",
          "application/json",
          "schema",
        ),
        recording.body,
      ),
    ).toEqual([]);
  });

  test.each(scenarios)("test_a_recorded_request_fits_the_contract: %s", (scenario) => {
    const recording = readRecorded(scenario);
    const id = recording.request.operation_id;
    if (id === null || recording.request.method !== "POST") return;
    // A request recorded to show a refusal is meant not to fit.
    if (recording.status === 422 || recording.status === 400) return;
    const { route, method } = operationOf(id);

    expect(
      problemsWith(
        pointer(
          "paths",
          route,
          method.toLowerCase(),
          "requestBody",
          "content",
          "application/json",
          "schema",
        ),
        recording.request.body,
      ),
    ).toEqual([]);
  });

  test("test_an_answer_that_does_not_fit_the_contract_is_caught", () => {
    // If the validator passed everything, every test above would pass too.
    const schemaAt = pointer(
      "paths",
      "/v1/rank",
      "post",
      "responses",
      "200",
      "content",
      "application/json",
      "schema",
    );
    const good = readRecorded("rank-first").body as {
      meta: object;
      data: { ranked: { score: number }[]; scores: object[] };
    };
    const first = good.data.ranked[0];
    const without = { meta: good.meta, data: { ...good.data, scores: undefined } };
    const withMore = { meta: good.meta, data: { ...good.data, invented: true } };
    const wrongType = {
      meta: good.meta,
      data: { ...good.data, ranked: [{ ...first, score: "high" }] },
    };
    const noFlag = { meta: { ...good.meta, synthetic: undefined }, data: good.data };

    expect(problemsWith(schemaAt, good)).toEqual([]);
    expect(problemsWith(schemaAt, without)).toEqual(["/data required"]);
    expect(problemsWith(schemaAt, withMore)).toEqual(["/data additionalProperties"]);
    expect(problemsWith(schemaAt, wrongType)).toEqual(["/data/ranked/0/score type"]);
    expect(problemsWith(schemaAt, noFlag)).toEqual(["/meta required"]);
  });

  test("test_every_recorded_answer_says_the_data_is_made_up", () => {
    const silent = recordings.filter((recording) => {
      const body = recording.body as { meta?: { synthetic?: boolean } };
      const inBody = recording.request.operation_id === "healthz" || body.meta?.synthetic === true;
      return recording.headers["x-burro-synthetic"] !== "true" || !inBody;
    });

    expect(silent.map((recording) => recording.scenario)).toEqual([]);
  });

  test("test_no_recorded_error_repeats_what_was_sent", () => {
    // An error holds a code, fixed words, and paths into the body. A canary
    // cannot be planted in a recording, so what is checked is that no string
    // of the request is found in the answer to it.
    const strings = (value: unknown): string[] => {
      if (typeof value === "string") return value.length >= 12 ? [value] : [];
      if (Array.isArray(value)) return value.flatMap(strings);
      if (typeof value === "object" && value !== null) return Object.values(value).flatMap(strings);
      return [];
    };
    const echoes = recordings
      .filter((recording) => recording.status >= 400)
      .filter((recording) => {
        const answer = JSON.stringify(recording.body);
        return strings(recording.request.body).some((sent) => answer.includes(sent));
      });

    expect(echoes.map((recording) => recording.scenario)).toEqual([]);
  });

  test("test_a_name_that_could_climb_out_of_the_folder_is_no_scenario", () => {
    for (const name of ["../package", "area/../../package", "/etc/hosts", "meta.json", "Meta", ""]) {
      expect(() => readRecorded(name)).toThrow("There is no recorded answer");
    }
  });
});
