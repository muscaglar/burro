/**
 * What the search page shows, and the words it uses, as a person who has
 * never seen it finds them. docs/design/web.md, sections 4 and 5.2.
 *
 * Two of the tests below are marked as failing. Each says what the page is to
 * show once the API gives what section 13 of the design asks of it, and fails
 * today. A test marked so passes while it fails, and fails the day it passes:
 * that day, take the mark off, and take out what the website did in the
 * meantime. Beside each is a test of what the page does until then, so that
 * the marked one cannot fail for a reason of its own.
 */

import { readdirSync } from "node:fs";

import { screen, within } from "@testing-library/react";

import { COMBINE } from "@/content/labels";
import { MAP } from "@/content/map";
import { CHIPS, JOURNEYS, PLACE, RESULTS } from "@/content/search";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { ExplanationsData, RankData } from "@/lib/api/schema";

import { standInApi, type Responder } from "../support/api";
import { openSearch, results, search, settled } from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", scenario).request.body as { text: string }).text;

/** A household with two places to reach, as it was recorded: the sentence, its ranking and its reasons. */
const twoJourneys = () =>
  standInApi()
    .on("interpret", "interpret-two-journeys")
    .on("rank", "rank-two-journeys")
    .on("explain_top", "explanations-two-journeys");

async function searchedForTwoPlaces() {
  const opened = await openSearch(twoJourneys());
  await search(opened.user, sentenceOf("interpret-two-journeys"));
  await settled();
  return opened;
}

/** Everything on the page that is a place shown by number, because its name is not in hand. */
const shownByNumber = () =>
  [...document.querySelectorAll("main li, main th, main legend, main button")]
    .map((element) => element.textContent ?? "")
    .filter((text) => /\bPlace \d+\b/.test(text));

/** The part of a result under the word "Trade-off". */
const tradeOff = (result: HTMLElement) =>
  within(result).getByRole("heading", { name: RESULTS.tradeOffTitle }).parentElement as HTMLElement;

describe("a place the person named", () => {
  test("test_a_place_with_no_name_in_hand_is_shown_by_number_and_the_page_says_why", async () => {
    await searchedForTwoPlaces();
    const chips = within(screen.getByRole("region", { name: CHIPS.label }));

    // The reading names both places by id. The one name in hand is from the one journey a sentence cites.
    expect(chips.getByRole("button", { name: /^Wexmoor University/ })).toBeInTheDocument();
    expect(chips.getByRole("button", { name: new RegExp(`^${PLACE.unnamed(1)}`) })).toBeInTheDocument();
    expect(chips.getByText(PLACE.unnamedHint(1, 2))).toBeInTheDocument();
    expect(shownByNumber().length).toBeGreaterThan(0);
  });

  // Waits on docs/design/web.md, section 13, gap 1: the names of the spec's places, in the
  // answers of routes 1, 2 and 10. When it passes, delete `PLACE.unnamed` and its hint.
  test.failing("test_no_place_the_person_named_is_shown_by_number", async () => {
    await searchedForTwoPlaces();

    expect(shownByNumber()).toEqual([]);
  });

  test("test_with_two_places_the_page_says_which_journey_counts_before_the_settings_are_opened", async () => {
    await searchedForTwoPlaces();
    const chips = within(screen.getByRole("region", { name: CHIPS.label }));

    expect(chips.getByRole("button", { name: new RegExp(`^${COMBINE.slowest}`) })).toHaveTextContent(CHIPS.assumed);
    expect(within(results()[0] as HTMLElement).getByText(JOURNEYS.usesOne("Wexmoor University"))).toBeInTheDocument();
  });
});

