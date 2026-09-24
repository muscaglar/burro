"""Ranking: a pure function of a preference spec and a data release.

The same inputs give the same output on every call. It does no IO and reads no
clock. It ranks places by what is there, and nothing that reaches it describes
who lives somewhere (ADR 0006). Missing data is never filled in: a component
with no figure for an area is dropped for that area, the remaining weights are
rebalanced, and the coverage is reported.
"""

from dataclasses import dataclass

from pydantic import Field

from burro_core._record import Record
from burro_core.facts import cost_key, fact_id, scored_on_just_missed, travel_key
from burro_core.ids import (
    BUDGET,
    COMMUTE,
    AreaId,
    AreaRuleKind,
    Combine,
    Confidence,
    Direction,
    FactKind,
    FilterReason,
    Mode,
    PlaceId,
    PtBasis,
    Strictness,
    TravelStatus,
    UnrankedReason,
    component_for_feature,
    component_for_tag,
)
from burro_core.release import CostEstimate, Neighbourhood, Release
from burro_core.spec import (
    WEIGHT_STEPS,
    Commute,
    PreferenceSpec,
    SpecError,
    check_spec,
    spec_hash,
    steps,
)

# Any change to the arithmetic in this module bumps it, and so does a change to a
# rule of the reducer or to a rule of what an explanation says.
ENGINE_VERSION = "1.3.0"

FULL_UNTIL_MIN = 15  # a journey this short is as good as any shorter
FULL_UNTIL_SHARE = 0.5  # unless that is more than half the cap
UTILITY_AT_CAP = 0.5  # a journey exactly at the cap is half as good as a short one
ZERO_AT_SHARE = 1.5  # a journey half as long again as the cap is worth nothing
# A home a quarter over budget is worth nothing. Tested against the upper
# quartile, because published rents understate what a new tenant pays.
BUDGET_OVER_SHARE = 0.25
# Below this share of the requested weight, an area is not scored. It is
# compared in whole steps of weight, so that an area with exactly this share
# present is scored however the weight is split between its components.
MIN_WEIGHT_COVERAGE = 0.5

_SORT_DECIMALS = 9
_OUT_DECIMALS = 4


class Contribution(Record):
    component: str
    present: bool
    weight: float  # as requested
    # A dropped component has no share, so these three are 0 when it is missing.
    share: float
    utility: float | None
    contribution: float
    loss: float
    fact_ids: tuple[str, ...]


class CommuteLeg(Record):
    place_id: PlaceId
    mode: Mode
    status: TravelStatus  # of the time that was scored
    minutes: int | None  # the time that was scored
    minutes_typical: int | None
    minutes_just_missed: int | None
    utility: float | None


class BudgetFit(Record):
    upper_quartile: int
    margin: int
    utility: float
    confidence: Confidence
    as_of: str


class RankedArea(Record):
    area_id: AreaId
    rank: int = Field(ge=1)
    score: float = Field(ge=0, le=100)
    weight_coverage: float = Field(ge=0, le=1)
    contributions: tuple[Contribution, ...]
    legs: tuple[CommuteLeg, ...]
    budget: BudgetFit | None
    untested_filters: tuple[FilterReason, ...]


class Filtered(Record):
    area_id: AreaId
    reason: FilterReason


class Unranked(Record):
    area_id: AreaId
    reason: UnrankedReason


class RankResult(Record):
    spec_hash: str
    release_id: str
    engine_version: str
    synthetic: bool
    empty_spec: bool
    ranked: tuple[RankedArea, ...]
    filtered: tuple[Filtered, ...]
    unranked: tuple[Unranked, ...]


