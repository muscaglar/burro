/**
 * Reads what a test needs to know of a font file: which characters it holds,
 * which weights, whether its letters slant, and how wide it draws a figure.
 * The file is a WOFF2: a list of tables, and the tables themselves packed as
 * one. Node unpacks it, so no package is asked for.
 *
 * A table is read as it is written in every such file. One that is kept in
 * another form, as the outlines are, is stepped over by its length, and
 * nothing here reads an outline. How wide each drawing is may be kept in
 * another form too, and is read in both.
 *
 * A file may hold one weight, or every weight between two. Which character is
 * which drawing is the same at every weight of a file. How wide a drawing is
 * is not: a file of many weights says how wide each is at rest, and what is
 * added to that as it grows heavy.
 */

import { brotliDecompressSync } from "node:zlib";

/** The names of the tables that a file gives by number, in the order the format numbers them. */
const KNOWN = [
  "cmap", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post", "cvt ", "fpgm", "glyf", "loca", "prep", "CFF ", "VORG", "EBDT",
  "EBLC", "gasp", "hdmx", "kern", "LTSH", "PCLT", "VDMX", "vhea", "vmtx", "BASE", "GDEF", "GPOS", "GSUB", "EBSC", "JSTF", "MATH",
  "CBDT", "CBLC", "COLR", "CPAL", "SVG ", "sbix", "acnt", "avar", "bdat", "bloc", "bsln", "cvar", "fdsc", "feat", "fmtx", "fvar",
  "gvar", "hsty", "just", "lcar", "mort", "morx", "opbd", "prop", "trak", "Zapf", "Silf", "Glat", "Gloc", "Feat", "Sill",
] as const;

/** One table of the file: where it lies once the tables are unpacked, and whether it is kept in another form. */
interface Table {
  readonly from: number;
  readonly length: number;
  readonly changed: boolean;
}

function tablesOf(file: Buffer): { tables: Map<string, Table>; packed: Buffer } {
  if (file.toString("latin1", 0, 4) !== "wOF2") throw new Error("Not a WOFF2 file.");
  const count = file.readUInt16BE(12);
  const packedLength = file.readUInt32BE(20);
  let at = 48;
  /** A number written in as many bytes as it needs, seven bits to a byte. */
  const number = (): number => {
    let value = 0;
    for (let byte = 0; byte < 5; byte += 1) {
      const next = file.readUInt8(at);
      at += 1;
      value = value * 128 + (next & 0x7f);
      if ((next & 0x80) === 0) return value;
    }
    throw new Error("A length in the file is longer than a length may be.");
  };

  const tables = new Map<string, Table>();
  let from = 0;
  for (let table = 0; table < count; table += 1) {
    const flags = file.readUInt8(at);
    at += 1;
    let name: string = KNOWN[flags & 0x3f] ?? "";
    if ((flags & 0x3f) === 0x3f) {
      name = file.toString("latin1", at, at + 4);
      at += 4;
    }
    const form = flags >> 6;
    const whole = number();
    // The outlines and where each begins are kept in another form unless they say they are
    // not. Every other table is kept as it is unless it says it is not.
    const kept = name === "glyf" || name === "loca" ? form === 3 : form === 0;
    const length = kept ? whole : number();
    tables.set(name, { from, length, changed: !kept });
    from += length;
  }
  return { tables, packed: file.subarray(at, at + packedLength) };
}

interface Opened {
  /** A table by its name, or nothing where the file has none of that name. */
  readonly table: (name: string) => Buffer | undefined;
  /** A table the file cannot be read without. */
  readonly need: (name: string) => Buffer;
  /** True where a table is kept in another form than it is written in. */
  readonly changed: (name: string) => boolean;
}

/** A file is unpacked once, however often it is asked of. */
const UNPACKED = new WeakMap<Buffer, Opened>();

