import type { ReactNode } from "react";

import { endsOf } from "@/lib/vibes";

import { Art } from "../Art/Art";
import { pictureOfEnd, picturesAtEnds } from "./picture";
import styles from "./Ends.module.css";

interface Props {
  /**
   * The id the service gives the vibe whose gauge this is. Each end then has the one
   * picture that is drawn for that end of that vibe, whichever way the vibe runs. Left
   * out, an end is drawn by its name, and every vibe that runs one way alike.
   */
  readonly id?: string | null;
  /** The name the API gives the low end of a scale. `null` of a vibe that runs one way, from least to most. */
  readonly low: string | null;
  /** The name the API gives the high end. `null` of a vibe that runs one way. */
  readonly high: string | null;
  /** What runs between the two ends: the steps of a band, a gauge, a slider. Left out, the two ends stand side by side. */
  readonly children?: ReactNode;
}

/**
 * The two ends of a gauge, each with its one small picture and its name: houses and flats,
 * calm and buzzy, little that is green and much. The low end is at the left.
 *
 * The pictures are for the eye and the names are read. Neither end is the good one, and
 * the two are drawn alike: the same size, the same weight, and no mark on either.
 */
export function Ends({ id, low, high, children }: Props) {
  const [first, last] = endsOf({ low_end: low, high_end: high });
  const [atFirst, atLast] = id === undefined ? [pictureOfEnd(first), pictureOfEnd(last)] : picturesAtEnds(id);
  return (
    <span className={styles.ends}>
      <span className={styles.end}>
        <Art name={atFirst} alt="" />
        <span className={styles.name}>{first}</span>
      </span>
      {children === undefined ? null : <span className={styles.between}>{children}</span>}
      <span className={styles.end}>
        <Art name={atLast} alt="" />
        <span className={styles.name}>{last}</span>
      </span>
    </span>
  );
}
