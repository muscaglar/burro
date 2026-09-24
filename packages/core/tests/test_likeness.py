"""Likeness between areas: a pure function of a release, counted on measured parts."""

import dataclasses

import pytest
from burro_core.catalogue import FAMILIES, FEATURES
from burro_core.explain import render
from burro_core.facts import facts_for
from burro_core.ids import Describes, FactKind, Family, FeatureId, FeatureKind, TemplateId
from burro_core.likeness import Likeness, part_bands, parts_of, similar
from burro_core.release import InMemoryRelease
from burro_core.verify import verify

from .support import area_id, documents, fixture_release, small_release, with_figures

PARTS = tuple(part.feature_id for part in parts_of(small_release()))
# Seven rankable areas and one that is not. Figures 0 to 6 sit in these bands.
RISING = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 3.0)
BANDS_OF_RISING = (1, 1, 2, 3, 3, 4, 5, 3)


def level(*figures: tuple[FeatureId, tuple[float | None, ...]]) -> InMemoryRelease:
    """A release in which every area has the same figure for every part, but for those given."""
    same = dict.fromkeys(PARTS, (1.0,) * 8)
    return with_figures(small_release(), same | dict(figures))


def of(found: tuple[Likeness, ...]) -> list[str]:
    return [between.area_id for between in found]


def test_likeness_is_counted_on_the_parts_a_release_carries_and_each_once():
    assert len(PARTS) == 23
    assert list(PARTS) == sorted(PARTS)
    # Two that are in core and in no release yet.
    assert {f for f, feature in FEATURES.items() if feature.in_likeness} - set(PARTS) == {
        FeatureId.GP_WALK,
        FeatureId.PHARMACY_WALK,
    }


@pytest.mark.parametrize("feature_id", FeatureId)
def test_likeness_is_never_counted_on_a_nuisance_crime_or_what_is_weighed_on_request(
    feature_id: FeatureId,
):
    feature = FEATURES[feature_id]
    barred = (
        feature.kind in (FeatureKind.NUISANCE, FeatureKind.ON_REQUEST)
        or feature.describes is Describes.EVENTS
        or feature.family is None
        or feature_id
        in (
            FeatureId.HOMES_FLATS,
            FeatureId.HOMES_DENSITY,
            FeatureId.PRIVATE_OUTDOOR_SPACE,
            FeatureId.SCHOOL_PRIMARY_NEARBY,
            FeatureId.SCHOOL_PRIMARY_ATTAINMENT,
            FeatureId.SCHOOL_SECONDARY_ATTAINMENT,
        )
    )
    if barred:
        assert feature_id not in PARTS
        assert not feature.in_likeness


def test_a_flag_on_a_feature_cannot_bring_a_nuisance_into_likeness():
    # A release is held to core's flags, so this is a release built by hand.
    release = small_release()
    flagged = dataclasses.replace(
        release, metrics=tuple(m.replace(in_likeness=True) for m in release.metrics)
    )
    assert parts_of(flagged) == parts_of(release)


def test_the_band_of_a_part_is_of_the_figure_itself_with_no_polarity_applied():
    # A walk to a park is better short, and its band is still counted from the low figure.
    release = level((FeatureId.PARK_PROXIMITY, RISING))
    bands = part_bands(release)[FeatureId.PARK_PROXIMITY]
    assert [bands[area_id(n)] for n in range(1, 9)] == list(BANDS_OF_RISING)


def test_areas_in_the_same_band_on_every_part_are_as_alike_as_can_be():
    found = similar(level(), area_id(1))
    assert [(b.distance, b.same, b.measures, b.family) for b in found] == [(0.0, 23, 23, None)] * 5
    # Nearest first, then by id. Five at most, and never the area itself.
    assert of(found) == [area_id(n) for n in range(2, 7)]


def test_only_a_rankable_area_is_offered_and_an_area_that_is_not_may_still_ask():
    release = level()
    assert not release.neighbourhoods[7].rankable
    assert area_id(8) not in of(similar(release, area_id(1), n=20))
    assert of(similar(release, area_id(8))) == [area_id(n) for n in range(1, 6)]
    assert len(similar(release, area_id(1), n=20)) == 6


def test_distance_is_the_mean_difference_in_band_within_a_family_and_the_mean_across_them():
    # One part of Green differs, by the whole of the scale: band 1 against band 5.
    release = level((FeatureId.PARK_PROXIMITY, RISING))
    green = [p for p in PARTS if FEATURES[p].family is Family.GREEN]
    assert len(green) == 7
    found = {b.area_id: b for b in similar(release, area_id(1), n=20)}
    far = found[area_id(7)]
    # Four bands of four, over seven parts, in one family of four.
    assert far.distance == pytest.approx((4 / 4) / 7 / 4)
    assert (far.same, far.measures, far.family) == (22, 23, Family.GREEN)
    # Area 2 is in the same band as area 1, though its figure differs.
    assert (found[area_id(2)].distance, found[area_id(2)].family) == (0.0, None)
    assert of(similar(release, area_id(1))) == [area_id(n) for n in (2, 3, 4, 5, 6)]


