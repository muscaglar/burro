// The page itself, run against a stand-in for the browser and one for the desk.
// No browser was opened: what these hold is what the page writes and asks for,
// not how it looks.

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { boot } from '../desk.mjs';
import { HOLD_MS, SAYS } from '../logic.mjs';
import { themeOf } from '../map.mjs';
import { LAYERS } from './support/city.mjs';
import { browser } from './support/dom.mjs';
import { ITEMS, QUESTIONS, standIn } from './support/standin.mjs';

async function open(queue, options = {}) {
  const desk = standIn({ layers: LAYERS, resume: queue ? { queue, item: options.item || null } : null, ...options });
  const page = browser(desk.fetch, options);
  page.desk = desk;
  page.app = boot(page.env);
  await page.settle();
  return page;
}

function lines(page, queue) {
  return page.desk.answersOf(queue);
}

function ops(page) {
  return page.calls.map((call) => call[0]);
}

function drawn(page) {
  return page.calls.filter((call) => call[0] !== 'set').length;
}

// ---------------------------------------------------------------- what is on the screen

test('before the desk has answered the page says that it does not yet know which data this is', () => {
  const page = browser(async () => new Promise(() => {}));
  assert.match(page.text('banner'), /Decide nothing yet/);
  boot(page.env);
  assert.equal(page.$('banner').className, 'banner unknown');
  assert.equal(page.$('answers').children.length, 0);
});

test('the page says on its top line and in its title that the city is made up', async () => {
  const page = await open('names');
  assert.equal(page.text('banner'), SAYS.madeUp);
  assert.equal(page.$('banner').className, 'banner made-up');
  assert.equal(page.document.title, 'Made-up city - Burro review desk');
});

test('the page says on its top line and in its title that the data is real', async () => {
  const page = await open('names', { synthetic: false, layers: {} });
  assert.equal(page.text('banner'), SAYS.real);
  assert.equal(page.$('banner').className, 'banner real');
  assert.equal(page.document.title, 'Real data - Burro review desk');
});

test('the top line is there on every screen: a map, a text, a record, a list and an empty queue', async () => {
  for (const queue of ['names', 'sentences', 'kinds']) {
    const page = await open(queue);
    assert.equal(page.text('banner'), SAYS.madeUp, queue);
    for (const key of ['q', 'g', '?']) {
      await page.key(key);
      assert.equal(page.text('banner'), SAYS.madeUp, `${queue}, ${key} open`);
      if (page.$('panel').open) {
        assert.equal(page.text('panel-banner'), SAYS.madeUp, `${queue}, in the list of ${key}`);
        assert.equal(page.$('panel-banner').className, 'banner made-up');
      }
      await page.key('Escape');
    }
  }
  const real = await open(null, { synthetic: false, layers: {} });
  assert.equal(real.$('panel').open, true);
  assert.equal(real.text('panel-banner'), SAYS.real);
  assert.equal(real.$('panel-banner').className, 'banner real');
  const page = await open('kinds');
  await page.key('1');
  assert.match(page.text('wait'), /^Nothing left/);
  assert.equal(page.text('banner'), SAYS.madeUp);
});

test('the item, the question and the answers are shown, each answer with its key', async () => {
  const page = await open('names');
  assert.equal(page.text('title'), 'Dulcimer Green, Quillhaven');
  assert.equal(page.text('flags'), 'Here because: one publisher');
  assert.equal(page.text('question'), 'Is this the name of an area?');
  assert.match(page.text('rule'), /^Use what you know/);
  assert.equal(page.$('rule-box').hidden, false);
  const rows = page.$('answers').children.map((row) => row.children[0].children.map((part) => `${part.tagName} ${part.textContent}`));
  assert.deepEqual(rows[0], ['KBD 1', 'SPAN An area (proposed: Enter)']);
  assert.deepEqual(rows[4], ['KBD 5', 'SPAN Not a name to keep']);
  assert.equal(rows.length, 5);
});

test('progress is in view from the first item', async () => {
  const page = await open('names');
  assert.equal(page.text('progress'), 'Names: 0 done, 4 left, 1 of them flagged, no pace yet');
  assert.equal(page.text('reviewer'), 'Reviewer r1');
  page.at += 30000;
  await page.key('1');
  assert.equal(page.text('progress'), 'Names: 1 done, 3 left, 31 s each, about 2 min left at this pace');
});

test('the keys are on the bottom line, each a button that does what its key does', async () => {
  const page = await open('names');
  const bar = page.$('bar').children;
  assert.deepEqual(bar.map((node) => node.children[0].textContent), ['1-9', 's', 'u', 'n', 'f', '[', ']', 'j', 'g', 'q', 'p', '?']);
  page.at += 1000;
  bar.find((node) => node.children[0].textContent === 's').click();
  await page.settle();
  assert.equal(lines(page, 'names')[0].answer, 'skip');
});

test('a sentence is shown marked, between the one before and the one after', async () => {
  const page = await open('sentences');
  assert.equal(page.$('text-box').hidden, false);
  assert.equal(page.$('map-box').hidden, true);
  assert.equal(page.text('text-before'), 'The mill closed long ago.');
  assert.equal(page.$('text-mark').tagName, 'MARK');
  assert.equal(page.text('text-mark'), 'Alderwick has a clock tower on its green.');
  assert.equal(page.text('text-after'), 'A market is held beside it.');
  assert.equal(page.text('lines'), 'HeadingPlaces and buildings (synthetic)');
  assert.equal(page.$('rule-box').hidden, true, 'a queue with no rule shows no place for one');
});

