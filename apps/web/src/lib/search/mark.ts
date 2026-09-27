/**
 * How far into the box the search has read.
 *
 * Once a search is open the box says that what is typed is added to it. So what is sent
 * to be read is what stands in the box after the words the search has read, and never
 * those words a second time: read again, onto a search that was set by hand since, they
 * set it back to what they say. The service keeps nothing, and cannot tell words it has
 * read from new ones. The website can, by where they stand.
 *
 * The search has read the words that something came of: an edit, an offer or a question.
 * Words that were sent and that nothing came of are still to be read.
 *
 * Words that were read may be taken out of the box and come back into it: the keys that
 * undo put back what was taken out, and what is cut or copied is pasted. They are the words
 * that were read, and are not read again. Nothing holds the words to know them by, so they
 * are known by how they came and by how many of them there may be.
 *
 * Nothing here holds a word, or anything worked out from one. How far the search has read
 * is a count of the characters of the box, as the box counts them. Where the box was
 * changed is a count, and how much went and how much came are two more. They mean nothing
 * without the box, which alone holds what was typed.
 */

/** A place in the box that the search has read to. */
export interface Mark {
  /** How many characters of the box the search has read, counted from its start. */
  readonly to: number;
  /**
   * True when words before that place were changed in the box after they were read. Nothing
   * holds the words as they were, so nobody can say what was changed to what, and they are
   * not read again.
   */
  readonly changed: boolean;
}

export const NOTHING_READ: Mark = { to: 0, changed: false };

/**
 * How what came into the box came, where it had been in the box before: the keys that undo
 * put it back, or the keys that do again, or it was cut or copied from among what was read
 * and is pasted. One of three fixed names.
 */
export type How = "undone" | "redone" | "pasted";

/** Where the box was changed, and by how much. Never what went, and never what came. */
export interface Change {
  /** Where the change begins, counted from the start of the box. `null` where that cannot be told. */
  readonly at: number | null;
  /** How many characters went. */
  readonly out: number;
  /** How many came in their place. */
  readonly into: number;
  /** How many the box holds now. */
  readonly holds: number;
  /** How what came had been in the box before. Left out where it was typed, or pasted from elsewhere. */
  readonly how?: How;
}

/**
 * What the search knew of the box as it once stood, which the keys that undo, or that do
 * again, lead back to. Once they leave the box holding as many characters as it held then,
 * and have taken out as many as had come into it since, it holds what it held, and this is
 * so again.
 */
export interface Was {
  /** How many characters the box held. */
  readonly held: number;
  /**
   * How many characters have come into the box since, typed over what was taken out. The
   * keys that lead back take as many out. `null` where that is not known.
   */
  readonly came: number | null;
  readonly read: Mark;
  readonly sending: Mark | null;
  readonly before: Mark | null;
  readonly gone: number;
}

/** What the search knows of the box: counts, and whether a thing is so. */
export interface Box {
  /** How far into it the search has read. */
  readonly read: Mark;
  /**
   * Where the words that were last read begin. The service counts where words stand from
   * the start of what it was sent, which is from here. `null` once the box has changed:
   * where the words stand is known for what was sent, and for nothing else.
   */
  readonly shown: number | null;
  /** Where the words that are being read end, and whether they were changed meanwhile. `null` while none are. */
  readonly sending: Mark | null;
  /**
   * How far the search had read when the sentence that is being read was sent, for "Stop"
   * to put back with the search. `null` once the ranking of that sentence is in.
   */
  readonly before: Mark | null;
  /**
   * How many characters that were read have been taken out of the box since it was drawn.
   * The box keeps what is taken out of it, for the keys that undo to put back, and they put
   * it back where what was read ended. So once those keys are used, as many characters
   * after that place may be what was read, and are taken as read.
   */
  readonly gone: number;
  /**
   * What the keys that undo lead back to, the nearest last: the box as it stood before
   * words that were read were taken out of it, and before each press of the keys that do
   * again. Empty once anything else is done to the box, and once the search has moved on.
   */
  readonly back: readonly Was[];
  /** What the keys that do again lead to, the nearest last: the box as it stood before each press of the keys that undo. */
  readonly again: readonly Was[];
}

