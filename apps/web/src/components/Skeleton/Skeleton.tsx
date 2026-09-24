import styles from "./Skeleton.module.css";

interface Props {
  /** How many lines of text it holds the place of. */
  readonly lines?: number;
  /** `card` holds the place of a whole result, `chip` of one chip. */
  readonly shape?: "lines" | "card" | "chip";
}

/**
 * Holds the place of what is coming, at the size it will be, so that nothing
 * on the page moves when it arrives. It does not shimmer, and it says
 * nothing to a screen reader: the status line says what is being waited for.
 */
export function Skeleton({ lines = 1, shape = "lines" }: Props) {
  if (shape === "chip") return <span className={`skeleton ${styles.chip}`} aria-hidden="true" />;
  return (
    <div className={shape === "card" ? styles.card : styles.lines} aria-hidden="true">
      {Array.from({ length: lines }, (_, at) => (
        <span key={at} className={`skeleton ${styles.line}`} />
      ))}
    </div>
  );
}
