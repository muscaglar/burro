import { LEFT_OUT } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";

import type { Refusal } from "./refusals";
import { leftOutOf, noticeOf, refusedOf } from "./said";
import type { Left } from "./state";

const beside = recordedAnswer("interpret", "interpret-suggest-notice").body.data;
const applied = recordedAnswer("interpret", "interpret-notice").body.data;
const offTopic = recordedAnswer("interpret", "interpret-off-topic").body.data;
const [least] = recordedAnswer("interpret", "interpret-by-model-least").body.data.suggestions;
if (!least) throw new Error("a recording holds too little");

const read = (data: typeof beside, took: number) => ({
  notice: data.notice,
  notice_text: data.notice_text,
  changed: data.applied.some((edit) => edit.changed),
  took,
});
const aHome = recordedAnswer("interpret", "visiting/interpret-home").body.data.suggestions;
type Said = Pick<Left, "label" | "does" | "follows"> & Partial<Pick<Left, "note" | "target">>;
const left = (why: Left["why"], of: Said = least): Left => ({
  why,
  target: of.target ?? "commute",
  label: of.label,
  does: of.does,
  follows: of.follows,
  note: of.note ?? "",
});

describe("the notice, once Burro has taken what it noticed", () => {
  test("test_the_notice_is_shown_as_it_came_where_nothing_was_taken", () => {
    expect(noticeOf(read(beside, 0))).toBe(beside.notice_text);
    expect(noticeOf(read(offTopic, 0))).toBe(offTopic.notice_text);
    expect(noticeOf(read(applied, 0))).toBe(applied.notice_text);
  });

  test("test_that_nothing_changed_the_search_is_not_said_once_burro_has_changed_it", () => {
    // Seen in a browser, when a thing was chosen: directly under the new ranking the page
    // still read "Nothing you typed has changed your search."
    expect(beside.notice_text).toMatch(/ Nothing you typed has changed your search\.$/);

    const shown = noticeOf(read(beside, 2));

    expect(shown).not.toMatch(/Nothing you typed/);
    // What the notice is there to say is said, whole and word for word: what Burro ranks by.
    expect(beside.notice_text.startsWith(shown)).toBe(true);
    expect(shown).toMatch(/^Burro ranks places by what is there\./);
    expect(shown).toMatch(/you cannot ask for fewer of any group of people\.$/);
    expect(beside.notice_text.slice(shown.length)).toBe(" Nothing you typed has changed your search.");
  });

  test("test_nothing_is_taken_from_a_notice_of_words_that_changed_the_search_themselves", () => {
    // Its last sentence says that the rest was applied, which is so.
    expect(applied.notice_text).toMatch(/The rest of your search has been applied\.$/);
    expect(noticeOf(read(applied, 3))).toBe(applied.notice_text);
  });

  test("test_a_notice_of_one_sentence_is_never_cut_to_nothing", () => {
    const one = { notice: beside.notice, notice_text: "Burro ranks places by what is there.", changed: false, took: 1 };

    expect(noticeOf(one)).toBe(one.notice_text);
    expect(noticeOf({ ...one, notice: "none", notice_text: "" })).toBe("");
  });
});

