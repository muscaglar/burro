"""What the tests of names and seeds share: a made-up town, in files shaped like the publishers'.

Nothing here is real. The town is Quillhaven and Tallowgate, two boroughs that
do not exist, drawn in squares of 500 metres in the North Sea. Every name is
one the made-up city of the synthetic release already holds, so none was
coined here. Every code is shaped like a publisher's and is none it has given
out.

    columns  0    1    2    3    4    5    6    7
    row 3  |    |    |    |    |    |    |    |    |
    row 2  | z  |    |    |    |    |    |    |    |     each square is one output area
    row 1  |    |    |    |    |    |    |    |    |     z is no part of London
    row 0  |    |    |    |    |    |    |    |    |
             Quillhaven, columns 0 to 4   Tallowgate

A road node stands at the middle of every square of London, and a link of 500
metres joins every two squares that lie side by side. Two nodes more stand
apart from the rest, joined to each other alone.

The files have the publishers' own layouts: the header of OS Open Names in a
document of its own, tables with no header, a mark at the start of each and
lines that end CR LF, a GeoPackage of several layers inside a zip, an index
beside each layer of the roads. So a reader that reads these reads the real
files. What they hold is made up.
"""

import atexit
import csv
import hashlib
import io
import shutil
import sqlite3
import struct
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from burro_pipeline.areas import names_draft
from burro_pipeline.areas.names_draft import Drafted, Read
from burro_pipeline.areas.seeds import Rules, Seed
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, MadeUp, lookup_csv, receipt_of, registry

EAST, NORTH, SIDE = 700_000, 400_000, 500
COLUMNS, ROWS = 8, 4
QUILLHAVEN, TALLOWGATE, OUTSIDE = "E09000901", "E09000902", "E07000901"
PUBLISHER_OF_PLACES, PUBLISHER_OF_CENTRES = "Ordnance Survey", "Greater London Authority"

NAMES, CENTRES, LINE, ROADS, OUTLINES, LOOKUP = (
    "os-open-names",
    "gla-town-centre-boundaries",
    "os-boundary-line",
    "os-open-roads",
    "ons-output-areas-2021",
    "ons-oa21-lsoa21-msoa21-lad22-lookup",
)
# The header of OS Open Names, as the document inside its zip gives it.
HEADER = (
    *("ID", "NAMES_URI", "NAME1", "NAME1_LANG", "NAME2", "NAME2_LANG", "TYPE", "LOCAL_TYPE"),
    *("GEOMETRY_X", "GEOMETRY_Y", "MOST_DETAIL_VIEW_RES", "LEAST_DETAIL_VIEW_RES"),
    *("MBR_XMIN", "MBR_YMIN", "MBR_XMAX", "MBR_YMAX"),
    *("POSTCODE_DISTRICT", "POSTCODE_DISTRICT_URI"),
    *("POPULATED_PLACE", "POPULATED_PLACE_URI", "POPULATED_PLACE_TYPE"),
    *("DISTRICT_BOROUGH", "DISTRICT_BOROUGH_URI", "DISTRICT_BOROUGH_TYPE"),
    *("COUNTY_UNITARY", "COUNTY_UNITARY_URI", "COUNTY_UNITARY_TYPE"),
    *("REGION", "REGION_URI", "COUNTRY", "COUNTRY_URI"),
    *("RELATED_SPATIAL_OBJECT", "SAME_AS_DBPEDIA", "SAME_AS_GEONAMES"),
)
ADDRESS = "https://names.made-up.example/id/"

Square = tuple[int, int]
Box = tuple[float, float, float, float]


def oa(square: Square) -> str:
    """The code of the output area of a square."""
    column, row = square
    return f"E00998{row * 10 + column + 1:03d}"


def middle(square: Square) -> tuple[float, float]:
    return EAST + (square[0] + 0.5) * SIDE, NORTH + (square[1] + 0.5) * SIDE


def box_of(square: Square, wide: int = 1, high: int = 1) -> Box:
    west, south = EAST + square[0] * SIDE, NORTH + square[1] * SIDE
    return (west, south, west + wide * SIDE, south + high * SIDE)


# The one square that is no part of London. It lies within the box that holds London.
BEYOND: Square = (0, 2)


def borough_of(square: Square) -> str:
    if square == BEYOND:
        return OUTSIDE
    return QUILLHAVEN if square[0] <= 4 else TALLOWGATE


