/** @jest-environment node */
/**
 * The words of the website, read as one voice. They are written a file at a time, to one
 * guide, and a file does not read the next: so one thing came to have four names, and a
 * sentence that was true where it was written was untrue where it stood.
 *
 * These read every file of site copy, each line with its gaps filled, and hold what can be
 * held of one voice by a rule: that no line uses a word of the design, that one thing is
 * called by one name on every page, and that a sentence which is drawn in more states than
 * one is true of each of them. That a sentence reads well is for a person to judge.
 */

import { readdirSync } from "node:fs";
import path from "node:path";

import { ABOUT } from "./about";
import { ADDED } from "./added";
import { AREA, LOOK, PORTRAIT } from "./area";
import { BAND_ONE_WAY, RESTS_ON } from "./bands";
import { COMPARE, COMPARE_STATUS, COMPARE_TABLE, COUNTS_FOR, COUNTS_SAID } from "./compare";
import { CENSUS } from "./census";
import { FACT_COLUMNS } from "./facts";
import { INCOME } from "./income";
import { CRIME_RULE } from "./crime";
import { COMBINE, DIRECTION, POLARITY } from "./labels";
import { LEGEND, TABLE } from "./map";
import { METHODS } from "./methods";
import {
  CHIPS,
  COMPLETENESS,
  FILTERED,
  FIND_AREA,
  JOURNEYS,
  NOTICE,
  NOT_IN_DATA,
  PROMPT,
  REJECTED,
  REJECTED_PART,
  RESULTS,
  SEARCH,
  SHELF,
  STRIP,
  SUGGEST,
  UNRANKED,
} from "./search";
import { BRANDS, CRIME, FEATURES, HOLDS, KIND_OF_SEARCH, SETTINGS, SLIDER } from "./settings";
import { SHARE, SHARED } from "./share";
import { BANNER, PREVIEW_BANNER, SITE } from "./site";
import { TAKEN } from "./taken";
import { USUAL } from "./usual";
import { VIBES } from "./vibes";
import { DEEP, REFINE, WAYS } from "./ways";

/** A name that stands in a gap, where a line is filled with a name the API sent. */
const GAP = "Somewhere";
const OTHER = "Elsewhere";

/**
 * What a line with gaps is filled with. A line may take a name, a count, a list of names or
 * a record, in any order, so each is tried with every handful here, and what comes of it is
 * read wherever it is whole. What is tried with the wrong handful reads oddly, and is read
 * all the same: the words round the gap are the website's.
 */
const HANDFULS: readonly (readonly unknown[])[] = [
  [GAP, OTHER, "Another", "Last", "More"],
  [2, 3, 4, 5, 6],
  [1, 1, 1, 1, 1],
  [0, 0, 0, 0, 0],
  [[GAP, OTHER], [GAP], [GAP], [GAP]],
  [[GAP], [GAP]],
  [2, [GAP, OTHER], 3, "as the service says", { added: 1, skipped: 1 }],
  [1, [GAP], 0, null, { added: 0, skipped: 0 }],
  [2, GAP, "71", "as the service says"],
  [GAP, 35, true],
  [GAP, 35, false],
  [GAP, true],
  [GAP, false],
  [{ journeys: true, costs: true }],
  [{ journeys: false, costs: false }],
  [{ journeys: true, costs: false }],
  [{ journeys: false, costs: true }],
  [
    {
      fixed_minutes: 10,
      minutes_a_km: 4,
      near_the_underground_m: 800,
      minutes_a_km_near_the_underground: 3,
      within_by: 5,
      beyond_by: 10,
    },
  ],
  [3, -2],
  [60, 60],
  [40, 60],
  [0, 60],
];

