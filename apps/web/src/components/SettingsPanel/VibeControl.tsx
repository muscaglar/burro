"use client";

import type { Told } from "@/content/rough";
import { NOT_IN_DATA, SHELF } from "@/content/search";
import { FEATURES } from "@/content/settings";
import type {
  FeatureWeight,
  Metric,
  Operations,
  RecipeHeld,
  ServedLimits,
  Tag,
  TagWeight,
} from "@/lib/api/schema";
import { counts } from "@/lib/search/counts";
import { edits } from "@/lib/search/edits";

import { Disclosure } from "../Disclosure/Disclosure";
import { RoughNote } from "../RoughGuide/RoughGuide";
import { WeightSlider } from "../WeightSlider/WeightSlider";
import styles from "./SettingsPanel.module.css";
import { WeightControl } from "./WeightControl";

interface Props {
  readonly tag: Tag;
  /**
   * What the release holds of the recipe. Where no area can be placed on the vibe there is
   * no slider: moved, it was turned away, and once it left no area ranked.
   */
  readonly held?: RecipeHeld;
  /** The entry in the spec, where there is one. A vibe counts when its entry is above 0. */
  readonly weight?: TagWeight;
  readonly limits: ServedLimits;
  readonly onEdit: (operations: Operations) => void;
  readonly version: number;
  readonly problem?: string | null;
  /** The id of the line that says what the scale of a slider means, where the group draws it once. */
  readonly scale?: string;
  /**
   * What the recipe counts that is recorded crime, in one line, where it counts any. To move
   * the slider of such a vibe is to ask for recorded crime, so the line stands beside it.
   */
  readonly crime?: string | null;
  /**
   * What the vibe says of itself where it is a rough guide: its label, and the sentence
   * that says why. It stands beside the slider, in sight, before the slider is moved.
   */
  readonly rough?: Told | null;
}

/** Where a vibe stands on its slider: from -1 at its low end, through 0, to 1 at its high end. */
export function standingOf(weight: TagWeight | undefined): number {
  if (weight === undefined || !counts(weight)) return 0;
  return weight.toward === "low" ? -weight.weight : weight.weight;
}

/**
 * One vibe: its name, and one slider. A scale has one slider with its two
 * ends named. It rests in the middle, which is no weight, and moves towards
 * either end. A vibe that runs one way has a slider from nothing to as much
 * as anything can count.
 *
 * Every move is one edit. At nothing the vibe is taken out of the search.
 */
export function VibeControl({
  tag,
  held,
  weight,
  limits,
  onEdit,
  version,
  problem = null,
  scale,
  crime = null,
  rough = null,
}: Props) {
  const { tag_id: tagId, label } = tag;
  const ends = tag.shape === "scale" && tag.low_end !== null && tag.high_end !== null
    ? ([tag.low_end, tag.high_end] as const)
    : undefined;
  if (held?.placed === false) {
    return (
      <div className={styles.weight} role="group" aria-label={label}>
        <p className={styles.label}>{label}</p>
        <RoughNote told={rough} />
        <p className={styles.hint}>
          {NOT_IN_DATA.why.vibe} {SHELF.held(held.held, held.needed)}
        </p>
      </div>
    );
  }
  return (
    <div className={styles.weight} role="group" aria-label={label}>
      <WeightSlider
        label={label}
        value={standingOf(weight)}
        limits={limits}
        ends={ends}
        onCommit={(value) =>
          onEdit(
            value === 0
              ? edits.tagOff(tagId)
              : edits.tagWeight(tagId, Math.abs(value), value < 0 ? "low" : "high"),
          )
        }
        version={version}
        scale={ends === undefined ? scale : undefined}
      />
      <RoughNote told={rough} />
      {crime === null ? null : <p className={styles.hint}>{crime}</p>}
      {problem ? (
        <p className={styles.problem} role="alert">
          {problem}
        </p>
      ) : null}
    </div>
  );
}

interface MadeOfProps {
  readonly tag: Tag;
  /** The features of the release. A part the release has no figure for is not among them. */
  readonly features: readonly Metric[];
  readonly weights: readonly FeatureWeight[];
  readonly limits: ServedLimits;
  readonly onEdit: (operations: Operations) => void;
  readonly version: number;
  readonly problemOf: (featureId: string) => string | null;
}

/**
 * What a vibe is made of: each part of its recipe, with the switch and the
 * slider that make that part count by itself. A part the release does not
 * carry cannot be made to count, and is said to be missing.
 */
export function MadeOf({ tag, features, weights, limits, onEdit, version, problemOf }: MadeOfProps) {
  const parts = tag.terms.flatMap((term) =>
    features.filter((metric) => metric.feature_id === term.feature_id && metric.rankable),
  );
  const missing = tag.terms.length - parts.length;
  return (
    <Disclosure label={FEATURES.madeOf} name={FEATURES.madeOfName(tag.label)} size="small">
      <p className={styles.hint}>{FEATURES.madeOfHint}</p>
      <ul className={styles.list}>
        {parts.map((metric) => (
          <li key={metric.feature_id}>
            <WeightControl
              metric={metric}
              weight={weights.find((one) => one.feature_id === metric.feature_id)}
              limits={limits}
              onEdit={onEdit}
              version={version}
              problem={problemOf(metric.feature_id)}
            />
          </li>
        ))}
      </ul>
      {/* A part the release does not carry has no name to give. It is counted, and said to be missing. */}
      {missing > 0 ? <p className={styles.hint}>{FEATURES.notInData(missing)}</p> : null}
    </Disclosure>
  );
}
