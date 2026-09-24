import dataclasses
from itertools import pairwise

import pytest
from burro_core.ids import (
    AreaRuleKind,
    Combine,
    Direction,
    FeatureId,
    FilterReason,
    Mode,
    Provenance,
    PtBasis,
    Strictness,
    TagId,
    Tenure,
    TravelStatus,
    UnrankedReason,
)
from burro_core.rank import (
    ENGINE_VERSION,
    MIN_WEIGHT_COVERAGE,
    RankedArea,
    RankResult,
    _contribution,  # pyright: ignore[reportPrivateUsage]
    _present_weight,  # pyright: ignore[reportPrivateUsage]
    _score,  # pyright: ignore[reportPrivateUsage]
    _Scored,  # pyright: ignore[reportPrivateUsage]
    budget_utility,
    commute_utility,
    rank,
)
from burro_core.release import InMemoryRelease, TravelTable
from burro_core.spec import (
    AreaRule,
    FeatureWeight,
    PreferenceSpec,
    TagWeight,
    default_spec,
    spec_hash,
    steps,
)

from .support import (
    WORKED,
    area_id,
    build_worked_release,
    build_worked_spec,
    cost,
    draws,
    feature_value,
    metric,
    place_id,
    random_spec,
    small_release,
    travel_table,
)

ALDERWICK, BRACKENHYTHE, CINDERMOOR, DULCIMER_GREEN = (area_id(n) for n in range(1, 5))


def by_area(result: RankResult) -> dict[str, RankedArea]:
    return {area.area_id: area for area in result.ranked}


def cells(area: RankedArea) -> dict[str, tuple[float, float | None, float]]:
    return {c.component: (c.share, c.utility, c.contribution) for c in area.contributions}


def worked_with(**changes: object) -> InMemoryRelease:
    return dataclasses.replace(build_worked_release(), **changes)  # pyright: ignore[reportArgumentType]


def times(*rows: tuple[int | None, int | None]) -> TravelTable:
    return travel_table(4, 2, rows)


def test_worked_example_ranks_as_the_contract_says():
    result = rank(build_worked_spec(), build_worked_release())

    assert [a.area_id for a in result.ranked] == [ALDERWICK, CINDERMOOR, BRACKENHYTHE]
    assert [a.rank for a in result.ranked] == [1, 2, 3]
    assert [(f.area_id, f.reason) for f in result.filtered] == [(DULCIMER_GREEN, "commute_cap")]
    assert result.unranked == ()
    assert not result.empty_spec

    areas = by_area(result)
    assert [areas[a].score for a in (ALDERWICK, BRACKENHYTHE, CINDERMOOR)] == [78.10, 54.81, 75.23]
    assert [areas[a].weight_coverage for a in (ALDERWICK, BRACKENHYTHE, CINDERMOOR)] == [1, 0.9, 1]

    # Each cell is share, utility, contribution, as section 6.8 prints them.
    assert cells(areas[ALDERWICK]) == {
        "commute": (0.3333, 0.6600, 0.2200),
        "budget": (0.2667, 1.0000, 0.2667),
        "feature:park_proximity": (0.1667, 0.8000, 0.1333),
        "feature:noise_exposure": (0.1000, 0.6500, 0.0650),
        "tag:leafy": (0.1333, 0.7200, 0.0960),
    }
    assert cells(areas[BRACKENHYTHE]) == {
        "commute": (0.3704, 0.5667, 0.2099),
        "budget": (0.2963, 0.6667, 0.1975),
        "feature:park_proximity": (0.1852, 0.4000, 0.0741),
        "feature:noise_exposure": (0.0, None, 0.0),
        "tag:leafy": (0.1481, 0.4500, 0.0667),
    }
    assert cells(areas[CINDERMOOR]) == {
        "commute": (0.3333, 0.4000, 0.1333),
        "budget": (0.2667, 1.0000, 0.2667),
        "feature:park_proximity": (0.1667, 0.9000, 0.1500),
        "feature:noise_exposure": (0.1000, 0.8500, 0.0850),
        "tag:leafy": (0.1333, 0.8800, 0.1173),
    }
    assert {c.component: c.loss for c in areas[ALDERWICK].contributions} == {
        "commute": 0.1133,
        "tag:leafy": 0.0373,
        "feature:noise_exposure": 0.0350,
        "feature:park_proximity": 0.0333,
        "budget": 0,
    }

    # The legs, and which of them drove the score.
    utilities = {a: [leg.utility for leg in areas[a].legs] for a in areas}
    assert utilities == {
        ALDERWICK: [0.6600, 0.7000],
        BRACKENHYTHE: [0.9400, 0.5667],
        CINDERMOOR: [0.4000, 0.7667],
    }
    margins = {a: (b.margin, b.utility) for a in areas if (b := areas[a].budget) is not None}
    assert margins == {ALDERWICK: (50, 1.0), BRACKENHYTHE: (-150, 0.6667), CINDERMOOR: (300, 1.0)}