def commute_utility(minutes: int, max_minutes: int) -> float:
    """How good a journey of `minutes` is to someone who will put up with `max_minutes`."""
    full_until = min(FULL_UNTIL_MIN, FULL_UNTIL_SHARE * max_minutes)
    zero_at = ZERO_AT_SHARE * max_minutes
    if minutes <= full_until:
        return 1.0
    if minutes <= max_minutes:
        return 1 - (1 - UTILITY_AT_CAP) * (minutes - full_until) / (max_minutes - full_until)
    if minutes < zero_at:
        return UTILITY_AT_CAP * (zero_at - minutes) / (zero_at - max_minutes)
    return 0.0


def budget_utility(amount: int, upper_quartile: int) -> float:
    """1 when the upper quartile is within budget, falling to 0 at a quarter over.

    Being further under budget earns nothing: Burro gives no affordability verdict.
    """
    return min(max(1 - (upper_quartile - amount) / (BUDGET_OVER_SHARE * amount), 0.0), 1.0)


@dataclass(frozen=True)
class _Part:
    """One requested component for one area, before rounding."""

    component: str
    weight: float
    utility: float | None  # None when the component is missing for this area
    fact_ids: tuple[str, ...]


@dataclass(frozen=True)
class _Scored:
    area_id: str
    total: float
    coverage: float
    parts: tuple[_Part, ...]
    legs: tuple[CommuteLeg, ...]
    budget: BudgetFit | None
    untested: tuple[FilterReason, ...]


def _leg(area_id: str, commute: Commute, spec: PreferenceSpec, release: Release) -> CommuteLeg:
    place = release.place(commute.place_id)
    destination = place.destination_id if place else ""
    typical = release.travel(area_id, destination, commute.mode, PtBasis.TYPICAL)
    missed = release.travel(area_id, destination, commute.mode, PtBasis.JUST_MISSED)
    scored = missed if scored_on_just_missed(commute, spec) else typical
    if not spec.commute_requested or scored.status is TravelStatus.MISSING:
        utility = None
    elif scored.minutes is None:
        # Beyond the cutoff: all the release holds is that it is longer than that.
        utility = 0.0
    else:
        utility = commute_utility(scored.minutes, commute.max_minutes)
    return CommuteLeg(
        place_id=commute.place_id,
        mode=commute.mode,
        status=scored.status,
        minutes=scored.minutes,
        minutes_typical=typical.minutes,
        minutes_just_missed=missed.minutes,
        utility=utility,
    )


def _over_cap(leg: CommuteLeg, commute: Commute) -> bool:
    if leg.status is TravelStatus.BEYOND_CUTOFF:
        return True
    return leg.minutes is not None and leg.minutes > commute.max_minutes


def _filter(
    area: Neighbourhood,
    spec: PreferenceSpec,
    estimate: CostEstimate | None,
    legs: tuple[CommuteLeg, ...],
) -> tuple[FilterReason | None, tuple[FilterReason, ...]]:
    """The first filter that catches the area, and the filters that could not be tested.

    A hard filter removes only an area known to fail. One with no estimate or
    no travel time cannot be tested: it stays.
    """
    rules = {rule.area_id: rule.rule for rule in spec.areas}
    if rules.get(area.area_id) is AreaRuleKind.EXCLUDE:
        return FilterReason.EXCLUDED, ()
    selecting = AreaRuleKind.ONLY in rules.values()
    if selecting and rules.get(area.area_id) is not AreaRuleKind.ONLY:
        return FilterReason.NOT_SELECTED, ()

    untested: list[FilterReason] = []
    amount = spec.budget.amount
    if spec.budget.strictness is Strictness.HARD and amount is not None:
        if estimate is None:
            untested.append(FilterReason.OVER_BUDGET)
        elif estimate.upper_quartile > amount:
            return FilterReason.OVER_BUDGET, ()
    hard = [
        leg
        for leg, commute in zip(legs, spec.commutes, strict=True)
        if commute.strictness is Strictness.HARD
    ]
    caps = {commute.place_id: commute for commute in spec.commutes}
    if any(_over_cap(leg, caps[leg.place_id]) for leg in hard):
        return FilterReason.COMMUTE_CAP, ()
    if any(leg.status is TravelStatus.MISSING for leg in hard):
        untested.append(FilterReason.COMMUTE_CAP)
    return None, tuple(untested)


