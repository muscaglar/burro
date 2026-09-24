// The small rules of the page, each on its own.

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  KEYS,
  MOST_SECONDS,
  clockGo,
  clockNew,
  clockSeconds,
  clockStop,
  countsFrom,
  detailOf,
  groupsOf,
  hasUnsaved,
  keyAction,
  left,
  lookItem,
  needsNote,
  nextFlagged,
  nextItem,
  pathOf,
  progress,
  questionText,
  retryAfter,
  settles,
  spell,
  start,
} from '../logic.mjs';

const items = [
  { id: 'a', group: 'north', state: 'done' },
  { id: 'b', group: 'north', state: 'open' },
  { id: 'c', group: 'south', state: 'skipped' },
  { id: 'd', group: 'south', state: 'open' },
  { id: 'e', group: 'north', state: 'disputed' },
];

test('the next item is the first open one after this one', () => {
  assert.equal(nextItem(items, 'a', null, 'r1'), 'b');
  assert.equal(nextItem(items, 'b', null, 'r1'), 'd');
});

test('with nothing on screen the next item is the first open one in the list', () => {
  assert.equal(nextItem(items, null, null, 'r1'), 'b');
});

test('the search for the next item goes round to the start', () => {
  assert.equal(nextItem(items, 'e', null, 'r2'), 'b');
});

test('a skipped item comes back only after every open one', () => {
  const list = [
    { id: 'a', group: 'g', state: 'skipped' },
    { id: 'b', group: 'g', state: 'open' },
    { id: 'c', group: 'g', state: 'done' },
  ];
  assert.equal(nextItem(list, 'a', null, 'r1'), 'b');
  assert.equal(nextItem(list.map((one) => (one.id === 'b' ? { ...one, state: 'done' } : one)), 'b', null, 'r1'), 'a');
});

test('an item whose answer is stale is open again', () => {
  assert.equal(nextItem([{ id: 'a', group: 'g', state: 'stale' }], null, null, 'r1'), 'a');
});

test('an item in dispute is offered to the first reviewer and to no other', () => {
  const list = [{ id: 'a', group: 'g', state: 'disputed' }];
  assert.equal(nextItem(list, null, null, 'r1'), 'a');
  assert.equal(nextItem(list, null, null, 'r2'), null);
});

test('with a group chosen the next item is of that group', () => {
  assert.equal(nextItem(items, 'a', 'south', 'r1'), 'd');
  assert.equal(nextItem(items, 'd', 'south', 'r2'), 'd');
});

test('when nothing is left there is no next item', () => {
  assert.equal(nextItem([{ id: 'a', group: 'g', state: 'done' }], 'a', null, 'r1'), null);
  assert.equal(nextItem([], null, null, 'r1'), null);
});

const flagged = [
  { id: 'a', group: 'north', state: 'done', flagged: true },
  { id: 'b', group: 'north', state: 'open', flagged: false },
  { id: 'c', group: 'north', state: 'open', flagged: false },
  { id: 'd', group: 'south', state: 'open', flagged: true },
  { id: 'e', group: 'south', state: 'skipped', flagged: true },
  { id: 'f', group: 'south', state: 'open', flagged: false },
];

test('the next flagged item is the first open one after this one that carries a flag', () => {
  assert.equal(nextFlagged(flagged, 'a', null, 'r1'), 'd');
  assert.equal(nextFlagged(flagged, 'b', null, 'r1'), 'd');
  assert.equal(nextFlagged(flagged, null, null, 'r1'), 'd');
});

test('a flagged item that was skipped comes back after every open one that is flagged', () => {
  assert.equal(nextFlagged(flagged, 'd', null, 'r1'), 'e');
  const done = flagged.map((one) => (one.id === 'd' ? { ...one, state: 'done' } : one));
  assert.equal(nextFlagged(done, 'a', null, 'r1'), 'e');
});

test('the search for the next flagged item goes round to the start and stays in the group chosen', () => {
  const open = flagged.map((one) => (one.id === 'a' ? { ...one, state: 'open' } : one));
  assert.equal(nextFlagged(open, 'e', null, 'r1'), 'a');
  assert.equal(nextFlagged(open, 'b', 'north', 'r1'), 'a');
  // Where the item on screen is the only flagged one that is left, it is that one.
  assert.equal(nextFlagged(open, 'a', 'north', 'r1'), 'a');
});

