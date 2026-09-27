/** @jest-environment node */
/**
 * The two faces of the website. Each is a file of the website's own, in
 * public/fonts with its licence beside it, declared in base.css, and fetched
 * from nowhere else: docs/design/web.md, section 10.
 *
 * A face that is declared wrongly fails without a word: the page is drawn in
 * a face of the system's, or light where heavy was asked, and no test of a
 * page sees it. So the files themselves are read here.
 *
 * Which face a sentence is set in is said in tokens.css and base.css, and may
 * be changed there. Nothing here names it: a face is known by what it is for.
 */

import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { themes } from "./support/contrast";
import { rulesOf } from "./support/css";
import { charactersOf, featuresOf, figuresOf, slants, weightsOf } from "./support/woff2";

const WEB = path.resolve(__dirname, "..");
const SRC = path.join(WEB, "src");
const FONTS = path.join(WEB, "public", "fonts");
const RECORDED = path.join(WEB, "test", "recorded");
const withoutComments = (css: string) => css.replace(/\/\*[\s\S]*?\*\//g, "");
const BASE = withoutComments(readFileSync(path.join(SRC, "styles", "base.css"), "utf8"));

interface Face {
  readonly family: string;
  readonly style: string;
  /** One weight, or the least and the most of those it is declared for. */
  readonly weight: string;
  readonly display: string;
  /** What `src` says, whole. */
  readonly from: string;
  /** The ranges of characters the face is declared for, each as its first and its last. */
  readonly ranges: readonly (readonly [first: number, last: number])[];
}

function rangesOf(written: string): [number, number][] {
  return written
    .split(",")
    .map((range) => range.trim())
    .filter(Boolean)
    .map((range) => {
      const found = /^U\+([0-9A-F]{1,6})(?:-([0-9A-F]{1,6}))?$/.exec(range);
      if (!found) throw new Error(`Not a range of characters: ${range}`);
      const first = parseInt(found[1] ?? "", 16);
      return [first, found[2] === undefined ? first : parseInt(found[2], 16)];
    });
}

/** Every face base.css declares. */
const FACES: readonly Face[] = [...BASE.matchAll(/@font-face\s*\{([^}]*)\}/g)].map(([, block]) => {
  const said = new Map(
    (block ?? "").split(";").flatMap((declaration): [string, string][] => {
      const at = declaration.indexOf(":");
      return at < 0 ? [] : [[declaration.slice(0, at).trim(), declaration.slice(at + 1).trim().replace(/\s+/g, " ")]];
    }),
  );
  return {
    family: (said.get("font-family") ?? "").replace(/^"|"$/g, ""),
    style: said.get("font-style") ?? "",
    weight: said.get("font-weight") ?? "",
    display: said.get("font-display") ?? "",
    from: said.get("src") ?? "",
    ranges: rangesOf(said.get("unicode-range") ?? ""),
  };
});

/** The file a face is fetched from, by its name in public/fonts, or what stands in its place if it is none. */
const fileOf = (face: Face) => /^url\("\/fonts\/([a-z0-9-]+\.woff2)"\) format\("woff2"\)$/.exec(face.from)?.[1] ?? face.from;
const bytesOf = (face: Face) => readFileSync(path.join(FONTS, fileOf(face)));
const first = (stack: string | undefined) => /^"([^"]+)"/.exec(stack ?? "")?.[1] ?? "";
const slug = (family: string) => family.toLowerCase().replace(/\s+/g, "-");
const inFolder = readdirSync(FONTS).sort();
const hashOf = (file: string) => createHash("sha256").update(readFileSync(path.join(FONTS, file))).digest("hex");

/** The weights a face is declared for: the least and the most, which are one where it is declared for one. */
function declaredFor(face: Face): [least: number, most: number] {
  const found = /^(\d+)(?: (\d+))?$/.exec(face.weight);
  if (!found) throw new Error(`Not a weight, nor two: ${face.weight}`);
  return [Number(found[1]), Number(found[2] ?? found[1])];
}

const isDeclaredFor = (face: Face, code: number) => face.ranges.some(([from, to]) => code >= from && code <= to);
const named = (code: number) => `U+${code.toString(16).toUpperCase().padStart(4, "0")}`;

