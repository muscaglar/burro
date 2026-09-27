"use client";

import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
  type RefObject,
} from "react";

import { COMBINE } from "@/content/labels";
import { countsOf } from "@/content/crime";
import { CHIPS, whyRefused } from "@/content/search";
import type { Handed } from "@/lib/api/handed";
import type {
  AreaSummary,
  InterpreterName,
  MetaData,
  Operations,
  PreferenceSpec,
  RejectReason,
  Tenure,
} from "@/lib/api/schema";
import { chipsOf, endAskedFor, type Beside, type Chip as ChipData } from "@/lib/search/chips";
import { leadsOf } from "@/lib/search/leads";
import type { Assumed } from "@/lib/search/state";

import { Frame } from "../kit/Frame/Frame";
import { Label } from "../kit/Label/Label";
import { Press } from "../kit/Press/Press";
import type { ThingOf, ThingState } from "../kit/Thing/drawn";
import { BudgetControl } from "../SettingsPanel/BudgetControl";
import { CommuteControl, JourneySettings } from "../SettingsPanel/CommuteControl";
import { TenureChoice } from "../SettingsPanel/TenureChoice";
import { VibeControl } from "../SettingsPanel/VibeControl";
import { WeightControl } from "../SettingsPanel/WeightControl";
import { begun, following, landed, nowDrawn, settled, wasDrawn } from "./arrives";
import { ON_A_WIDE_SCREEN, stateOf, thingOf, type Art, type Drawn } from "./drawn";
import { inSight, lying, NARROW_REM, standing, type Laid } from "./rows";
import { inOneLine, saidBy, type Said } from "./says";
import styles from "./ChipRow.module.css";

/** How many chips stand in the row before the rest are asked for. */
export const SHOWN_AT_FIRST = 6;

interface Props extends Beside {
  /** The spec the API last returned. The chips are drawn from it, never from the edits. */
  readonly spec: PreferenceSpec;
  readonly assumed: Assumed;
  readonly placeNames: Readonly<Record<string, string>>;
  readonly meta: Handed;
  readonly areas: readonly AreaSummary[];
  readonly onEdit: (operations: Operations) => void;
  readonly onTenure: (tenure: Tenure) => void;
  readonly version: number;
  readonly refused?: ReadonlyMap<string, RejectReason>;
  /**
   * Who read the words, once words have been read. It says that words were read into the
   * search, and so what the chips are called. Who it was is said nowhere in the row.
   */
  readonly readBy?: InterpreterName | null;
  /** True while a sentence is being read and no chip can be drawn yet. */
  readonly waiting?: boolean;
  /** An id for the row, so that the page can give it the focus. */
  readonly id?: string;
  /**
   * How large a chip is drawn on a wide screen. The page asks for them small where what
   * stands over the answer must give way, as where a question stands over the chips. Left
   * out, as the look has chosen.
   */
  readonly art?: Art;
}

const notChosen = (from: PreferenceSpec["commute_combine_from"]) => from === "default" || from === "inferred";

/** The row while it holds the place of chips that are on their way: it has drawn none. */
const NO_CHIPS: readonly string[] = [];

/**
 * The chips of the search, with the one that says which journey counts after
 * the places, once there are two of them. With one place there is nothing to
 * choose between. With two, only one journey feeds the fit unless the person
 * says otherwise, and until they do the chip is marked "assumed".
 *
 * That one is drawn here and not among the search's own because it is for the
 * eye alone: a stored search that is shown as chips says nothing of it.
 */
function withWhichJourneyCounts(chips: readonly ChipData[], spec: PreferenceSpec): readonly Drawn[] {
  if (spec.commutes.length < 2) return chips;
  const after = chips.reduce((last, chip, at) => (chip.kind === "place" ? at : last), -1);
  const which: Drawn = {
    key: "journeys",
    kind: "journeys",
    id: null,
    label: COMBINE[spec.commute_combine] ?? "",
    parts: [],
    assumed: notChosen(spec.commute_combine_from),
    removal: null,
    turn: null,
  };
  // A choice the website has no word for is left out.
  if (which.label === "") return chips;
  return [...chips.slice(0, after + 1), which, ...chips.slice(after + 1)];
}