function opened(file: Buffer): Opened {
  const before = UNPACKED.get(file);
  if (before !== undefined) return before;
  const { tables, packed } = tablesOf(file);
  const whole = brotliDecompressSync(packed);
  const table = (name: string) => {
    const where = tables.get(name);
    return where === undefined ? undefined : whole.subarray(where.from, where.from + where.length);
  };
  const now: Opened = {
    table,
    need: (name) => {
      const found = table(name);
      if (found === undefined) throw new Error(`The file has no table named ${name.trim()}.`);
      return found;
    },
    changed: (name) => tables.get(name)?.changed ?? false,
  };
  UNPACKED.set(file, now);
  return now;
}

/** Which drawing each character has, by the fullest list the file holds. */
function drawingsOf(file: Buffer): Map<number, number> {
  const { table } = opened(file);
  const cmap = table("cmap");
  if (cmap === undefined) throw new Error("The file does not say which character is which drawing.");

  // The fullest list the file holds: one that goes beyond the first 65,536 where there is one.
  const lists = Array.from({ length: cmap.readUInt16BE(2) }, (_, list) => cmap.readUInt32BE(4 + list * 8 + 4));
  const formats = lists.map((list) => cmap.readUInt16BE(list));
  const chosen = lists[formats.indexOf(12)] ?? lists[formats.indexOf(4)];
  if (chosen === undefined) throw new Error("The file lists its characters in a way this does not read.");

  const found = new Map<number, number>();
  if (cmap.readUInt16BE(chosen) === 12) {
    const groups = cmap.readUInt32BE(chosen + 12);
    for (let group = 0; group < groups; group += 1) {
      const start = cmap.readUInt32BE(chosen + 16 + group * 12);
      const end = cmap.readUInt32BE(chosen + 20 + group * 12);
      const first = cmap.readUInt32BE(chosen + 24 + group * 12);
      for (let code = start; code <= end; code += 1) found.set(code, first + (code - start));
    }
    return found;
  }

  const parts = cmap.readUInt16BE(chosen + 6) / 2;
  const ends = chosen + 14;
  const starts = ends + parts * 2 + 2;
  const deltas = starts + parts * 2;
  const offsets = deltas + parts * 2;
  for (let part = 0; part < parts; part += 1) {
    const start = cmap.readUInt16BE(starts + part * 2);
    const end = cmap.readUInt16BE(ends + part * 2);
    const delta = cmap.readUInt16BE(deltas + part * 2);
    const offset = cmap.readUInt16BE(offsets + part * 2);
    for (let code = start; code <= end && code !== 0xffff; code += 1) {
      const written = offset === 0 ? code : cmap.readUInt16BE(offsets + part * 2 + offset + (code - start) * 2);
      // Nought, where it is written out, is the drawing of a character the file lacks.
      const drawing = offset !== 0 && written === 0 ? 0 : (written + delta) & 0xffff;
      if (drawing !== 0) found.set(code, drawing);
    }
  }
  return found;
}

/** Every character the file has a drawing for, in order. */
export function charactersOf(file: Buffer): number[] {
  return [...drawingsOf(file).keys()].sort((one, other) => one - other);
}

/** A number with a fraction, as a file writes one: sixteen bits of each. */
const fraction = (table: Buffer, at: number) => table.readInt32BE(at) / 65536;

/**
 * The weights a file holds: the least and the most. A file of one weight holds that one
 * alone, and says which. A file of many says between which two it can be drawn, and a
 * browser draws it at any weight between them.
 */
export function weightsOf(file: Buffer): readonly [least: number, most: number] {
  const { table, need } = opened(file);
  const ways = table("fvar");
  if (ways !== undefined) {
    const first = ways.readUInt16BE(4);
    const count = ways.readUInt16BE(8);
    const size = ways.readUInt16BE(10);
    for (let way = 0; way < count; way += 1) {
      const at = first + way * size;
      if (ways.toString("latin1", at, at + 4) === "wght") return [fraction(ways, at + 4), fraction(ways, at + 12)];
    }
  }
  const weight = need("OS/2").readUInt16BE(4);
  return [weight, weight];
}

