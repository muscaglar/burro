"use client";

import { useId, type ReactNode } from "react";

import { DIMENSION } from "@/content/labels";
import { whyRefused } from "@/content/search";
import { CRIME_ACCOUNT, countsOf, crimeVibes } from "@/content/crime";
import { roughOf } from "@/content/rough";
import { BRANDS, CRIME, CRIME_CAVEAT, FEATURES, HIDDEN, JOURNEY, SETTINGS, SLIDER } from "@/content/settings";
import type { Answer } from "@/lib/api/client";
import type {
  AreaSummary,
  FoundPlace,
  MetaData,
  Metric,
  Operations,
  PlacesData,
  PreferenceSpec,
  RejectReason,
  Tenure,
} from "@/lib/api/schema";
import { inOrder } from "@/lib/area/profile";
import { recipeOf } from "@/lib/holds";
import { namesOfPlaces } from "@/lib/search/chips";
import { counts } from "@/lib/search/counts";
import { edits } from "@/lib/search/edits";

import { Disclosure } from "../Disclosure/Disclosure";
import { PlaceCombobox } from "../PlaceCombobox/PlaceCombobox";
import { BudgetControl } from "./BudgetControl";
import { CommuteControl, JourneySettings } from "./CommuteControl";
import styles from "./SettingsPanel.module.css";
import { TenureChoice } from "./TenureChoice";
import { MadeOf, VibeControl } from "./VibeControl";
import { WeightControl } from "./WeightControl";

