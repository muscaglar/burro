"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { COMPARE, COMPARE_TABLE } from "@/content/compare";
import type { CrimeVibe } from "@/content/crime";
import { NOTICE, PROMPT } from "@/content/search";
import { api, type Client, type Failure } from "@/lib/api/client";
import type { CompareData, Defaults, PreferenceSpec, RoughGuide, Tag } from "@/lib/api/schema";
import { isEnough, type Chosen } from "@/lib/compare/list";
import { paths } from "@/lib/paths";
import { useOpenSearch } from "@/lib/search/store";
import { SessionBoundary, useCompare } from "@/lib/session/session";

import { wordsFor } from "../ErrorBlock/ErrorBlock";
import { Skeleton } from "../Skeleton/Skeleton";
import { CharacterTable } from "./CharacterTable";
import { CompareAreas, CompareTable, standingsOf } from "./CompareTable";
import styles from "./CompareView.module.css";

interface Props {
  /** The areas the address names, as the release knows them. Two to four, or too few to compare. */
  readonly chosen: readonly Chosen[];
  /** The settings a search starts from, from route 11. They are what is compared on when no search is open. */
  readonly defaults: Defaults;
  /** The vibes of the release, from route 11: their names and the names of their ends. */
  readonly tags: readonly Tag[];
  /** The vibes whose recipe holds recorded crime, read from route 11 where the page is built. */
  readonly crime?: readonly CrimeVibe[];
  /** What each vibe that is a rough guide says of itself, from route 11. */
  readonly guides?: readonly RoughGuide[];
  /** How many slugs of the address named no area. They are counted and never shown. */
  readonly unknown?: number;
  /** How many areas beyond the fourth the address named. */
  readonly dropped?: number;
  /** The API to call. A test passes its own. */
  readonly client?: Client;
}

interface Answered {
  /** What was asked, so that an answer to an older question is never shown for a newer one. */
  readonly asked: string;
  readonly data: CompareData | null;
  readonly failure: Failure | null;
}

/**
 * The comparison page: two to four areas side by side, on the search that is
 * open. The spec that is sent is the last one the API returned, as the store
 * holds it. With no search open it is the default the API served, and the
 * page says so.
 *
 * The areas come from the address, which holds their slugs and nothing else.
 */
export function CompareView(props: Props) {
  return (
    <SessionBoundary>
      <Comparison {...props} />
    </SessionBoundary>
  );
}

function Comparison({
  chosen,
  defaults,
  tags,
  crime = [],
  guides = [],
  unknown = 0,
  dropped = 0,
  client = api,
}: Props) {
  const search = useOpenSearch();
  const { set } = useCompare();
  const [attempt, setAttempt] = useState(0);
  const [answered, setAnswered] = useState<Answered | null>(null);

  // A search is open once the API has answered it. Until then the spec is a default, as served.
  const open = search !== null && !search.untouched;
  const spec: PreferenceSpec = search?.spec ?? defaults.rent;
  const enough = isEnough(chosen);
  const ids = chosen.map((area) => area.area_id).join(" ");
  // The hash names the spec where there is one. A default has none, and is named by its tenure.
  const asked = `${ids} ${search?.specHash ?? `default ${spec.tenure}`} ${search?.answers ?? 0} ${attempt}`;

  // The tray holds what is being compared, so that going back to choose others starts from here.
  useEffect(() => {
    if (chosen.length > 0) set(chosen);
  }, [chosen, set]);

  useEffect(() => {
    if (!enough) return;
    const stop = new AbortController();
    void client
      .compare({ area_ids: chosen.map((area) => area.area_id), spec }, stop.signal)
      .then((answer) => {
        if (stop.signal.aborted) return;
        setAnswered(
          answer.ok
            ? { asked, data: answer.data, failure: null }
            : { asked, data: null, failure: answer.failure },
        );
      });
    return () => stop.abort();
    // What is asked is named by `asked`: the areas, the spec and the attempt.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [asked, client, enough]);

  const current = answered !== null && answered.asked === asked ? answered : null;
  const ranking = search?.ranking ?? null;
  const standings = useMemo(
    () =>
      // The ranking is of the spec that is sent only when the two hashes agree.
      open && search !== null && ranking !== null && search.rankedHash === search.specHash
        ? standingsOf(ranking.scores, ranking.empty_spec)
        : new Map(),
    [open, search, ranking],
  );

  return (
    <div className={styles.view}>
      <h1>{COMPARE.title}</h1>
      <p className={styles.lead}>{COMPARE.lead}</p>

      {unknown > 0 ? <p className={styles.note}>{COMPARE.unknown(unknown)}</p> : null}
      {dropped > 0 ? <p className={styles.note}>{COMPARE.dropped(dropped)}</p> : null}

      {!enough ? (
        <>
          <div className={styles.state} role="status">
            <p>{COMPARE.tooFew}</p>
          </div>
          <CompareAreas chosen={chosen} />
        </>
      ) : (
        <>
          <div className={styles.state} role="status">
            <p>{open ? COMPARE.fromSearch : COMPARE.fromDefaults[spec.tenure]}</p>
          </div>
          <p className="visually-hidden" role="status" aria-live="polite">
            {current === null
              ? COMPARE.comparing
              : current.data !== null
                ? COMPARE.compared(current.data.areas.length)
                : ""}
          </p>
          <CompareAreas
            chosen={chosen}
            compared={current?.data?.areas}
            waiting={current === null}
            standings={standings}
          />
          <noscript>
            <p className={styles.note}>{COMPARE.needsScripts}</p>
          </noscript>
          {current === null ? (
            <div aria-busy="true">
              <Skeleton shape="card" lines={6} />
            </div>
          ) : current.failure !== null ? (
            <div className={styles.error} role="alert">
              <p className={styles.errorTitle}>{COMPARE.failedTitle}</p>
              <p>{wordsFor(current.failure)}</p>
              {current.failure.requestId !== null ? (
                <p className={styles.request}>
                  {NOTICE.requestId} <code>{current.failure.requestId}</code>
                </p>
              ) : null}
              <button type="button" className="target" onClick={() => setAttempt((last) => last + 1)}>
                {PROMPT.tryAgain}
              </button>
            </div>
          ) : current.data !== null ? (
            <>
              {/* Where each area sits on each vibe is of the release, and comes first. */}
              {current.data.character.length > 0 ? (
                <section className={styles.part} aria-labelledby="compare-character">
                  <h2 id="compare-character">{COMPARE_TABLE.character.title}</h2>
                  <CharacterTable data={current.data} tags={tags} crime={crime} guides={guides} />
                </section>
              ) : null}
              <section className={styles.part} aria-labelledby="compare-counts">
                <h2 id="compare-counts">{COMPARE_TABLE.counts}</h2>
                {current.data.rows.length === 0 ? (
                  <div className={styles.state} role="status">
                    <p>{COMPARE.nothingCounts}</p>
                  </div>
                ) : (
                  <CompareTable
                    data={current.data}
                    combine={spec.commute_combine}
                    tags={tags}
                    guides={guides}
                  />
                )}
              </section>
            </>
          ) : null}
        </>
      )}

      <p className={styles.back}>
        <Link className="target" href={paths.home()}>
          {open ? COMPARE.chooseOthers : COMPARE.toSearch}
        </Link>
      </p>
    </div>
  );
}
