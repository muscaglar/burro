"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { Frame } from "@/components/kit/Frame/Frame";
import { Press } from "@/components/kit/Press/Press";
import { RESULTS } from "@/content/search";
import { TOWNS } from "@/content/towns";
import type { Handed } from "@/lib/api/handed";
import type {
  AreaData,
  AreaSummary,
  Explanation,
  GeometryData,
  Meta,
  Operations,
  PreferenceSpec,
  RankedArea,
  Unranked,
  VibeBands,
} from "@/lib/api/schema";
import { costFor, type Facts } from "@/lib/search/card";
import { namesOfPlaces } from "@/lib/search/chips";
import { EXPLAINED } from "@/lib/search/flow";


import { useHandOver } from "../CompareTray/drawnFrom";
import { Invite, invites } from "../CompareTray/Invite";
import { INVITE_STANDS, type InviteStands } from "../CompareTray/look";
import { ofATown } from "../CompareTray/town";
import { scaleOf } from "../CostRange/CostRange";
import { Skeleton } from "../Skeleton/Skeleton";
import { bringBeside, hold, pressedIn } from "./held";
import {
  ENDS_ON_A_RESULT,
  LINE_STANDS,
  ON_A_NARROW_RESULT,
  ON_A_NARROW_RESULT_A_BUTTON_IS,
  OTHERS_STAND,
  OVER_THE_LIST,
  TOWN_DRAWN,
  TRADE_OFF_DRAWN,
  WHAT_A_FIT_IS_BASED_ON_IS_SAID_IN_THE,
  type EndsOnAResult,
  type FitSaid,
  type LineStands,
  type OnANarrowResult,
  type OnANarrowResultAButtonIs,
  type OthersStand,
  type OverTheList,
  type TownDrawn,
  type TradeOffDrawn,
} from "./look";
import { columnOf as namesInTheColumn } from "./lines";
import { NotRanked } from "./NotRanked";
import { ResultCard, ResultRow } from "./ResultCard";
import styles from "./ResultList.module.css";
import { marksOn } from "./town";

/** How many results are on the page before "Show 10 more" is pressed. */
export const SHOWN_AT_FIRST = 10;

/**
 * Which part of the list is drawn. The first result stands before the map and the rest
 * after it, so that on a narrow screen the answer is whole on the first screen and the map
 * comes next. To whoever reads the page they are one list: the first, and then the rest
 * from the second.
 */
export type Part = "first" | "rest";

interface Props {
  readonly part: Part;
  /** The first twenty, in rank order. `null` while the first ranking is waited for. */
  readonly ranked: readonly RankedArea[] | null;
  readonly areas: readonly AreaSummary[];
  /** The reasons for the ranking on screen. Empty while they are waited for. */
  readonly explanations: readonly Explanation[];
  /** True once the reasons for the ranking on screen are in. */
  readonly explained: boolean;
  readonly explainFailed: boolean;
  readonly facts: Facts;
  readonly details: Readonly<Record<string, AreaData>>;
  readonly detailsFailed: readonly string[];
  readonly geometry: GeometryData | null;
  readonly spec: PreferenceSpec;
  readonly meta: Handed;
  readonly served: Pick<Meta, "release_id" | "engine_version">;
  readonly placeNames: Readonly<Record<string, string>>;
  readonly noFit: boolean;
  /** The areas the ranking could not place. They are listed apart, under the list. */
  readonly unranked: readonly Unranked[];
  /** How many areas are ranked, and how many of them the answer holds in full. Both are the API's. */
  readonly areasRanked: number;
  readonly areasListed: number;
  /** True while a new ranking is being worked out. The list stays where it is. */
  readonly busy: boolean;
  readonly selectedId: string | null;
  /**
   * Where every area sits on every vibe, as the page holds it from the list of areas. With
   * it the town of a result is whole, and is the town the page of its area draws. Left
   * out, a town is drawn from the strip of its result, and what the strip does not hold of
   * it is left blank. Nothing is asked of the service for a town either way.
   */
  readonly bands?: readonly VibeBands[] | undefined;
  /** How large the town of a result is drawn. Left out, as the page leaves it, it is what `look.ts` chooses. */
  readonly townDrawn?: TownDrawn | undefined;
  /** Where the line stands that says what a town is. Left out, it is what `look.ts` chooses. */
  readonly lineStands?: LineStands | undefined;
  /** What becomes of a town on a result with no room for one. Left out, it is what `look.ts` chooses. */
  readonly onANarrowResult?: OnANarrowResult | undefined;
  /** Where what says that areas can be compared stands. Left out, it is what the look of comparing chooses. */
  readonly inviteStands?: InviteStands | undefined;
  /**
   * What stands over the list, where its results have room for a town. Left out, it is what
   * `look.ts` chooses. Where nothing does, the page that draws the list says that areas can
   * be compared, and the first result says what a town is.
   */
  readonly over?: OverTheList | undefined;
  /** How high the buttons of a narrow result are. Left out, it is what `look.ts` chooses. */
  readonly buttons?: OnANarrowResultAButtonIs | undefined;
  /** How the two ends of a gauge are drawn on a result. Left out, it is what `look.ts` chooses. */
  readonly ends?: EndsOnAResult | undefined;
  /** How the trade-off of a result is drawn. Left out, it is what `look.ts` chooses. */
  readonly tradeOff?: TradeOffDrawn | undefined;
  /** Where the vibes stand that nobody asked for. Left out, it is what `look.ts` chooses. */
  readonly others?: OthersStand | undefined;
  /** Where what a fit is based on is said. Left out, it is what `look.ts` chooses. */
  readonly fitSaid?: FitSaid | undefined;
  readonly onSelect: (areaId: string) => void;
  readonly onHover: (areaId: string | null) => void;
  readonly onEdit: (operations: Operations) => void;
}

function reducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * The results, as an ordered list: the order is the rank. The first five are
 * cards, each the answer in short, and the rest are rows, which are shorter.
 * Ten are shown at first, and "Show 10 more" shows the rest.
 *
 * The list is drawn in two parts, the first result and the rest, with the map
 * between them. What says that the list is being worked out again stands over
 * the first part, and what shows more and names the release under the rest.
 *
 * Nothing stands over the list: the answer comes first, and the first result
 * stands directly under what refines the search. That areas can be compared,
 * and how, is said once of a list, in sight, and not over it: by the page
 * that draws the list, beside what refines the search. On a narrow result,
 * and wherever the page asks it, the list says it under its first result,
 * which is whole on the first screen of a phone. The way to compare is in the
 * heading of every result.
 *
 * Beside the name of every result, card and row alike, stands the town of its
 * area: a small drawing made by rule from where the area sits on four vibes.
 * It is of one size for every result. A result with no room for a town beside
 * its name, as every result of a phone is, has none: the answer comes first.
 *
 * What a town is, and that it is no picture of the place, is said on no
 * result: the founder asked for that line to go from the results. It is said
 * in the key to the drawings and at the head of the page of an area. What a
 * town leaves blank, and why, is still said with the town, in sight. One line
 * of the look has the line stand once again, where the first town is, and
 * another puts what is said once of a list back over it, in one slip.
 *
 * Under the rest stand two things that say what the list does not hold. Where
 * areas are ranked below the last one listed, a line says so once every
 * listed area is on the page: until then the button that shows more says it.
 * And the areas that are not ranked are listed apart, closed at first.
 *
 * When an area is chosen on the map, its card is marked as the one that is
 * chosen, and is brought into view where that leaves what was pressed where
 * it stands: beside the list, the map stays in the window as the page
 * scrolls. Where the map goes with the page, as on a narrow screen, the page
 * is left where it is. The focus stays where it was.
 *
 * In every result each thing is a line: what it is, and where the area sits on
 * it, drawn as five steps with a picture at each end. The steps of every line
 * stand in one column, in every result of the list, so that the eye runs down
 * them: the list says which names stand in the column before them, and every
 * result lays its lines out by all of them.
 *
 * What is pressed in a result stays under the hand: whatever a press opens
 * or closes in place, the page is held where it stood.
 *
 * While a new ranking is worked out the list stays as it was, at full
 * strength, under a line that says so.
 */
