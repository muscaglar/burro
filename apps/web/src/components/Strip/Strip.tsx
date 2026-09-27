"use client";

import { useId, useState, type CSSProperties, type ReactNode } from "react";

import { Approx, NoData } from "@/components/kit/Approx/Approx";
import { Art } from "@/components/kit/Art/Art";
import { NO_PICTURE, picturesAtEnds } from "@/components/kit/Ends/picture";
import { Press } from "@/components/kit/Press/Press";
import type { ThingOf } from "@/components/kit/Thing/drawn";
import { Thing } from "@/components/kit/Thing/Thing";
import { CARD } from "@/content/card";
import { KNOWN } from "@/content/kit";
import { PEG } from "@/content/kit";
import { STRIP } from "@/content/search";
import type { Fact, StripMark, Tag } from "@/lib/api/schema";
import { endsOf, inWords, type Placed } from "@/lib/vibes";

import { HIGH, Track } from "../Track/Track";
import { namesOf, withThePlaceOf } from "./column";
import styles from "./Strip.module.css";

/**
 * How the two ends of a gauge are drawn. `pictured`: each by its one small picture, and
 * nothing under it. `named`: each by its picture, with the names of the two ends under
 * the gauge, each at its own end.
 *
 * Whichever it is, each end of every gauge has a picture, the two are of one size and one
 * weight, and the steps of every line begin in one place: the room of an end is as wide
 * on every line, whatever its vibe.
 */
export type Ends = "pictured" | "named";

/** The pictures at the two ends of a gauge, the low end first. */
type AtEnds = ReturnType<typeof picturesAtEnds>;

interface GaugeProps {
  /** Where the area sits. `null` where that is not known: five empty steps and no peg. */
  readonly placed: Placed | null;
  /** What the picture says, to whoever hears the page. */
  readonly says: string;
  readonly pictures: AtEnds;
  /** What the two ends are called, the low end first. */
  readonly names: readonly [low: string, high: string];
  /** The end that was asked for, of a gauge that runs between two ends that have names. */
  readonly asked?: "low" | "high" | null;
  readonly as: "line" | "short";
  readonly ends: Ends;
  readonly part: boolean;
}

interface PictureProps {
  /**
   * Where the area sits. `null` of a vibe that Burro could not work out for the area: five
   * empty steps and no peg, which is neither the middle nor nought.
   */
  readonly mark: StripMark | null;
  readonly tag: Tag;
  /** How the picture stands. `line`: on the line of its vibe. `short`: in a list of many small things. */
  readonly as?: "line" | "short";
  /** How the ends of the gauge are drawn. */
  readonly ends?: Ends;
  /** True where the band was worked out from some of what goes into it: the step the peg stands on is chequered. */
  readonly part?: boolean;
}

/**
 * What the picture of a mark says: the band, the ends the bands are counted between, and
 * whether it was asked for. Nothing of it is written beside the steps, so this is where
 * whoever hears the page is told where the area sits.
 */
function saidBy(mark: StripMark, tag: Tag): string {
  const [low, high] = endsOf(tag);
  const where = `${inWords(mark)}, ${STRIP.from(low, high)}`;
  if (!mark.asked) return where;
  return `${where}, ${tag.shape === "scale" ? STRIP.askedFor(mark.toward === "low" ? low : high) : STRIP.asked}`;
}

interface EndProps {
  /** The picture of the end, which is chosen by the id of its vibe. */
  readonly picture: Parameters<typeof Art>[0]["name"];
}

/**
 * One end of a gauge: its one small picture. The picture is dress, and says what the end
 * is. Neither end is the good one, and the two are drawn alike.
 */
function End({ picture }: EndProps) {
  return (
    <span className={styles.end}>
      <Art name={picture} alt="" />
    </span>
  );
}

/**
 * A gauge: five steps from its low end to its high end, with a peg on the one the area
 * sits on, and a picture at each end. It is one picture, and its name says what it shows.
 * No word stands beside it, so what it says is said by its name alone.
 *
 * Wherever it stands, its steps begin where the steps of every other begin: the picture of
 * an end is of one size, whatever it is of.
 */
function Gauge({ placed, says, pictures: [atLow, atHigh], names: [low, high], asked = null, as, ends, part }: GaugeProps) {
  return (
    <span className={styles.picture} role="img" aria-label={says} data-as={as} data-ends={ends}>
      <End picture={atLow} />
      <Track placed={placed} part={part} small={as === "short"} />
      <End picture={atHigh} />
      {/* Where the look has the ends named: the two names under the gauge, each at its own
          end. The end that was asked for is named heavier. */}
      {ends === "named" ? (
        <span className={styles.named}>
          <span className={styles.ofEnd} data-asked={asked === "low"}>
            {low}
          </span>
          <span className={styles.ofEnd} data-asked={asked === "high"}>
            {high}
          </span>
        </span>
      ) : null}
    </span>
  );
}