test('a source is named after a value, unless the label names it already', async () => {
  const items = {
    kinds: [{
      id: 'syn-p0001', rev: 'aaaaaaaaaaaa', group: 'landmark', title: 'The Alderwick Clock',
      lines: [{ label: 'synthetic-names', value: 'Alderwick Clock', source_id: 'synthetic-names' }, { label: 'Sample', value: '3 of 9', source_id: '' }],
      text: null, map: null, picks: null, flags: [], fill: { kind: 'landmark' }, preset: {},
    }],
  };
  const page = await open('kinds', { items });
  assert.deepEqual(page.$('record').children.map((node) => node.textContent), ['synthetic-names', 'Alderwick Clock', 'Sample', '3 of 9']);
});

test('a source is not named after a value that is the source itself', async () => {
  const items = {
    kinds: [{
      id: 'syn-p0001', rev: 'aaaaaaaaaaaa', group: 'landmark', title: 'The Alderwick Clock',
      lines: [{ label: 'Category as written', value: 'monument', source_id: 'synthetic' }, { label: 'Source', value: 'synthetic', source_id: 'synthetic' }],
      text: null, map: null, picks: null, flags: [], fill: { kind: 'landmark' }, preset: {},
    }],
  };
  const page = await open('kinds', { items });
  assert.deepEqual(page.$('record').children.map((node) => node.textContent), ['Category as written', 'monument (synthetic)', 'Source', 'synthetic']);
});

test('a record of a venue is shown with its kind in the question', async () => {
  const page = await open('kinds');
  assert.equal(page.$('record').hidden, false);
  assert.deepEqual(page.$('record').children.map((node) => `${node.tagName} ${node.textContent}`), [
    'DT Name',
    'DD The Alderwick Clock (synthetic)',
    'DT Category as written',
    'DD monument (synthetic)',
    'DT Given by',
    'DD synthetic',
  ]);
  assert.equal(page.text('question'), 'Is this a landmark?');
});

test('the name of the item is printed once: over the item, and not beside it nor under it', async () => {
  // At the desk the name was printed three times in a queue of words: over the
  // text, in the column, and as what was said.
  for (const [queue, name] of [['kinds', 'The Alderwick Clock'], ['names', 'Dulcimer Green, Quillhaven'], ['sentences', 'Alderwick, in the made-up encyclopaedia']]) {
    const page = await open(queue);
    assert.equal(page.text('title'), name);
    assert.ok(page.$('item').contains(page.$('title')), `${queue}: over the item`);
    assert.doesNotMatch(page.$('side').textContent, new RegExp(name), `${queue}: not in the column`);
    assert.equal(page.text('said'), name, 'it is said aloud');
    assert.equal(page.$('said').className, 'unseen', `${queue}: and not printed again`);
  }
});

test('what was saved is printed, in the line under the top line', async () => {
  const page = await open('names');
  await page.key('1');
  assert.match(page.text('said'), /^Saved: An area, for Dulcimer Green, Quillhaven\. Next: /);
  assert.equal(page.$('said').className, '');
  assert.ok(!page.$('side').contains(page.$('said')));
  assert.ok(!page.$('side').contains(page.$('trouble')));
});

test('the words under the note are shown while a note is written or kept, and at no other time', async () => {
  const page = await open('names');
  assert.equal(page.$('note-hint').hidden, true);
  await page.key('n');
  assert.equal(page.$('note-hint').hidden, false);
  assert.equal(page.text('note-hint'), SAYS.noteHint);
  await page.type('on the sign');
  await page.key('Enter', { on: page.$('note') });
  assert.equal(page.$('note-hint').hidden, false, 'a note is kept');
  await page.key('1');
  assert.equal(page.$('note-hint').hidden, true, 'the note went with the answer');
  page.$('note').focus();
  await page.settle();
  assert.equal(page.$('note-hint').hidden, false, 'a click in the note shows them too');
});

test('an answer that waits for its note shows the words under the note', async () => {
  const page = await open('borders');
  await page.key('2');
  assert.equal(page.document.activeElement, page.$('note'));
  assert.equal(page.$('note-hint').hidden, false);
});

test('the rule is open on the first item of a queue, and shut from the next', async () => {
  const page = await open('names');
  assert.equal(page.$('rule-box').open, true);
  await page.key('1');
  assert.equal(page.$('rule-box').open, false);
  await page.key('3');
  assert.equal(page.$('rule-box').open, false);
  await page.key('q');
  await page.key('2');
  assert.equal(page.text('question'), 'Is this boundary right?');
  assert.equal(page.$('rule-box').open, true, 'the first item of another queue');
});

test('a rule that a person opened stays open until the next item', async () => {
  const page = await open('names');
  await page.key('1');
  page.$('rule-box').open = true;
  await page.key('f');
  assert.equal(page.$('rule-box').open, true);
  await page.key('3');
  assert.equal(page.$('rule-box').open, false);
});