def test_the_result_records_what_it_was_ranked_from():
    spec = build_worked_spec()
    result = rank(spec, build_worked_release())
    assert result.spec_hash == spec_hash(spec)
    assert result.release_id == "syn-2026-09-23-01"
    assert result.engine_version == ENGINE_VERSION == "1.3.0"
    assert result.synthetic is True


def test_rank_gives_the_same_result_every_time():
    spec = build_worked_spec()
    release = build_worked_release()
    first = rank(spec, release)
    assert all(rank(spec, release) == first for _ in range(100))

    # The order the release and the spec were put together in changes nothing.
    draw = draws(5)
    for _ in range(25):
        rows = draw.sample(range(4), 4)
        table = release.travel_table
        shuffled = dataclasses.replace(
            release,
            neighbourhoods=tuple(draw.sample(release.neighbourhoods, 4)),
            features=tuple(draw.sample(release.features, len(release.features))),
            tags=tuple(draw.sample(release.tags, len(release.tags))),
            costs=tuple(draw.sample(release.costs, len(release.costs))),
            places=tuple(reversed(release.places)),
            travel_table=table.replace(
                area_ids=tuple(table.area_ids[r] for r in rows),
                pt_typical=tuple(table.pt_typical[r] for r in rows),
                pt_just_missed=tuple(table.pt_just_missed[r] for r in rows),
                cycle=tuple(table.cycle[r] for r in rows),
                walk=tuple(table.walk[r] for r in rows),
            ),
        )
        reordered = spec.replace(
            commutes=tuple(reversed(spec.commutes)), weights=tuple(reversed(spec.weights))
        )
        assert rank(reordered, shuffled) == first


def test_missing_feature_is_dropped_and_weights_rebalanced():
    result = by_area(rank(build_worked_spec(), build_worked_release()))
    brackenhythe = result[BRACKENHYTHE]
    noise = next(c for c in brackenhythe.contributions if c.component == "feature:noise_exposure")

    # Nothing is filled in: the component is reported as missing, with no share.
    assert (noise.present, noise.utility, noise.share, noise.contribution) == (False, None, 0, 0)
    assert noise.weight == 0.3
    assert noise.fact_ids == (f"{BRACKENHYTHE}/missing/feature:noise_exposure",)
    # 2.70 of the 3.00 requested is present, and the shares are of what is present.
    assert brackenhythe.weight_coverage == 0.9
    present = [c for c in brackenhythe.contributions if c.present]
    assert sum(c.share for c in present) == pytest.approx(1, abs=2e-4)
    assert [c.share for c in present] == [round(c.weight / 2.7, 4) for c in present]

    # Had the figure been a poor one, the score would be lower. A gap is not a zero.
    filled = worked_with(
        features=tuple(
            feature_value(BRACKENHYTHE, FeatureId.NOISE_EXPOSURE, 100.0)
            if (f.area_id, f.feature_id) == (BRACKENHYTHE, FeatureId.NOISE_EXPOSURE)
            else f
            for f in build_worked_release().features
        )
    )
    worst = by_area(rank(build_worked_spec(), filled))[BRACKENHYTHE]
    assert worst.score < brackenhythe.score
    assert worst.weight_coverage == 1