/**
 * Where an area sits on one vibe: five steps from its low end to its high end, with a peg
 * on the one it sits on, and a picture at each end. The two pictures are opposites: what
 * there is little of, and what there is much of.
 *
 * It is one picture, and its name says what it shows: the band, and the ends the bands
 * run between. No word stands beside it, so what it says is said by its name alone.
 *
 * Wherever it stands, its steps begin where the steps of every other begin: the picture of
 * an end is of one size, whatever its vibe.
 */
export function Picture({ mark, tag, as = "line", ends = "pictured", part = false }: PictureProps) {
  // Of a scale, the end that was asked for. A vibe that runs one way is asked for, and no end of it.
  const asked = mark !== null && mark.asked && tag.shape === "scale" ? (mark.toward === "low" ? "low" : "high") : null;
  return (
    <Gauge
      placed={mark}
      says={mark === null ? PEG.empty : saidBy(mark, tag)}
      pictures={picturesAtEnds(tag.tag_id)}
      names={endsOf(tag)}
      asked={asked}
      as={as}
      ends={ends}
      part={part}
    />
  );
}

/** What begins the name of the picture of an end of a measure, and of the family of one: neither is the picture of a vibe. */
const OF_A_MEASURE = "measure-";
const OF_A_FAMILY = "family-";

/**
 * The pictures at the two ends of the gauge of a measure: its own, where the kit has a
 * pair for the measure, and else those of its family, and else the blank one at both. A
 * measure is never drawn by the pictures of a vibe, whatever the service calls it: the
 * pictures of a measure and of a family are named apart from those of a vibe.
 */
export function picturesOfAMeasure({ id = null, family = null }: Pick<ThingOf, "id" | "family">): AtEnds {
  const own = picturesAtEnds(id === null || id === "" ? null : `${OF_A_MEASURE}${id}`);
  if (own.some((picture) => picture !== NO_PICTURE)) return own;
  return picturesAtEnds(family === null || family === "" ? null : `${OF_A_FAMILY}${family}`);
}

/**
 * True of a band that was worked out from some of what goes into its vibe, where its fact
 * is in hand to say so. The two counts are the API's, and nothing is added up here.
 */
export function isFromPart(fact: Fact | undefined): boolean {
  if (fact === undefined) return false;
  const { known, parts } = fact.slots;
  return known !== undefined && parts !== undefined && known !== parts;
}

/**
 * The room the mark of two words takes before them, in art pixels: the nine of a step of
 * a band, and the two that stand between the mark and the words.
 */
export const BEFORE_THE_TWO_WORDS = 11;

/**
 * What else stands in the column of names, under a name: the two words that say a figure
 * is not whole, and the two that say it is not known, each after its mark. The column is
 * told of both on every line, so that it is as wide on a line that says neither.
 */
export const UNDER_A_NAME = [
  { says: KNOWN.some, more: BEFORE_THE_TWO_WORDS },
  { says: KNOWN.none, more: BEFORE_THE_TWO_WORDS },
] as const;

/**
 * Where an area stands on a measure, as its gauge shows it: the step its peg stands on,
 * and what the picture says to whoever hears the page, which is the figure and where it
 * stands in the words of the service.
 */
export interface Stands {
  readonly placed: Placed;
  readonly says: string;
}

/**
 * A line of a thing that was asked for and is no vibe: a measure, a journey or a budget.
 * Every word of it that says anything of the area is the API's, or a figure of the ranking.
 */
export interface Asked {
  /** What tells the line from the next. It is drawn nowhere and is no name of anything. */
  readonly key: string;
  /** The name of the thing, as the page names it everywhere: of a journey, the name of its place. */
  readonly name: string;
  /** What is drawn for it. */
  readonly thing: ThingOf;
  /**
   * How much is known of its figure. `some`: it is an estimate. `none`: the area has no
   * figure for the thing, and the line says so.
   */
  readonly known: "whole" | "some" | "none";
  /** Where the area stands on it, of a measure whose fact says so. */
  readonly gauge?: Stands | undefined;
  /** What the area has of it, in a figure: the minutes of a journey, what a home costs. */
  readonly figure?: string | undefined;
  /** On which side of what the person set the figure falls, in a word. */
  readonly side?: string | undefined;
}

