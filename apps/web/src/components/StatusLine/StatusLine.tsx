import { STATUS } from "@/content/search";
import type { AreaSummary } from "@/lib/api/schema";
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
}

/** What the line says for a state of the search. One state, one thing said. */
export function statusOf({
  phase,
  ranking,
  areas,
  moved,
  was = null,
  gaveWay,
  budgetWent = false,
  asking = false,
}: Props): string {
  if (phase === "interpreting") return STATUS.reading;
  // While an edit is being ranked the line keeps what it said, and the list is marked busy.
  if (ranking === null) return asking ? STATUS.question : "";
  if (ranking.ranked.length === 0) return STATUS.nothingMatches;

  const said: string[] = [];
  if (ranking.empty_spec) said.push(STATUS.rankedNoOrder(ranking.scores.length));
  else if (moved === null) {
    // The first result the page has a name for. An area it was not built with has none,
    // and a line that ends "First: ." says nothing.
    const first = ranking.ranked
      .map((ranked) => areas.find((area) => area.area_id === ranked.area_id)?.name)
      .find((name) => name !== undefined && name !== "");
    said.push(
      first === undefined
        ? STATUS.rankedUnnamed(ranking.scores.length)
        : STATUS.ranked(ranking.scores.length, first),
    );
  } else if (was !== null && was !== ranking.scores.length) {
    // Areas went or came. That is said first, and then how many of the rest moved: an area
    // that went moves no other, so a list of 15 is never said to hold 21 that changed place.
    said.push(STATUS.rankedNow(ranking.scores.length, ranking.scores.length - was));
    said.push(STATUS.movedOfTheRest(moved));
  } else said.push(STATUS.moved(moved));
  if (budgetWent) said.push(STATUS.budgetWent);
  if (gaveWay) said.push(STATUS.gaveWay);
  if (asking) said.push(STATUS.question);
  return said.join(" ");
}

/**
 * Says what has just happened, to everyone: it is on the page, and it is a
 * polite live region, so a screen reader says it when it changes.
 */
export function StatusLine(props: Props) {
  return (
    <p className={styles.status} role="status" aria-live="polite">
      {statusOf(props)}
    </p>
  );
}
