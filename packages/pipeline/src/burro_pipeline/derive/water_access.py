"""Water close by: the share of an area's homes that are near a river, a canal or a lake.

Ordnance Survey publishes OS Open Rivers twice a year, as one GeoPackage for
Great Britain inside a zip. Its layer `watercourse_link` holds one row for
each stretch of water between two nodes. A row says what form the water takes
and draws it as one line, on the National Grid, in metres. The line has no
width: the file does not say how wide a river is, or where its bank is.

**It is a share of homes, and not of the area.** It is what the pipeline design
asks for and what `homes_within` works out. A share of an area's land is
another figure, and a park or a works beside a river moves it where no home
stands. So the row of the catalogue carries `LABEL`, which says homes, a
straight line and the line along the middle of the water, as core names the
measure. Do not name it a share of the area while it counts homes.

What counts as water, from the file's own classes. The column `form` holds one
of four words, and every one counts. The file names the forms and defines
none of them, and no page of the publisher was opened for this. So the reading
rests on the names alone:

| `form` | Counts | What the name says |
|---|---|---|
| `inlandRiver` | Yes | A river that the tide does not reach |
| `tidalRiver` | Yes | A river that the tide reaches |
| `canal` | Yes | A canal |
| `lake` | Yes | A lake, where a line of the layer runs through one |

What the file cannot tell apart, so that nothing is left out for it:

- **Water in the open from water under the ground.** No column says that a
  stretch runs in a culvert, a pipe or a tunnel. Some stretches are drawn as
  one long straight line. The file does not say what they are, and no
  stretch is left out for how it is drawn.
- **A river from a ditch.** Many rows have no name. The file has no class for
  the size of a stream, and a name is not a class, so a stretch with no name
  counts as one with a name does. No name is read.
- **A lake with no line.** The file draws a line through a lake, and holds no
  outline of one. A lake, a pond, a dock or a reservoir that no line is drawn
  through is not in the file at all.

The column `fictitious` is `0` in every row of the file this was written on.
A row that is marked otherwise stops the build, until a person has read what
the publisher means by it.

How a figure is made:

1. A home is placed at the point the statistics office gives as the centre of
   population of its output area.
2. For each output area, the distance in a straight line from that point to
   the nearest line of the file, in metres. It is worked out to the nearest
   point of the line, and not only to the points the line is drawn with.
3. An output area is near water where that distance is 300 metres or less.
   The distance is core's and the design's.
4. An area's figure is the homes of its output areas that are near, over the
   homes of its output areas that have a verdict, as a percentage. That is
   `homes_within`, which the pipeline design names. It is given to one
   decimal place.
5. An output area has a verdict where it has a centre, and the centre is
   inside the box the file says its lines cover. One that has none adds
   nothing and lowers the coverage. It is never taken to be far from water.

Nought is a figure. An area that the file covers, with no line within 300
metres of any of its centres, reads 0.0: the publisher drew no water there.

What the centre and the line cost. A line with no width stands for water that
has one, and the licence registry records that the line is drawn along the
middle of the water. Where a river is 400 metres wide its bank is then 200
metres from the line, and a home on the bank is near only if its centre is
within 100 metres of the water's edge. So the figure is too low beside wide
water. And every home of an output area takes the verdict of its centre, so
the figure moves in steps of about 4 in 100.

How the file is laid out, and what the parser holds it to:

- A zip with one member whose name ends `.gpkg`. It is unpacked to the step's
  own folder to be read, and the copy is removed afterwards.
- A layer `watercourse_link` of lines in two dimensions, on the National
  Grid. The file holds a second layer, `hydro_node`, which is not read.
- The columns `geometry`, `form`, `fictitious` and `length`. No other column
  is read: not the name of a river, and not the way it flows.
- A form is one of the four above. A form the parser has not met stops the
  build: water under a new name would otherwise be counted as none.
- The file says how long each stretch is. The lines as drawn must add up to
  within 0.5 in 100 of that, or the lines were not read as they are.
- The day the layer was last changed must fall in the month its receipt gives
  as its edition, so that the period a figure is shown with is the file's own.
- The file's own index of where each line lies is used to read the water
  within 10,000 metres of the box the homes of the build stand in, and no
  other. It is held to the count of the layer's rows. Without an index every
  row is read, and the same water is kept.
- More than 1 in 100 centres with no line within 10,000 metres stops the
  build: the file then holds no water round these homes, and a share of
  nought would be a gap read as a figure. Water is not everywhere, as roads
  are, so the file is asked for no more than that.

A line is read from its bytes by `line_of` in `derive/road_major_exposure.py`:
the publisher lays out the lines of its roads and of its rivers the same way.
"""

