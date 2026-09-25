"""The geometry of a file that writes where things are in longitude and latitude.

`cells/shapes.py` reads outlines on the National Grid and turns them to
longitude and latitude. A file of the planning data platform is the other way
about: it gives longitude and latitude, and the land of an area is measured on
the grid. So this module holds what that needs: the way back to the grid, an
outline made from the rings a file writes, how much land two outlines share,
and which outline a point stands in. It is here while the measures are built
side by side, and belongs in `cells/shapes.py` once they are joined. Like that
module, this one tells the type checker not to ask what the libraries return.

The way back to the grid is the operation of `cells/shapes.py`, run the other
way, and that module runs it: it alone names the coordinate library. The
operation is fixed, reads no grid file and reaches no network. The coordinate
library gives it as good to 2 metres. That is small beside an area
of tens of hectares. It is not small beside a line between two areas: a point
within 2 metres of one may be counted on the wrong side of it.

A place on the grid is kept to a whole millimetre, so that the last digits of
a sum do not turn on the machine that made it.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false

from collections.abc import Mapping, Sequence

import shapely

from burro_pipeline.cells.shapes import (
    Point,
    Shape,
    box_of,
    hectares,
    longitude_and_latitude,
    national_grid,
)
from burro_pipeline.rounding import to_places

# A place on the grid is kept to this many decimal places of a metre.
DECIMALS = 3
# A ring is closed by its first point, so it holds at least four.
LEAST_POINTS = 4
POLYGON, MULTIPOLYGON, POINT = "Polygon", "MultiPolygon", "Point"
# A box, as its least easting and northing and then its greatest, or the same in degrees.
Box = tuple[float, float, float, float]


def on_the_grid(points: Sequence[Sequence[float]]) -> list[Point]:
    """Points given as longitude and latitude, on the National Grid, to a millimetre.

    A point may hold a height after its two coordinates, as the standard for
    GeoJSON allows. It is not read.
    """
    if not points:
        return []
    try:
        degrees_east = [float(point[0]) for point in points]
        degrees_north = [float(point[1]) for point in points]
    except (IndexError, TypeError, ValueError):
        raise ValueError("a point is a longitude and a latitude") from None
    if not all(-180 <= x <= 180 for x in degrees_east):
        raise ValueError("a longitude is between -180 and 180")
    if not all(-90 <= y <= 90 for y in degrees_north):
        raise ValueError("a latitude is between -90 and 90")
    return [
        (to_places(east, DECIMALS), to_places(north, DECIMALS))
        for east, north in national_grid(degrees_east, degrees_north)
    ]


def in_degrees(box: Box, margin: float) -> Box:
    """A box of the grid, grown by a margin in metres, as a box of longitude and latitude.

    The sides of a box of the grid are not lines of longitude and latitude. So
    the box that is given back is the one that holds all four corners of the
    grown box, and it is a little larger than the box it stands for.
    """
    west, south, east, north = box
    corners = [
        longitude_and_latitude(x, y)
        for x in (west - margin, east + margin)
        for y in (south - margin, north + margin)
    ]
    return (
        min(corner[0] for corner in corners),
        min(corner[1] for corner in corners),
        max(corner[0] for corner in corners),
        max(corner[1] for corner in corners),
    )


def box_in_degrees(coordinates: object) -> Box | None:
    """The box that holds every point of a geometry, as a file writes its coordinates.

    It reads a point, a ring, an outline or several, to whatever depth they
    are written. It gives nothing where no point is found, and raises
    `ValueError` where what is found is not a number.
    """
    east: list[float] = []
    north: list[float] = []
    still: list[object] = [coordinates]
    while still:
        held = still.pop()
        if not isinstance(held, list):
            raise ValueError("coordinates are lists of numbers")
        if not held:
            continue
        if isinstance(held[0], list):
            still.extend(held)
            continue
        if len(held) < 2 or not all(_is_a_number(value) for value in held[:2]):
            raise ValueError("a point is a longitude and a latitude")
        east.append(float(held[0]))
        north.append(float(held[1]))
    if not east:
        return None
    return min(east), min(north), max(east), max(north)


def _is_a_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def touch(a: Box, b: Box) -> bool:
    """Whether two boxes share any point."""
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def box_round(outlines: Mapping[str, Shape]) -> Box:
    """The box on the grid that holds every outline."""
    boxes = [box_of(outline) for outline in outlines.values()]
    if not boxes:
        raise ValueError("there is no outline to draw a box round")
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _rings(written: object) -> list[list[Point]]:
    """The rings of one piece, on the grid: the ring round it, then the ring round each hole."""
    if not isinstance(written, list) or not written:
        raise ValueError("a piece is a ring, and then a ring for each hole")
    rings: list[list[Point]] = []
    for ring in written:
        if not isinstance(ring, list) or len(ring) < LEAST_POINTS:
            raise ValueError("a ring holds four points or more")
        rings.append(on_the_grid(ring))
    return rings


def outline_from(kind: str, coordinates: object) -> tuple[Shape, bool] | None:
    """An outline on the grid, from the coordinates a file writes, and whether it was mended.

    `kind` is `Polygon` or `MultiPolygon`. A piece whose ring crosses itself
    encloses land all the same, and so do pieces that lie over one another. It
    is mended: each piece is drawn again as the land its rings enclose, by the
    geometry library's own rule, and the pieces are joined, so that land inside
    two of them is land once. It is then said to be mended. Nothing is given
    where the rings enclose no land, before or after. It raises `ValueError`
    where what is written is not rings of points.
    """
    if kind == POLYGON:
        pieces = [_rings(coordinates)]
    elif kind == MULTIPOLYGON:
        if not isinstance(coordinates, list) or not coordinates:
            raise ValueError("an outline in several pieces holds one or more")
        pieces = [_rings(piece) for piece in coordinates]
    else:
        raise ValueError("an outline is a polygon, or several")
    try:
        drawn = [shapely.Polygon(rings[0], rings[1:]) for rings in pieces]
        shape = drawn[0] if len(drawn) == 1 else shapely.MultiPolygon(drawn)
        mended = not bool(shapely.is_valid(shape))
        if mended:
            land = [_land_of(piece) for piece in drawn]
            shape = shapely.union_all([piece for piece in land if piece is not None])
    except (TypeError, ValueError, shapely.errors.ShapelyError):
        raise ValueError("rings that make no outline") from None
    if shape.is_empty or float(shape.area) <= 0:
        return None
    return shapely.normalize(shape), mended


def _land_of(piece: Shape) -> Shape | None:
    """The land one piece encloses. A piece that is a line or a point encloses none."""
    mended = piece if shapely.is_valid(piece) else shapely.make_valid(piece)
    if mended.geom_type in (POLYGON, MULTIPOLYGON):
        return None if mended.is_empty else mended
    if mended.geom_type != "GeometryCollection":
        return None
    parts = [part for part in mended.geoms if part.geom_type in (POLYGON, MULTIPOLYGON)]
    return shapely.union_all(parts) if parts else None


def point_from(coordinates: object) -> Point:
    """A point on the grid, from the longitude and latitude a file writes."""
    if not isinstance(coordinates, list):
        raise ValueError("a point is a longitude and a latitude")
    return on_the_grid([coordinates])[0]


def share_of_both(a: Shape, b: Shape) -> float:
    """The land two outlines share, as a share of the land the two cover together.

    It is 1 where the two are one outline, and 0 where they share no land.
    """
    together = float(shapely.union(a, b).area)
    return float(shapely.intersection(a, b).area) / together if together > 0 else 0.0


def sharing_land(shapes: Sequence[Shape]) -> list[tuple[int, int]]:
    """Every two outlines that share a point, by where each stands in the list.

    Each pair is given once, the earlier of the two first, in order.
    """
    held = list(shapes)
    if not held:
        return []
    tree = shapely.STRtree(held)
    found: list[tuple[int, int]] = []
    for first, shape in enumerate(held):
        for second in sorted(int(at) for at in tree.query(shape, predicate="intersects")):
            if second > first:
                found.append((first, second))
    return found


def land_shared(shape: Shape, ground: Shape) -> Shape | None:
    """The land an outline shares with another, as an outline. Nothing where they share none.

    Two outlines that only touch share a line or a point, which is no land.
    """
    if not shapely.intersects(shape, ground):
        return None
    shared = _land_of(shapely.intersection(shape, ground))
    return None if shared is None or float(shared.area) <= 0 else shapely.normalize(shared)


def hectares_in_each(shape: Shape, ground: Mapping[str, Shape]) -> dict[str, float]:
    """The land of one outline that lies inside each outline of the ground, in hectares.

    An outline of the ground that shares no land with it is left out.
    """
    found: dict[str, float] = {}
    for name in sorted(ground):
        if not shapely.intersects(shape, ground[name]):
            continue
        shared = hectares(shapely.intersection(shape, ground[name]))
        if shared > 0:
            found[name] = shared
    return found


class Ground:
    """Outlines that a point is looked for in. They are indexed once."""

    def __init__(self, outlines: Mapping[str, Shape]) -> None:
        self._codes = sorted(outlines)
        self._tree = shapely.STRtree([outlines[code] for code in self._codes])

    def holding(self, points: Sequence[Point]) -> list[str | None]:
        """For each point, the outline it stands in, or nothing where it stands in none.

        A point on the line between two outlines stands on both. It is given
        to the one whose code sorts first, so that a build repeats.
        """
        if not points:
            return []
        placed = shapely.points([list(point) for point in points])
        asked, held = self._tree.query(placed, predicate="intersects")
        found: list[str | None] = [None] * len(points)
        for which, at in zip(asked.tolist(), held.tolist(), strict=True):
            code = self._codes[int(at)]
            earlier = found[int(which)]
            if earlier is None or code < earlier:
                found[int(which)] = code
        return found
