import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DIMENSION, POLARITY, SEGMENT } from "@/content/labels";
import { PLACE, REJECTED, TENURE_CHOICE } from "@/content/search";
import {
  BRANDS,
  BUDGET,
  CRIME_CAVEAT,
  FEATURES,
  HIDDEN,
  JOURNEY,
  SEGMENTS,
  SETTINGS,
  SLIDER,
} from "@/content/settings";
import { failed } from "@/lib/api/failure";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, FoundPlace, Operations, PreferenceSpec, RejectReason, Tenure } from "@/lib/api/schema";
import { edits, merged, NO_EDITS } from "@/lib/search/edits";

import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
import { SettingsPanel } from "./SettingsPanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data.spec;
const FAMILIES = meta.families.map((one) => one.label);

/** Everything a person can press, type in or move. */
const CONTROLS = "button, input, select, textarea, a[href]";

interface Shown {
  refused?: ReadonlyMap<string, RejectReason>;
  version?: number;
  form?: typeof meta;
  full?: string | null;
}

function show(spec: PreferenceSpec = first, { refused, version = 1, form = meta, full = null }: Shown = {}) {
  const sent: Operations[] = [];
  const tenures: Tenure[] = [];
  const added: FoundPlace[] = [];
  const onRank = jest.fn();
  const panel = (shown: PreferenceSpec, at: number) => (
    <SettingsPanel
      spec={shown}
      meta={form}
      areas={areas}
      placeNames={{ "syn-p0021": "Cindermoor Works" }}
      onEdit={(operations) => sent.push(operations)}
      onTenure={(tenure) => tenures.push(tenure)}
      searchPlaces={() => Promise.resolve(failed("offline"))}
      onAddPlace={(place) => added.push(place)}
      full={full}
      version={at}
      refused={refused}
      open
      onToggle={() => undefined}
      onRank={onRank}
    />
  );
  const view = render(panel(spec, version));
  const user = userEvent.setup({ delay: null });
  return {
    sent,
    tenures,
    added,
    onRank,
    user,
    /** Opens groups of the settings, and what a vibe is made of, by the names of their buttons. */
    open: async (...names: string[]) => {
      for (const name of names) await user.click(screen.getByRole("button", { name }));
    },
    again: (next: PreferenceSpec, at: number) => view.rerender(panel(next, at)),
    ...view,
  };
}

const group = (name: string) => within(screen.getByRole("group", { name }));
/** The buttons that open the groups of the settings, in the order they stand. */
const groups = () =>
  screen
    .getAllByRole("button")
    .filter((button) => button.hasAttribute("aria-expanded"))
    .slice(1)
    .map((button) => button.textContent);

