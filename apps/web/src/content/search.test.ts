/** @jest-environment node */
/**
 * The words of a result, of its working, of a failure and of what Burro cannot answer are
 * read by somebody who is choosing where to live and has never seen Burro. These hold what
 * can be held of that by a rule, and what each line must go on saying however it is put:
 * a figure, a source, what is not known, and what Burro does not do.
 *
 * They hold the lines of `search.ts` that are named here, and no other. The line under the
 * box, the chips, the offers and the question of a place have tests beside the parts that
 * draw them.
 */

import { recordedAnswer } from "@/lib/api/recorded";

import { AREA } from "./area";
import { COMPARE_TABLE } from "./compare";
import { FACT_COLUMNS } from "./facts";
import {
  APART,
  BREAKDOWN,
  COMPLETENESS,
  CONFIDENCE,
  COST,
  FAILURE,
  FILTERED,
  JOURNEYS,
  LOCATOR,
  NOTICE,
  REJECTED_LABEL,
  RESULTS,
  SOURCE,
  STRIP,
  UNMET,
  UNMET_LABEL,
  UNTESTED,
} from "./search";
import { JOURNEY } from "./settings";
import { SITE } from "./site";
import { REFINE } from "./ways";

/** A name that stands in a gap, where a line is filled with a name the API sent. */
const GAP = "Somewhere";
const OTHER = "Elsewhere";

