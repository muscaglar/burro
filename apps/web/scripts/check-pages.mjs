// Reads every page the build wrote, as a browser would be sent it, and fails
// on what a person or a screen reader would trip over.
//
//   node scripts/check-pages.mjs     after `npm run build`
//
// The tests draw each page in a stand-in for a browser. This reads what was
// built: the language, the title and what a search engine is told are only
// there. It checks structure and words. It cannot see a page, so it says
// nothing of layout, colour or size.
//
// It also counts what the search page and an area's page hold before anything
// is opened. The heights the pages are held to were measured in a browser, and
// are in docs/design/web.md, section 4.1. They stand only while no more is drawn
// at first than was measured, so a page that draws more fails here.

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

// The parser is the one the tests draw pages with. It is found through the
// package that brings it, so that no package is named here that is not asked for.
const require = createRequire(import.meta.url);
const { JSDOM } = createRequire(require.resolve("jest-environment-jsdom"))("jsdom");

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", ".next", "server", "app");
// The files of the website's own, which a page may ask for by name.
const PUBLIC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "public");
const BANNER = "This is made-up test data.";
const PREVIEW_BANNER = "This is a preview for the people who build Burro.";
// The page a fault in the server shows before anything is drawn. It is the framework's
// own and is built whatever the website holds, so it is not the website's to be held to.
// docs/design/web.md, section 12, says what it lacks.
const NOT_OURS = new Set(["_global-error.html"]);
// What the search page may hold before a search, as it is built: docs/design/web.md, section 4.1.
// The first screen offers two ways in, as two tabs, the first of them chosen: the box, with
// one line of helpers under it, each closed until it is pressed. Built, it draws 13
// controls: two links that skip, the two tabs, the box and Search, two helpers, and five
// of the map. It drew one more while a button stood by the rabbit, and 15 while the way
// to how words are handled stood beside the box: the founder had each go. It was 30 at
// most while the shelf, the tenure, the place field and the examples stood open.
// The panel of the second way is in the page and holds nothing until its tab is pressed.
// What the helpers hold, and the second way, are kept in the page for a browser with
// scripts off, which no button can open anything for, each way under its name. The helpers
// keep 11 controls, of which eight at most are words of the shelf. What the second way
// keeps is the settings', and is theirs to count.
// A page is built with no screen to ask, so it is built as for a screen of one column,
// where the map stands over the two ways in: it is what a phone draws before any script
// has run, and nothing moves there once one has. On a wide screen every part has its
// column and its row by name, and the page puts the map after the two ways in once it runs.
const AT_FIRST = { controls: 13, ways: 2, helpers: 2, kept: 11, words: 8 };
// What stood beside the box and under it, and is said there no longer: that what is typed is
// sent or read, by whom, and the way to how words are handled.
const OF_WHO_READS = /What you type is (sent|read)|language model|words are handled/i;
const CONTROLS = "a[href], button, input, select, textarea";
// What is drawn only by a browser with scripts off.
const KEPT = "noscript";
// What the page of an area may draw before anything is opened: docs/design/web.md, section 4.2.
// Measured on the made-up release: 151 lines and 32 controls at the most, with 11 vibes. The
// portrait opens with what the area is like in short, five lines at most, and where it is.
// With 12 vibes the most was 161 lines. The census of an area is closed at first and draws three
// lines, so the most was 164. Neither was measured again. With 14 vibes, Well connected and the
// two that count who lived there among them, and with the chains of grocers, gyms and coffee,
// what "Go and look" says of an area grew, and the household income of an area is a part that
// is closed at first: the most is 190 lines and 40 controls, of the centre. That was not
// measured in a browser either.
const AREA_AT_FIRST = { lines: 190, controls: 40, vibes: 14, short: 5 };
const LINES = "h1, h2, h3, h4, p, li, summary, dt, dd";
// The parts of the page of an area that are closed until they are pressed.
const AREA_CLOSED = ["alike", "cost", "measured", "sources"];
// The part that offers the census figures of an area. The figures are asked for when it is
// opened, and are in no page as it is built: not in what is drawn, and not in what the page
// hands its scripts.
const CENSUS = "census";
const OF_A_CENSUS = /fewer than 1 in 100|over 99%/;
// What the service says of the vibes it calls a rough guide, by the name of its part of
// route 11: a label and a sentence for each. The founder asked that neither is passed on.
// No page drew either, and a page that was handed the whole of route 11 held both, in what
// it hands its scripts. It is read by the name of the part, and not by its words, which
// are the service's to change.
const OF_A_ROUGH_GUIDE = /rough_guides/;