test('when no flagged item is left there is no next one, and an item that says nothing of flags is not flagged', () => {
  assert.equal(nextFlagged(items, 'a', null, 'r1'), null);
  assert.equal(nextFlagged([], null, null, 'r1'), null);
});

test('looking goes to the item before or after whatever its state', () => {
  assert.equal(lookItem(items, 'b', -1, null), 'a');
  assert.equal(lookItem(items, 'b', 1, null), 'c');
});

test('looking stops at the first and the last item', () => {
  assert.equal(lookItem(items, 'a', -1, null), null);
  assert.equal(lookItem(items, 'e', 1, null), null);
});

test('looking stays inside the group chosen', () => {
  assert.equal(lookItem(items, 'b', 1, 'north'), 'e');
});

test('the groups are listed in the order they first appear with what is left in each', () => {
  assert.deepEqual(groupsOf(items, 'r2'), [
    { group: 'north', total: 3, left: 1 },
    { group: 'south', total: 2, left: 2 },
  ]);
});

test('a time is said in seconds, then minutes, then hours', () => {
  assert.equal(spell(38), '38 s');
  assert.equal(spell(60), '1 min');
  assert.equal(spell(25 * 60), '25 min');
  assert.equal(spell(7 * 3600), '7 h');
  assert.equal(spell(7 * 3600 + 16 * 60), '7 h 16 min');
});

test('a time that is not known is said as nothing', () => {
  assert.equal(spell(null), '');
  assert.equal(spell(Number.NaN), '');
  assert.equal(spell(-1), '');
});

test('what is left counts skipped and stale items and not those in dispute', () => {
  assert.equal(left({ total: 10, done: 4, skipped: 2, stale: 1, disputed: 1 }), 5);
  assert.equal(left({ total: 1, done: 3 }), 0);
  assert.equal(left(null), 0);
});

test('the progress line says done, left, the pace and the time left at this pace', () => {
  const line = progress({ queue: 'names', title: 'Names', total: 1100, done: 412, skipped: 0, stale: 0, disputed: 0, median_seconds: 38 });
  assert.equal(line, 'Names: 412 done, 688 left, 38 s each, about 7 h 16 min left at this pace');
});

test('a pace of under a second is said as one, and not as no pace', () => {
  const counts = { queue: 'borders', title: 'Borders', total: 24, done: 20, median_seconds: 0 };
  assert.equal(progress(counts), 'Borders: 20 done, 4 left, under 1 s each');
  assert.equal(progress({ ...counts, done: 0, median_seconds: null }), 'Borders: 0 done, 24 left, no pace yet');
});

test('the progress line says so when there is no pace yet', () => {
  const line = progress({ queue: 'names', title: 'Names', total: 3, done: 0, median_seconds: null });
  assert.equal(line, 'Names: 0 done, 3 left, no pace yet');
});

test('the progress line says when the clock is stopped', () => {
  assert.match(progress({ queue: 'names', title: 'Names', total: 3, done: 0 }, true), /^PAUSED\. /);
});

test('the progress line says how many of what is left were flagged', () => {
  const line = progress({ queue: 'borders', title: 'Borders', total: 24, done: 3, flagged: 8, flagged_left: 5, median_seconds: null });
  assert.equal(line, 'Borders: 3 done, 21 left, 5 of them flagged, no pace yet');
});

test('the progress line says apart how many answers decide nothing', () => {
  const counts = { queue: 'borders', title: 'Borders', total: 120, done: 120, not_known: 14, wrong: 10, median_seconds: null };
  assert.equal(progress(counts), 'Borders: 96 done, 14 not known, 10 wrong, 0 left, no pace yet');
  assert.equal(progress({ ...counts, wrong: 0 }), 'Borders: 106 done, 14 not known, 0 left, no pace yet');
});

test('the progress line counts what is in dispute apart', () => {
  assert.match(progress({ queue: 'names', title: 'Names', total: 9, done: 4, disputed: 2, median_seconds: 10 }), /3 left, 2 in dispute/);
});

test('the counts are read whether the answer nests them or not', () => {
  assert.deepEqual(countsFrom({ counts: { total: 2 } }), { total: 2 });
  assert.deepEqual(countsFrom({ total: 2, done: 1 }), { total: 2, done: 1 });
  assert.equal(countsFrom({ line: {} }), null);
  assert.equal(countsFrom(null), null);
});

