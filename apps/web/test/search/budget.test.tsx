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
import { ON_THE_SHELF } from "@/components/Shelf/Shelf";
import { inSight, SHOWN_AT_FIRST as SUGGESTIONS_AT_FIRST } from "@/components/Suggestions/Suggestions";
import { addedWithOthers } from "@/lib/search/suggestion";
import { TABLE } from "@/content/map";
import { CHIPS, PROMPT, RESULTS, SHELF, SUGGEST } from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { SHARE } from "@/content/share";
import { recordedAnswer } from "@/lib/api/recorded";

import { setOnline, standInApi } from "../support/api";
import { meta, openSearch, promptBox, results, search, settled } from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

/** Everything a person can press, type in or move. */
const CONTROLS = "a[href], button, input, select, textarea";
const controlsIn = (part: Element) => [...part.querySelectorAll<HTMLElement>(CONTROLS)];
const main = () => screen.getByRole("main");
const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", `interpret-${scenario}`).request.body as { text: string }).text;

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
  test("test_it_holds_the_box_the_shelf_the_choice_of_tenure_the_place_field_and_the_examples", async () => {
    await openSearch();

    const names = controlsIn(main()).map((control) => control.getAttribute("aria-label") ?? control.textContent?.trim() ?? "");
    const shelf = within(screen.getByRole("region", { name: SHELF.title }));
    // Seven words of the shelf and the way to the rest.
    expect(shelf.getAllByRole("button")).toHaveLength(ON_THE_SHELF + 1);
    expect(names.filter((name) => name === PROMPT.submit)).toHaveLength(1);
    expect(names).toContain(SETTINGS.title);
    expect(names).toContain(TABLE.title);
    // No more than thirty controls, the links that skip among them.
    expect(names.length).toBeLessThanOrEqual(30);
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
    expect(shown.filter((one) => within(one).queryByRole("heading", { name: RESULTS.reasonsTitle }))).toHaveLength(
      Math.min(5, ranked.length),
    );
    // Everything that opens is closed: the working of each result, the settings, sharing, the table.
    expect([...main().querySelectorAll("[aria-expanded='true']")]).toEqual([]);
    for (const name of [SETTINGS.title, SHARE.open, TABLE.title]) {
      expect(screen.getByRole("button", { name })).toHaveAttribute("aria-expanded", "false");
    }
    expect(main().querySelectorAll("table, svg, dl, details[open]")).toHaveLength(0);
    expect(document.querySelectorAll(".skeleton")).toHaveLength(0);
  });

  test.each(SEARCHES)("test_a_card_is_a_name_that_leads_to_its_page_a_strip_one_reason_the_trade_off_and_three_ways_on: %s", async (scenario) => {
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
        // One reason and the trade-off, where the API gave them. Every other sentence waits in the working.
        expect(sentences.map((line) => line.textContent)).toEqual(
          [given?.reasons[0]?.text, given?.trade_off?.text].filter((text) => text !== undefined),
        );
        expect(within(card).getAllByRole("heading").map((heading) => heading.textContent)).toEqual([
          expect.any(String),
          RESULTS.reasonsTitle,
          RESULTS.tradeOffTitle,
        ]);
        // The strip holds what the API chose for it: what was asked for, and two more at most.
        const asked = area?.strip.filter((mark) => mark.asked).length ?? 0;
        expect(within(card).queryAllByRole("img")).toHaveLength(area?.strip.length ?? 0);
        expect(area?.strip.length ?? 0).toBeLessThanOrEqual(asked + 2);
        // The name, which leads to the page of the area. The source of each sentence. Its
        // working, the areas like it, and the comparison. A mark of the strip opens its fact.
        const others = controlsIn(card).filter((control) => control.closest("ul") === null);
        expect(others.filter((control) => /^Source/.test(control.getAttribute("aria-label") ?? "")).length).toBe(
          sentences.length,
        );
        expect(others.filter((control) => control.closest("h3") !== null).length).toBe(1);
        expect(others.length).toBe(4 + sentences.length);
        expect(controlsIn(card).length).toBeLessThanOrEqual(6 + (area?.strip.length ?? 0));
      });
  });

  test.each(SEARCHES)("test_a_row_is_a_name_that_leads_to_its_page_a_strip_and_three_ways_on_and_holds_no_sentence: %s", async (scenario) => {
    await searched(scenario);

    for (const row of results().slice(5)) {
      expect(within(row).getAllByRole("heading").length).toBe(1);
      // The name, and the three ways on.
      expect(controlsIn(row).length).toBe(4);
      expect(controlsIn(row)[0]?.closest("h3")).not.toBeNull();
      // What the fit rests on, where that is not everything, and a firm limit that was not tested.
      expect(row.querySelectorAll("p").length).toBeLessThanOrEqual(5);
      expect(row.querySelectorAll("header p")).toHaveLength(2);
    }
  });

  test.each(SEARCHES)("test_what_was_understood_is_said_in_short_six_chips_at_most_and_the_usual_settings: %s", async (scenario) => {
    await searched(scenario);
    const chips = screen.getByRole("region", { name: CHIPS.label });
    const drawn = within(chips).getAllByRole("listitem");
    const spec = recordedAnswer("rank", `rank-${scenario}`).body.data.spec;

    expect(CHIPS_AT_FIRST).toBe(6);
    // Six of what was asked for, and then the usual settings, which are not counted.
    expect(drawn.length).toBeLessThanOrEqual(CHIPS_AT_FIRST + 1);
    expect(drawn.filter((chip) => /^Usual settings/.test(chip.textContent ?? "")).length).toBeLessThanOrEqual(1);
    // Every vibe that was asked for is among them: none waits behind a budget or a workplace.
    expect(spec.tags.length).toBeLessThanOrEqual(CHIPS_AT_FIRST);
    expect(drawn.slice(0, spec.tags.length).every((chip) => chip.querySelector("[data-main]") !== null)).toBe(true);
    expect(chips.querySelector("[data-out]")).toHaveAttribute("data-out", "false");
    // What explains the chips waits until the row is opened out.
    expect(within(chips).queryByText(CHIPS.assumedHint)).toBeNull();
    expect(within(chips).queryByText(CHIPS.usualHint, { exact: false })).toBeNull();
  });

  test.each(SEARCHES)("test_between_the_box_and_the_first_result_stand_few_controls: %s", async (scenario) => {
    await searched(scenario);
    const [first] = results();
    const before = controlsIn(main()).filter(
      (control) =>
        Boolean(promptBox().compareDocumentPosition(control) & Node.DOCUMENT_POSITION_FOLLOWING) &&
        Boolean(control.compareDocumentPosition(first as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING),
    );

    // Start again and Search. The chips, six at most and each with its way out, and the usual
    // settings. No more: the settings, sharing and the map stand after the first result.
    expect(before.length).toBeLessThanOrEqual(13);
  });

  test.each(SEARCHES)("test_the_whole_page_holds_no_more_controls_than_was_measured: %s", async (scenario) => {
    await searched(scenario);

    // Here there is no map, so its pins and its controls are not counted. It was 80 at most.
    // The name of each of the ten results is now a link to its page, and every chip of what
    // was asked for is drawn, where three were: 88 is the most the recorded searches hold.
    expect(controlsIn(main()).length).toBeLessThanOrEqual(90);
  });

  test("test_the_settings_open_with_every_group_closed_hold_twelve_controls_at_most", async () => {
    const { user } = await searched("first");

    await user.click(screen.getByRole("button", { name: SETTINGS.title }));
    const settings = document.getElementById(
      screen.getByRole("button", { name: SETTINGS.title }).getAttribute("aria-controls") ?? "",
    ) as HTMLElement;

    expect(controlsIn(settings).length).toBeLessThanOrEqual(12);
    expect(controlsIn(settings).map((control) => control.getAttribute("aria-expanded"))).toEqual(
      controlsIn(settings).map(() => "false"),
    );
    // One group for the money, one for the journeys, one for each family, one for the brands, and
    // two that stand apart.
    expect(controlsIn(settings)).toHaveLength(meta.data.families.length + 5);
  });

  test("test_of_what_the_reader_noticed_four_things_that_need_a_choice_are_drawn_at_most", async () => {
    const { user } = await openSearch(standInApi().on("interpret", "interpret-suggest-many"));
    await user.type(promptBox(), sentenceOf("suggest-many"));
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await settled();
    const offered = within(screen.getByRole("region", { name: SUGGEST.title }));
    const noticed = recordedAnswer("interpret", "interpret-suggest-many").body.data.suggestions;
    const needsAChoice = noticed.map((one) => addedWithOthers(one) === null);

    expect(SUGGESTIONS_AT_FIRST).toBe(4);
    expect(noticed.length).toBeGreaterThan(SUGGESTIONS_AT_FIRST);
    // A thing that needs a choice is a line of three buttons, and four are drawn at most. A
    // thing there is one way to want is one button, and is always in sight: what waits behind
    // "Show all" is only what is a question. Measured in a browser on 2026-09-24.
    const drawn = inSight(noticed);
    expect(offered.getAllByRole("listitem")).toHaveLength(drawn.length);
    expect(drawn.filter((at) => needsAChoice[at]).length).toBeLessThanOrEqual(SUGGESTIONS_AT_FIRST);
    expect(noticed.filter((_, at) => !drawn.includes(at)).every((one) => addedWithOthers(one) === null)).toBe(true);
    // Nothing is ranked from what was noticed, so no result is drawn.
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
  });
});
