import type { CSSProperties, ReactNode } from "react";

import { pictureOf, sizeOf, type Drawing } from "../kit/drawings";
import { Frame } from "../kit/Frame/Frame";
import { holdsAFigure } from "../kit/reads";
import styles from "./Disclosure.module.css";
import { BAR_AT_REST, type BarAtRest } from "./look";

/**
 * Where a bar stands, which says what frames it. `stacked`: one of a stack of bars, in a
 * box, with a rule of ink between it and the next. `alone`: by itself, with an edge of ink
 * and a shadow of its own. `boxed`: by itself on the grass among the boxes of a page, as a
 * box of the kit. `small`: no bar, but a small fold beside a line of text, on a rule of ink.
 */
export type Stands = "stacked" | "alone" | "boxed" | "small";

/** The arrow of a fold. It is drawn pointing up, and the style sheet turns it. */
const ARROW: Drawing = "ui-arrow";

/** The arrow, as the style sheet is handed it: its picture, and its size in art pixels. */
export function theArrow(): CSSProperties {
  const { width, height } = sizeOf(ARROW);
  return {
    "--arrow": `url("${pictureOf(ARROW)}")`,
    "--arrow-w": width,
    "--arrow-h": height,
  } as CSSProperties;
}

/** The classes of what takes the press, by where it stands: a bar, or a small fold. */
export function drawnAs(stands: Stands): string {
  if (stands === "small") return `${styles.button} ${styles.small} target-min`;
  const kind = stands === "alone" ? styles.alone : stands === "boxed" ? styles.boxed : null;
  return [styles.button, styles.bar, kind, "target"].filter(Boolean).join(" ");
}

/**
 * The class of the browser's own element that folds, which holds a bar and what it opens:
 * the style sheet tells by it whether the bar is open. One of a stack has a rule of ink
 * between it and the next.
 */
export function foldOf(stands: Stands, className?: string): string {
  return [styles.fold, stands === "stacked" ? styles.stacked : null, className].filter(Boolean).join(" ");
}

interface Props {
  /** What the bar says. It names what is shown, and does not change when it opens. */
  readonly label: ReactNode;
  /**
   * What it is said of, for whoever hears the page and cannot see what the bar stands
   * under: the name of a vibe, of a source. It is said after the words, and is not drawn.
   */
  readonly of?: string;
  readonly stands?: Stands;
  /**
   * The rank of the heading, where what the bar says is the heading of what it opens: the
   * part is then found by its heading, as any part of a page is. Left out, it is no heading.
   */
  readonly heading?: 2 | 3 | 4;
  /** The drawing that stands before its name. It is dress, and is kept from whoever hears the page by what draws it. */
  readonly drawn?: ReactNode;
  /**
   * True where whatever holds the fold hands the arrow to all that it holds, as the page
   * of an area does. The bar then bears no style of its own: nothing that is written on an
   * element stands among the figures of the census.
   */
  readonly handed?: boolean;
  /** What a bar stands on while it is closed. It is a matter of taste, which `look.ts` chooses: a page hands none. */
  readonly rest?: BarAtRest;
}

/**
 * The bar of a fold that is the browser's own, so that it folds with scripts off. It is
 * the `summary` of a `details`, and is drawn as every bar that folds is: its name at its
 * near end, and at its far end its arrow, in a cell, which points down while the fold is
 * closed and up while it is open. While it is open the bar is amber.
 *
 * It is what takes the press, and the browser opens and closes what it stands in. It says
 * whether it is open to whoever hears the page, as the browser's own element does.
 *
 * The arrow is first in the bar and is laid out last: it says nothing, wherever it stands.
 * What holds the bar says `foldOf` of itself, so that the style sheet knows it for a fold.
 */
export function Summary({ label, of, stands = "stacked", heading, drawn, handed = false, rest = BAR_AT_REST }: Props) {
  const reads = typeof label !== "string" || holdsAFigure(label);
  const said = (
    <>
      {label}
      {of === undefined ? null : <span className="visually-hidden">: {of}</span>}
    </>
  );

  if (stands === "small") {
    return (
      <summary className={drawnAs(stands)}>
        <span className={styles.says} data-reads={reads}>
          <span className={styles.mark} aria-hidden="true" />
          {said}
        </span>
      </summary>
    );
  }

  const Told = heading === undefined ? "span" : (`h${heading}` as const);
  const holds = (
    <>
      <span className={styles.mark} aria-hidden="true" />
      {drawn === undefined ? null : <span className={styles.drawn}>{drawn}</span>}
      <Told className={styles.told} data-reads={reads}>
        {said}
      </Told>
    </>
  );
  const its = {
    className: drawnAs(stands),
    style: handed ? undefined : theArrow(),
    "data-arrow": "end",
    "data-rest": rest,
  } as const;

  // On the grass the bar is a box of the kit, which brings the rule and the shadow every box has.
  if (stands === "boxed") {
    return (
      <Frame kind="box" as="summary" bare {...its}>
        {holds}
      </Frame>
    );
  }
  return <summary {...its}>{holds}</summary>;
}
