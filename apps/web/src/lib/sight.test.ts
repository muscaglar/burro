import {
  bringIntoSight,
  bringWholeIntoSight,
  DOUBLE_PRESS_MS,
  HEAD,
  keepInPlace,
  OPENS,
  sideWithRoom,
  WHAT_A_PRESS_OPENS,
} from "./sight";

/** Where a thing stands in the window, from its top to its foot. */
type Stands = readonly [top: number, foot: number];

/** Stands a thing in the window, as a browser that lays it out would. jsdom lays nothing out. */
function stand(part: HTMLElement, at: Stands | (() => Stands)): void {
  part.getBoundingClientRect = () => {
    const [top, foot] = typeof at === "function" ? at() : at;
    return { top, bottom: foot, left: 0, right: 300, x: 0, y: top, width: 300, height: foot - top, toJSON: () => ({}) };
  };
}

/** A press as a browser counts it: the first of its kind, or the second of a double press. */
const press = (count: number) => new MouseEvent("click", { bubbles: true, cancelable: true, detail: count });

interface Page {
  readonly pressed: HTMLButtonElement;
  readonly opened: HTMLDivElement;
  readonly inside: HTMLButtonElement;
  /** How far the window was asked to scroll, each time it was. */
  readonly asked: number[];
}

/** A button, and under it what the button opened, which holds a button of its own. */
function aPage(holds: HTMLElement = document.body): Page {
  const pressed = document.createElement("button");
  const opened = document.createElement("div");
  const inside = document.createElement("button");
  opened.append(inside);
  holds.append(pressed, opened);
  const asked: number[] = [];
  jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
    asked.push(y);
  }) as typeof window.scrollBy);
  return { pressed, opened, inside, asked };
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
  Object.defineProperty(window, "innerHeight", { configurable: true, value: 844 });
});

afterEach(() => {
  document.body.replaceChildren();
  jest.useRealTimers();
});

