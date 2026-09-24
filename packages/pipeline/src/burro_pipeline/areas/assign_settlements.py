"""The settlement that the roads of an output area name, from OS Open Names.

A record of a road in OS Open Names names the settlement the road is in. The
design cuts a distance by 15% where the roads of an output area name the seed's
own place (section 4, steps 5 and 6). So for each output area the settlement
that most of its road records name is found, and the seed that is that
settlement is favoured there.

A road is joined to its settlement by the settlement's address, never by its
name: two places may share a name. A seed is joined the same way, by the id of
the record it was read from. The address of a place ends in the digits of its
record's id.

The file is a zip of tables, and no table has a header: the names of the
columns are the one row of a document inside the zip. A row is read by the
names of its columns, and only a road is read. A postcode is never read. A
record is in an output area when its point lies in the full outline or on it,
and on a line between two it is in the one whose code sorts first.

An output area with no road record says nothing, and no distance is cut for it.
"""

import csv
import io
import math
import zipfile
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.areas.assign_shapes import Box, Outlines
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Opened

SOURCE = "os-open-names"
HEADER = "Doc/OS_Open_Names_Header.csv"
TABLES, TABLE_ENDS = "Data/", ".csv"
TYPE, KIND, X, Y = "TYPE", "LOCAL_TYPE", "GEOMETRY_X", "GEOMETRY_Y"
SETTLEMENT, SETTLEMENT_URI = "POPULATED_PLACE", "POPULATED_PLACE_URI"
READ = (TYPE, KIND, X, Y, SETTLEMENT, SETTLEMENT_URI)
TRANSPORT = "transportNetwork"
ROADS = frozenset(
    {"Named Road", "Section Of Named Road", "Numbered Road", "Section Of Numbered Road"}
)
# What stands before the digits in the id of a record of a place.
BEFORE_THE_DIGITS = "osgb"


@dataclass(frozen=True)
class Settlement:
    """The settlement most of the roads of an output area name."""

    # The last part of the settlement's address: the digits of its record's id.
    key: str
    # Its name, as the road records write it.
    name: str
    # How many road records of the output area name it, and how many name any.
    roads: int
    of: int


def key_of_address(address: str) -> str:
    """What joins a road to its settlement: the last part of the settlement's address."""
    return address.rstrip("/").rsplit("/", 1)[-1]


def key_of_record(record_id: str) -> str:
    """What joins a seed to its settlement: the digits of the id of its record."""
    return record_id.removeprefix(BEFORE_THE_DIGITS)


def _tables(opened: Opened) -> tuple[list[str], list[str]]:
    """The names of the columns, and the names of the tables, in order."""
    try:
        with zipfile.ZipFile(opened.path) as archive:
            names = archive.namelist()
            with archive.open(HEADER) as raw:
                header = next(csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")))
    except (zipfile.BadZipFile, OSError, KeyError, StopIteration, UnicodeDecodeError, csv.Error):
        raise LockError(
            "input_is_as_described", opened.file_id, "it holds no list of its columns"
        ) from None
    if not set(READ) <= set(header) or len(set(header)) != len(header):
        raise LockError("input_is_as_described", opened.file_id, "a column is missing")
    tables = sorted(name for name in names if name.startswith(TABLES) and name.endswith(TABLE_ENDS))
    if not tables:
        raise LockError("input_is_as_described", opened.file_id, "it holds no table")
    return header, tables


def roads_in(opened: Opened, box: Box) -> Iterator[tuple[tuple[float, float], str, str]]:
    """Every road record in a box that names a settlement: its point, the address, the name."""
    header, tables = _tables(opened)
    at = {name: header.index(name) for name in READ}
    try:
        with zipfile.ZipFile(opened.path) as archive:
            for table in tables:
                with archive.open(table) as raw:
                    text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                    for row in csv.reader(text):
                        if len(row) != len(header):
                            raise LockError(
                                "input_is_as_described", opened.file_id, "a row is short"
                            )
                        if row[at[TYPE]] != TRANSPORT or row[at[KIND]] not in ROADS:
                            continue
                        if not row[at[SETTLEMENT_URI]]:
                            continue
                        point = float(row[at[X]]), float(row[at[Y]])
                        if not all(math.isfinite(part) for part in point):
                            raise ValueError
                        if box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]:
                            yield point, row[at[SETTLEMENT_URI]], row[at[SETTLEMENT]]
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError, csv.Error, ValueError):
        raise LockError(
            "input_is_as_described", opened.file_id, "a table could not be read"
        ) from None


def most_named(
    found: Sequence[tuple[str | None, str, str]],
) -> dict[str, Settlement]:
    """For each output area, the settlement that most of its road records name.

    Each record is the output area it lies in, the address of the settlement
    it names, and the settlement's name. Of two settlements named as often,
    the one whose address sorts first. The name is the one written most often
    for that address, and of two as often the one that sorts first.
    """
    counted: dict[str, dict[str, dict[str, int]]] = {}
    for oa, address, name in found:
        if oa is not None:
            names = counted.setdefault(oa, {}).setdefault(key_of_address(address), {})
            names[name] = names.get(name, 0) + 1
    said: dict[str, Settlement] = {}
    for oa in sorted(counted):
        totals = {key: sum(names.values()) for key, names in counted[oa].items()}
        key = min(totals, key=lambda each: (-totals[each], each))
        names = counted[oa][key]
        said[oa] = Settlement(
            key=key,
            name=min(names, key=lambda each: (-names[each], each)),
            roads=totals[key],
            of=sum(totals.values()),
        )
    return said


def read(opened: Opened, outlines: Outlines, box: Box) -> dict[str, Settlement]:
    """The settlement the roads of each output area name, from the file of names."""
    records = list(roads_in(opened, box))
    inside = outlines.holding([point for point, _, _ in records])
    return most_named(
        [(oa, address, name) for oa, (_, address, name) in zip(inside, records, strict=True)]
    )


def favoured(settlement: Settlement, records: Mapping[str, str]) -> frozenset[str]:
    """The seeds that are a settlement: those read from the record its address names.

    `records` gives each seed the id of the record it was read from.
    """
    return frozenset(
        seed
        for seed, record in records.items()
        if record and key_of_record(record) == settlement.key
    )
