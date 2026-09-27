import { useId } from "react";

import { TOWN } from "@/content/town";
import type { MetaData } from "@/lib/api/schema";
import { isPlaced } from "@/lib/holds";
import { NOTHING_KNOWN, type Bands } from "@/lib/town/bands";
import { piecesOf } from "@/lib/town/pieces";
import { planOf } from "@/lib/town/plan";
import { mayBeDrawn, vibesOf, type Release } from "@/lib/town/release";
import { endsOf } from "@/lib/vibes";

import { KeyGroup, KeyRow } from "../About/KeyRows";
import { Drawing } from "./Drawing";
import styles from "./TownKey.module.css";

interface Props {
  /** What the release holds, from route 11: its vibes, its measures, and which vibes place any area. */
  readonly meta: Release & Pick<MetaData, "recipes">;
  /**
   * The id of its heading, which a link may lead to. Left out, it is one the page makes up,
   * which is not the same from one build to the next.
   */
  readonly id?: string;
  /** A class of whatever lays the key out. It sets where the key stands, never how it is drawn. */
  readonly className?: string;
}

/** The vibes a town is drawn from, each with whether a town of this release may draw it. */
const drawnFrom = (meta: Props["meta"]) =>
  vibesOf(meta).map((vibe) => ({
    ...vibe,
    // A part is drawn where a town may draw its vibe, and some area of the release has a band for it.
    placed: mayBeDrawn(vibe) && vibe.tag !== undefined && isPlaced(meta, vibe.tag.tag_id),
  }));

/** What a town of this release may hold: the middle of each part it can draw, and nothing of the rest. */
const middleOf = (vibes: ReturnType<typeof drawnFrom>) =>
  Object.fromEntries(vibes.map(({ part, placed }) => [part, placed ? 3 : null])) as Bands;

const drawn = (bands: Bands) => piecesOf(planOf(bands));

/**
 * A town of the key, and nothing beside it: the middle of every part this release can
 * draw. It is dress, for whatever leads to the part of the key that says what a town is
 * built of: it says nothing, and that part says what every town is and is not.
 */
export function TownOfTheKey({ meta }: Pick<Props, "meta">) {
  return <Drawing pieces={drawn(middleOf(drawnFrom(meta)))} says="" />;
}

/**
 * What a town is built of: the part of the key to the drawings that is of the town of an
 * area. A row for each part, with what the part is drawn from and a town at each end of it.
 *
 * Every town of the key is drawn by the rule that draws the town of an area, from bands
 * that are written here: the part at one end, and every other part in the middle. A part
 * the release cannot draw for any area is left blank in the key too, so that the key shows
 * no town that the release could not.
 *
 * The name of a vibe and the names of its ends are the service's. Neither end is the good
 * end, and the two are drawn alike: one size, and no mark on either.
 */
export function TownKey({ meta, id, className }: Props) {
  const madeUp = useId();
  const vibes = drawnFrom(meta);
  const middle = middleOf(vibes);
  return (
    <KeyGroup
      id={id ?? madeUp}
      title={TOWN.key.title}
      className={className === undefined ? styles.towns : `${styles.towns} ${className}`}
      lead={
        <>
          <p>{TOWN.key.lead}</p>
          <p>{TOWN.key.ends}</p>
        </>
      }
    >
      {vibes.map(({ part, tag, placed, crime }) => {
        if (tag === undefined || !placed) {
          return (
            // No town is drawn of it: what is said of it has the row to itself.
            <KeyRow key={part} of={`built-of-${part}`} part={part} size="many" drawn={null}>
              <p>
                {/* A vibe the release names is named, though no town is drawn from it. */}
                <span className={styles.vibe}>{tag?.label ?? TOWN.key.noVibe}</span> <span>{TOWN.key.is[part]}</span>
              </p>
              <p>{crime ? TOWN.key.countsCrime : TOWN.key.notYet}</p>
            </KeyRow>
          );
        }
        const [low, high] = endsOf(tag);
        return (
          <KeyRow
            key={part}
            of={`built-of-${part}`}
            part={part}
            size="wide"
            drawn={
              <>
                <span className={styles.end}>
                  <Drawing pieces={drawn({ ...middle, [part]: 1 })} says="" />
                  <span className={styles.name}>{low}</span>
                </span>
                <span className={styles.end}>
                  <Drawing pieces={drawn({ ...middle, [part]: 5 })} says="" />
                  <span className={styles.name}>{high}</span>
                </span>
              </>
            }
          >
            <p>
              <span className={styles.vibe}>{tag.label}</span> <span>{TOWN.key.is[part]}</span>
            </p>
          </KeyRow>
        );
      })}
      <KeyRow
        of="built-of-blank"
        part="blank"
        size="wide"
        drawn={
          <span className={styles.end}>
            <Drawing pieces={drawn(NOTHING_KNOWN)} says="" />
          </span>
        }
      >
        <p>
          <span className={styles.vibe}>{TOWN.key.notKnown}</span> <span>{TOWN.key.isBlank}</span>
        </p>
        <p>{TOWN.key.blank}</p>
      </KeyRow>
    </KeyGroup>
  );
}
