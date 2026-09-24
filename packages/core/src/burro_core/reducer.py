"""The reducer: the only way a spec changes.

Sliders, chips and chat all arrive here as `Operations`, so the three can never
drift apart. It is pure and total: the same inputs give the same output, and a
bad edit is rejected, never raised. Nothing is half-applied.

What a person says outweighs what they did not say. A default weight is
nobody's choice, so the first wish that is applied makes every one of them
give way to a quarter of itself, and a thing that is simply named is worth a
half. Both happen here and are written into the spec, so ranking stays a
function of the spec alone.

What a person takes off stays off. A weight that some tenure has a default
for leaves an entry of nothing behind when it is taken off, so that a change
of tenure does not bring the default back.
"""

from collections.abc import Callable

from burro_core._record import Record
from burro_core.catalogue import FEATURES, default_direction, direction_allowed
from burro_core.ids import (
    AreaAction,
    AreaRuleKind,
    BudgetAction,
    Choice,
    Combine,
    CommuteAction,
    Dimension,
    Direction,
    DirectionChoice,
    EditProvenance,
    Mode,
    ModeChoice,
    OpsGroup,
    Provenance,
    PtBasis,
    RejectReason,
    Segment,
    SegmentChoice,
    SettingAction,
    Step,
    Strictness,
    StrictnessChoice,
    Tenure,
    TenureChoice,
    WeightAction,
    segments_for,
)
from burro_core.ids import Setting as SettingName
from burro_core.ops import (
    AreaEdit,
    BudgetEdit,
    CommuteEdit,
    Operations,
    SettingEdit,
    TagEdit,
    WeightEdit,
)
from burro_core.release import Release
from burro_core.spec import (
    DEFAULT_BUDGET_WEIGHT,
    DEFAULT_COMBINE,
    DEFAULT_COMMUTE_MINUTES,
    DEFAULT_COMMUTE_MODE,
    DEFAULT_COMMUTE_WEIGHT,
    DEFAULT_PT_BASIS,
    DEFAULT_SEGMENT,
    DEFAULT_STRICTNESS,
    DEFAULT_WEIGHTS,
    LIMITS,
    MENTION_WEIGHT,
    WEIGHT_STEPS,
    AreaRule,
    Commute,
    FeatureWeight,
    PreferenceSpec,
    TagWeight,
    default_spec,
    given_way,
    snap,
    steps,
)


class Applied(Record):
    group: OpsGroup
    index: int
    # False for an edit that is in order but leaves the spec as it was.
    changed: bool


class Rejected(Record):
    group: OpsGroup
    index: int
    reason: RejectReason


class ReducerResult(Record):
    spec: PreferenceSpec
    applied: tuple[Applied, ...]
    rejected: tuple[Rejected, ...]


Outcome = PreferenceSpec | RejectReason

_UP = frozenset({Step.UP_SMALL, Step.UP_LARGE})
_LARGE = frozenset({Step.UP_LARGE, Step.DOWN_LARGE})
_WEIGHT_SETTINGS = frozenset({SettingName.COMMUTE_WEIGHT, SettingName.BUDGET_WEIGHT})


def _sign(step: Step) -> int:
    return 1 if step in _UP else -1


def _stamped[R: Record](before: R | None, after: R, provenance: Provenance) -> R:
    """`after`, carrying the edit's provenance if it differs from what was there.

    `after` is built with the old provenance, so an edit that changes nothing
    leaves provenance alone too.
    """
    return after if after == before else after.replace(provenance=provenance)


def _weighed[W: (FeatureWeight, TagWeight)](
    before: W | None, after: W, provenance: Provenance, given_outright: bool
) -> W:
    """As `_stamped`, but a number given outright for a weight nobody had chosen is a choice.

    A slider moved to the very number the default gave has still been moved.
    Without this it would go on giving way, and a change of tenure would reset it.
    """
    chosen = given_outright and before is not None and before.provenance is Provenance.DEFAULT
    return after.replace(provenance=provenance) if chosen else _stamped(before, after, provenance)


def _nobody_chose(weight: FeatureWeight | TagWeight | None) -> bool:
    """Whether a step up starts from nothing anybody asked for.

    An entry of nothing records that a weight was taken off. Named again, the
    thing is worth what any mention is.
    """
    return weight is None or weight.provenance is Provenance.DEFAULT or weight.weight == 0


# The features some tenure weighs by default. Only these can come back with a
# change of tenure, so only these leave an entry behind when they are taken off.
_HAS_A_DEFAULT = frozenset(feature_id for held in DEFAULT_WEIGHTS.values() for feature_id in held)