test('a wait grows to ten seconds and no further', () => {
  assert.deepEqual([1, 2, 3, 4, 5, 6, 50].map(retryAfter), [1000, 2000, 4000, 8000, 10000, 10000, 10000]);
});

test('the clock counts only while it runs', () => {
  let clock = clockGo(clockNew(), 1000);
  clock = clockStop(clock, 4000);
  assert.equal(clockSeconds(clock, 60000), 3);
  clock = clockGo(clock, 60000);
  assert.equal(clockSeconds(clock, 62000), 5);
});

test('the clock never says more than fifteen minutes', () => {
  assert.equal(clockSeconds(clockGo(clockNew(), 0), 3600 * 1000), MOST_SECONDS);
});

test('starting a clock that runs does not start it again', () => {
  const clock = clockGo(clockGo(clockNew(), 1000), 5000);
  assert.equal(clockSeconds(clock, 6000), 5);
});

test('the question takes its words from the item', () => {
  assert.equal(questionText({ text: 'Is this a {kind}?' }, { fill: { kind: 'landmark' } }), 'Is this a landmark?');
  assert.equal(questionText({ text: '{rubric}' }, { fill: { rubric: 'How leafy?' } }), 'How leafy?');
});

test('a word the item does not hold is left in the question so the fault shows', () => {
  assert.equal(questionText({ text: 'Is this a {kind}?' }, { fill: {} }), 'Is this a {kind}?');
  assert.equal(questionText({ text: 'Is this a {kind}?' }, { fill: { kind: 7 } }), 'Is this a {kind}?');
});

test('the answer wrong needs a note', () => {
  assert.equal(needsNote({ adds: 'move' }, 'wrong', []), true);
  assert.equal(needsNote({ adds: 'move' }, 'right', []), false);
});

test('any answer given after a move needs a note', () => {
  const moves = [{ part: 'syn-oa-1' }];
  assert.equal(needsNote({ adds: 'move' }, 'right', moves), true);
  assert.equal(needsNote({ adds: ['move'] }, 'unknown', moves), true);
  assert.equal(needsNote({ adds: 'pick' }, 'area', moves), false);
});

test('the detail of a line is what the item was made with and the spelling chosen', () => {
  const item = { preset: { of: ['syn-n0004'] }, picks: ['Dulcimer Green', 'Dulcimer'] };
  assert.deepEqual(detailOf({ adds: 'pick' }, item, 1), { of: ['syn-n0004'], pick: 'Dulcimer' });
  assert.deepEqual(detailOf({ adds: 'pick' }, item, 0), { of: ['syn-n0004'], pick: 'Dulcimer Green' });
});

test('a spelling is written only where the queue lets one be chosen', () => {
  assert.deepEqual(detailOf({ adds: null }, { preset: { kind: 'landmark' }, picks: ['x'] }, 0), { kind: 'landmark' });
  assert.deepEqual(detailOf({ adds: 'pick' }, { preset: {}, picks: null }, 0), {});
});

test('the detail never shares the item own preset', () => {
  const item = { preset: { of: [] }, picks: ['x'] };
  const detail = detailOf({ adds: 'pick' }, item, 0);
  detail.extra = true;
  assert.deepEqual(item.preset, { of: [] });
});

test('only the first reviewer settles and only an item in dispute', () => {
  assert.equal(settles('r1', 'disputed'), true);
  assert.equal(settles('r2', 'disputed'), false);
  assert.equal(settles('r1', 'done'), false);
});

test('an address is a path on the desk own origin and names no host', () => {
  const paths = [
    pathOf({ do: 'get', what: 'state' }),
    pathOf({ do: 'get', what: 'queue', queue: 'names' }),
    pathOf({ do: 'get', what: 'item', queue: 'names', item: 'n:syn-n0004' }),
    pathOf({ do: 'get', what: 'layer', group: 'quillhaven', layer: 'cells' }),
    pathOf({ do: 'post', what: 'decide' }),
    pathOf({ do: 'post', what: 'undo' }),
  ];
  assert.deepEqual(paths, [
    '/api/state',
    '/api/queue/names',
    '/api/item/names/n:syn-n0004',
    '/api/layer/quillhaven/cells',
    '/api/decide',
    '/api/undo',
  ]);
});

