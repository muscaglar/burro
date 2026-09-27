/**
 * What a search is, while it is open: one plain object, and the one function
 * that moves it on. docs/design/web.md, section 5.3.
 *
 * It is held in memory and nowhere else. It never holds what a person typed:
 * the sentence stays in its box and in the body of one request. It holds ids
 * of the release, the spec the API last returned, and what the API answered.
 * Of the box it holds counts: how far into it the search has read, and where
 * the words that were last read begin.
 *
 * `reduce` is pure. It builds no spec: every spec in the state is one the
 * API returned, or one of the two defaults the API served.
 */

import type { Failure } from "@/lib/api/failure";
import type {
  AreaData,
  AreaSummary,
  Clarify,
  Explanation,
  ExplanationsData,
  Fact,
  GeometryData,
  InterpretData,
  Meta,
  MetaData,
  NamedPlace,
  Operations,
  OpsGroup,
  PreferenceSpec,
  RankData,
  Reader,
  Rejected,
  ShareData,
  Suggestion,
  Tenure,
} from "@/lib/api/schema";
import type { Handed } from "@/lib/api/handed";

import { keyOf } from "./suggestion";
import { chipOf, countOf, GROUPS, isEmpty, merged, NO_EDITS, saidBy, type ChipKey } from "./edits";
import {
  answered,
  begunAgain,
  edited,
  found,
  NO_BOX,
  notRead,
  putBack,
  ranked,
  readNoMore,
  sent,
  type Box,
  type Change,
} from "./mark";
import type { AssumedCode, Mark, WhyLeft } from "./takes";

export type Phase = "empty" | "interpreting" | "results" | "refining";

/** How many results are cards in full, which is how many the API gives reasons for. */
export const EXPLAINED = 5;

/**
 * Which release and which engine made an answer. It is kept with what the
 * answer brought, because nothing else says it: a hash is of the spec alone,
 * and the same spec has the same hash on every release.
 */
export type Served = Pick<Meta, "release_id" | "engine_version">;

export function servedBy(meta: Meta): Served {
  return { release_id: meta.release_id, engine_version: meta.engine_version };
}

/** True when both were made by one release and one engine. */
export function sameServed(one: Served | null, other: Served | null): boolean {
  return (
    one !== null &&
    other !== null &&
    one.release_id === other.release_id &&
    one.engine_version === other.engine_version
  );
}

/** Which call a failure came from: reading the words, or ranking. */
export type Step = "read" | "rank";

/** What route 1 said of the words, in codes and fixed text. Never the words. */
export interface Read
  extends Pick<
    InterpretData,
    | "status"
    | "operations"
    | "assumptions"
    | "clarify"
    | "unmet"
    | "rejected"
    | "notice"
    | "notice_text"
    | "interpreter"
    | "degraded"
    // True when the rules read the words because the language model would not.
    | "model_refused"
    // What the reader noticed and did not apply. The page takes each as soon as the reading
    // is in, so none is held for longer than that. Each holds where its words stand in the
    // text, as offsets, and never the words.
    | "suggestions"
    // The stretches of the text the reader made nothing of: offsets, and never the words.
    // They mean nothing without the text, which only the box holds.
    | "unread"
    // What was asked for that the release holds for no area, each by the API's name for it.
    | "not_in_release"
  > {
  /** How many edits the words were read into. */
  readonly edits: number;
  /** True when any of them changed the spec. */
  readonly changed: boolean;
  /**
   * True when a stretch of what was typed was not read. It stays true of the ranking when
   * the box changes, though where the stretch stood can no longer be shown.
   */
  readonly partUnread: boolean;
  /** The count of answers when this one came, so the page can tell it is the latest. */
  readonly at: number;
  /**
   * Which sending of words this is the reading of, by the number of its run. What a model
   * reads of the same words after the rules is the same reading, and what is read of the
   * next words that are sent is another.
   */
  readonly of: number;
  /** The release and the engine that read the words. */
  readonly by: Served;
  /**
   * True while a model reads what the rules left unread. What the rules noticed is on the
   * page meanwhile: it never waits on a model.
   */
  readonly more: boolean;
  /**
   * The offers that something was made of, taken or left, each by what tells it from every
   * other of its answer: so that none is taken a second time when a model has read.
   */
  readonly chosen: readonly string[];
  /** What was taken, each by what it is of: what the rules took of a thing, a model's reading does not take again. */
  readonly things: readonly string[];
  /**
   * The words of which a wish was taken, by where they stand in what was sent: offsets,
   * and never the words. What another reader reads into the same words is a second
   * reading of them. They go when the box changes, as all that is known by offsets does.
   */
  readonly words: readonly string[];
  /** How many offers Burro took of itself, of the words that were last read. */
  readonly took: number;
  /** What Burro noticed and took nothing of, each with why, in the order it was noticed. */
  readonly left: readonly Left[];
}

/**
 * A thing Burro noticed and took nothing of. What it is called, what it is of, and what
 * the service says of it are the service's words, as they came. It holds nothing typed.
 */
export interface Left extends Pick<Suggestion, "target" | "label" | "does" | "follows" | "note"> {
  readonly why: WhyLeft;
}

/** One offer that was taken: where it stood among those of its answer, the edits of the way taken, and what was assumed. */
export interface TakenAt {
  readonly at: number;
  readonly operations: Operations;
  readonly marks: readonly Mark[];
  /** What it is of, which tells it from every other thing whoever read it. */
  readonly thing: string;
  /** Where the words of a wish stand, as offsets. `null` or left out of what is no wish. */
  readonly words?: string | null;
}

/** One offer that nothing was taken of: where it stood, and why. */
export interface LeftAt {
  readonly at: number;
  readonly why: WhyLeft;
}

/**
 * One question that was settled with no person asked. `id` is the place that was taken,
 * the first the service gave, with the edit that holds it. Both are `null` where nothing
 * was taken: the service gave no place, or the question was of an area.
 */
export interface SettledAt {
  readonly question: Clarify;
  readonly id: string | null;
  readonly operations: Operations | null;
}

export type Ranking = Pick<
  RankData,
  "scores" | "ranked" | "filtered" | "unranked" | "empty_spec" | "areas_ranked" | "areas_listed"
>;

/** Edits a control sent that the reducer refused, with the edits they point into. */
export interface Refused {
  readonly operations: Operations;
  readonly rejected: readonly Rejected[];
}

/**
 * The share a search was opened from: its id, and what the API said of it
 * when it was opened. The id is held so that coming back to the link does
 * not open it again over what the person has changed since.
 */
export interface Shared extends Pick<ShareData, "coarsened" | "stale" | "original_release_id"> {
  readonly id: string;
}

