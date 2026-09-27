import { RESULTS } from "@/content/search";
import type { ExplainedSentence, Fact, MetaData } from "@/lib/api/schema";

import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./Sentence.module.css";

interface Props {
  readonly sentence: ExplainedSentence;
  /** The facts in hand. The sentence's own are found among them by id. */
  readonly facts: Readonly<Record<string, Fact>> | readonly Fact[];
  /** What the sentence is, to name its "Source" button: "reason 1", "trade-off". */
  readonly of?: string;
  /** The vibes and the features of the release, for the source of a vibe that counts recorded crime. */
  readonly meta?: Pick<MetaData, "tags" | "features">;
  /**
   * False where the key of its source stands elsewhere, as it does for a sentence of a
   * result as it is first shown: its source is in the working of the result.
   */
  readonly source?: boolean;
}

/** The facts a sentence cites, of those in hand. */
export function factsCited(
  sentence: Pick<ExplainedSentence, "fact_ids">,
  facts: Readonly<Record<string, Fact>> | readonly Fact[],
): readonly Fact[] {
  const byId = (id: string) =>
    Array.isArray(facts)
      ? (facts as readonly Fact[]).find((fact) => fact.fact_id === id)
      : (facts as Readonly<Record<string, Fact>>)[id];
  return sentence.fact_ids.flatMap((id) => byId(id) ?? []);
}

/** The fact a sentence is about: the first it cites, of those in hand. Any other only names the area. */
export function factAbout(
  sentence: Pick<ExplainedSentence, "fact_ids">,
  facts: Readonly<Record<string, Fact>> | readonly Fact[],
): readonly Fact[] {
  return factsCited(sentence, facts).slice(0, 1);
}

/**
 * One sentence about a place, as the API wrote it: not reworded, not joined
 * to another, nothing added. It ends in its source, unless it is told that
 * its source stands elsewhere. A sentence a model wrote says so.
 */
export function Sentence({ sentence, facts, of, meta, source = true }: Props) {
  return (
    <div className={styles.sentence}>
      <p className={styles.text}>{sentence.text}</p>
      {sentence.origin === "model" ? <p className={styles.byModel}>{RESULTS.byModel}</p> : null}
      {source ? <SourceNote facts={factAbout(sentence, facts)} of={of} meta={meta} /> : null}
    </div>
  );
}
