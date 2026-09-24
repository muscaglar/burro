"""What the tests of cells share: a made-up town, in files shaped like the publishers'.

Nothing here is real. The town is Quillhaven and Tallowgate, two boroughs that
do not exist, drawn in squares of 100 metres in the North Sea. Beside them is
one district outside London, which the spine must leave out. Every code is
shaped like the statistics office's and is none it has given out: the office's
own codes run far below these.

The files have the publishers' own layouts: the names of the columns, the
members of the zip, the layer and the fields of the GeoPackage, the mark at
the start of a file and the ends of its lines. So a parser that reads these
reads the real files. What they hold is made up.

    columns  0    1    2    3    4    5        7
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |   | z1 |     each square is one output area
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |
             Quillhaven 001  002   Tallowgate 001   outside London

Two output areas side by side are one LSOA. An output area of Tallowgate has a
second piece, an island, so that one outline is in two pieces.
"""

import csv
import hashlib
import io
import sqlite3
import struct
import tempfile
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path

from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry, load
from burro_pipeline.registry.model import Use

REPOSITORY = Path(__file__).parents[4]
# A string found nowhere else. It stands in a column the spine does not read.
CANARY = "Zzyzx Parva"
# A zip holds the time each member was written. It is fixed here, so that the same made-up
# file is the same bytes, and so the same file, whenever a test makes it.
WRITTEN = (2026, 9, 23, 0, 0, 0)
# Where the made-up town stands on the National Grid: in the North Sea.
EAST, NORTH, SIDE = 700_000, 400_000, 100

LOOKUP_NAME = "OA21_LAD22_LSOA21_MSOA21_LEP22_EN_LU_V2_made_up.csv"
HOMES_NAME = "census2021-ts044.zip"
OUTLINES_NAME = "Output_Areas_2021_EW_BGC_V2_made_up.gpkg"
LSOA_OUTLINES_NAME = (
    "Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5_made_up.gpkg"
)
CENTRES_NAME = "Output_Areas_(December_2021)_EW_Population_Weighted_Centroids_(V4)_made_up.csv"

LOOKUP_COLUMNS = (
    "OA21CD",
    "LSOA21CD",
    "LSOA21NM",
    "MSOA21CD",
    "MSOA21NM",
    "LEP22CD1",
    "LEP22NM1",
    "LEP22CD2",
    "LEP22NM2",
    "LAD22CD",
    "LAD22NM",
    "ObjectId",
)
HOMES_COLUMNS = (
    "date",
    "geography",
    "geography code",
    "Accommodation type: Total: All households",
    "Accommodation type: Detached",
    "Accommodation type: Semi-detached",
    "Accommodation type: Terraced",
    "Accommodation type: In a purpose-built block of flats or tenement",
    "Accommodation type: Part of a converted or shared house, including bedsits",
    "Accommodation type: Part of another converted building, for example, former school, "
    "church or warehouse",
    "Accommodation type: In a commercial building, for example, in an office building, hotel "
    "or over a shop",
    "Accommodation type: A caravan or other mobile or temporary structure",
)
CENTRES_COLUMNS = ("X", "Y", "FID", "OA21CD", "GlobalID", "GlobalID_2")
OUTLINE_FIELDS = (
    ("LSOA21CD", "TEXT(9)"),
    ("LSOA21NM", "TEXT(40)"),
    ("LSOA21NMW", "TEXT(29)"),
    ("BNG_E", "MEDIUMINT"),
    ("BNG_N", "MEDIUMINT"),
    ("LAT", "FLOAT"),
    ("LONG", "FLOAT"),
    ("GlobalID", "TEXT(38)"),
)

Square = tuple[int, int]


@dataclass(frozen=True)
class MadeUp:
    """One made-up output area."""

    oa: str
    lsoa: str
    lsoa_name: str
    msoa: str
    msoa_name: str
    borough: str
    borough_name: str
    homes: int
    # The squares it covers, by column and row. The first is where its homes are.
    squares: tuple[Square, ...]


def _town() -> tuple[MadeUp, ...]:
    found: list[MadeUp] = []
    msoas = (
        ("E02999001", "Quillhaven 001", "E09000901", "Quillhaven", 0),
        ("E02999002", "Quillhaven 002", "E09000901", "Quillhaven", 2),
        ("E02999003", "Tallowgate 001", "E09000902", "Tallowgate", 4),
    )
    number = 0
    for msoa, name, borough, borough_name, first in msoas:
        for row, letter in ((1, "A"), (0, "B")):
            for column in (first, first + 1):
                number += 1
                found.append(
                    MadeUp(
                        oa=f"E00999{number:03d}",
                        lsoa=f"E01999{(number + 1) // 2:03d}",
                        lsoa_name=f"{name}{letter}",
                        msoa=msoa,
                        msoa_name=name,
                        borough=borough,
                        borough_name=borough_name,
                        homes=100 + 10 * number,
                        squares=((column, row),),
                    )
                )
    # The last output area of Tallowgate has an island, two squares to the south.
    last = found[-1]
    found[-1] = replace(last, squares=(*last.squares, (5, -2)))
    found.append(
        MadeUp(
            oa="E00999901",
            lsoa="E01999901",
            lsoa_name="Made-up District 001A",
            msoa="E02999901",
            msoa_name="Made-up District 001",
            borough="E07000901",
            borough_name="Made-up District",
            homes=500,
            squares=((7, 1),),
        )
    )
    return tuple(found)


