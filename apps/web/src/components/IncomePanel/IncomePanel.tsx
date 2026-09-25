"use client";

import { useCallback, useEffect, useId, useRef, useState, type SyntheticEvent } from "react";

import { INCOME } from "@/content/income";
import { api, type Client, type Failure } from "@/lib/api/client";
import type { IncomeOffer, IncomeShown as Served } from "@/lib/api/schema";

import profile from "../AreaProfile/AreaProfile.module.css";
import { wordsFor } from "../ErrorBlock/ErrorBlock";
import styles from "./IncomePanel.module.css";
import { INCOME_PART } from "./part";

interface Props {
  /** What route 11 says of household income: whether any is served, and the words that offer it. */
  readonly offer: IncomeOffer;
  /** The area whose page this is, by its slug. It comes from the release, never from a search. */
  readonly area: { readonly slug: string };
  /** The API to call. A test passes its own. */
  readonly client?: Client;
}

type State =
  | { readonly kind: "closed" }
  | { readonly kind: "asking" }
  | { readonly kind: "shown"; readonly data: Served }
  | { readonly kind: "failed"; readonly failure: Failure };

/** True where the service said that it serves none: the page was built while it served one. */
function servesNone(failure: Failure): boolean {
  return failure.kind === "api" && failure.code === "income_not_available";
}

/** The publisher's page for the estimates, where the address is one a browser may follow. */
function webAddress(url: string): string | null {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" ? parsed.href : null;
  } catch {
    return null;
  }
}

/**
 * The figure, as the API sent it: the name of the kind of income and the estimate, the
 * limits round it, the year, and the publisher's words for what it is. Every word and
 * every figure is the API's, and each is drawn as it came. Nothing stands beside the
 * figure, and nothing is drawn of it: no bar, no scale and no colour.
 */
function Figure({ data }: { readonly data: Served }) {
  const notes = useId();
  const address = webAddress(data.source_url);
  return (
    <div className={styles.shown}>
      <p className={styles.year}>{data.year_line}</p>
      <dl className={styles.figures}>
        <div>
          <dt>{data.kind}</dt>
          {/* Where the publisher gives none, that is said in the place of the figure. */}
          <dd>{data.estimate ?? data.none_given}</dd>
        </div>
        {data.limits === null ? null : (
          <div>
            <dt>{data.limits_label}</dt>
            <dd>{data.limits}</dd>
          </div>
        )}
      </dl>
      <p>{data.modelled}</p>
      <p>{data.definition}</p>
      <div role="group" aria-labelledby={notes}>
        <h3 id={notes} className={profile.small}>
          {INCOME.notes}
        </h3>
        <ol className={styles.notes}>
          {data.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ol>
      </div>
      <div className={styles.foot}>
        <p>{data.source_line}</p>
        <p>{data.licence_line}</p>
        {address === null ? null : (
          <p>
            {/* The publisher is told nothing of the page the person came from. */}
            <a className="target-min" href={address} rel="noreferrer noopener">
              {data.open_source}
            </a>
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * The household income of an area, as its publisher estimates it.
 *
 * It is closed until it is pressed, and the figure is asked for only then, from a route
 * of its own, as the census is. So it is not in the page as it is built, in its title,
 * its description or a link preview, and no answer is kept: the block is closed again on
 * every visit. It asks for one area, by the slug of the page, and sends nothing of a
 * search.
 *
 * Burro ranks no area on this figure, compares none by it and gives no reason from it.
 * So this reads nothing of a search, a comparison, a vibe or the map, and hands the figure
 * to nothing.
 */
export function IncomePanel({ offer, area, client = api }: Props) {
  const part = useRef<HTMLDetailsElement>(null);
  const asked = useRef<AbortController | null>(null);
  const [state, setState] = useState<State>({ kind: "closed" });

  const ask = useCallback(async () => {
    asked.current?.abort();
    const stop = new AbortController();
    asked.current = stop;
    setState({ kind: "asking" });
    const answer = await client.getIncome(area.slug, stop.signal);
    if (stop.signal.aborted) return;
    setState(answer.ok ? { kind: "shown", data: answer.data } : { kind: "failed", failure: answer.failure });
  }, [area.slug, client]);

  // What is asked for is let go when the page is left.
  useEffect(() => () => asked.current?.abort(), []);

  // A link that names the part opens it, as it opens every other part of the page.
  useEffect(() => {
    const openIfAskedFor = () => {
      if (window.location.hash === `#${INCOME_PART}` && part.current !== null) part.current.open = true;
    };
    openIfAskedFor();
    window.addEventListener("hashchange", openIfAskedFor);
    return () => window.removeEventListener("hashchange", openIfAskedFor);
  }, []);

  const onToggle = (event: SyntheticEvent<HTMLDetailsElement>) => {
    // Asked for once it is opened, and not again while the answer is in hand.
    if (event.currentTarget.open && state.kind === "closed") void ask();
  };

  if (!offer.available) return null;
  return (
    // A search engine is asked to quote nothing of it.
    <details ref={part} id={INCOME_PART} className={profile.closed} onToggle={onToggle} data-nosnippet="">
      <summary className="target">
        <h2 className={profile.opensTo}>{offer.heading}</h2>
      </summary>
      <div className={profile.part}>
        <p className={profile.lead}>{offer.intro}</p>
        <noscript>
          <p>{INCOME.noScript}</p>
        </noscript>
        {state.kind === "asking" ? (
          <p role="status" className={styles.state}>
            {INCOME.loading}
          </p>
        ) : null}
        {state.kind === "failed" ? (
          <div role="alert" className={styles.state}>
            <p>{wordsFor(state.failure)}</p>
            {servesNone(state.failure) ? null : (
              // Where the service serves none, asking again would bring the same answer.
              <>
                <p>{INCOME.failed}</p>
                <button type="button" className="target" onClick={() => void ask()}>
                  {INCOME.again}
                </button>
              </>
            )}
          </div>
        ) : null}
        {state.kind === "shown" ? <Figure data={state.data} /> : null}
      </div>
    </details>
  );
}
