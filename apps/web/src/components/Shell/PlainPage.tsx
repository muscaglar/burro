import type { ReactNode } from "react";

import { Art } from "../kit/Art/Art";
import { Frame } from "../kit/Frame/Frame";
import styles from "./PlainPage.module.css";

interface Props {
  /**
   * `lost` is a page that is not there. `fault` is a page that could not be shown, and is
   * marked as a failure is. `held` is a page that is held back, and is marked as a notice
   * is. A fault and a page held back are said at once to whoever hears the page.
   */
  readonly kind: PlainKind;
  /** The one heading of the page. */
  readonly title: string;
  /** What the page says: a sentence, or a few. */
  readonly text: string;
  /** The one way on, where there is one: a link or a button, drawn as a button is. */
  readonly children?: ReactNode;
}

export type PlainKind = "lost" | "fault" | "held";

/**
 * A page that says one thing and offers one way on at the most: the page that is not
 * there, the two pages of a fault, and what stands in place of a page that is held back.
 * It is one box on the meadow, as the box is that Burro asks in.
 *
 * It shows no figure and names no place. Burro is not drawn on it: he is drawn while a
 * person searches, and beside no failure. A page that is not there has the drawing of a
 * plot with nothing built on it, which is dress and says nothing to a screen reader.
 */
export function PlainPage({ kind, title, text, children }: Props) {
  return (
    <div className={styles.page} data-dressed>
      <Frame kind="box" bare className={styles.box} role={kind === "lost" ? undefined : "alert"} data-says={kind}>
        <div className={styles.head}>
          {kind === "lost" ? <Art name="key-blank" alt="" /> : <span className={styles.mark} aria-hidden="true" />}
          <h1 className={styles.title}>{title}</h1>
        </div>
        <p className={styles.says}>{text}</p>
        {children === undefined ? null : <div className={styles.way}>{children}</div>}
      </Frame>
    </div>
  );
}
