"use client";

import Link from "next/link";
import { useId } from "react";

import { COMPARE, TRAY } from "@/content/compare";
import type { Chosen } from "@/lib/compare/list";
import { paths } from "@/lib/paths";
import { useCompare } from "@/lib/session/session";

import styles from "./CompareTray.module.css";

interface Props {
  /** The area, as the API names it. */
  readonly area: Chosen;
  readonly className?: string;
  /** True where the button stands in a row of small ones, as it does on a result. */
  readonly small?: boolean;
}

/**
 * Puts an area among those to compare, or takes it out. What it would do is
 * what it says, so that whether the area is chosen is never told by colour
 * alone. When four are chosen it can add no more, and says why where it
 * stands: the tray says so too, but the tray may be a long way off.
 *
 * The tray is at the foot of the screen, which may be a long way from the
 * button. So the button of an area that is chosen says beside itself what
 * the tray would, and leads to the comparison: the way on is beside what was
 * just pressed.
 */
export function CompareButton({ area, className, small = false }: Props) {
  const id = useId();
  const { chosen: all, has, full, enough, toggle } = useCompare();
  const chosen = has(area.area_id);
  const off = !chosen && full;
  return (
    <span className={styles.beside}>
      <button
        type="button"
        className={[small ? `${styles.small} target-min` : "target", className].filter(Boolean).join(" ")}
        disabled={off}
        aria-describedby={off ? `${id}-why` : undefined}
        // In a row of small buttons it says what it does in a word, and names the area to a screen reader.
        aria-label={small ? (chosen ? COMPARE.removeNamed(area.name) : COMPARE.addNamed(area.name)) : undefined}
        onClick={() => toggle(area)}
      >
        {small
          ? chosen
            ? COMPARE.removeShort
            : COMPARE.addShort
          : chosen
            ? COMPARE.remove(area.name)
            : COMPARE.add(area.name)}
      </button>
      {off ? (
        <span id={`${id}-why`} className={styles.why}>
          {TRAY.full}
        </span>
      ) : null}
      {chosen ? (
        enough ? (
          // Which page a person reads next is told to no server ahead of time.
          <Link
            className={`${styles.near} ${small ? "target-min" : "target"}`}
            href={paths.compare(all.map((one) => one.slug))}
            prefetch={false}
          >
            {TRAY.go(all.length)}
          </Link>
        ) : (
          <span className={styles.why}>{TRAY.one}</span>
        )
      ) : null}
    </span>
  );
}
