/** @jest-environment node */
/**
 * Which lines a result draws. The founder, who had walked the website three times, asked
 * of a result for "title of what was asked for, the visual gauge, and where relevent, the
 * approx data call out". A result drew a line for each vibe that was asked for and for
 * nothing else that was: a search for one journey drew two vibes that nobody asked for,
 * and nothing of the journey.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { CARD } from "@/content/card";
import { KNOWN } from "@/content/kit";
import { BREAKDOWN, JOURNEYS } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Fact, RankData, RankedArea } from "@/lib/api/schema";
import { namesOfPlaces } from "@/lib/search/chips";

import { thingOf as thingOfAChip } from "../ChipRow/drawn";
import { drawingOf } from "../kit/Thing/drawn";
import { columnOf, linesOf, standsLower, type Held, type Look } from "./lines";
import { A_MEASURE_RUNS, A_MEASURE_MAY_RUN, OTHERS_STAND } from "./look";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const profile = (areaId: string) =>
  recordedAnswer("get_area", `area/${areas.find((area) => area.area_id === areaId)?.slug ?? ""}`).body.data;

const LOOK: Look = { others: OTHERS_STAND, fitSaid: "working", runs: A_MEASURE_RUNS };

const ranking = (name: string): RankData => recordedAnswer("rank", name).body.data;
/** The names of the places of a search, as the answer that brought the search gave them. */
const placesOf = (ranked: RankData) =>
  namesOfPlaces(ranked.spec, Object.fromEntries(ranked.places.map((place) => [place.place_id, place.name])));
/** What a card holds of a result: the facts of its profile, and the places of its search. */
const aCard = (ranked: RankData, area: RankedArea, more: readonly Fact[] = []): Held => ({
  facts: Object.fromEntries([...profile(area.area_id).facts, ...more].map((fact) => [fact.fact_id, fact])),
  places: placesOf(ranked),
});
/** What a row holds: the ranking, and the places of its search. */
const aRow = (ranked: RankData): Held => ({ facts: null, places: placesOf(ranked) });
const at = (ranked: RankData, place: number) => ranked.ranked[place] as RankedArea;
const shortOf = (featureId: string) => meta.features.find((one) => one.feature_id === featureId)?.short_label;

