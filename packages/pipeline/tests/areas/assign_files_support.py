"""What the tests of the ground share: a made-up town on a river, in files shaped like the real.

Nothing here is real. The town stands in the North Sea, in two boroughs that do
not exist. Its wards and its seeds take names of the made-up city of the
synthetic release. Every code is shaped like a publisher's and is none a
publisher has given out.

The files have the publishers' own layouts: a lookup and a table of centres as
the statistics office writes them, its boundaries twice over as a GeoPackage of
one layer, and Ordnance Survey's Boundary-Line and roads each as a zip that
holds a GeoPackage of several layers, each layer with its index, and its names
of places as a zip of tables with no header.

    northing
    440 +----+----+----+----+----+----+
        | 21 | 22 | 23 | 24 | 25 | 26 |    row 3     Tallowgate
    340 +----+----+----+----+----+----+
        | 15 | 16 | 17 | 18 | 19 | 20 |    row 2
    240 +----+----+~~~~~~~~~~~~~~~~~~~+
        | 13 | 14 |  the tidal water     a bridge at column 4, and a road
    200 +----+----+~~~~~~~~~~~~~~~~~~~+    that runs out over the water and back
        |  7 |  8 |  9 | 10 | 11 | 12 |    row 1     Quillhaven
    100 +----+----+----+----+----+----+
        |  1 |  2 |  3 |  4 |  5 |  6 |    row 0
      0 +----+----+----+----+----+----+
        0   100  200  300  400  500  600   easting

The water ends at easting 200. West of it two low output areas, 13 and 14, join
the banks, as the banks of a river meet above where the tide ends.
"""

import csv
import io
import sqlite3
import struct
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from itertools import pairwise
from pathlib import Path

from burro_pipeline.areas.assign_files import Reading, SeedPoint
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, CENTRES_COLUMNS, LOOKUP_COLUMNS, receipt_of, registry

EAST, NORTH = 700_000.0, 400_000.0
SIDE, WIDE = 100.0, 40.0
COLUMNS, ENDS_AT = 6, 2
QUILLHAVEN, TALLOWGATE, ELSEWHERE = "E09000901", "E09000902", "E07000901"
BOROUGH_NAMES = {
    QUILLHAVEN: "Quillhaven",
    TALLOWGATE: "Tallowgate",
    ELSEWHERE: "Made-up District",
}
# The wards, each with the box it covers: west, south, east, north.
WARDS = {
    "E05999001": ("Alderwick Ward", (0.0, 0.0, 300.0, 240.0)),
    "E05999002": ("Cindermoor Ward", (300.0, 0.0, 600.0, 220.0)),
    "E05999003": ("Dulcimer Green Ward", (0.0, 240.0, 300.0, 440.0)),
    "E05999004": ("Eskerfold & Foxholt Ward", (300.0, 220.0, 600.0, 440.0)),
}
# For a made-up town: the water is small, and so is every piece of its roads.
READING = Reading(margin=500.0, least_water=1.0, least_piece=3)

Box = tuple[float, float, float, float]
Point = tuple[float, float]


@dataclass(frozen=True)
class Made:
    """One made-up output area: its code, its borough and the box it covers."""

    oa: str
    borough: str
    box: Box
    # Its place in the drawing above: the column, and the row. The low ones are row -1.
    square: tuple[int, int]

    @property
    def centre(self) -> Point:
        west, south, east, north = self.box
        return (west + east) / 2, (south + north) / 2


def _town() -> tuple[Made, ...]:
    found: list[Made] = []

    def add(column: int, row: int, south: float, high: float, borough: str) -> None:
        box = (column * SIDE, south, (column + 1) * SIDE, south + high)
        found.append(Made(f"E00999{len(found) + 1:03d}", borough, box, (column, row)))

    for row in (0, 1):
        for column in range(COLUMNS):
            add(column, row, row * SIDE, SIDE, QUILLHAVEN)
    for column in range(ENDS_AT):
        add(column, -1, 2 * SIDE, WIDE, QUILLHAVEN)
    for row in (2, 3):
        for column in range(COLUMNS):
            add(column, row, row * SIDE + WIDE, SIDE, TALLOWGATE)
    return tuple(found)


