// A person sits at the page and works through a queue. The desk is a stand-in.

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { BURST_MS, GRACE_MS, HOLD_MS, SAYS, hasUnsaved, step } from '../logic.mjs';
import { ITEMS, QUESTIONS, ratingsOf, sitting, standIn } from './support/standin.mjs';

const LINE_FIELDS = ['answer', 'detail', 'item', 'note', 'part', 'queue', 'rev', 'second', 'seconds', 'settles', 'stands'];

function at(queue, options = {}) {
  const desk = standIn(options);
  const sit = sitting(desk).open();
  if (queue) sit.choose(queue);
  return { desk, sit };
}

function posts(desk) {
  return desk.asked.filter((line) => line.startsWith('POST'));
}

// A click on a cell of the map, which the page has found to be in an area.
function cell(sit, id, area) {
  return sit.pass(1000).send({ type: 'cell', cell: id, area });
}

// ---------------------------------------------------------------- opening

test('it opens where the person left off', () => {
  const { sit } = at(null, { resume: { queue: 'names', item: 'n:syn-n0007' } });
  assert.equal(sit.state.queue.id, 'names');
  assert.equal(sit.item, 'n:syn-n0007');
});

test('with nowhere to go back to it lists the queues', () => {
  const { sit } = at(null);
  assert.equal(sit.view.panel.kind, 'queues');
  assert.equal(sit.view.panel.rows.length, 5);
  assert.match(sit.view.panel.rows[0].text, /^Names: 0 done, 4 left/);
});

test('the list of queues says that a number chooses one, and the list of groups does not', () => {
  const { sit } = at(null);
  assert.equal(sit.view.panel.foot, SAYS.queuesFoot);
  assert.match(sit.view.panel.foot, /^Press the key of a queue/);
  sit.key('1').key('g');
  assert.equal(sit.view.panel.kind, 'groups');
  assert.equal(sit.view.panel.foot, SAYS.panelFoot);
  assert.doesNotMatch(sit.view.panel.foot, /number/);
});

test('with the list closed and no queue chosen it says which key lists the queues', () => {
  const { sit } = at(null);
  sit.key('Escape');
  assert.equal(sit.view.panel, null);
  assert.equal(sit.view.main.text, 'No queue is chosen. Press q to list them.');
  sit.key('g');
  assert.equal(sit.view.said, 'No queue is chosen. Press q to list them.');
});

test('when the item left off at is gone it opens at the first open item and says so', () => {
  const { sit } = at(null, { resume: { queue: 'names', item: 'n:syn-gone' } });
  assert.equal(sit.item, 'n:syn-n0004');
  assert.match(sit.view.said, /no longer in the queue/);
});

test('a queue opens at its first open item', () => {
  const { sit } = at('names');
  assert.equal(sit.item, 'n:syn-n0004');
  assert.equal(sit.view.title, 'Dulcimer Green, Quillhaven');
  assert.equal(sit.view.question, 'Is this the name of an area?');
});

test('it says which data it shows before anything has loaded, while it loads and after', () => {
  const desk = standIn();
  const sit = sitting(desk);
  assert.equal(sit.view.banner.kind, 'unknown');
  assert.notEqual(sit.view.banner.text, '');
  sit.open();
  assert.equal(sit.view.banner.kind, 'made-up');
  assert.equal(sit.view.banner.text, SAYS.madeUp);
  sit.choose('sentences');
  assert.equal(sit.view.banner.text, SAYS.madeUp);
  assert.match(sit.view.page, /^Made-up city/);
});

test('it says so when the data is real', () => {
  const { sit } = at('names', { synthetic: false });
  assert.equal(sit.view.banner.kind, 'real');
  assert.equal(sit.view.banner.text, SAYS.real);
  assert.match(sit.view.page, /^Real data/);
});

test('it decides nothing when two answers differ on which data this is', () => {
  const { desk, sit } = at('names');
  desk.synthetic = false;
  sit.key(']');
  assert.equal(sit.view.banner.kind, 'unknown');
  assert.equal(sit.view.trouble, SAYS.mixed);
  sit.key('1');
  assert.deepEqual(posts(desk), []);
});

test('it stops when an answer is confirmed under the name of the other city', () => {
  const { desk, sit } = at('names');
  const ask = desk.ask;
  desk.ask = (method, path, headers, body) => {
    const out = ask(method, path, headers, body);
    return method === 'POST' ? { status: out.status, body: { ...out.body, synthetic: false } } : out;
  };
  sit.key('1');
  assert.equal(sit.view.trouble, SAYS.mixed);
  assert.equal(sit.view.banner.kind, 'unknown');
  assert.equal(sit.item, 'n:syn-n0004', 'it does not move on');
  sit.key('2').key('s').key('u');
  assert.equal(posts(desk).length, 1, 'and it writes nothing more');
});

test('it says how many saved lines cannot be read', () => {
  const { sit } = at('names', { broken: 2 });
  assert.equal(sit.view.warn, '2 saved lines cannot be read. They are kept, and not used.');
});

test('every request is to a path of the desk and never to a host', () => {
  const { desk, sit } = at('names');
  sit.key('1').key('s').key('u').key(']');
  assert.ok(desk.asked.length > 8);
  for (const line of desk.asked) assert.match(line, /^(GET|POST) \/api\//);
});

// ---------------------------------------------------------------- one key, one answer

test('one key writes the answer and shows the next open item', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  const lines = desk.answersOf('names');
  assert.equal(lines.length, 1);
  assert.equal(lines[0].item, 'n:syn-n0004');
  assert.equal(lines[0].answer, 'area');
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.match(sit.view.said, /^Saved: An area, for Dulcimer Green, Quillhaven\. Next: Dulcimer, Quillhaven\.$/);
});

test('what is sent holds the fields the desk knows and no other', () => {
  const { desk, sit } = at('names');
  const seen = [];
  const ask = desk.ask;
  desk.ask = (method, path, headers, body) => {
    if (method === 'POST') seen.push(body);
    return ask(method, path, headers, body);
  };
  sit.key('1');
  assert.deepEqual(Object.keys(seen[0]).sort(), LINE_FIELDS);
  assert.equal(seen[0].rev, desk.items.names[0].rev);
  assert.equal(seen[0].part, '');
});

test('the answer in each place is the one its key shows', () => {
  const { desk, sit } = at('sentences');
  assert.deepEqual(sit.view.answers.map((one) => `${one.key} ${one.code}`), [
    '1 fit',
    '2 residents',
    '3 safety',
    '4 praise',
    '5 person',
    '6 change_or_price',
    '7 not_a_place',
  ]);
  sit.key('6');
  assert.equal(desk.answersOf('sentences')[0].answer, 'change_or_price');
});

test('a key with no answer in its place writes nothing', () => {
  const { desk, sit } = at('names');
  sit.key('6').key('9');
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.item, 'n:syn-n0004');
});

test('the item after the one on screen is asked for before the answer is given', () => {
  const { desk, sit } = at('names');
  assert.ok(desk.asked.includes('GET /api/item/names/a:syn-n0004:dulcimer'));
  const before = desk.asked.length;
  sit.key('1');
  const since = desk.asked.slice(before);
  assert.equal(since[0], 'POST /api/decide');
  assert.ok(!since.includes('GET /api/item/names/a:syn-n0004:dulcimer'), 'the next item was already held');
  assert.ok(since.includes('GET /api/item/names/n:syn-n0007'), 'and the one after it is asked for');
});

test('the page moves on only when the desk has answered', () => {
  const { desk, sit } = at('names');
  desk.down = true;
  sit.key('1');
  assert.equal(sit.item, 'n:syn-n0004');
});

test('a second key struck at once does not answer the item that has just appeared', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  sit.pass(GRACE_MS - 1).send({ type: 'key', key: '3' });
  assert.equal(desk.answersOf('names').length, 1);
  assert.equal(sit.view.said, SAYS.tooSoon);
  sit.pass(2).send({ type: 'key', key: '3' });
  assert.equal(desk.answersOf('names').length, 2);
});

test('the counts on screen are the ones the desk gave with the answer', () => {
  const { sit } = at('names');
  assert.match(sit.view.progress, /^Names: 0 done, 4 left, 1 of them flagged, no pace yet/);
  sit.pass(30000).key('1');
  assert.match(sit.view.progress, /^Names: 1 done, 3 left, 31 s each, about 2 min left at this pace/);
});

test('when the queue is done it says so and says what to press', () => {
  const { sit } = at('kinds');
  sit.key('1');
  assert.equal(sit.item, null);
  assert.equal(sit.view.main.kind, 'wait');
  assert.equal(sit.view.main.text, 'Nothing left in Kinds of venue. Press q for another queue.');
  assert.deepEqual(sit.view.answers, []);
});

// ---------------------------------------------------------------- skip, undo, note, mark

test('a skipped item comes back after the rest', () => {
  const { desk, sit } = at('borders');
  sit.key('s');
  assert.equal(desk.answersOf('borders')[0].answer, 'skip');
  assert.equal(sit.item, 'syn-n0012');
  sit.key('1');
  assert.equal(sit.item, 'syn-n0007');
  assert.match(sit.view.said, /You skipped this before/);
});

test('undo takes back the last answer and shows its item again', () => {
  const { desk, sit } = at('names');
  sit.key('1').key('2');
  assert.equal(sit.item, 'n:syn-n0007');
  sit.key('u');
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.equal(sit.view.mine, '');
  assert.equal(sit.view.said.startsWith(SAYS.tookBack), true);
  assert.equal(desk.lines.names.at(-1).answer, 'undo');
  assert.equal(desk.lines.names.at(-1).undoes, 2);
});

test('undo asked again takes back the one before', () => {
  const { desk, sit } = at('names');
  sit.key('1').key('2').key('u').key('u');
  assert.equal(sit.item, 'n:syn-n0004');
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area', 'same_ground', 'undo', 'undo']);
  assert.match(sit.view.progress, /^Names: 0 done, 4 left/);
});

test('between an undo and its item no key answers the item still on screen', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  const asked = { ...sit.state, pending: { what: 'undo', body: { queue: 'names' } } };
  const answer = { undone: desk.lines.names[0], counts: sit.state.queues[0], synthetic: true };
  const told = step(asked, { type: 'wrote', what: 'undo', ok: true, status: 200, data: answer, at: sit.at });
  assert.equal(told.state.now.id, 'a:syn-n0004:dulcimer', 'the item of before is still on screen');
  assert.deepEqual(told.effects, [{ do: 'get', what: 'queue', queue: 'names' }]);
  const struck = step(told.state, { type: 'key', key: '1', at: sit.at + 5000 });
  assert.deepEqual(struck.effects, []);
  assert.equal(struck.state.pending, null);
});

test('undo with nothing to take back says so', () => {
  const { desk, sit } = at('names');
  sit.key('u').key('u');
  assert.equal(sit.view.said, SAYS.nothingToUndo);
  assert.equal(sit.item, 'n:syn-n0004');
  assert.deepEqual(desk.lines.names, []);
});

test('the first undo of a sitting asks again before it takes back an answer of an earlier one', () => {
  // At the start of a sitting u would reach back into the work of another day.
  const desk = standIn();
  const before = sitting(desk).open().choose('names');
  before.key('n').type('seen on the sign').key('Enter').key('1');
  const today = sitting(desk).open().choose('names');
  assert.equal(today.item, 'a:syn-n0004:dulcimer');
  today.key('u');
  assert.equal(today.view.said, SAYS.undoEarlier);
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area'], 'nothing is taken back yet');
  assert.equal(today.item, 'a:syn-n0004:dulcimer');
  today.key('u');
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area', 'undo']);
  assert.equal(today.item, 'n:syn-n0004');
  assert.match(today.view.said, /^Taken back: An area, for Dulcimer Green, Quillhaven\./);
});

test('an undo of what this sitting saved asks nothing', () => {
  const { desk, sit } = at('names');
  sit.key('1').key('3').key('u');
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area', 'inside', 'undo']);
  sit.key('u');
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area', 'inside', 'undo', 'undo']);
  sit.key('u');
  assert.equal(sit.view.said, SAYS.undoEarlier, 'and then there is nothing of this sitting left');
});

