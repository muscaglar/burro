"""Cafes, gyms and pubs nearby, from the file of places to a figure for each area.

Every file here is made up, and says so: `culture_support.py` draws the town
and writes its places. The centres stand 1,000 metres apart, so that a home is
within reach of what stands by its own centre and of little else, and every
count can be made by hand:

    Quillhaven 001   Q1  two cafes, a gym, and a pub, a bar and a gastropub side by side
                     Q2  a coffee shop, 500 metres east, half way to Q3
                     Q3  the same coffee shop, 500 metres west
                     Q4  a yoga studio 790 metres north. A pub 810 metres north is out of reach
    Quillhaven 002   R1  a pub. R2, R3 and R4 have nothing within reach
    Tallowgate 001   T1  a cafe, a tea room and a pilates studio. T2, T3 and T4 have nothing

Beside Q1 stand eight records that are not counted: a bakery, an internet
cafe, a trainer, a gymnastics centre, a lounge, a restaurant, a nightclub, and
a pub that has closed. A bookshop stands by every centre, so that the file is
seen to hold something within reach of every home.
"""

import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, RANKED_AS, TAGS
from burro_core.ids import FeatureId, NativeResolution, TagId
from burro_pipeline.cells import spine
from burro_pipeline.derive import culture_venues, measures, venues_nearby
from burro_pipeline.derive.culture_reach import METRES
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.venue_kinds import KINDS, Kind, LeftOut
from burro_pipeline.derive.venues_nearby import (
    COUNT_OF,
    EVERY,
    MEASURES,
    PUBS_ARE_FROM_THE_FILE,
    THIN_AT_THE_EDGE,
    Found,
    Nearby,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence

from ..fetch.parquet_support import Place
from .culture_support import (
    BY_EVERY_CENTRE,
    CANARY,
    DAY,
    OAS,
    ONE,
    Q1,
    Q2,
    Q4,
    R1,
    SHOP,
    SOURCE,
    T1,
    THREE,
    TWO,
    beside,
    centres_at,
    inputs_of,
    place,
)

FOOD = "food_and_drink"
DRINK = (FOOD, "alcoholic_beverage_venue")
CAFE = (FOOD, "casual_eatery", "cafe")
COFFEE = (FOOD, "non_alcoholic_beverage_venue", "coffee_shop")
TEA = (FOOD, "non_alcoholic_beverage_venue", "tea_room")
PUB = (*DRINK, "bar", "pub")
BAR = (*DRINK, "bar")
GASTROPUB = (FOOD, "casual_eatery", "gastropub")
FACILITY = ("sports_and_recreation", "sport_or_fitness_facility")
GYM = (*FACILITY, "gym")
YOGA = (*FACILITY, "fitness_studio", "yoga_studio")
PILATES = (*FACILITY, "fitness_studio", "pilates_studio")
OA_Q1, OA_Q2, OA_Q3, OA_Q4 = OAS[:4]
OA_R1, OA_R2, OA_T1 = OAS[4], OAS[5], OAS[8]
CAFES, GYMS, PUBS = (KINDS.index(kind) for kind in KINDS)
# Three pubs and bars that stand apart, each within 150 metres of the first centre.
SIDE_BY_SIDE = (
    place(beside(Q1, 0, -100), PUB),
    place(beside(Q1, 60, -100), BAR),
    place(beside(Q1, -60, -100), GASTROPUB),
)
NOT_COUNTED = (
    place(beside(Q1, 10, 10), (FOOD, "casual_eatery", "bakery")),
    place(beside(Q1, 20, 20), (*CAFE, "internet_cafe")),
    place(beside(Q1, 30, 30), (*FACILITY, "fitness_trainer")),
    place(beside(Q1, 40, 40), (*FACILITY, "gymnastics_center")),
    place(beside(Q1, 50, 50), (*DRINK, "lounge")),
    place(beside(Q1, 60, 60), (FOOD, "restaurant")),
    place(beside(Q1, 70, 70), ("arts_and_entertainment", "nightlife_venue", "dance_club")),
    place(beside(Q1, 80, 80), PUB, status="permanently_closed"),
)
IN_THE_TOWN = (
    *BY_EVERY_CENTRE,
    place(beside(Q1, 100), CAFE),
    place(beside(Q1, 0, 100), COFFEE),
    place(beside(Q1, -100), GYM),
    *SIDE_BY_SIDE,
    *NOT_COUNTED,
    place(beside(Q2, 500), COFFEE),
    place(beside(Q4, 0, 790), YOGA),
    place(beside(Q4, 0, 810), PUB),
    place(beside(R1, 0, 50), PUB),
    place(beside(T1, 50), CAFE),
    place(beside(T1, -50), TEA),
    place(beside(T1, 0, 50), PILATES),
)


def found_in(folder: Path, *places: Place, centres: bytes | None = None) -> Found:
    inputs = inputs_of(folder, places if places else IN_THE_TOWN, centres)
    return venues_nearby.found_of(inputs, spine.build(inputs))


def built(folder: Path, feature: FeatureId, *places: Place) -> Nearby:
    inputs = inputs_of(folder, places if places else IN_THE_TOWN)
    return venues_nearby.build(feature, inputs, spine.build(inputs))


@pytest.fixture
def town(tmp_path: Path) -> Found:
    return found_in(tmp_path)


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


# What is within reach


def test_each_home_is_given_the_places_of_each_kind_within_reach_of_its_own_centre(town: Found):
    within = town.reach.within
    assert town.reach.metres == METRES == 800
    assert within[OA_Q1][:EVERY] == (2, 1, 3)
    assert within[OA_Q2][:EVERY] == within[OA_Q3][:EVERY] == (1, 0, 0)
    assert within[OA_R1][:EVERY] == (0, 0, 1) and within[OA_R2][:EVERY] == (0, 0, 0)
    assert within[OA_T1][:EVERY] == (2, 1, 0)


def test_a_place_790_metres_off_on_the_grid_is_within_reach_and_one_810_off_is_not(town: Found):
    assert town.reach.within[OA_Q4][GYMS] == 1
    assert town.reach.within[OA_Q4][PUBS] == 0


def test_what_is_no_cafe_no_gym_and_no_pub_is_not_counted(town: Found):
    """Eight records stand beside Q1 that are none of the three. Six that are stand there too."""
    assert sum(town.reach.within[OA_Q1][:EVERY]) == 6
    assert town.reach.within[OA_Q1][EVERY] == 6 + len(NOT_COUNTED) + 1
    assert dict(town.held.left_out) == {
        LeftOut.NOT_A_KIND: 5,
        LeftOut.NOT_OF_THE_TABLE: len(BY_EVERY_CENTRE) + 2,
        "closed": 1,
    }
    assert dict(town.held.left_out_as) == {
        "bakery": 1,
        "fitness_trainer": 1,
        "gymnastics_center": 1,
        "internet_cafe": 1,
        "lounge": 1,
        "pub": 1,
    }


def test_the_count_of_an_area_is_the_mean_over_its_homes(tmp_path: Path):
    cafes = built(tmp_path, FeatureId.VENUE_CAFE).worked
    assert value_of(cafes[ONE]) == round((110 * 2 + 120 + 130) / 500, 1) == 0.9
    assert value_of(cafes[TWO]) == 0.0
    assert value_of(cafes[THREE]) == round(190 * 2 / 820, 1) == 0.5
    gyms = built(tmp_path, FeatureId.VENUE_GYM).worked
    assert value_of(gyms[ONE]) == round((110 + 140) / 500, 1) == 0.5
    assert value_of(gyms[THREE]) == round(190 / 820, 1) == 0.2
    pubs = built(tmp_path, FeatureId.VENUE_EVENING).worked
    assert value_of(pubs[ONE]) == round(110 * 3 / 500, 1) == 0.7
    assert value_of(pubs[TWO]) == round(150 / 660, 1) == 0.2
    assert value_of(pubs[THREE]) == 0.0
    assert {one.state for one in (*cafes.values(), *gyms.values(), *pubs.values())} == {
        State.PRESENT
    }


def test_the_second_figure_is_for_each_1000_homes_within_the_same_reach(tmp_path: Path):
    """One sum over another: no home of another output area is within reach of a centre."""
    bottom = 110 * 110 + 120 * 120 + 130 * 130 + 140 * 140
    cafes = built(tmp_path, FeatureId.VENUE_CAFE_PER_HOMES).worked
    assert value_of(cafes[ONE]) == round(1_000 * (110 * 2 + 120 + 130) / bottom, 1) == 7.5
    gyms = built(tmp_path, FeatureId.VENUE_GYM_PER_HOMES).worked
    assert value_of(gyms[ONE]) == round(1_000 * (110 + 140) / bottom, 1) == 4.0
    pubs = built(tmp_path, FeatureId.VENUE_EVENING_PER_HOMES).worked
    assert value_of(pubs[ONE]) == round(1_000 * 110 * 3 / bottom, 1) == 5.2
    assert value_of(pubs[THREE]) == 0.0


# One place with many records


def test_records_of_one_kind_that_stand_together_are_one_place(tmp_path: Path):
    """A cafe with three records within 25 metres of the first, one of them as a coffee shop."""
    found = found_in(
        tmp_path,
        place(Q1, CAFE),
        place(beside(Q1, 10), CAFE),
        place(beside(Q1, 0, 24), COFFEE),
        place(beside(Q1, 26), CAFE),
        place(Q2, SHOP),
    )
    assert culture_venues.ONE_VENUE == 25
    assert len(found.held.records) == 4 and len(found.of_kind(Kind.CAFE)) == 2
    assert found.records_of_one_place == {Kind.CAFE: 2}
    assert found.reach.within[OA_Q1][CAFES] == 2


def test_a_pub_a_bar_and_a_gastropub_on_one_spot_are_one_place(tmp_path: Path):
    """They are one kind to the measure, so three records of one door count once."""
    found = found_in(tmp_path, place(Q1, PUB), place(Q1, BAR), place(Q1, GASTROPUB))
    assert len(found.of_kind(Kind.PUB)) == 1
    assert found.records_of_one_place == {Kind.PUB: 2}


def test_a_cafe_and_a_gym_on_one_spot_are_two_places(tmp_path: Path):
    found = found_in(tmp_path, place(Q1, CAFE), place(Q1, GYM), place(Q1, PUB))
    assert [len(found.of_kind(kind)) for kind in KINDS] == [1, 1, 1]
    assert found.records_of_one_place == {}


def test_which_records_are_one_place_does_not_turn_on_the_order_of_the_file(tmp_path: Path):
    row = [place(beside(Q1, 20.0 * n), CAFE) for n in range(10)]
    one = found_in(tmp_path / "a", *row)
    other = found_in(tmp_path / "b", *reversed(row))
    assert one.places == other.places and len(one.places) == 5


# When nought is a count, and the edge of London


def test_nought_is_a_count_where_the_file_holds_something_within_reach(town: Found):
    assert OA_R2 in town.seen and town.counted(Kind.CAFE)[OA_R2] == 0.0


def test_where_the_file_holds_nothing_at_all_within_reach_nothing_is_known(tmp_path: Path):
    found = found_in(tmp_path, place(Q1, CAFE), place(beside(R1, 50), SHOP))
    assert OA_R2 not in found.seen and OA_R2 not in found.counted(Kind.CAFE)
    assert found.counted(Kind.CAFE)[OA_Q1] == 1.0 and found.counted(Kind.CAFE)[OA_R1] == 0.0


def test_an_output_area_with_homes_outside_london_within_reach_has_no_count(tmp_path: Path):
    found = found_in(tmp_path, centres=centres_at(outside=beside(Q4, 500)))
    assert found.reach.near_the_edge == (OA_Q4,)
    assert OA_Q4 not in found.counted(Kind.GYM)


# The evidence, and the row of the catalogue


@pytest.mark.parametrize("feature", MEASURES, ids=[str(feature) for feature in MEASURES])
def test_every_area_has_a_row_that_holds_the_figure_and_names_the_files_behind_it(
    tmp_path: Path, feature: FeatureId
):
    made = built(tmp_path, feature)
    assert [row.fact_id for row in made.rows] == [
        f"{area}/feature/{feature}" for area in sorted(made.worked)
    ]
    for row in made.rows:
        area = row.fact_id.split("/")[0]
        assert row.value == made.worked[area].value and row.state is made.worked[area].state
    assert sorted(receipt.source_id for receipt in made.files) == [
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        SOURCE,
    ]
    method = venues_nearby.MEASURES[feature].method
    assert {row.derivation_id for row in made.rows} == {method.derivation_id}
    assert Evidence.of("lon-2026-10-02-01", made.files, (method,), made.rows)
    assert made.geography is Geography.POINT


@pytest.mark.parametrize("feature", MEASURES, ids=[str(feature) for feature in MEASURES])
def test_core_names_each_figure_as_it_is_measured_so_a_build_carries_it(
    tmp_path: Path, feature: FeatureId
):
    metric = built(tmp_path, feature).metric
    core = FEATURES[feature]
    assert says_what_core_says(metric)
    assert (metric.label, metric.unit) == (core.label, core.unit)
    assert metric.native_resolution is NativeResolution.POINT
    # It cites the file of places, and the centres, the lookup and the homes beside it.
    assert metric.vintage == DAY and SOURCE in metric.source_ids and len(metric.source_ids) == 4
    # The count is shown, and the figure for each 1,000 homes is what is ranked on.
    assert metric.rankable is (feature not in RANKED_AS)
    assert metric.definition.endswith(".") and not re.search(r"[!?\n]", metric.definition)
    assert "Overture Maps Foundation" in metric.definition and DAY in metric.definition
    assert "800 metres in a straight line" in metric.definition
    assert ("for each 1,000 homes" in metric.definition) is venues_nearby.MEASURES[feature].rate


def test_the_six_are_measures_of_a_build_and_each_is_the_count_or_the_rate_of_a_kind():
    listed = {one.feature: one for one in measures.MEASURES}
    assert list(MEASURES) == [
        FeatureId.VENUE_CAFE,
        FeatureId.VENUE_CAFE_PER_HOMES,
        FeatureId.VENUE_GYM,
        FeatureId.VENUE_GYM_PER_HOMES,
        FeatureId.VENUE_EVENING,
        FeatureId.VENUE_EVENING_PER_HOMES,
    ]
    for feature, of in MEASURES.items():
        assert of.rate is (feature not in RANKED_AS)
        assert feature in (COUNT_OF[of.kind], RANKED_AS[COUNT_OF[of.kind]])
        one = listed[feature]
        assert (one.source, one.methods, one.cannot_see) == (SOURCE, (of.method,), of.cannot_see)
        assert not (one.waits_on or one.held_back or one.in_parts or one.in_squares)
    assert {RANKED_AS[count] for count in COUNT_OF.values()} == {
        feature for feature, of in MEASURES.items() if of.rate
    }
    with pytest.raises(ValueError, match="no measure of cafes, gyms or pubs"):
        venues_nearby.builder(FeatureId.CULTURE_VENUES)


def test_pubs_are_in_going_out_as_the_figure_for_each_1000_homes():
    parts = {term.feature_id: term.hundredths for term in TAGS[TagId.PACE].terms}
    assert parts[FeatureId.VENUE_EVENING_PER_HOMES] == 35
    assert FeatureId.VENUE_EVENING not in parts


# What is said beside a figure


@pytest.mark.parametrize("feature", MEASURES, ids=[str(feature) for feature in MEASURES])
def test_what_a_figure_cannot_see_is_said_in_whole_sentences(feature: FeatureId):
    lines = MEASURES[feature].cannot_see
    assert len(lines) == len(set(lines)) >= 12
    for said in lines:
        assert re.fullmatch(r"[A-Z][^!\n|]+\.", said), said
    together = " ".join(lines)
    assert "not the day of each record" in together and "not a walk" in together
    assert ("reads highest where few homes are" in together) is MEASURES[feature].rate
    assert ("dense and central" in together) is not MEASURES[feature].rate


def test_a_figure_of_pubs_says_that_the_file_is_thin_at_the_edge_and_counts_no_nightclub():
    for feature, of in MEASURES.items():
        said = " ".join(of.cannot_see)
        assert (THIN_AT_THE_EDGE in of.cannot_see) is (of.kind is Kind.PUB), feature
        assert ("A nightclub" in said) is (of.kind is Kind.PUB)
        assert ("A trainer" in said) is (of.kind is Kind.GYM)


def test_why_pubs_are_counted_from_the_file_is_said_and_names_no_place():
    said = " ".join(PUBS_ARE_FROM_THE_FILE)
    for words in (
        "councils do not give kinds alike",
        "is not confirmed",
        "the file stands in its place",
        "not the better of the two everywhere",
        "No name was read of either",
    ):
        assert words in said
    names = re.compile(r"\b(Westminster|Camden|Hackney|Bexley|Bromley|Harrow|London Borough)\b")
    for sentence in (*PUBS_ARE_FROM_THE_FILE, THIN_AT_THE_EDGE):
        assert sentence.endswith(".") and not re.search(r"[!|\n]", sentence)
        assert not names.search(sentence)


def test_no_word_of_the_measures_says_who_lives_or_goes_anywhere():
    words = re.compile(r"\b(residents?|people who|students?|families|young|elderly)\b", re.I)
    for of in MEASURES.values():
        for said in (of.label, *of.cannot_see):
            assert not words.search(said), said


# The gate, and what is read


def test_with_no_file_of_places_there_is_no_figure_and_nothing_is_filled_in(tmp_path: Path):
    inputs = inputs_of(tmp_path, None)
    with pytest.raises(LockError) as refused:
        venues_nearby.build(FeatureId.VENUE_CAFE, inputs, spine.build(inputs))
    assert refused.value.rule == "input_has_one_receipt"


def test_a_category_of_a_branch_that_is_read_that_is_on_no_table_stops_the_build(
    tmp_path: Path,
):
    inputs = inputs_of(tmp_path, (place(Q1, (*DRINK, "bar", "zzyzx_parva_bar")),))
    with pytest.raises(LockError) as refused:
        venues_nearby.found_of(inputs, spine.build(inputs))
    assert refused.value.rule == "input_is_as_described"
    assert "zzyzx" not in str(refused.value)


def test_nothing_the_measure_gives_back_holds_a_name_of_a_place(tmp_path: Path):
    assert CANARY not in repr(built(tmp_path, FeatureId.VENUE_EVENING_PER_HOMES))


def test_built_twice_from_the_same_file_the_figures_and_the_rows_are_the_same(tmp_path: Path):
    one = built(tmp_path / "a", FeatureId.VENUE_GYM_PER_HOMES)
    other = built(tmp_path / "b", FeatureId.VENUE_GYM_PER_HOMES)
    assert (one.worked, one.rows, one.metric) == (other.worked, other.rows, other.metric)


def test_the_order_of_the_rows_of_a_file_changes_no_figure(tmp_path: Path):
    one = built(tmp_path / "a", FeatureId.VENUE_EVENING, *IN_THE_TOWN)
    other = built(tmp_path / "b", FeatureId.VENUE_EVENING, *reversed(IN_THE_TOWN))
    assert one.worked == other.worked