TOWN = _town()
# One output area of a district that is no part of London, far to the east.
OUTSIDE = Made("E00999901", ELSEWHERE, (900.0, 0.0, 1000.0, 100.0), (9, 0))
AT = {made.square: made for made in TOWN}


def oa(column: int, row: int) -> str:
    return AT[(column, row)].oa


def node(column: int, row: int) -> str:
    return f"syn-node-{AT[(column, row)].oa[-3:]}"


def on_the_grid(point: Point) -> Point:
    return EAST + point[0], NORTH + point[1]


def record(number: int) -> str:
    """The id of a record of a place, shaped like Ordnance Survey's and none it has given."""
    return f"osgb99990000{number:08d}"


def address(number: int) -> str:
    """The address of a record of a place, which ends in the digits of its id."""
    return f"http://data.made-up.example/id/99990000{number:08d}"


def seed(number: int, name: str, column: int, row: int, weight: float = 6.0) -> SeedPoint:
    """A seed at the centre of one output area, with a name of the made-up city."""
    at = on_the_grid(AT[(column, row)].centre)
    return SeedPoint(f"syn-n{number:04d}", at, weight, name, record(number))


# Four seeds: one on each bank beside the bridge, and one on each bank in the west.
SEEDS = (
    seed(1, "Alderwick", 0, 0),
    seed(2, "Cindermoor", 5, 0),
    seed(3, "Eskerfold", 4, 2),
    seed(4, "Dulcimer Green", 1, 3),
)


# A geometry, as a GeoPackage holds it


def _header(grid: int = 27700) -> bytes:
    return b"GP" + bytes([0, 1]) + struct.pack("<i", grid)


def _points(points: Sequence[Point]) -> bytes:
    return struct.pack("<I", len(points)) + b"".join(
        struct.pack("<dd", *on_the_grid(point)) for point in points
    )


def outline_blob(boxes: Sequence[Box], grid: int = 27700) -> bytes:
    """Boxes as one outline. A box has a corner wherever the town's lines cross its sides."""
    polygons = b""
    for west, south, east, north in boxes:
        ring: list[Point] = []
        for start, end in (
            ((west, south), (east, south)),
            ((east, south), (east, north)),
            ((east, north), (west, north)),
            ((west, north), (west, south)),
        ):
            ring += _along(start, end)
        ring.append((west, south))
        polygons += struct.pack("<BII", 1, 3, 1) + _points(ring)
    return _header(grid) + struct.pack("<BII", 1, 6, len(boxes)) + polygons


# Every easting and northing a line of the town runs along.
EASTINGS = tuple(column * SIDE for column in range(COLUMNS + 1))
NORTHINGS = (0.0, 100.0, 200.0, 220.0, 240.0, 340.0, 440.0)


def _along(start: Point, end: Point) -> list[Point]:
    """The corners on one side of a box, from its start up to but not with its end."""
    if start[1] == end[1]:
        low, high = sorted((start[0], end[0]))
        between = [(x, start[1]) for x in EASTINGS if low < x < high]
    else:
        low, high = sorted((start[1], end[1]))
        between = [(start[0], y) for y in NORTHINGS if low < y < high]
    if (end[0], end[1]) < (start[0], start[1]):
        between.reverse()
    return [start, *between]


def line_blob(points: Sequence[Point]) -> bytes:
    return _header() + struct.pack("<BI", 1, 2) + _points(points)


def point_blob(point: Point) -> bytes:
    return _header() + struct.pack("<BI", 1, 1) + struct.pack("<dd", *on_the_grid(point))


# A GeoPackage


# One row of a layer: its geometry, the box it fits in, and a value for each field.
Row = tuple[bytes, Box, tuple[object, ...]]


@dataclass(frozen=True)
class Layer:
    """One layer of a GeoPackage: its name, its fields, its rows and whether it has an index."""

    name: str
    kind: str
    column: str
    fields: tuple[tuple[str, str], ...]
    rows: tuple[Row, ...]
    indexed: bool = True