test('the rule is shut at once where it would push an answer out of view', async () => {
  const desk = standIn({ layers: LAYERS, resume: { queue: 'names', item: null } });
  const page = browser(desk.fetch);
  // A window so low that the question, the rule and the answers do not fit.
  page.$('ask').scrollHeight = 700;
  page.$('ask').clientHeight = 500;
  boot(page.env);
  await page.settle();
  assert.equal(page.$('rule-box').open, false);
  assert.equal(page.$('rule-box').hidden, false, 'it is there to be opened');
});

test('the rule is shut where the line that says there is more to read pushes an answer out of view', async () => {
  // Seen at the desk, on the first name of London in a window of 1440 by 900: the
  // answers fitted until the line under what is known was shown, and that line took
  // its height from them. The mark for a second reviewer was cut by the keys.
  const desk = standIn({ layers: LAYERS, resume: { queue: 'names', item: null } });
  const page = browser(desk.fetch);
  page.$('known').scrollHeight = 546;
  page.$('known').clientHeight = 196;
  page.$('ask').scrollHeight = 590;
  Object.defineProperty(page.$('ask'), 'clientHeight', { get: () => (page.$('more').hidden ? 600 : 548) });
  boot(page.env);
  await page.settle();
  assert.equal(page.$('more').hidden, false, 'there is more to read');
  assert.equal(page.$('rule-box').open, false, 'the rule gave way to the answers');
  assert.equal(page.$('rule-box').hidden, false, 'it is there to be opened');
});

test('what is known keeps a floor only where it is long, and the page says when there is more to read', async () => {
  const page = await open('names');
  assert.equal(page.$('side').className, '');
  assert.equal(page.$('more').hidden, true);
  page.$('known').scrollHeight = 546;
  page.$('known').clientHeight = 196;
  await page.key('f');
  assert.equal(page.$('side').className, 'floor');
  assert.equal(page.$('more').hidden, false);
  assert.match(page.text('more'), /^More below\. Press/);
  // The next item is short: the floor of the last is not left on it.
  page.$('known').scrollHeight = 60;
  page.$('known').clientHeight = 196;
  await page.key('1');
  assert.equal(page.$('side').className, '');
  assert.equal(page.$('more').hidden, true);
});

test('a key pages what is known of the item, and the next item is read from its top', async () => {
  const page = await open('names');
  page.$('known').scrollHeight = 546;
  page.$('known').clientHeight = 196;
  assert.equal((await page.key('.')).defaultPrevented, true);
  assert.equal(page.$('known').scrollTop, 148);
  await page.key('PageDown');
  assert.equal(page.$('known').scrollTop, 296);
  await page.key(',');
  assert.equal(page.$('known').scrollTop, 148);
  await page.key('PageUp');
  await page.key('PageUp');
  assert.equal(page.$('known').scrollTop, 0);
  await page.key('.');
  await page.key('1');
  assert.equal(page.$('known').scrollTop, 0);
  assert.deepEqual(lines(page, 'names').map((line) => line.answer), ['area'], 'a key that pages decides nothing');
});

test('a letter typed in the note does not draw the map again', async () => {
  const page = await open('borders');
  await page.key('n');
  const before = drawn(page);
  await page.type('t');
  await page.type('th');
  await page.type('the');
  assert.equal(drawn(page), before);
  await page.key('Escape', { on: page.$('note') });
  await page.key('+');
  assert.ok(drawn(page) > before);
});

test('an area is rated with its outline in view, six keys and one for the whole area, and no score', async () => {
  const page = await open('ratings');
  assert.equal(page.$('map-box').hidden, false);
  assert.equal(page.text('question'), 'How much of the street is under trees, or beside grass?');
  assert.equal(page.$('answers').children.length, 7);
  assert.equal(page.$('answers').children[6].textContent, '7I do not know this area');
  assert.equal(page.text('lines'), '');
  assert.doesNotMatch(page.$('side').textContent, /score|band/i);
});

test('words from a file are written as text and never as markup', async () => {
  const items = {
    kinds: [{
      id: 'syn-p0001', rev: 'aaaaaaaaaaaa', group: 'landmark', title: '<img src=x onerror=alert(1)>',
      lines: [{ label: '<b>Name</b>', value: '<script>alert(1)</script>', source_id: 'synthetic' }],
      text: null, map: null, picks: null, flags: [], fill: { kind: '<i>landmark</i>' }, preset: {},
    }],
  };
  const page = await open('kinds', { items });
  assert.equal(page.text('title'), '<img src=x onerror=alert(1)>');
  assert.equal(page.text('question'), 'Is this a <i>landmark</i>?');
  assert.equal(page.$('record').children[1].textContent, '<script>alert(1)</script> (synthetic)');
  assert.equal(page.$('record').find((node) => ['SCRIPT', 'IMG', 'B', 'I'].includes(node.tagName)), null);
});

test('an address in a line is shown as text to copy and never as a link', async () => {
  const items = {
    kinds: [{
      id: 'syn-p0001', rev: 'aaaaaaaaaaaa', group: 'landmark', title: 'The Alderwick Clock',
      lines: [{ label: 'Address of the revision', value: 'https://encyclopaedia.invalid/w/index.php?oldid=1', source_id: 'synthetic' }],
      text: null, map: null, picks: null, flags: [], fill: { kind: 'landmark' }, preset: {},
    }],
  };
  const page = await open('kinds', { items });
  assert.equal(page.$('item').find((node) => node.tagName === 'A'), null);
  assert.equal(page.$('side').find((node) => node.tagName === 'A'), null);
  assert.match(page.text('record'), /https:\/\/encyclopaedia\.invalid/);
});