describe("every thing that was asked for has its line", () => {
  test("test_the_lines_stand_in_the_order_the_search_holds_them_a_vibe_a_measure_a_journey_a_budget", () => {
    const asked = ranking("rank-one-press");
    const area = at(asked, 0);
    const lines = linesOf(area, meta, asked.spec, aCard(asked, area), LOOK);

    expect(asked.spec.tags.map((tag) => tag.tag_id)).toEqual(["quiet_residential"]);
    expect(lines.marks.map((mark) => mark.tag_id)).toEqual(["quiet_residential"]);
    // The measures in the order of the search, then each journey by the name of its place, then the budget.
    expect(lines.asked.map((line) => line.name)).toEqual([
      ...asked.spec.weights.filter((weight) => weight.provenance !== "default").map((weight) => shortOf(weight.feature_id)),
      ...asked.places.map((place) => place.name),
      BREAKDOWN.budget,
    ]);
    expect(lines.asked.map((line) => line.thing.kind)).toEqual(["feature", "feature", "place", "budget"]);
  });

  test("test_what_nobody_chose_and_what_counts_for_nothing_have_no_line", () => {
    const asked = ranking("rank-switched-off");
    const area = at(asked, 0);
    const lines = linesOf(area, meta, asked.spec, aCard(asked, area), LOOK);

    // Six measures count in every search, and one that was asked for was taken off again.
    expect(asked.spec.weights.filter((weight) => weight.provenance === "default").length).toBeGreaterThan(3);
    expect(asked.spec.weights.filter((weight) => weight.provenance !== "default").map((weight) => weight.weight)).toEqual([0]);
    expect(lines.asked.map((line) => line.thing.kind)).toEqual(["place", "budget"]);
  });

  test("test_a_journey_says_how_long_it_takes_in_minutes_and_on_which_side_of_its_limit_it_falls", () => {
    const asked = ranking("rank-first");
    const said = asked.ranked.map((area) => linesOf(area, meta, asked.spec, aRow(asked), LOOK).asked.find((line) => line.thing.kind === "place"));
    const [commute] = asked.spec.commutes;

    expect(said.map((line) => line?.name)).toEqual(asked.ranked.map(() => asked.places[0]?.name));
    asked.ranked.forEach((area, place) => {
      const [leg] = area.legs;
      expect([place, said[place]?.figure, said[place]?.side, said[place]?.known]).toEqual([
        place,
        JOURNEYS.minutes(leg?.minutes ?? -1),
        (leg?.minutes ?? 0) <= (commute?.max_minutes ?? 0) ? CARD.side.within : CARD.side.over,
        "whole",
      ]);
    });
    // Both sides are met in the recording, and each is one word.
    expect(new Set(said.map((line) => line?.side))).toEqual(new Set([CARD.side.within, CARD.side.over]));
    expect([CARD.side.within, CARD.side.over]).toEqual([JOURNEYS.within, JOURNEYS.over]);
  });

  test("test_a_journey_that_was_estimated_says_its_band_with_approx_data_and_no_minutes", () => {
    const asked = recordedAnswer("rank", "estimate/rank").body.data;
    const said = asked.ranked.map((area) => linesOf(area, meta, asked.spec, aRow(asked), LOOK).asked[0]);

    asked.ranked.forEach((area, place) => {
      const band = area.legs[0]?.estimate;
      expect(area.legs[0]?.status).toBe("estimated");
      expect([place, said[place]?.known, said[place]?.figure, said[place]?.side]).toEqual([
        place,
        "some",
        band === null || band === undefined ? undefined : JOURNEYS.estimated[band],
        undefined,
      ]);
      expect(/\d/.test(said[place]?.figure ?? "")).toBe(false);
    });
    expect(KNOWN.some).toBe("approx data");
  });

  test("test_a_journey_longer_than_the_data_holds_says_so_and_one_with_no_time_says_no_data", () => {
    const onFoot = ranking("rank-on-foot");
    const beyond = onFoot.ranked.findIndex((area) => area.legs[0]?.status === "beyond_cutoff");
    const far = linesOf(at(onFoot, beyond), meta, onFoot.spec, aRow(onFoot), LOOK).asked.find((line) => line.thing.kind === "place");

    expect(beyond).toBeGreaterThanOrEqual(0);
    expect([far?.figure, far?.side, far?.known]).toEqual([JOURNEYS.beyond(meta.limits.cutoff_minutes.walk), CARD.side.over, "whole"]);

    // Of two journeys one has no time: it says so by the name of its place, and the other gives its minutes.
    const one = ranking("rank-only-one");
    const lines = linesOf(at(one, 0), meta, one.spec, aRow(one), LOOK).asked;
    expect(at(one, 0).legs.map((leg) => leg.status)).toEqual(["ok", "missing"]);
    expect(lines.map((line) => [line.name, line.known, line.figure])).toEqual([
      [one.places[0]?.name, "whole", JOURNEYS.minutes(at(one, 0).legs[0]?.minutes ?? -1)],
      [one.places[1]?.name, "none", undefined],
    ]);
  });

  test("test_a_budget_says_what_a_home_of_the_kind_costs_as_the_service_gives_it_and_on_which_side_of_the_budget_that_falls", () => {
    const asked = ranking("rank-first");
    const reasons = recordedAnswer("explain_top", "explanations-first").body.data.facts;

    asked.ranked.slice(0, 5).forEach((area, place) => {
      const fact = reasons.find((one) => one.fact_id === `${area.area_id}/budget_fit/rent.bed_1`);
      const onACard = linesOf(area, meta, asked.spec, aCard(asked, area, reasons), LOOK).asked.find((line) => line.thing.kind === "budget");
      const onARow = linesOf(area, meta, asked.spec, aRow(asked), LOOK).asked.find((line) => line.thing.kind === "budget");

      // The amount is a slot of the fact, as the service formatted it, and a rent is by the month.
      expect(fact?.slots.upper).toBeDefined();
      expect([place, onACard?.figure]).toEqual([place, `£${fact?.slots.upper} a month`]);
      expect([place, onACard?.side]).toEqual([place, fact?.template === "budget_over" ? CARD.side.over : CARD.side.within]);
      // A row holds no fact, and says what the ranking gave: it reads the same.
      expect([place, onARow]).toEqual([place, onACard]);
    });
    const sides = asked.ranked.map((area) => linesOf(area, meta, asked.spec, aRow(asked), LOOK).asked.at(-1)?.side);
    expect(new Set(sides)).toEqual(new Set([CARD.side.within, CARD.side.over]));
  });

  test("test_a_price_with_no_range_is_given_where_its_fact_is_in_hand_and_the_side_it_falls_on_always", () => {
    const asked = recordedAnswer("rank", "one-number/rank-buyer").body.data;
    const reasons = recordedAnswer("explain_top", "one-number/explanations-buyer").body.data.facts;
    const [area] = asked.ranked;
    if (area === undefined) throw new Error("The recording ranks nothing.");
    const fact = reasons.find((one) => one.fact_id === area.contributions.find((part) => part.component === "budget")?.fact_ids[0]);
    const held: Held = { facts: Object.fromEntries(reasons.map((one) => [one.fact_id, one])), places: new Map() };

    expect(area.budget?.upper_quartile).toBeNull();
    expect(fact?.slots.median).toBeDefined();
    expect(linesOf(area, meta, asked.spec, held, LOOK).asked.map((line) => [line.figure, line.side])).toEqual([
      [`£${fact?.slots.median}`, CARD.side.over],
    ]);
    // The ranking gives no amount of such a price, and nothing is worked out in its place.
    expect(linesOf(area, meta, asked.spec, { facts: null, places: new Map() }, LOOK).asked.map((line) => [line.figure, line.side])).toEqual([
      [undefined, CARD.side.over],
    ]);
  });

  test("test_a_thing_with_no_figure_says_no_data_by_its_name", () => {
    const two = ranking("rank-two-journeys");
    const lines = linesOf(at(two, 0), meta, two.spec, aRow(two), LOOK).asked;

    expect(at(two, 0).contributions.filter((part) => !part.present).map((part) => part.component)).toEqual(["budget"]);
    expect(lines.at(-1)).toMatchObject({ name: BREAKDOWN.budget, known: "none" });
    expect(lines.at(-1)?.figure).toBeUndefined();

    const family = ranking("rank-buyer-family");
    const lacking = family.ranked.find((area) => area.contributions.some((part) => part.component === "feature:school_primary_attainment" && !part.present));
    if (lacking === undefined) throw new Error("The recording holds no area that lacks the measure.");
    const measure = linesOf(lacking, meta, family.spec, aCard(family, lacking), LOOK).asked.find((line) => line.name === shortOf("school_primary_attainment"));
    expect([measure?.known, measure?.gauge, measure?.figure]).toEqual(["none", undefined, undefined]);
    // Where the look has what a fit is based on said in sentences on the result, the sentence names it.
    expect(linesOf(at(two, 0), meta, two.spec, aRow(two), { ...LOOK, fitSaid: "result" }).asked.map((line) => line.known)).not.toContain("none");
  });

  test("test_a_visit_has_no_line_of_a_budget", () => {
    const visit = recordedAnswer("rank", "visiting/rank").body.data;

    expect(visit.spec.tenure).toBe("visit");
    for (const area of visit.ranked) {
      expect(linesOf(area, meta, visit.spec, aRow(visit), LOOK).asked.map((line) => line.thing.kind)).toEqual(["feature"]);
    }
  });
});

