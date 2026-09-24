import { SHARED } from "@/content/share";
import type { Meta } from "@/lib/api/schema";
import type { Shared } from "@/lib/search/state";

import styles from "./SharedSearch.module.css";

interface Props {
  /** What the API said of the share when it was opened. */
  readonly shared: Pick<Shared, "coarsened" | "stale" | "original_release_id">;
  /** The release the search is ranked on now. */
  readonly release: Meta["release_id"];
  /** True when the search names a place to reach. */
  readonly hasPlaces: boolean;
  /** False where the page's own heading already says it is a shared search. */
  readonly titled?: boolean;
}

/**
 * Says that the search on screen came from a link, what such a link holds,
 * and how this one may differ from what its sender saw: a place stood in for
 * by a station or a district, or data that has changed since.
 */
export function SharedHeader({ shared, release, hasPlaces, titled = true }: Props) {
  return (
    <section className={styles.header} aria-label={SHARED.title}>
      {titled ? <h2 className={styles.title}>{SHARED.title}</h2> : null}
      <p>{SHARED.text}</p>
      <p>{SHARED.holds}</p>
      {shared.coarsened ? <p>{SHARED.coarsened}</p> : hasPlaces ? <p>{SHARED.exact}</p> : null}
      {shared.stale ? (
        <p>
          {SHARED.stale} {SHARED.madeOn} <code>{shared.original_release_id}</code>. {SHARED.shownOn}{" "}
          <code>{release}</code>.
        </p>
      ) : null}
    </section>
  );
}
