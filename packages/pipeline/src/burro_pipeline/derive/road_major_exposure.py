"""Main roads: the share of an area's homes that are near a motorway or an A road.

Ordnance Survey publishes OS Open Roads twice a year, as one GeoPackage for
Great Britain inside a zip. Its layer `road_link` holds one row for each
stretch of road, from one node of the network to the next. A row says how the
road is classed and draws it as one line, on the National Grid, in metres. The
file does not say where across a road its line runs. It calls some roads a
collapsed dual carriageway, which is read here as one line for both sides.

The measure is a part of the vibe of quiet streets. It says how much of an
area stands beside a road of the file's two highest classes. It is not a
measure of traffic, of noise or of air: the file holds none of those.

**It is core's measure of main roads**, `road_major_exposure`, and a build
carries it. Core names it "Share of homes within 100 m of a main road", and
the row of the catalogue that is made here is core's. The sentence of the
measure says what the name leaves out: which roads are main, that the
distance is a straight line, and that it is to the line the file draws along
the road and not to its kerb.

**The row switches the measure off for ranking by itself.** Its values are
shown. The design expects main roads to follow who lives somewhere, and no
audit of the figure has been run (ADR 0006). A vibe still rests on it: core
places a vibe on every part of its recipe that a release holds.

How a figure is made:

1. A road is a main road where the file classes it `Motorway` or `A Road`. A
   stretch the file marks `Road In Tunnel` is left out: a road under the
   ground is not beside a home. Every form of way counts: a slip road and a
   roundabout of a main road are part of it.
2. A home is placed at the point the statistics office gives as the centre of
   population of its output area. An output area is near a main road where
   that point is within 100 metres of the line of one, in a straight line.
3. An area's figure is the homes of its output areas that are near, over the
   homes of its output areas that have a verdict, as a percentage. That is
   `homes_within`, which the pipeline design names. It is given to one
   decimal place.
4. An output area has a verdict where it has a centre, and the centre is
   inside the box the file says its roads cover. One that has none adds
   nothing and lowers the coverage. It is never taken to be far from a road.

Why 100 metres. The design names it, and gives no reason. It is about as
fine as the data can bear. The first build counted 26,369 output areas on
157,334 hectares of land, so one covers 6 hectares on average, which is a
square about 240 metres wide. A centre then stands for homes 100 metres and
more from it, and a shorter distance would ask of a centre what it cannot
say. A longer one takes in homes that no main road is beside. No file in the
store says at what distance a road is no longer heard, so the distance is a
choice and not a finding.

What a centre costs. The centre of an output area is not a front door. Every
home of an output area takes the verdict of its centre. So a home that fronts
a main road is counted as away from it where the centre of its output area is
101 metres back, and a home at the back of an output area is counted as near
where the centre is 99 metres from the road. Within an area of some 26 output
areas the two errors partly cancel, and a figure still moves in steps of
about 4 in 100. Main roads are often the edge of an output area and seldom
its middle, so the figure is likelier to be too low than too high. That last
is reasoning, and it has not been measured: no file in the store places each
home.

How the file is laid out, and what the parser holds it to:

- A zip with one member whose name ends `.gpkg`. It is unpacked to the step's
  own folder to be read, and the copy is removed afterwards.
- A layer `road_link` of lines in two dimensions, on the National Grid.
- The columns `geometry`, `road_classification`, `road_structure`,
  `fictitious` and `length`. No other column is read: not the name of a
  road, and not its number.
- A class is one of seven the file is known to write. `Unknown` and
  `Not Classified` are classes of their own, and neither is a main road. A
  class the parser has not met stops the build: a main road under a new name
  would otherwise be counted as none.
- `road_structure` is empty or `Road In Tunnel`. No road is marked
  `fictitious` in the file this was written on, and one that is stops the
  build until a person has read what it means.
- The file says how long each road is. The lines as drawn must add up to
  within 0.5 in 100 of that, or the lines were not read as they are.
- The day the layer was last changed must fall in the month its receipt
  gives as its edition, so that the period a figure is shown with is the
  file's own.
- The file's own index of where each road lies is used to read the roads near
  the homes of the build and no others. It is held to the count of the
  layer's rows. Without an index every row is read, and the same roads are
  kept.
- More than 1 in 100 centres further than 250 metres from any road of any
  class stops the build: the file then holds no network under these homes,
  and a share of nought would be a gap read as a figure.
"""

