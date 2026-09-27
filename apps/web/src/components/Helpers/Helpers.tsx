"use client";

import {
  createContext,
  useContext,
  useId,
  useImperativeHandle,
  useRef,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
  type Ref,
} from "react";

import type { Opens } from "@/lib/sight";

import { pictureOf, sizeOf } from "../kit/drawings";
import { picturesOf } from "../kit/Press/kinds";
import styles from "./Helpers.module.css";
import { useWhereItOpens } from "./where";

/**
 * The pictures of a helper, as the style sheet needs them: the button of the look as it
 * stands and pressed, in cream while it is closed and in amber while it is open.
 */
function faceOf(open: boolean): CSSProperties {
  const { up, down } = picturesOf("plain", open);
  return { "--face": `url("${pictureOf(up)}")`, "--face-down": `url("${pictureOf(down)}")` } as CSSProperties;
}

/** The arrow of what opens in place: where it is served from, and its size in art pixels. */
const ARROW = {
  "--arrow": `url("${pictureOf("ui-arrow")}")`,
  "--arrow-w": sizeOf("ui-arrow").width,
  "--arrow-h": sizeOf("ui-arrow").height,
} as CSSProperties;

/** The helper a part stands under: what its button says, and the id of the button, to be named by. */
export interface Under {
  readonly says: string;
  readonly by: string;
}

const Over = createContext<Under | null>(null);

/**
 * The helper a part stands under, or `null` where it stands under none. What a helper
 * opens stands directly under its button, which says what it is: so a part that would say
 * the same over itself says it once. Where the button says its very name the part is named
 * by the button, and where it says another the part keeps its heading for whoever hears
 * the page, and does not draw it.
 *
 * With scripts off no button is drawn, and a part is told of none.
 */
export function useHelper(): Under | null {
  return useContext(Over);
}

/**
 * How a part that stands under a helper is named, for the part that is headed `title`.
 * `drawn`: it stands under no helper, and draws its heading. `heard`: a helper of another
 * name stands over it, and it keeps its heading for whoever hears the page. `named`: the
 * helper over it says its name, and it is named by the helper's button and has no heading.
 */
export function headedUnder(under: Under | null, title: string): "drawn" | "heard" | "named" {
  if (under === null) return "drawn";
  return under.says === title ? "named" : "heard";
}

export interface Helper<Id extends string = string> {
  readonly id: Id;
  /** What its button says. It names what is opened, and does not change when it opens. */
  readonly label: string;
  /** What it opens. It is drawn while the helper is open, and at no other time. */
  readonly children: ReactNode;
}

/** What the page may ask of the helpers, for what it draws of one outside them. */
export interface HelpersHandle {
  /**
   * Closes the helper that is open and puts the focus on its button, as Escape does from
   * inside what it holds. While every helper is closed it does nothing.
   */
  readonly close: () => void;
}

interface Props<Id extends string> {
  /** What the line is, to whoever hears the page. */
  readonly label: string;
  /** The helpers, in the order they stand in. One that has nothing to offer is left out by the page. */
  readonly helpers: readonly Helper<Id>[];
  /** The one that is open. `null` while every one is closed. */
  readonly open: Id | null;
  /** Told which helper is to be open, or `null` when the one that was open is closed. */
  readonly onOpen: (id: Id | null) => void;
  /** A way to close what is open from a part that the page draws for a helper, outside it. */
  readonly ref?: Ref<HelpersHandle>;
  /** Where what a press opens stands. Left out, as the look has chosen. */
  readonly opens?: Opens;
}

