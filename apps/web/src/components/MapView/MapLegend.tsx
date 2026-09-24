import { LEGEND } from "@/content/map";
import { BANDS } from "@/lib/map/fill";

import styles from "./MapView.module.css";

interface Props {
  /** True once there is a ranking to colour the map by. */
  readonly searched: boolean;
  /** True when nothing is set to rank by, so no area has a band. */
  readonly emptySpec?: boolean;
}

/**
 * What the colours and the patterns of the map stand for, in figures and in
 * words. A band is a range of fit. It is not enough to read a fit from, and
 * nothing asks anyone to: the fit is a figure wherever it is shown.
 */
export function MapLegend({ searched, emptySpec = false }: Props) {
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
            <li>
              <span className={styles.swatch} data-pattern="filtered" aria-hidden="true" />
              {LEGEND.filtered}
            </li>
            <li>
              <span className={styles.swatch} data-pattern="unranked" aria-hidden="true" />
              {LEGEND.unranked}
            </li>
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
