import type { ReactNode } from "react";

import { Folded } from "../Disclosure/Folded";
import { Summary, theArrow, type Stands } from "../Disclosure/Summary";
import styles from "./Fold.module.css";

/**
 * `bar`: a bar across what holds it, inside a box. `line`: a small one on a rule of ink,
 * inside what another fold opened. `ground`: one that stands on the grass, so its bar is a
 * box of its own, and what it opens stands boxes of its own on the grass under it.
 */
export type FoldKind = "bar" | "line" | "ground";

/** Where the bar of each kind stands, which says how the one bar of the website is framed. */
const STANDS: Readonly<Record<FoldKind, Stands>> = { bar: "alone", line: "small", ground: "boxed" };

interface Props {
  /** What the fold says: what a person would ask. It does not change when it opens. */
  readonly says: string;
  /**
   * What it is said of, for whoever hears the page and cannot see what the fold stands
   * under: the name of a vibe, of a source. It is said after the words, and is not drawn.
   */
  readonly of?: string;
  /** The id of the fold, which a link may lead to. */
  readonly id?: string;
  readonly kind?: FoldKind;
  /** A class of whatever lays the fold out. It sets where the fold stands, never how it is drawn. */
  readonly className?: string;
  readonly children: ReactNode;
}

/**
 * What is long, closed until it is pressed. It is the browser's own element, so that it
 * opens with scripts off, and is closed as the page is built: a page that explains is read
 * in short, and whoever wants all of it opens it.
 *
 * Its bar is the bar of every fold of the website: its words at its near end, and at its
 * far end its arrow, in a cell, which points down at what is closed and up once it is
 * open. While it is open the bar is amber. A small one, inside what another opened, is no
 * bar: it stands on a rule of ink, with its mark before its words. The fold draws none of
 * it: what is said here is where a fold stands, and the room round what it opens.
 *
 * A bar is where it was after it is pressed, open or closed. Nothing of it is lost while
 * it is closed: what it holds is in the page.
 */
export function Fold({ says, of, id, kind = "bar", className, children }: Props) {
  const stands = STANDS[kind];
  return (
    <Folded
      id={id}
      stands={stands}
      className={[styles.fold, className].filter(Boolean).join(" ")}
      data-fold={kind}
      // The arrow is handed once, to the fold, and its bar has it from there.
      style={theArrow()}
      bar={<Summary label={says} of={of} stands={stands} handed />}
    >
      <div className={styles.opened}>{children}</div>
    </Folded>
  );
}
