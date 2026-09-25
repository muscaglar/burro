import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { SUGGEST } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Span, Suggestion } from "@/lib/api/schema";
import { written } from "@/lib/search/spans";
import type { Added } from "@/lib/search/state";
import { addedWithOthers, setsAFirmBudget } from "@/lib/search/suggestion";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { SHOWN_AT_FIRST, Suggestions, everyOffer, inSight, leftInSight } from "./Suggestions";

const two = recordedAnswer("interpret", "interpret-suggest");
const many = recordedAnswer("interpret", "interpret-suggest-many");
const place = recordedAnswer("interpret", "interpret-suggest-place");
const long = recordedAnswer("interpret", "interpret-by-model-long");
const asksPlace = recordedAnswer("interpret", "interpret-by-model-place");
const least = recordedAnswer("interpret", "interpret-by-model-least");
const natural = recordedAnswer("interpret", "interpret-suggest-notice");
const counted = recordedAnswer("interpret", "interpret-suggest-who-is-counted");
const rough = recordedAnswer("interpret", "interpret-suggest-rough-guide");
const atOnce = recordedAnswer("interpret", "interpret-rules-at-once");
const house = recordedAnswer("interpret", "interpret-suggest-house");
const pressed = recordedAnswer("rank", "rank-one-press");
const typedOf = (recorded: { request: { body?: unknown } }) => (recorded.request.body as { text: string }).text;
// The long sentence holds twelve offers. Seven are in sight at first: the first four, and each that
// one press may add. The five that carry a guess stand first. Two readings of a word for how well
// off a place is, and three of a word for its identity, wait behind "Show all 12".
const longOffers = long.body.data.suggestions;
const longInSight = inSight(longOffers).map((at) => longOffers[at] as Suggestion);
// Where the journey of the long sentence stands among the twelve, and among the seven in sight.
const JOURNEY = { of: 10, drawn: 3 };

interface Told {
  chosen: [number, string, string?][];
  /** Each press of the button that adds several things: which things. */
  all: (readonly number[])[];
  shown: (readonly Span[])[];
  /** Each press of "Take it all back". */
  back: true[];
}

interface Drawn {
  readonly offered: readonly Suggestion[];
  readonly told: Told;
  /** What the box holds. Left out, the page cannot show the person's words. */
  readonly box?: string;
  readonly reading?: boolean;
  /** How many areas the ranking that follows a press says a firm budget left out. */
  readonly leftOut?: number;
}

/** The offers, held as the page holds them: one that is chosen of goes. */
function Held({ offered, told, box, reading = false, leftOut }: Drawn) {
  const [left, setLeft] = useState(offered);
  const [added, setAdded] = useState<Added | null>(null);
  return (
    <Suggestions
      suggestions={left}
      added={added}
      leftOut={added?.firm === true && leftOut !== undefined ? leftOut : null}
      reading={reading}
      onChoose={(at, id, placeId) => {
        told.chosen.push(placeId === undefined ? [at, id] : [at, id, placeId]);
        setLeft((before) => before.filter((_, index) => index !== at));
      }}
      onChooseAll={(ats) => {
        told.all.push(ats);
        const gone = left.filter((_, index) => ats.includes(index));
        const stay = left.filter((_, index) => !ats.includes(index));
        setAdded({
          count: gone.length,
          needs: [...gone, ...stay].map((one) => one.needs).filter((needs) => needs !== ""),
          firm: gone.some((one) => setsAFirmBudget(addedWithOthers(one)?.operations ?? { budget_ops: [] })),
          spec: long.body.data.spec,
          suggestions: left,
          chosen: [],
        });
        setLeft(stay);
      }}
      onTakeBack={() => {
        told.back.push(true);
        setLeft(added?.suggestions ?? []);
        setAdded(null);
      }}
      onShow={(spans) => told.shown.push(spans)}
      {...(box === undefined ? {} : { wrote: (span: Span) => written(box, span) })}
      searchPlaces={() => {
        const { body } = recordedAnswer("search_places", "places-search");
        const found = { ok: true as const, status: 200, synthetic: true, requestId: null };
        return Promise.resolve({ ...found, data: body.data, meta: body.meta });
      }}
    />
  );
}

function show(offered: readonly Suggestion[] = two.body.data.suggestions, more: Partial<Drawn> = {}) {
  const told: Told = { chosen: [], all: [], shown: [], back: [] };
  const view = render(<Held offered={offered} told={told} {...more} />);
  return { told, user: userEvent.setup({ delay: null }), ...view };
}

const block = () => screen.getByRole("region", { name: SUGGEST.title });
const items = () => within(block()).getAllByRole("listitem");
const item = (at: number) => items()[at] as HTMLElement;
/** What each offer says it would do, which is what its choices are named by. */
const does = () => items().map((one) => within(one).getAllByRole("group")[0]?.getAttribute("aria-labelledby"));
const said = () => items().map((one) => one.querySelector("p")?.textContent ?? "");
const buttonsOf = (one: HTMLElement) =>
  within(one)
    .getAllByRole("button")
    .map((button) => button.textContent);
/** A thing that carries a note, as an offer of recorded crime does. It is chosen by its own button. */
const noted = (label: string): Suggestion => ({
  ...(natural.body.data.suggestions[1] as Suggestion),
  target: `feature:${label.toLowerCase().replace(/\W+/g, "_")}`,
  label,
  note: "Recorded crime counts only when you ask for it by name.",
  add_all: "",
  needs: "recorded crime, which is added under its own name",
});

