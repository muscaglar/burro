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

/**
 * One sentence about a place, as the API wrote it: not reworded, not joined
 * to another, nothing added. It ends in its source. A sentence a model wrote
 * says so.
 */
export function Sentence({ sentence, facts, of, meta }: Props) {
  const cited = factsCited(sentence, facts);
  // The first fact cited is the one the sentence is about. Any other only names the area.
  const about = cited.slice(0, 1);
  return (
    <div className={styles.sentence}>
      <p className={styles.text}>{sentence.text}</p>
      {sentence.origin === "model" ? <p className={styles.byModel}>{RESULTS.byModel}</p> : null}
      <SourceNote facts={about} of={of} meta={meta} />
    </div>
  );
}
