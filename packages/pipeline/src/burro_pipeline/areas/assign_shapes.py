"""The geometry a draft of areas needs, and that `cells/shapes.py` does not yet hold.

`cells/shapes.py` reads the one layer of a file, joins outlines and says which
share a side. A draft needs a little more: the part of a named layer that lies
in a box, the tidal water between two publishers' lines, which links of the
roads cross it, the outline a point lies in, the node nearest a point, the ward
that holds most of an output area, and how many metres of side two output areas
share. They are here while the parts of the areas are built side by side, and
belong in `cells/shapes.py` once those parts are joined. Like that module, this
one tells the type checker not to ask what the geometry library returns.

Every coordinate is on the National Grid, in metres, so a length is a length on
the ground and nothing is projected.

Where two answers are as good as each other, the one whose code sorts first is
given. So a build repeats.

Nothing here reads a name. It is handed shapes, and gives back shapes and numbers.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false

import math
import sqlite3
import struct
from collections.abc import Mapping, Sequence
from pathlib import Path

import shapely

from burro_pipeline.cells.shapes import NATIONAL_GRID, Point, Shape, hectares, joined, sides
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.fetch.kinds import read_only

# The header of a geometry in a GeoPackage, as `cells/shapes.py` reads it.
MAGIC, HEADER = b"GP", 8
BOX = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}
# West, south, east, north.
Box = tuple[float, float, float, float]
# One row of a layer: the fields that were asked for, in their order, and its geometry.
Row = tuple[tuple[object, ...], Shape]


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
    box: Box | None = None,
    where: tuple[str, str] | None = None,
) -> list[Row]:
    """The rows of one named layer of a GeoPackage, in the order of the layer's own numbers.

    `box` asks for the rows whose own box meets it, by the index the layer
    carries. `where` names a field and the one value of it that is wanted. It
    stops when the layer, its index or a field is not there, and when a
    geometry cannot be read.
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
            known = [
                str(row[0])
                for row in database.execute(
                    "SELECT name FROM pragma_table_info(?) ORDER BY pk DESC, cid", (layer,)
                )
            ]
            wanted = [*fields, *([where[0]] if where else [])]
            if not set(wanted) <= set(known):
                raise LockError("input_is_as_described", file_id, "a column is missing")
            # Every name in the statement was looked up in the file's own list of names.
            number, shape = _quoted(known[0]), _quoted(str(held[1]))
            columns = ", ".join(f"l.{_quoted(name)}" for name in fields)
            statement = (
                f"SELECT l.{shape}{', ' if columns else ''}{columns} FROM {_quoted(layer)} l"  # noqa: S608
            )
            asked: list[object] = []
            said: list[str] = []
            if box is not None:
                index = f"rtree_{layer}_{held[1]}"
                if not database.execute(
                    "SELECT 1 FROM sqlite_master WHERE name = ?", (index,)
                ).fetchone():
                    raise LockError("input_is_as_described", file_id, "a layer has no index")
                statement += f" JOIN {_quoted(index)} r ON r.id = l.{number}"
                said.append("r.maxx >= ? AND r.minx <= ? AND r.maxy >= ? AND r.miny <= ?")
                asked += [box[0], box[2], box[1], box[3]]
            if where is not None:
                said.append(f"l.{_quoted(where[0])} = ?")
                asked.append(where[1])
            if said:
                statement += " WHERE " + " AND ".join(said)
            rows = database.execute(f"{statement} ORDER BY l.{number}", asked).fetchall()
        finally:
            database.close()
        return [(tuple(row[1:]), geometry_of(bytes(row[0]))) for row in rows]
    except (sqlite3.Error, ValueError, TypeError, struct.error, shapely.errors.ShapelyError):
        raise LockError("input_is_as_described", file_id, "a layer could not be read") from None


def are_shapes(shapes: Sequence[Shape]) -> bool:
    """Whether every one is a valid shape that is not empty."""
    return all(bool(shapely.is_valid(shape)) and not shape.is_empty for shape in shapes)


def at(shape: Shape) -> Point:
    """Where a point geometry is."""
    return float(shape.x), float(shape.y)


def box_of(shapes: Sequence[Shape], margin: float = 0.0) -> Box:
    """The box some shapes fit in, with a margin in metres on every side."""
    west, south, east, north = (float(each) for each in shapely.total_bounds(list(shapes)))
    return west - margin, south - margin, east + margin, north + margin


def west_of(shape: Shape) -> float:
    """The easting of the most westerly point of a shape."""
    return float(shape.bounds[0])


def metres_round(shape: Shape) -> float:
    """The length of an outline, holes and all, in metres."""
    return float(shape.length)


def largest_piece(shape: Shape) -> Shape | None:
    """The largest piece of a shape that is ground. Nothing where it holds no ground."""
    pieces = [
        piece
        for piece in (shape.geoms if hasattr(shape, "geoms") else [shape])
        if piece.geom_type == "Polygon" and not piece.is_empty
    ]
    if not pieces:
        return None
    return max(pieces, key=lambda piece: (float(piece.area), piece.wkb_hex))


