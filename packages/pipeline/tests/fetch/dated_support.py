"""Made-up files that date themselves, each shaped like a publisher's.

A register in XML with a day in its header, a GeoPackage that records when its
contents were last changed, and a street extract whose header block says what
time its data runs to. Every row under a header is the canary row: a reader
that reads past the header gives itself away. Nothing here is a publisher's.
"""

import sqlite3
import struct
import zlib
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from .support import CANARY_ROW

# The day a made-up file was retrieved, and the day and the time it says of itself.
RETRIEVED_AT = "2026-09-24T09:12:31Z"
DAY = "2026-09-16"
TIME = "2026-09-22T20:22:59Z"

A_ROW = (
    "<EstablishmentDetail>"
    f"<BusinessName>{CANARY_ROW}</BusinessName>"
    "<RatingDate>2025-01-02</RatingDate>"
    "<ExtractDate>2001-01-01</ExtractDate>"
    "</EstablishmentDetail>"
)


def header_of(*days: str, more: str = "") -> str:
    """The header of a made-up register, with a day for each given. None gives no day."""
    stated = "".join(f"<ExtractDate>{day}</ExtractDate>" for day in days)
    return (
        f"<Header>{stated}<ItemCount>2</ItemCount><ReturnCode>Success</ReturnCode>{more}</Header>"
    )


def register(header: str, *, before: str = "", rows: int = 2, mark: bytes = b"") -> bytes:
    """A made-up register: a declaration, a root, a header, and a row for each business."""
    text = (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'{before}<FHRSEstablishment xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"{header}<EstablishmentCollection>{A_ROW * rows}</EstablishmentCollection>"
        "</FHRSEstablishment>"
    )
    return mark + text.encode()


def written(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    return path


def geopackage(path: Path, changes: Sequence[object], column: str = "last_change") -> Path:
    """A made-up GeoPackage with a layer for each change given, and a row in each layer."""
    path.unlink(missing_ok=True)
    database = sqlite3.connect(path)
    try:
        database.execute("PRAGMA application_id = 0x47504B47")
        database.execute(
            "CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY, data_type TEXT, "
            f"identifier TEXT, description TEXT, {column} DATETIME, srs_id INTEGER)"
        )
        for number, change in enumerate(changes, start=1):
            layer = f"made_up_{number}"
            database.execute(f"CREATE TABLE {layer} (fid INTEGER PRIMARY KEY, name TEXT)")
            database.execute(f"INSERT INTO {layer} VALUES (NULL, ?)", (CANARY_ROW,))  # noqa: S608
            database.execute(
                "INSERT INTO gpkg_contents VALUES (?, 'features', ?, ?, ?, 27700)",
                (layer, layer, CANARY_ROW, change),
            )
        database.commit()
    finally:
        database.close()
    return path


def geopackage_drawn_from_a_layer(path: Path) -> Path:
    """A made-up GeoPackage whose record of contents is a view of a layer's rows."""
    database = sqlite3.connect(path)
    try:
        database.execute("CREATE TABLE made_up (fid INTEGER PRIMARY KEY, name TEXT)")
        database.execute("INSERT INTO made_up VALUES (NULL, '2025-12-22T16:37:50.337Z')")
        database.execute("CREATE VIEW gpkg_contents AS SELECT name AS last_change FROM made_up")
        database.commit()
    finally:
        database.close()
    return path


def number(value: int) -> bytes:
    """A whole number as a street extract writes one: seven bits to a byte, the least first."""
    value &= (1 << 64) - 1
    written = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        written.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(written)


def whole(field: int, value: int) -> bytes:
    return number(field << 3) + number(value)


def held(field: int, content: bytes) -> bytes:
    return number(field << 3 | 2) + number(len(content)) + content


def seconds_of(time: str) -> int:
    return int(datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC).timestamp())


def header_block(*times: str) -> bytes:
    """What the first block of a made-up street extract holds, with each time given."""
    stated = b"".join(whole(32, seconds_of(time)) for time in times)
    return held(4, b"OsmSchema-V0.6") + held(4, b"DenseNodes") + held(16, b"made-up") + stated


def block(kind: bytes, content: bytes, *, packed: bool = True) -> bytes:
    """One block of a street extract: the length of its header, its header, and its blob."""
    blob = whole(2, len(content)) + held(3, zlib.compress(content)) if packed else held(1, content)
    header = held(1, kind) + whole(3, len(blob))
    return struct.pack(">I", len(header)) + header + blob


def street_extract(first: bytes) -> bytes:
    """A made-up street extract: a first block, and then a block of data that is the canary."""
    return first + block(b"OSMData", CANARY_ROW.encode() * 50)