test('an id cannot climb out of its place in an address', () => {
  assert.equal(pathOf({ do: 'get', what: 'item', queue: 'names', item: '../../state?x=1#y' }), '/api/item/names/..%2F..%2Fstate%3Fx%3D1%23y');
  assert.equal(pathOf({ do: 'get', what: 'queue', queue: 'a/b' }), '/api/queue/a%2Fb');
});

const ready = { ...start(), phase: 'ready', synthetic: true };

test('every key of the manual does something', () => {
  const struck = ['1', '9', 's', 'u', 'n', 'f', 'ArrowLeft', 'ArrowRight', 'j', 'g', 'q', 'p', '?', '+', '-', '0', 'a', 'e', 'm'];
  for (const key of struck) assert.notEqual(keyAction(ready, { key }), null, key);
  assert.notEqual(keyAction(ready, { key: 'ArrowUp', shift: true }), null);
  assert.ok(KEYS.length >= struck.length - 6);
});

test('a key struck with control, command or alt is left to the browser', () => {
  assert.equal(keyAction(ready, { key: 's', ctrl: true }), null);
  assert.equal(keyAction(ready, { key: 'r', meta: true }), null);
  assert.equal(keyAction(ready, { key: '1', alt: true }), null);
});

test('a key held down answers nothing', () => {
  assert.equal(keyAction(ready, { key: '1', repeat: true }), null);
  assert.equal(keyAction(ready, { key: 's', repeat: true }), null);
});

test('a key held down still moves the map and looks along the queue', () => {
  assert.deepEqual(keyAction(ready, { key: '+', repeat: true }), { type: 'map', op: 'in' });
  assert.deepEqual(keyAction(ready, { key: 'ArrowRight', repeat: true }), { type: 'look', by: 1 });
});

test('a capital letter is the same key', () => {
  assert.deepEqual(keyAction(ready, { key: 'S', shift: true }), { type: 'skip' });
});

test('while the note is open only Enter and Esc act', () => {
  const open = { ...ready, noteOpen: true };
  assert.deepEqual(keyAction(open, { key: 'Enter' }), { type: 'keep' });
  assert.deepEqual(keyAction(open, { key: 'Escape' }), { type: 'leave' });
  for (const key of ['1', 's', 'u', 'q', 'ArrowLeft', '?', 'p']) assert.equal(keyAction(open, { key }), null, key);
});

test('a key struck in the note is never an answer even if the page thinks the note shut', () => {
  assert.equal(keyAction(ready, { key: '1', inNote: true }), null);
  assert.equal(keyAction(ready, { key: 's', inNote: true }), null);
});

test('while a list is open no answer key acts', () => {
  const open = { ...ready, panel: { kind: 'groups', at: 0 } };
  for (const key of ['1', 's', 'u', 'n', 'f']) assert.equal(keyAction(open, { key }), null, key);
  assert.deepEqual(keyAction(open, { key: 'ArrowDown' }), { type: 'move', by: 1 });
  assert.deepEqual(keyAction(open, { key: 'Escape' }), { type: 'close' });
});

test('in the list of queues a digit chooses a queue', () => {
  const open = { ...ready, panel: { kind: 'queues', at: 0 } };
  assert.deepEqual(keyAction(open, { key: '3' }), { type: 'choose', index: 2 });
  assert.deepEqual(keyAction(open, { key: '0' }), { type: 'choose', index: 9 });
});

test('Enter on a button of a list is left to the button', () => {
  const open = { ...ready, panel: { kind: 'queues', at: 1 } };
  assert.equal(keyAction(open, { key: 'Enter', onButton: true }), null);
  assert.deepEqual(keyAction(open, { key: 'Enter' }), { type: 'choose', index: 1 });
});

test('Esc lets go of a cell and is otherwise left alone', () => {
  assert.deepEqual(keyAction({ ...ready, hand: { cell: 'c', area: 'a' } }, { key: 'Escape' }), { type: 'letgo' });
  assert.equal(keyAction(ready, { key: 'Escape' }), null);
});

test('nothing is unsaved on a page that has written nothing', () => {
  assert.equal(hasUnsaved(start()), false);
});

test('an answer on its way, or waiting for its note, is unsaved', () => {
  assert.equal(hasUnsaved({ ...start(), pending: { what: 'decide', body: {} } }), true);
  assert.equal(hasUnsaved({ ...start(), held: 'wrong' }), true);
});
