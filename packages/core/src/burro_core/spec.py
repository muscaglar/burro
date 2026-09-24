"""The preference spec: what a person wants, as ids and numbers and nothing else.

It holds no free text and no place name, so it can be hashed, cached and
logged by its hash without holding anything a person typed. Construction
checks each field alone. `check_spec` checks what depends on another field,
the catalogue or the release.
"""

import hashlib
import json
import math
from collections.abc import Hashable, Mapping, Sequence
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, field_validator

from burro_core._record import Record
from burro_core.catalogue import default_direction, direction_allowed
from burro_core.ids import (
    AreaId,
    AreaRuleKind,
    Combine,
    Direction,
    FeatureId,
    Mode,
    PlaceId,
    Provenance,
    PtBasis,
    Segment,
    SpecProblemKind,
    Strictness,
    TagId,
    Tenure,
    segments_for,
)
from burro_core.release import Release

WEIGHT_STEPS = 20  # a weight moves in steps of 0.05


class MoneyLimits(Record):
    minimum: int
    maximum: int
    unit: int


class Limits(Record):
    """The numbers of section 5.2. A form that keeps to them is never refused by the reducer."""

    weight_unit: float = 1 / WEIGHT_STEPS
    weight_step_small: float = 0.10
    weight_step_large: float = 0.25
    budget_step_small_percent: int = 5
    budget_step_large_percent: int = 15
    rent: MoneyLimits = MoneyLimits(minimum=300, maximum=20_000, unit=25)
    buy: MoneyLimits = MoneyLimits(minimum=50_000, maximum=20_000_000, unit=5_000)
    minutes_min: int = 10
    # A release may set a lower limit for a mode: its cutoff (section 6.1).
    minutes_max: int = 120
    minutes_step_small: int = 5
    minutes_step_large: int = 15
    max_commutes: int = 3

    def money(self, tenure: Tenure) -> MoneyLimits:
        return self.rent if tenure is Tenure.RENT else self.buy


LIMITS = Limits()

DEFAULT_SEGMENT = {Tenure.RENT: Segment.BED_1, Tenure.BUY: Segment.FLAT}
DEFAULT_COMMUTE_MODE = Mode.PT
DEFAULT_COMMUTE_MINUTES = 45
DEFAULT_STRICTNESS = Strictness.SOFT
DEFAULT_BUDGET_WEIGHT = 0.80
DEFAULT_COMMUTE_WEIGHT = 1.00
DEFAULT_COMBINE = Combine.SLOWEST
DEFAULT_PT_BASIS = PtBasis.TYPICAL
# What a thing that is simply named is worth: a step up never leaves a weight
# that nobody had chosen below it (section 5.2).
MENTION_WEIGHT = 0.50
# Once a wish has been applied, a default weight counts for one part in this
# many of what it did, so that one thing said outweighs all that was not
# (section 5.3). A third left 0.55 unsaid for a renter against a mention of 0.50.
GIVE_WAY_TO_ONE_IN = 4


def snap(weight: float) -> float:
    """The nearest step of 0.05 between 0 and 1. The one place that rounds a tie up."""
    return min(max(math.floor(weight * WEIGHT_STEPS + 0.5), 0), WEIGHT_STEPS) / WEIGHT_STEPS


def steps(weight: float) -> int:
    """A snapped weight as its whole number of 0.05 steps, 0 to 20."""
    return round(snap(weight) * WEIGHT_STEPS)


def given_way(weight: float) -> float:
    """A default weight once a wish has been applied: a quarter of it, rounded down to a step.

    It is never less than one step, so that a default is outweighed and not
    switched off. It is counted in whole steps, so that no float decides which
    step 0.075 is nearer to, and it is rounded down, because to the nearest
    step a quarter of a renter's defaults is 0.55 in all, as a third is, and
    one mention would still not outweigh them.
    """
    return max(steps(weight) // GIVE_WAY_TO_ONE_IN, 1) / WEIGHT_STEPS if weight > 0 else 0.0


Weight = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False), AfterValidator(snap)]


class Budget(Record):
    # `None` is "not stated". Zero never stands for unknown.
    amount: Annotated[int, Field(gt=0)] | None
    segment: Segment
    strictness: Strictness
    weight: Weight
    provenance: Provenance


class Commute(Record):
    place_id: PlaceId
    mode: Mode
    max_minutes: int = Field(ge=LIMITS.minutes_min, le=LIMITS.minutes_max)
    strictness: Strictness
    provenance: Provenance


class FeatureWeight(Record):
    feature_id: FeatureId
    weight: Weight
    direction: Direction
    provenance: Provenance


class TagWeight(Record):
    tag_id: TagId
    weight: Weight
    provenance: Provenance


