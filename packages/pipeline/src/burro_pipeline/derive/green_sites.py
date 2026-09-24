"""OS Open Greenspace: the sites and the ways into them, as the publisher's files give them.

Ordnance Survey publishes the product for Great Britain, cut into the squares
of the National Grid that are 100 kilometres wide. A file is a zip named for
its square, `opgrsp_gml3_tq.zip`, and holds one document of GML beside a
licence and a note on the folders. London lies on two squares.

What a file holds:

| Feature | What it is | What is read of it |
|---|---|---|
| `GreenspaceSite` | One site, with its outline | Its id, its kind and its outline |
| `AccessPoint` | One way into a site, a point on its edge | Its site, who it is for, its place |

A site is of one of ten kinds, which the publisher calls its function. The
file names the kinds and defines none of them. A site may have a name or two.
No name is read: a figure needs none, and the registry asks for another use
before a name is shown.

How a missing value is written. An element that does not apply is left out:
most sites have no name. No element that is read was found empty. A site with
no kind or no outline, and a way in with no site, no kind or no point, stops
the step.

What a file is held to, because a figure rests on it:

- **Its square.** The name of a file gives two letters, and the National
  Grid's own lettering gives the square they stand for. Every way in must lie
  on that square, and every site must touch it. So a file that holds no way in
  near a home is known to hold none, and a home near a square that was not read
  is known not to be covered.
- **Its grid.** Every outline and every point says it is on the National Grid.
- **Its year.** The document says whose it is and of which year, and the year
  must be the year of the receipt.
- **Its kinds.** A kind that is not one of the ten stops the step. A person
  then decides whether it counts as a park.

A site that lies across the line between two squares is in both files, drawn
the same way. It is kept once. A way in is in one file alone.

Nothing here decides what counts as a park, and nothing here is a figure.
"""

import hashlib
import math
import re
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from burro_pipeline.cells.shapes import Point, Shape, box_of, hectares, outline_of
from burro_pipeline.derive.methods import cell_of
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.fetch.markup import Limited, MarkupError
from burro_pipeline.fetch.markup import read as walk
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "os-open-greenspace"
PUBLISHER = "Ordnance Survey"
# The publisher names a file for the product, the format and the square: `opgrsp_gml3_tq.zip`.
FILE = re.compile(r"opgrsp_gml3_(?P<square>[a-z]{2})\.zip")
# The one document inside the zip, named for the same square in capitals.
DOCUMENT = "/data/OSOpenGreenspace_{square}.gml"
# How much of a document is read once unpacked. The largest read so far unpacks to 54 MB.
DOCUMENT_LIMIT = 1024 * 1024 * 1024
# The National Grid names its squares by two letters. `I` is not used.
LETTERS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
# The width of a square that a file is cut to, in metres.
SQUARE = 100_000
# What every outline and every point must say of its coordinates.
NATIONAL_GRID = "urn:ogc:def:crs:EPSG::27700"

# The elements that are read, by the last part of their names.
COLLECTION, MEMBER, SAID = "FeatureCollection", "featureMember", "description"
SITE, WAY_IN = "GreenspaceSite", "AccessPoint"
KIND, ACCESS, OF_SITE = "function", "accessType", "refToGreenspaceSite"
OUTLINE, PIECE, OUTER, HOLE, POINTS = (
    "MultiSurface",
    "PolygonPatch",
    "exterior",
    "interior",
    "posList",
)
PLACE, AT = "Point", "pos"
IDENTITY, GRID_NAMED = "id", "srsName"
# The text of these is kept while a document is walked, and the text of no other.
KEPT = frozenset({SAID, KIND, ACCESS, OF_SITE, POINTS, AT})

