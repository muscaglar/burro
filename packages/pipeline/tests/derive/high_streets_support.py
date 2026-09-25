"""What the tests of the high streets share: made-up high streets, in a file as the publisher's.

Nothing here is real. The high streets stand on the made-up town of the tests
of cells, which is drawn in squares of 100 metres in the North Sea, among the
made-up conservation areas of `heritage_support.py`. The centre of population
of each output area is put in the very middle of its square, so each distance
can be worked out by hand.

The file is a GeoPackage of one layer, `Table1`, with the columns the
publisher's file has, under the same names. It holds a row for each piece of a
high street. What it holds is made up. The name of every high street is a
string found nowhere else, because no name is ever read, and the size every
row gives is a size of nothing, because no size is read either.

    metres east   0    100   200   300   400   500   600
    row 1       | a1  | a2  | b1  | b2  | c1  | c2  |    Within in a1 and a2,
    row 0       | a3  | a4  | b3  | b4  | c3  | c4  |    Far Side in c1 and in c2,
                  Quillhaven 001, 002, Tallowgate 001    In Two in b3 and in b4

    Within     one piece of 0.64 hectares, all of it inside Old Quarter
    In Two     two pieces of 0.18 hectares. One lies inside Wharf, and one inside nothing
    Far Side   two pieces of 0.24 hectares, in Tallowgate. One lies inside Quayside

    The home of    a1  a2  a3  a4  b1  b2  b3  b4  c1  c2  c3  c4
    Is nearest to  W   W   W   W   W   F   T   T   F   F   F   F
    At, in metres  0   0   70  70  70  70  10  10  0   0   70  70

W is Within, T is In Two and F is Far Side. Each is named for what a test asks
of it, and is the name of no place.
"""

import hashlib
import sqlite3
import struct
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.derive import high_streets
from burro_pipeline.evidence.receipt import EditionFrom, How, Period, Receipt, Where
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, FILES, contents, receipt_of, registry
from .centres_support import Ring, box, homes_in_the_middle
from .heritage_support import AREAS, CONSERVATION, areas_file, heritage_receipt

# The day the made-up file says its data is as at, and the edition a fetch would write.
AS_AT = "2025-07-01"
EDITION = f"last changed {AS_AT}"
LAYER, GEOMETRY = "Table1", "geom"
# Every column of the publisher's layer beside its key and its outline, in the file's order.
COLUMNS: tuple[str, ...] = (
    "objectid",
    "highstreet_id",
    "highstreet_name",
    "area_ha",
    "gdb_geomattr_data",
)
# A size that is the size of nothing that is drawn. It stands where the file gives one.
NO_SIZE = 999.0


@dataclass(frozen=True)
class MadeUpStreet:
    """One made-up high street. Each piece of it is a row of the file."""

    record_id: int | None
    # Each piece is the ring round it. No made-up piece has a hole.
    pieces: tuple[Ring, ...]
    grid: int = 27700


WITHIN = MadeUpStreet(101, (box(20, 120, 160, 40),))
IN_TWO = MadeUpStreet(102, (box(220, 10, 60, 30), box(320, 10, 60, 30)))
FAR_SIDE = MadeUpStreet(103, (box(420, 120, 60, 40), box(510, 120, 60, 40)))
STREETS = (WITHIN, IN_TWO, FAR_SIDE)
ONE, TWO, THREE = "101", "102", "103"


def piece(ring: Ring, grid: int = 27700) -> bytes:
    """One piece as a GeoPackage holds it: its header, then a polygon of one ring."""
    shape = (
        struct.pack("<BII", 1, 3, 1)
        + struct.pack("<I", len(ring))
        + b"".join(struct.pack("<dd", *corner) for corner in ring)
    )
    return b"GP" + bytes([0, 1]) + struct.pack("<i", grid) + shape


