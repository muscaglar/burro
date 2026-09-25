import { readdirSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CANNOT_PLACE, FACT_KIND, ONE_NUMBER } from "@/content/facts";
import { JOURNEYS, SOURCE } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, ExplanationsData, Fact, JourneyBand, TemplateId } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { columnsOf, FactRow } from "./FactRow";

const farrowmere = recordedAnswer("get_area", "area/farrowmere").body.data;

/** Every fact of every recording: each area's profile, and each search's reasons. */
function everyFact(): Fact[] {
  const facts: Fact[] = [];
  for (const file of readdirSync(path.join(recordedFolder(), "area"))) {
    facts.push(...(readRecorded(`area/${file.replace(/\.json$/, "")}`).body as { data: AreaData }).data.facts);
  }
  for (const file of readdirSync(recordedFolder())) {
    if (!file.startsWith("explanations-")) continue;
    facts.push(...(readRecorded(file.replace(/\.json$/, "")).body as { data: ExplanationsData }).data.facts);
  }
  // The committed release holds every cost as a range. A price that is one number is
  // recorded from a release of its own.
  facts.push(...recordedAnswer("get_area", "one-number/area").body.data.facts);
  facts.push(...recordedAnswer("explain_top", "one-number/explanations-buyer").body.data.facts);
  // The committed release holds a time for every journey. A journey that is estimated is
  // recorded from a release that holds none.
  facts.push(...recordedAnswer("explain_top", "estimate/explanations").body.data.facts);
  facts.push(...recordedAnswer("compare", "estimate/compare").body.data.facts);
  // And a price that was counted from sales, from another.
  facts.push(...recordedAnswer("get_area", "counted/area").body.data.facts);
  facts.push(...recordedAnswer("explain_top", "counted/explanations-firm").body.data.facts);
  return facts;
}

const all = everyFact();
const byTemplate = (template: TemplateId) => all.find((fact) => fact.template === template);

