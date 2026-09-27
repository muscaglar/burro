import type { CSSProperties } from "react";

import { RESULTS } from "@/content/search";

import { faceOf, pictureOf, sizeOf } from "../drawings";
import styles from "./Pennant.module.css";

interface Props {
  /** The rank of the result, as the API sent it. */
  readonly rank: number;
}

/**
 * The rank of a result: a pennant on its pole, with the number set on it in type. The
 * pennant of the first is the pennant of the tenth: one drawing, one colour and one size,
 * because nobody wins.
 *
 * The number is drawn for the eye, and the rank is said in words to whoever hears the page.
 */
export function Pennant({ rank }: Props) {
  const { width, height } = sizeOf("ui-flag");
  const face = faceOf("ui-flag");
  // A rank of one figure is set as a rank of two is, so the first has the pennant of the
  // tenth. A rank of three is set smaller, and stays on its pennant.
  const figures = Math.max(2, String(Math.trunc(Math.abs(rank))).length);
  const style = {
    "--art": `url("${pictureOf("ui-flag")}")`,
    "--w": width,
    "--h": height,
    "--left": face.left,
    "--top": face.top,
    "--wide": face.width,
    "--high": face.height,
    "--figures": figures,
  } as CSSProperties;
  return (
    <span className={styles.pennant} style={style}>
      <span className="visually-hidden">{RESULTS.rank(rank)}</span>
      <span className={styles.figure} aria-hidden="true">
        {rank}
      </span>
    </span>
  );
}
