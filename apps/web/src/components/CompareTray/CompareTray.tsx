"use client";

import Link from "next/link";
import { useId } from "react";

import { TRAY } from "@/content/compare";
import { useCompare } from "@/lib/session/session";
import { paths } from "@/lib/paths";

import styles from "./CompareTray.module.css";

/** What the tray says of how many areas are chosen. It is said aloud when it changes. */
export function trayStatus(count: number, full: boolean): string {
  if (count === 0) return TRAY.none;
  if (count === 1) return TRAY.one;
  return full ? TRAY.full : "";
}

/**
 * The areas chosen to compare, and the link that compares them. It has its
 * place on the page whether or not anything is chosen, so that choosing an
 * area moves nothing.
 *
 * The link holds the slugs of the areas and nothing else. It is followed
 * when it is pressed and not fetched before.
 */
export function CompareTray() {
  const id = useId();
  const { chosen, enough, full, toggle, clear } = useCompare();
  const status = trayStatus(chosen.length, full);
  return (
    <section className={styles.tray} aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`} className={styles.title}>
        {TRAY.title}
      </h2>
      {chosen.length > 0 ? (
        <ul className={styles.chosen}>
          {chosen.map((area) => (
            <li key={area.area_id} className={styles.area}>
              <span className={styles.name}>{area.name}</span>
              <button
                type="button"
                className={`${styles.remove} target`}
                aria-label={TRAY.remove(area.name)}
                onClick={() => toggle(area)}
              >
                <span aria-hidden="true">×</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      <p className={styles.status} role="status">
        {status}
      </p>
      {chosen.length > 0 ? (
        <div className={styles.actions}>
          {enough ? (
            <Link
              className={`${styles.go} target`}
              href={paths.compare(chosen.map((area) => area.slug))}
              prefetch={false}
            >
              {TRAY.go(chosen.length)}
            </Link>
          ) : null}
          <button type="button" className="target" onClick={clear}>
            {TRAY.clear}
          </button>
        </div>
      ) : null}
    </section>
  );
}
