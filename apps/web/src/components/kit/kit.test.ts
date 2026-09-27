/** @jest-environment node */
/**
 * What every part of the kit is held to, read from the files of the kit. It holds whatever
 * part is written next as well as the ones that are there.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { contrast, roundedDown, themes } from "../../../test/support/contrast";
import { rulesOf, type Rule } from "../../../test/support/css";
import { isDrawn } from "./drawings";

const KIT = __dirname;

/** The parts of the kit, each by the name a page takes it by: a page that names one must find it. */
const PARTS = [
  "Art",
  "Frame",
  "Press",
  "Pennant",
  "Ends",
  "Thing",
  "Label",
  "Peg",
  "Gauge",
  "Note",
  "Approx",
  "Burro",
] as const;

/** The seventeen colours of the look, by the names and the values the look gives them. */
const SEVENTEEN: Readonly<Record<string, string>> = {
  "--ink": "#2a2140",
  "--page": "#f7f1de",
  "--lea": "#dbe8b1",
  "--sand": "#e9cf94",
  "--meadow": "#a8d85e",
  "--verge": "#63b34a",
  "--hedge": "#2b7a5a",
  "--shallows": "#86dde2",
  "--haven": "#2f9fd0",
  "--cobalt": "#3453d1",
  "--amber": "#f6b426",
  "--poppy": "#db533b",
  "--heath": "#b87bc6",
  "--fur": "#9b8a7f",
  "--shade": "#65566a",
  "--slate": "#6d7fa6",
  "--earth": "#a9683d",
};

/** What the look adds to the tokens beside its colours: the faces, the art pixel, the box and the lengths of movement. */
const OF_THE_LOOK = [
  ...["--font-name", "--font-say", "--name-1", "--name-2", "--name-3", "--name-4"],
  ...["--px", "--px-stage", "--edge"],
  ...["--frame-box", "--frame-box-on", "--frame-box-cut", "--frame-box-wide", "--frame-box-out", "--box-shadow"],
  ...["--motion-hop", "--motion-drop"],
];


/**
 * The drawings the kit names itself, each of which was promised by that name. A vibe, a
 * family and an end of a scale are drawn by rule, by the name the service gives them, and
 * are not written here or anywhere in the kit.
 */
const NAMED = [
  ...["burro-hops", "burro-sits", "burro-waits"],
  ...["gauge-cell", "gauge-cell-full"],
  "key-blank",
  ...["thing-alike", "thing-area", "thing-budget", "thing-home", "thing-journey", "thing-plain", "thing-tenure", "thing-usual"],
  ...["ui-button", "ui-button-go", "ui-button-on", "ui-button-stop"],
  ...["ui-button-down", "ui-button-go-down", "ui-button-on-down", "ui-button-stop-down"],
  ...["ui-approx", "ui-cross", "ui-flag", "ui-key", "ui-peg", "ui-weight"],
];

type Found = Rule & { readonly file: string };

const folders = readdirSync(KIT, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);
const filesOf = (kept: (name: string) => boolean) =>
  folders.flatMap((folder) =>
    readdirSync(path.join(KIT, folder))
      .filter(kept)
      .map((name) => path.join(folder, name)),
  );
