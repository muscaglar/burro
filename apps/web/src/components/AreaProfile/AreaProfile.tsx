import Link from "next/link";
import type { ReactNode } from "react";

import { AREA, LOOK, NAMED } from "@/content/area";
import { ruleIn } from "@/content/crime";
import { DIMENSION } from "@/content/labels";
import { sentenceOf } from "@/content/templates";
import type { AreaData, AreaSummary, Fact, GeometryData, MetaData, Tenure, VibeBands } from "@/lib/api/schema";
import { saidOfTheName } from "@/lib/area/named";
import { cannotSee, nearestStation, portraitOf, shownOn } from "@/lib/area/portrait";
import {
  alikeRows,
  areaFact,
  costFacts,
  factsShown,
  featuresByDimension,
  sharedVibes,
  stationFacts,
} from "@/lib/area/profile";
import { sourcesOf } from "@/lib/facts";
import { paths, type AreaPart } from "@/lib/paths";

import { CensusPanel } from "../CensusPanel/CensusPanel";
import { CENSUS_PART } from "../CensusPanel/part";
import { CompareButton } from "../CompareTray/CompareButton";
import { CompareTray } from "../CompareTray/CompareTray";
import { FactRow } from "../FactRow/FactRow";
import { IncomePanel } from "../IncomePanel/IncomePanel";
import { INCOME_PART } from "../IncomePanel/part";
import { LocatorMap } from "../LocatorMap/LocatorMap";
import { Portrait } from "../Portrait/Portrait";
import { SourceLine } from "../SourceLine/SourceLine";
import styles from "./AreaProfile.module.css";
import { OpenAtLink } from "./OpenAtLink";
import { SearchForThis } from "./SearchForThis";
import { YourJourneys } from "./YourJourneys";

interface Props {
  /** The area's profile, from route 6. */
  readonly data: AreaData;
  /**
   * The features and the vibes of the release, from route 11: their names, and what each is
   * about. And whether census figures are served, with the words of the block that offers them,
   * and the same of household income.
   */
  readonly meta: Pick<MetaData, "features" | "tags"> & Partial<Pick<MetaData, "census" | "income" | "counts">>;
  /** The boundary of every area, from route 5. */
  readonly geometry: GeometryData;
  /** Every area of the release, from route 4: the address of each area that is like this one. */
  readonly areas: readonly Pick<AreaSummary, "area_id" | "slug" | "name">[];
  /** The band of every area on every vibe, from route 4: what this area shares with one that is like it. */
  readonly bands?: readonly VibeBands[];
}

const LIST = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

/** The part a result leads to by "More like this": `paths.area` names it. */
const ALIKE: AreaPart = "alike";

