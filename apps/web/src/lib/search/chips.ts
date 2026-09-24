/**
 * The chips: what Burro understood, one for each thing the spec holds.
 * docs/design/web.md, section 5.2.
 *
 * A chip is drawn from the spec the API returned, never from the edits. Its
 * words are names the API gave (a feature's label, a place's name) and site
 * copy for the codes. A part is marked "assumed" when nobody chose it.
 */

import { CRIME_ACCOUNT, crimeParts } from "@/content/crime";
import { CHIPS, PLACE } from "@/content/search";
import { MODE, SEGMENT, TENURE } from "@/content/labels";
import type {
  AreaSummary,
  AssumptionCode,
  MetaData,
  Operations,
  PreferenceSpec,
  Provenance,
  Tag,
  TagWeight,
} from "@/lib/api/schema";
import { grouped } from "@/lib/format";

import { counts } from "./counts";
import { edits } from "./edits";
import type { Assumed } from "./state";

export type ChipKind = "tenure" | "budget" | "place" | "feature" | "tag" | "area" | "usual";

export interface ChipPart {
  readonly text: string;
  /** True when nobody chose this part: the words did not say it. */
  readonly assumed: boolean;
  /**
   * True when the part is said in the row as well as in full, though it was assumed: a
   * word that has two meanings, and the one it was read as. It is never left for a press.
   */
  readonly always?: boolean;
}

export interface Chip {
  /** Tells one chip from another. It holds an id of the release, never anything typed. */
  readonly key: string;
  readonly kind: ChipKind;
  /** The place, feature, tag or area the chip is for. `null` where there is one of its kind. */
  readonly id: string | null;
  readonly label: string;
  readonly parts: readonly ChipPart[];
  /** True when the chip as a whole was assumed, or any part of it was. */
  readonly assumed: boolean;
  /** The edit that takes it out, where it can be taken out. */
  readonly removal: Operations | null;
  /** The edit that asks for the other end of a scale, where the chip is of one. */
  readonly turn: Operations | null;
}

const notChosen = (provenance: Provenance) => provenance === "default" || provenance === "inferred";

/**
 * The name of each place of the spec, as the answer that brought the spec gave it. Every
 * answer names every place of its spec. One that did not is said to have no name here, and
 * is never given a number or a name of the website's own.
 */
export function namesOfPlaces(
  spec: PreferenceSpec,
  placeNames: Readonly<Record<string, string>>,
): ReadonlyMap<string, string> {
  return new Map(
    spec.commutes.map((commute) => [commute.place_id, placeNames[commute.place_id] ?? PLACE.noName]),
  );
}

/** The name of the end of a scale that is asked for. `null` for a vibe that runs one way. */
export function endAskedFor(tag: Pick<Tag, "shape" | "low_end" | "high_end">, toward: TagWeight["toward"]) {
  if (tag.shape !== "scale") return null;
  return (toward === "low" ? tag.low_end : tag.high_end) ?? null;
}

/** A budget as the person gave it: pounds, and "a month" for a rent. */
export function budgetText(amount: number, tenure: PreferenceSpec["tenure"]): string {
  return tenure === "rent" ? `£${grouped(amount)} a month` : `£${grouped(amount)}`;
}

/** What the page knows of the search that the spec alone does not show. */
export interface Beside {
  /**
   * True when the person picked renting or buying before anything was sent. The page then
   * shows the default the API served for that tenure, which no edit made, so the spec
   * calls the tenure a default.
   */
  readonly tenurePicked?: boolean;
  /** The word each vibe was read from, where the word has two meanings: by the key of its chip. */
  readonly quoted?: Readonly<Record<string, string>>;
}

