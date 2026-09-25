"""Places to eat and drink, from the register to a figure for each area.

Every file here is made up, and says so. `food_support.py` draws the town and
writes its register. The centres stand 1,000 metres apart, so that a home is
within reach of what stands by its own centre and of little else, and every
count can be made by hand:

    Quillhaven 001   Q1  three places to eat, a pub and a takeaway, each 100 metres off
                     Q2  one place to eat, 500 metres east, half way to Q3
                     Q3  the same place to eat, 500 metres west
                     Q4  a pub 790 metres north. A takeaway 810 metres north is out of reach
    Quillhaven 002   R1  one takeaway. R2, R3 and R4 have nothing within reach
    Tallowgate 001   T1  two places to eat and a pub. T2, T3 and T4 have nothing

The town stands far east of the grid's middle, where 1,000 metres on the grid
are 999.3 on the ground. So 790 on the grid is within 800, and 810 is not.
"""

import re
from collections.abc import Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, RANKED_AS, TAG_MIN_COVERAGE_HUNDREDTHS, TAGS
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.derive import (
    food_register,
    measures,
    venue_food_drink,
    venue_food_drink_per_homes,
)
from burro_pipeline.derive.culture_reach import (
    kept,
    metres_between,
    metres_to_a_degree,
    within,
    within_at,
)
from burro_pipeline.derive.food_register import Group
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.venue_food_drink import FOOD_AND_DRINK, METRES, Venues
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .food_support import (
    CANARY,
    DAY,
    EAT,
    IN_QUILLHAVEN,
    IN_TALLOWGATE,
    LATER,
    OAS,
    ONE,
    PUB,
    Q1,
    Q2,
    QUILLHAVEN,
    R1,
    SHOP,
    SOURCE,
    T1,
    T4,
    TAKEAWAY,
    TALLOWGATE,
    THREE,
    TWO,
    Business,
    Metres,
    beside,
    centres_at,
    inputs_of,
    register_receipt,
    register_xml,
)

OA_Q1, OA_Q2, OA_Q3, OA_Q4 = OAS[:4]
OA_R1, OA_T1, OA_T4 = OAS[4], OAS[8], OAS[11]


def built(
    folder: Path,
    quillhaven: Sequence[Business] = IN_QUILLHAVEN,
    tallowgate: Sequence[Business] = IN_TALLOWGATE,
    centres: bytes | None = None,
) -> Venues:
    registers = {
        QUILLHAVEN: register_xml(quillhaven, QUILLHAVEN),
        TALLOWGATE: register_xml(tallowgate, TALLOWGATE),
    }
    inputs = inputs_of(folder, registers, centres)
    return venue_food_drink.build(inputs, spine.build(inputs))


def refused(folder: Path, **given: Sequence[Business]) -> LockError:
    """The refusal of a register that is not London's, which repeats nothing a file holds."""
    registers = {
        code.removeprefix("of_"): register_xml(held, code.removeprefix("of_"))
        for code, held in given.items()
    }
    inputs = inputs_of(folder, registers)
    with pytest.raises(LockError) as stopped:
        venue_food_drink.build(inputs, spine.build(inputs))
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


# What is within reach


def test_each_home_is_given_the_places_within_reach_of_its_own_centre(tmp_path: Path):
    reach = built(tmp_path).reach
    assert reach.metres == 800 and reach.groups == (Group.EAT, Group.PUB, Group.TAKEAWAY)
    assert reach.places[OA_Q1] == (3, 1, 1)
    assert reach.places[OA_Q2] == reach.places[OA_Q3] == (1, 0, 0)
    assert reach.places[OA_T1] == (2, 1, 0)
    assert reach.places[OA_R1] == (0, 0, 1)
    assert sum(sum(found) for found in reach.places.values()) == 12
    assert set(reach.places) == set(OAS) and reach.near_the_edge == ()


def test_a_place_at_790_metres_is_within_reach_and_one_at_810_is_not(tmp_path: Path):
    """The pub stands 790 metres north of the last centre of the area, and the takeaway 810."""
    assert built(tmp_path).reach.places[OA_Q4] == (0, 1, 0)


