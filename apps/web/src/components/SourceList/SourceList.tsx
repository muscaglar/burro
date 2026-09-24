import { SOURCES } from "@/content/sources";
import type { Metric, Source } from "@/lib/api/schema";
import { readableDate } from "@/lib/format";

import styles from "./SourceList.module.css";

interface Props {
  readonly sources: readonly Source[];
  /** The features of the release, each of which names the sources it came from. */
  readonly features: readonly Metric[];
}

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
 * Every source of the release, each anchored by its id, with its licence, the
 * credit its publisher asks for, and the features that came from it. Every
 * word about a source is the API's.
 */
export function SourceList({ sources, features }: Props) {
  if (sources.length === 0) return <p>{SOURCES.none}</p>;
  const { rows } = SOURCES;
  return (
    <ul className={styles.sources}>
      {sources.map((source) => {
        const usedFor = features.filter((metric) => metric.source_ids.includes(source.source_id));
        return (
          <li key={source.source_id} className={styles.source}>
            <article id={source.source_id} aria-labelledby={`${source.source_id}-name`}>
              <h2 id={`${source.source_id}-name`} className={styles.name}>
                {source.name}
              </h2>
              <p className={styles.attribution}>{source.attribution}</p>
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
                  <dt>{rows.retrieved}</dt>
                  <dd>
                    <time dateTime={source.retrieved_on}>{readableDate(source.retrieved_on)}</time>
                  </dd>
                </div>
                <div>
                  <dt>{rows.link}</dt>
                  <dd>
                    <PublisherPage url={source.url} />
                  </dd>
                </div>
              </dl>
              <h3 className={styles.usedFor}>{rows.usedFor}</h3>
              {usedFor.length === 0 ? (
                <p className="muted">{SOURCES.notUsed}</p>
              ) : (
                <ul className={styles.features}>
                  {usedFor.map((metric) => (
                    <li key={metric.feature_id}>{metric.label}</li>
                  ))}
                </ul>
              )}
            </article>
          </li>
        );
      })}
    </ul>
  );
}