/** Every line held here, with where it stands. A line with a gap is filled as a page fills it. */
const copy: readonly (readonly [where: string, words: string])[] = [
  ...Object.entries(NOTICE)
    .filter(([key]) => !["degraded", "refused", "nothingRead", "nothingChanged", "partUnread", "partShown", "partNotFound"].includes(key))
    .flatMap(([key, words]): [string, string][] =>
      typeof words === "string" ? [[`NOTICE.${key}`, words]] : [],
    ),
  ["NOTICE.takeOut", NOTICE.takeOut(GAP)],
  ["NOTICE.takeOut, of a place", NOTICE.takeOut(NOTICE.thePlace)],
  ...Object.entries(FAILURE).map(([key, words]): [string, string] => [`FAILURE.${key}`, words]),
  ...Object.entries(UNMET).map(([key, words]): [string, string] => [`UNMET.${key}`, words]),
  ["UNMET_LABEL", UNMET_LABEL],
  ["REJECTED_LABEL", REJECTED_LABEL],
  ["APART.title, of one", APART.title(1)],
  ["APART.title, of many", APART.title(3)],
  ["APART.label", APART.label],
  ["APART.lead", APART.lead],
  ["APART.lacks", APART.lacks],
  ...Object.entries(UNTESTED).map(([key, words]): [string, string] => [`UNTESTED.${key}`, words]),
  ["RESULTS.listLabel", RESULTS.listLabel],
  ["RESULTS.restLabel", RESULTS.restLabel],
  ["RESULTS.firstFive", RESULTS.firstFive],
  ["RESULTS.waiting", RESULTS.waiting],
  ["RESULTS.showMore, of one", RESULTS.showMore(1)],
  ["RESULTS.showMore, of many", RESULTS.showMore(11)],
  ["RESULTS.listed", RESULTS.listed(10, 21)],
  ["RESULTS.showWorking", RESULTS.showWorking],
  ["RESULTS.workingOf", RESULTS.workingOf(GAP)],
  ["RESULTS.moreLike", RESULTS.moreLike],
  ["RESULTS.moreLikeOf", RESULTS.moreLikeOf(GAP)],
  ["RESULTS.moreReasons", RESULTS.moreReasons],
  ["RESULTS.working", RESULTS.working],
  ["RESULTS.whereTitle", RESULTS.whereTitle],
  ["RESULTS.reasonsTitle", RESULTS.reasonsTitle],
  ["RESULTS.noReasons", RESULTS.noReasons],
  ["RESULTS.tradeOffTitle", RESULTS.tradeOffTitle],
  ["RESULTS.noTradeOff", RESULTS.noTradeOff],
  ["RESULTS.reasonsFailed", RESULTS.reasonsFailed],
  ["RESULTS.detailsFailed", RESULTS.detailsFailed],
  ["RESULTS.byModel", RESULTS.byModel],
  ["RESULTS.sourceOfReason", SOURCE.buttonFor(RESULTS.sourceOfReason(1, GAP))],
  ["RESULTS.sourceOfTradeOff", SOURCE.buttonFor(RESULTS.sourceOfTradeOff(GAP))],
  ["RESULTS.openArea", RESULTS.openArea(GAP)],
  ["RESULTS.hide", RESULTS.hide(GAP)],
  ["RESULTS.showOnMap", RESULTS.showOnMap(GAP)],
  ["RESULTS.actions", RESULTS.actions],
  ["STRIP.label", STRIP.label(GAP)],
  ["STRIP.asked", STRIP.asked],
  ["STRIP.askedFor", STRIP.askedFor(GAP)],
  ["STRIP.group.asked", STRIP.group.asked],
  ["STRIP.group.also", STRIP.group.also],
  ["COMPLETENESS.missingTitle", COMPLETENESS.missingTitle],
  ["COMPLETENESS.lacks, of one", COMPLETENESS.lacks([GAP])],
  ["COMPLETENESS.lacks, of many", COMPLETENESS.lacks([GAP, OTHER, GAP])],
  ["COMPLETENESS.lacksAsked, of one", COMPLETENESS.lacksAsked([GAP])],
  ["COMPLETENESS.lacksAsked, of many", COMPLETENESS.lacksAsked([GAP, OTHER])],
  ["JOURNEYS.title", JOURNEYS.title],
  ...Object.entries(JOURNEYS.columns).map(([key, words]): [string, string] => [`JOURNEYS.columns.${key}`, words]),
  ["JOURNEYS.minutes", JOURNEYS.minutes(21)],
  ["JOURNEYS.within", JOURNEYS.within],
  ["JOURNEYS.over", JOURNEYS.over],
  ["JOURNEYS.limit", JOURNEYS.limit(35)],
  ["JOURNEYS.withinLimit", JOURNEYS.withinLimit(35)],
  ["JOURNEYS.overLimit", JOURNEYS.overLimit(35)],
  ["JOURNEYS.beyond", JOURNEYS.beyond(90)],
  ["JOURNEYS.missing", JOURNEYS.missing],
  ...Object.entries(JOURNEYS.estimated).map(([key, words]): [string, string] => [`JOURNEYS.estimated.${key}`, words]),
  ["JOURNEYS.estimatedFrom", JOURNEYS.estimatedFrom],
  ["JOURNEYS.usesOne", JOURNEYS.usesOne(GAP)],
  ["JOURNEYS.usesMean", JOURNEYS.usesMean],
  ["JOURNEYS.notCounted, of one", JOURNEYS.notCounted(1)],
  ["JOURNEYS.notCounted, of many", JOURNEYS.notCounted(2)],
  ["JOURNEYS.usesNone, of one", JOURNEYS.usesNone(1)],
  ["JOURNEYS.usesNone, of many", JOURNEYS.usesNone(2)],
  ["JOURNEYS.timed", JOURNEYS.timed],
  ["JOURNEYS.notGiven", JOURNEYS.notGiven],
  ["JOURNEYS.notApply", JOURNEYS.notApply],
  ...Object.entries(COST).map(([key, words]): [string, string] => [`COST.${key}`, words]),
  ...Object.entries(CONFIDENCE).map(([key, words]): [string, string] => [`CONFIDENCE.${key}`, words]),
  ["BREAKDOWN.title", BREAKDOWN.title],
  ["BREAKDOWN.caption", BREAKDOWN.caption],
  ...Object.entries(BREAKDOWN.columns).map(([key, words]): [string, string] => [`BREAKDOWN.columns.${key}`, words]),
  ["BREAKDOWN.has", BREAKDOWN.has],
  ["BREAKDOWN.hasNot", BREAKDOWN.hasNot],
  ["BREAKDOWN.outOf", BREAKDOWN.outOf(50)],
  ["BREAKDOWN.percent", BREAKDOWN.percent(24)],
  ["BREAKDOWN.roundedDown", BREAKDOWN.roundedDown],
  ["SOURCE.buttonFor", SOURCE.buttonFor(GAP)],
  ["SOURCE.dataFrom", SOURCE.dataFrom],
  ["SOURCE.by", SOURCE.by],
  ["SOURCE.madeUp", SOURCE.madeUp],
  ["LOCATOR.title", LOCATOR.title(GAP)],
  ["LOCATOR.city", LOCATOR.city],
  ["LOCATOR.close", LOCATOR.close],
];

