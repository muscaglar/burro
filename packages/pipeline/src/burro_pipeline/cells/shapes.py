"""Outlines: read from a GeoPackage, joined, measured, and turned to longitude and latitude.

This is the one module that names the geometry library and the coordinate
library, so that the rest of the pipeline handles plain numbers. The library
of geometry carries no types, so the type checker is told here, and only here,
not to ask what it returns.

A GeoPackage is an SQLite file. It is opened to read and nothing more, as one
that cannot change, so nothing is written beside it. A layer's outlines are
held as the standard's own bytes: a short header, then the geometry as
well-known binary.

Coordinates are turned from the National Grid to longitude and latitude by one
fixed operation, written out below. It reads no grid file and reaches no
network. The operation is the seven-parameter shift the coordinate library
lists as "OSGB36 to WGS 84 (6)", which its own table gives as good to 2
metres. An area's outline needs no better.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false

import math
import sqlite3
import struct
from collections.abc import Collection, Iterator, Mapping, Sequence
from functools import cache
from itertools import pairwise
from typing import Any

import pyproj
import shapely

from burro_pipeline.evidence.lock import LockError
from burro_pipeline.fetch.kinds import read_only
from burro_pipeline.inputs import Opened

# An outline, as the geometry library holds it. Nothing outside this module looks inside one.
Shape = Any
Point = tuple[float, float]
# A ring as GeoJSON writes it: each point a list of longitude and latitude.
Ring = list[list[float]]

# The code the boundaries are in: the National Grid, in metres.
NATIONAL_GRID = 27700
SQUARE_METRES_IN_A_HECTARE = 10_000
# How many decimal places a longitude or a latitude is written to. The sixth is about 0.1 m.
DECIMALS = 6
# From the National Grid to longitude and latitude on WGS84. Fixed here, so that a new
# version of the library cannot choose another.
TO_LONGITUDE_AND_LATITUDE = (
    "+proj=pipeline "
    "+step +inv +proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 "
    "+x_0=400000 +y_0=-100000 +ellps=airy "
    "+step +proj=push +v_3 "
    "+step +proj=cart +ellps=airy "
    "+step +proj=helmert +x=446.448 +y=-125.157 +z=542.06 "
    "+rx=0.15 +ry=0.247 +rz=0.842 +s=-20.489 +convention=position_vector "
    "+step +inv +proj=cart +ellps=WGS84 "
    "+step +proj=pop +v_3 "
    "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
)
# The header of an outline in a GeoPackage: two letters, a version, flags, and the code of
# its coordinates. After it may stand the box the outline fits in, of one of these sizes.
MAGIC, HEADER = b"GP", 8
BOX = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


@cache
def _turner() -> pyproj.Transformer:
    pyproj.network.set_network_enabled(False)
    return pyproj.Transformer.from_pipeline(TO_LONGITUDE_AND_LATITUDE)


def may_reach_a_network() -> bool:
    """Whether the coordinate library would fetch a grid file if an operation asked for one."""
    _turner()
    return bool(pyproj.network.is_network_enabled())


def longitude_and_latitude(easting: float, northing: float) -> Point:
    """A point of the National Grid as longitude and latitude, each to six decimal places."""
    longitude, latitude = _turner().transform(easting, northing)
    return round(longitude, DECIMALS), round(latitude, DECIMALS)


def national_grid(longitudes: Sequence[float], latitudes: Sequence[float]) -> list[Point]:
    """Points given as longitude and latitude, on the National Grid, in metres.

    It is the same fixed operation, run the other way, so it is good to the
    same 2 metres. Nothing is rounded here.
    """
    east, north = _turner().transform(list(longitudes), list(latitudes), direction="INVERSE")
    return [(float(x), float(y)) for x, y in zip(east, north, strict=True)]


def on_the_grid(points: Sequence[Point]) -> list[Point]:
    """Points given as longitude and latitude, on the National Grid.

    It is the one fixed operation, run the other way. A publisher that gives
    a point as longitude and latitude is placed on the grid the outlines are
    in, and nothing else is projected.
    """
    if not points:
        return []
    return national_grid([point[0] for point in points], [point[1] for point in points])


def holding(outlines: Mapping[str, Shape], points: Sequence[Point]) -> list[str | None]:
    """For each point of the National Grid, the name of the outline it lies in, or none.

    A point on a line that two outlines share lies in both, and is given to
    the one whose name sorts first, so that a point is counted once and the
    same way each time. A point that lies in no outline is given to none:
    nothing is given to the nearest.
    """
    names = sorted(outlines)
    found: list[str | None] = [None] * len(points)
    if not points or not names:
        return found
    tree = shapely.STRtree([outlines[name] for name in names])
    at, inside = tree.query(
        shapely.points([list(point) for point in points]), predicate="intersects"
    )
    for point, outline in sorted(zip(at.tolist(), inside.tolist(), strict=True)):
        if found[point] is None:
            found[point] = names[outline]
    return found


def _quoted(name: str) -> str:
    """A name from the file, written so that it can only ever be read as a name."""
    return '"' + name.replace('"', '""') + '"'


def _shape(blob: bytes) -> Shape:
    """The outline a GeoPackage holds in one cell."""
    if len(blob) < HEADER or blob[:2] != MAGIC:
        raise ValueError("not an outline of a GeoPackage")
    flags = blob[3]
    order = "<" if flags & 1 else ">"
    box = BOX.get((flags >> 1) & 7)
    if box is None or flags & 0b00110000:
        # An outline that is empty, or of a kind the standard leaves to an extension.
        raise ValueError("an outline of a kind that is not read")
    if struct.unpack(f"{order}i", blob[4:8])[0] != NATIONAL_GRID:
        raise ValueError("an outline that is not in the National Grid")
    return shapely.from_wkb(bytes(blob[HEADER + box :]))


def read_outlines(opened: Opened, code_field: str, wanted: Collection[str]) -> dict[str, Shape]:
    """The outline of each unit that is wanted, by its code, from the one layer of a file.

    It stops if the file holds more than one layer, if its layer is not in the
    National Grid, or if an outline is not a valid shape. A unit the file does
    not hold is left out: it is for the caller to say what that means.
    """
    found: dict[str, Shape] = {}
    try:
        database = read_only(opened.path)
        try:
            layers = database.execute(
                "SELECT table_name, srs_id FROM gpkg_contents WHERE data_type = 'features'"
            ).fetchall()
            if len(layers) != 1 or layers[0][1] != NATIONAL_GRID:
                raise LockError(
                    "input_is_as_described", opened.file_id, "it is not one layer in the grid"
                )
            table = str(layers[0][0])
            column = database.execute(
                "SELECT column_name FROM gpkg_geometry_columns WHERE table_name = ?", (table,)
            ).fetchone()
            fields = {
                row[0]
                for row in database.execute("SELECT name FROM pragma_table_info(?)", (table,))
            }
            if column is None or code_field not in fields:
                raise LockError("input_is_as_described", opened.file_id, "a column is missing")
            rows = database.execute(
                f"SELECT {_quoted(code_field)}, {_quoted(str(column[0]))} FROM {_quoted(table)}"  # noqa: S608
            )
            for code, blob in rows:
                if code in wanted:
                    if code in found or blob is None:
                        raise ValueError("a unit with no outline, or with two")
                    found[code] = _shape(bytes(blob))
        finally:
            database.close()
    except (sqlite3.Error, ValueError, struct.error, shapely.errors.ShapelyError, OSError):
        raise LockError(
            "input_is_as_described", opened.file_id, "an outline could not be read"
        ) from None
    if not all(shapely.is_valid(shape) and not shape.is_empty for shape in found.values()):
        raise LockError("input_is_as_described", opened.file_id, "an outline is not a shape")
    return found


def joined(shapes: Sequence[Shape]) -> Shape:
    """Several outlines as one, with every line between them taken out."""
    return shapely.union_all(list(shapes))


def hectares(shape: Shape) -> float:
    """What an outline encloses, in hectares. The grid is in metres, so nothing is projected."""
    return float(shape.area) / SQUARE_METRES_IN_A_HECTARE


def outline_of(pieces: Sequence[Sequence[Sequence[Point]]]) -> Shape:
    """An outline from its pieces: each a ring round the piece, then a ring round each hole.

    It is for a file that writes an outline as lists of points, on the
    National Grid. It raises `ValueError` where the rings make no shape: a
    ring of too few points, a ring that crosses itself, a piece that lies
    over another.
    """
    try:
        drawn = [shapely.Polygon(rings[0], list(rings[1:])) for rings in pieces]
        shape = drawn[0] if len(drawn) == 1 else shapely.MultiPolygon(drawn)
    except (IndexError, TypeError, ValueError, shapely.errors.ShapelyError):
        raise ValueError("rings that make no outline") from None
    if shape.is_empty or not shapely.is_valid(shape):
        raise ValueError("rings that make no outline")
    return shape


def box_of(shape: Shape) -> tuple[float, float, float, float]:
    """The box an outline fits in: its least easting and northing, then its greatest."""
    west, south, east, north = shape.bounds
    return float(west), float(south), float(east), float(north)


def hectares_inside(outlines: Mapping[str, Shape], others: Sequence[Shape]) -> dict[str, float]:
    """For each outline, the hectares of it that lie inside any of the other shapes.

    The others may lie over one another. They are joined before anything is
    measured, so land that is inside two of them is counted once. An outline
    that none of them touches holds nought.
    """
    held = list(others)
    tree = shapely.STRtree(held)
    found: dict[str, float] = {}
    for name in sorted(outlines):
        near = sorted(int(at) for at in tree.query(outlines[name], predicate="intersects"))
        shared = shapely.intersection(outlines[name], shapely.union_all([held[at] for at in near]))
        found[name] = hectares(shared) if near else 0.0
    return found


def vertices(shape: Shape) -> int:
    """How many points an outline is drawn with."""
    return int(shapely.get_num_coordinates(shape))


def pieces(shape: Shape) -> int:
    """How many separate pieces an outline is in."""
    return len(_polygons(shape))


def point_inside(shape: Shape) -> Point:
    """A point that is inside the largest piece of an outline, on the National Grid."""
    largest = max(_polygons(shape), key=lambda piece: (piece.area, piece.wkb_hex))
    inside = largest.representative_point()
    return float(inside.x), float(inside.y)


def _polygons(shape: Shape) -> list[Shape]:
    return list(shape.geoms) if shape.geom_type == "MultiPolygon" else [shape]


def _ring(ring: Shape) -> Ring:
    """A ring in longitude and latitude, run the other way round.

    The library's own fixed form runs an outer ring clockwise and a hole
    anticlockwise. The standard for GeoJSON asks for the opposite.
    """
    return [list(longitude_and_latitude(x, y)) for x, y in reversed(list(ring.coords))]


def as_geojson(shape: Shape) -> dict[str, object]:
    """An outline as a GeoJSON geometry, in longitude and latitude.

    It is a polygon where the outline is in one piece, and a multipolygon
    where it is in several. An outer ring runs anticlockwise and a hole
    clockwise, as the standard for GeoJSON asks. The outline is put in the
    library's fixed form first: its pieces in a fixed order and each ring
    begun at a fixed point, so that the same outline is always the same bytes.
    """
    if shape.geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError("an outline is a polygon, or several")
    drawn = [
        [_ring(piece.exterior), *(_ring(hole) for hole in piece.interiors)]
        for piece in _polygons(shapely.normalize(shape))
    ]
    if len(drawn) == 1:
        return {"type": "Polygon", "coordinates": drawn[0]}
    return {"type": "MultiPolygon", "coordinates": drawn}


def sides(shape: Shape) -> Iterator[tuple[Point, Point]]:
    """Every straight side of an outline, each as its two ends in a fixed order."""
    for piece in _polygons(shape):
        for ring in (piece.exterior, *piece.interiors):
            points = [(float(x), float(y)) for x, y in ring.coords]
            for a, b in pairwise(points):
                yield (a, b) if a <= b else (b, a)


def sharing_a_side(outlines: Mapping[str, Shape]) -> dict[str, tuple[str, ...]]:
    """For each outline, the others that share a side with it, in the order of their ids.

    Two outlines that meet at a point alone share no side. Outlines that were
    cut from one map share their sides exactly, which is what is looked for:
    no distance is measured and nothing is taken as near enough.
    """
    beside: dict[tuple[Point, Point], set[str]] = {}
    for name in sorted(outlines):
        for side in sides(outlines[name]):
            beside.setdefault(side, set()).add(name)
    found: dict[str, set[str]] = {name: set() for name in outlines}
    for names in beside.values():
        for name in names:
            found[name] |= names - {name}
    return {name: tuple(sorted(found[name])) for name in sorted(found)}


def fit_together(outlines: Sequence[Shape]) -> bool:
    """Whether outlines tile: none lies over another, and each shared side is shared exactly."""
    return bool(shapely.coverage_is_valid(list(outlines)))


def metres_between(a: Point, b: Point) -> float:
    """The distance between two points given as longitude and latitude, roughly.

    It is good to a few parts in a thousand at London's latitude. It is for
    checking one position against another, and for nothing else.
    """
    metres_a_degree = 111_320.0
    east = (a[0] - b[0]) * metres_a_degree * math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot(east, (a[1] - b[1]) * 110_574.0)