def test_an_area_with_too_little_data_is_not_scored():
    release = build_worked_release()
    spec = default_spec(Tenure.RENT).replace(
        weights=(
            FeatureWeight(
                feature_id=FeatureId.NOISE_EXPOSURE,
                weight=0.6,
                direction=Direction.LESS,
                provenance=Provenance.STATED,
            ),
            FeatureWeight(
                feature_id=FeatureId.PARK_PROXIMITY,
                weight=0.4,
                direction=Direction.LESS,
                provenance=Provenance.STATED,
            ),
        )
    )
    result = rank(spec, release)
    # Brackenhythe has 0.4 of 1.0 present, which is below half.
    assert MIN_WEIGHT_COVERAGE == 0.5
    assert [(u.area_id, u.reason) for u in result.unranked] == [
        (BRACKENHYTHE, UnrankedReason.INSUFFICIENT_DATA)
    ]
    assert BRACKENHYTHE not in by_area(result)


def noise_and(*others: tuple[FeatureId, float]) -> PreferenceSpec:
    """Noise at 0.9, which Brackenhythe has no figure for, beside weights that also sum to 0.9."""
    weights = ((FeatureId.NOISE_EXPOSURE, 0.9), *others)
    return default_spec(Tenure.RENT).replace(
        weights=tuple(
            FeatureWeight(
                feature_id=feature_id,
                weight=weight,
                direction=Direction.LESS,
                provenance=Provenance.STATED,
            )
            for feature_id, weight in weights
        )
    )


@pytest.mark.parametrize(
    "present",
    [
        # 0.3 + 0.6 is 0.8999999999999999 in floats, and that over 1.8 is 0.49999999999999994.
        ((FeatureId.PARK_PROXIMITY, 0.3), (FeatureId.AIR_NO2, 0.6)),
        ((FeatureId.PARK_PROXIMITY, 0.45), (FeatureId.AIR_NO2, 0.45)),
        ((FeatureId.PARK_PROXIMITY, 0.9),),
    ],
    ids=["0.3 and 0.6", "0.45 and 0.45", "0.9"],
)
def test_exactly_half_the_weight_present_is_ranked_however_the_weight_is_split(
    present: tuple[tuple[FeatureId, float], ...],
):
    known = build_worked_release()
    air = tuple(feature_value(area_id(n), FeatureId.AIR_NO2, 40.0) for n in range(1, 5))
    release = worked_with(
        metrics=(*known.metrics, metric(FeatureId.AIR_NO2)), features=(*known.features, *air)
    )
    result = rank(noise_and(*present), release)
    # Brackenhythe has 0.9 of the 1.8 asked for. Only an area below half is dropped.
    assert result.unranked == ()
    assert by_area(result)[BRACKENHYTHE].weight_coverage == 0.5


def test_one_step_short_of_half_the_weight_is_not_ranked():
    spec = noise_and((FeatureId.PARK_PROXIMITY, 0.85))
    result = rank(spec, build_worked_release())
    assert [(u.area_id, u.reason) for u in result.unranked] == [
        (BRACKENHYTHE, UnrankedReason.INSUFFICIENT_DATA)
    ]


def test_coverage_is_never_decided_by_how_a_float_rounds():
    # Every way of splitting the weight over a feature and a tag that are
    # present and a feature that is missing, in whole steps.
    release = build_worked_release()
    checked = 0
    for park in range(1, 21):
        for leafy in range(1, 21):
            for noise in {park + leafy - 1, park + leafy, park + leafy + 1} & set(range(1, 21)):
                spec = default_spec(Tenure.RENT).replace(
                    weights=(
                        FeatureWeight(
                            feature_id=FeatureId.PARK_PROXIMITY,
                            weight=park / 20,
                            direction=Direction.LESS,
                            provenance=Provenance.STATED,
                        ),
                        FeatureWeight(
                            feature_id=FeatureId.NOISE_EXPOSURE,
                            weight=noise / 20,
                            direction=Direction.LESS,
                            provenance=Provenance.STATED,
                        ),
                    ),
                    tags=(
                        TagWeight(
                            tag_id=TagId.LEAFY, weight=leafy / 20, provenance=Provenance.STATED
                        ),
                    ),
                )
                assert (steps(park / 20), steps(noise / 20)) == (park, noise)
                ranked = BRACKENHYTHE in by_area(rank(spec, release))
                # Ranked when at least half the steps asked for are present.
                assert ranked == (park + leafy >= noise), (park, leafy, noise)
                checked += 1
    assert checked > 500


