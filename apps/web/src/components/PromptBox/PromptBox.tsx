"use client";

import Link from "next/link";
import {
  useEffect,
  useId,
  useImperativeHandle,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type ReactNode,
  type Ref,
} from "react";

import { EXAMPLES, PROMPT } from "@/content/search";
import { READER, WORDS_LINE } from "@/content/site";
import type { Reader, ServedLimits } from "@/lib/api/schema";
import { paths } from "@/lib/paths";

import styles from "./PromptBox.module.css";

/** The count of characters left is shown once fewer than this many remain. */
const COUNT_FROM = 100;

/**
 * What the page may ask of the box: what is in it now, to send it again, to have a part of
 * it selected, and to have an example put in it. The words stay in the box either way.
 */
export interface PromptHandle {
  readonly text: () => string;
  /** Selects a part of what is in the box, from `start` up to `end`, and gives the box the focus. */
  readonly select: (part: { readonly start: number; readonly end: number }) => void;
  /** Puts an example in the box, in place of what is there, and gives the box the focus. Nothing is sent. */
  readonly fill: (example: string) => void;
}

interface Props {
  readonly maxText: ServedLimits["max_text"];
  /** True while a sentence is being read. */
  readonly busy: boolean;
  readonly onSubmit: (text: string) => void;
  readonly onStop: () => void;
  /** The API's own words for why the text was refused, when it was. */
  readonly refusal?: string | null;
  /** A way to read the box, so that "Try again" can send what is in it. */
  readonly ref?: Ref<PromptHandle>;
  /**
   * True once a search is open. The box is then on one line, so that the answer comes
   * first. What is typed is added to the search, and the box says so, with a way to start
   * again beside it.
   */
  readonly open?: boolean;
  readonly onStartAgain?: () => void;
  /** Told whenever what is in the box changes. It is told that it changed, and never what to. */
  readonly onTyped?: () => void;
  /**
   * Who reads what is typed, as the service says now. `null` until it has said. Its notice
   * is drawn as it was served: the website writes no provider's name and no terms.
   */
  readonly reader?: Reader | null;
  /** True when the service was asked who reads and could not say. */
  readonly readerFailed?: boolean;
  /**
   * What to say a person may type, under the label. It asks only for what the data can
   * answer. Left out, it asks for everything.
   */
  readonly hint?: string;
  /** What Burro says of the search: drawn directly under the box, where it is seen when Search is pressed. */
  readonly children?: ReactNode;
}

/**
 * The one box to type in.
 *
 * What is typed is held by the box and by nothing else: not by this
 * component's state, which keeps only how many characters there are. The
 * form is a `post` with no name on its field, so that if scripts fail,
 * pressing Enter cannot put the text in an address, and the browser is asked
 * not to keep it for next time, and not to check its spelling.
 *
 * What Burro makes of a search is drawn directly under the box, so that
 * pressing Search changes what is on screen.
 *
 * Once a search is open the box is one line high, and takes room for three
 * while it is typed in. It never gives that room back under a press: what is
 * under the box would move between the button going down and coming up, and
 * the press would land on nothing. So how high it is follows what was done,
 * and never the focus alone (`tall`).
 */