def test_a_place_between_two_centres_is_within_reach_of_both(tmp_path: Path):
    """A high street on a border serves both sides."""
    between = (Business(EAT, beside(Q2, 500)), Business(EAT, Q1))
    reach = built(tmp_path, between).reach
    assert reach.places[OA_Q2] == reach.places[OA_Q3] == (1, 0, 0)
    assert reach.places[OA_Q1] == (1, 0, 0) and reach.places[OA_Q4] == (0, 0, 0)


def test_a_business_with_no_point_is_within_reach_of_nobody(tmp_path: Path):
    """It is counted by the parser, and it is never put at the centre of its authority."""
    nowhere = (Business(EAT, Q1), *[Business(EAT, None)] * 40)
    found = built(tmp_path, nowhere)
    assert found.register.listed(Group.EAT) == 43 and found.register.placed(Group.EAT) == 3
    assert sum(held[0] for held in found.reach.places.values()) == 3
    assert [value_of(found.worked[area]) for area in (ONE, TWO)] == [0.2, 0.0]


def test_a_kind_that_is_no_place_to_eat_or_drink_is_not_counted(tmp_path: Path):
    """A shop, a school, a caterer, a van and a hotel stand beside the first centre."""
    beside_the_first = sum(
        business.at is not None and abs(business.at[0]) < 200 and abs(business.at[1]) < 200
        for business in IN_QUILLHAVEN
    )
    assert beside_the_first == 10
    assert sum(built(tmp_path).reach.places[OA_Q1]) == 5
    only = (Business(SHOP, Q1), Business(EAT, R1))
    assert value_of(built(tmp_path / "a-shop", only).worked[ONE]) == 0.0


def test_the_homes_within_reach_are_those_of_every_centre_within_the_same_distance(
    tmp_path: Path,
):
    assert built(tmp_path).reach.homes == {
        oa: 100 + 10 * number for number, oa in enumerate(OAS, start=1)
    }


# The distance


def test_a_degree_is_as_many_metres_as_the_earth_makes_it():
    """At the equator a degree east is 111,319.49 metres and a degree north 110,574.28.

    At a pole a degree north is 111,693.98 metres, and a degree east is none.
    """
    east, north = metres_to_a_degree(0.0)
    assert (round(east, 2), round(north, 2)) == (111_319.49, 110_574.28)
    east, north = metres_to_a_degree(90.0)
    assert (round(east, 2), round(north, 2)) == (0.0, 111_693.98)


def test_a_distance_is_the_same_whichever_way_it_is_measured_on_the_grid():
    """On the middle line of the National Grid 1,000 metres on the grid are 1,000.4 on the ground.

    The grid is drawn 4 parts in 10,000 small along its middle line, and the
    pipeline's one fixed operation is good to 2 metres.
    """
    for north in (150_000, 180_000, 200_000):
        a, b = (
            longitude_and_latitude(400_000, north),
            longitude_and_latitude(400_000, north + 1_000),
        )
        assert abs(metres_between(a, b) - 1_000.4) < 0.3
        a, b = longitude_and_latitude(400_000, north), longitude_and_latitude(401_000, north)
        assert abs(metres_between(a, b) - 1_000.4) < 0.3
    # London stands 130 kilometres east of the middle line, where the grid is drawn nearly true.
    a, b = longitude_and_latitude(530_000, 180_000), longitude_and_latitude(530_600, 180_800)
    assert abs(metres_between(a, b) - 1_000.2) < 0.3


def test_a_place_is_within_reach_up_to_the_distance_and_not_beyond_it():
    at = (-0.1, 51.5)
    _, north = metres_to_a_degree(at[1])
    for metres, how_many in ((0.0, 1), (799.999, 1), (800.001, 0)):
        place = (at[0], at[1] + metres / north, 0, 1)
        assert within(kept([place]), at, METRES, 1) == [how_many], metres


# The figures


