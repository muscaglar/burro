/**
 * What becomes of the search page when the API answers with what the website
 * did not expect: a field or a code it does not know, an answer with nothing
 * in it, markup where words should be, an area it was not built with, and a
 * release of London's size. None of it may stop the page, leave it waiting
 * for ever, or put a word such as "undefined" in front of a person.
 */

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { TABLE } from "@/content/map";
import { FAILURE, PROMPT, STATUS } from "@/content/search";
import { readRecorded, recordedAnswer, type Recorded } from "@/lib/api/recorded";

import { setOnline, standInApi, type Responder, type StandIn } from "../support/api";
import { areas, arrived, firstSearch, meta, openSearch, promptBox, results, settled, setWebGL } from "../support/search";
import { lastMap } from "../support/maplibre";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

type Data = Record<string, unknown>;
type Rows = readonly Data[];

/** A recorded answer, changed in one way, as a newer or a faulty API might send it. */
function changed(scenario: string, change: (data: Data) => Data): Responder {
  return (): Recorded => {
    const recorded = readRecorded(scenario);
    const body = recorded.body as { data: Data };
    return { ...recorded, body: { ...body, data: change(JSON.parse(JSON.stringify(body.data)) as Data) } };
  };
}

const each = (rows: unknown, change: (row: Data, at: number) => Data): Rows => (rows as Rows).map(change);

/** What a person would see that no person should: a value that was never filled in. */
function leftUnfilled(): string[] {
  const text = (document.querySelector("main")?.textContent ?? "").replace(promptBox().value, "");
  return [...text.matchAll(/undefined|\bNaN\b|\[object Object\]|\bnull\b/g)].map((found) =>
    text.slice(Math.max(0, found.index - 40), found.index + 20),
  );
}

async function searched(api: StandIn) {
  const errors = jest.spyOn(console, "error").mockImplementation(() => undefined);
  const view = await openSearch(api);
  await view.user.type(promptBox(), "leafy and quiet");
  await view.user.click(screen.getByRole("button", { name: PROMPT.submit }));
  await settled();
  return { ...view, errors };
}

beforeEach(() => setOnline(true));