/** True where the letters of a file slant: it says at what angle, and that it is italic. */
export function slants(file: Buffer): boolean {
  const { need } = opened(file);
  return fraction(need("post"), 4) !== 0 || (need("OS/2").readUInt16BE(62) & 1) === 1;
}

/** What a file can do to a run of drawings when a style sheet asks: each by its four letters, in order. */
export function featuresOf(file: Buffer): string[] {
  const { table } = opened(file);
  const changes = table("GSUB");
  if (changes === undefined) return [];
  const list = changes.readUInt16BE(6);
  const count = changes.readUInt16BE(list);
  const found = Array.from({ length: count }, (_, at) => changes.toString("latin1", list + 2 + at * 6, list + 6 + at * 6));
  return [...new Set(found)].sort();
}

/** Every drawing a list of them covers, in the order the list counts them. */
function coveredBy(table: Buffer, list: number): number[] {
  const count = table.readUInt16BE(list + 2);
  if (table.readUInt16BE(list) === 1) return Array.from({ length: count }, (_, at) => table.readUInt16BE(list + 4 + at * 2));
  return Array.from({ length: count }, (_, range) => {
    const start = table.readUInt16BE(list + 4 + range * 6);
    const end = table.readUInt16BE(list + 6 + range * 6);
    return Array.from({ length: end - start + 1 }, (_, at) => start + at);
  }).flat();
}

/** What a feature puts in place of what, where it puts one drawing in place of one. */
function putInPlaceBy(file: Buffer, feature: string): Map<number, number> {
  const { table } = opened(file);
  const changes = table("GSUB");
  const found = new Map<number, number>();
  if (changes === undefined) return found;
  const features = changes.readUInt16BE(6);
  const lookups = changes.readUInt16BE(8);

  const asked = Array.from({ length: changes.readUInt16BE(features) }, (_, at) => features + 2 + at * 6)
    .filter((record) => changes.toString("latin1", record, record + 4) === feature)
    .flatMap((record) => {
      const one = features + changes.readUInt16BE(record + 4);
      return Array.from({ length: changes.readUInt16BE(one + 2) }, (_, at) => changes.readUInt16BE(one + 4 + at * 2));
    });

  for (const index of new Set(asked)) {
    const lookup = lookups + changes.readUInt16BE(lookups + 2 + index * 2);
    const kind = changes.readUInt16BE(lookup);
    for (let part = 0; part < changes.readUInt16BE(lookup + 4); part += 1) {
      let at = lookup + changes.readUInt16BE(lookup + 6 + part * 2);
      let is = kind;
      // A part may say only where the part itself lies, further on in the table.
      if (is === 7) {
        is = changes.readUInt16BE(at + 2);
        at += changes.readUInt32BE(at + 4);
      }
      if (is !== 1) throw new Error(`The file does what ${feature} asks in a way this does not read.`);
      const covered = coveredBy(changes, at + changes.readUInt16BE(at + 2));
      if (changes.readUInt16BE(at) === 1) {
        const by = changes.readInt16BE(at + 4);
        for (const drawing of covered) found.set(drawing, (drawing + by) & 0xffff);
      } else {
        covered.forEach((drawing, place) => found.set(drawing, changes.readUInt16BE(at + 6 + place * 2)));
      }
    }
  }
  return found;
}

