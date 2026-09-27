/** @jest-environment node */
/**
 * The drawings, and the pictures made of them.
 *
 * A drawing is text, one character a pixel, in `art/`. `npm run gen:art` makes a picture of
 * each in `public/art/`, and the list of their names. What is read here is read a second
 * time, by other code than the command's: the drawings by a reader of its own, the pictures
 * by Node's zlib, which had no part in writing them.
 */

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { inflateSync } from "node:zlib";

import { STRIP } from "@/content/search";
import { recordedFolder } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";
import { ART, type ArtName, type Drawn } from "@/lib/art/names";

const ROOT = path.resolve(__dirname, "..");
const DRAWINGS = path.join(ROOT, "art");
const PICTURES = path.join(ROOT, "public", "art");

const CLEAR = "clear";
type Pixel = string;

interface Drawing {
  readonly name: string;
  readonly file: string;
  readonly pixels: readonly (readonly Pixel[])[];
}

/** The drawings of one file, as the format has them: a palette, then each drawing under `== name`. */
function drawingsOf(text: string, file: string): Drawing[] {
  const palette = new Map<string, Pixel>();
  const found: { name: string; rows: string[][] }[] = [];
  let mode = "";
  for (const line of text.split("\n")) {
    if ((line.startsWith("#") && mode !== "drawing") || line.trim() === "") continue;
    if (line.trim() === "palette") mode = "palette";
    else if (line.startsWith("==")) {
      found.push({ name: line.slice(2).trim(), rows: [] });
      mode = "drawing";
    } else if (mode === "palette") {
      const [key = "", colour = ""] = line.trim().split(" ");
      palette.set(key, colour.startsWith("#") ? colour.toLowerCase() : CLEAR);
    } else if (!line.startsWith("# ")) found.at(-1)?.rows.push([...line]);
  }
  return found.map(({ name, rows }) => ({
    name,
    file,
    pixels: rows.map((row) => row.map((key) => palette.get(key) ?? `not in the palette: ${key}`)),
  }));
}

function everyDrawing(): Drawing[] {
  return readdirSync(DRAWINGS)
    .filter((file) => file.endsWith(".sprite.txt"))
    .sort()
    .flatMap((file) => drawingsOf(readFileSync(path.join(DRAWINGS, file), "utf8"), file));
}

interface Picture {
  readonly width: number;
  readonly height: number;
  readonly colours: readonly Pixel[];
  readonly pixels: readonly (readonly Pixel[])[];
}

/** A picture as a browser reads it: a PNG with a palette, unpacked by zlib. */
function opened(png: Buffer): Picture {
  if (png.subarray(0, 8).toString("latin1") !== "\x89PNG\r\n\x1a\n") throw new Error("Not a PNG.");
  const chunks = new Map<string, Buffer[]>();
  for (let at = 8; at < png.length; ) {
    const length = png.readUInt32BE(at);
    const kind = png.subarray(at + 4, at + 8).toString("latin1");
    chunks.set(kind, [...(chunks.get(kind) ?? []), png.subarray(at + 8, at + 8 + length)]);
    at += 12 + length;
  }
  const header = chunks.get("IHDR")?.[0];
  const palette = chunks.get("PLTE")?.[0];
  if (header === undefined || palette === undefined) throw new Error("A picture has a header and a palette.");
  const [width, height, depth, kind] = [header.readUInt32BE(0), header.readUInt32BE(4), header[8] ?? 0, header[9]];
  if (kind !== 3) throw new Error("A picture is drawn with a palette.");
  const clear = chunks.get("tRNS")?.[0] ?? Buffer.alloc(0);
  const colours = Array.from({ length: palette.length / 3 }, (_, index) =>
    (clear[index] ?? 255) === 0 ? CLEAR : `#${palette.subarray(index * 3, index * 3 + 3).toString("hex")}`,
  );

  const lines = inflateSync(Buffer.concat(chunks.get("IDAT") ?? []));
  const stride = 1 + Math.ceil((width * depth) / 8);
  const pixels = Array.from({ length: height }, (_, y) => {
    const line = lines.subarray(y * stride, (y + 1) * stride);
    if (line[0] !== 0) throw new Error("A line of a picture is written as it is, with no filter.");
    return Array.from({ length: width }, (__, x) => {
      const byte = line[1 + Math.floor((x * depth) / 8)] ?? 0;
      const index = (byte >> (8 - depth - ((x * depth) % 8))) & (2 ** depth - 1);
      return colours[index] ?? `not in the palette: ${index}`;
    });
  });
  if (lines.length !== stride * height) throw new Error("A picture holds its lines and nothing more.");
  return { width, height, colours, pixels };
}

const read = new Map<string, Picture>();

/** A picture of the website, opened once however many tests look at it. */
function pictureOf(name: string): Picture {
  const picture = read.get(name) ?? opened(readFileSync(path.join(PICTURES, `${name}.png`)));
  read.set(name, picture);
  return picture;
}

/** The colours of the look by name, as the command that makes the pictures holds them. */
function theColours(): Map<string, string> {
  const script = readFileSync(path.join(ROOT, "scripts", "gen-art.mjs"), "utf8");
  return new Map([...script.matchAll(/^ {2}\["([a-z]+)", "(#[0-9a-f]{6})"\],$/gm)].map(([, name, value]) => [name!, value!]));
}

// ---------------------------------------------------------------------------
// The command, tried on drawings of its own in a folder of its own.
// ---------------------------------------------------------------------------

const PALETTE = ["palette", ". transparent", "k #2a2140", "s #e9cf94", "x #123456", "v #e9cf9480"].join("\n");
const DOT = [PALETTE, "", "== dot", ".k.", "ksk", ".k.", ""].join("\n");

const made: string[] = [];

/** A folder laid out as the website is, with these drawings in it. */
function workshop(drawings: Readonly<Record<string, string>>) {
  const root = mkdtempSync(path.join(tmpdir(), "burro-art-"));
  made.push(root);
  mkdirSync(path.join(root, "art"));
  for (const [file, text] of Object.entries(drawings)) writeFileSync(path.join(root, "art", file), text);
  const run = (...given: string[]) =>
    // The command is an ES module, so it is run as the npm script runs it.
    spawnSync(process.execPath, ["scripts/gen-art.mjs", "--root", root, ...given], { cwd: ROOT, encoding: "utf8" });
  return {
    root,
    make: () => run(),
    check: () => run("--check"),
    draw: (file: string, text: string) => writeFileSync(path.join(root, "art", file), text),
    picture: (name: string) => path.join(root, "public", "art", `${name}.png`),
    names: () => readFileSync(path.join(root, "src", "lib", "art", "names.ts"), "utf8"),
  };
}

afterEach(() => {
  for (const root of made.splice(0)) rmSync(root, { recursive: true, force: true });
});

describe("the command that makes the pictures", () => {
  test("test_the_committed_pictures_and_names_are_what_the_drawings_give", () => {
    const run = spawnSync(process.execPath, ["scripts/gen-art.mjs", "--check"], { cwd: ROOT, encoding: "utf8" });

    expect(run.stderr).toBe("");
    expect(run.status).toBe(0);
  });

  test("test_a_drawing_becomes_a_picture_of_its_pixels_and_a_line_of_the_list", () => {
    const shop = workshop({ "one.sprite.txt": DOT });

    expect(shop.make().status).toBe(0);

    const picture = opened(readFileSync(shop.picture("dot")));
    expect([picture.width, picture.height]).toEqual([3, 3]);
    expect(picture.pixels).toEqual([
      [CLEAR, "#2a2140", CLEAR],
      ["#2a2140", "#e9cf94", "#2a2140"],
      [CLEAR, "#2a2140", CLEAR],
    ]);
    expect(shop.names()).toContain('  "dot": { width: 3, height: 3 },');
    expect(shop.names().startsWith("/**\n * Generated from art/*.sprite.txt")).toBe(true);
    expect(shop.check().status).toBe(0);
  });

  test("test_the_same_drawings_give_the_same_bytes_wherever_they_are_made", () => {
    const [one, other] = [workshop({ "one.sprite.txt": DOT }), workshop({ "one.sprite.txt": DOT })];
    one.make();
    other.make();

    expect(readFileSync(one.picture("dot")).equals(readFileSync(other.picture("dot")))).toBe(true);
    // The bytes themselves, so that a machine that packs a picture another way fails here.
    expect(readFileSync(one.picture("dot")).toString("hex")).toBe(DOT_AS_BYTES);
  });

  test("test_a_picture_that_is_not_what_its_drawing_gives_fails_the_check_by_name", () => {
    const shop = workshop({ "one.sprite.txt": DOT });
    shop.make();
    shop.draw("one.sprite.txt", DOT.replace("ksk", "kkk"));

    const run = shop.check();

    expect(run.status).toBe(1);
    expect(run.stderr).toContain("public/art/dot.png is not what the drawings in art/ give.");
    expect(run.stderr).not.toContain("names.ts");
  });

  test("test_a_list_of_names_that_is_out_of_date_fails_the_check", () => {
    const shop = workshop({ "one.sprite.txt": DOT });
    shop.make();
    shop.draw("one.sprite.txt", `${DOT}\n== dash\nkkkk\n`);

    const run = shop.check();

    expect(run.status).toBe(1);
    expect(run.stderr).toContain("src/lib/art/names.ts is not what the drawings in art/ give.");
    expect(run.stderr).toContain("public/art/dash.png is not there.");
  });

  test("test_a_picture_with_no_drawing_fails_by_name_and_is_left_where_it_is", () => {
    const shop = workshop({ "one.sprite.txt": DOT });
    shop.make();
    writeFileSync(shop.picture("stray"), readFileSync(shop.picture("dot")));

    for (const run of [shop.check(), shop.make()]) {
      expect(run.status).toBe(1);
      expect(run.stderr).toContain("public/art/stray.png has no drawing in art/.");
    }
    expect(existsSync(shop.picture("stray"))).toBe(true);
  });

  test("test_a_colour_that_is_not_of_the_look_is_refused_with_the_drawing_that_uses_it", () => {
    for (const [key, said] of [
      ["x", "#123456 ('x')"],
      ["v", "#e9cf9480, which is see-through ('v')"],
    ] as const) {
      const shop = workshop({ "one.sprite.txt": DOT.replace("ksk", `k${key}k`) });

      for (const run of [shop.make(), shop.check()]) {
        expect(run.status).toBe(1);
        expect(run.stderr).toContain(`art/one.sprite.txt: 'dot' uses ${said}.`);
      }
      expect(existsSync(shop.picture("dot"))).toBe(false);
    }
  });

  test("test_a_colour_a_palette_names_and_no_drawing_uses_is_no_fault", () => {
    // A file drawn for a sheet may name colours of its own. What counts is what is drawn with.
    expect(workshop({ "one.sprite.txt": DOT }).make().stderr).toBe("");
  });

  test("test_a_drawing_is_read_as_the_sheets_wrote_it", () => {
    const shop = workshop({
      "one.sprite.txt": [
        "# written by a script of the sheets",
        "palette",
        "# a note among the colours",
        ". none",
        "k #2A2140",
        "c clear",
        "",
        "== two-rows",
        "# a note inside a drawing, which is no row of it",
        "k.c",
        "",
        "ckk",
      ].join("\r\n"),
    });

    expect(shop.make().stderr).toBe("");
    expect(opened(readFileSync(shop.picture("two-rows"))).pixels).toEqual([
      ["#2a2140", CLEAR, CLEAR],
      [CLEAR, "#2a2140", "#2a2140"],
    ]);
  });

  test.each([
    ["a character that is not in the palette", "== dot\n.k.\nkzk\n", "art/one.sprite.txt:9, column 2: 'z' is not in the palette."],
    ["a row of another width", "== dot\n.k.\nkk\n", "art/one.sprite.txt:9: this row of 'dot' is 2 wide and its first is 3."],
    ["a name that is none", "== Dot\n.k.\n", "art/one.sprite.txt:7: 'Dot' is not a name. Use lower case, digits and hyphens."],
    ["a drawing with no rows", "== dot\n", "art/one.sprite.txt: the drawing 'dot' has no rows."],
    ["no drawing at all", "", "art/one.sprite.txt: no drawing found."],
    ["a colour that is none", "g green\n== dot\nk\n", "art/one.sprite.txt:7: 'green' is not a colour."],
    ["a name drawn twice", "== dot\nk\n== dot\nk\n", "art/one.sprite.txt:9: 'dot' is drawn twice. The other is at art/one.sprite.txt:7."],
  ])("test_a_fault_in_a_drawing_is_said_with_where_it_is: %s", (_, drawn, said) => {
    const shop = workshop({ "one.sprite.txt": `${PALETTE}\n${drawn}` });

    const run = shop.make();

    expect(run.status).toBe(1);
    expect(run.stderr).toContain(said);
    expect(existsSync(path.join(shop.root, "public"))).toBe(false);
  });

  test("test_what_a_drawing_says_of_itself_is_in_the_list", () => {
    const shop = workshop({
      "one.sprite.txt": [
        PALETTE,
        "== frame",
        "# @cut 1",
        ...Array<string>(4).fill("kkkk"),
        "== tag",
        "# @cut 1 0 2 1",
        ...Array<string>(4).fill("kkkk"),
        "== strip",
        "# A plain note may stand beside what it says of itself.",
        "# @frames 2",
        "# @face 1 0 2 1",
        "kkkk",
      ].join("\n"),
    });

    expect(shop.make().stderr).toBe("");

    expect(shop.names()).toContain('  "frame": { width: 4, height: 4, cut: [1, 1, 1, 1] },');
    expect(shop.names()).toContain('  "tag": { width: 4, height: 4, cut: [1, 0, 2, 1] },');
    expect(shop.names()).toContain('  "strip": { width: 4, height: 1, frames: 2, face: [1, 0, 2, 1] },');
  });

  test.each([
    ["# @cut 3", "'thing' is 4 by 1, and its cut is more than the whole of it."],
    ["# @cut 1px", "A cut is said in whole numbers."],
    ["# @frames 3", "'thing' is 4 wide, which is not 3 frames of one width."],
    ["# @face 3 0 2 1", "'thing' is 4 by 1, and its face runs off it."],
    ["# @size 4", "'@size' is not something a drawing says."],
  ])("test_what_a_drawing_says_of_itself_is_held_to_the_drawing: %s", (says, said) => {
    const shop = workshop({ "one.sprite.txt": [PALETTE, "== thing", says, "kkkk"].join("\n") });

    const run = shop.make();

    expect(run.status).toBe(1);
    expect(run.stderr).toContain(`art/one.sprite.txt:8: ${said}`);
  });
});

