"use client";

import {
  useCallback,
  useEffect,
  useId,
  useImperativeHandle,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
  type Ref,
} from "react";
import { flushSync } from "react-dom";

import { ADDED } from "@/content/added";
import { EXAMPLES, PROMPT, SUGGEST } from "@/content/search";
import type { ServedLimits } from "@/lib/api/schema";
import { added, changeOf, moved, type Change, type How } from "@/lib/search/mark";
import { useMarks, type Marks } from "@/lib/search/store";

import { headedUnder, useHelper } from "../Helpers/Helpers";
import { pictureOf, sizeOf } from "../kit/drawings";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
import { HELP_ON_A_NARROW_SCREEN, type HelpStands } from "./look";
import styles from "./PromptBox.module.css";

/**
 * The carrot that lies beside the example in hand, as the style sheet needs it: where it is
 * served from, and its size in art pixels. It is the pointer of every menu of the look.
 */
const CARROT = {
  "--carrot": `url("${pictureOf("ui-carrot")}")`,
  "--carrot-w": sizeOf("ui-carrot").width,
  "--carrot-h": sizeOf("ui-carrot").height,
} as CSSProperties;

/** The count of characters left is shown once fewer than this many remain. */
const COUNT_FROM = 100;

/**
 * What the page may ask of the box: the words it sends, to send them again, to have a part
 * of them selected, and to have an example put in the box. The words stay in the box
 * either way.
 */
export interface PromptHandle {
  /**
   * The words the box sends to be read: what it holds that the search had not read when
   * they were sent. Before anything is read that is all it holds. The service counts where
   * words stand from the start of these.
   */
  readonly text: () => string;
  /**
   * Selects a part of those words, from `start` up to `end`, counted from where they begin,
   * and gives the box the focus.
   */
  readonly select: (part: { readonly start: number; readonly end: number }) => void;
  /** Puts an example in the box, in place of what is there, and gives the box the focus. Nothing is sent. */
  readonly fill: (example: string) => void;
}

/** What the box says under itself of what it sent or did not send, and why. `null` while it says nothing. */
type Said = "empty" | "nothingNew" | "changed" | "changedToo" | "stillRead" | "full" | null;

/**
 * How what came into the box came, as the browser names it, where it may have been in the
 * box before: the keys that undo, the keys that do again, and the key that puts back what
 * a key took out to the end of a line, which undoes that. What is pasted or dropped is
 * another matter: it had been in the box only if it was taken from there.
 */
function howOf(kind: string): How | undefined {
  if (kind === "historyRedo") return "redone";
  return kind.startsWith("history") || kind === "insertFromYank" ? "undone" : undefined;
}

const PASTED = new Set(["insertFromPaste", "insertFromPasteAsQuotation", "insertFromDrop"]);

