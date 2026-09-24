"""The town centres: their outlines as the publisher's file draws them, and which is nearest.

The Greater London Authority publishes one GeoPackage of town centre
boundaries. Its one layer, `town_centres`, holds a row for each centre, with
an outline on the National Grid. Three measures read it: how far the nearest
centre is, whether it is a small one, and how compact it is. This module reads
the file for all three and works out no figure.

What is read of a row, and what is not:

| Column | Read | Why |
|---|---|---|
| `layerreference` | Yes | The id of the centre. It tells two centres apart |
| `geom` | Yes | The outline |
| `hectares` | Yes | The size the file gives. The outline as read is held to it |
| `sitename` | No | A figure needs no name. The registry asks for another use to show one |
| `classification` | No | The class says what part a centre plays, and not its size |
| `easting`, `northing` | No | The file's own point lies outside the outline of some centres |
| Every other column | No | |

**The outlines are a guide and no border.** The publisher's page calls them
indicative, and every row of the file says that the data belongs to the
planning authorities. So nothing here says that a home is in a town centre or
out of one. A distance is measured to the outline as drawn.

**The file holds the larger centres.** Its page names five kinds of centre,
down to the neighbourhood. The file that was described holds 234 rows, and 7
of them are of the local kind: `docs/research/data/m3-files.md` has the
counts. A parade of shops, or the centre of a village, that is below the rank
of a district is mostly not in it. So where the file holds no centre near a
home, that is not known to be a home with no shops near: the file does not
say. A measure of what kind of centre a home has gives such a home no figure.
Nought is never written for it.

**The file holds London alone.** A home near the edge of London may be nearer
to a centre beyond it, which no row holds. The files of a build give one thing
to tell by: the centres of population of the output areas beyond London. Where
a home is nearer to one of those than to the nearest centre the file holds, a
nearer centre may stand among those homes. Its nearest centre is then not
known, it adds nothing, and the coverage of its area falls by its homes.

Which centre is nearest. The distance is a straight line from the centre of
population of an output area to the nearest point of an outline, and nothing
where the outline holds the point. It is kept to the millimetre. Of two
centres as near, the one whose id sorts first is taken, so that a build
repeats. A few centres lie over one another, and a home inside two is given to
the first by id.

What the file is held to, because a figure rests on it:

- The layer is there, and says it is on the National Grid.
- Every id is written, and none is written twice.
- Every outline is a valid shape.
- The outline as read encloses what the row says it does, to 2 in 100. The
  file that was described gives each to 1 in 100.
- The file holds a centre. A file with none would read as a London with no
  town centre.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId

from burro_pipeline.areas import names_shapes
from burro_pipeline.cells import centres as homes_at
from burro_pipeline.cells.shapes import Point, Shape, hectares
from burro_pipeline.cells.spine import OA, Spine
from burro_pipeline.derive.centre_shapes import Points, fills_its_circle
from burro_pipeline.derive.methods import Worked, row_of, to_places
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "gla-town-centre-boundaries"
PUBLISHER = "the Greater London Authority"
PRODUCT = "Town Centre Boundaries"
# The publisher's name for the one file.
FILE = "Town_Centres_Boundaries.gpkg"
LAYER = "town_centres"
ID, HECTARES = "layerreference", "hectares"
FIELDS = (ID, HECTARES)
# How far the outline as read may be from the size the row gives, as a share of it.
AS_DRAWN = 0.02
# A home has a town centre of its own where one is no further than this, in metres and in a
# straight line. It is what ten minutes on foot would cover if the way were straight, and ten
# minutes is the catalogue's own measure of what is within a walk.
REACH = 800
# A distance is kept to so many decimal places of a metre, which is the millimetre. A point
# of the grid is written in six figures, and the last digits of what is worked out from two
# of them are no part of any distance.
KEPT = 3
# What the rows of the file are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = Geography.POLYGON
CENSUS = 2021


@dataclass(frozen=True)
class Centre:
    """One town centre, as the file draws it."""

    record_id: str
    shape: Shape
    # What its outline encloses, in hectares. A hole in it is no part of it.
    hectares: float
    # What it encloses as a share of the smallest circle that holds all of it, from 0 to 1.
    fills: float


@dataclass(frozen=True)
class Nearest:
    """The town centre nearest the homes of one output area."""

    centre: str
    # How far its outline is, in metres. Nothing where the outline holds the homes.
    metres: float


@dataclass(frozen=True)
class Found:
    """The centres of the file, and the nearest of them to each output area where it is known."""

    centres: Mapping[str, Centre]
    # By output area. One with no centre of population, and one that stands nearer to homes
    # beyond London than to any centre of the file, is not here.
    nearest: Mapping[str, Nearest]
    # How many output areas of the build have a centre of population, and how many of them
    # stand nearer to homes beyond London than to any centre of the file.
    placed: int
    may_be_nearer_beyond: int
    # The receipt of every file a figure rests on: the centres, where homes are, and the spine.
    files: tuple[Receipt, ...]
    # The day the receipt of the town centres gives for its data.
    as_at: str
    geography: Geography = KEYED_BY


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file these measures read."""
    return name == FILE


