/**
 * What a style sheet sets of an element, in a result of a given width.
 *
 * jsdom lays nothing out, and a test of one rule holds that rule alone: every rule of a
 * sheet was held by a test, and between two of them a result of some widths was laid out
 * by neither. What a test can do is ask of every width what a browser would: which rules
 * hold there, which of them are for the element, and which of those a browser takes.
 *
 * A result is laid out by its own width, which a sheet asks of what holds it
 * (`@container`). A condition by anything else, as by the width of the screen or by what
 * the system asks for, holds of no width here.
 */

import { heavier, weightOf, type Rule } from "./css";

/** True when a condition of a sheet holds of a result that wide, in rem. */
export function holdsAt(under: string | null, rem: number): boolean {
  if (under === null) return true;
  if (!under.startsWith("@container")) return false;
  const tests = [...under.matchAll(/\(\s*(max-width|min-width|width)\s*(:|<=|>=|<|>)\s*([\d.]+)rem\s*\)/g)];
  // A condition is read whole or not at all: one that is read in part would hold where it does not.
  const read = tests.map(([all]) => all).join(" and ");
  if (tests.length === 0 || under !== `@container ${read}`) throw new Error(`A condition this cannot read: ${under}`);
  return tests.every(([, what, how, value]) => {
    const at = Number(value);
    if (what === "max-width") return rem <= at;
    if (what === "min-width") return rem >= at;
    return how === "<" ? rem < at : how === ">" ? rem > at : how === "<=" ? rem <= at : rem >= at;
  });
}

/**
 * What a sheet sets of an element, in a result that wide: every rule that holds there and
 * is for the element, the heavier over the lighter and the later over the earlier, as a
 * browser takes them. What a rule sets of a part that is no element, as of what stands
 * before one, is none of it.
 */
export function setAt(rules: readonly Rule[], element: Element, rem: number): ReadonlyMap<string, string> {
  const held = rules
    .map((rule, at) => ({ rule, at, weight: weightOf(rule.selector) }))
    .filter(({ rule }) => !rule.selector.includes("::") && holdsAt(rule.under, rem) && element.matches(rule.selector))
    .sort((one, other) => (heavier(one.weight, other.weight) ? 1 : heavier(other.weight, one.weight) ? -1 : one.at - other.at));
  const sets = new Map<string, string>();
  for (const { rule } of held) for (const [property, value] of rule.sets) sets.set(property, value);
  return sets;
}

/** The line of a grid a part begins on, where a sheet says one: the first number of what it sets. */
export function rowOf(sets: ReadonlyMap<string, string>): number {
  return Number(/^\d+/.exec(sets.get("grid-row") ?? "")?.[0]);
}
