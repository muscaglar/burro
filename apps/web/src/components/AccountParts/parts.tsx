"use client";

import { useId, useSyncExternalStore, type ReactNode, type Ref } from "react";

import { NOTICE } from "@/content/search";
import { isAway, subscribeToAway } from "@/lib/account/away";
import type { Failure } from "@/lib/api/failure";

import { wordsFor } from "../ErrorBlock/ErrorBlock";
import { Frame } from "../kit/Frame/Frame";
import styles from "./parts.module.css";

/** While a page is built it is put away by nobody. */
const asBuilt = () => false;

/**
 * Holds a page of accounts for as long as it is open, and lets all of it go as the
 * browser puts the page away to come back to.
 *
 * A browser shows a page that it kept as it stood, and asks nothing as it does: so a page
 * that showed an account would show it to whoever pressed Back, though the person had
 * signed out since. While the page is put away nothing of it is drawn, and nothing that
 * it held is held: the address, the searches, the token of a link. When the browser shows
 * it again the page begins again, as it does when it is first opened, and asks the service.
 */
export function WhileOpen({ children }: { readonly children: ReactNode }) {
  const away = useSyncExternalStore(subscribeToAway, isAway, asBuilt);
  return away ? null : children;
}

interface PageProps {
  /**
   * `narrow`: a page that says one thing and asks one, in the middle of the screen and no
   * wider than a sentence is read at. `wide`: a page of several boxes, as wide as the page.
   */
  readonly lay?: "narrow" | "wide";
  readonly children: ReactNode;
}

/**
 * A page of accounts. It stands boxes of its own on the grass and says so, so that the
 * shell draws none round it. From then on nothing of the page may stand loose: what it
 * holds is a box, a notice or a failure, and each brings the cream it is read on.
 */
export function Page({ lay = "wide", children }: PageProps) {
  return (
    <div className={styles.page} data-dressed="" data-lay={lay}>
      {children}
    </div>
  );
}

interface BoxProps {
  /** The heading of the box, where it has one. The first box of a page holds the heading of the page. */
  readonly title?: string;
  /** The rank of the heading: the one heading of the page, or the heading of one of its boxes. */
  readonly rank?: 1 | 2;
  /** The id of the heading, by which the box is named to whoever hears the page. */
  readonly id?: string;
  /** The heading itself, for a page that hands it the focus: what was pressed and went leaves the focus here. */
  readonly heading?: Ref<HTMLHeadingElement>;
  readonly children: ReactNode;
}

/**
 * One box of a page: its heading, and what is read under it. A box that has a heading of
 * the second rank is a part of the page by that name, to whoever goes from part to part.
 *
 * Its heading can be handed the focus, and is no stop of its own.
 */
export function Box({ title, rank = 2, id, heading, children }: BoxProps) {
  const own = useId();
  const named = id ?? own;
  const Heading = rank === 1 ? "h1" : "h2";
  return (
    <Frame
      kind="box"
      as={title !== undefined && rank === 2 ? "section" : "div"}
      bare
      className={styles.box}
      {...(title !== undefined && rank === 2 ? { "aria-labelledby": named } : {})}
    >
      {title === undefined ? null : (
        <Heading id={named} ref={heading} className={`${rank === 1 ? styles.title : styles.heading} ${styles.lands}`} tabIndex={-1}>
          {title}
        </Heading>
      )}
      {children}
    </Frame>
  );
}

interface FailedProps {
  /** What it was that failed, in a line: the failure says why. */
  readonly title: string;
  readonly failure: Failure;
  /** What can be done about it: a button, or a link drawn as one. */
  readonly children?: ReactNode;
}

/**
 * Says that something failed, in words, and what can be done. It is an alert, so a screen
 * reader says it at once.
 *
 * What it says is the service's own fixed text for what it refused with, or site copy
 * where the failure is not the service's, and the id of the request to quote. It shows
 * nothing that was sent, because it is given nothing that was sent.
 */
export function Failed({ title, failure, children }: FailedProps) {
  return (
    <div className={styles.failed} role="alert">
      <p className={styles.failedTitle}>{title}</p>
      <p>{wordsFor(failure)}</p>
      {failure.requestId !== null ? (
        <p className={styles.request}>
          {NOTICE.requestId} <code>{failure.requestId}</code>
        </p>
      ) : null}
      {children === undefined ? null : <div className={styles.ways}>{children}</div>}
    </div>
  );
}

interface NoticeProps {
  /** What the notice is of, in a line. */
  readonly title?: string;
  /** True of what a person is told the moment it is so. Left out, it is read where it stands. */
  readonly atOnce?: boolean;
  readonly children: ReactNode;
}

/** What a person is to read before they go on: cream, inside a rule of ink, with a band of amber at its start. */
export function Notice({ title, atOnce = false, children }: NoticeProps) {
  return (
    <div className={styles.notice} role={atOnce ? "alert" : undefined}>
      {title === undefined ? null : <p className={styles.noticeTitle}>{title}</p>}
      {children}
    </div>
  );
}

interface TickProps {
  /** What ticking it says, in the words of whoever ticks it: "I am 18 or over". */
  readonly says: string;
  readonly ticked: boolean;
  readonly onTick: (ticked: boolean) => void;
  /** What is said of it under it, where more is to be said. */
  readonly hint?: string;
  /** True once a person went on without it and may not: what is missing is then said under it, at once. */
  readonly missing?: string | null;
  /** True while it waits on an answer. It says that it is off and keeps the focus. */
  readonly off?: boolean;
  /** The box itself, for a page that hands it the focus. */
  readonly box?: Ref<HTMLInputElement>;
}

/**
 * A tick and its words: the browser's own checkbox, drawn in the look. The whole line
 * takes the press. It is never switched off: a control that is switched off while it has
 * the focus leaves the focus on nothing. While it waits it ignores the press and says so.
 */
export function Tick({ says, ticked, onTick, hint, missing = null, off = false, box }: TickProps) {
  const id = useId();
  const described = [hint === undefined ? null : `${id}-hint`, missing === null ? null : `${id}-missing`].filter(Boolean).join(" ");
  return (
    <div className={styles.tick}>
      <label className={styles.check}>
        <input
          ref={box}
          type="checkbox"
          className="target-min"
          checked={ticked}
          aria-describedby={described === "" ? undefined : described}
          aria-invalid={missing === null ? undefined : true}
          aria-disabled={off ? true : undefined}
          onChange={(event) => {
            if (!off) onTick(event.target.checked);
          }}
        />
        <span>{says}</span>
      </label>
      {hint === undefined ? null : (
        <p id={`${id}-hint`} className={styles.quiet}>
          {hint}
        </p>
      )}
      {missing === null ? null : (
        <p id={`${id}-missing`} className={styles.failedTitle} role="alert">
          {missing}
        </p>
      )}
    </div>
  );
}
