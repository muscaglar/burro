// Reads every page the build wrote, as a browser would be sent it, and fails
// on what a person or a screen reader would trip over.
//
//   node scripts/check-pages.mjs     after `npm run build`
//
// The tests draw each page in a stand-in for a browser. This reads what was
// built: the language, the title and what a search engine is told are only
// there. It checks structure and words. It cannot see a page, so it says
// nothing of layout, colour or size.

import { readdirSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

// The parser is the one the tests draw pages with. It is found through the
// package that brings it, so that no package is named here that is not asked for.
const require = createRequire(import.meta.url);
const { JSDOM } = createRequire(require.resolve("jest-environment-jsdom"))("jsdom");

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", ".next", "server", "app");
const BANNER = "This is made-up test data.";
// The page a fault in the server shows before anything is drawn. It is the framework's
// own and is built whatever the website holds, so it is not the website's to be held to.
// docs/design/web.md, section 12, says what it lacks.
const NOT_OURS = new Set(["_global-error.html"]);

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
  const { document } = new JSDOM(readFileSync(file, "utf8")).window;
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

  // An icon of the website's own. With none named, a browser asks for one that is not there.
  const icon = document.querySelector('link[rel~="icon"]')?.getAttribute("href") ?? "";
  if (!icon.startsWith("/") || icon.startsWith("//")) say("the page names no icon of the website's own");

  // Nothing comes from anywhere else.
  for (const one of document.querySelectorAll("[src], link[href]")) {
    const from = one.getAttribute("src") ?? one.getAttribute("href") ?? "";
    if (/^([a-z]+:)?\/\//i.test(from)) say(`something is loaded from another origin: ${from}`);
  }

  return { page, title, robots, faults, hasBanner: text.includes(BANNER), names: text.includes("syn-") };
}

let pages;
try {
  pages = pagesUnder(ROOT).map(faultsOf);
} catch {
  process.stderr.write("No built pages were found. Run `npm run build` first.\n");
  process.exit(1);
}

// Across pages: the banner, what a search engine is told, and titles that tell pages apart.
const home = pages.find(({ page }) => page === "index.html");
if (home === undefined) pages.push({ page: "index.html", title: "", robots: "", faults: ["the search page was not built"] });
const madeUp = home?.hasBanner === true;
const titles = new Map();
for (const found of pages) {
  if (found.hasBanner !== madeUp) found.faults.push("the banner is on some pages and not on others");
  if (found.names && !found.hasBanner) found.faults.push("the page names made-up data and does not say it is made up");
  if (madeUp && !/noindex/.test(found.robots)) found.faults.push("a page of made-up data may be indexed");
  titles.set(found.title, [...(titles.get(found.title) ?? []), found.page]);
}
for (const [title, sharing] of titles) {
  if (title !== "" && sharing.length > 1) {
    for (const found of pages.filter(({ page }) => sharing.includes(page))) {
      found.faults.push(`its title is also the title of ${sharing.filter((page) => page !== found.page).join(", ")}`);
    }
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
  const served = JSON.parse(readFileSync(path.join(BUILT, "routes-manifest.json"), "utf8")).headers ?? [];
  const keptOut = served.some(
    ({ source, headers }) =>
      source === "/:path*" &&
      headers.some(({ key, value }) => key.toLowerCase() === "x-robots-tag" && /noindex/.test(value)),
  );
  if (madeUp && !keptOut) notPages.faults.push("what is not a page does not ask to be left out of a search engine");
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
