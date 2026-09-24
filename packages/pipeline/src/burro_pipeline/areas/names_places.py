"""The names of places, as Ordnance Survey writes them in OS Open Names.

The file is a zip of tables, one for each square of the National Grid. No
table has a header: the names of the columns are the one row of a document
inside the zip. A row is read by the names of its columns and never by their
order, and a table whose rows are not as long as the header stops the step.

Three kinds of record are read, and no other:

- A populated place: a name with a point and a box. It is a candidate name.
- A road: only the settlement it names is read, to count how many roads give
  each place as their settlement. A road is joined to its settlement by the
  settlement's address, never by its name: two places may share a name.
- A railway station: a name with a point. It is no candidate. It is read so
  that a name that is also a station can be put to a person.

A postcode is never read: the registry asks that it is dropped, because a
postcode carries rights of its own. A name is kept exactly as the file writes
it. Nothing is trimmed, respelt or put in another case.
"""

import csv
import io
import zipfile
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.areas.names_files import File
from burro_pipeline.evidence.lock import LockError

SOURCE = "os-open-names"
HEADER = "Doc/OS_Open_Names_Header.csv"
TABLES = "Data/"
# The columns that are read, by the names the header gives them.
ID, URI, NAME, SECOND_NAME = "ID", "NAMES_URI", "NAME1", "NAME2"
TYPE, KIND = "TYPE", "LOCAL_TYPE"
X, Y = "GEOMETRY_X", "GEOMETRY_Y"
BOX = ("MBR_XMIN", "MBR_YMIN", "MBR_XMAX", "MBR_YMAX")
SETTLEMENT = "POPULATED_PLACE_URI"
READ = (ID, URI, NAME, SECOND_NAME, TYPE, KIND, X, Y, *BOX, SETTLEMENT)

PLACE, TRANSPORT = "populatedPlace", "transportNetwork"
STATION, POSTCODE = "Railway Station", "Postcode"
ROADS = frozenset(
    {"Named Road", "Section Of Named Road", "Numbered Road", "Section Of Numbered Road"}
)
# The kinds of populated place, as the file writes them.
CITY = "City"

Box = tuple[float, float, float, float]


@dataclass(frozen=True, order=True)
class Record:
    """One record of the file: a populated place, or a railway station."""

    record_id: str
    # The record's own address, which a road gives as its settlement.
    uri: str
    name: str
    # A second name, where the file gives one. Empty for nearly every record.
    second_name: str
    # The kind, as the file writes it: `Suburban Area`, `Village`, `Railway Station`.
    kind: str
    x: float
    y: float
    # The box round the thing named: west, south, east, north. None where the file gives none.
    box: Box | None

    @property
    def at(self) -> tuple[float, float]:
        return self.x, self.y

    @property
    def hectares(self) -> float | None:
        """What the box encloses, in hectares."""
        if self.box is None:
            return None
        return (self.box[2] - self.box[0]) * (self.box[3] - self.box[1]) / 10_000


@dataclass(frozen=True)
class Names:
    """What was read from the file, for the ground that was asked about."""

    places: tuple[Record, ...]
    stations: tuple[Record, ...]
    # How many road records give each populated place as their settlement, by its address.
    # It is counted over the whole file, so a road just outside the ground counts too.
    roads: Mapping[str, int]
    tables: int
    rows: int


def _number(text: str, file_id: str) -> float:
    try:
        return float(text)
    except ValueError:
        raise LockError("input_is_as_described", file_id, "a coordinate is not a number") from None


def _record(row: Mapping[str, str], file_id: str) -> Record:
    corners = [row[name] for name in BOX]
    box = None
    if all(corners):
        west, south, east, north = (_number(corner, file_id) for corner in corners)
        box = (west, south, east, north)
    if not (row[ID] and row[NAME]):
        raise LockError("input_is_as_described", file_id, "a record has no id or no name")
    return Record(
        record_id=row[ID],
        uri=row[URI],
        name=row[NAME],
        second_name=row[SECOND_NAME],
        kind=row[KIND],
        x=_number(row[X], file_id),
        y=_number(row[Y], file_id),
        box=box,
    )


def _rows(archive: zipfile.ZipFile, member: str) -> Iterator[list[str]]:
    with archive.open(member) as raw:
        yield from csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))


def _columns(archive: zipfile.ZipFile, file_id: str) -> dict[str, int]:
    """Where each column that is read stands in a row, from the header the zip holds."""
    found = [name for name in archive.namelist() if name.endswith(HEADER)]
    if len(found) != 1:
        raise LockError("input_is_as_described", file_id, "it holds no header")
    header = list(_rows(archive, found[0]))
    if len(header) != 1 or not set(READ) <= set(header[0]):
        raise LockError("input_is_as_described", file_id, "a column is missing")
    return {name: header[0].index(name) for name in header[0]}


def _inside(record: Record, ground: Box) -> bool:
    return ground[0] <= record.x <= ground[2] and ground[1] <= record.y <= ground[3]


def read(file: File, ground: Box) -> Names:
    """The places and stations whose point lies in a box, and the roads of every place.

    The box is a first cut, and only that: whoever calls this tests each
    record against the ground itself. Every table is read, because a table
    is not quite the square of its name.
    """
    places: list[Record] = []
    stations: list[Record] = []
    roads: dict[str, int] = {}
    tables = rows = 0
    try:
        with zipfile.ZipFile(file.path) as archive:
            at = _columns(archive, file.file_id)
            width, kind, local = len(at), at[TYPE], at[KIND]
            settlement = at[SETTLEMENT]
            members: Sequence[str] = sorted(
                name
                for name in archive.namelist()
                if TABLES in name and name.lower().endswith(".csv")
            )
            for member in members:
                tables += 1
                for row in _rows(archive, member):
                    rows += 1
                    if len(row) != width:
                        raise LockError(
                            "input_is_as_described", file.file_id, "a row is not as the header"
                        )
                    if row[local] == POSTCODE:
                        continue
                    if row[kind] == TRANSPORT and row[local] in ROADS:
                        if row[settlement]:
                            roads[row[settlement]] = roads.get(row[settlement], 0) + 1
                        continue
                    is_place = row[kind] == PLACE
                    if not (is_place or row[local] == STATION):
                        continue
                    record = _record({name: row[at[name]] for name in READ}, file.file_id)
                    if _inside(record, ground):
                        (places if is_place else stations).append(record)
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError, csv.Error):
        raise LockError("input_is_as_described", file.file_id, "it could not be read") from None
    if not tables:
        raise LockError("input_is_as_described", file.file_id, "it holds no table")
    return Names(
        places=tuple(sorted(places)),
        stations=tuple(sorted(stations)),
        roads=dict(sorted(roads.items())),
        tables=tables,
        rows=rows,
    )