def _taken_off(
    spec: PreferenceSpec,
    current: FeatureWeight | None,
    others: tuple[FeatureWeight, ...],
    provenance: Provenance,
) -> PreferenceSpec:
    """The spec with a feature's weight at nothing.

    Zero has one canonical form, which is no entry, and `canonical`, `rank`
    and `check_spec` all pass over an entry of nothing. One is kept all the
    same where a tenure has a default for the feature, in the name of whoever
    took it off, or the next change of tenure would bring the default back.
    Taking off what is not there leaves nothing behind.
    """
    if current is None or current.feature_id not in _HAS_A_DEFAULT:
        return spec.replace(weights=others)
    if current.weight == 0:
        return spec
    return spec.replace(weights=(*others, current.replace(weight=0.0, provenance=provenance)))


def _moved_weight(before: FeatureWeight | TagWeight | None, step: Step) -> float:
    """A weight moved by a step. A step up from nobody's choice is worth a mention at least.

    So "pubs" is worth a half, "more pubs" on a first prompt is worth as much,
    and naming what has a default counts for no less than naming what has none.
    """
    moved = nudged_weight(before.weight if before else 0.0, step)
    return max(moved, MENTION_WEIGHT) if step in _UP and _nobody_chose(before) else moved


def given_way_spec(spec: PreferenceSpec) -> PreferenceSpec:
    """The spec with every weight that is still a default at a quarter of its default value.

    It looks at what the default is, never at what the weight holds, so doing
    it twice changes nothing. A default-provenance weight that the tenure has
    no default for, which only a spec from the wire can hold, has nothing to
    give way to and is left as it is. The budget and the commute settings are
    not weights of this kind and are not touched.
    """
    defaults = DEFAULT_WEIGHTS[spec.tenure]
    weights = tuple(
        w.replace(weight=given_way(defaults[w.feature_id]))
        if w.provenance is Provenance.DEFAULT and w.feature_id in defaults
        else w
        for w in spec.weights
    )
    return spec if weights == spec.weights else spec.replace(weights=weights)


def _new_tenure(spec: PreferenceSpec, tenure: Tenure, release: Release) -> PreferenceSpec:
    """The spec moved to another tenure: what nobody chose becomes the new tenure's default.

    Everything the person set is kept. The budget's amount and segment are
    left to the edit that moved the tenure, because a rent is not a price and
    no segment suits both.
    """
    fresh = default_spec(tenure)
    ranked = {m.feature_id for m in release.metrics if m.rankable}
    # What the person took off is among what they chose: it is an entry of nothing.
    kept = tuple(w for w in spec.weights if w.provenance is not Provenance.DEFAULT)
    chosen = {w.feature_id for w in kept}
    nobody = spec.budget.provenance is Provenance.DEFAULT
    return spec.replace(
        tenure=tenure,
        budget=spec.budget.replace(
            strictness=DEFAULT_STRICTNESS if nobody else spec.budget.strictness,
            weight=DEFAULT_BUDGET_WEIGHT if nobody else spec.budget.weight,
        ),
        weights=(
            *kept,
            # A default the release cannot rank is left out, as it is from one that is served.
            *(w for w in fresh.weights if w.feature_id in ranked and w.feature_id not in chosen),
        ),
        tags=tuple(t for t in spec.tags if t.provenance is not Provenance.DEFAULT),
        commute_combine=DEFAULT_COMBINE
        if spec.commute_combine_from is Provenance.DEFAULT
        else spec.commute_combine,
        pt_basis=DEFAULT_PT_BASIS if spec.pt_basis_from is Provenance.DEFAULT else spec.pt_basis,
        commute_weight=DEFAULT_COMMUTE_WEIGHT
        if spec.commute_weight_from is Provenance.DEFAULT
        else spec.commute_weight,
    )


def _provenance(edit: EditProvenance) -> Provenance:
    return Provenance(edit.value)


def nudged_weight(weight: float, step: Step) -> float:
    """A weight moved by a bounded step and kept within 0 to 1."""
    size = LIMITS.weight_step_large if step in _LARGE else LIMITS.weight_step_small
    # Whole steps, so that ten small steps up from 0 land on exactly 1.
    return snap((steps(weight) + _sign(step) * round(size * WEIGHT_STEPS)) / WEIGHT_STEPS)


