/**
 * The chips: what Burro understood, one for each thing the spec holds.
 * docs/design/web.md, section 5.2.
 *
 * A chip is drawn from the spec the API returned, never from the edits. Its
 * words are names the API gave (a feature's label, a place's name) and site
 * copy for the codes. A part is marked "assumed" when nobody chose it.
 */

import { CHIPS, PLACE } from "@/content/search";
import { MODE, SEGMENT, TENURE } from "@/content/labels";
import type {
  AreaSummary,
  AssumptionCode,
  MetaData,
  Operations,
  PreferenceSpec,
  Provenance,
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
}

const notChosen = (provenance: Provenance) => provenance === "default" || provenance === "inferred";

/** The name of each place of the spec: the one in hand, or "Place 1" in the spec's order. */
export function namesOfPlaces(
  spec: PreferenceSpec,
  placeNames: Readonly<Record<string, string>>,
): ReadonlyMap<string, string> {
  return new Map(
    spec.commutes.map((commute, at) => [
      commute.place_id,
      placeNames[commute.place_id] ?? PLACE.unnamed(at + 1),
    ]),
  );
}

/** A budget as the person gave it: pounds, and "a month" for a rent. */
export function budgetText(amount: number, tenure: PreferenceSpec["tenure"]): string {
  return tenure === "rent" ? `£${grouped(amount)} a month` : `£${grouped(amount)}`;
}

/** What the person is known to have said, which the spec alone does not show. */
export interface SaidByThePerson {
  /**
   * True when the person said whether they rent or buy. The API leaves the tenure marked a
   * default when the one that was said is the one the spec already held, so the spec
   * cannot say so (docs/design/web.md, section 13, gap 20).
   */
  readonly tenure?: boolean;
}

export function chipsOf(
  spec: PreferenceSpec,
  meta: Pick<MetaData, "features" | "tags">,
  areas: readonly AreaSummary[],
  placeNames: Readonly<Record<string, string>>,
  assumed: Assumed,
  said: SaidByThePerson = {},
): Chip[] {
  const has = (key: string, code: AssumptionCode) => assumed[key]?.includes(code) ?? false;
  const chip = (
    made: Omit<Chip, "assumed" | "parts"> & { parts?: ChipPart[]; assumed?: boolean },
  ): Chip => {
    // A code the website has no word for makes a part with nothing in it, which is left out.
    const parts = (made.parts ?? []).filter((part) => Boolean(part.text));
    return { ...made, parts, assumed: (made.assumed ?? false) || parts.some((part) => part.assumed) };
  };
  const chips: Chip[] = [];

  chips.push(
    chip({
      key: "tenure",
      kind: "tenure",
      id: null,
      label: TENURE[spec.tenure],
      assumed: said.tenure !== true && (notChosen(spec.tenure_from) || has("tenure", "tenure")),
      removal: null,
    }),
  );

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

  // An entry of 0 is a thing a person took off. It is said to count for nothing, so that
  // "ignore the high street" is never shown as a wish for one, and it has nothing to remove.
  const takenOff: ChipPart[] = [{ text: CHIPS.off, assumed: false }];

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
        label: metric?.label ?? weight.feature_id,
        parts: counts(weight) ? direction : takenOff,
        assumed: weight.provenance === "inferred" || has(key, "weight"),
        removal: counts(weight) ? edits.featureOff(weight.feature_id) : null,
      }),
    );
  }

  for (const weight of spec.tags) {
    const key = `tag:${weight.tag_id}`;
    chips.push(
      chip({
        key,
        kind: "tag",
        id: weight.tag_id,
        label: meta.tags.find((tag) => tag.tag_id === weight.tag_id)?.label ?? weight.tag_id,
        parts: counts(weight) ? [] : takenOff,
        assumed: weight.provenance === "inferred" || has(key, "weight"),
        removal: counts(weight) ? edits.tagOff(weight.tag_id) : null,
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
