"use client";

import { useId, useRef, useState, type MouseEvent } from "react";

import { SUGGEST } from "@/content/search";
import type { Answer } from "@/lib/api/client";
import type { FoundPlace, PlacesData, Span, Suggestion, SuggestionChoice } from "@/lib/api/schema";
import type { Added } from "@/lib/search/state";
import { SKIP, addedWithOthers, keyOf, noteOf } from "@/lib/search/suggestion";

import { PlaceCombobox } from "../PlaceCombobox/PlaceCombobox";
import styles from "./Suggestions.module.css";

/**
 * How many offers are shown before "Show all" is pressed. Every offer beyond them that one
 * press may add is shown as well: see `inSight`.
 */
export const SHOWN_AT_FIRST = 4;

/**
 * Where in the list the offers stand that are drawn before "Show all" is pressed: the
 * first four, and every other that one press may add. So what waits out of sight is only
 * what is the person's to choose, and the one button adds nothing that is not in sight.
 */
export function inSight(suggestions: readonly Suggestion[]): readonly number[] {
  return suggestions.flatMap((suggestion, at) =>
    at < SHOWN_AT_FIRST || addedWithOthers(suggestion) !== null ? [at] : [],
  );
}

interface Props {
  /** What Burro read and did not apply, in the order the things stand in the text. */
  readonly suggestions: readonly Suggestion[];
  /**
   * Takes one choice of the offer at that place in the list, by the id of the choice. A
   * journey to a place the release does not hold comes with the place the person chose.
   */
  readonly onChoose: (at: number, id: string, placeId?: string) => void;
  /**
   * Takes, of each of these offers, the way one press may add, all at once. Left out, no
   * button offers to, and each thing is added by its own.
   */
  readonly onChooseAll?: (ats: readonly number[]) => void;
  /** What the last such press added, until it is taken back. */
  readonly added?: Added | null;
  /** Takes back all that the last such press added. */
  readonly onTakeBack?: () => void;
  /** True while a model reads what the rules left unread. */
  readonly reading?: boolean;
  /**
   * Selects stretches of the text in the box, where the box still holds what was sent.
   * Left out, the page cannot show where the words stand, and no button offers to.
   */
  readonly onShow?: (spans: readonly Span[]) => void;
  /**
   * The person's own words of one stretch, cut from the box as it stands, or `null` where
   * the box no longer holds them. They are drawn and kept nowhere. Left out, none is drawn.
   */
  readonly wrote?: (span: Span) => string | null;
  /** Route 8, for a journey whose place Burro does not know. Left out, no place can be chosen. */
  readonly searchPlaces?: (text: string, signal: AbortSignal) => Promise<Answer<PlacesData>>;
}

/**
 * The button to give the focus to when an offer goes: the first of the one after it, or
 * else of the one before, or else the block itself. The button that was pressed goes with
 * its offer, and the focus must not go with it.
 */
function besideOf(item: HTMLElement | null): HTMLElement | null {
  const all = [...(item?.parentElement?.children ?? [])];
  const at = item === null ? -1 : all.indexOf(item);
  if (at < 0) return null;
  for (const other of [...all.slice(at + 1), ...all.slice(0, at).reverse()]) {
    const button = other.querySelector<HTMLElement>("button");
    if (button) return button;
  }
  return item?.closest<HTMLElement>("section") ?? null;
}

/**
 * What a choice is called to whoever cannot see what it stands under: its own words, the
 * mark of the guess, and the thing it is of where its words do not name it. `undefined`
 * where its own words say it all.
 */
function nameOf(choice: SuggestionChoice, suggestion: Suggestion): string | undefined {
  const names = choice.label.toLowerCase().includes(suggestion.label.toLowerCase());
  if (names && !choice.guess) return undefined;
  const words = choice.guess ? `${choice.label} (${SUGGEST.guess})` : choice.label;
  return names ? words : SUGGEST.named(words, suggestion.label);
}

/**
 * What Burro read in a prompt and did not apply. Nothing is added until it is pressed.
 *
 * Each offer is drawn in four parts, in this order: what it would do, the person's own
 * words, what follows for areas, and the choices. Where Burro reads a thing one way, that
 * way is marked as its guess, and the mark applies nothing. Doing nothing is "Skip".
 *
 * What an offer would do, what follows and the words of each choice are the API's. The
 * person's words are cut from the box by where they stand, while the box holds what was
 * sent, and are kept nowhere.
 *
 * One button adds every offer in sight that the API says one press may add. It says what
 * it added and what is left for the person, and one press takes it all back.
 */