/** How wide the row is, in whole pixels, and whether that is narrow. Nought where nothing was laid out. */
interface Width {
  readonly narrow: boolean;
  readonly wide: number;
}

const NOT_LAID_OUT: Width = { narrow: false, wide: 0 };

/**
 * How wide the row is, and whether it is narrow: as wide as the style sheet lays a narrow
 * row out by, or narrower. It is measured once the row is on the page and before the page
 * is drawn, so that the chips are first seen as they will stand, and again when the row is
 * made wider or narrower. A browser that lays nothing out measures nothing, and the row is
 * then taken to be wide.
 */
function useWidth(row: RefObject<HTMLElement | null>): Width {
  const [width, setWidth] = useState<Width>(NOT_LAID_OUT);
  useLayoutEffect(() => {
    const measured = row.current;
    if (measured === null) return;
    const measure = () => {
      const wide = Math.round(measured.getBoundingClientRect().width);
      const rem = Number.parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
      const narrow = wide > 0 && wide <= NARROW_REM * rem;
      setWidth((was) => (was.narrow === narrow && was.wide === wide ? was : { narrow, wide }));
    };
    measure();
    if (typeof ResizeObserver !== "function") return;
    const watched = new ResizeObserver(measure);
    watched.observe(measured);
    return () => watched.disconnect();
  }, [row]);
  return width;
}

/** How many of the chips of a row stand in sight, for the chips and the width it was measured of. */
interface Stands {
  readonly of: string;
  readonly count: number;
}

/**
 * How many of the first chips stand in sight on a wide row, or `null` while that is not
 * known, when every one of them is drawn. The row is drawn with all of them, and read
 * before the page is drawn: where they stand in more rows than the answer leaves room
 * for, those of the first rows are drawn and the rest waits with what is over six. So
 * the rows that fold are never seen unfolded.
 *
 * It is read again when the search holds other chips, when what a chip says changes and
 * when the row is made wider or narrower, and not while the row is opened out, which
 * draws every chip. A browser that lays nothing out says that every chip stands at nought,
 * and nothing is folded there.
 */
function useStanding(chips: RefObject<HTMLElement | null>, of: string, reads: boolean): number | null {
  const [stands, setStands] = useState<Stands | null>(null);
  const known = stands !== null && stands.of === of;
  useLayoutEffect(() => {
    if (!reads || known) return;
    const read = () => {
      const laid = chips.current;
      if (laid === null) return;
      const tops = [...laid.children].map((chip) => (chip instanceof HTMLElement ? chip.offsetTop : 0));
      setStands({ of, count: standing(tops) });
    };
    read();
  }, [chips, of, reads, known]);
  // What was read of the row holds while it stands opened out: how many chips were folded
  // is what its button folds again. Read while it is opened out, nothing is: every chip is
  // then drawn, and in full.
  return known ? stands.count : null;
}

/** True when the spec is one of the two a search starts from, as the API served them. */
function isWhereASearchStarts(spec: PreferenceSpec, defaults: MetaData["defaults"]): boolean {
  const start = defaults[spec.tenure];
  return spec === start || JSON.stringify(spec) === JSON.stringify(start);
}

