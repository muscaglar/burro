import { readdirSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FACT_KIND } from "@/content/facts";
import { SOURCE } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, ExplanationsData, Fact, TemplateId } from "@/lib/api/schema";

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
  return facts;
}

const all = everyFact();
const byTemplate = (template: TemplateId) => all.find((fact) => fact.template === template);

describe("a fact laid out in columns", () => {
  test("test_there_is_a_recorded_fact_of_nearly_every_template_to_test_with", () => {
    const seen = new Set(all.map((fact) => fact.template));

    expect((Object.keys(FACT_KIND) as TemplateId[]).filter((template) => !seen.has(template))).toEqual([]);
    expect(all.length).toBeGreaterThan(1000);
  });

  test("test_every_value_shown_is_a_slot_of_the_fact_as_the_api_formatted_it", () => {
    for (const fact of all) {
      const slots = Object.values(fact.slots);
      for (const [, value] of columnsOf(fact)) {
        // A money slot gets its pound sign, and a range its "to". Nothing else is added.
        const parts = (value ?? "").split(" to ").map((part) => part.replace(/^£/, ""));
        expect(parts.filter((part) => !slots.includes(part))).toEqual([]);
      }
    }
  });

  test.each([
    ["feature", ["Figure", "Where it sits"]],
    ["feature_crime", ["Figure", "Where it sits"]],
    ["tag", ["Where it sits"]],
    ["cost_rent", ["Kind of home", "Range", "Middle", "As of", "Confidence"]],
    ["cost_buy", ["Kind of home", "Range", "Middle", "As of", "Confidence"]],
    ["budget_under", ["Upper end of the range", "Your budget", "Under your budget by"]],
    ["budget_over", ["Upper end of the range", "Your budget", "Over your budget by"]],
    ["travel_pt", ["To", "How", "Typical minutes", "Minutes if you just miss one"]],
    ["travel_other", ["To", "How", "Minutes"]],
    ["station", ["Station", "Minutes on foot", "Lines"]],
    ["station_nearby", ["Station", "Minutes on foot", "Lines"]],
    ["area", ["Name", "Borough"]],
    ["missing", ["Name"]],
  ] as const)("test_the_columns_are_chosen_by_the_template: %s", (template, columns) => {
    const fact = byTemplate(template);
    if (!fact) throw new Error(`no recorded fact of template ${template}`);

    expect(columnsOf(fact).map(([column]) => column)).toEqual(columns);
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
