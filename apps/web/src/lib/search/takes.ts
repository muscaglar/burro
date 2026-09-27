/**
 * What Burro takes of what it noticed, of itself, and what it says it assumed in taking it.
 *
 * The page asks nothing. Where a sentence is no plain list of wishes the service applies
 * none of it, and returns what it noticed as offers, each with the ways it may be taken.
 * The page takes every offer as soon as the reading is in, ranks, and shows the results.
 * Everything it took is a chip, which can be taken off, and what a person did not say in
 * so many words says that it was assumed.
 *
 * Which way of an offer is taken, in this order:
 *
 * 1. The way the service says one press may add (`add_all`): a wish at a mention, a budget
 *    as it was worded, a journey as a guide.
 * 2. Of a limit, the way that leaves no area out: a guide, and never a firm limit, so that
 *    no area is left out on a guess.
 * 3. The way the service marks as Burro's guess.
 * 4. Of a thing that runs one way, that way: more of what the name of the thing says.
 *
 * A rule for an area, which looks only there or leaves it out, is taken by the third of
 * these alone. Whichever way it is taken, areas are left out, so neither way is the
 * gentler, and that a way stands first or may be added at a press is no reading of the
 * words. Such an offer is told by the edits the service gives with its ways. Where it is
 * taken, its chip says that it was assumed.
 *
 * Where the words give no way, which is where the service names none and marks none, two
 * kinds of offer are left, and the page says of each in a line that it was:
 *
 * - A rule for an area.
 * - A thing that runs two ways: more or fewer, or towards either end of a scale. More of
 *   it was taken of a sentence that said neither, and may have been the wrong way round.
 *   One line has more of it taken, as it was (`WHERE_BURRO_CANNOT_TELL`).
 *
 * To skip a thing is no way of taking it, and nor is to stop counting it, but where the
 * service marks that as the way the words give: "honestly, no station" turns away a thing
 * that counts a little in every search, and it is counted no longer
 * (`WHAT_THE_WORDS_TURN_AWAY`). A journey to a place whose name several places bear is to
 * the first of them the service gives.
 *
 * Some kinds of thing wait for a person, because a promise or a decision of the product
 * has them wait or because the words do not say that the wish is the person's own, and
 * the page says once, in a line, which were left and where each can be added:
 *
 * - What counts recorded crime, unless the person asked for it by name. To type "gritty"
 *   is to ask, and to type "posh" is not, though the same vibe is offered for both. Which
 *   it was is the service's to say, of every offer (`by_name`): the page reads no word. A
 *   service that does not say has not said that the person asked, and it is left.
 * - What counts who lived somewhere, whatever the service says of it: no word applies it,
 *   its own name among them.
 * - Whatever the service says waits for a person (`only_by_choice`): the two above, as it
 *   reads them, a measure that a decision holds to be offered and never applied, and a
 *   wish or a journey that may be somebody else's.
 *
 * Which thing counts what is the service's to say, of every measure and of the recipe of
 * every vibe (route 11), and no name of one is written here.
 *
 * Nor is a journey taken to a place Burro does not know, where the data holds none with a
 * name like it.
 *
 * Words that are read more ways than one count once: of the things that are read into the
 * same words, one is taken (`OF_A_WORD_READ_SEVERAL_WAYS`).
 *
 * It is plain code with no state. Every edit it hands on is one the service gave, with
 * nothing of it changed but the place of a journey that held none. It builds no edit.
 */

import type {
  Clarify,
  ClarifyOption,
  MetaData,
  Operations,
  Suggestion,
  SuggestionChoice,
} from "@/lib/api/schema";

import { answered, type AssumedCode, type ChipKey } from "./edits";
import {
  addedWithOthers,
  guessOf,
  isAWish,
  namedByThePerson,
  waitsForAPerson,
  waysOf,
  withPlace,
} from "./suggestion";

export type { AssumedCode };

/** One thing that was assumed, of one part of the search, by the key of its chip. */
export interface Mark {
  readonly key: ChipKey;
  readonly code: AssumedCode;
}

