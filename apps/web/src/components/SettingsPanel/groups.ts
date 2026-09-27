/**
 * The groups of the settings: which there are, what each holds that a person asked for, and
 * which stand open at first. It is plain code with no state, kept apart from the panel that
 * draws them, which runs in the browser.
 *
 * What a group holds is read from the spec the API returned. A part of a spec says who set
 * it. What nobody chose is what Burro counts in every search: a bar names it after what a
 * person asked for, so that what a fit is based on can be found, and it opens no group.
 * Every name is the API's, or site copy for a code.
 */

import { DIMENSION, SEGMENT, TENURE } from "@/content/labels";
import { HIDDEN, HOLDS, KIND_OF_SEARCH, SETTINGS } from "@/content/settings";
import { USUAL } from "@/content/usual";
import type {
  AreaSummary,
  Family,
  MetaData,
  Metric,
  PreferenceSpec,
  Provenance,
  Tag,
  Tenure,
} from "@/lib/api/schema";
import { inOrder } from "@/lib/area/profile";
import { budgetText, endAskedFor, namesOfPlaces } from "@/lib/search/chips";
import { counts } from "@/lib/search/counts";

import type { ThingOf } from "../kit/Thing/drawn";
import { ofADimension, ofAFamily } from "./drawn";
import { OPENS_AT_FIRST, type OpensAtFirst } from "./look";

/** The group of the money, of the journeys, of each family of vibes, and of each thing the API gives no family. */
export type GroupKey = "money" | "journeys" | "brands" | "apart" | "crime" | "hidden" | `family:${string}`;

/** What opens and closes in the settings: a group, and under a vibe what the vibe is made of. */
export type FoldKey = GroupKey | `made:${string}`;

export interface Group {
  /** Tells one group from another. It holds a name of the website's own or an id of the release, never anything typed. */
  readonly key: GroupKey;
  readonly label: string;
  /** The thing the group is drawn by. */
  readonly thing: ThingOf;
  /** What the bar of the group says that the group holds, in a few words. `null` where it says nothing. */
  readonly holds: string | null;
  /** True where the group holds something a person asked for, in words or with a control. */
  readonly asked: boolean;
  /** What the group holds that counts and that nobody chose, each by the name the API gives it. */
  readonly usual: readonly string[];
}

/** One family of vibes: its vibes, and its features that are in no recipe. */
export interface OfAFamily {
  readonly family: Family;
  readonly label: string;
  readonly vibes: readonly Tag[];
  readonly others: readonly Metric[];
}

/** What the settings hold of a release, by group, in the order the groups stand in. */
export interface Held {
  readonly families: readonly OfAFamily[];
  /** The mix of brands, and every chain a person may ask to be near. */
  readonly brands: readonly Metric[];
  /** The features that belong to no family of vibes, and are of no brand and no crime. */
  readonly apart: readonly Metric[];
  readonly crime: readonly Metric[];
}

/** True when the feature is recorded crime, which is a group of its own, off unless asked for. */
const isCrime = (metric: Metric) => metric.dimension === "crime";

/**
 * True when the feature is of the chains of grocers, gyms and coffee. They are a group of
 * their own: a switch for every chain would bury the family they belong to.
 */
const isBrand = (metric: Metric) => metric.dimension === "brands";

/** What a search starts from, before anybody has chosen: the page opens on it. */
const STARTS_FROM: Tenure = "rent";

/** The sign of a sum of money, which begins the unit of every figure that is one. */
const POUNDS = "£";

/**
 * True of a measurement of what homes sell for: its figures are sums of money, and the
 * API says so by their unit. No name of a measurement is written here.
 */
export const isOfAPrice = (metric: Pick<Metric, "unit">) => metric.unit.startsWith(POUNDS);

/**
 * What a search of this kind may be made of. A visit is a search for somewhere to stay: it
 * holds no budget and no kind of home, and nothing of a price is offered to it in any group.
 */