# The ten kinds of site, as the publisher writes them.
PARK = "Public Park Or Garden"
KINDS = (
    "Allotments Or Community Growing Spaces",
    "Bowling Green",
    "Cemetery",
    "Golf Course",
    "Other Sports Facility",
    "Play Space",
    "Playing Field",
    PARK,
    "Religious Grounds",
    "Tennis Court",
)
# Who a way in is for, as the publisher writes it. The first two are for a person on foot.
ON_FOOT = ("Pedestrian", "Motor Vehicle And Pedestrian")
ACCESSES = (*ON_FOOT, "Motor Vehicle")

WHOSE = re.compile(r"Ordnance Survey Crown Copyright (?P<year>[0-9]{4})")
NUMBER = r"-?[0-9]+(?:\.[0-9]+)?"
A_RING = re.compile(rf"\s*{NUMBER}(?:\s+{NUMBER})*\s*")
A_POINT = re.compile(rf"\s*{NUMBER}\s+{NUMBER}\s*")
# A ring is closed, so the least is a triangle: three corners, and the first again.
LEAST_RING = 4

Corner = tuple[int, int]
Ring = tuple[Point, ...]


class _Refused(Exception):
    """The document is not as the step expects. It holds the fixed words that say how."""


@dataclass(frozen=True)
class Site:
    """One site, as the publisher draws it."""

    site_id: str
    # One of the ten kinds, as the publisher writes it.
    kind: str
    shape: Shape
    # What its outline encloses, in hectares. A hole in it is no part of it.
    hectares: float
    # A hash of its kind and of its outline as written, to tell whether two files agree.
    drawn: str


@dataclass(frozen=True)
class WayIn:
    """One way into a site, as the publisher marks it: a point on the edge of the site."""

    site_id: str
    # Who it is for, as the publisher writes it.
    access: str
    point: Point

    @property
    def on_foot(self) -> bool:
        return self.access in ON_FOOT


@dataclass(frozen=True)
class Tile:
    """What one file holds: the sites and the ways in of one square of the National Grid."""

    # The two letters of the square, in capitals, and the corner nearest the grid's origin.
    letters: str
    corner: Corner
    # The year the document says it is of.
    year: int
    sites: Mapping[str, Site]
    ways_in: tuple[WayIn, ...]
    file_id: str


@dataclass(frozen=True)
class Greenspace:
    """Every site and every way in of the files that were read, each once."""

    sites: Mapping[str, Site]
    ways_in: tuple[WayIn, ...]
    # The file of each square that was read, by the corner of the square.
    file_of: Mapping[Corner, str]
    # The receipt of each file, in the order of their ids.
    files: tuple[Receipt, ...]
    # How many sites were in more than one file, and so were kept once.
    in_two_files: int
    # The period the files are of, as their receipts give it. Every file gives the same.
    as_at: str

    def beyond(self, point: Point) -> float:
        """How far a point is from the nearest land that no file was read for, in metres.

        It is nought where the point stands on such land itself. A way in
        further from a home than this may not be the nearest: a nearer one may
        lie on a square that was not read.
        """
        own = cell_of(*point, SQUARE)
        if own not in self.file_of:
            return 0.0
        best, ring = math.inf, 0
        while ring * SQUARE < best:
            ring += 1
            for corner in _round(own, ring):
                if corner not in self.file_of:
                    best = min(best, _metres_to(corner, point))
        return best

    def files_within(self, point: Point, metres: float) -> tuple[str, ...]:
        """The files of the squares that lie within so many metres of a point."""
        return tuple(
            sorted(
                file_id
                for corner, file_id in self.file_of.items()
                if _metres_to(corner, point) <= metres
            )
        )

    def files_under(self, shape: Shape) -> tuple[str, ...] | None:
        """The files of the squares an outline lies on, or none if one of them was not read.

        An outline is taken to lie on every square that the box round it
        touches. That is never fewer squares than it lies on.
        """
        west, south, east, north = box_of(shape)
        low, high = cell_of(west, south, SQUARE), cell_of(east, north, SQUARE)
        under = [
            (across, up)
            for across in range(low[0], high[0] + SQUARE, SQUARE)
            for up in range(low[1], high[1] + SQUARE, SQUARE)
        ]
        if not all(corner in self.file_of for corner in under):
            return None
        return tuple(sorted(self.file_of[corner] for corner in under))


