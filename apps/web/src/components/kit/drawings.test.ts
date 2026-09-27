/** @jest-environment node */
/**
 * No drawing of the website draws an edge, a rule or a line in pieces. A person who walked
 * the website did not know what a dashed edge was for, and asked for none: and a line of
 * dots is drawn in a picture as well as by a style sheet, where no search for "dashed"
 * finds it. What is left in dots is a drawing of a thing, and is named here with what it is.
 *
 * It reads the drawings as they are written, one character a pixel, and so holds whatever
 * is drawn next as well as what is there. What marks a blank in the town of an area is held
 * beside the town, which alone may name a drawing of one.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { isDrawn, sizeOf } from "./drawings";

const ART = path.join(__dirname, "../../../art");
const CLEAR = ".";

interface Written {
  readonly name: string;
  /** The rows of the drawing, one character a pixel. */
  readonly rows: readonly string[];
  /** What each character of it is, as the palette of its file says: a colour, or clear. */
  readonly palette: ReadonlyMap<string, string>;
}

/** Every drawing, as its file writes it. */
const DRAWINGS: readonly Written[] = readdirSync(ART)
  .filter((file) => file.endsWith(".sprite.txt"))
  .sort()
  .flatMap((file) => {
    const found: { name: string; rows: string[]; palette: Map<string, string> }[] = [];
    const palette = new Map<string, string>();
    let inPalette = false;
    for (const line of readFileSync(path.join(ART, file), "utf8").split("\n")) {
      if (line.startsWith("== ")) {
        inPalette = false;
        found.push({ name: line.slice(3).trim(), rows: [], palette });
      } else if (line.trim() === "palette") {
        inPalette = true;
      } else if (line.startsWith("#") || line.trim() === "") {
        continue;
      } else if (inPalette) {
        const [character = "", colour = ""] = line.trim().split(/\s+/);
        palette.set(character, colour);
      } else {
        found[found.length - 1]?.rows.push(line);
      }
    }
    return found;
  });

const written = (name: string): Written => {
  const found = DRAWINGS.find((drawing) => drawing.name === name);
  if (found === undefined) throw new Error(`no drawing is named ${name}`);
  return found;
};

const BY_A_SIDE = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
] as const;
interface Pixel {
  readonly x: number;
  readonly y: number;
}

const at = ({ rows }: Written, x: number, y: number) => rows[y]?.[x] ?? CLEAR;

/** Every pixel of a drawing that is of one colour of the look, by the name the style sheet gives the colour. */
function pixelsOf(drawing: Written, colour: string): Pixel[] {
  return drawing.rows.flatMap((row, y) => [...row].flatMap((character, x) => (drawing.palette.get(character) === colour ? [{ x, y }] : [])));
}

/**
 * The lines of dots in a drawing: three pixels or more of one colour in one row or one
 * column, each two from the next, where none touches a pixel of its colour by a side. So a
 * stripe and a chequer are none, and a line of dots is one, whichever way it runs.
 */
function linesOfDots(drawing: Written): string[] {
  const alone = (x: number, y: number) => {
    const here = at(drawing, x, y);
    return here !== CLEAR && BY_A_SIDE.every(([across, down]) => at(drawing, x + across, y + down) !== here);
  };
  const found: string[] = [];
  drawing.rows.forEach((row, y) =>
    [...row].forEach((here, x) => {
      if (!alone(x, y)) return;
      for (const [across, down] of [
        [2, 0],
        [0, 2],
      ] as const) {
        const like = (n: number) => alone(x + across * n, y + down * n) && at(drawing, x + across * n, y + down * n) === here;
        if (like(-1)) continue;
        let dots = 1;
        while (like(dots)) dots += 1;
        if (dots >= 3) found.push(`${dots} of ${drawing.palette.get(here) ?? here} along a ${across > 0 ? "row" : "column"}`);
      }
    }),
  );
  return found;
}

/** How many pixels of a line touch a pixel of it by a side. */
const touching = (line: readonly Pixel[], one: Pixel) =>
  line.filter((other) => BY_A_SIDE.some(([across, down]) => other.x === one.x + across && other.y === one.y + down)).length;

const SHADE = "#65566a";

describe("no drawing draws an edge in pieces", () => {
  test("test_every_drawing_is_read_and_each_is_one_the_website_has_made", () => {
    expect(DRAWINGS.length).toBeGreaterThan(100);
    expect(DRAWINGS.filter((drawing) => !isDrawn(drawing.name)).map((drawing) => drawing.name)).toEqual([]);
    for (const drawing of DRAWINGS) {
      if (!isDrawn(drawing.name)) continue;
      const { width, height } = sizeOf(drawing.name);
      expect([drawing.name, drawing.rows.length, new Set(drawing.rows.map((row) => row.length)).size, drawing.rows[0]?.length]).toEqual([
        drawing.name,
        height,
        1,
        width,
      ]);
    }
  });

  test("test_no_drawing_holds_a_line_of_dots_but_where_the_dots_are_a_thing_that_is_drawn", () => {
    // What is in dots and is no edge: each is a thing, and is named with what it is. A
    // drawing that comes to hold a line of dots fails here until it is drawn whole, or is
    // written down as the thing it is.
    const THINGS: Readonly<Record<string, string>> = {
      "thing-everyday-on-foot": "the eyelets of a boot, and the studs of its sole",
      "thing-foodie": "the tines of a fork",
      "thing-foodie-off": "the tines of a fork, in outline",
      "thing-homes": "the windows of a block of flats",
    };
    const found = DRAWINGS.flatMap((drawing) => (linesOfDots(drawing).length > 0 ? [drawing.name] : []));

    expect(found.filter((name) => !Object.hasOwn(THINGS, name))).toEqual([]);
    // And each that is written down is drawn, and still holds what it was written down for.
    expect(Object.keys(THINGS).filter((name) => !found.includes(name))).toEqual([]);
  });

  test("test_the_plot_of_an_end_that_has_no_picture_is_marked_out_by_one_whole_line", () => {
    // It stands beside the heading of the page that is not there, and at an end of a scale
    // that nobody has drawn. Its plot was a square of dots.
    const blank = written("key-blank");
    const plot = pixelsOf(blank, SHADE);

    expect(plot.length).toBeGreaterThanOrEqual(8);
    expect(plot.filter((one) => touching(plot, one) !== 2)).toEqual([]);
    expect(linesOfDots(blank)).toEqual([]);
    // Seen in a browser, beside "Page not found": a plot as high as it was wide was a box
    // to be ticked. It lies on the ground, low and wide, as a plot does, and is no square.
    const across = plot.map((one) => one.x);
    const down = plot.map((one) => one.y);
    const [wide, high] = [Math.max(...across) - Math.min(...across) + 1, Math.max(...down) - Math.min(...down) + 1];
    expect(wide).toBeGreaterThanOrEqual(high * 2);
    // It stands on the line the house beside it stands on.
    expect(Math.max(...down)).toBe(blank.rows.length - 1);
  });
});
