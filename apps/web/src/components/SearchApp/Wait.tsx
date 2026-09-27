import type { CSSProperties } from "react";

import { STATUS } from "@/content/search";
import { WAIT } from "@/content/wait";

import { Burro } from "../kit/Burro/Burro";
import { Frame } from "../kit/Frame/Frame";
import styles from "./Wait.module.css";

/**
 * What his box holds the room of, where nothing stood there to be measured. `result`: the
 * first result, and no more. `answer`: what Burro understood as well, which comes with the
 * answer and stands over the first result, so that the first result ends where his box ended.
 */
export type Room = "result" | "answer";

interface Props {
  /**
   * How high what stood in the place of the first result was when the sentence was sent, in
   * pixels of the screen. `null` where nothing stood there, as on a first search.
   */
  readonly held: number | null;
  /** What his box holds the room of on a first search. The first result alone, where nothing is said. */
  readonly room?: Room;
  /**
   * What a person waits on. `reading`: a sentence that is read. `ranking`: a first ranking
   * that a control asked for, where nothing is read. The words under him say which, as the
   * line under the box does. A sentence, where nothing is said.
   */
  readonly of?: Awaited;
}

/** What a person waits on while he hops: a sentence that is read, or a first ranking that a control asked for. */
export type Awaited = "reading" | "ranking";

/** What stands under him, which is what the line under the box says of that moment. */
const SAYS: Readonly<Record<Awaited, string>> = { reading: STATUS.reading, ranking: WAIT.ranking };

/**
 * The wait. While a search is read Burro hops in and out of his hole, centre
 * stage, in the place where the results will stand, with the words that say
 * a search is being read under him. When the answer is in, the results stand
 * where he was. He hops there too while a first ranking that a control asked
 * for is worked out: a person waits there for a first answer as they do after
 * a sentence, and the words under him say what is worked out.
 *
 * His box is of one size whatever he does, so nothing on the page moves while
 * he hops. It is as high as the result that stood there, where one did, so
 * that nothing under him moves when he comes: and where none did, as high as
 * a first result is. The soil that flicks up from his hole is his: the part
 * that draws him draws it, inside his own box, and nothing here makes room
 * for it.
 *
 * He says nothing to a screen reader, and nor do the words under him: the
 * line under the box says them, to everyone, and is the one that is heard.
 */
export function Wait({ held, room = "result", of = "reading" }: Props) {
  const measured = held === null ? undefined : ({ "--held": `${held}px` } as CSSProperties);
  return (
    <div className={styles.wait} style={measured} aria-busy="true" data-wait="" data-room={room}>
      <Frame kind="box" bare className={styles.stage} aria-hidden="true">
        <span className={styles.meadow}>
          <Burro pose="hops" stage />
        </span>
        <span className={styles.says}>{SAYS[of]}</span>
      </Frame>
    </div>
  );
}
