"use client";

import { useEffect, useRef, useState } from "react";

import { MAP } from "@/content/map";
import { NOTICE, PLACE, PROMPT, RESULTS, SEARCH, VIEWS } from "@/content/search";
import { SHARED } from "@/content/share";
import type { Client } from "@/lib/api/client";
import type { AreaSummary, MetaData } from "@/lib/api/schema";
import { namesOfPlaces } from "@/lib/search/chips";
import { isEmpty } from "@/lib/search/edits";
import { refusals, refusedByPart } from "@/lib/search/refusals";
import { isStale, repairsFor } from "@/lib/search/repairs";
import {
  failureOfTheCards,
  isUnreachable,
  profilesFailed,
  reasonsAreIn,
  reasonsFailure,
  servedTheRanking,
  type SearchState,
} from "@/lib/search/state";
import { SearchProvider, useSearch } from "@/lib/search/store";
import { unreadStretches } from "@/lib/search/unread";
import { SessionBoundary, useMadeLink } from "@/lib/session/session";

import { AreaTable } from "../AreaTable/AreaTable";
import { ChipRow } from "../ChipRow/ChipRow";
import { ClarifyQuestion } from "../ClarifyQuestion/ClarifyQuestion";
import { CompareTray } from "../CompareTray/CompareTray";
import { ErrorBlock } from "../ErrorBlock/ErrorBlock";
import { MapView } from "../MapView/MapView";
import { NothingMatches } from "../NothingMatches/NothingMatches";
import {
  NoticeBlock,
  OfflineLine,
  RejectedList,
  StateLine,
  UnmetList,
} from "../NoticeBlock/NoticeBlock";
import { PlaceCombobox } from "../PlaceCombobox/PlaceCombobox";
import { PromptBox, type PromptHandle } from "../PromptBox/PromptBox";
import { ResultList } from "../ResultList/ResultList";
import { SettingsPanel } from "../SettingsPanel/SettingsPanel";
import { TenureChoice } from "../SettingsPanel/TenureChoice";
import { SharedHeader } from "../SharedSearch/SharedHeader";
import { SharePanel } from "../SharePanel/SharePanel";
import { StatusLine } from "../StatusLine/StatusLine";
import { Tabs } from "../Tabs/Tabs";
import styles from "./SearchApp.module.css";

interface Props {
  /** What a form needs: the vocabulary, both defaults and the limits. From route 11, at build. */
  readonly meta: MetaData;
  /** Every area of the release, from route 4, at build. */
  readonly areas: readonly AreaSummary[];
  /** The API to call. A test passes its own. */
  readonly client?: Client;
}

type View = "list" | "map" | "table";

const PANEL = { list: "results", map: "panel-map", table: "panel-table" } as const;
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
 * The search page: one box to type in, what Burro understood, the settings,
 * and the results as a ranked list beside a map.
 *
 * Typing and the controls both end in edits the API applies. Nothing a
 * person types is kept here: the sentence goes from its box to one call.
 */
export function SearchApp({ meta, areas, client }: Props) {
  return (
    // The search is kept by the session, so that it is still there when the person comes back.
    <SessionBoundary>
      <SearchProvider meta={meta} areas={areas} client={client}>
        <SearchView />
      </SearchProvider>
    </SessionBoundary>
  );
}

interface ViewProps {
  /** True on the page a shared link opens, whose heading says that the search is a shared one. */
  readonly shared?: boolean;
}

/**
 * The search page itself, for whatever holds the search: the page at `/`, or an opened share.
 *
 * What Burro says of a search stands directly under the box: what happened, what was not
 * read, a question, a failure, and what was understood. It is what a person must see when
 * they press Search, so nothing but the box's own line stands between the two. Before a
 * search there is nothing to say, and the examples, the tenure and the place field come
 * first, as on a first visit.
 */
