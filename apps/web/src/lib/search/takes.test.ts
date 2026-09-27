import { readdirSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { InterpretData, Suggestion } from "@/lib/api/schema";

import { NO_EDITS } from "./edits";
import { SKIP, addedWithOthers, guessOf, namedByThePerson, waitsForAPerson, waysOf } from "./suggestion";
import {
  countsCrime,
  countsResidents,
  DOUBTS,
  OF_A_WORD_READ_SEVERAL_WAYS,
  ONLY_BY_CHOICE,
  READINGS,
  readSeveralWays,
  settledOf,
  takenOf,
  takenOfAll,
  thingOf,
  TURNED,
  WHAT_THE_WORDS_TURN_AWAY,
  WHERE_BURRO_CANNOT_TELL,
  type Readings,
  type Taken,
} from "./takes";

const meta = recordedAnswer("get_meta", "meta").body.data;
const [pubs, noise] = recordedAnswer("interpret", "interpret-suggest").body.data.suggestions;
const long = recordedAnswer("interpret", "interpret-by-model-long").body.data.suggestions;
const atOnce = recordedAnswer("interpret", "interpret-rules-at-once").body.data.suggestions;
const [unknown] = recordedAnswer("interpret", "interpret-by-model-place").body.data.suggestions;
const [least] = recordedAnswer("interpret", "interpret-by-model-least").body.data.suggestions;
const counted = recordedAnswer("interpret", "interpret-suggest-who-is-counted").body.data.suggestions;
const house = recordedAnswer("interpret", "interpret-suggest-house").body.data.suggestions;
const asked = recordedAnswer("interpret", "interpret-clarify").body.data;
const notFound = recordedAnswer("interpret", "interpret-clarify-no-options").body.data;
const visitSaid = recordedAnswer("interpret", "visiting/interpret-said").body.data.suggestions;
const aNight = recordedAnswer("interpret", "visiting/interpret-night").body.data.suggestions;
const [mother] = recordedAnswer("interpret", "visiting/interpret-mother").body.data.suggestions;
const aHome = recordedAnswer("interpret", "visiting/interpret-home").body.data.suggestions;

const named = (offers: readonly Suggestion[], label: string): Suggestion => {
  const found = offers.find((one) => one.label === label);
  if (found === undefined) throw new Error(`no offer is named ${label}`);
  return found;
};
const of = (offers: readonly Suggestion[], target: string): Suggestion => {
  const found = offers.find((one) => one.target === target);
  if (found === undefined) throw new Error(`no offer is of ${target}`);
  return found;
};
if (!pubs || !noise || !unknown || !least) throw new Error("a recording holds too little");

/**
 * A rule for an area, as the service offers one where a sentence that is no plain list
 * names an area: to look only there, or to leave it out, with no guess and no way that one
 * press may add. No answer that was recorded holds one, so this is what the service gave
 * on 2026-09-26 to "visiting my mother in" and the name of an area, edit for edit, laid on
 * an offer that was recorded. `leftOut` is what it gave to "not", the name, "honestly":
 * the one way of the two.
 */
const ofAnArea = (rule: "only" | "exclude", area_id = "syn-n0018") => ({
  ...NO_EDITS,
  area_ops: [{ action: rule, area_id, provenance: "ui_edit" as const }],
});
const lookOnly = { id: "more", direction: "more", label: "Look only in Pellam Cross", guess: false, operations: ofAnArea("only") } as const;
const leaveOut = { id: "less", direction: "less", label: "Leave it out of the results", guess: false, operations: ofAnArea("exclude") } as const;
const skip = pubs?.choices.find((way) => way.id === SKIP);
if (!pubs || !skip) throw new Error("a recording holds too little");
const anArea: Suggestion = {
  ...pubs,
  target: "area",
  label: "Pellam Cross",
  does: "Pellam Cross: do you want Burro to look only there, or to leave it out?",
  follows: "",
  note: "",
  add_all: "",
  choices: [lookOnly, leaveOut, skip],
};
const leftOut: Suggestion = { ...anArea, does: "Leave Pellam Cross out of the results.", choices: [leaveOut, skip] };

/**
 * What an offer says of itself, laid on one that was recorded: whether the person's own
 * words name what it counts, and whether it waits for a person to choose it.
 */
const saying = (offer: Suggestion, says: { by_name?: boolean; only_by_choice?: boolean }): Suggestion => ({
  ...offer,
  ...says,
});
/** The same offer with one of its ways marked as the guess of the service, by the id of the way. */
const guessing = (offer: Suggestion, id: string): Suggestion => ({
  ...offer,
  choices: offer.choices.map((way) => ({ ...way, guess: way.id === id })),
});
/**
 * The same offer with nothing said of it: no way marked as the guess, none named for one
 * press, no word that names it, and nothing that waits. It is what the page makes of a
 * thing by itself, where the service leaves everything to it.
 */
const bare = (offer: Suggestion): Suggestion => ({
  ...guessing(offer, ""),
  add_all: "",
  by_name: false,
  only_by_choice: false,
});

const take = (suggestion: Suggestion, doubt = WHERE_BURRO_CANNOT_TELL) => takenOf(suggestion, meta, doubt);
/** The way that was taken, by its id, or why none was. */
const taken = (made: Taken) => (made.way === null ? `left: ${made.why}` : made.way.id);
const marksOf = (made: Taken) => (made.way === null ? null : made.marks.map((mark) => `${mark.key} ${mark.code}`));

/** Every offer of every answer that was recorded, with the name of its recording. */
const EVERY_OFFER = readdirSync(recordedFolder(), { recursive: true, encoding: "utf8" })
  .filter((file) => file.endsWith(".json"))
  .flatMap((file) => {
    const recorded = readRecorded(file.replace(/\.json$/, "").split(path.sep).join("/"));
    const data = (recorded.body as { data?: Partial<InterpretData> } | null)?.data;
    return (data?.suggestions ?? []).map((offer) => ({ file, offer }));
  });

describe("what Burro takes of what it noticed", () => {
  test("test_an_offer_that_needs_no_choice_is_taken_as_one_press_took_it", () => {
    const quiet = named(long, "Quiet streets");
    const budget = of(long, "budget");
    const renting = of(atOnce, "tenure");

    for (const offer of [quiet, budget, renting]) {
      const made = take(offer);
      expect(taken(made)).toBe(addedWithOthers(offer)?.id);
      // The edits are the service's own, and nothing of them is changed.
      expect(made.way === null ? null : made.operations).toBe(addedWithOthers(offer)?.operations);
      // It is what the person said, so nothing of it is said to be assumed.
      expect(marksOf(made)).toEqual([]);
    }
    // "Max" makes a budget a firm limit, and it is taken as it was worded.
    expect(taken(take(budget))).toBe("firm");
  });

  test("test_a_journey_is_taken_as_a_guide_though_the_words_give_a_firm_limit_and_the_guide_is_said_to_be_assumed", () => {
    // A journey is estimated from distance, so no area is left out on one without a press.
    const journey = of(long, "commute");
    const made = take(journey);

    expect(guessOf(journey)?.id).toBe("firm");
    expect(taken(made)).toBe("guide");
    expect(made.way === null ? [] : made.operations.commute_ops.map((edit) => edit.strictness)).toEqual(["soft"]);
    // The person wrote "at most". That the limit is flexible is Burro's, and the chip says so.
    expect(marksOf(made)).toEqual(["place:syn-p0017 strictness"]);
  });

  test("test_an_offer_that_needs_a_choice_is_taken_as_burros_guess_where_the_service_marks_one", () => {
    // The park as a model read it, with no way that one press may add, read into words that do not name it.
    const park = { ...named(long, "Nearer a park"), add_all: "", by_name: false };
    const made = take(park);

    expect(guessOf(park)?.id).toBe("more");
    expect(taken(made)).toBe("more");
    expect(marksOf(made)).toEqual(["feature:park_proximity weight"]);
    // Where the words name it, the way they give is what the person said, and nothing is assumed.
    expect(marksOf(take({ ...park, by_name: true }))).toEqual([]);
    // The guess is taken whichever way it points.
    const turned = { ...park, choices: park.choices.map((way) => ({ ...way, guess: way.id === "tag:parks_close_by/more" })) };
    expect(taken(take(turned))).toBe("tag:parks_close_by/more");
    expect(marksOf(take(turned))).toEqual(["tag:parks_close_by weight"]);
  });

  test("test_where_the_service_marks_no_guess_a_thing_that_runs_one_way_counts_for_more_of_what_its_name_says", () => {
    // A nuisance runs one way, which is less of it: that is what its name says.
    expect(noise.label).toBe("Less transport noise");
    expect(waysOf(noise).map((way) => way.id)).toEqual(["less"]);
    expect(taken(take(bare(noise)))).toBe("less");
    expect(marksOf(take(bare(noise)))).toEqual(["feature:noise_exposure weight"]);
    // A thing that counts already may be counted or no longer counted. To stop counting it
    // is no way of taking it, so it runs one way, and is taken that way.
    const station = named(counted, "Nearer a station");
    expect(waysOf(station).map((way) => way.id)).toEqual(["more", "off"]);
    expect(taken(take(bare(station)))).toBe("more");
    expect(marksOf(take(bare(station)))).toEqual(["feature:station_walk weight"]);
    // As the service gives it, "near a station" names it and gives the way: nothing is assumed.
    expect(taken(take(station))).toBe("more");
    expect(marksOf(take(station))).toEqual([]);
  });

  test("test_a_wish_the_words_do_not_say_is_the_persons_own_waits_for_them_and_is_left", () => {
    // "Pubs are so noisy" names a nuisance, and does not say that the person wants less of
    // it for themselves: it is said of the pubs. The service says that it waits.
    expect([namedByThePerson(noise), waitsForAPerson(noise), guessOf(noise)]).toEqual([true, true, null]);
    expect(take(noise)).toEqual({ way: null, why: "by_choice" });
  });

  test("test_where_the_words_give_neither_way_of_a_thing_that_runs_two_ways_burro_takes_neither", () => {
    // "Pubs are so noisy" says neither more pubs nor fewer. More was taken of it, and areas
    // with more pubs came first for a person who may have wanted fewer.
    expect(waysOf(pubs).map((way) => [way.id, way.guess])).toEqual([["more", false], ["less", false]]);
    expect(addedWithOthers(pubs)).toBeNull();
    expect(take(pubs)).toEqual({ way: null, why: "two_ways" });
    // A scale is taken towards neither of its ends, where the service marks neither.
    const goingOut = named(counted, "Going out");
    expect(waysOf(goingOut).map((way) => way.id)).toEqual(["more", "less"]);
    expect(take(bare(goingOut))).toEqual({ way: null, why: "two_ways" });
    // "Lively" gives the way, and the service marks it: it is taken that way.
    expect([guessOf(goingOut)?.id, addedWithOthers(goingOut)?.id]).toEqual(["more", "more"]);
    expect(taken(take(goingOut))).toBe("more");
    // Of everything that was recorded, no thing that runs two ways is taken but by the
    // way that one press may add, or by the way the service marks as its guess.
    for (const { offer } of EVERY_OFFER) {
      const made = take(offer);
      const ways = waysOf(offer).filter((way) => way.operations.weight_ops.every((edit) => edit.action !== "remove") && way.operations.tag_ops.every((edit) => edit.action !== "remove"));
      const twoWays = ways.some((way) => way.direction === "more") && ways.some((way) => way.direction === "less");
      if (made.way === null || !twoWays) continue;
      expect([addedWithOthers(offer)?.id, guessOf(offer)?.id]).toContain(made.way.id);
    }
  });

  test("test_a_thing_that_runs_two_ways_is_taken_the_way_the_service_marks_as_its_guess_whichever_that_is", () => {
    const fewer = guessing(pubs, "less");

    expect(taken(take(fewer))).toBe("less");
    // The words name pubs, and the way is the one they give: it is what the person said.
    expect(namedByThePerson(fewer)).toBe(true);
    expect(marksOf(take(fewer))).toEqual([]);
    // Read into words that do not name it, which way was taken is said on the chip, with the thing itself.
    expect(marksOf(take(saying(fewer, { by_name: false })))).toEqual([
      "feature:venue_evening_per_homes weight",
      "feature:venue_evening_per_homes direction",
    ]);
  });

  test("test_to_skip_a_thing_is_never_taken_and_to_stop_counting_it_is_no_way_of_taking_it_that_the_page_chooses", () => {
    const station = named(counted, "Nearer a station");

    expect(station.choices.map((way) => way.id)).toEqual(["more", "off", SKIP]);
    expect(taken(take(station))).toBe("more");
    // Though it is the first way the service gives, where it marks none and names none.
    const first = { ...bare(station), choices: [...bare(station).choices].reverse() };
    expect(first.choices.map((way) => way.id)).toEqual([SKIP, "off", "more"]);
    expect(taken(take(first))).toBe("more");
    // Of everything that was recorded, no thing is skipped, and none is counted no longer
    // but where the service marks that as the way the words give.
    for (const { offer } of EVERY_OFFER) {
      const made = take(offer);
      expect(taken(made)).not.toBe(SKIP);
      if (made.way?.id === "off") expect([offer.label, made.way.guess]).toEqual([offer.label, true]);
    }
  });

  test("test_what_counts_recorded_crime_is_left_unless_the_service_says_the_persons_own_words_name_it", () => {
    // Recorded crime counts only where a person asks for it by name. A word that a vibe
    // which counts it was offered for is no such asking: "posh" names nothing.
    const gritty = named(atOnce, "Gritty");

    expect(waysOf(gritty).every((way) => countsCrime(way.operations, meta))).toBe(true);
    // A service that says nothing of whether the words name it has not said that they do.
    expect(namedByThePerson(gritty)).toBe(false);
    expect(take(gritty)).toEqual({ way: null, why: "crime" });
    expect(take(saying(gritty, { by_name: false }))).toEqual({ way: null, why: "crime" });
    // Though a model, or a service that came after this one, marks it as the guess.
    const guessed = { ...gritty, choices: gritty.choices.map((way) => ({ ...way, guess: way.id !== SKIP })) };
    expect(take(guessed)).toEqual({ way: null, why: "crime" });
    const said = { ...gritty, add_all: waysOf(gritty)[0]?.id ?? "" };
    expect(take(said)).toEqual({ way: null, why: "crime" });
    // Of everything that was recorded, nothing that is taken sets recorded crime counting
    // but what the service says the person named, and says does not wait for them.
    const crimes = EVERY_OFFER.filter(({ offer }) => {
      const made = take(offer);
      return made.way !== null && countsCrime(made.operations, meta);
    });
    expect(crimes.filter(({ offer }) => !namedByThePerson(offer) || waitsForAPerson(offer))).toEqual([]);
    expect(countsCrime(NO_EDITS, meta)).toBe(false);
  });

  test("test_what_counts_recorded_crime_is_taken_where_the_service_says_the_persons_own_words_name_it", () => {
    // "Somewhere gritty, I think": to type "gritty" is to ask for what it counts by name.
    // The sentence is no plain list, so the service applies none of it, and offers the vibe.
    const gritty = saying(named(atOnce, "Gritty"), { by_name: true, only_by_choice: false });
    const [oneWay] = waysOf(gritty);
    if (!oneWay) throw new Error("the recording holds no way of it");

    const made = take(gritty);
    expect(taken(made)).toBe(oneWay.id);
    expect(made.way === null ? null : made.operations).toBe(oneWay.operations);
    expect(made.way !== null && countsCrime(made.operations, meta)).toBe(true);
    // Nobody said how much it counts, so the chip says that it was assumed.
    expect(marksOf(made)).toEqual(["tag:street_character weight"]);
    // A measure of recorded crime that was named, as "low crime" names two of them.
    const burglary = meta.features.find((one) => one.dimension === "crime");
    if (!burglary) throw new Error("the release holds no measure of recorded crime");
    const less = {
      ...NO_EDITS,
      weight_ops: [{ action: "nudge", feature_id: burglary.feature_id, value: 0, step: "up_large", direction: "default", provenance: "ui_edit" }],
    } as typeof NO_EDITS;
    const measure: Suggestion = saying(
      { ...noise, target: `feature:${burglary.feature_id}`, label: burglary.short_label, choices: noise.choices.map((way) => (way.id === SKIP ? way : { ...way, operations: less })) },
      { by_name: true, only_by_choice: false },
    );
    expect(countsCrime(less, meta)).toBe(true);
    expect(taken(take(measure))).toBe("less");
    // The same measure, where the words name nothing: "safe" is read into it.
    expect(take(saying(measure, { by_name: false, only_by_choice: true }))).toEqual({ way: null, why: "crime" });
  });

  test("test_a_thing_that_was_named_is_taken_the_way_the_service_marks_and_by_neither_way_where_it_marks_none", () => {
    // Gritty runs from Polished to Gritty. Where the words name it and give no way, neither
    // is taken, and the line says that Burro could not tell which was meant: it does not say
    // that recorded crime must be asked for by name, since it was.
    const [one] = waysOf(named(atOnce, "Gritty"));
    if (!one) throw new Error("the recording holds no way of it");
    const other = { ...one, id: "more", direction: "more" as const, label: "Towards Gritty" };
    const skip = named(atOnce, "Gritty").choices.filter((way) => way.id === SKIP);
    const bothWays = saying({ ...named(atOnce, "Gritty"), choices: [other, one, ...skip] }, { by_name: true, only_by_choice: false });

    expect(waysOf(bothWays).map((way) => way.direction)).toEqual(["more", "less"]);
    expect(take(bothWays)).toEqual({ way: null, why: "two_ways" });
    expect(taken(take(guessing(bothWays, "more")))).toBe("more");
    expect(taken(take(guessing(bothWays, one.id)))).toBe(one.id);
    // Where the words do not name it, it says that of itself whichever way is marked.
    expect(take(saying(bothWays, { by_name: false, only_by_choice: true }))).toEqual({ way: null, why: "crime" });
    expect(take(saying(guessing(bothWays, "more"), { by_name: false, only_by_choice: true }))).toEqual({ way: null, why: "crime" });
  });

  test("test_what_the_service_says_waits_for_a_person_is_never_taken_whatever_it_says_of_its_ways", () => {
    // A measure that a decision holds to be offered and never applied: the service marks
    // it, and the page names no measure. "Posh" is read into the share of homes in the
    // higher council tax bands, which follows what households have.
    const waits = named(atOnce, "Homes in the higher council tax bands");
    const bands = saying(waits, { only_by_choice: false });

    expect(waitsForAPerson(bands)).toBe(false);
    expect(waitsForAPerson(waits)).toBe(true);
    expect(taken(take(bands))).toBe("more");
    expect(take(waits)).toEqual({ way: null, why: "by_choice" });
    // Though the service marks a way of it as its guess, or names one for one press.
    expect(take(guessing(waits, "more"))).toEqual({ way: null, why: "by_choice" });
    expect(take({ ...waits, add_all: "more" })).toEqual({ way: null, why: "by_choice" });
    // And though it says that the words name it: what waits, waits.
    expect(take(saying(waits, { by_name: true }))).toEqual({ way: null, why: "by_choice" });
    // What waits because it counts recorded crime, or who lived somewhere, says that of itself.
    expect(take(saying(named(atOnce, "Gritty"), { only_by_choice: true }))).toEqual({ way: null, why: "crime" });
    expect(take(saying(named(counted, "Young professionals"), { only_by_choice: true }))).toEqual({ way: null, why: "residents" });
    // A journey that waits says that it is one: it counts no measure, and is named by its place.
    if (!mother) throw new Error("the recording holds no offer");
    expect(take(saying(mother, { only_by_choice: true }))).toEqual({ way: null, why: "journey" });
    // A rule for an area that waits says what is said of every rule for an area that was left.
    expect(take(saying(anArea, { only_by_choice: true }))).toEqual({ way: null, why: "area" });
    expect(take(saying(guessing(anArea, "more"), { only_by_choice: true }))).toEqual({ way: null, why: "area" });
    // Each of the four is a thing that a person alone may add.
    expect(ONLY_BY_CHOICE).toEqual(["crime", "residents", "by_choice", "journey"]);
  });

  test("test_what_counts_who_lived_somewhere_is_never_taken_and_is_said_to_be_left", () => {
    // Of who lives somewhere Burro counts two things, and only where a person chooses them.
    // A word that such a vibe was offered for is no such choice, though the vibe runs one way.
    const young = named(counted, "Young professionals");

    expect(waysOf(young).map((way) => way.id)).toEqual(["more"]);
    expect(waysOf(young).every((way) => countsResidents(way.operations, meta))).toBe(true);
    expect(take(young)).toEqual({ way: null, why: "residents" });
    // Though a service that came after this one marks it as the guess, or has one press add it.
    const guessed = { ...young, add_all: "more", choices: young.choices.map((way) => ({ ...way, guess: way.id === "more" })) };
    expect(take(guessed)).toEqual({ way: null, why: "residents" });
    // And though it says that the person's own words name it, and that it does not wait:
    // no word applies it, its own name among them.
    expect(take(saying(guessed, { by_name: true, only_by_choice: false }))).toEqual({ way: null, why: "residents" });
    // What stands beside it in the same sentence is taken as it would be without it.
    expect(counted.map((offer) => [offer.label, taken(take(offer))])).toEqual([
      ["Young professionals", "left: residents"],
      ["Going out", "more"],
      ["Nearer a station", "more"],
    ]);
    // Of everything that was recorded, nothing that is taken counts who lived somewhere.
    const residents = EVERY_OFFER.map(({ offer }) => take(offer)).filter(
      (made) => made.way !== null && countsResidents(made.operations, meta),
    );
    expect(residents).toEqual([]);
    expect(countsResidents(NO_EDITS, meta)).toBe(false);
  });

  test("test_which_vibe_and_which_measure_is_left_is_read_from_what_the_service_says_of_each_and_never_written_down", () => {
    // Route 11 says of every measure what it is a fact about, and what it is filed under,
    // and of every vibe what its recipe holds. A release that says otherwise is believed.
    const nudge = (tag_id: string) => ({
      ...NO_EDITS,
      tag_ops: [{ action: "nudge", tag_id, value: 0, step: "up_large", toward: "high", provenance: "ui_edit" }],
    }) as typeof NO_EDITS;
    const vibes = (counts: (edits: typeof NO_EDITS, form: typeof meta) => boolean, form = meta) =>
      form.tags.filter((tag) => counts(nudge(tag.tag_id), form)).map((tag) => tag.tag_id);

    expect(vibes(countsCrime)).toEqual(["street_character"]);
    expect(vibes(countsResidents)).toEqual(["family_area", "young_professionals"]);
    // The same vibes, in a release whose measures are all facts about the place, count neither.
    const ofThePlace = {
      ...meta,
      features: meta.features.map((one) => ({ ...one, describes: "place" as const, dimension: "homes" as const })),
    };
    expect(vibes(countsCrime, ofThePlace)).toEqual([]);
    expect(vibes(countsResidents, ofThePlace)).toEqual([]);
    // A measure is left by itself as it is inside a vibe.
    const weigh = (feature_id: string) => ({
      ...NO_EDITS,
      weight_ops: [{ action: "nudge", feature_id, value: 0, step: "up_large", direction: "default", provenance: "ui_edit" }],
    }) as typeof NO_EDITS;
    const measures = (counts: (edits: typeof NO_EDITS, form: typeof meta) => boolean) =>
      meta.features.filter((one) => counts(weigh(one.feature_id), meta)).map((one) => one.feature_id);
    expect(measures(countsCrime)).toEqual(meta.features.filter((one) => one.dimension === "crime").map((one) => one.feature_id));
    expect(measures(countsResidents)).toEqual(
      meta.features.filter((one) => one.describes === "residents").map((one) => one.feature_id),
    );
    expect(measures(countsCrime).length).toBeGreaterThan(0);
    expect(measures(countsResidents).length).toBeGreaterThan(0);
    // To take a thing off is not to count it.
    const off = { ...NO_EDITS, tag_ops: nudge("street_character").tag_ops.map((edit) => ({ ...edit, action: "remove" as const })) };
    expect(countsCrime(off, meta)).toBe(false);
  });

  test("test_a_journey_to_a_place_burro_does_not_know_is_left_where_the_data_holds_none_with_a_name_like_it", () => {
    expect(unknown.asks_place).toBe(true);
    expect(unknown.options).toEqual([]);
    expect(take(unknown)).toEqual({ way: null, why: "place" });
  });

  test("test_a_name_that_several_places_bear_is_taken_as_the_first_the_service_gives_as_a_guide_and_says_so", () => {
    const [first, second] = asked.clarify[0]?.options ?? [];
    if (!first || !second) throw new Error("the recording holds too few places");
    const made = take({ ...unknown, options: [first, second] });

    // The words give a firm limit. Two guesses are not laid one on the other: it is a guide.
    expect(guessOf(unknown)?.id).toBe("firm");
    expect(taken(made)).toBe("guide");
    expect(made.way === null ? [] : made.operations.commute_ops).toMatchObject([
      { action: "add", place_id: first.id, max_minutes: 40, strictness: "soft" },
    ]);
    expect(marksOf(made)).toEqual([`place:${first.id} place`, `place:${first.id} strictness`]);
    // The edits the service gave are as they were: the place is put into a copy of them.
    expect(waysOf(unknown).flatMap((way) => way.operations.commute_ops.map((edit) => edit.place_id))).toEqual(["", ""]);
  });

  test("test_an_offer_with_no_way_to_take_it_is_left_and_the_services_words_say_why", () => {
    expect(waysOf(least)).toEqual([]);
    expect(take(least)).toEqual({ way: null, why: "no_way" });
    expect(least.does).not.toBe("");
  });

  test("test_a_budget_for_a_house_of_no_kind_is_taken_with_the_kind_burro_takes", () => {
    const budget = of(house, "budget");
    const made = take(budget);

    expect(taken(made)).toBe("terraced");
    expect(made.way === null ? [] : made.operations.budget_ops.map((edit) => [edit.segment, edit.provenance])).toEqual([
      ["terraced", "inferred"],
      ["unchanged", "ui_edit"],
    ]);
  });

  test("test_whatever_is_taken_is_a_way_the_service_gave_with_the_edits_it_gave", () => {
    expect(EVERY_OFFER.length).toBeGreaterThan(60);
    for (const { offer } of EVERY_OFFER) {
      const made = take(offer);
      if (made.way === null) continue;
      expect(offer.choices).toContain(made.way);
      // Nothing of an edit is changed but the place of a journey that held none.
      const given = JSON.stringify(made.way.operations).replaceAll('"place_id":""', '"place_id":"?"');
      const sent = JSON.stringify(made.operations).replaceAll(/"place_id":"[^"]+"/g, (held) =>
        given.includes(held) ? held : '"place_id":"?"',
      );
      expect(sent).toBe(given);
      expect(made.operations.commute_ops.every((edit) => edit.place_id !== "")).toBe(true);
      // A rule for an area is taken on the guess of the service alone: no area is hidden,
      // and none is the only one, because a way of it stood first or could be added at a press.
      const rules = made.operations.area_ops.some((edit) => edit.action !== "clear");
      if (rules) expect([offer.label, made.way.guess]).toEqual([offer.label, true]);
    }
  });

  test("test_a_rule_for_an_area_is_never_the_gentler_way_and_neither_of_its_ways_is_taken_where_the_service_marks_no_guess", () => {
    // "Visiting my mother in" an area: the service offers to look only there, or to leave
    // it out, and guesses at neither. The first way was taken: one area was ranked, and
    // every other was left out on a guess.
    expect(waysOf(anArea).map((way) => [way.id, way.guess])).toEqual([["more", false], ["less", false]]);
    expect(take(anArea)).toEqual({ way: null, why: "area" });
    // Whichever of the two the service gives first, and though it gives one alone.
    expect(take({ ...anArea, choices: [leaveOut, lookOnly, skip] })).toEqual({ way: null, why: "area" });
    expect(take(leftOut)).toEqual({ way: null, why: "area" });
    expect(take({ ...anArea, choices: [lookOnly, skip] })).toEqual({ way: null, why: "area" });
    // And whichever way the line of the look has a thing that runs two ways taken.
    for (const doubt of DOUBTS) expect(take(anArea, doubt)).toEqual({ way: null, why: "area" });
  });

  test("test_such_an_offer_is_told_by_the_edits_the_service_gives_with_its_ways_and_by_no_name", () => {
    // Under another name, and as a thing of another kind: the edits are what leave areas out.
    const renamed = { ...anArea, target: "feature:something_new", label: "Something new" };
    expect(take(renamed)).toEqual({ way: null, why: "area" });
    // An offer that bears its name and its kind, and holds no rule for an area, is taken as any other is.
    const inNameOnly = { ...bare(noise), target: "area", label: "Pellam Cross" };
    expect(taken(take(inNameOnly))).toBe("less");
    // To show an area again leaves none out, and is no such rule.
    const shown = { ...lookOnly, label: "Show it again", operations: { ...NO_EDITS, area_ops: [{ action: "clear", area_id: "syn-n0018", provenance: "ui_edit" }] } } as const;
    expect(taken(take({ ...anArea, choices: [shown, skip] }))).toBe("more");
  });

  test("test_a_rule_for_an_area_is_taken_on_the_guess_of_the_service_alone_and_says_that_it_was_assumed", () => {
    // The way the service marks as its guess is the way it reads the words. It is taken,
    // and nobody said in so many words that areas are to be left out: the chip says so.
    const guessed = { ...anArea, choices: [lookOnly, { ...leaveOut, guess: true }, skip] };
    const made = take(guessed);
    expect(taken(made)).toBe("less");
    expect(made.way === null ? null : made.operations).toBe(leaveOut.operations);
    expect(marksOf(made)).toEqual(["area:syn-n0018 rule"]);
    expect(taken(take(guessing(anArea, "more")))).toBe("more");
    expect(marksOf(take(guessing(anArea, "more")))).toEqual(["area:syn-n0018 rule"]);
    // That one press may add a way is no guess at it. The service names no rule for an area
    // so, and one that did would have areas left out on no guess at all.
    expect(take({ ...anArea, add_all: "more" })).toEqual({ way: null, why: "area" });
    expect(take({ ...anArea, add_all: "less" })).toEqual({ way: null, why: "area" });
    // Where it says both of one way, the way is taken, and says that it was assumed all the same.
    const both = { ...guessing(anArea, "more"), add_all: "more" };
    expect(taken(take(both))).toBe("more");
    expect(marksOf(take(both))).toEqual(["area:syn-n0018 rule"]);
    // To show an area again leaves none out: it is no such rule, and nothing of it is assumed.
    const shown = { ...lookOnly, label: "Show it again", operations: { ...NO_EDITS, area_ops: [{ action: "clear", area_id: "syn-n0018", provenance: "ui_edit" }] } } as const;
    expect(marksOf(take({ ...anArea, choices: [shown, skip] }))).toEqual([]);
  });

  test("test_no_limit_leaves_an_area_out_unless_the_service_says_one_press_may_set_it", () => {
    for (const { offer } of EVERY_OFFER) {
      const made = take(offer);
      if (made.way === null) continue;
      const firm = [...made.operations.budget_ops, ...made.operations.commute_ops].some(
        (edit) => edit.strictness === "hard",
      );
      if (firm) expect([offer.target, made.way.id]).toEqual(["budget", addedWithOthers(offer)?.id]);
    }
  });
});