/** Every file under a folder that a test of its own is not, with where it is. */
function filesUnder(folder: string, ending: RegExp): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry): string[] => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return filesUnder(file, ending);
    return ending.test(entry.name) && !/\.test\.tsx?$/.test(entry.name) ? [file] : [];
  });
}

/** Every style sheet of the website, with what is said in comments taken out. */
function styleSheets(): [file: string, css: string][] {
  return filesUnder(SRC, /\.css$/).map((file) => [path.relative(SRC, file), withoutComments(readFileSync(file, "utf8"))]);
}

/** A weight as a style sheet writes one: a figure, one of the two words that stand for one, or a token that holds either. */
function weightOf(written: string): number | null {
  const token = /^var\((--[a-z0-9-]+)\)$/.exec(written)?.[1];
  const said = token === undefined ? written : (themes().light[token] ?? written);
  if (said === "normal") return 400;
  if (said === "bold") return 700;
  return /^\d{1,4}$/.test(said) ? Number(said) : null;
}

interface Asked {
  readonly where: string;
  /** The weight the rule asks for, or what it wrote where that is no weight this can weigh. */
  readonly weight: number | string | null;
  readonly slanted: boolean;
}

/**
 * What every rule of every style sheet asks of a face: a weight, a slant, or both. A rule
 * that writes `font` whole asks for both, and for the plain ones where it names none.
 */