describe("the settings, in groups", () => {
  test("test_the_groups_are_money_journeys_each_family_of_vibes_and_recorded_crime_last", () => {
    show();

    // What is there comes first, and who lived there after it.
    expect(FAMILIES).toEqual([
      "Streets and homes",
      "Pace and food",
      "Green",
      "Daily life",
      "Who lives there, at the 2021 census",
    ]);
    expect(groups()).toEqual([
      SETTINGS.money,
      SETTINGS.journeys,
      ...FAMILIES,
      DIMENSION.brands,
      SETTINGS.airAndNoise,
      DIMENSION.crime,
    ]);
  });

  test("test_the_brands_are_a_group_of_their_own_with_the_mix_first_and_a_switch_for_each_chain", async () => {
    // A switch for every chain, under the family the brands belong to, would bury the family.
    const { open } = show();
    await open(DIMENSION.brands);

    const opened = within(
      document.getElementById(
        screen.getByRole("button", { name: DIMENSION.brands }).getAttribute("aria-controls") ?? "",
      ) as HTMLElement,
    );
    const brands = meta.features.filter((metric) => metric.dimension === "brands");
    const ranked = brands.filter((metric) => metric.rankable);
    const switches = opened.getAllByRole("switch");
    // The mix, and each of 29 chains.
    expect(switches).toHaveLength(ranked.length);
    expect(ranked).toHaveLength(30);
    expect(switches[0]).toHaveAccessibleName("Mix of brands");
    expect(opened.getByText(BRANDS.lead)).toBeVisible();
    // Nothing of the brands counts until a person asks: every switch is off, and no slider is drawn.
    for (const one of switches) expect(one).not.toBeChecked();
    expect(opened.queryAllByRole("slider")).toHaveLength(0);
    // What is counted of a tier is shown on an area's page, and has no switch.
    const shown = brands.filter((metric) => !metric.rankable);
    expect(shown).toHaveLength(18);
    for (const metric of shown) expect(screen.queryByRole("switch", { name: metric.short_label })).toBeNull();
  });

  test("test_every_group_is_closed_at_first_and_few_controls_are_on_screen", () => {
    // Seen in a browser: the settings held a hundred controls, all on screen at once.
    const { container } = show(meta.defaults.rent);
    const settings = container.querySelector("[aria-busy]") as HTMLElement;

    expect(screen.getAllByRole("button", { expanded: false })).toHaveLength(groups().length);
    expect(settings.querySelectorAll(CONTROLS).length).toBeLessThanOrEqual(12);
    expect(screen.queryAllByRole("slider")).toEqual([]);
    expect(screen.queryAllByRole("switch")).toEqual([]);
  });

  test("test_a_family_holds_one_row_for_each_of_its_vibes_with_one_slider", async () => {
    const { open } = show();

    for (const { family, label } of meta.families) {
      await open(label);
      const vibes = meta.tags.filter((tag) => tag.family === family);
      expect(vibes.length).toBeGreaterThan(0);
      for (const tag of vibes) {
        expect(group(tag.label).getAllByRole("slider")).toHaveLength(1);
        expect(group(tag.label).getByRole("slider")).toHaveAccessibleName(tag.label);
      }
    }
    expect(screen.getAllByRole("slider", { name: new RegExp(`^(${meta.tags.map((tag) => tag.label).join("|")})$`) })).toHaveLength(
      meta.tags.length,
    );
  });

  test("test_a_feature_in_no_recipe_is_under_other_things_that_count_in_its_family", async () => {
    const { open } = show();
    const inARecipe = new Set(meta.tags.flatMap((tag) => tag.terms.map((term) => term.feature_id)));

    for (const label of FAMILIES) await open(label);

    const others = screen.getAllByRole("group", { name: FEATURES.others });
    const shown = others.flatMap((one) => within(one).getAllByRole("switch"));
    // A count that is shown and never ranked on has no switch: its rate is what counts.
    const expected = meta.features.filter(
      (metric) =>
        metric.rankable &&
        metric.family !== null &&
        metric.dimension !== "crime" &&
        metric.dimension !== "brands" &&
        !inARecipe.has(metric.feature_id),
    );
    expect(meta.features.filter((metric) => !metric.rankable && metric.family !== null).map((one) => one.feature_id)).toEqual(
      expect.arrayContaining(["venue_food_drink", "culture_venues"]),
    );
    expect(shown).toHaveLength(expected.length);
    for (const metric of expected) {
      expect(others.some((one) => within(one).queryByRole("switch", { name: metric.short_label }) !== null)).toBe(true);
    }
  });

  test("test_a_feature_that_belongs_to_no_family_has_a_group_of_its_own", async () => {
    const { open } = show();

    await open(SETTINGS.airAndNoise);

    const apart = meta.features.filter((metric) => metric.family === null && metric.dimension !== "crime");
    expect(apart.map((metric) => metric.feature_id).sort()).toEqual(["air_no2", "noise_exposure"]);
    for (const metric of apart) expect(screen.getByRole("switch", { name: metric.short_label })).toBeChecked();
  });

  test("test_every_feature_the_release_can_rank_can_be_reached", async () => {
    const { open } = show();
    await open(...FAMILIES, DIMENSION.brands, SETTINGS.airAndNoise, DIMENSION.crime);
    for (const tag of meta.tags) await open(FEATURES.madeOfName(tag.label));

    for (const metric of meta.features.filter((one) => one.rankable)) {
      expect(screen.getAllByRole("switch", { name: metric.short_label }).length).toBeGreaterThan(0);
    }
  });
});