describe("a search for somewhere to stay, in words that are no plain list", () => {
  test("test_a_visit_that_was_said_is_taken_as_one_press_took_it_and_nothing_of_it_is_assumed", () => {
    const visiting = of(visitSaid, "tenure");

    expect([visiting.label, visiting.add_all, guessOf(visiting)?.id]).toEqual(["Visiting", "more", "more"]);
    const made = take(visiting);
    expect(taken(made)).toBe("more");
    expect(made.way === null ? null : made.operations.budget_ops.map((edit) => edit.tenure)).toEqual(["visit"]);
    expect(marksOf(made)).toEqual([]);
  });

  test("test_a_visit_that_the_words_only_suggest_is_taken_and_says_that_it_was_assumed", () => {
    // "A hotel for so much a night": nobody said that they are visiting, and one press
    // took no such thing. Burro takes it, and the chip of the kind of search says so.
    const visiting = of(aNight, "tenure");

    expect([visiting.add_all, guessOf(visiting)]).toEqual(["", null]);
    expect(taken(take(visiting))).toBe("more");
    expect(marksOf(take(visiting))).toEqual(["tenure tenure"]);
  });

  test("test_a_journey_the_service_cannot_tell_is_needed_waits_for_the_person_and_is_left", () => {
    // "Visiting my mother in a place": the place may be the mother's to reach, and not the
    // person's. The service says that the journey waits, and it is left, as a journey.
    if (!mother) throw new Error("the recording holds no offer");
    const [journey] = waysOf(mother).flatMap((way) => way.operations.commute_ops);

    expect([mother.target, mother.add_all, guessOf(mother), mother.asks_place]).toEqual(["commute", "", null, false]);
    expect(waitsForAPerson(mother)).toBe(true);
    expect(take(mother)).toEqual({ way: null, why: "journey" });
    // A service that does not say so leaves it to the page, which adds it and says on the
    // chip of the place that it was assumed.
    const left = saying(mother, { only_by_choice: false });
    expect(taken(take(left))).toBe("more");
    expect(marksOf(take(left))).toEqual([`place:${journey?.place_id} place`]);
    // A journey that one press added is the person's own, and says nothing of the kind.
    expect(marksOf(take(of(aNight, "commute")))).toEqual([]);
  });

  test("test_a_home_and_a_budget_that_a_visit_cannot_hold_are_left_with_no_way_to_take_them", () => {
    expect(aHome.map((offer) => offer.target)).toEqual(["budget", "budget"]);
    expect(aHome.map((offer) => taken(take(offer)))).toEqual(["left: no_way", "left: no_way"]);
  });
});

