import Link from "next/link";

import { AREA } from "@/content/area";
import { DIMENSION } from "@/content/labels";
import type { AreaData, Fact, GeometryData, MetaData, Tenure } from "@/lib/api/schema";
import {
  areaFact,
  costFacts,
  factsShown,
  featuresByDimension,
  stationFacts,
  tagRows,
} from "@/lib/area/profile";
import { sourcesOf } from "@/lib/facts";
import { paths } from "@/lib/paths";

import { CompareButton } from "../CompareTray/CompareButton";
import { CompareTray } from "../CompareTray/CompareTray";
import { FactRow } from "../FactRow/FactRow";
import { LocatorMap, outlinesOf } from "../LocatorMap/LocatorMap";
import { SourceLine } from "../SourceLine/SourceLine";
import styles from "./AreaProfile.module.css";

interface Props {
  /** The area's profile, from route 6. */
  readonly data: AreaData;
  /** The features and tags of the release, from route 11: their names, and what each is about. */
  readonly meta: Pick<MetaData, "features" | "tags">;
  /** The boundary of every area, from route 5. */
  readonly geometry: GeometryData;
}

/** The ids of the headings, which the list of contents links to. They name sections, never a place. */
const SECTION = {
  where: "where",
  stations: "stations",
  cost: "cost",
  features: "measured",
  tags: "feel",
  sources: "sources",
} as const;

function Rows({ facts }: { readonly facts: readonly Fact[] }) {
  return (
    <ul className={styles.rows}>
      {facts.map((fact) => (
        <li key={fact.fact_id}>
          <FactRow fact={fact} source="line" />
        </li>
      ))}
    </ul>
  );
}

/** A row for something the area has no figure for. It says so, and gives no figure and no source. */
function NoFigure({ name, says }: { readonly name: string; readonly says: string }) {
  return (
    <div className={styles.noFigure} role="group" aria-label={name}>
      <p className={styles.name}>{name}</p>
      <p className={styles.says}>{says}</p>
    </div>
  );
}

function Cost({ data, tenure }: { readonly data: AreaData; readonly tenure: Tenure }) {
  const facts = costFacts(data, tenure);
  return (
    // A heading and its rows. It is no landmark: the page has one for each part, and no more.
    <div className={styles.part}>
      <h3>{AREA.cost.tenure[tenure]}</h3>
      {facts.length > 0 ? (
        <ul className={styles.rows}>
          {facts.map((fact) => (
            <li key={fact.fact_id}>
              {/* The kind of home names the row. "Rent" would name six of them alike. */}
              <FactRow fact={fact} source="line" name={fact.slots.segment ?? fact.label} />
            </li>
          ))}
        </ul>
      ) : (
        <p>{AREA.cost.none[tenure]}</p>
      )}
    </div>
  );
}

/**
 * One area's page: where it is, its stations, what homes cost, every figure
 * the release holds for it laid out by what it is about, and its tags. Every
 * figure is a fact of the API's, shown as it came, with its source and its
 * date written out under it.
 *
 * It is drawn on the server and reads with scripts off. The one part that
 * needs a script is the button that puts the area among those to compare.
 */