describe("an offer in its four parts", () => {
  test("test_an_offer_says_what_it_would_do_what_you_wrote_what_follows_and_the_choices_in_that_order", () => {
    show(long.body.data.suggestions, { box: typedOf(long) });
    const journey = item(JOURNEY.drawn);
    const parts = [...journey.children].map((part) => part.textContent);

    expect(parts).toEqual([
      "Add a journey to Pellam Exchange: at most 40 minutes, by public transport.",
      `${SUGGEST.wrote} At most 35-40min commute from Pellam Exchange`,
      "Areas further off are left out.",
      "You gave 35 to 40: Burro took 40.",
      "You named no way of travelling: Burro took public transport.",
      [
        `Add as a firm limit: areas further off are left out ${SUGGEST.guess}`,
        "Add as a guide: areas further off rank lower",
        "Skip",
        SUGGEST.showWords,
      ].join(""),
    ]);
  });

  test("test_what_an_offer_would_do_and_what_follows_are_the_apis_words", () => {
    show(long.body.data.suggestions, { box: typedOf(long) });

    expect(said()).toEqual(longInSight.map((one) => one.does));
    longInSight.forEach((one, at) => {
      for (const line of [one.follows, ...one.said]) {
        expect(item(at).textContent.includes(line)).toBe(true);
      }
      expect(buttonsOf(item(at)).slice(0, -1).map((text) => text?.replace(` ${SUGGEST.guess}`, ""))).toEqual(
        one.choices.map((choice) => choice.label),
      );
    });
  });

  test("test_the_persons_words_are_cut_from_the_box_by_where_they_stand_and_never_retyped", () => {
    const box = typedOf(long);
    show(long.body.data.suggestions, { box });

    const wrote = items().map((one) => one.querySelector("q")?.textContent ?? null);
    expect(wrote).toEqual([
      "I want to live somewhere quiet",
      "with access to parks",
      // The culture, which carries a guess, and after the guesses two readings of the word
      // for how well off a place is, which stands beside it.
      "slightly affluent but with some culture around it",
      "At most 35-40min commute from Pellam Exchange",
      "If I'm renting, max £1,900 a month for a 1 bed flat",
      "slightly affluent but with some culture around it",
      "slightly affluent but with some culture around it",
    ]);
    // Each is the text of the box between two offsets, letter for letter.
    expect(wrote.every((words) => words !== null && box.includes(words))).toBe(true);
    // No answer holds a word of them: what is served is where they stand.
    expect(wrote.some((words) => JSON.stringify(long.body).includes(words ?? ""))).toBe(false);
  });

  test("test_the_words_are_cut_from_the_box_as_it_stands_with_the_space_before_them", () => {
    show(long.body.data.suggestions.slice(0, 1), { box: `  \n ${typedOf(long)}` });

    expect(item(0).querySelector("q")).toHaveTextContent("I want to live somewhere quiet");
  });

  test("test_where_the_page_cannot_read_the_box_no_words_are_drawn_and_the_offer_is_whole_without_them", () => {
    show(long.body.data.suggestions);

    expect(block().querySelector("q")).toBeNull();
    expect(block().textContent.includes(SUGGEST.wrote)).toBe(false);
    expect(said()).toEqual(longInSight.map((one) => one.does));
  });

  test("test_words_that_are_not_in_the_box_are_not_drawn", () => {
    show(long.body.data.suggestions, { box: "leafy" });

    expect(block().querySelector("q")).toBeNull();
  });

  test("test_doing_nothing_is_skip_and_says_what_it_skips", () => {
    show(long.body.data.suggestions);

    const skips = items().map((one) => within(one).getByRole("button", { name: /^Skip: / }));
    expect(skips.map((button) => button.textContent)).toEqual(Array(7).fill("Skip"));
    expect(skips.map((button) => button.getAttribute("aria-label"))).toEqual(
      longInSight.map((one) => SUGGEST.named("Skip", one.label)),
    );
    // Every choice that does not name its thing is named with it, for whoever cannot see the offer.
    expect(within(item(0)).getByRole("button", { name: `Add (${SUGGEST.guess}): Quiet streets` })).toBeVisible();
    expect(
      within(item(JOURNEY.drawn)).getByRole("button", {
        name: "Add as a guide: areas further off rank lower: Pellam Exchange",
      }),
    ).toBeVisible();
    // It is the last choice of each, and sends nothing.
    expect(skips.every((button) => button.getAttribute("data-way") === "ignore")).toBe(true);
    expect(screen.queryByRole("button", { name: /Leave it out$/ })).toBeNull();
  });

  test("test_a_question_is_asked_where_burro_has_no_guess", () => {
    show();

    expect(said()[0]).toBe("Pubs and bars: more, or fewer?");
    expect(buttonsOf(item(0))).toEqual(["More pubs and bars", "Fewer pubs and bars", "Skip", SUGGEST.showWords]);
    expect(block().querySelector("[data-guess]")).toBeNull();
  });

  test("test_the_choices_of_an_offer_are_named_by_what_it_would_do", () => {
    show(long.body.data.suggestions);

    items().forEach((one, at) => {
      expect(within(one).getAllByRole("group")[0]).toHaveAccessibleName(longInSight[at]?.does);
    });
    expect(new Set(does()).size).toBe(7);
  });
});