test('the page says which answer was saved, and for which item', () => {
  // After a slip of the finger "Saved." did not show the slip.
  const { sit } = at('names');
  sit.key('5');
  assert.equal(sit.view.said, 'Saved: Not a name to keep, for Dulcimer Green, Quillhaven. Next: Dulcimer, Quillhaven.');
  sit.key('s');
  assert.equal(sit.view.said, 'Skipped: Dulcimer, Quillhaven. It comes back after the rest. Next: Alderwick, Quillhaven.');
  sit.key('u');
  assert.match(sit.view.said, /^Taken back: Skipped, for Dulcimer, Quillhaven\./);
});

test('after a move the page says what was saved in the words the person read', () => {
  const { sit } = at('borders');
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  sit.key('1').type('the brook is the border').key('Enter', { inNote: true });
  assert.match(sit.view.said, /^Saved: Right now, with a note, for Alderwick, Quillhaven\./);
});

test('the page says that a note and a mark went with the answer, so that a mark struck by mistake is seen', () => {
  // At the desk f and then 1 said "Saved: Yes", with no word of the mark.
  const { sit } = at('names');
  sit.key('f').key('5');
  assert.equal(sit.view.said, 'Saved: Not a name to keep, second reviewer asked, for Dulcimer Green, Quillhaven. Next: Dulcimer, Quillhaven.');
  sit.key('n').type('on the sign').key('Enter', { inNote: true }).key('f').key('3');
  assert.match(sit.view.said, /^Saved: A smaller place inside, with a note, second reviewer asked, for Dulcimer, Quillhaven\./);
  sit.key('f').key('s');
  assert.match(sit.view.said, /^Skipped, second reviewer asked: Alderwick, Quillhaven\. It comes back after the rest\./);
  sit.key('5');
  assert.match(sit.view.said, /^Saved: Not a name to keep, for Thrushcombe, Marrowmere\./, 'and says nothing of them when there is none');
});

test('in a queue where an area is asked about many times, the page says which was saved', () => {
  // In Ratings every item of an area has the name of the area, and "Saved: 4,
  // for Cindermoor" did not say on which vibe.
  const { sit } = at('ratings', { items: { ...ITEMS, ratings: ratingsOf(['syn-n0001', 'syn-n0002'], ['homes', 'built_age', 'leafy']) } });
  sit.key('4');
  assert.equal(sit.view.said, 'Saved: 4, on homes, for Made-up area syn-n0001. Next: Made-up area syn-n0001.');
  sit.key('2').key('u');
  assert.equal(sit.view.said, 'Taken back: 2, on built_age, for Made-up area syn-n0001.');
});

test('an answer taken back gives its note and its mark back, to be used again', () => {
  const { desk, sit } = at('names');
  const note = 'seen on the sign at the corner of the high road, and in the parish book';
  sit.key('n').type(note).key('Enter', { inNote: true }).key('f').key('1');
  assert.equal(sit.view.note.text, '');
  sit.key('u');
  assert.equal(sit.item, 'n:syn-n0004');
  assert.equal(sit.view.note.text, note);
  assert.equal(sit.view.second, true);
  sit.key('5');
  const last = desk.answersOf('names').at(-1);
  assert.deepEqual([last.answer, last.note, last.second], ['drop', note, true]);
});

test('a note goes with the next answer and with no answer after it', () => {
  const { desk, sit } = at('names');
  sit.key('n').type('seen on the high road sign').key('Enter');
  assert.equal(sit.view.note.text, 'seen on the high road sign');
  sit.key('1').key('3');
  const lines = desk.answersOf('names');
  assert.equal(lines[0].note, 'seen on the high road sign');
  assert.equal(lines[1].note, '');
});

test('a note is kept as one line of plain text, whatever was pasted into it', () => {
  // The desk refuses a note with a tab, an end of line or a mark that is not seen.
  const { desk, sit } = at('names');
  sit.key('n').type('the brook\tis the edge\u202e, by the\u200d mill\nand the lane').key('Enter', { inNote: true });
  assert.equal(sit.view.note.text, 'the brook is the edge, by the mill and the lane');
  sit.key('1');
  assert.equal(desk.answersOf('names')[0].note, 'the brook is the edge, by the mill and the lane');
});

test('Esc leaves the note as it was', () => {
  const { desk, sit } = at('names');
  sit.key('n').type('first').key('Enter');
  sit.key('n').type('second thoughts').key('Escape');
  assert.equal(sit.view.note.open, false);
  sit.key('1');
  assert.equal(desk.answersOf('names')[0].note, 'first');
});

test('while the note is open a digit is a letter of the note and not an answer', () => {
  const { desk, sit } = at('names');
  sit.key('n').key('1').key('s').key('u');
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.view.note.open, true);
});

test('a note is cut at the most the desk takes', () => {
  const { desk, sit } = at('names');
  sit.key('n').type('x'.repeat(600)).key('Enter').key('1');
  assert.equal(desk.answersOf('names')[0].note.length, 500);
});

test('the mark for a second reviewer goes with the next answer and with no answer after it', () => {
  const { desk, sit } = at('names');
  sit.key('f');
  assert.equal(sit.view.second, true);
  sit.key('1').key('3');
  assert.deepEqual(desk.answersOf('names').map((line) => line.second), [true, false]);
});

test('the mark for a second reviewer goes with a skip', () => {
  const { desk, sit } = at('names');
  sit.key('f').key('s');
  assert.equal(desk.answersOf('names')[0].second, true);
});

test('the mark is taken off by the key that put it on', () => {
  const { desk, sit } = at('names');
  sit.key('f').key('f').key('1');
  assert.equal(desk.answersOf('names')[0].second, false);
});

test('a note that was kept and a mark stay through a look, until an answer is given', () => {
  const { desk, sit } = at('names');
  sit.key('n').type('seen on the sign').key('Enter', { inNote: true }).key('f');
  sit.key(']').key('[');
  assert.equal(sit.item, 'n:syn-n0004');
  assert.equal(sit.view.note.text, 'seen on the sign');
  assert.equal(sit.view.second, true);
  sit.key('1').key('3');
  assert.deepEqual(desk.answersOf('names').map((line) => [line.note, line.second]), [['seen on the sign', true], ['', false]]);
});

test('Esc drops a note that was kept and a mark, and says so', () => {
  const { desk, sit } = at('names');
  sit.key('n').type('about the first').key('Enter', { inNote: true }).key('f').key('Escape');
  assert.equal(sit.view.said, SAYS.dropped);
  assert.equal(sit.view.note.text, '');
  assert.equal(sit.view.second, false);
  sit.key('1');
  assert.deepEqual([desk.answersOf('names')[0].note, desk.answersOf('names')[0].second], ['', false]);
});

test('a note that was kept does not travel to another queue', () => {
  const { desk, sit } = at('names');
  sit.key('n').type('about a name').key('Enter', { inNote: true }).key('f');
  sit.choose('kinds').key('1');
  assert.deepEqual([desk.answersOf('kinds')[0].note, desk.answersOf('kinds')[0].second], ['', false]);
});

test('where a map is shown an arrow moves the map, and never leaves the item', () => {
  const { sit } = at('borders');
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  sit.key('ArrowRight').key('ArrowLeft').key('ArrowUp').key('ArrowDown');
  assert.equal(sit.item, 'syn-n0007');
  assert.deepEqual(sit.state.hand, { cell: 'syn-oa-0031', area: 'syn-n0007' }, 'the cell is still in the hand');
  assert.deepEqual(sit.maps, ['right', 'left', 'up', 'down']);
});

test('an arrow with Shift moves the map by a small step', () => {
  const { sit } = at('borders');
  const effects = [];
  for (const [key, shift] of [['ArrowRight', true], ['ArrowUp', false], ['ArrowDown', true]]) {
    const out = step(sit.pass(1000).state, { type: 'key', key, shift, at: sit.at });
    effects.push(...out.effects);
  }
  assert.deepEqual(effects, [{ do: 'map', op: 'right', small: true }, { do: 'map', op: 'up', small: false }, { do: 'map', op: 'down', small: true }]);
});

test('the bracket keys look at the item before and after, in every queue', () => {
  for (const queue of ['borders', 'sentences']) {
    const { desk, sit } = at(queue);
    const first = sit.item;
    sit.key(']');
    assert.notEqual(sit.item, first, queue);
    sit.key('[');
    assert.equal(sit.item, first, queue);
    assert.deepEqual(posts(desk), []);
  }
});

test('where no map is shown the arrows look at the item before and after', () => {
  const { sit } = at('sentences');
  sit.key('ArrowRight');
  assert.equal(sit.item, 'syn-page-3:18');
  sit.key('ArrowLeft');
  assert.equal(sit.item, 'syn-page-3:17');
});

// ---------------------------------------------------------------- looking, groups, queues

test('looking at the item before or after decides nothing', () => {
  const { desk, sit } = at('names');
  sit.key(']').key(']').key('[');
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.deepEqual(posts(desk), []);
});

test('looking past the end says so and stays', () => {
  const { sit } = at('names');
  sit.key('[');
  assert.equal(sit.item, 'n:syn-n0004');
  assert.equal(sit.view.said, SAYS.firstItem);
});

test('an item looked at again shows the answer that stands', () => {
  const { sit } = at('names');
  sit.key('n').type('on the sign').key('Enter').key('1').key('[');
  assert.equal(sit.item, 'n:syn-n0004');
  assert.equal(sit.view.mine, 'You answered: An area. Note: on the sign');
  assert.deepEqual(sit.view.answers.map((one) => one.stands), [true, false, false, false, false]);
});

test('an item answered again takes the new answer', () => {
  const { desk, sit } = at('names');
  sit.key('1').key('[').key('5');
  assert.deepEqual(desk.answersOf('names').map((line) => `${line.item} ${line.answer}`), [
    'n:syn-n0004 area',
    'n:syn-n0004 drop',
  ]);
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
});

test('with a group chosen only items of that group are shown', () => {
  const { sit } = at('names');
  sit.key('g');
  assert.deepEqual(sit.view.panel.rows.map((row) => row.text), [
    'Every group: 4 left',
    'quillhaven: 3 left of 3',
    'marrowmere: 1 left of 1',
  ]);
  sit.key('ArrowDown').key('ArrowDown').key('Enter');
  assert.equal(sit.item, 'n:syn-n0012');
  sit.key('1');
  assert.equal(sit.item, null);
  assert.equal(sit.view.main.text, 'Nothing left in Names in marrowmere. Press q for another queue, or g for another group.');
});

test('a queue with one group has no group to choose', () => {
  const { sit } = at('sentences');
  sit.key('g');
  assert.equal(sit.view.panel, null);
  assert.equal(sit.view.said, SAYS.noGroups);
});

test('another queue is one key and one digit away', () => {
  const { sit } = at('names');
  sit.key('q').key('3');
  assert.equal(sit.state.queue.id, 'sentences');
  assert.equal(sit.item, 'syn-page-3:17');
});

test('Esc closes a list and changes nothing', () => {
  const { sit } = at('names');
  sit.key('q').key('Escape');
  assert.equal(sit.view.panel, null);
  assert.equal(sit.item, 'n:syn-n0004');
});

test('the keys are listed on one key', () => {
  const { sit } = at('names');
  sit.key('?');
  assert.equal(sit.view.panel.kind, 'keys');
  assert.ok(sit.view.panel.rows.some((row) => row.key === 'u' && /Undo/.test(row.text)));
  sit.key('?');
  assert.equal(sit.view.panel, null);
});

// ---------------------------------------------------------------- what each queue adds

test('a name shows the spellings and the first is chosen', () => {
  const { sit } = at('names');
  assert.deepEqual(sit.view.picks, [
    { key: 'a', text: 'Dulcimer Green', chosen: true },
    { key: 'b', text: 'Dulcimer', chosen: false },
  ]);
  assert.equal(sit.view.flags, 'Here because: one publisher');
  assert.equal(sit.view.main.kind, 'map');
});

test('a letter chooses a spelling and the answer carries it', () => {
  const { desk, sit } = at('names');
  sit.key('b').key('1');
  assert.deepEqual(desk.answersOf('names')[0].detail, { of: [], pick: 'Dulcimer', proposed: 'area' });
});

test('a letter with no spelling in its place changes nothing', () => {
  const { desk, sit } = at('names');
  sit.key('e').key('1');
  assert.equal(desk.answersOf('names')[0].detail.pick, 'Dulcimer Green');
});

test('an alias carries the areas it is a name of', () => {
  const { desk, sit } = at('names');
  sit.key(']').key('2');
  assert.deepEqual(desk.answersOf('names')[0].detail, { of: ['syn-n0004'], pick: 'Dulcimer', proposed: 'inside' });
});