describe("what is said under the word trade-off", () => {
  /** The reasons as they were recorded, with the trade-off of the first area changed. */
  const withFirstTradeOff = (change: (data: ExplanationsData) => ExplanationsData): Responder => () => {
    const recorded = readRecorded("explanations-first");
    const body = recorded.body as { data: ExplanationsData };
    return { ...recorded, body: { ...body, data: change(body.data) } };
  };

  test("test_when_the_api_gives_no_trade_off_the_card_says_that_none_was_found", async () => {
    const none = withFirstTradeOff((data) => ({
      ...data,
      explanations: data.explanations.map((one, at) => (at === 0 ? { ...one, trade_off: null } : one)),
    }));
    const { user } = await openSearch(
      standInApi().on("interpret", "interpret-first").on("rank", "rank-first").on("explain_top", none),
    );
    await search(user);
    await settled();

    expect(tradeOff(results()[0] as HTMLElement)).toHaveTextContent(RESULTS.noTradeOff);
    expect(within(tradeOff(results()[0] as HTMLElement)).queryByRole("button")).toBeNull();
    // The next card has one, and says it in the API's words.
    const given = recordedAnswer("explain_top", "explanations-first").body.data.explanations[1]?.trade_off;
    expect(tradeOff(results()[1] as HTMLElement)).toHaveTextContent(given?.text ?? "no trade-off");
  });

  test("test_a_strength_the_api_gave_as_a_trade_off_is_not_shown_as_one", async () => {
    // As an engine before 1.3.0 answered: the least good thing, though the area does it well.
    const text = "A strength, said as an older engine would give it.";
    const strength = withFirstTradeOff((data) => ({
      ...data,
      explanations: data.explanations.map((one, at) =>
        at === 0
          ? {
              ...one,
              trade_off: {
                text,
                fact_ids: ["syn-n0006/tag/quiet_residential"],
                origin: "template" as const,
                replaced: false,
              },
            }
          : one,
      ),
    }));
    const { user } = await openSearch(
      standInApi().on("interpret", "interpret-first").on("rank", "rank-first").on("explain_top", strength),
    );
    await search(user);
    await settled();

    expect(document.body.textContent?.includes(text)).toBe(false);
    expect(tradeOff(results()[0] as HTMLElement)).toHaveTextContent(RESULTS.noTradeOff);
  });
});

describe("the side a sentence is said from", () => {
  const SEARCHES = readdirSync(recordedFolder())
    .filter((name) => /^explanations-.*\.json$/.test(name))
    .map((name) => name.slice("explanations-".length, -".json".length));

  /** The word each sentence of a kind compares by, for each thing the recordings hold a sentence about. */
  function comparedBy(kind: "reasons" | "trade_off"): Map<string, Set<string>> {
    const words = new Map<string, Set<string>>();
    for (const search of SEARCHES) {
      const { explanations, facts } = recordedAnswer("explain_top", `explanations-${search}`).body.data;
      for (const explanation of explanations) {
        const sentences = kind === "reasons" ? explanation.reasons : [explanation.trade_off];
        for (const sentence of sentences) {
          const fact = facts.find((one) => one.fact_id === sentence?.fact_ids[0]);
          const word = fact?.slots.comparative;
          if (fact === undefined || word === undefined) continue;
          words.set(`${fact.kind}:${fact.key}`, new Set([...(words.get(`${fact.kind}:${fact.key}`) ?? []), word]));
        }
      }
    }
    return words;
  }

  /** The things a reason is said of in the very word a trade-off is said of them. */
  function saidFromTheBadSide(): string[] {
    const bad = comparedBy("trade_off");
    return [...comparedBy("reasons")].flatMap(([thing, words]) =>
      [...words].filter((word) => bad.get(thing)?.has(word)).map((word) => `${thing} ${word}`),
    );
  }

  test("test_a_reason_is_shown_word_for_word_from_whichever_side_the_api_said_it", async () => {
    // Marrowfen, under "Why it fits": a walk to a park that is "further than" 47% of areas.
    const ranking: RankData = recordedAnswer("rank", "rank-buyer-family").body.data;
    const { explanations } = recordedAnswer("explain_top", "explanations-buyer-family").body.data;
    const { user } = await openSearch(
      standInApi()
        .on("interpret", "interpret-buyer-family")
        .on("rank", "rank-buyer-family")
        .on("explain_top", "explanations-buyer-family"),
    );
    await search(user, sentenceOf("interpret-buyer-family"));
    await settled();

    // The website lays the sentence out. It does not reword it, and it does not turn it round.
    ranking.ranked.slice(0, 5).forEach((area, at) => {
      for (const reason of explanations.find((one) => one.area_id === area.area_id)?.reasons ?? []) {
        expect(results()[at]?.textContent?.includes(reason.text)).toBe(true);
      }
    });
    expect(saidFromTheBadSide()).toContain("feature:park_proximity further than");
  });

  // Waits on docs/design/web.md, section 13, gap 17: a reason said from its good side. When
  // it passes, the answers have been recorded from an API that does so. Take the mark off.
  test.failing("test_no_reason_is_said_in_the_word_a_trade_off_is_said_in", () => {
    expect(comparedBy("reasons").size).toBeGreaterThan(3);
    expect(saidFromTheBadSide()).toEqual([]);
  });
});

describe("the map", () => {
  test("test_the_keys_that_move_the_map_are_not_said_where_there_is_no_map", async () => {
    // The test browser cannot draw a map, so the table stands in for it, with no keys to say.
    await openSearch();

    expect(screen.queryByText(MAP.keys)).toBeNull();
  });
});
