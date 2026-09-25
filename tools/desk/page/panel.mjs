// The panel itself: it asks the desk, copies what panel-logic.mjs worked out
// to the page, and carries out what a press asks for.
//
// Nothing is decided here. What a screen holds is worked out in
// panel-logic.mjs and panel-map.mjs, which are tested without a browser. This
// file asks the desk by a path on the page's own origin and never by a host,
// and writes words to the page as text and never as markup.

import { SAYS, VIEWS, hashOf, pathOf, pathTo, proposed, rebalance, routeOf, screen, sharesOf, titleOf, viewLooked } from './panel-logic.mjs';
import { PLAIN, areaAt, boxOf, fillOf, fit, legendOf, ringsOf, toGround, toScreen } from './panel-map.mjs';

// How long an answer from the desk is waited for. A release of a whole city is
// read from the disk of this machine, so an answer takes a moment and no more.
const ANSWER_WAIT_MS = 30000;
// What is set on an element as a property, and not as an attribute.
const PROPERTIES = new Set(['value', 'checked', 'disabled']);

// Start the panel. `env` is the browser, or a stand-in for it in a test.
export function boot(env) {
  const { document, window } = env;
  const $ = (id) => document.getElementById(id);
  const el = {};
  for (const id of ['banner', 'who', 'trouble', 'said', 'main', 'box', 'box-title', 'box-of', 'box-more', 'why', 'box-trouble', 'box-yes', 'box-no']) {
    el[id] = $(id);
  }
  const state = { route: routeOf(env.location.hash), data: null, token: '', synthetic: null, words: '', outlines: null, asked: false, box: null, canvas: null, made: new Map(), busy: false, adjust: null };

  // ---------------------------------------------------------------- asking the desk

  async function ask(path, init) {
    const control = new env.AbortController();
    const stop = env.setTimeout(() => control.abort(), ANSWER_WAIT_MS);
    try {
      const answer = await env.fetch(path, { ...init, cache: 'no-store', credentials: 'same-origin', redirect: 'error', signal: control.signal });
      let data = null;
      try {
        data = await answer.json();
      } catch {
        data = null;
      }
      return { ok: answer.ok && data !== null, status: answer.status, data };
    } catch {
      return { ok: false, status: 0, data: null };
    } finally {
      env.clearTimeout(stop);
    }
  }

  function read(path) {
    return ask(path, { method: 'GET', headers: { Accept: 'application/json' } });
  }

  function write(path, body) {
    return ask(path, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'X-Desk-Token': state.token },
      body: JSON.stringify(body),
    });
  }

  function wrong(out) {
    if (out.data && typeof out.data.message === 'string') return out.data.message;
    return out.status === 0 ? 'The desk did not answer. Is it still running? Start it with make desk.' : 'The desk could not answer that.';
  }

  // ---------------------------------------------------------------- the page

  function build(tree) {
    if (typeof tree === 'string') return tree;
    const node = document.createElement(tree.tag);
    for (const [name, value] of Object.entries(tree.attrs)) {
      if (name === 'do' || name === 'on' || name === 'draw' || PROPERTIES.has(name)) continue;
      if (value === true) node.setAttribute(name, '');
      else if (value !== false && value !== null && value !== undefined) node.setAttribute(name, String(value));
    }
    if (tree.attrs.do) node.addEventListener(tree.attrs.on || 'click', (event) => act(tree.attrs.do, node, event));
    if (tree.attrs.draw) state.canvas = { node, draw: tree.attrs.draw };
    if (tree.attrs.id) state.made.set(tree.attrs.id, node);
    node.append(...tree.children.map(build));
    // What a box holds is set once what it may hold is in it: a list takes its choice so.
    for (const name of PROPERTIES) if (name in tree.attrs) node[name] = tree.attrs[name];
    return node;
  }

  function banner() {
    const known = state.synthetic !== null;
    el.banner.className = `banner ${known ? (state.synthetic ? 'made-up' : 'real') : 'unknown'}`;
  }

  function render() {
    state.canvas = null;
    state.made = new Map();
    const view = VIEWS[state.route.view];
    const trees = state.data ? view(state.data, { words: state.words, adjust: state.adjust }) : [];
    el.main.replaceChildren(...screen(trees).map(build));
    document.title = titleOf(state.route, state.data);
    banner();
    draw();
  }

  async function show(quiet = false) {
    const route = routeOf(env.location.hash);
    // What was moved and looked at is of one screen. It is dropped when the screen is left.
    if (route.view !== state.route.view || route.id !== state.route.id) state.adjust = null;
    state.route = route;
    if (!quiet) el.said.textContent = '';
    const out = await read(pathOf(route));
    if (route !== state.route) return;
    if (!out.ok) {
      state.data = null;
      el.trouble.textContent = wrong(out);
      render();
      return;
    }
    el.trouble.textContent = '';
    state.data = out.data;
    state.synthetic = out.data.synthetic === true;
    render();
    if (state.canvas && state.outlines === null && !state.asked) outlines();
  }

  // ---------------------------------------------------------------- the map

  async function outlines() {
    state.asked = true;
    const out = await read(pathTo('outlines'));
    state.asked = false;
    if (!out.ok) return;
    state.outlines = out.data.outlines;
    draw();
  }

  function dark() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function laid() {
    const canvas = state.canvas && state.canvas.node;
    if (!canvas || state.outlines === null) return null;
    const ratio = window.devicePixelRatio || 1;
    const width = Math.max(1, Math.round(canvas.clientWidth * ratio));
    const height = Math.max(1, Math.round(canvas.clientHeight * ratio));
    return { canvas, ratio, width, height, view: fit(boxOf(state.outlines), width, height) };
  }

  function draw() {
    const held = laid();
    if (held === null || held.view === null) return;
    const { canvas, width, height, view } = held;
    canvas.width = width;
    canvas.height = height;
    const pen = canvas.getContext('2d');
    const shade = PLAIN[dark() ? 'dark' : 'light'];
    pen.fillStyle = shade.paper;
    pen.fillRect(0, 0, width, height);
    pen.strokeStyle = shade.line;
    pen.lineWidth = 1;
    for (const id of Object.keys(state.outlines).sort()) {
      pen.beginPath();
      for (const ring of ringsOf(state.outlines[id])) {
        ring.forEach((point, at) => {
          const [x, y] = toScreen(view, point);
          if (at === 0) pen.moveTo(x, y);
          else pen.lineTo(x, y);
        });
        pen.closePath();
      }
      pen.fillStyle = fillOf(state.canvas.draw, id, dark());
      pen.fill('evenodd');
      pen.stroke();
    }
    const legend = legendOf(state.canvas.draw, dark());
    legend.forEach((row, at) => {
      pen.fillStyle = row.colour;
      pen.fillRect(12, 12 + at * 26, 20, 20);
      pen.strokeRect(12, 12 + at * 26, 20, 20);
      pen.fillStyle = shade.ink;
      pen.font = '16px system-ui, sans-serif';
      pen.fillText(row.words, 40, 28 + at * 26);
    });
  }

  function pressed(event) {
    const held = laid();
    if (held === null || held.view === null) return null;
    const box = held.canvas.getBoundingClientRect();
    const point = [(event.clientX - box.left) * held.ratio, (event.clientY - box.top) * held.ratio];
    return areaAt(state.outlines, toGround(held.view, point));
  }

  // ---------------------------------------------------------------- what a press asks for

  function open(box) {
    state.box = box;
    el['box-title'].textContent = box.title;
    el['box-of'].textContent = box.words;
    el['box-yes'].textContent = box.yes;
    el['box-trouble'].textContent = '';
    el['box-more'].replaceChildren(...screen(box.more || []).map(build));
    el.why.value = '';
    if (!el.box.open) el.box.showModal();
    el.why.focus();
  }

  function shut() {
    state.box = null;
    if (el.box.open) el.box.close();
  }

  async function confirm() {
    const box = state.box;
    if (box === null || state.busy) return;
    const why = el.why.value.trim();
    if (why === '') {
      el['box-trouble'].textContent = SAYS.needsReason;
      return;
    }
    state.busy = true;
    const sent = { flag: () => write(pathTo('flag'), { of: box.of, why, leave_out: false }), takeBack: () => write(pathTo('takeBack'), { n: box.n, why }), keep: () => write(pathTo('keep'), { ...box.change, why, seen: box.seen }) };
    const out = await sent[box.kind]();
    state.busy = false;
    if (!out.ok) {
      el['box-trouble'].textContent = wrong(out);
      return;
    }
    const line = out.data.line;
    shut();
    const did = { flag: 'Flagged', takeBack: 'Taken back', keep: 'Kept' }[box.kind];
    el.said.textContent = `${did}: ${box.words}. It is line ${line.n} of your file of changes.${box.kind === 'keep' ? ' Nothing that is served has changed: a build is made from the file.' : ''}`;
    await show(true);
  }

  // The sliders of a recipe, as a person has moved them on this screen.
  function moved() {
    const of = state.data.vibe.id;
    if (state.adjust === null || state.adjust.of !== of) state.adjust = { of, shares: sharesOf(state.data.adjust), found: null, why: '', trouble: '' };
    return state.adjust;
  }

  function again(id) {
    render();
    const node = state.made.get(id);
    if (node) node.focus();
  }

  async function look() {
    const mine = moved();
    if (state.busy) return;
    state.busy = true;
    const out = await write(pathTo('preview'), { what: 'recipe', of: mine.of, now: mine.shares });
    state.busy = false;
    if (state.adjust !== mine) return;
    mine.found = out.ok ? out.data : null;
    mine.trouble = out.ok ? '' : wrong(out);
    again(out.ok ? 'moved' : 'look');
  }

  async function keepIt() {
    const mine = moved();
    if (state.busy || mine.found === null) return;
    if (mine.why.trim() === '') {
      mine.trouble = SAYS.needsReason;
      again('keep-why');
      return;
    }
    state.busy = true;
    const out = await write(pathTo('keep'), { what: 'recipe', of: mine.of, now: mine.shares, why: mine.why.trim(), seen: mine.found.seen });
    state.busy = false;
    if (!out.ok) {
      mine.trouble = wrong(out);
      again('keep-why');
      return;
    }
    state.adjust = null;
    el.said.textContent = `Kept: the shares of ${state.data.vibe.label}. It is line ${out.data.line.n} of your file of changes. Nothing that is served has changed: a build is made from the file.`;
    await show(true);
  }

  // A change that is proposed is looked at first: the desk says what stood and what would
  // stand, and only then is the reason asked for.
  async function lookAt(action) {
    if (state.busy) return;
    const values = Object.fromEntries([...state.made].map(([id, node]) => [id, node.value]));
    const change = proposed(action, values);
    state.busy = true;
    const out = await write(pathTo('preview'), change);
    state.busy = false;
    const trouble = state.made.get('propose-trouble');
    if (trouble) trouble.textContent = out.ok ? '' : wrong(out);
    if (!out.ok) {
      if (!trouble) el.trouble.textContent = wrong(out);
      return;
    }
    open({ kind: 'keep', title: 'Keep', yes: 'Keep', words: action.words, change, seen: out.data.seen, more: viewLooked(out.data) });
  }

  function act(action, node, event) {
    if (action.type === 'propose') lookAt(action);
    else if (action.type === 'slide') {
      const mine = moved();
      mine.shares = rebalance(mine.shares, action.part, Number(node.value), state.data.adjust.least, state.data.adjust.most);
      mine.trouble = '';
      again(`share-${action.part}`);
    } else if (action.type === 'why') moved().why = node.value;
    else if (action.type === 'reset') {
      state.adjust = null;
      again('look');
    } else if (action.type === 'preview') look();
    else if (action.type === 'keep') keepIt();
    else if (action.type === 'flag') open({ kind: 'flag', title: 'Flag', yes: 'Flag', of: action.of, words: action.words });
    else if (action.type === 'takeBack') open({ kind: 'takeBack', title: 'Take back', yes: 'Take back', n: action.n, words: action.words });
    else if (action.type === 'find') {
      state.words = node.value;
      render();
      // The box a person types in is made again with the rest. The keyboard stays in it.
      const again = state.made.get('find');
      if (again) again.focus();
      if (again && again.setSelectionRange) again.setSelectionRange(state.words.length, state.words.length);
    } else if (action.type === 'map') {
      const id = pressed(event);
      if (id !== null) env.location.hash = hashOf('area', id);
    }
  }

  // ---------------------------------------------------------------- starting

  el['box-yes'].addEventListener('click', () => confirm());
  el['box-no'].addEventListener('click', () => shut());
  el.why.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') confirm();
  });
  el.box.addEventListener('close', () => {
    state.box = null;
  });
  window.addEventListener('hashchange', () => show());
  window.addEventListener('resize', () => draw());

  async function start() {
    const out = await read(pathTo('state'));
    if (!out.ok) {
      el.trouble.textContent = wrong(out);
      return;
    }
    state.token = out.data.token;
    state.synthetic = out.data.synthetic === true;
    el.banner.textContent = out.data.banner;
    el.who.textContent = `You are ${out.data.reviewer}.`;
    banner();
    await show();
  }

  const started = start();
  return { state, started, show };
}

if (typeof document !== 'undefined' && typeof window !== 'undefined') {
  boot({
    document,
    window,
    location: window.location,
    fetch: (path, init) => window.fetch(path, init),
    setTimeout: (fn, ms) => window.setTimeout(fn, ms),
    clearTimeout: (id) => window.clearTimeout(id),
    AbortController: window.AbortController,
  });
}