/** How wide every drawing is at rest, in the units of the file. */
function widthsAtRest(file: Buffer): number[] {
  const { need, changed } = opened(file);
  const counted = need("hhea").readUInt16BE(34);
  const drawings = need("maxp").readUInt16BE(4);
  const widths = need("hmtx");
  // As it is written, a width is followed by where the drawing begins. Kept in another
  // form, one byte says what is left out, and the widths follow it one after another.
  const [first, step] = changed("hmtx") ? [1, 2] : [0, 4];
  const given = Array.from({ length: counted }, (_, at) => widths.readUInt16BE(first + at * step));
  // The drawings after the last that is given a width are as wide as it is.
  return Array.from({ length: drawings }, (_, drawing) => given[drawing] ?? given[counted - 1] ?? 0);
}

/**
 * What is added to the width of a drawing as the file is drawn away from rest: one figure
 * for each way the file says it can change. None, where the file holds one weight.
 */
function growthOf(file: Buffer): (drawing: number) => number[] {
  const { table } = opened(file);
  const grows = table("HVAR");
  if (grows === undefined) {
    if (table("fvar") !== undefined) throw new Error("The file says how its widths change in a way this does not read.");
    return () => [];
  }
  const store = grows.readUInt32BE(4);
  const map = grows.readUInt32BE(8);
  const ways = grows.readUInt16BE(store + grows.readUInt32BE(store + 2) + 2);
  const sets = grows.readUInt16BE(store + 6);

  /** Which row of which set is a drawing's. Where the file does not say, the first set, by the number of the drawing. */
  const rowOf = (drawing: number): [set: number, row: number] => {
    if (map === 0) return [0, drawing];
    const long = grows.readUInt8(map) === 1;
    const form = grows.readUInt8(map + 1);
    const count = long ? grows.readUInt32BE(map + 2) : grows.readUInt16BE(map + 2);
    const size = ((form & 0x30) >> 4) + 1;
    const inner = 2 ** ((form & 0x0f) + 1);
    // A drawing past the last that is listed has the row of the last.
    const entry = grows.readUIntBE(map + (long ? 6 : 4) + Math.min(drawing, count - 1) * size, size);
    return [Math.floor(entry / inner), entry % inner];
  };

  return (drawing) => {
    const added: number[] = Array.from({ length: ways }, () => 0);
    const [set, row] = rowOf(drawing);
    if (set >= sets) return added;
    const at = store + grows.readUInt32BE(store + 8 + set * 4);
    const rows = grows.readUInt16BE(at);
    const words = grows.readUInt16BE(at + 2);
    const count = grows.readUInt16BE(at + 4);
    if (row >= rows) return added;
    // The first figures of a row are written long and the rest short, and a set may say that both are twice as long.
    const [long, short] = (words & 0x8000) === 0 ? [2, 1] : [4, 2];
    const written = words & 0x7fff;
    let next = at + 6 + count * 2 + row * (written * long + (count - written) * short);
    for (let place = 0; place < count; place += 1) {
      const size = place < written ? long : short;
      added[grows.readUInt16BE(at + 6 + place * 2)] = grows.readIntBE(next, size);
      next += size;
    }
    return added;
  };
}

/**
 * How wide the file draws each of the ten figures, nought to nine: as it draws a figure
 * where nothing is asked of it, or as it draws one where a style sheet asks for a feature,
 * as `font-variant-numeric: tabular-nums` asks for `tnum`.
 *
 * Each is its width at rest, in the units of the file, and then what is added to it as the
 * file is drawn away from rest. Two figures that are given the same are of one width at
 * every weight the file holds.
 */
export function figuresOf(file: Buffer, feature?: string): number[][] {
  const drawings = drawingsOf(file);
  const inPlace = feature === undefined ? new Map<number, number>() : putInPlaceBy(file, feature);
  const atRest = widthsAtRest(file);
  const grows = growthOf(file);
  return [..."0123456789"].map((figure) => {
    const plain = drawings.get(figure.codePointAt(0) ?? 0);
    if (plain === undefined) throw new Error(`The file has no drawing of the figure ${figure}.`);
    const drawing = inPlace.get(plain) ?? plain;
    return [atRest[drawing] ?? 0, ...grows(drawing)];
  });
}