TOWN = _town()
LONDON = tuple(unit for unit in TOWN if unit.borough.startswith("E09"))


def lookup_csv(town: Iterable[MadeUp] = TOWN, columns: Sequence[str] = LOOKUP_COLUMNS) -> bytes:
    """The lookup, as the portal writes it: a mark at the start, and lines that end CR LF."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, columns, extrasaction="ignore", lineterminator="\r\n")
    table.writeheader()
    for number, unit in enumerate(town, start=1):
        table.writerow(
            {
                "OA21CD": unit.oa,
                "LSOA21CD": unit.lsoa,
                "LSOA21NM": unit.lsoa_name,
                "MSOA21CD": unit.msoa,
                "MSOA21NM": unit.msoa_name,
                "LEP22CD1": "E37999901",
                "LEP22NM1": CANARY,
                "LEP22CD2": "",
                "LEP22NM2": "",
                "LAD22CD": unit.borough,
                "LAD22NM": unit.borough_name,
                "ObjectId": number,
            }
        )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def homes_zip(town: Iterable[MadeUp] = TOWN, columns: Sequence[str] = HOMES_COLUMNS) -> bytes:
    """The census table of accommodation type: a zip with a CSV for each geography."""
    town = tuple(town)
    by_oa = io.StringIO(newline="")
    table = csv.DictWriter(by_oa, columns, extrasaction="ignore", lineterminator="\n")
    table.writeheader()
    for unit in town:
        # The kinds of home add up to the total, as they do in the table. 9 is no count the
        # spine may read: it reads the total and nothing else.
        kinds = dict.fromkeys(HOMES_COLUMNS[4:], 9) | {HOMES_COLUMNS[4]: unit.homes - 63}
        table.writerow(
            {"date": 2021, "geography": unit.oa, "geography code": unit.oa}
            | {HOMES_COLUMNS[3]: unit.homes}
            | kinds
        )
    return zip_of(
        {
            "census2021-ts044-lsoa.csv": ",".join(columns) + "\n",
            "census2021-ts044-oa.csv": by_oa.getvalue(),
            "metadata/ts044-2021-2.txt": "Made up for a test.\n",
        }
    )


def zip_of(members: Mapping[str, str | bytes]) -> bytes:
    """A made-up zip of the members given, in their order, each written at `WRITTEN`."""
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        for name, content in members.items():
            archive.writestr(zipfile.ZipInfo(name, date_time=WRITTEN), content)
    return packed.getvalue()


def centres_csv(town: Iterable[MadeUp] = TOWN) -> bytes:
    """The centres of population: one point for each output area, on the National Grid."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, CENTRES_COLUMNS, lineterminator="\n")
    table.writeheader()
    for number, unit in enumerate(town, start=1):
        column, row = unit.squares[0]
        table.writerow(
            {
                "X": f"{EAST + column * SIDE + 50.25:.4f}",
                "Y": f"{NORTH + row * SIDE + 50.75:.4f}",
                "FID": number,
                "OA21CD": unit.oa,
                "GlobalID": f"{{made-up-{number}}}",
                "GlobalID_2": f"{{made-up-{number}-2}}",
            }
        )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def _ring(square: Square, wide: int = 1) -> bytes:
    """A ring round a square, or round several squares side by side in one row."""
    column, row = square
    west, south = EAST + column * SIDE, NORTH + row * SIDE
    corners = (
        (west, south),
        (west + wide * SIDE, south),
        (west + wide * SIDE, south + SIDE),
        (west, south + SIDE),
        (west, south),
    )
    return struct.pack("<I", len(corners)) + b"".join(
        struct.pack("<dd", float(x), float(y)) for x, y in corners
    )


def outline_blob(squares: Sequence[Square], grid: int = 27700) -> bytes:
    """An outline as a GeoPackage holds it: its header, then a multipolygon.

    Squares side by side in one row are one piece of it, because the pieces of
    a valid outline do not share a side.
    """
    pieces: list[tuple[Square, int]] = []
    for column, row in sorted(squares, key=lambda square: (square[1], square[0])):
        first, wide = pieces[-1] if pieces else ((column, row), 0)
        if pieces and first[1] == row and first[0] + wide == column:
            pieces[-1] = (first, wide + 1)
        else:
            pieces.append(((column, row), 1))
    polygons = b"".join(struct.pack("<BII", 1, 3, 1) + _ring(*piece) for piece in pieces)
    shape = struct.pack("<BII", 1, 6, len(pieces)) + polygons
    return b"GP" + bytes([0, 1]) + struct.pack("<i", grid) + shape


