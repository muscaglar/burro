import { ABOUT } from "@/content/about";
import { CANNOT_PLACE } from "@/content/facts";
import { PEG } from "@/content/kit";
import { STRIP } from "@/content/search";
import type { MetaData, Tag } from "@/lib/api/schema";
import { endsOf, inWords, plainly, VIBE_BANDS, type Placed } from "@/lib/vibes";

import { KeyGroup, KeyRow } from "../About/KeyRows";
import { Approx } from "../kit/Approx/Approx";
import { Art } from "../kit/Art/Art";
import { ENDS, pictureAtEnd, type End as WhichEnd } from "../kit/Ends/picture";
import { Thing } from "../kit/Thing/Thing";
import { Track } from "../Track/Track";
import styles from "./BandKey.module.css";
import { PAIRS_STAND, type PairsStand } from "./look";

interface Props {
  /**
   * The vibes of the release, from route 11. The states of a band are shown by the first of
   * them that runs one way, and a scale by the first that is one.
   */
  readonly meta: Pick<MetaData, "tags">;
  /** The id of its heading, which a link may lead to. Left out, it is the one it had. */
  readonly id?: string;
  /** Where the two pictures of every vibe stand. Left out, it is what `look.ts` chooses. */
  readonly pairs?: PairsStand;
}

/** A vibe as the key needs it: its id, its family, its name and the names of its ends. */
type Shown = Pick<Tag, "tag_id" | "family" | "label" | "low_end" | "high_end">;

/** Where a band of the key sits: in one band, and in no range. */
const at = (band: number): Placed => ({ band, spread_low: band, spread_high: band });

interface EndProps {
  readonly vibe: Shown;
  readonly at: WhichEnd;
  /** True where the name of the end stands under its picture. */
  readonly named: boolean;
}

/** One end of a gauge: its one picture, which is chosen by the id of its vibe, and its name where it is named. */
function End({ vibe, at: end, named }: EndProps) {
  const [low, high] = endsOf(vibe);
  return (
    <span className={styles.end} data-at={end}>
      <Art name={pictureAtEnd(vibe.tag_id, end)} alt="" />
      {named ? <span className={styles.endName}>{end === "low" ? low : high}</span> : null}
    </span>
  );
}

/** The name of a vibe, with its small drawing before it. The drawing is dress. */
function Named({ vibe }: { readonly vibe: Shown }) {
  return (
    <span className={styles.vibe} data-vibe={vibe.tag_id}>
      <Thing kind="tag" id={vibe.tag_id} family={vibe.family} />
      <span>{vibe.label}</span>
    </span>
  );
}

interface SitsProps {
  /** The vibe whose gauge it is: a vibe of the release, by which the pictures of its ends are chosen. */
  readonly vibe: Shown;
  /** Where the area of the key sits. `null` of an area the vibe could not be worked out for. */
  readonly placed: Placed | null;
  /** True where the band was worked out from some of what goes into the vibe. */
  readonly approx?: boolean;
  /** True where the name of each end stands under its picture, as it does of a scale. */
  readonly named?: boolean;
}

/**
 * One gauge of the key, as a gauge is drawn wherever it is met: the picture of the low end
 * of its vibe, five steps with a peg on one, and the picture of the high end. Beside it is
 * where the area sits in words, as the page of an area says it.
 *
 * It is one picture, and its name says what it shows: the band, and the two ends the bands
 * run between. What is drawn in it is for the eye.
 */
function Sits({ vibe, placed, approx = false, named = false }: SitsProps) {
  const [low, high] = endsOf(vibe);
  return (
    <span className={styles.sits}>
      <span
        className={styles.gauge}
        role="img"
        aria-label={placed === null ? PEG.empty : `${inWords(placed)}, ${STRIP.from(low, high)}`}
      >
        <End vibe={vibe} at="low" named={named} />
        <Track placed={placed} part={approx} />
        <End vibe={vibe} at="high" named={named} />
      </span>
      {/* A band the website has no word for is said by the picture alone. */}
      <span className={styles.words}>{placed === null ? CANNOT_PLACE : plainly(vibe, placed)}</span>
      {approx ? <Approx /> : null}
    </span>
  );
}

