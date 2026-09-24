// The page's own code, run against the desk's own server.
//
// Every other test of the page asks a stand-in for the desk. This one starts the
// desk itself on the loopback address, hands the page a stand-in for the browser,
// and strikes keys. What came on the screen is printed as one line of JSON. It is
// run by tools/desk/tests/test_page_at_the_desk.py, which reads that line and the
// lines of decisions on the disk.
//
//     node at-the-desk.mjs PYTHON TOOLS DATA
//
// No browser is opened, so nothing here says how the page looks.

import { spawn } from 'node:child_process';

import { boot } from '../../desk.mjs';
import { QUEUE_KEYS } from '../../logic.mjs';
import { browser } from './dom.mjs';

const [python, tools, data] = process.argv.slice(2);
const desk = { port: 0, child: null, printed: '' };
const asked = [];
let waiting = 0;

// Start the desk as `make desk` does, and wait until it has said where it is.
function start(port) {
  return new Promise((resolve, reject) => {
    const args = ['-m', 'desk', 'serve', '--data', data, '--port', String(port)];
    const child = spawn(python, args, { env: { ...process.env, PYTHONPATH: tools }, stdio: ['ignore', 'pipe', 'pipe'] });
    let said = '';
    const hear = (chunk) => {
      said += chunk;
      desk.printed += chunk;
      const found = /Open http:\/\/127\.0\.0\.1:(\d+)\/\n[^\n]+\n/.exec(said);
      if (found) {
        desk.port = Number(found[1]);
        resolve();
      }
    };
    child.stdout.on('data', hear);
    child.stderr.on('data', hear);
    child.on('exit', () => reject(new Error(`the desk stopped: ${said}`)));
    desk.child = child;
  });
}

function stop() {
  return new Promise((resolve) => {
    const child = desk.child;
    desk.child = null;
    if (!child) return resolve();
    child.removeAllListeners('exit');
    child.on('exit', resolve);
    child.kill('SIGINT');
    return undefined;
  });
}

// What the browser does with a path: it asks the origin the page came from, and
// says that the request is the page's own.
async function ask(path, init) {
  asked.push(`${init.method} ${path}`);
  waiting += 1;
  try {
    const own = `http://127.0.0.1:${desk.port}`;
    const headers = { ...init.headers, 'Sec-Fetch-Site': 'same-origin', ...(init.method === 'POST' ? { Origin: own } : {}) };
    return await fetch(new URL(path, own), { method: init.method, headers, body: init.body, redirect: 'error', signal: init.signal });
  } finally {
    waiting -= 1;
  }
}

function open() {
  const page = browser(ask);
  page.app = boot(page.env);
  return page;
}

// Wait until nothing is on its way to the desk or back.
async function settle(page) {
  for (let quiet = 0, turns = 0; quiet < 3 && turns < 2000; turns += 1) {
    await new Promise((done) => setTimeout(done, 1));
    const state = page.app.state;
    quiet = waiting === 0 && state.pending === null && state.want === null && state.phase === 'ready' ? quiet + 1 : 0;
  }
}

async function key(page, name, fields = {}) {
  page.at += 1000;
  const on = fields.on || page.document.activeElement || page.document.body;
  on.fire('keydown', { key: name, shiftKey: false, ctrlKey: false, altKey: false, metaKey: false, repeat: false, isComposing: false, ...fields });
  await settle(page);
  // A letter is held a moment before it acts. The moment is over.
  await page.letGo();
  await settle(page);
}

async function note(page, text) {
  page.$('note').value = text;
  page.$('note').fire('input');
  await key(page, 'Enter', { on: page.$('note') });
}

// Move the cross over the map, a step at a time, until `m` gives what is wanted.
async function cross(page, wanted) {
  for (const way of ['ArrowRight', 'ArrowUp', 'ArrowLeft', 'ArrowDown']) {
    for (let steps = 0; steps < 12; steps += 1) {
      await key(page, way);
      await key(page, 'm');
      if (wanted.test(page.text('said'))) return true;
      // The cell that was taken up was put down again. Take it up once more.
      if (page.text('said') === 'Let go.') await key(page, 'm');
    }
    await key(page, '0');
  }
  return false;
}