describe("a thing that runs two ways, where the words give neither", () => {
  test("test_one_line_of_the_look_has_more_of_it_taken_and_nothing_else_is_changed_by_it", () => {
    expect(DOUBTS).toEqual(["more", "left"]);
    // Where the words give neither way, Burro takes neither.
    expect(WHERE_BURRO_CANNOT_TELL).toBe("left");

    // The other way it was built: more of what the name of the thing says, and the chip says so.
    expect(taken(take(pubs, "more"))).toBe("more");
    expect(marksOf(take(pubs, "more"))).toEqual([
      "feature:venue_evening_per_homes weight",
      "feature:venue_evening_per_homes direction",
    ]);
    // A scale is then taken towards its high end, which is the end its name is of.
    expect(taken(take(bare(named(counted, "Going out")), "more"))).toBe("more");
    expect(marksOf(take(bare(named(counted, "Going out")), "more"))).toEqual(["tag:pace weight"]);
    // What runs one way, what the service marks a guess of, and what one press may add are taken as they were.
    for (const offer of [noise, named(counted, "Nearer a station"), ...long]) {
      expect(take(offer, "left")).toEqual(take(offer, "more"));
    }
  });
});

describe("a thing the words turn away", () => {
  // "Honestly, no station": the words turn away a thing that counts a little in every
  // search, until a person says otherwise. It can rank an area higher and never lower, so
  // all that is offered of it is to stop counting it, and the service marks that as the
  // way the words give. Of "I never use the station" it marks nothing: it cannot read the turn.
  const station = named(counted, "Nearer a station");
  const stop = station.choices.find((way) => way.id === "off");
  const pass = station.choices.find((way) => way.id === SKIP);
  if (!stop || !pass) throw new Error("the recording holds too little");
  const notRead: Suggestion = { ...bare(station), by_name: true, does: "Stop counting this: nearer a station.", choices: [stop, pass] };
  const turnedAway = guessing(notRead, "off");

  test("test_one_line_of_the_look_chooses_and_it_is_counted_no_longer", () => {
    expect(TURNED).toEqual(["stopped", "left"]);
    expect(WHAT_THE_WORDS_TURN_AWAY).toBe("stopped");
  });

  test("test_where_the_service_marks_that_as_its_guess_the_thing_is_counted_no_longer_and_nothing_of_it_is_assumed", () => {
    const made = take(turnedAway);

    expect(taken(made)).toBe("off");
    // The edits are the service's own: the thing is taken off, and nothing is set in its place.
    expect(made.way === null ? null : made.operations).toBe(stop.operations);
    expect(made.way === null ? [] : made.operations.weight_ops.map((edit) => edit.action)).toEqual(["remove"]);
    // The words name the thing and give the way: it is what the person said.
    expect(marksOf(made)).toEqual([]);
    // Read into words that do not name it, that it was taken off is Burro's, and the chip says so.
    expect(marksOf(take(saying(turnedAway, { by_name: false })))).toEqual(["feature:station_walk weight"]);
  });

  test("test_where_the_service_marks_no_guess_nothing_is_taken_and_its_own_words_say_why", () => {
    expect(take(notRead)).toEqual({ way: null, why: "no_way" });
    // Though it stands beside a way that counts the thing, which is taken as it is.
    expect(taken(take(bare(station)))).toBe("more");
  });

  test("test_what_waits_for_a_person_is_not_stopped_for_them_either", () => {
    expect(take(saying(turnedAway, { only_by_choice: true }))).toEqual({ way: null, why: "by_choice" });
  });

  test("test_the_other_way_it_was_built_leaves_it_and_the_services_words_say_why", () => {
    expect(takenOf(turnedAway, meta, WHERE_BURRO_CANNOT_TELL, "left")).toEqual({ way: null, why: "no_way" });
    expect(takenOfAll([turnedAway], meta, WHERE_BURRO_CANNOT_TELL, OF_A_WORD_READ_SEVERAL_WAYS, [], "left")).toEqual([
      { way: null, why: "no_way" },
    ]);
    expect(takenOfAll([turnedAway], meta).map(taken)).toEqual(["off"]);
  });
});

