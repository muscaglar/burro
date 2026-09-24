"""The wards and the boroughs of London, as Ordnance Survey's Boundary-Line writes them.

The file is a zip that holds one GeoPackage of many layers. Two are read: the
wards and the boroughs. London's are told by the file's own code for the kind
of area, and never by where an outline lies.

A ward's name is kept as written, with the word for its kind after it. No
column says which borough a ward is in, so whoever calls this finds it from a
point inside the ward.

A ward is no candidate for an area. Its name is read for two things: a ward
that carries the name of a place adds to what is known of that name, and a name
that is also a ward is put to a person.
"""

from dataclasses import dataclass

from burro_pipeline.areas import names_shapes
from burro_pipeline.areas.names_files import File, taken_out
from burro_pipeline.cells import shapes
from burro_pipeline.cells.shapes import Point, Shape
from burro_pipeline.evidence.lock import LockError

SOURCE = "os-boundary-line"
MEMBER = "bdline_gb.gpkg"
WARDS, BOROUGHS = "district_borough_unitary_ward", "district_borough_unitary"
NAME, CODE, KIND, DESCRIPTION = "Name", "Census_Code", "Area_Code", "Area_Description"
# The file's codes for a ward and for a borough of London.
WARD_OF_LONDON, BOROUGH_OF_LONDON = "LBW", "LBO"
# What the file writes after the name of every ward and of nearly every borough of London.
WARD_ENDS, BOROUGH_ENDS = " Ward", " London Boro"


@dataclass(frozen=True)
class Outlined:
    """One ward or one borough: the statistics office's code, the name, and the outline."""

    record_id: str
    name: str
    # The kind of area, in the file's own words.
    kind: str
    shape: Shape

    @property
    def inside(self) -> Point:
        """A point that lies inside it."""
        return shapes.point_inside(self.shape)


def _read(file: File, layer: str, kind: str) -> tuple[Outlined, ...]:
    path = taken_out(file, MEMBER)
    rows = names_shapes.read_layer(
        path, file.file_id, layer, (NAME, CODE, DESCRIPTION), where=(KIND, kind)
    )
    found = [
        Outlined(row.text(CODE), row.text(NAME), row.text(DESCRIPTION), row.shape) for row in rows
    ]
    if not all(each.record_id and each.name for each in found):
        raise LockError("input_is_as_described", file.file_id, "an area lacks a code or a name")
    if len({each.record_id for each in found}) != len(found):
        raise LockError("input_is_as_described", file.file_id, "a code is held twice")
    return tuple(sorted(found, key=lambda each: each.record_id))


def read_wards(file: File) -> tuple[Outlined, ...]:
    """Every ward of London, in the order of their codes."""
    return _read(file, WARDS, WARD_OF_LONDON)


def read_boroughs(file: File) -> tuple[Outlined, ...]:
    """Every borough of London, in the order of their codes."""
    return _read(file, BOROUGHS, BOROUGH_OF_LONDON)
