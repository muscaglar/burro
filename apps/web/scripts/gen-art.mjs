// Makes the pictures of the website from its drawings.
//
//   node scripts/gen-art.mjs           write the files
//   node scripts/gen-art.mjs --check   write nothing; fail if a file is not what the drawings give
//
// A drawing is text, one character a pixel, in art/NAME.sprite.txt. A file may
// hold several. Two things come of them:
//   public/art/NAME.png     one picture for each drawing, a pixel of it an art pixel
//   src/lib/art/names.ts    every drawing, with its width and height in art pixels
//
// The drawings are the only source of either. Nothing in public/art/ is drawn by hand.
//
// The same drawings give the same bytes on every machine. Node's own zlib would
// not promise it: how it packs a stream is left to the library a build of Node
// was made with, and a picture is checked on other machines than the one that
// made it. So a picture is packed here, in a way that is written down below,
// and zlib reads it back: here, before a picture is written, and again in
// test/art.test.ts, which opens every picture with it.
//
// `--root FOLDER` reads and writes under another folder than the website's. It
// is for the tests of this file.

import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { inflateSync } from "node:zlib";

// The colours of the look, by the names the style sheet gives them. A drawing is made of
// these and of no other. test/art.test.ts holds each to the colour of its name in
// src/styles/tokens.css, so a colour is added here and there, in one change. A colour is
// added at the foot: the colours of a picture stand in this order, and a picture that does
// not use the new one keeps its bytes.
const COLOURS = [
  ["ink", "#2a2140"],
  ["page", "#f7f1de"],
  ["lea", "#dbe8b1"],
  ["sand", "#e9cf94"],
  ["meadow", "#a8d85e"],
  ["verge", "#63b34a"],
  ["hedge", "#2b7a5a"],
  ["shallows", "#86dde2"],
  ["haven", "#2f9fd0"],
  ["cobalt", "#3453d1"],
  ["amber", "#f6b426"],
  ["poppy", "#db533b"],
  ["heath", "#b87bc6"],
  ["fur", "#9b8a7f"],
  ["shade", "#65566a"],
  ["slate", "#6d7fa6"],
  ["earth", "#a9683d"],
];
const OF_THE_LOOK = new Set(COLOURS.map(([, value]) => value));
const CLEAR = "clear";

const NAME = /^[a-z0-9][a-z0-9-]*$/;
const DRAWINGS = ".sprite.txt";
const BANNER = `/**
 * Generated from art/*.sprite.txt by \`npm run gen:art\`.
 * Never edited by hand: change a drawing and generate again.
 */

`;

/** What is wrong with a drawing, said with where it is. Nothing is written once one is thrown. */
class Fault extends Error {}

// ---------------------------------------------------------------------------
// Reading. A file is read line by line, from its head: the palette, and then
// each drawing under its name. What a line is depends on what stands over it
// and never on what follows, so a fault is said with the line it is on.
// ---------------------------------------------------------------------------

/** The colour a palette line names: one of the look by its value, `clear`, or a fault. */
function colourOf(text, where) {
  const said = text.trim();
  if (said === "transparent" || said === "none" || said === "clear") return { is: CLEAR };
  const found = /^#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$/.exec(said);
  if (found === null) {
    throw new Fault(`${where}: '${said}' is not a colour. Write #rrggbb, #rrggbbaa or transparent.`);
  }
  const alpha = found[2] === undefined ? 255 : Number.parseInt(found[2], 16);
  if (alpha === 0) return { is: CLEAR };
  const value = `#${found[1].toLowerCase()}`;
  // A colour that is not of the look may stand in a palette. It may not be drawn with.
  if (alpha !== 255) return { is: "refused", why: `${said}, which is see-through` };
  if (!OF_THE_LOOK.has(value)) return { is: "refused", why: said };
  return { is: value };
}

/** Whole numbers after a word, as `# @cut 12` has them, or a fault. */
function numbersOf(text, where, what) {
  const parts = text.trim().split(/\s+/);
  if (text.trim() === "" || parts.some((part) => !/^\d+$/.test(part))) {
    throw new Fault(`${where}: ${what} is said in whole numbers.`);
  }
  return parts.map(Number);
}