describe("what a press opens, brought into sight", () => {
  test("test_what_opens_under_the_foot_of_the_window_is_brought_up_by_its_head_and_no_further", () => {
    // Seen on a phone 844 px high: "Try an example" stood from 747 to 791, and what it
    // opened from 855 to 1,211. The button turned amber, and nothing else was seen to happen.
    // Then the whole of it was brought into sight, and the button went 375 px from under
    // the finger. Its head is what must be seen: that it opened, and where to read on.
    const { pressed, opened, asked } = aPage();
    stand(pressed, [747, 791]);
    stand(opened, [855, 1211]);

    const moved = bringIntoSight(opened, pressed);

    expect(asked).toEqual([855 + HEAD - 844]);
    expect(moved).toBe(11 + HEAD);
  });

  test("test_what_is_whole_and_in_sight_is_left_where_it_is", () => {
    const { pressed, opened, asked } = aPage();
    stand(pressed, [300, 344]);
    stand(opened, [356, 700]);

    expect(bringIntoSight(opened, pressed)).toBe(0);
    expect(asked).toEqual([]);
  });

  test("test_where_the_head_of_what_opened_is_in_sight_nothing_is_moved", () => {
    // Seen at 1440 by 900: "Refine search" was pressed at 764, and the settings it opened
    // began at 823, with 77 px of them in sight: their name and the start of what they say.
    // The page went 726 px all the same, and a sentence of the settings lay under the pointer.
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const { pressed, opened, asked } = aPage();
    stand(pressed, [764, 811]);
    stand(opened, [823, 2845]);

    expect(bringIntoSight(opened, pressed)).toBe(0);

    // And where they began at 685, under what says that areas can be compared: 215 px of
    // them were in sight, ten short of a quarter of the window, and the page went 597.
    stand(pressed, [604.5, 651.5]);
    stand(opened, [685, 3089]);
    expect(bringIntoSight(opened, pressed)).toBe(0);
    expect(asked).toEqual([]);
  });

  test("test_the_head_is_in_sight_by_as_much_as_a_line_and_the_edge_over_it", () => {
    const { pressed, opened, asked } = aPage();
    stand(pressed, [324, 368]);

    // Its head, to the pixel: nothing is moved.
    stand(opened, [844 - HEAD, 3000]);
    expect(bringIntoSight(opened, pressed)).toBe(0);
    // One pixel less of it in sight, and the page goes by that pixel.
    stand(opened, [844 - HEAD + 1, 3000]);
    expect(bringIntoSight(opened, pressed)).toBe(1);
    expect(asked).toEqual([1]);
  });

  test("test_what_was_pressed_is_moved_by_a_few_pixels_where_a_few_are_missing", () => {
    // Seen at 1440 by 900: "Try an example" stood from 793.5 to 844.5 and was pressed at its
    // middle, and what it opened began at 856.5, with 43.5 px of it in sight. The page went
    // 274 px, and the third example lay under the pointer, in hand: a second press put it in
    // the box. Moved by what is missing of the head, the button is still under the pointer.
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const { pressed, opened, asked } = aPage();
    stand(pressed, [793.5, 844.5]);
    stand(opened, [856.5, 1184.5]);

    const moved = bringIntoSight(opened, pressed);

    expect(moved).toBe(HEAD - 43.5);
    expect(asked).toEqual([HEAD - 43.5]);
    // The middle of the button, where it was pressed, is still on the button.
    expect(793.5 - moved).toBeLessThan(819);
    expect(844.5 - moved).toBeGreaterThan(819);
  });

  test("test_what_is_shorter_than_a_head_is_brought_into_sight_whole_with_a_little_room_under_it", () => {
    const { pressed, opened, asked } = aPage();
    stand(pressed, [780, 824]);
    stand(opened, [836, 866]);

    bringIntoSight(opened, pressed);

    expect(asked).toEqual([866 + 8 - 844]);
  });

  test("test_what_was_pressed_is_never_taken_over_the_top_of_the_window", () => {
    // A window so low that the head of what opened cannot stand under what was pressed:
    // what was pressed stays in sight, at the top, and what it opened begins under it.
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 60 });
    const { pressed, opened, asked } = aPage();
    stand(pressed, [20, 64]);
    stand(opened, [76, 3000]);

    bringIntoSight(opened, pressed);

    expect(asked).toEqual([20 - 8]);
  });

  test("test_nothing_is_moved_for_what_holds_nothing_or_begins_over_the_top", () => {
    const { pressed, opened, asked } = aPage();
    stand(pressed, [747, 791]);
    stand(opened, [855, 855]);
    expect(bringIntoSight(opened, pressed)).toBe(0);

    // A person who has read down into what is open is not taken back to the start of it.
    stand(pressed, [-600, -556]);
    stand(opened, [-544, 1200]);
    expect(bringIntoSight(opened, pressed)).toBe(0);
    expect(asked).toEqual([]);
  });

  test("test_in_a_box_that_scrolls_in_itself_the_box_is_scrolled_and_the_page_is_not", () => {
    // Seen at 1440 by 900: the column of the map stood from 16 to 884 and scrolled in
    // itself. "Table of all areas" stood at its foot, from 833 to 880, and the table it
    // opened began at 896, under the foot of the column.
    const column = aBoxThatScrolls([16, 884], 6685);
    const { pressed, opened, asked } = aPage(column);
    stand(pressed, [833, 880]);
    stand(opened, [896, 6659]);
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });

    const moved = bringIntoSight(opened, pressed);

    // The head of the table is brought over the foot of the column, and the page stays.
    expect(moved).toBe(896 + HEAD - 884);
    expect(column.scrollTop).toBe(12 + HEAD);
    expect(asked).toEqual([]);
  });

  test("test_a_box_that_holds_no_more_than_it_shows_is_no_box_that_scrolls", () => {
    const column = aBoxThatScrolls([16, 884], 868);
    const { pressed, opened, asked } = aPage(column);
    stand(pressed, [747, 791]);
    stand(opened, [855, 1211]);

    bringIntoSight(opened, pressed);

    expect(column.scrollTop).toBe(0);
    expect(asked).toEqual([855 + HEAD - 844]);
  });
});

describe("the second press of a double press, once the page has moved", () => {
  test("test_it_lands_on_nothing_of_what_was_brought_under_it", () => {
    // What was pressed has gone up, and what it opened stands where it stood. A second
    // press that follows at once was aimed at what was pressed, and is no press on what
    // now stands there.
    const { pressed, opened, inside } = aPage();
    stand(pressed, [747, 791]);
    stand(opened, [855, 1211]);
    const heard = jest.fn();
    inside.addEventListener("click", heard);
    bringIntoSight(opened, pressed);

    const second = press(2);
    inside.dispatchEvent(second);

    expect(heard).not.toHaveBeenCalled();
    // A link among what was opened is not followed by it either.
    expect(second.defaultPrevented).toBe(true);
  });

  test("test_a_press_of_its_own_lands_at_once", () => {
    const { pressed, opened, inside } = aPage();
    stand(pressed, [747, 791]);
    stand(opened, [855, 1211]);
    const heard = jest.fn();
    inside.addEventListener("click", heard);
    bringIntoSight(opened, pressed);

    inside.dispatchEvent(press(1));
    // A press by keyboard is counted as none.
    inside.dispatchEvent(press(0));

    expect(heard).toHaveBeenCalledTimes(2);
  });

  test("test_a_double_press_lands_once_the_time_of_one_has_passed", () => {
    jest.useFakeTimers();
    const { pressed, opened, inside } = aPage();
    stand(pressed, [747, 791]);
    stand(opened, [855, 1211]);
    const heard = jest.fn();
    inside.addEventListener("click", heard);
    bringIntoSight(opened, pressed);

    jest.advanceTimersByTime(DOUBLE_PRESS_MS);
    inside.dispatchEvent(press(2));

    expect(heard).toHaveBeenCalledTimes(1);
  });

  test("test_where_nothing_moved_every_press_lands", () => {
    const { pressed, opened, inside } = aPage();
    stand(pressed, [300, 344]);
    stand(opened, [356, 700]);
    const heard = jest.fn();
    inside.addEventListener("click", heard);
    bringIntoSight(opened, pressed);

    inside.dispatchEvent(press(2));

    expect(heard).toHaveBeenCalledTimes(1);
  });
});

