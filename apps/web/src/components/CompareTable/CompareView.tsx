"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { COMPARE, COMPARE_TABLE } from "@/content/compare";
import type { CrimeVibe } from "@/content/crime";
import { NOTICE, PROMPT } from "@/content/search";
import { api, type Client, type Failure } from "@/lib/api/client";
import type { CompareData, Defaults, PreferenceSpec, Tag } from "@/lib/api/schema";
import { isEnough, type Chosen } from "@/lib/compare/list";
import { paths } from "@/lib/paths";
import { useOpenSearch } from "@/lib/search/store";
import { SessionBoundary, useCompare } from "@/lib/session/session";

import { useHandOver } from "../CompareTray/drawnFrom";
import { ofATown } from "../CompareTray/town";
import { wordsFor } from "../ErrorBlock/ErrorBlock";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
import { Skeleton } from "../Skeleton/Skeleton";
import { CharacterTable } from "./CharacterTable";
import { CompareAreas, CompareTable, standingsOf } from "./CompareTable";
import styles from "./CompareView.module.css";
import type { HeadsSayOfTheirTowns } from "./look";
import { releaseOf, type MarksOf, type Towns } from "./towns";

interface Props {
  /** The areas the address names, as the release knows them. Two to four, or too few to compare. */
  readonly chosen: readonly Chosen[];
  /** The settings a search starts from, from route 11. They are what is compared on when no search is open. */
  readonly defaults: Defaults;
  /** The vibes of the release, from route 11: their names and the names of their ends. */
  readonly tags: readonly Tag[];
  /** The vibes whose recipe holds recorded crime, read from route 11 where the page is built. */
  readonly crime?: readonly CrimeVibe[];
  /**
   * Where each area of the address sits on each vibe of the release, from route 4, read
   * where the page is built. With it in hand each area has its town. A town draws nothing
   * of a vibe whose recipe holds recorded crime, so none is drawn unless the page has said
   * which vibes those are.
   */
  readonly marks?: MarksOf;
  /** How many slugs of the address named no area. They are counted and never shown. */
  readonly unknown?: number;
  /** How many areas beyond the fourth the address named. */
  readonly dropped?: number;
  /** The API to call. A test passes its own. */
  readonly client?: Client;
  /** What the heads of the areas say of their towns. Left out, it is what the look of a comparison chooses. */
  readonly saysOfTowns?: HeadsSayOfTheirTowns;
}

