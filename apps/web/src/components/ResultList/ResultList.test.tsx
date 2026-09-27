import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { cloneElement, useState } from "react";

import { NAMED } from "@/content/area";
import { CARD } from "@/content/card";
import { KNOWN } from "@/content/kit";
import { FACT_COLUMNS } from "@/content/facts";
import { MapCard } from "@/components/MapView/MapCard";
import { COMPARE, TRAY } from "@/content/compare";
import { MAP_CARD } from "@/content/map";
import {
  APART,
  BREAKDOWN,
  COMPLETENESS,
  CONFIDENCE,
  COST,
  JOURNEYS,
  LOCATOR,
  RESULTS,
  SOURCE,
  STRIP,
  UNTESTED,
} from "@/content/search";
import { JOURNEY } from "@/content/settings";
import { TOWN } from "@/content/town";
import { TOWNS } from "@/content/towns";
import { REFINE } from "@/content/ways";
import { recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type {
  AreaData,
  ExplainedSentence,
  Explanation,
  Fact,
  MetaData,
  RankData,
  RankedArea,
  VibeBands,
} from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";
import { SessionProvider } from "@/lib/session/session";
import type { Mark } from "@/lib/town/bands";
import { blankSaid, saidOf } from "@/lib/town/said";
import { inWords } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { holdsAt, rowOf, setAt } from "../../../test/support/cascade";
import { heavier, isFor, rulesOf, subjectOf, weightOf } from "../../../test/support/css";
import { figuresNotFrom, saidBy as saidByFacts } from "../../../test/support/figures";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { CompareTray } from "../CompareTray/CompareTray";
import { INVITE_STANDS, TWO_TOWNS, type InviteStands } from "../CompareTray/look";
import { asLines, namesOf } from "../Strip/column";
import { Town } from "../Town/Town";
import { Key } from "../VibesList/Key";
import { TRADE_OFF_SHOWN } from "../VibesList/look";
import { columnOf } from "./lines";
import {
  ENDS_ON_A_RESULT,
  ENDS_ON_A_RESULT_MAY_BE,
  FIT_MAY_BE_SAID,
  LINE_STANDS,
  LINE_STANDS_AT,
  ON_A_NARROW_RESULT,
  ON_A_NARROW_RESULT_A_BUTTON_IS,
  OTHERS_MAY_STAND,
  OTHERS_STAND,
  OVER_THE_LIST,
  OVER_THE_LIST_MAY_STAND,
  BESIDE_A_TRADE_OFF,
  DRAWING_OF_A_TRADE_OFF,
  TOWN_DRAWN,
  TRADE_OFF_DRAWN,
  TRADE_OFF_MAY_BE_DRAWN,
  WHAT_A_FIT_IS_BASED_ON_IS_SAID_IN_THE,
  type EndsOnAResult,
  type FitSaid,
  type LineStands,
  type OnANarrowResult,
  type OnANarrowResultAButtonIs,
  type OthersStand,
  type OverTheList,
  type TownDrawn,
  type TradeOffDrawn,
} from "./look";
import { ResultList as ListPart, SHOWN_AT_FIRST } from "./ResultList";
import { isGivenUp } from "./tradeoff";

const STYLES = rulesOf(readFileSync(path.join(__dirname, "ResultList.module.css"), "utf8"));

/**
 * The whole list, as the page draws it: the first result, and then the rest of them. On
 * the page the map stands between the two.
 */
function ResultList(props: Omit<Parameters<typeof ListPart>[0], "part">) {
  return (
    <>
      <ListPart {...props} part="first" />
      <ListPart {...props} part="rest" />
    </>
  );
}
/** Both parts of the list, in the order they stand in. */
const lists = () => screen.getAllByRole("list", { name: new RegExp(`^${RESULTS.listLabel}`) });
/**
 * The rules for a class that hold in a narrow place and not in a wide one. The working of
 * a result is laid out by the width of its own box, which on a phone is the screen less
 * its edges: so a rule that holds up to 30rem of it holds on every phone.
 */
const onANarrowScreen = (className: string) =>
  STYLES.filter((rule) => isFor(rule.selector, className) && /^@container \(max-width:\s*(30|40)rem\)$/.test(rule.under ?? ""));

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
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";

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
  /** Where every area sits on every vibe, where the page hands it down. */
  bands?: readonly VibeBands[];
  /** The release the list is handed, where it is another than the one that was recorded. */
  form?: MetaData;
  /** The calls of the look of a town on a result, where a test makes one the page does not. */
  townDrawn?: TownDrawn;
  lineStands?: LineStands;
  onANarrowResult?: OnANarrowResult;
  inviteStands?: InviteStands;
  over?: OverTheList;
  buttons?: OnANarrowResultAButtonIs;
  ends?: EndsOnAResult;
  tradeOff?: TradeOffDrawn;
  others?: OthersStand;
  fitSaid?: FitSaid;
  /**
   * What is opened once the list is drawn: the working of every result that is on
   * screen, which is what most of these tests are of. `false` leaves the list as a
   * person first finds it.
   */
  opened?: boolean;
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
  placeNames,
  waitingForFirst = false,
  bands,
  form = meta.data,
  townDrawn,
  lineStands,
  onANarrowResult,
  inviteStands,
  over,
  buttons,
  ends,
  tradeOff,
  others,
  fitSaid,
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
      meta={form}
      served={meta.meta}
      // Every answer names every place of its spec.
      placeNames={placeNames ?? Object.fromEntries(ranking.places.map((place) => [place.place_id, place.name]))}
      noFit={ranking.empty_spec}
      unranked={ranking.unranked}
      areasRanked={ranking.areas_ranked}
      areasListed={ranking.areas_listed}
      busy={busy}
      selectedId={selectedId}
      bands={bands}
      townDrawn={townDrawn}
      lineStands={lineStands}
      onANarrowResult={onANarrowResult}
      inviteStands={inviteStands}
      over={over}
      buttons={buttons}
      ends={ends}
      tradeOff={tradeOff}
      others={others}
      fitSaid={fitSaid}
      {...told}
    />
  );
  return { element, told };
}

function show(shown: Shown) {
  const { element, told } = listOf(shown);
  const view = render(element);
  if (shown.opened !== false) {
    const more = screen.queryByRole("button", { name: /^Show \d+ more$/ });
    if (more !== null) fireEvent.click(more);
    for (const working of screen.queryAllByRole("button", { name: /^Show the working: / })) fireEvent.click(working);
  }
  return { ...told, user: userEvent.setup({ delay: null }), ...view };
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
/** A search whose third result has no figure for one of the things that count. */
const money = {
  ranking: recordedAnswer("rank", "rank-money-and-work").body.data,
  ...recordedAnswer("explain_top", "explanations-money-and-work").body.data,
};
/** Where an area with a figure for everything stands in the list of the first search. */
const FARROWMERE = 0;
/** Where an area with no figure for one thing stands in the list of the search by money and work. */
const MARROWFEN = 2;
/** The working of a result: what "Show the working" opens. */
const working = (at: number) =>
  document.getElementById(
    card(at).getByRole("button", { name: /^Show the working: / }).getAttribute("aria-controls") ?? "",
  ) as HTMLElement;
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

    expect(lists().map((list) => list.tagName)).toEqual(["OL", "OL"]);
    // The first result, and then the rest of them, which say that they begin at the second.
    expect(lists().map((list) => list.getAttribute("aria-label"))).toEqual([RESULTS.listLabel, RESULTS.restLabel]);
    expect(lists().map((list) => list.getAttribute("start"))).toEqual([null, "2"]);
    expect(lists().map((list) => list.children.length)).toEqual([1, first.ranking.ranked.length - 1]);
    expect(lists().flatMap((list) => [...list.children].map((item) => item.getAttribute("data-area")))).toEqual(
      first.ranking.ranked.map((area) => area.area_id),
    );
    expect(cards().map((one) => within(one).getAllByText(/^Rank \d+$/)[0]?.textContent)).toEqual(
      first.ranking.ranked.map((area) => `Rank ${area.rank}`),
    );
  });

  test("test_the_name_of_a_result_leads_to_the_page_of_its_area_in_one_press", () => {
    // Seen in a browser: the name of a result was plain text. The way to its page was at
    // the foot of its working, four presses and a scroll from arriving.
    show({ ...first, opened: false });

    const names = cards().map((one) => within(one).getByRole("heading", { level: 3 }));
    expect(names.map((name) => within(name).getByRole("link").getAttribute("href"))).toEqual(
      first.ranking.ranked.slice(0, SHOWN_AT_FIRST).map((area) => `/synthetic/${slugOf(area.area_id)}`),
    );
    for (const name of names) {
      const link = within(name).getByRole("link");
      // The link is the name, and nothing more: the card is still named by its heading.
      expect(link.textContent).toBe(name.textContent);
      // Which page a person reads next is told to no server ahead of time.
      expect(link).toHaveAttribute("data-prefetch", "false");
      expect(link.className).toMatch(/\btarget-min\b/);
    }
  });

  test("test_the_first_five_are_cards_with_a_trade_off_and_their_reasons_one_press_away_and_the_rest_are_rows", () => {
    show({ ...first, opened: false });

    const withATradeOff = cards().filter((one) => within(one).queryByRole("heading", { name: RESULTS.tradeOffTitle }));
    expect(withATradeOff).toHaveLength(5);
    expect(withATradeOff).toEqual(cards().slice(0, 5));
    for (const row of cards().slice(5)) {
      expect(within(row).getByRole("button", { name: /^Show the working: / })).toBeInTheDocument();
    }
    // Why an area fits is written for the first five, and is in the working of each.
    for (const opens of screen.getAllByRole("button", { name: /^Show the working: / })) fireEvent.click(opens);
    const withReasons = cards().filter((one) => within(one).queryByRole("heading", { name: RESULTS.reasonsTitle }));
    expect(withReasons).toEqual(cards().slice(0, 5));
  });

  test("test_ten_results_are_shown_at_first_and_a_button_shows_the_rest", async () => {
    const { user } = show({ ...first, opened: false });

    expect(SHOWN_AT_FIRST).toBe(10);
    expect(cards()).toHaveLength(10);
    await user.click(screen.getByRole("button", { name: RESULTS.showMore(10) }));

    expect(cards()).toHaveLength(20);
    expect(cards().map((one) => within(one).getAllByText(/^Rank \d+$/)[0]?.textContent).slice(10)).toEqual(
      first.ranking.ranked.slice(10).map((area) => `Rank ${area.rank}`),
    );
    // The button has gone, and the focus has gone to the list it added to, and not to nothing.
    expect(screen.queryByRole("button", { name: /^Show \d+ more$/ })).toBeNull();
    expect(screen.getByRole("list", { name: RESULTS.restLabel })).toHaveFocus();
  });

  test("test_a_list_of_ten_or_fewer_has_no_more_to_show", () => {
    show({ ...two, opened: false });

    expect(two.ranking.ranked).toHaveLength(1);
    expect(screen.queryByRole("button", { name: /^Show \d+ more$/ })).toBeNull();
  });

  test("test_an_area_chosen_from_the_map_that_is_not_among_the_first_ten_is_shown_in_the_list", () => {
    const chosen = first.ranking.ranked[14]?.area_id ?? "";
    show({ ...first, opened: false, selectedId: chosen });

    expect(cards()).toHaveLength(20);
    expect(cards().filter((one) => one.getAttribute("aria-current") === "true")).toEqual([cards()[14]]);
  });

  test("test_under_the_list_is_said_which_results_have_reasons_and_which_release_ranked_them", () => {
    show({ ...first, opened: false });
    const foot = screen.getByRole("contentinfo");

    // Once, under the list, and not on every card.
    expect(within(foot).getByText(RESULTS.firstFive)).toBeInTheDocument();
    expect(within(foot).getByText(meta.meta.release_id)).toBeInTheDocument();
    expect(within(foot).getByText(meta.meta.engine_version)).toBeInTheDocument();
    expect(screen.getAllByText(meta.meta.release_id)).toHaveLength(1);
  });

  test("test_a_list_being_worked_out_again_stays_and_says_it_is_busy", () => {
    show({ ...first, busy: true });

    expect(lists().map((list) => list.getAttribute("aria-busy"))).toEqual(["true", "true"]);
    expect(cards()).toHaveLength(20);
  });

  test("test_a_list_being_worked_out_again_says_so_in_words_that_can_be_seen", () => {
    const { rerender } = show({ ...first, busy: true, opened: false });

    // It is said in words, and not by dimming: dimmed, the text falls below the contrast it needs.
    const words = screen.getByText(RESULTS.working);
    expect(words.closest("[aria-hidden='true'], .visually-hidden, [hidden]")).toBeNull();
    // The words are above the list, so that they are read before it.
    const list = screen.getByRole("list", { name: RESULTS.listLabel });
    expect(words.compareDocumentPosition(list) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // The state is said once: the line in the form is the one that is announced.
    expect(words.closest("[role='status'], [role='alert'], [aria-live]")).toBeNull();

    rerender(listOf({ ...first, busy: false }).element);

    expect(screen.queryByText(RESULTS.working)).toBeNull();
  });

  test("test_a_first_search_that_is_waited_for_is_not_said_to_be_worked_out_again", () => {
    render(listOf({ ...first, busy: true, waitingForFirst: true }).element);

    expect(screen.queryByText(RESULTS.working)).toBeNull();
  });
});

