"use client";

import { BREAKDOWN, FILTERED, NOTHING_MATCHES, UNRANKED } from "@/content/search";
import type {
  AreaSummary,
  Filtered,
  FilterReason,
  MetaData,
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
  /** The names the API gives what counts, so that what has no figure is said by name. */
  readonly meta?: Pick<MetaData, "features" | "tags">;
  readonly onEdit: (operations: Operations) => void;
}

/**
 * What the areas that could not be ranked have no figure for, each thing once, by the name
 * the API gives it, with how many areas lack it. The thing most areas lack comes first. A
 * thing the page has no name for is left out, and never shown as its code.
 */
export function lacksOf(
  unranked: readonly Unranked[],
  meta: Pick<MetaData, "features" | "tags"> | undefined,
): readonly { readonly name: string; readonly count: number }[] {
  const counts = new Map<string, number>();
  for (const area of unranked) {
    for (const component of (area.missing as readonly string[] | undefined) ?? []) {
      counts.set(component, (counts.get(component) ?? 0) + 1);
    }
  }
  const nameOf = (component: string): string | null => {
    if (component === "commute") return BREAKDOWN.journey;
    if (component === "budget") return BREAKDOWN.budget;
    const [kind, id] = component.split(":", 2);
    if (kind === "feature") return meta?.features.find((one) => one.feature_id === id)?.label ?? null;
    if (kind === "tag") return meta?.tags.find((one) => one.tag_id === id)?.label ?? null;
    return null;
  };
  return [...counts]
    .flatMap(([component, count]) => {
      const name = nameOf(component);
      return name === null ? [] : [{ name, count }];
    })
    .sort((one, other) => other.count - one.count);
}

const FILTER_ORDER: readonly FilterReason[] = [
  "excluded",
  "not_selected",
  "over_budget",
  "commute_cap",
  "commute_likely_beyond",
];
const UNRANKED_ORDER: readonly UnrankedReason[] = ["not_rankable", "insufficient_data", "character_unknown"];

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
export function NothingMatches({ filtered, unranked, spec, areas, placeNames, meta, onEdit }: Props) {
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
  // A limit is offered to be loosened only where a limit left an area out.
  const limited = filtered.length > 0;
  const ways = limited ? waysOut(spec, areas, placeNames) : [];
  const lacks = lacksOf(unranked, meta);

  return (
    <section className={styles.nothing} aria-labelledby="nothing-matches">
      <h2 id="nothing-matches" className={styles.title}>
        {limited ? NOTHING_MATCHES.title : NOTHING_MATCHES.noData}
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
      {lacks.length > 0 ? (
        <>
          <p className={styles.lacks} id="nothing-lacks">
            {NOTHING_MATCHES.lacks}
          </p>
          <ul className={styles.things} aria-labelledby="nothing-lacks">
            {lacks.map(({ name, count }) => (
              <li key={name}>{NOTHING_MATCHES.lacking(name, count)}</li>
            ))}
          </ul>
        </>
      ) : null}
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
