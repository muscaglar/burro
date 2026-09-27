import type { Fact, Tag } from "@/lib/api/schema";
import { inWords, isRange, plainly, type Placed } from "@/lib/vibes";

import { Approx } from "../kit/Approx/Approx";
import { Art } from "../kit/Art/Art";
import { picturesAtEnds } from "../kit/Ends/picture";
import { Track } from "../Track/Track";
import styles from "./CompareTable.module.css";
import { ENDS_STAND, UNDER_A_GAUGE, type EndsStand, type UnderAGauge } from "./look";

interface Props {
  /** The vibe, from route 11: its id, by which the pictures of its ends are chosen, and the names of its ends. */
  readonly tag: Tag;
  /** Where the area sits on it, as the API says. */
  readonly placed: Placed;
  /** The fact of the vibe for the area: how many parts of its recipe have a figure, of how many. */
  readonly fact: Fact;
  /** What is said under the gauge. Left out, it is what `look.ts` chooses. */
  readonly under?: UnderAGauge;
  /** Where the pictures of the two ends stand. Left out, it is what `look.ts` chooses. */
  readonly ends?: EndsStand;
}

/**
 * True of a band that rests on part of what goes into its vibe. The two counts are the
 * fact's own, and nothing is added up here.
 */
function restsOnPart({ slots }: Fact): boolean {
  const { known, parts } = slots;
  return known !== undefined && parts !== undefined && known !== parts;
}

/** Where an area sits, in words: in words a person would use, and the band. A mixed area is said to vary by its band alone. */
export function whereInWords(tag: Pick<Tag, "low_end" | "high_end">, placed: Placed): string {
  const plain = isRange(placed) ? null : plainly(tag, placed);
  return plain === null ? inWords(placed) : `${plain}, ${inWords(placed)}`;
}

/**
 * Where one area sits on one vibe, as a comparison draws it: its gauge, which is five
 * steps with a peg on one, and the one picture of each of its ends at either side where
 * the look has them stand there. It is never a colour alone, a score or a percentage.
 *
 * Where the area sits is said in words: under the gauge where the look has words there,
 * and else by the name of the picture, which whoever hears the page hears. A band that
 * rests on part of what goes into it says so as a result does, in the two words after the
 * mark of what is not whole, and the step its peg stands on is chequered as the mark is.
 * What it rests on is said on the page of the area, which its name leads to.
 *
 * The pictures of the two ends are dress, and are of one size whatever the vibe: so the
 * steps of every gauge of a column begin on one line.
 */
export function VibeMark({ tag, placed, fact, under = UNDER_A_GAUGE, ends = ENDS_STAND }: Props) {
  const part = restsOnPart(fact);
  const where = whereInWords(tag, placed);
  const [low, high] = picturesAtEnds(tag.tag_id);
  return (
    <p className={styles.placed} data-under={under} data-ends={ends}>
      <span className={styles.gauge}>
        {ends === "gauge" ? <Art name={low} alt="" /> : null}
        {/* With words under it the picture is for the eye. With none, its name says them. */}
        <Track placed={placed} part={part} {...(under === "words" ? {} : { says: where })} />
        {ends === "gauge" ? <Art name={high} alt="" /> : null}
      </span>
      {under === "words" ? <span className={styles.where}>{where}</span> : null}
      {part ? (
        <>
          <span className="visually-hidden">. </span>
          <Approx />
        </>
      ) : null}
    </p>
  );
}
