/**
 * Every state of the search page, as docs/design/web.md section 3 lists
 * them, against the answers recorded from the API.
 */

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";

import { MAP, TABLE } from "@/content/map";
import {
  CHIPS,
  CLARIFY,
  FILTERED,
  NOTHING_MATCHES,
  NOTICE,
  PLACE,
  PROMPT,
  REJECTED,
  REJECTED_LABEL,
  RESULTS,
  STATUS,
  TENURE_CHOICE,
  UNMET,
  UNMET_LABEL,
  UNRANKED,
} from "@/content/search";
import { BUDGET, JOURNEY, SETTINGS } from "@/content/settings";
import { BANNER } from "@/content/site";
import { recordedAnswer, recordedError, responseFrom } from "@/lib/api/recorded";
import type { Operations } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { setOnline, standInApi, withTheSpecSent } from "../support/api";
import { faultsIn } from "../support/axe";
import {
  areas,
  firstSearch,
  meta,
  openSearch,
  promptBox,
  resultList,
  results,
  search,
  settled,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const first = {
  read: recordedAnswer("interpret", "interpret-first").body.data,
  rank: recordedAnswer("rank", "rank-first").body.data,
  explain: recordedAnswer("explain_top", "explanations-first").body.data,
};
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";
/** The sentence a reading was recorded of, so that what is typed is what was answered. */
const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", scenario).request.body as { text: string }).text;
const status = () => screen.getAllByRole("status").map((line) => line.textContent ?? "");
const banner = () => screen.getByRole("region", { name: BANNER.label });
const settingsButton = () => screen.getByRole("button", { name: SETTINGS.title });
const settingsAreOpen = () => settingsButton().getAttribute("aria-expanded") === "true";

beforeEach(() => setOnline(true));
afterEach(() => jest.useRealTimers());

describe("empty: before anything is asked for", () => {
  test("test_the_page_opens_on_one_box_the_choice_of_tenure_a_place_search_and_every_area", async () => {
    const { api } = await openSearch();

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(promptBox()).toHaveValue("");
    expect(screen.getByRole("radio", { name: TENURE_CHOICE.rent })).toBeChecked();
    expect(screen.getByRole("combobox", { name: PLACE.label })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /./ }).map((button) => button.textContent)).toEqual(
      expect.arrayContaining([PROMPT.submit]),
    );
    // Every area of the release is there by name, as a link to its page.
    for (const area of areas) {
      expect(screen.getAllByRole("link", { name: area.name })[0]).toHaveAttribute(
        "href",
        `/synthetic/${area.slug}`,
      );
    }
    expect(settingsAreOpen()).toBe(false);
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    // Nothing is sent until something is asked for, but the boundaries for the map.
    expect(api.calls.map((call) => call.operation)).toEqual(["get_geometry"]);
  });

  test("test_the_synthetic_banner_is_present_in_every_state", async () => {
    const { user, api } = await openSearch();
    expect(banner()).toHaveTextContent(BANNER.text);

    await search(user);
    expect(banner()).toHaveTextContent(BANNER.text);

    api.on("rank", "rank-nothing-matches");
    await user.click(screen.getAllByRole("button", { name: `${CHIPS.remove}: Leafy` })[0] as HTMLElement);
    await settled();
    expect(banner()).toHaveTextContent(BANNER.text);

    api.on("rank", "error-internal");
    await user.click(screen.getByRole("button", { name: NOTHING_MATCHES.budgetFlexible }));
    await screen.findByRole("alert");
    expect(banner()).toHaveTextContent(BANNER.text);
    expect(within(banner()).queryAllByRole("button")).toEqual([]);
  });

  test("test_an_example_fills_the_box_and_sends_nothing", async () => {
    const { user, api } = await openSearch();
    api.calls.length = 0;

    await user.click(screen.getByRole("button", { name: /^Buying a terraced house/ }));

    expect(promptBox().value).toMatch(/^Buying a terraced house/);
    expect(promptBox()).toHaveFocus();
    expect(api.calls).toEqual([]);
  });

  test("test_rent_or_buy_swaps_the_defaults_and_sends_nothing", async () => {
    const { user, api } = await openSearch();
    api.calls.length = 0;

    await user.click(screen.getByRole("radio", { name: TENURE_CHOICE.buy }));

    expect(screen.getByRole("radio", { name: TENURE_CHOICE.buy })).toBeChecked();
    // Nothing has been understood yet: the chips are what a search starts from, and say so.
    const chips = within(screen.getByRole("region", { name: CHIPS.startLabel }));
    expect(chips.getByRole("button", { name: /^Buying/ })).toBeInTheDocument();
    expect(chips.getByRole("button", { name: /^Usual settings: 7/ })).toBeInTheDocument();
    expect(api.calls).toEqual([]);
  });

  test("test_the_settings_hold_the_defaults_and_can_be_ranked_by_hand", async () => {
    const { user, api } = await openSearch(standInApi().on("rank", "rank-default-rent").on("explain_top", "explanations-first"));

    await user.click(settingsButton());
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await settled();

    expect(api.callsTo("interpret")).toEqual([]);
    expect(api.lastCallTo("rank").body).toEqual({ spec: meta.data.defaults.rent, limit: 20 });
    expect(results().length).toBeGreaterThan(0);
  });

  test("test_the_empty_page_has_no_accessibility_fault", async () => {
    const { container } = await openSearch();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("interpreting: a sentence was sent", () => {
  test("test_the_page_says_it_is_reading_at_once_and_keeps_the_text_in_the_box", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);

    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(screen.getByRole("button", { name: PROMPT.reading })).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByRole("button", { name: PROMPT.stop })).toBeInTheDocument();
    expect(status()).toContain(STATUS.reading);
    expect(promptBox()).toHaveValue("leafy and quiet");
    // Skeletons hold the place of the chips and of five cards. They say nothing to a reader.
    expect(document.querySelectorAll(".skeleton").length).toBeGreaterThanOrEqual(8);
    expect(document.querySelector("[aria-busy='true']")).not.toBeNull();

    reading.release();
    await settled();
    expect(screen.getByRole("button", { name: PROMPT.submit })).not.toHaveAttribute("aria-disabled");
    expect(promptBox()).toHaveValue("leafy and quiet");
  });

  test("test_pressing_enter_sends_and_shift_enter_does_not", async () => {
    const { user, api } = await openSearch();

    await user.type(promptBox(), "leafy{Shift>}{Enter}{/Shift}and quiet");
    expect(api.callsTo("interpret")).toEqual([]);
    expect(promptBox().value).toBe("leafy\nand quiet");

    await user.type(promptBox(), "{Enter}");
    await settled();
    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(api.lastCallTo("interpret").body).toMatchObject({ text: "leafy\nand quiet" });
  });

  test("test_stop_ends_the_request_and_returns_to_the_state_before", async () => {
    const { user, api } = await openSearch(firstSearch().silent("interpret"));

    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await user.click(screen.getByRole("button", { name: PROMPT.stop }));

    expect(api.lastCallTo("interpret").init.signal?.aborted).toBe(true);
    expect(screen.getByRole("button", { name: PROMPT.submit })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: PROMPT.stop })).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(status()).not.toContain(STATUS.reading);
    expect(promptBox()).toHaveValue("leafy");
  });

  test("test_a_second_press_while_reading_sends_nothing_more", async () => {
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);

    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await user.click(screen.getByRole("button", { name: PROMPT.reading }));
    await user.type(promptBox(), "{Enter}");

    expect(api.callsTo("interpret")).toHaveLength(1);
    reading.release();
    await settled();
  });

  test("test_an_empty_box_is_not_sent_and_says_what_to_do", async () => {
    const { user, api } = await openSearch();

    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(api.callsTo("interpret")).toEqual([]);
    expect(screen.getByRole("alert")).toHaveTextContent(PROMPT.empty);
    expect(promptBox()).toHaveAccessibleDescription(expect.stringContaining(PROMPT.empty));
    expect(promptBox()).toHaveFocus();
  });
});

