"use client";

import { useId, useRef, useState, type KeyboardEvent, type MouseEvent, type ReactNode } from "react";

import { COMBINE } from "@/content/labels";
import { countsOf } from "@/content/crime";
import { CHIPS, whyRefused } from "@/content/search";
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

import { BudgetControl } from "../SettingsPanel/BudgetControl";
import { CommuteControl, JourneySettings } from "../SettingsPanel/CommuteControl";
import { TenureChoice } from "../SettingsPanel/TenureChoice";
import { VibeControl } from "../SettingsPanel/VibeControl";
import { WeightControl } from "../SettingsPanel/WeightControl";
import { Skeleton } from "../Skeleton/Skeleton";
import styles from "./ChipRow.module.css";

/**
 * How many chips of what was asked for stand in the row before the rest are asked for. The
 * usual settings are not counted among them: they stand last, whatever else does.
 */
export const SHOWN_AT_FIRST = 6;

interface Props extends Beside {
  /** The spec the API last returned. The chips are drawn from it, never from the edits. */
  readonly spec: PreferenceSpec;
  readonly assumed: Assumed;
  readonly placeNames: Readonly<Record<string, string>>;
  readonly meta: MetaData;
  readonly areas: readonly AreaSummary[];
  readonly onEdit: (operations: Operations) => void;
  readonly onTenure: (tenure: Tenure) => void;
  readonly onOpenSettings: () => void;
  readonly version: number;
  readonly refused?: ReadonlyMap<string, RejectReason>;
  /** Who read the words, once words have been read. */
  readonly readBy?: InterpreterName | null;
  /** True while a sentence is being read and no chip can be drawn yet. */
  readonly waiting?: boolean;
  /** An id for the row, so that the page can give it the focus. */
  readonly id?: string;
}

/**
 * A chip as the row draws it: one of the search's own, or the one that says
 * which journey counts. That one is drawn here and not among the search's own
 * because it is for the eye alone: a stored search that is shown as chips
 * says nothing of it.
 */
type Drawn = Omit<ChipData, "kind"> & { readonly kind: ChipData["kind"] | "journeys" };

const notChosen = (from: PreferenceSpec["commute_combine_from"]) => from === "default" || from === "inferred";

/**
 * The chips of the search, with the one that says which journey counts after
 * the places, once there are two of them. With one place there is nothing to
 * choose between. With two, only one journey feeds the fit unless the person
 * says otherwise, and until they do the chip is marked "assumed".
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

/** True when the spec is one of the two a search starts from, as the API served them. */
function isWhereASearchStarts(spec: PreferenceSpec, defaults: MetaData["defaults"]): boolean {
  const start = defaults[spec.tenure];
  return spec === start || JSON.stringify(spec) === JSON.stringify(start);
}

/**
 * What Burro understood, one chip for each thing. What was asked for by way
 * of character stands first, and the settings nobody chose last. The chips
 * wrap, so that none is cut off or scrolled out of sight, and each is said in
 * short until the row is opened out. A chip opens the same control the
 * settings hold, in place, and can be removed where the setting can be. A
 * part nobody chose carries the word "assumed" and a dashed edge. A chip of a
 * scale says which end is asked for, and "Turn" asks for the other.
 *
 * Everything that explains the chips is drawn where it can be seen, once the
 * row is opened out: what "assumed" means, and what the usual settings are.
 * Who read the words is said in the heading, always.
 */
