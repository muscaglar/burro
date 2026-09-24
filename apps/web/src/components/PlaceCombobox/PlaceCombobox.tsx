"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";

import { PLACE, PLACE_KIND } from "@/content/search";
import type { Answer } from "@/lib/api/client";
import type { FoundPlace, PlacesData } from "@/lib/api/schema";
import { PLACE_QUERY } from "@/lib/search/flow";

import styles from "./PlaceCombobox.module.css";

/** How long after the last key the search is sent. */
export const WAIT_MS = 250;

type Status = "idle" | "searching" | "found" | "none" | "failed";

interface Props {
  /** Route 8. What is typed goes in the body of the call and nowhere else. */
  readonly search: (text: string, signal: AbortSignal) => Promise<Answer<PlacesData>>;
  readonly onPick: (place: FoundPlace) => void;
  readonly label?: string;
  readonly hint?: string;
  /** Said in place of the field when no more places can be named. */
  readonly full?: string | null;
}

/**
 * Search as you type for a place to reach. It follows the combobox pattern:
 * the focus stays in the field, the arrow keys move through the options,
 * Enter picks one and Escape closes the list.
 *
 * What is typed is held by the field and by nothing else. The field has no
 * name and asks the browser not to keep it. An option is known by its place
 * in the list, so no id of a place is written into the page's markup.
 */
export function PlaceCombobox({ search, onPick, label = PLACE.label, hint = PLACE.hint, full = null }: Props) {
  const id = useId();
  const field = useRef<HTMLInputElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlight = useRef<AbortController | null>(null);
  const [options, setOptions] = useState<readonly FoundPlace[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);

  const halt = () => {
    if (timer.current !== null) clearTimeout(timer.current);
    timer.current = null;
    inFlight.current?.abort();
    inFlight.current = null;
  };

  useEffect(() => halt, []);

  const close = () => {
    setOpen(false);
    setActive(-1);
  };

  const look = async (text: string) => {
    const controller = new AbortController();
    inFlight.current = controller;
    setStatus("searching");
    const answer = await search(text, controller.signal);
    // An answer to what was typed before the last key is dropped.
    if (inFlight.current !== controller) return;
    inFlight.current = null;
    if (!answer.ok) {
      setOptions([]);
      setStatus("failed");
      close();
      return;
    }
    setOptions(answer.data.places);
    setStatus(answer.data.places.length > 0 ? "found" : "none");
    setOpen(answer.data.places.length > 0);
    setActive(-1);
  };

  const onInput = () => {
    halt();
    const text = (field.current?.value ?? "").trim();
    if (text.length < PLACE_QUERY.least) {
      setOptions([]);
      setStatus("idle");
      close();
      return;
    }
    timer.current = setTimeout(() => {
      timer.current = null;
      void look(text);
    }, WAIT_MS);
  };

  const pick = (place: FoundPlace | undefined) => {
    if (!place) return;
    halt();
    if (field.current) field.current.value = "";
    setOptions([]);
    setStatus("idle");
    close();
    onPick(place);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.nativeEvent.isComposing) return;
    const last = options.length - 1;
    switch (event.key) {
      case "ArrowDown":
        if (options.length === 0) return;
        event.preventDefault();
        setOpen(true);
        setActive(active >= last ? 0 : active + 1);
        return;
      case "ArrowUp":
        if (options.length === 0) return;
        event.preventDefault();
        setOpen(true);
        setActive(active <= 0 ? last : active - 1);
        return;
      case "Home":
      case "End":
        if (!open) return;
        event.preventDefault();
        setActive(event.key === "Home" ? 0 : last);
        return;
      case "Enter":
        // Enter never sends a form from here: it picks, or it does nothing.
        event.preventDefault();
        if (open && active >= 0) pick(options[active]);
        return;
      case "Escape":
        if (!open) return;
        event.preventDefault();
        event.stopPropagation();
        close();
        return;
      default:
    }
  };

  const said =
    status === "searching"
      ? PLACE.searching
      : status === "found"
        ? PLACE.found(options.length)
        : status === "none"
          ? PLACE.none
          : status === "failed"
            ? PLACE.failed
            : "";

  if (full !== null) {
    return (
      <p className={styles.full} role="status">
        {full}
      </p>
    );
  }

  return (
    <div className={styles.combobox}>
      <label className={styles.label} htmlFor={`${id}-field`}>
        {label}
      </label>
      <p id={`${id}-hint`} className={styles.hint}>
        {hint}
      </p>
      <input
        ref={field}
        id={`${id}-field`}
        className={`${styles.field} target`}
        type="text"
        role="combobox"
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck={false}
        maxLength={PLACE_QUERY.most}
        aria-expanded={open}
        aria-controls={`${id}-list`}
        aria-autocomplete="list"
        aria-activedescendant={open && active >= 0 ? `${id}-option-${active}` : undefined}
        aria-describedby={`${id}-hint`}
        onInput={onInput}
        onKeyDown={onKeyDown}
        onBlur={close}
      />
      <ul
        id={`${id}-list`}
        className={styles.list}
        role="listbox"
        aria-label={PLACE.options}
        hidden={!open}
      >
        {options.map((place, at) => (
          // The keys are heard by the field, where the focus stays: the arrows move, Enter picks.
          // eslint-disable-next-line jsx-a11y/click-events-have-key-events
          <li
            key={place.place_id}
            id={`${id}-option-${at}`}
            className={`${styles.option} target`}
            role="option"
            aria-selected={at === active}
            // The focus stays in the field, so pressing an option must not take it.
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => pick(place)}
          >
            <span className={styles.name}>{place.name}</span>
            <span className={styles.kind}>
              {PLACE_KIND[place.kind]}
              {place.coarse_name !== place.name ? `, ${PLACE.within} ${place.coarse_name}` : null}
            </span>
          </li>
        ))}
      </ul>
      <p className={styles.status} role="status">
        {said}
      </p>
    </div>
  );
}