export function ResultList({
  part,
  ranked,
  areas,
  explanations,
  explained,
  explainFailed,
  facts,
  details,
  detailsFailed,
  geometry,
  spec,
  meta,
  served,
  placeNames,
  noFit,
  unranked,
  areasRanked,
  areasListed,
  busy,
  selectedId,
  bands,
  townDrawn = TOWN_DRAWN,
  lineStands = LINE_STANDS,
  onANarrowResult = ON_A_NARROW_RESULT,
  inviteStands = INVITE_STANDS,
  over = OVER_THE_LIST,
  buttons = ON_A_NARROW_RESULT_A_BUTTON_IS,
  ends = ENDS_ON_A_RESULT,
  tradeOff = TRADE_OFF_DRAWN,
  others = OTHERS_STAND,
  fitSaid = WHAT_A_FIT_IS_BASED_ON_IS_SAID_IN_THE,
  onSelect,
  onHover,
  onEdit,
}: Props) {
  const list = useRef<HTMLOListElement>(null);
  const [all, setAll] = useState(false);
  const names = useMemo(() => namesOfPlaces(spec, placeNames), [spec, placeNames]);
  // One scale for the cost of every card, so that the budget is in one place on all of
  // them and a dearer home is drawn further along. It is worked out from the costs in hand.
  const scale = useMemo(() => {
    const costs = (ranked ?? []).slice(0, EXPLAINED).flatMap((area) => {
      const cost = costFor(details[area.area_id], spec);
      return cost === null ? [] : [cost.estimate];
    });
    return scaleOf(costs, spec.budget.amount);
  }, [ranked, details, spec]);
  // An area chosen on the map or in the table is shown in the list, wherever it stands in it.
  const chosenAt = selectedId === null ? -1 : (ranked ?? []).findIndex((area) => area.area_id === selectedId);
  const upTo = all || chosenAt >= SHOWN_AT_FIRST ? (ranked?.length ?? 0) : SHOWN_AT_FIRST;
  // Where this part begins in the ranking: the first result is one part, and the rest another.
  const from = part === "first" ? 0 : 1;
  const shown = (ranked ?? []).slice(from, part === "first" ? 1 : upTo);
  const more = part === "first" ? 0 : Math.max(0, (ranked?.length ?? 0) - upTo);
  // What the town of each result is drawn from, worked out once for a ranking and not at every press.
  const marks = useMemo(
    () => new Map((ranked ?? []).map((area) => [area.area_id, marksOn(area, bands)])),
    [ranked, bands],
  );

  // Every name that stands in the column of names: of each line that a result of the
  // ranking draws, of the results that are shown and of those that are one press away.
  // So the column is as wide in the first result as in the twentieth, and is no wider
  // once more results are shown.
  const columnOf = useMemo(
    () => namesInTheColumn(ranked ?? [], meta, spec, others, fitSaid),
    [ranked, meta, spec, others, fitSaid],
  );

  // What a town reads of the release, and no more: the vibes it is drawn from. Nothing the
  // service says of a vibe it holds to be less sure than the rest is among it.
  const release = useMemo(() => ofATown(meta), [meta]);

  // What a town is drawn from is handed to the bar of areas to compare, which stands at
  // the foot of the screen and is handed nothing by the page: the town of an area is then
  // the same in the bar as beside its result. It is handed over once the list is on the
  // page, and holds where areas sit and nothing of a search.
  const hand = useHandOver();
  useEffect(() => {
    if (ranked === null) return;
    hand({ release, bands, marks: Object.fromEntries(marks) });
  }, [hand, ranked, release, bands, marks]);

  useEffect(() => {
    const holds = list.current;
    if (selectedId === null || holds === null) return;
    const chosen = [...holds.children].find((item) => item.getAttribute("data-area") === selectedId);
    // What was pressed has the focus, where the browser gives a press the focus: a pin of the
    // map, a line of the table, or a button of the result itself.
    if (chosen) bringBeside(holds, chosen, document.activeElement, !reducedMotion());
  }, [selectedId]);

  if (ranked === null) {
    // The place of each card is held while the first ranking is waited for: one before the
    // map, and the rest after it, so that the map does not move when they come.
    if (!busy && part === "rest") return null;
    return (
      <div className={styles.list} aria-busy={busy}>
        {busy ? (
          Array.from({ length: part === "first" ? 1 : EXPLAINED - 1 }, (_, at) => (
            // The place of a card is a box, as a card is: what is coming is read on cream.
            <Frame key={at} kind="box">
              <Skeleton lines={4} />
            </Frame>
          ))
        ) : (
          <Frame kind="plain">
            <p className={styles.waiting}>{RESULTS.waiting}</p>
          </Frame>
        )}
      </div>
    );
  }

  const showTheRest = () => {
    setAll(true);
    // The button goes once it is pressed. The focus goes to the list it added to, and not to nothing.
    list.current?.focus({ preventScroll: true });
  };

  const shared = { facts, spec, meta, release, names, noFit, townDrawn, ends, others, fitSaid, columnOf, onSelect, onHover, onEdit };
  // What a town is, is said on no result unless the look has it stand once, of every town
  // of the list. Where nothing then stands over the list it stands with the first town, in
  // the first result, and is handed to no other.
  const lineOf = (at: number) => (over === "nothing" && lineStands === "once" && at === 0 ? TOWNS.line : undefined);
  const results = (
    <ol
      ref={list}
      className={styles.list}
      // The rest of the list begins at the second result, and says so.
      start={part === "rest" ? 2 : undefined}
      aria-label={part === "first" ? RESULTS.listLabel : RESULTS.restLabel}
      aria-busy={busy}
      // How large its towns are drawn, whether their line stands anywhere, what becomes of a
      // town on a result with no room for one, and how high the buttons of a narrow result
      // are: the style sheet reads all four.
      data-town={townDrawn}
      data-line={lineStands}
      data-narrow={onANarrowResult}
      data-buttons={buttons}
      // It can be given the focus by "Show 10 more", and is no stop of its own.
      tabIndex={-1}
      // Heard on the way down, before whatever was pressed hears of it and anything has changed.
      onClickCapture={(event) => {
        const pressed = pressedIn(event.currentTarget, event.target);
        if (pressed !== null) hold(pressed);
      }}
    >
      {shown.map((area, within) => {
        const at = from + within;
        const summary = areas.find((known) => known.area_id === area.area_id);
        if (!summary) return null;
        const selected = selectedId === area.area_id;
        const drawnFrom = marks.get(area.area_id) ?? marksOn(area, bands);
        if (at >= EXPLAINED) {
          return (
            <ResultRow
              key={area.area_id}
              {...shared}
              area={area}
              summary={summary}
              marks={drawnFrom}
              selected={selected}
            />
          );
        }
        return (
          <ResultCard
            key={area.area_id}
            {...shared}
            area={area}
            summary={summary}
            marks={drawnFrom}
            selected={selected}
            line={lineOf(at)}
            tradeOffDrawn={tradeOff}
            explanation={explanations.find((one) => one.area_id === area.area_id)}
            explained={explained}
            explainFailed={explainFailed}
            detail={details[area.area_id]}
            detailFailed={detailsFailed.includes(area.area_id)}
            geometry={geometry ?? null}
            scale={scale}
          />
        );
      })}
    </ol>
  );
  return (
    <>
      {/* That the list is being worked out again is said in words, and the list is not dimmed:
          dimmed, its text falls below the contrast it needs. The line in the form is the one
          that is announced, so this one is not. */}
      {busy && part === "first" ? <p className={styles.workingOut}>{RESULTS.working}</p> : null}
      {/* A search that ranks one area has no rest of a list to draw. */}
      {shown.length === 0 ? null : part === "first" ? (
        // What holds the first part of the list and what is said over it is as wide as a
        // result is, and says how wide that is: so what is said goes where the towns go,
        // by the width of a result and never by the width of the screen.
        <div
          className={styles.listed}
          data-town={townDrawn}
          data-narrow={onANarrowResult}
          data-invite={inviteStands}
          data-over={over}
        >
          {over === "slip" && (invites("over", inviteStands) || lineStands === "once") ? (
            // One slip, and in it one paragraph: what is said over the list is said in as
            // few lines as it takes, since the first result stands under it.
            <p className={styles.above}>
              {/* That areas can be compared is said before anybody has chosen one: over the
                  list where a result has room for it, and under the first result where it has not. */}
              <Invite stands="over" wide={inviteStands} />
              {/* Where the look has it stand once: what a town is, and that it is no picture
                  of the place, of every town of the list, over the first of them. */}
              {lineStands === "once" ? <span className={styles.towns}> {TOWNS.line}</span> : null}
            </p>
          ) : null}
          {results}
          {invites("under", inviteStands) ? (
            <p className={styles.underFirst}>
              <Invite stands="under" wide={inviteStands} />
            </p>
          ) : null}
        </div>
      ) : (
        results
      )}
      {part === "rest" ? (
        // What stands under the list stands in one plain edge: the list does not end on the grass.
        <Frame kind="plain" className={styles.under} bare>
          {/* On one line where there is room, so that what the list does not hold costs the
              page no height before it is opened. */}
          <div className={styles.more}>
            {more > 0 ? (
              <Press onPress={showTheRest} className={styles.showMore}>
                {RESULTS.showMore(more)}
              </Press>
            ) : areasListed < areasRanked ? (
              // Areas stand below the last one listed. A list once stopped at 20 of 22 and said nothing.
              <p className={styles.below}>{RESULTS.listed(areasListed, areasRanked)}</p>
            ) : null}
            <NotRanked unranked={unranked} areas={areas} meta={meta} spec={spec} />
          </div>
          <footer className={styles.foot}>
            {ranked.length > EXPLAINED ? <span>{RESULTS.firstFive}</span> : null}
            <span>
              {RESULTS.foot.release} <code>{served.release_id}</code>
            </span>
            <span>
              {RESULTS.foot.engine} <code>{served.engine_version}</code>
            </span>
          </footer>
        </Frame>
      ) : null}
    </>
  );
}