LONDON = tuple(
    (column, row) for row in range(ROWS) for column in range(COLUMNS) if (column, row) != BEYOND
)
BOROUGH_NAMES = {QUILLHAVEN: "Quillhaven", TALLOWGATE: "Tallowgate", OUTSIDE: "Made-up District"}


# What the files hold


@dataclass(frozen=True)
class Named:
    """One record of the made-up OS Open Names."""

    number: int
    name: str
    kind: str
    at: tuple[float, float]
    box: Box | None = None
    second: str = ""
    of: str = "populatedPlace"
    # The record this one gives as its settlement, by its number, and the name it writes.
    settlement: int | None = None
    settlement_name: str = ""

    @property
    def record_id(self) -> str:
        return f"osgb9{self.number:015d}"

    @property
    def uri(self) -> str:
        return f"{ADDRESS}9{self.number:015d}"


def _near(square: Square, east: float = 0.0, north: float = 0.0) -> tuple[float, float]:
    x, y = middle(square)
    return x + east, y + north


ALDERWICK, FOXHOLT, CINDERMOOR, ESKERFOLD, FARROWMERE_WEST, FARROWMERE_EAST = 1, 2, 3, 4, 5, 6
THE_CITY, GORSEBECK, KINDLEWHARF, WEXMOOR, THRUSHCOMBE = 7, 8, 9, 10, 11
PLACES = (
    Named(ALDERWICK, "Alderwick", "Other Settlement", middle((1, 1)), box_of((0, 0), 3, 3)),
    # One link east of Alderwick: 500 m along the roads.
    Named(FOXHOLT, "Foxholt", "Suburban Area", middle((2, 1)), box_of((2, 1))),
    Named(CINDERMOOR, "Cindermoor", "Suburban Area", middle((4, 3)), box_of((3, 2), 2, 2)),
    Named(ESKERFOLD, "Eskerfold", "Suburban Area", middle((0, 3)), box_of((0, 3))),
    Named(FARROWMERE_WEST, "Farrowmere", "Suburban Area", middle((3, 0)), box_of((3, 0))),
    Named(FARROWMERE_EAST, "Farrowmere", "Village", middle((7, 3)), box_of((7, 3))),
    # A box of 8 km by 6 km round the whole town: 4,800 hectares.
    Named(THE_CITY, "Quillhaven", "City", middle((2, 2)), box_of((-4, -4), 16, 12)),
    Named(GORSEBECK, "Gorsebeck", "Village", middle(BEYOND), box_of(BEYOND)),
    Named(
        KINDLEWHARF,
        "Kindlewharf",
        "Suburban Area",
        middle((6, 1)),
        box_of((6, 1)),
        second="Lantern Yard",
    ),
    # Its town centre lies 1,250 m to the west, inside its box.
    Named(WEXMOOR, "Wexmoor", "Suburban Area", _near((7, 0), east=200), box_of((4, 0), 4, 1)),
    # On the line between two output areas.
    Named(
        THRUSHCOMBE,
        "Thrushcombe",
        "Suburban Area",
        (EAST + 2 * SIDE, NORTH + 3.5 * SIDE),
        box_of((1, 3), 2, 1),
    ),
)
STATIONS = (
    Named(21, "Alderwick", "Railway Station", _near((1, 1), east=60), of="transportNetwork"),
    # A station of the name of a place, far from the place.
    Named(22, "Eskerfold", "Railway Station", middle((7, 1)), of="transportNetwork"),
    Named(23, "Osierholm", "Railway Station", middle(BEYOND), of="transportNetwork"),
)
# Sixty roads give Alderwick as their settlement, and ten give Foxholt. Three write the
# name of Cindermoor and give the address of Eskerfold: a road is joined by the address.
ROADS_OF = ((ALDERWICK, "Alderwick", 60), (FOXHOLT, "Foxholt", 10), (ESKERFOLD, "Cindermoor", 3))


@dataclass(frozen=True)
class Centred:
    """One town centre of the made-up file."""

    record_id: str
    name: str
    rank: str
    outline: Box
    # The point the file gives. With none given, the middle of the outline.
    point: tuple[float, float] | None = None


def _round(at: tuple[float, float], half: float = 50.0) -> Box:
    return (at[0] - half, at[1] - half, at[0] + half, at[1] + half)


