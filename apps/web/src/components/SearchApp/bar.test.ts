import { HEIGHT_OF_THE_BAR, tellHowHigh } from "./bar";

/** A part with a bar held in it, which is as high as a test says: jsdom lays nothing out. */
function held(high: { now: number }) {
  const part = document.createElement("div");
  const bar = document.createElement("div");
  part.append(bar);
  document.body.append(part);
  bar.getBoundingClientRect = () => ({ height: high.now }) as DOMRect;
  return { part, bar, told: () => part.style.getPropertyValue(HEIGHT_OF_THE_BAR) };
}

/** What watches the size of a part, as a test stands in for it: it is told to look by the test. */
function watcher() {
  const watched: { look: () => void; of: Element[]; on: boolean }[] = [];
  const kept = (globalThis as { ResizeObserver?: unknown }).ResizeObserver;
  (globalThis as { ResizeObserver?: unknown }).ResizeObserver = class {
    private readonly one: (typeof watched)[number];
    constructor(look: () => void) {
      this.one = { look, of: [], on: true };
      watched.push(this.one);
    }
    observe(part: Element) {
      this.one.of.push(part);
    }
    disconnect() {
      this.one.on = false;
    }
  };
  return {
    watched,
    /** The size of what is watched changed: whatever still watches looks again. */
    changed: () => watched.filter((one) => one.on).forEach((one) => one.look()),
    gone: () => {
      (globalThis as { ResizeObserver?: unknown }).ResizeObserver = kept;
    },
  };
}

afterEach(() => {
  document.body.replaceChildren();
});

describe("how high the bar of the button is, told to the style sheet", () => {
  test("test_the_part_the_bar_is_held_in_is_told_how_high_the_bar_is_in_whole_pixels", () => {
    const { part, bar, told } = held({ now: 71.5 });

    tellHowHigh(bar);

    // Rounded up: a bar is never said to be lower than it is.
    expect(told()).toBe("72px");
    expect(HEIGHT_OF_THE_BAR).toBe("--bar-high");
    // It is told to the part, which holds what the bar is held over, and to nothing else.
    expect(bar.getAttribute("style")).toBeNull();
    expect(document.documentElement.getAttribute("style")).toBeNull();
    expect(part.style.length).toBe(1);
  });

  test("test_it_is_told_again_when_what_is_said_in_the_bar_makes_it_higher_or_lower", () => {
    const sizes = watcher();
    const high = { now: 72 };
    const { bar, told } = held(high);

    tellHowHigh(bar);
    expect(sizes.watched.map((one) => one.of)).toEqual([[bar]]);
    // A search could not be sent, and Burro says so over the button.
    high.now = 236;
    sizes.changed();
    expect(told()).toBe("236px");
    high.now = 72;
    sizes.changed();
    expect(told()).toBe("72px");

    sizes.gone();
  });

  test("test_a_bar_that_is_not_laid_out_tells_nothing_and_what_was_told_stands", () => {
    const sizes = watcher();
    const high = { now: 0 };
    const { bar, told } = held(high);

    tellHowHigh(bar);
    // Nothing is told, so the style sheet goes by what the bar was measured at.
    expect(told()).toBe("");
    high.now = 74;
    sizes.changed();
    expect(told()).toBe("74px");
    // The way it stands in is put away, and is not drawn: it has no height while it is.
    high.now = 0;
    sizes.changed();
    expect(told()).toBe("74px");

    sizes.gone();
  });

  test("test_let_go_of_nothing_watches_and_nothing_is_left_told", () => {
    const sizes = watcher();
    const high = { now: 74 };
    const { bar, told } = held(high);

    const letGo = tellHowHigh(bar);
    letGo();

    expect(told()).toBe("");
    expect(sizes.watched.map((one) => one.on)).toEqual([false]);
    high.now = 236;
    sizes.changed();
    expect(told()).toBe("");

    sizes.gone();
  });

  test("test_where_a_browser_watches_no_sizes_the_bar_is_told_once_as_it_is_drawn", () => {
    const kept = (globalThis as { ResizeObserver?: unknown }).ResizeObserver;
    Reflect.deleteProperty(globalThis, "ResizeObserver");
    const { bar, told } = held({ now: 74 });

    const letGo = tellHowHigh(bar);

    expect(told()).toBe("74px");
    letGo();
    expect(told()).toBe("");
    if (kept !== undefined) (globalThis as { ResizeObserver?: unknown }).ResizeObserver = kept;
  });

  test("test_a_bar_that_stands_in_nothing_tells_nothing", () => {
    const bar = document.createElement("div");

    expect(() => tellHowHigh(bar)()).not.toThrow();
  });
});