describe("the way Burro reads the words", () => {
  test("test_the_guess_is_marked_in_words_on_the_button_and_not_by_colour_alone", () => {
    show(long.body.data.suggestions);

    const marked = [...block().querySelectorAll("button[data-guess]")];
    expect(marked.map((button) => button.textContent)).toEqual([
      `Add ${SUGGEST.guess}`,
      `Add: nearer a park ${SUGGEST.guess}`,
      // The culture. The two readings of a word for how well off a place is, which stand
      // before it in the sentence, have no guess: they are the rules' to offer.
      `Add ${SUGGEST.guess}`,
      `Add as a firm limit: areas further off are left out ${SUGGEST.guess}`,
      // "Max" says the most that can be paid, so the guess is the firm limit.
      `Set as a firm limit: dearer areas are left out ${SUGGEST.guess}`,
    ]);
    expect(SUGGEST.guess).toBe("Burro's guess");
  });

  test("test_the_brackets_of_the_mark_stand_against_its_words_and_a_space_before_them", () => {
    // Seen in a browser: "Add( Burro's guess)". The style sheet puts the mark in brackets, and
    // the space that parts it from the way stood inside them.
    show(long.body.data.suggestions);

    const marks = [...block().querySelectorAll("button[data-guess] span")];
    expect(marks.length).toBeGreaterThan(0);
    expect(marks.map((mark) => mark.textContent)).toEqual(marks.map(() => SUGGEST.guess));
    expect(marks.map((mark) => mark.previousSibling?.textContent?.endsWith(" "))).toEqual(marks.map(() => true));
    // The brackets are the style sheet's, and are drawn hard against what the mark holds.
    const rules = rulesOf(readFileSync(path.join(__dirname, "Suggestions.module.css"), "utf8"));
    const brackets = rules.filter((rule) => /\.guess::(before|after)$/.test(rule.selector));
    expect(brackets.map((rule) => rule.sets.get("content"))).toEqual(['"("', '")"']);
  });

  test("test_a_guess_is_a_mark_and_nothing_is_chosen_until_it_is_pressed", async () => {
    const { told, user } = show(long.body.data.suggestions);

    expect(told.chosen).toEqual([]);
    expect(block().querySelectorAll("[aria-pressed='true'], [aria-checked='true']")).toHaveLength(0);
    await user.click(within(item(JOURNEY.drawn)).getByRole("button", { name: /^Add as a guide/ }));

    // The way that was pressed is the way that is taken, whatever the guess was.
    expect(told.chosen).toEqual([[JOURNEY.of, "guide"]]);
  });

  test("test_at_most_one_way_of_an_offer_is_the_guess", () => {
    show(long.body.data.suggestions);

    expect(items().map((one) => one.querySelectorAll("[data-guess]").length)).toEqual([1, 1, 1, 1, 1, 0, 0]);
  });

  test("test_a_way_that_leaves_areas_out_says_so_on_its_face", () => {
    show(long.body.data.suggestions);

    const firm = [...block().querySelectorAll("button[data-way='firm']")].map((button) => button.textContent);
    expect(firm).toHaveLength(2);
    expect(firm.every((words) => /are left out/.test(words))).toBe(true);
  });

  test("test_two_things_for_the_same_words_are_one_offer_and_each_button_names_its_thing", async () => {
    const { told, user } = show(long.body.data.suggestions);

    expect(buttonsOf(item(1))).toEqual([
      `Add: nearer a park ${SUGGEST.guess}`,
      "Nearer a park: stop counting it",
      "Add: Parks close by",
      "Skip",
      SUGGEST.showWords,
    ]);
    await user.click(within(item(1)).getByRole("button", { name: "Add: Parks close by: Nearer a park" }));

    expect(told.chosen).toEqual([[1, "tag:parks_close_by/more"]]);
  });
});