CENTRE_OF_ALDERWICK, HIGH_STREET, PELLAM, OF_TWO_NAMES, CENTRE_OF_WEXMOOR, OSIERHOLM = (
    "TCB90000001",
    "TCB90000002",
    "TCB90000003",
    "TCB90000004",
    "TCB90000005",
    "TCB90000006",
)
TOWN_CENTRES = (
    # It stands where the place does, on a node of the roads.
    Centred(CENTRE_OF_ALDERWICK, "Alderwick", "District", _round(middle((1, 1)))),
    Centred(HIGH_STREET, "Kindlewharf High Street", "Major", _round(_near((6, 1), north=200))),
    # No place has its name. Its class is written with another word beside the rank.
    Centred(PELLAM, "Pellam Cross", "District Centre", _round(middle((2, 3)))),
    # A label of two names, of a class below district.
    Centred(OF_TWO_NAMES, "Grapnel Dock/ Cindermoor", "Local Centre", _round(middle((4, 2)))),
    Centred(CENTRE_OF_WEXMOOR, "Wexmoor", "District", _round(middle((5, 0)))),
    # The file's own point lies outside the outline.
    Centred(OSIERHOLM, "Osierholm", "District", _round(middle((7, 2))), point=middle((5, 2))),
)


@dataclass(frozen=True)
class Warded:
    """One ward or borough of the made-up Boundary-Line."""

    code: str
    name: str
    outline: Box
    kind: str = "LBW"
    description: str = "London Borough Ward"


WARDS = (
    Warded("E05998001", "Alderwick Ward", box_of((0, 0), 2, 2)),
    Warded("E05998002", "Brackenhythe & Cindermoor Ward", box_of((3, 2), 2, 2)),
    Warded("E05998003", "Larkspur Hill Ward", box_of((5, 2), 3, 2)),
    # A ward of the name of a place, far from the place.
    Warded("E05998004", "Foxholt Ward", box_of((6, 3), 2, 1)),
    # A ward of another part of the country, which is never read.
    Warded("E05998901", f"{CANARY} Ward", box_of(BEYOND), "DIW", "District Ward"),
)
BOROUGHS = (
    Warded(QUILLHAVEN, "Quillhaven London Boro", box_of((0, 0), 5, 4), "LBO", "London Borough"),
    Warded(TALLOWGATE, "Tallowgate London Boro", box_of((5, 0), 3, 4), "LBO", "London Borough"),
    Warded(OUTSIDE, f"{CANARY} District", box_of(BEYOND), "DIS", "District"),
)


# The files, as bytes


def _lines(rows: Sequence[Sequence[object]]) -> bytes:
    """A table as OS Open Names writes one: a mark at the start, and lines that end CR LF."""
    text = io.StringIO(newline="")
    csv.writer(text, lineterminator="\r\n").writerows(rows)
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def _row(record: Named, header: Sequence[str], **more: str) -> list[str]:
    box = record.box or ("", "", "", "")
    held = {
        "ID": record.record_id,
        "NAMES_URI": record.uri,
        "NAME1": record.name,
        "NAME2": record.second,
        "TYPE": record.of,
        "LOCAL_TYPE": record.kind,
        "GEOMETRY_X": f"{record.at[0]:.0f}",
        "GEOMETRY_Y": f"{record.at[1]:.0f}",
        "MBR_XMIN": f"{box[0]:.0f}" if record.box else "",
        "MBR_YMIN": f"{box[1]:.0f}" if record.box else "",
        "MBR_XMAX": f"{box[2]:.0f}" if record.box else "",
        "MBR_YMAX": f"{box[3]:.0f}" if record.box else "",
        # A column the reader does not read. The borough is taken from the output area.
        "DISTRICT_BOROUGH": CANARY,
        "COUNTRY": "England",
    } | more
    return [held.get(name, "") for name in header]


