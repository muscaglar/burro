// What the page decides, as plain functions.
//
// Nothing here touches the screen, the network or a clock. The page hands in
// what happened, with the time it happened at, and is handed back what is now
// so and what to do next. So every rule of the page can be tested with
// `node --test` and no browser. docs/design/desk.md, sections 2 to 5, is what
// this is built to.

export const MOST_SECONDS = 900;
export const MOST_NOTE = 500;

// A key held down, or struck twice, must not answer an item nobody has read.
export const GRACE_MS = 250;

// A letter is held this long before it acts, so that words typed with the note
// shut are known for words before any of them is taken for a key. Three
// letters inside BURST_MS are words. Digits, Enter and the key for a note act
// at once: an answer is never held.
export const HOLD_MS = 350;
export const BURST_MS = 1000;

// Every word the page says of its own. A word from a file is never in here.
export const SAYS = {
  name: 'Burro review desk',
  madeUp: 'MADE-UP CITY. Nothing here is a real place.',
  real: 'REAL DATA FOR LONDON. A draft that nobody has checked. What you decide here is built.',
  notKnown: 'Not yet known which data this is. Decide nothing.',
  mixed: 'The desk gave two answers about which data this is. Decide nothing. Start the desk again with make desk.',
  loading: 'Loading.',
  noAnswer: 'The desk does not answer. Start it again with make desk. Trying again.',
  notSaved: 'Not saved. Start the desk again with make desk.',
  kept: 'Your answer is kept here and will be sent again. Do not close this page.',
  otherData: 'The desk was started again with other data. Your last answer was not saved. Look again, then answer.',
  changed: 'This item changed after it was shown. Your answer was not saved. Look again, then answer.',
  already: 'You answered this already, from another page. Nothing was changed. Press the key again to change it.',
  refused: 'The desk refused that. Nothing was saved.',
  gone: 'That item is no longer in the queue.',
  lost: 'The desk lists items it does not hold. Start the desk again with make desk.',
  noteHint: 'A note may be published. Write nothing about yourself or anyone else.',
  noteNeeded: 'This answer needs a note. Say why, then press Enter. Esc takes the answer back.',
  noteOpen: 'Write the note. Enter keeps it. Esc leaves it.',
  noteKept: 'Note kept. It goes with your next answer.',
  noteLeft: 'Note left as it was.',
  answerLeft: 'Answer taken back. Nothing was saved.',
  secondOn: 'Your next answer will ask for a second reviewer.',
  secondOff: 'Your next answer will not ask for a second reviewer.',
  paused: 'Paused. The clock is stopped. Press p to go on.',
  goOn: 'Going on.',
  tooSoon: 'Too quick. Read the item, then answer.',
  pressN: 'That was taken for words, and nothing was done. Press n to write a note.',
  undoEarlier: 'Nothing was saved in this sitting. Press u again to take back an answer of an earlier one.',
  dropped: 'The note and the mark were dropped.',
  skipped: 'It comes back after the rest.',
  moved: 'Moved. Press u to take it back. Then say whether it is right now. Your answer will need a note.',
  sameArea: 'That cell is in the same area. Nothing moved.',
  letGo: 'Let go.',
  tookBack: 'Taken back:',
  nothingToUndo: 'Nothing to take back.',
  firstItem: 'This is the first.',
  lastItem: 'This is the last.',
  asDrafted: 'left as drafted',
  leansOn: 'Leans on',
  asTheRulesStand: 'As the rules stand',
  toOpenThem: 'To open them',
  openDrawn: 'Press o to open the first of the items below. ] and [ go through them, and o comes back to this rule. Nothing is decided there.',
  noneDrawn: 'No item is shown here to open. In Rules, o opens the items a rule shows.',
  visiting: 'You are looking at an item that was drawn for a rule. Nothing is decided here. Press o to go back to the rule.',
  firstDrawn: 'This is the first of the items drawn. Press o to go back to the rule.',
  lastDrawn: 'This is the last of the items drawn. Press o to go back to the rule.',
  nothingChanged: 'Nothing was changed.',
  noFlagged: 'No flagged item is left here. Press ] for the next item, or q for another queue.',
  lastFlagged: 'This is the only flagged item that is left here.',
  chooseQueue: 'Choose a queue.',
  noQueue: 'No queue is chosen. Press q to list them.',
  noGroups: 'This queue has one group.',
  everyGroup: 'Every group',
  queues: 'Queues',
  groups: 'Groups',
  keys: 'Keys',
  queuesFoot: 'Press the key of a queue. Or Up and Down to move, and Enter to choose. Esc to close.',
  panelFoot: 'Up and Down to move. Enter to choose. Esc to close.',
  keysFoot: 'Esc to close.',
  skippedBefore: 'You skipped this before.',
  noPick: 'This queue has no spellings to choose.',
  noMove: 'Cells cannot be moved in this queue.',
  areaNeeded: 'Say which area this is a name of. Click a cell of it, or press m with the cross over it. Then answer.',
  areaSelf: 'That is the area this name was proposed as. Choose another.',
  areasMost: 'A name is given to five areas at most.',
  areaChosen: 'Area chosen. Now answer.',
  notAnArea: 'The desk cannot make an area of another name. If it should be one, write a note and skip it.',
  noKeyForArea: 'No key 1 here: the desk cannot make an area of another name. If it should be one, write a note and skip it.',
  nothingProposed: 'Nothing is proposed for this item. Press the number of an answer.',
  areaBack: 'Area taken back.',
  noMap: 'This item has no map.',
  waits: 'A name decided later opens its border again.',
  settles: 'You and another reviewer differ. Your answer now settles it.',
  inDispute: 'You and another reviewer differ. The first reviewer settles it.',
};

export const KEYS = [
  { key: '1-9', does: 'Give the answer with that number. It is saved, and the next item is shown.' },
  { key: '7', does: 'Ratings: say that you do not know the area. Every vibe of it that is open is answered, and one undo takes them all back.' },
  { key: 'Enter', does: 'Give the answer marked as proposed, where one is.' },
  { key: 's', does: 'Skip. The item comes back after the rest.' },
  { key: 'u', does: 'Undo. Takes back what the last key saved in this queue, and shows its item.' },
  { key: 'n', does: 'Write a note for the next answer. Enter keeps it. Esc leaves it.' },
  { key: 'f', does: 'Ask a second reviewer to look at the next answer, or skip.' },
  { key: '[  ]', does: 'Look at the item before or after. Nothing is decided, and a note that was kept stays.' },
  { key: 'Left, Right', does: 'The same, where no map is shown.' },
  { key: 'j', does: 'Go to the next flagged item that is not done. Nothing is decided.' },
  { key: 'o', does: 'Rules: open the first of the items a rule shows. [ and ] go through them, and o comes back to the rule.' },
  { key: 'g', does: 'Choose a group, such as a borough.' },
  { key: 'q', does: 'List the queues.' },
  { key: 'p', does: 'Pause. The clock stops. Press p again to go on.' },
  { key: '?', does: 'Show these keys.' },
  { key: '.  ,', does: 'Read on in what is known of the item, and go back. Page Down and Page Up do the same.' },
  { key: '+  -  0', does: 'Map: zoom in, zoom out, fit the item.' },
  { key: 'An arrow', does: 'Map: move it. With Shift, by a small step. A mouse can drag it, and its wheel zooms.' },
  { key: 'a-e', does: 'Names: choose a spelling.' },
  { key: 'm', does: 'Map: does to the cell under the cross what a click does.' },
  { key: 'Click, click', does: 'Borders: take up a cell, then click a cell of the area it should join.' },
  { key: 'Click', does: 'Names: say which area this is a name of. Click again to take it back.' },
  { key: 'Esc', does: 'Let go of a cell, leave a note, close a list, or drop a note that was kept.' },
];

// The key that chooses each row of the list of queues: the keys of the top row,
// from left to right. No letter chooses one, because a letter may be a word.
export const QUEUE_KEYS = '1234567890-=';

const BAR = [
  { key: '1-9', label: 'answer', action: null },
  { key: 's', label: 'skip', action: { type: 'skip' } },
  { key: 'u', label: 'undo', action: { type: 'undo' } },
  { key: 'n', label: 'note', action: { type: 'note' } },
  { key: 'f', label: 'second reviewer', action: { type: 'second' } },
  { key: '[', label: 'before', action: { type: 'look', by: -1 } },
  { key: ']', label: 'after', action: { type: 'look', by: 1 } },
  { key: 'j', label: 'flagged', action: { type: 'flagged' } },
  { key: 'g', label: 'group', action: { type: 'panel', kind: 'groups' } },
  { key: 'q', label: 'queues', action: { type: 'panel', kind: 'queues' } },
  { key: 'p', label: 'pause', action: { type: 'pause' } },
  { key: '?', label: 'keys', action: { type: 'panel', kind: 'keys' } },
];

// ---------------------------------------------------------------- small things