export const offeredTo = (kind: Tenure, features: readonly Metric[]): readonly Metric[] =>
  kind === "visit" ? features.filter((metric) => !isOfAPrice(metric)) : features;

/**
 * What the settings hold of a release, for a search of this kind: only what the release
 * can rank, and of that what the kind of search is offered. A family that holds nothing is
 * left out.
 */
export function heldBy(meta: Pick<MetaData, "families" | "tags" | "features">, kind: Tenure = STARTS_FROM): Held {
  const inARecipe = new Set(meta.tags.flatMap((tag) => tag.terms.map((term) => term.feature_id)));
  const rankable = offeredTo(kind, meta.features).filter((metric) => metric.rankable);
  const families = meta.families.flatMap(({ family, label }) => {
    const vibes = meta.tags.filter((tag) => tag.family === family);
    const others = rankable.filter(
      (metric) =>
        metric.family === family && !isCrime(metric) && !isBrand(metric) && !inARecipe.has(metric.feature_id),
    );
    return vibes.length === 0 && others.length === 0 ? [] : [{ family, label, vibes, others }];
  });
  return {
    families,
    brands: inOrder(rankable.filter(isBrand)),
    apart: rankable.filter((metric) => metric.family === null && !isCrime(metric) && !isBrand(metric)),
    crime: rankable.filter(isCrime),
  };
}

/** True of what a person asked for, in words or with a control: everything but what nobody chose. */
const isAsked = (provenance: Provenance) => provenance !== "default";

/** A list of names as a bar says it: the first few, and how many more there are. */
function listed(names: readonly string[]): string {
  if (names.length <= HOLDS.named) return names.join(", ");
  return `${names.slice(0, HOLDS.named).join(", ")} ${HOLDS.more(names.length - HOLDS.named)}`;
}

/** What a group holds, by name: what was asked for and counts, what counts that nobody chose, and what was taken off. */
interface Holds {
  readonly counting: readonly string[];
  readonly usual: readonly string[];
  readonly off: readonly string[];
}

/** What two lists hold, as one: the first of each comes first. */
const both = (one: Holds, other: Holds): Holds => ({
  counting: [...one.counting, ...other.counting],
  usual: [...one.usual, ...other.usual],
  off: [...one.off, ...other.off],
});

/**
 * What a bar says, as one line: what was asked for first, then what is counted in every
 * search, then what was taken off. `null` where there is none of the three.
 */
function said({ counting, usual, off }: Holds): string | null {
  const parts = [
    counting.length > 0 ? listed(counting) : null,
    usual.length > 0 ? USUAL.onTheBar(listed(usual)) : null,
    off.length > 0 ? HOLDS.off(listed(off)) : null,
  ].filter((part): part is string => part !== null);
  return parts.length === 0 ? null : parts.join(". ");
}

/** Where a thing of a search belongs on a bar, by who set it and whether it counts. `null` where it is said nowhere. */
function placeOf(weight: { readonly weight: number; readonly provenance: Provenance }): keyof Holds | null {
  if (isAsked(weight.provenance)) return counts(weight) ? "counting" : "off";
  // What nobody chose and counts for nothing is not in the search, and nothing is said of it.
  return counts(weight) ? "usual" : null;
}

/** What the search holds of these features, each by the plain name the API gives it. */
function ofFeatures(spec: PreferenceSpec, features: readonly Metric[]): Holds {
  const holds = { counting: [] as string[], usual: [] as string[], off: [] as string[] };
  for (const metric of features) {
    const weight = spec.weights.find((one) => one.feature_id === metric.feature_id);
    const place = weight === undefined ? null : placeOf(weight);
    if (place !== null) holds[place].push(metric.short_label);
  }
  return holds;
}

/** True where a family shows the feature: under one of its vibes, as a part of it, or among its other things. */
const shows = (family: OfAFamily, metric: Metric) =>
  family.others.includes(metric) ||
  family.vibes.some((tag) => tag.terms.some((term) => term.feature_id === metric.feature_id));