def _commute_part(area_id: str, spec: PreferenceSpec, legs: tuple[CommuteLeg, ...]) -> _Part:
    if any(leg.utility is None for leg in legs):
        # The slowest cannot be known, so the whole component is missing.
        missing = fact_id(area_id, FactKind.MISSING, COMMUTE)
        return _Part(COMMUTE, spec.commute_weight, None, (missing,))
    utilities = [leg.utility for leg in legs if leg.utility is not None]
    slowest = min(utilities)
    utility = slowest if spec.commute_combine is Combine.SLOWEST else sum(utilities) / len(legs)
    # The leg that drove the score goes first: the lowest utility, and on a tie
    # the first in place order.
    driver = utilities.index(slowest)
    order = [driver, *(i for i in range(len(legs)) if i != driver)]
    facts = tuple(fact_id(area_id, FactKind.TRAVEL, travel_key(spec.commutes[i])) for i in order)
    return _Part(COMMUTE, spec.commute_weight, utility, facts)


def _parts(
    area_id: str,
    spec: PreferenceSpec,
    release: Release,
    legs: tuple[CommuteLeg, ...],
    fit: BudgetFit | None,
) -> tuple[_Part, ...]:
    """Every requested component, in the order sums run: commute, budget, features, tags."""
    parts: list[_Part] = []

    def part(component: str, weight: float, utility: float | None, kind: FactKind, key: str):
        found = kind if utility is not None else FactKind.MISSING
        name = key if utility is not None else component
        parts.append(_Part(component, weight, utility, (fact_id(area_id, found, name),)))

    if spec.commute_requested:
        parts.append(_commute_part(area_id, spec, legs))
    if spec.budget_requested:
        key = cost_key(spec.tenure, spec.budget.segment)
        part(BUDGET, spec.budget.weight, fit.utility if fit else None, FactKind.BUDGET_FIT, key)
    for weight in spec.active_weights:
        row = release.feature(area_id, weight.feature_id)
        utility = None
        if row is not None and row.percentile is not None:
            share = row.percentile / 100
            utility = share if weight.direction is Direction.MORE else 1 - share
        component = component_for_feature(weight.feature_id)
        part(component, weight.weight, utility, FactKind.FEATURE, weight.feature_id)
    for tag in spec.active_tags:
        score = release.tag(area_id, tag.tag_id)
        utility = None if score is None or score.score is None else score.score / 100
        part(component_for_tag(tag.tag_id), tag.weight, utility, FactKind.TAG, tag.tag_id)
    return tuple(parts)


def _fit(spec: PreferenceSpec, estimate: CostEstimate | None) -> BudgetFit | None:
    if spec.budget.amount is None or estimate is None:
        return None
    return BudgetFit(
        upper_quartile=estimate.upper_quartile,
        margin=spec.budget.amount - estimate.upper_quartile,
        utility=budget_utility(spec.budget.amount, estimate.upper_quartile),
        # Reported, and changes no arithmetic.
        confidence=estimate.confidence,
        as_of=estimate.as_of,
    )


def _present_weight(parts: tuple[_Part, ...]) -> float:
    return sum(p.weight for p in parts if p.utility is not None)


def _covered(parts: tuple[_Part, ...]) -> bool:
    """Whether enough of the weight asked for is present for the area to be scored.

    Counted in whole steps, as `canonical` counts them. A float sum of 0.3 and
    0.6 over 1.8 is a hair under a half, and must not be what decides.
    """
    present = sum(steps(p.weight) for p in parts if p.utility is not None)
    requested = sum(steps(p.weight) for p in parts)
    return present * WEIGHT_STEPS >= requested * steps(MIN_WEIGHT_COVERAGE)


def _contribution(part: _Part, present: float) -> float:
    return 0.0 if part.utility is None else part.weight / present * part.utility