import math
import re
import shutil
import sqlite3
import struct
import zipfile
from collections.abc import Collection, Generator, Iterable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.shapes import NATIONAL_GRID
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, homes_within, homes_within_at, row_of, to_places
from burro_pipeline.derive.road_major_exposure import Box, Line, box_of, line_of, metres_of
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.fetch.kinds import read_only
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.WATER_ACCESS
SOURCE = "os-open-rivers"
PUBLISHER = "Ordnance Survey"
PRODUCT = "OS Open Rivers"
# The publisher names the zip for the product, its format and what it covers.
FILE_STARTS = "oprvrs_gpkg"
MEMBER_ENDS = ".gpkg"
# A member is unpacked to be read. One that unpacks to more than this is not read.
MEMBER_LIMIT = 8 * 1024**3
LAYER = "watercourse_link"
GEOMETRY, FORM, FICTITIOUS, LENGTH = "geometry", "form", "fictitious", "length"
COLUMNS = (GEOMETRY, FORM, FICTITIOUS, LENGTH)
# The forms the file is known to write, in the order of their names. Every one counts.
FORMS: tuple[str, ...] = ("canal", "inlandRiver", "lake", "tidalRiver")
# How the file marks a stretch that is there, and one that is not. The column is text.
THERE, NOT_THERE = ("0", 0), ("1", 1)
LINES = "LINESTRING"
# The extension a GeoPackage names where a layer has an index of where each row lies.
INDEXED_BY = "gpkg_rtree_index"
INDEX = f"rtree_{LAYER}_{GEOMETRY}"
# A home is near water within this many metres of a line.
METRES = 300
# A line is looked for this far from a home, in metres, and no further.
REACH = 10_000
# The file holds water round the homes of a build where all but a few centres have a line
# within reach.
UNREACHED_IN_100 = 1
# The lines are kept by squares this wide while the nearest is looked for, in metres.
KEPT_BY = 500
# The lines as drawn add up to what the file says they do, to within this share.
LENGTH_GATE = 0.005
# What the rows of the file are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = Geography.LINE
# A figure is given to this many decimal places.
DECIMALS = 1
CENSUS = 2021
DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

# The arithmetic: what a methods page prints beside the measure, and what a row of evidence names.
METHOD = homes_within_at(METRES)
METHODS: tuple[Method, ...] = (METHOD,)
# What a person reads beside the figure, which is core's name for the measure.
# It says that the distance is a straight line, and that it is to the line the file draws
# along the middle of the water and not to the bank.
LABEL = (
    "Share of homes within 300 m, in a straight line, of the centre line of a river, canal or lake"
)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The share of the area's homes that are within {metres} metres of a river, a canal or a "
    "lake, from {publisher}'s {product} of {edition}: each home is placed at the point the "
    "statistics office gives as the centre of its census output area, homes are counted as "
    "they stood at the census of {census}, the distance is in a straight line to the line the "
    "file draws for a river, a tidal river, a canal or a lake, and the figure is given to "
    "{decimals} decimal place with a half taken upward, so it is measured to a line with no "
    "width and not to the edge of the water, the file does not say where water runs under the "
    "ground, and it is not a measure of a view, of a walk to the water or of the risk of a flood."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It measures in a straight line from the centre of each small census area to a line drawn "
    "along the water, which has no width, so a home on the bank of a wide river can be counted "
    "as away from it.",
    "It cannot tell water that runs in the open from water that runs in a tunnel or a pipe, and "
    "it counts a lake only where its publisher draws a line through one.",
)