test('a spelling chosen before is shown as chosen when the item is looked at again', () => {
  const { sit } = at('names');
  sit.key('b').key('1').key('[');
  assert.deepEqual(sit.view.picks.map((one) => one.chosen), [false, true]);
});

test('an answer that gives a name to an area waits until the area is named', () => {
  const { desk, sit } = at('names');
  for (const key of ['2', '3', '4']) {
    sit.key(key);
    assert.equal(sit.view.said, SAYS.areaNeeded, key);
  }
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.item, 'n:syn-n0004');
});

test('a click on a cell names the area, and the answer carries it', () => {
  const { desk, sit } = at('names');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  assert.deepEqual(sit.view.of, ['syn-n0012']);
  assert.deepEqual(posts(desk), [], 'naming an area writes nothing');
  sit.key('3');
  const line = desk.answersOf('names')[0];
  assert.equal(line.answer, 'inside');
  assert.deepEqual(line.detail, { of: ['syn-n0012'], pick: 'Dulcimer Green', proposed: 'area' });
});

test('a second click on the area takes it back', () => {
  const { sit } = at('names');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  cell(sit, 'syn-oa-0091', 'syn-n0012');
  assert.deepEqual(sit.view.of, []);
  sit.key('3');
  assert.equal(sit.view.said, SAYS.areaNeeded);
});

test('a name is not given to the area it was proposed as', () => {
  const { sit } = at('names');
  cell(sit, 'syn-oa-0031', 'syn-n0004');
  assert.deepEqual(sit.view.of, []);
  assert.equal(sit.view.said, SAYS.areaSelf);
});

test('a wide name is given to five areas at most', () => {
  const { desk, sit } = at('names');
  for (const n of [1, 2, 3, 5, 6, 7]) cell(sit, `syn-oa-000${n}`, `syn-n000${n}`);
  assert.equal(sit.view.of.length, 5);
  assert.equal(sit.view.said, SAYS.areasMost);
  sit.key('4');
  assert.deepEqual(desk.answersOf('names')[0].detail.of, ['syn-n0001', 'syn-n0002', 'syn-n0003', 'syn-n0005', 'syn-n0006']);
});

test('a name proposed for an area keeps that area unless the person changes it', () => {
  const { desk, sit } = at('names');
  sit.key(']');
  assert.deepEqual(sit.view.of, ['syn-n0004']);
  cell(sit, 'syn-oa-0031', 'syn-n0004');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  sit.key('2');
  assert.deepEqual(desk.answersOf('names')[0].detail.of, ['syn-n0012']);
});

test('the answer that a name is an area needs no area named', () => {
  const { desk, sit } = at('names');
  sit.key('1').key(']').key(']').key('5');
  assert.deepEqual(desk.answersOf('names').map((line) => line.answer), ['area', 'drop']);
});

test('the areas named before are shown when the item is looked at again', () => {
  const { sit } = at('names');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  sit.key('3').key('[');
  assert.deepEqual(sit.view.of, ['syn-n0012']);
});

test('no area is named in a queue that is not of names', () => {
  const { sit } = at('ratings');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  assert.deepEqual(sit.view.of, []);
  assert.equal(sit.view.canName, false);
  assert.equal(sit.view.said, SAYS.noMove);
});

test('a sentence is shown between the one before and the one after', () => {
  const { sit } = at('sentences');
  assert.deepEqual(sit.view.main, {
    kind: 'text',
    before: 'The mill closed long ago.',
    body: 'Alderwick has a clock tower on its green.',
    after: 'A market is held beside it.',
  });
  assert.deepEqual(sit.view.lines, [{ label: 'Heading', value: 'Places and buildings', source_id: 'synthetic' }]);
  assert.deepEqual(sit.view.picks, []);
});

test('a sentence carries where it stands in its article', () => {
  const { desk, sit } = at('sentences');
  sit.key('1');
  assert.deepEqual(desk.answersOf('sentences')[0].detail, { page_id: 3, revision_id: 1, sentence: 17 });
});

test('a record of a venue is shown with its kind in the question', () => {
  const { sit } = at('kinds');
  assert.equal(sit.view.question, 'Is this a landmark?');
  assert.equal(sit.view.main.kind, 'record');
  assert.deepEqual(sit.view.main.lines.map((line) => `${line.label}: ${line.value}`), [
    'Name: The Alderwick Clock',
    'Category as written: monument',
    'Given by: synthetic',
  ]);
  assert.deepEqual(sit.view.lines, [], 'the record is shown once, not twice');
});

test('an area is rated on a scale of five with the rubric as the question', () => {
  const { desk, sit } = at('ratings');
  assert.equal(sit.view.question, 'How much of the street is under trees, or beside grass?');
  assert.deepEqual(sit.view.answers.filter((one) => !one.covers).map((one) => one.code), ['1', '2', '3', '4', '5', 'cannot_say']);
  assert.equal(sit.view.main.kind, 'map');
  sit.key('4');
  const line = desk.answersOf('ratings')[0];
  assert.equal(line.answer, '4');
  assert.deepEqual(line.detail, { area_id: 'syn-n0004', vibe: 'leafy' });
});

test('the rule of the queue is shown under its question', () => {
  const { sit } = at('borders');
  assert.match(sit.view.rule, /^Use what you know and what the page shows\./);
});

// ---------------------------------------------------------------- moving a cell

test('a cell taken up and put down is written at once as a line of its own', () => {
  const { desk, sit } = at('borders');
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  assert.deepEqual(sit.view.hand, { cell: 'syn-oa-0031', area: 'syn-n0007' });
  assert.deepEqual(posts(desk), []);
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  const line = desk.answersOf('borders')[0];
  assert.equal(line.item, 'syn-n0007');
  assert.equal(line.part, 'syn-oa-0031');
  assert.equal(line.answer, 'move');
  assert.deepEqual(line.detail, { from: 'syn-n0007', to: 'syn-n0012' });
  assert.equal(sit.view.hand, null);
  assert.equal(sit.item, 'syn-n0007', 'a move does not leave the item');
  assert.deepEqual(sit.view.moves, [{ cell: 'syn-oa-0031', from: 'syn-n0007', to: 'syn-n0012' }]);
});

test('a cell put down in its own area moves nothing', () => {
  const { desk, sit } = at('borders');
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  cell(sit, 'syn-oa-0032', 'syn-n0007');
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.view.said, SAYS.sameArea);
});

test('Esc lets go of a cell and moves nothing', () => {
  const { desk, sit } = at('borders');
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  sit.key('Escape');
  assert.equal(sit.view.hand, null);
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  assert.deepEqual(posts(desk), []);
  assert.deepEqual(sit.view.hand, { cell: 'syn-oa-0090', area: 'syn-n0012' });
});

test('a cell cannot be moved in a queue that does not add moving', () => {
  for (const queue of ['names', 'ratings']) {
    const { desk, sit } = at(queue);
    cell(sit, 'syn-oa-0031', 'syn-n0007');
    cell(sit, 'syn-oa-0090', 'syn-n0012');
    assert.deepEqual(posts(desk), [], queue);
    assert.equal(sit.view.hand, null, queue);
    assert.equal(sit.view.canMove, false, queue);
  }
});

test('the answer wrong opens the note and waits', () => {
  const { desk, sit } = at('borders');
  sit.key('2');
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.view.note.open, true);
  assert.equal(sit.view.said, SAYS.noteNeeded);
  assert.equal(hasUnsaved(sit.state), true);
  sit.type('the brook is the border here, not the lane').key('Enter');
  const line = desk.answersOf('borders')[0];
  assert.equal(line.answer, 'wrong');
  assert.equal(line.note, 'the brook is the border here, not the lane');
  assert.equal(sit.item, 'syn-n0012');
});

test('an answer that needs a note is not sent with an empty one', () => {
  const { desk, sit } = at('borders');
  sit.key('2').type('   ').key('Enter');
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.view.note.open, true);
});

test('Esc takes back an answer that waits for its note', () => {
  const { desk, sit } = at('borders');
  sit.key('2').key('Escape');
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.view.said, SAYS.answerLeft);
  assert.equal(hasUnsaved(sit.state), false);
  sit.key('1');
  assert.equal(desk.answersOf('borders')[0].answer, 'right');
});

test('an answer given after a move needs a note', () => {
  const { desk, sit } = at('borders');
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  sit.key('1');
  assert.equal(sit.view.note.open, true);
  assert.equal(desk.answersOf('borders').length, 1);
  sit.type('the lane belongs with the green').key('Enter');
  assert.deepEqual(desk.answersOf('borders').map((line) => line.answer), ['move', 'right']);
});

test('going elsewhere while an answer waits for its note takes the answer back and keeps the words', () => {
  const { desk, sit } = at('borders');
  sit.key('2').type('the brook').send({ type: 'blur' });
  assert.deepEqual(posts(desk), []);
  assert.equal(hasUnsaved(sit.state), false);
  assert.equal(sit.view.note.open, false);
  assert.equal(sit.view.note.text, 'the brook');
  assert.equal(sit.view.said, SAYS.answerLeft);
});

test('going elsewhere while writing a note keeps the note', () => {
  const { desk, sit } = at('names');
  sit.key('n').type('on the sign').send({ type: 'blur' });
  sit.key('1');
  assert.equal(desk.answersOf('names')[0].note, 'on the sign');
});

test('a note written first goes with an answer that needs one', () => {
  const { desk, sit } = at('borders');
  sit.key('n').type('the brook is the border').key('Enter').key('2');
  assert.equal(desk.answersOf('borders')[0].note, 'the brook is the border');
});

test('undo takes back a move and the cell is where it was', () => {
  const { sit } = at('borders');
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  sit.key('u');
  assert.equal(sit.item, 'syn-n0007');
  assert.deepEqual(sit.view.moves, []);
});

test('moves made before are shown when the item is opened again', () => {
  const desk = standIn();
  const first = sitting(desk).open().choose('borders');
  cell(first, 'syn-oa-0031', 'syn-n0007');
  cell(first, 'syn-oa-0090', 'syn-n0012');
  const second = sitting(desk).open().choose('borders');
  assert.deepEqual(second.view.moves, [{ cell: 'syn-oa-0031', from: 'syn-n0007', to: 'syn-n0012' }]);
});

// ---------------------------------------------------------------- the clock

test('the line says how long the item was on screen', () => {
  const { desk, sit } = at('names');
  sit.pass(30000).key('1');
  assert.equal(desk.answersOf('names')[0].seconds, 31);
});

test('a pause stops the clock', () => {
  const { desk, sit } = at('names');
  sit.pass(9000).key('p');
  assert.match(sit.view.progress, /^PAUSED\. /);
  sit.pass(3600 * 1000).key('p');
  sit.pass(9000).key('1');
  assert.equal(desk.answersOf('names')[0].seconds, 20);
});

test('no answer is taken while paused', () => {
  const { desk, sit } = at('names');
  sit.key('p').key('1').key('s');
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.view.trouble, SAYS.paused);
  sit.key('p');
  assert.equal(sit.view.trouble, '');
  sit.key('1');
  assert.equal(desk.answersOf('names').length, 1);
});

test('the clock stops while the tab is out of view', () => {
  const { desk, sit } = at('names');
  sit.pass(5000).send({ type: 'seen', seen: false });
  sit.pass(600000).send({ type: 'seen', seen: true });
  sit.pass(4000).key('1');
  assert.equal(desk.answersOf('names')[0].seconds, 10);
});

test('no line says more than fifteen minutes', () => {
  const { desk, sit } = at('names');
  sit.pass(3 * 3600 * 1000).key('1');
  assert.equal(desk.answersOf('names')[0].seconds, 900);
});

test('the clock starts again with each item', () => {
  const { desk, sit } = at('names');
  sit.pass(60000).key('1').pass(4000).key('3');
  assert.deepEqual(desk.answersOf('names').map((line) => line.seconds), [61, 5]);
});

test('a move does not start the clock again', () => {
  const { desk, sit } = at('borders');
  sit.pass(20000);
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  sit.pass(8000).key('1').type('why').key('Enter');
  assert.deepEqual(desk.answersOf('borders').map((line) => line.seconds), [22, 32]);
});

// ---------------------------------------------------------------- never losing an answer