def test_an_area_with_nothing_present_is_unranked_and_nothing_is_divided_by_zero():
    spec = default_spec(Tenure.RENT).replace(
        weights=(),
        tags=(TagWeight(tag_id=TagId.WATERSIDE, weight=1.0, provenance=Provenance.STATED),),
    )
    # The worked release holds no waterside score for any area.
    result = rank(spec, build_worked_release())
    assert result.ranked == ()
    assert {u.reason for u in result.unranked} == {UnrankedReason.INSUFFICIENT_DATA}
    assert len(result.unranked) == 4


def hard_on_both() -> PreferenceSpec:
    spec = build_worked_spec()
    return spec.replace(budget=spec.budget.replace(strictness=Strictness.HARD))


def test_hard_filter_keeps_an_area_it_cannot_test():
    # Alderwick has no time to place 2, whose cap is hard.
    no_time = worked_with(travel_table=times((32, None), (18, 28), (44, 22), (25, 36)))
    result = rank(hard_on_both(), no_time)
    alderwick = by_area(result)[ALDERWICK]
    assert alderwick.untested_filters == (FilterReason.COMMUTE_CAP,)
    # The component is dropped from its score, and the area is still ranked.
    assert [c.component for c in alderwick.contributions if not c.present] == ["commute"]
    assert alderwick.weight_coverage == 0.6667
    # An area known to fail is still removed.
    assert [(f.area_id, f.reason) for f in result.filtered] == [
        (BRACKENHYTHE, FilterReason.OVER_BUDGET),
        (DULCIMER_GREEN, FilterReason.COMMUTE_CAP),
    ]


def test_hard_budget_keeps_an_area_with_no_estimate():
    costs = tuple(c for c in build_worked_release().costs if c.area_id != ALDERWICK)
    alderwick = by_area(rank(hard_on_both(), worked_with(costs=costs)))[ALDERWICK]
    assert alderwick.untested_filters == (FilterReason.OVER_BUDGET,)
    assert alderwick.budget is None
    assert [c.component for c in alderwick.contributions if not c.present] == ["budget"]
    assert alderwick.weight_coverage == 0.7333


def test_an_area_that_can_be_tested_on_nothing_is_unranked_and_not_filtered():
    release = worked_with(
        travel_table=times((32, None), (18, 28), (44, 22), (25, 36)),
        costs=tuple(c for c in build_worked_release().costs if c.area_id != ALDERWICK),
    )
    result = rank(hard_on_both(), release)
    # With the commute and the budget both unknown, 1.2 of 3.0 is present.
    assert ALDERWICK not in {f.area_id for f in result.filtered}
    assert [(u.area_id, u.reason) for u in result.unranked] == [
        (ALDERWICK, UnrankedReason.INSUFFICIENT_DATA)
    ]


def test_a_journey_beyond_the_cutoff_is_known_to_fail_a_hard_cap_and_scores_nothing():
    release = worked_with(travel_table=times((-1, -1), (18, 28), (44, 22), (25, 36)))
    result = rank(build_worked_spec(), release)
    assert (ALDERWICK, FilterReason.COMMUTE_CAP) in {(f.area_id, f.reason) for f in result.filtered}

    soft = build_worked_spec()
    soft = soft.replace(commutes=tuple(c.replace(strictness="soft") for c in soft.commutes))
    alderwick = by_area(rank(soft, release))[ALDERWICK]
    assert [(leg.status, leg.minutes, leg.utility) for leg in alderwick.legs] == [
        (TravelStatus.BEYOND_CUTOFF, None, 0),
        (TravelStatus.BEYOND_CUTOFF, None, 0),
    ]
    assert cells(alderwick)["commute"] == (0.3333, 0, 0)


