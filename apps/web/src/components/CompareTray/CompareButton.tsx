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
  /**
   * True where the tray is far from the button, as it is from a result: the button then
   * says what the tray would, beside itself, and leads to the comparison.
   */
  readonly far?: boolean;
}

/**
 * Puts an area among those to compare, or takes it out. What it would do is
 * what it says, so that whether the area is chosen is never told by colour
 * alone. When four are chosen it can add no more, and says why where it
 * stands: the tray says so too, but the tray may be a long way off.
 *
 * Far from the tray, the button of an area that is chosen leads to the
 * comparison itself, so that the way on is beside what was just pressed.
 */
export function CompareButton({ area, className, far = false }: Props) {
  const id = useId();
  const { chosen: all, has, full, enough, toggle } = useCompare();
  const chosen = has(area.area_id);
  const off = !chosen && full;
  return (
    <span className={styles.beside}>
      <button
        type="button"
        className={["target", className].filter(Boolean).join(" ")}
        disabled={off}
        aria-describedby={off ? `${id}-why` : undefined}
        onClick={() => toggle(area)}
      >
        {chosen ? COMPARE.remove(area.name) : COMPARE.add(area.name)}
      </button>
      {off ? (
        <span id={`${id}-why`} className={styles.why}>
          {TRAY.full}
        </span>
      ) : null}
      {far && chosen ? (
        enough ? (
          // Which page a person reads next is told to no server ahead of time.
          <Link
            className={`${styles.near} target`}
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
