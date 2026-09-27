/**
 * The website's icon. With none, every page a browser opens asks for one and
 * is told there is none. It is one small drawing, written out in full, that loads
 * nothing and runs nothing: the head of Burro, who is a rabbit, as he is drawn
 * where he sits, on a ground of meadow.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";

const ROOT = path.resolve(__dirname, "..");
const APP = path.join(ROOT, "src", "app");
const ICON = path.join(APP, "icon.svg");
const written = () => readFileSync(ICON, "utf8");
const drawn = () => new DOMParser().parseFromString(written(), "image/svg+xml");
/** How many squares the grid of the drawing has, across and down. It is shown at 16 pixels and at 32. */
const GRID = 16;

/**
 * The colours of the look, by name, as the command that makes the pictures holds them.
 * `art.test` holds those to the colours of the style sheet, so the icon is held to both.
 */
function theColours(): Map<string, string> {
  const script = readFileSync(path.join(ROOT, "scripts", "gen-art.mjs"), "utf8");
  return new Map([...script.matchAll(/^ {2}\["([a-z]+)", "(#[0-9a-f]{6})"\],$/gm)].map(([, name, value]) => [name!, value!]));
}

/** Where in the drawing of him his head is: the icon is this much of his canvas, from its left and from its top. */
const HEAD = { left: 10, top: 3 };