/**
 * The one group whose bar speaks of a feature. A part of a recipe has a switch under every
 * vibe it is a part of, which may be of three families: said on the bar of each, a wish
 * for a station would open who lives there. So it is said where a person would look for
 * it: in the group of its own kind, and else in the first group that shows it.
 */
export function homeOf(metric: Metric, held: Held): GroupKey | null {
  if (isCrime(metric)) return "crime";
  if (isBrand(metric)) return "brands";
  if (metric.family === null) return "apart";
  const own = held.families.find((family) => family.family === metric.family && shows(family, metric));
  const home = own ?? held.families.find((family) => shows(family, metric));
  return home === undefined ? null : ofFamily(home.family);
}

/**
 * What the money holds: renting or buying, and what can be paid. Where no sum is set it
 * says the kind of home in its place, if a person chose one. A bar is short: the kind of
 * home that a budget is held against is one press away, with the budget. Of a visit it
 * says that it is one, and no more: a visit holds no budget and no kind of home.
 */
function ofTheMoney(spec: PreferenceSpec): string | null {
  const { budget, tenure } = spec;
  if (tenure === "visit") return KIND_OF_SEARCH.visit;
  // A search starts from renting, so that buying is a thing somebody chose, whoever the spec says set it.
  const chosen = isAsked(spec.tenure_from) || tenure !== STARTS_FROM;
  if (budget.amount !== null) {
    return `${TENURE[tenure]}, ${HOLDS.budget(budgetText(budget.amount, tenure), budget.strictness === "hard")}`;
  }
  if (isAsked(budget.provenance)) return `${TENURE[tenure]}, ${SEGMENT[budget.segment]}`;
  return chosen ? TENURE[tenure] : null;
}

/** What the journeys hold: each place, by the name the answer gave it, and the longest journey to it. */
function ofTheJourneys(spec: PreferenceSpec, placeNames: Readonly<Record<string, string>>): string | null {
  const names = namesOfPlaces(spec, placeNames);
  const journeys = spec.commutes.map((commute) =>
    HOLDS.journey(names.get(commute.place_id) ?? "", commute.max_minutes, commute.strictness === "hard"),
  );
  return journeys.length === 0 ? null : journeys.join("; ");
}

/** What the search holds of the vibes of a family, each by the name the API gives it. A scale says which of its ends. */
function ofTheVibes(spec: PreferenceSpec, family: OfAFamily): Holds {
  const holds = { counting: [] as string[], usual: [] as string[], off: [] as string[] };
  for (const tag of family.vibes) {
    const weight = spec.tags.find((one) => one.tag_id === tag.tag_id);
    const place = weight === undefined ? null : placeOf(weight);
    if (weight === undefined || place === null) continue;
    const end = endAskedFor(tag, weight.toward);
    holds[place].push(place === "off" || end === null ? tag.label : HOLDS.towards(tag.label, end));
  }
  return holds;
}

/** The areas a person hid or kept to, by name. */
function ofTheAreas(spec: PreferenceSpec, areas: readonly AreaSummary[]): string | null {
  const names = spec.areas.map((rule) => areas.find((area) => area.area_id === rule.area_id)?.name ?? rule.area_id);
  return names.length === 0 ? null : listed(names);
}

/** The features a family shows, in the order it draws them: the parts of each of its vibes, and then its other things. */
function shownIn(family: OfAFamily, meta: Pick<MetaData, "features">, kind: Tenure): readonly Metric[] {
  const rankable = offeredTo(kind, meta.features).filter((metric) => metric.rankable);
  return [
    ...new Set([
      ...family.vibes.flatMap((tag) =>
        tag.terms.flatMap((term) => rankable.filter((metric) => metric.feature_id === term.feature_id)),
      ),
      ...family.others,
    ]),
  ];
}

/** The key of the group of a family. */
export function ofFamily(family: Family): GroupKey {
  return `family:${family}`;
}

