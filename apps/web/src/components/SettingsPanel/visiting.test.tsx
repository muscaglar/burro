import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DIMENSION } from "@/content/labels";
import { TENURE_CHOICE } from "@/content/search";
import { BUDGET, FEATURES, JOURNEY, KIND_OF_SEARCH, SEGMENTS, SETTINGS } from "@/content/settings";
import { failed } from "@/lib/api/failure";
import { recordedAnswer } from "@/lib/api/recorded";
import type { FeatureWeight, Operations, PreferenceSpec, Tenure } from "@/lib/api/schema";
import { edits, merged, NO_EDITS } from "@/lib/search/edits";

import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
import { BudgetControl } from "./BudgetControl";
import { groupsOf, hasBegun, heldBy, isOfAPrice } from "./groups";
import { SettingsPanel } from "./SettingsPanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** "Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works", as it was ranked. */
const first = recordedAnswer("rank", "rank-first").body.data.spec;
const NAMED = { "syn-p0021": "Cindermoor Works" } as const;

/**
 * What a visit starts from, as the service serves it: no amount, a budget that counts for
 * nothing, and a kind of home that stands for nothing and is shown by nobody.
 */
const visit = meta.defaults.visit;
/** A visit that is a search: a place to reach and two vibes, which a visitor asked for. */
const visiting: PreferenceSpec = { ...visit, commutes: first.commutes, tags: first.tags, tenure_from: "ui_edit" };
/** A search for a home that became a visit, as the service was sent it and as it answered. */
const became = recordedAnswer("rank", "visiting/rank-becomes");

/** The measurements of the service that are of a price: what homes sell for, and how that has risen. */
const PRICED = meta.features.filter((metric) => metric.rankable && isOfAPrice(metric));
const switched = (featureId: FeatureWeight["feature_id"]): FeatureWeight => ({
  feature_id: featureId,
  weight: 0.5,
  direction: "less",
  provenance: "ui_edit",
});

function show(spec: PreferenceSpec) {
  const sent: Operations[] = [];
  const kinds: Tenure[] = [];
  const view = render(
    <SettingsPanel
      spec={spec}
      meta={meta}
      areas={areas}
      placeNames={NAMED}
      onEdit={(operations) => sent.push(operations)}
      onTenure={(kind) => kinds.push(kind)}
      searchPlaces={() => Promise.resolve(failed("offline"))}
      onAddPlace={() => undefined}
      version={1}
      open
      onToggle={() => undefined}
      standing
    />,
  );
  const user = userEvent.setup({ delay: null });
  /** Opens groups, and what a vibe is made of, by the names of their buttons. What stands open is left so. */
  const open = async (...names: string[]) => {
    for (const name of names) {
      const button = screen.getByRole("button", { name });
      if (button.getAttribute("aria-expanded") !== "true") await user.click(button);
    }
  };
  /** Opens every group, and what every vibe is made of. */
  const openAll = async () => {
    await open(...groupsOf(spec, meta, areas, NAMED).map((group) => group.label));
    await open(...meta.tags.map((tag) => FEATURES.madeOfName(tag.label)));
  };
  return { ...view, sent, kinds, user, open, openAll };
}

const heldBy_ = (name: string) => screen.getByRole("button", { name }).querySelector(".holds")?.textContent ?? null;
const asked = () => screen.getByRole("group", { name: KIND_OF_SEARCH.legend });

