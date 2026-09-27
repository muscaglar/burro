"use client";

import { useId, useLayoutEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import { bringIntoSight } from "@/lib/sight";

import { holdsAFigure } from "../kit/reads";
import styles from "./Disclosure.module.css";
import { BAR_AT_REST, type BarAtRest } from "./look";
import { drawnAs, theArrow } from "./Summary";

interface Props {
  /** What the button says. It names what is shown, and does not change when it opens. */
  readonly label: ReactNode;
  /** A name for the button where the label alone would not say enough. */
  readonly name?: string;
  /** Whether it is open, where the page decides. Left out, it keeps its own. */
  readonly open?: boolean;
  readonly openAtFirst?: boolean;
  readonly onToggle?: (open: boolean) => void;
  /**
   * `main` is a bar that stands alone, as "Share this search" does. `bar` is one of a
   * stack of bars, each from edge to edge of what holds them, as the groups of the
   * settings are. `small` is for a button beside a line of text, such as "Source".
   */
  readonly size?: "main" | "small" | "bar";
  /**
   * True where the button may stand at the foot of what it is seen through, so that what
   * it opens would begin out of sight: it is then brought into sight as a press opens it,
   * as far as it must be and no further. Left out, nothing is moved.
   */
  readonly bring?: boolean;
  readonly className?: string;
  readonly children: ReactNode;
  /**
   * Of a bar: the drawing that stands before its name. It is dress, and is kept from
   * whoever hears the page by what draws it.
   */
  readonly drawn?: ReactNode;
  /**
   * Of a bar: what it holds, in a few words, said on the bar beside its name so that it is
   * read without the bar being opened. It describes the button and is no part of its
   * name. Left out, or `null`, the bar says nothing of what it holds.
   */
  readonly holds?: string | null;
  /** What a bar stands on while it is closed. It is a matter of taste, which `look.ts` chooses: a page hands none. */
  readonly rest?: BarAtRest;
}

/**
 * A button that shows and hides what is under it, in place. Nothing appears
 * on hover. It stays open until it is closed, and Escape closes it and puts
 * the focus back on the button.
 *
 * It is drawn as every bar that folds is: cream, with its name at its near end and its
 * arrow in a cell at its far end, where the eye looks for it. The arrow points down while
 * the fold is closed, at what would open under it, and up while it is open. One of a
 * stack goes from edge to edge of what holds the stack. A main one stands alone: it has
 * an edge of ink and a shadow of its own, and is as wide as what it says unless a page
 * lays it out wider. A small one is no bar: it stands beside a line of text, on a rule of
 * ink, with its mark before its words. Each is amber while it is open, as what is on is,
 * and says so to whoever hears the page.
 *
 * A bar may say what it holds, beside its name. That is heard after the name of the
 * button and whether it is open, as what describes it: the name stays what it was.
 *
 * A short label is set in the face of names. Words that hold a figure are read, and so is
 * a label that is more than words: both are set in the reading face.
 *
 * The button is what takes the press, and it never moves. What is drawn of it is its
 * face: a bar is lit as it is in hand, and where movement is welcome what stands on the
 * face steps with it, one art pixel down and one to the right.
 *
 * Where it is told to, it brings what a press opened into sight once the press has landed.
 * Nothing is moved as it closes, or where the page draws it open of itself.
 *
 * A fold that must open with scripts off is the browser's own: `Folded`, whose bar is a
 * `Summary`. Both are drawn by the sheet that draws this one.
 */
export function Disclosure({
  label,
  name,
  open,
  openAtFirst = false,
  onToggle,
  size = "main",
  bring = false,
  className,
  children,
  drawn,
  holds = null,
  rest = BAR_AT_REST,
}: Props) {
  const [own, setOwn] = useState(openAtFirst);
  const isOpen = open ?? own;
  const id = useId();
  const button = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  /** True from a press that opens it until what it opened has been brought into sight. */
  const pressed = useRef(false);

  const set = (next: boolean) => {
    setOwn(next);
    onToggle?.(next);
  };

  // Before the page is drawn, so that what was opened is first seen where it will stand.
  useLayoutEffect(() => {
    const by = pressed.current;
    pressed.current = false;
    if (!by || !isOpen || !bring) return;
    if (panel.current !== null && button.current !== null) bringIntoSight(panel.current, button.current);
  }, [bring, isOpen]);

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Escape" || !isOpen) return;
    // The innermost open one closes. One that holds it stays as it is.
    event.stopPropagation();
    set(false);
    button.current?.focus();
  };

  const small = size === "small";
  const stacked = size === "bar";
  const said = !small && holds !== null && holds !== "";
  const reads = typeof label !== "string" || holdsAFigure(label);

  return (
    // The keys are heard here for what is inside: the button itself is the control.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div
      className={[styles.disclosure, stacked ? styles.stacked : null, className].filter(Boolean).join(" ")}
      onKeyDown={onKeyDown}
    >
      <button
        ref={button}
        type="button"
        className={drawnAs(small ? "small" : stacked ? "stacked" : "alone")}
        style={small ? undefined : theArrow()}
        data-arrow={small ? undefined : "end"}
        // One of a stack says what it stands on, and is told from every other fold by it.
        data-rest={stacked ? rest : undefined}
        aria-expanded={isOpen}
        aria-controls={id}
        aria-label={name}
        // What a bar holds is no part of its name: the name is what the bar is called.
        aria-labelledby={said && name === undefined ? `${id}-name` : undefined}
        aria-describedby={said ? `${id}-holds` : undefined}
        onClick={(event) => {
          // Not every browser gives the focus to a button that is pressed, and what had the
          // focus may be in what this press closes: it is never left on nothing. What is
          // pressed is in sight already, and the page is not moved for it.
          event.currentTarget.focus({ preventScroll: true });
          pressed.current = !isOpen;
          set(!isOpen);
        }}
      >
        {/* What the button says, and its arrow. Its face and its size are set on it and not
            on the button, so that a page which lays the button out sets neither. The arrow
            is first here and is laid out last: it says nothing, wherever it stands. */}
        <span className={styles.says} data-reads={reads}>
          <span className={styles.mark} aria-hidden="true" />
          {small ? (
            label
          ) : (
            <>
              {drawn === undefined ? null : <span className={styles.drawn}>{drawn}</span>}
              <span className={styles.told}>
                <span id={`${id}-name`} className={styles.named}>
                  {label}
                </span>
                {said ? (
                  <span id={`${id}-holds`} className={styles.holds}>
                    {holds}
                  </span>
                ) : null}
              </span>
            </>
          )}
        </span>
      </button>
      <div ref={panel} id={id} className={styles.panel} hidden={!isOpen}>
        {isOpen ? children : null}
      </div>
    </div>
  );
}