def _size(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError("a size that is no number")
    return float(value)


def read(opened: Opened) -> dict[str, Centre]:
    """Every centre of the file, by its id. It stops where the file is not as described above."""
    found: dict[str, Centre] = {}
    for row in names_shapes.read_layer(opened.path, opened.file_id, LAYER, FIELDS):
        record_id = row.text(ID)
        if not record_id or record_id in found:
            raise LockError("input_is_as_described", opened.file_id, "an id is missing or twice")
        drawn = hectares(row.shape)
        try:
            said = _size(row.fields[HECTARES])
            fills = fills_its_circle(row.shape)
        except ValueError:
            raise LockError(
                "input_is_as_described", opened.file_id, "a centre has no size"
            ) from None
        if not (said > 0 and abs(drawn - said) <= AS_DRAWN * said):
            raise LockError(
                "input_is_as_described", opened.file_id, "an outline is not of the size given"
            )
        found[record_id] = Centre(record_id, row.shape, drawn, fills)
    if not found:
        raise LockError("input_is_as_described", opened.file_id, "it holds no centre")
    return {record_id: found[record_id] for record_id in sorted(found)}


def homes_beyond(placed: Opened, spine: Spine) -> Points:
    """Where the homes beyond London stand.

    They are the centres of population of the output areas that the file of
    centres holds and the spine does not. A row that is no point stops the
    step, as it does for an output area of the build.
    """
    inside = spine.area_of
    kept: list[Point] = []
    with placed.text() as text:
        for row in placed.rows(text, (OA, homes_at.EASTING, homes_at.NORTHING)):
            if row[OA] in inside:
                continue
            try:
                point = float(row[homes_at.EASTING]), float(row[homes_at.NORTHING])
            except ValueError:
                point = math.nan, math.nan
            if not all(math.isfinite(part) for part in point):
                raise LockError("input_is_as_described", placed.file_id, "a point is no point")
            kept.append(point)
    return Points(kept)


def nearest_of(
    held: Mapping[str, Centre], points: Mapping[str, Point], beyond: Points
) -> dict[str, Nearest]:
    """The nearest centre to each output area, where no nearer one may stand beyond London.

    An output area is left out where homes beyond London are nearer to it than
    the nearest centre of the file. One as near to such homes as to a centre
    is kept: the centre is then no further than any that could stand there.
    """
    ground = names_shapes.Ground({record_id: one.shape for record_id, one in held.items()})
    found: dict[str, Nearest] = {}
    for oa in sorted(points):
        record_id = ground.nearest(points[oa])
        if record_id is None:
            continue
        metres = to_places(names_shapes.metres_from(ground.shape(record_id), points[oa]), KEPT)
        edge = beyond.nearest(points[oa])
        if edge is None or metres <= to_places(edge, KEPT):
            found[oa] = Nearest(record_id, metres)
    return found


def build(inputs: Inputs, spine: Spine, *, edition: str | None = None) -> Found:
    """The centres and the nearest of them to each output area, from the files of the build.

    The gate is asked about the town centres and about the centres of
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
    nearest = nearest_of(held, points, homes_beyond(placed, spine))
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


def within_reach(found: Found) -> dict[str, Nearest]:
    """The output areas with a town centre of their own: one no further than `REACH`."""
    return {oa: one for oa, one in found.nearest.items() if one.metres <= REACH}


def rows_of(
    found: Found, worked: Mapping[str, Worked], feature: FeatureId, method: Method
) -> tuple[EvidenceRow, ...]:
    """The row of evidence behind the figure of each area, and behind each that is missing."""
    return tuple(
        row_of(fact_id(area, FactKind.FEATURE, feature), worked[area], method, found.files)
        for area in sorted(worked)
    )
