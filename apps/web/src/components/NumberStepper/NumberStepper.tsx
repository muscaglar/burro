"use client";

import { useId, useState, type KeyboardEvent } from "react";

import styles from "./NumberStepper.module.css";

interface Props {
  readonly label: string;
  /** The number as the API returned it. `null` when none is set. */
  readonly value: number | null;
  /** The limits, said under the field. */
  readonly hint?: string;
  /** Why the last number was not taken, in words. */
  readonly problem?: string | null;
  /** What to say when what was typed is no number at all. */
  readonly notANumber: string;
  /** When given, a typed number is brought within these before it is sent. */
  readonly keptWithin?: { readonly least: number; readonly most: number };
  readonly less: string;
  readonly more: string;
  /** False while there is nothing to step from. */
  readonly canStep?: boolean;
  /** A number typed in, sent when the field is left or Enter is pressed. */
  readonly onCommit: (value: number) => void;
  /** A step down or up. The API works out where it lands. */
  readonly onStep: (step: "down_small" | "up_small") => void;
  /** A number that changes with every answer from the API. */
  readonly version: number;
}

/** The number that was sent, and the count of answers when it was: it waits for the next one. */
interface Sent {
  readonly number: number;
  readonly version: number;
}

/**
 * A field for a whole number, with a minus and a plus button beside it.
 *
 * A typed number is sent when the field is left, or on Enter, and never key
 * by key: half a number is not a number. A button sends a step, and the
 * field shows where the API says it landed.
 *
 * An answer that comes while a number is being typed leaves the typing
 * alone. It may be the answer to something else, a sentence that was being
 * read, and the digits typed next would be joined to its number and sent.
 */
export function NumberStepper({
  label,
  value,
  hint,
  problem = null,
  notANumber,
  keptWithin,
  less,
  more,
  canStep = true,
  onCommit,
  onStep,
  version,
}: Props) {
  const id = useId();
  // What is being typed is nobody's but the person's until it is sent. No answer touches it.
  const [typed, setTyped] = useState<string | null>(null);
  const [sent, setSent] = useState<Sent | null>(null);
  // The count of answers when a step was last sent. Where a step lands is the API's to say.
  const [stepped, setStepped] = useState<number | null>(null);
  const [unread, setUnread] = useState(false);

  // A number that was sent stands until an answer comes. Then the field is the API's again.
  const waiting = sent !== null && sent.version === version ? sent.number : null;
  const shown = typed ?? String(waiting ?? value ?? "");
  const said = unread ? notANumber : problem;

  const commit = () => {
    if (typed === null) return;
    const text = typed.replace(/[\s,£]/g, "");
    if (text === "") {
      setTyped(null);
      setUnread(false);
      return;
    }
    if (!/^\d+$/.test(text)) {
      setUnread(true);
      return;
    }
    setUnread(false);
    const number = keptWithin
      ? Math.min(keptWithin.most, Math.max(keptWithin.least, Number(text)))
      : Number(text);
    setTyped(null);
    // It is held against the number that is waiting, where one is: a number put back
    // to what the API last said must still be sent, to undo the one on its way. After a
    // step nobody here knows what is on its way, so the number is sent whatever it is.
    if (stepped !== version && number === (waiting ?? value)) return;
    setSent({ number, version });
    setStepped(null);
    onCommit(number);
  };

  const step = (by: "down_small" | "up_small") => {
    setStepped(version);
    onStep(by);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    commit();
  };

  const described = [hint ? `${id}-hint` : null, said ? `${id}-problem` : null]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.stepper}>
      <label className={styles.label} htmlFor={`${id}-field`}>
        {label}
      </label>
      <div className={styles.row}>
        <button
          type="button"
          className={`${styles.step} target`}
          aria-label={less}
          disabled={!canStep}
          onClick={() => step("down_small")}
        >
          <span aria-hidden="true">−</span>
        </button>
        <input
          id={`${id}-field`}
          className={`${styles.field} target`}
          type="text"
          inputMode="numeric"
          autoComplete="off"
          value={shown}
          aria-describedby={described || undefined}
          aria-invalid={said ? true : undefined}
          onChange={(event) => {
            setTyped(event.currentTarget.value);
            if (unread) setUnread(false);
          }}
          onBlur={commit}
          onKeyDown={onKeyDown}
        />
        <button
          type="button"
          className={`${styles.step} target`}
          aria-label={more}
          disabled={!canStep}
          onClick={() => step("up_small")}
        >
          <span aria-hidden="true">+</span>
        </button>
      </div>
      {hint ? (
        <p id={`${id}-hint`} className={styles.hint}>
          {hint}
        </p>
      ) : null}
      {said ? (
        <p id={`${id}-problem`} className={styles.problem} role="alert">
          {said}
        </p>
      ) : null}
    </div>
  );
}
