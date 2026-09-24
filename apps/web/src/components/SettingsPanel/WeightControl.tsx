"use client";

import { DIRECTION, POLARITY } from "@/content/labels";
import { FEATURES } from "@/content/settings";
import type {
  Direction,
  FeatureWeight,
  Metric,
  Operations,
  ServedLimits,
  Tag,
  TagWeight,
} from "@/lib/api/schema";
import { counts } from "@/lib/search/counts";
import { useDraft } from "@/lib/search/draft";
import { edits } from "@/lib/search/edits";

import { WeightSlider } from "../WeightSlider/WeightSlider";
import { Check, Radios } from "./fields";
import styles from "./SettingsPanel.module.css";

const DIRECTIONS: readonly Direction[] = ["more", "less"];

interface Shared {
  readonly limits: ServedLimits;
  readonly onEdit: (operations: Operations) => void;
  readonly version: number;
  readonly problem?: string | null;
  /** The id of the line that says what the scale of a slider means, where the group draws it once. */
  readonly scale?: string;
}

interface WeightProps extends Shared {
  readonly metric: Metric;
  /**
   * The entry in the spec, where there is one. A feature counts when its entry is above
   * 0. One a person took off keeps an entry of 0, and is drawn as off.
   */
  readonly weight?: FeatureWeight;
}

/**
 * One feature: a switch that says whether it counts, and, while it does, how
 * much. Where more or fewer can be the better, which one. Its name is the
 * API's own label for it, which names a measure and not a wish: so under the
 * switch the form says which way counts as better, in the words Methods uses.
 */
export function WeightControl({
  metric,
  weight,
  limits,
  onEdit,
  version,
  problem = null,
  scale,
}: WeightProps) {
  const { feature_id: featureId, label } = metric;
  const [on, showOn] = useDraft(counts(weight), version);
  const [direction, showDirection] = useDraft(weight?.direction ?? "more", version);
  // The weight the person set since the last answer, which is on its way and not yet in the spec.
  const [set, showSet] = useDraft<number | null>(null, version);

  return (
    <div className={styles.weight} role="group" aria-label={label}>
      <Check
        as="switch"
        label={label}
        hint={POLARITY[metric.polarity]}
        checked={on}
        onChange={(checked) => {
          showOn(checked);
          onEdit(checked ? edits.featureOn(featureId) : edits.featureOff(featureId));
        }}
      />
      {weight !== undefined && counts(weight) && on ? (
        <div className={styles.inner}>
          <WeightSlider
            label={FEATURES.weight(label)}
            value={weight.weight}
            limits={limits}
            onCommit={(value) => {
              showSet(value);
              onEdit(edits.featureWeight(featureId, value));
            }}
            version={version}
            scale={scale}
          />
          {metric.polarity === "either" ? (
            <Radios
              legend={FEATURES.direction(label)}
              options={DIRECTIONS.map((value) => ({ value, label: DIRECTION[value] }))}
              value={direction}
              onChange={(chosen) => {
                showDirection(chosen);
                // A `set` always reads its value, and a later edit wins. So the weight sent
                // with the direction is the one just set, or it would undo the one on its way.
                onEdit(edits.featureDirection(featureId, set ?? weight.weight, chosen));
              }}
            />
          ) : null}
        </div>
      ) : null}
      {problem ? (
        <p className={styles.problem} role="alert">
          {problem}
        </p>
      ) : null}
    </div>
  );
}

interface TagProps extends Shared {
  readonly tag: Tag;
  readonly weight?: TagWeight;
}

/** One tag: a switch, and how much it counts while it is on. */
export function TagControl({ tag, weight, limits, onEdit, version, problem = null, scale }: TagProps) {
  const { tag_id: tagId, label } = tag;
  const [on, showOn] = useDraft(counts(weight), version);

  return (
    <div className={styles.weight} role="group" aria-label={label}>
      <Check
        as="switch"
        label={label}
        checked={on}
        onChange={(checked) => {
          showOn(checked);
          onEdit(checked ? edits.tagOn(tagId) : edits.tagOff(tagId));
        }}
      />
      {weight !== undefined && counts(weight) && on ? (
        <div className={styles.inner}>
          <WeightSlider
            label={FEATURES.weight(label)}
            value={weight.weight}
            limits={limits}
            onCommit={(value) => onEdit(edits.tagWeight(tagId, value))}
            version={version}
            scale={scale}
          />
        </div>
      ) : null}
      {problem ? (
        <p className={styles.problem} role="alert">
          {problem}
        </p>
      ) : null}
    </div>
  );
}