/**
 * The picture of the dot above, byte by byte: a header, a palette of three with the clear
 * colour first, which of them is clear, the lines packed, the end.
 */
const DOT_AS_BYTES = [
  "89504e470d0a1a0a",
  // 3 by 3, two bits to a pixel, with a palette
  "0000000d49484452" + "0000000300000003" + "0203000000" + "2b465d2c",
  "00000009504c5445" + "000000" + "2a2140" + "e9cf94" + "5fd2e6ea",
  "0000000174524e53" + "00" + "40e6d866",
  "0000000e49444154" + "78da" + "631060486110000001920085" + "20504511",
  "0000000049454e44" + "ae426082",
].join("");

// ---------------------------------------------------------------------------
// The pictures of the website.
// ---------------------------------------------------------------------------

const MOST = 96;

/**
 * The seventeen colours of the look, by the names the style sheet gives them. Three more may
 * come to stand beside them, each because a rule of contrast cannot be met without it.
 */
const SEVENTEEN = [
  "ink",
  "page",
  "lea",
  "sand",
  "meadow",
  "verge",
  "hedge",
  "shallows",
  "haven",
  "cobalt",
  "amber",
  "poppy",
  "heath",
  "fur",
  "shade",
  "slate",
  "earth",
] as const;
const THREE_MORE = 3;

/** The colours a drawing is held to by name, as the command that makes the pictures names them. */
const THE_COLOURS = theColours();
const ofTheLook = (name: (typeof SEVENTEEN)[number]) => THE_COLOURS.get(name) ?? `no colour is named ${name}`;

/**
 * Burro is a rabbit, and there are three drawings of him: he sits, he hops in and out of
 * his hole while a search is read, and he waits beside it where nothing may move. He asks
 * nothing, so nothing is drawn of him asking.
 */
const BURRO = ["burro-hops", "burro-sits", "burro-waits"] as const;
/**
 * What he does where he rests, which is where he sits: a strip of frames, made of the
 * drawing of that pose. The test beside the part that draws him holds what is in the
 * strip, frame by frame.
 */
const AT_REST = ["burro-sits-stirs"] as const;
/** How many frames the strip of what he does at rest holds. */
const FRAMES_AT_REST = 15;
/**
 * What flies about him as he hops, where any is drawn: a strip that lies over the strip of
 * his hop, and is named for it. The test beside the part that draws him holds what is in it.
 */
const OVER_HIS_HOP = /^burro-hops-[a-z]+$/;
/**
 * What was drawn of a question and of the button that stood by him, which nothing draws:
 * him up on his hind legs where he asked, what he did as he stood there, and the button
 * that stopped him and let him move, each as it stood and pressed.
 */
const GONE = ["burro-asks", "burro-asks-stirs", "burro-move", "burro-move-down", "burro-stop", "burro-stop-down"] as const;
/** The canvas of every drawing of him, so that he never jumps as one gives way to the next. */
const CANVAS = { width: 24, height: 30 };
/** The row he stands on, and his burrow with him. The row under it is clear. */
const GROUND = 28;

/**
 * What the look was first drawn round, by a wrong guess: a donkey, and all that was his. None
 * of it is drawn, and a drawing that is named for any of it is refused by name. A carrot and a
 * tile are no longer among them: they are Town Map's, and are the pointer of a menu and the
 * ground of a page.
 */
const THE_DONKEYS = [
  /^burro-(idle|walk|ask(-\d+)?|carry|face)(-.*)?$/,
  /^wee-|^carry-/,
  /pannier|wicker|weave|buckle|hinge/,
  /stable|yard|fence|gate|hay|bucket|noticeboard|fingerpost/,
  /lamp|skyline|^sun$|cloud|stars|smoke|dither|^fade-|shadow/,
  /bracket|nail/,
  /^sheet-tab$|^tab-|book|ribbon/,
];

const isDrawn = (name: string): name is ArtName => Object.hasOwn(ART, name);
/** What the service gives, as a drawing is named for it: in lower case, every underscore and every space a hyphen. */
const inAName = (given: string) => given.toLowerCase().replaceAll(/[_ ]/g, "-");

/** What is read of a release: its vibes, the families they are put in, and its measures. */
type Release = Pick<MetaData, "tags" | "families" | "features">;

/** Every recorded answer of the route that says what a release holds. */
function releases(folder = recordedFolder()): Release[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return releases(file);
    if (!/^meta(-[a-z-]+)?\.json$/.test(entry.name)) return [];
    const recorded = JSON.parse(readFileSync(file, "utf8")) as { body: { data?: Release } };
    return recorded.body.data === undefined ? [] : [recorded.body.data];
  });
}

/**
 * What was drawn for an earlier account of the look, in browns, which was turned down: jars
 * and brass weights, a seal of wax, frames of wood and of paper, a strap, a wooden rule. Town
 * Map drew each of those things its own way, and its way is taken. A drawing that is named
 * for any of them is refused by name. The one frame there is, is the box.
 */
const OF_THE_EARLIER_ACCOUNT = [
  /^jar-/,
  /^weight-|^pan$|^balance/,
  /^seal$|^note-pin|^pin-no/,
  /^frame-(?!box(-on)?$)/,
  /strap|^label-|^mark-/,
  /^rule$|^peg|^staple$|^sure-/,
  /^burro-(digs|hole|home)$/,
];

