"""Ranking: a pure function of a preference spec and a data release.

The same inputs give the same output on every call. It does no IO and reads no
clock. It ranks places by what is there. Of who lives somewhere, what reaches it
is their age and their households alone, as a share at Census 2021, and the
spec it is handed can ask for more of either and never for fewer
(ADR 0006). Missing data is never filled in: a component
with no figure for an area is dropped for that area, the remaining weights are
rebalanced, and the coverage is reported. An area with no figure for a thing
that was asked for is ranked, and stands below every area that has one: it is
never left out for it, and never scored as nought. An area with a figure for
under half of what counts, or for under half of the character that counts, is
not ranked among the others. It is listed apart, with what it lacks.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import Field

from burro_core._record import Record
from burro_core.catalogue import HOLDS_CRIME, default_direction
from burro_core.estimate import WORTH, estimate
from burro_core.facts import (
    cost_key,
    fact_id,
    journey_key,
    scored_on_just_missed,
    travel_key,
)
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
    JourneyBand,
    Mode,
    PlaceId,
    PtBasis,
    Strictness,
    TagId,
    TagShape,
    Toward,
    TravelStatus,
    UnrankedReason,
    component_for_feature,
    component_for_tag,
)
from burro_core.release import Band, CostEstimate, Neighbourhood, Release, TagValue
from burro_core.spec import (
    DEFAULT_WEIGHTS,
    WEIGHT_STEPS,
    Commute,
    PreferenceSpec,
    SpecError,
    TagWeight,
    check_spec,
    given_way,
    spec_hash,
    steps,
)

# Any change to the arithmetic in this module bumps it, and so does a change to a
# rule of the reducer or to a rule of what an explanation says. 1.4.0 ranks a
# vibe towards either end, scores the journeys on the legs that have a time,
# and says a reason and a trade-off each from its own side. 1.5.0 ranks an
# area only where it has a figure for half of the character that counts.
# 1.6.0 says a vibe in short in an explanation. 1.7.0 shows a vibe nobody
# asked for on a result only where the area has more of it than most. 1.8.0
# is the engine of the vibes and the engine of the first real builds, joined:
# it moves no arithmetic, and one number names what both had become. 1.9.0
# turns away a wish for what the release holds for no area: a vibe no area has
# a band for, a budget where it holds no cost, a journey where it names no
# place. It moves no arithmetic either. 1.10.0 is that engine joined with the
# one that holds a budget against the median of a cost that has no range. It
# moves no result of a release whose costs all have one. 1.11.0 lets what is
# said of the place lead: a journey weighs 0.40 and a budget 0.30 until a person
# moves them, where they weighed 1.00 and 0.80. It moves no arithmetic, and a
# search that holds its own weights, as a share does, is ranked as it was.
# 1.12.0 puts an area with no figure for a thing that was asked for below every
# area that has one. Its fit is worked out as it was. 1.13.0 estimates a journey
# by public transport from distance where a release holds no time for it and
# says where the homes of the area stand: it is said as a band against the
# limit, a firm limit leaves out only what is likely beyond it, and a flexible
# one counts the band. It moves no result of a release that holds its times.
# In the same version a firm budget leaves an area out on a median only where
# the median is over the budget by more than `FIRM_BUDGET_MARGIN_PERCENT`, and
# it is said beside a median that is over the budget that about half of the
# homes sold for less. It moves no result of a release whose costs all have a
# range. 1.13.0 is one number for both. 1.14.0 holds a budget to rent against the
# middle rent of the place a rent is of, where a release says that a rent is of a
# postcode district or a borough: a firm budget has the same margin there, and the
# sentence says the place. It moves no result of a release whose rents are each of
# the area alone. In the same version an estimated journey is called likely within
# its limit only where the estimate is 10 minutes or more under it, where it was 5:
# the founder decided so on 2026-09-25, once the estimate had been held against
# timetables. What is likely beyond a limit is what it was, so a firm limit leaves
# out no more than it did. It moves no result of a release that holds its times.
# In the same version a cost is said to be at a budget, and a journey at its limit,
# where the difference is nothing: no fact gives a difference of nothing as a
# figure. It moves no result. 1.14.0 is one number for the three: nothing past
# 1.13.0 had been served when they were joined.
ENGINE_VERSION = "1.14.0"

FULL_UNTIL_MIN = 15  # a journey this short is as good as any shorter
FULL_UNTIL_SHARE = 0.5  # unless that is more than half the cap
UTILITY_AT_CAP = 0.5  # a journey exactly at the cap is half as good as a short one
ZERO_AT_SHARE = 1.5  # a journey half as long again as the cap is worth nothing
# A home a quarter over budget is worth nothing. A range that Burro worked out is
# tested against its upper quartile. Where a cost has no range it is tested against the
# median, as it is written: nothing is put in the place of a quartile that no source
# gives. A rent that is of a wider place is tested against its median too: it is the
# middle of the rents that were recorded there, and about half were let for less.
BUDGET_OVER_SHARE = 0.25
# How far over a firm budget the median of an area may be, in hundredths of the budget,
# before the budget leaves the area out. It is held against a cost that is one number, a
# median of what sold, and against the median of a rent that is of a wider place. It is
# held against no range that is of the area alone.
#
# Half of the homes behind a median sold for less than it. So an area whose median is a
# little over a budget is one where many homes sold within it, and a firm budget that
# left it out on the median left out places a person could buy in. How many sold within
# it falls as the median rises: of the flats sold in London from 2023 to 2025, with a
# budget of 400,000, about half sold within it where the median stood at the budget, about
# a quarter where the median stood a quarter over it, and fewer beyond. A quarter over is
# also where a flexible budget counts an area for nothing (`BUDGET_OVER_SHARE`), so a firm
# budget leaves out what a flexible one would give no credit to, and no more. And a
# person who names a size, as a flat of one bedroom, is held against homes of every size,
# of which the smaller sold for less than the middle. It is a first figure, and the
# founder's to change: this is the one place it is written.
FIRM_BUDGET_MARGIN_PERCENT = 25
# Below this share of the requested weight, an area is not scored. It is
# compared in whole steps of weight, so that an area with exactly this share
# present is scored however the weight is split between its components.
MIN_WEIGHT_COVERAGE = 0.5
# The same share, of the character that counts alone: the features and the
# vibes of the spec, apart from the journeys and the budget. A journey and a
# budget are over half of almost any search, so an area with a journey time
# and a rent passed the floor above with no figure for anything that was
# asked of the place itself, and came first.
MIN_CHARACTER_COVERAGE = 0.5
# A result shows the vibes that were asked for, and then a few it sits far from
# the middle on. They are shown and never scored.
STRIP_ASKED = 4
STRIP_OTHERS = 2

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
    # Where the journey stands against its limit, where its status is `estimated`: the
    # release holds no time for it, and one was estimated from distance. It is never
    # given in minutes. `None` for every other journey.
    estimate: JourneyBand | None = None


class BudgetFit(Record):
    # None where the budget was held against the median: the cost has no range, or is of
    # a wider place than the area. The margin is then to the median.
    upper_quartile: int | None
    margin: int
    utility: float
    confidence: Confidence
    as_of: str


class StripMark(Record):
    """Where an area sits on one vibe, for the strip under its name. Shown, never scored."""

    tag_id: TagId
    band: Band
    spread_low: Band
    spread_high: Band
    # Whether the vibe is in the spec, and if so towards which end.
    asked: bool
    toward: Toward | None
    # The `tag` fact that holds the sentence, the sources and the date.
    fact_id: str


class RankedArea(Record):
    area_id: AreaId
    rank: int = Field(ge=1)
    score: float = Field(ge=0, le=100)
    weight_coverage: float = Field(ge=0, le=1)
    contributions: tuple[Contribution, ...]
    legs: tuple[CommuteLeg, ...]
    budget: BudgetFit | None
    untested_filters: tuple[FilterReason, ...]
    strip: tuple[StripMark, ...]

    @property
    def counted(self) -> int:
        """How many things count in the spec."""
        return len(self.contributions)

    @property
    def present(self) -> int:
        """For how many of them this area has a figure."""
        return sum(1 for contribution in self.contributions if contribution.present)


class Filtered(Record):
    area_id: AreaId
    reason: FilterReason


class Unranked(Record):
    area_id: AreaId
    reason: UnrankedReason
    # Every component the search asks for that the area has no figure for, in
    # the order the sums run. Empty for an area that is not rankable: it was
    # never scored, so nothing is said of what it lacks.
    missing: tuple[str, ...]


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


def held_on_the_median(estimate: CostEstimate) -> bool:
    """Whether a budget is held against the median of a cost, and not against an upper end.

    It is of a cost that is one number, which has no upper end, and of a rent
    that is of a wider place. Such a rent is the middle of the rents that were
    recorded in a postcode district or a borough: about half were let for
    less, and its upper end says how widely the rents of the place spread and
    nothing of the area.
    """
    return estimate.upper_quartile is None or estimate.of_a_wider_place


def budget_held_against(estimate: CostEstimate) -> int:
    """The figure of a cost that a budget is held against.

    The upper quartile of a range that is of the area alone. Where a cost has
    no range, or is of a wider place, it is the median, to the pound: it is
    never raised to stand for a quartile, and never scaled to a size of home
    that the source gives no figure for.
    """
    if held_on_the_median(estimate) or estimate.upper_quartile is None:
        return estimate.median
    return estimate.upper_quartile


def over_a_firm_budget(estimate: CostEstimate, amount: int) -> bool:
    """Whether a firm budget leaves out an area whose home costs this.

    A range that is of the area alone is over the budget where its upper
    quartile is. A median is over it only where it is more than
    `FIRM_BUDGET_MARGIN_PERCENT` in 100 over, whether it is of what sold or
    of the rents of a wider place: about half of the homes behind a median
    went for less than it. It is counted in whole pounds, so that no float
    decides which side of the line an area falls.
    """
    if held_on_the_median(estimate) or estimate.upper_quartile is None:
        return 100 * estimate.median > (100 + FIRM_BUDGET_MARGIN_PERCENT) * amount
    return estimate.upper_quartile > amount


def budget_utility(amount: int, upper_quartile: int) -> float:
    """1 when the upper quartile is within budget, falling to 0 at a quarter over.

    Being further under budget earns nothing: Burro gives no affordability verdict.
    Of a cost with no range it is given the median: `budget_held_against`.
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
    strip: tuple[StripMark, ...] = ()

    def lacks(self, asked: frozenset[str]) -> bool:
        """Whether the area has no figure for a thing that was asked for."""
        return any(part.utility is None and part.component in asked for part in self.parts)


