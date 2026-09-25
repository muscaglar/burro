// The panel's own code, run against the desk's own server.
//
// Every other test of the panel asks a stand-in for the desk. This one starts the
// desk itself on the loopback address, with its panel on the made-up city, hands
// the panel a stand-in for the browser, and presses what a person would. What
// came on the screen is printed as one line of JSON. It is run by
// tools/desk/tests/test_panel_at_the_desk.py, which reads that line and the file
// of changes on the disk.
//
//     node panel-at-the-desk.mjs PYTHON TOOLS DATA
//
// No browser is opened, so nothing here says how the panel looks.

import { spawn } from 'node:child_process';

import { boot } from '../../panel.mjs';
import { PANEL, browser } from './dom.mjs';

const [python, tools, data] = process.argv.slice(2);
const desk = { port: 0, child: null, printed: '' };
const asked = [];
let waiting = 0;

// Start the desk as `make desk` does, and wait until it has said where it is.
function start() {
  return new Promise((resolve, reject) => {
    const args = ['-m', 'desk', 'serve', '--data', data, '--port', '0'];
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

// Wait until nothing is on its way to the desk or back.
async function settle() {
  for (let quiet = 0, turns = 0; quiet < 5 && turns < 5000; turns += 1) {
    await new Promise((done) => setTimeout(done, 1));
    quiet = waiting === 0 ? quiet + 1 : 0;
  }
}

function screen(page) {
  return { tab: page.document.title, banner: page.text('banner'), said: page.text('said'), trouble: page.text('trouble'), main: page.text('main') };
}

async function go(page, hash) {
  page.location.hash = hash;
  page.fireWindow('hashchange');
  await settle();
  return screen(page);
}

function button(page, test) {
  return page.$('main').find((node) => node.tagName === 'BUTTON' && test(node));
}

async function confirm(page, why) {
  page.$('why').value = why;
  page.$('box-yes').click();
  await settle();
  return { open: page.$('box').open, trouble: page.text('box-trouble'), ...screen(page) };
}

await start();
const page = browser(ask, { html: PANEL });
page.app = boot(page.env);
await page.app.started;
await settle();

const out = { first: screen(page) };
out.areas = await go(page, '#/areas');
const find = page.$('main').find((node) => node.id === 'find');
find.value = 'dulcimer';
find.fire('input');
await settle();
out.found = screen(page);
out.area = await go(page, '#/area/syn-n0004');
out.measure = await go(page, '#/measure/air_no2');
out.vibe = await go(page, '#/vibe/leafy');
out.drawn = [...new Set(page.calls.map((call) => call[0]))];
out.vibes = await go(page, '#/vibes');
out.measures = await go(page, '#/measures');
// The desk was started with no other release to hold the one it shows against.
out.moved = await go(page, '#/moved');

// A figure is flagged, from the screen of its area.
await go(page, '#/area/syn-n0004');
button(page, (node) => node.parent.tagName === 'TD' && node.parent.parent.textContent.includes('Modelled annual mean nitrogen dioxide')).click();
out.asked_why = { open: page.$('box').open, of: page.text('box-of') };
out.flagged = await confirm(page, 'A made-up reason, from the panel');
out.listed = await go(page, '#/flagged');
out.home = await go(page, '#/');

// The flag is taken back, from the history.
out.history = await go(page, '#/history');
button(page, (node) => node.textContent === 'Take back').click();
out.taken_back = await confirm(page, 'A made-up reason to take it back');
out.after = await go(page, '#/flagged');

// A share of a recipe is moved, what would move is looked at, and it is kept.
const made = (id) => page.$('main').find((node) => node.id === id);
const shares = () => ['school_primary_nearby', 'play_space_proximity', 'park_proximity'].map((part) => made(`share-${part}`).value);
out.recipe = { ...(await go(page, '#/vibe/family_amenities')), shares: shares(), can_look: !made('look').disabled };
made('share-school_primary_nearby').value = '20';
made('share-school_primary_nearby').fire('input');
await settle();
out.slid = { shares: shares(), can_look: !made('look').disabled, can_keep: made('keep') !== null };
made('look').click();
await settle();
out.looked = { ...screen(page), can_keep: made('keep') !== null };
made('keep-why').value = 'A made-up reason to move a share';
made('keep-why').fire('input');
made('keep').click();
await settle();
out.kept = { ...screen(page), shares: shares() };
out.changed = await go(page, '#/');

// It is taken back, from the history, and the shares stand as they did.
await go(page, '#/history');
button(page, (node) => node.textContent === 'Take back' && node.parent.parent.textContent.includes('The shares of a recipe')).click();
out.recipe_back = await confirm(page, 'A made-up reason to put the shares back');
out.unchanged = await go(page, '#/');
out.recipe_after = { ...(await go(page, '#/vibe/family_amenities')), shares: shares() };

// A chain of the table of brands is moved to another tier.
out.brands = await go(page, '#/brands');
made('tier-lidl').value = 'premium';
button(page, (node) => node.textContent === 'Move' && node.parent.parent.textContent.startsWith('Lidl')).click();
await settle();
out.brand_looked = { open: page.$('box').open, title: page.text('box-title'), more: page.text('box-more') };
out.brand_kept = await confirm(page, 'A made-up reason to move a chain');

// A vibe is given another name, and a measure another label.
await go(page, '#/vibe/leafy');
made('name-label').value = 'Green and leafy';
function every(node, test, found = []) {
  if (test(node)) found.push(node);
  for (const child of node.children) every(child, test, found);
  return found;
}
const looks = () => every(page.$('main'), (node) => node.tagName === 'BUTTON' && node.textContent === 'Look at it');
looks()[0].click();
await settle();
out.name_looked = { open: page.$('box').open, more: page.text('box-more') };
out.name_kept = await confirm(page, 'A made-up reason to give a name');
made('name-label').value = 'Safe and leafy';
looks()[0].click();
await settle();
out.name_refused = { open: page.$('box').open, trouble: made('propose-trouble').textContent };
await go(page, '#/measure/air_no2');
made('label-short').value = 'Nitrogen dioxide';
looks()[0].click();
await settle();
out.label_kept = await confirm(page, 'A made-up reason to give a label');

// A screen the desk does not hold.
out.nowhere = await go(page, '#/area/syn-n9999');

await stop();
out.asked = asked;
out.printed = desk.printed;
process.stdout.write(`${JSON.stringify(out)}\n`);
