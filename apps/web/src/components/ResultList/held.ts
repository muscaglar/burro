/**
 * What is pressed in a result stays under the hand.
 *
 * A browser holds a page where a person reads while something grows over it, and holds it
 * by the first thing in sight, in the order of the page. On a narrow screen what refines a
 * search comes before the first result in the page and is drawn after it. So once the box
 * had been scrolled out of the window, the first thing in sight, in the order of the page,
 * stood under the first result: the browser held the page by it, and whatever a press
 * opened in the first result sent the page down by as much as it opened. Seen on a phone:
 * "Show the working" took the page 1,634 px down, and the button that was pressed stood
 * 1,518 px over the top of the window.
 *
 * So the list holds what was pressed itself. It is measured as the press lands, and once
 * what the press opened is laid out, before anything is drawn, the page is put back by as
 * much as what was pressed went. Whatever moved it, it stands where it stood.
 *
 * It is done of a press that opens or closes something in place, and of no other: a press
 * that leads elsewhere, as "Show on the map" does, takes the page where it leads.
 */

/**
 * What opens or closes in place, in a result: the working, and in it the key of a source
 * and what opens how the fit is worked out, each of which says whether what it opens is
 * open, and the way to compare, which says whether its area is chosen.
 */
const OPENS_IN_PLACE = "button[aria-expanded], [data-chosen] > button";

/** Less than this is how a browser rounds where a thing stands, and is not seen. */
const SEEN = 0.5;

const topOf = (part: Element) => part.getBoundingClientRect().top;

/** What a press was made on, where it opens or closes something in place inside what holds it. `null` of any other press. */
export function pressedIn(holds: Element, on: EventTarget | null): Element | null {
  const pressed = on instanceof Element ? on.closest(OPENS_IN_PLACE) : null;
  return pressed !== null && holds.contains(pressed) ? pressed : null;
}

/**
 * Puts the page back by as much as what was pressed went from where it stood, and says by
 * how much: nought where it stands where it stood, or went from the page with its press.
 */
export function putBack(pressed: Element, stood: number): number {
  if (!pressed.isConnected) return 0;
  const by = topOf(pressed) - stood;
  if (Math.abs(by) < SEEN) return 0;
  // At once, whatever the page says of how it scrolls: a page that glided back would be seen to go and to come.
  window.scrollBy({ top: by, left: 0, behavior: "instant" });
  return by;
}

/**
 * Holds what was pressed where it stands in the window, from now until what the press
 * opened has been laid out. It is called as the press lands, before anything has changed.
 *
 * What a press opens is on the page by the next frame, and the frame is not drawn until
 * this has run: so the page is never seen anywhere but where it was. It is looked at once
 * more in the frame after, for a browser that lays the page out later than that.
 */
export function hold(pressed: Element): void {
  const stood = topOf(pressed);
  requestAnimationFrame(() => {
    putBack(pressed, stood);
    requestAnimationFrame(() => putBack(pressed, stood));
  });
}

/**
 * True where a part stays in the window as the page is scrolled to where it would stand
 * with another part brought into view. The page is taken there and back at once, before
 * anything is drawn, and the part is measured at both: a box that sticks goes with the
 * page until it comes to rest, and only the browser knows where that is.
 */
function staysAs(chosen: Element, part: Element): boolean {
  const from = { top: window.scrollY, left: window.scrollX };
  const stood = topOf(part);
  chosen.scrollIntoView({ block: "nearest", behavior: "instant" });
  const went = Math.abs(topOf(part) - stood) >= SEEN;
  window.scrollTo({ ...from, behavior: "instant" });
  return !went;
}

/**
 * Brings a result that was chosen elsewhere into view, as on the map, where that leaves
 * what was pressed where it stands, and says whether it did.
 *
 * Beside the list the map stays in the window as the page scrolls, once it has come to
 * rest at its head: the list then goes to the result, and the pin that was pressed stays
 * under the hand. On a narrow screen the map is over the list or under it, and goes with
 * the page. Seen on a phone: a pin that was pressed went 1,108 px up and out of the window,
 * and the card of the map with it. There the page is left where it is: the result is
 * marked as chosen, and "Show in the list" is the press that goes to it.
 *
 * Where the press was made in the list itself, as "Show on the map" is, the result is
 * where the person is, and the page is taken to the map by what draws the page. Brought
 * back to the result, the map was out of sight again.
 */
export function bringBeside(list: Element, chosen: Element, pressed: Element | null, glides: boolean): boolean {
  if (typeof chosen.scrollIntoView !== "function") return false;
  // Nothing is known of what was pressed: the page is left where it is.
  if (pressed === null || pressed === document.body || !pressed.isConnected) return false;
  if (list.contains(pressed) || chosen.contains(pressed)) return false;
  if (!staysAs(chosen, pressed)) return false;
  chosen.scrollIntoView({ block: "nearest", behavior: glides ? "smooth" : "auto" });
  return true;
}
