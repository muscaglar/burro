import { LEGEND } from "@/content/map";
import { BANDS } from "@/lib/map/fill";
import { endsOf, type Lens } from "@/lib/vibes";

import { Ends } from "../kit/Ends/Ends";
import { Thing } from "../kit/Thing/Thing";
import styles from "./MapView.module.css";
import { pinDrawn } from "./pin";

interface Props {
  /** True once there is a ranking to colour the map by. */
  readonly searched: boolean;
  /** True when nothing is set to rank by, so no area has a band. */
  readonly emptySpec?: boolean;
  /** The vibe the map is coloured by, before a search. */
  readonly lens?: Lens | null;
  /**
   * Whether a limit left any area out, and whether any area is not ranked. A pattern is
   * explained only where the map draws it: the legend spoke of "a limit you set" under a
   * search that set none. Left out, both are explained.
   */
  readonly filtered?: boolean;
  readonly unranked?: boolean;
}

/**
 * What the colours and the patterns of the map stand for, in figures and in
 * words. A band is a range of fit, or one of the five bands of a vibe, with
 * its two ends named. It is not enough to read a figure from, and nothing
 * asks anyone to: the figure is in words wherever it is shown.
 *
 * Each is drawn beside its words as the map draws it: a band as a piece of
 * land of its colour with its grain, a pattern as it lies on the land, and the
 * pin as the drawing it is.
 *
 * Where the map is coloured by one vibe the legend is the gauge of that vibe:
 * the small drawing of the vibe with its name, and under it the five shades in
 * a row, from the palest to the darkest, with the one picture of each end of
 * the vibe at either side and the name of the end under its picture. Neither
 * end is the better one. The pictures are chosen by the id of the vibe.
 */
export function MapLegend({
  searched,
  emptySpec = false,
  lens = null,
  filtered = true,
  unranked = true,
}: Props) {
  if (lens !== null) {
    const { tag } = lens;
    const [low, high] = endsOf(tag);
    return (
      <section className={styles.legend} aria-label={LEGEND.title} data-of="vibe">
        <p className={styles.legendTitle}>
          {/* The drawing of the vibe is dress, and says nothing: its name is in the line beside it. */}
          <Thing kind="tag" id={tag.tag_id} family={tag.family} />
          {LEGEND.vibe(tag.label)}
        </p>
        {/* One picture, whose name says what it shows. What is drawn in it is for the eye. */}
        <p className={styles.gauge} role="img" aria-label={LEGEND.vibeRuns(low, high)}>
          <Ends id={tag.tag_id} low={tag.low_end} high={tag.high_end}>
            <span className={styles.shades}>
              {BANDS.map(({ band }) => (
                <span key={band} className={styles.swatch} data-band={band} />
              ))}
            </span>
          </Ends>
        </p>
        {lens.marks.some((mark) => mark.band === null) ? (
          <ul>
            <li>
              <span className={styles.swatch} data-pattern="unranked" aria-hidden="true" />
              {LEGEND.notPlaced}
            </li>
          </ul>
        ) : null}
      </section>
    );
  }
  return (
    <section className={styles.legend} aria-label={LEGEND.title}>
      <ul>
        {searched && !emptySpec ? (
          [...BANDS].reverse().map(({ band, from, to }) => (
            <li key={band}>
              <span className={styles.swatch} data-band={band} aria-hidden="true" />
              {LEGEND.fit} {LEGEND.band(from, to)}
            </li>
          ))
        ) : (
          <li>
            <span className={styles.swatch} data-band={0} aria-hidden="true" />
            {LEGEND.noScore}
          </li>
        )}
        {searched ? (
          <>
            {filtered ? (
              <li>
                <span className={styles.swatch} data-pattern="filtered" aria-hidden="true" />
                {LEGEND.filtered}
              </li>
            ) : null}
            {unranked ? (
              <li>
                <span className={styles.swatch} data-pattern="unranked" aria-hidden="true" />
                {LEGEND.unranked}
              </li>
            ) : null}
            <li>
              <span className={styles.pinSwatch} style={pinDrawn()} aria-hidden="true">
                <span className={styles.figure}>1</span>
              </span>
              {LEGEND.pin}
            </li>
          </>
        ) : null}
      </ul>
    </section>
  );
}