describe("what one press may add", () => {
  test("test_one_button_adds_every_offer_the_api_says_one_press_may_add", async () => {
    const { told, user } = show(long.body.data.suggestions);

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));

    expect(told.all).toEqual([[0, 1, 6, 10, 11]]);
    expect(long.body.data.suggestions.map((one) => one.add_all)).toEqual([
      "more",
      "more",
      "",
      "",
      "",
      "",
      "more",
      "",
      "",
      "",
      // The journey as a guide, and the budget as it was worded: "max" makes it firm.
      "guide",
      "firm",
    ]);
  });

  test("test_it_says_what_it_added_and_what_still_needs_the_person", async () => {
    const { user } = show(long.body.data.suggestions);

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));

    expect(screen.getByRole("status")).toHaveTextContent(
      [
        "5 added. 8 need you: the journey can be made a firm limit",
        "mix of brands",
        "recorded crime, which is added under its own name",
        "what homes sell for",
        "homes in the higher council tax bands",
        "Village feel",
        "Age of buildings",
        "nearer a town centre.",
      ].join("; "),
    );
  });

  test("test_it_says_how_many_areas_a_firm_budget_left_out_and_where_they_are_listed", async () => {
    // A budget that leaves areas out is never taken in silence.
    const left = pressed.body.data.filtered.filter((area) => area.reason === "over_budget").length;
    const { user } = show(long.body.data.suggestions, { leftOut: left });

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));

    expect(left).toBe(13);
    expect(screen.getByRole("status").textContent).toBe(
      [
        "5 added. Your budget is a firm limit and left out 13 areas: the table of all areas lists each. " +
          "8 need you: the journey can be made a firm limit",
        "mix of brands",
        "recorded crime, which is added under its own name",
        "what homes sell for",
        "homes in the higher council tax bands",
        "Village feel",
        "Age of buildings",
        "nearer a town centre.",
      ].join("; "),
    );
  });

  test("test_it_says_nothing_of_areas_left_out_where_no_firm_budget_was_added", async () => {
    const { user } = show(many.body.data.suggestions, { leftOut: 13 });

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(3) }));

    expect(screen.getByRole("status").textContent).toBe(
      "3 added. 3 need you: pubs and bars; nearer a station; nearer a town centre.",
    );
    expect(SUGGEST.added(2, [], 1)).toBe(
      "2 added. Your budget is a firm limit and left out 1 area: the table of all areas lists it.",
    );
    expect(SUGGEST.added(2, [], 0)).toBe("2 added. Your budget is a firm limit. It left no area out.");
    expect(SUGGEST.added(2, [])).toBe("2 added.");
  });

  test("test_the_line_says_that_the_rents_behind_it_are_of_a_district_or_a_borough", () => {
    // What is said of the rents is the API's, and stands with the count of what was left out.
    const said = recordedAnswer("get_meta", "let/meta").body.data.rents?.of_a_place ?? null;

    expect(said).toBe("Each rent is of a postcode district or of a whole borough, and not of one area alone.");
    expect(SUGGEST.added(2, [], 13, said)).toBe(
      `2 added. Your budget is a firm limit and left out 13 areas: the table of all areas lists each. ${said}`,
    );
    expect(SUGGEST.added(2, [], 0, said)).toBe(`2 added. Your budget is a firm limit. It left no area out. ${said}`);
    // With no firm budget among what was added, nothing is said of it.
    expect(SUGGEST.added(2, [], null, said)).toBe("2 added.");
    // A release whose rents are of the area alone says nothing of a wider place.
    expect(recordedAnswer("get_meta", "meta").body.data.rents ?? null).toBeNull();
  });

  test("test_one_press_takes_it_all_back", async () => {
    const { told, user } = show(long.body.data.suggestions);

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));
    // What one press may not add is still offered: seven things, behind one line.
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
    expect(screen.getByRole("button", { name: SUGGEST.showLeft(7) })).toBeVisible();
    await user.click(screen.getByRole("button", { name: SUGGEST.takeBack }));

    expect(told.back).toEqual([true]);
    expect(items()).toHaveLength(7);
    expect(screen.getByRole("status")).toHaveTextContent("");
    expect(screen.queryByRole("button", { name: SUGGEST.takeBack })).toBeNull();
  });

  test("test_the_focus_is_not_left_on_nothing_when_all_is_taken_back", async () => {
    // Seen in a browser: the button goes with what it took back, and the focus went with it
    // to the page as a whole, so that the next Tab began at the top of the page.
    const { user } = show(long.body.data.suggestions);
    const block = screen.getByRole("region", { name: SUGGEST.title });

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));
    expect(block).toHaveFocus();
    await user.click(screen.getByRole("button", { name: SUGGEST.takeBack }));

    expect(screen.queryByRole("button", { name: SUGGEST.takeBack })).toBeNull();
    expect(block).toHaveFocus();
    expect(document.body).not.toHaveFocus();
  });

  test("test_what_is_the_persons_to_choose_is_left_and_the_button_says_how_many_it_adds", async () => {
    const { told, user } = show(many.body.data.suggestions);

    // Pubs run two ways, and a station and a town centre may be counted or not.
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(3) }));

    expect(told.all).toEqual([[3, 4, 5]]);
    expect(screen.getByRole("status")).toHaveTextContent(
      "3 added. 3 need you: pubs and bars; nearer a station; nearer a town centre.",
    );
    // Each of the three is one press away.
    await user.click(screen.getByRole("button", { name: SUGGEST.showLeft(3) }));
    expect(said()).toEqual(many.body.data.suggestions.slice(0, 3).map((one) => one.does));
  });

  test("test_an_offer_the_api_names_no_way_for_is_never_added_whatever_it_looks_like", () => {
    const one = long.body.data.suggestions[0] as Suggestion;
    show([one, { ...one, target: "tag:leafy", add_all: "" }, noted("Less recorded burglary")]);

    // One thing may be added, so there is no button for all: its own button adds it.
    expect(screen.queryByRole("button", { name: /^Add (all|the) / })).toBeNull();
  });

  test("test_a_journey_to_a_place_that_is_yet_to_be_chosen_is_never_added_at_one_press", () => {
    const one = long.body.data.suggestions[0] as Suggestion;
    show([one, { ...one, target: "tag:leafy" }, ...asksPlace.body.data.suggestions]);

    expect(screen.getByRole("button", { name: SUGGEST.addThese(2) })).toBeVisible();
    expect(asksPlace.body.data.suggestions[0]).toMatchObject({ asks_place: true, add_all: "" });
  });

  test("test_every_offer_one_press_may_add_is_in_sight_and_what_waits_is_the_persons_to_choose", async () => {
    const { user } = show(many.body.data.suggestions);

    // Three are the person's to choose, and three may be added: all six are in sight.
    expect(items()).toHaveLength(6);
    expect(screen.queryByRole("button", { name: SUGGEST.showAll(6) })).toBeNull();
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(3) }));
    // What is left is a question, each of the three, and waits behind one line.
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
    await user.click(screen.getByRole("button", { name: SUGGEST.showLeft(3) }));
    expect(items()).toHaveLength(3);
  });

  test("test_four_are_shown_at_first_and_one_button_shows_them_all", async () => {
    const asked = [...many.body.data.suggestions.slice(0, 3), ...many.body.data.suggestions.slice(0, 3)].map(
      (one, at) => ({ ...one, target: `${one.target}-${at}` }),
    );
    const { user } = show(asked);

    expect(items()).toHaveLength(SHOWN_AT_FIRST);
    await user.click(screen.getByRole("button", { name: SUGGEST.showAll(6) }));

    expect(items()).toHaveLength(6);
    expect(screen.queryByRole("button", { name: SUGGEST.showAll(6) })).toBeNull();
  });

  test("test_while_a_model_reads_the_page_says_so_and_what_the_rules_noticed_is_already_there", () => {
    show(atOnce.body.data.suggestions, { reading: true });

    expect(atOnce.body.data.model_pending).toBe(true);
    expect(screen.getByRole("status")).toHaveTextContent(SUGGEST.reading);
    expect(items().length).toBeGreaterThanOrEqual(4);
    // The rules guess at nothing but what was plainly said, of the journey and of the home.
    const guessed = items().filter((one) => one.querySelector("[data-guess]") !== null);
    expect(guessed.map((one) => one.querySelector("p")?.textContent)).toEqual([
      "Add a journey to Pellam Exchange: at most 40 minutes, by public transport.",
      "Look for a home to rent.",
      "Set a budget of £1,900 a month, as a firm limit.",
      "Look for a 1-bedroom home.",
    ]);
  });
});