/** Where the page is not handed them: no vibe is said to hold recorded crime. */
const NO_CRIME: readonly CrimeVibe[] = [];

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
 *
 * The page stands boxes of its own on the grass: the way back, then what it is and what it
 * compares on, then a box for each area, then each table within a plain edge of ink under
 * its heading, then the way back again. Nothing is read on the grass.
 *
 * The way back stands at the head of the page, before anything else: a person who came
 * from a search asked how to get back to it, with the way back under both tables. It
 * leads to the search as it was left, which the session holds while the tab is open: what
 * was asked for, what was set, the results, and the areas chosen to compare. Where the
 * search came from a link it leads to the page that link opened, where the search is open
 * already. Where no search is open, as where a comparison was opened by its link alone,
 * it says that it leads to a search that is yet to be made. It is said again at the foot
 * of the page, in the same words, since a comparison is long.
 *
 * One area is no comparison, and no area is none. The page then says so in place of what
 * it says of the areas set side by side, and says what to do: the way on, at its foot, is
 * its one cobalt button, and so the one that matters most.
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
  crime,
  marks,
  unknown = 0,
  dropped = 0,
  client = api,
  saysOfTowns,
}: Props) {
  const search = useOpenSearch();
  const { set } = useCompare();
  const answer = useRef<HTMLDivElement>(null);
  // The heading of the page, which takes the focus where what had it goes and no area is left to take it.
  const heading = useRef<HTMLHeadingElement>(null);
  const [attempt, setAttempt] = useState(0);
  const [answered, setAnswered] = useState<Answered | null>(null);

  // A search is open once the API has answered it. Until then the spec is a default, as served.
  const open = search !== null && !search.untouched;
  // Where the way back leads: to the page the search was made on. A search that came from a
  // link was opened on the page of that link, whose address holds the id of the share after
  // its `#`, which a browser sends to no server.
  const from = open && search.shared !== null ? paths.share(search.shared.id) : paths.home();
  const back = open ? COMPARE.back : COMPARE.start;
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
  // A town is drawn only with all it is drawn from in hand: where each area sits, and which vibes hold recorded crime.
  const towns = useMemo<Towns | undefined>(
    () => (marks === undefined || crime === undefined ? undefined : { meta: releaseOf(tags, crime), marks }),
    [marks, crime, tags],
  );
  // The bar of the page a person goes back to draws the towns that stand here: what they are
  // drawn from is handed over with the areas, once the page is in the browser.
  const hand = useHandOver();
  useEffect(() => {
    if (towns !== undefined) hand({ release: ofATown(towns.meta), marks: towns.marks });
  }, [hand, towns]);
  const standings = useMemo(
    () =>
      // The ranking is of the spec that is sent only when the two hashes agree.
      open && search !== null && ranking !== null && search.rankedHash === search.specHash
        ? standingsOf(ranking.scores, ranking.empty_spec)
        : new Map(),
    [open, search, ranking],
  );

  return (
    // It stands boxes of its own on the grass, so the shell draws none round it.
    <div className={styles.view} data-dressed="">
      {/* Before anything else: the way back to the search. It is a button of the look, which
          brings the ground it is read on, and is fetched when it is pressed and not before. */}
      <p className={styles.back}>
        <Press href={from}>{back}</Press>
      </p>
      <Frame kind="box" className={styles.head}>
        {/* It can be given the focus, and is no stop of its own. */}
        <h1 ref={heading} tabIndex={-1}>
          {COMPARE.title}
        </h1>
        {/* That the areas are set side by side is said of two or more. One area is no comparison. */}
        {enough ? <p className={styles.lead}>{COMPARE.lead}</p> : null}

        {unknown > 0 ? <p className={styles.note}>{COMPARE.unknown(unknown)}</p> : null}
        {dropped > 0 ? <p className={styles.note}>{COMPARE.dropped(dropped)}</p> : null}

        {/* What the areas were compared on is said once they were: while the comparison is
            waited for, and where it failed, none was made. Too few areas are said to be so
            from the first, since nothing is waited for. */}
        {enough && (current === null || current.data === null) ? null : (
          <div className={styles.state} role="status">
            <p>
              {enough
                ? open
                  ? COMPARE.fromSearch
                  : COMPARE.fromDefaults[spec.tenure]
                : chosen.length === 0
                  ? COMPARE.none
                  : COMPARE.tooFew}
            </p>
          </div>
        )}
      </Frame>

      {/* What is heard while the comparison is waited for, and once it is in. */}
      {enough ? (
        <p className="visually-hidden" role="status" aria-live="polite">
          {current === null ? COMPARE.comparing : current.data !== null ? COMPARE.compared(current.data.areas.length) : ""}
        </p>
      ) : null}
      {/* The areas are one part of the page, whatever it holds: where an area is taken out and
          one is left, that one is what it was, and keeps the focus it was handed. */}
      <CompareAreas
        chosen={chosen}
        compared={enough ? current?.data?.areas : undefined}
        waiting={enough && current === null}
        standings={standings}
        towns={towns}
        character={enough ? current?.data?.character : undefined}
        head={heading}
        {...(saysOfTowns === undefined ? {} : { saysOfTowns })}
      />
      {enough ? (
        <noscript>
          <p className={styles.note}>{COMPARE.needsScripts}</p>
        </noscript>
      ) : null}
      {enough ? (
        // Where the answer stands, and where it is waited for. It can be given the focus, and
        // is no stop of its own: what is pressed in it and goes leaves the focus here.
        <div ref={answer} className={styles.answer} tabIndex={-1}>
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
              {/* Where a comparison failed it is the one button that matters most, as on the page a shared link opens. */}
              <Press
                kind="go"
                onPress={() => {
                  // The button goes with the failure it stands in, and the focus must not go with it.
                  answer.current?.focus({ preventScroll: true });
                  setAttempt((last) => last + 1);
                }}
              >
                {PROMPT.tryAgain}
              </Press>
            </div>
          ) : current.data !== null ? (
            <>
              {/* Where each area sits on each vibe is of the release, and comes first. */}
              {current.data.character.length > 0 ? (
                <Frame as="section" kind="plain" bare className={styles.part} aria-labelledby="compare-character">
                  <h2 id="compare-character" className={styles.partTitle}>
                    {COMPARE_TABLE.character.title}
                  </h2>
                  <CharacterTable data={current.data} tags={tags} crime={crime ?? NO_CRIME} />
                </Frame>
              ) : null}
              <Frame as="section" kind="plain" bare className={styles.part} aria-labelledby="compare-counts">
                <h2 id="compare-counts" className={styles.partTitle}>
                  {COMPARE_TABLE.counts}
                </h2>
                {current.data.rows.length === 0 ? (
                  <div className={styles.state} role="status">
                    <p>{COMPARE.nothingCounts}</p>
                  </div>
                ) : (
                  <CompareTable
                    data={current.data}
                    combine={spec.commute_combine}
                    tags={tags}
                    fits={[...standings.values()].some((standing) => standing.fit !== null)}
                  />
                )}
              </Frame>
            </>
          ) : null}
        </div>
      ) : null}

      <p className={styles.on}>
        {enough ? (
          // Under both tables the way back is said again, in the words it has at the head of the page.
          <Press href={from}>{back}</Press>
        ) : (
          // Where there is nothing to compare, the way to choose areas is what matters most.
          <Press kind="go" href={from}>
            {open ? COMPARE.chooseMore : COMPARE.start}
          </Press>
        )}
      </p>
    </div>
  );
}