describe("visiting, the third kind of search", () => {
  test("test_renting_buying_and_visiting_are_three_choices_side_by_side_and_each_as_wide_as_the_next", async () => {
    // The founder: "Add a visiting option under renting or buying".
    const { open } = show(meta.defaults.rent);
    await open(SETTINGS.money);

    expect(KIND_OF_SEARCH.visit).toBe("Visiting");
    expect(within(asked()).getAllByRole("radio").map((one) => one.nextElementSibling?.textContent)).toEqual([
      TENURE_CHOICE.rent,
      TENURE_CHOICE.buy,
      KIND_OF_SEARCH.visit,
    ]);
    expect(within(asked()).getAllByRole("radio").map((one) => (one as HTMLInputElement).value)).toEqual(["rent", "buy", "visit"]);
    expect(within(asked()).getByRole("radio", { name: TENURE_CHOICE.rent })).toBeChecked();
    // What is asked names all three, and none is the first of them by its size.
    expect(KIND_OF_SEARCH.legend).toMatch(/visiting/);
    expect(asked().querySelector(".options")).toHaveAttribute("data-even", "true");
    for (const one of within(asked()).getAllByRole("radio")) expect(one.parentElement).toHaveClass("target");
  });

  test("test_what_is_asked_over_the_three_is_said_one_way_wherever_it_is_written", () => {
    // The words of the search page said what is asked over renting and buying, and named
    // no third. While they did, every test of the search page that looked for the choice
    // by them found nothing, and one that looked for it to be gone passed whatever the page
    // drew. They name the three as the settings do, so both say the same.
    expect(KIND_OF_SEARCH.legend).toBe("Renting, buying or visiting");
    expect(TENURE_CHOICE.legend).toBe(KIND_OF_SEARCH.legend);
    expect([TENURE_CHOICE.rent, TENURE_CHOICE.buy, KIND_OF_SEARCH.visit]).toEqual(["Renting", "Buying", "Visiting"]);
  });

  test("test_visiting_is_told_to_the_page_as_the_kind_the_service_calls_a_visit_and_the_settings_send_nothing_of_their_own", async () => {
    const { open, user, kinds, sent } = show(first);
    await open(SETTINGS.money);

    await user.click(screen.getByRole("radio", { name: KIND_OF_SEARCH.visit }));

    expect(kinds).toEqual(["visit"]);
    expect(sent).toEqual([]);
    expect(screen.getByRole("radio", { name: KIND_OF_SEARCH.visit })).toBeChecked();
    // What the page sends of it is an edit the contract takes.
    expect(problemsWith("Operations", edits.tenure("visit"))).toEqual([]);
  });

  test("test_with_visiting_chosen_nothing_of_a_price_the_bedrooms_or_the_kind_of_home_is_drawn_in_any_group", async () => {
    // The founder: "Visiting should remove some of the price and bedroom fields, we are
    // just finding a location where they might want to book a hotel."
    const { openAll } = show(visiting);
    await openAll();

    expect(screen.queryByRole("group", { name: BUDGET.legend })).toBeNull();
    for (const amount of Object.values(BUDGET.amount)) expect(screen.queryByRole("textbox", { name: amount })).toBeNull();
    expect(screen.queryByRole("combobox", { name: BUDGET.segment })).toBeNull();
    expect(screen.queryByRole("checkbox", { name: BUDGET.firm })).toBeNull();
    expect(screen.queryByRole("slider", { name: BUDGET.weight })).toBeNull();
    for (const name of [BUDGET.clear, BUDGET.less, BUDGET.more]) expect(screen.queryByRole("button", { name })).toBeNull();
    // Nor a measurement of what homes sell for, which the service says by its unit.
    expect(PRICED.map((metric) => metric.feature_id).sort()).toEqual(["price_median", "price_rise_10y", "price_rise_5y"]);
    for (const metric of PRICED) expect([metric.short_label, screen.queryAllByRole("switch", { name: metric.short_label })]).toEqual([metric.short_label, []]);
    // No word of a pound, of a bedroom or of a price is left on the page.
    const said = screen.getByRole("region", { name: SETTINGS.title }).textContent ?? "";
    expect(/£|\bbedrooms?\b|\bprices?\b|\brents?\b|\bbudget\b(?! and home)/i.test(said)).toBe(false);
  });

  test("test_the_same_groups_draw_each_of_them_for_whoever_is_renting_so_that_it_is_visiting_that_takes_them_out", async () => {
    const { openAll } = show({ ...first, tags: visiting.tags });
    await openAll();

    expect(screen.getByRole("group", { name: BUDGET.legend })).toBeVisible();
    expect(screen.getByRole("combobox", { name: BUDGET.segment })).toBeVisible();
    for (const metric of PRICED) expect(screen.getAllByRole("switch", { name: metric.short_label })).toHaveLength(1);
  });

  test("test_what_is_left_is_where_a_visitor_needs_to_get_to_and_what_they_want_around_them", async () => {
    const { openAll } = show(visiting);
    await openAll();

    // Every group is there, the first among them: it holds what asks the kind of search,
    // and is named for that. Every other is named as it is for whoever rents or buys.
    const [of, renting] = [groupsOf(visiting, meta, areas, NAMED), groupsOf(first, meta, areas, NAMED)];
    expect(of.map((group) => group.key)).toEqual(renting.map((group) => group.key));
    expect(of.slice(1).map((group) => group.label)).toEqual(renting.slice(1).map((group) => group.label));
    expect(of[0]?.label).toBe(KIND_OF_SEARCH.legend);
    expect(screen.getByRole("group", { name: JOURNEY.place("Cindermoor Works") })).toBeVisible();
    for (const tag of meta.tags) expect(screen.getByRole("slider", { name: tag.label })).toBeInTheDocument();
    // And every measurement but those of a price, recorded crime under its own bar among them.
    const left = meta.features.filter((metric) => metric.rankable && !isOfAPrice(metric));
    expect(left.length).toBe(meta.features.filter((metric) => metric.rankable).length - PRICED.length);
    for (const metric of left) expect(screen.getAllByRole("switch", { name: metric.short_label }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: DIMENSION.crime })).toHaveAttribute("aria-expanded", "true");
  });

  test("test_with_visiting_chosen_the_first_group_is_named_for_what_it_asks_and_holds_no_name_of_a_budget_or_a_home", () => {
    // Seen in a browser: the bar read "Budget and home  Visiting", and under that name stood
    // "You are visiting, so Burro does not ask what you can pay or what kind of home you want".
    show(visiting);
    const bars = () => groupsOf(visiting, meta, areas, NAMED).map((group) => group.label);

    expect(bars()[0]).toBe(KIND_OF_SEARCH.legend);
    expect(bars()).not.toContain(SETTINGS.money);
    expect(KIND_OF_SEARCH.legend).not.toMatch(/budget|home/i);
    expect(screen.queryByRole("button", { name: SETTINGS.money })).toBeNull();
    expect(screen.getByRole("button", { name: KIND_OF_SEARCH.legend })).toBeInTheDocument();
    // Whoever rents or buys is asked what they can pay and for what home, under the name it had.
    for (const spec of [meta.defaults.rent, meta.defaults.buy]) {
      expect(groupsOf(spec, meta, areas, NAMED)[0]?.label).toBe(SETTINGS.money);
    }
  });

  test("test_the_bar_of_the_group_says_visiting_and_nothing_of_a_home", () => {
    show(visiting);

    expect(heldBy_(KIND_OF_SEARCH.legend)).toBe("Visiting");
    // Before anything else is chosen too: visiting is a thing somebody chose, as buying is.
    expect(groupsOf(visit, meta, areas, NAMED)[0]).toMatchObject({ key: "money", holds: KIND_OF_SEARCH.visit, asked: true });
    expect(groupsOf(meta.defaults.buy, meta, areas, NAMED)[0]).toMatchObject({ key: "money", holds: TENURE_CHOICE.buy });
    expect(groupsOf(meta.defaults.rent, meta, areas, NAMED)[0]).toMatchObject({ key: "money", holds: null });
  });

  test("test_in_the_place_of_the_budget_the_group_says_why_there_is_none_in_whole_sentences", async () => {
    const { open } = show(visiting);
    await open(KIND_OF_SEARCH.legend);
    const held = document.getElementById(
      screen.getByRole("button", { name: KIND_OF_SEARCH.legend }).getAttribute("aria-controls") ?? "",
    ) as HTMLElement;

    expect(within(held).getByText(KIND_OF_SEARCH.noBudget)).toBeVisible();
    expect(KIND_OF_SEARCH.noBudget).toMatch(/^You are visiting, so /);
    expect(KIND_OF_SEARCH.noBudget).toMatch(/\.$/);
    // It is said of a visit, and of no other kind of search.
    expect(within(held).getAllByRole("radio")).toHaveLength(3);
    expect(held.querySelectorAll("input, select, button")).toHaveLength(3);
  });

  test("test_it_is_not_said_to_whoever_rents_or_buys", async () => {
    const { open } = show(first);
    await open(SETTINGS.money);

    expect(screen.queryByText(KIND_OF_SEARCH.noBudget)).toBeNull();
  });

  test("test_what_the_search_held_of_a_price_is_taken_off_as_visiting_is_chosen_in_the_one_edit_that_says_so", async () => {
    // Left in, it would go on counting in a visit, with nothing in sight to turn it off by.
    const priced: PreferenceSpec = {
      ...first,
      weights: [...first.weights, switched("price_median"), { ...switched("price_rise_5y"), weight: 0 }],
    };
    const { open, user, kinds, sent } = show(priced);
    await open(SETTINGS.money);

    await user.click(screen.getByRole("radio", { name: KIND_OF_SEARCH.visit }));

    // What counts of a price, and not what was taken off already: and the page is not asked a second time.
    expect(sent).toEqual([[edits.featureOff("price_median"), edits.tenure("visit")].reduce(merged, NO_EDITS)]);
    expect(kinds).toEqual([]);
    expect(problemsWith("Operations", sent[0])).toEqual([]);
  });

  test("test_renting_and_buying_are_told_to_the_page_as_they_were_whatever_the_search_holds_of_a_price", async () => {
    const priced: PreferenceSpec = { ...first, weights: [...first.weights, switched("price_median")] };
    const { open, user, kinds, sent } = show(priced);
    await open(SETTINGS.money);

    await user.click(screen.getByRole("radio", { name: TENURE_CHOICE.buy }));

    expect(kinds).toEqual(["buy"]);
    expect(sent).toEqual([]);
  });

  test("test_a_search_that_holds_what_a_visit_starts_from_has_not_begun", () => {
    expect(hasBegun(meta.defaults.visit, meta)).toBe(false);
    expect(hasBegun({ ...meta.defaults.visit }, meta)).toBe(true);
    expect(hasBegun(meta.defaults.rent, meta)).toBe(false);
    expect(hasBegun(meta.defaults.buy, meta)).toBe(false);
  });

  test("test_a_visit_has_no_kind_of_home_to_offer", () => {
    expect(SEGMENTS.visit).toEqual([]);
    expect(Object.keys(SEGMENTS).sort()).toEqual(["buy", "rent", "visit"]);
    expect(Object.keys(BUDGET.amount).sort()).toEqual(["buy", "rent"]);
  });

  test("test_the_budget_of_a_visit_draws_nothing_wherever_it_is_asked_for", () => {
    // A chip opens the budget in place, by the same part: of a visit there is none to open.
    const { container } = render(
      <BudgetControl budget={visit.budget} tenure="visit" limits={meta.limits} onEdit={() => undefined} version={1} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  test("test_what_is_of_a_price_is_told_by_the_unit_the_service_gives_and_by_no_name", () => {
    expect(isOfAPrice({ unit: "£" })).toBe(true);
    expect(isOfAPrice({ unit: "£ a month" })).toBe(true);
    for (const unit of ["%", "m", "count", "per 1,000 homes", ""]) expect([unit, isOfAPrice({ unit })]).toEqual([unit, false]);
    // A visit is offered every other measurement the service can rank, in the group it stood in.
    const [home, away] = [heldBy(meta, "rent"), heldBy(meta, "visit")];
    const others = (held: typeof home) => held.families.flatMap((family) => family.others.map((metric) => metric.feature_id));
    expect(others(home).filter((id) => !others(away).includes(id)).sort()).toEqual(PRICED.map((metric) => metric.feature_id).sort());
    expect([away.brands, away.apart, away.crime]).toEqual([home.brands, home.apart, home.crime]);
    expect(heldBy(meta)).toEqual(home);
  });

  test("test_what_the_page_sends_of_the_choice_is_what_the_service_was_sent_as_a_search_became_a_visit", () => {
    const sent = became.request.body as { readonly spec: PreferenceSpec; readonly operations: Operations };

    expect(sent.operations).toEqual(edits.tenure("visit"));
    // It was a search for a home with a budget, and the service answered with a visit that holds none.
    expect([sent.spec.tenure, sent.spec.budget.amount]).toEqual(["rent", 1800]);
    expect(became.body.data.spec).toMatchObject({ tenure: "visit", budget: visit.budget });
    expect(visit.budget).toEqual({ amount: null, segment: "bed_1", strictness: "soft", weight: 0, provenance: "default" });
  });

  test("test_drawn_from_what_the_service_answered_the_settings_say_visiting_and_draw_no_budget_and_no_home", async () => {
    const { spec, places } = became.body.data;
    const named = Object.fromEntries(places.map((place) => [place.place_id, place.name]));
    const sent: Operations[] = [];
    render(
      <SettingsPanel
        spec={spec}
        meta={meta}
        areas={areas}
        placeNames={named}
        onEdit={(operations) => sent.push(operations)}
        onTenure={() => undefined}
        searchPlaces={() => Promise.resolve(failed("offline"))}
        onAddPlace={() => undefined}
        version={1}
        open
        onToggle={() => undefined}
        standing
      />,
    );
    const user = userEvent.setup({ delay: null });
    await user.click(screen.getByRole("button", { name: KIND_OF_SEARCH.legend }));

    expect(heldBy_(KIND_OF_SEARCH.legend)).toBe(KIND_OF_SEARCH.visit);
    expect(screen.getByRole("radio", { name: KIND_OF_SEARCH.visit })).toBeChecked();
    expect(screen.queryByRole("group", { name: BUDGET.legend })).toBeNull();
    expect(screen.queryByRole("combobox", { name: BUDGET.segment })).toBeNull();
    // The journey stayed, and its bar names the place by the name the answer gave it.
    expect(spec.commutes).toHaveLength(1);
    expect(heldBy_(SETTINGS.journeys)).toContain(places[0]?.name ?? "no place was named");
    expect(sent).toEqual([]);
  });

  test("test_with_visiting_chosen_the_settings_have_no_accessibility_fault", async () => {
    const { container, open } = show(visiting);
    await open(KIND_OF_SEARCH.legend, SETTINGS.journeys);

    expect(await faultsIn(container)).toEqual([]);
  });
});