/** The drawing `burro-sits`, as its text has it: a colour a pixel, and `null` where it is clear. */
function burroSits(): (string | null)[][] {
  const text = readFileSync(path.join(ROOT, "art", "burro.sprite.txt"), "utf8");
  const palette = new Map([...text.matchAll(/^(\S) (#[0-9a-f]{6})$/gm)].map(([, key, colour]) => [key!, colour!]));
  const drawn = text.slice(text.indexOf("== burro-sits\n")).split("\n").slice(1);
  const rows = drawn.slice(0, drawn.findIndex((line) => line.startsWith("=="))).filter((line) => line !== "" && !line.startsWith("#"));
  return rows.map((row) => [...row].map((key) => palette.get(key) ?? null));
}

const isColour = (value: string) => /^#[0-9a-f]{6}$/.test(value);
/** Every shape of the drawing, in the order it is laid down. */
const shapes = () => [...drawn().querySelectorAll("*")].filter((one) => !/^(svg|title|g)$/.test(one.tagName));

/** The icon as a browser paints it at 16 pixels: each rectangle laid over what was there, a square a pixel. */
function painted(): string[][] {
  const squares = Array.from({ length: GRID }, () => Array<string>(GRID).fill("nothing is drawn here"));
  for (const shape of shapes()) {
    const of = (name: string) => Number(shape.getAttribute(name) ?? "0");
    const fill = shape.getAttribute("fill") ?? shape.parentElement?.getAttribute("fill") ?? "no fill";
    for (let y = of("y"); y < of("y") + of("height"); y += 1) {
      for (let x = of("x"); x < of("x") + of("width"); x += 1) squares[y]![x] = fill;
    }
  }
  return squares;
}

describe("the website's icon", () => {
  test("test_the_website_has_an_icon_where_the_framework_looks_for_one", () => {
    // Next serves `app/icon.svg` and names it in the head of every page.
    expect(existsSync(ICON)).toBe(true);
    expect(readdirSync(APP).filter((name) => /^(icon|favicon|apple-icon)\./.test(name))).toEqual(["icon.svg"]);
  });

  test("test_the_icon_is_a_drawing_that_can_be_read", () => {
    const icon = drawn();

    expect(icon.querySelector("parsererror")).toBeNull();
    expect(icon.documentElement.tagName).toBe("svg");
    expect(icon.documentElement.getAttribute("viewBox")).toBe(`0 0 ${GRID} ${GRID}`);
    expect(icon.querySelector("title")?.textContent).toBe("Burro");
    // Small enough to be read by whoever opens it. It holds his head as it is drawn, with
    // what is lit and what is shaded, which is more than a head drawn for the icon alone held.
    expect(written().length).toBeLessThan(2400);
  });

  test("test_the_icon_loads_nothing_runs_nothing_and_needs_no_font", () => {
    const icon = drawn();
    const everything = [...icon.querySelectorAll("*")];

    expect(everything.map((one) => one.tagName).filter((tag) => /^(script|foreignObject|image|use|a|text|tspan|iframe)$/i.test(tag))).toEqual([]);
    expect(everything.flatMap((one) => [...one.attributes]).filter(({ name }) => /^on|href$/i.test(name))).toEqual([]);
    expect(/url\(|@import|javascript:/i.test(written())).toBe(false);
    // The one address in it is the name of what it is written in. Nothing is fetched from it.
    expect(written().match(/https?:\/\/[^"'\s)]+/g)).toEqual(["http://www.w3.org/2000/svg"]);
  });

  test("test_the_icon_is_drawn_in_the_colours_of_the_look_and_is_one_whatever_the_system_asks", () => {
    const ofTheLook = [...theColours().values()];
    const colours = [...new Set(written().match(/#[0-9a-f]{3,8}\b/gi) ?? [])];

    expect(ofTheLook.length).toBeGreaterThanOrEqual(17);
    expect(colours.length).toBeGreaterThan(2);
    expect(colours.filter((colour) => !ofTheLook.includes(colour))).toEqual([]);
    // Every colour is written as a fill, so that none comes in by a name or by a style.
    expect([...drawn().querySelectorAll("[fill]")].map((one) => one.getAttribute("fill")).filter((fill) => !isColour(fill ?? ""))).toEqual([]);
    expect(drawn().querySelectorAll("style, [style], [class], [stroke], [opacity]")).toHaveLength(0);
    // The look has no dark colours, so the icon does not ask the system which it prefers.
    expect(/prefers-color-scheme|light-dark\(|currentColor/i.test(written())).toBe(false);
  });

  test("test_the_icon_is_plain_rectangles_on_a_grid_so_that_it_is_sharp_at_sixteen_and_at_thirty_two", () => {
    // A rectangle whose edges lie on a grid of sixteen has, at 16 pixels, every edge on a
    // pixel, and at 32 on every other one. An edge between two pixels is drawn as a blur.
    const icon = drawn();
    const figures = shapes().flatMap((shape) =>
      ["x", "y", "width", "height"].map((name) => [name, shape.getAttribute(name) ?? "0"] as const),
    );
    const ends = shapes().map((shape) => {
      const of = (name: string) => Number(shape.getAttribute(name) ?? "0");
      return Math.max(of("x") + of("width"), of("y") + of("height"));
    });

    expect(shapes().length).toBeGreaterThan(10);
    expect(shapes().map((shape) => shape.tagName).filter((tag) => tag !== "rect")).toEqual([]);
    // Nothing is turned, stretched or moved off the grid.
    expect(icon.querySelectorAll("[transform]")).toHaveLength(0);
    expect(figures.filter(([, value]) => !/^\d+$/.test(value))).toEqual([]);
    expect(ends.filter((end) => end > GRID)).toEqual([]);
    expect(icon.documentElement.getAttribute("shape-rendering")).toBe("crispEdges");
    // The ground covers the whole of it, so that the icon reads on a tab of any colour.
    expect(shapes()[0]?.getAttribute("width")).toBe(String(GRID));
    expect(shapes()[0]?.getAttribute("height")).toBe(String(GRID));
  });

  test("test_the_icon_is_the_head_of_burro_as_he_sits_square_for_square", () => {
    // He is one rabbit wherever he is drawn. A square of the icon that is not meadow is the
    // colour his drawing has in that place, and his ears, which are all that stand in the
    // rows over his head, are there whole.
    const squares = painted();
    const ground = squares[0]![0]!;
    const his = burroSits();
    const drawn = (x: number, y: number) => his[y + HEAD.top]?.[x + HEAD.left] ?? null;
    const strange = squares.flatMap((row, y) => row.flatMap((square, x) => (square === ground || square === drawn(x, y) ? [] : [`${x}, ${y}`])));
    const ears = squares
      .slice(0, 8)
      .map((row, y) => row.map((square) => (square === ground ? null : square)).join() === Array.from({ length: GRID }, (_, x) => drawn(x, y)).join());

    expect(strange).toEqual([]);
    expect(ears).toEqual(Array(8).fill(true));
    // He is whole from the tip of his ear to his chin: the first row and the last hold some of him.
    expect([squares[0]!.some((square) => square !== ground), squares[GRID - 1]!.some((square) => square !== ground)]).toEqual([true, true]);
    expect(squares.every((row) => row[0] === ground && row[GRID - 1] === ground)).toBe(true);
  });

  test("test_the_rabbit_of_the_icon_is_on_meadow_and_has_his_colours_and_his_eye", () => {
    // He is a wild rabbit, brown and grey: his fur lit in sand and shaded in shade, pale at the
    // muzzle, his outline and his eye in ink. Not white, not pink. His eye is two squares and no more.
    const named = theColours();
    const his = ["ink", "fur", "sand", "shade", "page"].map((name) => named.get(name));
    const squares = painted();
    const ground = squares[0]![0]!;
    const ink = named.get("ink");
    const at = (x: number, y: number) => squares[y]?.[x] ?? ground;
    // Ink that touches no ink that touches the meadow is no outline: it is his eye.
    const outline = new Set<string>();
    const reach = (x: number, y: number) => {
      if (at(x, y) !== ink || outline.has(`${x},${y}`)) return;
      outline.add(`${x},${y}`);
      for (const [across, down] of [[1, 0], [-1, 0], [0, 1], [0, -1]] as const) reach(x + across, y + down);
    };
    squares.forEach((row, y) =>
      row.forEach((square, x) => {
        if (square === ink && [at(x - 1, y), at(x + 1, y), at(x, y - 1), at(x, y + 1)].includes(ground)) reach(x, y);
      }),
    );
    const eye = squares.flatMap((row, y) => row.filter((square, x) => square === ink && !outline.has(`${x},${y}`)));

    expect(ground).toBe(named.get("meadow"));
    expect([...new Set(squares.flat())].filter((square) => square !== ground).sort()).toEqual([...his].sort());
    expect(eye).toHaveLength(2);
  });
});
