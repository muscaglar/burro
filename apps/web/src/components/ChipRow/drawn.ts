/**
 * What is drawn of a chip beside its words: the thing it is of, and its state. It is plain
 * code with no state of its own.
 *
 * The thing of a vibe and of a measure is chosen by the id and the family the service
 * gives, and of every other chip by its kind. No name of a vibe, a measure or a place is
 * written here, and the id of a place is handed to nothing: a drawing says nothing of where
 * a person must get to.
 */

import type { MetaData, PreferenceSpec } from "@/lib/api/schema";
import type { Chip } from "@/lib/search/chips";
import { counts } from "@/lib/search/counts";

import type { ThingOf, ThingState } from "../kit/Thing/drawn";

/**
 * How large a chip is drawn on a wide screen, where one pixel of a drawing is three of the
 * screen. `screen`: at three, as every drawing is there. `small`: at two, as on a phone,
 * which is the size the look was first drawn at and leaves the answer more of the screen.
 *
 * The answer comes first, and the height of a chip gives way to it. Measured at 1440 by
 * 900 after a plain search, beside the map as wide as it now is: drawn at three a chip was
 * 66 px high with its edge, the five chips stood in four rows of 300 px, and the first
 * result began at 899 of 900. Drawn at two a chip is 48 px with its edge, which is a main
 * control and its edge, and the five stand in three rows of 164 px.
 */
export type Art = "screen" | "small";

/** The one line that chooses between the two. */
export const ON_A_WIDE_SCREEN: Art = "small";

/** A chip as the row draws it: one of the search's own, or the one that says which journey counts. */
export type Drawn = Omit<Chip, "kind"> & { readonly kind: Chip["kind"] | "journeys" };

export function thingOf(chip: Pick<Drawn, "kind" | "id">, meta: Pick<MetaData, "tags" | "features">): ThingOf {
  switch (chip.kind) {
    case "tag":
      return { kind: "tag", id: chip.id, family: meta.tags.find((one) => one.tag_id === chip.id)?.family ?? null };
    case "feature":
      return {
        kind: "feature",
        id: chip.id,
        family: meta.features.find((one) => one.feature_id === chip.id)?.family ?? null,
      };
    // Which journey counts is said of the journeys, and is drawn as a journey is.
    case "journeys":
      return { kind: "place" };
    default:
      return { kind: chip.kind };
  }
}

/** The weight a chip stands for, where it stands for one. */
function weightOf(chip: Pick<Drawn, "kind" | "id">, spec: Pick<PreferenceSpec, "tags" | "weights">) {
  if (chip.kind === "tag") return spec.tags.find((one) => one.tag_id === chip.id);
  if (chip.kind === "feature") return spec.weights.find((one) => one.feature_id === chip.id);
  return undefined;
}

/**
 * The state a chip is in. What counts for nothing is drawn so whoever said it: that it is
 * in the search and moves no area is what a person most needs to see of it. What nobody
 * said, or not the whole of, is assumed. Each is said in the words of the chip, and every
 * chip has the same solid edge.
 */
export function stateOf(
  chip: Pick<Drawn, "kind" | "id" | "assumed">,
  spec: Pick<PreferenceSpec, "tags" | "weights">,
): ThingState {
  const weight = weightOf(chip, spec);
  if (weight !== undefined && !counts(weight)) return "off";
  return chip.assumed ? "assumed" : "said";
}