def test_a_time_that_is_not_known_is_none_and_never_zero():
    release = worked_with(travel_table=times((None, 24), (18, 28), (44, 22), (25, 36)))
    assert release.travel(ALDERWICK, "syn-d0001", Mode.PT, PtBasis.TYPICAL).minutes is None
    assert release.travel(ALDERWICK, "syn-d0099", Mode.PT, PtBasis.TYPICAL).status == "missing"
    assert release.travel("syn-n0099", "syn-d0001", Mode.PT, PtBasis.TYPICAL).status == "missing"

    alderwick = by_area(rank(build_worked_spec(), release))[ALDERWICK]
    unknown, known = alderwick.legs
    assert (unknown.status, unknown.minutes, unknown.utility) == ("missing", None, None)
    assert (unknown.minutes_typical, unknown.minutes_just_missed) == (None, None)
    # The leg that is known is still reported, but the slowest cannot be known.
    assert (known.minutes, known.minutes_typical, known.minutes_just_missed) == (24, 24, 29)
    commute = next(c for c in alderwick.contributions if c.component == "commute")
    assert (commute.present, commute.utility) == (False, None)
    # A journey of no minutes at all would have scored the full 1.0.
    assert commute_utility(0, 40) == 1


def test_slowest_destination_drives_the_score():
    spec = build_worked_spec()
    release = build_worked_release()
    slowest = by_area(rank(spec, release))
    mean = by_area(rank(spec.replace(commute_combine=Combine.MEAN), release))

    # Brackenhythe: 0.94 to place 1 and 0.5667 to place 2.
    assert cells(slowest[BRACKENHYTHE])["commute"][1] == 0.5667
    assert cells(mean[BRACKENHYTHE])["commute"][1] == round((0.94 + 17 / 30) / 2, 4)
    # The leg that drove the score is cited first, whichever way they are combined.
    for result in (slowest, mean):
        commute = next(c for c in result[BRACKENHYTHE].contributions if c.component == "commute")
        assert commute.fact_ids == (
            f"{BRACKENHYTHE}/travel/syn-p0002.pt",
            f"{BRACKENHYTHE}/travel/syn-p0001.pt",
        )

    # Making the better journey better still changes nothing; the worse one decides.
    faster = worked_with(travel_table=times((32, 24), (5, 28), (44, 22), (25, 36)))
    assert by_area(rank(spec, faster))[BRACKENHYTHE].score == slowest[BRACKENHYTHE].score
    slower = worked_with(travel_table=times((32, 24), (18, 30), (44, 22), (25, 36)))
    assert by_area(rank(spec, slower))[BRACKENHYTHE].score < slowest[BRACKENHYTHE].score


def test_the_default_is_the_slowest_on_typical_times():
    spec = default_spec(Tenure.RENT)
    assert spec.commute_combine is Combine.SLOWEST
    assert spec.pt_basis is PtBasis.TYPICAL


def test_just_missed_times_are_scored_when_asked_for():
    spec = build_worked_spec().replace(pt_basis=PtBasis.JUST_MISSED)
    alderwick = by_area(rank(spec, build_worked_release()))[ALDERWICK]
    # Five minutes more on each leg: 37 of 40, and 29 of 30.
    assert [(leg.minutes, leg.minutes_typical) for leg in alderwick.legs] == [(37, 32), (29, 24)]
    assert [leg.utility for leg in alderwick.legs] == [0.56, 0.5333]


@pytest.mark.parametrize(
    ("minutes", "utility"),
    [(0, 1.0), (15, 1.0), (32, 0.66), (40, 0.5), (44, 0.4), (59, 0.025), (60, 0.0), (90, 0.0)],
)
def test_the_decay_curve_with_a_cap_of_forty_minutes(minutes: int, utility: float):
    assert commute_utility(minutes, 40) == pytest.approx(utility)


def test_a_short_cap_is_full_only_until_half_of_it():
    # With a cap of 20, fifteen minutes is more than half, so full runs to 10.
    assert commute_utility(10, 20) == 1
    assert commute_utility(15, 20) == pytest.approx(0.75)
    assert commute_utility(20, 20) == 0.5


@pytest.mark.parametrize("cap", [10, 20, 30, 45, 60, 90, 120])
def test_the_decay_never_rises_with_a_longer_journey(cap: int):
    curve = [commute_utility(minutes, cap) for minutes in range(0, 200)]
    assert all(0 <= u <= 1 for u in curve)
    assert all(later <= earlier for earlier, later in pairwise(curve))
    assert curve[cap] == 0.5