/** Every line of every file of site copy, each with where it stands. */
function everyLine(): [where: string, words: string][] {
  const found: [string, string][] = [];
  const seen = new Set<string>();
  const keep = (where: string, words: string) => {
    // What came of the wrong handful and is not whole is no line of the website.
    if (/undefined|NaN|\[object/.test(words)) return;
    const key = `${where}\n${words}`;
    if (seen.has(key)) return;
    seen.add(key);
    found.push([where, words]);
  };
  const walk = (where: string, value: unknown) => {
    if (typeof value === "string") keep(where, value);
    else if (typeof value === "function") {
      for (const handful of HANDFULS) {
        try {
          const said: unknown = (value as (...gaps: unknown[]) => unknown)(...handful);
          if (typeof said === "string") keep(where, said);
          else if (Array.isArray(said)) {
            said.forEach((one, at) => {
              if (typeof one === "string") keep(`${where}[${at}]`, one);
            });
          }
        } catch {
          // What reads a record of the service is no line of words, and a name breaks it.
          continue;
        }
      }
    } else if (Array.isArray(value)) value.forEach((one, at) => walk(`${where}[${at}]`, one));
    else if (typeof value === "object" && value !== null) {
      for (const [key, one] of Object.entries(value)) walk(`${where}.${key}`, one);
    }
  };
  const files = readdirSync(__dirname)
    .filter((name) => /\.ts$/.test(name) && !/\.test\.ts$/.test(name))
    .sort();
  for (const file of files) {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    walk(file.replace(/\.ts$/, ""), require(path.join(__dirname, file)));
  }
  return found;
}

const copy = everyLine();

/** The lines that stand at a place, or under it. */
const at = (...places: readonly string[]) =>
  copy.filter(([where]) => places.some((place) => where === place || where.startsWith(`${place}.`) || where.startsWith(`${place}[`)));

/** Where the lines stand that a rule finds, each once. */
const places = (lines: readonly (readonly [string, string])[]) => [...new Set(lines.map(([where]) => where))];

/**
 * The sentences of the service that the website fills in for it, word for word as the
 * contract writes them. They are the service's, and are written again with the service.
 */
const OF_THE_SERVICE = /^(templates\.|crime\.(countsOf|crimeParts|crimeVibes|ruleIn|askingFor))/;

/**
 * Names that are kept for the tests of others and drawn by no page, and the lines that
 * choose between two ways a thing was built, which are no words of the website.
 */
const DRAWN_BY_NOTHING = /^(compare\.COUNTS_SAID|area\.OPENS_SAYS)\b/;

const ours = copy.filter(([where]) => !OF_THE_SERVICE.test(where) && !DRAWN_BY_NOTHING.test(where));

describe("every line of site copy", () => {
  test("test_every_file_of_site_copy_is_read_with_its_gaps_filled", () => {
    expect(new Set(copy.map(([where]) => where.split(".")[0])).size).toBeGreaterThanOrEqual(25);
    expect(copy.length).toBeGreaterThan(1500);
    expect(copy.filter(([, words]) => words.includes(GAP)).length).toBeGreaterThan(200);
  });

  test("test_no_line_says_this_data_a_release_a_recipe_or_counted_from", () => {
    // Each said nothing to somebody who had not read the design. What Burro has is
    // "Burro's data", and which data a page was built on is "a version of the data".
    const design = /\bthis data\b|\breleases?\b|\brecipes?\b|\bcounted from\b|\bhundredths\b|\bfor want of\b|\bin hand\b/i;

    expect(places(ours.filter(([, words]) => design.test(words)))).toEqual([]);
  });

  test("test_a_part_is_a_part_of_a_page_or_of_a_drawing_and_never_of_a_vibe", () => {
    // What a vibe is worked out from is its measurements. A page, a town, a link and an
    // estimate have parts, as they have in any other sentence, and each is named here.
    const parts = /\bparts?\b/i;
    const plain = new Set([
      // A part of the page, which an arrow marks.
      "about.ABOUT.key.result.arrow",
      // A part of the drawing of a town: its trees, its buildings, its windows and its roofs.
      "town.TOWN.leftBlank",
      "town.TOWN.whyBlank.unknown",
      "town.TOWN.whyBlank.crime",
      "town.TOWN.key.notYet",
      "town.TOWN.key.countsCrime",
      "town.TOWN.key.blank",
      // A part of a link, which was lost on its way.
      "share.SHARED.none.text",
      "share.SHARED.notOne.text",
    ]);
    const found = places(ours.filter(([, words]) => parts.test(words))).filter(
      (where) => !plain.has(where.replace(/\[\d+\]$/, "")),
    );

    expect(found).toEqual([]);
  });

  test("test_a_figure_is_based_on_what_it_was_worked_out_from_and_rests_on_nothing", () => {
    expect(places(ours.filter(([, words]) => /\brests? on\b|\brested on\b/i.test(words)))).toEqual([]);
    expect(METHODS.confidence.rows.unstated).toMatch(/how many sales the figure is based on/);
    expect(COMPLETENESS.some(9, 10)).toMatch(/is based on 9 of the 10/);
  });

  test("test_what_needs_javascript_says_javascript_and_never_scripts", () => {
    // The privacy line of the methods names a script from anyone else, which is what it is.
    const said = ours.filter(([where, words]) => /\bscripts?\b/i.test(words) && where !== "methods.METHODS.words.points[4]");

    expect(places(said)).toEqual([]);
    for (const words of [COMPARE.needsScripts, CENSUS.noScript, INCOME.noScript]) expect(words).toMatch(/JavaScript/);
  });

  test("test_nothing_is_better_or_worse_and_no_line_gives_a_verdict", () => {
    // "A good deal" is how much, and is said of how the homes of an area differ.
    const verdict =
      /\b(best|worst|worse|good(?! deal\b)|bad|badly|nice|lovely|desirable|popular|sought|safe|safer|unsafe|dangerous|rough|up and coming|affluent|deprived|posh)\b/i;
    // "Better" is said only to say that nothing is: neither end of a scale, and no area.
    const better = ours.filter(([, words]) => /\bbetter\b/i.test(words) && !/\b(not|neither|no)\b[^.]*\bbetter\b/i.test(words));
    // "The best" is said once, to say that Burro calls no area so. An example is what a
    // person might type, in their words and not in Burro's.
    const allowed = (where: string) => where === "methods.METHODS.account.wont.before" || /^search\.EXAMPLE/.test(where);

    expect(places(ours.filter(([where, words]) => verdict.test(words) && !allowed(where)))).toEqual([]);
    expect(places(better)).toEqual([]);
    expect(METHODS.account.wont.before).toMatch(/It does not call any area the best/);
  });

  test("test_every_line_is_plain_with_straight_quotation_marks_and_nothing_the_face_lacks", () => {
    // Two files wrote curly quotation marks where every other wrote straight ones.
    const drawn = ours.filter(([, words]) => /[^\x20-\x7e£·]/.test(words));
    const loud = ours.filter(([, words]) => /!|\p{Extended_Pictographic}/u.test(words));

    expect([places(drawn), places(loud)]).toEqual([[], []]);
  });
});

describe("one thing is called by one name", () => {
  test("test_what_a_person_tells_burro_is_what_is_important_in_their_space_wherever_it_is_said", () => {
    // The founder: "Change describe the life you want to - tell me whats important in your
    // space". The label of the box was changed. The sentence under the heading of the first
    // page, and what a search engine and a shared link show of the website, said it still.
    expect(places(ours.filter(([, words]) => /\bthe life you want\b/i.test(words)))).toEqual([]);
    expect(PROMPT.label).toBe("Tell me what's important in your space");
    for (const words of [SEARCH.lead, SEARCH.leadNoJourneys, SITE.description]) {
      expect(words).toContain("Tell Burro what's important in your space");
    }
    // Who Burro is for is said first, and places to reach only where the data names some.
    for (const words of [SEARCH.lead, SEARCH.leadNoJourneys, SITE.description]) expect(words.startsWith(SEARCH.forWhom)).toBe(true);
    expect(SEARCH.leadNoJourneys).not.toMatch(/\breach\b/);
  });

  test("test_the_settings_are_space_requirements_wherever_a_visitor_reads_of_them", () => {
    // The founder named the settings "Space requirements". The sentence over them and the
    // button under them called them the settings still, and so did the methods, the key
    // and the page of an area. What an account holds of itself is another thing, and is
    // a setting of the account.
    const ofAnAccount = (where: string) => where.startsWith("account.");
    const said = ours.filter(([where, words]) => /\bsettings?\b/i.test(words) && !ofAnAccount(where));

    expect(places(said)).toEqual([]);
    expect(SETTINGS.title).toBe("Space requirements");
    expect(SETTINGS.rank).toBe("Search with these requirements");
    // A line that sends a person to them names them as they name themselves.
    for (const words of [
      CRIME_RULE,
      DEEP.lead,
      METHODS.limits.lead,
      METHODS.journeys.points[1],
      METHODS.journeys.points[5],
      VIBES.facts.family,
      ...Object.values(COUNTS_FOR).map((one) => one.means),
    ]) {
      expect(words).toContain(`under ${SETTINGS.title}`);
    }
    // Once a search is open they stand under the fold that refines it, and the line names both.
    for (const words of [PROMPT.emptyOpen, ADDED.nothingNew, ADDED.changed, ADDED.changedToo]) {
      expect(words).toMatch(new RegExp(`or change your space requirements under ${REFINE.label}\\.$`));
    }
    expect(DEEP.lead).toContain(`press "${SETTINGS.rank}"`);
    // What a group of them holds is said of the things in it, and what a link holds of the search.
    expect(BRANDS.lead).toMatch(/^The things in this group are about\b/);
    expect(CRIME.lead).toMatch(/Each thing here is a count of what was reported/);
    expect(SHARE.stored).toBe("What the link holds of the search");
    expect(SHARED.holds).toMatch(/^A shared link holds what was chosen in a search, and not what was typed to make it\./);
  });

  test("test_what_nobody_chose_is_what_burro_counts_in_every_search_wherever_it_is_said", () => {
    // It had two names: "usual settings" on a result, in a comparison and in the methods,
    // and "counted in every search" on the bar of the group that holds each.
    expect(USUAL.onTheBar(GAP)).toBe(`Counted in every search: ${GAP}`);
    expect(COMPLETENESS.usual(1)).toBe(`One of them is counted in every search. You can see and change it under ${REFINE.label}.`);
    expect(COMPLETENESS.usual(6)).toBe(`6 of them are counted in every search. You can see and change them under ${REFINE.label}.`);
    // On a result it takes no more room than the line it takes the place of.
    expect(COMPLETENESS.usual(6).length).toBeLessThanOrEqual("6 of them are Burro's usual settings, which you can see and change under Refine search.".length);
    for (const words of Object.values(COMPARE.fromDefaults)) expect(words).toMatch(/\bby the things it counts in every search\b/);
    expect(METHODS.ranking.points[1]).toMatch(/\bThe things Burro counts in every search still count\b/);
    expect(METHODS.defaults.lead).toMatch(/\bwhich Burro counts in every search\b/);
    expect(METHODS.defaults.columns.setting).toBe("What counts");
    expect(places(ours.filter(([, words]) => /\busual\b/i.test(words)))).toEqual([]);
  });

  test("test_a_search_is_to_rent_to_buy_or_to_visit_wherever_the_choice_is_named", () => {
    // A visit is the third kind of search. The key to the drawings, and two lines that say
    // why a change was not made, still named the choice as one of two.
    const ofTwo = ours.filter(([, words]) => /\brenting or buying\b|\brent or buy\b/i.test(words));

    expect(places(ofTwo)).toEqual([]);
    expect(KIND_OF_SEARCH.legend).toBe("Renting, buying or visiting");
    expect(REJECTED_PART.tenure).toBe(KIND_OF_SEARCH.legend);
    expect(ABOUT.key.things.kinds.tenure).toBe("Whether you are renting, buying or visiting");
    expect(REJECTED.segment_not_for_tenure).toMatch(/the choice of renting, buying or visiting\.$/);
  });

  test("test_what_burro_ranks_is_an_area_and_never_a_neighbourhood", () => {
    // How an area comes by its name is the one place a neighbourhood is spoken of: there it
    // is another thing, the named place that an area takes its name from.
    const said = ours.filter(([where, words]) => /\bneighbou?rhoods?\b/i.test(words) && !where.startsWith("methods.METHODS.names."));

    expect(places(said)).toEqual([]);
    expect(SITE.description).toMatch(/rank the areas/);
    expect(FIND_AREA.hint).toMatch(/a district or an area\./);
    expect(FIND_AREA.hintAlone).toMatch(/^Type the name of an area\b/);
  });

  test("test_what_is_asked_of_an_area_is_asked_of_the_area_and_a_place_is_a_place_to_reach", () => {
    // "A place" is what a person needs to reach: a station, a workplace, a school. What is
    // ranked is an area, so what is asked of it, and what is measured of it, is of the area.
    const ofThePlace = /\b(asked of|judgement of) the place\b|\bthe place (itself|counted)\b|\bwho lives in a place\b/;

    expect(places(ours.filter(([, words]) => ofThePlace.test(words)))).toEqual([]);
    expect(CHIPS.leadsHint).toMatch(/what you asked of the area itself/);
    expect(AREA.alike.lead).toMatch(/Burro compares nothing about who lives in an area\.$/);
    // What Burro promises of itself is kept in the words it was promised in.
    expect(METHODS.ranking.points[5]).toMatch(/^Burro ranks places by what is there\./);
  });

  test("test_what_a_vibe_is_worked_out_from_is_what_goes_into_it_on_every_page", () => {
    // It had four names: "What goes into it", "What it is made of", "Its measurements" and
    // "What Leafy is made of".
    const name = "What goes into it";

    expect([SHELF.recipe, VIBES.recipe.title, FEATURES.madeOf]).toEqual([name, name, name]);
    expect(FEATURES.madeOfName(GAP)).toBe(`${GAP}: what goes into it`);
    expect(NOT_IN_DATA.more).toBe("See what goes into each vibe");
    expect(VIBES.recipe.caption(GAP)).toBe(`What goes into ${GAP}`);
    // The heading on the page of an area says the same, and is not the button that opened it.
    expect(PORTRAIT.madeOf.title).toBe("The measurements that go into it");
    expect(places(ours.filter(([, words]) => /\bmade of\b|^Its measurements$/i.test(words)))).toEqual([
      // What the households of an area were made of, at the census: it is said of people.
      "methods.METHODS.ranking.points[5]",
    ]);
  });

  test("test_what_a_vibe_cannot_tell_is_what_it_cannot_see_on_every_page", () => {
    const name = "What it cannot see";

    expect([SHELF.cannotSee, VIBES.cannotSee.title]).toEqual([name, name]);
    expect(LOOK.cannotSeeEach).toBe("What each vibe cannot see");
    expect(PORTRAIT.madeOf.about(GAP)).toMatch(/what it cannot see$/);
    // The founder's own sentence, at the head of the page of vibes, is kept as it was given.
    expect(places(ours.filter(([, words]) => /\bleaves out\b/.test(words) && /\bvibe\b|\bit leaves out\b/.test(words)))).toEqual([
      "vibes.VIBES.lead",
      "vibes.VIBES.leadAsWritten",
    ]);
  });

  test("test_a_vibe_is_worked_out_for_an_area_and_an_area_is_never_placed_on_one", () => {
    // "Burro could not work out 1 of the 14 vibes" is the founder's own sentence. An area is
    // placed in a band, which is plain, and never on a vibe.
    const placed =
      /\b(cannot|could not|can) place\b|\bplaced? (an|any|the|it) (area )?(on|from)\b|\bplaced on\b|\bnot placed\b|\bcannot be placed\b|\bplaces an area\b|\bto place an area\b/i;

    expect(places(ours.filter(([, words]) => placed.test(words)))).toEqual([]);
    expect([TABLE.notPlaced, COMPARE_TABLE.character.notPlaced]).toEqual(["Not worked out", "Not worked out"]);
    expect(VIBES.how.title).toBe("How Burro works out a vibe for an area");
    expect(PORTRAIT.lead).toMatch(/places it in one of five bands/);
  });

  test("test_how_much_a_thing_counts_is_said_in_a_comparison_in_words_that_say_what_the_figure_is", () => {
    // The settings and the working of a result say "how much it counts". A comparison names
    // the figure a weight, or says it as they do: it was built both ways, and one line chooses.
    expect(Object.keys(COUNTS_FOR)).toEqual(["weight", "counts"]);
    expect(COUNTS_FOR.weight.says(50)).toBe("Weight 50");
    expect(COUNTS_FOR.counts.says(50)).toBe("Counts 50 of 100");
    expect(COMPARE_TABLE.countsFor(50)).toBe(COUNTS_FOR[COUNTS_SAID].says(50));
    expect(COMPARE_TABLE.weights).toBe(COUNTS_FOR[COUNTS_SAID].means);
    expect(FEATURES.weight(GAP)).toBe(`How much it counts: ${GAP}`);
    for (const { means } of Object.values(COUNTS_FOR)) {
      // Whichever is chosen, the line says what the figure is, in the words of the settings,
      // that it is no share of a whole, and nothing of who set it: it is said with no search open too.
      expect(means).toMatch(/how much it counts, from 0 to 100/);
      expect(means).toMatch(/where its slider stands under Space requirements/);
      expect(means).toMatch(/not shares of a whole, so they do not add up to 100\.$/);
      expect(means).not.toMatch(/\byour search\b|\byou set\b/);
    }
    // A weight is named where it is said what a weight is, and nowhere else in a comparison.
    const named = at("compare").filter(
      ([where, words]) => /\bweights?\b/i.test(words) && !/^compare\.(COUNTS_FOR\.weight|COUNTS_SAID)\b/.test(where),
    );
    expect(places(named)).toEqual(COUNTS_SAID === "weight" ? ["compare.COMPARE_TABLE.countsFor", "compare.COMPARE_TABLE.weights"] : []);
  });

  test("test_which_way_a_figure_counts_says_what_follows_for_the_ranking", () => {
    // "A higher figure counts as better" stood under "More older residents".
    expect(POLARITY).toEqual({
      more: "A higher figure ranks an area higher",
      less: "A lower figure ranks an area higher",
      either: "You choose whether a higher or a lower figure ranks an area higher",
    });
    expect(DIRECTION).toEqual({ more: "A higher figure ranks higher", less: "A lower figure ranks higher" });
    expect(FEATURES.direction(GAP)).toBe(`Which way it counts: ${GAP}`);
    expect(METHODS.features.columns.polarity).toBe(PORTRAIT.madeOf.reading);
  });

  test("test_the_journey_that_counts_is_the_one_that_does_least_well_wherever_it_is_said", () => {
    const said = [COMBINE.slowest, JOURNEYS.usesOne(GAP), JOURNEYS.usesMean, METHODS.journeys.points[5]];

    for (const words of said) expect(words).toMatch(/does least well against (its|its own|the) limit/);
  });

  test("test_the_pin_the_dots_and_the_lines_of_the_map_are_said_as_the_key_says_them", () => {
    expect(LEGEND.pin).toBe(ABOUT.key.map.pin);
    expect(LEGEND.unranked).toBe("Dots mean that Burro could not rank the area.");
    expect(ABOUT.key.map.dots.startsWith(LEGEND.unranked.replace(/\.$/, ""))).toBe(true);
    expect(ABOUT.key.map.lines.startsWith(LEGEND.filtered.replace(/\.$/, ""))).toBe(true);
    // Under the map each is one line, where the box of the map must stand whole in a window:
    // measured at 1440 by 900, a line of the legend holds some sixty letters.
    for (const words of [LEGEND.notPlaced, LEGEND.filtered, LEGEND.unranked]) expect(words.length).toBeLessThanOrEqual(56);
    // Each is a sentence: "Could not be ranked. Shown with dots." was two fragments.
    for (const words of [LEGEND.notPlaced, LEGEND.filtered, LEGEND.unranked, LEGEND.pin]) {
      expect(words).toMatch(/^[A-Z][^.]*\.$/);
    }
  });

  test("test_which_data_a_page_was_built_on_is_a_version_at_the_foot_of_a_page_a_list_and_the_methods", () => {
    expect(SITE.footer).toEqual({ release: "Version of the data", engine: "Version of the ranking" });
    expect(RESULTS.foot).toEqual(SITE.footer);
    expect(METHODS.release.rows.release).toBe(SITE.footer.release);
    expect(METHODS.release.rows.engine).toBe(SITE.footer.engine);
    expect(SHARED.madeOn).toMatch(/version of the data:$/);
    expect([BANNER.label, PREVIEW_BANNER.label]).toEqual(["About the data", "About this preview"]);
  });

  test("test_which_way_the_bands_run_is_said_in_words_that_read_alone_and_after_a_band", () => {
    expect(STRIP.from("least", "most")).toBe("from least to most");
    expect(`${STRIP.band(4)}, ${STRIP.from("Calm", "Buzzy")}`).toBe("band 4 of 5, from Calm to Buzzy");
    // A mixed area sits between two bands, as the page of an area says it.
    expect(`${STRIP.bands(2, 4)}, ${STRIP.from("Newer", "Historic")}`).toBe(
      "varies within this area, between band 2 and band 4 of 5, from Newer to Historic",
    );
    expect(FACT_COLUMNS.bands).toMatch(/between bands$/);
  });

  test("test_where_an_area_sits_is_said_of_it_among_the_areas_and_never_here", () => {
    // "around the middle here" was read as the middle of the area.
    expect(BAND_ONE_WAY).toEqual({
      1: "among the least",
      2: "on the low side",
      3: "around the middle",
      4: "on the high side",
      5: "among the most",
    });
    expect(ABOUT.band.states.oneWay).toMatch(/among all the areas that were compared/);
    expect(ABOUT.band.states.oneWay).not.toMatch(/\bhere\b/);
    expect(ABOUT.band.states.oneWay).toContain(`"${BAND_ONE_WAY[3]}"`);
  });

  test("test_what_a_band_was_worked_out_from_is_so_many_of_its_measurements", () => {
    expect(RESTS_ON.short("2", "3")).toBe("from 2 of its 3 measurements");
    expect(RESTS_ON.full("2", "3")).toMatch(/^Burro worked this out from 2 of the 3 measurements that go into the vibe\./);
    // What is not known is said to be not known, and nothing is filled in.
    expect(RESTS_ON.full("2", "3")).toMatch(/It has no figure for the rest in this area, and it fills nothing in for them\.$/);
    expect(`${RESTS_ON.without}: ${RESTS_ON.waits(GAP)}`).toBe(
      `Burro has no figure for: ${GAP}, which it does not have for any area yet`,
    );
  });
});

describe("what Burro does with a sentence is said as it is done", () => {
  test("test_no_line_a_visitor_reads_speaks_of_choosing_what_to_add_of_an_offer_or_of_a_question_burro_asks", () => {
    // The methods said that Burro applies none of a sentence and that the person chooses
    // what to add, and the key that Burro asks and adds nothing until a person chooses.
    // The website takes what it read and asks nothing.
    const asks =
      /\bchoose what to add\b|\bapplies none of it\b|\bshows what it noticed\b|\badds nothing to your search\b|\buntil you choose\b|\bonly when you press it\b|\basks you a question\b|\basks when it is not sure\b|\bhas a question about\b|\bleft for you to decide\b|\bleft to choose\b/i;

    expect(places(ours.filter(([, words]) => asks.test(words)))).toEqual([]);
    // The rule bites: what stood over the offers, and what the line said of a question, are found by it.
    expect(["Choose what to add", "Burro has a question about a place."].filter((words) => asks.test(words))).toHaveLength(2);
  });

  test("test_the_methods_say_that_burro_adds_what_it_read_and_that_each_thing_is_a_chip_that_can_be_taken_off", () => {
    expect(METHODS.ranking.points).toContain(TAKEN.does);
    expect(TAKEN.does).toMatch(/^Burro reads what you type and adds what it understood to your search straight away\b/);
    expect(TAKEN.does).toMatch(/\bwithout asking\b/);
    // A chip is said to be what it is where it is first spoken of.
    expect(TAKEN.does).toMatch(/\bunder the search box as a chip, which is a small label with a cross on it\b/);
    expect(TAKEN.does).toMatch(/\btake any chip off again\b/);
  });

  test("test_the_methods_name_the_two_things_that_are_never_taken_for_a_person_with_the_one_rule_and_why", () => {
    expect(METHODS.ranking.points).toContain(TAKEN.never);
    expect(TAKEN.never).toMatch(/\brecorded crime, and anything that counts who lived in an area\b/);
    expect(TAKEN.never).toMatch(/\bunless you choose them yourself\b/);
    // When recorded crime counts is said by the one rule, word for word.
    expect(TAKEN.never).toContain(CRIME_RULE);
    // Where Burro says that it left one out, and why it leaves both to the person.
    // The line stands under the box and over what was understood.
    expect(TAKEN.never).toMatch(/\bnames it in a line under the search box\b/);
    expect(TAKEN.never).toMatch(/\bbecause it gives no verdict on an area or on the people who live in it\b/);
    // What Burro does is said first, and what it never does after it.
    const at = (words: string) => METHODS.ranking.points.findIndex((point) => point === words);
    expect(at(TAKEN.never)).toBe(at(TAKEN.does) + 1);
  });

  test("test_the_key_says_the_same_beside_the_cross_of_a_chip_and_the_band_of_a_note", () => {
    expect(ABOUT.key.things.cross).toMatch(/^Burro adds what it understood of your words to your search without asking you first\b/);
    expect(ABOUT.key.things.cross).toMatch(/\bas a chip with a cross on it\b/);
    expect(ABOUT.key.things.cross).toMatch(/\bThe cross takes that thing out of your search again\b/);
    expect(ABOUT.key.result.notice).toMatch(/\bthe line that names what it left out of your search\.$/);
    // What is never taken, and why, in the words the methods say them in.
    for (const sentence of ABOUT.key.result.never.split(/(?<=\.)\s+/)) expect(TAKEN.never).toContain(sentence);
    expect(ABOUT.key.result.never).toMatch(/\brecorded crime, and anything that counts who lived in an area\b/);
    expect(ABOUT.key.result.never).toMatch(/\bbecause it gives no verdict\b/);
  });

  test("test_a_carrot_is_said_to_lie_beside_the_choice_in_hand_of_a_list_which_is_where_it_is_drawn", () => {
    // It was said to point at the answer to a question. It lies beside an example and
    // beside a place that matches, and nothing else draws it.
    expect(ABOUT.key.result.carrot).toMatch(/^A carrot lies beside the choice you are on in a list\b/);
    expect(ABOUT.key.result.carrot).toMatch(/\bthe examples under the search box\b/);
    expect(ABOUT.key.result.carrot).toMatch(/\bthe places that match a name you typed\b/);
    expect(ABOUT.key.result.carrot).not.toMatch(/\bquestion|\basks?\b|\banswer\b/i);
  });
});

describe("a sentence that is drawn in more states than one is true of each", () => {
  test("test_what_stands_beside_the_words_that_were_not_read_is_true_of_some_and_of_all", () => {
    // It is drawn where nothing was read too: "Some of your words were not read" stood
    // under "Nothing in that could be read".
    expect(SUGGEST.unread).not.toMatch(/\b(some|part|a few|all|none|nothing)\b/i);
    expect(SUGGEST.unread).toMatch(/the words it did not read/);
    expect(NOTICE.nothingRead).toMatch(/^Burro could not read anything in what you typed\./);
    // It gives a sentence that Burro reads, in quotation marks: which sentence, a test of the search page holds.
    expect(NOTICE.nothingRead).toMatch(/\bsuch as "[a-z][^"]+"\./);
  });

  test("test_a_line_that_sends_a_person_to_the_settings_names_what_holds_them", () => {
    // "Use the settings" named nothing that can be pressed. After a search they are under
    // the part that refines it, and before one they are the second way in.
    const loose = ours.filter(([, words]) => /\buse the settings\b|\bin Settings\b/i.test(words));

    expect(places(loose)).toEqual([]);
    for (const words of [NOTICE.nothingRead, NOTICE.degraded, NOTICE.partUnread]) {
      expect(words).toContain(`under ${REFINE.label}`);
    }
    expect(at("ways.UNREAD.before").map(([, words]) => words.includes(WAYS.deep))).toEqual([true]);
  });

  test("test_the_minutes_of_a_journey_are_said_on_a_chip_without_a_word_that_makes_them_firm", () => {
    // "Within" is one of the words Burro reads as a firm limit. It stood on the chip of a
    // limit that was flexible, beside a bar that said "ideally within".
    expect(CHIPS.within(35)).toBe("35 minutes");
    expect([CHIPS.firm, CHIPS.flexible]).toEqual(["firm limit", "flexible"]);
    expect(HOLDS.journey(GAP, 35, false)).toBe(`${GAP}, ideally within 35 minutes`);
    expect(HOLDS.journey(GAP, 35, true)).toBe(`${GAP} within 35 minutes`);
  });

  test("test_what_a_fit_is_based_on_is_a_sentence_wherever_it_stands", () => {
    // It stands under a fit, in a row of the table and after the name of a pin.
    expect(COMPLETENESS.all).toBe("This fit is based on everything that counts in your search.");
    expect(COMPLETENESS.some(9, 10)).toBe("This fit is based on 9 of the 10 things that count in your search.");
    // What counts is not all that was asked for: what nobody chose counts too.
    expect(COMPLETENESS.some(9, 10)).not.toMatch(/asked/);
  });

  test("test_what_0_and_100_mean_names_what_it_speaks_of_wherever_it_stands", () => {
    // It may stand before the first slider of its group: "The scale" and "it" were of nothing yet.
    expect(SLIDER.range).toMatch(/^Each slider here runs from 0 to 100\./);
    expect(SLIDER.range).toMatch(/At 0 the thing does not count at all, and at 100 it counts as much as anything can\.$/);
  });

  test("test_where_a_slider_of_two_ends_stands_is_not_said_twice", () => {
    // "In the middle: it does not count" stood directly over "In the middle this does not count at all".
    expect(SLIDER.middle).toBe("In the middle");
    expect(SLIDER.twoEnds).toMatch(/^While it is in the middle, this does not count at all\./);
    expect(SLIDER.towards("Buzzy", 40)).toBe("Towards Buzzy, 40 of 100");
  });

  test("test_why_an_area_has_no_rank_is_a_label_that_a_list_and_a_count_can_take", () => {
    // Each stands before a full stop of the table's own, and beside a count of areas.
    for (const words of [...Object.values(UNRANKED), FILTERED.excluded, FILTERED.not_selected, FILTERED.over_budget, FILTERED.commute_cap]) {
      expect(words).not.toMatch(/\.$/);
      expect(words).not.toMatch(/\bthis area\b/);
    }
    expect(UNRANKED.not_rankable).toBe("Not ranked by Burro");
  });

  test("test_in_a_comparison_whether_an_area_is_ranked_is_a_sentence_and_speaks_of_no_search", () => {
    // It is said with a search open and with none.
    for (const words of Object.values(COMPARE_STATUS)) {
      expect(words).toMatch(/^[A-Z].*\.$/);
      expect(words).not.toMatch(/\byour search\b/);
    }
    // What the service says of an estimate is kept word for word.
    expect(COMPARE_STATUS.commute_likely_beyond.endsWith(JOURNEYS.estimatedFrom)).toBe(true);
    expect(FILTERED.commute_likely_beyond.endsWith(JOURNEYS.estimatedFrom)).toBe(true);
    // What is put after it keeps its own full stop.
    expect(COMPARE_TABLE.basedOn(9, 10)).not.toMatch(/\.$/);
  });

  test("test_why_a_change_was_not_made_says_what_burro_does_and_blames_nothing", () => {
    expect(REJECTED.unknown_place).toBe("Burro does not know that place.");
    expect(REJECTED.unknown_area).toBe("Burro does not cover that area.");
    expect(REJECTED.nothing_to_change).toBe("Your search already says that.");
    for (const [reason, words] of Object.entries(REJECTED)) {
      expect([reason, /\.$/.test(words)]).toEqual([reason, true]);
    }
  });
});

describe("what is said of an area, of what is typed and of what is not known", () => {
  test("test_a_measurement_burro_lacks_is_said_to_be_lacking_and_is_never_filled_in", () => {
    expect(AREA.features.noFigure).toBe("Burro has no figure for this area.");
    expect(PORTRAIT.madeOf.waits).toBe("Burro does not have this measurement yet.");
    expect(VIBES.recipe.waits).toBe("Burro does not have it yet");
    expect(VIBES.held(0, 60)).toMatch(/^Burro has none of these measurements yet, so it cannot work this vibe out for any area\./);
    expect(VIBES.held(40, 60)).toMatch(/so it cannot work this vibe out for any area yet\.$/);
    expect(VIBES.held(70, 60)).toMatch(/carry 70 of the 100 shares, which is enough to work the vibe out/);
    expect(SHELF.held(0, 60)).toMatch(/count for 60 of 100 in it/);
    expect(SHELF.held(40, 60)).toMatch(/count for 40 of 100 in it, and it needs 60 of 100/);
    // How much of a vibe a measurement makes up is said one way, in a card and in a notice.
    expect(`${SHELF.share(40)} ${GAP}`).toBe(`Counts for 40 of 100: ${GAP}`);
    expect(NOT_IN_DATA.part(GAP, 40)).toBe(`${GAP}, which counts for 40 of 100 in it`);
  });

  test("test_how_much_of_a_vibe_an_area_needs_is_the_figure_of_the_method", () => {
    expect(VIBES.how.points[2]).toMatch(/carry 60 of the 100 shares/);
    expect(VIBES.how.points[2]).toMatch(/never puts it in the middle as a guess\.$/);
  });

  test("test_whose_choice_the_make_up_of_a_vibe_is_is_still_said", () => {
    // "The recipe is Burro's own, and the weights are a judgement."
    expect(VIBES.how.points[5]).toMatch(/that choice is a judgement\./);
    expect(VIBES.how.points[5]).toMatch(/No language model writes or scores a vibe\.$/);
  });
});
