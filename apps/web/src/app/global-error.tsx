"use client";

import { LiveSyntheticBanner } from "@/components/SyntheticBanner/LiveSyntheticBanner";
import { FAULT, SITE } from "@/content/site";

import "@/styles/tokens.css";
import "@/styles/base.css";

import styles from "./global-error.module.css";

interface Props {
  // The error is not read. Its message could repeat what a person typed, so
  // the page says fixed words and reports nothing.
  /** Asks for the page again and draws it again. What "Try again" does, where there is one. */
  readonly retry?: () => void;
  /** Draws the page again from what is in hand. Used where there is no `retry`. */
  readonly reset?: () => void;
}

/**
 * The page shown when the layout itself fails, so that there is no shell to
 * show a fault in. It stands in for the whole document.
 *
 * It is not the page a fault in the server shows before anything is drawn:
 * that one is the framework's own, built as `_global-error.html`, and the
 * website has no say in it (docs/design/web.md, section 12).
 *
 * It shows no figure and names no place. It carries the banner when anything
 * this tab has read said the data was made up. When the layout fails on the
 * first page a tab opens, nothing is known of the data, and nothing is said.
 */
export default function GlobalError({ retry, reset }: Props) {
  return (
    <html lang="en-GB">
      <head>
        <title>{`${FAULT.title} · ${SITE.name}`}</title>
        <meta name="robots" content="noindex, nofollow" />
        <meta name="referrer" content="no-referrer" />
      </head>
      <body>
        <LiveSyntheticBanner />
        <main id="main" className={styles.main}>
          <div role="alert">
            <h1>{FAULT.title}</h1>
            <p>{FAULT.text}</p>
            <button type="button" className="target" onClick={() => (retry ?? reset)?.()}>
              {FAULT.retry}
            </button>
          </div>
        </main>
      </body>
    </html>
  );
}
