"""Ranking the committed synthetic release: different wishes find visibly different places.

Each case says what a person asks for, which made-up areas they would expect
to be shown first, and why. The areas have the character `names.py` gives
them, so an expectation here can be checked against that plan by eye.
"""

from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pytest
from burro_core import InterpretRequest, RuleInterpreter, apply, default_spec, rank
from burro_core.ids import (
    Direction,
    FeatureId,
    FilterReason,
    Mode,
    Provenance,
    Segment,
    Strictness,
    TagId,
    Tenure,
    UnrankedReason,
)
from burro_core.rank import RankedArea, RankResult
from burro_core.release import InMemoryRelease
from burro_core.spec import Budget, Commute, FeatureWeight, PreferenceSpec, TagWeight
from burro_pipeline.release import build_synthetic, read_release
from burro_pipeline.release.synthetic import RELEASE_ID

FIXTURE = Path(__file__).parents[3] / "data" / "fixtures" / "synthetic" / RELEASE_ID
STATED = Provenance.STATED


@cache
def release() -> InMemoryRelease:
    return read_release(FIXTURE)


def name_of(area_id: str) -> str:
    found = release().neighbourhood(area_id)
    assert found is not None
    return found.name


def commute(place: str, minutes: int, mode: Mode = Mode.PT, hard: bool = False) -> Commute:
    return Commute(
        place_id=next(p.place_id for p in release().places if p.name == place),
        mode=mode,
        max_minutes=minutes,
        strictness=Strictness.HARD if hard else Strictness.SOFT,
        provenance=STATED,
    )


def asking(
    tenure: Tenure = Tenure.RENT,
    budget: tuple[int, Segment] | None = None,
    hard_budget: bool = False,
    commutes: tuple[Commute, ...] = (),
    tags: dict[TagId, float] | None = None,
    weights: dict[FeatureId, float] | None = None,
) -> PreferenceSpec:
    """A spec that weights what is named and nothing else, so each case stands on its own.

    A journey and a budget each weigh all they can, whatever a search gives them at first.
    """
    base = default_spec(tenure)
    return base.replace(
        commute_weight=1.0,
        commute_weight_from=STATED,
        budget=Budget(
            amount=budget[0] if budget else None,
            segment=budget[1] if budget else base.budget.segment,
            strictness=Strictness.HARD if hard_budget else Strictness.SOFT,
            weight=1.0,
            provenance=STATED,
        ),
        commutes=commutes,
        tags=tuple(
            TagWeight(tag_id=tag_id, weight=weight, provenance=STATED)
            for tag_id, weight in (tags or {}).items()
        ),
        weights=tuple(
            FeatureWeight(
                feature_id=feature_id, weight=weight, direction=Direction.MORE, provenance=STATED
            )
            for feature_id, weight in (weights or {}).items()
        ),
    )


@dataclass(frozen=True)
class Case:
    asks_for: str
    spec: PreferenceSpec
    first: tuple[str, ...]  # the areas expected at the top, in any order
    because: str
    above_all: str  # what they care most about, which the area ranked first must do well on
    not_for_them: str  # an area that belongs in the bottom third


