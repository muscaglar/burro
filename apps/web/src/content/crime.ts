/**
 * When recorded crime counts, said one way on every page that speaks of it:
 * the search, the settings, the methods, the page of vibes and the page of
 * an area. The contract's rule is that crime is weighed only when a person
 * asks for it or moves its control (section 5.3, rule 8), and that a vibe
 * whose recipe holds recorded crime is held to the same rule.
 *
 * No vibe is written here. Which vibe holds recorded crime, and which parts
 * of its recipe are of crime, is read from route 11, and named as the API
 * names it.
 */

import type { MetaData, Metric, Tag } from "@/lib/api/schema";

/** The rule, word for word wherever it is said. */
export const CRIME_RULE =
  "Recorded crime counts only when you ask for it by name, switch it on in the settings, or ask for a vibe whose recipe holds it.";

export const CRIME_ACCOUNT = {
  rule: CRIME_RULE,
  /** Where no vibe of the release holds recorded crime. */
  noVibe: "In this data no vibe holds it.",
  /** Before the vibes that do. Each is then named, with the parts of its recipe that are of crime. */
  vibes: "In this data the vibes that hold it are these, each with what it counts.",
  /** On the card of such a vibe, before the parts of its recipe that are of crime. */
  counts: "This vibe counts recorded crime",
  /** On the chip of such a vibe, after its name, so that a search that holds it says so in the row. */
  chip: "counts recorded crime",
  /** After them: what asking for the vibe is. A scale counts it towards whichever end is asked for. */
  asking: "To ask for it, towards either end, is to ask for recorded crime by name.",
  askingOneWay: "To ask for it is to ask for recorded crime by name.",
} as const;

/** What asking for a vibe that holds recorded crime is, by whether the vibe is a scale. */
export function askingFor(tag: Pick<Tag, "low_end" | "high_end">): string {
  return tag.low_end !== null && tag.high_end !== null ? CRIME_ACCOUNT.asking : CRIME_ACCOUNT.askingOneWay;
}

/** A vibe whose recipe holds recorded crime, with the parts of it that are of crime. */
export interface CrimeVibe {
  readonly tag: Tag;
  readonly parts: readonly Metric[];
}

/** The parts of a recipe that are of recorded crime, as the release names them. */
export function crimeParts(tag: Pick<Tag, "terms">, features: readonly Metric[]): readonly Metric[] {
  return tag.terms.flatMap((term) => {
    const metric = features.find((one) => one.feature_id === term.feature_id);
    return metric !== undefined && metric.dimension === "crime" ? [metric] : [];
  });
}

/**
 * The rule as a page says it of one release. Where no vibe of the release holds recorded
 * crime, the third way of the rule is true of nothing there, and the page says so after it.
 */
export function ruleIn(meta: Pick<MetaData, "tags" | "features">): string {
  return crimeVibes(meta).length === 0 ? `${CRIME_RULE} ${CRIME_ACCOUNT.noVibe}` : CRIME_RULE;
}

/** What the recipe of a vibe counts that is recorded crime, as one line, or `null` where it counts none. */
export function countsOf(tag: Pick<Tag, "terms">, features: readonly Metric[]): string | null {
  const parts = crimeParts(tag, features);
  return parts.length === 0 ? null : `${CRIME_ACCOUNT.counts}: ${parts.map((part) => part.label).join("; ")}.`;
}

/** The vibes of the release whose recipe holds recorded crime, in the order the API lists them. */
export function crimeVibes(meta: Pick<MetaData, "tags" | "features">): readonly CrimeVibe[] {
  return meta.tags.flatMap((tag) => {
    const parts = crimeParts(tag, meta.features);
    return parts.length === 0 ? [] : [{ tag, parts }];
  });
}
