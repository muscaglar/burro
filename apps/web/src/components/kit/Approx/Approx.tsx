import { KNOWN } from "@/content/kit";

import { asStyle } from "../Art/Art";
import styles from "./Approx.module.css";

interface Props {
  /** What it says. Left out, the two words of the kit. */
  readonly says?: string;
  /** A class of whatever lays it out. It sets where it stands, never how it is drawn. */
  readonly className?: string | undefined;
}

const classes = (className: string | undefined) => [styles.approx, className].filter(Boolean).join(" ");

/**
 * Said beside a figure that was worked out from some of what goes into it, or that is an
 * estimate: the mark of what is not whole, and two words after it. The mark is one step of
 * a band, chequered as the step is that a peg stands on where a band is such a figure. It
 * is drawn the same wherever a gauge is drawn, so that one mark means one thing on every
 * page: a result, the page of an area, a comparison and the key to the drawings.
 *
 * It says no more than that. What the figure was worked out from is said beside it where a
 * page has the room, and where the figure is opened: there the mark may stand before the
 * sentence that says so, which it is handed. The mark is dress, and the words are what is
 * heard.
 */
export function Approx({ says = KNOWN.some, className }: Props) {
  return (
    <span className={classes(className)} data-known="some">
      <span className={styles.mark} style={asStyle("ui-approx")} aria-hidden="true" />
      <span className={styles.said}>{says}</span>
    </span>
  );
}

/**
 * Said beside the name of a thing that the area has no figure for: a step that holds
 * nothing, and two words. What is not known is said to be not known. The step has the
 * whole edge of any step, and is neither nought nor the middle.
 */
export function NoData({ says = KNOWN.none, className }: Props) {
  return (
    <span className={classes(className)} data-known="none">
      <span className={styles.blank} aria-hidden="true" />
      <span className={styles.said}>{says}</span>
    </span>
  );
}