// How long, in words a tired person can read at a glance.
export function spell(seconds) {
  if (typeof seconds !== 'number' || !Number.isFinite(seconds) || seconds < 0) return '';
  if (seconds < 60) return `${Math.round(seconds)} s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
}

// How long to wait before trying again: 1, 2, 4, 8 seconds, then 10 for ever.
export function retryAfter(tries) {
  return Math.min(10000, 1000 * 2 ** Math.max(0, Math.min(tries, 5) - 1));
}

function number(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

// What is still to do in a queue. A skipped item and one whose answer is stale
// both come back, so both are left. An item in dispute waits on the first reviewer.
export function left(counts) {
  if (!counts) return 0;
  return Math.max(0, number(counts.total) - number(counts.done) - number(counts.disputed));
}

// "Done" is what a build will see. What the person called wrong, or could not
// judge, is said apart, so that the top line never says work is finished that
// changes nothing.
export function progress(counts, paused = false) {
  if (!counts) return '';
  if (counts.parts && number(counts.parts.total) > 0) {
    // Counted in areas. A pace for each vibe would say nothing of an area.
    const done = number(counts.parts.done);
    const line = `${counts.title || counts.queue}: ${done} of ${counts.parts.total} areas done, ${counts.parts.total - done} left`;
    return paused ? `PAUSED. ${line}` : line;
  }
  const wrong = number(counts.wrong);
  const notKnown = number(counts.not_known);
  const aside = number(counts.set_aside);
  const byRule = number(counts.by_rule);
  const parts = [`${Math.max(0, number(counts.done) - wrong - notKnown - aside - byRule)} done`];
  // What a rule settled was read by no person, and is never counted as read.
  if (byRule > 0) parts.push(`${byRule} by rule`);
  if (notKnown > 0) parts.push(`${notKnown} not known`);
  if (wrong > 0) parts.push(`${wrong} wrong`);
  // An answer that a build will set aside is saved, and is no work done until
  // the draft is made again.
  if (aside > 0) parts.push(`${aside} ${aside === 1 ? 'waits' : 'wait'} for a new draft`);
  parts.push(`${left(counts)} left`);
  if (number(counts.flagged_left) > 0) parts.push(`${counts.flagged_left} of them flagged`);
  if (number(counts.disputed) > 0) parts.push(`${counts.disputed} in dispute`);
  const pace = counts.median_seconds;
  if (typeof pace === 'number' && pace > 0) {
    parts.push(`${spell(pace)} each`);
    if (left(counts) > 0) parts.push(`about ${spell(pace * left(counts))} left at this pace`);
  } else if (pace === 0 && number(counts.done) > 0) {
    // The desk counts whole seconds. Work that is timed at none is not work with no pace.
    parts.push('under 1 s each');
  } else {
    parts.push('no pace yet');
  }
  const line = `${counts.title || counts.queue}: ${parts.join(', ')}`;
  return paused ? `PAUSED. ${line}` : line;
}

// What a queue waits on, in words, or nothing. Names are decided before borders
// are drafted, and a name decided afterwards opens a border again.
export function waitsWords(counts) {
  const waits = counts && Array.isArray(counts.waits) ? counts.waits.filter((row) => row && number(row.left) > 0) : [];
  if (waits.length === 0) return '';
  return `Waits on ${waits.map((row) => `${row.left} in ${row.title || row.queue}`).join(' and ')}.`;
}

// What a queue waits on a new draft for, in words, or nothing: the answers in
// a queue it is made from that a build will set aside until the draft is made
// again. A border looked at before then is drawn round a name that is to go.
export function redraftWords(counts) {
  const rows = counts && Array.isArray(counts.waits) ? counts.waits.filter((row) => row && number(row.set_aside) > 0) : [];
  if (rows.length === 0) return '';
  const each = rows.map((row) => `${row.set_aside} in ${row.title || row.queue} ${number(row.set_aside) === 1 ? 'waits' : 'wait'} for a new draft.`);
  return `${each.join(' ')} Make the draft again from the answers, and fill the queues again, before you go on here.`;
}

// What the question says of an answer that a build will set aside, for the
// item on screen, or null. The desk cannot take the ground from under an area:
// it saves an answer that turns the name of such an area down, and the step
// that makes a build's files sets it aside. The item says what its area holds.
function asideOf(question, item) {
  const held = question && question.set_aside && typeof question.set_aside === 'object' ? question.set_aside : null;
  const holds = item && item.preset && typeof item.preset.holds === 'string' ? item.preset.holds : '';
  const words = held !== null && holds !== '' && held[holds] && typeof held[holds] === 'object' ? held[holds] : null;
  if (words === null || !Array.isArray(held.answers)) return null;
  const said = (key) => (typeof words[key] === 'string' ? words[key] : '');
  return { answers: held.answers, mark: typeof held.mark === 'string' ? held.mark : '', short: said('short'), words: said('words'), saved: said('saved') };
}

// The counts of a queue by its parts, where one answer may be given to a whole
// part: a rater is asked about areas, and the queue holds each on eight vibes.
// A part is done when every item of it is.
function partsOf(state, counts) {
  const items = state.queue && coversOf(state) ? state.queue.items : [];
  const parts = new Map();
  for (const entry of items) {
    if (typeof entry.part !== 'string') return counts;
    parts.set(entry.part, (parts.get(entry.part) ?? true) && entry.state === 'done');
  }
  if (parts.size === 0) return counts;
  return { ...counts, parts: { total: parts.size, done: [...parts.values()].filter(Boolean).length } };
}

// The counts of a queue, wherever the answer keeps them.
export function countsFrom(data) {
  if (!data || typeof data !== 'object') return null;
  if (data.counts && typeof data.counts === 'object') return data.counts;
  if (typeof data.total === 'number') return data;
  return null;
}

function adds(question, what) {
  const value = question ? question.adds : null;
  if (Array.isArray(value)) return value.includes(what);
  return value === what;
}

// The words a queue asks in once a cell of the item has been moved, or null.
// After a move "Is this boundary right?" can be read as "was the draft
// right?", and both answers apply the move. So the question and its answers
// say that they are about the border as it now stands.
function afterMove(question, moves) {
  const held = question && question.moved && typeof question.moved === 'object' ? question.moved : null;
  return held !== null && adds(question, 'move') && Array.isArray(moves) && moves.length > 0 ? held : null;
}

// The question, with the item's own words put in where it asks for them.
// A word the item does not hold is left as written, so the fault shows.
export function questionText(question, item, moves = []) {
  const moved = afterMove(question, moves);
  const asked = moved !== null && typeof moved.text === 'string' && moved.text !== '' ? moved.text : question && question.text;
  const text = typeof asked === 'string' ? asked : '';
  const fill = item && item.fill && typeof item.fill === 'object' ? item.fill : {};
  return text.replace(/\{([a-z_]+)\}/g, (whole, word) =>
    typeof fill[word] === 'string' && fill[word] !== '' ? fill[word] : whole,
  );
}

// `wrong` needs a note, and so does any answer given after a cell was moved:
// the note is the reason a build writes beside the move.
export function needsNote(question, code, moves) {
  if (code === 'wrong') return true;
  return adds(question, 'move') && Array.isArray(moves) && moves.length > 0;
}

// The answers that give a name to an area, and so need the area named.
const NAMES_AN_AREA = ['same_ground', 'inside', 'wide'];
const MOST_AREAS = 5;

// True where the person may say which areas a name is a name of: the item
// was made with a list of them, which may be empty.
function namesAreas(question, item) {
  return adds(question, 'pick') && Boolean(item && item.preset && Array.isArray(item.preset.of));
}

// The area a name was proposed as, which it cannot also be another name of.
function ownArea(item) {
  return item && typeof item.id === 'string' && item.id.startsWith('n:') ? item.id.slice(2) : null;
}

// What the queue adds to the line: what the item was made with, the spelling
// chosen, and the areas the name is given to.
export function detailOf(question, item, pick, of = null) {
  const detail = item && item.preset && typeof item.preset === 'object' ? { ...item.preset } : {};
  const picks = item && Array.isArray(item.picks) ? item.picks : [];
  if (adds(question, 'pick') && picks.length > 0) {
    detail.pick = picks[Math.max(0, Math.min(pick, picks.length - 1))];
  }
  if (namesAreas(question, item)) detail.of = Array.isArray(of) ? [...of] : [...item.preset.of];
  return detail;
}

// Only the first reviewer ends a dispute, and only on an item that is in one.
export function settles(reviewer, itemState) {
  return reviewer === 'r1' && itemState === 'disputed';
}

// One part of an address. A colon is left as it is: an item's id holds one,
// and it needs no escape in a path.
function part(text) {
  return encodeURIComponent(String(text)).replace(/%3A/gi, ':');
}

// The address of what is asked for. Always a path on the desk's own origin:
// the page never names a host.
export function pathOf(effect) {
  if (effect.do === 'post') return effect.what === 'undo' ? '/api/undo' : '/api/decide';
  switch (effect.what) {
    case 'state':
      return '/api/state';
    case 'queue':
      return `/api/queue/${part(effect.queue)}`;
    case 'item':
      return `/api/item/${part(effect.queue)}/${part(effect.item)}`;
    case 'layer':
      return `/api/layer/${part(effect.group)}/${part(effect.layer)}`;
    default:
      return '/api/state';
  }
}

// ---------------------------------------------------------------- the clock

// How long an item has been on screen with the tab in view and no pause.
export function clockNew() {
  return { ran: 0, from: null };
}

export function clockGo(clock, at) {
  return clock.from === null ? { ran: clock.ran, from: at } : clock;
}

export function clockStop(clock, at) {
  if (clock.from === null) return clock;
  return { ran: clock.ran + Math.max(0, at - clock.from), from: null };
}

export function clockSeconds(clock, at) {
  const running = clock.from === null ? 0 : Math.max(0, at - clock.from);
  return Math.min(MOST_SECONDS, Math.round((clock.ran + running) / 1000));
}

// ---------------------------------------------------------------- which item

function inGroup(entry, group) {
  return group === null || group === undefined || entry.group === group;
}

function isOpen(entry, reviewer) {
  if (entry.state === 'open' || entry.state === 'stale') return true;
  return entry.state === 'disputed' && reviewer === 'r1';
}

// The next item to decide: the first open one after this one, going round to
// the start. When none is open, the first skipped one, in the same way.
export function nextItem(items, after, group, reviewer) {
  const list = Array.isArray(items) ? items : [];
  if (list.length === 0) return null;
  const from = list.findIndex((entry) => entry.id === after);
  const order = [];
  for (let i = 1; i <= list.length; i += 1) order.push(list[(from + i + list.length) % list.length]);
  const open = order.find((entry) => inGroup(entry, group) && isOpen(entry, reviewer));
  if (open) return open.id;
  const skipped = order.find((entry) => inGroup(entry, group) && entry.state === 'skipped');
  return skipped ? skipped.id : null;
}

// The next flagged item to decide: the first open one after this one that
// carries a flag, going round to the start. When none is open, the first
// skipped one. So a person who looks at flagged borders alone need not skip
// each one that is not flagged. Where this one is the only one left, it is
// this one.
export function nextFlagged(items, after, group, reviewer) {
  const list = Array.isArray(items) ? items : [];
  const from = list.findIndex((entry) => entry.id === after);
  const order = [];
  for (let i = 1; i <= list.length; i += 1) order.push(list[(from + i + list.length) % list.length]);
  const flagged = order.filter((entry) => entry.flagged === true && inGroup(entry, group));
  const open = flagged.find((entry) => entry.id !== after && isOpen(entry, reviewer));
  if (open) return open.id;
  const left = flagged.find((entry) => entry.id !== after && entry.state === 'skipped') || flagged.find((entry) => isOpen(entry, reviewer) || entry.state === 'skipped');
  return left ? left.id : null;
}

// The item before or after in the list, whatever its state. Looking decides nothing.
export function lookItem(items, from, by, group) {
  const list = (Array.isArray(items) ? items : []).filter((entry) => inGroup(entry, group));
  if (list.length === 0) return null;
  const at = list.findIndex((entry) => entry.id === from);
  if (at < 0) return list[0].id;
  const to = at + by;
  return to < 0 || to >= list.length ? null : list[to].id;
}

// The groups of a queue, in the order they first appear, with what is left in each.
export function groupsOf(items, reviewer) {
  const seen = new Map();
  for (const entry of Array.isArray(items) ? items : []) {
    const row = seen.get(entry.group) || { group: entry.group, total: 0, left: 0 };
    row.total += 1;
    if (isOpen(entry, reviewer) || entry.state === 'skipped') row.left += 1;
    seen.set(entry.group, row);
  }
  return [...seen.values()];
}

// ---------------------------------------------------------------- the state

export function start() {
  return {
    phase: 'loading',
    synthetic: null,
    banner: '',
    reviewer: '',
    token: '',
    broken: 0,
    mixed: false,
    queues: [],
    queue: null, // { id, question, items, group }
    first: null, // the item to show when a queue's list comes
    want: null, // the item asked for, to show when it comes
    now: null, // { id, item, mine, moves, others, shownAt }
    cache: {},
    note: '',
    noteOpen: false,
    draft: '',
    held: null, // an answer that waits for its note
    second: false,
    pick: 0,
    of: [], // the areas a name is given to
    notedAt: null, // when a note was last kept: Enter struck twice must not answer
    letters: [], // when each letter of the last second was struck
    heldKeys: [], // what the letters that are held a moment would do
    typingUntil: 0, // until when a key is taken for one of the words being typed
    queued: [], // a note, a mark or a spelling asked for while an answer was on its way
    wrote: {}, // by queue: how many lines this sitting wrote that stand
    acts: {}, // by queue: the numbers of the lines each key of this sitting wrote, the last key last
    sweep: null, // { part, title, ns }: the part whose every open item is being given one answer
    unsweep: null, // { of }: the lines of one key that are being taken back, one after another
    undoAsked: null, // the queue in which an undo of an earlier sitting was asked for once
    saidOf: null, // the item that what is said is about, when it is the one to be shown
    hand: null, // { cell, area }: the cell taken up
    visit: null, // { rule, title, queue, list, at }: the items drawn for a rule, while one is looked at
    ruleAt: {}, // by queue: the first item of it shown in this sitting, on which the rule is open
    asideAt: {}, // by queue: the first item shown in this sitting whose answer may be set aside
    panel: null, // { kind, at }
    paused: false,
    seen: true,
    clock: clockNew(),
    pending: null, // { what, body }: a write the desk has not confirmed
    tries: 0,
    lost: 0, // how many items in a row the desk listed and did not hold
    again: null, // what to ask for when the wait is over
    trouble: '',
    said: '',
  };
}

// True while closing the page would lose an answer.
export function hasUnsaved(state) {
  return state.pending !== null || state.held !== null;
}

function entryOf(state, id) {
  if (!state.queue) return null;
  return state.queue.items.find((entry) => entry.id === id) || null;
}

function countsOf(state) {
  if (!state.queue) return null;
  return state.queues.find((row) => row.queue === state.queue.id) || null;
}

function answersOf(state) {
  const list = state.queue && state.queue.question ? state.queue.question.answers : null;
  return Array.isArray(list) ? list.slice(0, 9) : [];
}

// The answer that is given to every item of a part at once, or null: a rater
// who does not know an area says so once, and not once for each vibe.
function coversOf(state) {
  const held = state.queue && state.queue.question ? state.queue.question.covers : null;
  const fits = held && typeof held === 'object' && typeof held.code === 'string' && typeof held.label === 'string';
  return fits && answersOf(state).length < 9 && answersOf(state).some((one) => one.code === held.code) ? held : null;
}

// The part of the queue that an item is of, as the list of the queue says it.
function partOf(state, id) {
  const entry = entryOf(state, id);
  return entry && typeof entry.part === 'string' ? entry.part : null;
}

function labelOf(state, code) {
  if (code === 'skip') return 'Skipped';
  if (code === 'rule') return SAYS.asDrafted;
  const found = answersOf(state).find((answer) => answer.code === code);
  return found ? found.label : code;
}

// The label of an answer as it reads now: after a move, in the words for that.
function labelNow(state, entry) {
  const moved = state.now ? afterMove(state.queue.question, state.now.moves) : null;
  const words = moved !== null && moved.answers && typeof moved.answers === 'object' ? moved.answers[entry.code] : null;
  return typeof words === 'string' && words !== '' ? words : String(entry.label);
}

function runs(state) {
  return state.now !== null && state.seen && !state.paused;
}

function withClock(state, at) {
  const clock = runs(state) ? clockGo(state.clock, at) : clockStop(state.clock, at);
  return clock === state.clock ? state : { ...state, clock };
}

function only(state, extra = {}) {
  return { state: { ...state, ...extra }, effects: [] };
}

function say(state, said, extra = {}) {
  return only(state, { said, ...extra });
}

// Ask again later for what failed, and say so. What was said of the answer
// before goes: the screen must not say Saved while it says Not saved.
function later(state, effect, words) {
  const tries = state.tries + 1;
  return {
    state: { ...state, tries, again: effect, trouble: words, said: '' },
    effects: [{ do: 'wait', ms: retryAfter(tries) }],
  };
}

function prune(cache, keep) {
  const ids = Object.keys(cache);
  if (ids.length <= 12) return cache;
  const out = {};
  for (const id of ids.slice(-6)) out[id] = cache[id];
  for (const id of keep) if (id && cache[id]) out[id] = cache[id];
  return out;
}

// Put an item on screen, or ask for it. A cell in the hand and an answer that
// waited for its note belong to one item, and go. A note that was kept and a
// mark stay: they go with the next answer, whichever item it is given to, until
// it is given or Esc drops them.
function show(state, id, at, said = '') {
  const clean = {
    ...state,
    noteOpen: false,
    draft: '',
    held: null,
    hand: null,
    panel: null,
    first: null,
  };
  if (id === null) {
    const none = { ...clean, now: null, want: null, clock: clockNew(), said };
    return { state: none, effects: [{ do: 'focus', on: 'page' }] };
  }
  const effects = [];
  let next = clean;
  const held = clean.cache[id];
  if (held) {
    const entry = entryOf(clean, id);
    const mine = held.mine;
    const picks = Array.isArray(held.item.picks) ? held.item.picks : [];
    const chosen = mine && mine.detail ? picks.indexOf(mine.detail.pick) : -1;
    const drafted = held.item.preset && Array.isArray(held.item.preset.of) ? held.item.preset.of : [];
    const given = mine && mine.answer !== 'skip' && mine.detail && Array.isArray(mine.detail.of) ? mine.detail.of : drafted;
    const covering = clean.sweep !== null && partOf(clean, id) === clean.sweep.part && coversOf(clean) !== null;
    next = {
      ...clean,
      want: null,
      now: { id, ...held, shownAt: at },
      pick: chosen >= 0 ? chosen : 0,
      of: given.filter((one) => typeof one === 'string').slice(0, MOST_AREAS),
      clock: clockNew(),
      // While a part is covered the page says nothing new of each item: what
      // was saved is said once, when the part is done.
      said: covering
        ? clean.said
        : [saidWith(said, held.item.title, clean.saidOf === id), entry && entry.state === 'skipped' ? SAYS.skippedBefore : '']
          .filter(Boolean)
          .join(' '),
      saidOf: null,
      queued: [],
      ruleAt: typeof clean.ruleAt[clean.queue.id] === 'string' ? clean.ruleAt : { ...clean.ruleAt, [clean.queue.id]: id },
      asideAt:
        typeof clean.asideAt[clean.queue.id] === 'string' || asideOf(clean.queue.question, held.item) === null
          ? clean.asideAt
          : { ...clean.asideAt, [clean.queue.id]: id },
    };
    next = withClock(next, at);
    effects.push({ do: 'focus', on: 'page' });
    if (covering) {
      // The part is being covered: this item is given the answer as it appears.
      if (entry !== null && ['open', 'stale', 'skipped'].includes(entry.state)) {
        const sent = send(next, bodyOf(next, coversOf(next).code, at, ''));
        return { state: sent.state, effects: [...effects, ...sent.effects] };
      }
      // An item that has an answer keeps it: one given from another page is
      // never written over. The rest of the part is gone on with.
      const more = nextOfPart(next, next.queue.items, id);
      if (more !== null) return show(clean, more, at);
      return show({ ...covered(clean), trouble: '' }, nextItem(next.queue.items, id, next.queue.group, next.reviewer), at, coveredWords(clean));
    }
    // What was asked for while the answer was on its way is done now.
    let out = { state: covered(next), effects: [] };
    for (const action of clean.queued) out = andThen(out, (now) => react(now, action, at));
    next = out.state;
    effects.push(...out.effects);
  } else {
    // While a part is covered what is said stays, as it does when the item is held.
    next = { ...clean, want: id, said: clean.sweep !== null ? clean.said : said };
    effects.push({ do: 'get', what: 'item', queue: clean.queue.id, item: id });
  }
  const after = nextItem(next.queue.items, id, next.queue.group, next.reviewer);
  if (after !== null && after !== id && !next.cache[after]) {
    effects.push({ do: 'get', what: 'item', queue: next.queue.id, item: after });
  }
  return { state: next, effects };
}

// The lines one key wrote are one act, and undo takes them back together. The
// page holds the number of each, for as many keys as a person might take back.
function actsWith(state, ns) {
  if (!state.queue || ns.length === 0) return state.acts;
  const held = Array.isArray(state.acts[state.queue.id]) ? state.acts[state.queue.id] : [];
  return { ...state.acts, [state.queue.id]: [...held, ns].slice(-50) };
}

// A part has been covered: the lines written for it are one act.
function covered(state) {
  if (state.sweep === null) return state;
  return { ...state, sweep: null, acts: actsWith(state, state.sweep.ns) };
}

function answersWord(count) {
  return `${count} ${count === 1 ? 'answer' : 'answers'}`;
}

// What is said once a part is covered: the answer, how many lines it wrote, and of what.
function coveredWords(state) {
  return `Saved: ${coversOf(state).label}, ${answersWord(state.sweep.ns.length)}, for ${state.sweep.title}.`;
}

// What is said as an item appears. With nothing to say, its name. With
// something said of the item before, that and then the name of this one. With
// something said of this very item, as when an answer to it was taken back,
// the words end with its name.
function saidWith(said, title, ofThis) {
  if (said === '') return title;
  return ofThis ? `${said}, for ${title}.` : `${said} Next: ${title}.`;
}

function openQueue(state, queue, first = null) {
  return {
    state: { ...state, panel: null, first, want: null, note: '', second: false, undoAsked: null, said: SAYS.loading },
    effects: [{ do: 'get', what: 'queue', queue }],
  };
}

// ---------------------------------------------------------------- what came back

function gotState(state, event, at) {
  if (!event.ok || !event.data || typeof event.data.synthetic !== 'boolean') {
    return later(state, { do: 'get', what: 'state' }, state.pending ? SAYS.notSaved : SAYS.noAnswer);
  }
  const data = event.data;
  const other =
    state.phase === 'ready' && (data.synthetic !== state.synthetic || data.reviewer !== state.reviewer);
  let next = {
    ...state,
    phase: 'ready',
    synthetic: data.synthetic,
    banner: typeof data.banner === 'string' ? data.banner : '',
    reviewer: typeof data.reviewer === 'string' ? data.reviewer : '',
    token: typeof data.token === 'string' ? data.token : '',
    broken: number(data.broken_lines),
    queues: Array.isArray(data.queues) ? data.queues : [],
    mixed: false,
    tries: 0,
    again: null,
    trouble: state.pending ? state.trouble : '',
  };
  if (other) {
    // Another city, or another reviewer: nothing held for the old one may be written.
    next = { ...start(), ...pickState(next), trouble: state.pending ? SAYS.otherData : '' };
    return { state: { ...next, panel: { kind: 'queues', at: 0 } }, effects: [{ do: 'focus', on: 'panel' }] };
  }
  if (state.pending) {
    return { state: next, effects: [{ do: 'post', what: state.pending.what, body: state.pending.body }] };
  }
  if (state.phase === 'loading') {
    const resume = data.resume && typeof data.resume === 'object' ? data.resume : null;
    if (resume && next.queues.some((row) => row.queue === resume.queue)) {
      return openQueue(next, resume.queue, typeof resume.item === 'string' ? resume.item : null);
    }
    return { state: { ...next, panel: { kind: 'queues', at: 0 }, said: SAYS.chooseQueue }, effects: [{ do: 'focus', on: 'panel' }] };
  }
  return withoutTrouble(next, at);
}

function pickState(state) {
  const { phase, synthetic, banner, reviewer, token, broken, queues, seen } = state;
  return { phase, synthetic, banner, reviewer, token, broken, queues, seen };
}

function withoutTrouble(state) {
  return only(state, { trouble: '' });
}

// Every answer says which data it is of. Two that differ stop the page.
function sameData(state, data) {
  if (!data || typeof data.synthetic !== 'boolean') return true;
  return state.synthetic === null || data.synthetic === state.synthetic;
}

function gotQueue(state, event, at) {
  if (!event.ok) {
    if (event.status >= 400 && event.status < 500) {
      return { state: { ...state, trouble: wordsOf(event, SAYS.refused), panel: { kind: 'queues', at: 0 } }, effects: [{ do: 'focus', on: 'panel' }] };
    }
    return later(state, { do: 'get', what: 'queue', queue: event.queue }, SAYS.noAnswer);
  }
  const data = event.data || {};
  const items = Array.isArray(data.items) ? data.items : [];
  const same = state.queue && state.queue.id === event.queue;
  if (event.quiet) {
    if (!same) return only(state);
    return only(state, { queue: { ...state.queue, question: data.question || state.queue.question, items } });
  }
  const group = same && items.some((entry) => entry.group === state.queue.group) ? state.queue.group : null;
  const next = {
    ...state,
    queue: { id: event.queue, question: data.question || {}, items, group },
    cache: same ? state.cache : {},
    tries: 0,
    again: null,
    trouble: state.trouble === SAYS.noAnswer ? '' : state.trouble,
  };
  const first = state.first !== null && items.some((entry) => entry.id === state.first) ? state.first : null;
  const id = first !== null ? first : nextItem(items, null, group, next.reviewer);
  const said = state.said === SAYS.loading ? '' : state.said;
  return show(next, id, at, state.first !== null && first === null ? SAYS.gone : said);
}

function gotItem(state, event, at) {
  if (!state.queue || event.queue !== state.queue.id) return only(state);
  const wanted = state.want === event.item;
  if (!event.ok) {
    if (!wanted) return only(state);
    if (event.status === 404) {
      // The list is read again. If the desk goes on listing what it does not
      // hold, the page stops asking: it must never ask without end.
      if (state.lost >= 2) return show({ ...state, lost: 0, trouble: SAYS.lost }, null, at);
      return { state: { ...state, want: null, lost: state.lost + 1, trouble: SAYS.gone }, effects: [{ do: 'get', what: 'queue', queue: state.queue.id }] };
    }
    return later(state, { do: 'get', what: 'item', queue: event.queue, item: event.item }, SAYS.noAnswer);
  }
  const data = event.data || {};
  if (!data.item || typeof data.item !== 'object') return only(state);
  const held = {
    item: data.item,
    mine: data.mine || null,
    moves: Array.isArray(data.moves) ? data.moves : [],
    others: Array.isArray(data.others) ? data.others : [],
    // For a rule that leans on others: how each of them stands today.
    leans: Array.isArray(data.leans) ? data.leans : [],
  };
  const cache = prune({ ...state.cache, [event.item]: held }, [state.now ? state.now.id : null, event.item]);
  // The desk says how the item stands now. The list is kept to it.
  const known = ['open', 'done', 'skipped', 'stale', 'disputed'].includes(data.state);
  const queue = known ? { ...state.queue, items: setEntry(state.queue.items, event.item, data.state) } : state.queue;
  const next = { ...state, cache, queue, tries: wanted ? 0 : state.tries, again: wanted ? null : state.again };
  if (wanted) next.lost = 0;
  if (!wanted) {
    // Read again while it is on screen: what is shown is brought up to date, and the clock runs on.
    if (state.now && state.now.id === event.item) return only(next, { now: { ...state.now, ...held } });
    return only(next);
  }
  return show({ ...next, trouble: state.trouble === SAYS.noAnswer ? '' : state.trouble }, event.item, at, state.said);
}

function wordsOf(event, otherwise) {
  const data = event.data;
  return data && typeof data.message === 'string' && data.message !== '' ? data.message : otherwise;
}

function setEntry(items, id, itemState) {
  return items.map((entry) => (entry.id === id ? { ...entry, state: itemState } : entry));
}

function setCounts(queues, counts) {
  if (!counts || typeof counts.queue !== 'string') return queues;
  return queues.map((row) => (row.queue === counts.queue ? { ...row, ...counts } : row));
}

function wrote(state, event, at) {
  if (!state.pending || state.pending.what !== event.what) return only(state);
  const pending = state.pending;
  // An undo that failed may have been taken all the same. So the rest of what
  // one key wrote is not gone on with: the person sees what stands, and asks again.
  if (!event.ok) return notWritten({ ...state, said: '', unsweep: null }, event, pending);
  return written(state, event, at, pending);
}

// An answer the desk did not take. What was said of the answer before is gone.
function notWritten(state, event, pending) {
  const code = event.data && typeof event.data.error === 'string' ? event.data.error : '';
  const sure = event.status >= 400 && event.status < 500 && event.status !== 403 && event.status !== 408;
  if (sure && pending.what === 'decide' && code === 'stale_item') {
    const cache = { ...state.cache };
    delete cache[pending.body.item];
    const next = { ...state, pending: null, cache, trouble: SAYS.changed, want: pending.body.item, hand: null, held: null };
    return { state: next, effects: [{ do: 'get', what: 'item', queue: pending.body.queue, item: pending.body.item }] };
  }
  if (sure && pending.what === 'decide' && code === 'already_answered') {
    // Another page answered this item, or took an answer back. What stands is
    // read again and shown, and nothing is replaced that the person has not seen.
    const cache = { ...state.cache };
    delete cache[pending.body.item];
    const next = { ...state, pending: null, cache, trouble: SAYS.already, want: pending.body.item, hand: null, held: null, tries: 0, again: null };
    return {
      state: next,
      effects: [
        { do: 'get', what: 'queue', queue: pending.body.queue, quiet: true },
        { do: 'get', what: 'item', queue: pending.body.queue, item: pending.body.item },
      ],
    };
  }
  if (sure && code === 'not_found' && state.queue) {
    // The list this page holds is of before a fill. Read it again.
    const next = { ...state, pending: null, hand: null, held: null, cache: {}, trouble: SAYS.gone, tries: 0, again: null };
    return { state: next, effects: [{ do: 'get', what: 'queue', queue: state.queue.id }] };
  }
  if (sure) {
    // What this page holds may be out of date. Read the list and the item
    // again, and leave on screen what the person was writing.
    const next = { ...state, pending: null, hand: null, trouble: wordsOf(event, SAYS.refused), tries: 0, again: null };
    const effects = state.queue ? [{ do: 'get', what: 'queue', queue: state.queue.id, quiet: true }] : [];
    if (state.queue && state.now) effects.push({ do: 'get', what: 'item', queue: state.queue.id, item: state.now.id, quiet: true });
    return { state: next, effects };
  }
  // The desk is down, or was started again and holds a new token, or could not
  // write. Ask it who it is now, then send the same answer again. Where the
  // desk says why it could not write, its words are said: a full disk is not
  // mended by starting the desk again.
  if (event.status >= 500 && wordsOf(event, '') !== '') return later(state, { do: 'get', what: 'state' }, wordsOf(event, ''));
  const why = event.status === 403 ? wordsOf(event, '') : '';
  return later(state, { do: 'get', what: 'state' }, [SAYS.notSaved, why].filter(Boolean).join(' '));
}

function written(state, event, at, pending) {
  const data = event.data || {};
  const counts = countsFrom(data);
  const base = {
    ...state,
    pending: null,
    tries: 0,
    again: null,
    trouble: '',
    queues: setCounts(state.queues, counts ? { queue: state.queue.id, ...counts } : null),
  };
  const queue = state.queue.id;
  const stands = number(state.wrote[queue]);
  if (pending.what === 'undo') return tookBack({ ...base, wrote: { ...state.wrote, [queue]: Math.max(0, stands - 1) }, undoAsked: null }, data, at);
  const n = data.line && typeof data.line === 'object' && typeof data.line.n === 'number' ? data.line.n : null;
  const counted = { ...base, wrote: { ...state.wrote, [queue]: stands + 1 }, undoAsked: null };
  // The line is an act of its own, or one more line of the part that is being covered.
  if (state.sweep !== null) counted.sweep = { ...state.sweep, ns: n === null ? state.sweep.ns : [...state.sweep.ns, n] };
  else if (n !== null) counted.acts = actsWith(state, [n]);
  if (pending.body.answer === 'move') {
    const line = data.line && typeof data.line === 'object' ? data.line : { ...pending.body };
    const moves = [...(state.now ? state.now.moves : []), line];
    const now = state.now ? { ...state.now, moves } : null;
    const cache = now ? { ...state.cache, [now.id]: { ...state.cache[now.id], moves } } : state.cache;
    return only(counted, { now, cache, hand: null, said: SAYS.moved });
  }
  const id = pending.body.item;
  const skipped = pending.body.answer === 'skip';
  // What is held of the item is of before the answer: it shows no answer of
  // your own, and none of another reviewer. It is asked for again when looked at.
  // An answer to a rule changes what a rule that leans on it would settle, so
  // nothing held of any rule is kept.
  const cache = leansOn(state, data) ? {} : { ...state.cache };
  delete cache[id];
  const items = setEntry(state.queue.items, id, skipped ? 'skipped' : 'done');
  // The note and the mark went with this answer.
  const next = { ...counted, cache, queue: { ...state.queue, items }, note: '', second: false };
  const more = nextOfPart(state, items, id);
  if (more !== null) return show(next, more, at);
  const to = nextItem(items, id, next.queue.group, next.reviewer);
  const title = titleOf(state, id);
  const whole = next.sweep !== null && coversOf(state) ? coveredWords(next) : null;
  // What went with the answer is said with it, so that a mark or a note that
  // was not meant is seen before the next answer.
  const with_ = [pending.body.note !== '' ? ', with a note' : '', pending.body.second === true ? ', second reviewer asked' : ''].join('');
  // An answer that a build will set aside is said to be saved, and to wait.
  const answered = state.now && state.now.id === id ? state.now.item : state.cache[id] ? state.cache[id].item : null;
  const aside = asideOf(state.queue.question, answered);
  const waits = aside !== null && aside.answers.includes(pending.body.answer) && aside.saved !== '' ? ` ${aside.saved}` : '';
  const saved = `Saved: ${labelAs(state, pending.body.answer)}${onWhich(state, pending.body.detail)}${with_}, for ${title}.${waits}${ruledWords(data)}`;
  const words = whole || (skipped ? `Skipped${with_}: ${title}. ${SAYS.skipped}` : saved);
  next.acts = covered(next).acts;
  next.sweep = null;
  if (to === null) {
    if (typeof data.next === 'string' && next.queue.group === null) {
      // The desk knows of an item this page does not. Its list has moved on.
      return { state: { ...next, first: data.next, want: data.next, said: words }, effects: [{ do: 'get', what: 'queue', queue: next.queue.id }] };
    }
    return show(next, null, at, words);
  }
  return show(next, to, at, words);
}

// True where the answer that came back was to a rule: the desk then says what
// the rules settled.
function leansOn(state, data) {
  return Boolean(data && data.ruled && typeof data.ruled === 'object');
}

// What an answer to a rule did, in words, or nothing where the answer was to
// no rule: how many items the rule settled, and how many of its answers were
// taken back. So the founder sees at once what a yes waved through. Where an
// adopted rule leans on one that is not, it says how many items that holds back.
function ruledWords(data) {
  const ruled = data && data.ruled && typeof data.ruled === 'object' ? data.ruled : null;
  if (ruled === null) return '';
  const settled = number(ruled.settled);
  const back = number(ruled.taken_back);
  const held = number(ruled.held_back);
  const said = [];
  if (settled > 0) said.push(`${settled} ${settled === 1 ? 'item was' : 'items were'} settled by the rule.`);
  if (back > 0) said.push(`${back} ${back === 1 ? 'answer' : 'answers'} the rule gave ${back === 1 ? 'was' : 'were'} taken back.`);
  const waits = held === 1 ? '1 item waits until the rule it leans on is adopted.' : `${held} items wait until the rule each leans on is adopted.`;
  if (held > 0) said.push(settled > 0 || back > 0 ? waits : `Nothing was settled: ${waits}`);
  return ` ${said.length > 0 ? said.join(' ') : SAYS.nothingChanged}`;
}

// A rule as the desk names it on its screen, from its code.
function ruleTitle(code) {
  const words = String(code).replace(/_/g, ' ');
  return words.charAt(0).toUpperCase() + words.slice(1);
}

// What the desk says of a rule that leans on others, as a line of the rule:
// which of them stand adopted, and what a yes would settle as they stand. It
// stands under the line that says what the rule leans on. Nothing for a rule
// that stands by itself.
function leanLine(now) {
  const leans = now && Array.isArray(now.leans) ? now.leans.filter((row) => row && typeof row.rule === 'string') : [];
  if (leans.length === 0) return null;
  const named = (rows) => rows.map((row) => ruleTitle(row.rule)).join(', ');
  const adopted = leans.filter((row) => row.stands === 'adopted');
  const again = leans.filter((row) => row.stands === 'asked_again');
  const not = leans.filter((row) => row.stands !== 'adopted' && row.stands !== 'asked_again');
  const count = (rows) => rows.reduce((sum, row) => sum + number(row.items), 0);
  if (adopted.length === 0 && again.length === 0) {
    return { label: SAYS.asTheRulesStand, value: `None of the rules it leans on is adopted: ${named(leans)}. A yes to this rule settles nothing until one of them is adopted.`, source_id: '' };
  }
  const said = [];
  if (adopted.length > 0) said.push(`Adopted: ${named(adopted)}.`);
  if (again.length > 0) said.push(`Adopted before the draft changed, and asked again: ${named(again)}.`);
  if (not.length > 0) said.push(`Not adopted: ${named(not)}.`);
  const settles = count(adopted);
  const leaves = count(leans) - settles;
  const lean = (n) => (n === 1 ? '1 item that leans' : `${n} items that lean`);
  said.push(
    settles === 0
      ? 'A yes to this rule settles nothing until one of them is adopted.'
      : `A yes to this rule settles the ${lean(settles)} on a rule that is adopted${leaves > 0 ? `, and leaves the ${leaves} that ${leaves === 1 ? 'does' : 'do'} not` : ''}.`,
  );
  return { label: SAYS.asTheRulesStand, value: said.join(' '), source_id: '' };
}

// The lines of an item that is read in the middle of the page. A rule that
// leans on others says how they stand, under the line that says it leans.
function recordLines(now) {
  const held = Array.isArray(now.item.lines) ? now.item.lines : [];
  // Before the items a rule shows, the key that opens them.
  const first = drawnOf(now.item) === null ? -1 : held.findIndex((line) => line && typeof line.label === 'string' && line.label.startsWith(DRAWN));
  const open = { label: SAYS.toOpenThem, value: SAYS.openDrawn, source_id: '' };
  const lines = first < 0 ? held : [...held.slice(0, first), open, ...held.slice(first)];
  const lean = leanLine(now);
  if (lean === null) return lines;
  const at = lines.findIndex((line) => line && line.label === SAYS.leansOn);
  const after = at >= 0 ? at + 1 : Math.min(2, lines.length);
  return [...lines.slice(0, after), lean, ...lines.slice(after)];
}

// How the line of an item that a rule shows begins.
const DRAWN = 'Drawn at random';

// The items a rule shows, as the rule holds them: the queue they are of and
// their ids, in the order of their lines. Null where the item shows none.
function drawnOf(item) {
  const preset = item && item.preset && typeof item.preset === 'object' ? item.preset : null;
  const list = preset !== null && Array.isArray(preset.drawn) ? preset.drawn.filter((id) => typeof id === 'string' && id !== '') : [];
  return preset !== null && typeof preset.queue === 'string' && preset.queue !== '' && list.length > 0 ? { queue: preset.queue, list } : null;
}

// Where the person is among the items drawn for a rule, in words, or nothing.
// It stays on the screen while one of them is looked at.
function visitWords(state) {
  const visit = state.visit;
  if (visit === null) return '';
  return `Drawn for the rule ${visit.title}, ${visit.at + 1} of ${visit.list.length}. Nothing is decided here. ] and [ go through them. o goes back to the rule.`;
}

// Open the items a rule shows, or go back to the rule. An item is opened in
// its own queue, so that it is shown as it is there: with its map, what is
// known of it and the answers. No answer is taken while it is looked at.
function openDrawn(state, at) {
  if (state.pending || busy(state)) return only(state);
  if (state.visit !== null) {
    const back = state.visit;
    return openQueue({ ...state, visit: null, queue: null, now: null, trouble: '' }, back.from, back.rule);
  }
  const drawn = state.queue && state.now ? drawnOf(state.now.item) : null;
  if (drawn === null || !state.queues.some((row) => row.queue === drawn.queue)) return say(state, SAYS.noneDrawn);
  const visit = { from: state.queue.id, rule: state.now.id, title: titleOf(state, state.now.id), queue: drawn.queue, list: drawn.list, at: 0 };
  return openQueue({ ...state, visit, queue: null, now: null, trouble: '' }, drawn.queue, drawn.list[0]);
}

// The item before or after among those drawn for a rule.
function lookDrawn(state, by, at) {
  if (state.pending || !state.queue) return only(state);
  const to = state.visit.at + (by < 0 ? -1 : 1);
  if (to < 0) return say(state, SAYS.firstDrawn);
  if (to >= state.visit.list.length) return say(state, SAYS.lastDrawn);
  return show({ ...state, visit: { ...state.visit, at: to }, trouble: '' }, state.visit.list[to], at);
}

// Which of the questions about one area an answer was to, in words, or
// nothing. Where an area is asked about many times, every item of it has the
// name of the area: what tells them apart is what the item was made with.
function onWhich(state, detail) {
  const covers = coversOf(state);
  if (covers === null || typeof covers.by !== 'string' || !detail || typeof detail !== 'object') return '';
  const which = Object.entries(detail)
    .filter(([key, value]) => key !== covers.by && key !== 'proposed' && typeof value === 'string' && value !== '')
    .map(([, value]) => value);
  return which.length > 0 ? `, on ${which.join(', ')}` : '';
}

// The name of an item, where the page holds it. Else its id.
function titleOf(state, id) {
  const held = state.now && state.now.id === id ? state.now : state.cache[id];
  return held && held.item && typeof held.item.title === 'string' && held.item.title !== '' ? held.item.title : String(id);
}

// An answer in words, as the person read it when they gave it.
function labelAs(state, code) {
  if (code === 'skip') return 'Skipped';
  if (code === 'move') return 'A move';
  const entry = answersOf(state).find((one) => one.code === code);
  return entry ? labelNow(state, entry) : String(code);
}

// An undo came back. Where one key wrote several lines, as the key that says a
// whole area is not known does, the rest of them are taken back too, one after
// another, before anything is shown: a person takes back what a key did, and
// not a seventh of it. The desk takes back the last line that stands, so the
// lines of one key come back from the last to the first.
function tookBack(state, data, at) {
  const line = data.undone && typeof data.undone === 'object' ? data.undone : null;
  const queue = state.queue.id;
  const acts = Array.isArray(state.acts[queue]) ? state.acts[queue] : [];
  const top = acts.length > 0 ? acts[acts.length - 1] : [];
  const ours = line !== null && top.includes(line.n);
  // A line this page did not write was taken back: from another page, or of an
  // earlier sitting. What the page held of its own keys no longer fits, and goes.
  const rest = ours ? top.filter((n) => n < line.n) : [];
  const kept = ours ? [...acts.slice(0, -1), ...(rest.length > 0 ? [rest] : [])] : [];
  const next = { ...state, acts: { ...state.acts, [queue]: kept }, unsweep: null };
  const sweep = state.unsweep;
  if (sweep !== null && ours && rest.length > 0) {
    const body = { queue };
    return { state: { ...next, unsweep: sweep, pending: { what: 'undo', body } }, effects: [{ do: 'post', what: 'undo', body }] };
  }
  const whole = sweep !== null && ours && coversOf(state) !== null ? `${SAYS.tookBack} ${coversOf(state).label}, ${answersWord(sweep.of)}` : null;
  return undone(next, data, at, whole);
}

function undone(state, data, at, whole = null) {
  const line = data.undone && typeof data.undone === 'object' ? data.undone : null;
  if (line === null || typeof line.item !== 'string') return say(state, SAYS.nothingToUndo);
  // The item taken back is shown next, and the words end with its name.
  const back = data.ruled && number(data.ruled.taken_back) > 0 ? `.${ruledWords(data).replace(/\.$/, '')}` : '';
  const said = whole || `${SAYS.tookBack} ${line.answer === 'move' ? `the move of cell ${line.part}` : `${labelAs(state, line.answer)}${onWhich(state, line.detail)}`}${back}`;
  const cache = leansOn(state, data) ? {} : { ...state.cache };
  delete cache[line.item];
  // The note and the mark of the answer taken back are given back, to be used
  // again. Until the item is on screen again, no key is taken for the one that is.
  const again = line.answer === 'move' ? {} : { note: typeof line.note === 'string' ? line.note : '', second: line.second === true };
  const clean = { ...state, ...again, cache, first: line.item, want: line.item, saidOf: line.item, hand: null, held: null, noteOpen: false, said };
  return { state: withClock(clean, at), effects: [{ do: 'get', what: 'queue', queue: state.queue.id }] };
}

// ---------------------------------------------------------------- what the person did

// Why nothing may be written now, or null when something may. While one answer
// is on its way, or the next item is, a key is dropped and nothing is said.
function blocked(state) {
  if (state.mixed) return SAYS.mixed;
  if (state.synthetic === null) return SAYS.notKnown;
  if (state.pending !== null || state.want !== null) return state.trouble;
  if (state.paused) return SAYS.paused;
  return null;
}

function send(state, body) {
  return {
    state: { ...state, pending: { what: 'decide', body }, held: null, noteOpen: false, draft: '' },
    effects: [{ do: 'post', what: 'decide', body }],
  };
}

// The number of the line the page shows as standing: for the item, or for one
// of its cells. The desk refuses an answer from a page that shows another.
function standsOf(now, part = '') {
  if (part !== '') {
    const moved = (now.moves || []).filter((move) => move.part === part && typeof move.n === 'number');
    return moved.length > 0 ? Math.max(...moved.map((move) => move.n)) : null;
  }
  return now.mine && typeof now.mine.n === 'number' ? now.mine.n : null;
}

function bodyOf(state, code, at, note) {
  const entry = entryOf(state, state.now.id);
  const real = code !== 'skip';
  return {
    queue: state.queue.id,
    item: state.now.id,
    rev: state.now.item.rev,
    part: '',
    answer: code,
    note,
    second: state.second,
    settles: real && settles(state.reviewer, entry ? entry.state : ''),
    detail: real ? detailOf(state.queue.question, state.now.item, state.pick, state.of) : {},
    seconds: clockSeconds(state.clock, at),
    stands: standsOf(state.now),
  };
}

// The answer the draft proposes for the item on screen, or null. It is marked
// among the answers, and Enter gives it, so that to accept costs one key
// whichever number the answer is on.
function proposedOf(state) {
  const item = state.now ? state.now.item : null;
  const code = item && item.preset && typeof item.preset.proposed === 'string' ? item.preset.proposed : null;
  return code !== null && answersOf(state).some((one) => one.code === code) ? code : null;
}

// A name proposed as another name of an area cannot be made an area at the
// desk: only the areas build gives an area its id. So the answer is not
// offered on such a name, and every other answer keeps its key.
function notAnArea(state, code) {
  return code === 'area' && Boolean(state.queue && state.now) && adds(state.queue.question, 'pick') && String(state.now.id).startsWith('a:');
}

function answer(state, code, at) {
  const stop = blocked(state);
  if (stop !== null) return only(state, { trouble: stop });
  if (!state.now || !state.queue) return only(state);
  if (at - state.now.shownAt < GRACE_MS) return say(state, SAYS.tooSoon);
  if (notAnArea(state, code)) return say(state, SAYS.notAnArea);
  if (NAMES_AN_AREA.includes(code) && namesAreas(state.queue.question, state.now.item) && state.of.length === 0) {
    return say(state, SAYS.areaNeeded);
  }
  if (code !== 'skip' && state.note === '' && needsNote(state.queue.question, code, state.now.moves)) {
    return {
      state: { ...state, held: code, noteOpen: true, draft: '', said: SAYS.noteNeeded },
      effects: [{ do: 'focus', on: 'note' }],
    };
  }
  return send(state, bodyOf(state, code, at, state.note));
}

// A note is one line of plain text. A tab or an end of line that was pasted is
// made a space, and a mark that is not seen is taken out, as the desk would
// refuse them.
function plain(text) {
  return String(text)
    .replace(/[\p{Cf}]/gu, '')
    .replace(/[\p{Cc}\p{Zl}\p{Zp}]+/gu, ' ')
    .replace(/ {2,}/g, ' ')
    .trim();
}

// Give one answer to every open item of the part that the item on screen is
// of, one after another. Each is a line of its own, and one undo takes them
// all back: see `tookBack`.
function cover(state, at) {
  const stop = blocked(state);
  if (stop !== null) return only(state, { trouble: stop });
  if (!state.now || !state.queue) return only(state);
  if (at - state.now.shownAt < GRACE_MS) return say(state, SAYS.tooSoon);
  const part = partOf(state, state.now.id);
  if (part === null) return only(state);
  const plain = { ...state, sweep: { part, title: titleOf(state, state.now.id), ns: [] }, note: '', second: false };
  return send(plain, bodyOf(plain, coversOf(state).code, at, ''));
}

// The next open item of the part that is being covered, or null when it is done.
function nextOfPart(state, items, after) {
  if (state.sweep === null) return null;
  const at = items.findIndex((entry) => entry.id === after);
  const order = [...items.slice(at + 1), ...items.slice(0, at + 1)];
  const found = order.find((entry) => entry.part === state.sweep.part && entry.id !== after && ['open', 'stale', 'skipped'].includes(entry.state));
  return found ? found.id : null;
}

function keepNote(state, at) {
  const text = plain(state.draft).slice(0, MOST_NOTE);
  if (state.held !== null) {
    if (text === '') return say(state, SAYS.noteNeeded);
    const next = { ...state, note: text };
    const sent = send(next, bodyOf(next, state.held, at, text));
    return { state: sent.state, effects: [...sent.effects, { do: 'focus', on: 'page' }] };
  }
  return {
    state: { ...state, note: text, noteOpen: false, draft: '', notedAt: at, said: text === '' ? SAYS.noteLeft : SAYS.noteKept },
    effects: [{ do: 'focus', on: 'page' }],
  };
}

function leaveNote(state) {
  const said = state.held !== null ? SAYS.answerLeft : SAYS.noteLeft;
  return {
    state: { ...state, noteOpen: false, draft: '', held: null, said },
    effects: [{ do: 'focus', on: 'page' }],
  };
}

function undo(state, at) {
  const stop = blocked(state);
  if (stop !== null) return only(state, { trouble: stop });
  if (!state.queue) return only(state);
  // Under the same quarter second as an answer: a key struck as an item appears
  // must not take back the answer just given.
  if (state.now && at - state.now.shownAt < GRACE_MS) return say(state, SAYS.tooSoon);
  if (number(state.wrote[state.queue.id]) <= 0 && state.undoAsked !== state.queue.id) {
    // What would be taken back was saved in an earlier sitting, or from another page.
    return say(state, SAYS.undoEarlier, { undoAsked: state.queue.id });
  }
  const body = { queue: state.queue.id };
  // Where the last key of this sitting wrote several lines, all are taken back.
  const acts = Array.isArray(state.acts[state.queue.id]) ? state.acts[state.queue.id] : [];
  const top = acts.length > 0 ? acts[acts.length - 1] : [];
  const unsweep = top.length > 1 ? { of: top.length } : null;
  return { state: { ...state, pending: { what: 'undo', body }, unsweep }, effects: [{ do: 'post', what: 'undo', body }] };
}

function look(state, by, at) {
  if (state.pending || !state.queue) return only(state);
  const from = state.now ? state.now.id : state.want;
  const to = lookItem(state.queue.items, from, by, state.queue.group);
  if (to === null) return say(state, by < 0 ? SAYS.firstItem : SAYS.lastItem);
  return show({ ...state, trouble: '' }, to, at);
}

// Go to the next flagged item that is not done. It decides nothing, and a note
// that was kept and a mark stay, as they do when an item is looked at.
function toFlagged(state, at) {
  if (state.pending || !state.queue) return only(state);
  const from = state.now ? state.now.id : state.want;
  const to = nextFlagged(state.queue.items, from, state.queue.group, state.reviewer);
  if (to === null) return say(state, SAYS.noFlagged);
  if (to === from) return say(state, SAYS.lastFlagged);
  return show({ ...state, trouble: '' }, to, at);
}

// A click on a cell of a name's map: the area of the cell is one the name is
// given to, or is no longer.
function nameArea(state, area) {
  if (state.of.includes(area)) {
    const of = state.of.filter((one) => one !== area);
    return say(state, SAYS.areaBack, { of });
  }
  if (area === ownArea(state.now.item)) return say(state, SAYS.areaSelf);
  if (state.of.length >= MOST_AREAS) return say(state, SAYS.areasMost);
  return say(state, SAYS.areaChosen, { of: [...state.of, area] });
}

function cell(state, event) {
  if (!state.now || !state.queue) return only(state);
  const names = namesAreas(state.queue.question, state.now.item);
  if (!names && !adds(state.queue.question, 'move')) return say(state, SAYS.noMove);
  const stop = blocked(state);
  if (stop !== null) return only(state, { trouble: stop });
  if (typeof event.cell !== 'string' || typeof event.area !== 'string') return only(state);
  if (names) return nameArea(state, event.area);
  if (state.hand === null) {
    const hand = { cell: event.cell, area: event.area };
    return say(state, `Took up cell ${event.cell}. Now choose a cell of the area it should join. Esc lets go.`, { hand });
  }
  if (event.cell === state.hand.cell) return say(state, SAYS.letGo, { hand: null });
  if (event.area === state.hand.area) return say(state, SAYS.sameArea);
  const body = {
    queue: state.queue.id,
    item: state.now.id,
    rev: state.now.item.rev,
    part: state.hand.cell,
    answer: 'move',
    note: '',
    second: false,
    settles: false,
    detail: { from: state.hand.area, to: event.area },
    seconds: clockSeconds(state.clock, event.at),
    stands: standsOf(state.now, state.hand.cell),
  };
  return { state: { ...state, pending: { what: 'decide', body } }, effects: [{ do: 'post', what: 'decide', body }] };
}

function rowsOf(state, kind) {
  if (kind === 'queues') return state.queues.map((row) => ({ id: row.queue, text: [progress(row), waitsWords(row), redraftWords(row)].filter(Boolean).join('. ') }));
  if (kind === 'groups') {
    if (!state.queue) return [];
    const rows = groupsOf(state.queue.items, state.reviewer);
    const all = rows.reduce((sum, row) => sum + row.left, 0);
    return [
      { id: null, text: `${SAYS.everyGroup}: ${all} left` },
      ...rows.map((row) => ({ id: row.group, text: `${row.group}: ${row.left} left of ${row.total}` })),
    ];
  }
  return [];
}

function openPanel(state, kind) {
  if (state.pending) return only(state);
  if (kind === 'groups') {
    if (!state.queue) return say(state, SAYS.noQueue);
    if (groupsOf(state.queue.items, state.reviewer).length < 2) return say(state, SAYS.noGroups);
  }
  const rows = rowsOf(state, kind);
  let at = 0;
  if (kind === 'queues' && state.queue) at = Math.max(0, rows.findIndex((row) => row.id === state.queue.id));
  if (kind === 'groups') at = Math.max(0, rows.findIndex((row) => row.id === state.queue.group));
  // The list of queues is read again as it opens: an answer in one queue changes
  // what another waits on.
  const fresh = kind === 'queues' ? [{ do: 'get', what: 'state' }] : [];
  return { state: { ...state, panel: { kind, at }, noteOpen: false, held: null }, effects: [{ do: 'focus', on: 'panel' }, ...fresh] };
}

function closePanel(state) {
  if (state.panel === null) return only(state);
  return { state: { ...state, panel: null }, effects: [{ do: 'focus', on: 'page' }] };
}

function choose(state, index, at) {
  if (state.panel === null) return only(state);
  const rows = rowsOf(state, state.panel.kind);
  const row = rows[index];
  if (!row) return only(state);
  if (state.panel.kind === 'queues') {
    const queue = state.queue && state.queue.id === row.id ? state.queue : null;
    // A queue chosen from the list ends a look at what was drawn for a rule.
    return openQueue({ ...state, visit: null, queue, now: null, trouble: '' }, row.id);
  }
  if (state.panel.kind === 'groups') {
    const next = { ...state, panel: null, trouble: '', queue: { ...state.queue, group: row.id } };
    const keep = state.now && inGroup(entryOf(next, state.now.id) || {}, row.id) ? state.now.id : null;
    return show(next, keep !== null ? keep : nextItem(next.queue.items, null, row.id, next.reviewer), at);
  }
  return closePanel(state);
}

// ---------------------------------------------------------------- keys

// True where the item on screen is shown as a map.
function showsMap(state) {
  return Boolean(state.now && state.queue && state.queue.question.view === 'map' && state.now.item.map);
}

// What a key means now, or null when it is the browser's to deal with.
// `inNote` is true when the key was struck in the note.
export function keyAction(state, key) {
  if (key.ctrl || key.meta || key.alt) return null;
  const name = key.key;
  if (state.noteOpen || key.inNote) {
    if (name === 'Enter') return { type: 'keep' };
    if (name === 'Escape') return { type: 'leave' };
    return null;
  }
  if (state.panel !== null) {
    if (name === 'Escape') return { type: 'close' };
    if (state.panel.kind === 'keys') return name === '?' ? { type: 'close' } : null;
    if (name === 'ArrowUp') return { type: 'move', by: -1 };
    if (name === 'ArrowDown') return { type: 'move', by: 1 };
    if (name === 'Enter' && !key.onButton) return { type: 'choose', index: state.panel.at };
    if (state.panel.kind === 'queues') {
      const index = QUEUE_KEYS.indexOf(name.toLowerCase());
      if (name.length === 1 && index >= 0) return { type: 'choose', index };
    }
    return null;
  }
  // Where a map is shown the arrows move it, with Shift or without: an arrow
  // must never leave the item and drop the cell in the hand. `[` and `]` look
  // at the item before and after, in every queue.
  if (name.startsWith('Arrow') && (key.shift || showsMap(state))) return { type: 'map', op: name.slice(5).toLowerCase(), small: key.shift === true };
  if (name === 'ArrowLeft' || name === '[') return { type: 'look', by: -1 };
  if (name === 'ArrowRight' || name === ']') return { type: 'look', by: 1 };
  if (name === '+' || name === '=') return { type: 'map', op: 'in' };
  if (name === '-' || name === '_') return { type: 'map', op: 'out' };
  if (name === '0') return { type: 'map', op: 'fit' };
  // What is known of an item may be longer than its box. It is paged by a key
  // that is no letter, so that it is never held and never taken for a word.
  if (name === '.' || name === 'PageDown') return { type: 'page', by: 1 };
  if (name === ',' || name === 'PageUp') return { type: 'page', by: -1 };
  if (name === 'Escape') {
    if (state.hand !== null) return { type: 'letgo' };
    return state.note !== '' || state.second ? { type: 'drop' } : null;
  }
  if (key.repeat) return null;
  if (/^[1-9]$/.test(name)) return { type: 'answer', index: Number(name) - 1 };
  // Enter on a button is the button's own: it does what a click on it does.
  if (name === 'Enter') return key.onButton ? null : { type: 'accept' };
  if (name === '?') return { type: 'panel', kind: 'keys' };
  switch (name.toLowerCase()) {
    case 's':
      return { type: 'skip' };
    case 'u':
      return { type: 'undo' };
    case 'n':
      return { type: 'note' };
    case 'f':
      return { type: 'second' };
    case 'j':
      return { type: 'flagged' };
    case 'o':
      return { type: 'drawn' };
    case 'g':
      return { type: 'panel', kind: 'groups' };
    case 'q':
      return { type: 'panel', kind: 'queues' };
    case 'p':
      return { type: 'pause' };
    case 'm':
      return { type: 'map', op: 'act' };
    case 'a':
    case 'b':
    case 'c':
    case 'd':
    case 'e':
      return { type: 'pick', index: name.toLowerCase().charCodeAt(0) - 97 };
    default:
      return null;
  }
}

// ---------------------------------------------------------------- words, and keys

// What belongs to the next item when it is asked for while an answer is on
// its way: it waits until the next item is shown.
const FOR_THE_NEXT = ['note', 'second', 'pick'];

function busy(state) {
  return state.pending !== null || state.want !== null;
}

// Carry out what a key means, or keep it for the next item.
function acted(state, action, at) {
  if (busy(state) && FOR_THE_NEXT.includes(action.type)) {
    return only(state, { queued: [...state.queued, action].slice(-8) });
  }
  return react(state, action, at);
}

function andThen(first, then) {
  const out = then(first.state);
  return { state: out.state, effects: [...first.effects, ...out.effects] };
}

// The moment of the letters that were held is over: they act, in order, each
// as of when it was struck. So a key struck as an item appeared is still too soon.
function release(state) {
  let out = only(state, { heldKeys: [] });
  for (const held of state.heldKeys) out = andThen(out, (now) => acted(now, held.action, held.at));
  return out;
}

// A key was struck. A letter struck with the note shut may be the first of some
// words, so it is held a moment. Three letters inside a second are words: none
// of them is taken, and the page says how to write a note.
function struck(state, event, at) {
  const action = keyAction(state, event);
  const name = typeof event.key === 'string' ? event.key : '';
  if (state.noteOpen || event.inNote === true || state.panel !== null) {
    // In the note a letter is a letter, and in a list it chooses nothing.
    const still = state.heldKeys.length === 0 && state.letters.length === 0 ? state : { ...state, heldKeys: [], letters: [] };
    return action === null ? only(still) : react(still, action, at);
  }
  if (event.ctrl || event.meta || event.alt) return only(state);
  if (name === 'Escape') {
    const quiet = { ...state, heldKeys: [], letters: [], typingUntil: 0 };
    return action === null ? only(quiet) : react(quiet, action, at);
  }
  const typed = name.length === 1 || name === 'Enter' || name === 'Backspace';
  if (at < state.typingUntil) {
    // Still words. Whatever the key, it is taken for one of them.
    return typed ? say(state, SAYS.pressN, { typingUntil: at + BURST_MS }) : only(state);
  }
  const held = state.heldKeys.length > 0 || state.letters.some((when) => at - when < HOLD_MS);
  if (name === ' ' && event.onButton !== true && held) {
    // A space after a letter that is still held ends a word. A sentence often
    // begins with a word of one letter or two, which three letters would not catch.
    return say(state, SAYS.pressN, { letters: [], heldKeys: [], typingUntil: at + BURST_MS });
  }
  if (!/^[a-z]$/i.test(name)) {
    // No letter: it acts at once, after whatever was held before it.
    const first = release(state);
    return action === null ? first : andThen(first, (now) => react(now, action, at));
  }
  const letters = [...state.letters.filter((when) => at - when < BURST_MS), at];
  if (letters.length >= 3) {
    return say(state, SAYS.pressN, { letters: [], heldKeys: [], typingUntil: at + BURST_MS });
  }
  if (action !== null && action.type === 'note') {
    // The note opens at once, so that what is typed next is typed in it.
    return acted({ ...state, letters: [], heldKeys: [] }, action, at);
  }
  const heldKeys = action === null ? state.heldKeys : [...state.heldKeys, { action, at }];
  return { state: { ...state, letters, heldKeys }, effects: [{ do: 'hold', ms: HOLD_MS }] };
}

// ---------------------------------------------------------------- the one step

// What is so after something happened, and what to do about it.
// Every event carries `at`, the time in milliseconds, from the page's clock.
export function step(state, event) {
  const at = typeof event.at === 'number' ? event.at : 0;
  const out = react(state, event, at);
  return { state: withClock(out.state, at), effects: out.effects };
}

// What decides something, or goes elsewhere in the queue: none of it is done
// while an item that was drawn for a rule is looked at.
const NOT_WHILE_VISITING = ['answer', 'accept', 'skip', 'undo', 'cell', 'flagged'];

function react(state, event, at) {
  if (state.visit !== null && NOT_WHILE_VISITING.includes(event.type)) return say(state, SAYS.visiting);
  switch (event.type) {
    case 'open':
      return { state, effects: [{ do: 'get', what: 'state' }] };
    case 'got': {
      if (event.what === 'state') return gotState(state, event, at);
      if (event.ok && !sameData(state, event.data)) {
        return only(state, { mixed: true, trouble: SAYS.mixed });
      }
      if (event.what === 'queue') return gotQueue(state, event, at);
      if (event.what === 'item') return gotItem(state, event, at);
      return only(state);
    }
    case 'wrote': {
      if (event.ok && !sameData(state, event.data)) {
        return only(state, { pending: null, mixed: true, trouble: SAYS.mixed });
      }
      return wrote(state, event, at);
    }
    case 'retry':
      if (state.again === null) return only(state);
      return { state: { ...state, again: null }, effects: [state.again] };
    case 'seen':
      return only(state, { seen: event.seen === true });
    case 'typed':
      return only(state, { draft: String(event.text || '').slice(0, MOST_NOTE) });
    case 'closed':
      return state.panel === null ? only(state) : only(state, { panel: null });
    case 'cell':
      return cell(state, { ...event, at });
    case 'key':
      return struck(state, event, at);
    case 'release':
      return release(state);
    case 'drop':
      return say(state, SAYS.dropped, { note: '', second: false });
    case 'answer': {
      const chosen = answersOf(state)[event.index];
      if (chosen) return answer(state, chosen.code, at);
      return event.index === answersOf(state).length && coversOf(state) ? cover(state, at) : only(state);
    }
    case 'accept': {
      if (!state.now) return only(state);
      if (state.notedAt !== null && at - state.notedAt < GRACE_MS) return say(state, SAYS.tooSoon);
      const code = proposedOf(state);
      return code === null ? say(state, SAYS.nothingProposed) : answer(state, code, at);
    }
    case 'skip':
      return answer(state, 'skip', at);
    case 'undo':
      return undo(state, at);
    case 'note': {
      if (busy(state)) return acted(state, event, at);
      if (!state.now) return only(state);
      return {
        state: { ...state, noteOpen: true, draft: state.note, panel: null, said: SAYS.noteOpen },
        effects: [{ do: 'focus', on: 'note' }],
      };
    }
    case 'keep':
      return state.noteOpen ? keepNote(state, at) : only(state);
    case 'leave':
      return state.noteOpen ? leaveNote(state) : only(state);
    case 'blur': {
      // The person went elsewhere without Enter or Esc. What was typed is
      // kept as the note. An answer that waited for it is taken back: going
      // elsewhere must never send one.
      if (!state.noteOpen) return only(state);
      const text = plain(state.draft).slice(0, MOST_NOTE);
      const said = state.held !== null ? SAYS.answerLeft : text === '' ? SAYS.noteLeft : SAYS.noteKept;
      return only(state, { note: text, noteOpen: false, draft: '', held: null, said });
    }
    case 'second': {
      if (!state.now) return only(state);
      const second = typeof event.on === 'boolean' ? event.on : !state.second;
      return say(state, second ? SAYS.secondOn : SAYS.secondOff, { second });
    }
    case 'pick': {
      if (!state.now || !state.queue) return only(state);
      const picks = Array.isArray(state.now.item.picks) ? state.now.item.picks : [];
      if (!adds(state.queue.question, 'pick') || picks.length === 0) return say(state, SAYS.noPick);
      if (event.index < 0 || event.index >= picks.length) return only(state);
      return say(state, `Spelling: ${picks[event.index]}`, { pick: event.index });
    }
    case 'look':
      return state.visit !== null ? lookDrawn(state, event.by, at) : look(state, event.by, at);
    case 'drawn':
      return openDrawn(state, at);
    case 'flagged':
      return toFlagged(state, at);
    case 'pause': {
      const paused = !state.paused;
      return only(state, { paused, said: paused ? SAYS.paused : SAYS.goOn, trouble: state.trouble === SAYS.paused ? '' : state.trouble });
    }
    case 'letgo':
      return state.hand === null ? only(state) : say(state, SAYS.letGo, { hand: null });
    case 'map': {
      if (!state.now || !state.now.item.map) return say(state, SAYS.noMap);
      if (event.op === 'act' && !adds(state.queue.question, 'move') && !namesAreas(state.queue.question, state.now.item)) {
        return say(state, SAYS.noMove);
      }
      return { state, effects: [{ do: 'map', op: event.op, ...(typeof event.small === 'boolean' ? { small: event.small } : {}) }] };
    }
    case 'page':
      return state.now ? { state, effects: [{ do: 'scroll', by: event.by < 0 ? -1 : 1 }] } : only(state);
    case 'panel':
      return openPanel(state, event.kind);
    case 'close':
      return closePanel(state);
    case 'move': {
      if (state.panel === null) return only(state);
      const rows = rowsOf(state, state.panel.kind);
      if (rows.length === 0) return only(state);
      const to = Math.max(0, Math.min(rows.length - 1, state.panel.at + event.by));
      return { state: { ...state, panel: { ...state.panel, at: to } }, effects: [{ do: 'focus', on: 'panel' }] };
    }
    case 'choose':
      return choose(state, event.index, at);
    default:
      return only(state);
  }
}

// ---------------------------------------------------------------- what is shown

function bannerOf(state) {
  if (state.mixed) return { kind: 'unknown', text: SAYS.mixed };
  if (state.synthetic === true) return { kind: 'made-up', text: state.banner || SAYS.madeUp };
  if (state.synthetic === false) return { kind: 'real', text: state.banner || SAYS.real };
  return { kind: 'unknown', text: state.phase === 'loading' ? SAYS.loading : SAYS.notKnown };
}

function mineWords(state) {
  const now = state.now;
  if (!now || !now.mine) return '';
  const mine = now.mine;
  const note = mine.note ? ` Note: ${mine.note}` : '';
  if (mine.answer === 'skip') return `${SAYS.skippedBefore}${note}`;
  const stale = typeof mine.rev === 'string' && mine.rev !== now.item.rev;
  const label = labelOf(state, mine.answer);
  const rule = state.queue.id !== 'rules' && mine.detail && typeof mine.detail.rule === 'string' ? mine.detail.rule : '';
  if (rule !== '' && stale) return `Before this item changed the rule "${rule.replace(/_/g, ' ')}" settled it: ${label}. It is open again.`;
  // No person read what a rule settled. The person may still answer it.
  if (rule !== '') return `Settled by the rule "${rule.replace(/_/g, ' ')}": ${label}. Your own answer takes its place.`;
  if (stale) return `Before this item changed you answered: ${label}. It is open again.${note}`;
  return `You answered: ${label}.${note}`;
}

function disputeWords(state) {
  const entry = state.now ? entryOf(state, state.now.id) : null;
  if (!entry || entry.state !== 'disputed') return '';
  return state.reviewer === 'r1' ? SAYS.settles : SAYS.inDispute;
}

function flagWords(state) {
  const codes = state.now && Array.isArray(state.now.item.flags) ? state.now.item.flags : [];
  if (codes.length === 0) return '';
  const words = state.queue.question.flags && typeof state.queue.question.flags === 'object' ? state.queue.question.flags : {};
  return `Here because: ${codes.map((code) => (typeof words[code] === 'string' ? words[code] : code)).join(', ')}`;
}

function mainOf(state) {
  if (state.phase === 'loading') return { kind: 'wait', text: SAYS.loading };
  if (!state.queue) return { kind: 'wait', text: SAYS.noQueue };
  if (!state.now) {
    if (state.want !== null) return { kind: 'wait', text: SAYS.loading };
    const counts = countsOf(state);
    const title = counts ? counts.title || counts.queue : state.queue.id;
    const group = state.queue.group === null ? '' : ` in ${state.queue.group}`;
    return { kind: 'wait', text: `Nothing left in ${title}${group}. Press q for another queue${group ? ', or g for another group' : ''}.` };
  }
  const item = state.now.item;
  const lines = recordLines(state.now);
  if (state.queue.question.view === 'map' && item.map) return { kind: 'map' };
  if (item.text && typeof item.text === 'object') {
    return {
      kind: 'text',
      before: String(item.text.before || ''),
      body: String(item.text.body || ''),
      after: String(item.text.after || ''),
    };
  }
  return { kind: 'record', lines };
}

// Everything the screen shows, as words and plain values. The page copies it
// to the screen as text, and adds nothing.
export function view(state) {
  const banner = bannerOf(state);
  const counts = countsOf(state);
  const main = mainOf(state);
  const now = state.now;
  const item = now ? now.item : null;
  const mine = now && now.mine ? now.mine.answer : null;
  const picks = item && state.queue && adds(state.queue.question, 'pick') && Array.isArray(item.picks) ? item.picks : [];
  const broken = state.broken > 0 ? `${state.broken} saved ${state.broken === 1 ? 'line' : 'lines'} cannot be read. They are kept, and not used.` : '';
  const waits = waitsWords(counts);
  const redraft = redraftWords(counts);
  const aside = now ? asideOf(state.queue.question, item) : null;
  return {
    page: `${banner.kind === 'real' ? 'Real data' : banner.kind === 'made-up' ? 'Made-up city' : 'Loading'} - ${SAYS.name}`,
    banner,
    progress: counts ? progress(partsOf(state, counts), state.paused) : '',
    reviewer: state.reviewer ? `Reviewer ${state.reviewer}` : '',
    main,
    // The name of the item, which the page prints once, over the item.
    title: item ? String(item.title || now.id) : '',
    group: item && typeof item.group === 'string' ? item.group : '',
    flags: now ? flagWords(state) : '',
    lines: item && main.kind !== 'record' && Array.isArray(item.lines) ? item.lines : [],
    picks: picks.slice(0, 5).map((text, index) => ({ key: 'abcde'[index], text: String(text), chosen: index === state.pick })),
    mine: mineWords(state),
    dispute: now ? disputeWords(state) : '',
    others: now
      ? now.others.map((other) => `${other.reviewer} answered: ${labelOf(state, other.answer)}.${other.note ? ` Note: ${other.note}` : ''}`)
      : [],
    moves: now ? now.moves.map((move) => ({ cell: move.part, from: move.detail ? move.detail.from : '', to: move.detail ? move.detail.to : '' })) : [],
    // The cells another reviewer moved. They are drawn, and are not moved on this map.
    theirs: now ? now.others.flatMap((other) => (Array.isArray(other.moves) ? other.moves : []).map((move) => ({ reviewer: other.reviewer, cell: move.part, from: move.from, to: move.to }))) : [],
    hand: state.hand,
    question: now ? questionText(state.queue.question, item, now.moves) : '',
    rule: now && typeof state.queue.question.rule === 'string' ? state.queue.question.rule : '',
    answers: now ? answerRows(state, mine) : [],
    // Why an answer of the question is not among them, where one is not.
    notOffered: now && answersOf(state).some((entry) => notAnArea(state, entry.code)) ? SAYS.noKeyForArea : '',
    // That an answer will be set aside, said before it is given: in short on
    // every such item, and with what to do on the first of a sitting.
    aside: aside === null ? null : { short: aside.short, words: aside.words, open: state.asideAt[state.queue.id] === now.id },
    canMove: Boolean(now && state.queue && adds(state.queue.question, 'move')),
    canName: Boolean(now && state.queue && namesAreas(state.queue.question, item)),
    of: now && state.queue && namesAreas(state.queue.question, item) ? state.of : [],
    note: {
      open: state.noteOpen,
      text: state.noteOpen ? state.draft : state.note,
      hint: SAYS.noteHint,
      // The words under the note are shown while a note is written or kept.
      hinted: state.noteOpen || state.note !== '',
      most: MOST_NOTE,
    },
    second: state.second,
    paused: state.paused,
    busy: state.pending !== null,
    trouble: [state.trouble, state.pending && state.tries > 0 ? SAYS.kept : ''].filter(Boolean).join(' '),
    // Only a queue that holds borders says what a name decided later does to one.
    // While an item drawn for a rule is looked at, the line says that and no more.
    warn: visitWords(state) !== '' ? visitWords(state) : [broken, waits, redraft, waits !== '' && redraft === '' && adds(state.queue.question, 'move') ? SAYS.waits : ''].filter(Boolean).join(' '),
    said: state.said,
    // True where what is said is the name of the item and no more: the page
    // prints the name once, over the item, and says this aloud only.
    saidIsName: item !== null && state.said !== '' && state.said === String(item.title || now.id),
    // True where anything is known of the item beside its name.
    known: now !== null && (flagWords(state) !== '' || (main.kind !== 'record' && Array.isArray(item.lines) && item.lines.length > 0) || picks.length > 0 || now.mine !== null || now.others.length > 0 || now.moves.length > 0 || disputeWords(state) !== ''),
    // The rule is open on the first item of a queue, and shut from then on.
    ruleOpen: now !== null && state.ruleAt[state.queue.id] === now.id,
    panel: panelOf(state),
    bar: BAR,
  };
}

// Every answer as the screen shows it: those of the question, and after them
// the one that is given to a whole part, on the next key.
function answerRows(state, mine) {
  const aside = asideOf(state.queue.question, state.now.item);
  const marked = (entry) => (aside !== null && aside.mark !== '' && aside.answers.includes(entry.code) ? ` (${aside.mark})` : '');
  const rows = answersOf(state)
    .map((entry, index) => answerRow({ ...entry, label: labelNow(state, entry) }, index, mine, proposedOf(state), marked(entry)))
    .filter((row) => !notAnArea(state, row.code));
  const covers = coversOf(state);
  if (covers === null) return rows;
  return [...rows, { key: String(answersOf(state).length + 1), code: covers.code, label: covers.label, text: covers.label, proposed: false, stands: false, covers: true }];
}

// One answer as the screen shows it. `text` is its label, and says so where the
// draft proposes it.
function answerRow(entry, index, mine, proposed, marked = '') {
  const label = String(entry.label);
  const isProposed = proposed === entry.code;
  return {
    key: String(index + 1),
    code: entry.code,
    label,
    text: isProposed ? `${label} (proposed: Enter)` : `${label}${marked}`,
    proposed: isProposed,
    stands: mine === entry.code,
  };
}

function panelOf(state) {
  if (state.panel === null) return null;
  const kind = state.panel.kind;
  if (kind === 'keys') {
    return { kind, title: SAYS.keys, rows: KEYS.map((row) => ({ key: row.key, text: row.does, at: false })), foot: SAYS.keysFoot };
  }
  const rows = rowsOf(state, kind).map((row, index) => ({
    key: kind === 'queues' ? QUEUE_KEYS.charAt(index) : '',
    text: row.text,
    at: index === state.panel.at,
  }));
  const queues = kind === 'queues';
  return { kind, title: queues ? SAYS.queues : SAYS.groups, rows, foot: queues ? SAYS.queuesFoot : SAYS.panelFoot };
}

// The areas a name is given to, in words.
export function ofWords(of, nameOf = (id) => id) {
  return of.length === 0 ? '' : `A name of: ${of.map((id) => nameOf(id)).join(', ')}`;
}

// A move, in words. `nameOf` gives an area's name where the map knows it.
export function moveWords(move, nameOf = (id) => id) {
  return `Cell ${move.cell}: from ${nameOf(move.from)} to ${nameOf(move.to)}`;
}

// A move another reviewer made, in words.
export function theirWords(move, nameOf = (id) => id) {
  return `${move.reviewer} moved cell ${move.cell}: from ${nameOf(move.from)} to ${nameOf(move.to)}`;
}