export function chipsOf(
  spec: PreferenceSpec,
  meta: Pick<MetaData, "features" | "tags">,
  areas: readonly AreaSummary[],
  placeNames: Readonly<Record<string, string>>,
  assumed: Assumed,
  beside: Beside = {},
): Chip[] {
  const has = (key: string, code: AssumptionCode) => assumed[key]?.includes(code) ?? false;
  const chip = (
    made: Omit<Chip, "assumed" | "parts" | "turn"> & { parts?: ChipPart[]; assumed?: boolean; turn?: Operations },
  ): Chip => {
    // A code the website has no word for makes a part with nothing in it, which is left out.
    const parts = (made.parts ?? []).filter((part) => Boolean(part.text));
    return {
      ...made,
      parts,
      assumed: (made.assumed ?? false) || parts.some((part) => part.assumed),
      turn: made.turn ?? null,
    };
  };
  const chips: Chip[] = [];

  // An entry of 0 is a thing a person took off. It is said to count for nothing, so that
  // "ignore the high street" is never shown as a wish for one, and it has nothing to remove.
  const takenOff: ChipPart[] = [{ text: CHIPS.off, assumed: false }];

  // What was asked for by way of character comes first: the vibes, and then the things
  // that count nearby. They are what sets one search apart from another, and were once
  // the part that was never seen, behind a tenure nobody said, a budget and a workplace.
  for (const weight of spec.tags) {
    const key = `tag:${weight.tag_id}`;
    const tag = meta.tags.find((one) => one.tag_id === weight.tag_id);
    const end = tag === undefined ? null : endAskedFor(tag, weight.toward);
    const name = tag?.label ?? weight.tag_id;
    // A word with two meanings is quoted, with what it was read as, until the person sets the vibe.
    const word = has(key, "word") ? beside.quoted?.[key] : undefined;
    const on = counts(weight);
    // Recorded crime counts only when a person asks for it. A vibe whose recipe holds it
    // says so on its chip, in the row, so that no search counts it unseen.
    const crime = tag !== undefined && crimeParts(tag, meta.features).length > 0;
    chips.push(
      chip({
        key,
        kind: "tag",
        id: weight.tag_id,
        // A scale says which end is asked for. A vibe that runs one way is asked for, or is not.
        label: end === null || !on ? name : CHIPS.towards(name, end),
        parts: on
          ? [
              ...(crime ? [{ text: CRIME_ACCOUNT.chip, assumed: false, always: true }] : []),
              ...(word === undefined ? [] : [{ text: CHIPS.readFrom(word), assumed: true, always: true }]),
            ]
          : takenOff,
        assumed: weight.provenance === "inferred" || has(key, "weight"),
        removal: on ? edits.tagOff(weight.tag_id) : null,
        ...(on && end !== null
          ? { turn: edits.tagWeight(weight.tag_id, weight.weight, weight.toward === "low" ? "high" : "low") }
          : {}),
      }),
    );
  }

  for (const weight of spec.weights) {
    if (weight.provenance === "default") continue;
    const metric = meta.features.find((feature) => feature.feature_id === weight.feature_id);
    const key = `feature:${weight.feature_id}`;
    const direction: ChipPart[] =
      metric?.polarity === "either"
        ? [
            {
              text: weight.direction === "more" ? CHIPS.more : CHIPS.fewer,
              assumed: has(key, "direction"),
            },
          ]
        : [];
    chips.push(
      chip({
        key,
        kind: "feature",
        id: weight.feature_id,
        // The plain name the API gives it, which says the wish where there is one way to wish.
        label: metric?.short_label ?? weight.feature_id,
        parts: counts(weight) ? direction : takenOff,
        assumed: weight.provenance === "inferred" || has(key, "weight"),
        removal: counts(weight) ? edits.featureOff(weight.feature_id) : null,
      }),
    );
  }

  // Then where the person must get to, and what they can pay.
  const names = namesOfPlaces(spec, placeNames);
  for (const commute of spec.commutes) {
    const key = `place:${commute.place_id}`;
    chips.push(
      chip({
        key,
        kind: "place",
        id: commute.place_id,
        label: names.get(commute.place_id) ?? "",
        parts: [
          { text: MODE[commute.mode], assumed: has(key, "mode") },
          { text: CHIPS.within(commute.max_minutes), assumed: has(key, "max_minutes") },
          {
            text: commute.strictness === "hard" ? CHIPS.firm : CHIPS.flexible,
            assumed: has(key, "strictness"),
          },
        ],
        removal: edits.placeRemove(commute.place_id),
      }),
    );
  }

  if (spec.budget.amount !== null) {
    chips.push(
      chip({
        key: "budget",
        kind: "budget",
        id: null,
        label: budgetText(spec.budget.amount, spec.tenure),
        parts: [
          { text: SEGMENT[spec.budget.segment], assumed: has("budget", "segment") },
          {
            text: spec.budget.strictness === "hard" ? CHIPS.firm : CHIPS.flexible,
            assumed: has("budget", "strictness"),
          },
        ],
        removal: edits.budgetClear(),
      }),
    );
  }

  for (const rule of spec.areas) {
    chips.push(
      chip({
        key: `area:${rule.area_id}`,
        kind: "area",
        id: rule.area_id,
        label: areas.find((area) => area.area_id === rule.area_id)?.name ?? rule.area_id,
        parts: [{ text: rule.rule === "exclude" ? CHIPS.hidden : CHIPS.only, assumed: false }],
        removal: edits.areaClear(rule.area_id),
      }),
    );
  }

  // Renting or buying is said of every search, and is most often what nobody said. It comes
  // after everything that was, and before the settings nobody chose, which come last.
  chips.push(
    chip({
      key: "tenure",
      kind: "tenure",
      id: null,
      label: TENURE[spec.tenure],
      assumed: beside.tenurePicked !== true && (notChosen(spec.tenure_from) || has("tenure", "tenure")),
      removal: null,
    }),
  );

  const usual = spec.weights.filter((weight) => weight.provenance === "default").length;
  if (usual > 0) {
    chips.push(
      chip({
        key: "usual",
        kind: "usual",
        id: null,
        label: CHIPS.usual(usual),
        assumed: true,
        removal: null,
      }),
    );
  }

  return chips;
}
