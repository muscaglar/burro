import { SHARED } from "@/content/share";
import type { Meta } from "@/lib/api/schema";
import { paths } from "@/lib/paths";
import type { Shared } from "@/lib/search/state";

import { Art } from "../kit/Art/Art";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
import { NOTICE_STANDS, type NoticeStands } from "./look";
import { takeTheWay } from "./own";
import styles from "./SharedSearch.module.css";

/** What is said of a shared search: what the API said of the share, and what it is shown on. */
export interface Told {
  /** What the API said of the share when it was opened. */
  readonly shared: Pick<Shared, "coarsened" | "stale" | "original_release_id">;
  /** The release the search is ranked on now. */
  readonly release: Meta["release_id"];
  /** True when the search names a place to reach. */
  readonly hasPlaces: boolean;
}

interface Props extends Told {
  /** False where the page's own heading already says it is a shared search. */
  readonly titled?: boolean;
  /** Where it stands. Left out, it stands where the one line of `look.ts` says. */
  readonly stands?: NoticeStands;
}

/**
 * Every sentence that is said of a search that came from a link, in the order it is said:
 * that it came from one, what such a link holds, and how this one may differ from what its
 * sender saw: a place stood in for by a station or a district, or data that has changed since.
 *
 * It ends in the way to a search of one's own. "Start again" opens the search again as the
 * link holds it, so a person who was sent a link had no way from the page to a search of
 * their own but the name of the website. It is a button of the look and no more: what
 * matters most on a search is Search. Pressed, it leads to the search page, and the page
 * a link opens begins the search again as it is left. Opened in another tab or window, it
 * leaves this page as it is: the search page begins afresh there.
 */
function Said({ shared, release, hasPlaces }: Told) {
  return (
    <>
      <p>{SHARED.text}</p>
      <p>{SHARED.holds}</p>
      {shared.coarsened ? <p>{SHARED.coarsened}</p> : hasPlaces ? <p>{SHARED.exact}</p> : null}
      {shared.stale ? (
        <p>
          {SHARED.stale} {SHARED.madeOn} <code>{shared.original_release_id}</code>. {SHARED.shownOn}{" "}
          <code>{release}</code>.
        </p>
      ) : null}
      <p>
        <Press
          href={paths.home()}
          onPress={(event) => {
            const elsewhere = event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
            if (!elsewhere) takeTheWay();
          }}
        >
          {SHARED.own}
        </Press>
      </p>
    </>
  );
}

/**
 * What says that a search came from a link, as what a fold opens to: a notice, plain and
 * flat. Cream inside a rule of ink, with a band of amber at its start and its words in
 * ink. It brings the cream it is read on. What opened it says what it is, so it has no
 * heading of its own.
 */
export function SharedNotice(told: Told) {
  return (
    <Frame as="section" kind="plain" bare className={styles.header} aria-label={SHARED.title}>
      <Said {...told} />
    </Frame>
  );
}

/**
 * Says that the search on screen came from a link, what such a link holds, and how this
 * one may differ from what its sender saw, where the page draws it: over the box.
 *
 * The answer comes first. So it is said in short, in one line that says what the search is
 * and opens in place, in the browser's own element: drawn in full it stood a third of a
 * phone's screen high over the answer, and the first result of a shared search was out of
 * sight. It is drawn as a notice is: plain and flat, cream inside a rule of ink, with a
 * band of amber at its start and its words in ink.
 *
 * Where it stands after the first result it is not drawn here at all: the way to share a
 * search stands there, and draws the way to it beside its own (`SharedFold`).
 */
export function SharedHeader({ titled = true, stands = NOTICE_STANDS, ...told }: Props) {
  if (stands === "after") return null;
  return (
    <Frame as="section" kind="plain" bare className={styles.header} aria-label={SHARED.title} data-stands="over">
      <details className={styles.opens}>
        <summary className="target-min">
          <span className={styles.mark}>
            <Art name="ui-arrow" alt="" />
          </span>
          {/* A short label, in the face of names. It is a heading where the page has none that says it. */}
          {titled ? (
            <h2 className={styles.title}>{SHARED.title}</h2>
          ) : (
            <span className={styles.title}>{SHARED.title}</span>
          )}
        </summary>
        <div className={styles.says}>
          <Said {...told} />
        </div>
      </details>
    </Frame>
  );
}
