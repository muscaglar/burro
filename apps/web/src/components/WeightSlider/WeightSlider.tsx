"use client";

import { useEffect, useId, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";

import { SLIDER } from "@/content/settings";
import type { ServedLimits } from "@/lib/api/schema";

import { Art } from "../kit/Art/Art";
import { cutOf, pictureOf, sizeOf, type Drawing } from "../kit/drawings";
import { NO_PICTURE, picturesAtEnds } from "../kit/Ends/picture";
import { Gauge } from "../kit/Gauge/Gauge";
import { picturesOf } from "../kit/Press/kinds";
import { holdsAFigure } from "../kit/reads";
import type { ThingOf } from "../kit/Thing/drawn";
import { Drawn } from "../kit/Thing/Thing";
import { StepButton } from "../NumberStepper/StepButton";
import { ENDS_OF_ONE_WAY, type EndsOfOneWay } from "./look";
import { eachWay, stepsOf } from "./steps";
import styles from "./WeightSlider.module.css";

/** How long after the last key or press a change is sent. */
export const SETTLE_MS = 150;

interface Props {
  /**
   * The weight as the API returned it, from 0 to 1. For a scale it runs from -1, which is
   * all the way to the low end, through 0, which is no weight, to 1 at the high end.
   */
  readonly value: number;
  readonly limits: Pick<ServedLimits, "weight_unit" | "weight_step_small">;
  /** What is being weighed. It names the slider, its buttons and its field. */
  readonly label: string;
  readonly onCommit: (value: number) => void;
  /** A number that changes with every answer from the API, so the slider is drawn again from it. */
  readonly version: number;
  /**
   * The id of the line that says what the scale means, where whatever holds the slider
   * draws it once for several. Left out, the slider draws the line under itself.
   */
  readonly scale?: string;
  /**
   * The names of the two ends of a scale, low and then high, as the API names them. With
   * them the slider is one slider with two ends: it rests in the middle, which is no
   * weight, and moves towards either. Its buttons are named for the ends, and it has no
   * field to type in: a number does not say which end it is towards.
   */
  readonly ends?: readonly [low: string, high: string];
  /**
   * The thing that is weighed, where it has a drawing to stand beside its name: by the id
   * and the family the API gives. It is drawn in outline while it counts for nothing.
   */
  readonly thing?: ThingOf;
  /**
   * What is seen of its name, where the whole of it would say again what stands over it:
   * the start of it, as the start of the name of a short button is what is seen of it.
   * Whoever hears the page hears the whole. Left out, the whole of its name is seen.
   */
  readonly seen?: string;
  /**
   * The id the API gives the vibe whose slider it is. The one picture of each of its ends
   * is chosen by it, and stands on the button at that end of the slider. Left out, as of
   * the slider of a measurement, no end has a picture of its own.
   */
  readonly vibe?: string | null | undefined;
  /**
   * What the two buttons of the slider of a vibe that runs one way bear. Left out, as a
   * page leaves it, it is what `look.ts` chooses.
   */
  readonly oneWay?: EndsOfOneWay;
}

/**
 * What is seen of a name: the start of it that was asked for, where it is the start of it,
 * and else the whole. What is seen is always in what is heard, in the order it is seen in.
 */
export function seenOf(whole: string, seen?: string): string {
  return seen !== undefined && whole.startsWith(seen) ? seen : whole;
}

const hundredths = (weight: number) => Math.round(weight * 100);

/** What a slider of two ends says its value is, in words: which end, and how far towards it. */
export function towardsInWords(value: number, [low, high]: readonly [string, string]): string {
  if (value === 0) return SLIDER.middle;
  return SLIDER.towards(value < 0 ? low : high, Math.abs(value));
}

/** What the style sheet needs of the button at an end of a scale: its picture, the same pressed, and where they are cut. */
function ofAnEnd(): CSSProperties {
  const { up, down } = picturesOf("plain", false);
  const [top, right, foot, left] = cutOf(up) ?? [0, 0, 0, 0];
  return {
    "--art": `url("${pictureOf(up)}")`,
    "--art-down": `url("${pictureOf(down)}")`,
    "--cut-top": top,
    "--cut-right": right,
    "--cut-foot": foot,
    "--cut-left": left,
  } as CSSProperties;
}

interface EndProps {
  /** The one picture of the end, which is chosen by the id of its vibe. */
  readonly picture: Drawing;
  /**
   * The name the API gives the end, which stands under its picture. Left out of an end of
   * a vibe that runs one way, which the API gives no name: its picture stands alone.
   */
  readonly end?: string;
  /** The name of the button: what is weighed, and which way a press moves it. */
  readonly name: string;
  /** True at the end it leads to: it says that it is off, and is not switched off, so that it keeps the focus. */
  readonly off: boolean;
  readonly onPress: () => void;
}

/**
 * The button at an end of the slider of a vibe: the one picture of that end of the vibe,
 * and under it the name of the end where it has one. The picture is dress, and says what
 * the end is: neither end is the better one, and the two are drawn alike.
 */
function End({ picture, end, name, off, onPress }: EndProps) {
  return (
    <button
      type="button"
      className={`${styles.end} target`}
      aria-label={name}
      aria-disabled={off ? true : undefined}
      data-named={end !== undefined}
      onClick={onPress}
    >
      <span className={styles.face} style={ofAnEnd()}>
        <Art name={picture} alt="" />
        {end === undefined ? null : <span className={styles.named}>{end}</span>}
      </span>
    </button>
  );
}

/** What a slider at rest is handed: what it would weigh, the steps the API serves, and where its scale is said. */
type AtRest = Pick<Props, "label" | "limits" | "scale" | "seen">;

/**
 * The slider of a thing that is switched off, at rest: its name, its two buttons down, its
 * gauge empty and its figure at nought. It is made as the slider is made and so is of the
 * same size, to keep the room of the slider while there is none: turned on, the slider
 * stands where this stood, and nothing on the page moves for it.
 *
 * It is a drawing. Nothing of it takes a press, a key or the focus, and it says nothing to
 * whoever hears the page: the switch of the thing says that it is off. Where the slider
 * says what its scale means under itself, so does this. Its words are quieter, in the
 * colour a button that does nothing just now has its words in.
 */
export function SliderAtRest({ label, limits, scale, seen }: AtRest) {
  const unit = Math.max(1, hundredths(limits.weight_unit));
  const step = Math.max(unit, hundredths(limits.weight_step_small));
  return (
    <div className={styles.slider} aria-hidden="true" data-rests="">
      <span className={styles.label}>
        <span className={styles.name} data-reads={holdsAFigure(seenOf(label, seen))}>
          {seenOf(label, seen)}
        </span>
      </span>
      <div className={styles.row} data-ends="false">
        <StepButton way="less" name={SLIDER.less(label)} disabled onPress={nothing} />
        <span className={styles.gauge}>
          <Gauge counts={0} steps={stepsOf(step)} alone={false} />
        </span>
        <StepButton way="more" name={SLIDER.more(label)} disabled onPress={nothing} />
        <span className={`${styles.number} ${styles.rests}`}>0</span>
      </div>
      {scale === undefined ? <p className={styles.scale}>{SLIDER.range}</p> : null}
    </div>
  );
}

/** What a press does to a button of a slider at rest. */
const nothing = () => undefined;

/** The value that was sent, and the count of answers when it was: it waits for the next one. */
interface Sent {
  readonly value: number;
  readonly version: number;
}

/**
 * How much something counts, from 0 to 100, drawn as Town Map draws a weight: a gauge of
 * steps that fill, with a weight standing where the filling has come to.
 *
 * The gauge is drawn and says nothing. What a person moves is a range input that lies over
 * it, as wide as the gauge and with a thumb as wide as the weight, so that the weight
 * stands where the thumb is. The input is the browser's own, and is what a keyboard and a
 * screen reader meet.
 *
 * It can be set three ways, and none needs dragging: the slider itself, by
 * pointer or by the arrow keys, a button at each of its ends, and a field to
 * type a number in.
 *
 * The slider of a vibe has the one picture of each end of the vibe on the
 * button at that end, and the two are opposites. Any other slider has a
 * minus and a plus.
 *
 * It shows its new value at once and sends it once: on release of the
 * pointer, or a moment after the last key or press. It never sends while it
 * is dragged, so dragging does not flood the API.
 *
 * What a person has set and not yet sent is theirs, and no answer takes it
 * away. What was sent stands until the next answer, and a new value is held
 * against it, so that a slider put back before the answer comes is sent too.
 *
 * What 0 and 100 mean is drawn where it can be seen: under the slider, or
 * once for a group of them by whatever holds the group.
 */
export function WeightSlider({
  value,
  limits,
  label,
  onCommit,
  version,
  scale,
  ends,
  thing,
  seen,
  vibe,
  oneWay = ENDS_OF_ONE_WAY,
}: Props) {
  const id = useId();
  const [atLow, atHigh] = picturesAtEnds(vibe);
  // A vibe whose ends nobody has drawn has a plot with nothing on it at both, which says
  // nothing of what a press does: the two signs do.
  const pictured = ends === undefined && oneWay === "pictured" && atLow !== NO_PICTURE && atHigh !== NO_PICTURE;
  const scaleId = scale ?? `${id}-range-hint`;
  const least = ends === undefined ? 0 : -100;
  const within = (given: number) => Math.min(100, Math.max(least, given));
  const unit = Math.max(1, hundredths(limits.weight_unit));
  const step = Math.max(unit, hundredths(limits.weight_step_small));
  const [moved, setMoved] = useState<number | null>(null);
  const [sent, setSent] = useState<Sent | null>(null);
  const [dragging, setDragging] = useState(false);
  const [typed, setTyped] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // What was sent stands until an answer comes. Then the slider is the API's again.
  const waiting = sent !== null && sent.version === version ? sent.value : null;
  const standing = waiting ?? hundredths(value);
  const draft = moved ?? standing;
  const latest = useRef({ draft, standing, version, onCommit });

  useEffect(() => {
    latest.current = { draft, standing, version, onCommit };
  });

  useEffect(
    () => () => {
      if (timer.current !== null) clearTimeout(timer.current);
    },
    [],
  );

  const send = (next: number) => {
    if (timer.current !== null) clearTimeout(timer.current);
    timer.current = null;
    setMoved(null);
    // Held against what is on its way, where something is, and not against the spec alone.
    if (next === latest.current.standing) return;
    setSent({ value: next, version: latest.current.version });
    latest.current.onCommit(next / 100);
  };

  const soon = (next: number) => {
    if (timer.current !== null) clearTimeout(timer.current);
    timer.current = setTimeout(() => send(next), SETTLE_MS);
  };

  const snapped = (next: number) => within(Math.round(next / unit) * unit);

  const released = () => {
    if (!dragging) return;
    setDragging(false);
    send(latest.current.draft);
  };

  const move = (by: number) => {
    const next = snapped(draft + by);
    // At an end, a button does nothing. It is said to be off and is not switched off: a
    // button that is switched off while it has the focus leaves the focus on nothing.
    if (next === draft) return;
    setMoved(next);
    soon(next);
  };

  const typedIn = () => {
    if (typed === null) return;
    const number = Number(typed.trim());
    setTyped(null);
    if (typed.trim() === "" || !Number.isFinite(number)) return;
    send(snapped(number));
  };

  const onFieldKey = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    typedIn();
  };

  // A press of the plus fills a step. A scale has half as many each way from its middle.
  const steps = ends === undefined ? stepsOf(step) : eachWay(stepsOf(step));
  // The thumb of the input is as wide as the weight that is drawn, so that the two stand
  // together, and as high as the gauge, which is its steps with the weight standing on them.
  const weight = sizeOf("ui-weight");
  const thumb = {
    "--thumb": weight.width,
    "--high": weight.height + sizeOf("gauge-cell").height - 1,
  } as CSSProperties;

  return (
    <div className={styles.slider}>
      <label className={styles.label} htmlFor={`${id}-range`}>
        {/* The drawing is dress. The name beside it is what is read, and what names the slider. */}
        {thing === undefined ? null : <Drawn thing={thing} state={draft === 0 ? "off" : "said"} />}
        <span className={styles.name} data-reads={holdsAFigure(seenOf(label, seen))}>
          {seenOf(label, seen)}
        </span>
      </label>
      <div className={styles.row} data-ends={ends !== undefined}>
        {ends !== undefined ? (
          <End
            picture={atLow}
            end={ends[0]}
            name={SLIDER.toward(label, ends[0])}
            off={draft <= least}
            onPress={() => move(-step)}
          />
        ) : pictured ? (
          <End picture={atLow} name={SLIDER.less(label)} off={draft <= least} onPress={() => move(-step)} />
        ) : (
          <StepButton way="less" name={SLIDER.less(label)} off={draft <= least} onPress={() => move(-step)} />
        )}
        <span className={styles.gauge} style={thumb}>
          <Gauge counts={draft} steps={steps} ends={ends} alone={false} />
          <input
            id={`${id}-range`}
            className={`${styles.range} target`}
            type="range"
            min={least}
            max={100}
            step={unit}
            value={draft}
            // Where the start of its name is all that is seen, the whole of it is said here.
            aria-label={seenOf(label, seen) === label ? undefined : label}
            aria-valuetext={ends === undefined ? undefined : towardsInWords(draft, ends)}
            aria-describedby={scaleId}
            onChange={(event) => {
              const next = snapped(Number(event.currentTarget.value));
              setMoved(next);
              // While the pointer is down nothing is sent. A key is sent a moment after the last.
              if (!dragging) soon(next);
            }}
            onPointerDown={() => setDragging(true)}
            onPointerUp={released}
            onPointerCancel={released}
            onBlur={released}
          />
        </span>
        {ends !== undefined ? (
          <End
            picture={atHigh}
            end={ends[1]}
            name={SLIDER.toward(label, ends[1])}
            off={draft >= 100}
            onPress={() => move(step)}
          />
        ) : pictured ? (
          <End picture={atHigh} name={SLIDER.more(label)} off={draft >= 100} onPress={() => move(step)} />
        ) : (
          <StepButton way="more" name={SLIDER.more(label)} off={draft >= 100} onPress={() => move(step)} />
        )}
        {ends === undefined ? (
          <input
            className={`${styles.number} target`}
            type="text"
            inputMode="numeric"
            autoComplete="off"
            aria-label={SLIDER.number(label)}
            aria-describedby={scaleId}
            value={typed ?? String(draft)}
            onChange={(event) => setTyped(event.currentTarget.value)}
            onBlur={typedIn}
            onKeyDown={onFieldKey}
          />
        ) : (
          // Where the slider stands, in words: a slider of two ends has no number to read.
          <output className={styles.stands} htmlFor={`${id}-range`}>
            {towardsInWords(draft, ends)}
          </output>
        )}
      </div>
      {scale === undefined ? (
        <p id={scaleId} className={styles.scale}>
          {ends === undefined ? SLIDER.range : SLIDER.twoEnds}
        </p>
      ) : null}
    </div>
  );
}