def geopackage(
    layer: str, code_field: str, outlines: Mapping[str, bytes], grid: int = 27700
) -> bytes:
    """A GeoPackage of one layer, with the fields the statistics office's have."""
    with tempfile.TemporaryDirectory(prefix="burro-made-up-") as folder:
        path = Path(folder) / "made-up.gpkg"
        _write_geopackage(path, layer, code_field, outlines, grid)
        return path.read_bytes()


def _write_geopackage(
    path: Path, layer: str, code_field: str, outlines: Mapping[str, bytes], grid: int
) -> None:
    database = sqlite3.connect(path)
    fields = [("OA21CD", "TEXT(9)"), *OUTLINE_FIELDS] if code_field == "OA21CD" else OUTLINE_FIELDS
    named = ", ".join(f'"{name}" {kind}' for name, kind in fields)
    # Every name in the script is written in this file.
    database.executescript(
        f"""
        PRAGMA application_id = 1196444487;
        CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT, srs_id INTEGER PRIMARY KEY,
            organization TEXT, organization_coordsys_id INTEGER, definition TEXT);
        CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY, data_type TEXT,
            identifier TEXT, srs_id INTEGER);
        CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT,
            geometry_type_name TEXT, srs_id INTEGER, z TINYINT, m TINYINT);
        CREATE TABLE "{layer}" (FID INTEGER PRIMARY KEY, SHAPE MULTIPOLYGON, {named});
        INSERT INTO gpkg_spatial_ref_sys
            VALUES ('British_National_Grid', 27700, 'EPSG', 27700, '');
        INSERT INTO gpkg_contents VALUES ('{layer}', 'features', '{layer}', {grid});
        INSERT INTO gpkg_geometry_columns
            VALUES ('{layer}', 'SHAPE', 'MULTIPOLYGON', {grid}, 0, 0);
        """  # noqa: S608
    )
    for code, blob in outlines.items():
        database.execute(
            f'INSERT INTO "{layer}" (SHAPE, "{code_field}", LSOA21NM) VALUES (?, ?, ?)',  # noqa: S608
            (blob, code, CANARY),
        )
    database.commit()
    database.close()


def oa_outlines(town: Iterable[MadeUp] = TOWN) -> bytes:
    outlines = {unit.oa: outline_blob(unit.squares) for unit in town}
    return geopackage("OA_2021_EW_BGC_V2", "OA21CD", outlines)


def lsoa_outlines(town: Iterable[MadeUp] = TOWN) -> bytes:
    squares: dict[str, list[Square]] = {}
    for unit in town:
        squares.setdefault(unit.lsoa, []).extend(unit.squares)
    outlines = {lsoa: outline_blob(found) for lsoa, found in squares.items()}
    return geopackage("LSOA_2021_EW_BGC_V5", "LSOA21CD", outlines)


@cache
def registry() -> Registry:
    """The repository's own registry, so that each use a step asks for is one it allows."""
    return load(REPOSITORY / "registry" / "sources")


def receipt_of(source_id: str, use: Use, name: str, content: bytes, edition: str) -> Receipt:
    """The receipt of a made-up file that stands in for a fetched one."""
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=source_id,
        use=use,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-23T21:09:21Z",
        how=How.FETCHED,
        edition=edition,
        data_period=Period(as_at="2021-03-21" if "census" in source_id else "2021-12"),
    )


# Each file of the made-up build: its source, the use it was fetched for, its name, its edition.
FILES = {
    "lookup": ("ons-oa21-lsoa21-msoa21-lad22-lookup", Use.SCORING, LOOKUP_NAME, "V2"),
    "homes": ("ons-census-2021-housing-tables", Use.SCORING, HOMES_NAME, "Census 2021 TS044"),
    "outlines": ("ons-output-areas-2021", Use.CELLS, OUTLINES_NAME, "BGC V2"),
    "lsoa_outlines": ("ons-lsoa-2021", Use.SCORING, LSOA_OUTLINES_NAME, "BGC V5"),
    "centres": ("ons-oa-pwc-2021", Use.SCORING, CENTRES_NAME, "V4"),
}


@cache
def _contents() -> Mapping[str, bytes]:
    return {
        "lookup": lookup_csv(),
        "homes": homes_zip(),
        "outlines": oa_outlines(),
        "lsoa_outlines": lsoa_outlines(),
        "centres": centres_csv(),
    }


def contents() -> dict[str, bytes]:
    """The bytes of every file of the made-up build, as its publisher would give them."""
    return dict(_contents())


def inputs_of(folder: Path, files: Mapping[str, bytes], **changes: Registry) -> Inputs:
    """The files of a build in a store of their own, with a receipt for each."""
    store = FolderStore(folder / "store")
    receipts: list[Receipt] = []
    for which, content in files.items():
        source_id, use, name, edition = FILES[which]
        given = folder / "given" / name
        given.parent.mkdir(parents=True, exist_ok=True)
        given.write_bytes(content)
        store.put(source_id, name, given)
        receipts.append(receipt_of(source_id, use, name, content, edition))
    return Inputs(changes.get("registry", registry()), receipts, store, folder / "work")


def held(folder: Path) -> dict[str, bytes]:
    """Every file under a folder, by its path. Two of these show whether anything changed."""
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }
