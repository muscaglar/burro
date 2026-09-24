import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FACT_COLUMNS } from "@/content/facts";
import {
  BREAKDOWN,
  COMPLETENESS,
  CONFIDENCE,
  COST,
  JOURNEYS,
  PLACE,
  RESULTS,
  SOURCE,
  UNTESTED,
} from "@/content/search";
import { recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type {
  AreaData,
  ExplainedSentence,
  Explanation,
  Fact,
  RankData,
  RankedArea,
} from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { figuresNotFrom, saidBy as saidByFacts } from "../../../test/support/figures";
import { ResultList } from "./ResultList";
import { DOES_WELL_FROM } from "./tradeoff";

const STYLES = rulesOf(readFileSync(path.join(__dirname, "ResultList.module.css"), "utf8"));
/** The rules for a class that hold on a narrow screen and not on a wide one. */
const onANarrowScreen = (className: string) =>
  STYLES.filter((rule) => isFor(rule.selector, className) && /max-width:\s*(39\.99|40)rem/.test(rule.under ?? ""));

/** What an element says to a reader: its text, without what is drawn only for the eye. */
function said(element: Element | null | undefined): string {
  const copy = element?.cloneNode(true) as Element | undefined;
  copy?.querySelectorAll("[aria-hidden='true']").forEach((drawn) => drawn.remove());
  return (copy?.textContent ?? "").replace(/\s+/g, " ").trim();
}

/** A whole number out of 100, rounded down, as the page writes one. */
const floored = (share: number) => Math.min(100, Math.max(0, Math.floor(share * 100 + 1e-9)));

const meta = recordedAnswer("get_meta", "meta").body;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const geometry = recordedAnswer("get_geometry", "geometry").body.data;

const profile = (slug: string) => recordedAnswer("get_area", `area/${slug}`).body.data;
const slugOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.slug ?? "";

interface Shown {
  ranking: RankData;
  explanations?: readonly Explanation[];
  facts?: readonly Fact[];
  explained?: boolean;
  explainFailed?: boolean;
  withDetails?: boolean;
  detailsFailed?: readonly string[];
  busy?: boolean;
  selectedId?: string | null;
  placeNames?: Record<string, string>;
  /** True to draw the list as it is before any ranking has come. */
  waitingForFirst?: boolean;
}

/** The list as an element, so that a test can draw it a second time with something changed. */
function listOf({
  ranking,
  explanations = [],
  facts = [],
  explained = true,
  explainFailed = false,
  withDetails = true,
  detailsFailed = [],
  busy = false,
  selectedId = null,
  placeNames = { "syn-p0021": "Cindermoor Works" },
  waitingForFirst = false,
}: Shown) {
  const details: Record<string, AreaData> = {};
  if (withDetails) {
    for (const area of ranking.ranked.slice(0, 5)) {
      if (!detailsFailed.includes(area.area_id)) details[area.area_id] = profile(slugOf(area.area_id));
    }
  }
  const held: Record<string, Fact> = {};
  for (const fact of [...facts, ...Object.values(details).flatMap((detail) => detail.facts)]) {
    held[fact.fact_id] = fact;
  }
  const told = { onSelect: jest.fn(), onHover: jest.fn(), onEdit: jest.fn() };
  const element = (
    <ResultList
      ranked={waitingForFirst ? null : ranking.ranked}
      areas={areas}
      explanations={explanations}
      explained={explained}
      explainFailed={explainFailed}
      facts={held}
      details={details}
      detailsFailed={detailsFailed}
      geometry={geometry}
      spec={ranking.spec}
      meta={meta.data}
      served={meta.meta}
      placeNames={placeNames}
      noFit={ranking.empty_spec}
      busy={busy}
      selectedId={selectedId}
      {...told}
    />
  );
  return { element, told };
}

function show(shown: Shown) {
  const { element, told } = listOf(shown);
  return { ...told, user: userEvent.setup({ delay: null }), ...render(element) };
}

const first = {
  ranking: recordedAnswer("rank", "rank-first").body.data,
  ...recordedAnswer("explain_top", "explanations-first").body.data,
};
const two = {
  ranking: recordedAnswer("rank", "rank-two-journeys").body.data,
  ...recordedAnswer("explain_top", "explanations-two-journeys").body.data,
};
const cards = () => screen.getAllByRole("article");
const card = (at: number) => within(cards()[at] as HTMLElement);
/** The part of a card under the word "Trade-off". */
const tradeOff = (at: number) =>
  card(at).getByRole("heading", { name: RESULTS.tradeOffTitle }).parentElement as HTMLElement;

/** The first ranked area of a ranking, changed in one way, with the rest as recorded. */
function withFirstArea(ranking: RankData, change: (area: RankedArea) => RankedArea): RankData {
  const [top, ...rest] = ranking.ranked;
  if (!top) throw new Error("the recording ranks nothing");
  return { ...ranking, ranked: [change(top), ...rest] };
}

describe("the list of results", () => {
  test("test_the_list_is_an_ordered_list_in_rank_order", () => {
    show(first);

    const list = screen.getByRole("list", { name: RESULTS.listLabel });
    expect(list.tagName).toBe("OL");
    expect([...list.children].map((item) => item.getAttribute("data-area"))).toEqual(
      first.ranking.ranked.map((area) => area.area_id),
    );
    expect(cards().map((one) => within(one).getAllByText(/^Rank \d+$/)[0]?.textContent)).toEqual(
      first.ranking.ranked.map((area) => `Rank ${area.rank}`),
    );
  });

  test("test_the_first_five_are_cards_in_full_and_the_rest_are_rows", () => {
    show(first);

    const full = cards().filter((one) => within(one).queryByRole("heading", { name: RESULTS.reasonsTitle }));
    expect(full).toHaveLength(5);
    expect(full).toEqual(cards().slice(0, 5));
    for (const row of cards().slice(5)) {
      expect(within(row).getByRole("button", { name: /^More about this result/ })).toBeInTheDocument();
      expect(within(row).queryByRole("heading", { name: RESULTS.tradeOffTitle })).toBeNull();
    }
  });

  test("test_a_list_being_worked_out_again_stays_and_says_it_is_busy", () => {
    show({ ...first, busy: true });

    expect(screen.getByRole("list", { name: RESULTS.listLabel })).toHaveAttribute("aria-busy", "true");
    expect(cards()).toHaveLength(20);
  });

  test("test_a_list_being_worked_out_again_says_so_in_words_that_can_be_seen", () => {
    const { rerender, container } = show({ ...first, busy: true });

    // It is said in words, and not by dimming: dimmed, the text falls below the contrast it needs.
    const words = screen.getByText(RESULTS.working);
    expect(words.closest("[aria-hidden='true'], .visually-hidden, [hidden]")).toBeNull();
    // The words are above the list, so that they are read before it.
    const list = screen.getByRole("list", { name: RESULTS.listLabel });
    expect(words.compareDocumentPosition(list) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // The state is said once: the line in the form is the one that is announced.
    expect(words.closest("[role='status'], [role='alert'], [aria-live]")).toBeNull();
    const held = container.querySelectorAll("p").length;

    rerender(listOf({ ...first, busy: false }).element);

    expect(screen.queryByText(RESULTS.working)).toBeNull();
    // Its place is kept whether or not it says anything, so the list stays where it is.
    expect(container.querySelectorAll("p")).toHaveLength(held);
  });

  test("test_a_first_search_that_is_waited_for_is_not_said_to_be_worked_out_again", () => {
    render(listOf({ ...first, busy: true, waitingForFirst: true }).element);

    expect(screen.queryByText(RESULTS.working)).toBeNull();
  });
});

describe("a result card", () => {
  test("test_the_heading_gives_rank_name_borough_and_fit_rounded_down", () => {
    show(first);

    expect(card(0).getByRole("heading", { level: 3, name: "Farrowmere" })).toBeInTheDocument();
    expect(card(0).getByText("Quillhaven")).toBeInTheDocument();
    expect(card(0).getByText("Rank 1")).toBeInTheDocument();
    // 80.99 is shown as 80: a fit is never said to be more than it is.
    expect(first.ranking.ranked[0]?.score).toBe(80.99);
    expect(card(0).getByText("80 of 100")).toBeInTheDocument();
    expect(card(0).queryByText("81 of 100")).toBeNull();
  });

  test("test_every_sentence_is_the_apis_word_for_word", () => {
    show(first);

    first.explanations.forEach((explanation, at) => {
      const sentences = [explanation.orientation, ...explanation.reasons, explanation.trade_off, ...explanation.missing];
      for (const sentence of sentences) {
        if (sentence) expect(card(at).getByText(sentence.text)).toBeInTheDocument();
      }
    });
  });

  test("test_there_are_three_reasons_and_one_trade_off_under_their_own_headings", () => {
    show(first);

    const reasons = card(0).getByRole("heading", { name: RESULTS.reasonsTitle }).parentElement as HTMLElement;
    expect(within(reasons).getAllByRole("listitem")).toHaveLength(3);
    expect(within(reasons).getByRole("list").tagName).toBe("OL");
    const tradeOff = card(0).getByRole("heading", { name: RESULTS.tradeOffTitle }).parentElement as HTMLElement;
    expect(tradeOff).toHaveTextContent(first.explanations[0]?.trade_off?.text ?? "no trade-off");
  });

  test("test_with_no_trade_off_the_card_says_so", () => {
    const [top, ...rest] = first.explanations;
    if (!top) throw new Error("the recording explains nothing");

    show({ ...first, explanations: [{ ...top, trade_off: null }, ...rest] });

    expect(RESULTS.noTradeOff).toBe("No trade-off found for this search");
    expect(tradeOff(0)).toHaveTextContent(RESULTS.noTradeOff);
    expect(card(1).queryByText(RESULTS.noTradeOff)).toBeNull();
    // Nothing else is put in its place: no sentence, and no source of one.
    expect(within(tradeOff(0)).queryByRole("button")).toBeNull();
  });

  test("test_with_fewer_than_three_reasons_only_those_are_shown", () => {
    const buyer = {
      ranking: recordedAnswer("rank", "rank-buyer-family").body.data,
      ...recordedAnswer("explain_top", "explanations-buyer-family").body.data,
    };

    show(buyer);

    const reasons = card(0).getByRole("heading", { name: RESULTS.reasonsTitle }).parentElement as HTMLElement;
    expect(buyer.explanations[0]?.reasons).toHaveLength(2);
    expect(within(reasons).getAllByRole("listitem")).toHaveLength(2);
  });

  test("test_a_sentence_a_model_wrote_says_so", () => {
    const [top, ...rest] = first.explanations;
    if (!top) throw new Error("the recording explains nothing");
    const written = { ...top, reasons: top.reasons.map((reason, at) => (at === 0 ? { ...reason, origin: "model" as const } : reason)) };

    show({ ...first, explanations: [written, ...rest] });

    expect(card(0).getAllByText(RESULTS.byModel)).toHaveLength(1);
    expect(card(1).queryByText(RESULTS.byModel)).toBeNull();
  });

  test("test_while_the_reasons_are_waited_for_their_place_is_held_and_nothing_moves_when_they_come", () => {
    show({ ...first, explanations: [], explained: false, withDetails: false });
    const held = cards()[0]?.querySelectorAll(".skeleton").length ?? 0;
    const parts = card(0).getAllByRole("heading").map((heading) => heading.textContent);

    expect(held).toBeGreaterThanOrEqual(5);
    for (const skeleton of document.querySelectorAll(".skeleton")) {
      expect(skeleton.closest("[aria-hidden='true']")).not.toBeNull();
    }

    cleanup();
    show(first);
    expect(cards()[0]?.querySelectorAll(".skeleton")).toHaveLength(0);
    // The same parts, in the same order, before and after.
    expect(card(0).getAllByRole("heading").map((heading) => heading.textContent)).toEqual(parts);
  });

  test("test_reasons_that_could_not_be_loaded_are_said_and_the_rest_of_the_card_is_there", () => {
    show({ ...first, explanations: [], explained: false, explainFailed: true });

    expect(card(0).getByText(RESULTS.reasonsFailed)).toBeInTheDocument();
    expect(cards()[0]?.querySelectorAll(".skeleton")).toHaveLength(0);
    expect(card(0).getByText("£975 to £1,300")).toBeInTheDocument();
  });

  test("test_where_it_is_gives_the_nearest_station_and_a_picture_named_for_the_area", () => {
    show(first);

    const station = within(card(0).getByRole("group", { name: "Nearest station" }));
    expect(station.getByText("Farrowmere")).toBeInTheDocument();
    expect(station.getByText("5")).toBeInTheDocument();
    expect(station.getByText("Cobalt line")).toBeInTheDocument();
    expect(card(0).getByRole("img", { name: "Where Farrowmere is among the areas of this data" })).toBeInTheDocument();
  });

  test("test_an_area_with_no_station_leaves_the_line_out", () => {
    const one = { ...first.ranking, ranked: first.ranking.ranked.slice(0, 1) };
    show({ ...first, ranking: one, withDetails: false, detailsFailed: ["syn-n0006"] });

    expect(card(0).queryByRole("group", { name: "Nearest station" })).toBeNull();
    expect(cards()[0]?.querySelectorAll(".skeleton")).toHaveLength(0);
  });

  test("test_of_two_stations_only_the_nearest_is_given_on_the_card", () => {
    // Pellam Cross has a nearest station and another within a short walk.
    const pellam = areas.find((area) => area.slug === "pellam-cross");
    const ranked = first.ranking.ranked.map((area, at) =>
      at === 0 ? { ...area, area_id: pellam?.area_id ?? "" } : area,
    );

    show({ ranking: { ...first.ranking, ranked: ranked.slice(0, 1) } });

    const stations = profile("pellam-cross").facts.filter((fact) => fact.kind === "station");
    expect(stations.map((fact) => fact.template).sort()).toEqual(["station", "station_nearby"]);
    expect(card(0).getAllByRole("group", { name: /station/i })).toHaveLength(1);
    const nearest = stations.find((fact) => fact.template === "station");
    expect(within(card(0).getByRole("group", { name: "Nearest station" })).getByText(nearest?.slots.name ?? "")).toBeInTheDocument();
  });

  test("test_every_sentence_and_every_figure_ends_in_a_source", () => {
    show(first);

    const sources = card(0).getAllByRole("button", { name: /^Source/ });
    // Where it is, the station, three reasons, the trade-off, the journey and the cost.
    expect(sources).toHaveLength(8);
    expect(new Set(sources.map((source) => source.getAttribute("aria-label"))).size).toBe(8);
    for (const source of sources) expect(source).toHaveClass("target-min");
  });

  test("test_a_source_opens_in_place_with_its_name_its_date_and_that_the_data_is_made_up", async () => {
    const { user } = show(first);
    const cost = card(0).getByRole("heading", { name: COST.title }).parentElement as HTMLElement;

    await user.click(within(cost).getByRole("button", { name: /^Source/ }));

    const link = within(cost).getByRole("link", { name: "Synthetic test data" });
    expect(link).toHaveAttribute("href", "/sources#synthetic");
    expect(within(cost).getByText(`${SOURCE.dataFrom} August 2026`)).toBeInTheDocument();
    expect(within(cost).getByText(SOURCE.madeUp)).toBeInTheDocument();
  });

  test("test_the_foot_of_the_card_names_the_release_and_the_engine", () => {
    show(first);

    expect(card(0).getByText(meta.meta.release_id)).toBeInTheDocument();
    expect(card(0).getByText(meta.meta.engine_version)).toBeInTheDocument();
  });

  test("test_the_actions_open_the_areas_page_show_it_on_the_map_and_hide_it", async () => {
    const { user, onSelect, onEdit } = show(first);

    expect(card(0).getByRole("link", { name: RESULTS.openArea("Farrowmere") })).toHaveAttribute(
      "href",
      "/synthetic/farrowmere",
    );
    await user.click(card(0).getByRole("button", { name: RESULTS.showOnMap("Farrowmere") }));
    expect(onSelect).toHaveBeenCalledWith("syn-n0006");
    await user.click(card(0).getByRole("button", { name: RESULTS.hide("Farrowmere") }));
    expect(onEdit).toHaveBeenCalledWith(edits.areaHide("syn-n0006"));
  });

  test("test_the_card_under_the_pointer_or_the_focus_is_told_to_the_map", async () => {
    const { user, onHover } = show(first);

    await user.hover(cards()[1] as HTMLElement);
    await user.unhover(cards()[1] as HTMLElement);
    await user.tab();

    expect(onHover.mock.calls.map(([areaId]) => areaId)).toEqual(
      expect.arrayContaining(["syn-n0017", null, "syn-n0006"]),
    );
  });

  test("test_the_chosen_card_says_so", () => {
    show({ ...first, selectedId: "syn-n0003" });

    expect(cards().filter((one) => one.getAttribute("aria-current") === "true")).toEqual([cards()[2]]);
  });
});

describe("a trade-off is something the area does badly", () => {
  /** A sentence as the API writes one, about a fact of the area that is in hand. */
  const sentenceOn = (factId: string, text: string): ExplainedSentence => ({
    text,
    fact_ids: [factId],
    origin: "template",
    replaced: false,
  });
  const withTradeOff = (sentence: ExplainedSentence | null) => {
    const [top, ...rest] = first.explanations;
    if (!top) throw new Error("the recording explains nothing");
    return { ...first, explanations: [{ ...top, trade_off: sentence }, ...rest] };
  };

  test("test_what_counts_as_doing_well_is_what_the_contract_says", () => {
    const contract = readFileSync(path.resolve(__dirname, "../../../../../docs/design/contract.md"), "utf8");

    // Contract 7.5: a reason is worth at least this, and a trade-off less, unless it is a shortfall.
    expect(contract).toContain("whose utility is at least `REASON_MIN_UTILITY`, 0.5,");
    expect(contract).toContain("**A trade-off is never something the area does well.**");
    expect(DOES_WELL_FROM).toBe(0.5);
  });

  test("test_a_strength_is_never_put_under_the_word_trade_off", () => {
    // Seen in a browser, from an engine before 1.3.0: "a 2 minute walk, closer than 77% of
    // areas" under "Trade-off". Here it is the air, which Farrowmere does better than most.
    const air = first.ranking.ranked[0]?.contributions.find((part) => part.component === "feature:air_no2");
    const strength = sentenceOn("syn-n0006/feature/air_no2", "A strength, said as the API would say one.");

    show(withTradeOff(strength));

    expect(air?.utility).toBeGreaterThanOrEqual(DOES_WELL_FROM);
    expect(tradeOff(0).textContent?.includes(strength.text)).toBe(false);
    expect(tradeOff(0)).toHaveTextContent(RESULTS.noTradeOff);
    // The cards beside it are as the API gave them.
    expect(tradeOff(1)).toHaveTextContent(first.explanations[1]?.trade_off?.text ?? "no trade-off");
  });

  test("test_a_sentence_about_nothing_that_counts_is_never_put_under_the_word_trade_off", () => {
    const stray = sentenceOn("syn-n0006/feature/homes_flats", "About a thing that does not count in this search.");

    show(withTradeOff(stray));

    expect(first.ranking.ranked[0]?.contributions.some((part) => part.fact_ids.includes(stray.fact_ids[0] ?? ""))).toBe(false);
    expect(tradeOff(0).textContent?.includes(stray.text)).toBe(false);
    expect(tradeOff(0)).toHaveTextContent(RESULTS.noTradeOff);
  });

  test("test_a_home_over_the_budget_is_a_trade_off_however_much_it_is_worth", () => {
    // Pellam Cross is £75 over the budget, which is worth 0.82: more than a half, and still a shortfall.
    show(first);

    const at = first.ranking.ranked.findIndex((area) => area.area_id === "syn-n0004");
    const budget = first.ranking.ranked[at]?.contributions.find((part) => part.component === "budget");
    expect(budget?.utility).toBeGreaterThanOrEqual(DOES_WELL_FROM);
    expect(first.ranking.ranked[at]?.budget?.margin).toBeLessThan(0);
    expect(tradeOff(at)).toHaveTextContent(first.explanations[at]?.trade_off?.text ?? "no trade-off");
  });

  const EXPLAINED = readdirSync(recordedFolder())
    .filter((name) => /^explanations-.*\.json$/.test(name))
    .map((name) => name.slice("explanations-".length, -".json".length));

  test.each(EXPLAINED)("test_every_trade_off_the_api_gave_is_shown_word_for_word: %s", (search) => {
    const ranking = recordedAnswer("rank", `rank-${search}`).body.data;
    const { explanations, facts } = recordedAnswer("explain_top", `explanations-${search}`).body.data;

    show({ ranking, explanations, facts });

    // The website's own check is never stricter than the engine's: nothing the API gave is lost.
    expect(explanations.length).toBeGreaterThan(0);
    ranking.ranked.slice(0, 5).forEach((area, at) => {
      const given = explanations.find((one) => one.area_id === area.area_id)?.trade_off;
      expect(tradeOff(at).textContent?.includes(given?.text ?? RESULTS.noTradeOff)).toBe(true);
    });
  });

  test("test_a_journey_given_as_the_trade_off_says_whether_it_is_over_the_time_that_was_set", () => {
    // The sentence gives the minutes and not the limit. The card holds both, and says which way it falls.
    show(two);

    expect(two.explanations[0]?.trade_off?.fact_ids[0]).toBe("syn-n0016/travel/syn-p0026.pt");
    expect(two.ranking.spec.commutes.find((one) => one.place_id === "syn-p0026")?.max_minutes).toBe(30);
    expect(tradeOff(0)).toHaveTextContent(two.explanations[0]?.trade_off?.text ?? "no trade-off");
    expect(within(tradeOff(0)).getByText(JOURNEYS.overLimit(30))).toBeInTheDocument();
  });

  test("test_a_trade_off_that_is_not_a_journey_has_no_verdict_beside_it", () => {
    show(first);

    for (const at of [0, 1, 2, 3, 4]) {
      expect(within(tradeOff(at)).queryByText(/your limit of/)).toBeNull();
    }
  });
});

describe("how complete the data is", () => {
  const completeness = (at: number) => cards()[at]?.querySelector("[class*='completeness']") as HTMLElement;
  const bar = (at: number) => completeness(at).querySelector<HTMLElement>("[class*='meter'] span");

  test("test_a_card_with_everything_says_so", () => {
    show(first);

    expect(card(0).getByText(COMPLETENESS.all)).toBeInTheDocument();
  });

  test("test_the_bar_is_as_wide_as_the_words_say", () => {
    show(first);

    // Seen by the reviewers: "5 of the 10" beside a bar 77% wide. The bar was another
    // measure, of how much of the weight had data. Now it draws what the words count.
    expect(first.ranking.ranked[1]?.weight_coverage).toBeCloseTo(0.7778, 3);
    expect(completeness(1)).toHaveTextContent(COMPLETENESS.some(5, 10));
    expect(bar(1)?.style.width).toBe("50%");

    first.ranking.ranked.forEach((area, at) => {
      const has = area.contributions.filter((part) => part.present).length;
      const of = area.contributions.length;
      expect(completeness(at)).toHaveTextContent(has === of ? COMPLETENESS.all : COMPLETENESS.some(has, of));
      expect(bar(at)?.style.width).toBe(`${(100 * has) / of}%`);
    });
  });

  test("test_how_complete_is_said_directly_under_the_fit_on_a_card_as_on_a_row", () => {
    show(first);

    // It is what says how far to trust the fit, so it is read with the fit.
    for (const at of [0, 1, 4, 5, 19]) {
      expect(cards()[at]?.querySelector("header")?.nextElementSibling).toBe(completeness(at));
    }
  });

  test("test_a_card_with_something_missing_counts_it_and_gives_the_apis_sentence_for_each", () => {
    show(first);

    expect(card(1).getByText(COMPLETENESS.some(5, 10))).toBeInTheDocument();
    const missing = first.explanations[1]?.missing ?? [];
    expect(missing).toHaveLength(5);
    for (const sentence of missing) expect(card(1).getByText(sentence.text)).toBeInTheDocument();
  });

  test("test_no_two_source_buttons_of_a_card_have_the_same_name", () => {
    show(first);

    for (const at of [0, 1, 2, 3, 4]) {
      const names = card(at)
        .getAllByRole("button", { name: /^Source/ })
        .map((button) => button.getAttribute("aria-label") ?? button.textContent ?? "");

      expect(names.length).toBeGreaterThan(5);
      expect(names.filter((name, index) => names.indexOf(name) !== index)).toEqual([]);
      // None is "Source" and no more: each says what it is the source of.
      expect(names.filter((name) => name === SOURCE.button)).toEqual([]);
    }
  });

  test("test_what_has_no_figure_is_listed_under_a_heading_and_its_place_is_held", () => {
    show({ ...first, explanations: [], explained: false });

    // How many sentences will come is known from the ranking, so their place is held.
    const waiting = card(1).getByRole("heading", { name: COMPLETENESS.missingTitle }).parentElement;
    expect(waiting?.querySelectorAll(".skeleton")).toHaveLength(5);
    expect(card(0).queryByRole("heading", { name: COMPLETENESS.missingTitle })).toBeNull();

    cleanup();
    show(first);
    const listed = card(1).getByRole("heading", { name: COMPLETENESS.missingTitle }).parentElement;
    expect(listed?.querySelectorAll(".skeleton")).toHaveLength(0);
    expect(within(listed as HTMLElement).getAllByRole("button", { name: /^Source/ })).toHaveLength(5);
  });

  test("test_a_limit_that_could_not_be_tested_is_said_in_a_line", () => {
    show(two);

    expect(two.ranking.ranked[0]?.untested_filters).toEqual(["over_budget"]);
    expect(card(0).getByText(UNTESTED.over_budget)).toBeInTheDocument();
  });

  test("test_a_limit_that_could_not_be_tested_is_said_under_the_fit_and_not_in_small_print", () => {
    show(two);

    // It is the gravest thing a result can carry: the one limit the person called firm
    // was not applied. It is given the weight of the trade-off, and the same mark.
    const line = card(0).getByText(UNTESTED.over_budget);
    expect(completeness(0).contains(line)).toBe(true);
    expect(line.closest("p")?.querySelector("[aria-hidden='true']")).not.toBeNull();
    const rules = STYLES.filter((rule) => isFor(rule.selector, "untested"));
    expect(rules.map((rule) => rule.sets.get("color")).filter(Boolean)).toEqual(["var(--tradeoff)"]);
    expect(rules.flatMap((rule) => [...rule.sets.keys()])).not.toContain("font-size");
  });

  test("test_a_row_says_how_complete_it_is_in_one_line", () => {
    show(first);

    expect(card(5).getByText(COMPLETENESS.some(9, 10))).toBeInTheDocument();
  });
});

describe("the journeys", () => {
  const journeys = (at: number) => within(card(at).getByRole("table", { name: JOURNEYS.title }));

  test("test_each_journey_gives_the_place_how_both_times_and_within_or_over_in_words", () => {
    show(first);

    const cells = journeys(0).getAllByRole("row")[1] as HTMLElement;
    expect(within(cells).getByRole("rowheader")).toHaveTextContent("Cindermoor Works");
    expect(within(cells).getAllByRole("cell").map(said)).toEqual([
      "Public transport",
      "21 minutes",
      "26 minutes",
      "within 35 minutes Source",
    ]);
  });

  test("test_a_journey_can_be_stacked_on_a_narrow_screen_and_is_still_a_table", () => {
    show(two);
    const table = card(0).getByRole("table", { name: JOURNEYS.title });
    const columns = journeys(0).getAllByRole("columnheader").map((header) => header.textContent);

    // Stacked, a browser may forget that a table is one. Each part says its role again.
    expect(table).toHaveAttribute("role", "table");
    expect([...table.querySelectorAll("thead, tbody")].map((group) => group.getAttribute("role"))).toEqual([
      "rowgroup",
      "rowgroup",
    ]);
    for (const row of table.querySelectorAll("tr")) expect(row).toHaveAttribute("role", "row");
    // Each cell says what it is of, for the eye, because the headings are not drawn when stacked.
    for (const row of journeys(0).getAllByRole("row").slice(1)) {
      const labels = [...row.querySelectorAll("td")].map(
        (cell) => cell.querySelector("[aria-hidden='true'][class*='cellLabel']")?.textContent,
      );
      expect(labels).toEqual(columns.slice(1));
    }
    // It does not scroll sideways: the verdict was in the last column, off the screen.
    expect(table.closest(".scroll-x")).toBeNull();
    expect(onANarrowScreen("journeys").some((rule) => rule.sets.get("display") === "block")).toBe(true);
    // The verdict comes first under the place, where it is read before the times.
    expect(onANarrowScreen("verdict").map((rule) => rule.sets.get("order"))).toEqual(["-1"]);
  });

  test("test_a_journey_over_the_longest_set_says_over", () => {
    const slow = withFirstArea(first.ranking, (area) => ({
      ...area,
      legs: area.legs.map((leg) => ({ ...leg, minutes: 41, minutes_typical: 41, minutes_just_missed: 47 })),
    }));

    show({ ...first, ranking: slow });

    expect(journeys(0).getByText(JOURNEYS.over)).toBeInTheDocument();
    expect(journeys(0).queryByText(JOURNEYS.within)).toBeNull();
    expect(journeys(1).getByText(JOURNEYS.within)).toBeInTheDocument();
  });

  test("test_a_journey_beyond_what_the_data_holds_says_more_than_the_cutoff", () => {
    const far = withFirstArea(first.ranking, (area) => ({
      ...area,
      legs: area.legs.map((leg) => ({
        ...leg,
        status: "beyond_cutoff" as const,
        minutes: null,
        minutes_typical: null,
        minutes_just_missed: null,
      })),
    }));

    show({ ...first, ranking: far });

    expect(journeys(0).getByText(JOURNEYS.beyond(meta.data.limits.cutoff_minutes.pt))).toBeInTheDocument();
    expect(journeys(0).getByText(JOURNEYS.over)).toBeInTheDocument();
  });

  test("test_a_journey_with_no_time_says_so_and_is_neither_within_nor_over", () => {
    const unknown = withFirstArea(first.ranking, (area) => ({
      ...area,
      legs: area.legs.map((leg) => ({
        ...leg,
        status: "missing" as const,
        minutes: null,
        minutes_typical: null,
        minutes_just_missed: null,
        utility: null,
      })),
    }));

    show({ ...first, ranking: unknown });

    expect(journeys(0).getByText(JOURNEYS.missing)).toBeInTheDocument();
    expect(journeys(0).queryByText(JOURNEYS.within)).toBeNull();
    expect(journeys(0).queryByText(JOURNEYS.over)).toBeNull();
  });

  test("test_by_bike_there_is_one_time_and_no_service_to_miss", () => {
    const river = {
      ranking: recordedAnswer("rank", "rank-by-the-river").body.data,
      ...recordedAnswer("explain_top", "explanations-by-the-river").body.data,
    };

    show({ ...river, placeNames: {} });

    const row = journeys(0).getAllByRole("row")[1] as HTMLElement;
    expect(within(row).getAllByRole("cell").map(said).slice(0, 3)).toEqual([
      "By bike",
      "5 minutes",
      JOURNEYS.notApply,
    ]);
    // No name was given for the place, so it is called by its position.
    expect(within(row).getByRole("rowheader")).toHaveTextContent(PLACE.unnamed(1));
  });

  test("test_with_two_journeys_a_line_under_them_says_which_one_the_fit_uses", () => {
    show({ ...two, placeNames: { "syn-p0019": "Foxholt Market", "syn-p0026": "Wexmoor University" } });

    const [area] = two.ranking.ranked;
    // The journey the fit uses is the one the API names first for the journey's part of the fit.
    expect(area?.contributions.find((one) => one.component === "commute")?.fact_ids[0]).toBe(
      "syn-n0016/travel/syn-p0026.pt",
    );
    const part = card(0).getByRole("heading", { name: JOURNEYS.title }).parentElement as HTMLElement;
    expect(within(part).getByText(JOURNEYS.usesOne("Wexmoor University"))).toBeInTheDocument();
    // A place is named by its name and nothing else: a reader heard "Wexmoor University counts".
    expect(journeys(0).getAllByRole("rowheader").map(said)).toEqual(["Foxholt Market", "Wexmoor University"]);
    expect(JOURNEYS.usesOne("x")).toMatch(/Settings/);
  });

  test("test_when_the_average_counts_the_line_says_so", () => {
    show({ ranking: { ...two.ranking, spec: { ...two.ranking.spec, commute_combine: "mean" } }, placeNames: {} });

    const part = card(0).getByRole("heading", { name: JOURNEYS.title }).parentElement as HTMLElement;
    expect(within(part).getByText(JOURNEYS.usesMean)).toBeInTheDocument();
    expect(within(part).queryByText(/does worst/)).toBeNull();
  });

  /** One journey that is known and is over its limit, and one with no time: so the API counts neither. */
  const oneUnknown = withFirstArea(two.ranking, (area) => ({
    ...area,
    legs: area.legs.map((leg, at) =>
      at === 0
        ? { ...leg, minutes: 63, minutes_typical: 63, minutes_just_missed: 68, utility: 0 }
        : {
            ...leg,
            status: "missing" as const,
            minutes: null,
            minutes_typical: null,
            minutes_just_missed: null,
            utility: null,
          },
    ),
    contributions: area.contributions.map((part) =>
      part.component === "commute"
        ? { ...part, present: false, utility: null, contribution: 0, share: 0, fact_ids: [] }
        : part,
    ),
  }));

  test("test_journeys_that_do_not_count_because_one_has_no_time_say_so_directly_under_the_fit", () => {
    // Seen in a browser: an area known to be 63 minutes from a workplace, against a limit
    // of 35, was ranked first, because its other journey had no time and so neither counted.
    // Its card gave the fit, then "within" and "over" for each journey, and never said that
    // the journeys counted for nothing.
    show({ ...two, ranking: oneUnknown, placeNames: {} });

    const under = cards()[0]?.querySelector("header")?.nextElementSibling as HTMLElement;
    const line = within(under).getByText(JOURNEYS.notCounted(2, true));
    // It has the weight of the trade-off, and the same mark: it says how far to trust the fit.
    expect(line.closest("p")?.querySelector("[aria-hidden='true']")).not.toBeNull();
    expect(line.closest("p")?.className.includes("untested")).toBe(true);
    expect(JOURNEYS.notCounted(2, true)).toMatch(/over the limit/);
    expect(JOURNEYS.notCounted(2, false)).not.toMatch(/over the limit/);
  });

  test("test_journeys_that_do_not_count_are_not_said_to_feed_the_fit_under_their_table", () => {
    show({ ...two, ranking: oneUnknown, placeNames: {} });

    const part = card(0).getByRole("heading", { name: JOURNEYS.title }).parentElement as HTMLElement;
    expect(within(part).getByText(JOURNEYS.usesNone(2))).toBeInTheDocument();
    // Neither of the lines that say which journey feeds the fit: none does.
    expect(part.textContent?.includes("does worst")).toBe(false);
    expect(part.textContent?.includes(JOURNEYS.usesMean)).toBe(false);
  });

  test("test_a_card_whose_journeys_count_says_nothing_of_journeys_under_the_fit", () => {
    show(two);

    const under = cards()[0]?.querySelector("header")?.nextElementSibling as HTMLElement;
    expect(under.textContent?.includes("Journeys do not count")).toBe(false);
    expect(under.textContent?.includes("journey does not count")).toBe(false);
  });

  test("test_one_journey_with_no_time_says_that_it_does_not_count", () => {
    const unknown = withFirstArea(first.ranking, (area) => ({
      ...area,
      legs: area.legs.map((leg) => ({
        ...leg,
        status: "missing" as const,
        minutes: null,
        minutes_typical: null,
        minutes_just_missed: null,
        utility: null,
      })),
      contributions: area.contributions.map((part) =>
        part.component === "commute"
          ? { ...part, present: false, utility: null, contribution: 0, share: 0, fact_ids: [] }
          : part,
      ),
    }));

    show({ ...first, ranking: unknown });

    const under = cards()[0]?.querySelector("header")?.nextElementSibling as HTMLElement;
    expect(within(under).getByText(JOURNEYS.notCounted(1, false))).toBeInTheDocument();
  });

  test("test_the_journeys_lead_to_how_a_journey_is_timed", () => {
    show(first);

    // "Typical" and "If you just miss one" are said in full on Methods, and nowhere on the card.
    const part = card(0).getByRole("heading", { name: JOURNEYS.title }).parentElement as HTMLElement;
    const link = within(part).getByRole("link", { name: JOURNEYS.timed });
    expect(link).toHaveAttribute("href", "/methods#journeys");
    expect(link).toHaveClass("target-min");
    expect(link).toHaveAttribute("data-prefetch", "false");
  });

  test("test_with_one_journey_nothing_is_said_of_which_one_counts", () => {
    show(first);

    const part = card(0).getByRole("heading", { name: JOURNEYS.title }).parentElement as HTMLElement;
    expect(first.ranking.spec.commutes).toHaveLength(1);
    expect(part.textContent?.includes(JOURNEYS.usesMean)).toBe(false);
    expect(part.textContent?.includes(JOURNEYS.usesOne("Cindermoor Works"))).toBe(false);
  });

  test("test_a_journey_with_no_fact_in_hand_takes_its_source_from_another_journey", async () => {
    const { user } = show(first);

    // Row 6 has no reasons, so no fact of its own. Its source is the release's one source for journeys.
    await user.click(card(5).getByRole("button", { name: /^More about this result/ }));
    await user.click(journeys(5).getByRole("button", { name: /^Source/ }));

    expect(journeys(5).getByRole("link", { name: "Synthetic test data" })).toBeInTheDocument();
  });

  test("test_with_no_journey_fact_at_all_source_links_to_the_sources_page", () => {
    show({ ranking: first.ranking, withDetails: false });

    expect(journeys(0).getByRole("link", { name: /^Source/ })).toHaveAttribute("href", "/sources");
  });
});

describe("the cost", () => {
  const cost = (at: number) => within(card(at).getByRole("heading", { name: COST.title }).parentElement as HTMLElement);

  test("test_the_cost_is_the_range_the_middle_what_it_is_for_the_month_and_the_confidence_as_a_word", () => {
    show(first);

    expect(cost(0).getByText("£975 to £1,300")).toBeInTheDocument();
    expect(cost(0).getByText("1-bedroom home")).toBeInTheDocument();
    expect(cost(0).getByText("£1,125")).toBeInTheDocument();
    expect(cost(0).getByText("August 2026")).toBeInTheDocument();
    expect(cost(0).getByText(CONFIDENCE.medium, { exact: false })).toBeInTheDocument();
    expect(cost(1).getByText(CONFIDENCE.low, { exact: false })).toBeInTheDocument();
  });

  test("test_every_figure_of_the_cost_is_a_slot_of_the_fact_as_the_api_formatted_it", () => {
    show(first);

    const fact = profile("farrowmere").facts.find((one) => one.fact_id === "syn-n0006/cost/rent.bed_1");
    const shown = cost(0).getAllByText(/£[\d,]+/).map((figure) => figure.textContent ?? "");
    const figures = shown.flatMap((text) => text.match(/[\d,]+/g) ?? []);

    expect(fact).toBeDefined();
    // The person's own budget is theirs. Every other figure is the fact's.
    expect(figures.filter((figure) => figure !== "1,700")).toEqual([
      fact?.slots.lower,
      fact?.slots.upper,
      fact?.slots.median,
    ]);
  });

  test("test_the_budget_is_marked_on_the_range_and_said_in_words", () => {
    show(first);

    expect(cost(0).getByText(COST.above)).toBeInTheDocument();
    expect(cost(3).getByText(COST.inside)).toBeInTheDocument();
    expect(cost(0).getByRole("img", { name: COST.picture })).toBeInTheDocument();
  });

  test("test_every_bar_of_a_list_is_drawn_on_one_scale", () => {
    show(first);

    // One budget, five cards: the mark for it is in one place, so the eye can run down the list.
    const marks = [0, 1, 2, 3, 4].map(
      (at) => cards()[at]?.querySelector<HTMLElement>("[class*='bar'] [class*='budget']")?.style.insetInlineStart,
    );
    expect(marks.every((mark) => /^\d+(\.\d+)?%$/.test(mark ?? ""))).toBe(true);
    expect(new Set(marks).size).toBe(1);
    // The homes do not all cost the same, and the bars show it.
    const ranges = [0, 1, 2, 3, 4].map(
      (at) => cards()[at]?.querySelector<HTMLElement>("[class*='bar'] [class*='span']")?.style.insetInlineStart,
    );
    expect(new Set(ranges).size).toBeGreaterThan(1);
  });

  test("test_a_buyer_sees_a_price_and_not_a_rent", () => {
    const buyer = {
      ranking: recordedAnswer("rank", "rank-buyer-family").body.data,
      ...recordedAnswer("explain_top", "explanations-buyer-family").body.data,
    };

    show(buyer);

    expect(cost(1).getByText("Price")).toBeInTheDocument();
    expect(cost(1).queryByText(COST.aMonth, { exact: false })).toBeNull();
    expect(cost(1).getByText("terraced house")).toBeInTheDocument();
  });

  test("test_with_no_cost_figure_the_card_says_so_and_shows_no_number", () => {
    const studio = { ...first.ranking, spec: { ...first.ranking.spec, tenure: "buy" as const } };

    show({ ...first, ranking: studio });

    // A renter's kind of home has no price to buy at, so the data holds no figure for it.
    expect(cost(0).getByText(COST.none)).toBeInTheDocument();
    expect(cost(0).queryByText(/£/)).toBeNull();
  });

  test("test_a_cost_that_could_not_be_loaded_is_not_said_to_be_missing_from_the_data", () => {
    show({ ...first, detailsFailed: ["syn-n0006"] });

    expect(cost(0).getByText(RESULTS.detailsFailed)).toBeInTheDocument();
    expect(cost(0).queryByText(COST.none)).toBeNull();
    expect(cost(1).getByText("£1,025 to £1,350")).toBeInTheDocument();
  });
});

describe("how the fit is worked out", () => {
  test("test_the_breakdown_is_closed_at_first_and_opens_to_a_table_of_everything_asked_for", async () => {
    const { user } = show(first);
    const button = card(0).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` });

    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(card(0).queryByRole("table", { name: BREAKDOWN.caption })).toBeNull();
    await user.click(button);

    const table = within(card(0).getByRole("table", { name: BREAKDOWN.caption }));
    // The rows are in the order the API gave the contributions in: the website sorts nothing.
    expect(first.ranking.ranked[0]?.contributions.map((part) => part.component)).toEqual([
      "commute",
      "budget",
      "tag:quiet_residential",
      "tag:leafy",
      "feature:air_no2",
      "feature:station_walk",
      "feature:noise_exposure",
      "feature:station_lines",
      "feature:park_proximity",
      "feature:highstreet_access",
    ]);
    expect(table.getAllByRole("rowheader").map((header) => header.textContent)).toEqual([
      BREAKDOWN.journey,
      BREAKDOWN.budget,
      "Quiet residential",
      "Leafy",
      "Modelled annual mean nitrogen dioxide",
      "Walk to the nearest station",
      "Share of homes at 55 dB or more of transport noise",
      "Lines within a 10-minute walk",
      "Walk to the nearest park of 2 ha or more",
      "Share of homes within a 10-minute walk of a high street or town centre",
    ]);
    expect(table.getAllByRole("columnheader").map((header) => header.textContent)).toEqual([
      BREAKDOWN.columns.thing,
      BREAKDOWN.columns.weight,
      BREAKDOWN.columns.share,
      BREAKDOWN.columns.adds,
      BREAKDOWN.columns.says,
    ]);
  });

  test("test_every_figure_of_the_breakdown_is_rounded_down", async () => {
    const { user } = show(first);
    await user.click(card(0).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` }));

    const journey = within(card(0).getByRole("table", { name: BREAKDOWN.caption })).getAllByRole("row")[1];
    const [contribution] = first.ranking.ranked[0]?.contributions ?? [];

    // Recorded: weight 1.0, share 0.3175, contribution 0.2698.
    // To the nearest whole number the share would be 32 and the contribution 27.
    expect(contribution).toMatchObject({ share: 0.3175, contribution: 0.2698 });
    expect(within(journey as HTMLElement).getAllByRole("cell").slice(0, 3).map(said)).toEqual([
      "100 of 100",
      "31%",
      "26 of 100",
    ]);
  });

  test("test_the_breakdown_says_that_its_figures_are_rounded_down_and_may_not_add_up", async () => {
    const { user } = show(two);
    await user.click(card(0).getByRole("button", { name: `${BREAKDOWN.title}: Ostrel Vale` }));

    // Seen by the reviewers: what each thing adds came to 31 under a fit of 32.
    const [area] = two.ranking.ranked;
    const adds = (area?.contributions ?? []).map((part) => floored(part.contribution));
    expect(adds.reduce((sum, one) => sum + one, 0)).toBeLessThan(Math.floor(area?.score ?? 0));
    const part = card(0).getByRole("table", { name: BREAKDOWN.caption }).parentElement?.parentElement;
    expect(within(part as HTMLElement).getByText(BREAKDOWN.roundedDown)).toBeInTheDocument();
  });

  test("test_the_breakdown_never_prints_how_an_area_scores_on_a_thing", async () => {
    const { user } = show(two);
    await user.click(card(0).getByRole("button", { name: `${BREAKDOWN.title}: Ostrel Vale` }));
    const table = card(0).getByRole("table", { name: BREAKDOWN.caption });
    const [area] = two.ranking.ranked;

    // The score of a feature is the percentile it is ranked by, which the contract says is
    // never printed: where areas tie it is untrue of the release. Seen by the reviewers:
    // "67 of 100" for noise, a few lines under "quieter than 65% of the 20 areas".
    const noise = area?.contributions.find((part) => part.component === "feature:noise_exposure");
    expect(noise?.utility).toBe(0.675);
    expect(table.textContent?.includes(`${floored(noise?.utility ?? 0)} of 100`)).toBe(false);
    expect(within(table).queryByRole("columnheader", { name: /how well/i })).toBeNull();
    expect(table).toHaveTextContent("quieter than 65% of the 20 areas compared in this release");
  });

  test.each([
    ["rank-first", "explanations-first"],
    ["rank-two-journeys", "explanations-two-journeys"],
    ["rank-buyer-family", "explanations-buyer-family"],
  ] as const)("test_no_figure_of_an_opened_breakdown_is_one_the_api_did_not_send: %s", async (ranked, explained) => {
    const ranking = recordedAnswer("rank", ranked).body.data;
    const { explanations, facts } = recordedAnswer("explain_top", explained).body.data;
    const { user } = show({ ranking, explanations, facts, placeNames: {} });

    for (const [at, area] of ranking.ranked.slice(0, 5).entries()) {
      const name = areas.find((one) => one.area_id === area.area_id)?.name ?? "";
      await user.click(card(at).getByRole("button", { name: `${BREAKDOWN.title}: ${name}` }));
      const table = card(at).getByRole("table", { name: BREAKDOWN.caption });
      const allowed = new Set([
        // Every slot of every fact of the area, as the API formatted it.
        ...saidByFacts([...facts, ...profile(slugOf(area.area_id)).facts].filter((fact) => fact.area_id === area.area_id)),
        // The names of what counts, which the API gives with the form.
        ...meta.data.features.map((feature) => feature.label),
        ...meta.data.tags.map((tag) => tag.label),
        // The numbers of the ranking itself: how much a thing counts, its share, and what it adds.
        ...area.contributions.flatMap((part) => [
          BREAKDOWN.outOf(Math.round(part.weight * 100)),
          BREAKDOWN.percent(floored(part.share)),
          BREAKDOWN.outOf(floored(part.contribution)),
        ]),
        // A place with no name in hand, by its position.
        ...ranking.spec.commutes.map((_, position) => PLACE.unnamed(position + 1)),
      ]);

      expect(within(table).getAllByRole("row").length).toBe(area.contributions.length + 1);
      expect(figuresNotFrom(table, allowed)).toEqual([]);
    }
  });

  test("test_each_row_gives_what_the_data_says_in_the_apis_words_with_its_source", async () => {
    const { user } = show(first);
    await user.click(card(0).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` }));

    const rows = within(card(0).getByRole("table", { name: BREAKDOWN.caption })).getAllByRole("row");
    const walk = rows.find((row) => within(row).queryByRole("rowheader", { name: "Walk to the nearest station" }));
    const fact = profile("farrowmere").facts.find((one) => one.fact_id === "syn-n0006/feature/station_walk");
    const says = within(walk as HTMLElement).getAllByRole("cell").at(-1) as HTMLElement;

    expect(within(says).getByText(FACT_COLUMNS.value).nextElementSibling).toHaveTextContent(fact?.slots.value ?? "none");
    expect(within(says).getByText(FACT_COLUMNS.standing).nextElementSibling).toHaveTextContent(
      fact?.slots.standing ?? "none",
    );
    await user.click(within(says).getByRole("button", { name: /^Source for How the fit is worked out: Walk/ }));
    expect(within(says).getByRole("link", { name: "Synthetic test data" })).toBeInTheDocument();
  });

  test("test_a_thing_whose_fact_is_not_in_hand_says_only_that_there_is_a_figure", async () => {
    const { user } = show(first);
    // A row has no profile and no reasons, so no fact of its own is in hand.
    await user.click(card(5).getByRole("button", { name: /^More about this result/ }));
    await user.click(card(5).getByRole("button", { name: /^How the fit is worked out/ }));

    const rows = within(card(5).getByRole("table", { name: BREAKDOWN.caption })).getAllByRole("row").slice(1);
    const area = first.ranking.ranked[5];

    expect(rows.map((row) => said(within(row).getAllByRole("cell").at(-1)))).toEqual(
      area?.contributions.map((part) => (part.present ? BREAKDOWN.has : BREAKDOWN.hasNot)),
    );
  });

  test("test_something_with_no_figure_says_so_and_adds_nothing", async () => {
    const { user } = show(first);
    await user.click(card(1).getByRole("button", { name: `${BREAKDOWN.title}: Otterby Fields` }));

    const rows = within(card(1).getByRole("table", { name: BREAKDOWN.caption })).getAllByRole("row");
    const quiet = rows.find((row) => within(row).queryByRole("rowheader", { name: "Quiet residential" }));

    expect(within(quiet as HTMLElement).getAllByRole("cell").map(said)).toEqual([
      "50 of 100",
      "0%",
      "0 of 100",
      BREAKDOWN.hasNot,
    ]);
  });

  test("test_the_breakdown_can_be_stacked_on_a_narrow_screen_and_is_still_a_table", async () => {
    const { user } = show(first);
    await user.click(card(0).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` }));
    const table = card(0).getByRole("table", { name: BREAKDOWN.caption });
    const columns = within(table).getAllByRole("columnheader").map((header) => header.textContent);

    expect(table).toHaveAttribute("role", "table");
    expect([...table.querySelectorAll("thead, tbody")].map((group) => group.getAttribute("role"))).toEqual([
      "rowgroup",
      "rowgroup",
    ]);
    for (const row of within(table).getAllByRole("row").slice(1)) {
      const labels = [...row.querySelectorAll("td")].map(
        (cell) => cell.querySelector("[aria-hidden='true'][class*='cellLabel']")?.textContent,
      );
      expect(labels).toEqual(columns.slice(1));
    }
    expect(table.closest(".scroll-x")).toBeNull();
    expect(onANarrowScreen("breakdown").some((rule) => rule.sets.get("display") === "block")).toBe(true);
  });
});

