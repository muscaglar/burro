"use client";

import { useId } from "react";

import { DIMENSION, DIMENSION_ORDER } from "@/content/labels";
import { REJECTED } from "@/content/search";
import { CRIME, CRIME_CAVEAT, FEATURES, HIDDEN, JOURNEY, SETTINGS, SLIDER } from "@/content/settings";
import type {
  AreaSummary,
  Dimension,
  MetaData,
  Operations,
  PreferenceSpec,
  RejectReason,
} from "@/lib/api/schema";
import { namesOfPlaces } from "@/lib/search/chips";
import { counts } from "@/lib/search/counts";
import { edits } from "@/lib/search/edits";

import { Disclosure } from "../Disclosure/Disclosure";
import { BudgetControl } from "./BudgetControl";
import { CommuteControl, JourneySettings } from "./CommuteControl";
import styles from "./SettingsPanel.module.css";
import { TagControl, WeightControl } from "./WeightControl";

interface Props {
  /** The spec the API last returned. Every control is drawn from it. */
  readonly spec: PreferenceSpec;
  readonly meta: MetaData;
  readonly areas: readonly AreaSummary[];
  readonly placeNames: Readonly<Record<string, string>>;
  readonly onEdit: (operations: Operations) => void;
  /** Changes with every answer from the API. */
  readonly version: number;
  /** Why the last edit to a part was not taken, by part. */
  readonly refused?: ReadonlyMap<string, RejectReason>;
  readonly open: boolean;
  readonly onToggle: (open: boolean) => void;
  /** Ranks the settings as they stand. Left out once there is a ranking. */
  readonly onRank?: () => void;
  readonly busy?: boolean;
}

/**
 * The settings: the same search as a form. Every control here makes the edit
 * a sentence would, so the page works with no words read at all.
 *
 * It offers only what the release can rank, within the limits the API
 * served, so it never offers what the reducer would refuse.
 */
export function SettingsPanel({
  spec,
  meta,
  areas,
  placeNames,
  onEdit,
  version,
  refused = new Map(),
  open,
  onToggle,
  onRank,
  busy = false,
}: Props) {
  const id = useId();
  const { limits } = meta;
  const names = namesOfPlaces(spec, placeNames);
  const why = (part: string) => {
    const reason = refused.get(part);
    return reason === undefined ? null : REJECTED[reason];
  };
  const shared = { limits, onEdit, version };

  // What the scale of a slider means is said once for each group of sliders, where it can be
  // seen, and only while the group shows a slider: a switch that is off shows none.
  const scales = { features: `${id}-scale-features`, tags: `${id}-scale-tags`, crime: `${id}-scale-crime` };
  const isCrime = (featureId: string) =>
    meta.features.some((metric) => metric.feature_id === featureId && metric.dimension === "crime");
  const slides = {
    features: spec.weights.some((weight) => counts(weight) && !isCrime(weight.feature_id)),
    tags: spec.tags.some((weight) => counts(weight)),
    crime: spec.weights.some((weight) => counts(weight) && isCrime(weight.feature_id)),
  };
  const scaleOf = (group: keyof typeof scales) =>
    slides[group] ? (
      <p id={scales[group]} className={styles.hint}>
        {SLIDER.range}
      </p>
    ) : null;

  const featuresOf = (dimension: Dimension) =>
    meta.features
      .filter((metric) => metric.rankable && metric.dimension === dimension)
      .map((metric) => (
        <li key={metric.feature_id}>
          <WeightControl
            {...shared}
            metric={metric}
            weight={spec.weights.find((weight) => weight.feature_id === metric.feature_id)}
            problem={why(`feature:${metric.feature_id}`)}
            scale={scales[dimension === "crime" ? "crime" : "features"]}
          />
        </li>
      ));

  return (
    <Disclosure
      label={SETTINGS.title}
      open={open}
      onToggle={onToggle}
      className={styles.settings}
    >
      <div className={styles.panel} aria-busy={busy}>
        <p className={styles.lead}>{SETTINGS.lead}</p>

        <BudgetControl
          {...shared}
          budget={spec.budget}
          tenure={spec.tenure}
          problem={why("budget")}
        />

        <fieldset className={styles.group}>
          <legend className={styles.groupLegend}>{JOURNEY.legend}</legend>
          {spec.commutes.length === 0 ? <p className={styles.hint}>{JOURNEY.none}</p> : null}
          {spec.commutes.map((commute) => (
            <CommuteControl
              {...shared}
              key={commute.place_id}
              commute={commute}
              name={names.get(commute.place_id) ?? ""}
              problem={why(`place:${commute.place_id}`)}
            />
          ))}
          {spec.commutes.length > 0 ? <JourneySettings {...shared} spec={spec} /> : null}
        </fieldset>

        <fieldset className={styles.group}>
          <legend className={styles.groupLegend}>{FEATURES.legend}</legend>
          {scaleOf("features")}
          {DIMENSION_ORDER.filter((dimension) => dimension !== "crime").map((dimension) => {
            const controls = featuresOf(dimension);
            if (controls.length === 0) return null;
            return (
              <fieldset key={dimension} className={styles.dimension}>
                <legend className={styles.legend}>{DIMENSION[dimension]}</legend>
                <ul className={styles.list}>{controls}</ul>
              </fieldset>
            );
          })}
        </fieldset>

        <fieldset className={styles.group}>
          <legend className={styles.groupLegend}>{FEATURES.tagsLegend}</legend>
          <p className={styles.hint}>{FEATURES.tagsHint}</p>
          {scaleOf("tags")}
          <ul className={styles.list}>
            {meta.tags.map((tag) => (
              <li key={tag.tag_id}>
                <TagControl
                  {...shared}
                  tag={tag}
                  weight={spec.tags.find((weight) => weight.tag_id === tag.tag_id)}
                  problem={why(`tag:${tag.tag_id}`)}
                  scale={scales.tags}
                />
              </li>
            ))}
          </ul>
        </fieldset>

        {featuresOf("crime").length > 0 ? (
          // Recorded crime is its own group, closed and off at first, under its caveat.
          <Disclosure label={DIMENSION.crime} className={styles.crime}>
            <p>{CRIME.lead}</p>
            <p>{CRIME_CAVEAT}</p>
            {scaleOf("crime")}
            <ul className={styles.list}>{featuresOf("crime")}</ul>
          </Disclosure>
        ) : null}

        <fieldset className={styles.group}>
          <legend className={styles.groupLegend}>{HIDDEN.legend}</legend>
          {spec.areas.length === 0 ? <p className={styles.hint}>{HIDDEN.none}</p> : null}
          <ul className={styles.list}>
            {spec.areas.map((rule) => {
              const name = areas.find((area) => area.area_id === rule.area_id)?.name ?? rule.area_id;
              return (
                <li key={rule.area_id}>
                  <button
                    type="button"
                    className="target"
                    onClick={() => onEdit(edits.areaClear(rule.area_id))}
                  >
                    {rule.rule === "exclude" ? HIDDEN.show(name) : HIDDEN.only(name)}
                  </button>
                </li>
              );
            })}
          </ul>
        </fieldset>

        {onRank ? (
          <div>
            <button type="button" className={`${styles.rank} target`} onClick={onRank}>
              {SETTINGS.rank}
            </button>
          </div>
        ) : null}
      </div>
    </Disclosure>
  );
}