// ---------------------------------------------------------------- the keyboard

test('one key answers and the next item is on screen', async () => {
  const page = await open('names');
  await page.key('1');
  assert.equal(lines(page, 'names')[0].answer, 'area');
  assert.equal(page.text('title'), 'Dulcimer, Quillhaven');
  assert.match(page.text('said'), /^Saved: /);
});

test('a key the page acts on is kept from the browser, and any other is left to it', async () => {
  const page = await open('names');
  assert.equal((await page.key('1')).defaultPrevented, true);
  assert.equal((await page.key('Tab')).defaultPrevented, false);
  assert.equal((await page.key('r', { metaKey: true })).defaultPrevented, false);
  assert.equal((await page.key('F5')).defaultPrevented, false);
});

// The guard against words is in logic.mjs, and is tested there. These hold the
// wiring: a key struck in the browser reaches the guard, and not the action.

test('a sentence typed with the note shut, through the page own listener, answers nothing and skips nothing', async () => {
  const page = await open('names');
  await page.pass(2000);
  await page.strike('this is not a hall');
  await page.pass(2000);
  assert.deepEqual(page.desk.lines.names || [], [], 'no line was written: no skip, no undo, no answer');
  assert.equal(page.text('title'), 'Dulcimer Green, Quillhaven');
  assert.equal(page.app.state.noteOpen, false);
  assert.equal(page.text('said'), SAYS.pressN);
});

test('a sentence that begins with a short word is words too', async () => {
  for (const words of ['so it is', 'up the hill', 'a hall', 'is it a farm']) {
    const page = await open('names');
    await page.key('1');
    await page.pass(2000);
    const before = page.desk.lines.names.length;
    await page.strike(words);
    await page.pass(2000);
    assert.equal(page.desk.lines.names.length, before, `${words}: no line was written`);
    assert.equal(page.text('title'), 'Dulcimer, Quillhaven', words);
    assert.equal(page.text('said'), SAYS.pressN, words);
    assert.equal(page.app.state.paused, false, `${words}: the page is not paused`);
  }
});

test('a letter struck in the browser is held a moment before it acts, and a digit is not', async () => {
  const page = await open('names');
  await page.pass(2000);
  const [event] = await page.strike('s', 0);
  assert.equal(event.defaultPrevented, true, 'the key is the page own');
  assert.deepEqual(page.desk.lines.names || [], [], 'held');
  await page.pass(HOLD_MS - 1);
  assert.deepEqual(page.desk.lines.names || [], [], 'still held');
  await page.pass(1);
  assert.deepEqual(page.desk.lines.names.map((line) => line.answer), ['skip']);
  await page.pass(2000);
  await page.strike('3', 0);
  assert.deepEqual(page.desk.lines.names.map((line) => line.answer), ['skip', 'inside']);
});

test('a click on an answer does what its key does', async () => {
  const page = await open('names');
  page.at += 1000;
  page.$('answers').children[4].children[0].click();
  await page.settle();
  assert.equal(lines(page, 'names')[0].answer, 'drop');
});

test('the keyboard stays on the button a person used', async () => {
  const page = await open('names');
  const button = page.$('answers').children[0].children[0];
  button.focus();
  page.at += 1000;
  button.click();
  await page.settle();
  assert.equal(page.text('title'), 'Dulcimer, Quillhaven');
  assert.equal(page.document.activeElement, button);
  assert.equal(page.$('answers').children[0].children[0], button);
});

test('a click of the mouse on an answer gives the keyboard back, so that Enter takes what is proposed', async () => {
  const page = await open('names');
  const button = page.$('answers').children[4].children[0];
  button.focus();
  page.at += 1000;
  button.fire('click', { detail: 1 });
  await page.settle();
  assert.equal(lines(page, 'names')[0].answer, 'drop');
  assert.equal(page.document.activeElement, page.$('item'));
  await page.key('Enter');
  assert.deepEqual(lines(page, 'names').map((line) => line.answer), ['drop', 'inside']);
});

test('Enter on an answer a person reached by the keyboard gives that answer', async () => {
  const page = await open('names');
  const button = page.$('answers').children[4].children[0];
  button.focus();
  page.at += 1000;
  const enter = await page.key('Enter', { on: button });
  assert.equal(enter.defaultPrevented, false, 'Enter is left to the button');
});

test('on a name proposed as another name no answer makes an area, and a click gives the answer it is on', async () => {
  // The desk refuses such an answer. The page offered it all the same, and said why
  // only once the key was struck.
  const page = await open('names');
  assert.equal(page.$('not-offered').hidden, true);
  await page.key('1');
  assert.equal(page.text('title'), 'Dulcimer, Quillhaven');
  assert.deepEqual(
    [...page.$('answers').children].map((row) => row.children[0].textContent),
    ['2Another name, same ground', '3A smaller place inside (proposed: Enter)', '4A wider name', '5Not a name to keep'],
  );
  assert.equal(page.$('not-offered').hidden, false);
  assert.equal(page.text('not-offered'), SAYS.noKeyForArea);
  page.at += 1000;
  page.$('answers').children[3].children[0].click();
  await page.settle();
  assert.deepEqual(lines(page, 'names').map((line) => line.answer), ['area', 'drop']);
  assert.equal(page.$('not-offered').hidden, true, 'the next name is proposed as an area');
});

