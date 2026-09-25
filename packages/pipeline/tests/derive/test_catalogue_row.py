"""The row of the catalogue a measure writes: what core decides, and how the figure was made."""

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution
from burro_core.ids import Method as MadeBy
from burro_core.release import DECIDED_BY_CORE
from burro_pipeline.derive import brands_nearby
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.measures import MEASURES, Measure, says_what_core_says
from burro_pipeline.derive.methods import AREA_ROW_RATIO, GRID_AT_HOMES, LSOA_VALUE_BY_HOMES

SOURCES = ("made-up-survey", "made-up-areas")
CARRIED = [measure for measure in MEASURES if not (measure.waits_on or measure.held_back)]


def row(feature_id: FeatureId, **said: object):
    given = {"method": AREA_ROW_RATIO, "source_ids": SOURCES, "vintage": "2025"} | said
    return catalogue_row(feature_id, definition="Made up for a test.", **given)  # pyright: ignore[reportArgumentType]


def test_a_row_says_of_a_feature_all_that_core_decides_of_it():
    made = row(FeatureId.HOMES_FLATS)
    core = FEATURES[FeatureId.HOMES_FLATS]
    assert {name: getattr(made, name) for name in DECIDED_BY_CORE} == {
        name: getattr(core, name) for name in DECIDED_BY_CORE
    }
    assert says_what_core_says(made)
    assert made.source_ids == ("made-up-areas", "made-up-survey")
    assert (made.vintage, made.rankable) == ("2025", True)


def test_a_row_may_switch_its_measure_off_for_ranking_and_says_what_core_says_all_the_same():
    """Core decides what a measure is. Whether a release ranks on it is the release's to say."""
    shown = row(FeatureId.ROAD_MAJOR_EXPOSURE, rankable=False)
    assert shown.rankable is False
    assert says_what_core_says(shown)


def test_a_row_says_how_its_figure_was_made_as_its_evidence_says_it():
    """The method a row of evidence names says what the screen must say of the figure."""
    assert row(FeatureId.AIR_NO2, method=GRID_AT_HOMES).method is MadeBy.MODELLED
    assert row(FeatureId.NOISE_EXPOSURE, method=LSOA_VALUE_BY_HOMES).method is MadeBy.AVERAGED
    assert row(FeatureId.HOMES_FLATS, method=AREA_ROW_RATIO).method is MadeBy.MEASURED


def test_a_row_that_is_made_otherwise_than_core_says_is_not_cores():
    """So a figure that is modelled is never carried under a row that says it was measured."""
    assert says_what_core_says(row(FeatureId.AIR_NO2, method=GRID_AT_HOMES))
    assert not says_what_core_says(row(FeatureId.AIR_NO2, method=AREA_ROW_RATIO))
    assert not says_what_core_says(row(FeatureId.HOMES_FLATS, method=GRID_AT_HOMES))


def test_a_row_that_names_the_measure_otherwise_than_core_does_is_not_cores():
    assert not says_what_core_says(row(FeatureId.GREEN_COVER, label="Public green space"))
    assert not says_what_core_says(row(FeatureId.PARK_PROXIMITY, label="Walk to a park"))
    polygon = row(FeatureId.WATER_ACCESS, native_resolution=NativeResolution.POINT)
    assert polygon.native_resolution is NativeResolution.POINT


@pytest.mark.parametrize("measure", CARRIED, ids=[measure.feature for measure in CARRIED])
def test_a_measure_that_waits_on_nothing_is_made_as_core_says_it_is_made(measure: Measure):
    """The first method of a measure is the one its rows name."""
    assert FEATURES[measure.feature].method.value == measure.methods[0].kind.value


def test_the_measures_a_build_carries_are_those_core_names_as_their_files_support():
    of_brands = set(brands_nearby.FEATURES)
    assert {measure.feature for measure in CARRIED} >= of_brands
    assert [measure.feature for measure in CARRIED if measure.feature not in of_brands] == [
        FeatureId.AIR_NO2,
        FeatureId.BUS_ROUTES_NEARBY,
        FeatureId.BUS_STOPS_NEARBY,
        FeatureId.CONSERVATION_COVER,
        FeatureId.CULTURE_VENUES,
        FeatureId.CULTURE_VENUES_PER_HOMES,
        FeatureId.EVENING_CLUSTER_EXPOSURE,
        FeatureId.GP_WALK,
        FeatureId.GREEN_COVER,
        FeatureId.GROCERY_WALK,
        FeatureId.HIGHSTREET_ACCESS,
        FeatureId.HIGHSTREET_CONSERVED,
        FeatureId.HOMES_DENSITY,
        FeatureId.HOMES_FLATS,
        FeatureId.HOMES_HIGHER_BANDS,
        FeatureId.HOMES_POST2000,
        FeatureId.HOMES_PRE1919,
        FeatureId.HOUSEHOLDS_DEPENDENT_CHILDREN,
        FeatureId.HOUSEHOLDS_ONE_PERSON,
        FeatureId.INCIDENT_ANTISOCIAL,
        FeatureId.INCIDENT_CRIMINAL_DAMAGE,
        FeatureId.LAND_GARDENS,
        FeatureId.LAND_INDUSTRY,
        FeatureId.LAND_STORAGE,
        FeatureId.LAND_TRANSPORT_OTHER,
        FeatureId.LAND_WOODLAND,
        FeatureId.LISTED_BUILDINGS,
        FeatureId.NOISE_EXPOSURE,
        FeatureId.OVERGROUND_PROXIMITY,
        FeatureId.PARK_LARGE_PROXIMITY,
        FeatureId.PARK_PROXIMITY,
        FeatureId.PHARMACY_WALK,
        FeatureId.PLAY_SPACE_PROXIMITY,
        FeatureId.PRICE_MEDIAN,
        FeatureId.PRICE_RISE_10Y,
        FeatureId.PRICE_RISE_5Y,
        FeatureId.PRIVATE_OUTDOOR_SPACE,
        FeatureId.RAIL_PROXIMITY,
        FeatureId.RESIDENTS_AGED_20_34,
        FeatureId.RESIDENTS_AGED_65_OVER,
        FeatureId.ROAD_MAJOR_EXPOSURE,
        FeatureId.ROAD_TRAFFIC_NEARBY,
        FeatureId.SCHOOL_PRIMARY_NEARBY,
        FeatureId.STATION_WALK,
        FeatureId.UNDERGROUND_PROXIMITY,
        FeatureId.VENUE_CAFE,
        FeatureId.VENUE_CAFE_PER_HOMES,
        FeatureId.VENUE_EVENING,
        FeatureId.VENUE_EVENING_PER_HOMES,
        FeatureId.VENUE_FOOD_DRINK,
        FeatureId.VENUE_FOOD_DRINK_PER_HOMES,
        FeatureId.VENUE_GYM,
        FeatureId.VENUE_GYM_PER_HOMES,
        FeatureId.WATER_ACCESS,
    ]
    # What is left out is named as core names it still. No measure is held back: private
    # outdoor space was, for want of a row of the proxy audit, until the audit was dropped
    # on 2026-09-25.
    assert [measure.feature for measure in MEASURES if measure.waits_on] == [
        FeatureId.CENTRE_COMPACT,
        FeatureId.CENTRE_SMALL,
        FeatureId.PARK_FACILITIES,
    ]
    assert [measure.feature for measure in MEASURES if measure.held_back] == []
