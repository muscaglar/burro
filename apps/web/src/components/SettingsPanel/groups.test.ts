import { DIMENSION, SEGMENT } from "@/content/labels";
import { HIDDEN, HOLDS, SETTINGS } from "@/content/settings";
import { USUAL } from "@/content/usual";
import { recordedAnswer } from "@/lib/api/recorded";
import type { FeatureWeight, PreferenceSpec, TagWeight } from "@/lib/api/schema";

import { inAName } from "../kit/drawings";
import { drawingOf, PLAIN } from "../kit/Thing/drawn";
import { A_COUPLE, groupsOf, hasBegun, heldBy, homeOf, madeOf, ofFamily, openAtFirst } from "./groups";
import { OPENS_AT_FIRST, OPENS_AT_FIRST_ARE, type OpensAtFirst } from "./look";

const meta = recordedAnswer("get_meta", "meta").body.data;
/**
 * What the service calls each family of vibes, by the id of the family. A name is the
 * service's to write, and it has written two again: so a test finds a group by the name
 * the service gives it, and writes none down.
 */
const familyCalled = (id: string) => meta.families.find((one) => one.family === id)?.label ?? id;
const [STREETS, GOING_OUT, GREEN, DAILY_LIFE, WHO_LIVES_THERE] = [
  familyCalled("streets_homes"),
  familyCalled("pace_food"),
  familyCalled("green"),
  familyCalled("daily_life"),
  familyCalled("who_lives_there"),
];
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** "Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works", as it was read. */
const first = recordedAnswer("rank", "rank-first").body.data.spec;
const NAMED = { "syn-p0021": "Cindermoor Works", "syn-p0017": "Pellam Cross" } as const;
const FAMILIES = meta.families.map((one) => one.label);

/** What a search starts from, as a search that is open holds it: nothing in it was asked for. */
const nothingAsked: PreferenceSpec = { ...meta.defaults.rent };

const groups = (spec: PreferenceSpec) => groupsOf(spec, meta, areas, NAMED);
/** The same search with nothing in it that nobody chose: what is left is what a person asked for. */
const askedAlone = (spec: PreferenceSpec): PreferenceSpec => ({
  ...spec,
  weights: spec.weights.filter((weight) => weight.provenance !== "default"),
  tags: spec.tags.filter((weight) => weight.provenance !== "default"),
});
/** What the bar of each group says of what a person asked for, by what the group is called. */
const held = (spec: PreferenceSpec) => new Map(groups(askedAlone(spec)).map((group) => [group.label, group.holds]));
/** What the bar of each group says, of all that counts, by what the group is called. */
const said = (spec: PreferenceSpec) => new Map(groups(spec).map((group) => [group.label, group.holds]));
/** The groups that stand open at first, by what each is called, whichever way is chosen. */
const open = (spec: PreferenceSpec, which: OpensAtFirst = OPENS_AT_FIRST) => {
  const at = openAtFirst(groups(spec), hasBegun(spec, meta), spec, meta, which);
  return groups(spec)
    .filter((group) => at.has(group.key))
    .map((group) => group.label);
};
/** A couple of groups, of which those that hold what was asked for come first, as one of the other ways has it. */
const openCouple = (spec: PreferenceSpec) => open(spec, "a-couple");
/** Every group that holds what was asked for, as the other has it. */
const openEvery = (spec: PreferenceSpec) => open(spec, "all-asked");
/** The ways that leave a group open once a search is open. */
const LEAVE_OPEN = OPENS_AT_FIRST_ARE.filter((which) => which !== "none");

const asked = (weight: Partial<TagWeight> & Pick<TagWeight, "tag_id">): TagWeight => ({
  weight: 0.5,
  toward: "high",
  provenance: "stated",
  ...weight,
});
const switched = (weight: Partial<FeatureWeight> & Pick<FeatureWeight, "feature_id">): FeatureWeight => ({
  weight: 0.5,
  direction: "more",
  provenance: "ui_edit",
  ...weight,
});

