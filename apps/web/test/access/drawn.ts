/**
 * What a browser does with the focus that jsdom does not, for a test that says where the
 * focus is left.
 *
 * A browser hands the focus to nothing that is not drawn. A control that is hidden, or that
 * stands in a part that is, is asked in vain: the focus stays where it was. jsdom lays
 * nothing out, and hands the focus to whatever is asked. So a test that reads where the
 * focus is would say what no browser does, where the page asks a thing that is not drawn.
 *
 * Seen in Chrome on 2026-09-26, at 1440 by 900 and at 390 by 844, before a search, in the
 * second way in: with a group of the settings closed by Escape, a second Escape and a third
 * left the focus on the bar of that group. The fold that holds the settings is held open
 * there and its button is not drawn: it is asked to take the focus, and cannot.
 */

/**
 * From now until the test ends, the focus goes only to what is drawn, as it does in a
 * browser: what is hidden, or stands in what is hidden, does not take it. It is set back
 * when the test ends, by the rule that every stand-in is.
 */
export function focusGoesOnlyToWhatIsDrawn(): void {
  // It is called with the element it was asked of, and with what it was asked with.
  const hand = HTMLElement.prototype.focus;
  jest.spyOn(HTMLElement.prototype, "focus").mockImplementation(function focus(this: HTMLElement, options?: FocusOptions) {
    if (this.closest("[hidden]") !== null) return;
    hand.call(this, options);
  });
}

/**
 * True where the focus is on something a person can see it on: not on the page as a whole,
 * which is where a browser leaves it when what had it goes, and not on a thing that is not
 * drawn. A browser takes the focus from what comes to be hidden, and jsdom leaves it there:
 * so a focus that jsdom shows on what is hidden is a focus that a browser has lost.
 */
export function theFocusIsOnWhatIsDrawn(): boolean {
  const on = document.activeElement;
  return on !== null && on !== document.body && on.isConnected && on.closest("[hidden]") === null;
}
