/**
 * What a results page holds before anything is opened. docs/design/web.md,
 * section 4.1, gives the heights it is held to: three screens of a desktop and
 * five of a phone, with the first result begun on the first.
 *
 * jsdom lays nothing out, so no test here measures a height. The heights were
 * measured in a browser, and are in section 4.1 with the searches they were
 * measured of. What this holds is what they depend on: how many results, how
 * many lines of each, and that everything else is closed. A change that draws
 * more than this before anything is pressed fails here, and is to be measured
 * again before the count is raised.
 */

import { screen, within } from "@testing-library/react";

import { SHOWN_AT_FIRST as CHIPS_AT_FIRST } from "@/components/ChipRow/ChipRow";
import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { OPENS_AT_FIRST } from "@/components/SettingsPanel/look";
import { ON_THE_SHELF } from "@/components/Shelf/Shelf";
import { HELPERS } from "@/content/helpers";
import { TABLE } from "@/content/map";
import { COMPARE } from "@/content/compare";
import { CHIPS, EXAMPLES_SHOWN, PROMPT, RESULTS, SHELF, TENURE_CHOICE } from "@/content/search";
import { KIND_OF_SEARCH, SETTINGS } from "@/content/settings";
import { SHARE } from "@/content/share";
import { TOWN } from "@/content/town";
import { REFINE, WAYS } from "@/content/ways";
import { recordedAnswer } from "@/lib/api/recorded";

