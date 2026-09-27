/**
 * The lines of a result, as it is first shown: one for each thing that was asked for, in
 * the order the search holds them, which vibes nobody asked for are drawn, and which names
 * stand in the column of names of a list. It is plain code with no state.
 *
 * A result holds a line for each thing that was asked for, and no more: a person who
 * walked the website asked for less on it, and for "title of what was asked for, the
 * visual gauge". A vibe and a measure have a gauge. A journey has the name of its place
 * and how long it takes, and a budget what a home of the kind costs, each with the word
 * that says on which side of what the person set it falls. The vibes nobody asked for, of
 * which the service gives two at the most, are in the working of the result.
 *
 * Nothing here writes a word about a place, and nothing is worked out: a band, a figure
 * and where a figure stands are a slot of a fact or a figure of the ranking. The small
 * drawing of a line is the drawing of its chip, so that a result asks the website for no
 * picture that the chips of its search did not ask for. What the
 * ranking gives of a thing, a row says as a card does. Where an area stands on a measure
 * is in the fact of the measure, which the page holds of the first results alone: so a
 * row is handed no fact, and says the same of a measure whatever another search left.
 */

import { CARD } from "@/content/card";
import { BREAKDOWN, JOURNEYS } from "@/content/search";
import type { Commute, Fact, MetaData, Metric, PreferenceSpec, RankedArea, StripMark } from "@/lib/api/schema";
import { grouped } from "@/lib/format";
import { estimateOf, withinLimit, type Facts } from "@/lib/search/card";
import { counts } from "@/lib/search/counts";
import { VIBE_BANDS } from "@/lib/vibes";

import { thingOf } from "../ChipRow/drawn";
import { namesOf } from "../Strip/column";
import type { Asked, Stands } from "../Strip/Strip";
import { A_MEASURE_RUNS, type AMeasureRuns, type FitSaid, type OthersStand } from "./look";
import { thingsLacked } from "./parts";

/** What a result draws of its area, line by line. */
export interface Lines {
  /** The marks that are drawn, in the order the service gave them: those that were asked for, and the others where they stand. */
  readonly marks: readonly StripMark[];
  /** The vibes that were asked for and could not be worked out for the area, by their ids. */
  readonly unplaced: readonly string[];
  /** What else was asked for, in the order the search holds it: each measure, each journey and the budget. */
  readonly asked: readonly Asked[];
}

/** What a result holds beside the ranking, of which its lines are drawn. */
export interface Held {
  /** The facts in hand, of a card. `null` of a row, which says what the ranking gives and no more. */
  readonly facts: Facts | null;
  /** The name of each place of the search, by place id, as the answer that brought the search gave it. */
  readonly places: ReadonlyMap<string, string>;
}

/** The calls of the look that choose which lines a result draws, and how. */
export interface Look {
  readonly others: OthersStand;
  readonly fitSaid: FitSaid;
  /** Which way the gauge of a measure runs. Left out, it is what `look.ts` chooses. */
  readonly runs?: AMeasureRuns;
}

type Area = Pick<RankedArea, "strip" | "contributions" | "legs" | "budget">;
type Form = Pick<MetaData, "features" | "tags" | "limits">;
type Search = Pick<PreferenceSpec, "weights" | "tags" | "commutes" | "budget" | "tenure">;

/** True of a measure that a person asked for: one that counts, and that is not among what Burro counts in every search. */
const isAsked = (weight: Search["weights"][number]) => weight.provenance !== "default" && counts(weight);

/** True of a search that holds a budget. A visit holds none. */
const holdsABudget = (spec: Pick<Search, "budget" | "tenure">) => spec.tenure !== "visit" && spec.budget.amount !== null;

/** True where a search asks for nothing at all: no vibe, no measure, no journey and no budget. */
export function asksNothing(spec: Search): boolean {
  return !spec.tags.some(counts) && !spec.weights.some(isAsked) && spec.commutes.length === 0 && !holdsABudget(spec);
}

const isBand = (band: number): boolean => (VIBE_BANDS as readonly number[]).includes(band);

/**
 * Where an area stands on a measure, read off the fact of the measure: the band the
 * service gives its figure among the areas it compared, and the figure and where it
 * stands in the words of the service. A fact that holds no band gives its figure, and one
 * that is not in hand gives nothing.
 *
 * The band is counted from the least figure. Where the look has a gauge run towards what
 * its name says, the gauge of a measure that can only be wished less of is turned round:
 * the step its peg stands on is as far from the high end as its band is from the low.
 */
