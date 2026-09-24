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
  Operations,
  OpsGroup,
  PreferenceSpec,
  RankData,
  Rejected,
  ShareData,
  Tenure,
} from "@/lib/api/schema";

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
    // Where the words each edit rests on stand in the text: offsets, and never the words.
    // They mean nothing without the text, which only the box holds.
    | "rests_on"
  > {
  /** How many edits the words were read into. */
  readonly edits: number;
  /** True when any of them changed the spec. */
  readonly changed: boolean;
  /** The count of answers when this one came, so the page can tell it is the latest. */
  readonly at: number;
  /** The release and the engine that read the words. */
  readonly by: Served;
}

export type Ranking = Pick<
  RankData,
  "scores" | "ranked" | "filtered" | "unranked" | "empty_spec"
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
  | "tenureSaid"
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

  readonly placeNames: Readonly<Record<string, string>>;
  readonly assumed: Assumed;
  /**
   * True when the person said whether they rent or buy, in words or with a control. The
   * spec alone cannot say so: said of the tenure a search starts from, it changes nothing,
   * and the API leaves the tenure marked as a default (docs/design/web.md, section 13).
   */
  readonly tenureSaid: boolean;

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
  | {
      readonly type: "explain_answered";
      readonly data: ExplanationsData;
      readonly hash: string;
      readonly meta: Meta;
    }
  | { readonly type: "explain_failed"; readonly hash: string; readonly failure: Failure }
  | { readonly type: "detail_answered"; readonly data: AreaData; readonly meta: Meta }
  | { readonly type: "detail_failed"; readonly areaId: string; readonly failure: Failure }
  | { readonly type: "settled" }
  | { readonly type: "failed"; readonly step: Step; readonly failure: Failure }
  | { readonly type: "stopped" }
  | { readonly type: "started_again" }
  | { readonly type: "question_answered"; readonly question: Clarify; readonly id: string }
  | { readonly type: "question_left"; readonly question: Clarify }
  | { readonly type: "place_named"; readonly placeId: string; readonly name: string }
  | { readonly type: "online_changed"; readonly online: boolean }
  | { readonly type: "settings_opened"; readonly open: boolean }
  | { readonly type: "geometry_loaded"; readonly geometry: GeometryData }
  | { readonly type: "geometry_failed" }
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
): SearchState {
  return {
    meta,
    areas,
    geometry,
    geometryFailed: false,
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
    tenureSaid: false,
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

/** True when any of these edits says whether the person rents or buys. */
function saysTheTenure(operations: Operations, by?: (edit: Operations["budget_ops"][number]) => boolean): boolean {
  return operations.budget_ops.some(
    (edit) => edit.action === "set" && edit.tenure !== "unchanged" && (by === undefined || by(edit)),
  );
}

/**
 * Whether the tenure is one the person said, once these words have been read. It is when
 * the words state the tenure the spec now holds. It no longer is when the tenure changed
 * and no words stated it, as when it was read into the kind of home.
 */
function tenureSaidAfter(state: Pick<SearchState, "spec" | "tenureSaid">, data: InterpretData): boolean {
  if (saysTheTenure(data.operations, (edit) => edit.provenance === "stated" && edit.tenure === data.spec.tenure)) {
    return true;
  }
  return data.spec.tenure === state.spec.tenure ? state.tenureSaid : false;
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

function namesFrom(facts: readonly Fact[], held: Readonly<Record<string, string>>) {
  let names = held;
  for (const fact of facts) {
    if (fact.kind !== "travel") continue;
    // The key of a journey's fact is the place and the mode: `syn-p0021.pt`.
    const placeId = fact.key.slice(0, fact.key.lastIndexOf("."));
    const name = fact.slots.place;
    if (placeId && name && names[placeId] !== name) names = { ...names, [placeId]: name };
  }
  return names;
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
  const { spec, specHash, untouched, read, refused, assumed, tenureSaid, gaveWay, budgetWent, degraded } = state;
  return { spec, specHash, untouched, read, refused, assumed, tenureSaid, gaveWay, budgetWent, degraded };
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
        tenureSaid: true,
        answers: state.answers + 1,
      };

    case "queued":
      return {
        ...state,
        pending: merged(state.pending, event.operations),
        assumed: withPlacesAdded(afterEdits(state.assumed, event.operations), event.operations),
        tenureSaid: state.tenureSaid || saysTheTenure(event.operations),
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
      const nothingRead =
        data.status === "off_topic" || (!changed && data.clarify.length === 0);
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
          rests_on: data.rests_on,
          edits: countOf(data.operations),
          changed,
          at: answers,
          by: servedBy(event.meta),
        },
        refused: null,
        degraded: data.degraded,
        ...settingsAfter(state, data.degraded || nothingRead),
        assumed: withAssumptions(afterEdits(state.assumed, data.operations, applied), data),
        tenureSaid: tenureSaidAfter(state, data),
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
        ...initialState(state.meta, state.areas, state.geometry),
        geometryFailed: state.geometryFailed,
        online: state.online,
        phase: "results",
        before: "results",
        seq: state.seq,
        answers: state.answers + 1,
        spec: data.spec,
        specHash: data.spec_hash,
        untouched: false,
        ranking: {
          scores: data.scores,
          ranked: data.ranked,
          filtered: data.filtered,
          unranked: data.unranked,
          empty_spec: data.empty_spec,
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
      const { data, hash } = event;
      const learned = {
        ...withFacts(state, data.facts, by, state.rankedBy),
        placeNames: namesFrom(data.facts, state.placeNames),
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
        ...initialState(state.meta, state.areas, state.geometry),
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

    case "place_named":
      return state.placeNames[event.placeId] === event.name
        ? state
        : { ...state, placeNames: { ...state.placeNames, [event.placeId]: event.name } };

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

    case "release_changed":
      // The form and the areas are read again. What the ranking on screen holds is of the
      // release that made the ranking, and goes when a ranking of another comes: the form
      // may come last, after the reasons and the profiles of the new release are in.
      return { ...state, meta: event.meta, areas: event.areas };

    case "selected":
      return { ...state, selectedId: event.areaId };

    case "hovered":
      return state.hoveredId === event.areaId ? state : { ...state, hoveredId: event.areaId };
  }
}