describe("the pictures of the website", () => {
  const drawings = everyDrawing();
  const names = Object.keys(ART) as ArtName[];

  test("test_every_name_of_the_list_has_its_picture_and_every_picture_its_name", () => {
    expect(readdirSync(PICTURES).filter((file) => !file.startsWith(".")).sort()).toEqual(
      names.map((name) => `${name}.png`).sort(),
    );
    expect(drawings.map(({ name }) => name).sort()).toEqual([...names].sort());
  });

  test("test_every_picture_is_of_the_size_the_list_gives_it", () => {
    const sizes = names.map((name) => {
      const { width, height } = pictureOf(name);
      return [name, width, height];
    });

    expect(sizes).toEqual(names.map((name) => [name, ART[name].width, ART[name].height]));
  });

  test("test_every_picture_holds_the_pixels_of_its_drawing", () => {
    const differ = drawings.filter(({ name, pixels }) => JSON.stringify(pictureOf(name).pixels) !== JSON.stringify(pixels));

    expect(differ.map(({ name }) => name)).toEqual([]);
  });

  test("test_the_command_draws_with_the_seventeen_colours_of_the_look_and_three_more_at_the_most", () => {
    const held = [...THE_COLOURS.keys()];

    expect(held.slice(0, SEVENTEEN.length)).toEqual([...SEVENTEEN]);
    expect(held.length).toBeLessThanOrEqual(SEVENTEEN.length + THREE_MORE);
    // No colour is held twice, under two names.
    expect(new Set(THE_COLOURS.values()).size).toBe(held.length);
  });

  test("test_every_picture_is_made_of_the_colours_of_the_look_and_of_no_other", () => {
    const ofTheLook = new Set(THE_COLOURS.values());

    const strange = names.flatMap((name) =>
      pictureOf(name)
        .colours.filter((colour) => colour !== CLEAR && !ofTheLook.has(colour))
        .map((colour) => `${name}: ${colour}`),
    );

    expect(strange).toEqual([]);
  });

  test("test_a_colour_of_a_drawing_is_the_colour_the_style_sheet_gives_that_name", () => {
    // A drawing and a page cannot come to differ: every colour the command draws with is
    // named in the style sheet, by the same name, with the same value. A colour is added to
    // both, in one change.
    const css = readFileSync(path.join(ROOT, "src", "styles", "tokens.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    const named = new Map(
      [...css.matchAll(/(?<![\w-])--([a-z]+):\s*(#[0-9a-f]{6})\s*;/gi)].map(([, name, value]) => [name!, value!.toLowerCase()]),
    );
    const drawnWith = [...THE_COLOURS];

    // The style sheet holds the look once it names its ink. Until it does it is the sheet of
    // the earlier account, which named its ink tar, and no colour of it is drawn with.
    if (!named.has("ink")) {
      expect(named.has("tar")).toBe(true);
      return;
    }
    expect(drawnWith.map(([name]) => [name, named.get(name) ?? "the style sheet does not name it"])).toEqual(drawnWith);
  });

  test("test_no_drawing_but_the_ground_is_wider_or_taller_than_96_art_pixels", () => {
    // A drawing is small, and stands beside the words it is for. The ground is set apart, by
    // name: it is the one picture that lies behind everything, and it is large so that its
    // repeat does not show. A strip is drawings of one width side by side: each of them is
    // held to the size, not the strip.
    const sizeOf = (name: ArtName) => {
      const drawing: Drawn = ART[name];
      return { wide: drawing.width / (drawing.frames ?? 1), high: drawing.height };
    };

    expect(names.filter((name) => sizeOf(name).wide > MOST || sizeOf(name).high > MOST)).toEqual(["ground"]);
  });
});

// ---------------------------------------------------------------------------
// The box, the button and the marks, which are Town Map's.
// ---------------------------------------------------------------------------

/** A part of a picture: from a column and a row, so many wide and so many high. */
function partOf(picture: Picture, left: number, top: number, wide: number, high: number): Pixel[][] {
  return picture.pixels.slice(top, top + high).map((row) => row.slice(left, left + wide));
}

/** Every place of a picture, with the colour that is there. */
function placesOf(picture: Picture): { x: number; y: number; colour: Pixel }[] {
  return picture.pixels.flatMap((row, y) => row.map((colour, x) => ({ x, y, colour })));
}

/**
 * A button as it is drawn when its face has stepped one art pixel down and one to the right,
 * into its shadow: worked out here from the button up, by other code than drew it.
 */
function steppedIn(up: Picture): Pixel[][] {
  const { width, height, pixels } = up;
  const middle = Math.floor(width / 2);
  const pressed = Array.from({ length: height }, () => Array<Pixel>(width).fill(CLEAR));
  // The row of its shadow is given up to it, and one column of its middle, where a button is
  // one colour from edge to edge: so the canvas holds it, and its first row and column are clear.
  for (let y = 0; y < height - 1; y += 1) {
    pixels[y]!.filter((_, x) => x !== middle).forEach((colour, x) => {
      pressed[y + 1]![x + 1] = colour;
    });
  }
  // With no shadow under it, the foot of its outline is notched as its head is.
  pressed[height - 1]![1] = CLEAR;
  pressed[height - 1]![width - 1] = CLEAR;
  return pressed;
}

/** What a frame says of where it is cut in nine: so much from its top, its right, its foot and its left. */
function cutOf(name: ArtName): readonly [top: number, right: number, foot: number, left: number] {
  const drawing: Drawn = ART[name];
  if (drawing.cut === undefined) throw new Error(`${name} says no cut.`);
  return drawing.cut;
}

/**
 * The parts of a frame that a style sheet stretches: its four edges, each along its length,
 * and its middle, both ways. A part that is stretched is one colour the way it is stretched,
 * or a pixel of it is drawn as a smear.
 */
function stretched(name: ArtName): { part: string; lines: Pixel[][] }[] {
  const picture = pictureOf(name);
  const [top, right, foot, left] = cutOf(name);
  const [wide, high] = [picture.width - left - right, picture.height - top - foot];
  const columns = (part: Pixel[][]) => part[0]!.map((_, x) => part.map((row) => row[x]!));
  return [
    { part: "the edge at its head", lines: partOf(picture, left, 0, wide, top) },
    { part: "the edge at its foot", lines: partOf(picture, left, picture.height - foot, wide, foot) },
    { part: "its left edge", lines: columns(partOf(picture, 0, top, left, high)) },
    { part: "its right edge", lines: columns(partOf(picture, picture.width - right, top, right, high)) },
    { part: "its middle", lines: [partOf(picture, left, top, wide, high).flat()] },
  ];
}

/** The buttons that are cut in nine, and the colour of the face of each, where its words stand. */
const BUTTONS = {
  "ui-button": "page",
  "ui-button-go": "cobalt",
  "ui-button-on": "amber",
  "ui-button-stop": "page",
} as const;

describe("the box, the button and the marks", () => {
  const names = Object.keys(ART) as ArtName[];
  const buttons = Object.keys(BUTTONS) as (keyof typeof BUTTONS)[];

  test("test_the_box_is_cut_where_its_rules_and_its_shadow_are", () => {
    for (const name of ["ui-box", "ui-box-on", "frame-box", "frame-box-on"] as const) {
      expect([name, ART[name]]).toEqual([name, { width: 18, height: 18, cut: [4, 6, 6, 4] }]);
    }
    const box = pictureOf("ui-box");
    // Its shadow is hard, and falls down and to the right and nowhere else: the light is from the top left.
    const shadow = placesOf(box).filter(({ colour }) => colour === ofTheLook("shade"));
    expect(shadow.length).toBeGreaterThan(0);
    // Under the box itself, which is 16 square, it is seen only through the notch of the corner it falls from.
    expect(shadow.filter(({ x, y }) => x < 16 && y < 16).map(({ x, y }) => [x, y])).toEqual([[15, 15]]);
    // What a box holds stands on page, and on nothing else.
    expect(new Set(partOf(box, 4, 4, 8, 8).flat())).toEqual(new Set([ofTheLook("page")]));
    // Each corner of its outline is notched by one art pixel.
    expect([box.pixels[0]![0], box.pixels[0]![15], box.pixels[15]![0]]).toEqual([CLEAR, CLEAR, CLEAR]);
  });

  test("test_the_box_the_style_sheet_names_is_town_maps_box_point_for_point", () => {
    // The style sheet names the box /art/frame-box.png, and Town Map drew it as ui-box. Both
    // names have the one drawing behind them, so that neither is a picture that is not there.
    expect(pictureOf("frame-box").pixels).toEqual(pictureOf("ui-box").pixels);
    expect(pictureOf("frame-box-on").pixels).toEqual(pictureOf("ui-box-on").pixels);
  });

  test("test_the_box_in_hand_is_the_box_with_amber_between_its_rules", () => {
    const [box, inHand] = [pictureOf("ui-box"), pictureOf("ui-box-on")];
    const changed = placesOf(box).filter(({ x, y, colour }) => inHand.pixels[y]![x] !== colour);

    expect(changed.length).toBeGreaterThan(0);
    expect(new Set(changed.map(({ colour }) => colour))).toEqual(new Set([ofTheLook("page")]));
    expect(new Set(changed.map(({ x, y }) => inHand.pixels[y]![x]))).toEqual(new Set([ofTheLook("amber")]));
    // Nothing a box holds is on amber: its inside is page still.
    expect(new Set(partOf(inHand, 4, 4, 8, 8).flat())).toEqual(new Set([ofTheLook("page")]));
  });

  test("test_a_button_is_of_one_size_and_one_cut_whatever_it_is_for_and_pressed_or_not", () => {
    // One takes the place of another, and nothing about the button moves.
    const drawn = names.filter((name) => name.startsWith("ui-button"));

    expect(drawn).toEqual(buttons.flatMap((name) => [name, `${name}-down`]).sort());
    expect(new Set(drawn.map((name) => JSON.stringify(ART[name])))).toEqual(
      new Set([JSON.stringify({ width: 12, height: 10, cut: [3, 3, 4, 3] })]),
    );
  });

  test("test_the_face_of_a_button_is_one_colour_where_its_words_stand", () => {
    // Cobalt for the one that matters most in sight, amber for what is on, page for the rest.
    // Words are set on a colour that was chosen for them, and on no light edge and no shade.
    for (const name of buttons) {
      const face = ofTheLook(BUTTONS[name]);

      // The middle of the picture is what lies under its words, pressed or not.
      expect([name, new Set(partOf(pictureOf(name), 3, 3, 6, 3).flat())]).toEqual([name, new Set([face])]);
      expect([name, new Set(partOf(pictureOf(`${name}-down`), 3, 3, 6, 3).flat())]).toEqual([name, new Set([face])]);
    }
    // The button that stops has an edge of poppy, and no other button has any poppy but the amber one, in its shade.
    expect(buttons.filter((name) => pictureOf(name).colours.includes(ofTheLook("poppy")))).toEqual(["ui-button-on", "ui-button-stop"]);
  });

  test("test_a_button_pressed_is_the_button_up_with_its_face_stepped_into_its_shadow", () => {
    // The face steps one art pixel down and one to the right. The button, which takes the
    // press, does not move and is of one size: so the canvas is the one of the button up.
    for (const name of buttons) {
      const [up, down] = [pictureOf(name), pictureOf(`${name}-down`)];
      // A button up may have a glint, a pixel of page one in from the corner of its face. Pressed
      // it has none: the pixel would stand in the middle of the picture, which is stretched.
      const stepped = steppedIn(up);
      stepped[3]![3] = ofTheLook(BUTTONS[name]);

      expect([name, down.pixels]).toEqual([name, stepped]);
      // Up, it throws a shadow of ink under it. Pressed, it has stepped into it, and throws none.
      expect(up.pixels.at(-1)!.filter((colour) => colour !== CLEAR)).toEqual(Array(up.width - 2).fill(ofTheLook("ink")));
      expect(down.pixels[0]!.every((colour) => colour === CLEAR)).toBe(true);
      expect(down.pixels.every((row) => row[0] === CLEAR)).toBe(true);
    }
  });

  test("test_what_is_stretched_of_a_frame_is_one_colour_the_way_it_is_stretched", () => {
    // A box and a button are cut in nine. Their corners are drawn as they are, and their edges
    // and their middle are stretched to the size of what they hold.
    const frames = names.filter((name) => (ART[name] as Drawn).cut !== undefined);
    const smeared = frames.flatMap((name) =>
      stretched(name)
        .filter(({ lines }) => lines.some((line) => new Set(line).size > 1))
        .map(({ part }) => `${name}: ${part}`),
    );

    expect(frames.length).toBeGreaterThan(0);
    expect(smeared).toEqual([]);
  });

  test("test_the_marks_are_town_maps_and_each_is_of_its_size", () => {
    const sizes = (["ui-carrot", "ui-key", "ui-peg", "ui-cross", "ui-arrow", "ui-weight"] as const).map((name) => [
      name,
      ART[name].width,
      ART[name].height,
    ]);

    expect(sizes).toEqual([
      ["ui-carrot", 16, 9],
      ["ui-key", 16, 7],
      ["ui-peg", 7, 10],
      ["ui-cross", 7, 7],
      ["ui-arrow", 10, 8],
      ["ui-weight", 12, 10],
    ]);
    // The carrot and the key are amber, the peg is poppy and the weight is slate: a mark is told by its colour too.
    expect(pictureOf("ui-carrot").colours).toContain(ofTheLook("amber"));
    expect(pictureOf("ui-key").colours).toContain(ofTheLook("amber"));
    expect(pictureOf("ui-peg").colours).toContain(ofTheLook("poppy"));
    expect(pictureOf("ui-weight").colours).toContain(ofTheLook("slate"));
  });

  test("test_a_trade_off_is_drawn_two_ways_of_one_size_and_neither_is_poppy", () => {
    // A person who walked the website did not know what a red arrow was for. What stands for
    // a trade-off says that one thing was given for another, and is never red: red says
    // danger, and a trade-off is what was given for what was got. It is drawn two ways, so
    // that a result may show either, and one takes the place of the other.
    const ways = ["ui-tradeoff", "ui-tradeoff-b"] as const;

    expect(names.filter((name) => name.startsWith("ui-tradeoff"))).toEqual([...ways]);
    for (const name of ways) {
      expect([name, ART[name]]).toEqual([name, { width: 16, height: 16 }]);
      expect([name, pictureOf(name).colours.includes(ofTheLook("poppy"))]).toEqual([name, false]);
      expect([name, pictureOf(name).colours.includes(ofTheLook("ink"))]).toEqual([name, true]);
    }
    expect(JSON.stringify(pictureOf("ui-tradeoff").pixels)).not.toBe(JSON.stringify(pictureOf("ui-tradeoff-b").pixels));
    // The first is a pair of scales, which is the same from its left and from its right but
    // for where its shade falls: neither pan hangs lower, so neither side is the worse.
    const scales = pictureOf("ui-tradeoff").pixels.map((row) => row.map((colour) => (colour === ofTheLook("shade") ? ofTheLook("sand") : colour)));
    expect(scales.map((row) => [...row].reverse())).toEqual(scales);
  });

  test("test_the_mark_of_what_is_not_whole_is_one_step_of_a_band_chequered_in_squares_of_two", () => {
    // It is the step a peg stands on where a band rests on part of what it needs, made a
    // mark that stands alone: as wide and as high as a step, with its edge of ink, and
    // chequered as the step is, in ink and in page and in nothing else.
    const mark = pictureOf("ui-approx");
    const [ink, page] = [ofTheLook("ink"), ofTheLook("page")];

    expect(ART["ui-approx"]).toEqual({ width: 9, height: 6 });
    expect([...mark.colours].sort()).toEqual([ink, page].sort());
    const edge = [...mark.pixels[0]!, ...mark.pixels.at(-1)!, ...mark.pixels.map((row) => row[0]!), ...mark.pixels.map((row) => row.at(-1)!)];
    expect(new Set(edge)).toEqual(new Set([ink]));
    // Within its edge a square is two art pixels each way, and each lies against squares of
    // the other colour: the one at the right is cut by the edge, as it is on a step.
    const within = partOf(mark, 1, 1, mark.width - 2, mark.height - 2);
    const square = (x: number, y: number) => ((Math.floor(x / 2) + Math.floor(y / 2)) % 2 === 0 ? page : ink);
    expect(within).toEqual(within.map((row, y) => row.map((_, x) => square(x, y))));
    // It is told from a step of a gauge, which fills in amber, and from the peg of a band.
    expect(mark.colours).not.toContain(ofTheLook("amber"));
    expect(mark.colours).not.toContain(ofTheLook("poppy"));
  });

  test("test_nothing_but_burro_and_his_burrow_holds_earth_or_fur", () => {
    // Brown is the rabbit's and his burrow's. Town Map held its brown in wood, in leather and as
    // the shade of amber: where a drawing of its is taken, that has another colour.
    const brown = [ofTheLook("earth"), ofTheLook("fur")];
    const holds = names.filter((name) => pictureOf(name).colours.some((colour) => brown.includes(colour)));

    expect(holds.filter((name) => !name.startsWith("burro-"))).toEqual([]);
    // The rule is not held by there being no brown at all: he is drawn in it.
    expect(holds.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// Where a number is set on a drawing in type.
// ---------------------------------------------------------------------------

describe("the pennant of a rank and the pin of the map", () => {
  const names = Object.keys(ART) as ArtName[];

  test("test_the_pennant_and_the_pin_each_hold_the_number_ten_on_bare_page", () => {
    // No figure is drawn in a picture: the rank is set in type, in ink, on the face the list
    // gives. The widest rank is 10. In the pixel face at 20 px it is 14 px wide and 11 high,
    // which on a phone, where an art pixel is 2 px, is 7 art pixels by 6.
    for (const name of ["ui-flag", "pin"] as const) {
      const [left, top, wide, high] = ART[name].face;

      expect([name, new Set(partOf(pictureOf(name), left, top, wide, high).flat())]).toEqual([name, new Set([ofTheLook("page")])]);
      expect([name, wide >= 9, high >= 7]).toEqual([name, true, true]);
    }
  });

  test("test_the_pennant_is_one_flag_on_its_pole_whatever_the_rank", () => {
    // The pennant of the first is the pennant of the tenth: nobody wins. There is one drawing
    // of it, with no gold in it and no other colour than page, ink and the shade of its shadow.
    expect(names.filter((name) => name.includes("flag") || name.includes("pennant"))).toEqual(["ui-flag"]);
    expect(pictureOf("ui-flag").colours.filter((colour) => colour !== CLEAR).sort()).toEqual(
      [ofTheLook("ink"), ofTheLook("page"), ofTheLook("shade")].sort(),
    );
    // Its pole is its first two columns, from its head to its foot.
    expect(new Set(pictureOf("ui-flag").pixels.flatMap((row) => row.slice(0, 2)))).toEqual(new Set([ofTheLook("ink")]));
  });

  test("test_the_point_of_the_pin_is_the_middle_of_its_last_row", () => {
    // A pin is set on the map by its point: where the place is. With the point in the middle
    // of the foot of the picture, a pin that is anchored there stands on its place.
    expect(names.filter((name) => name.startsWith("pin"))).toEqual(["pin"]);
    const { width, pixels } = pictureOf("pin");
    const foot = pixels.at(-1)!.map((colour, x) => (colour === CLEAR ? [] : [x])).flat();

    expect(width % 2).toBe(1);
    expect(foot).toEqual([(width - 1) / 2]);
    // It is a mirror of itself about that column, but for where its shade falls.
    const shade = ofTheLook("sand");
    const lit = pixels.map((row) => row.map((colour) => (colour === shade ? ofTheLook("page") : colour)));
    expect(lit.map((row) => [...row].reverse())).toEqual(lit);
  });
});

// ---------------------------------------------------------------------------
// How much a thing counts: a gauge of steps, and the two buttons that move it.
// ---------------------------------------------------------------------------

describe("a step of a gauge, and the buttons of a step", () => {
  /** The sign of a button of a step: the ink that stands on its face, inside its outline. */
  const signOf = (picture: Picture, from: number) =>
    placesOf(picture)
      .filter(({ x, y, colour }) => colour === ofTheLook("ink") && x > from && x < 20 && y > from && y < from + 18)
      .map(({ x, y }) => [x, y]);
  /** The same picture, its sign taken off its face. */
  const bare = (picture: Picture, from: number): Picture => {
    const sign = new Set(signOf(picture, from).map(([x, y]) => `${x},${y}`));
    return {
      ...picture,
      pixels: picture.pixels.map((row, y) => row.map((colour, x) => (sign.has(`${x},${y}`) ? ofTheLook("page") : colour))),
    };
  };

  test("test_a_step_of_a_gauge_is_never_to_be_taken_for_a_cell_of_the_band_of_five", () => {
    // Where an area sits is a band: five cells, wider than they are tall, none of which fills,
    // and a peg of poppy over one. How much a thing counts is a gauge: its steps are taller
    // than they are wide, there are ten or twenty, they fill from the left, and what fills them is amber.
    const [empty, full] = [pictureOf("gauge-cell"), pictureOf("gauge-cell-full")];

    expect(ART["gauge-cell-full"]).toEqual(ART["gauge-cell"]);
    expect(empty.height).toBeGreaterThanOrEqual(2 * empty.width);
    expect(full.colours).toContain(ofTheLook("amber"));
    expect(empty.colours).not.toContain(ofTheLook("amber"));
    // And the peg of a band holds no amber, as a step of a gauge holds no peg.
    expect(pictureOf("ui-peg").colours).not.toContain(ofTheLook("amber"));
  });

  test("test_a_step_keeps_its_outline_as_it_fills_and_twenty_stand_on_a_phone", () => {
    // Nothing moves as a gauge fills: a step filled is drawn where the step empty was.
    const outline = (picture: Picture) => picture.pixels.map((row) => row.map((colour) => (colour === CLEAR || colour === ofTheLook("ink") ? colour : "inside")));

    expect(outline(pictureOf("gauge-cell-full"))).toEqual(outline(pictureOf("gauge-cell")));
    // The steps of a gauge share their outlines: each lies one art pixel over the one before
    // it. So its first and its last column are its outline, from its notch to its notch.
    const { width, pixels } = pictureOf("gauge-cell");
    for (const column of [0, width - 1]) {
      expect(pixels.map((row) => row[column])).toEqual([CLEAR, ...Array<string>(pixels.length - 2).fill(ofTheLook("ink")), CLEAR]);
    }
    // A weight moves by a twentieth. Twenty steps laid so are 101 art pixels, 202 px on a
    // phone: with the two buttons of a step, 44 px each, that is under the 310 px a box has
    // inside it on a phone 390 px wide.
    expect(2 * (20 * (width - 1) + 1) + 2 * 44).toBeLessThanOrEqual(310);
  });

  test("test_a_button_of_a_step_is_22_art_pixels_square_and_is_drawn_as_a_button", () => {
    // 22 art pixels are 44 px on a phone, which is the least a main control may be. It is
    // shown whole, so it says no cut.
    const steps = ["btn-less", "btn-less-down", "btn-more", "btn-more-down"] as const;

    expect((Object.keys(ART) as ArtName[]).filter((name) => name.startsWith("btn-"))).toEqual([...steps]);
    for (const name of steps) expect([name, ART[name]]).toEqual([name, { width: 22, height: 22 }]);
    // It is Town Map's button: page, its shade in sand, its outline and its shadow in ink.
    for (const name of steps) {
      expect([name, pictureOf(name).colours.filter((colour) => colour !== CLEAR).sort()]).toEqual([
        name,
        [ofTheLook("ink"), ofTheLook("page"), ofTheLook("sand")].sort(),
      ]);
    }
  });

  test("test_a_button_of_a_step_pressed_is_the_button_up_its_face_and_its_sign_stepped_into_its_shadow", () => {
    for (const step of ["btn-less", "btn-more"] as const) {
      const [up, down] = [pictureOf(step), pictureOf(`${step}-down`)];
      const sign = signOf(up, 1);

      expect(sign.length).toBeGreaterThan(0);
      // The sign steps with the face it stands on: one art pixel down and one to the right.
      expect(signOf(down, 2)).toEqual(sign.map(([x, y]) => [x! + 1, y! + 1]));
      expect(bare(down, 2).pixels).toEqual(steppedIn(bare(up, 1)));
    }
    expect(signOf(pictureOf("btn-less"), 1)).not.toEqual(signOf(pictureOf("btn-more"), 1));
  });
});

// ---------------------------------------------------------------------------
// The two ends of a scale.
// ---------------------------------------------------------------------------

describe("the picture at each end of a scale", () => {
  const names = Object.keys(ART) as ArtName[];
  /** What stands for the two ends of what runs one way, and for an end with no picture of its own. */
  const OF_NO_SCALE = ["key-blank", "key-least", "key-most"];
  const ends = [
    ...new Set(
      releases().flatMap(({ tags }) =>
        tags.filter(({ shape }) => shape === "scale").flatMap(({ low_end, high_end }) => [low_end ?? "", high_end ?? ""]),
      ),
    ),
  ];

  test("test_every_end_of_every_scale_of_every_recorded_release_has_its_picture", () => {
    // A picture is named for its end, in the words the service gives the end. A later release
    // may bring a scale with no picture, and the blank stands for its ends: every scale there
    // is today was drawn, and this says which picture to draw when one is not.
    expect(ends.length).toBeGreaterThan(0);
    expect(ends.filter((end) => !isDrawn(`key-${inAName(end)}`))).toEqual([]);
  });

  test("test_every_picture_of_an_end_has_its_scale_but_the_three_that_stand_for_none", () => {
    const ofAScale = new Set(ends.map((end) => `key-${inAName(end)}`));

    expect(names.filter((name) => name.startsWith("key-") && !ofAScale.has(name))).toEqual(OF_NO_SCALE);
  });

  test("test_every_picture_of_an_end_is_of_one_size_so_that_one_may_stand_for_another", () => {
    const sizes = new Set(names.filter((name) => name.startsWith("key-")).map((name) => `${ART[name].width} by ${ART[name].height}`));

    expect(sizes).toEqual(new Set(["32 by 22"]));
  });

  test("test_an_end_that_is_drawn_by_its_name_is_one_picture_too_the_one_of_that_end_of_its_vibe", () => {
    // An end was two pictures side by side: two houses, two blocks. A part that draws an
    // end by its name draws the one picture that the end of its vibe has, set in the middle
    // of the canvas it had and on its last row: so no end is drawn two ways, and none is two.
    const scales = releases().flatMap(({ tags }) => tags.filter(({ shape }) => shape === "scale"));
    const within = (name: string) => {
      const { pixels, width, height } = pictureOf(name);
      const [left, top] = [(width - 16) / 2, height - 16];
      const around = placesOf(pictureOf(name)).filter(({ x, y }) => x < left || x >= left + 16 || y < top);
      return { middle: pixels.slice(top).map((row) => row.slice(left, left + 16)), clear: around.every(({ colour }) => colour === CLEAR) };
    };

    expect(scales.length).toBeGreaterThan(0);
    for (const { tag_id, low_end, high_end } of scales) {
      for (const [end, name] of [
        ["low", low_end],
        ["high", high_end],
      ] as const) {
        const byName = within(`key-${inAName(name ?? "")}`);

        expect([tag_id, end, byName.clear]).toEqual([tag_id, end, true]);
        expect([tag_id, end, byName.middle]).toEqual([tag_id, end, pictureOf(`end-${inAName(tag_id)}-${end}`).pixels]);
      }
    }
    // What runs one way and is drawn by no vibe of its own has one picture at each end as well.
    for (const name of ["key-least", "key-most"]) expect([name, within(name).clear]).toEqual([name, true]);
  });

  test("test_the_two_ends_of_a_scale_are_two_pictures", () => {
    // Neither end is the good end, and neither is the other.
    const scales = releases().flatMap(({ tags }) => tags.filter(({ shape }) => shape === "scale"));
    const same = scales.filter(
      ({ low_end, high_end }) =>
        JSON.stringify(pictureOf(`key-${inAName(low_end ?? "")}`).pixels) === JSON.stringify(pictureOf(`key-${inAName(high_end ?? "")}`).pixels),
    );

    expect(same.map(({ tag_id }) => tag_id)).toEqual([]);
    expect(JSON.stringify(pictureOf("key-least").pixels)).not.toBe(JSON.stringify(pictureOf("key-most").pixels));
  });
});

// ---------------------------------------------------------------------------
// The two ends of a gauge, of every vibe.
// ---------------------------------------------------------------------------

/** What stands at an end that has no picture of its own. */
const NO_PICTURE = "end-blank";
const endOf = (vibe: string, end: "low" | "high") => `end-${inAName(vibe)}-${end}`;
/** What follows the name of the picture of an end in the name of the same end, drawn a second way. */
const A_SECOND_WAY = "-b";
/** The family whose vibes count who lived somewhere, which nothing pictures. */
const WHO_LIVES_THERE = "who_lives_there";
/** The dimension of the measures of recorded crime, as the service names it. */
const RECORDED_CRIME = "crime";

describe("the picture at each end of a gauge", () => {
  const names = Object.keys(ART) as ArtName[];
  const drawn = names.filter((name) => name.startsWith("end-"));
  const vibes = releases().flatMap(({ tags }) => tags);
  /** The ids of the measures of recorded crime, which the service tells by their dimension. */
  const ofCrime = new Set(
    releases().flatMap(({ features }) => features.filter(({ dimension }) => dimension === RECORDED_CRIME).map(({ feature_id }) => feature_id)),
  );

  test("test_every_vibe_of_every_recorded_release_has_a_picture_at_each_of_its_ends_today", () => {
    // Whether a vibe runs between two ends that have names or one way, from least to most.
    // A later release may bring a vibe that has none, and the blank one stands at its ends:
    // every vibe there is today was drawn, and this says which pictures to draw when one is not.
    expect(vibes.length).toBeGreaterThan(0);
    expect(vibes.some(({ shape }) => shape === "scale")).toBe(true);
    expect(vibes.some(({ shape }) => shape === "one_way")).toBe(true);

    const undrawn = vibes.flatMap(({ tag_id }) => [endOf(tag_id, "low"), endOf(tag_id, "high")]).filter((name) => !isDrawn(name));

    expect([...new Set(undrawn)]).toEqual([]);
    expect(isDrawn(NO_PICTURE)).toBe(true);
  });

  test("test_every_picture_of_an_end_is_an_end_of_a_vibe_or_the_blank_one", () => {
    const ofVibes = new Set(vibes.flatMap(({ tag_id }) => [endOf(tag_id, "low"), endOf(tag_id, "high")]));

    expect(drawn.filter((name) => !ofVibes.has(name) && !name.endsWith(A_SECOND_WAY))).toEqual([NO_PICTURE]);
    // No vibe is named so that an end of it would be taken for the blank one.
    expect([...ofVibes].filter((name) => name === NO_PICTURE)).toEqual([]);
  });

  test("test_an_end_that_is_drawn_a_second_way_has_its_first_and_the_two_ways_are_two_pictures", () => {
    // Where it was not plain which picture says an end best, the end was drawn two ways, for
    // the founder to choose between: one line of the kit chooses. A second way stands for a
    // first, and is held to all that a first is held to.
    const seconds = drawn.filter((name) => name.endsWith(A_SECOND_WAY));
    const firstOf = (name: string) => name.slice(0, -A_SECOND_WAY.length);

    expect(seconds.length).toBeGreaterThan(0);
    expect(seconds.filter((name) => !isDrawn(firstOf(name)) || firstOf(name) === NO_PICTURE)).toEqual([]);
    expect(seconds.filter((name) => JSON.stringify(pictureOf(name).pixels) === JSON.stringify(pictureOf(firstOf(name)).pixels))).toEqual([]);
    // The two ends of a vibe are two pictures the second way as well, and neither is the blank one.
    const blank = JSON.stringify(pictureOf(NO_PICTURE).pixels);
    const second = (name: string) => JSON.stringify(pictureOf(isDrawn(`${name}${A_SECOND_WAY}`) ? `${name}${A_SECOND_WAY}` : name).pixels);
    const faults = [...new Set(vibes.map(({ tag_id }) => tag_id))].filter((vibe) => {
      const [low, high] = [second(endOf(vibe, "low")), second(endOf(vibe, "high"))];
      return low === high || low === blank || high === blank;
    });
    expect(faults).toEqual([]);
  });

  test("test_an_end_is_one_picture_of_the_size_of_a_thing_so_that_one_may_stand_for_another", () => {
    // An end was two pictures side by side, 32 art pixels by 22: two houses, two blocks. A
    // person who walked the website asked for one at each end, which leaves a gauge its room.
    expect(drawn.length).toBeGreaterThan(2);
    expect(new Set(drawn.map((name) => `${ART[name].width} by ${ART[name].height}`))).toEqual(new Set(["16 by 16"]));
  });

  test("test_every_picture_of_an_end_stands_on_its_last_row_and_is_held_by_its_canvas", () => {
    // The two ends and what runs between them stand on one line. A picture that ended a
    // row higher than the next would stand higher than it, beside the same gauge.
    const floating = drawn.filter((name) => pictureOf(name).pixels.at(-1)!.every((colour) => colour === CLEAR));

    expect(floating).toEqual([]);
    // And something of each is drawn: no end is a clear canvas.
    expect(drawn.filter((name) => pictureOf(name).colours.every((colour) => colour === CLEAR))).toEqual([]);
  });

  test("test_the_ends_of_a_vibe_that_counts_who_lived_somewhere_are_its_page_with_little_written_on_it_and_with_much", () => {
    // Nothing pictures a person, or a kind of person. At its high end such a vibe has the
    // page of the register that is its thing, set one row lower so that it stands on the
    // line. At its low end it has the same page with fewer of its lines written.
    const counted = [...new Set(vibes.filter(({ family }) => family === WHO_LIVES_THERE).map(({ tag_id }) => tag_id))];
    const [shade, page] = [ofTheLook("shade"), ofTheLook("page")];
    const lower = (picture: Picture) => [picture.pixels[0]!.map(() => CLEAR), ...picture.pixels.slice(0, -1)];

    expect(counted.length).toBeGreaterThan(0);
    for (const vibe of counted) {
      const thing = pictureOf(thingOf(vibe));
      const [low, high] = [pictureOf(endOf(vibe, "low")), pictureOf(endOf(vibe, "high"))];

      expect(thing.pixels.at(-1)!.every((colour) => colour === CLEAR)).toBe(true);
      expect([vibe, high.pixels]).toEqual([vibe, lower(thing)]);
      const differ = placesOf(low).filter(({ x, y, colour }) => high.pixels[y]![x] !== colour);
      expect([vibe, differ.length > 0, differ.filter(({ x, y, colour }) => colour !== page || high.pixels[y]![x] !== shade)]).toEqual([vibe, true, []]);
      // Something is written on it still: a page with nothing on it says that nobody lived there.
      expect([vibe, placesOf(low).filter(({ colour, y }) => colour === shade && y > 4).length > 0]).toEqual([vibe, true]);
    }
  });

  test("test_the_two_ends_of_a_vibe_are_two_pictures_and_neither_is_the_blank_one", () => {
    // The two are opposites: what is drawn at one end is never what is drawn at the other.
    const blank = JSON.stringify(pictureOf(NO_PICTURE).pixels);
    const faults = [...new Set(vibes.map(({ tag_id }) => tag_id))].flatMap((vibe) => {
      const [low, high] = [endOf(vibe, "low"), endOf(vibe, "high")].map((name) => JSON.stringify(pictureOf(name).pixels));
      return low === high || low === blank || high === blank ? [vibe] : [];
    });

    expect(faults).toEqual([]);
  });

  test("test_nothing_is_poppy_at_the_end_where_more_crime_was_recorded", () => {
    // Recorded crime is drawn as what it is, a count that was written down, and never as a
    // warning: nothing is red to say danger. Which vibe counts it, and towards which of its
    // ends, is the service's to say, of every part of every recipe.
    const ends = [
      ...new Set(
        vibes.flatMap(({ tag_id, terms }) =>
          terms.filter(({ feature_id }) => ofCrime.has(feature_id)).map(({ reading }) => endOf(tag_id, reading === "high" ? "high" : "low")),
        ),
      ),
    ];
    // Whichever way the end is drawn.
    const everyWay = ends.flatMap((name) => [name, `${name}${A_SECOND_WAY}`]).filter(isDrawn);

    expect(ends.length).toBeGreaterThan(0);
    expect(everyWay.filter((name) => pictureOf(name).colours.includes(ofTheLook("poppy")))).toEqual([]);
  });

  test("test_the_blank_one_is_a_plot_marked_out_by_one_whole_line_low_and_wide", () => {
    // It is one colour, the shade of a blank in a town, and its line is whole: every pixel of
    // it lies against two others. As high as it was wide, a plot was taken for a box to be ticked.
    const blank = pictureOf(NO_PICTURE);
    const line = placesOf(blank).filter(({ colour }) => colour !== CLEAR);
    const beside = (one: { x: number; y: number }) =>
      line.filter((other) => Math.abs(other.x - one.x) + Math.abs(other.y - one.y) === 1).length;

    expect(new Set(line.map(({ colour }) => colour))).toEqual(new Set([ofTheLook("shade")]));
    expect(line.filter((one) => beside(one) !== 2)).toEqual([]);
    const [across, down] = [line.map(({ x }) => x), line.map(({ y }) => y)];
    const [wide, high] = [Math.max(...across) - Math.min(...across) + 1, Math.max(...down) - Math.min(...down) + 1];
    expect(wide).toBeGreaterThanOrEqual(high * 2);
    expect(Math.max(...down)).toBe(blank.height - 1);
  });
});

// ---------------------------------------------------------------------------
// The ground of a page: the meadow, in tiles.
// ---------------------------------------------------------------------------

describe("the ground of a page", () => {
  /** A tile is 16 art pixels square. */
  const TILE = 16;
  /** The four tiles of meadow: three that are marked, with tufts and with daisies, and the plain one. */
  const MEADOW = { a: "tile-grass-a", b: "tile-grass-b", c: "tile-grass-c", d: "tile-grass-d" } as const;
  const DAISIES = "b";
  const PLAIN = "d";

  /** The ground read back into its tiles: a letter for each, or a question mark for what is none of the four. */
  const tiles = (): string[][] => {
    const ground = pictureOf("ground");
    const kinds = Object.entries(MEADOW).map(([kind, name]) => [kind, JSON.stringify(pictureOf(name).pixels)] as const);
    return Array.from({ length: ground.height / TILE }, (_, row) =>
      Array.from({ length: ground.width / TILE }, (__, column) => {
        const tile = JSON.stringify(partOf(ground, column * TILE, row * TILE, TILE, TILE));
        return kinds.find(([, pixels]) => pixels === tile)?.[0] ?? "?";
      }),
    );
  };
  /** Where the tiles of some kinds lie, by column and row. */
  const where = (kinds: string) =>
    tiles().flatMap((row, y) => row.flatMap((kind, x) => (kinds.includes(kind) ? [{ x, y }] : [])));
  /** How far apart two tiles are one way, round the edge if that is nearer: the ground lies against itself. */
  const apart = (one: number, other: number, side: number) => Math.min(Math.abs(one - other), side - Math.abs(one - other));
  /** Every pair of some tiles. */
  const pairs = <T,>(of: readonly T[]) => of.flatMap((one, at) => of.slice(at + 1).map((other) => [one, other] as const));

  test("test_the_ground_is_town_maps_four_tiles_of_meadow_and_nothing_else", () => {
    const ground = pictureOf("ground");

    // Town Map laid one of 64 art pixels, and the eye found its daisy eleven times across a desk.
    expect([128, 192]).toContain(ground.width);
    expect(ground.height).toBe(ground.width);
    expect(tiles().flat().filter((kind) => kind === "?")).toEqual([]);
    expect([...ground.colours].sort()).toEqual([ofTheLook("meadow"), ofTheLook("verge"), ofTheLook("page"), ofTheLook("amber")].sort());
  });

  test("test_the_meadow_is_laid_three_ways_and_most_of_it_is_plain_grass", () => {
    // It is a ground, behind boxes of words, and is never busier than what stands on it.
    const laid = tiles().flat();
    const count = (kind: string) => laid.filter((one) => one === kind).length;

    expect(["a", "b", "c"].filter((kind) => count(kind) === 0)).toEqual([]);
    expect(count(PLAIN)).toBeGreaterThanOrEqual((laid.length * 3) / 4);
    // The daisies are what the eye finds first, so they are the fewest.
    expect(count(DAISIES)).toBeLessThan(count("a"));
    expect(count(DAISIES)).toBeLessThan(count("c"));
  });

  test("test_no_row_and_no_column_of_daisies_lines_up", () => {
    // No two tiles of daisies stand in one row of tiles, in one column or on one slant.
    const side = tiles().length;
    const lined = pairs(where(DAISIES)).filter(([one, other]) => {
      const [across, down] = [apart(one.x, other.x, side), apart(one.y, other.y, side)];
      return across === 0 || down === 0 || across === down;
    });

    expect(where(DAISIES).length).toBeGreaterThan(1);
    expect(lined).toEqual([]);
  });

  test("test_no_tile_with_anything_on_it_stands_beside_another_or_corner_to_corner_with_one", () => {
    // Round the edges too: the right edge of the ground lies against its left, and its foot against its head.
    const side = tiles().length;
    const close = pairs(where("abc")).filter(
      ([one, other]) => Math.max(apart(one.x, other.x, side), apart(one.y, other.y, side)) < 2,
    );

    expect(close).toEqual([]);
  });

  test("test_the_ground_lies_edge_to_edge_with_itself_with_no_seam", () => {
    // A style sheet lays the picture again and again. Its left column lies beside its right and
    // its top row under its last: all four are plain meadow, so nothing is cut in two where
    // they meet, and nothing drawn at one edge stands against what is drawn at the other.
    const { pixels, width, height } = pictureOf("ground");
    const meadow = ofTheLook("meadow");
    const edges = [pixels[0]!, pixels[height - 1]!, pixels.map((row) => row[0]!), pixels.map((row) => row[width - 1]!)];

    expect(edges.map((edge) => [...new Set(edge)])).toEqual(Array(4).fill([meadow]));
    // Laid two across and two down, it reads back as the same tiles, twice each way.
    const twice = [...pixels, ...pixels].map((row) => [...row, ...row]);
    const again = partOf({ ...pictureOf("ground"), pixels: twice }, width - TILE, height - TILE, 2 * TILE, 2 * TILE);
    const corners = [tiles().at(-1)!.at(-1)!, tiles().at(-1)![0]!, tiles()[0]!.at(-1)!, tiles()[0]![0]!].map((kind) =>
      pictureOf(MEADOW[kind as keyof typeof MEADOW]).pixels,
    );
    const met = [
      ...corners[0]!.map((row, y) => [...row, ...corners[1]![y]!]),
      ...corners[2]!.map((row, y) => [...row, ...corners[3]![y]!]),
    ];
    expect(again).toEqual(met);
  });

  test("test_nothing_drawn_on_a_tile_of_meadow_touches_its_edge", () => {
    // So any tile of meadow lies against any other, whichever way round.
    for (const name of Object.values(MEADOW)) {
      const { pixels } = pictureOf(name);
      const edge = [...pixels[0]!, ...pixels[TILE - 1]!, ...pixels.map((row) => row[0]!), ...pixels.map((row) => row[TILE - 1]!)];

      expect([name, ART[name], [...new Set(edge)]]).toEqual([name, { width: TILE, height: TILE }, [ofTheLook("meadow")]]);
    }
    expect(new Set(pictureOf(MEADOW.d).pixels.flat())).toEqual(new Set([ofTheLook("meadow")]));
  });

  test("test_the_grain_of_water_is_two_tiles_of_haven_and_shallows", () => {
    for (const name of ["tile-water-1", "tile-water-2"] as const) {
      expect([name, ART[name], [...pictureOf(name).colours].sort()]).toEqual([
        name,
        { width: TILE, height: TILE },
        [ofTheLook("haven"), ofTheLook("shallows")].sort(),
      ]);
    }
    expect(JSON.stringify(pictureOf("tile-water-1").pixels)).not.toBe(JSON.stringify(pictureOf("tile-water-2").pixels));
  });
});

// ---------------------------------------------------------------------------
// The things of a search.
// ---------------------------------------------------------------------------

/** What is no vibe, and is a thing of a search all the same. */
const NO_VIBE = ["thing-alike", "thing-area", "thing-budget", "thing-home", "thing-journey", "thing-tenure", "thing-usual"];
/** What stands for whatever has no drawing of its own and no family that has one. */
const PLAIN = "thing-plain";
/** A thing in outline is named for its thing, with this after it. */
const IN_OUTLINE = "-off";
/** The dimension of the chains of grocers, gyms and coffee places, which the settings show as a group of their own. */
const BRANDS = "brands";

/** What begins the name of the thing of a family, and of a group of measures that is drawn as one. */
const OF_A_FAMILY = "thing-family-";
/** What begins the name of the thing of a vibe whose id would give it the name of another thing. */
const OF_A_VIBE = "thing-vibe-";

/**
 * The thing of a vibe, by its id. Where that would be named as the thing of a family is,
 * it is named for a vibe outright: so no vibe takes the drawing of a family, and none is
 * left under its family's because of how its id begins.
 */
const thingOf = (vibe: string) => {
  const plain = `thing-${inAName(vibe)}`;
  return plain.startsWith(OF_A_FAMILY) || plain.startsWith(OF_A_VIBE) ? `${OF_A_VIBE}${inAName(vibe)}` : plain;
};
const thingOfFamily = (family: string) => `${OF_A_FAMILY}${inAName(family)}`;

describe("the things of a search", () => {
  const things = (Object.keys(ART) as ArtName[]).filter((name) => name.startsWith("thing-") && !name.endsWith(IN_OUTLINE));
  const vibes = releases().flatMap(({ tags }) => tags);
  const families = [...new Set(releases().flatMap(({ families: named }) => named.map(({ family }) => family)))];
  const measures = releases().flatMap(({ features }) => features);
  /** What kind of thing a measure counts, as the service says it of every measure. */
  const dimensions = [...new Set(measures.map(({ dimension }) => dimension))];
  /**
   * The groups of measures that stand apart from the families of vibes, each by the
   * dimension of what it holds: the measures the service puts in no family, and the brands,
   * which it puts in one and which would bury it.
   */
  const apart = [...new Set(measures.filter(({ family, dimension }) => family === null || dimension === BRANDS).map(({ dimension }) => dimension))];

  test("test_every_vibe_of_every_recorded_release_has_a_thing_or_falls_to_its_familys", () => {
    expect(vibes.length).toBeGreaterThan(0);

    const undrawn = vibes.filter(({ tag_id, family }) => !isDrawn(thingOf(tag_id)) && !isDrawn(thingOfFamily(family)));

    expect(undrawn.map(({ tag_id }) => tag_id)).toEqual([]);
  });

  test("test_every_vibe_of_the_recorded_releases_has_a_thing_of_its_own_today", () => {
    // A later release may bring a vibe that has none, and its family's drawing stands for it.
    // Every vibe there is today was drawn, and this says which thing to draw when one is not.
    const ofVibes = new Set(vibes.map(({ tag_id }) => thingOf(tag_id)));
    const ofFamilies = new Set(families.map(thingOfFamily));

    expect([...ofVibes].filter((thing) => !isDrawn(thing))).toEqual([]);
    // And nothing is drawn that stands for nothing: a thing is a vibe's, a family's, that of
    // a group of measures that stands apart, one of the seven that are no vibe, or the plain one.
    const ofGroups = new Set(apart.map(thingOfFamily));
    expect(
      things.filter((thing) => !ofVibes.has(thing) && !ofFamilies.has(thing) && !ofGroups.has(thing) && !NO_VIBE.includes(thing) && thing !== PLAIN),
    ).toEqual([]);
  });

  test("test_every_group_of_measures_that_stands_apart_has_a_thing_by_the_dimension_of_what_it_holds", () => {
    // Three groups of the settings stood under the plain box, where every family of vibes
    // had a drawing: the brands nearby, air and noise, and recorded crime. Each is drawn as a
    // family is, and is named for the dimension the service gives its measures.
    expect(apart.length).toBe(3);
    expect(apart.filter((dimension) => !isDrawn(thingOfFamily(dimension)))).toEqual([]);
    // A dimension is no family, and no vibe is named as the thing of one is.
    expect(apart.filter((dimension) => (families as string[]).includes(dimension))).toEqual([]);
    expect(vibes.map(({ tag_id }) => thingOf(tag_id)).filter((thing) => dimensions.map(thingOfFamily).includes(thing))).toEqual([]);
  });

  test("test_the_thing_of_a_family_or_of_a_group_holds_no_amber_since_the_bar_it_stands_on_is_amber_while_open", () => {
    // Seen in a browser: a carrier bag in amber was lost on the bar of its group once the
    // group was open. What stands on such a bar is told from it by its colours.
    const onABar = [...families, ...apart].map(thingOfFamily).filter(isDrawn);

    expect(onABar.length).toBe(families.length + apart.length);
    expect(onABar.filter((name) => pictureOf(name).colours.includes(ofTheLook("amber")))).toEqual([]);
  });

  test("test_recorded_crime_is_drawn_as_a_count_that_was_written_down_and_nothing_of_it_is_poppy", () => {
    // It is never a warning, a villain or a thing to fear, and nothing is red to say danger.
    // What is drawn is a sheet on its board with a tally on it, in ink on page.
    const crime = [...new Set(measures.filter(({ dimension }) => dimension === RECORDED_CRIME).map(({ dimension }) => thingOfFamily(dimension)))];

    expect(crime).toHaveLength(1);
    for (const name of crime) {
      const picture = pictureOf(name as ArtName);
      expect([name, picture.colours.includes(ofTheLook("poppy"))]).toEqual([name, false]);
      expect([name, picture.colours.includes(ofTheLook("amber"))]).toEqual([name, false]);
      expect([name, picture.colours.includes(ofTheLook("page")), picture.colours.includes(ofTheLook("ink"))]).toEqual([name, true, true]);
      // What is written on its sheet is a tally, stroke by stroke. Each stroke is upright and
      // stands apart, and nothing crosses one: crossed, the strokes were read as letters, and
      // no word and no figure is drawn in a picture.
      const sheet = placesOf(picture).filter(({ colour }) => colour === ofTheLook("page"));
      const [left, right] = [Math.min(...sheet.map(({ x }) => x)), Math.max(...sheet.map(({ x }) => x))];
      const [top, foot] = [Math.min(...sheet.map(({ y }) => y)), Math.max(...sheet.map(({ y }) => y))];
      const written = placesOf(picture).filter(({ x, y, colour }) => colour === ofTheLook("ink") && x > left && x < right && y > top && y < foot);
      const inkAt = (x: number, y: number) => picture.pixels[y]?.[x] === ofTheLook("ink");
      expect(written.length).toBeGreaterThanOrEqual(10);
      expect(written.filter(({ x, y }) => inkAt(x - 1, y) || inkAt(x + 1, y))).toEqual([]);
      expect(written.filter(({ x, y }) => !inkAt(x, y - 1) && !inkAt(x, y + 1))).toEqual([]);
    }
  });

  test("test_the_brands_nearby_are_drawn_with_no_letter_and_no_mark_on_them", () => {
    // No name and no mark of a company is drawn: what is drawn is one thing, whole, of few
    // colours, and nothing stands on its face but a band from edge to edge. Its face is
    // what lies under the row where the light falls on it, within its outline and its shade.
    const picture = pictureOf(thingOfFamily(BRANDS) as ArtName);
    const face = partOf(picture, 3, 6, 9, 7);

    // Every row of its face is one colour from side to side: a letter or a mark would break one.
    expect(face.filter((row) => new Set(row).size > 1)).toEqual([]);
  });

  test("test_every_family_the_service_names_has_a_thing_and_so_has_what_has_none", () => {
    expect(families.length).toBeGreaterThan(0);

    expect(families.filter((family) => !isDrawn(thingOfFamily(family)))).toEqual([]);
    // What a later release brings that has no drawing, and no family that has one.
    expect(isDrawn(PLAIN)).toBe(true);
  });

  test("test_no_vibe_has_the_name_of_the_thing_of_a_family_whatever_its_id_begins_with", () => {
    // A vibe whose id begins "family" would be named as the thing of a family is, and a
    // family named "area" would take the drawing of the vibe "family_area". So the thing
    // of such a vibe is named for a vibe outright, and what is named as a family's is a
    // family's, or that of a group of measures.
    const ofFamilies = [...families, ...dimensions].map(thingOfFamily);
    const ofVibes = vibes.map(({ tag_id }) => thingOf(tag_id));

    expect(vibes.some(({ tag_id }) => `thing-${inAName(tag_id)}`.startsWith(OF_A_FAMILY))).toBe(true);
    expect(ofVibes.filter((thing) => ofFamilies.includes(thing) || thing.startsWith(OF_A_FAMILY))).toEqual([]);
    expect(things.filter((thing) => thing.startsWith(OF_A_FAMILY) && !ofFamilies.includes(thing))).toEqual([]);
    expect(things.filter((thing) => thing.startsWith(OF_A_VIBE) && !ofVibes.includes(thing))).toEqual([]);
  });

  test("test_what_is_no_vibe_has_its_thing", () => {
    // A journey, a budget, renting or buying, the kind of home, an area that was named, more
    // like a place, and the usual settings nobody chose.
    expect(NO_VIBE.filter((thing) => !isDrawn(thing))).toEqual([]);
  });

  test("test_every_thing_is_16_art_pixels_square", () => {
    // Each stands beside the words it is for, and one may take the place of another there.
    expect(things.length).toBeGreaterThan(0);
    expect(new Set(things.map((name) => `${ART[name].width} by ${ART[name].height}`))).toEqual(new Set(["16 by 16"]));
  });

  test("test_a_thing_of_who_lives_there_is_a_page_of_a_register_and_pictures_nobody", () => {
    // Nothing pictures a person. What stands for a vibe that counts who lived somewhere is the
    // page of the family, ruled, with the band at its head in a colour of its own, and nothing else.
    const counted = [...new Set(vibes.filter(({ family }) => family === WHO_LIVES_THERE).map(({ tag_id }) => thingOf(tag_id)))];
    const page = pictureOf(thingOfFamily(WHO_LIVES_THERE));
    const band = (picture: Picture) => new Set(partOf(picture, 3, 2, 10, 1).flat());
    const under = (picture: Picture) => picture.pixels.map((row, y) => (y === 2 ? [] : row));

    expect(counted.length).toBeGreaterThan(0);
    for (const name of counted) {
      const thing = pictureOf(name as ArtName);

      // It is the page of the family, point for point, but for its band.
      expect([name, under(thing)]).toEqual([name, under(page)]);
      expect([name, band(thing).size]).toEqual([name, 1]);
    }
    // Each is told from the others, and from the page of the family, by its band.
    const bands = [page, ...counted.map((name) => pictureOf(name as ArtName))].map((picture) => [...band(picture)][0]);
    expect(new Set(bands).size).toBe(bands.length);

    // The page itself: ink, page, its shade in sand, and its rules and its band in shade. A
    // rule is one row high, with paper over it and under it.
    expect([...page.colours].filter((colour) => colour !== CLEAR).sort()).toEqual(
      [ofTheLook("ink"), ofTheLook("page"), ofTheLook("sand"), ofTheLook("shade")].sort(),
    );
    const ruled = partOf(page, 3, 4, 9, 9).map((row) => row.filter((colour) => colour === ofTheLook("shade")).length > 0);
    expect(ruled).toEqual([false, true, false, true, false, true, false, true, false]);
  });
});

describe("a thing in outline", () => {
  const names = Object.keys(ART) as ArtName[];
  const things = names.filter((name) => name.startsWith("thing-") && !name.endsWith(IN_OUTLINE));
  const outlines = names.filter((name) => name.endsWith(IN_OUTLINE));

  test("test_every_thing_has_its_outline_and_every_outline_its_thing", () => {
    // A thing that counts for nothing is drawn in outline, whatever thing it is.
    expect(outlines).toEqual(things.map((name) => `${name}${IN_OUTLINE}`).sort());
  });

  test("test_a_thing_in_outline_is_its_thing_with_every_colour_but_ink_turned_to_page", () => {
    // Nothing is dimmed or drawn see-through to say that a thing does not count. Its colour is
    // taken off it, and its words say the rest.
    const differ = things.filter((name) => {
      const bare = pictureOf(name).pixels.map((row) =>
        row.map((colour) => (colour === CLEAR || colour === ofTheLook("ink") ? colour : ofTheLook("page"))),
      );
      return JSON.stringify(pictureOf(`${name}${IN_OUTLINE}`).pixels) !== JSON.stringify(bare);
    });

    expect(differ).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Burro, who is a rabbit.
// ---------------------------------------------------------------------------

/** A strip cut into its frames, each as wide as the canvas. */
function framesOf(strip: Picture, frames: number): Pixel[][][] {
  const wide = strip.width / frames;
  return Array.from({ length: frames }, (_, frame) => strip.pixels.map((row) => row.slice(frame * wide, (frame + 1) * wide)));
}

describe("the drawings of Burro", () => {
  const names = Object.keys(ART) as ArtName[];
  const still = BURRO.filter((name) => name !== "burro-hops");
  const hop = () => framesOf(pictureOf("burro-hops"), ART["burro-hops"].frames);
  /** Every picture of him as a page shows one: each still drawing, and each frame of the hop. */
  const shown = (): [string, Pixel[][]][] => [
    ...still.map((name): [string, Pixel[][]] => [name, pictureOf(name).pixels.map((row) => [...row])]),
    ...hop().map((frame, at): [string, Pixel[][]] => [`burro-hops, frame ${at + 1}`, frame]),
  ];
  const used = (pixels: readonly (readonly Pixel[])[]) => [...new Set(pixels.flat())].filter((pixel) => pixel !== CLEAR);
  /** His fur, his light, his shade and what is pale of him: his outline is ink, which his burrow's is too. */
  const his = (["fur", "sand", "shade", "page"] as const).map(ofTheLook);
  const ink = ofTheLook("ink");
  const earth = ofTheLook("earth");

  test("test_nothing_is_named_for_burro_but_his_three_drawings_and_what_he_does_at_rest", () => {
    // He sits, he hops and he waits. Where he rests he stirs, and a strip holds what he
    // does there. What was drawn of an earlier story is gone: he digs no hole, and is not
    // at home in one.
    const his = names.filter((name) => name.startsWith("burro"));
    expect(his.filter((name) => !OVER_HIS_HOP.test(name))).toEqual([...BURRO, ...AT_REST].sort());
    expect(BURRO).toHaveLength(3);
    // What lies over his hop holds a frame for each frame of it, on his canvas: so it is
    // laid over him frame for frame, and moves nothing that stands beside him.
    for (const name of his.filter((one) => OVER_HIS_HOP.test(one))) expect([name, ART[name]]).toEqual([name, ART["burro-hops"]]);
    // A strip is of a pose in which nothing is asked of him. Where he hops he has the hop,
    // and where he waits nothing may move.
    expect(AT_REST.map((name) => name.replace(/-stirs$/, ""))).toEqual(["burro-sits"]);
  });

  test("test_nothing_is_drawn_of_a_question_or_of_the_button_that_stood_by_him", () => {
    // Burro asks nothing, and the founder had the button that stopped him go. The
    // drawings of both were kept, and nothing drew them: they are gone from the drawings,
    // from the pictures and from the list of their names.
    const pictures = readdirSync(PICTURES);
    const drawings = readdirSync(DRAWINGS)
      .filter((file) => file.endsWith(".sprite.txt"))
      .map((file) => readFileSync(path.join(DRAWINGS, file), "utf8"));

    for (const name of GONE) {
      expect([name, (names as readonly string[]).includes(name)]).toEqual([name, false]);
      expect([name, pictures.includes(`${name}.png`)]).toEqual([name, false]);
      expect([name, drawings.some((text) => new RegExp(`^== ${name}$`, "m").test(text))]).toEqual([name, false]);
    }
  });

  test("test_every_drawing_of_burro_is_on_one_canvas_so_that_he_never_jumps", () => {
    // The part that draws him keeps a box of one size in every pose, which is there before he
    // is and after. A drawing of another size would move what stands beside him.
    const { frames } = ART["burro-hops"];

    expect(still.map((name) => [name, ART[name]])).toEqual(still.map((name) => [name, CANVAS]));
    expect(ART["burro-hops"]).toEqual({ width: CANVAS.width * frames, height: CANVAS.height, frames });
    expect(frames).toBeGreaterThanOrEqual(8);
    expect(frames).toBeLessThanOrEqual(12);
    // A frame of what he does at rest is one canvas too, and the two strips hold as many.
    for (const name of AT_REST) {
      expect([name, ART[name]]).toEqual([
        name,
        { width: CANVAS.width * FRAMES_AT_REST, height: CANVAS.height, frames: FRAMES_AT_REST },
      ]);
    }
  });

  test("test_burro_stands_on_the_same_row_in_every_drawing_and_in_every_frame", () => {
    const lowest = shown().map(([name, pixels]) => [name, pixels.findLastIndex((row) => row.some((pixel) => pixel !== CLEAR))]);

    expect(lowest).toEqual(shown().map(([name]) => [name, GROUND]));
  });

  test("test_the_hop_comes_round_with_no_jump_and_the_hole_is_alone_for_a_beat", () => {
    // The strip is shown again and again until the answer is in. Its last frame is its first,
    // the hole alone: so where it comes round nothing is seen to change, and the hole is
    // alone for two frames together.
    const frames = hop();
    const [first, last] = [frames[0]!, frames.at(-1)!];

    expect(last).toEqual(first);
    // Nothing of him is in sight in it: it is earth, its clods in shade, and the dark.
    expect(used(first).sort()).toEqual([ink, earth, ofTheLook("shade")].sort());
    // No other frame is drawn twice: each is a step of the one movement.
    expect(new Set(frames.slice(0, -1).map((frame) => JSON.stringify(frame))).size).toBe(frames.length - 1);
  });

  test("test_he_comes_up_ears_first_and_goes_down_scut_last", () => {
    // After the hole alone, his ears: fur, and nothing pale of him yet. Before it, his scut:
    // pale, and no fur left in sight.
    const frames = hop();
    const [fur, pale] = [ofTheLook("fur"), ofTheLook("page")];
    const [ears, scut] = [used(frames[1]!), used(frames.at(-2)!)];

    expect([ears.includes(fur), ears.includes(pale)]).toEqual([true, false]);
    expect([scut.includes(fur), scut.includes(pale)]).toEqual([false, true]);
    // Between them he is out, and whole: in some frame he stands as high as his canvas.
    expect(frames.some((frame) => frame[0]!.some((pixel) => pixel !== CLEAR))).toBe(true);
  });

  test("test_his_burrow_is_in_one_place_in_every_frame_of_the_hop", () => {
    // Nothing is seen to move but him. Where the hole alone is drawn, a frame holds the hole
    // or him in front of it. And no earth is drawn where the hole alone has none.
    const hole = hop()[0]!;
    const moved = hop().map((frame, at) =>
      frame.flatMap((row, y) =>
        row.flatMap((pixel, x) => {
          const there = hole[y]![x]!;
          if (pixel === earth && there !== earth) return [`frame ${at + 1}: earth at ${x}, ${y}`];
          if (there !== CLEAR && pixel !== there && pixel !== ink && !his.includes(pixel)) return [`frame ${at + 1}: ${pixel} at ${x}, ${y}`];
          return [];
        }),
      ),
    );

    expect(moved.flat()).toEqual([]);
  });

  test("test_where_nothing_may_move_he_waits_as_he_sits_up_in_the_hop_point_for_point", () => {
    // So his hole is where it is in the hop, and the box he is drawn in holds the same picture
    // whether he moves or not.
    const waits = JSON.stringify(pictureOf("burro-waits").pixels);
    const as = hop().flatMap((frame, at) => (JSON.stringify(frame) === waits ? [at] : []));

    expect(as).toHaveLength(1);
    // In it he is out, whole, and beside his hole: all that is his is in sight, and so is the dark of its mouth.
    const frame = hop()[as[0]!]!;
    expect(his.filter((colour) => !used(frame).includes(colour))).toEqual([]);
    expect(used(frame)).toContain(earth);
  });

  test("test_burro_is_a_wild_rabbit_in_brown_and_grey_with_a_pale_belly_and_a_pale_scut", () => {
    // Not white, not pink, not a toy. His fur is fur, lit in sand and shaded in shade, what is
    // pale of him is page, and his outline and his eye are ink. His burrow is earth, and its clods are shade.
    expect(used(pictureOf("burro-sits").pixels).sort()).toEqual([ink, ...his].sort());
    for (const [name, pixels] of shown()) {
      expect([name, used(pixels).filter((pixel) => ![ink, earth, ...his].includes(pixel))]).toEqual([name, []]);
    }
  });

  test("test_every_part_of_burro_and_of_his_burrow_has_an_outline_of_ink", () => {
    // A colour never stands bare against the page, in any drawing of him or frame of the hop.
    const bare = shown().map(([name, pixels]) => {
      const at = (x: number, y: number) => pixels[y]?.[x] ?? CLEAR;
      const found = pixels.flatMap((row, y) =>
        row.flatMap((pixel, x) =>
          pixel !== CLEAR && pixel !== ink && [at(x - 1, y), at(x + 1, y), at(x, y - 1), at(x, y + 1)].includes(CLEAR)
            ? [`${pixel} at ${x}, ${y}`]
            : [],
        ),
      );
      return [name, found];
    });

    expect(bare.filter(([, found]) => found!.length > 0)).toEqual([]);
  });
});

/** Every file of the website that is no test, and is not the list of the drawings: what draws them. */
function theWebsite(folder = path.join(ROOT, "src")): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return theWebsite(file);
    if (!/\.(tsx?|css)$/.test(entry.name) || /\.test\.tsx?$/.test(entry.name)) return [];
    return file === path.join(ROOT, "src", "lib", "art", "names.ts") ? [] : [readFileSync(file, "utf8")];
  });
}

describe("what draws each drawing", () => {
  const names = Object.keys(ART) as ArtName[];
  const written = theWebsite().join("\n");
  /** True of a drawing that a file of the website names outright, or asks for by its address. */
  const isNamed = (name: string) => written.includes(`"${name}"`) || written.includes(`/art/${name}.png`);
  const vibes = releases().flatMap(({ tags }) => tags);
  /**
   * What a rule of the kit makes the name of, from what the service gives: the thing of a
   * vibe, of a family and of a dimension, the two ends of a vibe, and an end by its name.
   */
  const byRule = new Set([
    ...vibes.map(({ tag_id }) => thingOf(tag_id)),
    ...releases().flatMap(({ families }) => families.map(({ family }) => thingOfFamily(family))),
    ...releases().flatMap(({ features }) => features.map(({ dimension }) => thingOfFamily(dimension))),
    ...vibes.flatMap(({ tag_id }) => [endOf(tag_id, "low"), endOf(tag_id, "high")]).flatMap((end) => [end, `${end}${A_SECOND_WAY}`]),
    ...vibes.flatMap(({ low_end, high_end }) => [low_end ?? STRIP.least, high_end ?? STRIP.most]).map((end) => `key-${inAName(end)}`),
  ]);
  const isDrawnBySomething = (name: string): boolean =>
    isNamed(name) || byRule.has(name) || (name.endsWith(IN_OUTLINE) && isDrawnBySomething(name.slice(0, -IN_OUTLINE.length)));
  /**
   * What no page draws, and is kept for what a test holds to it. The tiles are what the
   * ground is laid with and what the grain of the map is held to, point for point. The box
   * as Town Map named it is what the box of the style sheet is held to.
   */
  const KEPT_FOR_A_TEST = ["tile-grass-a", "tile-grass-b", "tile-grass-c", "tile-grass-d", "tile-water-1", "tile-water-2", "ui-box", "ui-box-on"];
  test("test_every_drawing_is_named_by_a_file_of_the_website_or_made_by_a_rule_from_what_the_service_gives", () => {
    // A drawing that nothing draws is taken away, with its picture: what was drawn of a
    // question went so, and the button that stood by the rabbit. His own drawings are held
    // beside the part that draws him.
    const ours = names.filter((name) => !name.startsWith("burro-"));
    const drawnByNothing = ours.filter((name) => !isDrawnBySomething(name));

    expect(written.length).toBeGreaterThan(100_000);
    expect(drawnByNothing.filter((name) => !KEPT_FOR_A_TEST.includes(name))).toEqual([]);
    // What is kept for a test is drawn by nothing still: one that a page comes to draw is no longer written down here.
    expect(KEPT_FOR_A_TEST.filter((name) => !drawnByNothing.includes(name as ArtName))).toEqual([]);
    expect(KEPT_FOR_A_TEST.filter((name) => !isDrawn(name))).toEqual([]);
    // What stands for a trade-off is drawn two ways, of which a result shows one, and both
    // are named by the one table a result and the key draw by: so the way that is not
    // shown is kept, for whoever chooses between the two. The mark of what is not whole is
    // named by its part of the kit.
    expect(["ui-approx", "ui-tradeoff", "ui-tradeoff-b"].filter((name) => !isNamed(name))).toEqual([]);
  });
});

describe("what is no longer drawn", () => {
  const names = Object.keys(ART) as ArtName[];

  test("test_nothing_is_drawn_of_the_donkey_or_of_what_was_his", () => {
    // A thing and an end of a scale are named by what the service gives, which may say anything.
    const ours = names.filter((name) => !name.startsWith("thing-") && !name.startsWith("key-"));

    expect(ours.filter((name) => THE_DONKEYS.some((his) => his.test(name)))).toEqual([]);
  });

  test("test_nothing_is_drawn_of_the_earlier_account_of_the_look", () => {
    const ours = names.filter((name) => !name.startsWith("thing-") && !name.startsWith("key-"));

    expect(ours.filter((name) => OF_THE_EARLIER_ACCOUNT.some((gone) => gone.test(name)))).toEqual([]);
    // A thing of a search is one of Town Map's things, and no jar.
    expect(names.filter((name) => name.includes("jar"))).toEqual([]);
  });
});