def _out(value: float) -> float:
    return round(value, _OUT_DECIMALS)


def _ranked(scored: _Scored, rank: int) -> RankedArea:
    present = _present_weight(scored.parts)
    # Largest contribution first, then by name. Sorted before rounding.
    parts = sorted(
        scored.parts,
        key=lambda p: (-round(_contribution(p, present), _SORT_DECIMALS), p.component),
    )
    contributions = tuple(
        Contribution(
            component=p.component,
            present=p.utility is not None,
            weight=p.weight,
            share=0.0 if p.utility is None else _out(p.weight / present),
            utility=None if p.utility is None else _out(p.utility),
            contribution=_out(_contribution(p, present)),
            loss=0.0 if p.utility is None else _out(p.weight / present * (1 - p.utility)),
            fact_ids=p.fact_ids,
        )
        for p in parts
    )
    return RankedArea(
        area_id=scored.area_id,
        rank=rank,
        score=round(100 * scored.total, 2),
        weight_coverage=_out(scored.coverage),
        contributions=contributions,
        legs=tuple(
            leg.replace(utility=None if leg.utility is None else _out(leg.utility))
            for leg in scored.legs
        ),
        budget=scored.budget.replace(utility=_out(scored.budget.utility))
        if scored.budget
        else None,
        untested_filters=scored.untested,
    )


def _score(
    area: Neighbourhood, spec: PreferenceSpec, release: Release
) -> _Scored | Filtered | Unranked:
    area_id = area.area_id
    if not area.rankable:
        return Unranked(area_id=area_id, reason=UnrankedReason.NOT_RANKABLE)
    estimate = release.cost(area_id, spec.tenure, spec.budget.segment)
    legs = tuple(_leg(area_id, commute, spec, release) for commute in spec.commutes)
    caught, untested = _filter(area, spec, estimate, legs)
    if caught is not None:
        return Filtered(area_id=area_id, reason=caught)

    fit = _fit(spec, estimate)
    parts = _parts(area_id, spec, release, legs, fit)
    if not parts:
        # Nothing was asked for, so every area that passes the filters is as good as any.
        return _Scored(area_id, 0.0, 1.0, (), legs, fit, untested)
    present = _present_weight(parts)
    # An area with nothing present is not covered, so nothing is divided by zero.
    if not _covered(parts):
        return Unranked(area_id=area_id, reason=UnrankedReason.INSUFFICIENT_DATA)
    # The float is only what is reported. It never decides whether an area is scored.
    coverage = present / sum(p.weight for p in parts)
    total = sum(_contribution(p, present) for p in parts)
    return _Scored(area_id, total, coverage, parts, legs, fit, untested)


def rank(spec: PreferenceSpec, release: Release) -> RankResult:
    """Rank every area of the release for this spec.

    Every area appears in exactly one of `ranked`, `filtered` and `unranked`.
    Raises `SpecError` if the spec names something the release does not have.
    """
    problems = check_spec(spec, release)
    if problems:
        raise SpecError(problems)

    outcomes = [
        _score(area, spec, release)
        for area in sorted(release.neighbourhoods, key=lambda n: n.area_id)
    ]
    scored = sorted(
        (o for o in outcomes if isinstance(o, _Scored)),
        # Equal scores get different ranks; the id decides.
        key=lambda s: (-round(s.total, _SORT_DECIMALS), s.area_id),
    )
    return RankResult(
        spec_hash=spec_hash(spec),
        release_id=release.manifest.release_id,
        engine_version=ENGINE_VERSION,
        synthetic=release.manifest.synthetic,
        empty_spec=not (
            spec.commute_requested
            or spec.budget_requested
            or spec.active_weights
            or spec.active_tags
        ),
        ranked=tuple(_ranked(s, position) for position, s in enumerate(scored, start=1)),
        filtered=tuple(o for o in outcomes if isinstance(o, Filtered)),
        unranked=tuple(o for o in outcomes if isinstance(o, Unranked)),
    )