# One straight part of a line: where it starts and where it ends.
Part = tuple[float, float, float, float]
Square = tuple[int, int]


def is_the_network(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the rivers as a GeoPackage."""
    return name.startswith(FILE_STARTS)


@dataclass(frozen=True)
class Link:
    """One stretch of water, as far as the measure reads it."""

    form: str
    line: Line


@dataclass(frozen=True)
class Rivers:
    """The water of the publisher's file that lies round the homes of a build."""

    # The month the layer was last changed, which is the month of the receipt.
    edition: str
    # The box the file says its lines cover.
    covers: Box
    # The stretches whose line comes within reach of the homes of the build.
    links: tuple[Link, ...]
    # How many rows the layer holds, for all of Great Britain.
    rows: int
    # How many of the stretches that were read the file gives each form.
    by_form: Mapping[str, int]
    # What the file says the stretches that were read are long, and what their lines add up to.
    metres_stated: float
    metres_drawn: float
    # Whether the file's own index was used to find them.
    indexed: bool
    file_id: str


@dataclass(frozen=True)
class Access:
    """The measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    rivers: Rivers
    geography: Geography
    # How far each output area is from the nearest line, in metres, where it has a verdict
    # and a line is within reach.
    metres: Mapping[str, float]
    # The verdict of each output area that has one: whether it is near water.
    near: Mapping[str, bool]
    # How many centres have no line within reach.
    unreached: int


def _refused(file_id: str, words: str) -> LockError:
    return LockError("input_is_as_described", file_id, words)


@contextmanager
def _unpacked(opened: Opened) -> Generator[Path]:
    """The GeoPackage inside the zip, unpacked to the step's own folder while it is read."""
    name = opened.member(MEMBER_ENDS)
    to = opened.path.parent / "unpacked" / f"{opened.file_id}{MEMBER_ENDS}"
    try:
        try:
            to.parent.mkdir(parents=True, exist_ok=True)
            to.unlink(missing_ok=True)
            with zipfile.ZipFile(opened.path) as archive:
                # No more is unpacked than the zip says the member holds.
                if archive.getinfo(name).file_size > MEMBER_LIMIT:
                    raise _refused(opened.file_id, "it unpacks to more than is read")
                with archive.open(name) as packed, to.open("xb") as target:
                    shutil.copyfileobj(packed, target, 16 * 1024 * 1024)
        except (zipfile.BadZipFile, OSError, EOFError):
            raise _refused(opened.file_id, "it could not be unpacked") from None
        yield to
    finally:
        to.unlink(missing_ok=True)


def _meet(a: Box, b: Box) -> bool:
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _layer(database: sqlite3.Connection, opened: Opened) -> tuple[str, Box]:
    """The month the layer was last changed and the box it covers, once it is seen to be water."""
    file_id = opened.file_id
    stated = database.execute(
        "SELECT data_type, srs_id, last_change, min_x, min_y, max_x, max_y "
        "FROM gpkg_contents WHERE table_name = ?",
        (LAYER,),
    ).fetchone()
    if stated is None or tuple(stated[:2]) != ("features", NATIONAL_GRID):
        raise _refused(file_id, "it holds no layer of water on the National Grid")
    drawn = database.execute(
        "SELECT column_name, geometry_type_name, srs_id, z, m "
        "FROM gpkg_geometry_columns WHERE table_name = ?",
        (LAYER,),
    ).fetchone()
    if drawn is None or tuple(drawn) != (GEOMETRY, LINES, NATIONAL_GRID, 0, 0):
        raise _refused(file_id, "its water is not lines in two dimensions")
    held = {row[0] for row in database.execute("SELECT name FROM pragma_table_info(?)", (LAYER,))}
    for name in COLUMNS:
        if name not in held:
            raise _refused(file_id, f"the column {name} is missing")
    changed = str(stated[2])[:10]
    first, last = opened.receipt.data_period.days()
    if not DAY.fullmatch(changed) or not first <= changed <= last or first[:7] != last[:7]:
        raise _refused(file_id, "the month it was made is not the month of its receipt")
    corners = stated[3:]
    if not all(isinstance(part, int | float) and math.isfinite(part) for part in corners):
        raise _refused(file_id, "it does not say what it covers")
    covers: Box = (float(corners[0]), float(corners[1]), float(corners[2]), float(corners[3]))
    if covers[0] >= covers[2] or covers[1] >= covers[3]:
        raise _refused(file_id, "it does not say what it covers")
    return changed[:7], covers


def _has_an_index(database: sqlite3.Connection) -> bool:
    """Whether the file names an index of its water, and this SQLite can read one."""
    named = database.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name = 'gpkg_extensions'"
    ).fetchone()
    if not named[0]:
        return False
    found = database.execute(
        "SELECT COUNT(*) FROM gpkg_extensions "
        "WHERE table_name = ? AND column_name = ? AND extension_name = ?",
        (LAYER, GEOMETRY, INDEXED_BY),
    ).fetchone()
    able = {str(row[0]) for row in database.execute("PRAGMA compile_options")}
    return bool(found[0]) and "ENABLE_RTREE" in able


