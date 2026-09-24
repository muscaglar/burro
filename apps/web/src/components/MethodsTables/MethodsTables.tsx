import Link from "next/link";

import {
  COMBINE,
  DIMENSION,
  DIMENSION_ORDER,
  DIRECTION,
  MODE,
  POLARITY,
  PT_BASIS,
  READING,
  SEGMENT,
  STRICTNESS,
  TENURE,
} from "@/content/labels";
import { METHODS } from "@/content/methods";
import type { MetaData, Metric, MoneyLimits, PreferenceSpec, Source, Tag } from "@/lib/api/schema";
import { grouped, outOfHundred, readableDate } from "@/lib/format";
import { paths } from "@/lib/paths";

import styles from "./MethodsTables.module.css";

interface Props {
  readonly meta: MetaData;
}

type Names = ReadonlyMap<string, string>;

function SourceLinks({ ids, sources }: { ids: readonly string[]; sources: Names }) {
  return (
    <ul className={styles.inline}>
      {ids.map((id) => (
        <li key={id}>
          <Link className="target-min" href={paths.sources(id)} prefetch={false}>
            {sources.get(id) ?? id}
          </Link>
        </li>
      ))}
    </ul>
  );
}

function Feature({ metric, sources }: { metric: Metric; sources: Names }) {
  const { columns, notRanked } = METHODS.features;
  return (
    <li className={styles.feature}>
      <h4 className={styles.featureName}>{metric.label}</h4>
      <p>{metric.definition}</p>
      {metric.rankable ? null : <p className="muted">{notRanked}</p>}
      <dl className={styles.facts}>
        <div>
          <dt>{columns.unit}</dt>
          <dd>{metric.unit}</dd>
        </div>
        <div>
          <dt>{columns.period}</dt>
          <dd>{metric.vintage}</dd>
        </div>
        <div>
          <dt>{columns.polarity}</dt>
          <dd>{POLARITY[metric.polarity]}</dd>
        </div>
        <div>
          <dt>{columns.sources}</dt>
          <dd>
            <SourceLinks ids={metric.source_ids} sources={sources} />
          </dd>
        </div>
      </dl>
    </li>
  );
}

function Features({ features, sources }: { features: readonly Metric[]; sources: Names }) {
  return (
    <section aria-labelledby="features">
      <h2 id="features">{METHODS.features.title}</h2>
      <p>{METHODS.features.lead}</p>
      {DIMENSION_ORDER.map((dimension) => {
        const inGroup = features.filter((metric) => metric.dimension === dimension);
        return (
          <section key={dimension} aria-labelledby={`features-${dimension}`}>
            <h3 id={`features-${dimension}`}>{DIMENSION[dimension]}</h3>
            {inGroup.length === 0 ? (
              <p className="muted">{METHODS.features.none}</p>
            ) : (
              <ul className={styles.features}>
                {inGroup.map((metric) => (
                  <Feature key={metric.feature_id} metric={metric} sources={sources} />
                ))}
              </ul>
            )}
          </section>
        );
      })}
    </section>
  );
}

