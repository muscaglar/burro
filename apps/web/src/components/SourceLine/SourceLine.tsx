import Link from "next/link";

import { SOURCE_LINE } from "@/content/area";
import { SOURCE } from "@/content/search";
import type { Fact } from "@/lib/api/schema";
import { citedBy } from "@/lib/facts";
import { readableDate } from "@/lib/format";
import { paths } from "@/lib/paths";

import styles from "./SourceLine.module.css";

interface Props {
  /** The facts behind the figure. Each says its sources and its date. */
  readonly facts: readonly Fact[];
}

const LIST = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

/**
 * What the line begins with. A vibe is Burro's own recipe, and its sources are
 * those of its parts: its fact says so in the API's words, and they are used
 * where every fact of the line says the same.
 */
function leadOf(facts: readonly Fact[]): string {
  const said = new Set(facts.map((fact) => fact.slots.made_from ?? ""));
  const [only] = [...said];
  return said.size === 1 && only !== undefined && only !== "" ? only : `${SOURCE_LINE.source}:`;
}

/**
 * The source and the date of a figure, written out under it: the name of
 * each source and who published it, linked to its entry on the sources page,
 * then the date of the data, and "Made-up data" when it is.
 *
 * Each source is named once, and the date is said once, after them all: it
 * is the date of the figure, and not of any one source.
 *
 * It says what the "Source" button says, without the button, so that a page
 * built ahead of time says where every figure came from with scripts off.
 */
export function SourceLine({ facts }: Props) {
  const { sources, dates, synthetic } = citedBy(facts);
  if (sources.length === 0) return null;
  return (
    <p className={styles.line}>
      {leadOf(facts)}{" "}
      {sources.map((source, at) => (
        <span key={source.source_id}>
          {at > 0 ? "; " : null}
          {/* Which source a person went on to read is not told to anyone ahead of time. */}
          <Link className={`${styles.link} target-min`} href={paths.sources(source.source_id)} prefetch={false}>
            {source.name}
          </Link>
          {source.publisher === undefined || source.publisher === "" ? null : `, ${SOURCE.by} ${source.publisher}`}
        </span>
      ))}
      .{" "}
      {dates.length === 0 ? null : (
        // The words before the date and the date stay on one line: a line once broke between them.
        <span className={styles.dated}>
          {SOURCE.dataFrom} {LIST.format(dates.map(readableDate))}.
        </span>
      )}
      {synthetic ? (
        <>
          {" "}
          <span className={styles.madeUp}>{SOURCE.madeUp}</span>
        </>
      ) : null}
    </p>
  );
}
