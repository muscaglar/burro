"use client";

import { useId } from "react";

import { SEGMENT } from "@/content/labels";
import { BUDGET, SEGMENTS } from "@/content/settings";
import type { Budget, Operations, ServedLimits, Tenure } from "@/lib/api/schema";
import { grouped } from "@/lib/format";
import { useDraft } from "@/lib/search/draft";
import { edits } from "@/lib/search/edits";

import { NumberStepper } from "../NumberStepper/NumberStepper";
import { WeightSlider } from "../WeightSlider/WeightSlider";
import { Check } from "./fields";
import styles from "./SettingsPanel.module.css";

interface Props {
  readonly budget: Budget;
  readonly tenure: Tenure;
  readonly limits: ServedLimits;
  readonly onEdit: (operations: Operations) => void;
  readonly version: number;
  /** Why the last edit to the budget was not taken, in words. */
  readonly problem?: string | null;
  /**
   * False where the data holds no cost to test a budget against. No amount is then asked
   * for: set, it was turned away, and once it left no area ranked. The kind of home can
   * still be chosen, which a search holds with or without an amount.
   */
  readonly costs?: boolean;
}

/** What a person can pay, for what kind of home, and how much that counts. */
export function BudgetControl({
  budget,
  tenure,
  limits,
  onEdit,
  version,
  problem = null,
  costs = true,
}: Props) {
  const id = useId();
  const money = limits[tenure];
  const [segment, showSegment] = useDraft(budget.segment, version);
  const [firm, showFirm] = useDraft(budget.strictness === "hard", version);
  const kinds = SEGMENTS[tenure];

  return (
    <fieldset className={styles.group}>
      <legend className={styles.groupLegend}>{BUDGET.legend}</legend>
      {costs ? null : <p className={styles.hint}>{BUDGET.notInData}</p>}
      {costs ? (
        <Amount budget={budget} tenure={tenure} money={money} problem={problem} onEdit={onEdit} version={version} />
      ) : null}
      <div className={styles.field}>
        <label className={styles.label} htmlFor={`${id}-segment`}>
          {BUDGET.segment}
        </label>
        <select
          id={`${id}-segment`}
          className="target"
          value={kinds.includes(segment) ? segment : ""}
          onChange={(event) => {
            const chosen = kinds.find((kind) => kind === event.currentTarget.value);
            if (chosen === undefined) return;
            showSegment(chosen);
            onEdit(edits.budgetSegment(chosen));
          }}
        >
          {kinds.map((kind) => (
            <option key={kind} value={kind}>
              {SEGMENT[kind]}
            </option>
          ))}
        </select>
      </div>
      {costs ? (
        <>
          <Check
            label={BUDGET.firm}
            hint={BUDGET.firmHint}
            checked={firm}
            onChange={(checked) => {
              showFirm(checked);
              onEdit(edits.budgetStrictness(checked ? "hard" : "soft"));
            }}
          />
          <WeightSlider
            label={BUDGET.weight}
            value={budget.weight}
            limits={limits}
            onCommit={(value) => onEdit(edits.budgetWeight(value))}
            version={version}
          />
        </>
      ) : null}
    </fieldset>
  );
}

interface AmountProps extends Pick<Props, "budget" | "tenure" | "onEdit" | "version" | "problem"> {
  readonly money: ServedLimits[Tenure];
}

/** The amount, the steps either side of it, and the button that takes it off. */
function Amount({ budget, tenure, money, problem = null, onEdit, version }: AmountProps) {
  return (
    <>
      <NumberStepper
        label={BUDGET.amount[tenure]}
        value={budget.amount}
        hint={BUDGET.between(grouped(money.minimum), grouped(money.maximum))}
        problem={problem}
        notANumber={BUDGET.notWhole}
        less={BUDGET.less}
        more={BUDGET.more}
        canStep={budget.amount !== null}
        onCommit={(amount) => onEdit(edits.budgetAmount(amount))}
        onStep={(step) => onEdit(edits.budgetStep(step))}
        version={version}
      />
      <div>
        <button
          type="button"
          className="target"
          // Said to be off, and not switched off: pressed, it takes the budget off and is then
          // off itself, and a button switched off while it has the focus leaves the focus on nothing.
          aria-disabled={budget.amount === null ? true : undefined}
          onClick={() => {
            if (budget.amount !== null) onEdit(edits.budgetClear());
          }}
        >
          {BUDGET.clear}
        </button>
      </div>
    </>
  );
}