/** What was assumed of each part of the search, by the key of its chip. */
export type Assumed = Readonly<Record<string, readonly AssumedCode[]>>;

/**
 * The search as it was when a sentence was sent: what reading the sentence
 * replaces before its ranking is in. "Stop" puts it back, so that the chips
 * are never left saying one search over the ranking of another.
 */
export type Kept = Pick<
  SearchState,
  | "spec"
  | "specHash"
  | "untouched"
  | "read"
  | "refused"
  | "assumed"
  | "quoted"
  | "placeNames"
  | "gaveWay"
  | "budgetWent"
  | "degraded"
>;

/**
 * True when Burro could not be reached at all: the request could not leave, or the
 * website holds no address for it. Nothing else can be asked of it either, so it is not
 * said that the words could not be read, nor that the settings do the same job.
 */
export function isUnreachable(failure: Failure): boolean {
  return failure.kind === "network" || failure.kind === "not_configured";
}

/** Reasons, with the search and the release they are for. */
export interface Ahead {
  readonly hash: string;
  readonly by: Served;
  readonly explanations: readonly Explanation[];
  readonly facts: readonly Fact[];
}

export interface SearchState {
  /** What the page was built on. Replaced if the API moves to another release. */
  readonly meta: Handed;
  readonly areas: readonly AreaSummary[];
  readonly geometry: GeometryData | null;
  readonly geometryFailed: boolean;
  /**
   * Who reads what is typed, as the service says now. `null` until it has said: what the
   * page was built on may be of a service that was set otherwise, so it is never shown in
   * its place. No sentence is sent while this is `null`.
   */
  readonly reader: Reader | null;

  readonly phase: Phase;
  /** The phase to go back to when a request is stopped or fails. */
  readonly before: "empty" | "results";
  /** The search as it was when the sentence now being read was sent. `null` once its ranking is in. */
  readonly kept: Kept | null;
  readonly seq: number;
  /**
   * Counts the answers that leave no edit waiting. A control holds what it was set to
   * against this count, and is the API's again when it moves. A reading that comes while
   * an edit waits does not move it: the edit has not been answered.
   */
  readonly answers: number;
  readonly failure: Failure | null;
  readonly failedStep: Step | null;
  readonly online: boolean;
  /** True when the words could not be read, so the settings are the way in. */
  readonly degraded: boolean;
  readonly settingsOpen: boolean;
  /**
   * True while the settings are open because the page opened them, for words it could not
   * read, and the person has not used them since. They close again when words are read.
   */
  readonly settingsByPage: boolean;

  readonly spec: PreferenceSpec;
  readonly specHash: string | null;
  /** True until an answer changes the spec: the spec is still a default as served. */
  readonly untouched: boolean;
  /** Edits made and not yet answered. They are sent again with the last spec returned. */
  readonly pending: Operations;
  /**
   * True while the search is what was chosen in the second of the two ways in, and no
   * search has been made of it. Each thing that was chosen there was sent to be applied,
   * so that the settings are drawn from the spec the API returned: a place is named, and
   * given the limits a journey starts from, by the API alone. No ranking was kept of it,
   * and the page is as it is before a search. It ends when a search is made: of the button
   * that ranks by the settings, of a sentence, or of anything else that opens one.
   */
  readonly gathering: boolean;

  readonly read: Read | null;
  readonly refused: Refused | null;
  readonly ranking: Ranking | null;
  readonly rankedHash: string | null;
  /** The release and the engine that made the ranking on screen. */
  readonly rankedBy: Served | null;
  /** How many areas changed place at the last answer. `null` for a first ranking. */
  readonly moved: number | null;
  /** How many areas the ranking before this one ranked. `null` for a first ranking. */
  readonly rankedBefore: number | null;
  /** True when the last answer made the settings nobody chose count for less. */
  readonly gaveWay: boolean;
  /** True when the last answer took the budget off, because the tenure changed. */
  readonly budgetWent: boolean;

  /** The reasons in hand. They are the ranking's only if `reasonsAreIn` says so. */
  readonly explanations: readonly Explanation[];
  readonly explainedHash: string | null;
  readonly explainedBy: Served | null;
  /** Why the reasons of a search could not be loaded, whole: its message and the id to quote. */
  readonly explainFailure: { readonly hash: string; readonly failure: Failure } | null;
  /**
   * Reasons that came before the ranking they are for. They wait here, and
   * the reasons on screen stay, until that ranking comes. If it never does,
   * the ranking on screen keeps its own reasons.
   */
  readonly explanationsAhead: Ahead | null;
  readonly facts: Readonly<Record<string, Fact>>;
  /** The release and the engine that made each fact, by `fact_id`. */
  readonly factsBy: Readonly<Record<string, Served>>;
  readonly details: Readonly<Record<string, AreaData>>;
  /** The release and the engine that made each profile, by `area_id`. */
  readonly detailsBy: Readonly<Record<string, Served>>;
  /** Why the profile of an area could not be loaded, by `area_id`. */
  readonly detailFailures: Readonly<Record<string, Failure>>;

  /** The release's own name for each place the spec names, by place id. From the answer that brought the spec. */
  readonly placeNames: Readonly<Record<string, string>>;
  readonly assumed: Assumed;
  /**
   * The word a vibe was read from, where the word has two meanings and the reader took
   * one: by the key of its chip. It is the lexicon's spelling, which the API sends, and
   * never what was typed.
   */
  readonly quoted: Readonly<Record<string, string>>;
  /**
   * True when the person picked renting or buying before anything was sent. The page then
   * shows the default the API served for that tenure, and sends nothing, so no answer says
   * that the tenure was chosen. Once an edit states the tenure, the spec says so itself.
   */
  readonly tenurePicked: boolean;

  /** The share the search was opened from. `null` for a search the person began. */
  readonly shared: Shared | null;

  readonly selectedId: string | null;
  readonly hoveredId: string | null;

  /**
   * What the search knows of the box: how far into it the search has read, and where the
   * words that were last read begin. Counts, and never a word: the box alone holds what
   * was typed.
   */
  readonly box: Box;
}

