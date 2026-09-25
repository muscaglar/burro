// What the files of the page hold, read as text: nothing from another host,
// nothing a content security policy would refuse, nothing too small or too
// faint to read, and a manual that matches the keys.

import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { KEYS, SAYS, keyAction, start } from '../logic.mjs';
import { contrast } from './support/colour.mjs';

const folder = new URL('../', import.meta.url);
const read = (name) => readFileSync(fileURLToPath(new URL(name, folder)), 'utf8');
const html = read('index.html');
const css = read('desk.css');
const scripts = ['desk.mjs', 'logic.mjs', 'map.mjs'];

test('the page is five files and a manual, and the panel five, with no build step and no package', () => {
  const names = readdirSync(fileURLToPath(folder)).filter((name) => !name.startsWith('.')).sort();
  const desk = ['desk.css', 'desk.mjs', 'index.html', 'logic.mjs', 'map.mjs'];
  const panel = ['panel-logic.mjs', 'panel-map.mjs', 'panel.css', 'panel.html', 'panel.mjs'];
  assert.deepEqual(names, ['README.md', ...desk, ...panel, 'test'].sort());
});

test('no file of the page names another host', () => {
  for (const name of ['index.html', 'desk.css', ...scripts]) {
    const text = read(name);
    assert.doesNotMatch(text, /https?:\/\//i, name);
    assert.doesNotMatch(text, /["'(]\/\/[a-z0-9]/i, name);
    assert.doesNotMatch(text, /\bwss?:\/\//i, name);
  }
});

test('the page loads its own style sheet and its own script and nothing else', () => {
  const loaded = [...html.matchAll(/\b(?:src|href|action|poster|data|srcset)\s*=\s*"([^"]*)"/gi)].map((match) => match[1]);
  assert.deepEqual(loaded.sort(), ['/page/desk.css', '/page/desk.mjs']);
  for (const tag of ['img', 'iframe', 'object', 'embed', 'video', 'audio', 'form', 'base', 'a']) {
    assert.doesNotMatch(html, new RegExp(`<${tag}[\\s>]`, 'i'), tag);
  }
});

test('the page holds nothing a strict content security policy would refuse', () => {
  assert.doesNotMatch(html, /<style[\s>]/i);
  assert.doesNotMatch(html, /\sstyle\s*=/i);
  assert.doesNotMatch(html, /\son[a-z]+\s*=/i);
  const inline = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
  assert.equal(inline.length, 1);
  assert.match(inline[0][1], /type="module"/);
  assert.equal(inline[0][2].trim(), '');
  for (const name of scripts) {
    const text = read(name);
    assert.doesNotMatch(text, /\beval\s*\(|new Function\b|\bimport\s*\(/, name);
    assert.doesNotMatch(text, /setAttribute\(\s*['"]style['"]|\.style\.|\.cssText/, name);
  }
});

test('no script writes markup', () => {
  for (const name of scripts) {
    assert.doesNotMatch(read(name), /innerHTML|outerHTML|insertAdjacentHTML|document\.write|DOMParser|createContextualFragment/, name);
  }
});

test('no script keeps anything in the browser or sends anything but by fetch', () => {
  for (const name of scripts) {
    const text = read(name);
    assert.doesNotMatch(text, /localStorage|sessionStorage|indexedDB|document\.cookie|caches\.|serviceWorker/, name);
    assert.doesNotMatch(text, /sendBeacon|WebSocket|EventSource|XMLHttpRequest|RTCPeerConnection|window\.open|location\.(href|assign|replace)/, name);
  }
});

test('only the file that is the page touches the screen or the network', () => {
  for (const name of ['logic.mjs', 'map.mjs']) {
    const text = read(name);
    assert.doesNotMatch(text, /\bdocument\b|\bwindow\b|\bfetch\b|\bDate\b|Math\.random|\bnavigator\b/, name);
    assert.doesNotMatch(text, /^import /m, name);
  }
});

test('the page asks the desk only by a path that logic.mjs built', () => {
  const text = read('desk.mjs');
  const asks = [...text.matchAll(/\bask\(([^,]+),/g)].map((match) => match[1].trim());
  assert.ok(asks.length >= 3);
  for (const first of asks) assert.ok(first === 'path' || first.startsWith('pathOf('), first);
  assert.equal([...text.matchAll(/\bfetch\(/g)].length, 2, 'one call in ask, and one that hands the browser own fetch in');
});

test('the page says in its language, its title and its first line what it is', () => {
  assert.match(html, /<html lang="en-GB" translate="no">/);
  assert.match(html, /<title>Loading - Burro review desk<\/title>/);
  assert.match(html, /<p id="banner" class="banner unknown">[^<]*Decide nothing yet\.<\/p>/);
  assert.match(html, /<meta name="referrer" content="no-referrer">/);
});

test('what is said aloud is marked so that a screen reader says it', () => {
  assert.match(html, /<p id="trouble" role="alert"><\/p>/);
  assert.match(html, /<details id="rule-box" open hidden>\s*<summary>The rule<\/summary>/);
  assert.match(html, /<p id="said" role="status" aria-live="polite"><\/p>/);
  assert.match(html, /<canvas id="map"[^>]*role="img"[^>]*aria-describedby="map-says"/);
  assert.match(html, /<label for="note">/);
  assert.match(html, /<label for="second">/);
  assert.match(html, /<main id="item" tabindex="-1" aria-labelledby="title">/);
  assert.match(html, /<dialog id="panel" aria-labelledby="panel-title">/);
});

test('what is typed in the note is handed to nothing that may send it to another machine', () => {
  // Some browsers check spelling on their maker's servers, and some offer to
  // translate or to complete what is typed. None of it is a request the page
  // makes, so no policy of the page can stop it. The note asks for none of it.
  const html = read('index.html');
  const note = /<input id="note"[^>]*>/.exec(html);
  assert.ok(note, 'the note is an input');
  for (const asked of ['spellcheck="false"', 'autocorrect="off"', 'autocapitalize="off"', 'autocomplete="off"']) {
    assert.ok(note[0].includes(asked), asked);
  }
  assert.match(html, /<html lang="en-GB" translate="no">/);
  assert.doesNotMatch(html, /spellcheck="true"/);
  const typed = [...html.matchAll(/<(?:input|textarea)[^>]*>/g)].filter((found) => !/type="checkbox"/.test(found[0]));
  assert.equal(typed.length, 1, 'the note is the only place a person types');
  assert.doesNotMatch(html, /contenteditable/);
});

test('the words under the note are the ones the design gives', () => {
  assert.equal(SAYS.noteHint, 'A note may be published. Write nothing about yourself or anyone else.');
  assert.ok(html.includes(`<p id="note-hint">${SAYS.noteHint}</p>`));
  assert.match(html, /<input id="note"[^>]*maxlength="500"[^>]*aria-describedby="note-hint"/);
});

// ---------------------------------------------------------------- the style sheet

test('the style sheet fetches nothing', () => {
  assert.doesNotMatch(css, /url\(|@import|@font-face/i);
});

test('nothing moves', () => {
  assert.doesNotMatch(css, /transition|animation|@keyframes|scroll-behavior/i);
});

test('no text is set smaller than 16 pixels', () => {
  const sizes = [...css.matchAll(/font(?:-size)?\s*:\s*([^;]+);/g)].map((match) => match[1]);
  assert.ok(sizes.length > 5);
  for (const value of sizes) {
    if (value.trim() === 'inherit') continue;
    const found = /(?:^|\s)([\d.]+)(rem|px|em|%)(?:\/|\s|$)/.exec(value);
    assert.ok(found, `a size this test can read: ${value}`);
    const [, number, unit] = found;
    const pixels = unit === 'px' ? Number(number) : unit === '%' ? (Number(number) / 100) * 16 : Number(number) * 16;
    assert.ok(pixels >= 16, value);
  }
  assert.doesNotMatch(css, /font-size\s*:\s*(small|smaller|x-small|xx-small)/);
});

test('the page never scrolls as a whole', () => {
  assert.match(css, /body\s*\{[^}]*height:\s*100vh;[^}]*overflow:\s*hidden;/);
  assert.match(css, /grid-template-columns:\s*minmax\(0, 1fr\) 22rem;/);
});

test('the question and the answers stay in view while what is known scrolls', () => {
  assert.match(css, /#side\s*\{[^}]*grid-template-rows:\s*minmax\(0, 1fr\) auto minmax\(0, max-content\);/);
  assert.match(css, /#known,\s*#ask\s*\{[^}]*overflow-y:\s*auto;/);
  const known = /<div id="known">([\s\S]*?)<\/div>\s*<p id="more" hidden>[^\n]*<\/p>\s*<div id="ask">([\s\S]*?)<\/div>\s*<\/aside>/.exec(html);
  assert.ok(known);
  for (const id of ['flags', 'lines', 'picks', 'moves']) assert.ok(known[1].includes(`id="${id}"`), id);
  for (const id of ['question', 'rule', 'answers', 'note', 'second']) assert.ok(known[2].includes(`id="${id}"`), id);
});

test('what is known keeps a floor where it is long, and the question gives way', () => {
  assert.match(css, /#side\.floor\s*\{[^}]*grid-template-rows:\s*minmax\(8rem, 1fr\) auto minmax\(0, max-content\);/);
});

test('a value of what is known has the width of the column, however long its label is', () => {
  // A label may be a publisher and the name of its file. In a column of its own such a
  // label left the value a few letters to the line, and one name took thirty pages to read.
  const lines = /#lines\s*\{([^}]*)\}/.exec(css);
  assert.ok(lines, 'the rows of what is known are styled');
  assert.doesNotMatch(lines[1], /grid|flex|column/, 'no column is kept for the labels');
  assert.match(css, /#lines dt\s*\{[^}]*float:\s*left;[^}]*clear:\s*left;/, 'a label begins the line of its value');
  assert.match(css, /#lines dt::after\s*\{[^}]*content:\s*":";/, 'a mark parts the label from the value');
  assert.match(css, /#lines dd\s*\{[^}]*overflow-wrap:\s*anywhere;/, 'a long id breaks, and is never cut');
});

test('what a person chooses and what they did stand over the rows of evidence, which are the longest', () => {
  const known = /<div id="known">([\s\S]*?)<\/div>/.exec(html)[1];
  const order = [...known.matchAll(/id="([a-z-]+)"/g)].map((match) => match[1]);
  assert.deepEqual(order, ['flags', 'picks', 'of', 'dispute', 'mine', 'others', 'moves', 'lines']);
});

test('what was saved and what went wrong are under the top line, where no fold hides them', () => {
  const status = /<\/header>\s*<div id="status">([\s\S]*?)<\/div>\s*<main /.exec(html);
  assert.ok(status, 'between the top line and the item');
  for (const id of ['trouble', 'said', 'warn']) assert.ok(status[1].includes(`id="${id}"`), id);
  assert.match(css, /#status\s*\{[^}]*grid-column:\s*1 \/ -1;[^}]*min-height:\s*3\.5rem;/);
  const side = /<aside id="side"[\s\S]*?<\/aside>/.exec(html)[0];
  for (const id of ['trouble', 'said', 'warn', 'title']) assert.ok(!side.includes(`id="${id}"`), `${id} is not in the column`);
});

test('the name of the item is in the page once, over the item', () => {
  assert.equal([...html.matchAll(/id="title"/g)].length, 1);
  assert.match(html, /<main id="item" tabindex="-1" aria-labelledby="title">\s*<h1 id="title"><\/h1>/);
  assert.doesNotMatch(html, /id="head"/);
});

test('every rule of the style sheet is closed, and styles something the page holds', () => {
  const bare = css.replace(/\/\*[\s\S]*?\*\//g, '');
  assert.equal([...bare.matchAll(/\{/g)].length, [...bare.matchAll(/\}/g)].length);
  const selectors = [...bare.matchAll(/(^|\})\s*([^{}@]+)\{/g)].map((match) => match[2]).join(' ');
  const script = read('desk.mjs');
  const ids = new Set([...selectors.matchAll(/#([a-z][a-z-]*)/g)].map((match) => match[1]));
  assert.ok(ids.size > 20);
  for (const id of ids) assert.ok(html.includes(`id="${id}"`), `#${id}`);
  const classes = new Set([...selectors.matchAll(/\.([a-z][a-z-]*)/g)].map((match) => match[1]));
  for (const name of classes) {
    const used = new RegExp(`class="[^"]*\\b${name}\\b`).test(html) || script.includes(`'${name}'`) || read('logic.mjs').includes(`'${name}'`);
    assert.ok(used, `.${name}`);
  }
});

test('an element that is hidden stays hidden whatever else styles it', () => {
  assert.match(css, /\[hidden\]\s*\{\s*display:\s*none\s*!important;\s*\}/);
});

function tokens(block) {
  return Object.fromEntries([...block.matchAll(/--([a-z-]+):\s*(#[0-9a-f]{3,6})\s*;/gi)].map((match) => [match[1], match[2]]));
}

const light = tokens(/:root\s*\{([^}]*)\}/.exec(css)[1]);
const dark = tokens(/prefers-color-scheme:\s*dark\)\s*\{\s*:root\s*\{([^}]*)\}/.exec(css)[1]);

test('the page follows the light or dark of the system, with every colour given for both', () => {
  assert.match(css, /color-scheme:\s*light dark;/);
  assert.deepEqual(Object.keys(dark).sort(), Object.keys(light).sort());
  assert.ok(Object.keys(light).length >= 15);
});

test('every colour used is one of the named ones', () => {
  const body = css.replace(/:root\s*\{[^}]*\}/g, '');
  assert.doesNotMatch(body, /#[0-9a-f]{3,8}\b/i);
  for (const [, name] of body.matchAll(/var\(--([a-z-]+)\)/g)) assert.ok(name in light, name);
});

const pairs = [
  ['ink', 'paper'],
  ['ink', 'panel'],
  ['ink', 'key'],
  ['soft', 'paper'],
  ['soft', 'panel'],
  ['mark-ink', 'mark'],
  ['stands-ink', 'stands'],
  ['trouble-ink', 'trouble'],
  ['made-up-ink', 'made-up'],
  ['real-ink', 'real'],
  ['unknown-ink', 'unknown'],
];

test('every text can be read on what is behind it, in daylight and in a dark room', () => {
  for (const [name, theme] of [['light', light], ['dark', dark]]) {
    for (const [ink, paper] of pairs) {
      const ratio = contrast(theme[ink], theme[paper]);
      assert.ok(ratio >= 7, `${ink} on ${paper}, ${name}: ${ratio.toFixed(2)}`);
    }
  }
});

test('the line round what has the keyboard can be seen', () => {
  for (const [name, theme] of [['light', light], ['dark', dark]]) {
    for (const paper of ['paper', 'panel']) {
      assert.ok(contrast(theme.focus, theme[paper]) >= 4.5, `${name}, on ${paper}`);
    }
  }
  assert.match(css, /:focus-visible\s*\{[^}]*outline:\s*3px solid var\(--focus\)/);
});

test('made-up and real are told apart by more than their words', () => {
  for (const theme of [light, dark]) {
    assert.notEqual(theme['made-up'], theme.real);
    assert.ok(contrast(theme['made-up'], theme.real) >= 3);
  }
});

// ---------------------------------------------------------------- the manual

const manual = read('README.md');

test('the manual gives every key on a line of its own, in the words the page uses', () => {
  for (const row of KEYS) {
    assert.ok(manual.includes(`| \`${row.key}\` | ${row.does} |`), `${row.key}: ${row.does}`);
  }
  const keys = /## The keys\n([\s\S]*?)\n## /.exec(manual)[1];
  const listed = [...keys.matchAll(/^\| `([^`]+)` \| /gm)].length;
  assert.equal(listed, KEYS.length);
});

test('the key that says a whole area is not known is in the list of keys', () => {
  const row = KEYS.find((one) => one.key === '7');
  assert.ok(row, 'the list of keys has a row for 7');
  assert.match(row.does, /^Ratings: /);
  assert.match(row.does, /undo takes them all back/);
});

test('every key in the manual that is one stroke does something', () => {
  const state = { ...start(), phase: 'ready', synthetic: true, hand: { cell: 'c', area: 'a' } };
  for (const key of ['s', 'u', 'n', 'f', 'j', 'g', 'q', 'p', '?', 'm']) {
    assert.ok(manual.includes(`| \`${key}\` |`), key);
    assert.notEqual(keyAction(state, { key }), null, key);
  }
  assert.notEqual(keyAction(state, { key: 'Escape' }), null);
});
