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