export type SearchEvent =
  | { readonly type: "tenure_swapped"; readonly tenure: Tenure }
  // `gathers` is true of what was chosen in the second way in, where a search is made of
  // its button alone: it is kept, and no search is made of it.
  | { readonly type: "queued"; readonly operations: Operations; readonly gathers?: boolean }
  // What was chosen in the second way in is sent to be applied, and has been. No ranking is
  // kept of the answer: it brings the spec, the names of its places and what was refused.
  | { readonly type: "gather_started" }
  | {
      readonly type: "gathered";
      readonly data: Pick<RankData, "spec" | "spec_hash" | "rejected" | "places">;
      readonly sent: Operations;
      readonly meta: Meta;
    }
  // `letters` is how many characters were handed over to be read, as they were typed: all
  // that stands in the box after what the search has read. It is a count, and no word.
  | { readonly type: "read_started"; readonly seq: number; readonly letters?: number }
  // Every answer comes with the `meta` of its envelope, which names the release that made it.
  | { readonly type: "read_answered"; readonly data: InterpretData; readonly meta: Meta }
  | { readonly type: "rank_started"; readonly seq: number }
  | {
      readonly type: "rank_answered";
      readonly data: RankData;
      readonly sent: Operations;
      readonly meta: Meta;
    }
  | { readonly type: "share_answered"; readonly id: string; readonly data: ShareData; readonly meta: Meta }
  | { readonly type: "explain_answered"; readonly data: ExplanationsData; readonly meta: Meta }
  | { readonly type: "explain_failed"; readonly hash: string; readonly failure: Failure }
  | { readonly type: "detail_answered"; readonly data: AreaData; readonly meta: Meta }
  | { readonly type: "detail_failed"; readonly areaId: string; readonly failure: Failure }
  | { readonly type: "settled" }
  | { readonly type: "failed"; readonly step: Step; readonly failure: Failure }
  | { readonly type: "stopped" }
  | { readonly type: "started_again" }
  // Burro settled what it would have asked, of itself: a name that several places bear is
  // the first the service gave. The edits wait to be sent, as the edits of a control do.
  | { readonly type: "questions_settled"; readonly settled: readonly SettledAt[] }
  // Burro took what it noticed, of itself: each offer by the way the page chose for it.
  // The edits wait to be sent, as the edits of a control do, and what was chosen for the
  // person is assumed. What nothing was taken of is kept with why, to be said in a line.
  // `again` are the offers of what was taken already, as another reader named it: they go,
  // and nothing more is made of them.
  | {
      readonly type: "offers_taken";
      readonly taken: readonly TakenAt[];
      readonly left: readonly LeftAt[];
      readonly again?: readonly number[];
    }
  // A model has read what the rules left unread. What it noticed is then taken as well.
  | { readonly type: "read_more_answered"; readonly data: InterpretData }
  // It could not be asked, did not answer, or was stopped. What the rules read stands.
  | { readonly type: "read_more_failed" }
  // Where words stand is known for the text that was sent: what was not read goes when the box changes.
  | { readonly type: "box_changed" }
  // Where the box was changed, and by how much: counts, and never what went or what came.
  | { readonly type: "box_edited"; readonly change: Change }
  // How much the box holds as the page is drawn. A box that is drawn again is empty.
  | { readonly type: "box_found"; readonly holds: number }
  | { readonly type: "online_changed"; readonly online: boolean }
  | { readonly type: "settings_opened"; readonly open: boolean }
  | { readonly type: "geometry_loaded"; readonly geometry: GeometryData }
  | { readonly type: "geometry_failed" }
  // The service said who reads what is typed, or was asked and could not.
  | { readonly type: "reader_said"; readonly reader: Reader }
  | {
      readonly type: "release_changed";
      readonly meta: MetaData;
      readonly areas: readonly AreaSummary[];
    }
  | { readonly type: "selected"; readonly areaId: string | null }
  | { readonly type: "hovered"; readonly areaId: string | null };

export function initialState(
  meta: Handed,
  areas: readonly AreaSummary[],
  geometry: GeometryData | null = null,
  reader: Reader | null = null,
): SearchState {
  return {
    meta,
    areas,
    geometry,
    geometryFailed: false,
    reader,
    phase: "empty",
    before: "empty",
    kept: null,
    seq: 0,
    answers: 0,
    failure: null,
    failedStep: null,
    online: true,
    degraded: false,
    settingsOpen: false,
    settingsByPage: false,
    spec: meta.defaults.rent,
    specHash: null,
    untouched: true,
    pending: NO_EDITS,
    gathering: false,
    read: null,
    refused: null,
    ranking: null,
    rankedHash: null,
    rankedBy: null,
    moved: null,
    rankedBefore: null,
    gaveWay: false,
    budgetWent: false,
    explanations: [],
    explainedHash: null,
    explainedBy: null,
    explainFailure: null,
    explanationsAhead: null,
    facts: {},
    factsBy: {},
    details: {},
    detailsBy: {},
    detailFailures: {},
    placeNames: {},
    assumed: {},
    quoted: {},
    tenurePicked: false,
    shared: null,
    selectedId: null,
    hoveredId: null,
    box: NO_BOX,
  };
}

function without<Value>(record: Readonly<Record<string, Value>>, key: string) {
  const { [key]: gone, ...rest } = record;
  void gone;
  return rest;
}

/** The assumptions that still stand after these edits have said what they say. */
function afterEdits(assumed: Assumed, operations: Operations, only?: ReadonlySet<string>): Assumed {
  let next: Record<string, readonly AssumedCode[]> = { ...assumed };
  for (const group of GROUPS) {
    operations[group].forEach((edit, index) => {
      if (only && !only.has(`${group}.${index}`)) return;
      for (const { key, states } of saidBy(operations, group, index)) {
        // A part that is taken out leaves nothing assumed behind it.
        const takenOut = edit.action === "remove" || edit.action === "clear";
        if (takenOut && key !== "budget") {
          next = without(next, key);
          continue;
        }
        const kept = (next[key] ?? []).filter((code) => !states.includes(code));
        next = kept.length > 0 ? { ...next, [key]: kept } : without(next, key);
      }
    });
  }
  return next;
}

/** What can be assumed of a place: how to travel there, how long at most, and whether that is firm. */
const OF_A_PLACE: readonly AssumedCode[] = ["mode", "max_minutes", "strictness"];

/**
 * A place that was added is assumed in every part its edit does not state. Words say so
 * through the API's own assumptions. A place picked from the field says nothing of how to
 * travel or for how long, so all of it was filled in, and all of it is marked.
 */
function withPlacesAdded(assumed: Assumed, operations: Operations): Assumed {
  let next = assumed;
  operations.commute_ops.forEach((edit, index) => {
    if (edit.action !== "add" || edit.place_id === "") return;
    for (const { key, states } of saidBy(operations, "commute_ops", index)) {
      const held = next[key] ?? [];
      const unsaid = OF_A_PLACE.filter((code) => !states.includes(code) && !held.includes(code));
      if (unsaid.length > 0) next = { ...next, [key]: [...held, ...unsaid] };
    }
  });
  return next;
}

