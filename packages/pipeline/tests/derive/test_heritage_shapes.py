"""The geometry of a file that writes where things are in longitude and latitude.

Every shape here is made up, and stands in the North Sea with the made-up town
of the tests of cells. A place is turned to longitude and latitude and back
again, so a test that holds a distance holds it to a few centimetres.
"""

import math

import pytest
from burro_pipeline.cells import shapes
from burro_pipeline.cells.shapes import hectares, outline_of
from burro_pipeline.derive import heritage_shapes
from burro_pipeline.derive.heritage_shapes import (
    MULTIPOLYGON,
    POLYGON,
    Ground,
    box_in_degrees,
    box_round,
    hectares_in_each,
    in_degrees,
    on_the_grid,
    outline_from,
    point_from,
    share_of_both,
    sharing_land,
    touch,
)

from ..cells.support import EAST, NORTH
from .heritage_support import at, outline, outlines, ring


def square(west: float, south: float, side: float = 100) -> shapes.Shape:
    x, y = EAST + west, NORTH + south
    return outline_of([[[(x, y), (x + side, y), (x + side, y + side), (x, y + side), (x, y)]]])


# The way back to the grid


@pytest.mark.parametrize(
    "place", [(530_000.0, 180_000.0), (503_000.5, 155_000.25), (700_000.0, 400_000.0)]
)
def test_a_place_turned_to_degrees_and_back_is_within_a_tenth_of_a_metre(
    place: tuple[float, float],
):
    """The sixth decimal place of a degree is about a tenth of a metre."""
    there = shapes.longitude_and_latitude(*place)
    (back,) = on_the_grid([list(there)])
    assert math.hypot(back[0] - place[0], back[1] - place[1]) < 0.1


def test_a_place_on_the_grid_is_kept_to_a_millimetre():
    (back,) = on_the_grid([[2.513016, 53.411393]])
    assert back == (round(back[0], 3), round(back[1], 3))


def test_a_height_after_the_two_coordinates_is_not_read():
    assert on_the_grid([[2.513016, 53.411393, 12.5]]) == on_the_grid([[2.513016, 53.411393]])


def test_no_points_are_no_points():
    assert on_the_grid([]) == []


@pytest.mark.parametrize(
    "written", [[[181.0, 51.0]], [[0.0, 91.0]], [[0.0]], [["east", "north"]], [[None, 1.0]]]
)
def test_a_point_that_is_no_longitude_and_latitude_is_refused(written: list[list[object]]):
    with pytest.raises(ValueError, match=r"longitude|latitude"):
        on_the_grid(written)  # pyright: ignore[reportArgumentType]


def test_the_coordinate_library_is_named_by_one_module_alone():
    """The way back to the grid is run by `cells/shapes.py`, which holds the operation."""
    assert not hasattr(heritage_shapes, "pyproj")
    assert not shapes.may_reach_a_network()


# The box that is looked in


def test_a_box_of_the_grid_in_degrees_holds_all_four_of_its_corners():
    box = (EAST, NORTH, EAST + 600.0, NORTH + 200.0)
    west, south, east, north = in_degrees(box, 1_000)
    for x in (EAST - 1_000, EAST + 1_600):
        for y in (NORTH - 1_000, NORTH + 1_200):
            longitude, latitude = shapes.longitude_and_latitude(x, y)
            assert west <= longitude <= east and south <= latitude <= north


def test_the_box_round_several_outlines_holds_each():
    found = box_round({"a": square(0, 0), "b": square(500, 100)})
    assert found == (EAST, NORTH, EAST + 600, NORTH + 200)


def test_there_is_no_box_round_no_outlines():
    with pytest.raises(ValueError, match="no outline"):
        box_round({})


def test_the_box_of_a_geometry_is_read_to_whatever_depth_it_is_written():
    a_point, a_ring = at(10, 20), ring(0, 0, 100, 100)
    assert box_in_degrees(a_point) == (a_point[0], a_point[1], a_point[0], a_point[1])
    one = box_in_degrees([a_ring])
    assert one == box_in_degrees(a_ring) == box_in_degrees([[a_ring], [a_ring]])
    assert one is not None and one[0] < one[2] and one[1] < one[3]


def test_a_geometry_with_no_point_has_no_box():
    nothing: list[object] = []
    assert box_in_degrees(nothing) is None
    assert box_in_degrees([nothing, [nothing]]) is None


@pytest.mark.parametrize("written", ["here", 5, [[1.0]], [["a", "b"]], [[True, False]], {"x": 1}])
def test_coordinates_that_are_not_lists_of_numbers_are_refused(written: object):
    with pytest.raises(ValueError, match=r"numbers|longitude"):
        box_in_degrees(written)


def test_two_boxes_touch_where_they_share_a_point():
    assert touch((0, 0, 1, 1), (1, 1, 2, 2))
    assert touch((0, 0, 3, 3), (1, 1, 2, 2))
    assert not touch((0, 0, 1, 1), (1.1, 0, 2, 1))
    assert not touch((0, 0, 1, 1), (0, 1.1, 1, 2))


# An outline from what a file writes


def test_an_outline_is_made_on_the_grid_from_the_rings_a_file_writes():
    written = outline(0, 0, 200, 100)
    made = outline_from(written["type"], written["coordinates"])
    assert made is not None
    shape, mended = made
    assert not mended
    assert hectares(shape) == pytest.approx(2.0, abs=0.01)


