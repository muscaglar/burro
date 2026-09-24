"""The town centres, as the Greater London Authority's file of boundaries writes them.

The file is a GeoPackage of one layer. Each centre has a name, a class, an
outline and a point. The name and the class are kept exactly as written.

A centre is known by its outline. The file's own point lies outside the
outline of some centres, so where a centre is taken to stand is its own point
when the outline holds it, and a point inside the largest piece of the outline
when it does not.

The design gives points for a centre "of district class or above". The file
writes eight classes. Four are of that rank as written. One more holds the word
for the rank and another word beside it: the file does not say that it is the
same class, so it is read as one and every centre of it is marked, for a person
to say.

Every row of the file carries one note, which says that the data belongs to the
planning authorities and that the publisher has not designated the boundaries.
So a centre's outline is a guide to where a centre is, and is never a border.
"""

from dataclasses import dataclass

from burro_pipeline.areas import names_shapes
from burro_pipeline.areas.names_files import File
from burro_pipeline.cells import shapes
from burro_pipeline.cells.shapes import Point, Shape
from burro_pipeline.evidence.lock import LockError

SOURCE = "gla-town-centre-boundaries"
LAYER = "town_centres"
ID, NAME, CLASS, EAST, NORTH = "layerreference", "sitename", "classification", "easting", "northing"
FIELDS = (ID, NAME, CLASS, EAST, NORTH)
# The classes that are of district rank or above, as the file writes them.
DISTRICT_OR_ABOVE = frozenset({"International", "Metropolitan", "Major", "District"})
# A class the file writes that holds the word for the rank and another word beside it.
READ_AS_DISTRICT = frozenset({"District Centre"})


@dataclass(frozen=True)
class Centre:
    """One town centre."""

    record_id: str
    name: str
    # The class, as written.
    rank: str
    # Who publishes the file, as the registry names them.
    publisher: str
    # The point the file gives, and whether the centre's own outline holds it.
    point: Point
    point_is_inside: bool
    shape: Shape

    @property
    def at(self) -> Point:
        """Where the centre is taken to stand."""
        return self.point if self.point_is_inside else shapes.point_inside(self.shape)

    @property
    def counts(self) -> bool:
        """Whether the centre is of district class or above, as the design asks."""
        return self.rank in DISTRICT_OR_ABOVE or self.rank in READ_AS_DISTRICT

    @property
    def rank_is_read(self) -> bool:
        """Whether the class was read as district rank, and is not written as it."""
        return self.rank in READ_AS_DISTRICT


def read(file: File) -> tuple[Centre, ...]:
    """Every centre of the file, in the order of their ids. It stops at an id held twice."""
    found: list[Centre] = []
    for row in names_shapes.read_layer(file.path, file.file_id, LAYER, FIELDS):
        east, north = row.fields[EAST], row.fields[NORTH]
        if not (
            isinstance(east, int | float)
            and isinstance(north, int | float)
            and row.text(ID)
            and row.text(NAME)
        ):
            raise LockError("input_is_as_described", file.file_id, "a centre lacks a field")
        point = (float(east), float(north))
        found.append(
            Centre(
                record_id=row.text(ID),
                name=row.text(NAME),
                rank=row.text(CLASS),
                publisher=file.publisher,
                point=point,
                point_is_inside=names_shapes.holds(row.shape, point),
                shape=row.shape,
            )
        )
    if len({centre.record_id for centre in found}) != len(found):
        raise LockError("input_is_as_described", file.file_id, "an id is held twice")
    return tuple(sorted(found, key=lambda centre: centre.record_id))
