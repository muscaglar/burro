import { PREVIEW_BANNER } from "@/content/site";
import type { Meta } from "@/lib/api/schema";

import styles from "./PreviewBanner.module.css";

interface Props {
  readonly preview: Meta["preview"];
  /** True where the data of the preview is not made up. The banner then says that it is real. */
  readonly real?: boolean;
}

/**
 * Says plainly that the release is not finished. It is on every page that was
 * built on a preview, and it has no way to be closed.
 *
 * It never says that the figures are made up: the other banner does. A
 * preview of real data shows this one alone, and it says that its figures are
 * of real places, so that a real figure is never taken for an invented one.
 *
 * On a narrow screen, once a search is open, it is one line: it says that this
 * is a preview, and the rest gives way to the answer. The line is written beside
 * the whole and drawn in its place, so that the whole is drawn as it always was:
 * cut in two where the line ends, its words stood a part of a point apart.
 */
export function PreviewBanner({ preview, real = false }: Props) {
  if (!preview) return null;
  return (
    <section className={styles.banner} aria-label={PREVIEW_BANNER.label}>
      <p className={styles.text}>
        <span className={styles.whole}>
          {PREVIEW_BANNER.text}
          {real ? ` ${PREVIEW_BANNER.real}` : null}
        </span>
        <span className={styles.short}>{PREVIEW_BANNER.short}</span>
      </p>
    </section>
  );
}