describe("the slider of a vibe", () => {
  test("test_a_scale_is_one_slider_with_its_two_ends_named_resting_in_the_middle", async () => {
    const { open } = show();

    await open("Pace and food");
    const slider = group("Going out").getByRole("slider", { name: "Going out" });

    expect(slider).toHaveAttribute("min", "-100");
    expect(slider).toHaveAttribute("max", "100");
    // No weight: the middle.
    expect(slider).toHaveValue("0");
    expect(slider).toHaveAttribute("aria-valuetext", SLIDER.middle);
    expect(group("Going out").getByRole("button", { name: SLIDER.toward("Going out", "Calm") })).toHaveTextContent("Calm");
    expect(group("Going out").getByRole("button", { name: SLIDER.toward("Going out", "Buzzy") })).toHaveTextContent("Buzzy");
    expect(group("Going out").getByText(SLIDER.twoEnds)).toBeVisible();
  });

  test("test_moving_a_scale_towards_an_end_sends_one_edit_that_names_the_end", async () => {
    const { open, sent } = show();
    await open("Pace and food");
    const slider = group("Going out").getByRole("slider");

    fireEvent.pointerDown(slider);
    fireEvent.change(slider, { target: { value: "-50" } });
    fireEvent.pointerUp(slider);

    expect(sent).toEqual([edits.tagWeight("pace", 0.5, "low")]);
    expect(problemsWith("Operations", sent[0])).toEqual([]);
  });

  test("test_a_scale_is_drawn_from_the_spec_towards_the_end_it_asks_for", async () => {
    const calm = recordedAnswer("rank", "rank-scale").body.data.spec;
    const buzzy = recordedAnswer("rank", "rank-scale-turned").body.data.spec;
    const { open, again } = show(calm);
    await open("Pace and food");

    expect(group("Going out").getByRole("slider")).toHaveValue("-50");
    expect(group("Going out").getByRole("slider")).toHaveAttribute("aria-valuetext", SLIDER.towards("Calm", 50));

    again(buzzy, 2);
    expect(group("Going out").getByRole("slider")).toHaveValue("50");
    expect(group("Going out").getByRole("status")).toHaveTextContent(SLIDER.towards("Buzzy", 50));
  });

  test("test_the_buttons_at_the_ends_move_a_scale_without_dragging", async () => {
    jest.useFakeTimers();
    try {
      const user = userEvent.setup({ delay: null, advanceTimers: jest.advanceTimersByTime });
      const { sent } = show(recordedAnswer("rank", "rank-scale").body.data.spec);
      await user.click(screen.getByRole("button", { name: "Pace and food" }));

      await user.click(group("Going out").getByRole("button", { name: SLIDER.toward("Going out", "Buzzy") }));
      act(() => jest.runOnlyPendingTimers());

      // A small step towards Buzzy, from 50 towards Calm.
      expect(sent).toEqual([edits.tagWeight("pace", 0.4, "low")]);
    } finally {
      jest.useRealTimers();
    }
  });

  test("test_a_scale_brought_back_to_the_middle_takes_the_vibe_out_of_the_search", async () => {
    const { open, sent } = show(recordedAnswer("rank", "rank-scale").body.data.spec);
    await open("Pace and food");
    const slider = group("Going out").getByRole("slider");

    fireEvent.pointerDown(slider);
    fireEvent.change(slider, { target: { value: "0" } });
    fireEvent.pointerUp(slider);

    expect(sent).toEqual([edits.tagOff("pace")]);
  });

  test("test_a_vibe_that_runs_one_way_has_a_slider_from_nothing_and_no_end_to_name", async () => {
    const { open, sent } = show();
    await open("Green");
    const slider = group("Leafy").getByRole("slider", { name: "Leafy" });

    expect(slider).toHaveAttribute("min", "0");
    expect(slider).toHaveValue("50");
    fireEvent.pointerDown(slider);
    fireEvent.change(slider, { target: { value: "70" } });
    fireEvent.pointerUp(slider);
    fireEvent.pointerDown(slider);
    fireEvent.change(slider, { target: { value: "0" } });
    fireEvent.pointerUp(slider);

    expect(sent).toEqual([edits.tagWeight("leafy", 0.7, "high"), edits.tagOff("leafy")]);
    for (const operations of sent) expect(problemsWith("Operations", operations)).toEqual([]);
  });

  test("test_a_vibe_that_is_a_rough_guide_says_so_beside_its_slider_and_says_why", async () => {
    const { open, sent } = show();
    const [told] = meta.rough_guides;
    await open("Streets and homes");

    // Beside the slider, before it is moved: nothing but the group was opened.
    const village = screen.getByRole("group", { name: "Village feel" });
    const note = village.querySelector("[data-rough-guide='note']");
    expect(note?.textContent).toBe(`${told?.label}. ${told?.why}`);
    expect(note?.closest("[hidden], [aria-hidden='true'], details:not([open])")).toBeNull();
    const slider = within(village).getByRole("slider", { name: "Village feel" });
    expect((note as Element).compareDocumentPosition(slider) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy();
    expect(sent).toEqual([]);
    // No other vibe of the group says it.
    for (const tag of meta.tags.filter((one) => one.tag_id !== "village_feel" && one.family === "streets_homes")) {
      expect(screen.getByRole("group", { name: tag.label }).querySelector("[data-rough-guide]")).toBeNull();
    }
  });

  test("test_every_vibe_of_the_release_that_is_a_scale_names_both_its_ends", async () => {
    const { open } = show();
    await open(...FAMILIES);

    const scales = meta.tags.filter((tag) => tag.shape === "scale");
    expect(scales.map((tag) => tag.tag_id).sort()).toEqual(["built_age", "homes", "pace", "street_character"]);
    for (const tag of scales) {
      expect(group(tag.label).getByRole("button", { name: SLIDER.toward(tag.label, tag.low_end ?? "") })).toBeVisible();
      expect(group(tag.label).getByRole("button", { name: SLIDER.toward(tag.label, tag.high_end ?? "") })).toBeVisible();
    }
  });
});

describe("what a vibe is made of", () => {
  test("test_made_of_opens_the_parts_of_the_recipe_each_with_its_switch", async () => {
    const { open } = show();
    await open("Green", FEATURES.madeOfName("Leafy"));
    const leafy = meta.tags.find((tag) => tag.tag_id === "leafy");
    const names = new Map(meta.features.map((metric) => [metric.feature_id, metric.short_label]));

    for (const term of leafy?.terms ?? []) {
      expect(screen.getByRole("switch", { name: names.get(term.feature_id) })).toBeInTheDocument();
    }
    expect(screen.getByText(FEATURES.madeOfHint)).toBeVisible();
  });

  test("test_a_part_sends_the_edit_of_a_feature_as_before", async () => {
    // Recorded: the switch of a usual setting turned off. The API answers with an entry
    // of 0 in its place, and not with no entry. The switch must not spring back on.
    const answered = recordedAnswer("rank", "rank-switched-off");
    const after = answered.body.data.spec;
    const station = () => screen.getByRole("switch", { name: "Nearer a station" });
    const { open, user, sent, again } = show();
    await open("Daily life", FEATURES.madeOfName("Everyday on foot"));
    expect(station()).toBeChecked();

    await user.click(station());
    expect(sent).toEqual([(answered.request.body as { operations: Operations }).operations]);
    again(after, 2);

    expect(after.weights.find((weight) => weight.feature_id === "station_walk")).toMatchObject({ weight: 0 });
    expect(station()).not.toBeChecked();
    expect(screen.queryByRole("slider", { name: FEATURES.weight("Nearer a station") })).toBeNull();

    // Switched on again, it is asked for as anything is that is switched on.
    await user.click(station());
    expect(sent[1]).toEqual(edits.featureOn("station_walk"));
  });

  test("test_a_part_the_release_does_not_carry_is_counted_and_never_shown_by_its_code", async () => {
    const { open, container } = show();
    const onFoot = meta.tags.find((tag) => tag.tag_id === "everyday_on_foot");
    const carried = new Set(meta.features.map((metric) => metric.feature_id));
    const missing = (onFoot?.terms ?? []).filter((term) => !carried.has(term.feature_id));

    await open("Daily life", FEATURES.madeOfName("Everyday on foot"));

    expect(missing.map((term) => term.feature_id).sort()).toEqual(["gp_walk", "pharmacy_walk"]);
    expect(screen.getByText(FEATURES.notInData(2))).toBeVisible();
    expect(container.textContent?.includes("gp_walk")).toBe(false);
  });
});

describe("the settings", () => {
  test("test_every_edit_a_control_sends_is_one_the_contract_accepts", async () => {
    const { user, open, sent, tenures } = show();
    await open(SETTINGS.money, SETTINGS.journeys, "Pace and food", "Green");

    await user.click(group(BUDGET.legend).getByRole("checkbox", { name: BUDGET.firm }));
    await user.selectOptions(group(BUDGET.legend).getByRole("combobox", { name: BUDGET.segment }), "bed_2");
    await user.click(group(BUDGET.legend).getByRole("button", { name: BUDGET.clear }));
    await user.click(group(BUDGET.legend).getByRole("button", { name: BUDGET.less }));
    await user.click(screen.getByRole("radio", { name: "By bike" }));
    await user.click(screen.getByRole("radio", { name: "The average of the journeys counts" }));
    await user.click(screen.getByRole("radio", { name: "The time if you just miss a service counts" }));
    await user.click(screen.getByRole("button", { name: JOURNEY.longer }));
    await user.click(screen.getByRole("button", { name: JOURNEY.remove("Cindermoor Works") }));
    await open(FEATURES.madeOfName("Going out"));
    await user.click(screen.getByRole("switch", { name: "Pubs and bars" }));
    await user.click(screen.getByRole("radio", { name: TENURE_CHOICE.buy }));

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
      edits.featureOn("venue_evening_per_homes"),
    ]);
    // Renting or buying is the page's to send: before anything is asked for, it sends nothing.
    expect(tenures).toEqual(["buy"]);
    for (const operations of sent) expect(problemsWith("Operations", operations)).toEqual([]);
  });

  test("test_every_control_is_drawn_from_the_spec_the_api_returned", async () => {
    const { open } = show();
    await open(SETTINGS.money, SETTINGS.journeys, "Green", "Daily life", FEATURES.madeOfName("Everyday on foot"));

    expect(screen.getByRole("radio", { name: TENURE_CHOICE.rent })).toBeChecked();
    expect(group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent })).toHaveValue("1700");
    expect(group(BUDGET.legend).getByRole("combobox", { name: BUDGET.segment })).toHaveValue("bed_1");
    expect(group(BUDGET.legend).getByRole("checkbox", { name: BUDGET.firm })).not.toBeChecked();
    expect(group(BUDGET.legend).getByRole("slider", { name: BUDGET.weight })).toHaveValue("30");
    const journey = group(JOURNEY.place("Cindermoor Works"));
    expect(journey.getByRole("radio", { name: "Public transport" })).toBeChecked();
    expect(journey.getByRole("textbox", { name: JOURNEY.longest })).toHaveValue("35");
    expect(screen.getByRole("slider", { name: "Leafy" })).toHaveValue("50");
    expect(screen.getByRole("slider", { name: "Parks close by" })).toHaveValue("0");
    // A setting nobody chose is on, at the weight it gave way to: a quarter of 0.50, rounded down to a step.
    expect(screen.getByRole("slider", { name: FEATURES.weight("Nearer a station") })).toHaveValue("10");
  });

  test("test_a_control_shows_its_new_value_at_once_and_is_drawn_again_from_the_answer", async () => {
    const { user, open, again } = show();
    await open(SETTINGS.money);
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

  test("test_a_thing_taken_off_in_words_is_drawn_as_off", async () => {
    const { open } = show(recordedAnswer("interpret", "interpret-second-sentence").body.data.spec);
    await open("Pace and food", FEATURES.madeOfName("Going out"), "Green", FEATURES.madeOfName("Leafy"));

    const highStreet = "Nearer a town centre";
    expect(screen.getByRole("switch", { name: highStreet })).not.toBeChecked();
    expect(screen.queryByRole("slider", { name: FEATURES.weight(highStreet) })).toBeNull();
    expect(screen.getByRole("switch", { name: "More public parks and gardens" })).toBeChecked();
  });

  test("test_a_switch_that_is_off_shows_no_slider", async () => {
    const { open } = show();
    await open(SETTINGS.airAndNoise, DIMENSION.crime);

    expect(screen.getByRole("switch", { name: "Cleaner air" })).toBeChecked();
    expect(screen.getByRole("slider", { name: FEATURES.weight("Cleaner air") })).toBeInTheDocument();
    expect(screen.getByRole("switch", { name: "Less recorded burglary and theft" })).not.toBeChecked();
    expect(screen.queryByRole("slider", { name: FEATURES.weight("Less recorded burglary and theft") })).toBeNull();
  });

  test("test_which_way_is_better_is_asked_only_where_either_can_be", async () => {
    const nights = recordedAnswer("rank", "rank-nights-out").body.data.spec;
    const { user, open, sent } = show(nights);
    await open("Pace and food", FEATURES.madeOfName("Going out"));

    const either = meta.features.filter((metric) => metric.polarity === "either").map((metric) => metric.short_label);
    expect(either.length).toBeGreaterThan(0);
    const asked = screen
      .getAllByRole("group")
      .filter((one) => one.tagName === "FIELDSET" && /Which way counts/.test(one.textContent ?? ""));
    expect(asked.length).toBeGreaterThan(0);
    for (const one of asked) expect(either.some((label) => one.textContent?.includes(label))).toBe(true);

    const pubs = group(FEATURES.direction("Pubs and bars"));
    expect(pubs.getByRole("radio", { name: "Higher is better" })).toBeChecked();
    await user.click(pubs.getByRole("radio", { name: "Lower is better" }));
    expect(sent).toEqual([edits.featureDirection("venue_evening_per_homes", 0.5, "less")]);
  });

  test("test_a_change_of_direction_is_sent_with_the_weight_the_person_just_set_and_not_the_one_before", async () => {
    const nights = recordedAnswer("rank", "rank-nights-out").body.data.spec;
    const { user, open, sent } = show(nights);
    await open("Pace and food", FEATURES.madeOfName("Going out"));
    const pubs = "Pubs and bars";
    const number = screen.getByRole("textbox", { name: SLIDER.number(FEATURES.weight(pubs)) });

    await user.clear(number);
    await user.type(number, "70{Enter}");
    // No answer has come: the spec still says 50. A `set` always reads its value, and the later edit wins.
    await user.click(group(FEATURES.direction(pubs)).getByRole("radio", { name: "Lower is better" }));
    // Then the person thinks again about how much, still before any answer.
    await user.clear(number);
    await user.type(number, "50{Enter}");

    expect(sent).toEqual([
      edits.featureWeight("venue_evening_per_homes", 0.7),
      edits.featureDirection("venue_evening_per_homes", 0.7, "less"),
      edits.featureWeight("venue_evening_per_homes", 0.5),
    ]);
    // As the API applies them, in order: it counts for 50, and fewer is better.
    expect(sent.reduce(merged, NO_EDITS).weight_ops.at(-1)).toMatchObject({ value: 0.5, direction: "default" });
    for (const operations of sent) expect(problemsWith("Operations", operations)).toEqual([]);
  });

  test("test_after_the_answer_a_change_of_direction_is_sent_with_the_weight_the_answer_gave", async () => {
    const nights = recordedAnswer("rank", "rank-nights-out").body.data.spec;
    const { user, open, sent, again } = show(nights);
    await open("Pace and food", FEATURES.madeOfName("Going out"));
    const pubs = "Pubs and bars";
    const number = screen.getByRole("textbox", { name: SLIDER.number(FEATURES.weight(pubs)) });

    await user.clear(number);
    await user.type(number, "70{Enter}");
    // The answer refused the weight: it is what it was.
    again(nights, 2);
    await user.click(group(FEATURES.direction(pubs)).getByRole("radio", { name: "Lower is better" }));

    expect(sent.at(-1)).toEqual(edits.featureDirection("venue_evening_per_homes", 0.5, "less"));
  });

  test("test_every_feature_is_named_plainly_and_says_under_its_switch_which_way_counts_as_better", async () => {
    const { open } = show();
    await open(...FAMILIES, DIMENSION.brands, SETTINGS.airAndNoise, DIMENSION.crime);
    for (const tag of meta.tags) await open(FEATURES.madeOfName(tag.label));

    // The settings stand alone when the words cannot be read, so a switch says the wish
    // where there is one way to wish, and which way counts as better.
    const features = meta.features.filter((metric) => metric.rankable);
    expect(new Set(features.map((metric) => metric.polarity))).toEqual(new Set(["more", "less", "either"]));
    for (const metric of features) {
      expect(metric.short_label.length).toBeLessThanOrEqual(40);
      for (const toggle of screen.getAllByRole("switch", { name: metric.short_label })) {
        expect(toggle).toHaveAccessibleDescription(POLARITY[metric.polarity]);
        // It is on the page for everyone, and not for a screen reader alone.
        const hint = within(toggle.closest("[role='group']") as HTMLElement).getByText(POLARITY[metric.polarity]);
        expect(hint).toBeVisible();
        expect(hint.closest(".visually-hidden")).toBeNull();
      }
    }
  });

  /** The lines that say what the scale of a slider means, of those that can be seen. */
  const scalesSeenIn = (part: HTMLElement) =>
    within(part)
      .queryAllByText(SLIDER.range)
      .filter((line) => line.closest(".visually-hidden, [aria-hidden='true'], [hidden]") === null);
  /** What a button of the settings opens. */
  const openedBy = (name: string) =>
    document.getElementById(screen.getByRole("button", { name }).getAttribute("aria-controls") ?? "") as HTMLElement;

  test("test_the_scale_of_the_sliders_is_drawn_once_for_each_group_that_shows_one", async () => {
    // Seen in a browser: all eight lines that say what 0 and 100 mean were 1 pixel by 1.
    const { open } = show();
    await open(SETTINGS.money, SETTINGS.journeys, "Green", SETTINGS.airAndNoise);

    // A group holds several sliders, and says what the scale means once, where it can be seen.
    for (const name of ["Green", SETTINGS.airAndNoise]) {
      expect(within(openedBy(name)).getAllByRole("slider").length).toBeGreaterThan(1);
      expect(scalesSeenIn(openedBy(name))).toHaveLength(1);
      for (const slider of within(openedBy(name)).getAllByRole("slider")) {
        expect(slider).toHaveAccessibleDescription(SLIDER.range);
      }
    }
    // The budget and the journeys hold one slider each, which says it for itself.
    expect(scalesSeenIn(screen.getByRole("group", { name: BUDGET.legend }))).toHaveLength(1);
    expect(scalesSeenIn(screen.getByRole("group", { name: JOURNEY.settingsLegend }))).toHaveLength(1);
  });

  test("test_a_group_with_every_switch_off_shows_no_slider_and_no_scale_for_one", async () => {
    const { open } = show();
    await open(DIMENSION.crime);

    expect(within(openedBy(DIMENSION.crime)).queryAllByRole("slider")).toHaveLength(0);
    expect(scalesSeenIn(openedBy(DIMENSION.crime))).toHaveLength(0);
  });

  test("test_the_form_offers_only_what_the_release_can_rank", async () => {
    const some = { ...meta, features: meta.features.map((metric, at) => ({ ...metric, rankable: at % 2 === 0 })) };
    const { open } = show(meta.defaults.rent, { form: some });
    await open(...FAMILIES, DIMENSION.brands, SETTINGS.airAndNoise, DIMENSION.crime);
    for (const tag of some.tags) await open(FEATURES.madeOfName(tag.label));

    for (const metric of some.features) {
      expect(screen.queryAllByRole("switch", { name: metric.short_label }).length > 0).toBe(metric.rankable);
    }
  });

  test("test_the_limits_are_the_ones_the_api_serves", async () => {
    const { open } = show();
    await open(SETTINGS.money, SETTINGS.journeys);

    expect(group(BUDGET.legend).getByText("Between £300 and £20,000.")).toBeInTheDocument();
    // The longest journey is kept within what the data holds for that way of travelling.
    expect(group(JOURNEY.place("Cindermoor Works")).getByText(JOURNEY.between(10, 90))).toBeInTheDocument();
  });

  test("test_changing_how_you_travel_changes_the_longest_journey_that_can_be_asked_for", async () => {
    const { user, open } = show();
    await open(SETTINGS.journeys);

    await user.click(screen.getByRole("radio", { name: "On foot" }));

    expect(group(JOURNEY.place("Cindermoor Works")).getByText(JOURNEY.between(10, 60))).toBeInTheDocument();
  });

  test("test_a_place_to_reach_can_be_added_from_the_settings", async () => {
    // Once a search is open the field is no longer beside the box: the answer comes first.
    const { open } = show();

    await open(SETTINGS.journeys);

    expect(screen.getByRole("combobox", { name: PLACE.label })).toBeInTheDocument();
  });

  test("test_when_no_more_places_can_be_named_the_field_gives_way_to_a_line_that_says_so", async () => {
    const { open } = show(first, { full: PLACE.full(3) });
    await open(SETTINGS.journeys);

    expect(screen.queryByRole("combobox", { name: PLACE.label })).toBeNull();
    expect(screen.getByText(PLACE.full(3))).toBeVisible();
  });

  test("test_a_typed_budget_is_sent_as_it_was_typed_so_the_api_can_say_if_it_is_out_of_range", async () => {
    const { user, open, sent } = show();
    await open(SETTINGS.money);
    const amount = group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent });

    await user.clear(amount);
    await user.type(amount, "1");
    expect(sent).toEqual([]);
    await user.type(amount, "850");
    await user.tab();

    expect(sent).toEqual([edits.budgetAmount(1850)]);
  });

  test("test_a_budget_that_is_no_number_is_said_beside_the_field_and_not_sent", async () => {
    const { user, open, sent } = show();
    await open(SETTINGS.money);
    const amount = group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent });

    await user.clear(amount);
    await user.type(amount, "about two grand{Enter}");

    expect(sent).toEqual([]);
    expect(group(BUDGET.legend).getByRole("alert")).toHaveTextContent(BUDGET.notWhole);
    expect(amount).toBeInvalid();
    expect(amount).toHaveAccessibleDescription(expect.stringContaining(BUDGET.notWhole));
  });

  test("test_a_budget_may_be_typed_with_a_pound_sign_and_commas", async () => {
    const { user, open, sent } = show();
    await open(SETTINGS.money);
    const amount = group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent });

    await user.clear(amount);
    await user.type(amount, "£2,100{Enter}");

    expect(sent).toEqual([edits.budgetAmount(2100)]);
  });

  test("test_with_no_budget_set_the_steps_and_clear_are_off_because_there_is_nothing_to_step_from", async () => {
    const { open } = show(meta.defaults.rent);
    await open(SETTINGS.money);

    expect(group(BUDGET.legend).getByRole("button", { name: BUDGET.less })).toBeDisabled();
    expect(group(BUDGET.legend).getByRole("button", { name: BUDGET.more })).toBeDisabled();
    expect(group(BUDGET.legend).getByRole("button", { name: BUDGET.clear })).toHaveAttribute("aria-disabled", "true");
    expect(group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.rent })).toHaveValue("");
  });

  test("test_clear_keeps_the_focus_when_the_budget_has_gone_and_then_sends_nothing", async () => {
    // Pressed, it takes the budget off, and is then off itself. It is not switched off, because
    // a button that is switched off while it has the focus leaves the focus on nothing.
    const { user, open, sent, again } = show();
    await open(SETTINGS.money);
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

  test("test_an_edit_that_was_refused_is_said_beside_the_control_it_concerns", async () => {
    const { open } = show(first, {
      refused: new Map<string, RejectReason>([["budget", "out_of_range"], ["tag:leafy", "not_in_release"]]),
    });
    await open(SETTINGS.money, "Green");

    expect(group(BUDGET.legend).getByRole("alert")).toHaveTextContent(REJECTED.out_of_range);
    expect(group("Leafy").getByRole("alert")).toHaveTextContent(REJECTED.not_in_release);
    expect(screen.getAllByRole("alert")).toHaveLength(2);
  });

  test("test_with_no_ranking_yet_the_settings_can_be_ranked_as_they_stand", async () => {
    const { user, onRank } = show(meta.defaults.rent);

    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));

    expect(onRank).toHaveBeenCalledTimes(1);
  });

  test("test_a_hidden_area_can_be_shown_again_and_the_group_is_there_only_while_one_is_hidden", async () => {
    const hidden = { ...first, areas: [{ area_id: "syn-n0006", rule: "exclude", provenance: "ui_edit" }] } as const;
    const { user, open, sent, again } = show(hidden);
    await open(HIDDEN.legend);

    await user.click(screen.getByRole("button", { name: HIDDEN.show("Farrowmere") }));

    expect(sent).toEqual([edits.areaClear("syn-n0006")]);
    again(first, 2);
    expect(screen.queryByRole("button", { name: HIDDEN.legend })).toBeNull();
  });

  test("test_the_settings_open_have_no_accessibility_fault", async () => {
    const { container, open } = show();
    await open(SETTINGS.money, SETTINGS.journeys, ...FAMILIES, SETTINGS.airAndNoise, DIMENSION.crime);
    await open(FEATURES.madeOfName("Going out"));

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("recorded crime", () => {
  test("test_recorded_crime_is_its_own_group_closed_and_off_at_first", () => {
    show();

    const crime = screen.getByRole("button", { name: DIMENSION.crime });
    expect(crime).toHaveAttribute("aria-expanded", "false");
    for (const metric of meta.features.filter((one) => one.dimension === "crime")) {
      expect(screen.queryByRole("switch", { name: metric.short_label })).toBeNull();
      expect(first.weights.some((weight) => weight.feature_id === metric.feature_id)).toBe(false);
      expect(meta.defaults.rent.weights.some((weight) => weight.feature_id === metric.feature_id)).toBe(false);
    }
  });

  test("test_every_figure_of_recorded_crime_is_in_that_group_whatever_recipe_holds_it", async () => {
    // Where gritty is a scale, recorded damage is a part of it. Its switch is under the caveat all the same.
    const { open } = show();
    await open(DIMENSION.crime);

    const crime = meta.features.filter((one) => one.dimension === "crime");
    expect(crime.map((one) => one.feature_id).sort()).toEqual([
      "crime_burglary_theft",
      "crime_violence_robbery",
      "incident_antisocial",
      "incident_criminal_damage",
    ]);
    const inTheGroup = within(
      document.getElementById(screen.getByRole("button", { name: DIMENSION.crime }).getAttribute("aria-controls") ?? "") as HTMLElement,
    );
    for (const metric of crime) expect(inTheGroup.getByRole("switch", { name: metric.short_label })).not.toBeChecked();
  });

  test("test_the_caveat_stands_above_its_switches_and_a_switch_sends_an_edit_made_by_a_control", async () => {
    const { user, open, sent } = show();

    await open(DIMENSION.crime);
    const caveat = screen.getByText(CRIME_CAVEAT);
    const theft = screen.getByRole("switch", { name: "Less recorded burglary and theft" });
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

  test("test_a_buyer_is_offered_kinds_of_home_to_buy_and_no_kind_to_rent", async () => {
    const { open } = show(recordedAnswer("rank", "rank-buyer-family").body.data.spec);
    await open(SETTINGS.money);

    const kinds = within(group(BUDGET.legend).getByRole("combobox", { name: BUDGET.segment }))
      .getAllByRole("option")
      .map((option) => option.textContent);
    expect(kinds).toEqual(SEGMENTS.buy.map((kind) => SEGMENT[kind]));
    expect(group(BUDGET.legend).getByRole("textbox", { name: BUDGET.amount.buy })).toHaveValue("450000");
    expect(group(BUDGET.legend).getByText("Between £50,000 and £20,000,000.")).toBeInTheDocument();
  });
});