describe("what an answer brought, brought into sight whole", () => {
  /** The field a person typed in, and under it what was said of the search they sent. */
  function aBox() {
    const { pressed: field, opened: said, inside, asked } = aPage();
    return { field, said, inside, asked };
  }

  test("test_what_is_said_under_the_foot_of_the_window_is_brought_up_until_the_whole_of_it_is_in_sight", () => {
    // Seen on a phone 844 px high, with the service out of reach: the field stood from 708
    // to 779, and what said that Burro could not be reached would stand from 790 to 946
    // under it, with the way to try again at its foot.
    const { field, said, asked } = aBox();
    stand(field, [708, 779]);
    stand(said, [790, 946]);

    const moved = bringWholeIntoSight(said, field);

    expect(asked).toEqual([946 + 8 - 844]);
    expect(moved).toBe(110);
  });

  test("test_no_room_that_is_kept_at_the_foot_of_the_window_for_something_else_moves_it_further", () => {
    // A browser that is asked to bring a thing into sight keeps the room the page has it
    // keep at the foot of the window, for the bar of areas to compare: 176 px. Asked so,
    // the page went 147 px at 1440 by 900 for a notice that was whole and in sight.
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const { field, said, asked } = aBox();
    stand(field, [648, 721]);
    stand(said, [737, 871]);

    expect(bringWholeIntoSight(said, field)).toBe(0);
    expect(asked).toEqual([]);
  });

  test("test_the_field_is_never_taken_over_the_top_for_it", () => {
    // Where what is said is higher than the window has room for under the field, the field
    // stays in sight, at the top, and what is said begins under it.
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 300 });
    const { field, said, asked } = aBox();
    stand(field, [120, 191]);
    stand(said, [202, 702]);

    bringWholeIntoSight(said, field);

    expect(asked).toEqual([120 - 8]);
  });

  test("test_with_nothing_to_keep_in_sight_its_own_head_is_never_taken_over_the_top", () => {
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 300 });
    const { said, asked } = aBox();
    stand(said, [202, 702]);

    bringWholeIntoSight(said);

    expect(asked).toEqual([202 - 8]);
  });

  test("test_nothing_is_moved_for_what_holds_nothing_or_is_whole_and_in_sight_or_begins_over_the_top", () => {
    const { field, said, asked } = aBox();
    stand(field, [300, 371]);
    stand(said, [382, 382]);
    expect(bringWholeIntoSight(said, field)).toBe(0);
    stand(said, [382, 538]);
    expect(bringWholeIntoSight(said, field)).toBe(0);
    stand(field, [-400, -329]);
    stand(said, [-318, 1200]);
    expect(bringWholeIntoSight(said, field)).toBe(0);
    expect(asked).toEqual([]);
  });

  test("test_a_second_press_of_a_double_press_lands_on_nothing_of_what_was_brought_under_it", () => {
    // Search was pressed, and what tries again may stand where it stood.
    const { field, said, inside } = aBox();
    stand(field, [708, 779]);
    stand(said, [790, 946]);
    const heard = jest.fn();
    inside.addEventListener("click", heard);

    bringWholeIntoSight(said, field);
    inside.dispatchEvent(press(2));
    inside.dispatchEvent(press(1));

    expect(heard).toHaveBeenCalledTimes(1);
  });
});

