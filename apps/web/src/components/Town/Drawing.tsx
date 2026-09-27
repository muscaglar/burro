import type { CSSProperties } from "react";

import { ART } from "@/lib/art/names";
import { CANVAS, framesIn, frameWidth, type Piece } from "@/lib/town/pieces";

import { pictureOf } from "../kit/drawings";
import styles from "./Drawing.module.css";

interface Props {
  /** Every piece of the town, in the order they are drawn in. */
  readonly pieces: readonly Piece[];
  /**
   * What the drawing is, and what it is made of, in words. Empty where the words that say
   * it stand beside it, in sight: it is then kept from a screen reader, and not said twice.
   */
  readonly says: string;
  /** True where it is drawn at the art pixel of the screen. Left out, at the pixel of the ground. */
  readonly large?: boolean;
}

/** What the style sheet needs of the canvas: its size, in art pixels. */
const canvas = { "--across": CANVAS.width, "--down": CANVAS.height } as CSSProperties;

/** What the style sheet needs of a piece: its picture, the frame of it, and where it stands. */
const laid = ({ drawing, frame, left, top }: Piece): CSSProperties =>
  ({
    "--art": `url("${pictureOf(drawing)}")`,
    "--w": frameWidth(drawing),
    "--h": ART[drawing].height,
    "--frames": framesIn(drawing),
    "--frame": frame,
    "--x": left,
    "--y": top,
  }) as CSSProperties;

/**
 * The drawing of a town, and nothing beside it: a canvas of one size, with every piece
 * laid on it where the rule put it. It is a picture that says in words what it shows.
 *
 * It takes no press and no focus, and nothing of it moves.
 */
export function Drawing({ pieces, says, large = false }: Props) {
  return (
    <span
      className={styles.drawing}
      style={canvas}
      data-size={large ? "large" : "small"}
      {...(says === "" ? { "aria-hidden": true } : { role: "img", "aria-label": says })}
    >
      {pieces.map((piece) => (
        <span key={`${piece.drawing} ${piece.left} ${piece.top}`} className={styles.piece} style={laid(piece)} />
      ))}
    </span>
  );
}
