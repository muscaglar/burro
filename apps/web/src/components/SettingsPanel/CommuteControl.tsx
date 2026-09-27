"use client";

import { COMBINE, MODE, PT_BASIS } from "@/content/labels";
import { JOURNEY } from "@/content/settings";
import type {
  Combine,
  Commute,
  Mode,
  Operations,
  PreferenceSpec,
  PtBasis,
  ServedLimits,
} from "@/lib/api/schema";
import { useDraft } from "@/lib/search/draft";
import { edits } from "@/lib/search/edits";

import { Press } from "../kit/Press/Press";
import { holdsAFigure } from "../kit/reads";
import { Drawn } from "../kit/Thing/Thing";
import { NumberStepper } from "../NumberStepper/NumberStepper";
import { WeightSlider } from "../WeightSlider/WeightSlider";
import { Check, Radios } from "./fields";
import styles from "./SettingsPanel.module.css";

const MODES: readonly Mode[] = ["pt", "cycle", "walk"];
const COMBINES: readonly Combine[] = ["slowest", "mean"];
const BASES: readonly PtBasis[] = ["typical", "just_missed"];

interface CommuteProps {
  readonly commute: Commute;
  /** The name of the place, as the API gave it. */
  readonly name: string;
  readonly limits: ServedLimits;
  readonly onEdit: (operations: Operations) => void;
  readonly version: number;
  readonly problem?: string | null;
}

/** One place to reach: how, within how long, and whether that is a firm limit. */
export function CommuteControl({ commute, name, limits, onEdit, version, problem = null }: CommuteProps) {
  const { place_id: placeId } = commute;
  const [mode, showMode] = useDraft(commute.mode, version);
  const [firm, showFirm] = useDraft(commute.strictness === "hard", version);
  // The longest journey that can be asked for is the longest the data holds for that way of travelling.
  const most = Math.min(limits.minutes_max, limits.cutoff_minutes[mode]);

  return (
    // It says that it is a journey, and what removes it that it does, to the settings: what is
    // removed hands the focus to the journey beside it. Neither says which journey.
    <fieldset className={styles.thing} data-journey="">
      <legend className={styles.groupLegend}>
        <span className={styles.line}>
          <Drawn thing={{ kind: "place" }} state="said" />
          <span className={styles.tag} data-reads={holdsAFigure(JOURNEY.place(name))}>
            {JOURNEY.place(name)}
          </span>
        </span>
      </legend>
      <Radios
        legend={JOURNEY.how}
        options={MODES.map((value) => ({ value, label: MODE[value] }))}
        value={mode}
        onChange={(chosen) => {
          showMode(chosen);
          onEdit(edits.placeMode(placeId, chosen));
        }}
      />
      <NumberStepper
        label={JOURNEY.longest}
        value={commute.max_minutes}
        hint={JOURNEY.between(limits.minutes_min, most)}
        problem={problem}
        notANumber={JOURNEY.notWhole}
        keptWithin={{ least: limits.minutes_min, most }}
        less={JOURNEY.shorter}
        more={JOURNEY.longer}
        onCommit={(minutes) => onEdit(edits.placeMinutes(placeId, minutes))}
        onStep={(step) => onEdit(edits.placeStep(placeId, step))}
        version={version}
      />
      <Check
        label={JOURNEY.firm}
        hint={JOURNEY.firmHint}
        checked={firm}
        onChange={(checked) => {
          showFirm(checked);
          onEdit(edits.placeStrictness(placeId, checked ? "hard" : "soft"));
        }}
      />
      <Press kind="stop" className={styles.press} data-removes="" onPress={() => onEdit(edits.placeRemove(placeId))}>
        {JOURNEY.remove(name)}
      </Press>
    </fieldset>
  );
}

interface SettingsProps {
  readonly spec: Pick<PreferenceSpec, "commute_combine" | "pt_basis" | "commute_weight">;
  readonly limits: ServedLimits;
  readonly onEdit: (operations: Operations) => void;
  readonly version: number;
  /** Why what was last set of them is not in the results, in words. */
  readonly problem?: string | null;
}

/** How the journeys count: which one, which time, and how much. */
export function JourneySettings({ spec, limits, onEdit, version, problem = null }: SettingsProps) {
  const [combine, showCombine] = useDraft(spec.commute_combine, version);
  const [basis, showBasis] = useDraft(spec.pt_basis, version);
  return (
    <fieldset className={styles.thing}>
      <legend className={styles.groupLegend}>
        <span className={styles.line}>
          <Drawn thing={{ kind: "place" }} state="said" />
          <span className={styles.tag}>{JOURNEY.settingsLegend}</span>
        </span>
      </legend>
      <Radios
        legend={JOURNEY.combine}
        options={COMBINES.map((value) => ({ value, label: COMBINE[value] }))}
        value={combine}
        reads
        onChange={(chosen) => {
          showCombine(chosen);
          onEdit(edits.journeyCombine(chosen));
        }}
      />
      <Radios
        legend={JOURNEY.basis}
        options={BASES.map((value) => ({ value, label: PT_BASIS[value] }))}
        value={basis}
        reads
        onChange={(chosen) => {
          showBasis(chosen);
          onEdit(edits.journeyBasis(chosen));
        }}
      />
      <WeightSlider
        label={JOURNEY.weight}
        value={spec.commute_weight}
        limits={limits}
        onCommit={(value) => onEdit(edits.journeyWeight(value))}
        version={version}
      />
      {problem ? (
        <p className={styles.problem} role="alert">
          {problem}
        </p>
      ) : null}
    </fieldset>
  );
}
