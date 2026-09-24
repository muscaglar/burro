"""The share of an area's homes that are near what is measured.

Every number here is made up. The town is four output areas in two areas, and
small enough that each figure can be worked out by hand beside the test.

    area north:  n1 (100 homes)  n2 (300 homes)
    area south:  s1 (200 homes)  s2 (200 homes)

The method is handed a verdict for each output area: whether its centre is
within the distance. How far a centre is from a line is for the measure to
say, and is tested with the measure.
"""

import math
import re
from pathlib import Path

import burro_pipeline
import pytest
from burro_pipeline.cells.spine import Homes
from burro_pipeline.derive.methods import (
    METHODS,
    Worked,
    homes_within,
    homes_within_at,
    row_of,
)
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence

from .test_methods import FILES

NORTH, SOUTH = "lon-nnorth", "lon-nsouth"
HOMES = Homes(
    area_of={"n1": NORTH, "n2": NORTH, "s1": SOUTH, "s2": SOUTH},
    homes={"n1": 100, "n2": 300, "s1": 200, "s2": 200},
)
NEAR = {"n1": True, "n2": False, "s1": False, "s2": False}


# The figure


def test_the_share_is_the_homes_of_the_output_areas_that_are_near_over_all_the_homes():
    found = homes_within(NEAR, HOMES, times=100)
    # 100 of the 400 homes of the north are in the output area that is near.
    assert found[NORTH] == Worked(25.0, 2, 2, 1.0, State.PRESENT)


def test_an_area_with_no_home_near_is_at_nought_and_nought_is_a_figure():
    found = homes_within(NEAR, HOMES, times=100)
    assert found[SOUTH] == Worked(0.0, 2, 2, 1.0, State.PRESENT)


def test_an_area_with_every_home_near_is_at_a_hundred():
    found = homes_within(dict.fromkeys(NEAR, True), HOMES, times=100)
    assert [one.value for one in found.values()] == [100.0, 100.0]


def test_the_share_is_by_homes_and_never_by_how_many_output_areas_are_near():
    found = homes_within({"n1": False, "n2": True, "s1": True, "s2": False}, HOMES, times=100)
    # One output area of two is near in each. 300 of 400 homes, and 200 of 400.
    assert (found[NORTH].value, found[SOUTH].value) == (75.0, 50.0)


def test_without_a_multiplier_the_figure_is_a_share_of_one():
    assert homes_within(NEAR, HOMES)[NORTH].value == 0.25


# What is missing is never taken to be far


def test_an_output_area_with_no_verdict_adds_nothing_and_is_not_covered():
    found = homes_within({"n2": True, "s1": False}, HOMES, times=100)
    # n1 has no verdict. The figure is of the 300 homes of n2, which are 75 in 100 of the area.
    assert found[NORTH] == Worked(100.0, 1, 2, 0.75, State.PARTIAL)
    assert found[SOUTH] == Worked(0.0, 1, 2, 0.5, State.PARTIAL)


def test_below_half_the_homes_the_figure_is_not_given():
    found = homes_within({"n1": True}, HOMES, times=100)
    assert found[NORTH] == Worked(None, 1, 2, 0.25, State.BELOW_THRESHOLD)


def test_an_area_with_no_verdict_at_all_is_a_gap_and_never_a_nought():
    found = homes_within({"n1": True, "n2": True}, HOMES, times=100)
    assert found[SOUTH] == Worked(None, 0, 2, 0.0, State.SOURCE_GAP)


def test_an_output_area_with_no_homes_weighs_nothing():
    homes = Homes(area_of={"a": NORTH, "b": NORTH}, homes={"a": 0, "b": 50})
    assert homes_within({"a": True, "b": False}, homes, times=100)[NORTH].value == 0.0


def test_an_area_with_no_homes_at_all_is_shared_out_by_its_output_areas():
    homes = Homes(area_of={"a": NORTH, "b": NORTH}, homes={"a": 0, "b": 0})
    found = homes_within({"a": True, "b": False}, homes, times=100)[NORTH]
    assert found == Worked(50.0, 2, 2, 1.0, State.PRESENT)


def test_a_verdict_for_an_output_area_that_is_not_of_the_build_is_refused():
    with pytest.raises(ValueError, match="every verdict"):
        homes_within({"elsewhere": True}, HOMES)


# What holds of every method


def test_every_area_has_a_figure_or_a_reason_and_no_figure_is_not_a_number():
    for near in ({}, {"n1": True}, NEAR):
        found = homes_within(near, HOMES, times=100)
        assert set(found) == {NORTH, SOUTH}
        for worked in found.values():
            assert (worked.value is None) == (worked.state not in (State.PRESENT, State.PARTIAL))
            assert worked.value is None or math.isfinite(worked.value)


def test_a_share_is_never_under_nought_or_over_a_hundred():
    for near in (dict.fromkeys(NEAR, True), dict.fromkeys(NEAR, False), NEAR):
        for worked in homes_within(near, HOMES, times=100).values():
            assert worked.value is not None and 0 <= worked.value <= 100


def test_the_order_the_verdicts_are_given_in_does_not_change_the_answer():
    turned = dict(reversed(list(NEAR.items())))
    homes = Homes(
        area_of=dict(reversed(list(HOMES.area_of.items()))),
        homes=dict(reversed(list(HOMES.homes.items()))),
    )
    assert homes_within(NEAR, HOMES, times=100) == homes_within(turned, homes, times=100)


# The record of the method


def test_the_record_states_the_distance_and_the_line_under_which_no_figure_is_given():
    method = homes_within_at(100)
    assert method.parameters == {"metres": 100, "enough_in_100": 50}
    assert "within 100 metres" in method.sentence
    assert "under 50 in 100" in method.sentence
    assert "in a straight line" in method.sentence
    assert method.sentence.endswith(".") and not re.search(r"[.!?]\s|\n", method.sentence)


def test_the_method_is_named_as_the_design_names_it_with_its_distance():
    assert homes_within_at(100).derivation_id == "homes_within_100m@1"
    assert homes_within_at(100).kind is Kind.MEASURED


def test_two_distances_are_two_records_and_one_distance_is_one():
    """The evidence of a release holds one record under one id."""
    assert homes_within_at(100) == homes_within_at(100)
    assert homes_within_at(100).derivation_id != homes_within_at(300).derivation_id
    taken = {method.derivation_id for method in METHODS}
    assert homes_within_at(100).derivation_id not in taken


@pytest.mark.parametrize("metres", [0, -100])
def test_a_distance_of_nothing_is_refused(metres: int):
    with pytest.raises(ValueError, match="a distance"):
        homes_within_at(metres)


def test_the_method_is_in_a_module_that_is_there_for_a_person_to_read():
    module = homes_within_at(100).code.removeprefix("burro_pipeline.").replace(".", "/")
    assert (Path(burro_pipeline.__file__).parent / f"{module}.py").is_file()


# The evidence


@pytest.mark.parametrize(
    "near",
    [NEAR, {"n2": True}, {"n1": True}, {}],
    ids=["present", "partial", "below_threshold", "source_gap"],
)
def test_the_row_behind_a_figure_is_one_the_evidence_takes(near: dict[str, bool]):
    method = homes_within_at(100)
    worked = homes_within(near, HOMES, times=100)[NORTH]
    row = row_of(f"{NORTH}/feature/road_major_exposure", worked, method, FILES)
    assert row.has_a_value == (worked.value is not None)
    assert (row.value, row.derivation_id) == (worked.value, "homes_within_100m@1")
    Evidence.of("lon-2026-09-24-01", FILES, [method], [row])
