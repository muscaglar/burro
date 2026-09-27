import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf } from "../../../../test/support/css";
import { framesOf, isDrawn, pictureOf, sizeOf } from "../drawings";
import { Burro, DRAWING, POSES, STILL } from "./Burro";
import { AT_REST, SOIL } from "./look";
import { FRAMES, HOP, RESTING, soilOf, STILL_OF, stirsOf } from "./poses";

const WEB = path.resolve(__dirname, "../../../..");
const CSS = readFileSync(path.join(__dirname, "Burro.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
/** What a rule sets, as it is written, with whatever parts its lines made one gap. */
const asWritten = (sets: ReadonlyMap<string, string>) => [...sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]);
const setsOf = (selector: string) =>
  new Map(STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => asWritten(rule.sets)));

/** One stop of a run of frames: how far through the run it stands, in hundredths, and what it sets. */
interface Stop {
  readonly at: number;
  readonly sets: ReadonlyMap<string, string>;
}

/** Every run of frames of the style sheet, by its name: its stops, in the order they are reached. */
const RUNS = new Map(
  [...CSS.matchAll(/@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}/g)].map(([, name, body]): [string, Stop[]] => [
    name ?? "",
    [...(body ?? "").matchAll(/([^{}]+)\{([^{}]*)\}/g)]
      .flatMap(([, stops, block]) => {
        const sets = new Map(
          (block ?? "")
            .split(";")
            .map((declaration) => declaration.split(":").map((part) => part.trim()))
            .filter((parts) => parts.length === 2 && parts[0] !== "")
            .map(([property, value]): [string, string] => [property ?? "", value ?? ""]),
        );
        return (stops ?? "").split(",").map((stop) => {
          const said = stop.trim();
          return { at: said === "from" ? 0 : said === "to" ? 100 : Number(said.replace("%", "")), sets };
        });
      })
      .sort((one, other) => one.at - other.at),
  ]),
);
/** Every property a run of frames sets, at whatever moment. */
const setBy = (name: string) => [...new Set((RUNS.get(name) ?? []).flatMap((stop) => [...stop.sets.keys()]))].sort();

/** Each thing that moves: the run of frames it names, its length, how it is timed and how often it runs. */
function movementsOf(selector: string) {
  return (setsOf(selector).get("animation") ?? "")
    .split(/,(?![^(]*\))/)
    .map((one) => one.trim().split(/\s+(?![^(]*\))/))
    .filter((parts) => parts.length > 1)
    .map(([name = "", length = "", timing = "", runs = ""]) => ({ name, length, timing, runs }));
}

/** What is drawn of him, which his box holds first: the layers of it, as the page has them. */
const drawnOf = (container: HTMLElement) => container.firstElementChild?.firstElementChild as HTMLElement;
const layersOf = (container: HTMLElement) => [...(drawnOf(container)?.children ?? [])] as HTMLElement[];
const classesOf = (layers: readonly Element[]) => layers.map((layer) => layer.className);

/** A round of his hop where movement is welcome, in thousandths of a second, as the tokens have it. */
const ROUND = (() => {
  const tokens = rulesOf(readFileSync(path.join(WEB, "src/styles/tokens.css"), "utf8"));
  const welcome = tokens.filter((rule) => /prefers-reduced-motion:\s*no-preference/.test(rule.under ?? ""));
  return Number(/^(\d+)ms$/.exec(new Map(welcome.flatMap((rule) => [...rule.sets])).get("--motion-hop") ?? "")?.[1]);
})();

/**
 * His clocks: what each moves, the run of frames it plays, and the frame that is drawn of
 * that part of him while it rests. What he does now and then is the whole of him, and is
 * drawn only while he does it.
 */
const CLOCKS = [
  { of: "nose", layer: ".nose", run: "burro-nose", length: "--clock-nose", frames: FRAMES.nose },
  { of: "eye", layer: ".eye", run: "burro-eye", length: "--clock-eye", frames: FRAMES.eye },
  { of: "ears", layer: ".ears", run: "burro-ears", length: "--clock-ears", frames: FRAMES.ears },
  { of: "now", layer: ".now", run: "burro-now", length: "--clock-now", frames: FRAMES.now },
] as const;

/** How many rounds of his hop a clock takes to come round, as the style sheet writes it. */
function roundsOf(length: string): number {
  return Number(/^calc\(var\(--motion-hop\) \* (\d+(?:\.\d+)?)\)$/.exec(setsOf(".burro").get(length) ?? "")?.[1]);
}

/**
 * How long a clock takes to come round where movement is welcome, in thousandths of a
 * second: so many rounds of his hop. A figure that is written in hundredths is not held
 * whole by a machine, so what it is out by, which is less than a millionth, is let go.
 */
function lastsFor(length: string): number {
  return Math.round(roundsOf(length) * ROUND * 1000) / 1000;
}

/** The same in tenths of a second, which is what the movements of a clock are written in. */
const tenthsOf = (length: string) => lastsFor(length) / 100;

/** The frame of the strip a position shows: `calc(var(--frame) * 7) 0` is the eighth, and `0 0` the first. */
function frameOf(position: string | undefined): number {
  if (position === "0 0") return 0;
  return Number(/^calc\(var\(--frame\) \* (\d+)\) 0$/.exec(position ?? "")?.[1] ?? Number.NaN);
}

/** What a clock shows, moment by moment: from when, in thousandths of a second, and which frame. `null` while nothing of it is drawn. */
function shownBy(clock: (typeof CLOCKS)[number]): { from: number; frame: number | null }[] {
  const length = lastsFor(clock.length);
  const atRest = setsOf(clock.layer).get("visibility") === "hidden" ? null : frameOf(setsOf(clock.layer).get("background-position") ?? "0 0");
  let frame = atRest;
  let seen = atRest !== null;
  return (RUNS.get(clock.run) ?? []).map((stop) => {
    if (stop.sets.has("visibility")) seen = stop.sets.get("visibility") === "visible";
    if (stop.sets.has("background-position")) frame = frameOf(stop.sets.get("background-position"));
    return { from: Math.round((stop.at / 100) * length), frame: seen ? frame : null };
  });
}

/** The frame that is drawn of a part while it rests. `null` of what is drawn only while it moves. */
const restOf = (clock: (typeof CLOCKS)[number]) => shownBy(clock)[0]?.frame ?? null;

/**
 * The movements of a clock: from when to when each is, in thousandths of a second. A sniff is
 * his nose up and down three times: what comes to rest for under a third of a second and
 * goes again is one movement.
 */
function movesOf(clock: (typeof CLOCKS)[number]): { from: number; to: number }[] {
  const shown = shownBy(clock);
  const rest = restOf(clock);
  const found: { from: number; to: number }[] = [];
  shown.forEach((one, at) => {
    if (one.frame === rest) return;
    const to = shown[at + 1]?.from ?? lastsFor(clock.length);
    const last = found.at(-1);
    if (last !== undefined && one.from - last.to < 300) last.to = to;
    else found.push({ from: one.from, to });
  });
  return found;
}

