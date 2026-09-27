"use client";

import Link from "next/link";
import { useEffect, useId, useLayoutEffect, useRef, type CSSProperties } from "react";

import { COMPARE, TRAY } from "@/content/compare";
import type { Chosen } from "@/lib/compare/list";
import { paths } from "@/lib/paths";
import { useCompare } from "@/lib/session/session";

import { pictureOf } from "../kit/drawings";
import { picturesOf } from "../kit/Press/kinds";
import press from "../kit/Press/Press.module.css";
import { keepClearOf } from "./clear";
import styles from "./CompareTray.module.css";
import { useHandOver } from "./drawnFrom";
import { BAR_SAYS } from "./look";
import type { TownOf } from "./town";

interface Props {
  /** The area, as the API names it. */
  readonly area: Chosen;
  readonly className?: string;
  /**
   * True where the button stands beside the name of its area, as it does in the heading of
   * a result and in the card of the map: what stands beside it is then said in short.
   */
  readonly small?: boolean;
  /**
   * What the town of the area is drawn from, where whatever draws the button holds it: the
   * bar then draws the town of the area beside its name. Left out, the bar draws the town
   * from what a list of results handed over, and draws none of an area it knows nothing of.
   */
  readonly town?: TownOf | undefined;
  /**
   * True where the button says beside itself what comparing is, until its area is chosen:
   * on the page of an area, which stands under no line that says so.
   */
  readonly invites?: boolean;
}

/**
 * Puts an area among those to compare, or takes it out. It says "Add to compare", and once
 * its area is chosen "Added to compare", in amber: so whether the area is chosen is said in
 * words, and never by colour alone. A press then takes the area out again, which its name
 * says to whoever hears the page. When four are chosen it can add no more, and says why
 * where it stands: the bar says so too, but the bar may be a long way off.
 *
 * It is as wide chosen as not: it keeps the room of the longer of its two lines from the
 * start, so that nothing beside it moves when it is pressed. Nor does what holds it grow
 * under the press.
 *
 * Beside the name of an area, as on a result and in the card of the map, nothing is said
 * beside it. What to do next is said by the bar of areas, which comes to the foot of the
 * screen with the press and is where the areas are gathered: said under the button, it
 * took the room of what stood beside it, and the head of a result on a phone was pressed
 * out of shape. A button that can add no more is switched off there, and is described by
 * what the bar says, which is why.
 *
 * On the page of an area it says beside itself what comparing is, then what to do next,
 * and why it can add no more. Each stands in one place, which keeps the room of the
 * longest of them from the start: so nothing under the press moves.
 *
 * Once there are areas enough the button of each leads to the comparison: the way on is
 * beside what was just pressed, and is the next stop of the keyboard after it. What lays
 * the button out says where the way on is drawn: where it has no room for it, it is drawn
 * while it has the focus, and the bar has the way on in sight.
 *
 * The bar comes at the foot of the window with the press that chooses an area, and may
 * come over the button that was pressed. That button is then brought clear of it, with
 * what stands beside it on its line: it holds the focus, and says what the press did. No
 * other button of the page is moved for it, and nothing is moved by a press that takes an
 * area out.
 *
 * It is drawn as the part Press of the kit draws a button, by the style sheet and the
 * pictures of that part. It is a part of its own because a button of the kit that is amber
 * says that it is pressed, and this one says in its words that its area is chosen: a
 * button that said both would say it twice.
 */
export function CompareButton({ area, className, small = false, town, invites = false }: Props) {
  const id = useId();
  const { chosen: all, has, full, enough, toggle } = useCompare();
  const hand = useHandOver();
  const chosen = has(area.area_id);
  const off = !chosen && full;
  // The way to the comparison, once this area is one of enough.
  const leads = chosen && enough;
  const { up, down } = picturesOf("plain", chosen);
  const drawn = { "--art": `url("${pictureOf(up)}")`, "--art-down": `url("${pictureOf(down)}")` } as CSSProperties;

  const button = useRef<HTMLButtonElement>(null);
  // True from the press that chooses the area until the page is laid out with the bar as it then stands.
  const choosing = useRef(false);
  useLayoutEffect(() => {
    if (!choosing.current) return;
    choosing.current = false;
    if (!chosen) return;
    // The bar is found by what it says, which is on the page before an area is chosen.
    return keepClearOf(() => document.getElementById(BAR_SAYS)?.closest("section") ?? null, button.current);
  }, [chosen]);

  // What the town of this area is drawn from is handed over once the button is on the page,
  // so that the bar has it whenever the area is chosen: here, or from the bar of another page.
  const { area_id: areaId } = area;
  useEffect(() => {
    if (town !== undefined) hand({ release: town.release, marks: { [areaId]: town.marks } });
  }, [hand, town, areaId]);

  const way = (
    // Which page a person reads next is told to no server ahead of time.
    <Link
      className={`${styles.near} ${small ? "target-min" : "target"}`}
      href={paths.compare(all.map((one) => one.slug))}
      prefetch={false}
    >
      {TRAY.go(all.length)}
    </Link>
  );

  return (
    <span className={styles.beside} data-chosen={chosen} data-small={small} data-invites={invites}>
      <button
        ref={button}
        type="button"
        className={[press.press, styles.fills, small ? `${styles.small} target-min` : "target", className]
          .filter(Boolean)
          .join(" ")}
        disabled={off}
        aria-describedby={off ? (invites ? `${id}-why` : BAR_SAYS) : undefined}
        // What is seen on it is the start of its name, and then the area: a page holds many of them.
        aria-label={chosen ? COMPARE.removeNamed(area.name) : COMPARE.addNamed(area.name)}
        onClick={() => {
          choosing.current = !chosen;
          toggle(area);
        }}
      >
        <span className={press.face} data-kind={chosen ? "on" : "plain"} style={drawn}>
          {/* A short label. It keeps the room of the longer of its two lines, which is laid out and not drawn. */}
          <span className={press.says} data-reads="false" data-widest={COMPARE.removeShort}>
            {chosen ? COMPARE.removeShort : COMPARE.addShort}
          </span>
        </span>
      </button>
      {invites ? (
        // What is said beside the button, or the way to the comparison: whichever it is, it
        // stands in one place, which keeps the room of what is said before the area is
        // chosen and of what is said after. The style sheet lays both out there, undrawn.
        <span className={styles.under} data-before={COMPARE.inviteHere} data-after={TRAY.one}>
          {off ? (
            <span id={`${id}-why`} className={styles.why}>
              {COMPARE.full}
            </span>
          ) : leads ? (
            way
          ) : (
            <span className={styles.why}>{chosen ? TRAY.one : COMPARE.inviteHere}</span>
          )}
        </span>
      ) : leads ? (
        way
      ) : null}
    </span>
  );
}
