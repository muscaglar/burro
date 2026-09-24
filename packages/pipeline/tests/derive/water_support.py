"""What the tests of water close by share: made-up water, in a file laid out as the publisher's.

Nothing here is real. The file has the publisher's own layout: a zip that
holds `Data/oprvrs_gb.gpkg` and two notes, a layer `watercourse_link` with the
publisher's ten columns beside its number, a second layer `hydro_node`, lines
in two dimensions on the National Grid, each with the box it fits in, an index
of where each line lies, and a column `fictitious` that is text. What it holds
is made up: a few straight lines in the North Sea, where the made-up town of
the tests of cells stands.

    northing
    401000                        -- a lake, 200 metres of line
    400000   ==================== a river, which ends at 702000
    398000   ~~~~~~~~~~~~~~~~~~~~ a tidal river
             699000      702000   703000: a canal, north to south

The town is twelve output areas in three areas. Each test puts their centres
where it needs them, so that each figure can be worked out by hand.

    Quillhaven 001   homes 110, 120, 130, 140   500 in all
    Quillhaven 002   homes 150, 160, 170, 180   660 in all
    Tallowgate 001   homes 190, 200, 210, 220   820 in all
"""

import hashlib
import io
import math
import sqlite3
import struct
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from itertools import pairwise
from pathlib import Path

from burro_pipeline.derive import water_access
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CENTRES_COLUMNS, FILES, LONDON, contents, receipt_of, registry

# A string found nowhere else. If a refusal repeats what a file holds, this shows up in it.
CANARY = "Zzyzx Parva"
ZIP_NAME, MEMBER = "oprvrs_gpkg_gb.zip", "Data/oprvrs_gb.gpkg"
EDITION, CHANGED = "2026-04", "2026-04-14T11:29:13.889Z"
LAYER = "watercourse_link"
# The columns of the publisher's layer, in its own order, each with its type.
FIELDS = (
    ("id", "TEXT"),
    ("flow_direction", "TEXT"),
    ("length", "REAL"),
    ("fictitious", "TEXT"),
    ("form", "TEXT"),
    ("watercourse_name", "TEXT"),
    ("watercourse_name_alternative", "TEXT"),
    ("start_node", "TEXT"),
    ("end_node", "TEXT"),
)
# What the made-up file says its lines cover: the North Sea round the town.
COVERS = (690_000.0, 390_000.0, 710_000.0, 510_000.0)
CAN_INDEX = "ENABLE_RTREE" in {
    str(row[0]) for row in sqlite3.connect(":memory:").execute("PRAGMA compile_options")
}
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
OAS = tuple(unit.oa for unit in LONDON)

Place = tuple[float, float]


@dataclass(frozen=True)
class Stretch:
    """One made-up stretch of water."""

    form: object
    line: tuple[Place, ...]
    fictitious: object = "0"
    # What the file says it is long. With none, what its line is long, to a whole metre.
    length: object = None
    # The line as the file holds it, where a test needs bytes that are no line.
    blob: bytes | None = None
    # Whether the file holds no line for it at all.
    without_a_line: bool = False


def stretch(form: str, *line: Place) -> Stretch:
    return Stretch(form, line)


RIVER = stretch("inlandRiver", (699_000, 400_000), (700_000, 400_000), (702_000, 400_000))
CANAL = stretch("canal", (703_000, 399_000), (703_000, 401_000))
LAKE = stretch("lake", (701_000, 401_000), (701_200, 401_000))
TIDAL = stretch("tidalRiver", (699_000, 398_000), (702_000, 398_000))
# A river far from the town. It is in the file, and no build of the town reads it.
FAR_AWAY = stretch("inlandRiver", (699_000, 500_000), (702_000, 500_000))
WATER = (RIVER, CANAL, LAKE, TIDAL, FAR_AWAY)
# Where one more stretch is drawn, by a test that needs one the build reads: north of the
# town, and further than 300 metres from every home of it.
NORTH_OF_THE_TOWN = ((700_000, 403_000), (701_000, 403_000))

