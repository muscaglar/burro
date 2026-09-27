"use client";

import { useId, useLayoutEffect, useRef, type CSSProperties, type MouseEvent } from "react";

import { TRAY } from "@/content/compare";
import { TOWNS } from "@/content/towns";
import { MOST_COMPARED } from "@/lib/compare/list";
import { useCompare } from "@/lib/session/session";
import { paths } from "@/lib/paths";
import { DOUBLE_PRESS_MS } from "@/lib/sight";

import { pictureOf, sizeOf } from "../kit/drawings";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
import { Town } from "../Town/Town";
import styles from "./CompareTray.module.css";
import { useDrawnFrom } from "./drawnFrom";
import {
  BAR_SAYS,
  BAR_SAYS_OF_ITS_TOWNS,
  CLEAR_STANDS,
  WAY_TO_COMPARE,
  type BarSaysOfItsTowns,
  type ClearStands,
} from "./look";
import { marksIn } from "./town";

interface Props {
  /** Whether the bar has the way to take every area out at once. Left out, it is what `look.ts` chooses. */
  readonly clears?: ClearStands;
  /** What the bar says of its towns. Left out, it is what `look.ts` chooses, which is nothing. */
  readonly says?: BarSaysOfItsTowns;
}

/**
 * What the tray says of how many areas are chosen: what to do next while one is chosen,
 * how much room is left while there are enough, and that four is the most. It is said in
 * sight, and aloud when it changes.
 */
export function trayStatus(count: number, full: boolean): string {
  if (count === 0) return "";
  if (count === 1) return TRAY.one;
  return full ? TRAY.full : TRAY.room(MOST_COMPARED - count);
}

/** What the style sheet needs of the cross to draw it: its picture, and its size in art pixels. */
function ofTheCross(): CSSProperties {
  const { width, height } = sizeOf("ui-cross");
  return { "--art": `url("${pictureOf("ui-cross")}")`, "--w": width, "--h": height } as CSSProperties;
}

/**
 * The cross that takes the focus when the area of this one is taken out: of the area that
 * stood after it, or else of the one before. `null` where it was the last area of the bar.
 */
function crossBeside(item: HTMLElement | null): HTMLElement | null {
  const all = [...(item?.parentElement?.children ?? [])];
  const at = item === null ? -1 : all.indexOf(item);
  if (at < 0) return null;
  for (const other of [...all.slice(at + 1), ...all.slice(0, at).reverse()]) {
    const cross = other.querySelector<HTMLElement>("button");
    if (cross !== null) return cross;
  }
  return null;
}

/**
 * The areas chosen to compare, and the one button that compares them.
 *
 * It takes no room until an area is chosen: what the page is for comes first. It then
 * stays at the foot of the screen, so that it is never a long way from the button that was
 * pressed. It is the one thing that stays there, and is a box of the look.
 *
 * It has four places, which is the most a comparison takes. Each area that is chosen has
 * one, with its town, its name and the cross that takes it out again, in the order they
 * were chosen and in no other. Each place that is left is kept empty, so that the bar is as
 * wide with one area as with four and nothing in it moves when an area is added. Nothing
 * is said of the towns: what a town is, is said in the key to the drawings and at the head
 * of the page of an area, and one line of the look has the bar say it once, as it did.
 * Nothing of the bar marks one area out: nobody wins.
 *
 * It says what to do next, in sight and aloud: with one area chosen, to choose one more.
 * With two to four it has its one button, which leads to the comparison. The link holds
 * the slugs of the areas and nothing else. It is followed when it is pressed and not
 * fetched before. What it says is what a button that can add no more is described by.
 *
 * After what it says stands what takes every area out at once, "Clear", once there are two
 * areas or more: the drawing of a cross and the word, on the line of what the bar says, as
 * the way that takes an area out of a comparison is drawn. It is small and quiet, so that
 * the bar has one button of the size of a main control, and it stands in the line so that
 * the bar is no higher for it. On a narrow screen the bar has no line to spare, and it is
 * not drawn: the style sheet says so. One line of the look takes it away everywhere.
 *
 * The town of an area is drawn from what the button that chose it handed over, or the list
 * of results it stood in. Of an area nothing was handed of no town is drawn: a town that
 * is left blank says that its parts are not known, which would be untrue of it.
 *
 * What is pressed in it and then goes hands the focus on, so that the focus is never left
 * on nothing: the cross of an area to the cross beside it, and the last cross and "Clear"
 * to the bar itself, which is no stop of its own. The page is not moved under the person: the bar
 * that is closed stands at the foot of the page, and they may be anywhere on it.
 *
 * The bar comes, and grows, at the foot of the screen, which may be where the button that
 * was pressed stands: it is then under the pointer, where that button was. A second press
 * that follows at once, as the second of a double press does, was aimed at that button:
 * for as long as a browser may count it so, it lands on nothing of the bar. A press of its
 * own lands at once, and so does a key.
 */
