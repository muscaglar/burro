/**
 * What a search is, while it is open: one plain object, and the one function
 * that moves it on. docs/design/web.md, section 5.3.
 *
 * It is held in memory and nowhere else. It never holds what a person typed:
 * the sentence stays in its box and in the body of one request. It holds ids
 * of the release, the spec the API last returned, and what the API answered.
 *
 * `reduce` is pure. It builds no spec: every spec in the state is one the
 * API returned, or one of the two defaults the API served.
 */

import type { Failure } from "@/lib/api/failure";
import type {
  AreaData,
  AreaSummary,
  AssumptionCode,
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
  Tenure,
} from "@/lib/api/schema";

import { addedWithOthers, keyOf, setsAFirmBudget } from "./suggestion";
import { chipOf, countOf, GROUPS, isEmpty, merged, NO_EDITS, saidBy, type ChipKey } from "./edits";

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
    // What the reader noticed and did not apply, for the person to choose from. Each holds
    // where its words stand in the text, as offsets, and never the words.
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
  /** The release and the engine that read the words. */
  readonly by: Served;
  /**
   * True while a model reads what the rules left unread. What the rules noticed is on the
   * page meanwhile: it never waits on a model.
   */
  readonly more: boolean;
  /** The offers the person has chosen of, so that one is not offered again when the model has read. */
  readonly chosen: readonly string[];
  /** What one press added, until it is taken back or the box changes. */
  readonly added: Added | null;
}

/** What "add all" added at one press, and what it takes to take it all back. */
export interface Added {
  readonly count: number;
  /** What is left for the person, each in the API's words. */
  readonly needs: readonly string[];
  /** True where a budget that is a firm limit was among what it added. It leaves areas out. */
  readonly firm: boolean;
  /**
   * The search as it stood before the press, and what is offered once it is all taken back:
   * what was offered at the press, or what a model has offered since.
   */
  readonly spec: PreferenceSpec;
  readonly suggestions: Read["suggestions"];
  /** What the person had chosen of, each by its own button, before the press. */
  readonly chosen: readonly string[];
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
export type Assumed = Readonly<Record<string, readonly AssumptionCode[]>>;

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
  readonly meta: MetaData;
  readonly areas: readonly AreaSummary[];
  readonly geometry: GeometryData | null;
  readonly geometryFailed: boolean;
  /**
   * Who reads what is typed, as the service says now. `null` until it has said: what the
   * page was built on may be of a service that was set otherwise, so it is never shown in
   * its place. No sentence is sent while this is `null`.
   */
  readonly reader: Reader | null;
  /** True when the service was asked who reads and could not say. */
  readonly readerFailed: boolean;

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
}

export type SearchEvent =
  | { readonly type: "tenure_swapped"; readonly tenure: Tenure }
  | { readonly type: "queued"; readonly operations: Operations }
  | { readonly type: "read_started"; readonly seq: number }
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
  | { readonly type: "question_answered"; readonly question: Clarify; readonly id: string }
  | { readonly type: "question_left"; readonly question: Clarify }
  // A suggestion goes when the person has chosen of it, whatever they chose. `changes` is
  // true where the choice holds edits, which change the search. Leaving a thing out holds none.
  | { readonly type: "suggestion_chosen"; readonly at: number; readonly changes?: boolean }
  // A model has read what the rules left unread. What it read joins what is offered.
  | { readonly type: "read_more_answered"; readonly data: InterpretData }
  // It could not be asked, did not answer, or was stopped. What the rules offered stands.
  | { readonly type: "read_more_failed" }
  // One press added several things. What it added is kept until it is taken back.
  | { readonly type: "all_added"; readonly ats: readonly number[] }
  | { readonly type: "all_taken_back" }
  // Every suggestion goes when the box changes: where its words stand is known for the text that was sent.
  | { readonly type: "box_changed" }
  | { readonly type: "online_changed"; readonly online: boolean }
  | { readonly type: "settings_opened"; readonly open: boolean }
  | { readonly type: "geometry_loaded"; readonly geometry: GeometryData }
  | { readonly type: "geometry_failed" }
  // The service said who reads what is typed, or was asked and could not.
  | { readonly type: "reader_said"; readonly reader: Reader }
  | { readonly type: "reader_unsaid" }
  | {
      readonly type: "release_changed";
      readonly meta: MetaData;
      readonly areas: readonly AreaSummary[];
    }
  | { readonly type: "selected"; readonly areaId: string | null }
  | { readonly type: "hovered"; readonly areaId: string | null };