describe("an answer that holds what the website does not know", () => {
  const CASES: readonly (readonly [string, (api: StandIn) => StandIn])[] = [
    [
      "a field it does not know, at every level",
      (api) =>
        api
          .on("interpret", changed("interpret-first", (data) => ({ ...data, mood: { a: 1 }, spec: { ...(data.spec as Data), colour: "blue" } })))
          .on("rank", changed("rank-first", (data) => ({ ...data, mood: [1], ranked: each(data.ranked, (area) => ({ ...area, mood: "fine" })) }))),
    ],
    ["a thing that could not be met", (api) => api.on("interpret", changed("interpret-unmet", (data) => ({ ...data, unmet: ["parking", "broadband"] })))],
    ["a reason an edit was refused", (api) => api.on("interpret", changed("interpret-rejected", (data) => ({ ...data, rejected: each(data.rejected, (one) => ({ ...one, reason: "too_vague" })) })))],
    ["a status of the reading", (api) => api.on("interpret", changed("interpret-first", (data) => ({ ...data, status: "partial" })))],
    ["a reader of the words", (api) => api.on("interpret", changed("interpret-first", (data) => ({ ...data, interpreter: "abacus" })))],
    ["a thing that was assumed", (api) => api.on("interpret", changed("interpret-first", (data) => ({ ...data, assumptions: [{ code: "season", group: "commute_ops", index: 0 }] })))],
    ["a kind of place", (api) => api.on("interpret", changed("interpret-clarify", (data) => ({ ...data, clarify: each(data.clarify, (one) => ({ ...one, options: each(one.options, (option) => ({ ...option, kind: "harbour" })) })) })))],
    ["a reason an area was left out", (api) => api.on("rank", changed("rank-refined", (data) => ({ ...data, filtered: each(data.filtered, (one) => ({ ...one, reason: "flood_zone" })) })))],
    ["a reason an area has no rank", (api) => api.on("rank", changed("rank-first", (data) => ({ ...data, unranked: each(data.unranked, (one) => ({ ...one, reason: "under_review" })) })))],
    [
      "a thing that counts",
      (api) =>
        api.on(
          "rank",
          changed("rank-first", (data) => ({
            ...data,
            ranked: each(data.ranked, (area) => ({
              ...area,
              contributions: [
                ...(area.contributions as Rows),
                { component: "weather", present: true, weight: 0.5, share: 0.1, utility: 0.5, contribution: 0.05, loss: 0.05, fact_ids: [] },
                { component: "feature:ponds", present: false, weight: 0.5, share: 0.1, utility: null, contribution: 0, loss: 0, fact_ids: [] },
              ],
            })),
          })),
        ),
    ],
    ["a state of a journey", (api) => api.on("rank", changed("rank-first", (data) => ({ ...data, ranked: each(data.ranked, (area) => ({ ...area, legs: each(area.legs, (leg) => ({ ...leg, status: "strike" })) })) })))],
    [
      "a way to travel, a kind of home, a feature and a tag in the spec",
      (api) =>
        api.on(
          "rank",
          changed("rank-first", (data) => {
            const spec = data.spec as Data;
            return {
              ...data,
              spec: {
                ...spec,
                budget: { ...(spec.budget as Data), segment: "houseboat" },
                commutes: each(spec.commutes, (one) => ({ ...one, mode: "boat" })),
                weights: [...(spec.weights as Rows), { feature_id: "ponds", weight: 0.5, direction: "more", provenance: "stated" }],
                tags: [...(spec.tags as Rows), { tag_id: "sunny", weight: 0.5, provenance: "stated" }],
              },
            };
          }),
        ),
    ],
    ["a template and a kind of fact", (api) => api.on("explain_top", changed("explanations-first", (data) => ({ ...data, facts: each(data.facts, (fact) => ({ ...fact, template: "weather_report", kind: "weather" })) })))],
    ["who wrote a sentence", (api) => api.on("explain_top", changed("explanations-first", (data) => ({ ...data, explanations: each(data.explanations, (one) => ({ ...one, reasons: each(one.reasons, (reason) => ({ ...reason, origin: "committee" })) })) })))],
    ["a sentence whose fact was not served", (api) => api.on("explain_top", changed("explanations-first", (data) => ({ ...data, facts: [] })))],
    ["no reasons and no trade-off", (api) => api.on("explain_top", changed("explanations-first", (data) => ({ ...data, explanations: each(data.explanations, (one) => ({ ...one, reasons: [], trade_off: null, missing: [] })) })))],
    ["reasons for other areas than the ranking's", (api) => api.on("explain_top", "explanations-nights-out")],
    [
      "how sure a cost is",
      (api) =>
        api.on("get_area", (call) => {
          const recorded = readRecorded(`area/${call.path.split("/").pop() ?? ""}`);
          const body = recorded.body as { data: Data };
          return { ...recorded, body: { ...body, data: { ...body.data, cost: each(body.data.cost, (one) => ({ ...one, confidence: "guess" })) } } };
        }),
    ],
    [
      "fits beyond 0 and 100",
      (api) => {
        const beyond = (row: Data, at: number) => ({ ...row, score: at === 0 ? 100.0001 : at === 1 ? -3 : row.score });
        return api.on("rank", changed("rank-first", (data) => ({ ...data, ranked: each(data.ranked, beyond), scores: each(data.scores, beyond) })));
      },
    ],
  ];

  test.each(CASES)("test_the_page_is_drawn_and_nothing_is_left_unfilled: %s", async (_, set) => {
    const { errors } = await searched(set(firstSearch()));

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(results().length).toBeGreaterThan(0);
    expect(leftUnfilled()).toEqual([]);
    expect(document.querySelectorAll("[aria-busy='true'], .skeleton")).toHaveLength(0);
    // Nothing went wrong while it was drawn.
    expect(errors.mock.calls.filter(([said]) => !String(said).includes("unique \"key\""))).toEqual([]);
  });

  test("test_a_fit_beyond_100_is_shown_as_100_and_one_below_0_as_0", async () => {
    const beyond = (row: Data, at: number) => ({ ...row, score: at === 0 ? 100.0001 : at === 1 ? -3 : row.score });
    await searched(
      firstSearch().on("rank", changed("rank-first", (data) => ({ ...data, ranked: each(data.ranked, beyond), scores: each(data.scores, beyond) }))),
    );

    expect(results()[0]).toHaveTextContent("Fit 100 of 100");
    expect(results()[1]).toHaveTextContent("Fit 0 of 100");
  });
});

