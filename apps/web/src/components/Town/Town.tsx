import { TOWN } from "@/content/town";
import type { Mark } from "@/lib/town/bands";
import type { Release } from "@/lib/town/release";
import { blankSaid } from "@/lib/town/said";
import { townOf } from "@/lib/town/town";

import { Drawing } from "./Drawing";
import styles from "./Town.module.css";

interface Props {
  /**
   * Where the area sits on the vibes of the release, as the service sent it: the `tags` of
   * an area's page, the strip of a result, or `marksOf` the bands of every area. Four of
   * them are read, and nothing else of the area is handed over: no name that is drawn, no
   * rank and no fit.
   */
  readonly marks: readonly Mark[];
  /** What the release holds, from route 11: its vibes with their names and the names of their ends, and its measures. */
  readonly meta: Release;
  /** The name of the area, as the service gives it. It is said to a screen reader, and is not drawn. */
  readonly of?: string;
  /**
   * True where what each part is drawn from is written out under the line, in sight, as
   * it is where there is room. Left out, it is said in the name of the drawing.
   */
  readonly written?: boolean;
  /**
   * True where the town stands on the grass, and not in a box. Its words then stand in a
   * box of their own, since nothing is read on the grass.
   */
  readonly onGrass?: boolean;
  /**
   * True where the town stands beside the title of a page, which is set larger than the
   * name of a result: it is then drawn at the art pixel of the screen, as every drawing is.
   * Left out, it is drawn at the pixel of the ground, which is two pixels of the screen on
   * every screen, so that it is never larger than the name it stands beside.
   */
  readonly large?: boolean;
  /** A class of whatever lays the town out. It sets where the town stands, never how it is drawn. */
  readonly className?: string;
}

/**
 * The town of an area: a few buildings and trees on a plot of meadow, built by rule from
 * where the area sits on four vibes. One vibe is its trees, one the height of its
 * buildings, one its lit windows and one its roofs.
 *
 * It is a drawing made from four figures. It is not a picture of the place, and the line
 * that says so stands with it, in sight, wherever it is drawn. What it is made of is said
 * band by band: in the name of the drawing, or written out under the line.
 *
 * It holds its line twice, whole and in short, and a style sheet draws one of the two: the
 * short one at the head of the page of an area on a narrow screen, where what the area is
 * like comes first, and the whole one everywhere else. The one that is not drawn is heard
 * by nobody. The short one stands outside what the town says under its drawing, so that
 * whatever lays a town out finds there what it found.
 *
 * It is of one size whatever it is drawn for, the first result or the tenth. What is not
 * known of an area is left blank, and is said to be.
 */
export function Town({ marks, meta, of, written = false, onGrass = false, large = false, className }: Props) {
  const { pieces, said } = townOf(marks, meta);
  const blank = blankSaid(said);
  const name = of === undefined ? TOWN.name : TOWN.nameOf(of);
  const parts = said.map((part) => `${part.name}: ${part.says}.`);
  return (
    <figure
      className={className === undefined ? styles.town : `${styles.town} ${className}`}
      data-on={onGrass ? "grass" : "page"}
      data-written={written}
    >
      {/* Written out under the line, the parts are read there, and are not said twice. */}
      <Drawing pieces={pieces} says={written ? `${name}.` : [`${name}.`, ...parts].join(" ")} large={large} />
      <span className={styles.short} data-line="short">
        {TOWN.short}
      </span>
      <figcaption className={styles.says}>
        <span className={styles.line}>{TOWN.line}</span>
        {written ? (
          <ul className={styles.parts} aria-label={TOWN.madeOf}>
            {said.map((part) => (
              <li key={part.part} className={styles.part} data-state={part.state}>
                <span className={styles.name}>{part.name}</span>
                <span>{part.says}</span>
              </li>
            ))}
          </ul>
        ) : blank === null ? null : (
          <span className={styles.blank}>{blank}</span>
        )}
      </figcaption>
    </figure>
  );
}