interface LineProps {
  /** What the line is of: the name the API gives it. */
  readonly name: string;
  /** The small drawing that stands with the name. */
  readonly thing: ThingOf;
  /** What is said once before a run of lines, for the eye: that they were asked for, or that they were not. */
  readonly group?: string | undefined;
  /** How much is known of the figure. */
  readonly known: "whole" | "some" | "none";
  readonly asked: boolean;
  readonly short: boolean;
  /** What the area has of the thing: its gauge, or its figure. */
  readonly children?: ReactNode;
}

/**
 * One line of a result: the small drawing of the thing with its name, what the area has
 * of it, and two words where its figure is not whole, or is not known. Nothing else is
 * said of it here: what a figure was worked out from is in the working of the result.
 */
function Line({ name, thing, group, known, asked, short, children }: LineProps) {
  return (
    <span className={styles.mark} data-asked={asked} data-short={short} data-known={known}>
      {/* What the line is of, in the column of names. */}
      <span className={styles.first}>
        <span className={styles.title}>
          <span className={styles.thing}>
            <Thing {...thing} />
          </span>
          <span className={styles.titled}>
            {group === undefined ? null : (
              <span className={styles.group} aria-hidden="true">
                {group}
              </span>
            )}
            <span className={styles.name}>{name}</span>
          </span>
        </span>
        {/* It holds nothing. The style sheet lays in it every name of the column, none of
            which is drawn or heard: so the column is as wide in this line as in the next. */}
        <span className={styles.wide} aria-hidden="true" />
      </span>
      {children}
      {known === "some" ? <Approx className={styles.said} /> : null}
      {known === "none" ? <NoData className={styles.said} /> : null}
    </span>
  );
}

interface Props {
  readonly marks: readonly StripMark[];
  /** The vibes of the release, from route 11: their names and the names of their ends. */
  readonly tags: readonly Tag[];
  /** The facts in hand. A band whose fact is among them says where it is not whole. */
  readonly facts?: Readonly<Record<string, Fact>>;
  /** The area, to name the list. */
  readonly of: string;
  /**
   * The vibes that were asked for and that Burro could not work out for the area, by the
   * ids the API gives them. Each has its line, after the marks: its gauge holds nothing,
   * and it is said to be not known.
   */
  readonly unplaced?: readonly string[];
  /**
   * What else was asked for, which is no vibe, in the order the search holds it: each
   * measure, each journey and the budget. Each has its line after the vibes that were
   * asked for, and one that the area has no figure for is said to be not known.
   */
  readonly asked?: readonly Asked[];
  /**
   * True in a list of many small things, as a row of results is: each mark is one short
   * line, with small steps.
   */
  readonly short?: boolean;
  /** How the two ends of a gauge are drawn. */
  readonly ends?: Ends;
  /**
   * Every name that stands in the column of names this strip stands in, as a list of
   * results has them of all its strips: the column is then of one width from one result
   * to the next. Left out, they are the names of this strip.
   */
  readonly names?: readonly string[];
  /**
   * False where a band that is not whole is left to say so where its fact is opened. Left
   * out, it says so beside the band, in two words, wherever its fact is in hand, and the
   * step its peg stands on is chequered.
   */
  readonly rests?: boolean;
  /** How the lines of what was asked for fold, in a result with no room for all of them. Left out, nothing is folded. */
  readonly fold?: Fold | undefined;
}

/**
 * How the lines of a result fold, where the result has no room for all of them. It is
 * counted in rows: a line is one row, and half a row more for each line more that its name
 * takes in the column of names.
 */
export interface Fold {
  /** How many rows stand over the press that shows the rest. */
  readonly over: number;
  /** The most rows a result shows with nothing pressed, and no press. */
  readonly most: number;
  /**
   * How many letters of a name stand on one line of the column of names of such a result.
   * Left out, every line counts for one row, whatever it is called.
   */
  readonly letters?: number | undefined;
}

/** One line of the list, as it is drawn, with what tells it from the next. */
interface Drawn {
  readonly key: string;
  readonly asked: boolean;
  /** True of a line that says the area has no figure for its thing. */
  readonly lacked: boolean;
  /** What the line is of, by the name that stands on it: a long one takes more rows than one. */
  readonly name: string;
  readonly line: ReactNode;
}

/** What each line more of a name counts for, in rows. */
const A_LINE_MORE = 0.5;