/**
 * What Burro understood, one chip for each thing a person asked for, and one
 * for renting or buying. What was asked for by way of character stands first.
 * The settings nobody chose have no chip. The chips wrap, so that none is cut
 * off or scrolled out of sight, and each is said in short until the row is
 * opened out. A chip opens the same control the settings hold, in place, and
 * can be removed where the setting can be. A part nobody chose carries the
 * word "assumed", and its chip has the solid edge every chip has. A chip of a
 * scale says which end is asked for, and "Turn" asks for the other.
 *
 * A chip is drawn as the look draws one: the small drawing of its thing, its
 * words, and a cross that takes it off. One that has this moment been added
 * drops into its place, once. Each part of the row brings the ground it is
 * read on, so the row reads on the grass as it does in a box.
 *
 * On a narrow row, as on a phone, the chips of a search of many things fold
 * to two rows and a button that opens the rest, which says how many it holds:
 * the answer comes first, and the first result is whole on the first screen.
 * On a wide row they fold so where they stand in more than three rows, so that
 * the first result is in sight. What is folded is one press away, and nothing
 * of it is lost.
 *
 * That button is one button on a row of any width. It stands on the line of
 * the heading, over the chips, so that it is where it was once they are
 * opened out: nothing that opens stands over it. It is of one size whichever
 * it says, keeps the focus, and folds the chips again. Where nothing is left
 * to fold as it does, it goes, and hands the focus to the row.
 *
 * Everything that explains the chips is drawn where it can be seen, once the
 * row is opened out: what "assumed" means, and what counts for most.
 *
 * Who read the words is not said here. Who reads what is typed is said on the
 * page of methods, which the foot of every page leads to.
 */