/** True for what is drawn while every part that opens is closed: what no such part holds, and what opens one. */
function drawnAtFirst(element) {
  const held = element.closest("details");
  if (held === null) return true;
  const opens = element.closest("summary");
  return opens !== null && opens.parentElement === held && held.parentElement.closest("details") === null;
}

function pagesUnder(folder) {
  return readdirSync(folder)
    .flatMap((name) => {
      const full = path.join(folder, name);
      if (statSync(full).isDirectory()) return pagesUnder(full);
      return name.endsWith(".html") && !NOT_OURS.has(name) ? [full] : [];
    })
    .sort();
}

function nameOf(element, document) {
  const labelled = (element.getAttribute("aria-labelledby") ?? "")
    .split(/\s+/)
    .map((id) => (id === "" ? "" : (document.getElementById(id)?.textContent ?? "")))
    .join(" ")
    .trim();
  if (labelled) return labelled;
  const label = (element.getAttribute("aria-label") ?? "").trim();
  if (label) return label;
  if (element.id) {
    const named = document.querySelector(`label[for="${element.id}"]`);
    if (named) return named.textContent.trim();
  }
  const around = element.closest("label");
  if (around) return around.textContent.trim();
  if (element.tagName === "IMG") return (element.getAttribute("alt") ?? "").trim();
  if (element.tagName.toLowerCase() === "svg") return element.querySelector("title")?.textContent?.trim() ?? "";
  if (element.tagName === "TABLE") return element.querySelector("caption")?.textContent?.trim() ?? "";
  return (element.textContent ?? "").replace(/\s+/g, " ").trim();
}

function faultsOf(file) {
  const page = path.relative(ROOT, file);
  const built = readFileSync(file, "utf8");
  const { window } = new JSDOM(built);
  try {
    const found = faultsIn(page, window.document);
    // Read from the file itself, so that what a script holds is read with what is drawn.
    if (OF_A_CENSUS.test(built)) found.faults.push("a figure of the census is in the page as it is built");
    if (OF_A_ROUGH_GUIDE.test(built)) {
      found.faults.push("what the service says of a rough guide is in the page as it is built");
    }
    return found;
  } finally {
    // A page that is kept open is kept in memory. A release of all of London has a
    // thousand pages, and the check ran out of room before it had read them.
    window.close();
  }
}