interface Props {
  readonly maxText: ServedLimits["max_text"];
  /** True while a sentence is being read. */
  readonly busy: boolean;
  /** Handed what the box holds that the search has not read, as it was typed. */
  readonly onSubmit: (text: string) => void;
  readonly onStop: () => void;
  /** The API's own words for why the text was refused, when it was. */
  readonly refusal?: string | null;
  /** A way to read the box, so that "Try again" can send again what the box sent. */
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
   * What helps Burro most, under the label: what a useful sentence holds. It asks only for
   * what the data can answer. Left out, it asks for everything.
   */
  readonly hint?: string;
  /**
   * One whole sentence as an example, which is shown after it and is never put in the box:
   * a sentence the data can answer the whole of. `null` or left out, none is shown.
   */
  readonly example?: string | null;
  /**
   * True once the page has asked which screen there is, and it is a narrow one. The
   * sentences that help then come after the field in the page, as they are drawn: the
   * sheet draws them there on a narrow screen from the first, so nothing moves.
   */
  readonly narrow?: boolean;
  /** Where those sentences stand on a narrow screen. Left out, as the look has chosen. */
  readonly help?: HelpStands;
  /** What Burro says of the search: drawn directly under the box, where it is seen when Search is pressed. */
  readonly children?: ReactNode;
  /**
   * How far into the box the search has read, in counts, and whom to tell where the box was
   * changed. Left out, it is asked of the search that is open around the box.
   */
  readonly marks?: Marks;
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
 * pressing Search changes what is on screen. Nothing else stands there: how
 * words are handled is said on the page of methods, which the foot of every
 * page leads to, and not beside the box.
 *
 * Before a search the box says what to tell it, and under that what a useful
 * sentence holds, with one whole sentence as an example. On a narrow screen
 * they stand under the field, so that the field is in sight on the first
 * screen, and under what Burro says: a failure that was said under them
 * stood under the foot of a phone's screen, and a person who pressed Search
 * saw the page as it had been. Once a search is open they give way to the
 * answer.
 *
 * Once a search is open the box is one line high, and takes room for three
 * while it is typed in. It never gives that room back under a press: what is
 * under the box would move between the button going down and coming up, and
 * the press would land on nothing. So how high it is follows what was done,
 * and never the focus alone (`tall`).
 *
 * Once a search is open, what is typed is added to it. The box keeps what it
 * held, and sends what stands after the words the search has read: read a
 * second time, they would set back what a person has set by hand since. How
 * far the search has read is a count, which the store holds. The box tells
 * it where it was changed, in counts, and never what was typed.
 *
 * Search is the button of the page that matters most, and is cobalt. No
 * other button of the box is: Burro asks nothing, so nothing of his stands
 * under the box to matter more.
 *
 * It is drawn as a box of the look: cream, a double rule of ink and a hard
 * shadow. While it is typed in it is the box in hand, whose inner rule is
 * amber. That too follows what was done and never the focus alone, so it is
 * one with how high the box is. What Burro says of the search is in the box,
 * under the field: the box is where a person and Burro speak.
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
  hint = PROMPT.hint,
  example = null,
  narrow = false,
  help = HELP_ON_A_NARROW_SCREEN,
  children,
  marks: given,
}: Props) {
  const id = useId();
  const box = useRef<HTMLTextAreaElement>(null);
  const told = useMarks();
  const { read, from, apart, reading, edited, found } = given ?? told;
  const [length, setLength] = useState(0);
  const [said, setSaid] = useState<Said>(null);
  // Where the caret stood, or what was selected began, when it was last seen to move, and
  // the same as a change begins, where the browser says that one does. How much the box
  // held when it last said that it had changed. They are counts: nothing here holds what
  // was typed.
  const caret = useRef(0);
  const about = useRef<number | null>(null);
  const held = useRef(0);
  // What was last copied, cut or dragged from the box: where it began, how many characters
  // it was, and whether any of them stood among what the search had read, or has been sent
  // to be read since. What is then pasted, and is as long, is taken for the same words.
  // `null` once something else on the page is copied, and once the search begins again.
  // They are counts: what was copied is the clipboard's to hold, and is never read from it.
  const lifted = useRef<{ readonly from: number; readonly many: number; readonly read: boolean } | null>(null);
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
    // What is copied elsewhere on the page takes the place of what was copied from the box.
    const elsewhere = (event: Event) => {
      if (event.target !== box.current) lifted.current = null;
    };
    document.addEventListener("mousedown", began, true);
    document.addEventListener("mouseup", over);
    document.addEventListener("click", landed);
    document.addEventListener("copy", elsewhere, true);
    document.addEventListener("cut", elsewhere, true);
    return () => {
      document.removeEventListener("mousedown", began, true);
      document.removeEventListener("mouseup", over);
      document.removeEventListener("click", landed);
      document.removeEventListener("copy", elsewhere, true);
      document.removeEventListener("cut", elsewhere, true);
    };
  }, []);

  useEffect(() => {
    // A search that begins again has read nothing: what was copied from the box before it
    // began is new to it, as all else is.
    if (!open) lifted.current = null;
  }, [open]);

  useEffect(() => {
    // What was copied from before the place the search has read to has been read. The box
    // may be typed over since, and the place gone: that it was read is kept.
    const taken = lifted.current;
    if (taken !== null && !taken.read && taken.from < read.to) lifted.current = { ...taken, read: true };
  }, [read.to]);

  useEffect(() => {
    const field = box.current;
    if (!field) return;
    // The search is told how much the box holds as it is drawn. A box that is drawn again
    // is empty, whatever the search had read of the one before it.
    caret.current = field.selectionStart;
    held.current = field.value.length;
    found(field.value.length);
    // Where a change is about to begin. React hears of a change once it is made, and of
    // this only for letters that are typed.
    const begins = () => {
      about.current = field.selectionStart;
    };
    field.addEventListener("beforeinput", begins);
    return () => field.removeEventListener("beforeinput", begins);
  }, [found]);

  /** Puts these words in the box in place of all it holds, and says so, in counts. */
  const put = useCallback(
    (words: string) => {
      const field = box.current;
      if (!field) return;
      const out = field.value.length;
      field.value = words;
      caret.current = words.length;
      held.current = words.length;
      about.current = null;
      edited({ at: 0, out, into: words.length, holds: words.length });
      setLength(words.length);
      setSaid(null);
      onTyped?.();
      field.focus();
    },
    [edited, onTyped],
  );

  useImperativeHandle(
    ref,
    () => ({
      text: () => added(box.current?.value ?? "", { to: from }),
      select({ start, end }) {
        const field = box.current;
        if (!field) return;
        // A browser brings the caret into sight when a box takes the focus, and does not
        // bring what is selected into sight at all: words that stood under the three lines
        // of the box were selected where nobody saw them. So the box is given its room, the
        // caret is put at the end of the words, the box takes the focus, and the words are
        // then selected back from there.
        flushSync(() => setTall(true));
        if (document.activeElement === field) field.blur();
        field.setSelectionRange(end + from, end + from);
        field.focus();
        field.setSelectionRange(start + from, end + from);
      },
      fill: put,
    }),
    [from, put],
  );
  // The box holds what the search has read as well as what is being added. The API takes so
  // much at a time, so what is counted is what would be sent.
  const unread = length - Math.min(read.to, length);
  const left = maxText - unread;
  const counting = left < COUNT_FROM;
  const problem =
    refusal ??
    (said === "empty"
      ? // It names the other way to say what is wanted, where that stands now.
        open
        ? PROMPT.emptyOpen
        : PROMPT.empty
      : said === "nothingNew"
        ? ADDED.nothingNew
        : said === "changed"
          ? ADDED.changed
          : null);
  // What is said of words that were sent, once they are read: the search has then read all
  // that the box holds. It is no fault, so it is not said as one.
  const readAll = length > 0 && read.to >= length;
  const note =
    problem !== null
      ? null
      : said === "stillRead" && reading
        ? SUGGEST.reading
        : said === "changedToo" && readAll
          ? ADDED.changedToo
          : said === "full"
            ? PROMPT.full(maxText)
            : apart
              ? ADDED.apart
              : null;

  /**
   * How far the search has read into the box as it stands. A box that holds more or less
   * than it last said was changed and did not say so, as by a tool that fills it in: where,
   * nobody knows, and the search is told that much.
   */
  const readOf = (text: string) => {
    if (text.length === held.current) return read;
    const unseen: Change = { at: null, out: held.current, into: text.length, holds: text.length };
    held.current = text.length;
    edited(unseen);
    return moved(read, unseen);
  };

  /** Words are copied, cut or dragged from the box. Where they began and how many they were is kept, and no word of them. */
  const lift = (field: HTMLTextAreaElement) => {
    const from = field.selectionStart;
    const many = field.selectionEnd - from;
    lifted.current = many > 0 ? { from, many, read: from < read.to } : null;
  };
  /**
   * True when so many characters, pasted now, are words that the search has read: as many
   * were taken from the box, from among what was read then or what has been read since.
   */
  const readBefore = (many: number) => {
    const taken = lifted.current;
    return taken !== null && taken.many === many && (taken.read || taken.from < read.to);
  };

  const send = () => {
    if (busy) return;
    const text = box.current?.value ?? "";
    if (text.trim() === "") {
      setSaid("empty");
      box.current?.focus();
      return;
    }
    // What is sent is what stands after the words the search has read. Where nothing does,
    // nothing is sent, and the box says why.
    const mark = readOf(text);
    const more = added(text, mark);
    if (more.trim() === "") {
      // While a model reads the words, they are being read: the box says so, and not that they were.
      setSaid(mark.changed ? "changed" : reading ? "stillRead" : "nothingNew");
      box.current?.focus();
      return;
    }
    setSaid(mark.changed ? "changedToo" : null);
    // The answer comes first: the box gives its room back, though the focus stays in it.
    setTall(false);
    // All that the box holds is now read or sent to be read, and so is what was copied from
    // it: the box may be changed before the answer comes, and the place never reach it.
    if (lifted.current !== null) lifted.current = { ...lifted.current, read: true };
    onSubmit(more);
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

  const startAgain = (event: MouseEvent<HTMLElement>) => {
    // Start again is drawn where Stop stood as soon as a reading has ended, so the second
    // press of a double press on Stop lands here, and the whole search was gone with all
    // that was set by hand. The browser counts the presses that follow one another in one
    // place, by what the person's own system takes for a double press: one that it counts
    // as the second, or as a later one, was aimed at what stood here before, and does
    // nothing. A press by keyboard is counted as none, and begins again as it did.
    if (event.detail > 1) return;
    put("");
    onStartAgain?.();
  };

  const described = [
    open ? null : `${id}-hint`,
    counting ? `${id}-count` : null,
    problem ? `${id}-problem` : null,
    note ? `${id}-note` : null,
  ]
    .filter(Boolean)
    .join(" ");

  // What a useful sentence holds, and one whole sentence as an example. All of it is said
  // of the box, so that whoever hears the page hears it as the box takes the focus.
  const helps = open ? null : (
    <div id={`${id}-hint`} className={styles.hint}>
      <p>{hint}</p>
      {example === null ? null : (
        <p>
          {PROMPT.forExample} <q>{example}</q>
        </p>
      )}
    </div>
  );
  // The order of the page is the order it is drawn in: where they are drawn under the
  // field, they come after it. The field has a place of its own, and is never drawn anew.
  const under = narrow && help === "under";

  return (
    <Frame kind={tall ? "box-on" : "box"} bare className={styles.prompt} data-open={open} data-help={help}>
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
        </div>
        {under ? null : helps}
        <div className={styles.line}>
          <textarea
            ref={box}
            id={`${id}-box`}
            className={`${styles.box} target`}
            rows={open ? 1 : 2}
            // What the search has read stays in the box, and takes none of the room for what is added.
            maxLength={read.to + maxText}
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
            // Where the caret stands is kept as a count, for a browser that does not say when a change begins.
            onSelect={(event) => {
              caret.current = event.currentTarget.selectionStart;
            }}
            onCopy={(event) => lift(event.currentTarget)}
            onCut={(event) => lift(event.currentTarget)}
            onDragStart={(event) => lift(event.currentTarget)}
            onInput={(event) => {
              const field = event.currentTarget;
              const kind = (event.nativeEvent as Partial<InputEvent>).inputType ?? "";
              const was = { start: about.current ?? caret.current, holds: held.current };
              const now = { start: field.selectionStart, end: field.selectionEnd, holds: field.value.length };
              const change = changeOf(was, now, howOf(kind));
              // What is pasted, and is as long as what was taken from among the words that
              // were read, is those words: they are not new, wherever they are put.
              const back = PASTED.has(kind) && readBefore(change.into);
              edited(back ? { ...change, how: "pasted" } : change);
              about.current = null;
              caret.current = field.selectionStart;
              held.current = now.holds;
              setLength(now.holds);
              // A browser cuts what is pasted or dropped at what the box takes, and says
              // nothing of it: 900 characters were pasted, and the search read 600 that
              // ended in the middle of a word. Where the box is filled so, it says that the
              // end may have been left out. What was pasted is not read to tell.
              setSaid(PASTED.has(kind) && now.holds >= read.to + maxText ? "full" : null);
              setTall(true);
              onTyped?.();
            }}
            onKeyDown={onKeyDown}
          />
          <div className={styles.buttons}>
            {/* One button in one place, which ends the reading while there is one and
                begins again once a search is open. */}
            {busy ? (
              <Press kind="stop" onPress={onStop}>
                {PROMPT.stop}
              </Press>
            ) : open && onStartAgain ? (
              <Press onPress={startAgain}>{PROMPT.startAgain}</Press>
            ) : null}
            {/* The one button of the box that is cobalt. While a sentence is read it is
                down, says that it is off, and keeps the focus. */}
            <Press kind="go" submits off={busy}>
              {busy ? PROMPT.reading : PROMPT.submit}
            </Press>
          </div>
        </div>
        {problem ? (
          <p id={`${id}-problem`} className={styles.problem} role="alert">
            {problem}
          </p>
        ) : null}
        {note ? (
          <p id={`${id}-note`} className={styles.note} role="status">
            {note}
          </p>
        ) : null}
      </form>

      {children}
      {/* What Burro says stands directly under the field. The sentences that help come after it. */}
      {under ? helps : null}
    </Frame>
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
 *
 * On the first screen they stand under the helper that offers one, which
 * says what they are. Their heading is then kept for whoever hears the page,
 * and is not drawn under the helper a second time.
 */
export function Examples({ onUse, examples = EXAMPLES }: ExamplesProps) {
  const id = useId();
  const under = useHelper();
  const headed = headedUnder(under, PROMPT.examplesTitle);
  // Where the data can answer no sentence of them, none is offered, and no heading over none.
  if (examples.length === 0) return null;
  return (
    <Frame
      kind="box"
      as="section"
      className={styles.examples}
      aria-labelledby={headed === "named" ? under?.by : `${id}-examples`}
      // What an example does is said once, of them all: said of each, it was heard three times.
      aria-describedby={`${id}-examples-hint`}
    >
      {headed === "named" ? null : (
        <h2 id={`${id}-examples`} className={headed === "heard" ? "visually-hidden" : styles.examplesTitle}>
          {PROMPT.examplesTitle}
        </h2>
      )}
      <p id={`${id}-examples-hint`} className={styles.hint}>
        {PROMPT.examplesHint}
      </p>
      {/* A menu, as the look draws one: the carrot lies beside the sentence in hand. */}
      <ul className={styles.list} style={CARROT}>
        {examples.map((example) => (
          <li key={example}>
            <button type="button" className={`${styles.example} target`} onClick={() => onUse(example)}>
              {example}
            </button>
          </li>
        ))}
      </ul>
    </Frame>
  );
}