def test_budget_is_soft_by_default_and_uses_the_upper_quartile():
    assert default_spec(Tenure.RENT).budget.strictness is Strictness.SOFT
    assert default_spec(Tenure.BUY).budget.strictness is Strictness.SOFT

    # Brackenhythe: median 1,800 is within a budget of 1,800; upper quartile 1,950 is not.
    estimate = cost(BRACKENHYTHE, 1950)
    assert (estimate.median, estimate.upper_quartile) == (1800, 1950)
    spec = build_worked_spec()
    soft = rank(spec, build_worked_release())
    fit = by_area(soft)[BRACKENHYTHE].budget
    assert fit is not None
    assert (fit.upper_quartile, fit.margin, fit.utility) == (1950, -150, 0.6667)
    assert fit.confidence == "high"

    hard = rank(spec.replace(budget=spec.budget.replace(strictness="hard")), build_worked_release())
    assert (BRACKENHYTHE, FilterReason.OVER_BUDGET) in {
        (f.area_id, f.reason) for f in hard.filtered
    }


@pytest.mark.parametrize(
    ("upper_quartile", "utility"),
    [(1000, 1.0), (1800, 1.0), (1950, 2 / 3), (2025, 0.5), (2250, 0.0), (4000, 0.0)],
)
def test_budget_fit_falls_in_a_line_to_nothing_at_a_quarter_over(
    upper_quartile: int, utility: float
):
    assert budget_utility(1800, upper_quartile) == pytest.approx(utility)


def test_being_further_under_budget_earns_nothing():
    assert budget_utility(1800, 900) == budget_utility(1800, 1799) == 1


def test_a_spec_that_asks_for_nothing_ranks_every_area_the_same():
    spec = default_spec(Tenure.RENT).replace(weights=())
    result = rank(spec, small_release())
    assert result.empty_spec
    assert [a.area_id for a in result.ranked] == sorted(a.area_id for a in result.ranked)
    assert {(a.score, a.weight_coverage, a.contributions) for a in result.ranked} == {(0, 1, ())}
    assert [u.reason for u in result.unranked] == [UnrankedReason.NOT_RANKABLE]


def test_areas_are_excluded_selected_and_filtered_in_the_order_the_contract_gives():
    def rule(area: str, kind: AreaRuleKind) -> AreaRule:
        return AreaRule(area_id=area, rule=kind, provenance=Provenance.UI_EDIT)

    spec = build_worked_spec()
    excluded = rank(
        spec.replace(areas=(rule(DULCIMER_GREEN, AreaRuleKind.EXCLUDE),)), build_worked_release()
    )
    # Dulcimer Green also fails the hard cap, but the exclusion catches it first.
    assert [(f.area_id, f.reason) for f in excluded.filtered] == [(DULCIMER_GREEN, "excluded")]

    only = rank(
        spec.replace(
            areas=(rule(ALDERWICK, AreaRuleKind.ONLY), rule(DULCIMER_GREEN, AreaRuleKind.ONLY))
        ),
        build_worked_release(),
    )
    assert [a.area_id for a in only.ranked] == [ALDERWICK]
    assert [(f.area_id, f.reason) for f in only.filtered] == [
        (BRACKENHYTHE, "not_selected"),
        (CINDERMOOR, "not_selected"),
        (DULCIMER_GREEN, "commute_cap"),
    ]


def test_hard_filters_apply_whatever_the_weights():
    spec = build_worked_spec().replace(commute_weight=0.0)
    result = rank(spec, build_worked_release())
    assert [(f.area_id, f.reason) for f in result.filtered] == [(DULCIMER_GREEN, "commute_cap")]
    alderwick = by_area(result)[ALDERWICK]
    # A component that is not requested appears nowhere and counts towards nothing.
    assert "commute" not in cells(alderwick)
    assert [leg.utility for leg in alderwick.legs] == [None, None]
    assert [leg.minutes for leg in alderwick.legs] == [32, 24]


def test_equal_scores_get_different_ranks_and_the_id_decides():
    same = tuple(feature_value(area_id(n), FeatureId.PARK_PROXIMITY, 50.0) for n in range(1, 5))
    spec = default_spec(Tenure.RENT).replace(
        weights=(
            FeatureWeight(
                feature_id=FeatureId.PARK_PROXIMITY,
                weight=1.0,
                direction=Direction.LESS,
                provenance=Provenance.STATED,
            ),
        )
    )
    result = rank(spec, worked_with(features=same))
    assert [(a.area_id, a.rank, a.score) for a in result.ranked] == [
        (ALDERWICK, 1, 50.0),
        (BRACKENHYTHE, 2, 50.0),
        (CINDERMOOR, 3, 50.0),
        (DULCIMER_GREEN, 4, 50.0),
    ]