/**
 * The groups, in the order they stand in: the money and the journeys first, then one for
 * each family of vibes, as the API names and orders them, then the brands, then what
 * belongs to no family, then recorded crime, and last the areas a person hid, while there
 * is one.
 *
 * Each is drawn by a thing of its own. A family of vibes is drawn by its family, and a
 * group that is of no family by the dimension the API gives what it holds.
 */
export function groupsOf(
  spec: PreferenceSpec,
  meta: Pick<MetaData, "families" | "tags" | "features">,
  areas: readonly AreaSummary[],
  placeNames: Readonly<Record<string, string>>,
): readonly Group[] {
  const held = heldBy(meta, spec.tenure);
  const shownBy = (family: OfAFamily) => shownIn(family, meta, spec.tenure);
  /** What the search holds of the features a group shows: of those that are said on its bar, and of no other. */
  const ofThese = (key: GroupKey, shown: readonly Metric[]) =>
    ofFeatures(
      spec,
      shown.filter((metric) => homeOf(metric, held) === key),
    );
  /** A group whose bar says one thing of it, which a person set: the money, the journeys, the areas they hid. */
  const set = (one: Pick<Group, "key" | "label" | "thing" | "holds">): Group => ({
    ...one,
    asked: one.holds !== null,
    usual: [],
  });
  /** A group of things that count, each by its name: what its bar says of them, and what of it a person asked for. */
  const counted = (one: Pick<Group, "key" | "label" | "thing">, holds: Holds): Group => ({
    ...one,
    holds: said(holds),
    asked: holds.counting.length > 0 || holds.off.length > 0,
    usual: holds.usual,
  });
  // A visit holds no budget and no kind of home, so its first group is named for what it
  // does ask, which is the kind of search: "Budget and home" stood over a group that held neither.
  const first = spec.tenure === "visit" ? KIND_OF_SEARCH.legend : SETTINGS.money;
  const groups: Group[] = [
    set({ key: "money", label: first, thing: { kind: "budget" }, holds: ofTheMoney(spec) }),
    set({ key: "journeys", label: SETTINGS.journeys, thing: { kind: "place" }, holds: ofTheJourneys(spec, placeNames) }),
    ...held.families.map((family) => {
      const key = ofFamily(family.family);
      return counted(
        { key, label: family.label, thing: ofAFamily(family.family) },
        both(ofTheVibes(spec, family), ofThese(key, shownBy(family))),
      );
    }),
  ];
  if (held.brands.length > 0) {
    groups.push(counted({ key: "brands", label: DIMENSION.brands, thing: ofADimension(held.brands) }, ofThese("brands", held.brands)));
  }
  if (held.apart.length > 0) {
    groups.push(counted({ key: "apart", label: SETTINGS.airAndNoise, thing: ofADimension(held.apart) }, ofThese("apart", held.apart)));
  }
  if (held.crime.length > 0) {
    groups.push(counted({ key: "crime", label: DIMENSION.crime, thing: ofADimension(held.crime) }, ofThese("crime", held.crime)));
  }
  if (spec.areas.length > 0) {
    groups.push(set({ key: "hidden", label: HIDDEN.legend, thing: { kind: "area" }, holds: ofTheAreas(spec, areas) }));
  }
  return groups;
}

/**
 * How much less than what was asked for is much less: a thing that nobody chose counts for
 * little beside what a person asked for where it counts for half as much, or for less.
 */
const MUCH_LESS = 2;

/**
 * What the settings say, at their head, of what Burro counts in every search that nobody
 * chose: each by the name the API gives it, in the order of the groups that hold them, and
 * how much they count beside what was asked for, where that can be said. `null` where
 * nothing counts that nobody chose.
 *
 * How much each counts is the search's own, and is read from the spec: it is of no place.
 * What was asked for is every vibe and every thing a person made count, the budget where a
 * sum is set, and the journeys where a place is named.
 */