/** The sentences of a line: what ends in a full stop, cut where one sentence gives way to the next. */
function sentencesOf(words: string): string[] {
  if (!/[.?]$/.test(words)) return [];
  return words
    .split(/(?<=[.?])\s+/)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence !== "");
}

const said = (where: string) => copy.filter(([at]) => at.startsWith(where)).map(([, words]) => words);

describe("the words of a result, of a failure and of what Burro cannot answer", () => {
  test("test_the_lines_are_read_whole_with_each_gap_filled", () => {
    expect(copy.length).toBeGreaterThan(150);
    expect(copy.filter(([, words]) => words.includes(GAP)).length).toBeGreaterThanOrEqual(12);
    expect(copy.filter(([, words]) => words.trim() === "")).toEqual([]);
  });

  test("test_no_line_uses_a_word_of_the_product_that_a_newcomer_does_not_know", () => {
    // "This data" said nothing to somebody who had not read the design, and nor did a
    // release, a recipe or its parts.
    const unknown = /\bthis data\b|\breleases?\b|\brecipes?\b|\bparts?\b|\bhundredths\b|\bfor want of\b|\bin hand\b/i;

    expect(copy.filter(([, words]) => unknown.test(words))).toEqual([]);
  });

  test("test_the_two_codes_at_the_foot_of_a_list_are_named_as_the_foot_of_every_page_names_them", () => {
    // They stand on one page together, so they say one thing one way. "Release" is a word
    // of the design: the day the foot of the page says it plainly, this follows.
    expect(RESULTS.foot).toEqual(SITE.footer);
  });

  test("test_no_line_gives_a_verdict_on_a_place", () => {
    const verdict =
      /\b(best|better|worst|worse|good|bad|badly|nice|lovely|desirable|popular|sought|safe|safer|unsafe|dangerous|rough|up and coming|affluent|deprived|posh)\b/i;

    expect(copy.filter(([, words]) => verdict.test(words))).toEqual([]);
  });

  test("test_a_sentence_is_whole_and_is_never_cut_down_to_a_fragment", () => {
    const short = copy.flatMap(([where, words]) =>
      sentencesOf(words)
        .filter((sentence) => sentence.split(/\s+/).length < 4)
        .map((sentence) => [where, sentence]),
    );

    expect(short).toEqual([]);
  });

  test("test_every_line_is_plain_british_english_with_nothing_the_face_of_a_sentence_lacks", () => {
    const loud = copy.filter(([, words]) => /!|\p{Extended_Pictographic}/u.test(words));
    const drawn = copy.filter(([, words]) => /[^\x20-\x7e£·]/.test(words));
    const american = copy.filter(([, words]) => /\b(neighbor|color|center|favorite|meter)s?\b/i.test(words));

    expect([loud, drawn, american]).toEqual([[], [], []]);
  });

  test("test_no_line_says_why_with_a_colon_where_a_person_says_because_or_so", () => {
    // "It could not be tested here: there is no cost figure." A colon before a name or a
    // code stands, as "Show the working: Somewhere" does. One inside a sentence does not.
    const riddles = copy.filter(([, words]) => sentencesOf(words).some((sentence) => /: [a-z]/.test(sentence)));

    expect(riddles).toEqual([]);
  });

  describe("what Burro cannot answer", () => {
    test("test_each_line_still_names_what_burro_has_no_data_on_word_for_word", () => {
      // What each says Burro lacks is a promise of what Burro does not do.
      const lacks: Readonly<Record<keyof typeof UNMET, string>> = {
        broadband: "Burro has no data on broadband",
        flood_risk: "Burro has no data on flood risk",
        health_services: "Burro has no data on health services other than GP surgeries and pharmacies",
        driving: "Burro does not work out journeys by car",
        listings: "Burro does not show homes to rent or to buy",
        affordability_verdict: "Burro does not say what you can afford",
        community_amenities: "Burro has no data on places of worship, or on shops and venues for one community",
        outside_the_city: "Burro covers one city",
        street_cleanliness: "Burro has no measure of how clean a street is",
        upkeep: "Burro has no measure of how well kept a place is",
        ratings: "Burro has no ratings or reviews of any place",
        prices_and_hours: "Burro has no data on what a place charges or when it opens",
        mobile_coverage: "Burro has no data on mobile signal",
        change_over_time: "Burro has no measure of how an area is changing",
        other: "Burro could not read some of what you typed",
      };

      for (const [category, words] of Object.entries(UNMET)) {
        expect(words.startsWith(lacks[category as keyof typeof UNMET])).toBe(true);
      }
    });

    test("test_what_burro_does_in_its_place_is_still_said", () => {
      expect(UNMET.driving).toMatch(/by public transport, by bike or on foot/);
      expect(UNMET.listings).toMatch(/It ranks areas/);
      expect(UNMET.affordability_verdict).toMatch(/It shows what homes cost in each area/);
    });

    test("test_site_copy_names_no_city", () => {
      expect(UNMET.outside_the_city).not.toMatch(/London|Quillhaven/);
    });
  });

  describe("what is not known", () => {
    test("test_a_figure_that_is_missing_is_said_to_be_missing_and_never_filled_in", () => {
      expect(APART.lead).toMatch(/Where a figure is missing, Burro says so and does not fill it in\./);
    });

    test("test_what_an_area_has_no_figure_for_is_named_and_the_fit_is_said_to_leave_it_out", () => {
      for (const words of [...said("COMPLETENESS.lacks"), ...said("COMPLETENESS.lacksAsked")]) {
        expect(words).toMatch(/Burro has no figure for/);
        expect(words).toMatch(/so the fit leaves (it|them) out\.$/);
      }
      // Each is named in quotation marks, as the name of a thing is: a name is a wish, as
      // "Less transport noise" is, and read as words of the sentence it said another thing.
      expect(COMPLETENESS.lacks([GAP])).toContain(`"${GAP}"`);
      expect(COMPLETENESS.lacks([GAP, OTHER])).toContain(`"${GAP}" and "${OTHER}"`);
      expect(COMPLETENESS.lacksAsked([GAP, OTHER])).toContain(`"${GAP}" and "${OTHER}"`);
    });

    test("test_only_what_a_person_asked_for_is_said_to_have_been_asked_for", () => {
      // What counts in a search is not all what was asked for: the settings nobody chose
      // count too. A usual setting with no figure is named without those words.
      expect(said("COMPLETENESS.lacksAsked").every((words) => /^You asked for /.test(words))).toBe(true);
      expect(said("COMPLETENESS.lacks,").some((words) => /asked/.test(words))).toBe(false);
      expect(BREAKDOWN.caption).toMatch(/counts in your search/);
      expect(BREAKDOWN.caption).not.toMatch(/asked/);
    });

    test("test_a_firm_limit_that_could_not_be_checked_says_so_and_says_which_figure_is_missing", () => {
      expect(UNTESTED.over_budget).toBe(
        "Your budget is a firm limit, but Burro could not check it for this area, because it has no cost figure.",
      );
      expect(UNTESTED.commute_cap).toBe(
        "Your limit for a journey is firm, but Burro could not check it for this area, because it has no journey time.",
      );
      // Both codes of a journey are one thing to a person: the limit was not checked.
      expect(UNTESTED.commute_likely_beyond).toBe(UNTESTED.commute_cap);
      for (const words of Object.values(UNTESTED)) expect(words).toMatch(/could not check/);
    });

    test("test_a_journey_with_no_time_is_said_not_to_count_and_is_never_said_to_take_no_time", () => {
      for (const words of [...said("JOURNEYS.notCounted"), ...said("JOURNEYS.usesNone")]) {
        // "Burro has no time for it" is what a person says of a thing they cannot be bothered with.
        expect(words).toMatch(/Burro has no journey time for/);
        expect(words).toMatch(/(does|do|counts) not count towards|counts towards the fit/);
        expect(/\d/.test(words)).toBe(false);
      }
    });
  });

  describe("what the service wrote", () => {
    test("test_an_estimate_is_said_in_the_words_of_the_service", () => {
      expect(JOURNEYS.estimated).toEqual({
        likely_within: "Likely within your limit",
        borderline: "Borderline for your limit",
        likely_beyond: "Likely beyond your limit",
      });
      // The line is the service's, which a release that estimates its journeys serves with
      // its form. It was held to words written here, and went on saying them once the
      // service had written its line again: a result then said one in its reason and the
      // other beside its journey. So it is held to the line as it was recorded.
      const served = recordedAnswer("get_meta", "estimate/meta").body.data.journey_estimate?.said;
      expect(served).toMatch(/\bestimate\b.*\bdistance\b.*\btimetable\.$/);
      expect(JOURNEYS.estimatedFrom).toBe(served);
      expect(FILTERED.commute_likely_beyond.endsWith(` ${served}`)).toBe(true);
    });

    test("test_how_sure_a_cost_is_is_written_as_its_fact_writes_it", () => {
      expect(CONFIDENCE).toEqual({ high: "high", medium: "medium", low: "low", unstated: "unstated" });
    });
  });

  describe("what is promised of a sentence and of a figure", () => {
    test("test_a_sentence_a_model_wrote_says_that_a_model_wrote_it_and_that_it_was_checked", () => {
      expect(RESULTS.byModel).toMatch(/written by AI/);
      expect(RESULTS.byModel).toMatch(/checked it against the source/);
    });

    test("test_made_up_data_says_so_under_every_figure", () => {
      expect(SOURCE.madeUp).toBe("Made-up data");
    });

    test("test_a_budget_is_said_to_be_below_above_or_the_same_and_nothing_is_said_of_what_that_means", () => {
      // What a budget below a range means for a person is a figure with no source.
      const lines = [COST.below, COST.above, COST.inside, COST.belowMiddle, COST.aboveMiddle, COST.atMiddle, COST.belowMiddleRent, COST.aboveMiddleRent, COST.atMiddleRent];

      for (const words of lines) {
        expect(words).toMatch(/^Your budget is (below|above|inside|the same as) this (range|middle price|middle rent)\.$/);
      }
    });
  });

  describe("one thing is said one way", () => {
    test("test_the_cost_of_a_result_names_its_figures_as_the_page_of_an_area_does", () => {
      expect(COST.title).toBe(AREA.cost.title);
      expect(COST.middle).toBe(FACT_COLUMNS.median);
      expect(COST.asOf).toBe(FACT_COLUMNS.asOf);
      expect(COST.confidence).toBe(FACT_COLUMNS.confidence);
      expect(COST.soldIn).toBe(FACT_COLUMNS.soldIn);
      expect(COST.sales).toBe(FACT_COLUMNS.sales);
      expect(COST.figureOf).toBe(FACT_COLUMNS.figureOf);
      expect(COST.recordedIn).toBe(FACT_COLUMNS.recordedIn);
      expect(COST.rents).toBe(FACT_COLUMNS.rents);
      expect(COST.budget).toBe(FACT_COLUMNS.amount);
    });

    test("test_the_journeys_of_a_result_name_their_times_as_a_fact_does", () => {
      expect(JOURNEYS.columns.place).toBe(FACT_COLUMNS.place);
      expect(JOURNEYS.columns.how).toBe(FACT_COLUMNS.mode);
      // A fact says "Minutes" first, since its figure is a bare number. A cell of the
      // table says "21 minutes", so its heading does not.
      expect(FACT_COLUMNS.typical.toLowerCase().endsWith(JOURNEYS.columns.typical.toLowerCase())).toBe(true);
      expect(FACT_COLUMNS.missed.toLowerCase().endsWith(JOURNEYS.columns.missed.toLowerCase())).toBe(true);
      expect(JOURNEYS.missing).toBe(COMPARE_TABLE.journeys.missing);
    });

    test("test_the_way_to_the_areas_most_alike_is_named_as_the_fold_it_opens", () => {
      expect(RESULTS.moreLike).toBe(AREA.alike.open);
      expect(RESULTS.moreLikeOf(GAP)).toBe(`${AREA.alike.open}: ${GAP}`);
    });

    test("test_each_key_of_a_result_says_which_sentence_it_is_the_source_of_and_of_which_area", () => {
      // "Source for Somewhere, 1" was what a person heard, and had to say to their device.
      const names = [
        SOURCE.buttonFor(RESULTS.sourceOfReason(1, GAP)),
        SOURCE.buttonFor(RESULTS.sourceOfReason(2, GAP)),
        SOURCE.buttonFor(RESULTS.sourceOfTradeOff(GAP)),
      ];

      expect(names).toEqual([
        `Source for reason 1 for ${GAP}`,
        `Source for reason 2 for ${GAP}`,
        `Source for the trade-off for ${GAP}`,
      ]);
      expect(new Set(names).size).toBe(names.length);
      // What is seen on the key is the start of its name.
      expect(names.every((name) => name.startsWith(SOURCE.button))).toBe(true);
    });

    test("test_what_is_seen_on_a_short_button_is_the_start_of_its_name", () => {
      expect(RESULTS.workingOf(GAP).startsWith(RESULTS.showWorking)).toBe(true);
      expect(RESULTS.moreLikeOf(GAP).startsWith(RESULTS.moreLike)).toBe(true);
    });

    test("test_a_line_that_sends_a_person_to_the_settings_names_the_fold_and_the_setting", () => {
      // "In Settings" named a button that is gone. Once a search is open the settings are
      // behind one fold, and the line names it as the fold names itself.
      const loose = copy.filter(([, words]) => /\b(in|use|under) (the )?settings\b/i.test(words));

      expect(loose).toEqual([]);
      for (const words of [UNMET.other, JOURNEYS.usesOne(GAP), JOURNEYS.usesMean]) {
        expect(words).toContain(`under ${REFINE.label}.`);
      }
      for (const words of [JOURNEYS.usesOne(GAP), JOURNEYS.usesMean]) expect(words).toContain(`"${JOURNEY.combine}"`);
    });

    test("test_what_is_said_under_the_table_of_a_fit_names_its_column_as_the_table_does", () => {
      expect(BREAKDOWN.roundedDown).toContain(`"${BREAKDOWN.columns.adds}"`);
      expect(BREAKDOWN.roundedDown).toMatch(/rounds every figure in this table down/);
    });

    test("test_the_list_of_what_an_area_lacks_is_named_one_way_wherever_it_stands", () => {
      expect(APART.lacks).toBe(COMPLETENESS.missingTitle);
    });
  });

  describe("a failure", () => {
    test("test_each_failure_is_said_in_words_of_its_own_and_none_blames_what_was_typed", () => {
      const words = Object.values(FAILURE);

      expect(new Set(words).size).toBe(words.length);
      expect(words.filter((one) => /\b(your words|what you typed|your search is wrong)\b/i.test(one))).toEqual([]);
    });

    test("test_being_offline_is_said_one_way_as_a_notice_and_as_a_failure", () => {
      expect(FAILURE.offline).toBe(NOTICE.offline);
      expect(NOTICE.offline).toMatch(/Your search is still here/);
    });

    test("test_that_burro_could_not_be_reached_is_still_said_in_those_words", () => {
      // The guides to the website tell a person what they will read when the service is down.
      expect(FAILURE.network.startsWith("Burro could not be reached.")).toBe(true);
    });

    test("test_what_is_quoted_with_a_report_is_led_in_by_a_line_that_ends_in_a_colon", () => {
      // The code of the request follows it on the same line.
      expect(NOTICE.requestId).toMatch(/quote this reference:$/);
    });
  });

  describe("room on a result", () => {
    test("test_what_a_result_says_of_its_fit_before_anything_is_opened_is_one_sentence", () => {
      // It stands on a result before anything is opened, where the first result must stay
      // whole on the first screen of a phone. What is long is one press away.
      const onTheCard = [
        ...said("COMPLETENESS.lacks"),
        ...said("COMPLETENESS.lacksAsked"),
        ...said("JOURNEYS.notCounted"),
        ...Object.values(UNTESTED),
        RESULTS.noReasons,
        RESULTS.noTradeOff,
      ];

      expect(onTheCard.filter((words) => sentencesOf(words).length !== 1)).toEqual([]);
    });

    test("test_that_no_trade_off_was_found_is_said_on_the_line_of_its_heading", () => {
      // Measured at 390 wide: what is said after the heading "Trade-off" has the room of
      // 34 letters on its line. A longer sentence took a second line, and the first result
      // was no longer whole on the first screen where Burro asks which place was meant.
      expect(RESULTS.noTradeOff).toBe("Burro found no trade-off.");
      expect(RESULTS.noTradeOff.length).toBeLessThanOrEqual(34);
    });

    test("test_the_two_small_headings_over_the_vibes_of_a_result_are_two_words_each", () => {
      // The first stands in the column of a name on a phone, which is as wide as two short
      // words: measured at 390 wide, "You asked for" took two lines and stood the foot of
      // the first result of a plain search 1.5 px under the first screen.
      expect(STRIP.group).toEqual({ asked: "Asked for", also: "Other vibes" });
      for (const words of Object.values(STRIP.group)) expect(words.split(/\s+/).length).toBeLessThanOrEqual(2);
    });
  });
});
