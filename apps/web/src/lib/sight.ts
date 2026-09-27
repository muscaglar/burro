/**
 * What a press opens is brought into sight, and what was pressed stays under the hand.
 *
 * What a press opens stands under what was pressed. Where that stands at the foot of the
 * window, or of a box that scrolls in itself, what it opened began under the foot of it:
 * the button turned amber, and nothing else was seen to happen. Seen in a browser, on a
 * phone 844 px high, of each of the helpers under the box: and at 1440 by 900 of the
 * table of all areas, which opened under the foot of the column of the map.
 *
 * So what was opened is brought up, by the press and at once, and only as far as it must
 * be: until its head is in sight, which is as much of it as shows that it opened and
 * where to read on. Where its head is in sight already nothing is moved, and what was
 * pressed stays where the hand is. The rest of it is the person's to scroll to. It is
 * scrolled in what it is seen through: the box that holds it, where one scrolls in
 * itself, and the window where none does.
 *
 * It was once brought up until the whole of it was in sight, or what was pressed stood at
 * the top. Seen at 1440 by 900: "Refine search" was pressed at 764 and went to 38, and an
 * example was pressed where its helper had been. A press lands where it was aimed, so the
 * page goes by no more than it must.
 *
 * Where the page is moved, what was pressed has gone from under the pointer by as much,
 * and something of what it opened may stand there. A second press that follows at once,
 * as the second of a double press does, was aimed at what was pressed: for as long as a
 * browser may count it so, it lands on nothing of what was opened. A press of its own
 * lands at once, and so does a key.
 *
 * Both were asked for at once: that what a press opens is in sight, whole where it fits,
 * and that what was pressed stays under the hand. Under what was pressed the two part
 * wherever that stands low in the window. So what a hand opens stands where there is room
 * for the whole of it: under what was pressed, or over it, where it has room there and
 * none under. What stands over pushes what was pressed down the page, and the page goes
 * on by as much, before anything is drawn: what was pressed stands where it stood, and
 * what it opened is whole and in sight over it. Where it has room neither way it stands
 * under, and its head is brought into sight.
 *
 * Some presses lead elsewhere. "Show on the map" is pressed in the working of a result or
 * in a row of the table of all areas, and what it opens is the box of the area under the
 * map, which may stand a long way off. What was pressed must then go from under the hand,
 * so that what it opened is in sight. It goes once, by as little as brings the map into
 * sight with the box under it, which is where a person looks for both: and not at all
 * where both are in sight already.
 *
 * And what a press closes may have held the room that what was pressed stood in. A box
 * that scrolls in itself holds less once a table in it has closed, and a browser scrolls
 * it back as far as it must: the bar that was pressed went to the foot of the box. So the
 * box keeps the room of what closed, at its foot, for as long as it stands scrolled into
 * that room, and gives it up as a person scrolls back.
 */

/** The room kept clear between what is brought into sight and the edge it is brought to, in pixels. */
const CLEAR = 8;

/**
 * The head of what a press opened, in pixels: the edge over it and its first line, which
 * is two lines of the face of a sentence high. It is what must be in sight of it.
 */
export const HEAD = 48;

/** How long after a press a browser may still count the next one as the second of a double press. */
export const DOUBLE_PRESS_MS = 500;

/** The box a part is seen through, where one that holds it scrolls in itself. `null` where it is the window. */
function seenThrough(part: HTMLElement): HTMLElement | null {
  for (let holds = part.parentElement; holds !== null && holds !== document.body; holds = holds.parentElement) {
    const { overflowY } = getComputedStyle(holds);
    if ((overflowY === "auto" || overflowY === "scroll") && holds.scrollHeight > holds.clientHeight) return holds;
  }
  return null;
}

/**
 * A press the browser counts as the second or a later one of a double press lands on
 * nothing here, for a moment. Nor does what a browser says of the two presses as one: a
 * map is drawn nearer by it.
 */
export function holdOffTheSecondPress(opened: HTMLElement): void {
  const stop = (event: MouseEvent) => {
    if (event.detail < 2) return;
    event.preventDefault();
    event.stopPropagation();
  };
  // Heard on the way down, before whatever was pressed hears of it.
  opened.addEventListener("click", stop, true);
  opened.addEventListener("dblclick", stop, true);
  setTimeout(() => {
    opened.removeEventListener("click", stop, true);
    opened.removeEventListener("dblclick", stop, true);
  }, DOUBLE_PRESS_MS);
}

/**
 * Brings the head of what a press opened into sight, where it is not, and says how far it
 * was moved: nought where nothing was. It is called once what was opened is on the page,
 * and before the page is drawn, so that it is first seen where it will stand.
 */
