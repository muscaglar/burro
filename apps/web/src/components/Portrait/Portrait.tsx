import Link from "next/link";
import type { ReactNode } from "react";

import { PORTRAIT } from "@/content/area";
import { RESTS_ON, restsOnWords } from "@/content/bands";
import { askingFor, CRIME_ACCOUNT } from "@/content/crime";
import { FACT_COLUMNS } from "@/content/facts";
import { STRIP } from "@/content/search";
import type { AreaData, Fact } from "@/lib/api/schema";
import {
  GROUPS,
  inShort,
  portraitOf,
  restsOn,
  shownOn,
  type Form,
  type Group,
  type MarkRow,
  type PartRow,
  type RestsOn,
} from "@/lib/area/portrait";
import { paths } from "@/lib/paths";
import { endsOf, inWords, isRange, plainly, readingOf } from "@/lib/vibes";

import { FactRow } from "../FactRow/FactRow";
import { SourceLine } from "../SourceLine/SourceLine";
import { Track } from "../Track/Track";
import styles from "./Portrait.module.css";

interface Props {
  /** The area's profile, from route 6. It holds the portrait and every fact the portrait names. */
  readonly data: AreaData;
  /** The vibes and the features of the release, from route 11: their names, ends and recipes. */
  readonly meta: Form;
  /** What stands beside what the area is like, in short: where it is. */
  readonly besideShort?: ReactNode;
  /** What stands under the vibes the area has more of than most, where there is anything to. */
  readonly underMore?: ReactNode;
}

/** The id of the portrait's heading, which the list of contents links to. */
export const PORTRAIT_ID = "character";
/** The id of the heading over the vibes that cannot place the area, which the summary leads to. */
export const UNPLACED_ID = `${PORTRAIT_ID}-unplaced`;

/** The lists whose vibes say a figure beside them. A scale says its two ends. */
const WITH_FIGURE: readonly Group[] = ["more", "less", "others"];

const LIST = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

/**
 * Which parts of a recipe have no figure for the area, in one line: each by the name the API
 * gives it, as it came. A part this data does not carry at all is named too, and said to be
 * what the vibe waits on. One the API gives no name for is counted.
 */
function Without({ rests }: { readonly rests: RestsOn }) {
  const named = [
    ...rests.missing,
    ...rests.waiting.map((name) => RESTS_ON.waits(name)),
    ...(rests.notCarried > 0 ? [RESTS_ON.notCarried(rests.notCarried)] : []),
  ];
  return (
    <p className={styles.says}>
      {RESTS_ON.without}:{" "}
      {named.map((name, at) => (
        <span key={name}>
          {at > 0 ? "; " : null}
          <span>{name}</span>
        </span>
      ))}
    </p>
  );
}

interface FigureProps {
  readonly fact: Fact;
  readonly className?: string;
  /** True where what stands before it ends in a full stop of its own. */
  readonly afterStop?: boolean;
}

/** A figure of one part of a vibe, under that part's own name. Both are the API's. */
function Figure({ fact, className, afterStop = false }: FigureProps) {
  if (fact.slots.value === undefined) return null;
  return (
    <span className={className}>
      <span className="visually-hidden">{afterStop ? " " : ". "}</span>
      {fact.label}: <span className={styles.value}>{fact.slots.value}</span>
    </span>
  );
}

/** One part of a recipe: its share, how it is read, and the area's figure for it with its source and date. */
function Part({ part, mark }: { readonly part: PartRow; readonly mark: MarkRow }) {
  const { madeOf } = PORTRAIT;
  const share = [madeOf.share, madeOf.shareOf(part.term.hundredths)] as const;
  if (part.metric === null || part.fact === null) {
    // A part with no figure says so. A part this data does not carry is named as the API
    // names it, and is never shown by its code. Nothing is filled in for either.
    const name = part.metric?.label ?? part.waits ?? madeOf.notCarried;
    return (
      <div className={styles.noFigure} role="group" aria-label={name}>
        <p className={styles.partName}>{name}</p>
        <dl className={styles.columns}>
          <div>
            <dt>{share[0]}</dt>
            <dd>{share[1]}</dd>
          </div>
        </dl>
        <p className={styles.says}>{part.metric === null ? madeOf.waits : madeOf.noFigure}</p>
      </div>
    );
  }
  return (
    <FactRow
      fact={part.fact}
      source="line"
      lead={[share, [madeOf.reading, readingOf(mark.tag, part.term.reading)], [FACT_COLUMNS.band, part.fact.slots.band]]}
    />
  );
}