def test_each_family_counts_the_same_however_many_parts_it_holds():
    # Daily life holds two parts and Green seven. One part apart in each.
    daily = level((FeatureId.STATION_WALK, RISING))
    green = level((FeatureId.PARK_PROXIMITY, RISING))
    one = {b.area_id: b.distance for b in similar(daily, area_id(1), n=20)}
    other = {b.area_id: b.distance for b in similar(green, area_id(1), n=20)}
    assert one[area_id(7)] == pytest.approx((4 / 4) / 2 / 4)
    assert other[area_id(7)] == pytest.approx((4 / 4) / 7 / 4)


def test_the_family_two_areas_are_least_alike_in_is_the_first_of_the_settings_on_a_tie():
    release = level(
        (FeatureId.STATION_WALK, RISING),
        (FeatureId.GROCERY_WALK, RISING),
        (FeatureId.VENUE_EVENING, RISING),
        (FeatureId.VENUE_FOOD_DRINK, RISING),
        (FeatureId.HIGHSTREET_ACCESS, RISING),
        (FeatureId.CULTURE_VENUES, RISING),
        (FeatureId.INDEPENDENTS_NEARBY, RISING),
    )
    found = {b.area_id: b for b in similar(release, area_id(1), n=20)}
    # Every part of Pace and food and of Daily life is the whole scale apart.
    assert found[area_id(7)].family is Family.PACE_FOOD
    assert list(FAMILIES).index(Family.PACE_FOOD) < list(FAMILIES).index(Family.DAILY_LIFE)


def test_a_part_one_area_has_no_figure_for_is_left_out_and_nothing_is_filled_in():
    gap = (None, 1.0, 1.0, 1.0, 1.0, 1.0, 6.0, 1.0)
    release = level((FeatureId.PARK_PROXIMITY, gap))
    found = {b.area_id: b for b in similar(release, area_id(1), n=20)}
    # Area 7 is far from the rest on that part. Area 1 has no figure for it,
    # so the part is not among what the two are compared on.
    assert (found[area_id(7)].measures, found[area_id(7)].distance) == (22, 0.0)


def test_likeness_is_unknown_where_under_six_parts_in_ten_have_a_figure():
    few = dict.fromkeys(PARTS[:10], (None, *[1.0] * 7))
    release = level(*few.items())
    # 13 of 23 is under 60%.
    assert similar(release, area_id(1)) == ()
    # And nothing is said to be like an area of which too little is known.
    assert area_id(1) not in of(similar(release, area_id(2), n=20))
    enough = level(*dict.fromkeys(PARTS[:9], (None, *[1.0] * 7)).items())
    # 14 of 23 is over.
    assert len(similar(enough, area_id(1))) == 5


def test_an_area_the_release_lacks_is_like_nothing():
    assert similar(small_release(), "syn-n0099") == ()
    assert similar(small_release(), "") == ()


def test_likeness_is_a_function_of_the_release_alone():
    release = small_release()
    again = dataclasses.replace(release, features=tuple(reversed(release.features)))
    for area in release.neighbourhoods:
        assert similar(release, area.area_id) == similar(again, area.area_id)
        assert similar(release, area.area_id) == similar(release, area.area_id)


def moved(feature_id: FeatureId) -> InMemoryRelease:
    return with_figures(small_release(), {feature_id: RISING})


@pytest.mark.parametrize(
    "feature_id",
    [
        FeatureId.CRIME_VIOLENCE_ROBBERY,
        FeatureId.INCIDENT_CRIMINAL_DAMAGE,
        FeatureId.NOISE_EXPOSURE,
        FeatureId.ROAD_MAJOR_EXPOSURE,
        FeatureId.UNIVERSITY_PROXIMITY,
        FeatureId.SCHOOL_PRIMARY_ATTAINMENT,
        FeatureId.HOMES_FLATS,
        FeatureId.HOMES_DENSITY,
    ],
)
def test_what_likeness_may_not_use_changes_no_likeness(feature_id: FeatureId):
    for area in small_release().neighbourhoods:
        assert similar(moved(feature_id), area.area_id) == similar(small_release(), area.area_id)
    # A part it may use does.
    changed = moved(FeatureId.PARK_PROXIMITY)
    assert any(
        similar(changed, area.area_id) != similar(small_release(), area.area_id)
        for area in small_release().neighbourhoods
    )