function screen(page) {
  const shown = ['map-box', 'text-box', 'record', 'wait'].filter((id) => !page.$(id).hidden);
  return {
    item: page.app.state.now ? page.app.state.now.id : null,
    banner: page.text('banner'),
    tab: page.document.title,
    progress: page.text('progress'),
    title: page.text('title'),
    question: page.text('question'),
    answers: page.$('answers').children.map((row) => row.textContent),
    shown,
    drawn: shown[0] === 'map-box' ? page.text('map-credit') : '',
    said: page.text('said'),
    trouble: page.text('trouble'),
    list: page.$('panel').open ? page.text('panel-title') : '',
  };
}

const out = { queues: {}, claims: [], borders: [], names: [] };
await start(0);
const page = open();
await settle(page);
out.first = screen(page);
const queues = page.app.state.queues.map((row) => row.queue);

// Choose a queue from the list, by the key the list gives it.
async function choose(queue) {
  await key(page, 'q');
  await key(page, QUEUE_KEYS.charAt(queues.indexOf(queue)));
}

// Every queue: open it from the list, and give the first answer to its first item. To
// a rule the answer is no, which changes nothing: what a yes does is held by the
// tests of the desk itself, and the rest of this sitting is a person's own.
for (const queue of queues) {
  await choose(queue);
  const opened = screen(page);
  await key(page, queue === 'rules' ? '2' : '1');
  out.queues[queue] = { opened, after: screen(page) };
}

// One queue at length: a skip, a mark, a note, an undo, and the desk stopped and started.
const step = async (what, does) => {
  await does();
  out.claims.push({ what, ...screen(page) });
};
await choose('claims');
await step('skip', () => key(page, 's'));
await step('mark', async () => {
  await key(page, 'f');
  await key(page, '1');
});
await step('note', async () => {
  // The item after is answered and this one is left open, so that an undo has
  // an item to go back to that is not the first one open.
  await key(page, ']');
  await key(page, 'n');
  await note(page, 'A made-up note, from the page');
  await key(page, '2');
});
await step('undo', () => key(page, 'u'));
await step('again', () => key(page, '3'));
await stop();
await step('down', async () => {
  page.at += 1000;
  page.document.body.fire('keydown', { key: '4', shiftKey: false, ctrlKey: false, altKey: false, metaKey: false, repeat: false, isComposing: false });
  for (let turns = 0; turns < 2000 && page.text('trouble') === ''; turns += 1) await new Promise((done) => setTimeout(done, 1));
});
out.unsaved = page.fireWindow('beforeunload').defaultPrevented;
await start(desk.port);
await step('back', async () => {
  for (let tries = 0; tries < 8 && page.app.state.pending !== null; tries += 1) {
    await page.wait();
    await settle(page);
  }
});

// A border: a cell moved with no mouse, and the answer after it, which needs a note.
const border = async (what, does) => {
  await does();
  out.borders.push({ what, moves: page.text('moves'), note: page.app.state.noteOpen, ...screen(page) });
};
await choose('borders');
await border('taken', () => key(page, 'm'));
await border('moved', () => cross(page, /^Moved\./));
await border('asked', () => key(page, '1'));
await border('answered', () => note(page, 'A made-up reason, from the page'));

// A name: one that needs its area named, and the area named with no mouse.
const name = async (what, does) => {
  await does();
  out.names.push({ what, of: page.text('of'), ...screen(page) });
};
await choose('names');
await name('asked', () => key(page, '2'));
await name('own', () => key(page, 'm'));
await name('named', () => cross(page, /^Area chosen\./));
await name('answered', () => key(page, '2'));

// The page is loaded again: it opens where the person left off.
const again = open();
await settle(again);
out.again = screen(again);

await stop();
out.asked = asked;
out.printed = desk.printed;
process.stdout.write(`${JSON.stringify(out)}\n`);