describe("the groups of the settings", () => {
  test("test_the_groups_stand_in_the_order_they_always_stood_in", () => {
    expect(groups(first).map((group) => group.label)).toEqual([
      SETTINGS.money,
      SETTINGS.journeys,
      ...FAMILIES,
      DIMENSION.brands,
      SETTINGS.airAndNoise,
      DIMENSION.crime,
    ]);
    // The areas a person hid are a group only while one is hidden.
    const hidden = { ...first, areas: [{ area_id: areas[0]?.area_id ?? "", rule: "exclude", provenance: "ui_edit" }] } as const;
    expect(groups(hidden).at(-1)?.label).toBe(HIDDEN.legend);
  });

  test("test_every_group_has_a_key_of_its_own_which_holds_nothing_a_person_typed", () => {
    const keys = groups(first).map((group) => group.key);

    expect(new Set(keys).size).toBe(keys.length);
    expect(keys).toEqual([
      "money",
      "journeys",
      ...meta.families.map((one) => ofFamily(one.family)),
      "brands",
      "apart",
      "crime",
    ]);
  });

  test("test_no_group_is_drawn_by_the_plain_box_and_one_that_is_of_no_family_is_drawn_by_the_dimension_of_what_it_holds", () => {
    // Three groups stood under the plain box, where every family of vibes had a drawing of
    // its own: they hold measures the service puts in no family of vibes, or that the
    // settings show apart from theirs. Each is drawn as a family is, by the dimension the
    // service gives what it holds. No dimension is written here: each is read off the measures.
    const held = heldBy(meta, first.tenure);
    const apart = new Map([
      ["brands", held.brands],
      ["apart", held.apart],
      ["crime", held.crime],
    ]);
    const drawn = new Map(groups(first).map((group) => [group.key as string, drawingOf(group.thing)]));

    expect([...drawn].filter(([, drawing]) => drawing === PLAIN).map(([key]) => key)).toEqual([]);
    for (const [key, measures] of apart) {
      const dimensions = [...new Set(measures.map((metric) => metric.dimension))];
      expect([key, dimensions.length]).toEqual([key, 1]);
      expect([key, drawn.get(key)]).toEqual([key, `thing-family-${inAName(dimensions[0] ?? "")}`]);
    }
    // Every group has a drawing of its own: no two are drawn alike.
    expect(new Set(drawn.values()).size).toBe(drawn.size);
  });

  test("test_a_group_whose_measures_are_of_more_dimensions_than_one_is_drawn_by_none_of_them", () => {
    // A later release may put a measure of another kind in no family. No one dimension then
    // stands for the group that holds both, and it is drawn by the plain one, and never by
    // the drawing of a part of what it holds.
    const held = heldBy(meta, first.tenure);
    const shownApart = new Set([...held.brands, ...held.apart, ...held.crime].map((metric) => metric.dimension));
    const [other] = meta.features.filter((metric) => metric.rankable && metric.family !== null && !shownApart.has(metric.dimension));
    if (other === undefined) throw new Error("The recorded release holds no measure of a family.");
    const mixed = { ...meta, features: meta.features.map((metric) => (metric === other ? { ...other, family: null } : metric)) };
    const group = groupsOf(first, mixed, areas, NAMED).find((one) => one.key === "apart");

    expect(new Set(heldBy(mixed, first.tenure).apart.map((metric) => metric.dimension)).size).toBe(2);
    expect(group === undefined ? null : drawingOf(group.thing)).toBe(PLAIN);
  });

  test("test_a_family_the_release_holds_nothing_of_is_no_group", () => {
    const [one] = meta.families;
    const without = {
      ...meta,
      tags: meta.tags.filter((tag) => tag.family !== one?.family),
      features: meta.features.filter((metric) => metric.family !== one?.family),
    };

    expect(heldBy(meta).families.map((family) => family.label)).toEqual(FAMILIES);
    expect(heldBy(without).families.map((family) => family.label)).toEqual(FAMILIES.slice(1));
  });
});