def geopackage(layers: Sequence[Layer]) -> bytes:
    """A GeoPackage of several layers, each with its index as Ordnance Survey's have."""
    with tempfile.TemporaryDirectory(prefix="burro-made-up-") as folder:
        path = Path(folder) / "made-up.gpkg"
        database = sqlite3.connect(path)
        # Every name in the script is written in this file.
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
            named = ", ".join(f'"{name}" {kind}' for name, kind in layer.fields)
            database.executescript(
                f"""
                CREATE TABLE "{layer.name}" (fid INTEGER PRIMARY KEY,
                    "{layer.column}" {layer.kind}, {named});
                INSERT INTO gpkg_contents
                    VALUES ('{layer.name}', 'features', '{layer.name}', 27700);
                INSERT INTO gpkg_geometry_columns
                    VALUES ('{layer.name}', '{layer.column}', '{layer.kind}', 27700, 0, 0);
                """  # noqa: S608
            )
            if layer.indexed:
                # The index is a table of boxes by row. A reader asks it as it asks any table.
                database.execute(
                    f'CREATE TABLE "rtree_{layer.name}_{layer.column}" '
                    "(id INTEGER PRIMARY KEY, minx REAL, maxx REAL, miny REAL, maxy REAL)"
                )
            marks = ", ".join("?" for _ in layer.fields)
            for number, (blob, box, values) in enumerate(layer.rows, start=1):
                database.execute(
                    f'INSERT INTO "{layer.name}" VALUES (?, ?, {marks})',  # noqa: S608
                    (number, blob, *values),
                )
                if layer.indexed:
                    west, south = on_the_grid((box[0], box[1]))
                    east, north = on_the_grid((box[2], box[3]))
                    database.execute(
                        f'INSERT INTO "rtree_{layer.name}_{layer.column}" VALUES (?, ?, ?, ?, ?)',  # noqa: S608
                        (number, west, east, south, north),
                    )
        database.commit()
        database.close()
        return path.read_bytes()


def zipped(inside: str, content: bytes) -> bytes:
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        archive.writestr("Doc/licence.txt", "Made up for a test.\n")
        archive.writestr(inside, content)
    return packed.getvalue()


# The files of the statistics office


def lookup_csv(town: Sequence[Made]) -> bytes:
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, LOOKUP_COLUMNS, lineterminator="\r\n")
    table.writeheader()
    for number, made in enumerate(town, start=1):
        table.writerow(
            {
                "OA21CD": made.oa,
                "LSOA21CD": f"E01999{number:03d}",
                "LSOA21NM": f"{BOROUGH_NAMES[made.borough]} {number:03d}A",
                "MSOA21CD": f"E02999{number:03d}",
                "MSOA21NM": f"{BOROUGH_NAMES[made.borough]} {number:03d}",
                "LEP22CD1": "E37999901",
                "LEP22NM1": CANARY,
                "LEP22CD2": "",
                "LEP22NM2": "",
                "LAD22CD": made.borough,
                "LAD22NM": BOROUGH_NAMES[made.borough],
                "ObjectId": number,
            }
        )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def centres_csv(town: Sequence[Made]) -> bytes:
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, CENTRES_COLUMNS, lineterminator="\n")
    table.writeheader()
    for number, made in enumerate(town, start=1):
        east, north = on_the_grid(made.centre)
        table.writerow(
            {
                "X": f"{east:.4f}",
                "Y": f"{north:.4f}",
                "FID": number,
                "OA21CD": made.oa,
                "GlobalID": f"{{made-up-{number}}}",
                "GlobalID_2": f"{{made-up-{number}-2}}",
            }
        )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def outlines_gpkg(town: Sequence[Made], layer: str) -> bytes:
    rows = tuple((outline_blob([made.box]), made.box, (made.oa, CANARY)) for made in town)
    fields = (("OA21CD", "TEXT(9)"), ("LSOA21NM", "TEXT(40)"))
    return geopackage([Layer(layer, "MULTIPOLYGON", "SHAPE", fields, rows, indexed=False)])


# The files of Ordnance Survey

