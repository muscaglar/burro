import { LEGEND } from "@/content/map";
import { BANDS } from "@/lib/map/fill";
import { endsOf, type Lens } from "@/lib/vibes";

import styles from "./MapView.module.css";

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
 */
export function MapLegend({
  searched,
  emptySpec = false,
  lens = null,
  filtered = true,
  unranked = true,
}: Props) {
  if (lens !== null) {
    const [low, high] = endsOf(lens.tag);
    const last = BANDS.length;
    return (
      <section className={styles.legend} aria-label={LEGEND.title}>
        <p className={styles.legendTitle}>{LEGEND.vibe(lens.tag.label)}</p>
        <ul>
          {BANDS.map(({ band }) => (
            <li key={band}>
              <span className={styles.swatch} data-band={band} aria-hidden="true" />
              {band === 1
                ? LEGEND.vibeEnd(band, low)
                : band === last
                  ? LEGEND.vibeEnd(band, high)
                  : LEGEND.vibeBand(band)}
            </li>
          ))}
          {lens.marks.some((mark) => mark.band === null) ? (
            <li>
              <span className={styles.swatch} data-pattern="unranked" aria-hidden="true" />
              {LEGEND.notPlaced}
            </li>
          ) : null}
        </ul>
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
              <span className={styles.pinSwatch} aria-hidden="true">
                1
              </span>
              {LEGEND.pin}
            </li>
          </>
        ) : null}
      </ul>
    </section>
  );
}