describe("results: the ranking came back", () => {
  test("test_the_chips_say_what_was_understood_and_mark_what_was_assumed", async () => {
    const { user } = await openSearch();
    await search(user);

    const chips = within(screen.getByRole("region", { name: CHIPS.label }));
    // The words said "Renting", so the tenure is not marked as assumed, though it is the
    // tenure a search starts from and the spec still calls it a default.
    expect(first.read.operations.budget_ops[0]).toMatchObject({ tenure: "rent", provenance: "stated" });
    expect(chips.getAllByRole("listitem").map((chip) => chip.textContent?.replace("×", ""))).toEqual([
      "Renting",
      "£1,700 a month, One bedroom, flexible assumed",
      "Cindermoor Works, Public transport assumed, within 35 minutes, flexible assumed",
      "Leafy",
      "Quiet residential",
      expect.stringMatching(/^Usual settings: 6 assumed/),
    ]);
    expect(chips.getByText(CHIPS.readBy.rule)).toBeInTheDocument();
  });

  test("test_the_list_is_in_rank_order_with_five_cards_and_fifteen_rows", async () => {
    const { user } = await openSearch();
    await search(user);
    await settled();

    const names = results().map((one) => within(one).getAllByRole("heading")[0]?.textContent);
    expect(names).toEqual(first.rank.ranked.map((area) => nameOf(area.area_id)));
    expect(resultList().tagName).toBe("OL");
    const withReasons = results().filter((one) => within(one).queryByText(RESULTS.reasonsTitle));
    expect(withReasons).toHaveLength(5);
    expect(screen.getByText(RESULTS.firstFive)).toBeInTheDocument();
    expect(status()).toContain(`${STATUS.ranked(22, "Farrowmere")} ${STATUS.gaveWay}`);
  });

  test("test_unmet_requests_are_each_said_in_a_line", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-unmet"));
    await search(user);

    const unmet = within(screen.getByRole("region", { name: UNMET_LABEL }));
    expect(unmet.getAllByRole("listitem").map((line) => line.textContent)).toEqual([
      UNMET.broadband,
      UNMET.flood_risk,
      UNMET.community_amenities,
    ]);
  });

  test("test_an_edit_that_was_not_applied_is_said_with_what_it_was_about_and_why", async () => {
    const { user } = await openSearch(
      firstSearch().on("interpret", "interpret-rejected").on("rank", withTheSpecSent("rank-first")),
    );
    await search(user, "somewhere safe, near a park");

    const refused = within(screen.getByRole("region", { name: REJECTED_LABEL }));
    expect(refused.getAllByRole("listitem").map((line) => line.textContent)).toEqual([
      `Recorded violence and robbery: ${REJECTED.crime_needs_explicit_request}`,
      `Recorded burglary and theft: ${REJECTED.crime_needs_explicit_request}`,
    ]);
    // The park was applied, and is a chip. Recorded crime was not, and is not.
    const chips = within(screen.getByRole("region", { name: CHIPS.label }));
    expect(chips.getByRole("button", { name: /^Walk to the nearest park/ })).toBeInTheDocument();
    expect(chips.queryByRole("button", { name: /^Recorded/ })).toBeNull();
  });

  test("test_the_results_page_has_no_accessibility_fault", async () => {
    const { user, container } = await openSearch();
    await search(user);
    await settled();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("refining: a control changed something", () => {
  test("test_the_list_stays_and_is_marked_busy_and_the_control_shows_its_new_value_at_once", async () => {
    const api = firstSearch();
    const { user } = await openSearch(api);
    await search(user);
    await settled();
    const slow = api.hold("rank", "rank-refined");
    api.on("explain_top", "explanations-refined");
    await user.click(settingsButton());
    const journey = within(screen.getByRole("group", { name: JOURNEY.place("Cindermoor Works") }));

    await user.click(journey.getByRole("checkbox", { name: JOURNEY.firm }));

    expect(journey.getByRole("checkbox", { name: JOURNEY.firm })).toBeChecked();
    expect(resultList()).toHaveAttribute("aria-busy", "true");
    expect(results()).toHaveLength(20);
    expect(api.lastCallTo("rank").body).toEqual({
      spec: first.rank.spec,
      operations: edits.placeStrictness("syn-p0021", "hard"),
      limit: 20,
    });

    slow.release();
    await settled();
    const refined = recordedAnswer("rank", "rank-refined").body.data;
    expect(results()).toHaveLength(refined.ranked.length);
    // Every control is drawn again from the spec that came back.
    expect(journey.getByRole("textbox", { name: JOURNEY.longest })).toHaveValue("30");
    // Fewer areas are ranked than were: the line says so, and how many of the rest moved.
    expect(status().join(" ")).toMatch(/11 areas ranked, 11 fewer than before\. \d+ of the rest changed place\./);
  });

  test("test_a_chip_opens_the_same_control_the_settings_hold_in_place", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));
    const editor = within(screen.getByRole("group", { name: JOURNEY.place("Cindermoor Works") }));
    await user.click(editor.getByRole("radio", { name: "By bike" }));
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({
      operations: edits.placeMode("syn-p0021", "cycle"),
    });
  });

  test("test_removing_a_chip_sends_the_edit_that_takes_it_out", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();

    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Quiet residential` }));
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({
      operations: edits.tagOff("quiet_residential"),
    });
  });

  test("test_an_edit_the_api_refuses_puts_the_control_back_and_says_why_beside_it", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "rank-rejected-edit");
    await user.click(settingsButton());
    const budget = within(screen.getByRole("group", { name: BUDGET.legend }));
    const amount = budget.getByRole("textbox", { name: BUDGET.amount.rent });

    await user.clear(amount);
    await user.type(amount, "1{Enter}");
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.budgetAmount(1) });
    expect(amount).toHaveValue("1700");
    expect(amount).toHaveAccessibleDescription(expect.stringContaining(REJECTED.out_of_range));
    expect(budget.getByRole("alert")).toHaveTextContent(REJECTED.out_of_range);
    expect(results()).toHaveLength(20);
  });

  test("test_hiding_an_area_from_its_card_sends_the_edit_that_hides_it", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();

    await user.click(screen.getByRole("button", { name: RESULTS.hide("Farrowmere") }));
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.areaHide("syn-n0006") });
  });
});

describe("clarifying a place", () => {
  const asked = recordedAnswer("interpret", "interpret-clarify").body.data;

  test("test_the_question_offers_each_place_by_name_and_kind_and_never_repeats_what_was_typed", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");

    const question = within(screen.getByRole("region", { name: CLARIFY.question }));
    expect(question.getAllByRole("button").map((button) => button.textContent)).toEqual([
      "Pellam CrossStation",
      "Pellam ExchangeDistrict",
      "Pellam InfirmaryHospital",
      CLARIFY.leaveOut,
    ]);
    expect(question.getByRole("combobox", { name: CLARIFY.search })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: CLARIFY.question }).textContent).not.toMatch(/30 minutes to Pellam\b/);
    // The rest was read and ranked: there are results under the question.
    expect(results().length).toBeGreaterThan(0);
    expect(status().join(" ")).toContain(STATUS.question);
    // The refusal the question stands for is not said twice.
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
  });

  test("test_picking_a_place_sends_the_copied_edit_with_its_id_and_the_question_goes", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");
    api.on("rank", "rank-nights-out").on("explain_top", "explanations-nights-out");

    await user.click(screen.getByRole("button", { name: /^Pellam Exchange/ }));
    await settled();

    const sent = (api.lastCallTo("rank").body as { operations: Operations }).operations;
    expect(sent.commute_ops).toEqual([{ ...asked.operations.commute_ops[0], place_id: "syn-p0017" }]);
    expect(screen.queryByRole("region", { name: CLARIFY.question })).toBeNull();
    // The chip for the place carries the name that was picked.
    expect(screen.getByRole("button", { name: /^Pellam Exchange/ })).toBeInTheDocument();
  });

  test("test_with_no_options_there_is_the_search_field_alone", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-clarify-no-options"));
    await search(user, sentenceOf("interpret-clarify-no-options"));
    const question = within(screen.getByRole("region", { name: CLARIFY.question }));

    expect(question.getAllByRole("button").map((button) => button.textContent)).toEqual([CLARIFY.leaveOut]);
    expect(question.getByText(CLARIFY.none)).toBeInTheDocument();

    await user.type(question.getByRole("combobox", { name: CLARIFY.search }), "pel");
    await user.click(await question.findByRole("option", { name: /^Pellam Cross/ }));
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({
      operations: { commute_ops: [{ action: "add", place_id: "syn-p0012", provenance: "stated" }] },
    });
  });

  test("test_leave_it_out_takes_the_question_away_and_sends_nothing", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));
    await search(user, "Leafy, renting, 30 minutes to Pellam");
    await settled();
    api.calls.length = 0;

    await user.click(screen.getByRole("button", { name: CLARIFY.leaveOut }));

    expect(screen.queryByRole("region", { name: CLARIFY.question })).toBeNull();
    expect(api.calls).toEqual([]);
  });
});

describe("nothing matches", () => {
  async function nothingMatches() {
    const opened = await openSearch(firstSearch().on("interpret", "interpret-two-journeys").on("rank", "rank-nothing-matches"));
    await search(opened.user, "at most 10 minutes, no more than £400");
    await settled();
    return opened;
  }

  test("test_the_page_says_so_with_a_count_for_each_reason", async () => {
    await nothingMatches();

    const block = within(screen.getByRole("region", { name: NOTHING_MATCHES.title }));
    expect(block.getByText(FILTERED.over_budget).nextSibling).toHaveTextContent("21 areas");
    expect(block.getByText(FILTERED.commute_cap).nextSibling).toHaveTextContent("1 area");
    expect(block.getByText(UNRANKED.not_rankable).nextSibling).toHaveTextContent("2 areas");
    expect(status()).toContain(STATUS.nothingMatches);
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
  });

  test("test_there_is_one_button_for_each_firm_limit_and_it_sends_that_one_edit", async () => {
    const { user, api } = await nothingMatches();
    const block = within(screen.getByRole("region", { name: NOTHING_MATCHES.title }));

    expect(
      within(block.getByRole("list", { name: NOTHING_MATCHES.loosen }))
        .getAllByRole("button")
        .map((button) => button.textContent),
    ).toEqual([NOTHING_MATCHES.budgetFlexible, NOTHING_MATCHES.journeyFlexible("Cindermoor Works")]);

    api.on("rank", "rank-first");
    await user.click(block.getByRole("button", { name: NOTHING_MATCHES.budgetFlexible }));
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.budgetStrictness("soft") });
    expect(results()).toHaveLength(20);
  });

  test("test_the_table_gives_each_area_its_reason_in_words", async () => {
    await nothingMatches();
    const nothing = recordedAnswer("rank", "rank-nothing-matches").body.data;

    const table = within(screen.getAllByRole("table", { name: TABLE.caption })[0] as HTMLElement);
    for (const { area_id: areaId, reason } of nothing.filtered) {
      const row = table.getByRole("row", { name: new RegExp(`^${TABLE.noRank} ${nameOf(areaId)} `) });
      expect(row).toHaveTextContent(FILTERED[reason]);
    }
  });

  test("test_nothing_matches_has_no_accessibility_fault", async () => {
    const { container } = await nothingMatches();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("nothing read", () => {
  test("test_the_page_says_so_opens_the_settings_and_keeps_the_results_on_screen", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.calls.length = 0;
    api.on("interpret", "interpret-nothing-read");

    await user.clear(promptBox());
    await search(user, "What is the best way to learn the piano");

    expect(status()).toContain(NOTICE.nothingRead);
    expect(settingsAreOpen()).toBe(true);
    expect(results()).toHaveLength(20);
    expect(api.calls.map((call) => call.operation)).toEqual(["interpret"]);
  });

  test("test_that_nothing_was_read_is_said_once_and_not_again_as_a_part_that_was_not", async () => {
    const unread = recordedAnswer("interpret", "interpret-nothing-read").body.data;
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-nothing-read"));

    await search(user, "What is the best way to learn the piano");

    // The API says `other` could not be met. With nothing read at all, the one line covers it.
    expect(unread.unmet).toEqual(["other"]);
    expect(status().filter((line) => line === NOTICE.nothingRead)).toHaveLength(1);
    expect(screen.queryByRole("region", { name: UNMET_LABEL })).toBeNull();
    expect(screen.queryByText(UNMET.other)).toBeNull();

    // Nor does it come up when the line goes.
    await user.click(screen.getByRole("switch", { name: "Leafy" }));
    await settled();
    expect(status()).not.toContain(NOTICE.nothingRead);
    expect(screen.queryByText(UNMET.other)).toBeNull();
  });

  test("test_a_part_that_was_not_read_is_still_said_when_the_rest_was", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-unmet"));

    await search(user, sentenceOf("interpret-unmet"));

    const unmet = within(screen.getByRole("region", { name: UNMET_LABEL }));
    for (const category of recordedAnswer("interpret", "interpret-unmet").body.data.unmet) {
      expect(unmet.getByText(UNMET[category])).toBeInTheDocument();
    }
  });

  test("test_words_that_change_nothing_are_not_called_unreadable", async () => {
    const said = recordedAnswer("interpret", "interpret-clarify");
    const body = {
      ...said.body,
      data: {
        ...said.body.data,
        status: "ok",
        clarify: [],
        rejected: [],
        operations: { ...said.body.data.operations, commute_ops: [], tag_ops: [] },
        applied: [{ group: "budget_ops", index: 0, changed: false }],
        spec: meta.data.defaults.rent,
      },
    };
    const { user } = await openSearch(firstSearch().on("interpret", () => responseFrom({ ...said, body })));

    await user.type(promptBox(), "renting");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    await waitFor(() => expect(status()).toContain(NOTICE.nothingChanged));
    expect(status()).not.toContain(NOTICE.nothingRead);
  });

  test("test_a_sentence_that_is_off_the_subject_gets_the_apis_own_words_once", async () => {
    // A model can tell a sentence that is about something else. The rules cannot. This is
    // recorded from the service with a stand-in for the model that answers "off the subject".
    const unread = recordedAnswer("interpret", "interpret-off-topic").body.data;
    const words = unread.notice_text;
    expect(unread).toMatchObject({ status: "off_topic", notice: "off_topic", interpreter: "claude" });
    expect(words).not.toBe("");
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-off-topic"));

    await user.type(promptBox(), "piano");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(settingsAreOpen()).toBe(true));

    expect(status().filter((line) => line === words)).toHaveLength(1);
    expect(status()).not.toContain(NOTICE.nothingRead);
    expect(api.callsTo("rank")).toEqual([]);
  });

  test("test_the_line_goes_once_a_control_is_used", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-nothing-read"));
    await user.type(promptBox(), "piano");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(NOTICE.nothingRead));

    await user.click(screen.getByRole("switch", { name: "Leafy" }));
    await settled();

    expect(status()).not.toContain(NOTICE.nothingRead);
    expect(results()).toHaveLength(20);
  });
});

describe("degraded to a form", () => {
  test("test_when_the_rules_read_the_words_the_page_says_so_and_shows_their_results", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-degraded"));
    await search(user);
    await settled();

    expect(status()).toContain(NOTICE.degraded);
    expect(settingsAreOpen()).toBe(true);
    expect(results()).toHaveLength(20);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("test_when_reading_takes_too_long_the_settings_open_on_the_defaults_and_still_work", async () => {
    const api = firstSearch().silent("interpret");
    const { user } = await openSearch(api);
    jest.useFakeTimers();

    fireEvent.input(promptBox(), { target: { value: "leafy and quiet" } });
    fireEvent.click(screen.getByRole("button", { name: PROMPT.submit }));
    await act(() => jest.advanceTimersByTimeAsync(8_000));
    jest.useRealTimers();

    expect(status()).toContain(NOTICE.degraded);
    expect(settingsAreOpen()).toBe(true);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(promptBox()).toHaveValue("leafy and quiet");

    // The same controls work as a form, with no words read at all.
    await user.click(screen.getByRole("switch", { name: "Leafy" }));
    await settled();
    expect(api.lastCallTo("rank").body).toEqual({
      spec: meta.data.defaults.rent,
      operations: edits.tagOn("leafy"),
      limit: 20,
    });
    expect(results()).toHaveLength(20);
  });

  // A request that cannot leave is another thing: the settings could not reach Burro either.
  // `test/search/walked.test.tsx` holds what the page says then.
  test.each([
    ["the service has a fault", "error-internal"],
    ["the answer is not the api's", "not-the-apis"],
  ] as const)("test_the_form_works_when_interpretation_fails: %s", async (_, how) => {
    const api = firstSearch();
    if (how === "not-the-apis") api.on("interpret", () => new Response("<html>"));
    else api.on("interpret", how);
    const { user } = await openSearch(api);

    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(NOTICE.degraded));

    expect(settingsAreOpen()).toBe(true);
    const budget = within(screen.getByRole("group", { name: BUDGET.legend }));
    await user.type(budget.getByRole("textbox", { name: BUDGET.amount.rent }), "1700{Enter}");
    await settled();
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.budgetAmount(1700) });
    expect(results()).toHaveLength(20);
  });

  test("test_try_again_sends_the_same_text_from_the_box", async () => {
    const api = firstSearch().on("interpret", "error-internal");
    const { user } = await openSearch(api);
    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(NOTICE.degraded));
    api.on("interpret", "interpret-first");

    await user.click(screen.getByRole("button", { name: PROMPT.tryAgain }));
    await settled();

    expect(api.callsTo("interpret").map((call) => (call.body as { text: string }).text)).toEqual([
      "leafy and quiet",
      "leafy and quiet",
    ]);
    expect(results()).toHaveLength(20);
    expect(status()).not.toContain(NOTICE.degraded);
  });

  test("test_the_degraded_form_has_no_accessibility_fault", async () => {
    const { user, container } = await openSearch(firstSearch().on("interpret", "error-internal"));
    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await waitFor(() => expect(status()).toContain(NOTICE.degraded));

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("the neutral notice", () => {
  const notice = recordedAnswer("interpret", "interpret-notice").body.data;

  test("test_the_apis_one_sentence_is_shown_word_for_word_and_the_rest_is_served", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-notice"));
    await search(user, "Quiet and leafy, 30 minutes to work");

    const block = screen.getByRole("status", { name: NOTICE.label });
    expect(block.textContent).toBe(notice.notice_text);
    expect(results()).toHaveLength(20);
  });

  test("test_nothing_on_the_page_says_what_was_left_out", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-notice"));
    await search(user, "Quiet and leafy, not too many students, 30 minutes to work");
    await settled();

    const page = document.querySelector("main")?.textContent ?? "";
    expect(page.replace(promptBox().value, "")).not.toMatch(/student/i);
    expect(screen.queryByRole("region", { name: UNMET_LABEL })).toBeNull();
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(status()).not.toContain(NOTICE.nothingRead);
  });

  test("test_the_notice_stays_while_controls_are_used_and_goes_with_the_next_sentence", async () => {
    const { user, api } = await openSearch(firstSearch().on("interpret", "interpret-notice"));
    await search(user, "Quiet and leafy");
    await settled();

    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));
    await settled();
    expect(screen.getByRole("status", { name: NOTICE.label })).toBeInTheDocument();

    api.on("interpret", "interpret-second-sentence");
    await search(user, " and more green space");
    await settled();
    expect(screen.queryByRole("status", { name: NOTICE.label })).toBeNull();
  });
});

describe("an error from the API", () => {
  test.each([
    ["not-found", "an address that is no route, as a wrong setting of the API's address gives"],
    ["rank-invalid-operations", "a request the API will not take"],
  ])("test_a_sentence_the_api_refuses_for_anything_but_its_words_is_never_met_with_silence: %s", async (scenario) => {
    const refused = recordedError(scenario);
    const { user } = await openSearch(firstSearch().on("interpret", scenario));

    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    const alert = await screen.findByRole("alert");
    expect(refused.status).toBeLessThan(500);
    expect(alert).toHaveTextContent(refused.body.error.message);
    expect(alert).toHaveTextContent(refused.headers["x-request-id"] ?? "no id");
    expect(within(alert).getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();
    // It is not said to be words that could not be read: the API did not get as far as reading.
    expect(status()).not.toContain(NOTICE.degraded);
    expect(promptBox()).toHaveValue("leafy and quiet");
  });

  test("test_a_refusal_of_the_text_is_said_under_the_box_in_the_apis_words", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-invalid-text"));
    const refusal = recordedError("interpret-invalid-text").body.error.message;

    await user.type(promptBox(), "x");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(await screen.findByRole("alert")).toHaveTextContent(refusal);
    expect(promptBox()).toHaveAccessibleDescription(expect.stringContaining(refusal));
    expect(promptBox()).toHaveAttribute("aria-invalid", "true");
    expect(status()).not.toContain(NOTICE.degraded);
  });

  test("test_a_fault_keeps_the_last_results_marked_not_updated_with_the_id_to_quote", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "error-internal");
    const fault = recordedError("error-internal");

    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));
    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent(fault.body.error.message);
    expect(alert).toHaveTextContent(NOTICE.notUpdated);
    expect(alert).toHaveTextContent(fault.headers["x-request-id"] ?? "no id");
    expect(results()).toHaveLength(20);

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await user.click(within(alert).getByRole("button", { name: PROMPT.tryAgain }));
    await settled();
    expect(screen.queryByRole("alert")).toBeNull();
    // The edit that failed was kept, and sent again.
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.tagOff("leafy") });
  });

  test("test_a_search_that_names_something_gone_offers_the_edit_that_takes_it_out", async () => {
    const stale = recordedAnswer("rank", "rank-stale-spec-repaired").request.body as {
      spec: typeof first.rank.spec;
    };
    const read = recordedAnswer("interpret", "interpret-first");
    const holdingAGonePlace = { ...read, body: { ...read.body, data: { ...read.body.data, spec: stale.spec } } };
    const { user, api } = await openSearch(
      firstSearch()
        .on("interpret", () => responseFrom(holdingAGonePlace))
        .on("rank", "rank-stale-spec"),
    );

    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent(NOTICE.stale);
    api.on("rank", "rank-stale-spec-repaired");
    await user.click(within(alert).getByRole("button", { name: NOTICE.takeOut("Place 2") }));
    await settled();

    expect(api.lastCallTo("rank").body).toEqual(recordedAnswer("rank", "rank-stale-spec-repaired").request.body && {
      spec: stale.spec,
      operations: edits.placeRemove("syn-p9999"),
      limit: 20,
    });
    expect(screen.queryByRole("alert")).toBeNull();
    expect(results()).toHaveLength(20);
  });

  test("test_start_again_returns_to_the_defaults", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "error-internal");
    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));

    await user.click(within(await screen.findByRole("alert")).getByRole("button", { name: PROMPT.startAgain }));

    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    const chips = within(screen.getByRole("region", { name: CHIPS.startLabel }));
    expect(chips.getAllByRole("listitem")).toHaveLength(2);
  });

  test("test_reasons_that_cannot_be_loaded_are_said_on_the_card_and_the_ranking_stays", async () => {
    const { user } = await openSearch(firstSearch().on("explain_top", "error-internal"));
    await search(user);
    await settled();
    const fault = recordedError("error-internal");

    expect(results()).toHaveLength(20);
    expect(within(results()[0] as HTMLElement).getByText(RESULTS.reasonsFailed)).toBeInTheDocument();
    // Why they could not be loaded is never met with silence: the API's words, the id to
    // quote and "Try again". The results themselves were updated, and are not said not to be.
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(fault.body.error.message);
    expect(alert).toHaveTextContent(fault.headers["x-request-id"] ?? "no id");
    expect(alert).not.toHaveTextContent(NOTICE.notUpdated);
    expect(within(alert).getByRole("button", { name: PROMPT.tryAgain })).toBeInTheDocument();
  });

  test("test_the_error_state_has_no_accessibility_fault", async () => {
    const { user, api, container } = await openSearch();
    await search(user);
    await settled();
    api.on("rank", "error-internal");
    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));
    await screen.findByRole("alert");

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("offline", () => {
  test("test_the_page_says_so_keeps_the_results_and_sends_the_edit_once_when_back", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settled();
    api.calls.length = 0;

    setOnline(false);
    act(() => void window.dispatchEvent(new Event("offline")));
    expect(status()).toContain(NOTICE.offline);

    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));
    await waitFor(() => expect(status()).toContain(`${NOTICE.offline} ${NOTICE.offlineWaiting}`));
    expect(api.calls).toEqual([]);
    expect(results()).toHaveLength(20);
    expect(screen.queryByRole("alert")).toBeNull();

    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    setOnline(true);
    act(() => void window.dispatchEvent(new Event("online")));
    await settled();

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toMatchObject({ operations: edits.tagOff("leafy") });
    expect(status().join(" ")).not.toContain(NOTICE.offline);
  });
});

describe("the map, where it cannot be drawn", () => {
  test("test_the_table_stands_in_for_the_map_with_a_line_saying_why", async () => {
    const { user } = await openSearch();
    await search(user);

    expect(status()).toContain(MAP.noWebGL);
    expect(screen.getAllByRole("table", { name: TABLE.caption }).length).toBeGreaterThan(0);
  });
});