def test_an_area_is_given_what_is_within_reach_of_its_typical_home(tmp_path: Path):
    found = built(tmp_path).worked
    # Of 500 homes, 110 have five places within reach and the other 390 have one.
    assert (110 * 5 + 120 * 1 + 130 * 1 + 140 * 1) / 500 == 1.88
    assert found[ONE] == Worked(1.9, 4, 4, 1.0, State.PRESENT)
    # Of 660 homes, 150 have one. Of 820, 190 have three.
    assert found[TWO] == Worked(0.2, 4, 4, 1.0, State.PRESENT)
    assert found[THREE] == Worked(0.7, 4, 4, 1.0, State.PRESENT)


def test_an_area_with_nothing_within_reach_reads_nought_and_is_a_figure(tmp_path: Path):
    """The register covers it: each borough has its file, and no home outside London is near."""
    found = built(tmp_path, (Business(EAT, Q1),), (Business(PUB, T1),))
    assert found.worked[TWO] == Worked(0.0, 4, 4, 1.0, State.PRESENT)
    assert found.rate[TWO] == Worked(0.0, 4, 4, 1.0, State.PRESENT)


def test_the_second_figure_is_the_places_for_each_thousand_homes_within_the_same_reach(
    tmp_path: Path,
):
    """One sum over another. Each home has its own output area within reach and no other."""
    found = built(tmp_path).rate
    top = 110 * 5 + 120 * 1 + 130 * 1 + 140 * 1
    bottom = 110 * 110 + 120 * 120 + 130 * 130 + 140 * 140
    assert round(1000 * top / bottom, 4) == 14.9206
    assert found[ONE] == Worked(14.9, 4, 4, 1.0, State.PRESENT)
    assert round(1000 * 150 / (150**2 + 160**2 + 170**2 + 180**2), 4) == 1.3711
    assert found[TWO] == Worked(1.4, 4, 4, 1.0, State.PRESENT)


def test_the_second_figure_is_never_a_mean_of_rates(tmp_path: Path):
    """The mean of what each home has for each thousand homes about it would be 16.0."""
    each = [(110, 5 / 110), (120, 1 / 120), (130, 1 / 130), (140, 1 / 140)]
    assert round(1000 * sum(homes * rate for homes, rate in each) / 500, 1) == 16.0
    assert value_of(built(tmp_path).rate[ONE]) == 14.9


def test_more_homes_within_reach_make_the_second_figure_smaller_and_leave_the_first(
    tmp_path: Path,
):
    """The last centre is brought to 700 metres from the first, and 900 from the one place."""
    only = (Business(EAT, beside(Q1, -200)), Business(EAT, R1))
    nearer = centres_at(moved={OA_Q4: beside(Q1, 700)})
    apart, near = built(tmp_path / "apart", only), built(tmp_path / "near", only, centres=nearer)
    assert (apart.reach.homes[OA_Q1], near.reach.homes[OA_Q1]) == (110, 110 + 140)
    assert near.reach.places[OA_Q1] == (1, 0, 0) and near.reach.places[OA_Q4] == (0, 0, 0)
    assert (apart.worked[ONE].value, near.worked[ONE].value) == (0.2, 0.2)
    bottom = 110 * 250 + 120 * 260 + 130 * 130 + 140 * 370
    assert (round(1000 * 110 / 63_000, 3), round(1000 * 110 / bottom, 3)) == (1.746, 0.863)
    assert (apart.rate[ONE].value, near.rate[ONE].value) == (1.7, 0.9)


def test_the_order_of_the_businesses_and_of_the_files_changes_nothing(tmp_path: Path):
    turned = built(tmp_path, tuple(reversed(IN_QUILLHAVEN)), tuple(reversed(IN_TALLOWGATE)))
    as_written = built(tmp_path / "as-written")
    assert turned.worked == as_written.worked and turned.rate == as_written.rate
    assert turned.reach == as_written.reach


# The edge of London


def near(centre: Metres, east: float) -> bytes:
    """The centres, with the output area outside London so far east of a centre."""
    return centres_at(outside=beside(centre, east))


