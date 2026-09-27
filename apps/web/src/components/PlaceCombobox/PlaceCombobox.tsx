"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";

import { FIND_AREA, PLACE, PLACE_KIND } from "@/content/search";
import type { Answer } from "@/lib/api/client";
import type { AreaSummary, FoundPlace, PlacesData } from "@/lib/api/schema";
import { paths } from "@/lib/paths";
import { PLACE_QUERY } from "@/lib/search/flow";

import { BesideName } from "../BesideName/BesideName";
import { pictureOf, sizeOf } from "../kit/drawings";
import styles from "./PlaceCombobox.module.css";

/**
 * The carrot that lies beside the place in hand, as the style sheet needs it: where it is
 * served from, and its size in art pixels. It is the pointer of every menu of the look.
 */
const CARROT = {
  "--carrot": `url("${pictureOf("ui-carrot")}")`,
  "--carrot-w": sizeOf("ui-carrot").width,
  "--carrot-h": sizeOf("ui-carrot").height,
} as CSSProperties;

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
  /**
   * True where the data names no place at all. The field is then not drawn: nothing typed
   * in it could match, and it once said "Try another spelling" of every spelling there is.
   * Where the box finds areas too it is drawn all the same, and finds areas alone.
   */
  readonly noPlaces?: boolean;
  /**
   * True where the box finds an area by its name too. Every area that bears the name is
   * listed under the field, each as a link to its page. An area is no place to reach, so it
   * is no option of the list and is never handed to `onPick`.
   */
  readonly areas?: boolean;
  /**
   * False where the field stands directly under a button that says what it is, in the same
   * words, as it does once such a button has opened it. Its label is then kept for whoever
   * hears the page, since it is what names the field, and is not drawn a second time.
   */
  readonly labelDrawn?: boolean;
}

/**
 * Search as you type for a place to reach. It follows the combobox pattern:
 * the focus stays in the field, the arrow keys move through the options,
 * Enter picks one and Escape closes the list.
 *
 * Where it finds areas alone it is a plain field, and says nothing of a list:
 * an area is a link under the field, and no option of one. Said to be a
 * combobox there, it promised a list that was hidden and empty whatever was
 * typed.
 *
 * What is typed is held by the field and by nothing else. The field has no
 * name and asks the browser not to keep it. An option is known by its place
 * in the list, so no id of a place is written into the page's markup.
 *
 * The list is a menu, as the look draws one: the place the keys are on is in
 * ink with its words in page, and the carrot lies beside it. It says that it
 * is the one in hand to a screen reader too.
 */
