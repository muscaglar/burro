import { render, screen } from "@testing-library/react";

import { CONFIDENCE, COST } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { CostEstimate } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { CostRange, placesOnBar, scaleOf } from "./CostRange";

const farrowmere = recordedAnswer("get_area", "area/farrowmere").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;

/** What a one-bedroom home costs to rent in each area that has a figure for it. */
const rents: CostEstimate[] = areas.flatMap((area) =>
  recordedAnswer("get_area", `area/${area.slug}`).body.data.cost.filter(
    (cost) => cost.tenure === "rent" && cost.segment === "bed_1",
  ),
);

describe("the cost as a picture", () => {
  const [estimate] = farrowmere.cost.filter((cost) => cost.tenure === "rent" && cost.segment === "bed_1");
  const fact = farrowmere.facts.find((one) => one.fact_id === "syn-n0006/cost/rent.bed_1");
  if (!estimate || !fact) throw new Error("no recorded cost");

  test("test_the_bar_places_the_range_the_middle_and_the_budget_in_their_order", () => {
    const above = placesOnBar(estimate, 1700);
    expect(above.lower).toBeLessThan(above.median);
    expect(above.median).toBeLessThan(above.upper);
    expect(above.upper).toBeLessThan(above.budget ?? 0);

    const below = placesOnBar(estimate, 600);
    expect(below.budget ?? 100).toBeLessThan(below.lower);

    const inside = placesOnBar(estimate, estimate.median);
    expect(inside.budget).toBe(inside.median);
  });

  test("test_everything_on_the_bar_is_inside_it", () => {
    for (const amount of [null, 1, 600, 1125, 1700, 20000]) {
      for (const at of Object.values(placesOnBar(estimate, amount))) {
        if (at === null) continue;
        expect(at).toBeGreaterThanOrEqual(0);
        expect(at).toBeLessThanOrEqual(100);
      }
    }
  });

  test("test_how_sure_a_cost_is_is_said_in_the_word_the_fact_holds_as_an_areas_page_says_it", () => {
    // Seen in a browser: "High" on a card and "high" on the page of the same area. The
    // page of an area shows the fact's own slot. So does the card.
    render(<CostRange fact={fact} estimate={estimate} budget={{ amount: null }} />);

    const word = fact.slots.confidence ?? "";
    expect(word).toMatch(/^(high|medium|low)$/);
    expect(screen.getByText(COST.confidence).closest("div")?.querySelector("dd")?.textContent?.trim()).toBe(word);
    expect(new Set(Object.entries(CONFIDENCE).map(([code, said]) => code === said))).toEqual(new Set([true]));
  });

  test("test_with_no_budget_set_no_budget_is_marked_or_mentioned", () => {
    render(<CostRange fact={fact} estimate={estimate} budget={{ amount: null }} />);

    expect(screen.queryByText(/budget/i)).toBeNull();
    expect(placesOnBar(estimate, null).budget).toBeNull();
  });

  test("test_on_one_scale_the_budget_is_in_the_same_place_whatever_the_homes_cost", () => {
    // Seen by the reviewers: each bar was scaled to its own figures, so one budget of £1,700
    // sat at 91.7% on three cards and at 77% on two. Scanning down the list, it seemed to move.
    const scale = scaleOf(rents, 1700);
    const alone = new Set(rents.map((rent) => placesOnBar(rent, 1700).budget));
    const together = new Set(rents.map((rent) => placesOnBar(rent, 1700, scale).budget));

    expect(rents.length).toBeGreaterThan(10);
    expect(alone.size).toBeGreaterThan(1);
    expect(together.size).toBe(1);
  });

  test("test_on_one_scale_a_dearer_home_is_drawn_further_along_with_or_without_a_budget", () => {
    // With no budget every bar was the same picture, whatever the homes cost.
    const scale = scaleOf(rents, null);
    const alone = new Set(rents.map((rent) => placesOnBar(rent, null).lower));
    const inOrder = [...rents].sort((one, other) => one.lower_quartile - other.lower_quartile);
    const drawn = inOrder.map((rent) => placesOnBar(rent, null, scale).lower);

    expect(alone.size).toBe(1);
    expect(new Set(drawn).size).toBeGreaterThan(1);
    expect(drawn).toEqual([...drawn].sort((one, other) => one - other));
  });

  test("test_everything_drawn_on_a_shared_scale_is_inside_the_bar", () => {
    for (const amount of [null, 1, 600, 1700, 20000]) {
      const scale = scaleOf(rents, amount);
      for (const rent of rents) {
        for (const at of Object.values(placesOnBar(rent, amount, scale))) {
          if (at === null) continue;
          expect(at).toBeGreaterThanOrEqual(0);
          expect(at).toBeLessThanOrEqual(100);
        }
      }
    }
  });

  test("test_with_nothing_to_share_a_scale_with_the_bar_is_drawn_on_its_own", () => {
    expect(scaleOf([], null)).toBeNull();
    expect(placesOnBar(estimate, 1700, null)).toEqual(placesOnBar(estimate, 1700));
  });

  test("test_the_word_for_how_sure_a_cost_is_leads_to_what_it_means", () => {
    render(<CostRange fact={fact} estimate={estimate} budget={{ amount: 1700 }} />);

    // "Confidence: medium" was the one graded sign of how far to trust a figure, and no page said what it meant.
    const link = screen.getByRole("link", { name: COST.confidence });
    expect(link).toHaveAttribute("href", "/methods#confidence");
    expect(link).toHaveClass("target-min");
    // Which page a person reads next is told to no server ahead of time.
    expect(link).toHaveAttribute("data-prefetch", "false");
  });

  test("test_the_picture_has_a_name_and_the_pips_are_kept_from_a_reader", async () => {
    const { container } = render(<CostRange fact={fact} estimate={estimate} budget={{ amount: 1700 }} />);

    expect(screen.getByRole("img")).toHaveAccessibleName();
    expect(container.querySelector("[class*='pips']")).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelectorAll("[class*='pips'] [data-on='true']")).toHaveLength(2);
    expect(await faultsIn(container)).toEqual([]);
  });
});
