import type { CSSProperties } from "react";

import { GAUGE } from "@/content/kit";
import { CHIPS } from "@/content/search";
import { SLIDER } from "@/content/settings";

import { pictureOf, sizeOf, type Drawing } from "../drawings";
import { filledOf, STEPS, within } from "./filled";
import styles from "./Gauge.module.css";

interface Props {
  /**
   * How much the thing counts, from 0 to 100. The API's weight runs from 0 to 1: multiply
   * it first. With `ends` it runs from -100, which is all the way to the low end, through
   * 0, which is no weight, to 100 at the high end, as the slider of a scale does.
   */
  readonly counts: number;
  /** How many steps there are from nought to a hundred. Ten, where none is given. */
  readonly steps?: number;
  /**
   * The names of the two ends of a scale, low and then high, as the API names them. The
   * gauge then has a middle, which is no weight, and fills from it towards either end.
   */
  readonly ends?: readonly [low: string, high: string];
  /**
   * False where it lies under a range input, which says how much itself: the gauge is then
   * drawn and says nothing. Left out, it stands alone and says how much in words.
   */
  readonly alone?: boolean;
}

/** How wide the middle of a scale is, in art pixels: a post of ink with an art pixel clear at either side. */
const MIDDLE = 5;

/** One step, the mark or the middle, placed in whole art pixels from the left of the gauge. */
const drawn = (name: Drawing, left: number): CSSProperties => {
  const { width, height } = sizeOf(name);
  return { "--art": `url("${pictureOf(name)}")`, "--w": width, "--h": height, "--left": left } as CSSProperties;
};

/** How much a thing counts, in words: what a gauge that stands alone says beside itself. */
export function inWords(counts: number, ends?: readonly [low: string, high: string]): string {
  const held = within(counts, ends === undefined ? 0 : -100);
  if (ends !== undefined) return held === 0 ? SLIDER.middle : SLIDER.towards(held < 0 ? ends[0] : ends[1], Math.abs(held));
  return held === 0 ? CHIPS.off : GAUGE.counts(held);
}

/**
 * How much a thing counts: a row of steps that fill, with a weight standing where the
 * filling has come to. It is drawn only. What a person moves is a range input, and the
 * gauge can lie under one and follow it: it is as wide as the travel of a thumb that is
 * as wide as its weight.
 *
 * It is never to be taken for where a place sits on a vibe, which is five steps and a peg
 * and never fills: a gauge has more steps, it fills, and it is in another colour.
 *
 * Alone, it says how much in words beside itself.
 */
export function Gauge({ counts, steps = STEPS, ends, alone = true }: Props) {
  const held = within(counts, ends === undefined ? 0 : -100);
  const each = Math.max(1, Math.round(steps));
  const filled = filledOf(held, each);
  const cell = sizeOf("gauge-cell");
  const mark = sizeOf("ui-weight");
  // Each step lies one art pixel over the one before it, so that two steps share one
  // outline. A scale has two runs of them, and its middle between.
  const pitch = cell.width - 1;
  const run = each * pitch + 1;
  const row = ends === undefined ? run : run * 2 + MIDDLE;
  // The weight stands over where the count has come to, in whole art pixels.
  const share = ends === undefined ? held / 100 : (held + 100) / 200;
  const at = Math.round(row * share);
  const inset = Math.floor(mark.width / 2);

  const cells = (side: "only" | "low" | "high") =>
    Array.from({ length: each }, (_, index) => {
      // Of a scale, the low side is counted from the middle outwards, which is from the right.
      const nth = side === "low" ? each - index : index + 1;
      const full = side === "only" ? nth <= filled : nth <= filled && (side === "low" ? held < 0 : held > 0);
      const from = side === "high" ? run + MIDDLE : 0;
      return (
        <span
          key={`${side}-${index}`}
          className={styles.cell}
          data-full={full}
          style={drawn(full ? "gauge-cell-full" : "gauge-cell", inset + from + index * pitch)}
        />
      );
    });

  return (
    <span className={styles.gauge} data-alone={alone}>
      <span
        className={styles.drawn}
        aria-hidden="true"
        style={{ "--wide": row + mark.width, "--high": mark.height + cell.height - 1 } as CSSProperties}
      >
        {ends === undefined ? (
          cells("only")
        ) : (
          <>
            {cells("low")}
            <span className={styles.middle} style={{ "--left": inset + run, "--w": MIDDLE, "--h": cell.height } as CSSProperties} />
            {cells("high")}
          </>
        )}
        <span className={styles.mark} style={drawn("ui-weight", at)} />
      </span>
      {alone ? <span className={styles.words}>{inWords(held, ends)}</span> : null}
    </span>
  );
}