describe("a measure, as a gauge of five steps", () => {
  const family = ranking("rank-buyer-family");
  const gaugeOf = (area: RankedArea, featureId: string, look: Look = LOOK) =>
    linesOf(area, meta, family.spec, aCard(family, area), look).asked.find((line) => line.name === shortOf(featureId));
  const factOf = (area: RankedArea, featureId: string) =>
    profile(area.area_id).facts.find((fact) => fact.fact_id === `${area.area_id}/feature/${featureId}`);

  test("test_where_an_area_stands_on_a_measure_is_the_band_its_fact_holds_among_the_areas_burro_compared", () => {
    family.ranked.slice(0, 5).forEach((area, place) => {
      const fact = factOf(area, "school_primary_attainment");
      const line = gaugeOf(area, "school_primary_attainment");
      const band = Number(fact?.slots.band);

      expect([place, band >= 1 && band <= 5]).toEqual([place, true]);
      expect([place, line?.gauge?.placed]).toEqual([place, { band, spread_low: band, spread_high: band }]);
      // Whoever hears the page is told in the words of the service: the figure, and where it stands.
      expect([place, line?.gauge?.says]).toEqual([place, `${fact?.slots.value}, ${fact?.slots.standing}`]);
      expect([place, line?.figure, line?.known]).toEqual([place, undefined, "whole"]);
    });
  });

  test("test_a_gauge_runs_towards_what_its_name_says_so_that_nearer_is_never_drawn_as_further", () => {
    // "Nearer a park" is a wish for less of its figure, which is a distance. Drawn from the
    // least figure to the most, the nearest area of all had its peg at the far left of a
    // line named "Nearer".
    const park = meta.features.find((one) => one.feature_id === "park_proximity");
    expect([park?.polarity, park?.unit]).toEqual(["less", "m"]);
    expect([A_MEASURE_RUNS, A_MEASURE_MAY_RUN]).toEqual(["name", ["name", "figure"]]);

    const bands = family.ranked.slice(0, 5).map((area) => Number(factOf(area, "park_proximity")?.slots.band));
    expect(new Set(bands).size).toBeGreaterThan(1);
    expect(family.ranked.slice(0, 5).map((area) => gaugeOf(area, "park_proximity")?.gauge?.placed.band)).toEqual(bands.map((band) => 6 - band));
    // The other way, which one line chooses: as the figure runs, from the least to the most.
    expect(
      family.ranked.slice(0, 5).map((area) => gaugeOf(area, "park_proximity", { ...LOOK, runs: "figure" })?.gauge?.placed.band),
    ).toEqual(bands);
    // A measure that is a wish for more, or for either, runs as its figure does whichever is chosen.
    const school = meta.features.find((one) => one.feature_id === "school_primary_attainment");
    expect(school?.polarity).toBe("more");
    for (const runs of A_MEASURE_MAY_RUN) {
      expect(family.ranked.slice(0, 5).map((area) => gaugeOf(area, "school_primary_attainment", { ...LOOK, runs })?.gauge?.placed.band)).toEqual(
        family.ranked.slice(0, 5).map((area) => Number(factOf(area, "school_primary_attainment")?.slots.band)),
      );
    }
  });

  test("test_a_fact_that_holds_no_band_gives_its_figure_as_the_service_words_it", () => {
    const [area] = family.ranked;
    if (area === undefined) throw new Error("The recording ranks nothing.");
    const fact = factOf(area, "park_proximity");
    if (fact === undefined) throw new Error("The profile holds no such fact.");
    const slots = Object.fromEntries(Object.entries(fact.slots).filter(([slot]) => slot !== "band"));
    const held: Held = { ...aCard(family, area), facts: { [fact.fact_id]: { ...fact, slots } } };
    const line = linesOf(area, meta, family.spec, held, LOOK).asked.find((one) => one.name === shortOf("park_proximity"));

    expect([line?.gauge, line?.figure, line?.known]).toEqual([undefined, fact.slots.value, "whole"]);
  });

  test("test_a_row_holds_no_fact_of_a_measure_and_says_its_name_whatever_facts_another_search_left", () => {
    // The ranking says that an area has a figure for a measure, and not where the area stands
    // on it: that is in the fact, which the page holds of the first five results alone.
    for (const area of family.ranked) {
      const lines = linesOf(area, meta, family.spec, aRow(family), LOOK).asked.filter((line) => line.thing.kind === "feature");
      expect(lines.map((line) => line.name)).toEqual([shortOf("park_proximity"), shortOf("school_primary_attainment")]);
      for (const line of lines) expect([line.gauge, line.figure]).toEqual([undefined, undefined]);
    }
  });

  test("test_the_small_drawing_of_a_line_is_the_drawing_of_its_chip_so_that_one_thing_is_drawn_one_way", () => {
    // The chip of a search and the line of a result stand on one page, a hand apart. What
    // a line asks the website for is what its chip asked for already, and nothing more:
    // so nothing that was asked for is told a second time by the pictures of a result.
    const asked = recordedAnswer("rank", "preview/example-5").body.data;
    const [area] = asked.ranked;
    if (area === undefined) throw new Error("The recording ranks nothing.");
    const ids = asked.spec.weights.filter((weight) => weight.provenance !== "default").map((weight) => weight.feature_id);
    const things = linesOf(area, meta, asked.spec, { facts: null, places: new Map() }, LOOK).asked.map((line) => line.thing);

    expect(ids).toEqual(["air_no2", "park_proximity"]);
    expect(things).toEqual(ids.map((id) => thingOfAChip({ kind: "feature", id }, meta)));
    expect(things.map(drawingOf)).toEqual(ids.map((id) => drawingOf(thingOfAChip({ kind: "feature", id }, meta))));
    // So it is of a journey and of a budget, each of which is drawn by what it is.
    const first = ranking("rank-first");
    const lines = linesOf(at(first, 0), meta, first.spec, aRow(first), LOOK).asked;
    expect(lines.map((line) => line.thing)).toEqual([thingOfAChip({ kind: "place", id: null }, meta), thingOfAChip({ kind: "budget", id: null }, meta)]);
    expect(lines.map((line) => line.thing)).toEqual([{ kind: "place" }, { kind: "budget" }]);
  });
});

