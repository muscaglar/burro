"use client";

import { useId, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import { askingFor, CRIME_ACCOUNT, countsOf } from "@/content/crime";
import { LEGEND } from "@/content/map";
import { SHELF } from "@/content/search";
import type {
  BandMark,
  GeometryData,
  Metric,
  Operations,
  RecipeHeld,
  Tag,
  TagId,
  VibeBands,
} from "@/lib/api/schema";
import { BANDS } from "@/lib/map/fill";
import { edits } from "@/lib/search/edits";
import type { Opens } from "@/lib/sight";
import { endsOf, readingOf } from "@/lib/vibes";

import { Folded } from "../Disclosure/Folded";
import { Summary, theArrow } from "../Disclosure/Summary";
import { headedUnder, useHelper } from "../Helpers/Helpers";
import { useWhereItOpens } from "../Helpers/where";
import { Art } from "../kit/Art/Art";
import { pictureOfEnd } from "../kit/Ends/picture";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
import { Thing } from "../kit/Thing/Thing";
import { outlinesOf, type Outline } from "../LocatorMap/LocatorMap";
import { VIBE_MAP_FRAME, VibeMap } from "../VibeMap/VibeMap";
import styles from "./Shelf.module.css";

interface Props {
  /** The vibes of the release, from route 11. Each says its own word and its place on the shelf. */
  readonly tags: readonly Tag[];
  /** The features of the release, which name the parts of a recipe. */
  readonly features: readonly Metric[];
  /**
   * What the release holds of each recipe, from route 11: whether any area has a band for
   * the vibe, how much of its recipe is held, and what it waits on. A vibe that no area can
   * be placed on stands apart, and cannot be added to a search: added, it left no area ranked.
   */
  readonly recipes?: readonly RecipeHeld[];
  /** The vibe whose card is open. The map is coloured by it, where it may be. */
  readonly open: TagId | null;
  readonly onOpen: (tagId: TagId | null) => void;
  /** Adds a vibe to the search: one edit, and no text. */
  readonly onAdd: (operations: Operations) => void;
  /** The boundary of every area, once it has come. The card of a word draws the city from it. */
  readonly geometry?: GeometryData | null;
  /**
   * Where every area sits on every vibe that may colour a map. They came with the page, so
   * nobody is told which word a person looks at.
   */
  readonly bands?: readonly VibeBands[];
  /** Where the card of a word stands. Left out, as the look has chosen. */
  readonly opens?: Opens;
}

/** How many words stand on the shelf before "more" is pressed. */
export const ON_THE_SHELF = 7;

/** The vibes in the order the API gives the shelf. One with no place on it comes last. */
export function inShelfOrder(tags: readonly Tag[]): readonly Tag[] {
  return [...tags].sort(
    (one, other) => (one.shelf_order ?? Infinity) - (other.shelf_order ?? Infinity),
  );
}

/**
 * What the card of a vibe draws the city from: the outline of every area, and where each
 * sits on the vibe. `null` where the boundaries have not come, or the vibe may colour no map.
 */
function cityOf(tag: Tag, outlines: readonly Outline[], bands: readonly VibeBands[]): CardProps["city"] {
  const marks = tag.lens ? bands.find((one) => one.tag_id === tag.tag_id)?.marks : undefined;
  return marks === undefined || outlines.length === 0 ? null : { outlines, marks };
}

/** The word a vibe stands on the shelf as: its everyday word, or its name where it has none. */
export const wordOf = (tag: Pick<Tag, "shelf_word" | "short_label">) => tag.shelf_word ?? tag.short_label;

interface CardProps extends Pick<Props, "features" | "onAdd"> {
  /**
   * The level of the heading that names the card: one under the heading of the shelf, or
   * where the shelf has none of its own, the level that one would have had. What is
   * headed inside the card is one level under it.
   */
  readonly level: 2 | 3;
  readonly tag: Tag;
  /** What the release holds of this vibe's recipe. `undefined` where the API said nothing of it. */
  readonly held?: RecipeHeld;
  readonly id: string;
  readonly onClose: () => void;
  /** The outline of every area, and where each sits on this vibe. `null` where either is not in hand. */
  readonly city: { readonly outlines: readonly Outline[]; readonly marks: readonly BandMark[] } | null;
}

/**
 * The city coloured by the vibe, in five bands, with what the bands are. It is drawn in
 * the card on a narrow screen, where the map itself is out of sight below the form: a
 * word that was pressed once coloured a map two screens down. On a wide screen the map
 * is beside the shelf, and this is not drawn.
 */
function City({ tag, city }: { readonly tag: Tag; readonly city: NonNullable<CardProps["city"]> }) {
  const [low, high] = endsOf(tag);
  const last = BANDS.length;
  return (
    <div className={styles.city}>
      <VibeMap outlines={city.outlines} marks={city.marks} title={LEGEND.vibe(tag.label)} />
      <ul className={styles.legend} aria-label={LEGEND.title}>
        {BANDS.map(({ band }) => (
          <li key={band}>
            <span className={styles.swatch} data-band={band} aria-hidden="true" />
            {band === 1 ? LEGEND.vibeEnd(band, low) : band === last ? LEGEND.vibeEnd(band, high) : LEGEND.vibeBand(band)}
          </li>
        ))}
        {city.marks.some((mark) => mark.band === null) ? (
          <li>
            <span className={styles.swatch} data-band="none" aria-hidden="true" />
            {LEGEND.notPlaced}
          </li>
        ) : null}
      </ul>
    </div>
  );
}

/**
 * What one vibe is, before it is asked for: its name, what it means, what it
 * is made of, and what it cannot see. Every word of it is the API's. Under
 * what it means, the button that adds it to the search.
 *
 * What it is made of and what it cannot see are long, and are folded, each in
 * the browser's own element: they are in the page, one press away. Drawn
 * open, they were 600 px of a card 1,170 px high on a phone, which had room
 * neither under its word nor over it.
 *
 * It is the box in hand: its inner rule is amber, as the word that opened it
 * is. A scale has the small picture of each of its ends beside the sentence
 * that names them. The pictures are for the eye, and the sentence is read.
 */
function VibeCard({ level, tag, held, features, id, onAdd, onClose, city }: CardProps) {
  const Name = level === 2 ? "h2" : "h3";
  const Small = level === 2 ? "h3" : "h4";
  /** A fold of the card: its bar is the heading of what it holds, one level under the name of the card. */
  const folded = (says: string, holds: ReactNode) => (
    <Folded
      stands="stacked"
      className={styles.folded}
      // The arrow is handed once, to the fold, and its bar has it from there.
      style={theArrow()}
      bar={<Summary label={says} of={tag.label} stands="stacked" heading={level === 2 ? 3 : 4} handed />}
    >
      <div className={styles.unfolded}>{holds}</div>
    </Folded>
  );
  const parts = tag.terms.flatMap((term) => {
    const metric = features.find((one) => one.feature_id === term.feature_id);
    return metric === undefined ? [] : [{ term, metric }];
  });
  const missing = tag.terms.length - parts.length;
  const scale = tag.shape === "scale" && tag.low_end !== null && tag.high_end !== null;
  // A vibe the API says nothing of is offered, and the API answers for it.
  const placed = held?.placed ?? true;
  // What the recipe counts that is recorded crime, as the API names it. To add such a vibe
  // is to ask for recorded crime by name, so the card says so before anything is pressed.
  const crime = countsOf(tag, features);

  return (
    <Frame kind="box-on" as="section" id={id} className={styles.card} aria-labelledby={`${id}-name`}>
      <Name id={`${id}-name`} className={styles.name}>
        {tag.label}
      </Name>
      <p className={styles.meaning}>{tag.meaning}</p>
      {scale ? (
        <p className={styles.ends}>
          <Art name={pictureOfEnd(tag.low_end ?? "")} alt="" />
          <span className={styles.between}>{SHELF.scale(tag.low_end ?? "", tag.high_end ?? "")}</span>
          <Art name={pictureOfEnd(tag.high_end ?? "")} alt="" />
        </p>
      ) : null}

      {/* A vibe that no area can be placed on says so first, and is not offered: there is
          nothing for a search to rank on. */}
      {placed ? null : (
        <p className={styles.waits} role="note">
          {SHELF.notPlaced(tag.label)}
        </p>
      )}
      {held === undefined ? null : (
        <p className={styles.held}>{held.held === 100 ? SHELF.whole : SHELF.held(held.held, held.needed)}</p>
      )}

      {crime === null ? null : (
        <p className={styles.crime} role="note" aria-label={CRIME_ACCOUNT.counts}>
          {crime} {CRIME_ACCOUNT.rule} {askingFor(tag)}
        </p>
      )}

      {/* What can be pressed comes before what is long, so that it is in sight when the card opens.
          None of it is cobalt: Search is in sight, and is the one button that is. */}
      <div className={styles.buttons}>
        {!placed ? null : scale && tag.shelf_toward === null ? (
          // A scale with no word of its own on the shelf says neither end. The person chooses one.
          <>
            <Press onPress={() => onAdd(edits.tagOn(tag.tag_id, "low"))}>{SHELF.addToward(tag.low_end ?? "")}</Press>
            <Press onPress={() => onAdd(edits.tagOn(tag.tag_id, "high"))}>{SHELF.addToward(tag.high_end ?? "")}</Press>
          </>
        ) : (
          <Press onPress={() => onAdd(edits.tagOn(tag.tag_id, tag.shelf_toward ?? "high"))}>{SHELF.add}</Press>
        )}
        <Press onPress={onClose}>{SHELF.close}</Press>
      </div>

      {/* A city with no area placed on it is a city of dots, and says nothing. */}
      {city === null || !placed ? null : <City tag={tag} city={city} />}

      {parts.length > 0
        ? folded(
            SHELF.recipe,
            <ul className={styles.recipe}>
              {parts.map(({ term, metric }) => (
                <li key={term.feature_id}>
                  <span className={styles.share}>{SHELF.share(term.hundredths)}</span> {metric.label}
                  <span className={styles.reading}>{readingOf(tag, term.reading)}</span>
                </li>
              ))}
            </ul>,
          )
        : null}
      {held !== undefined && held.waits_on.length > 0 ? (
        // Each part the data does not hold is named, as the API names it, with what it
        // counts for. It was counted and not named: "2 parts of this recipe are not in this data".
        <>
          <Small className={styles.small}>{SHELF.waitsOn}</Small>
          <ul className={styles.recipe}>
            {held.waits_on.map((part) => (
              <li key={part.feature_id}>
                <span className={styles.share}>{SHELF.share(part.hundredths)}</span> {part.label}
                <span className={styles.reading}>{SHELF.notHeld}</span>
              </li>
            ))}
          </ul>
        </>
      ) : missing > 0 ? (
        // Where the API names no part, the parts are counted, and said to be missing.
        <p className={styles.note}>{SHELF.missing(missing)}</p>
      ) : null}

      {folded(
        SHELF.cannotSee,
        <ul className={styles.cannot}>
          {tag.cannot_see.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>,
      )}
    </Frame>
  );
}

/**
 * The shelf a search can start from: seven everyday words as buttons, and the
 * rest under "more". A word opens its card in place, and colours the map by
 * that vibe. On a narrow screen, where the map is out of sight, the card
 * holds the city coloured by the vibe, with its legend. Nothing is sent when
 * a word is pressed: the bands of every vibe came with the page, so nobody
 * is told which word it was.
 *
 * The word that was pressed stays where it was pressed. The shelf stands at
 * the foot of the window once its helper has opened it, and the card of a
 * word opened under the words, out of sight: brought into sight by its head,
 * it took the word 189 px from under the hand. So the card that a hand opens
 * stands where the whole of it has room, under the words or over them. It
 * comes before the words in the page where it stands over them. Where it
 * has room neither way it stands under them, and its head is brought into
 * sight. What the keys open stands under the words.
 *
 * The shelf is a box. A word is a chip with the small drawing of its vibe
 * beside it, which is chosen by the id and the family the API gives the vibe
 * and falls to the plain one. While its card is open a word is amber, and
 * says that it is open.
 *
 * On the first screen it stands under the helper that opens it, which bears
 * its name. The name is said once: the shelf has no heading there, and is
 * named by the helper. What is headed in it is then headed one level up, so
 * that no level is skipped under the heading of the page.
 */
export function Shelf({
  tags,
  features,
  recipes = [],
  open,
  onOpen,
  onAdd,
  geometry = null,
  bands = [],
  opens,
}: Props) {
  const id = useId();
  // On the first screen the shelf stands under the helper that opens it, which says its name.
  const under = useHelper();
  const headed = headedUnder(under, SHELF.title);
  // Where the shelf has no heading of its own, what is headed in it is headed one level up,
  // so that no level is skipped between the heading of the page and the name of a card.
  const level = headed === "named" ? 2 : 3;
  const [more, setMore] = useState(false);
  const words = useRef(new Map<TagId, HTMLButtonElement>());
  /** What holds every word of the shelf: the card of one stands under it, or over it. */
  const all = useRef<HTMLDivElement>(null);
  const where = useWhereItOpens(all, `${id}-card`, open, opens);
  const heldOf = (tag: Tag) => recipes.find((one) => one.tag_id === tag.tag_id);
  // The words a search can start from come first, in the order the API gives the shelf.
  // A word that no area can be placed on comes after every one of them, and stands apart.
  const inOrder = inShelfOrder(tags);
  const waiting = inOrder.filter((tag) => heldOf(tag)?.placed === false);
  const ordered = [...inOrder.filter((tag) => !waiting.includes(tag)), ...waiting];
  const answerable = ordered.length - waiting.length;
  // The outlines are worked out once for the boundaries in hand: every card draws every area.
  const outlines = useMemo(() => (geometry === null ? [] : outlinesOf(geometry, VIBE_MAP_FRAME)), [geometry]);
  /** Closes the card. The button that closed it goes with it, so the focus goes back to its word. */
  const close = (tagId: TagId) => {
    const word = words.current.get(tagId);
    word?.focus();
    // The words stay where they stand, whichever side of them the card goes from.
    if (word !== undefined) where.pressed(word, false);
    onOpen(null);
  };
  const opened = ordered.find((tag) => tag.tag_id === open);
  // The card of a word under "more" is never left open with its word out of sight: a vibe
  // the page opens from elsewhere brings the rest of the shelf with it.
  // What stands on the shelf at first: seven words at most, and none that cannot be added.
  const atFirst = Math.min(ON_THE_SHELF, answerable);
  const underMore = ordered.slice(atFirst).some((tag) => tag.tag_id === open);
  const shown = more || underMore ? ordered : ordered.slice(0, atFirst);
  if (ordered.length === 0) return null;
  // Escape closes the card that is open, as it closes everything that opens in place,
  // wherever on the shelf the focus is.
  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key !== "Escape" || opened === undefined) return;
    event.stopPropagation();
    close(opened.tag_id);
  };
  const wordButton = (tag: Tag) => (
    <li key={tag.tag_id}>
      <button
        ref={(button) => {
          if (button === null) words.current.delete(tag.tag_id);
          else words.current.set(tag.tag_id, button);
        }}
        type="button"
        className={`${styles.word} target`}
        aria-expanded={tag.tag_id === open}
        aria-controls={`${id}-card`}
        onClick={(event) => {
          // A press by the keys is counted as none by a browser, and a hand's as one.
          where.pressed(event.currentTarget, event.detail > 0);
          onOpen(tag.tag_id === open ? null : tag.tag_id);
        }}
      >
        {/* The drawing is dress. The word beside it is the API's, and names the button. */}
        <Thing kind="tag" id={tag.tag_id} family={tag.family} />
        <span className={styles.says}>{wordOf(tag)}</span>
      </button>
    </li>
  );
  const theWords = (
    <div key="words" ref={all} className={styles.all} data-words="">
      <ul className={styles.words}>
        {shown.slice(0, answerable).map(wordButton)}
        {ordered.length > atFirst ? (
          <li>
            <Press
              expanded={shown.length === ordered.length}
              onPress={() => {
                const every = shown.length === ordered.length;
                setMore(!every);
                // A card whose word goes out of sight goes with it.
                if (every && underMore) onOpen(null);
              }}
            >
              {shown.length === ordered.length ? SHELF.fewer : SHELF.more}
            </Press>
          </li>
        ) : null}
      </ul>
      {/* The words that cannot be added yet stand apart, under what they are. Each opens
          as any word does, and says what it waits on. */}
      {shown.length > answerable ? (
        <div className={styles.apart}>
          {/* It is a small heading, in the face of a sentence, at whichever level it stands. */}
          <p id={`${id}-waiting`} className={styles.waiting} role="heading" aria-level={level}>
            {SHELF.waiting}
          </p>
          <ul className={styles.words} aria-labelledby={`${id}-waiting`}>
            {shown.slice(answerable).map(wordButton)}
          </ul>
        </div>
      ) : null}
    </div>
  );
  // The card has its place whether or not a word is open, so that the buttons can name it.
  const theCard = (
    <div key="card" id={`${id}-card`} className={styles.place}>
      {opened === undefined ? null : (
        <VibeCard
          // A card is made anew for each word: what a person opened in one is closed in the next.
          key={opened.tag_id}
          level={level}
          tag={opened}
          held={heldOf(opened)}
          features={features}
          id={`${id}-open`}
          onAdd={onAdd}
          onClose={() => close(opened.tag_id)}
          city={cityOf(opened, outlines, bands)}
        />
      )}
    </div>
  );
  return (
    // The keys are heard here for what is inside: the buttons are the controls.
    <Frame
      kind="box"
      as="section"
      className={styles.shelf}
      aria-labelledby={headed === "named" ? under?.by : `${id}-title`}
      onKeyDown={onKeyDown}
    >
      {/* Under the helper of its name the name is said once, by the helper. */}
      {headed === "named" ? null : (
        <h2 id={`${id}-title`} className={headed === "heard" ? "visually-hidden" : styles.title}>
          {SHELF.title}
        </h2>
      )}
      {/* What a word is, and what a press on one does, is said before the words. */}
      <p className={styles.lead}>{SHELF.lead}</p>
      {/* In the order they are drawn in. Each is told by its key, so that the card is moved
          from one side of the words to the other, and is not made anew. */}
      {where.side === "over" ? [theCard, theWords] : [theWords, theCard]}
    </Frame>
  );
}