def water_between(whole: Sequence[Shape], land: Sequence[Shape]) -> Shape | None:
    """The largest piece of what one publisher draws as the whole and another leaves out.

    Boundary-Line draws a borough to the middle of the tidal river. The
    statistics office stops an output area at the mean high water mark. What
    lies between them is tidal water. The slivers where the two publishers'
    lines differ by a metre are left out: only the largest piece is water.
    """
    if not whole or not land:
        return None
    return largest_piece(shapely.difference(joined(whole), joined(land)))


def crossing(lines: Sequence[Shape], water: Shape) -> list[int]:
    """Which lines lie over the water for any of their length, by their place in the list."""
    if not lines:
        return []
    tree = shapely.STRtree(list(lines))
    met = sorted(int(index) for index in tree.query(water, predicate="intersects").tolist())
    return [index for index in met if float(shapely.intersection(lines[index], water).length) > 0.0]


class Outlines:
    """Outlines by their codes, asked which of them holds a point."""

    def __init__(self, outlines: Mapping[str, Shape]) -> None:
        self.codes: tuple[str, ...] = tuple(sorted(outlines))
        self._shapes = [outlines[code] for code in self.codes]
        self._tree = shapely.STRtree(self._shapes)

    def holding(self, points: Sequence[Point]) -> list[str | None]:
        """The outline each point lies in or on. Of several, the code that sorts first.

        A point on the line between two outlines lies on both, so the choice
        is fixed. A point in no outline is given none.
        """
        found: list[str | None] = [None] * len(points)
        if not points or not self.codes:
            return found
        asked, held = self._tree.query(shapely.points(list(points)), predicate="intersects")
        for point, outline in zip(asked.tolist(), held.tolist(), strict=True):
            code = self.codes[int(outline)]
            before = found[int(point)]
            if before is None or code < before:
                found[int(point)] = code
        return found


class Points:
    """Points by their ids, asked which of them is nearest to another point."""

    def __init__(self, points: Mapping[str, Point]) -> None:
        self.ids: tuple[str, ...] = tuple(sorted(points))
        self._tree = shapely.STRtree(shapely.points([points[name] for name in self.ids]))

    def __len__(self) -> int:
        return len(self.ids)

    def nearest(self, points: Sequence[Point]) -> list[tuple[str, float]]:
        """The point nearest each of some points, and how far it is in metres.

        Of two as near as each other, the one whose id sorts first.
        """
        if not points:
            return []
        if not self.ids:
            raise ValueError("there is no point to be near")
        asked, held = self._tree.query_nearest(shapely.points(list(points)), all_matches=True)
        first: dict[int, int] = {}
        for point, other in zip(asked.tolist(), held.tolist(), strict=True):
            first[int(point)] = min(first.get(int(point), int(other)), int(other))
        return [
            (self.ids[first[number]], math.dist(point, at(self._tree.geometries[first[number]])))
            for number, point in enumerate(points)
        ]


def shared_metres(outlines: Mapping[str, Shape]) -> dict[str, dict[str, float]]:
    """For each outline, the outlines it shares a side with, and how many metres they share.

    Outlines cut from one map share their sides exactly, which is what is
    looked for, as `sharing_a_side` of `cells/shapes.py` does. Two outlines
    that meet at a point alone share nothing.
    """
    holders: dict[tuple[Point, Point], list[str]] = {}
    for name in sorted(outlines):
        for side in sides(outlines[name]):
            if side[0] != side[1]:
                holders.setdefault(side, []).append(name)
    lengths: dict[tuple[str, str], list[float]] = {}
    for side in sorted(holders):
        names = sorted(set(holders[side]))
        for number, one in enumerate(names):
            for other in names[number + 1 :]:
                lengths.setdefault((one, other), []).append(math.dist(*side))
    found: dict[str, dict[str, float]] = {name: {} for name in sorted(outlines)}
    for (one, other), parts in sorted(lengths.items()):
        found[one][other] = found[other][one] = math.fsum(sorted(parts))
    return found


def held_most_by(
    outlines: Mapping[str, Shape], others: Mapping[str, Shape]
) -> dict[str, tuple[str, float]]:
    """For each outline, the other that holds most of its ground, and the share it holds.

    Of two that hold as much, the one whose code sorts first. An outline that
    no other holds any of is left out.
    """
    codes = sorted(others)
    shapes = [others[code] for code in codes]
    if not shapes:
        return {}
    tree = shapely.STRtree(shapes)
    found: dict[str, tuple[str, float]] = {}
    for name in sorted(outlines):
        shape = outlines[name]
        ground = float(shape.area)
        if ground <= 0:
            continue
        met = sorted(int(index) for index in tree.query(shape, predicate="intersects").tolist())
        shares = sorted(
            (-float(shapely.intersection(shape, shapes[index]).area) / ground, codes[index])
            for index in met
        )
        if shares and shares[0][0] < 0:
            found[name] = (shares[0][1], min(1.0, -shares[0][0]))
    return found


def ground_of(shape: Shape) -> float:
    """What an outline encloses, in hectares."""
    return hectares(shape)