export function PromptBox({
  maxText,
  busy,
  onSubmit,
  onStop,
  refusal = null,
  ref,
  open = false,
  onStartAgain,
  onTyped,
  reader = null,
  readerFailed = false,
  hint = PROMPT.hint,
  children,
}: Props) {
  const id = useId();
  const box = useRef<HTMLTextAreaElement>(null);
  const [length, setLength] = useState(0);
  const [empty, setEmpty] = useState(false);
  // True while the box has room for what is typed in it. It matters only once a search is open.
  const [tall, setTall] = useState(false);
  // True from the button of a mouse going down to the press landing. A finger is heard the
  // same way: a browser makes the events of a mouse from a tap, and moves the focus with them.
  const pressing = useRef(false);

  useEffect(() => {
    const began = () => {
      pressing.current = true;
    };
    const over = () => {
      pressing.current = false;
    };
    // The press has landed. If it took the focus from the box, the box may now be one line.
    const landed = () => {
      pressing.current = false;
      if (document.activeElement !== box.current) setTall(false);
    };
    document.addEventListener("mousedown", began, true);
    document.addEventListener("mouseup", over);
    document.addEventListener("click", landed);
    return () => {
      document.removeEventListener("mousedown", began, true);
      document.removeEventListener("mouseup", over);
      document.removeEventListener("click", landed);
    };
  }, []);

  useImperativeHandle(
    ref,
    () => ({
      text: () => box.current?.value ?? "",
      select({ start, end }) {
        const field = box.current;
        if (!field) return;
        field.focus();
        field.setSelectionRange(start, end);
      },
      fill(example) {
        const field = box.current;
        if (!field) return;
        field.value = example;
        setLength(example.length);
        setEmpty(false);
        onTyped?.();
        field.focus();
      },
    }),
    [onTyped],
  );
  const left = maxText - length;
  const counting = left < COUNT_FROM;
  const problem = refusal ?? (empty ? PROMPT.empty : null);

  const send = () => {
    if (busy) return;
    const text = box.current?.value ?? "";
    if (text.trim() === "") {
      setEmpty(true);
      box.current?.focus();
      return;
    }
    setEmpty(false);
    // The answer comes first: the box gives its room back, though the focus stays in it.
    setTall(false);
    onSubmit(text);
  };

  const onFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    send();
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter sends. Shift and Enter starts a new line. A key pressed to pick a
    // character, as when writing in Japanese, is left alone.
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) return;
    event.preventDefault();
    send();
  };

  const startAgain = () => {
    if (box.current) {
      box.current.value = "";
      box.current.focus();
    }
    setLength(0);
    setEmpty(false);
    onTyped?.();
    onStartAgain?.();
  };

  const described = [
    open ? null : `${id}-hint`,
    counting ? `${id}-count` : null,
    problem ? `${id}-problem` : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.prompt} data-open={open}>
      <form method="post" className={styles.form} onSubmit={onFormSubmit} noValidate>
        <div className={styles.over}>
          {/* Once a search is open the label says that what is typed is added to it. */}
          <label className={styles.label} htmlFor={`${id}-box`}>
            {open ? PROMPT.labelOpen : PROMPT.label}
          </label>
          {/* It has its place on the label's line whether or not it says anything, so nothing moves when it does. */}
          <span id={`${id}-count`} className={styles.count}>
            {counting ? PROMPT.left(Math.max(0, left)) : null}
          </span>
          {/* Before a search the line on how words are handled stands under the box, in full. */}
          {open ? (
            <Link className={`${styles.wordsLink} target-min`} href={paths.methods("words")} prefetch={false}>
              {PROMPT.wordsLink}
            </Link>
          ) : null}
        </div>
        {open ? null : (
          <p id={`${id}-hint`} className={styles.hint}>
            {hint}
          </p>
        )}
        <div className={styles.line}>
          <textarea
            ref={box}
            id={`${id}-box`}
            className={`${styles.box} target`}
            rows={open ? 1 : 2}
            maxLength={maxText}
            autoComplete="off"
            // A browser's fuller spell check sends the text of a checked field to its maker.
            // That would be a second place for the words to go, and no policy can stop it.
            spellCheck={false}
            aria-describedby={described === "" ? undefined : described}
            aria-invalid={problem ? true : undefined}
            data-tall={tall}
            onFocus={() => setTall(true)}
            // Left by keyboard, it is one line at once. Left by a press, it waits for the press to land.
            onBlur={() => {
              if (!pressing.current) setTall(false);
            }}
            onInput={(event) => {
              setLength(event.currentTarget.value.length);
              if (empty) setEmpty(false);
              setTall(true);
              onTyped?.();
            }}
            onKeyDown={onKeyDown}
          />
          <div className={styles.buttons}>
            {busy ? (
              <button type="button" className={`${styles.stop} target`} onClick={onStop}>
                {PROMPT.stop}
              </button>
            ) : open && onStartAgain ? (
              <button type="button" className="target" onClick={startAgain}>
                {PROMPT.startAgain}
              </button>
            ) : null}
            <button
              type="submit"
              className={`${styles.submit} target`}
              aria-disabled={busy ? true : undefined}
            >
              {busy ? PROMPT.reading : PROMPT.submit}
            </button>
          </div>
        </div>
        {problem ? (
          <p id={`${id}-problem`} className={styles.problem} role="alert">
            {problem}
          </p>
        ) : null}
      </form>

      {/*
        Before anything is sent, how words are handled is said in full, where it is typed.
        What Burro does with them is the website's to say. Who else reads them is the
        service's, and is drawn as it was served. Once a search is open the answer comes
        first, and the line is one press away.
      */}
      {open ? null : (
        <div className={styles.words} role="group" aria-label={READER.label}>
          <p>{WORDS_LINE}</p>
          <p data-reader={reader === null ? (readerFailed ? "unsaid" : "checking") : "said"}>
            {reader === null ? (readerFailed ? READER.unsaid : READER.checking) : reader.notice}
            {/* What the company does with the words is the company's to say, on its own page. */}
            {reader?.terms_url ? (
              <>
                {" "}
                <a className="target-min" href={reader.terms_url} rel="noreferrer noopener">
                  {READER.terms}
                </a>
              </>
            ) : null}
          </p>
          <p>
            <Link className="target-min" href={paths.methods("words")} prefetch={false}>
              {PROMPT.wordsLink}
            </Link>
          </p>
        </div>
      )}

      {children}
    </div>
  );
}

interface ExamplesProps {
  /** Puts the example in the box. Nothing is sent until Search is pressed. */
  readonly onUse: (example: string) => void;
  /** The sentences to offer. Left out, the three that a release that holds everything shows. */
  readonly examples?: readonly string[];
}

/**
 * Three sentences to start from. Each fills the box and sends nothing. They
 * are for a first search: once a search is open an example would be added to
 * it, so the page takes them away.
 */
export function Examples({ onUse, examples = EXAMPLES }: ExamplesProps) {
  const id = useId();
  // Where the data can answer no sentence of them, none is offered, and no heading over none.
  if (examples.length === 0) return null;
  return (
    <section className={styles.examples} aria-labelledby={`${id}-examples`}>
      <h2 id={`${id}-examples`} className={styles.examplesTitle}>
        {PROMPT.examplesTitle}
      </h2>
      <p id={`${id}-examples-hint`} className={styles.hint}>
        {PROMPT.examplesHint}
      </p>
      <ul className={styles.list}>
        {examples.map((example) => (
          <li key={example}>
            <button
              type="button"
              className={`${styles.example} target`}
              aria-describedby={`${id}-examples-hint`}
              onClick={() => onUse(example)}
            >
              {example}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