export function ChipRow({
  spec,
  assumed,
  placeNames,
  meta,
  areas,
  onEdit,
  onTenure,
  version,
  refused = new Map(),
  readBy = null,
  waiting = false,
  tenurePicked = false,
  quoted = {},
  id: rowId,
  art = ON_A_WIDE_SCREEN,
}: Props) {
  const id = useId();
  const section = useRef<HTMLElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const { narrow, wide } = useWidth(section);
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [all, setAll] = useState(false);
  const chips = withWhichJourneyCounts(
    chipsOf(spec, meta, areas, placeNames, assumed, { tenurePicked, quoted }),
    spec,
  );

  // Which chips have this moment been added. The row holds what it last drew, and what
  // it draws now is held against that before anything is drawn, so that a chip is new
  // from the first moment it is seen.
  const keys = waiting ? NO_CHIPS : chips.map((chip) => chip.key);
  const [last, setLast] = useState(() => begun(keys, waiting || wasDrawn(spec)));
  const row = following(last, keys);
  if (row !== last) setLast(row);
  useEffect(() => {
    if (!waiting) nowDrawn(spec);
  }, [spec, waiting]);
  /** A press was made in the row: nothing in it is new, whether or not it was seen to drop. */
  const settle = () => setLast(settled);

  const shared = { limits: meta.limits, onEdit, version };
  // Before anything has changed the search, the chips are what a search starts from and
  // were understood from nothing. So are they after words that were read into nothing.
  const heading = waiting
    ? CHIPS.label
    : isWhereASearchStarts(spec, meta.defaults)
      ? CHIPS.startLabel
      : readBy !== null
        ? CHIPS.label
        : CHIPS.setLabel;
  // A chip that is open is drawn in full, with its control under it, so the row is opened out
  // for it. Until the person opens the row or a chip of it, the chips are said in short,
  // however few they are: the answer comes first.
  const out = all || openKey !== null;
  /** What "Turn" says it will do: the name of the vibe, and the end it would ask for. */
  const turnOf = (chip: Drawn): string | null => {
    if (chip.turn === null) return null;
    const tag = meta.tags.find((one) => one.tag_id === chip.id);
    const weight = spec.tags.find((one) => one.tag_id === chip.id);
    if (tag === undefined || weight === undefined) return null;
    const other = endAskedFor(tag, weight.toward === "low" ? "high" : "low");
    return other === null ? null : CHIPS.turnTo(tag.label, other);
  };

  /** What says how much room a chip takes where the row is narrow: its words, in full or in short, and its buttons. */
  const sized = (chip: Drawn, full: boolean, alone = false) => ({
    words: inOneLine(saidBy(chip, full)),
    cross: chip.removal !== null,
    turn: turnOf(chip) !== null,
    alone,
  });
  // In the row stand the first six of what the search holds. What is over six waits to be asked for.
  const six = chips.slice(0, SHOWN_AT_FIRST);
  // On a narrow row those stand in rows of one and of two, and with more rows than the
  // answer leaves room for, the first rows of them stand and the rest waits with what is
  // over six. They are counted as they lie in short, with none of them open.
  // On a wide row they stand as they fall, as many to a row as fit, so how they lie is read
  // from the row once it is laid out: of what each of the six says, at the width there is.
  const laidAs = `${wide} ${six.map((chip) => `${chip.key} ${inOneLine(saidBy(chip, false))}`).join(" | ")}`;
  const reads = !narrow && !out && !waiting && wide > 0;
  const stands = useStanding(list, laidAs, reads);
  // True of a wide row that is drawn to be read, and is not yet: nobody sees it so.
  const measuring = reads && stands === null;
  const atFirst = narrow
    ? six.slice(0, inSight(lying(six.map((chip) => sized(chip, false)))))
    : six.slice(0, stands ?? six.length);
  const more = chips.length - atFirst.length;
  const shown = out ? chips : atFirst;
  // The button that opens the rest is there while something is folded, and while the row
  // stands opened out by it: what it opened, it folds again. It stays while the row is
  // read, so that it is the button it was, with the focus it had, once the row is folded.
  const folds = more > 0 || all || measuring;
  const rest = useRef<HTMLButtonElement>(null);
  // True from the press that folds the row again until the row is drawn folded.
  const folding = useRef(false);
  useLayoutEffect(() => {
    if (!folding.current || measuring) return;
    folding.current = false;
    // Nothing was left to fold, and the button went with the press: the focus goes to the row.
    if (rest.current === null) section.current?.focus({ preventScroll: true });
  });
  const hints = {
    assumed: chips.some((chip) => chip.assumed),
    // Where a journey or a budget counts for more than what was asked of the place.
    leads: leadsOf(spec) !== null,
  };
  const explained = out && (hints.assumed || hints.leads);

  const editorOf = (chip: Drawn): ReactNode => {
    const problem = (() => {
      const reason = refused.get(chip.key);
      return reason === undefined ? null : whyRefused(reason, meta);
    })();
    switch (chip.kind) {
      case "tenure":
        return <TenureChoice tenure={spec.tenure} onChoose={onTenure} version={version} problem={problem} />;
      case "budget":
        return <BudgetControl {...shared} budget={spec.budget} tenure={spec.tenure} problem={problem} />;
      case "place": {
        const commute = spec.commutes.find((one) => one.place_id === chip.id);
        return commute ? (
          <CommuteControl {...shared} commute={commute} name={chip.label} problem={problem} />
        ) : null;
      }
      case "feature": {
        const metric = meta.features.find((one) => one.feature_id === chip.id);
        const weight = spec.weights.find((one) => one.feature_id === chip.id);
        return metric ? <WeightControl {...shared} metric={metric} weight={weight} problem={problem} /> : null;
      }
      case "tag": {
        const tag = meta.tags.find((one) => one.tag_id === chip.id);
        const weight = spec.tags.find((one) => one.tag_id === chip.id);
        return tag ? (
          <VibeControl
            {...shared}
            tag={tag}
            weight={weight}
            problem={problem}
            crime={countsOf(tag, meta.features)}
          />
        ) : null;
      }
      case "journeys":
        return <JourneySettings {...shared} spec={spec} />;
      default:
        return null;
    }
  };

  // Where the row is narrow, how each of the chips in sight lies: two to a row, or alone.
  const laid = lying(shown.map((chip) => sized(chip, out, openKey === chip.key)));

  return (
    // It can be given the focus by the page, as when a question is answered and goes, and
    // is no stop of its own.
    <section
      ref={section}
      id={rowId}
      className={styles.row}
      data-art={art}
      aria-labelledby={`${id}-title`}
      tabIndex={-1}
    >
      <div className={styles.top}>
        <p className={styles.heading}>
          <span id={`${id}-title`} className={styles.title} role="heading" aria-level={2}>
            {heading}
          </span>
        </p>
        {folds && !waiting ? (
          <Press
            ref={rest}
            className={styles.rest}
            reads
            expanded={out}
            controls={`${id}-chips`}
            // While a chip is open the row is opened out for it, and this button does nothing.
            off={openKey !== null}
            onPress={() => {
              settle();
              folding.current = all;
              setAll(!all);
            }}
          >
            {/* It holds the room of both of the things it says, so that it is of one size
                under the press. The one it does not say is not drawn, and is not heard. */}
            <span className={styles.says}>
              <span className={styles.said} data-said={!out} aria-hidden={out ? true : undefined}>
                {CHIPS.rest(more)}
              </span>
              <span className={styles.said} data-said={out} aria-hidden={out ? undefined : true}>
                {CHIPS.showFewer}
              </span>
            </span>
          </Press>
        ) : null}
      </div>
      {waiting ? (
        // What holds the place of a chip is the row's own, within a solid edge. It bears the
        // mark of everything that holds a place, by which the page knows that something is on its way.
        <div className={styles.holding} aria-hidden="true">
          <span className={`skeleton ${styles.held}`} />
          <span className={`skeleton ${styles.held}`} />
          <span className={`skeleton ${styles.held}`} />
        </div>
      ) : (
        <div className={styles.line} data-out={out}>
          <ul ref={list} id={`${id}-chips`} className={styles.chips}>
            {shown.map((chip, at) => (
              <Chip
                key={chip.key}
                chip={chip}
                thing={thingOf(chip, meta)}
                state={stateOf(chip, spec)}
                full={out}
                open={openKey === chip.key}
                onToggle={(open) => {
                  settle();
                  setOpenKey(open ? chip.key : null);
                }}
                onRemove={chip.removal ? () => onEdit(chip.removal as Operations) : undefined}
                onTurn={chip.turn ? () => onEdit(chip.turn as Operations) : undefined}
                turnName={turnOf(chip)}
                editor={editorOf(chip)}
                arrives={row.fresh.has(chip.key)}
                onArrived={() => setLast((was) => landed(was, chip.key))}
                laid={laid[at]}
              />
            ))}
          </ul>
        </div>
      )}
      {waiting || !explained ? null : (
        <div className={styles.notes}>
          <div className={styles.hints}>
            {hints.leads ? <p>{CHIPS.leadsHint}</p> : null}
            {hints.assumed ? <p>{CHIPS.assumedHint}</p> : null}
          </div>
        </div>
      )}
    </section>
  );
}