const NONE: readonly Was[] = [];

export const NO_BOX: Box = {
  read: NOTHING_READ,
  shown: null,
  sending: null,
  before: null,
  gone: 0,
  back: NONE,
  again: NONE,
};

/** No more is kept than a person presses those keys in a row. */
const KEPT = 64;
const onto = (kept: readonly Was[], one: Was): readonly Was[] => [...kept, one].slice(-KEPT);
const last = (kept: readonly Was[]): Was | undefined => kept[kept.length - 1];
const sameKept = (one: readonly Was[], other: readonly Was[]) => one === other || (one.length === 0 && other.length === 0);

/** Where the caret stood in the box, or where what was selected began, and how much the box held. */
export interface Stood {
  readonly start: number;
  readonly holds: number;
}

/**
 * Where what is selected ends once the box has changed, which is where the caret is left,
 * and how much the box holds. Where it begins is said where something is selected.
 */
export interface Stands {
  readonly start?: number;
  readonly end: number;
  readonly holds: number;
}

/**
 * Where the box was changed, worked out from where the caret stood before and where it
 * stands after. What came in ends where the caret is left, and it began where the caret
 * stood or where what was selected began, whichever comes first: that holds for a letter
 * typed, a selection typed over, a paste, and a letter taken out from either side.
 *
 * Where a change is undone or done again the caret did not stand where the change was.
 * What those keys put back they leave selected, and it is placed by that. With nothing
 * selected, where the change began is worked out from where it ends alone, as letters that
 * went or letters that came. A change that does not add up cannot be placed, and is said
 * not to be.
 */
export function changeOf(was: Stood, now: Stands, how?: How): Change {
  const grew = now.holds - was.holds;
  const placedAt = (at: number): Change | null => {
    const into = now.end - at;
    const out = into - grew;
    const placed = at >= 0 && into >= 0 && out >= 0 && at + out <= was.holds;
    return placed ? { at, out, into, holds: now.holds } : null;
  };
  const putBack = how === "undone" || how === "redone";
  const selected = putBack && now.start !== undefined && now.start < now.end ? placedAt(now.start) : null;
  const change: Change = selected ??
    placedAt(putBack ? now.end - Math.max(grew, 0) : Math.min(was.start, now.end)) ?? {
      at: null,
      out: was.holds,
      into: now.holds,
      holds: now.holds,
    };
  return how === undefined ? change : { ...change, how };
}

/**
 * How far the search has read, once the box has been changed.
 *
 * A change after what was read leaves it as it was. A change that takes out the end of what
 * was read, or all of it, leaves less that was read: what stands from where the change
 * began is new. A change among the words that were read is not read: the place moves with
 * the words after it, and the words before it are said to have been changed.
 */
export function moved(mark: Mark, { at, out, into, holds }: Change): Mark {
  // Nothing of the box was read, or it holds nothing now: there is nothing to keep apart.
  if (mark.to === 0 || holds === 0) return NOTHING_READ;
  // A change that cannot be placed may have been made anywhere. So that no word is read a
  // second time, all that the box holds is taken as read, and as changed.
  if (at === null) return { to: holds, changed: true };
  if (at >= mark.to || (out === 0 && into === 0)) return mark;
  if (at + out >= mark.to) return at === 0 ? NOTHING_READ : { to: at, changed: mark.changed };
  return { to: mark.to + into - out, changed: true };
}

/** A place that the box is too short to hold is brought to its end, and is no longer sure. */
function within(mark: Mark, holds: number): Mark {
  if (mark.to <= holds) return mark;
  return holds === 0 ? NOTHING_READ : { to: holds, changed: true };
}

const same = (one: Mark | null, other: Mark | null) =>
  one === other || (one !== null && other !== null && one.to === other.to && one.changed === other.changed);

