"use client";

import Link from "next/link";
import { useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { flushSync } from "react-dom";

import { Approx } from "@/components/kit/Approx/Approx";
import { Art } from "@/components/kit/Art/Art";
import { Frame } from "@/components/kit/Frame/Frame";
import { Pennant } from "@/components/kit/Pennant/Pennant";
import { Press } from "@/components/kit/Press/Press";
import { restsOnWords } from "@/content/bands";
import { CARD } from "@/content/card";
import { FACT_COLUMNS } from "@/content/facts";
import { MAP_CARD } from "@/content/map";
import { COST, JOURNEYS, RESULTS } from "@/content/search";
import type { Handed } from "@/lib/api/handed";
import type {
  AreaData,
  AreaSummary,
  ExplainedSentence,
  Explanation,
  Fact,
  GeometryData,
  Operations,
  PreferenceSpec,
  RankedArea,
  StripMark,
  Tag,
} from "@/lib/api/schema";
import { fitOf } from "@/lib/map/fill";
import { paths } from "@/lib/paths";
import { costFor, nearestStation, type Facts } from "@/lib/search/card";
import { edits } from "@/lib/search/edits";
import type { Mark } from "@/lib/town/bands";
import type { Release } from "@/lib/town/release";
import { endsOf, isRange } from "@/lib/vibes";

import { CompareButton } from "../CompareTray/CompareButton";
import { CostRange, type Scale } from "../CostRange/CostRange";
import { FactRow } from "../FactRow/FactRow";
import { BesideName } from "../BesideName/BesideName";
import { LocatorMap } from "../LocatorMap/LocatorMap";
import { factAbout, Sentence } from "../Sentence/Sentence";
import { Skeleton } from "../Skeleton/Skeleton";
import { SourceNote } from "../SourceNote/SourceNote";
import { isFromPart, Strip, type Ends } from "../Strip/Strip";
import { Town } from "../Town/Town";
import { linesOf, measuredBy, standsLower } from "./lines";
import {
  BESIDE_A_TRADE_OFF,
  DRAWING_OF_A_TRADE_OFF,
  LETTERS_ON_A_LINE_OF_A_NAME,
  LINES_WITH_NO_FOLD,
  type FitSaid,
  type LinesOverTheFold,
  type OthersStand,
  type TownDrawn,
  type TradeOffDrawn,
} from "./look";
import { Opens } from "./Opens";
import { Completeness, isNotWhole, JourneyList, Missing, ScoreBreakdown } from "./parts";
import styles from "./ResultList.module.css";
import { isGivenUp } from "./tradeoff";

/** How many reasons the API writes for a result, at most. Each is in the working. */
const REASONS = 3;

interface Shared {
  readonly area: RankedArea;
  readonly summary: AreaSummary;
  readonly facts: Facts;
  readonly spec: PreferenceSpec;
  readonly meta: Handed;
  /** What a town reads of the release, and no more of it: the vibes it is drawn from. */
  readonly release: Release;
  /** The name of each place of the search, by place id. */
  readonly names: ReadonlyMap<string, string>;
  /** True when nothing is set to rank by, so the fit says nothing. */
  readonly noFit: boolean;
  /**
   * Where the area sits on the vibes, of which its town is drawn: what its strip says, and
   * what the page holds of the area besides. It holds no rank and no fit.
   */
  readonly marks: readonly Mark[];
  /** How large the town is drawn, which is the same for every result. */
  readonly townDrawn: TownDrawn;
  /** How the two ends of a gauge are drawn, which is the same for every result. */
  readonly ends: Ends;
  /** Where the vibes stand that nobody asked for, which is the same for every result. */
  readonly others: OthersStand;
  /** Where what a fit is based on is said, which is the same for every result. */
  readonly fitSaid: FitSaid;
  /** How many lines of a narrow result stand over the press that shows the rest, which is the same for every result. */
  readonly linesOver: LinesOverTheFold;
  /**
   * Every name that stands in the column of names, of every result of the list: what an
   * area has of each thing then begins in one place from one result to the next.
   */
  readonly columnOf: readonly string[];
  readonly selected: boolean;
  readonly onSelect: (areaId: string) => void;
  readonly onHover: (areaId: string | null) => void;
  readonly onEdit: (operations: Operations) => void;
}

interface HeadingProps extends Pick<Shared, "area" | "summary" | "noFit" | "release" | "marks" | "townDrawn"> {
  readonly id: string;
  /** True where the fit is not whole, and two words say so beside it. */
  readonly approx: boolean;
  /**
   * What is said once of every town of the list, where the look has it stand with this
   * town: what a town is, and that it is no picture of the place. Left out, as it is unless
   * the look says otherwise, this result does not say it.
   */
  readonly line?: string | undefined;
}

function Heading({ area, summary, noFit, release, marks, townDrawn, id, approx, line }: HeadingProps) {
  return (
    <header className={styles.heading}>
      {/* A pennant with its number, the same for the first as for the tenth: nobody wins. */}
      <p className={styles.rank}>
        <Pennant rank={area.rank} />
      </p>
      <div className={styles.titled}>
        <h3 id={id} className={styles.name}>
          {/* One press from the name of a result to the page of its area. The page is fetched
              when the link is pressed, and not before: which areas a search led to is not told
              to anyone by fetching their pages ahead of time. */}
          <Link className={`${styles.toArea} target-min`} href={paths.area(summary)} prefetch={false}>
            {summary.name}
          </Link>
        </h3>
        {/* Beside the name, smaller: the label its publisher gives the area, which says its
            borough, and that the name is a draft. A name that says its borough says it once.
            A row says it as a card does: a name with no borough beside it was taken for a
            name somebody had checked, and two areas of one name could not be told apart. */}
        <BesideName area={summary} className={styles.borough} />
        {noFit ? null : (
          <p className={styles.fit}>
            <span className={styles.fitLabel}>{RESULTS.fit} </span>
            <span className={styles.fitFigure}>{RESULTS.fitOf(fitOf(area.score))}</span>
            {/* A fit is never given alone where it is not whole: two words say so, with the
                fit, and the working says what it is based on. */}
            {approx ? <Approx className={styles.approx} /> : null}
          </p>
        )}
        {/* The way to compare stands where the eye goes: in the heading, beside the town of
            the area, and not at the foot of the result. It is the same on the first result
            as on the tenth, and says nothing of how an area did: nobody wins. */}
        <CompareButton area={summary} small />
      </div>
      {/* Where the look has it stand: what a town is, said once of every town of the list,
          where the first of them is. It is the list's to say and no part of the town: it says
          nothing of this area, and the town of this result is the town every other result
          has. It is heard before the town it stands under is, and what that town says of
          itself follows it. */}
      {line === undefined ? null : <p className={styles.towns}>{line}</p>}
      {/* The town of the area, beside its name and its fit and after both: the rank, the name
          and the fit are read first, and heard first. It is the same for the first result as
          for the tenth, and is handed no rank and no fit: nobody wins. */}
      <Town marks={marks} meta={release} of={summary.name} large={townDrawn === "screen"} className={styles.town} />
    </header>
  );
}

/**
 * The box of the area that is chosen, which the map draws under itself. It is found as a
 * person finds it, by what it is and by its name. `null` where the map is not drawn.
 */
function boxOfTheMap(): HTMLElement | null {
  const boxes = [...document.querySelectorAll<HTMLElement>("section[aria-label]")];
  return boxes.find((one) => one.getAttribute("aria-label") === MAP_CARD.label) ?? null;
}

/**
 * What is one press away, inside the working: the area's page, the map, and hiding the area.
 *
 * What shows an area on the map leads to the map. A press marks the area there and opens
 * its box under the map, which may be a long way from the working of a result, and out of
 * sight of whoever cannot see the page at all. So the press says what it did, in a line
 * that is heard as it is written, and the focus goes to the box the press opened, which
 * is brought into sight with it: the box leads back to the list.
 *
 * The line is said for as long as the area is the one that is chosen. Once another is
 * chosen it would say of this one what is no longer so.
 */
function Actions({ summary, selected, onSelect, onEdit }: Pick<Shared, "summary" | "selected" | "onSelect" | "onEdit">) {
  const [did, setDid] = useState<string | null>(null);

  const showOnTheMap = () => {
    // The page draws what the press chose before the box is looked for: it is drawn of the press.
    flushSync(() => onSelect(summary.area_id));
    const box = boxOfTheMap();
    box?.focus();
    setDid(box === null ? CARD.notOnMap(summary.name) : CARD.shownOnMap(summary.name));
  };

  return (
    <div className={styles.acts}>
      <ul className={styles.actions} aria-label={RESULTS.actions}>
        <li>
          {/* The page is fetched when the link is pressed, and not before: which areas a search
              led to is not told to anyone by fetching their pages ahead of time. */}
          <Press href={paths.area(summary)}>{RESULTS.openArea(summary.name)}</Press>
        </li>
        <li>
          <Press onPress={showOnTheMap}>{RESULTS.showOnMap(summary.name)}</Press>
        </li>
        <li>
          {/* It takes the area out of the answer, and is drawn as what takes away is. */}
          <Press kind="stop" onPress={() => onEdit(edits.areaHide(summary.area_id))}>
            {RESULTS.hide(summary.name)}
          </Press>
        </li>
      </ul>
      {/* It is on the page from the first, and holds nothing, so that what comes to stand in
          it is heard. It takes no room until it speaks. */}
      <p className={styles.did} role="status">
        {selected ? did : null}
      </p>
    </div>
  );
}

interface ResultProps extends Pick<Shared, "summary" | "selected" | "onHover"> {
  /** A card is one of the first five, and stands in a box. A row is one of the rest, in a plain edge. */
  readonly kind: "card" | "row";
  readonly areaId: string;
  /** The id of the heading that names the result. */
  readonly named: string;
  /** The answer: what the result says before anything is pressed. */
  readonly children: ReactNode;
  /** The full working of the result, which "Show the working" opens under it. */
  readonly working: ReactNode;
}

/**
 * One result: the answer, in a box, and under it the working, in a box of its own, which
 * is drawn only while it is open. A result leads three ways on. The way to compare stands
 * in its heading, beside its town, where the eye goes. The answer ends in the other two,
 * in one row: its full working, which opens in place, and the areas most like it, which
 * are on its own page.
 *
 * None of the three is the button that matters most in sight: that is Search.
 */
function Result({ kind, areaId, summary, selected, named, onHover, children, working }: ResultProps) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const button = useRef<HTMLButtonElement>(null);

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key !== "Escape" || !open) return;
    // The innermost open one closes. One that holds it stays as it is.
    event.stopPropagation();
    setOpen(false);
    button.current?.focus();
  };

  return (
    <li
      className={styles.item}
      data-area={areaId}
      data-kind={kind}
      onMouseEnter={() => onHover(areaId)}
      onMouseLeave={() => onHover(null)}
      onFocus={() => onHover(areaId)}
      onBlur={() => onHover(null)}
    >
      <article
        className={styles.result}
        aria-labelledby={named}
        aria-current={selected ? "true" : undefined}
        // It can be given the focus by "Show in the list", and is no stop of its own.
        tabIndex={-1}
      >
        <Frame
          // The chosen area is in hand: the inner rule of its box is amber, and it says so to a screen reader.
          kind={kind === "row" ? "plain" : selected ? "box-on" : "box"}
          className={kind === "row" ? styles.row : styles.card}
          bare
        >
          {children}
          <div className={styles.waysOn}>
            {/* The keys are heard here for what is inside: the button itself is the control. */}
            {/* eslint-disable-next-line jsx-a11y/no-static-element-interactions */}
            <span onKeyDown={onKeyDown}>
              <Opens
                ref={button}
                name={RESULTS.workingOf(summary.name)}
                open={open}
                controls={id}
                onPress={() => setOpen(!open)}
              >
                {RESULTS.showWorking}
              </Opens>
            </span>
            {/* Which page a person reads next is told to no server ahead of time: the part draws no link that is fetched ahead. */}
            <Press href={paths.area(summary, "alike")} name={RESULTS.moreLikeOf(summary.name)}>
              {RESULTS.moreLike}
            </Press>
          </div>
        </Frame>
        <Frame kind="box" id={id} className={styles.working} hidden={!open} onKeyDown={onKeyDown} bare>
          {open ? (
            <>
              {/* Whose working it is, on a board at the head of its box. */}
              <p className={styles.workingOf}>{CARD.workingOf(summary.name)}</p>
              {working}
            </>
          ) : null}
        </Frame>
      </article>
    </li>
  );
}

