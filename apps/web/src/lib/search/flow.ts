/**
 * What the search page does: each thing a person can do, as the calls it
 * makes and the events it sends to the store. docs/design/web.md, section 5.3.
 *
 * Three rules are kept here.
 *
 * 1. The sentence a person typed is passed to one call and is never kept. It
 *    is not in the store and not in this file's memory once the call is made.
 * 2. The website never edits a spec. An edit is sent with the last spec the
 *    API returned, and the spec that comes back replaces it. Edits made
 *    while a call is out are sent again together, so none is lost.
 * 3. The latest request wins. Each run of calls has a number, and an answer
 *    to an older run is dropped.
 *
 * And a fourth, which the first three do not give: what is on screen is of
 * one release. Every answer names the release that made it, and that is kept
 * with what the answer brought. Reasons are a ranking's only when the same
 * release made both.
 *
 * And a fifth: no sentence is sent before the service has said who reads it.
 * The page is built ahead of time, and the service may since have been set
 * to another reader, so what the page was built on is never taken for it.
 */

import type { Answer, Client, Failure } from "@/lib/api/client";
import { failed } from "@/lib/api/failure";
import type {
  Clarify,
  ClarifyOption,
  FoundPlace,
  Meta,
  Operations,
  PlacesData,
  PreferenceSpec,
  RankedArea,
  ShareCreated,
  Tenure,
} from "@/lib/api/schema";

import { answered, edits, isEmpty, merged, NO_EDITS } from "./edits";
import { addedWithOthers, namesItsPlaces, withPlace } from "./suggestion";
import {
  EXPLAINED,
  failureOfTheCards,
  reasonsAreIn,
  reasonsFailure,
  type SearchEvent,
  type SearchState,
} from "./state";

/** How many results the list holds, and how many of them the API gives reasons for. */
export const LIST_LENGTH = 20;
export { EXPLAINED };
/** The fewest and the most characters a place search may hold. */
export const PLACE_QUERY = { least: 2, most: 80, limit: 8 } as const;

export interface FlowDeps {
  readonly client: Client;
  readonly getState: () => SearchState;
  readonly dispatch: (event: SearchEvent) => void;
}

export interface Flow {
  /** Sends a sentence to be read. The text goes to the call and nowhere else. */
  submitText(text: string): Promise<void>;
  /** Sends the edits of one control. */
  applyEdits(operations: Operations): Promise<void>;
  /** Answers "Which place did you mean?" with the place that was picked. */
  answerClarify(question: Clarify, option: Pick<ClarifyOption, "id">): Promise<void>;
  /** "Leave it out": the question goes, and nothing is sent. */
  leaveOut(question: Clarify): void;
  /**
   * Takes one of the choices of an offer, by its id. The offer goes, whatever was chosen.
   * A choice that holds edits sends them, as a control does. "Skip" holds none, and sends
   * nothing. A journey to a place the release does not hold is sent with the place the
   * person chose for it, and is not sent without one.
   */
  choose(at: number, id: string, placeId?: string): Promise<void>;
  /**
   * Takes, of each of these offers, the way the API says one press may add, in one
   * request. What is the person's to choose is left as it is.
   */
  chooseAll(ats: readonly number[]): Promise<void>;
  /** Takes back all that the last "add all" added: the search and the offers are as they were. */
  takeBack(): Promise<void>;
  /** Told that the box changed, and never what to. What rested on the text that was sent goes. */
  boxChanged(): void;
  /** Adds a place picked from the place search as a journey. */
  addPlace(place: Pick<FoundPlace, "place_id">): Promise<void>;
  setTenure(tenure: Tenure): Promise<void>;
  /** Ranks the settings as they stand, with no edit. */
  rankNow(): Promise<void>;
  /**
   * Tries again what failed. A sentence is passed in, because none is kept. Where it is
   * the reasons or a profile that failed, the search is ranked again and they are asked
   * for with it, so that the ranking and what its cards hold come from one release.
   */
  retry(text?: string): Promise<void>;
  /**
   * Stops what is being worked out. While a sentence is read or ranked, the search goes
   * back to what it was when the sentence was sent.
   */
  stop(): void;
  startAgain(): void;
  /**
   * Opens a shared search: the spec the link holds, ranked now. It answers
   * with the failure where there is one, for the page that opened the link to
   * say, and with `null` when the search is open.
   */
  openShare(shareId: string): Promise<Failure | null>;
  /** Route 9. Stores the search as it stands and answers with the id of the share. */
  createShare(exactPlaces: boolean, signal?: AbortSignal): Promise<Answer<ShareCreated>>;
  select(areaId: string | null): void;
  hover(areaId: string | null): void;
  openSettings(open: boolean): void;
  loadGeometry(): Promise<void>;
  /** Asks the service who reads what is typed, if it has not yet said. Route 11. */
  loadReader(): Promise<void>;
  wentOffline(): void;
  wentOnline(): Promise<void>;
  /** Route 8, for the place search. What is typed goes in the body of the call. */
  searchPlaces(text: string, signal?: AbortSignal): Promise<Answer<PlacesData>>;
}

