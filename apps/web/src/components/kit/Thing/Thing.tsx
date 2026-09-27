import { CHIPS } from "@/content/search";

import { asStyle } from "../Art/Art";
import { drawingOf, outlineOf, type ThingOf, type ThingState } from "./drawn";
import styles from "./Thing.module.css";

/** The word for each state. What a person said says what it holds and no more. */
export const STATE_WORD: Readonly<Record<ThingState, string | null>> = {
  said: null,
  assumed: CHIPS.assumed,
  off: CHIPS.off,
};

interface DrawnProps {
  readonly thing: ThingOf;
  readonly state: ThingState;
  /**
   * False where the thing stands in a label, whose words say what nobody said: the thing
   * then has no edge of its own.
   */
  readonly edged?: boolean;
}

/**
 * A thing as it is drawn, for the eye alone: its drawing, and the mark of its state. What
 * nobody said has a solid edge of ink. What counts for nothing is drawn in outline, its
 * colour taken off it: by the drawing of its outline, and where it has none by its own
 * drawing, of which the style sheet keeps the edge.
 */
export function Drawn({ thing, state, edged = true }: DrawnProps) {
  const drawing = drawingOf(thing);
  const outline = state === "off" ? outlineOf(drawing) : null;
  return (
    <span className={styles.thing} data-state={state} data-edged={edged} aria-hidden="true">
      <span
        className={styles.drawing}
        data-cut={state === "off" && outline === null}
        style={asStyle(outline ?? drawing)}
      />
    </span>
  );
}

interface Props extends ThingOf {
  readonly state?: ThingState;
  /**
   * What the thing is, in words: what it holds, as its chip would say it. Its state is
   * said after it. Left out where the words stand beside the drawing, which is then kept
   * from a screen reader: it would be heard twice.
   */
  readonly says?: string;
}

/** What a thing says to whoever hears the page: what it holds, and then its state. */
export function saidOf(says: string, state: ThingState): string {
  const word = STATE_WORD[state];
  return word === null ? says : `${says}, ${word}`;
}

/**
 * The small drawing that stands for a thing of a search: a ticket for a journey, a purse
 * for a budget, a leaf for a leafy place. It draws the picture named for the id it is
 * given, or the picture of its family, or the plain one, and never nothing.
 *
 * It stands beside the words it is for, at its own size. Its state is drawn and is said in
 * words: by the name of the picture, or by the words beside it.
 */
export function Thing({ kind, id, family, state = "said", says }: Props) {
  const drawn = <Drawn thing={{ kind, id, family }} state={state} />;
  if (says === undefined) return drawn;
  return (
    <span className={styles.said} role="img" aria-label={saidOf(says, state)}>
      {drawn}
    </span>
  );
}