interface CardProps extends Shared {
  /** The reasons for this area, where the API gave any. */
  readonly explanation?: Explanation;
  /** True once the reasons for this ranking are in, whether or not this area has any. */
  readonly explained: boolean;
  /** True when the reasons could not be loaded. */
  readonly explainFailed?: boolean;
  /** The area's profile, once it is in. */
  readonly detail?: AreaData;
  readonly detailFailed?: boolean;
  /** The boundary of every area, once it has come. The working draws where the area is from it. */
  readonly geometry: GeometryData | null;
  /** The scale the cost of every card of the list is drawn on. */
  readonly scale?: Scale | null;
  /** What is said once of every town of the list, where this result is the one that says it. */
  readonly line?: string | undefined;
  /** How the trade-off is drawn, which is the same for every result. */
  readonly tradeOffDrawn: TradeOffDrawn;
}

/** The trade-off as the card shows it: the API's, where the ranking says the area does that thing badly. */
function tradeOffOf(
  area: RankedArea,
  explanation: Explanation | undefined,
  spec: PreferenceSpec,
  meta: Handed,
): ExplainedSentence | null {
  const given = explanation?.trade_off ?? null;
  return given !== null && isGivenUp(area, given, spec.commutes, meta.limits.trade_off_max_utility) ? given : null;
}

