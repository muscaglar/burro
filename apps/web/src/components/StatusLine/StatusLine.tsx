import { STATUS } from "@/content/search";
import type { AreaSummary, PreferenceSpec } from "@/lib/api/schema";
import { leadsOf } from "@/lib/search/leads";
import type { Phase, Ranking } from "@/lib/search/state";

import styles from "./StatusLine.module.css";

interface Props {
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
  /** True when there is a question to answer about a place. */
  readonly asking?: boolean;
  /**
   * The spec the ranking is of. With it in hand the line says where a journey or a budget
   * counts for more than anything that was asked of the place.
   */
  readonly spec?: PreferenceSpec;
}

/** One thing the line says. What is not drawn is still said to a screen reader. */
interface Said {
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
  asking = false,
  spec,
}: Props): readonly Said[] {
  const drawn = (text: string): Said => ({ text, drawn: true });
  if (phase === "interpreting") return [drawn(STATUS.reading)];
  // While an edit is being ranked the line keeps what it said, and the list is marked busy.
  if (ranking === null) return asking ? [drawn(STATUS.question)] : [];
  // Where no limit left an area out, the line does not say that one did.
  if (ranking.ranked.length === 0) {
    return [drawn(ranking.filtered.length > 0 ? STATUS.nothingMatches : STATUS.nothingRanked)];
  }

  const said: Said[] = [];
  if (ranking.empty_spec) said.push(drawn(STATUS.rankedNoOrder(ranking.scores.length)));
  // A ranking that follows one of no area is a first ranking: there is no rest to have moved.
  else if (moved === null || was === 0) {
    // The first result the page has a name for. An area it was not built with has none,
    // and a line that ends "First: ." says nothing.
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
  if (budgetWent) said.push(drawn(STATUS.budgetWent));
  // What explains the order on screen is said of every ranking it is true of. A person who
  // asked for leafy and quiet, and named a workplace, must not read the first result as the
  // leafiest: the journey counts for more, and the line says so.
  const leads = spec === undefined || ranking.empty_spec ? null : leadsOf(spec);
  if (leads !== null) said.push(drawn(STATUS.leads(leads.journey ? leads.journeys : 0, leads.budget)));
  else if (gaveWay) said.push(drawn(STATUS.gaveWay));
  if (asking) said.push(drawn(STATUS.question));
  return said;
}

/** The whole of what the line says, as a screen reader hears it. */
export function statusOf(props: Props): string {
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
 */
export function StatusLine(props: Props) {
  const said = saidOf(props);
  return (
    <p className={styles.status} role="status" aria-live="polite">
      {said.map((one, at) => (
        // The parts are told apart by where they stand: two may say the same.
        <span key={`${at} ${one.text}`} className={one.drawn ? undefined : "visually-hidden"}>
          {at > 0 ? " " : null}
          {one.text}
        </span>
      ))}
    </p>
  );
}
