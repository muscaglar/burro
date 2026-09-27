import { STATUS } from "@/content/search";
import { WAIT } from "@/content/wait";
import type { AreaSummary, PreferenceSpec } from "@/lib/api/schema";
import { leadsOf } from "@/lib/search/leads";
import type { Phase, Ranking } from "@/lib/search/state";

import { Frame } from "../kit/Frame/Frame";
import styles from "./StatusLine.module.css";

/**
 * How the line is framed. A `box` is the box of the look, with its double rule. A `slip` is
 * a plain edge of ink with the hard shadow of the look, as the slip that is tied to the foot
 * of the box on the map of a game: it is six art pixels lower than a box. With `none` it
 * stands in no frame of its own, as it does on a narrow screen: it is in the box of the
 * search, which is a box already. A page asks for none where what stands over the answer
 * must give way. Measured at 1440 by 900 where Burro asks which place was meant: in its
 * box the line was 96 px high, and in none it is one line of 24.
 */
export type StatusFrame = "box" | "slip" | "none";

export const FRAMES: readonly StatusFrame[] = ["box", "slip", "none"];

/** The frame the line stands in where the page asks for none. This one line chooses. */
const FRAME: StatusFrame = "box";

/**
 * What becomes of the room of the line while it says nothing, once a search is open. `kept`:
 * it is as high as it is with one line in it, so that nothing under it moves when it next
 * says something, as it was before the line had a frame. `given`: it takes no room, and what
 * stands under it moves when an answer brings it something to say, or takes it away.
 */
export type StatusRoom = "kept" | "given";

export const ROOMS: readonly StatusRoom[] = ["kept", "given"];

/** What becomes of it where the page does not say. This one line chooses. */
const ROOM: StatusRoom = "kept";

/**
 * How the line says what the order means, where what was asked for counts the most. `short`:
 * in one sentence, so that the line is two lines on a phone and the first result is whole on
 * its first screen. `full`: in the sentence that was given as the way the line should read,
 * which says why as well. On a phone that is a third line, and the foot of the first result
 * of a plain search is then 4 px under the first screen.
 */
export type OrderSaid = "short" | "full";

export const ORDER_SAID: readonly OrderSaid[] = ["short", "full"];

/** How it is said where the page does not say. This one line chooses. */
const MEANS: OrderSaid = "short";

interface Said {
  readonly phase: Phase;
  readonly ranking: Ranking | null;
  readonly areas: readonly AreaSummary[];
  /** How many areas changed place at the last answer. `null` for a first ranking. */
  readonly moved: number | null;
  /** How many areas the ranking before this one ranked. Left out or `null` for a first ranking. */
  readonly was?: number | null;
  /** True when the last answer made the settings nobody chose count for less. */
  readonly gaveWay: boolean;
  /** True when the last answer took the budget off, because the tenure changed. */
  readonly budgetWent?: boolean;
  /**
   * True where the search is a visit. A budget that went as a search became one is said
   * to have gone because a visit has none, and not because a rent is no price.
   */
  readonly visiting?: boolean;
  /**
   * The spec the ranking is of. With it in hand the line says where a journey or a budget
   * counts for more than anything that was asked of the place.
   */
  readonly spec?: PreferenceSpec;
  /**
   * True once a search is open. The line keeps the room of a line then, so that nothing
   * moves when it speaks, and where nothing is ranked it says so: it said nothing, and the
   * room was an empty band in the box. Left out, as before a search, it says nothing there.
   */
  readonly open?: boolean;
  /** How what the order means is said. Left out, as the look has chosen. */
  readonly means?: OrderSaid;
}

interface Props extends Said {
  /** The frame the line stands in. Left out, the one the look has chosen. */
  readonly frame?: StatusFrame;
  /** Whether the line keeps its room while it says nothing. Left out, as the look has chosen. */
  readonly room?: StatusRoom;
  /**
   * The count of the answers. What the line says of a ranking is drawn anew when it moves,
   * so that an answer the line says in the words of the last is said all the same: a screen
   * reader is told of a node that came, and of none that stayed as it was.
   */
  readonly answers?: number;
}

/** One thing the line says. What is not drawn is still said to a screen reader. */
interface Part {
  readonly text: string;
  /**
   * False for what a person who sees the page reads from the layout: the name of the first
   * result, which its card gives directly under the line.
   */
  readonly drawn: boolean;
}

/** What the line says for a state of the search, part by part. One state, one thing said. */
export function saidOf({
  phase,
  ranking,
  areas,
  moved,
  was = null,
  gaveWay,
  budgetWent = false,
  visiting = false,
  spec,
  open = false,
  means = MEANS,
}: Said): readonly Part[] {
  const drawn = (text: string): Part => ({ text, drawn: true });
  if (phase === "interpreting") return [drawn(STATUS.reading)];
  if (ranking === null) {
    // A control asked for a first ranking, and it is on its way. Nothing is read, so the
    // line does not say that a search is: it says what is worked out.
    const waits = phase === "refining" ? [drawn(WAIT.ranking)] : [];
    if (waits.length > 0 || !open) return waits;
    // A search is open and nothing is ranked.
    return [drawn(WAIT.notYet)];
  }
  // While an edit is being ranked the line keeps what it said, and the list is marked busy.
  // Where no limit left an area out, the line does not say that one did.
  if (ranking.ranked.length === 0) {
    return [drawn(ranking.filtered.length > 0 ? STATUS.nothingMatches : STATUS.nothingRanked)];
  }

  const said: Part[] = [];
  if (ranking.empty_spec) said.push(drawn(STATUS.rankedNoOrder(ranking.scores.length)));
  // A ranking that follows one of no area is a first ranking: there is no rest to have moved.
  else if (moved === null || was === 0) {
    // The first result the page has a name for. An area it was not built with has none,
    // and a line that names nothing as the first says nothing.
    const first = ranking.ranked
      .map((ranked) => areas.find((area) => area.area_id === ranked.area_id)?.name)
      .find((name) => name !== undefined && name !== "");
    said.push(drawn(STATUS.rankedUnnamed(ranking.scores.length)));
    if (first !== undefined) said.push({ text: STATUS.first(first), drawn: false });
  } else if (was !== null && was !== ranking.scores.length) {
    // Areas went or came. That is said first, and then how many of the rest moved: an area
    // that went moves no other, so a list of 15 is never said to hold 21 that changed place.
    said.push(drawn(STATUS.rankedNow(ranking.scores.length, ranking.scores.length - was)));
    said.push(drawn(STATUS.movedOfTheRest(moved)));
  } else said.push(drawn(STATUS.moved(moved)));
  if (budgetWent) said.push(drawn(visiting ? STATUS.budgetWentForAVisit : STATUS.budgetWent));
  // What explains the order on screen is said of every ranking it is true of. A person who
  // asked for leafy and quiet, and named a workplace, must not read the first result as the
  // leafiest: the journey counts for more, and the line says so.
  const leads = spec === undefined || ranking.empty_spec ? null : leadsOf(spec);
  if (leads !== null) said.push(drawn(STATUS.leads(leads.journey ? leads.journeys : 0, leads.budget)));
  // It is not said where the areas are in no order: nothing counts there, and nothing comes first.
  else if (gaveWay && !ranking.empty_spec) {
    said.push(drawn(means === "full" ? STATUS.gaveWayInFull : STATUS.gaveWay));
  }
  return said;
}

/** The whole of what the line says, as a screen reader hears it. */
export function statusOf(props: Said): string {
  return saidOf(props)
    .map((one) => one.text)
    .join(" ");
}

/**
 * Says what has just happened, to everyone: it is on the page, and it is a
 * polite live region, so a screen reader says it when it changes.
 *
 * It is one short line where it can be. The name of the first result is said
 * to a screen reader and not drawn: the first card stands directly under the
 * line, and gives it.
 *
 * It stands in a frame of its own, directly under the box, and what happened is set
 * heavier than what follows it. While it says nothing it is no frame: it holds nothing at
 * all, and its style sheet draws nothing round nothing, and keeps the room of the frame
 * clear. It is the same paragraph all the while, whatever frame a page asks for and
 * whether it asks for one, so that a screen reader hears it when it first says something.
 *
 * Once a search is open it always says something, so that the room it keeps is no hole in
 * the box: what happened, what is read or worked out, what is asked, or that nothing is
 * ranked yet.
 */
export function StatusLine({ frame = FRAME, room = ROOM, answers = 0, ...state }: Props) {
  const said = saidOf(state);
  // That a search is read, or that nothing is ranked yet, is said once: the count moves
  // while a sentence is read, and the line would say twice that it is.
  const turn = state.ranking === null || state.phase === "interpreting" ? 0 : answers;
  return (
    <Frame
      kind={frame === "box" ? "box" : "plain"}
      as="p"
      // The room inside it is the line's own: it is lower than a box that holds a paragraph.
      bare
      className={styles.status}
      role="status"
      aria-live="polite"
      data-room={room}
      // Which frame was asked for. With none the frame of the kit is a plain one, whose edge the line takes away.
      data-frame={frame}
    >
      {said.map((one, at) => (
        // The parts are told apart by where they stand: two may say the same.
        <span
          key={`${turn} ${at} ${one.text}`}
          className={one.drawn ? (at === 0 ? styles.happened : undefined) : "visually-hidden"}
        >
          {at > 0 ? " " : null}
          {one.text}
        </span>
      ))}
    </Frame>
  );
}