interface Props {
  /** The spec the API last returned. Every control is drawn from it. */
  readonly spec: PreferenceSpec;
  readonly meta: MetaData;
  readonly areas: readonly AreaSummary[];
  readonly placeNames: Readonly<Record<string, string>>;
  readonly onEdit: (operations: Operations) => void;
  /** Told of a choice of renting or buying. Before anything is asked for, it sends nothing. */
  readonly onTenure: (tenure: Tenure) => void;
  /** Route 8, for the field that adds a place to reach. */
  readonly searchPlaces: (text: string, signal: AbortSignal) => Promise<Answer<PlacesData>>;
  readonly onAddPlace: (place: FoundPlace) => void;
  /** Said in place of the field when no more places can be named. */
  readonly full?: string | null;
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

/** True when the feature is recorded crime, which is a group of its own, off unless asked for. */
const isCrime = (metric: Metric) => metric.dimension === "crime";

/**
 * True when the feature is of the chains of grocers, gyms and coffee. They are a group of
 * their own: a switch for every chain would bury the family they belong to.
 */
const isBrand = (metric: Metric) => metric.dimension === "brands";

/**
 * The settings: the same search as a form, in groups, each closed at first.
 * Money and journeys first, then one group for each family of vibes, as the
 * API names and orders them, then the brands, then what belongs to no family,
 * and recorded crime last. Every control here makes the edit a sentence would, so the page
 * works with no words read at all.
 *
 * In a family each vibe has one slider, and "Made of" opens its parts. A
 * feature of the family that is in no recipe is under "Other things that
 * count". It offers only what the release can rank, within the limits the
 * API served, so it never offers what the reducer would refuse.
 */
export function SettingsPanel({
  spec,
  meta,
  areas,
  placeNames,
  onEdit,
  onTenure,
  searchPlaces,
  onAddPlace,
  full = null,
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
    return reason === undefined ? null : whyRefused(reason, meta);
  };
  const shared = { limits, onEdit, version };
  const inARecipe = new Set(meta.tags.flatMap((tag) => tag.terms.map((term) => term.feature_id)));
  const rankable = meta.features.filter((metric) => metric.rankable);

  const controlsOf = (features: readonly Metric[], scale: string) =>
    features.map((metric) => (
      <li key={metric.feature_id}>
        <WeightControl
          {...shared}
          metric={metric}
          weight={spec.weights.find((weight) => weight.feature_id === metric.feature_id)}
          problem={why(`feature:${metric.feature_id}`)}
          scale={scale}
        />
      </li>
    ));

  /** True when any of these features counts, so that its slider is drawn. */
  const anyCounts = (features: readonly Metric[]) =>
    features.some((metric) => counts(spec.weights.find((weight) => weight.feature_id === metric.feature_id)));

  /**
   * One group of the settings, closed at first. What the scale of a slider means is said
   * once for the group, where it can be seen, and only while the group shows a slider.
   */
  const group = (key: string, label: string, slides: boolean, children: (scale: string) => ReactNode) => (
    <Disclosure key={key} label={label} className={styles.group}>
      <div className={styles.inside}>
        {slides ? (
          <p id={`${id}-${key}`} className={styles.hint}>
            {SLIDER.range}
          </p>
        ) : null}
        {children(`${id}-${key}`)}
      </div>
    </Disclosure>
  );

  const families = meta.families.map(({ family, label }) => {
    const vibes = meta.tags.filter((tag) => tag.family === family);
    const others = rankable.filter(
      (metric) =>
        metric.family === family && !isCrime(metric) && !isBrand(metric) && !inARecipe.has(metric.feature_id),
    );
    if (vibes.length === 0 && others.length === 0) return null;
    // A vibe that runs one way always shows its slider, where any area can be placed on it.
    // A scale says what its own ends mean.
    const slides =
      vibes.some((tag) => tag.shape === "one_way" && recipeOf(meta, tag.tag_id)?.placed !== false) ||
      anyCounts(others);
    return group(family, label, slides, (scale) => (
      <>
        <ul className={styles.list}>
          {vibes.map((tag) => (
            <li key={tag.tag_id} className={styles.vibe}>
              <VibeControl
                {...shared}
                tag={tag}
                held={recipeOf(meta, tag.tag_id)}
                weight={spec.tags.find((weight) => weight.tag_id === tag.tag_id)}
                problem={why(`tag:${tag.tag_id}`)}
                scale={scale}
                crime={countsOf(tag, meta.features)}
                rough={roughOf(tag, meta)}
              />
              <MadeOf
                {...shared}
                tag={tag}
                features={meta.features}
                weights={spec.weights}
                problemOf={(featureId) => why(`feature:${featureId}`)}
              />
            </li>
          ))}
        </ul>
        {others.length > 0 ? (
          <fieldset className={styles.dimension}>
            <legend className={styles.legend}>{FEATURES.others}</legend>
            <ul className={styles.list}>{controlsOf(others, scale)}</ul>
          </fieldset>
        ) : null}
      </>
    ));
  });

  const apart = rankable.filter((metric) => metric.family === null && !isCrime(metric) && !isBrand(metric));
  const brands = inOrder(rankable.filter(isBrand));
  const crime = rankable.filter(isCrime);

  return (
    <Disclosure label={SETTINGS.title} open={open} onToggle={onToggle} className={styles.settings}>
      <div className={styles.panel} aria-busy={busy}>
        <p className={styles.lead}>{SETTINGS.lead}</p>

        <Disclosure label={SETTINGS.money} className={styles.group}>
          <div className={styles.inside}>
            <TenureChoice tenure={spec.tenure} onChoose={onTenure} version={version} problem={why("tenure")} />
            <BudgetControl
              {...shared}
              budget={spec.budget}
              tenure={spec.tenure}
              problem={why("budget")}
              costs={meta.holds.costs}
            />
          </div>
        </Disclosure>

        <Disclosure label={SETTINGS.journeys} className={styles.group}>
          <div className={styles.inside}>
            {/* Where the data names no place, there is none to add, and the group says so. */}
            {meta.holds.journeys ? (
              <PlaceCombobox search={searchPlaces} onPick={onAddPlace} full={full} />
            ) : (
              <p className={styles.hint}>{JOURNEY.notInData}</p>
            )}
            {meta.holds.journeys && spec.commutes.length === 0 ? (
              <p className={styles.hint}>{JOURNEY.none}</p>
            ) : null}
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
          </div>
        </Disclosure>

        {families}

        {brands.length > 0
          ? // The mix of brands, and every chain a person may ask to be near. Closed at first.
            group("brands", DIMENSION.brands, anyCounts(brands), (scale) => (
              <>
                <p>{BRANDS.lead}</p>
                <ul className={styles.list}>{controlsOf(brands, scale)}</ul>
              </>
            ))
          : null}

        {apart.length > 0
          ? group("apart", SETTINGS.airAndNoise, anyCounts(apart), (scale) => (
              <ul className={styles.list}>{controlsOf(apart, scale)}</ul>
            ))
          : null}

        {crime.length > 0
          ? // Recorded crime is its own group, closed and off at first, under its caveat.
            group("crime", DIMENSION.crime, anyCounts(crime), (scale) => (
              <>
                <p>{CRIME.lead}</p>
                {/* Where no vibe of the release holds recorded crime, the rule is followed by a line that says so. */}
                {crimeVibes(meta).length === 0 ? <p>{CRIME_ACCOUNT.noVibe}</p> : null}
                <p>{CRIME_CAVEAT}</p>
                <ul className={styles.list}>{controlsOf(crime, scale)}</ul>
              </>
            ))
          : null}

        {spec.areas.length > 0 ? (
          <Disclosure label={HIDDEN.legend} className={styles.group}>
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
          </Disclosure>
        ) : null}

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