/**
 * Why nothing was taken of an offer. `crime`: it counts recorded crime, and the service
 * does not say that the person asked for that by name. `residents`: it counts who lived
 * somewhere. `by_choice`: the service says that it waits for a person to choose it, and
 * it counts neither of those: a measure that a decision holds to be offered and never
 * applied, or a wish that the words do not say is the person's own. `journey`: it is a
 * journey that the service says waits for a person, to a place that may be somebody
 * else's. `place`: it is a journey to a place Burro does not know. `no_way`: the service
 * gave no way to take it, and says why in its own words. `area`: it is a rule for an
 * area, which leaves areas out, and the service marks no way of it as its guess.
 * `two_ways`: it runs two ways, the words give neither, and the look has such a thing
 * left out. `otherwise`: it is read into words that were taken another way, and the look
 * has such words count once. `several`: it is read into words that are read more ways
 * than one, and the look has no reading of such words taken.
 */
export type WhyLeft =
  | "crime"
  | "residents"
  | "by_choice"
  | "journey"
  | "place"
  | "no_way"
  | "area"
  | "two_ways"
  | "otherwise"
  | "several";

/** The kinds that a person alone may add: the service says of each that it waits for a person. */
export const ONLY_BY_CHOICE: readonly WhyLeft[] = ["crime", "residents", "by_choice", "journey"];

/**
 * What is made of a thing that runs two ways, where the service marks neither as its
 * guess: more pubs or fewer, towards one end of a scale or the other. It is the founder's
 * to choose.
 *
 * `left`: nothing is taken of it, and the page says in a line that Burro could not tell
 * which was meant. `more`: more of what the name of the thing says is taken, and its chip
 * says that it was assumed. A person who wrote that pubs are noisy then has more pubs
 * counted, until they turn the chip or take it off, and so has a person who asked for
 * fewer in a sentence that is no plain list: the service marks no guess there either.
 */
export type Doubt = "more" | "left";

export const DOUBTS: readonly Doubt[] = ["more", "left"];

/** This is the one line that chooses. */
export const WHERE_BURRO_CANNOT_TELL: Doubt = "left";

/**
 * What is made of a thing the words turn away, where all that the service offers of it is
 * to stop counting it, and it marks that as the way the words give: "honestly, no
 * station". Such a thing counts a little in every search until a person says otherwise,
 * and can rank an area higher and never lower. It is the founder's to choose.
 *
 * `stopped`: the thing is counted no longer, and its chip says that it is off. `left`:
 * nothing is taken of it, the thing counts as it did, and the line of what was left out
 * says in the service's words that the most Burro can do is to stop counting it.
 *
 * Where the service marks no guess, as of "I never use the station", nothing is taken
 * whichever is chosen: it could not read the turn.
 */
export type Turned = "stopped" | "left";

export const TURNED: readonly Turned[] = ["stopped", "left"];

/** This is the one line that chooses. */
export const WHAT_THE_WORDS_TURN_AWAY: Turned = "stopped";

/**
 * What is made of words that are read more ways than one. "Affluent" is read as a mix of
 * brands, as what homes sell for and as homes in the higher council tax bands, and "a
 * real identity" as a village feel, as the age of the buildings and as a town centre
 * nearby. The words name none of them. It is the founder's to choose.
 *
 * `first`: one reading of the words is taken, and its chip says that it was assumed. It
 * is the one the service marks as its guess, or else the first it gives, of those that
 * may be taken at all. The others are named in the line of what was left out, which says
 * that the words were taken another way. So a word counts once.
 *
 * `every`: each reading is taken, and its chip says that it was assumed. One word then
 * counts as many times as it has readings: a person who wrote "slightly affluent" had
 * three things ranked on.
 *
 * `none`: no reading of such words is taken, and each is named in the line of what was
 * left out, which says that the words could be read more than one way.
 */
export type Readings = "every" | "first" | "none";

export const READINGS: readonly Readings[] = ["every", "first", "none"];

/** This is the one line that chooses. */
export const OF_A_WORD_READ_SEVERAL_WAYS: Readings = "first";

/** What is made of one offer: the way that is taken, with its edits and what was assumed, or why none is. */
export type Taken =
  | {
      readonly way: SuggestionChoice;
      /** The edits of the way, as the service gave them, with the place of a journey that held none. */
      readonly operations: Operations;
      readonly marks: readonly Mark[];
    }
  | { readonly way: null; readonly why: WhyLeft };

/** What the service says of every vibe and measure: what a measure is of, and what the recipe of a vibe holds. */
type Form = Pick<MetaData, "tags" | "features">;
type Measure = Form["features"][number];

/**
 * Whether some edit sets counting a measure that the service says this of, by itself or
 * inside a vibe whose recipe holds one. To take a thing off is not to count it.
 */
