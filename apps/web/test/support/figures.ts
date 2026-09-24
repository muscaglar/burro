/**
 * Finds every figure a page shows, and says which of them the API did not
 * send. The website never writes a fact about a place, so every piece of
 * text that holds a digit must be the API's own, or site copy that says
 * nothing of a place.
 */

import { columnsOf } from "@/components/FactRow/FactRow";
import type { Fact, FactSource } from "@/lib/api/schema";
import { readableDate } from "@/lib/format";

const DIGIT = /\d/;
/** What is never read as text of the page: a program, a style, and what a picture is drawn from. */
const NOT_TEXT = new Set(["SCRIPT", "STYLE", "NOSCRIPT"]);

/** Every piece of text under an element that holds a digit, as the page shows it. */
export function textsWithFigures(container: Element): string[] {
  const found: string[] = [];
  const walker = container.ownerDocument.createTreeWalker(container, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node !== null; node = walker.nextNode()) {
    const text = node.textContent?.trim() ?? "";
    if (!DIGIT.test(text)) continue;
    if (node.parentElement !== null && NOT_TEXT.has(node.parentElement.tagName)) continue;
    found.push(text);
  }
  return found;
}

/**
 * Everything the facts let a page say: each slot as it came, each slot as a
 * fact's row lays it out, each label and name, and the date and the sources
 * of each fact.
 */
export function saidBy(facts: readonly Fact[]): Set<string> {
  const said = new Set<string>();
  for (const fact of facts) {
    said.add(fact.label);
    for (const value of Object.values(fact.slots)) said.add(value);
    for (const [, value] of columnsOf(fact)) if (value !== undefined) said.add(value);
    for (const name of fact.names) said.add(name);
    said.add(fact.as_of);
    said.add(readableDate(fact.as_of));
    for (const source of fact.sources as readonly FactSource[]) said.add(source.name);
  }
  return said;
}

/** The figures on the page that nothing in `allowed` accounts for. A test expects none. */
export function figuresNotFrom(container: Element, allowed: ReadonlySet<string>): string[] {
  return textsWithFigures(container).filter((text) => !allowed.has(text));
}
