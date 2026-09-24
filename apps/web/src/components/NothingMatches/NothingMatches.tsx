"use client";

import { FILTERED, NOTHING_MATCHES, UNRANKED } from "@/content/search";
import type {
  AreaSummary,
  Filtered,
  FilterReason,
  Operations,
  PreferenceSpec,
  Unranked,
  UnrankedReason,
} from "@/lib/api/schema";
import { namesOfPlaces } from "@/lib/search/chips";
import { edits } from "@/lib/search/edits";

import styles from "./NothingMatches.module.css";

interface Props {
  readonly filtered: readonly Filtered[];
  readonly unranked: readonly Unranked[];
  readonly spec: PreferenceSpec;
  readonly areas: readonly AreaSummary[];
  readonly placeNames: Readonly<Record<string, string>>;
  readonly onEdit: (operations: Operations) => void;
}

const FILTER_ORDER: readonly FilterReason[] = ["excluded", "not_selected", "over_budget", "commute_cap"];
const UNRANKED_ORDER: readonly UnrankedReason[] = ["not_rankable", "insufficient_data"];

/** Each firm limit in the spec, with the one edit that loosens it. */
export function waysOut(
  spec: PreferenceSpec,
  areas: readonly AreaSummary[],
  placeNames: Readonly<Record<string, string>>,
): readonly { readonly key: string; readonly label: string; readonly operations: Operations }[] {
  const ways = [];
  if (spec.budget.amount !== null && spec.budget.strictness === "hard") {
    ways.push({
      key: "budget",
      label: NOTHING_MATCHES.budgetFlexible,
      operations: edits.budgetStrictness("soft"),
    });
  }
  const names = namesOfPlaces(spec, placeNames);
  for (const commute of spec.commutes) {
    if (commute.strictness !== "hard") continue;
    ways.push({
      key: `place:${commute.place_id}`,
      label: NOTHING_MATCHES.journeyFlexible(names.get(commute.place_id) ?? ""),
      operations: edits.placeStrictness(commute.place_id, "soft"),
    });
  }
  for (const rule of spec.areas) {
    const name = areas.find((area) => area.area_id === rule.area_id)?.name ?? "";
    ways.push({
      key: `area:${rule.area_id}`,
      label: rule.rule === "exclude" ? NOTHING_MATCHES.showHidden(name) : NOTHING_MATCHES.showAll(name),
      operations: edits.areaClear(rule.area_id),
    });
  }
  return ways;
}

/**
 * Said when the ranking came back with nobody in it: why, as a count for
 * each reason, and one button for each firm limit, which sends the one edit
 * that loosens it.
 */
export function NothingMatches({ filtered, unranked, spec, areas, placeNames, onEdit }: Props) {
  const counts = [
    ...FILTER_ORDER.map((reason) => ({
      reason,
      label: FILTERED[reason],
      count: filtered.filter((area) => area.reason === reason).length,
    })),
    ...UNRANKED_ORDER.map((reason) => ({
      reason,
      label: UNRANKED[reason],
      count: unranked.filter((area) => area.reason === reason).length,
    })),
  ].filter(({ count }) => count > 0);
  const ways = waysOut(spec, areas, placeNames);

  return (
    <section className={styles.nothing} aria-labelledby="nothing-matches">
      <h2 id="nothing-matches" className={styles.title}>
        {NOTHING_MATCHES.title}
      </h2>
      <p>{NOTHING_MATCHES.lead}</p>
      <dl className={styles.counts}>
        {counts.map(({ reason, label, count }) => (
          <div key={reason}>
            <dt>{label}</dt>
            <dd>{NOTHING_MATCHES.count(count)}</dd>
          </div>
        ))}
      </dl>
      {ways.length > 0 ? (
        <ul className={styles.ways} aria-label={NOTHING_MATCHES.loosen}>
          {ways.map(({ key, label, operations }) => (
            <li key={key}>
              <button type="button" className="target" onClick={() => onEdit(operations)}>
                {label}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