function counts(operations: Operations, form: Form, says: (measure: Measure) => boolean): boolean {
  const said = (featureId: string) => form.features.some((one) => one.feature_id === featureId && says(one));
  const byAMeasure = operations.weight_ops.some((edit) => edit.action !== "remove" && said(edit.feature_id));
  const insideAVibe = operations.tag_ops.some(
    (edit) =>
      edit.action !== "remove" &&
      (form.tags.find((one) => one.tag_id === edit.tag_id)?.terms ?? []).some((term) => said(term.feature_id)),
  );
  return byAMeasure || insideAVibe;
}

/** True of a way that takes a thing off: it stops counting it, and is no way of taking it. */
function takesOff(way: SuggestionChoice): boolean {
  const { weight_ops: weights, tag_ops: tags } = way.operations;
  const wishes = [...weights, ...tags];
  return wishes.length > 0 && wishes.every((edit) => edit.action === "remove");
}

/** True of a way that sets a limit that leaves areas out: a budget or a journey, as a firm limit. */
function isFirm(way: SuggestionChoice): boolean {
  const { budget_ops: budgets, commute_ops: journeys } = way.operations;
  return [...budgets, ...journeys].some((edit) => edit.strictness === "hard");
}

/**
 * True of a way that sets a rule for an area: to look only there, or to leave it out.
 * Either leaves areas out. To show an area again leaves none out, and is no such rule.
 */
function rulesAnArea(way: SuggestionChoice): boolean {
  return way.operations.area_ops.some((edit) => edit.action !== "clear");
}

/** True of a way that sets a limit of either kind: it says whether the limit is firm. */
function setsALimit(way: SuggestionChoice): boolean {
  const { budget_ops: budgets, commute_ops: journeys } = way.operations;
  return [...budgets, ...journeys].some((edit) => edit.strictness !== "unchanged");
}

/**
 * Whether some edit sets recorded crime counting, by a measure or inside a vibe. A measure
 * of recorded crime is one the service files under crime.
 */
export function countsCrime(operations: Operations, form: Form): boolean {
  return counts(operations, form, (measure) => measure.dimension === "crime");
}

/**
 * Whether some edit sets counting who lived somewhere, by a measure or inside a vibe. Such
 * a measure is one the service says is a fact about residents.
 */
export function countsResidents(operations: Operations, form: Form): boolean {
  return counts(operations, form, (measure) => measure.describes === "residents");
}

/** The ways a thing may be taken: every choice of it but to skip it and to stop counting it. */
function takenWaysOf(suggestion: Pick<Suggestion, "choices">): readonly SuggestionChoice[] {
  return waysOf(suggestion).filter((way) => !takesOff(way));
}

/** True of a thing that runs two ways: some way of it asks for more, and some for less. */
function runsTwoWays(ways: readonly SuggestionChoice[]): boolean {
  return ways.some((way) => way.direction === "more") && ways.some((way) => way.direction === "less");
}

/** The way of an offer that is taken, before anything is asked of what it counts, or why none is. */
function wayOf(suggestion: Suggestion, doubt: Doubt, turned: Turned): SuggestionChoice | WhyLeft {
  const ways = takenWaysOf(suggestion);
  const guessed = guessOf({ choices: ways });
  // A rule for an area leaves areas out whichever way it is taken, so it is taken by the
  // way the service marks as its guess, and by no other.
  if (ways.some(rulesAnArea)) return guessed ?? "area";
  const said = addedWithOthers(suggestion);
  if (said !== null) return said;
  // The words turn the thing away, and the service reads them so.
  const stops = turned === "stopped" ? guessOf(suggestion) : null;
  if (stops !== null && takesOff(stops)) return stops;
  // A limit that may be firm or a guide is a guide, whichever the words give.
  const guide = ways.filter(setsALimit).find((way) => !isFirm(way));
  if (guide !== undefined) return guide;
  if (guessed !== null) return guessed;
  // The words give no way.
  if (doubt === "left" && runsTwoWays(ways)) return "two_ways";
  return ways.find((way) => way.direction === "more") ?? ways[0] ?? "no_way";
}