def test_an_output_area_with_a_home_outside_london_within_reach_has_no_verdict(tmp_path: Path):
    """A place outside London may be within its reach, and no file of it was read."""
    found = built(tmp_path, centres=near(T4, 700))
    assert found.reach.near_the_edge == (OA_T4,)
    assert OA_T4 not in found.reach.places and OA_T4 not in found.reach.homes
    # 220 of the 820 homes of the area are near the edge. The figure is of the other 600.
    assert found.worked[THREE] == Worked(1.0, 3, 4, round(600 / 820, 6), State.PARTIAL)
    assert found.worked[ONE] == Worked(1.9, 4, 4, 1.0, State.PRESENT)


def test_a_home_outside_london_that_is_out_of_reach_changes_nothing(tmp_path: Path):
    found = built(tmp_path, centres=near(T4, 810))
    assert found.reach.near_the_edge == ()
    assert found.worked == built(tmp_path / "far").worked


def test_below_half_the_homes_no_figure_is_given(tmp_path: Path):
    """Three of the four centres of the area are within reach of homes outside London."""
    outside = [beside(centre, 0, 300) for centre in (beside(T1, 1_000), beside(T1, 2_000), T4)]
    found = built(tmp_path, centres=centres_at(more=outside))
    assert len(found.reach.near_the_edge) == 3
    assert found.worked[THREE] == Worked(None, 1, 4, round(190 / 820, 6), State.BELOW_THRESHOLD)
    assert found.rate[THREE] == Worked(None, 1, 4, round(190 / 820, 6), State.BELOW_THRESHOLD)


def test_an_area_wholly_near_the_edge_is_a_gap_and_never_nought(tmp_path: Path):
    outside = [beside(centre, 0, 300) for centre in (R1, beside(R1, 1_000), beside(R1, 2_000))]
    outside.append(beside(R1, 3_000, 300))
    found = built(tmp_path, centres=centres_at(more=outside))
    assert found.worked[TWO] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert found.rate[TWO] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)


def test_an_output_area_with_no_centre_has_no_verdict_and_is_not_given_a_neighbours(
    tmp_path: Path,
):
    found = built(tmp_path, centres=centres_at(without=[OA_Q1]))
    assert OA_Q1 not in found.reach.places
    # The first output area holds 110 of the area's 500 homes. Each of the others has one place.
    assert found.worked[ONE] == Worked(1.0, 3, 4, round(390 / 500, 6), State.PARTIAL)


# The register is held to London


def test_every_borough_has_its_file_and_each_file_is_of_one_borough(tmp_path: Path):
    assert built(tmp_path).reach.borough_of == {QUILLHAVEN: "E09000901", TALLOWGATE: "E09000902"}


def test_a_borough_with_no_file_stops_the_build(tmp_path: Path):
    """Nought in Tallowgate would be no count: nothing says what is there."""
    stopped = refused(tmp_path, of_901=IN_QUILLHAVEN)
    assert stopped.rule == "input_is_as_described"
    assert "one file for each borough" in str(stopped)


def test_two_files_of_one_borough_stop_the_build(tmp_path: Path):
    stopped = refused(
        tmp_path, of_901=IN_QUILLHAVEN, of_902=IN_TALLOWGATE, of_903=(Business(EAT, Q2),)
    )
    assert "one file for each borough" in str(stopped)


def test_a_file_whose_businesses_lie_in_another_borough_stops_the_build(tmp_path: Path):
    """The file named for Tallowgate holds what stands in Quillhaven."""
    stopped = refused(tmp_path, of_901=IN_QUILLHAVEN, of_902=(Business(EAT, Q1), Business(PUB, Q2)))
    assert "one file for each borough" in str(stopped)


def test_a_file_that_places_nothing_near_a_home_is_of_no_borough(tmp_path: Path):
    far = (Business(EAT, beside(T1, 0, 300)), Business(EAT, None))
    assert "one file for each borough" in str(refused(tmp_path, of_901=IN_QUILLHAVEN, of_902=far))


def test_a_business_listed_by_one_authority_and_standing_in_another_is_counted_where_it_stands(
    tmp_path: Path,
):
    """The register says where a business is, and an authority may list one beyond its border."""
    found = built(tmp_path, (*IN_QUILLHAVEN, Business(PUB, beside(T4, 50))))
    assert found.reach.places[OA_T4] == (0, 1, 0)
    assert found.reach.borough_of[QUILLHAVEN] == "E09000901"


