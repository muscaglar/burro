import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CRIME_RULE } from "@/content/crime";
import { CHIPS, LEFT_OUT, NOTICE } from "@/content/search";
import { REFINE } from "@/content/ways";
import { recordedAnswer } from "@/lib/api/recorded";
import type { LeftThing } from "@/lib/search/said";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { LeftOut } from "./LeftOut";

const meta = recordedAnswer("get_meta", "meta").body.data;
const [least] = recordedAnswer("interpret", "interpret-by-model-least").body.data.suggestions;
if (!least) throw new Error("a recording holds too little");

const gritty: LeftThing = { key: "crime Gritty", name: "Gritty", why: "crime", says: "" };
const young: LeftThing = { key: "residents Young professionals", name: "Young professionals", why: "residents", says: "" };
const pubs: LeftThing = { key: "two_ways Pubs and bars", name: "Pubs and bars", why: "two_ways", says: "" };
const unknown: LeftThing = { key: "place A journey", name: "A journey", why: "place", says: "" };
const anArea: LeftThing = { key: "area Pellam Cross", name: LEFT_OUT.ofAnArea("Pellam Cross"), why: "area", says: "" };
const noWay: LeftThing = {
  key: "no_way A journey",
  name: least.label,
  why: "no_way",
  says: `${least.does} ${least.follows}`,
};

const notice = () => screen.getByRole("status", { name: LEFT_OUT.title });
const line = () => notice().querySelector("summary") as HTMLElement;
const opens = () => notice().querySelector("details") as HTMLDetailsElement;
const entries = () => within(notice()).getAllByRole("listitem").map((item) => item.textContent);

const SHEET = rulesOf(readFileSync(path.join(__dirname, "LeftOut.module.css"), "utf8"));
const setsOf = (selector: string, under: string | null = null) =>
  new Map(SHEET.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));

describe("the line of what was left out, as it is drawn", () => {
  test("test_it_is_one_line_however_much_it_names_and_what_does_not_fit_is_one_press_away", () => {
    // Measured on a phone: the line ran to two lines and three, in a box, and was 60 px and
    // 88. With the chips of the search under it, the first result ended under the screen
    // after five searches of nine.
    render(<LeftOut things={[gritty, young, pubs, unknown, anArea]} words meta={meta} />);

    const said = line().querySelector("[data-names]") as HTMLElement;
    // Every name is in the line, for whoever hears it and whoever opens it.
    expect(said.textContent).toBe(
      `${LEFT_OUT.title}: Gritty; Young professionals; Pubs and bars; A journey; What to do with Pellam Cross; ${LEFT_OUT.words}`,
    );
    const drawn = setsOf(".names");
    expect([drawn.get("white-space"), drawn.get("overflow"), drawn.get("text-overflow")]).toEqual(["nowrap", "hidden", "ellipsis"]);
    // What gives way where there is little room is the line, and never the mark before it.
    expect(drawn.get("min-width")).toBe("0");
    expect(setsOf(".mark").get("flex")).toBe("none");
  });

  test("test_the_line_is_of_one_size_open_and_closed_and_what_it_names_is_said_whole_under_it", async () => {
    // Measured in a browser: opened, the line said all that it names on as many lines as
    // that took, and grew under the press by 42 px at 1440 wide and by 96 on a phone.
    // Nothing changes size under a press. What the line has no room for is said under
    // it, each thing by its name with why.
    const user = userEvent.setup({ delay: null });
    render(<LeftOut things={[gritty, young, pubs, unknown, anArea]} words meta={meta} />);

    const open = SHEET.filter((rule) => /\[open\]/.test(rule.selector));
    expect(open.map((rule) => rule.selector)).toEqual([".opens[open] > summary > .mark"]);
    // What turns as it opens is the mark, inside the room it keeps.
    expect(open.flatMap((rule) => [...rule.sets.keys()])).toEqual(["transform"]);
    expect(setsOf(".opens > summary").get("align-items")).toBe("center");

    await user.click(line());

    expect(opens().open).toBe(true);
    const names = ["Gritty", "Young professionals", "Pubs and bars", "A journey", "What to do with Pellam Cross", LEFT_OUT.words];
    expect(entries().map((entry, at) => entry?.startsWith(`${names[at]}. `))).toEqual(names.map(() => true));
  });

  test("test_it_stands_in_no_box_and_a_band_of_amber_marks_it_as_a_note", () => {
    render(<LeftOut things={[gritty]} words={false} meta={meta} />);

    // No frame of the kit, no rule and no shadow: it is in the box of the search, which is a box already.
    expect(notice()).not.toHaveAttribute("data-kind");
    expect(notice().closest("[data-kind]")).toBeNull();
    const drawn = setsOf(".left");
    expect(drawn.get("box-shadow")).toBe("inset calc(var(--px) * 2) 0 0 var(--notice-mark)");
    expect([...drawn.keys()].filter((name) => /^border|^outline|^background/.test(name))).toEqual([]);
    // No rule of its sheet draws an edge, but where the system's colours are forced and no shadow is drawn.
    const edged = SHEET.filter((rule) => [...rule.sets.keys()].some((name) => name.startsWith("border")));
    expect(edged.map((rule) => [rule.under, rule.selector])).toEqual([["@media (forced-colors: active)", ".left"]]);
  });

  test("test_the_line_is_as_high_as_a_small_control_and_the_whole_of_it_takes_the_press", () => {
    render(<LeftOut things={[gritty]} words={false} meta={meta} />);

    expect(line()).toHaveClass("target-min");
    const drawn = setsOf(".opens > summary");
    expect(drawn.get("display")).toBe("flex");
    expect(drawn.get("align-items")).toBe("center");
    // It keeps no room over or under its words: the least a control is high is its height.
    expect([drawn.get("padding-block"), drawn.get("padding")]).toEqual([undefined, undefined]);
  });
});