describe("nothing to rank by", () => {
  test("test_with_nothing_set_no_fit_is_shown_because_it_would_say_nothing", () => {
    show({ ranking: recordedAnswer("rank", "rank-empty-spec").body.data, withDetails: false, placeNames: {} });

    expect(cards()).toHaveLength(20);
    expect(screen.queryByText(/of 100/)).toBeNull();
    expect(screen.queryByText(COMPLETENESS.all)).toBeNull();
  });
});

describe("automated checks", () => {
  test("test_a_list_of_results_has_no_accessibility_fault", async () => {
    const { container, user } = show(first);
    await user.click(card(0).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` }));
    await user.click(card(6).getByRole("button", { name: /^More about this result/ }));

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the website writes no fact about a place", () => {
  const SEARCHES = [
    ["rank-first", "explanations-first"],
    ["rank-buyer-family", "explanations-buyer-family"],
    ["rank-two-journeys", "explanations-two-journeys"],
    ["rank-nights-out", "explanations-nights-out"],
    ["rank-by-the-river", "explanations-by-the-river"],
  ] as const;

  /** What a card says, to a reader: its text, without what is drawn only for the eye. */
  const saidBy = (at: number) => {
    const copy = cards()[at]?.cloneNode(true) as HTMLElement;
    copy.querySelectorAll("[aria-hidden='true']").forEach((drawn) => drawn.remove());
    return copy.textContent ?? "";
  };

  /** Every run of digits in a text, with its separators taken out. */
  const figuresIn = (text: string) => (text.match(/\d[\d,]*(\.\d+)?/g) ?? []).map((figure) => figure.replace(/,/g, ""));

  test.each(SEARCHES)(
    "test_no_figure_on_a_card_is_one_the_api_did_not_send: %s",
    (ranked, explained) => {
      const ranking = recordedAnswer("rank", ranked).body.data;
      const { explanations, facts } = recordedAnswer("explain_top", explained).body.data;
      show({ ranking, explanations, facts, placeNames: {} });

      ranking.ranked.slice(0, 5).forEach((area, at) => {
        const detail = profile(slugOf(area.area_id));
        const explanation = explanations.find((one) => one.area_id === area.area_id);
        const sent = [
          // What the API said in words, and the slots of every fact in hand.
          ...(explanation ? [explanation.orientation, ...explanation.reasons, explanation.trade_off, ...explanation.missing] : [])
            .flatMap((sentence) => (sentence ? figuresIn(sentence.text) : [])),
          ...[...facts, ...detail.facts]
            .filter((fact) => fact.area_id === area.area_id)
            .flatMap((fact) => Object.values(fact.slots).flatMap(figuresIn)),
          // The numbers of the ranking itself, rounded down where they are shown as a whole.
          String(area.rank),
          String(Math.floor(area.score)),
          ...area.legs.flatMap((leg) => [leg.minutes, leg.minutes_typical, leg.minutes_just_missed].map(String)),
          String(area.contributions.length),
          String(area.contributions.filter((one) => one.present).length),
          // What the person set themselves.
          String(ranking.spec.budget.amount),
          ...ranking.spec.commutes.map((commute) => String(commute.max_minutes)),
          // The place's position, where it has no name in hand.
          ...ranking.spec.commutes.map((_, position) => String(position + 1)),
          // The release and the engine, and the top of the scale.
          ...figuresIn(meta.meta.release_id),
          ...figuresIn(meta.meta.engine_version),
          "100",
        ];
        const shown = figuresIn(saidBy(at));

        expect(shown.length).toBeGreaterThan(8);
        expect(shown.filter((figure) => !sent.includes(figure))).toEqual([]);
      });
    },
  );

  test.each(SEARCHES)(
    "test_no_name_on_a_card_is_one_the_api_did_not_send: %s",
    (ranked, explained) => {
      const ranking = recordedAnswer("rank", ranked).body.data;
      const { explanations, facts } = recordedAnswer("explain_top", explained).body.data;
      show({ ranking, explanations, facts, placeNames: {} });
      // Every name the release holds, of an area, a borough, a station, a line or a place.
      const everyName = new Set(
        areas.flatMap((area) => [
          area.name,
          area.borough,
          ...profile(area.slug).facts.flatMap((fact) => fact.names),
        ]),
      );
      for (const fact of facts) fact.names.forEach((name) => everyName.add(name));

      ranking.ranked.slice(0, 5).forEach((area, at) => {
        const allowed = new Set([
          ...[...facts, ...profile(slugOf(area.area_id)).facts]
            .filter((fact) => fact.area_id === area.area_id)
            .flatMap((fact) => fact.names),
        ]);
        const text = saidBy(at);
        const named = [...everyName].filter((name) => text.includes(name));

        expect(named.length).toBeGreaterThan(1);
        // A name on this card is a name of one of this area's own facts.
        expect(named.filter((name) => ![...allowed].some((own) => own.includes(name)))).toEqual([]);
      });
    },
  );
});

describe("a card chosen on the map", () => {
  const scrolled: { area: string | null; how: unknown }[] = [];
  const motion = (reduced: boolean) =>
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: (query: string) => ({ matches: reduced && query.includes("reduce"), media: query }),
    });

  beforeEach(() => {
    scrolled.length = 0;
    Element.prototype.scrollIntoView = function scrollIntoView(this: Element, how?: unknown) {
      scrolled.push({ area: this.getAttribute("data-area"), how });
    };
  });

  afterEach(() => {
    delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
    delete (window as { matchMedia?: unknown }).matchMedia;
  });

  function list(selectedId: string | null) {
    return (
      <ResultList
        ranked={first.ranking.ranked}
        areas={areas}
        explanations={first.explanations}
        explained
        explainFailed={false}
        facts={{}}
        details={{}}
        detailsFailed={[]}
        geometry={null}
        spec={first.ranking.spec}
        meta={meta.data}
        served={meta.meta}
        placeNames={{}}
        noFit={false}
        busy={false}
        selectedId={selectedId}
        onSelect={() => undefined}
        onHover={() => undefined}
        onEdit={() => undefined}
      />
    );
  }

  test("test_its_card_is_brought_into_view_and_the_focus_stays_where_it_was", () => {
    motion(false);
    const { rerender } = render(list(null));
    const focused = screen.getAllByRole("button")[0] as HTMLElement;
    focused.focus();

    rerender(list("syn-n0023"));

    expect(scrolled).toEqual([{ area: "syn-n0023", how: { block: "nearest", behavior: "smooth" } }]);
    expect(focused).toHaveFocus();
    rerender(list(null));
    expect(scrolled).toHaveLength(1);
  });

  test("test_with_reduced_motion_the_list_jumps_and_does_not_glide", () => {
    motion(true);
    const { rerender } = render(list(null));

    rerender(list("syn-n0023"));

    expect(scrolled).toEqual([{ area: "syn-n0023", how: { block: "nearest", behavior: "auto" } }]);
  });
});
