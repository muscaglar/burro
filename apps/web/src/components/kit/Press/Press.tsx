"use client";

import Link from "next/link";
import type { CSSProperties, MouseEvent, ReactNode, Ref } from "react";

import { pictureOf } from "../drawings";
import { holdsAFigure } from "../reads";
import { picturesOf, type PressKind } from "./kinds";
import styles from "./Press.module.css";

/** What a page may say of a button beside what is listed: a mark of its own, by which it finds the button again. */
type Marks = { readonly [mark: `data-${string}`]: string | boolean | undefined };

interface Props extends Marks {
  readonly kind?: PressKind;
  /** With an address it is a link, drawn as a button is. It takes an address the website built, never text. */
  readonly href?: string;
  /**
   * Whether it is on: a choice that is made, as "Renting" is. It is then amber, whatever
   * its kind. Left out of a button that holds no state. A button says so as `aria-pressed`,
   * and a link as the page one is on.
   */
  readonly on?: boolean;
  /** What a press does. A button that is off ignores it. */
  readonly onPress?: (event: MouseEvent<HTMLElement>) => void;
  /**
   * True of a button that does nothing just now: it waits on an answer, or has been pressed
   * until there is nothing left to do. It says that it is off and keeps the focus. Its face
   * is down in its shadow, as far as a press would take it.
   */
  readonly off?: boolean;
  /** True of the button that sends the form it stands in. */
  readonly submits?: boolean;
  /**
   * True where its words run to a sentence: they are then set in the reading face. Left
   * out, they are a short label and are set in the pixel face. Words that hold a figure
   * are set in the reading face whatever is said here.
   */
  readonly reads?: boolean;
  /** The whole name, where what is seen is the start of it: "Compare", and "Compare: Alderwick". */
  readonly name?: string;
  /** Whether what it opens is open, where it opens something. */
  readonly expanded?: boolean;
  /** The id of what it opens. */
  readonly controls?: string;
  /** The id of what says more of it. */
  readonly describedBy?: string;
  readonly id?: string;
  /** A class of whatever lays the button out. It sets where the button stands, never how it is drawn. */
  readonly className?: string;
  /** The button itself, for a page that gives it the focus: what goes hands the focus on to what is beside it. */
  readonly ref?: Ref<HTMLButtonElement> | Ref<HTMLAnchorElement>;
  readonly children: ReactNode;
}

/**
 * A button, or a link drawn as one, as Town Map draws a button: lit from the top left, with
 * a hard shadow. It is a native element, 44 px high at the least.
 *
 * The button is what takes the press, and it never moves or changes size. Inside it is its
 * face, which is what is drawn: a picture cut in nine, with the shadow of the face in it,
 * so that the room of the shadow is the button's own from the start. Under a press the
 * picture gives way to the picture of the button pressed, in which the face has stepped
 * down and to the right into its shadow: and the button stays where it was, so a press
 * lands where it was aimed and what follows the button does not move.
 */
export function Press({
  kind = "plain",
  href,
  on,
  onPress,
  off = false,
  submits = false,
  reads = false,
  name,
  expanded,
  controls,
  describedBy,
  id,
  className,
  ref,
  children,
  ...marks
}: Props) {
  const classes = [styles.press, "target", className].filter(Boolean).join(" ");
  const { up, down } = picturesOf(kind, on === true);
  const drawn = { "--art": `url("${pictureOf(up)}")`, "--art-down": `url("${pictureOf(down)}")` } as CSSProperties;
  const face = (
    <span className={styles.face} data-kind={on === true ? "on" : kind} style={drawn}>
      <span className={styles.says} data-reads={reads || holdsAFigure(children)}>
        {children}
      </span>
    </span>
  );
  if (href !== undefined) {
    return (
      // Which page a person reads next is told to no server ahead of time.
      <Link
        {...marks}
        ref={ref as Ref<HTMLAnchorElement>}
        id={id}
        className={classes}
        href={href}
        prefetch={false}
        aria-label={name}
        aria-current={on === true ? "page" : undefined}
        aria-describedby={describedBy}
        onClick={onPress}
      >
        {face}
      </Link>
    );
  }
  return (
    <button
      {...marks}
      ref={ref as Ref<HTMLButtonElement>}
      id={id}
      type={submits ? "submit" : "button"}
      className={classes}
      aria-label={name}
      aria-pressed={on}
      aria-expanded={expanded}
      aria-controls={controls}
      aria-describedby={describedBy}
      aria-disabled={off ? true : undefined}
      onClick={(event) => {
        if (off) {
          // It is off and not switched off, so it is still pressed: the press does nothing.
          event.preventDefault();
          return;
        }
        onPress?.(event);
      }}
    >
      {face}
    </button>
  );
}
