"use client";

import { useRef, type KeyboardEvent } from "react";

import styles from "./Tabs.module.css";

export interface Tab<Id extends string> {
  readonly id: Id;
  readonly label: string;
  /** The id of the panel the tab shows. */
  readonly panel: string;
}

interface Props<Id extends string> {
  /** What the tabs choose between. */
  readonly label: string;
  readonly tabs: readonly Tab<Id>[];
  readonly selected: Id;
  readonly onSelect: (id: Id) => void;
  readonly className?: string;
}

/**
 * A row of tabs. One is chosen at a time. Every tab can be reached with Tab,
 * and the arrow keys, Home and End move between them as well. The panels are
 * the page's own: a tab names the one it shows.
 */
export function Tabs<Id extends string>({ label, tabs, selected, onSelect, className }: Props<Id>) {
  const list = useRef<HTMLDivElement>(null);

  const move = (to: number) => {
    const tab = tabs[(to + tabs.length) % tabs.length];
    if (!tab) return;
    onSelect(tab.id);
    list.current?.querySelector<HTMLElement>(`[data-tab="${tab.id}"]`)?.focus();
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const at = tabs.findIndex((tab) => tab.id === selected);
    const to = { ArrowRight: at + 1, ArrowLeft: at - 1, Home: 0, End: tabs.length - 1 }[event.key];
    if (to === undefined) return;
    event.preventDefault();
    move(to);
  };

  return (
    <div
      ref={list}
      role="tablist"
      aria-label={label}
      className={[styles.tabs, className].filter(Boolean).join(" ")}
    >
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          data-tab={tab.id}
          className={`${styles.tab} target`}
          aria-selected={tab.id === selected}
          aria-controls={tab.panel}
          onClick={() => onSelect(tab.id)}
          onKeyDown={onKeyDown}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
