import Link from "next/link";

import { CRIME_ACCOUNT, crimeVibes } from "@/content/crime";
import {
  COMBINE,
  DIMENSION,
  DIMENSION_ORDER,
  DIRECTION,
  MODE,
  POLARITY,
  PT_BASIS,
  SEGMENT,
  STRICTNESS,
  TENURE,
} from "@/content/labels";
import { METHODS } from "@/content/methods";
import { CRIME_CAVEAT } from "@/content/settings";
import { READER } from "@/content/site";
import type { MetaData, Metric, MoneyLimits, PreferenceSpec, Reader, Source } from "@/lib/api/schema";
import { grouped, outOfHundred, readableDate } from "@/lib/format";
import { placedOf } from "@/lib/holds";
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

const LIST = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

interface FeatureProps {
  readonly metric: Metric;
  readonly sources: Names;
  /** The vibes whose recipes hold the measure, by the names the API gives them. */
  readonly partOf: readonly string[];
}

function Feature({ metric, sources, partOf }: FeatureProps) {
  const { columns, notRanked } = METHODS.features;
  return (
    <li className={styles.feature}>
      <h4 className={styles.featureName}>{metric.label}</h4>
      <p>{metric.definition}</p>
      {/* A measure no search ranks on alone may still count, as a part of a vibe. It was
          said of one such that it was "not used in ranking". */}
      {metric.rankable ? null : (
        <p className="muted">
          {partOf.length === 0 ? notRanked : METHODS.features.partOf(LIST.format(partOf))}
        </p>
      )}
      <dl className={styles.facts}>
        <div>
          <dt>{columns.unit}</dt>
          <dd>{metric.unit}</dd>
        </div>
        <div>
          <dt>{columns.period}</dt>
          {/* Written as every other date on the website is. */}
          <dd>{readableDate(metric.vintage)}</dd>
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

interface FeaturesProps {
  readonly features: readonly Metric[];
  readonly sources: Names;
  readonly meta: Pick<MetaData, "tags" | "recipes">;
}

function Features({ features, sources, meta }: FeaturesProps) {
  // Only a vibe that some area is placed on: a part of one that waits counts in nothing yet.
  const partOf = (metric: Metric) =>
    placedOf(meta, meta.tags)
      .filter((tag) => tag.terms.some((term) => term.feature_id === metric.feature_id))
      .map((tag) => tag.label);
  return (
    <section aria-labelledby="features">
      <h2 id="features">{METHODS.features.title}</h2>
      <p>{METHODS.features.lead}</p>
      {DIMENSION_ORDER.map((dimension) => {
        const inGroup = features.filter((metric) => metric.dimension === dimension);
        return (
          <section key={dimension} aria-labelledby={`features-${dimension}`}>
            <h3 id={`features-${dimension}`}>{DIMENSION[dimension]}</h3>
            {dimension === "crime" ? (
              // When recorded crime counts, as every page says it, and the caveat of every such figure.
              <>
                <p>{CRIME_ACCOUNT.rule}</p>
                <p>{CRIME_CAVEAT}</p>
              </>
            ) : null}
            {inGroup.length === 0 ? (
              <p className="muted">{METHODS.features.none}</p>
            ) : (
              <ul className={styles.features}>
                {inGroup.map((metric) => (
                  <Feature key={metric.feature_id} metric={metric} sources={sources} partOf={partOf(metric)} />
                ))}
              </ul>
            )}
          </section>
        );
      })}
    </section>
  );
}

/**
 * What a vibe is, in a few lines, and the way to the page that lists every one. Which vibe
 * holds recorded crime, if any does, is said here by the names the API gives: it is part of
 * the one account of when recorded crime counts.
 */
function Vibes({ meta }: { meta: Pick<MetaData, "tags" | "features"> }) {
  const held = crimeVibes(meta);
  return (
    <section aria-labelledby="vibes">
      <h2 id="vibes">{METHODS.vibes.title}</h2>
      <p>{METHODS.vibes.lead}</p>
      <p>
        <Link className="target-min" href={paths.vibes()}>
          {METHODS.vibes.link}
        </Link>
      </p>
      <p>
        {CRIME_ACCOUNT.rule} {held.length === 0 ? CRIME_ACCOUNT.noVibe : CRIME_ACCOUNT.vibes}
      </p>
      {held.length === 0 ? null : (
        <ul>
          {held.map(({ tag, parts }) => (
            <li key={tag.tag_id}>
              <Link className="target-min" href={paths.vibes(tag.tag_id)} prefetch={false}>
                {tag.label}
              </Link>
              {": "}
              {parts.map((part, at) => (
                <span key={part.feature_id}>
                  {at > 0 ? "; " : null}
                  <span>{part.label}</span>
                </span>
              ))}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

interface DefaultsProps {
  readonly spec: PreferenceSpec;
  readonly labels: Names;
  readonly holds: MetaData["holds"];
}

function DefaultsTable({ spec, labels, holds }: DefaultsProps) {
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
          {/* What the data does not hold counts for nothing, whatever the setting says. */}
          <tr>
            <th scope="row">{budget}</th>
            {holds.costs ? (
              <>
                <td className={styles.number}>
                  {outOfHundred(spec.budget.weight)} {weightOf}
                </td>
                <td>{STRICTNESS[spec.budget.strictness]}</td>
              </>
            ) : (
              <td colSpan={2}>{METHODS.notInData}</td>
            )}
          </tr>
          <tr>
            <th scope="row">{journeys}</th>
            {holds.journeys ? (
              <>
                <td className={styles.number}>
                  {outOfHundred(spec.commute_weight)} {weightOf}
                </td>
                <td>
                  {COMBINE[spec.commute_combine]}. {PT_BASIS[spec.pt_basis]}.
                </td>
              </>
            ) : (
              <td colSpan={2}>{METHODS.notInData}</td>
            )}
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

function Limits({ limits, holds }: { limits: MetaData["limits"]; holds: MetaData["holds"] }) {
  const copy = METHODS.limits;
  const cutoffs = limits.cutoff_minutes;
  // A limit of what the data does not hold is a limit of nothing, and is not given.
  const ofABudget: readonly (readonly [string, string | null])[] = holds.costs
    ? [
        [copy.rows.rent, money(limits.rent)],
        [copy.rows.buy, money(limits.buy)],
      ]
    : [];
  const ofAJourney: readonly (readonly [string, string | null])[] = holds.journeys
    ? [
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
      ]
    : [];
  const rows: readonly (readonly [string, string | null])[] = [
    ...ofABudget,
    ...ofAJourney,
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
      {holds.costs ? null : <p>{copy.noCosts}</p>}
      {holds.journeys ? null : <p>{copy.noJourneys}</p>}
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
    [rows.preview, meta.preview ? yes : no],
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

/**
 * How a person's words are handled. What Burro does with them is site copy, and is true
 * whoever else reads them. Who else reads them and what is sent with them are the service's
 * to say, and are drawn as they were served. What the company does with them is the
 * company's to say: the service gives the address of its terms, and the page links to it.
 */
function Words({ reader }: { reader: Reader }) {
  const { title, points, reader: copy } = METHODS.words;
  const [first, ...rest] = points;
  return (
    <section aria-labelledby="words">
      <h2 id="words">{title}</h2>
      <ul>
        <li>{first}</li>
        {rest.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>
      <h3 id="reader">{copy.title}</h3>
      <p>
        {reader.notice}
        {reader.terms_url ? (
          <>
            {" "}
            <a className="target-min" href={reader.terms_url} rel="noreferrer noopener">
              {READER.terms}
            </a>
          </>
        ) : null}
      </p>
      <p className="muted">{copy.asBuilt}</p>
    </section>
  );
}

function namesOf(sources: readonly Source[]): Names {
  return new Map(sources.map((source) => [source.source_id, source.name]));
}

/**
 * The methods page: how the ranking works, how an area is named, what is
 * measured, the way to the page of vibes, where a search starts, the limits, how a journey is timed,
 * what each word for how sure a cost is means, the release, and how a
 * person's words are handled. Every figure and every definition of a feature
 * is the API's.
 */
export function MethodsTables({ meta }: Props) {
  const sources = namesOf(meta.attributions);
  const labels: Names = new Map(meta.features.map((metric) => [metric.feature_id, metric.label]));
  return (
    <>
      <Points id="ranking" title={METHODS.ranking.title} points={METHODS.ranking.points} />
      {/* The page of an area leads here by this id: `paths.methods` names it. */}
      <Points id="names" title={METHODS.names.title} points={METHODS.names.points} />
      <Features features={meta.features} sources={sources} meta={meta} />
      <Vibes meta={meta} />
      <section aria-labelledby="defaults">
        <h2 id="defaults">{METHODS.defaults.title}</h2>
        <p>{METHODS.defaults.lead}</p>
        <div className={styles.tables}>
          <DefaultsTable spec={meta.defaults.rent} labels={labels} holds={meta.holds} />
          <DefaultsTable spec={meta.defaults.buy} labels={labels} holds={meta.holds} />
        </div>
      </section>
      <Limits limits={meta.limits} holds={meta.holds} />
      {/* A result leads here by these two ids: `paths.methods` names them. */}
      {meta.journey_estimate ? (
        // The data holds no journey time, and a journey is estimated: how, in the API's
        // numbers, under the line that stands wherever an estimate is shown.
        <Points
          id="journeys"
          title={METHODS.estimate.title}
          lead={`${meta.journey_estimate.said} ${METHODS.estimate.lead}`}
          points={METHODS.estimate.points(meta.journey_estimate)}
        />
      ) : (
        <Points
          id="journeys"
          title={METHODS.journeys.title}
          lead={meta.holds.journeys ? undefined : METHODS.journeys.notYet}
          points={METHODS.journeys.points}
        />
      )}
      <Points
        id="confidence"
        title={METHODS.confidence.title}
        lead={meta.holds.costs ? METHODS.confidence.lead : `${METHODS.confidence.notYet} ${METHODS.confidence.lead}`}
        points={[
          METHODS.confidence.rows.high,
          METHODS.confidence.rows.medium,
          METHODS.confidence.rows.low,
          METHODS.confidence.rows.unstated,
        ]}
      />
      <Release meta={meta} />
      <Words reader={meta.reader} />
    </>
  );
}