/** What can be assumed of a budget: the size of home it is for, and whether it is firm. */
const OF_A_BUDGET: readonly AssumedCode[] = ["segment", "strictness"];

/**
 * A budget that is given to a search that had none is assumed in every part its edits do
 * not state. An offer of a budget holds the amount alone, and so does the number typed in
 * the settings: nobody chose the size of home or whether the limit is firm, and the chip
 * must not read as if they had. A budget the person has set a part of before is left as it is.
 *
 * What is sent together is read together. One press sends the amount and the kind of home
 * in an edit each, as they were offered, so the kind of home is the person's own words
 * though the edit that holds the amount does not hold it: "£400,000, A flat assumed" stood
 * under a sentence that said "a 1 bed flat".
 */
function withBudgetSet(assumed: Assumed, budget: PreferenceSpec["budget"], operations: Operations): Assumed {
  if (budget.amount !== null || budget.provenance !== "default") return assumed;
  const ofTheBudget = operations.budget_ops.flatMap((_, index) =>
    saidBy(operations, "budget_ops", index).filter(({ key }) => key === "budget"),
  );
  const stated = new Set(ofTheBudget.flatMap(({ states }) => states));
  let next = assumed;
  operations.budget_ops.forEach((edit) => {
    if (edit.action !== "set" || edit.amount === 0) return;
    const held = next.budget ?? [];
    const unsaid = OF_A_BUDGET.filter((code) => !stated.has(code) && !held.includes(code));
    if (unsaid.length > 0) next = { ...next, budget: [...held, ...unsaid] };
  });
  return next;
}

/**
 * The kind of home that Burro took, where a person named a house and no kind of house. The
 * edit that holds it says that it is Burro's, `inferred`, so the search says that it is
 * assumed, as it does where the API applies the same of a plain sentence. A kind that a
 * person presses is theirs, and is marked as nothing.
 */
function withTheKindTaken(assumed: Assumed, operations: Operations): Assumed {
  const took = operations.budget_ops.some((edit) => edit.segment !== "unchanged" && edit.provenance === "inferred");
  const held = assumed.budget ?? [];
  if (!took || held.includes("segment")) return assumed;
  return { ...assumed, budget: [...held, "segment"] };
}

/**
 * What Burro chose for the person in taking what it noticed, laid on what was assumed
 * already: the way of a thing, whether a limit is firm, which of several places.
 */
function withMarks(assumed: Assumed, marks: readonly Mark[]): Assumed {
  let next = assumed;
  for (const { key, code } of marks) {
    const held = next[key] ?? [];
    if (!held.includes(code)) next = { ...next, [key]: [...held, code] };
  }
  return next;
}

/**
 * What becomes of the search as edits are made and wait to be sent: they are kept to be
 * sent with the last spec returned, and what they state is assumed no longer.
 */
function withEditsWaiting(
  state: SearchState,
  operations: Operations,
): Pick<SearchState, "pending" | "assumed" | "settingsByPage" | "degraded"> {
  return {
    pending: merged(state.pending, operations),
    assumed: withTheKindTaken(
      withBudgetSet(withPlacesAdded(afterEdits(state.assumed, operations), operations), state.spec.budget, operations),
      operations,
    ),
    // The person is using the controls, so the settings are theirs to close.
    settingsByPage: false,
    // That words could not be read is said until the person does something about it:
    // they have now. What the rules read in place of a model is said until the next sentence.
    degraded: state.degraded && (state.read?.degraded ?? false),
  };
}

function withAssumptions(assumed: Assumed, data: Pick<InterpretData, "operations" | "assumptions">) {
  const next: Record<string, readonly AssumedCode[]> = { ...assumed };
  for (const { group, index, code } of data.assumptions) {
    const key = chipOf(data.operations, group, index, code);
    if (key === null) continue;
    const held = next[key] ?? [];
    if (!held.includes(code)) next[key] = [...held, code];
  }
  return next;
}

/** The word each part was read from, where the reader says it took one meaning of a word that has two. */
function withQuoted(
  quoted: SearchState["quoted"],
  data: Pick<InterpretData, "operations" | "assumptions">,
): SearchState["quoted"] {
  let next = quoted;
  for (const { group, index, code, word } of data.assumptions) {
    if (code !== "word" || word === "") continue;
    const key = chipOf(data.operations, group, index, code);
    if (key !== null && next[key] !== word) next = { ...next, [key]: word };
  }
  return next;
}

/** Only what is still among the keys given. The same record where that is all of it. */
function onlyOf<Value>(record: Readonly<Record<string, Value>>, keys: ReadonlySet<string>) {
  const kept = Object.keys(record).filter((key) => keys.has(key));
  if (kept.length === Object.keys(record).length) return record;
  return Object.fromEntries(kept.map((key) => [key, record[key] as Value]));
}

/** The name of each place an answer names, by place id. The names are the release's own. */
export function namesOf(places: readonly NamedPlace[]): Readonly<Record<string, string>> {
  return Object.fromEntries(places.map((place) => [place.place_id, place.name]));
}

/** True when both point at the same edit. */
function sameEdit(one: { group: OpsGroup; index: number }, other: { group: OpsGroup; index: number }) {
  return one.group === other.group && one.index === other.index;
}

/**
 * What was read, with a question gone from it. Where the question was settled, the refusal
 * it stood for goes with it. Where nothing was taken for it, the refusal stays, and is
 * what the page says of the place: that Burro does not know it.
 */
function withoutQuestion(read: Read, question: Clarify, settled: boolean): Read {
  return {
    ...read,
    clarify: read.clarify.filter((asked) => !sameEdit(asked, question)),
    rejected: settled ? read.rejected.filter((refusal) => !sameEdit(refusal, question)) : read.rejected,
  };
}

/**
 * How many areas stand elsewhere in the order than they did, among the areas ranked both
 * times. An area that went, or came, moves no other: what is left stands in the order it
 * stood in. How many went or came is said apart, from how many were ranked before.
 */
export function movedBetween(before: Ranking, after: Ranking): number {
  const stayed = new Set(before.scores.map((score) => score.area_id));
  const still = new Set(after.scores.map((score) => score.area_id));
  const was = before.scores.map((score) => score.area_id).filter((areaId) => still.has(areaId));
  const is = after.scores.map((score) => score.area_id).filter((areaId) => stayed.has(areaId));
  return is.filter((areaId, at) => was[at] !== areaId).length;
}