test('when the desk does not answer it says so, keeps the answer and will try again', () => {
  const { desk, sit } = at('names');
  desk.down = true;
  sit.key('1');
  assert.match(sit.view.trouble, /^Not saved\. Start the desk again with make desk\./);
  assert.match(sit.view.trouble, /Your answer is kept here and will be sent again\. Do not close this page\./);
  assert.equal(hasUnsaved(sit.state), true);
  assert.deepEqual(sit.waits, [1000]);
  assert.equal(sit.state.pending.body.answer, 'area');
});

test('when the disk is full the page says so, and does not say to start the desk again', () => {
  const { desk, sit } = at('names');
  const ask = desk.ask;
  const full = 'Not saved. The disk is full. Make room on it. The desk need not be started again.';
  desk.ask = (method, path, headers, body) => (method === 'POST' ? { status: 500, body: { error: 'not_saved', message: full, synthetic: true } } : ask(method, path, headers, body));
  sit.key('1');
  assert.equal(sit.view.trouble, `${full} ${SAYS.kept}`);
  assert.doesNotMatch(sit.view.trouble, /make desk/);
  assert.equal(hasUnsaved(sit.state), true);
  desk.ask = ask;
  sit.retry();
  assert.equal(desk.answersOf('names').length, 1, 'once there is room the answer is written');
  assert.equal(sit.view.trouble, '');
});

test('while an answer is not saved it does not still say that the one before was', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  assert.match(sit.view.said, /^Saved: /);
  desk.down = true;
  sit.key('3');
  assert.match(sit.view.trouble, /^Not saved\./);
  assert.equal(sit.view.said, '');
  desk.down = false;
  sit.retry();
  assert.equal(sit.view.trouble, '');
  assert.match(sit.view.said, /^Saved: /);
});

test('when an answer is refused or the item has changed it does not still say Saved', () => {
  const changed = at('names');
  changed.sit.key('1');
  changed.desk.change('names', changed.sit.item, { title: 'Dulcimer, as now written' });
  changed.sit.key('3');
  assert.equal(changed.sit.view.trouble, SAYS.changed);
  assert.equal(changed.sit.view.said, 'Dulcimer, as now written');
  const refused = at('names');
  refused.sit.key('1');
  refused.desk.questions.names.answers[2].code = 'renamed';
  refused.sit.key('3');
  assert.equal(refused.sit.view.trouble, 'The desk says: bad_request.');
  assert.equal(refused.sit.view.said, '');
});

test('an answer kept is written once the desk is back, and once only', () => {
  const { desk, sit } = at('names');
  desk.down = true;
  sit.key('1').retry().retry();
  assert.equal(desk.answersOf('names').length, 0);
  assert.deepEqual(sit.waits, [4000]);
  desk.down = false;
  sit.retry();
  assert.equal(desk.answersOf('names').length, 1);
  assert.equal(desk.answersOf('names')[0].answer, 'area');
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.equal(sit.view.trouble, '');
  assert.equal(hasUnsaved(sit.state), false);
  assert.deepEqual(sit.waits, []);
});

test('an answer kept is written to a desk that was started again and holds a new token', () => {
  const { desk, sit } = at('names');
  desk.down = true;
  sit.key('5');
  desk.again('token-after-restart');
  sit.retry();
  assert.equal(desk.answersOf('names')[0].answer, 'drop');
  assert.equal(sit.state.token, 'token-after-restart');
  assert.equal(hasUnsaved(sit.state), false);
});

test('an answer the desk forbids is kept, and sent again with the token of the day', () => {
  const { desk, sit } = at('names');
  desk.token = 'token-after-restart';
  sit.key('1');
  assert.equal(hasUnsaved(sit.state), true);
  assert.match(sit.view.trouble, /^Not saved\./);
  sit.retry();
  assert.equal(desk.answersOf('names').length, 1);
});

test('a fault of the desk own keeps the answer too', () => {
  const { desk, sit } = at('names');
  desk.fail = 1;
  sit.key('1');
  assert.equal(hasUnsaved(sit.state), true);
  sit.retry();
  assert.equal(desk.answersOf('names').length, 1);
});

test('while an answer is kept no other answer is taken', () => {
  const { desk, sit } = at('names');
  desk.down = true;
  sit.key('1').key('5').key('s').key('u').key(']');
  assert.equal(sit.state.pending.body.answer, 'area');
  assert.equal(sit.item, 'n:syn-n0004');
  desk.down = false;
  sit.retry();
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area']);
});

test('a move the desk did not answer is kept and written when it is back', () => {
  const { desk, sit } = at('borders');
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  desk.down = true;
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  assert.equal(hasUnsaved(sit.state), true);
  desk.down = false;
  sit.retry();
  assert.equal(desk.answersOf('borders')[0].answer, 'move');
  assert.deepEqual(sit.view.moves, [{ cell: 'syn-oa-0031', from: 'syn-n0007', to: 'syn-n0012' }]);
});

test('an undo the desk did not answer is asked again', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  desk.down = true;
  sit.key('u');
  assert.equal(hasUnsaved(sit.state), true);
  desk.down = false;
  sit.retry();
  assert.equal(desk.lines.names.at(-1).answer, 'undo');
  assert.equal(sit.item, 'n:syn-n0004');
});

test('an answer is not written to a desk that came back with other data', () => {
  const { desk, sit } = at('names');
  desk.down = true;
  sit.key('1');
  desk.again();
  desk.synthetic = false;
  sit.retry();
  assert.deepEqual(desk.answersOf('names'), []);
  assert.equal(sit.view.trouble, SAYS.otherData);
  assert.equal(sit.view.banner.kind, 'real');
  assert.equal(hasUnsaved(sit.state), false);
  assert.equal(sit.view.panel.kind, 'queues');
});

test('an answer is not written to a desk that came back for another reviewer', () => {
  const { desk, sit } = at('names');
  desk.down = true;
  sit.key('1');
  desk.again();
  desk.reviewer = 'r2';
  sit.retry();
  assert.deepEqual(desk.answersOf('names'), []);
  assert.equal(sit.view.trouble, SAYS.otherData);
});

// ---------------------------------------------------------------- words typed with the note shut

function typedInto(queue, words, options = {}) {
  const { desk, sit } = at(queue, options);
  const before = structuredClone({ second: sit.state.second, pick: sit.state.pick, note: sit.state.note, item: sit.item, panel: sit.state.panel, paused: sit.state.paused });
  sit.pass(1000).strike(words).pass(2000);
  const after = { second: sit.state.second, pick: sit.state.pick, note: sit.state.note, item: sit.item, panel: sit.state.panel, paused: sit.state.paused };
  return { desk, sit, before, after };
}

test('words that begin with the key for a note open the note, and nothing else is done', () => {
  const { desk, sit } = at('names');
  sit.pass(1000).strike('unsure, see the sign').pass(2000);
  assert.deepEqual(desk.lines.names || [], [], 'no answer is taken back and none is given');
  assert.equal(sit.view.note.open, true, 'the rest is typed in the note');
  assert.equal(sit.item, 'n:syn-n0004');
});

test('words typed with the note shut are taken as no key at all', () => {
  for (const words of ['but see the school', 'made up note', 'qupsg', 'see 12 flats', 'SEE THE SIGN']) {
    for (const queue of ['borders', 'names', 'kinds']) {
      const { desk, sit, before, after } = typedInto(queue, words);
      assert.deepEqual(posts(desk), [], `${queue}: ${words}`);
      assert.deepEqual(after, before, `${queue}: ${words}`);
      assert.equal(sit.view.said, SAYS.pressN, `${queue}: ${words}`);
      assert.equal(sit.view.note.open, false);
    }
  }
});

test('a short word and a space are words: the space says so before the letters act', () => {
  // A sentence often begins with a word of one letter or two: so, up, is, a.
  for (const words of ['so it is', 'up the hill', 'a hall', 'is it a farm', 'pub on the corner']) {
    for (const queue of ['borders', 'names', 'kinds']) {
      const { desk, before, after, sit } = typedInto(queue, words);
      assert.deepEqual(posts(desk), [], `${queue}: ${words}`);
      assert.deepEqual(after, before, `${queue}: ${words}`);
      assert.equal(sit.view.said, SAYS.pressN, `${queue}: ${words}`);
    }
  }
});

test('a space on a button is the button own, and a space struck alone does nothing', () => {
  const { desk, sit } = at('names');
  sit.pass(1000).send({ type: 'key', key: 's' }).pass(100).send({ type: 'key', key: ' ', onButton: true }).pass(HOLD_MS);
  assert.deepEqual(desk.answersOf('names').map((line) => line.answer), ['skip'], 'the letter acted');
  sit.pass(2000).send({ type: 'key', key: ' ' }).pass(100).send({ type: 'key', key: '3' });
  assert.deepEqual(desk.answersOf('names').map((line) => line.answer), ['skip', 'inside'], 'a space alone is not words');
});

test('words typed after an answer take back nothing and skip nothing', () => {
  // The run of the review: 3 in Borders, and then the note that belonged with it.
  const { desk, sit } = at('borders');
  sit.key('3').strike('but see the school').pass(2000);
  assert.deepEqual(desk.answersOf('borders').map((line) => line.answer), ['unknown']);
  assert.deepEqual(desk.lines.borders.map((line) => line.answer), ['unknown'], 'no undo and no skip');
  assert.equal(sit.view.said, SAYS.pressN);
});

test('one letter is one key, and two are two', () => {
  const { desk, sit } = at('names');
  sit.pass(1000).strike('f').pass(2000);
  assert.equal(sit.state.second, true);
  sit.strike('bs', 200).pass(2000);
  const [line] = desk.answersOf('names');
  assert.equal(line.answer, 'skip');
  assert.equal(line.second, true);
});

test('a key that writes waits a moment, so that words are known for words before it acts', () => {
  const { desk, sit } = at('names');
  sit.pass(1000).send({ type: 'key', key: 's' });
  assert.deepEqual(posts(desk), [], 'it has not yet been sent');
  sit.pass(HOLD_MS - 1);
  assert.deepEqual(posts(desk), []);
  sit.pass(1);
  assert.deepEqual(desk.answersOf('names').map((line) => line.answer), ['skip']);
});

test('an answer struck after a key that writes does not overtake it', () => {
  const { desk, sit } = at('names');
  sit.key('1').pass(1000).send({ type: 'key', key: 'u' }).pass(50).send({ type: 'key', key: '5' });
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area', 'undo']);
  assert.equal(sit.item, 'n:syn-n0004');
  sit.key('5');
  assert.deepEqual(desk.answersOf('names').map((line) => line.answer), ['area', 'drop']);
});

test('when the words stop the keys act again', () => {
  const { desk, sit } = typedInto('names', 'made up note');
  sit.pass(BURST_MS).strike('n');
  assert.equal(sit.view.note.open, true);
  sit.type('made up note').key('Enter', { inNote: true }).key('Enter');
  assert.equal(desk.answersOf('names')[0].note, 'made up note');
});

test('a key struck just after the words is still taken for one of them', () => {
  const { desk, sit } = at('names');
  sit.pass(1000).strike('made up').strike('1', 300).strike(['Enter'], 300);
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.view.said, SAYS.pressN);
  sit.pass(BURST_MS).strike('1', 0);
  assert.equal(desk.answersOf('names').length, 1);
});

test('Esc ends the words at once', () => {
  const { desk, sit } = at('names');
  sit.pass(1000).strike('made up').strike(['Escape', '1'], 100);
  assert.equal(desk.answersOf('names').length, 1);
});

test('the key for a note struck while an answer is on its way opens the note on the next item', () => {
  // The run of the review: 1, n, the note, Enter, on a desk that takes a moment to write.
  const { desk, sit } = at('names');
  sit.slow = true;
  sit.pass(1000).strike('1n');
  assert.equal(sit.state.pending.body.answer, 'area');
  assert.equal(sit.view.note.open, false);
  sit.arrive();
  assert.equal(desk.answersOf('names').length, 1);
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.equal(sit.view.note.open, true, 'the note opens when the next item is shown');
  assert.deepEqual(sit.focus.slice(-1), ['note']);
  sit.slow = false;
  sit.type('seen on the sign').key('Enter', { inNote: true }).key('3');
  assert.equal(desk.answersOf('names')[1].note, 'seen on the sign');
});

test('words typed while an answer is on its way are taken as no key at all', () => {
  // The run of the review, on a desk that takes half a second to write.
  const { desk, sit } = at('names');
  sit.key('1');
  sit.slow = true;
  sit.pass(1000).strike('3').strike('but see the school').arrive().pass(2000);
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area', 'inside']);
});

