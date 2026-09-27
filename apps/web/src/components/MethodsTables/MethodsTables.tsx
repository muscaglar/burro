import Link from "next/link";
import type { ReactNode } from "react";

import { KEPT_WITH_ACCOUNTS } from "@/content/account";
import { CRIME_ACCOUNT, crimeVibes, ruleIn } from "@/content/crime";
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
import { accountsOn } from "@/lib/account/on";
import type { MetaData, Metric, MoneyLimits, PreferenceSpec, Reader, Source } from "@/lib/api/schema";
import { grouped, outOfHundred, readableDate } from "@/lib/format";
import { placedOf } from "@/lib/holds";
import { METHODS_PARTS, paths } from "@/lib/paths";

import { Board, Edged, Marked, Part, Points as Listed, Sourced } from "../About/About";
import { Fold } from "../About/Fold";
import { Frame } from "../kit/Frame/Frame";
import { Thing } from "../kit/Thing/Thing";
import styles from "./MethodsTables.module.css";

interface Props {
  readonly meta: MetaData;
}

type Names = ReadonlyMap<string, string>;

function SourceLinks({ ids, sources }: { ids: readonly string[]; sources: Names }) {
  return (
    <Sourced>
      {ids.map((id) => (
        <li key={id}>
          <Link className="target-min" href={paths.sources(id)} prefetch={false}>
            {sources.get(id) ?? id}
          </Link>
        </li>
      ))}
    </Sourced>
  );
}

const LIST = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

interface FeatureProps {
  readonly metric: Metric;
  readonly sources: Names;
  /** The vibes whose recipes hold the measure, by the names the API gives them. */
  readonly partOf: readonly string[];
}

/**
 * One measure, as a card with a plain edge of ink: there are many of them, and a shadow
 * under each would be noise. Before its name is the small drawing of the family the API
 * puts it in. Where it puts it in none, the measure is drawn by the dimension the API
 * gives it, as the group of the settings that holds it is, and by the plain drawing where
 * nobody has drawn that. The drawing is dress.
 */