/**
 * What a drawing says of itself, on a line that begins `# @`, before its first row.
 * It begins as a note does, so that whatever reads the format and knows no such line
 * takes it for a note.
 *
 *   # @cut 12          where a frame is cut in nine, from the top, the right, the foot
 *   # @cut 9 3 6 12    and the left, written as `border-image-slice` is
 *   # @frames 8        how many drawings of one width stand side by side in a strip
 *   # @face 7 8 18 9   where a figure is set on it in type: from the left, from the
 *                      top, how wide, how high
 */
function said(drawing, line, where) {
  const [word, ...rest] = line.slice(3).trim().split(/\s+/);
  const given = rest.join(" ");
  if (drawing.rows.length > 0) {
    throw new Fault(`${where}: '@${word}' comes before the first row of '${drawing.name}'.`);
  }
  if (word === "cut") {
    const cut = numbersOf(given, where, "A cut");
    if (cut.length > 4) throw new Fault(`${where}: a cut is four numbers at the most.`);
    const [top, right = top, bottom = top, left = right] = cut;
    drawing.cut = [top, right, bottom, left];
    drawing.cutAt = where;
    return;
  }
  if (word === "frames") {
    const frames = numbersOf(given, where, "How many frames a strip holds");
    if (frames.length !== 1 || frames[0] < 2) {
      throw new Fault(`${where}: a strip holds two frames or more, said as one number.`);
    }
    drawing.frames = frames[0];
    drawing.framesAt = where;
    return;
  }
  if (word === "face") {
    const face = numbersOf(given, where, "A face");
    if (face.length !== 4 || face[2] === 0 || face[3] === 0) {
      throw new Fault(`${where}: a face is four numbers: from the left, from the top, how wide, how high.`);
    }
    drawing.face = face;
    drawing.faceAt = where;
    return;
  }
  throw new Fault(`${where}: '@${word}' is not something a drawing says. It says @cut, @frames or @face.`);
}

/** The drawings of one file, each with its rows as the keys of the file's palette. */
function read(text, file) {
  const palette = new Map();
  const drawings = [];
  let mode = "";
  text.split(/\r\n|\r|\n/).forEach((line, index) => {
    const where = `${file}:${index + 1}`;
    if (line.startsWith("#") && mode !== "drawing") return;
    if (line.trim() === "") return;
    if (line.trim() === "palette") {
      mode = "palette";
      return;
    }
    if (line.startsWith("==")) {
      const name = line.slice(2).trim();
      if (!NAME.test(name)) {
        throw new Fault(`${where}: '${name}' is not a name. Use lower case, digits and hyphens.`);
      }
      drawings.push({ name, file, at: where, rows: [] });
      mode = "drawing";
      return;
    }
    if (mode === "palette") {
      const trimmed = line.trim();
      const space = trimmed.indexOf(" ");
      const key = space === -1 ? trimmed : trimmed.slice(0, space);
      const value = space === -1 ? "" : trimmed.slice(space + 1);
      if ([...key].length !== 1 || value === "") {
        throw new Fault(`${where}: a palette line is one character, a space and a colour.`);
      }
      palette.set(key, colourOf(value, where));
      return;
    }
    if (mode === "drawing") {
      const drawing = drawings[drawings.length - 1];
      if (line.startsWith("# @")) return said(drawing, line, where);
      if (line.startsWith("# ")) return;
      const row = [...line];
      row.forEach((key, column) => {
        if (!palette.has(key)) {
          throw new Fault(`${where}, column ${column + 1}: '${key}' is not in the palette.`);
        }
      });
      const first = drawing.rows[0];
      if (first !== undefined && first.length !== row.length) {
        throw new Fault(
          `${where}: this row of '${drawing.name}' is ${row.length} wide and its first is ${first.length}.`,
        );
      }
      drawing.rows.push(row);
      return;
    }
    throw new Fault(`${where}: expected 'palette' or '== name' before this line.`);
  });
  if (drawings.length === 0) {
    throw new Fault(`${file}: no drawing found. A drawing begins with a line '== name'.`);
  }
  return drawings.map((drawing) => finished(drawing, palette));
}