interface TradeOffProps extends Pick<Shared, "area" | "facts" | "spec" | "meta"> {
  readonly explanation?: Explanation;
  readonly waiting: boolean;
  /** True when what Burro wrote of the result could not be loaded. */
  readonly failed: boolean;
  readonly drawn: TradeOffDrawn;
}

/**
 * What the area gives up, under the word "Trade-off". The sentence is the
 * API's, word for word. It is shown only if the ranking itself says the area
 * does that thing badly, so that a strength is never put under the word.
 * With none to show, the card says that none was found.
 *
 * It stands out by where it stands and how it is drawn: on a band of its own,
 * or in a box of its own, with a drawing that says one thing was given for
 * another. Nothing of it is red, and nothing of it says that the area is the
 * worse for it. The key of its source is in the working.
 *
 * Where its figure is not whole, a band that was worked out from some of what
 * goes into its vibe or a journey that was estimated, the sentence says so
 * itself, in the API's words, and nothing is said of it a second time. Nor is
 * it said a second time that a journey is over the limit that was set: the
 * sentence says by how much, and the table of journeys in the working says
 * which way each journey falls.
 */
function TradeOff({ area, explanation, facts, spec, meta, waiting, failed, drawn }: TradeOffProps) {
  const sentence = tradeOffOf(area, explanation, spec, meta);
  // Where the service wrote nothing of the area, and nothing is waited for or failed, there
  // is nothing to say under the word: a heading over nothing is not drawn.
  if (explanation === undefined && !waiting && !failed) return null;
  return (
    // It is no part of the page that a person goes to by its name: a page of five results
    // would hold five of one name. Its heading names it.
    <div className={styles.tradeOff} data-drawn={drawn}>
      <h4 className={styles.tradeOffTitle}>
        <Art name={DRAWING_OF_A_TRADE_OFF[BESIDE_A_TRADE_OFF[drawn]]} alt="" />
        <span className={styles.tradeOffWord}>{RESULTS.tradeOffTitle}</span>
      </h4>
      <div className={styles.tradeOffSaid}>
        {explanation ? (
          sentence !== null ? (
            <Sentence sentence={sentence} facts={facts} meta={meta} source={false} />
          ) : (
            <p>{RESULTS.noTradeOff}</p>
          )
        ) : waiting ? (
          <Skeleton />
        ) : failed ? (
          <p className={styles.failed}>{CARD.tradeOffFailed}</p>
        ) : null}
      </div>
    </div>
  );
}