export function bringIntoSight(opened: HTMLElement, pressed: HTMLElement): number {
  const box = seenThrough(opened);
  const edges = box?.getBoundingClientRect();
  const top = Math.max(0, edges?.top ?? 0);
  const foot = Math.min(window.innerHeight, edges?.bottom ?? window.innerHeight);
  const held = opened.getBoundingClientRect();
  // What holds nothing has nothing to show. What begins over the top is being read already.
  if (held.bottom <= held.top || held.top < top) return 0;
  // Its head, or the whole of what is shorter than one, with a little room under it.
  const seen = Math.min(HEAD, held.bottom - held.top + CLEAR);
  const missing = held.top + seen - foot;
  if (missing <= 0) return 0;
  // What was pressed is never taken over the top of what it is seen through.
  const by = Math.min(missing, pressed.getBoundingClientRect().top - CLEAR - top);
  if (by <= 0) return 0;
  if (box === null) window.scrollBy(0, by);
  else box.scrollTop += by;
  holdOffTheSecondPress(opened);
  return by;
}

/**
 * Brings the whole of what an answer brought into sight, where it is not, and says how
 * far it was moved: nought where nothing was. What says that a search failed is what a
 * person came to read, with the way to try again at its foot, so the whole of it is
 * brought up, as far as it must be and no further. The press that asked for it has
 * landed by then.
 *
 * It asks the window by how much, and asks no browser to bring the thing into sight: a
 * browser keeps the room the page has it keep at the foot of the window for the bar of
 * areas to compare, and moved the page for what was whole and in sight.
 *
 * `keeps` is what is never taken over the top for it: the field a person typed in. Left
 * out, its own head is never taken over the top.
 */
export function bringWholeIntoSight(brought: HTMLElement, keeps: HTMLElement | null = null): number {
  const box = seenThrough(brought);
  const edges = box?.getBoundingClientRect();
  const top = Math.max(0, edges?.top ?? 0);
  const foot = Math.min(window.innerHeight, edges?.bottom ?? window.innerHeight);
  const held = brought.getBoundingClientRect();
  if (held.bottom <= held.top || held.top < top) return 0;
  const missing = held.bottom + CLEAR - foot;
  if (missing <= 0) return 0;
  const by = Math.min(missing, (keeps ?? brought).getBoundingClientRect().top - CLEAR - top);
  if (by <= 0) return 0;
  if (box === null) window.scrollBy(0, by);
  else box.scrollTop += by;
  holdOffTheSecondPress(brought);
  return by;
}

/** The side of what was pressed that what it opened stands on. */
export type Side = "under" | "over";

/**
 * Where what a press opens stands. It is the founder's to choose.
 *
 * `room`: what a hand opens stands where the whole of it has room, under what was pressed
 * or over it, and what was pressed stays where it was pressed. What the keys open stands
 * under, as everything that opens does for whoever goes by the order of the page, and the
 * whole of it is brought into sight: no hand is on what was pressed.
 *
 * `under`: it stands under what was pressed, always, and its head is brought into sight.
 * What was pressed at the foot of the window goes up by as much, from under the hand.
 */
export type Opens = "room" | "under";

export const OPENS: readonly Opens[] = ["room", "under"];

/** This is the one line that chooses. */
export const WHAT_A_PRESS_OPENS: Opens = "room";

/**
 * The side that has room for the whole of what a press opened: under the line that holds
 * what was pressed, where it has room there, over it where it has room there alone, and
 * under where it has room neither way. `stood` is where the line stood as it was pressed,
 * which is where it is to stand. What was opened is measured where it now stands, on the
 * side `stands`, with the room that parts it from the line.
 */
export function sideWithRoom(
  stood: { readonly top: number; readonly bottom: number },
  line: HTMLElement,
  opened: HTMLElement,
  stands: Side,
): Side {
  const edges = seenThrough(line)?.getBoundingClientRect();
  const top = Math.max(0, edges?.top ?? 0);
  const foot = Math.min(window.innerHeight, edges?.bottom ?? window.innerHeight);
  const held = opened.getBoundingClientRect();
  if (held.bottom <= held.top) return "under";
  const at = line.getBoundingClientRect();
  const parted = Math.max(0, stands === "over" ? at.top - held.bottom : held.top - at.bottom);
  const needs = held.bottom - held.top + parted + CLEAR;
  if (stood.bottom + needs <= foot) return "under";
  return stood.top - needs >= top ? "over" : "under";
}

/**
 * Keeps a part where it stood in the window, by moving the page, or the box the part is
 * seen through, by as much as the part has gone. It says how far that was: nought where
 * the part stands where it stood.
 */