function faultsIn(page, document) {
  const faults = [];
  const say = (fault) => faults.push(fault);

  const body = document.body.cloneNode(true);
  for (const one of body.querySelectorAll("script, style, template")) one.remove();
  const text = body.textContent.replace(/\s+/g, " ");
  const count = (selector) => body.querySelectorAll(selector).length;

  // What the document says of itself.
  if (document.documentElement.getAttribute("lang") !== "en-GB") say("the page does not say it is in British English");
  const title = (document.querySelector("title")?.textContent ?? "").trim();
  if (title === "") say("the page has no title");
  const viewport = document.querySelector('meta[name="viewport"]')?.getAttribute("content") ?? "";
  if (/user-scalable\s*=\s*no|maximum-scale\s*=\s*1(\D|$)/.test(viewport)) say("the page cannot be zoomed");
  const robots = document.querySelector('meta[name="robots"]')?.getAttribute("content") ?? "";

  // Headings, in order.
  const headings = [...body.querySelectorAll("h1, h2, h3, h4, h5, h6")];
  const levels = headings.map((heading) => Number(heading.tagName[1]));
  if (levels.filter((level) => level === 1).length !== 1) say("the page does not have one main heading");
  if (levels[0] !== 1) say("the first heading is not the main heading");
  levels.forEach((level, at) => {
    if (at > 0 && level > (levels[at - 1] ?? 0) + 1) {
      say(`a heading skips a level: "${headings[at].textContent.trim().slice(0, 60)}"`);
    }
  });
  if (headings.some((heading) => heading.textContent.trim() === "")) say("a heading is empty");

  // Landmarks, and the way past them.
  if (count("main") !== 1) say("the page does not have one main landmark");
  if (count("header") < 1) say("the page has no header");
  if (count("footer") < 1) say("the page has no footer");
  if (count("nav") < 1) say("the page has no navigation");
  const first = body.querySelector("a[href], button, input, select, textarea");
  const target = first?.getAttribute("href") ?? "";
  if (!target.startsWith("#") || document.getElementById(target.slice(1)) === null) {
    say("the first thing a keyboard reaches is not a link to the page itself");
  }
  const navs = [...body.querySelectorAll("nav")].map(
    (nav) =>
      (nav.getAttribute("aria-label") ?? "").trim() ||
      (document.getElementById(nav.getAttribute("aria-labelledby") ?? "")?.textContent ?? "").trim(),
  );
  if (navs.length > 1 && (navs.some((name) => name === "") || new Set(navs).size !== navs.length)) {
    say("two navigations cannot be told apart by name");
  }

  // Names: every link, control, picture and table has one.
  for (const link of body.querySelectorAll("a")) {
    const name = nameOf(link, document);
    const href = link.getAttribute("href");
    if (href === null || href === "") say(`a link leads nowhere: "${name.slice(0, 40)}"`);
    if (name === "") say(`a link has no words: ${href}`);
    if (/^(click here|here|read more|more|link|this)$/i.test(name)) say(`a link's words say nothing: "${name}"`);
    if (/^https?:/.test(href ?? "") && !(link.getAttribute("rel") ?? "").split(/\s+/).includes("noreferrer")) {
      say(`a link to another site tells it where the person came from: ${href}`);
    }
    if (href?.startsWith("#") && href.length > 1 && document.getElementById(decodeURIComponent(href.slice(1))) === null) {
      say(`a link leads to a part of the page that is not there: ${href}`);
    }
  }
  for (const control of body.querySelectorAll("input:not([type=hidden]), select, textarea")) {
    if (nameOf(control, document) === "") say(`a field has no label: ${control.outerHTML.slice(0, 80)}`);
  }
  for (const button of body.querySelectorAll("button")) {
    if (nameOf(button, document) === "") say("a button has no name");
    if (!button.hasAttribute("type")) say(`a button does not say what kind it is: "${nameOf(button, document).slice(0, 40)}"`);
  }
  for (const form of body.querySelectorAll("form")) {
    if ((form.getAttribute("method") ?? "get").toLowerCase() !== "post") say("a form could put what is typed in the address");
  }
  for (const fieldset of body.querySelectorAll("fieldset")) {
    if (fieldset.querySelector("legend") === null) say("a group of fields has no legend");
  }
  for (const image of body.querySelectorAll("img")) {
    if (!image.hasAttribute("alt")) say("a picture has no words in its place");
  }
  for (const picture of body.querySelectorAll("svg")) {
    const hidden = picture.closest("[aria-hidden='true']") !== null;
    if (!hidden && nameOf(picture, document) === "") say("a drawing is neither named nor hidden from a reader");
  }
  for (const table of body.querySelectorAll("table")) {
    if (nameOf(table, document) === "") say("a table does not say what it is a table of");
    if (table.querySelector("th") === null) say("a table has no header cell");
  }

  // Ids, and what points at them.
  const ids = [...document.querySelectorAll("[id]")].map((one) => one.id);
  const twice = [...new Set(ids.filter((id, at) => ids.indexOf(id) !== at))];
  if (twice.length > 0) say(`an id is used twice: ${twice.slice(0, 3).join(", ")}`);
  for (const attribute of ["aria-labelledby", "aria-describedby", "aria-controls"]) {
    for (const one of body.querySelectorAll(`[${attribute}]`)) {
      for (const id of (one.getAttribute(attribute) ?? "").split(/\s+/).filter(Boolean)) {
        if (document.getElementById(id) === null) say(`${attribute} names what is not on the page`);
      }
    }
  }
  if (count("[tabindex]:not([tabindex='0']):not([tabindex='-1'])") > 0) say("the order of the keyboard is set by hand");

  // Words that must not be shipped.
  const WORDS = [
    ["filler text", /lorem|ipsum/i],
    ["a note to self", /\bTODO\b|\bFIXME\b|\bTBD\b|\bXXX\b/],
    ["a placeholder", /placeholder|coming soon|not built yet|under construction/i],
    ["a value that was never filled in", /\bundefined\b|\[object Object\]|\bNaN\b/],
    ["a template that was never filled in", /\{\{|\}\}|\$\{/],
    ["an exclamation mark", /!/],
  ];
  for (const [what, pattern] of WORDS) {
    const found = pattern.exec(text);
    if (found) say(`${what}: "${text.slice(Math.max(0, found.index - 40), found.index + 40).trim()}"`);
  }

  // The face of names is asked for with the page: every page draws its name board in it, and
  // a page that asks for it once its style sheets have come jumps as the face arrives. It is
  // asked for as a style sheet asks for a face, or a browser fetches it a second time.
  const ahead = [...document.querySelectorAll("link[rel='preload'][as='font']")];
  if (ahead.length === 0) say("the page asks for no face ahead of its style sheets, and jumps as the face of names comes");
  for (const face of ahead) {
    const file = face.getAttribute("href") ?? "";
    if (!/^\/fonts\/[a-z0-9-]+\.woff2$/.test(file) || !existsSync(path.join(PUBLIC, file))) {
      say(`the page asks ahead for a face that is not there: ${file}`);
    }
    if (!face.hasAttribute("crossorigin")) say(`a face is asked for ahead in a way that has it fetched twice: ${file}`);
  }

  // An icon of the website's own. With none named, a browser asks for one that is not there.
  const icon = document.querySelector('link[rel~="icon"]')?.getAttribute("href") ?? "";
  if (!icon.startsWith("/") || icon.startsWith("//")) say("the page names no icon of the website's own");

  // What is drawn before anything is opened.
  const main = body.querySelector("main");
  if (page === "index.html" && main !== null) {
    // This reads a page as a browser with scripts off does, so what is kept for one is in
    // it as the rest is. A browser with scripts on draws none of that.
    const drawn = (selector, within = main) =>
      [...within.querySelectorAll(selector)].filter((one) => one.closest(KEPT) === null);
    const kept = (selector) => [...main.querySelectorAll(KEPT)].flatMap((part) => [...part.querySelectorAll(selector)]);
    // A part of the page by its id, as the page that is read here holds it.
    const named = (id) => (id === null || id === "" ? null : main.querySelector(`[id="${id.replace(/"/g, '\\"')}"]`));
    const controls = drawn(CONTROLS).length;
    if (controls > AT_FIRST.controls) {
      say(`the search page draws ${controls} controls before a search, and may draw ${AT_FIRST.controls}`);
    }
    // What is kept for a browser with scripts off may hold a part that stands open, as a
    // group of the settings may: no browser with scripts on draws it.
    if (drawn("[aria-expanded='true'], details[open]").length > 0) {
      say("something on the search page is open before anything is pressed");
    }
    if (main.querySelector("article, table") !== null) say("the search page holds a result or a table before a search");

    // Two ways in, as tabs: one list of them, each a tab that says whether it is chosen and
    // names the panel it shows. The first is chosen. The panel of a tab that is not chosen
    // is in the page, so that the tab names something, is not drawn, and holds nothing.
    const box = drawn("textarea")[0];
    // Nothing beside the box says who reads what is typed, as the page is built: not in
    // what is drawn, and not in what is kept for a browser with scripts off.
    const form = box?.closest("form") ?? null;
    if (form !== null && OF_WHO_READS.test(form.textContent ?? "")) {
      say("the box of the search page says who reads what is typed, or leads to how words are handled");
    }
    if (form !== null && form.querySelector("a[href]") !== null) say("a link stands in the box of the search page");
    const lists = drawn("[role='tablist']");
    const tabs = lists.flatMap((list) => [...list.querySelectorAll("[role='tab']")]);
    if (box === undefined) say("the search page has no box to type in");
    if (lists.length !== 1) say("the search page does not have one list of tabs");
    const map = named("panel-map");
    if (map === null) say("the search page holds no map before a search");
    else if (lists.some((list) => !(map.compareDocumentPosition(list) & 4))) {
      say("the map does not stand over the two ways in, in the page as it is built");
    }
    if (lists.some((list) => nameOf(list, document) === "")) say("the list of tabs has no name");
    if (lists.some((list) => [...list.children].some((one) => one.getAttribute("role") !== "tab"))) {
      say("something that is no tab stands in the list of tabs");
    }
    if (tabs.length !== AT_FIRST.ways) say(`the search page offers ${tabs.length} ways in, and offers ${AT_FIRST.ways}`);
    if (tabs.map((tab) => tab.getAttribute("aria-selected")).join() !== ["true", ...tabs.slice(1).map(() => "false")].join()) {
      say("the first way in is not the one that is chosen as the page is built");
    }
    if (box !== undefined && lists.some((list) => !(list.compareDocumentPosition(box) & 4))) {
      say("the tabs of the search page do not stand over the box");
    }
    for (const tab of tabs) {
      const name = nameOf(tab, document).slice(0, 40);
      const chosen = tab.getAttribute("aria-selected") === "true";
      const panel = named(tab.getAttribute("aria-controls"));
      if (tab.tagName !== "BUTTON") say(`a tab is no button: "${name}"`);
      if (tab.getAttribute("tabindex") !== (chosen ? "0" : "-1")) say(`a keyboard does not stop at the chosen tab alone: "${name}"`);
      if (panel === null || panel.getAttribute("role") !== "tabpanel" || panel.getAttribute("aria-labelledby") !== tab.id) {
        say(`a tab names no panel that is named by it: "${name}"`);
        continue;
      }
      if (panel.closest(KEPT) !== null) say(`the panel of a tab is kept for a browser with scripts off alone: "${name}"`);
      if (chosen && (panel.hasAttribute("hidden") || (box !== undefined && !panel.contains(box)))) {
        say(`the panel of the chosen tab is not drawn, or does not hold the box: "${name}"`);
      }
      if (!chosen && (!panel.hasAttribute("hidden") || panel.childNodes.length > 0)) {
        say(`the panel of a tab that is not chosen is drawn before it is pressed: "${name}"`);
      }
      // With scripts off no tab can be pressed, and each way stands under its name.
      if (!kept("h2").some((heading) => heading.textContent.trim() === nameOf(tab, document))) {
        say(`a way in does not stand under its name for a browser with scripts off: "${name}"`);
      }
    }

    // Under the box, one line of helpers, each closed. A helper is a button that says
    // whether it is open and names the part it opens.
    const lines = drawn("[role='group']").filter((group) => {
      const held = [...group.querySelectorAll("button")];
      return (
        held.length > 0 &&
        held.length === group.querySelectorAll(CONTROLS).length &&
        held.every((one) => one.hasAttribute("aria-expanded") && one.hasAttribute("aria-controls"))
      );
    });
    const helpers = lines.flatMap((line) => [...line.querySelectorAll("button")]);
    if (lines.length !== 1) say("the search page does not have one line of helpers under the box");
    if (helpers.length > AT_FIRST.helpers) {
      say(`the search page holds ${helpers.length} helpers, and may hold ${AT_FIRST.helpers}`);
    }
    if (box !== undefined && lines.some((line) => !(box.compareDocumentPosition(line) & 4))) {
      say("the helpers of the search page do not stand under the box");
    }
    if (lines.some((line) => nameOf(line, document) === "")) say("the line of helpers has no name");
    for (const helper of helpers) {
      const name = nameOf(helper, document).slice(0, 40);
      const opens = named(helper.getAttribute("aria-controls"));
      if (helper.getAttribute("aria-expanded") !== "false") say(`a helper does not say that it is closed: "${name}"`);
      if (opens === null || !opens.hasAttribute("hidden") || opens.childNodes.length > 0) {
        say(`what a helper opens is drawn before it is pressed: "${name}"`);
      }
      if (opens !== null && lines.some((line) => !(line.compareDocumentPosition(opens) & 4) || line.contains(opens))) {
        say(`what a helper opens does not stand under the line of helpers: "${name}"`);
      }
    }
    // What a helper holds, and what the second way holds, is drawn by no browser with
    // scripts on until it is pressed.
    const wordsIn = (parts) =>
      parts
        .filter((part) => part.querySelector("h2") !== null && part.querySelectorAll(":scope > ul > li > button").length > 0)
        .map((part) => part.querySelectorAll(":scope > ul > li > button").length);
    if (wordsIn(drawn("section")).length > 0 || drawn("input, select").length > 0) {
      say("something a helper or the second way in holds stands open on the search page before it is pressed");
    }

    // With scripts off no button can open a helper, so what each holds is kept in the page,
    // beside the line: one part for each helper, and none of them empty.
    const beside = lines.flatMap((line) => [...(line.parentElement?.querySelectorAll(`:scope > ${KEPT}`) ?? [])]);
    const parts = beside.flatMap((part) => [...part.querySelectorAll(":scope > div > div")]);
    const keptBeside = (selector) => beside.flatMap((part) => [...part.querySelectorAll(selector)]);
    if (helpers.length > 0 && parts.length !== helpers.length) {
      say(`the search page holds ${helpers.length} helpers, and keeps ${parts.length} parts for a browser with scripts off`);
    }
    if (parts.some((part) => part.querySelector(CONTROLS) === null)) {
      say("a part that is kept for a browser with scripts off holds nothing to use");
    }
    if (lines.some((line) => beside.some((part) => !(line.compareDocumentPosition(part) & 4)))) {
      say("what is kept for a browser with scripts off does not stand under the line of helpers");
    }
    if (keptBeside(CONTROLS).length > AT_FIRST.kept) {
      say(
        `the helpers keep ${keptBeside(CONTROLS).length} controls for a browser with scripts off, and may keep ${AT_FIRST.kept}`,
      );
    }
    if (wordsIn(keptBeside("section")).some((count) => count > AT_FIRST.words)) {
      say(`the shelf holds more than ${AT_FIRST.words} buttons before "more" is pressed`);
    }
    // And the second way in is kept under the first: what it says of itself, the settings,
    // which ask renting or buying and the place to reach, what ranks by them, and the field
    // that finds an area by its name.
    const second = [...main.querySelectorAll(KEPT)].filter((part) => !beside.includes(part) && part.querySelector(CONTROLS) !== null);
    if (tabs.length > 1 && second.length !== tabs.length - 1) {
      say(`the search page keeps ${second.length} ways in for a browser with scripts off, beside the first`);
    }
    for (const way of second) {
      if (box !== undefined && !(box.compareDocumentPosition(way) & 4)) {
        say("a way in that is kept for a browser with scripts off does not stand under the box");
      }
      if (way.querySelector("input[type='text']") === null) {
        say("the search page keeps no field that finds by name for a browser with scripts off");
      }
      if (way.querySelectorAll("input[type='radio']").length < 2) {
        say("the search page keeps no choice of renting or buying for a browser with scripts off");
      }
      if (way.querySelector("section[aria-labelledby] button") === null) {
        say("the search page keeps no settings for a browser with scripts off");
      }
    }
  }
  const closedAtFirst = body.querySelectorAll("details");
  for (const part of closedAtFirst) {
    if (part.hasAttribute("open")) say("a part that is closed until it is pressed was built open");
    if (part.querySelector(":scope > summary") === null) say("a part that opens has nothing to open it by");
  }
  if (/^(synthetic|london)\/.+\.html$/.test(page) && main !== null) {
    for (const id of AREA_CLOSED) {
      if (main.querySelector(`details#${id}`) === null) {
        say(`the page of an area has no part "${id}" that is closed until it is pressed`);
      }
    }
    const census = main.querySelector(`details#${CENSUS}`);
    if (census !== null) {
      if (census.querySelector("table, td, svg") !== null || /\d\s?%/.test(census.textContent)) {
        say("the census figures are in the page of an area as it is built");
      }
      if (!census.hasAttribute("data-nosnippet")) say("the part that offers the census may be quoted by a search engine");
      if (census.querySelector("noscript") === null) {
        say("the part that offers the census says nothing to a browser with scripts off");
      }
      if (census.querySelector("a[href], button, input, select") !== null) {
        say("the part that offers the census holds a control before it is opened");
      }
    }
    for (const page of document.querySelectorAll("table caption")) {
      if (/census/i.test(page.textContent)) say("a table of the census is in a page as it is built");
    }
    const parts = [...main.querySelectorAll("article h2")].filter((heading) => drawnAtFirst(heading));
    if (parts[0]?.id !== "character") say("the page of an area does not open with the portrait");
    // The tray of areas to compare is at the foot of the screen, and is no part of the page's order.
    const ordered = parts.filter((heading) => heading.closest("[data-closed]") === null);
    if (ordered.at(-1)?.id !== "look") say("the page of an area does not end with where to go and look");
    // What opens the sources of what is said in short is no vibe, and is not counted as one.
    const vibes = [...main.querySelectorAll("section[aria-labelledby='character'] details")].filter(
      (opens) => opens.closest("[aria-labelledby='character-short']") === null,
    ).length;
    if (vibes === 0) say("the portrait of an area holds no vibe");
    if (vibes > AREA_AT_FIRST.vibes) say(`the portrait holds ${vibes} vibes, and may hold ${AREA_AT_FIRST.vibes}`);
    const short = main.querySelector("section[aria-labelledby='character'] [aria-labelledby='character-short']");
    if (short === null) say("the portrait of an area does not open with what the area is like in short");
    const said = short?.querySelectorAll("li").length ?? 0;
    if (said > AREA_AT_FIRST.short) {
      say(`what an area is like in short is ${said} lines, and may be ${AREA_AT_FIRST.short}`);
    }
    if (main.querySelector("section[aria-labelledby='character'] [aria-labelledby='where']") === null) {
      say("the portrait of an area does not say where the area is");
    }
    const lines = [...main.querySelectorAll(LINES)].filter(drawnAtFirst).length;
    if (lines > AREA_AT_FIRST.lines) {
      say(`the page of an area draws ${lines} lines before anything is opened, and may draw ${AREA_AT_FIRST.lines}`);
    }
    const controls = [...main.querySelectorAll("a[href], button, summary")].filter(drawnAtFirst).length;
    if (controls > AREA_AT_FIRST.controls) {
      say(`the page of an area holds ${controls} controls before anything is opened, and may hold ${AREA_AT_FIRST.controls}`);
    }
    if (/\d%/.test([...main.querySelectorAll("section[aria-labelledby='character'] summary > :nth-child(-n+3)")].map((one) => one.textContent).join(" "))) {
      say("a vibe of the portrait is shown as a percentage");
    }
  }

  // Nothing comes from anywhere else.
  for (const one of document.querySelectorAll("[src], link[href]")) {
    const from = one.getAttribute("src") ?? one.getAttribute("href") ?? "";
    if (/^([a-z]+:)?\/\//i.test(from)) say(`something is loaded from another origin: ${from}`);
  }

  // The style sheets the page lays, and those it asks for ahead and may never lay.
  const sheets = (rel, as) =>
    [...document.querySelectorAll(`link[rel='${rel}']${as}`)].map((one) => one.getAttribute("href") ?? "");

  return {
    page,
    title,
    robots,
    faults,
    laid: sheets("stylesheet", ""),
    ahead: sheets("preload", "[as='style']"),
    hasBanner: text.includes(BANNER),
    saysPreview: text.includes(PREVIEW_BANNER),
    names: text.includes("syn-"),
  };
}

let pages;
try {
  pages = [];
  for (const file of pagesUnder(ROOT)) {
    pages.push(faultsOf(file));
    // What a closed page held is let go of only once the loop has turned.
    await new Promise((done) => setImmediate(done));
  }
} catch {
  process.stderr.write("No built pages were found. Run `npm run build` first.\n");
  process.exit(1);
}

// Across pages: the banner, what a search engine is told, and titles that tell pages apart.
const home = pages.find(({ page }) => page === "index.html");
if (home === undefined) pages.push({ page: "index.html", title: "", robots: "", faults: ["the search page was not built"] });
if (!pages.some(({ page }) => page === "vibes.html")) {
  pages.push({ page: "vibes.html", title: "", robots: "", faults: ["the page of vibes was not built"] });
}
const madeUp = home?.hasBanner === true;
const preview = home?.saysPreview === true;
const titles = new Map();
for (const found of pages) {
  if (found.hasBanner !== madeUp) found.faults.push("the banner is on some pages and not on others");
  if (found.saysPreview !== preview) found.faults.push("some pages say the release is a preview and others do not");
  if (found.names && !found.hasBanner) found.faults.push("the page names made-up data and does not say it is made up");
  if (madeUp && !/noindex/.test(found.robots)) found.faults.push("a page of made-up data may be indexed");
  if (preview && !/noindex/.test(found.robots)) found.faults.push("a page of a preview may be indexed");
  titles.set(found.title, [...(titles.get(found.title) ?? []), found.page]);
}
for (const [title, sharing] of titles) {
  if (title !== "" && sharing.length > 1) {
    for (const found of pages.filter(({ page }) => sharing.includes(page))) {
      found.faults.push(`its title is also the title of ${sharing.filter((page) => page !== found.page).join(", ")}`);
    }
  }
}

// A style sheet that pages ask for ahead is one that some page lays. One that no page lays
// is fetched by each page that asks for it and used by none, and the browser says so in the
// console of each: as the sheet of the page of a fault in the layout was, which the
// framework has every page ask for.
const laid = new Set(pages.flatMap((found) => found.laid ?? []));
for (const found of pages) {
  for (const sheet of new Set(found.ahead ?? [])) {
    if (!laid.has(sheet)) found.faults.push(`the page asks ahead for a style sheet that no page lays: ${sheet}`);
  }
}

// What is not a page: the robots file, and the header every answer carries. A crawler kept
// out by the robots file never reads the page that asks to be left out, so it is let in,
// and while the data is made up every answer asks to be left out in a header as well.
const BUILT = path.resolve(ROOT, "..", "..");
const notPages = { page: "robots.txt and the headers", title: "", robots: "", faults: [] };
try {
  const asked = readFileSync(path.join(ROOT, "robots.txt.body"), "utf8");
  if (/^\s*disallow\s*:\s*\S/im.test(asked)) {
    notPages.faults.push("the robots file keeps a crawler out, so it cannot read what a page asks of it");
  }
  if (madeUp && /^\s*sitemap\s*:/im.test(asked)) notPages.faults.push("the robots file names a sitemap of made-up places");
  if (preview && /^\s*sitemap\s*:/im.test(asked)) notPages.faults.push("the robots file names a sitemap of a preview");
  const served = JSON.parse(readFileSync(path.join(BUILT, "routes-manifest.json"), "utf8")).headers ?? [];
  const keptOut = served.some(
    ({ source, headers }) =>
      source === "/:path*" &&
      headers.some(({ key, value }) => key.toLowerCase() === "x-robots-tag" && /noindex/.test(value)),
  );
  if ((madeUp || preview) && !keptOut) {
    notPages.faults.push("what is not a page does not ask to be left out of a search engine");
  }
} catch {
  notPages.faults.push("the robots file or the headers were not built");
}
pages.push(notPages);

const faulty = pages.filter(({ faults }) => faults.length > 0);
for (const { page, faults } of faulty) {
  process.stderr.write(`${page}\n${faults.map((fault) => `  ${fault}`).join("\n")}\n`);
}
if (faulty.length > 0) {
  process.stderr.write(`\n${faulty.length} of the ${pages.length} things built have something wrong.\n`);
  process.exit(1);
}
process.stdout.write(`${pages.length - 1} built pages read, the robots file and the headers. Nothing wrong was found.\n`);