describe("an answer with nothing in it", () => {
  const nothing = () => new Response(JSON.stringify({ meta: meta.meta, data: {} }), { status: 200 });

  test("test_a_ranking_with_nothing_in_it_is_said_to_be_unreadable_and_nothing_is_left_waiting", async () => {
    await searched(firstSearch().on("rank", nothing));

    expect(screen.getByRole("alert")).toHaveTextContent(FAILURE.unreadable);
    expect(within(screen.getByRole("alert")).getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();
    expect(document.querySelectorAll("[aria-busy='true'], .skeleton")).toHaveLength(0);
    expect(screen.queryByRole("button", { name: PROMPT.stop })).toBeNull();
  });

  test.each(["interpret", "explain_top", "get_area", "get_geometry"] as const)(
    "test_nothing_is_left_waiting_when_the_answer_holds_nothing: %s",
    async (operation) => {
      setWebGL(true);
      const { errors } = await searched(firstSearch().on(operation, nothing));

      expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
      expect(document.querySelectorAll("[aria-busy='true'], .skeleton")).toHaveLength(0);
      expect(screen.queryByRole("button", { name: PROMPT.stop })).toBeNull();
      expect(leftUnfilled()).toEqual([]);
      expect(errors).not.toHaveBeenCalled();
      setWebGL(false);
    },
  );

  test("test_a_ranking_of_no_area_at_all_is_said_in_words", async () => {
    await searched(
      firstSearch().on("rank", changed("rank-first", (data) => ({ ...data, ranked: [], scores: [], filtered: [], unranked: [] }))),
    );

    expect(screen.getAllByRole("status").map((line) => line.textContent)).toContain(STATUS.nothingMatches);
    expect(leftUnfilled()).toEqual([]);
  });
});

describe("words from the API", () => {
  test("test_markup_in_a_sentence_is_shown_as_the_letters_it_is_and_never_acted_on", async () => {
    const markup = "<img src=x onerror=alert(1)> <script>alert(1)</script> <b>bold</b>";
    await searched(
      firstSearch().on(
        "explain_top",
        changed("explanations-first", (data) => ({
          ...data,
          explanations: each(data.explanations, (one) => ({ ...one, reasons: each(one.reasons, (reason) => ({ ...reason, text: markup })) })),
        })),
      ),
    );

    expect(within(results()[0] as HTMLElement).getAllByText(markup).length).toBeGreaterThan(0);
    expect(document.querySelectorAll("main img, main script, main b")).toHaveLength(0);
  });

  test("test_a_notice_of_any_length_is_shown_whole", async () => {
    const long = "Burro ranks places. ".repeat(100).trim();
    await searched(firstSearch().on("interpret", changed("interpret-notice", (data) => ({ ...data, notice_text: long }))));

    expect(screen.getAllByRole("status").map((line) => line.textContent)).toContain(long);
  });
});

describe("a release of the size of London", () => {
  const HOW_MANY = 450;
  const RANKED = 430;
  const many = Array.from({ length: HOW_MANY }, (_, at) => {
    const from = areas[at % areas.length] as (typeof areas)[number];
    return { ...from, area_id: `syn-n${String(at + 1).padStart(4, "0")}`, slug: `${from.slug}-${at + 1}`, name: `${from.name} ${at + 1}` };
  });
  const geometry = recordedAnswer("get_geometry", "geometry").body.data;
  const ranking = recordedAnswer("rank", "rank-first").body.data;

  function london(): StandIn {
    return standInApi()
      .on("get_geometry", () => ({
        ...readRecorded("geometry"),
        body: {
          meta: meta.meta,
          data: {
            ...geometry,
            features: many.map((area, at) => {
              const from = geometry.features[at % geometry.features.length] as (typeof geometry.features)[number];
              return { ...from, id: area.area_id, properties: { ...from.properties, area_id: area.area_id } };
            }),
          },
        },
      }))
      .on("interpret", "interpret-first")
      .on("rank", () => ({
        ...readRecorded("rank-first"),
        body: {
          meta: meta.meta,
          data: {
            ...ranking,
            scores: many.slice(0, RANKED).map((area, at) => ({ area_id: area.area_id, score: Math.max(0, 99 - at * 0.2) })),
            ranked: ranking.ranked.map((area, at) => ({ ...area, area_id: many[at]?.area_id ?? area.area_id, rank: at + 1 })),
            unranked: many.slice(RANKED).map((area) => ({ area_id: area.area_id, reason: "not_rankable" })),
          },
        },
      }))
      .on("explain_top", changed("explanations-first", (data) => ({ ...data, explanations: [], facts: [] })))
      .on("get_area", (call) => {
        // The profile of the area that was asked for, made of one that was recorded.
        const asked = many.find((area) => area.slug === call.path.split("/").pop());
        const recorded = readRecorded("area/alderwick");
        const body = recorded.body as { data: { area: Data } };
        return { ...recorded, body: { ...body, data: { ...body.data, area: { ...body.data.area, ...asked } } } };
      });
  }

  test("test_every_area_is_in_the_table_once_and_only_the_first_ten_are_pinned", async () => {
    setWebGL(true);
    const user = userEvent.setup({ delay: null });
    const api = london();
    render(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={many} client={api.client} />
      </Shell>,
    );
    await arrived();
    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    lastMap().fire("load");
    await arrived();

    expect(results()).toHaveLength(ranking.ranked.length);
    expect(screen.getAllByRole("status").map((line) => line.textContent).join(" ")).toContain(
      STATUS.ranked(RANKED, many[0]?.name ?? ""),
    );
    for (const table of screen.getAllByRole("table", { name: TABLE.caption })) {
      const rows = within(table).getAllByRole("row").slice(1);
      expect(rows).toHaveLength(HOW_MANY);
      // In rank order, and then by name: the last ranked area, then the first with no rank.
      expect(rows[RANKED - 1]).toHaveTextContent(String(RANKED));
      expect(within(rows[RANKED] as HTMLElement).getAllByRole("cell")[0]).not.toHaveTextContent(/\d/);
    }
    expect(lastMap().markers).toHaveLength(10);
    expect(leftUnfilled()).toEqual([]);
    setWebGL(false);
  }, 60_000);
});