# Every name in these is written in this module. None is taken from the file.
_NAMED = ", ".join(f'l."{name}"' for name in COLUMNS)
_BY_THE_INDEX = (
    f'SELECT {_NAMED} FROM "{INDEX}" AS r JOIN "{LAYER}" AS l ON l.fid = r.id '  # noqa: S608
    "WHERE r.maxx >= ? AND r.minx <= ? AND r.maxy >= ? AND r.miny <= ?"
)
_EVERY_ROW = f'SELECT {_NAMED} FROM "{LAYER}" AS l'  # noqa: S608
_COUNT = f'SELECT COUNT(*), SUM(l."{GEOMETRY}" IS NULL) FROM "{LAYER}" AS l'  # noqa: S608
_COUNT_OF_THE_INDEX = f'SELECT COUNT(*) FROM "{INDEX}"'  # noqa: S608


def _drawn(blob: object, file_id: str) -> Line:
    """The line of one row, or a refusal."""
    if not isinstance(blob, bytes):
        raise _refused(file_id, "a stretch of water has no line")
    try:
        return line_of(blob)
    except (ValueError, struct.error):
        raise _refused(file_id, "a stretch of water is not a line in two dimensions") from None


def _classed(row: Sequence[object], file_id: str) -> tuple[str, float]:
    """One row as its form and the length the file states, once it is seen to be there."""
    form, fictitious, length = row
    if not isinstance(form, str) or form not in FORMS:
        raise _refused(file_id, "a stretch of water is of a form that is not known")
    if fictitious in NOT_THERE:
        raise _refused(file_id, "a stretch of water is marked as fictitious")
    if fictitious not in THERE:
        raise _refused(file_id, "a stretch of water is neither there nor not there")
    if not isinstance(length, int | float) or not math.isfinite(length) or length < 0:
        raise _refused(file_id, "a length is no length")
    return form, float(length)