/** A drawing as it is used: its size, and each pixel as a colour of the look or as clear. */
function finished(drawing, palette) {
  const { name, file, rows } = drawing;
  if (rows.length === 0) throw new Fault(`${file}: the drawing '${name}' has no rows.`);
  const width = rows[0].length;
  const height = rows.length;
  const refused = new Map();
  const pixels = rows.map((row) =>
    row.map((key) => {
      const colour = palette.get(key);
      if (colour.is === "refused") refused.set(key, colour.why);
      return colour.is;
    }),
  );
  if (refused.size > 0) {
    const which = [...refused].map(([key, why]) => `${why} ('${key}')`).join(", ");
    throw new Fault(
      `${file}: '${name}' uses ${which}. A drawing is made of the colours of the look and of no other.`,
    );
  }
  const { cut, frames, face } = drawing;
  if (cut !== undefined && (cut[0] + cut[2] > height || cut[1] + cut[3] > width)) {
    throw new Fault(`${drawing.cutAt}: '${name}' is ${width} by ${height}, and its cut is more than the whole of it.`);
  }
  if (frames !== undefined && width % frames !== 0) {
    throw new Fault(`${drawing.framesAt}: '${name}' is ${width} wide, which is not ${frames} frames of one width.`);
  }
  if (face !== undefined && (face[0] + face[2] > width || face[1] + face[3] > height)) {
    throw new Fault(`${drawing.faceAt}: '${name}' is ${width} by ${height}, and its face runs off it.`);
  }
  return { name, file, at: drawing.at, width, height, pixels, cut, frames, face };
}

// ---------------------------------------------------------------------------
// Writing a picture. A PNG with a palette: the clear colour first where the
// drawing has one, then the colours it uses in the order of the list above, and as
// few bits to a pixel as hold them. No date and no name of a tool goes in.
// ---------------------------------------------------------------------------

const CRC = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});

function crc32(bytes) {
  let c = 0xffffffff;
  for (const byte of bytes) c = CRC[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function adler32(bytes) {
  let a = 1;
  let b = 0;
  for (const byte of bytes) {
    a = (a + byte) % 65521;
    b = (b + a) % 65521;
  }
  return ((b << 16) | a) >>> 0;
}

function fourBytes(value) {
  return [(value >>> 24) & 0xff, (value >>> 16) & 0xff, (value >>> 8) & 0xff, value & 0xff];
}

function chunk(kind, data) {
  const body = [...Buffer.from(kind, "latin1"), ...data];
  return [...fourBytes(data.length), ...body, ...fourBytes(crc32(body))];
}

/** Bits as deflate packs them: from the low end of each byte. */
class Bits {
  bytes = [];
  held = 0;
  count = 0;

  /** The low `length` bits of `value`, the lowest first. */
  put(value, length) {
    this.held |= value << this.count;
    this.count += length;
    while (this.count >= 8) {
      this.bytes.push(this.held & 0xff);
      this.held >>>= 8;
      this.count -= 8;
    }
  }

  /** A code of the fixed tables, which is written from its high end. */
  code(value, length) {
    let turned = 0;
    for (let bit = 0; bit < length; bit += 1) turned |= ((value >>> bit) & 1) << (length - 1 - bit);
    this.put(turned, length);
  }

  end() {
    if (this.count > 0) this.bytes.push(this.held & 0xff);
    return this.bytes;
  }
}

const LENGTHS = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258];
const LENGTH_BITS = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0];
const DISTANCES = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577];
const DISTANCE_BITS = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13];

const SHORTEST = 3;
const LONGEST = 258;
const WINDOW = 32768;
// Three bytes found again far back cost more to point at than to write out.
const TOO_FAR = 4096;

/** The last place whose start is no greater than the value. */
function placeIn(starts, value) {
  let place = starts.length - 1;
  while (starts[place] > value) place -= 1;
  return place;
}

/**
 * The bytes as one block of deflate, with the fixed tables. Where three bytes
 * or more stood before, within the window, the longest run of them is pointed
 * at, and of two as long the nearer. A run gives way to a longer one that
 * begins a byte later. Nothing here is left to chance or to a library, so the
 * bytes that come out depend on the bytes that go in and on nothing else.
 */