describe("what stands open at first", () => {
  test("test_which_groups_stand_open_at_first_is_chosen_in_one_line_and_once_a_search_is_open_none_does", () => {
    // The founder: "Leave a couple of the accordians open by default to indicate this."
    // That is before a search. Once one is open a person came to change one thing.
    expect(A_COUPLE).toBe(2);
    expect(OPENS_AT_FIRST_ARE).toEqual(["none", "a-couple", "all-asked"]);
    expect(OPENS_AT_FIRST).toBe("none");
  });

  test.each(OPENS_AT_FIRST_ARE)("test_before_a_search_the_first_two_groups_stand_open: %s", (which) => {
    expect(hasBegun(meta.defaults.rent, meta)).toBe(false);
    expect(open(meta.defaults.rent, which)).toEqual([SETTINGS.money, SETTINGS.journeys]);
    // A person who chose buying before anything was asked for has begun no search.
    expect(hasBegun(meta.defaults.buy, meta)).toBe(false);
    expect(open(meta.defaults.buy, which)).toEqual([SETTINGS.money, SETTINGS.journeys]);
  });

  test("test_once_a_search_is_open_every_group_is_closed_whatever_was_asked_for", () => {
    // Walked at 1440 by 900: with two groups open the settings were 2,022 px high, and the
    // first result went from 927 to 2,949. The bar of every group says what it holds.
    expect(hasBegun(first, meta)).toBe(true);
    expect(open(first)).toEqual([]);
    expect(open(nothingAsked)).toEqual([]);
    for (const name of ["rank-first", "rank-scale", "rank-buyer-family", "rank-nights-out", "rank-switched-off", "rank-crime-switched-on"] as const) {
      expect([name, open(recordedAnswer("rank", name).body.data.spec)]).toEqual([name, []]);
    }
    // What was asked for is still said, on the bar of its group.
    expect(groups(first).filter((group) => group.asked).map((group) => group.label)).toEqual([
      SETTINGS.money,
      SETTINGS.journeys,
      STREETS,
      GREEN,
    ]);
  });

  test.each(LEAVE_OPEN)("test_where_a_search_is_open_and_nothing_was_asked_for_the_first_two_stand_open: %s", (which) => {
    // As when a person ranks the settings as they stand.
    expect(hasBegun(nothingAsked, meta)).toBe(true);
    expect(open(nothingAsked, which)).toEqual([SETTINGS.money, SETTINGS.journeys]);
  });

  test("test_by_one_line_two_groups_stand_open_and_those_that_hold_what_was_asked_for_come_first", () => {
    // A budget, a journey, quiet streets and leafy were asked for: the first two of their groups.
    expect(openCouple(first)).toEqual([SETTINGS.money, SETTINGS.journeys]);
    // Leafy and quiet, and no more: the groups of the two.
    const vibes = { ...nothingAsked, tags: first.tags };
    expect(openCouple(vibes)).toEqual([STREETS, GREEN]);
    // A journey and a vibe, with the money between them untouched.
    expect(openCouple({ ...vibes, commutes: first.commutes, tags: [asked({ tag_id: "leafy" })] })).toEqual([SETTINGS.journeys, GREEN]);
  });

  test("test_where_one_group_holds_what_was_asked_for_the_first_of_the_rest_stands_open_beside_it", () => {
    // Two stand open, so that it is seen that a group opens and closes, whatever was asked for.
    const scale = recordedAnswer("rank", "rank-scale").body.data.spec;

    expect(openCouple(scale)).toEqual([SETTINGS.money, GOING_OUT]);
    expect(openCouple({ ...nothingAsked, tags: [asked({ tag_id: "leafy" })] })).toEqual([SETTINGS.money, GREEN]);
    expect(openCouple({ ...nothingAsked, commutes: first.commutes })).toEqual([SETTINGS.money, SETTINGS.journeys]);
    expect(openCouple({ ...nothingAsked, budget: first.budget })).toEqual([SETTINGS.money, SETTINGS.journeys]);
  });

  test("test_never_more_than_a_couple_stand_open_at_first_however_much_was_asked_for", () => {
    // Measured in a browser at 390 by 844, with every group that held what was asked for
    // open: after a plain search the settings were 5,187 px high and drew 79 controls.
    const much = recordedAnswer("rank", "rank-crime-switched-on").body.data.spec;

    expect(openEvery(much).length).toBeGreaterThan(4);
    expect(openCouple(much)).toEqual([SETTINGS.money, SETTINGS.journeys]);
    for (const name of ["rank-first", "rank-scale", "rank-buyer-family", "rank-nights-out", "rank-switched-off"] as const) {
      expect([name, openCouple(recordedAnswer("rank", name).body.data.spec).length]).toEqual([name, A_COUPLE]);
    }
  });

  test("test_the_other_way_every_group_that_holds_something_asked_for_stands_open", () => {
    expect(openEvery(first)).toEqual([SETTINGS.money, SETTINGS.journeys, STREETS, GREEN]);
    // A search that asks for one thing opens the group of that thing, and no other.
    expect(openEvery(recordedAnswer("rank", "rank-scale").body.data.spec)).toEqual([GOING_OUT]);
    expect(openEvery({ ...nothingAsked, tags: [asked({ tag_id: "leafy" })] })).toEqual([GREEN]);
  });

  test.each(OPENS_AT_FIRST_ARE)("test_a_usual_setting_that_nobody_chose_opens_no_group: %s", (which) => {
    const usual = meta.defaults.rent.weights.filter((weight) => weight.weight > 0);

    // Six of them count in a search that starts, and their groups are closed all the same.
    expect(usual.length).toBeGreaterThan(3);
    expect(usual.every((weight) => weight.provenance === "default")).toBe(true);
    expect(open(nothingAsked, which)).not.toContain(SETTINGS.airAndNoise);
    expect(groups(nothingAsked).find((group) => group.label === SETTINGS.airAndNoise)?.asked).toBe(false);
  });

  test("test_recorded_crime_stands_open_only_once_a_person_has_switched_it_on", () => {
    const on = recordedAnswer("rank", "rank-crime-switched-on").body.data.spec;
    const alone = { ...nothingAsked, weights: on.weights };

    expect(openEvery(first)).not.toContain(DIMENSION.crime);
    expect(openEvery(on)).toContain(DIMENSION.crime);
    // And where it is all that was asked for, it is one of the couple.
    expect(openCouple(nothingAsked)).not.toContain(DIMENSION.crime);
    expect(openCouple(alone)).toEqual([SETTINGS.money, DIMENSION.crime]);
    // As the website is left, it stands open only once a person has opened it.
    expect(open(on)).toEqual([]);
  });

  test.each(OPENS_AT_FIRST_ARE)("test_what_a_vibe_is_made_of_stands_open_where_a_person_asked_for_a_part_of_it: %s", (which) => {
    const station = { ...nothingAsked, weights: [switched({ feature_id: "station_walk" })] };
    const at = openAtFirst(groups(station), true, station, meta, which);
    const made = meta.tags.filter((tag) => at.has(madeOf(tag))).map((tag) => tag.tag_id);

    // Every vibe whose recipe holds the part: what was asked for is in sight wherever a person opens.
    expect(made.sort()).toEqual(
      meta.tags
        .filter((tag) => tag.terms.some((term) => term.feature_id === "station_walk"))
        .map((tag) => tag.tag_id)
        .sort(),
    );
    expect(made.length).toBeGreaterThan(0);
    // Before a search nothing was asked for, and where a search holds no part by itself none stands open.
    expect([...openAtFirst(groups(station), false, station, meta, which)].filter((key) => key.startsWith("made:"))).toEqual([]);
    const noPart = askedAlone(first);
    expect([...openAtFirst(groups(noPart), true, noPart, meta, which)].filter((key) => key.startsWith("made:"))).toEqual([]);
  });

  test.each(OPENS_AT_FIRST_ARE)("test_what_a_vibe_is_made_of_stands_open_where_it_holds_what_the_bar_of_its_group_names: %s", (which) => {
    // Seen in a browser: the bar of Green said "Counted in every search: Nearer a park", and
    // the group opened onto no such thing. Its switch stood in what a vibe is made of, closed.
    const made = (spec: PreferenceSpec, begun: boolean) =>
      meta.tags.filter((tag) => openAtFirst(groups(spec), begun, spec, meta, which).has(madeOf(tag))).map((tag) => tag.tag_id);

    // What goes into a vibe, of what a search of renting starts from, each in the group whose bar names it.
    expect(made(nothingAsked, true).sort()).toEqual(["everyday_on_foot", "pace", "parks_close_by"]);
    // Before a search too: what is counted is counted from the first.
    expect(made(meta.defaults.rent, false).sort()).toEqual(["everyday_on_foot", "pace", "parks_close_by"]);
    expect(made(meta.defaults.buy, false).sort()).toEqual(["everyday_on_foot", "leafy", "pace", "parks_close_by"]);
    // In the one group whose bar names it, and in no other that holds the part.
    const park = meta.tags.filter((tag) => tag.terms.some((term) => term.feature_id === "park_proximity"));
    expect(park.map((tag) => tag.tag_id).sort()).toEqual(["family_amenities", "family_area", "parks_close_by"]);
    expect(made(first, true).sort()).toEqual(["everyday_on_foot", "pace", "parks_close_by"]);
    // So whatever a bar names as counted in every search is in sight as its group opens:
    // the group draws it beside its vibes, or a vibe of the group that holds it stands open.
    const holds = heldBy(meta);
    const beside = [...holds.apart, ...holds.brands, ...holds.crime, ...holds.families.flatMap((family) => family.others)];
    const named = groups(first).flatMap((group) => group.usual.map((name) => ({ group, name })));
    expect(named).toHaveLength(6);
    for (const { group, name } of named) {
      const metric = meta.features.find((one) => one.short_label === name);
      const open = meta.tags.filter((tag) => made(first, true).includes(tag.tag_id) && ofFamily(tag.family) === group.key);
      const inAVibe = open.some((tag) => tag.terms.some((term) => term.feature_id === metric?.feature_id));
      expect([name, beside.some((one) => one.feature_id === metric?.feature_id) || inAVibe]).toEqual([name, true]);
    }
  });
});

