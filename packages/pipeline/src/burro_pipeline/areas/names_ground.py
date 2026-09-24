"""London, as the ground a name is placed on: its output areas and their boroughs.

London is the rows of the statistics office's lookup whose local authority
code starts `E09`, as the spine has it. It is read here for the use
`gazetteer`, with the spine's own reader, and without the table of homes: the
gate does not give that table for this use.

A record is in London when its point lies in an output area of London, or on
the edge of one. The outlines are the full-resolution ones, which run to the
mean high water mark. The generalised outlines put one name in 23 in another
output area. A point on the line between two output areas is given to the one
whose code sorts first. The borough of a record is the borough of its output
area, and never the borough its own file writes.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from burro_pipeline.areas.names_files import File, with_receipt
from burro_pipeline.areas.names_shapes import Ground
from burro_pipeline.cells import shapes, spine
from burro_pipeline.cells.shapes import Point
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Inputs

BOUNDARIES = "ons-output-areas-2021"
# The full-resolution outlines, clipped to the coast.
EDITION = "BFC V8"
CODE = "OA21CD"


@dataclass(frozen=True)
class London:
    """The output areas of London, and the borough of each."""

    ground: Ground
    # The borough of each output area, by the statistics office's code.
    borough_of: Mapping[str, str]
    # The name of each borough, as the lookup writes it.
    borough_names: Mapping[str, str]
    lookup: File
    boundaries: File

    def cell_of(self, point: Point) -> str | None:
        """The output area a point is given to, or nothing if it is not in London."""
        return self.ground.first_holding(point)

    def borough_at(self, point: Point) -> str | None:
        cell = self.cell_of(point)
        return None if cell is None else self.borough_of[cell]


def read(inputs: Inputs) -> London:
    """London, from the lookup and the full-resolution outlines of the output areas."""
    lookup = with_receipt(inputs, spine.LOOKUP, edition=spine.LOOKUP_EDITION)
    rows = spine.read_lookup(lookup.opened)
    borough_of = {row[spine.OA]: row[spine.BOROUGH] for row in rows}
    if not rows or len(borough_of) != len(rows):
        raise LockError("input_is_as_described", lookup.file_id, "an output area is there twice")
    names = {row[spine.BOROUGH]: row[spine.BOROUGH_NAME] for row in rows}
    boundaries = with_receipt(inputs, BOUNDARIES, edition=EDITION)
    outlines = shapes.read_outlines(boundaries.opened, CODE, set(borough_of))
    if set(outlines) != set(borough_of):
        raise LockError("input_is_as_described", boundaries.file_id, "an outline is missing")
    return London(
        ground=Ground(outlines),
        borough_of=dict(sorted(borough_of.items())),
        borough_names=dict(sorted(names.items())),
        lookup=lookup,
        boundaries=boundaries,
    )
