import Link from "next/link";

import { SOURCE_LINE } from "@/content/area";
import { SOURCE } from "@/content/search";
import type { Fact } from "@/lib/api/schema";
import { linesOf } from "@/lib/facts";
import { readableDate } from "@/lib/format";
import { paths } from "@/lib/paths";

import styles from "./SourceLine.module.css";

interface Props {
  /** The facts behind the figure. Each says its sources and its date. */
  readonly facts: readonly Fact[];
}

/**
 * The source and the date of a figure, written out under it: the name of
 * each source, linked to its entry on the sources page, the date of the
 * data, and "Made-up data" when it is.
 *
 * It says what the "Source" button says, without the button, so that a page
 * built ahead of time says where every figure came from with scripts off.
 */
export function SourceLine({ facts }: Props) {
  const lines = linesOf(facts);
  if (lines.length === 0) return null;
  return (
    <p className={styles.line}>
      {SOURCE_LINE.source}:{" "}
      {lines.map((line, at) => (
        <span key={`${line.sourceId} ${line.asOf}`}>
          {at > 0 ? " " : null}
          {/* Which source a person went on to read is not told to anyone ahead of time. */}
          <Link className={`${styles.link} target-min`} href={paths.sources(line.sourceId)} prefetch={false}>
            {line.name}
          </Link>
          . {SOURCE.dataFrom} {readableDate(line.asOf)}.
          {line.synthetic ? (
            <>
              {" "}
              <span className={styles.madeUp}>{SOURCE.madeUp}</span>
            </>
          ) : null}
        </span>
      ))}
    </p>
  );
}