// ---------------------------------------------------------------------------
// The drawings, as their text has them.
// ---------------------------------------------------------------------------

type Grid = readonly (readonly string[])[];
const CLEAR = ".";

const SPRITES = (() => {
  const text = readFileSync(path.join(WEB, "art/burro.sprite.txt"), "utf8");
  const found = new Map<string, { frames: number; rows: string[] }>();
  let name = "";
  for (const line of text.split("\n")) {
    if (line.startsWith("== ")) {
      name = line.slice(3).trim();
      found.set(name, { frames: 1, rows: [] });
    } else if (name !== "" && line.startsWith("# @frames ")) {
      (found.get(name) as { frames: number }).frames = Number(line.slice("# @frames ".length));
    } else if (name !== "" && line !== "" && !line.startsWith("#")) {
      found.get(name)?.rows.push(line);
    }
  }
  return found;
})();

/** The frames of a drawing, each a grid of the keys of its pixels. A drawing that is no strip is its own one frame. */
function framesIn(name: string): Grid[] {
  const drawn = SPRITES.get(name);
  if (drawn === undefined) throw new Error(`${name} is not drawn`);
  const wide = (drawn.rows[0]?.length ?? 0) / drawn.frames;
  return Array.from({ length: drawn.frames }, (_, frame) => drawn.rows.map((row) => [...row.slice(frame * wide, (frame + 1) * wide)]));
}

/** Frames laid over one another, the first lowest, and how many pixels were drawn twice. */
function laid(...frames: Grid[]): { grid: Grid; twice: number } {
  let twice = 0;
  const grid = (frames[0] ?? []).map((row, y) =>
    row.map((_, x) => {
      const drawn = frames.map((frame) => frame[y]?.[x] ?? CLEAR).filter((key) => key !== CLEAR);
      if (drawn.length > 1) twice += 1;
      return drawn.at(-1) ?? CLEAR;
    }),
  );
  return { grid, twice };
}

const textOf = (grid: Grid) => grid.map((row) => row.join("")).join("\n");

/** What is his in a drawing, by its key: his fur, its light, its shade and what is pale of him. His outline is ink, as his burrow's is. */
const HIS_OWN = ["d", "s", "D", "w"];

interface Point {
  readonly x: number;
  readonly y: number;
}

/** Where he is in a frame of his hop: every pixel that is his, and is no clod of his burrow as the hole alone has it. */
function heIn(frame: Grid, hole: Grid): Point[] {
  return frame.flatMap((row, y) => row.flatMap((key, x) => (HIS_OWN.includes(key) && hole[y]?.[x] !== key ? [{ x, y }] : [])));
}

/** The middle of what is drawn: of its columns, and of its rows. */
function middleOf(drawn: readonly Point[]): Point {
  const mean = (all: readonly number[]) => all.reduce((sum, one) => sum + one, 0) / all.length;
  return { x: mean(drawn.map((one) => one.x)), y: mean(drawn.map((one) => one.y)) };
}

