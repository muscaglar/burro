"use client";

import { useId, useRef, useState } from "react";

import { CHIPS, NOTICE } from "@/content/search";
import { SHARE } from "@/content/share";
import type { Answer, Failure } from "@/lib/api/client";
import type { AreaSummary, MetaData, PreferenceSpec, ShareCreated } from "@/lib/api/schema";
import { isShareId, paths } from "@/lib/paths";
import { chipsOf } from "@/lib/search/chips";
import type { MadeShare } from "@/lib/session/session";

import { Disclosure } from "../Disclosure/Disclosure";
import { wordsFor } from "../ErrorBlock/ErrorBlock";
import styles from "./SharePanel.module.css";

interface Props {
  /** The search as it stands: the last spec the API returned. */
  readonly spec: PreferenceSpec;
  /** The hash of that spec, which tells one search from the next. `null` for a default. */
  readonly specHash: string | null;
  readonly meta: Pick<MetaData, "features" | "tags">;
  readonly areas: readonly AreaSummary[];
  /** The name of each place of the search, by place id, where one is in hand. */
  readonly placeNames: Readonly<Record<string, string>>;
  /** Route 9, with the spec the store holds. */
  readonly create: (exactPlaces: boolean, signal?: AbortSignal) => Promise<Answer<ShareCreated>>;
  /**
   * The link the store holds, made before the page was left. It is shown again for the
   * search it was made of, so that coming back does not mean making a second link.
   */
  readonly held?: MadeShare | null;
  /** Told of a link once it is made, so that it can be kept while the tab is open. */
  readonly onMade?: (made: MadeShare) => void;
}

type Said = "none" | "made" | "copied" | "not_copied";

/** The whole address of a share, or `null` when the id is not one the API makes. */
export function linkTo(shareId: string, origin: string): string | null {
  if (!isShareId(shareId)) return null;
  return `${origin}${paths.share(shareId)}`;
}

/** A name for each place the stored spec holds: the one in hand, or what stands in for it. */
function namesFor(share: ShareCreated, sent: PreferenceSpec, held: Readonly<Record<string, string>>) {
  const wasSent = new Set(sent.commutes.map((commute) => commute.place_id));
  const names: Record<string, string> = { ...held };
  share.spec.commutes.forEach((commute, at) => {
    // A place that was not in the search is the station or district that stands in for one that was.
    if (!wasSent.has(commute.place_id)) names[commute.place_id] = SHARE.standIn(at + 1);
  });
  return names;
}

/**
 * Makes a link to the search. It says what the link will hold before it is
 * made, and offers to share the exact places, unticked. The link holds an id
 * in its fragment and nothing else.
 *
 * It opens in place and traps nothing. The id is held in memory, here and in
 * the store, and is written nowhere.
 *
 * The button that makes the link is never switched off: a button that is
 * switched off while it has the focus leaves the focus on nothing. It says
 * that it is busy, and a press while it is asks for nothing more. So the
 * focus stays on it, and the next Tab reaches the field that holds the link.
 */
