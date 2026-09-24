import { RESTS_ON } from "@/content/bands";
import type { Fact, Tag } from "@/lib/api/schema";
import { inWords, isRange, plainly, type Placed } from "@/lib/vibes";

import { Track } from "../Track/Track";
import styles from "./CompareTable.module.css";

interface Props {
  /** The vibe, from route 11: the names of its ends. */
  readonly tag: Tag;
  /** Where the area sits on it, as the API says. */
  readonly placed: Placed;
  /** The fact of the vibe for the area: how many parts of its recipe have a figure, of how many. */
  readonly fact: Fact;
}

/**
 * What a band rests on, where that is not the whole of its recipe: the API's own clause where
 * the fact holds one, which is a sentence, and otherwise the two counts the fact does hold.
 */
function restsOn({ slots }: Fact): { readonly words: string; readonly sentence: boolean } | null {
  const { known, parts, partly } = slots;
  if (known === undefined || parts === undefined || known === parts) return null;
  return partly === undefined || partly === ""
    ? { words: RESTS_ON.short(known, parts), sentence: false }
    : { words: partly, sentence: true };
}

/**
 * Where one area sits on one vibe, as a comparison draws it: a mark on a line
 * of five, where it sits in words a person would use, and the band. A band
 * that rests on part of a recipe says so. It is never a colour alone, a
 * score or a percentage.
 */
export function VibeMark({ tag, placed, fact }: Props) {
  const plain = isRange(placed) ? null : plainly(tag, placed);
  const rests = restsOn(fact);
  return (
    <p className={styles.placed}>
      {/* The picture is for the eye. The words beside it say the same. */}
      <Track placed={placed} />
      <span>
        {plain === null ? null : `${plain}, `}
        <span className={styles.band}>{inWords(placed)}</span>
        {rests === null ? null : (
          <>
            {rests.sentence ? ". " : ", "}
            <span>{rests.words}</span>
          </>
        )}
      </span>
    </p>
  );
}
