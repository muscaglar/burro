import styles from "./Burro.module.css";
import { Drawn } from "./Drawn";
import { AT_REST, SOIL, type AtRest, type Soil } from "./look";
import type { Pose } from "./poses";

export { DRAWING, POSES, STILL, type Pose } from "./poses";

interface Props {
  readonly pose: Pose;
  /**
   * True where he is centre stage, as he is while a search is read: he is then drawn at
   * the art pixel of the stage, which is larger. Left out, he is drawn at the art pixel of
   * every drawing.
   */
  readonly stage?: boolean;
  /**
   * True where he is seen from behind a rule, as in the name board: he is drawn from his
   * back up, and his box is as wide as it was and 19 art pixels high. Left out, all of him
   * is drawn.
   */
  readonly peeps?: boolean;
  /**
   * True where what every page stands in draws him, and not the page: he is then no
   * drawing of the page, and does not keep himself out of the name board. Left out, he is
   * the page's.
   */
  readonly ofEveryPage?: boolean;
  /** What he does where nothing is asked of him. Left out, what the look says. */
  readonly atRest?: AtRest;
  /** What flies as he hops. Left out, what the look says. */
  readonly soil?: Soil;
}

/**
 * Burro, who is a rabbit. His box is 24 art pixels by 30 in every pose, so that a pose
 * that gives way to another moves nothing.
 *
 * He is never still for long. Where he sits, an ear twitches, his nose
 * goes, he blinks, he shifts his weight, and now and then he looks round or washes an
 * ear: each on a clock of its own, so that what he does next is not what he did at this
 * point the last time. While a search is read he hops in and out of his hole, and soil
 * flicks up from it as he goes down and as he comes up. Nothing of him or of his soil is
 * ever drawn outside his box, and nothing on the page moves when he does.
 *
 * He moves only where the length of a hop is more than nought: which it is where the
 * system says movement is welcome, and nowhere else. That is the one thing that stills
 * him. Nothing on the page stops him, and nothing of him takes a press.
 *
 * He says nothing to a screen reader, and the whole of him is kept from one. What happens
 * is said in words, by the page.
 */
export function Burro({ pose, stage = false, peeps = false, ofEveryPage = false, atRest = AT_REST, soil = SOIL }: Props) {
  const stirs = pose !== "hops" && atRest === "stirs";
  return (
    <span className={styles.burro} data-pose={pose} data-stage={stage} data-peeps={peeps} aria-hidden="true">
      <Drawn pose={pose} stirs={stirs} soil={soil === "flicks"} ofThePage={!ofEveryPage} />
    </span>
  );
}
