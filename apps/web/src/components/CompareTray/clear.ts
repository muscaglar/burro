/**
 * What was pressed is brought clear of the bar that came over it.
 *
 * The bar of areas to compare comes at the foot of the window with the press that chose
 * the first area, and is as high as a result's heading and more. Where the button that was
 * pressed stood in that band, the bar came over it: the button that held the focus could
 * not be seen, nor could what it then said, and the name and the fit that stood beside it
 * went under the bar with it. Measured at 1440 by 900, the bar is 124 px high, and at 390
 * by 844 it is 111.
 *
 * So what was pressed is brought up, by the press and at once, and only as far as it must
 * be: until it stands over the bar with a little room between the two. What stands beside
 * it on its line comes clear with it. What stood clear already is left where it is, so
 * that nothing moves under a press that the bar did not come over. It is scrolled in what
 * it is seen through: the box that holds it, where one scrolls in itself, and the window
 * where none does.
 *
 * What is brought under the pointer by it is the bar, and the foot of the button that was
 * pressed. The bar holds off a press that a browser counts as the second of a double
 * press, for as long as it may be counted so.
 *
 * What holds a list of results puts the page back where it stood in each of the two frames
 * after a press, so that what was pressed stays under the hand whatever grew over it. It
 * knows nothing of the bar: seen in a browser, the button was brought clear and stood under
 * the bar again in the next frame. So what was pressed is brought clear at once, and again
 * in each of those frames, after the page was put back and before it is drawn: it is never
 * seen under the bar.
 */

/** The room kept between what was pressed and the bar, in pixels: that of a ring of focus and its offset. */
export const OVER_THE_BAR = 8;

/** In how many frames after a press the page may be put back where it stood. */
export const FRAMES_HELD = 2;

/** The box a part is seen through, where one that holds it scrolls in itself. `null` where it is the window. */
function seenThrough(part: HTMLElement): HTMLElement | null {
  for (let holds = part.parentElement; holds !== null && holds !== document.body; holds = holds.parentElement) {
    const { overflowY } = getComputedStyle(holds);
    if ((overflowY === "auto" || overflowY === "scroll") && holds.scrollHeight > holds.clientHeight) return holds;
  }
  return null;
}

/**
 * The foot of the line that what was pressed stands on: its own foot, or that of what
 * stands beside it where that is lower. What stands beside it is what is laid out with
 * it, by whatever holds it, and meets it from top to foot. It counts for no more than the
 * height of what was pressed again: a drawing or a column beside a button may be as high as
 * the whole of a result.
 */
function footOfTheLine(pressed: HTMLElement): number {
  const own = pressed.getBoundingClientRect();
  // What holds the button, with whatever is said beside it, is laid out as one by what holds that.
  const laidOut = pressed.parentElement;
  const others = [...(laidOut?.parentElement?.children ?? [])].filter((one) => one !== laidOut);
  let foot = own.bottom;
  for (const other of others) {
    const { top, bottom } = other.getBoundingClientRect();
    if (bottom > top && top < own.bottom && bottom > own.top) foot = Math.max(foot, bottom);
  }
  return Math.min(foot, own.bottom + (own.bottom - own.top));
}

/**
 * Brings what was pressed clear of the bar, where the bar came over it, and says how far
 * it was moved: nought where nothing was. It is called once the bar is on the page as it
 * will stand, and before the page is drawn, so that what was pressed is first seen where
 * it will stand.
 */
export function bringClearOf(bar: HTMLElement | null, pressed: HTMLElement | null): number {
  if (bar === null || pressed === null || bar.contains(pressed)) return 0;
  const over = bar.getBoundingClientRect();
  const held = pressed.getBoundingClientRect();
  // A bar that draws nothing comes over nothing, and what is not laid out stands nowhere.
  if (over.bottom <= over.top || held.bottom <= held.top) return 0;
  // What stands under the foot of the bar follows it in the page: the bar is not over it.
  if (held.top >= over.bottom) return 0;
  const under = footOfTheLine(pressed) + OVER_THE_BAR - over.top;
  if (under <= 0) return 0;
  const box = seenThrough(pressed);
  const top = Math.max(0, box?.getBoundingClientRect().top ?? 0);
  // What was pressed is never taken over the top of what it is seen through.
  const by = Math.min(under, held.top - OVER_THE_BAR - top);
  if (by <= 0) return 0;
  if (box === null) window.scrollBy(0, by);
  else box.scrollTop += by;
  return by;
}

/**
 * Brings what was pressed clear of the bar at once, and again in each frame the page may
 * be put back in. A frame asked for here comes after one that was asked for as the press
 * landed, so that this has the last word of each. The bar is looked for each time. What
 * it gives back lets go of what was pressed: no frame that has not come moves the page.
 */
export function keepClearOf(bar: () => HTMLElement | null, pressed: HTMLElement | null): () => void {
  bringClearOf(bar(), pressed);
  let left = FRAMES_HELD;
  let next = 0;
  const again = () => {
    bringClearOf(bar(), pressed);
    left -= 1;
    if (left > 0) next = requestAnimationFrame(again);
  };
  next = requestAnimationFrame(again);
  return () => cancelAnimationFrame(next);
}