test('the answer proposed is marked on the screen', async () => {
  const page = await open('names');
  assert.deepEqual(
    [...page.$('answers').children].map((row) => row.children[0].children[1].textContent),
    ['An area (proposed: Enter)', 'Another name, same ground', 'A smaller place inside', 'A wider name', 'Not a name to keep'],
  );
});

test('the note opens on n, takes the keyboard, and gives it back on Enter', async () => {
  const page = await open('names');
  await page.key('n');
  assert.equal(page.document.activeElement, page.$('note'));
  await page.type('on the sign');
  await page.key('1', { on: page.$('note') });
  assert.deepEqual(lines(page, 'names'), []);
  await page.key('Enter', { on: page.$('note') });
  assert.equal(page.document.activeElement, page.$('item'));
  assert.equal(page.$('note').value, 'on the sign');
  await page.key('1');
  assert.equal(lines(page, 'names')[0].note, 'on the sign');
  assert.equal(page.$('note').value, '');
});

test('a click in the note opens it, so that no letter typed there is an answer', async () => {
  const page = await open('names');
  page.$('note').focus();
  await page.settle();
  assert.equal(page.app.state.noteOpen, true);
  await page.key('s', { on: page.$('note') });
  assert.deepEqual(lines(page, 'names'), []);
});

test('the box for a second reviewer and its key agree', async () => {
  const page = await open('names');
  await page.key('f');
  assert.equal(page.$('second').checked, true);
  page.$('second').checked = false;
  page.$('second').fire('change');
  await page.key('1');
  assert.equal(lines(page, 'names')[0].second, false);
});

test('the list of queues opens over the page and a digit chooses from it', async () => {
  const page = await open('names');
  await page.key('q');
  assert.equal(page.$('panel').open, true);
  assert.equal(page.text('panel-title'), 'Queues');
  assert.equal(page.$('panel-rows').children.length, 5);
  assert.equal(page.document.activeElement, page.$('panel-rows').children[0].children[0]);
  await page.key('3');
  assert.equal(page.$('panel').open, false);
  assert.equal(page.text('question'), 'Is this sentence fit to quote about the place?');
});

test('the arrows move along a list and Enter on a row chooses it', async () => {
  const page = await open('names');
  await page.key('g');
  await page.key('ArrowDown');
  await page.key('ArrowDown');
  const row = page.$('panel-rows').children[2].children[0];
  assert.equal(page.document.activeElement, row);
  assert.equal(row.getAttribute('aria-current'), 'true');
  const enter = await page.key('Enter');
  assert.equal(enter.defaultPrevented, false, 'Enter is left to the button');
  row.click();
  await page.settle();
  assert.equal(page.text('title'), 'Thrushcombe, Marrowmere');
});

test('a list shut by the browser is shut for the page too', async () => {
  const page = await open('names');
  await page.key('q');
  page.$('panel').close();
  await page.settle();
  assert.equal(page.app.state.panel, null);
  await page.key('1');
  assert.equal(lines(page, 'names').length, 1);
});

test('the keys are listed on one key', async () => {
  const page = await open('names');
  await page.key('?');
  assert.equal(page.text('panel-title'), 'Keys');
  const rows = page.$('panel-rows').children.map((row) => row.children[0].textContent);
  for (const key of ['1-9', 's', 'u', 'n', 'f', 'g', 'q', 'p', '?', 'm', 'a-e', 'Esc']) assert.ok(rows.includes(key), key);
  await page.key('Escape');
  assert.equal(page.$('panel').open, false);
});

test('a pause is said on the top line', async () => {
  const page = await open('names');
  await page.key('p');
  assert.match(page.text('progress'), /^PAUSED\. /);
  assert.equal(page.document.body.className, 'paused');
  await page.key('1');
  assert.deepEqual(lines(page, 'names'), []);
  await page.key('p');
  assert.equal(page.document.body.className, '');
});

test('the clock stops while the tab is out of view', async () => {
  const page = await open('names');
  page.at += 4000;
  page.document.hidden = true;
  page.document.body.fire('visibilitychange');
  page.at += 600000;
  page.document.hidden = false;
  page.document.body.fire('visibilitychange');
  page.at += 3000;
  await page.key('1');
  assert.equal(lines(page, 'names')[0].seconds, 8);
});

test('a page opened in a tab that is out of view counts nothing until it is seen', async () => {
  // At the desk the page was opened in a tab behind another, and its lines
  // said that items had been read for 26, 37 and 59 seconds.
  const desk = standIn({ layers: LAYERS, resume: { queue: 'names', item: null } });
  const page = browser(desk.fetch);
  page.document.hidden = true;
  boot(page.env);
  await page.settle();
  page.at += 600000;
  page.document.hidden = false;
  page.document.body.fire('visibilitychange');
  page.at += 3000;
  await page.key('1');
  assert.equal(desk.answersOf('names')[0].seconds, 4);
});

// ---------------------------------------------------------------- never losing an answer

test('when the desk does not answer the page says so, keeps the answer and sends it again', async () => {
  const page = await open('names');
  page.desk.down = true;
  await page.key('1');
  assert.match(page.text('trouble'), /^Not saved\. Start the desk again with make desk\. Your answer is kept here/);
  assert.equal(page.text('title'), 'Dulcimer Green, Quillhaven');
  assert.equal(page.document.body.className, 'busy');
  page.desk.again('token-2');
  await page.wait();
  assert.equal(lines(page, 'names').length, 1);
  assert.equal(page.text('trouble'), '');
  assert.equal(page.text('title'), 'Dulcimer, Quillhaven');
});

