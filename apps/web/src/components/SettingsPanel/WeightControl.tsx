"use client";

import { useLayoutEffect, useRef } from "react";

import { DIRECTION, POLARITY } from "@/content/labels";
import { FEATURES } from "@/content/settings";
import type { Direction, FeatureWeight, Metric, Operations, ServedLimits } from "@/lib/api/schema";
import { counts } from "@/lib/search/counts";
import { useDraft } from "@/lib/search/draft";
import { edits } from "@/lib/search/edits";

import { SliderAtRest, WeightSlider } from "../WeightSlider/WeightSlider";
import { Check, Radios } from "./fields";
import { SLIDER_STANDS } from "./look";
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
 * plain name the API gives it, which says the wish where there is one way to
 * wish, and the measure where there are two. Under the switch the form says
 * which way counts as better, in the words Methods uses.
 *
 * WHAT THE SWITCH SHOWS HAS ITS ROOM WHILE THE SWITCH IS OFF. The slider, and
 * the two ways where either can count, were drawn as the switch was turned on,
 * and all that stood under them went down the page by as much: the founder,
 * "there is toomuch layout shift when toggling". So each is drawn at rest
 * while the thing is off, made as it is made while it is on and so of the same
 * size. At rest it is a drawing: it offers nothing, and says nothing to
 * whoever hears the page. Turned on, the slider stands where its drawing stood.
 *
 * In a box that is wide the slider stands beside its thing, at the far side of
 * the row, and under it in a narrow one: `look.ts` has the line that chooses.
 * It is read and reached in one order wherever it stands.
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
  const { feature_id: featureId, short_label: label } = metric;
  const [on, showOn] = useDraft(counts(weight), version);
  const [direction, showDirection] = useDraft(weight?.direction ?? "more", version);
  // The weight the person set since the last answer, which is on its way and not yet in the spec.
  const [set, showSet] = useDraft<number | null>(null, version);
  // It counts once the API says that it does. Turned off, it is at rest at once.
  const counting = weight !== undefined && counts(weight) && on;

  // What the switch shows gives way to its drawing at rest as the thing comes to count for
  // nothing, as when its own slider is brought to nought. Where the focus was on it, the
  // focus goes to the switch, which stays and says that the thing is off: it is never left
  // on nothing. Where the focus is, is asked of the page as it stands before this is drawn.
  const thing = useRef<HTMLDivElement>(null);
  const held = typeof document === "undefined" ? null : document.activeElement;
  const heldIn = held?.closest('[role="group"]') ?? null;
  const onTheSwitch = held?.matches('[role="switch"]') ?? false;
  useLayoutEffect(() => {
    if (counting || heldIn === null || heldIn !== thing.current || onTheSwitch) return;
    const now = document.activeElement;
    if (now === null || now === document.body || now.closest("[data-rests]") !== null) {
      thing.current.querySelector<HTMLElement>('[role="switch"]')?.focus({ preventScroll: true });
    }
    // It is for the drawing in which the thing came to rest, and for what had the focus then.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [counting]);

  return (
    // Where its slider stands is a line of the look, which the style sheet reads here.
    <div ref={thing} className={styles.weight} role="group" aria-label={label} data-slider={SLIDER_STANDS}>
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
      <div className={styles.inner}>
        {counting ? (
          <WeightSlider
            label={FEATURES.weight(label)}
            seen={FEATURES.howMuch}
            value={weight.weight}
            limits={limits}
            onCommit={(value) => {
              showSet(value);
              onEdit(edits.featureWeight(featureId, value));
            }}
            version={version}
            scale={scale}
          />
        ) : (
          <SliderAtRest label={FEATURES.weight(label)} seen={FEATURES.howMuch} limits={limits} scale={scale} />
        )}
        {metric.polarity === "either" ? (
          <Radios
            legend={FEATURES.direction(label)}
            seen={FEATURES.whichWay}
            options={DIRECTIONS.map((value) => ({ value, label: DIRECTION[value] }))}
            value={direction}
            reads
            rests={!counting}
            onChange={(chosen) => {
              showDirection(chosen);
              // It counts, or no way could be chosen: nothing is sent of what is at rest.
              if (!counting) return;
              // A `set` always reads its value, and a later edit wins. So the weight sent
              // with the direction is the one just set, or it would undo the one on its way.
              onEdit(edits.featureDirection(featureId, set ?? weight.weight, chosen));
            }}
          />
        ) : null}
      </div>
      {problem ? (
        <p className={styles.problem} role="alert">
          {problem}
        </p>
      ) : null}
    </div>
  );
}
