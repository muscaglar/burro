/**
 * What the search page does: each thing a person can do, as the calls it
 * makes and the events it sends to the store. docs/design/web.md, section 5.3.
 *
 * Three rules are kept here.
 *
 * 1. The sentence a person typed is passed to one call and is never kept. It
 *    is not in the store and not in this file's memory once the call is made.
 *    What is passed is what the box holds that the search has not read: the
 *    box cuts it, by the count the store holds of how far the search has read.
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
 *
 * And a sixth: the page asks nothing. Where a sentence is no plain list of
 * wishes the service applies none of it, and returns what it noticed as
 * offers. The page takes every one as soon as the reading is in, by the way
 * `takes.ts` chooses, and ranks. A name that several places bear is the
 * first the service gave. The service is as it was: what it offers is its
 * own to say, and what a model may read is its own to guard.
 *
 * A search that begins with no results in sight is answered no sooner than
 * Burro has been seen to hop: `wait.ts` says how long. A failure is said at
 * once, and so is the answer to a search that is refined.
 */

import type { Answer, Client, Failure } from "@/lib/api/client";
import { failed } from "@/lib/api/failure";
import type {
  FoundPlace,
  Meta,
  Operations,
  PlacesData,
  PreferenceSpec,
  RankedArea,
  ShareCreated,
  Tenure,
} from "@/lib/api/schema";

import { edits, isEmpty, merged, NO_EDITS } from "./edits";
import type { Change } from "./mark";
import {
  EXPLAINED,
  failureOfTheCards,
  reasonsAreIn,
  reasonsFailure,
  type LeftAt,
  type SearchEvent,
  type SearchState,
  type TakenAt,
} from "./state";
import { isAWish } from "./suggestion";
import {
  A_LIMIT_THE_WORDS_MAKE_FIRM,
  OF_A_WORD_READ_SEVERAL_WAYS,
  restsOn,
  settledOf,
  takenOfAll,
  thingOf,
  WHAT_THE_WORDS_TURN_AWAY,
  WHERE_BURRO_CANNOT_TELL,
  type Doubt,
  type Readings,
  type Turned,
  type Worded,
} from "./takes";

/** How many results the list holds, and how many of them the API gives reasons for. */
export const LIST_LENGTH = 20;
export { EXPLAINED };
/** How many results are asked for where none is kept: the fewest the API gives. */
export const GATHERED = 1;
/** The fewest and the most characters a place search may hold. */
export const PLACE_QUERY = { least: 2, most: 80, limit: 8 } as const;

/**
 * What is made of an edit. `rank`: the search is ranked again with it, and a search opens
 * of it where none was open. `gather`: it is sent to be applied, and kept as what the
 * search will be made of. No search opens of it, and nothing is ranked for the page: it
 * is what the second of the two ways in does, where its button makes the search.
 */
export type How = "rank" | "gather";

export interface FlowDeps {
  readonly client: Client;
  readonly getState: () => SearchState;
  readonly dispatch: (event: SearchEvent) => void;
  /**
   * How long a search that begins with no results in sight waits at the least before its
   * answer is shown, in milliseconds, asked as the search begins. Left out, it waits for
   * nothing.
   */
  readonly rests?: () => number;
  /** What is made of a thing that runs two ways where the words give neither. Left out, as the look has chosen. */
  readonly doubt?: Doubt;
  /** What is made of words that are read more ways than one. Left out, as the look has chosen. */
  readonly readings?: Readings;
  /** What is made of a thing the words turn away. Left out, as the look has chosen. */
  readonly turned?: Turned;
  /** What is made of a journey whose words make its limit firm. Left out, as the look has chosen. */
  readonly worded?: Worded;
}

