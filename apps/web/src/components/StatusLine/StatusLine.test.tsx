import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { STATUS } from "@/content/search";
import { WAIT } from "@/content/wait";
import { recordedAnswer } from "@/lib/api/recorded";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf, weightOf, heavier } from "../../../test/support/css";
import { FRAMES, ORDER_SAID, ROOMS, StatusLine, statusOf } from "./StatusLine";

const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data;

const CSS = readFileSync(path.join(__dirname, "StatusLine.module.css"), "utf8");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => rule.under === null);
const FRAME = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Frame", "Frame.module.css"), "utf8"));
/** What the style sheet sets of a selector, in all: one may be named by more rules than one. */
const setsOf = (selector: string, rules = STYLES) =>
  new Map(rules.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

const ranked = { phase: "results" as const, ranking: first, areas, moved: null, gaveWay: true };
const nothing = { phase: "empty" as const, ranking: null, areas, moved: null, gaveWay: false };
/** How many areas the recorded ranking ranks, and the name the service gives the first of them. */
const COUNT = first.scores.length;
const FIRST = areas.find((area) => area.area_id === first.ranked[0]?.area_id)?.name ?? "";

describe("the line that says what happened, as it is drawn", () => {
  test("test_it_is_one_paragraph_that_is_on_the_page_before_it_says_anything_and_says_the_next_thing_itself", () => {
    const { rerender } = render(<StatusLine {...nothing} />);
    const line = screen.getByRole("status");

    expect(line.tagName).toBe("P");
    expect(line).toHaveAttribute("aria-live", "polite");
    // It holds nothing at all, no mark among it: what is drawn of it is drawn by its style sheet.
    expect(line).toBeEmptyDOMElement();

    rerender(<StatusLine {...nothing} phase="interpreting" />);
    expect(screen.getByRole("status")).toBe(line);
    expect(line).toHaveTextContent(STATUS.reading);

    rerender(<StatusLine {...ranked} />);
    expect(screen.getByRole("status")).toBe(line);
    expect(line.textContent).toBe(statusOf(ranked));
  });

  test("test_it_says_each_thing_once_in_one_order", () => {
    render(<StatusLine {...ranked} budgetWent />);

    expect(screen.getByRole("status").textContent).toBe(
      [STATUS.ranked(COUNT, FIRST), STATUS.budgetWent, STATUS.gaveWay].join(" "),
    );
  });

  test("test_a_budget_that_went_because_the_search_became_a_visit_is_not_told_of_renting_or_of_buying", () => {
    // Seen in a browser: a search to rent became a visit, and the line said that what can be
    // paid in rent is not what can be paid to buy, and that a new budget could be typed.
    // Neither is so of a visit, which has no budget to type.
    const said = statusOf({ ...ranked, budgetWent: true, visiting: true });

    expect(said).toBe([STATUS.ranked(COUNT, FIRST), STATUS.budgetWentForAVisit, STATUS.gaveWay].join(" "));
    expect(STATUS.budgetWentForAVisit).toMatch(/^Your budget was taken off, because /);
    expect(STATUS.budgetWentForAVisit).not.toMatch(/\brent\b|\bbuy\b|type a new one|Refine search/i);
    // It says why, and what the areas are ranked by: as the settings say it of a visit.
    expect(STATUS.budgetWentForAVisit).toMatch(/you are visiting/);
    expect(STATUS.budgetWentForAVisit).toMatch(/by everything else/);
    // Of a search for a home it says what it said.
    expect(statusOf({ ...ranked, budgetWent: true, visiting: false })).toContain(STATUS.budgetWent);
    expect(statusOf({ ...ranked, budgetWent: true })).toContain(STATUS.budgetWent);
    // Where no budget went, nothing is said of one.
    expect(statusOf({ ...ranked, visiting: true })).not.toMatch(/budget/i);
  });

  test("test_where_a_journey_or_a_budget_counts_for_more_than_the_place_the_line_says_so", () => {
    // A person who asked for leafy and quiet, and named a workplace, must not read the first
    // result as the leafiest. It is said of every ranking it is true of.
    const led = { ...first.spec, commute_weight: 1, budget: { ...first.spec.budget, weight: 0.8 } };
    const said = STATUS.leads(led.commutes.length, true);

    expect(statusOf({ ...ranked, spec: led })).toBe(`${STATUS.ranked(COUNT, FIRST)} ${said}`);
    expect(statusOf({ ...ranked, spec: led })).not.toContain(STATUS.gaveWay);
  });

  test("test_where_the_areas_are_in_no_order_the_line_does_not_say_what_the_order_means", () => {
    // Drawn side by side: "they are in no particular order" and then "The closest match to
    // what you asked for comes first". Nothing counts in such a search, so nothing comes first.
    const inNoOrder = { ...ranked, ranking: { ...first, empty_spec: true } };

    expect(statusOf(inNoOrder)).toBe(STATUS.rankedNoOrder(COUNT));
  });

  test("test_what_the_line_says_of_a_first_ranking_is_written_as_a_person_would_say_it", () => {
    // It read "21 areas ranked. What you asked for counts most.": two fragments, and the
    // second a riddle to whoever has not seen Burro before.
    expect(STATUS.rankedUnnamed(21)).toBe("Burro has ranked 21 areas for you.");
    expect(STATUS.rankedUnnamed(1)).toBe("Burro has ranked 1 area for you.");
    expect(STATUS.first("Farrowmere")).toBe("The first is Farrowmere.");
    expect(STATUS.gaveWay).toBe("The closest match to what you asked for comes first.");
    expect([STATUS.leads(1, false), STATUS.leads(2, false), STATUS.leads(1, true), STATUS.leads(2, true), STATUS.leads(0, true)]).toEqual([
      "The journey counts the most here.",
      "The journeys count the most here.",
      "The journey and the budget count the most here.",
      "The journeys and the budget count the most here.",
      "The budget counts the most here.",
    ]);
    // No verdict on a place: the first is the closest match to a search, and never the best area.
    for (const said of [STATUS.gaveWay, STATUS.rankedUnnamed(21), STATUS.first("Farrowmere")]) {
      expect(/\b(best|good|better|top|safe|rough|winner|wins?)\b/i.test(said)).toBe(false);
    }
  });

  test("test_what_the_order_means_is_said_in_short_or_in_full_and_one_line_chooses", () => {
    // In full it is the sentence that was given as the way the line should read. Measured on
    // a phone 390 wide it is a third line, and the foot of the first result of a plain search
    // is then 4 px under the first screen: so the line says it in short unless it is told to.
    expect(ORDER_SAID).toEqual(["short", "full"]);
    expect(STATUS.gaveWayInFull).toBe(
      "The things you asked for count the most, so the areas at the top are the closest match to them.",
    );
    expect(statusOf(ranked)).toBe(statusOf({ ...ranked, means: "short" }));
    expect(statusOf({ ...ranked, means: "short" })).toBe(`${STATUS.ranked(COUNT, FIRST)} ${STATUS.gaveWay}`);
    expect(statusOf({ ...ranked, means: "full" })).toBe(`${STATUS.ranked(COUNT, FIRST)} ${STATUS.gaveWayInFull}`);
    render(<StatusLine {...ranked} means="full" />);
    expect(screen.getByRole("status").textContent).toBe(statusOf({ ...ranked, means: "full" }));
  });

  test("test_what_it_says_of_a_first_ranking_is_short_enough_for_two_lines_of_a_phone", () => {
    // Measured in a browser 390 wide, where the line is 338 px of the reading face at 15 px:
    // 89 letters stood in two lines and 96 in three, and a third line puts the foot of the
    // first result 4 px under the first screen. A release of London ranks a thousand areas.
    const longest = [STATUS.gaveWay, ...[1, 2].flatMap((journeys) => [STATUS.leads(journeys, true), STATUS.leads(journeys, false)]), STATUS.leads(0, true)];

    for (const said of longest) {
      expect([said, `${STATUS.rankedUnnamed(1000)} ${said}`.length <= 89]).toEqual([said, true]);
    }
  });

  test("test_while_a_first_ranking_that_a_control_asked_for_is_worked_out_it_says_so", () => {
    // Nothing is read, so it does not say that a search is. It said nothing at all, and the
    // wait was told to nobody who could not see it.
    const asked = { ...nothing, phase: "refining" as const };
    render(<StatusLine {...asked} />);

    expect(statusOf(asked)).toBe(WAIT.ranking);
    expect(screen.getByRole("status").textContent).toBe(WAIT.ranking);
    // A ranking that is worked out again keeps what the line said of the one on the page.
    expect(statusOf({ ...ranked, phase: "refining" })).toBe(statusOf(ranked));
  });

  test("test_once_a_search_is_open_and_nothing_is_ranked_it_says_so_and_leaves_no_hole_in_the_box", () => {
    // Seen in a browser, where Burro asks and where nothing was read: the line said nothing
    // and kept its room, so that nothing moves when it speaks, and the room was an empty
    // band in the box, 72 px on a desk and 44 on a phone. It keeps its room and says what is so.
    const open = { ...nothing, open: true };
    render(<StatusLine {...open} />);
    const line = screen.getByRole("status");

    expect(statusOf(open)).toBe(WAIT.notYet);
    expect(line.textContent).toBe(WAIT.notYet);
    expect(line).not.toBeEmptyDOMElement();
    expect(line.firstElementChild).toHaveClass("happened");
    // Before a search the line says nothing, and the page gives it no room.
    expect(statusOf(nothing)).toBe("");
    expect(statusOf({ ...nothing, open: false })).toBe("");
    // What happens is said in its place.
    expect(statusOf({ ...open, phase: "interpreting" })).toBe(STATUS.reading);
    expect(statusOf({ ...open, phase: "refining" })).toBe(WAIT.ranking);
    expect(statusOf({ ...ranked, open: true })).toBe(statusOf(ranked));
  });

  test("test_the_name_of_the_first_result_is_said_to_a_screen_reader_and_not_drawn", () => {
    render(<StatusLine {...ranked} />);
    const parts = [...screen.getByRole("status").children];

    expect(parts.map((part) => [(part.textContent ?? "").trim(), part.classList.contains("visually-hidden")])).toEqual([
      [STATUS.rankedUnnamed(COUNT), false],
      [STATUS.first(FIRST), true],
      [STATUS.gaveWay, false],
    ]);
  });

  test("test_what_happened_is_said_first_and_is_set_heavier_than_what_follows_it", () => {
    render(<StatusLine {...ranked} />);
    const [happened, ...rest] = [...screen.getByRole("status").children];

    expect(happened).toHaveClass("happened");
    expect(rest.filter((part) => part.classList.contains("happened"))).toEqual([]);
    expect(setsOf(".happened").get("font-weight")).toBe("700");
    // It is heavier and nothing else: not larger, not in another face, not in another colour.
    expect([...setsOf(".happened").keys()]).toEqual(["font-weight"]);
  });

  test("test_it_is_read_in_ink_in_the_face_of_a_sentence", () => {
    expect(setsOf(".status").get("color")).toBe("var(--ink)");
    // The face and the size are the page's: a sentence is set in the reading face, and on a
    // phone the page sets this one small, so that it is one line where it can be.
    const set = ALL.flatMap((rule) => [...rule.sets.keys()]).filter((property) => /^font(-family|-size)?$/.test(property));
    expect(set).toEqual([]);
  });

  test("test_where_the_page_does_not_say_which_frame_it_stands_in_the_box_of_the_look", () => {
    render(<StatusLine {...ranked} />);

    expect(FRAMES).toEqual(["box", "slip", "none"]);
    expect(screen.getByRole("status")).toHaveAttribute("data-kind", "box");
    expect(screen.getByRole("status")).toHaveAttribute("data-frame", "box");
  });

  test("test_where_a_page_asks_for_none_it_stands_in_no_frame_of_its_own_and_is_as_high_as_its_words", () => {
    // Measured at 1440 by 900 where Burro asks which place was meant: the line was two
    // lines in a box of its own, 96 px, over a question 304 px high, and the first result
    // began at 964 of 900, out of sight. It stands in the box of the search, which is a box
    // already: with no frame of its own what it says there is one line of 24 px.
    render(<StatusLine {...ranked} frame="none" />);
    const line = screen.getByRole("status");
    const none = setsOf('.status[data-frame="none"]');

    expect(line).toHaveAttribute("data-frame", "none");
    expect([none.get("border-width"), none.get("box-shadow"), none.get("padding"), none.get("margin")]).toEqual(["0", "none", "0", "0"]);
    // It keeps the room of one line while it says nothing, and of no edge: what it is as
    // high as is worked out from these, as it is in a frame.
    expect([none.get("--room"), none.get("--edges"), none.get("--shadow")]).toEqual(["0px", "0px", "0px"]);
    expect([none.has("min-height"), none.has("height"), none.has("font-size"), none.has("line-height")]).toEqual([false, false, false, false]);
    // It is read on cream, which the frame of the kit brings: the line lays no ground of its own.
    expect([line.getAttribute("data-kind"), none.has("background")]).toEqual(["plain", false]);
    expect(FRAME.filter((rule) => rule.selector === ".plain" && rule.under === null).map((rule) => rule.sets.get("background"))).toEqual(["var(--page)"]);
    // It weighs more than what draws the frame, whichever sheet is read last, and comes
    // after what the line says of each kind of frame, which weighs as much.
    for (const drawn of [".plain", ".plain:not(:where(.frame *))", ".roomy"]) {
      expect([drawn, heavier(weightOf('.status[data-frame="none"]'), weightOf(drawn))]).toEqual([drawn, true]);
    }
    const order = STYLES.map((rule) => rule.selector);
    expect(order.indexOf('.status[data-frame="none"]')).toBeGreaterThan(order.indexOf('.status[data-kind="plain"]'));
    expect(order.indexOf('.status[data-frame="none"]')).toBeGreaterThan(order.indexOf('.status[data-kind="box"]'));
    // On a narrow screen it is as it is there in any frame: what is said of a narrow screen comes after.
    const all = ALL.map((rule) => `${rule.under ?? ""} ${rule.selector}`.trim());
    expect(all.indexOf("@media (max-width: 40rem) .status[data-kind]")).toBeGreaterThan(all.indexOf('.status[data-frame="none"]'));
  });

  test("test_it_is_the_same_paragraph_when_a_page_asks_for_another_frame_so_that_what_it_next_says_is_heard", () => {
    // A question comes and goes with an answer, and the frame of the line with it. A line
    // that was drawn anew would be a line that a screen reader had not yet been told to hear.
    const { rerender } = render(<StatusLine {...ranked} />);
    const line = screen.getByRole("status");

    rerender(<StatusLine {...ranked} frame="none" />);
    expect(screen.getByRole("status")).toBe(line);
    expect(line.tagName).toBe("P");
    expect(line).toHaveAttribute("aria-live", "polite");
    expect(line.textContent).toBe(statusOf(ranked));

    rerender(<StatusLine {...ranked} />);
    expect(screen.getByRole("status")).toBe(line);
    expect(line).toHaveAttribute("data-frame", "box");
  });

  test.each(FRAMES)("test_it_stands_in_a_frame_of_the_kit_while_it_says_something: %s", (frame) => {
    render(<StatusLine {...ranked} frame={frame} />);
    const line = screen.getByRole("status");

    expect(line).toHaveClass("frame", "status");
    expect(line).toHaveAttribute("data-kind", frame === "box" ? "box" : "plain");
    // The frame brings the cream it is read on. The line lays no ground of its own under its words.
    expect(STYLES.filter((rule) => !rule.selector.includes(":empty") && rule.sets.has("background")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_slip_throws_the_shadow_of_the_look_inside_the_room_it_takes", () => {
    const slip = setsOf('.status[data-kind="plain"]');

    // The shadow is the look's own, by its name, so that it goes when the look is turned down.
    expect(slip.get("box-shadow")).toBe("var(--box-shadow)");
    // It falls two art pixels down and to the right, and the slip keeps that room clear: so
    // it is not cut off at the edge of a phone's screen, and does not lie on what follows.
    expect([slip.get("margin-block-end"), slip.get("margin-inline-end")]).toEqual(["var(--shadow)", "var(--shadow)"]);
    expect(slip.get("--shadow")).toBe("calc(var(--px) * 2)");
  });

  test("test_while_it_says_nothing_it_is_no_box_and_keeps_the_room_of_one_so_that_nothing_under_it_moves", () => {
    const empty = setsOf(".status:empty");

    // Nothing of a box is drawn round nothing: no edge, no ground, no shadow, no picture.
    expect([empty.get("border-width"), empty.get("background"), empty.get("box-shadow")]).toEqual(["0", "none", "none"]);
    expect(setsOf(".status:empty::before").get("content")).toBe("none");
    // It is as high as it is with one line in it: the line, the room round it, its two edges
    // and its shadow. The room round it is then no room inside it.
    expect(setsOf(".status").get("min-height")).toBe("calc(var(--leading-text) * 1em + 2 * var(--room) + var(--edges))");
    expect(empty.get("min-height")).toBe(
      "calc(var(--leading-text) * 1em + 2 * var(--room) + var(--edges) + var(--shadow))",
    );
    expect([empty.get("padding"), empty.get("margin")]).toEqual(["0", "0"]);
    // The edges are as wide as the frame draws them, of each kind.
    const edges = (kind: string) =>
      FRAME.filter((rule) => rule.selector === `.${kind}` && rule.under === null).flatMap((rule) => [
        rule.sets.get("border-width") ?? rule.sets.get("border") ?? [],
      ]);
    expect(edges("plain")).toEqual(["var(--edge) solid var(--border)"]);
    expect(setsOf('.status[data-kind="plain"]').get("--edges")).toBe("calc(var(--px) * 2)");
    expect(edges("box")).toEqual(["var(--frame-box-wide)"]);
    // Four art pixels at the top and six at the foot, where the shadow of a box lies inside it.
    expect(setsOf('.status[data-kind="box"]').get("--edges")).toBe("calc(var(--px) * 10)");
    expect(setsOf('.status[data-kind="box"]').get("--shadow")).toBe("0px");
  });

  test("test_the_room_is_kept_unless_the_look_gives_it_up_and_then_the_line_takes_none_while_it_says_nothing", () => {
    const { rerender } = render(<StatusLine {...nothing} />);

    // As it was before the line had a frame: nothing under it moves when it next says something.
    expect(ROOMS).toEqual(["kept", "given"]);
    expect(screen.getByRole("status")).toHaveAttribute("data-room", "kept");
    expect(STYLES.filter((rule) => /data-room="kept"/.test(rule.selector))).toEqual([]);

    rerender(<StatusLine {...nothing} room="given" />);
    expect(screen.getByRole("status")).toHaveAttribute("data-room", "given");
    expect([...setsOf('.status[data-room="given"]:empty')]).toEqual([["min-height", "0"]]);
    // It comes after what keeps the room, and weighs more, so that it holds.
    expect(heavier(weightOf('.status[data-room="given"]:empty'), weightOf(".status:empty"))).toBe(true);
    // It is on the page all the same, so that a screen reader is told when it first says something.
    expect(ALL.filter((rule) => rule.sets.get("display") === "none" || rule.sets.has("visibility"))).toEqual([]);
  });

  test("test_what_takes_the_box_away_weighs_more_than_what_draws_it_whichever_sheet_is_read_last", () => {
    // Which of two style sheets a browser reads last is not the website's to decide.
    const drawing = [
      ...FRAME.filter((rule) => rule.under === null).map((rule) => rule.selector),
      '.status[data-kind="plain"]',
      '.status[data-kind="box"]',
      ".status",
    ];
    const taking = [".status:empty", ".status:empty::before", '.status[data-frame="none"]'];

    for (const taken of taking) {
      const lighter = drawing.filter((drawn) => taken.endsWith("::before") === drawn.endsWith("::before"));
      expect(lighter.length).toBeGreaterThan(1);
      for (const drawn of lighter) {
        const wins =
          heavier(weightOf(taken), weightOf(drawn)) ||
          // In the one sheet the later rule holds, where two weigh the same.
          (String(weightOf(taken)) === String(weightOf(drawn)) &&
            STYLES.findIndex((rule) => rule.selector === taken) > STYLES.findIndex((rule) => rule.selector === drawn) &&
            STYLES.some((rule) => rule.selector === drawn));
        expect([taken, drawn, wins]).toEqual([taken, drawn, true]);
      }
    }
  });

  test("test_on_a_narrow_screen_it_stands_in_no_frame_of_its_own_so_that_the_answer_comes_first", () => {
    // Measured on a phone 390 wide, with every part dressed: the line ran to two lines in a
    // box of its own, 77 px, where the trunk had one line of 21, and the first result ended
    // 150 px under the foot of the first screen. What stands over the answer gives way, and
    // the room between two boxes is the first to: the line stands in the search box, which
    // is a box already.
    const NARROW = "@media (max-width: 40rem)";
    const narrow = (selector: string) =>
      new Map(ALL.filter((rule) => rule.under === NARROW && rule.selector === selector).flatMap((rule) => [...rule.sets]));
    const line = narrow(".status[data-kind]");

    expect([line.get("border-width"), line.get("box-shadow"), line.get("padding"), line.get("margin")]).toEqual(["0", "none", "0", "0"]);
    expect(narrow(".status[data-kind]::before").get("content")).toBe("none");
    // It is read on cream wherever it stands, and brings it.
    expect(line.get("background")).toBe("var(--page)");
    // It keeps the room of one line while it says nothing, and of no edge: what it is as high
    // as is worked out from these, as it is on a wide screen.
    expect([line.get("--room"), line.get("--edges"), line.get("--shadow")]).toEqual(["0px", "0px", "0px"]);
    // Its lines are set as close as the reading face sets a short sentence, and it keeps the
    // room of two of them whatever it says: what it says of a ranking is two lines on a
    // phone and what it says while a search is read is one, and nothing under it may move
    // as Burro comes or as the results take his place.
    expect([line.get("--leading-text"), line.get("line-height")]).toEqual(["1.35", "var(--leading-text)"]);
    expect(line.get("min-height")).toBe("calc(2 * var(--leading-text) * 1em)");
    // Where the look gives the room up, it takes none while it says nothing, there too.
    expect([...narrow('.status[data-kind][data-room="given"]:empty')]).toEqual([["min-height", "0"]]);
    // It weighs more than what draws the frame, whichever sheet is read last, and comes after
    // what the line says of each kind of frame.
    for (const drawn of [".box", ".box-on", ".plain", ".box::before", ".box-on::before"]) {
      const taking = drawn.endsWith("::before") ? ".status[data-kind]::before" : ".status[data-kind]";
      expect([drawn, heavier(weightOf(taking), weightOf(drawn))]).toEqual([drawn, true]);
    }
    const order = ALL.map((rule) => `${rule.under ?? ""} ${rule.selector}`.trim());
    expect(order.indexOf(`${NARROW} .status[data-kind]`)).toBeGreaterThan(order.indexOf('.status[data-kind="box"]'));
    // From 40rem it stands in the frame the look gave it.
    expect([...new Set(ALL.map((rule) => rule.under))]).toEqual([null, NARROW]);
  });

  test("test_nothing_of_it_moves_and_nothing_of_it_is_keyed_on_the_pointer_or_the_focus", () => {
    expect(ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition|transform)/.test(property)))).toEqual([]);
    expect(ALL.filter((rule) => /:(hover|focus|active)/.test(rule.selector))).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault_in_any_frame_in_none_or_with_nothing_to_say", async () => {
    const { container } = render(
      <>
        <StatusLine {...ranked} frame="slip" />
        <StatusLine {...ranked} frame="box" />
        <StatusLine {...ranked} frame="none" />
        <StatusLine {...nothing} />
      </>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
