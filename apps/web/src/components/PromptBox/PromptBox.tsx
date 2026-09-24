"use client";

import Link from "next/link";
import {
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
import { WORDS_LINE } from "@/content/site";
import type { ServedLimits } from "@/lib/api/schema";
import { paths } from "@/lib/paths";

import styles from "./PromptBox.module.css";

/** The count of characters left is shown once fewer than this many remain. */
const COUNT_FROM = 100;

/**
 * What the page may ask of the box: what is in it now, to send it again, and to have a
 * part of it selected. The words stay in the box either way.
 */
export interface PromptHandle {
  readonly text: () => string;
  /** Selects a part of what is in the box, from `start` up to `end`, and gives the box the focus. */
  readonly select: (part: { readonly start: number; readonly end: number }) => void;
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
   * True once a search is open. What is typed is then added to it, and the box says so, with
   * a way to start again beside it. The examples are for a first search, and go.
   */
  readonly open?: boolean;
  readonly onStartAgain?: () => void;
  /** Told whenever what is in the box changes. It is told that it changed, and never what to. */
  readonly onTyped?: () => void;
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
 * What Burro makes of a search is drawn directly under the box, before the
 * examples, so that pressing Search changes what is on screen.
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
  children,
}: Props) {
  const id = useId();
  const box = useRef<HTMLTextAreaElement>(null);
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
    }),
    [],
  );
  const [length, setLength] = useState(0);
  const [empty, setEmpty] = useState(false);
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

  const use = (example: string) => {
    if (!box.current) return;
    box.current.value = example;
    setLength(example.length);
    setEmpty(false);
    onTyped?.();
    box.current.focus();
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
    `${id}-hint`,
    counting ? `${id}-count` : null,
    problem ? `${id}-problem` : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.prompt}>
      <form method="post" className={styles.form} onSubmit={onFormSubmit} noValidate>
        <label className={styles.label} htmlFor={`${id}-box`}>
          {PROMPT.label}
        </label>
        <p id={`${id}-hint`} className={styles.hint}>
          {open ? PROMPT.hintOpen : PROMPT.hint}
        </p>
        <textarea
          ref={box}
          id={`${id}-box`}
          className={`${styles.box} target`}
          rows={3}
          maxLength={maxText}
          autoComplete="off"
          // A browser's fuller spell check sends the text of a checked field to its maker.
          // That would be a second place for the words to go, and no policy can stop it.
          spellCheck={false}
          aria-describedby={described}
          aria-invalid={problem ? true : undefined}
          onInput={(event) => {
            setLength(event.currentTarget.value.length);
            if (empty) setEmpty(false);
            onTyped?.();
          }}
          onKeyDown={onKeyDown}
        />
        <div className={styles.under}>
          {/* The space is kept whether or not the count shows, so nothing moves when it does. */}
          <p id={`${id}-count`} className={styles.count}>
            {counting ? PROMPT.left(Math.max(0, left)) : null}
          </p>
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

      <p className={styles.words}>
        {WORDS_LINE}{" "}
        <Link href={paths.methods()} prefetch={false}>
          {PROMPT.wordsLink}
        </Link>
      </p>

      {children}

      {open ? null : (
        <section className={styles.examples} aria-labelledby={`${id}-examples`}>
          <h2 id={`${id}-examples`} className={styles.examplesTitle}>
            {PROMPT.examplesTitle}
          </h2>
          <p id={`${id}-examples-hint`} className={styles.hint}>
            {PROMPT.examplesHint}
          </p>
          <ul className={styles.list}>
            {EXAMPLES.map((example) => (
              <li key={example}>
                <button
                  type="button"
                  className={`${styles.example} target`}
                  aria-describedby={`${id}-examples-hint`}
                  onClick={() => use(example)}
                >
                  {example}
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