export function Suggestions({
  suggestions,
  onChoose,
  onChooseAll,
  added = null,
  onTakeBack,
  reading = false,
  onShow,
  wrote,
  searchPlaces,
}: Props) {
  const id = useId();
  const block = useRef<HTMLElement>(null);
  const [all, setAll] = useState(false);
  // The offer a place is being chosen for, and the way of it that was pressed.
  const [placing, setPlacing] = useState<{ readonly key: string; readonly id: string } | null>(null);
  if (suggestions.length === 0 && added === null && !reading) return null;
  // Each offer that is drawn, with where it stands among them all: a choice names its offer
  // by its place in the whole list.
  const shown = (all ? suggestions.map((_, at) => at) : inSight(suggestions)).flatMap((at) => {
    const suggestion = suggestions[at];
    return suggestion === undefined ? [] : [{ suggestion, at }];
  });
  const more = suggestions.length - shown.length;
  // The offers in sight that one press may add. What is out of sight is never added.
  const together = shown.flatMap(({ suggestion, at }) => (addedWithOthers(suggestion) === null ? [] : [at]));
  const every = together.length === shown.length;

  const choose = (event: MouseEvent<HTMLButtonElement>, at: number, suggestion: Suggestion, way: string) => {
    // A journey whose place Burro does not know asks which place before it is added.
    if (suggestion.asks_place && way !== SKIP) {
      setPlacing({ key: keyOf(suggestion), id: way });
      return;
    }
    (besideOf(event.currentTarget.closest("li")) ?? block.current)?.focus();
    onChoose(at, way);
  };

  const place = (at: number, way: string, found: Pick<FoundPlace, "place_id">) => {
    setPlacing(null);
    block.current?.focus();
    onChoose(at, way, found.place_id);
  };

  // A note that neighbours share word for word is drawn once, with the first of them, and said
  // of each. "Safe" brings two offers of recorded crime under one note of three lines.
  const notes = shown.map(({ suggestion }, row) => {
    const note = noteOf(suggestion);
    if (note === null) return null;
    let first = row;
    while (first > 0 && noteOf(shown[first - 1]?.suggestion ?? {}) === note) first -= 1;
    return { words: note, id: `${id}-note-${first}`, drawn: first === row };
  });

  const chooseAll = () => {
    // The button goes with what it added. The focus goes to the block, or to what holds it.
    block.current?.focus();
    onChooseAll?.(together);
  };

  return (
    // It can be given the focus when its last offer goes, and is no stop of its own.
    <section ref={block} className={styles.suggestions} aria-labelledby={`${id}-title`} tabIndex={-1}>
      <h2 id={`${id}-title`} className={styles.title}>
        {SUGGEST.title}
      </h2>
      <p className={styles.why}>{SUGGEST.why}</p>
      {/* It is on the page before it says anything, so that a screen reader is told when it does. */}
      <p className={styles.state} role="status">
        {reading ? SUGGEST.reading : added !== null ? SUGGEST.added(added.count, added.needs) : ""}
      </p>
      {added !== null && onTakeBack ? (
        <button type="button" className={`${styles.back} target`} onClick={onTakeBack}>
          {SUGGEST.takeBack}
        </button>
      ) : null}
      {onChooseAll && together.length > 1 ? (
        <button type="button" className={`${styles.every} target`} onClick={chooseAll}>
          {every ? SUGGEST.addAll(together.length) : SUGGEST.addThese(together.length)}
        </button>
      ) : null}
      <ul className={styles.list}>
        {shown.map(({ suggestion, at }, row) => {
          const words = wrote?.(suggestion.shown) ?? null;
          const asking = placing !== null && placing.key === keyOf(suggestion) ? placing : null;
          return (
            // An offer is known by its thing and where its words begin: the API gives no id.
            <li key={keyOf(suggestion)} className={styles.item}>
              <p id={`${id}-does-${row}`} className={styles.does}>
                {suggestion.does}
              </p>
              {words === null ? null : (
                <p className={styles.wrote}>
                  <span className={styles.lead}>{SUGGEST.wrote}</span> <q>{words}</q>
                </p>
              )}
              {suggestion.follows === "" ? null : <p className={styles.follows}>{suggestion.follows}</p>}
              {suggestion.said.map((line) => (
                <p key={line} className={styles.follows}>
                  {line}
                </p>
              ))}
              {notes[row]?.drawn ? (
                <p id={notes[row].id} className={styles.note}>
                  {notes[row].words}
                </p>
              ) : null}
              <span
                className={styles.choices}
                role="group"
                aria-labelledby={`${id}-does-${row}`}
                aria-describedby={notes[row]?.id}
              >
                {suggestion.choices.map((choice) => (
                  <button
                    key={choice.id}
                    type="button"
                    className={`${styles.choice} target`}
                    data-way={choice.id}
                    data-guess={choice.guess ? "" : undefined}
                    aria-pressed={asking?.id === choice.id ? true : undefined}
                    // "Add" and "Skip" are said of many offers, so each says what it is of.
                    aria-label={nameOf(choice, suggestion)}
                    onClick={(event) => choose(event, at, suggestion, choice.id)}
                  >
                    {choice.label}
                    {/* The style sheet puts the mark in brackets, so the space stands before them. */}
                    {choice.guess ? (
                      <>
                        {" "}
                        <span className={styles.guess}>{SUGGEST.guess}</span>
                      </>
                    ) : null}
                  </button>
                ))}
                {onShow && suggestion.spans.length > 0 ? (
                  <button
                    type="button"
                    className={`${styles.show} target-min`}
                    aria-label={SUGGEST.showWordsOf(suggestion.label)}
                    onClick={() => onShow(suggestion.spans)}
                  >
                    {SUGGEST.showWords}
                  </button>
                ) : null}
              </span>
              {asking !== null ? (
                <div className={styles.place}>
                  {suggestion.options.length > 0 ? (
                    <span className={styles.choices} role="group" aria-label={SUGGEST.alike}>
                      {suggestion.options.map((option) => (
                        <button
                          key={option.name}
                          type="button"
                          className={`${styles.choice} target`}
                          onClick={() => place(at, asking.id, { place_id: option.id })}
                        >
                          {option.name}
                        </button>
                      ))}
                    </span>
                  ) : null}
                  {searchPlaces ? (
                    <PlaceCombobox
                      search={searchPlaces}
                      onPick={(found) => place(at, asking.id, found)}
                      label={SUGGEST.whichPlace}
                    />
                  ) : null}
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
      {more > 0 ? (
        <button type="button" className={`${styles.all} target`} onClick={() => setAll(true)}>
          {SUGGEST.showAll(suggestions.length)}
        </button>
      ) : null}
    </section>
  );
}
