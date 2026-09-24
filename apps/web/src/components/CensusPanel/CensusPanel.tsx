"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
  type SyntheticEvent,
} from "react";

import { CENSUS } from "@/content/census";
import { api, type Client, type Failure } from "@/lib/api/client";
import type {
  CensusOffer,
  CensusPanel as Served,
  CensusPanelRow,
  CensusPanelTable,
} from "@/lib/api/schema";
import { paths } from "@/lib/paths";

import profile from "../AreaProfile/AreaProfile.module.css";
import { wordsFor } from "../ErrorBlock/ErrorBlock";
import styles from "./CensusPanel.module.css";
import { CENSUS_PART } from "./part";

interface Props {
  /** What route 11 says of the census: whether any is served, and the words that offer it. */
  readonly offer: CensusOffer;
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

/** True where the service said that it serves no census: the page was built while it served one. */
function servesNone(failure: Failure): boolean {
  return failure.kind === "api" && failure.code === "census_not_available";
}

/** The publisher's page for a table, where the address is one a browser may follow. */
function webAddress(url: string): string | null {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" ? parsed.href : null;
  } catch {
    return null;
  }
}

/**
 * The same share, drawn: a bar for the area, and a mark for the whole city. It
 * is a picture of what the two cells say in words, so it is kept from a
 * screen reader. Every bar of every table is drawn alike: no colour, shade or
 * size says that a figure is much or little, or that one row is unlike another.
 */
function Picture({ row }: { readonly row: CensusPanelRow }) {
  // Where neither share is a figure there is nothing to draw, and a line alone says nothing.
  if (row.percent === null && row.city_percent === null) return null;
  return (
    <svg
      className={styles.picture}
      viewBox="0 0 100 10"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
    >
      <line className={styles.line} x1="0" y1="9.5" x2="100" y2="9.5" />
      {row.percent === null ? null : (
        <rect className={styles.bar} x="0" y="3" width={row.percent} height="6.5" />
      )}
      {row.city_percent === null ? null : (
        <line className={styles.mark} x1={row.city_percent} y1="0" x2={row.city_percent} y2="10" />
      )}
    </svg>
  );
}

interface CellProps {
  /** Whose figure it is: the heading of the column, said again where the rows are stacked. */
  readonly name: string;
  /** The figure in words, as the API sent it. */
  readonly says: string;
  readonly children?: ReactNode;
}

/**
 * One figure of a row. It says its role again, because a browser forgets that a
 * cell is a cell once it is laid out as a block, as it is on a narrow screen.
 */
function Cell({ name, says, children }: CellProps) {
  return (
    // eslint-disable-next-line jsx-a11y/no-interactive-element-to-noninteractive-role
    <td role="cell" className={styles.cell}>
      <span className={styles.cellName}>{name} </span>
      <span className={styles.figure}>
        <span className={styles.said}>{says}</span>
        {children}
      </span>
    </td>
  );
}

/** What stands under a table: what it counts in the publisher's words, and the way to its source. */
function Under({ table }: { readonly table: CensusPanelTable }) {
  const address = webAddress(table.source_url);
  return (
    <div className={styles.under}>
      <p>{table.definition}</p>
      {table.note === null ? null : <p>{table.note}</p>}
      {table.shown_only === null ? null : <p>{table.shown_only}</p>}
      <p className={styles.links}>
        {/* Which source a person went on to read is told to nobody ahead of time. */}
        <Link className="target-min" href={paths.sources(table.source_id)} prefetch={false}>
          {CENSUS.source}
        </Link>
        {address === null ? null : (
          // The publisher is told nothing of the page the person came from.
          <a className="target-min" href={address} rel="noreferrer noopener">
            {table.source_label}
          </a>
        )}
      </p>
    </div>
  );
}

/**
 * One table of the census. It is closed until it is pressed, under its own
 * name, so that what is opened is what a person chose to read: five tables
 * open at once are thirteen screens of a phone. It is the browser's own
 * element, and nothing is asked for when it opens.
 *
 * A table that is left out for the area says so, and holds nothing to open.
 */