def _leg(area_id: str, commute: Commute, spec: PreferenceSpec, release: Release) -> CommuteLeg:
    place = release.place(commute.place_id)
    destination = place.destination_id if place else ""
    typical = release.travel(area_id, destination, commute.mode, PtBasis.TYPICAL)
    missed = release.travel(area_id, destination, commute.mode, PtBasis.JUST_MISSED)
    scored = missed if scored_on_just_missed(commute, spec) else typical
    if scored.status is TravelStatus.MISSING:
        # No time is held. Where one can be estimated from distance, it is, and is
        # said as a band: a time that a release holds always takes its place.
        band = estimate(release, area_id, commute.place_id, commute.mode, commute.max_minutes)
        if band is not None:
            return CommuteLeg(
                place_id=commute.place_id,
                mode=commute.mode,
                status=TravelStatus.ESTIMATED,
                minutes=None,
                minutes_typical=None,
                minutes_just_missed=None,
                utility=WORTH[band] if spec.commute_requested else None,
                estimate=band,
            )
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
        elif over_a_firm_budget(estimate, amount):
            return FilterReason.OVER_BUDGET, ()
    hard = [
        leg
        for leg, commute in zip(legs, spec.commutes, strict=True)
        if commute.strictness is Strictness.HARD
    ]
    caps = {commute.place_id: commute for commute in spec.commutes}
    if any(_over_cap(leg, caps[leg.place_id]) for leg in hard):
        return FilterReason.COMMUTE_CAP, ()
    # A firm limit leaves out only what an estimate puts well beyond it. What is
    # borderline stays: the estimate is too rough to leave an area out on.
    if any(leg.estimate is JourneyBand.LIKELY_BEYOND for leg in hard):
        return FilterReason.COMMUTE_LIKELY_BEYOND, ()
    if any(leg.status is TravelStatus.MISSING for leg in hard):
        untested.append(FilterReason.COMMUTE_CAP)
    return None, tuple(untested)


