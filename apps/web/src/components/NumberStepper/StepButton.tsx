"use client";

import type { CSSProperties } from "react";

import { pictureOf, sizeOf, type Drawing } from "../kit/drawings";
import styles from "./NumberStepper.module.css";

interface Props {
  /** Which way it steps: `less` is the minus and `more` is the plus. */
  readonly way: "less" | "more";
  /** Its name: what it does, and to what. Its sign is in its drawing, and nothing is written on it. */
  readonly name: string;
  /**
   * True where there is nothing to step from, as with a budget that is not set: the
   * button is switched off, and no keyboard stops on it.
   */
  readonly disabled?: boolean;
  /**
   * True where it has been pressed until there is nothing left to do. It says that it is
   * off and is not switched off, so that it keeps the focus it was pressed with.
   */
  readonly off?: boolean;
  readonly onPress: () => void;
}

const DRAWN: Readonly<Record<Props["way"], readonly [up: Drawing, down: Drawing]>> = {
  less: ["btn-less", "btn-less-down"],
  more: ["btn-more", "btn-more-down"],
};

/**
 * The button of a step, as Town Map draws a button: one drawing, shown whole at its own
 * size, with its sign on it and its shadow under it. Under a press it gives way to the
 * drawing of the button pressed, which is of the same size, so the button does not move.
 *
 * Between the two of a step stands a field, or a gauge.
 */
export function StepButton({ way, name, disabled = false, off = false, onPress }: Props) {
  const [up, down] = DRAWN[way];
  const { width, height } = sizeOf(up);
  const drawn = {
    "--art": `url("${pictureOf(up)}")`,
    "--art-down": `url("${pictureOf(down)}")`,
    "--w": width,
    "--h": height,
  } as CSSProperties;
  return (
    <button
      type="button"
      className={`${styles.step} target`}
      style={drawn}
      aria-label={name}
      aria-disabled={off ? true : undefined}
      disabled={disabled}
      onClick={onPress}
    />
  );
}
