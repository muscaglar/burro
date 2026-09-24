import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DIMENSION, POLARITY, SEGMENT } from "@/content/labels";
import { REJECTED } from "@/content/search";
import { BUDGET, CRIME_CAVEAT, FEATURES, HIDDEN, JOURNEY, SEGMENTS, SETTINGS, SLIDER } from "@/content/settings";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, Operations, PreferenceSpec, RejectReason } from "@/lib/api/schema";
import { edits, merged, NO_EDITS } from "@/lib/search/edits";

import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
import { SettingsPanel } from "./SettingsPanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data.spec;

function show(
  spec: PreferenceSpec = first,
  { refused, version = 1 }: { refused?: ReadonlyMap<string, RejectReason>; version?: number } = {},
) {
  const sent: Operations[] = [];
  const onRank = jest.fn();
  const panel = (shown: PreferenceSpec, at: number) => (
    <SettingsPanel
      spec={shown}
      meta={meta}
      areas={areas}
      placeNames={{ "syn-p0021": "Cindermoor Works" }}
      onEdit={(operations) => sent.push(operations)}
      version={at}
      refused={refused}
      open
      onToggle={() => undefined}
      onRank={onRank}
    />
  );
  const view = render(panel(spec, version));
  return {
    sent,
    onRank,
    user: userEvent.setup({ delay: null }),
    again: (next: PreferenceSpec, at: number) => view.rerender(panel(next, at)),
    ...view,
  };
}

const group = (name: string) => within(screen.getByRole("group", { name }));

