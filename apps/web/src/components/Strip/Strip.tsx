"use client";

import { Approx, NoData } from "@/components/kit/Approx/Approx";
import { Art } from "@/components/kit/Art/Art";
import { picturesAtEnds } from "@/components/kit/Ends/picture";
import type { ThingOf } from "@/components/kit/Thing/drawn";
import { Thing } from "@/components/kit/Thing/Thing";
import { CARD } from "@/content/card";
import { KNOWN } from "@/content/kit";
import { PEG } from "@/content/kit";
import { STRIP } from "@/content/search";
import type { Fact, StripMark, Tag } from "@/lib/api/schema";
import { endsOf, inWords } from "@/lib/vibes";

import { Track } from "../Track/Track";
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
  const [low, high] = endsOf(tag);
  const [atLow, atHigh] = picturesAtEnds(tag.tag_id);
  const named = ends === "named";
  // Of a scale, the end that was asked for. A vibe that runs one way is asked for, and no end of it.
  const asked = mark !== null && mark.asked && tag.shape === "scale" ? (mark.toward === "low" ? "low" : "high") : null;
  return (
    <span
      className={styles.picture}
      role="img"
      aria-label={mark === null ? PEG.empty : saidBy(mark, tag)}
      data-as={as}
      data-ends={ends}
    >
      <End picture={atLow} />
      <Track placed={mark} part={part} small={as === "short"} />
      <End picture={atHigh} />
      {/* Where the look has the ends named: the two names under the gauge, each at its own
          end. The end that was asked for is named heavier. */}
      {named ? (
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

/** A thing that was asked for and is no vibe, which the area has no figure for. */
export interface Lacked {
  /** The name of the thing, as the page names it everywhere. */
  readonly name: string;
  /** What is drawn for it. */
  readonly thing: ThingOf;
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
  /** The gauge of the line, where the line is of a vibe. */
  readonly children?: React.ReactNode;
}

/**
 * One line of a result: the small drawing of the thing with its name, its gauge, and two
 * words where its figure is not whole, or is not known. Nothing else is said of it here:
 * what a figure was worked out from is in the working of the result.
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
   * What else was asked for that the area has no figure for, which is no vibe: a journey, a
   * budget, a measurement. Each is named in a list of its own under the vibes, and is
   * said to be not known.
   */
  readonly lacked?: readonly Lacked[];
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
}

/**
 * The lines of a result: where the area sits on the vibes the page chose to draw of those
 * the API gave, and what was asked for that the area has no figure for. It is shown and
 * never scored: only what is in the search counts.
 *
 * Which vibes, in what order, and every band are the API's. A vibe the release does not
 * name is left out. Every line is drawn as the next is: the small drawing of the thing
 * with its name, its gauge with a picture at each end, and two words where the figure is
 * not whole. No word says where the area sits: the gauge does, and its name says it to
 * whoever hears the page.
 *
 * The steps of every line stand in one column, so that the eye runs down them: the names
 * before them have a column of their own, which is as wide as the longest name that
 * stands in it needs and no wider than it can be given. A name that is longer breaks onto
 * a second line.
 */
export function Strip({
  marks,
  tags,
  facts = {},
  of,
  unplaced = [],
  lacked = [],
  short = false,
  ends = "pictured",
  rests = true,
  names,
}: Props) {
  const drawn = marks.flatMap((mark) => {
    const tag = tags.find((one) => one.tag_id === mark.tag_id);
    return tag === undefined ? [] : [{ mark, tag }];
  });
  // A vibe that has a mark is placed, whatever else is said of it: it is drawn once.
  const blank = tags.filter((tag) => unplaced.includes(tag.tag_id) && !drawn.some((one) => one.tag.tag_id === tag.tag_id));
  if (drawn.length === 0 && blank.length === 0 && lacked.length === 0) return null;
  // That a line was asked for is said for the eye only where a line beside it was not.
  const both = drawn.some(({ mark }) => mark.asked) && drawn.some(({ mark }) => !mark.asked);
  const column = names ?? [...namesOf([drawn.map(({ mark }) => mark)], tags), ...blank.map((tag) => tag.label), ...lacked.map((one) => one.name)];
  return (
    <div
      className={styles.strip}
      data-short={short}
      data-ends={ends}
      // What stands in the column of names, for the style sheet to lay in every line of it.
      style={withThePlaceOf({
        names: column,
        groups: both ? [STRIP.group.asked, STRIP.group.also] : [],
        beside: UNDER_A_NAME,
      })}
    >
      {drawn.length + blank.length === 0 ? null : (
        <ul className={styles.lines} aria-label={STRIP.label(of)}>
          {drawn.map(({ mark, tag }, at) => {
            // The marks stand in the order the API gave them. Where one run ends and another
            // begins, the next is said to be asked for, or not.
            const group =
              !both || (at > 0 && drawn[at - 1]?.mark.asked === mark.asked)
                ? undefined
                : mark.asked
                  ? STRIP.group.asked
                  : STRIP.group.also;
            const part = rests && isFromPart(facts[mark.fact_id]);
            return (
              <li key={mark.tag_id} className={styles.item} data-asked={mark.asked}>
                <Line
                  name={tag.label}
                  thing={{ kind: "tag", id: tag.tag_id, family: tag.family }}
                  group={group}
                  known={part ? "some" : "whole"}
                  asked={mark.asked}
                  short={short}
                >
                  <Picture mark={mark} tag={tag} as={short ? "short" : "line"} ends={ends} part={part} />
                </Line>
              </li>
            );
          })}
          {blank.map((tag) => (
            <li key={tag.tag_id} className={styles.item} data-asked="true">
              <Line name={tag.label} thing={{ kind: "tag", id: tag.tag_id, family: tag.family }} known="none" asked short={short}>
                <Picture mark={null} tag={tag} as={short ? "short" : "line"} ends={ends} />
              </Line>
            </li>
          ))}
        </ul>
      )}
      {lacked.length === 0 ? null : (
        <ul className={styles.lines} aria-label={CARD.lacked(of)}>
          {lacked.map(({ name, thing }) => (
            <li key={name} className={styles.item} data-asked="true">
              <Line name={name} thing={thing} known="none" asked short={short} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