# Where the centre of each output area stands, in the order of their codes.
PLACED: tuple[Place, ...] = (
    # Quillhaven 001: one near the river, one at 300 metres exactly, one half a metre
    # further, and one far from everything.
    (700_100, 400_060),
    (700_200, 400_300),
    (700_300, 400_300.5),
    (700_400, 400_900),
    # Quillhaven 002: one near the lake, two beyond the end of the river and near it, the
    # second at 300 metres exactly, and one half way between the two rivers.
    (701_100, 401_100),
    (702_200, 400_000),
    (702_180, 400_240),
    (701_500, 399_000),
    # Tallowgate 001: one near the canal, one a metre too far from it, one near the tidal
    # river, and one far from everything.
    (702_950, 400_500),
    (703_301, 400_500),
    (701_500, 398_250),
    (705_000, 405_000),
)


def line_blob(line: Sequence[Place], grid: int = 27700, kind: int = 2, order: str = "<") -> bytes:
    """A line as a GeoPackage holds it: its header, the box it fits in, then the line."""
    east, north = [x for x, _ in line], [y for _, y in line]
    flags = 0b0010 | (order == "<")
    head = b"GP" + bytes([0, flags]) + struct.pack(f"{order}i", grid)
    box = struct.pack(f"{order}4d", min(east), max(east), min(north), max(north))
    points = b"".join(struct.pack(f"{order}2d", float(x), float(y)) for x, y in line)
    shape = struct.pack(f"{order}BII", order == "<", kind, len(line)) + points
    return head + box + shape


def drawn(line: Sequence[Place]) -> float:
    return sum(math.dist(a, b) for a, b in pairwise(line))


def network(
    made: Sequence[Stretch] = WATER,
    *,
    indexed: bool = CAN_INDEX,
    changed: str = CHANGED,
    fields: Sequence[tuple[str, str]] = FIELDS,
    geometry: str = "geometry",
    lines: str = "LINESTRING",
    grid: int = 27700,
    z: int = 0,
    covers: Sequence[object] = COVERS,
    index_holds: int | None = None,
    layer: str = LAYER,
) -> bytes:
    """The water as a GeoPackage with the publisher's layout. What it holds is made up."""
    with tempfile.TemporaryDirectory(prefix="burro-made-up-") as folder:
        path = Path(folder) / "made-up.gpkg"
        database = sqlite3.connect(path)
        named = ", ".join(f'"{name}" {kind}' for name, kind in fields)
        # Every name in the script is written in this file.
        database.executescript(
            f"""
            PRAGMA application_id = 1196444487;
            PRAGMA user_version = 10200;
            CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT, srs_id INTEGER PRIMARY KEY,
                organization TEXT, organization_coordsys_id INTEGER, definition TEXT,
                description TEXT);
            CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY, data_type TEXT,
                identifier TEXT, description TEXT, last_change DATETIME, min_x DOUBLE,
                min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER);
            CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT,
                geometry_type_name TEXT, srs_id INTEGER, z TINYINT, m TINYINT);
            CREATE TABLE gpkg_extensions (table_name TEXT, column_name TEXT,
                extension_name TEXT, definition TEXT, scope TEXT);
            CREATE TABLE gpkg_ogr_contents (table_name TEXT PRIMARY KEY, feature_count INTEGER);
            CREATE TABLE "{layer}" ("fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                "{geometry}" {lines}, {named});
            CREATE TABLE "hydro_node" ("fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                "geometry" POINT, "id" TEXT, "hydro_node_category" TEXT);
            INSERT INTO gpkg_spatial_ref_sys
                VALUES ('OSGB 1936 / British National Grid', 27700, 'EPSG', 27700, '', NULL);
            INSERT INTO gpkg_geometry_columns VALUES ('{layer}', '{geometry}', '{lines}',
                {grid}, {z}, 0);
            INSERT INTO gpkg_geometry_columns VALUES ('hydro_node', 'geometry', 'POINT',
                27700, 0, 0);
            INSERT INTO gpkg_contents VALUES ('hydro_node', 'features', 'hydro_node', '',
                '{changed}', 690000, 390000, 710000, 510000, 27700);
            INSERT INTO "hydro_node" ("id", "hydro_node_category")
                VALUES ('made-up-node', '{CANARY}');
            """  # noqa: S608
        )
        database.execute(
            "INSERT INTO gpkg_contents VALUES (?, 'features', ?, '', ?, ?, ?, ?, ?, ?)",
            (layer, layer, changed, *covers, grid),
        )
        if indexed:
            database.executescript(
                f"""
                CREATE VIRTUAL TABLE "rtree_{LAYER}_geometry"
                    USING rtree(id, minx, maxx, miny, maxy);
                INSERT INTO gpkg_extensions VALUES ('{LAYER}', 'geometry', 'gpkg_rtree_index',
                    'http://www.geopackage.org/spec120/#extension_rtree', 'write-only');
                """  # noqa: S608
            )
        held_by = {name for name, _ in fields}
        for number, water in enumerate(made, start=1):
            east, north = [x for x, _ in water.line], [y for _, y in water.line]
            shape = line_blob(water.line) if water.blob is None else water.blob
            row: dict[str, object] = {
                geometry: None if water.without_a_line else shape,
                "id": f"made-up-{number}",
                "flow_direction": "in direction",
                "length": round(drawn(water.line)) if water.length is None else water.length,
                "fictitious": water.fictitious,
                "form": water.form,
                "watercourse_name": CANARY,
                "watercourse_name_alternative": None,
                "start_node": f"made-up-{number}-a",
                "end_node": f"made-up-{number}-b",
            }
            kept = {name: value for name, value in row.items() if name in {geometry, *held_by}}
            columns = ", ".join(f'"{name}"' for name in kept)
            database.execute(
                f'INSERT INTO "{layer}" ({columns}) VALUES ({", ".join("?" * len(kept))})',  # noqa: S608
                tuple(kept.values()),
            )
            if indexed and (index_holds is None or number <= index_holds):
                database.execute(
                    f'INSERT INTO "rtree_{LAYER}_geometry" VALUES (?, ?, ?, ?, ?)',  # noqa: S608
                    (number, min(east), max(east), min(north), max(north)),
                )
        database.execute("INSERT INTO gpkg_ogr_contents VALUES (?, ?)", (layer, len(made)))
        database.commit()
        database.close()
        return path.read_bytes()