describe("once one press has added what it may", () => {
  test("test_what_is_left_folds_to_one_line_under_the_line_that_names_each", async () => {
    // Seen in a browser: after the press seven offers of several lines each stood between
    // the line that said what was done and the first result, which was two screens down.
    const { user } = show(long.body.data.suggestions, { box: typedOf(long) });

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));

    const left = long.body.data.suggestions.filter((one) => one.add_all === "");
    expect(left).toHaveLength(7);
    // No offer is drawn, and no choice of one: the block is the line, the way back and the fold.
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
    expect(within(block()).getAllByRole("button").map((button) => button.textContent)).toEqual([
      SUGGEST.takeBack,
      SUGGEST.showLeft(7),
    ]);
    // The line over the fold names each thing that is left, by the name the API gives it.
    const line = screen.getByRole("status").textContent ?? "";
    for (const one of left) expect(line.includes(one.needs)).toBe(true);
    // What is said of pressing an offer is said where one can be pressed.
    expect(block().textContent?.includes(SUGGEST.why)).toBe(false);
  });

  test("test_each_offer_that_is_left_is_one_press_away_and_none_is_lost", async () => {
    const { told, user } = show(long.body.data.suggestions, { box: typedOf(long) });
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));

    await user.click(screen.getByRole("button", { name: SUGGEST.showLeft(7) }));

    const left = long.body.data.suggestions.filter((one) => one.add_all === "");
    expect(said()).toEqual(left.map((one) => one.does));
    // Each is whole: every way of it can be pressed, and doing nothing is one of them.
    items().forEach((one, at) => {
      expect(buttonsOf(one).slice(0, left[at]?.choices.length)).toEqual(
        left[at]?.choices.map((way) => (way.guess ? `${way.label} ${SUGGEST.guess}` : way.label)),
      );
    });
    expect(block().textContent?.includes(SUGGEST.why)).toBe(true);
    expect(screen.queryByRole("button", { name: SUGGEST.showLeft(7) })).toBeNull();
    // To open the fold chooses nothing and adds nothing.
    expect(told).toMatchObject({ chosen: [], all: [[0, 1, 6, 10, 11]], back: [] });
  });

  test("test_an_offer_behind_the_fold_is_chosen_as_any_other_is", async () => {
    const { told, user } = show(long.body.data.suggestions);
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));
    await user.click(screen.getByRole("button", { name: SUGGEST.showLeft(7) }));
    const left = long.body.data.suggestions.filter((one) => one.add_all === "");
    const way = left[0]?.choices[0];

    await user.click(within(item(0)).getAllByRole("button")[0] as HTMLElement);

    // It is named by where it stands among what is left, as the page holds them.
    expect(told.chosen).toEqual([[0, way?.id]]);
  });

  test("test_opening_the_fold_leaves_the_focus_on_the_block_and_never_on_nothing", async () => {
    const { user } = show(long.body.data.suggestions);
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));

    await user.click(screen.getByRole("button", { name: SUGGEST.showLeft(7) }));

    expect(block() === document.activeElement).toBe(true);
  });

  test("test_what_was_opened_before_the_press_is_folded_after_it", async () => {
    const { user } = show(long.body.data.suggestions);
    await user.click(screen.getByRole("button", { name: SUGGEST.showAll(12) }));
    expect(items()).toHaveLength(12);

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));

    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
    expect(screen.getByRole("button", { name: SUGGEST.showLeft(7) })).toBeVisible();
  });

  test("test_what_one_press_may_still_add_stays_in_sight_so_that_no_button_adds_what_is_out_of_sight", () => {
    // A model may read the words after the press, and mark a guess. What one press may add
    // is then in sight with its button, and what is a question waits behind "Show all".
    const offers = long.body.data.suggestions;
    const added: Added = { count: 1, needs: [], firm: false, spec: long.body.data.spec, suggestions: offers, chosen: [] };
    render(<Suggestions suggestions={offers} added={added} onChoose={() => undefined} onChooseAll={() => undefined} />);

    expect(leftInSight(offers)).toEqual([0, 1, 6, 10, 11]);
    expect(said()).toEqual([0, 1, 6, 10, 11].map((at) => offers[at]?.does));
    expect(screen.getByRole("button", { name: SUGGEST.addAll(5) })).toBeVisible();
    expect(screen.getByRole("button", { name: SUGGEST.showAll(12) })).toBeVisible();
    expect(leftInSight(offers.filter((one) => one.add_all === ""))).toEqual([]);
  });

  test("test_before_any_press_the_offers_are_in_sight_as_they_were", () => {
    show(long.body.data.suggestions);

    expect(items()).toHaveLength(inSight(longOffers).length);
    expect(block().textContent?.includes(SUGGEST.why)).toBe(true);
    expect(screen.queryByRole("button", { name: /left to choose$/ })).toBeNull();
  });

  test("test_with_nothing_left_there_is_no_fold", async () => {
    const offers = long.body.data.suggestions.filter((one) => one.add_all !== "");
    const { user } = show(offers);

    await user.click(screen.getByRole("button", { name: SUGGEST.addAll(5) }));

    expect(within(block()).getAllByRole("button").map((button) => button.textContent)).toEqual([SUGGEST.takeBack]);
    expect(SUGGEST.showLeft(1)).toBe("Show the one left to choose");
  });
});