def names_zip(
    places: Sequence[Named] = PLACES,
    stations: Sequence[Named] = STATIONS,
    header: Sequence[str] = HEADER,
    *,
    short_row: bool = False,
) -> bytes:
    """The zip of OS Open Names: a header in a document of its own, and tables with none."""
    by_number = {record.number: record for record in places}
    rows = [_row(record, header) for record in (*places, *stations)]
    number = 100
    for settlement, written, count in ROADS_OF:
        for _ in range(count if settlement in by_number else 0):
            number += 1
            road = Named(
                number, f"Made-up Road {number}", "Named Road", middle((0, 0)), box_of((0, 0))
            )
            rows.append(
                _row(
                    road,
                    header,
                    TYPE="transportNetwork",
                    POPULATED_PLACE=written,
                    POPULATED_PLACE_URI=by_number[settlement].uri,
                )
            )
    postcode = Named(999, CANARY, "Postcode", middle((1, 1)), of="other")
    rows.append(_row(postcode, header, ID="QV1 1XX"))
    if short_row:
        rows.append(rows[0][:-1])
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        archive.writestr("Doc/OS_Open_Names_Header.csv", _lines([list(header)]))
        archive.writestr("Doc/licence.txt", b"Made up for a test.\xa9")
        # Two tables, as the file is cut by squares of the grid. The second holds the rest.
        archive.writestr("Data/TV00.csv", _lines(rows[:5]))
        archive.writestr("Data/TV02.csv", _lines(rows[5:]))
    return packed.getvalue()


def rectangle(box: Box) -> bytes:
    """An outline as a GeoPackage holds it: its header, then a multipolygon of one piece."""
    west, south, east, north = box
    corners = ((west, south), (east, south), (east, north), (west, north), (west, south))
    ring = struct.pack("<I", len(corners)) + b"".join(struct.pack("<dd", *c) for c in corners)
    polygon = struct.pack("<BII", 1, 3, 1) + ring
    return b"GP" + bytes([0, 1]) + struct.pack("<i", 27700) + struct.pack("<BII", 1, 6, 1) + polygon


def point(at: tuple[float, float]) -> bytes:
    """A point as a GeoPackage holds it."""
    return b"GP" + bytes([0, 1]) + struct.pack("<i", 27700) + struct.pack("<BIdd", 1, 1, *at)


@dataclass(frozen=True)
class Layer:
    """One layer of a made-up GeoPackage."""

    name: str
    column: str
    kind: str
    fields: tuple[str, ...]
    # Each row: its geometry, the box of it for the index, and its fields in order.
    rows: tuple[tuple[bytes, Box, tuple[object, ...]], ...]
    indexed: bool = False


def geopackage(layers: Sequence[Layer]) -> bytes:
    """A GeoPackage of several layers, each on the National Grid."""
    with tempfile.TemporaryDirectory(prefix="burro-made-up-") as folder:
        path = Path(folder) / "made-up.gpkg"
        database = sqlite3.connect(path)
        # Every name in a statement is written in this file.
        database.executescript(
            """
            PRAGMA application_id = 1196444487;
            CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT, srs_id INTEGER PRIMARY KEY,
                organization TEXT, organization_coordsys_id INTEGER, definition TEXT);
            CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY, data_type TEXT,
                identifier TEXT, srs_id INTEGER);
            CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT,
                geometry_type_name TEXT, srs_id INTEGER, z TINYINT, m TINYINT);
            INSERT INTO gpkg_spatial_ref_sys
                VALUES ('British_National_Grid', 27700, 'EPSG', 27700, '');
            """
        )
        for layer in layers:
            named = ", ".join(f'"{name}"' for name in layer.fields)
            database.execute(
                f'CREATE TABLE "{layer.name}" (fid INTEGER PRIMARY KEY, "{layer.column}" BLOB, '
                f"{named})"
            )
            database.execute(
                "INSERT INTO gpkg_contents VALUES (?, 'features', ?, 27700)",
                (layer.name, layer.name),
            )
            database.execute(
                "INSERT INTO gpkg_geometry_columns VALUES (?, ?, ?, 27700, 0, 0)",
                (layer.name, layer.column, layer.kind),
            )
            if layer.indexed:
                database.execute(
                    f'CREATE VIRTUAL TABLE "rtree_{layer.name}_{layer.column}" '
                    "USING rtree(id, minx, maxx, miny, maxy)"
                )
            marks = ", ".join("?" for _ in layer.fields)
            for number, (blob, box, values) in enumerate(layer.rows, start=1):
                database.execute(
                    f'INSERT INTO "{layer.name}" VALUES (?, ?, {marks})',  # noqa: S608
                    (number, blob, *values),
                )
                if layer.indexed:
                    database.execute(
                        f'INSERT INTO "rtree_{layer.name}_{layer.column}" '  # noqa: S608
                        "VALUES (?, ?, ?, ?, ?)",
                        (number, box[0], box[2], box[1], box[3]),
                    )
        database.commit()
        database.close()
        return path.read_bytes()


