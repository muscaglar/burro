"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { MAP } from "@/content/map";
import { roughOf } from "@/content/rough";
import { leadFor, NOTICE, PLACE, PROMPT, REJECTED_PART, RESULTS, SEARCH, SUGGEST } from "@/content/search";
import { SHARED } from "@/content/share";
import type { Client } from "@/lib/api/client";
import type { AreaSummary, MetaData, Span, TagId, VibeBands } from "@/lib/api/schema";
import { examplesFor, isPlaced } from "@/lib/holds";
import { isEmpty } from "@/lib/search/edits";
import { isSaidAsMissing, missingFrom, refusals, refusedByPart } from "@/lib/search/refusals";
import { isStale, repairsFor } from "@/lib/search/repairs";
import { inTheBox, written } from "@/lib/search/spans";
import {
  failureOfTheCards,
  isUnreachable,
  leftOutByTheBudget,
  rentsHeldAgainst,
  profilesFailed,
  reasonsAreIn,
  reasonsFailure,
  servedTheRanking,
  type SearchState,
} from "@/lib/search/state";
import { SearchProvider, useSearch } from "@/lib/search/store";
import { SessionBoundary, useMadeLink, useSessionIfAny } from "@/lib/session/session";
import type { Lens } from "@/lib/vibes";

import { AreaTable } from "../AreaTable/AreaTable";
import { ChipRow } from "../ChipRow/ChipRow";
import { ClarifyQuestion } from "../ClarifyQuestion/ClarifyQuestion";
import { CompareTray } from "../CompareTray/CompareTray";
import { ErrorBlock } from "../ErrorBlock/ErrorBlock";
import { MapView } from "../MapView/MapView";
import { NothingMatches } from "../NothingMatches/NothingMatches";
import { NotInData } from "../NotInData/NotInData";
import {
  NoticeBlock,
  OfflineLine,
  RejectedList,
  StateLine,
  UnmetList,
} from "../NoticeBlock/NoticeBlock";
import { PlaceCombobox } from "../PlaceCombobox/PlaceCombobox";
import { Examples, PromptBox, type PromptHandle } from "../PromptBox/PromptBox";
import { ResultList, type Part } from "../ResultList/ResultList";
import { SettingsPanel } from "../SettingsPanel/SettingsPanel";
import { TenureChoice } from "../SettingsPanel/TenureChoice";
import { SharedHeader } from "../SharedSearch/SharedHeader";
import { SharePanel } from "../SharePanel/SharePanel";
import { Shelf } from "../Shelf/Shelf";
import { StatusLine } from "../StatusLine/StatusLine";
import { Suggestions } from "../Suggestions/Suggestions";
import styles from "./SearchApp.module.css";

interface Props {
  /** What a form needs: the vocabulary, both defaults and the limits. From route 11, at build. */
  readonly meta: MetaData;
  /** Every area of the release, from route 4, at build. */
  readonly areas: readonly AreaSummary[];
  /**
   * Where every area sits on every vibe that may colour the map, from route 4, at build.
   * They come with the page, so that nobody is told which vibe a person looks at.
   */
  readonly bands?: readonly VibeBands[];
  /** The API to call. A test passes its own. */
  readonly client?: Client;
}

const PANEL = { list: "results", map: "panel-map" } as const;
/** The chips, which the page gives the focus to when a question is answered and goes. */
const UNDERSTOOD = "understood";

/** What a failure is shown as. One failure is shown in one place. */
function placeOf(state: SearchState): "none" | "offline" | "box" | "form" | "block" {
  const { failure, failedStep } = state;
  if (failure === null) return state.online ? "none" : "offline";
  if (failure.kind === "offline") return "offline";
  if (failure.kind === "api" && failure.code === "invalid_text") return "box";
  // A request the API refused, other than for its words, is a fault to report and is said
  // in the API's own words. Left to the form it would be said nowhere: the form speaks
  // only when the words went unread.
  const refused = failure.kind === "api" && failure.status < 500;
  // Words that could not be read are not a fault to report. The form does the same job.
  // Words that never reached Burro are another thing: the form could not reach it either,
  // so the page says that Burro could not be reached, as it does for a control.
  if (failedStep === "read" && !isStale(failure) && !refused && !isUnreachable(failure)) return "form";
  return "block";
}