export function CompareTray({ clears = CLEAR_STANDS, says = BAR_SAYS_OF_ITS_TOWNS }: Props = {}) {
  const id = useId();
  const tray = useRef<HTMLElement>(null);
  const { chosen, enough, full, toggle, clear } = useCompare();
  const handed = useDrawnFrom();
  /** Gives the focus to what stays, before what has it goes. */
  const handOn = (to: HTMLElement | null) => (to ?? tray.current)?.focus({ preventScroll: true });
  const closed = chosen.length === 0;
  const status = trayStatus(chosen.length, full);
  // Each area with where it sits, where that was handed over.
  const places = chosen.map((area) => ({ area, marks: marksIn(handed, area.area_id) }));
  const drawsATown = handed !== null && places.some(({ marks }) => marks !== null);
  // How many areas it held as it was last drawn, and when it last came or grew.
  const held = useRef(0);
  const grew = useRef<number | null>(null);
  useLayoutEffect(() => {
    if (chosen.length > held.current) grew.current = Date.now();
    held.current = chosen.length;
  }, [chosen.length]);
  /** A press the browser counts as the second or a later one of a double press, on a bar that has only just come or grown. */
  const holdOffTheSecondPress = (event: MouseEvent<HTMLElement>) => {
    if (event.detail < 2 || grew.current === null || Date.now() - grew.current > DOUBLE_PRESS_MS) return;
    event.preventDefault();
    event.stopPropagation();
  };
  return (
    <Frame
      as="section"
      ref={tray}
      // Until an area is chosen it is a frame that draws nothing: no edge, no ground and no shadow.
      kind={closed ? "plain" : "box"}
      bare
      className={styles.tray}
      data-closed={closed}
      data-towns={drawsATown}
      // It holds a heading once it holds an area. Until then it is named without one: a
      // heading with nothing under it leads a person who goes by headings to nothing, and the
      // bar still says what it is as it takes the focus from the last area that goes.
      aria-labelledby={closed ? undefined : `${id}-title`}
      aria-label={closed ? TRAY.title : undefined}
      // It can be given the focus by what is pressed in it and goes, and is no stop of its own.
      tabIndex={-1}
      // Heard on the way down, before whatever was pressed hears of it.
      onClickCapture={holdOffTheSecondPress}
    >
      <div className={styles.about}>
        {closed ? null : (
          <h2 id={`${id}-title`} className={styles.title}>
            {TRAY.title}
          </h2>
        )}
        {/* Where the look has it said: what a town is, and that it is no picture of the
            place, once, of every town of the bar. */}
        {drawsATown && says === "line" ? (
          <p className={styles.towns} data-says="towns">
            {TOWNS.short}
          </p>
        ) : null}
      </div>
      {closed ? null : (
        <div className={styles.places}>
          <ul className={styles.chosen}>
            {places.map(({ area, marks }) => (
              <li key={area.area_id} className={styles.area}>
                {/* The town is handed the name to say and not to draw, and no rank and no fit. */}
                {handed === null || marks === null ? null : (
                  <Town marks={marks} meta={handed.release} of={area.name} className={styles.town} />
                )}
                <span className={styles.name} data-says="name">
                  {area.name}
                </span>
                <button
                  type="button"
                  className={`${styles.remove} target-min`}
                  aria-label={TRAY.remove(area.name)}
                  onClick={(event) => {
                    handOn(crossBeside(event.currentTarget.closest("li")));
                    toggle(area);
                  }}
                >
                  {/* The cross is a drawing. The letter under it is what it stands for, and is not drawn. */}
                  <span className={styles.cross} style={ofTheCross()} aria-hidden="true">
                    ×
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {/* A place for each area there is still room for. It is drawn for the eye: how much
              room is left is said in words, where the bar says what it says. */}
          {Array.from({ length: MOST_COMPARED - chosen.length }, (_, at) => (
            <span key={at} className={styles.plot} data-place="empty" aria-hidden="true" />
          ))}
        </div>
      )}
      <div className={styles.next}>
        <div className={styles.says}>
          {/* It is on the page before anything is chosen, so that a screen reader is told when it first says something. */}
          <p id={BAR_SAYS} className={styles.status} role="status">
            {status}
          </p>
          {/* One area is taken out by its own cross: there is something to clear once there are two. */}
          {!enough || clears === "none" ? null : (
            <button
              type="button"
              className={`${styles.clear} target-min`}
              aria-label={TRAY.clearNamed}
              onClick={() => {
                // Every area goes, and the bar with them: the focus is left on the bar, and never on nothing.
                handOn(null);
                clear();
              }}
            >
              {/* The cross is a drawing, and is dress: the word says what the press does. */}
              <span className={styles.cross} style={ofTheCross()} aria-hidden="true" />
              {TRAY.clear}
            </button>
          )}
        </div>
        {enough ? (
          <Press kind={WAY_TO_COMPARE} href={paths.compare(chosen.map((area) => area.slug))}>
            {TRAY.go(chosen.length)}
          </Press>
        ) : null}
      </div>
    </Frame>
  );
}
