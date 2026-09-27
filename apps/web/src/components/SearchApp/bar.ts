/**
 * How high the bar is that holds the button of the second way in, told to the style sheet.
 *
 * The bar is held at the foot of the window, over the space requirements. A browser brings
 * what takes the focus clear of the foot of the window by the room the page keeps there,
 * and knows nothing of the bar: seen in a browser, with the bar held over the bar of areas
 * to compare, a field that took the focus by the keyboard stood under the button. How far
 * to bring it is how high the bar is, which grows with what Burro says in it: measured on
 * a phone 390 wide, 72 px with nothing said, and 236 with a search that could not be sent.
 *
 * So the bar is measured, and again whenever it grows or shrinks, and the part it is held
 * in is told. The style sheet does the rest, and until it is told it goes by what the bar
 * was measured at with nothing said in it.
 */

/** The name the style sheet knows the height of the bar by, in pixels. */
export const HEIGHT_OF_THE_BAR = "--bar-high";

/**
 * Tells the part a bar is held in how high the bar is, now and whenever that changes, and
 * gives back what lets go of it. A bar that is not laid out has no height to tell, and
 * what was told before stands.
 */
export function tellHowHigh(bar: HTMLElement): () => void {
  const part = bar.parentElement;
  if (part === null) return () => undefined;
  const tell = () => {
    const high = Math.ceil(bar.getBoundingClientRect().height);
    if (high > 0) part.style.setProperty(HEIGHT_OF_THE_BAR, `${high}px`);
  };
  tell();
  const watched = typeof ResizeObserver === "function" ? new ResizeObserver(tell) : null;
  watched?.observe(bar);
  return () => {
    watched?.disconnect();
    part.style.removeProperty(HEIGHT_OF_THE_BAR);
  };
}