interface SourceOfProps extends Pick<Shared, "summary" | "facts" | "meta"> {
  readonly sentence: ExplainedSentence;
}

/**
 * The source of the trade-off, in the working: what its sentence is about, by the name
 * the API gives the fact, and the key of its source. The sentence itself stands on the
 * result, and is not said a second time: nor are the figures of its fact laid out again,
 * which say from the other side what the sentence says.
 */
function SourceOfTheTradeOff({ sentence, facts, summary, meta }: SourceOfProps) {
  const about = factAbout(sentence, facts);
  return (
    <div className={styles.part}>
      <h4 className={styles.tag}>{CARD.sourceOfTheTradeOff}</h4>
      <div className={styles.ofWhat}>
        {about.map((fact) => (
          <p key={fact.fact_id}>{fact.label}</p>
        ))}
        <SourceNote facts={about} of={RESULTS.sourceOfTradeOff(summary.name)} meta={meta} />
      </div>
    </div>
  );
}

interface VibesProps extends Pick<Shared, "summary" | "facts" | "meta"> {
  readonly marks: readonly StripMark[];
  /**
   * The fact of each measure whose line on the result is drawn from one, in the order the
   * search holds them. `undefined` of one whose fact may yet come. Left out of a row,
   * which draws nothing of a measure but its name.
   */
  readonly measures?: readonly (Fact | undefined)[];
  /** True while the facts of the result may yet come, with its reasons or with its profile. */
  readonly waiting: boolean;
  /**
   * True where the result shows a figure whose source the working does not hold, as a row
   * shows what a home costs: the way to the page of the area is then drawn, whatever is
   * held of the gauges.
   */
  readonly away?: boolean;
}

