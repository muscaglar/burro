"use client";

import type { CSSProperties, ReactNode } from "react";

import { pictureOf } from "../kit/drawings";
import { picturesOf } from "../kit/Press/kinds";
import styles from "./Small.module.css";

interface Props {
  readonly onPress: () => void;
  /** The whole name, where what is seen is the start of it: "Show the words", and of which thing. */
  readonly name?: string;
  /** A class of whatever lays the button out. It sets where the button stands, never how it is drawn. */
  readonly className?: string;
  readonly children: ReactNode;
}

/** The pictures of a small button: the plain button of the kit, as it stands and pressed. */
const DRAWN = (() => {
  const { up, down } = picturesOf("plain", false);
  return { "--art": `url("${pictureOf(up)}")`, "--art-down": `url("${pictureOf(down)}")` } as CSSProperties;
})();

/**
 * A small button of the look, for a control that stands beside a line of words or at the
 * end of one: the way to see, in the box, the words a thing was read from, and the words
 * that were not read. It is a native button of the size of a small control.
 *
 * It is drawn as Town Map draws a button, by the pictures of the button of the kit, at two
 * pixels of the screen to one of the drawing on every screen: a button of the kit is 44 px
 * high and no less, and these stand between the box and the first result. Under a press
 * its picture gives way to the picture of the button pressed, and the button stays where it
 * is and as large as it is.
 */
export function Small({ onPress, name, className, children }: Props) {
  return (
    <button
      type="button"
      className={[styles.small, "target-min", className].filter(Boolean).join(" ")}
      aria-label={name}
      onClick={onPress}
    >
      <span className={styles.face} style={DRAWN}>
        <span className={styles.says}>{children}</span>
      </span>
    </button>
  );
}
