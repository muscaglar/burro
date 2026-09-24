"use client";

import { MAP } from "@/content/map";

import styles from "./MapView.module.css";

interface Props {
  readonly disabled: boolean;
  readonly onMove: (how: "in" | "out" | "whole") => void;
}

/**
 * The buttons that move the map: nearer, further, and the whole city. With
 * them nothing on the map needs dragging or pinching. They sit in a row under
 * the map, where none of them covers an area.
 */
export function MapControls({ disabled, onMove }: Props) {
  return (
    <div className={styles.controls} role="group" aria-label={MAP.controls}>
      <button
        type="button"
        className={`${styles.control} target-min`}
        aria-label={MAP.zoomIn}
        disabled={disabled}
        onClick={() => onMove("in")}
      >
        <span aria-hidden="true">+</span>
      </button>
      <button
        type="button"
        className={`${styles.control} target-min`}
        aria-label={MAP.zoomOut}
        disabled={disabled}
        onClick={() => onMove("out")}
      >
        <span aria-hidden="true">−</span>
      </button>
      <button
        type="button"
        className={`${styles.control} ${styles.whole} target-min`}
        disabled={disabled}
        onClick={() => onMove("whole")}
      >
        {MAP.whole}
      </button>
    </div>
  );
}