describe("the vibes nobody asked for", () => {
  test("test_where_nothing_but_a_journey_or_a_budget_was_asked_for_a_result_shows_that_and_no_vibe_that_nobody_asked_for", () => {
    const money = ranking("rank-money-and-work");

    expect([money.spec.tags, money.spec.commutes.length, money.spec.budget.amount]).toEqual([[], 1, 1500]);
    expect(OTHERS_STAND).toBe("alone");
    for (const area of money.ranked) {
      const lines = linesOf(area, meta, money.spec, aRow(money), LOOK);
      expect(area.strip.length).toBeGreaterThan(0);
      expect(lines.marks).toEqual([]);
      expect(lines.asked.map((line) => line.thing.kind)).toEqual(["place", "budget"]);
    }
  });

  test("test_they_stand_on_a_result_only_where_nothing_at_all_was_asked_for", () => {
    const nothing = ranking("rank-default-rent");

    expect([nothing.spec.tags, nothing.spec.commutes, nothing.spec.budget.amount]).toEqual([[], [], null]);
    expect(nothing.spec.weights.every((weight) => weight.provenance === "default")).toBe(true);
    for (const area of nothing.ranked) {
      const lines = linesOf(area, meta, nothing.spec, aRow(nothing), LOOK);
      expect(lines.marks).toEqual(area.strip);
      expect(lines.asked).toEqual([]);
    }
    // One line of the look has them stand under what was asked for as well, and another on no result.
    const first = ranking("rank-first");
    const [area] = first.ranked;
    if (area === undefined) throw new Error("The recording ranks nothing.");
    expect(linesOf(area, meta, first.spec, aRow(first), LOOK).marks).toEqual(area.strip.filter((mark) => mark.asked));
    expect(linesOf(area, meta, first.spec, aRow(first), { ...LOOK, others: "beside" }).marks).toEqual(area.strip);
    for (const one of nothing.ranked) expect(linesOf(one, meta, nothing.spec, aRow(nothing), { ...LOOK, others: "never" }).marks).toEqual([]);
  });
});