# The gate, the receipts and the store


def without_scoring(source_id: str) -> Registry:
    sources = [
        source.model_copy(update={"uses": (Use.VALIDATION_ONLY,)})
        if source.id == source_id
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_the_register_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=without_scoring(SOURCE))
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        venue_food_drink.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert inputs.opened == before


def test_a_build_with_no_file_of_the_register_leaves_the_measure_out(tmp_path: Path):
    """The step that puts a release together reads this rule, and goes on."""
    inputs = inputs_of(tmp_path, {})
    with pytest.raises(LockError) as stopped:
        venue_food_drink.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    venue_food_drink.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


# The evidence


def test_every_area_has_a_row_of_evidence_for_each_of_the_two_figures(tmp_path: Path):
    found = built(tmp_path, centres=near(T4, 700))
    areas = (ONE, TWO, THREE)
    assert [row.fact_id for row in found.rows] == [
        f"{area}/feature/venue_food_drink" for area in areas
    ]
    assert [row.fact_id for row in found.rows_of_the_rate] == [
        f"{area}/feature/venue_food_drink_per_homes" for area in areas
    ]
    assert [row.state for row in found.rows] == [State.PRESENT, State.PRESENT, State.PARTIAL]
    assert [row.value for row in found.rows] == [found.worked[area].value for area in areas]
    assert [row.value for row in found.rows_of_the_rate] == [
        found.rate[area].value for area in areas
    ]


def test_a_row_names_every_file_of_the_register_the_centres_the_lookup_and_the_homes(
    tmp_path: Path,
):
    found = built(tmp_path)
    by_source: dict[str, list[str]] = {}
    for receipt in found.files:
        by_source.setdefault(receipt.source_id, []).append(receipt.file_id)
    assert sorted(by_source) == sorted([SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES])
    assert len(by_source[SOURCE]) == 2
    every = tuple(sorted(file_id for held in by_source.values() for file_id in held))
    for row in (*found.rows, *found.rows_of_the_rate):
        assert row.inputs == every
        assert row.retrieved_on == "2026-09-23"
        # From the day of the census, which the weights are of, to the day of the extract.
        assert row.data_period == Period(start="2021-03-21", end=DAY)
    assert {row.derivation_id for row in found.rows} == {"places_within_800m_at_homes@1"}
    assert {row.derivation_id for row in found.rows_of_the_rate} == {
        "places_per_1000_homes_within_800m@1"
    }


def test_the_methods_say_the_distance_and_that_it_is_a_straight_line():
    count, rate = venue_food_drink.METHODS
    for method in (count, rate):
        assert method.kind is Kind.MEASURED
        assert method.parameters["metres"] == METRES == 800
        assert "800 metres, in a straight line" in method.sentence
        # Every measure of venues has the one record of each method, from the one module.
        assert method.code == "burro_pipeline.derive.culture_reach"
    assert rate.parameters["per_homes"] == 1000 and "times 1000" in rate.sentence
    assert within_at(400).derivation_id == "places_within_400m_at_homes@1"
    assert count == within_at(METRES)


def test_the_methods_say_what_the_rule_at_the_edge_of_london_is_and_claim_no_more():
    """The rule asks where homes outside London are. It does not ask where land is.

    A check found output areas with land outside London within reach and no home on it.
    They are counted, so a method may not say that the source covers their whole reach.
    """
    for method in venue_food_drink.METHODS:
        said = method.sentence
        assert "whose whole reach the source covers" not in said
        assert "leaving out every output area" in said
        assert "homes of an output area outside London are taken to stand within" in said
        assert "land outside London with no home near may still be within reach" in said
        assert "under 50 in 100 of the area's homes are in an output area that is counted" in said
        # What is true of the register alone is said beside a figure, and not of every source.
        assert "the file of its authority" not in said and "missed" not in said
    assert "missed" in venue_food_drink.AT_THE_EDGE and "land outside London" in (
        venue_food_drink.AT_THE_EDGE
    )
    assert venue_food_drink.AT_THE_EDGE in venue_food_drink.CANNOT_SEE


