/**
 * The picture of a town, pixel by pixel, as a browser draws it: every piece laid on the
 * canvas where the rule put it, in the order the pieces are drawn in.
 *
 * It reads the drawings from disk, as text, so it is for tests only. A test counts in it
 * what the rule says is there: a window that is lit, a tree, a roof. So the rule, the
 * drawings and where each is laid are held to each other, and a drawing that is changed by
 * hand cannot come to say what the rule did not.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { CANVAS, frameWidth, type Piece } from "./pieces";

/** One pixel: the colour it is drawn in, as the drawing writes it, or `null` where it is clear. */
export type Pixel = string | null;

/** One frame of a drawing: rows of pixels, from the top. */
export type Frame = readonly (readonly Pixel[])[];

const DRAWINGS = path.join(process.cwd(), "art", "town.sprite.txt");

/** Every drawing of the town, by its name: the whole of it, with its frames side by side. */
export function drawings(file = DRAWINGS): ReadonlyMap<string, Frame> {
  const palette = new Map<string, Pixel>();
  const found = new Map<string, Pixel[][]>();
  let mode = "";
  let name = "";
  for (const line of readFileSync(file, "utf8").split("\n")) {
    if ((line.startsWith("#") && mode !== "drawing") || line.trim() === "") continue;
    if (line.trim() === "palette") mode = "palette";
    else if (line.startsWith("==")) {
      name = line.slice(2).trim();
      found.set(name, []);
      mode = "drawing";
    } else if (mode === "palette") {
      const [key = "", colour = ""] = line.trim().split(" ");
      palette.set(key, colour.startsWith("#") ? colour.toLowerCase() : null);
    } else if (!line.startsWith("# ")) {
      found.get(name)?.push([...line].map((key) => palette.get(key) ?? null));
    }
  }
  return found;
}

/** One frame of a strip, counted from nought. */
export function frameOf(piece: Pick<Piece, "drawing" | "frame">, from = drawings()): Frame {
  const whole = from.get(piece.drawing) ?? [];
  const wide = frameWidth(piece.drawing);
  return whole.map((row) => row.slice(piece.frame * wide, (piece.frame + 1) * wide));
}

/** Where a piece has anything drawn, on the canvas: each pixel with its place and its colour. */
export function laid(piece: Piece, from = drawings()): readonly { readonly x: number; readonly y: number; readonly colour: string }[] {
  return frameOf(piece, from).flatMap((row, down) =>
    row.flatMap((colour, across) => (colour === null ? [] : [{ x: piece.left + across, y: piece.top + down, colour }])),
  );
}

/** The canvas with every piece laid on it in turn. What is laid later lies over what was laid before. */
export function pictureOf(pieces: readonly Piece[], from = drawings()): Pixel[][] {
  const canvas: Pixel[][] = Array.from({ length: CANVAS.height }, () => Array.from({ length: CANVAS.width }, () => null));
  for (const piece of pieces) {
    for (const { x, y, colour } of laid(piece, from)) {
      const row = canvas[y];
      // What would lie off the canvas is cut off, as the box of the drawing cuts it.
      if (row !== undefined && x >= 0 && x < CANVAS.width) row[x] = colour;
    }
  }
  return canvas;
}

/** How many pixels of a picture are of a colour. */
export function count(picture: Frame, colour: string): number {
  return picture.flat().filter((pixel) => pixel === colour).length;
}
