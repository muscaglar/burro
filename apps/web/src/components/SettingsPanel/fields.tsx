"use client";

import { useId, type ReactNode } from "react";

import styles from "./SettingsPanel.module.css";

interface Option<Value extends string> {
  readonly value: Value;
  readonly label: string;
}

interface RadiosProps<Value extends string> {
  readonly legend: string;
  readonly options: readonly Option<Value>[];
  readonly value: Value;
  readonly onChange: (value: Value) => void;
  /** Why the last choice was not taken, in words. */
  readonly problem?: string | null;
}

/** A choice of one among a few, as native radio buttons in a group with a name. */
export function Radios<Value extends string>({
  legend,
  options,
  value,
  onChange,
  problem = null,
}: RadiosProps<Value>) {
  const id = useId();
  return (
    <fieldset className={styles.radios} aria-describedby={problem ? `${id}-problem` : undefined}>
      <legend className={styles.legend}>{legend}</legend>
      <div className={styles.options}>
        {options.map((option) => (
          <label key={option.value} className={`${styles.option} target`}>
            <input
              type="radio"
              name={id}
              value={option.value}
              checked={option.value === value}
              onChange={() => onChange(option.value)}
            />
            <span>{option.label}</span>
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

export function Check({ label, checked, onChange, hint, as = "checkbox" }: CheckProps) {
  const id = useId();
  return (
    <div className={styles.check}>
      <label className={`${styles.option} target`}>
        <input
          type="checkbox"
          role={as === "switch" ? "switch" : undefined}
          checked={checked}
          aria-describedby={hint ? `${id}-hint` : undefined}
          onChange={(event) => onChange(event.currentTarget.checked)}
        />
        <span>{label}</span>
      </label>
      {hint ? (
        <p id={`${id}-hint`} className={styles.hint}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}
