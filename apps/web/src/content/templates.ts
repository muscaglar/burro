/**
 * Sentences of the API's, as the contract writes their templates (section
 * 7.3). Route 6 serves a fact as slots and no sentence (docs/design/web.md,
 * section 13, gap 4), so a fact of an area's page that is to read as a
 * sentence is filled in here, from the fact's own slots and nothing else.
 *
 * Each is the contract's template word for word, and a test holds it to the
 * contract. The website words no sentence of its own about a place. Where a
 * fact comes with a sentence of its own, that is shown and this is not.
 */

import type { Fact } from "@/lib/api/schema";

type Slots = Fact["slots"];

/** The templates, as the contract writes them, with each slot in braces. */
export const TEMPLATES = {
  likeness:
    "{name} is in the same band as {other} on {same} of the {measures} measures compared, and least alike in {family}.",
  likeness_same: "{name} is in the same band as {other} on all {measures} measures compared.",
  station: "Nearest station: {name}, about {walk} minutes on foot. Lines: {lines}.",
  station_nearby: "Station within a short walk: {name}, about {walk} minutes on foot. Lines: {lines}.",
} as const;

export type Templated = keyof typeof TEMPLATES;

const isTemplated = (template: string): template is Templated => template in TEMPLATES;

/**
 * The sentence of a fact: its own where it has one, and otherwise the
 * contract's template filled from its slots. `null` for a template that is
 * not held here, and where a slot the template names is missing: nothing is
 * filled in.
 */
export function sentenceOf(fact: Pick<Fact, "template" | "slots">): string | null {
  const own = (fact as { readonly text?: unknown }).text;
  if (typeof own === "string" && own !== "") return own;
  if (!isTemplated(fact.template)) return null;
  const slots: Slots = fact.slots;
  let whole = true;
  const filled = TEMPLATES[fact.template].replace(/\{(\w+)\}/g, (_, name: string) => {
    const value = slots[name];
    if (value === undefined || value === "") whole = false;
    return value ?? "";
  });
  return whole ? filled : null;
}
