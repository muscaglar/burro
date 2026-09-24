import { NOTICE, REJECTED, REJECTED_LABEL, UNMET, UNMET_LABEL } from "@/content/search";
import type { InterpretData, Notice, UnmetCategory } from "@/lib/api/schema";
import type { Refusal } from "@/lib/search/refusals";

import styles from "./NoticeBlock.module.css";

interface NoticeProps {
  readonly notice: Notice;
  /** The API's own sentence. It is shown word for word. */
  readonly text: InterpretData["notice_text"];
}

/**
 * The API's one neutral notice, word for word, in a plain block. It says what
 * Burro ranks by. It never says what was left out, and neither does the page.
 */
export function NoticeBlock({ notice, text }: NoticeProps) {
  if (notice === "none" || text === "") return null;
  return (
    <div className={styles.notice} role="status" aria-label={NOTICE.label}>
      <p>{text}</p>
    </div>
  );
}

/** One line of site copy for a state of the page: words that could not be read, or nothing read. */
export function StateLine({ children }: { readonly children: string }) {
  return (
    <div className={styles.state} role="status">
      <p>{children}</p>
    </div>
  );
}

/** One line for each kind of thing that was asked for and cannot be answered. */
export function UnmetList({ unmet }: { readonly unmet: readonly UnmetCategory[] }) {
  if (unmet.length === 0) return null;
  return (
    <section className={styles.list} aria-label={UNMET_LABEL}>
      <ul>
        {unmet.map((category) => (
          <li key={category}>{UNMET[category]}</li>
        ))}
      </ul>
    </section>
  );
}

interface RejectedProps {
  readonly refusals: readonly Refusal[];
  /** The name of the part a refusal is about, where it has one: the API's label, or a place's name. */
  readonly nameOf: (key: string) => string | null;
}

/** One line for each edit that was not applied, with what it was about and why. */
export function RejectedList({ refusals, nameOf }: RejectedProps) {
  if (refusals.length === 0) return null;
  return (
    <section className={styles.list} aria-label={REJECTED_LABEL}>
      <ul>
        {refusals.map(({ key, reason }, at) => {
          const about = key === null ? null : nameOf(key);
          return (
            <li key={`${key ?? "none"}-${reason}-${at}`}>
              {about !== null ? <strong>{about}: </strong> : null}
              {REJECTED[reason]}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/** Said while the browser has no connection. What is on screen stays readable. */
export function OfflineLine({ waiting }: { readonly waiting: boolean }) {
  return (
    <div className={styles.state} role="status">
      <p>
        {NOTICE.offline}
        {waiting ? ` ${NOTICE.offlineWaiting}` : null}
      </p>
    </div>
  );
}