function Tags({ tags, labels }: { tags: readonly Tag[]; labels: Names }) {
  const { columns, shareOf } = METHODS.tags;
  return (
    <section aria-labelledby="tags">
      <h2 id="tags">{METHODS.tags.title}</h2>
      <p>{METHODS.tags.lead}</p>
      <div className={styles.tables}>
        {tags.map((tag) => (
          <table key={tag.tag_id} className={styles.table}>
            <caption className={styles.caption}>{tag.label}</caption>
            <thead>
              <tr>
                <th scope="col">{columns.feature}</th>
                <th scope="col">{columns.reading}</th>
                <th scope="col" className={styles.number}>
                  {columns.share}
                </th>
              </tr>
            </thead>
            <tbody>
              {tag.terms.map((term) => (
                <tr key={term.feature_id}>
                  <th scope="row">{labels.get(term.feature_id) ?? term.feature_id}</th>
                  <td>{READING[term.reading]}</td>
                  <td className={styles.number}>
                    {term.hundredths} {shareOf}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}
      </div>
    </section>
  );
}

function DefaultsTable({ spec, labels }: { spec: PreferenceSpec; labels: Names }) {
  const { columns, budget, journeys, home, weightOf } = METHODS.defaults;
  const id = `defaults-${spec.tenure}`;
  return (
    <section aria-labelledby={id}>
      <h3 id={id}>{TENURE[spec.tenure]}</h3>
      <p>
        {home}: {SEGMENT[spec.budget.segment]}
      </p>
      <table className={styles.table} aria-labelledby={id}>
        <thead>
          <tr>
            <th scope="col">{columns.setting}</th>
            <th scope="col" className={styles.number}>
              {columns.value}
            </th>
            <th scope="col">{columns.direction}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">{budget}</th>
            <td className={styles.number}>
              {outOfHundred(spec.budget.weight)} {weightOf}
            </td>
            <td>{STRICTNESS[spec.budget.strictness]}</td>
          </tr>
          <tr>
            <th scope="row">{journeys}</th>
            <td className={styles.number}>
              {outOfHundred(spec.commute_weight)} {weightOf}
            </td>
            <td>
              {COMBINE[spec.commute_combine]}. {PT_BASIS[spec.pt_basis]}.
            </td>
          </tr>
          {spec.weights.map((weight) => (
            <tr key={weight.feature_id}>
              <th scope="row">{labels.get(weight.feature_id) ?? weight.feature_id}</th>
              <td className={styles.number}>
                {outOfHundred(weight.weight)} {weightOf}
              </td>
              <td>{DIRECTION[weight.direction]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function money(limits: MoneyLimits | undefined): string | null {
  if (limits === undefined) return null;
  const { to, inStepsOf } = METHODS.limits;
  return `£${grouped(limits.minimum)} ${to} £${grouped(limits.maximum)}, ${inStepsOf} £${grouped(limits.unit)}`;
}

function Limits({ limits }: { limits: MetaData["limits"] }) {
  const copy = METHODS.limits;
  const cutoffs = limits.cutoff_minutes;
  const rows: readonly (readonly [string, string | null])[] = [
    [copy.rows.rent, money(limits.rent)],
    [copy.rows.buy, money(limits.buy)],
    [
      copy.rows.minutes,
      limits.minutes_min === undefined || limits.minutes_max === undefined
        ? null
        : `${limits.minutes_min} ${copy.to} ${limits.minutes_max} ${copy.minutes}`,
    ],
    [`${copy.rows.cutoff}: ${MODE.pt}`, `${cutoffs.pt} ${copy.minutes}`],
    [`${copy.rows.cutoff}: ${MODE.cycle}`, `${cutoffs.cycle} ${copy.minutes}`],
    [`${copy.rows.cutoff}: ${MODE.walk}`, `${cutoffs.walk} ${copy.minutes}`],
    [copy.rows.places, limits.max_commutes === undefined ? null : String(limits.max_commutes)],
    [copy.rows.text, `${grouped(limits.max_text)} ${copy.characters}`],
    [
      copy.rows.weightStep,
      limits.weight_unit === undefined
        ? null
        : `${outOfHundred(limits.weight_unit)} ${METHODS.defaults.weightOf}`,
    ],
  ];
  return (
    <section aria-labelledby="limits">
      <h2 id="limits">{copy.title}</h2>
      <p>{copy.lead}</p>
      <table className={styles.table} aria-labelledby="limits">
        <thead>
          <tr>
            <th scope="col">{copy.columns.limit}</th>
            <th scope="col">{copy.columns.value}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([name, value]) =>
            value === null ? null : (
              <tr key={name}>
                <th scope="row">{name}</th>
                <td>{value}</td>
              </tr>
            ),
          )}
        </tbody>
      </table>
    </section>
  );
}

function Release({ meta }: { meta: MetaData }) {
  const { rows, yes, no } = METHODS.release;
  const entries: readonly (readonly [string, string])[] = [
    [rows.release, meta.release_id],
    [rows.built, readableDate(meta.built_at)],
    [rows.engine, meta.engine_version],
    [rows.catalogue, String(meta.catalogue_version)],
    [rows.synthetic, meta.synthetic ? yes : no],
    [rows.areas, grouped(meta.counts.neighbourhoods)],
    [rows.rankable, grouped(meta.counts.rankable)],
    [rows.places, grouped(meta.counts.places)],
    [rows.stations, grouped(meta.counts.stations)],
    [rows.destinations, grouped(meta.counts.destinations)],
  ];
  return (
    <section aria-labelledby="release">
      <h2 id="release">{METHODS.release.title}</h2>
      <dl className={styles.facts}>
        {entries.map(([name, value]) => (
          <div key={name}>
            <dt>{name}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

interface PointsProps {
  readonly id: string;
  readonly title: string;
  readonly lead?: string;
  readonly points: readonly string[];
}

function Points({ id, title, lead, points }: PointsProps) {
  return (
    <section aria-labelledby={id}>
      <h2 id={id}>{title}</h2>
      {lead === undefined ? null : <p>{lead}</p>}
      <ul>
        {points.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>
    </section>
  );
}

function namesOf(sources: readonly Source[]): Names {
  return new Map(sources.map((source) => [source.source_id, source.name]));
}

/**
 * The methods page: how the ranking works, what is measured, the formula of
 * each tag, where a search starts, the limits, how a journey is timed, what
 * each word for how sure a cost is means, the release, and how a person's
 * words are handled. Every figure and every definition of a feature is the
 * API's.
 */
export function MethodsTables({ meta }: Props) {
  const sources = namesOf(meta.attributions);
  const labels: Names = new Map(meta.features.map((metric) => [metric.feature_id, metric.label]));
  return (
    <>
      <Points id="ranking" title={METHODS.ranking.title} points={METHODS.ranking.points} />
      <Features features={meta.features} sources={sources} />
      <Tags tags={meta.tags} labels={labels} />
      <section aria-labelledby="defaults">
        <h2 id="defaults">{METHODS.defaults.title}</h2>
        <p>{METHODS.defaults.lead}</p>
        <div className={styles.tables}>
          <DefaultsTable spec={meta.defaults.rent} labels={labels} />
          <DefaultsTable spec={meta.defaults.buy} labels={labels} />
        </div>
      </section>
      <Limits limits={meta.limits} />
      {/* A result leads here by these two ids: `paths.methods` names them. */}
      <Points id="journeys" title={METHODS.journeys.title} points={METHODS.journeys.points} />
      <Points
        id="confidence"
        title={METHODS.confidence.title}
        lead={METHODS.confidence.lead}
        points={[METHODS.confidence.rows.high, METHODS.confidence.rows.medium, METHODS.confidence.rows.low]}
      />
      <Release meta={meta} />
      <Points id="words" title={METHODS.words.title} points={METHODS.words.points} />
    </>
  );
}