export function saidOfTheUsual(spec: PreferenceSpec, groups: readonly Group[], begun: boolean): string | null {
  const names = groups.flatMap((group) => group.usual);
  if (names.length === 0) return null;
  if (!begun) return USUAL.before(names);
  if (!groups.some((group) => group.asked)) return USUAL.alone(names);
  const of = (weights: readonly { readonly weight: number; readonly provenance: Provenance }[], asked: boolean) =>
    weights.filter((weight) => counts(weight) && isAsked(weight.provenance) === asked).map((weight) => weight.weight);
  const usual = [...of(spec.weights, false), ...of(spec.tags, false)];
  const asked = [
    ...of(spec.weights, true),
    ...of(spec.tags, true),
    ...(spec.budget.amount === null ? [] : [spec.budget.weight]),
    ...(spec.commutes.length === 0 ? [] : [spec.commute_weight]),
  ].filter((weight) => weight > 0);
  const little = asked.length > 0 && Math.max(...usual) * MUCH_LESS <= Math.min(...asked);
  return little ? USUAL.little(names) : USUAL.also(names);
}

/** The key of what a vibe is made of, which opens under the vibe. */
export function madeOf(tag: Pick<Tag, "tag_id">): FoldKey {
  return `made:${tag.tag_id}`;
}

/** How many groups a couple is: enough to show that a group opens and closes, and few enough to leave the rest in sight. */
export const A_COUPLE = 2;

/**
 * What stands open at first. Before a search, the first two groups: it is then seen that a
 * group opens and closes. Once a search is open, none: a person has the answer before
 * them and came to change one thing, and the bar of every group says what it holds. Where
 * another way is chosen, a couple of groups, of which those that hold something the person
 * asked for come first: or every group that holds something asked for, and the first two
 * where none does.
 *
 * With them, what a vibe is made of, where the search holds a part of it by itself: what
 * is named on the bar of a group is then in sight as soon as the group is open. Of what a
 * person asked for, every vibe that holds the part. Of what Burro counts in every search,
 * which nobody chose, the vibes of the one group whose bar names it, before a search too.
 */
export function openAtFirst(
  groups: readonly Group[],
  begun: boolean,
  spec: Pick<PreferenceSpec, "weights">,
  meta: Pick<MetaData, "families" | "tags" | "features">,
  which: OpensAtFirst = OPENS_AT_FIRST,
): ReadonlySet<FoldKey> {
  const asked = begun ? groups.filter((group) => group.asked) : [];
  const rest = groups.filter((group) => !asked.includes(group));
  const standing =
    begun && which === "none"
      ? []
      : which === "all-asked" && asked.length > 0
        ? asked
        : [...asked, ...rest].slice(0, A_COUPLE);
  // In the order the groups stand in, whichever of them was found first.
  const open = new Set<FoldKey>(groups.filter((group) => standing.includes(group)).map((group) => group.key));
  const held = heldBy(meta);
  /** The parts the search holds by themselves that are said on the bar of the group a vibe stands in. */
  const saidWith = (tag: Tag, parts: ReadonlySet<string>) =>
    meta.features.some(
      (metric) =>
        parts.has(metric.feature_id) &&
        tag.terms.some((term) => term.feature_id === metric.feature_id) &&
        homeOf(metric, held) === ofFamily(tag.family),
    );
  /** What a person asked for, which they may have taken off, or what nobody chose and counts. */
  const parts = (chosen: boolean) =>
    new Set(
      spec.weights
        .filter((weight) => isAsked(weight.provenance) === chosen && (chosen || counts(weight)))
        .map((weight) => weight.feature_id),
    );
  const [chosen, usual] = [begun ? parts(true) : new Set<string>(), parts(false)];
  for (const tag of meta.tags) {
    if (tag.terms.some((term) => chosen.has(term.feature_id)) || saidWith(tag, usual)) open.add(madeOf(tag));
  }
  return open;
}

/**
 * True once a search is open: the spec is one the API returned, and no longer what a search
 * of any kind starts from.
 */
export function hasBegun(spec: PreferenceSpec, meta: Pick<MetaData, "defaults">): boolean {
  return !Object.values(meta.defaults).includes(spec);
}