/**
 * The figures behind each gauge, in the working: the fact of each vibe the API gave with
 * the result, of those that were asked for and of the others, and of each measure that
 * was asked for, each with the key of its source. A band that was worked out from some of
 * what goes into its vibe says so here, in the API's words, after the mark that stands
 * beside its gauge.
 *
 * The page holds the facts of the first five results and asks for no other: so a row has
 * none, unless another search left them, and a card has none where they failed to come.
 * A gauge is drawn of the ranking all the same. Of one whose fact the page does not hold,
 * the working says what the ranking gave, laid out as its fact would be, and one link
 * under them leads to the page of the area, which holds every figure with its source and
 * its date. So no gauge of a result is without a way to its source, and no figure.
 */
function Vibes({ marks, measures = [], facts, meta, summary, waiting, away = false }: VibesProps) {
  const drawn = marks.flatMap((mark) => {
    const fact = facts[mark.fact_id];
    const tag = meta.tags.find((one) => one.tag_id === mark.tag_id);
    // A vibe the release does not name has no line on the result, and none here without its fact.
    return fact === undefined && tag === undefined ? [] : [{ mark, fact, tag }];
  });
  // A measure whose fact did not come has its name on the result and no figure: nothing of it is owed a source.
  const measured = measures.filter((fact) => fact !== undefined || waiting);
  if (drawn.length === 0 && measured.length === 0 && !away) return null;
  const elsewhere = !waiting && (away || drawn.some(({ fact }) => fact === undefined));
  return (
    <div className={styles.part}>
      <h4 className={styles.tag}>{CARD.vibes}</h4>
      <ul className={styles.vibes}>
        {drawn.map(({ mark, fact, tag }) => {
          if (fact === undefined) {
            return <li key={mark.tag_id}>{waiting || tag === undefined ? <Skeleton /> : <Placed mark={mark} tag={tag} />}</li>;
          }
          const { known, parts, partly } = fact.slots;
          return (
            <li key={mark.tag_id}>
              <FactRow fact={fact} withSource={false} />
              {isFromPart(fact) && known !== undefined && parts !== undefined ? (
                <p className={styles.marked}>
                  <Approx
                    says={restsOnWords({ known, parts, partly: partly === undefined || partly === "" ? null : partly }, "full")}
                  />
                </p>
              ) : null}
              <SourceNote facts={[fact]} of={fact.label} meta={meta} judgementSaid />
            </li>
          );
        })}
        {measured.map((fact, at) => (
          // The measures of a search are in one order, which no answer changes: each is told by its place.
          <li key={fact?.fact_id ?? at}>{fact === undefined ? <Skeleton /> : <FactRow fact={fact} />}</li>
        ))}
      </ul>
      {elsewhere ? (
        <p className={styles.elsewhere}>
          <Art name="ui-key" alt="" />
          {/* The page is fetched when the link is pressed, and not before: which areas a search
              led to is not told to anyone by fetching their pages ahead of time. */}
          <Link className="target-min" href={paths.area(summary)} prefetch={false}>
            {CARD.sourcesOn(summary.name)}
          </Link>
        </p>
      ) : null}
    </div>
  );
}