function Table({ table }: { readonly table: CensusPanelTable }) {
  if (table.left_out !== null) {
    return (
      <div className={styles.table} role="group" aria-label={table.title} data-table={table.table_code}>
        {/* It says so, and gives no figure. Nothing is filled in, and nothing more is said. */}
        <p className={styles.leftOut}>{table.left_out}</p>
      </div>
    );
  }
  return (
    <details
      className={`${profile.closed} ${styles.table}`}
      aria-label={table.title}
      data-table={table.table_code}
    >
      <summary className="target">
        <h3 className={profile.opensTo}>{table.title}</h3>
      </summary>
      <div className={styles.opened}>
        <table role="table" className={styles.figures}>
          <caption>{table.caption}</caption>
          {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
          <thead role="rowgroup" className={styles.head}>
            <tr role="row">
              <th role="columnheader" scope="col">
                {table.columns.label}
              </th>
              <th role="columnheader" scope="col">
                {table.columns.share}
              </th>
              <th role="columnheader" scope="col">
                {table.columns.count}
              </th>
              <th role="columnheader" scope="col">
                {table.columns.city}
              </th>
            </tr>
          </thead>
          {/* In the order the API sent them, which is the publisher's. Nothing here sorts. */}
          {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
          <tbody role="rowgroup">
            {table.rows.map((row) => (
              <tr role="row" key={row.code} className={styles.row}>
                <th role="rowheader" scope="row" className={styles.label} data-depth={row.depth}>
                  {row.heading === row.label ? (
                    row.label
                  ) : (
                    <>
                      {/* A row under a group is read whole, and printed under its group. */}
                      <span className="visually-hidden">{row.heading}</span>
                      <span aria-hidden="true">{row.label}</span>
                    </>
                  )}
                </th>
                <Cell name={table.columns.share} says={row.share}>
                  <Picture row={row} />
                </Cell>
                <Cell name={table.columns.count} says={row.count ?? CENSUS.noCount} />
                <Cell name={table.columns.city} says={row.city_share} />
              </tr>
            ))}
          </tbody>
        </table>
        <Under table={table} />
      </div>
    </details>
  );
}

function Figures({ data }: { readonly data: Served }) {
  const notes = useId();
  // The picture is explained where there is one: a table that is left out draws nothing.
  const drawn = data.tables.find((table) => table.rows.length > 0);
  return (
    <div className={styles.shown}>
      <p className={styles.date}>{data.date_line}</p>
      <div role="group" aria-labelledby={notes}>
        <h3 id={notes} className={profile.small}>
          {CENSUS.notes}
        </h3>
        <ol className={styles.notes}>
          {data.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ol>
        {drawn === undefined ? null : (
          // The name of the area is the heading of its own column, as the API sent it.
          <p className={styles.legend}>{CENSUS.picture(drawn.columns.share, data.city)}</p>
        )}
      </div>
      <div className={styles.tables}>
        {data.tables.map((table) => (
          <Table key={table.table_code} table={table} />
        ))}
      </div>
      <div className={styles.foot}>
        <p>{data.source_line}</p>
        <p>{data.derivation_line}</p>
        <p>{data.licence_line}</p>
      </div>
    </div>
  );
}

/**
 * The census figures of an area: who lived there on the day of the census.
 *
 * It is closed until it is pressed, and the figures are asked for only then,
 * from a route of their own. So they are not in the page as it is built, in
 * its title, its description or a link preview, and no answer is kept: the
 * block is closed again on every visit. It asks for one area, by the slug of
 * the page, and sends nothing of a search.
 *
 * Once the figures have come, each table is closed under its own name until it
 * is pressed. Every word about a figure is the API's, and every row is drawn in
 * the order it came. A figure stands beside the whole city's figure for the same thing,
 * and beside nothing else: no other area, no rank, no fit. Nothing here sorts,
 * filters or colours by a figure. It is a table first, and the picture in it
 * says only what the table says.
 */
export function CensusPanel({ offer, area, client = api }: Props) {
  const part = useRef<HTMLDetailsElement>(null);
  const asked = useRef<AbortController | null>(null);
  const [state, setState] = useState<State>({ kind: "closed" });

  const ask = useCallback(async () => {
    asked.current?.abort();
    const stop = new AbortController();
    asked.current = stop;
    setState({ kind: "asking" });
    const answer = await client.getCensus(area.slug, stop.signal);
    if (stop.signal.aborted) return;
    setState(answer.ok ? { kind: "shown", data: answer.data } : { kind: "failed", failure: answer.failure });
  }, [area.slug, client]);

  // What is asked for is let go when the page is left.
  useEffect(() => () => asked.current?.abort(), []);

  // A link that names the part opens it, as it opens every other part of the page.
  useEffect(() => {
    const openIfAskedFor = () => {
      if (window.location.hash === `#${CENSUS_PART}` && part.current !== null) part.current.open = true;
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
    <details ref={part} id={CENSUS_PART} className={profile.closed} onToggle={onToggle} data-nosnippet="">
      <summary className="target">
        <h2 className={profile.opensTo}>{offer.heading}</h2>
      </summary>
      <div className={profile.part}>
        <p className={profile.lead}>{offer.intro}</p>
        <noscript>
          <p>{CENSUS.noScript}</p>
        </noscript>
        {state.kind === "asking" ? (
          <p role="status" className={styles.state}>
            {CENSUS.loading}
          </p>
        ) : null}
        {state.kind === "failed" ? (
          <div role="alert" className={styles.state}>
            <p>{wordsFor(state.failure)}</p>
            {servesNone(state.failure) ? null : (
              // Where the service serves no census, asking again would bring the same answer.
              <>
                <p>{CENSUS.failed}</p>
                <button type="button" className="target" onClick={() => void ask()}>
                  {CENSUS.again}
                </button>
              </>
            )}
          </div>
        ) : null}
        {state.kind === "shown" ? <Figures data={state.data} /> : null}
      </div>
    </details>
  );
}
