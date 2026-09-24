import { BANNER } from "@/content/site";
import type { Meta } from "@/lib/api/schema";

import styles from "./SyntheticBanner.module.css";

interface Props {
  readonly synthetic: Meta["synthetic"];
}

/**
 * Says plainly that the data is made up. It is on every page while the
 * release is synthetic, and it has no way to be closed.
 */
export function SyntheticBanner({ synthetic }: Props) {
  if (!synthetic) return null;
  return (
    <section className={styles.banner} aria-label={BANNER.label}>
      <p className={styles.text}>{BANNER.text}</p>
    </section>
  );
}