describe("what the bar of a group says of what the group holds", () => {
  test("test_it_says_nothing_of_what_was_asked_for_where_nothing_was", () => {
    expect([...held(meta.defaults.rent).values()]).toEqual(groups(meta.defaults.rent).map(() => null));
    expect([...held(nothingAsked).values()]).toEqual(groups(nothingAsked).map(() => null));
    expect(groups(nothingAsked).filter((group) => group.asked)).toEqual([]);
  });

  test("test_the_money_says_renting_or_buying_and_what_can_be_paid", () => {
    // "for about £1,700 a month" is no firm limit, and the bar does not make it one.
    expect(first.budget).toMatchObject({ amount: 1700, strictness: "soft" });
    expect(held(first).get(SETTINGS.money)).toBe("Renting, ideally up to £1,700 a month");
    const firm = { ...first, budget: { ...first.budget, strictness: "hard" } } as const;
    expect(held(firm).get(SETTINGS.money)).toBe("Renting, up to £1,700 a month");

    const buyer = recordedAnswer("rank", "rank-buyer-family").body.data.spec;
    expect(buyer.budget).toMatchObject({ amount: 450000, strictness: "soft" });
    expect(held(buyer).get(SETTINGS.money)).toBe("Buying, ideally up to £450,000");
  });

  test("test_with_no_sum_set_the_money_says_what_a_person_chose_of_it_and_nothing_nobody_chose", () => {
    const chose = (budget: Partial<PreferenceSpec["budget"]>, spec: Partial<PreferenceSpec> = {}) =>
      held({ ...nothingAsked, ...spec, budget: { ...nothingAsked.budget, ...budget } }).get(SETTINGS.money);

    expect(chose({})).toBeNull();
    // Buying is a thing somebody chose, though the spec a search starts from says nobody set it.
    expect(held(meta.defaults.buy).get(SETTINGS.money)).toBe("Buying");
    expect(chose({}, { tenure_from: "ui_edit" })).toBe("Renting");
    expect(chose({ segment: "bed_2", provenance: "ui_edit" })).toBe(`Renting, ${SEGMENT.bed_2}`);
  });

  test("test_the_journeys_say_each_place_by_its_name_and_the_longest_journey_to_it", () => {
    expect(first.commutes).toMatchObject([{ place_id: "syn-p0021", max_minutes: 35, strictness: "soft" }]);
    expect(held(first).get(SETTINGS.journeys)).toBe("Cindermoor Works, ideally within 35 minutes");

    const [one] = first.commutes;
    const two = {
      ...first,
      commutes: [
        { ...one, strictness: "hard" },
        { ...one, place_id: "syn-p0017", max_minutes: 45 },
      ],
    } as PreferenceSpec;
    expect(held(two).get(SETTINGS.journeys)).toBe(
      "Cindermoor Works within 35 minutes; Pellam Cross, ideally within 45 minutes",
    );
  });

  test("test_a_family_says_its_vibes_that_were_asked_for_by_the_names_the_api_gives", () => {
    expect(held(first).get(GREEN)).toBe("Leafy");
    expect(held(first).get(STREETS)).toBe("Quiet streets");
    expect(held(first).get(GOING_OUT)).toBeNull();
    // A scale says which of its ends was asked for.
    const calm = recordedAnswer("rank", "rank-scale").body.data.spec;
    const buzzy = recordedAnswer("rank", "rank-scale-turned").body.data.spec;
    expect(held(calm).get(GOING_OUT)).toBe(HOLDS.towards("Going out", "Calm"));
    expect(held(buzzy).get(GOING_OUT)).toBe("Going out towards Buzzy");
  });

  test("test_a_thing_a_person_took_off_is_said_to_be_not_counted_and_never_as_a_wish_for_it", () => {
    // "ignore the high street", as it was read.
    const spec = recordedAnswer("interpret", "interpret-second-sentence").body.data.spec;

    expect(spec.weights.find((weight) => weight.feature_id === "highstreet_access")).toMatchObject({ weight: 0, provenance: "stated" });
    expect(held(spec).get(GOING_OUT)).toBe("Not counted: Nearer a town centre");
    // What counts comes first, and what was taken off after it.
    const both = { ...spec, tags: [...spec.tags, asked({ tag_id: "foodie" })] };
    expect(held(both).get(GOING_OUT)).toBe("Food and drink. Not counted: Nearer a town centre");
  });

  test("test_a_part_of_a_recipe_is_said_on_the_bar_of_one_group_which_is_that_of_its_own_kind", () => {
    // "Nearer a station" is a part of two vibes, one of daily life and one of who lives there.
    const station = meta.features.find((metric) => metric.feature_id === "station_walk");
    const of = meta.tags.filter((tag) => tag.terms.some((term) => term.feature_id === "station_walk")).map((tag) => tag.family);
    const spec = { ...nothingAsked, weights: [switched({ feature_id: "station_walk" })] };

    expect(station?.family).toBe("daily_life");
    expect(of.sort()).toEqual(["daily_life", "who_lives_there"]);
    expect(homeOf(station as NonNullable<typeof station>, heldBy(meta))).toBe(ofFamily("daily_life"));
    expect(held(spec).get(DAILY_LIFE)).toBe("Nearer a station");
    expect(held(spec).get(WHO_LIVES_THERE)).toBeNull();
    expect(openEvery(spec)).toEqual([DAILY_LIFE]);
  });

  test("test_every_feature_the_release_can_rank_is_said_on_the_bar_of_one_group_that_shows_it", () => {
    const holds = heldBy(meta);
    const rankable = meta.features.filter((metric) => metric.rankable);

    for (const metric of rankable) {
      const home = homeOf(metric, holds);
      const spec = { ...nothingAsked, weights: [switched({ feature_id: metric.feature_id })] };
      const speak = groups(spec).filter((group) => group.holds !== null);
      expect([metric.feature_id, speak.map((group) => [group.key, group.holds, group.asked])]).toEqual([
        metric.feature_id,
        [[home, metric.short_label, true]],
      ]);
    }
    expect(rankable.length).toBeGreaterThan(40);
  });

  test("test_recorded_crime_and_what_is_of_no_family_are_said_on_their_own_bars_whatever_recipe_holds_them", () => {
    const noise = { ...nothingAsked, weights: [switched({ feature_id: "noise_exposure" })] };
    const on = recordedAnswer("rank", "rank-crime-switched-on").body.data.spec;

    // Transport noise is a part of two vibes of streets and homes, and is of air and noise.
    expect(meta.tags.some((tag) => tag.terms.some((term) => term.feature_id === "noise_exposure"))).toBe(true);
    expect(held(noise).get(SETTINGS.airAndNoise)).toBe("Less transport noise");
    expect(held(noise).get(STREETS)).toBeNull();
    expect(held(on).get(DIMENSION.crime)).toBe("Less recorded burglary and theft");
  });

  test("test_a_long_list_names_the_first_three_and_counts_the_rest", () => {
    const brands = heldBy(meta).brands.slice(0, 5);
    const spec = { ...nothingAsked, weights: brands.map((metric) => switched({ feature_id: metric.feature_id })) };
    const named = brands.slice(0, 3).map((metric) => metric.short_label);

    expect(HOLDS.named).toBe(3);
    expect(held(spec).get(DIMENSION.brands)).toBe(`${named.join(", ")} and 2 more`);
  });

  test("test_the_areas_a_person_hid_are_said_by_name", () => {
    const [one, two] = areas;
    const hidden = {
      ...first,
      areas: [
        { area_id: one?.area_id ?? "", rule: "exclude", provenance: "ui_edit" },
        { area_id: two?.area_id ?? "", rule: "exclude", provenance: "ui_edit" },
      ],
    } as const;

    expect(held(hidden).get(HIDDEN.legend)).toBe(`${one?.name}, ${two?.name}`);
  });

  test("test_nothing_a_bar_says_is_a_code_of_the_service", () => {
    const every = [first, ...["rank-scale", "rank-buyer-family", "rank-nights-out", "rank-crime-switched-on", "rank-switched-off"].map(
      (name) => recordedAnswer("rank", name as "rank-scale").body.data.spec,
    )];
    const spoken = every.flatMap((spec) => [...said(spec).values()]).filter((holds): holds is string => holds !== null);

    expect(spoken.length).toBeGreaterThan(12);
    // No id of a vibe, a feature or a place: each has an underscore or a hyphen and a digit in it.
    expect(spoken.filter((holds) => /[a-z]_[a-z]|syn-/.test(holds))).toEqual([]);
  });
});

