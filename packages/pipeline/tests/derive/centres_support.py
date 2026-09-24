"""What the tests of the town centre measures share: made-up centres, in a file as the publisher's.

Nothing here is real. The centres stand beside the made-up town of the tests
of cells, which is drawn in squares of 100 metres in the North Sea. The centre
of population of each output area is put in the very middle of its square, so
each distance can be worked out by hand.

The file is a GeoPackage of one layer, `town_centres`, with the 28 columns
the publisher's file has beside its id and its outline, under the same names.
What it holds is made up. The name of every centre is a string found nowhere
else, because no name is ever read.

    metres east   -300  -100  0    100  200  300  400  500  600      1000        2000
    row 1         +------+    | a1 | a2 | b1 | b2 | c1 | c2 |   z1   +-------------+
    row 0         | Green|    | a3 | a4 | b3 | b4 | c3 | c4 |        |    Road     |
                  +------+      Quillhaven 001, 002, Tallowgate 001  +-------------+

    Green   a square of 4 hectares. It fills 63.7 in 100 of the circle round it
    Road    a strip of 20 hectares, five times as long as wide. It fills 24.5 in 100

    Column of the home     0     1     2     3     4     5
    Metres from Green      150   250   350   450   550   650
    Metres from Road       950   850   750   650   550   450

`z1` is the one output area beyond London. It is in the file of centres of
population only where a test asks for it.
"""

import hashlib
import math
import sqlite3
import struct
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from burro_pipeline.derive import town_centres
from burro_pipeline.evidence.receipt import EditionFrom, How, Period, Receipt, Where
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import (
    CANARY,
    CENTRES_COLUMNS,
    EAST,
    FILES,
    NORTH,
    SIDE,
    TOWN,
    MadeUp,
    contents,
    receipt_of,
    registry,
)