def _commute_part(area_id: str, spec: PreferenceSpec, legs: tuple[CommuteLeg, ...]) -> _Part:
    """The journeys, scored on the legs that have a time.

    A leg with no time is left out of the score and said to be missing. It
    does not take the legs that have one out with it: an area 63 minutes
    from a workplace, against a limit of 35, once ranked first because
    another journey had no figure. The component is missing only when no
    leg has a time.
    """
    timed = [(i, leg.utility) for i, leg in enumerate(legs) if leg.utility is not None]
    missing = tuple(
        fact_id(area_id, FactKind.MISSING, journey_key(spec.commutes[i]))
        for i, leg in enumerate(legs)
        if leg.utility is None
    )
    if not timed:
        return _Part(COMMUTE, spec.commute_weight, None, missing)
    utilities = [utility for _, utility in timed]
    slowest = min(utilities)
    utility = slowest if spec.commute_combine is Combine.SLOWEST else sum(utilities) / len(timed)
    # The leg that drove the score goes first: the lowest utility, and on a tie
    # the first in place order.
    driver = timed[utilities.index(slowest)][0]
    order = [driver, *(i for i, _ in timed if i != driver)]
    facts = tuple(fact_id(area_id, FactKind.TRAVEL, travel_key(spec.commutes[i])) for i in order)
    return _Part(COMMUTE, spec.commute_weight, utility, (*facts, *missing))


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
        part(
            component_for_tag(tag.tag_id),
            tag.weight,
            tag_utility(release.tag(area_id, tag.tag_id), tag.toward),
            FactKind.TAG,
            tag.tag_id,
        )
    return tuple(parts)


