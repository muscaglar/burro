"use client";

import { STRIP } from "@/content/search";
import type { Fact, StripMark, Tag } from "@/lib/api/schema";
import { endsOf, inWords, isRange, VIBE_BANDS } from "@/lib/vibes";

import { Disclosure } from "../Disclosure/Disclosure";
import { FactRow } from "../FactRow/FactRow";
import { Track } from "../Track/Track";
import styles from "./Strip.module.css";

interface PictureProps {
  readonly mark: StripMark;
  readonly tag: Tag;
}

/**
 * What the picture of a mark says: the band, the ends the bands are counted between, and
 * whether it was asked for. The names of the ends are drawn beside the cells for the eye,
 * and are said here, once, for whoever hears the page: said in both places, a mark read
 * "asked for: Buzzy Buzzy".
 */
function saidBy(mark: StripMark, tag: Tag): string {
  const [low, high] = endsOf(tag);
  const where = `${inWords(mark)}, ${STRIP.from(low, high)}`;
  if (!mark.asked) return where;
  return `${where}, ${tag.shape === "scale" ? STRIP.askedFor(mark.toward === "low" ? low : high) : STRIP.asked}`;
}

/**
 * Where an area sits on one vibe: five cells, from its low end to its high
 * end. A scale has the names the API gives its ends, one at each side. A vibe
 * that runs one way says which end the area sits at, where it sits at one:
 * "least" or "most". With no word, one filled cell at the left could be
 * praise or a warning.
 *
 * It is drawn in the strip after the name of its vibe, and beside a sentence
 * that is about its vibe, which names the vibe itself.
 */
export function Picture({ mark, tag }: PictureProps) {
  const [low, high] = endsOf(tag);
  const picture = <Track placed={mark} says={saidBy(mark, tag)} narrow />;
  if (tag.shape !== "scale") {
    // A mixed area sits at no one end. In the middle bands the cells say enough.
    const at = isRange(mark) ? null : mark.band === 1 ? low : mark.band === VIBE_BANDS.length ? high : null;
    return (
      <>
        {picture}
        {at === null ? null : (
          <span className={styles.end} aria-hidden="true">
            {at}
          </span>
        )}
      </>
    );
  }
  // The end that was asked for is drawn heavier, and said in the name of the picture.
  const asked = mark.asked ? (mark.toward === "low" ? "low" : "high") : null;
  return (
    <>
      <span className={styles.end} data-asked={asked === "low"} aria-hidden="true">
        {low}
      </span>
      {picture}
      <span className={styles.end} data-asked={asked === "high"} aria-hidden="true">
        {high}
      </span>
    </>
  );
}

interface MarkProps extends PictureProps {
  /**
   * What is said once before a run of marks: that they were asked for, or that they were
   * not. It is drawn for the eye. A screen reader hears it of each mark, from its picture.
   */
  readonly group?: string;
}

/** One vibe of the strip: its name, its two ends, and where between them the area sits. */
function Mark({ mark, tag, group }: MarkProps) {
  return (
    <span className={styles.mark} data-asked={mark.asked}>
      {group === undefined ? null : (
        <span className={styles.group} aria-hidden="true">
          {group}
        </span>
      )}
      <span className={styles.name}>{tag.label}</span>
      <Picture mark={mark} tag={tag} />
    </span>
  );
}

interface Props {
  readonly marks: readonly StripMark[];
  /** The vibes of the release, from route 11: their names and the names of their ends. */
  readonly tags: readonly Tag[];
  /** The facts in hand. A mark whose fact is among them opens to it, with its source and date. */
  readonly facts?: Readonly<Record<string, Fact>>;
  /** The area, to tell one strip's buttons from the next. */
  readonly of: string;
  /**
   * True where a vibe that was asked for is drawn beside its sentence and not here. The
   * marks that were not asked for are then said to be beside it, though they come first.
   */
  readonly also?: boolean;
}

/**
 * The strip under a result's name: where the area sits on the vibes that
 * were asked for, and on up to two others it sits at an end of. It is shown
 * and never scored: only what is in the search counts.
 *
 * Which vibes, in what order, and every band are the API's. A vibe the
 * release does not name is left out. Where the fact behind a mark is in
 * hand, the mark opens to it in place, with its source and date.
 */
export function Strip({ marks, tags, facts = {}, of, also = false }: Props) {
  const drawn = marks.flatMap((mark) => {
    const tag = tags.find((one) => one.tag_id === mark.tag_id);
    return tag === undefined ? [] : [{ mark, tag }];
  });
  if (drawn.length === 0) return null;
  return (
    // It says whether any vibe was asked for, here or beside a sentence. On a narrow screen
    // the marks of what was not asked for then give way: they are on the page of the area.
    <ul className={styles.strip} aria-label={STRIP.label(of)} data-asked={also || drawn.some(({ mark }) => mark.asked)}>
      {drawn.map(({ mark, tag }, at) => {
        const fact = facts[mark.fact_id];
        // The marks stand in the order the API gave them. Where one run ends and another
        // begins, the next is said to be asked for, or not.
        const group =
          at > 0 && drawn[at - 1]?.mark.asked === mark.asked
            ? undefined
            : mark.asked
              ? STRIP.group.asked
              : at > 0 || also
                ? STRIP.group.also
                : undefined;
        return (
          <li key={mark.tag_id} className={styles.item} data-asked={mark.asked}>
            {fact === undefined ? (
              <Mark mark={mark} tag={tag} group={group} />
            ) : (
              <Disclosure
                label={<Mark mark={mark} tag={tag} group={group} />}
                size="small"
                className={styles.opens}
              >
                <FactRow fact={fact} />
              </Disclosure>
            )}
          </li>
        );
      })}
    </ul>
  );
}