LINE_FIELDS = (
    ("Name", "TEXT(100)"),
    ("Area_Code", "TEXT(3)"),
    ("Area_Description", "TEXT(50)"),
    ("Census_Code", "TEXT(9)"),
)


def boundary_line() -> bytes:
    """Two boroughs, each drawn to the middle of the water, a district, and four wards."""
    boroughs = (
        ("Quillhaven London Boro", "LBO", QUILLHAVEN, (0.0, 0.0, 600.0, 220.0)),
        ("Tallowgate London Boro", "LBO", TALLOWGATE, (0.0, 220.0, 600.0, 440.0)),
        ("Made-up District", "DIS", ELSEWHERE, (900.0, 0.0, 1000.0, 100.0)),
    )
    wards = tuple((name, "LBW", code, box) for code, (name, box) in WARDS.items())

    def rows(units: Sequence[tuple[str, str, str, Box]]) -> tuple[Row, ...]:
        return tuple(
            (outline_blob([box]), box, (name, kind, CANARY, code))
            for name, kind, code, box in units
        )

    return geopackage(
        [
            Layer(
                "district_borough_unitary", "MULTIPOLYGON", "geometry", LINE_FIELDS, rows(boroughs)
            ),
            Layer(
                "district_borough_unitary_ward",
                "MULTIPOLYGON",
                "geometry",
                LINE_FIELDS,
                rows(wards),
            ),
            Layer("high_water", "LINESTRING", "geometry", (("Name", "TEXT(100)"),), ()),
        ]
    )


LINK_FIELDS = (
    ("id", "TEXT(36)"),
    ("name_1", "TEXT(150)"),
    ("road_classification", "TEXT(21)"),
    ("length", "REAL"),
    ("start_node", "TEXT(36)"),
    ("end_node", "TEXT(36)"),
)
NODE_FIELDS = (("id", "TEXT(36)"), ("form_of_road_node", "TEXT(21)"))
# A yard of two nodes that joins no road, beside output area 3.
YARD = {"syn-node-yard-a": (250.0, 40.0), "syn-node-yard-b": (250.0, 60.0)}
# A quay on the north bank, at the end of a road of its own, 5 m from the water.
QUAY = {"syn-node-quay": (450.0, 245.0)}


def _links() -> list[tuple[str, str, list[Point]]]:
    """Every link: a node at the centre of each output area, joined to the ones beside it."""
    found: list[tuple[str, str, list[Point]]] = []

    def join(a: tuple[int, int], b: tuple[int, int], through: Sequence[Point] = ()) -> None:
        found.append((node(*a), node(*b), [AT[a].centre, *through, AT[b].centre]))

    for row in (0, 1, 2, 3):
        for column in range(COLUMNS - 1):
            join((column, row), (column + 1, row))
    for column in range(COLUMNS):
        join((column, 0), (column, 1))
        join((column, 2), (column, 3))
    join((0, -1), (1, -1))
    for column in range(ENDS_AT):
        join((column, 1), (column, -1))
        join((column, -1), (column, 2))
    # The bridge, from one bank to the other.
    join((4, 1), (4, 2))
    # A road of the south bank that runs out over the water and back.
    join((5, 1), (3, 1), through=((550.0, 210.0), (350.0, 210.0)))
    found.append(("syn-node-yard-a", "syn-node-yard-b", list(YARD.values())))
    found.append(("syn-node-quay", node(4, 2), [QUAY["syn-node-quay"], AT[(4, 2)].centre]))
    return found


def _box(points: Sequence[Point]) -> Box:
    return (
        min(x for x, _ in points),
        min(y for _, y in points),
        max(x for x, _ in points),
        max(y for _, y in points),
    )


def _length(points: Sequence[Point]) -> float:
    return sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 for a, b in pairwise(points))