def zipped(geopackage: bytes | None = None, *, members: Sequence[str] = (MEMBER,)) -> bytes:
    """The zip as the publisher gives it: the GeoPackage, and two notes beside it."""
    packed = io.BytesIO()
    inside = network() if geopackage is None else geopackage
    notes = {"Doc/licence.txt": b"Made up for a test.\n", "Doc/readme.txt": b"Made up.\n"}
    with zipfile.ZipFile(packed, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in (dict.fromkeys(members, inside) | notes).items():
            # A fixed day, so that the same water is always the same bytes.
            archive.writestr(zipfile.ZipInfo(name, (2026, 4, 14, 12, 0, 0)), content)
    return packed.getvalue()


@cache
def the_water() -> bytes:
    return zipped()


def with_one(water: Stretch) -> bytes:
    """The water of the town, and one stretch more."""
    return zipped(network((*WATER, water)))


def centres_at(placed: Mapping[str, Place]) -> bytes:
    """The centres of the town's output areas, as the statistics office writes them."""
    lines = [",".join(CENTRES_COLUMNS)]
    for number, unit in enumerate(LONDON, start=1):
        if unit.oa in placed:
            east, north = placed[unit.oa]
            lines.append(
                f"{east:.4f},{north:.4f},{number},{unit.oa},"
                f"{{made-up-{number}}},{{made-up-{number}-2}}"
            )
    return b"\xef\xbb\xbf" + "".join(f"{line}\n" for line in lines).encode()


def on(*placed: Place) -> dict[str, Place]:
    """Twelve centres, one for each output area of the town, in the order of their codes."""
    assert len(placed) == len(OAS)
    return dict(zip(OAS, placed, strict=True))


def water_receipt(content: bytes, name: str = ZIP_NAME, edition: str = EDITION) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=water_access.SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-23T21:51:27Z",
        how=How.FETCHED,
        edition=edition,
        data_period=Period(as_at=edition),
    )


def inputs_of(
    folder: Path,
    packed: bytes | None = None,
    placed: Mapping[str, Place] | None = None,
    *,
    more: Sequence[tuple[Receipt, bytes]] = (),
    edition: str = EDITION,
    given: Registry | None = None,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each."""
    packed = the_water() if packed is None else packed
    files = contents() | {"centres": centres_at(on(*PLACED) if placed is None else placed)}
    receipts = [
        receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3])
        for which, content in files.items()
    ]
    every = [
        *zip(receipts, files.values(), strict=True),
        (water_receipt(packed, edition=edition), packed),
        *more,
    ]
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")
