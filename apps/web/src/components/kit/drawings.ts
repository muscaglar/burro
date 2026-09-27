/**
 * The drawings, as the kit reads them. This is the one file of the kit that reads the list
 * the pictures are made with, so that a change to how the list is written is a change here.
 *
 * A drawing is named by its file: `jar-leafy` is served as /art/jar-leafy.png. Its size is
 * in art pixels, and it is shown at that size times `--px`, never at any other.
 */

import { ART, type ArtName, type Drawn } from "@/lib/art/names";

/** The name of a drawing that has been made. */
export type Drawing = ArtName;

export interface Size {
  readonly width: number;
  readonly height: number;
}

/** A part of a drawing, in art pixels: where it begins, from the left and from the top, and its size. */
export interface Place extends Size {
  readonly left: number;
  readonly top: number;
}

/** What the list holds of a drawing, read as the list types it. */
const drawn = (name: Drawing): Drawn => ART[name];

/** True of a name that has a drawing. */
export function isDrawn(name: string): name is Drawing {
  return Object.hasOwn(ART, name);
}

/** The width and the height of a drawing, in art pixels. */
export function sizeOf(name: Drawing): Size {
  const { width, height } = drawn(name);
  return { width, height };
}

/** How many frames stand side by side in a strip. One, of a drawing that is no strip. */
export function framesOf(name: Drawing): number {
  return drawn(name).frames ?? 1;
}

/** Where a figure is set on a drawing in type. The whole of it, where the drawing marks no place. */
export function faceOf(name: Drawing): Place {
  const { width, height, face } = drawn(name);
  if (face === undefined) return { left: 0, top: 0, width, height };
  return { left: face[0], top: face[1], width: face[2], height: face[3] };
}

/** Where a frame is cut in nine, as `border-image-slice` is written. `null` of a drawing that is no frame. */
export function cutOf(name: Drawing): readonly [top: number, right: number, foot: number, left: number] | null {
  return drawn(name).cut ?? null;
}

/** Where a drawing is served from: the website's own origin, and no other. */
export function pictureOf(name: Drawing): string {
  return `/art/${name}.png`;
}

/** A code of the service as a drawing names it: `quiet_residential` is `quiet-residential`. */
export function inAName(code: string): string {
  return code.toLowerCase().replaceAll("_", "-");
}