describe("what the bar of a group says of what nobody chose", () => {
  /** What a search starts from holds of each group, by the names the API gives. */
  const USUAL_OF_RENTING = new Map([
    [GOING_OUT, ["Nearer a town centre"]],
    [GREEN, ["Nearer a park"]],
    [DAILY_LIFE, ["Nearer a station", "More lines nearby"]],
    [SETTINGS.airAndNoise, ["Cleaner air", "Less transport noise"]],
  ]);

  test("test_a_search_starts_from_settings_that_nobody_chose_and_each_is_named_on_the_bar_of_its_group", () => {
    // A result said "Based on 9 of the 10 things that count in your search" of a search of
    // four things, and nothing in sight said what the other six were.
    const counting = meta.defaults.rent.weights.filter((weight) => weight.weight > 0);
    expect(counting).toHaveLength(6);
    expect(counting.every((weight) => weight.provenance === "default")).toBe(true);

    for (const spec of [meta.defaults.rent, nothingAsked]) {
      for (const group of groups(spec)) {
        const names = USUAL_OF_RENTING.get(group.label) ?? [];
        expect([group.label, [...group.usual].sort()]).toEqual([group.label, [...names].sort()]);
        expect([group.label, group.holds]).toEqual([
          group.label,
          names.length === 0 ? null : USUAL.onTheBar(group.usual.join(", ")),
        ]);
        // To name what nobody chose is not to say that a person asked for it.
        expect([group.label, group.asked]).toEqual([group.label, false]);
      }
    }
    expect(groups(nothingAsked).flatMap((group) => group.usual).sort()).toEqual(
      counting.map((weight) => meta.features.find((metric) => metric.feature_id === weight.feature_id)?.short_label).sort(),
    );
  });

  test("test_every_name_is_the_apis_and_each_is_said_on_one_bar_and_no_other", () => {
    const names = groups(first).flatMap((group) => group.usual);

    expect(names).toHaveLength(6);
    expect(new Set(names).size).toBe(6);
    expect(names.filter((name) => !meta.features.some((metric) => metric.short_label === name))).toEqual([]);
  });

  test("test_what_was_asked_for_comes_first_on_a_bar_then_what_is_counted_in_every_search_then_what_was_taken_off", () => {
    expect(said(first).get(GREEN)).toBe("Leafy. Counted in every search: Nearer a park");
    expect(said(first).get(STREETS)).toBe("Quiet streets");
    expect(said(first).get(SETTINGS.airAndNoise)).toBe("Counted in every search: Cleaner air, Less transport noise");
    expect(said(first).get(SETTINGS.money)).toBe("Renting, ideally up to £1,700 a month");
    // "ignore the high street", as it was read: what a person took off is no longer counted in every search.
    const spec = recordedAnswer("interpret", "interpret-second-sentence").body.data.spec;
    expect(said(spec).get(GOING_OUT)).toBe("Not counted: Nearer a town centre");
    expect(groups(spec).flatMap((group) => group.usual)).not.toContain("Nearer a town centre");
  });

  test("test_a_setting_a_person_changed_is_theirs_and_is_no_longer_said_to_be_counted_in_every_search", () => {
    const park = meta.defaults.rent.weights.find((weight) => weight.feature_id === "park_proximity");
    const turnedUp = {
      ...nothingAsked,
      weights: nothingAsked.weights.map((weight) => (weight === park ? { ...weight, weight: 0.8, provenance: "ui_edit" as const } : weight)),
    };

    expect(said(nothingAsked).get(GREEN)).toBe("Counted in every search: Nearer a park");
    expect(said(turnedUp).get(GREEN)).toBe("Nearer a park");
    expect(groups(turnedUp).find((group) => group.label === GREEN)).toMatchObject({ asked: true, usual: [] });
  });

  test("test_the_money_and_the_journeys_hold_nothing_that_is_counted_in_every_search", () => {
    // How much the budget and the journeys count is set from the first, and counts for
    // nothing until a budget is set or a place is named.
    expect(meta.defaults.rent.budget).toMatchObject({ amount: null, provenance: "default" });
    expect(meta.defaults.rent.commutes).toEqual([]);
    for (const spec of [meta.defaults.rent, first]) {
      for (const label of [SETTINGS.money, SETTINGS.journeys]) {
        expect(groups(spec).find((group) => group.label === label)?.usual).toEqual([]);
      }
    }
  });
});