/** What pressing a vibe opens: what it means, where its band came from, and every part of its recipe. */
function MadeOf({ mark }: { readonly mark: MarkRow }) {
  const rests = restsOn(mark);
  // The parts of the recipe that are of recorded crime, as the release files them.
  const crime = mark.parts.flatMap((part) => (part.metric?.dimension === "crime" ? [part.metric.label] : []));
  return (
    <div className={styles.made}>
      <p className={styles.meaning}>{mark.tag.meaning}</p>
      <FactRow fact={mark.fact} source="line" />
      {crime.length === 0 ? null : (
        // One account of when recorded crime counts, as every page says it.
        <div className={styles.rests}>
          <p className={styles.says}>
            {CRIME_ACCOUNT.counts}:{" "}
            {crime.map((name, at) => (
              <span key={name}>
                {at > 0 ? "; " : null}
                <span>{name}</span>
              </span>
            ))}
          </p>
          <p className={styles.says}>
            {CRIME_ACCOUNT.rule} {askingFor(mark.tag)}
          </p>
        </div>
      )}
      {rests === null ? null : (
        // A band worked out from part of a recipe is not shown as any other.
        <div className={styles.rests}>
          <p className={styles.says}>{restsOnWords(rests, "full")}</p>
          <Without rests={rests} />
        </div>
      )}
      <h4 className={styles.small}>{PORTRAIT.madeOf.title}</h4>
      <ul className={styles.parts}>
        {mark.parts.map((part) => (
          <li key={part.term.feature_id}>
            <Part part={part} mark={mark} />
          </li>
        ))}
      </ul>
      <p className={styles.about}>
        <Link className="target-min" href={paths.vibes(mark.tag.tag_id)} prefetch={false}>
          {PORTRAIT.madeOf.about(mark.tag.label)}
        </Link>
      </p>
    </div>
  );
}

/**
 * One vibe: its name, the line it is marked on between its two ends, where it
 * sits in words a person would use, and the band. The whole line is what
 * opens its parts, and it is the browser's own element, so it opens with
 * scripts off.
 */
function Mark({ mark, withFigure }: { readonly mark: MarkRow; readonly withFigure: boolean }) {
  const [low, high] = endsOf(mark.tag);
  const { placed, pictured } = mark;
  if (placed === null) return null;
  // A mixed area is said to vary by the band's own words, and is not said twice.
  const plain = isRange(placed) ? null : plainly(mark.tag, placed);
  const rests = restsOn(mark);
  // The API's own clause is a sentence, and ends in a full stop of its own.
  const stopped = rests !== null && rests.partly !== null;
  return (
    <details className={styles.mark} data-vibe={mark.tag.tag_id} data-shape={mark.tag.shape}>
      <summary className={`${styles.line} target-min`}>
        <span className={styles.name}>{mark.tag.label}</span>
        {/* The picture is for the eye. The words beside it say the same, and more. */}
        <span className={styles.picture} aria-hidden="true">
          <span className={styles.end}>{low}</span>
          <Track placed={placed} />
          <span className={styles.end}>{high}</span>
        </span>
        <span className={styles.words}>
          {plain === null ? null : (
            <>
              <span className={styles.plain}>{plain}</span>
              {/* Where the words stand over the band, the comma between them is for a screen reader. */}
              <span className={styles.then}>, </span>
            </>
          )}
          {/* The band is said in full, in words that are drawn: it is never told by the picture alone. */}
          <small className={styles.detail}>
            <span className={styles.band}>{inWords(placed)}</span>
            <span className="visually-hidden">, {STRIP.from(low, high)}</span>
            {rests === null ? null : (
              <>
                {stopped ? ". " : ", "}
                <span className={styles.part}>{restsOnWords(rests, "short")}</span>
              </>
            )}
          </small>
        </span>
        {withFigure && pictured !== null ? (
          <Figure fact={pictured} className={styles.figure} afterStop={stopped} />
        ) : null}
        <span className={styles.opens}>
          <span className="visually-hidden">{stopped && !(withFigure && pictured !== null) ? " " : ". "}</span>
          {PORTRAIT.opens}
        </span>
      </summary>
      <MadeOf mark={mark} />
    </details>
  );
}

interface ShortProps {
  /** The vibes that say what the area is like, the furthest from the middle first. */
  readonly lines: readonly MarkRow[];
  /** How many vibes cannot place the area, and how many the release holds. */
  readonly unplaced: number;
  readonly vibes: number;
}

/**
 * What the area is like, in five lines at most. Each line is one vibe: its
 * name, where the area sits on it in words a person would use, and a figure
 * of one of its parts that a person can picture. Every one is a fact of the
 * API's, and the line under them gives their source and their date.
 */