describe("the column of names", () => {
  test("test_the_column_holds_the_name_of_every_line_that_a_result_of_the_ranking_draws", () => {
    const asked = ranking("rank-one-press");

    expect(columnOf(asked.ranked, meta, asked.spec, placesOf(asked), LOOK)).toEqual([
      meta.tags.find((tag) => tag.tag_id === "quiet_residential")?.label,
      shortOf("culture_venues_per_homes"),
      shortOf("park_proximity"),
      asked.places[0]?.name,
      BREAKDOWN.budget,
    ]);
  });
});

describe("an area that stands lower for what it lacks", () => {
  test("test_it_is_one_that_has_no_figure_for_a_thing_that_was_asked_for_and_never_one_that_lacks_what_nobody_chose", () => {
    const money = ranking("rank-money-and-work");
    const two = ranking("rank-two-journeys");

    // A measure that counts in every search has no figure in the third area: nobody asked for it.
    expect(at(money, 2).contributions.filter((part) => !part.present).map((part) => part.component)).toEqual(["feature:noise_exposure"]);
    expect(money.ranked.map((area) => standsLower(area, meta, money.spec))).toEqual(money.ranked.map(() => false));
    expect(standsLower(at(two, 0), meta, two.spec)).toBe(true);
    // Of two journeys one has no time, and the other still counts: the area lacks nothing the ranking holds against it.
    const one = ranking("rank-only-one");
    expect(standsLower(at(one, 0), meta, one.spec)).toBe(false);
  });
});

describe("no name is written into the lines", () => {
  test("test_the_lines_name_no_vibe_no_measure_and_no_place", () => {
    const written = readFileSync(path.join(__dirname, "lines.ts"), "utf8");
    const names = [
      ...areas.flatMap((area) => [area.name, area.slug]),
      ...meta.tags.flatMap((tag) => [tag.label, tag.tag_id]),
      ...meta.features.flatMap((feature) => [feature.short_label, feature.feature_id]),
    ].filter((name) => name.length > 3);

    expect(names.filter((name) => new RegExp(`["'\`]${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["'\`]`, "i").test(written))).toEqual([]);
  });
});
