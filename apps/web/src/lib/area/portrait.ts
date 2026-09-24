/**
 * The portrait of an area: where it sits on every vibe of the release, read
 * off what route 6 sent. docs/design/web.md, section 2.
 *
 * Which vibe stands in which list, and in what order, is the API's. So is
 * every band, every figure and every name. Nothing here works out a band or
 * writes a word about a place: it finds the fact each mark names. A mark that
 * names a vibe or a fact that is not in hand is left out, because nothing can
 * be said of it.
 */

import type { AreaData, Fact, MetaData, Metric, PortraitPart, RecipeHeld, Tag } from "@/lib/api/schema";
import { fromTheMiddle, isRange, VIBE_BANDS, type Placed } from "@/lib/vibes";

/** The lists of a portrait, in the order the page draws them. */
export const GROUPS = ["scales", "more", "less", "others", "unplaced"] as const;
export type Group = (typeof GROUPS)[number];

/** One part of a recipe, with the area's figure for it. */
export interface PartRow {
  readonly term: PortraitPart;
  /** `null` for a part this release does not carry. It has no name to give, and is never shown by its code. */
  readonly metric: Metric | null;
  /** `null` where the area has no figure for the part. Nothing is filled in. */
  readonly fact: Fact | null;
  /**
   * The name the API gives a part this release does not carry, where it gives one: what the
   * vibe waits on. `null` for a part the release carries, and where the API names none.
   */
  readonly waits: string | null;
}

/** What a portrait is read against: the vibes and the features of the release, and what it holds of each recipe. */
export type Form = Pick<MetaData, "tags" | "features"> & Partial<Pick<MetaData, "recipes">>;

/** One vibe on the portrait. */
export interface MarkRow {
  readonly tag: Tag;
  /** The fact of the vibe: its band, its ends, its date and its sources. */
  readonly fact: Fact;
  /** Where the area sits. `null` for a vibe it cannot be placed on: it is never put in the middle. */
  readonly placed: Placed | null;
  /** The figure of the heaviest part that has one, as the API chose it. */
  readonly figure: Fact | null;
  /**
   * The figure that stands beside the vibe: of its parts, one a person can picture, where
   * the recipe holds one. It is never a figure of recorded crime, which nobody asked for.
   */
  readonly pictured: Fact | null;
  readonly parts: readonly PartRow[];
  /**
   * What the release holds of the recipe, where the API says: whether any area has a band
   * for the vibe, and how much of its recipe is held. `null` where it does not say.
   */
  readonly held: RecipeHeld | null;
}

export type Portrait = Readonly<Record<Group, readonly MarkRow[]>>;

const isBand = (value: number): boolean => (VIBE_BANDS as readonly number[]).includes(value);

/**
 * Where a fact of a vibe says the area sits. `null` where it names no band,
 * as the fact of a vibe that cannot place the area does, and where what it
 * names is not a band.
 */
export function placedBy(fact: Pick<Fact, "slots">): Placed | null {
  const { band, spread_low: low, spread_high: high } = fact.slots;
  if (band === undefined || low === undefined || high === undefined) return null;
  const placed = { band: Number(band), spread_low: Number(low), spread_high: Number(high) };
  const whole = isBand(placed.band) && isBand(placed.spread_low) && isBand(placed.spread_high);
  return whole && placed.spread_low <= placed.band && placed.band <= placed.spread_high ? placed : null;
}

/**
 * The units of a figure a newcomer can picture: a walk in minutes or in metres, a count of
 * things, and a share. A count for each square kilometre is none. They are the API's own
 * words for a unit, and one it sends that is not here is taken for one that is hard to picture.
 */
export const PICTURED: ReadonlySet<string> = new Set(["min", "m", "count", "%"]);

const ofRecordedCrime = (part: PartRow): boolean =>
  part.metric?.dimension === "crime" || part.fact?.template === "feature_crime";

/** Of some parts, the one that carries most of the recipe, and of two as heavy the first. */
const heaviest = (parts: readonly PartRow[]): PartRow | null =>
  parts.reduce<PartRow | null>(
    (found, part) => (found === null || part.term.hundredths > found.term.hundredths ? part : found),
    null,
  );

/**
 * How far a part sits from the band of its vibe, in bands. A part that is read from its low
 * end is turned round first, so that band 1 of a nuisance stands with band 5 of a vibe. It
 * is `null` where the part or the vibe has no band.
 */
function apartFrom(band: number | null, part: PartRow): number | null {
  const own = Number(part.fact?.slots.band);
  if (band === null || !isBand(own)) return null;
  return Math.abs((part.term.reading === "low" ? VIBE_BANDS.length + 1 - own : own) - band);
}