describe("what stands under the list", () => {
  const refined = { ranking: recordedAnswer("rank", "rank-refined").body.data };

  test("test_the_list_says_when_areas_are_ranked_below_the_last_one_listed", async () => {
    // Seen in a browser: 22 areas ranked, 20 listed, and no line and no button said so.
    const { user } = show({ ...first, opened: false });
    const { areas_ranked: ranked, areas_listed: listed } = first.ranking;

    expect([ranked, listed]).toEqual([21, 20]);
    // While a button still shows more, the button is what says that there is more.
    expect(screen.queryByText(RESULTS.listed(listed, ranked))).toBeNull();
    await user.click(screen.getByRole("button", { name: RESULTS.showMore(10) }));

    expect(cards()).toHaveLength(listed);
    expect(screen.getByText(RESULTS.listed(listed, ranked))).toBeInTheDocument();
    expect(RESULTS.listed(listed, ranked)).toContain("20 of the 21");
  });

  test("test_nothing_is_said_of_more_where_every_area_that_is_ranked_is_listed", () => {
    show(refined);

    expect([refined.ranking.areas_ranked, refined.ranking.areas_listed]).toEqual([10, 10]);
    expect(cards()).toHaveLength(10);
    expect(screen.queryByText(/areas ranked are listed/)).toBeNull();
  });

  test("test_the_areas_that_are_not_ranked_stand_after_the_list_and_never_in_it", async () => {
    const { user } = show(first);
    const apart = first.ranking.unranked.map((area) => area.area_id);

    expect(apart).toHaveLength(3);
    expect(cards().map((one) => one.closest("li")?.getAttribute("data-area")).filter((id) => apart.includes(id ?? ""))).toEqual([]);
    const button = screen.getByRole("button", { name: APART.title(3) });
    const last = lists().at(-1) as HTMLElement;
    expect(last.compareDocumentPosition(button) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    await user.click(button);

    expect(screen.getByRole("list", { name: APART.label })).toHaveTextContent("Otterby Fields");
    // It is no result: it has no rank, no fit and no card.
    expect(cards().some((one) => one.textContent?.includes("Otterby Fields"))).toBe(false);
  });

  test("test_the_areas_that_are_not_ranked_are_drawn_once_though_the_list_is_drawn_in_two_parts", () => {
    show({ ...first, opened: false });

    expect(screen.getAllByRole("button", { name: APART.title(3) })).toHaveLength(1);
  });
});

describe("a result, in short", () => {
  test("test_a_result_holds_its_heading_a_line_for_each_thing_asked_for_its_trade_off_and_two_ways_on_and_no_more", () => {
    // The founder, who had walked the website three times: "Again, we don't need to over
    // complicate and bloat with too much info." Counted in a browser before: the first
    // result of a plain search held 124 words, nine things to press and five pictures.
    show({ ...first, opened: false });
    const given = first.explanations.find((one) => one.area_id === "syn-n0006");

    cards()
      .slice(0, 5)
      .forEach((result, at) => {
        const answer = result.firstElementChild as HTMLElement;
        // Its heading, its lines, its trade-off and its ways on, in that order, and nothing else.
        expect([at, [...answer.children].map((part) => part.className.split(" ")[0])]).toEqual([at, ["top", "strip", "tradeOff", "waysOn"]]);
        expect([at, [...(answer.querySelector(".top") as HTMLElement).children].map((part) => part.tagName)]).toEqual([at, ["HEADER"]]);
        // It is named twice: by the name of its area, and by the word over what it gives up.
        expect([at, within(result).getAllByRole("heading").map((heading) => heading.tagName)]).toEqual([at, ["H3", "H4"]]);
        expect([at, within(result).queryByRole("heading", { name: RESULTS.reasonsTitle })]).toEqual([at, null]);
        // Four things to press: the name, the way to compare, the working, and more like this.
        expect([at, within(result).getAllByRole("link").length + within(result).getAllByRole("button").length]).toEqual([at, 4]);
        // Its pictures are its gauges and the town of its area.
        const lines = within(result).getAllByRole("listitem");
        expect([at, within(result).getAllByRole("img").length]).toEqual([at, lines.length + 1]);
      });

    const farrowmere = cards()[FARROWMERE] as HTMLElement;
    // Rank, name, the label beside it and fit. A line for each of the two vibes that were
    // asked for. The trade-off.
    expect(within(farrowmere).getByRole("heading", { level: 3, name: "Farrowmere" })).toBeInTheDocument();
    expect(within(farrowmere).getByText("Quillhaven 006")).toBeInTheDocument();
    expect(within(farrowmere).getByText("71 of 100")).toBeInTheDocument();
    expect(within(within(farrowmere).getByRole("list", { name: STRIP.label("Farrowmere") })).getAllByRole("listitem")).toHaveLength(2);
    expect(within(farrowmere).getByText(given?.trade_off?.text ?? "no trade-off")).toBeInTheDocument();
    // Under its heading it says the name of each thing that was asked for, the sentence of
    // its trade-off under its word, and the names of its two buttons, and no word more.
    const [, lines, gives, ways] = [...(farrowmere.firstElementChild as HTMLElement).children];
    expect([lines?.textContent, said(gives), ways?.textContent]).toEqual([
      "LeafyQuiet streets",
      `${RESULTS.tradeOffTitle}${given?.trade_off?.text}`,
      `${RESULTS.showWorking}${RESULTS.moreLike}`,
    ]);
    // Every reason, and everything else, waits for the working to be opened.
    expect(given?.reasons).toHaveLength(3);
    for (const reason of given?.reasons ?? []) expect(within(farrowmere).queryByText(reason.text)).toBeNull();
    expect(within(farrowmere).queryByText(given?.orientation.text ?? "none")).toBeNull();
    expect(within(farrowmere).queryAllByRole("table")).toEqual([]);
    // Where the area is on the map is in the working.
    expect(within(farrowmere).queryAllByRole("img", { name: /^Where / })).toEqual([]);
    expect(farrowmere.querySelectorAll("svg")).toHaveLength(0);
    expect(within(farrowmere).queryByRole("heading", { name: COST.title })).toBeNull();
    expect(within(farrowmere).queryByRole("heading", { name: JOURNEYS.title })).toBeNull();
  });

  test("test_no_key_of_a_source_stands_on_a_result_as_it_is_first_shown_and_every_figure_has_its_source_one_press_away", async () => {
    // The founder: "the source's key should just exist under the show the working section
    // we dont need it at the summary high level card version". It is a promise of the
    // product that every figure a person is shown traces to a fact with a source and a
    // date. It still does, one press away.
    const { user } = show({ ...first, opened: false });

    expect(cards()).toHaveLength(SHOWN_AT_FIRST);
    for (const result of cards()) {
      expect(within(result).queryAllByRole("button", { name: /^Source/ })).toEqual([]);
      expect(within(result).queryAllByRole("link", { name: /^Source/ })).toEqual([]);
      expect(result.querySelector("[style*='ui-key']")).toBeNull();
    }
    for (const opens of screen.getAllByRole("button", { name: /^Show the working: / })) await user.click(opens);

    first.ranking.ranked.slice(0, 5).forEach((area, at) => {
      const name = nameOf(area.area_id);
      const given = first.explanations.find((one) => one.area_id === area.area_id);
      const sources = within(working(at)).getAllByRole("button", { name: /^Source/ }).map((key) => key.getAttribute("aria-label"));
      // Of what stands on the result: the band of each gauge, and the figure of the trade-off.
      const onTheResult = within(cards()[at]?.firstElementChild as HTMLElement).getAllByRole("listitem").map((line) => said(line.querySelector("[class*='name']")));
      expect(onTheResult.length).toBeGreaterThan(0);
      const ofTheTradeOff = first.facts.find((fact) => fact.fact_id === given?.trade_off?.fact_ids[0]);
      for (const vibe of onTheResult) {
        // A vibe that the trade-off is about has its source under the trade-off.
        expect([at, vibe, sources.includes(SOURCE.buttonFor(vibe)) || ofTheTradeOff?.label === vibe]).toEqual([at, vibe, true]);
      }
      expect([at, sources.includes(SOURCE.buttonFor(RESULTS.sourceOfTradeOff(name)))]).toEqual([at, given?.trade_off !== null]);
      // And of every reason, which a result no longer says.
      (given?.reasons ?? []).forEach((_, nth) => {
        expect([at, nth, sources.includes(SOURCE.buttonFor(RESULTS.sourceOfReason(nth + 1, name)))]).toEqual([at, nth, true]);
      });
    });
    // The source of the trade-off opens in place, with its name, its date and that the data is made up.
    const key = within(working(FARROWMERE)).getByRole("button", { name: SOURCE.buttonFor(RESULTS.sourceOfTradeOff("Farrowmere")) });
    const about = first.facts.find((fact) => fact.fact_id === first.explanations[FARROWMERE]?.trade_off?.fact_ids[0]);
    const part = within(working(FARROWMERE)).getByRole("heading", { name: CARD.sourceOfTheTradeOff }).parentElement as HTMLElement;
    expect(part.contains(key)).toBe(true);
    // The part names what the trade-off is about, as the API names it, and says no figure of it a second time.
    expect(said(part)).toBe(`${CARD.sourceOfTheTradeOff}${about?.label}${SOURCE.button}`);
    await user.click(key);
    expect(within(part).getByRole("link", { name: "Synthetic test data" })).toHaveAttribute("href", "/sources#synthetic");
    expect(within(part).getByText(SOURCE.madeUp)).toBeInTheDocument();
    expect(part.textContent?.includes(SOURCE.dataFrom)).toBe(true);
  });

  test("test_a_result_leads_to_its_working_to_what_is_like_it_and_to_the_comparison", () => {
    show({ ...first, opened: false });

    for (const at of [0, 1, 4, 5, 9]) {
      const name = areas.find((area) => area.area_id === first.ranking.ranked[at]?.area_id);
      const ways = [...(cards()[at]?.querySelectorAll("[class*='waysOn'] > *") ?? [])];
      expect(card(at).getByRole("button", { name: RESULTS.workingOf(name?.name ?? "") })).toHaveTextContent(
        RESULTS.showWorking,
      );
      const like = card(at).getByRole("link", { name: RESULTS.moreLikeOf(name?.name ?? "") });
      expect(like).toHaveTextContent(RESULTS.moreLike);
      // The areas most like it are on its own page, which is fetched when the link is pressed and not before.
      expect(like).toHaveAttribute("href", `/synthetic/${name?.slug}#alike`);
      expect(like).toHaveAttribute("data-prefetch", "false");
      expect(card(at).getByRole("button", { name: COMPARE.addNamed(name?.name ?? "") })).toHaveTextContent(
        COMPARE.addShort,
      );
      // Two of the three stand at the foot of the result. The way to compare stands in its heading.
      expect(ways.length).toBe(2);
    }
  });

  test("test_the_way_to_compare_stands_in_the_heading_of_every_result_beside_its_town_and_not_at_its_foot", () => {
    // The founder: "Compare function is great, make this more of a highlighted feature". It
    // was the third of three buttons at the foot of a result, and a person might never find it.
    show({ ...first, opened: false });

    expect(cards()).toHaveLength(SHOWN_AT_FIRST);
    cards().forEach((result, at) => {
      const name = nameOf(first.ranking.ranked[at]?.area_id ?? "");
      const heading = result.querySelector("header") as HTMLElement;
      const way = within(result).getByRole("button", { name: COMPARE.addNamed(name) });
      const town = heading.querySelector("figure") as HTMLElement;
      const fit = heading.querySelector("p.fit") as HTMLElement;

      // A card and a row alike: the first result as the tenth.
      expect([at, heading.contains(way)]).toEqual([at, true]);
      expect([at, way.closest("[class*='waysOn']")]).toEqual([at, null]);
      // It is read after the name and the fit, and the town is the next thing of the result
      // after it, in the first result as in every other: nothing stands between the two.
      expect(Boolean(fit.compareDocumentPosition(way) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
      expect(Boolean(way.compareDocumentPosition(town) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
      const follows = [];
      for (let next = way.closest("[data-chosen]")?.parentElement?.nextElementSibling; next; next = next.nextElementSibling) follows.push(next);
      expect([at, follows.map((one) => (one === town ? "the town" : one.textContent))]).toEqual([at, ["the town"]]);
      // It says what it does, in the words of a button, and is a control of the browser's own.
      expect(way.tagName).toBe("BUTTON");
      expect(way).toHaveTextContent(new RegExp(`^${COMPARE.addShort}$`));
      expect(way).toBeEnabled();
    });
  });

  test("test_the_way_to_compare_is_drawn_the_same_on_every_result_because_nobody_wins", () => {
    show({ ...first, opened: false });
    const ways = cards().map((result, at) =>
      within(result).getByRole("button", { name: COMPARE.addNamed(nameOf(first.ranking.ranked[at]?.area_id ?? "")) }),
    );

    // One drawing, one size and one colour, whatever the rank and the fit of the result.
    expect(new Set(ways.map((way) => way.className)).size).toBe(1);
    expect(new Set(ways.map((way) => way.querySelector("[data-kind]")?.getAttribute("data-kind")))).toEqual(new Set(["plain"]));
    expect(new Set(ways.map((way) => way.textContent))).toEqual(new Set([COMPARE.addShort]));
    // No rule of the sheet draws the way to compare of one result otherwise than the next.
    const counting = STYLES.filter((rule) => /data-chosen/.test(rule.selector) && /:(first|last|nth)-|-of-type/.test(rule.selector));
    expect(counting.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_once_its_area_is_chosen_the_way_to_compare_says_so_in_amber_and_leads_on", async () => {
    const user = userEvent.setup({ delay: null });
    render(<SessionProvider>{listOf({ ...first, opened: false }).element}</SessionProvider>);
    const [one, two] = [0, 1].map((at) => nameOf(first.ranking.ranked[at]?.area_id ?? ""));

    await user.click(card(0).getByRole("button", { name: COMPARE.addNamed(one ?? "") }));

    const chosen = card(0).getByRole("button", { name: COMPARE.removeNamed(one ?? "") });
    expect(chosen).toHaveTextContent(new RegExp(`^${COMPARE.removeShort}$`));
    expect(chosen.querySelector("[data-kind]")).toHaveAttribute("data-kind", "on");
    // While it is the only one chosen nothing stands beside it, so that the head of the result
    // is as high pressed as it was: the bar of areas says what to do next.
    expect([...(chosen.parentElement as HTMLElement).children]).toEqual([chosen]);
    expect(card(0).queryByRole("link", { name: /^Compare \d areas$/ })).toBeNull();

    await user.click(card(1).getByRole("button", { name: COMPARE.addNamed(two ?? "") }));

    for (const at of [0, 1]) {
      const near = card(at).getByRole("link", { name: TRAY.go(2) });
      expect(near.closest("header")).not.toBeNull();
      expect(near).toHaveAttribute("data-prefetch", "false");
    }
    // A press takes it out again.
    await user.click(chosen);
    expect(card(0).getByRole("button", { name: COMPARE.addNamed(one ?? "") })).toBeInTheDocument();
    expect(card(0).queryByRole("link", { name: /^Compare \d areas$/ })).toBeNull();
  });

  test("test_the_button_that_fills_the_comparison_says_what_it_does_in_words_that_are_in_its_name", () => {
    // What is seen on a button must be in the name a person speaks to press it, as it is seen.
    expect(COMPARE.addNamed("Farrowmere").startsWith(COMPARE.addShort)).toBe(true);
    expect(COMPARE.removeNamed("Farrowmere").startsWith(COMPARE.removeShort)).toBe(true);
    expect(RESULTS.workingOf("Farrowmere").startsWith(RESULTS.showWorking)).toBe(true);
    expect(RESULTS.moreLikeOf("Farrowmere").startsWith(RESULTS.moreLike)).toBe(true);
  });

  test("test_show_the_working_opens_the_result_in_place_and_closes_no_other", async () => {
    const { user } = show({ ...first, opened: false });
    const open = (at: number) => card(at).getByRole("button", { name: /^Show the working: / });

    await user.click(open(FARROWMERE));
    expect(open(FARROWMERE)).toHaveAttribute("aria-expanded", "true");
    expect(within(working(FARROWMERE)).getByRole("heading", { name: COST.title })).toBeInTheDocument();
    expect(cards()[FARROWMERE]?.contains(working(FARROWMERE))).toBe(true);

    await user.click(open(3));

    expect(open(FARROWMERE)).toHaveAttribute("aria-expanded", "true");
    expect(open(3)).toHaveAttribute("aria-expanded", "true");
    expect(open(1)).toHaveAttribute("aria-expanded", "false");
  });

  test("test_the_lines_of_a_result_are_the_vibes_that_were_asked_for_in_the_order_the_api_gave_them", () => {
    show({ ...first, opened: false });

    first.ranking.ranked.slice(0, 10).forEach((area, at) => {
      const name = areas.find((one) => one.area_id === area.area_id)?.name ?? "";
      const asked = area.strip.filter((mark) => mark.asked);
      const marks = within(card(at).getByRole("list", { name: STRIP.label(name) })).getAllByRole("listitem");
      // The picture of each mark says its band in words.
      expect(marks.map((mark) => within(mark).getByRole("img").getAttribute("aria-label")?.split(",")[0])).toEqual(
        asked.map((mark) => inWords(mark)),
      );
      expect(marks.map((mark) => said(mark.querySelector("[class*='name']")))).toEqual(
        asked.map((mark) => meta.data.tags.find((tag) => tag.tag_id === mark.tag_id)?.label),
      );
      // Each is drawn once, whatever the trade-off is about. The one picture more is the
      // town of the area, which stands in the heading.
      expect(card(at).getAllByRole("img")).toHaveLength(asked.length + 1);
      expect(marks.flatMap((mark) => within(mark).queryAllByRole("img", { name: new RegExp(`^${TOWN.name}`) }))).toEqual([]);
    });
    // Recorded: the first result has a band on the two vibes asked for, and on two others.
    expect(first.ranking.ranked[FARROWMERE]?.strip.map((mark) => mark.asked)).toEqual([true, true, false, false]);
    expect(first.ranking.ranked[FARROWMERE]?.strip.map((mark) => mark.tag_id)).toEqual([
      "leafy",
      "quiet_residential",
      "built_age",
      "homes",
    ]);
  });

  test("test_the_vibes_nobody_asked_for_stand_on_a_result_only_where_no_vibe_was_asked_for_and_are_in_the_working_of_every_card", () => {
    // A result holds a line for each thing that was asked for. The service gives two more
    // vibes at the most with every result, those its area sits at an end of: on a phone
    // they gave way to what was asked for, and on a desk they stood under it. They give
    // way at every width, so that a phone and a desk draw one result of one answer.
    const { unmount } = show({ ...first, opened: false });
    const drawn = (at: number, name: string) =>
      within(card(at).getByRole("list", { name: STRIP.label(name) }))
        .getAllByRole("listitem")
        .map((line) => said(line.querySelector("[class*='name']")));
    const labelOf = (tagId: string) => meta.data.tags.find((tag) => tag.tag_id === tagId)?.label ?? "";

    expect(OTHERS_STAND).toBe("alone");
    expect(OTHERS_MAY_STAND).toEqual(["alone", "beside", "never"]);
    expect(drawn(FARROWMERE, "Farrowmere")).toEqual(["Leafy", "Quiet streets"]);
    // No word tells one kind of line from another, since a result holds one kind.
    expect(cards().some((one) => one.textContent?.includes(STRIP.group.asked) || one.textContent?.includes(STRIP.group.also))).toBe(false);
    unmount();

    // Where no vibe was asked for a result holds the vibes the service chose, so that it is never without a gauge.
    const none = show({ ...money, opened: false });
    expect(money.ranking.spec.tags).toEqual([]);
    money.ranking.ranked.slice(0, SHOWN_AT_FIRST).forEach((area, at) => {
      expect([at, drawn(at, nameOf(area.area_id))]).toEqual([at, area.strip.map((mark) => labelOf(mark.tag_id))]);
      expect([at, area.strip.length > 0]).toEqual([at, true]);
    });
    expect(cards().some((one) => one.textContent?.includes(STRIP.group.also))).toBe(false);
    none.unmount();

    // One line of the look has them stand beside what was asked for, each run under its word, as a desk drew them.
    const beside = show({ ...first, opened: false, others: "beside" });
    expect(drawn(FARROWMERE, "Farrowmere")).toEqual(["Leafy", "Quiet streets", "Age of buildings", "Houses or flats"]);
    expect(within(cards()[FARROWMERE] as HTMLElement).getByText(STRIP.group.asked)).toHaveAttribute("aria-hidden", "true");
    expect(within(cards()[FARROWMERE] as HTMLElement).getByText(STRIP.group.also)).toHaveAttribute("aria-hidden", "true");
    beside.unmount();

    // Another has them stand on no result: a result then holds what was asked for and no
    // other line, and none at all where no vibe was asked for.
    const never = show({ ...first, opened: false, others: "never" });
    expect(drawn(FARROWMERE, "Farrowmere")).toEqual(["Leafy", "Quiet streets"]);
    never.unmount();
    const bare = show({ ...money, opened: false, others: "never" });
    expect(cards().flatMap((one) => within(one).queryAllByRole("list"))).toEqual([]);
    expect(cards().flatMap((one) => within(one).queryAllByRole("img").filter((picture) => picture.closest("figure") === null))).toEqual([]);
    expect(columnOf(money.ranking.ranked, meta.data, money.ranking.spec, "never", "working")).toEqual([]);
    bare.unmount();

    // Whichever is chosen, each of them is in the working of a card, with its source.
    show(first);
    for (const vibe of ["Leafy", "Quiet streets", "Age of buildings", "Houses or flats"]) {
      const figures = within(working(FARROWMERE)).getByRole("heading", { name: CARD.vibes }).parentElement as HTMLElement;
      expect(within(figures).getByRole("group", { name: vibe })).toBeInTheDocument();
      expect(within(figures).getByRole("button", { name: SOURCE.buttonFor(vibe) })).toBeInTheDocument();
    }
  });

  test("test_no_line_of_a_result_opens_and_the_fact_of_each_is_in_the_working_of_a_card_with_its_source", async () => {
    const { user } = show({ ...first, opened: false });
    const strip = (at: number, name: string) => within(card(at).getByRole("list", { name: STRIP.label(name) }));

    // A line is its name and its gauge, and is pressed by nobody: a card as a row.
    expect(strip(FARROWMERE, "Farrowmere").queryAllByRole("button")).toEqual([]);
    expect(strip(5, "Dulcimer Green").queryAllByRole("button")).toEqual([]);
    // The API sends the fact of every mark of the first five, with the reasons.
    await user.click(card(FARROWMERE).getByRole("button", { name: /^Show the working: / }));
    const leafy = first.facts.find((fact) => fact.fact_id === "syn-n0006/tag/leafy");
    const figures = within(within(working(FARROWMERE)).getByRole("group", { name: "Leafy" }));
    expect(figures.getByText(leafy?.slots.judgement ?? "none")).toBeInTheDocument();
    expect(figures.getByText(leafy?.slots.band ?? "none")).toBeInTheDocument();
    // A row has no fact in hand, so its working says nothing in the words of one.
    await user.click(card(5).getByRole("button", { name: /^Show the working: / }));
    expect(within(working(5)).queryByText(leafy?.slots.judgement ?? "none")).toBeNull();
  });

  test("test_the_working_of_a_row_names_every_gauge_of_the_row_and_leads_to_the_page_that_holds_the_source_of_each", async () => {
    // Seen in a browser: a row drew a gauge for every vibe that was asked for, and its
    // working gave the source of its journey and of nothing else. The key of a source
    // stands in the working alone, so the band of a row led to no source at all. It is a
    // promise of the product that every figure a person is shown traces to a fact with a
    // source and a date.
    const { user } = show({ ...first, opened: false });
    const ROWS = [5, 9];
    for (const at of ROWS) await user.click(card(at).getByRole("button", { name: /^Show the working: / }));

    for (const at of ROWS) {
      const area = first.ranking.ranked[at] as RankedArea;
      const name = nameOf(area.area_id);
      const figures = within(working(at)).getByRole("heading", { name: CARD.vibes }).parentElement as HTMLElement;
      const onTheRow = within(card(at).getByRole("list", { name: STRIP.label(name) }))
        .getAllByRole("listitem")
        .map((line) => said(line.querySelector("[class*='name']")));
      const named = within(figures).getAllByRole("group").map((group) => group.getAttribute("aria-label"));

      // Every gauge the row draws is among them, and so is every other the service gave with the result.
      expect(onTheRow.length).toBeGreaterThan(0);
      for (const vibe of onTheRow) expect([at, vibe, named.includes(vibe)]).toEqual([at, vibe, true]);
      expect(named).toEqual(area.strip.map((mark) => meta.data.tags.find((tag) => tag.tag_id === mark.tag_id)?.label));
      // Each says what the ranking gave of it, laid out as its fact is, and nothing the page does not hold.
      for (const mark of area.strip) {
        const tag = meta.data.tags.find((one) => one.tag_id === mark.tag_id);
        const ends = `${tag?.low_end ?? STRIP.least} ${FACT_COLUMNS.to} ${tag?.high_end ?? STRIP.most}`;
        const band =
          mark.spread_high - mark.spread_low >= 2
            ? `${FACT_COLUMNS.bands}${mark.spread_low} ${FACT_COLUMNS.to} ${mark.spread_high}`
            : `${FACT_COLUMNS.band}${mark.band}`;
        expect(said(within(figures).getByRole("group", { name: tag?.label ?? "none" }))).toBe(
          `${tag?.label}${band}${FACT_COLUMNS.ends}${ends}`,
        );
      }
      // One way leads to where the source and the date of each stand: the page of the area.
      const way = within(figures).getByRole("link");
      expect(way).toHaveAccessibleName(CARD.sourcesOn(name));
      expect(way).toHaveAttribute("href", `/synthetic/${slugOf(area.area_id)}`);
      // Which page a person reads next is told to no server ahead of time.
      expect(way).toHaveAttribute("data-prefetch", "false");
      expect(way.className).toMatch(/\btarget-min\b/);
      // It is drawn with the key, as the source of a figure is wherever one stands.
      expect(way.parentElement?.querySelector("[style*='ui-key']")).not.toBeNull();
      // No key opens on nothing.
      expect(within(figures).queryAllByRole("button")).toEqual([]);
    }
    expect(CARD.sourcesOn("Somewhere")).toBe("See the source and the date of each figure on the page for Somewhere");
  });

  test("test_the_working_of_a_row_gives_the_key_of_a_source_in_place_wherever_the_fact_of_a_gauge_is_in_hand", async () => {
    // An area that stood among the first five of another search has its facts in hand.
    const every = areas.flatMap((area) => profile(area.slug).facts);
    const { user } = show({ ...first, facts: every, opened: false });
    const area = first.ranking.ranked[5] as RankedArea;
    await user.click(card(5).getByRole("button", { name: /^Show the working: / }));

    const figures = within(working(5)).getByRole("heading", { name: CARD.vibes }).parentElement as HTMLElement;
    for (const mark of area.strip) {
      const fact = every.find((one) => one.fact_id === mark.fact_id);
      expect(within(figures).getByRole("button", { name: SOURCE.buttonFor(fact?.label ?? "none") })).toBeInTheDocument();
    }
    // Nothing leads away where every source opens in place.
    expect(within(figures).queryAllByRole("link")).toEqual([]);
  });

  test("test_a_card_whose_facts_did_not_come_names_its_gauges_all_the_same_and_waits_for_those_that_may_yet_come", () => {
    // Where the reasons and the profile of an area both failed, its working held nothing of
    // its gauges, which stood on the card with no source.
    const failed = first.ranking.ranked.slice(0, 5).map((area) => area.area_id);
    const name = nameOf(first.ranking.ranked[FARROWMERE]?.area_id ?? "");
    const lost = show({ ...first, explanations: [], facts: [], explained: false, explainFailed: true, withDetails: false, detailsFailed: failed });
    const figures = () => within(working(FARROWMERE)).getByRole("heading", { name: CARD.vibes }).parentElement as HTMLElement;

    expect(within(figures()).getAllByRole("group")).toHaveLength(first.ranking.ranked[FARROWMERE]?.strip.length ?? 0);
    expect(within(figures()).getByRole("link")).toHaveAccessibleName(CARD.sourcesOn(name));
    lost.unmount();

    // While either is waited for, the place of each is held, and nothing leads away yet.
    show({ ...first, explanations: [], facts: [], explained: false, withDetails: false });
    expect(within(figures()).queryAllByRole("link")).toEqual([]);
    expect(within(figures()).queryAllByRole("group")).toEqual([]);
    expect(figures().querySelectorAll(".skeleton")).toHaveLength(first.ranking.ranked[FARROWMERE]?.strip.length ?? 0);
  });

  test("test_a_row_says_beside_its_name_what_a_card_says_the_borough_and_that_the_name_is_a_draft", () => {
    // Seen in a browser: the first five results said their borough and that the name was a
    // draft, and results six to ten gave a name alone. A name with nothing beside it was
    // taken for one somebody had checked.
    show({ ...first, opened: false });
    const ranked = first.ranking.ranked.slice(0, SHOWN_AT_FIRST);

    expect(cards()).toHaveLength(SHOWN_AT_FIRST);
    cards().forEach((result, at) => {
      const summary = areas.find((area) => area.area_id === ranked[at]?.area_id);
      const heading = result.querySelector("header") as HTMLElement;
      const [rank, beside, fit, ...more] = [...heading.querySelectorAll("p")].map((part) => part.textContent);
      const whole = ranked[at]?.contributions.every((part) => part.present);
      expect(within(heading).getByRole("heading", { level: 3 }).textContent).toBe(summary?.name);
      expect(rank).toMatch(/^Rank \d+\d+$/);
      // The label its publisher gives the area begins with its borough.
      expect(summary?.named?.label.startsWith(`${summary.borough} `)).toBe(true);
      expect(beside).toBe(`${summary?.named?.label}${NAMED.between}${NAMED.draft}`);
      // With the fit, where it is not whole, stand the two words that say so.
      expect(fit).toMatch(whole ? /^Fit \d+ of 100$/ : new RegExp(`^Fit \\d+ of 100${KNOWN.some}$`));
      // A heading says no more, the first as the tenth: what a town is, is said on no result.
      expect([at, more]).toEqual([at, []]);
    });
  });

  test("test_the_heading_of_a_row_has_a_line_of_its_own_so_that_the_ways_on_stand_together", () => {
    // With the borough beside the name there was room on the line for one of the three
    // ways on, and the other two were drawn under it.
    show({ ...first, opened: false });
    const atRest = (selector: string) => STYLES.filter((rule) => rule.selector === selector && rule.under === null);
    const setBy = (selector: string, property: string) => atRest(selector).flatMap((rule) => rule.sets.get(property) ?? []);

    // A row is a column of its parts, so each has a line of its own: the heading first, the ways on last.
    expect(setBy(".row", "display")).toEqual(["grid"]);
    expect([...setBy(".row", "grid-template-columns"), ...setBy(".row", "grid-auto-flow")]).toEqual(["minmax(0, 1fr)"]);
    for (const row of cards().slice(5)) {
      const parts = [...(row.firstElementChild?.children ?? [])];
      expect(parts.at(0)?.tagName).toBe("HEADER");
      expect(parts.at(-1)?.className).toMatch(/waysOn/);
    }
    // The two ways on at the foot are one row, in which each is as wide as its words ask and
    // no wider, and no word is broken: the way to compare, in the heading, is the one a result makes most of.
    expect(setBy(".waysOn", "display")).toEqual(["flex"]);
    for (const way of [".waysOn > a", ".waysOn > span > button"]) {
      expect([way, setBy(way, "flex"), setBy(way, "min-width")]).toEqual([way, ["0 1 auto"], ["min-content"]]);
    }
    expect(setBy(".waysOn > span", "display")).toEqual(["contents"]);
  });

  /** What a result says its fit is based on, where that is part of what counts: `null` where it is everything. */
  const basedOnPart = (area: RankedArea) => {
    const has = area.contributions.filter((part) => part.present).length;
    return has < area.contributions.length ? COMPLETENESS.some(has, area.contributions.length) : null;
  };
  /** What every such line begins with, however many things it counts. */
  const BASED_ON = COMPLETENESS.some(1, 2).split("1")[0] ?? "";
  /** The two words that say a fit is not whole, where a result says them beside its fit. */
  const besideTheFit = (result: HTMLElement) => within(result.querySelector("header") as HTMLElement).queryByText(KNOWN.some);

  test("test_a_fit_that_is_not_whole_says_approx_data_beside_it_and_a_fit_that_is_whole_says_nothing", () => {
    // A fit is never given alone where it is based on some of what counts. A result said
    // so in a sentence or two under its fit. It says so in two words, after the mark of
    // what is not whole, and the sentences are in its working.
    show({ ...first, opened: false });
    const partial = first.ranking.ranked.slice(0, 10).map(basedOnPart);

    // A row says it where its fit is based on some of what counts, and the rest say nothing of it.
    expect(partial.slice(5).map((based) => based !== null)).toEqual(expect.arrayContaining([true, false]));
    expect(BASED_ON.length).toBeGreaterThan(10);
    cards().forEach((result, at) => {
      expect([at, besideTheFit(result) !== null]).toEqual([at, partial[at] !== null]);
      // It is in sight, and heard, and its mark is dress.
      expect([at, besideTheFit(result)?.closest("[aria-hidden='true'], [hidden], .visually-hidden") ?? null]).toEqual([at, null]);
      if (partial[at] !== null) expect(besideTheFit(result)?.previousElementSibling).toHaveAttribute("aria-hidden", "true");
      // No sentence of it stands on the result as it is first shown.
      expect([at, result.textContent?.includes(BASED_ON)]).toEqual([at, false]);
    });
  });

  test("test_what_a_fit_is_based_on_is_said_in_full_in_the_working_after_the_two_words_that_stand_beside_the_fit", () => {
    show(money);
    const partial = money.ranking.ranked.slice(0, 5).map(basedOnPart);

    expect(partial.map((based) => based !== null)).toEqual([false, false, true, false, false]);
    cards()
      .slice(0, 5)
      .forEach((result, at) => {
        expect([at, besideTheFit(result) !== null]).toEqual([at, partial[at] !== null]);
        expect([at, working(at).textContent?.includes(partial[at] ?? BASED_ON)]).toEqual([at, partial[at] !== null]);
        // What is said in the working is said nowhere on the result over it.
        expect([at, (result.firstElementChild as HTMLElement).textContent?.includes(BASED_ON)]).toEqual([at, false]);
      });
    // It stands under the heading that says what the area has no figure for, after the
    // same mark and the same two words.
    const part = within(working(MARROWFEN)).getByRole("heading", { name: COMPLETENESS.missingTitle }).parentElement as HTMLElement;
    expect([...part.children].slice(0, 3).map((one) => one.className.split(" ")[0])).toEqual(["tag", "marked", "completeness"]);
    expect(part.children[1]?.textContent).toBe(KNOWN.some);
    expect(part.children[2]?.textContent?.startsWith(COMPLETENESS.some(7, 8))).toBe(true);
  });

  test("test_one_line_of_the_look_says_what_a_fit_is_based_on_in_full_on_the_result_as_it_was", () => {
    expect(WHAT_A_FIT_IS_BASED_ON_IS_SAID_IN_THE).toBe("working");
    expect(FIT_MAY_BE_SAID).toEqual(["working", "result"]);
    show({ ...money, opened: false, fitSaid: "result" });
    const partial = money.ranking.ranked.slice(0, 5).map(basedOnPart);

    cards()
      .slice(0, 5)
      .forEach((result, at) => {
        expect([at, result.textContent?.includes(partial[at] ?? BASED_ON)]).toEqual([at, partial[at] !== null]);
        // The sentence says it, and the two words are not said as well.
        expect([at, besideTheFit(result)]).toEqual([at, null]);
      });
    // Directly under the heading, in the answer.
    expect(cards()[MARROWFEN]?.querySelector("header")?.nextElementSibling?.className).toMatch(/completeness/);
  });
});

describe("a result card", () => {
  test("test_the_heading_gives_rank_name_borough_and_fit_rounded_down", () => {
    const { unmount } = show(first);

    expect(card(FARROWMERE).getByRole("heading", { level: 3, name: "Farrowmere" })).toBeInTheDocument();
    // The name comes first. Beside it, smaller, is the label its publisher gives the area,
    // which says its borough, and that the name is a draft.
    const beside = card(FARROWMERE).getByText("Quillhaven 006");
    expect(beside.textContent).toBe(`Quillhaven 006${NAMED.between}${NAMED.draft}`);
    expect(beside.tagName).toBe("P");
    expect(card(FARROWMERE).getByText("Rank 1")).toBeInTheDocument();
    expect(first.ranking.ranked[FARROWMERE]?.score).toBe(71.38);
    expect(card(FARROWMERE).getByText("71 of 100")).toBeInTheDocument();
    unmount();
    // 78.52 is shown as 78: a fit is never said to be more than it is.
    show({ ...first, ranking: withFirstArea(first.ranking, (area) => ({ ...area, score: 78.52 })) });
    expect(card(FARROWMERE).getByText("78 of 100")).toBeInTheDocument();
    expect(card(FARROWMERE).queryByText("79 of 100")).toBeNull();
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

  test("test_no_sentence_is_said_twice_once_the_working_is_open", () => {
    show(first);

    first.explanations.forEach((explanation, at) => {
      for (const reason of explanation.reasons) expect(card(at).getAllByText(reason.text)).toHaveLength(1);
      // The trade-off is said on the result, and its source is in the working, which does not say it again.
      if (explanation.trade_off !== null) expect(card(at).getAllByText(explanation.trade_off.text)).toHaveLength(1);
    });
  });

  test("test_why_it_fits_stands_on_no_result_and_every_reason_is_in_the_working_in_the_order_the_api_gave_them", () => {
    // The founder: "Remove the why it fits section, again too much detail". The first
    // reason stood on a result, with the picture of its vibe, and the others in its working.
    show(first);
    const given = first.explanations[FARROWMERE];
    const answer = cards()[FARROWMERE]?.firstElementChild as HTMLElement;

    expect(given?.reasons).toHaveLength(3);
    expect(within(answer).queryByRole("heading", { name: RESULTS.reasonsTitle })).toBeNull();
    for (const reason of given?.reasons ?? []) expect(answer.textContent?.includes(reason.text)).toBe(false);
    const why = within(working(FARROWMERE)).getByRole("heading", { name: RESULTS.reasonsTitle }).parentElement as HTMLElement;
    expect(within(why).getAllByRole("listitem").map((item) => item.querySelector("p")?.textContent)).toEqual(
      given?.reasons.map((reason) => reason.text),
    );
    // They are counted from the first, as the key of each is named.
    expect(within(why).getByRole("list").tagName).toBe("OL");
    expect(within(why).getByRole("list")).not.toHaveAttribute("start");
    expect(within(why).getAllByRole("button", { name: /^Source/ }).map((key) => key.getAttribute("aria-label"))).toEqual(
      [1, 2, 3].map((nth) => SOURCE.buttonFor(RESULTS.sourceOfReason(nth, "Farrowmere"))),
    );
    // No heading of the working says that these are more of them: they are all of them.
    expect(working(FARROWMERE).textContent?.includes(RESULTS.moreReasons)).toBe(false);
    expect(tradeOff(FARROWMERE)).toHaveTextContent(given?.trade_off?.text ?? "no trade-off");
  });

  test("test_with_no_trade_off_the_card_says_so", () => {
    const [top, ...rest] = first.explanations;
    if (!top) throw new Error("the recording explains nothing");

    show({ ...first, explanations: [{ ...top, trade_off: null }, ...rest] });

    // It stands on the line of its heading on a phone: a longer one took a second line.
    expect(RESULTS.noTradeOff).toBe("Burro found no trade-off.");
    expect(tradeOff(0)).toHaveTextContent(RESULTS.noTradeOff);
    expect(card(1).queryByText(RESULTS.noTradeOff)).toBeNull();
    // Seen in a browser: a warning mark over the line that no trade-off was found. It
    // warned of nothing. Nothing of a trade-off warns now, whether one was found or not.
    expect(said(tradeOff(0))).toBe(`${RESULTS.tradeOffTitle}${RESULTS.noTradeOff}`);
    // Nothing else is put in its place: no sentence, and no source of one, on the result or in its working.
    expect(within(tradeOff(0)).queryByRole("button")).toBeNull();
    expect(within(working(0)).queryByRole("heading", { name: CARD.sourceOfTheTradeOff })).toBeNull();
    expect(within(working(1)).getByRole("heading", { name: CARD.sourceOfTheTradeOff })).toBeInTheDocument();
  });

  test("test_the_api_gives_no_trade_off_where_an_area_does_nothing_badly", () => {
    const search = {
      ranking: recordedAnswer("rank", "rank-no-time").body.data,
      ...recordedAnswer("explain_top", "explanations-no-time").body.data,
    };

    show(search);

    expect(search.explanations[0]?.trade_off).toBeNull();
    expect(tradeOff(0)).toHaveTextContent(RESULTS.noTradeOff);
  });

  test("test_with_one_reason_the_working_gives_that_one_and_with_none_it_says_so", () => {
    const [top, second, ...rest] = first.explanations;
    if (!top || !second) throw new Error("the recording explains nothing");

    show({ ...first, explanations: [{ ...top, reasons: top.reasons.slice(0, 1) }, { ...second, reasons: [] }, ...rest] });
    const why = (at: number) => within(working(at)).getByRole("heading", { name: RESULTS.reasonsTitle }).parentElement as HTMLElement;

    expect(within(why(0)).getAllByRole("listitem").map((item) => item.querySelector("p")?.textContent)).toEqual([top.reasons[0]?.text]);
    expect(said(why(1))).toBe(`${RESULTS.reasonsTitle}${RESULTS.noReasons}`);
    expect(within(why(2)).getAllByRole("listitem")).toHaveLength(3);
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
    show({ ...first, explanations: [], explained: false, withDetails: false, opened: false });
    const held = cards()[FARROWMERE]?.querySelectorAll(".skeleton").length ?? 0;
    const parts = card(FARROWMERE).getAllByRole("heading").map((heading) => heading.textContent);

    // The trade-off, which is a line.
    expect(held).toBe(1);
    for (const skeleton of document.querySelectorAll(".skeleton")) {
      expect(skeleton.closest("[aria-hidden='true']")).not.toBeNull();
    }

    cleanup();
    show({ ...first, opened: false });
    expect(cards()[FARROWMERE]?.querySelectorAll(".skeleton")).toHaveLength(0);
    // The same parts, in the same order, before and after.
    expect(card(FARROWMERE).getAllByRole("heading").map((heading) => heading.textContent)).toEqual(parts);
  });

  test("test_a_result_the_service_wrote_nothing_of_draws_no_heading_with_nothing_under_it", () => {
    // The reasons are in, and hold nothing of this area: there is no sentence to wait for,
    // and none that failed. A heading over nothing said that something was missing.
    show({ ...first, explanations: first.explanations.slice(1) });

    expect(within(cards()[0] as HTMLElement).queryByRole("heading", { name: RESULTS.tradeOffTitle })).toBeNull();
    expect(within(working(0)).queryByRole("heading", { name: RESULTS.reasonsTitle })).toBeNull();
    expect(cards()[0]?.querySelectorAll(".skeleton")).toHaveLength(0);
    // Its lines and its ways on are there, and so is the rest of its working.
    expect(within(cards()[0] as HTMLElement).getByRole("list", { name: STRIP.label("Farrowmere") })).toBeInTheDocument();
    expect(within(working(0)).getByRole("heading", { name: COST.title })).toBeInTheDocument();
    // The result beside it, which the service wrote of, has both.
    expect(within(cards()[1] as HTMLElement).getByRole("heading", { name: RESULTS.tradeOffTitle })).toBeInTheDocument();
    expect(within(working(1)).getByRole("heading", { name: RESULTS.reasonsTitle })).toBeInTheDocument();
  });

  test("test_reasons_that_could_not_be_loaded_are_said_and_the_rest_of_the_card_is_there", () => {
    show({ ...first, explanations: [], explained: false, explainFailed: true });

    // The result says it of its trade-off, in sight, and its working of its reasons.
    expect(within(tradeOff(FARROWMERE)).getByText(CARD.tradeOffFailed)).toBeInTheDocument();
    expect(within(working(FARROWMERE)).getByText(RESULTS.reasonsFailed)).toBeInTheDocument();
    expect(card(FARROWMERE).getAllByText(RESULTS.reasonsFailed)).toHaveLength(1);
    expect(cards()[FARROWMERE]?.querySelectorAll(".skeleton")).toHaveLength(0);
    expect(card(FARROWMERE).getByText("£975 to £1,300")).toBeInTheDocument();
  });

  test("test_where_it_is_gives_the_nearest_station_and_a_picture_named_for_the_area", () => {
    show(first);

    const station = within(card(FARROWMERE).getByRole("group", { name: "Nearest station" }));
    expect(station.getByText("Farrowmere")).toBeInTheDocument();
    expect(station.getByText("5")).toBeInTheDocument();
    expect(station.getByText("Cobalt line")).toBeInTheDocument();
    // It is named for what it is and for the area: "the areas of this data" said nothing to a newcomer.
    expect(card(FARROWMERE).getByRole("img", { name: LOCATOR.title("Farrowmere") })).toBeInTheDocument();
    expect(LOCATOR.title("Farrowmere")).toContain("Farrowmere");
    expect(LOCATOR.title("Farrowmere")).not.toMatch(/this data/);
  });

  test("test_an_area_with_no_station_leaves_the_line_out", () => {
    const one = { ...first.ranking, ranked: first.ranking.ranked.slice(0, 1) };
    show({ ...first, ranking: one, withDetails: false, detailsFailed: [one.ranked[0]?.area_id ?? ""] });

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

    const sources = card(FARROWMERE).getAllByRole("button", { name: /^Source/ });
    // Where it is, the station, three reasons, the trade-off, the four vibes the service
    // gave with the result, the journey and the cost.
    expect(sources).toHaveLength(12);
    expect(new Set(sources.map((source) => source.getAttribute("aria-label"))).size).toBe(12);
    for (const source of sources) expect(source).toHaveClass("target-min");
    // Each of them is in the working, and none on the result over it.
    for (const source of sources) expect(working(FARROWMERE).contains(source)).toBe(true);
  });

  test("test_a_source_opens_in_place_with_its_name_its_date_and_that_the_data_is_made_up", async () => {
    const { user } = show(first);
    const cost = card(FARROWMERE).getByRole("heading", { name: COST.title }).parentElement as HTMLElement;

    await user.click(within(cost).getByRole("button", { name: /^Source/ }));

    const link = within(cost).getByRole("link", { name: "Synthetic test data" });
    expect(link).toHaveAttribute("href", "/sources#synthetic");
    expect(within(cost).getByText(`${SOURCE.dataFrom} August 2026`)).toBeInTheDocument();
    expect(within(cost).getByText(SOURCE.madeUp)).toBeInTheDocument();
  });

  test("test_the_working_leads_to_the_areas_page_shows_it_on_the_map_and_hides_it", async () => {
    const { user, onSelect, onEdit } = show(first);

    expect(card(FARROWMERE).getByRole("link", { name: RESULTS.openArea("Farrowmere") })).toHaveAttribute(
      "href",
      "/synthetic/farrowmere",
    );
    await user.click(card(FARROWMERE).getByRole("button", { name: RESULTS.showOnMap("Farrowmere") }));
    expect(onSelect).toHaveBeenCalledWith("syn-n0006");
    await user.click(card(FARROWMERE).getByRole("button", { name: RESULTS.hide("Farrowmere") }));
    expect(onEdit).toHaveBeenCalledWith(edits.areaHide("syn-n0006"));
  });

  /**
   * The list as a page holds it: what a result chooses is what the page holds as chosen,
   * and the map draws the box of that area under itself. The box is the map's own, as the
   * map draws it: so a box that came to be named another way would be found by no result,
   * and that is seen here.
   */
  function APage({ map = true }: { readonly map?: boolean }) {
    const [chosen, setChosen] = useState<string | null>(null);
    const { element } = listOf({ ...first, selectedId: chosen });
    const summary = areas.find((area) => area.area_id === chosen);
    return (
      <>
        {cloneElement(element, { onSelect: setChosen })}
        {map && summary !== undefined ? (
          <MapCard
            summary={summary}
            scores={first.ranking.scores}
            filtered={first.ranking.filtered}
            unranked={first.ranking.unranked}
            inList
            onShowInList={() => undefined}
            onClose={() => setChosen(null)}
          />
        ) : null}
      </>
    );
  }

  test("test_show_on_the_map_says_what_it_did_and_the_focus_goes_to_the_box_the_map_opened_for_the_area", async () => {
    // Seen in a browser: a press on it said nothing to whoever cannot see the map, and on a
    // phone the map was brought into sight and the focus left on the button, 1,492 px
    // under the window.
    const user = userEvent.setup({ delay: null });
    render(<APage />);
    await user.click(card(FARROWMERE).getByRole("button", { name: /^Show the working: / }));
    const said = within(working(FARROWMERE)).getByRole("status");
    const pressed = card(FARROWMERE).getByRole("button", { name: RESULTS.showOnMap("Farrowmere") });

    // It is on the page before the press, and holds nothing: what comes to stand in it is heard.
    expect(said.textContent).toBe("");
    await user.click(pressed);

    expect(said).toHaveTextContent(CARD.shownOnMap("Farrowmere"));
    expect(said.closest("[aria-hidden='true'], [hidden], .visually-hidden")).toBeNull();
    // The focus is on what the press showed, which says which area it is of.
    const box = screen.getByRole("region", { name: MAP_CARD.label });
    expect(box).toHaveFocus();
    expect(box).toHaveTextContent("Farrowmere");
    // The result is marked as the one that is chosen, and its working stays open.
    expect(cards()[FARROWMERE]).toHaveAttribute("aria-current", "true");
    expect(card(FARROWMERE).getByRole("button", { name: /^Show the working: / })).toHaveAttribute("aria-expanded", "true");
    // A second press leads there again, from a result that is chosen already.
    pressed.focus();
    await user.click(pressed);
    expect(box).toHaveFocus();
    // No other result says anything of it.
    await user.click(card(1).getByRole("button", { name: /^Show the working: / }));
    expect(within(working(1)).getByRole("status").textContent).toBe("");
    // Once another area is shown there, the line is that area's: the first no longer says
    // that it is the one marked, which would be untrue.
    const other = nameOf(first.ranking.ranked[1]?.area_id ?? "");
    await user.click(card(1).getByRole("button", { name: RESULTS.showOnMap(other) }));
    expect(within(working(1)).getByRole("status")).toHaveTextContent(CARD.shownOnMap(other));
    expect(said.textContent).toBe("");
    expect(screen.getByRole("region", { name: MAP_CARD.label })).toHaveFocus();
    expect(screen.getByRole("region", { name: MAP_CARD.label })).toHaveTextContent(other);
  });

  test("test_where_no_map_is_drawn_show_on_the_map_says_so_and_the_focus_stays_on_what_was_pressed", async () => {
    const user = userEvent.setup({ delay: null });
    render(<APage map={false} />);
    await user.click(card(FARROWMERE).getByRole("button", { name: /^Show the working: / }));
    const pressed = card(FARROWMERE).getByRole("button", { name: RESULTS.showOnMap("Farrowmere") });

    await user.click(pressed);

    expect(within(working(FARROWMERE)).getByRole("status")).toHaveTextContent(CARD.notOnMap("Farrowmere"));
    expect(pressed).toHaveFocus();
    expect(document.body.textContent?.includes(CARD.shownOnMap("Farrowmere"))).toBe(false);
  });

  test("test_what_a_press_said_takes_no_room_until_it_speaks_and_is_said_once", () => {
    const at = (selector: string) => new Map(STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

    // It is never taken off the page to make no room: what is not on the page is not heard when it comes.
    expect(STYLES.filter((rule) => /\.did\b/.test(rule.selector) && rule.sets.has("display"))).toEqual([]);
    expect(at(".did").get("margin")).toBe("0");
    expect(at(".did:not(:empty)").get("margin-block-start")).toBe("var(--space-2)");
    show(first);
    // One for each working, and each holds nothing until its button is pressed.
    expect(screen.getAllByRole("status").map((one) => one.textContent)).toEqual(cards().map(() => ""));
  });

  test("test_the_card_under_the_pointer_or_the_focus_is_told_to_the_map", async () => {
    const { user, onHover } = show({ ...first, opened: false });

    await user.hover(cards()[1] as HTMLElement);
    await user.unhover(cards()[1] as HTMLElement);
    await user.tab();

    expect(onHover.mock.calls.map(([areaId]) => areaId)).toEqual(
      expect.arrayContaining(["syn-n0005", null, "syn-n0006"]),
    );
  });

  test("test_the_chosen_card_says_so", () => {
    show({ ...first, selectedId: "syn-n0005" });

    // Recorded: the area chosen is the second of the list. No other card says it is chosen.
    expect(first.ranking.ranked[1]?.area_id).toBe("syn-n0005");
    expect(cards().map((one) => one.getAttribute("aria-current") === "true").indexOf(true)).toBe(1);
    expect(cards().filter((one) => one.getAttribute("aria-current") === "true")).toHaveLength(1);
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
  /** The first search, with the trade-off of Farrowmere put in the place of the one the API gave. */
  const withTradeOff = (sentence: ExplainedSentence | null) => ({
    ...first,
    explanations: first.explanations.map((one) =>
      one.area_id === "syn-n0006" ? { ...one, trade_off: sentence } : one,
    ),
  });
  const farrowmere = first.ranking.ranked[FARROWMERE];
  const { reason_min_utility: DOES_WELL_FROM, trade_off_max_utility: DOES_BADLY_BELOW } = meta.data.limits;

  test("test_what_counts_as_doing_badly_is_what_the_api_serves_and_the_contract_says", () => {
    const contract = readFileSync(path.resolve(__dirname, "../../../../../docs/design/contract.md"), "utf8");

    // Contract 7.5: a reason is worth at least a half. A trade-off is worth less than 0.35, or is a shortfall.
    expect(contract).toContain("whose utility is at least `REASON_MIN_UTILITY`, 0.50,");
    expect(contract).toContain("whose utility is below `TRADE_OFF_MAX_UTILITY`, 0.35,");
    expect(contract).toContain("**A trade-off is never something the area does well**");
    // The website holds no copy of either figure: it reads them from the form.
    expect(DOES_WELL_FROM).toBe(0.5);
    expect(DOES_BADLY_BELOW).toBe(0.35);
  });

  test("test_a_strength_is_never_put_under_the_word_trade_off", () => {
    // Seen in a browser, from an engine before 1.3.0: "a 2 minute walk, closer than 77% of
    // areas" under "Trade-off". Here it is the air, which Farrowmere does better than most.
    const air = farrowmere?.contributions.find((part) => part.component === "feature:air_no2");
    const strength = sentenceOn("syn-n0006/feature/air_no2", "A strength, said as the API would say one.");

    show(withTradeOff(strength));

    expect(air?.utility).toBeGreaterThanOrEqual(DOES_WELL_FROM);
    expect(tradeOff(FARROWMERE).textContent?.includes(strength.text)).toBe(false);
    expect(tradeOff(FARROWMERE)).toHaveTextContent(RESULTS.noTradeOff);
    // The cards beside it are as the API gave them.
    expect(tradeOff(2)).toHaveTextContent(first.explanations[2]?.trade_off?.text ?? "no trade-off");
  });

  test("test_a_thing_done_neither_well_nor_badly_is_never_put_under_the_word_trade_off", () => {
    // Seen in a browser, from an engine before 1.4.0: a walk of five minutes to a station,
    // worth a hair under a half, given as what an area gives up.
    const walk = farrowmere?.contributions.find((part) => part.component === "feature:station_walk");
    const middling = sentenceOn("syn-n0006/feature/station_walk", "A walk of five minutes, said as the API would say it.");

    show(withTradeOff(middling));

    expect(walk?.utility).toBe(0.455);
    expect(walk?.utility).toBeLessThan(DOES_WELL_FROM);
    expect(walk?.utility).toBeGreaterThanOrEqual(DOES_BADLY_BELOW);
    expect(tradeOff(FARROWMERE).textContent?.includes(middling.text)).toBe(false);
    expect(tradeOff(FARROWMERE)).toHaveTextContent(RESULTS.noTradeOff);
  });

  test("test_how_little_a_thing_is_worth_to_be_done_badly_is_the_figure_that_is_passed_in", () => {
    const walk = sentenceOn("syn-n0006/feature/station_walk", "");
    if (!farrowmere) throw new Error("the recording does not rank Farrowmere second");

    expect(isGivenUp(farrowmere, walk, first.ranking.spec.commutes, 0.35)).toBe(false);
    expect(isGivenUp(farrowmere, walk, first.ranking.spec.commutes, 0.5)).toBe(true);
  });

  test("test_a_sentence_about_nothing_that_counts_is_never_put_under_the_word_trade_off", () => {
    const stray = sentenceOn("syn-n0006/feature/homes_flats", "About a thing that does not count in this search.");

    show(withTradeOff(stray));

    expect(farrowmere?.contributions.some((part) => part.fact_ids.includes(stray.fact_ids[0] ?? ""))).toBe(false);
    expect(tradeOff(FARROWMERE).textContent?.includes(stray.text)).toBe(false);
    expect(tradeOff(FARROWMERE)).toHaveTextContent(RESULTS.noTradeOff);
  });

  test("test_a_home_over_the_budget_is_a_trade_off_however_much_it_is_worth", () => {
    // Eskerfold is £50 over the budget, which is worth more than a half, and is still a shortfall.
    show(first);

    const at = first.ranking.ranked.findIndex((area) => area.area_id === "syn-n0005");
    const budget = first.ranking.ranked[at]?.contributions.find((part) => part.component === "budget");
    expect(budget?.utility).toBeGreaterThanOrEqual(DOES_WELL_FROM);
    expect(first.ranking.ranked[at]?.budget?.margin).toBeLessThan(0);
    expect(tradeOff(at)).toHaveTextContent(first.explanations[at]?.trade_off?.text ?? "no trade-off");
  });

  /** Every search that was recorded with both its ranking and its reasons. */
  const EXPLAINED = readdirSync(recordedFolder())
    .filter((name) => /^explanations-.*\.json$/.test(name))
    .map((name) => name.slice("explanations-".length, -".json".length))
    .filter((search) => existsSync(path.join(recordedFolder(), `rank-${search}.json`)));

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

  test.each(EXPLAINED)("test_the_first_reason_of_every_card_is_something_the_area_does_well: %s", (search) => {
    // Seen in a browser: "Why it fits" led with a walk further than 77% of areas. A reason is
    // worth at least a half, and never states a shortfall.
    const ranking = recordedAnswer("rank", `rank-${search}`).body.data;
    const { explanations } = recordedAnswer("explain_top", `explanations-${search}`).body.data;

    for (const area of ranking.ranked.slice(0, 5)) {
      const given = explanations.find((one) => one.area_id === area.area_id);
      for (const reason of given?.reasons ?? []) {
        const part = area.contributions.find((one) => one.fact_ids.includes(reason.fact_ids[0] ?? ""));
        expect(part?.utility).toBeGreaterThanOrEqual(DOES_WELL_FROM);
        expect(isGivenUp(area, reason, ranking.spec.commutes, DOES_BADLY_BELOW)).toBe(false);
      }
    }
  });

  test("test_a_journey_given_as_the_trade_off_says_in_the_apis_sentence_that_it_is_over_the_time_that_was_set_and_the_working_says_it_of_every_journey", () => {
    // The card said under the sentence "Over your limit of 30 minutes", which the sentence
    // of the service had said by then, with by how much. A result says it once.
    show(two);
    const said = two.explanations[0]?.trade_off?.text ?? "no trade-off";

    expect(two.explanations[0]?.trade_off?.fact_ids[0]).toBe("syn-n0016/travel/syn-p0026.pt");
    expect(two.ranking.spec.commutes.find((one) => one.place_id === "syn-p0026")?.max_minutes).toBe(30);
    expect(said).toContain("6 minutes over the limit of 30 minutes you set");
    expect(tradeOff(0).textContent).toBe(`${RESULTS.tradeOffTitle}${said}`);
    expect(within(tradeOff(0)).queryByText(JOURNEYS.overLimit(30))).toBeNull();
    // Which way each journey falls is in the working, in the table of the journeys.
    const journeys = within(working(0)).getByRole("table", { name: JOURNEYS.title });
    expect(within(journeys).getAllByText(JOURNEYS.over).length).toBeGreaterThan(0);
  });

  test("test_under_trade_off_stands_the_sentence_of_the_service_and_no_verdict_of_the_website", () => {
    const journeysGivenUp = ["first", "by-the-river", "only-one", "by-bike-over", "on-foot"].map((search) => {
      const ranking = recordedAnswer("rank", `rank-${search}`).body.data;
      const { explanations, facts } = recordedAnswer("explain_top", `explanations-${search}`).body.data;
      const { unmount } = show({ ranking, explanations, facts });
      const ofAJourney = explanations.filter((one) => /\/travel\//.test(one.trade_off?.fact_ids[0] ?? ""));
      ranking.ranked.slice(0, 5).forEach((area, at) => {
        const given = explanations.find((one) => one.area_id === area.area_id)?.trade_off;
        expect([search, at, tradeOff(at).textContent]).toEqual([search, at, `${RESULTS.tradeOffTitle}${given?.text ?? RESULTS.noTradeOff}`]);
        expect([search, at, within(tradeOff(at)).queryByText(/your limit of/)]).toEqual([search, at, null]);
      });
      unmount();
      return ofAJourney.length;
    });
    // The recorded searches hold trade-offs that are journeys, over a limit and with none set.
    expect(journeysGivenUp.every((count) => count > 0)).toBe(true);
    expect(readFileSync(path.join(__dirname, "ResultList.module.css"), "utf8")).not.toMatch(/\.against\b/);
  });
});

describe("a vibe the service calls a rough guide, on a card", () => {
  // The founder, who had walked the website twice: "remove the concept of rough guide, we
  // don't want to pass this on to a user". The service still says which vibe it holds to be
  // less sure than the rest, in a code, and no word more. What it said of it until it
  // stopped, its label and why, a service may say again: so the list is handed the release
  // as such a service gave it, with both laid on it. No result says either.
  const village = {
    ranking: recordedAnswer("rank", "rank-rough-guide").body.data,
    ...recordedAnswer("explain_top", "explanations-rough-guide").body.data,
  };
  const told = sayingSo(meta.data);
  const guide = meta.data.tags.find((tag) => tag.tag_id === ROUGH.tag_id);
  if (guide === undefined) throw new Error("the recorded release holds no such vibe");

  test("test_a_card_and_a_row_that_show_it_say_nothing_of_it_that_they_do_not_say_of_any_vibe", () => {
    show({ ...village, facts: village.facts, bands: recordedAnswer("list_areas", "areas").body.data.bands, form: told });

    expect(guide.sureness).toBe("rough_guide");
    expect(told.rough_guides).toEqual([ROUGH]);
    expect(cards().length).toBeGreaterThan(5);
    village.ranking.ranked.slice(0, cards().length).forEach((area, at) => {
      const result = cards()[at] as HTMLElement;
      // Every result of the recorded search shows the vibe: it was asked for.
      expect([at, area.strip.some((mark) => mark.tag_id === guide.tag_id)]).toEqual([at, true]);
      expect([at, result.textContent?.includes(guide.label)]).toEqual([at, true]);
      // With its working open as well, nothing of it says that the vibe is a rough guide, or why.
      expect([at, result.querySelector("[data-rough-guide]")]).toEqual([at, null]);
      expect([at, result.textContent?.includes(ROUGH.label)]).toEqual([at, false]);
      expect([at, result.textContent?.includes(ROUGH.why)]).toEqual([at, false]);
      expect([at, /rough guide|less sure/i.test(result.textContent ?? "")]).toEqual([at, false]);
    });
  });

  test("test_no_part_of_a_result_reads_a_word_a_rough_guide_says_of_itself", () => {
    const written = readdirSync(__dirname)
      .filter((file) => /\.(tsx?|css)$/.test(file) && !/\.test\.tsx?$/.test(file))
      .map((file) => readFileSync(path.join(__dirname, file), "utf8"))
      .join("\n");

    expect(written.length).toBeGreaterThan(10_000);
    expect(/rough_guides|sureness|RoughGuide|rough guide|roughOf/i.test(written)).toBe(false);
  });

  test("test_a_card_of_a_search_that_did_not_ask_for_it_does_not_show_the_vibe", () => {
    show({ ...first, opened: false, form: told });

    for (const one of cards()) expect(one.textContent?.includes(guide.label)).toBe(false);
  });
});

describe("a vibe that a sentence is about", () => {
  // The picture of a vibe stood beside the sentence that was about it, a reason or a
  // trade-off, and was taken out of the strip over it. A result holds a line for each vibe
  // that was asked for, whatever any sentence is about, and no picture stands beside a sentence.
  const leafy = {
    ranking: recordedAnswer("rank", "rank-shelf").body.data,
    ...recordedAnswer("explain_top", "explanations-shelf").body.data,
  };
  /** The part of the working of a card under a heading of its own. */
  const part = (at: number, name: string) => within(working(at)).getByRole("heading", { name }).parentElement as HTMLElement;
  const strip = (at: number, name: string) => card(at).queryByRole("list", { name: STRIP.label(name) });
  const factsOf = (shown: typeof leafy) => ({ facts: shown.facts });

  test("test_a_vibe_that_a_reason_is_about_is_drawn_once_on_its_line_and_no_picture_stands_beside_a_sentence", () => {
    show({ ...leafy, ...factsOf(leafy) });
    const [top] = leafy.ranking.ranked;
    const given = leafy.explanations.find((one) => one.area_id === top?.area_id);
    const mark = top?.strip.find((one) => given?.reasons[0]?.fact_ids.includes(one.fact_id));
    if (top === undefined || mark === undefined) throw new Error("the first reason of the recording is no vibe of its strip");

    // Its line is on the result, and says the band and which way the bands run.
    const lines = within(strip(0, nameOf(top.area_id)) as HTMLElement).getAllByRole("listitem");
    expect(lines.map((line) => within(line).getByRole("img").getAttribute("aria-label"))).toEqual([
      `${STRIP.band(mark.band)}, ${STRIP.from(STRIP.least, STRIP.most)}, ${STRIP.asked}`,
    ]);
    expect(mark.band).toBe(5);
    // Its reason is in the working, as it came, with no picture beside it.
    const why = part(0, RESULTS.reasonsTitle);
    expect(within(why).getByText(given?.reasons[0]?.text ?? "no reason")).toBeInTheDocument();
    expect(within(why).queryAllByRole("img")).toEqual([]);
    expect(within(tradeOff(0)).queryAllByRole("img")).toEqual([]);
  });

  test("test_a_vibe_that_is_the_reason_is_said_in_short_and_what_it_leaves_out_is_behind_its_source", async () => {
    // Seen by a reviewer: "Why it fits" was one sentence of thirty words about bands and
    // dates, the same on every card that led with that vibe, and half of it a disclaimer.
    const { user } = show({ ...leafy, ...factsOf(leafy) });
    const [top] = leafy.ranking.ranked;
    const given = leafy.explanations.find((one) => one.area_id === top?.area_id);
    const sentence = given?.reasons[0];
    const fact = leafy.facts.find((one) => one.fact_id === sentence?.fact_ids[0]);
    if (top === undefined || sentence === undefined || fact === undefined) throw new Error("the recording gives no reason");
    const why = within(part(0, RESULTS.reasonsTitle)).getAllByRole("listitem")[0] as HTMLElement;

    expect(fact.kind).toBe("tag");
    // It is the API's sentence, as it came: the band, among how many areas, and which way the bands run.
    expect(sentence.text).toBe("Leafy: band 5 of 5 among the 21 areas Burro compared, where the bands run from least to most.");
    expect(within(why).getByText(sentence.text)).toBeInTheDocument();
    // The line that the recipe is a judgement, and the date of its parts, are not said with it.
    expect(why.textContent?.includes(fact.slots.judgement ?? "none")).toBe(false);
    expect(why.textContent?.includes("Parts dated")).toBe(false);
    await user.click(within(why).getByRole("button", { name: /^Source for / }));

    // They are one press away, in the API's words, with the source.
    expect(within(why).getByText(fact.slots.judgement ?? "none")).toBeInTheDocument();
    expect(within(why).getByText(fact.slots.made_from ?? "none")).toBeInTheDocument();
    expect(within(why).getByText(`${SOURCE.dataFrom} ${fact.as_of}`)).toBeInTheDocument();
  });

  test("test_a_vibe_that_is_the_trade_off_is_drawn_once_on_its_line_and_its_source_is_under_the_trade_off", () => {
    show(first);
    const at = first.ranking.ranked.findIndex((area) => {
      const given = first.explanations.find((one) => one.area_id === area.area_id);
      return area.strip.some((mark) => given?.trade_off?.fact_ids.includes(mark.fact_id));
    });
    const area = first.ranking.ranked[at];
    const given = first.explanations.find((one) => one.area_id === area?.area_id);
    const about = first.facts.find((fact) => fact.fact_id === given?.trade_off?.fact_ids[0]);
    if (area === undefined || about === undefined) throw new Error("no trade-off of the recording is a vibe of its strip");

    expect(within(tradeOff(at)).queryAllByRole("img")).toEqual([]);
    // It was asked for, so it has its line among what was asked for.
    const asked = area.strip.filter((mark) => mark.asked);
    expect(asked.some((mark) => mark.fact_id === about.fact_id)).toBe(true);
    expect(within(strip(at, nameOf(area.area_id)) as HTMLElement).getAllByRole("listitem")).toHaveLength(asked.length);
    // In the working its source stands once, under the trade-off, and its figures are not
    // laid out a second time among those of the other vibes.
    expect(within(part(at, CARD.sourceOfTheTradeOff)).getByText(about.label)).toBeInTheDocument();
    expect(within(part(at, CARD.vibes)).queryByRole("group", { name: about.label })).toBeNull();
    expect(within(part(at, CARD.vibes)).getAllByRole("group")).toHaveLength(area.strip.length - 1);
    expect(within(working(at)).queryAllByRole("button", { name: SOURCE.buttonFor(about.label) })).toEqual([]);
  });

  test("test_the_lines_of_a_result_are_whole_whatever_its_sentences_are_about_and_while_they_are_waited_for", () => {
    // Recorded: the first reason of the fourth area is its journey. Its trade-off is a vibe.
    const { unmount } = show({ ...first, opened: false });
    const at = first.ranking.ranked.findIndex((one) => one.area_id === "syn-n0003");
    const area = first.ranking.ranked[at];
    const asked = area?.strip.filter((mark) => mark.asked).length ?? 0;

    expect(first.explanations[at]?.reasons[0]?.fact_ids[0]).toBe("syn-n0003/travel/syn-p0021.pt");
    expect(asked).toBeGreaterThan(0);
    expect(within(strip(at, "Cindermoor") as HTMLElement).getAllByRole("listitem")).toHaveLength(asked);
    unmount();
    show({ ...first, explanations: [], explained: false, opened: false });
    expect(within(strip(at, "Cindermoor") as HTMLElement).getAllByRole("listitem")).toHaveLength(asked);
  });

  test("test_a_short_sentence_is_laid_out_as_a_long_one_is_word_for_word", () => {
    // The sentence is the API's to write, and is to be made short. The card holds no word of
    // it, and no room for any: whatever comes is shown as it came.
    const short = "Leafy: among the least.";
    const [top] = first.ranking.ranked;
    const explanations = first.explanations.map((one) =>
      one.area_id === top?.area_id && one.trade_off !== null ? { ...one, trade_off: { ...one.trade_off, text: short } } : one,
    );
    show({ ...first, explanations, opened: false });

    expect(within(tradeOff(0)).getByText(short).tagName).toBe("P");
    // Nothing of the sentence that was there before is left, and nothing is added to the new one.
    expect(said(tradeOff(0))).toBe(`${RESULTS.tradeOffTitle}${short}`);
    // No style gives a sentence, or what holds it, a height of its own.
    const sized = STYLES.filter(
      (rule) => ["part", "tradeOff", "tradeOffSaid"].some((name) => isFor(rule.selector, name)) && (rule.sets.has("height") || rule.sets.has("min-height")),
    );
    expect(sized).toEqual([]);
  });
});

describe("how complete the data is", () => {
  /** What a result says in full of what its fit is based on: it is in its working. */
  const completeness = (at: number) => cards()[at]?.querySelector("[class*='completeness']") as HTMLElement;
  /** The answer of a result: what it says before anything is pressed. */
  const answer = (at: number) => cards()[at]?.firstElementChild as HTMLElement;
  /** What a result says was asked for and has no figure, line by line. */
  const lacked = (at: number, name: string) =>
    within(answer(at))
      .queryAllByRole("list", { name: CARD.lacked(name) })
      .flatMap((list) => within(list).getAllByRole("listitem"))
      .map((line) => line.textContent);

  test("test_a_card_whose_fit_rests_on_everything_says_no_more_of_it", () => {
    // It was said on every such card, which is most of them: a line of each that said
    // nothing a person needed to act on. What a fit rests on is said where it is part.
    show(first);
    const ranked = first.ranking.ranked[FARROWMERE];

    expect(ranked?.contributions.every((part) => part.present)).toBe(true);
    expect(card(FARROWMERE).queryByText(COMPLETENESS.all)).toBeNull();
    expect(completeness(FARROWMERE)).toBeNull();
    // A fit that rests on part of what counts is never given alone.
    cleanup();
    show(money);
    expect(completeness(MARROWFEN)).toHaveTextContent(COMPLETENESS.some(7, 8));
  });

  test("test_what_a_fit_rests_on_is_said_in_words_and_counted_from_the_ranking", () => {
    show(money);

    // Seen by the reviewers: "5 of the 10" beside a bar 77% wide. The bar was another
    // measure, of how much of the weight had data. There is no bar now: the words say it.
    expect(money.ranking.ranked[MARROWFEN]?.weight_coverage).toBeLessThan(1);
    expect(completeness(MARROWFEN)).toHaveTextContent(COMPLETENESS.some(7, 8));
    expect(document.querySelectorAll("[class*='meter']")).toHaveLength(0);

    money.ranking.ranked.slice(0, 5).forEach((area, at) => {
      const has = area.contributions.filter((part) => part.present).length;
      const of = area.contributions.length;
      if (has === of) expect(completeness(at)).toBeNull();
      else expect(completeness(at)).toHaveTextContent(COMPLETENESS.some(has, of));
    });
  });

  test("test_a_fit_that_rests_on_part_says_how_many_of_the_things_that_count_nobody_chose", () => {
    // The founder, of a chip that read "Usual settings: 6 assumed": "either show those or
    // remove the section". The chip went, and a result of a search of four things still
    // said "9 of the 10 things that count", with nothing in sight to say what the other six
    // were. So where the things that count are counted, the result says how many of them
    // Burro counts in every search, and where they can be seen and changed. It says so in
    // the words of the bar of the group that holds each, now that the settings are named
    // "Space requirements" and nothing on the page is called a setting.
    show(money);
    const usual = money.ranking.spec.weights.filter((weight) => weight.provenance === "default").length;

    expect(usual).toBe(6);
    expect(working(MARROWFEN).contains(completeness(MARROWFEN))).toBe(true);
    expect(completeness(MARROWFEN)).toHaveTextContent(`${COMPLETENESS.some(7, 8)} ${COMPLETENESS.usual(usual)}`);
    expect(COMPLETENESS.usual(6)).toBe(`6 of them are counted in every search. You can see and change them under ${REFINE.label}.`);
    expect(COMPLETENESS.usual(1)).toMatch(/^One of them is counted in every search\. You can see and change it under /);
    // Both are whole sentences, and the first says what is counted: the fit.
    expect(COMPLETENESS.some(7, 8)).toMatch(/^This fit is based on 7 of the 8 things that count in your search\.$/);
    expect(COMPLETENESS.all).toMatch(/^This fit is based on everything that counts in your search\.$/);
  });

  test("test_nothing_is_said_of_what_burro_counts_in_every_search_where_every_thing_that_counts_was_chosen", () => {
    // A search that a person set wholly by hand holds nothing that nobody chose, and says nothing of it.
    const chosen = {
      ...money.ranking,
      spec: {
        ...money.ranking.spec,
        weights: money.ranking.spec.weights.map((weight) => ({ ...weight, provenance: "stated" as const })),
      },
    };
    show({ ...money, ranking: chosen });

    expect(completeness(MARROWFEN)).toHaveTextContent(COMPLETENESS.some(7, 8));
    expect(/counted in every search|usual setting/.test(completeness(MARROWFEN).textContent ?? "")).toBe(false);
  });

  test("test_what_the_list_counts_is_what_the_api_counts_for_the_map_and_the_table", () => {
    // The list counts the parts of a ranked area. The map and the table read the count the API gives.
    for (const area of first.ranking.ranked) {
      const score = first.ranking.scores.find((one) => one.area_id === area.area_id);
      expect(score).toMatchObject({
        counted: area.contributions.length,
        present: area.contributions.filter((part) => part.present).length,
      });
    }
  });

  test("test_that_a_fit_is_not_whole_is_said_with_the_fit_in_the_heading_of_the_result", () => {
    show({ ...first, opened: false });

    // It is what says how far to trust the fit, so it is read with the fit, and is the last thing of it.
    const partial = first.ranking.ranked.findIndex(
      (area, at) => at >= 5 && area.contributions.some((part) => !part.present),
    );
    expect(partial).toBeGreaterThanOrEqual(5);
    const heading = cards()[partial]?.querySelector("header") as HTMLElement;
    const fit = heading.querySelector("p.fit") as HTMLElement;
    expect([...fit.children].map((part) => part.className.split(" ")[0])).toEqual(["fitLabel", "fitFigure", "approx"]);
    expect(fit.lastElementChild?.textContent).toBe(KNOWN.some);
    // The part says of itself that it is there, to whatever looks for one.
    expect(heading.querySelectorAll("[data-known]")).toHaveLength(1);
    expect(fit.lastElementChild).toHaveAttribute("data-known", "some");
    expect([...(heading.querySelector("[class*='titled']") as HTMLElement).children].map((part) => part.className.split(" ")[0]).slice(0, 3)).toEqual([
      "name",
      "borough",
      "fit",
    ]);
    // A result whose fit is whole says nothing in its place, and nothing stands under its heading.
    for (const at of [0, 1, 4]) {
      expect(cards()[at]?.querySelector("header [data-known]")).toBeNull();
      expect(cards()[at]?.querySelector("header")?.nextElementSibling).toBeNull();
    }
    // Nothing is said of a fit where nothing is set to rank by: there is no fit to speak of.
    cleanup();
    show({ ...first, ranking: { ...first.ranking, empty_spec: true }, opened: false });
    expect(document.querySelectorAll("header [data-known]")).toHaveLength(0);
  });

  test("test_a_card_with_something_missing_counts_it_and_gives_the_apis_sentence_for_each", () => {
    show(money);

    expect(card(MARROWFEN).getByText(COMPLETENESS.some(7, 8))).toBeInTheDocument();
    const missing = money.explanations[MARROWFEN]?.missing ?? [];
    expect(missing).toHaveLength(1);
    for (const sentence of missing) expect(card(MARROWFEN).getByText(sentence.text)).toBeInTheDocument();
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
    show({ ...money, explanations: [], explained: false });

    // How many sentences will come is known from the ranking, so their place is held.
    const waiting = card(MARROWFEN).getByRole("heading", { name: COMPLETENESS.missingTitle }).parentElement;
    expect(waiting?.querySelectorAll(".skeleton")).toHaveLength(1);
    expect(card(0).queryByRole("heading", { name: COMPLETENESS.missingTitle })).toBeNull();

    cleanup();
    show(money);
    const listed = card(MARROWFEN).getByRole("heading", { name: COMPLETENESS.missingTitle }).parentElement;
    expect(listed?.querySelectorAll(".skeleton")).toHaveLength(0);
    expect(within(listed as HTMLElement).getAllByRole("button", { name: /^Source/ })).toHaveLength(1);
  });

  test("test_a_limit_that_could_not_be_held_against_an_area_is_said_on_the_result_in_two_words_and_in_full_in_its_working", () => {
    show({ ...two, opened: false });

    expect(two.ranking.ranked[0]?.untested_filters).toEqual(["over_budget"]);
    expect(two.ranking.ranked[0]?.contributions.filter((part) => !part.present).map((part) => part.component)).toEqual(["budget"]);
    // In sight, with nothing pressed: the fit is not whole, and the budget is not known here.
    expect(within(answer(0).querySelector("header") as HTMLElement).getByText(KNOWN.some)).toBeInTheDocument();
    expect(lacked(0, "Ostrel Vale")).toEqual([`${BREAKDOWN.budget}${KNOWN.none}`]);
    expect(within(answer(0)).getByText(KNOWN.none).closest("[aria-hidden='true'], [hidden], .visually-hidden")).toBeNull();
    // What is not known is never drawn as nought or as the middle: its line has no gauge.
    const line = within(answer(0)).getByRole("list", { name: CARD.lacked("Ostrel Vale") });
    expect(line.querySelector("[role='img'], [class*='track']")).toBeNull();
    // The sentence is one press away.
    expect(answer(0).textContent?.includes(UNTESTED.over_budget)).toBe(false);
    fireEvent.click(card(0).getByRole("button", { name: /^Show the working: / }));
    expect(within(working(0)).getByText(UNTESTED.over_budget)).toBeInTheDocument();
  });

  test("test_a_limit_that_could_not_be_held_against_an_area_is_said_heavier_in_ink_and_not_in_small_print", () => {
    show(two);

    // It is the gravest thing that is said of a fit: the one limit the person called firm
    // was not applied. It stands under the mark of what is not whole, with what the fit
    // is based on, and is said heavier than what stands round it.
    const line = within(working(0)).getByText(UNTESTED.over_budget);
    expect(completeness(0).contains(line)).toBe(true);
    expect(line.className).toBe("untested");
    const rules = STYLES.filter((rule) => isFor(rule.selector, "untested"));
    expect(rules.map((rule) => rule.sets.get("color")).filter(Boolean)).toEqual(["var(--ink)"]);
    expect(rules.map((rule) => rule.sets.get("font-weight")).filter(Boolean)).toEqual(["700"]);
    // Whatever the size of what is around it, it is the size of the body of the page.
    expect(rules.map((rule) => rule.sets.get("font-size")).filter(Boolean)).toEqual(["var(--size-body)"]);
    // Nothing of it warns: the mark of a warning went with the mark of the trade-off.
    expect(completeness(0).querySelector("[aria-hidden='true']")).toBeNull();
    expect(completeness(0).previousElementSibling?.textContent).toBe(KNOWN.some);
  });

  test("test_a_row_says_that_its_fit_is_not_whole_in_two_words_and_what_it_is_based_on_in_its_working", () => {
    show({ ...first, opened: false });
    const at = first.ranking.ranked.findIndex(
      (area, place) => place >= 5 && area.contributions.some((part) => !part.present),
    );

    expect(within(answer(at).querySelector("header") as HTMLElement).getByText(KNOWN.some)).toBeInTheDocument();
    expect(answer(at).textContent?.includes(COMPLETENESS.some(9, 10))).toBe(false);
    fireEvent.click(card(at).getByRole("button", { name: /^Show the working: / }));
    expect(within(working(at)).getByText(COMPLETENESS.some(9, 10))).toBeInTheDocument();
  });

  test("test_a_vibe_that_was_asked_for_and_has_no_figure_has_its_line_on_the_result_with_an_empty_gauge_and_says_no_data", () => {
    // An area with no figure for a thing that was asked for stands below every area that
    // has one, and says which figure it lacks. It said so in a sentence. It says so on
    // the line of the thing, which is named by the thing, and the sentence is in its working.
    const lacking = withFirstArea(first.ranking, (area) => ({
      ...area,
      strip: area.strip.filter((mark) => mark.tag_id !== "leafy"),
      contributions: area.contributions.map((part) =>
        part.component === "tag:leafy" ? { ...part, present: false, utility: null, contribution: 0, fact_ids: [] } : part,
      ),
    }));
    show({ ...first, ranking: lacking, opened: false });
    const lines = within(within(answer(0)).getByRole("list", { name: STRIP.label("Farrowmere") })).getAllByRole("listitem");

    expect(lacking.ranked[0]?.contributions.some((part) => part.component === "tag:leafy")).toBe(true);
    // What has a figure comes first, and then what has none.
    expect(lines.map((line) => line.textContent)).toEqual(["Quiet streets", `Leafy${KNOWN.none}`]);
    expect(lines[1]?.querySelectorAll("[data-on]")).toHaveLength(0);
    expect(lines[1]?.querySelector("[class*='peg']")).toBeNull();
    expect(within(answer(0).querySelector("header") as HTMLElement).getByText(KNOWN.some)).toBeInTheDocument();
    expect(answer(0).textContent?.includes(COMPLETENESS.lacksAsked(["Leafy"]))).toBe(false);
    fireEvent.click(card(0).getByRole("button", { name: /^Show the working: / }));
    expect(within(working(0)).getByText(COMPLETENESS.lacksAsked(["Leafy"]))).toBeInTheDocument();
    // The result beside it has a figure for all that was asked for, and says nothing of the kind.
    expect(answer(1).textContent?.includes(KNOWN.none)).toBe(false);
  });

  test("test_what_nobody_chose_and_has_no_figure_has_no_line_on_a_result_and_is_named_in_its_working", () => {
    show(money);
    const noise = meta.data.features.find((feature) => feature.feature_id === "noise_exposure");

    expect(money.ranking.ranked[MARROWFEN]?.contributions.filter((part) => !part.present).map((part) => part.component)).toEqual([
      "feature:noise_exposure",
    ]);
    expect(money.ranking.spec.weights.find((weight) => weight.feature_id === "noise_exposure")?.provenance).toBe("default");
    expect(answer(MARROWFEN).textContent?.includes(KNOWN.none)).toBe(false);
    expect(lacked(MARROWFEN, nameOf(money.ranking.ranked[MARROWFEN]?.area_id ?? ""))).toEqual([]);
    expect(within(working(MARROWFEN)).getByText(COMPLETENESS.lacks([noise?.short_label ?? "none"]))).toBeInTheDocument();
  });
});

describe("the journeys", () => {
  const journeys = (at: number) => within(card(at).getByRole("table", { name: JOURNEYS.title }));

  test("test_each_journey_gives_the_place_how_both_times_and_within_or_over_in_words", () => {
    show(first);

    const cells = journeys(FARROWMERE).getAllByRole("row")[1] as HTMLElement;
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

  /** A release that holds no journey time: each journey is estimated from distance. */
  const estimated = {
    ranking: recordedAnswer("rank", "estimate/rank").body.data,
    ...recordedAnswer("explain_top", "estimate/explanations").body.data,
  };

  test("test_a_journey_that_was_estimated_says_its_band_and_that_it_is_an_estimate_and_gives_no_minutes", () => {
    show(estimated);

    const bands = new Set<string>();
    const inHand = new Set<boolean>();
    const lines = new Set<string>();
    // The line that says a journey is an estimate is one line, of every journey of a release.
    const [anyOfThem] = estimated.facts.filter((fact) => fact.template === "travel_estimated");
    if (anyOfThem === undefined) throw new Error("the recorded reasons cite no journey that was estimated");
    for (const [at, area] of estimated.ranking.ranked.slice(0, 5).entries()) {
      const [leg] = area.legs;
      if (!leg?.estimate) throw new Error("the recorded journey was not estimated");
      bands.add(leg.estimate);
      const row = journeys(at).getAllByRole("row")[1] as HTMLElement;
      const [how, long, limit] = within(row).getAllByRole("cell").map(said);
      // The fact of the journey itself, where the answer that brought the reasons brought it.
      const own = estimated.facts.find((fact) => fact.area_id === area.area_id && fact.template === "travel_estimated");
      inHand.add(own !== undefined);

      expect(leg.status).toBe("estimated");
      expect(how).toBe("Public transport");
      // The band in words, and that it is an estimate. No time, typical or missed. With the
      // fact of the journey in hand both are its own, as they came. With the fact of another
      // journey in hand the band is said in the words the website keeps for it, and that it
      // is an estimate in the line the service says of every such journey.
      expect(long).toBe(`${own?.slots.verdict ?? JOURNEYS.estimated[leg.estimate]}. ${anyOfThem.slots.estimated}`);
      lines.add((long ?? "").slice((long ?? "").indexOf(". ") + 2));
      expect([leg.minutes, leg.minutes_typical, leg.minutes_just_missed]).toEqual([null, null, null]);
      // The limit is said, and the journey is not said to be within it or over it.
      expect(limit).toBe("30 minutes Source");
      expect(journeys(at).queryByText(JOURNEYS.within)).toBeNull();
      expect(journeys(at).queryByText(JOURNEYS.over)).toBeNull();
      expect(journeys(at).queryByText(JOURNEYS.missing)).toBeNull();
    }
    expect(bands.size).toBeGreaterThan(0);
    // Both are in the recording, so both are held: a journey whose fact is in hand, and one whose fact is not.
    expect(inHand).toEqual(new Set([true, false]));
    // Seen in a browser: of five results the first three said it in the words of the service,
    // and the last two in older words of the website. One list says it one way.
    expect([...lines]).toEqual([anyOfThem.slots.estimated]);
  });

  test.each(["likely_within", "borderline", "likely_beyond"] as const)(
    "test_each_band_of_an_estimate_is_said_in_the_words_its_fact_says_it_in: %s",
    (band) => {
      // The comparison of the same search cites a fact of each band, each of an area of the ranking.
      const fact = recordedAnswer("compare", "estimate/compare").body.data.facts.find(
        (one) => one.template === "travel_estimated" && one.slots.band === band,
      );
      if (!fact) throw new Error(`no recorded fact of a journey that is ${band}`);
      const recorded = estimated.ranking.ranked.find((area) => area.area_id === fact.area_id);
      if (!recorded) throw new Error(`the area of the recorded fact that is ${band} is not ranked`);
      expect(recorded.legs[0]?.estimate).toBe(band);
      const ranking = { ...estimated.ranking, ranked: [recorded] };

      // With the fact of the journey in hand, the row says what the fact says, as it came:
      // the band, and the line that says it is an estimate and what it was worked out from.
      const { unmount } = show({ ranking, facts: [fact] });
      const row = () => said(journeys(0).getAllByRole("row")[1]);
      expect(journeys(0).getByText(fact.slots.verdict ?? "no verdict")).toBeInTheDocument();
      expect(row()).toContain(`${fact.slots.verdict}. ${fact.slots.estimated}`);
      expect(fact.slots.estimated).toMatch(/^This is an estimate\b.*\bdistance\b.*\bnot\b.*\btimetable\.$/);
      // The line is said once, and the website's own is not said beside it.
      expect(row().split(fact.slots.estimated ?? "no line")).toHaveLength(2);
      expect(row().split("timetable")).toHaveLength(2);
      unmount();

      // The website keeps words of its own for a journey whose fact is not in hand. For the
      // band they are the API's, word for word.
      show({ ranking, facts: [] });
      expect(journeys(0).getByText(JOURNEYS.estimated[band])).toBeInTheDocument();
      expect(fact.slots.verdict).toBe(JOURNEYS.estimated[band]);
      expect(row()).toContain(`${JOURNEYS.estimated[band]}. ${JOURNEYS.estimatedFrom}`);
    },
  );

  test("test_the_band_of_an_estimate_is_said_only_of_the_journey_it_is_of_and_the_line_of_every_journey", () => {
    const facts = recordedAnswer("compare", "estimate/compare").body.data.facts.filter(
      (one) => one.template === "travel_estimated",
    );
    const within30 = facts.find((one) => one.slots.band === "likely_within");
    const alike = facts.find((one) => one.slots.band === "borderline");
    // An area whose journey is borderline, and of which no fact of a journey was recorded.
    const other = estimated.ranking.ranked.find(
      (area) => area.legs[0]?.estimate === "borderline" && facts.every((one) => one.area_id !== area.area_id),
    );
    if (!within30 || !alike || !other) throw new Error("the recording holds no such journeys");
    const ranking = { ...estimated.ranking, ranked: [other] };
    const row = () => said(journeys(0).getAllByRole("row")[1]);
    // The words of the service are told from the words the website keeps by a mark that is in neither.
    const marked = (fact: Fact, mark: string): Fact => ({
      ...fact,
      slots: { ...fact.slots, verdict: `${fact.slots.verdict} ${mark}`, estimated: `${fact.slots.estimated} ${mark}` },
    });

    // The fact of another area is in hand, and says another band. The row of this area says
    // its own band, in the words the website keeps, and never the band of the other. That
    // it is an estimate is said of every journey in one line, which is the fact's.
    const another = show({ ranking, facts: [marked(within30, "(of another)")] });
    expect(row()).toContain(`${JOURNEYS.estimated.borderline}. ${within30.slots.estimated} (of another)`);
    expect(row().includes(within30.slots.verdict ?? "no verdict")).toBe(false);
    another.unmount();

    // Nor is the band of a fact said that says another band than the ranking does: it is of an older answer.
    const stale = { ...within30, area_id: other.area_id, fact_id: within30.fact_id.replace(within30.area_id, other.area_id) };
    const older = show({ ranking, facts: [marked(stale, "(of an older answer)")] });
    expect(row()).toContain(`${JOURNEYS.estimated.borderline}. `);
    expect(row().includes(within30.slots.verdict ?? "no verdict")).toBe(false);
    older.unmount();

    // The fact of another area that says the same band is not the fact of this journey
    // either: the band of this one is said in the words the website keeps.
    show({ ranking, facts: [marked(alike, "(of another)")] });
    expect(row()).toContain(`${JOURNEYS.estimated.borderline}. ${alike.slots.estimated} (of another)`);
    expect(row().includes(`${alike.slots.verdict} (of another)`)).toBe(false);
  });

  test("test_a_journey_that_has_a_time_in_hand_lends_an_estimate_no_line", () => {
    // A fact of a journey that was timed says nothing of an estimate: with no other in hand
    // the website says the line it keeps.
    const timed = first.facts.find((one) => one.kind === "travel" && one.template !== "travel_estimated");
    const [area] = estimated.ranking.ranked;
    if (!timed || !area?.legs[0]?.estimate) throw new Error("the recordings hold no such journeys");

    show({ ranking: { ...estimated.ranking, ranked: [area] }, facts: [timed] });

    expect(timed.slots.estimated).toBeUndefined();
    expect(said(journeys(0).getAllByRole("row")[1])).toContain(
      `${JOURNEYS.estimated[area.legs[0].estimate]}. ${JOURNEYS.estimatedFrom}`,
    );
  });

  test("test_an_estimate_is_given_up_only_where_it_is_likely_beyond_the_limit", () => {
    const { spec } = estimated.ranking;
    const about = (area: RankedArea) => ({ fact_ids: [`${area.area_id}/travel/${area.legs[0]?.place_id}.pt`] });
    const given = (band: string) => {
      const area = estimated.ranking.ranked.find((one) => one.legs[0]?.estimate === band);
      if (!area) throw new Error(`no recorded journey is ${band}`);
      // What the journeys are worth is left out of it, so that the band alone decides.
      const alone = {
        ...area,
        contributions: area.contributions.map((part) =>
          part.component === "commute" ? { ...part, utility: 1 } : part,
        ),
      };
      return isGivenUp(alone, about(area), spec.commutes, meta.data.limits.trade_off_max_utility);
    };

    expect(given("likely_beyond")).toBe(true);
    expect(given("borderline")).toBe(false);
    expect(given("likely_within")).toBe(false);
  });

  test("test_by_bike_there_is_one_time_and_no_service_to_miss", () => {
    const river = {
      ranking: recordedAnswer("rank", "rank-by-the-river").body.data,
      ...recordedAnswer("explain_top", "explanations-by-the-river").body.data,
    };

    show(river);

    const row = journeys(0).getAllByRole("row")[1] as HTMLElement;
    expect(within(row).getAllByRole("cell").map(said).slice(0, 3)).toEqual([
      "By bike",
      "5 minutes",
      JOURNEYS.notApply,
    ]);
    // The place is called by the name the answer gives it, and never by its position.
    expect(within(row).getByRole("rowheader")).toHaveTextContent("Tallowgate Guild Quarter");
  });

  test("test_a_place_is_named_by_the_answer_with_nothing_handed_down_from_the_box", () => {
    // Seen in a browser: one of two workplaces was shown as "Place 1", because the website
    // knew only the names of the places a person had picked from the list.
    show(two);

    expect(journeys(0).getAllByRole("rowheader").map(said)).toEqual(["Foxholt Market", "Wexmoor University"]);
    expect(cards()[0]?.textContent?.match(/\bPlace \d/)).toBeNull();
  });

  test("test_with_two_journeys_a_line_under_them_says_which_one_the_fit_uses", () => {
    show(two);

    const [area] = two.ranking.ranked;
    // The journey the fit uses is the one the API names first for the journey's part of the fit.
    expect(area?.contributions.find((one) => one.component === "commute")?.fact_ids[0]).toBe(
      "syn-n0016/travel/syn-p0026.pt",
    );
    const part = card(0).getByRole("heading", { name: JOURNEYS.title }).parentElement as HTMLElement;
    expect(within(part).getByText(JOURNEYS.usesOne("Wexmoor University"))).toBeInTheDocument();
    // A place is named by its name and nothing else: a reader heard "Wexmoor University counts".
    expect(journeys(0).getAllByRole("rowheader").map(said)).toEqual(["Foxholt Market", "Wexmoor University"]);
    // The settings stand behind one fold once a search is open. The line names the fold and the setting.
    expect(JOURNEYS.usesOne("x")).toContain(`"${JOURNEY.combine}" under ${REFINE.label}.`);
  });

  test("test_when_the_average_counts_the_line_says_so", () => {
    show({ ranking: { ...two.ranking, spec: { ...two.ranking.spec, commute_combine: "mean" } } });

    const part = card(0).getByRole("heading", { name: JOURNEYS.title }).parentElement as HTMLElement;
    expect(within(part).getByText(JOURNEYS.usesMean)).toBeInTheDocument();
    // The line that says one journey counts is said of neither place.
    for (const place of ["Foxholt Market", "Wexmoor University"]) {
      expect([place, part.textContent?.includes(JOURNEYS.usesOne(place))]).toEqual([place, false]);
    }
  });

  /** Recorded: one area chosen, 63 minutes from one place against a limit of 35, with no time to the other. */
  const gorsebeck = {
    ranking: recordedAnswer("rank", "rank-only-one").body.data,
    ...recordedAnswer("explain_top", "explanations-only-one").body.data,
  };

  test("test_a_journey_over_its_limit_counts_against_an_area_whose_other_journey_has_no_time", () => {
    // Seen in a browser, from an engine before 1.4.0: an area known to be 63 minutes from a
    // workplace, against a limit of 35, was ranked first, because its other journey had no
    // time and so neither counted. Now the journey that is known counts, and is the trade-off.
    show(gorsebeck);
    const [area] = gorsebeck.ranking.ranked;

    expect(area?.legs.map((leg) => [leg.status, leg.minutes])).toEqual([
      ["ok", 63],
      ["missing", null],
    ]);
    expect(area?.contributions.find((part) => part.component === "commute")).toMatchObject({ present: true });
    expect(tradeOff(0)).toHaveTextContent(gorsebeck.explanations[0]?.trade_off?.text ?? "no trade-off");
    // The sentence is the API's, and says by how much: 63 minutes against a limit of 35.
    expect(gorsebeck.explanations[0]?.trade_off?.text).toContain("28 minutes over the limit of 35 minutes you set");
    // The journey with no time is said to have none, in the API's own sentence.
    expect(card(0).getByText(gorsebeck.explanations[0]?.missing[0]?.text ?? "none")).toBeInTheDocument();
    expect(gorsebeck.facts.map((fact) => fact.template)).toEqual(
      expect.arrayContaining(["travel_pt_over", "missing_journey"]),
    );
    // Nothing says that the journeys do not count, because one of them does.
    expect(cards()[0]?.textContent?.includes(JOURNEYS.notCounted(2))).toBe(false);
  });

  /** An area none of whose journeys has a time: so the API counts no journey for it. */
  const noneKnown = (ranking: RankData) =>
    withFirstArea(ranking, (area) => ({
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

  /** The answer of a result: what it says before anything is pressed. */
  const answer = (at: number) => cards()[at]?.firstElementChild as HTMLElement;
  /** What a result says was asked for and has no figure, line by line. */
  const lacked = (at: number) => [...answer(at).querySelectorAll("[data-short][data-known='none']")].map((line) => line.textContent);

  test("test_journeys_that_do_not_count_because_none_has_a_time_are_said_on_the_result_to_be_not_known_and_in_its_working_why", () => {
    show({ ...two, ranking: noneKnown(two.ranking) });

    // On the result: the fit is not whole, and the journey is named as what has no figure.
    expect(within(answer(0).querySelector("header") as HTMLElement).getByText(KNOWN.some)).toBeInTheDocument();
    expect(lacked(0)).toContain(`${BREAKDOWN.journey}${KNOWN.none}`);
    expect(answer(0).textContent?.includes(JOURNEYS.notCounted(2))).toBe(false);
    // In its working, said heavier: it says how far to trust the fit.
    const line = within(working(0)).getByText(JOURNEYS.notCounted(2));
    expect(line.className).toBe("untested");
    expect(line.closest("[class*='completeness']")).not.toBeNull();
  });

  test("test_journeys_that_do_not_count_are_not_said_to_feed_the_fit_under_their_table", () => {
    show({ ...two, ranking: noneKnown(two.ranking) });

    const part = card(0).getByRole("heading", { name: JOURNEYS.title }).parentElement as HTMLElement;
    expect(within(part).getByText(JOURNEYS.usesNone(2))).toBeInTheDocument();
    // Neither of the lines that say which journey feeds the fit: none does.
    for (const place of ["Foxholt Market", "Wexmoor University"]) {
      expect([place, part.textContent?.includes(JOURNEYS.usesOne(place))]).toEqual([place, false]);
    }
    expect(part.textContent?.includes(JOURNEYS.usesMean)).toBe(false);
  });

  test("test_a_card_whose_journeys_count_says_nothing_of_journeys_that_do_not", () => {
    show(two);

    expect(lacked(0)).not.toContain(`${BREAKDOWN.journey}${KNOWN.none}`);
    for (const said of [JOURNEYS.notCounted(2), JOURNEYS.notCounted(1)]) expect(cards()[0]?.textContent?.includes(said)).toBe(false);
    expect(cards()[0]?.textContent ?? "").not.toMatch(/\bdo(es)? not count towards this fit\b/);
  });

  test("test_one_journey_with_no_time_says_that_it_does_not_count", () => {
    show({ ...first, ranking: noneKnown(first.ranking) });

    expect(lacked(0)).toEqual([`${BREAKDOWN.journey}${KNOWN.none}`]);
    expect(within(working(0)).getByText(JOURNEYS.notCounted(1))).toBeInTheDocument();
  });

  test("test_a_budget_and_a_journey_with_no_figure_are_each_said_once_in_the_working_in_a_sentence_of_their_own", () => {
    // Seen in a browser, in the working of a result: "You asked for Budget, but Burro has no
    // figure for it in this area, so the fit leaves it out." stood directly over "Your
    // budget is a firm limit, but Burro could not check it for this area, because it has no
    // cost figure." A budget and a journey are names of no thing a person asks for, and
    // each has a sentence of its own, which says all of it.
    const firm = show(two);
    expect(two.ranking.spec.budget.strictness).toBe("hard");
    expect(two.ranking.ranked[0]?.contributions.filter((part) => !part.present).map((part) => part.component)).toEqual(["budget"]);
    expect(within(working(0)).getAllByText(UNTESTED.over_budget)).toHaveLength(1);
    expect(working(0).textContent ?? "").not.toMatch(/You asked for/);
    expect(working(0).textContent?.includes(CARD.noCost)).toBe(false);
    firm.unmount();

    // A budget that is a guide leaves no area out, so nothing of it was left unchecked: it
    // counts for nothing in the fit, as a journey with no time does, and is said as one is.
    const guide = withFirstArea(first.ranking, (area) => ({
      ...area,
      contributions: area.contributions.map((part) =>
        part.component === "budget" ? { ...part, present: false, utility: null, contribution: 0, share: 0, fact_ids: [] } : part,
      ),
    }));
    const soft = show({ ...first, ranking: guide });
    expect([first.ranking.spec.budget.strictness, guide.ranked[0]?.untested_filters]).toEqual(["soft", []]);
    expect(lacked(0)).toEqual([`${BREAKDOWN.budget}${KNOWN.none}`]);
    expect(within(working(0)).getAllByText(CARD.noCost)).toHaveLength(1);
    expect(within(working(0)).getByText(CARD.noCost).className).toBe("untested");
    expect(working(0).textContent ?? "").not.toMatch(/You asked for/);
    expect(working(0).textContent?.includes(UNTESTED.over_budget)).toBe(false);
    soft.unmount();

    // Journeys of which none has a time, beside a firm budget that could not be checked.
    const neither = show({ ...two, ranking: noneKnown(two.ranking) });
    expect(within(working(0)).getAllByText(JOURNEYS.notCounted(2))).toHaveLength(1);
    expect(within(working(0)).getAllByText(UNTESTED.over_budget)).toHaveLength(1);
    expect(working(0).textContent ?? "").not.toMatch(/You asked for/);
    neither.unmount();

    // A vibe and a measurement are named, each in quotation marks, as the name of a thing is.
    expect(COMPLETENESS.lacksAsked(["Leafy"])).toBe('You asked for "Leafy", but Burro has no figure for it in this area, so the fit leaves it out.');
    expect(COMPLETENESS.lacks(["Less transport noise", "Cleaner air"])).toBe(
      'Burro has no figure for "Less transport noise" and "Cleaner air" in this area, so the fit leaves them out.',
    );
    expect(CARD.noCost).toBe("Your budget does not count towards this fit, because Burro has no cost figure for this area.");
  });

  test("test_the_journeys_lead_to_how_a_journey_is_timed", () => {
    show(first);

    // What a typical morning is, and what it is to just miss a service, are said in full on Methods, and nowhere on the card.
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

    expect(cost(FARROWMERE).getByText("£975 to £1,300")).toBeInTheDocument();
    expect(cost(FARROWMERE).getByText("1-bedroom home")).toBeInTheDocument();
    expect(cost(FARROWMERE).getByText("£1,125")).toBeInTheDocument();
    expect(cost(FARROWMERE).getByText("August 2026")).toBeInTheDocument();
    expect(cost(FARROWMERE).getByText(CONFIDENCE.high, { exact: false })).toBeInTheDocument();
    expect(cost(1).getByText(CONFIDENCE.medium, { exact: false })).toBeInTheDocument();
  });

  test("test_every_figure_of_the_cost_is_a_slot_of_the_fact_as_the_api_formatted_it", () => {
    show(first);

    const fact = profile("farrowmere").facts.find((one) => one.fact_id === "syn-n0006/cost/rent.bed_1");
    const shown = cost(FARROWMERE).getAllByText(/£[\d,]+/).map((figure) => figure.textContent ?? "");
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
    expect(cost(1).getByText(COST.inside)).toBeInTheDocument();
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

  test("test_a_visit_draws_nothing_of_a_cost_or_of_a_kind_of_home_on_a_result_or_in_its_working", () => {
    // Seen in a browser: the working of every result of a visit held "What homes cost",
    // with "Burro has no cost figure for this kind of home in this area." A visitor chose
    // no kind of home, and read that a figure was missing.
    const visit = {
      ranking: recordedAnswer("rank", "visiting/rank").body.data,
      ...recordedAnswer("explain_top", "visiting/explanations").body.data,
    };
    show(visit);

    expect(visit.ranking.spec.tenure).toBe("visit");
    expect(cards().length).toBeGreaterThan(5);
    // The page holds what homes cost in each of these areas, and draws none of it.
    const costs = visit.ranking.ranked.slice(0, 5).flatMap((area) => profile(slugOf(area.area_id)).facts.filter((fact) => fact.kind === "cost"));
    const kinds = [...new Set(costs.flatMap((fact) => fact.slots.segment ?? []))];
    expect(costs.length).toBeGreaterThan(10);
    expect(kinds.length).toBeGreaterThan(3);
    cards().forEach((result, at) => {
      expect([at, within(result).queryByRole("heading", { name: COST.title })]).toEqual([at, null]);
      expect([at, result.textContent?.includes(COST.none)]).toEqual([at, false]);
      expect([at, /£/.test(result.textContent ?? "")]).toEqual([at, false]);
      // Each kind of home as a word of its own: a vibe may be named for homes of two kinds.
      expect([at, kinds.filter((kind) => new RegExp(`\\b${kind}\\b`).test(result.textContent ?? ""))]).toEqual([at, []]);
      expect([at, result.querySelector(".cost, .range, .facts")]).toEqual([at, null]);
      // Nor is it said to be waited for, or to have failed to load.
      expect([at, result.textContent?.includes(RESULTS.detailsFailed)]).toEqual([at, false]);
    });
    // The rest of the working of a card is there: where the area is, and its nearest station.
    expect(within(working(0)).getByRole("heading", { name: RESULTS.whereTitle })).toBeInTheDocument();
    expect(within(working(0)).getByRole("group", { name: "Nearest station" })).toBeInTheDocument();
    // While the profile of an area is waited for, nothing holds the place of a cost.
    cleanup();
    show({ ...visit, withDetails: false });
    expect(within(working(0)).queryByRole("heading", { name: COST.title })).toBeNull();
    // A search to rent has its cost, as it had.
    cleanup();
    show(first);
    expect(cost(FARROWMERE).getByText("£975 to £1,300")).toBeInTheDocument();
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

    expect(cost(FARROWMERE).getByText(RESULTS.detailsFailed)).toBeInTheDocument();
    expect(cost(FARROWMERE).queryByText(COST.none)).toBeNull();
    // The card of another has its cost, which was loaded.
    const cindermoor = first.ranking.ranked.findIndex((area) => area.area_id === "syn-n0003");
    expect(cost(cindermoor).getByText("£775 to £1,050")).toBeInTheDocument();
  });
});

describe("how the fit is worked out", () => {
  /** The name the API gives a measure, by its id. */
  const measure = (id: string) => {
    const found = meta.data.features.find((feature) => feature.feature_id === id);
    if (found === undefined) throw new Error(`the recorded release holds no measure ${id}`);
    return found.label;
  };

  test("test_the_breakdown_is_closed_at_first_and_opens_to_a_table_of_everything_asked_for", async () => {
    const { user } = show(first);
    const button = card(FARROWMERE).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` });

    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(card(FARROWMERE).queryByRole("table", { name: BREAKDOWN.caption })).toBeNull();
    await user.click(button);

    const table = within(card(FARROWMERE).getByRole("table", { name: BREAKDOWN.caption }));
    // The rows are in the order the API gave the contributions in: the website sorts nothing.
    expect(first.ranking.ranked[FARROWMERE]?.contributions.map((part) => part.component)).toEqual([
      "tag:quiet_residential",
      "commute",
      "budget",
      "tag:leafy",
      "feature:air_no2",
      "feature:station_walk",
      "feature:noise_exposure",
      "feature:station_lines",
      "feature:park_proximity",
      "feature:highstreet_access",
    ]);
    // Each is named as the API names it with the form: a vibe and a measure by its label,
    // which the website writes none of. A journey and a budget are named by the website.
    expect(table.getAllByRole("rowheader").map((header) => header.textContent)).toEqual([
      "Quiet streets",
      BREAKDOWN.journey,
      BREAKDOWN.budget,
      "Leafy",
      measure("air_no2"),
      measure("station_walk"),
      measure("noise_exposure"),
      measure("station_lines"),
      measure("park_proximity"),
      measure("highstreet_access"),
    ]);
    expect(["air_no2", "station_walk", "noise_exposure"].map(measure)).toEqual([
      "Nitrogen dioxide in the air, as a modelled average over a year",
      "Distance to the nearest station entrance, in a straight line",
      "Share of residents exposed to 55 dB or more of transport noise",
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
    await user.click(card(FARROWMERE).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` }));

    const rows = within(card(FARROWMERE).getByRole("table", { name: BREAKDOWN.caption })).getAllByRole("row");
    const [, journey] = first.ranking.ranked[FARROWMERE]?.contributions ?? [];

    // Recorded of the journey, which is the second row: weight 0.4, share 0.1951,
    // contribution 0.1659. To the nearest whole number the share would be 20 and the
    // contribution 17.
    expect(journey).toMatchObject({ component: "commute", share: 0.1951, contribution: 0.1659 });
    expect(within(rows[2] as HTMLElement).getAllByRole("cell").slice(0, 3).map(said)).toEqual([
      "40 of 100",
      "19%",
      "16 of 100",
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
    // "67 of 100" for noise, a few lines under "quieter than 65% of the 20 areas". Recorded
    // now: it is ranked on 62.5, and one area is level with it, so it is quieter than 60%.
    const noise = area?.contributions.find((part) => part.component === "feature:noise_exposure");
    expect(noise?.utility).toBe(0.625);
    expect(table.textContent?.includes(`${floored(noise?.utility ?? 0)} of 100`)).toBe(false);
    expect(within(table).queryByRole("columnheader", { name: /how well/i })).toBeNull();
    // What is said in its place is where the fact says the area stands, in the API's words.
    const fact = two.facts.find((one) => one.fact_id === noise?.fact_ids[0]);
    expect(fact?.slots.standing).toBe("quieter than 60% of the 20 areas Burro compared");
    expect(table).toHaveTextContent(fact?.slots.standing ?? "no standing");
  });

  test.each([
    ["rank-first", "explanations-first"],
    ["rank-two-journeys", "explanations-two-journeys"],
    ["rank-buyer-family", "explanations-buyer-family"],
  ] as const)("test_no_figure_of_an_opened_breakdown_is_one_the_api_did_not_send: %s", async (ranked, explained) => {
    const ranking = recordedAnswer("rank", ranked).body.data;
    const { explanations, facts } = recordedAnswer("explain_top", explained).body.data;
    const { user } = show({ ranking, explanations, facts });

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
      ]);

      expect(within(table).getAllByRole("row").length).toBe(area.contributions.length + 1);
      expect(figuresNotFrom(table, allowed)).toEqual([]);
    }
  });

  test("test_each_row_gives_what_the_data_says_in_the_apis_words_with_its_source", async () => {
    const { user } = show(first);
    await user.click(card(FARROWMERE).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` }));

    const rows = within(card(FARROWMERE).getByRole("table", { name: BREAKDOWN.caption })).getAllByRole("row");
    const walk = rows.find((row) => within(row).queryByRole("rowheader", { name: measure("station_walk") }));
    const fact = profile("farrowmere").facts.find((one) => one.fact_id === "syn-n0006/feature/station_walk");
    const says = within(walk as HTMLElement).getAllByRole("cell").at(-1) as HTMLElement;

    expect(within(says).getByText(FACT_COLUMNS.value).nextElementSibling).toHaveTextContent(fact?.slots.value ?? "none");
    expect(within(says).getByText(FACT_COLUMNS.standing).nextElementSibling).toHaveTextContent(
      fact?.slots.standing ?? "none",
    );
    // Its source is named by the row it stands in, so that no two of a card are named alike.
    await user.click(
      within(says).getByRole("button", { name: `Source for ${BREAKDOWN.title}: ${measure("station_walk")}` }),
    );
    expect(within(says).getByRole("link", { name: "Synthetic test data" })).toBeInTheDocument();
  });

  test("test_a_thing_whose_fact_is_not_in_hand_says_only_that_there_is_a_figure", async () => {
    const { user } = show(first);
    // A row has no profile and no reasons, so no fact of its own is in hand.
    await user.click(card(5).getByRole("button", { name: /^How the fit is worked out/ }));

    const rows = within(card(5).getByRole("table", { name: BREAKDOWN.caption })).getAllByRole("row").slice(1);
    const area = first.ranking.ranked[5];

    expect(rows.map((row) => said(within(row).getAllByRole("cell").at(-1)))).toEqual(
      area?.contributions.map((part) => (part.present ? BREAKDOWN.has : BREAKDOWN.hasNot)),
    );
  });

  test("test_something_with_no_figure_says_so_and_adds_nothing", async () => {
    const { user } = show(money);
    await user.click(card(MARROWFEN).getByRole("button", { name: `${BREAKDOWN.title}: Marrowfen` }));

    const rows = within(card(MARROWFEN).getByRole("table", { name: BREAKDOWN.caption })).getAllByRole("row");
    const quiet = rows.find((row) =>
      within(row).queryByRole("rowheader", { name: "Share of residents exposed to 55 dB or more of transport noise" }),
    );

    expect(within(quiet as HTMLElement).getAllByRole("cell").map(said)).toEqual([
      "5 of 100",
      "0%",
      "0 of 100",
      BREAKDOWN.hasNot,
    ]);
  });

  test("test_the_breakdown_can_be_stacked_on_a_narrow_screen_and_is_still_a_table", async () => {
    const { user } = show(first);
    await user.click(card(FARROWMERE).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` }));
    const table = card(FARROWMERE).getByRole("table", { name: BREAKDOWN.caption });
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

describe("a result as the look draws it", () => {
  const SHEET = readFileSync(path.join(__dirname, "ResultList.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const RULES = rulesOf(SHEET);
  const atRest = (selector: string) =>
    new Map(
      RULES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) =>
        [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]),
      ),
    );
  /** The box of a result, and the box of its working under it. */
  const boxesOf = (at: number) => [...(cards()[at] as HTMLElement).children] as HTMLElement[];
  const opens = (at: number) => card(at).getByRole("button", { name: /^Show the working: / });

  test("test_the_rank_is_a_pennant_which_is_the_same_for_the_first_as_for_the_tenth", async () => {
    // Nobody wins: no medal, no gold for the first, and no pennant that is larger than the next.
    const { user } = show({ ...first, opened: false });
    await user.click(screen.getByRole("button", { name: /^Show \d+ more$/ }));
    const pennants = cards().map((one) => one.querySelector("header p:first-child > span") as HTMLElement);

    expect(pennants).toHaveLength(first.ranking.ranked.length);
    expect(new Set(pennants.map((one) => one.style.getPropertyValue("--art")))).toEqual(new Set(['url("/art/ui-flag.png")']));
    expect(new Set(pennants.map((one) => `${one.className} ${one.style.getPropertyValue("--w")} ${one.style.getPropertyValue("--h")}`)).size).toBe(1);
    // The number is drawn for the eye, and the rank is said in words to whoever hears the page.
    expect(pennants.map((one) => one.textContent)).toEqual(first.ranking.ranked.map((area) => `Rank ${area.rank}${area.rank}`));
    for (const one of pennants) expect(one.querySelector("[aria-hidden='true']")?.textContent).toMatch(/^\d+$/);
    // Nothing of a result is drawn for the first alone: a card is a card, whichever it is.
    expect(RULES.filter((rule) => /:(first|last|nth)-(child|of-type)/.test(rule.selector) && /\.(item|card|result|rank|name|fit)\b/.test(rule.selector))).toEqual([]);
  });

  test("test_a_card_stands_in_a_box_and_a_row_in_a_plain_edge_of_ink", () => {
    show({ ...first, opened: false });

    // A box with a shadow on every row of a long list would be noise.
    expect(cards().map((one) => one.firstElementChild?.getAttribute("data-kind"))).toEqual([
      ...Array.from({ length: 5 }, () => "box"),
      ...Array.from({ length: 5 }, () => "plain"),
    ]);
    // The article is no box of its own: it holds the answer, and the working under it.
    for (const property of ["background", "border", "box-shadow", "padding"]) {
      expect([property, atRest(".result").get(property)]).toEqual([property, undefined]);
    }
  });

  test("test_the_area_that_is_chosen_has_the_box_of_what_is_in_hand_and_says_so", () => {
    show({ ...first, opened: false, selectedId: "syn-n0005" });
    const chosen = cards().findIndex((one) => one.getAttribute("aria-current") === "true");

    expect(cards().map((one) => one.firstElementChild?.getAttribute("data-kind") === "box-on")).toEqual(
      cards().map((_, at) => at === chosen),
    );
    // A row that is chosen has a band of amber inside its edge of ink: amber is not told from cream.
    expect(atRest('.result[aria-current="true"] > .row').get("box-shadow")).toBe("inset 0 0 0 calc(var(--px) * 2) var(--chosen)");
  });

  test("test_none_of_the_three_ways_on_is_drawn_as_the_button_that_matters_most", async () => {
    // The one cobalt button in sight is Search.
    const { user } = show({ ...first, opened: false });
    const faces = () => [...document.querySelectorAll<HTMLElement>("[class*='waysOn'] [data-kind]")];

    // Each of the two at the foot has the face of a button of the look, and so has the way
    // to compare in the heading, which is amber once its area is chosen. None is chosen here.
    expect(faces()).toHaveLength(2 * SHOWN_AT_FIRST);
    expect(new Set(faces().map((face) => face.dataset.kind))).toEqual(new Set(["plain"]));
    const inTheHeadings = [...document.querySelectorAll<HTMLElement>("header [data-chosen] [data-kind]")];
    expect(inTheHeadings).toHaveLength(SHOWN_AT_FIRST);
    expect(new Set(inTheHeadings.map((face) => face.dataset.kind))).toEqual(new Set(["plain"]));
    await user.click(opens(FARROWMERE));
    // Nor is any button of a working: what takes an area away has an edge of poppy.
    const inTheWorking = [...working(FARROWMERE).querySelectorAll<HTMLElement>("[data-kind]")].map((face) => face.dataset.kind);
    expect(inTheWorking).toEqual(["plain", "plain", "stop"]);
    expect(document.querySelectorAll("[data-kind='go']")).toHaveLength(0);
    // No rule of the sheet draws anything of a result in cobalt, but the name under the pointer.
    const cobalt = RULES.filter((rule) => [...rule.sets.values()].some((value) => /var\(--(cobalt|accent)\)/.test(value)));
    expect(cobalt.map((rule) => [rule.selector, [...rule.sets.keys()]])).toEqual([[".toArea:hover", ["color"]]]);
  });

  test("test_each_of_the_three_ways_on_is_a_native_control_which_the_part_that_draws_it_draws", () => {
    show({ ...first, opened: false });

    for (const at of [0, 4, 5, 9]) {
      const result = cards()[at] as HTMLElement;
      const ways = [...result.querySelectorAll<HTMLElement>("[class*='waysOn'] :is(a, button)")];
      const compare = result.querySelector<HTMLElement>("header [data-chosen] > button") as HTMLElement;
      expect(ways.map((way) => way.tagName)).toEqual(["BUTTON", "A"]);
      expect(ways.map((way) => way.classList.contains("target"))).toEqual([true, true]);
      // The way to compare is drawn by the part that holds the comparison, which gives it the
      // face of a button of the look and makes it as high as a main control where there is room.
      expect(compare.tagName).toBe("BUTTON");
      expect(compare.classList.contains("target-min")).toBe(true);
      expect([...ways, compare].map((way) => way.querySelectorAll(":scope > [data-kind]").length)).toEqual([1, 1, 1]);
      // A result hands none of them a picture: it carries nothing of how a button is drawn.
      expect(result.querySelector("[class*='waysOn']")?.hasAttribute("style")).toBe(false);
      expect(compare.closest("[data-chosen]")?.hasAttribute("style")).toBe(false);
    }
    // So the sheet of a result draws no button of its own: it says where each stands, and
    // on a narrow result how high the least of them is, and no more.
    const drawsAButton = RULES.filter(
      (rule) =>
        /^button\b/.test(subjectOf(rule.selector)) &&
        [...rule.sets.keys()].some((property) => /^(border|background|color|font|padding|min-height)/.test(property)),
    );
    expect(RULES.filter((rule) => /^button\b/.test(subjectOf(rule.selector))).length).toBeGreaterThan(0);
    expect(drawsAButton.map((rule) => [rule.under, rule.selector, [...rule.sets]])).toEqual([
      ["@container (max-width: 30rem)", '.list[data-buttons="small"] .titled > [data-chosen] > button', [["min-height", "var(--target-min)"]]],
      ["@container (max-width: 30rem)", '.list[data-buttons="small"] .waysOn > span > button', [["min-height", "var(--target-min)"]]],
    ]);
  });

  test("test_on_a_narrow_result_the_buttons_are_as_high_as_a_small_button_so_that_the_way_to_compare_costs_the_first_result_of_a_phone_no_height", () => {
    // Measured on a phone, 390 by 844, after a plain search. Before the way to compare stood
    // in the heading the first result stood from 454 to 828, 374 px high, with 16 px to
    // spare. With it in the heading, beside what stands beside the name, the heading is 22
    // px higher. The two ways on at the foot have a line each of one line, where they had
    // two, and are as high as a small button is: the foot is 20 px lower. The first result
    // is 374 px high as it was, and whole on the first screen.
    const { unmount } = show({ ...first, opened: false });
    const NARROW = "@container (max-width: 30rem)";
    const small = RULES.filter((rule) => rule.under === NARROW && /data-buttons="small"/.test(rule.selector));

    expect(ON_A_NARROW_RESULT_A_BUTTON_IS).toBe("small");
    expect(lists().map((one) => one.dataset.buttons)).toEqual(["small", "small"]);
    expect(small.map((rule) => rule.selector)).toEqual([
      '.list[data-buttons="small"] .titled > [data-chosen] > button',
      '.list[data-buttons="small"] .waysOn > a',
      '.list[data-buttons="small"] .waysOn > span > button',
    ]);
    // Each is as high as its words and its edge, and never less than the smallest a control may be.
    expect(small.map((rule) => [...rule.sets])).toEqual(small.map(() => [["min-height", "var(--target-min)"]]));
    // They weigh more than what makes a button as high as a main control, wherever that is said.
    for (const rule of small) expect([rule.selector, heavier(weightOf(rule.selector), weightOf(".fills.small"))]).toEqual([rule.selector, true]);
    // No other rule says how high a button of a result is, on a result of any width.
    const floors = RULES.filter((rule) => rule.sets.has("min-height"));
    expect(floors).toEqual(small);
    unmount();

    // The other way is one line: the buttons of a narrow result are then as high as a main control.
    show({ ...first, opened: false, buttons: "main" });
    expect(lists().map((one) => one.dataset.buttons)).toEqual(["main", "main"]);
  });

  test("test_on_a_narrow_result_the_way_to_compare_stands_at_the_far_end_of_the_line_of_what_stands_beside_the_name", () => {
    const NARROW = "@container (max-width: 30rem)";
    const narrow = (selector: string) =>
      new Map(RULES.filter((rule) => rule.under === NARROW && rule.selector === selector).flatMap((rule) => [...rule.sets]));

    // The name and the fit have the first line, and what follows begins the next.
    expect([narrow(".name").get("order"), narrow(".fit").get("order")]).toEqual(["1", "2"]);
    expect([...narrow(".titled::after")]).toEqual([
      ["content", '""'],
      ["flex", "0 0 100%"],
      ["order", "3"],
    ]);
    // What stands beside the name has what room the button leaves it, and the button is never narrowed.
    expect([narrow(".borough").get("order"), narrow(".borough").get("flex"), narrow(".borough").get("min-width")]).toEqual(["4", "1 1 0", "0"]);
    expect([narrow(".titled > [data-chosen]").get("order"), narrow(".titled > [data-chosen]").get("flex")]).toEqual(["5", "0 0 auto"]);
  });

  test("test_a_narrow_result_is_as_high_once_its_area_is_chosen_as_it_was", () => {
    // Seen in a browser, on a phone: adding the first area pressed the head of its result
    // out of shape. What was said under the button took the room of what stands beside the
    // name, and the result went from 373 to 412 px high under the press. With two chosen
    // the way to the comparison stood under the button, and the result was 19 px higher.
    const theirs = rulesOf(readFileSync(path.join(__dirname, "..", "CompareTray", "CompareTray.module.css"), "utf8"));
    const laidOver = new Map(
      theirs.filter((rule) => rule.under === null && rule.selector === '.beside[data-small="true"] > .near').flatMap((rule) => [...rule.sets]),
    );
    // The part that draws the button lays the way to the comparison over the page, where it
    // takes no room, and sets it down under the button while a keyboard has it.
    expect([laidOver.get("position"), laidOver.get("transform")]).toEqual(["absolute", "translateY(-9999px)"]);
    // A result says that it has the room for it only where it is wider than a narrow one.
    const roomy = RULES.filter((rule) => /\[data-chosen\] > a$/.test(rule.selector));
    expect(roomy.map((rule) => [rule.under, rule.selector])).toEqual([
      ["@container (width > 30rem)", ".list .heading .titled > [data-chosen] > a"],
    ]);
    expect([roomy[0]?.sets.get("position"), roomy[0]?.sets.get("transform")]).toEqual(["static", "none"]);
    // It weighs more than what lays the way over the page, whichever sheet is read last.
    expect(heavier(weightOf(".list .heading .titled > [data-chosen] > a"), weightOf('.beside[data-small="true"] > .near'))).toBe(true);
    // Nothing of the sheet is moved by the focus, the pointer or a press.
    const moved = RULES.filter(
      (rule) =>
        /:(hover|focus|focus-within|focus-visible|active)\b/.test(rule.selector) &&
        [...rule.sets.keys()].some((property) => /^(transform|translate|width|height|margin|padding|inset|top|display)/.test(property)),
    );
    expect(moved.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_where_a_result_has_a_town_and_no_room_beside_it_the_way_to_compare_has_the_line_under_the_town", () => {
    const MIDDLE = "@container (width > 36rem) and (width < 46rem)";
    const middle = (selector: string) =>
      new Map(RULES.filter((rule) => rule.under === MIDDLE && rule.selector === selector).flatMap((rule) => [...rule.sets]));
    const way = middle(".list[data-narrow] .titled > [data-chosen]");

    // What the name stands with is laid out by the heading, part by part.
    expect([...middle(".list[data-narrow] .titled")]).toEqual([["display", "contents"]]);
    expect(middle(".list[data-narrow] .heading").get("grid-template-columns")).toBe("auto minmax(0, 1fr) auto auto");
    // It stands under the town, at the far end, and what it says beside itself before it on
    // its line: so the heading is no higher once the area is chosen.
    expect([way.get("grid-row"), way.get("grid-column"), way.get("justify-self")]).toEqual(["3", "1 / -1", "end"]);
    expect([way.get("display"), way.get("flex-direction")]).toEqual(["flex", "row-reverse"]);
    expect(middle(".list[data-narrow] .heading > .town > figcaption").get("grid-row")).toBe("4");
    // Where a result is wider it stands beside the town, in the line of the name and the fit.
    const beside = new Map(RULES.filter((rule) => rule.under === null && rule.selector === ".titled > [data-chosen]").flatMap((rule) => [...rule.sets]));
    expect([beside.get("grid-column"), beside.get("grid-row")]).toEqual(["3", "1 / span 2"]);
  });

  test("test_the_button_that_opens_the_working_is_amber_while_it_is_open_and_never_says_that_it_is_pressed", async () => {
    const { user } = show({ ...first, opened: false });
    const face = () => opens(FARROWMERE).querySelector("[data-kind]") as HTMLElement;

    expect([opens(FARROWMERE).getAttribute("aria-expanded"), face().dataset.kind]).toEqual(["false", "plain"]);
    expect(face().style.getPropertyValue("--art")).toBe('url("/art/ui-button.png")');
    await user.click(opens(FARROWMERE));

    // What is on is amber. It is said as a thing that is open is said, as it always was.
    expect([opens(FARROWMERE).getAttribute("aria-expanded"), face().dataset.kind]).toEqual(["true", "on"]);
    expect(face().style.getPropertyValue("--art")).toBe('url("/art/ui-button-on.png")');
    expect(opens(FARROWMERE)).not.toHaveAttribute("aria-pressed");
    expect(opens(FARROWMERE)).toHaveTextContent(RESULTS.showWorking);
    // No other result is drawn as open.
    expect(document.querySelectorAll("[class*='waysOn'] [data-kind='on']")).toHaveLength(1);
  });

  test("test_the_working_opens_under_the_result_in_a_box_of_its_own_and_is_not_on_the_page_until_then", async () => {
    const { user } = show({ ...first, opened: false });

    for (const at of [FARROWMERE, 6]) {
      const [answer, under] = boxesOf(at);
      expect(boxesOf(at)).toHaveLength(2);
      expect(under?.id).toBe(opens(at).getAttribute("aria-controls"));
      expect([under?.hasAttribute("hidden"), under?.textContent]).toEqual([true, ""]);
      expect(answer?.contains(opens(at))).toBe(true);
      await user.click(opens(at));

      expect(under?.hasAttribute("hidden")).toBe(false);
      expect(under?.getAttribute("data-kind")).toBe("box");
      // It says whose working it is, at its head: a page may hold several, each a long way down.
      const name = areas.find((area) => area.area_id === first.ranking.ranked[at]?.area_id)?.name ?? "";
      expect(under?.firstElementChild?.textContent).toBe(CARD.workingOf(name));
      expect(under?.firstElementChild?.tagName).toBe("P");
    }
    // A box that is hidden takes no room, whatever else is said of it.
    expect(new Map(RULES.filter((rule) => rule.selector === ".working[hidden]").flatMap((rule) => [...rule.sets])).get("display")).toBe("none");
  });

  test("test_escape_closes_the_working_from_inside_it_and_puts_the_focus_back_on_its_button", async () => {
    const { user } = show({ ...first, opened: false });

    await user.click(opens(FARROWMERE));
    const name = areas.find((area) => area.area_id === first.ranking.ranked[FARROWMERE]?.area_id)?.name ?? "";
    const inside = within(working(FARROWMERE)).getByRole("button", { name: RESULTS.showOnMap(name) });
    inside.focus();
    await user.keyboard("{Escape}");

    // What had the focus goes when the working closes. The focus does not go with it.
    expect(opens(FARROWMERE)).toHaveAttribute("aria-expanded", "false");
    expect(opens(FARROWMERE)).toHaveFocus();
    // A source that is open inside it closes first, and the working stays.
    await user.click(opens(FARROWMERE));
    const source = within(working(FARROWMERE)).getAllByRole("button", { name: /^Source/ })[0] as HTMLElement;
    await user.click(source);
    await user.keyboard("{Escape}");
    expect(source).toHaveAttribute("aria-expanded", "false");
    expect(opens(FARROWMERE)).toHaveAttribute("aria-expanded", "true");
    // From a way on that opens nothing, Escape closes nothing.
    card(FARROWMERE).getByRole("link", { name: RESULTS.moreLikeOf(name) }).focus();
    await user.keyboard("{Escape}");
    expect(opens(FARROWMERE)).toHaveAttribute("aria-expanded", "true");
  });

  test("test_the_name_of_an_area_and_a_short_label_are_set_in_the_face_of_names_and_all_that_is_read_in_the_reading_face", () => {
    const faced = RULES.filter((rule) => rule.under === null).flatMap((rule) =>
      [...rule.sets].filter(([property]) => property === "font" || property === "font-family").map(([, value]) => [rule.selector, value.replace(/\s+/g, " ")] as const),
    );
    const inTheFaceOfNames = faced.filter(([, font]) => /var\(--font-name\)/.test(font)).map(([selector]) => selector);

    // The name of an area, the word over the fit, the label over a part, the word over a
    // trade-off, whose working it is, and the name of an area that is not ranked.
    expect(inTheFaceOfNames.sort()).toEqual([".apartName", ".fitLabel", ".name", ".tag", ".tradeOffWord", ".workingOf"].sort());
    // A heading in the face of names is never under thirty pixels. A short label may be twenty.
    expect(atRest(".name").get("font")).toBe("400 var(--name-2) / 1 var(--font-name)");
    for (const selector of inTheFaceOfNames) {
      expect([selector, /^400 var\(--name-[12]\) /.test(atRest(selector).get("font") ?? ""), atRest(selector).get("font-synthesis")]).toEqual([selector, true, "none"]);
    }
    // A fit is a figure, and is read: it is set in the reading face, heavy.
    expect(atRest(".fitFigure").get("font")).toBe("700 var(--name-2) / 1 var(--font-say)");
    expect(faced.filter(([, font]) => !/var\(--font-(name|say)\)/.test(font))).toEqual([]);
  });

  test("test_a_trade_off_stands_out_by_where_it_stands_and_how_it_is_drawn_and_nothing_of_it_is_red", () => {
    // The founder, who had walked the website three times: "The trade of section is
    // important, the icon of a red arrow doesnt make sense, and the section could stand out
    // a bit more visually." Red says danger, and a trade-off is what was given for what was
    // got: nothing of it says that the area is the worse for it.
    show({ ...first, opened: false });
    const heading = card(FARROWMERE).getByRole("heading", { name: RESULTS.tradeOffTitle });
    const gives = heading.parentElement as HTMLElement;
    const ofATradeOff = RULES.filter((rule) => /\.tradeOff\w*\b/.test(rule.selector));
    const colours = ofATradeOff.flatMap((rule) => [...rule.sets.values()].flatMap((value) => value.match(/var\(--[a-z0-9-]+\)/g) ?? []));

    expect(ofATradeOff.length).toBeGreaterThan(6);
    expect(colours.filter((colour) => /poppy|tradeoff|error|amber|good|hedge/.test(colour))).toEqual([]);
    expect(SHEET).not.toMatch(/tradeOffMark/);
    // Poppy is left in the working alone: over a journey that is over its limit, beside a
    // fault, and nowhere on a result as it is first shown.
    const poppy = RULES.filter((rule) => [...rule.sets].some(([, value]) => /var\(--(poppy|tradeoff-mark|error-edge)\)/.test(value)));
    expect(poppy.map((rule) => rule.selector)).toEqual([".over::before", ".failed"]);
    // Every word of it is ink, but the word of its heading on its plate, which is the colour that is read on.
    expect(atRest(".tradeOff").get("color")).toBe("var(--ink)");
    expect(atRest('.tradeOff[data-drawn="band"] .tradeOffWord').get("background")).toBe("var(--ink)");
    expect(atRest('.tradeOff[data-drawn="band"] .tradeOffWord').get("color")).toBe("var(--page)");
    // Its drawing is dress, and stands before its word: the word is what is heard.
    const drawn = heading.firstElementChild as HTMLElement;
    expect(drawn).toHaveAttribute("aria-hidden", "true");
    expect(drawn.style.getPropertyValue("--art")).toBe('url("/art/ui-tradeoff.png")');
    expect(said(heading)).toBe(RESULTS.tradeOffTitle);
    expect(gives.querySelectorAll("button, a")).toHaveLength(0);
  });

  test("test_the_trade_off_is_built_two_ways_and_one_line_chooses_between_a_band_with_the_scales_and_a_box_with_two_arrows", () => {
    expect(TRADE_OFF_MAY_BE_DRAWN).toEqual(["band", "box"]);
    expect(TRADE_OFF_MAY_BE_DRAWN).toContain(TRADE_OFF_DRAWN);
    const drawnFor: Readonly<Record<TradeOffDrawn, string>> = { band: "ui-tradeoff", box: "ui-tradeoff-b" };

    const asDrawn = TRADE_OFF_MAY_BE_DRAWN.map((way) => {
      const { unmount } = show({ ...first, opened: false, tradeOff: way });
      const parts = cards()
        .slice(0, 5)
        .map((_, at) => tradeOff(at));
      expect(parts.map((part) => part.getAttribute("data-drawn"))).toEqual(parts.map(() => way));
      expect(parts.map((part) => (part.querySelector("h4 > [aria-hidden='true']") as HTMLElement).style.getPropertyValue("--art"))).toEqual(
        parts.map(() => `url("/art/${drawnFor[way]}.png")`),
      );
      const says = parts.map((part) => said(part));
      unmount();
      return says;
    });
    // Either way it says the same: its word, and the sentence of the service, word for word.
    expect(asDrawn[0]).toEqual(asDrawn[1]);
    expect(asDrawn[0]).toEqual(first.explanations.slice(0, 5).map((one) => expect.stringContaining(one.trade_off?.text ?? RESULTS.noTradeOff)));

    // On a band of its own, from edge to edge of the result: sand, between two rules of ink.
    const band = atRest('.tradeOff[data-drawn="band"]');
    expect([band.get("background"), band.get("border-block"), band.get("margin-inline")]).toEqual([
      "var(--sand)",
      "var(--edge) solid var(--ink)",
      "calc(var(--inside) * -1)",
    ]);
    expect(band.get("padding")).toBe("var(--space-2) var(--inside)");
    // In a box of its own within the result: cream, in an edge of ink, with the hard shadow
    // of the look, whose room it keeps inside the result.
    const box = atRest('.tradeOff[data-drawn="box"]');
    expect([box.get("background"), box.get("border"), box.get("box-shadow")]).toEqual(["var(--page)", "var(--edge) solid var(--ink)", "var(--box-shadow)"]);
    expect([box.get("margin-inline-end"), box.get("margin-block-end")]).toEqual(["calc(var(--px) * 2)", "calc(var(--px) * 2)"]);
    // Neither moves under a press, the pointer or the focus: nothing of it is pressed.
    expect(RULES.filter((rule) => /tradeOff/.test(rule.selector) && /:(hover|focus|active)/.test(rule.selector))).toEqual([]);
  });

  test("test_the_key_to_the_drawings_shows_the_drawing_of_a_trade_off_that_a_result_draws_and_one_line_chooses_for_both", () => {
    // A result and the key each chose, in a line of their own, and nothing held the two
    // together: with one changed alone, the key explained a drawing that no result drew.
    const ofATradeOff = (part: Element) =>
      [...part.querySelectorAll<HTMLElement>("[style*='/art/ui-tradeoff']")].map((one) => one.style.getPropertyValue("--art"));
    /** What a result draws beside the word, and what the key shows, each as it is handed a way or none. */
    const drawnAndShown = (way?: TradeOffDrawn) => {
      const result = show({ ...first, opened: false, ...(way === undefined ? {} : { tradeOff: way }) });
      const drawn = ofATradeOff(tradeOff(FARROWMERE));
      result.unmount();
      const key = render(way === undefined ? <Key meta={meta.data} /> : <Key meta={meta.data} tradeOff={BESIDE_A_TRADE_OFF[way]} />);
      const shown = ofATradeOff(key.container);
      key.unmount();
      return { drawn, shown };
    };

    for (const way of TRADE_OFF_MAY_BE_DRAWN) {
      const { drawn, shown } = drawnAndShown(way);
      expect([way, drawn]).toEqual([way, [`url("/art/${DRAWING_OF_A_TRADE_OFF[BESIDE_A_TRADE_OFF[way]]}.png")`]]);
      expect([way, shown]).toEqual([way, drawn]);
    }
    // The two ways are two drawings, so that the one is told from the other.
    expect(new Set(TRADE_OFF_MAY_BE_DRAWN.map((way) => DRAWING_OF_A_TRADE_OFF[BESIDE_A_TRADE_OFF[way]])).size).toBe(2);
    // Handed nothing, each goes by the one line that chooses.
    const { drawn, shown } = drawnAndShown();
    expect(drawn).toEqual([`url("/art/${DRAWING_OF_A_TRADE_OFF[BESIDE_A_TRADE_OFF[TRADE_OFF_DRAWN]]}.png")`]);
    expect(shown).toEqual(drawn);
    expect(TRADE_OFF_SHOWN).toBe(BESIDE_A_TRADE_OFF[TRADE_OFF_DRAWN]);
    // No line of the key's own chooses: what it shows is worked out from the line of a result.
    const ofTheKey = readFileSync(path.join(__dirname, "../VibesList/look.ts"), "utf8");
    expect(ofTheKey).toMatch(/^export const TRADE_OFF_SHOWN: TradeOffShown = BESIDE_A_TRADE_OFF\[TRADE_OFF_DRAWN\];$/m);
    // And one table names the drawings of a trade-off, for both: no part names one itself.
    const SRC = path.resolve(__dirname, "..", "..");
    const written = (folder: string): [file: string, holds: string][] =>
      readdirSync(folder, { withFileTypes: true }).flatMap((entry): [string, string][] => {
        const file = path.join(folder, entry.name);
        if (entry.isDirectory()) return written(file);
        return /\.tsx?$/.test(entry.name) && !/\.test\.tsx?$/.test(entry.name) ? [[path.relative(SRC, file), readFileSync(file, "utf8")]] : [];
      });
    // The list of the drawings names every drawing, and draws none.
    const naming = written(SRC).filter(([file, holds]) => file !== "lib/art/names.ts" && /"ui-tradeoff(-b)?"/.test(holds));
    expect(naming.map(([file]) => file)).toEqual(["components/ResultList/look.ts"]);
  });

  test("test_the_sentence_of_a_trade_off_runs_beside_its_heading_and_then_under_it", () => {
    // Measured on a phone after the founder's own sentence: with its heading on the first
    // line of the sentence, which was then as high as the drawing, the first result ended
    // 21.5 px under the foot of the first screen.
    expect(atRest(".tradeOff").get("display")).toBe("flow-root");
    expect([atRest(".tradeOffTitle").get("float"), atRest(".tradeOffTitle").get("display")]).toEqual(["inline-start", "flex"]);
    // The sentence is laid out as words are, and not as a box beside the heading.
    expect(atRest(".tradeOffSaid > div").get("display")).toBe("block");
    expect(heavier(weightOf(".tradeOffSaid > div"), weightOf(".sentence"))).toBe(true);
    // Its drawing is drawn at two pixels of the screen to one of its own, on every screen.
    expect(atRest(".tradeOffTitle").get("--px")).toBe("var(--px-ground)");
  });

  test("test_nothing_that_holds_words_has_a_height_of_its_own_so_that_text_can_be_made_larger", () => {
    const sized = RULES.filter((rule) => ["height", "max-height", "block-size"].some((property) => rule.sets.has(property)));
    const floors = RULES.filter((rule) => rule.sets.has("min-height"));

    // What has a height is a mark that holds no word, and what is kept for a screen reader.
    expect([...new Set(sized.map((rule) => rule.selector))].sort()).toEqual(
      [".breakdown .head", ".journeys .head", ".over::before"].sort(),
    );
    // Nothing is given a height at the least either: a button brings its own, from the part
    // that draws it. On a narrow result a button is as high as its words and its edge, and
    // what says so says the smallest a control may be, by its token.
    expect([...new Set(floors.map((rule) => rule.sets.get("min-height")))]).toEqual(["var(--target-min)"]);
    expect(floors.every((rule) => rule.under === "@container (max-width: 30rem)")).toBe(true);
  });

  test("test_a_result_is_laid_out_by_its_own_width_and_no_column_of_it_is_wider_than_what_holds_it", () => {
    // Seen in a browser: in the middle column of a wide screen, with text twice as large, a
    // card was 234 px wide and was laid out as for a desk, and its name ran out of its box.
    expect(atRest(".result").get("container-type")).toBe("inline-size");
    expect(atRest(".working").get("container-type")).toBe("inline-size");
    const narrow = RULES.filter((rule) => /^@container \(max-width:/.test(rule.under ?? "")).map((rule) => rule.selector);
    expect(narrow).toEqual(
      expect.arrayContaining([".card", ".titled", ".name", ".fit", ".borough", ".titled > [data-chosen]", ".waysOn"]),
    );
    // The width of the screen decides only how far apart the results stand.
    const byTheScreen = RULES.filter((rule) => /^@media \((max|min)-width/.test(rule.under ?? "")).map((rule) => rule.selector);
    expect(byTheScreen).toEqual([".list", '.item[data-kind="row"]:has(> article > [hidden]) + .item[data-kind="row"]']);
    // A column of one is never wider than what holds it, so a long word is broken and pushes nothing out.
    const columns = RULES.filter((rule) => rule.under === null && rule.sets.get("display") === "grid" && !rule.sets.has("grid-template-columns"));
    expect(columns.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_narrow_result_stands_close_and_what_is_read_of_it_is_the_size_of_a_small_sentence", () => {
    // Measured on a phone 390 wide, with every part of the page dressed: a card was 418 px
    // high, where the trunk's was 305, and the first result ended 28 px under the foot of
    // the first screen once all that stands over it had given way.
    const narrow = (selector: string) =>
      new Map(
        RULES.filter((rule) => rule.under === "@container (max-width: 30rem)" && rule.selector === selector).flatMap((rule) => [...rule.sets]),
      );

    // Measured since, on the page a shared link opens: what that search holds is said in
    // full, its chips are 18 px higher, and the first result ended 1.5 px under the foot of
    // the first screen. So a narrow result keeps one art pixel under its last line, as it
    // does over its first, where it kept two: it is 2 px lower, and whole on that screen.
    // The room a narrow result keeps at its sides is the second of the spaces. A row keeps
    // three art pixels more, so that what it holds begins where what a card holds begins.
    for (const kind of [".card", ".row"]) {
      expect([kind, narrow(kind).get("padding"), narrow(kind).get("--inside")]).toEqual([kind, "var(--px) var(--inside)", "var(--space-2)"]);
    }
    // The parts of a row stand one space apart. The lines of a card stand directly on its
    // trade-off, which begins with a rule of its own, and a space is kept under the
    // heading and under the trade-off.
    expect([narrow(".row").get("gap"), narrow(".card").get("gap")]).toEqual(["var(--space-1)", "0"]);
    expect([narrow(".card > .top").get("margin-block-end"), narrow(".card > .tradeOff").get("margin-block-end")]).toEqual([
      "var(--space-1)",
      "var(--space-1)",
    ]);
    expect(narrow(".row").get("padding-inline")).toBe("calc(var(--inside) + var(--px) * 3)");
    // A sentence is never set smaller than a small sentence, and by its token, so that it
    // grows with the size a person has set for text.
    expect(narrow(".card > .tradeOff").get("font-size")).toBe("var(--size-small)");
    // Its lines stand a little closer than those of a page of reading, and no closer than
    // the lines of a gauge. Measured on a phone after a sentence of seven things, with the
    // lines as far apart as on a page: the first result ended 4 px over the foot of the
    // first screen, and a word more in its trade-off would have put it under.
    expect(narrow(".card > .tradeOff").get("line-height")).toBe("1.4");
    const sizes = RULES.filter((rule) => rule.sets.has("font-size")).map((rule) => rule.sets.get("font-size"));
    expect([...new Set(sizes)].sort()).toEqual(["var(--size-body)", "var(--size-h3)", "var(--size-small)"]);
  });

  test("test_a_row_says_the_same_of_a_band_whatever_facts_are_in_hand", () => {
    // Seen in a test of the whole page: a row said what its band rests on only once another
    // search had left the fact of the band in hand, so the list changed under a person who
    // had changed nothing.
    const every = areas.flatMap((area) => profile(area.slug).facts);
    const partly = every.filter((fact) => fact.kind === "tag" && fact.slots.known !== fact.slots.parts);
    /** How many of the first results are cards. The rest are rows. */
    const CARDS = 5;
    const textOf = () => cards().map((one) => one.firstElementChild?.textContent ?? "");

    // With every vibe the service gave drawn, so that a band which is not whole is among them.
    const bare = show({ ...first, opened: false, facts: [], withDetails: false, others: "beside" });
    const without = textOf();
    bare.unmount();
    show({ ...first, opened: false, facts: every, others: "beside" });
    const withAll = textOf();

    expect(partly.length).toBeGreaterThan(0);
    // A row reads the same. A card says more, once it has the fact: that a band is not whole.
    expect(withAll.slice(CARDS)).toEqual(without.slice(CARDS));
    expect(withAll.slice(0, CARDS)).not.toEqual(without.slice(0, CARDS));
    const notWhole = (result: HTMLElement) => result.querySelectorAll("[data-short][data-known='some'], [data-part='true']").length;
    expect(cards().slice(0, CARDS).some((card) => notWhole(card) > 0)).toBe(true);
    for (const row of cards().slice(CARDS)) expect(notWhole(row)).toBe(0);
  });

  test("test_no_name_of_a_vibe_a_measure_or_a_place_is_written_into_a_result", () => {
    const written = readdirSync(__dirname)
      .filter((name) => !/\.test\.tsx?$/.test(name))
      .map((name) => readFileSync(path.join(__dirname, name), "utf8"))
      .join("\n");
    const names = [
      ...areas.flatMap((area) => [area.name, area.borough, area.slug]),
      ...meta.data.tags.flatMap((tag) => [tag.label, tag.tag_id, tag.low_end, tag.high_end]),
      ...meta.data.features.flatMap((feature) => [feature.label, feature.short_label, feature.feature_id]),
      ...meta.data.families.map((family) => family.label),
    ].filter((name): name is string => typeof name === "string" && name.length > 3);
    const quoted = (name: string) => new RegExp(`["'\`/-]${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["'\`.]`, "i");

    expect(names.length).toBeGreaterThan(100);
    expect([...new Set(names)].filter((name) => quoted(name).test(written))).toEqual([]);
  });
});

describe("the town of an area, on a result", () => {
  const RULES = rulesOf(readFileSync(path.join(__dirname, "ResultList.module.css"), "utf8"));
  /** A result that is as narrow as a phone is, by its own width. */
  const NARROW = "@container (max-width: 30rem)";
  /** A result with no room for a town beside its name and its fit, by its own width. */
  const NO_ROOM = "@container (max-width: 36rem)";
  /** A result with no room for the larger of the two sizes of a town, which is half as wide again. */
  const NO_ROOM_FOR_THE_LARGER = "@container (width < 39rem)";
  const setBy = (selector: string, under: string | null = null) =>
    new Map(
      RULES.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) =>
        [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]),
      ),
    );
  /** Where every area sits on every vibe, as the service sends it with the list of areas. */
  const { bands } = recordedAnswer("list_areas", "areas").body.data;
  const shown = first.ranking.ranked.slice(0, SHOWN_AT_FIRST);
  const townOf = (result: Element) => result.querySelector("figure") as HTMLElement;
  const drawingOf = (result: Element) => within(townOf(result)).getByRole("img");
  /** What each piece of a drawing is handed: its picture, its frame and where it stands. */
  const piecesOf = (drawing: Element) =>
    [...drawing.children].map((piece) =>
      ["--art", "--w", "--h", "--frames", "--frame", "--x", "--y"]
        .map((name) => (piece as HTMLElement).style.getPropertyValue(name))
        .join(" "),
    );
  /** The town that the part draws of what it is handed, with nothing about it. */
  function alone(marks: readonly Mark[], name: string) {
    const { container, unmount } = render(<Town marks={marks} meta={meta.data} of={name} />);
    const drawing = container.querySelector("[role='img']") as HTMLElement;
    const drawn = {
      pieces: piecesOf(drawing),
      heard: drawing.getAttribute("aria-label"),
      says: container.querySelector("figcaption")?.textContent,
    };
    unmount();
    return drawn;
  }

  test("test_every_result_card_and_row_alike_has_the_town_of_its_area_in_its_heading_after_its_name_and_its_fit", () => {
    show({ ...first, opened: false });

    expect(cards()).toHaveLength(SHOWN_AT_FIRST);
    expect(cards().map((one) => one.closest("li")?.getAttribute("data-kind"))).toEqual([
      ...Array.from({ length: 5 }, () => "card"),
      ...Array.from({ length: 5 }, () => "row"),
    ]);
    cards().forEach((result, at) => {
      const heading = result.querySelector("header") as HTMLElement;
      const name = within(heading).getByRole("heading", { level: 3 });
      const fit = heading.querySelector("p.fit") as HTMLElement;

      // One town to a result, and it stands in the heading.
      expect(result.querySelectorAll("figure")).toHaveLength(1);
      expect(townOf(result).parentElement).toBe(heading);
      // The rank, the name and the fit are read first and heard first: the town comes after them.
      expect(heading.lastElementChild).toBe(townOf(result));
      expect(Boolean(name.compareDocumentPosition(townOf(result)) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
      expect(Boolean(fit.compareDocumentPosition(townOf(result)) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
      // It says whose town it is, to whoever hears the page.
      const heard = drawingOf(result).getAttribute("aria-label") ?? "";
      expect([at, heard.startsWith(`${TOWN.nameOf(nameOf(shown[at]?.area_id ?? ""))}.`)]).toEqual([at, true]);
    });
  });

  test("test_with_nothing_more_in_hand_a_town_is_drawn_from_the_strip_of_its_result_and_what_the_strip_does_not_hold_is_left_blank", () => {
    show({ ...first, opened: false });

    cards().forEach((result, at) => {
      const area = shown[at] as RankedArea;
      const lone = alone(area.strip, nameOf(area.area_id));
      const blank = blankSaid(saidOf(area.strip, meta.data));

      expect([at, piecesOf(drawingOf(result))]).toEqual([at, lone.pieces]);
      expect([at, drawingOf(result).getAttribute("aria-label")]).toEqual([at, lone.heard]);
      // No strip holds all four, so such a town says in sight which part of it is left blank.
      expect([at, blank === null]).toEqual([at, false]);
      expect(within(townOf(result)).getByText(blank ?? "")).toBeInTheDocument();
    });
  });

  test("test_handed_where_every_area_sits_the_town_of_a_result_is_the_town_of_the_page_of_its_area", () => {
    show({ ...first, opened: false, bands });

    cards().forEach((result, at) => {
      const area = shown[at] as RankedArea;
      const page = alone(profile(slugOf(area.area_id)).tags, nameOf(area.area_id));

      expect([at, piecesOf(drawingOf(result))]).toEqual([at, page.pieces]);
      expect([at, drawingOf(result).getAttribute("aria-label")]).toEqual([at, page.heard]);
      expect([at, townOf(result).querySelector("figcaption")?.textContent]).toEqual([at, page.says]);
    });
    // Most of them are whole, and say their line and no more.
    const whole = cards().filter((result) => townOf(result).querySelector("figcaption")?.textContent === TOWN.line);
    expect(whole.length).toBeGreaterThan(SHOWN_AT_FIRST / 2);
  });

  test("test_a_town_is_of_one_size_on_the_first_result_as_on_the_tenth_and_says_nothing_of_a_rank_or_a_fit", () => {
    const sizeOf = (result: Element) => {
      const drawing = drawingOf(result);
      return [
        townOf(result).className,
        drawing.className,
        drawing.dataset.size,
        drawing.style.getPropertyValue("--across"),
        drawing.style.getPropertyValue("--down"),
      ].join(" ");
    };
    const { unmount } = show({ ...first, opened: false, bands });

    expect(new Set(cards().map(sizeOf)).size).toBe(1);
    expect(drawingOf(cards()[0] as HTMLElement).dataset.size).toBe(TOWN_DRAWN === "screen" ? "large" : "small");
    cards().forEach((result, at) => {
      const heard = drawingOf(result).getAttribute("aria-label") ?? "";
      // Nothing of a town is a figure in sight, and what is heard of it holds no rank and no fit.
      expect([at, /\d/.test(townOf(result).textContent ?? "")]).toEqual([at, false]);
      expect([at, heard.includes(`${Math.floor(shown[at]?.score ?? 0)} of 100`)]).toEqual([at, false]);
      expect([at, /\brank/i.test(heard)]).toEqual([at, false]);
    });
    // Nothing of a town is drawn for one result and not the next: no rule of it counts the results.
    const counting = RULES.filter((rule) => /\.towns?\b/.test(rule.selector) && /:(nth|last)-|-of-type/.test(rule.selector));
    expect(counting.map((rule) => rule.selector)).toEqual([]);
    unmount();

    // The larger of the two sizes a town was built at is the same for every result too.
    show({ ...first, opened: false, bands, townDrawn: "screen" });
    expect(new Set(cards().map(sizeOf)).size).toBe(1);
    expect(drawingOf(cards()[0] as HTMLElement).dataset.size).toBe("large");
  });

  test("test_no_result_says_what_a_town_is_and_no_town_of_a_result_says_it_of_itself", () => {
    // The founder, who had walked the website twice: "remove the 'each little town'
    // disclaimer on the ranking cards". It stood under the heading of the first result, two
    // lines of it, between the name of the area and where the area sits.
    show({ ...first, opened: false, bands });
    const [list] = lists() as [HTMLElement];

    expect([LINE_STANDS, OVER_THE_LIST]).toEqual(["none", "nothing"]);
    expect(LINE_STANDS_AT).toEqual(["none", "once", "each"]);
    // The list says it nowhere: in no heading, and over no part of itself.
    expect(screen.queryByText(TOWNS.line)).toBeNull();
    expect(list.previousElementSibling).toBeNull();
    for (const result of cards()) {
      const heading = result.querySelector("header") as HTMLElement;
      expect([...heading.children].map((part) => part.tagName)).toEqual(["P", "DIV", "FIGURE"]);
      expect(heading.querySelector(".towns")).toBeNull();
    }
    // Each part of the list says that the line stands nowhere, and there the line of each
    // town is not drawn either: what is not drawn is heard by nobody.
    expect(lists().map((one) => one.dataset.line)).toEqual(["none", "none"]);
    expect([...setBy('.list:not([data-line="each"]) .town > figcaption > :first-child')]).toEqual([["display", "none"]]);
    // What is not drawn is the line and nothing else: the line is the first thing a town says.
    for (const result of cards()) {
      expect(townOf(result).querySelector(":scope > figcaption > :first-child")?.textContent).toBe(TOWN.line);
    }
    // A town that says its line and no more has nothing left to say, and takes no room to say it in.
    expect([...setBy('.list:not([data-line="each"]) .town > figcaption:not(:has(> :not(:first-child)))')]).toEqual([
      ["display", "none"],
    ]);
    // Nor is the line in short drawn, which a town holds for the head of the page of an area:
    // the heading of a result says nothing that the sheet of a town knows it by.
    for (const result of cards()) expect(result.querySelector("header")?.hasAttribute("data-town")).toBe(false);
  });

  test("test_one_line_of_the_look_has_the_line_stand_once_where_the_first_town_is_and_no_town_says_it_again", () => {
    // As it was before the founder asked for it to go. Measured then at 1440 by 900 after a
    // plain search: over the list, in one slip with what says that areas can be compared,
    // the line was four lines of 92 px and the first result began at 899 of 900. So it
    // stood where the first town is, and took nothing from the top of the answer.
    show({ ...first, opened: false, bands, lineStands: "once" });
    const [list, rest] = lists() as [HTMLElement, HTMLElement];
    const lines = screen.getAllByText(TOWNS.line);
    const [line] = lines as [HTMLElement];
    const heading = (cards()[0] as HTMLElement).querySelector("header") as HTMLElement;

    // Once, however many towns are drawn, and with the first of them: in the heading of the
    // first result, directly before its town. It is a paragraph of its own and no part of the town.
    expect(lines).toHaveLength(1);
    expect(line.tagName).toBe("P");
    expect(line.parentElement).toBe(heading);
    expect(line.nextElementSibling).toBe(townOf(cards()[0] as HTMLElement));
    expect(townOf(cards()[0] as HTMLElement).contains(line)).toBe(false);
    expect(rest.contains(line)).toBe(false);
    // Nothing stands over the list for it: the first result is the first thing of its part.
    expect(list.previousElementSibling).toBeNull();
    // It is in sight, and is heard: nothing keeps it for a screen reader alone, or from one.
    expect(line.closest(".visually-hidden, [hidden], [aria-hidden='true']")).toBeNull();
    expect(line).toBeVisible();
    // It is laid under the heading from edge to edge, as what a town says of itself is, and
    // what the town of that result says of itself follows it on the next line.
    const under = setBy(".heading > .towns");
    expect([under.get("grid-column"), under.get("grid-row")]).toEqual(["1 / -1", "2"]);
    expect([under.get("font-size"), under.get("line-height")]).toEqual(["var(--size-small)", "1.3"]);
    expect([...setBy(".heading:has(> .towns) > .town > figcaption")]).toEqual([["grid-row", "3"]]);
    expect(heavier(weightOf(".heading:has(> .towns) > .town > figcaption"), weightOf(".heading > .town > figcaption"))).toBe(true);
    // Where the way to compare has a line of its own under the name, the line follows it.
    const BETWEEN = "@container (width > 36rem) and (width < 46rem)";
    expect(setBy(".list[data-narrow] .titled > [data-chosen]", BETWEEN).get("grid-row")).toBe("3");
    expect(setBy(".list[data-narrow] .heading > .towns", BETWEEN).get("grid-row")).toBe("4");
    expect(setBy(".list[data-narrow] .heading:has(> .towns) > .town > figcaption", BETWEEN).get("grid-row")).toBe("5");
    // Each part of the list says where the line stands, and there the line of each town is not drawn.
    expect(lists().map((one) => one.dataset.line)).toEqual(["once", "once"]);
    for (const result of cards()) {
      expect(townOf(result).className.split(" ")).toContain("town");
      expect(townOf(result).querySelector(":scope > figcaption > :first-child")?.textContent).toBe(TOWN.line);
    }
  });

  test("test_what_a_town_leaves_blank_is_said_with_the_town_whether_or_not_its_line_is", () => {
    // Drawn from its strip alone, every town has a part that is left blank.
    show({ ...first, opened: false });

    for (const result of cards()) {
      const [line, blank, ...more] = [...(townOf(result).querySelector("figcaption")?.children ?? [])];
      expect(line?.textContent).toBe(TOWN.line);
      expect(blank?.textContent?.startsWith(TOWN.leftBlank([]).replace(/[:.\s]+$/, ""))).toBe(true);
      expect(more).toEqual([]);
    }
    // It is in sight: what is not known of an area is said to be not known.
    for (const result of cards()) {
      const blank = townOf(result).querySelector(":scope > figcaption > :nth-child(2)") as HTMLElement;
      expect(blank.closest("[hidden], [aria-hidden='true'], .visually-hidden")).toBeNull();
    }
    // No rule takes anything a town says away but its line, and what holds its line alone.
    const takenAway = RULES.filter((rule) => /figcaption/.test(rule.selector) && rule.sets.get("display") === "none");
    expect(takenAway.map((rule) => rule.selector)).toEqual([
      '.list:not([data-line="each"]) .town > figcaption > :first-child',
      '.list:not([data-line="each"]) .town > figcaption:not(:has(> :not(:first-child)))',
    ]);
  });

  test("test_the_line_may_stand_under_each_town_instead_and_then_the_list_says_it_nowhere", () => {
    const { unmount } = show({ ...first, opened: false, bands, lineStands: "each" });

    expect(screen.queryByText(TOWNS.line)).toBeNull();
    expect(lists().map((one) => one.dataset.line)).toEqual(["each", "each"]);
    expect((lists()[0] as HTMLElement).previousElementSibling).toBeNull();
    for (const result of cards()) expect(within(townOf(result)).getByText(TOWN.line)).toBeVisible();
    unmount();

    // Where the look has a slip stand over the list, it then says that areas can be compared, and no more.
    show({ ...first, opened: false, bands, lineStands: "each", over: "slip" });
    expect(screen.queryByText(TOWNS.line)).toBeNull();
    expect((lists()[0] as HTMLElement).previousElementSibling?.textContent).toBe(COMPARE.invite);
  });

  test("test_a_slip_over_the_list_says_that_areas_can_be_compared_and_nothing_of_a_town", () => {
    expect(OVER_THE_LIST_MAY_STAND).toEqual(["slip", "nothing"]);
    show({ ...first, opened: false, bands, over: "slip" });
    const [list] = lists() as [HTMLElement];
    const slip = list.previousElementSibling as HTMLElement;

    expect(screen.queryByText(TOWNS.line)).toBeNull();
    expect([slip.tagName, slip.className]).toEqual(["P", "above"]);
    expect(slip.textContent?.trim()).toBe(COMPARE.invite);
    expect(slip.querySelector(".towns")).toBeNull();
  });

  test("test_two_lines_of_the_look_put_what_was_said_once_of_a_list_back_over_it_in_one_slip", () => {
    // As it was first built: that areas can be compared, and then what a town is, in one slip
    // over the list. The first result then holds no line, and stands lower by the slip.
    show({ ...first, opened: false, bands, over: "slip", lineStands: "once" });
    const [list, rest] = lists() as [HTMLElement, HTMLElement];
    const lines = screen.getAllByText(TOWNS.line);
    const [line] = lines as [HTMLElement];

    expect(lines).toHaveLength(1);
    expect((list.parentElement as HTMLElement).dataset.over).toBe("slip");
    // It is the last thing said in the slip that stands directly over the list.
    expect(line.parentElement?.tagName).toBe("P");
    expect(line.parentElement?.className).toBe("above");
    expect(line.parentElement?.lastElementChild).toBe(line);
    expect(line.parentElement?.firstElementChild?.textContent).toBe(COMPARE.invite);
    expect(line.parentElement?.nextElementSibling).toBe(list);
    expect(Boolean(line.compareDocumentPosition(rest) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    expect(line).toBeVisible();
    // No heading says it a second time.
    for (const result of cards()) expect((result.querySelector("header") as HTMLElement).querySelectorAll("p")).toHaveLength(3);
  });

  test("test_no_line_stands_where_no_town_does", () => {
    const { unmount } = show({ ...first, waitingForFirst: true, opened: false });

    expect(screen.queryByText(TOWNS.line)).toBeNull();
    expect(document.querySelectorAll("figure")).toHaveLength(0);
    unmount();
    // A list that is worked out again stays, and its towns with it.
    const worked = show({ ...first, opened: false, busy: true, bands });
    expect(screen.queryByText(TOWNS.line)).toBeNull();
    expect(document.querySelectorAll("figure")).toHaveLength(SHOWN_AT_FIRST);
    worked.unmount();
    // So does their line, where the look has one stand.
    show({ ...first, waitingForFirst: true, opened: false, lineStands: "once" }).unmount();
    expect(screen.queryByText(TOWNS.line)).toBeNull();
    show({ ...first, opened: false, busy: true, bands, lineStands: "once" });
    expect(screen.getAllByText(TOWNS.line)).toHaveLength(1);
  });

  test("test_a_result_with_no_room_for_a_town_has_none_and_its_list_no_line_so_that_the_first_result_is_whole_on_the_first_screen_of_a_phone", () => {
    // Measured on a phone, 390 by 844, after a plain search: the first result stands from 454
    // to 828, with 16 px to spare. A town is 64 px high and the heading of a result 50. With
    // a town at the far end of the heading the first result was 28 px higher, and with the
    // line over the list it stood from 519 to 921. And under 36rem of a result a name had
    // less room beside a town than it has on a phone, and was seen to break inside a word.
    // The line stands on no result now. Where the look puts it back, it goes where the towns go.
    show({ ...first, opened: false, bands, lineStands: "once" });
    const holds = (lists()[0] as HTMLElement).parentElement as HTMLElement;

    expect(ON_A_NARROW_RESULT).toBe("none");
    expect(lists().map((one) => one.dataset.narrow)).toEqual(["none", "none"]);
    expect([holds.className, holds.dataset.narrow]).toEqual(["listed", "none"]);
    // What says what a town is stands in what holds the list, wherever the look has it stand.
    expect(holds).toContainElement(screen.getByText(TOWNS.line));
    // A town goes by the width of its result, and the line by the width of what holds it
    // and the list. The two are as wide as each other, so the line goes where the towns go.
    expect(setBy(".result").get("container-type")).toBe("inline-size");
    expect(setBy(".listed").get("container-type")).toBe("inline-size");
    expect([...setBy('.list[data-narrow="none"] .heading > .town', NO_ROOM)]).toEqual([["display", "none"]]);
    expect([...setBy('.listed[data-narrow="none"] .towns', NO_ROOM)]).toEqual([["display", "none"]]);
    // That rule is of the line wherever it stands in what holds the list: under the heading
    // of the first result, or in a slip over the list. It weighs more than what lays the
    // line out under a heading, which says nothing of whether the line is drawn.
    expect(heavier(weightOf('.listed[data-narrow="none"] .towns'), weightOf(".heading > .towns"))).toBe(true);
    expect(RULES.filter((rule) => /\.heading\b.*> \.towns$/.test(rule.selector) && rule.sets.has("display"))).toEqual([]);
    // Nor is the slip that holds the line, which would stand empty over the list.
    expect([...setBy('.listed[data-narrow="none"] > .above', NO_ROOM)]).toEqual([["display", "none"]]);
    // The heading is then as it was before a town stood in one: the pennant, and the name with the fit.
    expect([...setBy('.list[data-narrow="none"] .heading', NO_ROOM)]).toEqual([
      ["grid-template-columns", "auto minmax(0, 1fr)"],
    ]);
    // Every result of a phone is one: what is narrow has no room.
    expect(Number(/(\d+)rem/.exec(NO_ROOM)?.[1])).toBeGreaterThan(Number(/(\d+)rem/.exec(NARROW)?.[1]));
    // Neither goes by the width of the screen: a result may be narrow on a wide one.
    const byTheScreen = RULES.filter((rule) => /^@media \((max|min)-width/.test(rule.under ?? ""));
    expect(byTheScreen.filter((rule) => /\.(towns?|listed|heading)\b/.test(rule.selector))).toEqual([]);
    // No other rule takes a town or the line away, but for the larger town, which asks for more room.
    const takenAway = RULES.filter((rule) => /\.towns?$/.test(rule.selector) && rule.sets.get("display") === "none");
    expect(takenAway.map((rule) => [rule.under, rule.selector])).toEqual([
      [NO_ROOM, '.list[data-narrow="none"] .heading > .town'],
      [NO_ROOM, '.listed[data-narrow="none"] .towns'],
      [NO_ROOM_FOR_THE_LARGER, '.list[data-narrow="none"][data-town="screen"] .heading > .town'],
      [NO_ROOM_FOR_THE_LARGER, '.listed[data-narrow="none"][data-town="screen"] .towns'],
    ]);
  });

  test("test_the_larger_town_asks_for_a_wider_result_so_that_the_name_keeps_its_room_beside_it", () => {
    // Seen in a browser: at 168 by 96, on a result 586 px wide, the name had 134 px, where
    // it has 172 on a phone, and a name of one word was broken in two.
    const { unmount } = show({ ...first, opened: false, bands });
    const holds = () => (lists()[0] as HTMLElement).parentElement as HTMLElement;

    expect(TOWN_DRAWN).toBe("ground");
    expect([...lists(), holds()].map((one) => one.dataset.town)).toEqual(["ground", "ground", "ground"]);
    unmount();
    show({ ...first, opened: false, bands, townDrawn: "screen" });
    expect([...lists(), holds()].map((one) => one.dataset.town)).toEqual(["screen", "screen", "screen"]);

    const larger = (selector: string) => setBy(selector, NO_ROOM_FOR_THE_LARGER);
    expect([...larger('.list[data-narrow="none"][data-town="screen"] .heading > .town')]).toEqual([["display", "none"]]);
    expect([...larger('.listed[data-narrow="none"][data-town="screen"] .towns')]).toEqual([["display", "none"]]);
    expect([...larger('.list[data-narrow="none"][data-town="screen"] .heading')]).toEqual([
      ["grid-template-columns", "auto minmax(0, 1fr)"],
    ]);
    // A result of the width a desk gives it, 39rem, has the room: the rule holds under that width and not at it.
    expect(/width < 39rem/.test(NO_ROOM_FOR_THE_LARGER)).toBe(true);
  });

  test("test_the_other_way_draws_a_town_on_a_result_with_no_room_beside_the_name_with_a_line_each_for_the_name_the_fit_and_what_stands_beside_the_name", () => {
    show({ ...first, opened: false, bands, onANarrowResult: "beside" });

    expect(lists().map((one) => one.dataset.narrow)).toEqual(["beside", "beside"]);
    expect(((lists()[0] as HTMLElement).parentElement as HTMLElement).dataset.narrow).toBe("beside");
    // The heading lays out what the name stood with: the pennant and the name, then the fit, then what stands beside the name.
    const of = (part: string) => setBy(`.list[data-narrow="beside"] ${part}`, NO_ROOM);
    expect([...of(".titled")]).toEqual([["display", "contents"]]);
    expect([of(".name").get("grid-row"), of(".fit").get("grid-row"), of(".borough").get("grid-row")]).toEqual(["1", "2", "3"]);
    // The fit is one line there, the word before the figure, as it is on a narrow result.
    expect([of(".fit").get("display"), of(".fit").get("text-align"), of(".fitFigure").get("font-size")]).toEqual([
      "flex",
      "start",
      "var(--size-h3)",
    ]);
    // The town stands beside all three. The way to compare has the line after them, at the
    // far end, and what the town says the line after that.
    expect(of('.heading > .town > [role="img"]').get("grid-row")).toBe("1 / 4");
    expect([of(".titled > [data-chosen]").get("grid-row"), of(".titled > [data-chosen]").get("justify-self")]).toEqual(["4", "end"]);
    expect(of(".heading > .town > figcaption").get("grid-row")).toBe("5");
    // In the first result what a town is has that line, and what the town says of itself the next.
    expect(of(".heading > .towns").get("grid-row")).toBe("5");
    expect(of(".heading:has(> .towns) > .town > figcaption").get("grid-row")).toBe("6");
    // Each of these weighs more than the rule it takes the place of, wherever that rule stands.
    for (const part of [".titled", ".name", ".fit", ".fitFigure", ".borough"]) {
      expect([part, heavier(weightOf(`.list[data-narrow="beside"] ${part}`), weightOf(part))]).toEqual([part, true]);
    }
    // A result with room for a town is laid out as it is whichever way is chosen. Seen in a
    // browser: the other way held under 39rem, and the line of the way to compare from 36rem
    // for the first way alone, so every result of a desk, which is 39.6rem, had neither, and
    // its name was left 49 px: "Bra/cke/nhyt/he". So no rule of a result between 36rem and
    // 46rem names a way, and no rule of the other way holds of a result that has the room.
    const BETWEEN = "@container (width > 36rem) and (width < 46rem)";
    expect(RULES.filter((rule) => rule.under === BETWEEN && /data-narrow="/.test(rule.selector))).toEqual([]);
    expect(RULES.filter((rule) => /data-narrow="beside"/.test(rule.selector) && rule.under !== NO_ROOM)).toEqual([]);
    // And no rule takes a town away there.
    const takenAway = RULES.filter((rule) => /\.towns?$/.test(rule.selector) && rule.sets.get("display") === "none");
    expect(takenAway.filter((rule) => !/data-narrow="none"/.test(rule.selector))).toEqual([]);
  });

  test("test_under_46rem_of_a_result_the_way_to_compare_has_a_line_after_the_name_at_every_width", () => {
    // Seen in a browser, as the website was served: in a window from 960 to 1120 px wide a
    // result is from 30rem to 36rem, and the way to compare stood beside its name and its
    // fit, where it takes some 175 px. A name was left 26 px, and was broken inside the
    // word six times: "Br/ac/ke/nh/yt/he". Each rule of the sheet was held by a test, and
    // no test asked what a result of a given width is laid out by. It is held whichever
    // way the look has a narrow result drawn: the other way was broken so from 39rem.
    /** The line the break of a row that wraps is laid on, where the heading is such a row. */
    const breakAt = (rem: number) => {
      const breaks = RULES.filter((rule) => rule.selector === ".titled::after" && holdsAt(rule.under, rem) && rule.sets.get("flex") === "0 0 100%");
      return Number(breaks[breaks.length - 1]?.sets.get("order"));
    };

    for (const way of ["none", "beside"] as const) {
      const { unmount } = show({ ...first, opened: false, bands, onANarrowResult: way });
      const name = within(cards()[FARROWMERE] as HTMLElement).getByRole("heading", { level: 3 });
      const holds = name.parentElement as HTMLElement;
      const toCompare = holds.querySelector("[data-chosen]") as HTMLElement;

      for (let rem = 18; rem <= 60; rem += 0.5) {
        const [ofWhatHolds, ofTheName, ofTheWay] = [holds, name, toCompare].map((part) => setAt(RULES, part, rem));
        const apart =
          ofWhatHolds?.get("display") === "flex"
            ? // A row that wraps: the name before the break of the row, and the way to compare after it.
              Number(ofTheName?.get("order")) < breakAt(rem) && Number(ofTheWay?.get("order")) > breakAt(rem)
            : // A grid: the way to compare on a line after the name and what stands beside it, from edge to edge.
              rowOf(ofTheWay ?? new Map()) > rowOf(ofTheName ?? new Map()) + 1 && ofTheWay?.get("grid-column") === "1 / -1";
        expect([way, rem, apart]).toEqual([way, rem, rem < 46]);
      }
      unmount();
    }
    // No rule lays a heading out by the width of the screen, or by anything but the width of its result.
    const others = RULES.filter((rule) => rule.under !== null && !rule.under.startsWith("@container"));
    expect(others.filter((rule) => /\.(heading|titled|name|fit|borough)\b|\[data-chosen\]/.test(rule.selector))).toEqual([]);
  });

  test("test_the_town_stands_at_the_far_end_of_the_heading_beside_the_name_and_the_fit_and_what_it_says_under_them", () => {
    const heading = setBy(".heading");

    expect([heading.get("display"), heading.get("grid-template-columns")]).toEqual(["grid", "auto minmax(0, 1fr) auto"]);
    // The town is no box of its own there: its drawing and what it says are each laid out by the heading.
    expect([...setBy(".heading > .town")]).toEqual([["display", "contents"]]);
    // Which sheet is read last is not the website's to decide, so a rule of a result that
    // lays the town out weighs more than the town's own.
    expect(heavier(weightOf(".heading > .town"), weightOf(".town"))).toBe(true);
    const drawing = setBy('.heading > .town > [role="img"]');
    expect([drawing.get("grid-column"), drawing.get("grid-row")]).toEqual(["3", "1"]);
    const says = setBy(".heading > .town > figcaption");
    expect([says.get("grid-column"), says.get("grid-row")]).toEqual(["1 / -1", "2"]);
    // A drawing has its own size. No rule of a result gives it another, stretches it, moves it or dims it.
    const ofATown = RULES.filter((rule) => /\.town\b/.test(rule.selector)).flatMap((rule) => [...rule.sets.keys()]);
    expect(
      ofATown.filter((property) => /^(width|height|inline-size|block-size|min-|max-|transform|scale|zoom|opacity|filter|animation|transition)/.test(property)),
    ).toEqual([]);
  });

  test("test_what_holds_the_line_and_the_list_has_no_ground_of_its_own_and_the_slip_brings_the_cream_it_is_read_on", () => {
    const holds = setBy(".listed");

    // The page lays a slip under a part that stands loose. A list stands on the grass, and so does what holds one.
    expect([holds.get("padding"), holds.get("border"), holds.get("background")]).toEqual(["0", "0", "none"]);
    expect([holds.get("display"), holds.get("grid-template-columns")]).toEqual(["grid", "minmax(0, 1fr)"]);
    // Nothing is read on the grass: what is said over the list, and under its first result,
    // stands on cream, within an edge of ink that is whole.
    for (const slip of [".above", ".underFirst"]) {
      const said = setBy(slip);
      expect([slip, said.get("background"), said.get("border")]).toEqual([slip, "var(--page)", "var(--edge) solid var(--border)"]);
      expect([slip, said.get("font-size")]).toEqual([slip, "var(--size-small)"]);
    }
    // The line of the towns is the quieter of what the slip says, and is ink all the same.
    expect([...setBy(".towns")]).toEqual([["color", "var(--muted)"]]);
  });

  test("test_the_edge_of_the_line_and_of_every_result_ends_where_the_edge_of_ink_of_a_card_ends", () => {
    // Measured in a browser, at 1440 by 900: the edge of ink of a card ended at 1,026, and
    // the line over the list, results six and on and what stands under the list at 1,032.
    // A card is a box, which keeps the room of its shadow inside itself: two art pixels at
    // its far side. What is in a plain edge keeps as much there, so that every edge of the
    // list ends on one line.
    for (const slip of [".above", ".underFirst"]) expect(setBy(slip).get("margin-inline-end")).toBe("calc(var(--px) * 2)");
    // A row and what stands under the list are plain frames of the kit, which keeps the
    // room itself where a plain frame stands on the grass. No rule here takes it back.
    const kit = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Frame", "Frame.module.css"), "utf8"));
    const kept = kit.filter((rule) => rule.sets.has("margin-inline-end") && rule.under === null);
    expect(kept.map((rule) => [rule.selector, rule.sets.get("margin-inline-end")])).toEqual([
      [".plain:not(:where(.frame *))", "calc(var(--px) * 2)"],
    ]);
    const takesItBack = RULES.filter(
      (rule) =>
        /\.(row|under)\b/.test(subjectOf(rule.selector)) &&
        [...rule.sets.keys()].some((property) => /^margin(-inline(-end)?|-right)?$/.test(property)),
    );
    expect(takesItBack.map((rule) => rule.selector)).toEqual([]);
    // A row is a plain frame, and a card a box. Neither stands in a frame, so the kit's rule holds of a row.
    show({ ...first, opened: false, bands });
    const frames = cards().map((result) => result.querySelector(":scope > [data-kind]") as HTMLElement);
    expect(frames.map((frame) => frame.getAttribute("data-kind"))).toEqual([
      ...Array.from({ length: 5 }, () => "box"),
      ...Array.from({ length: 5 }, () => "plain"),
    ]);
    expect(frames.map((frame) => frame.matches(".plain:not(:where(.frame *))"))).toEqual([
      ...Array.from({ length: 5 }, () => false),
      ...Array.from({ length: 5 }, () => true),
    ]);
  });

  test("test_a_town_can_be_neither_pressed_nor_given_the_focus_and_adds_no_control_to_a_result", () => {
    const controls = "a, button, input, select, textarea, [tabindex]";
    const { unmount } = show({ ...first, opened: false, withDetails: false, explanations: [], facts: [] });
    const without = cards().map((result) => result.querySelectorAll(controls).length - townOf(result).querySelectorAll(controls).length);
    unmount();
    show({ ...first, opened: false, withDetails: false, explanations: [], facts: [], bands });

    expect(cards().map((result) => townOf(result).querySelectorAll(controls).length)).toEqual(cards().map(() => 0));
    expect(cards().map((result) => result.querySelectorAll(controls).length)).toEqual(without);
  });

  test("test_the_line_the_look_may_put_back_says_that_a_town_is_a_drawing_made_of_vibes_and_no_picture_of_the_place", () => {
    // As the founder asked for it to read: in whole sentences, which say what follows from
    // what. It stands on no result, and is kept for the one line of the look that puts it back.
    expect(TOWNS.line).toBe(
      "Each little town is a drawing based on four of the area's vibes. This means it shows the character of the area, and is not a picture of what the place looks like.",
    );
    // It says both things the line of one town says: what a town is drawn from, and that it is no picture.
    expect(TOWN.line).toMatch(/vibes/);
    expect(TOWN.line).toMatch(/[Nn]ot a picture/);
    expect(TOWNS.line).toMatch(/four of the area's vibes/);
    expect(TOWNS.line).toMatch(/not a picture/);
    // It holds no figure: a town says nothing that is measured.
    expect(/\d/.test(TOWNS.line)).toBe(false);
  });

  test("test_a_list_of_results_with_its_towns_has_no_accessibility_fault", async () => {
    const { container } = show({ ...first, opened: false, bands });

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("what says that areas can be compared", () => {
  const RULES = rulesOf(readFileSync(path.join(__dirname, "ResultList.module.css"), "utf8"));
  const NO_ROOM = "@container (max-width: 36rem)";
  const setBy = (selector: string, under: string | null = null) =>
    new Map(RULES.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));
  const said = () => screen.getAllByText(COMPARE.invite);
  const over = () => said().find((one) => one.closest("[data-stands='over']") !== null) as HTMLElement;
  const under = () => said().find((one) => one.closest("[data-stands='under']") !== null) as HTMLElement;

  test("test_the_list_says_it_before_anybody_has_chosen_anything_with_the_drawing_of_two_towns_and_not_over_itself", () => {
    // The founder: "Compare function is great, make this more of a highlighted feature". A
    // person who never pressed the third button of a result never learned that areas can be
    // set side by side. Measured at 1440 by 900: said over the list, with what a town is,
    // it stood the first result 100 px lower, and out of sight. So the page that draws the
    // list says it beside what refines the search, and the list says it under its first
    // result, which is drawn where a result is narrow and wherever the page asks.
    show({ ...first, opened: false });
    const [list] = lists() as [HTMLElement];

    expect([INVITE_STANDS, OVER_THE_LIST]).toEqual(["over", "nothing"]);
    expect(COMPARE.invite).toBe('Choose two to four areas with "Add to compare", and Burro will put them side by side.');
    // Nothing stands over the first part of the list: the first result is the first thing of it.
    expect(list.previousElementSibling).toBeNull();
    expect((list.parentElement as HTMLElement).dataset.over).toBe("nothing");
    expect(said()).toHaveLength(1);
    expect(under().closest("p")?.previousElementSibling).toBe(list);
    // It is heard wherever it is drawn: nothing keeps it for a screen reader alone, or from one.
    expect(under().closest(".visually-hidden, [hidden], [aria-hidden='true']")).toBeNull();
    // Before it stands the drawing of two towns, which is dress and says nothing.
    const drawing = under().previousElementSibling as HTMLElement;
    expect(drawing).toHaveAttribute("aria-hidden", "true");
    expect([...drawing.children].map((one) => (one as HTMLElement).style.getPropertyValue("--art"))).toEqual(
      TWO_TOWNS.map((name) => `url("/art/${name}.png")`),
    );
    expect(drawing.textContent).toBe("");
    expect(drawing.querySelectorAll("a, button, [tabindex]")).toHaveLength(0);
  });

  test("test_where_the_look_has_a_slip_stand_over_the_list_it_is_said_there_directly_over_the_first_result", () => {
    show({ ...first, opened: false, over: "slip" });
    const [list] = lists() as [HTMLElement];

    // Over the first part of the list, in the slip that stands directly over the first result.
    expect(over().closest("p")?.nextElementSibling).toBe(list);
    expect(Boolean(over().compareDocumentPosition(cards()[0] as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    expect(over().closest(".visually-hidden, [hidden], [aria-hidden='true']")).toBeNull();
    // It is on the page twice then, and the style sheet draws the one that has room.
    expect(said()).toHaveLength(2);
  });

  test("test_where_a_result_is_narrow_it_stands_under_the_first_result_so_that_nothing_is_put_between_the_box_and_the_answer", () => {
    // On a phone the first result is whole on the first screen, with 16 px to spare.
    show({ ...first, opened: false });
    const [list, rest] = lists() as [HTMLElement, HTMLElement];

    // The list says it once, and the style sheet draws it where a result is narrow. Where a
    // result is wide the page that draws the list says it, beside what refines the search,
    // and what the list says is not drawn: what is not drawn is not read out.
    expect(said()).toHaveLength(1);
    expect(under().closest("p")?.previousElementSibling).toBe(list);
    expect(Boolean(under().compareDocumentPosition(rest) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    // Where a result has room, the one under the first result is not drawn.
    expect([...setBy('.listed[data-invite="over"] > .underFirst')]).toEqual([["display", "none"]]);
    // Where it has none, the one over the list is not drawn and the one under the first result is.
    expect([...setBy('.listed > .above > [data-stands="over"]', NO_ROOM)]).toEqual([["display", "none"]]);
    expect([...setBy('.listed[data-invite="over"] > .underFirst', NO_ROOM)]).toEqual([["display", "flow-root"]]);
    // The rule that draws it there comes after the rule that does not, and weighs as much: so it holds.
    const order = RULES.map((rule) => `${rule.under ?? ""} ${rule.selector}`);
    expect(order.indexOf(`${NO_ROOM} .listed[data-invite="over"] > .underFirst`)).toBeGreaterThan(
      order.indexOf(' .listed[data-invite="over"] > .underFirst'),
    );
    // It goes by the width of a result, as a town does, and never by the width of the screen.
    expect(setBy(".listed").get("container-type")).toBe("inline-size");
    const byTheScreen = RULES.filter((rule) => /^@media \((max|min)-width/.test(rule.under ?? ""));
    expect(byTheScreen.filter((rule) => /above|underFirst|data-stands/.test(rule.selector))).toEqual([]);
  });

  test("test_it_may_stand_under_the_first_result_on_every_screen_or_nowhere_by_one_line", () => {
    const slip = show({ ...first, opened: false, inviteStands: "under", over: "slip" });

    // A slip over the list then has nothing to say, and is not drawn.
    expect(said()).toHaveLength(1);
    expect((lists()[0] as HTMLElement).previousElementSibling).toBeNull();
    slip.unmount();

    // Where the look has the line of the towns stand once, the slip says that, and no more.
    const withTheLine = show({ ...first, opened: false, inviteStands: "under", over: "slip", lineStands: "once" });
    expect(said()).toHaveLength(1);
    expect(screen.getByText(TOWNS.line).parentElement?.textContent?.trim()).toBe(TOWNS.line);
    withTheLine.unmount();

    // A page asks it of the list where what stands over the answer must give way: it is
    // then drawn under the first result however wide a result is.
    const { unmount } = show({ ...first, opened: false, inviteStands: "under" });
    expect(said()).toHaveLength(1);
    expect(under().closest("p")?.previousElementSibling).toBe(lists()[0]);
    expect((lists()[0] as HTMLElement).previousElementSibling).toBeNull();
    // And no rule takes it away where a result is wide.
    expect(under().closest("div")?.getAttribute("data-invite")).toBe("under");
    expect(RULES.filter((rule) => /underFirst/.test(rule.selector) && rule.sets.get("display") === "none").map((rule) => rule.selector)).toEqual([
      '.listed[data-invite="over"] > .underFirst',
    ]);
    unmount();

    show({ ...first, opened: false, inviteStands: "none" });
    expect(screen.queryByText(COMPARE.invite)).toBeNull();
    // Nothing is said in its place.
    expect(screen.queryByText(TOWNS.line)).toBeNull();
    expect((lists()[0] as HTMLElement).parentElement?.querySelectorAll(":scope > p")).toHaveLength(0);
  });

  test("test_it_says_the_same_whatever_the_list_holds_and_whatever_is_chosen_and_nothing_of_any_area", async () => {
    const user = userEvent.setup({ delay: null });
    render(<SessionProvider>{listOf({ ...first, opened: false }).element}</SessionProvider>);
    const before = said().map((one) => one.closest("p")?.textContent);

    await user.click(card(0).getByRole("button", { name: COMPARE.addNamed(nameOf(first.ranking.ranked[0]?.area_id ?? "")) }));

    // It does not go when an area is chosen: what is over the list does not move under a person.
    expect(said().map((one) => one.closest("p")?.textContent)).toEqual(before);
    // It names no area and holds no figure of one.
    for (const area of areas) expect(COMPARE.invite.includes(area.name)).toBe(false);
    expect(/\d/.test(COMPARE.invite)).toBe(false);
  });

  test("test_no_list_no_invitation", () => {
    const { unmount } = show({ ...first, waitingForFirst: true, opened: false });

    expect(screen.queryByText(COMPARE.invite)).toBeNull();
    unmount();
    // A list that is worked out again stays, and what is said of it with it.
    show({ ...first, opened: false, busy: true });
    expect(said()).toHaveLength(1);
    cleanup();
    show({ ...first, opened: false, busy: true, over: "slip" });
    expect(said()).toHaveLength(2);
  });
});

describe("what the list hands the bar of areas to compare", () => {
  const { bands } = recordedAnswer("list_areas", "areas").body.data;
  /** What each piece of a drawing is handed: its picture, its frame and where it stands. */
  const piecesOf = (drawing: Element) =>
    [...drawing.children].map((piece) =>
      ["--art", "--w", "--h", "--frames", "--frame", "--x", "--y"]
        .map((name) => (piece as HTMLElement).style.getPropertyValue(name))
        .join(" "),
    );
  const bar = () => screen.getByRole("region", { name: TRAY.title });

  function withTheBar(shown: Shown) {
    const user = userEvent.setup({ delay: null });
    render(
      <SessionProvider>
        {listOf({ ...shown, opened: false }).element}
        <CompareTray />
      </SessionProvider>,
    );
    return user;
  }

  test.each([
    ["where every area sits", bands],
    ["the strip of its result", undefined],
  ])("test_the_town_of_an_area_in_the_bar_is_the_town_beside_its_result_drawn_from_%s", async (_, held) => {
    const user = withTheBar({ ...first, bands: held });

    for (const at of [0, 5]) {
      await user.click(card(at).getByRole("button", { name: COMPARE.addNamed(nameOf(first.ranking.ranked[at]?.area_id ?? "")) }));
    }

    const inTheBar = within(bar()).getAllByRole("img");
    expect(inTheBar).toHaveLength(2);
    [0, 5].forEach((at, place) => {
      const beside = within(cards()[at]?.querySelector("figure") as HTMLElement).getByRole("img");
      expect([at, piecesOf(inTheBar[place] as HTMLElement)]).toEqual([at, piecesOf(beside)]);
      expect([at, inTheBar[place]?.getAttribute("aria-label")]).toEqual([at, beside.getAttribute("aria-label")]);
    });
  });

  test("test_nothing_is_handed_over_of_a_rank_or_a_fit_and_nothing_a_person_typed", async () => {
    const user = withTheBar({ ...first, bands });
    const top = first.ranking.ranked[0] as RankedArea;

    await user.click(card(0).getByRole("button", { name: COMPARE.addNamed(nameOf(top.area_id)) }));

    // The bar names the area and draws its town. It says nothing of how the area did.
    expect(bar()).toHaveTextContent(nameOf(top.area_id));
    expect(bar().textContent).not.toMatch(/\b(rank|fit)\b/i);
    expect(bar().textContent?.includes(String(Math.floor(top.score * 100)))).toBe(false);
  });
});

describe("nothing to rank by", () => {
  test("test_with_nothing_set_no_fit_is_shown_because_it_would_say_nothing", () => {
    show({ ranking: recordedAnswer("rank", "rank-empty-spec").body.data, withDetails: false });

    expect(cards()).toHaveLength(20);
    expect(screen.queryByText(/of 100/)).toBeNull();
    expect(screen.queryByText(COMPLETENESS.all)).toBeNull();
  });
});

describe("automated checks", () => {
  test("test_a_list_of_results_has_no_accessibility_fault", async () => {
    const { container, user } = show(first);
    await user.click(card(FARROWMERE).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` }));

    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_a_list_of_results_as_it_first_stands_has_no_accessibility_fault", async () => {
    const { container } = show({ ...first, opened: false });

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
      show({ ranking, explanations, facts });

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
          // The bands of the strip, of five, as the ranking gives them.
          ...area.strip.flatMap((mark) => [mark.band, mark.spread_low, mark.spread_high].map(String)),
          "5",
          // The top of the scale.
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
      show({ ranking, explanations, facts });
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
          // The places of the search, by the names the answer gives them.
          ...ranking.places.map((place) => place.name),
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

/**
 * jsdom lays nothing out, so a test says where the page stands and where a part stands in
 * the window. The page goes where a test, or the list, sends it.
 */
function aWindow() {
  const page = { at: 0 };
  const moves: { by?: number; to?: number; into?: string | null; how?: unknown }[] = [];
  const stands = (part: Element, at: () => number) =>
    jest.spyOn(part, "getBoundingClientRect").mockImplementation(() => ({ top: at(), bottom: at() + 34 }) as DOMRect);
  const open = (toAResult = 0) => {
    Object.defineProperty(window, "scrollY", { configurable: true, get: () => page.at });
    Object.defineProperty(window, "scrollBy", {
      configurable: true,
      value: ({ top, behavior }: ScrollToOptions) => {
        page.at += top ?? 0;
        moves.push({ by: top, how: behavior });
      },
    });
    Object.defineProperty(window, "scrollTo", {
      configurable: true,
      value: ({ top, behavior }: ScrollToOptions) => {
        page.at = top ?? 0;
        moves.push({ to: top, how: behavior });
      },
    });
    Element.prototype.scrollIntoView = function scrollIntoView(this: Element, how?: unknown) {
      page.at += toAResult;
      moves.push({ into: this.getAttribute("data-area"), how });
    };
  };
  const close = () => {
    for (const name of ["scrollY", "scrollBy", "scrollTo", "matchMedia"]) delete (window as unknown as Record<string, unknown>)[name];
    delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
  };
  const frames = async (count: number) => {
    for (let at = 0; at < count; at += 1) await new Promise<void>((done) => requestAnimationFrame(() => done()));
  };
  return { page, moves, stands, open, close, frames };
}

describe("what is pressed in a result stays under the hand", () => {
  const { page, moves, stands, open, close, frames } = aWindow();

  beforeEach(() => {
    page.at = 460;
    moves.length = 0;
    open();
  });

  afterEach(close);

  test("test_the_page_is_put_back_where_the_browser_sent_it_as_the_working_of_the_first_result_opened", async () => {
    // Seen in a browser, on a phone, once the page was scrolled by 430 px or more: a press on
    // "Show the working" sent the page 1,634 px down, and the button stood 1,316 px over the
    // top of the window. On a narrow screen what refines a search comes before the first
    // result in the page and is drawn after it, so the browser held the page by it.
    show({ ...first, opened: false });
    const pressed = card(FARROWMERE).getByRole("button", { name: RESULTS.workingOf("Farrowmere") });
    stands(pressed, () => 317.5 - (page.at - 460));

    fireEvent.click(pressed);
    expect(pressed).toHaveAttribute("aria-expanded", "true");
    // What the browser does of itself, as what it holds the page by goes down.
    page.at += 1634;
    await frames(2);

    expect(moves).toEqual([{ by: -1634, how: "instant" }]);
    expect(page.at).toBe(460);
    expect(pressed.getBoundingClientRect().top).toBe(317.5);
  });

  test("test_every_press_that_opens_or_closes_in_place_is_held_in_the_first_result_and_in_the_rest", async () => {
    show({ ...first, opened: false });
    // Each is found as it is come to: what a working holds is on the page once it is open.
    const held = [
      () => card(FARROWMERE).getByRole("button", { name: RESULTS.workingOf("Farrowmere") }),
      // The key of a source, which stands in the working.
      () => card(FARROWMERE).getByRole("button", { name: SOURCE.buttonFor(RESULTS.sourceOfReason(1, "Farrowmere")) }),
      () => card(FARROWMERE).getByRole("button", { name: SOURCE.buttonFor(RESULTS.sourceOfTradeOff("Farrowmere")) }),
      // What opens how the fit is worked out.
      () => card(FARROWMERE).getByRole("button", { name: `${BREAKDOWN.title}: Farrowmere` }),
      () => card(FARROWMERE).getByRole("button", { name: COMPARE.addNamed("Farrowmere") }),
      // A result of the rest of the list, which stands after the map.
      () => card(3).getByRole("button", { name: /^Show the working: / }),
    ].map((find) => find);

    for (const find of held) {
      const pressed = find();
      moves.length = 0;
      page.at = 460;
      stands(pressed, () => 200 - (page.at - 460));
      fireEvent.click(pressed);
      page.at += 235;
      await frames(2);
      expect([pressed.getAttribute("aria-label"), moves]).toEqual([pressed.getAttribute("aria-label"), [{ by: -235, how: "instant" }]]);
    }
  });

  test("test_a_press_that_stays_where_it_stood_moves_nothing", async () => {
    show({ ...first, opened: false });
    const pressed = card(FARROWMERE).getByRole("button", { name: RESULTS.workingOf("Farrowmere") });
    stands(pressed, () => 477.5);

    fireEvent.click(pressed);
    await frames(2);

    expect(moves).toEqual([]);
  });

  test("test_a_press_that_leads_elsewhere_takes_the_page_where_it_leads", async () => {
    // "Show on the map" takes the page to the map, and the name of a result to the page of
    // its area. Neither opens anything in place, and the list holds neither.
    const { onSelect } = show(first);
    const onMap = card(FARROWMERE).getByRole("button", { name: RESULTS.showOnMap("Farrowmere") });
    stands(onMap, () => 524 - (page.at - 460));

    fireEvent.click(onMap);
    // What draws the page takes it to the map.
    page.at -= 265;
    await frames(2);

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(moves).toEqual([]);
    expect(page.at).toBe(195);
  });
});

describe("a card chosen on the map", () => {
  /** How far the page goes to bring the chosen result into view. */
  const TO_THE_RESULT = 1108;
  const { page, moves, stands, open, close } = aWindow();
  const motion = (reduced: boolean) =>
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: (query: string) => ({ matches: reduced && query.includes("reduce"), media: query }),
    });
  /** A pin of the map, which stands outside the list and has the focus as it is pressed. */
  function aPin(at: () => number): HTMLElement {
    const pin = document.createElement("button");
    document.body.append(pin);
    stands(pin, at);
    pin.focus();
    return pin;
  }

  beforeEach(() => {
    page.at = 0;
    moves.length = 0;
    open(TO_THE_RESULT);
  });

  afterEach(() => {
    close();
    document.body.querySelectorAll(":scope > button").forEach((pin) => pin.remove());
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
        unranked={first.ranking.unranked}
        areasRanked={first.ranking.areas_ranked}
        areasListed={first.ranking.areas_listed}
        busy={false}
        selectedId={selectedId}
        onSelect={() => undefined}
        onHover={() => undefined}
        onEdit={() => undefined}
      />
    );
  }

  test("test_its_card_is_brought_into_view_where_the_map_stays_in_the_window_and_the_focus_stays_where_it_was", () => {
    // Beside the list the map has come to rest at the head of the window, and stays there as the page scrolls.
    motion(false);
    const { rerender } = render(list(null));
    const pin = aPin(() => 91);

    rerender(list("syn-n0023"));

    // The page is taken to the result and back at once, to see that the pin stays, and then glides there.
    expect(moves).toEqual([
      { into: "syn-n0023", how: { block: "nearest", behavior: "instant" } },
      { to: 0, how: "instant" },
      { into: "syn-n0023", how: { block: "nearest", behavior: "smooth" } },
    ]);
    expect(pin).toHaveFocus();
    expect(screen.getAllByRole("article").filter((one) => one.getAttribute("aria-current") === "true")).toHaveLength(1);
    rerender(list(null));
    expect(moves).toHaveLength(3);
  });

  test("test_where_the_map_goes_with_the_page_the_page_is_left_where_it_is_and_the_card_is_marked", () => {
    // Seen in a browser, on a phone: a pin that was pressed went 1,108 px up and out of the
    // window, and the card of the map with it. "Show in the list" is the press that goes to the list.
    motion(false);
    const { rerender } = render(list(null));
    const pin = aPin(() => 329.5 - page.at);

    rerender(list("syn-n0023"));

    expect(moves).toEqual([
      { into: "syn-n0023", how: { block: "nearest", behavior: "instant" } },
      { to: 0, how: "instant" },
    ]);
    expect(page.at).toBe(0);
    expect(pin.getBoundingClientRect().top).toBe(329.5);
    expect(pin).toHaveFocus();
    // It is marked as the one that is chosen all the same, and says so to whoever hears the page.
    const chosen = screen.getAllByRole("article").filter((one) => one.getAttribute("aria-current") === "true");
    expect(chosen.map((one) => one.closest("li")?.getAttribute("data-area"))).toEqual(["syn-n0023"]);
  });

  test("test_an_area_chosen_from_its_own_result_is_not_brought_anywhere", () => {
    // Seen in a browser, on a phone: "Show on the map" took the page to the map, and the list
    // brought it back to the result, so that the map was out of sight again.
    motion(false);
    const { rerender } = render(list(null));
    const pressed = screen.getAllByRole("button", { name: /^Show the working: / })[0] as HTMLElement;
    pressed.focus();

    rerender(list(first.ranking.ranked[0]?.area_id ?? ""));

    expect(moves).toEqual([]);
    expect(pressed).toHaveFocus();
  });

  test("test_with_reduced_motion_the_list_jumps_and_does_not_glide", () => {
    motion(true);
    const { rerender } = render(list(null));
    aPin(() => 91);

    rerender(list("syn-n0023"));

    expect(moves.at(-1)).toEqual({ into: "syn-n0023", how: { block: "nearest", behavior: "auto" } });
  });
});

describe("the steps of every result stand in one column", () => {
  // The founder, who had walked the website twice: "on the ranking cards, ensure the gauges
  // all line up vertically so that a user can scan downwards with ease". Measured in a
  // browser before: at 1440 by 900 the steps of the first three results began at 411.78,
  // 403.8, 464.22, 248.66, 399.16, 394.86 and 281.66 px, and at 390 by 844 at 136, 119.66
  // and 141.66 px. Measured with what is held here: at 362.5 px, every one, and at 141.66 px.
  // Of a search that ranks ten: at 370 px and at 141.66 px, in the cards and the rows alike.
  const STRIP_RULES = rulesOf(readFileSync(path.join(__dirname, "..", "Strip", "Strip.module.css"), "utf8"));
  const TOKENS = readFileSync(path.join(__dirname, "..", "..", "styles", "tokens.css"), "utf8");
  const setBy = (rules: typeof STYLES, selector: string, under: string | null = null) =>
    new Map(rules.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));
  const many = {
    ranking: recordedAnswer("rank", "rank-by-the-river").body.data,
    ...recordedAnswer("explain_top", "explanations-by-the-river").body.data,
  };
  /** What holds the lines of each result that draws any. */
  const strips = () => cards().flatMap((one) => [...one.querySelectorAll<HTMLElement>("div[data-ends]")]);

  test("test_every_result_of_a_list_is_handed_the_names_of_one_column", () => {
    // A search that asks for no vibe: every result draws the vibes the service chose for it.
    show({ ...money, opened: false });
    const drawn = namesOf(money.ranking.ranked.map((area) => area.strip), meta.data.tags);

    // The recorded search ranks more results than are cards, and its results draw many vibes.
    expect(money.ranking.ranked.length).toBeGreaterThan(SHOWN_AT_FIRST);
    expect(drawn.length).toBeGreaterThan(4);
    expect(columnOf(money.ranking.ranked, meta.data, money.ranking.spec, "alone", "working")).toEqual(drawn);
    // Every result is handed the same names, whichever vibes it draws itself: of every
    // result of the ranking, of those that are one press away as well.
    expect(strips().length).toBe(SHOWN_AT_FIRST);
    expect([...new Set(strips().map((strip) => strip.style.getPropertyValue("--names")))]).toEqual([asLines(drawn)]);
    const own = new Set(money.ranking.ranked.slice(0, SHOWN_AT_FIRST).map((area) => asLines(namesOf([area.strip], meta.data.tags))));
    expect(own.size).toBeGreaterThan(1);
    expect(own.has(asLines(drawn))).toBe(false);
    // With the names every line is told of the two words that may stand under a name, so
    // that the column is as wide on a line that says them as on one that does not.
    for (const strip of strips()) {
      expect([strip.style.getPropertyValue("--beside-1"), strip.style.getPropertyValue("--beside-2")]).toEqual([
        asLines([KNOWN.some]),
        asLines([KNOWN.none]),
      ]);
      expect([strip.style.getPropertyValue("--beside-1-more"), strip.style.getPropertyValue("--beside-2-more")]).toEqual(["11", "11"]);
    }
    // The list itself lays no name out: nothing of a result but its lines stands in the column.
    for (const list of lists()) expect(list.style.getPropertyValue("--names")).toBe("");
  });

  test("test_the_column_holds_the_names_of_the_lines_that_are_drawn_and_of_no_other", () => {
    // Seen in a browser: with the names of every vibe the service gave, of which a result
    // draws those that were asked for, the steps stood 20 px further from the longest name
    // that was drawn than they need.
    const { unmount } = show({ ...many, opened: false });
    const every = namesOf(many.ranking.ranked.map((area) => area.strip), meta.data.tags);

    expect(many.ranking.spec.tags.map((tag) => tag.tag_id)).toEqual(["built_age"]);
    expect(every.length).toBeGreaterThan(4);
    expect([...new Set(strips().map((strip) => strip.style.getPropertyValue("--names")))]).toEqual([asLines(["Age of buildings"])]);
    unmount();
    // Where the look has the others stand beside what was asked for, the names of all of them.
    const beside = show({ ...many, opened: false, others: "beside" });
    expect([...new Set(strips().map((strip) => strip.style.getPropertyValue("--names")))]).toEqual([asLines(every)]);
    beside.unmount();
    // What was asked for and has no figure stands in the column by its name too.
    show({ ...two, opened: false });
    expect(columnOf(two.ranking.ranked, meta.data, two.ranking.spec, "alone", "working")).toEqual([
      ...namesOf(two.ranking.ranked.map((area) => area.strip), meta.data.tags),
      BREAKDOWN.budget,
    ]);
    // And not where what a fit is based on is said in full on the result, which names it in a sentence.
    expect(columnOf(two.ranking.ranked, meta.data, two.ranking.spec, "alone", "result")).toEqual(
      namesOf(two.ranking.ranked.map((area) => area.strip), meta.data.tags),
    );
  });

  test("test_the_column_is_as_wide_once_more_results_are_shown_as_it_was_before", async () => {
    const { user } = show({ ...money, opened: false });
    const before = strips().map((strip) => strip.style.getPropertyValue("--names"));
    // Among the names are those of vibes that only a result that is yet to be shown draws.
    const shown = namesOf(money.ranking.ranked.slice(0, SHOWN_AT_FIRST).map((area) => area.strip), meta.data.tags);
    expect(before[0]).toBe(asLines(namesOf(money.ranking.ranked.map((area) => area.strip), meta.data.tags)));
    expect(before[0] === asLines(shown)).toBe(false);

    await user.click(screen.getByRole("button", { name: /^Show \d+ more$/ }));

    expect(strips().length).toBeGreaterThan(before.length);
    expect([...new Set(strips().map((strip) => strip.style.getPropertyValue("--names")))]).toEqual([...new Set(before)]);
  });

  test("test_what_a_row_holds_begins_where_what_a_card_holds_begins", () => {
    // Measured in a browser: the steps of a row stood 9 px before the steps of every card
    // over it, and 6 px on a phone. A row is a plain frame, whose edge is one art pixel
    // wide where the rule of a box is four.
    expect(/--edge:\s*var\(--px\);/.test(TOKENS)).toBe(true);
    expect(/--frame-box-wide:\s*calc\(var\(--px\) \* 4\) calc\(var\(--px\) \* 6\) calc\(var\(--px\) \* 6\) calc\(var\(--px\) \* 4\);/.test(TOKENS)).toBe(true);

    expect(setBy(STYLES, ".card").get("padding")).toBe("var(--space-2) var(--inside) var(--space-3)");
    expect(setBy(STYLES, ".row").get("padding")).toBe("var(--space-2) calc(var(--inside) + var(--px) * 3)");
    expect(setBy(STYLES, ".row", "@container (max-width: 30rem)").get("padding-inline")).toBe("calc(var(--inside) + var(--px) * 3)");
    // The room is one room, said once for both at each width.
    const said = STYLES.filter((rule) => rule.sets.has("--inside"));
    expect(said.map((rule) => [rule.under, rule.selector, rule.sets.get("--inside")])).toEqual([
      [null, ".card", "var(--space-3)"],
      [null, ".row", "var(--space-3)"],
      ["@container (max-width: 30rem)", ".card", "var(--space-2)"],
      ["@container (max-width: 30rem)", ".row", "var(--space-2)"],
    ]);
    // A row draws the lines of its strip as a card does: in the columns of every line.
    show({ ...many, opened: true });
    const rows = cards().filter((one) => one.parentElement?.getAttribute("data-kind") === "row");
    expect(cards().length).toBe(many.ranking.ranked.length);
    expect(rows.length).toBeGreaterThan(SHOWN_AT_FIRST);
    for (const row of rows) {
      const strip = row.querySelector<HTMLElement>("div[data-ends]");
      expect([strip?.getAttribute("data-short"), strip?.getAttribute("data-ends")]).toEqual(["true", ENDS_ON_A_RESULT]);
    }
  });

  test("test_one_line_of_the_look_names_each_end_of_a_gauge_under_its_picture_and_the_steps_keep_their_column", () => {
    // Built two ways, behind one line. Either way each end of every gauge has its picture.
    expect(ENDS_ON_A_RESULT_MAY_BE).toEqual(["pictured", "named"]);
    expect(ENDS_ON_A_RESULT).toBe("pictured");

    for (const ends of ENDS_ON_A_RESULT_MAY_BE) {
      const { unmount } = show({ ...first, opened: false, ends });
      const drawn = [...document.querySelectorAll("div[data-ends], span[data-as][data-ends]")].map((one) => one.getAttribute("data-ends"));
      expect(drawn.length).toBeGreaterThan(10);
      expect([...new Set(drawn)]).toEqual([ends]);
      // An end has its name under its picture only where the look has the ends named.
      const named = document.querySelectorAll("[class*='ofEnd']").length;
      const gauges = document.querySelectorAll("span[data-as][data-ends]").length;
      expect([ends, named]).toEqual([ends, ends === "named" ? gauges * 2 : 0]);
      expect([ends, document.querySelectorAll("span[data-as][data-ends] [class*='end'] > [aria-hidden='true']").length]).toEqual([ends, gauges * 2]);
      unmount();
    }
    // The room of an end is said once, of every line, whichever way the ends are drawn.
    const rooms = STRIP_RULES.filter((rule) => rule.sets.has("--room"));
    expect(rooms.map((rule) => [rule.under, rule.selector])).toEqual([[null, ".strip"]]);
  });
});
