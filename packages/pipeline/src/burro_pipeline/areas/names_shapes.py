"""Where a name is: the geometry a reader of names needs, and nothing a border is drawn with.

`cells/shapes.py` reads the one layer of a file and joins outlines. A reader of
names needs three things more: a named layer of a file that holds several, the
outline that holds a point, and how far an outline is from a point. They are
here while three parts of the areas are built side by side, and belong in
`cells/shapes.py` once those parts are joined. Like that module, this one tells
the type checker not to ask what the geometry library returns.

Every coordinate is on the National Grid, in metres, so a distance is a
distance on the ground and nothing is projected.

A point on the line between two outlines lies on both. Which one it is given
to is fixed: the outline whose code sorts first. So a build repeats.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false

import sqlite3
import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import shapely

from burro_pipeline.cells.shapes import NATIONAL_GRID, Point, Shape
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.fetch.kinds import read_only

# The header of a geometry in a GeoPackage, as `cells/shapes.py` reads it.
MAGIC, HEADER = b"GP", 8
BOX = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


@dataclass(frozen=True)
class Feature:
    """One row of a layer: the fields that were asked for, and its geometry."""

    fields: Mapping[str, object]
    shape: Shape

    def text(self, name: str) -> str:
        """A field as text, exactly as the file holds it. Empty where the file holds nothing."""
        value = self.fields[name]
        return "" if value is None else str(value)


def _quoted(name: str) -> str:
    """A name from the file, written so that it can only ever be read as a name."""
    return '"' + name.replace('"', '""') + '"'


def geometry_of(blob: bytes) -> Shape:
    """The geometry a GeoPackage holds in one cell, which must be on the National Grid."""
    if len(blob) < HEADER or blob[:2] != MAGIC:
        raise ValueError("not a geometry of a GeoPackage")
    flags = blob[3]
    order = "<" if flags & 1 else ">"
    box = BOX.get((flags >> 1) & 7)
    if box is None or flags & 0b00110000:
        raise ValueError("a geometry of a kind that is not read")
    if struct.unpack(f"{order}i", blob[4:8])[0] != NATIONAL_GRID:
        raise ValueError("a geometry that is not on the National Grid")
    return shapely.from_wkb(bytes(blob[HEADER + box :]))


def read_layer(
    path: Path,
    file_id: str,
    layer: str,
    fields: Sequence[str],
    *,
    where: tuple[str, str] | None = None,
) -> list[Feature]:
    """The rows of one named layer of a GeoPackage, in the order of the file.

    `where` names a field and the one value of it that is wanted. A row holds
    the fields asked for and no other. It stops when the layer or a field is
    not there, and when a geometry is missing or is not a valid shape.
    """
    try:
        database = read_only(path)
        try:
            held = database.execute(
                "SELECT c.srs_id, g.column_name FROM gpkg_contents c "
                "JOIN gpkg_geometry_columns g ON g.table_name = c.table_name "
                "WHERE c.table_name = ? AND c.data_type = 'features'",
                (layer,),
            ).fetchone()
            if held is None or held[0] != NATIONAL_GRID:
                raise LockError("input_is_as_described", file_id, "a layer is missing")
            known = {
                row[0]
                for row in database.execute("SELECT name FROM pragma_table_info(?)", (layer,))
            }
            wanted = [*fields, *([where[0]] if where else [])]
            if not set(wanted) <= known:
                raise LockError("input_is_as_described", file_id, "a column is missing")
            # Every name in the statement was looked up in the file's own list of names.
            columns = ", ".join(_quoted(name) for name in (*fields, str(held[1])))
            statement = f"SELECT {columns} FROM {_quoted(layer)}"  # noqa: S608
            if where:
                statement += f" WHERE {_quoted(where[0])} = ?"
            rows = database.execute(statement, (where[1],) if where else ()).fetchall()
        finally:
            database.close()
        found = [
            Feature(dict(zip(fields, row[:-1], strict=True)), geometry_of(bytes(row[-1])))
            for row in rows
        ]
    except (sqlite3.Error, ValueError, TypeError, struct.error, shapely.errors.ShapelyError):
        raise LockError("input_is_as_described", file_id, "a layer could not be read") from None
    if not all(shapely.is_valid(each.shape) and not each.shape.is_empty for each in found):
        raise LockError("input_is_as_described", file_id, "an outline is not a shape")
    return found


def holds(shape: Shape, point: Point) -> bool:
    """Whether a point lies in an outline, or on its edge."""
    return bool(shapely.intersects(shape, shapely.Point(point)))


def metres_from(shape: Shape, point: Point) -> float:
    """How far a point is from an outline, in metres. Nothing where the outline holds it."""
    return float(shapely.distance(shape, shapely.Point(point)))


def metres_apart(a: Shape, b: Shape) -> float:
    """How far two outlines are from each other, in metres. Nothing where they touch."""
    return float(shapely.distance(a, b))


def in_box(shape: Shape, box: tuple[float, float, float, float]) -> bool:
    """Whether the whole of an outline lies in a box: west, south, east, north."""
    return bool(shapely.covers(shapely.box(*box), shape))


def at(shape: Shape) -> Point:
    """Where a point geometry is."""
    return float(shape.x), float(shape.y)


class Ground:
    """Outlines by their codes, asked which of them holds a point or lies near one."""

    def __init__(self, outlines: Mapping[str, Shape]) -> None:
        self.codes: tuple[str, ...] = tuple(sorted(outlines))
        self._shapes = [outlines[code] for code in self.codes]
        self._index = {code: index for index, code in enumerate(self.codes)}
        self._tree = shapely.STRtree(self._shapes)

    def __len__(self) -> int:
        return len(self.codes)

    @property
    def box(self) -> tuple[float, float, float, float]:
        """The box that holds every outline: west, south, east, north."""
        west, south, east, north = shapely.total_bounds(self._shapes).tolist()
        return float(west), float(south), float(east), float(north)

    def shape(self, code: str) -> Shape:
        return self._shapes[self._index[code]]

    def holding(self, point: Point) -> tuple[str, ...]:
        """Every outline the point lies in or on, in the order of their codes."""
        found = self._tree.query(shapely.Point(point), predicate="intersects")
        return tuple(sorted(self.codes[int(index)] for index in found.tolist()))

    def first_holding(self, point: Point) -> str | None:
        """The outline a point is given to: of those that hold it, the code that sorts first."""
        found = self.holding(point)
        return found[0] if found else None

    def within(self, point: Point, metres: float) -> tuple[tuple[float, str], ...]:
        """Every outline within so many metres of a point, the nearest first."""
        here = shapely.Point(point)
        found = self._tree.query(here, predicate="dwithin", distance=metres)
        return tuple(
            sorted(
                (float(shapely.distance(self._shapes[int(index)], here)), self.codes[int(index)])
                for index in found.tolist()
            )
        )

    def inside(self, box: tuple[float, float, float, float]) -> tuple[str, ...]:
        """Every outline that lies wholly in a box, in the order of their codes."""
        found = self._tree.query(shapely.box(*box), predicate="covers")
        return tuple(sorted(self.codes[int(index)] for index in found.tolist()))

    def near(self, shape: Shape, metres: float) -> tuple[tuple[float, str], ...]:
        """Every outline within so many metres of another outline, the nearest first."""
        found = self._tree.query(shape, predicate="dwithin", distance=metres)
        return tuple(
            sorted(
                (float(shapely.distance(self._shapes[int(index)], shape)), self.codes[int(index)])
                for index in found.tolist()
            )
        )

    def nearest(self, point: Point) -> str | None:
        """The outline nearest a point, and of two as near the code that sorts first."""
        if not self.codes:
            return None
        here = shapely.Point(point)
        index = int(self._tree.nearest(here))
        reach = float(shapely.distance(self._shapes[index], here))
        return self.within(point, reach + 0.001)[0][1]