function deflated(data) {
  const bits = new Bits();
  bits.put(1, 1);
  bits.put(1, 2);

  const before = new Int32Array(data.length).fill(-1);
  const last = new Map();
  const keyAt = (at) => (data[at] << 16) | (data[at + 1] << 8) | data[at + 2];
  const remember = (at) => {
    if (at + SHORTEST > data.length) return;
    const key = keyAt(at);
    before[at] = last.get(key) ?? -1;
    last.set(key, at);
  };
  const longestAt = (at) => {
    let best = { length: 0, distance: 0 };
    if (at + SHORTEST > data.length) return best;
    const most = Math.min(LONGEST, data.length - at);
    for (let from = last.get(keyAt(at)) ?? -1; from >= 0 && at - from <= WINDOW; from = before[from]) {
      let length = 0;
      while (length < most && data[from + length] === data[at + length]) length += 1;
      if (length > best.length) best = { length, distance: at - from };
      if (length === most) break;
    }
    if (best.length < SHORTEST || (best.length === SHORTEST && best.distance > TOO_FAR)) {
      return { length: 0, distance: 0 };
    }
    return best;
  };
  const literal = (byte) => (byte < 144 ? bits.code(0x30 + byte, 8) : bits.code(0x190 + byte - 144, 9));
  const symbol = (value) => (value < 280 ? bits.code(value - 256, 7) : bits.code(0xc0 + value - 280, 8));

  let at = 0;
  while (at < data.length) {
    const here = longestAt(at);
    remember(at);
    if (here.length === 0) {
      literal(data[at]);
      at += 1;
      continue;
    }
    if (here.length < LONGEST && longestAt(at + 1).length > here.length) {
      literal(data[at]);
      at += 1;
      continue;
    }
    const length = placeIn(LENGTHS, here.length);
    symbol(257 + length);
    bits.put(here.length - LENGTHS[length], LENGTH_BITS[length]);
    const distance = placeIn(DISTANCES, here.distance);
    bits.code(distance, 5);
    bits.put(here.distance - DISTANCES[distance], DISTANCE_BITS[distance]);
    for (let covered = at + 1; covered < at + here.length; covered += 1) remember(covered);
    at += here.length;
  }
  symbol(256);
  return bits.end();
}

function picture({ name, width, height, pixels }) {
  const used = new Set(pixels.flat());
  const colours = [
    ...(used.has(CLEAR) ? [CLEAR] : []),
    ...COLOURS.map(([, value]) => value).filter((value) => used.has(value)),
  ];
  const indexOf = new Map(colours.map((colour, index) => [colour, index]));
  const depth = [1, 2, 4, 8].find((bits) => 2 ** bits >= colours.length);

  const lines = [];
  for (const row of pixels) {
    // Each line begins with how it is filtered: not at all.
    lines.push(0);
    for (let x = 0; x < width; x += 8 / depth) {
      let byte = 0;
      for (let n = 0; n < 8 / depth; n += 1) {
        byte = (byte << depth) | (x + n < width ? indexOf.get(row[x + n]) : 0);
      }
      lines.push(byte);
    }
  }

  const header = [...fourBytes(width), ...fourBytes(height), depth, 3, 0, 0, 0];
  const palette = colours.flatMap((colour) =>
    colour === CLEAR ? [0, 0, 0] : [1, 3, 5].map((at) => Number.parseInt(colour.slice(at, at + 2), 16)),
  );
  const packed = [0x78, 0xda, ...deflated(lines), ...fourBytes(adler32(lines))];
  // A picture that a browser could not open is never written.
  if (!inflateSync(Buffer.from(packed)).equals(Buffer.from(lines))) {
    throw new Error(`The picture of '${name}' does not read back as it was packed. The fault is in this file.`);
  }
  return Buffer.from([
    ...[0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a],
    ...chunk("IHDR", header),
    ...chunk("PLTE", palette),
    // The clear colour is the first of the palette, and the only one that is not solid.
    ...(used.has(CLEAR) ? chunk("tRNS", [0]) : []),
    ...chunk("IDAT", packed),
    ...chunk("IEND", []),
  ]);
}

// ---------------------------------------------------------------------------
// The list of names.
// ---------------------------------------------------------------------------

function names(drawings) {
  const lines = drawings.map(({ name, width, height, cut, frames, face }) => {
    const holds = [
      `width: ${width}`,
      `height: ${height}`,
      ...(frames === undefined ? [] : [`frames: ${frames}`]),
      ...(cut === undefined ? [] : [`cut: [${cut.join(", ")}]`]),
      ...(face === undefined ? [] : [`face: [${face.join(", ")}]`]),
    ];
    return `  ${JSON.stringify(name)}: { ${holds.join(", ")} },`;
  });
  return `${BANNER}/** What the list holds of a drawing. Every length is in art pixels. */
export interface Drawn {
  readonly width: number;
  readonly height: number;
  /** How many drawings of one width stand side by side in a strip. */
  readonly frames?: number;
  /** Where a frame is cut in nine, as \`border-image-slice\` is written. */
  readonly cut?: readonly [top: number, right: number, foot: number, left: number];
  /** Where a figure is set on the drawing in type. */
  readonly face?: readonly [left: number, top: number, width: number, height: number];
}

/**
 * Every drawing. Its picture is served as \`/art/NAME.png\`, and is shown at its width and
 * its height times \`--px\`.
 */
export const ART = {
${lines.join("\n")}
} as const satisfies Readonly<Record<string, Drawn>>;

/** The name of a drawing. */
export type ArtName = keyof typeof ART;
`;
}