export interface Flow {
  /**
   * Sends words to be read, with the search as it stands. They are what the box holds
   * that the search has not read, and go to the call and nowhere else.
   */
  submitText(text: string): Promise<void>;
  /** Sends the edits of one control. */
  applyEdits(operations: Operations, how?: How): Promise<void>;
  /** Told that the box changed, and never what to. What rested on the text that was sent goes. */
  boxChanged(): void;
  /**
   * Told where the box was changed and by how much, in counts, and never what went or what
   * came. How far the search has read moves with the words it stands among.
   */
  boxEdited(change: Change): void;
  /** Told how much the box holds as the page is drawn. A box that is drawn again is empty. */
  boxFound(holds: number): void;
  /** Adds a place picked from the place search as a journey. */
  addPlace(place: Pick<FoundPlace, "place_id">, how?: How): Promise<void>;
  setTenure(tenure: Tenure, how?: How): Promise<void>;
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

/** Waits so long, or until what is waited for is stopped, whichever comes first. */
function pause(milliseconds: number, signal: AbortSignal): Promise<void> {
  return new Promise((done) => {
    if (signal.aborted || milliseconds <= 0) {
      done();
      return;
    }
    const over = () => {
      clearTimeout(timer);
      signal.removeEventListener("abort", over);
      done();
    };
    const timer = setTimeout(over, milliseconds);
    signal.addEventListener("abort", over);
  });
}

export function createFlow({
  client,
  getState,
  dispatch,
  rests = () => 0,
  doubt = WHERE_BURRO_CANNOT_TELL,
  readings = OF_A_WORD_READ_SEVERAL_WAYS,
  turned = WHAT_THE_WORDS_TURN_AWAY,
  worded = A_LIMIT_THE_WORDS_MAKE_FIRM,
}: FlowDeps): Flow {
  let current = 0;
  let readingRun: number | null = null;
  /** The model's reading of what the rules left unread, while it is under way. */
  let reading: AbortController | null = null;
  let inFlight: AbortController | null = null;
  /** The release the form is being read again for, while it is, so that it is not asked for twice at once. */
  let catchingUp: { readonly release: string; readonly done: Promise<void> } | null = null;
  /** The release whose boundaries could not be read: as the page opened, or when its form was read again. */
  let boundariesOwed: string | null = null;
  /**
   * Until when the answer to a search that began with no results in sight is held back, by
   * the clock of the page. `null` while none is: before a search, once an answer is shown,
   * and while results are in sight.
   */
  let heldUntil: number | null = null;

  /**
   * A run of calls begins, and whatever was on its way is stopped. `answers` is true of a
   * run whose answer the page shows: a search, where what the second way in gathers and a
   * link that is opened are none.
   */
  function begin(answers = true) {
    inFlight?.abort();
    inFlight = new AbortController();
    current += 1;
    // A person waits for a first answer, and Burro hops where the results will stand. A
    // search that is sent again before its answer is shown waits no longer for it.
    if (!answers || getState().ranking !== null) heldUntil = null;
    else heldUntil ??= Date.now() + Math.max(0, rests());
    return { mine: current, signal: inFlight.signal };
  }

  /** Ends once the answer may be shown: at once, where nothing holds it back or the search was stopped. */
  async function rested(signal: AbortSignal): Promise<void> {
    if (heldUntil === null) return;
    await pause(heldUntil - Date.now(), signal);
  }

  /** An answer is shown, or the search has ended with none: the next to begin waits as a first one does. */
  function shown() {
    heldUntil = null;
  }

  const isStale = (mine: number) => mine !== current;

  function fail(step: "read" | "rank", failure: Failure) {
    // A failure is said at once: nobody is made to wait to be told that nothing came.
    shown();
    // A call that was stopped has nothing to report.
    if (failure.kind === "aborted") dispatch({ type: "stopped" });
    else dispatch({ type: "failed", step, failure });
  }

  /**
   * Takes what was noticed in the words that were last read, of itself: every question is
   * settled and every offer is taken, by the way `takes.ts` chooses. The edits wait to be
   * sent, as the edits of a control do, and nothing is sent here. It answers whether any
   * edit came of it.
   */
  function takeWhatWasNoticed(): boolean {
    const { read, meta } = getState();
    if (read === null) return false;
    let edits = NO_EDITS;
    if (read.clarify.length > 0) {
      const settled = read.clarify.map((question) => {
        // A rule for an area hides it, or leaves every other out: none is set on a guess.
        const made = question.group === "commute_ops" ? settledOf(read.operations, question) : null;
        return { question, id: made?.option?.id ?? null, operations: made?.operations ?? null };
      });
      for (const one of settled) edits = merged(edits, one.operations ?? NO_EDITS);
      dispatch({ type: "questions_settled", settled });
    }
    if (read.suggestions.length === 0) return !isEmpty(edits);
    const taken: TakenAt[] = [];
    const left: LeftAt[] = [];
    const again: number[] = [];
    // Words that are read more ways than one count as the look has them count, whoever
    // read them: what the rules took of some words, a model's reading does not take again.
    const made = takenOfAll(read.suggestions, meta, doubt, readings, read.words, turned, worded);
    read.suggestions.forEach((offer, at) => {
      const one = made[at];
      if (one === undefined) return;
      if (one.way === null) {
        left.push({ at, why: one.why });
        return;
      }
      const thing = thingOf(offer, one.operations);
      // What was taken of a thing as the rules read it is not taken again as a model did:
      // taken twice, a wish would count for twice as much.
      if (read.things.includes(thing)) again.push(at);
      else taken.push({ at, operations: one.operations, marks: one.marks, thing, words: isAWish(offer) ? restsOn(offer) : null });
    });
    for (const one of taken) edits = merged(edits, one.operations);
    dispatch({ type: "offers_taken", taken, left, again });
    return !isEmpty(edits);
  }

  /** Every answer says which release made it. If that has changed, the form is read again. */
  function heard(meta: Meta) {
    void caughtUpWith(meta);
  }

  /** The same, for whoever must wait until the form has been read again before going on. */
  function caughtUpWith(meta: Pick<Meta, "release_id">): Promise<void> {
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
    // A first answer is shown no sooner than Burro has been seen to hop.
    await rested(signal);
    if (isStale(mine)) return;
    shown();
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

  /**
   * Sends what was chosen in the second way in to be applied, with the last spec returned.
   * The answer brings the spec the settings are drawn from, and the name of each place.
   * Its ranking is asked for as short as can be and is not kept, and neither its reasons
   * nor a profile is asked for: no search is made until its button is pressed.
   */
  async function gather() {
    const { spec, pending } = getState();
    if (isEmpty(pending)) return;
    const { mine, signal } = begin(false);
    readingRun = null;
    dispatch({ type: "gather_started" });
    const answer = await client.rank({ spec, limit: GATHERED, operations: pending }, signal);
    if (isStale(mine)) return;
    if (!answer.ok) {
      fail("rank", answer.failure);
      return;
    }
    heard(answer.meta);
    dispatch({ type: "gathered", data: answer.data, sent: pending, meta: answer.meta });
  }

  /** Sends what waits as the search stands: gathered where it gathers, and else ranked. */
  const send = () => (getState().gathering ? gather() : rerank());

  /** Sends the edits that are waiting, if any are. */
  async function sendWhatWaits() {
    if (!isEmpty(getState().pending)) await send();
  }

  async function applyEdits(operations: Operations, how: How = "rank") {
    if (isEmpty(operations)) return;
    dispatch({ type: "queued", operations, gathers: how === "gather" });
    // A sentence is being read: its answer brings the spec these edits are for.
    if (readingRun !== null && readingRun === current) return;
    await send();
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
    return answer.failure;
  }

  async function submitText(text: string) {
    const said = text.trim();
    if (said === "") return;
    stopReading();
    const { mine, signal } = begin();
    readingRun = mine;
    // The store is told how much was handed over, as it was typed, and none of it: once the
    // words are read, the search has read that much further into the box.
    dispatch({ type: "read_started", seq: mine, letters: text.length });
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
    // Then the model, where one reads and the rules left words unread. It is asked at
    // once, and reads while the person waits. What it read joins what the rules read, and
    // so is kept until that is on the page.
    let onThePage: () => void = () => undefined;
    const byTheRules = new Promise<void>((done) => {
      onThePage = done;
    });
    const more = answer.data.model_pending ? readMore(said, sent, byTheRules) : null;
    // A first answer is shown no sooner than Burro has been seen to hop: what was read and
    // what is ranked of it come together, where he was.
    await rested(signal);
    if (isStale(mine)) {
      onThePage();
      return;
    }
    heard(answer.meta);
    dispatch({ type: "read_answered", data: answer.data, meta: answer.meta });
    // What was noticed and not applied is taken, and what would have been asked is settled.
    takeWhatWasNoticed();
    onThePage();
    const changed = answer.data.applied.some((edit) => edit.changed);
    const { pending } = getState();
    if (changed || !isEmpty(pending)) {
      await settle(mine, signal, answer.data.spec, answer.data.spec_hash, pending);
    } else {
      shown();
      dispatch({ type: "settled" });
    }
    await more;
  }

  /**
   * Asks again, of the model this time, for the same words and the same search. It has a
   * stop of its own: a control that is moved meanwhile ranks, and does not stop the reading.
   * The words go to the call and nowhere else.
   */
  async function readMore(said: string, sent: PreferenceSpec, byTheRules: Promise<void>) {
    const mine = new AbortController();
    reading = mine;
    const answer = await client.interpret({ text: said, spec: sent, ask_model: true }, mine.signal);
    if (reading !== mine) return;
    // What the rules read is on the page first, whichever answer was the sooner to land.
    await byTheRules;
    if (reading !== mine) return;
    reading = null;
    if (!answer.ok) {
      dispatch({ type: "read_more_failed" });
      return;
    }
    dispatch({ type: "read_more_answered", data: answer.data });
    // What the model noticed beyond the rules is taken as well, and ranked with the rest:
    // what waits is sent together, so nothing that the rules read is lost with it.
    if (takeWhatWasNoticed()) await send();
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

    boxChanged() {
      stopReading();
      dispatch({ type: "box_changed" });
    },

    boxEdited(change) {
      dispatch({ type: "box_edited", change });
    },

    boxFound(holds) {
      dispatch({ type: "box_found", holds });
    },

    async addPlace(place, how) {
      // The answer names the place: the spec holds its id, and `places` the release's name for it.
      await applyEdits(edits.placeAdd(place.place_id), how);
    },

    async setTenure(tenure, how) {
      const state = getState();
      if (state.spec.tenure === tenure) return;
      // Before anything is asked for, the other default is shown, and nothing is sent.
      if (state.untouched && isEmpty(state.pending) && readingRun === null) {
        dispatch({ type: "tenure_swapped", tenure });
        return;
      }
      await applyEdits(edits.tenure(tenure), how);
    },

    rankNow: rerank,

    async openShare(shareId) {
      const { mine, signal } = begin(false);
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
      // What was chosen in the second way in and could not be sent is sent again, as it was:
      // no search is made of trying again.
      await send();
    },

    stop() {
      // "Stop" is offered until the ranking of the words is in, which is after they are read.
      const wasReading = getState().phase === "interpreting";
      stopReading();
      inFlight?.abort();
      inFlight = null;
      current += 1;
      readingRun = null;
      shown();
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
      shown();
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
      if (answer.ok) {
        dispatch({ type: "geometry_loaded", geometry: answer.data });
        return;
      }
      dispatch({ type: "geometry_failed" });
      // They are owed, as where a release changed: the next answer asks for them again. One
      // slow answer as the page opened left it with no map for as long as it stayed open.
      // Where they came with the form of a release meanwhile, nothing is owed.
      if (getState().geometry === null) boundariesOwed = getState().meta.release_id;
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
      // Boundaries that are owed are asked for now that a call can leave, whether or not
      // anything else is: with nothing to send, no answer would come to ask for them.
      if (boundariesOwed !== null) void caughtUpWith({ release_id: boundariesOwed });
      // The edit that waited is sent once, now that it can leave.
      if (waiting) await send();
    },

    searchPlaces(text, signal) {
      return client.searchPlaces({ q: text, limit: PLACE_QUERY.limit }, signal);
    },
  };
}
