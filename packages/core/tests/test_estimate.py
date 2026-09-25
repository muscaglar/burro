"""A journey estimated from distance, where a release holds no journey time.

Every release here is made up. The homes of each area are put a whole number of
kilometres from the one place, so that each estimate can be worked out by hand:
12 minutes, and 3 for each kilometre.
"""

import dataclasses

import pytest
from burro_core import estimate as how
from burro_core.estimate import (
    ESTIMATED,
    HOW,
    VERDICT,
    WORTH,
    band_against,
    estimated_minutes,
    estimates_journeys,
    kilometres,
)
from burro_core.explain import TEMPLATES, TemplateExplainer, explain, render
from burro_core.facts import Fact, facts_for
from burro_core.ids import (
    FactKind,
    FeatureId,
    FilterReason,
    JourneyBand,
    Mode,
    Provenance,
    Strictness,
    TemplateId,
    Tenure,
    TravelStatus,
)
from burro_core.rank import CommuteLeg, RankResult, rank
from burro_core.release import InMemoryRelease, ReleaseError, parse_release
from burro_core.spec import Commute, PreferenceSpec, default_spec
from burro_core.verify import verify

from .support import (
    HOMES_KM,
    KM_TO_A_DEGREE,
    area_id,
    estimated_documents,
    estimated_release,
    place,
    place_id,
    small_release,
    with_figures,
)

WITHIN, BORDERLINE, BEYOND = (
    JourneyBand.LIKELY_WITHIN,
    JourneyBand.BORDERLINE,
    JourneyBand.LIKELY_BEYOND,
)
# The band of each area against 40 minutes, in the order of the areas. The last area is not
# ranked, and its journey is estimated all the same.
AGAINST_40 = (WITHIN, WITHIN, WITHIN, WITHIN, BORDERLINE, BORDERLINE, BORDERLINE, BEYOND)


def commute(
    number: int,
    minutes: int = 40,
    strictness: Strictness = Strictness.SOFT,
    mode: Mode = Mode.PT,
) -> Commute:
    return Commute(
        place_id=place_id(number),
        mode=mode,
        max_minutes=minutes,
        strictness=strictness,
        provenance=Provenance.STATED,
    )


def searching(minutes: int = 40, strictness: Strictness = Strictness.SOFT) -> PreferenceSpec:
    """A search for nothing but one journey, to the one place."""
    return default_spec(Tenure.RENT).replace(
        weights=(), commutes=(commute(1, minutes=minutes, strictness=strictness),)
    )


def legs(result: RankResult) -> dict[str, CommuteLeg]:
    return {area.area_id: area.legs[0] for area in result.ranked}


def fact_of(release: InMemoryRelease, area: int, spec: PreferenceSpec) -> Fact:
    (found,) = (f for f in facts_for(release, area_id(area), spec) if f.kind is FactKind.TRAVEL)
    return found


# The numbers


def test_the_numbers_of_an_estimate_are_named_in_one_place_and_are_the_first_guesses():
    assert (how.FIXED_MINUTES, how.MINUTES_A_KM) == (12, 3)
    assert (how.MINUTES_A_KM_NEAR_THE_UNDERGROUND, how.NEAR_THE_UNDERGROUND_M) == (2.5, 800)
    assert (how.WITHIN_BY, how.BEYOND_BY) == (5, 10)
    assert HOW.model_dump() == {
        "fixed_minutes": 12,
        "minutes_a_km": 3,
        "minutes_a_km_near_the_underground": 2.5,
        "near_the_underground_m": 800,
        "within_by": 5,
        "beyond_by": 10,
        "said": "Estimated from distance, not from a timetable.",
    }


def test_a_distance_is_a_straight_line_over_the_ground():
    assert kilometres((0.0, 0.0), (0.0, 0.0)) == 0
    assert kilometres((0.0, 0.0), (1.0, 0.0)) == pytest.approx(KM_TO_A_DEGREE, abs=1e-4)
    assert kilometres((0.0, 0.0), (0.0, 1.0)) == pytest.approx(KM_TO_A_DEGREE, abs=1e-4)
    # The same either way, and shorter across a degree of longitude further north.
    assert kilometres((-0.1, 51.5), (0.1, 51.6)) == kilometres((0.1, 51.6), (-0.1, 51.5))
    assert kilometres((0.0, 51.5), (1.0, 51.5)) == pytest.approx(69.2, abs=0.1)


