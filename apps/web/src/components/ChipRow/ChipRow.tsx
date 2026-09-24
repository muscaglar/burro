"use client";

import { useId, useRef, useState, type KeyboardEvent, type MouseEvent, type ReactNode } from "react";

import { COMBINE } from "@/content/labels";
import { CHIPS, PLACE, REJECTED } from "@/content/search";
import type {
  AreaSummary,
  InterpreterName,
  MetaData,
  Operations,
  PreferenceSpec,
  RejectReason,
  Tenure,
} from "@/lib/api/schema";
import { chipsOf, type Chip as ChipData } from "@/lib/search/chips";
import type { Assumed } from "@/lib/search/state";

import { BudgetControl } from "../SettingsPanel/BudgetControl";
import { CommuteControl, JourneySettings } from "../SettingsPanel/CommuteControl";
import { TenureChoice } from "../SettingsPanel/TenureChoice";
import { TagControl, WeightControl } from "../SettingsPanel/WeightControl";
import { Skeleton } from "../Skeleton/Skeleton";
import styles from "./ChipRow.module.css";

interface Props {
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
  /** True when the person said whether they rent or buy, in words or with a control. */
  readonly tenureSaid?: boolean;
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
 * What Burro understood, one chip for each thing. A chip opens the same
 * control the settings hold, in place, and can be removed where the setting
 * can be. A part nobody chose carries the word "assumed" and a dashed edge.
 *
 * Everything that explains the chips is drawn where it can be seen: the
 * heading, what "assumed" means, what the usual settings are, and why a
 * place is shown by number. None of it is for a screen reader alone.
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
  tenureSaid = false,
  id: rowId,
}: Props) {
  const id = useId();
  const [openKey, setOpenKey] = useState<string | null>(null);
  const chips = withWhichJourneyCounts(
    chipsOf(spec, meta, areas, placeNames, assumed, { tenure: tenureSaid }),
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
  const unnamed = spec.commutes.filter((commute) => placeNames[commute.place_id] === undefined).length;
  const hints = {
    assumed: chips.some((chip) => chip.assumed),
    usual: chips.some((chip) => chip.kind === "usual"),
    unnamed: unnamed > 0,
  };

  const editorOf = (chip: Drawn): ReactNode => {
    const problem = (() => {
      const reason = refused.get(chip.key);
      return reason === undefined ? null : REJECTED[reason];
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
        return tag ? <TagControl {...shared} tag={tag} weight={weight} problem={problem} /> : null;
      }
      case "journeys":
        return <JourneySettings {...shared} spec={spec} />;
      default:
        return null;
    }
  };

  return (
    // It can be given the focus by the page, as when a question is answered and goes, and
    // is no stop of its own.
    <section id={rowId} className={styles.row} aria-labelledby={`${id}-title`} tabIndex={-1}>
      <h2 id={`${id}-title`} className={styles.title}>
        {heading}
      </h2>
      {waiting ? (
        <div className={styles.chips} aria-hidden="true">
          <Skeleton shape="chip" />
          <Skeleton shape="chip" />
          <Skeleton shape="chip" />
        </div>
      ) : (
        <ul className={styles.chips}>
          {chips.map((chip) => (
            <Chip
              key={chip.key}
              chip={chip}
              open={openKey === chip.key}
              onToggle={(open) => setOpenKey(open ? chip.key : null)}
              onRemove={chip.removal ? () => onEdit(chip.removal as Operations) : undefined}
              onOpenSettings={onOpenSettings}
              describedBy={`${id}-usual`}
              editor={editorOf(chip)}
            />
          ))}
        </ul>
      )}
      {waiting || !(hints.assumed || hints.usual || hints.unnamed || readBy !== null) ? null : (
        <div className={styles.hints}>
          {hints.assumed ? <p>{CHIPS.assumedHint}</p> : null}
          {/* Beside the chip and not in it, so that it is said once, after the chip's name. */}
          {hints.usual ? (
            <p id={`${id}-usual`}>
              {CHIPS.usualHint} {CHIPS.openSettings}
            </p>
          ) : null}
          {/* The API gives a place's id and not its name (docs/design/web.md, section 13, gap 1). */}
          {hints.unnamed ? <p>{PLACE.unnamedHint(unnamed, spec.commutes.length)}</p> : null}
          {readBy !== null ? <p>{CHIPS.readBy[readBy]}</p> : null}
        </div>
      )}
    </section>
  );
}

interface ChipProps {
  readonly chip: Drawn;
  readonly open: boolean;
  readonly onToggle: (open: boolean) => void;
  readonly onRemove?: () => void;
  readonly onOpenSettings: () => void;
  /** The id of the line that says what the usual settings are, which describes their chip. */
  readonly describedBy?: string;
  /** The control the chip opens. `null` where it opens none. */
  readonly editor: ReactNode;
}

function Words({ chip }: { readonly chip: Drawn }) {
  const whole = chip.assumed && !chip.parts.some((part) => part.assumed);
  return (
    <span className={styles.words}>
      <span className={styles.label}>{chip.label}</span>
      {whole ? <span className={styles.assumed}> {CHIPS.assumed}</span> : null}
      {chip.parts.map((part) => (
        <span key={part.text} className={styles.part}>
          , {part.text}
          {part.assumed ? <span className={styles.assumed}> {CHIPS.assumed}</span> : null}
        </span>
      ))}
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

export function Chip({ chip, open, onToggle, onRemove, onOpenSettings, describedBy, editor }: ChipProps) {
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
            <Words chip={chip} />
          </button>
        ) : chip.kind === "usual" ? (
          <button
            type="button"
            className={`${styles.main} target`}
            data-main
            aria-describedby={describedBy}
            onClick={onOpenSettings}
          >
            <Words chip={chip} />
          </button>
        ) : (
          <span className={`${styles.main} ${styles.plain}`}>
            <Words chip={chip} />
          </span>
        )}
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