describe("words that are read more ways than one", () => {
  // "Slightly affluent" is read as a mix of brands, as a vibe that counts recorded crime,
  // as what homes sell for and as homes in the higher council tax bands. "A real identity"
  // is read as three things more. The words name none of them: each is read into them.
  const readings = (offers: readonly Suggestion[]) => [...readSeveralWays(offers).keys()].map((at) => offers[at]?.label);
  const all = (offers: readonly Suggestion[], how: Readings, before: readonly string[] = []) =>
    takenOfAll(offers, meta, WHERE_BURRO_CANNOT_TELL, how, before).map((made, at) => [offers[at]?.label, taken(made)]);
  const [brands, gritty, prices, bands] = atOnce.filter((offer) => readSeveralWays(atOnce).has(atOnce.indexOf(offer)));
  if (!brands || !gritty || !prices || !bands) throw new Error("the recording holds too little");
  /** The four readings of one word as the service gives them since it says what an offer says of itself. */
  const posh = [
    saying(brands, { by_name: false, only_by_choice: false }),
    saying(gritty, { by_name: false, only_by_choice: true }),
    saying(prices, { by_name: false, only_by_choice: false }),
    saying(bands, { by_name: false, only_by_choice: true }),
  ];

  test("test_which_offers_are_readings_of_the_same_words_is_told_by_the_words_they_rest_on", () => {
    expect(readings(atOnce)).toEqual([
      "Mix of brands",
      "Gritty",
      "What homes sell for",
      "Homes in the higher council tax bands",
      "Village feel",
      "Age of buildings",
      "Nearer a town centre",
    ]);
    // A model reads the same sentence, and marks its guess of what was plainly said: what
    // is a reading of words that are read several ways is what it was.
    expect(readings(long)).toEqual(readings(atOnce));
    // The readings of one stretch of words are told from those of another.
    const words = readSeveralWays(atOnce);
    expect(new Set(words.values()).size).toBe(2);
    expect(words.get(atOnce.indexOf(brands))).toBe(words.get(atOnce.indexOf(bands)));
    expect(words.get(atOnce.indexOf(brands))).not.toBe(words.get(atOnce.indexOf(named(atOnce, "Village feel"))));
  });

  test("test_a_thing_that_is_the_one_reading_of_its_words_is_none_of_them", () => {
    // Pubs and the noise of transport rest on words of their own, each.
    expect(readings([pubs, noise])).toEqual([]);
    expect(readings(counted)).toEqual([]);
    expect(readings(house)).toEqual([]);
    expect(readings([])).toEqual([]);
  });

  test("test_only_a_wish_is_such_a_reading_and_what_is_said_of_a_home_in_the_same_words_is_none", () => {
    // A budget, a home and that a person rents may each rest on the very same words: they
    // are three things that were said, and no three readings of one.
    const budget = of(long, "budget");
    const home = { ...budget, label: "A home" };
    const tenure = { ...budget, target: "tenure", label: "Renting" };
    const journey = { ...of(long, "commute"), spans: budget.spans };
    expect(readings([budget, home, tenure, journey])).toEqual([]);
    expect(readings([anArea, { ...anArea, label: "Another" }])).toEqual([]);
  });

  test("test_what_the_persons_own_words_name_is_what_they_asked_for_and_no_reading_of_them", () => {
    // "Low crime" names two measures, and both are what was asked for.
    const named = [saying(brands, { by_name: true }), saying(prices, { by_name: true })];
    expect(readings(named)).toEqual([]);
    expect(all(named, "first")).toEqual([["Mix of brands", "more"], ["What homes sell for", "more"]]);
    // What is read into the same words beside a thing they name is a reading of them.
    const beside = [saying(brands, { by_name: true }), prices];
    expect(readings(beside)).toEqual(["What homes sell for"]);
  });

  test("test_a_reading_is_one_whatever_the_service_says_of_its_ways", () => {
    // Whether a way of it is marked as the guess, or may be added at one press, says which
    // way a thing is meant. It does not say that the words name the thing.
    const said = { ...brands, add_all: "more" };
    const guessed = guessing(prices, "more");

    expect(readings([said, guessed])).toEqual(["Mix of brands", "What homes sell for"]);
    expect(readings([said, prices, { ...prices, label: "Another reading" }])).toEqual([
      "Mix of brands",
      "What homes sell for",
      "Another reading",
    ]);
  });

  test("test_of_the_readings_of_the_same_words_the_first_that_may_be_taken_is_and_the_rest_are_left", () => {
    expect(all(posh, "first")).toEqual([
      ["Mix of brands", "more"],
      // What is never taken says that of itself, and not that the words were read otherwise.
      ["Gritty", "left: crime"],
      ["What homes sell for", "left: otherwise"],
      ["Homes in the higher council tax bands", "left: by_choice"],
    ]);
    // Where the first of them cannot be taken, the next that can be is.
    expect(all(posh.slice(1), "first")).toEqual([
      ["Gritty", "left: crime"],
      ["What homes sell for", "more"],
      ["Homes in the higher council tax bands", "left: by_choice"],
    ]);
    // Where none can be, none is, and each says why of itself.
    expect(all([posh[1]!, posh[3]!], "first")).toEqual([
      ["Gritty", "left: crime"],
      ["Homes in the higher council tax bands", "left: by_choice"],
    ]);
    // One word counts once: of two stretches of words, one reading of each.
    expect(all(atOnce, "first").filter(([, how]) => how === "more" || how === "left: otherwise")).toEqual([
      ["Quiet streets", "more"],
      ["Nearer a park", "more"],
      ["Mix of brands", "more"],
      ["What homes sell for", "left: otherwise"],
      ["More culture nearby", "more"],
      ["Village feel", "more"],
      ["Age of buildings", "left: otherwise"],
      ["Nearer a town centre", "left: otherwise"],
      ["Renting", "more"],
      ["A budget of £1,900 a month", "more"],
      ["A 1-bedroom home", "more"],
    ]);
  });

  test("test_the_reading_the_service_marks_as_its_guess_is_the_one_that_is_taken", () => {
    const marked = [posh[0]!, posh[1]!, guessing(posh[2]!, "more"), posh[3]!];
    expect(all(marked, "first")).toEqual([
      ["Mix of brands", "left: otherwise"],
      ["Gritty", "left: crime"],
      ["What homes sell for", "more"],
      ["Homes in the higher council tax bands", "left: by_choice"],
    ]);
  });

  test("test_where_the_words_name_a_thing_no_reading_of_the_same_words_is_taken_beside_it", () => {
    // The words were taken as what they name, and count once.
    const beside = [saying(brands, { by_name: true }), prices, saying(bands, { only_by_choice: false })];
    expect(all(beside, "first")).toEqual([
      ["Mix of brands", "more"],
      ["What homes sell for", "left: otherwise"],
      ["Homes in the higher council tax bands", "left: otherwise"],
    ]);
    // What waits for a person says that of itself, and not that the words were read otherwise.
    expect(all([saying(brands, { by_name: true }), prices, bands], "first")[2]).toEqual([
      "Homes in the higher council tax bands",
      "left: by_choice",
    ]);
  });

  test("test_a_reading_of_words_that_were_taken_already_is_not_taken_when_another_reader_gives_it", () => {
    // A model reads after the rules. What it reads into words of which a reading was taken
    // is a second reading of them.
    const words = readSeveralWays(posh).get(0);
    if (words === undefined) throw new Error("the offers share no words");
    const later = { ...prices, label: "A later reading" };
    expect(all([later], "first")).toEqual([["A later reading", "more"]]);
    expect(all([later], "first", [words])).toEqual([["A later reading", "left: otherwise"]]);
    expect(all([later], "every", [words])).toEqual([["A later reading", "more"]]);
    // What the words name is taken whoever reads it.
    expect(all([saying(later, { by_name: true })], "first", [words])).toEqual([["A later reading", "more"]]);
  });

  test("test_the_other_two_ways_it_was_built_take_every_reading_or_none", () => {
    expect(all(posh, "every")).toEqual([
      ["Mix of brands", "more"],
      ["Gritty", "left: crime"],
      ["What homes sell for", "more"],
      ["Homes in the higher council tax bands", "left: by_choice"],
    ]);
    expect(all(posh, "none")).toEqual([
      ["Mix of brands", "left: several"],
      ["Gritty", "left: crime"],
      ["What homes sell for", "left: several"],
      ["Homes in the higher council tax bands", "left: by_choice"],
    ]);
    // Whichever is chosen, what is no such reading is taken as it is by itself.
    for (const how of READINGS) {
      expect(all([pubs, noise, ...counted, ...house], how)).toEqual(
        [pubs, noise, ...counted, ...house].map((offer) => [offer.label, taken(take(offer))]),
      );
    }
  });

  test("test_one_line_of_the_look_chooses_and_a_word_counts_once", () => {
    expect(READINGS).toEqual(["every", "first", "none"]);
    expect(OF_A_WORD_READ_SEVERAL_WAYS).toBe("first");
  });
});