test('the page will not be closed with an answer unsaved', async () => {
  const page = await open('names');
  assert.equal(page.fireWindow('beforeunload').defaultPrevented, false);
  page.desk.down = true;
  await page.key('1');
  const event = page.fireWindow('beforeunload');
  assert.equal(event.defaultPrevented, true);
  assert.equal(event.returnValue, '');
  page.desk.down = false;
  await page.wait();
  assert.equal(page.fireWindow('beforeunload').defaultPrevented, false);
});

test('the page will not be closed while an answer waits for its note', async () => {
  const page = await open('borders');
  await page.key('2');
  assert.equal(page.document.activeElement, page.$('note'));
  assert.equal(page.fireWindow('beforeunload').defaultPrevented, true);
  await page.key('Escape', { on: page.$('note') });
  assert.equal(page.fireWindow('beforeunload').defaultPrevented, false);
});

test('an answer that is not JSON is not taken for a yes', async () => {
  const page = await open('names');
  const real = page.env.fetch;
  page.env.fetch = async (path, init) => {
    if (init.method === 'POST') return { ok: true, status: 200, json: async () => { throw new SyntaxError('not JSON'); } };
    return real(path, init);
  };
  await page.key('1');
  assert.match(page.text('trouble'), /^Not saved\./);
  assert.equal(page.text('title'), 'Dulcimer Green, Quillhaven');
});

test('every request is to the page own origin, by a path, and carries nothing in its address', async () => {
  const seen = [];
  const desk = standIn({ layers: LAYERS, resume: { queue: 'borders', item: null } });
  const page = browser(async (path, init) => {
    seen.push({ path, init });
    return desk.fetch(path, init);
  });
  boot(page.env);
  await page.settle();
  await page.key('n');
  await page.type('the brook is the border');
  await page.key('Enter', { on: page.$('note') });
  await page.key('1');
  await page.key('u');
  assert.ok(seen.length > 8);
  for (const { path, init } of seen) {
    assert.match(path, /^\/api\/[a-z]+(\/[A-Za-z0-9:_.%-]+)*$/, path);
    assert.doesNotMatch(path, /brook/);
    assert.equal(init.credentials, 'same-origin');
    assert.equal(init.cache, 'no-store');
    assert.equal(init.redirect, 'error');
  }
  const written = seen.filter(({ init }) => init.method === 'POST');
  assert.equal(written.length, 2);
  for (const { init } of written) {
    assert.equal(init.headers['Content-Type'], 'application/json');
    assert.equal(init.headers['X-Desk-Token'], 'token-1');
  }
});

// ---------------------------------------------------------------- the map



test('the map is drawn on the canvas from the layers of the item', async () => {
  const page = await open('borders');
  assert.equal(page.$('map-box').hidden, false);
  assert.ok(page.desk.asked.includes('GET /api/layer/quillhaven/cells'));
  assert.ok(page.desk.asked.includes('GET /api/layer/quillhaven/roads'));
  assert.ok(ops(page).includes('fillRect'));
  assert.ok(ops(page).includes('fill'));
  assert.equal(page.$('map').width, 1600, 'drawn at the sharpness of the screen');
  assert.equal(page.text('map-credit'), 'Drawn from: synthetic. No other map is behind it.');
});

test('the map is said in words for a person who cannot see it', async () => {
  const page = await open('borders');
  assert.equal(page.$('map').getAttribute('aria-describedby'), 'map-says');
  assert.match(page.text('map-says'), /^Map of Alderwick, Quillhaven\. 2 cells are in it\. Beside it: Thrushcombe\./);
});

test('no layer but those of the design is asked for, whatever an item says', async () => {
  const items = standIn().items;
  for (const item of items.borders) item.map.layers = ['cells', 'basemap', 'tiles', 'osm', 'stations', 'residents', 'roads'];
  const page = await open('borders', { items });
  const asked = page.desk.asked.filter((line) => line.includes('/api/layer/'));
  assert.deepEqual([...new Set(asked)].sort(), ['GET /api/layer/quillhaven/cells', 'GET /api/layer/quillhaven/roads']);
});

test('a layer the page may not draw is left out, and the page says which and why', async () => {
  const layers = { ...LAYERS, 'quillhaven/roads': { ...LAYERS['quillhaven/roads'], desk: { layer: 'roads', group: 'quillhaven', source_ids: ['openstreetmap-points-of-interest'], synthetic: true } } };
  const page = await open('borders', { layers });
  assert.match(page.text('map-credit'), /roads is not drawn: its source, openstreetmap-points-of-interest, may not stand behind a border\./);
  assert.match(page.text('map-says'), /roads is not drawn/);
  assert.ok(!ops(page).includes('fillText') || !page.calls.some((call) => call[0] === 'fillText' && call[1] === 'Quill Road'));
});

test('a layer the desk does not hold is said to be missing and the rest is drawn', async () => {
  const layers = { ...LAYERS };
  delete layers['quillhaven/wards'];
  const page = await open('borders', { layers });
  assert.match(page.text('map-credit'), /wards is not drawn: the desk did not send it\./);
  assert.ok(ops(page).includes('fill'));
});