describe("the settings", () => {
  test("test_every_edit_a_control_sends_is_one_the_contract_accepts", async () => {
    const { user, sent } = show();

    await user.click(group(BUDGET.legend).getByRole("checkbox", { name: BUDGET.firm }));
    await user.selectOptions(group(BUDGET.legend).getByRole("combobox", { name: BUDGET.segment }), "bed_2");
    await user.click(group(BUDGET.legend).getByRole("button", { name: BUDGET.clear }));
    await user.click(group(BUDGET.legend).getByRole("button", { name: BUDGET.less }));
    await user.click(screen.getByRole("radio", { name: "By bike" }));
    await user.click(screen.getByRole("radio", { name: "The average of the journeys counts" }));
    await user.click(screen.getByRole("radio", { name: "The time if you just miss a service counts" }));
    await user.click(screen.getByRole("button", { name: JOURNEY.longer }));
    await user.click(screen.getByRole("button", { name: JOURNEY.remove("Cindermoor Works") }));
    await user.click(screen.getByRole("switch", { name: "Waterside" }));
    await user.click(screen.getByRole("switch", { name: "Leafy" }));
    await user.click(screen.getByRole("switch", { name: "Pubs, bars and evening venues" }));

    expect(sent).toEqual([
      edits.budgetStrictness("hard"),
      edits.budgetSegment("bed_2"),
      edits.budgetClear(),
      edits.budgetStep("down_small"),
      edits.placeMode("syn-p0021", "cycle"),
      edits.journeyCombine("mean"),
      edits.journeyBasis("just_missed"),
      edits.placeStep("syn-p0021", "up_small"),
      edits.placeRemove("syn-p0021"),
      edits.tagOn("waterside"),
      edits.tagOff("leafy"),
      edits.featureOn("venue_evening"),
    ]);
    for (const operations of sent) expect(problemsWith("Operations", operations)).toEqual([]);
  });

  test("test_every_control_is_drawn_from_the_spec_the_api_returned", () => {
    show();

    expect(group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent })).toHaveValue("1700");
    expect(group(BUDGET.legend).getByRole("combobox", { name: BUDGET.segment })).toHaveValue("bed_1");
    expect(group(BUDGET.legend).getByRole("checkbox", { name: BUDGET.firm })).not.toBeChecked();
    expect(group(BUDGET.legend).getByRole("slider", { name: BUDGET.weight })).toHaveValue("80");
    const journey = group(JOURNEY.place("Cindermoor Works"));
    expect(journey.getByRole("radio", { name: "Public transport" })).toBeChecked();
    expect(journey.getByRole("textbox", { name: JOURNEY.longest })).toHaveValue("35");
    expect(screen.getByRole("switch", { name: "Leafy" })).toBeChecked();
    expect(screen.getByRole("slider", { name: FEATURES.weight("Leafy") })).toHaveValue("50");
    expect(screen.getByRole("switch", { name: "Waterside" })).not.toBeChecked();
    // A setting nobody chose is on, at the weight it gave way to: a quarter of 0.50, rounded down to a step.
    expect(screen.getByRole("slider", { name: FEATURES.weight("Walk to the nearest station") })).toHaveValue("10");
  });

  test("test_a_control_shows_its_new_value_at_once_and_is_drawn_again_from_the_answer", async () => {
    const { user, again } = show();
    const firm = () => group(BUDGET.legend).getByRole("checkbox", { name: BUDGET.firm });

    await user.click(firm());
    expect(firm()).toBeChecked();

    // The answer came back and the budget is still flexible: the edit was refused.
    again(first, 2);
    expect(firm()).not.toBeChecked();

    await user.click(firm());
    again({ ...first, budget: { ...first.budget, strictness: "hard" } }, 3);
    expect(firm()).toBeChecked();
  });

  test("test_a_usual_setting_that_was_switched_off_stays_off_when_the_answer_comes", async () => {
    // Recorded: the switch of a usual setting turned off. The API answers with an entry
    // of 0 in its place, and not with no entry. The switch must not spring back on.
    const answered = recordedAnswer("rank", "rank-switched-off");
    const after = answered.body.data.spec;
    const station = () => screen.getByRole("switch", { name: "Walk to the nearest station" });
    const { user, sent, again } = show();
    expect(station()).toBeChecked();

    await user.click(station());
    expect(sent).toEqual([(answered.request.body as { operations: Operations }).operations]);
    again(after, 2);

    expect(after.weights.find((weight) => weight.feature_id === "station_walk")).toMatchObject({ weight: 0 });
    expect(station()).not.toBeChecked();
    expect(screen.queryByRole("slider", { name: FEATURES.weight("Walk to the nearest station") })).toBeNull();

    // Switched on again, it is asked for as anything is that is switched on.
    await user.click(station());
    expect(sent[1]).toEqual(edits.featureOn("station_walk"));
  });

  test("test_a_thing_taken_off_in_words_is_drawn_as_off", () => {
    show(recordedAnswer("interpret", "interpret-second-sentence").body.data.spec);

    const highStreet = "Share of homes within a 10-minute walk of a high street or town centre";
    expect(screen.getByRole("switch", { name: highStreet })).not.toBeChecked();
    expect(screen.queryByRole("slider", { name: FEATURES.weight(highStreet) })).toBeNull();
    expect(screen.getByRole("switch", { name: "Public green space as a share of the area" })).toBeChecked();
  });

  test("test_a_switch_that_is_off_shows_no_slider", () => {
    show();

    expect(screen.queryByRole("slider", { name: FEATURES.weight("Waterside") })).toBeNull();
    expect(screen.getAllByRole("switch")).toHaveLength(meta.features.length + meta.tags.length - 2);
  });

  test("test_the_slider_of_a_feature_sends_its_weight_and_a_weight_of_nothing_removes_it", () => {
    const { sent } = show();
    const slider = screen.getByRole("slider", { name: FEATURES.weight("Leafy") });

    fireEvent.pointerDown(slider);
    fireEvent.change(slider, { target: { value: "0" } });
    fireEvent.pointerUp(slider);

    // The API takes a weight of nothing as the feature taken out, so zero has one spelling.
    expect(sent).toEqual([edits.tagWeight("leafy", 0)]);
  });

  test("test_which_way_is_better_is_asked_only_where_either_can_be", async () => {
    const nights = recordedAnswer("rank", "rank-nights-out").body.data.spec;
    const { user, sent } = show(nights);

    const either = meta.features.filter((metric) => metric.polarity === "either").map((metric) => metric.label);
    expect(either.length).toBeGreaterThan(0);
    const asked = screen.getAllByRole("group").filter((one) => one.tagName === "FIELDSET" && /Which way counts/.test(one.textContent ?? ""));
    expect(asked.length).toBeGreaterThan(0);
    for (const one of asked) {
      expect(either.some((label) => one.textContent?.includes(label))).toBe(true);
    }

    const pubs = group(FEATURES.direction("Pubs, bars and evening venues"));
    expect(pubs.getByRole("radio", { name: "Higher is better" })).toBeChecked();
    await user.click(pubs.getByRole("radio", { name: "Lower is better" }));
    expect(sent).toEqual([edits.featureDirection("venue_evening", 0.5, "less")]);
  });

  test("test_a_change_of_direction_is_sent_with_the_weight_the_person_just_set_and_not_the_one_before", async () => {
    const nights = recordedAnswer("rank", "rank-nights-out").body.data.spec;
    const { user, sent } = show(nights);
    const pubs = "Pubs, bars and evening venues";
    const number = screen.getByRole("textbox", { name: SLIDER.number(FEATURES.weight(pubs)) });

    await user.clear(number);
    await user.type(number, "70{Enter}");
    // No answer has come: the spec still says 50. A `set` always reads its value, and the later edit wins.
    await user.click(group(FEATURES.direction(pubs)).getByRole("radio", { name: "Lower is better" }));
    // Then the person thinks again about how much, still before any answer.
    await user.clear(number);
    await user.type(number, "50{Enter}");

    expect(sent).toEqual([
      edits.featureWeight("venue_evening", 0.7),
      edits.featureDirection("venue_evening", 0.7, "less"),
      edits.featureWeight("venue_evening", 0.5),
    ]);
    // As the API applies them, in order: it counts for 50, and fewer is better.
    expect(sent.reduce(merged, NO_EDITS).weight_ops.at(-1)).toMatchObject({ value: 0.5, direction: "default" });
    for (const operations of sent) expect(problemsWith("Operations", operations)).toEqual([]);
  });

  test("test_after_the_answer_a_change_of_direction_is_sent_with_the_weight_the_answer_gave", async () => {
    const nights = recordedAnswer("rank", "rank-nights-out").body.data.spec;
    const { user, sent, again } = show(nights);
    const pubs = "Pubs, bars and evening venues";
    const number = screen.getByRole("textbox", { name: SLIDER.number(FEATURES.weight(pubs)) });

    await user.clear(number);
    await user.type(number, "70{Enter}");
    // The answer refused the weight: it is what it was.
    again(nights, 2);
    await user.click(group(FEATURES.direction(pubs)).getByRole("radio", { name: "Lower is better" }));

    expect(sent.at(-1)).toEqual(edits.featureDirection("venue_evening", 0.5, "less"));
  });

  test("test_every_feature_says_under_its_switch_which_way_counts_as_better", async () => {
    const { user } = show();
    await user.click(screen.getByRole("button", { name: DIMENSION.crime }));

    // The settings stand alone when the words cannot be read, so a switch named for a
    // measure, such as noise, must say whether more of it or less of it is wanted.
    const features = meta.features.filter((metric) => metric.rankable);
    expect(new Set(features.map((metric) => metric.polarity))).toEqual(new Set(["more", "less", "either"]));
    for (const metric of features) {
      const toggle = screen.getByRole("switch", { name: metric.label });
      expect(toggle).toHaveAccessibleDescription(POLARITY[metric.polarity]);
      // It is on the page for everyone, and not for a screen reader alone.
      const hint = within(toggle.closest("[role='group']") as HTMLElement).getByText(POLARITY[metric.polarity]);
      expect(hint).toBeVisible();
      expect(hint.closest(".visually-hidden")).toBeNull();
    }
  });

  test("test_the_features_are_headed_by_what_they_are_and_not_by_a_wish", () => {
    // Seen in a browser, and by the reviewers before it: under "What you want nearby" stood
    // transport noise and nitrogen dioxide. A feature names a measure, which may be wanted
    // low, so the heading says that it counts and not that it is wanted.
    show();

    expect(FEATURES.legend).toBe("What counts nearby");
    expect(screen.getByRole("group", { name: FEATURES.legend })).toBeInTheDocument();
    expect(document.body.textContent?.includes("What you want nearby")).toBe(false);
  });

  /** The lines that say what the scale of a slider means, of those that can be seen. */
  const scalesSeenIn = (part: HTMLElement) =>
    within(part)
      .queryAllByText(SLIDER.range)
      .filter((line) => line.closest(".visually-hidden, [aria-hidden='true'], [hidden]") === null);

  test("test_the_scale_of_the_sliders_is_drawn_once_for_each_group_that_shows_one", () => {
    // Seen in a browser: all eight lines that say what 0 and 100 mean were 1 pixel by 1.
    show();
    const features = screen.getByRole("group", { name: FEATURES.legend });
    const tags = screen.getByRole("group", { name: FEATURES.tagsLegend });

    // The features hold several sliders, and say what the scale means once, where it can be seen.
    for (const part of [features, tags]) {
      expect(within(part).getAllByRole("slider").length).toBeGreaterThan(1);
      expect(scalesSeenIn(part)).toHaveLength(1);
      for (const slider of within(part).getAllByRole("slider")) {
        expect(slider).toHaveAccessibleDescription(SLIDER.range);
      }
    }
    // The budget and the journeys hold one slider each, which says it for itself.
    expect(scalesSeenIn(screen.getByRole("group", { name: BUDGET.legend }))).toHaveLength(1);
    expect(scalesSeenIn(screen.getByRole("group", { name: JOURNEY.settingsLegend }))).toHaveLength(1);
  });

  test("test_a_group_with_every_switch_off_shows_no_slider_and_no_scale_for_one", () => {
    show({ ...first, tags: [] });
    const tags = screen.getByRole("group", { name: FEATURES.tagsLegend });

    expect(within(tags).queryAllByRole("slider")).toHaveLength(0);
    expect(scalesSeenIn(tags)).toHaveLength(0);
  });

  test("test_a_tag_has_no_way_that_counts_as_better_and_says_none", () => {
    show();

    for (const tag of meta.tags) {
      expect(screen.getByRole("switch", { name: tag.label })).not.toHaveAccessibleDescription();
    }
  });

  test("test_the_form_offers_only_what_the_release_can_rank", () => {
    const some = { ...meta, features: meta.features.map((metric, at) => ({ ...metric, rankable: at % 2 === 0 })) };
    render(
      <SettingsPanel
        spec={meta.defaults.rent}
        meta={some}
        areas={areas}
        placeNames={{}}
        onEdit={() => undefined}
        version={1}
        open
        onToggle={() => undefined}
      />,
    );

    for (const metric of some.features.filter((one) => one.dimension !== "crime")) {
      expect(screen.queryAllByRole("switch", { name: metric.label })).toHaveLength(metric.rankable ? 1 : 0);
    }
  });

  test("test_the_limits_are_the_ones_the_api_serves", () => {
    show();

    expect(group(BUDGET.legend).getByText("Between £300 and £20,000.")).toBeInTheDocument();
    // The longest journey is kept within what the data holds for that way of travelling.
    expect(group(JOURNEY.place("Cindermoor Works")).getByText(JOURNEY.between(10, 90))).toBeInTheDocument();
  });

  test("test_changing_how_you_travel_changes_the_longest_journey_that_can_be_asked_for", async () => {
    const { user } = show();

    await user.click(screen.getByRole("radio", { name: "On foot" }));

    expect(group(JOURNEY.place("Cindermoor Works")).getByText(JOURNEY.between(10, 60))).toBeInTheDocument();
  });

  test("test_a_typed_budget_is_sent_as_it_was_typed_so_the_api_can_say_if_it_is_out_of_range", async () => {
    const { user, sent } = show();
    const amount = group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent });

    await user.clear(amount);
    await user.type(amount, "1");
    expect(sent).toEqual([]);
    await user.type(amount, "850");
    await user.tab();

    expect(sent).toEqual([edits.budgetAmount(1850)]);
  });

  test("test_a_budget_that_is_no_number_is_said_beside_the_field_and_not_sent", async () => {
    const { user, sent } = show();
    const amount = group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent });

    await user.clear(amount);
    await user.type(amount, "about two grand{Enter}");

    expect(sent).toEqual([]);
    expect(group(BUDGET.legend).getByRole("alert")).toHaveTextContent(BUDGET.notWhole);
    expect(amount).toBeInvalid();
    expect(amount).toHaveAccessibleDescription(expect.stringContaining(BUDGET.notWhole));
  });

  test("test_a_budget_may_be_typed_with_a_pound_sign_and_commas", async () => {
    const { user, sent } = show();
    const amount = group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent });

    await user.clear(amount);
    await user.type(amount, "£2,100{Enter}");

    expect(sent).toEqual([edits.budgetAmount(2100)]);
  });

  test("test_with_no_budget_set_the_steps_and_clear_are_off_because_there_is_nothing_to_step_from", () => {
    show(meta.defaults.rent);

    expect(group(BUDGET.legend).getByRole("button", { name: BUDGET.less })).toBeDisabled();
    expect(group(BUDGET.legend).getByRole("button", { name: BUDGET.more })).toBeDisabled();
    expect(group(BUDGET.legend).getByRole("button", { name: BUDGET.clear })).toHaveAttribute("aria-disabled", "true");
    expect(group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent })).toHaveValue("");
  });

  test("test_clear_keeps_the_focus_when_the_budget_has_gone_and_then_sends_nothing", async () => {
    // Pressed, it takes the budget off, and is then off itself. It is not switched off, because
    // a button that is switched off while it has the focus leaves the focus on nothing.
    const { user, sent, again } = show();
    const clear = group(BUDGET.legend).getByRole("button", { name: BUDGET.clear });

    await user.click(clear);
    again({ ...first, budget: { ...first.budget, amount: null } }, 2);

    expect(sent).toEqual([edits.budgetClear()]);
    expect(clear).not.toBeDisabled();
    expect(clear).toHaveAttribute("aria-disabled", "true");
    expect(clear).toHaveFocus();
    await user.click(clear);
    expect(sent).toEqual([edits.budgetClear()]);
  });

  test("test_an_edit_that_was_refused_is_said_beside_the_control_it_concerns", () => {
    show(first, { refused: new Map<string, RejectReason>([["budget", "out_of_range"], ["tag:leafy", "not_in_release"]]) });

    expect(group(BUDGET.legend).getByRole("alert")).toHaveTextContent(REJECTED.out_of_range);
    expect(group("Leafy").getByRole("alert")).toHaveTextContent(REJECTED.not_in_release);
    expect(screen.getAllByRole("alert")).toHaveLength(2);
  });

  test("test_with_no_ranking_yet_the_settings_can_be_ranked_as_they_stand", async () => {
    const { user, onRank } = show(meta.defaults.rent);

    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));

    expect(onRank).toHaveBeenCalledTimes(1);
  });

  test("test_a_hidden_area_can_be_shown_again", async () => {
    const hidden = { ...first, areas: [{ area_id: "syn-n0006", rule: "exclude", provenance: "ui_edit" }] } as const;
    const { user, sent } = show(hidden);

    await user.click(group(HIDDEN.legend).getByRole("button", { name: HIDDEN.show("Farrowmere") }));

    expect(sent).toEqual([edits.areaClear("syn-n0006")]);
  });

  test("test_the_settings_open_have_no_accessibility_fault", async () => {
    const { container, user } = show();
    await user.click(screen.getByRole("button", { name: DIMENSION.crime }));

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("recorded crime", () => {
  test("test_recorded_crime_is_its_own_group_closed_and_off_at_first", () => {
    show();

    const crime = screen.getByRole("button", { name: DIMENSION.crime });
    expect(crime).toHaveAttribute("aria-expanded", "false");
    for (const metric of meta.features.filter((one) => one.dimension === "crime")) {
      expect(screen.queryByRole("switch", { name: metric.label })).toBeNull();
      expect(first.weights.some((weight) => weight.feature_id === metric.feature_id)).toBe(false);
      expect(meta.defaults.rent.weights.some((weight) => weight.feature_id === metric.feature_id)).toBe(false);
    }
  });

  test("test_the_caveat_stands_above_its_switches_and_a_switch_sends_an_edit_made_by_a_control", async () => {
    const { user, sent } = show();

    await user.click(screen.getByRole("button", { name: DIMENSION.crime }));
    const caveat = screen.getByText(CRIME_CAVEAT);
    const theft = screen.getByRole("switch", { name: "Recorded burglary and theft" });
    expect(caveat.compareDocumentPosition(theft) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(theft).not.toBeChecked();

    await user.click(theft);
    // The API weighs crime only when a person asks for it or moves its control: this is the control.
    const recorded = recordedAnswer("rank", "rank-crime-switched-on").request.body as { operations: Operations };
    expect(sent).toEqual([recorded.operations]);
  });

  test("test_the_caveat_is_the_contracts_word_for_word", () => {
    const contract = readFileSync(
      path.resolve(__dirname, "../../../../../docs/design/contract.md"),
      "utf8",
    );

    expect(contract.includes(CRIME_CAVEAT)).toBe(true);
    expect(CRIME_CAVEAT).toBe("Recorded crime depends on what is reported, and locations are approximate.");
  });
});

describe("the kinds of home", () => {
  test("test_the_kinds_offered_for_each_tenure_are_the_ones_the_api_serves_a_cost_for", () => {
    const served: Record<string, Set<string>> = { rent: new Set(), buy: new Set() };
    for (const file of readdirSync(path.join(recordedFolder(), "area"))) {
      const { data } = readRecorded(`area/${file.replace(/\.json$/, "")}`).body as { data: AreaData };
      for (const cost of data.cost) served[cost.tenure]?.add(cost.segment);
    }

    expect([...SEGMENTS.rent].sort()).toEqual([...(served.rent ?? [])].sort());
    expect([...SEGMENTS.buy].sort()).toEqual([...(served.buy ?? [])].sort());
    expect(SEGMENTS.rent).toContain(meta.defaults.rent.budget.segment);
    expect(SEGMENTS.buy).toContain(meta.defaults.buy.budget.segment);
  });

  test("test_a_buyer_is_offered_kinds_of_home_to_buy_and_no_kind_to_rent", () => {
    show(recordedAnswer("rank", "rank-buyer-family").body.data.spec);

    const kinds = within(group(BUDGET.legend).getByRole("combobox", { name: BUDGET.segment }))
      .getAllByRole("option")
      .map((option) => option.textContent);
    expect(kinds).toEqual(SEGMENTS.buy.map((kind) => SEGMENT[kind]));
    expect(group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.buy })).toHaveValue("450000");
    expect(group(BUDGET.legend).getByText("Between £50,000 and £20,000,000.")).toBeInTheDocument();
  });
});