/**
 * How a band is drawn, state by state: the part of the key that is of the gauge, which
 * stands wherever Burro shows where an area sits on a vibe. Each state is the drawing
 * itself, as a page draws it, beside the line that says what is seen.
 *
 * It says what the two pictures of a vibe mean, and that neither end of a gauge is the
 * better one. The pictures of every vibe stand with the vibe, on the page this is a part
 * of: where the look has them stand here as well, each pair stands beside the name of its
 * vibe, under what the two mean.
 *
 * It is of no area. Its bands are written here, to show each state, and none is a figure
 * of a place. Every gauge is the gauge of a vibe of the release, by the name the API gives
 * the vibe and the names it gives its ends: no vibe is written into the website.
 *
 * Nothing of it can be pressed and nothing of it moves.
 */
export function BandKey({ meta, id = "key-steps", pairs = PAIRS_STAND }: Props) {
  const { states } = ABOUT.band;
  const oneWay = meta.tags.find((tag) => tag.low_end === null || tag.high_end === null);
  const scale = meta.tags.find((tag) => tag.low_end !== null && tag.high_end !== null);
  // What the states of a band are shown by: a vibe that runs one way, and a scale where the release holds no other.
  const shown = oneWay ?? scale;
  const lead = (
    <>
      <p>{ABOUT.band.lead}</p>
      {/* What the two pictures mean is said once: here, or beside the pictures where the key has them. */}
      {pairs === "vibe" && meta.tags.length > 0 ? <p>{ABOUT.band.pictures}</p> : null}
    </>
  );
  return (
    <KeyGroup id={id} title={ABOUT.band.title} lead={lead} lay="lines" className={styles.steps}>
      {oneWay === undefined ? null : (
        <KeyRow
          of="one-way"
          size="wide"
          drawn={
            <div className={styles.drawn}>
              <Named vibe={oneWay} />
              <ul className={styles.five} aria-label={ABOUT.band.five}>
                {VIBE_BANDS.map((band) => (
                  <li key={band}>
                    <Sits vibe={oneWay} placed={at(band)} />
                  </li>
                ))}
              </ul>
            </div>
          }
        >
          <p>{states.oneWay}</p>
        </KeyRow>
      )}
      {scale === undefined ? null : (
        <KeyRow
          of="scale"
          size="wide"
          drawn={
            <div className={styles.drawn}>
              <Named vibe={scale} />
              <Sits vibe={scale} placed={at(2)} named />
            </div>
          }
        >
          <p>{states.scale}</p>
        </KeyRow>
      )}
      {pairs !== "key" || meta.tags.length === 0 ? null : (
        <KeyRow
          of="ends"
          size="many"
          drawn={
            <ul className={styles.pairs} aria-label={ABOUT.band.pairs}>
              {meta.tags.map((tag) => (
                <li key={tag.tag_id}>
                  <Named vibe={tag} />
                  {/* What joins the three is for whoever hears the page: for the eye they are laid out apart. */}
                  <span className="visually-hidden">: </span>
                  <span className={styles.pair}>
                    {ENDS.map((end) => (
                      <span key={end} className={styles.ofPair}>
                        {end === "high" ? <span className="visually-hidden"> {ABOUT.band.to} </span> : null}
                        {/* Each end is its picture over its name, the low end first. */}
                        <End vibe={tag} at={end} named />
                      </span>
                    ))}
                  </span>
                </li>
              ))}
            </ul>
          }
        >
          <p>{states.ends}</p>
        </KeyRow>
      )}
      {shown === undefined ? null : (
        <>
          <KeyRow of="part" size="wide" drawn={<Sits vibe={shown} placed={at(2)} approx />}>
            <p>{states.part}</p>
          </KeyRow>
          <KeyRow of="mixed" size="wide" drawn={<Sits vibe={shown} placed={{ band: 3, spread_low: 2, spread_high: 4 }} />}>
            <p>{states.mixed}</p>
          </KeyRow>
          <KeyRow of="unplaced" size="wide" drawn={<Sits vibe={shown} placed={null} />}>
            <p>{states.unplaced}</p>
          </KeyRow>
        </>
      )}
    </KeyGroup>
  );
}