describe("Burro, who is a rabbit", () => {
  test.each(POSES)("test_the_drawing_of_him_says_nothing_to_a_screen_reader_whatever_he_does: %s", (pose) => {
    const { container } = render(<Burro pose={pose} />);

    expect(container.firstElementChild).toHaveAttribute("data-pose", pose);
    expect(drawnOf(container)).toHaveAttribute("aria-hidden", "true");
    expect(screen.queryByRole("img")).toBeNull();
    expect(container.textContent).toBe("");
    // Nothing of him is heard: the whole of him is kept from a screen reader, in every pose.
    expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
    expect([...container.querySelectorAll("*")].filter((one) => one.closest("[aria-hidden='true']") === null)).toEqual([]);
  });

  test.each(POSES)("test_his_box_is_twenty_four_art_pixels_by_thirty_in_every_pose: %s", (pose) => {
    const box = setsOf(".burro");

    // The box is of one size, said once, whatever is drawn in it: a pose that gives way to
    // another moves nothing, and nor does anything he does.
    expect([box.get("width"), box.get("height")]).toEqual(["calc(var(--size) * 24)", "calc(var(--size) * 30)"]);
    const sized = STYLES.filter((rule) => [...rule.sets.keys()].some((property) => /^((min|max)-)?(width|height|inline-size|block-size)$/.test(property)));
    expect(sized.map((rule) => rule.selector).sort()).toEqual([".burro", '.burro[data-peeps="true"]']);
    // And every drawing of him is drawn for that box: one frame of it is 24 by 30.
    const his = pose === "hops" ? [DRAWING[pose], STILL, soilOf(pose)] : [DRAWING[pose], stirsOf(pose)];
    for (const name of his) {
      expect([name, isDrawn(name)]).toEqual([name, true]);
      expect([name, sizeOf(name).width / framesOf(name), sizeOf(name).height]).toEqual([name, 24, 30]);
    }
  });

  test("test_behind_a_rule_he_is_drawn_from_his_back_up_in_a_box_that_is_as_wide_and_not_as_high", () => {
    const { container, rerender } = render(<Burro pose="sits" />);
    expect(container.firstElementChild).toHaveAttribute("data-peeps", "false");

    rerender(<Burro pose="sits" peeps />);
    expect(container.firstElementChild).toHaveAttribute("data-peeps", "true");

    // His box ends at the row his back begins to fall away from: what is under it is behind
    // the rule. It is the height of his box that changes, and nothing else is said of it.
    expect([...setsOf('.burro[data-peeps="true"]')]).toEqual([["height", "calc(var(--size) * 19)"]]);
    // Nothing of him is moved for it: every layer of him begins at the top of his box, and is cut off at its foot.
    expect(classesOf(layersOf(container))).toEqual(["waits", "stirs"]);
    expect(setsOf(".drawn").get("overflow")).toBe("hidden");
  });

  test("test_he_is_drawn_at_the_art_pixel_of_every_drawing_or_at_that_of_the_stage_as_the_page_says", () => {
    const { container, rerender } = render(<Burro pose="hops" />);
    expect(container.firstElementChild).toHaveAttribute("data-stage", "false");

    rerender(<Burro pose="hops" stage />);
    expect(container.firstElementChild).toHaveAttribute("data-stage", "true");

    expect(setsOf(".burro").get("--size")).toBe("var(--px)");
    expect(setsOf('.burro[data-stage="true"]').get("--size")).toBe("var(--px-stage)");
    // It is the size of a pixel that changes, and nothing else is said of the stage.
    expect([...setsOf('.burro[data-stage="true"]').keys()]).toEqual(["--size"]);
    // A pixel of him is a whole square of the screen, with a hard edge, in every layer of him.
    for (const layer of [".still", ".waits", ".hops", ".soil", ".body", ".ears", ".eye", ".nose", ".now"]) {
      expect([layer, setsOf(layer).get("image-rendering")]).toEqual([layer, "pixelated"]);
      expect([layer, setsOf(layer).get("background")]).toEqual([
        layer,
        "var(--art) 0 0 / calc(var(--size) * var(--strip)) calc(var(--size) * 30) no-repeat",
      ]);
    }
    // One frame of a strip is as wide as his box, and a strip is moved by whole frames.
    expect(setsOf(".burro").get("--frame")).toBe("calc(var(--size) * -24)");
  });

  test("test_he_moves_nothing_but_what_is_inside_his_own_box", () => {
    // What is drawn of him lies in his box, and is cut off where it would lie outside it.
    expect(setsOf(".burro").get("position")).toBe("relative");
    expect([setsOf(".drawn").get("position"), setsOf(".drawn").get("inset"), setsOf(".drawn").get("overflow")]).toEqual(["absolute", "0", "hidden"]);
    for (const layer of [".still", ".waits", ".hops", ".soil", ".stirs", ".rests", ".body", ".ears", ".eye", ".nose", ".now"]) {
      expect([layer, setsOf(layer).get("position"), setsOf(layer).get("inset")]).toEqual([layer, "absolute", "0"]);
    }
    // A movement changes which part of a drawing is seen, and whether it is seen. It moves
    // no box, and changes the size of none.
    expect([...new Set([...RUNS.keys()].flatMap(setBy))].sort()).toEqual(["background-position", "visibility"]);
    expect([...RUNS.keys()].sort()).toEqual(["burro-ears", "burro-eye", "burro-hops", "burro-nose", "burro-now", "burro-rests", "burro-seen", "burro-unseen"]);
    // Nothing of him is moved, turned or made larger by a style: he is drawn a frame at a time.
    expect(ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(transform|translate|scale|rotate|zoom|margin|top|left)/.test(property))).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_every_movement_of_his_is_in_steps_and_takes_its_length_from_the_length_of_his_hop", () => {
    const moving = ALL.filter((rule) => rule.sets.has("animation") && rule.sets.get("animation") !== "none");
    const all = moving.flatMap((rule) => movementsOf(rule.selector).map((one) => ({ ...one, of: rule.selector })));

    expect(moving.map((rule) => rule.under)).toEqual(moving.map(() => null));
    expect(all.map((one) => `${one.of} ${one.name}`).sort()).toEqual([
      ".ears burro-ears",
      ".eye burro-eye",
      ".hops burro-hops",
      ".hops burro-seen",
      ".nose burro-nose",
      ".now burro-now",
      ".rests burro-rests",
      ".stirs burro-seen",
      ".waits burro-unseen",
    ]);
    // A frame is held, and never blended into the next.
    expect(all.filter((one) => !/^(step-end|steps\(var\(--frames\)\))$/.test(one.timing))).toEqual([]);
    // Each runs for as long as he is drawn. None is written in parts, and none is eased.
    expect(all.filter((one) => one.runs !== "infinite")).toEqual([]);
    expect(ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(transition|animation-)/.test(property))).map((rule) => rule.selector)).toEqual([]);
    // Its length is the length of his hop, or a clock of his, which is so many rounds of his
    // hop: so where the length of a hop is nought, as it is until movement is welcome, every
    // length of his is nought, and nothing of him moves. No length is written out.
    const clocks = CLOCKS.map((clock) => `var(${clock.length})`);
    expect(all.filter((one) => one.length !== "var(--motion-hop)" && !clocks.includes(one.length))).toEqual([]);
    expect(CLOCKS.map((clock) => [clock.length, tenthsOf(clock.length) > 0])).toEqual(CLOCKS.map((clock) => [clock.length, true]));
    expect(/\d(ms|s)\b/.test(CSS)).toBe(false);
  });

  test("test_a_person_who_asked_for_less_movement_is_shown_none", () => {
    // A browser that is told to end every movement at once still gives each its first
    // moment. So where less movement is asked for, his are taken away, and he is drawn still.
    // It is the one way he is stilled: the founder relies on what a person has set in their
    // system, and the page has no control of its own for it.
    const stilled = ALL.filter((rule) => /prefers-reduced-motion:\s*reduce/.test(rule.under ?? ""));
    const moving = ALL.filter((rule) => rule.sets.has("animation") && rule.sets.get("animation") !== "none");

    expect(moving.length).toBeGreaterThanOrEqual(8);
    expect(stilled.map((rule) => [rule.selector, [...rule.sets]])).toEqual(moving.map((rule) => [rule.selector, [["animation", "none"]]]));
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <p>
        {POSES.map((pose) => (
          <Burro key={pose} pose={pose} />
        ))}
        <Burro pose="hops" stage />
      </p>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("while a search is read", () => {
  test("test_he_hops_through_the_strip_round_and_round_and_one_round_takes_the_length_of_a_hop", () => {
    const { container } = render(<Burro pose="hops" />);
    const hops = layersOf(container).find((layer) => layer.className === "hops");
    const strip = sizeOf("burro-hops");
    const frames = framesOf("burro-hops");

    expect(hops?.style.getPropertyValue("--art")).toBe('url("/art/burro-hops.png")');
    expect(hops?.style.getPropertyValue("--strip")).toBe(String(strip.width));
    expect(hops?.style.getPropertyValue("--frames")).toBe(String(frames));
    // A strip is a whole number of frames, and more than one.
    expect(frames).toBeGreaterThan(1);
    expect(strip.width % frames).toBe(0);

    const [moved] = movementsOf(".hops").filter((one) => one.name === "burro-hops");
    // One step for each frame, so that a frame is held and never blended into the next.
    expect(moved).toEqual({ name: "burro-hops", length: "var(--motion-hop)", timing: "steps(var(--frames))", runs: "infinite" });
    // It is moved on by the whole of its width in a round, so the last frame leads into the first.
    expect(setBy("burro-hops")).toEqual(["background-position"]);
    expect(/@keyframes burro-hops\s*\{\s*to\s*\{\s*background-position: calc\(var\(--size\) \* var\(--strip\) \* -1\) 0;/.test(CSS)).toBe(true);
  });

  test("test_every_frame_of_his_hop_is_one_thing_he_does_and_the_hole_is_alone_in_the_first_and_in_the_last", () => {
    const frames = framesIn(DRAWING.hops);
    const all = [...HOP.alone, ...HOP.up, ...HOP.out, ...HOP.down].sort((one, other) => one - other);

    // Every frame of the strip is a frame of one thing he does, and of no other.
    expect(all).toEqual(frames.map((_, at) => at));
    expect(framesOf(DRAWING.hops)).toBe(frames.length);
    // He comes up, is out, and goes down, in that order, between the hole alone and the hole alone.
    expect([HOP.alone[0], ...HOP.up, ...HOP.out, ...HOP.down, HOP.alone[1]]).toEqual(all);
    const hole = frames[0] as Grid;
    for (const at of HOP.alone) expect([at, heIn(frames[at] as Grid, hole).length, textOf(frames[at] as Grid) === textOf(hole)]).toEqual([at, 0, true]);
    for (const at of [...HOP.up, ...HOP.out, ...HOP.down]) expect([at, heIn(frames[at] as Grid, hole).length > 0]).toEqual([at, true]);
  });

  test("test_he_climbs_out_of_his_hole_before_he_springs_from_it", () => {
    // Seen frame by frame in a browser: from the frame in which his head and his forepaws
    // are at the mouth of his hole he was in the air in the next, whole, and the middle of
    // him had gone seven art pixels, further than in any other step of the round. He left
    // his hole too suddenly. A frame stands between the two, in which he climbs out.
    const frames = framesIn(DRAWING.hops);
    const hole = frames[0] as Grid;
    const he = frames.map((frame) => heIn(frame, hole));
    const highest = (at: number) => Math.min(...(he[at] ?? []).map((one) => one.y));
    const lowest = (at: number) => Math.max(...(he[at] ?? []).map((one) => one.y));
    const [climbs, springs] = [HOP.up.at(-1) as number, HOP.out[0]];

    // He rises with every frame as he comes up, and by no more in one than his ears are long.
    const tops = [...HOP.up, springs].map(highest);
    expect(tops).toEqual([...tops].sort((one, other) => other - one));
    expect(tops.slice(1).map((top, at) => (tops[at] ?? 0) - top).filter((rise) => rise < 1 || rise > 8)).toEqual([]);
    // As he climbs, what is lowest of him is in his hole still, under the rim of it. As he springs he is clear of it.
    const rim = hole.findIndex((row) => row.includes("n"));
    expect(rim).toBeGreaterThan(0);
    expect([lowest(climbs) > rim, lowest(springs) < rim]).toEqual([true, true]);
    // No step of the round takes the middle of him further than a quarter of the width of his box.
    const steps = he.flatMap((now, at) => {
      const before = he[at - 1] ?? [];
      if (now.length === 0 || before.length === 0) return [];
      const [from, to] = [middleOf(before), middleOf(now)];
      return [{ into: at, moved: Math.hypot(to.x - from.x, to.y - from.y) }];
    });
    expect(steps).toHaveLength(frames.length - 3);
    expect(steps.filter((step) => step.moved > 6).map((step) => step.into)).toEqual([]);
  });

  test("test_he_hops_as_a_rabbit_who_digs_and_not_as_one_in_a_hurry", () => {
    // The founder: "slow the hole hopping animation down a bit". A round was a second, in
    // eleven frames, and read as hurried. It is a second and a quarter, in twelve: so a
    // frame is held for longer than a tenth of a second, where it was held for less.
    const frames = framesOf(DRAWING.hops);

    expect(ROUND).toBeGreaterThanOrEqual(1200);
    expect(ROUND).toBeLessThanOrEqual(1350);
    expect(ROUND / frames).toBeGreaterThan(100);
    expect(ROUND / frames).toBeLessThan(115);
    // He moves in steps, and the steps are of one length: the strip is moved on by the
    // whole of its width in as many steps as it has frames, and no frame is held by a stop of its own.
    expect(movementsOf(".hops").find((one) => one.name === "burro-hops")?.timing).toBe("steps(var(--frames))");
    expect((RUNS.get("burro-hops") ?? []).map((stop) => stop.at)).toEqual([100]);
  });

  test("test_where_the_length_of_a_hop_is_nought_nothing_moves_and_he_waits", () => {
    const { container } = render(<Burro pose="hops" />);
    const [waits, hops] = layersOf(container);

    // Two drawings lie in his box: the one in which he waits, and the strip.
    expect([waits?.className, hops?.className]).toEqual(["waits", "hops"]);
    expect(waits?.style.getPropertyValue("--art")).toBe(`url("/art/${STILL}.png")`);
    expect(STILL).toBe("burro-waits");

    // At rest the strip is not seen and the drawing in which he waits is. Only a movement
    // shows the one and hides the other, and a movement whose length is nought never runs.
    expect(setsOf(".hops").get("visibility")).toBe("hidden");
    expect(setsOf(".waits").has("visibility")).toBe(false);
    expect(movementsOf(".hops").map((one) => one.name)).toEqual(["burro-hops", "burro-seen"]);
    expect(movementsOf(".waits").map((one) => one.name)).toEqual(["burro-unseen"]);
    expect([...movementsOf(".hops"), ...movementsOf(".waits")].filter((one) => one.length !== "var(--motion-hop)")).toEqual([]);
    // Neither is taken out of his box, in any state: nothing of him is laid out but his box.
    expect(STYLES.filter((rule) => rule.under === null && rule.sets.has("display")).map((rule) => rule.selector)).toEqual([".burro"]);
    expect(setBy("burro-seen")).toEqual(["visibility"]);
    expect(setBy("burro-unseen")).toEqual(["visibility"]);
    expect(/@keyframes burro-seen\s*\{\s*from,\s*to\s*\{\s*visibility: visible;/.test(CSS)).toBe(true);
    expect(/@keyframes burro-unseen\s*\{\s*from,\s*to\s*\{\s*visibility: hidden;/.test(CSS)).toBe(true);
  });
});

describe("the soil that flicks up as he burrows", () => {
  // The founder: "make soil flick up as it burros".
  const EARTH = "n";
  const SHADE = "D";
  const soil = () => framesIn(soilOf("hops"));
  const hop = () => framesIn(DRAWING.hops);
  /** Where soil is drawn in a frame. */
  const flying = (frame: Grid): Point[] => frame.flatMap((row, y) => row.flatMap((key, x) => (key === CLEAR ? [] : [{ x, y }])));
  /** The two flicks of a round, each the frames it is drawn in: as he comes up, and as he goes down. */
  const FLICKS = [HOP.up, HOP.down] as const;
  /** The things that fly in a frame, each the pixels of it: a pixel is of the thing it lies against. */
  const things = (frame: Grid): Point[][] => {
    const left = flying(frame);
    const found: Point[][] = [];
    while (left.length > 0) {
      const thing = [left.pop() as Point];
      for (const one of thing) {
        for (let at = left.length - 1; at >= 0; at -= 1) {
          const other = left[at] as Point;
          if (Math.abs(other.x - one.x) <= 1 && Math.abs(other.y - one.y) <= 1) thing.push(...left.splice(at, 1));
        }
      }
      found.push(thing);
    }
    return found;
  };
  /** The middle of the mouth of his hole: of what is dark in the frame of the hole alone. */
  const mouth = () => middleOf((hop()[0] as Grid).flatMap((row, y) => row.flatMap((key, x) => (key === "k" && y > 20 && y < 26 && x > 2 && x < 13 ? [{ x, y }] : []))));

  test("test_soil_flicks_up_as_he_goes_down_his_hole_and_again_as_he_comes_up_and_at_no_other_moment", () => {
    const frames = soil();
    const holds = frames.flatMap((frame, at) => (flying(frame).length > 0 ? [at] : []));

    expect(SOIL).toBe("flicks");
    expect(holds).toEqual([...HOP.up, ...HOP.down]);
    // While he is out, and while the hole is alone, nothing flies: so the round comes round with no jump.
    for (const at of [...HOP.alone, ...HOP.out]) expect([at, flying(frames[at] as Grid)]).toEqual([at, []]);
  });

  test("test_the_soil_is_a_strip_of_its_own_with_a_frame_for_every_frame_of_his_hop", () => {
    // It lies over his hop frame for frame, and is moved as far: so it is as wide, to the pixel.
    expect(isDrawn(soilOf("hops"))).toBe(true);
    expect(sizeOf(soilOf("hops"))).toEqual(sizeOf(DRAWING.hops));
    expect(framesOf(soilOf("hops"))).toBe(framesOf(DRAWING.hops));
    expect(soil()).toHaveLength(hop().length);
  });

  test("test_it_is_a_few_pixels_in_the_brown_of_his_burrow_and_in_its_shade", () => {
    for (const at of [...HOP.up, ...HOP.down]) {
      const keys = (soil()[at] as Grid).flat().filter((key) => key !== CLEAR);

      expect([at, [...new Set(keys)].sort()]).toEqual([at, [SHADE, EARTH]]);
      // It is soil, so it is earth for the most part, and its shade is the lesser part of a lump.
      expect([at, keys.filter((key) => key === EARTH).length > keys.filter((key) => key === SHADE).length * 2]).toEqual([at, true]);
      // A few pixels: a flick, and no fountain.
      expect([at, keys.length >= 5 && keys.length <= 24]).toEqual([at, true]);
      // In a few things: a lump of four pixels, a clod of two, a crumb of one. None is larger.
      const sizes = things(soil()[at] as Grid).map((thing) => thing.length);
      expect([at, sizes.length >= 4 && sizes.length <= 8, sizes.filter((size) => ![1, 2, 4].includes(size))]).toEqual([at, true, []]);
    }
  });

  test("test_it_breaks_up_as_it_falls_so_that_it_thins_before_it_is_gone", () => {
    // Seen frame by frame: a lump that was whole in the air in one frame, and gone in the
    // next, was seen to be taken away. What falls is what flew, broken up: a lump falls as
    // a clod, and a clod as a crumb.
    for (const flick of FLICKS) {
      const [rises, spreads, falls] = flick.map((at) => things(soil()[at] as Grid).map((thing) => thing.length));
      const most = (sizes: readonly number[] | undefined) => Math.max(...(sizes ?? []));
      const sum = (sizes: readonly number[] | undefined) => (sizes ?? []).reduce((all, one) => all + one, 0);

      expect([flick[0], most(rises), most(spreads), most(falls)]).toEqual([flick[0], 4, 4, 2]);
      expect([flick[0], sum(falls) < sum(spreads), sum(spreads) >= sum(rises)]).toEqual([flick[0], true, true]);
    }
  });

  test("test_it_rises_spreads_and_falls", () => {
    for (const flick of FLICKS) {
      const [first, second, third] = flick.map((at) => flying(soil()[at] as Grid));
      const high = [first, second, third].map((drawn) => middleOf(drawn ?? []).y);
      const far = [first, second, third].map((drawn) => {
        const from = mouth();
        return (drawn ?? []).reduce((sum, one) => sum + Math.abs(one.x - from.x), 0) / (drawn ?? []).length;
      });

      expect(flick).toHaveLength(3);
      // It is highest in the second frame of the three: it rises into it, and falls out of it.
      expect([flick[0], (high[1] ?? 0) < (high[0] ?? 0) - 2, (high[1] ?? 0) < (high[2] ?? 0) - 2]).toEqual([flick[0], true, true]);
      // And it goes further out from the mouth of his hole with every frame.
      expect([flick[0], (far[0] ?? 0) < (far[1] ?? 0), (far[1] ?? 0) < (far[2] ?? 0)]).toEqual([flick[0], true, true]);
      // It is thrown up: as it rises all of it is over the rim of his hole already, and none lies beside it.
      expect([flick[0], (first ?? []).filter((one) => one.y > 20).length]).toEqual([flick[0], 0]);
    }
  });

  test("test_it_flies_over_the_grass_and_never_over_him_or_over_his_burrow", () => {
    const over = soil().flatMap((frame, at) =>
      flying(frame).flatMap(({ x, y }) => {
        const under = (hop()[at] as Grid)[y]?.[x] ?? CLEAR;
        return under === CLEAR ? [] : [`frame ${at + 1}: soil over ${under} at ${x}, ${y}`];
      }),
    );

    expect(over).toEqual([]);
    // Nor does it touch him: a crumb that lies against his outline is read as a part of him.
    const beside = soil().flatMap((frame, at) =>
      flying(frame).flatMap(({ x, y }) => {
        const near = [-1, 0, 1].flatMap((down) => [-1, 0, 1].map((across) => (hop()[at] as Grid)[y + down]?.[x + across] ?? CLEAR));
        return near.every((key) => key === CLEAR) ? [] : [`frame ${at + 1}: soil against him at ${x}, ${y}`];
      }),
    );
    expect(beside).toEqual([]);
  });

  test("test_it_lies_over_his_hop_has_no_movement_of_its_own_and_is_seen_only_while_he_hops", () => {
    const { container } = render(<Burro pose="hops" />);
    const [, hops] = layersOf(container);
    const [over, ...others] = [...(hops?.children ?? [])] as HTMLElement[];

    // It is drawn inside the strip of his hop, which is the one thing of him that moves there.
    expect([hops?.className, over?.className, others.length]).toEqual(["hops", "soil", 0]);
    expect(over?.style.getPropertyValue("--art")).toBe(`url("${pictureOf(soilOf("hops"))}")`);
    expect(over?.style.getPropertyValue("--strip")).toBe(hops?.style.getPropertyValue("--strip"));
    // It lies where the strip under it lies, moment by moment, and no movement is its own: so
    // it is never out of step with him. It is seen while the strip is seen, and hidden with it:
    // where the length of a hop is nought, and where less movement is asked for, no soil is drawn.
    expect([...setsOf(".soil")].filter(([property]) => !["position", "inset", "background", "image-rendering"].includes(property))).toEqual([
      ["background-position", "inherit"],
    ]);
    expect(STYLES.filter((rule) => /\.soil\b/.test(rule.selector) && [...rule.sets.keys()].some((property) => /^(animation|visibility|transition)/.test(property))).map((rule) => rule.under)).toEqual([]);
    expect(setsOf(".hops").get("visibility")).toBe("hidden");
    // And it is cut off with him where it would lie outside his box: it moves nothing on the page.
    expect([setsOf(".soil").get("position"), setsOf(".soil").get("inset")]).toEqual(["absolute", "0"]);
    expect(drawnOf(container)).toContainElement(over as HTMLElement);
    expect(setsOf(".drawn").get("overflow")).toBe("hidden");
  });

  test("test_where_he_waits_still_no_soil_is_drawn", () => {
    // What is drawn where nothing may move is the frame of his hop in which he sits up, and
    // no soil flies in that frame: so the drawing in which he waits holds none.
    const waits = textOf(framesIn(STILL)[0] as Grid);
    const as = hop().findIndex((frame) => textOf(frame) === waits);

    expect(HOP.out).toContain(as);
    expect(flying(soil()[as] as Grid)).toEqual([]);
    const { container } = render(<Burro pose="hops" />);
    expect(layersOf(container)[0]?.children).toHaveLength(0);
  });

  test("test_one_line_takes_the_soil_away_and_he_hops_as_he_did", () => {
    const { container } = render(<Burro pose="hops" soil="none" />);
    const [waits, hops, ...others] = layersOf(container);

    expect([waits?.className, hops?.className, others.length]).toEqual(["waits", "hops", 0]);
    expect(hops?.children).toHaveLength(0);
    expect(container.innerHTML.includes(soilOf("hops"))).toBe(false);
    // Where he rests there is no soil, whatever the line says.
    const resting = render(<Burro pose="sits" soil="flicks" />);
    expect(resting.container.innerHTML.includes("soil")).toBe(false);
  });
});

describe("where nothing is asked of him", () => {
  test.each(RESTING)("test_he_stirs_wherever_he_is_drawn_in_a_strip_of_the_pose_he_is_in: %s", (pose) => {
    const { container } = render(<Burro pose={pose} />);
    const [waits, stirs, ...others] = layersOf(container);

    expect(AT_REST).toBe("stirs");
    expect(drawnOf(container)).toHaveAttribute("data-moves", "true");
    // Two drawings lie in his box, as where he hops: him drawn still, and the strip of what he does.
    expect([waits?.className, stirs?.className, others.length]).toEqual(["waits", "stirs", 0]);
    expect(waits?.style.getPropertyValue("--art")).toBe(`url("${pictureOf(STILL_OF[pose])}")`);
    expect(STILL_OF[pose]).toBe(DRAWING[pose]);
    expect(stirs?.style.getPropertyValue("--art")).toBe(`url("/art/burro-${pose}-stirs.png")`);
    expect(stirs?.style.getPropertyValue("--strip")).toBe(String(sizeOf(stirsOf(pose)).width));
    // What rests of him is four layers, each a part of him, and over them what he does now and then.
    const [rests, now] = [...(stirs?.children ?? [])];
    expect(classesOf([...(stirs?.children ?? [])])).toEqual(["rests", "now"]);
    expect(classesOf([...(rests?.children ?? [])])).toEqual(["body", "ears", "eye", "nose"]);
    expect(now?.children).toHaveLength(0);
    // Every layer is a window on the one strip, which is handed once and asked for once.
    expect([...(stirs?.querySelectorAll("[style]") ?? [])]).toEqual([]);
  });

  test("test_where_the_length_of_a_hop_is_nought_nothing_of_him_stirs_and_he_is_drawn_still", () => {
    // As where he hops: the strip is not seen and the drawing of him still is, and only a
    // movement shows the one and hides the other.
    expect(setsOf(".stirs").get("visibility")).toBe("hidden");
    expect(movementsOf(".stirs")).toEqual([{ name: "burro-seen", length: "var(--motion-hop)", timing: "step-end", runs: "infinite" }]);
    expect(STYLES.filter((rule) => rule.sets.has("visibility")).map((rule) => rule.selector).sort()).toEqual([".hops", ".now", ".stirs"]);
    // What is drawn still is the drawing of his pose, which the strip at rest is point for point.
    for (const pose of RESTING) {
      const [body, ears, , , eye, , nose] = framesIn(stirsOf(pose));
      const atRest = laid(body as Grid, ears as Grid, eye as Grid, nose as Grid);

      expect([pose, textOf(atRest.grid) === textOf(framesIn(STILL_OF[pose])[0] as Grid)]).toEqual([pose, true]);
    }
  });

  test("test_the_frames_of_a_strip_stand_in_one_order_so_that_one_style_sheet_moves_him_in_every_pose", () => {
    const all = [FRAMES.body, FRAMES.ears, FRAMES.eye, FRAMES.nose, FRAMES.now].flat();

    // Every frame of the strip is a frame of one movement, and of no other.
    expect(all).toEqual(all.map((_, at) => at));
    for (const pose of RESTING) expect([pose, framesOf(stirsOf(pose))]).toEqual([pose, all.length]);
    // A part at rest shows the first of its frames, and a movement of it shows its own and no other.
    for (const clock of CLOCKS) {
      const shown = [...new Set(shownBy(clock).map((one) => one.frame))].filter((frame) => frame !== null).sort((one, other) => one - other);

      expect([clock.of, restOf(clock)]).toEqual([clock.of, clock.of === "now" ? null : clock.frames[0]]);
      expect([clock.of, shown]).toEqual([clock.of, [...clock.frames]]);
    }
    expect(setsOf(".body").has("background-position")).toBe(false);
    expect(setsOf(".body").has("animation")).toBe(false);
  });

  test("test_his_nose_his_eye_his_ears_and_what_he_does_now_and_then_each_have_a_clock_and_no_two_share_a_factor", () => {
    const factor = (one: number, other: number): number => (other === 0 ? one : factor(other, one % other));
    const tenths = CLOCKS.map((clock) => tenthsOf(clock.length));

    // Each comes round in a whole number of tenths of a second, which is what its movements are written in.
    expect(tenths.filter((one) => !Number.isInteger(one))).toEqual([]);

    for (const clock of CLOCKS) {
      expect([clock.of, movementsOf(clock.layer)]).toEqual([
        clock.of,
        [{ name: clock.run, length: `var(${clock.length})`, timing: "step-end", runs: "infinite" }],
      ]);
    }
    // One strip played round and round is seen for what it is in ten seconds. His clocks
    // come round together only after as many tenths of a second as all four multiplied:
    // so what he does next is not what he did at this point the last time.
    const shared = tenths.flatMap((one, at) => tenths.slice(at + 1).map((other) => [one, other, factor(one, other)]));
    expect(shared.filter(([, , common]) => common !== 1)).toEqual([]);
    const together = tenths.reduce((all, one) => all * one, 1) * 100;
    expect(together / 1000 / 60 / 60 / 24).toBeGreaterThan(7);
    expect(Math.max(...tenths) * 100).toBeGreaterThanOrEqual(30_000);
  });

  test("test_what_he_does_at_rest_is_no_slower_for_his_hop_being_slower", () => {
    // A clock is so many rounds of his hop, so that one line of the tokens stills all of
    // him. The founder asked for his hop to be slower, and for nothing of what he does at
    // rest: so a clock is fewer rounds than it was, and as long. Whoever changes the length
    // of his hop changes these with it, or he stirs at a pace that nobody chose for him.
    expect(CLOCKS.map((clock) => [clock.of, lastsFor(clock.length)])).toEqual([
      ["nose", 9_700],
      ["eye", 11_300],
      ["ears", 13_100],
      ["now", 40_900],
    ]);
  });

  test("test_no_part_of_him_moves_to_a_beat_and_he_is_never_still_for_long", () => {
    // Seen in a browser, by a person who watched him for a minute: "his nose lifts every
    // 3.1 seconds to the tick, he blinks every 5.3 and his ears go every 7.3". Each clock
    // came round in a few seconds with a movement or two in it, so each part of him was a
    // metronome. A round of a part now holds four movements or more, with no two waits of
    // one length between them, and comes round in no less than nine seconds.
    for (const clock of CLOCKS.filter((one) => one.of !== "now")) {
      const round = lastsFor(clock.length);
      expect([clock.of, movesOf(clock).length >= 4, round >= 9000]).toEqual([clock.of, true, true]);
    }
    // All that he does in ten minutes, clock by clock, and the longest he is still in them.
    const span = 10 * 60 * 1000;
    const moves = CLOCKS.flatMap((clock) => {
      const round = lastsFor(clock.length);
      return Array.from({ length: Math.ceil(span / round) }, (_, turn) => movesOf(clock).map(({ from, to }) => ({ from: from + turn * round, to: to + turn * round }))).flat();
    }).sort((one, other) => one.from - other.from);
    let until = 0;
    let longest = 0;
    for (const { from, to } of moves) {
      if (from > until) longest = Math.max(longest, from - until);
      until = Math.max(until, to);
    }
    // He is a rabbit at rest and no picture: something of him moves every three seconds at the least.
    expect(longest).toBeLessThanOrEqual(3000);
    expect(longest).toBeGreaterThan(1000);
    // And he is not busy: in a minute he begins no more than he did.
    expect(moves.filter(({ from }) => from < 60_000).length).toBeLessThanOrEqual(84);
  });

  test.each(CLOCKS)("test_every_movement_of_a_clock_is_shorter_than_the_wait_before_it_and_the_wait_after_it: $of", (clock) => {
    const round = lastsFor(clock.length);
    const moves = movesOf(clock);

    expect(moves.length).toBeGreaterThan(1);
    const waits = moves.map((one, at) => {
      const next = moves[(at + 1) % moves.length] as { from: number };
      return { moved: one.to - one.from, then: at === moves.length - 1 ? round - one.to + next.from : next.from - one.to };
    });
    const before = (at: number) => waits[(at + waits.length - 1) % waits.length]?.then ?? 0;
    expect(waits.filter((one, at) => one.moved >= one.then || one.moved >= before(at))).toEqual([]);
    // No two waits of a clock are of one length: he does nothing to a beat.
    expect(new Set(waits.map((one) => one.then)).size).toBe(waits.length);
  });

  test.each(CLOCKS)("test_every_frame_is_held_long_enough_to_be_seen: $of", (clock) => {
    const round = lastsFor(clock.length);
    const shown = shownBy(clock);
    // Every stop but the first and the last, which are the two ends of the round: how long what begins at it is held.
    const held = shown.slice(1, -1).map((one, at) => (shown[at + 2]?.from ?? round) - one.from);

    // A frame that is held for under a twelfth of a second is a flicker, and is not seen for what it is.
    expect(held.filter((length) => length < 80)).toEqual([]);
    // Each stop is written once, with all that it sets: a browser that keeps only the last of two takes nothing away.
    const stops = (RUNS.get(clock.run) ?? []).map((stop) => stop.at);
    expect(new Set(stops).size).toBe(stops.length);
  });

  test("test_every_clock_begins_and_ends_at_rest_and_no_two_begin_together_as_the_page_opens", () => {
    for (const clock of CLOCKS) {
      const stops = RUNS.get(clock.run) ?? [];
      const [first, last] = [stops[0], stops.at(-1)];

      // It comes round with no jump: its last moment is its first, and both are rest.
      expect([clock.of, first?.at, last?.at, first?.sets === last?.sets]).toEqual([clock.of, 0, 100, true]);
      expect([clock.of, shownBy(clock)[0]?.frame, shownBy(clock).at(-1)?.frame]).toEqual([clock.of, restOf(clock), restOf(clock)]);
    }
    // Every clock starts as he is drawn. The first thing each does is at a moment of its
    // own, so that he is not seen to do four things at once and then nothing.
    const first = CLOCKS.map((clock) => movesOf(clock)[0]?.from ?? 0).sort((one, other) => one - other);
    expect(first[0]).toBeGreaterThanOrEqual(500);
    expect(first.slice(1).map((from, at) => from - (first[at] ?? 0)).filter((apart) => apart < 1000)).toEqual([]);
    // And something of him moves within the first seconds: he is not taken for a picture.
    expect(first[0]).toBeLessThanOrEqual(2000);
  });

  test("test_while_he_does_what_he_does_now_and_then_the_rest_of_him_is_not_drawn", () => {
    // What he does now and then is the whole of him, drawn over where he rests. So while
    // it is seen, what rests is not, and the two change at one moment.
    const seen = (run: string) => (RUNS.get(run) ?? []).filter((stop) => stop.sets.has("visibility")).map((stop) => [stop.at, stop.sets.get("visibility")]);
    const other = (is: string | undefined) => (is === "visible" ? "hidden" : "visible");

    expect(movementsOf(".rests")).toEqual([{ name: "burro-rests", length: "var(--clock-now)", timing: "step-end", runs: "infinite" }]);
    expect(seen("burro-rests")).toEqual(seen("burro-now").map(([at, is]) => [at, other(is as string)]));
    expect(setBy("burro-rests")).toEqual(["visibility"]);
    expect(setsOf(".now").get("visibility")).toBe("hidden");
    expect(setsOf(".rests").has("visibility")).toBe(false);
  });
});

describe("the drawings of what he does at rest", () => {
  const his = ["k", "w", "s", "d", "D"];

  test.each(RESTING)("test_every_part_of_him_is_drawn_in_a_place_of_its_own_whatever_it_does: %s", (pose) => {
    const frames = framesIn(stirsOf(pose));
    const of = (which: readonly number[]) => which.map((at) => frames[at] as Grid);
    const body = frames[FRAMES.body[0]] as Grid;

    // A part that moves is drawn by its own layer and by no other: so no pixel of him is
    // drawn twice, whatever his ears, his eye and his nose are doing at one moment.
    for (const ears of of(FRAMES.ears)) {
      for (const eye of of(FRAMES.eye)) {
        for (const nose of of(FRAMES.nose)) expect(laid(body, ears, eye, nose).twice).toBe(0);
      }
    }
    // And no part leaves a hole in him: where a part is drawn at rest, it is drawn in every frame of it.
    for (const part of [FRAMES.eye, FRAMES.nose]) {
      const [rest, ...moved] = of(part);
      const inside = (rest as Grid).flatMap((row, y) => row.flatMap((key, x) => (key !== CLEAR && key !== "k" ? [[y, x] as const] : [])));
      for (const frame of moved) expect(inside.filter(([y, x]) => frame[y]?.[x] === CLEAR)).toEqual([]);
    }
  });

  test.each(RESTING)("test_whatever_his_parts_do_he_is_whole_with_an_outline_of_ink_and_on_his_row: %s", (pose) => {
    const frames = framesIn(stirsOf(pose));
    const body = frames[FRAMES.body[0]] as Grid;
    const whole = [
      ...FRAMES.ears.flatMap((ears) => FRAMES.eye.flatMap((eye) => FRAMES.nose.map((nose) => laid(body, frames[ears] as Grid, frames[eye] as Grid, frames[nose] as Grid).grid))),
      ...FRAMES.now.map((at) => frames[at] as Grid),
    ];

    expect(whole).toHaveLength(FRAMES.ears.length * FRAMES.eye.length * FRAMES.nose.length + FRAMES.now.length);
    for (const grid of whole) {
      const at = (x: number, y: number) => grid[y]?.[x] ?? CLEAR;
      const bare = grid.flatMap((row, y) =>
        row.flatMap((key, x) => (key !== CLEAR && key !== "k" && [at(x - 1, y), at(x + 1, y), at(x, y - 1), at(x, y + 1)].includes(CLEAR) ? [`${key} at ${x}, ${y}`] : [])),
      );

      // A colour never stands bare against the page, and he stands on the row he stands on in every drawing.
      expect(bare).toEqual([]);
      expect(grid.findLastIndex((row) => row.some((key) => key !== CLEAR))).toBe(28);
      // He is drawn in his own colours and in no other: fur, its light and its shade, what is pale of him, and ink.
      expect([...new Set(grid.flat())].filter((key) => key !== CLEAR && !his.includes(key))).toEqual([]);
    }
  });

  test.each(RESTING)("test_no_frame_of_what_he_does_now_and_then_is_drawn_twice: %s", (pose) => {
    const frames = framesIn(stirsOf(pose));
    const now = FRAMES.now.map((at) => textOf(frames[at] as Grid));

    expect(new Set(now).size).toBe(now.length);
    // And none of them is him as he rests: each is something he does.
    expect(now).not.toContain(textOf(framesIn(STILL_OF[pose])[0] as Grid));
  });
});

describe("nothing stops him but what a person has set in their system", () => {
  /** Every file of his that is no test, by its name. */
  const HIS = readdirSync(__dirname).filter((file) => !/\.test\.tsx?$/.test(file));

  test.each(POSES)("test_no_button_stands_by_him_and_nothing_of_him_takes_a_press_or_the_focus: %s", async (pose) => {
    const user = userEvent.setup();
    const { container } = render(
      <p>
        <Burro pose={pose} />
        <Burro pose={pose} peeps ofEveryPage />
      </p>,
    );

    // The founder: "remove the pause button for the rabbit".
    expect(screen.queryByRole("button")).toBeNull();
    expect(container.querySelectorAll("button, a, input, [tabindex], [role], [aria-label]")).toHaveLength(0);
    await user.tab();
    expect(document.body).toHaveFocus();
    // A press on him does nothing: he moves as he moved.
    const moves = () => [...container.querySelectorAll("[data-moves]")].map((one) => one.getAttribute("data-moves"));
    const before = moves();
    for (const he of container.querySelectorAll<HTMLElement>("[data-pose]")) await user.click(he);
    expect(moves()).toEqual(before);
    expect(before).toEqual(["true", "true"]);
  });

  test("test_no_file_of_his_draws_a_button_holds_whether_he_was_stopped_or_names_anything_a_browser_keeps", () => {
    // What was left of what stopped him did nothing, and nothing called it: it is gone.
    expect(HIS.filter((file) => /^stop/i.test(file))).toEqual([]);
    for (const file of HIS.filter((one) => /\.tsx?$/.test(one))) {
      const source = readFileSync(path.join(__dirname, file), "utf8").replace(/\/\*[\s\S]*?\*\/|(?<![:"'`])\/\/.*$/gm, "");
      expect([file, /<button\b|onClick|onKey|aria-label|useState|useSyncExternalStore\(listen, isStopped/.test(source)]).toEqual([file, false]);
      expect([file, /localStorage|sessionStorage|indexedDB|cookie|location|history|searchParams/.test(source)]).toEqual([file, false]);
    }
  });

  test("test_no_style_of_his_is_of_a_button_and_none_is_keyed_on_a_press_the_pointer_or_the_focus", () => {
    expect(ALL.filter((rule) => /\.(stop|by)\b|:(active|hover|focus)|\[data-does/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    expect(/--(stop|move)\b|cursor|--target/.test(CSS)).toBe(false);
  });

  test("test_nothing_of_the_website_names_what_was_drawn_of_his_button_or_of_him_asking", () => {
    // Four drawings were of the button: as it stopped him and as it let him move, and each
    // pressed. Two were of him where he asked. They are gone from the drawings, and
    // nothing of the website names one of them, by its name or by the rule that made it.
    const SRC = path.join(WEB, "src");
    const under = (folder: string): string[] =>
      readdirSync(folder, { withFileTypes: true }).flatMap((entry) =>
        entry.isDirectory() ? under(path.join(folder, entry.name)) : [path.join(folder, entry.name)],
      );
    const drawn = under(SRC).filter((file) => /\.(tsx?|css)$/.test(file) && !/\.test\.tsx?$/.test(file));
    const naming = drawn.filter((file) => /burro-(stop|move|asks)|`burro-\$\{(?!pose\})/.test(readFileSync(file, "utf8")));

    expect(drawn.length).toBeGreaterThan(300);
    expect(naming.map((file) => path.relative(SRC, file))).toEqual([]);
    // What he is drawn from is the drawing of each pose, the one in which he waits, a strip for
    // the pose he rests in, and the soil that flies as he hops.
    const his = [...new Set([...POSES.map((pose) => DRAWING[pose]), STILL, ...RESTING.map(stirsOf), soilOf("hops")])].sort();
    expect(his).toEqual(["burro-hops", "burro-hops-soil", "burro-sits", "burro-sits-stirs", "burro-waits"]);
    for (const name of his) expect([name, isDrawn(name)]).toEqual([name, true]);
  });

  test("test_one_line_draws_him_still_as_he_was", () => {
    for (const pose of RESTING) {
      const { container, unmount } = render(<Burro pose={pose} atRest="still" />);
      const [only, ...others] = layersOf(container);

      expect(screen.queryByRole("button")).toBeNull();
      expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
      expect(drawnOf(container)).toHaveAttribute("data-moves", "false");
      expect([pose, others.length, only?.className]).toEqual([pose, 0, "still"]);
      expect([pose, only?.style.getPropertyValue("--art")]).toEqual([pose, `url("/art/burro-${pose}.png")`]);
      unmount();
    }
    // Where he hops is no part of it: he hops while a search is read, as he did.
    const { container } = render(<Burro pose="hops" atRest="still" />);
    expect(classesOf(layersOf(container))).toEqual(["waits", "hops"]);
    expect(classesOf([...(layersOf(container)[1]?.children ?? [])])).toEqual(["soil"]);
  });
});
