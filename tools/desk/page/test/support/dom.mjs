// A stand-in for the browser, for the page's tests: as much of a document as
// desk.mjs touches, and no more. It is read from index.html itself, so a test
// fails when the page asks for an element the file does not hold.
//
// It lays nothing out and draws nothing. What a browser shows is for a person
// to look at.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const VOID = new Set(['meta', 'link', 'input', 'br', 'hr', 'img']);

class Node {
  constructor(tag, page) {
    this.tagName = tag.toUpperCase();
    this.page = page;
    this.parent = null;
    this.nodes = []; // elements and strings
    this.attrs = new Map();
    this.listeners = new Map();
    this.value = '';
    this.checked = false;
    this.disabled = false;
    this.open = false;
    this.width = 300;
    this.height = 150;
    this.clientWidth = 800;
    this.clientHeight = 600;
    // Nothing is laid out, so nothing is ever taller than its box unless a test says so.
    this.scrollHeight = 0;
    this.scrollTop = 0;
  }

  get id() {
    return this.attrs.get('id') || '';
  }

  get children() {
    return this.nodes.filter((node) => node instanceof Node);
  }

  get className() {
    return this.attrs.get('class') || '';
  }

  set className(value) {
    this.attrs.set('class', String(value));
  }

  get hidden() {
    return this.attrs.has('hidden');
  }

  set hidden(value) {
    if (value) this.attrs.set('hidden', '');
    else this.attrs.delete('hidden');
  }

  get textContent() {
    return this.nodes.map((node) => (node instanceof Node ? node.textContent : node)).join('');
  }

  set textContent(value) {
    for (const node of this.children) node.parent = null;
    this.nodes = value === '' ? [] : [String(value)];
  }

  set innerHTML(value) {
    throw new Error(`the page wrote markup: ${value}`);
  }

  setAttribute(name, value) {
    if (name === 'style' || name.startsWith('on')) throw new Error(`the page set the attribute ${name}`);
    this.attrs.set(name, String(value));
  }

  getAttribute(name) {
    return this.attrs.has(name) ? this.attrs.get(name) : null;
  }

  removeAttribute(name) {
    this.attrs.delete(name);
  }

  append(...nodes) {
    for (const node of nodes) {
      if (node instanceof Node) {
        node.remove();
        node.parent = this;
      }
      this.nodes.push(node instanceof Node ? node : String(node));
    }
  }

  remove() {
    if (this.parent === null) return;
    this.parent.nodes = this.parent.nodes.filter((node) => node !== this);
    this.parent = null;
    if (this.page.document.activeElement === this || this.contains(this.page.document.activeElement)) {
      this.page.document.activeElement = this.page.document.body;
    }
  }

  replaceChildren(...nodes) {
    for (const node of this.children) node.remove();
    this.nodes = [];
    this.append(...nodes);
  }

  contains(other) {
    for (let node = other; node; node = node.parent) if (node === this) return true;
    return false;
  }

  addEventListener(type, fn) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(fn);
  }

  // Tell the element something happened. It is told to each element above it
  // too, and then to the document, as a browser does.
  fire(type, fields = {}) {
    const event = {
      type,
      target: this,
      defaultPrevented: false,
      preventDefault() {
        this.defaultPrevented = true;
      },
      ...fields,
    };
    for (let node = this; node; node = node.parent) {
      for (const fn of node.listeners.get(type) || []) fn(event);
      if (type === 'focus' || type === 'blur' || type === 'close') break;
    }
    if (type !== 'focus' && type !== 'blur' && type !== 'close') {
      for (const fn of this.page.document.listeners.get(type) || []) fn(event);
    }
    return event;
  }

  focus() {
    const document = this.page.document;
    if (this.disabled || document.activeElement === this) return;
    const before = document.activeElement;
    document.activeElement = this;
    if (before && before !== document.body) before.fire('blur');
    this.fire('focus');
  }

  click() {
    if (!this.disabled) this.fire('click');
  }

  showModal() {
    if (this.open) throw new Error('the list was opened twice');
    this.open = true;
  }

  close() {
    if (!this.open) return;
    this.open = false;
    if (this.contains(this.page.document.activeElement)) this.page.document.activeElement = this.page.document.body;
    this.fire('close');
  }

  getContext() {
    return this.page.ctx;
  }

  getBoundingClientRect() {
    return { left: 0, top: 0, width: this.clientWidth, height: this.clientHeight };
  }

  setPointerCapture() {}

  find(test) {
    if (test(this)) return this;
    for (const node of this.children) {
      const found = node.find(test);
      if (found) return found;
    }
    return null;
  }
}