def test_what_a_home_costs_and_how_long_a_journey_takes_change_no_likeness():
    release = small_release()
    bare = dataclasses.replace(
        release,
        costs=(),
        travel_table=release.travel_table.replace(
            pt_typical=tuple((None,) * 4 for _ in range(8)),
            pt_just_missed=tuple((None,) * 4 for _ in range(8)),
        ),
    )
    for area in release.neighbourhoods:
        assert similar(bare, area.area_id) == similar(release, area.area_id)


def test_a_vibes_own_score_changes_no_likeness():
    release = small_release()
    unscored = dataclasses.replace(
        release,
        tags=tuple(
            row.replace(raw=None, score=None, band=None, spread_low=None, spread_high=None)
            for row in release.tags
        ),
    )
    for area in release.neighbourhoods:
        assert similar(unscored, area.area_id) == similar(release, area.area_id)


def likeness_facts(release: InMemoryRelease, number: int):
    facts = facts_for(release, area_id(number), None)
    return [fact for fact in facts if fact.kind is FactKind.LIKENESS]


def test_each_area_that_is_offered_has_a_fact_with_one_sentence_that_is_true():
    release = level((FeatureId.PARK_PROXIMITY, RISING))
    facts = {fact.key: fact for fact in likeness_facts(release, 1)}
    assert list(facts) == of(similar(release, area_id(1)))
    alike = facts[area_id(2)]
    assert alike.template is TemplateId.LIKENESS_SAME
    assert render(alike).text == (
        "Alderwick is in the same band as Brackenhythe on all 23 measures compared."
    )
    far = {fact.key: fact for fact in likeness_facts(release, 7)}[area_id(1)]
    assert far.template is TemplateId.LIKENESS
    assert render(far).text == (
        "Gorsebeck is in the same band as Alderwick on 22 of the 23 measures compared, "
        "and least alike in Green."
    )
    assert far.names == ("Gorsebeck", "Alderwick")
    assert far.numbers == ("22", "23")
    assert far.fact_id == f"{area_id(7)}/likeness/{area_id(1)}"
    for fact in (alike, far):
        assert verify(render(fact), {fact.fact_id: fact}).ok


def test_a_likeness_fact_cites_the_sources_and_the_dates_of_what_was_compared():
    found = documents()
    for metric in found["catalogue.json"]["metrics"]:
        if metric["feature_id"] == "park_proximity":
            metric["vintage"] = "2021"
        if metric["feature_id"] == "crime_burglary_theft":
            metric["vintage"] = "2019"
    from burro_core.release import parse_release

    release = parse_release(found)
    (fact, *_) = likeness_facts(release, 1)
    # The span of the parts that were compared. Crime is none of them.
    assert fact.as_of == "2021 to 2025"
    assert [source.source_id for source in fact.sources] == ["synthetic"]


def test_no_likeness_is_said_where_it_is_unknown_or_with_a_spec():
    few = dict.fromkeys(PARTS[:10], (None, *[1.0] * 7))
    assert likeness_facts(level(*few.items()), 1) == []
    # It is what a profile page needs, and a ranking does not.
    from burro_core.ids import Tenure
    from burro_core.spec import default_spec

    with_a_spec = facts_for(small_release(), area_id(1), default_spec(Tenure.RENT))
    assert not [fact for fact in with_a_spec if fact.kind is FactKind.LIKENESS]


def test_the_areas_most_like_an_area_are_in_the_order_of_the_count_each_sentence_gives():
    # Under a heading that promised the areas in the same band on the most
    # measures, Thrushcombe's read 10, 10, 5, 7 and 8 of 23, in that order.
    release = fixture_release()
    ids = {area.name: area.area_id for area in release.neighbourhoods}
    names = {area.area_id: area.name for area in release.neighbourhoods}
    found = similar(release, ids["Thrushcombe"])
    assert [(names[like.area_id], like.same) for like in found] == [
        ("Dulcimer Green", 10),
        ("Tallowgate", 9),
        ("Osierholm", 9),
        ("Eskerfold", 8),
        ("Wickerford", 7),
    ]
    for area in release.neighbourhoods:
        every = similar(release, area.area_id, n=len(release.neighbourhoods))
        shown = every[:5]
        # Most alike first, by the count the sentence prints.
        assert [like.same for like in shown] == sorted((like.same for like in shown), reverse=True)
        # No area that was left out shares more measures than the last one shown.
        assert all(left.same <= shown[-1].same for left in every[5:]), area.name
        # Where two share as many, the nearer comes first, and then the id decides.
        order = [(-like.same, like.distance, like.area_id) for like in every]
        assert order == sorted(order), area.name
        # And the sentence of each says the count it was ordered by.
        facts = {f.key: f for f in facts_for(release, area.area_id, None) if f.kind == "likeness"}
        assert [facts[like.area_id].slots["same"] for like in shown] == [
            str(like.same) for like in shown
        ]