/** What was assumed in taking a way that the person did not choose, by the parts its edits are about. */
function assumedIn(way: SuggestionChoice, operations: Operations, suggestion: Suggestion): readonly Mark[] {
  // A rule for an area is taken on a guess, whatever else the service says of its way, and
  // what is taken on a guess says so.
  const rules = operations.area_ops.flatMap((edit): Mark[] =>
    edit.action === "clear" ? [] : [{ key: `area:${edit.area_id}`, code: "rule" }],
  );
  const said = addedWithOthers(suggestion);
  const guessed = guessOf(suggestion);
  // One press took it as it was said, and it is the way the words give, or the one way there is.
  if (said !== null && (guessed === null || guessed.id === said.id)) return rules;
  // One press took a way, and the words give another: what parts the two is assumed.
  const onlyTheLimit = said !== null;
  const marks: Mark[] = [...rules];
  for (const edit of operations.commute_ops) {
    // A journey that one press did not add was added by Burro, to a place that a person
    // named and did not say they must reach: the place itself was taken for them.
    if (!onlyTheLimit && edit.action === "add") marks.push({ key: `place:${edit.place_id}`, code: "place" });
    if (edit.strictness !== "unchanged") marks.push({ key: `place:${edit.place_id}`, code: "strictness" });
  }
  for (const edit of operations.budget_ops) {
    if (edit.strictness !== "unchanged") marks.push({ key: "budget", code: "strictness" });
    if (!onlyTheLimit && edit.tenure !== "unchanged") marks.push({ key: "tenure", code: "tenure" });
  }
  if (onlyTheLimit) return marks;
  // The person named the thing, and the way taken is the way their words give: it is what
  // they said. The service names no way of what counts recorded crime for one press, so
  // such a thing would say that it was assumed where a thing beside it, asked for in the
  // same breath, does not.
  if (namedByThePerson(suggestion) && guessed?.id === way.id) return marks;
  // A measure that runs two ways says which way was taken, and that way was assumed too.
  const twoWays = runsTwoWays(takenWaysOf(suggestion));
  for (const edit of operations.weight_ops) {
    marks.push({ key: `feature:${edit.feature_id}`, code: "weight" });
    if (twoWays && edit.direction !== "default") marks.push({ key: `feature:${edit.feature_id}`, code: "direction" });
  }
  for (const edit of operations.tag_ops) marks.push({ key: `tag:${edit.tag_id}`, code: "weight" });
  return marks;
}

/**
 * Why an offer that the service says waits for a person does: by what its ways would set
 * counting, where that is one of the two the page has an account of, and by whether they
 * would rule an area or add a journey, which count no measure and are each said of in
 * words of their own.
 */
function whyItWaits(suggestion: Suggestion, form: Form): WhyLeft {
  const ways = takenWaysOf(suggestion);
  if (ways.some((way) => countsResidents(way.operations, form))) return "residents";
  if (ways.some((way) => countsCrime(way.operations, form))) return "crime";
  if (ways.some(rulesAnArea)) return "area";
  return ways.some((way) => way.operations.commute_ops.length > 0) ? "journey" : "by_choice";
}

/**
 * What is made of one offer. The way that is taken is one the service gave, and its edits
 * are the service's: the page chooses among them, and changes none.
 */
export function takenOf(
  suggestion: Suggestion,
  form: Form,
  doubt: Doubt = WHERE_BURRO_CANNOT_TELL,
  turned: Turned = WHAT_THE_WORDS_TURN_AWAY,
): Taken {
  // What waits for a person is taken by no way, and says which kind of thing it is: not
  // that Burro could not tell which way was meant, where it runs two.
  if (waitsForAPerson(suggestion)) return { way: null, why: whyItWaits(suggestion, form) };
  const way = wayOf(suggestion, doubt, turned);
  if (typeof way === "string") return { way: null, why: way };
  // Whatever the service says of it or of its ways: never for a person.
  if (countsResidents(way.operations, form)) return { way: null, why: "residents" };
  // Only where the service says that the person asked for it by name.
  if (countsCrime(way.operations, form) && !namedByThePerson(suggestion)) return { way: null, why: "crime" };
  if (!suggestion.asks_place) {
    return { way, operations: way.operations, marks: assumedIn(way, way.operations, suggestion) };
  }
  // A journey whose place Burro does not know: the first the data holds with a name like it.
  const [first] = suggestion.options;
  if (first === undefined) return { way: null, why: "place" };
  const operations = withPlace(way.operations, first.id);
  const place: Mark = { key: `place:${first.id}`, code: "place" };
  const others = assumedIn(way, operations, suggestion).filter(
    (mark) => mark.key !== place.key || mark.code !== place.code,
  );
  return { way, operations, marks: [place, ...others] };
}

/** The words an offer rests on, by where they stand: two offers that rest on the same words say the same. */
export const restsOn = (suggestion: Pick<Suggestion, "spans">): string =>
  suggestion.spans.map((span) => `${span.start}-${span.end}`).join(" ");