def zipped(member: str, content: bytes) -> bytes:
    """A zip as Ordnance Survey packs a product: the file under `Data/`, and a document."""
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        archive.writestr(f"Data/{member}", content)
        archive.writestr("Doc/licence.txt", "Made up for a test.\n")
    return packed.getvalue()


def centres_gpkg(centres: Sequence[Centred] = TOWN_CENTRES) -> bytes:
    fields = ("layerreference", "sitename", "classification", "easting", "northing", "notes")
    rows = tuple(
        (
            rectangle(centre.outline),
            centre.outline,
            (
                centre.record_id,
                centre.name,
                centre.rank,
                (centre.point or _middle(centre.outline))[0],
                (centre.point or _middle(centre.outline))[1],
                CANARY,
            ),
        )
        for centre in centres
    )
    return geopackage([Layer("town_centres", "geom", "MULTIPOLYGON", fields, rows)])


def _middle(box: Box) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def line_zip(wards: Sequence[Warded] = WARDS, boroughs: Sequence[Warded] = BOROUGHS) -> bytes:
    """Boundary-Line: a zip that holds one GeoPackage of three layers."""
    fields = ("Name", "Area_Code", "Area_Description", "Census_Code", "File_Name")

    def rows(held: Sequence[Warded]) -> tuple[tuple[bytes, Box, tuple[object, ...]], ...]:
        return tuple(
            (
                rectangle(each.outline),
                each.outline,
                (each.name, each.kind, each.description, each.code, CANARY),
            )
            for each in held
        )

    parish = (Warded("E04998001", CANARY, box_of((0, 0)), "CPC", "Civil Parish"),)
    return zipped(
        "bdline_gb.gpkg",
        geopackage(
            [
                Layer(
                    "district_borough_unitary", "geometry", "MULTIPOLYGON", fields, rows(boroughs)
                ),
                Layer(
                    "district_borough_unitary_ward", "geometry", "MULTIPOLYGON", fields, rows(wards)
                ),
                Layer("parish", "geometry", "MULTIPOLYGON", fields, rows(parish)),
            ]
        ),
    )


def node(square: Square) -> str:
    return f"made-up-node-{square[1]:02d}-{square[0]:02d}"


# Two nodes that are joined to each other and to nothing else, north of the town.
APART = ((2, 6), (3, 6))


def roads_zip(squares: Sequence[Square] = LONDON, apart: Sequence[Square] = APART) -> bytes:
    """OS Open Roads: a zip that holds one GeoPackage of links and nodes, each with its index."""
    held = set(squares)
    links: list[tuple[bytes, Box, tuple[object, ...]]] = []
    pairs = [
        (square, (square[0] + east, square[1] + north))
        for square in sorted(held)
        for east, north in ((1, 0), (0, 1))
        if (square[0] + east, square[1] + north) in held
    ]
    pairs += [(apart[0], apart[1])] if len(apart) == 2 else []
    for number, (a, b) in enumerate(pairs, start=1):
        (west, south), (east, north) = middle(a), middle(b)
        links.append(
            (
                # The line itself is never read: the length and the nodes are.
                point(middle(a)),
                (west, south, east, north),
                (f"made-up-link-{number:04d}", node(a), node(b), float(SIDE), CANARY),
            )
        )
    nodes = tuple(
        (point(middle(square)), (*middle(square), *middle(square)), (node(square), "junction"))
        for square in (*sorted(held), *apart)
    )
    return zipped(
        "oproad_gb.gpkg",
        geopackage(
            [
                Layer(
                    "road_link",
                    "geometry",
                    "LINESTRING",
                    ("id", "start_node", "end_node", "length", "name_1"),
                    tuple(links),
                    indexed=True,
                ),
                Layer(
                    "road_node",
                    "geometry",
                    "POINT",
                    ("id", "form_of_road_node"),
                    nodes,
                    indexed=True,
                ),
            ]
        ),
    )


def outlines_gpkg(squares: Sequence[Square] = (*LONDON, BEYOND)) -> bytes:
    """The full-resolution outlines of the output areas: one layer, as the office gives it."""
    rows = tuple(
        (rectangle(box_of(square)), box_of(square), (oa(square), CANARY)) for square in squares
    )
    return geopackage(
        [Layer("OA_2021_EW_BFC_V8", "SHAPE", "MULTIPOLYGON", ("OA21CD", "LSOA21NM"), rows)]
    )