// ---------------------------------------------------------------------------
// The run.
// ---------------------------------------------------------------------------

async function holds(target) {
  try {
    return await readFile(target);
  } catch {
    return null;
  }
}

async function listed(folder) {
  try {
    return (await readdir(folder)).filter((name) => !name.startsWith(".")).sort();
  } catch {
    return [];
  }
}

async function everyDrawing(folder) {
  const files = (await listed(folder)).filter((name) => name.endsWith(DRAWINGS));
  if (files.length === 0) throw new Fault(`art/ holds no drawing. A drawing is a file art/NAME${DRAWINGS}.`);
  const drawings = [];
  const seen = new Map();
  for (const file of files) {
    for (const drawing of read(await readFile(path.join(folder, file), "utf8"), `art/${file}`)) {
      const first = seen.get(drawing.name);
      if (first !== undefined) {
        throw new Fault(`${drawing.at}: '${drawing.name}' is drawn twice. The other is at ${first}.`);
      }
      seen.set(drawing.name, drawing.at);
      drawings.push(drawing);
    }
  }
  // By name, as a computer orders text and not as a language does, so that the order is one everywhere.
  return drawings.sort((one, other) => (one.name < other.name ? -1 : 1));
}

async function run(root, check) {
  const pictures = path.join(root, "public", "art");
  const list = path.join(root, "src", "lib", "art", "names.ts");
  const drawings = await everyDrawing(path.join(root, "art"));

  const files = [
    ...drawings.map((drawing) => ({
      name: `public/art/${drawing.name}.png`,
      target: path.join(pictures, `${drawing.name}.png`),
      fresh: picture(drawing),
    })),
    { name: "src/lib/art/names.ts", target: list, fresh: Buffer.from(names(drawings), "utf8") },
  ];
  const wanted = new Set(drawings.map((drawing) => `${drawing.name}.png`));
  const strays = (await listed(pictures)).filter((name) => !wanted.has(name));

  const stale = [];
  for (const file of files) {
    const there = await holds(file.target);
    if (there === null || !there.equals(file.fresh)) stale.push({ ...file, missing: there === null });
  }

  const say = (line) => process.stderr.write(`${line}\n`);
  if (check) {
    for (const { name, missing } of stale) {
      say(
        missing
          ? `${name} is not there. Run \`npm run gen:art\`.`
          : `${name} is not what the drawings in art/ give. Run \`npm run gen:art\`.`,
      );
    }
  } else {
    await mkdir(pictures, { recursive: true });
    await mkdir(path.dirname(list), { recursive: true });
    for (const { target, fresh } of stale) await writeFile(target, fresh);
  }
  for (const name of strays) {
    say(`public/art/${name} has no drawing in art/. Take it out, or draw it: every picture is made from a drawing.`);
  }
  if (strays.length > 0 || (check && stale.length > 0)) {
    process.exitCode = 1;
    if (check) return;
  }

  const count = `${drawings.length} ${drawings.length === 1 ? "picture" : "pictures"}`;
  const drawn = stale.filter(({ target }) => target !== list).length;
  const wrote = [
    ...(drawn > 0 ? [`${drawn} of ${count}`] : []),
    ...(stale.length > drawn ? ["src/lib/art/names.ts"] : []),
  ];
  process.stdout.write(
    check || wrote.length === 0
      ? `${count} in public/art and src/lib/art/names.ts are what the drawings in art/ give\n`
      : `Wrote ${wrote.join(" and ")}\n`,
  );
}

const given = process.argv.slice(2);
const at = given.indexOf("--root");
const root =
  at === -1 ? path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..") : path.resolve(given[at + 1] ?? "");

try {
  await run(root, given.includes("--check"));
} catch (fault) {
  if (!(fault instanceof Fault)) throw fault;
  process.stderr.write(`${fault.message}\n`);
  process.exitCode = 1;
}