def nudged_amount(amount: int, step: Step, tenure: Tenure) -> int:
    """A budget moved by a share of itself, rounded to its unit and kept within its limits.

    A step always moves the number unless it is already at a limit: where
    rounding would leave it where it started, it moves on to the next unit. At
    50,000 a step of 5% is 2,500, which rounds back to 50,000.
    """
    limits = LIMITS.money(tenure)
    large = step in _LARGE
    percent = LIMITS.budget_step_large_percent if large else LIMITS.budget_step_small_percent
    sign = _sign(step)
    # One division, so a tie is an exact tie and goes to the even neighbour.
    moved = round(amount * (100 + sign * percent) / (100 * limits.unit)) * limits.unit
    if (moved - amount) * sign <= 0:
        below = amount // limits.unit * limits.unit
        moved = (
            below + limits.unit if sign > 0 else (below if below < amount else below - limits.unit)
        )
    return min(max(moved, limits.minimum), limits.maximum)


def minutes_limit(mode: Mode, release: Release) -> int:
    """The longest cap a commute by this mode may have on this release."""
    return max(LIMITS.minutes_min, min(LIMITS.minutes_max, release.cutoff(mode)))


def _nudged_minutes(minutes: int, step: Step, limit: int) -> int:
    size = LIMITS.minutes_step_large if step in _LARGE else LIMITS.minutes_step_small
    return min(max(minutes + _sign(step) * size, LIMITS.minutes_min), limit)


def _budget(spec: PreferenceSpec, edit: BudgetEdit, release: Release) -> Outcome:
    budget = spec.budget
    provenance = _provenance(edit.provenance)
    if edit.action is BudgetAction.CLEAR:
        return spec.replace(budget=_stamped(budget, budget.replace(amount=None), provenance))
    if edit.action is BudgetAction.NUDGE:
        if edit.step is Step.NONE or budget.amount is None:
            return RejectReason.NOTHING_TO_CHANGE
        amount = nudged_amount(budget.amount, edit.step, spec.tenure)
        return spec.replace(budget=_stamped(budget, budget.replace(amount=amount), provenance))

    given = (
        edit.tenure is not TenureChoice.UNCHANGED,
        edit.amount != 0,
        edit.segment is not SegmentChoice.UNCHANGED,
        edit.strictness is not StrictnessChoice.UNCHANGED,
    )
    if not any(given):
        return RejectReason.NOTHING_TO_CHANGE
    tenure = Tenure(edit.tenure.value) if given[0] else spec.tenure
    moved = tenure is not spec.tenure
    # A rent and a price are not the same kind of number, and no segment suits
    # both tenures, so a change of tenure keeps neither unless the edit gives them.
    amount = edit.amount if given[1] else (None if moved else budget.amount)
    if given[2]:
        segment = Segment(edit.segment.value)
    else:
        segment = DEFAULT_SEGMENT[tenure] if moved else budget.segment
    strictness = Strictness(edit.strictness.value) if given[3] else budget.strictness

    if segment not in segments_for(tenure):
        return RejectReason.SEGMENT_NOT_FOR_TENURE
    limits = LIMITS.money(tenure)
    if given[1] and not limits.minimum <= edit.amount <= limits.maximum:
        return RejectReason.OUT_OF_RANGE
    if moved:
        spec = _new_tenure(spec, tenure, release)
        if not given[3]:
            strictness = spec.budget.strictness
    after = spec.budget.replace(amount=amount, segment=segment, strictness=strictness)
    return spec.replace(
        tenure_from=provenance if moved else spec.tenure_from,
        budget=_stamped(budget, after, provenance),
    )