test('a click on a cell and a click on another moves the first, and the move is written at once', async () => {
  const page = await open('borders');
  const map = page.$('map');
  const click = async (x, y) => {
    page.at += 1000;
    map.fire('pointerdown', { button: 0, clientX: x, clientY: y, pointerId: 1 });
    map.fire('pointerup', { button: 0, clientX: x, clientY: y, pointerId: 1 });
    await page.settle();
  };
  await click(200, 500);
  assert.match(page.text('said'), /^Took up cell syn-oa-0001\./);
  await click(200, 100);
  const line = lines(page, 'borders')[0];
  assert.equal(line.answer, 'move');
  assert.equal(line.part, 'syn-oa-0001');
  assert.deepEqual(line.detail, { from: 'syn-n0007', to: 'syn-n0012' });
  assert.deepEqual(page.$('moves').children.map((row) => row.textContent), ['Cell syn-oa-0001: from Alderwick to Thrushcombe']);
  assert.match(page.text('map-says'), /1 cell has been moved\./);
});

test('on the map of a name a click says which area the name is of, and the page names the area', async () => {
  const page = await open('names', { item: 'n:syn-n0007' });
  assert.equal(page.text('title'), 'Alderwick, Quillhaven');
  const map = page.$('map');
  page.at += 1000;
  map.fire('pointerdown', { button: 0, clientX: 200, clientY: 100, pointerId: 1 });
  map.fire('pointerup', { button: 0, clientX: 200, clientY: 100, pointerId: 1 });
  await page.settle();
  assert.equal(page.text('of'), 'A name of: Thrushcombe');
  await page.key('3');
  assert.deepEqual(lines(page, 'names')[0].detail, { of: ['syn-n0012'], pick: 'Alderwick', proposed: 'area' });
  assert.equal(page.text('of'), '');
});

test('a drag moves the map and moves no cell', async () => {
  const page = await open('borders');
  const map = page.$('map');
  const before = drawn(page);
  map.fire('pointerdown', { button: 0, clientX: 200, clientY: 500, pointerId: 1 });
  map.fire('pointermove', { clientX: 260, clientY: 470, pointerId: 1 });
  map.fire('pointerup', { button: 0, clientX: 260, clientY: 470, pointerId: 1 });
  await page.settle();
  assert.ok(drawn(page) > before, 'the map was drawn again');
  assert.equal(page.app.state.hand, null);
  assert.deepEqual(lines(page, 'borders'), []);
});

test('a cell is moved by the keyboard alone, with the cross and the key m', async () => {
  const page = await open('borders');
  assert.ok(ops(page).includes('moveTo'));
  await page.key('ArrowDown');
  await page.key('ArrowDown');
  await page.key('m');
  assert.match(page.text('said'), /^Took up cell syn-oa-000[12]\./);
  // Four steps up by the arrow alone, of which the last is made of four small ones.
  for (let i = 0; i < 3; i += 1) await page.key('ArrowUp');
  for (let i = 0; i < 4; i += 1) await page.key('ArrowUp', { shiftKey: true });
  await page.key('m');
  const line = lines(page, 'borders')[0];
  assert.equal(line.answer, 'move');
  assert.deepEqual(line.detail, { from: 'syn-n0007', to: 'syn-n0012' });
});

test('the map is measured after the line under it is written, so the first map is not squashed', async () => {
  // At the desk the line under the map took its height after the map was
  // drawn. The map lost 30 pixels, was stretched to fit, and the first keys
  // were lost to the draw that put it right.
  const desk = standIn({ layers: LAYERS, resume: { queue: 'borders', item: null } });
  const page = browser(desk.fetch);
  const map = page.$('map');
  Object.defineProperty(map, 'clientHeight', { get: () => (page.text('map-credit') === '' ? 600 : 570) });
  // Every layer has come before the browser draws its first frame.
  const frames = [];
  page.env.requestAnimationFrame = (fn) => frames.push(fn);
  boot(page.env);
  await page.settle();
  assert.equal(frames.length, 1, 'one frame is asked for, however many layers came');
  frames[0]();
  assert.equal(page.text('map-credit'), 'Drawn from: synthetic. No other map is behind it.');
  assert.equal(map.height, 570 * 2, 'the canvas holds as many rows as are shown');
});

test('a window that changes size keeps the map where the person put it', async () => {
  const page = await open('borders');
  await page.key('ArrowDown');
  page.$('map').clientHeight = 570;
  await page.key('ArrowDown');
  await page.key('m');
  assert.match(page.text('said'), /^Took up cell syn-oa-000[12]\./, 'the cross is where the arrows put it');
});

test('the map is drawn again when its box changes size', async () => {
  const desk = standIn({ layers: LAYERS, resume: { queue: 'borders', item: null } });
  const page = browser(desk.fetch);
  const watched = [];
  page.env.ResizeObserver = class {
    constructor(fn) {
      this.fn = fn;
    }

    observe(node) {
      watched.push({ node, fn: this.fn });
    }
  };
  boot(page.env);
  await page.settle();
  assert.equal(watched.length, 1);
  assert.ok(watched[0].node === page.$('map'), 'the canvas is what is watched');
  const before = drawn(page);
  page.$('map').clientHeight = 540;
  watched[0].fn();
  await page.settle();
  assert.ok(drawn(page) > before);
  assert.equal(page.$('map').height, 540 * 2);
});