export function AreaProfile({ data, meta, geometry }: Props) {
  const { area } = data;
  const named = areaFact(data);
  // The name and the borough are the fact's, where there is one: it carries their source.
  const name = named?.slots.name ?? area.name;
  const borough = named?.slots.borough ?? area.borough;
  const stations = stationFacts(data);
  const groups = featuresByDimension(data, meta.features);
  const tags = tagRows(data, meta.tags);
  const sources = sourcesOf(factsShown(data, meta.features, meta.tags));
  const outlines = outlinesOf(geometry);

  return (
    <article className={styles.profile} aria-labelledby="area-name">
      <header className={styles.head}>
        <h1 id="area-name">{name}</h1>
        <dl className={styles.borough}>
          <div>
            <dt>{AREA.borough}</dt>
            <dd>{borough}</dd>
          </div>
        </dl>
        {named ? <SourceLine facts={[named]} /> : null}
        {area.rankable ? null : <p className={styles.notRanked}>{AREA.notRanked}</p>}
      </header>

      <nav className={styles.contents} aria-label={AREA.contents}>
        <ul>
          {(
            [
              [SECTION.where, AREA.where.title],
              [SECTION.stations, AREA.stations.title],
              [SECTION.cost, AREA.cost.title],
              [SECTION.features, AREA.features.title],
              [SECTION.tags, AREA.tags.title],
              [SECTION.sources, AREA.sources.title],
            ] as const
          ).map(([id, title]) => (
            <li key={id}>
              <a className="target-min" href={`#${id}`}>
                {title}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <section className={styles.compare} aria-label={AREA.compare}>
        {/* Only what the button needs is handed to the browser. */}
        <CompareButton area={{ area_id: area.area_id, slug: area.slug, name }} />
        <CompareTray />
      </section>

      <section className={styles.part} aria-labelledby={SECTION.where}>
        <h2 id={SECTION.where}>{AREA.where.title}</h2>
        <div className={styles.where}>
          <LocatorMap outlines={outlines} areaId={area.area_id} name={name} />
          <div>
            <h3 className={styles.small}>{AREA.where.neighbours}</h3>
            {data.neighbours.length > 0 ? (
              <ul className={styles.neighbours}>
                {data.neighbours.map((neighbour) => (
                  <li key={neighbour.area_id}>
                    <Link className="target-min" href={paths.area(neighbour)} prefetch={false}>
                      {neighbour.name}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p>{AREA.where.noNeighbours}</p>
            )}
          </div>
        </div>
      </section>

      <section className={styles.part} aria-labelledby={SECTION.stations}>
        <h2 id={SECTION.stations}>{AREA.stations.title}</h2>
        {stations.length > 0 ? <Rows facts={stations} /> : <p>{AREA.stations.none}</p>}
      </section>

      <section className={styles.part} aria-labelledby={SECTION.cost}>
        <h2 id={SECTION.cost}>{AREA.cost.title}</h2>
        <p className={styles.lead}>{AREA.cost.lead}</p>
        <p>
          <Link className="target-min" href={paths.methods("confidence")} prefetch={false}>
            {AREA.cost.confidence}
          </Link>
        </p>
        <Cost data={data} tenure="rent" />
        <Cost data={data} tenure="buy" />
      </section>

      <section className={styles.part} aria-labelledby={SECTION.features}>
        <h2 id={SECTION.features}>{AREA.features.title}</h2>
        <p className={styles.lead}>{AREA.features.lead}</p>
        {groups.map((group) => (
          <div key={group.dimension} className={styles.part}>
            <h3>{DIMENSION[group.dimension]}</h3>
            <ul className={styles.rows}>
              {group.rows.map(({ metric, fact }) => (
                <li key={metric.feature_id}>
                  {fact ? (
                    <FactRow fact={fact} source="line" />
                  ) : (
                    <NoFigure name={metric.label} says={AREA.features.noFigure} />
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      <section className={styles.part} aria-labelledby={SECTION.tags}>
        <h2 id={SECTION.tags}>{AREA.tags.title}</h2>
        <p className={styles.lead}>{AREA.tags.lead}</p>
        <ul className={styles.rows}>
          {tags.map(({ tag, fact }) => (
            <li key={tag.tag_id}>
              {fact ? (
                <FactRow fact={fact} source="line" />
              ) : (
                <NoFigure name={tag.label} says={AREA.tags.noFigure} />
              )}
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.part} aria-labelledby={SECTION.sources}>
        <h2 id={SECTION.sources}>{AREA.sources.title}</h2>
        <p className={styles.lead}>{AREA.sources.lead}</p>
        <ul className={styles.sources}>
          {sources.map((source) => (
            <li key={source.source_id}>
              <Link className="target-min" href={paths.sources(source.source_id)} prefetch={false}>
                {source.name}
              </Link>
            </li>
          ))}
        </ul>
        <p>
          <Link className="target-min" href={paths.methods()}>
            {AREA.methods}
          </Link>
        </p>
      </section>

      <p className={styles.back}>
        <Link className="target" href={paths.home()}>
          {AREA.search}
        </Link>
      </p>
    </article>
  );
}