import math
import re
import shutil
import sqlite3
import struct
import zipfile
from collections.abc import Collection, Generator, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.shapes import BOX, HEADER, MAGIC, NATIONAL_GRID
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, homes_within, homes_within_at, row_of, to_places
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.fetch.kinds import read_only
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.ROAD_MAJOR_EXPOSURE
# The id the rows are written under.
KEY = FEATURE.value
# Whether an area is ranked on the figure by itself. The design expects main roads to follow
# who lives somewhere, and no audit of the figure has been run (ADR 0006).
RANKABLE = False
SOURCE = "os-open-roads"
PUBLISHER = "Ordnance Survey"
PRODUCT = "OS Open Roads"
# The publisher names the zip for the product, its format and what it covers.
FILE_STARTS = "oproad_gpkg"
MEMBER_ENDS = ".gpkg"
# A member is unpacked to be read. One that unpacks to more than this is not read.
MEMBER_LIMIT = 8 * 1024**3
LAYER = "road_link"
GEOMETRY, CLASS, STRUCTURE, FICTITIOUS, LENGTH = (
    "geometry",
    "road_classification",
    "road_structure",
    "fictitious",
    "length",
)
COLUMNS = (GEOMETRY, CLASS, STRUCTURE, FICTITIOUS, LENGTH)
# How the file classes a road. The first two are the main roads.
MAIN: tuple[str, ...] = ("Motorway", "A Road")
CLASSES: tuple[str, ...] = (
    *MAIN,
    "B Road",
    "Classified Unnumbered",
    "Unclassified",
    "Not Classified",
    "Unknown",
)
IN_TUNNEL = "Road In Tunnel"
LINES = "LINESTRING"
# The kind of geometry a line is, in well-known binary.
LINE = 2
# The extension a GeoPackage names where a layer has an index of where each row lies.
INDEXED_BY = "gpkg_rtree_index"
INDEX = f"rtree_{LAYER}_{GEOMETRY}"
# A home is near a main road within this many metres of its line.
METRES = 100
# The file holds a network under the homes of a build where all but a few centres are
# within this many metres of some road of any class (pipeline design, section 3, step 6).
REACH, UNREACHED_IN_100 = 250, 1
# The lines as drawn add up to what the file says they do, to within this share.
LENGTH_GATE = 0.005
# What the rows of the file are keyed by, as the parser finds them.
KEYED_BY = Geography.LINE
DECIMALS = 1
DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

METHOD = homes_within_at(METRES)
METHODS: tuple[Method, ...] = (METHOD,)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The share of the area's homes that are within {metres} metres of a motorway or an A road, "
    "from {publisher}'s {product} of {edition}: each home is placed at the point the statistics "
    "office gives as the centre of its census output area, homes are counted as they stood at "
    "the census of 2021, the distance is in a straight line to the line the file draws along "
    "the road, a road in a tunnel is left out, and the figure is given to {decimals} decimal "
    "place with a half taken upward, so it counts homes by where their output area is centred "
    "and by the class of a road, and is not a measure of traffic, of noise or of any one home."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It places each home at the centre of its small census area and not at its front door, so "
    "a home that fronts a main road can be counted as away from it.",
    "It knows how a road is classed and not how busy it is: a quiet A road counts, and a busy "
    "road of a lower class does not.",
)

# The least easting and northing, then the greatest.
Box = tuple[float, float, float, float]
# A line as the file draws it: easting, northing, easting, northing, and so on.
Line = tuple[float, ...]