export function initialState(
  meta: MetaData,
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
    readerFailed: false,
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
  };
}

function without<Value>(record: Readonly<Record<string, Value>>, key: string) {
  const { [key]: gone, ...rest } = record;
  void gone;
  return rest;
}

/** The assumptions that still stand after these edits have said what they say. */
function afterEdits(assumed: Assumed, operations: Operations, only?: ReadonlySet<string>): Assumed {
  let next: Record<string, readonly AssumptionCode[]> = { ...assumed };
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
const OF_A_PLACE: readonly AssumptionCode[] = ["mode", "max_minutes", "strictness"];

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
const OF_A_BUDGET: readonly AssumptionCode[] = ["segment", "strictness"];

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
  const ofTheBudget = operations.budget_ops.flatMap((edit, index) =>
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

function withAssumptions(assumed: Assumed, data: Pick<InterpretData, "operations" | "assumptions">) {
  const next: Record<string, readonly AssumptionCode[]> = { ...assumed };
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

function withoutQuestion(read: Read | null, question: Clarify): Read | null {
  if (read === null) return null;
  return {
    ...read,
    clarify: read.clarify.filter((asked) => !sameEdit(asked, question)),
    // The question stood for this refusal. With the question gone, so is it.
    rejected: read.rejected.filter((refusal) => !sameEdit(refusal, question)),
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
 * What one press added, once a model has read the words since. What is put back when it is
 * all taken back is then what the model offers, and not what the rules offered at the
 * press: its guesses and the ways it added would be lost with it. What the person chose of
 * by its own button before the press stays chosen, as it was when the press was made.
 */
function afterTheModelRead(read: Read, offered: Read["suggestions"]): Added | null {
  const { added } = read;
  if (added === null) return null;
  return { ...added, suggestions: offered.filter((one) => !added.chosen.includes(keyOf(one))) };
}

/**
 * How many areas the firm budget that one press added leaves out of the ranking on screen,
 * as the API lists them. `null` where one press added no firm budget, while the ranking
 * that follows the press is awaited, and once the budget is a firm limit no longer.
 */
export function leftOutByTheBudget(
  state: Pick<SearchState, "read" | "spec" | "ranking" | "phase">,
): number | null {
  const added = state.read?.added ?? null;
  if (added === null || !added.firm || state.ranking === null || state.phase !== "results") return null;
  if (state.spec.budget.strictness !== "hard") return null;
  return state.ranking.filtered.filter((area) => area.reason === "over_budget").length;
}

/**
 * What the API says of the rents a budget is held against, where the search is for a home
 * to rent and each rent of the release is of a postcode district or a borough. It stands
 * beside the count of the areas a firm budget left out. `null` for a buyer, and where the
 * rents of the release are of the area alone.
 */
export function rentsHeldAgainst(state: Pick<SearchState, "spec" | "meta">): string | null {
  if (state.spec.tenure !== "rent") return null;
  return state.meta.rents?.of_a_place ?? null;
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
        pending: merged(state.pending, event.operations),
        assumed: withTheKindTaken(
          withBudgetSet(
            withPlacesAdded(afterEdits(state.assumed, event.operations), event.operations),
            state.spec.budget,
            event.operations,
          ),
          event.operations,
        ),
        // The person is using the controls, so the settings are theirs to close.
        settingsByPage: false,
        // That words could not be read is said until the person does something about it:
        // they have now. What the rules read in place of a model is said until the next sentence.
        degraded: state.degraded && (state.read?.degraded ?? false),
      };

    case "read_started":
      return {
        ...state,
        phase: "interpreting",
        before: settledPhase(state),
        // A sentence sent before the last one was ranked is undone with it: what is
        // kept is the search as it was when spec and ranking last agreed.
        kept: state.kept ?? keep(state),
        seq: event.seq,
        failure: null,
        failedStep: null,
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
          by: servedBy(event.meta),
          more: data.model_pending,
          chosen: [],
          added: null,
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
        ? { ...state, phase: settledPhase(state), kept: null }
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
      };

    case "question_answered": {
      const { question, id } = event;
      const operations = state.read?.operations ?? NO_EDITS;
      // What was assumed of the journey asked about is assumed of the place chosen.
      const codes = (state.read?.assumptions ?? [])
        .filter((assumption) => sameEdit(assumption, question))
        .map((assumption) => assumption.code);
      const asked = saidBy(operations, question.group, question.index)[0]?.key;
      const key: ChipKey = question.group === "area_ops" ? `area:${id}` : `place:${id}`;
      let assumed: Record<string, readonly AssumptionCode[]> = { ...state.assumed };
      if (asked !== undefined) assumed = without(assumed, asked);
      if (codes.length > 0 && question.group === "commute_ops") assumed[key] = codes;
      return { ...state, read: withoutQuestion(state.read, question), assumed };
    }

    case "question_left":
      return { ...state, read: withoutQuestion(state.read, event.question) };

    case "suggestion_chosen": {
      const { read } = state;
      const gone = read?.suggestions[event.at];
      if (read === null || gone === undefined) return state;
      const suggestions = read.suggestions.filter((_, at) => at !== event.at);
      const chosen = [...read.chosen, keyOf(gone)];
      if (event.changes !== true) return { ...state, read: { ...read, suggestions, chosen } };
      // The notice was written of the words as they were read, and may end "Nothing you
      // typed has changed your search". A choice that holds edits changes it. The notice is
      // the API's, and is never cut or reworded, so it goes whole.
      return { ...state, read: { ...read, suggestions, chosen, notice: "none", notice_text: "" } };
    }

    case "read_more_answered": {
      const { read } = state;
      if (read === null || !read.more) return state;
      const { data } = event;
      // What the person chose of while the model read is not offered again.
      const suggestions = data.suggestions.filter((one) => !read.chosen.includes(keyOf(one)));
      return {
        ...state,
        degraded: data.degraded,
        read: {
          ...read,
          suggestions,
          added: afterTheModelRead(read, data.suggestions),
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
      return state.read?.more ? { ...state, read: { ...state.read, more: false } } : state;

    case "all_added": {
      const { read } = state;
      if (read === null) return state;
      const taken = new Set(event.ats);
      const added = read.suggestions.filter((_, at) => taken.has(at));
      if (added.length === 0) return state;
      const left = read.suggestions.filter((_, at) => !taken.has(at));
      return {
        ...state,
        read: {
          ...read,
          suggestions: left,
          chosen: [...read.chosen, ...added.map(keyOf)],
          notice: "none",
          notice_text: "",
          added: {
            count: added.length,
            // What is left for the person: of what was added, and of what was not.
            needs: [...added, ...left].map((one) => one.needs).filter((needs) => needs !== ""),
            firm: added.some((one) => setsAFirmBudget(addedWithOthers(one)?.operations ?? NO_EDITS)),
            spec: state.spec,
            suggestions: read.suggestions,
            chosen: read.chosen,
          },
        },
      };
    }

    case "all_taken_back": {
      const { read } = state;
      if (read === null || read.added === null) return state;
      return {
        ...state,
        read: {
          ...read,
          suggestions: read.added.suggestions,
          chosen: read.added.chosen,
          added: null,
        },
      };
    }

    case "box_changed": {
      const { read } = state;
      if (read === null) return state;
      const nothing = read.suggestions.length === 0 && read.unread.length === 0;
      if (nothing && !read.more && read.added === null) return state;
      // Where the words stand is known for the text that was sent, and for no other.
      return { ...state, read: { ...read, suggestions: [], unread: [], more: false, added: null } };
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
      return { ...state, reader: event.reader, readerFailed: false };

    case "reader_unsaid":
      // What the service said before still stands until it says otherwise.
      return state.reader === null ? { ...state, readerFailed: true } : state;

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
        readerFailed: false,
      };

    case "selected":
      return { ...state, selectedId: event.areaId };

    case "hovered":
      return state.hoveredId === event.areaId ? state : { ...state, hoveredId: event.areaId };
  }
}
