import { act, fireEvent, render, screen } from "@testing-library/react";
import { createRef } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { Folded } from "./Folded";
import { Summary } from "./Summary";

const folds = () => [...document.querySelectorAll("details")] as HTMLDetailsElement[];
const barOf = (fold: HTMLDetailsElement) => fold.querySelector(":scope > summary") as HTMLElement;

describe("a fold that is the browser's own", () => {
  test("test_it_is_closed_as_the_page_is_built_and_opens_with_scripts_off_with_what_it_holds_in_the_page", () => {
    const markup = renderToStaticMarkup(
      <Folded bar={<Summary label="What homes cost" heading={2} />}>
        <p>What it holds.</p>
      </Folded>,
    );

    expect(markup).toMatch(/^<details[ >]/);
    expect(markup).not.toMatch(/<details[^>]* open/);
    expect(markup).not.toMatch(/<button|aria-expanded|onclick/i);
    expect(markup).toContain("What it holds.");
  });

  test("test_it_says_that_it_is_a_fold_and_whether_it_is_one_of_a_stack_so_that_its_bar_is_drawn_by_it", () => {
    render(
      <>
        <Folded bar={<Summary label="One of a stack" />}>a</Folded>
        <Folded stands="alone" bar={<Summary label="By itself" stands="alone" />}>
          b
        </Folded>
        <Folded stands="boxed" className="of-the-page" bar={<Summary label="On the grass" stands="boxed" />}>
          c
        </Folded>
      </>,
    );
    const [stacked, alone, boxed] = folds();

    expect(stacked).toHaveClass("fold", "stacked");
    expect(alone).toHaveClass("fold");
    expect(alone).not.toHaveClass("stacked");
    // What lays it out may give it a class of its own, which says where it stands.
    expect(boxed).toHaveClass("fold", "of-the-page");
    expect(boxed).not.toHaveClass("stacked");
  });

  test("test_what_holds_it_may_keep_hold_of_it_and_hear_it_open_and_hand_it_what_any_part_of_a_page_has", () => {
    const kept = createRef<HTMLDetailsElement>();
    const heard = jest.fn();
    render(
      <Folded ref={kept} id="census" data-nosnippet="" aria-label="The census" onToggle={heard} bar={<Summary label="Who lived here" heading={2} />}>
        figures
      </Folded>,
    );

    expect(kept.current).toBe(folds()[0]);
    expect(kept.current).toHaveAttribute("id", "census");
    expect(kept.current).toHaveAttribute("data-nosnippet", "");
    expect(kept.current).toHaveAttribute("aria-label", "The census");
    act(() => {
      (kept.current as HTMLDetailsElement).open = true;
      fireEvent(kept.current as HTMLDetailsElement, new Event("toggle"));
    });
    expect(heard).toHaveBeenCalledTimes(1);
  });
});

