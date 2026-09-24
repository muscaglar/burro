import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { SUGGEST } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Span, Suggestion } from "@/lib/api/schema";
import { written } from "@/lib/search/spans";
import type { Added } from "@/lib/search/state";

import { faultsIn } from "../../../test/support/axe";
import { SHOWN_AT_FIRST, Suggestions, inSight } from "./Suggestions";

const two = recordedAnswer("interpret", "interpret-suggest");
const many = recordedAnswer("interpret", "interpret-suggest-many");
const place = recordedAnswer("interpret", "interpret-suggest-place");
const long = recordedAnswer("interpret", "interpret-by-model-long");
const asksPlace = recordedAnswer("interpret", "interpret-by-model-place");
const least = recordedAnswer("interpret", "interpret-by-model-least");
const natural = recordedAnswer("interpret", "interpret-suggest-notice");
const typedOf = (recorded: { request: { body?: unknown } }) => (recorded.request.body as { text: string }).text;
// The long sentence holds ten offers. Seven are in sight at first: the first four, and each that one
// press may add. Three readings of a word for the identity of a place wait behind "Show all 10".
const longOffers = long.body.data.suggestions;
const longInSight = inSight(longOffers).map((at) => longOffers[at] as Suggestion);
// Where the journey of the long sentence stands among the ten, and among the seven in sight.
const JOURNEY = { of: 8, drawn: 5 };

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
}

/** The offers, held as the page holds them: one that is chosen of goes. */
function Held({ offered, told, box, reading = false }: Drawn) {
  const [left, setLeft] = useState(offered);
  const [added, setAdded] = useState<Added | null>(null);
  return (
    <Suggestions
      suggestions={left}
      added={added}
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
          spec: long.body.data.spec,
          suggestions: left,
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
      // Two readings of the word for how well off a place is, and the culture beside it.
      "slightly affluent but with some culture around it",
      "slightly affluent but with some culture around it",
      "slightly affluent but with some culture around it",
      "At most 35-40min commute from Pellam Exchange",
      "If I'm renting, max £1,900 a month for a 1 bed flat",
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
      // The third and the fourth have no guess: they are the two readings of a word for how
      // well off a place is, which are the rules' to offer. The fifth is the culture beside it.
      `Add ${SUGGEST.guess}`,
      `Add as a firm limit: areas further off are left out ${SUGGEST.guess}`,
      // "Max" says the most that can be paid, so the guess is the firm limit.
      `Set as a firm limit: dearer areas are left out ${SUGGEST.guess}`,
    ]);
    expect(SUGGEST.guess).toBe("Burro's guess");
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

    expect(items().map((one) => one.querySelectorAll("[data-guess]").length)).toEqual([1, 1, 0, 0, 1, 1, 1]);
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

    expect(told.all).toEqual([[0, 1, 4, 8, 9]]);
    expect(long.body.data.suggestions.map((one) => one.add_all)).toEqual([
      "more",
      "more",
      "",
      "",
      "more",
      "",
      "",
      "",
      "guide",
      "guide",
    ]);
  });

  test("test_it_says_what_it_added_and_what_still_needs_the_person", async () => {
    const { user } = show(long.body.data.suggestions);

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));

    expect(screen.getByRole("status")).toHaveTextContent(
      [
        "5 added. 7 need you: the journey can be made a firm limit; the budget can be made a firm limit",
        "recorded crime, which is added under its own name",
        "what homes sell for",
        "Village feel",
        "Age of buildings",
        "nearer a town centre.",
      ].join("; "),
    );
  });

  test("test_one_press_takes_it_all_back", async () => {
    const { told, user } = show(long.body.data.suggestions);

    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(5) }));
    // What one press may not add is still offered: five things, of which four are in sight.
    expect(screen.queryAllByRole("listitem")).toHaveLength(SHOWN_AT_FIRST);
    expect(screen.getByRole("button", { name: SUGGEST.showAll(5) })).toBeVisible();
    await user.click(screen.getByRole("button", { name: SUGGEST.takeBack }));

    expect(told.back).toEqual([true]);
    expect(items()).toHaveLength(7);
    expect(screen.getByRole("status")).toHaveTextContent("");
    expect(screen.queryByRole("button", { name: SUGGEST.takeBack })).toBeNull();
  });

  test("test_what_is_the_persons_to_choose_is_left_and_the_button_says_how_many_it_adds", async () => {
    const { told, user } = show(many.body.data.suggestions);

    // Pubs run two ways, and a station and a town centre may be counted or not.
    await user.click(screen.getByRole("button", { name: SUGGEST.addThese(3) }));

    expect(told.all).toEqual([[3, 4, 5]]);
    expect(said()).toEqual(many.body.data.suggestions.slice(0, 3).map((one) => one.does));
    expect(screen.getByRole("status")).toHaveTextContent(
      "3 added. 3 need you: pubs and bars; nearer a station; nearer a town centre.",
    );
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
    const atOnce = recordedAnswer("interpret", "interpret-rules-at-once");
    show(atOnce.body.data.suggestions, { reading: true });

    expect(atOnce.body.data.model_pending).toBe(true);
    expect(screen.getByRole("status")).toHaveTextContent(SUGGEST.reading);
    expect(items().length).toBeGreaterThanOrEqual(4);
    expect(block().querySelector("[data-guess]")).toBeNull();
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
