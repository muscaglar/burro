import { render, screen } from "@testing-library/react";

import { ONE_NUMBER } from "@/content/facts";
import { CONFIDENCE, COST } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { CostEstimate } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { CostRange, hasARange, placesOnBar, scaleOf } from "./CostRange";

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
    expect(above.lower ?? 100).toBeLessThan(above.median);
    expect(above.median).toBeLessThan(above.upper ?? 0);
    expect(above.upper ?? 100).toBeLessThan(above.budget ?? 0);

    const below = placesOnBar(estimate, 600);
    expect(below.budget ?? 100).toBeLessThan(below.lower ?? 0);

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
    const inOrder = [...rents].sort((one, other) => (one.lower_quartile ?? 0) - (other.lower_quartile ?? 0));
    const drawn = inOrder.map((rent) => placesOnBar(rent, null, scale).lower ?? -1);

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
    // The recorded cost is of high confidence, which is three pips of three.
    expect(estimate.confidence).toBe("high");
    expect(container.querySelectorAll("[class*='pips'] [data-on='true']")).toHaveLength(3);
    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a price that is one number", () => {
  // A release whose prices are as a publisher gives them: the middle price, and no range.
  const area = recordedAnswer("get_area", "one-number/area").body.data;
  const [estimate] = area.cost.filter((cost) => cost.tenure === "buy" && cost.segment === "flat");
  const fact = area.facts.find((one) => one.kind === "cost" && one.key === "buy.flat");
  if (!estimate || !fact) throw new Error("no recorded price");
  const ranked = recordedAnswer("rank", "one-number/rank-buyer").body.data;
  const amount = ranked.spec.budget.amount ?? 0;

  test("test_the_recorded_price_is_one_number_with_no_range_and_nothing_said_of_how_sure_it_is", () => {
    expect([estimate.lower_quartile, estimate.upper_quartile, estimate.confidence]).toEqual([null, null, "unstated"]);
    expect(fact.template).toBe("cost_buy_median");
    expect(hasARange(estimate)).toBe(false);
    expect(amount).toBeGreaterThan(0);
  });

  test("test_one_number_is_drawn_as_one_number_and_never_as_a_range", () => {
    const { container } = render(<CostRange fact={fact} estimate={estimate} budget={{ amount }} />);
    const said = container.textContent ?? "";

    expect(container.querySelector("[class*='figure']")?.textContent).toBe(`£${fact.slots.median}`);
    // No second figure stands beside it as the end of a range, and no block is drawn for one.
    expect(said.includes(` ${COST.to} £`)).toBe(false);
    expect(container.querySelector("[class*='span']")).toBeNull();
    expect(placesOnBar(estimate, amount)).toMatchObject({ lower: null, upper: null });
  });

  test("test_it_says_what_the_number_is_of_and_what_is_not_known_of_it", () => {
    render(<CostRange fact={fact} estimate={estimate} budget={{ amount: null }} />);

    expect(screen.getByText(COST.middleOfAll)).toBeInTheDocument();
    expect(screen.getByText(fact.slots.period ?? "no period")).toBeInTheDocument();
    expect(screen.getByText(ONE_NUMBER)).toBeInTheDocument();
  });

  test("test_no_word_and_no_pip_says_how_sure_one_number_is", () => {
    const { container } = render(<CostRange fact={fact} estimate={estimate} budget={{ amount }} />);

    expect(screen.queryByRole("link", { name: COST.confidence })).toBeNull();
    expect(container.querySelector("[class*='pips']")).toBeNull();
    expect((container.textContent ?? "").includes(CONFIDENCE.unstated)).toBe(false);
  });

  test.each([
    ["below", -1, COST.belowMiddle],
    ["above", 1, COST.aboveMiddle],
    ["at", 0, COST.atMiddle],
  ] as const)("test_the_budget_is_said_to_be_%s_the_middle_price", (_, more, words) => {
    render(<CostRange fact={fact} estimate={estimate} budget={{ amount: estimate.median + more }} />);

    expect(screen.getByText(words)).toBeInTheDocument();
    for (const range of [COST.below, COST.above, COST.inside]) expect(screen.queryByText(range)).toBeNull();
  });

  test("test_with_no_budget_set_no_picture_is_drawn_and_no_budget_is_mentioned", () => {
    render(<CostRange fact={fact} estimate={estimate} budget={{ amount: null }} />);

    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.queryByText(/budget/i)).toBeNull();
  });

  test("test_on_one_scale_one_number_counts_as_itself_and_is_drawn_inside_the_bar", () => {
    const scale = scaleOf([estimate], amount);
    if (scale === null) throw new Error("no scale");

    expect(scale.from).toBeLessThan(Math.min(estimate.median, amount));
    expect(scale.to).toBeGreaterThan(Math.max(estimate.median, amount));
    for (const at of Object.values(placesOnBar(estimate, amount, scale))) {
      if (at === null) continue;
      expect(at).toBeGreaterThanOrEqual(0);
      expect(at).toBeLessThanOrEqual(100);
    }
  });

  test("test_the_picture_of_one_number_has_a_name_and_no_fault", async () => {
    const { container } = render(<CostRange fact={fact} estimate={estimate} budget={{ amount }} />);

    expect(screen.getByRole("img")).toHaveAccessibleName(COST.pictureOfOne);
    expect(await faultsIn(container)).toEqual([]);
  });
});