describe("what Burro left out of a search", () => {
  test("test_with_nothing_left_out_and_every_word_read_nothing_is_on_the_page", () => {
    const { container } = render(<LeftOut things={[]} words={false} meta={meta} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_it_names_each_thing_in_one_line_that_is_closed_and_opens_by_the_browsers_own_element", async () => {
    // Drawn in full, what was left out and that words were not read stood over the first
    // result. Measured at 1440 by 900 after the founder's own sentence: the first result
    // began at 909 of 900, out of sight. One line names each thing, and why is one press away.
    const user = userEvent.setup({ delay: null });
    render(<LeftOut things={[gritty, young]} words={false} meta={meta} />);

    expect(opens().open).toBe(false);
    expect(line().textContent).toBe(`${LEFT_OUT.title}: Gritty; Young professionals`);
    expect(line()).toHaveClass("target-min");
    expect(notice().querySelectorAll(":scope > :not(details)")).toHaveLength(0);

    await user.click(line());
    expect(opens().open).toBe(true);
  });

  test("test_what_counts_recorded_crime_is_said_with_the_one_account_of_when_recorded_crime_counts", () => {
    render(<LeftOut things={[gritty]} words={false} meta={meta} />);

    expect(entries()).toEqual([`Gritty. ${CRIME_RULE}`]);
  });

  test("test_what_counts_who_lived_somewhere_says_that_it_counts_only_where_a_person_chooses_it_and_where_it_is_added", () => {
    render(<LeftOut things={[young]} words={false} meta={meta} />);

    const [said] = entries();
    expect(said).toBe(`Young professionals. ${LEFT_OUT.why.residents}`);
    expect(said).toMatch(/census of 2021/);
    expect(said).toMatch(/only counts that when you choose it yourself/);
    expect(said?.includes(REFINE.label)).toBe(true);
    // It names no group of people, and passes no judgement on anybody.
    expect(LEFT_OUT.why.residents).not.toMatch(/young|old|famil|student|professional/i);
  });

  test("test_a_place_burro_does_not_know_and_a_thing_that_runs_two_ways_each_say_why_and_where_to_add_it", () => {
    render(<LeftOut things={[unknown, pubs]} words={false} meta={meta} />);

    expect(entries()).toEqual([`A journey. ${LEFT_OUT.why.place}`, `Pubs and bars. ${LEFT_OUT.why.two_ways}`]);
    for (const why of [LEFT_OUT.why.place, LEFT_OUT.why.two_ways]) expect(why.includes(REFINE.label)).toBe(true);
  });

  test("test_a_rule_for_an_area_says_that_no_area_was_left_out_why_and_how_a_person_sets_one", () => {
    render(<LeftOut things={[anArea]} words={false} meta={meta} />);

    expect(line().textContent).toBe(`${LEFT_OUT.title}: What to do with Pellam Cross`);
    expect(entries()).toEqual([`What to do with Pellam Cross. ${LEFT_OUT.why.area}`]);
    // What Burro did, and why: no area is left out on a guess.
    expect(LEFT_OUT.why.area).toMatch(/could not be sure what you want done with it/);
    expect(LEFT_OUT.why.area).toMatch(/would take areas out of your results, so Burro does neither on a guess, and no area has been left out because of it\./);
    // How a person does either, where they want it.
    expect(LEFT_OUT.why.area).toMatch(/you can type "only" and then its name/);
    expect(LEFT_OUT.why.area).toMatch(/you can hide it with the button on its result\.$/);
    // It names no area: the name is the service's, and stands before it.
    expect(LEFT_OUT.why.area).not.toMatch(/Pellam|Foxholt/);
  });

  test("test_the_word_that_sets_a_search_to_one_area_is_one_the_reader_takes_as_the_page_says_it_does", () => {
    // A sentence that begins with the word and the name of an area, as it was recorded.
    const recorded = recordedAnswer("interpret", "interpret-only-one");
    const areas = recordedAnswer("list_areas", "areas").body.data.areas;
    const text = (recorded.request.body as { text: string }).text;
    const [rule] = recorded.body.data.operations.area_ops;

    expect(recorded.body.data.status).toBe("ok");
    expect(rule?.action).toBe("only");
    expect(text.startsWith(`only ${areas.find((area) => area.area_id === rule?.area_id)?.name}`)).toBe(true);
  });

  test("test_a_reading_of_words_that_were_taken_another_way_says_so_and_where_it_is_added", () => {
    // One word counts once. Of the things that are read into the same words one is taken,
    // and each of the others says that the words were taken another way, and where that is seen.
    const prices: LeftThing = { key: "otherwise What homes sell for", name: "What homes sell for", why: "otherwise", says: "" };
    render(<LeftOut things={[prices]} words={false} meta={meta} />);

    expect(entries()).toEqual([`What homes sell for. ${LEFT_OUT.why.otherwise}`]);
    expect(LEFT_OUT.why.otherwise).toMatch(/more than one way/);
    expect(LEFT_OUT.why.otherwise).toMatch(/so that the same words are not counted twice/);
    expect(LEFT_OUT.why.otherwise.includes(CHIPS.label)).toBe(true);
    expect(LEFT_OUT.why.otherwise.includes(REFINE.label)).toBe(true);
  });

  test("test_a_reading_of_words_of_which_no_reading_was_taken_says_so_and_where_it_is_added", () => {
    // The other way it was built: no reading of such words is taken.
    const brands: LeftThing = { key: "several Mix of brands", name: "Mix of brands", why: "several", says: "" };
    render(<LeftOut things={[brands]} words={false} meta={meta} />);

    expect(entries()).toEqual([`Mix of brands. ${LEFT_OUT.why.several}`]);
    expect(LEFT_OUT.why.several).toMatch(/more than one way/);
    expect(LEFT_OUT.why.several.includes(REFINE.label)).toBe(true);
  });

  test("test_a_number_burro_cannot_take_says_what_burro_did_and_where_each_box_says_what_it_takes", () => {
    const minutes: LeftThing = { key: "refused range A journey 0", name: LEFT_OUT.named_by_the_page.commute, why: "range", says: "" };
    render(<LeftOut things={[unknown, minutes]} words={false} meta={meta} />);

    expect(line().textContent).toBe(`${LEFT_OUT.title}: A journey; A journey`);
    expect(entries()).toEqual([`A journey. ${LEFT_OUT.why.place}`, `A journey. ${LEFT_OUT.why.range}`]);
    expect(LEFT_OUT.why.range).toMatch(/, so Burro has left it out of your search\./);
    expect(LEFT_OUT.why.range.includes(REFINE.label)).toBe(true);
    // What was typed is drawn in the box alone: it names no number.
    expect(LEFT_OUT.why.range).not.toMatch(/\d/);
  });

  test("test_a_journey_that_waits_for_a_person_says_that_burro_could_not_be_sure_it_is_needed_and_where_it_is_added", () => {
    const journey: LeftThing = { key: "journey Cindermoor Works", name: LEFT_OUT.ofAJourney("Cindermoor Works"), why: "journey", says: "" };
    render(<LeftOut things={[journey]} words={false} meta={meta} />);

    expect(entries()).toEqual([`A journey to Cindermoor Works. ${LEFT_OUT.why.journey}`]);
    expect(LEFT_OUT.why.journey).toMatch(/could not be sure that you need to reach it/);
    expect(LEFT_OUT.why.journey.includes(REFINE.label)).toBe(true);
    expect(LEFT_OUT.why.journey).not.toMatch(/\?/);
  });

  test("test_a_measure_that_waits_by_a_decision_says_that_burro_adds_it_only_where_it_is_chosen_and_where_it_is_added", () => {
    // A measure that a decision holds to be offered and never applied. Which measure that
    // is, is the service's to say, so what is said of it names none. Seen in a browser: it
    // said that Burro "could not be sure that you want it counted", which is why a wish
    // waits that may be somebody else's, and is not why this does.
    const bands: LeftThing = { key: "by_choice Homes", name: "Homes in the higher council tax bands", why: "by_choice", says: "" };
    render(<LeftOut things={[bands]} words={false} meta={meta} />);

    const [said] = entries();
    expect(said).toBe(`Homes in the higher council tax bands. ${LEFT_OUT.why.by_choice}`);
    expect(LEFT_OUT.why.by_choice).toMatch(/only when you choose it yourself/);
    expect(LEFT_OUT.why.by_choice).not.toMatch(/could not be sure|could not tell/);
    expect(LEFT_OUT.why.by_choice).toMatch(/left it for you to add/);
    expect(LEFT_OUT.why.by_choice.includes(REFINE.label)).toBe(true);
    expect(LEFT_OUT.why.by_choice).not.toMatch(/council|tax|income|crime|census/i);
    // It asks nothing and offers nothing, as every line of the notice.
    expect(LEFT_OUT.why.by_choice).not.toMatch(/\?/);
  });

  test("test_a_wish_that_may_be_somebody_elses_says_that_burro_could_not_be_sure_it_is_wanted_and_where_it_is_added", () => {
    const park: LeftThing = { key: "not_said Nearer a park", name: "Nearer a park", why: "not_said", says: "" };
    render(<LeftOut things={[park]} words={false} meta={meta} />);

    expect(entries()).toEqual([`Nearer a park. ${LEFT_OUT.why.not_said}`]);
    expect(LEFT_OUT.why.not_said).toMatch(/could not be sure that you want it counted/);
    expect(LEFT_OUT.why.not_said).toMatch(/left it for you to add/);
    expect(LEFT_OUT.why.not_said.includes(REFINE.label)).toBe(true);
    expect(LEFT_OUT.why.not_said).not.toBe(LEFT_OUT.why.by_choice);
    expect(LEFT_OUT.why.not_said).not.toMatch(/\?/);
  });

  test("test_a_thing_the_service_gave_no_way_to_take_is_said_in_the_services_own_words", () => {
    render(<LeftOut things={[noWay]} words={false} meta={meta} />);

    expect(entries()).toEqual([`${least.label}. ${least.does} ${least.follows}`]);
  });

  test("test_words_that_were_not_read_are_named_last_with_what_follows_for_the_ranking_and_the_way_to_see_them", async () => {
    const user = userEvent.setup({ delay: null });
    const pressed = jest.fn();
    render(
      <LeftOut things={[gritty]} words meta={meta}>
        <button type="button" onClick={pressed}>
          Show in the box
        </button>
      </LeftOut>,
    );

    expect(line().textContent).toBe(`${LEFT_OUT.title}: Gritty; ${LEFT_OUT.words}`);
    expect(entries()).toEqual([`Gritty. ${CRIME_RULE}`, `${LEFT_OUT.words}. ${NOTICE.partUnread}Show in the box`]);
    // The way to see them is held by what is said of them, and is pressed once the line is opened.
    await user.click(line());
    await user.click(within(notice()).getByRole("button", { name: "Show in the box" }));
    expect(pressed).toHaveBeenCalledTimes(1);
  });

  test("test_what_the_way_to_the_words_did_is_said_beside_it_once_and_by_the_notice_itself", () => {
    // The notice says of itself what changes in it, to whoever hears the page: a line in it
    // that said so too would be said twice over.
    const way = (
      <button type="button" onClick={() => undefined}>
        Show in the box
      </button>
    );
    const { rerender } = render(
      <LeftOut things={[]} words meta={meta}>
        {way}
      </LeftOut>,
    );
    expect(notice().textContent?.includes(NOTICE.partShown(1, 1))).toBe(false);

    rerender(
      <LeftOut things={[]} words meta={meta} did={NOTICE.partShown(1, 1)}>
        {way}
      </LeftOut>,
    );

    const said = within(notice()).getByText(NOTICE.partShown(1, 1));
    expect(said.tagName).toBe("P");
    expect(said.closest("[role='status']")).toBe(notice());
    expect(notice().querySelectorAll("[role='status'], [aria-live]")).toHaveLength(0);
    // It stands with the way that did it, after it.
    expect(said.previousElementSibling?.textContent).toBe("Show in the box");
  });

  test("test_where_words_alone_were_left_out_the_line_says_so_and_holds_no_thing", () => {
    render(<LeftOut things={[]} words meta={meta} />);

    expect(line().textContent).toBe(`${LEFT_OUT.title}: ${LEFT_OUT.words}`);
    expect(entries()).toEqual([`${LEFT_OUT.words}. ${NOTICE.partUnread}`]);
  });

  test("test_where_nothing_is_ranked_it_stands_open_and_can_be_closed", async () => {
    // There is no answer for it to give way to, and why is what a person came to read.
    const user = userEvent.setup({ delay: null });
    render(<LeftOut things={[noWay]} words={false} meta={meta} startsOpen />);

    expect(opens().open).toBe(true);
    await user.click(line());
    expect(opens().open).toBe(false);
  });

  test("test_it_closes_as_the_answer_comes_unless_a_person_has_pressed_it", async () => {
    const user = userEvent.setup({ delay: null });
    const { rerender } = render(<LeftOut things={[gritty]} words={false} meta={meta} startsOpen />);
    expect(opens().open).toBe(true);

    // The areas are ranked: the answer stands under the line, which gives way to it.
    rerender(<LeftOut things={[gritty]} words={false} meta={meta} />);
    expect(opens().open).toBe(false);

    // Opened by a person, it stays open whatever comes.
    await user.click(line());
    rerender(<LeftOut things={[gritty]} words={false} meta={meta} startsOpen />);
    rerender(<LeftOut things={[gritty]} words={false} meta={meta} />);
    expect(opens().open).toBe(true);
  });

  test("test_nothing_of_it_asks_and_nothing_of_it_is_offered_to_be_added", () => {
    const bands: LeftThing = { key: "by_choice Homes", name: "Homes", why: "by_choice", says: "" };
    const park: LeftThing = { key: "not_said A park", name: "A park", why: "not_said", says: "" };
    const prices: LeftThing = { key: "otherwise Prices", name: "Prices", why: "otherwise", says: "" };
    render(<LeftOut things={[gritty, young, pubs, unknown, anArea, noWay, bands, park, prices]} words meta={meta} />);

    expect(notice().textContent).not.toMatch(/\?/);
    expect(within(notice()).queryAllByRole("button")).toEqual([]);
    expect(within(notice()).queryAllByRole("link")).toEqual([]);
  });

  test("test_it_stays_open_when_it_is_drawn_again_with_more_in_it", async () => {
    // A model may read on once the line is opened, and what it noticed is added to the line.
    const user = userEvent.setup({ delay: null });
    const { rerender } = render(<LeftOut things={[gritty]} words={false} meta={meta} />);
    await user.click(line());

    rerender(<LeftOut things={[gritty, young]} words meta={meta} />);

    expect(opens().open).toBe(true);
    expect(entries()).toHaveLength(3);
  });

  test("test_closed_and_opened_it_has_no_accessibility_fault", async () => {
    const user = userEvent.setup({ delay: null });
    const { container } = render(
      <main>
        <LeftOut things={[gritty, young]} words meta={meta} />
      </main>,
    );

    expect(await faultsIn(container)).toEqual([]);
    await user.click(line());
    expect(await faultsIn(container)).toEqual([]);
  });
});
