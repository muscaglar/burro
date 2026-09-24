"use client";

import { useId } from "react";

import { CLARIFY, PLACE_KIND } from "@/content/search";
import type { Answer } from "@/lib/api/client";
import type { Clarify, ClarifyOption, PlacesData } from "@/lib/api/schema";

import { PlaceCombobox } from "../PlaceCombobox/PlaceCombobox";
import styles from "./ClarifyQuestion.module.css";

interface Props {
  readonly clarify: Clarify;
  /** Told of the place or the area that was picked: its id, and its name as the API gave it. */
  readonly onPick: (option: Pick<ClarifyOption, "id" | "name">) => void;
  readonly onLeaveOut: () => void;
  readonly search: (text: string, signal: AbortSignal) => Promise<Answer<PlacesData>>;
  /** Which question this is, and of how many, where there is more than one. */
  readonly position?: { readonly at: number; readonly of: number };
}

/**
 * The one question Burro asks: which place was meant. Up to five buttons,
 * each a place the release holds, then a search field, then "Leave it out".
 *
 * It never repeats what was typed. The API does not send it back, and the
 * page does not keep it.
 */
export function ClarifyQuestion({ clarify, onPick, onLeaveOut, search, position }: Props) {
  const id = useId();
  const aboutAnArea = clarify.group === "area_ops";
  const asked = aboutAnArea ? CLARIFY.questionArea : CLARIFY.question;
  // Two questions are told apart by their number, so that each has a name of its own.
  const question =
    position && position.of > 1 ? `${asked} ${CLARIFY.numbered(position.at, position.of)}` : asked;

  return (
    <section className={styles.question} aria-labelledby={`${id}-question`}>
      <h2 id={`${id}-question`} className={styles.title}>
        {question}
      </h2>
      {clarify.options.length > 0 ? (
        <ul className={styles.options}>
          {clarify.options.map((option) => (
            <li key={option.id}>
              <button type="button" className={`${styles.option} target`} onClick={() => onPick(option)}>
                <span className={styles.name}>{option.name}</span>
                <span className={styles.kind}>{PLACE_KIND[option.kind]}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : aboutAnArea ? null : (
        <p className={styles.none}>{CLARIFY.none}</p>
      )}
      {aboutAnArea ? null : (
        <PlaceCombobox
          search={search}
          label={CLARIFY.search}
          onPick={(place) => onPick({ id: place.place_id, name: place.name })}
        />
      )}
      <div>
        <button type="button" className="target" onClick={onLeaveOut}>
          {CLARIFY.leaveOut}
        </button>
      </div>
    </section>
  );
}
