import { recordedAnswer } from "@/lib/api/recorded";
import type { PreferenceSpec } from "@/lib/api/schema";

import { leadsOf, mostAskedOfThePlace } from "./leads";

const specOf = (scenario: string): PreferenceSpec => recordedAnswer("interpret", scenario).body.data.spec;
const asked = specOf("interpret-first");
/** The same search, once the person has made the journey and the budget count for more than the place. */
const first: PreferenceSpec = { ...asked, commute_weight: 1, budget: { ...asked.budget, weight: 0.8 } };

describe("what counts most in a search", () => {
  test("test_what_is_asked_of_the_place_in_a_word_outweighs_a_journey_and_a_budget", () => {
    // A person asked for leafy and quiet, named a workplace and a budget. Each thing asked of
    // the place counts for more than the journey, and for more than the budget.
    expect(asked.tags.map((tag) => [tag.tag_id, tag.weight])).toEqual([
      ["leafy", 0.5],
      ["quiet_residential", 0.5],
    ]);
    expect([asked.commute_weight, asked.budget.weight]).toEqual([0.4, 0.3]);

    expect(leadsOf(asked)).toBeNull();
  });

  test("test_a_journey_and_a_budget_that_were_made_to_count_for_more_outweigh_a_vibe", () => {
    // Seen in a browser, when a journey and a budget counted for 1 and 0.8 until a person said
    // otherwise: the first five results sat in bands 3, 2, 3, 4 and 4 for Leafy, and the page
    // said "What you asked for counts most." Now they count so only where a person made them.
    expect([first.commute_weight, first.budget.weight]).toEqual([1, 0.8]);

    expect(leadsOf(first)).toEqual({ journey: true, budget: true, journeys: 1 });
  });

  test("test_with_nothing_asked_of_the_place_nothing_is_outweighed", () => {
    // Rent and a workplace alone: the journey and the budget are what was asked for.
    const spec = specOf("interpret-money-and-work");

    expect(mostAskedOfThePlace(spec)).toBe(0);
    expect(leadsOf(spec)).toBeNull();
    expect(leadsOf(recordedAnswer("get_meta", "meta").body.data.defaults.rent)).toBeNull();
  });

  test("test_a_setting_nobody_chose_is_not_what_was_asked_of_the_place", () => {
    const usual = first.weights.filter((weight) => weight.provenance === "default");

    expect(usual.length).toBeGreaterThan(0);
    expect(mostAskedOfThePlace({ tags: [], weights: usual })).toBe(0);
    // A thing a person took off counts for nothing.
    expect(mostAskedOfThePlace({ tags: first.tags.map((tag) => ({ ...tag, weight: 0 })), weights: [] })).toBe(0);
  });

  test("test_only_what_the_search_holds_can_outweigh", () => {
    // A vibe and no journey and no budget: the weights the spec keeps for them count for nothing.
    expect(leadsOf(specOf("interpret-scale"))).toBeNull();
    // A journey and no budget.
    const byTheRiver = specOf("interpret-by-the-river");
    expect(leadsOf(byTheRiver)).toBeNull();
    expect(leadsOf({ ...byTheRiver, commute_weight: 1 })).toEqual({ journey: true, budget: false, journeys: 1 });
    expect(leadsOf({ ...first, commutes: [] })).toEqual({ journey: false, budget: true, journeys: 0 });
  });

  test("test_a_vibe_the_person_made_count_as_much_is_not_outweighed", () => {
    const raised = { ...first, tags: first.tags.map((tag) => ({ ...tag, weight: 1 })) };

    expect(leadsOf(raised)).toBeNull();
    // Level with the budget, and under the journey.
    const level = { ...first, tags: first.tags.map((tag) => ({ ...tag, weight: 0.8 })) };
    expect(leadsOf(level)).toEqual({ journey: true, budget: false, journeys: 1 });
  });
});
