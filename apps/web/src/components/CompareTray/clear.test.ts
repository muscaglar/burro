import { bringClearOf, FRAMES_HELD, keepClearOf, OVER_THE_BAR } from "./clear";

/** Where a thing stands in the window, from its top to its foot. */
type Stands = readonly [top: number, foot: number];

/** Stands a thing in the window, as a browser that lays it out would. jsdom lays nothing out. */
function stand(part: HTMLElement, at: Stands): void {
  const [top, foot] = at;
  part.getBoundingClientRect = () => ({
    top,
    bottom: foot,
    left: 0,
    right: 300,
    x: 0,
    y: top,
    width: 300,
    height: foot - top,
    toJSON: () => ({}),
  });
}

interface Page {
  /** What holds the button that was pressed, with what stands beside it. */
  readonly head: HTMLDivElement;
  readonly pressed: HTMLButtonElement;
  readonly bar: HTMLElement;
  /** How far the window was asked to scroll, each time it was. */
  readonly asked: number[];
}

/** The head of a result with its button, and the bar at the foot of a window 900 px high. */
function aPage(button: Stands, bar: Stands = [776, 900], holds: HTMLElement = document.body): Page {
  const head = document.createElement("div");
  const beside = document.createElement("span");
  const pressed = document.createElement("button");
  beside.append(pressed);
  head.append(beside);
  holds.append(head);
  const section = document.createElement("section");
  document.body.append(section);
  stand(pressed, button);
  stand(beside, button);
  stand(section, bar);
  const asked: number[] = [];
  jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
    asked.push(y);
  }) as typeof window.scrollBy);
  return { head, pressed, bar: section, asked };
}

/** Something that stands in the head, beside the button or over it or under it. */
function beside(head: HTMLElement, at: Stands): HTMLElement {
  const one = document.createElement("p");
  stand(one, at);
  head.prepend(one);
  return one;
}

/** A box that scrolls in itself, as the column of the map does beside the answer. */
function aBoxThatScrolls(at: Stands, holdsAsMuchAs: number): HTMLDivElement {
  const box = document.createElement("div");
  box.style.overflowY = "auto";
  stand(box, at);
  Object.defineProperty(box, "clientHeight", { configurable: true, value: at[1] - at[0] });
  Object.defineProperty(box, "scrollHeight", { configurable: true, value: holdsAsMuchAs });
  document.body.append(box);
  return box;
}

beforeEach(() => {
  Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
});

afterEach(() => {
  document.body.replaceChildren();
  jest.restoreAllMocks();
});

describe("what was pressed, brought clear of the bar that came over it", () => {
  test("test_a_button_the_bar_came_over_is_brought_up_until_it_stands_clear_of_the_bar_and_no_further", () => {
    // Measured at 1440 by 900: "Add to compare" stood from 775 to 819, and the bar came from
    // 776.5 to the foot of the window. The button that held the focus was under the bar.
    const { pressed, bar, asked } = aPage([775, 819], [776.5, 900]);

    const moved = bringClearOf(bar, pressed);

    expect(asked).toEqual([819 + OVER_THE_BAR - 776.5]);
    expect(moved).toBe(819 + OVER_THE_BAR - 776.5);
  });

  test("test_a_button_that_stands_clear_of_the_bar_is_left_where_it_is_so_that_nothing_moves_under_the_press", () => {
    const { pressed, bar, asked } = aPage([300, 344]);

    expect(bringClearOf(bar, pressed)).toBe(0);
    // One that stands over the bar with the room that is kept between the two is clear of it.
    stand(pressed, [724 - OVER_THE_BAR, 776 - OVER_THE_BAR]);
    expect(bringClearOf(bar, pressed)).toBe(0);
    expect(asked).toEqual([]);
  });

  test("test_a_button_the_bar_is_only_just_over_is_brought_up_by_as_little", () => {
    const { pressed, bar, asked } = aPage([730, 774]);

    // Its foot stood two pixels over the bar: it is given the room that is kept between the two.
    expect(bringClearOf(bar, pressed)).toBe(774 + OVER_THE_BAR - 776);
    expect(asked).toEqual([OVER_THE_BAR - 2]);
  });

  test("test_what_stands_beside_the_button_on_its_line_is_brought_clear_with_it", () => {
    // The name and the fit of a first result that stood low were under the bar as well.
    const { head, pressed, bar, asked } = aPage([760, 804]);
    beside(head, [756, 812]);
    // What stands over the line of the button, and what stands under it, is no part of its line.
    beside(head, [700, 750]);
    beside(head, [830, 1200]);

    expect(bringClearOf(bar, pressed)).toBe(812 + OVER_THE_BAR - 776);
    expect(asked).toEqual([812 + OVER_THE_BAR - 776]);
  });

  test("test_what_stands_beside_the_button_and_is_far_higher_than_it_takes_it_no_further_than_a_line_more", () => {
    // A drawing or a column that stands beside the button may be as high as the result: the
    // page is not moved by the height of it.
    const { head, pressed, bar } = aPage([760, 804]);
    beside(head, [700, 1400]);

    expect(bringClearOf(bar, pressed)).toBe(804 + (804 - 760) + OVER_THE_BAR - 776);
  });

  test("test_what_was_pressed_is_never_taken_over_the_top_of_the_window", () => {
    // A bar as high as the window, as with the text of a phone made far larger.
    const { pressed, bar, asked } = aPage([40, 84], [60, 900]);

    expect(bringClearOf(bar, pressed)).toBe(40 - OVER_THE_BAR);
    expect(asked).toEqual([40 - OVER_THE_BAR]);
    // One that stands at the top already is left there.
    stand(pressed, [4, 48]);
    expect(bringClearOf(bar, pressed)).toBe(0);
  });

  test("test_in_a_box_that_scrolls_in_itself_the_box_is_scrolled_and_the_window_is_left", () => {
    // The card of an area stands in the column of the map, which scrolls in itself and
    // stays in sight: the window would take the answer away and leave the card where it was.
    const box = aBoxThatScrolls([16, 884], 1400);
    box.scrollTop = 120;
    const { pressed, bar, asked } = aPage([800, 844], [776, 900], box);

    expect(bringClearOf(bar, pressed)).toBe(844 + OVER_THE_BAR - 776);
    expect(box.scrollTop).toBe(120 + 844 + OVER_THE_BAR - 776);
    expect(asked).toEqual([]);
  });

  test("test_a_box_that_holds_no_more_than_is_seen_of_it_does_not_scroll_and_the_window_does", () => {
    const box = aBoxThatScrolls([16, 884], 868);
    const { pressed, bar, asked } = aPage([800, 844], [776, 900], box);

    expect(bringClearOf(bar, pressed)).toBe(844 + OVER_THE_BAR - 776);
    expect(box.scrollTop).toBe(0);
    expect(asked).toEqual([844 + OVER_THE_BAR - 776]);
  });

  test("test_a_bar_that_draws_nothing_and_a_button_that_is_not_laid_out_move_nothing", () => {
    const { pressed, bar, asked } = aPage([775, 819], [900, 900]);

    // The bar that is closed takes no room, and comes over nothing.
    expect(bringClearOf(bar, pressed)).toBe(0);
    stand(bar, [776, 900]);
    stand(pressed, [0, 0]);
    expect(bringClearOf(bar, pressed)).toBe(0);
    expect(bringClearOf(null, pressed)).toBe(0);
    expect(bringClearOf(bar, null)).toBe(0);
    expect(asked).toEqual([]);
  });

  test("test_a_bar_that_stands_in_the_page_over_what_was_pressed_is_not_over_it", () => {
    // At the end of a page the bar stands where the page has it, and what follows it in the
    // page stands under its foot: nothing is over that.
    const { pressed, bar, asked } = aPage([640, 684], [500, 624]);

    expect(bringClearOf(bar, pressed)).toBe(0);
    expect(asked).toEqual([]);
  });

  test("test_what_is_pressed_in_the_bar_itself_is_not_under_it", () => {
    const { bar, asked } = aPage([775, 819]);
    const cross = document.createElement("button");
    bar.append(cross);
    stand(cross, [800, 844]);

    expect(bringClearOf(bar, cross)).toBe(0);
    expect(asked).toEqual([]);
  });
});