def _commute(spec: PreferenceSpec, edit: CommuteEdit, release: Release) -> Outcome:
    provenance = _provenance(edit.provenance)
    current = next((c for c in spec.commutes if c.place_id == edit.place_id), None)
    others = tuple(c for c in spec.commutes if c is not current)
    mode_given = edit.mode is not ModeChoice.UNCHANGED
    strictness_given = edit.strictness is not StrictnessChoice.UNCHANGED

    if current is None:
        if release.place(edit.place_id) is None:
            return RejectReason.UNKNOWN_PLACE
        if edit.action is not CommuteAction.ADD:
            return RejectReason.NO_SUCH_COMMUTE
        if len(spec.commutes) >= LIMITS.max_commutes:
            return RejectReason.TOO_MANY_COMMUTES
        mode = Mode(edit.mode.value) if mode_given else DEFAULT_COMMUTE_MODE
        limit = minutes_limit(mode, release)
        if edit.max_minutes != 0 and not LIMITS.minutes_min <= edit.max_minutes <= limit:
            return RejectReason.OUT_OF_RANGE
        added = Commute(
            place_id=edit.place_id,
            mode=mode,
            max_minutes=edit.max_minutes or min(DEFAULT_COMMUTE_MINUTES, limit),
            strictness=Strictness(edit.strictness.value)
            if strictness_given
            else DEFAULT_STRICTNESS,
            provenance=provenance,
        )
        return spec.replace(commutes=(*others, added))

    if edit.action is CommuteAction.REMOVE:
        return spec.replace(commutes=others)

    # An update, or an add of a place that is already in the spec, which is one.
    # An add does not read `step`.
    steps_minutes = (
        edit.action is CommuteAction.UPDATE and edit.max_minutes == 0 and edit.step is not Step.NONE
    )
    asks_nothing = not (mode_given or strictness_given or edit.max_minutes or steps_minutes)
    if asks_nothing and edit.action is CommuteAction.UPDATE:
        return RejectReason.NOTHING_TO_CHANGE
    mode = Mode(edit.mode.value) if mode_given else current.mode
    limit = minutes_limit(mode, release)
    if edit.max_minutes != 0:
        if not LIMITS.minutes_min <= edit.max_minutes <= limit:
            return RejectReason.OUT_OF_RANGE
        minutes = edit.max_minutes
    elif steps_minutes:
        minutes = _nudged_minutes(current.max_minutes, edit.step, limit)
    else:
        # A change of mode brings the cap within the new mode's cutoff.
        minutes = min(current.max_minutes, limit)
    after = current.replace(
        mode=mode,
        max_minutes=minutes,
        strictness=Strictness(edit.strictness.value) if strictness_given else current.strictness,
    )
    return spec.replace(commutes=(*others, _stamped(current, after, provenance)))


def _weight(spec: PreferenceSpec, edit: WeightEdit, release: Release) -> Outcome:
    provenance = _provenance(edit.provenance)
    current = next((w for w in spec.weights if w.feature_id is edit.feature_id), None)
    others = tuple(w for w in spec.weights if w is not current)
    if edit.action is WeightAction.REMOVE:
        return _taken_off(spec, current, others, provenance)

    if not any(m.feature_id is edit.feature_id and m.rankable for m in release.metrics):
        return RejectReason.NOT_IN_RELEASE
    if edit.action is WeightAction.NUDGE and edit.step is Step.NONE:
        return RejectReason.NOTHING_TO_CHANGE
    if edit.action is WeightAction.SET and not 0 <= edit.value <= 1:
        return RejectReason.OUT_OF_RANGE
    if edit.direction is DirectionChoice.DEFAULT:
        # "As it is": the direction in the spec, or the one the polarity gives.
        direction = current.direction if current else default_direction(edit.feature_id)
    else:
        direction = Direction(edit.direction.value)
        if not direction_allowed(edit.feature_id, direction):
            return RejectReason.DIRECTION_NOT_ALLOWED

    outright = edit.action is WeightAction.SET
    weight = snap(edit.value) if outright else _moved_weight(current, edit.step)
    # Crime is weighted only when the user asks for it or moves its control.
    crime = FEATURES[edit.feature_id].dimension is Dimension.CRIME
    if crime and weight > 0 and edit.provenance is EditProvenance.INFERRED:
        return RejectReason.CRIME_NEEDS_EXPLICIT_REQUEST
    if weight == 0:
        return _taken_off(spec, current, others, provenance)
    after = FeatureWeight(
        feature_id=edit.feature_id,
        weight=weight,
        direction=direction,
        provenance=current.provenance if current else provenance,
    )
    return spec.replace(weights=(*others, _weighed(current, after, provenance, outright)))


def _tag(spec: PreferenceSpec, edit: TagEdit, release: Release) -> Outcome:
    provenance = _provenance(edit.provenance)
    current = next((t for t in spec.tags if t.tag_id is edit.tag_id), None)
    others = tuple(t for t in spec.tags if t is not current)
    if edit.action is WeightAction.REMOVE:
        return spec.replace(tags=others)
    if edit.action is WeightAction.NUDGE and edit.step is Step.NONE:
        return RejectReason.NOTHING_TO_CHANGE
    if edit.action is WeightAction.SET and not 0 <= edit.value <= 1:
        return RejectReason.OUT_OF_RANGE

    outright = edit.action is WeightAction.SET
    weight = snap(edit.value) if outright else _moved_weight(current, edit.step)
    if weight == 0:
        return spec.replace(tags=others)
    after = TagWeight(
        tag_id=edit.tag_id,
        weight=weight,
        provenance=current.provenance if current else provenance,
    )
    return spec.replace(tags=(*others, _weighed(current, after, provenance, outright)))