test('the wheel zooms the map and the page does not scroll', async () => {
  const page = await open('borders');
  const before = drawn(page);
  const event = page.$('map').fire('wheel', { deltaY: -120, clientX: 400, clientY: 300 });
  await page.settle();
  assert.equal(event.defaultPrevented, true);
  assert.ok(drawn(page) > before);
});

test('in a dark room the map is drawn dark', async () => {
  const page = await open('borders', { dark: true });
  const light = await open('borders');
  const paper = (one) => one.calls.find((call) => call[0] === 'set' && call[1] === 'fillStyle')[2];
  assert.equal(paper(page), themeOf(true).paper);
  assert.equal(paper(light), themeOf(false).paper);
});

test('the layers of the next item are asked for before it is shown', async () => {
  const page = await open('names');
  assert.ok(page.desk.asked.includes('GET /api/layer/quillhaven/cells'));
  const before = page.desk.asked.length;
  await page.key('1');
  const since = page.desk.asked.slice(before).filter((line) => line.includes('/api/layer/quillhaven/'));
  assert.deepEqual(since, [], 'nothing of the group already held is asked for again');
});

// ---------------------------------------------------------------- an answer that will be set aside

const WAITS = {
  answers: ['same_ground', 'inside', 'wide', 'drop'],
  mark: 'waits',
  cells: { short: 'This area has ground. To turn its name down waits for a new draft.', words: 'Read every name first. Then make the draft again from the answers. Then look at borders.', saved: 'It is set aside until the draft is made again.' },
};

function grounded() {
  const names = ITEMS.names.map((entry) => (entry.id.startsWith('n:') ? { ...entry, preset: { ...entry.preset, holds: 'cells' } } : entry));
  return { items: { ...ITEMS, names }, questions: { ...QUESTIONS, names: { ...QUESTIONS.names, set_aside: WAITS } } };
}

test('that an answer will be set aside is printed above the answers, with what to do', async () => {
  const page = await open('names', grounded());
  assert.equal(page.$('aside-box').hidden, false);
  assert.equal(page.$('aside-box').open, true);
  assert.equal(page.text('aside-short'), WAITS.cells.short);
  assert.equal(page.text('aside'), WAITS.cells.words);
  const asked = page.$('ask').children.map((node) => node.id);
  assert.ok(asked.indexOf('aside-box') < asked.indexOf('answers'), 'it is read before an answer is given');
  await page.key('1');
  assert.equal(page.text('title'), 'Dulcimer, Quillhaven');
  assert.equal(page.$('aside-box').hidden, true, 'a name that is no area has no ground');
});

test('what to do is shut from the second such item, and a person may open it again', async () => {
  const page = await open('names', grounded());
  await page.key('1');
  await page.key('s');
  assert.equal(page.text('title'), 'Alderwick, Quillhaven');
  assert.equal(page.$('aside-box').hidden, false);
  assert.equal(page.$('aside-box').open, false);
  assert.equal(page.text('aside-short'), WAITS.cells.short);
});

// ---------------------------------------------------------------- an item read in the middle of the page

test('the line that says there is more to read goes when the last line is in view, and comes back', async () => {
  // Seen at the desk on a rule of London: "More below" stayed after the last of
  // the ten items was in view, and a person pressed the key again for nothing.
  const page = await open('kinds');
  page.$('record').scrollHeight = 900;
  page.$('record').clientHeight = 400;
  await page.key('f');
  assert.equal(page.$('more').hidden, false);
  await page.key('.');
  assert.equal(page.$('record').scrollTop, 352);
  assert.equal(page.$('more').hidden, false, 'a page and a half is left');
  await page.key('.');
  assert.ok(page.$('record').scrollTop + 400 >= 900);
  assert.equal(page.$('more').hidden, true, 'the last line is in view');
  await page.key(',');
  assert.equal(page.$('more').hidden, false, 'read back: there is more below again');
  // The wheel reads on too, and the page is told by the browser.
  page.$('record').scrollTop = 500;
  page.$('record').fire('scroll');
  assert.equal(page.$('more').hidden, true);
  // What is known of an item, in the column, is held to the same.
  const names = await open('names');
  names.$('known').scrollHeight = 546;
  names.$('known').clientHeight = 196;
  await names.key('f');
  assert.equal(names.$('more').hidden, false);
  await names.key('.');
  await names.key('.');
  await names.key('.');
  assert.equal(names.$('more').hidden, true);
});

test('an item that is read in the middle of the page is paged by the same keys, and says when there is more', async () => {
  // A rule is longer than the window: the rule, what could go wrong, and ten items.
  const page = await open('kinds');
  assert.equal(page.$('record').hidden, false);
  assert.equal(page.$('more').hidden, true);
  page.$('record').scrollHeight = 900;
  page.$('record').clientHeight = 400;
  await page.key('f');
  assert.equal(page.$('more').hidden, false);
  assert.equal((await page.key('.')).defaultPrevented, true);
  assert.equal(page.$('record').scrollTop, 352);
  await page.key(',');
  assert.equal(page.$('record').scrollTop, 0);
  await page.key('.');
  await page.key('1');
  assert.deepEqual(lines(page, 'kinds').map((line) => line.answer), ['yes'], 'a key that pages decides nothing');
});