interface PlacedProps {
  readonly mark: StripMark;
  readonly tag: Tag;
}

/**
 * Where an area sits on a vibe, as the ranking gave it, under the names the columns of its
 * fact bear: the band, or the bands of an area that varies, and the ends the bands are
 * counted between. Nothing else of the vibe is known without its fact, and nothing else
 * is said.
 */
function Placed({ mark, tag }: PlacedProps) {
  const [low, high] = endsOf(tag);
  return (
    <div className={styles.placed} role="group" aria-label={tag.label}>
      <p>{tag.label}</p>
      <dl className={styles.says}>
        <div>
          <dt>{isRange(mark) ? FACT_COLUMNS.bands : FACT_COLUMNS.band}</dt>
          <dd>{isRange(mark) ? `${mark.spread_low} ${FACT_COLUMNS.to} ${mark.spread_high}` : mark.band}</dd>
        </div>
        <div>
          <dt>{FACT_COLUMNS.ends}</dt>
          <dd>{`${low} ${FACT_COLUMNS.to} ${high}`}</dd>
        </div>
      </dl>
    </div>
  );
}

/**
 * One of the first five results. Its short form is the answer, and holds no
 * more than this: its rank, its name and what stands beside the name, its
 * fit, the way to compare it and the town of the area; a line for each thing
 * that was asked for, with its gauge or its figure; and its trade-off.
 * Everything else is the working, one press away: where the area is, why it
 * fits, the figures behind the trade-off and behind each gauge, what has no
 * figure, each journey, the cost, and how the fit is worked out.
 *
 * Every sentence is the API's. No key of a source stands on the answer: in the
 * working every sentence and every figure ends in its source. Opening one
 * result closes no other.
 */