interface ChipProps {
  readonly chip: Drawn;
  /** The thing the chip is of, which is drawn beside its words. Left out, it is drawn by its kind. */
  readonly thing?: ThingOf;
  /** Whether a person said it, nobody did, or it counts for nothing. The words of the chip say it. */
  readonly state?: ThingState;
  /** True where the chip says every part of itself. In the row it says what was said, and that the rest was assumed. */
  readonly full?: boolean;
  readonly open: boolean;
  readonly onToggle: (open: boolean) => void;
  readonly onRemove?: () => void;
  /** Asks for the other end of a scale. Left out for a chip that is of no scale. */
  readonly onTurn?: () => void;
  readonly turnName?: string | null;
  /** The control the chip opens. `null` where it opens none. */
  readonly editor: ReactNode;
  /** True of a chip that has this moment been added: it drops into its place, once. */
  readonly arrives?: boolean;
  /** Told when it has dropped into its place. */
  readonly onArrived?: () => void;
  /** How it lies where the row is narrow. Left out, it has the row. */
  readonly laid?: Laid;
}

/** A chip that has a row to itself, where nothing says how it lies. */
const ALONE: Laid = { lies: "alone", beside: 0, letters: 0, row: 1 };

function Words({ said }: { readonly said: Said }) {
  return (
    <span className={styles.words}>
      <span className={styles.label}>{said.label}</span>
      {said.whole ? <span className={styles.assumed}> {CHIPS.assumed}</span> : null}
      {said.parts.map((part) => (
        <span key={part.text} className={styles.part}>
          , {part.text}
          {part.assumed ? <span className={styles.assumed}> {CHIPS.assumed}</span> : null}
        </span>
      ))}
      {said.rest ? <span className={styles.assumed}>, {CHIPS.restAssumed}</span> : null}
    </span>
  );
}