describe("what Burro noticed and left out of the search", () => {
  test("test_each_thing_is_named_as_the_service_names_it_with_why_it_was_left", () => {
    const things = leftOutOf({
      left: [
        left("crime", { ...least, label: "Gritty" }),
        left("residents", { ...least, label: "Young professionals" }),
        left("two_ways", { ...least, label: "Pubs and bars" }),
        left("place"),
      ],
    });

    expect(things.map((thing) => [thing.name, thing.why, thing.says])).toEqual([
      ["Gritty", "crime", ""],
      ["Young professionals", "residents", ""],
      ["Pubs and bars", "two_ways", ""],
      [least.label, "place", ""],
    ]);
    expect(new Set(things.map((thing) => thing.key)).size).toBe(4);
  });

  test("test_a_thing_the_service_gave_no_way_to_take_carries_the_services_own_words", () => {
    expect(leftOutOf({ left: [left("no_way")] }).map((thing) => thing.says)).toEqual([`${least.does} ${least.follows}`]);
    // Where the service says nothing after it, nothing is put after it.
    expect(leftOutOf({ left: [left("no_way", { ...least, follows: "" })] }).map((thing) => thing.says)).toEqual([least.does]);
  });

  test("test_what_the_service_says_a_person_should_know_of_a_thing_it_gave_no_way_to_take_is_said_with_it", () => {
    // On a visit, "a 2 bed flat, up to so much": the service gives no way to take either,
    // and says why in what it has a person know before they choose.
    const [flat, budget] = aHome;
    if (!flat || !budget) throw new Error("the recording holds too little");
    expect([flat.follows, budget.follows]).toEqual(["", ""]);

    const things = leftOutOf({ left: [left("no_way", flat), left("no_way", budget)] });

    expect(things.map((thing) => thing.says)).toEqual([`${flat.does} ${flat.note}`, `${budget.does} ${budget.note}`]);
    expect(things[0]?.says).toMatch(/no number of bedrooms and no kind of home/);
    expect(things[1]?.says).toMatch(/has no budget/);
  });

  test("test_a_name_the_service_gives_that_holds_a_figure_is_not_said_and_the_page_names_the_thing_itself", () => {
    // The name the service gives a budget holds the amount that was typed, and the name of
    // a journey may hold its minutes. What was typed is drawn in the box and nowhere else.
    const [flat, budget] = aHome;
    if (!flat || !budget) throw new Error("the recording holds too little");
    expect(budget.label).toMatch(/\d/);

    const things = leftOutOf({ left: [left("no_way", flat), left("no_way", budget)] });

    expect(things.map((thing) => thing.name)).toEqual([flat.label, LEFT_OUT.named_by_the_page.budget]);
    expect(things.map((thing) => thing.name).join(" ")).not.toMatch(/\d/);
    expect(leftOutOf({ left: [left("place", { ...least, label: "A journey of 40 minutes" })] })[0]?.name).toBe(
      LEFT_OUT.named_by_the_page.commute,
    );
    // Two things that the page names alike are two things still.
    expect(new Set(things.map((thing) => thing.key)).size).toBe(2);
  });

  test("test_a_rule_for_an_area_is_named_as_what_to_do_with_the_area_and_never_by_the_name_of_the_area_alone", () => {
    // After "Left out of your search", the name of an area alone read as though the area
    // had been left out of the results. Every area is ranked: what was left out is the rule.
    const area = { target: "area", label: "Pellam Cross", does: "Pellam Cross: do you want Burro to look only there, or to leave it out?", follows: "" };
    const [thing] = leftOutOf({ left: [left("area", area)] });

    expect(thing).toEqual({ key: "area Pellam Cross", name: LEFT_OUT.ofAnArea("Pellam Cross"), why: "area", says: "" });
    expect(thing?.name).toBe("What to do with Pellam Cross");
    // Two areas that were named are two things, and one that was named twice is one.
    const other = { ...area, label: "Foxholt" };
    expect(leftOutOf({ left: [left("area", area), left("area", other), left("area", area)] }).map((one) => one.name)).toEqual([
      "What to do with Pellam Cross",
      "What to do with Foxholt",
    ]);
  });

  test("test_a_journey_that_waits_for_the_person_is_named_as_a_journey_to_its_place_and_never_by_the_place_alone", () => {
    // "Visiting my mother in a place": after "Left out of your search", the name of the
    // place alone read as though the place had been left out. What was left out is the journey.
    const journey = { target: "commute", label: "Cindermoor Works", does: "Add a journey to Cindermoor Works, by public transport.", follows: "" };
    const [thing] = leftOutOf({ left: [left("journey", journey)] });

    expect(thing).toEqual({ key: "journey Cindermoor Works", name: LEFT_OUT.ofAJourney("Cindermoor Works"), why: "journey", says: "" });
    expect(thing?.name).toBe("A journey to Cindermoor Works");
    // A name that holds a figure is not said: what was typed is drawn in the box alone.
    const [timed] = leftOutOf({ left: [left("journey", { ...journey, label: "Cindermoor Works in 30 minutes" })] });
    expect(timed?.name).toBe(LEFT_OUT.named_by_the_page.commute);
    // Two places are two journeys, and one that was named twice is one.
    const other = { ...journey, label: "Pellam Exchange" };
    expect(leftOutOf({ left: [left("journey", journey), left("journey", other), left("journey", journey)] }).map((one) => one.name)).toEqual([
      "A journey to Cindermoor Works",
      "A journey to Pellam Exchange",
    ]);
  });

  test("test_each_thing_is_named_once_and_nothing_is_said_of_nothing", () => {
    expect(leftOutOf({ left: [left("no_way"), left("no_way")] })).toHaveLength(1);
    expect(leftOutOf({ left: [left("crime", { ...least, label: "Gritty" }), left("crime", { ...least, label: "Gritty" })] })).toHaveLength(1);
    expect(leftOutOf({ left: [left("no_way", { label: "", does: "", follows: "" })] })).toEqual([]);
    expect(leftOutOf({ left: [left("no_way", { label: "A journey", does: "", follows: "" })] })).toEqual([]);
    expect(leftOutOf({ left: [] })).toEqual([]);
    expect(leftOutOf(null)).toEqual([]);
  });

  test("test_nothing_that_was_typed_is_in_what_is_named", () => {
    // What is named is the name the service gives the thing, and its own account of it.
    const [thing] = leftOutOf({ left: [left("no_way")] });

    expect(Object.keys(thing ?? {}).sort()).toEqual(["key", "name", "says", "why"]);
  });
});