export function ResultCard({
  area,
  summary,
  explanation,
  explained,
  explainFailed = false,
  detail,
  detailFailed = false,
  facts,
  spec,
  meta,
  release,
  names,
  noFit,
  marks,
  townDrawn,
  ends,
  others,
  fitSaid,
  linesOver,
  tradeOffDrawn,
  columnOf,
  geometry,
  scale = null,
  line,
  selected,
  onSelect,
  onHover,
  onEdit,
}: CardProps) {
  const id = useId();
  const station = nearestStation(detail);
  const cost = costFor(detail, spec);
  const waitingForDetail = detail === undefined && !detailFailed;
  const waitingForReasons = !explained && !explainFailed;
  const { area_id: areaId } = area;
  const reasons = explanation?.reasons.slice(0, REASONS) ?? [];
  const tradeOff = tradeOffOf(area, explanation, spec, meta);
  const lines = linesOf(area, meta, spec, { facts, places: names }, { others, fitSaid });
  const inShort = fitSaid === "working";
  // What the trade-off is about has its figures under the trade-off, and is not said a second time.
  const ofTheTradeOff = tradeOff === null ? [] : factAbout(tradeOff, facts).map((fact) => fact.fact_id);
  // A visit is a search for somewhere to stay: nothing of what a home costs is drawn of one.
  const aVisit = spec.tenure === "visit";
  // What a home costs stands on the line of the budget. Its source is with the cost, in the
  // working: where the cost did not come, the page of the area holds it.
  const costShown = lines.asked.some((one) => one.thing.kind === "budget" && one.figure !== undefined);

  const working = (
    <div className={styles.opened}>
      <div className={styles.part}>
        <h4 className={styles.tag}>{RESULTS.whereTitle}</h4>
        <div className={styles.where}>
          <div className={styles.whereWords}>
            {explanation ? (
              <Sentence sentence={explanation.orientation} facts={facts} of={summary.name} />
            ) : waitingForReasons ? (
              <Skeleton />
            ) : null}
            {station ? <FactRow fact={station} /> : waitingForDetail ? <Skeleton /> : null}
          </div>
          <LocatorMap geometry={geometry} areaId={areaId} name={summary.name} />
        </div>
      </div>

      {/* Where the service wrote nothing of the area there are no reasons to give, to wait for or to fail. */}
      {explanation === undefined && !waitingForReasons && !explainFailed ? null : (
        <div className={styles.part}>
          <h4 className={styles.tag}>{RESULTS.reasonsTitle}</h4>
          {explanation ? (
            reasons.length > 0 ? (
              <ol className={styles.reasons}>
                {reasons.map((reason, at) => (
                  <li key={reason.fact_ids.join(" ")}>
                    <Sentence sentence={reason} facts={facts} of={RESULTS.sourceOfReason(at + 1, summary.name)} meta={meta} />
                  </li>
                ))}
              </ol>
            ) : (
              <p>{RESULTS.noReasons}</p>
            )
          ) : waitingForReasons ? (
            <Skeleton />
          ) : explainFailed ? (
            <p className={styles.failed}>{RESULTS.reasonsFailed}</p>
          ) : null}
        </div>
      )}

      {tradeOff === null ? null : <SourceOfTheTradeOff sentence={tradeOff} facts={facts} summary={summary} meta={meta} />}

      <Vibes
        marks={area.strip.filter((mark) => !ofTheTradeOff.includes(mark.fact_id))}
        measures={measuredBy(area, spec, facts).filter((fact) => fact === undefined || !ofTheTradeOff.includes(fact.fact_id))}
        facts={facts}
        meta={meta}
        summary={summary}
        waiting={waitingForReasons || waitingForDetail}
        away={costShown && cost === null && !waitingForDetail}
      />

      <Missing
        area={area}
        missing={explanation?.missing}
        waiting={waitingForReasons}
        facts={facts}
        {...(inShort ? { meta, spec } : {})}
      />

      {area.legs.length > 0 ? (
        <div className={styles.part}>
          <h4 className={styles.tag}>{JOURNEYS.title}</h4>
          <JourneyList
            area={area}
            commutes={spec.commutes}
            combine={spec.commute_combine}
            cutoffs={meta.limits.cutoff_minutes}
            names={names}
            facts={facts}
          />
        </div>
      ) : null}

      {aVisit ? null : (
        <div className={styles.part}>
          <h4 className={styles.tag}>{COST.title}</h4>
          {cost ? (
            <CostRange fact={cost.fact} estimate={cost.estimate} budget={spec.budget} scale={scale} />
          ) : waitingForDetail ? (
            <Skeleton lines={2} />
          ) : detailFailed ? (
            <p className={styles.failed}>{RESULTS.detailsFailed}</p>
          ) : (
            <p>{COST.none}</p>
          )}
        </div>
      )}

      {area.contributions.length > 0 ? (
        <div className={styles.part}>
          <ScoreBreakdown area={area} meta={meta} name={summary.name} facts={facts} />
        </div>
      ) : null}
      <div className={styles.part}>
        <Actions summary={summary} selected={selected} onSelect={onSelect} onEdit={onEdit} />
      </div>
    </div>
  );

  return (
    <Result
      kind="card"
      areaId={areaId}
      summary={summary}
      selected={selected}
      named={`${id}-name`}
      onHover={onHover}
      working={working}
    >
      <div className={styles.top}>
        <Heading
          area={area}
          summary={summary}
          noFit={noFit}
          release={release}
          marks={marks}
          townDrawn={townDrawn}
          id={`${id}-name`}
          approx={inShort && isNotWhole(area)}
          line={line}
        />
        {/* Such an area stands below every area that has the figure, whatever its fit: said
            under the fit, where a higher fit is seen to stand under a lower. */}
        {inShort && standsLower(area, meta, spec) ? <p className={styles.lower}>{CARD.listedLower}</p> : null}
        {/* Where the look has it said on the result, directly after the fit: it says how far the fit is to be trusted. */}
        {inShort ? null : <Completeness area={area} meta={meta} spec={spec} />}
      </div>
      <Strip
        marks={lines.marks}
        tags={meta.tags}
        facts={facts}
        of={summary.name}
        unplaced={lines.unplaced}
        asked={lines.asked}
        ends={ends}
        names={columnOf}
        fold={{ over: linesOver, most: LINES_WITH_NO_FOLD, letters: LETTERS_ON_A_LINE_OF_A_NAME }}
      />
      <TradeOff
        area={area}
        explanation={explanation}
        facts={facts}
        spec={spec}
        meta={meta}
        waiting={waitingForReasons}
        failed={explainFailed}
        drawn={tradeOffDrawn}
      />
    </Result>
  );
}