/** A wish that is read into its words: it is of a measure or a vibe, and the service does not say that the words name it. */
const isReadIn = (offer: Suggestion) => offer.spans.length > 0 && isAWish(offer) && !namedByThePerson(offer);

/**
 * Which offers of one answer are readings of words that are read more ways than one, each
 * by where it stands among them, with the words it rests on. Such an offer is a wish that
 * the person's own words do not name, and another wish rests on the very same words: one
 * that is read into them too, or one that they name. What the words name is what the
 * person asked for, and is no reading of them. What is said of a home, a journey or an
 * area is no wish: several of them may rest on the same words and each be meant. No word
 * and no thing is named here.
 */
export function readSeveralWays(suggestions: readonly Suggestion[]): ReadonlyMap<number, string> {
  const found = new Map<number, string>();
  suggestions.forEach((offer, at) => {
    if (!isReadIn(offer)) return;
    const words = restsOn(offer);
    const shares = suggestions.some((other, where) => where !== at && isAWish(other) && restsOn(other) === words);
    if (shares) found.set(at, words);
  });
  return found;
}

/**
 * What is made of every offer of one answer, in the order they were noticed. Each is
 * taken as it is by itself, but a wish that is read into words that are taken another
 * way, where the look has such words count once or not at all.
 *
 * `before` holds the words of which a wish was taken already, of the same sentence, as
 * another reader read it: what is read into them now is a second reading of them.
 */
export function takenOfAll(
  suggestions: readonly Suggestion[],
  form: Form,
  doubt: Doubt = WHERE_BURRO_CANNOT_TELL,
  readings: Readings = OF_A_WORD_READ_SEVERAL_WAYS,
  before: readonly string[] = [],
  turned: Turned = WHAT_THE_WORDS_TURN_AWAY,
): readonly Taken[] {
  const made = suggestions.map((offer) => takenOf(offer, form, doubt, turned));
  if (readings === "every") return made;
  const mayBeTaken = (at: number) => made[at]?.way != null;
  const several = new Set(readSeveralWays(suggestions).values());
  /** Where the wishes that rest on some words stand: those that are read into them, or those they name. */
  const onTheWords = (words: string, readIn: boolean) =>
    suggestions.flatMap((offer, at) =>
      isAWish(offer) && restsOn(offer) === words && isReadIn(offer) === readIn ? [at] : [],
    );
  for (const words of new Set(suggestions.filter(isReadIn).map(restsOn))) {
    // The words were taken as what they name, or as another reader read them before.
    const takenAlready = before.includes(words) || onTheWords(words, false).some(mayBeTaken);
    // A wish that is the one reading of its words is taken as it is by itself.
    if (!takenAlready && !several.has(words)) continue;
    const readIn = onTheWords(words, true).filter(mayBeTaken);
    const kept =
      readings === "first" && !takenAlready
        ? (readIn.find((at) => made[at]?.way?.guess === true) ?? readIn[0])
        : undefined;
    // Each of the others says whether the words were taken another way, or no way at all.
    const why: WhyLeft = takenAlready || kept !== undefined ? "otherwise" : "several";
    for (const at of readIn) if (at !== kept) made[at] = { way: null, why };
  }
  return made;
}

/**
 * By what a thing that was taken is told from every other, whoever read it: what it is
 * of, and for a journey the place it leads to. The rules and a model may name one thing
 * in two ways, as a budget is named with its amount alone or with "a month" after it, and
 * what was taken of the one is not taken again of the other.
 */
export function thingOf(suggestion: Pick<Suggestion, "target">, operations: Operations): string {
  const places = operations.commute_ops.map((edit) => edit.place_id);
  return places.length === 0 ? suggestion.target : `${suggestion.target}:${places.join(",")}`;
}

/** What is made of a question about a place or an area: the edit asked about, with the first the service gives. */
export interface Settled {
  /** The one that was taken. `null` where the service gave none to take. */
  readonly option: ClarifyOption | null;
  /** The edit the question pointed at, with the id of what was taken in it. */
  readonly operations: Operations | null;
}

/**
 * A name that several places bear is taken as the first of them the service gives. Where
 * it gives none, nothing is taken, and the page says that Burro does not know the place.
 */
export function settledOf(operations: Operations, question: Clarify): Settled {
  const [first] = question.options;
  if (first === undefined) return { option: null, operations: null };
  const edits = answered(operations, question.group, question.index, first.id);
  return edits === null ? { option: null, operations: null } : { option: first, operations: edits };
}