def streets_gpkg(
    streets: Sequence[MadeUpStreet] = STREETS,
    *,
    layer: str = LAYER,
    columns: Sequence[str] = COLUMNS,
    grid: int = 27700,
) -> bytes:
    """The file of high streets, as the publisher lays it out. What it holds is made up."""
    with tempfile.TemporaryDirectory(prefix="burro-made-up-") as folder:
        path = Path(folder) / "made-up.gpkg"
        database = sqlite3.connect(path)
        named = ", ".join(f'"{name}"' for name in columns)
        # Every name in a statement is written in this file.
        database.executescript(
            f"""
            PRAGMA application_id = 1196444487;
            CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT, srs_id INTEGER PRIMARY KEY,
                organization TEXT, organization_coordsys_id INTEGER, definition TEXT);
            CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY, data_type TEXT,
                identifier TEXT, srs_id INTEGER, last_change DATETIME);
            CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT,
                geometry_type_name TEXT, srs_id INTEGER, z TINYINT, m TINYINT);
            INSERT INTO gpkg_spatial_ref_sys
                VALUES ('British_National_Grid', 27700, 'EPSG', 27700, '');
            CREATE TABLE "{layer}" (id INTEGER PRIMARY KEY, "{GEOMETRY}" BLOB, {named});
            INSERT INTO gpkg_contents
                VALUES ('{layer}', 'features', '{layer}', {grid}, '{AS_AT}T08:14:17.872Z');
            INSERT INTO gpkg_geometry_columns
                VALUES ('{layer}', '{GEOMETRY}', 'POLYGON', {grid}, 0, 0);
            """  # noqa: S608
        )
        marks = ", ".join("?" for _ in columns)
        number = 0
        for street in streets:
            for ring in street.pieces:
                number += 1
                every: dict[str, object] = {
                    "objectid": number,
                    "highstreet_id": street.record_id,
                    "highstreet_name": CANARY,
                    "area_ha": NO_SIZE,
                    "gdb_geomattr_data": None,
                }
                database.execute(
                    f'INSERT INTO "{layer}" VALUES (?, ?, {marks})',  # noqa: S608
                    (number, piece(ring, street.grid), *(every[name] for name in columns)),
                )
        database.commit()
        database.close()
        return path.read_bytes()


def streets_receipt(content: bytes, *, name: str = high_streets.FILE) -> Receipt:
    """The receipt a fetch would write of the made-up file, once its period is stated."""
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=high_streets.SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-24T12:04:00Z",
        how=How.FETCHED,
        edition=EDITION,
        edition_from=EditionFrom(
            where=Where.GEOPACKAGE, at="gpkg_contents.last_change", period_too=False
        ),
        data_period=Period(as_at=AS_AT),
    )


def inputs_of(
    folder: Path,
    packed: bytes | None = None,
    *,
    areas: bytes | None = None,
    homes: bytes | None = None,
    given: Registry | None = None,
    with_a_receipt: bool = True,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each.

    They are the files of the town, the high streets, and the conservation
    areas: `areas_file()` of `heritage_support.py`, where none is given.
    """
    files = contents() | {"centres": homes_in_the_middle() if homes is None else homes}
    every = [
        (
            receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3]),
            content,
        )
        for which, content in files.items()
    ]
    drawn = streets_gpkg() if packed is None else packed
    every.append((streets_receipt(drawn), drawn))
    recorded = areas_file(AREAS) if areas is None else areas
    every.append((heritage_receipt(CONSERVATION[0], CONSERVATION[1], recorded), recorded))
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    receipts = [
        receipt
        for receipt, _ in every
        if with_a_receipt or receipt.source_id != high_streets.SOURCE
    ]
    return Inputs(given or registry(), receipts, store, folder / "work")


def opened_of(folder: Path, packed: bytes) -> Opened:
    """One made-up file of high streets, handed over as a step of a build is handed one."""
    receipt = streets_receipt(packed)
    path = folder / "given" / receipt.publisher_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(packed)
    store = FolderStore(folder / "store")
    store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(registry(), [receipt], store, folder / "work").open(
        high_streets.SOURCE, Use.SCORING
    )