def test_rank_reads_the_percentiles_it_is_given_and_does_not_work_them_out():
    # Section 2.4 would give four areas 12.5, 37.5, 62.5 and 87.5. The worked
    # release says 20, 60, 10 and 30, and those are what is scored.
    given = [row[3] for row in WORKED]
    spec = default_spec(Tenure.RENT).replace(
        weights=(
            FeatureWeight(
                feature_id=FeatureId.PARK_PROXIMITY,
                weight=1.0,
                direction=Direction.LESS,
                provenance=Provenance.STATED,
            ),
        )
    )
    scores = {a.area_id: a.score for a in rank(spec, build_worked_release()).ranked}
    assert scores == {area_id(n + 1): 100 - p for n, p in enumerate(given) if p is not None}


def test_every_area_is_ranked_filtered_or_unranked_exactly_once():
    release = small_release()
    everyone = sorted(n.area_id for n in release.neighbourhoods)
    draw = draws(21)
    for _ in range(150):
        result = rank(random_spec(draw, release), release)
        placed = [
            *(a.area_id for a in result.ranked),
            *(f.area_id for f in result.filtered),
            *(u.area_id for u in result.unranked),
        ]
        assert sorted(placed) == everyone
        assert [f.area_id for f in result.filtered] == sorted(f.area_id for f in result.filtered)
        assert [u.area_id for u in result.unranked] == sorted(u.area_id for u in result.unranked)


def test_what_a_reader_can_check_of_a_result_adds_up():
    release = small_release()
    draw = draws(22)
    for _ in range(150):
        spec = random_spec(draw, release)
        result = rank(spec, release)
        assert [a.rank for a in result.ranked] == list(range(1, len(result.ranked) + 1))
        scores = [a.score for a in result.ranked]
        assert scores == sorted(scores, reverse=True)
        for area in result.ranked:
            assert 0 <= area.score <= 100
            assert MIN_WEIGHT_COVERAGE <= area.weight_coverage <= 1 or result.empty_spec
            total = sum(c.contribution for c in area.contributions)
            assert total == pytest.approx(area.score / 100, abs=0.002)
            present = [c for c in area.contributions if c.present]
            for c in present:
                assert c.utility is not None
                assert c.contribution + c.loss == pytest.approx(c.share, abs=2e-4)
            shown = [c.contribution for c in area.contributions]
            assert shown == sorted(shown, reverse=True)
            assert len(area.legs) == len(spec.commutes)


def test_contributions_sum_to_the_score_before_they_are_rounded():
    release = small_release()
    draw = draws(23)
    checked = 0
    for _ in range(100):
        spec = random_spec(draw, release)
        for area in release.neighbourhoods:
            scored = _score(area, spec, release)
            if isinstance(scored, _Scored) and scored.parts:
                present = _present_weight(scored.parts)
                total = sum(_contribution(part, present) for part in scored.parts)
                assert total == pytest.approx(scored.total, abs=1e-9)
                assert 0 <= scored.total <= 1 + 1e-9
                checked += 1
    assert checked > 100


def test_a_better_figure_never_lowers_an_areas_score():
    release = build_worked_release()
    spec = build_worked_spec()
    before = by_area(rank(spec, release))[ALDERWICK].score
    for percentile in (20.0, 15.0, 5.0, 0.0):
        better = worked_with(
            features=tuple(
                # Park proximity is wanted low, so a lower percentile is a better figure.
                feature_value(ALDERWICK, FeatureId.PARK_PROXIMITY, percentile)
                if (f.area_id, f.feature_id) == (ALDERWICK, FeatureId.PARK_PROXIMITY)
                else f
                for f in release.features
            )
        )
        after = by_area(rank(spec, better))[ALDERWICK].score
        assert after >= before
        before = after


def test_a_place_in_the_worked_example_is_the_one_the_commute_names():
    release = build_worked_release()
    assert [p.place_id for p in release.places] == [place_id(1), place_id(2)]
    assert [c.place_id for c in build_worked_spec().commutes] == [place_id(1), place_id(2)]
