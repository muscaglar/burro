"use client";

import Link from "next/link";

import { APART, BREAKDOWN, UNRANKED } from "@/content/search";
import type { AreaSummary, MetaData, PreferenceSpec, Unranked } from "@/lib/api/schema";
import { paths } from "@/lib/paths";

import { Disclosure } from "../Disclosure/Disclosure";
import styles from "./ResultList.module.css";

interface Props {
  /** The areas the ranking could not place, each with why and what it lacks. They are the API's. */
  readonly unranked: readonly Unranked[];
  readonly areas: readonly AreaSummary[];
  readonly meta: Pick<MetaData, "features" | "tags">;
  /** The spec that was ranked. With it in hand, what the person asked for is said first. */
  readonly spec?: Pick<PreferenceSpec, "weights">;
}

/**
 * The name of a thing an area has no figure for, by the name the API gives it. `null` for one
 * the page has no name for: it is left out, and never shown as its code.
 */
function nameOf(component: string, meta: Props["meta"]): string | null {
  if (component === "commute") return BREAKDOWN.journey;
  if (component === "budget") return BREAKDOWN.budget;
  const [kind, id] = component.split(":", 2);
  if (kind === "feature") return meta.features.find((feature) => feature.feature_id === id)?.label ?? null;
  if (kind === "tag") return meta.tags.find((tag) => tag.tag_id === id)?.label ?? null;
  return null;
}

/**
 * What an area lacks, with what the person asked for before the settings nobody chose. Each
 * kind keeps the order the API gave it. A vibe, a journey and a budget are always asked for.
 */
function askedFirst(missing: readonly string[], spec: Props["spec"]): readonly string[] {
  if (spec === undefined) return missing;
  const usual = new Set(
    spec.weights.filter((weight) => weight.provenance === "default").map((weight) => `feature:${weight.feature_id}`),
  );
  return [...missing.filter((one) => !usual.has(one)), ...missing.filter((one) => usual.has(one))];
}

/**
 * The areas that are not ranked, listed apart from those that are. An area
 * Burro cannot place on what counts in a search has no fit and no rank: it
 * once came first on its journey and its rent alone, with no figure for
 * anything that was asked of the place. Each says why, in words, and what it
 * has no figure for, by the names the API gives.
 *
 * It is closed at first and says how many areas it holds, so that the answer
 * stays a few lines however many areas a release cannot place. Which areas,
 * why, and what each lacks are the API's. No figure is given for any of them.
 * The areas this search cannot place come first, and then the ones that the
 * data ranks for no search.
 */
export function NotRanked({ unranked, areas, meta, spec }: Props) {
  const named = unranked.flatMap((one) => {
    const summary = areas.find((area) => area.area_id === one.area_id);
    return summary === undefined ? [] : [{ ...one, summary }];
  });
  // An area that this search cannot place comes before one that no search ranks. Within each
  // the order is the API's.
  const never = (one: Unranked) => one.reason === "not_rankable";
  const listed = [...named.filter((one) => !never(one)), ...named.filter(never)];
  if (listed.length === 0) return null;
  return (
    <Disclosure label={APART.title(listed.length)} className={styles.apart}>
      <p className={styles.apartLead}>{APART.lead}</p>
      <ul className={styles.apartList} aria-label={APART.label}>
        {listed.map(({ summary, reason, missing }) => {
          // A newer service may give a reason the page has no words for, and an older one
          // may not say what an area lacks. Neither is shown as a code or as a blank.
          const why = (UNRANKED as Readonly<Record<string, string | undefined>>)[reason];
          const lacks = askedFirst((missing as readonly string[] | undefined) ?? [], spec).flatMap(
            (component) => nameOf(component, meta) ?? [],
          );
          return (
            <li key={summary.area_id} data-area={summary.area_id} className={styles.apartItem}>
              <p className={styles.apartName}>
                {/* Which page a person reads next is told to no server ahead of time. */}
                <Link className="target-min" href={paths.area(summary)} prefetch={false}>
                  {summary.name}
                </Link>
              </p>
              {why === undefined ? null : <p>{why}</p>}
              {lacks.length > 0 ? (
                <>
                  <p className={styles.apartLacks}>{APART.lacks}</p>
                  <ul className={styles.apartThings} aria-label={APART.lacks}>
                    {lacks.map((name) => (
                      <li key={name}>{name}</li>
                    ))}
                  </ul>
                </>
              ) : null}
            </li>
          );
        })}
      </ul>
    </Disclosure>
  );
}
