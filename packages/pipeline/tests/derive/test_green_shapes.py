"""Outlines made from lists of points, and the land of one that lies inside others.

Every shape here is made up: squares of 100 metres in the North Sea, where the
made-up town of the tests of cells stands.
"""

import pytest
from burro_pipeline.cells.shapes import box_of, hectares, hectares_inside, outline_of

Ring = list[tuple[float, float]]


def square(west: float, south: float, side: float = 100.0) -> Ring:
    east, north = west + side, south + side
    return [(west, south), (east, south), (east, north), (west, north), (west, south)]


def test_an_outline_is_made_from_a_ring_and_the_holes_in_it():
    whole = outline_of([[square(700_000, 400_000)]])
    holed = outline_of([[square(700_000, 400_000), square(700_040, 400_040, 20)]])
    assert hectares(whole) == 1.0
    assert hectares(holed) == 0.96


def test_an_outline_in_two_pieces_is_the_land_of_both():
    found = outline_of([[square(700_000, 400_000)], [square(700_300, 400_000, 50)]])
    assert hectares(found) == 1.25
    assert box_of(found) == (700_000.0, 400_000.0, 700_350.0, 400_100.0)


@pytest.mark.parametrize(
    "pieces",
    [
        [],
        [[]],
        [[[(700_000.0, 400_000.0), (700_100.0, 400_000.0)]]],
        # A ring that crosses itself.
        [[[(0.0, 0.0), (100.0, 100.0), (100.0, 0.0), (0.0, 100.0), (0.0, 0.0)]]],
        # Two pieces, one over the other.
        [[square(700_000, 400_000)], [square(700_050, 400_050)]],
    ],
)
def test_rings_that_make_no_outline_are_refused(pieces: list[list[Ring]]):
    with pytest.raises(ValueError, match="rings that make no outline"):
        outline_of(pieces)


def test_the_land_inside_others_is_measured_where_they_lie_over_the_outline():
    outlines = {
        "a": outline_of([[square(700_000, 400_000)]]),
        "b": outline_of([[square(700_100, 400_000)]]),
        "c": outline_of([[square(700_200, 400_000)]]),
    }
    # One shape lies across the line between the first two. None touches the third.
    across = outline_of([[square(700_050, 400_000)]])
    assert hectares_inside(outlines, [across]) == {"a": 0.5, "b": 0.5, "c": 0.0}
    assert hectares_inside(outlines, []) == {"a": 0.0, "b": 0.0, "c": 0.0}


def test_land_inside_two_shapes_is_counted_once():
    outlines = {"a": outline_of([[square(700_000, 400_000)]])}
    one = outline_of([[square(700_000, 400_000, 60)]])
    other = outline_of([[square(700_040, 400_040, 60)]])
    # Each is 0.36 hectares, and they share a square of 20 metres.
    assert round(hectares_inside(outlines, [one, other])["a"], 6) == 0.68
    assert hectares_inside(outlines, [other, one]) == hectares_inside(outlines, [one, other])