export function SharePanel({ spec, specHash, meta, areas, placeNames, create, held = null, onMade }: Props) {
  const id = useId();
  const field = useRef<HTMLInputElement>(null);
  const [exact, setExact] = useState(false);
  const [busy, setBusy] = useState(false);
  // `undefined` until a link is asked for here. Until then the one the store holds stands.
  const [made, setMade] = useState<MadeShare | null | undefined>(undefined);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [said, setSaid] = useState<Said>("none");

  // A link made of an earlier search is not shown for this one.
  const latest = made === undefined ? held : made;
  const link =
    latest !== null && latest.of === specHash && typeof window !== "undefined"
      ? linkTo(latest.share.share_id, window.location.origin)
      : null;
  const current = latest !== null && link !== null ? { ...latest, link } : null;
  const hasPlaces = spec.commutes.length > 0;

  const make = async () => {
    if (busy) return;
    setBusy(true);
    setFailure(null);
    setSaid("none");
    const answer = await create(hasPlaces && exact);
    setBusy(false);
    if (!answer.ok) {
      setMade(null);
      setFailure(answer.failure);
      return;
    }
    if (linkTo(answer.data.share_id, window.location.origin) === null) {
      // An id that is not one the API makes is not put in an address.
      setMade(null);
      setFailure({ kind: "unreadable", status: answer.status, synthetic: answer.synthetic, requestId: answer.requestId });
      return;
    }
    const kept: MadeShare = { of: specHash, exact: hasPlaces && exact, share: answer.data };
    setMade(kept);
    onMade?.(kept);
    setSaid("made");
  };

  const copy = async () => {
    if (current === null) return;
    try {
      await navigator.clipboard.writeText(current.link);
      setSaid("copied");
    } catch {
      // Where the browser will not copy, the link is selected for the person to copy.
      field.current?.focus();
      field.current?.select();
      setSaid("not_copied");
    }
  };

  const chips =
    current === null
      ? []
      : chipsOf(current.share.spec, meta, areas, namesFor(current.share, spec, placeNames), {});

  return (
    // Open at first where it holds a link made before the page was left.
    <Disclosure label={SHARE.open} className={styles.share} openAtFirst={current !== null}>
      <section className={styles.panel} aria-labelledby={`${id}-title`}>
        <h3 id={`${id}-title`} className={styles.title}>
          {SHARE.holds.title}
        </h3>
        <ul className={styles.points}>
          {SHARE.holds.points.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>

        {hasPlaces ? (
          <div className={styles.exact}>
            <label className={styles.check}>
              <input
                type="checkbox"
                className="target-min"
                checked={exact}
                aria-describedby={`${id}-exact`}
                onChange={(event) => setExact(event.target.checked)}
              />
              <span>{SHARE.exact.label}</span>
            </label>
            <p id={`${id}-exact`} className={styles.hint}>
              {SHARE.exact.hint}
            </p>
          </div>
        ) : (
          <p className={styles.hint}>{SHARE.noPlaces}</p>
        )}

        <button
          type="button"
          className={`${styles.make} target`}
          aria-disabled={busy ? true : undefined}
          onClick={() => void make()}
        >
          {busy ? SHARE.making : current === null ? SHARE.make : SHARE.makeAgain}
        </button>

        <p className={styles.said} role="status">
          {said === "made" && current !== null
            ? SHARE.made
            : said === "copied"
              ? SHARE.copied
              : said === "not_copied"
                ? SHARE.notCopied
                : ""}
        </p>

        {failure !== null ? (
          <div className={styles.error} role="alert">
            <p className={styles.errorTitle}>{SHARE.failed}</p>
            <p>{wordsFor(failure)}</p>
            {failure.requestId !== null ? (
              <p className={styles.request}>
                {NOTICE.requestId} <code>{failure.requestId}</code>
              </p>
            ) : null}
          </div>
        ) : null}

        {current !== null ? (
          <div className={styles.made}>
            <label className={styles.link} htmlFor={`${id}-link`}>
              {SHARE.link}
            </label>
            <div className={styles.linkRow}>
              {/* It has no name, so that a browser does not keep it, and it cannot be sent by a form. */}
              <input
                ref={field}
                id={`${id}-link`}
                className={styles.field}
                type="text"
                readOnly
                value={current.link}
                autoComplete="off"
                spellCheck={false}
                onFocus={(event) => event.target.select()}
              />
              <button type="button" className="target" onClick={() => void copy()}>
                {SHARE.copy}
              </button>
            </div>
            <p className={styles.hint}>
              {current.share.coarsened
                ? SHARE.coarsened
                : current.share.spec.commutes.length === 0
                  ? SHARE.noPlaces
                  : current.exact
                    ? SHARE.exactKept
                    : // Nothing was replaced, and nobody asked for that: each place stood in for itself.
                      SHARE.noneReplaced}
            </p>
            <h4 className={styles.stored}>{SHARE.stored}</h4>
            <ul className={styles.chips}>
              {chips.map((chip) => (
                <li key={chip.key} className={styles.chip} data-assumed={chip.assumed}>
                  <span className={styles.chipLabel}>{chip.label}</span>
                  {chip.assumed && !chip.parts.some((part) => part.assumed) ? (
                    <span className={styles.assumed}> {CHIPS.assumed}</span>
                  ) : null}
                  {chip.parts.map((part) => (
                    <span key={part.text}>
                      , {part.text}
                      {part.assumed ? <span className={styles.assumed}> {CHIPS.assumed}</span> : null}
                    </span>
                  ))}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>
    </Disclosure>
  );
}
