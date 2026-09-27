"use client";

import type { ReactNode, Ref } from "react";

import { LABEL } from "@/content/kit";

import { asStyle } from "../Art/Art";
import type { ThingOf, ThingState } from "../Thing/drawn";
import { Drawn } from "../Thing/Thing";
import styles from "./Label.module.css";
import { ASSUMED_STANDS_ON } from "./look";
import { stateOf } from "./state";

interface Props {
  /** The thing the chip is of: its kind, the id the service gives, and its family. */
  readonly thing: ThingOf;
  /** What it holds, by the names the service gives: a line of words, or the words as the page has set them. */
  readonly says: ReactNode;
  readonly state?: ThingState;
  /**
   * What the state is said of, where it is said of a part: "45 minutes, public transport"
   * is drawn as "assumed: 45 minutes, public transport". Left out, the state is said alone.
   */
  readonly of?: string;
  /**
   * True where the words that were handed in say the state already, as the words of a chip
   * of the search do. The state is then drawn, and is not said a second time.
   */
  readonly stateSaid?: boolean;
  /** Opens the control of the thing. Left out, the chip is words and no button. */
  readonly onOpen?: () => void;
  /** Whether what it opens is open. */
  readonly open?: boolean;
  /** The id of what it opens. */
  readonly controls?: string;
  /** The id of what says more of it. */
  readonly describedBy?: string;
  /** Takes the thing off. Left out, the chip has no cross. */
  readonly onTakeOff?: () => void;
  /** What is taken off, in words, to name the cross: "Leafy". It is needed with `onTakeOff`. */
  readonly named?: string;
  /** What else is pressed on the chip, between its words and its cross: "Turn", of a scale. */
  readonly beside?: ReactNode;
  /**
   * True of a chip that has this moment been added. It drops into its place in four steps
   * and settles, once, where the system says movement is welcome. Elsewhere it is there.
   */
  readonly arrives?: boolean;
  readonly id?: string;
  /** The button that opens, for a page that gives it the focus: what goes hands the focus on to what is beside it. */
  readonly ref?: Ref<HTMLButtonElement>;
}

/**
 * A chip: the small drawing of a thing, what it holds in words, and a cross that takes it
 * off. It wraps and is never cut. It is one press from the control of its thing.
 *
 * Every chip has a solid edge of ink. Its state is said in its words: nothing for what a
 * person said, "assumed" for what nobody said, and "does not count" for what counts for
 * nothing, which has its thing in outline as well. What nobody said may stand on sand too:
 * `look.ts` chooses.
 *
 * The chip stands in a box of its own, which is there before the chip is: so a chip that
 * arrives moves nothing, and moves inside its own box alone.
 */
export function Label({
  thing,
  says,
  state = "said",
  of,
  stateSaid = false,
  onOpen,
  open,
  controls,
  describedBy,
  onTakeOff,
  named,
  beside,
  arrives = false,
  id,
  ref,
}: Props) {
  const said = stateSaid ? null : stateOf(state, of);
  const held = (
    <>
      <Drawn thing={thing} state={state} edged={false} />
      <span className={styles.words}>
        <span className={styles.says}>{says}</span>
        {/* The space is for whoever hears the two as one name. */}
        {said === null ? null : <> <span className={styles.state}>{said}</span></>}
      </span>
    </>
  );
  return (
    <span
      className={styles.label}
      data-state={state}
      data-ground={ASSUMED_STANDS_ON}
      data-kind={thing.kind}
      data-arrives={arrives}
    >
      <span className={styles.chip}>
        {onOpen === undefined ? (
          <span id={id} className={styles.holds}>
            {held}
          </span>
        ) : (
          <button
            ref={ref}
            id={id}
            type="button"
            className={`${styles.holds} ${styles.opens} target`}
            aria-expanded={open}
            aria-controls={controls}
            aria-describedby={describedBy}
            onClick={onOpen}
          >
            {held}
          </button>
        )}
        {beside}
        {onTakeOff === undefined ? null : (
          <button
            type="button"
            className={`${styles.off} target`}
            aria-label={LABEL.takeOff(named ?? (typeof says === "string" ? says : ""))}
            onClick={onTakeOff}
          >
            <span className={styles.cross} style={asStyle("ui-cross")} aria-hidden="true" />
          </button>
        )}
      </span>
    </span>
  );
}
