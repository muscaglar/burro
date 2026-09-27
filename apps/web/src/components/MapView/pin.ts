/**
 * The pin of the map, as its style sheet is handed it: the drawing, its size, and the
 * face the drawing leaves bare for a number. The number is set on the face in type.
 *
 * A pin is drawn in two places, on the map and in what explains the map, and is one
 * drawing in both. It is named here, where its name is held to the list of drawings.
 */

import { faceOf, pictureOf, sizeOf, type Drawing } from "../kit/drawings";

const PIN: Drawing = "pin";

/** What the style sheet needs of the pin, by the names it reads them under. All are counts of art pixels but the first. */
export function pinDrawn(): Readonly<Record<string, string>> {
  const { width, height } = sizeOf(PIN);
  const face = faceOf(PIN);
  return {
    "--art": `url("${pictureOf(PIN)}")`,
    "--w": String(width),
    "--h": String(height),
    "--left": String(face.left),
    "--top": String(face.top),
    "--wide": String(face.width),
    "--high": String(face.height),
  };
}