class AreaRule(Record):
    area_id: AreaId
    rule: AreaRuleKind
    provenance: Provenance


def _in_order[T](items: Sequence[T], key: str) -> tuple[T, ...]:
    """Sorted by id, and refused if an id repeats.

    Sorting on construction means nothing downstream depends on the order
    edits arrived in.
    """
    keys: list[Hashable] = [getattr(item, key) for item in items]
    if len(set(keys)) != len(keys):
        raise ValueError(f"{key} repeats")
    return tuple(sorted(items, key=lambda item: getattr(item, key)))


class PreferenceSpec(Record):
    schema_version: Literal[1]
    tenure: Tenure
    budget: Budget
    commutes: Annotated[tuple[Commute, ...], Field(max_length=LIMITS.max_commutes)]
    commute_combine: Combine
    pt_basis: PtBasis
    commute_weight: Weight
    # A feature with no entry has weight 0.
    weights: tuple[FeatureWeight, ...]
    tags: tuple[TagWeight, ...]
    areas: tuple[AreaRule, ...]
    tenure_from: Provenance
    commute_combine_from: Provenance
    pt_basis_from: Provenance
    commute_weight_from: Provenance

    @field_validator("commutes", mode="after")
    @classmethod
    def _commutes_in_order(cls, value: tuple[Commute, ...]) -> tuple[Commute, ...]:
        return _in_order(value, "place_id")

    @field_validator("weights", mode="after")
    @classmethod
    def _weights_in_order(cls, value: tuple[FeatureWeight, ...]) -> tuple[FeatureWeight, ...]:
        return _in_order(value, "feature_id")

    @field_validator("tags", mode="after")
    @classmethod
    def _tags_in_order(cls, value: tuple[TagWeight, ...]) -> tuple[TagWeight, ...]:
        return _in_order(value, "tag_id")

    @field_validator("areas", mode="after")
    @classmethod
    def _areas_in_order(cls, value: tuple[AreaRule, ...]) -> tuple[AreaRule, ...]:
        return _in_order(value, "area_id")

    @property
    def commute_requested(self) -> bool:
        return bool(self.commutes) and self.commute_weight > 0

    @property
    def budget_requested(self) -> bool:
        return self.budget.amount is not None and self.budget.weight > 0

    @property
    def active_weights(self) -> tuple[FeatureWeight, ...]:
        return tuple(w for w in self.weights if w.weight > 0)

    @property
    def active_tags(self) -> tuple[TagWeight, ...]:
        return tuple(t for t in self.tags if t.weight > 0)


class SpecProblem(Record):
    # A path into the spec, such as `commutes[0].place_id`. Never a value. A
    # position is one in the spec as it is kept and returned, which is in id
    # order, and not in the body that was sent, whose order the spec does not keep.
    path: str
    problem: SpecProblemKind


class SpecError(Exception):
    """A spec that cannot be ranked on this release. Holds paths and codes, never a value."""

    def __init__(self, problems: tuple[SpecProblem, ...]) -> None:
        self.problems = problems
        super().__init__("; ".join(f"{p.path}: {p.problem}" for p in problems))


_RENTER_WEIGHTS = (
    (FeatureId.STATION_WALK, 0.50),
    (FeatureId.STATION_LINES, 0.30),
    (FeatureId.PARK_PROXIMITY, 0.30),
    (FeatureId.HIGHSTREET_ACCESS, 0.30),
    (FeatureId.NOISE_EXPOSURE, 0.20),
    (FeatureId.AIR_NO2, 0.20),
)
_BUYER_WEIGHTS = (
    (FeatureId.STATION_WALK, 0.40),
    (FeatureId.PARK_PROXIMITY, 0.40),
    (FeatureId.GREEN_COVER, 0.30),
    (FeatureId.HIGHSTREET_ACCESS, 0.30),
    (FeatureId.NOISE_EXPOSURE, 0.30),
    (FeatureId.STATION_LINES, 0.20),
    (FeatureId.AIR_NO2, 0.20),
)


# What each default weight is, for the reducer, which lets them give way.
DEFAULT_WEIGHTS: Mapping[Tenure, Mapping[FeatureId, float]] = MappingProxyType(
    {
        Tenure.RENT: MappingProxyType(dict(_RENTER_WEIGHTS)),
        Tenure.BUY: MappingProxyType(dict(_BUYER_WEIGHTS)),
    }
)