/** Of some parts, those that sit nearest the band of their vibe. All of them where none can be placed. */
function nearest(band: number | null, parts: readonly PartRow[]): readonly PartRow[] {
  const placed = parts.flatMap((part) => {
    const apart = apartFrom(band, part);
    return apart === null ? [] : [{ part, apart }];
  });
  if (placed.length === 0) return parts;
  const least = Math.min(...placed.map((one) => one.apart));
  return placed.filter((one) => one.apart === least).map((one) => one.part);
}

/**
 * The figure to stand beside a vibe. Every one is a fact of a part of its recipe, as the API
 * sent it. Of the parts a person can picture, it is the one that sits nearest the band of
 * the vibe, and of two as near the heavier. A band rests on every part of its recipe, and
 * the heaviest part may sit at the other end from it: "among the most here" once stood
 * beside the one figure that said otherwise. Where no part is easy to picture, it is the one
 * the API names, which is the heaviest of all.
 */
function picturedOf(figure: Fact | null, parts: readonly PartRow[], band: number | null): Fact | null {
  const shown = parts.filter((part) => part.fact !== null && !ofRecordedCrime(part));
  const plain = heaviest(nearest(band, shown.filter((part) => PICTURED.has(part.metric?.unit ?? ""))));
  if (plain !== null) return plain.fact;
  if (figure !== null && figure.template !== "feature_crime") return figure;
  return heaviest(nearest(band, shown))?.fact ?? null;
}

/** The marks of one list of the portrait, in the order the API gave them. */
export function marksOf(data: AreaData, meta: Form, group: Group): readonly MarkRow[] {
  const factAt = (id: string | null): Fact | null =>
    id === null ? null : (data.facts.find((fact) => fact.fact_id === id) ?? null);
  return data.portrait[group].flatMap((mark) => {
    const tag = meta.tags.find((one) => one.tag_id === mark.tag_id);
    const fact = factAt(mark.fact_id);
    if (tag === undefined || fact === null) return [];
    const held = meta.recipes?.find((one) => one.tag_id === mark.tag_id) ?? null;
    const parts = mark.parts.map((term) => {
      const metric = meta.features.find((one) => one.feature_id === term.feature_id) ?? null;
      const waited = held?.waits_on.find((part) => part.feature_id === term.feature_id)?.label;
      return { term, metric, fact: factAt(term.fact_id), waits: metric === null ? (waited ?? null) : null };
    });
    const figure = factAt(mark.figure_fact_id);
    const placed = group === "unplaced" ? null : placedBy(fact);
    return [
      {
        tag,
        fact,
        placed,
        figure,
        pictured: picturedOf(figure, parts, placed?.band ?? null),
        parts,
        held,
      },
    ];
  });
}

export function portraitOf(data: AreaData, meta: Form): Portrait {
  return {
    scales: marksOf(data, meta, "scales"),
    more: marksOf(data, meta, "more"),
    less: marksOf(data, meta, "less"),
    others: marksOf(data, meta, "others"),
    unplaced: marksOf(data, meta, "unplaced"),
  };
}

/** How much of its recipe a band rests on, where that is not all of it. */
export interface RestsOn {
  /** How many parts of the recipe have a figure for the area, as the fact says it. */
  readonly known: string;
  /** How many parts the recipe holds, as the fact says it. */
  readonly parts: string;
  /** The parts with no figure for the area, by the names the API gives them. */
  readonly missing: readonly string[];
  /** The parts this data does not carry, by the names the API gives them: what the vibe waits on. */
  readonly waiting: readonly string[];
  /** How many parts this data does not carry and the API gives no name for. */
  readonly notCarried: number;
  /**
   * What the parts that have a figure carry of the recipe, of the 100 it adds up to, as the
   * fact says it. `null` where the fact does not: the website adds up no shares of its own,
   * because a sum has no source.
   */
  readonly share: string | null;
  /**
   * The API's own clause for a band that rests on part of a recipe, word for word: "Worked
   * out from 2 of its 3 parts, 75 of 100 by weight." `null` where the fact holds none.
   */
  readonly partly: string | null;
}

/** The slots of a vibe's fact that say what its band rests on (contract 7.3). */
export const SHARE_SLOT = "share";
export const PARTLY_SLOT = "partly";

const slotOf = (fact: Pick<Fact, "slots">, name: string): string | null => {
  const value = fact.slots[name];
  return value === undefined || value === "" ? null : value;
};

/**
 * What a band rests on, where the area has no figure for a part of the recipe. `null` where
 * it has one for every part, and where the fact does not say how many: nothing is worked out.
 */
