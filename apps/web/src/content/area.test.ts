/** @jest-environment node */
/**
 * What the page of an area promises in its own words. The words may change, and have: each
 * test holds what a line must still say however it is put, and none holds a line whole.
 */

import { AREA, LOOK, NAMED, OPENS, OPENS_SAYS, PORTRAIT } from "./area";
import { BREAKDOWN } from "./search";
import { FEATURES } from "./settings";
import { VIBES } from "./vibes";

describe("what is said of the name of an area", () => {
  test("test_a_draft_says_who_wrote_the_name_that_it_is_a_draft_and_that_no_person_has_checked_it", () => {
    const said = NAMED.state.draft("a publisher of names");

    expect(said).toContain("a publisher of names");
    expect(said).toMatch(/\bdraft\b/);
    expect(said).toMatch(/No person has checked it/);
  });

  test("test_a_name_a_person_has_checked_says_so_and_is_not_said_to_be_a_draft", () => {
    const said = NAMED.state.checked("a publisher of names");

    expect(said).toContain("a publisher of names");
    expect(said).toMatch(/a person has checked it/);
    expect(said).not.toMatch(/draft/i);
  });
});

describe("what is not known of an area", () => {
  const notKnown = [
    AREA.where.noNeighbours,
    AREA.where.noStation,
    AREA.where.noStations,
    AREA.journeys.notInHand,
    AREA.cost.none.rent,
    AREA.cost.none.buy,
    AREA.features.noFigure,
    AREA.alike.none,
    LOOK.noStation,
    PORTRAIT.madeOf.noFigure,
    PORTRAIT.madeOf.waits,
    PORTRAIT.unplacedWhy,
    PORTRAIT.notInData,
  ];

  test("test_it_is_said_to_be_not_known_and_is_never_made_to_sound_like_nought", () => {
    for (const said of notKnown) {
      // It says that Burro has none, or does not know. It never says that there is none.
      expect([said, /\b(no|not|none|cannot)\b/i.test(said)]).toEqual([said, true]);
      expect([said, /\b(zero|nought|nil|nothing there|there (is|are) no)\b/i.test(said)]).toEqual([said, false]);
    }
  });

  test("test_it_is_said_of_what_burro_holds_and_not_of_the_place", () => {
    // "No station near this area" reads as a fact about the area. What is true is that
    // Burro knows of none, and each line says whose want it is.
    for (const said of notKnown) expect([said, /\bBurro\b/.test(said)]).toEqual([said, true]);
  });

  test("test_a_vibe_that_was_not_worked_out_is_left_blank_and_never_put_in_the_middle", () => {
    expect(PORTRAIT.unplacedWhy).toMatch(/\bmiddle\b/);
    expect(PORTRAIT.unplacedWhy).toMatch(/\bguess\b/);
    expect(PORTRAIT.unplacedWhy).toMatch(/\bblank\b/);
    // Why, of a vibe that no area has: it is so of every area, and the line says so.
    expect(PORTRAIT.notInData).toMatch(/every area/);
    expect(PORTRAIT.notInData).not.toBe(PORTRAIT.unplacedWhy);
  });
});

describe("what Burro does not do is still said", () => {
  test("test_nothing_about_who_lives_in_a_place_is_compared_and_the_words_over_the_list_say_so", () => {
    expect(AREA.alike.lead).toMatch(/nothing about who lives in an area/i);
  });

  test("test_no_figure_is_a_judgement_of_the_place_and_the_words_over_the_figures_say_so", () => {
    expect(AREA.features.lead).toMatch(/none of them is a judgement of the area/);
  });

  test("test_an_area_that_is_not_ranked_says_that_no_search_lists_it_and_that_the_page_still_holds_it", () => {
    expect(AREA.notRanked).toMatch(/does not rank this area/);
    expect(AREA.notRanked).toMatch(/\bsearch\b/);
    expect(AREA.notRanked).toMatch(/\bpage\b/);
  });

  test("test_the_page_ends_by_sending_a_person_to_walk_the_area", () => {
    expect(LOOK.lead).toMatch(/\bmany\b.*\bstreets\b/);
    expect(LOOK.lead).toMatch(/\bwalk/);
    // What no vibe can see is for the person to see, and is said of the vibes alone: the
    // same page may offer the census, which says who lived there.
    expect(LOOK.cannotSeeLead).toMatch(/^No vibe on this page\b/);
    expect(LOOK.cannotSeeLead).not.toMatch(/\b(no|none of the) figures?\b|\bBurro cannot\b/i);
  });
});