test('a mark and a spelling struck while an answer is on its way are for the next item', () => {
  const { desk, sit } = at('names');
  sit.slow = true;
  sit.pass(1000).strike('1').strike('f', 400).pass(HOLD_MS).arrive();
  assert.equal(desk.answersOf('names')[0].second, false);
  assert.equal(sit.state.second, true);
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
});

test('a mark struck just before the answer comes back is for the next item too', () => {
  const { desk, sit } = at('names');
  sit.slow = true;
  sit.pass(1000).strike('1').strike('f', 400).arrive().pass(HOLD_MS);
  assert.equal(desk.answersOf('names')[0].second, false);
  assert.equal(sit.state.second, true);
});

test('undo is not taken in the first quarter second of an item', () => {
  const { desk, sit } = at('names');
  sit.key('1').pass(GRACE_MS - 1).send({ type: 'key', key: 'u' }).pass(HOLD_MS);
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area']);
  assert.equal(sit.view.said, SAYS.tooSoon);
  sit.key('u');
  assert.deepEqual(desk.lines.names.map((line) => line.answer), ['area', 'undo']);
});

// ---------------------------------------------------------------- an area that is not known

const VIBES = ['homes', 'built_age', 'pace', 'leafy', 'village_feel', 'quiet_residential', 'foodie', 'works_warehouses'];

function rating(areas = ['syn-n0001', 'syn-n0002', 'syn-n0003']) {
  return at('ratings', { items: { ...ITEMS, ratings: ratingsOf(areas, VIBES) } });
}

test('one key says of a whole area that it is not known, and the next area is shown', () => {
  // A rater who knows 15 areas in boroughs that hold 70 pressed a key 440 times to say so.
  const { desk, sit } = rating();
  assert.deepEqual(sit.view.answers.map((one) => `${one.key} ${one.text}`).slice(-2), ['6 Cannot say', '7 I do not know this area']);
  sit.key('7');
  const lines = desk.answersOf('ratings');
  assert.deepEqual(lines.map((line) => line.item), VIBES.map((vibe) => `syn-n0001:${vibe}`));
  assert.ok(lines.every((line) => line.answer === 'cannot_say' && line.note === '' && line.second === false));
  assert.deepEqual(lines.map((line) => line.detail), VIBES.map((vibe) => ({ area_id: 'syn-n0001', vibe })));
  assert.equal(sit.item, 'syn-n0002:homes');
  assert.equal(sit.view.said, 'Saved: I do not know this area, 8 answers, for Made-up area syn-n0001. Next: Made-up area syn-n0002.');
});

test('the vibes of an area that were rated before stay as they were rated', () => {
  const { desk, sit } = rating();
  sit.key('4').key('2').key('7');
  assert.deepEqual(desk.answersOf('ratings').map((line) => line.answer), ['4', '2', ...Array(6).fill('cannot_say')]);
  assert.equal(sit.item, 'syn-n0002:homes');
});

test('an area that is not known is one key in the middle of rating another too', () => {
  const { desk, sit } = rating();
  sit.key('7').key('3').key('7');
  assert.equal(desk.answersOf('ratings').filter((line) => line.item.startsWith('syn-n0002:')).length, 8);
  assert.equal(sit.item, 'syn-n0003:homes');
});

test('no key answers while an area is being said not to be known', () => {
  const { desk, sit } = rating();
  sit.slow = true;
  sit.pass(1000).strike('7').strike('55', 300);
  sit.arrive().arrive().arrive();
  sit.slow = false;
  sit.arrive();
  assert.deepEqual([...new Set(desk.answersOf('ratings').map((line) => line.answer))], ['cannot_say']);
});

test('a vibe that another page rated meanwhile is not written over when the area is said not to be known', () => {
  const desk = standIn({ items: { ...ITEMS, ratings: ratingsOf(['syn-n0001', 'syn-n0002'], VIBES) } });
  const first = sitting(desk).open().choose('ratings');
  const second = sitting(desk).open().choose('ratings');
  first.key(']').key(']').key('5');
  assert.equal(desk.answersOf('ratings')[0].item, 'syn-n0001:pace');
  second.key('7');
  const held = Object.fromEntries(desk.answersOf('ratings').map((line) => [line.item, line.answer]));
  assert.equal(held['syn-n0001:pace'], '5', 'the rating stands');
  assert.equal(desk.lines.ratings.filter((line) => line.item === 'syn-n0001:pace').length, 1);
  assert.equal(Object.values(held).filter((answer) => answer === 'cannot_say').length, 7);
});

// What stands in a queue of the stand-in: by item, the answer no later line took back.
function standing(desk, queue) {
  const lines = desk.lines[queue] || [];
  const undone = new Set(lines.filter((line) => line.answer === 'undo').map((line) => line.undoes));
  return Object.fromEntries(lines.filter((line) => line.answer !== 'undo' && !undone.has(line.n)).map((line) => [line.item, line.answer]));
}

test('one undo takes back every answer that one key gave to an area, and says how many', () => {
  // At the desk, 7 beside 6 wrote seven lines and u took back one: the page
  // looked mended, and six vibes of an area the person knew stood as not known.
  const { desk, sit } = rating();
  sit.key('7').key('u');
  assert.deepEqual(standing(desk, 'ratings'), {}, 'nothing of the area stands');
  assert.equal(desk.lines.ratings.filter((line) => line.answer === 'undo').length, 8, 'each line is taken back by a line of its own');
  assert.equal(sit.item, 'syn-n0001:homes', 'the item the key was struck on is shown again');
  assert.equal(sit.view.said, 'Taken back: I do not know this area, 8 answers, for Made-up area syn-n0001.');
  assert.match(sit.view.progress, /^Ratings: 0 of 3 areas done, 3 left/);
  assert.equal(sit.state.pending, null);
});

test('the undo of a whole area leaves the ratings given before it', () => {
  const { desk, sit } = rating();
  sit.key('4').key('2').key('7').key('u');
  assert.deepEqual(standing(desk, 'ratings'), { 'syn-n0001:homes': '4', 'syn-n0001:built_age': '2' });
  assert.equal(sit.item, 'syn-n0001:pace');
  assert.equal(sit.view.said, 'Taken back: I do not know this area, 6 answers, for Made-up area syn-n0001.');
  sit.key('u');
  assert.deepEqual(standing(desk, 'ratings'), { 'syn-n0001:homes': '4' }, 'the next undo takes back one rating');
  assert.equal(sit.view.said, 'Taken back: 2, on built_age, for Made-up area syn-n0001.');
});

test('an answer given after a whole area is taken back first, and then the whole area', () => {
  const { desk, sit } = rating();
  sit.key('7').key('3').key('u');
  assert.equal(Object.keys(standing(desk, 'ratings')).length, 8, 'the area still stands');
  assert.equal(sit.item, 'syn-n0002:homes');
  sit.key('u');
  assert.deepEqual(standing(desk, 'ratings'), {});
  assert.equal(sit.item, 'syn-n0001:homes');
});

test('the undo of a whole area stops at a line this page did not write', () => {
  const desk = standIn({ items: { ...ITEMS, ratings: ratingsOf(['syn-n0001', 'syn-n0002'], VIBES) } });
  const first = sitting(desk).open().choose('ratings');
  first.key('7');
  const second = sitting(desk).open().choose('ratings');
  second.key('5');
  assert.equal(standing(desk, 'ratings')['syn-n0002:homes'], '5');
  first.key('u');
  const held = standing(desk, 'ratings');
  assert.equal(Object.values(held).filter((answer) => answer === 'cannot_say').length, 8, 'the area is not half taken back');
  assert.equal(held['syn-n0002:homes'], undefined, 'the last line of the queue was taken back, as one undo does');
  assert.equal(first.state.pending, null);
});

test('no key answers while a whole area is being taken back', () => {
  const { desk, sit } = rating();
  sit.key('7');
  sit.slow = true;
  sit.pass(1000).strike('u').pass(HOLD_MS).strike('55', 300);
  for (let turns = 0; turns < 10; turns += 1) sit.arrive();
  sit.slow = false;
  assert.deepEqual(standing(desk, 'ratings'), {});
  assert.deepEqual([...new Set(desk.answersOf('ratings').map((line) => line.answer))], ['cannot_say']);
});

test('while a whole area is answered the page says one thing, and then what was saved', () => {
  // A screen reader is told each time the line changes. Seven changes in a
  // tenth of a second are seven things said.
  const { sit } = rating();
  sit.key('4');
  const before = sit.view.said;
  assert.match(before, /^Saved: 4, on homes, /);
  sit.heard.length = 0;
  sit.key('7');
  assert.deepEqual(sit.heard, [before, 'Saved: I do not know this area, 7 answers, for Made-up area syn-n0001. Next: Made-up area syn-n0002.']);
  // Taken back, the page says so as one undo does: once, and then with the name of the item.
  sit.heard.length = 0;
  sit.key('u');
  assert.deepEqual(sit.heard.slice(1), ['Taken back: I do not know this area, 7 answers', 'Taken back: I do not know this area, 7 answers, for Made-up area syn-n0001.']);
});

test('the top line of a queue of ratings counts areas, and not the vibes of each', () => {
  const { sit } = rating();
  assert.match(sit.view.progress, /^Ratings: 0 of 3 areas done, 3 left/);
  sit.key('7');
  assert.match(sit.view.progress, /^Ratings: 1 of 3 areas done, 2 left/);
  sit.key('3');
  assert.match(sit.view.progress, /^Ratings: 1 of 3 areas done, 2 left/, 'an area is done when every vibe of it is');
  for (let at = 0; at < 7; at += 1) sit.key('3');
  assert.match(sit.view.progress, /^Ratings: 2 of 3 areas done, 1 left/);
  assert.doesNotMatch(sit.view.progress, /24|16|8 left/);
});

test('a queue with no answer for a whole part has no such key', () => {
  const { desk, sit } = at('kinds');
  assert.equal(sit.view.answers.length, 3);
  sit.key('4');
  assert.deepEqual(posts(desk), []);
});

// ---------------------------------------------------------------- the order of the work