/** The box as it is, where nothing of what is known of it has changed, so that nobody is told of nothing. */
function unlessAsItWas(next: Box, box: Box): Box {
  const asItWas =
    next.shown === box.shown &&
    next.gone === box.gone &&
    sameKept(next.back, box.back) &&
    sameKept(next.again, box.again) &&
    same(next.read, box.read) &&
    same(next.sending, box.sending) &&
    same(next.before, box.before);
  return asItWas ? box : next;
}

/** How many characters that the search had read to this place the change took out of the box. */
function lostTo(mark: Mark, { at, out }: Change): number {
  // A change that cannot be placed may have taken out all of them.
  if (at === null) return Math.min(out, mark.to);
  return at >= mark.to ? 0 : Math.min(at + out, mark.to) - at;
}

/**
 * The place, once words have come into the box that had been in it before. What was pasted
 * is what was read, and ends where the paste ends. What the keys that undo put back stands
 * where what was read ended, and there is no more of it than was ever taken out: they say
 * too little of what they did for more to be known. Where they took out words that were
 * read, what they put in their place is of the words before the place too. None of it is
 * read again, nor what stands before it, and that the words before the place are not as
 * they were is said.
 *
 * `lost` is how many characters that were read to this place the change took out, and
 * `astray` that nothing is known of where the keys that do again have led.
 */
function backIn(mark: Mark, { at, into, holds, how }: Change, gone: number, lost: number, astray: boolean): Mark {
  if (how === undefined) return mark;
  const pasted = how === "pasted";
  const comes = (at ?? holds) + into;
  const ends = pasted ? comes : Math.max(mark.to + gone, lost > 0 ? comes : 0);
  const to = Math.min(holds, Math.max(mark.to, ends));
  // Those keys may have put other words where words that were read stood.
  const unsure = to !== mark.to || (!pasted && to > 0 && (lost > 0 || astray));
  if (!unsure || (to === mark.to && mark.changed)) return mark;
  return { to, changed: true };
}

/**
 * The box was changed. Every place in it moves with the words it stands among. What is
 * typed after them all moves none of them: a person who types what they add tells the
 * search nothing that it keeps.
 *
 * Words that were read and come back into the box are not new. The keys that undo and
 * that do again lead the box back to what it held at another time. Where that time is
 * known, all is as it was then. Else what came back is taken as read, as far as it may reach.
 */
export function edited(box: Box, change: Change): Box {
  const { how } = change;
  const held = change.holds - change.into + change.out;
  const here: Was = { held, came: null, read: box.read, sending: box.sending, before: box.before, gone: box.gone };
  const kept = how === "undone" ? box.back : how === "redone" ? box.again : NONE;
  const there = last(kept);
  // The one set of keys leads back from where the other led, and from where words were taken out.
  if (there !== undefined && there.held === change.holds && (there.came === null || there.came === change.out)) {
    const rest = kept.length === 1 ? NONE : kept.slice(0, -1);
    return {
      read: there.read,
      shown: null,
      sending: there.sending,
      before: there.before,
      gone: there.gone,
      back: how === "undone" ? rest : onto(box.back, here),
      again: how === "undone" ? onto(box.again, here) : rest,
    };
  }
  // Counted for the place that lost most: no place lost more.
  const lost = Math.max(0, ...[box.read, box.sending, box.before].map((mark) => (mark === null ? 0 : lostTo(mark, change))));
  const gone = box.gone + lost;
  // The keys that do again, with nothing known of where they lead: the search has moved on
  // since the keys that undo were used.
  const astray = how === "redone";
  const placed = (mark: Mark) => backIn(moved(mark, change), change, gone, lostTo(mark, change), astray);
  // What was known before words that were read were taken out is kept from the first of
  // them, with how much has come into the box since, for as long as nothing else is done to it.
  const cut = how === undefined && change.at !== null && lost > 0;
  const first = last(box.back);
  const taken =
    first !== undefined && first.came !== null
      ? [...box.back.slice(0, -1), { ...first, came: first.came + change.into }]
      : onto(box.back, { ...here, came: change.into });
  return unlessAsItWas(
    {
      read: placed(box.read),
      shown: null,
      sending: box.sending === null ? null : placed(box.sending),
      before: box.before === null ? null : placed(box.before),
      gone,
      back: how === "undone" ? box.back : how === "redone" ? onto(box.back, here) : cut ? taken : NONE,
      again: how === "undone" ? onto(box.again, here) : NONE,
    },
    box,
  );
}