def cases() -> list[Case]:
    return [
        Case(
            "somewhere leafy and quiet",
            asking(tags={TagId.LEAFY: 1.0, TagId.QUIET_RESIDENTIAL: 0.8}),
            first=("Alderwick", "Larkspur Hill", "Gorsebeck"),
            because="they are the north-western edge of the city: green, built low, and a "
            "long way from anything that is open in the evening",
            above_all="tag:leafy",
            not_for_them="Pellam Cross",
        ),
        Case(
            "bars, restaurants and things to do at night",
            asking(
                tags={TagId.PACE: 1.0},
                weights={
                    FeatureId.VENUE_EVENING: 0.7,
                    FeatureId.CULTURE_VENUES_PER_HOMES: 0.5,
                },
            ),
            first=("Pellam Cross", "Lantern Yard"),
            because="the centre and the nightlife quarter one stop north of it hold more of "
            "the city's venues than anywhere else",
            above_all="tag:pace",
            not_for_them="Alderwick",
        ),
        Case(
            "a one-bed for £1,350 a month, within 45 minutes of Pellam Cross",
            asking(budget=(1350, Segment.BED_1), commutes=(commute("Pellam Cross", 45),)),
            first=("Cindermoor", "Farrowmere"),
            because="they are cheap and each is the far end of a line, so the rent fits and "
            "the train still reaches the centre in half an hour",
            above_all="budget",
            not_for_them="Larkspur Hill",
        ),
        Case(
            "old streets with some history, and the river close by",
            asking(tags={TagId.BUILT_AGE: 1.0}, weights={FeatureId.WATER_ACCESS: 0.6}),
            first=("Tallowgate",),
            because="the old town has the oldest homes and the most protected streets in "
            "the city, and it stands on the north bank",
            above_all="tag:built_age",
            not_for_them="Farrowmere",
        ),
        Case(
            "a family house to buy for £800,000, near schools, working at the hospital",
            asking(
                tenure=Tenure.BUY,
                budget=(800_000, Segment.SEMI_DETACHED),
                commutes=(commute("Dulcimer Green Hospital", 40),),
                tags={TagId.FAMILY_AMENITIES: 1.0},
                weights={FeatureId.SCHOOL_SECONDARY_ATTAINMENT: 0.5},
            ),
            first=("Dulcimer Green",),
            because="it has the most schools and play space of any area, houses at that "
            "price, and the hospital is in it",
            above_all="tag:family_amenities",
            not_for_them="Lantern Yard",
        ),
        Case(
            "to cycle to the university in 15 minutes and reach Pellam Exchange in 30",
            asking(
                commutes=(
                    commute("Wexmoor University", 15, Mode.CYCLE),
                    commute("Pellam Exchange", 30),
                )
            ),
            first=("Wexmoor",),
            because="it is around the campus and two stops from the centre. The centre is "
            "minutes from Pellam Exchange but a longer ride from the campus, and the slower "
            "journey decides",
            above_all="commute",
            not_for_them="Wickerford",
        ),
    ]


def check(case: Case, found: InMemoryRelease) -> None:
    result = rank(case.spec, found)
    order = [name_of(area.area_id) for area in result.ranked]
    top = order[: len(case.first)]
    assert set(top) == set(case.first), f"expected {case.first} first because {case.because}"
    served = {c.component: c.utility for c in result.ranked[0].contributions}
    assert (served[case.above_all] or 0) >= 0.85
    assert order.index(case.not_for_them) >= len(order) * 2 // 3, order


@pytest.mark.parametrize("case", cases(), ids=lambda case: case.asks_for)
def test_the_first_areas_are_the_ones_a_person_would_expect(case: Case):
    check(case, release())


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_what_a_person_would_expect_comes_from_the_plan_and_not_from_the_seed(seed: int):
    # The seed moves every figure a little. If that changed who comes first, the
    # expectations above would be luck, and the next change to the plan would break them.
    redrawn = build_synthetic(seed)
    for case in cases():
        check(case, redrawn)


def test_no_two_of_the_wishes_are_answered_with_the_same_area():
    firsts = [name_of(rank(case.spec, release()).ranked[0].area_id) for case in cases()]
    assert len(set(firsts)) == len(firsts), firsts


def test_words_about_the_made_up_city_reach_a_ranking_with_no_model():
    text = "Renting a one bed for £1,200 a month, 45 minutes to Pellam Cross, not Cindermoor"
    start = default_spec(Tenure.RENT)
    read = RuleInterpreter().interpret(InterpretRequest(text=text, spec=start, release=release()))
    reduced = apply(start, read.operations, release())
    # Every name in it was found in the release, so no edit was turned away.
    assert (read.status.value, read.unmet, read.clarify, reduced.rejected) == ("ok", (), (), ())
    spec = reduced.spec
    assert (spec.budget.amount, spec.budget.segment) == (1200, Segment.BED_1)
    assert spec.commutes == (commute("Pellam Cross", 45).replace(provenance=Provenance.STATED),)
    result = rank(spec, release())
    assert [(name_of(f.area_id), f.reason) for f in result.filtered] == [
        ("Cindermoor", FilterReason.EXCLUDED)
    ]
    # The new town has a journey time and a rent and little else, so it is
    # listed apart from the areas that can be placed on what counts.
    assert len(result.ranked) == 20
    assert [(name_of(u.area_id), u.reason) for u in result.unranked if u.missing] == [
        ("Otterby Fields", UnrankedReason.CHARACTER_UNKNOWN)
    ]


