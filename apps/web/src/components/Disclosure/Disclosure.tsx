"use client";

import { useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import styles from "./Disclosure.module.css";

interface Props {
  /** What the button says. It names what is shown, and does not change when it opens. */
  readonly label: ReactNode;
  /** A name for the button where the label alone would not say enough. */
  readonly name?: string;
  /** Whether it is open, where the page decides. Left out, it keeps its own. */
  readonly open?: boolean;
  readonly openAtFirst?: boolean;
  readonly onToggle?: (open: boolean) => void;
  /** `small` is for a button beside a line of text, such as "Source". */
  readonly size?: "main" | "small";
  readonly className?: string;
  readonly children: ReactNode;
}

/**
 * A button that shows and hides what is under it, in place. Nothing appears
 * on hover. It stays open until it is closed, and Escape closes it and puts
 * the focus back on the button.
 */
export function Disclosure({
  label,
  name,
  open,
  openAtFirst = false,
  onToggle,
  size = "main",
  className,
  children,
}: Props) {
  const [own, setOwn] = useState(openAtFirst);
  const isOpen = open ?? own;
  const id = useId();
  const button = useRef<HTMLButtonElement>(null);

  const set = (next: boolean) => {
    setOwn(next);
    onToggle?.(next);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Escape" || !isOpen) return;
    // The innermost open one closes. One that holds it stays as it is.
    event.stopPropagation();
    set(false);
    button.current?.focus();
  };

  return (
    // The keys are heard here for what is inside: the button itself is the control.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div className={[styles.disclosure, className].filter(Boolean).join(" ")} onKeyDown={onKeyDown}>
      <button
        ref={button}
        type="button"
        className={`${styles.button} ${size === "small" ? `${styles.small} target-min` : "target"}`}
        aria-expanded={isOpen}
        aria-controls={id}
        aria-label={name}
        onClick={() => set(!isOpen)}
      >
        <span className={styles.mark} aria-hidden="true" />
        {label}
      </button>
      <div id={id} className={styles.panel} hidden={!isOpen}>
        {isOpen ? children : null}
      </div>
    </div>
  );
}