/** True when a setting nobody chose counts for less in `after` than it did in `before`. */
export function gaveWayBetween(before: PreferenceSpec, after: PreferenceSpec): boolean {
  const was = new Map(
    before.weights
      .filter((weight) => weight.provenance === "default")
      .map((weight) => [weight.feature_id, weight.weight]),
  );
  return after.weights.some((weight) => {
    const held = was.get(weight.feature_id);
    return weight.provenance === "default" && held !== undefined && weight.weight < held;
  });
}

/**
 * True when `after` has no budget where `before` had one, and the tenure is another. A
 * change of tenure takes the budget off, because a rent is not a price (contract 5.3,
 * rule 5). Nobody asked for it to go, so the page says that it went.
 */
export function budgetWentBetween(before: PreferenceSpec, after: PreferenceSpec): boolean {
  return before.budget.amount !== null && after.budget.amount === null && before.tenure !== after.tenure;
}

type Learned = Pick<SearchState, "facts" | "factsBy">;

/**
 * The facts in hand, with those an answer brought. A fact made by the release
 * that made the ranking is not given up for one made by another: a browser may
 * answer a profile from its own cache for an hour after the release has moved.
 */
function withFacts(held: Learned, facts: readonly Fact[], by: Served, rankedBy: Served | null): Learned {
  if (facts.length === 0) return held;
  const next: Record<string, Fact> = { ...held.facts };
  const nextBy: Record<string, Served> = { ...held.factsBy };
  const stranger = rankedBy !== null && !sameServed(by, rankedBy);
  for (const fact of facts) {
    if (stranger && sameServed(nextBy[fact.fact_id] ?? null, rankedBy)) continue;
    next[fact.fact_id] = fact;
    nextBy[fact.fact_id] = by;
  }
  return { facts: next, factsBy: nextBy };
}

/** Only what this release and engine made. The same record where that is all of it. */
function madeBy<Value>(
  held: Readonly<Record<string, Value>>,
  heldBy: Readonly<Record<string, Served>>,
  by: Served,
): { readonly held: Readonly<Record<string, Value>>; readonly heldBy: Readonly<Record<string, Served>> } {
  const keys = Object.keys(held);
  const kept = keys.filter((key) => sameServed(heldBy[key] ?? null, by));
  if (kept.length === keys.length) return { held, heldBy };
  return {
    held: Object.fromEntries(kept.flatMap((key) => (key in held ? [[key, held[key] as Value]] : []))),
    heldBy: Object.fromEntries(kept.flatMap((key) => (key in heldBy ? [[key, heldBy[key] as Served]] : []))),
  };
}

/**
 * What a ranking finds in hand when it comes. When the release or the engine
 * that made it is another than made the ranking before, what the other made
 * goes: facts and profiles are of the release that made them. Reasons go
 * whenever another made them, and reasons that waited for this ranking, from
 * this release, are its reasons now.
 */
function inHandFor(
  state: SearchState,
  hash: string,
  by: Served,
): Pick<
  SearchState,
  | "explanations"
  | "explainedHash"
  | "explainedBy"
  | "explanationsAhead"
  | "facts"
  | "factsBy"
  | "details"
  | "detailsBy"
> {
  const moved = !sameServed(state.rankedBy, by);
  const facts = moved ? madeBy(state.facts, state.factsBy, by) : { held: state.facts, heldBy: state.factsBy };
  const details = moved
    ? madeBy(state.details, state.detailsBy, by)
    : { held: state.details, heldBy: state.detailsBy };
  const waited = state.explanationsAhead;
  const ahead = waited !== null && waited.hash === hash && sameServed(waited.by, by) ? waited : null;
  const ours = state.explainedBy === null || sameServed(state.explainedBy, by);
  const learned = withFacts({ facts: facts.held, factsBy: facts.heldBy }, ahead?.facts ?? [], by, by);
  return {
    explanations: ahead !== null ? ahead.explanations : ours ? state.explanations : [],
    explainedHash: ahead !== null ? ahead.hash : ours ? state.explainedHash : null,
    explainedBy: ahead !== null ? ahead.by : ours ? state.explainedBy : null,
    explanationsAhead: null,
    ...learned,
    details: details.held,
    detailsBy: details.heldBy,
  };
}

function settledPhase(state: Pick<SearchState, "ranking">): "empty" | "results" {
  return state.ranking === null ? "empty" : "results";
}

function keep(state: SearchState): Kept {
  const { spec, specHash, untouched, read, refused, assumed, quoted, placeNames, gaveWay, budgetWent, degraded } =
    state;
  return { spec, specHash, untouched, read, refused, assumed, quoted, placeNames, gaveWay, budgetWent, degraded };
}

/** The vibes a spec holds, by the key of the chip each has. */
function vibesOf(spec: PreferenceSpec): ReadonlySet<string> {
  return new Set(spec.tags.map((tag) => `tag:${tag.tag_id}`));
}

/**
 * Whether the settings are open once words have or have not been read. The page opens
 * them for words it could not read. It closes them again when words are next read, if it
 * was the page that opened them and the person has not used them since: open, they stand
 * between what Burro understood and the results.
 */
function settingsAfter(
  state: Pick<SearchState, "settingsOpen" | "settingsByPage">,
  unread: boolean,
): Pick<SearchState, "settingsOpen" | "settingsByPage"> {
  if (unread) return { settingsOpen: true, settingsByPage: state.settingsOpen ? state.settingsByPage : true };
  if (state.settingsByPage) return { settingsOpen: false, settingsByPage: false };
  return { settingsOpen: state.settingsOpen, settingsByPage: false };
}

/**
 * True when something came of the words that were read: an edit, whether or not it was
 * taken, an offer or a question. The search has then read them, and they are not sent
 * again. Words of which nothing came were made no part of the search, and are still to be read.
 */
export function cameOf(data: Pick<InterpretData, "operations" | "suggestions" | "clarify">): boolean {
  return countOf(data.operations) > 0 || data.suggestions.length > 0 || data.clarify.length > 0;
}

/**
 * True when what was last read stands in the box after words the search had read before,
 * and was read without them, and words of it were not read. The person is told so: words
 * that rest on what came before them, as "by bike" does, say nothing by themselves. It is
 * so until the box changes, and is not said while a model still reads.
 */
export function readApart(state: Pick<SearchState, "read" | "box" | "phase">): boolean {
  const { read, box } = state;
  if (read === null || state.phase === "interpreting" || read.more) return false;
  if (box.shown === null || box.shown === 0) return false;
  return read.partUnread || read.status === "off_topic" || nothingCameOf(read);
}

/**
 * True when the words that were read changed the search: an edit of them did, or Burro
 * took a thing it noticed in them, which changes the search as an edit does.
 */
export function changedTheSearch(read: Pick<Read, "changed" | "took">): boolean {
  return read.changed || read.took > 0;
}

