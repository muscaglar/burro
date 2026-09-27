import type { CSSProperties } from "react";

import { pictureOf, sizeOf, type Drawing } from "../drawings";
import styles from "./Art.module.css";

interface Props {
  readonly name: Drawing;
  /** What the drawing shows, in words. Empty where it is decoration, or stands beside the words that say it. */
  readonly alt: string;
}

/** What a style sheet needs of a drawing to show it: where it is served from, and its size in art pixels. */
export function asStyle(name: Drawing): CSSProperties {
  const { width, height } = sizeOf(name);
  return { "--art": `url("${pictureOf(name)}")`, "--w": width, "--h": height } as CSSProperties;
}

/**
 * One drawing, at its own size times the art pixel. It is never stretched, never shown at a
 * percentage and never at a fraction: its width and its height are whole counts of art
 * pixels, read from the list the pictures are made with.
 *
 * With words it is a picture that says them. With none it is kept from a screen reader.
 */
export function Art({ name, alt }: Props) {
  return (
    <span
      className={styles.art}
      style={asStyle(name)}
      {...(alt === "" ? { "aria-hidden": true } : { role: "img", "aria-label": alt })}
    />
  );
}