def test_an_estimate_is_a_fixed_part_and_a_part_for_each_kilometre():
    release = estimated_release()
    found = [estimated_minutes(release, area_id(n), place(1)) for n in range(1, 9)]
    assert found == pytest.approx([12 + 3 * km for km in HOMES_KM], abs=1e-6)


def test_near_the_underground_each_kilometre_takes_less():
    """The homes of area 5 stand 9 kilometres off: 39 minutes, and 34.5 near the Underground."""
    near = with_figures(
        estimated_release(), {FeatureId.UNDERGROUND_PROXIMITY: (None, None, None, None, 800)}
    )
    assert estimated_minutes(near, area_id(5), place(1)) == pytest.approx(12 + 2.5 * 9)
    assert legs(rank(searching(), near))[area_id(5)].estimate is WITHIN
    # A metre further than 800, and an area with no figure, are not known to be near.
    far = with_figures(
        estimated_release(), {FeatureId.UNDERGROUND_PROXIMITY: (None, None, None, None, 801)}
    )
    for release in (far, estimated_release()):
        assert estimated_minutes(release, area_id(5), place(1)) == pytest.approx(12 + 3 * 9)
        assert legs(rank(searching(), release))[area_id(5)].estimate is BORDERLINE


# The bands


@pytest.mark.parametrize(
    ("minutes", "band"),
    [
        (12, WITHIN),
        (35, WITHIN),  # exactly 5 under is at least 5 under
        (35.01, BORDERLINE),
        (40, BORDERLINE),
        (50, BORDERLINE),  # exactly 10 over is not more than 10 over
        (50.01, BEYOND),
        (90, BEYOND),
    ],
)
def test_a_band_is_likely_within_borderline_or_likely_beyond(minutes: float, band: JourneyBand):
    assert band_against(minutes, 40) is band


def test_a_journey_is_said_as_a_band_against_the_limit_a_person_gave():
    release = estimated_release()
    found = legs(rank(searching(40), release))
    assert [found[area_id(n)].estimate for n in range(1, 8)] == list(AGAINST_40[:7])
    # Against 30 minutes the same homes stand otherwise: 12 + 3 x 5 is 27, which is not 5 under.
    against_30 = legs(rank(searching(30), release))
    assert [against_30[area_id(n)].estimate for n in (1, 2, 3)] == [WITHIN, BORDERLINE, BORDERLINE]


# What a limit does


def test_a_firm_limit_leaves_out_only_the_areas_that_are_likely_beyond():
    release = with_figures(estimated_release(), {})
    # The last area is not rankable, so an eighth that is likely beyond is made rankable.
    rankable = dataclasses.replace(
        release,
        neighbourhoods=tuple(area.replace(rankable=True) for area in release.neighbourhoods),
    )
    result = rank(searching(40, Strictness.HARD), rankable)
    assert [(f.area_id, f.reason) for f in result.filtered] == [
        (area_id(8), FilterReason.COMMUTE_LIKELY_BEYOND)
    ]
    # What is borderline stays, and so does what is likely within.
    assert {area.area_id for area in result.ranked} == {area_id(n) for n in range(1, 8)}
    assert all(not area.untested_filters for area in result.ranked)


def test_a_flexible_limit_leaves_none_out_and_counts_the_band_in_the_fit():
    release = estimated_release()
    rankable = dataclasses.replace(
        release,
        neighbourhoods=tuple(area.replace(rankable=True) for area in release.neighbourhoods),
    )
    result = rank(searching(40, Strictness.SOFT), rankable)
    assert not result.filtered and len(result.ranked) == 8
    assert WORTH == {WITHIN: 1.0, BORDERLINE: 0.5, BEYOND: 0.0}
    found = legs(result)
    assert [found[area_id(n)].utility for n in range(1, 9)] == [WORTH[b] for b in AGAINST_40]
    # The fit follows the band and nothing finer: areas of one band are level.
    assert [round(area.score) for area in result.ranked] == [100] * 4 + [50] * 3 + [0]


# What is served