def tag_utility(row: TagValue | None, toward: Toward) -> float | None:
    """What an area is worth on a vibe, towards the end that was asked for.

    Towards the high end it is `score / 100`, and towards the low end one
    less that, so the same spec with the end turned reverses the order on
    that vibe alone. The band and the spread are for showing and never
    change a rank.
    """
    if row is None or row.score is None:
        return None
    share = row.score / 100
    return share if toward is Toward.HIGH else 1 - share


def _mark(area_id: str, row: TagValue | None, asked: TagWeight | None) -> StripMark | None:
    if row is None or row.band is None or row.spread_low is None or row.spread_high is None:
        return None  # a vibe the area cannot be placed on is left out
    return StripMark(
        tag_id=row.tag_id,
        band=row.band,
        spread_low=row.spread_low,
        spread_high=row.spread_high,
        asked=asked is not None,
        toward=asked.toward if asked else None,
        fact_id=fact_id(area_id, FactKind.TAG, row.tag_id),
    )


def strip_of(area_id: str, spec: PreferenceSpec, release: Release) -> tuple[StripMark, ...]:
    """The vibes shown under a result's name. It is worked out after ranking and changes none.

    First the vibes of the spec, heaviest first, then by id. Then a few
    others the release lets a result show, on which the area sits furthest
    from the middle: band 1 or 5 first, then 2 or 4, by id.

    Of those others, a vibe that runs one way is shown only where the area
    has more of it than most, in band 4 or 5. At its least it read as a
    warning on a result, about a thing nobody had asked for. A scale has no
    lesser end, and is shown towards either. A vibe that was asked for is
    shown wherever the area sits on it.

    A vibe whose recipe holds recorded crime is never among the others:
    recorded crime counts, and is shown, only where a person asks for it.
    """
    asked = sorted(spec.active_tags, key=lambda tag: (-tag.weight, tag.tag_id))
    first = [_mark(area_id, release.tag(area_id, tag.tag_id), tag) for tag in asked]
    shown = [mark for mark in first if mark is not None][:STRIP_ASKED]
    taken = {tag.tag_id for tag in asked}
    others = [
        mark
        for vibe in release.vibes
        if vibe.strip and vibe.tag_id not in taken and vibe.tag_id not in HOLDS_CRIME
        for mark in [_mark(area_id, release.tag(area_id, vibe.tag_id), None)]
        if mark is not None and mark.band != 3 and (vibe.shape is TagShape.SCALE or mark.band > 3)
    ]
    others.sort(key=lambda mark: (mark.band in (2, 4), mark.tag_id))
    return (*shown, *others[:STRIP_OTHERS])


def _fit(spec: PreferenceSpec, estimate: CostEstimate | None) -> BudgetFit | None:
    if spec.budget.amount is None or estimate is None:
        return None
    held = budget_held_against(estimate)
    return BudgetFit(
        upper_quartile=None if held_on_the_median(estimate) else estimate.upper_quartile,
        margin=spec.budget.amount - held,
        utility=budget_utility(spec.budget.amount, held),
        # Reported, and changes no arithmetic.
        confidence=estimate.confidence,
        as_of=estimate.as_of,
    )


def _present_weight(parts: tuple[_Part, ...]) -> float:
    return sum(p.weight for p in parts if p.utility is not None)