test('every queue has a key in the list, the eleventh too', () => {
  const questions = structuredClone(QUESTIONS);
  const items = {};
  for (let at = 1; at <= 12; at += 1) {
    questions[`queue${at}`] = { ...questions.kinds, id: `queue${at}`, title: `Queue ${at}` };
    items[`queue${at}`] = [{ id: `syn-item-${at}`, rev: '0'.repeat(12), group: 'all', title: `Item ${at}`, lines: [], text: null, map: null, picks: null, flags: [], fill: { kind: 'x' }, preset: {} }];
  }
  const { sit } = at(null, { questions, items });
  assert.deepEqual(sit.view.panel.rows.map((row) => row.key), ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=']);
  sit.key('-');
  assert.equal(sit.state.queue.id, 'queue11');
  sit.key('q').key('0');
  assert.equal(sit.state.queue.id, 'queue10');
  sit.key('q').key('=');
  assert.equal(sit.state.queue.id, 'queue12');
  sit.key('q').key('a');
  assert.equal(sit.view.panel.kind, 'queues', 'a letter chooses nothing: it may be a word');
});

test('the list of queues says what a queue waits on', () => {
  const { sit } = at(null);
  const rows = sit.view.panel.rows.map((row) => row.text);
  assert.match(rows[0], /^Names: 0 done, 4 left, 1 of them flagged, no pace yet$/);
  assert.match(rows[1], /^Borders: 0 done, 2 left, .* Waits on 4 in Names\.$/);
  assert.doesNotMatch(rows[2], /Waits on/);
});

test('a queue that holds no border says what it waits on, and nothing of borders', () => {
  // At the desk Articles, Ratings and Claims each said that a name decided
  // later opens its border again. None of them has a border.
  const questions = structuredClone(QUESTIONS);
  questions.ratings.after = ['names'];
  questions.kinds.after = ['names'];
  for (const queue of ['ratings', 'kinds']) {
    const { sit } = at(queue, { questions });
    assert.equal(sit.view.warn, 'Waits on 4 in Names.', queue);
  }
});

test('a queue that waits on another says so while it is worked, until the other is done', () => {
  const { sit } = at('borders');
  assert.equal(sit.view.warn, 'Waits on 4 in Names. A name decided later opens its border again.');
  sit.choose('names');
  assert.equal(sit.view.warn, '');
  sit.key('Enter').key('Enter').key('Enter').key('Enter');
  sit.choose('borders');
  assert.equal(sit.view.warn, '');
  assert.doesNotMatch(sit.key('q').view.panel.rows[1].text, /Waits on/);
});

// ---------------------------------------------------------------- after a move

test('once a cell is moved the question and the answers say that they are about the border as it now stands', () => {
  const { sit } = at('borders');
  assert.equal(sit.view.question, 'Is this boundary right?');
  assert.deepEqual(sit.view.answers.map((one) => one.text), ['Right', 'Wrong', 'I do not know this ground']);
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  assert.equal(sit.view.question, 'With your moves, is it right now?');
  assert.deepEqual(sit.view.answers.map((one) => `${one.key} ${one.text}`), ['1 Right now', '2 Still wrong', '3 I do not know this ground']);
  assert.deepEqual(sit.view.answers.map((one) => one.code), ['right', 'wrong', 'unknown']);
  assert.match(sit.view.said, /^Moved\. .*say whether it is right now\./);
});

test('when the move is taken back the question is the first one again', () => {
  const { sit } = at('borders');
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  sit.key('u');
  assert.equal(sit.view.question, 'Is this boundary right?');
  assert.deepEqual(sit.view.answers.map((one) => one.text), ['Right', 'Wrong', 'I do not know this ground']);
});

test('a queue with no other words for it asks the same question after a move', () => {
  const questions = structuredClone(QUESTIONS);
  delete questions.borders.moved;
  const { sit } = at('borders', { questions });
  cell(sit, 'syn-oa-0031', 'syn-n0007');
  cell(sit, 'syn-oa-0090', 'syn-n0012');
  assert.equal(sit.view.question, 'Is this boundary right?');
});

// ---------------------------------------------------------------- what the draft proposes

test('the answer the draft proposes is marked, whichever key it is on', () => {
  const { sit } = at('names');
  assert.deepEqual(sit.view.answers.filter((one) => one.proposed).map((one) => one.code), ['area']);
  assert.equal(sit.view.answers[0].text, 'An area (proposed: Enter)');
  assert.equal(sit.view.answers[1].text, 'Another name, same ground');
  sit.key('1');
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.deepEqual(sit.view.answers.filter((one) => one.proposed).map((one) => one.key), ['3']);
});

test('Enter gives the answer the draft proposes, in every item', () => {
  const { desk, sit } = at('names');
  sit.key('Enter').key('Enter').key('Enter');
  assert.deepEqual(
    desk.answersOf('names').map((line) => [line.item, line.answer]),
    [['n:syn-n0004', 'area'], ['a:syn-n0004:dulcimer', 'inside'], ['n:syn-n0007', 'area']],
  );
});

test('Enter answers nothing where the draft proposes nothing, and the page says so', () => {
  const { desk, sit } = at('kinds');
  sit.key('Enter');
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.view.said, SAYS.nothingProposed);
  assert.deepEqual(sit.view.answers.filter((one) => one.proposed), []);
});

test('Enter struck twice to keep a note does not answer the item', () => {
  const { desk, sit } = at('names');
  sit.key('n').type('seen on the sign').key('Enter', { inNote: true }).key('Enter', { soon: true });
  assert.deepEqual(posts(desk), []);
  assert.equal(sit.view.said, SAYS.tooSoon);
  sit.key('Enter');
  assert.equal(desk.answersOf('names')[0].note, 'seen on the sign');
});

test('Enter held down answers one item', () => {
  const { desk, sit } = at('names');
  sit.key('Enter').key('Enter', { repeat: true }).key('Enter', { repeat: true });
  assert.equal(desk.answersOf('names').length, 1);
});

test('the answer that makes an area is not offered on a name proposed as another name, and the rest keep their keys', () => {
  const { desk, sit } = at('names');
  assert.deepEqual(sit.view.answers.map((one) => one.key), ['1', '2', '3', '4', '5']);
  assert.equal(sit.view.notOffered, '');
  sit.key('1');
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.deepEqual(sit.view.answers.map((one) => [one.key, one.code]), [['2', 'same_ground'], ['3', 'inside'], ['4', 'wide'], ['5', 'drop']]);
  assert.equal(sit.view.notOffered, SAYS.noKeyForArea);
  // A key keeps its answer: 5 is still the answer that keeps no name.
  sit.key('5');
  assert.deepEqual(desk.answersOf('names').map((line) => [line.item, line.answer]), [['n:syn-n0004', 'area'], ['a:syn-n0004:dulcimer', 'drop']]);
  assert.equal(sit.item, 'n:syn-n0007');
  assert.deepEqual(sit.view.answers.map((one) => one.key), ['1', '2', '3', '4', '5']);
});

test('another name is not made an area: the page says why and sends nothing', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  sit.key('1');
  assert.equal(desk.answersOf('names').length, 1);
  assert.equal(sit.view.said, SAYS.notAnArea);
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.doesNotMatch(sit.view.said, /Saved/);
});

// ---------------------------------------------------------------- two windows

test('an answer from a second window replaces nothing, and the page says the item was answered', () => {
  const desk = standIn();
  const first = sitting(desk).open();
  first.choose('names');
  const second = sitting(desk).open();
  second.choose('names');
  assert.equal(second.item, 'n:syn-n0004');
  first.key('1');
  // The second window still shows the item as open.
  assert.equal(second.view.mine, '');
  second.key('5');
  assert.deepEqual(desk.answersOf('names').map((line) => line.answer), ['area']);
  assert.equal(second.item, 'n:syn-n0004', 'the item is shown again');
  assert.equal(second.view.trouble, SAYS.already);
  assert.equal(second.view.mine, 'You answered: An area.');
  assert.doesNotMatch(second.view.said, /Saved/);
});

test('shown the answer that stands, the same key changes it', () => {
  const desk = standIn();
  const first = sitting(desk).open();
  first.choose('names');
  const second = sitting(desk).open();
  second.choose('names');
  first.key('1');
  second.key('5').key('5');
  assert.deepEqual(desk.answersOf('names').map((line) => line.answer), ['area', 'drop']);
  assert.equal(second.view.trouble, '');
  assert.notEqual(second.item, 'n:syn-n0004');
});

test('an answer names the line the page showed as standing, or none', () => {
  const { desk, sit } = at('names');
  const seen = [];
  const ask = desk.ask;
  desk.ask = (method, path, headers, body) => {
    if (method === 'POST') seen.push(structuredClone(body));
    return ask(method, path, headers, body);
  };
  sit.key('1').key('[').key('5');
  assert.deepEqual(seen.map((body) => [body.answer, body.stands]), [['area', null], ['drop', 1]]);
});

test('a cell moved in another window is not moved again from an old one', () => {
  const desk = standIn();
  const first = sitting(desk).open();
  first.choose('borders');
  const second = sitting(desk).open();
  second.choose('borders');
  cell(first, 'syn-oa0101', 'syn-n0007');
  cell(first, 'syn-oa0202', 'syn-n0012');
  cell(second, 'syn-oa0101', 'syn-n0007');
  cell(second, 'syn-oa0303', 'syn-n0004');
  const moves = desk.answersOf('borders').filter((line) => line.answer === 'move');
  assert.deepEqual(moves.map((line) => line.detail.to), ['syn-n0012']);
  assert.equal(second.view.trouble, SAYS.already);
  assert.equal(second.view.moves.length, 1, 'the move that stands is shown');
});

test('an item that changed after it was shown is shown again and nothing is written', () => {
  const { desk, sit } = at('names');
  desk.change('names', 'n:syn-n0004', { title: 'Dulcimer Green, as now written' });
  sit.key('1');
  assert.deepEqual(desk.answersOf('names'), []);
  assert.equal(sit.item, 'n:syn-n0004');
  assert.equal(sit.view.title, 'Dulcimer Green, as now written');
  assert.equal(sit.view.trouble, SAYS.changed);
  assert.equal(hasUnsaved(sit.state), false);
  sit.key('1');
  assert.equal(desk.answersOf('names').length, 1);
  assert.equal(sit.view.trouble, '');
});

test('an answer the desk refuses is said in the desk own words and is not sent again', () => {
  const { desk, sit } = at('names');
  desk.questions.names.answers[0].code = 'renamed';
  sit.key('1');
  assert.equal(sit.view.trouble, 'The desk says: bad_request.');
  assert.equal(hasUnsaved(sit.state), false);
  assert.deepEqual(sit.waits, []);
  assert.equal(sit.item, 'n:syn-n0004');
});

test('when the desk does not answer at the start it says so and asks again', () => {
  const desk = standIn();
  desk.down = true;
  const sit = sitting(desk).open();
  assert.equal(sit.view.trouble, SAYS.noAnswer);
  assert.equal(sit.view.banner.kind, 'unknown');
  desk.down = false;
  sit.retry();
  assert.equal(sit.view.trouble, '');
  assert.equal(sit.view.banner.kind, 'made-up');
});

test('when an item does not come it says so and asks again', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  desk.down = true;
  sit.key('[');
  assert.equal(sit.view.trouble, SAYS.noAnswer);
  const before = posts(desk).length;
  sit.key('5');
  assert.equal(posts(desk).length, before, 'no answer is taken while the item asked for is not on screen');
  desk.down = false;
  sit.retry();
  assert.equal(sit.item, 'n:syn-n0004');
  assert.equal(sit.view.trouble, '');
});

test('an item the desk no longer holds sends the page back to the list', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  desk.items.names.splice(0, 1);
  sit.key('[');
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.equal(sit.state.queue.items.length, 3);
  assert.equal(sit.view.trouble, SAYS.gone);
});

test('the page stops asking when the desk goes on listing an item it does not hold', () => {
  const desk = standIn();
  const ask = desk.ask;
  desk.ask = (method, path, headers, body) => {
    if (path.startsWith('/api/item/names/')) {
      desk.asked.push(`${method} ${path}`);
      return { status: 404, body: { error: 'not_found', message: 'The desk holds nothing by that name.', synthetic: true } };
    }
    return ask(method, path, headers, body);
  };
  const sit = sitting(desk).open().choose('names');
  assert.equal(sit.item, null);
  assert.equal(sit.view.trouble, SAYS.lost);
  assert.ok(desk.asked.length < 20, `asked ${desk.asked.length} times`);
});

test('an answer on an item the desk no longer holds is not sent again and the list is read again', () => {
  const { desk, sit } = at('names');
  desk.items.names.splice(0, 1);
  sit.key('1');
  assert.deepEqual(desk.answersOf('names'), []);
  assert.equal(hasUnsaved(sit.state), false);
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.equal(sit.view.trouble, SAYS.gone);
  sit.key('2');
  assert.equal(desk.answersOf('names')[0].item, 'a:syn-n0004:dulcimer');
  assert.equal(sit.view.trouble, '');
});

// ---------------------------------------------------------------- two reviewers

const differs = { names: { 'n:syn-n0004': [{ reviewer: 'r2', answer: 'drop', note: 'a shop, not a place', at: '2026-10-07T09:00:00Z' }] } };

test('another reviewer answer is not shown before your own stands', () => {
  const { sit } = at('names', { others: differs });
  assert.deepEqual(sit.view.others, []);
});

test('another reviewer answer is shown once your own stands', () => {
  const { sit } = at('names', { others: differs });
  sit.key('1').key('[');
  assert.deepEqual(sit.view.others, ['r2 answered: Not a name to keep. Note: a shop, not a place']);
});

test('the cells another reviewer moved are shown with their answer, once your own stands', () => {
  const moved = [{ part: 'syn-oa0101', from: 'syn-n0007', to: 'syn-n0012' }];
  const others = { borders: { 'syn-n0007': [{ reviewer: 'r2', answer: 'right', note: 'Walked it.', at: '2026-10-07T09:00:00Z', moves: moved }] } };
  const { sit } = at('borders', { others });
  assert.deepEqual(sit.view.theirs, []);
  sit.key('3').key('[');
  assert.deepEqual(sit.view.others, ['r2 answered: Right. Note: Walked it.']);
  assert.deepEqual(sit.view.theirs, [{ reviewer: 'r2', cell: 'syn-oa0101', from: 'syn-n0007', to: 'syn-n0012' }]);
  assert.deepEqual(sit.view.moves, [], 'they are not my moves, and need no note of mine');
});

test('the first reviewer answer on an item in dispute settles it', () => {
  const { desk, sit } = at('names', { others: differs });
  sit.key('1');
  assert.equal(desk.answersOf('names')[0].settles, false);
  const again = sitting(desk).open().choose('names');
  again.send({ type: 'choose', index: 0 });
  while (again.item !== 'n:syn-n0004') again.key('[');
  assert.equal(again.view.dispute, SAYS.settles);
  again.key('1');
  assert.equal(desk.answersOf('names').at(-1).settles, true);
});