def test_nothing_served_gives_the_estimate_as_minutes():
    release = estimated_release()
    spec = searching(40)
    for leg in legs(rank(spec, release)).values():
        assert leg.status is TravelStatus.ESTIMATED and leg.estimate is not None
        assert (leg.minutes, leg.minutes_typical, leg.minutes_just_missed) == (None, None, None)
    for n in range(1, 9):
        fact = fact_of(release, n, spec)
        # The one number of the fact is the limit the person gave.
        assert fact.numbers == ("40",)
        assert not {"minutes", "typical", "missed", "margin"} & set(fact.slots)
        assert not any(character.isdigit() for character in render(fact).text.replace("40", ""))


def test_the_fact_of_an_estimate_says_that_it_is_one():
    release = estimated_release()
    said = {
        band: render(fact_of(release, n, searching())).text
        for n, band in ((1, WITHIN), (5, BORDERLINE), (8, BEYOND))
    }
    assert said == {
        WITHIN: "By public transport to Pellam Cross: likely within the 40 minutes you set. "
        "Estimated from distance, not from a timetable.",
        BORDERLINE: "By public transport to Pellam Cross: borderline for the 40 minutes you "
        "set. Estimated from distance, not from a timetable.",
        BEYOND: "By public transport to Pellam Cross: likely beyond the 40 minutes you set. "
        "Estimated from distance, not from a timetable.",
    }
    assert ESTIMATED == "Estimated from distance, not from a timetable."
    assert TEMPLATES[TemplateId.TRAVEL_ESTIMATED].endswith("{estimated}")


def test_the_fact_of_an_estimate_names_its_sources_and_its_date_and_passes_the_verifier():
    release = estimated_release()
    for n in range(1, 9):
        fact = fact_of(release, n, searching())
        assert fact.template is TemplateId.TRAVEL_ESTIMATED
        assert fact.fact_id == f"{area_id(n)}/travel/{place_id(1)}.pt"
        assert (fact.slots["band"], fact.slots["estimated"]) == (AGAINST_40[n - 1], ESTIMATED)
        # What a table says of it, where the band stands alone.
        assert fact.slots["verdict"] == VERDICT[AGAINST_40[n - 1]]
        assert fact.sources and fact.as_of and fact.names == ("Pellam Cross",)
        for role in ("reason", "trade_off"):
            sentence = render(fact)
            assert verify(sentence, {fact.fact_id: fact}).ok, role


def test_a_journey_that_is_estimated_is_not_said_to_be_missing():
    release = estimated_release()
    for n in range(1, 9):
        facts = facts_for(release, area_id(n), searching())
        assert not [f for f in facts if f.template is TemplateId.MISSING_JOURNEY]


# What an explanation says of one


def test_an_estimate_is_a_reason_only_where_it_is_likely_within_its_limit():
    release = estimated_release()
    spec = searching()
    result = rank(spec, release)
    explained = {
        found.area_id: found
        for found in explain(
            result, release, spec, tuple(a.area_id for a in result.ranked), TemplateExplainer()
        )
    }
    for n, band in enumerate(AGAINST_40[:7], start=1):
        found = explained[area_id(n)]
        reasons = [s for s in found.reasons if "/travel/" in s.fact_ids[0]]
        # What is borderline is neither a reason nor what the area gives up.
        assert bool(reasons) == (band is WITHIN), n
        assert found.trade_off is None, n
        assert not found.missing
        for sentence in reasons:
            assert sentence.text.endswith(ESTIMATED) and not sentence.replaced


def test_a_journey_that_is_likely_beyond_its_limit_is_what_an_area_gives_up():
    release = estimated_release()
    rankable = dataclasses.replace(
        release,
        neighbourhoods=tuple(area.replace(rankable=True) for area in release.neighbourhoods),
    )
    spec = searching()
    (found,) = explain(rank(spec, rankable), rankable, spec, (area_id(8),), TemplateExplainer())
    assert found.trade_off is not None and not found.reasons
    assert "likely beyond the 40 minutes you set" in found.trade_off.text
    assert found.trade_off.text.endswith(ESTIMATED)


# When nothing is estimated


def test_a_journey_time_that_a_release_holds_takes_the_place_of_an_estimate():
    """The small release holds its times. Where it says where homes stand, they still stand."""
    held = small_release()
    placed = dataclasses.replace(
        held,
        neighbourhoods=tuple(area.replace(homes_at=area.centroid) for area in held.neighbourhoods),
    )
    assert estimates_journeys(placed)
    before, after = legs(rank(searching(), held)), legs(rank(searching(), placed))
    timed = [leg for leg in after.values() if leg.status is TravelStatus.OK]
    assert timed and all(leg.estimate is None and leg.minutes is not None for leg in timed)
    assert {a: leg for a, leg in after.items() if leg.status is TravelStatus.OK} == {
        a: leg for a, leg in before.items() if leg.status is TravelStatus.OK
    }


