"""The high streets: their outlines as the publisher's file draws them, and which is nearest.

The Greater London Authority publishes one GeoPackage of high street
boundaries. Its one layer, `Table1`, holds a row for each piece of a high
street, with an outline on the National Grid. This module reads the file and
works out no figure.

What is read of a row, and what is not:

| Column | Read | Why |
|---|---|---|
| `highstreet_id` | Yes | The id of the high street. The rows of one id are one high street |
| `geom` | Yes | The outline of the piece |
| `highstreet_name` | No | A figure needs no name. The registry gives the file for scoring alone |
| `area_ha` | No | It is not the size of the row's outline. See below |
| `id`, `objectid` | No | They tell one row from another, and not one high street |
| `gdb_geomattr_data` | No | It is what the publisher's software keeps |

**A high street is the rows of one id, joined.** The file draws a high street
that stands in several pieces as several rows, each of one piece, under one
id. Some pieces enclose a square metre or less. So the rows of an id are
joined, and what a measure reads is the outline of them all.

**The size the file gives is not read.** `area_ha` is the same on every row
of an id, so it is no size of a piece. It is no size of the high street
either: the file that was read gives two pairs of high streets, each under
ids of its own, the size of the pair. So a size is what the joined outline
encloses, as it is drawn.

**The outlines are wider than a town centre's.** Their page says they
"reflect the wider uses of High Streets including community, public and
cultural, in addition to concentrations of retail units". So a high street
and a town centre of one place are two outlines, and the size of one says
nothing of the size of the other.

**The file holds London alone.** A home near the edge of London may be nearer
to a high street beyond it, which no row holds. So the nearest high street is
known only where no home beyond London is nearer: `town_centres.py` holds the
rule, and it is asked here.

**It holds more than the town centres.** The file of town centres holds
London's larger centres. This one holds the local ones too, and a high street
is within 800 metres of nine in ten of London's homes. It does not hold every
centre a person would name, and nothing in it says which it leaves out.

What the file is held to, because a figure rests on it:

- The layer is there, and says it is on the National Grid.
- Every row has an id.
- Every outline is a valid shape, so every high street encloses land.
- The file holds a high street. A file with none would read as a London with
  no high street.
"""

from burro_pipeline.areas import names_shapes
from burro_pipeline.cells import centres as homes_at
from burro_pipeline.cells.shapes import Shape, hectares, joined
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import town_centres
from burro_pipeline.derive.centre_shapes import fills_its_circle
from burro_pipeline.derive.town_centres import Centre, Found
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "gla-high-street-boundaries"
PUBLISHER = "the Greater London Authority"
PRODUCT = "High Street Boundaries"
# The publisher's name for the one file.
FILE = "GLA_High_Street_boundaries_2.gpkg"
LAYER = "Table1"
ID = "highstreet_id"
FIELDS = (ID,)
# A home has a high street of its own where one is no further than this, in metres and in a
# straight line: what a town centre is held to.
REACH = town_centres.REACH
# What the rows of the file are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = Geography.POLYGON
CENSUS = town_centres.CENSUS


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file that is read."""
    return name == FILE


def read(opened: Opened) -> dict[str, Centre]:
    """Every high street of the file, by its id. It stops where the file is not as described.

    A high street is kept as a town centre is: its id, its outline, what the
    outline encloses and how much of its circle it fills.
    """
    pieces: dict[str, list[Shape]] = {}
    for row in names_shapes.read_layer(opened.path, opened.file_id, LAYER, FIELDS):
        record_id = row.text(ID)
        if not record_id:
            raise LockError("input_is_as_described", opened.file_id, "an id is missing")
        pieces.setdefault(record_id, []).append(row.shape)
    if not pieces:
        raise LockError("input_is_as_described", opened.file_id, "it holds no high street")
    found: dict[str, Centre] = {}
    for record_id in sorted(pieces):
        shape = joined(pieces[record_id])
        found[record_id] = Centre(record_id, shape, hectares(shape), fills_its_circle(shape))
    return found


def build(inputs: Inputs, spine: Spine, *, edition: str | None = None) -> Found:
    """The high streets and the nearest of them to each output area, from the files of the build.

    The gate is asked about the high streets and about the centres of
    population before either is read. `spine` is the spine of the same build:
    a row of evidence names its files beside the two, so they must be files
    this build opened.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=edition, named=is_the_file)
    placed = inputs.open(homes_at.CENTRES, Use.SCORING, edition=homes_at.CENTRES_EDITION)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(spine.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    held = read(opened)
    points = homes_at.centres_of(placed, spine)
    nearest = town_centres.nearest_of(held, points, town_centres.homes_beyond(placed, spine))
    behind = sorted({opened.file_id, placed.file_id, *spine.inputs})
    period = opened.receipt.data_period
    return Found(
        centres=held,
        nearest=nearest,
        placed=len(points),
        may_be_nearer_beyond=len(points) - len(nearest),
        files=tuple(handed[file_id] for file_id in behind),
        as_at=period.as_at or f"{period.start} to {period.end}",
    )
