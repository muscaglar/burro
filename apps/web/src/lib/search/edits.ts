/**
 * The edits a control sends. Each is one `Operations` with one edit in it and
 * five empty arrays, as docs/design/web.md section 5.1 lists them.
 *
 * The website builds edits and never a spec: the API's reducer applies an
 * edit, and what it returns is what the controls are drawn from. A field an
 * edit has nothing to say in carries its sentinel: `unchanged`, `none`,
 * `default`, `0` or `0.0`.
 */

import type {
  AreaEdit,
  AssumptionCode,
  BudgetEdit,
  Combine,
  CommuteEdit,
  Direction,
  FeatureId,
  Mode,
  Operations,
  OpsGroup,
  PtBasis,
  Segment,
  SettingEdit,
  Step,
  Strictness,
  TagEdit,
  TagId,
  Tenure,
  Toward,
  WeightEdit,
} from "@/lib/api/schema";

/** The six arrays, in the order the reducer applies them. */
export const GROUPS: readonly OpsGroup[] = [
  "budget_ops",
  "commute_ops",
  "weight_ops",
  "tag_ops",
  "area_ops",
  "setting_ops",
];

export const NO_EDITS: Operations = {
  budget_ops: [],
  commute_ops: [],
  weight_ops: [],
  tag_ops: [],
  area_ops: [],
  setting_ops: [],
};

/** Every edit a control makes says that a control made it. */
const BY_A_CONTROL = "ui_edit" as const;

const BUDGET: BudgetEdit = {
  action: "set",
  tenure: "unchanged",
  amount: 0,
  segment: "unchanged",
  strictness: "unchanged",
  step: "none",
  provenance: BY_A_CONTROL,
};

const WEIGHT: Omit<WeightEdit, "feature_id"> = {
  action: "set",
  value: 0,
  step: "none",
  direction: "default",
  provenance: BY_A_CONTROL,
};

const TAG: Omit<TagEdit, "tag_id"> = {
  action: "set",
  value: 0,
  step: "none",
  // Which end is asked for is left as it is unless the edit says: the high end for a vibe not yet asked for.
  toward: "default",
  provenance: BY_A_CONTROL,
};

const SETTING: Omit<SettingEdit, "setting"> = {
  action: "set",
  choice: "none",
  value: 0,
  step: "none",
  provenance: BY_A_CONTROL,
};

function commute(placeId: string, change: Partial<CommuteEdit>): Operations {
  const edit: CommuteEdit = {
    action: "update",
    place_id: placeId,
    mode: "unchanged",
    max_minutes: 0,
    strictness: "unchanged",
    step: "none",
    provenance: BY_A_CONTROL,
    ...change,
  };
  return { ...NO_EDITS, commute_ops: [edit] };
}

const budget = (change: Partial<BudgetEdit>): Operations => ({
  ...NO_EDITS,
  budget_ops: [{ ...BUDGET, ...change }],
});

const weight = (featureId: FeatureId, change: Partial<WeightEdit>): Operations => ({
  ...NO_EDITS,
  weight_ops: [{ ...WEIGHT, feature_id: featureId, ...change }],
});

const tag = (tagId: TagId, change: Partial<TagEdit>): Operations => ({
  ...NO_EDITS,
  tag_ops: [{ ...TAG, tag_id: tagId, ...change }],
});

const setting = (name: SettingEdit["setting"], change: Partial<SettingEdit>): Operations => ({
  ...NO_EDITS,
  setting_ops: [{ ...SETTING, setting: name, ...change }],
});

const area = (areaId: string, action: AreaEdit["action"]): Operations => ({
  ...NO_EDITS,
  area_ops: [{ action, area_id: areaId, provenance: BY_A_CONTROL }],
});

/** A step a button takes: one small step down, or one small step up. */
export type SmallStep = Extract<Step, "down_small" | "up_small">;

export const edits = {
  tenure: (tenure: Tenure) => budget({ tenure }),
  budgetAmount: (amount: number) => budget({ amount }),
  budgetStep: (step: SmallStep) => budget({ action: "nudge", step }),
  budgetClear: () => budget({ action: "clear" }),
  budgetSegment: (segment: Segment) => budget({ segment }),
  budgetStrictness: (strictness: Strictness) => budget({ strictness }),
  budgetWeight: (value: number) => setting("budget_weight", { value }),

  placeAdd: (placeId: string) => commute(placeId, { action: "add" }),
  placeMode: (placeId: string, mode: Mode) => commute(placeId, { mode }),
  placeMinutes: (placeId: string, minutes: number) => commute(placeId, { max_minutes: minutes }),
  placeStep: (placeId: string, step: SmallStep) => commute(placeId, { step }),
  placeStrictness: (placeId: string, strictness: Strictness) => commute(placeId, { strictness }),
  placeRemove: (placeId: string) => commute(placeId, { action: "remove" }),

  journeyCombine: (choice: Combine) => setting("commute_combine", { choice }),
  journeyBasis: (choice: PtBasis) => setting("pt_basis", { choice }),
  journeyWeight: (value: number) => setting("commute_weight", { value }),

  /** A switch turned on is worth what a word is: a large step up. */
  featureOn: (featureId: FeatureId) => weight(featureId, { action: "nudge", step: "up_large" }),
  featureWeight: (featureId: FeatureId, value: number) => weight(featureId, { value }),
  /** The weight is sent as it is, because `set` always reads it. */
  featureDirection: (featureId: FeatureId, value: number, direction: Direction) =>
    weight(featureId, { value, direction }),
  featureOff: (featureId: FeatureId) => weight(featureId, { action: "remove" }),

  /** A vibe added is worth what a word is: a large step, towards the end asked for. */
  tagOn: (tagId: TagId, toward: Toward = "high") => tag(tagId, { action: "nudge", step: "up_large", toward }),
  /** How much a vibe counts. Which end is asked for is left as it is, unless one is given. */
  tagWeight: (tagId: TagId, value: number, toward: Toward | "default" = "default") =>
    tag(tagId, { value, toward }),
  tagOff: (tagId: TagId) => tag(tagId, { action: "remove" }),

  areaHide: (areaId: string) => area(areaId, "exclude"),
  areaClear: (areaId: string) => area(areaId, "clear"),
} as const;

