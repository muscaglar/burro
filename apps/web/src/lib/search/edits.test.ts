import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations } from "@/lib/api/schema";

import { problemsWith } from "../../../test/support/contract";
import { answered, chipOf, countOf, edits, GROUPS, isEmpty, merged, NO_EDITS, saidBy } from "./edits";

const EVERY_EDIT: readonly (readonly [string, Operations])[] = [
  ["tenure", edits.tenure("buy")],
  ["budgetAmount", edits.budgetAmount(1700)],
  ["budgetStep", edits.budgetStep("up_small")],
  ["budgetClear", edits.budgetClear()],
  ["budgetSegment", edits.budgetSegment("bed_2")],
  ["budgetStrictness", edits.budgetStrictness("hard")],
  ["budgetWeight", edits.budgetWeight(0.6)],
  ["placeAdd", edits.placeAdd("syn-p0021")],
  ["placeMode", edits.placeMode("syn-p0021", "cycle")],
  ["placeMinutes", edits.placeMinutes("syn-p0021", 30)],
  ["placeStep", edits.placeStep("syn-p0021", "down_small")],
  ["placeStrictness", edits.placeStrictness("syn-p0021", "hard")],
  ["placeRemove", edits.placeRemove("syn-p0021")],
  ["journeyCombine", edits.journeyCombine("mean")],
  ["journeyBasis", edits.journeyBasis("just_missed")],
  ["journeyWeight", edits.journeyWeight(0.5)],
  ["featureOn", edits.featureOn("park_proximity")],
  ["featureWeight", edits.featureWeight("park_proximity", 0.4)],
  ["featureDirection", edits.featureDirection("venue_evening", 0.5, "less")],
  ["featureOff", edits.featureOff("park_proximity")],
  ["tagOn", edits.tagOn("leafy")],
  ["tagWeight", edits.tagWeight("leafy", 0.25)],
  ["tagOff", edits.tagOff("leafy")],
  ["areaHide", edits.areaHide("syn-n0006")],
  ["areaClear", edits.areaClear("syn-n0006")],
];

describe("the edits a control sends", () => {
  test("test_there_is_a_test_for_every_edit_a_control_can_make", () => {
    expect(EVERY_EDIT.map(([name]) => name).sort()).toEqual(Object.keys(edits).sort());
  });

  test.each(EVERY_EDIT)("test_an_edit_is_one_the_contract_accepts: %s", (_, operations) => {
    expect(problemsWith("Operations", operations)).toEqual([]);
  });

  test.each(EVERY_EDIT)("test_an_edit_holds_one_edit_made_by_a_control: %s", (_, operations) => {
    const all = GROUPS.flatMap((group) => [...operations[group]]);

    expect(all).toHaveLength(1);
    expect(all[0]?.provenance).toBe("ui_edit");
    expect(Object.keys(operations).sort()).toEqual([...GROUPS].sort());
  });

  test("test_a_control_sends_the_edit_the_api_was_recorded_taking", () => {
    // Recorded: the journey made firm and five minutes shorter, in one edit.
    // A control changes one thing, so each sends that edit with one field filled.
    const sent = recordedAnswer("rank", "rank-refined").request.body as {
      operations: Operations;
    };
    const [recorded] = sent.operations.commute_ops;

    expect(edits.placeMinutes("syn-p0021", 30).commute_ops).toEqual([
      { ...recorded, strictness: "unchanged" },
    ]);
    expect(edits.placeStrictness("syn-p0021", "hard").commute_ops).toEqual([
      { ...recorded, max_minutes: 0 },
    ]);
  });

  test("test_an_edit_that_is_not_an_edit_is_caught_by_the_check_these_tests_rely_on", () => {
    const broken = { ...NO_EDITS, tag_ops: [{ action: "set" }] };

    expect(problemsWith("Operations", broken).length).toBeGreaterThan(0);
  });

  test("test_switching_a_feature_on_is_worth_what_a_word_is", () => {
    const said = recordedAnswer("interpret", "interpret-rejected").body.data.operations;

    const [byControl] = edits.featureOn("park_proximity").weight_ops;
    const byWord = said.weight_ops.find((edit) => edit.feature_id === "park_proximity");

    expect(byControl).toEqual({ ...byWord, provenance: "ui_edit" });
  });

  test("test_a_field_an_edit_does_not_change_carries_its_sentinel", () => {
    expect(edits.budgetStrictness("hard").budget_ops[0]).toEqual({
      action: "set",
      tenure: "unchanged",
      amount: 0,
      segment: "unchanged",
      strictness: "hard",
      step: "none",
      provenance: "ui_edit",
    });
    expect(edits.placeStep("syn-p0021", "up_small").commute_ops[0]).toMatchObject({
      action: "update",
      max_minutes: 0,
      mode: "unchanged",
      strictness: "unchanged",
      step: "up_small",
    });
  });

  test("test_edits_made_together_are_kept_in_the_order_they_were_made", () => {
    const both = merged(edits.tagWeight("leafy", 0.4), edits.tagWeight("leafy", 0.6));

    expect(both.tag_ops.map((edit) => edit.value)).toEqual([0.4, 0.6]);
    expect(countOf(both)).toBe(2);
    expect(isEmpty(both)).toBe(false);
    expect(isEmpty(NO_EDITS)).toBe(true);
    expect(merged(NO_EDITS, NO_EDITS)).toEqual(NO_EDITS);
  });
});