export function ChipRow({
  spec,
  assumed,
  placeNames,
  meta,
  areas,
  onEdit,
  onTenure,
  onOpenSettings,
  version,
  refused = new Map(),
  readBy = null,
  waiting = false,
  tenurePicked = false,
  quoted = {},
  id: rowId,
}: Props) {
  const id = useId();
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [all, setAll] = useState(false);
  const chips = withWhichJourneyCounts(
    chipsOf(spec, meta, areas, placeNames, assumed, { tenurePicked, quoted }),
    spec,
  );
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
  // In the row stand the first six of what the search holds, and then the usual settings,
  // which are last and are not counted. What is over six waits to be asked for.
  const asked = chips.filter((chip) => chip.kind !== "usual");
  const more = Math.max(0, asked.length - SHOWN_AT_FIRST);
  const shown = out
    ? chips
    : [...asked.slice(0, SHOWN_AT_FIRST), ...chips.filter((chip) => chip.kind === "usual")];
  const hints = {
    assumed: chips.some((chip) => chip.assumed),
    usual: chips.some((chip) => chip.kind === "usual"),
    // Where a journey or a budget counts for more than what was asked of the place.
    leads: leadsOf(spec) !== null,
  };

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

  /** What "Turn" says it will do: the name of the vibe, and the end it would ask for. */
  const turnOf = (chip: Drawn): string | null => {
    if (chip.turn === null) return null;
    const tag = meta.tags.find((one) => one.tag_id === chip.id);
    const weight = spec.tags.find((one) => one.tag_id === chip.id);
    if (tag === undefined || weight === undefined) return null;
    const other = endAskedFor(tag, weight.toward === "low" ? "high" : "low");
    return other === null ? null : CHIPS.turnTo(tag.label, other);
  };

  return (
    // It can be given the focus by the page, as when a question is answered and goes, and
    // is no stop of its own.
    <section id={rowId} className={styles.row} aria-labelledby={`${id}-title`} tabIndex={-1}>
      <p className={styles.heading}>
        <span id={`${id}-title`} className={styles.title} role="heading" aria-level={2}>
          {heading}
        </span>
        {!waiting && readBy !== null ? <span className={styles.readBy}> {CHIPS.readBy[readBy]}</span> : null}
      </p>
      {waiting ? (
        <div className={styles.chips} aria-hidden="true">
          <Skeleton shape="chip" />
          <Skeleton shape="chip" />
          <Skeleton shape="chip" />
        </div>
      ) : (
        <div className={styles.line} data-out={out}>
          <ul className={styles.chips}>
            {shown.map((chip) => (
              <Chip
                key={chip.key}
                chip={chip}
                full={out}
                open={openKey === chip.key}
                onToggle={(open) => setOpenKey(open ? chip.key : null)}
                onRemove={chip.removal ? () => onEdit(chip.removal as Operations) : undefined}
                onTurn={chip.turn ? () => onEdit(chip.turn as Operations) : undefined}
                turnName={turnOf(chip)}
                onOpenSettings={onOpenSettings}
                describedBy={out && hints.usual ? `${id}-usual` : undefined}
                editor={editorOf(chip)}
              />
            ))}
          </ul>
          {more > 0 ? (
            <button
              type="button"
              className={`${styles.rest} target`}
              aria-expanded={out}
              // While a chip is open the row is opened out for it, and this button does nothing.
              aria-disabled={openKey !== null ? true : undefined}
              onClick={() => (openKey === null ? setAll(!all) : undefined)}
            >
              {out ? CHIPS.showFewer : CHIPS.rest(more)}
            </button>
          ) : null}
        </div>
      )}
      {waiting || !out || !(hints.assumed || hints.usual || hints.leads) ? null : (
        <div className={styles.hints}>
          {hints.leads ? <p>{CHIPS.leadsHint}</p> : null}
          {hints.assumed ? <p>{CHIPS.assumedHint}</p> : null}
          {/* Beside the chip and not in it, so that it is said once, after the chip's name. */}
          {hints.usual ? (
            <p id={`${id}-usual`}>
              {CHIPS.usualHint} {CHIPS.openSettings}
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}

interface ChipProps {
  readonly chip: Drawn;
  /** True where the chip says every part of itself. In the row it says what was said, and that the rest was assumed. */
  readonly full?: boolean;
  readonly open: boolean;
  readonly onToggle: (open: boolean) => void;
  readonly onRemove?: () => void;
  /** Asks for the other end of a scale. Left out for a chip that is of no scale. */
  readonly onTurn?: () => void;
  readonly turnName?: string | null;
  readonly onOpenSettings: () => void;
  /** The id of the line that says what the usual settings are, which describes their chip. */
  readonly describedBy?: string;
  /** The control the chip opens. `null` where it opens none. */
  readonly editor: ReactNode;
}

function Words({ chip, full }: { readonly chip: Drawn; readonly full: boolean }) {
  const some = chip.parts.some((part) => part.assumed);
  const whole = chip.assumed && !some;
  // In the row a chip says what was said, and says once that the rest was assumed. A word
  // that was read one way of two is said in the row as well.
  const unsaid = chip.parts.filter((part) => part.assumed && part.always !== true);
  // One part that nobody said is named, with the word "assumed" on it and on nothing else:
  // "rest assumed" stood beside the very words the person typed, and read as if they were.
  const named = !full && unsaid.length === 1;
  const parts = full || named ? chip.parts : chip.parts.filter((part) => !part.assumed || part.always === true);
  const rest = !named && unsaid.length > 0;
  return (
    <span className={styles.words}>
      <span className={styles.label}>{chip.label}</span>
      {whole ? <span className={styles.assumed}> {CHIPS.assumed}</span> : null}
      {parts.map((part) => (
        <span key={part.text} className={styles.part}>
          , {part.text}
          {part.assumed ? <span className={styles.assumed}> {CHIPS.assumed}</span> : null}
        </span>
      ))}
      {!full && rest ? <span className={styles.assumed}>, {CHIPS.restAssumed}</span> : null}
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
  full = true,
  open,
  onToggle,
  onRemove,
  onTurn,
  turnName = null,
  onOpenSettings,
  describedBy,
  editor,
}: ChipProps) {
  const id = useId();
  const button = useRef<HTMLButtonElement>(null);
  const opens = editor !== null;

  const remove = (event: MouseEvent<HTMLButtonElement>) => {
    besideOf(event.currentTarget.closest("li"))?.focus();
    onRemove?.();
  };

  const onKeyDown = (event: KeyboardEvent<HTMLLIElement>) => {
    if (event.key !== "Escape" || !open) return;
    event.stopPropagation();
    onToggle(false);
    button.current?.focus();
  };

  return (
    // Escape is heard here for the control the chip holds: the buttons are the controls.
    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
    <li
      className={styles.chip}
      data-assumed={chip.assumed}
      data-open={open}
      onKeyDown={onKeyDown}
    >
      <div className={styles.head}>
        {opens ? (
          <button
            ref={button}
            type="button"
            className={`${styles.main} target`}
            data-main
            aria-expanded={open}
            aria-controls={`${id}-editor`}
            onClick={() => onToggle(!open)}
          >
            <Words chip={chip} full={full} />
          </button>
        ) : chip.kind === "usual" ? (
          <button
            type="button"
            className={`${styles.main} target`}
            data-main
            aria-describedby={describedBy}
            onClick={onOpenSettings}
          >
            <Words chip={chip} full={full} />
          </button>
        ) : (
          <span className={`${styles.main} ${styles.plain}`}>
            <Words chip={chip} full={full} />
          </span>
        )}
        {onTurn && turnName !== null ? (
          <button type="button" className={`${styles.turn} target`} aria-label={turnName} onClick={onTurn}>
            {CHIPS.turn}
          </button>
        ) : null}
        {onRemove ? (
          <button
            type="button"
            className={`${styles.remove} target`}
            aria-label={`${CHIPS.remove}: ${chip.label}`}
            onClick={remove}
          >
            <span aria-hidden="true">×</span>
          </button>
        ) : null}
      </div>
      {opens ? (
        <div id={`${id}-editor`} className={styles.editor} hidden={!open}>
          {open ? editor : null}
        </div>
      ) : null}
    </li>
  );
}
