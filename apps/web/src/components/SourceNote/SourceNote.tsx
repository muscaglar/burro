"use client";

import Link from "next/link";

import { countsOf } from "@/content/crime";
import { SOURCE } from "@/content/search";
import type { Fact, MetaData } from "@/lib/api/schema";
import { citedBy, linesOf } from "@/lib/facts";
import { readableDate } from "@/lib/format";
import { paths } from "@/lib/paths";

import { Disclosure } from "../Disclosure/Disclosure";
import styles from "./SourceNote.module.css";

interface Props {
  /** The facts behind the figure or the sentence. Each says its sources and its date. */
  readonly facts: readonly Fact[];
  /** What the source is of, to tell one "Source" button from the next. */
  readonly of?: string;
  /** True where the line about judgement stands beside the button already, so it is not said twice. */
  readonly judgementSaid?: boolean;
  /**
   * The vibes and the features of the release. With them in hand, the source of a vibe whose
   * recipe holds recorded crime says so, and names what it counts.
   */
  readonly meta?: Pick<MetaData, "tags" | "features">;
}

// Kept here as well, for whoever reads a fact's lines beside its button.
export { linesOf };

/** What every fact in hand says in one slot, where each holds it and all say the same. */
function saidByAll(facts: readonly Fact[], slot: "made_from" | "judgement"): string | null {
  const said = new Set(facts.map((fact) => fact.slots[slot] ?? ""));
  const [only] = [...said];
  return said.size === 1 && only !== undefined && only !== "" ? only : null;
}

/** What the vibes these facts are of count that is recorded crime: one line for each that counts any. */
function crimeOf(facts: readonly Fact[], meta: Props["meta"]): readonly string[] {
  if (meta === undefined) return [];
  const said = facts.flatMap((fact) => {
    const tag = fact.kind === "tag" ? meta.tags.find((one) => one.tag_id === fact.key) : undefined;
    return tag === undefined ? [] : (countsOf(tag, meta.features) ?? []);
  });
  return [...new Set(said)];
}

/**
 * The "Source" button that ends every sentence and every figure. It opens,
 * in place: the name of each source, linked to its entry on the sources
 * page, the date of the data, and "Made-up data" when it is.
 *
 * A vibe is Burro's own recipe, and its sources are those of its parts. Its
 * fact says so, and that the weights are a judgement, in the API's words.
 * Both are shown here, word for word: a result says a vibe in short, and what
 * the short sentence leaves out is one press away, with its source.
 *
 * With no fact in hand there is nothing to open, so it is a link to the
 * sources page instead.
 */
export function SourceNote({ facts, of, judgementSaid = false, meta }: Props) {
  const name = of === undefined ? undefined : SOURCE.buttonFor(of);
  if (facts.length === 0) {
    return (
      <Link className={`${styles.link} target-min`} href={paths.sources()} aria-label={name} prefetch={false}>
        {SOURCE.button}
      </Link>
    );
  }
  const madeFrom = saidByAll(facts, "made_from");
  const judgement = judgementSaid ? null : saidByAll(facts, "judgement");
  const { sources, dates, synthetic } = citedBy(facts);
  return (
    <Disclosure label={SOURCE.button} name={name} size="small" className={styles.note}>
      {madeFrom === null ? null : <p className={styles.said}>{madeFrom}</p>}
      {/* Each source once, with who published it. The date is said once, after them: it is
          the date of what is said, and not of any one source. */}
      <ul className={styles.lines}>
        {sources.map((source) => (
          <li key={source.source_id}>
            <Link className={`${styles.link} target-min`} href={paths.sources(source.source_id)} prefetch={false}>
              {source.name}
            </Link>
            {source.publisher === undefined || source.publisher === "" ? null : (
              <span>
                {SOURCE.by} {source.publisher}
              </span>
            )}
          </li>
        ))}
        {dates.map((date) => (
          <li key={date}>
            <span>
              {SOURCE.dataFrom} {readableDate(date)}
            </span>
          </li>
        ))}
        {synthetic ? (
          <li>
            <span className={styles.madeUp}>{SOURCE.madeUp}</span>
          </li>
        ) : null}
      </ul>
      {/* After the sources, which the line before them leads in to. */}
      {crimeOf(facts, meta).map((line) => (
        <p key={line} className={styles.said}>
          {line}
        </p>
      ))}
      {judgement === null ? null : <p className={styles.said}>{judgement}</p>}
    </Disclosure>
  );
}
