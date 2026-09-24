"""What is within reach of where homes are: the distance, the weights and the edge of London.

Every file here is made up, and says so: `culture_support.py` draws the town.
The centres stand 1,000 metres apart, so that a home is within reach of what
stands by its own centre and of little else, and every count can be made by
hand. The town stands far east of the grid's middle, where 1,000 metres on the
grid are a little under 1,000 on the ground. So 790 on the grid is within 800,
and 810 is not.
"""

import ast
import math
from pathlib import Path

import burro_pipeline
import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.derive import culture_reach
from burro_pipeline.derive.culture_reach import (
    METRES,
    Ground,
    Reach,
    figures,
    first_of_each,
    for_each_at,
    ground_of,
    kept,
    metres_between,
    metres_to_a_degree,
    rates,
    reach_of,
    within,
    within_at,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.row import State
from burro_pipeline.inputs import Inputs

from .culture_support import (
    APART,
    OAS,
    ONE,
    Q1,
    Q2,
    Q3,
    Q4,
    R1,
    T1,
    THREE,
    TWO,
    Metres,
    beside,
    centres_at,
    inputs_of,
    on_the_grid,
)

OA_Q1, OA_Q2, OA_Q3, OA_Q4 = OAS[:4]
OA_R1, OA_T1 = OAS[4], OAS[8]


def at(where: Metres, slot: int = 0, adds: int = 1) -> tuple[float, float, int, int]:
    return (*longitude_and_latitude(*on_the_grid(where)), slot, adds)


def ground(folder: Path, centres: bytes | None = None) -> tuple[Inputs, spine.Spine, Ground]:
    inputs = inputs_of(folder, None, centres)
    found = spine.build(inputs)
    return inputs, found, ground_of(inputs, found)


# The places of the town, as points: three in the first slot by Q1, one in the second half
# way from Q2 to Q3, and one each 790 and 810 metres north of Q4.
PLACES = (
    at(beside(Q1, 100)),
    at(beside(Q1, 0, 100)),
    at(beside(Q1, -100)),
    at(beside(Q2, 500), slot=1),
    at(beside(Q4, 0, 790), slot=1),
    at(beside(Q4, 0, 810), slot=1),
    at(beside(R1, 0, 50)),
    at(beside(T1, 50), adds=2),
)


@pytest.fixture
def reach(tmp_path: Path) -> tuple[Reach, spine.Spine]:
    _, found, stood = ground(tmp_path)
    return reach_of(PLACES, 2, stood, found), found


# The distance


def test_a_degree_is_as_many_metres_as_the_earth_makes_it():
    """At the equator and at a pole, to the metre, as WGS84 gives them."""
    east, north = metres_to_a_degree(0.0)
    assert (round(east), round(north)) == (111_319, 110_574)
    east, north = metres_to_a_degree(90.0)
    assert (round(east), round(north)) == (0, 111_694)
    east, north = metres_to_a_degree(51.5)
    assert 69_000 < east < 70_000 and 111_200 < north < 111_300


def test_a_distance_on_the_ground_is_a_little_under_the_distance_on_the_grid():
    here, there = (longitude_and_latitude(*on_the_grid(where)) for where in (Q1, Q2))
    assert 0.998 * APART < metres_between(here, there) < APART
    north = longitude_and_latitude(*on_the_grid(beside(Q1, 0, 800)))
    assert 0.998 * 800 < metres_between(here, north) < 800
    assert metres_between(here, here) == 0.0


def test_a_place_at_exactly_the_distance_is_within_it():
    here = (0.0, 51.5)
    east, north = metres_to_a_degree(51.5)
    on_the_line = (800 / east, 51.5, 0, 1)
    beyond = (0.0, 51.5 + 800.001 / north, 0, 1)
    assert within(kept([on_the_line, beyond]), here, 800, 1) == [1]
    assert within(kept([on_the_line, beyond]), here, 801, 1) == [2]


def test_what_is_found_is_what_a_search_of_every_point_finds():
    """Points are kept by squares so that what is near is found by looking near."""
    here = (-0.1, 51.5)
    points = [
        (-0.1 + (n % 41 - 20) / 1500, 51.5 + (n // 41 - 20) / 2500, n % 3, 1 + n % 2)
        for n in range(41 * 41)
    ]
    for metres in (1, 250, 800, 1_500):
        by_hand = [0, 0, 0]
        for longitude, latitude, slot, adds in points:
            if metres_between(here, (longitude, latitude)) <= metres:
                by_hand[slot] += adds
        assert within(kept(points), here, metres, 3) == by_hand


# Several records of one thing


def points_at(*metres_east: float) -> list[tuple[float, float]]:
    return [longitude_and_latitude(*on_the_grid(beside(Q1, east))) for east in metres_east]


def test_a_point_beside_one_that_came_before_it_is_that_point_again():
    assert first_of_each(points_at(0, 10, 24, 26, 500, 510), 25) == [0, 0, 0, 3, 4, 4]


def test_a_row_of_points_each_beside_the_next_is_not_one_thing_from_end_to_end():
    """Ten galleries in a row, 20 metres apart: each is held to the first of its group."""
    assert first_of_each(points_at(*range(0, 200, 20)), 25) == [0, 0, 2, 2, 4, 4, 6, 6, 8, 8]


def test_points_on_one_spot_are_one_thing_and_points_far_apart_are_not():
    assert first_of_each(points_at(0, 0, 0), 25) == [0, 0, 0]
    assert first_of_each(points_at(0, 100, 200), 25) == [0, 1, 2]
    assert first_of_each([], 25) == []
    assert first_of_each(points_at(0, 10), 0) == [0, 1]


def test_what_is_beside_what_is_the_same_by_a_search_of_every_point():
    points = [(-0.1 + (n * 37 % 101) / 40_000, 51.5 + (n * 53 % 103) / 60_000) for n in range(300)]
    by_hand: list[int] = []
    for place, point in enumerate(points):
        firsts = [n for n in range(place) if by_hand[n] == n]
        near = [n for n in firsts if metres_between(points[n], point) <= 40]
        by_hand.append(min(near) if near else place)
    assert first_of_each(points, 40) == by_hand
    assert len(set(by_hand)) < len(points)


# What is within reach


def test_each_home_is_given_what_is_within_reach_of_its_own_centre(
    reach: tuple[Reach, spine.Spine],
):
    found, _ = reach
    assert found.metres == METRES == 800
    assert found.within[OA_Q1] == (3, 0)
    assert found.within[OA_Q2] == (0, 1) and found.within[OA_Q3] == (0, 1)
    assert found.within[OA_R1] == (1, 0)
    assert found.within[OA_T1] == (2, 0)


def test_790_metres_on_the_grid_is_within_reach_and_810_is_not(
    reach: tuple[Reach, spine.Spine],
):
    found, _ = reach
    assert found.within[OA_Q4] == (0, 1)


def test_a_home_with_nothing_within_reach_has_a_count_of_nought(
    reach: tuple[Reach, spine.Spine],
):
    found, _ = reach
    assert found.within[OAS[5]] == (0, 0)
    assert set(found.within) == set(OAS) and found.near_the_edge == ()


def test_the_homes_within_reach_of_a_home_are_its_own_and_those_beside_it(
    reach: tuple[Reach, spine.Spine],
):
    """A centre 1,000 metres off on the grid is out of reach, so each has its own alone."""
    found, town = reach
    assert found.homes == {oa: town.homes[oa] for oa in OAS}


def test_some_slots_are_added_up_and_how_many_hold_anything_is_counted(
    reach: tuple[Reach, spine.Spine],
):
    found, _ = reach
    assert found.of((0, 1))[OA_Q1] == 3.0 and found.of((1,))[OA_Q1] == 0.0
    assert found.how_many_of((0, 1))[OA_Q1] == 1.0
    assert found.how_many_of((0, 1))[OAS[5]] == 0.0


# The edge of London


def test_an_output_area_with_homes_outside_london_within_reach_has_no_count(tmp_path: Path):
    """The one output area outside London is brought 500 metres east of the fourth centre."""
    _, found, stood = ground(tmp_path, centres_at(outside=beside(Q4, 500)))
    reach = reach_of(PLACES, 2, stood, found)
    assert reach.near_the_edge == (OA_Q4,)
    assert OA_Q4 not in reach.within and OA_Q4 not in reach.homes
    assert reach.within[OA_Q1] == (3, 0)


def test_an_output_area_outside_london_that_is_out_of_reach_changes_nothing(tmp_path: Path):
    _, found, stood = ground(tmp_path, centres_at(outside=beside(Q4, 810)))
    assert len(stood.beyond) == 1
    assert reach_of(PLACES, 2, stood, found).near_the_edge == ()


def test_only_the_centres_near_london_are_kept_of_those_outside_it(tmp_path: Path):
    far = [(100_000.0, 0.0), (0.0, -50_000.0)]
    near = [(-1_500.0, 0.0), (3_000.0, 11_500.0)]
    _, _, stood = ground(tmp_path, centres_at(more=[*far, *near]))
    assert len(stood.beyond) == 2


def test_an_output_area_with_no_centre_has_no_count_and_is_not_near_the_edge(tmp_path: Path):
    _, found, stood = ground(tmp_path, centres_at(without=[OA_Q1]))
    reach = reach_of(PLACES, 2, stood, found)
    assert OA_Q1 not in reach.within and OA_Q1 not in reach.near_the_edge


def test_a_centre_that_is_no_point_stops_the_build(tmp_path: Path):
    broken = centres_at().replace(b"750000.0000,400000.0000", b"nowhere,400000.0000")
    assert broken != centres_at()
    inputs = inputs_of(tmp_path, None, broken)
    with pytest.raises(LockError) as stopped:
        ground_of(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_is_as_described"


# The figure of an area


def test_the_figure_of_an_area_is_the_mean_over_its_homes(reach: tuple[Reach, spine.Spine]):
    """Quillhaven 001 has 110, 120, 130 and 140 homes, with 3, 1, 1 and 1 within reach."""
    found, town = reach
    worked = figures(found.of((0, 1)), town)
    by_hand = (110 * 3 + 120 + 130 + 140) / 500
    assert worked[ONE].value == 1.4 == round(by_hand, 1)
    assert worked[ONE].state is State.PRESENT and worked[ONE].weight_covered == 1.0
    assert worked[TWO].value == 0.2 and worked[THREE].value == 0.5


def test_the_second_figure_is_one_sum_over_another_and_never_a_mean_of_rates(
    reach: tuple[Reach, spine.Spine],
):
    found, town = reach
    worked = rates(found.of((0, 1)), found, town)
    top = 110 * 3 + 120 + 130 + 140
    bottom = 110 * 110 + 120 * 120 + 130 * 130 + 140 * 140
    assert worked[ONE].value == round(1_000 * top / bottom, 1) == 11.4
    # The mean over homes of each home's own rate would be 12.0.
    mean_of_rates = (110 * (3_000 / 110) + 120 * (1_000 / 120) + 130 * (1_000 / 130) + 1_000) / 500
    assert round(mean_of_rates, 1) == 12.0 != worked[ONE].value


def test_a_figure_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    _, found, stood = ground(tmp_path)
    # 1 within reach of Q1's 110 homes, of the area's 500: 0.22. And 125 of 500: 0.25.
    one = figures(reach_of([at(Q1)], 1, stood, found).of((0,)), found)
    assert one[ONE].value == 0.2
    quarter = figures({OA_Q1: 1.25, OA_Q2: 0.0, OA_Q3: 0.0, OA_Q4: 0.0}, found)
    assert quarter[ONE].value == 0.3


def test_an_output_area_near_the_edge_lowers_the_coverage_and_is_never_nought(tmp_path: Path):
    _, found, stood = ground(tmp_path, centres_at(outside=beside(Q1, 500)))
    reach = reach_of(PLACES, 2, stood, found)
    worked = figures(reach.of((0, 1)), found)
    assert reach.near_the_edge == (OA_Q1, OA_Q2)
    assert worked[ONE].state is State.PARTIAL
    assert worked[ONE].weight_covered == pytest.approx(270 / 500)
    assert worked[ONE].value == round((130 + 140) / 270, 1)
    assert rates(reach.of((0, 1)), reach, found)[ONE].state is State.PARTIAL


def test_below_half_the_homes_covered_no_figure_is_given(tmp_path: Path):
    """Three of the four output areas of the first area are near the edge: 110 homes of 500."""
    near = [beside(Q2, 500), beside(Q4, 500)]
    _, found, stood = ground(tmp_path, centres_at(more=near))
    reach = reach_of(PLACES, 2, stood, found)
    assert reach.near_the_edge == (OA_Q2, OA_Q3, OA_Q4)
    for worked in (figures(reach.of((0, 1)), found), rates(reach.of((0, 1)), reach, found)):
        assert (worked[ONE].value, worked[ONE].state) == (None, State.BELOW_THRESHOLD)
        assert worked[ONE].weight_covered == pytest.approx(110 / 500)
        assert worked[TWO].value is not None


def test_an_area_wholly_near_the_edge_is_a_gap_and_is_never_nought(tmp_path: Path):
    near = [beside(Q1, 500), beside(Q3, 500)]
    _, found, stood = ground(tmp_path, centres_at(more=near))
    reach = reach_of(PLACES, 2, stood, found)
    assert reach.near_the_edge == (OA_Q1, OA_Q2, OA_Q3, OA_Q4)
    worked = figures(reach.of((0, 1)), found)
    assert (worked[ONE].value, worked[ONE].state) == (None, State.SOURCE_GAP)


def test_the_same_places_in_any_order_give_the_same_figures(tmp_path: Path):
    _, found, stood = ground(tmp_path)
    one = reach_of(PLACES, 2, stood, found)
    other = reach_of(tuple(reversed(PLACES)), 2, stood, found)
    assert one == other


# The records of the methods


def test_the_distance_is_part_of_the_id_of_a_method_and_stands_in_its_sentence():
    for metres in (400, 800):
        count, rate = within_at(metres), for_each_at(metres)
        assert count.derivation_id == f"places_within_{metres}m_at_homes@1"
        assert rate.derivation_id == f"places_per_1000_homes_within_{metres}m@1"
        for method in (count, rate):
            assert method.kind is Kind.MEASURED
            assert f"{metres} metres" in method.sentence and "straight line" in method.sentence
            assert method.parameters["metres"] == metres
            assert method.code == "burro_pipeline.derive.culture_reach"


def test_a_method_says_what_the_rule_at_the_edge_is_and_claims_no_more():
    said = within_at(800).sentence
    assert "outside London" in said and "land outside London" in said
    assert "covers" not in said and "!" not in said


# There is one of this


# Two measures that are of no venue say where London ends in a way of their own, under the
# same name. The nearest station reads the outlines of the land outside London, and a place
# given by its postcode reads the centres that stand in a box. Each was written apart from
# this module and is held by its own tests on the real files. They are named here so that a
# third is still refused. `docs/design/what-core-needs.md` says that the rule at the edge is
# to be made one.
SAYS_IT_ANOTHER_WAY = {
    "nearest_by_postcode.py: outside_london",
    "station_walk.py: outside_london",
}


def test_no_other_module_measures_a_distance_on_the_ground_or_says_where_london_ends():
    """Two measures of venues are comparable only if both are made the same way.

    So what is within reach is worked out in one module, and a second copy of
    any part of it is refused here: a measure imports it. Two modules that
    measure no venue are known to say where London ends another way.
    """
    derive = Path(burro_pipeline.__file__).parent / "derive"
    own = {
        node.name
        for node in ast.parse(Path(culture_reach.__file__).read_text(encoding="utf-8")).body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    assert {"metres_to_a_degree", "metres_between", "outside_london", "within", "kept"} <= own
    guarded = {"metres_to_a_degree", "metres_between", "outside_london", "reach_of"}
    again = {
        f"{path.name}: {node.name}"
        for path in sorted(derive.glob("*.py"))
        if path.name != "culture_reach.py"
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef) and node.name.lstrip("_") in guarded
    }
    assert again == SAYS_IT_ANOTHER_WAY
    assert math.isclose(metres_to_a_degree(51.5)[1], 111_248.7, rel_tol=1e-4)