describe("a bar is where it was after it is pressed", () => {
  /** What waits for the page to be drawn next, which jsdom never does: the test draws it. */
  let waiting: FrameRequestCallback[] = [];
  const drawn = () => {
    const due = waiting;
    waiting = [];
    act(() => due.forEach((one) => one(0)));
  };
  /** Where each bar stands in the window, by what it says, which the test says: jsdom lays nothing out. */
  let stands = new Map<string, number>();
  let moved: number[] = [];

  beforeEach(() => {
    waiting = [];
    moved = [];
    stands = new Map();
    jest.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => waiting.push(callback));
    jest.spyOn(window, "cancelAnimationFrame").mockImplementation(() => {
      waiting = [];
    });
    jest.spyOn(window, "scrollBy").mockImplementation(((_: number, by: number) => {
      moved.push(by);
    }) as typeof window.scrollBy);
    jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
      const top = this.tagName === "SUMMARY" ? (stands.get(this.textContent ?? "") ?? 352) : 0;
      return { top, bottom: top + 44, left: 0, right: 0, x: 0, y: top, width: 0, height: 44, toJSON: () => ({}) };
    });
  });

  afterEach(() => jest.restoreAllMocks());

  const leafy = () =>
    render(
      <Folded stands="alone" bar={<Summary label="How Burro works this out" stands="alone" />}>
        <p>What goes into it.</p>
      </Folded>,
    );

  test("test_the_page_goes_by_as_much_as_the_bar_went_so_that_the_bar_stands_where_it_stood", () => {
    // Walked by keyboard at 1440 by 900: on the page of vibes the bar of Leafy stood at 352
    // and after Enter stood at 303, with the page not scrolled. Two vibes stand side by side
    // there, and one whose fold is open is laid out by itself. A second press at the same
    // place landed on what the bar had opened.
    leafy();
    const bar = barOf(folds()[0] as HTMLDetailsElement);

    fireEvent.click(bar);
    stands.set("How Burro works this out", 303);
    drawn();

    expect(moved).toEqual([303 - 352]);
    // And as it closes, the other way.
    stands.set("How Burro works this out", 352);
    fireEvent.click(bar);
    stands.set("How Burro works this out", 401);
    drawn();
    expect(moved).toEqual([-49, 49]);
  });

  test("test_a_press_on_the_arrow_or_on_the_words_is_a_press_on_the_bar", () => {
    leafy();
    const bar = barOf(folds()[0] as HTMLDetailsElement);

    fireEvent.click(bar.querySelector("[aria-hidden='true']") as HTMLElement);
    stands.set("How Burro works this out", 300);
    drawn();
    fireEvent.click(screen.getByText("How Burro works this out"));
    stands.set("How Burro works this out", 310);
    drawn();

    expect(moved).toEqual([300 - 352, 310 - 300]);
  });

  test("test_nothing_is_moved_where_the_bar_did_not_move", () => {
    leafy();

    fireEvent.click(barOf(folds()[0] as HTMLDetailsElement));
    drawn();

    expect(moved).toEqual([]);
  });

  test("test_a_press_on_what_a_fold_holds_is_no_press_on_its_bar_and_a_fold_inside_it_holds_its_own", () => {
    render(
      <Folded bar={<Summary label="What is measured here" heading={2} />}>
        <p>What it holds.</p>
        <Folded bar={<Summary label="Stations and bus stops" heading={3} />}>
          <p>Figures.</p>
        </Folded>
      </Folded>,
    );
    const [, inner] = folds() as [HTMLDetailsElement, HTMLDetailsElement];

    fireEvent.click(screen.getByText("What it holds."));
    expect(waiting).toHaveLength(0);
    // The fold inside holds its own bar, and the fold that holds it holds nothing for that press.
    fireEvent.click(barOf(inner));
    expect(waiting).toHaveLength(1);
    stands.set("Stations and bus stops", 300);
    drawn();
    expect(moved).toEqual([300 - 352]);
  });

  test("test_what_holds_the_fold_still_hears_the_press", () => {
    const heard = jest.fn();
    render(
      <Folded onClick={heard} bar={<Summary label="Sources on this page" heading={2} />}>
        <p>Sources.</p>
      </Folded>,
    );

    fireEvent.click(barOf(folds()[0] as HTMLDetailsElement));

    expect(heard).toHaveBeenCalledTimes(1);
  });

  test("test_a_second_press_before_the_page_is_drawn_leaves_one_thing_waiting", () => {
    leafy();
    const bar = barOf(folds()[0] as HTMLDetailsElement);

    fireEvent.click(bar);
    fireEvent.click(bar);

    expect(waiting).toHaveLength(1);
  });

  test("test_a_fold_that_has_left_the_page_moves_nothing", () => {
    const { unmount } = leafy();

    fireEvent.click(barOf(folds()[0] as HTMLDetailsElement));
    stands.set("How Burro works this out", 100);
    unmount();
    drawn();

    expect(moved).toEqual([]);
  });

  test("test_it_keeps_nothing_and_the_browser_opens_what_is_its_own", () => {
    const stored = jest.spyOn(Storage.prototype, "setItem");
    leafy();
    const bar = barOf(folds()[0] as HTMLDetailsElement);
    const press = new MouseEvent("click", { bubbles: true, cancelable: true });

    act(() => {
      bar.dispatchEvent(press);
    });
    drawn();

    // Nothing here stops the press, says whether the fold is open, or writes to the address or the browser.
    expect(press.defaultPrevented).toBe(false);
    expect(folds()[0]).not.toHaveAttribute("aria-expanded");
    expect(stored).not.toHaveBeenCalled();
    expect(window.location.hash).toBe("");
  });
});