export function restsOn(mark: Pick<MarkRow, "fact" | "parts">): RestsOn | null {
  const { known, parts } = mark.fact.slots;
  const without = mark.parts.filter((part) => part.fact === null);
  if (known === undefined || parts === undefined || without.length === 0) return null;
  return {
    known,
    parts,
    missing: without.flatMap((part) => (part.metric === null ? [] : [part.metric.label])),
    waiting: without.flatMap((part) => (part.metric === null && part.waits !== null ? [part.waits] : [])),
    notCarried: without.filter((part) => part.metric === null && part.waits === null).length,
    share: slotOf(mark.fact, SHARE_SLOT),
    partly: slotOf(mark.fact, PARTLY_SLOT),
  };
}

/** True of a vibe whose recipe holds a figure of recorded crime. Which one does is the API's to say. */
export function holdsRecordedCrime(tag: Pick<Tag, "terms">, features: readonly Metric[]): boolean {
  return tag.terms.some(
    (term) => features.find((metric) => metric.feature_id === term.feature_id)?.dimension === "crime",
  );
}

/** How many vibes say what an area is like, in short. */
export const IN_SHORT = 5;

/** What a line of the summary says of the area: that it has much of a thing, little of it, or sits towards an end. */
type Kind = "most" | "ends" | "least";
/** The order the kinds are read in. */
const KINDS: readonly Kind[] = ["most", "ends", "least"];
/** The order the kinds are chosen in, so that what an area has least of is never crowded out. */
const TURNS: readonly Kind[] = ["most", "least", "ends"];

function kindOf(mark: MarkRow): Kind {
  if (mark.tag.low_end !== null && mark.tag.high_end !== null) return "ends";
  return (mark.placed?.band ?? 3) > 3 ? "most" : "least";
}

/**
 * What an area is like, in five lines at most: what it has most of, where it sits between
 * two ends, and what it has least of. Every one is a vibe the API placed, in the band its
 * fact holds. The vibes furthest from the middle are chosen first, a kind at a time, so that
 * what an area has least of is said beside what it has most of. Within a kind they stand in
 * the order the portrait lists them.
 *
 * A vibe in the middle band says little, and is left to its own line. So is a mixed area,
 * which sits at no one point. A vibe whose recipe holds recorded crime is in no line of it:
 * recorded crime counts only when a person asks for it, and nobody asked for the summary.
 */
export function inShort(portrait: Portrait, features: readonly Metric[]): readonly MarkRow[] {
  const apart = shownOn(portrait)
    .filter((mark) => mark.placed !== null && !isRange(mark.placed) && fromTheMiddle(mark.placed) > 0)
    .filter((mark) => !holdsRecordedCrime(mark.tag, features));
  const chosen: MarkRow[] = [];
  for (const far of [2, 1]) {
    const waiting = TURNS.map((kind) =>
      apart.filter((mark) => kindOf(mark) === kind && mark.placed !== null && fromTheMiddle(mark.placed) === far),
    );
    while (chosen.length < IN_SHORT && waiting.some((queue) => queue.length > 0)) {
      for (const queue of waiting) {
        const next = queue.shift();
        if (next !== undefined && chosen.length < IN_SHORT) chosen.push(next);
      }
    }
  }
  return KINDS.flatMap((kind) => chosen.filter((mark) => kindOf(mark) === kind));
}

/** The vibes the portrait places the area on, in the order they are drawn. */
export function shownOn(portrait: Portrait): readonly MarkRow[] {
  return GROUPS.filter((group) => group !== "unplaced").flatMap((group) => portrait[group]);
}

/** Every fact the portrait lays out: each vibe's, and the figure of each part. */
export function factsOf(portrait: Portrait): readonly Fact[] {
  return GROUPS.flatMap((group) =>
    portrait[group].flatMap((mark) => [
      mark.fact,
      ...mark.parts.flatMap((part) => (part.fact === null ? [] : [part.fact])),
    ]),
  );
}

export interface CannotSee {
  /** What every vibe of the release says it cannot see. It is said once. */
  readonly common: readonly string[];
  /** What each vibe cannot see beyond that, in the API's words and order. */
  readonly own: readonly { readonly tag: Tag; readonly lines: readonly string[] }[];
}

/**
 * What the vibes that are shown cannot see. A line that every vibe of the
 * release says is said once, above the rest, and not again for each. Every
 * line is the API's, word for word.
 */
export function cannotSee(shown: readonly Tag[], all: readonly Tag[]): CannotSee {
  const first = all[0]?.cannot_see ?? [];
  const common =
    all.length < 2 ? [] : first.filter((line) => all.every((tag) => tag.cannot_see.includes(line)));
  return {
    common,
    own: shown.map((tag) => ({ tag, lines: tag.cannot_see.filter((line) => !common.includes(line)) })),
  };
}

/** The station the API says is the nearest, as a fact. `null` where the release holds none for the area. */
export function nearestStation(data: AreaData): Fact | null {
  return data.facts.find((fact) => fact.kind === "station" && fact.template === "station") ?? null;
}