import { setOnline, standInApi } from "../support/api";
import {
  areas,
  helper,
  helpers,
  meta,
  openSearch,
  panelOf,
  promptBox,
  results,
  search,
  settingsAt,
  settled,
  tabOf,
  theSettings,
  theSettingsIfAny,
  way,
  ways,
  whatRefines,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

/** Everything a person can press, type in or move. */
const CONTROLS = "a[href], button, input, select, textarea";
const controlsIn = (part: Element) => [...part.querySelectorAll<HTMLElement>(CONTROLS)];
/**
 * The press that shows the rest of the lines of a result, where the result holds more
 * than it has room for on a phone. It is drawn on a result as narrow as a phone and on no
 * other, by the width of the result: a test lays no style sheet, so it is on the page of
 * a test wherever the lines of a result fold. It names the list it shows.
 */
const foldsIn = (part: Element) =>
  controlsIn(part).filter((control) => {
    const shows = document.getElementById(control.getAttribute("aria-controls") ?? "");
    return shows?.tagName === "UL" && shows.closest("div[data-ends]") !== null && control.closest("article") !== null;
  });
/**
 * The same, of what is drawn. The way in that is not chosen is kept on the page as it was
 * left, and is not drawn: nothing of it is seen, and no key comes to it.
 */
const drawnIn = (part: Element) => controlsIn(part).filter((control) => control.closest("[hidden]") === null);
/** The groups of the settings, each by the bar that opens and closes it. */
const bars = () => [...theSettings().querySelectorAll<HTMLElement>("button[data-rest][aria-expanded]")];
const isOpen = (bar: HTMLElement) => bar.getAttribute("aria-expanded") === "true";
const main = () => screen.getByRole("main");
const nameOf = (areaId: string | undefined) => areas.find((area) => area.area_id === areaId)?.name ?? "";
const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", `interpret-${scenario}`).request.body as { text: string }).text;

/**
 * The ways on of a result, by where each stands: the way to compare in its heading, after
 * its name, and its working and the areas like it at its foot.
 */
function waysOnOf(result: HTMLElement, name: string) {
  const compare = within(result).getByRole("button", { name: COMPARE.addNamed(name) });
  const foot = [
    within(result).getByRole("button", { name: RESULTS.workingOf(name) }),
    within(result).getByRole("link", { name: RESULTS.moreLikeOf(name) }),
  ];
  return {
    compare: [compare.closest("header") !== null, compare.closest("h3") === null, compare.textContent],
    foot: foot.map((way) => [way.closest("header") === null, way.textContent]),
  };
}
/** Where each way on of a result stands, and what is seen of it. */
const WAYS_ON = {
  compare: [true, true, COMPARE.addShort],
  foot: [
    [true, RESULTS.showWorking],
    [true, RESULTS.moreLike],
  ],
};

/** The most controls a results page holds before anything is opened, the map apart. */
const MOST_ON_A_PAGE = 61;

/** The searches the heights were measured of: a sentence of each kind, as it was recorded. */
const SEARCHES = ["first", "buyer-family", "nights-out", "scale", "two-journeys", "by-the-river"] as const;

const searching = (scenario: string) =>
  standInApi()
    .on("interpret", `interpret-${scenario}`)
    .on("rank", `rank-${scenario}`)
    .on("explain_top", `explanations-${scenario}`)
    .on("search_places", "places-search");

async function searched(scenario: string) {
  const opened = await openSearch(searching(scenario));
  await search(opened.user, sentenceOf(scenario));
  return opened;
}

beforeEach(() => setOnline(true));

describe("the page before a search, before anything is opened", () => {
  const namesOf = (part: Element) =>
    controlsIn(part).map((control) => control.getAttribute("aria-label") ?? control.textContent?.trim() ?? "");

  test("test_it_holds_two_ways_in_the_box_and_one_line_of_two_helpers_and_nothing_that_either_opens", async () => {
    await openSearch();

    const names = namesOf(main());
    expect(names.filter((name) => name === PROMPT.submit)).toHaveLength(1);
    // Two ways in, as two tabs. The first is chosen, and the box is in it.
    expect(namesOf(ways())).toEqual([WAYS.quick, WAYS.deep]);
    expect([tabOf("quick"), tabOf("deep")].map((tab) => tab.getAttribute("aria-selected"))).toEqual(["true", "false"]);
    expect(panelOf("quick")).toContainElement(promptBox());
    // Two helpers, and no more: what else a quick search can begin from is behind one of them.
    expect(namesOf(helpers())).toEqual([HELPERS.example, HELPERS.word]);
    // Nothing of the second way is drawn until it is chosen: no setting, and no button that ranks by them.
    expect(controlsIn(panelOf("deep"))).toEqual([]);
    expect(theSettingsIfAny()).toBeNull();
    for (const name of [SETTINGS.title, SETTINGS.rank, REFINE.label]) expect(names).not.toContain(name);
    expect(names).toContain(TABLE.title);
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(main().querySelectorAll("input")).toHaveLength(0);
    // The link that skips to the map, the two tabs, the box and Search, the two helpers,
    // the link that skips the map and the way to the table: nine. It was one more while a
    // button stood by Burro. Nothing leads to how words are handled from here: the foot of
    // every page does. Here there is no map, so its controls are not counted.
    // Measured in a browser on 2026-09-26: at 1440 by 900 every one of them is on the first
    // screen, and the line of helpers stands from 747 to 791.
    expect(names.length).toBeLessThanOrEqual(9);
    expect(main().querySelectorAll("a[href^='/methods']")).toHaveLength(0);
  });

  test("test_a_helper_opens_no_more_than_stood_open_on_the_first_screen", async () => {
    const { user } = await openSearch();
    const closed = drawnIn(main()).length;
    const opens = async (which: "example" | "word") => {
      await helper(user, which);
      return drawnIn(main()).length - closed;
    };

    expect(await opens("example")).toBe(EXAMPLES_SHOWN);
    // Seven words of the shelf and the way to the rest.
    expect(await opens("word")).toBe(ON_THE_SHELF + 1);
    expect(within(screen.getByRole("region", { name: SHELF.title })).getAllByRole("button")).toHaveLength(ON_THE_SHELF + 1);
  });

  test("test_the_second_way_in_holds_what_it_asks_first_the_settings_with_two_groups_open_and_the_button_that_ranks", async () => {
    const { user } = await openSearch();
    await way(user, "deep");
    const deep = panelOf("deep");

    // Nothing of the first way is drawn while the second is chosen. It is kept on the page
    // as it was left, the box with it, for when it is chosen again.
    expect(drawnIn(panelOf("quick"))).toEqual([]);
    expect(panelOf("quick").querySelectorAll("textarea")).toHaveLength(1);
    // The settings, which stand open under no button and ask everything the way asks:
    // renting, buying or visiting is the first thing in them. Then the one button that ranks
    // by them, and after it the field that finds an area by its name, which is no part of a
    // search.
    expect(deep).toContainElement(theSettings());
    expect(whatRefines()).toBeNull();
    const outside = drawnIn(deep).filter((control) => !theSettings().contains(control));
    // The field opens no list, so it is a plain field of text.
    expect(outside.map((control) => control.getAttribute("role") ?? control.getAttribute("type"))).toEqual([
      "button",
      "text",
    ]);
    expect(outside[0]?.textContent).toBe(SETTINGS.rank);
    // Three choices and no other: the founder asked for a visit beside renting and buying.
    // They are what the settings ask first, after the bar of the group that holds them.
    const kinds = within(theSettings()).getAllByRole("radio");
    const named = [TENURE_CHOICE.rent, TENURE_CHOICE.buy, KIND_OF_SEARCH.visit].map((name) =>
      within(theSettings()).getByRole("radio", { name }),
    );
    expect(kinds).toHaveLength(named.length);
    expect(kinds.map((one, at) => one === named[at])).toEqual([true, true, true]);
    expect(drawnIn(theSettings()).filter((control) => !bars().includes(control))[0]).toBe(kinds[0]);
    // One bar for the money, one for the journeys, one for each family, one for the brands,
    // and two that stand apart. The first two stand open, so that it is seen that a group
    // opens and closes, and every other is closed.
    expect(bars()).toHaveLength(meta.data.families.length + 5);
    expect(bars().map(isOpen)).toEqual(bars().map((_, at) => at < 2));
    expect(bars().slice(0, 2).map((bar) => bar.getAttribute("aria-label") ?? bar.querySelector("[id$='-name']")?.textContent)).toEqual([
      SETTINGS.money,
      SETTINGS.journeys,
    ]);
    // The ten bars, the three choices, and what the money holds: the sum with its two steps
    // and what clears it, the kind of home, whether the budget is firm, and how much it
    // counts. The journeys hold the field that finds a place, and nothing more until one is
    // named. They were 23 while the choices were two. Measured in a browser on 2026-09-26,
    // with the second way chosen and the three choices: the page was 2,689 px high at 1440
    // by 900 and 3,182 at 390 by 844. It had been 2,665 and 3,394. The three stand in one
    // row, each 44 px high, so the third is a control more and no line more.
    expect(drawnIn(theSettings()).length).toBeLessThanOrEqual(24);
    expect(drawnIn(deep).length).toBeLessThanOrEqual(27);
  });

  test("test_nothing_is_open_and_nothing_is_ranked", async () => {
    await openSearch();

    expect([...main().querySelectorAll("[aria-expanded='true']")]).toEqual([]);
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    expect(screen.queryByRole("region", { name: CHIPS.label })).toBeNull();
    expect(main().querySelectorAll("table, article, details[open]")).toHaveLength(0);
  });
});

describe("a results page, before anything is opened", () => {
  test.each(SEARCHES)("test_ten_results_at_most_five_of_them_cards_and_nothing_open: %s", async (scenario) => {
    await searched(scenario);
    const ranked = recordedAnswer("rank", `rank-${scenario}`).body.data.ranked;
    const shown = results();

    expect(SHOWN_AT_FIRST).toBe(10);
    expect(shown).toHaveLength(Math.min(SHOWN_AT_FIRST, ranked.length));
    // A card says what its area gives up, and a row does not. No result says why it fits:
    // that is in its working.
    expect(shown.filter((one) => within(one).queryByRole("heading", { name: RESULTS.tradeOffTitle }))).toHaveLength(
      Math.min(5, ranked.length),
    );
    expect(shown.filter((one) => within(one).queryByRole("heading", { name: RESULTS.reasonsTitle }))).toEqual([]);
    // Everything that opens is closed: the working of each result, the settings, sharing, the table.
    expect([...main().querySelectorAll("[aria-expanded='true']")]).toEqual([]);
    for (const name of [REFINE.label, SHARE.open, TABLE.title]) {
      expect(screen.getByRole("button", { name })).toHaveAttribute("aria-expanded", "false");
    }
    // The settings are one fold, and nothing of them is drawn until it is pressed. The two
    // ways in were for beginning: once a search is open there is no tab.
    expect(theSettingsIfAny()).toBeNull();
    expect(screen.queryAllByRole("tab")).toEqual([]);
    expect(main().querySelectorAll("table, svg, dl, details[open]")).toHaveLength(0);
    expect(document.querySelectorAll(".skeleton")).toHaveLength(0);
  });

  test.each(SEARCHES)("test_a_card_is_a_name_that_leads_to_its_page_the_way_to_compare_a_line_for_each_thing_asked_for_the_trade_off_and_two_ways_on: %s", async (scenario) => {
    // The founder, who had walked the website three times: "Again, we don't need to over
    // complicate and bloat with too much info." Measured in a browser after a plain search,
    // at 1440 by 900: a card was 661.5 px high and the page 4,640, and with no more on a
    // card than this a card is 432 px high and the page 3,372.
    await searched(scenario);
    const ranking = recordedAnswer("rank", `rank-${scenario}`).body.data;
    const reasons = recordedAnswer("explain_top", `explanations-${scenario}`).body.data.explanations;

    results()
      .slice(0, 5)
      .forEach((card, at) => {
        const area = ranking.ranked[at];
        const given = reasons.find((one) => one.area_id === area?.area_id);
        const sentences = [...card.querySelectorAll("p")].filter((line) =>
          [...(given?.reasons ?? []), given?.trade_off, ...(given?.missing ?? []), given?.orientation]
            .map((sentence) => sentence?.text)
            .includes(line.textContent ?? ""),
        );
        // The trade-off, where the API gave one. Every other sentence waits in the working.
        expect(sentences.map((line) => line.textContent)).toEqual([given?.trade_off?.text].filter((text) => text !== undefined));
        expect(within(card).getAllByRole("heading").map((heading) => heading.textContent)).toEqual([
          expect.any(String),
          RESULTS.tradeOffTitle,
        ]);
        // A line for each thing that was asked for: a vibe, a measure, a journey and the
        // budget. Where nothing was, a line for each of the vibes the API chose, which are
        // two at the most. A thing that was asked for and has no figure says so on its line.
        const { spec } = ranking;
        const counts = (one: { readonly weight: number }) => one.weight > 0;
        const things =
          spec.tags.filter(counts).length +
          spec.weights.filter((weight) => weight.provenance !== "default" && counts(weight)).length +
          spec.commutes.length +
          (spec.budget.amount === null || spec.tenure === "visit" ? 0 : 1);
        const asked = area?.strip.filter((mark) => mark.asked).length ?? 0;
        const lines = within(card).queryAllByRole("listitem");
        const lacked = lines.filter((line) => line.querySelector("[data-known='none']") !== null);
        expect(things).toBeGreaterThan(0);
        expect(lines.length).toBe(things);
        expect(lacked.length).toBeLessThanOrEqual(
          (area?.contributions.filter((part) => !part.present).length ?? 0) + (area?.legs.filter((leg) => leg.status === "missing").length ?? 0),
        );
        expect(area?.strip.length ?? 0).toBeLessThanOrEqual(asked + 2);
        // Where its lines take more rows than a narrow result has room for, one press
        // shows the rest of them, and no result holds two.
        const folds = foldsIn(card);
        expect(folds.length).toBeLessThanOrEqual(1);
        for (const fold of folds) expect(fold).toHaveAttribute("aria-expanded", "false");
        // Its pictures are the gauges of its lines, and one more: the town of its area,
        // which stands in its heading and says whose it is.
        const pictures = within(card).queryAllByRole("img");
        const towns = pictures.filter((picture) => picture.closest("figure") !== null);
        expect(towns.map((town) => town.closest("header") !== null)).toEqual([true]);
        expect(towns[0]?.getAttribute("aria-label")?.startsWith(`${TOWN.nameOf(nameOf(area?.area_id))}.`)).toBe(true);
        const gauges = pictures.filter((picture) => !towns.includes(picture));
        expect(gauges.every((gauge) => gauge.closest("li") !== null)).toBe(true);
        expect(gauges.length).toBeLessThanOrEqual(lines.length);
        // A town is a drawing and takes no press: it adds no control, no heading and no line to a card.
        expect(towns[0]?.closest("figure")?.querySelectorAll(`${CONTROLS}, [tabindex], h1, h2, h3, h4, p`)).toHaveLength(0);
        // Four things to press and no more. The name, which leads to the page of the area.
        // The way to compare, which stands in the heading of every result, since comparing
        // is a headline. Its working and the areas like it, at its foot. No line opens, and
        // no key of a source stands on a card: each is in its working.
        expect(waysOnOf(card, nameOf(area?.area_id))).toEqual(WAYS_ON);
        expect(controlsIn(card).filter((control) => /^Source/.test(control.getAttribute("aria-label") ?? control.textContent ?? ""))).toEqual([]);
        expect(controlsIn(card).filter((control) => control.closest("h3") !== null).length).toBe(1);
        expect(within(card).queryAllByRole("list").flatMap((list) => controlsIn(list))).toEqual([]);
        expect(controlsIn(card).length).toBe(4 + folds.length);
      });
  });

  test.each(SEARCHES)("test_a_row_is_a_name_that_leads_to_its_page_the_way_to_compare_its_lines_and_two_ways_on_and_holds_no_sentence: %s", async (scenario) => {
    await searched(scenario);
    const ranking = recordedAnswer("rank", `rank-${scenario}`).body.data;

    for (const [at, row] of results().slice(5).entries()) {
      const folds = foldsIn(row);
      expect(within(row).getAllByRole("heading").length).toBe(1);
      // The name, the way to compare in its heading, and the two ways on at its foot: the
      // tenth result can be compared as the first can. And the press that shows the rest
      // of its lines, where a narrow result has no room for all of them.
      expect(folds.length).toBeLessThanOrEqual(1);
      expect(controlsIn(row).length).toBe(4 + folds.length);
      expect(controlsIn(row)[0]?.closest("h3")).not.toBeNull();
      expect(waysOnOf(row, nameOf(ranking.ranked[at + 5]?.area_id))).toEqual(WAYS_ON);
      // The rank, what stands beside the name, and the fit, with the two words that say it
      // is not whole where it is not. A row holds no other paragraph: what its fit is
      // based on is in its working.
      expect(row.querySelectorAll("header p")).toHaveLength(3);
      // What holds the press is the one paragraph more, and holds no sentence.
      const beside = [...row.querySelectorAll("p")].filter((one) => one.closest("header") === null);
      expect(beside.map((one) => controlsIn(one))).toEqual(folds.map((fold) => [fold]));
    }
  });

  test.each(SEARCHES)("test_what_was_understood_is_said_in_short_six_chips_at_most_and_nothing_of_the_settings_nobody_chose: %s", async (scenario) => {
    await searched(scenario);
    const chips = screen.getByRole("region", { name: CHIPS.label });
    const drawn = within(chips).getAllByRole("listitem");
    const spec = recordedAnswer("rank", `rank-${scenario}`).body.data.spec;

    expect(CHIPS_AT_FIRST).toBe(6);
    // Six of what was asked for, and no more. The settings nobody chose have no chip: a
    // usual setting moves no area, so a count of them told a person nothing. Each stands
    // with its value under the fold of the settings.
    expect(drawn.length).toBeLessThanOrEqual(CHIPS_AT_FIRST);
    expect(drawn.filter((chip) => /usual settings/i.test(chip.textContent ?? ""))).toEqual([]);
    expect(spec.weights.some((weight) => weight.provenance === "default")).toBe(true);
    // Every vibe that was asked for is among them: none waits behind a budget or a workplace.
    expect(spec.tags.length).toBeLessThanOrEqual(CHIPS_AT_FIRST);
    expect(drawn.slice(0, spec.tags.length).every((chip) => chip.querySelector("[data-main]") !== null)).toBe(true);
    expect(chips.querySelector("[data-out]")).toHaveAttribute("data-out", "false");
    // What explains the chips waits until the row is opened out.
    expect(within(chips).queryByText(CHIPS.assumedHint)).toBeNull();
  });

  test.each(SEARCHES)("test_between_the_box_and_the_first_result_stand_few_controls: %s", async (scenario) => {
    await searched(scenario);
    const [first] = results();
    const before = controlsIn(main()).filter(
      (control) =>
        Boolean(promptBox().compareDocumentPosition(control) & Node.DOCUMENT_POSITION_FOLLOWING) &&
        Boolean(control.compareDocumentPosition(first as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING),
    );

    // Start again and Search. The chips, six at most, each with its way out, and a scale
    // with the way to its other end. Then the fold of the settings, closed, which is the last
    // of them. No more: sharing and the map stand after the first result. With six chips
    // they are thirteen, as they were while the settings nobody chose had a chip, and the
    // way to the settings stood after the first result.
    expect(before.length).toBeLessThanOrEqual(13);
    expect(before.at(-1)).toBe(whatRefines());
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
  });

  test.each(SEARCHES)("test_the_whole_page_holds_no_more_controls_than_was_measured: %s", async (scenario) => {
    await searched(scenario);

    // Here there is no map, so its pins and its controls are not counted. It was 80 at most.
    // The name of each of the ten results became a link to its page, and every chip of what
    // was asked for came to be drawn, where three were: 86 was the most the recorded
    // searches held. A result holds four controls since, a card as a row: no line of it
    // opens, and no key of a source stands on it.
    // The press that shows the rest of the lines of a result is drawn on a narrow result
    // alone, and is counted apart: a desk draws none, and a phone one to a result at the most.
    const folds = foldsIn(main());
    expect(folds.length).toBeLessThanOrEqual(results().length);
    expect(controlsIn(main()).length - folds.length).toBeLessThanOrEqual(MOST_ON_A_PAGE);
    expect(results().flatMap((result) => controlsIn(result))).toHaveLength(results().length * 4 + folds.length);
  });

  test.each(SEARCHES)("test_the_settings_open_with_a_couple_of_groups_open_and_every_other_closed: %s", async (scenario) => {
    const { user } = await searched(scenario);

    await settingsAt(user);

    expect(whatRefines()).toHaveAttribute("aria-expanded", "true");
    // One bar for the money, one for the journeys, one for each family, one for the brands,
    // and two that stand apart.
    expect(bars()).toHaveLength(meta.data.families.length + 5);
    // A person has the answer before them and came to change one thing. How many groups
    // stand open as the settings open is the settings' to choose, in one line of their
    // look: none, a couple, or every one that holds something asked for. With two open the
    // settings of a plain search were 2,404 px high on a desk, and the first result stood
    // that far under the fold.
    const open = bars().filter(isOpen);
    if (OPENS_AT_FIRST === "none") expect(open).toHaveLength(0);
    if (OPENS_AT_FIRST === "a-couple") expect(open).toHaveLength(2);
    if (OPENS_AT_FIRST === "all-asked") expect(open.length).toBeGreaterThan(0);
    // A group that is closed draws its bar and nothing of what it holds. With them, in
    // sight whichever group is open, stand renting or buying and no more.
    const opened = open.map((bar) => document.getElementById(bar.getAttribute("aria-controls") ?? "") as HTMLElement);
    const held = opened.flatMap((group) => drawnIn(group));
    const beside = drawnIn(theSettings()).filter((control) => !bars().includes(control) && !held.includes(control));
    expect(beside.filter((control) => control.getAttribute("type") !== "radio")).toEqual([]);
    expect(drawnIn(theSettings())).toHaveLength(bars().length + held.length + beside.length);
  });

  test("test_the_settings_of_a_plain_search_hold_no_more_controls_as_they_open_than_was_measured_and_their_bars_with_every_group_closed", async () => {
    const { user } = await searched("first");

    await settingsAt(user);

    // Measured in a browser on 2026-09-26, as the settings of this search opened with the
    // money and the journeys open, which a plain search asked for both of: 39 controls,
    // 2,404 px high at 1440 by 900 and 2,768 at 390 by 844. With every group that holds
    // something asked for open, four stood open and the settings drew 79. With none open
    // they hold their bars, and renting or buying. On a phone they open under the first
    // result, which stays where it stood.
    const open = bars()
      .filter(isOpen)
      .map((bar) => bar.querySelector("[id$='-name']")?.textContent);
    const MOST = { none: 0, "a-couple": 2, "all-asked": 4 } as const;
    const CONTROLS_AT_MOST = { none: 14, "a-couple": 41, "all-asked": 81 } as const;
    expect(open).toHaveLength(MOST[OPENS_AT_FIRST]);
    if (OPENS_AT_FIRST !== "none") expect(open.slice(0, 2)).toEqual([SETTINGS.money, SETTINGS.journeys]);
    expect(drawnIn(theSettings()).length).toBeLessThanOrEqual(CONTROLS_AT_MOST[OPENS_AT_FIRST]);
    // With every group closed they hold their bars, and renting or buying, and no more.
    for (const bar of bars().filter(isOpen)) await user.click(bar);
    expect(bars().map(isOpen)).toEqual(bars().map(() => false));
    const beside = drawnIn(theSettings()).filter((control) => !bars().includes(control));
    expect(beside.filter((control) => control.getAttribute("type") !== "radio")).toEqual([]);
    expect(bars()).toHaveLength(meta.data.families.length + 5);
    expect(drawnIn(theSettings()).length).toBeLessThanOrEqual(14);
  });

  test("test_of_what_the_reader_noticed_nothing_is_drawn_to_be_chosen_and_the_answer_holds_what_any_answer_holds", async () => {
    // Four offers that needed a choice were drawn at most, each a line of three buttons,
    // and the rest waited behind "Show all". Burro asks nothing now: what he noticed he
    // took, and the page holds what it holds after any search.
    //
    // It is a sentence of which the service says that nothing waits for a person: of one
    // whose every offer waits, the page takes nothing and ranks nothing, and holds no answer.
    const noticed = recordedAnswer("interpret", "interpret-suggest-newcomer").body.data.suggestions;
    const { user, api } = await openSearch(
      standInApi()
        .on("interpret", "interpret-suggest-newcomer")
        .on("rank", "rank-first")
        .on("explain_top", "explanations-first"),
    );
    await user.type(promptBox(), sentenceOf("suggest-newcomer"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();

    expect(noticed.length).toBeGreaterThan(4);
    expect(noticed.filter((offer) => offer.only_by_choice)).toEqual([]);
    // Each thing that was noticed was taken, by the way the service says one press may
    // take, and what was sent to be ranked holds the edits of those ways and no other.
    const KINDS = ["budget_ops", "commute_ops", "weight_ops", "tag_ops", "area_ops", "setting_ops"] as const;
    const ways = noticed.map((offer) => offer.choices.find((way) => way.id === offer.add_all));
    const sent = (api.lastCallTo("rank").body as { operations: Record<(typeof KINDS)[number], readonly unknown[]> }).operations;
    expect(ways.filter((way) => way === undefined)).toEqual([]);
    expect(KINDS.map((kind) => [kind, sent[kind].length])).toEqual(
      KINDS.map((kind) => [kind, ways.reduce((edits, way) => edits + (way?.operations[kind].length ?? 0), 0)]),
    );
    expect(api.callsTo("rank")).toHaveLength(1);
    expect(screen.queryByRole("region", { name: "Choose what to add" })).toBeNull();
    expect(main().querySelectorAll("[data-way]")).toHaveLength(0);
    expect(results().length).toBeGreaterThan(0);
    // Between the box and the first result: Start again and Search, the chips with their
    // ways out, the way to see the words that were not read, and the fold of the settings.
    const [first] = results();
    const before = controlsIn(main()).filter(
      (control) =>
        Boolean(promptBox().compareDocumentPosition(control) & Node.DOCUMENT_POSITION_FOLLOWING) &&
        Boolean(control.compareDocumentPosition(first as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING),
    );
    expect(before.length).toBeLessThanOrEqual(14);
    expect(before.at(-1)).toBe(whatRefines());
    // The whole page holds what it holds after a plain search, and the way to see the
    // words that were not read. It held 91 at most while a result held more than four.
    expect(controlsIn(main()).length).toBeLessThanOrEqual(MOST_ON_A_PAGE + 1);
    expect(results().flatMap((result) => controlsIn(result))).toHaveLength(results().length * 4);
  });
});