describe("what was pressed, kept clear of the bar while the page is put back", () => {
  // Seen in a browser, on a page of results: the button was brought clear of the bar, and in
  // the next frame the page stood where it had stood, with the button under the bar. What
  // holds a list of results puts the page back in each of the two frames after a press, so
  // that what was pressed stays under the hand whatever grew over it.

  /** The frames that were asked for and have not yet come, in the order they were asked for. */
  function frames() {
    const asked: (FrameRequestCallback | null)[] = [];
    jest.spyOn(window, "requestAnimationFrame").mockImplementation((next) => asked.push(next));
    jest.spyOn(window, "cancelAnimationFrame").mockImplementation((id) => void (asked[id - 1] = null));
    let come = 0;
    return {
      /** The next frame comes: what was asked of it is done, in the order it was asked. */
      next: () => {
        const upTo = asked.length;
        for (; come < upTo; come += 1) asked[come]?.(0);
      },
      waiting: () => asked.slice(come).filter((one) => one !== null).length,
    };
  }

  test("test_what_was_pressed_is_brought_clear_at_once_and_again_in_each_frame_the_page_may_be_put_back_in", () => {
    const frame = frames();
    const { pressed, bar, asked } = aPage([775, 819], [776.5, 900]);
    const by = 819 + OVER_THE_BAR - 776.5;

    keepClearOf(() => bar, pressed);

    // At once, before the page is drawn.
    expect(asked).toEqual([by]);
    // In each frame the page was put back, and what was pressed stands where it stood.
    frame.next();
    expect(asked).toEqual([by, by]);
    frame.next();
    expect(asked).toEqual([by, by, by]);
    // Nothing puts the page back after that, and nothing more is asked of any frame.
    expect(FRAMES_HELD).toBe(2);
    expect(frame.waiting()).toBe(0);
  });

  test("test_where_nothing_put_the_page_back_nothing_more_is_moved", () => {
    const frame = frames();
    const { pressed, bar, asked } = aPage([775, 819], [776.5, 900]);

    keepClearOf(() => bar, pressed);
    // The page went where it was sent, and what was pressed with it.
    stand(pressed, [775 - asked[0]!, 819 - asked[0]!]);
    frame.next();
    frame.next();

    expect(asked).toHaveLength(1);
  });

  test("test_the_bar_is_looked_for_in_each_frame_so_that_one_that_came_late_is_found", () => {
    const frame = frames();
    const { pressed, bar, asked } = aPage([775, 819], [776.5, 900]);
    let found: HTMLElement | null = null;

    keepClearOf(() => found, pressed);
    expect(asked).toEqual([]);
    found = bar;
    frame.next();

    expect(asked).toEqual([819 + OVER_THE_BAR - 776.5]);
  });

  test("test_what_is_pressed_again_at_once_is_let_go_and_no_frame_moves_the_page_for_it", () => {
    const frame = frames();
    const { pressed, bar, asked } = aPage([775, 819], [776.5, 900]);

    const letGo = keepClearOf(() => bar, pressed);
    letGo();
    frame.next();
    frame.next();

    expect(asked).toHaveLength(1);
  });
});
