"""The row of the catalogue a measure writes: what core decides, and how the figure was made."""

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution
from burro_core.ids import Method as MadeBy
from burro_core.release import DECIDED_BY_CORE
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.measures import MEASURES, Measure, says_what_core_says
from burro_pipeline.derive.methods import AREA_ROW_RATIO, GRID_AT_HOMES, LSOA_VALUE_BY_HOMES

SOURCES = ("made-up-survey", "made-up-areas")
CARRIED = [measure for measure in MEASURES if not measure.waits_on]


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
    assert [measure.feature for measure in CARRIED] == [
        FeatureId.AIR_NO2,
        FeatureId.CONSERVATION_COVER,
        FeatureId.CULTURE_VENUES,
        FeatureId.CULTURE_VENUES_PER_HOMES,
        FeatureId.GREEN_COVER,
        FeatureId.HIGHSTREET_ACCESS,
        FeatureId.HOMES_DENSITY,
        FeatureId.HOMES_FLATS,
        FeatureId.HOMES_POST2000,
        FeatureId.HOMES_PRE1919,
        FeatureId.INCIDENT_ANTISOCIAL,
        FeatureId.INCIDENT_CRIMINAL_DAMAGE,
        FeatureId.LAND_GARDENS,
        FeatureId.LAND_INDUSTRY,
        FeatureId.LAND_STORAGE,
        FeatureId.LAND_TRANSPORT_OTHER,
        FeatureId.LAND_WOODLAND,
        FeatureId.LISTED_BUILDINGS,
        FeatureId.NOISE_EXPOSURE,
        FeatureId.PARK_LARGE_PROXIMITY,
        FeatureId.PARK_PROXIMITY,
        FeatureId.PLAY_SPACE_PROXIMITY,
        FeatureId.PRICE_MEDIAN,
        FeatureId.ROAD_MAJOR_EXPOSURE,
        FeatureId.SCHOOL_PRIMARY_NEARBY,
        FeatureId.STATION_WALK,
        FeatureId.VENUE_FOOD_DRINK,
        FeatureId.VENUE_FOOD_DRINK_PER_HOMES,
        FeatureId.WATER_ACCESS,
    ]
    # What is left out is named as core names it still, or held back by a check.
    assert [measure.feature for measure in MEASURES if measure.waits_on] == [
        FeatureId.CENTRE_COMPACT,
        FeatureId.CENTRE_SMALL,
        FeatureId.PARK_FACILITIES,
        FeatureId.VENUE_EVENING,
    ]