def test_the_evidence_of_the_measure_has_no_loose_end(tmp_path: Path):
    """Every row names a method and files that the evidence of a release would hold."""
    found = built(tmp_path)
    rows = (*found.rows, *found.rows_of_the_rate)
    evidence = Evidence.of("lon-2026-10-02-01", found.files, venue_food_drink.METHODS, rows)
    assert len(evidence.rows) == 6
    assert found.geography is Geography.POINT


# The name, the unit and the sentences


def test_the_row_of_the_catalogue_says_a_count_within_reach_as_core_does(tmp_path: Path):
    metric = built(tmp_path).metric
    feature = FEATURES[FeatureId.VENUE_FOOD_DRINK]
    assert metric.feature_id is FeatureId.VENUE_FOOD_DRINK
    assert metric.label == "Places to eat and drink within 800 m of home, in a straight line"
    assert (metric.label, metric.unit) == (feature.label, feature.unit)
    assert metric.unit == "count"
    assert (metric.dimension, metric.polarity) == (feature.dimension, feature.polarity)
    assert metric.polarity is Polarity.EITHER
    assert metric.native_resolution is NativeResolution.POINT
    assert measures.says_what_core_says(metric)
    assert metric.source_ids == tuple(sorted(metric.source_ids)) and len(metric.source_ids) == 4


def test_the_count_is_shown_and_no_area_is_ranked_on_it(tmp_path: Path):
    """Decided on 2026-09-24: both figures are shown, and a wish is ranked on the second."""
    assert FeatureId.VENUE_FOOD_DRINK in RANKED_AS
    assert venue_food_drink.RANKABLE is False
    assert built(tmp_path).metric.rankable is False
    # What a check of its figures found is still said beside it.
    assert venue_food_drink.FOLLOWS_DENSITY in venue_food_drink.CANNOT_SEE
    assert "dense and central" in venue_food_drink.FOLLOWS_DENSITY


def test_the_places_for_each_thousand_homes_are_a_measure_of_their_own_and_are_ranked_on(
    tmp_path: Path,
):
    registers = {
        QUILLHAVEN: register_xml(IN_QUILLHAVEN, QUILLHAVEN),
        TALLOWGATE: register_xml(IN_TALLOWGATE, TALLOWGATE),
    }
    inputs = inputs_of(tmp_path / "rate", registers, None)
    rate = venue_food_drink_per_homes.build(inputs, spine.build(inputs))
    count = built(tmp_path / "count")
    feature = FEATURES[FeatureId.VENUE_FOOD_DRINK_PER_HOMES]
    assert rate.metric.feature_id is feature.feature_id is venue_food_drink_per_homes.FEATURE
    assert (rate.metric.label, rate.metric.unit) == (feature.label, feature.unit)
    assert rate.metric.label == (
        "Places to eat and drink for each 1,000 homes within 800 m, in a straight line"
    )
    assert (rate.metric.unit, rate.metric.rankable) == ("per 1,000 homes", True)
    assert measures.says_what_core_says(rate.metric)
    # It is the second figure of the count, with its own rows, and rests on the same files.
    assert rate.worked == count.rate and rate.rows == count.rows_of_the_rate
    assert {row.fact_id.rsplit("/", 1)[1] for row in rate.rows} == {"venue_food_drink_per_homes"}
    assert venue_food_drink_per_homes.KEY == "venue_food_drink_per_homes"
    method = venue_food_drink_per_homes.METHOD
    assert {row.derivation_id for row in rate.rows} == {method.derivation_id}
    assert venue_food_drink_per_homes.METHODS == (venue_food_drink.METHOD_OF_THE_RATE,)
    assert rate.files == count.files and rate.geography is count.geography
    assert "for each 1,000 homes" in rate.metric.definition
    assert venue_food_drink_per_homes.CANNOT_SEE == venue_food_drink.CANNOT_SEE_OF_THE_RATE


