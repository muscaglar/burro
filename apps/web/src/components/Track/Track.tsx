import type { CSSProperties } from "react";

import { pictureOf, sizeOf } from "@/components/kit/drawings";
import { isRange, VIBE_BANDS, type Placed } from "@/lib/vibes";

import styles from "./Track.module.css";

interface Props {
  /**
   * Where the area sits. `null` of an area the vibe cannot place, which is drawn as five
   * empty steps with no peg: it is never put in the middle, and never at nought.
   */
  readonly placed: Placed | null;
  /**
   * What the picture shows, in words: the band, and which way the bands are counted.
   * Left out where the same words are written beside it, and the picture is then kept
   * from a screen reader, which would hear them twice.
   */
  readonly says?: string;
  /** True where marks stand side by side on a narrow screen, and the steps are drawn narrower. */
  readonly narrow?: boolean;
  /**
   * True where the band rests on part of its recipe. The step the peg stands on is then
   * chequered, and the words that say what it rests on stand beside the picture: whatever
   * draws the line writes them.
   */
  readonly part?: boolean;
  /**
   * True in a list of many small things, as a row of results is: the steps are small, and
   * the one the area sits on has a cap and no peg.
   */
  readonly small?: boolean;
}

/**
 * What whatever holds lines of steps says in a style sheet of its own, to have every line
 * it holds drawn with steps of one width, in art pixels: a result as narrow as a phone says
 * seven, so that the steps of one of its lines stand under the steps of another. It is
 * read by the style sheet of a line, where a step is nine unless this says otherwise.
 * Small steps, and the narrow steps a line asks for itself, are what they are whatever it says.
 */
export const STEP_OF_THE_LINES_HELD = "--track-step";

/** How much of the peg stands in its step, and how high a step is, in art pixels: what the style sheet lays a line of steps out by. */
const IN_ITS_STEP = 3;
const RISE = 6;

/**
 * How high a line of steps is, in art pixels: the peg over its step, and the step. A line
 * that holds no steps, as the line of a journey is, is told it, so that it is as high as
 * the line of a gauge that stands over it.
 */
export const HIGH = sizeOf("ui-peg").height - IN_ITS_STEP + RISE;

/** What the style sheet needs of the peg to stand it on a step: its picture and its size, in art pixels. */
function ofThePeg(): CSSProperties {
  const { width, height } = sizeOf("ui-peg");
  return { "--art": `url("${pictureOf("ui-peg")}")`, "--w": width, "--h": height } as CSSProperties;
}

/**
 * Where an area sits on a vibe, as the look draws a band: five steps from the low end to
 * the high end, with a peg on the one the area sits on. It is a place on a line and never
 * a bar that fills: a peg far to the right is more, and not better.
 *
 * A mixed area has a rail that joins the steps it spans, and no peg: it is never drawn as
 * a point in the middle. It is a picture, and says in words what it shows, or stands
 * beside the words that do.
 */
export function Track({ placed, says, narrow = false, part = false, small = false }: Props) {
  const range = placed !== null && isRange(placed);
  const [first] = VIBE_BANDS;
  // Where the mark begins, counted in steps from the low end, and how many steps it lies across.
  const at = placed === null ? 0 : (range ? placed.spread_low : placed.band) - first;
  const over = placed !== null && range ? placed.spread_high - placed.spread_low + 1 : 1;
  const on = (band: number) =>
    placed === null ? false : range ? band >= placed.spread_low && band <= placed.spread_high : band === placed.band;
  return (
    <span
      className={styles.track}
      data-range={range}
      data-narrow={narrow}
      data-part={part}
      data-small={small}
      data-placed={placed !== null}
      style={{ ...ofThePeg(), "--at": at, "--over": over } as CSSProperties}
      {...(says === undefined ? { "aria-hidden": true } : { role: "img", "aria-label": says })}
    >
      {VIBE_BANDS.map((band) => (
        <span key={band} className={styles.cell} {...(placed === null ? {} : { "data-on": on(band) })} />
      ))}
      {placed === null ? null : <span className={range ? styles.rail : styles.peg} />}
    </span>
  );
}
