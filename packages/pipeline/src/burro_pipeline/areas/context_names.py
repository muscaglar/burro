"""The names a reviewer finds their way by, from OS Open Names: places, stations, water, woods.

The design draws place names from OS Open Names behind a border. It also wants
stations, parks and rivers, from three sources the licence gate does not give
for the use `gazetteer`. OS Open Names is given for it, and holds a name and a
point for railway stations, for water and for woods and green spaces. So these
stand in, as names at points. No outline is drawn from them: the file gives a
box round each thing, and a box is no outline.

The file is a zip of tables with no header. The names of the columns are the
one row of a document inside the zip, and a row is read by the names of its
columns. Four kinds of record are read and no other: a populated place, a
railway station, water, and land cover. A postcode is never read: the registry
asks that it is dropped. A road is not read here: the layer of roads names it.

A place is drawn as the file writes it, whatever the draft makes of its name.
A name is kept exactly as the file writes it.
"""

import csv
import io
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.areas.assign_shapes import Box
from burro_pipeline.evidence.lock import LockError

SOURCE = "os-open-names"
HEADER = "Doc/OS_Open_Names_Header.csv"
TABLES = "Data/"
ID, NAME, TYPE, KIND, X, Y = "ID", "NAME1", "TYPE", "LOCAL_TYPE", "GEOMETRY_X", "GEOMETRY_Y"
READ = (ID, NAME, TYPE, KIND, X, Y)
# What is read: every record of three of the file's types, and one kind of a fourth.
PLACE, WATER, LAND_COVER, TRANSPORT = (
    "populatedPlace",
    "hydrography",
    "landcover",
    "transportNetwork",
)
STATION, POSTCODE = "Railway Station", "Postcode"


@dataclass(frozen=True, order=True)
class Named:
    """One name at one point: a place, a station, a water or a wood."""

    record_id: str
    name: str
    # The kind, as the file writes it: `Railway Station`, `Inland Water`, `Woodland Or Forest`.
    kind: str
    x: float
    y: float


def _rows(archive: zipfile.ZipFile, member: str) -> Iterator[list[str]]:
    with archive.open(member) as raw:
        yield from csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))


def _wanted(of_type: str, kind: str) -> bool:
    return kind != POSTCODE and (
        of_type in (PLACE, WATER, LAND_COVER) or (of_type == TRANSPORT and kind == STATION)
    )


def read(path: Path, file_id: str, ground: Box) -> tuple[Named, ...]:
    """Every place, station, water and wood whose point lies in a box, in the order of their ids.

    Every table is read, because a table is not quite the square of its name.
    It stops where a row is not as long as the header, or a record that is
    wanted has no id, no name or no point.
    """
    west, south, east, north = ground
    found: list[Named] = []
    try:
        with zipfile.ZipFile(path) as archive:
            headers = [name for name in archive.namelist() if name.endswith(HEADER)]
            header = list(_rows(archive, headers[0])) if len(headers) == 1 else []
            if len(header) != 1 or not set(READ) <= set(header[0]):
                raise LockError("input_is_as_described", file_id, "a column is missing")
            at = {name: header[0].index(name) for name in READ}
            tables = sorted(
                name
                for name in archive.namelist()
                if TABLES in name and name.lower().endswith(".csv")
            )
            if not tables:
                raise LockError("input_is_as_described", file_id, "it holds no table")
            for table in tables:
                for row in _rows(archive, table):
                    if len(row) != len(header[0]):
                        raise LockError(
                            "input_is_as_described", file_id, "a row is not as the header"
                        )
                    if not _wanted(row[at[TYPE]], row[at[KIND]]):
                        continue
                    x, y = float(row[at[X]]), float(row[at[Y]])
                    if not (row[at[ID]] and row[at[NAME]]):
                        raise LockError(
                            "input_is_as_described", file_id, "a record has no id or no name"
                        )
                    if west <= x <= east and south <= y <= north:
                        found.append(Named(row[at[ID]], row[at[NAME]], row[at[KIND]], x, y))
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError, csv.Error, ValueError):
        raise LockError("input_is_as_described", file_id, "it could not be read") from None
    if len({each.record_id for each in found}) != len(found):
        raise LockError("input_is_as_described", file_id, "an id is held twice")
    return tuple(sorted(found))