function parse(html, page) {
  const root = new Node('#root', page);
  const open = [root];
  const token = /<!--[\s\S]*?-->|<!doctype[^>]*>|<\/([\w-]+)\s*>|<([\w-]+)((?:\s+[\w-]+(?:\s*=\s*"[^"]*")?)*)\s*\/?>|([^<]+)/gi;
  for (const [, closing, tag, attrs, text] of html.matchAll(token)) {
    const top = open[open.length - 1];
    if (closing) {
      while (open.length > 1 && open[open.length - 1].tagName !== closing.toUpperCase()) open.pop();
      if (open.length > 1) open.pop();
    } else if (tag) {
      const node = new Node(tag, page);
      for (const [, name, value] of (attrs || '').matchAll(/([\w-]+)(?:\s*=\s*"([^"]*)")?/g)) node.attrs.set(name, value || '');
      node.parent = top;
      top.nodes.push(node);
      if (!VOID.has(tag.toLowerCase())) open.push(node);
    } else if (text && text.trim() !== '') {
      top.nodes.push(text.replace(/\s+/g, ' ').trim());
    }
  }
  return root;
}

export const HTML = readFileSync(fileURLToPath(new URL('../../index.html', import.meta.url)), 'utf8');

// The page, as desk.mjs is handed it. `fetch` is the desk's, or a stand-in's.
export function browser(fetch, options = {}) {
  const page = { calls: [], timers: [], at: options.at === undefined ? 100000 : options.at, dark: options.dark === true };
  page.ctx = new Proxy(
    {},
    {
      get: (target, name) => (name in target ? target[name] : (...args) => page.calls.push([name, ...args])),
      set: (target, name, value) => {
        target[name] = value;
        page.calls.push(['set', name, value]);
        return true;
      },
    },
  );
  const root = parse(HTML, page);
  const listeners = new Map();
  page.document = {
    listeners,
    title: '',
    hidden: false,
    body: root.find((node) => node.tagName === 'BODY'),
    activeElement: null,
    getElementById: (id) => {
      const found = root.find((node) => node.id === id);
      if (!found) throw new Error(`index.html holds no element with the id ${id}`);
      return found;
    },
    createElement: (tag) => new Node(tag, page),
    addEventListener: (type, fn) => {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(fn);
    },
  };
  page.document.activeElement = page.document.body;
  const windowListeners = new Map();
  page.window = {
    devicePixelRatio: 2,
    matchMedia: () => ({ matches: page.dark, addEventListener() {} }),
    addEventListener: (type, fn) => {
      if (!windowListeners.has(type)) windowListeners.set(type, []);
      windowListeners.get(type).push(fn);
    },
  };
  page.fireWindow = (type) => {
    const event = { type, defaultPrevented: false, returnValue: undefined, preventDefault() { this.defaultPrevented = true; } };
    for (const fn of windowListeners.get(type) || []) fn(event);
    return event;
  };
  page.env = {
    document: page.document,
    window: page.window,
    fetch,
    now: () => page.at,
    setTimeout: (fn, ms) => {
      const id = page.timers.length + 1;
      page.timers.push({ id, fn, ms, due: page.at + ms, done: false });
      return id;
    },
    clearTimeout: (id) => {
      const timer = page.timers.find((one) => one.id === id);
      if (timer) timer.done = true;
    },
    requestAnimationFrame: (fn) => fn(),
    AbortController,
  };

  page.$ = (id) => page.document.getElementById(id);
  page.text = (id) => page.$(id).textContent;
  // Let every answer that is on its way arrive.
  page.settle = async () => {
    for (let i = 0; i < 20; i += 1) await new Promise((done) => setImmediate(done));
  };
  // Strike a key, a moment after the last thing happened.
  page.key = async (key, fields = {}) => {
    page.at += fields.soon ? 0 : 1000;
    const target = fields.on || page.document.activeElement || page.document.body;
    const event = target.fire('keydown', { key, shiftKey: false, ctrlKey: false, altKey: false, metaKey: false, repeat: false, isComposing: false, ...fields });
    await page.settle();
    await page.letGo();
    return event;
  };
  // Time passes. A key that was held is let go when its moment is over, as a
  // browser's own clock would let it go.
  page.pass = async (ms) => {
    const to = page.at + ms;
    for (;;) {
      const due = page.timers.filter((one) => !one.done && one.ms < 1000 && one.due <= to).sort((a, b) => a.due - b.due)[0];
      if (!due) break;
      due.done = true;
      page.at = Math.max(page.at, due.due);
      due.fn();
      await page.settle();
    }
    page.at = to;
  };
  // Strike the keys of some words one after another, as a person types: each
  // goes through the page's own listener, and none is let go before its time.
  page.strike = async (words, gap = 120) => {
    const events = [];
    for (const key of words) {
      await page.pass(gap);
      const target = page.document.activeElement || page.document.body;
      events.push(target.fire('keydown', { key, shiftKey: false, ctrlKey: false, altKey: false, metaKey: false, repeat: false, isComposing: false }));
      await page.settle();
    }
    return events;
  };
  // The moment for which a letter is held is over.
  page.letGo = async () => {
    for (const timer of page.timers.filter((one) => !one.done && one.ms < 1000)) {
      timer.done = true;
      page.at += timer.ms;
      timer.fn();
    }
    await page.settle();
  };
  // Run the waits that are over: those for a retry, and not those that only
  // give up on an answer.
  page.wait = async () => {
    for (const timer of page.timers.filter((one) => !one.done && one.ms < 15000)) {
      timer.done = true;
      page.at += timer.ms;
      timer.fn();
    }
    await page.settle();
  };
  page.type = async (text) => {
    const note = page.$('note');
    note.value = text;
    note.fire('input');
    await page.settle();
  };
  page.answers = () => page.$('answers').children.map((row) => row.textContent);
  return page;
}