export function SearchView({ shared = false }: ViewProps) {
  const { state, flow } = useSearch();
  const [madeLink, keepLink] = useMadeLink();
  const prompt = useRef<PromptHandle>(null);
  const results = useRef<HTMLElement>(null);
  const [view, setView] = useState<View>("list");
  const [reveal, setReveal] = useState<{ areaId: string; at: number } | null>(null);
  // True while the box holds what was last sent. Where the words of a sentence stand is
  // known for the text that was sent, and for no other.
  const [asSent, setAsSent] = useState(false);
  // Which part that was not read is selected in the box, and of how many. `of` is 0 when none was found.
  const [part, setPart] = useState<{ readonly at: number; readonly of: number } | null>(null);

  useEffect(() => {
    void flow.loadGeometry();
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

  // "Show in the list": the card is brought into view and takes the focus, because
  // on a narrow screen the button that was pressed has just gone with the map. It is
  // brought in by its top: a card is taller than a phone's screen, and brought to the
  // nearest edge it opened at its middle, with no heading in sight.
  useEffect(() => {
    if (reveal === null) return;
    const card = [...(results.current?.querySelectorAll<HTMLElement>("[data-area]") ?? [])]
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
  const names = namesOfPlaces(spec, state.placeNames);
  const shows = placeOf(state);
  const refusedAt = refusedByPart(state.refused);
  const notApplied = reading ? [] : refusals(read, state.refused);
  const repairs = repairsFor(state.failure, spec, state.pending);
  const questions = reading ? [] : (read?.clarify ?? []);
  const isLatest = read !== null && read.at === state.answers;
  const nothingRead =
    !reading && isLatest && read !== null && questions.length === 0 && !read.changed
      ? read.status === "off_topic" || read.edits === 0
        ? NOTICE.nothingRead
        : read.rejected.length === 0
          ? NOTICE.nothingChanged
          : null
      : null;
  const noticed = read !== null && read.notice !== "none" && read.notice_text !== "";
  // Where the API has words of its own for it, they are in the notice, and are not said
  // twice. The neutral notice is not that: it says what Burro ranks by, and ends by saying
  // that the rest was applied. Where nothing was, the page says so under it.
  const nothingSaid =
    nothingRead === null
      ? null
      : !noticed
        ? nothingRead
        : read?.notice !== "neutral_places"
          ? null
          : nothingRead === NOTICE.nothingRead
            ? NOTICE.nothingElse
            : nothingRead;
  // When nothing at all was read, the line that says so is enough: "part of what you
  // typed could not be read" would say the same thing a second time. It is judged by the
  // reading and not by the line, so that it does not come up when the line goes.
  const readNothing =
    read !== null && questions.length === 0 && (read.status === "off_topic" || read.edits === 0);
  // That a part was not read is said beside the box, where it is seen, and not in the list
  // under the chips.
  const partUnread = !reading && read !== null && read.unmet.includes("other") && !readNothing;
  const unmet = (read?.unmet ?? []).filter((category) => category !== "other");
  // Reasons are the ranking's only when they are for the same spec and the same release made both.
  const explained = reasonsAreIn(state);
  // The search came, and the reasons or a profile of one of its cards did not.
  const ofTheCards = failureOfTheCards(state);
  const served = servedTheRanking(state);
  const full =
    spec.commutes.length >= meta.limits.max_commutes ? PLACE.full(meta.limits.max_commutes) : null;

  const nameOfPart = (key: string): string | null => {
    const [kind, id] = key.split(":", 2);
    if (kind === "feature") return meta.features.find((one) => one.feature_id === id)?.label ?? null;
    if (kind === "tag") return meta.tags.find((one) => one.tag_id === id)?.label ?? null;
    if (kind === "place" && id) return names.get(id) ?? state.placeNames[id] ?? null;
    if (kind === "area") return areas.find((one) => one.area_id === id)?.name ?? null;
    return null;
  };

  /** Sends what is in the box. From now until the box is changed, it holds what was sent. */
  const send = (text: string) => {
    setAsSent(true);
    setPart(null);
    void flow.submitText(text);
  };
  const retry = () => {
    const text = prompt.current?.text() ?? "";
    // The box is sent again only where it was the words that failed. Where it was the
    // ranking, the box may hold anything by now, and is not what the reading is of.
    if (state.failedStep === "read" && text.trim() !== "") {
      setAsSent(true);
      setPart(null);
    }
    void flow.retry(text);
  };
  const sendAgain = () => send(prompt.current?.text() ?? "");
  const typed = () => {
    if (asSent) setAsSent(false);
    if (part !== null) setPart(null);
  };
  const startAgain = () => {
    setAsSent(false);
    setPart(null);
    flow.startAgain();
  };
  /**
   * Selects, in the box, the next part of what was typed that no edit rests on. The words
   * stay in the box: the page is given where they stand, and never what they are.
   */
  const showPart = () => {
    const box = prompt.current;
    if (!box || read === null) return;
    const parts = unreadStretches(box.text(), read.rests_on);
    const next = part === null || part.of !== parts.length ? 0 : part.at % parts.length;
    const found = parts[next];
    if (found === undefined) {
      setPart({ at: 0, of: 0 });
      return;
    }
    box.select(found);
    setPart({ at: next + 1, of: parts.length });
  };
  /** A question goes when it is answered, so the focus is put on what the answer changes. */
  const toUnderstood = () => document.getElementById(UNDERSTOOD)?.focus({ preventScroll: true });
  const toResults = () => setView("list");

  const table = (
    <AreaTable
      areas={areas}
      scores={ranking?.scores ?? []}
      ranked={ranking?.ranked ?? []}
      filtered={ranking?.filtered ?? []}
      unranked={ranking?.unranked ?? []}
      emptySpec={ranking?.empty_spec ?? false}
      searched={ranking !== null}
      selectedId={state.selectedId}
      onSelect={flow.select}
      onHover={flow.hover}
    />
  );

  const understood = (
    <>
      <ChipRow
        id={UNDERSTOOD}
        spec={spec}
        assumed={state.assumed}
        tenureSaid={state.tenureSaid}
        placeNames={state.placeNames}
        meta={meta}
        areas={areas}
        version={state.answers}
        refused={refusedAt}
        readBy={read?.interpreter ?? null}
        waiting={reading && read === null && ranking === null}
        onEdit={(operations) => void flow.applyEdits(operations)}
        onTenure={(tenure) => void flow.setTenure(tenure)}
        onOpenSettings={() => flow.openSettings(true)}
      />
      {read !== null && !reading ? <UnmetList unmet={unmet} /> : null}
      <RejectedList refusals={notApplied} nameOf={nameOfPart} />
    </>
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
      />

      {shows === "offline" ? <OfflineLine waiting={!isEmpty(state.pending)} /> : null}
      {partUnread ? (
        <div className={styles.part}>
          <div className={styles.partSaid} role="status" aria-label={NOTICE.partLabel}>
            <p>{NOTICE.partUnread}</p>
          </div>
          {asSent && read.rests_on.length > 0 && part?.of !== 0 ? (
            <button type="button" className="target" onClick={showPart}>
              {part === null || part.of < 2 ? NOTICE.showPart : NOTICE.showNextPart}
            </button>
          ) : null}
          <p className={styles.partShown} role="status">
            {part === null ? "" : part.of === 0 ? NOTICE.partNotFound : NOTICE.partShown(part.at, part.of)}
          </p>
        </div>
      ) : null}
      {state.degraded && !reading ? (
        <div className={styles.degraded}>
          <StateLine>{NOTICE.degraded}</StateLine>
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
          onEdit={(operations) => void flow.applyEdits(operations)}
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
          onEdit={(operations) => void flow.applyEdits(operations)}
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

      {open ? understood : null}
      {open && ranking !== null ? (
        <p className={styles.goTo}>
          <a className="target-min" href={`#${PANEL.list}`} onClick={toResults}>
            {RESULTS.goTo}
          </a>
        </p>
      ) : null}
    </div>
  );

  return (
    <div className={styles.search}>
      {/* On a narrow screen the results and the map may each be behind a tab, so the link brings them forward. */}
      <a className={`${styles.skip} target`} href={`#${PANEL.list}`} onClick={toResults}>
        {SEARCH.skipToResults}
      </a>
      {/* The list comes before the map in the page, and is a hundred stops long. */}
      <a className={`${styles.skip} target`} href={`#${PANEL.map}`} onClick={() => setView("map")}>
        {SEARCH.skipToMap}
      </a>
      <h1>{shared ? SHARED.title : SEARCH.title}</h1>
      <p className={styles.lead}>{SEARCH.lead}</p>
      {state.shared !== null ? (
        <SharedHeader
          shared={state.shared}
          release={served.release_id}
          hasPlaces={spec.commutes.length > 0}
          titled={!shared}
        />
      ) : null}

      <div className={styles.columns}>
        <div className={styles.left}>
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
            >
              {says}
            </PromptBox>
            <div className={styles.beside}>
              <TenureChoice
                tenure={spec.tenure}
                onChoose={(tenure) => void flow.setTenure(tenure)}
                version={state.answers}
              />
              <PlaceCombobox
                search={flow.searchPlaces}
                onPick={(place) => void flow.addPlace(place)}
                full={full}
              />
            </div>
          </section>

          {/* Before a search the chips say what a search starts from, and come after the form. */}
          {open ? null : understood}

          <SettingsPanel
            spec={spec}
            meta={meta}
            areas={areas}
            placeNames={state.placeNames}
            version={state.answers}
            refused={refusedAt}
            open={state.settingsOpen}
            busy={busy}
            onToggle={flow.openSettings}
            onEdit={(operations) => void flow.applyEdits(operations)}
            onRank={ranking === null && !busy ? () => void flow.rankNow() : undefined}
          />

          {/* Shown on a narrow screen only. It is wrapped so that hiding it does not depend on the order of two style sheets. */}
          <div className={styles.narrowTabs}>
            <Tabs<View>
              label={VIEWS.label}
              selected={view}
              onSelect={setView}
              tabs={[
                { id: "list", label: VIEWS.list, panel: PANEL.list },
                { id: "map", label: VIEWS.map, panel: PANEL.map },
                { id: "table", label: VIEWS.table, panel: PANEL.table },
              ]}
            />
          </div>

          <CompareTray />

          <section
            ref={results}
            id={PANEL.list}
            className={styles.panel}
            data-narrow={view === "list"}
            data-wide
            tabIndex={-1}
            aria-labelledby="results-title"
          >
            <h2 id="results-title" className={styles.resultsTitle}>
              {RESULTS.title}
            </h2>
            {ranking !== null ? (
              <SharePanel
                spec={spec}
                specHash={state.specHash}
                meta={meta}
                areas={areas}
                placeNames={state.placeNames}
                create={flow.createShare}
                held={madeLink}
                onMade={keepLink}
              />
            ) : null}
            {ranking !== null && ranking.ranked.length === 0 ? (
              <NothingMatches
                filtered={ranking.filtered}
                unranked={ranking.unranked}
                spec={spec}
                areas={areas}
                placeNames={state.placeNames}
                onEdit={(operations) => void flow.applyEdits(operations)}
              />
            ) : (
              <>
                {ranking !== null && ranking.ranked.length > 5 ? (
                  <p className={styles.note}>{RESULTS.firstFive}</p>
                ) : null}
                <ResultList
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
                  busy={busy}
                  selectedId={state.selectedId}
                  onSelect={flow.select}
                  onHover={flow.hover}
                  onEdit={(operations) => void flow.applyEdits(operations)}
                />
              </>
            )}
          </section>
        </div>

        <div className={styles.right}>
          <div className={styles.wideTabs}>
            <Tabs<Exclude<View, "list">>
              label={VIEWS.sideLabel}
              selected={view === "table" ? "table" : "map"}
              onSelect={setView}
              tabs={[
                { id: "map", label: VIEWS.map, panel: PANEL.map },
                { id: "table", label: VIEWS.table, panel: PANEL.table },
              ]}
            />
          </div>
          <div
            id={PANEL.map}
            className={styles.panel}
            role="tabpanel"
            aria-label={MAP.label}
            data-narrow={view === "map"}
            data-wide={view !== "table"}
            // The link that skips to the map puts the focus here. It is no stop of its own.
            tabIndex={-1}
          >
            <a className={`${styles.skip} target`} href="#after-map">
              {VIEWS.skipMap}
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
              onShowInList={(areaId) => {
                setView("list");
                setReveal((last) => ({ areaId, at: (last?.at ?? 0) + 1 }));
              }}
              fallback={table}
            />
            <span id="after-map" tabIndex={-1} />
          </div>
          <div
            id={PANEL.table}
            className={styles.panel}
            role="tabpanel"
            aria-label={VIEWS.table}
            data-narrow={view === "table"}
            data-wide={view === "table"}
          >
            {table}
          </div>
        </div>
      </div>
    </div>
  );
}