def _read(database: sqlite3.Connection, opened: Opened, around: Box) -> Rivers:
    file_id = opened.file_id
    edition, covers = _layer(database, opened)
    rows, without = database.execute(_COUNT).fetchone()
    if not rows:
        raise _refused(file_id, "it holds no water")
    if without:
        raise _refused(file_id, "a stretch of water has no line")
    indexed = _has_an_index(database)
    if indexed and database.execute(_COUNT_OF_THE_INDEX).fetchone()[0] != rows:
        raise _refused(file_id, "its index does not hold every stretch of water")
    west, south, east, north = around
    found = (
        database.execute(_BY_THE_INDEX, (west, east, south, north))
        if indexed
        else database.execute(_EVERY_ROW)
    )
    links: list[Link] = []
    by_form = dict.fromkeys(FORMS, 0)
    stated: list[float] = []
    drawn: list[float] = []
    for row in found:
        line = _drawn(row[0], file_id)
        # The index holds a box a little wider than the line. The line itself decides, so
        # that the same water is kept with an index and without one.
        if not _meet(box_of(line), around):
            continue
        form, length = _classed(row[1:], file_id)
        by_form[form] += 1
        stated.append(length)
        drawn.append(metres_of(line))
        links.append(Link(form=form, line=line))
    metres_stated, metres_drawn = math.fsum(stated), math.fsum(drawn)
    if abs(metres_drawn - metres_stated) > LENGTH_GATE * metres_stated:
        raise _refused(file_id, "its lines are not as long as it says")
    # In a fixed order, whatever order the file gave them in.
    links.sort(key=lambda link: (link.line, link.form))
    return Rivers(
        edition=edition,
        covers=covers,
        links=tuple(links),
        rows=int(rows),
        by_form=by_form,
        metres_stated=metres_stated,
        metres_drawn=metres_drawn,
        indexed=indexed,
        file_id=file_id,
    )


def read(opened: Opened, around: Box) -> Rivers:
    """The water of the file whose line comes inside a box, each stretch with its form.

    `around` is the box the homes of the build stand in, widened by as far as
    a line is looked for. Water outside London counts where it is near a home
    inside it.
    """
    with _unpacked(opened) as path:
        try:
            database = read_only(path)
            try:
                return _read(database, opened, around)
            finally:
                database.close()
        except (sqlite3.Error, OSError):
            raise _refused(opened.file_id, "its water could not be read") from None


def _square_of(x: float, y: float) -> Square:
    return math.floor(x / KEPT_BY), math.floor(y / KEPT_BY)


def _kept(lines: Iterable[Line]) -> dict[Square, list[Part]]:
    """Every straight part of every line, by each square of a grid that its box touches."""
    found: dict[Square, list[Part]] = {}
    for line in lines:
        for at in range(0, len(line) - 2, 2):
            x0, y0, x1, y1 = line[at : at + 4]
            west, south = _square_of(min(x0, x1), min(y0, y1))
            east, north = _square_of(max(x0, x1), max(y0, y1))
            for across in range(west, east + 1):
                for up in range(south, north + 1):
                    found.setdefault((across, up), []).append((x0, y0, x1, y1))
    return found


def _ring(own: Square, ring: int) -> list[Square]:
    """The squares that stand so many squares from a square, in a ring round it."""
    if ring == 0:
        return [own]
    reach = range(-ring, ring + 1)
    return [
        (own[0] + across, own[1] + up)
        for across in reach
        for up in reach
        if max(abs(across), abs(up)) == ring
    ]


def _squared(point: Point, part: Part) -> float:
    """The distance from a point to the nearest point of a straight part, squared.

    Only sums, products and one division are taken, so that the same points
    give the same answer on every machine.
    """
    x, y = point
    x0, y0, x1, y1 = part
    along_x, along_y = x1 - x0, y1 - y0
    along = (x - x0) * along_x + (y - y0) * along_y
    whole = along_x * along_x + along_y * along_y
    if along <= 0 or whole == 0:
        nearest_x, nearest_y = x0, y0
    elif along >= whole:
        nearest_x, nearest_y = x1, y1
    else:
        nearest_x, nearest_y = x0 + along / whole * along_x, y0 + along / whole * along_y
    return (x - nearest_x) ** 2 + (y - nearest_y) ** 2


def nearest_squared(
    points: Mapping[str, Point], lines: Iterable[Line], reach: float = REACH
) -> dict[str, float]:
    """The square of how far each point is from the nearest of the lines, in a straight line.

    The distance is to the nearest point of a line, which may lie between two
    of the points the line is drawn with. A point with no line within `reach`
    has no distance: it is left out, and is not given the reach. The answer
    does not turn on the order of the points or of the lines.
    """
    kept = _kept(lines)
    found: dict[str, float] = {}
    for name in sorted(points):
        point = points[name]
        own = _square_of(*point)
        best, ring = math.inf, 0
        # Once the squares within so many rings have been looked at, a part that none of
        # them holds lies at least that many squares from a point on the square in the middle.
        while (ring - 1) * KEPT_BY <= reach and (ring == 0 or ((ring - 1) * KEPT_BY) ** 2 < best):
            for square in _ring(own, ring):
                for part in kept.get(square, ()):
                    best = min(best, _squared(point, part))
            ring += 1
        if best <= reach * reach:
            found[name] = best
    return found


