import { isRange, VIBE_BANDS, type Placed } from "@/lib/vibes";

import styles from "./Track.module.css";

interface Props {
  readonly placed: Placed;
  /**
   * What the picture shows, in words: the band, and which way the bands are counted.
   * Left out where the same words are written beside it, and the picture is then kept
   * from a screen reader, which would hear them twice.
   */
  readonly says?: string;
  /** True where marks stand side by side on a narrow screen, and the cells are drawn narrower. */
  readonly narrow?: boolean;
}

/**
 * Five cells from the low end to the high end, with the one the area sits in
 * filled. A mixed area fills the cells it spans, and is never drawn as a point
 * in the middle. It is a picture, and says in words what it shows, or stands
 * beside the words that do.
 */
export function Track({ placed, says, narrow = false }: Props) {
  const range = isRange(placed);
  return (
    <span
      className={styles.track}
      data-range={range}
      data-narrow={narrow}
      {...(says === undefined ? { "aria-hidden": true } : { role: "img", "aria-label": says })}
    >
      {VIBE_BANDS.map((band) => (
        <span
          key={band}
          className={styles.cell}
          data-on={range ? band >= placed.spread_low && band <= placed.spread_high : band === placed.band}
        />
      ))}
    </span>
  );
}
