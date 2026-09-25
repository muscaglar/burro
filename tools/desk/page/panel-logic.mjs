// What the panel shows and says: plain functions, with no browser in them.
//
// A screen is worked out here as a tree of plain objects, from what the desk
// answered. panel.mjs copies the tree to the page, as text and never as markup,
// and carries out what a press asks for. So what a person reads can be tested
// with no browser.
//
// A node is { tag, attrs, children }. A child is a node or a string. The
// attribute `do` is what a press of the node asks for, as a plain object.

export const SAYS = {
  loading: 'Loading. Which data this is will be said here. Decide nothing yet.',
  notBuilt: 'Nothing here changes what is served. A build does, and a build is made on purpose.',
  noteHint: 'A reason may be published. Write nothing about yourself or anyone else.',
  noBand: 'No band',
  follows: 'A vibe that is only a map of how built up a place is says little.',
  needsReason: 'Say why first. A change is kept with its reason.',
  previewFirst: 'See what would move first. Nothing is kept that was not looked at.',
};

export const PARTS = [
  ['home', 'What is served'],
  ['moved', 'What moved'],
  ['areas', 'Areas'],
  ['measures', 'Measures'],
  ['vibes', 'Vibes'],
  ['brands', 'Brands'],
  ['numbers', 'Numbers'],
  ['flagged', 'Flagged'],
  ['history', 'History'],
];

// What each kind of line is called, where a person reads it.
export const WHAT = {
  recipe: 'The shares of a recipe',
  name: 'The name of a vibe',
  cannot_see: 'What a vibe cannot see',
  label: 'The label of a measure',
  brand: 'The table of brands',
  number: 'A number set by judgement',
  flag: 'Flagged',
  leave_out: 'Left out of the next build',
  take_back: 'Taken back',
};

const WHY_STANDS_OUT = {
  far_from_the_areas_beside_it: 'Far from the areas beside it',
  nought_where_the_areas_beside_it_are_not: 'At nought, where the areas beside it are not',
};

const STATES = {
  present: 'Covers the area',
  partial: 'Covers part of the area',
  unknown: 'Its evidence is not held',
};

// ---------------------------------------------------------------- the tree

export function h(tag, attrs, ...children) {
  const kept = children.flat(Infinity).filter((child) => child !== null && child !== undefined && child !== false && child !== '');
  return { tag, attrs: attrs || {}, children: kept.map((child) => (typeof child === 'object' ? child : String(child))) };
}

// The trees of a screen, one after another, with nothing where a part of it is not shown.
export function screen(...trees) {
  return trees.flat(Infinity).filter((tree) => tree !== null && tree !== undefined && tree !== false && tree !== '');
}

// Every word of a tree, as a person would read it, a space between two nodes.
export function textOf(tree) {
  if (typeof tree === 'string') return tree;
  if (Array.isArray(tree)) return screen(tree).map(textOf).join(' ');
  return tree.children.map(textOf).join(' ');
}

export function every(tree, test, found = []) {
  if (Array.isArray(tree)) {
    for (const one of screen(tree)) every(one, test, found);
  } else if (typeof tree === 'object') {
    if (test(tree)) found.push(tree);
    for (const child of tree.children) every(child, test, found);
  }
  return found;
}

// ---------------------------------------------------------------- where a screen is

function part(word) {
  return encodeURIComponent(String(word));
}

const ONE = { area: 'area', measure: 'measure', vibe: 'vibe' };
const LISTS = { home: 'home', moved: 'moved', areas: 'areas', measures: 'measures', vibes: 'home', flagged: 'flags', history: 'history', brands: 'brands', numbers: 'numbers' };

