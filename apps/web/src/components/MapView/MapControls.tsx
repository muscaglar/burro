"use client";

import { MAP } from "@/content/map";

import { Press } from "../kit/Press/Press";
import styles from "./MapView.module.css";

interface Props {
  readonly disabled: boolean;
  readonly onMove: (how: "in" | "out" | "whole") => void;
}

/**
 * The buttons that move the map: nearer, further, and the whole city. With
 * them nothing on the map needs dragging or pinching. They sit in a row under
 * the map, where none of them covers an area.
 *
 * Each is a button of the look. Nearer and further bear a sign, drawn in
 * pixels of the size the button is drawn in, and say what they do to whoever
 * hears the page. Until the map is drawn a button does nothing, says that it
 * is off, and keeps the focus if it has it.
 */
export function MapControls({ disabled, onMove }: Props) {
  return (
    <div className={styles.controls} role="group" aria-label={MAP.controls}>
      <Press name={MAP.zoomIn} off={disabled} onPress={() => onMove("in")}>
        <span className={styles.sign} data-sign="more" aria-hidden="true" />
      </Press>
      <Press name={MAP.zoomOut} off={disabled} onPress={() => onMove("out")}>
        <span className={styles.sign} data-sign="less" aria-hidden="true" />
      </Press>
      <Press off={disabled} onPress={() => onMove("whole")}>
        {MAP.whole}
      </Press>
    </div>
  );
}