test('a second reviewer answer never settles', () => {
  const others = { names: { 'n:syn-n0004': [{ reviewer: 'r1', answer: 'drop', note: '', at: '2026-10-07T09:00:00Z' }] } };
  const { desk, sit } = at('names', { reviewer: 'r2', others });
  sit.key('1');
  const again = sitting(desk).open().choose('names');
  while (again.item !== 'n:syn-n0004') again.key('[');
  assert.equal(again.view.dispute, SAYS.inDispute);
  again.key('5');
  assert.deepEqual(desk.answersOf('names').map((line) => line.settles), [false, false]);
});

test('an answer that settles nothing is refused once, and the next try is taken', () => {
  const { desk, sit } = at('names', { others: differs });
  sit.key('1');
  const again = sitting(desk).open().choose('names');
  while (again.item !== 'n:syn-n0004') again.key('[');
  desk.others = {};
  again.key('n').type('it is on the sign').key('Enter').key('f').key('1');
  assert.equal(again.view.trouble, 'There is no dispute on this item to settle.');
  assert.equal(again.item, 'n:syn-n0004');
  assert.equal(again.view.note.text, 'it is on the sign', 'the note is still there');
  assert.equal(again.view.second, true, 'and so is the mark');
  assert.equal(again.view.dispute, '');
  again.key('1');
  const line = desk.answersOf('names').at(-1);
  assert.equal(line.settles, false);
  assert.equal(line.note, 'it is on the sign');
  assert.equal(again.view.trouble, '');
});

test('what the desk says of an item when it is read is what the list holds', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  desk.others = differs;
  sit.key('[');
  assert.equal(sit.state.queue.items[0].state, 'disputed');
  assert.equal(sit.view.dispute, SAYS.settles);
});

test('looking elsewhere takes the last trouble off the screen', () => {
  const { desk, sit } = at('names');
  desk.questions.names.answers[0].code = 'renamed';
  sit.key('1');
  assert.notEqual(sit.view.trouble, '');
  sit.key(']');
  assert.equal(sit.view.trouble, '');
});

test('an answer given before the item changed is shown as such and the item is open', () => {
  const { desk, sit } = at('names');
  sit.key('1');
  desk.change('names', 'n:syn-n0004', {});
  const again = sitting(desk).open().choose('names');
  assert.equal(again.item, 'n:syn-n0004');
  assert.equal(again.view.mine, 'Before this item changed you answered: An area. It is open again.');
});

// ---------------------------------------------------------------- the next flagged item

// Six borders in two boroughs. In each the flagged ones come first, as the desk fills them.
function bordersOf() {
  const entry = (id, group, flags) => ({ ...ITEMS.borders[0], id, group, title: `Made-up area ${id}`, flags, rev: `${id.slice(-4)}00000000` });
  return [
    entry('syn-n0001', 'quillhaven', ['margin_under_10']),
    entry('syn-n0002', 'quillhaven', []),
    entry('syn-n0003', 'quillhaven', []),
    entry('syn-n0004', 'marrowmere', ['margin_under_10']),
    entry('syn-n0005', 'marrowmere', ['margin_under_10']),
    entry('syn-n0006', 'marrowmere', []),
  ];
}

test('one key goes to the next flagged border, past those that are not flagged, and decides nothing', () => {
  const { desk, sit } = at('borders', { items: { ...ITEMS, borders: bordersOf() } });
  assert.equal(sit.item, 'syn-n0001');
  sit.key('1');
  assert.equal(sit.item, 'syn-n0002', 'the next open item of the borough is not flagged');
  sit.key('j');
  assert.equal(sit.item, 'syn-n0004');
  assert.equal(sit.view.said, 'Made-up area syn-n0004');
  sit.key('j');
  assert.equal(sit.item, 'syn-n0005');
  assert.equal(desk.answersOf('borders').length, 1, 'only the answer was written');
});

test('the key for the next flagged item says so when none is left, and stays where it is', () => {
  const borders = bordersOf().map((entry) => ({ ...entry, flags: entry.id === 'syn-n0001' ? entry.flags : [] }));
  const { sit } = at('borders', { items: { ...ITEMS, borders } });
  sit.key('1');
  assert.equal(sit.item, 'syn-n0002');
  sit.key('j');
  assert.equal(sit.item, 'syn-n0002');
  assert.equal(sit.view.said, SAYS.noFlagged);
});

test('on the only flagged item that is left the key says that it is the last', () => {
  const borders = bordersOf().map((entry) => ({ ...entry, flags: entry.id === 'syn-n0004' ? entry.flags : [] }));
  const { sit } = at('borders', { items: { ...ITEMS, borders } });
  sit.key('j');
  assert.equal(sit.item, 'syn-n0004');
  sit.key('j');
  assert.equal(sit.item, 'syn-n0004');
  assert.equal(sit.view.said, SAYS.lastFlagged);
});

test('a note that was kept stays while the key goes to the next flagged item', () => {
  const { sit } = at('borders', { items: { ...ITEMS, borders: bordersOf() } });
  sit.key('n').type('Look at the towpath').key('Enter', { inNote: true });
  sit.key('j');
  assert.equal(sit.item, 'syn-n0004');
  assert.equal(sit.view.note.text, 'Look at the towpath');
});

test('the top line says how many of what is left are flagged', () => {
  const { sit } = at('borders', { items: { ...ITEMS, borders: bordersOf() } });
  assert.match(sit.view.progress, /6 left, 3 of them flagged/);
  sit.key('1');
  assert.match(sit.view.progress, /5 left, 2 of them flagged/);
});

// ---------------------------------------------------------------- an answer that will be set aside

const SET_ASIDE = {
  answers: ['same_ground', 'inside', 'wide', 'drop'],
  mark: 'waits',
  cells: {
    short: 'This area has ground. To turn its name down waits for a new draft.',
    words: 'Read every name first. Then make the draft again from the answers. Then look at borders.',
    saved: 'It is set aside until the draft is made again from the answers.',
  },
  names: {
    short: 'Other names are given to this area. To turn its name down waits on them.',
    words: 'Decide its other names first.',
    saved: 'It is set aside while another name is given to this area.',
  },
};

// The names of the made-up desk, with ground under each that is an area.
function withGround(holds = 'cells') {
  const names = ITEMS.names.map((entry) => (entry.id.startsWith('n:') ? { ...entry, preset: { ...entry.preset, holds } } : entry));
  return { items: { ...ITEMS, names }, questions: { ...QUESTIONS, names: { ...QUESTIONS.names, set_aside: SET_ASIDE } } };
}

test('before the name of an area with ground is turned down the page says that the answer will wait, and what to do', () => {
  const { desk, sit } = at('names', withGround());
  assert.equal(sit.item, 'n:syn-n0004');
  assert.deepEqual(sit.view.aside, { short: SET_ASIDE.cells.short, words: SET_ASIDE.cells.words, open: true });
  assert.deepEqual(
    sit.view.answers.map((row) => row.text),
    ['An area (proposed: Enter)', 'Another name, same ground (waits)', 'A smaller place inside (waits)', 'A wider name (waits)', 'Not a name to keep (waits)'],
  );
  assert.equal(posts(desk).length, 0, 'it is said before any answer is given');
});

test('a name that is no area has no ground, and the page says nothing of waiting', () => {
  const { sit } = at('names', withGround());
  sit.key('1');
  assert.equal(sit.item, 'a:syn-n0004:dulcimer');
  assert.equal(sit.view.aside, null);
  assert.ok(sit.view.answers.every((row) => !row.text.includes('waits')));
});

test('an area that holds other names and no ground is said to wait on them', () => {
  const { sit } = at('names', withGround('names'));
  assert.equal(sit.view.aside.short, SET_ASIDE.names.short);
  assert.equal(sit.view.aside.words, SET_ASIDE.names.words);
});

test('a queue whose question says nothing of answers set aside shows nothing of them', () => {
  const { sit } = at('names', { items: withGround().items });
  assert.equal(sit.view.aside, null);
  assert.deepEqual(sit.view.answers[4].text, 'Not a name to keep');
});

test('what to do is open on the first such item of a sitting, and shut from the next', () => {
  const { sit } = at('names', withGround());
  assert.equal(sit.view.aside.open, true);
  sit.key('1').key('s');
  assert.equal(sit.item, 'n:syn-n0007');
  assert.equal(sit.view.aside.open, false);
  assert.equal(sit.view.aside.short, SET_ASIDE.cells.short, 'that it waits is said on every such item');
});

test('when the name of an area with ground is turned down the page says that the answer was saved and that it waits', () => {
  const { desk, sit } = at('names', withGround());
  sit.key('5');
  assert.equal(desk.answersOf('names')[0].answer, 'drop', 'the answer is saved as it was given');
  assert.equal(sit.view.said, `Saved: Not a name to keep, for Dulcimer Green, Quillhaven. ${SET_ASIDE.cells.saved} Next: Dulcimer, Quillhaven.`);
  sit.key('s').key('1');
  assert.match(sit.view.said, /^Saved: An area, for Alderwick, Quillhaven\. Next: /);
});

test('the top line counts apart the answers that wait for a new draft', () => {
  const { sit } = at('names', withGround());
  sit.key('5');
  assert.match(sit.view.progress, /^Names: 0 done, 1 waits for a new draft, 3 left/);
  sit.key('s').key('1');
  assert.match(sit.view.progress, /^Names: 1 done, 1 waits for a new draft, 2 left/);
  sit.key('u');
  sit.pass(1000).key('u');
  assert.match(sit.view.progress, /^Names: 0 done, 1 waits for a new draft, 3 left/);
});

test('borders say that a name turned down still has ground, and that the draft is to be made again first', () => {
  const { sit } = at('names', withGround());
  sit.key('5').key('3').key('1').key('1');
  sit.choose('borders');
  assert.equal(sit.view.warn, '1 in Names waits for a new draft. Make the draft again from the answers, and fill the queues again, before you go on here.');
  sit.key('q');
  const row = sit.view.panel.rows.find((one) => one.text.startsWith('Borders'));
  assert.match(row.text, /1 in Names waits for a new draft\./);
});

test('borders that wait on names still to read say so, and then what waits for a new draft', () => {
  const { sit } = at('names', withGround());
  sit.key('5');
  sit.choose('borders');
  assert.match(sit.view.warn, /^Waits on 3 in Names\. 1 in Names waits for a new draft\./);
});

// ---------------------------------------------------------------- the rules put to the founder

const RULES = {
  id: 'rules',
  title: 'Rules',
  text: 'Shall this rule settle what it fits, with no person reading each?',
  rule: 'None is adopted until you say yes.',
  view: 'text',
  adds: null,
  public: true,
  answers: [
    { code: 'yes', label: 'Yes, adopt the rule' },
    { code: 'no', label: 'No, a person reads each' },
  ],
  flags: {},
};

// Two made-up rules: one accepts two names as proposed, one leaves a border as drafted.
function withRules() {
  const rule = (id, queue, gives) => ({
    ...ITEMS.kinds[0],
    id,
    group: queue,
    title: id === 'a_made_up_rule' ? 'A made up rule' : 'Every made up border',
    lines: [
      { label: 'The rule', value: 'Made up for testing.', source_id: '' },
      { label: 'Would settle', value: '2 of the 4 items of Names.', source_id: '' },
      { label: 'What could go wrong', value: 'Made up for testing.', source_id: '' },
      { label: 'Drawn at random', value: 'Alderwick, Quillhaven. Accepted as proposed: An area.', source_id: '' },
    ],
    fill: {},
    preset: { rule: id, queue, gives, settles: '0123456789ab' },
    rev: `${id.length}`.padStart(12, 'a'),
  });
  const fits = (entry, code) => ({ ...entry, preset: { ...entry.preset, fits: code } });
  const names = ITEMS.names.map((entry) => (['n:syn-n0007', 'n:syn-n0012'].includes(entry.id) ? fits(entry, 'a_made_up_rule') : entry));
  const borders = ITEMS.borders.map((entry) => (entry.id === 'syn-n0012' ? fits(entry, 'every_made_up_border') : entry));
  return {
    items: { rules: [rule('a_made_up_rule', 'names', 'proposed'), rule('every_made_up_border', 'borders', '')], ...ITEMS, names, borders },
    questions: { rules: RULES, ...QUESTIONS },
  };
}