/** The ids of the parts, which the list of contents links to. They name parts of the page, never a place. */
const SECTION = {
  where: "where",
  cost: "cost",
  features: "measured",
  sources: "sources",
  look: "look",
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

interface ClosedProps {
  readonly id: string;
  readonly title: string;
  readonly children: ReactNode;
}

/**
 * A part of the page that is closed until it is pressed, under a heading of
 * its own. It is the browser's own element, so it opens with scripts off, and
 * what it holds is in the page either way. A link that names it opens it.
 */
function Closed({ id, title, children }: ClosedProps) {
  return (
    <OpenAtLink id={id} className={styles.closed} summary={<h2 className={styles.opensTo}>{title}</h2>}>
      <div className={styles.part}>{children}</div>
    </OpenAtLink>
  );
}

/**
 * One area's page. It opens with the portrait: what the area is like in
 * short, where it is, and then where it sits on each vibe. Under it is the
 * list of what else the page holds, each one press away: the areas most like
 * it, what homes cost, every figure the release holds for it, the sources,
 * and the census figures of who lived there. It ends with where to go and
 * look, and what no vibe can see.
 *
 * Every figure is a fact of the API's, shown as it came, with its source and
 * its date written out under it. The page is drawn on the server and reads
 * with scripts off: what opens is the browser's own element. The parts that
 * need a script are the buttons that put the area among those to compare and
 * that start a search from it, and the census figures, which are asked for
 * when their part is opened.
 */
export function AreaProfile({ data, meta, geometry, areas, bands = [] }: Props) {
  const { area } = data;
  const named = areaFact(data);
  // The name and the borough are the fact's, where there is one: it carries their source.
  const name = named?.slots.name ?? area.name;
  const borough = named?.slots.borough ?? area.borough;
  const said = named === null ? null : saidOfTheName(named);
  const stations = stationFacts(data);
  const nearest = nearestStation(data);
  // A release may name no station for any area. No area is then said to have none near it:
  // that is so of the data, and a vibe of the same page may give how far the nearest one is.
  const namesStations = meta.counts === undefined || meta.counts.stations > 0;
  const nearestSaid = nearest === null ? null : sentenceOf(nearest);
  const groups = featuresByDimension(data, meta.features);
  const alike = alikeRows(data, areas);
  const sources = sourcesOf(factsShown(data, meta));
  const portrait = portraitOf(data, meta);
  const unseen = cannotSee(
    shownOn(portrait).map((mark) => mark.tag),
    meta.tags,
  );
  const here = { area_id: area.area_id, slug: area.slug, name };
  // Offered only where the service serves one. The words are the API's, and hold no figure.
  const census = meta.census?.available === true ? meta.census : null;
  const income = meta.income?.available === true ? meta.income : null;

  return (
    <article className={styles.profile} aria-labelledby="area-name">
      <header className={styles.head}>
        <div className={styles.named}>
          <h1 id="area-name">{name}</h1>
          <div className={styles.under}>
            <dl className={styles.borough}>
              <div>
                <dt>{AREA.borough}</dt>
                <dd>{borough}</dd>
              </div>
              {/* The label its publisher gives the area, and what is known of the name it
                  bears: who wrote it, and whether a person has checked it. Each is the fact's. */}
              {named?.slots.label ? (
                <div>
                  <dt>{NAMED.label}</dt>
                  <dd>{named.slots.label}</dd>
                </div>
              ) : null}
              {said !== null ? (
                <div>
                  <dt>{NAMED.name}</dt>
                  <dd>
                    {said}{" "}
                    <Link className="target-min" href={paths.methods("names")} prefetch={false}>
                      {NAMED.how}
                    </Link>
                  </dd>
                </div>
              ) : null}
            </dl>
            {named ? <SourceLine facts={[named]} /> : null}
          </div>
        </div>
        <div className={styles.compare} role="group" aria-label={AREA.compare}>
          {/* Only what the button needs is handed to the browser. The tray is at the foot of the screen. */}
          <CompareButton area={here} />
        </div>
        {area.rankable ? null : <p className={styles.notRanked}>{AREA.notRanked}</p>}
      </header>

      <Portrait
        data={data}
        meta={meta}
        besideShort={
          // Where the area is: what is beside it, its nearest station, and how long it takes
          // to the places of the search that is open. It is a group of the portrait, and no
          // landmark of its own.
          <div className={styles.whereShort} role="group" aria-labelledby={SECTION.where}>
            <h3 id={SECTION.where}>{AREA.where.title}</h3>
            <div className={styles.where}>
              <LocatorMap geometry={geometry} areaId={area.area_id} name={name} />
              <div className={styles.whereSaid}>
                <p className={styles.small} id={`${SECTION.where}-beside`}>
                  {AREA.where.neighbours}
                </p>
                {data.neighbours.length > 0 ? (
                  <ul className={styles.neighbours} aria-labelledby={`${SECTION.where}-beside`}>
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
            {nearest !== null && nearestSaid !== null ? (
              <div className={styles.station}>
                <p>{nearestSaid}</p>
                <SourceLine facts={[nearest]} />
              </div>
            ) : (
              <p>{namesStations ? AREA.where.noStation : AREA.where.noStations}</p>
            )}
            <YourJourneys areaId={area.area_id} />
          </div>
        }
        underMore={
          <SearchForThis
            vibes={portrait.more.map(({ tag }) => ({ tag_id: tag.tag_id, label: tag.label }))}
          />
        }
      />

      {/* The portrait comes first. What else the page holds is listed under it. */}
      <nav className={styles.contents} aria-label={AREA.contents}>
        <ul>
          {(
            [
              [ALIKE, AREA.alike.open],
              [SECTION.cost, AREA.cost.title],
              [SECTION.features, AREA.features.title],
              [SECTION.sources, AREA.sources.title],
              ...(census === null ? [] : ([[CENSUS_PART, census.heading]] as const)),
              ...(income === null ? [] : ([[INCOME_PART, income.heading]] as const)),
              [SECTION.look, LOOK.title],
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

      <div className={styles.closedParts}>
        {/* Closed until it is pressed, or come to by a link: "More like this" on a result leads here. */}
        <Closed id={ALIKE} title={AREA.alike.open}>
          <h3 className={styles.small}>{AREA.alike.title}</h3>
          {alike.length > 0 ? (
            <>
              <p className={styles.lead}>{AREA.alike.lead}</p>
              {/* In the order the API gives them, which is the most alike first. */}
              <ol className={styles.alike}>
                {alike.map(({ area: other, fact }) => {
                  const shared = other === null ? [] : sharedVibes(area.area_id, other.area_id, bands, meta);
                  return (
                    <li key={fact.fact_id}>
                      <p className={styles.name}>
                        {other === null ? (
                          (fact.slots.other ?? fact.label)
                        ) : (
                          // The name leads to the area's own page. It starts no search.
                          <Link className="target-min" href={paths.area(other)} prefetch={false}>
                            {other.name}
                          </Link>
                        )}
                      </p>
                      {/* What the API says of the two, in the contract's own sentence. */}
                      <p>{sentenceOf(fact)}</p>
                      {other === null ? null : (
                        <p>
                          {shared.length > 0
                            ? `${AREA.alike.shares}: ${LIST.format(shared.map((tag) => tag.label))}.`
                            : AREA.alike.sharesNone}
                        </p>
                      )}
                      <SourceLine facts={[fact]} />
                      {other === null ? null : (
                        <p className={styles.beside}>
                          {/* How the two differ, vibe by vibe, is the comparison's to show. */}
                          <Link
                            className="target-min"
                            href={paths.compare([area.slug, other.slug])}
                            prefetch={false}
                          >
                            {AREA.alike.compare(name, other.name)}
                          </Link>
                        </p>
                      )}
                    </li>
                  );
                })}
              </ol>
            </>
          ) : (
            <p>{AREA.alike.none}</p>
          )}
        </Closed>

        <Closed id={SECTION.cost} title={AREA.cost.title}>
          {/* What the two figures of a range mean is said where there is a range to read. */}
          {data.facts.some((fact) => fact.template === "cost_rent" || fact.template === "cost_buy") ? (
            <>
              <p className={styles.lead}>{AREA.cost.lead}</p>
              <p>
                <Link className="target-min" href={paths.methods("confidence")} prefetch={false}>
                  {AREA.cost.confidence}
                </Link>
              </p>
            </>
          ) : null}
          <Cost data={data} tenure="rent" />
          <Cost data={data} tenure="buy" />
        </Closed>

        <Closed id={SECTION.features} title={AREA.features.title}>
          <p className={styles.lead}>{AREA.features.lead}</p>
          {/* A release holds a hundred measures, and a person came for a few of them. Each
              group is closed under its own name, in the browser's own element, so that the
              part opens to the names of its groups and not to every row of them all. */}
          {groups.map((group) => (
            <details key={group.dimension} className={styles.group}>
              <summary className="target">
                <h3>{DIMENSION[group.dimension]}</h3>
              </summary>
              {/* When recorded crime counts, as every page says it. */}
              {group.dimension === "crime" ? <p className={styles.lead}>{ruleIn(meta)}</p> : null}
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
            </details>
          ))}
        </Closed>

        <Closed id={SECTION.sources} title={AREA.sources.title}>
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
        </Closed>

        {/*
          Who lived here, at the census. It comes after every figure of the place and stands
          beside none of them. Only the slug is handed on: the figures are not in the page,
          and are asked for when it is opened.
        */}
        {census === null ? null : <CensusPanel offer={census} area={{ slug: area.slug }} />}
        {/*
          What the households here are estimated to have as income. It stands where the census
          does and is asked for as it is: the figure is not in the page, and is handed to nothing.
        */}
        {income === null ? null : <IncomePanel offer={income} area={{ slug: area.slug }} />}
      </div>

      <section className={styles.part} aria-labelledby={SECTION.look}>
        <h2 id={SECTION.look}>{LOOK.title}</h2>
        <p className={styles.lead}>{LOOK.lead}</p>
        <div className={styles.look}>
          {/* With no station in the data there is none to start from, and the part is left out. */}
          {namesStations ? (
            <div className={styles.part}>
              <h3 className={styles.small}>{LOOK.start}</h3>
              {stations.length > 0 ? <Rows facts={stations} /> : <p>{LOOK.noStation}</p>}
            </div>
          ) : null}
          {unseen.own.length > 0 ? (
            <div className={styles.part}>
              <h3 className={styles.small}>{LOOK.cannotSee}</h3>
              <p className={styles.lead}>{LOOK.cannotSeeLead}</p>
              {/* What every vibe cannot see is said once. Every line is the API's, word for word. */}
              {unseen.common.map((line) => (
                <p key={line}>{line}</p>
              ))}
              {/* A release holds fourteen vibes, and each cannot see four things or five. The
                  list is one press away, in the browser's own element. */}
              <details className={styles.group}>
                <summary className="target">{LOOK.cannotSeeEach}</summary>
                <dl className={styles.unseen}>
                  {unseen.own.map(({ tag, lines }) => (
                    <div key={tag.tag_id}>
                      <dt>{tag.label}</dt>
                      <dd>
                        <ul>
                          {lines.map((line) => (
                            <li key={line}>{line}</li>
                          ))}
                        </ul>
                      </dd>
                    </div>
                  ))}
                </dl>
                <p>
                  <Link className="target-min" href={paths.vibes()}>
                    {LOOK.vibes}
                  </Link>
                </p>
              </details>
            </div>
          ) : null}
        </div>
      </section>

      <p className={styles.back}>
        <Link className="target" href={paths.home()}>
          {AREA.search}
        </Link>
      </p>

      {/* It takes no room until an area is chosen, and then stays at the foot of the screen. */}
      <CompareTray />
    </article>
  );
}
