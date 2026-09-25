import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { NAMED } from "@/content/area";
import { FACT_COLUMNS } from "@/content/facts";
import { COMPARE } from "@/content/compare";
import {
  APART,
  BREAKDOWN,
  COMPLETENESS,
  CONFIDENCE,
  COST,
  JOURNEYS,
  RESULTS,
  SOURCE,
  STRIP,
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
import { inWords } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { figuresNotFrom, saidBy as saidByFacts } from "../../../test/support/figures";
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
      // Every answer names every place of its spec.
      placeNames={placeNames ?? Object.fromEntries(ranking.places.map((place) => [place.place_id, place.name]))}
      noFit={ranking.empty_spec}
      unranked={ranking.unranked}
      areasRanked={ranking.areas_ranked}
      areasListed={ranking.areas_listed}
      busy={busy}
      selectedId={selectedId}
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

  test("test_the_first_five_are_cards_with_a_reason_and_the_rest_are_rows", () => {
    show({ ...first, opened: false });

    const withAReason = cards().filter((one) => within(one).queryByRole("heading", { name: RESULTS.reasonsTitle }));
    expect(withAReason).toHaveLength(5);
    expect(withAReason).toEqual(cards().slice(0, 5));
    for (const row of cards().slice(5)) {
      expect(within(row).getByRole("button", { name: /^Show the working: / })).toBeInTheDocument();
      expect(within(row).queryByRole("heading", { name: RESULTS.tradeOffTitle })).toBeNull();
    }
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
  test("test_the_answer_is_a_few_lines_and_everything_else_is_one_press_away", () => {
    show({ ...first, opened: false });
    const farrowmere = cards()[FARROWMERE] as HTMLElement;
    const given = first.explanations.find((one) => one.area_id === "syn-n0006");

    // Rank, name, the label beside it and fit. What the fit rests on. The strip. One reason and
    // the trade-off.
    expect(within(farrowmere).getByRole("heading", { level: 3, name: "Farrowmere" })).toBeInTheDocument();
    expect(within(farrowmere).getByText("Quillhaven 006")).toBeInTheDocument();
    expect(within(farrowmere).getByText("71 of 100")).toBeInTheDocument();
    // Its fit rests on everything that counts, so no more is said of what it rests on.
    expect(within(farrowmere).queryByText(COMPLETENESS.all)).toBeNull();
    expect(within(farrowmere).getByRole("list", { name: STRIP.label("Farrowmere") })).toBeInTheDocument();
    expect(within(farrowmere).getByText(given?.reasons[0]?.text ?? "no reason")).toBeInTheDocument();
    expect(within(farrowmere).getByText(given?.trade_off?.text ?? "no trade-off")).toBeInTheDocument();
    // The second and third reasons, and everything else, wait for the working to be opened.
    expect(given?.reasons).toHaveLength(3);
    expect(within(farrowmere).queryByText(given?.reasons[1]?.text ?? "none")).toBeNull();
    expect(within(farrowmere).queryByText(given?.orientation.text ?? "none")).toBeNull();
    expect(within(farrowmere).queryAllByRole("table")).toEqual([]);
    // The only pictures are the marks of the strip: where the area is on the map is in the working.
    expect(within(farrowmere).queryAllByRole("img", { name: /^Where / })).toEqual([]);
    expect(farrowmere.querySelectorAll("svg")).toHaveLength(0);
    expect(within(farrowmere).queryByRole("heading", { name: COST.title })).toBeNull();
    expect(within(farrowmere).queryByRole("heading", { name: JOURNEYS.title })).toBeNull();
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
      expect(ways.length).toBe(3);
    }
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

  test("test_the_strip_is_the_vibes_the_api_chose_in_the_order_it_gave_them", () => {
    show({ ...first, opened: false });

    first.ranking.ranked.slice(0, 10).forEach((area, at) => {
      const name = areas.find((one) => one.area_id === area.area_id)?.name ?? "";
      const given = first.explanations.find((one) => one.area_id === area.area_id);
      // A vibe that a sentence of the card is about is drawn beside that sentence, and once.
      const beside = [given?.reasons[0], given?.trade_off].flatMap((sentence) => sentence?.fact_ids ?? []);
      const marks = within(card(at).getByRole("list", { name: STRIP.label(name) })).getAllByRole("listitem");
      // The picture of each mark says its band in words.
      expect(marks.map((mark) => within(mark).getByRole("img").getAttribute("aria-label")?.split(",")[0])).toEqual(
        area.strip.filter((mark) => !beside.includes(mark.fact_id)).map((mark) => inWords(mark)),
      );
      // Every mark the API chose is drawn, in the strip or beside its sentence.
      expect(card(at).getAllByRole("img")).toHaveLength(area.strip.length);
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

  test("test_a_mark_of_a_card_opens_to_its_fact_and_a_mark_of_a_row_does_not", async () => {
    const { user } = show({ ...first, opened: false });
    const strip = (at: number, name: string) => within(card(at).getByRole("list", { name: STRIP.label(name) }));

    // The API sends the fact of every mark of the first five, with the reasons.
    await user.click(strip(FARROWMERE, "Farrowmere").getAllByRole("button")[0] as HTMLElement);
    const leafy = first.facts.find((fact) => fact.fact_id === "syn-n0006/tag/leafy");
    expect(strip(FARROWMERE, "Farrowmere").getByText(leafy?.slots.judgement ?? "none")).toBeInTheDocument();
    expect(strip(FARROWMERE, "Farrowmere").getByRole("button", { name: /^Source/ })).toBeInTheDocument();
    // A row has no fact in hand, so its marks say where the area sits and open nothing.
    expect(strip(5, "Dulcimer Green").queryAllByRole("button")).toEqual([]);
  });

  test("test_a_row_gives_the_rank_the_name_and_the_fit_and_leaves_the_borough_to_the_table", () => {
    show({ ...first, opened: false });

    for (const row of cards().slice(5)) {
      const heading = row.querySelector("header") as HTMLElement;
      expect(within(heading).getByRole("heading", { level: 3 })).toBeInTheDocument();
      expect(heading.textContent).toMatch(/^Rank \d+\d+.+Fit \d+ of 100$/);
      expect(heading.textContent?.includes("Quillhaven")).toBe(false);
    }
    // A card gives the borough.
    for (const one of cards().slice(0, 5)) expect(one.querySelector("header")?.textContent).toContain("Quillhaven");
  });

  test("test_a_result_says_what_its_fit_rests_on_only_where_that_is_not_everything", () => {
    show({ ...first, opened: false });
    const partial = first.ranking.ranked
      .slice(0, 10)
      .map((area) => area.contributions.filter((part) => part.present).length < area.contributions.length);

    // A row says it where its fit rests on part of what counts, and the rest say nothing of it.
    expect(partial.slice(5)).toEqual(expect.arrayContaining([true, false]));
    cards().forEach((result, at) => {
      expect(result.textContent?.includes("Based on")).toBe(partial[at]);
    });
  });

  test("test_a_card_says_what_its_fit_rests_on_where_that_is_not_everything", () => {
    show({ ...money, opened: false });
    const partial = money.ranking.ranked
      .slice(0, 5)
      .map((area) => area.contributions.filter((part) => part.present).length < area.contributions.length);

    expect(partial).toEqual([false, false, true, false, false]);
    cards()
      .slice(0, 5)
      .forEach((result, at) => expect(result.textContent?.includes("Based on")).toBe(partial[at]));
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
    });
  });

  test("test_the_first_reason_is_in_the_answer_and_the_others_are_in_the_working", () => {
    show(first);
    const given = first.explanations[FARROWMERE];

    const others = within(working(FARROWMERE)).getByRole("heading", { name: RESULTS.moreReasons })
      .parentElement as HTMLElement;
    expect(within(others).getAllByRole("listitem").map((item) => item.querySelector("p")?.textContent)).toEqual(
      given?.reasons.slice(1).map((reason) => reason.text),
    );
    expect(within(others).getByRole("list").tagName).toBe("OL");
    expect(working(FARROWMERE).textContent?.includes(given?.reasons[0]?.text ?? "none")).toBe(false);
    const tradeOff = card(FARROWMERE).getByRole("heading", { name: RESULTS.tradeOffTitle }).parentElement as HTMLElement;
    expect(tradeOff).toHaveTextContent(given?.trade_off?.text ?? "no trade-off");
  });

  test("test_with_no_trade_off_the_card_says_so", () => {
    const [top, ...rest] = first.explanations;
    if (!top) throw new Error("the recording explains nothing");

    show({ ...first, explanations: [{ ...top, trade_off: null }, ...rest] });

    expect(RESULTS.noTradeOff).toBe("No trade-off found for this search");
    expect(tradeOff(0)).toHaveTextContent(RESULTS.noTradeOff);
    expect(card(1).queryByText(RESULTS.noTradeOff)).toBeNull();
    // Seen in a browser: a warning mark over "No trade-off found". It warned of nothing.
    expect(tradeOff(0).querySelector(".tradeOffMark")).toBeNull();
    expect(tradeOff(1).querySelector(".tradeOffMark")).not.toBeNull();
    // Nothing else is put in its place: no sentence, and no source of one.
    expect(within(tradeOff(0)).queryByRole("button")).toBeNull();
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

  test("test_with_one_reason_there_are_no_more_to_give_in_the_working", () => {
    const [top, ...rest] = first.explanations;
    if (!top) throw new Error("the recording explains nothing");

    show({ ...first, explanations: [{ ...top, reasons: top.reasons.slice(0, 1) }, ...rest] });

    expect(card(0).getByText(top.reasons[0]?.text ?? "none")).toBeInTheDocument();
    expect(within(working(0)).queryByRole("heading", { name: RESULTS.moreReasons })).toBeNull();
    expect(within(working(1)).getByRole("heading", { name: RESULTS.moreReasons })).toBeInTheDocument();
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

    // The reason and the trade-off, each a line.
    expect(held).toBe(2);
    for (const skeleton of document.querySelectorAll(".skeleton")) {
      expect(skeleton.closest("[aria-hidden='true']")).not.toBeNull();
    }

    cleanup();
    show({ ...first, opened: false });
    expect(cards()[FARROWMERE]?.querySelectorAll(".skeleton")).toHaveLength(0);
    // The same parts, in the same order, before and after.
    expect(card(FARROWMERE).getAllByRole("heading").map((heading) => heading.textContent)).toEqual(parts);
  });

  test("test_reasons_that_could_not_be_loaded_are_said_and_the_rest_of_the_card_is_there", () => {
    show({ ...first, explanations: [], explained: false, explainFailed: true });

    expect(card(FARROWMERE).getByText(RESULTS.reasonsFailed)).toBeInTheDocument();
    expect(cards()[FARROWMERE]?.querySelectorAll(".skeleton")).toHaveLength(0);
    expect(card(FARROWMERE).getByText("£975 to £1,300")).toBeInTheDocument();
  });

  test("test_where_it_is_gives_the_nearest_station_and_a_picture_named_for_the_area", () => {
    show(first);

    const station = within(card(FARROWMERE).getByRole("group", { name: "Nearest station" }));
    expect(station.getByText("Farrowmere")).toBeInTheDocument();
    expect(station.getByText("5")).toBeInTheDocument();
    expect(station.getByText("Cobalt line")).toBeInTheDocument();
    expect(
      card(FARROWMERE).getByRole("img", { name: "Where Farrowmere is among the areas of this data" }),
    ).toBeInTheDocument();
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
    // Where it is, the station, three reasons, the trade-off, the journey and the cost.
    expect(sources).toHaveLength(8);
    expect(new Set(sources.map((source) => source.getAttribute("aria-label"))).size).toBe(8);
    for (const source of sources) expect(source).toHaveClass("target-min");
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
    const aJourney = (at: number) => /\/travel\//.test(first.explanations[at]?.trade_off?.fact_ids[0] ?? "");

    // Recorded: the third area is the leafiest and the quietest, and its journey is what it gives up.
    expect([0, 1, 2, 3, 4].filter(aJourney)).toEqual([2]);
    for (const at of [0, 1, 2, 3, 4]) {
      const verdict = within(tradeOff(at)).queryByText(/your limit of/);
      if (aJourney(at)) expect(verdict).toBeInTheDocument();
      else expect(verdict).toBeNull();
    }
  });
});

describe("a vibe that is the reason, or the trade-off", () => {
  const leafy = {
    ranking: recordedAnswer("rank", "rank-shelf").body.data,
    ...recordedAnswer("explain_top", "explanations-shelf").body.data,
  };
  /** The part of a card under a heading of its own: "Why it fits", or "Trade-off". */
  const part = (at: number, name: string) => card(at).getByRole("heading", { name }).parentElement as HTMLElement;
  const strip = (at: number, name: string) => card(at).queryByRole("list", { name: STRIP.label(name) });
  const factsOf = (shown: typeof leafy) => ({ facts: shown.facts });

  test("test_a_vibe_that_is_the_first_reason_is_drawn_once_beside_its_sentence_and_not_again_in_the_strip", () => {
    // Seen in a browser: "Asked for Leafy" and its five cells, and directly under them
    // "Leafy: band 5 of 5, counted from least to most", which said the same again.
    show({ ...leafy, ...factsOf(leafy), opened: false });
    const [top] = leafy.ranking.ranked;
    const given = leafy.explanations.find((one) => one.area_id === top?.area_id);
    const mark = top?.strip.find((one) => given?.reasons[0]?.fact_ids.includes(one.fact_id));
    if (top === undefined || mark === undefined) throw new Error("the first reason of the recording is no vibe of its strip");

    const why = part(0, RESULTS.reasonsTitle);
    // Its picture stands beside the sentence, and says which end the area sits at.
    expect(within(why).getAllByRole("img").map((picture) => picture.getAttribute("aria-label"))).toEqual([
      `${STRIP.band(mark.band)}, ${STRIP.from(STRIP.least, STRIP.most)}, ${STRIP.asked}`,
    ]);
    expect(mark.band).toBe(5);
    expect(why.textContent?.startsWith(`${RESULTS.reasonsTitle}${STRIP.most}`)).toBe(true);
    expect(why.textContent?.includes(given?.reasons[0]?.text ?? "no reason")).toBe(true);
    // The strip holds the others, and says that they are beside what was asked for.
    const names = within(strip(0, nameOf(top.area_id)) as HTMLElement).getAllByRole("listitem");
    expect(names).toHaveLength(top.strip.length - 1);
    expect(names.some((one) => one.textContent?.includes("Leafy"))).toBe(false);
    expect(names[0]).toHaveTextContent(STRIP.group.also);
    // Every mark the API chose is still drawn, each once.
    expect(card(0).getAllByRole("img")).toHaveLength(top.strip.length);
  });

  test("test_a_vibe_that_is_the_reason_is_said_in_short_and_what_it_leaves_out_is_behind_its_source", async () => {
    // Seen by a reviewer: "Why it fits" was one sentence of thirty words about bands and
    // dates, the same on every card that led with that vibe, and half of it a disclaimer.
    const { user } = show({ ...leafy, ...factsOf(leafy), opened: false });
    const [top] = leafy.ranking.ranked;
    const given = leafy.explanations.find((one) => one.area_id === top?.area_id);
    const sentence = given?.reasons[0];
    const fact = leafy.facts.find((one) => one.fact_id === sentence?.fact_ids[0]);
    if (top === undefined || sentence === undefined || fact === undefined) throw new Error("the recording gives no reason");
    const why = part(0, RESULTS.reasonsTitle);

    expect(fact.kind).toBe("tag");
    expect(sentence.text).toBe("Leafy: band 5 of 5, counted from least to most, among the 21 areas compared in this release.");
    expect(within(why).getByText(sentence.text)).toBeInTheDocument();
    // The line that the recipe is a judgement, and the date of its parts, are not on the card.
    expect(why.textContent?.includes(fact.slots.judgement ?? "none")).toBe(false);
    expect(why.textContent?.includes("Parts dated")).toBe(false);
    await user.click(within(why).getByRole("button", { name: /^Source for / }));

    // They are one press away, in the API's words, with the source.
    expect(within(why).getByText(fact.slots.judgement ?? "none")).toBeInTheDocument();
    expect(within(why).getByText(fact.slots.made_from ?? "none")).toBeInTheDocument();
    expect(within(why).getByText(`${SOURCE.dataFrom} ${fact.as_of}`)).toBeInTheDocument();
  });

  test("test_a_vibe_that_is_the_trade_off_is_drawn_once_beside_its_sentence_too", () => {
    show({ ...first, opened: false });
    const at = first.ranking.ranked.findIndex((area) => {
      const given = first.explanations.find((one) => one.area_id === area.area_id);
      return area.strip.some((mark) => given?.trade_off?.fact_ids.includes(mark.fact_id));
    });
    const area = first.ranking.ranked[at];
    if (area === undefined) throw new Error("no trade-off of the recording is a vibe of its strip");

    expect(within(tradeOff(at)).getAllByRole("img")).toHaveLength(1);
    expect(within(strip(at, nameOf(area.area_id)) as HTMLElement).getAllByRole("listitem")).toHaveLength(
      area.strip.length - 1,
    );
    expect(card(at).getAllByRole("img")).toHaveLength(area.strip.length);
  });

  test("test_a_reason_that_is_no_vibe_leaves_the_strip_whole_and_has_no_picture", () => {
    // Recorded: the first reason of the fourth area is its journey. Its trade-off is a vibe.
    show({ ...first, opened: false });
    const at = first.ranking.ranked.findIndex((one) => one.area_id === "syn-n0003");
    const area = first.ranking.ranked[at];

    expect(first.explanations[at]?.reasons[0]?.fact_ids[0]).toBe("syn-n0003/travel/syn-p0021.pt");
    expect(within(part(at, RESULTS.reasonsTitle)).queryAllByRole("img")).toEqual([]);
    expect(within(strip(at, "Cindermoor") as HTMLElement).getAllByRole("listitem")).toHaveLength(
      (area?.strip.length ?? 0) - 1,
    );
  });

  test("test_while_the_reasons_are_waited_for_the_strip_is_whole", () => {
    show({ ...leafy, explanations: [], explained: false, opened: false });
    const [top] = leafy.ranking.ranked;

    expect(within(strip(0, nameOf(top?.area_id ?? "")) as HTMLElement).getAllByRole("listitem")).toHaveLength(
      top?.strip.length ?? 0,
    );
  });

  test("test_a_short_sentence_is_laid_out_as_a_long_one_is_word_for_word_with_its_source", () => {
    // The sentence is the API's to write, and is to be made short. The card holds no word of
    // it, and no room for any: whatever comes is shown as it came, and ends in its source.
    const short = "Leafy: among the most here.";
    const [top] = leafy.ranking.ranked;
    const explanations = leafy.explanations.map((one) =>
      one.area_id === top?.area_id
        ? { ...one, reasons: one.reasons.map((reason, at) => (at === 0 ? { ...reason, text: short } : reason)) }
        : one,
    );
    show({ ...leafy, explanations, ...factsOf(leafy), opened: false });

    const why = part(0, RESULTS.reasonsTitle);
    expect(within(why).getByText(short).tagName).toBe("P");
    expect(within(why).getAllByRole("button", { name: /^Source/ })).toHaveLength(1);
    expect(within(why).getAllByRole("img")).toHaveLength(1);
    // Nothing of the sentence that was there before is left, and nothing is added to the new one.
    expect(why.textContent).toBe(`${RESULTS.reasonsTitle}${STRIP.most}${short}${SOURCE.button}`);
    // No style gives a sentence, or what holds it, a height of its own.
    const sized = STYLES.filter(
      (rule) => ["part", "runIn"].some((name) => isFor(rule.selector, name)) && (rule.sets.has("height") || rule.sets.has("min-height")),
    );
    expect(sized).toEqual([]);
  });
});

describe("how complete the data is", () => {
  const completeness = (at: number) => cards()[at]?.querySelector("[class*='completeness']") as HTMLElement;

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

  test("test_how_complete_is_said_directly_under_the_fit", () => {
    show({ ...first, opened: false });

    // It is what says how far to trust the fit, so it is read with the fit.
    for (const at of [0, 1, 4]) {
      expect(cards()[at]?.querySelector("header")?.nextElementSibling).toBe(completeness(at));
    }
    // A row says it where the fit rests on part of what counts, and is one line shorter where it does not.
    const partial = first.ranking.ranked.findIndex(
      (area, at) => at >= 5 && area.contributions.some((part) => !part.present),
    );
    expect(partial).toBeGreaterThanOrEqual(5);
    expect(cards()[partial]?.querySelector("header")?.nextElementSibling).toBe(completeness(partial));
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

  test("test_a_limit_that_could_not_be_tested_is_said_in_a_line", () => {
    show({ ...two, opened: false });

    expect(two.ranking.ranked[0]?.untested_filters).toEqual(["over_budget"]);
    expect(card(0).getByText(UNTESTED.over_budget)).toBeInTheDocument();
  });

  test("test_a_limit_that_could_not_be_tested_is_said_under_the_fit_and_not_in_small_print", () => {
    show({ ...two, opened: false });

    // It is the gravest thing a result can carry: the one limit the person called firm
    // was not applied. It is given the weight of the trade-off, and the same mark, and
    // it is in the answer: nobody has to open the working to find it.
    const line = card(0).getByText(UNTESTED.over_budget);
    expect(completeness(0).contains(line)).toBe(true);
    expect(line.closest("p")?.querySelector("[aria-hidden='true']")).not.toBeNull();
    const rules = STYLES.filter((rule) => isFor(rule.selector, "untested"));
    expect(rules.map((rule) => rule.sets.get("color")).filter(Boolean)).toEqual(["var(--tradeoff)"]);
    // Whatever the size of what is around it, it is the size of the body of the page.
    expect(rules.map((rule) => rule.sets.get("font-size")).filter(Boolean)).toEqual(["var(--size-body)"]);
  });

  test("test_a_row_says_how_complete_it_is_in_one_line", () => {
    show({ ...first, opened: false });
    const at = first.ranking.ranked.findIndex(
      (area, place) => place >= 5 && area.contributions.some((part) => !part.present),
    );

    expect(card(at).getByText(COMPLETENESS.some(9, 10))).toBeInTheDocument();
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
    for (const [at, area] of estimated.ranking.ranked.slice(0, 5).entries()) {
      const [leg] = area.legs;
      if (!leg?.estimate) throw new Error("the recorded journey was not estimated");
      bands.add(leg.estimate);
      const row = journeys(at).getAllByRole("row")[1] as HTMLElement;
      const [how, long, limit] = within(row).getAllByRole("cell").map(said);

      expect(leg.status).toBe("estimated");
      expect(how).toBe("Public transport");
      // The band in words, and that it is an estimate. No time, typical or missed.
      expect(long).toBe(`${JOURNEYS.estimated[leg.estimate]}. ${JOURNEYS.estimatedFrom}`);
      expect([leg.minutes, leg.minutes_typical, leg.minutes_just_missed]).toEqual([null, null, null]);
      // The limit is said, and the journey is not said to be within it or over it.
      expect(limit).toBe("30 minutes Source");
      expect(journeys(at).queryByText(JOURNEYS.within)).toBeNull();
      expect(journeys(at).queryByText(JOURNEYS.over)).toBeNull();
      expect(journeys(at).queryByText(JOURNEYS.missing)).toBeNull();
    }
    expect(bands.size).toBeGreaterThan(0);
  });

  test.each(["likely_within", "borderline", "likely_beyond"] as const)(
    "test_each_band_of_an_estimate_is_said_in_the_words_its_fact_says_it_in: %s",
    (band) => {
      const recorded = estimated.ranking.ranked.find((area) => area.legs[0]?.estimate === band);
      if (!recorded) throw new Error(`no recorded journey is ${band}`);
      // The comparison of the same search cites a fact of each band.
      const fact = recordedAnswer("compare", "estimate/compare").body.data.facts.find(
        (one) => one.template === "travel_estimated" && one.slots.band === band,
      );
      if (!fact) throw new Error(`no recorded fact of a journey that is ${band}`);
      show({ ...estimated, ranking: { ...estimated.ranking, ranked: [recorded] } });

      // The words are the API's own: the website keeps them for a journey whose fact is not in hand.
      expect(journeys(0).getByText(JOURNEYS.estimated[band])).toBeInTheDocument();
      expect(fact.slots.verdict).toBe(JOURNEYS.estimated[band]);
      expect(fact.slots.estimated).toBe(JOURNEYS.estimatedFrom);
      expect(said(journeys(0).getAllByRole("row")[1])).toContain(JOURNEYS.estimatedFrom);
    },
  );

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
    expect(JOURNEYS.usesOne("x")).toMatch(/Settings/);
  });

  test("test_when_the_average_counts_the_line_says_so", () => {
    show({ ranking: { ...two.ranking, spec: { ...two.ranking.spec, commute_combine: "mean" } } });

    const part = card(0).getByRole("heading", { name: JOURNEYS.title }).parentElement as HTMLElement;
    expect(within(part).getByText(JOURNEYS.usesMean)).toBeInTheDocument();
    expect(within(part).queryByText(/does worst/)).toBeNull();
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
    expect(gorsebeck.explanations[0]?.trade_off?.text).toContain("28 minutes over the 35 you set");
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

  test("test_journeys_that_do_not_count_because_none_has_a_time_say_so_directly_under_the_fit", () => {
    show({ ...two, ranking: noneKnown(two.ranking), opened: false });

    const under = cards()[0]?.querySelector("header")?.nextElementSibling as HTMLElement;
    const line = within(under).getByText(JOURNEYS.notCounted(2));
    // It has the weight of the trade-off, and the same mark: it says how far to trust the fit.
    expect(line.closest("p")?.querySelector("[aria-hidden='true']")).not.toBeNull();
    expect(line.closest("p")?.className.includes("untested")).toBe(true);
  });

  test("test_journeys_that_do_not_count_are_not_said_to_feed_the_fit_under_their_table", () => {
    show({ ...two, ranking: noneKnown(two.ranking) });

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
    show({ ...first, ranking: noneKnown(first.ranking), opened: false });

    const under = cards()[0]?.querySelector("header")?.nextElementSibling as HTMLElement;
    expect(within(under).getByText(JOURNEYS.notCounted(1))).toBeInTheDocument();
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
    expect(table.getAllByRole("rowheader").map((header) => header.textContent)).toEqual([
      "Quiet streets",
      BREAKDOWN.journey,
      BREAKDOWN.budget,
      "Leafy",
      "Modelled annual mean nitrogen dioxide",
      "Straight-line distance to the nearest way in to a station",
      "Share of residents exposed to 55 dB or more of transport noise",
      "Lines within a 10-minute walk",
      "Straight-line distance to the nearest marked way into a park of 2 ha or more",
      "Straight-line distance to the nearest town centre boundary",
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
    expect(table).toHaveTextContent("quieter than 60% of the 20 areas compared in this release");
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
    const walk = rows.find((row) =>
      within(row).queryByRole("rowheader", { name: "Straight-line distance to the nearest way in to a station" }),
    );
    const fact = profile("farrowmere").facts.find((one) => one.fact_id === "syn-n0006/feature/station_walk");
    const says = within(walk as HTMLElement).getAllByRole("cell").at(-1) as HTMLElement;

    expect(within(says).getByText(FACT_COLUMNS.value).nextElementSibling).toHaveTextContent(fact?.slots.value ?? "none");
    expect(within(says).getByText(FACT_COLUMNS.standing).nextElementSibling).toHaveTextContent(
      fact?.slots.standing ?? "none",
    );
    await user.click(within(says).getByRole("button", { name: /^Source for How the fit is worked out: Straight-line/ }));
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