const sheets = filesOf((name) => name.endsWith(".module.css")).sort();
const scripts = [
  ...filesOf((name) => /\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name)),
  ...readdirSync(KIT).filter((name) => /\.ts$/.test(name) && !/\.test\.ts$/.test(name)),
].sort();
const read = (file: string) => readFileSync(path.join(KIT, file), "utf8");
const written = (file: string) => read(file).replace(/\/\*[\s\S]*?\*\//g, "");
const RULES: readonly Found[] = sheets.flatMap((file) => rulesOf(written(file)).map((rule) => ({ ...rule, file })));
const where = (rule: Found) => `${rule.file}: ${rule.selector}`;
const FORCED = /forced-colors/;

/** A value parted where it has a comma, or a gap, that is not inside brackets. */
function partsOf(value: string, at: "," | " "): string[] {
  const found: string[] = [];
  let depth = 0;
  let from = 0;
  const text = value.replace(/\s+/g, " ").trim();
  [...text].forEach((character, index) => {
    if (character === "(") depth += 1;
    if (character === ")") depth -= 1;
    if (character === at && depth === 0) {
      found.push(text.slice(from, index));
      from = index + 1;
    }
  });
  found.push(text.slice(from));
  return found.map((part) => part.trim()).filter(Boolean);
}

/**
 * A selector that holds only in a state: under the pointer, with the focus, under a press,
 * or while the part says of itself that it is on, off, open, chosen, assumed, arriving.
 * What a part is handed for good, as its kind and its pose are, is no state.
 */
const inAState = (selector: string) =>
  /:(hover|focus|focus-within|focus-visible|active|target)\b|\[(aria-(pressed|current|disabled|expanded)|data-(state|here|part|mixed|placed|asked|full|arrives))\b/.test(
    selector,
  );

describe("the kit of parts", () => {
  test.each(PARTS)("test_every_part_has_a_folder_of_its_own_with_its_style_sheet_and_its_test: %s", (part) => {
    const held = ["tsx", "module.css", "test.tsx"].map((kind) => existsSync(path.join(KIT, part, `${part}.${kind}`)));

    expect(held).toEqual([true, true, true]);
  });

  test("test_the_kit_holds_the_parts_that_were_promised_and_no_folder_that_is_no_part", () => {
    expect([...folders].sort()).toEqual([...PARTS].sort());
    // What was drawn for the accounts before this one is gone: the weight on its pan, the
    // balance, the yard and the lamp were the donkey's.
    expect(folders.filter((folder) => ["Weight", "Balance", "Yard", "Lamp"].includes(folder))).toEqual([]);
  });

  test("test_no_two_files_of_a_part_differ_only_by_a_capital", () => {
    // Seen on this machine: `Ends.tsx` and `ends.ts` are one file to a disk that knows no
    // capitals, and the part then asks itself for what it meant to ask the other.
    const twice = folders.flatMap((folder) => {
      const names = readdirSync(path.join(KIT, folder)).map((name) => name.replace(/\.(test\.)?(module\.css|tsx?)$/, "").toLowerCase());
      const plain = readdirSync(path.join(KIT, folder)).map((name) => name.replace(/\.(test\.)?(module\.css|tsx?)$/, ""));
      return [...new Set(plain)].filter((name) => new Set(plain.filter((other) => other.toLowerCase() === name.toLowerCase())).size > 1 && names.length > 0);
    });

    expect(twice).toEqual([]);
  });

  test("test_a_file_that_runs_in_the_browser_hands_out_components_and_nothing_else", () => {
    // What a page drawn on the server takes from a file that runs in the browser is a
    // component and nothing else: a constant taken from one arrives as a function, and no
    // test of a component sees it. So a list of kinds or a function that says a state is
    // kept in a file beside the part, which runs wherever it is read.
    const inTheBrowser = scripts.filter((file) => /^"use client";/.test(read(file)));
    const handedOut = inTheBrowser.flatMap((file) =>
      [...read(file).matchAll(/^export (?:(const|function|class) (\w+)|\{)/gm)]
        // A component is a function whose name begins with a capital. A type is no value, and is handed out freely.
        .filter(([, kind, name]) => !(kind === "function" && /^[A-Z]/.test(name ?? "")))
        .map(([line]) => `${file}: ${line}`),
    );

    // Of the rabbit, what is drawn of him, which says to the page that it is drawn for as
    // long as it is. And the rabbit of every page, who asks whether the page draws him.
    // Both are known in the browser alone. The button that stopped him ran there too, and
    // went when the founder asked: no file of the kit is a button of his.
    expect(scripts.filter((file) => /^Burro\/Stop\b/.test(file))).toEqual([]);
    expect(inTheBrowser.sort()).toEqual([
      "Burro/Drawn.tsx",
      "Burro/OfEveryPage.tsx",
      "Label/Label.tsx",
      "Note/Note.tsx",
      "Press/Press.tsx",
    ]);
    expect(handedOut).toEqual([]);
  });

  test("test_no_style_sheet_names_a_picture_which_is_named_by_the_list_of_drawings_or_by_a_token", () => {
    // A drawing is named where its name is held to the list by its type: one that is not
    // drawn is a fault when the website is built, and not a gap on the page. The picture of
    // a box is named by a token, so that one line of the tokens turns it off.
    const named = sheets.flatMap((file) => (written(file).match(/url\([^)]*\)/g) ?? []).map((found) => `${file} ${found}`));

    expect(sheets.length).toBe(PARTS.length);
    expect(named).toEqual([]);
  });

  test("test_every_drawing_the_kit_names_was_promised_by_that_name_and_has_been_made", () => {
    // A name that is written whole: one that ends in a hyphen is the start of a name made by rule.
    const DRAWING = /"((?:burro|gauge|key|thing|ui|btn|tile|frame)-[a-z0-9-]*[a-z0-9]|pin|ground)"/g;
    const found = [...new Set(scripts.flatMap((file) => [...read(file).matchAll(DRAWING)].map(([, name]) => name ?? "")))].sort();

    expect(found).toEqual([...NAMED].sort());
    expect(found.filter((name) => !isDrawn(name))).toEqual([]);
  });

  test("test_a_drawing_is_shown_with_a_hard_edge_and_at_its_own_size_never_stretched_and_never_at_a_percentage", () => {
    const named = RULES.filter((rule) => !FORCED.test(rule.under ?? "")).filter((rule) =>
      ["background", "background-image"].some((property) => /var\(--art(-down)?\)/.test(rule.sets.get(property) ?? "")),
    );
    // What is laid at no size is asked for and never seen: the picture of a button pressed,
    // which the face of a button asks for with the page, so that it is there at the first press.
    const unseen = named.filter((rule) => rule.sets.get("background-size") === "0 0");
    expect(unseen.map((rule) => [where(rule), rule.sets.get("background-image"), rule.sets.get("background-repeat")])).toEqual([
      ["Press/Press.module.css: .face", "var(--art-down)", "no-repeat"],
    ]);
    const laid = named.filter((rule) => !unseen.includes(rule));
    // The size of a drawing is what follows the stroke, in a rule that lays one as a ground.
    const sizes = laid.map((rule) => [where(rule), ((rule.sets.get("background") ?? "").replace(/\s+/g, " ").split(" / ")[1] ?? "").replace(/ no-repeat$/, "")]);
    const OWN = "calc(var(--px) * var(--w)) calc(var(--px) * var(--h))";
    // Burro is drawn at the art pixel of the stage where the page says so, in a box of one size.
    const HIS = "calc(var(--size) * var(--strip)) calc(var(--size) * 30)";

    expect(laid.length).toBeGreaterThan(8);
    expect(sizes.filter(([at, size]) => size !== (at?.startsWith("Burro/") ? HIS : OWN))).toEqual([]);
    // What draws one in the place of another, in a state, is the thing that was told to keep a hard edge.
    for (const rule of laid) {
      const hard = RULES.filter((other) => other.file === rule.file && other.sets.get("image-rendering") === "pixelated").map((other) => other.selector);
      const base = rule.selector.replace(/:(hover|focus-visible|active)|\[aria-disabled="true"\]/g, "");
      expect([where(rule), hard.includes(rule.selector) || hard.includes(base)]).toEqual([where(rule), true]);
    }
    // A picture that is cut in nine has its sides laid end to end. Stretched, or made to fit, a pixel of it would be no square.
    const cut = RULES.flatMap((rule) => [...rule.sets].filter(([property]) => property === "border-image" || property === "border-image-repeat").map(([, value]) => ({ at: where(rule), value })));
    expect(cut.filter(({ value }) => value !== "none" && !/\brepeat$/.test(value)).map(({ at }) => at)).toEqual([]);
    expect(RULES.filter((rule) => rule.sets.has("image-rendering") && rule.sets.get("image-rendering") !== "pixelated").map(where)).toEqual([]);
  });

  test("test_no_state_of_a_part_changes_the_room_it_takes", () => {
    /** What sets the room a thing takes, or where it lies. A state sets none of them. */
    const ROOM =
      /^(width|height|min-.*|max-.*|padding.*|margin.*|border|border-width|border-style|border-image|border-image-width|border-image-slice|border-image-outset|font.*|line-height|letter-spacing|display|position|inset.*|top|right|bottom|left|gap|flex.*|grid.*|float|translate|scale|rotate|zoom|white-space|overflow.*)$/;
    const states = RULES.filter((rule) => inAState(rule.selector) && !FORCED.test(rule.under ?? ""));
    const moved = states.flatMap((rule) =>
      [...rule.sets.keys()].filter((property) => ROOM.test(property)).map((property) => `${where(rule)} sets ${property}`),
    );

    expect(states.length).toBeGreaterThan(20);
    expect(moved).toEqual([]);
    // One thing is moved by a state: the words of a button, which step with its face, one
    // art pixel down and one to the right, inside the button. Nothing else is moved a little way.
    const transformed = states.filter((rule) => rule.sets.has("transform"));
    expect(transformed.map((rule) => [rule.file, rule.selector, rule.sets.get("transform")])).toEqual([
      ["Press/Press.module.css", '.press[aria-disabled="true"] > .face > .says', "translate(var(--px), var(--px))"],
      ["Press/Press.module.css", ".press:active > .face > .says", "translate(var(--px), var(--px))"],
    ]);
  });

  test("test_the_length_of_every_movement_is_a_token_and_every_movement_is_in_steps", () => {
    const named = RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition)/.test(property)));
    // What takes a movement away, for a person who asked for less of it, is no movement.
    const stilled = named.filter((rule) => rule.sets.get("animation") === "none");
    const moving = named.filter((rule) => !stilled.includes(rule));
    const movements = moving.flatMap((rule) =>
      partsOf(rule.sets.get("animation") ?? "", ",").map((one) => {
        const [name = "", length = "", timing = "", runs = ""] = partsOf(one, " ");
        return { where: where(rule), name, length, timing, runs };
      }),
    );

    expect(stilled.filter((rule) => !/prefers-reduced-motion:\s*reduce/.test(rule.under ?? "")).map(where)).toEqual([]);
    // Every movement is taken away for such a person, and not one is left to its first moment.
    expect(stilled.map((rule) => rule.selector).sort()).toEqual(moving.map((rule) => rule.selector).sort());
    // The rabbit, and a chip that arrives. The face of a button steps in no time at all.
    expect([...new Set(moving.map((rule) => rule.file))].sort()).toEqual(["Burro/Burro.module.css", "Label/Label.module.css"]);
    // Nothing is eased from one state to the next, and no movement is written in parts.
    expect(moving.flatMap((rule) => [...rule.sets.keys()].filter((property) => /^(transition|animation-)/.test(property)))).toEqual([]);
    // A length is a token, which is nought unless the system says that movement is welcome.
    // Or it is a clock of the rabbit's, which is so many rounds of his hop: so it is nought
    // wherever the length of a hop is, and one line of the tokens stills all of him.
    const clocks = RULES.flatMap((rule) =>
      [...rule.sets].filter(([property]) => /^--clock-/.test(property)).map(([name, length]) => ({ where: where(rule), name, length })),
    );
    expect(clocks.map((clock) => [clock.where, clock.name])).toEqual([
      ["Burro/Burro.module.css: .burro", "--clock-nose"],
      ["Burro/Burro.module.css: .burro", "--clock-eye"],
      ["Burro/Burro.module.css: .burro", "--clock-ears"],
      ["Burro/Burro.module.css: .burro", "--clock-now"],
    ]);
    expect(clocks.filter((clock) => !/^calc\(var\(--motion-hop\) \* \d+(\.\d+)?\)$/.test(clock.length))).toEqual([]);
    const his = ["var(--motion-hop)", ...clocks.map((clock) => `var(${clock.name})`)];
    expect(movements.length).toBeGreaterThan(4);
    expect(movements.filter((one) => one.length !== "var(--motion-drop)" && !his.includes(one.length))).toEqual([]);
    expect(sheets.flatMap((file) => (written(file).match(/\b\d*\.?\d+m?s\b/g) ?? []).map((found) => `${file} ${found}`))).toEqual([]);
    // A frame is held, and never blended into the next.
    expect(movements.filter((one) => !/^(step-end|step-start|steps\(.+\))$/.test(one.timing))).toEqual([]);
    // Each runs once and ends, but the rabbit's, which run for as long as he is drawn: his
    // hop while a search is read, and what he does where he rests. They are nine, all in his
    // own style sheet.
    expect(movements.filter((one) => one.runs !== "1" && !(one.runs === "infinite" && his.includes(one.length)))).toEqual([]);
    const endless = movements.filter((one) => one.runs === "infinite");
    expect(endless.map((one) => one.where.split(":")[0])).toEqual(Array.from({ length: 9 }, () => "Burro/Burro.module.css"));
    expect(endless.filter((one) => !/^burro-/.test(one.name))).toEqual([]);
    // What is not his runs once, in the length of a chip that drops: a clock of his is the length of nothing else.
    const others = movements.filter((one) => !/^Burro\//.test(one.where));
    expect(others.length).toBeGreaterThan(0);
    expect(others.filter((one) => one.length !== "var(--motion-drop)" || one.runs !== "1")).toEqual([]);
    // His sheet drew the button that stopped him, which the founder asked to go. It draws
    // none, and nothing of the kit stops what runs without end: the system alone stills
    // him, where it asks for less movement, and there each of the nine is taken away.
    expect(RULES.filter((rule) => /^Burro\//.test(rule.file) && /\.stop(?![\w-])/.test(rule.selector)).map(where)).toEqual([]);
    const without = moving.filter((rule) => /\binfinite\b/.test(rule.sets.get("animation") ?? ""));
    const taken = stilled.filter((rule) => rule.file === "Burro/Burro.module.css").map((rule) => rule.selector);
    expect(without.filter((rule) => !taken.includes(rule.selector)).map(where)).toEqual([]);
  });

  test("test_every_hard_shadow_is_the_shadow_of_the_look_so_that_it_goes_when_the_look_is_turned_down", () => {
    const thrown = RULES.filter((rule) => rule.sets.has("box-shadow") && !FORCED.test(rule.under ?? ""));
    /** A ring, which falls to no side, and what is drawn inside an edge: neither is thrown. */
    const isNoShadow = (layer: string) => /^inset\b/.test(layer) || /^0 0 0 /.test(layer) || layer === "none";
    const own = thrown.filter((rule) => partsOf(rule.sets.get("box-shadow") ?? "", ",").some((layer) => layer !== "var(--box-shadow)" && !isNoShadow(layer)));

    // A box and a chip throw one. The shadow of a button is in its picture, at its foot.
    expect(thrown.filter((rule) => rule.sets.get("box-shadow") === "var(--box-shadow)").map((rule) => rule.file).sort()).toEqual([
      "Frame/Frame.module.css",
      "Frame/Frame.module.css",
      "Label/Label.module.css",
    ]);
    expect(own.map(where)).toEqual([]);
    // It is named in a shadow and nowhere else, and never worked on: `calc` of `none` is nothing.
    const misnamed = RULES.filter((rule) => [...rule.sets].some(([property, value]) => property !== "box-shadow" && /var\(--box-shadow\)/.test(value)));
    expect(misnamed.map(where)).toEqual([]);
  });

  test("test_every_edge_of_the_kit_is_whole_and_a_step_of_a_band_keeps_its_edge_whatever_is_known_of_the_place", () => {
    // No edge of the kit is dashed or dotted: what nobody said is told by the word, and what
    // a source opens to stands within a whole edge.
    const broken = RULES.flatMap((rule) =>
      [...rule.sets].filter(([, value]) => /\b(dashed|dotted)\b/.test(value)).map(([property]) => `${where(rule)} sets ${property}`),
    );
    expect(broken).toEqual([]);
    // A step of a band is drawn one way, with a rule of ink all round it. Where a place
    // cannot be placed the five steps are empty and there is no peg: nothing takes the edge
    // of a step away, and nothing draws it in pieces.
    const edges = RULES.filter((rule) => rule.file === "Peg/Peg.module.css" && /\.step\b/.test(rule.selector)).flatMap((rule) =>
      [...rule.sets].filter(([property]) => /^(border|outline)/.test(property)).map(([property, value]) => [rule.selector, property, value]),
    );
    expect(edges).toEqual([[".step", "border", "var(--px) solid var(--ink)"]]);
    expect(RULES.filter((rule) => rule.file === "Peg/Peg.module.css" && /data-placed/.test(rule.selector)).map(where)).toEqual([]);
  });

  test("test_no_part_takes_the_ring_of_the_focus_off", () => {
    const taken = RULES.filter((rule) =>
      ["outline", "outline-style", "outline-width"].some((property) => /^(none|0)\b/.test(rule.sets.get(property) ?? "")),
    );

    expect(taken.map(where)).toEqual([]);
  });

  test("test_every_sentence_and_every_figure_is_set_in_the_reading_face", () => {
    // The pixel face is for a name and a short label. These are all that are set in it: the
    // words of a button and the word on the key of a source. Each gives way to the reading
    // face where its words hold a figure.
    const faces = RULES.filter((rule) => !FORCED.test(rule.under ?? "")).flatMap((rule) =>
      [...rule.sets]
        .filter(([property]) => property === "font" || property === "font-family")
        .map(([, value]) => ({ where: where(rule), face: /var\(--font-(name|say)\)/.exec(value)?.[1] ?? value, rule })),
    );

    expect(faces.length).toBeGreaterThan(8);
    expect(faces.filter(({ face }) => face === "name").map((one) => one.where)).toEqual([
      "Note/Note.module.css: .key",
      "Press/Press.module.css: .press",
    ]);
    // Everything else names the reading face, by its token: never a face by its own name.
    expect(faces.filter(({ face }) => face !== "name" && face !== "say" && face !== "inherit").map((one) => one.where)).toEqual([]);
    // The face of names has one weight and stands upright: a browser that thickens it smears it.
    for (const { rule, where: at } of faces.filter(({ face }) => face === "name")) {
      expect([at, /^400 /.test(rule.sets.get("font") ?? ""), rule.sets.get("font-synthesis")]).toEqual([at, true, "none"]);
    }
    // No part sets a figure on a drawing in the pixel face: a rank and a count are read.
    for (const part of ["Pennant", "Gauge", "Peg", "Label", "Ends"]) {
      expect([part, /var\(--font-name\)/.test(written(`${part}/${part}.module.css`))]).toEqual([part, false]);
    }
  });

  test("test_every_token_a_style_sheet_names_is_one_the_website_has_or_one_the_look_adds", () => {
    const { light } = themes();
    // What a part hands its own style sheet, on the element it draws.
    const own = new Set(
      sheets.flatMap((file) => [...written(file).matchAll(/(^|[\s;{])(--[a-z0-9-]+)\s*:/g)].map(([, , name]) => name)),
    );
    const handed = new Set(
      scripts.flatMap((file) => [...read(file).matchAll(/"(--[a-z0-9-]+)"/g)].map(([, name]) => name ?? "")),
    );
    const known = (name: string) =>
      name in light || name in SEVENTEEN || OF_THE_LOOK.includes(name) || own.has(name) || handed.has(name);
    const named = sheets.flatMap((file) =>
      [...written(file).matchAll(/var\((--[a-z0-9-]+)\s*(,?)/g)].map(([, name, comma]) => ({ file, name: name ?? "", otherwise: comma === "," })),
    );
    // What a part lets whatever lays it out say, as how much room a chip keeps round its
    // words. Wherever it is named, the sheet says what is drawn where nobody says: so it is
    // never a name that draws nothing.
    const said = new Set(named.filter(({ name }) => !known(name)).map(({ name }) => name));
    const left = [...said].filter((name) => named.some((one) => one.name === name && !one.otherwise));

    expect(named.length).toBeGreaterThan(100);
    expect(left).toEqual([]);
    expect([...said]).toEqual(["--label-room"]);
  });

  test("test_every_colour_a_style_sheet_names_is_a_token_and_none_is_written_out", () => {
    const writtenOut = sheets.flatMap((file) =>
      (written(file).match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).map((found) => `${file} ${found}`),
    );

    expect(writtenOut).toEqual([]);
  });

  test("test_brown_is_in_the_rabbit_and_nowhere_in_the_kit_but_in_his_drawings", () => {
    const brown = sheets.flatMap((file) => (written(file).match(/var\(--(fur|earth)\)/g) ?? []).map((found) => `${file} ${found}`));

    expect(brown).toEqual([]);
  });

  test.each([
    // The words of a box, a chip and a choice, on the grounds they stand on.
    ["--ink", "--page"],
    ["--ink", "--sand"],
    ["--ink", "--amber"],
    // The words of the main button, and of the choice in hand.
    ["--page", "--cobalt"],
    ["--page", "--ink"],
  ])("test_words_can_be_read_on_the_ground_they_are_set_on: %s on %s", (words, ground) => {
    expect(roundedDown(contrast(SEVENTEEN[words] ?? "", SEVENTEEN[ground] ?? ""))).toBeGreaterThanOrEqual(4.5);
  });

  test.each([
    // The rule of ink round a box, a button and a chip, on what it may stand on.
    ["--ink", "--page"],
    ["--ink", "--meadow"],
    ["--ink", "--lea"],
    // What is on is amber, which is not told from page: so it has an edge of ink.
    ["--ink", "--amber"],
    // The edge of poppy of a button that ends or takes away, inside its rule of ink, on its ground of page.
    ["--poppy", "--page"],
    // A step of a gauge that is filled, beside one that is not, and the peg on its step.
    ["--cobalt", "--page"],
    ["--poppy", "--ink"],
  ])("test_an_edge_and_a_mark_are_told_from_the_ground_they_lie_on: %s on %s", (mark, ground) => {
    expect(roundedDown(contrast(SEVENTEEN[mark] ?? "", SEVENTEEN[ground] ?? ""))).toBeGreaterThanOrEqual(3);
  });

  test("test_every_word_of_the_kit_is_ink_but_on_cobalt_where_it_is_page", () => {
    const set = RULES.filter((rule) => !FORCED.test(rule.under ?? "")).flatMap((rule) => {
      const colour = rule.sets.get("color");
      return colour === undefined ? [] : [{ where: where(rule), colour }];
    });
    const onADarkGround = set.filter(({ colour }) => colour === "var(--page)").map((one) => one.where);

    expect(set.length).toBeGreaterThan(8);
    expect(set.filter(({ colour }) => !["var(--ink)", "var(--page)", "inherit"].includes(colour))).toEqual([]);
    // Page is the colour of words on the main button.
    expect(onADarkGround.sort()).toEqual(['Press/Press.module.css: .face[data-kind="go"]']);
  });
});
