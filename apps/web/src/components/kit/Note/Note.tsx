"use client";

import { useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import { SOURCE } from "@/content/search";

import { asStyle } from "../Art/Art";
import styles from "./Note.module.css";

interface Props {
  /** What the source says: the names of the sources, the date of the data, and what else the page has to say of it. */
  readonly children: ReactNode;
  /** What the key says. "Source", where it is told nothing. It does not change when it opens. */
  readonly label?: string;
  /** A name for the key where the label alone would not say enough: "Source for reason 1". */
  readonly name?: string;
  /** Whether it is open, where the page decides. Left out, it keeps its own. */
  readonly open?: boolean;
  readonly openAtFirst?: boolean;
  readonly onToggle?: (open: boolean) => void;
  /** A class of whatever lays the note out. It sets where the note stands, never how it is drawn. */
  readonly className?: string;
}

/**
 * The key of a source. It ends a sentence or a figure, and opens what it is the source of,
 * in place, under what it stands beside. Nothing appears under the pointer. It stays open
 * until it is closed, and Escape closes it and puts the focus back on the key.
 *
 * It is a small control, as "Source" has always been: 24 px at the least, and clear of the
 * next. What it opens is read, and is set in the reading face.
 */
export function Note({ children, label = SOURCE.button, name, open, openAtFirst = false, onToggle, className }: Props) {
  const [own, setOwn] = useState(openAtFirst);
  const isOpen = open ?? own;
  const id = useId();
  const key = useRef<HTMLButtonElement>(null);

  const set = (next: boolean) => {
    setOwn(next);
    onToggle?.(next);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Escape" || !isOpen) return;
    // The innermost open one closes. One that holds it stays as it is.
    event.stopPropagation();
    set(false);
    key.current?.focus();
  };

  return (
    // The keys are heard here for what is inside: the button itself is the control.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div className={[styles.note, className].filter(Boolean).join(" ")} onKeyDown={onKeyDown}>
      <button
        ref={key}
        type="button"
        className={`${styles.key} target-min`}
        aria-expanded={isOpen}
        aria-controls={id}
        aria-label={name}
        onClick={() => set(!isOpen)}
      >
        <span className={styles.drawn} style={asStyle("ui-key")} aria-hidden="true" />
        <span>{label}</span>
      </button>
      <div id={id} className={styles.opened} hidden={!isOpen}>
        {isOpen ? children : null}
      </div>
    </div>
  );
}