export function keepInPlace(part: HTMLElement, stoodAt: number): number {
  const by = part.getBoundingClientRect().top - stoodAt;
  if (Math.abs(by) < 1) return 0;
  const box = seenThrough(part);
  if (box === null) window.scrollBy(0, by);
  else box.scrollTop += by;
  return by;
}

/**
 * Brings what a press elsewhere led to into sight with what it stands under, and says how
 * far it moved what they are seen through: nought where nothing was moved, and less than
 * nought where it went back. The box of an area stands under the map, and a press that
 * asks for an area to be shown on the map is answered by both.
 *
 * Where both have room they are both brought into sight, by as little as must be: the head
 * of what stands over to the top, where it began over it, and else the foot of what was
 * brought to the foot. Where they have not, what was brought is shown whole, with as much
 * over it as has room. What is higher than the room there is, is shown from its head.
 *
 * `held` is what is held at the foot of the window, as the bar of areas to compare is once
 * an area is chosen: nothing is left under it. It asks no browser to bring a thing into
 * sight: a browser keeps the room of that bar clear whether or not the bar is there.
 */
export function bringIntoSightUnder(over: HTMLElement, brought: HTMLElement, held: HTMLElement | null = null): number {
  const box = seenThrough(brought);
  const edges = box?.getBoundingClientRect();
  const bar = held?.getBoundingClientRect();
  const floor = bar !== undefined && bar.bottom > bar.top ? Math.min(window.innerHeight, bar.top) : window.innerHeight;
  const top = Math.max(0, edges?.top ?? 0) + CLEAR;
  const foot = Math.min(floor, edges?.bottom ?? floor) - CLEAR;
  const { top: head, bottom: end } = brought.getBoundingClientRect();
  if (end <= head) return 0;
  const room = foot - top;
  const begins = Math.min(head, over.getBoundingClientRect().top);
  // What is to be in sight: from the head of what stands over it, where both have room.
  const first = end - begins <= room ? begins : Math.min(head, end - room);
  const by = first < top ? first - top : Math.max(0, Math.min(end - foot, first - top));
  if (by === 0) return 0;
  if (box === null) window.scrollBy(0, by);
  else box.scrollTop += by;
  return by;
}

/** Where what is about to close what it opened stands, and how far what it is seen through is scrolled. */
export interface Stood {
  readonly pressed: HTMLElement;
  readonly top: number;
  /** The box it is seen through, where one that holds it scrolls in itself. `null` where it is the window. */
  readonly box: HTMLElement | null;
  readonly scrolled: number;
}

/** Where a thing stands as it is pressed, before what the press does is drawn. */
export function standsAt(pressed: HTMLElement): Stood {
  const box = seenThrough(pressed);
  return { pressed, top: pressed.getBoundingClientRect().top, box, scrolled: box?.scrollTop ?? 0 };
}

/**
 * Keeps what was pressed where it stood, once what it had opened has closed under it in a
 * box that scrolls in itself. The box keeps the room of what closed, at its foot, and is
 * scrolled to where it was. It is called once what closed is off the page, and before the
 * page is drawn.
 *
 * The room is given up as the box is scrolled back, by as much as has gone under its
 * foot: so none of it is seen to go, and nothing in sight moves for it. What it gives
 * back gives the whole of it up at once, as where what closed is opened again. It gives
 * back `null` where nothing was kept: what was pressed stands where it stood, or stands in
 * no box that scrolls in itself, where what follows it holds the page as long as it was.
 */
export function keepTheRoomOf(stood: Stood): (() => void) | null {
  const { pressed, box } = stood;
  if (box === null || !pressed.isConnected) return null;
  const went = pressed.getBoundingClientRect().top - stood.top;
  if (went < 1) return null;
  // What the box keeps at its foot already is its style sheet's, and is kept with the room.
  const own = Number.parseFloat(getComputedStyle(box).paddingBottom) || 0;
  let kept = went;
  const keep = () => {
    box.style.paddingBottom = kept > 0 ? `${own + kept}px` : "";
  };
  const scrolled = () => {
    const needed = Math.max(0, Math.ceil(box.scrollTop + box.clientHeight - (box.scrollHeight - kept)));
    if (needed >= kept) return;
    kept = needed;
    keep();
    if (kept === 0) box.removeEventListener("scroll", scrolled);
  };
  keep();
  box.scrollTop = stood.scrolled;
  box.addEventListener("scroll", scrolled, { passive: true });
  return () => {
    kept = 0;
    keep();
    box.removeEventListener("scroll", scrolled);
  };
}