def is_the_network(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the roads as a GeoPackage."""
    return name.startswith(FILE_STARTS)


@dataclass(frozen=True)
class Link:
    """One stretch of road, as far as the measure reads it."""

    # Whether it is a motorway or an A road, and not in a tunnel.
    main: bool
    line: Line


@dataclass(frozen=True)
class Roads:
    """The roads of the publisher's file that lie round the homes of a build."""

    # The month the layer was last changed, which is the month of the receipt.
    edition: str
    # The box the file says its roads cover.
    covers: Box
    links: tuple[Link, ...]
    # How many rows the layer holds, for all of Great Britain.
    rows: int
    # How many of the roads that were read the file puts in each class.
    by_class: Mapping[str, int]
    # How many stretches of a main road were left out, as in a tunnel.
    in_tunnel: int
    # What the file says the roads that were read are long, and what their lines add up to.
    metres_stated: float
    metres_drawn: float
    # Whether the file's own index was used to find them.
    indexed: bool
    file_id: str


@dataclass(frozen=True)
class Exposure:
    """The measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    roads: Roads
    geography: Geography
    # The verdict of each output area that has one: whether it is near a main road.
    near: Mapping[str, bool]
    # How many centres are further than the reach from any road of any class.
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


def line_of(blob: bytes) -> Line:
    """The line a GeoPackage holds in one cell, as its points on the National Grid.

    It raises `ValueError` for anything but a line of two points or more, in
    two dimensions, on the National Grid, with every point a number.
    """
    if len(blob) < HEADER or blob[:2] != MAGIC:
        raise ValueError("not a geometry of a GeoPackage")
    flags = blob[3]
    box = BOX.get((flags >> 1) & 7)
    if box is None or flags & 0b00110000:
        # A line that is empty, or of a kind the standard leaves to an extension.
        raise ValueError("a geometry of a kind that is not read")
    if struct.unpack_from("<i" if flags & 1 else ">i", blob, 4)[0] != NATIONAL_GRID:
        raise ValueError("a line that is not in the National Grid")
    at = HEADER + box
    if len(blob) < at + 9 or blob[at] not in (0, 1):
        raise ValueError("a line that is cut short")
    order = "<" if blob[at] else ">"
    kind, count = struct.unpack_from(f"{order}II", blob, at + 1)
    if kind != LINE or count < 2 or len(blob) != at + 9 + 16 * count:
        raise ValueError("not a line in two dimensions")
    line: Line = struct.unpack_from(f"{order}{2 * count}d", blob, at + 9)
    if not all(math.isfinite(part) for part in line):
        raise ValueError("a point is no point")
    return line


def box_of(line: Line) -> Box:
    """The box a line fits in."""
    east, north = line[0::2], line[1::2]
    return min(east), min(north), max(east), max(north)


def metres_of(line: Line) -> float:
    """How long a line is as drawn, in metres."""
    return math.fsum(
        math.sqrt((line[at + 2] - line[at]) ** 2 + (line[at + 3] - line[at + 1]) ** 2)
        for at in range(0, len(line) - 2, 2)
    )


def _meet(a: Box, b: Box) -> bool:
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _layer(database: sqlite3.Connection, opened: Opened) -> tuple[str, Box]:
    """The month the layer was last changed and the box it covers, once it is seen to be roads."""
    file_id = opened.file_id
    stated = database.execute(
        "SELECT data_type, srs_id, last_change, min_x, min_y, max_x, max_y "
        "FROM gpkg_contents WHERE table_name = ?",
        (LAYER,),
    ).fetchone()
    if stated is None or tuple(stated[:2]) != ("features", NATIONAL_GRID):
        raise _refused(file_id, "it holds no layer of roads on the National Grid")
    drawn = database.execute(
        "SELECT column_name, geometry_type_name, srs_id, z, m "
        "FROM gpkg_geometry_columns WHERE table_name = ?",
        (LAYER,),
    ).fetchone()
    if drawn is None or tuple(drawn) != (GEOMETRY, LINES, NATIONAL_GRID, 0, 0):
        raise _refused(file_id, "its roads are not lines in two dimensions")
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
    """Whether the file names an index of its roads, and this SQLite can read one."""
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
        raise _refused(file_id, "a road has no line")
    try:
        return line_of(blob)
    except (ValueError, struct.error):
        raise _refused(file_id, "a road is not a line in two dimensions") from None


def _classed(row: Sequence[object], file_id: str) -> tuple[str, bool, float]:
    """One row as its class, whether it is in a tunnel, and the length the file states."""
    kind, structure, fictitious, length = row
    if not isinstance(kind, str) or kind not in CLASSES:
        raise _refused(file_id, "a road is of a class that is not known")
    if structure is not None and structure != IN_TUNNEL:
        raise _refused(file_id, "a road is of a structure that is not known")
    if fictitious not in (0, 1):
        raise _refused(file_id, "a road is neither there nor not there")
    if fictitious:
        raise _refused(file_id, "a road is marked as fictitious")
    if not isinstance(length, int | float) or not math.isfinite(length) or length < 0:
        raise _refused(file_id, "a length is no length")
    return kind, structure == IN_TUNNEL, float(length)


def _read(database: sqlite3.Connection, opened: Opened, around: Box) -> Roads:
    file_id = opened.file_id
    edition, covers = _layer(database, opened)
    rows, without = database.execute(_COUNT).fetchone()
    if not rows:
        raise _refused(file_id, "it holds no road")
    if without:
        raise _refused(file_id, "a road has no line")
    indexed = _has_an_index(database)
    if indexed and database.execute(_COUNT_OF_THE_INDEX).fetchone()[0] != rows:
        raise _refused(file_id, "its index does not hold every road")
    west, south, east, north = around
    found = (
        database.execute(_BY_THE_INDEX, (west, east, south, north))
        if indexed
        else database.execute(_EVERY_ROW)
    )
    links: list[Link] = []
    by_class = dict.fromkeys(CLASSES, 0)
    in_tunnel = 0
    stated: list[float] = []
    drawn: list[float] = []
    for row in found:
        line = _drawn(row[0], file_id)
        # The index holds a box a little wider than the line. The line itself decides, so
        # that the same roads are kept with an index and without one.
        if not _meet(box_of(line), around):
            continue
        kind, tunnel, length = _classed(row[1:], file_id)
        by_class[kind] += 1
        in_tunnel += kind in MAIN and tunnel
        stated.append(length)
        drawn.append(metres_of(line))
        links.append(Link(main=kind in MAIN and not tunnel, line=line))
    metres_stated, metres_drawn = math.fsum(stated), math.fsum(drawn)
    if abs(metres_drawn - metres_stated) > LENGTH_GATE * metres_stated:
        raise _refused(file_id, "its lines are not as long as it says")
    # In a fixed order, whatever order the file gave them in.
    links.sort(key=lambda link: (link.line, link.main))
    return Roads(
        edition=edition,
        covers=covers,
        links=tuple(links),
        rows=int(rows),
        by_class=by_class,
        in_tunnel=in_tunnel,
        metres_stated=metres_stated,
        metres_drawn=metres_drawn,
        indexed=indexed,
        file_id=file_id,
    )


def read(opened: Opened, around: Box) -> Roads:
    """The roads of the file whose line comes inside a box, each with its class.

    `around` is the box the homes of the build stand in, widened by as far as
    a road is looked for. A road outside London counts where it is near a
    home inside it.
    """
    with _unpacked(opened) as path:
        try:
            database = read_only(path)
            try:
                return _read(database, opened, around)
            finally:
                database.close()
        except (sqlite3.Error, OSError):
            raise _refused(opened.file_id, "its roads could not be read") from None


def _cells(box: Box, side: float) -> Iterator[tuple[int, int]]:
    for column in range(math.floor(box[0] / side), math.floor(box[2] / side) + 1):
        for row in range(math.floor(box[1] / side), math.floor(box[3] / side) + 1):
            yield column, row


def _within(point: Point, line: Line, square: float) -> bool:
    """Whether a point is within a distance of a line. `square` is the distance, squared.

    Only sums, products and one division are taken, so that the same points
    give the same answer on every machine.
    """
    x, y = point
    for at in range(0, len(line) - 2, 2):
        x0, y0, x1, y1 = line[at : at + 4]
        along_x, along_y = x1 - x0, y1 - y0
        along = (x - x0) * along_x + (y - y0) * along_y
        whole = along_x * along_x + along_y * along_y
        if along <= 0 or whole == 0:
            nearest_x, nearest_y = x0, y0
        elif along >= whole:
            nearest_x, nearest_y = x1, y1
        else:
            nearest_x, nearest_y = x0 + along / whole * along_x, y0 + along / whole * along_y
        if (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= square:
            return True
    return False


def near(points: Mapping[str, Point], lines: Iterable[Line], metres: float) -> frozenset[str]:
    """The points that are within a distance of any of the lines, in a straight line.

    A point at the distance exactly is within it. The answer does not turn on
    the order of the points or of the lines.
    """
    waiting: dict[tuple[int, int], list[str]] = {}
    for name in sorted(points):
        x, y = points[name]
        waiting.setdefault((math.floor(x / metres), math.floor(y / metres)), []).append(name)
    found: set[str] = set()
    square = metres * metres
    for line in lines:
        west, south, east, north = box_of(line)
        for cell in _cells((west - metres, south - metres, east + metres, north + metres), metres):
            names = waiting.get(cell)
            if not names:
                continue
            close = [name for name in names if _within(points[name], line, square)]
            if close:
                found.update(close)
                waiting[cell] = [name for name in names if name not in found]
    return frozenset(found)


def verdicts(roads: Roads, points: Mapping[str, Point]) -> tuple[dict[str, bool], int]:
    """Whether each output area is near a main road, and how many are far from every road.

    An output area has a verdict where it has a centre and the centre is
    inside the box the file says its roads cover. It stops where the file
    holds no network under the homes of the build.
    """
    west, south, east, north = roads.covers
    covered = {
        oa: point
        for oa, point in points.items()
        if west <= point[0] <= east and south <= point[1] <= north
    }
    reached = near(covered, (link.line for link in roads.links), REACH)
    unreached = len(covered) - len(reached)
    if unreached * 100 > UNREACHED_IN_100 * len(covered):
        raise _refused(roads.file_id, "its roads do not reach the homes of the build")
    beside = near(covered, (link.line for link in roads.links if link.main), METRES)
    return {oa: oa in beside for oa in sorted(covered)}, unreached


def figures(beside: Mapping[str, bool], found: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, or why an area has none."""
    worked = homes_within(beside, found.weights, times=100)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def metric_of(files: Sequence[Receipt], edition: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the name, the unit and which way is better. The period is
    the month of the edition, which the file's own date is held to.
    """
    return catalogue_row(
        FEATURE,
        method=METHOD,
        source_ids={receipt.source_id for receipt in files},
        vintage=edition,
        rankable=RANKABLE,
        definition=DEFINITION.format(
            metres=METRES,
            publisher=PUBLISHER,
            product=PRODUCT,
            edition=edition,
            decimals=DECIMALS,
        ),
    )


def around_of(points: Collection[Point]) -> Box:
    """The box some centres stand in, widened by as far as a road is looked for."""
    if not points:
        raise ValueError("a build has homes")
    east, north = [point[0] for point in points], [point[1] for point in points]
    reach = max(METRES, REACH)
    return min(east) - reach, min(north) - reach, max(east) + reach, max(north) + reach


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Exposure:
    """The figure of every area and its evidence, from the files of the build.

    The gate is asked about the roads and about the centres before either is
    read. `found` is the spine of the same build: a row of evidence names its
    files beside the roads and the centres, so they must be files this build
    opened. `edition` is the month of the release, as the receipt gives it.
    It tells apart the files of two releases, once the store holds both.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=edition, named=is_the_network)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    points = centres.centres_of(placed, found)
    if not points:
        raise _refused(placed.file_id, "it holds no centre of the build")
    roads = read(opened, around_of(points.values()))
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted({opened.file_id, placed.file_id, *found.inputs})
    if not all(file_id in handed for file_id in behind):
        raise ValueError("the spine is made from files of this build")
    files = tuple(handed[file_id] for file_id in behind)
    beside, unreached = verdicts(roads, points)
    worked = figures(beside, found)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, KEY), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    return Exposure(
        worked=worked,
        rows=rows,
        metric=metric_of(files, roads.edition),
        files=files,
        roads=roads,
        geography=KEYED_BY,
        near=beside,
        unreached=unreached,
    )