function InShort({ lines, unplaced, vibes }: ShortProps) {
  const id = `${PORTRAIT_ID}-short`;
  const facts = lines.flatMap((mark) => [mark.fact, ...(mark.pictured === null ? [] : [mark.pictured])]);
  return (
    <div className={styles.short} role="group" aria-labelledby={id}>
      <h3 id={id}>{PORTRAIT.short.title}</h3>
      {lines.length === 0 ? (
        <p className={styles.shortLead}>{PORTRAIT.short.none}</p>
      ) : (
        <>
          <p className={styles.shortLead}>{PORTRAIT.short.lead}</p>
          <ul className={styles.shortLines}>
            {lines.map((mark) => {
              const rests = restsOn(mark);
              return (
                <li key={mark.tag.tag_id}>
                  <span className={styles.shortName}>{mark.tag.label}</span>
                  <span className="visually-hidden">: </span>
                  <span className={styles.shortWords}>
                    {mark.placed === null ? null : plainly(mark.tag, mark.placed)}
                    {rests === null ? null : (
                      <>
                        , <span className={styles.part}>{RESTS_ON.short(rests.known, rests.parts)}</span>
                      </>
                    )}
                  </span>
                  {mark.pictured === null ? null : <Figure fact={mark.pictured} className={styles.shortFigure} />}
                </li>
              );
            })}
          </ul>
        </>
      )}
      {unplaced > 0 ? (
        <p className={styles.shortUnplaced}>
          {PORTRAIT.short.unplaced(unplaced, vibes)}{" "}
          <a className="target-min" href={`#${UNPLACED_ID}`}>
            {PORTRAIT.short.why}
          </a>
        </p>
      ) : null}
      <SourceLine facts={facts} />
    </div>
  );
}

/**
 * The vibes that cannot place the area. It is said once, with why, and every
 * vibe is named in one line. What is known of each is one press away: how
 * many parts of its recipe have a figure, of how many, and which have none.
 * None is drawn as a mark, and none is put in the middle.
 */
function Unplaced({ marks }: { readonly marks: readonly MarkRow[] }) {
  // A vibe that no area of the data can be placed on is told from one that cannot place
  // this area alone. It was said of both that too few parts had a figure "for this area".
  const nowhere = marks.filter((mark) => mark.held?.placed === false);
  const here = marks.filter((mark) => mark.held?.placed !== false);
  return (
    <div className={styles.unplaced}>
      {here.length === 0 ? null : (
        <>
          {nowhere.length === 0 ? null : <p className={styles.kind}>{PORTRAIT.ofThisArea}</p>}
          <p className={styles.names}>{LIST.format(here.map((mark) => mark.tag.label))}</p>
          <p className={styles.why}>{PORTRAIT.unplacedWhy}</p>
        </>
      )}
      {nowhere.length === 0 ? null : (
        <>
          {here.length === 0 ? null : <p className={styles.kind}>{PORTRAIT.ofEveryArea}</p>}
          <p className={styles.names}>{LIST.format(nowhere.map((mark) => mark.tag.label))}</p>
          <p className={styles.why}>{PORTRAIT.notInData}</p>
        </>
      )}
      <details className={styles.mark}>
        <summary className={`${styles.line} target-min`}>
          <span className={styles.opens}>{PORTRAIT.unplacedOpens}</span>
        </summary>
        <ul className={`${styles.parts} ${styles.made}`}>
          {marks.map((mark) => {
            const rests = restsOn(mark);
            return (
              <li key={mark.tag.tag_id}>
                <FactRow fact={mark.fact} source="line" />
                {rests === null ? null : <Without rests={rests} />}
              </li>
            );
          })}
        </ul>
      </details>
    </div>
  );
}

/**
 * The portrait an area's page opens with. First what the area is like in
 * short, in words a person would use, and beside it where it is. Then where
 * it sits on every vibe of the release, in words and as a mark on a line. It
 * is never a colour alone, and never a percentage or a score.
 *
 * Which vibe stands in which list, the order, every band and every figure
 * are the API's. A band that rests on part of a recipe says so beside it. A
 * vibe the area cannot be placed on is said to be so, once, and is never put
 * in the middle. The parts behind each vibe are one press away, each with its
 * source and its date. It is built with no search, so it is the same for
 * everyone.
 */
export function Portrait({ data, meta, besideShort, underMore }: Props) {
  const portrait = portraitOf(data, meta);
  const placed = shownOn(portrait);
  return (
    <section className={styles.portrait} aria-labelledby={PORTRAIT_ID}>
      <h2 id={PORTRAIT_ID}>{PORTRAIT.title}</h2>
      <div className={styles.top}>
        <InShort
          lines={inShort(portrait, meta.features)}
          unplaced={portrait.unplaced.length}
          vibes={placed.length + portrait.unplaced.length}
        />
        {besideShort}
      </div>
      {placed.length === 0 ? null : <p className={styles.lead}>{PORTRAIT.lead}</p>}
      {GROUPS.map((group) =>
        portrait[group].length === 0 ? null : (
          <div key={group} className={styles.group} role="group" aria-labelledby={`${PORTRAIT_ID}-${group}`}>
            <div className={styles.heading}>
              <h3 id={`${PORTRAIT_ID}-${group}`}>{PORTRAIT.groups[group]}</h3>
            </div>
            {group === "unplaced" ? (
              <Unplaced marks={portrait[group]} />
            ) : (
              <ul className={styles.marks}>
                {portrait[group].map((mark) => (
                  <li key={mark.tag.tag_id}>
                    <Mark mark={mark} withFigure={WITH_FIGURE.includes(group)} />
                  </li>
                ))}
              </ul>
            )}
            {group === "more" && underMore !== undefined ? <div className={styles.under}>{underMore}</div> : null}
          </div>
        ),
      )}
    </section>
  );
}
