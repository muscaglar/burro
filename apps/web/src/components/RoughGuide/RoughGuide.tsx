import type { Told } from "@/content/rough";

import styles from "./RoughGuide.module.css";

interface LabelProps {
  /** What the vibe says of itself, from route 11. `null` for a vibe that is as sure as the rest. */
  readonly told: Told | null;
}

/**
 * The short label of a vibe that is a rough guide, which stands beside its
 * name wherever the name is drawn. The word is the API's. It is drawn for
 * the eye and read out with the name, and nothing is drawn of any other vibe.
 */
export function RoughLabel({ told }: LabelProps) {
  if (told === null) return null;
  return (
    <span className={styles.label} data-rough-guide="label">
      <span className="visually-hidden">, </span>
      {told.label}
    </span>
  );
}

interface NoteProps extends LabelProps {
  /** The name of the vibe, where the note stands apart from it and must say which vibe it is of. */
  readonly of?: string;
  /** True where the label stands beside the name already, and only the sentence is left to say. */
  readonly labelled?: boolean;
}

/**
 * What a vibe that is a rough guide says of itself: its label, and the
 * sentence that says why it is less sure than the rest. Both are the API's,
 * word for word. It is drawn in sight, and never behind a press.
 */
export function RoughNote({ told, of, labelled = false }: NoteProps) {
  if (told === null) return null;
  return (
    <p className={styles.note} role="note" data-rough-guide="note">
      {of === undefined ? null : <span className={styles.of}>{of}: </span>}
      {labelled ? null : <span className={styles.said}>{told.label}. </span>}
      {told.why}
    </p>
  );
}
