"use client";

import { useRef, type KeyboardEvent } from "react";

import styles from "./Ways.module.css";

/** One way in: what its tab says. */
export interface Way<Id extends string = string> {
  readonly id: Id;
  /** What its tab says. It names the panel the tab shows. */
  readonly label: string;
}

interface Props<Id extends string> {
  /** What the tabs are, to whoever hears the page. */
  readonly label: string;
  /** What the id of every tab and of every panel begins with, so that each can name the other. */
  readonly name: string;
  /** The ways, in the order their tabs stand in. */
  readonly ways: readonly Way<Id>[];
  /** The one that is chosen. There is always one. */
  readonly chosen: Id;
  /** Told which way was chosen, by a press or by a key. It is not told of the one that is chosen already. */
  readonly onChoose: (id: Id) => void;
}

/** The id of the tab of a way, which its panel is named by. */
export const tabIdOf = (name: string, id: string): string => `${name}-${id}-tab`;

/** The id of the panel of a way, which its tab names. */
export const panelIdOf = (name: string, id: string): string => `${name}-${id}`;

/**
 * What the panel of a way says of itself, for whatever element the page draws it as: that
 * it is a panel, which tab names it, and that it is not drawn while another way is chosen.
 * It is on the page all the same, so that what it holds is kept as it was left.
 */
export function panelOf(name: string, id: string, chosen: string) {
  return {
    id: panelIdOf(name, id),
    role: "tabpanel",
    "aria-labelledby": tabIdOf(name, id),
    hidden: id !== chosen,
  } as const;
}

/** The keys that move between the tabs, and where each leads from the tab at `at` of `many`. */
const LEADS: Readonly<Record<string, (at: number, many: number) => number>> = {
  ArrowRight: (at, many) => (at + 1) % many,
  ArrowLeft: (at, many) => (at - 1 + many) % many,
  Home: () => 0,
  End: (_, many) => many - 1,
};

/**
 * The ways into a search, as tabs: one list of them, each a tab that says
 * whether it is chosen and names the panel it shows. The page draws the
 * panels, with `panelOf`, since what stands in one may have to stay where it
 * is once the tabs are gone.
 *
 * The arrow keys move between the tabs and go round at either end, Home and
 * End go to the first and the last, and the tab a key leads to is chosen as
 * it takes the focus: both panels are on the page already, so nothing is
 * waited for. Tab goes from the chosen tab into its panel, because the chosen
 * tab is the only one the keyboard stops at.
 *
 * A tab is drawn as a tab of the look. The chosen one stands forward: it is
 * of the cream of the box under it, bears a band of amber at its head as
 * what is on does, and is laid over the rule of that box, so that the two are
 * one. The other stands back, lower, on sand, and ends where the rule of
 * the box begins. The button is what takes the press, and is of one size
 * whichever is chosen: what changes is its face, inside it.
 *
 * A tab needs a script. With scripts off none is drawn, and the page stands
 * both panels one under the other, each under its name.
 */
export function Ways<Id extends string>({ label, name, ways, chosen, onChoose }: Props<Id>) {
  const tabs = useRef(new Map<Id, HTMLButtonElement>());

  const choose = (id: Id) => {
    if (id !== chosen) onChoose(id);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const leads = LEADS[event.key];
    // A key held with another is the browser's own, as Alt and an arrow is.
    if (leads === undefined || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const at = ways.findIndex((way) => way.id === chosen);
    const next = ways[leads(Math.max(at, 0), ways.length)];
    if (next === undefined) return;
    // The page is not scrolled by the key: the tab it leads to is in sight, beside the one it left.
    event.preventDefault();
    tabs.current.get(next.id)?.focus({ preventScroll: true });
    choose(next.id);
  };

  return (
    // The list itself is no stop of a keyboard and hears no key: the tabs are the controls.
    <div className={styles.ways} role="tablist" aria-label={label}>
      {ways.map((way) => (
        <button
          key={way.id}
          ref={(tab) => {
            if (tab === null) tabs.current.delete(way.id);
            else tabs.current.set(way.id, tab);
          }}
          id={tabIdOf(name, way.id)}
          type="button"
          role="tab"
          className={`${styles.way} target`}
          aria-selected={way.id === chosen}
          aria-controls={panelIdOf(name, way.id)}
          // The keyboard stops at the chosen tab, and the arrow keys lead to the others.
          tabIndex={way.id === chosen ? 0 : -1}
          onKeyDown={onKeyDown}
          onClick={(event) => {
            // Not every browser gives the focus to a button that is pressed, and what had the
            // focus may stand in the panel that this press hides.
            event.currentTarget.focus({ preventScroll: true });
            choose(way.id);
          }}
        >
          <span className={styles.face}>{way.label}</span>
        </button>
      ))}
    </div>
  );
}