/**
 * The box as the page finds it when it is drawn. A box that is drawn again is empty: what
 * was typed was nowhere else, so nothing in it has been read.
 */
export function found(box: Box, holds: number): Box {
  const read = within(box.read, holds);
  const sending = box.sending === null ? null : within(box.sending, holds);
  const before = box.before === null ? null : within(box.before, holds);
  const moved = read !== box.read || sending !== box.sending || before !== box.before;
  // Where the words of a reading stand is known for the box that sent them, and for no other.
  const shown = moved || box.shown === null || box.shown > holds ? null : box.shown;
  // A box that is drawn keeps nothing that was taken out of the one before it.
  return unlessAsItWas({ read, shown: holds === 0 ? null : shown, sending, before, gone: 0, back: NONE, again: NONE }, box);
}

/**
 * So many characters were sent to be read: all that stands in the box after what was read,
 * as it was typed. A sentence sent before the last one was ranked is undone with it, so
 * what "Stop" puts back is the older place.
 */
export function sent(box: Box, letters: number): Box {
  const to = box.read.to + Math.max(letters, 0);
  return { ...box, sending: { to, changed: false }, before: box.before ?? box.read, back: NONE, again: NONE };
}

/**
 * The words that were sent are answered. Where something came of them, an edit, an offer or
 * a question, the search has read them, and they are not sent again. Where nothing came of
 * them they are still to be read: a person who is told that nothing could be read says it
 * another way where it stands, or puts before it the words it rests on, and all of it is
 * sent. Nothing of it was made part of the search, so nothing of it can be read twice.
 *
 * While a model goes on reading words of which the rules made nothing, they are being read
 * yet. What the person was told when they sent them, that words before them were changed,
 * is not said again once they are read.
 */
export function answered(box: Box, came: boolean, goesOn = false): Box {
  const { sending } = box;
  if (sending === null) return box;
  // Words that were changed while they were read stand where nobody knows.
  const shown = sending.changed ? null : Math.min(box.read.to, sending.to);
  if (!came) return { ...box, shown, sending: goesOn ? sending : null, back: NONE, again: NONE };
  return { ...box, read: sending.to === 0 ? NOTHING_READ : sending, shown, sending: null, back: NONE, again: NONE };
}

/** The words that were sent were not read: the search has read no further than it had. */
export function notRead(box: Box): Box {
  return box.sending === null && box.before === null ? box : { ...box, sending: null, before: null, back: NONE, again: NONE };
}

/** A model has stopped reading the words, or made nothing of them either: nothing reads them now. */
export function readNoMore(box: Box): Box {
  return box.sending === null ? box : { ...box, sending: null, back: NONE, again: NONE };
}

/** The ranking of what was read is in, so there is nothing for "Stop" to put back. */
export function ranked(box: Box): Box {
  return box.before === null ? box : { ...box, before: null, back: NONE, again: NONE };
}

/** "Stop" put the search back as it was when the sentence was sent: it has read what it had read then. */
export function putBack(box: Box): Box {
  return { ...box, read: box.before ?? box.read, shown: null, sending: null, before: null, back: NONE, again: NONE };
}

/** A search that begins again has read nothing of the box, whatever the box holds. */
export function begunAgain(): Box {
  return NO_BOX;
}

/**
 * What stands in the box after what the search has read: the words to send. They are cut
 * from the box, where they already are, and nothing keeps them.
 */
export function added(box: string, read: Pick<Mark, "to">): string {
  return box.slice(Math.min(Math.max(read.to, 0), box.length));
}