/**
 * How many rows a line counts for, by the lines its name takes in the column of names: one,
 * and half a row more for each line more. A name of two lines makes its line a fifth
 * higher, and one of three nearly twice as high, and a long name takes room over the
 * result as well, where its chip has a row to itself.
 */
function rowsOf(name: string, fold: Fold): number {
  const { letters } = fold;
  if (letters === undefined || letters < 1) return 1;
  return 1 + A_LINE_MORE * (Math.max(1, Math.ceil(name.length / letters)) - 1);
}

/**
 * Which lines stand over the press that shows the rest, of a result with no room for all
 * of them: every line that says the area has no figure for its thing, and the first of
 * the others, as many as there is room for beside those. Each stands in the order of the
 * search, over the press and under it, and once a line is put away so is every line
 * after it that has a figure. The first line stands however long its name is: a result is
 * never without a line for the length of a name.
 *
 * What an area has no figure for is said in sight, with nothing pressed: such an area
 * stands below every area that has the figure, and the line is what says which it lacks.
 */
function overTheFold(lines: readonly Drawn[], fold: Fold | undefined): readonly boolean[] {
  if (fold === undefined) return lines.map(() => true);
  const rows = lines.map((one) => rowsOf(one.name, fold));
  if (rows.reduce((all, one) => all + one, 0) <= fold.most) return lines.map(() => true);
  const lacked = lines.some((one) => one.lacked);
  const room = fold.over - lines.reduce((all, one, at) => (one.lacked ? all + (rows[at] ?? 1) : all), 0);
  let taken = 0;
  return lines.map((one, at) => {
    if (one.lacked) return true;
    const first = taken === 0 && !lacked;
    taken += rows[at] ?? 1;
    return first || taken <= room;
  });
}

/**
 * The lines of a result: one for each thing that was asked for, in the order the search
 * holds them, and the vibes nobody asked for where the page chose to draw them. What is
 * drawn of a vibe is shown and never scored: only what is in the search counts.
 *
 * Which vibes, in what order, and every band are the API's. A vibe the release does not
 * name is left out. Every line is drawn as the next is: the small drawing of the thing
 * with its name, what the area has of it, and two words where the figure is not whole or
 * is not known. Of a vibe and of a measure that is a gauge, with a picture at each end. No
 * word says where the area sits: the gauge does, and its name says it to whoever hears
 * the page. Of a journey and of a budget it is a figure, and on which side of what the
 * person set the figure falls.
 *
 * What the area has of each thing stands in one column, so that the eye runs down it: the
 * names before it have a column of their own, which is as wide as the longest name that
 * stands in it needs and no wider than it can be given. A name that is longer breaks onto
 * a second line.
 *
 * Each list says what it holds, to whoever hears the page: what was asked for, and the
 * vibes that were not. A result with no room for every line of what was asked for shows
 * the first of them, with every line that says a figure is not known, and one press under
 * them shows the rest: what stands under the press opens under it, so that the press
 * stays where it was.
 */