def test_an_outline_in_several_pieces_is_the_land_of_them_all():
    written = outlines((0, 0, 100, 100), (300, 0, 100, 50))
    made = outline_from(written["type"], written["coordinates"])
    assert made is not None
    assert hectares(made[0]) == pytest.approx(1.5, abs=0.01)
    assert shapes.pieces(made[0]) == 2


def test_a_hole_in_an_outline_is_no_part_of_its_land():
    made = outline_from(POLYGON, [ring(0, 0, 200, 100), ring(50, 25, 100, 50)])
    assert made is not None
    assert hectares(made[0]) == pytest.approx(1.5, abs=0.01)


def test_an_outline_whose_ring_crosses_itself_is_mended_and_said_to_be():
    """A ring drawn as a bow tie encloses two triangles, a quarter of the box each."""
    bow = [at(0, 0), at(100, 100), at(100, 0), at(0, 100), at(0, 0)]
    made = outline_from(POLYGON, [bow])
    assert made is not None
    shape, mended = made
    assert mended
    assert shapes.pieces(shape) == 2
    assert hectares(shape) == pytest.approx(0.5, abs=0.01)


def test_pieces_that_lie_over_one_another_are_mended_and_their_land_counted_once():
    written = outlines((0, 0, 100, 100), (50, 0, 100, 100))
    made = outline_from(written["type"], written["coordinates"])
    assert made is not None
    assert made[1]
    assert hectares(made[0]) == pytest.approx(1.5, abs=0.01)


def test_rings_that_enclose_no_land_make_no_outline():
    """A ring that runs out along a line and back along it encloses nothing."""
    there_and_back = [at(0, 0), at(100, 0), at(0, 0), at(100, 0), at(0, 0)]
    assert outline_from(POLYGON, [there_and_back]) is None


@pytest.mark.parametrize(
    ("kind", "written"),
    [
        (POLYGON, []),
        (POLYGON, [[[0.0, 51.0], [0.1, 51.0], [0.0, 51.0]]]),
        (POLYGON, "a ring"),
        (POLYGON, [[["a", "b"]] * 4]),
        (MULTIPOLYGON, []),
        (MULTIPOLYGON, "pieces"),
        ("LineString", [[0.0, 51.0], [0.1, 51.0]]),
        ("Point", [0.0, 51.0]),
    ],
)
def test_what_is_not_rings_of_points_is_refused(kind: str, written: object):
    with pytest.raises(ValueError, match=r"ring|outline|piece|longitude"):
        outline_from(kind, written)


def test_a_point_is_put_on_the_grid():
    east, north = point_from(at(250, 50))
    assert math.hypot(east - (EAST + 250), north - (NORTH + 50)) < 0.1


@pytest.mark.parametrize("written", ["here", None, 5])
def test_a_point_that_is_no_list_is_refused(written: object):
    with pytest.raises(ValueError, match="longitude"):
        point_from(written)


# How much land two outlines share


def test_two_outlines_that_are_one_share_all_their_land():
    assert share_of_both(square(0, 0), square(0, 0)) == 1.0


def test_two_outlines_that_share_no_land_share_none():
    assert share_of_both(square(0, 0), square(100, 0)) == 0.0
    assert share_of_both(square(0, 0), square(500, 0)) == 0.0


def test_the_land_two_outlines_share_is_a_share_of_the_land_they_cover_together():
    # Half of each is shared: 0.5 hectares of 1.5.
    assert share_of_both(square(0, 0), square(50, 0)) == pytest.approx(1 / 3)


def test_a_small_outline_inside_a_large_one_shares_little_of_the_two_together():
    assert share_of_both(square(0, 0, 200), square(50, 50, 50)) == pytest.approx(1 / 16)


def test_every_two_outlines_that_share_a_point_are_given_once_and_in_order():
    held = [square(0, 0), square(500, 0), square(50, 0), square(100, 0)]
    assert sharing_land(held) == [(0, 2), (0, 3), (2, 3)]
    assert sharing_land([]) == []
    assert sharing_land([square(0, 0)]) == []


def test_the_land_of_an_outline_is_shared_out_between_the_outlines_it_lies_in():
    ground = {"east": square(100, 0), "far": square(500, 0), "west": square(0, 0)}
    found = hectares_in_each(square(40, 0), ground)
    assert list(found) == ["east", "west"]
    assert found == {"east": pytest.approx(0.4), "west": pytest.approx(0.6)}


def test_an_outline_that_only_touches_another_shares_no_land_with_it():
    assert hectares_in_each(square(100, 0), {"west": square(0, 0)}) == {}


# Which outline a point stands in


def test_a_point_is_given_to_the_outline_it_stands_in():
    ground = Ground({"b": square(100, 0), "a": square(0, 0)})
    found = ground.holding([(EAST + 50, NORTH + 50), (EAST + 150, NORTH + 50)])
    assert found == ["a", "b"]


def test_a_point_that_stands_in_no_outline_is_given_to_none():
    ground = Ground({"a": square(0, 0)})
    assert ground.holding([(EAST + 50, NORTH + 150), (EAST - 1, NORTH + 50)]) == [None, None]
    assert ground.holding([]) == []


def test_a_point_on_the_line_between_two_outlines_goes_to_the_one_that_sorts_first():
    points = [(EAST + 100.0, NORTH + 50.0)]
    assert Ground({"b": square(100, 0), "a": square(0, 0)}).holding(points) == ["a"]
    assert Ground({"b": square(0, 0), "a": square(100, 0)}).holding(points) == ["a"]