describe("a budget for a house", () => {
  test("test_a_budget_for_a_house_is_offered_for_a_terraced_house_and_each_other_kind_is_a_button", async () => {
    // "Max £400k for a house" was held against what flats sold for. A price is held by the
    // kind of house, so the API takes a terraced house, says why, and offers every other kind.
    const offers = house.body.data.suggestions;
    const { told, user } = show(offers, { box: typedOf(house) });
    const budget = item(1);

    expect(house.body.data.applied).toEqual([]);
    expect(said()[1]).toBe("Set a budget of £400,000 to buy a terraced house, as a firm limit.");
    expect(budget.textContent.includes("You named no kind of house, so Burro has taken a terraced house")).toBe(true);
    expect(budget.textContent.includes("Semi-detached and detached are one press away.")).toBe(true);
    expect(offers[1]?.choices.map((way) => [way.id, way.guess])).toEqual([
      ["terraced", true],
      ["semi_detached", false],
      ["detached", false],
      ["ignore", false],
    ]);
    // A terraced house is Burro's guess, and one press takes it with the tenure.
    expect(budget.querySelector("[data-guess]")).not.toBeNull();
    expect(offers.map((one) => one.add_all)).toEqual(["more", "terraced"]);
    await user.click(screen.getByRole("button", { name: SUGGEST.addAll(2) }));
    expect(told.all).toEqual([[0, 1]]);
    // The kind that Burro took is sent in an edit that says it is Burro's.
    const sent = offers[1]?.choices.find((way) => way.id === "terraced")?.operations.budget_ops;
    expect(sent?.map((edit) => [edit.amount, edit.segment, edit.provenance])).toEqual([
      [0, "terraced", "inferred"],
      [400000, "unchanged", "ui_edit"],
    ]);
  });

  test("test_another_kind_of_house_is_one_press_away_and_is_the_persons_own", async () => {
    const offers = house.body.data.suggestions;
    const { told, user } = show(offers, { box: typedOf(house) });

    await user.click(within(item(1)).getByRole("button", { name: /semi-detached house/ }));

    expect(told.chosen).toEqual([[1, "semi_detached"]]);
    const sent = offers[1]?.choices.find((way) => way.id === "semi_detached")?.operations.budget_ops;
    expect(sent?.map((edit) => [edit.amount, edit.segment, edit.provenance])).toEqual([
      [0, "semi_detached", "ui_edit"],
      [400000, "unchanged", "ui_edit"],
    ]);
  });
});

describe("what is in sight", () => {
  const labels = (offers: readonly Suggestion[], ats: readonly number[]) => ats.map((at) => offers[at]?.label);

  test("test_the_offers_that_carry_a_guess_come_first_in_the_order_their_words_stand", () => {
    show(long.body.data.suggestions);

    // Quiet, the park, the culture, the journey and the budget, as they stand in the sentence.
    // Then what is asked: the first two readings of a word for how well off a place is.
    expect(inSight(longOffers)).toEqual([0, 1, 6, 10, 11, 2, 3]);
    expect(said()).toEqual([0, 1, 6, 10, 11, 2, 3].map((at) => longOffers[at]?.does));
    expect(items().map((one) => one.querySelector("[data-guess]") !== null)).toEqual([
      true,
      true,
      true,
      true,
      true,
      false,
      false,
    ]);
  });

  test("test_what_the_rules_read_plainly_comes_first_where_no_model_has_read", () => {
    const offers = atOnce.body.data.suggestions;

    // The journey is in sight before "Show all", and one press takes it as a guide.
    expect(labels(offers, inSight(offers))).toEqual([
      "Pellam Exchange",
      "Renting",
      "A budget of £1,900 a month",
      "A 1-bedroom home",
      "Quiet streets",
      "Nearer a park",
      "Mix of brands",
      "Gritty",
      "More culture nearby",
    ]);
  });

  test("test_which_offers_are_in_sight_is_as_it_was_the_first_four_and_what_one_press_may_add", () => {
    for (const offers of [longOffers, atOnce.body.data.suggestions, many.body.data.suggestions]) {
      const expected = offers.flatMap((one, at) => (at < SHOWN_AT_FIRST || one.add_all !== "" ? [at] : []));
      expect([...inSight(offers)].sort((one, other) => one - other)).toEqual(expected);
    }
  });

  test("test_nothing_in_sight_moves_when_the_rest_is_shown", async () => {
    const { user } = show(long.body.data.suggestions);
    const before = said();

    await user.click(screen.getByRole("button", { name: SUGGEST.showAll(12) }));

    expect(items()).toHaveLength(12);
    expect(said().slice(0, 5)).toEqual(before.slice(0, 5));
    // Under the guesses, every other offer in the order its words stand in the sentence.
    expect(everyOffer(longOffers)).toEqual([0, 1, 6, 10, 11, 2, 3, 4, 5, 7, 8, 9]);
    expect(said()).toEqual(everyOffer(longOffers).map((at) => longOffers[at]?.does));
    expect(said().slice(5, 7)).toEqual(before.slice(5));
  });

  test("test_an_offer_is_chosen_by_where_it_stands_in_the_list_whatever_the_order_it_is_drawn_in", async () => {
    const { told, user } = show(long.body.data.suggestions);

    // The culture is drawn third, and is the seventh thing the API offered.
    await user.click(within(item(2)).getByRole("button", { name: /^Add/ }));

    expect(told.chosen).toEqual([[6, "more"]]);
  });
});

