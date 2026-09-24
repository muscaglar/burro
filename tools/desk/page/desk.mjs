// The page itself: it carries out what logic.mjs decides, and copies what it
// says to the screen.
//
// Nothing is decided here. What a key means, what is sent and what is shown
// are worked out in logic.mjs and map.mjs, which are tested without a browser.
// This file asks the desk, by a path on the page's own origin and never by a
// host, and writes words to the screen as text and never as markup.

import { hasUnsaved, keyAction, moveWords, ofWords, pathOf, start, step, theirWords, view } from './logic.mjs';
import { accept, areasAfter, boxFor, cellAt, credit, describe, drawList, fit, layersFor, moveView, nameOf, paint, panBy, refit, toGround, zoomBy } from './map.mjs';

// How long an answer from the desk is waited for. The desk is on this machine,
// so an answer that has not come by now will not.
const ANSWER_WAIT_MS = 15000;
const MOST_LAYERS = 24;
// What is known of an item keeps this much height where it holds as much: the
// 8rem of the style sheet, at the 16 pixels the page sets text in.
const FLOOR_PX = 128;
// A page of what is known keeps two lines of the last in view.
const PAGE_KEEP_PX = 48;
const PAGE_LEAST_PX = 40;

// Start the page. `env` is the browser, or a stand-in for it in a test.
export function boot(env) {
  const { document, window } = env;
  const $ = (id) => document.getElementById(id);
  const el = {};
  for (const id of [
    'banner', 'progress', 'reviewer', 'item', 'map-box', 'map', 'map-credit', 'map-says', 'text-box', 'text-before',
    'text-mark', 'text-after', 'record', 'wait', 'title', 'side', 'known', 'more', 'ask', 'flags', 'lines', 'picks', 'of', 'dispute',
    'mine', 'others', 'moves', 'question', 'rule-box', 'rule', 'aside-box', 'aside-short', 'aside', 'not-offered', 'answers', 'note', 'note-hint',
    'second', 'trouble', 'warn', 'said',
    'bar', 'panel', 'panel-banner', 'panel-title', 'panel-rows', 'panel-foot',
  ]) {
    el[id] = $(id);
  }

  let state = start();
  let timer = null;
  let letter = null;
  let lastItem = '';
  let lastDrawn = '';
  let lastShown = '';
  let ruleOurs = false; // true while the rule is open because the page opened it
  let asideOurs = false; // true while what to do is open because the page opened it
  const layers = new Map(); // "group/layer" to { file } or { why } or { asked: true }
  const chart = { key: '', view: null, fitted: null, size: { width: 0, height: 0 }, waiting: false, drag: null };

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

  async function carry(effect) {
    if (effect.do === 'get') {
      const out = await ask(pathOf(effect), { method: 'GET', headers: { Accept: 'application/json' } });
      dispatch({ type: 'got', what: effect.what, queue: effect.queue, item: effect.item, quiet: effect.quiet === true, ...out });
    } else if (effect.do === 'post') {
      const out = await ask(pathOf(effect), {
        method: 'POST',
        headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'X-Desk-Token': state.token },
        body: JSON.stringify(effect.body),
      });
      dispatch({ type: 'wrote', what: effect.what, ...out });
    } else if (effect.do === 'wait') {
      if (timer !== null) env.clearTimeout(timer);
      timer = env.setTimeout(() => {
        timer = null;
        dispatch({ type: 'retry' });
      }, effect.ms);
    } else if (effect.do === 'hold') {
      // A letter is held a moment. Each new letter starts the moment again.
      if (letter !== null) env.clearTimeout(letter);
      letter = env.setTimeout(() => {
        letter = null;
        dispatch({ type: 'release' });
      }, effect.ms);
    } else if (effect.do === 'map') {
      mapKey(effect.op, effect.small === true);
    } else if (effect.do === 'scroll') {
      page(effect.by);
    } else if (effect.do === 'focus') {
      focus(effect.on);
    }
  }

  function dispatch(event) {
    const out = step(state, { ...event, at: env.now() });
    state = out.state;
    render();
    for (const effect of out.effects) carry(effect);
  }

  // ---------------------------------------------------------------- the layers of the map

  function wanted() {
    return state.now && view(state).main.kind === 'map' ? layersFor(state.now.item) : [];
  }

  function held() {
    const out = {};
    for (const want of wanted()) {
      const entry = layers.get(want.key);
      if (entry && entry.file && !out[want.layer]) out[want.layer] = entry.file;
    }
    return out;
  }

  function refused() {
    return wanted().map((want) => layers.get(want.key)).filter((entry) => entry && entry.why).map((entry) => entry.why);
  }

  async function fetchLayer(want) {
    layers.set(want.key, { asked: true });
    const out = await ask(pathOf({ do: 'get', what: 'layer', group: want.group, layer: want.layer }), { method: 'GET', headers: { Accept: 'application/json' } });
    if (!out.ok) {
      // Not held: it is asked for again the next time an item wants it.
      layers.delete(want.key);
      if (wanted().some((one) => one.key === want.key)) layers.set(want.key, { why: `${want.layer} is not drawn: the desk did not send it.`, again: true });
    } else {
      const verdict = accept(out.data, want, state.synthetic);
      layers.set(want.key, verdict.ok ? { file: out.data } : { why: verdict.why });
    }
    draw();
  }

  function ensureLayers() {
    const keep = new Set();
    const items = [state.now ? state.now.item : null, ...Object.values(state.cache).map((entry) => entry.item)];
    for (const item of items) {
      for (const want of layersFor(item)) {
        keep.add(want.key);
        const entry = layers.get(want.key);
        if (!entry) fetchLayer(want);
      }
    }
    if (layers.size > MOST_LAYERS) for (const key of [...layers.keys()]) if (!keep.has(key)) layers.delete(key);
  }

  // A layer the desk did not send is asked for again when the item is next shown.
  function forgetFailed() {
    for (const [key, entry] of layers) if (entry.again) layers.delete(key);
  }

  // ---------------------------------------------------------------- the map

  function sizeOf() {
    const canvas = el.map;
    return { width: Math.max(1, canvas.clientWidth || 0), height: Math.max(1, canvas.clientHeight || 0) };
  }

  function draw() {
    if (chart.waiting) return;
    chart.waiting = true;
    env.requestAnimationFrame(() => {
      chart.waiting = false;
      drawNow();
    });
  }

  function drawNow() {
    const shown = view(state);
    if (shown.main.kind !== 'map' || !state.now) return;
    const canvas = el.map;
    const has = held();
    const no = refused();
    // The line under the map is written before the map is measured. Its words
    // may take the map a line of its height, and a map measured first is drawn
    // for a box it no longer has.
    set(el['map-credit'], [credit(has), ...no].filter(Boolean).join(' '));
    set(el['map-says'], describe({ layers: has, item: state.now.item, moves: state.now.moves, theirs: shown.theirs, refused: no }));
    const size = sizeOf();
    const ratio = window.devicePixelRatio || 1;
    if (canvas.width !== Math.round(size.width * ratio)) canvas.width = Math.round(size.width * ratio);
    if (canvas.height !== Math.round(size.height * ratio)) canvas.height = Math.round(size.height * ratio);
    const box = boxFor(state.now.item, has);
    const key = `${state.queue.id}/${state.now.id}/${state.now.item.rev}/${box ? box.join(',') : ''}`;
    if (chart.key !== key) {
      chart.key = key;
      chart.fitted = fit(box, size);
      chart.view = chart.fitted;
    } else if (size.width !== chart.size.width || size.height !== chart.size.height) {
      // Only the box changed size. The map stays where the person put it.
      const fitted = fit(box, size);
      chart.view = refit(chart.view, chart.fitted, fitted);
      chart.fitted = fitted;
    }
    chart.size = size;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    const dark = Boolean(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    paint(ctx, size, drawList({ layers: has, view: chart.view, size, item: state.now.item, moves: state.now.moves, theirs: shown.theirs, hand: state.hand, chosen: shown.of, cross: shown.canMove || shown.canName, dark }));
  }

  function cellUnder(point) {
    const has = held();
    if (!has.cells || !chart.view) return;
    const found = cellAt(has.cells, toGround(chart.view, chart.size, point));
    if (!found) return;
    const area = areasAfter(has.cells, state.now ? state.now.moves : []).get(found.id);
    if (typeof area === 'string') dispatch({ type: 'cell', cell: found.id, area });
  }

  function mapKey(op, small = false) {
    if (!chart.view) return;
    if (op === 'act') {
      cellUnder([chart.size.width / 2, chart.size.height / 2]);
      return;
    }
    chart.view = moveView(chart.view, chart.size, op, chart.fitted, small);
    draw();
  }

  function pointOf(event) {
    const box = el.map.getBoundingClientRect();
    return [event.clientX - box.left, event.clientY - box.top];
  }

  function onPointerDown(event) {
    if (event.button !== 0 || !chart.view) return;
    chart.drag = { from: pointOf(event), last: pointOf(event), moved: false };
    if (el.map.setPointerCapture && event.pointerId !== undefined) el.map.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event) {
    if (!chart.drag || !chart.view) return;
    const at = pointOf(event);
    if (Math.hypot(at[0] - chart.drag.from[0], at[1] - chart.drag.from[1]) > 4) chart.drag.moved = true;
    if (chart.drag.moved) {
      chart.view = panBy(chart.view, at[0] - chart.drag.last[0], at[1] - chart.drag.last[1]);
      draw();
    }
    chart.drag.last = at;
  }

  function onPointerUp(event) {
    const drag = chart.drag;
    chart.drag = null;
    if (drag && !drag.moved) cellUnder(pointOf(event));
  }

  function onWheel(event) {
    if (!chart.view) return;
    event.preventDefault();
    chart.view = zoomBy(chart.view, chart.size, event.deltaY < 0 ? 1.25 : 0.8, pointOf(event));
    draw();
  }

  // ---------------------------------------------------------------- the screen

  function make(tag, text = '', className = '') {
    const node = document.createElement(tag);
    if (text !== '') node.textContent = text;
    if (className !== '') node.className = className;
    return node;
  }

  function set(node, text) {
    if (node.textContent !== text) node.textContent = text;
  }

  // Keep a list at so many rows, and hand each row to `fill`. A row that is
  // already there is kept, so the keyboard stays where it was.
  function rows(list, count, create, fill) {
    while (list.children.length > count) list.children[list.children.length - 1].remove();
    while (list.children.length < count) list.append(create(list.children.length));
    for (let i = 0; i < count; i += 1) fill(list.children[i], i);
  }

  function keyed(onClick) {
    return () => {
      const row = make('li');
      const button = make('button');
      button.setAttribute('type', 'button');
      button.append(make('kbd'), make('span'));
      button.addEventListener('click', (event) => {
        onClick(row);
        // A click of the mouse gives the keyboard back to the page, so that the
        // next Enter takes what is proposed and not this button again. A button
        // reached by the keyboard keeps it.
        if (event && event.detail > 0) el.item.focus();
      });
      row.append(button);
      return row;
    };
  }

  function fillKeyed(row, key, text) {
    const button = row.children[0];
    set(button.children[0], key);
    set(button.children[1], text);
    return button;
  }

  function pairs(list, lines) {
    const flat = [];
    for (const line of lines) {
      flat.push({ tag: 'dt', text: String(line.label ?? '') });
      // The source is named after the value, unless the label or the value names it already.
      const named = line.source_id === line.label || line.source_id === line.value;
      const source = typeof line.source_id === 'string' && !named ? line.source_id : '';
      flat.push({ tag: 'dd', text: String(line.value ?? ''), source });
    }
    // A label and its value take turns, so the row at a place is always of one kind.
    rows(
      list,
      flat.length,
      (i) => make(flat[i].tag),
      (node, i) => set(node, flat[i].source ? `${flat[i].text} (${flat[i].source})` : flat[i].text),
    );
  }

  function texts(list, words) {
    rows(list, words.length, () => make('li'), (node, i) => set(node, words[i]));
  }

  function render() {
    const shown = view(state);
    document.title = shown.page;
    set(el.banner, shown.banner.text);
    el.banner.className = `banner ${shown.banner.kind}`;
    set(el.progress, shown.progress);
    set(el.reviewer, shown.reviewer);
    document.body.className = [shown.busy ? 'busy' : '', shown.paused ? 'paused' : ''].filter(Boolean).join(' ');

    const kind = shown.main.kind;
    el['map-box'].hidden = kind !== 'map';
    el['text-box'].hidden = kind !== 'text';
    el.record.hidden = kind !== 'record';
    el.wait.hidden = kind !== 'wait';
    if (kind === 'wait') set(el.wait, shown.main.text);
    if (kind === 'text') {
      set(el['text-before'], shown.main.before);
      set(el['text-mark'], shown.main.body);
      set(el['text-after'], shown.main.after);
    }
    if (kind === 'record') pairs(el.record, shown.main.lines);
    if (kind === 'map') {
      el.map.className = shown.canMove || shown.canName ? 'can-move' : '';
      if (state.now.id !== lastItem) {
        lastItem = state.now.id;
        forgetFailed();
      }
      ensureLayers();
      // The map is drawn again only when what it shows has changed, so that a
      // letter typed in the note does not draw a borough.
      const mark = [state.queue.id, state.now.id, state.now.item.rev, state.now.moves.length, shown.theirs.length, state.hand ? state.hand.cell : '', shown.canMove, shown.of.join(',')].join('/');
      if (mark !== lastDrawn) {
        lastDrawn = mark;
        draw();
      }
    } else {
      lastDrawn = '';
    }

    set(el.title, shown.title);
    set(el.flags, shown.flags);
    pairs(el.lines, shown.lines);
    rows(
      el.picks,
      shown.picks.length,
      keyed((row) => dispatch({ type: 'pick', index: [...el.picks.children].indexOf(row) })),
      (row, i) => fillKeyed(row, shown.picks[i].key, shown.picks[i].text).setAttribute('aria-pressed', shown.picks[i].chosen ? 'true' : 'false'),
    );
    const names = held();
    set(el.of, ofWords(shown.of, (id) => nameOf(names, id)));
    set(el.dispute, shown.dispute);
    set(el.mine, shown.mine);
    texts(el.others, [...shown.others, ...shown.theirs.map((move) => theirWords(move, (id) => nameOf(names, id)))]);
    texts(el.moves, shown.moves.map((move) => moveWords(move, (id) => nameOf(names, id))));
    set(el.question, shown.question);
    el['rule-box'].hidden = shown.rule === '';
    set(el.rule, shown.rule);
    // That an answer will be set aside is said above the answers, before one is given.
    el['aside-box'].hidden = shown.aside === null;
    set(el['aside-short'], shown.aside === null ? '' : shown.aside.short);
    set(el.aside, shown.aside === null ? '' : shown.aside.words);
    // Why an answer of the question is not offered on this item, where one is not.
    el['not-offered'].hidden = shown.notOffered === '';
    set(el['not-offered'], shown.notOffered);
    // A click gives the answer whose key the button shows: where an answer is
    // not offered, a button is not at the place of its key.
    rows(
      el.answers,
      shown.answers.length,
      keyed((row) => dispatch({ type: 'answer', index: Number(row.children[0].children[0].textContent) - 1 })),
      (row, i) => {
        const button = fillKeyed(row, shown.answers[i].key, shown.answers[i].text);
        if (shown.answers[i].stands) button.setAttribute('aria-current', 'true');
        else button.removeAttribute('aria-current');
      },
    );
    if (el.note.value !== shown.note.text) el.note.value = shown.note.text;
    el.note.disabled = !state.now;
    // The words under the note are shown while a note is written or kept.
    el['note-hint'].hidden = !shown.note.hinted;
    el.second.checked = shown.second;
    el.second.disabled = !state.now;
    set(el.trouble, shown.trouble);
    set(el.warn, shown.warn);
    set(el.said, shown.said);
    // The name of the item is printed once, over the item. Where what is said
    // is that name and no more, it is said aloud and not printed again.
    el.said.className = shown.saidIsName ? 'unseen' : '';
    const at = state.queue && state.now ? `${state.queue.id}/${state.now.id}` : '';
    const fresh = at !== lastShown;
    lastShown = at;
    if (fresh) {
      // A new item is read from its top, and the rule is open on the first item
      // of a queue and shut from then on. A person who opens it keeps it open
      // until the next item.
      el.known.scrollTop = 0;
      el.record.scrollTop = 0;
      el['rule-box'].open = shown.ruleOpen;
      ruleOurs = shown.ruleOpen;
      el['aside-box'].open = shown.aside !== null && shown.aside.open;
      asideOurs = el['aside-box'].open;
    }
    fitSide(shown);
    renderPanel(shown.panel);
  }

  // Fit the column to the window. What is known keeps a floor only where it
  // holds that much, the rule the page opened is shut if it pushes an answer
  // out of view, and the page says so when there is more to read than is shown.
  // Whether a box holds more than it shows, below what is in view. Once the last
  // line is in view there is no more below, however much there is above.
  function below(box) {
    return box.scrollHeight > box.clientHeight + 1 && box.scrollTop + box.clientHeight < box.scrollHeight - 1;
  }

  function fitSide(shown = view(state)) {
    const over = (box) => box.scrollHeight > box.clientHeight + 1;
    const more = () => (shown.known && below(el.known)) || (shown.main.kind === 'record' && below(el.record));
    const giveWay = () => {
      if (ruleOurs && el['rule-box'].open && over(el.ask)) {
        el['rule-box'].open = false;
        ruleOurs = false;
      }
      // What to do is shut after the rule, and only if an answer is still out of
      // view: that the answer waits is said in its first line, which stays.
      if (asideOurs && el['aside-box'].open && over(el.ask)) {
        el['aside-box'].open = false;
        asideOurs = false;
      }
    };
    // Measured with no floor and no line under it, so that what is measured is
    // what is known and not the box the last item left.
    el.more.hidden = true;
    el.side.className = '';
    if (shown.known && el.known.scrollHeight > FLOOR_PX) el.side.className = 'floor';
    giveWay();
    el.more.hidden = !more();
    // The line that says there is more takes its height from the answers. Where
    // that puts one out of view the rule gives way again, and what it gives may
    // be all that was left to read.
    if (!el.more.hidden && over(el.ask)) {
      giveWay();
      el.more.hidden = !more();
    }
  }

  // Page what is known of the item, up or down, by a little less than what is in
  // view. An item that is read in the middle of the page, as a rule is, is paged there.
  function page(by) {
    const box = view(state).main.kind === 'record' ? el.record : el.known;
    const step = Math.max(PAGE_LEAST_PX, box.clientHeight - PAGE_KEEP_PX);
    box.scrollTop = Math.max(0, box.scrollTop + by * step);
    readOn();
  }

  // What was read on, by a key or by the wheel: the line that says there is more
  // goes when the last line is in view, and comes back when it is not.
  function readOn() {
    const shown = view(state);
    const more = (shown.known && below(el.known)) || (shown.main.kind === 'record' && below(el.record));
    if (el.more.hidden === more) el.more.hidden = !more;
  }

  function renderPanel(panel) {
    const dialog = el.panel;
    if (panel === null) {
      if (dialog.open) dialog.close();
      return;
    }
    // A list lies over the page and dims it, so it says for itself which data this is.
    const banner = view(state).banner;
    set(el['panel-banner'], banner.text);
    el['panel-banner'].className = `banner ${banner.kind}`;
    set(el['panel-title'], panel.title);
    set(el['panel-foot'], panel.foot);
    const list = el['panel-rows'];
    if (list.getAttribute('data-kind') !== panel.kind) {
      list.replaceChildren();
      list.setAttribute('data-kind', panel.kind);
    }
    if (panel.kind === 'keys') {
      rows(
        list,
        panel.rows.length,
        () => {
          const row = make('li');
          row.append(make('kbd'), make('span'));
          return row;
        },
        (row, i) => {
          set(row.children[0], panel.rows[i].key);
          set(row.children[1], panel.rows[i].text);
        },
      );
    } else {
      rows(
        list,
        panel.rows.length,
        keyed((row) => dispatch({ type: 'choose', index: [...list.children].indexOf(row) })),
        (row, i) => {
          const button = fillKeyed(row, panel.rows[i].key, panel.rows[i].text);
          if (panel.rows[i].at) button.setAttribute('aria-current', 'true');
          else button.removeAttribute('aria-current');
        },
      );
    }
    if (!dialog.open) dialog.showModal();
  }

  function focus(on) {
    if (on === 'note') {
      el.note.focus();
      return;
    }
    if (on === 'panel') {
      const shown = view(state).panel;
      if (shown === null) return;
      const at = shown.rows.findIndex((row) => row.at);
      const row = el['panel-rows'].children[Math.max(0, at)];
      const target = row && row.children[0] && row.children[0].tagName === 'BUTTON' ? row.children[0] : el.panel;
      target.focus();
      return;
    }
    // Back to the page. The keyboard is moved only if it was somewhere that is
    // now shut, so that a person who works by the buttons stays on their button.
    const active = document.activeElement;
    const lost = !active || active === document.body || active === el.note || el.panel.contains(active);
    if (lost) el.item.focus();
  }

  // ---------------------------------------------------------------- what the person does

  function onKey(event) {
    if (event.isComposing) return;
    const target = event.target;
    const tag = target && target.tagName ? target.tagName : '';
    const key = {
      key: event.key,
      shift: event.shiftKey,
      ctrl: event.ctrlKey,
      alt: event.altKey,
      meta: event.metaKey,
      repeat: event.repeat,
      inNote: target === el.note,
      onButton: tag === 'BUTTON',
    };
    // A key the page has a use for is kept from the browser, whether it acts
    // now, is held a moment, or is taken for one of some words.
    if (keyAction(state, key) !== null) event.preventDefault();
    // What the key does is for logic.mjs to say: a letter may be the first of
    // some words, so the key is handed over and never the action.
    dispatch({ type: 'key', ...key });
  }

  function bar() {
    for (const entry of view(state).bar) {
      const node = entry.action ? make('button') : make('span');
      if (entry.action) {
        node.setAttribute('type', 'button');
        node.addEventListener('click', () => dispatch(entry.action));
      }
      node.append(make('kbd', entry.key), make('span', entry.label));
      el.bar.append(node);
    }
  }

  document.addEventListener('keydown', onKey);
  document.addEventListener('visibilitychange', () => dispatch({ type: 'seen', seen: !document.hidden }));
  window.addEventListener('beforeunload', (event) => {
    if (!hasUnsaved(state)) return undefined;
    event.preventDefault();
    event.returnValue = '';
    return '';
  });
  window.addEventListener('resize', () => {
    fitSide();
    draw();
  });
  if (window.matchMedia) {
    const scheme = window.matchMedia('(prefers-color-scheme: dark)');
    if (scheme.addEventListener) scheme.addEventListener('change', draw);
  }
  el.note.addEventListener('focus', () => {
    if (!state.noteOpen) dispatch({ type: 'note' });
  });
  el.note.addEventListener('input', () => dispatch({ type: 'typed', text: el.note.value }));
  el.note.addEventListener('blur', () => dispatch({ type: 'blur' }));
  el.second.addEventListener('change', () => dispatch({ type: 'second', on: el.second.checked }));
  el.panel.addEventListener('close', () => dispatch({ type: 'closed' }));
  el.map.addEventListener('pointerdown', onPointerDown);
  el.map.addEventListener('pointermove', onPointerMove);
  el.map.addEventListener('pointerup', onPointerUp);
  el.map.addEventListener('pointercancel', () => {
    chart.drag = null;
  });
  el.map.addEventListener('wheel', onWheel, { passive: false });
  el.known.addEventListener('scroll', readOn);
  el.record.addEventListener('scroll', readOn);
  // The map is drawn again when its box changes size, whatever changed it: the
  // window, or a line of the page that took a line more.
  if (env.ResizeObserver) new env.ResizeObserver(() => draw()).observe(el.map);

  bar();
  // The browser says when the tab goes out of view, and not that it began so.
  if (document.hidden) dispatch({ type: 'seen', seen: false });
  dispatch({ type: 'open' });

  return {
    dispatch,
    get state() {
      return state;
    },
  };
}

if (typeof document !== 'undefined' && typeof window !== 'undefined') {
  boot({
    document,
    window,
    fetch: (path, init) => window.fetch(path, init),
    now: () => Date.now(),
    setTimeout: (fn, ms) => window.setTimeout(fn, ms),
    clearTimeout: (id) => window.clearTimeout(id),
    requestAnimationFrame: (fn) => window.requestAnimationFrame(fn),
    AbortController: window.AbortController,
    ResizeObserver: window.ResizeObserver,
  });
}