export function Strip({
  marks,
  tags,
  facts = {},
  of,
  unplaced = [],
  asked = [],
  short = false,
  ends = "pictured",
  rests = true,
  names,
  fold,
}: Props) {
  const [open, setOpen] = useState(false);
  const rest = useId();
  const drawn = marks.flatMap((mark) => {
    const tag = tags.find((one) => one.tag_id === mark.tag_id);
    return tag === undefined ? [] : [{ mark, tag }];
  });
  // A vibe that has a mark is placed, whatever else is said of it: it is drawn once.
  const blank = tags.filter((tag) => unplaced.includes(tag.tag_id) && !drawn.some((one) => one.tag.tag_id === tag.tag_id));
  if (drawn.length === 0 && blank.length === 0 && asked.length === 0) return null;
  const wanted = drawn.filter(({ mark }) => mark.asked);
  const others = drawn.filter(({ mark }) => !mark.asked);
  const anyAsked = wanted.length + blank.length + asked.length > 0;
  // That a line was asked for is said for the eye only where a line beside it was not.
  const both = anyAsked && others.length > 0;
  const column = names ?? [
    ...namesOf([wanted.map(({ mark }) => mark)], tags),
    ...blank.map((tag) => tag.label),
    ...asked.map((one) => one.name),
    ...namesOf([others.map(({ mark }) => mark)], tags),
  ];
  const as = short ? "short" : "line";

  const ofAVibe = ({ mark, tag }: (typeof drawn)[number], group: string | undefined): Drawn => {
    const part = rests && isFromPart(facts[mark.fact_id]);
    return {
      key: `vibe ${mark.tag_id}`,
      asked: mark.asked,
      lacked: false,
      name: tag.label,
      line: (
        <Line
          name={tag.label}
          thing={{ kind: "tag", id: tag.tag_id, family: tag.family }}
          group={group}
          known={part ? "some" : "whole"}
          asked={mark.asked}
          short={short}
        >
          <Picture mark={mark} tag={tag} as={as} ends={ends} part={part} />
        </Line>
      ),
    };
  };

  // What was asked for, in the order the search holds it. The first of them says so for
  // the eye, where a vibe nobody asked for is drawn as well.
  const first = both ? STRIP.group.asked : undefined;
  const lines: Drawn[] = [
    ...wanted.map((one, at) => ofAVibe(one, at === 0 ? first : undefined)),
    ...blank.map((tag, at) => ({
      key: `vibe ${tag.tag_id}`,
      asked: true,
      lacked: true,
      name: tag.label,
      line: (
        <Line
          name={tag.label}
          thing={{ kind: "tag", id: tag.tag_id, family: tag.family }}
          group={wanted.length === 0 && at === 0 ? first : undefined}
          known="none"
          asked
          short={short}
        >
          <Picture mark={null} tag={tag} as={as} ends={ends} />
        </Line>
      ),
    })),
    ...asked.map((one, at) => ({
      key: one.key,
      asked: true,
      lacked: one.known === "none",
      name: one.name,
      line: (
        <Line
          name={one.name}
          thing={one.thing}
          group={wanted.length + blank.length === 0 && at === 0 ? first : undefined}
          known={one.known}
          asked
          short={short}
        >
          {one.gauge !== undefined ? (
            <Gauge
              placed={one.gauge.placed}
              says={one.gauge.says}
              pictures={picturesOfAMeasure(one.thing)}
              names={[STRIP.least, STRIP.most]}
              as={as}
              ends={ends}
              part={false}
            />
          ) : one.figure !== undefined || one.side !== undefined ? (
            <span className={styles.told}>
              {one.figure === undefined ? null : <span className={styles.figure}>{one.figure}</span>}
              {one.side === undefined ? null : <span className={styles.side}>{one.side}</span>}
            </span>
          ) : null}
        </Line>
      ),
    })),
  ];
  // A result shows every line where they take four rows or fewer. Of more, those that stand over the press.
  const stays = overTheFold(lines, fold);
  const shown = lines.filter((_, at) => stays[at] === true);
  const folded = lines.filter((_, at) => stays[at] !== true);
  const seen = open ? CARD.fewer : CARD.more(folded.length);
  const listOf = (held: readonly Drawn[]) =>
    held.map(({ key, asked: wasAsked, line }) => (
      <li key={key} className={styles.item} data-asked={wasAsked}>
        {line}
      </li>
    ));

  return (
    <div
      className={styles.strip}
      data-short={short}
      data-ends={ends}
      // What stands in the column of names, for the style sheet to lay in every line of it,
      // and how high a line of steps is, which every line is whatever it holds.
      style={
        {
          ...withThePlaceOf({
            names: column,
            groups: both ? [STRIP.group.asked, STRIP.group.also] : [],
            beside: UNDER_A_NAME,
          }),
          "--steps-high": HIGH,
        } as CSSProperties
      }
    >
      {lines.length === 0 ? null : (
        <ul className={styles.lines} aria-label={STRIP.askedOf(of)}>
          {listOf(shown)}
        </ul>
      )}
      {folded.length === 0 ? null : (
        <>
          <p className={styles.fold}>
            <Press name={CARD.moreOf(seen, of)} expanded={open} controls={rest} onPress={() => setOpen(!open)}>
              {/* It holds the room of both of the things it says, so that it is of one size
                  under the press. The one it does not say is not drawn, and is not heard. */}
              <span className={styles.says}>
                <span className={styles.saying} data-said={!open} aria-hidden={open ? true : undefined}>
                  {CARD.more(folded.length)}
                </span>
                <span className={styles.saying} data-said={open} aria-hidden={open ? undefined : true}>
                  {CARD.fewer}
                </span>
              </span>
            </Press>
          </p>
          <ul id={rest} className={styles.lines} data-folded={!open} aria-label={STRIP.restOf(of)}>
            {listOf(folded)}
          </ul>
        </>
      )}
      {others.length === 0 ? null : (
        <ul className={styles.lines} aria-label={anyAsked ? STRIP.othersOf(of) : STRIP.label(of)}>
          {listOf(others.map((one, at) => ofAVibe(one, both && at === 0 ? STRIP.group.also : undefined)))}
        </ul>
      )}
    </div>
  );
}
