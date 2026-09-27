import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { countsOf } from "@/content/crime";
import { DIMENSION, DIRECTION, POLARITY, SEGMENT } from "@/content/labels";
import { NOT_IN_DATA, PLACE, REJECTED, TENURE_CHOICE } from "@/content/search";
import {
  BRANDS,
  BUDGET,
  CRIME_CAVEAT,
  FEATURES,
  HIDDEN,
  JOURNEY,
  KIND_OF_SEARCH,
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
import { asWritten } from "../../../test/support/contrast";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { cutOf, isDrawn, sizeOf } from "../kit/drawings";
import { picturesAtEnds } from "../kit/Ends/picture";
import { drawingOf, outlineOf, PLAIN } from "../kit/Thing/drawn";
import { ENDS_OF_ONE_WAY } from "../WeightSlider/look";
import { heldBy as heldByTheRelease } from "./groups";
import { SettingsPanel } from "./SettingsPanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
/**
 * What the service calls each family of vibes, by the id of the family. A name is the
 * service's to write, and it has written two again: so a test finds a group by the name
 * the service gives it, and writes none down.
 */
const familyCalled = (id: string) => meta.families.find((one) => one.family === id)?.label ?? id;
const [STREETS, GOING_OUT, GREEN, DAILY_LIFE, WHO_LIVES_THERE] = [
  familyCalled("streets_homes"),
  familyCalled("pace_food"),
  familyCalled("green"),
  familyCalled("daily_life"),
  familyCalled("who_lives_there"),
];
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data.spec;
const FAMILIES = meta.families.map((one) => one.label);
/** The places of the search, as the answer that brought the spec named them. */
const NAMED = { "syn-p0021": "Cindermoor Works" } as const;

/** Everything a person can press, type in or move. */
const CONTROLS = "button, input, select, textarea, a[href]";

interface Shown {
  refused?: ReadonlyMap<string, RejectReason>;
  /** The parts whose change has not been answered, and what the page says of that. */
  unsent?: { readonly parts: ReadonlySet<string>; readonly says: string };
  version?: number;
  form?: typeof meta;
  full?: string | null;
  /** True where the settings stand open beside the answer, with no button to open them. */
  standing?: boolean;
  /** Whether the page says they are open. It says nothing to settings that stand open. */
  opened?: boolean;
}

function show(
  spec: PreferenceSpec = first,
  { refused, unsent, version = 1, form = meta, full = null, standing = false, opened = true }: Shown = {},
) {
  const sent: Operations[] = [];
  const tenures: Tenure[] = [];
  const added: FoundPlace[] = [];
  const onRank = jest.fn();
  const onToggle = jest.fn();
  const panel = (shown: PreferenceSpec, at: number) => (
    <SettingsPanel
      spec={shown}
      meta={form}
      areas={areas}
      placeNames={NAMED}
      onEdit={(operations) => sent.push(operations)}
      onTenure={(tenure) => tenures.push(tenure)}
      searchPlaces={() => Promise.resolve(failed("offline"))}
      onAddPlace={(place) => added.push(place)}
      full={full}
      version={at}
      refused={refused}
      unsent={unsent}
      open={opened}
      onToggle={onToggle}
      onRank={onRank}
      standing={standing}
    />
  );
  const view = render(panel(spec, version));
  const user = userEvent.setup({ delay: null });
  return {
    sent,
    tenures,
    added,
    onRank,
    onToggle,
    user,
    /**
     * Opens groups of the settings, and what a vibe is made of, by the names of their
     * buttons. One that stands open is left as it is: a press would close it.
     */
    open: async (...names: string[]) => {
      for (const name of names) {
        const button = screen.getByRole("button", { name });
        if (button.getAttribute("aria-expanded") !== "true") await user.click(button);
      }
    },
    again: (next: PreferenceSpec, at: number) => view.rerender(panel(next, at)),
    ...view,
  };
}

const group = (name: string) => within(screen.getByRole("group", { name }));
/** The bars of the groups of the settings, in the order they stand. */
const bars = (part: HTMLElement = document.body) =>
  [...part.querySelectorAll<HTMLElement>("button[data-arrow][data-rest]")];
/** What each group is called, in the order the groups stand. */
const groups = (part?: HTMLElement) => bars(part).map((bar) => bar.querySelector(".name")?.textContent);
/** The groups that stand open, by what each is called. */
const standOpen = (part?: HTMLElement) =>
  bars(part)
    .filter((bar) => bar.getAttribute("aria-expanded") === "true")
    .map((bar) => bar.querySelector(".name")?.textContent);
/** What the bar of a group says of what the group holds. `null` where it says nothing. */
const heldBy = (name: string) => screen.getByRole("button", { name }).querySelector(".holds")?.textContent ?? null;

describe("the settings, in groups", () => {
  test("test_the_groups_are_money_journeys_each_family_of_vibes_and_recorded_crime_last", () => {
    show();

    // What is there comes first, and who lived there after it. It is held by the id of each
    // family: what a family is called is the service's to write, and is drawn as it came.
    expect(meta.families.map((one) => one.family)).toEqual([
      "streets_homes",
      "pace_food",
      "green",
      "daily_life",
      "who_lives_there",
    ]);
    expect(FAMILIES).toEqual([STREETS, GOING_OUT, GREEN, DAILY_LIFE, WHO_LIVES_THERE]);
    expect(FAMILIES.filter((name) => name.trim() === "" || /_/.test(name))).toEqual([]);
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

  test("test_all_but_the_groups_that_stand_open_at_first_are_closed_and_few_controls_are_on_screen", () => {
    // Seen in a browser: the settings held a hundred controls, all on screen at once. Two
    // groups stand open at first, which hold thirteen between them since visiting is asked
    // beside renting and buying, and every other is a bar.
    const { container } = show(meta.defaults.rent);
    const settings = container.querySelector("[aria-busy]") as HTMLElement;

    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
    expect(screen.getAllByRole("button", { expanded: false })).toHaveLength(groups().length - 2);
    expect(settings.querySelectorAll(CONTROLS).length).toBeLessThanOrEqual(groups().length + 15);
    // The slider of the budget, and no other: no family is open, and no switch is drawn.
    expect(screen.getAllByRole("slider").map((slider) => slider.getAttribute("aria-label") ?? slider.id)).toHaveLength(1);
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

    await open(GOING_OUT);
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
    await open(GOING_OUT);
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
    await open(GOING_OUT);

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
      // The search asks for the scale, and the group that holds it is closed as every group is: it is opened.
      expect(screen.getByRole("button", { name: GOING_OUT })).toHaveAttribute("aria-expanded", "false");
      await user.click(screen.getByRole("button", { name: GOING_OUT }));

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
    await open(GOING_OUT);
    const slider = group("Going out").getByRole("slider");

    fireEvent.pointerDown(slider);
    fireEvent.change(slider, { target: { value: "0" } });
    fireEvent.pointerUp(slider);

    expect(sent).toEqual([edits.tagOff("pace")]);
  });

  test("test_a_vibe_that_runs_one_way_has_a_slider_from_nothing_and_no_end_to_name", async () => {
    const { open, sent } = show();
    await open(GREEN);
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

  /** The release as a service gave it that said of a rough guide its label and why, which the recorded one does not. */
  const told = sayingSo(meta);

  test.each([
    ["can be placed on it", told],
    // As in a release that is not finished, where its slider gives way to why it cannot be moved.
    ["cannot", { ...told, recipes: told.recipes.map((held) => (held.tag_id === ROUGH.tag_id ? { ...held, placed: false, held: 45 } : held)) }],
  ])("test_a_vibe_the_service_calls_a_rough_guide_stands_as_any_other_and_nothing_says_that_it_is_one: an area %s", async (_, form) => {
    // The founder, who had walked the website twice: "remove the concept of rough guide, we
    // don't want to pass this on to a user". The service still says which vibe it holds to
    // be less sure than the rest, in a code. What it said of it, its label and why, is laid
    // on the release, as a service may say it again. The settings say neither, beside its
    // slider or anywhere else, with every group of them open.
    const { open, sent, container } = show(first, { form });
    const guide = meta.tags.find((tag) => tag.tag_id === ROUGH.tag_id);
    if (guide === undefined) throw new Error("The recorded release holds no such vibe.");
    await open(...groups().filter((name): name is string => typeof name === "string"));
    for (const tag of form.tags) await open(FEATURES.madeOfName(tag.label));

    expect(guide.sureness).toBe("rough_guide");
    expect(form.rough_guides).toEqual([ROUGH]);
    expect(standOpen()).toEqual(groups());
    const village = screen.getByRole("group", { name: guide.label });
    expect(within(village).queryAllByRole("slider", { name: guide.label })).toHaveLength(form === told ? 1 : 0);
    // Neither its label nor the sentence that said why stands anywhere, in sight or out of it.
    const said = [
      container.textContent ?? "",
      ...[...container.querySelectorAll("*")].flatMap((part) =>
        ["aria-label", "aria-description", "aria-roledescription", "aria-valuetext", "title", "alt", "placeholder"].map((name) => part.getAttribute(name) ?? ""),
      ),
    ].join("\n");
    expect(container.querySelector("[data-rough-guide]")).toBeNull();
    expect(said.includes(ROUGH.label)).toBe(false);
    expect(said.includes(ROUGH.why)).toBe(false);
    expect(/rough guide|less sure/i.test(said)).toBe(false);
    // What stands beside its slider is what stands beside the slider of any vibe of its kind.
    const partsOf = (one: Element) => [...one.querySelectorAll("*")].map((part) => `${part.tagName} ${part.className}`);
    const others = form.tags.filter(
      (tag) =>
        tag.tag_id !== guide.tag_id &&
        tag.shape === guide.shape &&
        form.recipes.find((held) => held.tag_id === tag.tag_id)?.placed !== false &&
        countsOf(tag, form.features) === null,
    );
    expect(others.length).toBeGreaterThan(0);
    if (form === told) {
      for (const tag of others) expect([tag.tag_id, partsOf(screen.getByRole("group", { name: tag.label }))]).toEqual([tag.tag_id, partsOf(village)]);
    }
    // Nothing was pressed but what opens a group, so nothing was sent.
    expect(sent).toEqual([]);
  });

  test("test_the_settings_read_nothing_of_what_a_rough_guide_says_of_itself", () => {
    // Nothing of the settings reads what the service says of a vibe that is less sure, and
    // nothing of them is handed it: no part draws it, and none is kept that would.
    const written = readdirSync(__dirname)
      .filter((file) => /\.(tsx?|css)$/.test(file) && !/\.test\.tsx?$/.test(file))
      .map((file) => [file, readFileSync(path.join(__dirname, file), "utf8").replace(/\/\*[\s\S]*?\*\/|(?<![:"'`])\/\/.*$/gm, "")] as const);

    expect(written.length).toBeGreaterThan(5);
    const reads = /rough_guides|sureness|\b(told|rough|guide)\??\.(label|why)\b|\brough\b|RoughGuide|data-rough-guide|rough guide|less sure/i;
    expect(written.filter(([, source]) => reads.test(source)).map(([file]) => file)).toEqual([]);
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
    await open(GREEN, FEATURES.madeOfName("Leafy"));
    const leafy = meta.tags.find((tag) => tag.tag_id === "leafy");
    const names = new Map(meta.features.map((metric) => [metric.feature_id, metric.short_label]));

    const opened = document.getElementById(
      screen.getByRole("button", { name: FEATURES.madeOfName("Leafy") }).getAttribute("aria-controls") ?? "",
    ) as HTMLElement;

    for (const term of leafy?.terms ?? []) {
      expect(within(opened).getByRole("switch", { name: names.get(term.feature_id) })).toBeInTheDocument();
    }
    expect(within(opened).getByText(FEATURES.madeOfHint)).toBeVisible();
  });

  test("test_a_part_sends_the_edit_of_a_feature_as_before", async () => {
    // Recorded: the switch of a usual setting turned off. The API answers with an entry
    // of 0 in its place, and not with no entry. The switch must not spring back on.
    const answered = recordedAnswer("rank", "rank-switched-off");
    const after = answered.body.data.spec;
    const station = () => screen.getByRole("switch", { name: "Nearer a station" });
    const { open, user, sent, again } = show();
    await open(DAILY_LIFE, FEATURES.madeOfName("Everyday on foot"));
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

    await open(DAILY_LIFE, FEATURES.madeOfName("Everyday on foot"));

    expect(missing.map((term) => term.feature_id).sort()).toEqual(["gp_walk", "pharmacy_walk"]);
    expect(screen.getByText(FEATURES.notInData(2))).toBeVisible();
    expect(container.textContent?.includes("gp_walk")).toBe(false);
  });
});

describe("the settings", () => {
  test("test_every_edit_a_control_sends_is_one_the_contract_accepts", async () => {
    const { user, open, sent, tenures } = show();
    await open(SETTINGS.money, SETTINGS.journeys, GOING_OUT, GREEN);

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
    await open(SETTINGS.money, SETTINGS.journeys, GREEN, DAILY_LIFE, FEATURES.madeOfName("Everyday on foot"));

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
    await open(GOING_OUT, FEATURES.madeOfName("Going out"), GREEN, FEATURES.madeOfName("Leafy"));

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
    await open(GOING_OUT, FEATURES.madeOfName("Going out"));

    const either = meta.features.filter((metric) => metric.polarity === "either").map((metric) => metric.short_label);
    expect(either.length).toBeGreaterThan(0);
    // What is asked over the two ways, whatever it is asked of: the words are the website's,
    // by name. The start of them is seen, under the name of the thing, and the whole is heard.
    const asks = FEATURES.direction("");
    const asked = screen
      .getAllByRole("group")
      .filter((one) => one.tagName === "FIELDSET" && (one.getAttribute("aria-label") ?? "").startsWith(asks));
    expect(asked.length).toBeGreaterThan(0);
    for (const one of asked) {
      expect(either.map((label) => FEATURES.direction(label))).toContain(one.getAttribute("aria-label"));
      expect(one.querySelector("legend")?.textContent).toBe(FEATURES.whichWay);
    }
    // And of the things of the page that count one way, none asks it, on or off.
    const oneWay = meta.features.filter((metric) => metric.polarity !== "either").map((metric) => metric.short_label);
    for (const label of oneWay.filter((one) => screen.queryAllByRole("switch", { name: one }).length > 0)) {
      for (const toggle of screen.getAllByRole("switch", { name: label })) {
        expect([label, toggle.closest("[role='group']")?.querySelector("fieldset") ?? null]).toEqual([label, null]);
      }
    }

    const pubs = group(FEATURES.direction("Pubs and bars"));
    expect(pubs.getByRole("radio", { name: DIRECTION.more })).toBeChecked();
    await user.click(pubs.getByRole("radio", { name: DIRECTION.less }));
    expect(sent).toEqual([edits.featureDirection("venue_evening_per_homes", 0.5, "less")]);
  });

  test("test_a_change_of_direction_is_sent_with_the_weight_the_person_just_set_and_not_the_one_before", async () => {
    const nights = recordedAnswer("rank", "rank-nights-out").body.data.spec;
    const { user, open, sent } = show(nights);
    await open(GOING_OUT, FEATURES.madeOfName("Going out"));
    const pubs = "Pubs and bars";
    const number = screen.getByRole("textbox", { name: SLIDER.number(FEATURES.weight(pubs)) });

    await user.clear(number);
    await user.type(number, "70{Enter}");
    // No answer has come: the spec still says 50. A `set` always reads its value, and the later edit wins.
    await user.click(group(FEATURES.direction(pubs)).getByRole("radio", { name: DIRECTION.less }));
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
    await open(GOING_OUT, FEATURES.madeOfName("Going out"));
    const pubs = "Pubs and bars";
    const number = screen.getByRole("textbox", { name: SLIDER.number(FEATURES.weight(pubs)) });

    await user.clear(number);
    await user.type(number, "70{Enter}");
    // The answer refused the weight: it is what it was.
    again(nights, 2);
    await user.click(group(FEATURES.direction(pubs)).getByRole("radio", { name: DIRECTION.less }));

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
    await open(SETTINGS.money, SETTINGS.journeys, GREEN, SETTINGS.airAndNoise);

    // A group holds several sliders, and says what the scale means once, where it can be seen.
    for (const name of [GREEN, SETTINGS.airAndNoise]) {
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

  test("test_a_group_with_every_switch_off_offers_no_slider_and_says_what_the_scale_means_all_the_same", async () => {
    // It said what the scale means only once a thing of it was on: the line was then drawn
    // over all the group holds, and what had been pressed went down the page by a line.
    const { open } = show();
    await open(DIMENSION.crime);

    expect(within(openedBy(DIMENSION.crime)).queryAllByRole("slider")).toHaveLength(0);
    expect(scalesSeenIn(openedBy(DIMENSION.crime))).toHaveLength(1);
    // It stands before the first thing of the group, which keeps the room of a slider.
    const [line] = scalesSeenIn(openedBy(DIMENSION.crime));
    const [theft] = within(openedBy(DIMENSION.crime)).getAllByRole("switch");
    expect((line as HTMLElement).compareDocumentPosition(theft as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
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

    expect(group(BUDGET.legend).getByText(BUDGET.between("300", "20,000"))).toBeInTheDocument();
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
    await open(SETTINGS.money, GREEN);

    expect(group(BUDGET.legend).getByRole("alert")).toHaveTextContent(REJECTED.out_of_range);
    expect(group("Leafy").getByRole("alert")).toHaveTextContent(REJECTED.not_in_release);
    expect(screen.getAllByRole("alert")).toHaveLength(2);
  });

  test("test_a_change_that_has_not_been_answered_is_said_at_whatever_made_it", async () => {
    // Every control of the space requirements may be moved while no answer can come, and
    // what says what failed stands at the head of the page, out of sight of all of them.
    const WAITS = "This change waits.";
    const hidden = { ...first, areas: [{ area_id: "syn-n0006", rule: "exclude", provenance: "ui_edit" }] } as const;
    const waits = (...parts: string[]) => ({ unsent: { parts: new Set(parts), says: WAITS } });
    const said = () => screen.queryAllByRole("alert").map((line) => line.textContent);
    const { open, rerender } = show(hidden, waits());
    await open(SETTINGS.money, SETTINGS.journeys, GREEN, SETTINGS.airAndNoise, HIDDEN.legend);
    const drawn = (unsent: ReturnType<typeof waits>["unsent"]) =>
      rerender(
        <SettingsPanel
          spec={hidden}
          meta={meta}
          areas={areas}
          placeNames={NAMED}
          onEdit={() => undefined}
          onTenure={() => undefined}
          searchPlaces={() => Promise.resolve(failed("offline"))}
          onAddPlace={() => undefined}
          version={1}
          unsent={unsent}
          open
          onToggle={() => undefined}
        />,
      );

    expect(said()).toEqual([]);
    // The kind of search, the budget, a journey, a vibe and a thing that counts say it under themselves.
    for (const [part, name] of [
      ["tenure", KIND_OF_SEARCH.legend],
      ["budget", BUDGET.legend],
      ["place:syn-p0021", JOURNEY.place("Cindermoor Works")],
      ["tag:leafy", "Leafy"],
      ["feature:air_no2", "Cleaner air"],
    ] as const) {
      drawn(waits(part).unsent);
      expect([part, said()]).toEqual([part, [WAITS]]);
      expect([part, group(name).getByRole("alert").textContent]).toEqual([part, WAITS]);
    }
    // How the journeys count, as a whole: under what sets it.
    drawn(waits("journeys").unsent);
    expect(group(JOURNEY.settingsLegend).getByRole("alert")).toHaveTextContent(WAITS);
    expect(said()).toEqual([WAITS]);
    // A place that is being added is no journey of the search yet: under the field that finds it.
    drawn(waits("place:syn-p0012").unsent);
    const field = screen.getByRole("combobox", { name: PLACE.label });
    expect(said()).toEqual([WAITS]);
    expect(field.parentElement?.nextElementSibling).toHaveTextContent(WAITS);
    expect(group(JOURNEY.place("Cindermoor Works")).queryByRole("alert")).toBeNull();
    // An area that is shown again: under what shows it, which stays while no answer comes.
    drawn(waits("area:syn-n0006").unsent);
    const shows = screen.getByRole("button", { name: HIDDEN.show("Farrowmere") });
    expect(said()).toEqual([WAITS]);
    expect(shows.closest("li")).toHaveTextContent(WAITS);
    // Why an edit was refused is said first, where both are so.
    rerender(
      <SettingsPanel
        spec={hidden}
        meta={meta}
        areas={areas}
        placeNames={NAMED}
        onEdit={() => undefined}
        onTenure={() => undefined}
        searchPlaces={() => Promise.resolve(failed("offline"))}
        onAddPlace={() => undefined}
        version={1}
        refused={new Map<string, RejectReason>([["budget", "out_of_range"]])}
        unsent={waits("budget").unsent}
        open
        onToggle={() => undefined}
      />,
    );
    expect(said()).toEqual([REJECTED.out_of_range]);
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

describe("the settings, opened where their button stands at the foot of the window", () => {
  /** The settings behind their button, which the page opens and closes as the button asks. */
  function Held() {
    const [opened, setOpened] = useState(false);
    return (
      <SettingsPanel
        spec={first}
        meta={meta}
        areas={areas}
        placeNames={NAMED}
        onEdit={() => undefined}
        onTenure={() => undefined}
        searchPlaces={() => Promise.resolve(failed("offline"))}
        onAddPlace={() => undefined}
        version={1}
        open={opened}
        onToggle={setOpened}
      />
    );
  }

  /** A browser in which the button stands at the foot of a phone, and what it opens under it. */
  function atTheFoot() {
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const [top, foot] = this.tagName === "BUTTON" ? [788, 832] : [848, 1588];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 844 });
    const moved: number[] = [];
    const scroll = jest
      .spyOn(window, "scrollBy")
      .mockImplementation(((_: number, by: number) => void moved.push(by)) as typeof window.scrollBy);
    return {
      moved,
      putBack: () => {
        scroll.mockRestore();
        measure.mockRestore();
        Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
      },
    };
  }

  test("test_what_the_way_to_the_settings_opens_is_brought_into_sight", async () => {
    // Seen in a browser at 390 by 844: the button stands after the first result, which is
    // the foot of the first screen. Pressed at 788 to 832, it opened the settings from 848:
    // the button turned amber, and nothing else was seen to happen.
    const { moved, putBack } = atTheFoot();
    try {
      render(<Held />);
      const user = userEvent.setup({ delay: null });

      await user.click(screen.getByRole("button", { name: SETTINGS.title }));

      // With every group closed the settings are 740 px high, as they were measured on a
      // phone. The page is moved once, up, and never so far that the button that was
      // pressed leaves the window: it keeps the focus. How far is what brings a thing
      // into sight to say, and its own test holds it.
      expect(screen.getByRole("button", { name: SETTINGS.money })).toBeInTheDocument();
      expect(moved).toHaveLength(1);
      expect(moved[0]).toBeGreaterThan(0);
      expect(moved[0]).toBeLessThanOrEqual(788 - 8);
      expect(screen.getByRole("button", { name: SETTINGS.title })).toHaveFocus();
    } finally {
      putBack();
    }
  });

  test("test_nothing_is_moved_as_the_settings_close_or_where_the_page_opens_them", async () => {
    const { moved, putBack } = atTheFoot();
    try {
      // The page opens them of itself where words could not be read, and where a chip leads to them.
      const { user } = show(first, { opened: true });
      expect(moved).toEqual([]);

      await user.click(screen.getByRole("button", { name: SETTINGS.title }));
      expect(moved).toEqual([]);
    } finally {
      putBack();
    }
  });

  test("test_a_group_of_the_settings_moves_nothing_as_it_opens", async () => {
    // A group opens in the settings, under the hand. Nothing was asked of it, and it is as it was.
    const { moved, putBack } = atTheFoot();
    try {
      const { open } = show();
      await open(SETTINGS.money);

      expect(moved).toEqual([]);
    } finally {
      putBack();
    }
  });
});

describe("the settings, standing open beside the answer", () => {
  test("test_they_are_open_with_no_button_to_open_them_under_a_heading_that_names_them", () => {
    // Before a search, as they stand in the second way in. Once a search is open the button
    // that opened them names them: the test of their head holds that.
    show(meta.defaults.rent, { standing: true });

    const settings = screen.getByRole("region", { name: SETTINGS.title });
    expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();
    expect(within(settings).getByRole("heading", { level: 2, name: SETTINGS.title })).toBeVisible();
    // Their name, and then their groups: the tab over them says what Deep search is.
    expect(settings.querySelectorAll(":scope > p")).toHaveLength(0);
    // Every group is there, in the order it stands in behind the button, and the same stand open.
    expect(groups(settings)).toEqual([
      SETTINGS.money,
      SETTINGS.journeys,
      ...FAMILIES,
      DIMENSION.brands,
      SETTINGS.airAndNoise,
      DIMENSION.crime,
    ]);
    const open = standOpen(settings);
    expect(open).toEqual([SETTINGS.money, SETTINGS.journeys]);
    cleanup();
    show(meta.defaults.rent, { standing: false });
    expect(standOpen()).toEqual(open);
  });

  test("test_they_stand_open_whatever_the_page_says_of_the_button_and_ask_nothing_of_it", async () => {
    const { open, onToggle, user } = show(first, { standing: true, opened: false });

    const settings = screen.getByRole("region", { name: SETTINGS.title });
    expect(within(settings).getByRole("button", { name: SETTINGS.money })).toBeVisible();
    await open(SETTINGS.money);
    screen.getByRole("button", { name: SETTINGS.money }).focus();
    // Escape closes the group that is open, and the settings stand as they stood.
    await user.keyboard("{Escape}");
    await user.keyboard("{Escape}");

    expect(screen.getByRole("button", { name: SETTINGS.money })).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("region", { name: SETTINGS.title })).toBe(settings);
    expect(onToggle).not.toHaveBeenCalled();
  });

  test("test_every_control_does_what_it_does_behind_the_button", async () => {
    const { open, sent, user, onRank } = show(meta.defaults.rent, { standing: true });
    await open(GREEN);
    const slider = group("Leafy").getByRole("slider", { name: "Leafy" });

    fireEvent.pointerDown(slider);
    fireEvent.change(slider, { target: { value: "70" } });
    fireEvent.pointerUp(slider);
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));

    expect(sent).toEqual([edits.tagWeight("leafy", 0.7, "high")]);
    expect(onRank).toHaveBeenCalledTimes(1);
  });

  test("test_the_page_can_give_them_the_focus_and_they_are_no_stop_of_their_own", () => {
    show(first, { standing: true });
    const settings = screen.getByRole("region", { name: SETTINGS.title });

    settings.focus();

    expect(settings).toHaveAttribute("tabindex", "-1");
    expect(settings).toHaveFocus();
  });

  test("test_standing_open_they_have_no_accessibility_fault", async () => {
    const { container, open } = show(first, { standing: true });
    expect(await faultsIn(container)).toEqual([]);

    await open(SETTINGS.money, SETTINGS.journeys, GREEN);
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
    expect(group(BUDGET.legend).getByText(BUDGET.between("50,000", "20,000,000"))).toBeInTheDocument();
  });
});

const CSS = readFileSync(path.join(__dirname, "SettingsPanel.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
/** What the style sheet sets of a selector, where no condition is set on it, with every gap in a value made one. */
const setsOf = (selector: string) =>
  new Map(
    STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) =>
      [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]),
    ),
  );
/** The drawing that stands in a part, by the picture the page names for it. */
const drawnIn = (part: Element | null) =>
  part?.querySelector<HTMLElement>("[aria-hidden='true'] [style*='--art']")?.style.getPropertyValue("--art") ?? null;
const served = (name: string) => `url("/art/${name}.png")`;

describe("a choice, a switch and what is ticked, as they are drawn", () => {
  test("test_renting_buying_and_visiting_are_three_buttons_of_which_the_one_that_is_chosen_is_amber", async () => {
    const { open, user, tenures } = show();
    await open(SETTINGS.money);
    const group = screen.getByRole("group", { name: KIND_OF_SEARCH.legend });
    const radios = within(group).getAllByRole("radio");
    const faceOf = (radio: HTMLElement) => radio.nextElementSibling as HTMLElement;

    // Each is the browser's own radio button, in its label, with the face of a button beside it.
    expect(radios.map((radio) => [radio.tagName, radio.getAttribute("type"), radio.parentElement?.tagName])).toEqual([
      ["INPUT", "radio", "LABEL"],
      ["INPUT", "radio", "LABEL"],
      ["INPUT", "radio", "LABEL"],
    ]);
    for (const radio of radios) {
      expect(radio.parentElement).toHaveClass("target");
      expect(faceOf(radio)).toHaveClass("face");
    }
    expect(radios.map((radio) => (radio as HTMLInputElement).checked)).toEqual([true, false, false]);
    // What is chosen is amber, by the picture of the button that is on and by its ground.
    const chosen = setsOf(".choice > input:checked + .face");
    expect([chosen.get("border-image-source"), chosen.get("background-color"), chosen.get("color")]).toEqual([
      "var(--art-on)",
      "var(--chosen)",
      "var(--on-chosen)",
    ]);
    const handed = (name: string) => (group.querySelector(".options") as HTMLElement).style.getPropertyValue(name);
    expect(["--art", "--art-down", "--art-on", "--art-on-down"].map(handed)).toEqual(
      ["ui-button", "ui-button-down", "ui-button-on", "ui-button-on-down"].map(served),
    );
    expect(["--cut-top", "--cut-right", "--cut-foot", "--cut-left"].map(handed)).toEqual((cutOf("ui-button") ?? []).map(String));
    // They stand side by side and each is as wide as the next: none is the first of them by its size.
    expect(group.querySelector(".options")).toHaveAttribute("data-even", "true");
    // As many to a row as have the room of their words. Measured in a browser 360 wide:
    // three to a row of 300 px were 96 px each, and "Renting" was broken after its fifth
    // letter, for its face asks 98.5. What has no room in the row goes under, as wide.
    expect(setsOf('.options[data-even="true"]').get("display")).toBe("grid");
    expect(setsOf('.options[data-even="true"]').get("grid-template-columns")).toBe("repeat(auto-fit, minmax(6.25rem, 1fr))");
    expect(16 * 6.25).toBeGreaterThanOrEqual(98.5);
    // No column is told to be as narrow as it must, which is what broke a word in two.
    expect(STYLES.filter((rule) => /\.options/.test(rule.selector) && /minmax\(0,/.test([...rule.sets.values()].join(" ")))).toEqual([]);
    // The drawing of its thing stands before what is asked, and is dress: the group is named as it was.
    expect(drawnIn(group.querySelector("legend"))).toBe(served(drawingOf({ kind: "tenure" })));

    // A press on the other chooses it, as a press on a radio button does.
    await user.click(screen.getByRole("radio", { name: TENURE_CHOICE.buy }));
    expect(tenures).toEqual(["buy"]);
    expect(screen.getByRole("radio", { name: TENURE_CHOICE.buy })).toBeChecked();
  });

  test("test_the_radio_button_is_laid_over_the_whole_of_its_face_and_nothing_of_it_is_faded", () => {
    const over = setsOf(".choice > input");

    expect([over.get("position"), over.get("inset"), over.get("width"), over.get("height")]).toEqual(["absolute", "0", "100%", "100%"]);
    expect([over.get("appearance"), over.get("background")]).toEqual(["none", "transparent"]);
    expect(setsOf(".choice").get("position")).toBe("relative");
    // Nothing is dimmed or see-through, and the ring of the focus is never taken off a control.
    expect(ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(opacity|filter|visibility)$/.test(property)))).toEqual([]);
    const ringless = ALL.filter(
      (rule) =>
        // The settings themselves, which the page gives the focus and no keyboard stops on.
        !/\.standing:focus$/.test(rule.selector) &&
        ["outline", "outline-style", "outline-width"].some((property) => /^(none|0)\b/.test(rule.sets.get(property) ?? "")),
    );
    expect(ringless.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_what_is_chosen_is_said_by_the_shape_of_its_lamp_as_well_as_by_its_colour", async () => {
    const { open } = show();
    await open(SETTINGS.money);
    const group = screen.getByRole("group", { name: KIND_OF_SEARCH.legend });

    // Amber is not told from cream by everyone. The lamp of a choice is lit with a square of ink.
    // It is drawn before the words of the choice by the style sheet, so it says nothing:
    // what is heard of a choice is its name, and that it is chosen.
    for (const radio of within(group).getAllByRole("radio")) {
      expect(radio.nextElementSibling?.children).toHaveLength(0);
      expect(radio).toHaveAccessibleName(radio.nextElementSibling?.textContent ?? "");
    }
    expect([setsOf(".face::before").get("content"), setsOf(".face::before").get("border")]).toEqual(['""', "var(--px) solid var(--ink)"]);
    expect(setsOf(".choice > input:checked + .face::before").get("background")).toMatch(/^linear-gradient\(var\(--ink\), var\(--ink\)\) center \/ /);
  });

  test("test_a_choice_that_runs_to_a_sentence_is_set_in_the_reading_face_and_a_short_label_in_the_face_of_names", async () => {
    const { open } = show();
    await open(SETTINGS.money, SETTINGS.journeys);
    const saidBy = (group: HTMLElement) => [...group.querySelectorAll<HTMLElement>(".face")].map((one) => one.dataset.reads);

    expect(saidBy(screen.getByRole("group", { name: KIND_OF_SEARCH.legend }))).toEqual(["false", "false", "false"]);
    expect(saidBy(screen.getByRole("group", { name: JOURNEY.how }))).toEqual(["false", "false", "false"]);
    expect(saidBy(screen.getByRole("group", { name: JOURNEY.combine }))).toEqual(["true", "true"]);
    expect(saidBy(screen.getByRole("group", { name: JOURNEY.basis }))).toEqual(["true", "true"]);
    expect([setsOf(".face").get("font"), setsOf(".face").get("font-synthesis")]).toEqual(["400 var(--name-1) / 1 var(--font-name)", "none"]);
    expect(setsOf('.face[data-reads="true"]').get("font")).toBe("700 var(--size-body) / 1.25 var(--font-say)");
  });

  test("test_a_switch_and_a_checkbox_are_each_the_browsers_own_and_a_checkbox_is_a_square_that_is_ticked", async () => {
    const { open } = show();
    await open(SETTINGS.money, SETTINGS.airAndNoise);
    const firm = screen.getByRole("checkbox", { name: BUDGET.firm });
    const opened = document.getElementById(
      screen.getByRole("button", { name: SETTINGS.airAndNoise }).getAttribute("aria-controls") ?? "",
    ) as HTMLElement;
    const [lever] = within(opened).getAllByRole("switch");

    for (const one of [firm, lever as HTMLElement]) {
      expect([one.tagName, one.getAttribute("type"), one.closest("label")?.tagName]).toEqual(["INPUT", "checkbox", "LABEL"]);
      expect(one.closest("label")).toHaveClass("target");
    }
    // The square is the box itself, drawn by the look. A switch is a box laid over the face
    // of a button that says which it is: the test of a switch holds how that is drawn.
    expect(firm.parentElement?.tagName).toBe("LABEL");
    expect((lever as HTMLElement).parentElement).toHaveClass("lever");
    expect(setsOf(".tick > input").get("appearance")).toBe("none");
    // No lever is left, which stood at one side or the other and did not say which was on.
    expect(ALL.filter((rule) => /\[role="switch"\]/.test(rule.selector))).toEqual([]);
    // A tick is drawn in ink on amber, and a square that is not ticked is clear.
    expect(setsOf(".tick > input:checked").get("background")).toMatch(/var\(--chosen\)$/);
    expect(setsOf(".tick > input").get("background")).toBe("var(--page)");
    // With forced colours the square is drawn by the browser again.
    const forced = ALL.filter((rule) => /forced-colors/.test(rule.under ?? "") && /^\.tick > input/.test(rule.selector));
    expect(forced.map((rule) => rule.sets.get("appearance"))).toEqual(["auto"]);
  });

  test("test_why_a_change_was_not_taken_is_said_in_ink_beside_an_edge_of_poppy", async () => {
    const { open } = show(first, { refused: new Map<string, RejectReason>([["tenure", "out_of_range"]]) });
    await open(SETTINGS.money);

    expect(screen.getByRole("alert")).toHaveClass("problem");
    expect([setsOf(".problem").get("color"), setsOf(".problem").get("border-inline-start")]).toEqual([
      "var(--error)",
      "calc(var(--px) * 2) solid var(--error-edge)",
    ]);
    // Poppy is an edge and a mark, and never a ground or the colour of a word.
    const inPoppy = STYLES.filter((rule) => /poppy|error-edge/.test(`${rule.sets.get("background") ?? ""} ${rule.sets.get("color") ?? ""}`));
    expect(inPoppy.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_every_control_is_drawn_at_the_pixel_of_a_phone_and_the_box_at_the_pixel_of_the_page", () => {
    const pinned = ALL.filter((rule) => rule.sets.has("--px"));

    expect(pinned.map((rule) => [rule.selector, rule.sets.get("--px"), rule.under])).toEqual([
      [".panel > *", "var(--px-small)", null],
      [".thing", "var(--px-small)", null],
      [".weight", "var(--px-small)", null],
      [".radios", "var(--px-small)", null],
    ]);
    // It is the pixel of a phone, by its name among the tokens, and is written out in no sheet.
    expect(asWritten()["--px-small"]).toBe("2px");
    expect(pinned.filter((rule) => /\dpx$/.test(rule.sets.get("--px") ?? ""))).toEqual([]);
    // The box is drawn by the tokens of the page, which hold the pixel of the page already:
    // so nothing of the box itself is said here, and no token of the look is given again.
    expect(ALL.filter((rule) => /^\.(panel|settings|standing|holds)$/.test(rule.selector) && rule.sets.has("--px"))).toEqual([]);
    expect(ALL.flatMap((rule) => [...rule.sets.keys()].filter((name) => /^--(edge|box-shadow|frame-box)/.test(name)))).toEqual([]);
    // An edge inside a control is as wide as a pixel of its drawing.
    const edges = STYLES.filter((rule) => [...rule.sets].some(([property, value]) => /^border/.test(property) && /var\(--edge\)/.test(value)));
    expect(edges.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_under_a_press_the_picture_of_a_choice_changes_and_nothing_moves_or_changes_size", () => {
    const states = STYLES.filter((rule) => /:(hover|focus|focus-visible|focus-within|active)\b/.test(rule.selector));

    expect(states.map((rule) => [rule.selector, [...rule.sets.keys()]])).toEqual([
      [".standing:focus", ["outline"]],
      [".choice > input:active + .face", ["border-image-source"]],
      [".choice > input:checked:active + .face", ["border-image-source"]],
      [".lever > input:active + .face", ["border-image-source"]],
      [".lever > input:checked:active + .face", ["border-image-source"]],
    ]);
    expect(STYLES.filter((rule) => [...rule.sets.keys()].some((property) => /^(transition|animation)/.test(property)))).toEqual([]);
  });

  test("test_with_forced_colours_no_picture_is_drawn_over_the_edge_of_a_choice", () => {
    const forced = ALL.filter((rule) => /forced-colors/.test(rule.under ?? ""));

    expect(forced.filter((rule) => rule.sets.has("border-image-source")).map((rule) => [rule.selector, rule.sets.get("border-image-source")])).toEqual([
      [".face", "none"],
      [".choice > input:checked + .face", "none"],
      [".choice > input:active + .face", "none"],
      [".choice > input:checked:active + .face", "none"],
      [".choice > input:disabled + .face", "none"],
      [".lever > input:checked + .face", "none"],
      [".lever > input:active + .face", "none"],
      [".lever > input:checked:active + .face", "none"],
    ]);
    // Taken away by its source: said as the whole of the picture, the build makes nothing of it.
    expect(ALL.filter((rule) => (rule.sets.get("border-image") ?? "").trim() === "none")).toEqual([]);
  });
});

/** The place of the search, by the name it was given and no other. */
const THE_PLACE: string = NAMED["syn-p0021"];

describe("a thing of the search, as the settings draw it", () => {
  test("test_a_thing_of_the_search_is_named_on_a_tag_with_its_drawing_before_it", async () => {
    const { open } = show();
    await open(SETTINGS.money, SETTINGS.journeys);

    const budget = screen.getByRole("group", { name: BUDGET.legend });
    const journey = screen.getByRole("group", { name: JOURNEY.place(THE_PLACE) });
    const how = screen.getByRole("group", { name: JOURNEY.settingsLegend });
    expect(drawnIn(budget.querySelector("legend"))).toBe(served(drawingOf({ kind: "budget" })));
    expect(drawnIn(journey.querySelector("legend"))).toBe(served(drawingOf({ kind: "place" })));
    expect(drawnIn(how.querySelector("legend"))).toBe(served(drawingOf({ kind: "place" })));
    for (const thing of [budget, journey, how]) expect(thing.querySelector("legend .tag")).not.toBeNull();
    expect([setsOf(".tag").get("background"), setsOf(".tag").get("color"), setsOf(".tag").get("font")]).toEqual([
      "var(--ink)",
      "var(--page)",
      "400 var(--name-1) / 1 var(--font-name)",
    ]);
  });

  test("test_a_budget_that_is_not_set_is_drawn_in_outline", async () => {
    const { open } = show(meta.defaults.rent);
    await open(SETTINGS.money);
    const budget = drawingOf({ kind: "budget" });

    expect(meta.defaults.rent.budget.amount).toBeNull();
    expect(drawnIn(screen.getByRole("group", { name: BUDGET.legend }).querySelector("legend"))).toBe(served(outlineOf(budget) ?? budget));
  });

  test("test_a_vibe_is_drawn_beside_its_slider_by_the_id_the_api_gives_it_and_in_outline_while_it_counts_for_nothing", async () => {
    const { open } = show();
    await open(...FAMILIES);

    for (const tag of meta.tags) {
      const own = drawingOf({ kind: "tag", id: tag.tag_id, family: tag.family });
      const counts = first.tags.some((weight) => weight.tag_id === tag.tag_id && weight.weight > 0);
      const drawn = drawnIn(screen.getByRole("group", { name: tag.label }).querySelector("label"));
      expect([tag.tag_id, drawn]).toEqual([tag.tag_id, served(counts ? own : (outlineOf(own) ?? own))]);
    }
    // Some count in this search and some do not: both are seen.
    const counting = meta.tags.filter((tag) => first.tags.some((weight) => weight.tag_id === tag.tag_id && weight.weight > 0));
    expect(counting.length).toBeGreaterThan(0);
    expect(counting.length).toBeLessThan(meta.tags.length);
  });

  test("test_the_slider_of_a_vibe_has_the_one_picture_of_each_end_of_the_vibe_on_the_button_at_that_end", async () => {
    const { open } = show();
    await open(...FAMILIES);
    /** The picture a button bears, by where it is served from: on its face, or as the whole of it. */
    const borne = (button: HTMLElement) =>
      button.querySelector<HTMLElement>("[style*='--art:']:not(.face)")?.style.getPropertyValue("--art") ??
      button.style.getPropertyValue("--art");

    for (const tag of meta.tags) {
      // The two buttons of its slider stand at either side of it, the low end first.
      const slider = within(screen.getByRole("group", { name: tag.label })).getByRole("slider", { name: tag.label });
      const buttons = [...(slider.closest(".row")?.querySelectorAll<HTMLElement>(":scope > button") ?? [])];
      const names =
        tag.low_end === null || tag.high_end === null
          ? [SLIDER.less(tag.label), SLIDER.more(tag.label)]
          : [SLIDER.toward(tag.label, tag.low_end), SLIDER.toward(tag.label, tag.high_end)];
      expect([tag.tag_id, buttons.map((button) => button.getAttribute("aria-label"))]).toEqual([tag.tag_id, names]);
      // Each bears the picture of that end of its vibe, which is chosen by the id of the vibe.
      expect([tag.tag_id, buttons.map(borne)]).toEqual([tag.tag_id, picturesAtEnds(tag.tag_id).map(served)]);
      expect([tag.tag_id, new Set(buttons.map(borne)).size]).toEqual([tag.tag_id, 2]);
    }
    expect(ENDS_OF_ONE_WAY).toBe("pictured");
    // The slider of a measurement is the slider of no vibe, and keeps its minus and its plus.
    const measured = [...document.querySelectorAll<HTMLInputElement>("input[type='range']")].filter(
      (slider) => !meta.tags.some((tag) => tag.label === (slider.getAttribute("aria-label") ?? slider.labels?.[0]?.textContent)),
    );
    expect(measured.length).toBeGreaterThan(0);
    for (const slider of measured) {
      const buttons = [...(slider.closest(".row")?.querySelectorAll<HTMLElement>(":scope > button") ?? [])];
      expect(buttons.map(borne)).toEqual([served("btn-less"), served("btn-more")]);
    }
  });

  test("test_a_vibe_that_no_area_can_be_placed_on_is_drawn_in_outline_beside_its_name_and_has_no_slider", async () => {
    // As in a first build of a real city, which holds a band for a few vibes and for no area of the rest.
    const [one] = meta.tags;
    const form = {
      ...meta,
      recipes: meta.recipes.map((held) => (held.tag_id === one?.tag_id ? { ...held, placed: false, held: 40 } : held)),
    };
    const { open } = show(first, { form });
    await open(meta.families.find((family) => family.family === one?.family)?.label ?? "");
    const group = screen.getByRole("group", { name: one?.label });
    const own = drawingOf({ kind: "tag", id: one?.tag_id, family: one?.family });

    expect(one).toBeDefined();
    expect(within(group).queryByRole("slider")).toBeNull();
    expect(within(group).getByText(one?.label ?? "")).toBeVisible();
    expect(drawnIn(group)).toBe(served(outlineOf(own) ?? own));
    // It says why in words, as it did: the drawing is dress.
    expect(group.querySelector(".hint")?.textContent).toContain(NOT_IN_DATA.why.vibe);
  });

  test("test_where_a_vibe_counts_recorded_crime_it_says_so_beside_its_slider_in_ink_as_a_notice_does", async () => {
    const { open } = show();
    await open(...FAMILIES);
    const told = meta.tags.flatMap((tag) => {
      const group = screen.getByRole("group", { name: tag.label });
      return [...group.querySelectorAll(".counts")].map((line) => ({ tag, line, group }));
    });

    // Which vibe that is, is the release's to say: the line is there for each that says so, and for no other.
    expect(told.length).toBeGreaterThan(0);
    expect(told.length).toBeLessThan(meta.tags.length);
    for (const { line, group } of told) {
      expect(line).toBeVisible();
      expect(line.closest("[hidden], [aria-hidden='true'], details:not([open])")).toBeNull();
      // It comes after the slider it is of, in the group of that vibe.
      expect(within(group).getByRole("slider").compareDocumentPosition(line) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
    const notice = STYLES.find((rule) => /^\.counts$/.test(rule.selector) && rule.sets.has("border-inline-start"));
    expect([notice?.sets.get("color"), notice?.sets.get("border-inline-start"), notice?.sets.get("box-shadow")]).toEqual([
      "var(--notice-text)",
      "var(--px) solid var(--notice-edge)",
      "inset calc(var(--px) * 2) 0 0 var(--notice-mark)",
    ]);
  });

  test("test_what_takes_a_thing_away_is_a_button_with_an_edge_of_poppy", async () => {
    const { open } = show();
    await open(SETTINGS.money, SETTINGS.journeys);

    // Each is the button of the kit: native, the size of a main control, its face inside it.
    for (const name of [BUDGET.clear, JOURNEY.remove(THE_PLACE)]) {
      const button = screen.getByRole("button", { name });
      expect(button).toHaveClass("target");
      expect(button.firstElementChild).toHaveClass("face");
      expect([name, button.firstElementChild?.getAttribute("data-kind")]).toEqual([name, "stop"]);
    }
  });

  test("test_the_kind_of_home_is_chosen_from_the_browsers_own_list_under_the_arrow_of_the_look", async () => {
    const { open } = show();
    await open(SETTINGS.money);
    const list = screen.getByRole("combobox", { name: BUDGET.segment });
    const holds = list.parentElement as HTMLElement;
    const arrow = sizeOf("ui-arrow");

    expect(list.tagName).toBe("SELECT");
    expect(list).toHaveClass("target");
    expect(holds).toHaveClass("select");
    expect(["--art", "--w", "--h"].map((name) => holds.style.getPropertyValue(name))).toEqual([
      served("ui-arrow"),
      String(arrow.width),
      String(arrow.height),
    ]);
    // The arrow is laid over the list and takes no press: the press is the list's.
    expect([setsOf(".select::after").get("pointer-events"), setsOf(".select::after").get("image-rendering")]).toEqual(["none", "pixelated"]);
    expect(setsOf(".select::after").get("background")).toBe(
      "var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat",
    );
    // It weighs more than what the page says of every list.
    expect(heavier(weightOf(".select > select"), weightOf("select"))).toBe(true);
    expect(drawnIn(holds.parentElement?.querySelector("label") ?? null)).toBe(served(drawingOf({ kind: "home" })));
  });
});

describe("the settings, as they are drawn", () => {
  /** What a button of the settings opens. */
  const openedBy = (name: string) =>
    document.getElementById(screen.getByRole("button", { name }).getAttribute("aria-controls") ?? "") as HTMLElement;

  test("test_the_settings_stand_in_one_box_behind_their_button_and_standing_open", () => {
    for (const standing of [false, true]) {
      const { container, unmount } = show(first, { standing });
      const boxes = container.querySelectorAll("[data-kind]");
      const box = container.querySelector("[data-kind='box']") as HTMLElement;

      // One box, and no box inside it: many boxes with shadows, one in another, are noise.
      expect([standing, [...boxes].filter((one) => /^box/.test(one.getAttribute("data-kind") ?? "")).length]).toEqual([standing, 1]);
      // All that they hold is in it: their groups, in one stack, which no sentence stands over.
      expect(box.querySelector(".stack")).not.toBeNull();
      expect(box.querySelectorAll(":scope > p")).toHaveLength(0);
      expect(bars(box).length).toBeGreaterThan(FAMILIES.length);
      // It says that it is busy while an edit waits, as what held the settings did.
      expect(box).toHaveAttribute("aria-busy", "false");
      unmount();
    }
  });

  test("test_standing_open_the_settings_are_the_box_themselves_and_their_name_stands_in_it", () => {
    const { container } = show(meta.defaults.rent, { standing: true });
    const box = container.querySelector("[data-kind='box']") as HTMLElement;
    const settings = screen.getByRole("region", { name: SETTINGS.title });

    // The page gives the focus to the first section it finds in their column: it is the
    // settings themselves. And a page that stands them on the grass finds a box of the kit
    // there, and lays no ground of its own under it: a box is not boxed twice.
    expect(settings).toBe(box);
    expect(settings.tagName).toBe("SECTION");
    expect(container.firstElementChild).toBe(box);
    expect(settings.querySelector("section")).toBeNull();
    expect(box).toContainElement(screen.getByRole("heading", { level: 2, name: SETTINGS.title }));
    // Nothing of the settings is read on the grass: all of it is in the box.
    const read = [...container.querySelectorAll("p, h2, button, label, legend")];
    expect(read.length).toBeGreaterThan(FAMILIES.length);
    expect(read.filter((one) => !box.contains(one))).toEqual([]);
    expect([setsOf(".title").get("font"), setsOf(".title").get("color"), setsOf(".title").get("background")]).toEqual([
      "400 var(--name-2) / 1 var(--font-name)",
      "var(--page)",
      "var(--ink)",
    ]);
  });

  test("test_each_group_is_named_in_the_face_of_names_with_the_drawing_of_its_thing_beside_the_name", () => {
    show();

    for (const { family, label } of meta.families) {
      const button = screen.getByRole("button", { name: label });
      const name = within(button).getByText(label);
      // The drawing is chosen by the family the API gives, and falls to the plain one. It is dress.
      expect([label, drawnIn(button)]).toEqual([label, served(drawingOf({ kind: "feature", family }))]);
      expect(name).toHaveClass("name");
      // It is named by its name and by nothing else, whatever it holds.
      expect(button).toHaveAccessibleName(label);
      expect(button.textContent).toBe(`${label}${heldBy(label) ?? ""}`);
    }
    expect([setsOf(".name").get("font"), setsOf(".name").get("font-synthesis")]).toEqual([
      "400 var(--name-2) / 1 var(--font-name)",
      "none",
    ]);
    // The money, the journeys: each by the drawing of its kind.
    expect(drawnIn(screen.getByRole("button", { name: SETTINGS.money }))).toBe(served(drawingOf({ kind: "budget" })));
    expect(drawnIn(screen.getByRole("button", { name: SETTINGS.journeys }))).toBe(served(drawingOf({ kind: "place" })));
    // What is of no family of vibes: by the dimension the service gives what the group holds,
    // as a family is drawn by its family. Each stood under the plain box, and none does.
    const held = heldByTheRelease(meta, first.tenure);
    const apart = [
      { name: DIMENSION.brands, measures: held.brands },
      { name: SETTINGS.airAndNoise, measures: held.apart },
      { name: DIMENSION.crime, measures: held.crime },
    ];
    for (const { name, measures } of apart) {
      const dimensions = [...new Set(measures.map((metric) => metric.dimension))];
      const drawn = drawnIn(screen.getByRole("button", { name }));
      expect([name, dimensions.length]).toEqual([name, 1]);
      expect([name, drawn]).toEqual([name, served(drawingOf({ kind: "feature", family: dimensions[0] }))]);
      expect([name, drawn === served(PLAIN)]).toEqual([name, false]);
    }
    // No two groups are drawn alike.
    const all = bars().map((bar) => drawnIn(bar));
    expect(new Set(all).size).toBe(all.length);
  });

  test("test_every_family_of_the_release_has_a_drawing_and_one_the_look_does_not_know_takes_the_plain_one", () => {
    const drawn = meta.families.map(({ family }) => drawingOf({ kind: "feature", family }));
    expect(drawn.filter((name) => !isDrawn(name) || name === PLAIN)).toEqual([]);
    expect(new Set(drawn).size).toBe(meta.families.length);

    const unknown = "a_family_nobody_has_drawn" as (typeof meta.families)[number]["family"];
    const [one] = meta.families;
    const form = {
      ...meta,
      families: [{ family: unknown, label: "A family of another release" }],
      tags: meta.tags.map((tag) => (tag.family === one?.family ? { ...tag, family: unknown } : tag)),
    };
    show(first, { form });

    expect(drawnIn(screen.getByRole("button", { name: "A family of another release" }))).toBe(served(PLAIN));
  });

  test("test_a_name_that_holds_a_figure_is_set_in_the_reading_face", () => {
    show();
    const withAFigure = meta.families.filter(({ label }) => /\d/.test(label));

    expect(withAFigure.length).toBeGreaterThan(0);
    for (const { label } of meta.families) {
      const name = within(screen.getByRole("button", { name: label })).getByText(label);
      expect([label, name.getAttribute("data-reads")]).toEqual([label, String(/\d/.test(label))]);
    }
    expect(setsOf('.name[data-reads="true"]').get("font")).toBe("700 var(--size-lead) / 1.2 var(--font-say)");
  });

  test("test_rank_with_these_settings_is_the_one_button_of_the_settings_that_is_cobalt", async () => {
    const { container, open } = show(meta.defaults.rent);
    await open(SETTINGS.money, SETTINGS.journeys);

    expect(screen.getByRole("button", { name: SETTINGS.rank }).firstElementChild).toHaveAttribute("data-kind", "go");
    expect(container.querySelectorAll("[data-kind='go']")).toHaveLength(1);
  });

  test("test_standing_open_beside_the_box_rank_with_these_settings_is_plain_for_search_is_in_sight_there", async () => {
    // Seen at 1440 by 900: two filled buttons before a search, Search and this one, and
    // three while Burro asks. The look allows one in sight, the one that matters most at
    // that moment, which beside the box is never this one. One press away the settings
    // stand under the box, a screen and more from Search, and there it is the one.
    const { container, open } = show(meta.defaults.rent, { standing: true });
    await open(SETTINGS.money, SETTINGS.journeys);

    expect(screen.getByRole("button", { name: SETTINGS.rank }).firstElementChild).toHaveAttribute("data-kind", "plain");
    expect(container.querySelectorAll("[data-kind='go']")).toHaveLength(0);
  });

  test("test_a_hidden_area_is_shown_again_by_a_button_of_the_kit_in_the_group_of_its_thing", async () => {
    const hidden = { ...first, areas: [{ area_id: areas[0]?.area_id ?? "", rule: "exclude", provenance: "ui_edit" }] } as const;
    const { open } = show(hidden);

    expect(drawnIn(screen.getByRole("button", { name: HIDDEN.legend }))).toBe(served(drawingOf({ kind: "area" })));
    await open(HIDDEN.legend);
    const again = within(openedBy(HIDDEN.legend)).getByRole("button");
    expect(again).toHaveTextContent(HIDDEN.show(areas[0]?.name ?? ""));
    expect(again.firstElementChild).toHaveAttribute("data-kind", "plain");
  });

  test("test_the_caveat_of_recorded_crime_is_drawn_as_a_notice_is_and_what_a_group_says_of_itself_as_a_sentence", async () => {
    const { open } = show();
    await open(DIMENSION.crime, DIMENSION.brands);

    expect(screen.getByText(CRIME_CAVEAT)).toHaveClass("caveat");
    expect(screen.getByText(BRANDS.lead)).toHaveClass("told");
    const notice = STYLES.find((rule) => /^\.caveat$/.test(rule.selector) && rule.sets.has("border-inline-start"));
    expect([notice?.sets.get("color"), notice?.sets.get("border-inline-start"), notice?.sets.get("box-shadow")]).toEqual([
      "var(--notice-text)",
      "var(--px) solid var(--notice-edge)",
      "inset calc(var(--px) * 2) 0 0 var(--notice-mark)",
    ]);
    // It is as large as it was: what is said of recorded crime is not set smaller than what stands beside it.
    expect(STYLES.filter((rule) => /^\.caveat$/.test(rule.selector) && rule.sets.has("font-size"))).toEqual([]);
  });

  test("test_what_the_settings_hold_asks_how_wide_their_box_is_and_never_how_wide_the_screen_is", () => {
    const asking = ALL.filter((rule) => /@container/.test(rule.under ?? ""));

    expect(asking.length).toBeGreaterThan(0);
    // It asks whatever holds the box: the column of the page where the settings stand open,
    // which the page has say how wide it is, and what the button opens where they are
    // one press away. So it names no box, and is never the box that is asked.
    expect([...new Set(asking.map((rule) => rule.under?.replace(/\s*\(.*$/, "")))]).toEqual(["@container"]);
    expect(asking.filter((rule) => /^\.(settings|standing|holds)$/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    expect(ALL.filter((rule) => /@media[^{]*\b(width|height)\b/.test(rule.under ?? "")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_behind_their_button_the_settings_are_held_by_what_says_how_wide_it_is", () => {
    const { container } = show(first, { standing: false });
    const box = container.querySelector("[data-kind='box']") as HTMLElement;

    expect(box.parentElement).toHaveClass("holds");
    expect(setsOf(".holds").get("container-type")).toBe("inline-size");
    // Standing open they are held by the column of the page, which says how wide it is:
    // the box itself says nothing of it, for what is asked cannot be what asks.
    expect(ALL.filter((rule) => /^\.(panel|standing|settings)$/.test(rule.selector) && [...rule.sets.keys()].some((name) => /^container/.test(name)))).toEqual([]);
  });

  test("test_every_sentence_is_set_in_the_reading_face_and_the_face_of_names_is_never_thickened", () => {
    const faces = STYLES.flatMap((rule) =>
      [...rule.sets]
        .filter(([property]) => property === "font" || property === "font-family")
        .map(([, value]) => ({ rule, face: /var\(--font-(name|say)\)/.exec(value)?.[1] ?? value })),
    );

    expect(faces.filter(({ face }) => face !== "name" && face !== "say").map(({ rule }) => rule.selector)).toEqual([]);
    // A name, a tag and a short label. Never a sentence, a hint or what is said of a fault.
    expect([...new Set(faces.filter(({ face }) => face === "name").map(({ rule }) => rule.selector))].sort()).toEqual(
      [".face", ".label", ".legend", ".name", ".tag", ".title"].sort(),
    );
    for (const { rule } of faces.filter(({ face }) => face === "name")) {
      expect([rule.selector, /^400 /.test(rule.sets.get("font") ?? ""), rule.sets.get("font-synthesis")]).toEqual([rule.selector, true, "none"]);
    }
  });

  test("test_every_colour_is_a_token_no_picture_is_named_by_the_style_sheet_and_nothing_has_a_height_of_its_own", () => {
    expect(CSS.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(CSS.match(/url\(/g) ?? []).toEqual([]);
    // What holds words grows with them. What has a height is a drawing, or lies over one.
    const high = STYLES.filter((rule) => rule.sets.has("height") || rule.sets.has("max-height"));
    expect(high.map((rule) => rule.selector).sort()).toEqual(
      [".choice > input", ".face::before", ".lever > input", ".select::after", ".tick > input"].sort(),
    );
  });
});
