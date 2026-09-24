"""A picture of a draft: drawn from outlines alone, the same bytes each time, and no basemap.

Every shape here is made up: squares in open sea.
"""

import re
from xml.etree import ElementTree

import pytest
from burro_pipeline.areas import draft_picture
from burro_pipeline.areas.draft_picture import (
    AREA,
    CENTRES,
    COLOURS,
    DOTS,
    LINE,
    ROADS,
    WATER_FILL,
    Label,
    Picture,
    Shape,
    box_of,
    svg,
)

SVG = "{http://www.w3.org/2000/svg}"


Ring = list[list[float]]


def ring(west: float, south: float, side: float = 0.01) -> Ring:
    return [
        [west, south],
        [west + side, south],
        [west + side, south + side],
        [west, south + side],
        [west, south],
    ]


def square(west: float, south: float, side: float = 0.01) -> dict[str, object]:
    return {"type": "Polygon", "coordinates": [ring(west, south, side)]}


def read(drawn: str | bytes) -> ElementTree.Element:
    """A picture as a document. It was drawn by the code under test, from made-up shapes."""
    return ElementTree.fromstring(drawn)  # noqa: S314


def two_areas() -> Picture:
    return Picture(
        "Two made-up areas",
        [
            Shape(AREA, square(2.50, 53.40), 0, "syn-n0001"),
            Shape(AREA, square(2.51, 53.40), 1, "syn-n0002"),
            Shape(WATER_FILL, square(2.50, 53.39)),
            Shape(ROADS, {"type": "LineString", "coordinates": [[2.50, 53.405], [2.52, 53.405]]}),
            Shape(CENTRES, square(2.505, 53.402, 0.002)),
            Shape(LINE, square(2.50, 53.40, 0.02)),
            Shape(DOTS, {"type": "Point", "coordinates": [2.505, 53.405]}),
        ],
        labels=[Label("1", (2.505, 53.405)), Label("A & <B>", (2.515, 53.405))],
    )


def test_a_picture_is_an_svg_that_draws_every_shape_it_is_handed():
    root = read(svg(two_areas()))
    assert root.tag == f"{SVG}svg"
    paths = root.findall(f"{SVG}path")
    assert len(paths) == 6
    assert [path.get("fill") for path in paths[:2]] == [COLOURS[0], COLOURS[1]]
    assert len(root.findall(f"{SVG}circle")) == 1
    assert [text.text for text in root.findall(f"{SVG}text")] == [
        "1",
        "A & <B>",
        "Two made-up areas",
    ]


def test_a_picture_asks_no_other_host_for_anything():
    """No basemap, no tile, no image, no font and no script: ADR 0004."""
    drawn = svg(two_areas())
    assert re.findall(r"https?://[^\"' ]+", drawn) == ["http://www.w3.org/2000/svg"]
    for word in ("<image", "href", "<script", "url(", "@import", "<foreignObject"):
        assert word not in drawn


def test_the_same_shapes_give_the_same_bytes():
    assert svg(two_areas()) == svg(two_areas())


def test_a_picture_is_flat_about_its_own_middle_so_a_square_on_the_ground_is_drawn_square():
    """A degree of longitude is drawn as wide as it is on the ground at that latitude."""
    high, wide = 0.01, 0.01 / 0.5962
    round_it = [[2.5, 53.4], [2.5 + wide, 53.4], [2.5 + wide, 53.4 + high], [2.5, 53.4 + high]]
    closed = {"type": "Polygon", "coordinates": [[*round_it, round_it[0]]]}
    [path] = read(svg(Picture("", [Shape(AREA, closed)]))).findall(f"{SVG}path")
    points = re.findall(r"(-?[\d.]+),(-?[\d.]+)", path.get("d") or "")
    xs, ys = {float(x) for x, _ in points}, {float(y) for _, y in points}
    assert (max(xs) - min(xs)) == pytest.approx(max(ys) - min(ys), rel=0.01)


def test_a_picture_is_fitted_to_what_it_is_told_to_and_draws_the_rest_beyond_it():
    far = Shape(AREA, square(3.0, 54.0), 2)
    near = two_areas().shapes[0]
    fitted = svg(Picture("", [near, far], fit_to=[near.geometry]))
    loose = svg(Picture("", [near, far]))
    assert fitted != loose
    assert box_of([near.geometry]) == (2.5, 53.4, 2.51, 53.41)


def test_an_area_in_several_pieces_and_one_with_a_hole_are_drawn_whole():
    island: dict[str, object] = {
        "type": "MultiPolygon",
        "coordinates": [[ring(2.5, 53.4)], [ring(2.6, 53.4)]],
    }
    hole: dict[str, object] = {
        "type": "Polygon",
        "coordinates": [ring(2.5, 53.4, 0.03), ring(2.51, 53.41)],
    }
    for geometry in (island, hole):
        root = read(svg(Picture("", [Shape(AREA, geometry)])))
        [path] = root.findall(f"{SVG}path")
        assert (path.get("d") or "").count("M") == 2
        assert (path.get("d") or "").count("Z") == 2


def test_a_feature_with_no_geometry_is_left_out():
    empty: dict[str, object] = {}
    held = {"features": [{"geometry": None}, {"geometry": empty}, {"geometry": square(2.5, 53.4)}]}
    assert len(draft_picture.features_of(held)) == 1
    with pytest.raises(ValueError, match="not a collection"):
        draft_picture.features_of({"features": "none"})


def test_a_shape_of_a_kind_that_is_not_drawn_stops_the_picture():
    with pytest.raises(ValueError, match="not drawn"):
        svg(Picture("", [Shape(AREA, {"type": "GeometryCollection", "coordinates": []})]))
    with pytest.raises(ValueError, match="nothing to draw"):
        svg(Picture("", []))