/**
 * The chip to give the focus to when this one is removed: the next one along that has a
 * button of its own, or else the one before. The button that was pressed goes with its
 * chip when the answer comes, and the focus must not go with it.
 */
function besideOf(item: HTMLElement | null): HTMLElement | null {
  const all = [...(item?.parentElement?.children ?? [])];
  const at = item === null ? -1 : all.indexOf(item);
  if (at < 0) return null;
  const inTurn = [...all.slice(at + 1), ...all.slice(0, at).reverse()];
  for (const other of inTurn) {
    const main = other.querySelector<HTMLElement>("button[data-main]");
    if (main) return main;
  }
  return item?.closest<HTMLElement>("section") ?? null;
}

export function Chip({
  chip,
  thing = thingOf(chip, { tags: [], features: [] }),
  state = chip.assumed ? "assumed" : "said",
  full = true,
  open,
  onToggle,
  onRemove,
  onTurn,
  turnName = null,
  editor,
  arrives = false,
  onArrived,
  laid = ALONE,
}: ChipProps) {
  const id = useId();
  const item = useRef<HTMLLIElement>(null);
  const button = useRef<HTMLButtonElement | null>(null);
  const opens = editor !== null;

  /**
   * The button the chip is pressed by. It bears a mark, by which the chip beside one that
   * goes is found, and by which a test tells the words of a chip from what it opens to.
   */
  const main = useCallback((pressed: HTMLButtonElement | null) => {
    button.current = pressed;
    pressed?.setAttribute("data-main", "");
  }, []);

  const remove = () => {
    besideOf(item.current)?.focus();
    onRemove?.();
  };

  // A chip may go while the focus is in what it opened, as when its slider is brought to
  // nought. It is asked as the chip is taken away, while it still stands in the row: the
  // focus goes to the chip beside it, and is never left on nothing. The page is not moved.
  useLayoutEffect(() => {
    const chipItself = item.current;
    return () => {
      if (chipItself?.contains(document.activeElement)) besideOf(chipItself)?.focus({ preventScroll: true });
    };
  }, []);

  const onKeyDown = (event: KeyboardEvent<HTMLLIElement>) => {
    if (event.key !== "Escape" || !open) return;
    event.stopPropagation();
    onToggle(false);
    button.current?.focus();
  };

  /** What a press on the words of the chip does: it opens its control, or is no press at all. */
  const pressed = opens ? { onOpen: () => onToggle(!open), open, controls: `${id}-editor` } : {};

  return (
    // Escape is heard here for the control the chip holds: the buttons are the controls.
    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
    <li
      ref={item}
      className={styles.chip}
      data-assumed={chip.assumed}
      data-open={open}
      data-lies={laid.lies}
      // What a chip that gives way is never made narrower than: its buttons, and its words on two lines.
      style={laid.lies === "gives" ? ({ "--beside": laid.beside, "--letters": laid.letters } as CSSProperties) : undefined}
      onKeyDown={onKeyDown}
      // The part that draws the chip says when it has dropped, from inside it.
      onAnimationEnd={arrives ? onArrived : undefined}
    >
      <span className={styles.head}>
        <Label
          ref={main}
          thing={thing}
          says={<Words said={saidBy(chip, full)} />}
          state={state}
          // The words of a chip say which part nobody chose, and that it counts for nothing.
          stateSaid
          named={chip.label}
          {...pressed}
          onTakeOff={onRemove ? remove : undefined}
          beside={
            onTurn && turnName !== null ? (
              <button type="button" className={`${styles.turn} target`} aria-label={turnName} onClick={onTurn}>
                {CHIPS.turn}
              </button>
            ) : undefined
          }
          arrives={arrives}
        />
      </span>
      {opens ? (
        <Frame kind="box-on" id={`${id}-editor`} className={styles.editor} hidden={!open}>
          {open ? editor : null}
        </Frame>
      ) : null}
    </li>
  );
}