describe("where what a press opens stands, so that it is in sight and what was pressed stays under the hand", () => {
  /** The line that holds what is pressed, and what a press opened, which stands under it. */
  function aLine(holds: HTMLElement = document.body) {
    const { pressed: line, opened, asked } = aPage(holds);
    return { line, opened, asked };
  }
  const GAP = 12;

  test("test_one_line_of_the_look_chooses_and_it_stands_where_there_is_room_for_it", () => {
    expect(OPENS).toEqual(["room", "under"]);
    expect(WHAT_A_PRESS_OPENS).toBe("room");
  });

  test("test_where_the_whole_of_it_has_room_under_what_was_pressed_it_stands_there", () => {
    const { line, opened } = aLine();
    stand(line, [300, 344]);
    stand(opened, [344 + GAP, 344 + GAP + 338]);

    expect(sideWithRoom({ top: 300, bottom: 344 }, line, opened, "under")).toBe("under");
    // To the pixel: its foot, and a little room under it, at the foot of the window.
    stand(line, [442, 486]);
    stand(opened, [498, 836]);
    expect(sideWithRoom({ top: 442, bottom: 486 }, line, opened, "under")).toBe("under");
    stand(line, [443, 487]);
    stand(opened, [499, 837]);
    expect(sideWithRoom({ top: 443, bottom: 487 }, line, opened, "under")).toBe("over");
  });

  test("test_where_it_has_no_room_under_and_has_room_over_it_stands_over", () => {
    // Measured at 1440 by 900: "Try an example" was pressed at 793, and what it opened was
    // 310 px high, of which 43 px were in sight. Over the line there were 793 px.
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const { line, opened } = aLine();
    stand(line, [793, 844]);
    stand(opened, [856, 1166]);

    expect(sideWithRoom({ top: 793, bottom: 844 }, line, opened, "under")).toBe("over");
  });

  test("test_where_it_has_room_neither_way_it_stands_under_as_everything_that_opens_does", () => {
    // A card 1,170 px high, on a phone: it is higher than the window.
    const { line, opened } = aLine();
    stand(line, [600, 780]);
    stand(opened, [792, 1962]);

    expect(sideWithRoom({ top: 600, bottom: 780 }, line, opened, "under")).toBe("under");
    // And what is pressed near the top of the window has no room over it.
    stand(line, [100, 144]);
    stand(opened, [156, 1000]);
    expect(sideWithRoom({ top: 100, bottom: 144 }, line, opened, "under")).toBe("under");
  });

  test("test_it_is_measured_where_it_stands_whichever_side_that_is_and_held_to_where_the_line_stood_at_the_press", () => {
    // What is open stands over the line, and another is opened in its place: the line has
    // gone down the window by as much as the second is higher, and is measured where it
    // stood as it was pressed, which is where it will stand.
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const { line, opened } = aLine();
    stand(opened, [431, 809]);
    stand(line, [821, 872]);

    expect(sideWithRoom({ top: 793, bottom: 844 }, line, opened, "over")).toBe("over");
    // One that is higher than the room over the line stands under it.
    stand(opened, [0, 800]);
    stand(line, [812, 863]);
    expect(sideWithRoom({ top: 793, bottom: 844 }, line, opened, "over")).toBe("under");
  });

  test("test_what_holds_nothing_stands_under", () => {
    const { line, opened } = aLine();
    stand(line, [793, 844]);
    stand(opened, [856, 856]);

    expect(sideWithRoom({ top: 793, bottom: 844 }, line, opened, "under")).toBe("under");
  });

  test("test_in_a_box_that_scrolls_in_itself_the_room_is_the_room_of_the_box", () => {
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const column = aBoxThatScrolls([16, 884], 6685);
    const { line, opened } = aLine(column);
    stand(line, [540, 584]);
    stand(opened, [596, 896]);

    // The window has room under it, and the box has not.
    expect(sideWithRoom({ top: 540, bottom: 584 }, line, opened, "under")).toBe("over");
  });

  test("test_the_line_is_kept_where_it_stood_by_moving_the_page_by_as_much_as_it_went", () => {
    const { line, asked } = aLine();
    stand(line, [1131, 1182]);

    expect(keepInPlace(line, 793)).toBe(338);
    expect(asked).toEqual([338]);
    // Back, as what stood over it closes.
    stand(line, [455, 506]);
    expect(keepInPlace(line, 793)).toBe(-338);
    expect(asked).toEqual([338, -338]);
  });

  test("test_nothing_is_moved_for_what_stands_where_it_stood", () => {
    const { line, asked } = aLine();
    stand(line, [793, 844]);

    expect(keepInPlace(line, 793)).toBe(0);
    expect(keepInPlace(line, 793.4)).toBe(0);
    expect(asked).toEqual([]);
  });

  test("test_in_a_box_that_scrolls_in_itself_the_box_is_scrolled_to_keep_it", () => {
    const column = aBoxThatScrolls([16, 884], 6685);
    const { line, asked } = aLine(column);
    stand(line, [700, 744]);

    expect(keepInPlace(line, 400)).toBe(300);
    expect(column.scrollTop).toBe(300);
    expect(asked).toEqual([]);
  });
});