/**
 * The search page: one box to type in, what Burro understood, and the answer.
 *
 * Typing and the controls both end in edits the API applies. Nothing a
 * person types is kept here: the sentence goes from its box to one call.
 */
export function SearchApp({ meta, areas, bands = [], client }: Props) {
  return (
    // The search is kept by the session, so that it is still there when the person comes back.
    <SessionBoundary>
      <SearchProvider meta={meta} areas={areas} client={client}>
        <SearchView bands={bands} />
      </SearchProvider>
    </SessionBoundary>
  );
}

interface ViewProps {
  /** True on the page a shared link opens, whose heading says that the search is a shared one. */
  readonly shared?: boolean;
  readonly bands?: readonly VibeBands[];
}

/** Which stretch of several is selected in the box: what it is of, and which one of how many. */
interface Shown {
  /** What the stretches are of: what was not read, or the suggestion at that place in the list. */
  readonly of: "unread" | number;
  readonly at: number;
  readonly among: number;
}

/**
 * The search page itself, for whatever holds the search: the page at `/`, or an opened share.
 *
 * Before a search it is a box, the shelf of vibes, and the map. After one the
 * answer comes first: the box on one line, one line that says what happened,
 * the chips, and then the first result, whole on the first screen of a phone.
 * The title gives way to it. After the first result stand the ways to the
 * settings and to sharing, then the map, and then the rest of the results: on
 * a wide screen the map is beside them all. Everything else is one press
 * away: the working of a result, the settings, sharing, the table.
 *
 * What Burro says of a search stands directly under the box: what happened, a
 * notice, a question, a failure, what was understood, and what was noticed
 * and not applied. It is what a person must see when they press Search.
 */
