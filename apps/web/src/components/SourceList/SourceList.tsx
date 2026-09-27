import type { CSSProperties } from "react";

import { SOURCES } from "@/content/sources";
import type { Metric, Source } from "@/lib/api/schema";
import { readableDate } from "@/lib/format";

import { Fold } from "../About/Fold";
import { pictureOf, sizeOf, type Drawing } from "../kit/drawings";
import { Frame } from "../kit/Frame/Frame";
import styles from "./SourceList.module.css";

interface Props {
  readonly sources: readonly Source[];
  /** The features of the release, each of which names the sources it came from. */
  readonly features: readonly Metric[];
}

/** The key of a source, as the look draws one. It stands before the name of each source, and opens nothing. */
const KEY: Drawing = "ui-key";

/** What the style sheet needs of the key to lay it before a name: its picture, and its size in art pixels. */
function ofTheKey(): CSSProperties {
  const { width, height } = sizeOf(KEY);
  return { "--key": `url("${pictureOf(KEY)}")`, "--key-w": width, "--key-h": height } as CSSProperties;
}

/** A gap a publisher's words leave to be filled: "[year]", or "20nn". */
const GAP = /\[[a-z ]+\]|\b20nn\b/i;

/** A web address is linked only if it is one. Anything else in the field is shown as text. */
function webAddress(url: string): string | null {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.href : null;
  } catch {
    return null;
  }
}

function PublisherPage({ url }: { url: string }) {
  if (url.trim() === "") return <>{SOURCES.noLink}</>;
  const address = webAddress(url);
  if (address === null) return <>{url}</>;
  return (
    // The publisher is told nothing of the page the person came from.
    <a href={address} rel="noreferrer noopener" className={`${styles.address} target-min`}>
      {url}
    </a>
  );
}

/**
 * Every source of the release, plainly, as a list: who published it, under which licence,
 * with its link, and the credit its publisher asks for, word for word. All of that is in
 * sight, because the licences of the data ask for it. What else is said of a source is
 * one press away: when Burro took its copy, and the measurements that came from it.
 *
 * Every word about a source is the API's. Each source is anchored by its id, so that a
 * figure anywhere on the website can lead to it, and stands in no fold.
 *
 * The list stands in one box, which brings the cream it is read on: there are many
 * sources, and a box with a shadow round each would be noise. Before the name of each is
 * the key of the look, which is what a source is known by.
 */
export function SourceList({ sources, features }: Props) {
  if (sources.length === 0) {
    return (
      <Frame kind="plain" as="p" className={styles.none}>
        {SOURCES.none}
      </Frame>
    );
  }
  const { rows, copied } = SOURCES;
  return (
    <Frame kind="box" bare className={styles.holder}>
      <ul className={styles.sources} style={ofTheKey()}>
        {sources.map((source) => {
          const usedFor = features.filter((metric) => metric.source_ids.includes(source.source_id));
          return (
            <li key={source.source_id} className={styles.source}>
              <article id={source.source_id} aria-labelledby={`${source.source_id}-name`}>
                <h2 id={`${source.source_id}-name`} className={styles.name}>
                  {source.name}
                </h2>
                <p className={styles.attribution}>{source.attribution}</p>
                {/* What the publisher's terms ask to be said wherever its credit is shown. It is
                    the API's, as the credit is, and stands under it. */}
                {(source.said_with_attribution ?? "") === "" ? null : (
                  <p className={styles.attribution}>{source.said_with_attribution}</p>
                )}
                {GAP.test(source.attribution) ? <p className={styles.unfinished}>{SOURCES.unfinished}</p> : null}
                <dl className={styles.facts}>
                  <div>
                    <dt>{rows.publisher}</dt>
                    <dd>{source.publisher}</dd>
                  </div>
                  <div>
                    <dt>{rows.licence}</dt>
                    <dd>{source.licence}</dd>
                  </div>
                  <div>
                    <dt>{rows.link}</dt>
                    <dd>
                      <PublisherPage url={source.url} />
                    </dd>
                  </div>
                </dl>
                <Fold says={SOURCES.more} of={source.name}>
                  <p>
                    {copied.before} <time dateTime={source.retrieved_on}>{readableDate(source.retrieved_on)}</time>
                    {copied.after}
                  </p>
                  {usedFor.length === 0 ? (
                    <p>{SOURCES.notUsed}</p>
                  ) : (
                    <>
                      <p>{SOURCES.usedFor}</p>
                      <ul className={styles.features}>
                        {usedFor.map((metric) => (
                          <li key={metric.feature_id}>{metric.label}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </Fold>
              </article>
            </li>
          );
        })}
      </ul>
    </Frame>
  );
}