describe("the answer to a question about a place", () => {
  const { operations, clarify } = recordedAnswer("interpret", "interpret-clarify").body.data;
  const question = clarify[0];
  if (!question) throw new Error("the recording holds no question");

  test("test_the_answer_is_the_edit_asked_about_with_the_chosen_place_in_it", () => {
    const option = question.options[1];
    if (!option) throw new Error("the recording holds no second option");

    const answer = answered(operations, question.group, question.index, option.id);

    expect(answer).toEqual({
      ...NO_EDITS,
      commute_ops: [{ ...operations.commute_ops[0], place_id: "syn-p0017" }],
    });
    // What the words said of the journey is kept: thirty minutes, as the person said it.
    expect(answer?.commute_ops[0]).toMatchObject({ max_minutes: 30, provenance: "stated" });
    expect(problemsWith("Operations", answer)).toEqual([]);
  });

  test("test_a_question_that_points_at_no_edit_has_no_answer", () => {
    expect(answered(operations, "commute_ops", 7, "syn-p0017")).toBeNull();
    expect(answered(operations, "tag_ops", 0, "syn-p0017")).toBeNull();
  });
});

describe("which part of the search an edit is about", () => {
  test("test_an_assumption_is_tied_to_the_part_its_edit_names", () => {
    const { operations, assumptions } = recordedAnswer("interpret", "interpret-first").body.data;

    const parts = assumptions.map(({ group, index, code }) => [
      code,
      chipOf(operations, group, index, code),
    ]);

    expect(parts).toEqual([
      ["strictness", "budget"],
      ["mode", "place:syn-p0021"],
      ["strictness", "place:syn-p0021"],
    ]);
  });

  test("test_an_assumed_tenure_belongs_to_the_tenure_and_not_to_the_budget", () => {
    const operations = edits.budgetAmount(1500);

    expect(chipOf(operations, "budget_ops", 0, "tenure")).toBe("tenure");
    expect(chipOf(operations, "budget_ops", 0, "segment")).toBe("budget");
    expect(chipOf(operations, "budget_ops", 3, "segment")).toBeNull();
  });

  test("test_an_edit_says_what_it_states_so_that_it_is_no_longer_an_assumption", () => {
    expect(saidBy(edits.placeMode("syn-p0021", "walk"), "commute_ops", 0)).toEqual([
      { key: "place:syn-p0021", states: ["mode"] },
    ]);
    expect(saidBy(edits.placeStep("syn-p0021", "up_small"), "commute_ops", 0)).toEqual([
      { key: "place:syn-p0021", states: ["max_minutes"] },
    ]);
    expect(saidBy(edits.budgetStrictness("hard"), "budget_ops", 0)).toEqual([
      { key: "budget", states: ["strictness"] },
    ]);
    expect(saidBy(edits.tenure("buy"), "budget_ops", 0)).toEqual([
      { key: "tenure", states: ["tenure"] },
    ]);
    expect(saidBy(edits.featureDirection("venue_evening", 0.5, "less"), "weight_ops", 0)).toEqual([
      { key: "feature:venue_evening", states: ["weight", "direction"] },
    ]);
    expect(saidBy(edits.tagWeight("leafy", 0.5), "tag_ops", 0)).toEqual([
      { key: "tag:leafy", states: ["weight"] },
    ]);
    expect(saidBy(edits.journeyBasis("typical"), "setting_ops", 0)).toEqual([
      { key: "journeys", states: [] },
    ]);
    expect(saidBy(edits.budgetWeight(0.5), "setting_ops", 0)).toEqual([
      { key: "budget", states: [] },
    ]);
    expect(saidBy(edits.areaHide("syn-n0006"), "area_ops", 0)).toEqual([
      { key: "area:syn-n0006", states: [] },
    ]);
  });
});