def test_nothing_holds_the_two_measures_back_and_the_registers_pubs_are_no_measure():
    """The hold on the count was lifted when core came to say what was decided. The pubs are
    counted from the file of places, and the register's pubs alone join no build. Private
    outdoor space is held for another reason: its audit has not been run."""
    listed = {one.feature: one for one in measures.MEASURES}
    for feature in (FeatureId.VENUE_FOOD_DRINK, FeatureId.VENUE_FOOD_DRINK_PER_HOMES):
        assert (listed[feature].held_back, listed[feature].waits_on) == ((), ())
        assert listed[feature].in_parts and not listed[feature].in_squares
    assert venue_food_drink.HELD_BACK == () and venue_food_drink.WAITS_ON == ()
    # One measure is held back, and by no check of these figures: the register's pubs alone
    # are no measure of a build.
    held = [one.feature for one in measures.MEASURES if one.held_back]
    assert held == [FeatureId.PRIVATE_OUTDOOR_SPACE]
    assert listed[FeatureId.VENUE_EVENING].source != venue_food_drink.SOURCE


def test_core_scores_no_tag_from_the_count():
    """The count says little of its own, so no recipe holds it: a vibe is ranked on the rate."""
    given = {
        str(tag_id): sum(
            term.hundredths for term in tag.terms if term.feature_id is FeatureId.VENUE_FOOD_DRINK
        )
        for tag_id, tag in sorted(TAGS.items())
    }
    # Going out and Food and drink are ranked on the places for each 1,000 homes.
    assert {tag_id: share for tag_id, share in given.items() if share} == {}
    of_the_rate = {
        str(tag_id): term.hundredths
        for tag_id, tag in sorted(TAGS.items())
        for term in tag.terms
        if term.feature_id is FeatureId.VENUE_FOOD_DRINK_PER_HOMES
    }
    assert of_the_rate == {"foodie": 40, "pace": 30, "young_professionals": 20}
    assert max(of_the_rate.values()) < TAG_MIN_COVERAGE_HUNDREDTHS == 60


def test_what_is_not_settled_of_the_register_is_said_beside_each_figure():
    said = " ".join(venue_food_drink.OF_THE_REGISTER)
    for words in ("no point", "postcode directory", "land outside London", "how long ago"):
        assert words in said
    for line in (
        venue_food_drink.NO_POINT,
        venue_food_drink.AT_THE_EDGE,
        venue_food_drink.HOW_LONG_AGO,
    ):
        assert line in venue_food_drink.CANNOT_SEE
        assert line in venue_food_drink.CANNOT_SEE_OF_THE_RATE


def test_the_date_of_a_figure_is_the_days_of_the_extracts(tmp_path: Path):
    """The registry asks that the date of the data stands wherever a figure appears."""
    assert built(tmp_path).metric.vintage == DAY
    later = register_xml(IN_TALLOWGATE, TALLOWGATE, day=LATER)
    inputs = inputs_of(
        tmp_path / "two-days",
        {QUILLHAVEN: register_xml(IN_QUILLHAVEN)},
        more=[(register_receipt(later, TALLOWGATE, LATER), later)],
    )
    found = venue_food_drink.build(inputs, spine.build(inputs))
    assert found.metric.vintage == f"{DAY} to {LATER}"
    assert f"as at {DAY} to {LATER}" in found.metric.definition
    assert all(row.data_period == Period(start="2021-03-21", end=LATER) for row in found.rows)


def test_the_definition_is_one_sentence_that_says_what_the_figure_is_and_is_not(tmp_path: Path):
    definition = built(tmp_path).metric.definition
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        "Food Standards Agency",
        "Pub/bar/nightclub, Restaurant/Cafe/Canteen or Takeaway/sandwich shop",
        f"as at {DAY}",
        "within 800 metres in a straight line",
        "census of 2021",
        "to 1 decimal place",
        "not along any street",
        "gives no point for is not counted",
        "has closed and is still listed",
    ):
        assert words in definition
    rate = venue_food_drink.definition_of(FOOD_AND_DRINK, DAY, rate=True)
    assert rate.endswith(".") and not re.search(r"[.!?]\s|\n", rate)
    assert "for each 1,000 homes" in rate and "before one is divided by the other" in rate


