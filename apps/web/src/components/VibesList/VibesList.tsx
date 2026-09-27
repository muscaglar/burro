import Link from "next/link";
import type { ReactNode } from "react";

import { askingFor, CRIME_ACCOUNT, crimeParts } from "@/content/crime";
import { CASE_LINES, OTHER_NAMES, type OtherName } from "@/content/names";
import { CRIME_CAVEAT } from "@/content/settings";
import { VIBES } from "@/content/vibes";
import type { AreaSummary, BandMark, GeometryData, MetaData, Metric, Tag, VibeBands } from "@/lib/api/schema";
import { readableDate } from "@/lib/format";
import { recipeOf } from "@/lib/holds";
import { paths } from "@/lib/paths";
import { endsOf, isRange, readingOf, VIBE_BANDS } from "@/lib/vibes";

import { Board, Boxed, Part, Points, Sourced } from "../About/About";
import { Fold } from "../About/Fold";
import { Ends } from "../kit/Ends/Ends";
import { Frame } from "../kit/Frame/Frame";
import { Thing } from "../kit/Thing/Thing";
import { outlinesOf, type Outline } from "../LocatorMap/LocatorMap";
import { SharedOutlines, VIBE_MAP_FRAME, VibeMap } from "../VibeMap/VibeMap";
import styles from "./VibesList.module.css";

type Area = Pick<AreaSummary, "area_id" | "slug" | "name">;

interface Props {
  /** The release, from route 11: its vibes, the features their recipes are made of, and the sources. */
  readonly meta: Pick<MetaData, "tags" | "features" | "attributions" | "families" | "recipes">;
  /** Every area of the release, from route 4: its name, and the address of its page. */
  readonly areas?: readonly Area[];
  /** The band of every area on every vibe, from route 4. */
  readonly bands?: readonly VibeBands[];
  /** The boundary of every area, from route 5. */
  readonly geometry?: GeometryData | null;
  /** The other names weighed for a vibe, by its id. They change nothing the engine does. */
  readonly names?: Readonly<Record<string, readonly OtherName[]>>;
}

const LIST = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

function SourceLinks({ ids, names }: { readonly ids: readonly string[]; readonly names: ReadonlyMap<string, string> }) {
  return (
    <Sourced>
      {ids.map((id) => (
        <li key={id}>
          {/* Which source a person went on to read is not told to anyone ahead of time. */}
          <Link className="target-min" href={paths.sources(id)} prefetch={false}>
            {names.get(id) ?? id}
          </Link>
        </li>
      ))}
    </Sourced>
  );
}

interface CellProps {
  /** The heading of the column, which the cell says for itself where the rows are stacked. */
  readonly name: string;
  readonly number?: boolean;
  readonly children: ReactNode;
}

/** One thing said of a part. Stacked, it says what it is: the heading of its column is then not drawn. */
function Cell({ name, number = false, children }: CellProps) {
  return (
    // The role is the cell's own, said again because a narrow screen stacks the rows. The
    // rule takes any cell for one of a grid that can be pressed, which this is not.
    // eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role
    <td role="cell" className={number ? styles.number : undefined}>
      {/* The column's heading says it to a screen reader, so this is kept from one. */}
      <span className={styles.cellName} aria-hidden="true">
        {name}
      </span>
      <span>{children}</span>
    </td>
  );
}

/** One part of a recipe, with what the release says of it and the other recipes that hold it. */
interface Part {
  readonly term: Tag["terms"][number];
  readonly metric: Metric | null;
  readonly alsoIn: readonly Tag[];
}

/**
 * What the id of each outline of the page begins with, where it is drawn once for all its
 * maps. One letter: every map writes it once for every area.
 */
const OUTLINES = "o";
/** The most areas an end names where it stands. With more, it says how many, and they are named below. */
export const NAMED_AT_AN_END = 12;