function Feature({ metric, sources, partOf }: FeatureProps) {
  const { columns, notRanked } = METHODS.features;
  return (
    <Frame kind="plain" as="li" bare className={styles.feature}>
      <div className={styles.featureHead}>
        <Thing kind="feature" id={metric.feature_id} family={metric.family ?? metric.dimension} />
        <h4 className={styles.featureName}>{metric.label}</h4>
      </div>
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
    </Frame>
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
    // What is measured is many parts: what it is, in a box, and then a box for each group of
    // measures, with the grass between them.
    <section className={styles.measured} aria-labelledby="features">
      <Part id="features" title={METHODS.features.title} region={false}>
        <p>{METHODS.features.lead}</p>
      </Part>
      {DIMENSION_ORDER.map((dimension) => {
        const inGroup = features.filter((metric) => metric.dimension === dimension);
        return (
          <Frame kind="box" as="section" bare key={dimension} className={styles.group} aria-labelledby={`features-${dimension}`}>
            <Board as="h3" id={`features-${dimension}`}>
              {DIMENSION[dimension]}
            </Board>
            {dimension === "crime" ? (
              // When recorded crime counts, as every page says it, and the caveat of every such figure.
              <div className={styles.notice}>
                <p>{CRIME_ACCOUNT.rule}</p>
                <p>{CRIME_CAVEAT}</p>
              </div>
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
          </Frame>
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
    <Part id="vibes" title={METHODS.vibes.title}>
      <p>{METHODS.vibes.lead}</p>
      <p>
        <Link className="target-min" href={paths.vibes()}>
          {METHODS.vibes.link}
        </Link>
      </p>
      {/* What a town is built of stood here. It is said once, in the key, and this says where. */}
      <p>{METHODS.vibes.key}</p>
      <p>
        {CRIME_ACCOUNT.rule} {held.length === 0 ? CRIME_ACCOUNT.noVibe : CRIME_ACCOUNT.vibes}
      </p>
      {held.length === 0 ? null : (
        <Marked>
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
        </Marked>
      )}
    </Part>
  );
}

interface CellProps {
  /** The heading of the column, which the cell says for itself where the rows are stacked. Left out of a cell that is of no one column. */
  readonly name?: string;
  readonly number?: boolean;
  /** How many columns the cell stands across. */
  readonly across?: number;
  readonly children: ReactNode;
}

/** One thing said of a setting. Stacked, it says what it is: the heading of its column is then not drawn. */
function Cell({ name, number = false, across, children }: CellProps) {
  return (
    // The role is the cell's own, said again because a narrow box stacks the rows. The
    // rule takes any cell for one of a grid that can be pressed, which this is not.
    // eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role
    <td role="cell" className={number ? styles.number : undefined} colSpan={across}>
      {name === undefined ? null : (
        // The column's heading says it to a screen reader, so this is kept from one.
        <span className={styles.cellName} aria-hidden="true">
          {name}
        </span>
      )}
      <span>{children}</span>
    </td>
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
    <section className={styles.tenure} aria-labelledby={id}>
      <Board as="h3" id={id}>
        {TENURE[spec.tenure]}
      </Board>
      <p>
        {home}: {SEGMENT[spec.budget.segment]}
      </p>
      <Edged>
        {/*
          In a narrow box each setting is stacked: its name, and under it each thing said of
          it, by name. It is one table either way, so every part of it says its role again:
          laid out as blocks, a browser may forget that a table is one.
        */}
        <table role="table" className={`${styles.table} ${styles.stacks}`} aria-labelledby={id}>
          {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
          <thead role="rowgroup" className={styles.head}>
            <tr role="row">
              <th role="columnheader" scope="col">
                {columns.setting}
              </th>
              <th role="columnheader" scope="col" className={styles.number}>
                {columns.value}
              </th>
              <th role="columnheader" scope="col">
                {columns.direction}
              </th>
            </tr>
          </thead>
          {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
          <tbody role="rowgroup">
            {/* What the data does not hold counts for nothing, whatever the setting says. */}
            <tr role="row" className={styles.row}>
              <th role="rowheader" scope="row">
                {budget}
              </th>
              {holds.costs ? (
                <>
                  <Cell name={columns.value} number>
                    {outOfHundred(spec.budget.weight)} {weightOf}
                  </Cell>
                  <Cell name={columns.direction}>{STRICTNESS[spec.budget.strictness]}</Cell>
                </>
              ) : (
                <Cell across={2}>{METHODS.notInData}</Cell>
              )}
            </tr>
            <tr role="row" className={styles.row}>
              <th role="rowheader" scope="row">
                {journeys}
              </th>
              {holds.journeys ? (
                <>
                  <Cell name={columns.value} number>
                    {outOfHundred(spec.commute_weight)} {weightOf}
                  </Cell>
                  <Cell name={columns.direction}>
                    {COMBINE[spec.commute_combine]}. {PT_BASIS[spec.pt_basis]}.
                  </Cell>
                </>
              ) : (
                <Cell across={2}>{METHODS.notInData}</Cell>
              )}
            </tr>
            {spec.weights.map((weight) => (
              <tr role="row" key={weight.feature_id} className={styles.row}>
                <th role="rowheader" scope="row">
                  {labels.get(weight.feature_id) ?? weight.feature_id}
                </th>
                <Cell name={columns.value} number>
                  {outOfHundred(weight.weight)} {weightOf}
                </Cell>
                <Cell name={columns.direction}>{DIRECTION[weight.direction]}</Cell>
              </tr>
            ))}
          </tbody>
        </table>
      </Edged>
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
    <Part id="limits" title={copy.title}>
      <p>{copy.lead}</p>
      {holds.costs ? null : <p>{copy.noCosts}</p>}
      {holds.journeys ? null : <p>{copy.noJourneys}</p>}
      {/* It is laid out by the width of its own box, as the tables of where a search starts are. */}
      <div className={styles.limits}>
        <Edged>
          <table role="table" className={`${styles.table} ${styles.stacks}`} aria-labelledby="limits">
            {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
            <thead role="rowgroup" className={styles.head}>
              <tr role="row">
                <th role="columnheader" scope="col">
                  {copy.columns.limit}
                </th>
                <th role="columnheader" scope="col">
                  {copy.columns.value}
                </th>
              </tr>
            </thead>
            {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
            <tbody role="rowgroup">
              {rows.map(([name, value]) =>
                value === null ? null : (
                  <tr role="row" key={name} className={styles.row}>
                    <th role="rowheader" scope="row">
                      {name}
                    </th>
                    <Cell name={copy.columns.value}>{value}</Cell>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </Edged>
      </div>
    </Part>
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
    <Part id="release" title={METHODS.release.title}>
      <dl className={styles.release}>
        {entries.map(([name, value]) => (
          <div key={name}>
            <dt>{name}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </Part>
  );
}

interface PointsProps {
  readonly id: string;
  readonly title: string;
  readonly lead?: string;
  readonly points: readonly string[];
}

/** True of a part that another page leads to, by the id of its heading. */
const isLedTo = (id: string): boolean => (METHODS_PARTS as readonly string[]).includes(id);

/** A part that is read: its heading, what is said first of it, and its points. */
function Points({ id, title, lead, points }: PointsProps) {
  return (
    <Part id={id} title={title} led={isLedTo(id)}>
      {lead === undefined ? null : <p>{lead}</p>}
      <Listed points={points} />
    </Part>
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
  // The third says what a browser keeps, which is nothing only while nobody can sign in.
  const said = accountsOn() ? points.map((point, at) => (at === 2 ? KEPT_WITH_ACCOUNTS : point)) : points;
  const [first, ...rest] = said;
  return (
    <Part id="words" title={title} led={isLedTo("words")}>
      <Marked>
        <li>{first}</li>
        {rest.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </Marked>
      <Board as="h3" id="reader">
        {copy.title}
      </Board>
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
    </Part>
  );
}

/**
 * How Burro finds areas for a person, in short: what it looks at, how it ranks, what it
 * will not do, and that every figure has its source. It is what the page is read for, so it
 * stands in sight, in a box of its own, under no heading but the page's.
 *
 * When recorded crime counts is said by the one rule, word for word, as every page says it.
 */
function Account({ meta }: { meta: Pick<MetaData, "tags" | "features"> }) {
  const { looks, ranks, wont, sourced, toVibes, toSources } = METHODS.account;
  return (
    <Frame kind="box" bare className={styles.account} data-methods="account">
      <p>{looks}</p>
      <p>{ranks}</p>
      <p>
        {wont.before} {ruleIn(meta)} {wont.after}
      </p>
      <p>{sourced}</p>
      <ul className={styles.ways}>
        <li>
          <Link className="target-min" href={paths.vibes()}>
            {toVibes}
          </Link>
        </li>
        <li>
          {/* Which page a person reads next is told to no server ahead of time. */}
          <Link className="target-min" href={paths.sources()} prefetch={false}>
            {toSources}
          </Link>
        </li>
      </ul>
    </Frame>
  );
}

function namesOf(sources: readonly Source[]): Names {
  return new Map(sources.map((source) => [source.source_id, source.name]));
}

/**
 * The methods page. First a short, plain account of how Burro finds areas for a person,
 * which somebody could read in a minute. Under it, one fold, closed until it is pressed,
 * that holds all of the rest as it was: how the ranking works, how an area is named, what
 * is measured, the way to the page of vibes, where a search starts, the limits, how a
 * journey is timed, what each word for how sure a cost is means, the release, and how a
 * person's words are handled. Every figure and every definition of a feature is the API's.
 *
 * Nothing of it is lost, and each part keeps the id another page leads to it by. Each part
 * is a box of its own, for a page that stands on the meadow. A table stands inside a plain
 * edge of ink, and so does each measure, of which there are many.
 */
export function MethodsTables({ meta }: Props) {
  const sources = namesOf(meta.attributions);
  const labels: Names = new Map(meta.features.map((metric) => [metric.feature_id, metric.label]));
  return (
    <>
      <Account meta={meta} />
      <Fold says={METHODS.detail} kind="ground">
        <Points id="ranking" title={METHODS.ranking.title} points={METHODS.ranking.points} />
        {/* The page of an area leads here by this id: `paths.methods` names it. Over a made-up
            city the method chose no name, which is said before the method is. */}
        <Points
          id="names"
          title={METHODS.names.title}
          lead={meta.synthetic ? METHODS.names.madeUp : undefined}
          points={METHODS.names.points}
        />
        <Features features={meta.features} sources={sources} meta={meta} />
        <Vibes meta={meta} />
        <Part id="defaults" title={METHODS.defaults.title} lay="over">
          <p>{METHODS.defaults.lead}</p>
          <div className={styles.tables}>
            <DefaultsTable spec={meta.defaults.rent} labels={labels} holds={meta.holds} />
            <DefaultsTable spec={meta.defaults.buy} labels={labels} holds={meta.holds} />
          </div>
        </Part>
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
        {meta.rents ? (
          // Each rent of the data is of a wider place than an area. What is said of the rents
          // is the API's: that each is of a district or a borough, and what their publisher
          // advises. How an area takes one, and how a budget is held against it, follows.
          <Points
            id="rents"
            title={METHODS.rents.title}
            lead={`${meta.rents.of_a_place} ${meta.rents.caution}`}
            points={METHODS.rents.points}
          />
        ) : null}
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
      </Fold>
    </>
  );
}