function standingOf(fact: Fact | undefined, metric: Metric, runs: AMeasureRuns): Pick<Asked, "gauge" | "figure"> {
  if (fact === undefined || fact.kind !== "feature") return {};
  const { band, value, standing } = fact.slots;
  if (value === undefined || value === "") return {};
  const at = Number(band);
  if (band === undefined || !isBand(at)) return { figure: value };
  const step = runs === "name" && metric.polarity === "less" ? VIBE_BANDS.length + 1 - at : at;
  const gauge: Stands = {
    placed: { band: step, spread_low: step, spread_high: step },
    says: standing === undefined || standing === "" ? value : `${value}, ${standing}`,
  };
  return { gauge };
}

/** The line of each measure that was asked for, in the order the search holds them. */
function measuresOf(area: Area, meta: Form, spec: Search, facts: Facts | null, runs: AMeasureRuns): readonly Asked[] {
  return spec.weights.filter(isAsked).flatMap((weight): Asked[] => {
    const metric = meta.features.find((one) => one.feature_id === weight.feature_id);
    const part = area.contributions.find((one) => one.component === `feature:${weight.feature_id}`);
    // A measure the release does not name has no name to stand on a line, and one the ranking did not count has nothing to say.
    if (metric === undefined || part === undefined) return [];
    const line = {
      key: `measure ${metric.feature_id}`,
      name: metric.short_label,
      // It is drawn as its chip is, which stands over it on the page: one thing is drawn one way.
      thing: thingOf({ kind: "feature", id: metric.feature_id }, meta),
    } as const;
    if (!part.present) return [{ ...line, known: "none" }];
    const [first] = part.fact_ids;
    const fact = facts === null || first === undefined ? undefined : facts[first];
    return [{ ...line, known: "whole", ...standingOf(fact, metric, runs) }];
  });
}

/** What a journey to one place says: how long it takes, or where an estimate of it stands, and on which side of its limit it falls. */
function toldOf(leg: Area["legs"][number], commute: Commute, meta: Form): Pick<Asked, "known" | "figure" | "side"> {
  if (leg.status === "missing") return { known: "none" };
  if (leg.status === "estimated") {
    // No time is held of an estimate. Its band is said, in the words of the service, and that it is one.
    const band = estimateOf(leg);
    return { known: "some", ...(band === null ? {} : { figure: JOURNEYS.estimated[band] }) };
  }
  if (leg.status === "beyond_cutoff") {
    return { known: "whole", figure: JOURNEYS.beyond(meta.limits.cutoff_minutes[leg.mode]), side: CARD.side.over };
  }
  const minutes = leg.minutes ?? leg.minutes_typical;
  if (minutes === null) return { known: "whole" };
  const within = withinLimit(leg, commute);
  return {
    known: "whole",
    figure: JOURNEYS.minutes(minutes),
    ...(within === null ? {} : { side: within ? CARD.side.within : CARD.side.over }),
  };
}

/** The line of each journey of the search, by the name of its place, in the order the search holds them. */
function journeysOf(area: Area, meta: Form, spec: Search, places: Held["places"]): readonly Asked[] {
  return spec.commutes.flatMap((commute, at): Asked[] => {
    const name = places.get(commute.place_id) ?? "";
    const leg = area.legs.find((one) => one.place_id === commute.place_id && one.mode === commute.mode);
    // A place with no name has none to stand on a line, and a journey the ranking gave nothing of has nothing to say.
    if (name === "" || leg === undefined) return [];
    return [{ key: `journey ${at}`, name, thing: thingOf({ kind: "place", id: null }, meta), ...toldOf(leg, commute, meta) }];
  });
}

/**
 * The line of the budget: what a home of the kind that is looked for costs in the area,
 * and on which side of the budget that falls. The amount is what the budget was held
 * against, as the fact of it holds it where that is in hand, and else as the ranking
 * gives it: the upper end of a range. Of a price with no range the ranking gives no
 * amount, and none is worked out: the line then says the side alone.
 */
