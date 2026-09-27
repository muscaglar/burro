import type { ComponentProps, ElementType, ReactNode } from "react";

import styles from "./Frame.module.css";

/**
 * The frames there are. `box` holds a thing a person acts on: the search box, a result, a
 * question, a panel. `box-on` is the same box while it is the one chosen or in hand.
 * `plain` holds a list of many small things, where a shadow on every row would be noise.
 */
export type FrameKind = "box" | "box-on" | "plain";

export const FRAME_KINDS: readonly FrameKind[] = ["box", "box-on", "plain"];

type Props<Element extends ElementType> = {
  readonly kind: FrameKind;
  /** The element the frame is. A `div` where none is given. */
  readonly as?: Element;
  /**
   * True where what stands in the frame brings its own room, as a table or a list of rows
   * does. Left out, the frame keeps what it holds clear of its edge.
   */
  readonly bare?: boolean;
  /** A class of whatever lays the frame out. It sets where the frame stands, never how it is drawn. */
  readonly className?: string;
  readonly children?: ReactNode;
} & Omit<ComponentProps<Element>, "as" | "className" | "children">;

/**
 * A box: page, a double rule of ink with a notch at each corner, and a hard shadow that
 * falls down and to the right. It is the one frame of the look, and everything that is
 * read stands in one.
 *
 * It is a box and nothing more: what it is, a section or a paragraph or an item of a list,
 * is for whatever draws it to say, and whatever that element takes the frame hands on to it.
 *
 * A frame brings its own ground, which lies behind what it holds: whatever lays it out
 * gives it none, and cuts nothing off at its edge.
 *
 * The edge of ink of every frame that stands on the grass ends on one line. A box keeps
 * the room of its shadow at its far side, and a plain frame on the grass keeps as much.
 */
export function Frame<Element extends ElementType = "div">({
  kind,
  as,
  bare = false,
  className,
  children,
  ...rest
}: Props<Element>) {
  const Box: ElementType = as ?? "div";
  return (
    <Box
      className={[styles.frame, styles[kind], bare ? null : styles.roomy, className].filter(Boolean).join(" ")}
      data-kind={kind}
      {...rest}
    >
      {children}
    </Box>
  );
}