/** A sitting at one point of a vibe: a band, and no range. A mixed area sits at no one point. */
const sitsIn = (mark: BandMark, band: number): boolean =>
  mark.band === band &&
  mark.spread_low !== null &&
  mark.spread_high !== null &&
  !isRange({ band, spread_low: mark.spread_low, spread_high: mark.spread_high });

interface NamedProps {
  readonly id: string;
  readonly title: string;
  readonly areas: readonly Area[];
  /**
   * The most areas to name here. With more, how many there are is said in their place:
   * they are named one press away, band by band. An end of a release of a thousand areas
   * named two hundred of them, and the page was thirty-eight screens long.
   */
  readonly most?: number;
}

/** Some areas, by name, under what is true of them. Each name is one press from the area's page. */
function Named({ id, title, areas, most = Infinity }: NamedProps) {
  return (
    <div className={styles.end} role="group" aria-labelledby={id}>
      <p className={styles.endName} id={id}>
        {title}
      </p>
      {areas.length === 0 ? (
        <p className={styles.noArea}>{VIBES.found.none}</p>
      ) : areas.length > most ? (
        <p className={styles.noArea}>{VIBES.found.many(areas.length)}</p>
      ) : (
        <ul className={styles.areas}>
          {areas.map((area) => (
            <li key={area.area_id}>
              {/* Which area a person reads next is told to no server ahead of time. */}
              <Link className="target-min" href={paths.area(area)} prefetch={false}>
                {area.name}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

interface VibeProps {
  readonly tag: Tag;
  readonly meta: Props["meta"];
  readonly sourceNames: ReadonlyMap<string, string>;
  readonly areas: readonly Area[];
  readonly marks: readonly BandMark[] | null;
  readonly outlines: readonly Outline[];
  readonly weighed: readonly OtherName[];
}

/**
 * One vibe, in short, laid out as every other is: the drawing of its thing, its name, what
 * it means, and the small map of the city coloured by it. Under the map is its gauge: the
 * five shades of the map between its two ends, each end with its one picture and its name.
 * The two pictures are opposites, and neither end is the better one. A vibe that counts
 * recorded crime says so on its face, in sight.
 *
 * A vibe whose map is not drawn has no gauge to stand its ends at, and has them under what
 * it means.
 *
 * How Burro works the vibe out is one fold under it, closed until it is pressed: what goes
 * into it, with the share, the period and the source of each part, what it cannot see, and
 * where it is found, band by band. Nothing of it is lost.
 *
 * It stands in a box of its own. The drawing before its name is chosen by the id and the
 * family the API gives the vibe, and falls to the plain one. The drawings are for the eye:
 * the name and the sentence are read.
 */
function Vibe({ tag, meta, sourceNames, areas, marks, outlines, weighed }: VibeProps) {
  const { recipe, found, cannotSee } = VIBES;
  const [low, high] = endsOf(tag);
  const scale = tag.low_end !== null && tag.high_end !== null;
  const parts: readonly Part[] = tag.terms.map((term) => ({
    term,
    metric: meta.features.find((one): one is Metric => one.feature_id === term.feature_id) ?? null,
    // The other recipes that hold the same part, by the names the API gives them.
    alsoIn: meta.tags.filter(
      (other) => other.tag_id !== tag.tag_id && other.terms.some((one) => one.feature_id === term.feature_id),
    ),
  }));
  const sources = [...new Set(parts.flatMap((part) => part.metric?.source_ids ?? []))];
  const family = meta.families.find((one) => one.family === tag.family);
  const crime = crimeParts(tag, meta.features);
  const heading = `${tag.tag_id}-name`;
  const byId = new Map(areas.map((area) => [area.area_id, area]));
  const named = (wanted: (mark: BandMark) => boolean): readonly Area[] =>
    (marks ?? []).filter(wanted).flatMap((mark) => byId.get(mark.area_id) ?? []);
  const held = recipeOf(meta, tag.tag_id);
  // A vibe the API says nothing of is drawn as it was.
  const placed = held?.placed ?? true;
  const unplaced = placed ? named((mark) => mark.band === null) : [];
  /** The name the API gives a part this data does not carry, where it gives one. */
  const waitedFor = (featureId: string) => held?.waits_on.find((part) => part.feature_id === featureId)?.label;
  // The map of a vibe is drawn where an area is placed on it and its bands and the boundaries came.
  const mapped = placed && marks !== null && outlines.length > 0;
  return (
    // A name of the key leads here: the vibe takes the focus then, and is reached by no key of its own.
    <Frame kind="box" as="section" bare id={tag.tag_id} className={styles.vibe} aria-labelledby={heading} tabIndex={-1}>
      <div className={styles.named}>
        <div className={styles.nameLine}>
          {/* The drawing is dress. The name beside it is the API's, and is what the heading says. */}
          <Thing kind="tag" id={tag.tag_id} family={tag.family} />
          {/* It is headed by what is said over the vibes, and heads what its fold holds. */}
          <h3 id={heading}>{tag.label}</h3>
        </div>
        <p className={styles.meaning}>{tag.meaning}</p>
        {mapped ? null : (
          // Its two ends, each with its picture, the low end first as it is wherever a band is
          // drawn: with no map there is no gauge for them to stand at the ends of.
          <p className={styles.ends} data-ends={scale ? "scale" : "one-way"}>
            <span className="visually-hidden">{VIBES.between} </span>
            <Ends id={tag.tag_id} low={tag.low_end} high={tag.high_end}>
              {/* The spaces are for whoever hears the page: the three are laid out apart. */}
              <span className={styles.between} data-between>
                {" "}
                {VIBES.to}{" "}
              </span>
            </Ends>
          </p>
        )}
      </div>

      <figure className={styles.figure}>
        {!placed ? (
          // A map of a vibe that no area is placed on is a map of dots, and says nothing.
          <p className={styles.noArea}>{VIBES.map.notYet}</p>
        ) : marks === null || outlines.length === 0 ? (
          <p className={styles.noArea}>{VIBES.map.none}</p>
        ) : (
          <>
            <VibeMap
              outlines={outlines}
              marks={marks}
              title={VIBES.map.title(tag.label, low, high)}
              shared={OUTLINES}
            />
            <figcaption>
              {/*
                The gauge of the vibe: five swatches from the low end to the high, between
                its two ends, each with its one picture and its name. It is for the eye. The
                name of the map says the same to whoever hears the page.
              */}
              <span className={styles.legend} aria-hidden="true">
                <Ends id={tag.tag_id} low={tag.low_end} high={tag.high_end}>
                  <span className={styles.swatches}>
                    {VIBE_BANDS.map((band) => (
                      <span key={band} className={styles.swatch} data-band={band} />
                    ))}
                  </span>
                </Ends>
              </span>
            </figcaption>
          </>
        )}
      </figure>

      {/*
        What the vibe says of itself, across its box, in sight: that it counts recorded
        crime. It takes no room where a vibe does not.
      */}
      <div className={styles.said}>
        {crime.length === 0 ? null : (
          // One account of when recorded crime counts, as every page says it.
          <div className={styles.crime} data-counts="recorded-crime">
            <p>
              {CRIME_ACCOUNT.counts}: {LIST.format(crime.map((part) => part.label))}.
            </p>
            <p>
              {CRIME_ACCOUNT.rule} {askingFor(tag)}
            </p>
            <p>{CRIME_CAVEAT}</p>
          </div>
        )}
      </div>

      <Fold says={VIBES.works} of={tag.label} className={styles.works}>
        <div className={styles.worked}>
          <div className={styles.recipe}>
            <Board as="h4">{recipe.title}</Board>
            <p>{recipe.lead}</p>
            {/* How much of the recipe the data holds, as one number. It was given part by part, and never added up. */}
            {held === undefined ? null : (
              <p className={styles.held}>{held.held === 100 ? VIBES.whole : VIBES.held(held.held, held.needed)}</p>
            )}
            {/*
              Each part is stacked: its name, and under it each thing said of it, by name. It is
              one table either way, so every part of it says its role again: laid out as blocks,
              a browser may forget that a table is one.
            */}
            <table role="table" className={styles.table}>
              <caption>{recipe.caption(tag.label)}</caption>
              {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
              <thead role="rowgroup" className={styles.head}>
                <tr role="row">
                  <th role="columnheader" scope="col">
                    {recipe.columns.part}
                  </th>
                  <th role="columnheader" scope="col">
                    {recipe.columns.reading}
                  </th>
                  <th role="columnheader" scope="col" className={styles.number}>
                    {recipe.columns.share}
                  </th>
                  <th role="columnheader" scope="col">
                    {recipe.columns.period}
                  </th>
                  <th role="columnheader" scope="col">
                    {recipe.columns.sources}
                  </th>
                </tr>
              </thead>
              {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
              <tbody role="rowgroup">
                {parts.map(({ term, metric, alsoIn }) => (
                  <tr role="row" key={term.feature_id} className={styles.row}>
                    <th role="rowheader" scope="row">
                      {/* A part the release does not carry is named as the API names it, and said
                          to be missing. It is never shown by its code. */}
                      <span>{metric?.label ?? waitedFor(term.feature_id) ?? recipe.notCarried}</span>
                      {metric === null ? <span className={styles.waits}>{recipe.waits}</span> : null}
                    </th>
                    <Cell name={recipe.columns.reading}>
                      {readingOf(tag, term.reading)}
                      {alsoIn.length > 0 ? `. ${recipe.alsoIn(LIST.format(alsoIn.map((other) => other.label)))}` : null}
                    </Cell>
                    <Cell name={recipe.columns.share} number>
                      {recipe.share(term.hundredths)}
                    </Cell>
                    <Cell name={recipe.columns.period}>
                      {metric === null ? recipe.noPeriod : readableDate(metric.vintage)}
                    </Cell>
                    <Cell name={recipe.columns.sources}>
                      {metric === null ? null : <SourceLinks ids={metric.source_ids} names={sourceNames} />}
                    </Cell>
                  </tr>
                ))}
              </tbody>
            </table>
            <div role="group" aria-label={VIBES.sources}>
              <p className={styles.endName}>{VIBES.sources}</p>
              {sources.length > 0 ? <SourceLinks ids={sources} names={sourceNames} /> : <p>{VIBES.noSources}</p>}
            </div>
          </div>

          <div className={styles.cannotSee} role="group" aria-label={cannotSee.title}>
            <Board as="h4">{cannotSee.title}</Board>
            <p>{cannotSee.lead}</p>
            <ul className={styles.cannot}>
              {tag.cannot_see.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>

          <div className={styles.found}>
            <Board as="h4">{found.title}</Board>
            {!placed ? (
              // It is found nowhere yet. Every area was once named here, under "Burro cannot place".
              <p className={styles.noArea}>{VIBES.map.notYet}</p>
            ) : marks === null ? (
              <p className={styles.noArea}>{VIBES.map.none}</p>
            ) : (
              <>
                <p>{found.lead}</p>
                {/* The high end first, as the vibe is named for it, and then the low. */}
                <Named
                  id={`${tag.tag_id}-high`}
                  title={scale ? found.end(high) : found.most}
                  areas={named((mark) => sitsIn(mark, 5))}
                  most={NAMED_AT_AN_END}
                />
                <Named
                  id={`${tag.tag_id}-low`}
                  title={scale ? found.end(low) : found.least}
                  areas={named((mark) => sitsIn(mark, 1))}
                  most={NAMED_AT_AN_END}
                />
                {/* A release of London names a thousand areas: they are one press further. */}
                <Fold says={found.every} of={tag.label} kind="line">
                  <div className={styles.every} role="group" aria-label={found.every}>
                    {[...VIBE_BANDS].reverse().map((band) => (
                      <Named
                        key={band}
                        id={`${tag.tag_id}-band-${band}`}
                        title={found.band(band)}
                        areas={named((mark) => mark.band === band)}
                      />
                    ))}
                    {unplaced.length === 0 ? null : (
                      <Named id={`${tag.tag_id}-unplaced`} title={found.unplaced} areas={unplaced} />
                    )}
                  </div>
                </Fold>
              </>
            )}
          </div>

          {family === undefined && tag.shelf_word === null ? null : (
            <dl className={styles.facts}>
              {family === undefined ? null : (
                <div>
                  <dt>{VIBES.facts.family}</dt>
                  <dd>{family.label}</dd>
                </div>
              )}
              {tag.shelf_word === null ? null : (
                <div>
                  <dt>{VIBES.facts.word}</dt>
                  <dd>{tag.shelf_word}</dd>
                </div>
              )}
            </dl>
          )}

          {/* The room for the case for other names. It is drawn only where a name is set down. */}
          {weighed.length === 0 ? null : (
            <div className={styles.weighed} role="group" aria-labelledby={`${tag.tag_id}-names`}>
              <p className={styles.endName} id={`${tag.tag_id}-names`}>
                {VIBES.names.title}
              </p>
              <dl>
                {weighed.map((other) => (
                  <div key={other.name}>
                    <dt>{other.name}</dt>
                    <dd>
                      {other.lines.slice(0, CASE_LINES).map((line) => (
                        <p key={line}>{line}</p>
                      ))}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </div>
      </Fold>
    </Frame>
  );
}

/**
 * Every vibe of the release, in short, each laid out as the next is: its drawing, its
 * name, what it means, and the city coloured by it. How Burro works a vibe out is one fold
 * under it. Every word about a vibe is the API's, from route 11, and every band from route
 * 4, so the page holds no vibe of its own and can never disagree with the engine.
 *
 * What is true of every vibe is said once, over them. How an area is placed on a vibe is
 * one fold at the foot, closed until it is pressed.
 *
 * It is drawn on the server and reads with scripts off. What is one press away is the
 * browser's own element.
 *
 * Each part of it is a box of its own, for a page that stands on the meadow.
 */
export function VibesList({ meta, areas = [], bands, geometry = null, names = OTHER_NAMES }: Props) {
  const sourceNames = new Map(meta.attributions.map((source) => [source.source_id, source.name]));
  // The outline of every area is worked out once: every map draws every area.
  const outlines = geometry === null ? [] : outlinesOf(geometry, VIBE_MAP_FRAME);
  return (
    <>
      {/* The outline of every area, once for the page. Each map points at it. */}
      <SharedOutlines outlines={outlines} id={OUTLINES} />
      {meta.tags.length === 0 ? null : (
        <Part id="vibes" title={VIBES.each.title}>
          <p>{VIBES.each.lead}</p>
          <p>{VIBES.each.residents}</p>
          <p>{VIBES.each.more}</p>
        </Part>
      )}
      <div className={styles.vibes}>
        {meta.tags.map((tag) => (
          <Vibe
            key={tag.tag_id}
            tag={tag}
            meta={meta}
            sourceNames={sourceNames}
            areas={areas}
            marks={bands?.find((one) => one.tag_id === tag.tag_id)?.marks ?? null}
            outlines={outlines}
            weighed={names[tag.tag_id] ?? []}
          />
        ))}
      </div>
      <Fold says={VIBES.how.title} kind="ground" id="how">
        <Boxed>
          <Points points={VIBES.how.points} />
          <p>
            <Link className="target-min" href={paths.methods()}>
              {VIBES.methods}
            </Link>
          </p>
        </Boxed>
      </Fold>
    </>
  );
}
