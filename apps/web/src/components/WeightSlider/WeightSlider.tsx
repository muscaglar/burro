"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";

import { SLIDER } from "@/content/settings";
import type { ServedLimits } from "@/lib/api/schema";

import styles from "./WeightSlider.module.css";

/** How long after the last key or press a change is sent. */
export const SETTLE_MS = 150;

interface Props {
  /** The weight as the API returned it, from 0 to 1. */
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
}

const hundredths = (weight: number) => Math.round(weight * 100);
const within = (value: number) => Math.min(100, Math.max(0, value));

/** The value that was sent, and the count of answers when it was: it waits for the next one. */
interface Sent {
  readonly value: number;
  readonly version: number;
}

/**
 * How much something counts, from 0 to 100.
 *
 * It can be set three ways, and none needs dragging: the slider itself, by
 * pointer or by the arrow keys, a minus and a plus button, and a field to
 * type a number in.
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
export function WeightSlider({ value, limits, label, onCommit, version, scale }: Props) {
  const id = useId();
  const scaleId = scale ?? `${id}-range-hint`;
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

  return (
    <div className={styles.slider}>
      <label className={styles.label} htmlFor={`${id}-range`}>
        {label}
      </label>
      <div className={styles.row}>
        <button
          type="button"
          className={`${styles.step} target`}
          aria-label={SLIDER.less(label)}
          aria-disabled={draft <= 0 ? true : undefined}
          onClick={() => move(-step)}
        >
          <span aria-hidden="true">−</span>
        </button>
        <input
          id={`${id}-range`}
          className={`${styles.range} target`}
          type="range"
          min={0}
          max={100}
          step={unit}
          value={draft}
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
        <button
          type="button"
          className={`${styles.step} target`}
          aria-label={SLIDER.more(label)}
          aria-disabled={draft >= 100 ? true : undefined}
          onClick={() => move(step)}
        >
          <span aria-hidden="true">+</span>
        </button>
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
      </div>
      {scale === undefined ? (
        <p id={scaleId} className={styles.scale}>
          {SLIDER.range}
        </p>
      ) : null}
    </div>
  );
}