def _covered(parts: Sequence[_Part], least: float = MIN_WEIGHT_COVERAGE) -> bool:
    """Whether enough of the weight asked for is present for the area to be scored.

    Counted in whole steps, as `canonical` counts them. A float sum of 0.3 and
    0.6 over 1.8 is a hair under a half, and must not be what decides.
    """
    present = sum(steps(p.weight) for p in parts if p.utility is not None)
    requested = sum(steps(p.weight) for p in parts)
    return present * WEIGHT_STEPS >= requested * steps(least)


def _character(parts: Sequence[_Part]) -> list[_Part]:
    """What is asked of the place itself: every feature and vibe that counts.

    It is every one of them, whoever chose it, a default among them. Two
    specs with one canonical form rank the same, and a canonical form holds
    no provenance, so who chose a weight can never decide what is ranked.
    """
    return [p for p in parts if p.component not in (COMMUTE, BUDGET)]


def _unranked_for(parts: Sequence[_Part]) -> UnrankedReason | None:
    """Why an area is not ranked among the others, if it is not.

    Too little of the whole comes first. Then too little of the character: a
    journey and a rent never stand in for what was asked of the place
    itself. An area with nothing present is covered on neither count, so
    nothing is divided by zero.
    """
    if not _covered(parts):
        return UnrankedReason.INSUFFICIENT_DATA
    if not _covered(_character(parts), MIN_CHARACTER_COVERAGE):
        return UnrankedReason.CHARACTER_UNKNOWN
    return None


def asked_for(spec: PreferenceSpec) -> frozenset[str]:
    """The components of a search that somebody asked for: all but its usual settings.

    A usual setting is a measure the tenure weighs by default that stands as
    nobody chose it: the way the default runs, at the weight of the default or
    at what that gives way to once a wish is applied. It is read from the
    weight and never from who set it, because two specs with one canonical
    form rank the same. A journey, a budget and a vibe are never a usual
    setting: no search holds one until a person asks.
    """
    usual = DEFAULT_WEIGHTS[spec.tenure]
    asked = {component_for_tag(tag.tag_id) for tag in spec.active_tags}
    asked |= {
        component_for_feature(weight.feature_id)
        for weight in spec.active_weights
        if weight.feature_id not in usual
        or weight.direction is not default_direction(weight.feature_id)
        or steps(weight.weight)
        not in (steps(usual[weight.feature_id]), steps(given_way(usual[weight.feature_id])))
    }
    if spec.commute_requested:
        asked.add(COMMUTE)
    if spec.budget_requested:
        asked.add(BUDGET)
    return frozenset(asked)


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
        strip=scored.strip,
    )


def _score(
    area: Neighbourhood, spec: PreferenceSpec, release: Release
) -> _Scored | Filtered | Unranked:
    area_id = area.area_id
    if not area.rankable:
        return Unranked(area_id=area_id, reason=UnrankedReason.NOT_RANKABLE, missing=())
    estimate = release.cost(area_id, spec.tenure, spec.budget.segment)
    legs = tuple(_leg(area_id, commute, spec, release) for commute in spec.commutes)
    caught, untested = _filter(area, spec, estimate, legs)
    if caught is not None:
        return Filtered(area_id=area_id, reason=caught)

    fit = _fit(spec, estimate)
    parts = _parts(area_id, spec, release, legs, fit)
    strip = strip_of(area_id, spec, release)
    if not parts:
        # Nothing was asked for, so every area that passes the filters is as good as any.
        return _Scored(area_id, 0.0, 1.0, (), legs, fit, untested, strip)
    reason = _unranked_for(parts)
    if reason is not None:
        lacking = tuple(p.component for p in parts if p.utility is None)
        return Unranked(area_id=area_id, reason=reason, missing=lacking)
    present = _present_weight(parts)
    # The float is only what is reported. It never decides whether an area is scored.
    coverage = present / sum(p.weight for p in parts)
    total = sum(_contribution(p, present) for p in parts)
    return _Scored(area_id, total, coverage, parts, legs, fit, untested, strip)


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
    asked = asked_for(spec)
    scored = sorted(
        (o for o in outcomes if isinstance(o, _Scored)),
        # An area with no figure for a thing that was asked for stands below every area
        # that has one, whatever its fit on the rest: decided on 2026-09-24. Its fit
        # leaves the thing out, so it says nothing of it, and the area came first for a
        # person who had asked for that very thing. A usual setting with no figure moves
        # no area. Equal scores get different ranks; the id decides.
        key=lambda s: (s.lacks(asked), -round(s.total, _SORT_DECIMALS), s.area_id),
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