describe("a word of the product is said to be what it is", () => {
  const MEANS = "A vibe is a way of describing what an area feels like.";

  test("test_the_portrait_says_what_a_vibe_is_before_it_names_one", () => {
    // What opens the portrait is one or the other of these, and each says it first.
    expect(PORTRAIT.short.lead.startsWith(MEANS)).toBe(true);
    expect(PORTRAIT.short.none.startsWith(MEANS)).toBe(true);
  });

  test("test_the_line_over_the_lists_says_what_a_band_is_and_what_a_press_opens", () => {
    expect(PORTRAIT.lead).toMatch(/one of five bands/);
    expect(PORTRAIT.lead).toMatch(/from the least to the most/);
    expect(PORTRAIT.lead).toMatch(/\bPress\b/);
  });

  test("test_the_words_over_the_areas_most_alike_say_what_a_measure_is", () => {
    // The sentence of each area counts "measures compared", in the service's words.
    expect(AREA.alike.lead).toMatch(/calls a measure/);
    // The order is the contract's: the areas in the same band on the most measures come first.
    expect(AREA.alike.lead).toContain("the most alike first");
    expect(AREA.alike.lead).toContain("in the same band as this one on the most measures");
  });

  test("test_a_range_of_cost_says_what_its_two_figures_are_and_what_the_middle_is", () => {
    expect(AREA.cost.lead).toContain("Half of homes of this kind cost between these two figures.");
    expect(AREA.cost.lead).toMatch(/\bmiddle\b.*\bhalf\b.*\bless\b.*\bhalf\b.*\bmore\b/);
    expect(AREA.cost.lead).not.toMatch(/\b(quartile|median|percentile)s?\b/i);
  });
});

describe("how much of a vibe a measurement makes up", () => {
  test("test_it_is_a_share_of_the_vibe_and_never_bears_the_name_of_where_a_slider_stands", () => {
    // "How much it counts" is where a slider stands, under Space requirements and in the
    // working of a result, and such figures are no shares of a whole. The page of an area
    // gave that name to a share, of the hundred that the shares of a vibe add up to.
    const ofASlider = [FEATURES.howMuch, BREAKDOWN.columns.weight];

    expect(ofASlider).toEqual(["How much it counts", "How much it counts"]);
    expect(ofASlider).not.toContain(PORTRAIT.madeOf.share);
    expect(PORTRAIT.madeOf.share).toBe("Its share of the vibe");
    // It is a share on the page of vibes, and is said there as it is here.
    expect(VIBES.recipe.columns.share).toBe("Share");
    expect(PORTRAIT.madeOf.shareOf(40)).toBe(VIBES.recipe.share(40));
    // In the working of a result a share is of the fit, and is named in the same manner.
    expect(BREAKDOWN.columns.share).toBe("Its share of the fit");
  });
});

describe("a heading and a label", () => {
  test("test_the_heading_of_a_list_of_vibes_says_by_itself_what_the_list_holds", () => {
    const headings = Object.values(PORTRAIT.groups);

    // "Here" was read as this area and as this city, and "placed" as nothing at all.
    for (const heading of headings) expect([heading, /\b(here|placed?)\b/i.test(heading)]).toEqual([heading, false]);
    expect(new Set(headings).size).toBe(headings.length);
    expect(PORTRAIT.groups.more).toMatch(/\bmore\b.*\bthan most areas\b/i);
    expect(PORTRAIT.groups.less).toMatch(/\bless\b.*\bthan most areas\b/i);
  });

  test("test_no_heading_says_again_what_the_button_that_opened_it_says", () => {
    // What opens a vibe and the heading over its parts each said "Made of".
    for (const opens of Object.values(OPENS)) expect(PORTRAIT.madeOf.title).not.toBe(opens);
    expect(AREA.alike.title).not.toBe(AREA.alike.open);
    expect(LOOK.cannotSeeEach).not.toBe(LOOK.cannotSee);
  });

  test("test_what_opens_a_vibe_is_built_two_ways_and_one_line_chooses", () => {
    expect(PORTRAIT.opens).toBe(OPENS[OPENS_SAYS]);
    expect(Object.keys(OPENS)).toEqual(["short", "full"]);
    // The short one is no wider than what it took the place of, so the line of a vibe keeps its height.
    expect(OPENS.short.length).toBeLessThanOrEqual("Made of".length);
    // Whichever is chosen, the sentence over the lists says what a press opens.
    expect(PORTRAIT.lead).toMatch(/Press a vibe to see the measurements it was worked out from\.$/);
  });

  test("test_a_label_is_a_name_and_a_sentence_ends_in_a_full_stop", () => {
    const labels = [
      NAMED.draft,
      NAMED.label,
      NAMED.name,
      NAMED.how,
      AREA.borough,
      AREA.contents,
      AREA.where.title,
      AREA.cost.title,
      AREA.features.title,
      AREA.alike.open,
      AREA.sources.title,
      AREA.compare,
      AREA.search,
      PORTRAIT.title,
      PORTRAIT.opens,
      PORTRAIT.search.button,
      LOOK.title,
      ...Object.values(PORTRAIT.groups),
    ];
    const sentences = [
      AREA.notRanked,
      AREA.cost.lead,
      AREA.features.lead,
      AREA.alike.lead,
      AREA.sources.lead,
      PORTRAIT.lead,
      PORTRAIT.short.lead,
      PORTRAIT.unplacedWhy,
      PORTRAIT.search.adds("two vibes"),
      LOOK.lead,
      LOOK.cannotSeeLead,
    ];

    for (const label of labels) expect([label, /[.:]$/.test(label)]).toEqual([label, false]);
    for (const sentence of sentences) expect([sentence, sentence.endsWith(".")]).toEqual([sentence, true]);
  });

  test("test_what_stands_before_a_list_of_names_reads_on_into_it", () => {
    // The page sets a colon and the names after it: "... for these vibes: Leafy and Going out."
    expect(AREA.alike.shares).toMatch(/these vibes$/);
    expect(AREA.alike.sharesNone.endsWith(".")).toBe(true);
  });
});