describe("a journey whose place Burro does not know", () => {
  test("test_it_is_a_question_with_its_minutes_and_asks_which_place_before_anything_is_added", async () => {
    const { told, user } = show(asksPlace.body.data.suggestions, { box: typedOf(asksPlace) });

    expect(said()).toEqual([
      "Add a journey of at most 40 minutes, by public transport. Burro does not know this place: choose one.",
    ]);
    expect(screen.queryByRole("combobox")).toBeNull();
    await user.click(screen.getByRole("button", { name: /^Add as a guide/ }));

    // Nothing is added yet: the journey has no place. The place search is on the page.
    expect(told.chosen).toEqual([]);
    expect(screen.getByRole("combobox", { name: SUGGEST.whichPlace })).toBeVisible();
    expect(screen.getByRole("button", { name: /^Add as a guide/ })).toHaveAttribute("aria-pressed", "true");
  });

  test("test_the_place_that_is_chosen_goes_with_the_way_that_was_pressed", async () => {
    const { told, user } = show(asksPlace.body.data.suggestions);
    const found = recordedAnswer("search_places", "places-search").body.data.places;

    await user.click(screen.getByRole("button", { name: /^Add as a firm limit/ }));
    await user.type(screen.getByRole("combobox", { name: SUGGEST.whichPlace }), "cin");
    await user.click(await screen.findByRole("option", { name: new RegExp(found[0]?.name ?? "") }));

    expect(told.chosen).toEqual([[0, "firm", found[0]?.place_id]]);
  });

  test("test_skip_needs_no_place", async () => {
    const { told, user } = show(asksPlace.body.data.suggestions);

    await user.click(screen.getByRole("button", { name: /^Skip/ }));

    expect(told.chosen).toEqual([[0, "ignore"]]);
  });

  test("test_a_least_distance_is_answered_in_a_fixed_line_with_nothing_to_press_but_skip", () => {
    show(least.body.data.suggestions, { box: typedOf(least) });

    expect(said()).toEqual(["Burro took no journey from these words."]);
    expect(item(0).textContent.includes("It cannot keep a search away from a place.")).toBe(true);
    expect(buttonsOf(item(0))).toEqual(["Skip", SUGGEST.showWords]);
    expect(item(0).querySelector("q")).toHaveTextContent("Minimum 45 minutes from Mirrowick Basin");
  });
});

