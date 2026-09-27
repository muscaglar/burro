import type { ReactNode } from "react";

import { Board } from "./About";
import styles from "./KeyRows.module.css";

interface GroupProps {
  /** The id of its heading, which the group is named by. */
  readonly id: string;
  /** What its heading says: where a person meets what the group holds. */
  readonly title: string;
  /** What is said first of the group, over its rows. */
  readonly lead?: ReactNode;
  /**
   * `pairs`: two rows side by side where each has the room of a line that reads well.
   * `lines`: one row to a line, for drawings that are wide and sentences that are long.
   */
  readonly lay?: "pairs" | "lines";
  /**
   * A class of whatever lays the group out. It sets where the group stands, and how wide
   * the room of a wide drawing is (`--drawn-wide`), never how the group is drawn.
   */
  readonly className?: string;
  /** The rows of the group, each a `KeyRow`. */
  readonly children: ReactNode;
}

/**
 * A part of the key to the drawings: what is met in one place, under a small heading that
 * says where, so that somebody who has seen a drawing finds it. Its rows stand one under
 * the other, and side by side where there is room.
 */
export function KeyGroup({ id, title, lead, lay = "pairs", className, children }: GroupProps) {
  return (
    <section className={[styles.group, className].filter(Boolean).join(" ")} data-lay={lay} aria-labelledby={id}>
      <Board as="h3" id={id}>
        {title}
      </Board>
      {lead === undefined ? null : <div className={styles.lead}>{lead}</div>}
      <ul className={styles.rows}>{children}</ul>
    </section>
  );
}

/**
 * `small`: a drawing no wider than a thing of a search, which stands beside its sentence
 * on every screen. `wide`: one that stands over its sentence on a narrow screen and beside
 * it on a wider one. `many`: many drawings, which stand under what is said of them.
 */
export type Drawn = "small" | "wide" | "many";

interface RowProps {
  /** What the row is of, by a name a test may find it by. */
  readonly of: string;
  readonly size?: Drawn;
  /** What is drawn: the drawing itself, as the page that draws it shows it. */
  readonly drawn: ReactNode;
  /** What else the row says of itself to its style sheet, as an attribute: the part of a town it is of. */
  readonly part?: string;
  /** What it means, in a sentence or two: one paragraph, or more. */
  readonly children: ReactNode;
}

/**
 * One row of the key: a drawing, at the size it is met, and what it means. What is said
 * comes first for whoever hears the page, and the drawing stands before it for the eye.
 */
export function KeyRow({ of, size = "small", drawn, part, children }: RowProps) {
  return (
    <li className={styles.row} data-key={of} data-drawn={size} data-part={part}>
      <div className={styles.says} data-says>
        {children}
      </div>
      <div className={styles.drawn} data-drawn-here>
        {drawn}
      </div>
    </li>
  );
}
