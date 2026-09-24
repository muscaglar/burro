/**
 * Reads a style sheet as far as a test needs to: its rules, what each sets,
 * and how much each selector weighs against another.
 *
 * jsdom lays nothing out and a test cannot see a page. What a test can do is
 * say which of two rules a browser would take, which is decided by the weight
 * of their selectors and, where they weigh the same, by which was loaded
 * last. The order two style sheets load in is not the website's to decide, so
 * a rule that must win has to weigh more.
 */

export interface Rule {
  /** One selector: a rule with a list of them is one of these for each. */
  readonly selector: string;
  /** What the rule sets, by property, as written. */
  readonly sets: ReadonlyMap<string, string>;
  /** The condition the rule is under, such as a width of the screen. `null` when it always holds. */
  readonly under: string | null;
}

/** How much a selector weighs: ids, then classes, attributes and states, then elements. */
export type Weight = readonly [ids: number, classes: number, elements: number];

const withoutComments = (css: string) => css.replace(/\/\*[\s\S]*?\*\//g, "");

function declarationsOf(block: string): Map<string, string> {
  const sets = new Map<string, string>();
  for (const declaration of block.split(";")) {
    const at = declaration.indexOf(":");
    if (at < 0) continue;
    sets.set(declaration.slice(0, at).trim().toLowerCase(), declaration.slice(at + 1).trim());
  }
  return sets;
}

/** Where the block that opens at `from` closes. */
function closeOf(css: string, from: number): number {
  let depth = 0;
  for (let at = from; at < css.length; at += 1) {
    if (css[at] === "{") depth += 1;
    if (css[at] === "}") {
      depth -= 1;
      if (depth === 0) return at;
    }
  }
  throw new Error("A block of the style sheet is never closed.");
}

/** A list of selectors, parted at the commas that are not inside brackets. */
function listOf(selectors: string): string[] {
  const found: string[] = [];
  let depth = 0;
  let from = 0;
  [...selectors].forEach((character, at) => {
    if (character === "(") depth += 1;
    if (character === ")") depth -= 1;
    if (character === "," && depth === 0) {
      found.push(selectors.slice(from, at));
      from = at + 1;
    }
  });
  found.push(selectors.slice(from));
  return found.map((selector) => selector.trim()).filter(Boolean);
}

/** Every rule of a style sheet, with the rules inside a condition among them. */
export function rulesOf(css: string, under: string | null = null): Rule[] {
  const text = withoutComments(css);
  const rules: Rule[] = [];
  let at = 0;
  while (at < text.length) {
    const open = text.indexOf("{", at);
    if (open < 0) break;
    const close = closeOf(text, open);
    // A statement with no block of its own, such as `@charset`, ends before the selector.
    const head = text.slice(at, open).split(";").pop()?.trim() ?? "";
    const block = text.slice(open + 1, close);
    if (/^@(media|supports|layer|container)\b/.test(head)) {
      rules.push(...rulesOf(block, under === null ? head : `${under} and ${head}`));
    } else if (!head.startsWith("@")) {
      for (const selector of listOf(head)) rules.push({ selector, sets: declarationsOf(block), under });
    }
    at = close + 1;
  }
  return rules;
}

/** A selector as a browser reads it: what CSS modules wrap round a class that is not theirs is taken off. */
const plain = (selector: string) => selector.replace(/:global\(([^()]*)\)/g, "$1");

/** The last part of a selector: the element the rule is for. */
export function subjectOf(selector: string): string {
  let depth = 0;
  let from = 0;
  const text = plain(selector).trim();
  [...text].forEach((character, at) => {
    if (character === "(") depth += 1;
    if (character === ")") depth -= 1;
    if (depth === 0 && /[\s>+~]/.test(character)) from = at + 1;
  });
  return text.slice(from);
}

/** True when the rule is for an element of that class. */
export function isFor(selector: string, className: string): boolean {
  return new RegExp(`\\.${className}(?![\\w-])`).test(subjectOf(selector));
}

const add = (one: Weight, other: Weight): Weight => [one[0] + other[0], one[1] + other[1], one[2] + other[2]];

export function heavier(one: Weight, other: Weight): boolean {
  for (const at of [0, 1, 2] as const) {
    if (one[at] !== other[at]) return one[at] > other[at];
  }
  return false;
}

/** How much a selector weighs, by the rules every browser keeps. */
export function weightOf(selector: string): Weight {
  let text = plain(selector);
  let weight: Weight = [0, 0, 0];
  // What is in the brackets of `:is`, `:not` and `:has` weighs what its heaviest part does.
  // What is in those of `:where` weighs nothing.
  for (;;) {
    const found = /:(is|not|has|where)\(([^()]*)\)/.exec(text);
    if (!found) break;
    if (found[1] !== "where") {
      const parts = listOf(found[2] ?? "").map(weightOf);
      const most = parts.reduce<Weight>((best, part) => (heavier(part, best) ? part : best), [0, 0, 0]);
      weight = add(weight, most);
    }
    text = text.replace(found[0], "");
  }
  // What is left of any other brackets is an argument, such as the `2n` of `:nth-child`.
  text = text.replace(/\([^()]*\)/g, "");
  const ids = text.match(/#[\w-]+/g)?.length ?? 0;
  const elements =
    (text.match(/::[\w-]+/g)?.length ?? 0) +
    (text.replace(/::[\w-]+|:[\w-]+|\.[\w-]+|#[\w-]+|\[[^\]]*\]/g, " ").match(/(^|[\s>+~])[a-z][\w-]*/gi)?.length ?? 0);
  const classes =
    (text.match(/\.[\w-]+/g)?.length ?? 0) +
    (text.match(/\[[^\]]*\]/g)?.length ?? 0) +
    (text.replace(/::[\w-]+/g, " ").match(/:[\w-]+/g)?.length ?? 0);
  return add(weight, [ids, classes, elements]);
}
