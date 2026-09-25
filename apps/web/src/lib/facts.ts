/**
 * Where a fact came from and when: read off the fact, for a page to show.
 *
 * Nothing here writes a word about a place. It finds what the API sent. It is
 * plain code with no state, so a page built on the server and a part drawn in
 * the browser read a fact the same way.
 */

import type { Fact, FactSource } from "@/lib/api/schema";

export interface SourceLine {
  readonly sourceId: string;
  readonly name: string;
  readonly asOf: string;
  readonly synthetic: boolean;
}

/** One line for each source and date, however many facts share them. */
export function linesOf(facts: readonly Fact[]): readonly SourceLine[] {
  const lines = new Map<string, SourceLine>();
  for (const fact of facts) {
    for (const source of fact.sources) {
      lines.set(`${source.source_id} ${fact.as_of}`, {
        sourceId: source.source_id,
        name: source.name,
        asOf: fact.as_of,
        synthetic: fact.synthetic,
      });
    }
  }
  return [...lines.values()];
}

/** What some facts rest on: each source once, and each date once. */
export interface Cited {
  /** Every source the facts name, once each, in the order the facts name them. */
  readonly sources: readonly FactSource[];
  /** Every date the facts give, once each, as the API wrote it, in the order the facts give them. */
  readonly dates: readonly string[];
  /** True where any of the facts is made up. */
  readonly synthetic: boolean;
}

/**
 * The sources and the dates of some facts, each said once.
 *
 * A date is the date of a figure, and never of a source: a figure worked out in one month
 * from a census of another year has one date, which is the figure's. The date once stood
 * beside each source, so that a census of 2021 read "Data from April 2026", and a fact of
 * five sources said its date five times.
 */
export function citedBy(facts: readonly Fact[]): Cited {
  const sources = new Map<string, FactSource>();
  const dates = new Set<string>();
  for (const fact of facts) {
    for (const source of fact.sources) if (!sources.has(source.source_id)) sources.set(source.source_id, source);
    if (fact.as_of !== "") dates.add(fact.as_of);
  }
  return {
    sources: [...sources.values()],
    dates: [...dates],
    synthetic: facts.some((fact) => fact.synthetic),
  };
}

/**
 * The statement of credit a source brings with it, where its publisher asks that it stands
 * wherever a figure made from its data is shown. The API says which: a source that is
 * credited by its name and its publisher brings none. A statement of several lines is one
 * line here, each part ended with a full stop.
 */
export function creditOf(source: FactSource): string | null {
  const said = (source.attribution ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line !== "");
  return said.length === 0 ? null : said.map((line) => (/[.!?]$/.test(line) ? line : `${line}.`)).join(" ");
}

/** Every source the facts name, once each, in the order of their names. */
export function sourcesOf(facts: readonly Fact[]): readonly FactSource[] {
  const found = new Map<string, FactSource>();
  for (const fact of facts) {
    for (const source of fact.sources) found.set(source.source_id, source);
  }
  return [...found.values()].sort(
    (one, other) => one.name.localeCompare(other.name, "en-GB") || one.source_id.localeCompare(other.source_id),
  );
}
