import type { CSSProperties, ReactNode } from "react";

import { Art } from "../kit/Art/Art";
import { sizeOf, type Drawing } from "../kit/drawings";
import { Frame } from "../kit/Frame/Frame";
import styles from "./About.module.css";

interface Props {
  /** The one heading of the page. */
  readonly title: string;
  /** What the page is for, in a sentence or two, under its heading. */
  readonly lead: string;
  /** A small drawing beside the heading. It is dress: it says nothing, and is kept from a screen reader. */
  readonly art?: Drawing;
  /** The parts of the page. Each brings the box it is read in. */
  readonly children: ReactNode;
}

/**
 * A page that explains: the vibes, the methods, the sources. It stands on the meadow as
 * boxes of cream, one over the other, with grass between them: its heading in the first,
 * and each of its parts in a box of its own.
 *
 * It is read more than it is used, so it is the calmest of the website. Burro is not drawn
 * on it, nothing of it moves, and every sentence is set as every sentence is: in ink, on
 * cream, in the reading face.
 *
 * It tells the shell that it stands boxes of its own, so the shell draws none round it.
 * From then on nothing of the page may stand loose: what is handed to it is a box, or is
 * given one here.
 */
export function About({ title, lead, art, children }: Props) {
  return (
    <div className={styles.page} data-dressed>
      <Frame kind="box" bare className={styles.head}>
        <div className={styles.titled} data-drawn={art !== undefined}>
          {art === undefined ? null : <Art name={art} alt="" />}
          <h1 className={styles.title}>{title}</h1>
        </div>
        <p className={styles.lead}>{lead}</p>
      </Frame>
      {children}
    </div>
  );
}

/** The key of a source, as the look draws one. */
const KEY: Drawing = "ui-key";

interface PartProps {
  /** The id of its heading, which another page may lead to. */
  readonly id: string;
  /** What its heading says. */
  readonly title: string;
  /**
   * `beside`: where there is room its heading stands beside what is read, and what is read
   * is as wide as a line reads well. `over`: its heading stands over what it holds, for
   * what is wide, as a table or a row of cards is.
   */
  readonly lay?: "beside" | "over";
  /** False of a part that was no landmark of the page, and is none now. */
  readonly region?: boolean;
  /**
   * True of a part that a link leads to, from this page or another. Its heading then takes
   * the focus as the link is followed, so that whoever hears the page is brought to the part
   * as whoever sees it is. No key of the keyboard stops at it.
   */
  readonly led?: boolean;
  /** A class of whatever lays the part out. It sets where the part stands, never how it is drawn. */
  readonly className?: string;
  readonly children: ReactNode;
}

/**
 * One part of a page that explains, in a box of its own: its heading, and what is read
 * under it. The heading is the part's own child, and what is read stands together after it.
 */
export function Part({ id, title, lay = "beside", region = true, led = false, className, children }: PartProps) {
  return (
    <Frame
      kind="box"
      as={region ? "section" : "div"}
      bare
      className={[styles.part, className].filter(Boolean).join(" ")}
      data-lay={lay}
      {...(region ? { "aria-labelledby": id } : {})}
    >
      <h2 id={id} className={styles.heading} tabIndex={led ? -1 : undefined}>
        {title}
      </h2>
      <div className={styles.holds}>{children}</div>
    </Frame>
  );
}

/** A list of a part, as the look marks one: each line by a square of ink. What it holds is its lines. */
export function Marked({ children }: { readonly children: ReactNode }) {
  return <ul className={styles.points}>{children}</ul>;
}

/** The points of a part, in the order they were given, each a line of a list. */
export function Points({ points }: { readonly points: readonly string[] }) {
  return (
    <Marked>
      {points.map((point) => (
        <li key={point}>{point}</li>
      ))}
    </Marked>
  );
}

interface BoardProps {
  /** The rank of the heading. It is drawn the same whatever its rank. */
  readonly as: "h3" | "h4";
  readonly id?: string;
  readonly children: ReactNode;
}

/**
 * A small heading inside a part, as the look draws the label of a part: a board of ink
 * with its words in the colour that is read on, in the face of names. So at the size of a
 * label it is never lighter to the eye than what it heads.
 */
export function Board({ as: Heading, id, children }: BoardProps) {
  return (
    <Heading id={id} className={styles.board}>
      {children}
    </Heading>
  );
}

/**
 * The sources of a thing that is written out: the key of the look, which is what a source
 * is known by wherever one is shown, and after it each source, as an item of a list. The
 * key is dress, and opens nothing: on a page that is built ahead of time a source is
 * written out, and nothing has to be pressed to read it.
 */
export function Sourced({ children }: { readonly children: ReactNode }) {
  // How high the key is, in pixels of a drawing: the style sheet stands it half way up a line of names.
  const high = { "--key-h": sizeOf(KEY).height } as CSSProperties;
  return (
    <div className={styles.sourced} style={high}>
      <Art name={KEY} alt="" />
      <ul className={styles.sources}>{children}</ul>
    </div>
  );
}

/** What holds a table: a plain edge of ink, and no shadow. The table is what it was. */
export function Edged({ children }: { readonly children: ReactNode }) {
  return (
    <Frame kind="plain" bare className={styles.edged}>
      {children}
    </Frame>
  );
}

/** A box for a part that another component draws whole, with a heading of its own. */
export function Boxed({ children }: { readonly children: ReactNode }) {
  return (
    <Frame kind="box" bare className={styles.boxed}>
      {children}
    </Frame>
  );
}

/** A slip of cream inside a plain edge of ink, for a line that belongs to no part. */
export function Slip({ children }: { readonly children: ReactNode }) {
  return (
    <Frame kind="plain" bare className={styles.slip}>
      {children}
    </Frame>
  );
}

/**
 * What another hand draws, held as it came. It is given no ground it did not ask for: a
 * part that stands boxes of its own stands them on the grass. Only a sentence that it
 * leaves loose is given cream to be read on.
 */
export function Loose({ children }: { readonly children: ReactNode }) {
  return (
    <div className={styles.loose} data-held="as-it-came">
      {children}
    </div>
  );
}