export function SearchView({ shared = false, bands = [] }: ViewProps) {
  const { state, flow } = useSearch();
  const [madeLink, keepLink] = useMadeLink();
  const prompt = useRef<PromptHandle>(null);
  // What holds the form, the map and both parts of the list of results.
  const columns = useRef<HTMLDivElement>(null);
  const map = useRef<HTMLDivElement>(null);
  const [reveal, setReveal] = useState<{ areaId: string; at: number } | null>(null);
  // Which stretch of the text is selected in the box. Where words stand is known for the
  // text that was sent, and for no other, so this goes when the box changes.
  const [shown, setShown] = useState<Shown | null>(null);
  // The vibe the map is coloured by, before a search. It is the one whose card is open.
  const [looksAt, setLooksAt] = useState<TagId | null>(null);
  // True when what was pressed goes as the search opens: a vibe on the shelf, the place field.
  const handsOver = useRef(false);
  const session = useSessionIfAny();

  // What another page asked the search to add, as "Search for this character" does on the
  // page of an area. It is taken once, and sent as the edits of a control are.
  useEffect(() => {
    const wanted = session?.wanted.take() ?? null;
    if (wanted === null || isEmpty(wanted)) return;
    handsOver.current = true;
    void flow.applyEdits(wanted);
  }, [session, flow]);

  useEffect(() => {
    void flow.loadGeometry();
    // Who reads what is typed is asked of the service as the page opens, so that the
    // line under the box says what is so now, and not what was so when the page was built.
    void flow.loadReader();
    if (typeof navigator !== "undefined" && navigator.onLine === false) flow.wentOffline();
    const online = () => void flow.wentOnline();
    const offline = () => flow.wentOffline();
    window.addEventListener("online", online);
    window.addEventListener("offline", offline);
    return () => {
      window.removeEventListener("online", online);
      window.removeEventListener("offline", offline);
    };
  }, [flow]);

  // "Show in the list": the card is brought into view and takes the focus. It is brought in
  // by its top, so that its heading is in sight.
  useEffect(() => {
    if (reveal === null) return;
    // A pin of the map names its area as a result does. The result is the one that holds a card.
    const card = [...(columns.current?.querySelectorAll<HTMLElement>("li[data-area]") ?? [])]
      .find((item) => item.dataset.area === reveal.areaId)
      ?.querySelector<HTMLElement>("article");
    if (!card) return;
    if (typeof card.scrollIntoView === "function") card.scrollIntoView({ block: "start" });
    card.focus({ preventScroll: true });
  }, [reveal]);

  const { spec, meta, areas, ranking, read, phase } = state;
  const reading = phase === "interpreting";
  const busy = reading || phase === "refining";
  // A search is open once anything has been read, ranked or changed, and while a sentence is read.
  const open = reading || read !== null || ranking !== null || !state.untouched;
  const shows = placeOf(state);

  // The shelf and the place field are for a first search, and go when one opens. The focus
  // goes to what Burro understood, which is where what was pressed has gone. It is never
  // left on nothing.
  useEffect(() => {
    if (!open || !handsOver.current) return;
    handsOver.current = false;
    document.getElementById(UNDERSTOOD)?.focus({ preventScroll: true });
  }, [open]);

  const refusedAt = refusedByPart(state.refused);
  const repairs = repairsFor(state.failure, spec, state.pending);
  const questions = reading ? [] : (read?.clarify ?? []);
  const suggestions = reading ? [] : (read?.suggestions ?? []);
  const unread = reading ? [] : (read?.unread ?? []);
  const isLatest = read !== null && read.at === state.answers;
  // Nothing was applied, nothing is asked and nothing is offered: the words were read into nothing.
  const readNothing =
    read !== null &&
    questions.length === 0 &&
    read.suggestions.length === 0 &&
    (read.status === "off_topic" || read.edits === 0);
  // While a model reads what the rules left unread, it is not yet so that nothing could be
  // read: the page says that Burro is still reading, and says no more until it has.
  const nothingRead =
    !reading &&
    isLatest &&
    read !== null &&
    !read.more &&
    questions.length === 0 &&
    suggestions.length === 0 &&
    !read.changed
      ? readNothing
        ? NOTICE.nothingRead
        : read.rejected.length === 0 && read.edits > 0
          ? NOTICE.nothingChanged
          : null
      : null;
  const noticed = read !== null && read.notice !== "none" && read.notice_text !== "";
  // Where the API has words of its own for it, they are in the notice, and are not said twice.
  const nothingSaid = noticed ? null : nothingRead;
  // Something was read, and a stretch of the text was not: the ranking leaves that stretch out.
  const partUnread = !reading && read !== null && read.partUnread && read.changed;
  const unmet = (read?.unmet ?? []).filter((category) => category !== "other");
  // Reasons are the ranking's only when they are for the same spec and the same release made both.
  const explained = reasonsAreIn(state);
  // The search came, and the reasons or a profile of one of its cards did not.
  const ofTheCards = failureOfTheCards(state);
  const served = servedTheRanking(state);
  const full =
    spec.commutes.length >= meta.limits.max_commutes ? PLACE.full(meta.limits.max_commutes) : null;
  // The map is coloured by a vibe only before a search. A ranking colours it by fit.
  const lens = useMemo((): Lens | null => {
    if (open || looksAt === null) return null;
    // A vibe that no area can be placed on colours nothing: the map was all dots, under a
    // legend that said it was coloured by the vibe.
    if (!isPlaced(meta, looksAt)) return null;
    const tag = meta.tags.find((one) => one.tag_id === looksAt && one.lens);
    const marks = bands.find((one) => one.tag_id === looksAt)?.marks;
    return tag === undefined || marks === undefined ? null : { tag, marks, rough: roughOf(tag, meta) };
  }, [open, looksAt, meta, bands]);

  const nameOfPart = (key: string): string | null => {
    if (key === "tenure" || key === "budget" || key === "journeys") return REJECTED_PART[key];
    const [kind, id] = key.split(":", 2);
    if (kind === "feature") return meta.features.find((one) => one.feature_id === id)?.short_label ?? null;
    if (kind === "tag") return meta.tags.find((one) => one.tag_id === id)?.label ?? null;
    // A place the answers gave no name for is spoken of as "the place", and never by a stand-in.
    if (kind === "place" && id) return state.placeNames[id] ?? null;
    if (kind === "area") return areas.find((one) => one.area_id === id)?.name ?? null;
    return null;
  };
  // What was asked for that the data does not hold is said by name, directly under the
  // box. It is not said a second time among what was not applied.
  const missing = reading ? [] : missingFrom(read, state.refused, nameOfPart);
  const notApplied = reading
    ? []
    : refusals(read, state.refused).filter((refusal) => !isSaidAsMissing(refusal, missing));

  /** Sends what is in the box. From now until the box is changed, it holds what was sent. */
  const send = (text: string) => {
    setShown(null);
    setLooksAt(null);
    void flow.submitText(text);
  };
  const retry = () => {
    setShown(null);
    void flow.retry(prompt.current?.text() ?? "");
  };
  const sendAgain = () => send(prompt.current?.text() ?? "");
  // What rested on the text that was sent goes when the box changes: where the words of a
  // suggestion stand, and which stretch was not read.
  const typed = useCallback(() => {
    setShown(null);
    flow.boxChanged();
  }, [flow]);
  const startAgain = () => {
    setShown(null);
    setLooksAt(null);
    // Nothing of the search before is left: not the areas that were chosen from it to
    // compare, and not the area that was chosen on its map, which goes with the search.
    session?.compare.clear();
    flow.startAgain();
  };
  const edit = (operations: Parameters<typeof flow.applyEdits>[0]) => {
    setLooksAt(null);
    void flow.applyEdits(operations);
  };
  /**
   * Selects, in the box, the next of these stretches of what was typed. The words stay in
   * the box: the page is given where they stand, and never what they are.
   */
  const show = (of: Shown["of"], spans: readonly Span[]) => {
    const box = prompt.current;
    if (!box) return;
    const found = inTheBox(box.text(), spans);
    const next = shown === null || shown.of !== of || shown.among !== found.length ? 0 : shown.at % found.length;
    const stretch = found[next];
    if (stretch === undefined) {
      setShown({ of, at: 0, among: 0 });
      return;
    }
    box.select(stretch);
    setShown({ of, at: next + 1, among: found.length });
  };
  /** A question goes when it is answered, so the focus is put on what the answer changes. */
  const toUnderstood = () => document.getElementById(UNDERSTOOD)?.focus({ preventScroll: true });

  const table = (
    <AreaTable
      areas={areas}
      scores={ranking?.scores ?? []}
      filtered={ranking?.filtered ?? []}
      unranked={ranking?.unranked ?? []}
      emptySpec={ranking?.empty_spec ?? false}
      searched={ranking !== null}
      lens={lens}
      meta={meta}
      selectedId={state.selectedId}
      onSelect={flow.select}
      onHover={flow.hover}
    />
  );

  const settings = (
    <SettingsPanel
      spec={spec}
      meta={meta}
      areas={areas}
      placeNames={state.placeNames}
      version={state.answers}
      refused={refusedAt}
      open={state.settingsOpen}
      busy={busy}
      full={full}
      onToggle={flow.openSettings}
      onEdit={edit}
      onTenure={(tenure) => void flow.setTenure(tenure)}
      searchPlaces={flow.searchPlaces}
      onAddPlace={(place) => void flow.addPlace(place)}
      onRank={ranking === null && !busy ? () => void flow.rankNow() : undefined}
    />
  );

  const says = (
    <div className={styles.says} data-open={open}>
      <StatusLine
        phase={phase}
        ranking={ranking}
        areas={areas}
        moved={state.moved}
        was={state.rankedBefore}
        gaveWay={state.gaveWay}
        budgetWent={state.budgetWent}
        asking={questions.length > 0}
        // The line speaks of the ranking on screen, so it is given the spec that was ranked.
        spec={ranking !== null && state.rankedHash === state.specHash ? spec : undefined}
      />

      {shows === "offline" ? <OfflineLine waiting={!isEmpty(state.pending)} /> : null}
      <NotInData missing={missing} meta={meta} />
      {partUnread ? (
        <div className={styles.part} role="status" aria-label={NOTICE.partLabel}>
          <p>{NOTICE.partUnread}</p>
        </div>
      ) : null}
      {state.degraded && !reading ? (
        <div className={styles.degraded}>
          {/* A reading is held while the next is asked for. Where the page is a form, nothing
              read the words in the box, so nothing is said to have refused them. */}
          <StateLine>
            {read?.model_refused === true && shows !== "form" ? NOTICE.refused : NOTICE.degraded}
          </StateLine>
          {/* Words that were not read can always be tried again, from the box. Words the
              rules read in place of a model were read, and there is nothing to try again. */}
          {read?.degraded !== true || shows === "form" ? (
            <button type="button" className="target" onClick={shows === "form" ? retry : sendAgain}>
              {PROMPT.tryAgain}
            </button>
          ) : null}
        </div>
      ) : null}
      {shows === "block" && state.failure !== null ? (
        <ErrorBlock
          failure={state.failure}
          notUpdated={ranking !== null}
          repairs={repairs}
          nameOf={nameOfPart}
          onRetry={retry}
          onStartAgain={startAgain}
          onEdit={edit}
        />
      ) : null}
      {/* The card says what it lacks. Here is why, in the API's words with the id to
          quote, and "Try again", which ranks again and asks for what is missing. */}
      {shows === "none" && ofTheCards !== null ? (
        <ErrorBlock
          failure={ofTheCards}
          notUpdated={false}
          onRetry={retry}
          onStartAgain={startAgain}
          onEdit={edit}
        />
      ) : null}

      {read !== null && !reading ? <NoticeBlock notice={read.notice} text={read.notice_text} /> : null}
      {nothingSaid !== null ? <StateLine>{nothingSaid}</StateLine> : null}
      {questions.map((question, at) => (
        <ClarifyQuestion
          key={`${question.group}.${question.index}`}
          clarify={question}
          position={{ at: at + 1, of: questions.length }}
          search={flow.searchPlaces}
          onPick={(option) => {
            toUnderstood();
            void flow.answerClarify(question, option);
          }}
          onLeaveOut={() => {
            toUnderstood();
            flow.leaveOut(question);
          }}
        />
      ))}

      {open ? (
        <>
          <ChipRow
            id={UNDERSTOOD}
            spec={spec}
            assumed={state.assumed}
            quoted={state.quoted}
            tenurePicked={state.tenurePicked}
            placeNames={state.placeNames}
            meta={meta}
            areas={areas}
            version={state.answers}
            refused={refusedAt}
            readBy={read?.interpreter ?? null}
            waiting={reading && read === null && ranking === null}
            onEdit={edit}
            onTenure={(tenure) => void flow.setTenure(tenure)}
            onOpenSettings={() => flow.openSettings(true)}
          />
          {read !== null && !reading ? <UnmetList unmet={unmet} /> : null}
          <RejectedList refusals={notApplied} nameOf={nameOfPart} meta={meta} />
        </>
      ) : null}

      <Suggestions
        suggestions={suggestions}
        added={reading ? null : (read?.added ?? null)}
        leftOut={leftOutByTheBudget(state)}
        heldAgainst={rentsHeldAgainst(state)}
        reading={!reading && read !== null && read.more}
        onChoose={(at, id, placeId) => {
          setShown(null);
          // The last suggestion takes the block with it. The focus goes to what Burro
          // understood, which is what a choice changes, and is never left on nothing.
          if (suggestions.length === 1 && read?.added == null && !read?.more) toUnderstood();
          void flow.choose(at, id, placeId);
        }}
        onChooseAll={(ats) => {
          setShown(null);
          void flow.chooseAll(ats);
        }}
        onTakeBack={() => {
          setShown(null);
          void flow.takeBack();
        }}
        // The words are cut from the box as it stands. What is offered goes when the box
        // changes, so while an offer is drawn the box holds what was sent.
        wrote={(span) => written(prompt.current?.text() ?? "", span)}
        searchPlaces={flow.searchPlaces}
        onShow={(spans) => {
          const at = suggestions.findIndex((one) => one.spans === spans);
          show(at < 0 ? 0 : at, spans);
        }}
      />
      {unread.length > 0 ? (
        <div className={styles.unread}>
          {partUnread ? null : <p>{SUGGEST.unread}</p>}
          <button type="button" className="target-min" onClick={() => show("unread", unread)}>
            {shown?.of === "unread" && shown.among > 1 ? SUGGEST.showNextUnread : SUGGEST.showUnread}
          </button>
        </div>
      ) : null}
      {suggestions.length > 0 || unread.length > 0 ? (
        // It is on the page before it says anything, so that a screen reader is told when it does.
        <p className={styles.shown} role="status">
          {shown === null
            ? ""
            : shown.among === 0
              ? NOTICE.partNotFound
              : shown.of === "unread"
                ? NOTICE.partShown(shown.at, shown.among)
                : SUGGEST.wordsShown}
        </p>
      ) : null}
    </div>
  );

  const nothingMatches = ranking !== null && ranking.ranked.length === 0;
  /** One list of results, drawn in two parts: the first result before the map, and the rest after it. */
  const list = (part: Part) => (
    <ResultList
      part={part}
      ranked={ranking?.ranked ?? null}
      areas={areas}
      explanations={explained ? state.explanations : []}
      explained={explained}
      explainFailed={reasonsFailure(state) !== null}
      facts={state.facts}
      details={state.details}
      detailsFailed={profilesFailed(state)}
      geometry={state.geometry}
      spec={spec}
      meta={meta}
      served={served}
      placeNames={state.placeNames}
      noFit={ranking?.empty_spec ?? false}
      unranked={ranking?.unranked ?? []}
      areasRanked={ranking?.areas_ranked ?? 0}
      areasListed={ranking?.areas_listed ?? 0}
      busy={busy}
      selectedId={state.selectedId}
      onSelect={(areaId) => {
        flow.select(areaId);
        // On a narrow screen the map may be some way from a result. It is brought into
        // view, and the focus stays on the button that was pressed.
        if (typeof map.current?.scrollIntoView === "function") {
          map.current.scrollIntoView({ block: "nearest" });
        }
      }}
      onHover={flow.hover}
      onEdit={edit}
    />
  );

  return (
    // It says whether a search is open, so that the banner over the page can give way to the answer.
    <div className={styles.search} data-open={open} data-search={open ? "open" : "closed"}>
      {/* Before a search there are no results to skip to, and no link that leads nowhere. */}
      {open || busy ? (
        <a className={`${styles.skip} target`} href={`#${PANEL.list}`}>
          {SEARCH.skipToResults}
        </a>
      ) : null}
      <a className={`${styles.skip} target`} href={`#${PANEL.map}`}>
        {SEARCH.skipToMap}
      </a>
      {/* Once a search is open the title gives way to the answer. It is still the heading of
          the page to whoever hears it. A shared search keeps its title: it says what the page is. */}
      <h1 className={open && !shared ? "visually-hidden" : styles.title}>{shared ? SHARED.title : SEARCH.title}</h1>
      {/* What the page is for is said to whoever has not searched yet. After that the answer comes first. */}
      {open ? null : <p className={styles.lead}>{leadFor(meta.holds)}</p>}
      {state.shared !== null ? (
        <SharedHeader
          shared={state.shared}
          release={served.release_id}
          hasPlaces={spec.commutes.length > 0}
          titled={!shared}
        />
      ) : null}

      <div ref={columns} className={styles.columns}>
        <section className={styles.form} aria-label={SEARCH.formLabel}>
          <PromptBox
            ref={prompt}
            maxText={meta.limits.max_text}
            busy={reading}
            open={open}
            onSubmit={send}
            onStop={flow.stop}
            onStartAgain={startAgain}
            onTyped={typed}
            refusal={shows === "box" && state.failure?.kind === "api" ? state.failure.message : null}
            reader={state.reader}
            readerFailed={state.readerFailed}
            hint={PROMPT.hintFor(meta.holds)}
          >
            {says}
          </PromptBox>
          {open ? null : (
            <>
              <Shelf
                tags={meta.tags}
                features={meta.features}
                recipes={meta.recipes}
                guides={meta.rough_guides}
                geometry={state.geometry}
                bands={bands}
                open={looksAt}
                onOpen={setLooksAt}
                onAdd={(operations) => {
                  handsOver.current = true;
                  edit(operations);
                }}
              />
              <div className={styles.beside}>
                <TenureChoice
                  tenure={spec.tenure}
                  onChoose={(tenure) => void flow.setTenure(tenure)}
                  version={state.answers}
                />
                {/* The one box that finds by name: a place to reach, which is added to the
                    search, and an area, which is a link to its page. */}
                <PlaceCombobox
                  search={flow.searchPlaces}
                  onPick={(place) => {
                    handsOver.current = true;
                    void flow.addPlace(place);
                  }}
                  full={full}
                  noPlaces={!meta.holds.journeys}
                  areas
                />
              </div>
              <Examples examples={examplesFor(meta)} onUse={(example) => prompt.current?.fill(example)} />
            </>
          )}
        </section>

        {/* The answer comes first: the first result stands directly after what Burro says of
            the search, and before the map. */}
        {open || busy ? (
          <section
            id={PANEL.list}
            className={styles.results}
            tabIndex={-1}
            aria-labelledby="results-title"
          >
            {/* A numbered list of areas under the line that says how many were ranked says
                what it is. The heading is kept for whoever hears the page. */}
            <h2 id="results-title" className="visually-hidden">
              {RESULTS.title}
            </h2>
            {ranking !== null && nothingMatches ? (
              <NothingMatches
                filtered={ranking.filtered}
                unranked={ranking.unranked}
                spec={spec}
                areas={areas}
                placeNames={state.placeNames}
                meta={meta}
                onEdit={edit}
              />
            ) : (
              list("first")
            )}
          </section>
        ) : null}

        {/* One press away, side by side: the settings, and sharing once there is a ranking.
            They stand after the first result, so that nothing stands between what Burro
            understood and the answer, and they stand where they did before a search: under
            the form. */}
        <div className={styles.tools}>
          {settings}
          {ranking !== null ? (
            <SharePanel
              spec={spec}
              specHash={state.specHash}
              meta={meta}
              areas={areas}
              create={flow.createShare}
              held={madeLink}
              onMade={keepLink}
            />
          ) : null}
        </div>

        <div
          ref={map}
          id={PANEL.map}
          className={styles.map}
          role="region"
          aria-label={MAP.label}
          // The link that skips to the map puts the focus here. It is no stop of its own.
          tabIndex={-1}
        >
          <a className={`${styles.skip} target`} href="#after-map">
            {SEARCH.skipMap}
          </a>
          <MapView
            geometry={state.geometry}
            geometryFailed={state.geometryFailed}
            areas={areas}
            scores={ranking?.scores ?? []}
            ranked={ranking?.ranked ?? []}
            filtered={ranking?.filtered ?? []}
            unranked={ranking?.unranked ?? []}
            emptySpec={ranking?.empty_spec ?? false}
            selectedId={state.selectedId}
            hoveredId={state.hoveredId}
            onSelect={flow.select}
            onHover={flow.hover}
            onShowInList={(areaId) => setReveal((last) => ({ areaId, at: (last?.at ?? 0) + 1 }))}
            lens={lens}
            table={table}
          />
          <span id="after-map" tabIndex={-1} />
        </div>

        {/* The rest of the results, from the second. They come after the map, and on a wide
            screen stand under the first result, beside it. */}
        {(open || busy) && !nothingMatches ? <div className={styles.rest}>{list("rest")}</div> : null}
      </div>
      <CompareTray />
    </div>
  );
}