LONDON = tuple(unit for unit in TOWN if unit.borough.startswith("E09"))
(BEYOND,) = tuple(unit for unit in TOWN if not unit.borough.startswith("E09"))
OAS = tuple(unit.oa for unit in LONDON)
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
AREAS = (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
# The day the made-up file says its data is as at, and the edition a fetch would write.
AS_AT = "2026-01-05"
EDITION = f"last changed {AS_AT}"
LAYER, GEOMETRY = "town_centres", "geom"
# Every column of the publisher's layer beside its key and its outline, in the file's order.
COLUMNS: tuple[str, ...] = (
    "OBJECTID",
    "layerreference",
    "sitereference",
    "sitename",
    "address",
    "uprn",
    "borough",
    "planningauthority",
    "firstaddeddate",
    "lastupdateddate",
    "removeddate",
    "status",
    "hectares",
    "easting",
    "northing",
    "designation",
    "boroughdesignation",
    "classification",
    "notes",
    "source",
    "extrainfo1",
    "extrainfo2",
    "extrainfo3",
    "missing",
    "st_area_geom_",
    "st_perimeter_geom_",
    "Shape_Length",
    "Shape_Area",
)

Point = tuple[float, float]
Ring = tuple[Point, ...]


def box(west: float, south: float, wide: float, high: float) -> Ring:
    """A ring round a box, by its corner nearest the grid's origin, on the grid of the town."""
    x, y = EAST + west, NORTH + south
    return ((x, y), (x + wide, y), (x + wide, y + high), (x, y + high), (x, y))


def _area(ring: Ring) -> float:
    """What a ring encloses, in square metres."""
    twice = math.fsum(a[0] * b[1] - b[0] * a[1] for a, b in pairwise(ring))
    return abs(twice) / 2


@dataclass(frozen=True)
class MadeUpCentre:
    """One made-up town centre."""

    record_id: str
    # Each piece is the ring round it. No made-up centre has a hole.
    pieces: tuple[Ring, ...]
    rank: str = "District"
    # The size the row gives, in hectares. None is the size the outline is drawn to.
    said: float | str | None = None
    grid: int = 27700

    @property
    def hectares(self) -> float:
        return math.fsum(_area(piece) for piece in self.pieces) / 10_000


GREEN = MadeUpCentre("TCB00000001", (box(-300, 0, 200, 200),))
ROAD = MadeUpCentre("TCB00000002", (box(1000, 0, 1000, 200),), rank="Major")
CENTRES = (GREEN, ROAD)
# What each fills of the circle round it, in 100: the area over pi times half the diagonal squared.
GREEN_FILLS = 100 * 40_000 / (math.pi * 20_000)
ROAD_FILLS = 100 * 200_000 / (math.pi * 260_000)


def outline(centre: MadeUpCentre) -> bytes:
    """An outline as a GeoPackage holds it: its header, then a multipolygon."""
    polygons = b"".join(
        struct.pack("<BII", 1, 3, 1)
        + struct.pack("<I", len(piece))
        + b"".join(struct.pack("<dd", *corner) for corner in piece)
        for piece in centre.pieces
    )
    shape = struct.pack("<BII", 1, 6, len(centre.pieces)) + polygons
    return b"GP" + bytes([0, 1]) + struct.pack("<i", centre.grid) + shape


def _row(number: int, centre: MadeUpCentre) -> tuple[object, ...]:
    size = centre.hectares if centre.said is None else centre.said
    held: dict[str, object] = {
        "OBJECTID": number,
        "layerreference": centre.record_id,
        "sitename": CANARY,
        "borough": "Quillhaven",
        "planningauthority": "Quillhaven",
        "hectares": size,
        "easting": int(centre.pieces[0][0][0]),
        "northing": int(centre.pieces[0][0][1]),
        "designation": "Town Centres",
        "boroughdesignation": "Town Centres",
        "classification": centre.rank,
        "notes": "Made up for a test.",
        "st_area_geom_": centre.hectares * 10_000,
        "Shape_Area": centre.hectares * 10_000,
    }
    return tuple(held.get(name) for name in COLUMNS)


def centres_gpkg(
    centres: Sequence[MadeUpCentre] = CENTRES,
    *,
    layer: str = LAYER,
    columns: Sequence[str] = COLUMNS,
    grid: int = 27700,
) -> bytes:
    """The file of town centres, as the publisher lays it out. What it holds is made up."""
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
            CREATE TABLE "{layer}" (fid INTEGER PRIMARY KEY, "{GEOMETRY}" BLOB, {named});
            INSERT INTO gpkg_contents
                VALUES ('{layer}', 'features', '{layer}', {grid}, '{AS_AT}T00:00:00.000Z');
            INSERT INTO gpkg_geometry_columns
                VALUES ('{layer}', '{GEOMETRY}', 'MULTIPOLYGON', {grid}, 0, 0);
            """  # noqa: S608
        )
        marks = ", ".join("?" for _ in columns)
        for number, centre in enumerate(centres, start=1):
            every = dict(zip(COLUMNS, _row(number, centre), strict=True))
            database.execute(
                f'INSERT INTO "{layer}" VALUES (?, ?, {marks})',  # noqa: S608
                (number, outline(centre), *(every[name] for name in columns)),
            )
        database.commit()
        database.close()
        return path.read_bytes()


def centres_receipt(content: bytes, *, name: str = town_centres.FILE) -> Receipt:
    """The receipt a fetch would write of the made-up file, once its period is stated."""
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=town_centres.SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-23T21:32:00Z",
        how=How.FETCHED,
        edition=EDITION,
        edition_from=EditionFrom(
            where=Where.GEOPACKAGE, at="gpkg_contents.last_change", period_too=False
        ),
        data_period=Period(as_at=AS_AT),
    )


def homes_in_the_middle(
    town: Sequence[MadeUp] = LONDON, *, left_out: Sequence[str] = (), broken: str | None = None
) -> bytes:
    """The centre of population of each output area, in the very middle of its square."""
    lines = [",".join(CENTRES_COLUMNS)]
    for number, unit in enumerate(town, start=1):
        if unit.oa in left_out:
            continue
        column, row = unit.squares[0]
        east, north = EAST + column * SIDE + SIDE / 2, NORTH + row * SIDE + SIDE / 2
        written = "east" if unit.oa == broken else f"{east:.4f}"
        lines.append(
            f"{written},{north:.4f},{number},{unit.oa},{{made-up-{number}}},{{made-up-{number}-2}}"
        )
    return b"\xef\xbb\xbf" + "".join(f"{line}\n" for line in lines).encode()


def inputs_of(
    folder: Path,
    packed: bytes | None = None,
    *,
    homes: bytes | None = None,
    given: Registry | None = None,
    with_a_receipt: bool = True,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each."""
    files = contents() | {"centres": homes_in_the_middle() if homes is None else homes}
    every = [
        (
            receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3]),
            content,
        )
        for which, content in files.items()
    ]
    drawn = centres_gpkg() if packed is None else packed
    every.append((centres_receipt(drawn), drawn))
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    receipts = [
        receipt
        for receipt, _ in every
        if with_a_receipt or receipt.source_id != town_centres.SOURCE
    ]
    return Inputs(given or registry(), receipts, store, folder / "work")


def opened_of(folder: Path, packed: bytes) -> Opened:
    """One made-up file of town centres, handed over as a step of a build is handed one."""
    receipt = centres_receipt(packed)
    path = folder / "given" / receipt.publisher_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(packed)
    store = FolderStore(folder / "store")
    store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(registry(), [receipt], store, folder / "work").open(
        town_centres.SOURCE, Use.SCORING
    )
