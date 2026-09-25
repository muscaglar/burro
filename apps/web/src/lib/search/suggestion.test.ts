import { recordedAnswer } from "@/lib/api/recorded";

import {
  addedWithOthers,
  guessFirst,
  guessOf,
  keyOf,
  namesItsPlaces,
  noteOf,
  setsAFirmBudget,
  waysOf,
  withPlace,
} from "./suggestion";

const [pubs, noise] = recordedAnswer("interpret", "interpret-suggest").body.data.suggestions;
const long = recordedAnswer("interpret", "interpret-by-model-long").body.data.suggestions;
const [asks] = recordedAnswer("interpret", "interpret-by-model-place").body.data.suggestions;
const atOnce = recordedAnswer("interpret", "interpret-rules-at-once").body.data.suggestions;
const [quiet, parks] = long;
const journey = long.find((one) => one.target === "commute");
const budget = long.find((one) => one.target === "budget");
const renting = atOnce.find((one) => one.target === "tenure");
if (!pubs || !noise || !quiet || !parks || !journey || !budget || !renting || !asks) {
  throw new Error("a recording holds too little");
}

describe("what may be done with an offer", () => {
  test("test_doing_nothing_is_no_way_of_taking_a_thing", () => {
    expect(waysOf(pubs).map((choice) => choice.id)).toEqual(["more", "less"]);
    expect(waysOf(noise).map((choice) => choice.id)).toEqual(["less"]);
    expect(waysOf(parks).map((choice) => choice.id)).toEqual(["more", "off", "tag:parks_close_by/more"]);
  });

  test("test_the_guess_is_the_way_the_api_marks_and_the_page_marks_none", () => {
    expect(guessOf(journey)?.id).toBe("firm");
    expect(guessOf(parks)?.id).toBe("more");
    expect(guessOf(pubs)).toBeNull();
    expect(guessOf(noise)).toBeNull();
    // The rules guess at what was plainly said of the journey and of the home, and at no wish.
    expect(guessOf(renting)?.id).toBe("more");
    expect(atOnce.filter((one) => guessOf(one) !== null).map((one) => one.target)).toEqual([
      "commute",
      "tenure",
      "budget",
      "budget",
    ]);
  });

  test("test_a_note_is_read_as_it_came_and_an_empty_one_is_no_note", () => {
    expect(noteOf(noise)).toBeNull();
    expect(noteOf({ ...noise, note: "" })).toBeNull();
    expect(noteOf({ ...noise, note: "  " })).toBeNull();
    expect(noteOf({ ...noise, note: 3 })).toBeNull();
    expect(noteOf({ ...noise, note: "Counts only when asked for by name." })).toBe("Counts only when asked for by name.");
  });

  test("test_what_one_press_may_add_is_the_apis_to_say_and_never_the_pages", () => {
    expect(addedWithOthers(quiet)?.id).toBe("more");
    // Where the guess is a firm journey, one press adds the guide: a journey is estimated,
    // and one press leaves no area out on an estimate.
    expect(guessOf(journey)?.id).toBe("firm");
    expect(addedWithOthers(journey)?.id).toBe("guide");
    // A budget is added as it was worded, and "max" makes it a firm limit.
    expect(guessOf(budget)?.id).toBe("firm");
    expect(addedWithOthers(budget)?.id).toBe("firm");
    // A thing the API names no way for is never added, though there is one way to take it.
    expect(waysOf(noise)).toHaveLength(1);
    expect(addedWithOthers(noise)).toBeNull();
    expect(addedWithOthers(pubs)).toBeNull();
    expect(addedWithOthers(asks)).toBeNull();
  });

  test("test_a_way_the_api_names_that_the_offer_does_not_hold_adds_nothing", () => {
    expect(addedWithOthers({ ...quiet, add_all: "firm" })).toBeNull();
    expect(addedWithOthers({ ...quiet, add_all: "ignore" })).toBeNull();
  });

  test("test_a_journey_with_no_place_is_not_sent_until_the_person_has_chosen_one", () => {
    const [firm] = waysOf(asks);
    if (!firm) throw new Error("the offer holds no way");

    expect(namesItsPlaces(firm.operations)).toBe(false);
    const placed = withPlace(firm.operations, "syn-p0021");
    expect(namesItsPlaces(placed)).toBe(true);
    expect(placed.commute_ops.map((edit) => [edit.place_id, edit.max_minutes, edit.strictness])).toEqual([
      ["syn-p0021", 40, "hard"],
    ]);
    // A journey that names its place keeps it.
    const [named] = waysOf(journey);
    expect(withPlace(named?.operations ?? firm.operations, "syn-p0021")).toEqual(named?.operations);
  });

  test("test_a_firm_budget_is_known_by_the_edits_the_api_gave", () => {
    const edits = (one: typeof budget) => addedWithOthers(one)?.operations ?? { budget_ops: [] };

    expect(setsAFirmBudget(edits(budget))).toBe(true);
    // A journey as a guide, a wish, and the tenure, which holds no amount.
    expect([journey, quiet, renting].map((one) => setsAFirmBudget(edits(one)))).toEqual([false, false, false]);
  });

  test("test_the_offers_that_carry_a_guess_come_first_and_each_part_keeps_its_order", () => {
    const every = long.map((_, at) => at);

    expect(guessFirst(long, every)).toEqual([0, 1, 6, 10, 11, 2, 3, 4, 5, 7, 8, 9]);
    expect(guessFirst(long, [3, 10, 2, 0])).toEqual([10, 0, 3, 2]);
    // Where nothing carries a guess, nothing moves.
    expect(guessFirst([pubs, noise], [0, 1])).toEqual([0, 1]);
    expect(guessFirst(long, [])).toEqual([]);
  });

  test("test_an_offer_is_told_from_every_other_of_its_answer", () => {
    expect(new Set(long.map(keyOf)).size).toBe(long.length);
  });
});