/** The edits of one followed by the edits of the other, group by group. */
export function merged(one: Operations, other: Operations): Operations {
  return {
    budget_ops: [...one.budget_ops, ...other.budget_ops],
    commute_ops: [...one.commute_ops, ...other.commute_ops],
    weight_ops: [...one.weight_ops, ...other.weight_ops],
    tag_ops: [...one.tag_ops, ...other.tag_ops],
    area_ops: [...one.area_ops, ...other.area_ops],
    setting_ops: [...one.setting_ops, ...other.setting_ops],
  };
}

export function countOf(operations: Operations): number {
  return GROUPS.reduce((total, group) => total + operations[group].length, 0);
}

export function isEmpty(operations: Operations): boolean {
  return countOf(operations) === 0;
}

/**
 * The answer to a question about a place or an area: the edit the question
 * points at, copied, with the id the person picked in it. Nothing else of the
 * edit is touched, so what the words said of the journey is kept.
 * `null` when the question points at no edit that takes an id.
 */
export function answered(
  operations: Operations,
  group: OpsGroup,
  index: number,
  id: string,
): Operations | null {
  if (group === "commute_ops") {
    const edit = operations.commute_ops[index];
    return edit ? { ...NO_EDITS, commute_ops: [{ ...edit, place_id: id }] } : null;
  }
  if (group === "area_ops") {
    const edit = operations.area_ops[index];
    return edit ? { ...NO_EDITS, area_ops: [{ ...edit, area_id: id }] } : null;
  }
  return null;
}

/**
 * The part of the search an edit is about, as the chips name it. The key
 * holds an id of the release and never anything a person typed.
 */
export type ChipKey =
  | "tenure"
  | "budget"
  | "journeys"
  | `place:${string}`
  | `feature:${string}`
  | `tag:${string}`
  | `area:${string}`;

export interface Said {
  readonly key: ChipKey;
  /** What the edit itself states of that part, so that it is no longer an assumption. */
  readonly states: readonly AssumptionCode[];
}

function budgetSaid(edit: BudgetEdit): Said[] {
  const said: Said[] = [];
  if (edit.action !== "set") return [{ key: "budget", states: [] }];
  if (edit.tenure !== "unchanged") said.push({ key: "tenure", states: ["tenure"] });
  const states: AssumptionCode[] = [];
  if (edit.segment !== "unchanged") states.push("segment");
  if (edit.strictness !== "unchanged") states.push("strictness");
  if (states.length > 0 || edit.amount !== 0 || said.length === 0) {
    said.push({ key: "budget", states });
  }
  return said;
}

function commuteSaid(edit: CommuteEdit): Said[] {
  const states: AssumptionCode[] = [];
  if (edit.mode !== "unchanged") states.push("mode");
  if (edit.max_minutes !== 0 || (edit.action === "update" && edit.step !== "none")) {
    states.push("max_minutes");
  }
  if (edit.strictness !== "unchanged") states.push("strictness");
  return [{ key: `place:${edit.place_id}`, states }];
}

function weightSaid(edit: WeightEdit): Said[] {
  const states: AssumptionCode[] = edit.provenance === "inferred" ? [] : ["weight"];
  if (edit.direction !== "default") states.push("direction");
  return [{ key: `feature:${edit.feature_id}`, states }];
}

/** Which parts of the search the edit at `operations[group][index]` is about. */
export function saidBy(operations: Operations, group: OpsGroup, index: number): readonly Said[] {
  switch (group) {
    case "budget_ops": {
      const edit = operations.budget_ops[index];
      return edit ? budgetSaid(edit) : [];
    }
    case "commute_ops": {
      const edit = operations.commute_ops[index];
      return edit ? commuteSaid(edit) : [];
    }
    case "weight_ops": {
      const edit = operations.weight_ops[index];
      return edit ? weightSaid(edit) : [];
    }
    case "tag_ops": {
      const edit = operations.tag_ops[index];
      if (!edit) return [];
      // A vibe a person set is theirs: it is no longer what a word with two meanings was read as.
      return [{ key: `tag:${edit.tag_id}`, states: edit.provenance === "inferred" ? [] : ["weight", "word"] }];
    }
    case "area_ops": {
      const edit = operations.area_ops[index];
      return edit ? [{ key: `area:${edit.area_id}`, states: [] }] : [];
    }
    case "setting_ops": {
      const edit = operations.setting_ops[index];
      if (!edit) return [];
      return [{ key: edit.setting === "budget_weight" ? "budget" : "journeys", states: [] }];
    }
  }
}

/** The part an assumption of this code belongs to, for the edit it was made about. */
export function chipOf(
  operations: Operations,
  group: OpsGroup,
  index: number,
  code: AssumptionCode,
): ChipKey | null {
  if (group === "budget_ops") {
    if (!operations.budget_ops[index]) return null;
    return code === "tenure" ? "tenure" : "budget";
  }
  return saidBy(operations, group, index)[0]?.key ?? null;
}