def ranked(result: RankResult, name: str) -> RankedArea:
    return next(area for area in result.ranked if name_of(area.area_id) == name)


def test_the_slower_of_two_journeys_decides_how_the_centre_ranks():
    two = cases()[-1].spec
    centre = ranked(rank(two, release()), "Pellam Cross")
    to_the_exchange, to_the_campus = centre.legs
    assert (to_the_exchange.mode, to_the_campus.mode) == (Mode.PT, Mode.CYCLE)
    # Minutes from Pellam Exchange, and still marked down for the ride to the campus.
    assert to_the_exchange.utility == 1.0
    assert to_the_campus.utility is not None and to_the_campus.utility < 1.0
    assert centre.score == round(100 * to_the_campus.utility, 2)
    assert centre.contributions[0].fact_ids[0].endswith(f"{to_the_campus.place_id}.cycle")


def test_an_area_with_no_cost_estimate_is_ranked_on_the_rest_and_says_so():
    cheap = asking(
        budget=(1200, Segment.BED_1),
        hard_budget=True,
        commutes=(commute("Pellam Cross", 45, hard=True),),
    )
    result = rank(cheap, release())
    # Only what is known to fail is filtered. Ostrel Vale has no estimate, so it stays.
    assert [name_of(area.area_id) for area in result.ranked] == ["Cindermoor", "Ostrel Vale"]
    vale = ranked(result, "Ostrel Vale")
    assert vale.budget is None
    assert vale.weight_coverage == 0.5
    assert vale.untested_filters == (FilterReason.OVER_BUDGET,)
    reasons = {name_of(found.area_id): found.reason for found in result.filtered}
    assert set(reasons.values()) == {FilterReason.OVER_BUDGET}
    assert len(reasons) == 20


def test_an_area_most_surveys_have_not_reached_is_left_unranked_and_not_guessed_at():
    by_default = rank(default_spec(Tenure.RENT), release())
    unranked = {name_of(found.area_id): found.reason for found in by_default.unranked}
    assert unranked == {
        "Grapnel Dock": UnrankedReason.NOT_RANKABLE,
        "Otterby Fields": UnrankedReason.INSUFFICIENT_DATA,
        "Sedgewater Marsh": UnrankedReason.NOT_RANKABLE,
    }
    # Asked only about what is known of it, the same area is ranked like any other.
    known = asking(tags={TagId.HOMES: 1.0}, weights={FeatureId.WATER_ACCESS: 0.5})
    assert ranked(rank(known, release()), "Otterby Fields").weight_coverage == 1.0


def test_a_missing_figure_is_dropped_for_that_area_and_the_coverage_reported():
    green = asking(weights={FeatureId.GREEN_COVER: 0.6}, tags={TagId.LEAFY: 0.4})
    result = rank(green, release())
    # Otterby Fields has a figure for its public green space and none for its
    # gardens or its woodland, so it cannot be placed on Leafy.
    otterby = ranked(result, "Otterby Fields")
    assert otterby.weight_coverage == 0.6
    dropped = [c for c in otterby.contributions if not c.present]
    assert [(c.component, c.utility, c.share) for c in dropped] == [("tag:leafy", None, 0.0)]
    assert ranked(result, "Wickerford").weight_coverage == 1.0
    # A recipe that is short of one part still places an area: Gorsebeck has no
    # conservation figure, and is placed on Built age by the parts it has.
    built = release().tag(otterby.area_id.replace("0017", "0008"), TagId.BUILT_AGE)
    assert built is not None and name_of(built.area_id) == "Gorsebeck"
    assert (built.coverage, built.band is not None) == (0.75, True)


def test_a_journey_that_was_never_computed_drops_the_commute_and_is_not_scored_as_zero():
    to_campus = asking(
        commutes=(commute("Wexmoor University", 60),), tags={TagId.QUIET_RESIDENTIAL: 1.0}
    )
    gorsebeck = ranked(rank(to_campus, release()), "Gorsebeck")
    assert gorsebeck.weight_coverage == 0.5
    assert [(leg.minutes, leg.utility) for leg in gorsebeck.legs] == [(None, None)]
    # All of its score comes from how quiet it is, which is very.
    assert gorsebeck.score > 75