/**
 * True when nothing came of the words that were read: no edit, nothing that Burro took or
 * left, and no question. What Burro took of itself came of the words as an edit does.
 */
export function nothingCameOf(
  read: Pick<Read, "edits" | "suggestions" | "clarify" | "took" | "left">,
): boolean {
  return (
    read.edits === 0 &&
    read.suggestions.length === 0 &&
    read.clarify.length === 0 &&
    read.took === 0 &&
    read.left.length === 0
  );
}

/**
 * True when the reasons in hand are the reasons of the ranking on screen: they
 * are for the same spec, and the same release and engine made both. The hash
 * alone cannot say so, because it is of the spec alone.
 */
export function reasonsAreIn(
  state: Pick<SearchState, "ranking" | "rankedHash" | "rankedBy" | "explainedHash" | "explainedBy">,
): boolean {
  return (
    state.ranking !== null &&
    state.explainedHash !== null &&
    state.explainedHash === state.rankedHash &&
    sameServed(state.explainedBy, state.rankedBy)
  );
}

/** Why the reasons of the ranking on screen could not be loaded. `null` when they were, or were not asked for. */
export function reasonsFailure(
  state: Pick<SearchState, "ranking" | "rankedHash" | "explainFailure">,
): Failure | null {
  const { explainFailure } = state;
  if (state.ranking === null || explainFailure === null) return null;
  return explainFailure.hash === state.rankedHash ? explainFailure.failure : null;
}

/** The areas among the cards whose profile could not be loaded, in rank order. */
export function profilesFailed(state: Pick<SearchState, "ranking" | "detailFailures">): readonly string[] {
  return (state.ranking?.ranked ?? [])
    .slice(0, EXPLAINED)
    .map((area) => area.area_id)
    .filter((areaId) => areaId in state.detailFailures);
}

/**
 * The failure to say of what the cards hold, where the search itself did not
 * fail: that of the reasons, or else of the first profile that is missing.
 * One failure is shown in one place, so there is none here while the search
 * has one of its own, and none for an area that has no card.
 */
export function failureOfTheCards(
  state: Pick<SearchState, "failure" | "ranking" | "rankedHash" | "explainFailure" | "detailFailures">,
): Failure | null {
  if (state.failure !== null) return null;
  const [first] = profilesFailed(state);
  return reasonsFailure(state) ?? (first === undefined ? null : (state.detailFailures[first] ?? null));
}

/**
 * True when no search is open: nothing was read, nothing is ranked or being ranked, and
 * the spec is a default as served, or what the second way in has gathered.
 */
export function isBeforeASearch(
  state: Pick<SearchState, "phase" | "read" | "ranking" | "untouched" | "gathering">,
): boolean {
  if (state.phase !== "empty" || state.read !== null || state.ranking !== null) return false;
  return state.untouched || state.gathering;
}

/** The release and the engine to name under a result: those that made the ranking. */
export function servedTheRanking(state: Pick<SearchState, "rankedBy" | "meta">): Served {
  return state.rankedBy ?? servedBy(state.meta);
}