def _area(spec: PreferenceSpec, edit: AreaEdit, release: Release) -> Outcome:
    provenance = _provenance(edit.provenance)
    current = next((a for a in spec.areas if a.area_id == edit.area_id), None)
    others = tuple(a for a in spec.areas if a is not current)
    # A rule already in the spec can always be cleared, so a spec that names an
    # area a newer release has dropped can still be put right.
    if current is None and release.neighbourhood(edit.area_id) is None:
        return RejectReason.UNKNOWN_AREA
    if edit.action is AreaAction.CLEAR:
        return spec.replace(areas=others)
    if release.neighbourhood(edit.area_id) is None:
        return RejectReason.UNKNOWN_AREA
    after = AreaRule(
        area_id=edit.area_id,
        rule=AreaRuleKind(edit.action.value),
        provenance=current.provenance if current else provenance,
    )
    return spec.replace(areas=(*others, _stamped(current, after, provenance)))


def _setting(spec: PreferenceSpec, edit: SettingEdit, release: Release) -> Outcome:
    provenance = _provenance(edit.provenance)
    if edit.setting in _WEIGHT_SETTINGS:
        on_budget = edit.setting is SettingName.BUDGET_WEIGHT
        before = spec.budget.weight if on_budget else spec.commute_weight
        if edit.action is SettingAction.NUDGE:
            if edit.step is Step.NONE:
                return RejectReason.NOTHING_TO_CHANGE
            weight = nudged_weight(before, edit.step)
        elif not 0 <= edit.value <= 1:
            return RejectReason.OUT_OF_RANGE
        else:
            weight = snap(edit.value)
        if on_budget:
            budget = _stamped(spec.budget, spec.budget.replace(weight=weight), provenance)
            return spec.replace(budget=budget)
        if weight == before:
            return spec
        return spec.replace(commute_weight=weight, commute_weight_from=provenance)

    # Only a weight can be nudged, and a choice must belong to its setting.
    if edit.action is SettingAction.NUDGE:
        return RejectReason.MISMATCHED_CHOICE
    if edit.setting is SettingName.COMMUTE_COMBINE:
        if edit.choice not in (Choice.SLOWEST, Choice.MEAN):
            return RejectReason.MISMATCHED_CHOICE
        combine = Combine(edit.choice.value)
        if combine is spec.commute_combine:
            return spec
        return spec.replace(commute_combine=combine, commute_combine_from=provenance)
    if edit.choice not in (Choice.TYPICAL, Choice.JUST_MISSED):
        return RejectReason.MISMATCHED_CHOICE
    basis = PtBasis(edit.choice.value)
    if basis is spec.pt_basis:
        return spec
    return spec.replace(pt_basis=basis, pt_basis_from=provenance)


def apply(spec: PreferenceSpec, ops: Operations, release: Release) -> ReducerResult:
    """Apply every edit that is in order, in a fixed order, and reject the rest.

    Groups are applied in the order budget, commute, weight, tag, area,
    setting, and within a group in array order. A later edit wins.

    Each edit is applied to the spec with its defaults given way, so a step
    from a default starts from where it gave way to. If the edit changes
    something, that is the new spec. If it is turned away, or changes nothing,
    the spec stays exactly as it was, defaults and all.
    """
    applied: list[Applied] = []
    rejected: list[Rejected] = []

    def run[E](
        group: OpsGroup,
        edits: tuple[E, ...],
        handler: Callable[[PreferenceSpec, E, Release], Outcome],
    ) -> None:
        nonlocal spec
        for index, edit in enumerate(edits):
            ready = given_way_spec(spec)
            outcome = handler(ready, edit, release)
            if isinstance(outcome, RejectReason):
                rejected.append(Rejected(group=group, index=index, reason=outcome))
                continue
            changed = outcome != ready
            applied.append(Applied(group=group, index=index, changed=changed))
            if changed:
                # Again, because a change of tenure brings new defaults with it.
                spec = given_way_spec(outcome)

    run(OpsGroup.BUDGET, ops.budget_ops, _budget)
    run(OpsGroup.COMMUTE, ops.commute_ops, _commute)
    run(OpsGroup.WEIGHT, ops.weight_ops, _weight)
    run(OpsGroup.TAG, ops.tag_ops, _tag)
    run(OpsGroup.AREA, ops.area_ops, _area)
    run(OpsGroup.SETTING, ops.setting_ops, _setting)
    return ReducerResult(spec=spec, applied=tuple(applied), rejected=tuple(rejected))
