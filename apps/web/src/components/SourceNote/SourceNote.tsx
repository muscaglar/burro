"use client";

import Link from "next/link";

import { SOURCE } from "@/content/search";
import type { Fact } from "@/lib/api/schema";
import { linesOf } from "@/lib/facts";
import { readableDate } from "@/lib/format";
import { paths } from "@/lib/paths";

import { Disclosure } from "../Disclosure/Disclosure";
import styles from "./SourceNote.module.css";

interface Props {
  /** The facts behind the figure or the sentence. Each says its sources and its date. */
  readonly facts: readonly Fact[];
  /** What the source is of, to tell one "Source" button from the next. */
  readonly of?: string;
}

// Kept here as well, for whoever reads a fact's lines beside its button.
export { linesOf };

/**
 * The "Source" button that ends every sentence and every figure. It opens,
 * in place: the name of each source, linked to its entry on the sources
 * page, the date of the data, and "Made-up data" when it is.
 *
 * With no fact in hand there is nothing to open, so it is a link to the
 * sources page instead.
 */
export function SourceNote({ facts, of }: Props) {
  const name = of === undefined ? undefined : SOURCE.buttonFor(of);
  if (facts.length === 0) {
    return (
      <Link className={`${styles.link} target-min`} href={paths.sources()} aria-label={name} prefetch={false}>
        {SOURCE.button}
      </Link>
    );
  }
  return (
    <Disclosure label={SOURCE.button} name={name} size="small" className={styles.note}>
      <ul className={styles.lines}>
        {linesOf(facts).map((line) => (
          <li key={`${line.sourceId} ${line.asOf}`}>
            <Link className={`${styles.link} target-min`} href={paths.sources(line.sourceId)} prefetch={false}>
              {line.name}
            </Link>
            <span>
              {SOURCE.dataFrom} {readableDate(line.asOf)}
            </span>
            {line.synthetic ? <span className={styles.madeUp}>{SOURCE.madeUp}</span> : null}
          </li>
        ))}
      </ul>
    </Disclosure>
  );
}