export function reduce(state: SearchState, event: SearchEvent): SearchState {
  switch (event.type) {
    case "tenure_swapped":
      // Nothing has been asked for yet, so the other default is swapped in as it was served.
      if (!state.untouched) return state;
      return {
        ...state,
        spec: state.meta.defaults[event.tenure],
        specHash: null,
        // The default that was swapped in is the search now, and is what "Stop" goes back to.
        kept: null,
        // The person chose it, so it is not marked as assumed.
        tenurePicked: true,
        answers: state.answers + 1,
      };

    case "queued":
      return {
        ...state,
        // What is chosen in the second way in is gathered while no search is open. Any
        // other edit makes a search, of what was gathered with it.
        gathering: event.gathers === true && isBeforeASearch(state),
        ...withEditsWaiting(state, event.operations),
      };

    case "gather_started":
      return state.failure === null ? state : { ...state, failure: null, failedStep: null };

    case "gathered": {
      // A search was made meanwhile, of a sentence or of a press: its answer is what stands.
      if (!state.gathering) return state;
      const { data } = event;
      return {
        ...state,
        spec: data.spec,
        specHash: data.spec_hash,
        answers: state.answers + 1,
        // The spec is one the API returned, as it is once a ranking is answered: renting or
        // buying is an edit from now, and swaps no default in over what was gathered.
        untouched: false,
        pending: NO_EDITS,
        refused: data.rejected.length > 0 ? { operations: event.sent, rejected: data.rejected } : null,
        placeNames: namesOf(data.places),
        failure: null,
        failedStep: null,
      };
    }

    case "read_started":
      return {
        ...state,
        gathering: false,
        phase: "interpreting",
        before: settledPhase(state),
        // A sentence sent before the last one was ranked is undone with it: what is
        // kept is the search as it was when spec and ranking last agreed.
        kept: state.kept ?? keep(state),
        seq: event.seq,
        failure: null,
        failedStep: null,
        // What is sent is all that stands in the box after what the search has read.
        box: sent(state.box, event.letters ?? 0),
      };

    case "read_answered": {
      const { data } = event;
      const applied = new Set(data.applied.map(({ group, index }) => `${group}.${index}`));
      const changed = data.applied.some((edit) => edit.changed);
      // Where something was noticed, there is something to choose from, and the settings stay shut.
      const nothingRead =
        data.status === "off_topic" ||
        (!changed && data.clarify.length === 0 && data.suggestions.length === 0);
      // An edit made while the words were read has not been answered by the reading.
      const answers = isEmpty(state.pending) ? state.answers + 1 : state.answers;
      return {
        ...state,
        spec: data.spec,
        specHash: data.spec_hash,
        answers,
        box: answered(state.box, cameOf(data), data.model_pending),
        untouched: state.untouched && !changed,
        gaveWay: changed && gaveWayBetween(state.spec, data.spec),
        budgetWent: changed && budgetWentBetween(state.spec, data.spec),
        read: {
          status: data.status,
          operations: data.operations,
          assumptions: data.assumptions,
          clarify: data.clarify,
          unmet: data.unmet,
          rejected: data.rejected,
          notice: data.notice,
          notice_text: data.notice_text,
          interpreter: data.interpreter,
          degraded: data.degraded,
          model_refused: data.model_refused,
          suggestions: data.suggestions,
          unread: data.unread,
          not_in_release: data.not_in_release,
          partUnread: data.unread.length > 0,
          edits: countOf(data.operations),
          changed,
          at: answers,
          of: state.seq,
          by: servedBy(event.meta),
          more: data.model_pending,
          chosen: [],
          things: [],
          words: [],
          took: 0,
          left: [],
        },
        refused: null,
        degraded: data.degraded,
        ...settingsAfter(state, data.degraded || nothingRead),
        assumed: withAssumptions(afterEdits(state.assumed, data.operations, applied), data),
        quoted: withQuoted(onlyOf(state.quoted, vibesOf(data.spec)), data),
        placeNames: namesOf(data.places),
        failure: null,
        failedStep: null,
      };
    }

    case "rank_started":
      return {
        ...state,
        gathering: false,
        phase: state.phase === "interpreting" ? "interpreting" : "refining",
        before: state.phase === "interpreting" ? state.before : settledPhase(state),
        seq: event.seq,
        failure: null,
        failedStep: null,
      };

    case "rank_answered": {
      const { data } = event;
      const ranking: Ranking = {
        scores: data.scores,
        ranked: data.ranked,
        filtered: data.filtered,
        unranked: data.unranked,
        empty_spec: data.empty_spec,
        areas_ranked: data.areas_ranked,
        areas_listed: data.areas_listed,
      };
      const changed = data.applied.some((edit) => edit.changed);
      const by = servedBy(event.meta);
      return {
        ...state,
        ...inHandFor(state, data.spec_hash, by),
        phase: "results",
        before: "results",
        kept: null,
        box: ranked(state.box),
        spec: data.spec,
        specHash: data.spec_hash,
        answers: state.answers + 1,
        untouched: false,
        pending: NO_EDITS,
        refused:
          data.rejected.length > 0 ? { operations: event.sent, rejected: data.rejected } : null,
        ranking,
        rankedHash: data.spec_hash,
        rankedBy: by,
        placeNames: namesOf(data.places),
        quoted: onlyOf(state.quoted, vibesOf(data.spec)),
        moved: state.ranking === null ? null : movedBetween(state.ranking, ranking),
        rankedBefore: state.ranking === null ? null : state.ranking.scores.length,
        gaveWay:
          (changed && gaveWayBetween(state.spec, data.spec)) ||
          (state.phase === "interpreting" && state.gaveWay),
        budgetWent:
          (changed && budgetWentBetween(state.spec, data.spec)) ||
          (state.phase === "interpreting" && state.budgetWent),
        failure: null,
        failedStep: null,
      };
    }

    case "share_answered": {
      // Whatever search was open gives way to the one the link holds. Nothing of
      // the search before is carried into it: not a name, not a reason, not an edit.
      const { data } = event;
      return {
        ...initialState(state.meta, state.areas, state.geometry, state.reader),
        geometryFailed: state.geometryFailed,
        online: state.online,
        // The search the link holds has read nothing of the box, whatever the box holds.
        box: begunAgain(),
        phase: "results",
        before: "results",
        seq: state.seq,
        answers: state.answers + 1,
        spec: data.spec,
        specHash: data.spec_hash,
        placeNames: namesOf(data.places),
        untouched: false,
        ranking: {
          scores: data.scores,
          ranked: data.ranked,
          filtered: data.filtered,
          unranked: data.unranked,
          empty_spec: data.empty_spec,
          areas_ranked: data.areas_ranked,
          areas_listed: data.areas_listed,
        },
        rankedHash: data.spec_hash,
        rankedBy: servedBy(event.meta),
        shared: {
          id: event.id,
          coarsened: data.coarsened,
          stale: data.stale,
          original_release_id: data.original_release_id,
        },
      };
    }

    case "explain_answered": {
      const by = servedBy(event.meta);
      const { data } = event;
      // The answer says which spec its reasons are for. The website keeps no record of its own.
      const hash = data.spec_hash;
      const learned = {
        ...withFacts(state, data.facts, by, state.rankedBy),
        // Whatever was asked for has come, so it is no longer said to have failed.
        explainFailure: state.explainFailure?.hash === hash ? null : state.explainFailure,
      };
      const ours = state.ranking !== null && hash === state.rankedHash && sameServed(by, state.rankedBy);
      // The ranking on screen has its reasons, and these are for a ranking that has not
      // come. They wait for it. If it fails, the list keeps the reasons it has.
      if (!ours && reasonsAreIn(state)) {
        return {
          ...state,
          ...learned,
          explanationsAhead: { hash, by, explanations: data.explanations, facts: data.facts },
        };
      }
      return {
        ...state,
        ...learned,
        explanations: data.explanations,
        explainedHash: hash,
        explainedBy: by,
        explanationsAhead: null,
      };
    }

    case "explain_failed":
      return {
        ...state,
        explainFailure: { hash: event.hash, failure: event.failure },
        online: event.failure.kind === "offline" ? false : state.online,
      };

    case "detail_answered": {
      const areaId = event.data.area.area_id;
      const by = servedBy(event.meta);
      return {
        ...state,
        details: { ...state.details, [areaId]: event.data },
        detailsBy: { ...state.detailsBy, [areaId]: by },
        detailFailures: areaId in state.detailFailures ? without(state.detailFailures, areaId) : state.detailFailures,
        ...withFacts(state, event.data.facts, by, state.rankedBy),
      };
    }

    case "detail_failed":
      return {
        ...state,
        detailFailures: { ...state.detailFailures, [event.areaId]: event.failure },
        online: event.failure.kind === "offline" ? false : state.online,
      };

    case "settled":
      // A reading that asked for no new ranking ends here, with what was on screen.
      return state.phase === "interpreting" || state.phase === "refining"
        ? { ...state, phase: settledPhase(state), kept: null, box: ranked(state.box) }
        : state;

    case "failed": {
      const { failure, step } = event;
      const offline = failure.kind === "offline";
      // Words that could not be read leave the settings as the way in. A
      // refusal of the words themselves is not that: the API read them. Nor is a
      // request that never reached Burro: the settings could not reach it either.
      const unread =
        step === "read" &&
        !offline &&
        !isUnreachable(failure) &&
        !(failure.kind === "api" && failure.status < 500);
      return {
        ...state,
        phase: state.before,
        // Words that were not read changed nothing, so there is nothing to put back. Words
        // that were read and then not ranked stay on screen, beside the failure that says
        // so, and what was kept stays too: a later "Stop" must not leave them there in silence.
        kept: step === "read" ? null : state.kept,
        // Words that were not read are still to be read: the search has read no further.
        box: step === "read" ? notRead(state.box) : state.box,
        failure,
        failedStep: step,
        online: offline ? false : state.online,
        degraded: state.degraded || unread,
        ...(unread ? settingsAfter(state, true) : {}),
      };
    }

    case "stopped": {
      const { kept } = state;
      if (state.phase !== "interpreting" || kept === null) return { ...state, phase: state.before };
      // The words may have been read already, and the chips drawn from them, over the
      // ranking of the search before. The search is put back as it was when the sentence
      // was sent. An edit made meanwhile still waits, and is sent with the spec put back.
      const waits = !isEmpty(state.pending);
      return {
        ...state,
        ...kept,
        assumed: waits ? afterEdits(kept.assumed, state.pending) : kept.assumed,
        phase: state.before,
        kept: null,
        // The search has read what it had read when the sentence was sent, and no more.
        box: putBack(state.box),
        // Reasons that came for the ranking that was stopped are let go with it.
        ...(reasonsAreIn(state) ? {} : { explanations: [], explainedHash: null, explainedBy: null }),
        explanationsAhead: null,
        answers: waits || state.spec === kept.spec ? state.answers : state.answers + 1,
      };
    }

    case "started_again":
      return {
        ...initialState(state.meta, state.areas, state.geometry, state.reader),
        geometryFailed: state.geometryFailed,
        online: state.online,
        answers: state.answers + 1,
        // A search that begins again has read nothing of the box, whatever the box holds.
        box: begunAgain(),
      };

    case "questions_settled": {
      const { read } = state;
      if (read === null) return state;
      const asked = event.settled.filter(({ question }) => read.clarify.some((one) => sameEdit(one, question)));
      if (asked.length === 0) return state;
      let next: Read = read;
      let assumed: Assumed = state.assumed;
      let operations = NO_EDITS;
      const marks: Mark[] = [];
      for (const { question, id, operations: edits } of asked) {
        const settled = id !== null && edits !== null;
        next = withoutQuestion(next, question, settled);
        const about = saidBy(read.operations, question.group, question.index)[0]?.key;
        if (about !== undefined) assumed = without(assumed, about);
        if (!settled) continue;
        operations = merged(operations, edits);
        if (question.group !== "commute_ops") continue;
        // What was assumed of the journey asked about is assumed of the place that was
        // taken, and so is the place itself: nobody chose it.
        const key: ChipKey = `place:${id}`;
        const codes = read.assumptions
          .filter((assumption) => sameEdit(assumption, question))
          .map((assumption) => assumption.code);
        for (const code of [...codes, "place" as const]) marks.push({ key, code });
      }
      const waiting = isEmpty(operations) ? { assumed } : withEditsWaiting({ ...state, assumed }, operations);
      return { ...state, ...waiting, assumed: withMarks(waiting.assumed, marks), read: next };
    }

    case "offers_taken": {
      const { read } = state;
      if (read === null) return state;
      const offered = (at: number) => read.suggestions[at] !== undefined;
      const taken = event.taken.filter(({ at }) => offered(at));
      const left = event.left.filter(({ at }) => offered(at));
      const went = new Set([...[...taken, ...left].map(({ at }) => at), ...(event.again ?? []).filter(offered)]);
      if (went.size === 0) return state;
      const operations = taken.reduce((all, one) => merged(all, one.operations), NO_EDITS);
      const waiting = isEmpty(operations) ? null : withEditsWaiting(state, operations);
      const marks = taken.flatMap((one) => one.marks);
      return {
        ...state,
        ...(waiting ?? {}),
        assumed: withMarks(waiting?.assumed ?? state.assumed, marks),
        read: {
          ...read,
          suggestions: read.suggestions.filter((_, at) => !went.has(at)),
          chosen: [...read.chosen, ...read.suggestions.filter((_, at) => went.has(at)).map(keyOf)],
          things: [...read.things, ...taken.map((one) => one.thing)],
          words: [...read.words, ...taken.flatMap((one) => (one.words == null ? [] : [one.words]))],
          took: read.took + taken.length,
          left: [
            ...read.left,
            ...left.flatMap(({ at, why }) => {
              const offer = read.suggestions[at];
              if (offer === undefined) return [];
              const { target, label, does, follows, note } = offer;
              return [{ target, label, does, follows, note, why }];
            }),
          ],
        },
      };
    }

    case "read_more_answered": {
      const { read } = state;
      if (read === null || !read.more) return state;
      const { data } = event;
      // What something was made of while the model read is not taken, or left, again.
      const suggestions = data.suggestions.filter((one) => !read.chosen.includes(keyOf(one)));
      return {
        ...state,
        // Where the rules made nothing of the words and the model did, they are read now.
        box: answered(state.box, cameOf(data)),
        degraded: data.degraded,
        read: {
          ...read,
          suggestions,
          unread: data.unread,
          unmet: data.unmet,
          partUnread: data.unread.length > 0,
          interpreter: data.interpreter,
          degraded: data.degraded,
          model_refused: data.model_refused,
          more: false,
        },
      };
    }

    case "read_more_failed":
      return state.read?.more
        ? { ...state, read: { ...state.read, more: false }, box: readNoMore(state.box) }
        : state;

    case "box_changed": {
      const { read } = state;
      if (read === null) return state;
      const nothing = read.suggestions.length === 0 && read.unread.length === 0 && read.words.length === 0;
      if (nothing && !read.more) return state;
      // Where the words stand is known for the text that was sent, and for no other.
      return { ...state, read: { ...read, suggestions: [], unread: [], words: [], more: false } };
    }

    case "box_edited": {
      const box = edited(state.box, event.change);
      return box === state.box ? state : { ...state, box };
    }

    case "box_found": {
      const box = found(state.box, event.holds);
      return box === state.box ? state : { ...state, box };
    }

    case "online_changed":
      return {
        ...state,
        online: event.online,
        failure: event.online && state.failure?.kind === "offline" ? null : state.failure,
        failedStep: event.online && state.failure?.kind === "offline" ? null : state.failedStep,
      };

    case "settings_opened":
      return { ...state, settingsOpen: event.open, settingsByPage: false };

    case "geometry_loaded":
      return { ...state, geometry: event.geometry, geometryFailed: false };

    case "geometry_failed":
      return state.geometry === null ? { ...state, geometryFailed: true } : state;

    case "reader_said":
      return { ...state, reader: event.reader };

    case "release_changed":
      // The form and the areas are read again. What the ranking on screen holds is of the
      // release that made the ranking, and goes when a ranking of another comes: the form
      // may come last, after the reasons and the profiles of the new release are in. The
      // form says who reads what is typed, and it was read from the service just now.
      return {
        ...state,
        meta: event.meta,
        areas: event.areas,
        reader: event.meta.reader,
      };

    case "selected":
      return { ...state, selectedId: event.areaId };

    case "hovered":
      return state.hoveredId === event.areaId ? state : { ...state, hoveredId: event.areaId };
  }
}