/**
 * One of results 6 to 20, in short: rank, name, what stands beside the name,
 * fit, the town of the area, and a line for each thing that was asked for. The
 * API writes reasons for the first five only, so a row has no trade-off.
 * Its working is one press away: the figures behind its gauges with the way
 * to their source, what its fit is based on, the journeys, and how the fit is
 * worked out.
 *
 * Its lines are those of a card, drawn of what the ranking gives: the gauge of
 * a vibe, how long a journey takes, and what a home costs. Where an area stands
 * on a measure is in the fact of the measure, and the page asks for the facts
 * of the first five results alone: so the line of a measure says its name, and
 * says the same whatever facts another search left.
 */
export function ResultRow({
  area,
  summary,
  facts,
  spec,
  meta,
  release,
  names,
  noFit,
  marks,
  townDrawn,
  ends,
  others,
  fitSaid,
  linesOver,
  columnOf,
  selected,
  onSelect,
  onHover,
  onEdit,
}: Shared) {
  const id = useId();
  const { area_id: areaId } = area;
  const lines = linesOf(area, meta, spec, { facts: null, places: names }, { others, fitSaid });
  const inShort = fitSaid === "working";
  // A row holds no cost with its source: the page of the area does.
  const costShown = lines.asked.some((one) => one.thing.kind === "budget" && one.figure !== undefined);

  const working = (
    <div className={styles.opened}>
      {/* Nothing is asked of the service for a row, so nothing of it is waited for. */}
      <Vibes marks={area.strip} facts={facts} meta={meta} summary={summary} waiting={false} away={costShown} />
      {inShort ? <Missing area={area} waiting={false} facts={facts} meta={meta} spec={spec} /> : null}
      {area.legs.length > 0 ? (
        <div className={styles.part}>
          <h4 className={styles.tag}>{JOURNEYS.title}</h4>
          <JourneyList
            area={area}
            commutes={spec.commutes}
            combine={spec.commute_combine}
            cutoffs={meta.limits.cutoff_minutes}
            names={names}
            facts={facts}
          />
        </div>
      ) : null}
      {area.contributions.length > 0 ? (
        <div className={styles.part}>
          <ScoreBreakdown area={area} meta={meta} name={summary.name} facts={facts} />
        </div>
      ) : null}
      <div className={styles.part}>
        <Actions summary={summary} selected={selected} onSelect={onSelect} onEdit={onEdit} />
      </div>
    </div>
  );

  return (
    <Result
      kind="row"
      areaId={areaId}
      summary={summary}
      selected={selected}
      named={`${id}-name`}
      onHover={onHover}
      working={working}
    >
      <Heading
        area={area}
        summary={summary}
        noFit={noFit}
        release={release}
        marks={marks}
        townDrawn={townDrawn}
        id={`${id}-name`}
        approx={inShort && isNotWhole(area)}
      />
      {inShort && standsLower(area, meta, spec) ? <p className={styles.lower}>{CARD.listedLower}</p> : null}
      {inShort ? null : <Completeness area={area} meta={meta} spec={spec} />}
      {/* In short: a row never says that a band is not whole. Said of a row only where its
          fact happened to be in hand, it came and went as other searches were made. It is
          one press away, on the page of the area. */}
      <Strip
        marks={lines.marks}
        tags={meta.tags}
        facts={facts}
        of={summary.name}
        unplaced={lines.unplaced}
        asked={lines.asked}
        short
        rests={false}
        ends={ends}
        names={columnOf}
        fold={{ over: linesOver, most: LINES_WITH_NO_FOLD, letters: LETTERS_ON_A_LINE_OF_A_NAME }}
      />
    </Result>
  );
}