function asked(): Asked[] {
  return styleSheets().flatMap(([file, css]) =>
    rulesOf(css).flatMap((rule): Asked[] => {
      const whole = rule.sets.get("font");
      const weight = rule.sets.get("font-weight");
      const slant = rule.sets.get("font-style");
      const found: { weight: Asked["weight"]; slanted: boolean }[] = [];
      if (whole !== undefined && !/^(inherit|initial|unset|revert)$/.test(whole)) {
        // What stands before the size, which is the first part that is a token, a sum or a figure with its unit.
        const parts = whole.split(/\s+/);
        const size = parts.findIndex((part) => /^(var\(|calc\(|\d*\.?\d+[a-z%]+)/.test(part));
        const before = parts.slice(0, Math.max(size, 0));
        found.push({ weight: before.map(weightOf).find((one) => one !== null) ?? 400, slanted: before.includes("italic") });
      }
      if (weight !== undefined || slant !== undefined) {
        found.push({
          weight: weight === undefined || weight === "inherit" ? (found[0]?.weight ?? null) : (weightOf(weight) ?? weight),
          slanted: slant === undefined ? (found[0]?.slanted ?? false) : slant === "italic" || slant === "oblique",
        });
      }
      return found.map((one) => ({ where: `${file}: ${rule.selector}`, ...one }));
    }),
  );
}

/** Every character of a text. One that the code writes by its number, after a stroke and a u, is read as itself. */
function charactersIn(text: string): Set<number> {
  const read = text.replace(/\\u\{([0-9a-fA-F]+)\}|\\u([0-9a-fA-F]{4})/g, (_, long: string | undefined, short: string | undefined) =>
    String.fromCodePoint(parseInt(long ?? short ?? "", 16)),
  );
  return new Set([...read].map((character) => character.codePointAt(0) ?? 0));
}

/** Every word of an answer: what it holds under each name, and never the names. */
function wordsOf(answer: unknown): string[] {
  if (typeof answer === "string") return [answer];
  if (Array.isArray(answer)) return answer.flatMap(wordsOf);
  if (typeof answer === "object" && answer !== null) return Object.values(answer).flatMap(wordsOf);
  return typeof answer === "number" ? [String(answer)] : [];
}

describe("the two faces", () => {
  const { light } = themes();
  const NAME = first(light["--font-name"]);
  const SAY = first(light["--font-say"]);

  /** What a face is for, which is how it is known here. */
  const forWhat = (face: Face) => (face.family === NAME ? "a name" : face.family === SAY ? "a sentence" : "nothing");
  const OF_A_SENTENCE = FACES.filter((face) => forWhat(face) === "a sentence");

  test("test_there_are_two_faces_and_no_third", () => {
    // The face of a name is drawn in pixels. The face of a sentence is another, and plain.
    expect(NAME).toBe("Jersey 10");
    expect([SAY === "", SAY === NAME]).toEqual([false, false]);
    expect([...new Set(FACES.map((face) => face.family))].sort()).toEqual([NAME, SAY].sort());
    // A name has one weight and stands upright.
    expect(FACES.filter((face) => face.family === NAME).map(({ style, weight }) => `${weight} ${style}`)).toEqual([
      "400 normal",
      "400 normal",
    ]);
    // A sentence may be heavy, at any weight from 400 to 700, which one file holds. Or
    // slanted, at 400: each is declared once, so that no weight and no slant has two files.
    expect(OF_A_SENTENCE.map(({ style, weight }) => `${weight} ${style}`).sort()).toEqual(["400 700 normal", "400 italic"]);
  });

  test("test_every_face_is_a_file_of_the_websites_own_and_every_file_is_declared", () => {
    const declared = FACES.map(fileOf).sort();

    expect(FACES.length).toBeGreaterThan(0);
    // Each is fetched from /fonts/ of the website's own origin, by a path and never an address.
    expect(declared.filter((file) => !/^[a-z0-9-]+\.woff2$/.test(file))).toEqual([]);
    expect(declared).toEqual(inFolder.filter((name) => name.endsWith(".woff2")));
    expect(new Set(declared).size).toBe(declared.length);
    // A file says in its name whose it is, whether it slants, and which weight it holds
    // where it holds one alone and the face has others. A file of every weight names none.
    expect(FACES.filter((face) => !fileOf(face).startsWith(`${slug(face.family)}-`)).map(fileOf)).toEqual([]);
    expect(FACES.filter((face) => fileOf(face).includes("-italic-") !== (face.style === "italic")).map(fileOf)).toEqual([]);
    for (const face of FACES) {
      const others = FACES.filter((other) => other.family === face.family && other.weight !== face.weight);
      const [least, most] = declaredFor(face);
      const says = new RegExp(`^${slug(face.family)}-${least}-`).test(fileOf(face));
      expect([fileOf(face), says]).toEqual([fileOf(face), others.length > 0 && least === most]);
    }
  });

  test("test_nothing_waits_on_a_face_and_a_file_is_fetched_only_for_the_characters_it_is_declared_for", () => {
    expect(FACES.filter((face) => face.display !== "swap").map(fileOf)).toEqual([]);
    expect(FACES.filter((face) => face.ranges.length === 0).map(fileOf)).toEqual([]);
  });

  test("test_the_characters_a_file_holds_are_the_ones_it_is_declared_for", () => {
    // A file declared for the wrong characters is fetched and never drawn, or never fetched:
    // the two files of a face, each declared for the other's, would draw nothing. A file
    // holds a few characters more than it is declared for, which the letters it is declared
    // for are built from: a plain A and an accent, in the file of the accented letters. They
    // are 7 of its 121. So nine in ten is asked, and a file that is another's has none.
    for (const face of FACES) {
      const held = charactersOf(bytesOf(face));
      const declared = held.filter((code) => isDeclaredFor(face, code));

      expect([fileOf(face), held.length > 100]).toEqual([fileOf(face), true]);
      expect([fileOf(face), declared.length / held.length > 0.9]).toEqual([fileOf(face), true]);
    }
  });

  test("test_every_letter_and_figure_of_a_sentence_in_english_is_in_both_faces_at_every_weight", () => {
    const needed = [..."ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,:;?'\"()-/%&+£’‘“”–"];
    const ofEnglish = FACES.filter((face) => isDeclaredFor(face, 0));
    const lacking = ofEnglish.flatMap((face) => {
      const held = new Set(charactersOf(bytesOf(face)));
      return needed.filter((character) => !held.has(character.codePointAt(0) ?? 0)).map((character) => `${fileOf(face)} ${character}`);
    });

    // One file for a name. Two for a sentence: upright, which is every weight of it, and slanted.
    expect(ofEnglish.map(forWhat)).toEqual(["a name", "a sentence", "a sentence"]);
    expect(lacking).toEqual([]);
  });

  test("test_every_figure_is_set_in_the_face_of_a_sentence_so_it_holds_what_a_measure_is_written_with", () => {
    // The service writes a measure as micrograms to the cubic metre, and an area in square
    // metres. A character the face lacks is drawn in a face of the system's, in the middle
    // of a figure. So it holds the pound, the per cent and the degree, a minus that is no
    // hyphen, the sign of multiplication, a half, the micro sign, and a two and a three set high.
    const needed = [..."£%°−×½µ²³"];
    // It holds no two set low, as the two of a gas is written, and no file of it is declared
    // for one: a browser draws it in the next face of the stack. Nothing that is shown holds
    // one today, which the next test sees to. Were one to be, it is known here first.
    const lacked = [..."₂"];

    expect(OF_A_SENTENCE).toHaveLength(2);
    for (const face of OF_A_SENTENCE) {
      const held = new Set(charactersOf(bytesOf(face)));
      const drawn = (character: string) => held.has(character.codePointAt(0) ?? 0) && isDeclaredFor(face, character.codePointAt(0) ?? 0);

      expect([fileOf(face), needed.filter((character) => !drawn(character))]).toEqual([fileOf(face), []]);
      expect([fileOf(face), lacked.filter(drawn)]).toEqual([fileOf(face), []]);
    }
  });

  test("test_every_character_the_service_and_the_website_write_is_in_the_face_of_a_sentence", () => {
    // What the service answered, as it was recorded, and what the website says of its own:
    // its copy and what its parts write between their tags. A character of either that the
    // face lacks, or is not declared for, is drawn in a face of the system's beside one that
    // is not. What a person types is theirs, and may be in any script.
    const answered = filesUnder(RECORDED, /\.json$/).flatMap((file) => {
      const words = wordsOf(JSON.parse(readFileSync(file, "utf8")));
      return [...charactersIn(words.join(" "))].map((code) => [code, path.relative(WEB, file)] as const);
    });
    const written = filesUnder(SRC, /\.tsx?$/).flatMap((file) => {
      // What is said to whoever reads the code is drawn on no page. An address holds two
      // strokes too, with no gap before them, and is left as it is.
      const source = readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|\s)\/\/.*$/gm, "");
      return [...charactersIn(source)].map((code) => [code, path.relative(WEB, file)] as const);
    });
    // A gap and the end of a line are drawn by no face.
    const shown = [...answered, ...written].filter(([code]) => code > 0x20);

    expect(answered.length).toBeGreaterThan(1000);
    expect(written.length).toBeGreaterThan(1000);
    // The pound, the micro sign and the three set high are all written today, so what is read
    // here is what is written. The two set high is not: the service writes an area out, as a
    // square kilometre. The face holds it all the same, which the test before this one sees to.
    expect([..."£µ³"].filter((character) => !answered.some(([code]) => code === character.codePointAt(0)))).toEqual([]);
    for (const face of OF_A_SENTENCE) {
      const held = new Set(charactersOf(bytesOf(face)));
      const lacking = shown.filter(([code]) => !held.has(code) || !isDeclaredFor(face, code));
      const once = [...new Map(lacking.map(([code, file]) => [code, `${named(code)} in ${file}`])).values()];

      expect([fileOf(face), once]).toEqual([fileOf(face), []]);
    }
  });

  test("test_a_file_holds_every_weight_it_is_declared_for_and_slants_where_it_is_declared_to", () => {
    // A browser is told which weights a file holds and believes it. A file of one weight
    // that is declared for many is drawn as it is where heavy is asked, and no browser makes
    // it heavier: it was told the file is heavy already. So a heavy word is drawn light,
    // and nothing says so. A file that is declared for fewer weights than it holds is safe.
    for (const face of FACES) {
      const [least, most] = weightsOf(bytesOf(face));
      const [from, to] = declaredFor(face);

      expect([fileOf(face), `${from} to ${to}`, least <= from && to <= most]).toEqual([fileOf(face), `${from} to ${to}`, true]);
      // An upright file that is declared slanted is slanted again by the browser, and a
      // slanted one that is declared upright sets every sentence of the website aslant.
      expect([fileOf(face), slants(bytesOf(face))]).toEqual([fileOf(face), face.style === "italic"]);
    }
    // The file of every weight holds more than the website asks of it, at either end.
    expect(OF_A_SENTENCE.map((face) => [face.style, ...weightsOf(bytesOf(face))])).toEqual([
      ["normal", 300, 900],
      ["italic", 400, 400],
    ]);
  });

  test("test_a_sentence_is_declared_for_the_weights_the_style_sheets_ask_and_for_no_other", () => {
    const all = asked();
    const weights = all.flatMap(({ weight }) => (typeof weight === "number" ? [weight] : []));
    const upright = OF_A_SENTENCE.filter((face) => face.style === "normal").map(declaredFor);
    const slanted = OF_A_SENTENCE.filter((face) => face.style === "italic").map(declaredFor);

    // A weight is asked as a figure, or as one of the two words that stand for one. What is
    // asked as heavier or lighter than what is round it cannot be held to a face by reading.
    expect(all.filter(({ weight }) => typeof weight === "string").map(({ where, weight }) => `${where}: ${weight}`)).toEqual([]);
    expect(weights.length).toBeGreaterThan(100);
    // The website asks for weights between the plain and the heavy, and is drawn at each.
    expect([...new Set(weights)].filter((weight) => weight > 400 && weight < 700).length).toBeGreaterThan(0);
    // The face is declared for the least and the most that is asked, and no further. What is
    // asked past either end is drawn at that end: the heavy word inside a heavy line, which a
    // browser asks at 900, is drawn at 700 and no blacker than the heading over it.
    expect(upright).toEqual([[Math.min(...weights), Math.max(...weights)]]);
    expect(upright).toEqual([[400, 700]]);

    // A slanted word is asked plain. Where a rule slants and says a weight, it is one the
    // slanted file holds: a heavier one is the plain one smeared by the browser. What a
    // slanted word takes from what is round it no reading of a style sheet sees. It was seen
    // in a browser on 2026-09-26, on every page with all of it open: no slanted word was heavy.
    const [[least, most] = [0, 0]] = slanted;
    const smeared = all.filter(({ slanted: is, weight }) => is && typeof weight === "number" && (weight < least || weight > most));

    expect(slanted).toEqual([[400, 400]]);
    expect(all.filter(({ slanted: is }) => is).length).toBeGreaterThan(0);
    expect(smeared.map(({ where, weight }) => `${where}: ${weight}`)).toEqual([]);
  });

  test("test_a_figure_in_a_table_stands_under_the_figure_above_it", () => {
    // The face draws a one narrower than a nought, as a sentence wants it: so the figures of
    // a column would not stand under one another. It holds ten more that are of one width,
    // and a style sheet asks for them. A table asks, whatever it is a table of.
    const table = rulesOf(BASE).filter((rule) => rule.selector === "table" && rule.under === null);

    expect(table.flatMap((rule) => rule.sets.get("font-variant-numeric") ?? [])).toEqual(["tabular-nums"]);
    for (const face of OF_A_SENTENCE) {
      const file = bytesOf(face);
      const asTheyCome = new Set(figuresOf(file).map((figure) => figure.join(" ")));
      const ofOneWidth = new Set(figuresOf(file, "tnum").map((figure) => figure.join(" ")));

      expect([fileOf(face), featuresOf(file).includes("tnum")]).toEqual([fileOf(face), true]);
      expect([fileOf(face), asTheyCome.size > 1]).toEqual([fileOf(face), true]);
      // Of one width at rest, and what is added as the file grows heavy is the same for
      // all ten: so they are of one width at every weight the file holds.
      expect([fileOf(face), ofOneWidth.size]).toEqual([fileOf(face), 1]);
    }

    // What is read of a file here was held against another reader of such files, which read
    // the same of every file of the website and of the two faces before this one. Of a
    // thousand to the size of the type: a nought and a one as they come, at the lightest the
    // upright file holds, with what each has grown by at its heaviest. Then a figure of one
    // width, which the browser draws 619 wide at 400 and 663 at 700, measured on a page.
    const [upright] = OF_A_SENTENCE.filter((face) => face.style === "normal").map(bytesOf);
    const [slanted] = OF_A_SENTENCE.filter((face) => face.style === "italic").map(bytesOf);
    if (upright === undefined || slanted === undefined) throw new Error("A sentence has no file that stands upright, or none that slants.");

    expect(figuresOf(upright).slice(0, 2)).toEqual([[616, 102], [398, 159]]);
    expect(figuresOf(upright, "tnum")[0]).toEqual([600, 100]);
    // The slanted file holds one weight, so nothing is added to a figure of it.
    expect(figuresOf(slanted, "tnum")[0]).toEqual([619]);
  });

  test("test_a_face_is_never_changed_under_its_name", () => {
    // A browser is told to keep a face for a year and not to ask for it again, by the name
    // of its file: lib/headers.ts. So a file whose bytes change is given a new name, and a
    // name that was served is never given to other bytes. If this fails, a file was changed
    // under its name, or a sentence is set in another face: name the file anew in base.css,
    // and say here what it holds. A line whose name stays is never given another hash.
    const AS_IT_WAS = {
      "a name, 400 normal, from U+0000, as latin.woff2": "c7ea08dca3e711a1e30c3d8faec7e2a50c08f32cfbc0f01f38e456cfdd11983b",
      "a name, 400 normal, from U+0100, as latin-ext.woff2": "da0724005aa9e5d863d736c27ce7c7b76e1469f174b86f241566eefaa1cf5d5e",
      "a sentence, 400 700 normal, from U+0000, as latin.woff2": "99ec7ccb40cf143f977c893649deece6cc2dcc7c0ff82ebf84b6584090f207ea",
      "a sentence, 400 italic, from U+0000, as 400-italic-latin.woff2": "b20df5e71ed67044c6f45b461f610044f924b7bdc6ec93cb92bf58460624a10b",
    };
    const from = (face: Face) => named(face.ranges[0]?.[0] ?? -1);
    /** What is left of the name of a file without the name of its face. */
    const rest = (face: Face) => fileOf(face).slice(slug(face.family).length + 1);
    const asItIs = Object.fromEntries(
      FACES.map((face) => [`${forWhat(face)}, ${face.weight} ${face.style}, from ${from(face)}, as ${rest(face)}`, hashOf(fileOf(face))]),
    );

    expect(asItIs).toEqual(AS_IT_WAS);
    // No two are one file under two names.
    expect(new Set(Object.values(asItIs)).size).toBe(FACES.length);
  });

  test("test_the_licence_of_each_face_stands_beside_it", () => {
    const families = [...new Set(FACES.map((face) => face.family))];

    for (const family of families) {
      const licence = readFileSync(path.join(FONTS, `OFL-${slug(family)}.txt`), "utf8");
      const [notice = ""] = licence.split("SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007");
      // Who drew it, and the licence whole: it asks to be kept with every copy of the face.
      expect([family, /^Copyright /.test(licence)]).toEqual([family, true]);
      expect(licence).toContain("SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007");
      expect(licence).toContain("PERMISSION & CONDITIONS");
      expect(licence).toContain("TERMINATION");
      expect(licence).toContain("DISCLAIMER");
      // A file here is the face cut to the characters of one script, and is served under
      // the name of the face. The licence lets a face that was changed bear its name unless
      // those who drew it kept the name for the face as they drew it, which their notice
      // would say. Neither notice does.
      expect([family, notice.length > 0 && notice.length < licence.length, /reserved font name/i.test(notice)]).toEqual([family, true, false]);
    }
    // The folder holds the faces and their licences, and nothing else.
    expect(inFolder.filter((name) => !name.endsWith(".woff2"))).toEqual(families.map((family) => `OFL-${slug(family)}.txt`).sort());
  });

  test("test_no_style_sheet_fetches_anything_from_another_origin", () => {
    // What a style sheet fetches is named by a path from the root of the website: a face
    // under /fonts/, a drawing under /art/. An address, or a sheet taken in from elsewhere,
    // would be another origin's, and the policy would stop it where a test had not.
    const fetched = styleSheets().flatMap(([file, css]) =>
      [...css.matchAll(/url\(\s*(["']?)([^"')]*)\1\s*\)/g)].map(([, , from]) => [file, from ?? ""] as const),
    );

    expect(fetched.filter(([, from]) => !/^\/(fonts|art)\/[a-z0-9-]+\.(woff2|png)$/.test(from))).toEqual([]);
    expect(styleSheets().filter(([, css]) => /@import/.test(css)).map(([file]) => file)).toEqual([]);
    expect(fetched.filter(([, from]) => from.startsWith("/fonts/")).map(([file]) => file)).toEqual(
      FACES.map(() => "styles/base.css"),
    );
  });
});