describe("a fact laid out in columns", () => {
  test("test_there_is_a_recorded_fact_of_nearly_every_template_to_test_with", () => {
    const seen = new Set(all.map((fact) => fact.template));

    // No two areas of the made-up city are alike in every measure, so none is said to be.
    expect((Object.keys(FACT_KIND) as TemplateId[]).filter((template) => !seen.has(template))).toEqual([
      "likeness_same",
    ]);
    expect(all.length).toBeGreaterThan(1000);
  });

  test("test_every_value_shown_is_a_slot_of_the_fact_as_the_api_formatted_it", () => {
    for (const fact of all) {
      const slots = Object.values(fact.slots);
      for (const [, value] of columnsOf(fact)) {
        // A money slot gets its pound sign, and a range its "to". Nothing else is added. The
        // figure of a measure in pounds comes with its sign, as every figure comes with its unit.
        const parts = (value ?? "").split(" to ");
        const held = (part: string) => slots.includes(part) || slots.includes(part.replace(/^£/, ""));
        expect(parts.filter((part) => !held(part))).toEqual([]);
      }
    }
  });

  test.each([
    ["feature", ["Figure", "Where it sits"]],
    ["feature_crime", ["Figure", "Where it sits"]],
    ["vibe", ["Band, of five", "Counted from", "Areas compared in this release", "Parts dated"]],
    ["vibe_range", ["Varies within this area, across bands", "Counted from", "Parts dated"]],
    ["vibe_unknown", ["Parts with a figure in this release", "Parts in the recipe"]],
    ["cost_rent", ["Kind of home", "Range", "Middle", "As of", "Confidence"]],
    ["cost_buy", ["Kind of home", "Range", "Middle", "As of", "Confidence"]],
    ["cost_buy_median", ["Kind of home", "Middle price, homes of all sizes", "Homes sold in"]],
    ["cost_buy_sold", ["Kind of home", "Middle price, homes of all sizes", "Homes sold in", "Sales it rests on"]],
    ["budget_under", ["Upper end of the range", "Your budget", "Under your budget by"]],
    ["budget_over", ["Upper end of the range", "Your budget", "Over your budget by"]],
    ["budget_under_median", ["Middle price, homes of all sizes", "Your budget", "Under your budget by"]],
    ["budget_over_median", ["Middle price, homes of all sizes", "Your budget", "Over your budget by"]],
    ["travel_pt", ["To", "How", "Typical minutes", "Minutes if you just miss one"]],
    ["travel_other", ["To", "How", "Minutes"]],
    ["travel_estimated", ["To", "How", "How this is known"]],
    ["likeness", ["Alike", "Measures in the same band", "Measures compared", "Least alike in"]],
    ["missing_journey", ["Name", "To"]],
    ["station", ["Station", "Minutes on foot", "Lines"]],
    ["station_nearby", ["Station", "Minutes on foot", "Lines"]],
    ["area", ["Name", "Borough"]],
    ["missing", ["Name"]],
  ] as const)("test_the_columns_are_chosen_by_the_template: %s", (template, columns) => {
    const fact = byTemplate(template);
    if (!fact) throw new Error(`no recorded fact of template ${template}`);

    // A journey of a search that sets a limit says where it stands against it as well. So
    // does a vibe say how many parts it rests on, where that is not all of them.
    const shown = columnsOf(fact).map(([column]) => column);
    const whole = fact.kind !== "tag" || fact.template === "vibe_unknown";
    expect(
      shown
        .filter((column) => !/your limit/i.test(column))
        .filter((column) => whole || !/^Parts (with a figure|in the recipe)/.test(column)),
    ).toEqual(columns);
  });

  test.each([
    ["travel_pt", "Under your limit by, in minutes"],
    ["travel_pt_over", "Over your limit by, in minutes"],
    ["travel_other_over", "Over your limit by, in minutes"],
  ] as const)("test_a_journey_says_where_it_stands_against_the_limit_that_was_set: %s", (template, column) => {
    const fact = all.find((one) => one.template === template && one.slots.limit !== undefined);
    if (!fact) throw new Error(`no recorded journey of template ${template} with a limit`);

    expect(Object.fromEntries(columnsOf(fact))).toMatchObject({
      "Your limit, in minutes": fact.slots.limit,
      [column]: fact.slots.margin,
    });
  });

  test("test_a_journey_that_was_estimated_says_its_band_and_that_it_is_an_estimate_and_gives_no_minutes", () => {
    const bands = all.filter((fact) => fact.template === "travel_estimated");

    // One of each band is recorded: likely within, borderline and likely beyond.
    expect(new Set(bands.map((fact) => fact.slots.band))).toEqual(
      new Set(["likely_within", "borderline", "likely_beyond"]),
    );
    for (const fact of bands) {
      expect(Object.fromEntries(columnsOf(fact))).toEqual({
        To: fact.slots.place,
        How: fact.slots.mode,
        "Your limit, in minutes": fact.slots.limit,
        "Against your limit": fact.slots.verdict,
        "How this is known": fact.slots.estimated,
      });
      // The words the website says a band in, and the line under it, are the API's own.
      expect(fact.slots.verdict).toBe(JOURNEYS.estimated[fact.slots.band as JourneyBand]);
      expect(fact.slots.estimated).toBe(JOURNEYS.estimatedFrom);
      // An estimate is never given in minutes: the one number of the fact is the limit.
      expect(fact.numbers).toEqual([fact.slots.limit]);
      for (const slot of ["minutes", "typical", "missed", "margin"]) expect(fact.slots[slot]).toBeUndefined();
    }
  });

  test("test_a_price_that_is_one_number_is_a_row_of_one_number_and_says_what_is_not_known_of_it", () => {
    const price = byTemplate("cost_buy_median");
    if (!price) throw new Error("no recorded price of one number");
    render(<FactRow fact={price} name={price.slots.segment} />);
    const row = screen.getByRole("group", { name: price.slots.segment });

    expect(Object.fromEntries(columnsOf(price))).toEqual({
      "Kind of home": price.slots.segment,
      "Middle price, homes of all sizes": `£${price.slots.median}`,
      "Homes sold in": price.slots.period,
    });
    // No range, and no word for how sure it is: neither is known, and the row says so.
    expect(columnsOf(price).map(([column]) => column)).not.toContain("Range");
    expect(columnsOf(price).map(([column]) => column)).not.toContain("Confidence");
    expect(row).toHaveTextContent(ONE_NUMBER);
    expect(row.textContent?.includes("unstated")).toBe(false);
  });

  test("test_a_range_is_never_said_to_lack_a_range", () => {
    const range = byTemplate("cost_buy");
    if (!range) throw new Error("no recorded range");
    render(<FactRow fact={range} />);

    expect(screen.queryByText(ONE_NUMBER)).toBeNull();
  });

  test("test_a_vibe_is_a_band_between_its_two_ends_and_never_a_score", () => {
    const pace = all.find((fact) => fact.template === "vibe" && fact.key === "pace");
    if (!pace) throw new Error("no recorded vibe");
    render(<FactRow fact={pace} />);
    const row = screen.getByRole("group", { name: "Going out" });

    expect(Object.fromEntries(columnsOf(pace))).toMatchObject({
      "Band, of five": pace.slots.band,
      "Counted from": "Calm to Buzzy",
    });
    // What every sentence about a vibe ends in, word for word.
    expect(row).toHaveTextContent("The recipe is Burro's own. The weights are a judgement.");
    expect(row.textContent?.includes("%")).toBe(false);
  });

  test("test_a_band_that_rests_on_part_of_a_recipe_says_how_many_parts_have_a_figure", () => {
    const marrowfen = (readRecorded("area/marrowfen").body as { data: AreaData }).data.facts;
    const part = marrowfen.find((fact) => fact.kind === "tag" && fact.key === "quiet_residential");
    const whole = marrowfen.find((fact) => fact.kind === "tag" && fact.key === "leafy");
    if (!part || !whole) throw new Error("no recorded vibe");

    // Marrowfen has no figure for transport noise, so Quiet streets is placed from two parts of three.
    expect([part.template, part.slots.band, part.slots.known, part.slots.parts]).toEqual(["vibe", "2", "2", "3"]);
    expect(Object.fromEntries(columnsOf(part))).toMatchObject({
      "Parts with a figure in this release": "2",
      "Parts in the recipe": "3",
    });
    // A band that rests on the whole of its recipe says no more than it did.
    expect([whole.slots.known, whole.slots.parts]).toEqual(["3", "3"]);
    expect(columnsOf(whole).map(([column]) => column)).toEqual([
      "Band, of five",
      "Counted from",
      "Areas compared in this release",
      "Parts dated",
    ]);
  });

  test("test_the_share_of_the_recipe_a_band_rests_on_is_given_where_the_fact_holds_it", () => {
    const marrowfen = (readRecorded("area/marrowfen").body as { data: AreaData }).data.facts;
    const part = marrowfen.find((fact) => fact.kind === "tag" && fact.key === "quiet_residential");
    const whole = marrowfen.find((fact) => fact.kind === "tag" && fact.key === "leafy");
    if (!part || !whole) throw new Error("no recorded vibe");

    const told = columnsOf({ ...part, slots: { ...part.slots, share: "70" } });

    expect(Object.fromEntries(told)).toMatchObject({
      "Parts with a figure in this release": "2",
      "Parts in the recipe": "3",
      "Share of the recipe they carry, in hundredths": "70",
    });
    // Of a band that rests on the whole of its recipe nothing is said, whatever the fact holds.
    const shown = columnsOf({ ...whole, slots: { ...whole.slots, share: "100" } }).map(([column]) => column);
    expect(shown.filter((column) => /^(Parts|Share)/.test(column))).toEqual(["Parts dated"]);
  });

  test("test_a_mixed_area_that_rests_on_part_of_a_recipe_says_so_too", () => {
    const mixed = byTemplate("vibe_range");
    if (!mixed) throw new Error("no recorded mixed area");

    const columns = columnsOf({ ...mixed, slots: { ...mixed.slots, known: "3", parts: "4" } });

    expect(Object.fromEntries(columns)).toMatchObject({
      "Parts with a figure in this release": "3",
      "Parts in the recipe": "4",
    });
  });

  test("test_a_mixed_area_is_a_range_of_bands", () => {
    const mixed = byTemplate("vibe_range");
    if (!mixed) throw new Error("no recorded mixed area");

    expect(Object.fromEntries(columnsOf(mixed))["Varies within this area, across bands"]).toBe(
      `${mixed.slots.spread_low} to ${mixed.slots.spread_high}`,
    );
    expect(columnsOf(mixed).map(([column]) => column)).not.toContain("Band, of five");
  });

  test("test_an_area_a_vibe_cannot_place_says_so_and_shows_no_band", () => {
    const unknown = byTemplate("vibe_unknown");
    if (!unknown) throw new Error("no recorded vibe that cannot place an area");
    render(<FactRow fact={unknown} />);

    expect(screen.getByRole("group")).toHaveTextContent(CANNOT_PLACE);
    expect(columnsOf(unknown).map(([column]) => column)).not.toContain("Band, of five");
  });

  test("test_a_fact_of_a_template_the_website_was_not_built_with_is_named_and_shows_no_column", () => {
    // Seen when every mark of a result was opened: the page stopped on a template it did not know.
    const known = byTemplate("vibe");
    if (!known) throw new Error("no recorded vibe");
    const newer = { ...known, template: "weather_report" } as unknown as Fact;
    render(<FactRow fact={newer} />);

    expect(columnsOf(newer)).toEqual([]);
    expect(screen.getByRole("group", { name: known.label })).toBeInTheDocument();
    expect(screen.queryAllByRole("term")).toEqual([]);
  });

  test("test_a_journey_beyond_the_cutoff_says_more_than_and_gives_no_time", () => {
    // Recorded: on foot to a place that is more than an hour from most areas.
    const beyond = byTemplate("travel_beyond");
    if (!beyond) throw new Error("no recorded journey beyond the longest time the release holds");

    expect(beyond.slots).toMatchObject({ mode: "On foot", place: "Cindermoor Works", cutoff: "60" });
    expect(columnsOf(beyond)).toEqual([
      ["To", "Cindermoor Works"],
      ["How", "On foot"],
      ["More than, in minutes", "60"],
    ]);
    // No time is given, because none is known.
    expect(Object.keys(beyond.slots).filter((slot) => /minutes|typical|missed/.test(slot))).toEqual([]);
  });

  test("test_a_money_slot_gets_its_pound_sign_and_nothing_else", () => {
    const cost = farrowmere.facts.find((fact) => fact.fact_id === "syn-n0006/cost/rent.bed_1");
    if (!cost) throw new Error("no recorded cost");

    expect(Object.fromEntries(columnsOf(cost))).toMatchObject({
      Range: "£975 to £1,300",
      Middle: "£1,125",
      "As of": "August 2026",
    });
  });

  test("test_never_a_percentile", () => {
    const feature = byTemplate("feature");
    if (!feature) throw new Error("no recorded feature");

    const shown = columnsOf(feature).map(([, value]) => value);

    // Where a figure sits is the API's own clause, which is literally true of the release.
    expect(shown).toEqual([feature.slots.value, feature.slots.standing]);
    expect(shown).not.toContain(feature.slots.pct);
  });

  test("test_under_a_figure_of_recorded_crime_stands_the_caveat_word_for_word", () => {
    const crime = byTemplate("feature_crime");
    const other = byTemplate("feature");
    if (!crime || !other) throw new Error("no recorded feature");

    const { unmount } = render(<FactRow fact={crime} />);
    expect(screen.getByText(CRIME_CAVEAT)).toBeInTheDocument();
    unmount();

    render(<FactRow fact={other} />);
    expect(screen.queryByText(CRIME_CAVEAT)).toBeNull();
  });

  test("test_a_row_is_named_and_ends_in_its_source", async () => {
    const station = byTemplate("station");
    if (!station) throw new Error("no recorded station");
    render(<FactRow fact={station} />);

    const row = within(screen.getByRole("group", { name: "Nearest station" }));
    await userEvent.setup({ delay: null }).click(row.getByRole("button", { name: SOURCE.buttonFor("Nearest station") }));

    expect(row.getByRole("link", { name: station.sources[0]?.name })).toBeInTheDocument();
  });

  test("test_a_station_that_is_not_the_nearest_is_not_called_the_nearest", () => {
    const nearby = byTemplate("station_nearby");
    if (!nearby) throw new Error("no recorded station nearby");
    render(<FactRow fact={nearby} />);

    expect(screen.getByRole("group", { name: "Station within a short walk" })).toBeInTheDocument();
    expect(screen.queryByText(/nearest/i)).toBeNull();
  });

  test("test_a_row_has_no_accessibility_fault", async () => {
    const crime = byTemplate("feature_crime");
    if (!crime) throw new Error("no recorded crime figure");
    const { container } = render(<FactRow fact={crime} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a fact on a page that must read with scripts off", () => {
  const cost = farrowmere.facts.find((fact) => fact.template === "cost_rent") as Fact;

  test("test_the_source_is_written_out_under_the_row_and_no_button_is_needed", () => {
    render(<FactRow fact={cost} source="line" />);
    const row = screen.getByRole("group");

    expect(within(row).queryByRole("button")).toBeNull();
    expect(within(row).getByRole("link", { name: cost.sources[0]?.name })).toHaveAttribute(
      "href",
      `/sources#${cost.sources[0]?.source_id}`,
    );
    expect(row).toHaveTextContent(`${SOURCE.dataFrom} August 2026`);
    expect(row).toHaveTextContent(SOURCE.madeUp);
  });

  test("test_the_source_is_behind_its_button_unless_a_line_is_asked_for", () => {
    render(<FactRow fact={cost} />);

    expect(within(screen.getByRole("group")).getByRole("button", { name: /^Source/ })).toBeInTheDocument();
    expect(within(screen.getByRole("group")).queryByRole("link")).toBeNull();
  });

  test("test_a_row_can_be_named_by_a_slot_of_its_fact_where_its_label_names_several_alike", () => {
    render(<FactRow fact={cost} source="line" name={cost.slots.segment} />);

    expect(screen.getByRole("group", { name: cost.slots.segment })).toHaveTextContent(`£${cost.slots.median}`);
    expect(cost.label).toBe("Rent");
  });

  test("test_a_column_that_only_repeats_the_name_of_the_row_is_left_out", () => {
    const { unmount } = render(<FactRow fact={cost} source="line" name={cost.slots.segment} />);
    const named = within(screen.getByRole("group"));

    // The kind of home is the row's name, so it is not said again as its first column.
    expect(named.getAllByRole("term").map((term) => term.textContent)).toEqual([
      "Range",
      "Middle",
      "As of",
      "Confidence",
    ]);
    expect(named.getAllByText(cost.slots.segment ?? "no kind")).toHaveLength(1);
    unmount();

    // Named by its label, the row still says what kind of home it is of.
    render(<FactRow fact={cost} source="line" />);
    expect(within(screen.getByRole("group")).getAllByRole("term")[0]).toHaveTextContent("Kind of home");
  });

  test("test_a_row_with_its_source_written_out_has_no_accessibility_fault", async () => {
    const { container } = render(<FactRow fact={cost} source="line" />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