test('a rule is shown in words, with what it would settle, what could go wrong and items drawn at random', () => {
  const { sit } = at('rules', withRules());
  assert.equal(sit.item, 'a_made_up_rule');
  assert.equal(sit.view.main.kind, 'record');
  assert.deepEqual(sit.view.main.lines.map((line) => line.label), ['The rule', 'Would settle', 'What could go wrong', 'Drawn at random']);
  assert.deepEqual(sit.view.answers.map((row) => row.text), ['Yes, adopt the rule', 'No, a person reads each']);
  assert.equal(sit.view.question, RULES.text);
});

test('yes to a rule says how many items it settled, and they leave their queue', () => {
  const { desk, sit } = at('rules', withRules());
  sit.key('1');
  assert.equal(sit.view.said, 'Saved: Yes, adopt the rule, for A made up rule. 2 items were settled by the rule. Next: Every made up border.');
  const written = desk.answersOf('names');
  assert.deepEqual(written.map((line) => [line.item, line.answer, line.detail.rule]), [
    ['n:syn-n0007', 'area', 'a_made_up_rule'],
    ['n:syn-n0012', 'area', 'a_made_up_rule'],
  ]);
  sit.choose('names');
  assert.match(sit.view.progress, /^Names: 0 done, 2 by rule, 2 left/);
  assert.deepEqual(sit.state.queue.items.map((entry) => entry.state), ['open', 'open', 'done', 'done']);
});

test('no to a rule changes nothing, and the page says so', () => {
  const { desk, sit } = at('rules', withRules());
  sit.key('2');
  assert.equal(sit.view.said, 'Saved: No, a person reads each, for A made up rule. Nothing was changed. Next: Every made up border.');
  assert.equal(desk.answersOf('names').length, 0);
});

test('undo takes back a yes and what it settled, and says how many', () => {
  const { desk, sit } = at('rules', withRules());
  sit.key('1').key('u');
  assert.equal(sit.view.said, 'Taken back: Yes, adopt the rule. 2 answers the rule gave were taken back, for A made up rule.');
  assert.equal(sit.item, 'a_made_up_rule');
  sit.choose('names');
  assert.match(sit.view.progress, /^Names: 0 done, 4 left/);
  assert.equal(desk.lines.names.filter((line) => line.answer === 'undo').length, 2);
});

test('an item a rule settled says which rule, and that the person may still answer it', () => {
  const { sit } = at('rules', withRules());
  sit.key('1');
  sit.choose('names');
  sit.key(']').key(']');
  assert.equal(sit.item, 'n:syn-n0007');
  assert.equal(sit.view.mine, 'Settled by the rule "a made up rule": An area. Your own answer takes its place.');
  sit.key('5');
  assert.match(sit.view.said, /^Saved: Not a name to keep, for Alderwick, Quillhaven\./);
  assert.equal(sit.item, 'n:syn-n0004', 'the next open item, from the start');
  sit.key(']').key(']');
  assert.equal(sit.item, 'n:syn-n0007');
  assert.equal(sit.view.mine, 'You answered: Not a name to keep.');
});

test('a border that a rule leaves as drafted says so, and is offered to nobody', () => {
  const { sit } = at('rules', withRules());
  sit.key('2').key('1');
  assert.match(sit.view.said, /^Saved: Yes, adopt the rule, for Every made up border\. 1 item was settled by the rule\./);
  sit.choose('borders');
  assert.equal(sit.item, 'syn-n0007');
  assert.match(sit.view.progress, /^Borders: 0 done, 1 by rule, 1 left/);
  sit.key(']');
  assert.equal(sit.view.mine, 'Settled by the rule "every made up border": left as drafted. Your own answer takes its place.');
});

test('the list of queues puts the rules first and says what waits on them', () => {
  const options = withRules();
  options.questions = { ...options.questions, names: { ...QUESTIONS.names, after: ['rules'] } };
  const { sit } = at(null, options);
  assert.equal(sit.view.panel.rows[0].key, '1');
  assert.match(sit.view.panel.rows[0].text, /^Rules: 0 done, 2 left/);
  assert.match(sit.view.panel.rows[1].text, /^Names: .*Waits on 2 in Rules\./);
});

// A third made-up rule leans on the first: it settles a name only where the first is
// adopted too. One name leans on the first rule, and one on a rule that is never put
// to a yes here.
function withLeaning() {
  const held = withRules();
  const [first, borders] = held.items.rules;
  const other = { ...first, id: 'another_made_up_rule', title: 'Another made up rule', rev: 'b'.repeat(12), preset: { ...first.preset, rule: 'another_made_up_rule' } };
  const leaning = {
    ...first,
    id: 'a_rule_that_leans',
    title: 'A rule that leans',
    rev: 'c'.repeat(12),
    lines: [
      { label: 'The rule', value: 'Made up for testing.', source_id: '' },
      { label: 'Would settle', value: '2 of the 4 items of Names.', source_id: '' },
      { label: 'Leans on', value: 'This rule settles an item only where the rule the item leans on is adopted too.', source_id: '' },
      { label: 'What could go wrong', value: 'Made up for testing.', source_id: '' },
    ],
    preset: { ...first.preset, rule: 'a_rule_that_leans', leans_on: ['a_made_up_rule', 'another_made_up_rule'] },
  };
  const leans = { 'n:syn-n0004': 'a_made_up_rule', 'a:syn-n0004:dulcimer': 'another_made_up_rule' };
  const names = held.items.names.map((entry) => (leans[entry.id] ? { ...entry, preset: { ...entry.preset, fits: 'a_rule_that_leans', leans_on: leans[entry.id] } } : entry));
  return { ...held, items: { ...held.items, rules: [first, other, leaning, borders], names } };
}

test('a rule that leans on others says which of them stand adopted, and what it would settle as they stand', () => {
  const { sit } = at('rules', withLeaning());
  sit.key(']').key(']');
  assert.equal(sit.item, 'a_rule_that_leans');
  const lines = sit.view.main.lines;
  assert.deepEqual(lines.map((line) => line.label), ['The rule', 'Would settle', 'Leans on', 'As the rules stand', 'What could go wrong']);
  assert.equal(
    lines[3].value,
    'None of the rules it leans on is adopted: A made up rule, Another made up rule. A yes to this rule settles nothing until one of them is adopted.',
  );
  sit.key('[').key('[').key('1');
  assert.equal(sit.item, 'another_made_up_rule');
  sit.key(']');
  assert.equal(
    sit.view.main.lines[3].value,
    'Adopted: A made up rule. Not adopted: Another made up rule. A yes to this rule settles the 1 item that leans on a rule that is adopted, and leaves the 1 that does not.',
  );
});

test('yes to a rule that leans settles nothing while no rule it leans on is adopted, and says so', () => {
  const { desk, sit } = at('rules', withLeaning());
  sit.key(']').key(']').key('1');
  assert.equal(
    sit.view.said,
    'Saved: Yes, adopt the rule, for A rule that leans. Nothing was settled: 2 items wait until the rule each leans on is adopted. Next: Every made up border.',
  );
  assert.equal(desk.answersOf('names').length, 0);
});

test('a rule that leans settles only what leans on a rule that is adopted, in whichever order they are adopted', () => {
  const { desk, sit } = at('rules', withLeaning());
  sit.key(']').key(']').key('1');
  sit.key('[').key('[').key('[');
  assert.equal(sit.item, 'a_made_up_rule');
  sit.key('1');
  assert.match(sit.view.said, /^Saved: Yes, adopt the rule, for A made up rule\. 3 items were settled by the rule\. 1 item waits until the rule it leans on is adopted\./);
  assert.deepEqual(
    desk.answersOf('names').map((line) => [line.item, line.detail.rule]).sort(),
    [['n:syn-n0004', 'a_rule_that_leans'], ['n:syn-n0007', 'a_made_up_rule'], ['n:syn-n0012', 'a_made_up_rule']],
  );
  // The rule leant on is taken back: what leant on it goes with it.
  sit.key('u');
  assert.match(sit.view.said, /^Taken back: Yes, adopt the rule\. 3 answers the rule gave were taken back/);
  assert.equal(desk.lines.names.filter((line) => line.answer === 'undo').length, 3);
});

// ---------------------------------------------------------------- the items drawn for a rule

// The first made-up rule shows two of the names it would settle, and holds their ids.
function withDrawn() {
  const held = withRules();
  const [first, borders] = held.items.rules;
  const drawn = {
    ...first,
    lines: [
      ...first.lines.slice(0, 3),
      { label: 'Drawn at random, 1 of 2', value: 'Alderwick, Quillhaven. Accepted as proposed: An area.', source_id: '' },
      { label: 'Drawn at random, 2 of 2', value: 'Thrushcombe, Marrowmere. Accepted as proposed: An area.', source_id: '' },
    ],
    preset: { ...first.preset, drawn: ['n:syn-n0007', 'n:syn-n0012'] },
  };
  return { ...held, items: { ...held.items, rules: [drawn, borders] } };
}

test('a rule says before the items it shows which key opens them', () => {
  const { sit } = at('rules', withDrawn());
  const lines = sit.view.main.lines;
  assert.deepEqual(lines.map((line) => line.label), ['The rule', 'Would settle', 'What could go wrong', 'To open them', 'Drawn at random, 1 of 2', 'Drawn at random, 2 of 2']);
  assert.equal(lines[3].value, SAYS.openDrawn);
  // A rule that shows no item says nothing of opening one.
  sit.key(']');
  assert.ok(!sit.view.main.lines.some((line) => line.label === 'To open them'));
});

test('an item that is drawn is opened from its rule, in its own queue, and the page says where it is', () => {
  const { desk, sit } = at('rules', withDrawn());
  sit.key('o');
  assert.equal(sit.state.queue.id, 'names');
  assert.equal(sit.item, 'n:syn-n0007');
  assert.equal(sit.view.main.kind, 'map');
  assert.equal(sit.view.warn, 'Drawn for the rule A made up rule, 1 of 2. Nothing is decided here. ] and [ go through them. o goes back to the rule.');
  sit.key(']');
  assert.equal(sit.item, 'n:syn-n0012', 'the next that is drawn, and not the next of the queue');
  assert.match(sit.view.warn, /^Drawn for the rule A made up rule, 2 of 2\./);
  sit.key(']');
  assert.equal(sit.item, 'n:syn-n0012');
  assert.equal(sit.view.said, SAYS.lastDrawn);
  sit.key('[').key('[');
  assert.equal(sit.item, 'n:syn-n0007');
  assert.equal(sit.view.said, SAYS.firstDrawn);
  assert.equal(posts(desk).length, 0);
});

test('the same key comes back to the rule, and the rule is as it was left', () => {
  const { desk, sit } = at('rules', withDrawn());
  sit.key('o').key(']').key('o');
  assert.equal(sit.state.queue.id, 'rules');
  assert.equal(sit.item, 'a_made_up_rule');
  assert.equal(sit.view.main.kind, 'record');
  assert.equal(sit.view.warn, '');
  assert.equal(sit.state.visit, null);
  // The rule is then answered as any rule is.
  sit.key('1');
  assert.match(sit.view.said, /^Saved: Yes, adopt the rule, for A made up rule\. 2 items were settled by the rule\./);
  assert.equal(posts(desk).length, 1);
});

test('nothing is decided while an item that is drawn is looked at', () => {
  const { desk, sit } = at('rules', withDrawn());
  sit.key('o');
  for (const key of ['1', '5', 'Enter', 's', 'u', 'j']) {
    sit.key(key);
    assert.equal(sit.view.said, SAYS.visiting, key);
    assert.equal(sit.item, 'n:syn-n0007', key);
  }
  assert.equal(posts(desk).length, 0);
  assert.equal(desk.answersOf('names').length, 0);
});

test('another queue chosen from the list ends the look at what was drawn', () => {
  const { sit } = at('rules', withDrawn());
  sit.key('o');
  sit.choose('names');
  assert.equal(sit.state.visit, null);
  assert.equal(sit.view.warn, '');
  sit.key('1');
  assert.match(sit.view.said, /^Saved: An area/);
});

test('where a rule shows no item the key says so and leaves the rule', () => {
  const { sit } = at('rules', withRules());
  sit.key('o');
  assert.equal(sit.state.queue.id, 'rules');
  assert.equal(sit.view.said, SAYS.noneDrawn);
  sit.choose('names').key('o');
  assert.equal(sit.view.said, SAYS.noneDrawn);
});