export function createFlow({ client, getState, dispatch }: FlowDeps): Flow {
  let current = 0;
  let readingRun: number | null = null;
  /** The model's reading of what the rules left unread, while it is under way. */
  let reading: AbortController | null = null;
  let inFlight: AbortController | null = null;
  /** The release the form is being read again for, while it is, so that it is not asked for twice at once. */
  let catchingUp: { readonly release: string; readonly done: Promise<void> } | null = null;
  /** The release whose boundaries could not be read when its form could. */
  let boundariesOwed: string | null = null;

  function begin() {
    inFlight?.abort();
    inFlight = new AbortController();
    current += 1;
    return { mine: current, signal: inFlight.signal };
  }

  const isStale = (mine: number) => mine !== current;

  function fail(step: "read" | "rank", failure: Failure) {
    // A call that was stopped has nothing to report.
    if (failure.kind === "aborted") dispatch({ type: "stopped" });
    else dispatch({ type: "failed", step, failure });
  }

  /** Every answer says which release made it. If that has changed, the form is read again. */
  function heard(meta: Meta) {
    void caughtUpWith(meta);
  }

  /** The same, for whoever must wait until the form has been read again before going on. */
  function caughtUpWith(meta: Meta): Promise<void> {
    const { release_id: release } = meta;
    const upToDate = release === getState().meta.release_id && boundariesOwed !== release;
    if (upToDate) return Promise.resolve();
    if (catchingUp?.release === release) return catchingUp.done;
    // A read that fails is not remembered. The next answer that names the release asks again.
    const done: Promise<void> = refresh().finally(() => {
      if (catchingUp?.done === done) catchingUp = null;
    });
    catchingUp = { release, done };
    return done;
  }

  async function refresh() {
    const [meta, areas, geometry] = await Promise.all([
      client.getMeta(),
      client.listAreas(),
      client.getGeometry(),
    ]);
    if (!meta.ok || !areas.ok) return;
    dispatch({ type: "release_changed", meta: meta.data, areas: areas.data.areas });
    boundariesOwed = geometry.ok ? null : meta.data.release_id;
    if (geometry.ok) dispatch({ type: "geometry_loaded", geometry: geometry.data });
  }

  async function explain(mine: number, signal: AbortSignal, spec: PreferenceSpec, hash: string) {
    const answer = await client.explainTop({ spec, limit: EXPLAINED }, signal);
    if (isStale(mine)) return;
    if (answer.ok) dispatch({ type: "explain_answered", data: answer.data, meta: answer.meta });
    else if (answer.failure.kind !== "aborted") {
      dispatch({ type: "explain_failed", hash, failure: answer.failure });
    }
  }

  /** Route 6 for each area not yet in hand. An area is asked for by its slug. */
  async function details(signal: AbortSignal, areaIds: readonly string[]) {
    const { areas, details: held } = getState();
    const wanted = areaIds
      .filter((areaId) => !(areaId in held))
      .flatMap((areaId) => areas.filter((area) => area.area_id === areaId));
    await Promise.all(
      wanted.map(async (area) => {
        const answer = await client.getArea(area.slug, signal);
        // A profile is of the release and not of the search, so a late one is still right.
        if (answer.ok) dispatch({ type: "detail_answered", data: answer.data, meta: answer.meta });
        else if (answer.failure.kind !== "aborted") {
          dispatch({ type: "detail_failed", areaId: area.area_id, failure: answer.failure });
        }
      }),
    );
  }

  /**
   * What the cards of a ranking hold: the profiles of its first areas, and its reasons.
   * `explaining` is the call for the reasons where it was made beside the ranking.
   */
  async function fill(
    mine: number,
    signal: AbortSignal,
    ranked: { readonly spec: PreferenceSpec; readonly spec_hash: string; readonly ranked: readonly RankedArea[] },
    explaining: Promise<void> | null,
  ) {
    const first = ranked.ranked.slice(0, EXPLAINED).map((area) => area.area_id);
    const jobs: Promise<void>[] = [details(signal, first)];
    if (explaining !== null) jobs.push(explaining);
    else if (first.length > 0 && !reasonsAreIn(getState())) {
      jobs.push(explain(mine, signal, ranked.spec, ranked.spec_hash));
    }
    await Promise.all(jobs);
    // The reasons must be for the ranking on screen: for the same spec, and made by the
    // same release. If they are not, as when the release moved between the two calls,
    // they are asked for once more.
    const settled = () =>
      isStale(mine) || reasonsAreIn(getState()) || reasonsFailure(getState()) !== null;
    if (first.length === 0 || settled()) return;
    await explain(mine, signal, ranked.spec, ranked.spec_hash);
    if (settled()) return;
    // Reasons that are still another release's are never shown as this ranking's. They are
    // said not to have come, so that no card is left waiting, and "Try again" ranks again.
    dispatch({ type: "explain_failed", hash: ranked.spec_hash, failure: failed("unreadable").failure });
  }

  async function settle(
    mine: number,
    signal: AbortSignal,
    spec: PreferenceSpec,
    hash: string | null,
    operations: Operations,
  ) {
    // With no edit to apply the spec is final, so its reasons are asked for at once.
    const explaining =
      isEmpty(operations) && hash !== null ? explain(mine, signal, spec, hash) : null;
    dispatch({ type: "rank_started", seq: mine });
    const answer = await client.rank(
      { spec, limit: LIST_LENGTH, ...(isEmpty(operations) ? {} : { operations }) },
      signal,
    );
    if (isStale(mine)) return;
    if (!answer.ok) {
      fail("rank", answer.failure);
      await explaining;
      return;
    }
    heard(answer.meta);
    dispatch({ type: "rank_answered", data: answer.data, sent: operations, meta: answer.meta });
    await fill(mine, signal, answer.data, explaining);
  }

  async function rerank() {
    const { mine, signal } = begin();
    readingRun = null;
    const { spec, specHash, pending } = getState();
    await settle(mine, signal, spec, specHash, pending);
  }

  /** Sends the edits that are waiting, if any are. */
  async function sendWhatWaits() {
    if (!isEmpty(getState().pending)) await rerank();
  }

  async function applyEdits(operations: Operations) {
    if (isEmpty(operations)) return;
    dispatch({ type: "queued", operations });
    // A sentence is being read: its answer brings the spec these edits are for.
    if (readingRun !== null && readingRun === current) return;
    await rerank();
  }

  /**
   * Who reads what is typed, asked of the service if it has not yet said. It answers with
   * the failure where the service could not say, and with `null` once it has.
   */
  async function whoReads(signal?: AbortSignal): Promise<Failure | null> {
    if (getState().reader !== null) return null;
    const answer = await client.getMeta(signal);
    if (answer.ok) {
      dispatch({ type: "reader_said", reader: answer.data.reader });
      return null;
    }
    if (answer.failure.kind !== "aborted") dispatch({ type: "reader_unsaid" });
    return answer.failure;
  }

  async function submitText(text: string) {
    const said = text.trim();
    if (said === "") return;
    stopReading();
    const { mine, signal } = begin();
    readingRun = mine;
    dispatch({ type: "read_started", seq: mine });
    // The sentence waits until the service has said who reads it. If it cannot say, the
    // sentence is not sent, and the page says that Burro could not be reached.
    if (getState().reader === null) {
      const unsaid = await whoReads(signal);
      if (isStale(mine)) return;
      if (unsaid !== null) {
        readingRun = null;
        fail("read", unsaid);
        return;
      }
    }
    // The rules are asked first, and answer at once. What they offer never waits on a model.
    const sent = getState().spec;
    const answer = await client.interpret({ text: said, spec: sent, ask_model: false }, signal);
    if (isStale(mine)) return;
    readingRun = null;
    if (!answer.ok) {
      fail("read", answer.failure);
      // A control moved while the words were being read is not lost with them.
      if (answer.failure.kind !== "offline") await sendWhatWaits();
      return;
    }
    heard(answer.meta);
    dispatch({ type: "read_answered", data: answer.data, meta: answer.meta });
    // Then the model, where one reads and the rules left words unread.
    const more = answer.data.model_pending ? readMore(said, sent) : null;
    const changed = answer.data.applied.some((edit) => edit.changed);
    const { pending } = getState();
    if (changed || !isEmpty(pending)) {
      await settle(mine, signal, answer.data.spec, answer.data.spec_hash, pending);
    } else {
      dispatch({ type: "settled" });
    }
    await more;
  }

  /**
   * Asks again, of the model this time, for the same words and the same search. It has a
   * stop of its own: a control that is moved meanwhile ranks, and does not stop the reading.
   * The words go to the call and nowhere else.
   */
  async function readMore(said: string, sent: PreferenceSpec) {
    const mine = new AbortController();
    reading = mine;
    const answer = await client.interpret({ text: said, spec: sent, ask_model: true }, mine.signal);
    if (reading !== mine) return;
    reading = null;
    if (answer.ok) dispatch({ type: "read_more_answered", data: answer.data });
    else dispatch({ type: "read_more_failed" });
  }

  /**
   * Stops the model's reading, where one is under way. What it would have added is let go,
   * and the store is told that nothing reads the words now: a search that is sent next may
   * fail or be stopped, and the page must not be left saying that Burro is still reading.
   */
  function stopReading() {
    if (reading === null) return;
    reading.abort();
    reading = null;
    dispatch({ type: "read_more_failed" });
  }

  return {
    submitText,
    applyEdits,

    async answerClarify(question, option) {
      const read = getState().read;
      if (read === null) return;
      const operations = answered(read.operations, question.group, question.index, option.id);
      if (operations === null) return;
      dispatch({ type: "question_answered", question, id: option.id });
      await applyEdits(operations);
    },

    leaveOut(question) {
      dispatch({ type: "question_left", question });
    },

    async choose(at, id, placeId) {
      const choice = getState().read?.suggestions[at]?.choices.find((one) => one.id === id);
      if (choice === undefined) return;
      const operations = placeId === undefined ? choice.operations : withPlace(choice.operations, placeId);
      // A journey that does not say where it leads is not sent: the person has yet to say.
      if (!namesItsPlaces(operations)) return;
      dispatch({ type: "suggestion_chosen", at, changes: !isEmpty(operations) });
      await applyEdits(operations);
    },

    async chooseAll(ats) {
      const offered = getState().read?.suggestions ?? [];
      // What the API names no way for is left: it is the person's to choose.
      const taken = [...new Set(ats)]
        .sort((one, other) => one - other)
        .flatMap((at) => {
          const suggestion = offered[at];
          const only = suggestion === undefined ? null : addedWithOthers(suggestion);
          return only === null || !namesItsPlaces(only.operations) ? [] : [{ at, operations: only.operations }];
        });
      if (taken.length === 0) return;
      dispatch({ type: "all_added", ats: taken.map(({ at }) => at) });
      // The edits of each choice, as the API gave them, in the order the things were noticed.
      await applyEdits(taken.reduce((edits, one) => merged(edits, one.operations), NO_EDITS));
    },

    async takeBack() {
      const added = getState().read?.added ?? null;
      if (added === null) return;
      dispatch({ type: "all_taken_back" });
      // The search as it stood before the press, ranked again. Nothing of what was added is kept.
      const { mine, signal } = begin();
      readingRun = null;
      await settle(mine, signal, added.spec, null, NO_EDITS);
    },

    boxChanged() {
      stopReading();
      dispatch({ type: "box_changed" });
    },

    async addPlace(place) {
      // The answer names the place: the spec holds its id, and `places` the release's name for it.
      await applyEdits(edits.placeAdd(place.place_id));
    },

    async setTenure(tenure) {
      const state = getState();
      if (state.spec.tenure === tenure) return;
      // Before anything is asked for, the other default is shown, and nothing is sent.
      if (state.untouched && isEmpty(state.pending) && readingRun === null) {
        dispatch({ type: "tenure_swapped", tenure });
        return;
      }
      await applyEdits(edits.tenure(tenure));
    },

    rankNow: rerank,

    async openShare(shareId) {
      const { mine, signal } = begin();
      readingRun = null;
      const answer = await client.getShare(shareId, signal);
      if (isStale(mine)) return null;
      // The page that opened the link says what went wrong. The search that was open is left as it was.
      if (!answer.ok) return answer.failure;
      // Where the release has moved on, the form is read again first, so that the shared
      // search is drawn with the names and the limits of the release that ranked it.
      await caughtUpWith(answer.meta);
      if (isStale(mine)) return null;
      dispatch({ type: "share_answered", id: shareId, data: answer.data, meta: answer.meta });
      await fill(mine, signal, answer.data, null);
      return null;
    },

    createShare(exactPlaces, signal) {
      // The spec is the last one the API returned. Nothing a person typed goes with it.
      return client.createShare({ spec: getState().spec, exact_destinations: exactPlaces }, signal);
    },

    async retry(text) {
      if (getState().failedStep === "read" && text !== undefined && text.trim() !== "") {
        await submitText(text);
        return;
      }
      await rerank();
    },

    stop() {
      // "Stop" is offered until the ranking of the words is in, which is after they are read.
      const wasReading = getState().phase === "interpreting";
      stopReading();
      inFlight?.abort();
      inFlight = null;
      current += 1;
      readingRun = null;
      dispatch({ type: "stopped" });
      // Stopping a sentence does not undo a control moved meanwhile.
      if (wasReading) void sendWhatWaits();
    },

    startAgain() {
      stopReading();
      inFlight?.abort();
      inFlight = null;
      current += 1;
      readingRun = null;
      dispatch({ type: "started_again" });
    },

    select(areaId) {
      dispatch({ type: "selected", areaId });
    },

    hover(areaId) {
      dispatch({ type: "hovered", areaId });
    },

    openSettings(open) {
      dispatch({ type: "settings_opened", open });
    },

    async loadGeometry() {
      if (getState().geometry !== null) return;
      const answer = await client.getGeometry();
      if (answer.ok) dispatch({ type: "geometry_loaded", geometry: answer.data });
      else dispatch({ type: "geometry_failed" });
    },

    async loadReader() {
      await whoReads();
    },

    wentOffline() {
      dispatch({ type: "online_changed", online: false });
    },

    async wentOnline() {
      const state = getState();
      const waiting =
        !isEmpty(state.pending) ||
        (state.failure?.kind === "offline" && state.failedStep === "rank") ||
        // The reasons or a profile that could not leave are asked for again with the ranking.
        failureOfTheCards(state)?.kind === "offline";
      dispatch({ type: "online_changed", online: true });
      // The edit that waited is sent once, now that it can leave.
      if (waiting) await rerank();
    },

    searchPlaces(text, signal) {
      return client.searchPlaces({ q: text, limit: PLACE_QUERY.limit }, signal);
    },
  };
}