def roads(turned: bool = False) -> bytes:
    """The roads. `turned` writes every row in the other order, and each link end for end."""
    links = _links()
    nodes = {node(*made.square): made.centre for made in TOWN} | YARD | QUAY
    if turned:
        links = [(end, start, points[::-1]) for start, end, points in reversed(links)]
        nodes = dict(reversed(nodes.items()))
    link_rows = tuple(
        (
            line_blob(points),
            _box(points),
            (
                f"syn-link-{start[-3:]}-{end[-3:]}",
                CANARY,
                "Unclassified",
                _length(points),
                start,
                end,
            ),
        )
        for start, end, points in links
    )
    node_rows = tuple(
        (point_blob(point), (*point, *point), (name, "junction")) for name, point in nodes.items()
    )
    return geopackage(
        [
            Layer("road_link", "LINESTRING", "geometry", LINK_FIELDS, link_rows),
            Layer("road_node", "POINT", "geometry", NODE_FIELDS, node_rows),
            Layer("motorway_junction", "POINT", "geometry", (("id", "TEXT(36)"),), ()),
        ]
    )


# The names of places

NAMES_COLUMNS = (
    *("ID", "NAMES_URI", "NAME1", "NAME1_LANG", "NAME2", "NAME2_LANG", "TYPE", "LOCAL_TYPE"),
    *("GEOMETRY_X", "GEOMETRY_Y", "MOST_DETAIL_VIEW_RES", "LEAST_DETAIL_VIEW_RES"),
    *("MBR_XMIN", "MBR_YMIN", "MBR_XMAX", "MBR_YMAX", "POSTCODE_DISTRICT"),
    *("POSTCODE_DISTRICT_URI", "POPULATED_PLACE", "POPULATED_PLACE_URI"),
    *("POPULATED_PLACE_TYPE", "DISTRICT_BOROUGH", "DISTRICT_BOROUGH_URI"),
    *("DISTRICT_BOROUGH_TYPE", "COUNTY_UNITARY", "COUNTY_UNITARY_URI", "COUNTY_UNITARY_TYPE"),
    *("REGION", "REGION_URI", "COUNTRY", "COUNTRY_URI", "RELATED_SPATIAL_OBJECT"),
    *("SAME_AS_DBPEDIA", "SAME_AS_GEONAMES"),
)
# Every record of a road: the square it lies in, how far east of the square's centre,
# and the settlement it names by its number. Nought is a road that names none.
ROAD_RECORDS: tuple[tuple[tuple[int, int], float, int], ...] = (
    # Two roads in each square of the south east name the second seed's place.
    *(((column, row), east, 2) for column in (3, 4, 5) for row in (0, 1) for east in (-10.0, 10.0)),
    # Three more in one of them name the first seed's place, which are the most there.
    *(((3, 0), east, 1) for east in (-20.0, 0.0, 20.0)),
    # Roads of the north east name the third seed's place, and one names no settlement.
    *(((column, 2), 5.0, 3) for column in (4, 5)),
    ((5, 3), 5.0, 0),
    # A road names another place, which has the name of the fourth seed and is not it.
    ((0, 3), 5.0, 44),
)
NAMED = {1: "Alderwick", 2: "Cindermoor", 3: "Eskerfold", 44: "Dulcimer Green"}


def _record(kind: tuple[str, str], at: Point, settlement: int) -> dict[str, object]:
    east, north = on_the_grid(at)
    empty: dict[str, object] = dict.fromkeys(NAMES_COLUMNS, "")
    return empty | {
        "NAME1": CANARY,
        "TYPE": kind[0],
        "LOCAL_TYPE": kind[1],
        "GEOMETRY_X": f"{east:.0f}",
        "GEOMETRY_Y": f"{north:.0f}",
        "POPULATED_PLACE": NAMED.get(settlement, ""),
        "POPULATED_PLACE_URI": address(settlement) if settlement else "",
        "DISTRICT_BOROUGH": CANARY,
    }