/**
 * One line of helpers under the box: each a button, closed until it is
 * pressed, and one open at a time. What the open one holds is drawn under the
 * whole line, or over it where a hand opened it and it has room there and
 * none under: so no helper moves under the hand that pressed it.
 *
 * A helper is a button that says whether it is open, and is drawn as a button
 * of the look is: lit from the top left, with a hard shadow, its face
 * stepping into its shadow under a press while the button stands. Its arrow
 * stands after its words, at its far end, as the arrow of every fold does: it
 * points down while the helper is closed and up while it is open. The one
 * that is open is amber. It says that it is open, and not that it is pressed,
 * so it is drawn here and not by the button of the kit, which says the one
 * with the other. What it opens brings its own box.
 *
 * The button that is pressed has the focus, whatever had it before: what had
 * it may be in what the press closes. It takes the focus where it stands, and the page is not
 * moved for it. Escape closes what is open and puts the focus back on its
 * button, as it does for everything that opens in place, and brings the
 * button into sight where it is not.
 *
 * What a press opens is seen, whole where it fits, and the helper that was
 * pressed stays where it was pressed. The line stands at the foot of the first
 * screen of a phone, and what a helper opened there began under it, out of
 * sight: brought into sight, it took the helper from under the hand. So what a
 * hand opens stands where the whole of it has room, under the line or over
 * it. It comes before the line in the page where it stands over it, so that
 * the keys go down the page as it is drawn. What the keys open stands under
 * the line, where whoever goes by the order of the page finds it, and the
 * whole of it is brought into sight. Nothing is moved for a helper that the
 * page draws open of itself.
 *
 * A button needs a script. So the page as it is built holds everything the
 * helpers hold, for a browser with scripts off, where nothing could open
 * one: an example and a word are in the page, under the line. A browser with
 * scripts on is never shown it.
 *
 * What a helper opens is told which helper it stands under, so that a name
 * is said once: a part headed as its helper is named draws no heading.
 */
export function Helpers<Id extends string>({ label, helpers, open, onOpen, ref, opens }: Props<Id>) {
  const id = useId();
  const buttons = useRef(new Map<Id, HTMLButtonElement>());
  const line = useRef<HTMLDivElement>(null);
  const opened = helpers.find((one) => one.id === open);
  const where = useWhereItOpens(line, `${id}-${open ?? ""}`, open, opens);

  /** The button of the helper takes the focus before what holds it goes, so that it is never left on nothing. */
  const close = () => {
    if (opened === undefined) return;
    const button = buttons.current.get(opened.id);
    button?.focus();
    if (button !== undefined) where.pressed(button, false);
    onOpen(null);
  };
  useImperativeHandle(ref, () => ({ close }));
  if (helpers.length === 0) return null;

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Escape" || opened === undefined) return;
    // What is open inside it has closed already, if anything was: this is the one that is left.
    event.stopPropagation();
    close();
  };

  const theLine = (
      <div key="line" ref={line} className={styles.line} role="group" aria-label={label}>
        {helpers.map((helper) => (
          <button
            key={helper.id}
            ref={(button) => {
              if (button === null) buttons.current.delete(helper.id);
              else buttons.current.set(helper.id, button);
            }}
            // What it opens may be named by it.
            id={`${id}-${helper.id}-way`}
            type="button"
            className={`${styles.helper} target`}
            aria-expanded={helper.id === open}
            aria-controls={`${id}-${helper.id}`}
            onClick={(event) => {
              // Not every browser gives the focus to a button that is pressed, and what had
              // the focus may go with the helper that this press closes. What is pressed is
              // in sight already. A browser brings what takes the focus clear of the foot of
              // the screen, so without this the page moved under the press, in those browsers.
              event.currentTarget.focus({ preventScroll: true });
              // A press by the keys is counted as none by a browser, and a hand's as one.
              where.pressed(event.currentTarget, event.detail > 0);
              onOpen(helper.id === open ? null : helper.id);
            }}
          >
            <span className={styles.face} data-open={helper.id === open} style={faceOf(helper.id === open)}>
              <span className={styles.says}>
                {helper.label}
                {/* The arrow is dress, and stands after the words, at the far end of the helper. */}
                <span className={styles.mark} style={ARROW} aria-hidden="true" />
              </span>
            </span>
          </button>
        ))}
      </div>
  );
  // Each has its place whether or not it is open, so that its button can name it.
  const places = helpers.map((helper) => (
    <div key={helper.id} id={`${id}-${helper.id}`} className={styles.opened} hidden={helper.id !== open}>
      {helper.id === open ? (
        <Over.Provider value={{ says: helper.label, by: `${id}-${helper.id}-way` }}>{helper.children}</Over.Provider>
      ) : null}
    </div>
  ));

  return (
    // The keys are heard here for what is inside: the buttons are the controls.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div className={styles.helpers} onKeyDown={onKeyDown}>
      {/* In the order they are drawn in. Each is told by its key, so that what is open is
          moved from one side of the line to the other, and is not made anew. */}
      {where.side === "over" ? [...places, theLine] : [theLine, ...places]}
      <noscript>
        <div className={styles.unscripted}>
          {helpers.map((helper) => (
            <div key={helper.id} className={styles.opened}>
              {helper.children}
            </div>
          ))}
        </div>
      </noscript>
    </div>
  );
}
