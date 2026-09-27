/**
 * A window that lays out what opens in place, for a test. jsdom lays nothing out and
 * scrolls nothing, so a test that holds where a thing stands says how high each part is,
 * and this works out where each stands as a browser would: what is open stands over the
 * line that opens it where it comes before the line in the page, and under it where it
 * comes after. It is for tests, and no page draws anything of it.
 */

export interface Sizes {
  /** How high the window is. */
  readonly window: number;
  /** How far down the page the line begins, with nothing open over it. */
  readonly line: number;
  /** How high the line is: the buttons of the helpers, or the words of the shelf. */
  readonly lineHigh: number;
  /** How high what a press opens is. */
  readonly opens: number;
  /** The room that parts the line from what is open. */
  readonly parted?: number;
  /** How far the page is scrolled as the test begins. */
  readonly scrolled?: number;
}

export interface Parts {
  /** The line that holds what is pressed. */
  readonly line: () => Element | null;
  /** What is open, or `null` while nothing is. */
  readonly opened: () => Element | null;
}

export interface Laid {
  /** Every distance the page was asked to go, in turn. */
  readonly asked: number[];
  /** How far the page is scrolled. */
  readonly scrolled: () => number;
  /** Where a part stands in the window, from its top to its foot. */
  readonly stands: (part: Element | null) => readonly [number, number];
  /** True where what is open comes before the line in the page, and so stands over it. */
  readonly over: () => boolean;
  /** The person scrolls the page by so much. */
  readonly scrollBy: (by: number) => void;
  readonly putBack: () => void;
}

export function laidOut(sizes: Sizes, parts: Parts): Laid {
  const parted = sizes.parted ?? 12;
  const asked: number[] = [];
  let scrolled = sizes.scrolled ?? 0;
  const open = () => {
    const opened = parts.opened();
    return opened !== null && !opened.hasAttribute("hidden") && opened.childNodes.length > 0 ? opened : null;
  };
  const over = () => {
    const [opened, line] = [open(), parts.line()];
    return opened !== null && line !== null && Boolean(opened.compareDocumentPosition(line) & Node.DOCUMENT_POSITION_FOLLOWING);
  };
  const standsAt = (part: Element | null): readonly [number, number] => {
    const [opened, line] = [open(), parts.line()];
    if (part === null) return [0, 0];
    const lineTop = sizes.line + (over() ? sizes.opens + parted : 0) - scrolled;
    if (line !== null && (part === line || line.contains(part))) return [lineTop, lineTop + sizes.lineHigh];
    if (opened !== null && (part === opened || opened.contains(part))) {
      const top = over() ? sizes.line - scrolled : lineTop + sizes.lineHigh + parted;
      return [top, top + sizes.opens];
    }
    return [0, 0];
  };
  const high = Object.getOwnPropertyDescriptor(window, "innerHeight");
  Object.defineProperty(window, "innerHeight", { configurable: true, value: sizes.window });
  const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
    this: HTMLElement,
  ) {
    const [top, foot] = standsAt(this);
    return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
  });
  const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
    asked.push(y);
    scrolled = Math.max(0, scrolled + y);
  }) as typeof window.scrollBy);
  return {
    asked,
    scrolled: () => scrolled,
    stands: standsAt,
    over,
    scrollBy(by) {
      scrolled = Math.max(0, scrolled + by);
    },
    putBack() {
      measure.mockRestore();
      scroll.mockRestore();
      if (high) Object.defineProperty(window, "innerHeight", high);
    },
  };
}