describe("what was taken, by what it is of", () => {
  test("test_a_thing_is_told_from_every_other_by_what_it_is_of_and_a_journey_by_its_place", () => {
    const things = long.flatMap((offer) => {
      const made = take(offer);
      return made.way === null ? [] : [thingOf(offer, made.operations)];
    });

    expect(things).toContain("commute:syn-p0017");
    expect(things).toContain("tag:quiet_residential");
    expect(new Set(things).size).toBe(things.length);
    // The rules name a budget by its amount and "a month", and a model by its amount: one thing.
    const byTheRules = atOnce.filter((one) => one.target === "budget").map((one) => one.label);
    const byAModel = long.filter((one) => one.target === "budget").map((one) => one.label);
    expect(byTheRules).not.toEqual(byAModel);
    expect(thingOf(of(atOnce, "budget"), NO_EDITS)).toBe(thingOf(of(long, "budget"), NO_EDITS));
  });
});

describe("a question about a place", () => {
  test("test_it_is_settled_with_the_first_place_the_service_gives", () => {
    const [question] = asked.clarify;
    if (!question) throw new Error("the recording holds no question");
    const settled = settledOf(asked.operations, question);

    expect(question.options.length).toBeGreaterThan(1);
    expect(settled.option).toBe(question.options[0]);
    expect(settled.operations).toEqual({
      ...NO_EDITS,
      commute_ops: [{ ...asked.operations.commute_ops[question.index], place_id: question.options[0]?.id }],
    });
  });

  test("test_where_the_service_gives_no_place_nothing_is_taken", () => {
    const [question] = notFound.clarify;
    if (!question) throw new Error("the recording holds no question");

    expect(question.options).toEqual([]);
    expect(settledOf(notFound.operations, question)).toEqual({ option: null, operations: null });
  });
});