def test_what_it_cannot_see_is_what_a_register_cannot():
    said = " ".join(venue_food_drink.CANNOT_SEE)
    assert "has closed and is still listed" in said
    assert "trades and is not registered" in said
    assert "not a walk" in said and "no point" in said and "edge of London" in said
    assert "councils do not give kinds alike" in said and len(venue_food_drink.CANNOT_SEE) == 10
    assert len(set(venue_food_drink.CANNOT_SEE)) == 10
    for sentence in venue_food_drink.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)


def test_what_a_check_of_the_figures_found_is_said_beside_the_figure():
    """Each is a thing a reader of the count would otherwise take it to say."""
    said = venue_food_drink.CANNOT_SEE
    # It follows how built up and how central an area is, and says little of its own.
    assert venue_food_drink.FOLLOWS_DENSITY in said
    assert "how built up an area is" in venue_food_drink.FOLLOWS_DENSITY
    assert "little more than that an area is dense and central" in venue_food_drink.FOLLOWS_DENSITY
    # Nothing that is read says how old a record is.
    assert venue_food_drink.HOW_LONG_AGO in said
    assert "how long ago a council last saw a place" in venue_food_drink.HOW_LONG_AGO
    # A point is not always a door.
    assert venue_food_drink.SHARED_POINT in said
    assert "a point that another shares" in venue_food_drink.SHARED_POINT
    # An area under a council that gives few points reads low.
    assert "reads lower" in venue_food_drink.NO_POINT
    # The homes that weigh a figure are those of the census.
    assert venue_food_drink.AS_AT_THE_CENSUS in said
    assert "built since" in venue_food_drink.AS_AT_THE_CENSUS


def test_the_figure_for_each_thousand_homes_says_what_it_divides_by_and_where_it_reads_high():
    """It divides the places of one year by the homes of another, and leads where homes are few."""
    of_the_rate = venue_food_drink.CANNOT_SEE_OF_THE_RATE
    assert venue_food_drink.FOLLOWS_DENSITY not in of_the_rate
    assert set(venue_food_drink.CANNOT_SEE) - set(of_the_rate) == {venue_food_drink.FOLLOWS_DENSITY}
    more = [line for line in of_the_rate if line not in venue_food_drink.CANNOT_SEE]
    assert len(more) == 2
    assert "homes of the last census" in more[0] and "reads too high" in more[0]
    assert "where few homes are" in more[1] and "offices" in more[1]
    assert "not ranked on" not in " ".join(of_the_rate)
    for sentence in of_the_rate:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)
        assert not RESIDENT_WORDS.search(sentence) and not NEVER_SAID.search(sentence)


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)
NEVER_SAID = re.compile(r"\b(rating|rated|hygiene rating|stars?|endorse[sd]?|approved by)\b", re.I)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(tmp_path: Path):
    found = built(tmp_path)
    rate = venue_food_drink.definition_of(FOOD_AND_DRINK, DAY, rate=True)
    sentences = (found.metric.definition, found.metric.label, rate, *venue_food_drink.CANNOT_SEE)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_no_sentence_of_the_measure_speaks_of_a_rating_or_of_the_agencys_backing(tmp_path: Path):
    """The registry forbids a rating, and asks that nothing implies the agency endorses it."""
    found = built(tmp_path)
    sentences = (
        found.metric.definition,
        found.metric.label,
        *venue_food_drink.CANNOT_SEE,
        *venue_food_drink.CANNOT_SEE_OF_THE_RATE,
        *venue_food_drink.OF_THE_REGISTER,
        *(method.sentence for method in venue_food_drink.METHODS),
    )
    assert [sentence for sentence in sentences if NEVER_SAID.search(sentence)] == []


def test_the_measure_reads_the_files_the_parser_reads_and_no_other():
    assert venue_food_drink.is_a_file("FHRS501en-GB.xml")
    assert not venue_food_drink.is_a_file("made-up-register-501.xml")
    assert venue_food_drink.SOURCE == food_register.SOURCE == SOURCE
    assert TAKEAWAY[0] in FOOD_AND_DRINK.kinds and len(FOOD_AND_DRINK.kinds) == 3