def nearest(
    points: Mapping[str, Point], lines: Iterable[Line], reach: float = REACH
) -> dict[str, float]:
    """How far each point is from the nearest of the lines, in metres, in a straight line."""
    return {
        name: math.sqrt(squared) for name, squared in nearest_squared(points, lines, reach).items()
    }


def verdicts(
    rivers: Rivers, points: Mapping[str, Point]
) -> tuple[dict[str, bool], dict[str, float], int]:
    """Whether each output area is near water, how far each is, and how many have none in reach.

    An output area has a verdict where it has a centre and the centre is
    inside the box the file says its lines cover. One with a verdict and no
    line within reach is far from water, and has no distance. It stops where
    the file holds no water round the homes of the build.
    """
    west, south, east, north = rivers.covers
    covered = {
        oa: point
        for oa, point in points.items()
        if west <= point[0] <= east and south <= point[1] <= north
    }
    squared = nearest_squared(covered, (link.line for link in rivers.links))
    unreached = len(covered) - len(squared)
    if unreached * 100 > UNREACHED_IN_100 * len(covered):
        raise _refused(rivers.file_id, "its water does not reach the homes of the build")
    # The verdict is taken on the square of the distance, which no root has rounded.
    near = {oa: oa in squared and squared[oa] <= METRES * METRES for oa in sorted(covered)}
    return near, {oa: math.sqrt(squared[oa]) for oa in sorted(squared)}, unreached


def figures(near: Mapping[str, bool], found: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, or why an area has none."""
    worked = homes_within(near, found.weights, times=100)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def metric_of(files: Sequence[Receipt], edition: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is `LABEL`: the one
    the figure supports. The period is the month of the publisher's release.
    """
    return catalogue_row(
        FEATURE,
        method=METHOD,
        label=LABEL,
        source_ids={receipt.source_id for receipt in files},
        vintage=edition,
        definition=DEFINITION.format(
            metres=METRES,
            publisher=PUBLISHER,
            product=PRODUCT,
            edition=edition,
            census=CENSUS,
            decimals=DECIMALS,
        ),
    )


def around_of(points: Collection[Point]) -> Box:
    """The box some centres stand in, widened by as far as a line is looked for."""
    if not points:
        raise ValueError("a build has homes")
    east, north = [point[0] for point in points], [point[1] for point in points]
    return min(east) - REACH, min(north) - REACH, max(east) + REACH, max(north) + REACH


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Access:
    """The figure of every area and its evidence, from the files of the build.

    The gate is asked about the water and about the centres before either is
    read. `found` is the spine of the same build: a row of evidence names its
    files beside the water and the centres, so they must be files this build
    opened. `edition` is the month of the release, as the receipt gives it.
    It tells apart the files of two releases, once the store holds both.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=edition, named=is_the_network)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    points = centres.centres_of(placed, found)
    if not points:
        raise _refused(placed.file_id, "it holds no centre of the build")
    rivers = read(opened, around_of(points.values()))
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted({opened.file_id, placed.file_id, *found.inputs})
    if not all(file_id in handed for file_id in behind):
        raise ValueError("the spine is made from files of this build")
    files = tuple(handed[file_id] for file_id in behind)
    near, metres, unreached = verdicts(rivers, points)
    worked = figures(near, found)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    return Access(
        worked=worked,
        rows=rows,
        metric=metric_of(files, rivers.edition),
        files=files,
        rivers=rivers,
        geography=KEYED_BY,
        metres=metres,
        near=near,
        unreached=unreached,
    )
