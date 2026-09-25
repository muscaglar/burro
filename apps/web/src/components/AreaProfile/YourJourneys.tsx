"use client";

import Link from "next/link";
import { useId } from "react";

import { AREA } from "@/content/area";
import { MODE } from "@/content/labels";
import { JOURNEYS } from "@/content/search";
import type { Commute, CommuteLeg, Cutoffs } from "@/lib/api/schema";
import { paths } from "@/lib/paths";
import { estimateOf, factsForJourney, withinLimit } from "@/lib/search/card";
import { useOpenSearch } from "@/lib/search/store";

import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./AreaProfile.module.css";

interface Props {
  /** The area whose page this is, by its id. */
  readonly areaId: string;
}

/** How long a journey takes, in the words a result says it in. */
function timeOf(leg: CommuteLeg, cutoffs: Cutoffs): string {
  const band = estimateOf(leg);
  // No time is held: the band is said, and that it is an estimate, and no minutes.
  if (band !== null) return `${JOURNEYS.estimated[band]}. ${JOURNEYS.estimatedFrom}`;
  if (leg.status === "missing") return JOURNEYS.missing;
  if (leg.status === "beyond_cutoff") return JOURNEYS.beyond(cutoffs[leg.mode]);
  // The time the ranking holds against the limit, so that the verdict beside it is of this figure.
  const counted = leg.minutes ?? leg.minutes_typical;
  return counted === null ? JOURNEYS.notGiven : JOURNEYS.minutes(counted);
}

/** Whether that is within the longest the person set, in words. Nothing where there is no time to hold against it. */
function verdictOf(leg: CommuteLeg, commute: Commute | undefined): string | null {
  const within = withinLimit(leg, commute);
  if (within === null || commute === undefined) return null;
  return within ? JOURNEYS.withinLimit(commute.max_minutes) : JOURNEYS.overLimit(commute.max_minutes);
}

/**
 * How long it takes from this area to each place of the search that is open.
 * Every name and every time is the API's: the places are named by the answer
 * that brought the search, and the times came with its ranking. Nothing is
 * asked for here, and nothing of the search is put in an address.
 *
 * With no search open, or one that names no place, it draws nothing. Where
 * the ranking in hand does not hold the area, it says so and gives no time.
 * It is drawn in the browser, because a page is built with no search.
 */
export function YourJourneys({ areaId }: Props) {
  const id = useId();
  const search = useOpenSearch();
  if (search === null || search.untouched || search.spec.commutes.length === 0) return null;
  const { spec, ranking, placeNames, facts, meta } = search;
  // The ranking is of the spec on screen only when the two hashes agree.
  const held = ranking !== null && search.rankedHash === search.specHash ? ranking : null;
  const area = held?.ranked.find((one) => one.area_id === areaId);
  return (
    <div className={styles.journeys} role="group" aria-labelledby={id}>
      <h4 id={id} className={styles.small}>
        {AREA.journeys.title}
      </h4>
      {area === undefined || area.legs.length === 0 ? (
        <p>
          {AREA.journeys.notInHand}{" "}
          <Link className="target-min" href={paths.home()}>
            {AREA.journeys.toSearch}
          </Link>
        </p>
      ) : (
        <ul className={styles.legs}>
          {area.legs.map((leg) => {
            const name = placeNames[leg.place_id] ?? "";
            const verdict = verdictOf(
              leg,
              spec.commutes.find((one) => one.place_id === leg.place_id),
            );
            return (
              <li key={`${leg.place_id}.${leg.mode}`}>
                <span className={styles.name}>{name}</span>
                <span className="visually-hidden">: </span>
                <span>
                  {estimateOf(leg) === null
                    ? `${timeOf(leg, meta.limits.cutoff_minutes)}, ${MODE[leg.mode]}`
                    : `${MODE[leg.mode]}: ${timeOf(leg, meta.limits.cutoff_minutes)}`}
                  {verdict === null ? null : `. ${verdict}`}
                </span>
                <SourceNote facts={factsForJourney(area, leg, facts)} of={name} />
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
