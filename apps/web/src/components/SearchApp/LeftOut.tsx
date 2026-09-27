"use client";

import { useState, type ReactNode } from "react";

import { ruleIn } from "@/content/crime";
import { LEFT_OUT, NOTICE } from "@/content/search";
import type { MetaData } from "@/lib/api/schema";
import type { LeftThing } from "@/lib/search/said";

import { Art } from "../kit/Art/Art";
import styles from "./LeftOut.module.css";

interface Props {
  /** What Burro noticed and left out of the search, each thing once, in the order it was noticed. */
  readonly things: readonly LeftThing[];
  /** True where something was read and a stretch of the words was not: the ranking leaves that stretch out. */
  readonly words: boolean;
  /** What the service says of every vibe and measure, by which the account of recorded crime is said of this release. */
  readonly meta: Pick<MetaData, "tags" | "features">;
  /**
   * True where it stands open until a person closes it: where nothing is ranked there is
   * no answer for it to give way to, and why is what a person came to read.
   */
  readonly startsOpen?: boolean;
  /** The way to see the words that were not read, which stands under what is said of them. */
  readonly children?: ReactNode;
  /**
   * What the way to the words did, once it was pressed. It stands beside the way, and is
   * heard because the notice says of itself what changes in it: it is no line that says so too.
   */
  readonly did?: string;
}

/** Why a thing was left out, in the words the page has for its kind, or in the service's own. */
function whyOf(thing: LeftThing, meta: Props["meta"]): string {
  switch (thing.why) {
    case "crime":
      return ruleIn(meta);
    case "no_way":
      return thing.says;
    default:
      return LEFT_OUT.why[thing.why];
  }
}

/**
 * What Burro left out of a search, in one line under what it says of the search: each
 * thing it noticed and did not take, by the name the service gives it, and that some of
 * the words were not read. Why is one press away, in the browser's own element.
 *
 * Burro asks nothing: what it noticed in a sentence it takes of itself. A few things it
 * never takes for a person, and says so here. What counts recorded crime, unless the
 * person asked for it by name. What counts who lived somewhere, which counts only where a
 * person chooses it. Whatever else the service says waits for a person: a measure that
 * waits by a decision, and a wish or a journey that may be somebody else's, each with
 * the reason that is its own. A journey to a
 * place it does not know. What the service gave no way to take. A rule for an area, which
 * leaves areas out, and a thing that runs two ways, where the words give no way of it.
 * And what is read into words that were taken another way. Nothing here is offered and
 * nothing can be added from here: each account says where the thing is added.
 *
 * It is one line, and stands in no box: it is in the box of the search, which is a box
 * already. Drawn in full these stood over the answer, and measured at 1440 by 900 after a
 * sentence of a dozen things the first result began at 909 of 900, out of sight. As a box
 * of one line that ran to two and three on a phone, it was 60 px and 88 there, and the
 * first result ended under the first screen. What the line has no room for is cut at its
 * end, and is said whole to whoever hears the page and to whoever opens it: under the
 * line, each thing by its name. The line is of one size open and closed, since it is what
 * takes the press. Where nothing is ranked the line stands open.
 *
 * It is a note, and a band of amber marks it as one, from its head to its foot.
 *
 * It is of one reading. The page draws it anew as the next begins, so it is closed at
 * every new search, whatever a person did with the one before.
 */
export function LeftOut({ things, words, meta, startsOpen = false, children, did = "" }: Props) {
  // What a person opened stays open, and what they closed stays closed, when the line is
  // drawn again with more in it. Until they press it, it stands as the page has it stand.
  const [chosen, setChosen] = useState<boolean | null>(null);
  const open = chosen ?? startsOpen;
  if (things.length === 0 && !words) return null;
  const names = [...things.map((thing) => thing.name), ...(words ? [LEFT_OUT.words] : [])];
  return (
    <div className={styles.left} role="status" aria-label={LEFT_OUT.title}>
      <details
        className={styles.opens}
        open={open}
        // The browser says so too when the page itself opens or closes the line: only what
        // a person did is kept.
        onToggle={(event) => {
          if (event.currentTarget.open !== open) setChosen(event.currentTarget.open);
        }}
      >
        <summary className="target-min">
          <span className={styles.mark}>
            <Art name="ui-arrow" alt="" />
          </span>
          <span className={styles.names} data-names="">
            <span className={styles.title}>{LEFT_OUT.title}</span>
            {LEFT_OUT.named(names)}
          </span>
        </summary>
        <div className={styles.why}>
          <ul className={styles.things}>
            {things.map((thing) => (
              <li key={thing.key}>
                <strong>{thing.name}</strong>
                {". "}
                {whyOf(thing, meta)}
              </li>
            ))}
            {words ? (
              <li>
                <strong>{LEFT_OUT.words}</strong>
                {". "}
                {NOTICE.partUnread}
                {children === undefined || children === null ? null : (
                  <div className={styles.way}>
                    {children}
                    {did === "" ? null : <p>{did}</p>}
                  </div>
                )}
              </li>
            ) : null}
          </ul>
        </div>
      </details>
    </div>
  );
}