export function PlaceCombobox({
  search,
  onPick,
  label,
  hint,
  full = null,
  noPlaces = false,
  areas = false,
  labelDrawn = true,
}: Props) {
  const id = useId();
  const named = label ?? (areas ? (noPlaces ? FIND_AREA.labelAlone : FIND_AREA.label) : PLACE.label);
  const hinted = hint ?? (areas ? (noPlaces ? FIND_AREA.hintAlone : FIND_AREA.hint) : PLACE.hint);
  // It finds areas alone: it offers no place, so it has no list to open.
  const alone = noPlaces && areas;
  const field = useRef<HTMLInputElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlight = useRef<AbortController | null>(null);
  const [options, setOptions] = useState<readonly FoundPlace[]>([]);
  const [found, setFound] = useState<readonly AreaSummary[]>([]);
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

  // The focus stays in the field, so a browser brings no place of the list into sight by
  // itself. Once the list is drawn the place in hand is brought into sight in it, by no more
  // than it must be, and a list with none in hand, as one is when an answer comes, is read
  // from its top. The list alone is moved, and never the page under it: asked to bring a
  // place into sight, a browser moves the page as well.
  useEffect(() => {
    const box = list.current;
    if (!open || box === null) return;
    const one = active < 0 ? null : document.getElementById(`${id}-option-${active}`);
    if (one === null) {
      box.scrollTop = 0;
      return;
    }
    const foot = one.offsetTop + one.offsetHeight;
    if (one.offsetTop < box.scrollTop) box.scrollTop = one.offsetTop;
    else if (foot > box.scrollTop + box.clientHeight) box.scrollTop = foot - box.clientHeight;
  }, [open, active, options, id]);

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
      setFound([]);
      setStatus("failed");
      close();
      return;
    }
    // A place is offered only where the data names places, and an area only where the box
    // finds areas.
    const places = noPlaces ? [] : answer.data.places;
    const bearing = areas ? answer.data.areas : [];
    setOptions(places);
    setFound(bearing);
    setStatus(places.length + bearing.length > 0 ? "found" : "none");
    setOpen(places.length > 0);
    setActive(-1);
  };

  const onInput = () => {
    halt();
    const text = (field.current?.value ?? "").trim();
    if (text.length < PLACE_QUERY.least) {
      setOptions([]);
      setFound([]);
      setStatus("idle");
      close();
      return;
    }
    timer.current = setTimeout(() => {
      timer.current = null;
      void look(text);
    }, WAIT_MS);
  };

  /** Looks again for what the field holds, at once: nothing more was typed to wait for. */
  const again = () => {
    const text = (field.current?.value ?? "").trim();
    if (text.length < PLACE_QUERY.least) return;
    halt();
    void look(text);
  };

  const pick = (place: FoundPlace | undefined) => {
    if (!place) return;
    halt();
    if (field.current) field.current.value = "";
    setOptions([]);
    setFound([]);
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
        // Enter never sends a form from here: it picks, or it looks again where the last
        // search failed, which is what the line under the field asks a person to do.
        event.preventDefault();
        if (open && active >= 0) pick(options[active]);
        else if (status === "failed") again();
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

  const nothing = areas ? (noPlaces ? FIND_AREA.noneAlone : FIND_AREA.none) : PLACE.none;
  const said =
    status === "searching"
      ? PLACE.searching
      : status === "found"
        ? areas
          ? FIND_AREA.found(options.length, found.length)
          : PLACE.found(options.length)
        : status === "none"
          ? nothing
          : status === "failed"
            ? PLACE.failed
            : "";

  if (noPlaces && !areas) {
    return (
      <div className={styles.combobox}>
        <p className={styles.label}>{named}</p>
        <p className={styles.hint}>{PLACE.notInData}</p>
      </div>
    );
  }
  if (full !== null) {
    return (
      <p className={styles.full} role="status">
        {full}
      </p>
    );
  }

  return (
    <div className={styles.combobox}>
      <label className={labelDrawn ? styles.label : "visually-hidden"} htmlFor={`${id}-field`}>
        {named}
      </label>
      <p id={`${id}-hint`} className={styles.hint}>
        {hinted}
      </p>
      <input
        ref={field}
        id={`${id}-field`}
        className={`${styles.field} target`}
        type="text"
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck={false}
        maxLength={PLACE_QUERY.most}
        {...(alone
          ? {}
          : {
              role: "combobox",
              "aria-expanded": open,
              "aria-controls": `${id}-list`,
              "aria-autocomplete": "list",
              "aria-activedescendant": open && active >= 0 ? `${id}-option-${active}` : undefined,
            })}
        aria-describedby={`${id}-hint`}
        onInput={onInput}
        onKeyDown={onKeyDown}
        onBlur={close}
      />
      {/* The areas that bear the name, each a link to its page. They stand in the flow of the
          page, over the list of places, which is laid over what is under it: so neither
          hides the other. Which page a person reads next is told to no server ahead of time. */}
      {found.length > 0 ? (
        <div className={styles.areas} role="group" aria-labelledby={`${id}-areas`}>
          <p id={`${id}-areas`} className={styles.areasTitle}>
            {FIND_AREA.title}
          </p>
          <ul className={styles.areasList}>
            {found.map((area) => (
              <li key={area.area_id}>
                <Link className="target-min" href={paths.area(area)} prefetch={false}>
                  {area.name}
                </Link>
                <BesideName area={area} className={styles.kind} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {alone ? null : (
        <ul
          ref={list}
          id={`${id}-list`}
          className={styles.list}
          style={CARROT}
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
      )}
      <p className={styles.status} role="status">
        {said}
      </p>
    </div>
  );
}