def names_zip(turned: bool = False) -> bytes:
    """The names of places: a zip of tables with no header, and the header in a document."""
    road = ("transportNetwork", "Named Road")
    rows = [
        _record(road, (AT[square].centre[0] + east, AT[square].centre[1]), settlement)
        for square, east, settlement in ROAD_RECORDS
    ]
    # What is not a road is not read, though it names a settlement: a postcode, a station.
    rows.append(_record(("other", "Postcode"), AT[(0, 0)].centre, 2))
    rows.append(_record(("transportNetwork", "Railway Station"), AT[(0, 0)].centre, 2))
    # A road outside London.
    rows.append(_record(road, OUTSIDE.centre, 2))
    for number, row in enumerate(rows, start=1):
        row["ID"] = f"osgb99995{number:011d}"
        row["NAMES_URI"] = f"http://data.made-up.example/id/99995{number:011d}"
    if turned:
        rows.reverse()

    def written(some: Sequence[Mapping[str, object]]) -> str:
        text = io.StringIO(newline="")
        table = csv.DictWriter(text, NAMES_COLUMNS, lineterminator="\r\n")
        table.writerows(some)
        return "\ufeff" + text.getvalue()

    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        header = "\ufeff" + ",".join(NAMES_COLUMNS) + "\r\n"
        archive.writestr("Doc/OS_Open_Names_Header.csv", header)
        archive.writestr("Doc/licence.txt", b"Made up for a test. \xa9\n")
        archive.writestr("Data/XA00.csv", written(rows[::2]))
        archive.writestr("Data/XA20.csv", written(rows[1::2]))
        archive.writestr("readme.txt", "Made up for a test.\n")
    return packed.getvalue()


# The files of a build, in a store

# Each file: its source, the use it was fetched for, its name and its edition.
FILES: Mapping[str, tuple[str, Use, str, str]] = {
    "lookup": (
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        Use.SCORING,
        "OA21_LAD22_LSOA21_MSOA21_LEP22_EN_LU_V2_made_up.csv",
        "V2",
    ),
    "centres": (
        "ons-oa-pwc-2021",
        Use.SCORING,
        "Output_Areas_(December_2021)_EW_Population_Weighted_Centroids_(V4)_made_up.csv",
        "V4",
    ),
    "to_draw": (
        "ons-output-areas-2021",
        Use.CELLS,
        "Output_Areas_2021_EW_BGC_V2_made_up.gpkg",
        "BGC V2",
    ),
    "to_place": (
        "ons-output-areas-2021",
        Use.CELLS,
        "Output_Areas_2021_EW_BFC_V8_made_up.gpkg",
        "BFC V8",
    ),
    "boundary_line": ("os-boundary-line", Use.GAZETTEER, "bdline_gpkg_gb.zip", "2026-05"),
    "roads": ("os-open-roads", Use.SCORING, "oproad_gpkg_gb.zip", "2026-04"),
    "names": ("os-open-names", Use.GAZETTEER, "opname_csv_gb.zip", "2026-07"),
}


@cache
def _contents() -> Mapping[str, bytes]:
    everywhere = (*TOWN, OUTSIDE)
    return {
        "lookup": lookup_csv(everywhere),
        "centres": centres_csv(everywhere),
        "to_draw": outlines_gpkg(everywhere, "OA_2021_EW_BGC_V2"),
        "to_place": outlines_gpkg(everywhere, "OA_2021_EW_BFC_V8"),
        "boundary_line": zipped("Data/bdline_gb.gpkg", boundary_line()),
        "roads": zipped("Data/oproad_gb.gpkg", roads()),
        "names": names_zip(),
    }


def contents() -> dict[str, bytes]:
    """The bytes of every file of the made-up build, as its publisher would give them."""
    return dict(_contents())


def receipts_of(files: Mapping[str, bytes]) -> list[Receipt]:
    return [
        receipt_of(*FILES[which][:3], content, FILES[which][3]) for which, content in files.items()
    ]


def inputs_of(folder: Path, files: Mapping[str, bytes], given: Registry | None = None) -> Inputs:
    """The files of a build in a store of their own, with a receipt for each."""
    store = FolderStore(folder / "store")
    for which, content in files.items():
        source_id, _, name, _ = FILES[which]
        held = folder / "given" / which / name
        held.parent.mkdir(parents=True, exist_ok=True)
        held.write_bytes(content)
        store.put(source_id, name, held)
    return Inputs(given or registry(), receipts_of(files), store, folder / "work")
