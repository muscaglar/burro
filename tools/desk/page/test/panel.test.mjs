// The panel: what its files hold, what each screen says, and what a press asks
// of the desk. Every name here is made up, and no browser is opened.

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { MOST_SHOWN, PARTS, SAYS, VIEWS, every, figure, found, hashOf, number, pathOf, pathTo, proposed, rebalance, routeOf, sameShares, sharesOf, textOf, titleOf, viewAdjust, viewLooked, viewMoved, viewRelabel, viewRename, viewWhatMoved } from '../panel-logic.mjs';
import { BANDS, PLAIN, areaAt, boxOf, fillOf, fit, holds, legendOf, ringsOf, toGround, toScreen } from '../panel-map.mjs';
import { boot } from '../panel.mjs';
import { contrast } from './support/colour.mjs';
import { PANEL, browser } from './support/dom.mjs';

const folder = new URL('../', import.meta.url);
const read = (name) => readFileSync(fileURLToPath(new URL(name, folder)), 'utf8');
const html = read('panel.html');
const css = read('panel.css');
const scripts = ['panel.mjs', 'panel-logic.mjs', 'panel-map.mjs'];

// ---------------------------------------------------------------- the files

test('no file of the panel names another host', () => {
  for (const name of ['panel.html', 'panel.css', ...scripts]) {
    const text = read(name);
    assert.doesNotMatch(text, /https?:\/\//i, name);
    assert.doesNotMatch(text, /["'(]\/\/[a-z0-9]/i, name);
    assert.doesNotMatch(text, /\bwss?:\/\//i, name);
  }
});

test('the panel loads its own style sheet and its own script, and links to the desk alone', () => {
  const loaded = [...html.matchAll(/\b(?:src|href|action|poster|data|srcset)\s*=\s*"([^"]*)"/gi)].map((match) => match[1]);
  for (const path of loaded) assert.match(path, /^(#\/[a-z]*|\/page\/(panel\.css|panel\.mjs|index\.html))$/, path);
  for (const tag of ['img', 'iframe', 'object', 'embed', 'video', 'audio', 'form', 'base']) {
    assert.doesNotMatch(html, new RegExp(`<${tag}[\\s>]`, 'i'), tag);
  }
});

test('the panel holds nothing a strict content security policy would refuse', () => {
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
    assert.doesNotMatch(text, /innerHTML|outerHTML|insertAdjacentHTML|document\.write|DOMParser|createContextualFragment/, name);
  }
});

test('no script of the panel keeps anything in the browser or sends anything but by fetch', () => {
  for (const name of scripts) {
    const text = read(name);
    assert.doesNotMatch(text, /localStorage|sessionStorage|indexedDB|document\.cookie|caches\.|serviceWorker/, name);
    assert.doesNotMatch(text, /sendBeacon|WebSocket|EventSource|XMLHttpRequest|RTCPeerConnection|window\.open|location\.(href|assign|replace)/, name);
  }
});

test('only the file that is the panel touches the screen or the network', () => {
  for (const name of ['panel-logic.mjs', 'panel-map.mjs']) {
    const text = read(name);
    assert.doesNotMatch(text, /\bdocument\b|\bwindow\b|\bfetch\b|\bDate\b|Math\.random|\bnavigator\b/, name);
    assert.doesNotMatch(text, /^import /m, name);
  }
});

test('the panel asks the desk only by a path that panel-logic.mjs built', () => {
  const text = read('panel.mjs');
  const asks = [...text.matchAll(/\bawait (?:read|write)\(([^,)]+)[,)]/g)].map((match) => match[1].trim());
  assert.ok(asks.length >= 4);
  for (const first of asks) assert.ok(first === 'path' || first.startsWith('pathOf(') || first.startsWith('pathTo('), first);
  assert.equal([...text.matchAll(/\bfetch\(/g)].length, 2, 'one call in ask, and one that hands the browser own fetch in');
});

test('what is typed at the panel is handed to nothing that may send it to another machine', () => {
  const typed = [...html.matchAll(/<(?:input|textarea)[^>]*>/g)].filter((one) => !/type="checkbox"/.test(one[0]));
  assert.equal(typed.length, 1, 'the reason is the only place of the page itself where a person types');
  for (const asked of ['spellcheck="false"', 'autocorrect="off"', 'autocapitalize="off"', 'autocomplete="off"', 'maxlength="500"']) {
    assert.ok(typed[0][0].includes(asked), asked);
  }
  assert.match(html, /<html lang="en-GB" translate="no">/);
  assert.doesNotMatch(html, /contenteditable/);
  assert.ok(html.includes(`<p id="why-hint">${SAYS.noteHint}</p>`));
});

test('the panel says first that nothing is to be decided until it has said which data it shows', () => {
  assert.match(html, /<title>The panel - Burro review desk<\/title>/);
  assert.match(html, /<p id="banner" class="banner unknown">[^<]*Decide nothing yet\.<\/p>/);
  assert.match(html, /<p id="trouble" role="alert"><\/p>/);
  assert.match(html, /<p id="said" role="status" aria-live="polite"><\/p>/);
});

test('the style sheet of the panel fetches nothing, moves nothing and sets no text under 16 pixels', () => {
  assert.doesNotMatch(css, /url\(|@import|@font-face/i);
  assert.doesNotMatch(css, /transition|animation|@keyframes|scroll-behavior/i);
  const sizes = [...css.matchAll(/font(?:-size)?\s*:\s*([^;]+);/g)].map((match) => match[1]);
  assert.ok(sizes.length >= 3);
  for (const value of sizes) {
    if (value.trim() === 'inherit') continue;
    const held = /(?:^|\s)([\d.]+)(rem|px|em|%)(?:\/|\s|$)/.exec(value);
    assert.ok(held, `a size this test can read: ${value}`);
    const pixels = held[2] === 'px' ? Number(held[1]) : held[2] === '%' ? (Number(held[1]) / 100) * 16 : Number(held[1]) * 16;
    assert.ok(pixels >= 16, value);
  }
});

test('the banner is as wide as the page, though a line of words is kept to a width that can be read', () => {
  // Seen in a browser, in a window 1440 wide: the banner stopped at 1120, short of the right edge.
  const rules = [...css.replace(/\/\*[\s\S]*?\*\//g, '').matchAll(/([^{}]+)\{([^{}]*)\}/g)].map(([, selector, block]) => [selector.trim(), block]);
  const of = (selector) => rules.filter(([found]) => found.split(',').map((one) => one.trim()).includes(selector));
  // A paragraph is kept to a width, and the banner is a paragraph.
  assert.ok(of('p').some(([, block]) => /max-width:\s*[\d.]+rem;/.test(block)));
  assert.match(html, /<p id="banner" class="banner [a-z-]+">/);
  // So the banner says that nothing keeps it, in the one rule that is its own.
  const banner = of('.banner');
  assert.equal(banner.length, 1);
  assert.match(banner[0][1], /max-width:\s*none;/);
  // No other rule that reaches the banner sets it a width.
  for (const [selector, block] of rules) {
    if (/banner/.test(selector) && selector !== '.banner') assert.doesNotMatch(block, /(^|[\s;])(max-)?width:/, selector);
  }
});

function tokens(block) {
  return Object.fromEntries([...block.matchAll(/--([a-z-]+):\s*(#[0-9a-f]{3,6})\s*;/gi)].map((match) => [match[1], match[2]]));
}

const light = tokens(/:root\s*\{([^}]*)\}/.exec(css)[1]);
const dark = tokens(/prefers-color-scheme:\s*dark\)\s*\{\s*:root\s*\{([^}]*)\}/.exec(css)[1]);

test('every colour of the panel is named, is given for light and for dark, and can be read', () => {
  assert.match(css, /color-scheme:\s*light dark;/);
  assert.deepEqual(Object.keys(dark).sort(), Object.keys(light).sort());
  const body = css.replace(/:root\s*\{[^}]*\}/g, '');
  assert.doesNotMatch(body, /#[0-9a-f]{3,8}\b/i);
  for (const [, name] of body.matchAll(/var\(--([a-z-]+)\)/g)) assert.ok(name in light, name);
  const pairs = [['ink', 'paper'], ['ink', 'panel'], ['ink', 'key'], ['soft', 'paper'], ['stands-ink', 'stands'], ['trouble-ink', 'trouble'], ['made-up-ink', 'made-up'], ['real-ink', 'real'], ['unknown-ink', 'unknown']];
  for (const [name, theme] of [['light', light], ['dark', dark]]) {
    for (const [ink, paper] of pairs) assert.ok(contrast(theme[ink], theme[paper]) >= 7, `${ink} on ${paper}, ${name}`);
    assert.ok(contrast(theme.focus, theme.paper) >= 4.5, `a link, ${name}`);
    assert.ok(contrast(theme['made-up'], theme.real) >= 3);
  }
  assert.match(css, /:focus-visible\s*\{[^}]*outline:\s*3px solid var\(--focus\)/);
});

test('the five colours of a band are told from each other and from the page, in light and in dark', () => {
  for (const mode of ['light', 'dark']) {
    const steps = BANDS[mode];
    assert.equal(steps.length, 5);
    assert.ok(contrast(steps[0], PLAIN[mode].paper) >= 2, `${mode}: the step beside the page`);
    for (let at = 1; at < steps.length; at += 1) {
      assert.ok(contrast(steps[at], steps[at - 1]) >= 1.25, `${mode}: band ${at} from band ${at + 1}`);
      assert.ok(contrast(steps[at], PLAIN[mode].paper) > contrast(steps[at - 1], PLAIN[mode].paper), `${mode}: a higher band stands further from the page`);
    }
    assert.ok(contrast(PLAIN[mode].ink, PLAIN[mode].paper) >= 7);
  }
  assert.deepEqual(legendOf({ fill: 'bands', bands: {} }, false).map((row) => row.words), ['Band 1', 'Band 2', 'Band 3', 'Band 4', 'Band 5', 'No band']);
});

// ---------------------------------------------------------------- where a screen is

test('an address names a screen, and an address that names none names the first', () => {
  assert.deepEqual(routeOf('#/area/syn-n0004'), { view: 'area', id: 'syn-n0004' });
  assert.deepEqual(routeOf('#/vibes'), { view: 'vibes', id: null });
  for (const hash of ['', '#', '#/', '#/nothing', '#/area', '#/area/a/b', '#/area/%E0%A4%A']) assert.deepEqual(routeOf(hash), { view: 'home', id: null }, hash);
  assert.equal(hashOf('area', 'syn-n0004'), '#/area/syn-n0004');
  assert.equal(hashOf('home'), '#/');
  assert.deepEqual(routeOf(hashOf('vibe', 'leafy')), { view: 'vibe', id: 'leafy' });
});

test('a word of an address is never a step into a folder of the desk', () => {
  assert.equal(pathOf({ view: 'area', id: '../state' }), '/api/panel/area/..%2Fstate');
  assert.equal(pathOf({ view: 'measure', id: 'a b?c#d' }), '/api/panel/measure/a%20b%3Fc%23d');
  assert.equal(pathOf({ view: 'vibes', id: null }), '/api/panel/home');
  assert.equal(pathOf({ view: 'flagged', id: null }), '/api/panel/flags');
  assert.equal(pathTo('takeBack'), '/api/panel/take-back');
  assert.equal(pathTo('state'), '/api/state');
});

// ---------------------------------------------------------------- how a figure is said

test('a figure is said with its unit, and a number that is not known is said as nothing', () => {
  assert.equal(number(1234567.04), '1,234,567');
  assert.equal(number(19.74), '19.7');
  assert.equal(number(-0.26), '-0.3');
  assert.equal(number(null), '');
  assert.equal(figure(400000, '£'), '£400,000');
  assert.equal(figure(12.5, '%'), '12.5%');
  assert.equal(figure(3, 'count'), '3');
  assert.equal(figure(19.7, 'per ha'), '19.7 per ha');
  assert.equal(figure(0, 'm'), '0 m');
  assert.equal(figure(null, 'm'), '');
});

// ---------------------------------------------------------------- the screens

const SOURCE = { id: 'synthetic', name: 'Synthetic test data', publisher: 'Burro' };
const FILE = { id: 'f-0123456789ab', name: 'made-up-air.csv', edition: 'made up', source: 'synthetic', retrieved_on: '2026-09-23' };
const AREA = {
  synthetic: true,
  area: { id: 'syn-n0004', name: 'Dulcimer Green', borough: 'Quillhaven', label: 'Quillhaven 004', state: 'draft', named_by: ['synthetic'], ranked: true, beside: [{ id: 'syn-n0006', name: 'Farrowmere', borough: 'Quillhaven' }] },
  figures: [{ measure: 'air_no2', label: 'Modelled annual mean nitrogen dioxide', value: 19.7, unit: 'µg/m³', percentile: 37.5, ranked_on: true, sources: [SOURCE], date: '2025', files: [FILE], method: 'Made up.', state: 'present', covered: 1 }],
  costs: [{ key: 'buy.flat', tenure: 'buy', segment: 'flat', median: 400000, lower_quartile: null, upper_quartile: null, sales: 41, since: '2023-01', unit: '£', sources: [SOURCE], date: '2026-08', files: [FILE], state: 'present' }],
  vibes: [
    { vibe: 'leafy', label: 'Leafy', low_end: null, high_end: null, band: 4, held: 100, rests_on_little: false, why: '', parts: [{ measure: 'land_gardens', label: 'Land that is residential garden', hundredths: 40, read: 'high', has_a_figure: true, percentile: 80 }] },
    { vibe: 'pace', label: 'Going out', low_end: 'Calm', high_end: 'Buzzy', band: null, held: 45, rests_on_little: false, why: 'It rests on 45 in 100 of its recipe here, and an area has a band from 60.', parts: [] },
  ],
  missing: [{ measure: 'cuisine_variety', label: 'Kinds of food nearby', why: 'This build does not work the measure out.' }],
  flags: [{ n: 1, on: '2026-10-06', by: 'r1', what: 'flag', of: 'figure/syn-n0004/air_no2', kind: 'figure', about: 'Modelled annual mean nitrogen dioxide', key: 'air_no2', area: { id: 'syn-n0004', name: 'Dulcimer Green', borough: 'Quillhaven' }, why: 'It looks too low.', mine: true }],
};

test('the screen of an area says every figure with its unit, its source, its date and its file', () => {
  const said = textOf(VIEWS.area(AREA));
  for (const words of ['Dulcimer Green, Quillhaven', 'Quillhaven 004', 'The name is a draft', 'Modelled annual mean nitrogen dioxide', '19.7 µg/m³', 'Burro', '2025', 'made-up-air.csv (made up)', '£400,000', '41 sales since 2023-01', 'Farrowmere']) {
    assert.ok(said.includes(words), words);
  }
});

test('the screen of an area says every vibe as a band, with the share of each part behind it', () => {
  const said = textOf(VIEWS.area(AREA));
  assert.ok(said.includes('4 of 5'));
  assert.ok(said.includes('40 in 100: Land that is residential garden, read from its high end. It has a figure.'));
  assert.ok(said.includes('No band'));
  assert.ok(said.includes('It rests on 45 in 100 of its recipe here'));
  // A vibe is said as a band, and never as a score or a percentage.
  assert.doesNotMatch(said, /37\.5|80%|percentile|score/i);
});

test('the screen of an area says what it has no figure for, and why', () => {
  const said = textOf(VIEWS.area(AREA));
  assert.ok(said.includes('No figure for: 1'));
  assert.ok(said.includes('Kinds of food nearby This build does not work the measure out.'));
});

test('a figure, a band, a name and a border can each be flagged in one press', () => {
  const flags = every(VIEWS.area(AREA), (node) => node.attrs.do && node.attrs.do.type === 'flag').map((node) => node.attrs.do);
  assert.deepEqual(
    flags.map((one) => one.of),
    ['name/syn-n0004', 'border/syn-n0004', 'figure/syn-n0004/air_no2', 'figure/syn-n0004/buy.flat', 'band/syn-n0004/leafy', 'band/syn-n0004/pace'],
  );
  // No press offers to leave a figure out: no build applies it yet.
  assert.ok(flags.every((one) => !('canLeaveOut' in one)));
  assert.ok(textOf(VIEWS.area(AREA)).includes('Flagged here'));
});

test('no screen of the panel has a box for a figure', () => {
  for (const trees of [VIEWS.area(AREA)]) {
    const typed = every(trees, (node) => ['input', 'textarea', 'select'].includes(node.tag));
    assert.deepEqual(typed, []);
  }
});

const MEASURE = {
  synthetic: true,
  measure: { id: 'air_no2', label: 'Modelled annual mean nitrogen dioxide', short_label: 'Cleaner air', unit: 'µg/m³', polarity: 'less', family: null, ranked_on: true, how: 'modelled', definition: 'Made up for testing.', date: '2025', sources: [SOURCE] },
  spread: { areas: 24, with_a_figure: 23, least: 8.1, lower_quartile: 14, median: 19.7, upper_quartile: 26, most: 41.5, bins: [{ from: 8.1, to: 24.8, areas: 15 }, { from: 24.8, to: 41.5, areas: 8 }] },
  highest: [{ id: 'syn-n0003', name: 'Cindermoor', borough: 'Quillhaven', value: 41.5 }],
  lowest: [{ id: 'syn-n0001', name: 'Alderwick', borough: 'Quillhaven', value: 8.1 }],
  missing: [{ id: 'syn-n0002', name: 'Brackenhythe', borough: 'Quillhaven', why: 'The publisher withheld the figure.' }],
  stands_out: [{ id: 'syn-n0003', name: 'Cindermoor', borough: 'Quillhaven', value: 41.5, why: 'far_from_the_areas_beside_it', beside: 3 }],
  flags: [],
};

test('the screen of a measure says its spread, its ends, its gaps and what stands out', () => {
  const said = textOf(VIEWS.measure(MEASURE));
  for (const words of ['23 of 24 areas have a figure', 'Least 8.1 µg/m³', 'median 19.7 µg/m³', 'most 41.5 µg/m³', 'Cindermoor Quillhaven 41.5 µg/m³', 'Alderwick Quillhaven 8.1 µg/m³', 'What stands out: 1', 'Far from the areas beside it', 'Areas with no figure: 1', 'The publisher withheld the figure.']) {
    assert.ok(said.includes(words), words);
  }
});

const VIBE = {
  synthetic: true,
  vibe: { id: 'pace', label: 'Going out', shape: 'scale', low_end: 'Calm', high_end: 'Buzzy', family: 'pace_food', meaning: 'How much there is to go out to', cannot_see: ['One street or one home. An area is many streets.', 'Opening hours.'], recipe: [{ measure: 'venue_evening_per_homes', label: 'Pubs and bars for each 1,000 homes', hundredths: 35, read: 'high', carried: true, counts_residents: false }], held: 100, needed: 60, placed: true },
  bands: { 'syn-n0001': 1, 'syn-n0003': 5, 'syn-n0004': null },
  counts: { 1: 1, 2: 0, 3: 0, 4: 0, 5: 1, none: 1 },
  highest: [{ id: 'syn-n0003', name: 'Cindermoor', borough: 'Quillhaven', band: 5 }],
  lowest: [{ id: 'syn-n0001', name: 'Alderwick', borough: 'Quillhaven', band: 1 }],
  follows: [{ what: 'homes_density', label: 'Homes per hectare', areas: 2, rank_correlation: 0.77 }, { what: 'distance_from_the_centre', label: 'Distance from the middle of the areas, in a straight line', areas: 2, rank_correlation: null }],
  rests_on_little: [{ id: 'syn-n0001', name: 'Alderwick', borough: 'Quillhaven', band: 1, held: 65 }],
  flags: [],
};

test('the screen of a vibe says its recipe, its bands, its ends and how closely it follows how built up a place is', () => {
  const trees = VIEWS.vibe(VIBE);
  const said = textOf(trees);
  for (const words of ['Going out', 'A scale, from Calm to Buzzy.', 'Opening hours.', 'Pubs and bars for each 1,000 homes 35 in 100', 'Band 5 1', 'No band 1', 'Cindermoor Quillhaven 5 of 5', 'Homes per hectare: 0.77, across 2 areas.', SAYS.follows, 'Bands that rest on little of the recipe: 1', '65 in 100']) {
    assert.ok(said.includes(words), words);
  }
  const map = every(trees, (node) => node.tag === 'canvas');
  assert.equal(map.length, 1);
  assert.deepEqual(map[0].attrs.draw, { fill: 'bands', bands: VIBE.bands });
});

const AREAS = {
  synthetic: true,
  areas: [
    { id: 'syn-n0001', name: 'Alderwick', borough: 'Quillhaven', label: 'Quillhaven 001', state: 'draft', centre: [0, 0] },
    { id: 'syn-n0004', name: 'Dulcimer Green', borough: 'Quillhaven', label: 'Quillhaven 004', state: 'checked', centre: [0.03, 0.02] },
    { id: 'syn-n0030', name: 'Tallowgate', borough: 'Marrowby', label: 'Marrowby 002', state: null, centre: [0.1, 0] },
  ],
};

test('an area is found by its name, by its borough or by its label, in any case', () => {
  assert.deepEqual(found(AREAS.areas, ' dulc ').map((area) => area.id), ['syn-n0004']);
  assert.deepEqual(found(AREAS.areas, 'MARROW').map((area) => area.id), ['syn-n0030']);
  assert.deepEqual(found(AREAS.areas, 'haven 001').map((area) => area.id), ['syn-n0001']);
  assert.equal(found(AREAS.areas, '').length, 3);
  assert.deepEqual(found(AREAS.areas, 'nowhere'), []);
  const said = textOf(VIEWS.areas(AREAS, { words: 'quill' }));
  assert.ok(said.includes('2 of 3 areas.'));
  assert.ok(!said.includes('Tallowgate'));
});

const HOME = {
  synthetic: true,
  reviewer: 'r1',
  banner: 'MADE-UP CITY. Nothing here is a real place.',
  served: { release_id: 'syn-2026-09-23-01', built_on: '2026-09-23', synthetic: true, preview: false, catalogue_version: 13, areas: 24, measures: 108, left_out: 0, vibes: [{ id: 'leafy', label: 'Leafy', held: 100, placed: true }, { id: 'village_feel', label: 'Village feel', held: 60, placed: false }] },
  waiting: [{ queue: 'names', title: 'Names', left: 40, total: 44 }],
  flagged: 2,
  built_with: 0,
  changed: [{ n: 3, on: '2026-10-06', by: 'r1', what: 'recipe', of: 'leafy', was: {}, now: {}, why: 'Gardens say most.', takes_back: null }],
};

test('the first screen says what is served, what waits for a person and what was changed', () => {
  const said = textOf(VIEWS.home(HOME));
  for (const words of ['Release syn-2026-09-23-01, built on 2026-09-23. The made-up city.', '24 areas. 108 measures, and 0 left out. 2 vibes, of which 1 place an area.', 'Names 40 44', '2 flagged', 'The shares of a recipe leafy r1 2026-10-06 Gardens say most.', SAYS.notBuilt]) {
    assert.ok(said.includes(words), words);
  }
  assert.ok(textOf(VIEWS.home({ ...HOME, changed: [] })).includes('The release was built with no file of changes. Nothing was changed.'));
  assert.ok(textOf(VIEWS.home({ ...HOME, built_with: 3, changed: [] })).includes('The release was built with the first 3 lines of your file of changes. Nothing was changed since.'));
  assert.ok(textOf(VIEWS.home({ ...HOME, built_with: null })).includes('a file of changes that is not the start of yours'));
  assert.equal(titleOf({ view: 'home', id: null }, HOME), 'What is served - The panel - Burro review desk');
  assert.equal(titleOf({ view: 'area', id: 'syn-n0004' }, AREA), 'Dulcimer Green - The panel - Burro review desk');
});

const HISTORY = {
  synthetic: true,
  history: [
    { n: 2, on: '2026-10-06', by: 'r1', what: 'take_back', of: 'leafy', was: null, now: null, why: 'It put the centre first.', takes_back: 1, stands: false, taken_back_by: null, mine: true },
    { n: 1, on: '2026-10-06', by: 'r1', what: 'recipe', of: 'leafy', was: { land_gardens: 40, land_woodland: 30, green_cover: 30 }, now: { land_gardens: 50, land_woodland: 25, green_cover: 25 }, why: 'Gardens say most.', takes_back: null, stands: false, taken_back_by: 2, mine: true },
    { n: 1, on: '2026-10-05', by: 'r2', what: 'flag', of: 'name/syn-n0004', kind: 'name', about: '', key: '', area: { id: 'syn-n0004', name: 'Dulcimer Green', borough: 'Quillhaven' }, was: null, now: null, why: 'Nobody calls it that.', takes_back: null, stands: true, taken_back_by: null, mine: false },
  ],
  differ: [{ what: 'recipe', of: 'leafy', said: [{ by: 'r1', now: { land_gardens: 50 }, why: 'Gardens say most.' }, { by: 'r2', now: { land_gardens: 30 }, why: 'Woods say most.' }], built: 'r1' }],
};

test('the history says of every change who, when, what it was, what it is and why, newest first', () => {
  const trees = VIEWS.history(HISTORY);
  const said = textOf(trees);
  for (const words of ['Taken back: line 1', 'land_gardens 40, land_woodland 30, green_cover 30', 'land_gardens 50, land_woodland 25, green_cover 25', 'Gardens say most.', 'Taken back by line 2', 'name: Dulcimer Green, Quillhaven', 'Nobody calls it that.', 'Stands']) {
    assert.ok(said.includes(words), words);
  }
  assert.ok(said.indexOf('It put the centre first.') < said.indexOf('Gardens say most.'));
  // A line of another reviewer's, and a line that was taken back, cannot be taken back here.
  const back = every(trees, (node) => node.attrs.do && node.attrs.do.type === 'takeBack').map((node) => node.attrs.do.n);
  assert.deepEqual(back, [2]);
});

test('two reviewers who differ are shown to each other, and whose change is built is said', () => {
  const said = textOf(VIEWS.history(HISTORY));
  assert.ok(said.includes('Where two reviewers differ: 1'));
  assert.ok(said.includes('r1: land_gardens 50. Gardens say most.'));
  assert.ok(said.includes('r2: land_gardens 30. Woods say most.'));
  assert.ok(said.includes('r1, the founder'));
});

// ---------------------------------------------------------------- the shares of a recipe

const SHARES = { school_primary_nearby: 40, play_space_proximity: 35, park_proximity: 25 };

function total(shares) {
  return Object.values(shares).reduce((sum, held) => sum + held, 0);
}

test('the shares of a recipe always come to 100, whichever is moved and however far', () => {
  for (const part of Object.keys(SHARES)) {
    for (let to = -20; to <= 120; to += 1) {
      const made = rebalance(SHARES, part, to, 1, 59);
      assert.equal(total(made), 100, `${part} to ${to}`);
      for (const held of Object.values(made)) assert.ok(Number.isInteger(held) && held >= 1 && held <= 59, `${part} to ${to}: ${held}`);
      assert.equal(made[part], Math.min(59, Math.max(1, to)), `${part} to ${to}`);
      assert.deepEqual(Object.keys(made), Object.keys(SHARES));
    }
  }
});

test('the parts that were not moved share what is left as they stood to each other', () => {
  assert.deepEqual(rebalance(SHARES, 'school_primary_nearby', 20, 1, 59), { school_primary_nearby: 20, play_space_proximity: 47, park_proximity: 33 });
  assert.deepEqual(rebalance(SHARES, 'school_primary_nearby', 40, 1, 59), SHARES);
  assert.deepEqual(rebalance(SHARES, 'park_proximity', 55, 1, 59), { school_primary_nearby: 24, play_space_proximity: 21, park_proximity: 55 });
  // A share that is not a number moves nothing, and a part the recipe does not hold is no part.
  assert.deepEqual(rebalance(SHARES, 'school_primary_nearby', Number.NaN, 1, 59), SHARES);
  assert.deepEqual(rebalance(SHARES, 'air_no2', 20, 1, 59), SHARES);
});

test('no part is pushed over the most a part may hold, or under the least', () => {
  // Two parts cannot make room for a third at 1: each would hold more than 59.
  const two = { a: 50, b: 50 };
  assert.deepEqual(rebalance(two, 'a', 10, 1, 59), { a: 41, b: 59 });
  // Beside a part that counts who lived there no part is over 40.
  const four = { households_dependent_children: 40, school_primary_nearby: 25, play_space_proximity: 20, park_proximity: 15 };
  for (let to = 0; to <= 100; to += 1) {
    const made = rebalance(four, 'park_proximity', to, 1, 40);
    assert.equal(total(made), 100);
    for (const held of Object.values(made)) assert.ok(held >= 1 && held <= 40, `to ${to}: ${held}`);
  }
  assert.equal(rebalance(four, 'households_dependent_children', 90, 1, 40).households_dependent_children, 40);
});

const ADJUST = {
  shares: [
    { measure: 'school_primary_nearby', label: 'State primary schools within 800 m in a straight line', hundredths: 40, read: 'high', carried: true, counts_residents: false },
    { measure: 'play_space_proximity', label: 'Straight-line distance to the nearest marked way into a play space', hundredths: 35, read: 'low', carried: true, counts_residents: false },
    { measure: 'park_proximity', label: 'Straight-line distance to the nearest marked way into a park of 2 ha or more', hundredths: 25, read: 'low', carried: true, counts_residents: false },
  ],
  least: 1,
  most: 59,
  names: { label: 'Family amenities', low_end: null, high_end: null },
  cannot_see: ['Catchments.'],
  as_served: true,
};
const FAMILY = { ...VIBE, vibe: { ...VIBE.vibe, id: 'family_amenities', label: 'Family amenities', shape: 'one_way', low_end: null, high_end: null }, adjust: ADJUST };
const NOW = { school_primary_nearby: 20, play_space_proximity: 47, park_proximity: 33 };
const AREA_MOVED = { id: 'syn-n0003', name: 'Cindermoor', borough: 'Quillhaven', from: 3, to: 5 };
const MOVED = {
  synthetic: true,
  what: 'recipe',
  of: 'family_amenities',
  was: SHARES,
  now: NOW,
  seen: '0123456789ab',
  bands: { areas: 24, change_band: 7, up: 4, down: 3, placed_before: 24, placed_after: 24, steps: [{ from: 3, to: 5, areas: 1 }, { from: 2, to: 1, areas: 3 }], rise: [AREA_MOVED], fall: [{ id: 'syn-n0001', name: 'Alderwick', borough: 'Quillhaven', from: 2, to: 1 }] },
  searches: [
    {
      id: 'a_family_buying_a_house',
      name: 'A family, buying a house',
      says: 'Family amenities, parks close by and quiet streets, to buy a terraced house.',
      read_as: 'Three vibes, each asked for by name, and a budget that is a guide.',
      before: { first: [{ id: 'syn-n0001', name: 'Alderwick', borough: 'Quillhaven' }, { id: 'syn-n0003', name: 'Cindermoor', borough: 'Quillhaven' }], ranked: 22, left_out: 2, notes: [] },
      after: { first: [{ id: 'syn-n0003', name: 'Cindermoor', borough: 'Quillhaven' }, { id: 'syn-n0001', name: 'Alderwick', borough: 'Quillhaven' }], ranked: 22, left_out: 2, notes: ['Village feel is not in this release, so the search is ranked without it.'] },
      same: false,
    },
  ],
};

test('a recipe has a slider for each part, which starts from what stands', () => {
  const trees = viewAdjust(FAMILY);
  const sliders = every(trees, (node) => node.tag === 'input' && node.attrs.type === 'range');
  assert.deepEqual(sliders.map((node) => [node.attrs.id, node.attrs.value, node.attrs.min, node.attrs.max, node.attrs.do.part]), [
    ['share-school_primary_nearby', 40, 1, 59, 'school_primary_nearby'],
    ['share-play_space_proximity', 35, 1, 59, 'play_space_proximity'],
    ['share-park_proximity', 25, 1, 59, 'park_proximity'],
  ]);
  const said = textOf(trees);
  assert.ok(said.includes('they always come to 100'));
  assert.ok(said.includes('No part is added, taken out or turned round here.'));
  // Until a share is moved there is nothing to look at, and nothing to keep.
  const buttons = Object.fromEntries(every(trees, (node) => node.tag === 'button').map((node) => [node.attrs.id, node.attrs.disabled]));
  assert.deepEqual(buttons, { look: true, reset: true });
  assert.deepEqual(sharesOf(ADJUST), SHARES);
  assert.ok(sameShares(SHARES, { ...SHARES }) && !sameShares(SHARES, NOW));
});

test('nothing is kept that was not looked at: the box for the reason is there only after the preview of those shares', () => {
  const moved = viewAdjust(FAMILY, { adjust: { of: 'family_amenities', shares: NOW, found: null, why: '', trouble: '' } });
  assert.ok(textOf(moved).includes(SAYS.previewFirst));
  assert.deepEqual(every(moved, (node) => node.attrs.id === 'keep'), []);
  const looked = viewAdjust(FAMILY, { adjust: { of: 'family_amenities', shares: NOW, found: MOVED, why: '', trouble: '' } });
  assert.equal(every(looked, (node) => node.attrs.id === 'keep').length, 1);
  assert.ok(textOf(looked).includes(SAYS.notBuilt));
  // A share moved after the preview was looked at: what was looked at is of other shares.
  const after = viewAdjust(FAMILY, { adjust: { of: 'family_amenities', shares: { ...NOW, school_primary_nearby: 21, play_space_proximity: 46 }, found: MOVED, why: '', trouble: '' } });
  assert.deepEqual(every(after, (node) => node.attrs.id === 'keep'), []);
  // What was moved on the screen of another vibe is not of this one.
  const other = viewAdjust(FAMILY, { adjust: { of: 'leafy', shares: NOW, found: MOVED, why: '', trouble: '' } });
  assert.deepEqual(every(other, (node) => node.attrs.type === 'range').map((node) => node.attrs.value), [40, 35, 25]);
});

test('what would move is said: how many areas change band, which rise and fall most, and three searches', () => {
  const said = textOf(viewMoved(MOVED));
  for (const words of ['7 of 24 areas change band: 4 go up, and 3 go down.', '3 5 1', 'Cindermoor Quillhaven 3 5', 'Alderwick Quillhaven 2 1', 'A family, buying a house', 'Family amenities, parks close by and quiet streets, to buy a terraced house.', 'Village feel is not in this release', 'The first ten differ.', '1 Alderwick, Quillhaven Cindermoor, Quillhaven', '2 Cindermoor, Quillhaven Alderwick, Quillhaven']) {
    assert.ok(said.includes(words), words);
  }
  // An area is said by its band, and never by a score.
  assert.doesNotMatch(said, /score|percentile|%/i);
});

// ---------------------------------------------------------------- a name

const PACE = { ...VIBE, adjust: { shares: [], least: 1, most: 59, names: { label: 'Going out', low_end: 'Calm', high_end: 'Buzzy' }, cannot_see: ['Opening hours.'], as_served: true } };

function asksOf(trees) {
  return every(trees, (node) => node.attrs.do && node.attrs.do.type === 'propose').map((node) => node.attrs.do);
}

test('the name of a vibe and of its two ends, and what it cannot see, are each looked at before they are kept', () => {
  const trees = viewRename(PACE);
  const boxes = Object.fromEntries(every(trees, (node) => node.tag === 'input' || node.tag === 'textarea').map((node) => [node.attrs.id, node.attrs.value]));
  assert.deepEqual(boxes, { 'name-label': 'Going out', 'name-low': 'Calm', 'name-high': 'Buzzy', 'cannot-see': 'Opening hours.' });
  const values = { 'name-label': ' Nights out ', 'name-low': 'Sleepy', 'name-high': 'Busy', 'cannot-see': 'Opening hours.\n\n  Whether a place is open late. \n' };
  assert.deepEqual(asksOf(trees).map((ask) => proposed(ask, values)), [
    { what: 'name', of: 'pace', now: { label: 'Nights out', low_end: 'Sleepy', high_end: 'Busy' } },
    { what: 'cannot_see', of: 'pace', now: ['Opening hours.', 'Whether a place is open late.'] },
  ]);
  const said = textOf(trees);
  assert.match(said, /Every vibe says this first, and it is not changed here:\s+One street or one home\. An area is many streets\./);
  assert.ok(said.includes('A line that names the census or recorded crime is kept.'));
});

test('a vibe of one way has no ends to name', () => {
  const trees = viewRename({ ...FAMILY, vibe: { ...FAMILY.vibe, cannot_see: ['One street or one home.'] } });
  assert.deepEqual(every(trees, (node) => node.tag === 'input').map((node) => node.attrs.id), ['name-label']);
  assert.deepEqual(proposed(asksOf(trees)[0], { 'name-label': 'For families' }), { what: 'name', of: 'family_amenities', now: { label: 'For families', low_end: null, high_end: null } });
});

test('the two labels of a measure are changed, but for a measure that counts who lived somewhere', () => {
  const adjust = { labels: { label: 'Modelled annual mean nitrogen dioxide', short_label: 'Cleaner air' }, may: true, as_served: true };
  const trees = viewRelabel({ ...MEASURE, adjust });
  assert.deepEqual(proposed(asksOf(trees)[0], { 'label-long': 'Nitrogen dioxide in the air', 'label-short': 'Nitrogen dioxide' }), { what: 'label', of: 'air_no2', now: { label: 'Nitrogen dioxide in the air', short_label: 'Nitrogen dioxide' } });
  const counted = viewRelabel({ ...MEASURE, adjust: { ...adjust, may: false } });
  assert.deepEqual(every(counted, (node) => node.tag === 'input' || node.tag === 'button'), []);
  assert.ok(textOf(counted).includes('It counts who lived somewhere, so it keeps the name core gives it'));
  assert.ok(textOf(VIEWS.measure({ ...MEASURE, adjust })).includes('Its label'));
  assert.deepEqual(viewRelabel(MEASURE), []);
});

// ---------------------------------------------------------------- the numbers set by judgement

test('the numbers set by judgement are listed with what each is today, and no box changes one', () => {
  const data = { synthetic: true, says: 'Each number is core\'s own.', groups: [{ title: 'A firm budget', numbers: [{ id: 'firm_budget_margin', says: 'An area is left out where its middle price is over a firm budget by more than this.', value: 25, unit: '%', where: 'FIRM_BUDGET_MARGIN_PERCENT in packages/core/src/burro_core/rank.py', changed_by: 'A change to core, in code, with its tests.' }] }] };
  const trees = VIEWS.numbers(data);
  const said = textOf(trees);
  for (const words of ['The numbers set by judgement', 'A firm budget', '25 %', 'FIRM_BUDGET_MARGIN_PERCENT', 'A change to core, in code, with its tests.']) assert.ok(said.includes(words), words);
  assert.deepEqual(every(trees, (node) => ['input', 'select', 'textarea', 'button'].includes(node.tag)), []);
  assert.equal(pathOf(routeOf('#/numbers')), '/api/panel/numbers');
});

// ---------------------------------------------------------------- the table of brands

const LIDL = { key: 'lidl', name: 'Lidl', kind: 'grocer', tier: 'value', wikidata: ['Q151954'], spellings: ['Lidl'], on_the_founders_table: true, named_by_core: true, changed: false };
const BRANDS = {
  synthetic: true,
  kinds: [{ id: 'grocer', label: 'Grocers' }, { id: 'gym', label: 'Gyms' }, { id: 'coffee', label: 'Coffee' }],
  tiers: [{ id: 'premium', label: 'Premium' }, { id: 'mid', label: 'Mid-range' }, { id: 'value', label: 'Value' }],
  read_in: 'overture-places 2026-09-23.0',
  chains: [LIDL, { key: 'gildcrest', name: 'Gildcrest', kind: 'coffee', tier: 'premium', wikidata: [], spellings: ['Gildcrest'], on_the_founders_table: true, named_by_core: false, changed: true }],
  taken_out: [{ key: 'waitrose', name: 'Waitrose', kind: 'grocer', tier: 'premium', wikidata: ['Q771734'], spellings: ['Waitrose'] }],
  says: 'What this moves is known only once it is built: the panel holds no file of places.',
};
const LIDL_ROW = { name: 'Lidl', kind: 'grocer', tier: 'value', wikidata: ['Q151954'], spellings: ['Lidl'] };

test('the table of brands says each chain with its kind, its tier and how the file writes it', () => {
  const said = textOf(VIEWS.brands(BRANDS));
  for (const words of ['Lidl Grocers Value Lidl Yes', 'Gildcrest Coffee Premium, which you changed Gildcrest No: it is counted in its tier', 'Taken out', 'Waitrose Grocers Premium', 'It says nothing of who shops there.', BRANDS.says, 'Add a chain']) {
    assert.ok(said.includes(words), words);
  }
});

test('a chain is moved, taken out, put back or added by one press, which is looked at first', () => {
  const asks = every(VIEWS.brands(BRANDS), (node) => node.attrs.do && node.attrs.do.type === 'propose').map((node) => node.attrs.do);
  const values = { 'tier-lidl': 'premium', 'tier-gildcrest': 'premium', 'new-key': ' planet ', 'new-name': 'Planet', 'new-kind': 'grocer', 'new-tier': 'premium', 'new-spellings': 'Planet ; Planet Food;', 'new-wikidata': '' };
  assert.deepEqual(asks.map((ask) => proposed(ask, values)), [
    { what: 'brand', of: 'lidl', now: { ...LIDL_ROW, tier: 'premium' } },
    { what: 'brand', of: 'lidl', now: null },
    { what: 'brand', of: 'gildcrest', now: { name: 'Gildcrest', kind: 'coffee', tier: 'premium', wikidata: [], spellings: ['Gildcrest'] } },
    { what: 'brand', of: 'gildcrest', now: null },
    { what: 'brand', of: 'waitrose', now: { name: 'Waitrose', kind: 'grocer', tier: 'premium', wikidata: ['Q771734'], spellings: ['Waitrose'] } },
    { what: 'brand', of: 'planet', now: { name: 'Planet', kind: 'grocer', tier: 'premium', wikidata: [], spellings: ['Planet', 'Planet Food'] } },
  ]);
  // A chain that is added is written first as it is named, whatever else it is written as.
  const add = asks[asks.length - 1];
  assert.deepEqual(proposed(add, { ...values, 'new-spellings': '' }).now.spellings, ['Planet']);
  assert.deepEqual(proposed(add, { ...values, 'new-spellings': 'Planet Food' }).now.spellings, ['Planet', 'Planet Food']);
  assert.ok(textOf(VIEWS.brands(BRANDS)).includes('One shop is no chain, and the name of a person is none.'));
});

test('what was looked at says what stood, what would stand and what a build works out again', () => {
  const found = { what: 'brand', of: 'lidl', was: LIDL_ROW, now: { ...LIDL_ROW, tier: 'premium' }, seen: '0123456789ab', worked_out_again: ['Premium grocers within 800 m of home', 'Mix of brands'] };
  const said = textOf(viewLooked(found));
  for (const words of ['tier value', 'tier premium', 'A build works these measures out again:', 'Premium grocers within 800 m of home', 'known only once it is built', SAYS.notBuilt]) assert.ok(said.includes(words), words);
  assert.ok(textOf(viewLooked({ ...found, now: null })).includes('Nothing: it is taken out'));
  assert.ok(textOf(viewLooked({ ...found, was: null })).includes('Nothing: it is not on the table'));
  assert.ok(textOf(viewLooked({ ...found, needs: 'A build adds a chain only where the file shows it.' })).includes('A build adds a chain only where the file shows it.'));
});

// ---------------------------------------------------------------- the map

const SQUARE = { type: 'Polygon', coordinates: [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]], [[0.5, 0.5], [1, 0.5], [1, 1], [0.5, 1], [0.5, 0.5]]] };
const TWO = { type: 'MultiPolygon', coordinates: [[[[3, 0], [4, 0], [4, 1], [3, 1], [3, 0]]], [[[5, 0], [6, 0], [6, 1], [5, 1], [5, 0]]]] };
const OUTLINES = { 'syn-n0001': SQUARE, 'syn-n0002': TWO };

// ---------------------------------------------------------------- what moved between two builds

const PLACE = (id, name) => ({ id, name, borough: 'Quillhaven' });
const FIRST_TEN = (names) => ({ first: names.map((name, at) => PLACE(`syn-n000${at + 1}`, name)), ranked: 24, left_out: 0, notes: ['Village feel is not in this release, so the search is ranked without it.'] });
const WHAT_MOVED = {
  synthetic: true,
  counts: { areas: 24 },
  moved: {
    before: { release_id: 'syn-2026-09-23-01', built_at: '2026-09-23T00:00:00Z', commit: null, synthetic: true, preview: false, catalogue_version: 13, areas: 24, measures: 107, vibes: 14 },
    after: { release_id: 'syn-2026-10-02-01', built_at: '2026-10-02T09:00:00Z', commit: null, synthetic: true, preview: false, catalogue_version: 14, areas: 24, measures: 108, vibes: 14 },
    catalogue: {
      before: 13,
      after: 14,
      measures: [{ id: 'air_no2', label: 'Modelled annual mean nitrogen dioxide', names: [{ what: 'label', was: 'Nitrogen dioxide, as it was', now: 'Modelled annual mean nitrogen dioxide' }] }],
      vibes: [
        {
          id: 'homes', label: 'Houses or flats',
          parts_came: [{ id: 'private_outdoor_space', label: 'Addresses with private outdoor space', share: 25, reading: 'low' }],
          parts_went: [{ id: 'homes_post2000', label: 'Homes built since 2000', share: 20, reading: 'high' }],
          shares: [{ id: 'homes_flats', label: 'Flats', was: 45, now: 40 }],
          names: [{ what: 'label', was: 'Homes', now: 'Houses or flats' }, { what: 'low_end', was: 'Mostly houses', now: 'Houses' }],
          rough: { was: false, now: false },
        },
        { id: 'village_feel', label: 'Village feel', parts_came: [], parts_went: [], shares: [], names: [], rough: { was: false, now: true } },
        { id: 'leafy', label: 'Leafy', parts_came: [], parts_went: [], shares: [], names: [], rough: { was: true, now: false } },
      ],
    },
    areas: {
      same: 23,
      came: [PLACE('syn-n0024', 'Yarrowfield')],
      went: [PLACE('syn-n0023', 'Wrenbury')],
      renamed: [{ ...PLACE('syn-n0004', 'Dulcimer Green'), was: 'Quillhaven 004', was_in: 'Quillhaven' }],
      redrawn: [PLACE('syn-n0006', 'Farrowmere')],
      moved_most: [{ ...PLACE('syn-n0003', 'Cindermoor'), bands: 3, vibes: 2, figures: 4 }],
    },
    measures: {
      same: 107,
      came: [{ id: 'private_outdoor_space', label: 'Addresses with private outdoor space', unit: '%', with_a_figure: 23 }],
      went: [],
      moved: [
        {
          id: 'air_no2', label: 'Modelled annual mean nitrogen dioxide', unit: 'µg/m³', dated: { was: '2024', now: '2025' },
          areas: 23, changed: 7, up: 5, down: 2, gained: 1, lost: 0, middle: 1.2, most: 7.3,
          moved_most: ['Cindermoor', 'Alderwick', 'Brackenhythe', 'Dulcimer Green', 'Farrowmere', 'Gorsefield', 'Harrowdene'].map((name, at) => ({ ...PLACE(`syn-n00${at}`, name), was: 10 + at, now: 17.3 + at, by: 7.3 })),
        },
      ],
    },
    vibes: {
      same: 14,
      came: [],
      went: [],
      moved: [{ id: 'homes', label: 'Houses or flats', areas: 23, changed: 4, up: 3, down: 1, gained: 0, lost: 2, by_bands: [{ by: -1, areas: 1 }, { by: 1, areas: 2 }, { by: 2, areas: 1 }], recipe_changed: true, moved_most: [{ ...PLACE('syn-n0003', 'Cindermoor'), was: 2, now: 4 }] }],
    },
    costs: [{ tenure: 'buy', segment: 'flat', unit: '£', areas: 23, changed: 3, up: 3, down: 0, gained: 0, lost: 0, middle: 5000, most: 12000, moved_most: [] }],
    files: {
      compared: true,
      same: 86,
      changed: [{ was: { source: 'synthetic', list: 'made-up', item: 'grid', file_id: 'f-0123456789ab', sha256: 'a', edition: '2024', period: '2024', retrieved_on: '2026-09-23' }, now: { source: 'synthetic', list: 'made-up', item: 'grid', file_id: 'f-ba9876543210', sha256: 'b', edition: '2025', period: '2025', retrieved_on: '2026-10-01' } }],
      came: [{ source: 'synthetic', list: 'made-up', item: 'outlines', file_id: 'f-111111111111', sha256: 'c', edition: 'last changed 2025-06-19', period: '2025-06-19', retrieved_on: '2026-10-01' }],
      went: [{ name: 'gazetteer/areas.csv', sha256: 'd' }],
    },
    searches: [
      { id: 'a_family_buying_a_house', name: 'A family, buying a house', read_as: 'Three vibes, each asked for by name.', before: FIRST_TEN(['Alderwick', 'Cindermoor']), after: FIRST_TEN(['Cindermoor', 'Alderwick']), same: false, kept: 2, came: 0, went: 0, reordered: 2 },
      { id: 'nights_out_well_connected', name: 'Nights out, and well connected', read_as: 'Four vibes.', before: FIRST_TEN(['Alderwick']), after: FIRST_TEN(['Alderwick']), same: true, kept: 1, came: 0, went: 0, reordered: 0 },
    ],
  },
};

test('what moved has a screen of its own, which the desk is asked for by one path', () => {
  assert.deepEqual(routeOf('#/moved'), { view: 'moved', id: null });
  assert.equal(pathOf({ view: 'moved', id: null }), '/api/panel/moved');
  assert.deepEqual(PARTS[1], ['moved', 'What moved']);
  assert.match(html, /<a href="#\/moved">What moved<\/a>/);
  assert.equal(titleOf({ view: 'moved', id: null }, WHAT_MOVED), 'What moved - The panel - Burro review desk');
});

test('with no other release named, the screen says how to name one and nothing else', () => {
  const says = 'No other release was named. Start the desk with the release that is served as well.';
  assert.equal(textOf(VIEWS.moved({ synthetic: true, moved: null, says })), `What moved ${says}`);
});

test('the screen of what moved says what came and went, and how far each measure and each vibe moved', () => {
  const said = textOf(viewWhatMoved(WHAT_MOVED));
  for (const words of [
    'Between syn-2026-09-23-01 and syn-2026-10-02-01, which is the release that is shown.',
    'syn-2026-10-02-01 2026-10-02 The made-up city 24 108 14',
    'Areas: 1 came, and 1 went',
    '23 areas are in both. 1 bear another name, and 1 another outline.',
    'Yarrowfield Quillhaven',
    'Wrenbury Quillhaven',
    'Quillhaven 004, Quillhaven Dulcimer Green Quillhaven',
    'Cindermoor Quillhaven 3 2 4',
    'Measures: 1 came, 0 went, and 1 moved',
    'Addresses with private outdoor space private_outdoor_space',
    '7 of 23 areas changed: 5 up, and 2 down. 1 gained a figure, and 0 lost one. Those that changed moved by 1.2 µg/m³ in the middle, and by 7.3 µg/m³ at most.',
    'It was of 2024, and is of 2025.',
    'Cindermoor Quillhaven 10 µg/m³ 17.3 µg/m³',
    'Vibes: 0 came, 0 went, and 1 moved',
    '4 of 23 areas changed band: 3 up, and 1 down. 0 gained a band, and 2 lost one. The release carries another recipe, name or line of it.',
    'Down 1 1',
    'Up 2 1',
    'Cindermoor Quillhaven 2 4',
    'What a home sells for: 1 kinds of home moved',
    'flat to buy 3 of 23 areas changed: 3 up, and 0 down.',
    'by £5,000 in the middle, and by £12,000 at most',
    'The files behind the builds: 1 changed, 1 came, and 1 went',
    '86 inputs are the same file in both.',
    'synthetic made-up grid 2024 2024 2025 2025',
    'synthetic made-up outlines last changed 2025-06-19 2025-06-19',
    'gazetteer/areas.csv',
    'The first ten areas of 2 searches, before and after',
    'The first ten differ: 2 stayed, 0 came and 0 went, and 2 of those that stayed stand at another place.',
    '1 Alderwick, Quillhaven Cindermoor, Quillhaven',
    'The first ten are the same, in the same order.',
    'Village feel is not in this release, so the search is ranked without it.',
  ]) {
    assert.ok(said.includes(words), words);
  }
});

test('the table of the two builds says the catalogue of each', () => {
  const said = textOf(viewWhatMoved(WHAT_MOVED));
  assert.ok(said.includes('Release Built on Kind Areas Measures Vibes Catalogue'));
  assert.ok(said.includes('syn-2026-09-23-01 2026-09-23 The made-up city 24 107 14 13'));
  assert.ok(said.includes('syn-2026-10-02-01 2026-10-02 The made-up city 24 108 14 14'));
});

test('the screen of what moved says what came and went of the catalogue itself', () => {
  const rough = { village_feel: { label: 'Rough guide', why: 'Of the areas it puts highest, about half read as villages to people.' } };
  const said = textOf(viewWhatMoved({ ...WHAT_MOVED, rough }));
  for (const words of [
    'The catalogue: version 13 before, and version 14 after',
    'Measures: 1 came, and 0 went. Vibes: 0 came, and 0 went. Each is named below.',
    'Names and labels that changed: 3',
    'Modelled annual mean nitrogen dioxide air_no2 Its label Nitrogen dioxide, as it was Modelled annual mean nitrogen dioxide',
    'Houses or flats homes Its label Homes Houses or flats',
    'Houses or flats homes The name of its low end Mostly houses Houses',
    'Houses or flats: its recipe',
    // A part that came had no share, and one that went has none: its cell is empty.
    'Addresses with private outdoor space private_outdoor_space  25 Came, read from its low end',
    'Homes built since 2000 homes_post2000 20  Went, read from its high end',
    'Flats homes_flats 45 40 Its share changed',
    'Village feel: its recipe Rough guide. Of the areas it puts highest, about half read as villages to people. Village feel became a rough guide. No part of its recipe came, went or changed its share.',
    'Leafy: its recipe Leafy is no longer a rough guide.',
  ]) {
    assert.ok(said.includes(words), words);
  }
  // It stands before the areas, the figures and the bands: it is why they moved.
  assert.ok(said.indexOf('The catalogue: version 13') < said.indexOf('Areas: 1 came, and 1 went'));
});

test('a measure and a vibe of the catalogue that changed each open their own screen', () => {
  const links = every(viewWhatMoved(WHAT_MOVED), (node) => node.tag === 'a').map((node) => `${node.attrs.href} ${textOf(node)}`);
  for (const link of ['#/measure/air_no2 Modelled annual mean nitrogen dioxide', '#/vibe/homes Houses or flats', '#/vibe/homes Houses or flats: its recipe', '#/vibe/village_feel Village feel: its recipe']) {
    assert.ok(links.includes(link), link);
  }
});

test('two builds of one catalogue say that nothing of it changed', () => {
  const still = {
    ...WHAT_MOVED.moved,
    after: { ...WHAT_MOVED.moved.after, catalogue_version: 13 },
    catalogue: { before: 13, after: 13, measures: [], vibes: [] },
    measures: { same: 108, came: [], went: [], moved: [] },
    vibes: { same: 14, came: [], went: [], moved: [] },
  };
  const said = textOf(viewWhatMoved({ synthetic: true, moved: still }));
  assert.ok(said.includes('The catalogue: version 13 in both Nothing of the catalogue changed between the two.'));
  assert.ok(!said.includes('Names and labels that changed'));
  // A measure that came is of the catalogue, whatever its version.
  const came = textOf(viewWhatMoved({ synthetic: true, moved: { ...still, measures: WHAT_MOVED.moved.measures } }));
  assert.ok(came.includes('The catalogue: version 13 in both Measures: 1 came, and 0 went.'));
});

test('what a search was ranked without says on which of the two releases', () => {
  const gone = 'Village feel is not in this release, so the search is ranked without it.';
  const other = 'Quiet streets is not in this release, so the search is ranked without it.';
  const search = { ...WHAT_MOVED.moved.searches[0], before: { ...FIRST_TEN(['Alderwick']), notes: [gone, other] }, after: { ...FIRST_TEN(['Alderwick']), notes: [gone, 'The release names no place.'] } };
  const said = textOf(viewWhatMoved({ synthetic: true, moved: { ...WHAT_MOVED.moved, searches: [search] } }));
  assert.ok(said.includes(`${gone} Before: ${other} After: The release names no place.`));
  assert.ok(!said.includes(`Before: ${gone}`) && !said.includes(`After: ${gone}`));
});

test('of the areas that moved most on a measure, the first five are shown', () => {
  const tables = every(viewWhatMoved(WHAT_MOVED), (node) => node.tag === 'table');
  const air = tables.find((table) => textOf(table).includes('17.3 µg/m³'));
  assert.equal(MOST_SHOWN, 5);
  assert.equal(every(air, (node) => node.tag === 'tr').length, 1 + MOST_SHOWN);
  assert.ok(!textOf(air).includes('Gorsefield'));
});

test('an area, a measure and a vibe that moved each open their own screen', () => {
  const links = every(viewWhatMoved(WHAT_MOVED), (node) => node.tag === 'a').map((node) => node.attrs.href);
  for (const href of ['#/area/syn-n0024', '#/measure/air_no2', '#/vibe/homes']) assert.ok(links.includes(href), href);
  // An area that went is in no release that is shown, so it opens nothing.
  assert.ok(!links.includes('#/area/syn-n0023'));
});

test('nothing on the screen of what moved is a press or a box, and it says what approves a build', () => {
  const trees = viewWhatMoved(WHAT_MOVED);
  assert.deepEqual(every(trees, (node) => ['button', 'input', 'textarea', 'select'].includes(node.tag) || node.attrs.do), []);
  assert.ok(textOf(trees).includes('Nothing here approves a build. To approve one is to commit its lock.'));
});

test('a made-up release says that no file was compared, and a build that moved nothing says so', () => {
  const still = {
    ...WHAT_MOVED.moved,
    areas: { same: 24, came: [], went: [], renamed: [], redrawn: [], moved_most: [] },
    measures: { same: 108, came: [], went: [], moved: [] },
    vibes: { same: 14, came: [], went: [], moved: [] },
    costs: [],
    files: { compared: false, same: 0, changed: [], came: [], went: [] },
    searches: [],
  };
  const said = textOf(viewWhatMoved({ synthetic: true, moved: still }));
  for (const words of ['No area moved.', 'No figure of a measure that both carry changed.', 'No area changed band on a vibe that both carry.', 'No price changed.', 'A made-up release has no lock, so no file was compared.']) {
    assert.ok(said.includes(words), words);
  }
});

test('a point is laid on the map and found again where it was', () => {
  const box = boxOf(OUTLINES);
  assert.deepEqual(box, [0, 0, 6, 2]);
  const view = fit(box, 800, 600);
  for (const point of [[0, 0], [6, 2], [3.3, 1.1]]) {
    const back = toGround(view, toScreen(view, point));
    assert.ok(Math.abs(back[0] - point[0]) < 1e-9 && Math.abs(back[1] - point[1]) < 1e-9);
  }
  const [left, top] = toScreen(view, [0, 2]);
  const [right, bottom] = toScreen(view, [6, 0]);
  assert.ok(left > 7.99 && top > 7.99 && right < 792.01 && bottom < 592.01, 'the whole of it is in view');
  assert.ok(top < bottom, 'north is up');
  assert.equal(fit(null, 800, 600), null);
  assert.equal(fit(box, 10, 10), null);
});

test('the area a press is in is found, and a press in a hole or in the sea finds none', () => {
  assert.equal(areaAt(OUTLINES, [1.5, 1.5]), 'syn-n0001');
  assert.equal(areaAt(OUTLINES, [0.75, 0.75]), null);
  assert.equal(areaAt(OUTLINES, [5.5, 0.5]), 'syn-n0002');
  assert.equal(areaAt(OUTLINES, [4.5, 0.5]), null);
  assert.equal(holds(SQUARE, [9, 9]), false);
  assert.equal(ringsOf(TWO).length, 2);
  assert.deepEqual(ringsOf({ type: 'Point', coordinates: [0, 0] }), []);
});

test('an area is drawn in the colour of its band, and an area with no band in none of the five', () => {
  const draw = { fill: 'bands', bands: { a: 1, b: 5, c: null, d: 9 } };
  assert.equal(fillOf(draw, 'a', false), BANDS.light[0]);
  assert.equal(fillOf(draw, 'b', true), BANDS.dark[4]);
  for (const id of ['c', 'd', 'e']) assert.equal(fillOf(draw, id, false), PLAIN.light.none);
  assert.equal(fillOf({ fill: 'found', ids: ['a'] }, 'a', false), PLAIN.light.found);
  assert.equal(fillOf({ fill: 'found', ids: ['a'] }, 'b', false), PLAIN.light.none);
  assert.equal(fillOf({ fill: 'found', ids: [] }, 'b', false), PLAIN.light.none);
});

// ---------------------------------------------------------------- the panel at a stand-in for the desk

function desk(answers) {
  const asked = [];
  const fetch = async (path, init) => {
    asked.push({ path, method: init.method, body: init.body ? JSON.parse(init.body) : null, token: init.headers['X-Desk-Token'] || null });
    const held = answers[`${init.method} ${path}`];
    const out = typeof held === 'function' ? held(asked[asked.length - 1]) : held;
    if (out === undefined) return { ok: false, status: 404, json: async () => ({ error: 'not_found', message: 'The desk holds nothing by that name.', synthetic: true }) };
    return { ok: out.status === undefined || out.status < 400, status: out.status || 200, json: async () => out.body || out };
  };
  return { asked, fetch };
}

const STATE = { desk: 1, reviewer: 'r1', token: 'made-up-token', banner: 'MADE-UP CITY. Nothing here is a real place.', synthetic: true };

async function opened(answers, hash = '') {
  const held = desk({ 'GET /api/state': STATE, 'GET /api/panel/home': HOME, 'GET /api/panel/outlines': { synthetic: true, outlines: OUTLINES }, ...answers });
  const page = browser(held.fetch, { html: PANEL, hash });
  const panel = boot(page.env);
  await panel.started;
  await page.settle();
  return { page, panel, asked: held.asked };
}

test('the panel says which data it shows before anything else, and then what is served', async () => {
  const { page } = await opened({});
  assert.equal(page.text('banner'), 'MADE-UP CITY. Nothing here is a real place.');
  assert.equal(page.$('banner').className, 'banner made-up');
  assert.equal(page.text('who'), 'You are r1.');
  assert.ok(page.text('main').includes('What is served today'));
  assert.equal(page.document.title, 'What is served - The panel - Burro review desk');
});

test('the panel says real data in another colour, and says what went wrong in the desk own words', async () => {
  const real = { ...STATE, synthetic: false, banner: 'REAL DATA FOR LONDON. A draft that nobody has checked. What you decide here is built.' };
  const { page } = await opened({ 'GET /api/state': real, 'GET /api/panel/home': { status: 404, body: { error: 'not_found', message: 'The panel is not open.', synthetic: false } } });
  assert.equal(page.$('banner').className, 'banner real');
  assert.equal(page.text('trouble'), 'The panel is not open.');
});

test('a press on Flag asks why, and the flag is sent with the reason and the token', async () => {
  const flagged = { synthetic: true, line: { n: 1, what: 'flag', of: 'figure/syn-n0004/air_no2' }, flags: [] };
  const { page, asked } = await opened({ 'GET /api/panel/area/syn-n0004': AREA, 'POST /api/panel/flag': flagged }, '#/area/syn-n0004');
  assert.ok(page.text('main').includes('Dulcimer Green, Quillhaven'));
  const figure = page.$('main').find((node) => node.tagName === 'BUTTON' && node.parent.tagName === 'TD' && node.parent.parent.textContent.includes('19.7'));
  figure.click();
  assert.equal(page.$('box').open, true);
  assert.equal(page.text('box-of'), 'Modelled annual mean nitrogen dioxide, of Dulcimer Green');
  // With no reason nothing is sent.
  page.$('box-yes').click();
  await page.settle();
  assert.equal(page.text('box-trouble'), SAYS.needsReason);
  assert.equal(asked.filter((one) => one.method === 'POST').length, 0);
  page.$('why').value = ' It looks too low. ';
  page.$('box-yes').click();
  await page.settle();
  const sent = asked.find((one) => one.method === 'POST');
  assert.deepEqual([sent.path, sent.body, sent.token], ['/api/panel/flag', { of: 'figure/syn-n0004/air_no2', why: 'It looks too low.', leave_out: false }, 'made-up-token']);
  assert.equal(page.$('box').open, false);
  assert.equal(page.text('said'), 'Flagged: Modelled annual mean nitrogen dioxide, of Dulcimer Green. It is line 1 of your file of changes.');
});

test('what the desk refuses is said in the box, and the box stays open with the reason in it', async () => {
  const refusal = { status: 400, body: { error: 'bad_request', message: 'The release holds no such figure, band, name or border to flag.', synthetic: true } };
  const { page } = await opened({ 'GET /api/panel/area/syn-n0004': AREA, 'POST /api/panel/flag': refusal }, '#/area/syn-n0004');
  page.$('main').find((node) => node.tagName === 'BUTTON').click();
  page.$('why').value = 'Nobody calls it that.';
  page.$('box-yes').click();
  await page.settle();
  assert.equal(page.text('box-trouble'), refusal.body.message);
  assert.equal(page.$('box').open, true);
  assert.equal(page.$('why').value, 'Nobody calls it that.');
});

test('a line of the history is taken back with a reason, and the history is read again', async () => {
  const back = { synthetic: true, line: { n: 3, what: 'take_back', takes_back: 2 }, history: [] };
  const { page, asked } = await opened({ 'GET /api/panel/history': HISTORY, 'POST /api/panel/take-back': back }, '#/history');
  page.$('main').find((node) => node.tagName === 'BUTTON').click();
  assert.equal(page.text('box-title'), 'Take back');
  page.$('why').value = 'It was right after all.';
  page.$('box-yes').click();
  await page.settle();
  const sent = asked.find((one) => one.method === 'POST');
  assert.deepEqual([sent.path, sent.body], ['/api/panel/take-back', { n: 2, why: 'It was right after all.' }]);
  assert.equal(asked.filter((one) => one.path === '/api/panel/history').length, 2);
});

test('the map of a vibe is drawn from the outlines, and a press on an area opens it', async () => {
  const { page } = await opened({ 'GET /api/panel/vibe/pace': VIBE }, '#/vibe/pace');
  const map = page.$('main').find((node) => node.tagName === 'CANVAS');
  assert.ok(map, 'the screen of a vibe holds a map');
  const drawn = page.calls.map((call) => call[0]);
  for (const step of ['beginPath', 'moveTo', 'lineTo', 'closePath', 'fill', 'stroke', 'fillText']) assert.ok(drawn.includes(step), step);
  const fills = page.calls.filter((call) => call[0] === 'set' && call[1] === 'fillStyle').map((call) => call[2]);
  assert.ok(fills.includes(BANDS.light[0]), 'an area in band 1 is drawn in the colour of band 1');
  // A press in the middle of the first square, clear of its hole.
  const view = fit(boxOf(OUTLINES), map.clientWidth * 2, map.clientHeight * 2);
  const [x, y] = toScreen(view, [1.5, 1.5]);
  map.fire('click', { clientX: x / 2, clientY: y / 2 });
  assert.equal(page.location.hash, '#/area/syn-n0001');
});

test('what is typed to find an area stays in its box while the list under it changes', async () => {
  const { page } = await opened({ 'GET /api/panel/areas': AREAS }, '#/areas');
  const box = page.$('main').find((node) => node.id === 'find');
  box.value = 'marrow';
  box.fire('input');
  await page.settle();
  const again = page.$('main').find((node) => node.id === 'find');
  assert.equal(again.value, 'marrow');
  assert.equal(page.document.activeElement, again);
  assert.ok(page.text('main').includes('1 of 3 areas.'));
  assert.ok(page.text('main').includes('Tallowgate') && !page.text('main').includes('Alderwick'));
});

test('a screen that the desk does not hold says so, and shows nothing of the screen before', async () => {
  const { page } = await opened({ 'GET /api/panel/area/syn-n0004': AREA }, '#/area/syn-n0004');
  await page.go('#/area/syn-n9999');
  assert.equal(page.text('trouble'), 'The desk holds nothing by that name.');
  assert.ok(!page.text('main').includes('Dulcimer Green'));
});

test('a share is moved, what would move is looked at, and it is kept with its reason', async () => {
  const kept = { synthetic: true, line: { n: 1, what: 'recipe', of: 'family_amenities' }, history: [] };
  const { page, asked } = await opened({ 'GET /api/panel/vibe/family_amenities': FAMILY, 'POST /api/panel/preview': MOVED, 'POST /api/panel/keep': kept }, '#/vibe/family_amenities');
  const find = (id) => page.$('main').find((node) => node.id === id);
  assert.equal(find('look').disabled, true);
  const slider = find('share-school_primary_nearby');
  slider.value = '20';
  slider.fire('input');
  await page.settle();
  assert.deepEqual(['share-school_primary_nearby', 'share-play_space_proximity', 'share-park_proximity'].map((id) => find(id).value), [20, 47, 33]);
  assert.equal(page.document.activeElement, find('share-school_primary_nearby'), 'the keyboard stays on the slider that was moved');
  assert.equal(find('keep'), null, 'nothing can be kept before it is looked at');
  find('look').click();
  await page.settle();
  const looked = asked.find((one) => one.path === '/api/panel/preview');
  assert.deepEqual(looked.body, { what: 'recipe', of: 'family_amenities', now: NOW });
  assert.ok(page.text('main').includes('7 of 24 areas change band'));
  // With no reason nothing is sent.
  find('keep').click();
  await page.settle();
  assert.equal(page.text('main').includes(SAYS.needsReason), true);
  assert.equal(asked.filter((one) => one.path === '/api/panel/keep').length, 0);
  const why = find('keep-why');
  why.value = 'A park says more of a week than a count of schools.';
  why.fire('input');
  find('keep').click();
  await page.settle();
  const sent = asked.find((one) => one.path === '/api/panel/keep');
  assert.deepEqual(sent.body, { what: 'recipe', of: 'family_amenities', now: NOW, why: 'A park says more of a week than a count of schools.', seen: '0123456789ab' });
  assert.equal(sent.token, 'made-up-token');
  assert.ok(page.text('said').startsWith('Kept: the shares of Family amenities. It is line 1 of your file of changes.'));
  assert.ok(page.text('said').includes('Nothing that is served has changed'));
});

test('a recipe the desk refuses is said beside the sliders, and nothing of it is kept', async () => {
  const refusal = { status: 400, body: { error: 'bad_request', message: 'A recipe comes to 100.', synthetic: true } };
  const { page } = await opened({ 'GET /api/panel/vibe/family_amenities': FAMILY, 'POST /api/panel/preview': refusal }, '#/vibe/family_amenities');
  const find = (id) => page.$('main').find((node) => node.id === id);
  find('share-park_proximity').value = '50';
  find('share-park_proximity').fire('input');
  find('look').click();
  await page.settle();
  assert.equal(find('adjust-trouble').textContent, 'A recipe comes to 100.');
  assert.equal(find('keep'), null);
});

test('what was moved on one screen is dropped when the screen is left', async () => {
  const { page } = await opened({ 'GET /api/panel/vibe/family_amenities': FAMILY, 'GET /api/panel/vibe/pace': VIBE }, '#/vibe/family_amenities');
  const find = (id) => page.$('main').find((node) => node.id === id);
  find('share-park_proximity').value = '50';
  find('share-park_proximity').fire('input');
  await page.go('#/vibe/pace');
  await page.go('#/vibe/family_amenities');
  assert.equal(find('share-park_proximity').value, 25);
});

test('a chain is moved to another tier: it is looked at, the reason is asked for, and it is kept', async () => {
  const looked = { synthetic: true, what: 'brand', of: 'lidl', was: LIDL_ROW, now: { ...LIDL_ROW, tier: 'premium' }, seen: 'abcdef012345', worked_out_again: ['Mix of brands'] };
  const kept = { synthetic: true, line: { n: 4, what: 'brand', of: 'lidl' }, history: [] };
  const { page, asked } = await opened({ 'GET /api/panel/brands': BRANDS, 'POST /api/panel/preview': looked, 'POST /api/panel/keep': kept }, '#/brands');
  const find = (id) => page.$('main').find((node) => node.id === id);
  assert.equal(find('tier-lidl').value, 'value', 'the list of tiers starts at the tier the chain is of');
  find('tier-lidl').value = 'premium';
  page.$('main').find((node) => node.tagName === 'BUTTON' && node.textContent === 'Move').click();
  await page.settle();
  assert.deepEqual(asked.find((one) => one.path === '/api/panel/preview').body, { what: 'brand', of: 'lidl', now: { ...LIDL_ROW, tier: 'premium' } });
  assert.equal(page.$('box').open, true);
  assert.equal(page.text('box-title'), 'Keep');
  assert.ok(page.text('box-more').includes('Mix of brands'));
  page.$('why').value = 'It charges what the premium grocers charge.';
  page.$('box-yes').click();
  await page.settle();
  assert.deepEqual(asked.find((one) => one.path === '/api/panel/keep').body, { what: 'brand', of: 'lidl', now: { ...LIDL_ROW, tier: 'premium' }, why: 'It charges what the premium grocers charge.', seen: 'abcdef012345' });
  assert.equal(page.text('said'), 'Kept: Lidl: to another tier. It is line 4 of your file of changes. Nothing that is served has changed: a build is made from the file.');
});

test('a row the desk refuses is said on the screen, and no reason is asked for', async () => {
  const refusal = { status: 400, body: { error: 'bad_request', message: 'A row of the table holds a name, a kind, a tier.', synthetic: true } };
  const { page } = await opened({ 'GET /api/panel/brands': BRANDS, 'POST /api/panel/preview': refusal }, '#/brands');
  page.$('main').find((node) => node.tagName === 'BUTTON' && node.textContent === 'Add').click();
  await page.settle();
  assert.equal(page.$('main').find((node) => node.id === 'propose-trouble').textContent, refusal.body.message);
  assert.equal(page.$('box').open, false);
});

// What the desk gives of a vibe that is a rough guide: core's label, and core's sentence.
const ROUGH = { label: 'Rough guide', why: 'Of the areas it puts highest, about half read as villages to people, and it takes some busy main roads and some grand inner streets for villages.' };
const SAID_ROUGH = `${ROUGH.label}. ${ROUGH.why}`;
const timesSaid = (trees) => textOf(trees).split(SAID_ROUGH).length - 1;

test('a vibe that is a rough guide says so beside its name wherever the panel names it', () => {
  const home = { ...HOME, served: { ...HOME.served, vibes: [{ id: 'leafy', label: 'Leafy', held: 100, placed: true, rough: null }, { id: 'village_feel', label: 'Village feel', held: 100, placed: true, rough: ROUGH }] } };
  const area = { ...AREA, vibes: [{ ...AREA.vibes[0], rough: null }, { ...AREA.vibes[0], vibe: 'village_feel', label: 'Village feel', rough: ROUGH }] };
  const vibe = { ...VIBE, vibe: { ...VIBE.vibe, id: 'village_feel', label: 'Village feel', shape: 'one_way', rough: ROUGH } };
  const moved = { ...WHAT_MOVED, rough: { village_feel: ROUGH }, moved: { ...WHAT_MOVED.moved, vibes: { ...WHAT_MOVED.moved.vibes, came: [{ id: 'village_feel', label: 'Village feel' }], moved: [...WHAT_MOVED.moved.vibes.moved, { ...WHAT_MOVED.moved.vibes.moved[0], id: 'village_feel', label: 'Village feel' }] } } };
  // Once where every vibe is listed, once in the audit of an area, once on its own screen,
  // and on the screen of what moved once where the catalogue changed of it, once where it
  // came and once where its bands moved.
  assert.equal(timesSaid(VIEWS.vibes(home)), 1);
  assert.equal(timesSaid(VIEWS.area(area)), 1);
  assert.equal(timesSaid(VIEWS.vibe(vibe)), 1);
  assert.equal(timesSaid(viewWhatMoved(moved)), 3);
  // It follows the name of its vibe, and is drawn: nothing is pressed to read it.
  for (const trees of [VIEWS.vibes(home), VIEWS.area(area), VIEWS.vibe(vibe), viewWhatMoved(moved)]) {
    const said = textOf(trees);
    assert.ok(said.includes(`Village feel ${SAID_ROUGH}`), said.slice(0, 80));
    const drawn = every(trees, (node) => node.tag === 'p' && textOf(node) === SAID_ROUGH);
    assert.ok(drawn.length >= 1);
    for (const node of drawn) assert.equal(node.attrs.do, undefined);
    assert.equal(every(trees, (node) => node.tag === 'details').length, 0);
  }
});

test('nothing is said of a vibe that is as sure as the rest, or where the desk says nothing', () => {
  for (const trees of [VIEWS.home(HOME), VIEWS.vibes(HOME), VIEWS.area(AREA), VIEWS.vibe(VIBE), viewWhatMoved(WHAT_MOVED)]) {
    assert.ok(!textOf(trees).includes(ROUGH.label));
  }
});
