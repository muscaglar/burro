"""How much of an outline lies on each output area, and which areas stand side by side.

Every shape here is made up: squares of 100 metres, drawn by `context_support.py`.

    columns   0    1    2
    row 0   | a  | b  | c  |
"""

import pytest
from burro_pipeline.areas import draft_shapes
from burro_pipeline.areas.names_shapes import Ground

from .context_support import block, corner


def ground() -> Ground:
    return Ground({"a": block(0, 0), "b": block(0, 1), "c": block(0, 2)})


def test_an_outline_is_shared_out_among_the_output_areas_it_lies_on():
    over_two = block(0, 0.75, high=1, wide=1)
    assert draft_shapes.shares_on(over_two, ground()) == {"a": 0.25, "b": 0.75}


def test_an_output_area_an_outline_only_touches_holds_none_of_it():
    assert draft_shapes.shares_on(block(0, 1), ground()) == {"b": 1.0}


def test_the_part_of_an_outline_that_lies_on_no_output_area_is_in_no_share():
    """Over the water, or beyond London. The shares then add up to less than one."""
    half_beyond = block(0, 2.5)
    assert draft_shapes.shares_on(half_beyond, ground()) == {"c": 0.5}
    assert draft_shapes.shares_on(block(5, 5), ground()) == {}


def test_the_names_nearest_an_area_are_given_with_how_far_off_each_is():
    points = {"far": corner(0.5, 4.0), "near": corner(0.5, 1.5), "inside": corner(0.5, 0.5)}
    assert draft_shapes.nearest_to(block(0, 0), points, 2) == ((0.0, "inside"), (50.0, "near"))
    assert [name for _, name in draft_shapes.nearest_to(block(0, 0), points, 9)] == [
        "inside",
        "near",
        "far",
    ]


@pytest.mark.parametrize(("metres", "beside"), [(10.0, ()), (100.0, ("c",)), (0.0, ())])
def test_two_areas_that_share_no_side_stand_side_by_side_where_they_are_near(
    metres: float, beside: tuple[str, ...]
):
    """As two areas on the two banks of a river do."""
    outlines = {"a": block(0, 0), "c": block(0, 1.5), "z": block(9, 9)}
    found = draft_shapes.near_each_other(outlines, metres)
    assert found == {"a": beside, "c": tuple("a" for _ in beside), "z": ()}