def test_nothing_is_estimated_where_a_release_does_not_say_where_homes_stand():
    """The committed kind of release: a journey with no time is missing, as it always was."""
    held = small_release()
    assert not estimates_journeys(held)
    assert all(area.homes_at is None for area in held.neighbourhoods)
    # Place 2 has no time from area 3, on purpose. With nothing else asked for, the area
    # has a figure for nothing that counts, and is listed apart with what it lacks.
    spec = searching().replace(commutes=(commute(2, minutes=40),))
    result = rank(spec, held)
    assert area_id(3) not in legs(result)
    assert [u.missing for u in result.unranked if u.area_id == area_id(3)] == [("commute",)]
    facts = facts_for(held, area_id(3), spec)
    assert not [f for f in facts if f.kind is FactKind.TRAVEL]
    assert TemplateId.MISSING_JOURNEY in {f.template for f in facts}


@pytest.mark.parametrize("mode", [Mode.CYCLE, Mode.WALK])
def test_nothing_is_estimated_by_bike_or_on_foot(mode: Mode):
    release = estimated_release()
    spec = searching().replace(commutes=(commute(1, minutes=40, mode=mode),))
    result = rank(spec, release)
    # No area has a time or an estimate, so none has a figure for the one thing asked for.
    assert not result.ranked and not result.filtered
    assert {u.missing for u in result.unranked if u.missing} == {("commute",)}
    facts = facts_for(release, area_id(1), spec)
    assert not [f for f in facts if f.kind is FactKind.TRAVEL]
    missing = [f for f in facts if f.template is TemplateId.MISSING_JOURNEY]
    # The release has routed no journey and states no source of one. So the fact cites
    # where the area came from, and says nothing but two names.
    assert [(f.numbers, f.names) for f in missing] == [((), ("Alderwick", "Pellam Cross"))]
    assert missing[0].sources and missing[0].as_of


def test_the_same_search_gives_the_same_answer():
    release, spec = estimated_release(), searching()
    first = rank(spec, release)
    assert all(rank(spec, release) == first for _ in range(5))
    again = parse_release(estimated_documents())
    assert legs(rank(spec, with_figures(again, {FeatureId.UNDERGROUND_PROXIMITY: ()}))) == legs(
        first
    )


# The release


def test_a_preview_may_name_places_and_hold_no_time_for_any():
    release = parse_release(estimated_documents())
    assert release.manifest.preview and release.places and release.destinations
    assert release.travel_table.destination_ids == ()
    assert parse_release(release.documents()) == release


def test_a_release_that_is_finished_holds_a_time_for_every_end_it_names():
    finished = estimated_documents()
    finished["manifest.json"].update(preview=False)
    with pytest.raises(ReleaseError) as refused:
        parse_release(finished)
    assert (refused.value.file, refused.value.rule) == ("travel.json", "rows_are_complete")


def test_a_release_that_routed_some_ends_and_not_all_is_refused_whatever_it_says():
    some = estimated_documents()
    some["travel.json"]["destination_ids"] = ["syn-d0001"]
    for matrix in ("pt_typical", "pt_just_missed", "cycle", "walk"):
        some["travel.json"][matrix] = [[20] for _ in some["travel.json"]["area_ids"]]
    some["travel.json"].update(source_ids=["synthetic"], as_of="2026-09")
    with pytest.raises(ReleaseError) as refused:
        parse_release(some)
    assert (refused.value.file, refused.value.rule) == ("travel.json", "rows_are_complete")


def test_where_the_homes_of_an_area_stand_is_held_to_the_area():
    far = estimated_documents()
    far["neighbourhoods.json"]["neighbourhoods"][0]["homes_at"] = [1.0, 0.05]
    with pytest.raises(ReleaseError) as refused:
        parse_release(far)
    assert (refused.value.file, refused.value.rule) == (
        "neighbourhoods.json",
        "values_are_in_range",
    )
    assert refused.value.row == "neighbourhoods[0].homes_at"
