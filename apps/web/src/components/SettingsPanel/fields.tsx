"use client";

import { useId, type ReactNode } from "react";

import { SWITCH } from "@/content/settings";

import { holdsAFigure } from "../kit/reads";
import type { ThingOf } from "../kit/Thing/drawn";
import { Drawn } from "../kit/Thing/Thing";
import { seenOf } from "../WeightSlider/WeightSlider";
import { ofAChoice } from "./drawn";
import styles from "./SettingsPanel.module.css";

interface Option<Value extends string> {
  readonly value: Value;
  readonly label: string;
}

interface RadiosProps<Value extends string> {
  readonly legend: string;
  /**
   * What is seen of what is asked, where the whole of it would say again what stands over
   * it: the start of it. Whoever hears the page hears the whole. Left out, all is seen.
   */
  readonly seen?: string;
  readonly options: readonly Option<Value>[];
  readonly value: Value;
  readonly onChange: (value: Value) => void;
  /** Why the last choice was not taken, in words. */
  readonly problem?: string | null;
  /**
   * True where what a choice says runs to a sentence: it is then set in the reading face.
   * Left out, it is a short label and is set in the face of names. Words that hold a
   * figure are set in the reading face whatever is said here.
   */
  readonly reads?: boolean;
  /** The thing that is chosen of, where it has a drawing to stand before what is asked. */
  readonly thing?: ThingOf;
  /**
   * True where the choices stand side by side and each is as wide as the next, as Town
   * Map's two buttons of renting and buying do. Left out, each is as wide as its words.
   */
  readonly even?: boolean;
  /**
   * True where there is nothing to choose of yet, as of a thing that is switched off: the
   * choices are drawn at rest, in the room they have while one can be made. None is
   * chosen, nothing of them takes a press, a key or the focus, and whoever hears the page
   * hears nothing of them.
   */
  readonly rests?: boolean;
}

/**
 * A choice of one among a few, as native radio buttons in a group with a name. Each is
 * drawn as Town Map draws a button, and the one that is chosen is amber, with its lamp lit.
 *
 * The radio button is the browser's own, and is laid over the whole of the button that is
 * drawn: it takes the press, the arrow keys and the ring of the focus, and says that it
 * is chosen to whoever hears the page.
 *
 * At rest it is made of the same parts, so that it is of the same size, and is switched
 * off whole: each choice is drawn pressed, as a button that is off is.
 */
export function Radios<Value extends string>({
  legend,
  seen,
  options,
  value,
  onChange,
  problem = null,
  reads = false,
  thing,
  even = false,
  rests = false,
}: RadiosProps<Value>) {
  const id = useId();
  return (
    <fieldset
      className={styles.radios}
      // Where the start of what is asked is all that is seen, the whole of it is said here.
      aria-label={seenOf(legend, seen) === legend ? undefined : legend}
      aria-describedby={problem ? `${id}-problem` : undefined}
      // What is switched off whole holds nothing a keyboard could come to.
      disabled={rests}
      aria-hidden={rests ? true : undefined}
      data-rests={rests ? "" : undefined}
    >
      <legend className={styles.legend} data-reads={holdsAFigure(seenOf(legend, seen))}>
        <span className={styles.line}>
          {thing === undefined ? null : <Drawn thing={thing} state="said" />}
          <span>{seenOf(legend, seen)}</span>
        </span>
      </legend>
      <div className={styles.options} style={ofAChoice()} data-even={even}>
        {options.map((option) => (
          <label key={option.value} className={`${styles.choice} target`}>
            <input
              type="radio"
              name={id}
              value={option.value}
              checked={!rests && option.value === value}
              onChange={() => onChange(option.value)}
            />
            {/* Its lamp is drawn before its words by the style sheet: it is dress, and says nothing. */}
            <span className={styles.face} data-reads={reads || holdsAFigure(option.label)}>
              {option.label}
            </span>
          </label>
        ))}
      </div>
      {problem ? (
        <p id={`${id}-problem`} className={styles.problem} role="alert">
          {problem}
        </p>
      ) : null}
    </fieldset>
  );
}

interface CheckProps {
  readonly label: ReactNode;
  readonly checked: boolean;
  readonly onChange: (checked: boolean) => void;
  readonly hint?: string;
  /** A switch is a thing that is on or off. A checkbox is a thing that is so or not. */
  readonly as?: "checkbox" | "switch";
}

/**
 * A thing that is so or not, drawn as a square that is ticked, and a thing that is on or
 * off, which is a switch. Each is the browser's own checkbox, and says what one says.
 *
 * A SWITCH SAYS WHICH IT IS IN A WORD. It is drawn as a button of the look, with a lamp
 * and the word "On" or "Off": on, it is amber and its lamp is lit, as what is chosen is
 * everywhere in the look. So it is told by its word, by its lamp and by its colour. The
 * word is for the eye: whoever hears the page hears of the switch itself that it is on.
 * The checkbox is laid over the whole of the face, and is clear.
 */
export function Check({ label, checked, onChange, hint, as = "checkbox" }: CheckProps) {
  const id = useId();
  const box = (
    <input
      type="checkbox"
      role={as === "switch" ? "switch" : undefined}
      checked={checked}
      aria-describedby={hint ? `${id}-hint` : undefined}
      onChange={(event) => onChange(event.currentTarget.checked)}
    />
  );
  return (
    <div className={styles.check}>
      <label className={`${styles.tick} target`}>
        {as === "switch" ? (
          <span className={styles.lever} style={ofAChoice()}>
            {box}
            {/* Its lamp is drawn before its word by the style sheet, as the lamp of a choice is. */}
            <span className={styles.face} data-reads="false" data-says={checked ? "on" : "off"} aria-hidden="true">
              <span className={styles.says}>{checked ? SWITCH.on : SWITCH.off}</span>
            </span>
          </span>
        ) : (
          box
        )}
        <span className={styles.ticked}>{label}</span>
      </label>
      {hint ? (
        <p id={`${id}-hint`} className={styles.hint}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}