describe("what the page holds and where the focus goes", () => {
  test("test_a_choice_tells_the_page_which_offer_and_which_way_and_nothing_else", async () => {
    const { told, user } = show();

    await user.click(screen.getByRole("button", { name: "Fewer pubs and bars" }));

    expect(told.chosen).toEqual([[0, "less"]]);
    expect(said()).toEqual(["Less transport noise: count it?"]);
  });

  test("test_a_choice_among_many_is_of_the_offer_it_stands_in", async () => {
    const { told, user } = show(many.body.data.suggestions);

    await user.click(within(item(2)).getAllByRole("button")[0] as HTMLElement);

    expect(told.chosen).toEqual([[2, many.body.data.suggestions[2]?.choices[0]?.id]]);
  });

  test("test_a_note_that_two_offers_share_is_drawn_once_and_said_of_both", () => {
    show([noted("Less recorded burglary"), noted("Less recorded violence")]);

    const notes = block().querySelectorAll("[class*='note']");
    expect(notes).toHaveLength(1);
    const groups = items().map((one) => within(one).getAllByRole("group")[0] as HTMLElement);
    expect(groups.map((group) => group.getAttribute("aria-describedby"))).toEqual([notes[0]?.id, notes[0]?.id]);
  });

  test("test_who_lived_somewhere_is_offered_towards_more_with_the_apis_note_and_never_at_one_press", async () => {
    const offered = counted.body.data.suggestions;
    const [first] = offered;
    const { told, user } = show(offered, { box: typedOf(counted) });

    // The note is the API's, word for word, and is said of the one offer that counts residents.
    expect(first?.target).toBe("tag:young_professionals");
    const notes = [...block().querySelectorAll("[class*='note']")];
    expect(notes.map((note) => note.textContent)).toEqual([first?.note]);
    expect(first?.note).toBe("Burro counts who was living there at the census of 2021. It measures places first.");
    expect(within(item(0)).getAllByRole("group")[0]?.getAttribute("aria-describedby")).toBe(notes[0]?.id);
    // There is a way to ask for more of them and a way to leave them out. There is none to
    // ask for fewer of anyone, and none is made here.
    expect(first?.choices.map((way) => way.direction)).toEqual(["more", "ignore"]);
    expect(buttonsOf(item(0))).toEqual(["Add", "Skip", SUGGEST.showWords]);
    expect(within(item(0)).queryByRole("button", { name: /fewer|less|towards|stop/i })).toBeNull();
    // One press adds nothing of it: it is chosen by its own button.
    expect(first?.add_all).toBe("");
    expect(screen.queryByRole("button", { name: /^Add (all|the) / })).toBeNull();

    await user.click(within(item(0)).getAllByRole("button")[0] as HTMLElement);

    expect(told.chosen).toEqual([[0, "more"]]);
  });

  test("test_a_vibe_that_is_a_rough_guide_is_offered_with_its_label_and_its_sentence_in_sight", () => {
    const offered = rough.body.data.suggestions;
    const village = offered[2];
    show(offered, { box: typedOf(rough) });

    expect(offered.map((one) => one.target)).toEqual(["tag:leafy", "tag:quiet_residential", "tag:village_feel"]);
    // The note is the API's, word for word: the label, and the sentence that says why.
    expect(village?.note).toBe(
      "Rough guide. Of the areas it puts highest, about half read as villages to people, and it takes some busy main roads and some grand inner streets for villages.",
    );
    const notes = [...block().querySelectorAll<HTMLElement>("[class*='note']")];
    expect(notes.map((note) => note.textContent)).toEqual([village?.note]);
    // It is drawn in the offer, before anything of it is pressed, and nothing hides it.
    expect(item(2)).toContainElement(notes[0] as HTMLElement);
    expect(notes[0]?.closest("[hidden], [aria-hidden='true'], .visually-hidden, details:not([open])")).toBeNull();
    expect(within(item(2)).getAllByRole("group")[0]?.getAttribute("aria-describedby")).toBe(notes[0]?.id);
    // No way of it is marked as Burro's guess.
    expect(village?.choices.map((way) => [way.id, way.guess])).toEqual([["more", false], ["ignore", false]]);
    expect(item(2).textContent?.includes(SUGGEST.guess)).toBe(false);
  });

  test("test_a_vibe_that_is_a_rough_guide_is_never_added_by_the_one_press_that_adds_the_rest", async () => {
    const offered = rough.body.data.suggestions;
    const { told, user } = show(offered, { box: typedOf(rough) });

    expect(offered.map((one) => one.add_all)).toEqual(["more", "more", ""]);
    // The button says that it adds the two that need no choice, and leaves the third.
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(2) }));

    expect(told.all).toEqual([[0, 1]]);
    expect(told.chosen).toEqual([]);
    // What is left waits behind one line, as whatever one press leaves does, and the line
    // over it names it. It is the person's to choose, by a press of its own.
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
    expect(screen.getByRole("status").textContent?.includes(offered[2]?.needs ?? "no name")).toBe(true);
    await user.click(screen.getByRole("button", { name: SUGGEST.showLeft(1) }));
    expect(items()).toHaveLength(1);
    expect(item(0)).toHaveTextContent("Add Village feel.");
    // Opened, the offer is whole: its label and its sentence are in sight, as they were
    // before the press, and nothing hides them.
    const note = item(0).querySelector<HTMLElement>("[class*='note']");
    expect(note?.textContent).toBe(offered[2]?.note);
    expect(note?.closest("[hidden], [aria-hidden='true'], .visually-hidden, details:not([open])")).toBeNull();
    // To open the fold added nothing.
    expect(told.chosen).toEqual([]);
    await user.click(within(item(0)).getAllByRole("button")[0] as HTMLElement);
    expect(told.chosen).toEqual([[0, "more"]]);
  });

  test("test_the_button_shows_where_the_words_stand_in_the_box", async () => {
    const { told, user } = show();

    await user.click(within(item(0)).getByRole("button", { name: SUGGEST.showWordsOf("Pubs and bars") }));

    expect(told.shown).toEqual([two.body.data.suggestions[0]?.spans]);
  });

  test("test_no_id_of_a_place_is_written_into_the_markup", () => {
    const { container } = show(place.body.data.suggestions);

    expect(place.body.data.suggestions[0]?.choices[0]?.operations.commute_ops[0]?.place_id).toBe("syn-p0028");
    expect(/syn-p\d+/.test(container.innerHTML)).toBe(false);
  });

  test("test_choosing_gives_the_focus_to_the_offer_beside_it_and_never_leaves_it_on_nothing", async () => {
    const { user } = show();

    await user.click(within(item(0)).getByRole("button", { name: "More pubs and bars" }));

    expect(document.activeElement).not.toBe(document.body);
    expect(within(item(0)).getAllByRole("button")[0]).toHaveFocus();
  });

  test("test_choosing_of_the_last_offer_gives_the_focus_to_something_that_stays", async () => {
    const { user, container } = show(two.body.data.suggestions.slice(0, 1));
    const last = within(item(0)).getByRole("button", { name: "More pubs and bars" });

    await user.click(last);

    // Nothing is offered any more, so the block has gone. The focus is not on what went with it.
    expect(screen.queryByRole("region", { name: SUGGEST.title })).toBeNull();
    expect(container.contains(last)).toBe(false);
    expect(document.activeElement).not.toBe(last);
  });

  test("test_every_offer_can_be_chosen_from_the_keyboard_in_the_order_it_is_read", async () => {
    const { told, user } = show(long.body.data.suggestions.slice(JOURNEY.of));

    // Add all, then the three ways of the journey in the order they are drawn.
    await user.tab();
    await user.tab();
    expect(document.activeElement).toHaveTextContent(/^Add as a firm limit/);
    await user.tab();
    expect(document.activeElement).toHaveTextContent(/^Add as a guide/);
    await user.keyboard("{Enter}");

    expect(told.chosen).toEqual([[0, "guide"]]);
  });

  test("test_with_nothing_offered_nothing_is_drawn", () => {
    const { container } = show([]);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_every_choice_is_a_native_button_that_takes_a_target_size", () => {
    const { container } = show([...many.body.data.suggestions, ...long.body.data.suggestions]);

    const buttons = [...container.querySelectorAll("button")];
    expect(buttons.length).toBeGreaterThan(10);
    expect(buttons.filter((button) => !/\btarget(-min)?\b/.test(button.className))).toEqual([]);
    expect(container.querySelectorAll("[role='button'], [onclick]")).toHaveLength(0);
  });

  test("test_the_offers_have_no_accessibility_fault", async () => {
    const { container, user } = show([...asksPlace.body.data.suggestions, ...long.body.data.suggestions], {
      box: typedOf(asksPlace),
    });
    await user.click(within(item(0)).getByRole("button", { name: /^Add as a guide/ }));

    expect(await faultsIn(container)).toEqual([]);
  });
});