def default_spec(tenure: Tenure) -> PreferenceSpec:
    """The spec a search starts from. Every provenance is `default`: nobody chose any of it."""
    weights = _RENTER_WEIGHTS if tenure is Tenure.RENT else _BUYER_WEIGHTS
    return PreferenceSpec(
        schema_version=1,
        tenure=tenure,
        budget=Budget(
            amount=None,
            segment=DEFAULT_SEGMENT[tenure],
            strictness=DEFAULT_STRICTNESS,
            weight=DEFAULT_BUDGET_WEIGHT,
            provenance=Provenance.DEFAULT,
        ),
        commutes=(),
        commute_combine=DEFAULT_COMBINE,
        pt_basis=DEFAULT_PT_BASIS,
        commute_weight=DEFAULT_COMMUTE_WEIGHT,
        weights=tuple(
            FeatureWeight(
                feature_id=feature_id,
                weight=weight,
                direction=default_direction(feature_id),
                provenance=Provenance.DEFAULT,
            )
            for feature_id, weight in weights
        ),
        tags=(),
        areas=(),
        tenure_from=Provenance.DEFAULT,
        commute_combine_from=Provenance.DEFAULT,
        pt_basis_from=Provenance.DEFAULT,
        commute_weight_from=Provenance.DEFAULT,
    )


def check_spec(spec: PreferenceSpec, release: Release) -> tuple[SpecProblem, ...]:
    """What is wrong with this spec on this release, as paths and codes. Empty if nothing is.

    It looks only at what `canonical` keeps: a weight of 0 and a budget with no
    amount are not checked, because two specs with the same canonical form
    must be treated the same.
    """
    problems: list[SpecProblem] = []

    def problem(path: str, kind: SpecProblemKind) -> None:
        problems.append(SpecProblem(path=path, problem=kind))

    if spec.budget.amount is not None:
        limits = LIMITS.money(spec.tenure)
        if spec.budget.segment not in segments_for(spec.tenure):
            problem("budget.segment", SpecProblemKind.SEGMENT_NOT_FOR_TENURE)
        if not limits.minimum <= spec.budget.amount <= limits.maximum:
            problem("budget.amount", SpecProblemKind.OUT_OF_RANGE)

    for index, commute in enumerate(spec.commutes):
        if release.place(commute.place_id) is None:
            problem(f"commutes[{index}].place_id", SpecProblemKind.UNKNOWN_PLACE)
        # A journey beyond the cutoff is known only to be longer than the
        # cutoff, so a cap above it could not be tested (section 6.1).
        if commute.max_minutes > release.cutoff(commute.mode):
            problem(f"commutes[{index}].max_minutes", SpecProblemKind.OUT_OF_RANGE)

    ranked = {m.feature_id for m in release.metrics if m.rankable}
    for index, weight in enumerate(spec.weights):
        if weight.weight == 0:
            continue
        if weight.feature_id not in ranked:
            problem(f"weights[{index}].feature_id", SpecProblemKind.NOT_IN_RELEASE)
        if not direction_allowed(weight.feature_id, weight.direction):
            problem(f"weights[{index}].direction", SpecProblemKind.DIRECTION_NOT_ALLOWED)

    for index, rule in enumerate(spec.areas):
        if release.neighbourhood(rule.area_id) is None:
            problem(f"areas[{index}].area_id", SpecProblemKind.UNKNOWN_AREA)

    return tuple(problems)


def canonical(spec: PreferenceSpec) -> str:
    """The form used for hashing, caching and comparing.

    Two specs with the same canonical form rank the same. The reverse is not
    promised: only differences that plainly cannot matter are folded together.
    """
    document: dict[str, object] = {
        "schema_version": spec.schema_version,
        "tenure": spec.tenure,
        "budget": None
        if spec.budget.amount is None
        else {
            "amount": spec.budget.amount,
            "segment": spec.budget.segment,
            "strictness": spec.budget.strictness,
            "weight": steps(spec.budget.weight),
        },
        "commutes": [
            {
                "place_id": c.place_id,
                "mode": c.mode,
                "max_minutes": c.max_minutes,
                "strictness": c.strictness,
            }
            for c in spec.commutes
        ],
        "weights": [
            {"feature_id": w.feature_id, "weight": steps(w.weight), "direction": w.direction}
            for w in spec.active_weights
        ],
        "tags": [{"tag_id": t.tag_id, "weight": steps(t.weight)} for t in spec.active_tags],
        "areas": [{"area_id": a.area_id, "rule": a.rule} for a in spec.areas],
    }
    # With no commute these three settings change nothing, so they are left out.
    if spec.commutes:
        document["commute_combine"] = spec.commute_combine
        document["pt_basis"] = spec.pt_basis
        document["commute_weight"] = steps(spec.commute_weight)
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def spec_hash(spec: PreferenceSpec) -> str:
    return hashlib.sha256(canonical(spec).encode("utf-8")).hexdigest()