def lookup(squares: Sequence[Square] = (*LONDON, BEYOND)) -> bytes:
    return lookup_csv(
        MadeUp(
            oa=oa(square),
            lsoa=f"E01998{square[1] * 10 + square[0] + 1:03d}",
            lsoa_name=f"{BOROUGH_NAMES[borough_of(square)]} 001A",
            msoa=f"E02998{'001' if borough_of(square) == QUILLHAVEN else '002'}",
            msoa_name=f"{BOROUGH_NAMES[borough_of(square)]} 001",
            borough=borough_of(square),
            borough_name=BOROUGH_NAMES[borough_of(square)],
            homes=100,
            squares=(square,),
        )
        for square in squares
    )


# The store, and the receipts


# Each file of the made-up draft: its source, its name as the publisher gives it, its edition.
FILES: Mapping[str, tuple[str, str, str]] = {
    "names": (NAMES, "opname_csv_gb.zip", "2026-07"),
    "centres": (CENTRES, "Town_Centres_Boundaries.gpkg", ""),
    "line": (LINE, "bdline_gpkg_gb.zip", "2026-05"),
    "roads": (ROADS, "oproad_gpkg_gb.zip", "2026-04"),
    "outlines": (OUTLINES, "Output_Areas_2021_EW_BFC_V8_made_up.gpkg", "BFC V8"),
    "lookup": (LOOKUP, "OA21_LAD22_LSOA21_MSOA21_LEP22_EN_LU_V2_made_up.csv", "V2"),
}
# The file that has no receipt: its publisher states no edition and no period.
WITHOUT_A_RECEIPT = frozenset({"centres"})


@cache
def _contents() -> Mapping[str, bytes]:
    return {
        "names": names_zip(),
        "centres": centres_gpkg(),
        "line": line_zip(),
        "roads": roads_zip(),
        "outlines": outlines_gpkg(),
        "lookup": lookup(),
    }


def contents() -> dict[str, bytes]:
    """The bytes of every file of the made-up draft, as its publisher would give them."""
    return dict(_contents())


@dataclass
class Given:
    """The files of a made-up draft in a store of their own, and what stands beside them."""

    inputs: Inputs
    store: Path
    receipts: list[Receipt] = field(default_factory=list[Receipt])


def given(
    folder: Path,
    files: Mapping[str, bytes] | None = None,
    *,
    receipted: frozenset[str] | None = None,
    held_by: Registry | None = None,
) -> Given:
    """The files of a draft in a store, each with its receipt but the one that has none."""
    files = contents() if files is None else files
    store = FolderStore(folder / "store")
    receipts: list[Receipt] = []
    for which, content in files.items():
        source_id, name, edition = FILES[which]
        handed = folder / "given" / which / name
        handed.parent.mkdir(parents=True, exist_ok=True)
        handed.write_bytes(content)
        store.put(source_id, name, handed)
        has = which not in WITHOUT_A_RECEIPT if receipted is None else which in receipted
        if has:
            receipts.append(
                receipt_of(source_id, Use.GAZETTEER, name, content, edition or "made up")
            )
    inputs = Inputs(held_by or registry(), receipts, store, folder / "work")
    return Given(inputs, folder / "store", receipts)


def sha256_of(which: str) -> str:
    return hashlib.sha256(contents()[which]).hexdigest()


# The made-up draft, read once for every test that only looks at it


# The range the count of areas is to land in, for a town of a dozen places.
RULES = Rules(least=5, most=6)


@cache
def held() -> Read:
    """Everything a draft reads, read once from the made-up files."""
    folder = Path(tempfile.mkdtemp(prefix="burro-made-up-names-"))
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    return names_draft.read(given(folder).inputs, draft=True)


@cache
def drafted() -> Drafted:
    """The draft of the made-up town, by the design's own rule."""
    return names_draft.make(held(), RULES)


def seed(name: str, kind: str | None = None, draft: Drafted | None = None) -> Seed:
    """The one seed of a name, and of a kind where two places share the name."""
    found = [
        each
        for each in (draft or drafted()).seeds.seeds
        if each.name == name and kind in (None, each.place.key.kind)
    ]
    assert len(found) == 1, f"{len(found)} places are named so"
    return found[0]
