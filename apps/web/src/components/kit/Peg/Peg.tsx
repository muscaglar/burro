import type { CSSProperties, ReactElement } from "react";

import { CANNOT_PLACE } from "@/content/facts";
import { PEG } from "@/content/kit";
import { STRIP } from "@/content/search";
import { endsOf, inWords, isRange, plainly, VIBE_BANDS, type Placed } from "@/lib/vibes";

import { pictureOf, sizeOf } from "../drawings";
import { Ends } from "../Ends/Ends";
import styles from "./Peg.module.css";

interface Props {
  /** The band the place sits in, from 1 to 5, as the API sent it. `null` for a place that cannot be placed. */
  readonly band: number | null;
  /** The name the API gives the low end of a scale. `null` of a vibe that runs one way, from least to most. */
  readonly low?: string | null;
  /** The name the API gives the high end of a scale. `null` of a vibe that runs one way. */
  readonly high?: string | null;
  /** The bands the place spans, lowest and highest, as the API sent them. Left out where it sits in one. */
  readonly spread?: readonly [low: number, high: number] | null;
  /** Whether the vibe was asked for. Of a scale, which end was: `low` or `high`. The words say so. */
  readonly asked?: boolean | "low" | "high";
  /**
   * What the band rests on, where it rests on part of its recipe: the line that says so,
   * in the API's words. The step the peg stands on is then chequered, and the line stands
   * under it.
   */
  readonly part?: string | null;
  /**
   * True where each end is drawn with its small picture, as `Ends` draws them: houses and
   * flats, calm and buzzy. Left out, the ends of a scale are named under the steps, and
   * those of a vibe that runs one way are said by the picture alone.
   */
  readonly pictured?: boolean;
  /**
   * The id the service gives the vibe. Each end that is pictured then has the one picture
   * that is drawn for that end of that vibe, whichever way the vibe runs. Left out, an end
   * is drawn by its name, and every vibe that runs one way alike.
   */
  readonly id?: string | null;
}

/** What the picture says to whoever hears the page: the band, the ends it is counted between, and whether it was asked for. */
function saidBy(placed: Placed, [low, high]: readonly [string, string], scale: boolean, asked: Props["asked"]): string {
  const where = `${inWords(placed)}, ${STRIP.from(low, high)}`;
  if (asked === undefined || asked === false) return where;
  return `${where}, ${scale && asked !== true ? STRIP.askedFor(asked === "low" ? low : high) : STRIP.asked}`;
}

/** What a style sheet needs of the peg to stand it on a step: its picture and its size, in art pixels. */
function ofThePeg(): CSSProperties {
  const { width, height } = sizeOf("ui-peg");
  return { "--art": `url("${pictureOf("ui-peg")}")`, "--w": width, "--h": height } as CSSProperties;
}

/**
 * Where a place sits on a vibe: five steps, with a peg on one. It is a place on a line and
 * never a bar that fills, a score or a percentage: a peg far to the right is more, and not
 * better. The band is said in words beside it.
 *
 * A scale has both its ends named, and neither is the good one. A band that rests on part
 * of its recipe has its step chequered. A mixed place has a rail that joins the steps it
 * spans, and no peg: it is never a point in the middle. A place that cannot be placed is
 * five empty steps and no peg, each step with the whole edge of any step: it is never put
 * in the middle, and never at nought. The line of a vibe draws the state the same way.
 *
 * The names of the ends are drawn for the eye and said by the picture, so that a screen
 * reader hears each once.
 */
export function Peg({
  band,
  low = null,
  high = null,
  spread = null,
  asked = false,
  part = null,
  pictured = false,
  id,
}: Props) {
  const ends = endsOf({ low_end: low, high_end: high });
  const scale = low !== null && high !== null;
  /** The line of steps between its two ends: each end with its picture, or named under the steps. */
  const between = (steps: ReactElement) =>
    pictured ? (
      <Ends {...(id === undefined ? {} : { id })} low={low} high={high}>
        {steps}
      </Ends>
    ) : (
      <>
        {steps}
        {scale ? (
          <span className={styles.ends}>
            <span>{ends[0]}</span>
            <span>{ends[1]}</span>
          </span>
        ) : null}
      </>
    );

  if (band === null) {
    return (
      <span className={styles.peg} data-placed="false">
        <span className={styles.picture} role="img" aria-label={PEG.empty}>
          {between(
            <span className={styles.steps} style={ofThePeg()}>
              {VIBE_BANDS.map((one) => (
                <span key={one} className={styles.step} />
              ))}
            </span>,
          )}
        </span>
        <span className={styles.words}>{CANNOT_PLACE}</span>
      </span>
    );
  }

  const placed: Placed = { band, spread_low: spread?.[0] ?? band, spread_high: spread?.[1] ?? band };
  const mixed = isRange(placed);
  const first = VIBE_BANDS[0];
  // Where the mark begins, counted in steps from the low end, and how many steps it lies across.
  const at = (mixed ? placed.spread_low : band) - first;
  const over = mixed ? placed.spread_high - placed.spread_low + 1 : 1;
  const words = plainly({ low_end: low, high_end: high }, placed);
  const isAsked = asked !== false;
  const marked = (one: number) => (mixed ? one >= placed.spread_low && one <= placed.spread_high : one === band);

  return (
    <span className={styles.peg} data-placed="true" data-mixed={mixed} data-asked={isAsked} data-part={part !== null}>
      <span className={styles.picture} role="img" aria-label={saidBy(placed, ends, scale, asked)}>
        {between(
          <span className={styles.steps} style={{ ...ofThePeg(), "--at": at, "--over": over } as CSSProperties}>
            {VIBE_BANDS.map((one) => (
              <span key={one} className={styles.step} data-here={marked(one)} />
            ))}
            <span className={mixed ? styles.rail : styles.mark} />
          </span>,
        )}
      </span>
      {/* A band the website has no word for is said by the picture alone. */}
      {words === null ? null : <span className={styles.words}>{words}</span>}
      {/* The picture has said that it was asked for. For the eye it is said here. */}
      {isAsked ? (
        <span className={styles.asked} aria-hidden="true">
          {STRIP.asked}
        </span>
      ) : null}
      {part === null ? null : <span className={styles.part}>{part}</span>}
    </span>
  );
}