describe("what a sentence asked for and Burro refused for its place or its number", () => {
  const PLACES: Readonly<Record<string, string>> = { "place:syn-p0021": "Cindermoor Works", "feature:air_no2": "Cleaner air" };
  const nameOf = (key: string) => PLACES[key] ?? null;
  const refused = (key: Refusal["key"], reason: Refusal["reason"]): Refusal => ({ key, reason });

  test("test_a_place_burro_does_not_know_and_a_number_it_cannot_take_are_named_among_what_was_left_out", () => {
    // Seen in a browser, under what Burro understood: "That number is outside what Burro
    // accepts.", of "within 2 minutes" of a place, and "Burro does not know that place.".
    // Neither said what it was about, what became of it or where to go on.
    const { named, rest } = refusedOf(
      [refused("place:", "unknown_place"), refused("place:syn-p0099", "out_of_range"), refused("budget", "out_of_range")],
      nameOf,
    );

    expect(named.map((thing) => [thing.name, thing.why])).toEqual([
      [LEFT_OUT.named_by_the_page.commute, "place"],
      [LEFT_OUT.named_by_the_page.commute, "range"],
      [LEFT_OUT.named_by_the_page.budget, "range"],
    ]);
    expect(rest).toEqual([]);
    // Each is told from every other of the line, though two bear one name.
    expect(new Set(named.map((thing) => thing.key)).size).toBe(3);
    // Nothing of them is the service's to say, and nothing that was typed is in them.
    expect(named.map((thing) => thing.says)).toEqual(["", "", ""]);
  });

  test("test_a_journey_whose_place_has_a_name_is_named_as_the_journey_there_and_a_thing_by_its_name", () => {
    const { named } = refusedOf([refused("place:syn-p0021", "out_of_range"), refused("feature:air_no2", "out_of_range")], nameOf);

    expect(named.map((thing) => thing.name)).toEqual([LEFT_OUT.ofAJourney("Cindermoor Works"), "Cleaner air"]);
  });

  test("test_every_other_refusal_and_one_that_has_no_name_is_said_where_it_was", () => {
    const others = [
      refused("budget", "nothing_to_change"),
      refused("feature:crime_burglary_theft", "crime_needs_explicit_request"),
      refused("place:syn-p0021", "too_many_commutes"),
      // It names no part, and the page has no name for it: said among what was left out, it would be said of nothing.
      refused(null, "out_of_range"),
      refused("feature:no_such_thing", "out_of_range"),
    ];

    expect(refusedOf(others, nameOf)).toEqual({ named: [], rest: others });
    expect(refusedOf([], nameOf)).toEqual({ named: [], rest: [] });
  });
});