// The screen an address names. An address that names none names the first screen.
export function routeOf(hash) {
  const words = String(hash || '').replace(/^#\/?/, '').split('/').filter((word) => word !== '');
  let id = null;
  try {
    id = words.length === 2 ? decodeURIComponent(words[1]) : null;
  } catch {
    id = null;
  }
  if (words.length === 2 && ONE[words[0]] && id) return { view: words[0], id };
  if (words.length === 1 && LISTS[words[0]]) return { view: words[0], id: null };
  return { view: 'home', id: null };
}

export function hashOf(view, id) {
  if (view === 'home') return '#/';
  return id === null || id === undefined ? `#/${view}` : `#/${view}/${part(id)}`;
}

// The path the desk is asked by, for a screen. It is built here and nowhere else.
export function pathOf(route) {
  if (ONE[route.view]) return `/api/panel/${ONE[route.view]}/${part(route.id)}`;
  return `/api/panel/${LISTS[route.view] || 'home'}`;
}

const WRITES = { flag: 'flag', takeBack: 'take-back', outlines: 'outlines', preview: 'preview', keep: 'keep' };

// The path of what is asked for by its name: what the desk is, the outlines, and each
// thing that is written.
export function pathTo(what) {
  return what === 'state' ? '/api/state' : `/api/panel/${WRITES[what]}`;
}

// ---------------------------------------------------------------- how a figure is said

function grouped(whole) {
  return String(whole).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// A number as it is read: whole where it is whole, and to one place where it is not.
export function number(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '';
  const rounded = Math.round(value * 10) / 10;
  const [whole, rest] = Math.abs(rounded).toFixed(1).split('.');
  return `${rounded < 0 ? '-' : ''}${grouped(whole)}${rest === '0' ? '' : `.${rest}`}`;
}

export function figure(value, unit) {
  if (value === null || value === undefined) return '';
  if (unit === '£') return `£${number(value)}`;
  if (unit === '%') return `${number(value)}%`;
  return unit && unit !== 'count' ? `${number(value)} ${unit}` : number(value);
}

export function bandOf(row) {
  if (row.band === null || row.band === undefined) return SAYS.noBand;
  const ends = row.low_end && row.high_end ? `, from ${row.low_end} at 1 to ${row.high_end} at 5` : '';
  return `${row.band} of 5${ends}`;
}

function sources(row) {
  return (row.sources || []).map((source) => source.publisher).filter((name, at, names) => names.indexOf(name) === at).join('; ');
}

function files(row) {
  return (row.files || []).map((file) => `${file.name} (${file.edition})`).join('; ');
}

// ---------------------------------------------------------------- small pieces

function link(view, id, words) {
  return h('a', { href: hashOf(view, id) }, words);
}

function table(head, rows, empty) {
  if (!rows.length) return h('p', { class: 'none' }, empty);
  return h(
    'table',
    {},
    h('thead', {}, h('tr', {}, head.map((words) => h('th', { scope: 'col' }, words)))),
    h('tbody', {}, rows.map((cells) => h('tr', {}, cells.map((cell) => h('td', {}, cell))))),
  );
}

function place(row) {
  return [link('area', row.id, row.name), row.borough];
}

// The press that flags a thing. A figure may also be left out of the next build.
export function flagButton(of, words) {
  return h('button', { type: 'button', class: 'flag', do: { type: 'flag', of, words } }, 'Flag');
}

function flagsOf(data) {
  const rows = (data.flags || []).map((flag) => [WHAT[flag.what], flag.area ? flag.area.name : '', flag.about || flag.kind, flag.by, flag.on, flag.why]);
  if (!rows.length) return [];
  return [h('h2', {}, 'Flagged here'), table(['What', 'Area', 'Of', 'By', 'On', 'Why'], rows, '')];
}

// ---------------------------------------------------------------- the first screen

// What a vibe that is a rough guide says of itself: its label and the sentence that says
// why, as the desk gives them. They are core's words. It is drawn beside the name of the
// vibe wherever the panel names one, and is behind no press. Nothing for a vibe that is as
// sure as the rest.
export function roughWords(told) {
  return told ? h('p', { class: 'rule' }, `${told.label}. ${told.why}`) : null;
}

function servedWords(served) {
  const which = served.synthetic ? 'The made-up city.' : served.preview ? 'A preview: it is not finished.' : 'A finished release.';
  const placed = served.vibes.filter((vibe) => vibe.placed).length;
  return [
    `Release ${served.release_id}, built on ${served.built_on}. ${which}`,
    `${number(served.areas)} areas. ${number(served.measures)} measures, and ${number(served.left_out)} left out. ` +
      `${served.vibes.length} vibes, of which ${placed} place an area.`,
  ];
}

function builtWords(built) {
  if (built === null) return 'The release was built with a file of changes that is not the start of yours. Every change of yours that stands is listed.';
  if (built > 0) return `The release was built with the first ${built === 1 ? 'line' : `${number(built)} lines`} of your file of changes.`;
  return 'The release was built with no file of changes.';
}

export function viewHome(data) {
  const served = data.served;
  const waiting = data.waiting.map((row) => [h('a', { href: '/page/index.html' }, row.title), number(row.left), number(row.total)]);
  const changed = data.changed.map((line) => [line.what === 'take_back' ? `${WHAT.take_back}: line ${line.takes_back}` : WHAT[line.what], ofWords(line), line.by, line.on, line.why]);
  return [
    h('h1', {}, 'What is served today'),
    servedWords(served).map((words) => h('p', {}, words)),
    h('h2', {}, 'Waiting for a person'),
    table(['Queue', 'Left', 'Of'], waiting, 'No queue is filled.'),
    h('p', {}, link('flagged', null, `${number(data.flagged)} flagged, for a person to look at again.`)),
    h('h2', {}, 'Changed, and not yet built'),
    h('p', {}, builtWords(data.built_with)),
    table(['What', 'Of', 'By', 'On', 'Why'], changed, data.built_with ? 'Nothing was changed since.' : 'Nothing was changed.'),
    h('p', { class: 'rule' }, SAYS.notBuilt),
  ];
}

export function viewVibes(data) {
  const rows = data.served.vibes.map((vibe) => [
    [link('vibe', vibe.id, vibe.label), roughWords(vibe.rough)],
    `${vibe.held} in 100`,
    vibe.placed ? 'Yes' : 'No area: it waits on a measure',
  ]);
  return [h('h1', {}, 'Vibes'), table(['Vibe', 'Of its recipe held', 'Places an area'], rows, 'The release carries no vibe.')];
}

export function viewMeasures(data) {
  const rows = data.measures.map((row) => [link('measure', row.id, row.label), row.unit, row.ranked_on ? 'Ranked on' : 'Shown, and never ranked on']);
  return [h('h1', {}, 'Measures'), table(['Measure', 'Unit', 'Use'], rows, 'The release carries no measure.')];
}

// ---------------------------------------------------------------- areas

function folded(words) {
  return String(words || '').trim().toLowerCase();
}

// The areas a person finds by what they typed: a name, a borough or a label.
export function found(areas, words) {
  const wanted = folded(words);
  if (wanted === '') return areas;
  return areas.filter((area) => [area.name, area.borough, area.label].some((held) => folded(held).includes(wanted)));
}

export const SHOWN = 60;

export function viewAreas(data, state = {}) {
  const matches = found(data.areas, state.words);
  const rows = matches.slice(0, SHOWN).map((area) => [link('area', area.id, area.name), area.borough, area.label, area.state === 'checked' ? 'Checked by a person' : area.state === 'draft' ? 'A draft' : 'Its label']);
  const more = matches.length > SHOWN ? ` The first ${SHOWN} are listed.` : '';
  return [
    h('h1', {}, 'Areas'),
    h(
      'p',
      { class: 'field' },
      h('label', { for: 'find' }, 'Find an area by its name or its borough'),
      h('input', { id: 'find', type: 'search', value: state.words || '', autocomplete: 'off', spellcheck: 'false', on: 'input', do: { type: 'find' } }),
    ),
    h('p', { id: 'found', role: 'status' }, `${number(matches.length)} of ${number(data.areas.length)} areas.${more}`),
    mapBox('Every area. Press one to open it.', { fill: 'found', ids: matches.length === data.areas.length ? [] : matches.map((area) => area.id) }),
    table(['Area', 'Borough', 'Label', 'Name'], rows, 'No area has that name or that borough.'),
  ];
}

// The map of a screen. panel.mjs draws on it what `draw` says, once the outlines are held.
export function mapBox(words, draw) {
  return h(
    'div',
    { class: 'map-box' },
    h('canvas', { id: 'map', class: 'map', role: 'img', 'aria-label': words, tabindex: '0', do: { type: 'map' }, draw }),
    h('p', { id: 'map-says', role: 'status' }, words),
  );
}

export function viewArea(data) {
  const area = data.area;
  const named = area.state === 'checked' ? 'A person has checked the name.' : area.state === 'draft' ? 'The name is a draft: no person has read it.' : 'It bears its publisher’s label.';
  const figures = data.figures.map((row) => [
    link('measure', row.measure, row.label),
    figure(row.value, row.unit),
    sources(row),
    row.date,
    files(row),
    STATES[row.state] || row.state,
    flagButton(`figure/${area.id}/${row.measure}`, `${row.label}, of ${area.name}`),
  ]);
  const costs = data.costs.map((row) => [
    `${row.segment} to ${row.tenure}`.replace(/_/g, ' '),
    figure(row.median, row.unit),
    row.sales === null ? 'The publisher gives no count' : `${number(row.sales)} sales since ${row.since}`,
    sources(row),
    row.date,
    files(row),
    flagButton(`figure/${area.id}/${row.key}`, `What a ${row.segment} sells for, in ${area.name}`.replace(/_/g, ' ')),
  ]);
  const vibes = data.vibes.map((row) => [
    [link('vibe', row.vibe, row.label), roughWords(row.rough)],
    bandOf(row),
    `${row.held} in 100 of its recipe${row.rests_on_little ? ', which is little' : ''}${row.why ? `. ${row.why}` : ''}`,
    h('ul', {}, row.parts.map((one) => h('li', {}, `${one.hundredths} in 100: ${one.label}, read from its ${one.read} end. ${one.has_a_figure ? 'It has a figure.' : 'No figure.'}`))),
    flagButton(`band/${area.id}/${row.vibe}`, `${row.label}, of ${area.name}`),
  ]);
  const missing = data.missing.map((row) => [row.label, row.why]);
  return [
    h('h1', {}, `${area.name}, ${area.borough}`),
    h('p', {}, `${area.label}. ${named}`, area.named_by.length ? ` The name is written by: ${area.named_by.join(', ')}.` : ''),
    h('p', {}, flagButton(`name/${area.id}`, `The name of ${area.name}`), ' the name, or ', flagButton(`border/${area.id}`, `The border of ${area.name}`), ' the border.'),
    h('p', {}, 'Beside it: ', area.beside.map((other, at) => [at ? ', ' : '', link('area', other.id, other.name)]), area.beside.length ? '.' : 'no area.'),
    flagsOf(data),
    h('h2', {}, `Every figure: ${figures.length}`),
    table(['Measure', 'Figure', 'Source', 'As of', 'The files it rests on', 'State', ''], figures, 'The release holds no figure of this area.'),
    h('h2', {}, 'What a home sells for'),
    table(['Home', 'Median', 'Rests on', 'Source', 'As of', 'The files it rests on', ''], costs, 'The release holds no price of this area.'),
    h('h2', {}, 'Every vibe'),
    table(['Vibe', 'Band', 'Rests on', 'The parts behind it', ''], vibes, 'The release carries no vibe.'),
    h('h2', {}, `No figure for: ${missing.length}`),
    table(['Measure', 'Why'], missing, 'It has a figure for every measure.'),
  ];
}

// ---------------------------------------------------------------- a measure

function wordsBox(id, words, value, more = {}) {
  return h('p', { class: 'field' }, h('label', { for: id }, words), h('input', { id, type: 'text', value: value === null || value === undefined ? '' : value, autocomplete: 'off', spellcheck: 'false', autocorrect: 'off', autocapitalize: 'off', ...more }));
}

const NAME_RULE = 'A name is one line of plain words, with no figure. It calls no place safe or unsafe, gives no praise or blame, and says nothing of who lives somewhere.';

// The two labels of a measure, as they stand for the reviewer, and the press that looks
// at a change of them.
export function viewRelabel(data) {
  const adjust = data.adjust;
  if (!adjust) return [];
  if (!adjust.may) return [h('h2', {}, 'Its label'), h('p', { class: 'rule' }, 'It counts who lived somewhere, so it keeps the name core gives it: the name says who was counted, and at which census.')];
  return [
    h('h2', {}, 'Its label'),
    adjust.as_served ? null : h('p', { class: 'rule' }, 'You have kept a change of this label that is not yet built.'),
    wordsBox('label-long', 'Its label, which says what is counted and how', adjust.labels.label, { maxlength: 200 }),
    wordsBox('label-short', 'Its short label, of 40 characters at most', adjust.labels.short_label, { maxlength: 40 }),
    h('p', { class: 'rule' }, NAME_RULE),
    h('p', { class: 'field' }, propose(`${data.measure.label}: its label`, { what: 'label', of: data.measure.id, fields: { label: { id: 'label-long' }, short_label: { id: 'label-short' } } })),
    h('p', { id: 'propose-trouble', role: 'alert' }, ''),
  ];
}

// The name of a vibe and of its two ends, and what it cannot see, as they stand for the
// reviewer.
export function viewRename(data) {
  const adjust = data.adjust;
  if (!adjust) return [];
  const about = data.vibe;
  const scale = adjust.names.low_end !== null;
  const ends = scale ? { low_end: { id: 'name-low' }, high_end: { id: 'name-high' } } : {};
  return [
    h('h2', {}, 'Its name'),
    wordsBox('name-label', 'The name of the vibe, of 40 characters at most', adjust.names.label, { maxlength: 40 }),
    scale ? wordsBox('name-low', 'The name of its low end', adjust.names.low_end, { maxlength: 40 }) : null,
    scale ? wordsBox('name-high', 'The name of its high end', adjust.names.high_end, { maxlength: 40 }) : null,
    h('p', { class: 'rule' }, NAME_RULE),
    h('p', { class: 'field' }, propose(`${about.label}: its name`, { what: 'name', of: about.id, base: { low_end: null, high_end: null }, fields: { label: { id: 'name-label' }, ...ends } })),
    h('h2', {}, 'What it cannot see'),
    h('p', {}, 'Every vibe says this first, and it is not changed here: ', h('q', {}, about.cannot_see[0] || '')),
    h('p', { class: 'field' }, h('label', { for: 'cannot-see' }, 'What else it cannot see, one line for each, of 200 characters at most'), h('textarea', { id: 'cannot-see', rows: 6, value: adjust.cannot_see.join('\n'), spellcheck: 'false', autocorrect: 'off', autocapitalize: 'off' })),
    h('p', { class: 'rule' }, 'A line that names the census or recorded crime is kept.'),
    h('p', { class: 'field' }, propose(`${about.label}: what it cannot see`, { what: 'cannot_see', of: about.id, whole: 'lines', fields: { lines: { id: 'cannot-see', as: 'lines' } } })),
    h('p', { id: 'propose-trouble', role: 'alert' }, ''),
  ];
}

export function viewMeasure(data) {
  const about = data.measure;
  const spread = data.spread;
  const most = Math.max(1, ...spread.bins.map((bin) => bin.areas));
  const bins = spread.bins.map((bin) => [
    `${number(bin.from)} to ${number(bin.to)}`,
    number(bin.areas),
    h('progress', { max: most, value: bin.areas }, `${bin.areas}`),
  ]);
  const ends = (rows) => rows.map((row) => [...place(row), figure(row.value, about.unit)]);
  const out = data.stands_out.map((row) => [...place(row), figure(row.value, about.unit), WHY_STANDS_OUT[row.why] || row.why, flagButton(`figure/${row.id}/${about.id}`, `${about.label}, of ${row.name}`)]);
  return [
    h('h1', {}, about.label),
    h('p', {}, `${about.unit}. ${about.ranked_on ? 'It is ranked on.' : 'It is shown, and never ranked on.'} ${sources(about)}, ${about.date}.`),
    h('p', {}, about.definition),
    flagsOf(data),
    viewRelabel(data),
    h('h2', {}, 'Its spread'),
    h('p', {}, `${number(spread.with_a_figure)} of ${number(spread.areas)} areas have a figure. ` + (spread.with_a_figure ? `Least ${figure(spread.least, about.unit)}, lower quartile ${figure(spread.lower_quartile, about.unit)}, median ${figure(spread.median, about.unit)}, upper quartile ${figure(spread.upper_quartile, about.unit)}, most ${figure(spread.most, about.unit)}.` : '')),
    table(['From and to', 'Areas', ''], bins, 'No area has a figure.'),
    h('h2', {}, 'Highest'),
    table(['Area', 'Borough', 'Figure'], ends(data.highest), 'No area has a figure.'),
    h('h2', {}, 'Lowest'),
    table(['Area', 'Borough', 'Figure'], ends(data.lowest), 'No area has a figure.'),
    h('h2', {}, `What stands out: ${out.length}`),
    table(['Area', 'Borough', 'Figure', 'Why', ''], out, 'No figure stands out from the areas beside it.'),
    h('h2', {}, `Areas with no figure: ${data.missing.length}`),
    table(['Area', 'Borough', 'Why'], data.missing.map((row) => [...place(row), row.why]), 'Every area has a figure.'),
  ];
}

// ---------------------------------------------------------------- a vibe

export function followsWords(follows) {
  return follows.map((one) => (one.rank_correlation === null ? `${one.label}: not known, for no area is placed.` : `${one.label}: ${one.rank_correlation.toFixed(2)}, across ${number(one.areas)} areas.`));
}

// ---------------------------------------------------------------- the shares of a recipe

function clamp(value, least, most) {
  return Math.min(most, Math.max(least, value));
}

// The shares of a recipe once one of them is moved: the part that was moved holds what it
// was moved to, as near as the rules let it, and the others share what is left in the
// proportion they stood in. They always come to 100, in whole hundredths, and each holds
// from `least` to `most`.
export function rebalance(shares, moved, to, least, most) {
  const others = Object.keys(shares).filter((part) => part !== moved);
  if (!(moved in shares) || others.length === 0) return { ...shares };
  const wanted = Number.isFinite(to) ? Math.round(to) : shares[moved];
  const value = clamp(wanted, Math.max(least, 100 - others.length * most), Math.min(most, 100 - others.length * least));
  const fixed = {};
  let free = others.slice();
  let ideal = {};
  for (;;) {
    const room = 100 - value - Object.values(fixed).reduce((sum, held) => sum + held, 0);
    const total = free.reduce((sum, part) => sum + shares[part], 0);
    ideal = Object.fromEntries(free.map((part) => [part, total > 0 ? (room * shares[part]) / total : room / free.length]));
    const out = free.find((part) => ideal[part] < least) || free.find((part) => ideal[part] > most);
    if (out === undefined) break;
    fixed[out] = ideal[out] < least ? least : most;
    free = free.filter((part) => part !== out);
  }
  const made = Object.fromEntries(free.map((part) => [part, Math.floor(ideal[part])]));
  let left = 100 - value - Object.values(fixed).reduce((sum, held) => sum + held, 0) - Object.values(made).reduce((sum, held) => sum + held, 0);
  // What rounding down left over goes, a hundredth each, to the parts that lost most by it.
  const order = free.slice().sort((a, b) => ideal[b] - Math.floor(ideal[b]) - (ideal[a] - Math.floor(ideal[a])) || others.indexOf(a) - others.indexOf(b));
  for (let at = 0; left > 0 && order.length > 0; at = (at + 1) % order.length) {
    if (made[order[at]] < most) {
      made[order[at]] += 1;
      left -= 1;
    } else if (order.every((part) => made[part] >= most)) {
      break;
    }
  }
  return Object.fromEntries(Object.keys(shares).map((part) => [part, part === moved ? value : part in fixed ? fixed[part] : made[part]]));
}

export function sharesOf(adjust) {
  return Object.fromEntries(adjust.shares.map((part) => [part.measure, part.hundredths]));
}

export function sameShares(one, other) {
  const parts = Object.keys(one);
  return parts.length === Object.keys(other).length && parts.every((part) => one[part] === other[part]);
}

function areaRows(rows) {
  return rows.map((row) => [...place(row), row.from === null ? SAYS.noBand : String(row.from), row.to === null ? SAYS.noBand : String(row.to)]);
}

// What a change would move, as the desk worked it out: shown before anything is kept.
export function viewMoved(found) {
  const bands = found.bands;
  const placed = bands.placed_before === bands.placed_after ? '' : ` ${number(bands.placed_before)} areas have a band today, and ${number(bands.placed_after)} would.`;
  const searches = found.searches.map((search) => {
    const rows = [];
    for (let at = 0; at < Math.max(search.before.first.length, search.after.first.length); at += 1) {
      const was = search.before.first[at];
      const now = search.after.first[at];
      rows.push([String(at + 1), was ? `${was.name}, ${was.borough}` : '', now ? `${now.name}, ${now.borough}` : '']);
    }
    const notes = [...new Set([...search.before.notes, ...search.after.notes])];
    return [
      h('h4', {}, search.name),
      h('p', { class: 'says' }, search.says),
      h('p', { class: 'rule' }, search.read_as),
      notes.map((words) => h('p', { class: 'rule' }, words)),
      h('p', {}, `${number(search.after.ranked)} areas are ranked, and ${number(search.after.left_out)} are left out by a firm limit. ` + (search.same ? 'The first ten are the same, in the same order.' : 'The first ten differ.')),
      table(['Place', 'Before', 'After'], rows, 'No area is ranked.'),
    ];
  });
  return [
    h('h3', { id: 'moved', tabindex: '-1' }, 'What would move'),
    h('p', {}, `${number(bands.change_band)} of ${number(bands.areas)} areas change band: ${number(bands.up)} go up, and ${number(bands.down)} go down.${placed}`),
    table(['From band', 'To band', 'Areas'], bands.steps.map((step) => [step.from === null ? SAYS.noBand : String(step.from), step.to === null ? SAYS.noBand : String(step.to), number(step.areas)]), 'No area changes band.'),
    h('h4', {}, 'The areas that rise most'),
    table(['Area', 'Borough', 'From band', 'To band'], areaRows(bands.rise), 'No area rises.'),
    h('h4', {}, 'The areas that fall most'),
    table(['Area', 'Borough', 'From band', 'To band'], areaRows(bands.fall), 'No area falls.'),
    h('h3', {}, 'The first ten areas of three searches, before and after'),
    searches,
  ];
}

// The sliders of a recipe, what would move, and the keeping of it. `state.adjust` is what
// a person has moved and looked at on this screen, and is null until they move a slider.
export function viewAdjust(data, state = {}) {
  const adjust = data.adjust;
  if (!adjust) return [];
  const stands = sharesOf(adjust);
  const mine = state.adjust && state.adjust.of === data.vibe.id ? state.adjust : null;
  const shares = mine ? mine.shares : stands;
  const moved = !sameShares(shares, stands);
  const looked = mine && mine.found && sameShares(mine.found.now, shares) ? mine.found : null;
  const rows = adjust.shares.map((part) => [
    h('label', { for: `share-${part.measure}` }, part.label),
    h('input', { id: `share-${part.measure}`, type: 'range', min: adjust.least, max: adjust.most, step: 1, value: shares[part.measure], on: 'input', do: { type: 'slide', part: part.measure } }),
    h('output', { for: `share-${part.measure}` }, `${shares[part.measure]} in 100`),
    `${stands[part.measure]} in 100`,
    `Read from its ${part.read} end${part.counts_residents ? '. It counts who lived there, at the census' : ''}`,
  ]);
  return [
    h('h2', {}, 'Adjust its recipe'),
    h('p', {}, `Move a share, and the others make room: they always come to 100. A part holds from ${adjust.least} to ${adjust.most} in 100. No part is added, taken out or turned round here.`),
    adjust.as_served ? null : h('p', { class: 'rule' }, 'You have kept a change of this vibe that is not yet built. What stands is what you kept, and not what is served.'),
    table(['Part', 'Its share', 'Would be', 'Stands at', 'Read'], rows, ''),
    h(
      'p',
      { class: 'field' },
      h('button', { type: 'button', id: 'look', disabled: !moved, do: { type: 'preview' } }, 'See what would move'),
      ' ',
      h('button', { type: 'button', id: 'reset', disabled: !moved, do: { type: 'reset' } }, 'Put the shares back'),
    ),
    h('p', { id: 'adjust-trouble', role: 'alert' }, (mine && mine.trouble) || ''),
    looked ? viewMoved(looked) : moved ? h('p', { class: 'rule' }, SAYS.previewFirst) : null,
    looked
      ? [
          h('h3', {}, 'Keep it'),
          h('p', { class: 'field' }, h('label', { for: 'keep-why' }, 'Why'), h('input', { id: 'keep-why', type: 'text', maxlength: 500, value: (mine && mine.why) || '', autocomplete: 'off', spellcheck: 'false', autocorrect: 'off', autocapitalize: 'off', on: 'input', do: { type: 'why' } })),
          h('p', { class: 'rule' }, SAYS.noteHint),
          h('p', { class: 'field' }, h('button', { type: 'button', id: 'keep', do: { type: 'keep' } }, 'Keep these shares')),
          h('p', { class: 'rule' }, SAYS.notBuilt),
        ]
      : null,
  ];
}

export function viewVibe(data, state = {}) {
  const about = data.vibe;
  const shape = about.shape === 'scale' ? `A scale, from ${about.low_end} to ${about.high_end}.` : 'It runs one way.';
  const recipe = about.recipe.map((one) => [
    link('measure', one.measure, one.label),
    `${one.hundredths} in 100`,
    `Read from its ${one.read} end`,
    one.carried ? 'Carried' : 'Not in this release',
    one.counts_residents ? 'Counts who lived there, at the census' : '',
  ]);
  const counts = ['1', '2', '3', '4', '5', 'none'].map((band) => [band === 'none' ? SAYS.noBand : `Band ${band}`, number(data.counts[band])]);
  const ends = (rows) => rows.map((row) => [...place(row), bandOf(row), flagButton(`band/${row.id}/${about.id}`, `${about.label}, of ${row.name}`)]);
  const little = data.rests_on_little.map((row) => [...place(row), bandOf(row), `${row.held} in 100`]);
  return [
    h('h1', {}, about.label),
    roughWords(about.rough),
    h('p', {}, `${about.meaning}. ${shape}`),
    h('p', {}, `The release holds ${about.held} in 100 of its recipe, and an area has a band from ${about.needed}. ${about.placed ? '' : 'It places no area.'}`),
    h('h2', {}, 'What it cannot see'),
    h('ul', {}, about.cannot_see.map((words) => h('li', {}, words))),
    flagsOf(data),
    h('h2', {}, 'Its recipe, as it is served'),
    table(['Part', 'Share', 'Read', 'In this release', ''], recipe, ''),
    viewAdjust(data, state),
    viewRename(data),
    h('h2', {}, 'Its five bands'),
    mapBox(`${about.label}, in five bands. Press an area to open it.`, { fill: 'bands', bands: data.bands }),
    table(['Band', 'Areas'], counts, ''),
    h('h2', {}, 'Highest'),
    table(['Area', 'Borough', 'Band', ''], ends(data.highest), 'No area is placed.'),
    h('h2', {}, 'Lowest'),
    table(['Area', 'Borough', 'Band', ''], ends(data.lowest), 'No area is placed.'),
    h('h2', {}, 'What it follows'),
    h('p', {}, SAYS.follows, ' A rank correlation of 1 is the same order, and 0 is no order in common.'),
    h('ul', {}, followsWords(data.follows).map((words) => h('li', {}, words))),
    h('h2', {}, `Bands that rest on little of the recipe: ${little.length}`),
    table(['Area', 'Borough', 'Band', 'Rests on'], little, 'Every band rests on three quarters of the recipe or more.'),
  ];
}

// ---------------------------------------------------------------- what is flagged, and the history

export function ofWords(line) {
  const area = line.area ? `${line.area.name}, ${line.area.borough}` : '';
  if (line.kind) return [line.kind, line.about, area].filter((words) => words).join(': ');
  return line.of;
}

function held(value) {
  if (value === null || value === undefined) return '';
  if (typeof value !== 'object') return String(value);
  if (Array.isArray(value)) return value.join(' ');
  return Object.entries(value).map(([name, one]) => `${name} ${one === null ? 'none' : one}`).join(', ');
}

export function takeBackButton(line) {
  return h('button', { type: 'button', do: { type: 'takeBack', n: line.n, words: `${WHAT[line.what]}: ${ofWords(line)}` } }, 'Take back');
}

export function viewFlagged(data) {
  const rows = data.flags.map((line) => [WHAT[line.what], line.area ? link('area', line.area.id, `${line.area.name}, ${line.area.borough}`) : '', line.about || line.kind, line.by, line.on, line.why, line.mine ? takeBackButton(line) : '']);
  return [
    h('h1', {}, `Flagged: ${rows.length}`),
    h('p', {}, 'Every flag that stands, newest first. A flag changes nothing in a build. A figure that is left out is not in the next build, with its reason.'),
    table(['What', 'Area', 'Of', 'By', 'On', 'Why', ''], rows, 'Nothing is flagged.'),
  ];
}

export function viewHistory(data) {
  const rows = data.history.map((line) => [
    String(line.n),
    line.on,
    line.by,
    line.what === 'take_back' ? `${WHAT.take_back}: line ${line.takes_back}` : WHAT[line.what],
    ofWords(line),
    held(line.was),
    held(line.now),
    line.why,
    line.what === 'take_back' ? (line.stands === false && line.taken_back_by ? `Taken back by line ${line.taken_back_by}` : '') : line.stands ? 'Stands' : line.taken_back_by ? `Taken back by line ${line.taken_back_by}` : 'A later line stands',
    line.mine && !line.taken_back_by ? takeBackButton(line) : '',
  ]);
  const differ = data.differ.map((one) => [WHAT[one.what], one.of, h('ul', {}, one.said.map((line) => h('li', {}, `${line.by}: ${held(line.now)}. ${line.why}`))), one.built ? `${one.built}, the founder` : 'Nobody: the founder has kept none']);
  return [
    h('h1', {}, 'History'),
    h('p', {}, 'Every change, newest first. A line is never changed and never removed: to take one back is a line too.'),
    table(['Line', 'On', 'By', 'What', 'Of', 'Before', 'Now', 'Why', 'Stands', ''], rows, 'Nothing was changed.'),
    h('h2', {}, `Where two reviewers differ: ${differ.length}`),
    table(['What', 'Of', 'Each says', 'Whose is built'], differ, 'No two reviewers differ.'),
  ];
}

// ---------------------------------------------------------------- a change that is proposed

// What a press proposes, read from the boxes of the screen. `values` gives what each box
// holds, by its id. A list is written with a semicolon between its items.
export function proposed(action, values) {
  const read = (field) => {
    const held = String(values[field.id] === undefined ? '' : values[field.id]).trim();
    // A list may begin with what another box holds: a chain is written first as it is named.
    const first = field.after ? [String(values[field.after] === undefined ? '' : values[field.after]).trim()] : [];
    if (field.as === 'list') return [...new Set([...first, ...held.split(';').map((one) => one.trim())])].filter((one) => one !== '');
    if (field.as === 'lines') return held.split('\n').map((one) => one.trim()).filter((one) => one !== '');
    if (field.as === 'number') return held === '' ? null : Number(held);
    if (field.as === 'or_none') return held === '' ? null : held;
    return held;
  };
  const of = action.ofFrom ? read({ id: action.ofFrom }) : action.of;
  if (action.now === null) return { what: action.what, of, now: null };
  const fields = Object.fromEntries(Object.entries(action.fields || {}).map(([name, field]) => [name, read(field)]));
  const now = action.whole ? fields[action.whole] : { ...(action.base || {}), ...fields };
  return { what: action.what, of, now };
}

function propose(words, action, label = 'Look at it') {
  return h('button', { type: 'button', do: { type: 'propose', words, ...action } }, label);
}

// What was looked at, as the box that asks for the reason shows it: what stood, what
// would stand, and what a build would work out again.
export function viewLooked(found) {
  const again = found.worked_out_again || [];
  return [
    table(['', 'Stands', 'Would stand'], [['', held(found.was) || 'Nothing: it is not on the table', held(found.now) || 'Nothing: it is taken out']], ''),
    again.length ? [h('p', {}, 'A build works these measures out again:'), h('ul', {}, again.map((label) => h('li', {}, label)))] : null,
    found.needs ? h('p', { class: 'rule' }, found.needs) : null,
    found.worked_out_again ? h('p', { class: 'rule' }, 'What this moves is known only once it is built: the panel holds no file of places.') : null,
    h('p', { class: 'rule' }, SAYS.notBuilt),
  ];
}

// ---------------------------------------------------------------- the table of brands

export function viewBrands(data) {
  const tiers = data.tiers;
  const kinds = Object.fromEntries(data.kinds.map((kind) => [kind.id, kind.label]));
  const tierOf = Object.fromEntries(tiers.map((tier) => [tier.id, tier.label]));
  const choose = (id, chosen, options) => h('select', { id, value: chosen }, options.map((one) => h('option', { value: one.id, selected: one.id === chosen }, one.label)));
  const row = (chain) => ({ name: chain.name, kind: chain.kind, tier: chain.tier, wikidata: chain.wikidata, spellings: chain.spellings });
  const rows = data.chains.map((chain) => [
    chain.name,
    kinds[chain.kind],
    tierOf[chain.tier] + (chain.changed ? ', which you changed' : ''),
    chain.spellings.join('; ') || 'The file of places writes it no way: it is counted nowhere',
    chain.named_by_core ? 'Yes' : 'No: it is counted in its tier, and cannot be asked for by name',
    [h('label', { for: `tier-${chain.key}`, class: 'unseen' }, `The tier of ${chain.name}`), choose(`tier-${chain.key}`, chain.tier, tiers), ' ', propose(`${chain.name}: to another tier`, { what: 'brand', of: chain.key, base: row(chain), fields: { tier: { id: `tier-${chain.key}` } } }, 'Move')],
    propose(`${chain.name}: taken out of the table`, { what: 'brand', of: chain.key, now: null }, 'Take out'),
  ]);
  const out = data.taken_out.map((chain) => [chain.name, kinds[chain.kind], tierOf[chain.tier], propose(`${chain.name}: put back on the table`, { what: 'brand', of: chain.key, base: row(chain), fields: {} }, 'Put back')]);
  const box = (id, words, more = {}) => h('p', { class: 'field' }, h('label', { for: id }, words), h('input', { id, type: 'text', autocomplete: 'off', spellcheck: 'false', autocorrect: 'off', autocapitalize: 'off', ...more }));
  return [
    h('h1', {}, 'The table of brands'),
    h('p', {}, 'Which chain of grocers, of gyms and of coffee is premium, which is mid-range and which is value. It is a judgement of what a chain charges and how it presents itself. It says nothing of who shops there.'),
    h('p', { class: 'rule' }, `${data.says} The ways a chain is written were read in ${data.read_in}.`),
    table(['Chain', 'Kind', 'Tier', 'As the file of places writes it', 'Core names a measure of it', 'Move it', 'Take it out'], rows, 'The table holds no chain.'),
    out.length ? [h('h2', {}, 'Taken out'), table(['Chain', 'Kind', 'Tier', ''], out, '')] : null,
    h('h2', {}, 'Add a chain'),
    box('new-key', 'Its name in an id, in small letters, as gildcrest', { maxlength: 40 }),
    box('new-name', 'Its name, letter for letter as the file of places writes it', { maxlength: 40 }),
    h('p', { class: 'field' }, h('label', { for: 'new-kind' }, 'Its kind'), choose('new-kind', 'grocer', data.kinds)),
    h('p', { class: 'field' }, h('label', { for: 'new-tier' }, 'Its tier'), choose('new-tier', 'mid', tiers)),
    box('new-spellings', 'Any other way the file of places writes it, with a semicolon between two'),
    box('new-wikidata', 'The ids an encyclopaedia gives it, as Q151954, with a semicolon between two'),
    h('p', { class: 'rule' }, 'A build adds a chain only where the file of places gives its name to two places or more that stand apart. One shop is no chain, and the name of a person is none.'),
    h('p', { class: 'field' }, propose('A chain added to the table', { what: 'brand', ofFrom: 'new-key', fields: { name: { id: 'new-name' }, kind: { id: 'new-kind' }, tier: { id: 'new-tier' }, wikidata: { id: 'new-wikidata', as: 'list' }, spellings: { id: 'new-spellings', as: 'list', after: 'new-name' } } }, 'Add')),
    h('p', { id: 'propose-trouble', role: 'alert' }, ''),
  ];
}

// ---------------------------------------------------------------- the numbers set by judgement

export function viewNumbers(data) {
  return [
    h('h1', {}, 'The numbers set by judgement'),
    h('p', {}, data.says),
    data.groups.map((group) => [h('h2', {}, group.title), table(['What it is', 'Today', 'Where it is', 'How it is changed'], group.numbers.map((row) => [row.says, `${number(row.value)} ${row.unit}`, row.where, row.changed_by]), '')]),
  ];
}

// ---------------------------------------------------------------- what moved between two builds

// How many areas are listed of those that moved most, of a measure and of a vibe.
export const MOST_SHOWN = 5;

function builtRow(one) {
  const kind = one.synthetic ? 'The made-up city' : one.preview ? 'A preview' : 'A finished release';
  return [one.release_id, one.built_at.slice(0, 10), kind, number(one.areas), number(one.measures), number(one.vibes)];
}

function stepsOf(one, unit) {
  const apart = one.changed ? ` Those that changed moved by ${figure(one.middle, unit)} in the middle, and by ${figure(one.most, unit)} at most.` : '';
  return `${number(one.changed)} of ${number(one.areas)} areas changed: ${number(one.up)} up, and ${number(one.down)} down. ${number(one.gained)} gained a figure, and ${number(one.lost)} lost one.${apart}`;
}

function fileRow(one) {
  if (!one.source) return [one.name, '', '', '', ''];
  return [one.source, one.list || '', one.item || '', one.edition || '', one.period || ''];
}

// What differs between the release that was named beside it and the release that is
// shown, as the step `moved` found it. An area is said by its band, and a figure with
// its unit. Nothing on this screen is a press: a build is approved by committing its lock.
export function viewWhatMoved(data) {
  if (!data.moved) return [h('h1', {}, 'What moved'), h('p', { class: 'rule' }, data.says)];
  const found = data.moved;
  const { areas, measures, vibes, files } = found;
  const rough = data.rough || {};
  const carried = (what, rows, empty) => [h('h3', {}, what), table(['Name', 'Id'], rows.map((one) => [[one.label, roughWords(rough[one.id])], one.id]), empty)];
  const moved = measures.moved.map((one) => [
    h('h3', {}, link('measure', one.id, one.label)),
    h('p', {}, stepsOf(one, one.unit), one.dated.was === one.dated.now ? '' : ` It was of ${one.dated.was}, and is of ${one.dated.now}.`),
    table(['Area', 'Borough', 'Was', 'Is'], one.moved_most.slice(0, MOST_SHOWN).map((row) => [...place(row), figure(row.was, one.unit), figure(row.now, one.unit)]), ''),
  ]);
  const bands = vibes.moved.map((one) => [
    h('h3', {}, link('vibe', one.id, one.label)),
    roughWords(rough[one.id]),
    h('p', {}, `${number(one.changed)} of ${number(one.areas)} areas changed band: ${number(one.up)} up, and ${number(one.down)} down. ${number(one.gained)} gained a band, and ${number(one.lost)} lost one.${one.recipe_changed ? ' The release carries another recipe, name or line of it.' : ''}`),
    table(['By how many bands', 'Areas'], one.by_bands.map((step) => [step.by > 0 ? `Up ${step.by}` : `Down ${-step.by}`, number(step.areas)]), ''),
    table(['Area', 'Borough', 'Was in band', 'Is in band'], one.moved_most.slice(0, MOST_SHOWN).map((row) => [...place(row), String(row.was), String(row.now)]), ''),
  ]);
  const costs = found.costs.map((one) => [`${one.segment} to ${one.tenure}`.replace(/_/g, ' '), stepsOf(one, one.unit)]);
  const searches = found.searches.map((search) => {
    const rows = [];
    for (let at = 0; at < Math.max(search.before.first.length, search.after.first.length); at += 1) {
      const was = search.before.first[at];
      const now = search.after.first[at];
      rows.push([String(at + 1), was ? `${was.name}, ${was.borough}` : '', now ? `${now.name}, ${now.borough}` : '']);
    }
    const notes = [...new Set([...search.before.notes, ...search.after.notes])];
    const same = search.same ? 'The first ten are the same, in the same order.' : `The first ten differ: ${number(search.kept)} stayed, ${number(search.came)} came and ${number(search.went)} went, and ${number(search.reordered)} of those that stayed stand at another place.`;
    return [
      h('h3', {}, search.name),
      h('p', { class: 'rule' }, search.read_as),
      notes.map((words) => h('p', { class: 'rule' }, words)),
      h('p', {}, `Before, ${number(search.before.ranked)} areas were ranked and ${number(search.before.left_out)} left out by a firm limit. After, ${number(search.after.ranked)} and ${number(search.after.left_out)}. ${same}`),
      table(['Place', 'Before', 'After'], rows, 'No area is ranked.'),
    ];
  });
  return [
    h('h1', {}, 'What moved'),
    h('p', {}, `Between ${found.before.release_id} and ${found.after.release_id}, which is the release that is shown.`),
    table(['Release', 'Built on', 'Kind', 'Areas', 'Measures', 'Vibes'], [builtRow(found.before), builtRow(found.after)], ''),
    h('p', { class: 'rule' }, 'Nothing here approves a build. To approve one is to commit its lock.'),
    h('h2', {}, `Areas: ${number(areas.came.length)} came, and ${number(areas.went.length)} went`),
    h('p', {}, `${number(areas.same)} areas are in both. ${number(areas.renamed.length)} bear another name, and ${number(areas.redrawn.length)} another outline.`),
    areas.came.length ? [h('h3', {}, 'Areas that came'), table(['Area', 'Borough'], areas.came.map((row) => place(row)), '')] : null,
    areas.went.length ? [h('h3', {}, 'Areas that went'), table(['Area', 'Borough'], areas.went.map((row) => [row.name, row.borough]), '')] : null,
    areas.renamed.length ? [h('h3', {}, 'Areas that bear another name'), table(['Was', 'Is', 'Borough'], areas.renamed.map((row) => [`${row.was}, ${row.was_in}`, link('area', row.id, row.name), row.borough]), '')] : null,
    areas.redrawn.length ? [h('h3', {}, 'Areas that have another outline'), table(['Area', 'Borough'], areas.redrawn.map((row) => place(row)), '')] : null,
    h('h3', {}, 'The areas that moved most'),
    table(['Area', 'Borough', 'Bands it moved by, in all', 'Vibes it changed band on', 'Figures that changed'], areas.moved_most.map((row) => [...place(row), number(row.bands), number(row.vibes), number(row.figures)]), 'No area moved.'),
    h('h2', {}, `Measures: ${number(measures.came.length)} came, ${number(measures.went.length)} went, and ${number(measures.moved.length)} moved`),
    measures.came.length ? carried('Measures that came', measures.came, '') : null,
    measures.went.length ? carried('Measures that went', measures.went, '') : null,
    measures.moved.length ? moved : h('p', { class: 'none' }, 'No figure of a measure that both carry changed.'),
    h('h2', {}, `Vibes: ${number(vibes.came.length)} came, ${number(vibes.went.length)} went, and ${number(vibes.moved.length)} moved`),
    vibes.came.length ? carried('Vibes that came', vibes.came, '') : null,
    vibes.went.length ? carried('Vibes that went', vibes.went, '') : null,
    vibes.moved.length ? bands : h('p', { class: 'none' }, 'No area changed band on a vibe that both carry.'),
    h('h2', {}, `What a home sells for: ${number(found.costs.length)} kinds of home moved`),
    table(['Home', 'What moved'], costs, 'No price changed.'),
    h('h2', {}, `The files behind the builds: ${number(files.changed.length)} changed, ${number(files.came.length)} came, and ${number(files.went.length)} went`),
    files.compared ? h('p', {}, `${number(files.same)} inputs are the same file in both.`) : h('p', { class: 'rule' }, 'A made-up release has no lock, so no file was compared.'),
    files.changed.length ? [h('h3', {}, 'Files that changed'), table(['Source', 'List', 'Item', 'Edition before', 'Period before', 'Edition after', 'Period after'], files.changed.map((one) => [...fileRow(one.was), fileRow(one.now)[3], fileRow(one.now)[4]]), '')] : null,
    files.came.length ? [h('h3', {}, 'Files that came'), table(['Source', 'List', 'Item', 'Edition', 'Period'], files.came.map(fileRow), '')] : null,
    files.went.length ? [h('h3', {}, 'Files that went'), table(['Source', 'List', 'Item', 'Edition', 'Period'], files.went.map(fileRow), '')] : null,
    h('h2', {}, `The first ten areas of ${number(found.searches.length)} searches, before and after`),
    searches,
  ];
}

export const VIEWS = {
  home: viewHome,
  moved: viewWhatMoved,
  areas: viewAreas,
  area: viewArea,
  measures: viewMeasures,
  measure: viewMeasure,
  vibes: viewVibes,
  vibe: viewVibe,
  flagged: viewFlagged,
  history: viewHistory,
  brands: viewBrands,
  numbers: viewNumbers,
};

// The title of the page, which says which screen it is.
export function titleOf(route, data) {
  const named = { area: data && data.area && data.area.name, measure: data && data.measure && data.measure.label, vibe: data && data.vibe && data.vibe.label }[route.view];
  const screen = named || (PARTS.find(([view]) => view === route.view) || PARTS[0])[1];
  return `${screen} - The panel - Burro review desk`;
}