function budgetOf(area: Area, meta: Form, spec: Search, facts: Facts | null): readonly Asked[] {
  if (!holdsABudget(spec)) return [];
  const part = area.contributions.find((one) => one.component === "budget");
  if (part === undefined) return [];
  const line = { key: "budget", name: BREAKDOWN.budget, thing: thingOf({ kind: "budget", id: null }, meta) } as const;
  if (!part.present || area.budget === null) return [{ ...line, known: "none" }];
  const [first] = part.fact_ids;
  const fact = facts === null || first === undefined ? undefined : facts[first];
  const { upper, median } = fact?.kind === "budget_fit" ? fact.slots : {};
  const ranked = area.budget.upper_quartile === null ? undefined : grouped(area.budget.upper_quartile);
  const held = upper ?? median ?? ranked;
  return [
    {
      ...line,
      known: "whole",
      ...(held === undefined ? {} : { figure: CARD.cost(held, spec.tenure === "rent") }),
      side: area.budget.margin < 0 ? CARD.side.over : CARD.side.within,
    },
  ];
}

/**
 * The lines of one result. A line for each thing that was asked for: the vibes in the
 * order the service gave them, and then each measure, each journey and the budget, in the
 * order the search holds them. The vibes nobody asked for stand on a result where nothing
 * at all was asked for, so that a result is never without a line: unless the look has them
 * stand beside what was asked for, or on no result.
 *
 * What has no figure has a line only where what a fit is based on is said in the working:
 * said in full on the result, the sentence names it.
 */
export function linesOf(area: Area, meta: Form, spec: Search, held: Held, look: Look): Lines {
  const inShort = look.fitSaid === "working";
  const { vibes } = thingsLacked(area, meta, spec);
  const asked = [
    ...measuresOf(area, meta, spec, held.facts, look.runs ?? A_MEASURE_RUNS),
    ...journeysOf(area, meta, spec, held.places),
    ...budgetOf(area, meta, spec, held.facts),
  ].filter((line) => inShort || line.known !== "none");
  const others = look.others === "beside" || (look.others === "alone" && asksNothing(spec));
  return {
    marks: others ? area.strip : area.strip.filter((mark) => mark.asked),
    unplaced: inShort ? vibes : [],
    asked,
  };
}

/**
 * Every name that stands in the column of names of a list: of each line that a result of
 * the ranking draws, once, in the order it is first met. The column is then as wide in
 * one result as in the next, and no wider than the names that are drawn ask for.
 */
export function columnOf(ranked: readonly Area[], meta: Form, spec: Search, places: Held["places"], look: Look): readonly string[] {
  // The names of a line are of the ranking, whatever facts are in hand.
  const lines = ranked.map((area) => linesOf(area, meta, spec, { facts: null, places }, look));
  const asked = (mark: StripMark) => mark.asked;
  const unplaced = lines.flatMap((one) => one.unplaced).flatMap((id) => meta.tags.find((tag) => tag.tag_id === id)?.label ?? []);
  return [
    ...new Set([
      ...namesOf(lines.map((one) => one.marks.filter(asked)), meta.tags),
      ...unplaced,
      ...lines.flatMap((one) => one.asked.map(({ name }) => name)),
      ...namesOf(lines.map((one) => one.marks.filter((mark) => !asked(mark))), meta.tags),
    ]),
  ];
}

/**
 * The fact of each measure that was asked for and that the area has a figure for, in the
 * order the search holds them: what the line of the measure is drawn from. `undefined` of
 * one whose fact is not in hand.
 */
export function measuredBy(area: Pick<RankedArea, "contributions">, spec: Pick<PreferenceSpec, "weights">, facts: Facts): readonly (Fact | undefined)[] {
  return spec.weights.filter(isAsked).flatMap((weight) => {
    const part = area.contributions.find((one) => one.component === `feature:${weight.feature_id}`);
    if (part === undefined || !part.present) return [];
    const [first] = part.fact_ids;
    const fact = first === undefined ? undefined : facts[first];
    return [fact?.kind === "feature" ? fact : undefined];
  });
}

/**
 * True of an area that stands below every area with a figure for all that was asked for:
 * one with no figure for a vibe, a measure or a budget that was asked for, or with no time
 * for any of its journeys. The order is the service's, and nothing is sorted here. What
 * nobody chose moves no area, and nor does one journey of several that has no time.
 */
export function standsLower(area: Pick<RankedArea, "contributions">, meta: Pick<MetaData, "features" | "tags">, spec: Pick<PreferenceSpec, "weights">): boolean {
  const { vibes, others } = thingsLacked(area, meta, spec);
  return vibes.length + others.length > 0;
}