def _round(own: Corner, ring: int) -> list[Corner]:
    """The squares that stand so many squares from a square, in a ring round it."""
    reach = range(-ring, ring + 1)
    return [
        (own[0] + across * SQUARE, own[1] + up * SQUARE)
        for across in reach
        for up in reach
        if max(abs(across), abs(up)) == ring
    ]


def _metres_to(corner: Corner, point: Point) -> float:
    """How far a point is from a square. Nought where it stands on the square."""
    across = max(corner[0] - point[0], 0.0, point[0] - (corner[0] + SQUARE))
    up = max(corner[1] - point[1], 0.0, point[1] - (corner[1] + SQUARE))
    return math.hypot(across, up)


def is_a_tile(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a square of the product."""
    return FILE.fullmatch(name) is not None


def corner_of(letters: str) -> Corner:
    """The corner of the square two letters of the National Grid stand for, in metres.

    The first letter names a square 500 kilometres wide and the second a
    square 100 kilometres wide inside it. Each runs through the alphabet
    without `I`, five to a row, from the north-west. The squares of 500
    kilometres are lettered from a point two such squares west and one south
    of the grid's origin.
    """
    if len(letters) != 2 or any(letter not in LETTERS for letter in letters):
        raise ValueError("a square is named by two letters of the grid")
    first, second = LETTERS.index(letters[0]), LETTERS.index(letters[1])
    across = ((first - 2) % 5) * 5 + second % 5
    up = 19 - (first // 5) * 5 - second // 5
    return across * SQUARE, up * SQUARE


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _ring(text: str) -> Ring:
    if A_RING.fullmatch(text) is None:
        raise _Refused("an outline is not a list of points")
    numbers = [float(number) for number in text.split()]
    if len(numbers) % 2 or len(numbers) < 2 * LEAST_RING:
        raise _Refused("an outline is not a list of points")
    ring = tuple(zip(numbers[0::2], numbers[1::2], strict=True))
    if ring[0] != ring[-1]:
        raise _Refused("an outline is not closed")
    return ring


@dataclass
class _Walk:
    """Walks one document, and keeps what is read of each site and of each way in."""

    corner: Corner
    sites: dict[str, Site] = field(default_factory=dict[str, Site])
    ways_in: list[WayIn] = field(default_factory=list[WayIn])
    said: str | None = None
    _path: list[str] = field(default_factory=list[str])
    _text: list[str] | None = None
    _id: str = ""
    _held: dict[str, str] = field(default_factory=dict[str, str])
    _pieces: list[list[Ring]] = field(default_factory=list[list[Ring]])
    _written: list[str] = field(default_factory=list[str])
    _on_the_grid: bool = False

    def start(self, name: str, given: dict[str, str]) -> None:
        depth = len(self._path)
        self._path.append(name)
        if depth == 0 and name != COLLECTION:
            raise _Refused("it is not a collection of features")
        if depth == 2 and self._path[1] == MEMBER:
            if name not in (SITE, WAY_IN):
                raise _Refused("it holds a feature that is neither a site nor a way in")
            self._id = given.get(IDENTITY, "")
            self._held, self._pieces, self._written = {}, [], []
            self._on_the_grid = False
        elif name in (OUTLINE, PLACE) and self._feature is not None:
            if given.get(GRID_NAMED) != NATIONAL_GRID:
                raise _Refused("it is not in the National Grid")
            self._on_the_grid = True
        elif name == PIECE and self._feature == SITE:
            self._pieces.append([])
        self._text = [] if name in KEPT and self._wanted(name) else None

    def text(self, piece: str) -> None:
        if self._text is not None:
            self._text.append(piece)

    def end(self, name: str) -> None:
        kept, self._text = self._text, None
        if kept is not None:
            self._keep(name, "".join(kept))
        if len(self._path) == 3 and self._path[1] == MEMBER:
            if name == SITE:
                self._site()
            else:
                self._way_in()
        self._path.pop()

    @property
    def _feature(self) -> str | None:
        """The feature the walk is inside, if it is inside one."""
        inside = len(self._path) >= 3 and self._path[1] == MEMBER
        return self._path[2] if inside else None

    def _wanted(self, name: str) -> bool:
        if name == SAID:
            return len(self._path) == 2
        return self._feature is not None

    def _keep(self, name: str, text: str) -> None:
        if name == SAID:
            self.said = text.strip()
        elif name == POINTS:
            self._ring_of(text)
        else:
            self._held[name] = text.strip()

    def _ring_of(self, text: str) -> None:
        if self._feature != SITE or not self._pieces or len(self._path) < 3:
            raise _Refused("an outline is not laid out in pieces")
        side = self._path[-3]
        if side not in (OUTER, HOLE) or (side == HOLE) != bool(self._pieces[-1]):
            raise _Refused("an outline is not laid out in pieces")
        self._pieces[-1].append(_ring(text))
        self._written.append(" ".join(text.split()))

    def _missing(self, *names: str) -> None:
        for name in names:
            if not self._held.get(name):
                # The name is the one this step asks for. Nothing of the file is repeated.
                raise _Refused(f"the element {name} is missing")

    def _site(self) -> None:
        self._missing(KIND)
        if not self._id:
            raise _Refused("a site has no id")
        if not self._pieces or not all(self._pieces):
            raise _Refused(f"the element {POINTS} is missing")
        if not self._on_the_grid:
            raise _Refused("it is not in the National Grid")
        kind = self._held[KIND]
        if kind not in KINDS:
            raise _Refused("a site is of a kind that is not one of the ten")
        if self._id in self.sites:
            raise _Refused("a site is there twice")
        try:
            shape = outline_of(self._pieces)
        except ValueError:
            raise _Refused("a site is not a shape") from None
        if not _touches(box_of(shape), self.corner):
            raise _Refused("a site is not on the square the file is named for")
        drawn = hashlib.sha256("|".join([kind, *self._written]).encode()).hexdigest()
        self.sites[self._id] = Site(self._id, kind, shape, hectares(shape), drawn)

    def _way_in(self) -> None:
        self._missing(ACCESS, OF_SITE, AT)
        if not self._on_the_grid:
            raise _Refused("it is not in the National Grid")
        if self._held[ACCESS] not in ACCESSES:
            raise _Refused("a way in is for somebody the step does not know")
        if A_POINT.fullmatch(self._held[AT]) is None:
            raise _Refused("a way in is at no point")
        east, north = (float(number) for number in self._held[AT].split())
        if cell_of(east, north, SQUARE) != self.corner:
            raise _Refused("a way in is not on the square the file is named for")
        self.ways_in.append(WayIn(self._held[OF_SITE], self._held[ACCESS], (east, north)))


def _touches(box: tuple[float, float, float, float], corner: Corner) -> bool:
    """Whether the box round an outline touches a square."""
    west, south, east, north = box
    return (
        west <= corner[0] + SQUARE
        and east >= corner[0]
        and south <= corner[1] + SQUARE
        and north >= corner[1]
    )


def read(opened: Opened) -> Tile:
    """The sites and the ways in of one file, held to its square, its grid and its year.

    It stops at a file that is not named for a square, at a document that is
    not laid out as the step expects, and at the first element it needs and
    does not find, which it names.
    """
    named = FILE.fullmatch(opened.receipt.publisher_file)
    if named is None:
        raise _refused(opened, "it is not named for a square of the grid")
    letters = named["square"].upper()
    try:
        corner = corner_of(letters)
    except ValueError:
        raise _refused(opened, "it is not named for a square of the grid") from None
    document = opened.member(DOCUMENT.format(square=letters))
    walked = _Walk(corner)
    over = _Refused("the document is larger than any that was read before")
    try:
        with zipfile.ZipFile(opened.path) as archive, archive.open(document) as raw:
            walk(Limited(raw, DOCUMENT_LIMIT, over), walked.start, walked.end, walked.text)
    except _Refused as stopped:
        raise _refused(opened, str(stopped)) from None
    except (MarkupError, zipfile.BadZipFile, OSError, ValueError):
        raise _refused(opened, "it could not be read as GML") from None
    if not walked.sites:
        raise _refused(opened, "it holds no site")
    if any(way.site_id not in walked.sites for way in walked.ways_in):
        raise _refused(opened, "a way in is to no site of the file")
    whose = WHOSE.fullmatch(walked.said or "")
    if whose is None:
        raise _refused(opened, "it does not say whose it is and of which year")
    year = int(whose["year"])
    if opened.receipt.data_period.days()[0][:4] != f"{year:04d}":
        raise _refused(opened, "the year it states is not the year of its receipt")
    return Tile(
        letters=letters,
        corner=corner,
        year=year,
        sites=walked.sites,
        ways_in=tuple(sorted(walked.ways_in, key=lambda way: (way.point, way.site_id))),
        file_id=opened.file_id,
    )


def joined(tiles: Sequence[Tile], files: Sequence[Receipt]) -> Greenspace:
    """The sites and the ways in of several files as one, with a site of two files kept once.

    It stops where two files are of one square, where two files draw one site
    differently, and where the files are not all of one period.
    """
    if not tiles:
        raise ValueError("at least one file is read")
    receipt_of = {receipt.file_id: receipt for receipt in files}
    sites: dict[str, Site] = {}
    file_of: dict[Corner, str] = {}
    in_two = 0
    for tile in sorted(tiles, key=lambda tile: tile.file_id):
        if tile.corner in file_of:
            raise LockError("input_has_one_receipt", SOURCE)
        file_of[tile.corner] = tile.file_id
        for site_id in sorted(tile.sites):
            site = tile.sites[site_id]
            if site_id not in sites:
                sites[site_id] = site
            elif sites[site_id].drawn == site.drawn:
                in_two += 1
            else:
                raise LockError(
                    "input_is_as_described", tile.file_id, "two files draw one site differently"
                )
    periods = {receipt_of[tile.file_id].data_period.days() for tile in tiles}
    if len(periods) != 1:
        raise LockError("input_is_as_described", SOURCE, "its files are not of one period")
    ways_in = sorted(
        (way for tile in tiles for way in tile.ways_in),
        key=lambda way: (way.point, way.site_id),
    )
    first = receipt_of[min(file_of.values())].data_period
    return Greenspace(
        sites=sites,
        ways_in=tuple(ways_in),
        file_of=file_of,
        files=tuple(receipt_of[file_id] for file_id in sorted(file_of.values())),
        in_two_files=in_two,
        as_at=first.as_at or f"{first.start} to {first.end}",
    )


def build(inputs: Inputs, *, edition: str | None = None) -> Greenspace:
    """Every site and way in of every square the build has a file of, from the files of the build.

    The gate is asked about each file before it is read. `edition` tells apart
    the files of two editions, once the store holds both.
    """
    names = sorted(
        receipt.publisher_file
        for receipt in inputs.receipts
        if receipt.source_id == SOURCE
        and is_a_tile(receipt.publisher_file)
        and (edition is None or receipt.edition == edition)
    )
    if not names:
        raise LockError("input_has_one_receipt", SOURCE)
    opened = [
        inputs.open(SOURCE, Use.SCORING, edition=edition, named=lambda name, one=one: name == one)
        for one in dict.fromkeys(names)
    ]
    return joined([read(one) for one in opened], [one.receipt for one in opened])
