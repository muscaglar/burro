"""What the tests of the ground and of the layers share: the made-up town as shapes.

Nothing here is real. The town is the one of `flags_support.py`: squares of
100 metres, drawn as rows of letters, in the North Sea. Here each square is an
outline on the National Grid, so that what reads shapes can be tested on them.
"""

import csv
import io
import sqlite3
import struct
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from burro_pipeline.areas import context_shapes
from burro_pipeline.cells.shapes import Shape
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells import support as cells
from .flags_support import EAST, NORTH, QUILLHAVEN, SIDE, TALLOWGATE, area_id, oa

Square = tuple[int, int]


def corner(row: float, column: float) -> tuple[float, float]:
    """A corner of the grid of squares: row 0 is the northern edge, column 0 the western."""
    return EAST + column * SIDE, NORTH - row * SIDE


def block(row: float, column: float, high: float = 1, wide: float = 1) -> Shape:
    """The outline of some squares side by side: so many high, so many wide."""
    return context_shapes.outline(
        [
            corner(row, column),
            corner(row, column + wide),
            corner(row + high, column + wide),
            corner(row + high, column),
        ]
    )


def road(*corners: tuple[float, float]) -> Shape:
    """A line through some corners of the grid, each given as a row and a column."""
    return context_shapes.line([corner(row, column) for row, column in corners])


def outlines_of(rows: Sequence[str]) -> dict[str, Shape]:
    """The outline of every output area of a town drawn as rows of letters."""
    return {
        oa(row, column): block(row, column)
        for row, line in enumerate(rows)
        for column, letter in enumerate(line)
        if letter != "."
    }


def boroughs_of(rows: Sequence[str], split: int) -> dict[str, str]:
    """The borough of every output area: Tallowgate from the column `split` eastwards."""
    return {
        oa(row, column): TALLOWGATE if column >= split else QUILLHAVEN
        for row, line in enumerate(rows)
        for column, letter in enumerate(line)
        if letter != "."
    }


# Files shaped like the publishers', for the step that makes the layers
#
# The output areas and the lookup are those of the tests of cells: Quillhaven and
# Tallowgate, twelve squares in two rows, with row 1 to the north of row 0. What is
# added here is laid over them: two wards, two town centres, three roads and five names.

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


def above(row: float, column: float, high: float = 1, wide: float = 1) -> Shape:
    """The outline of some squares of the town of the tests of cells, where rows run north."""
    west, south = EAST + column * SIDE, NORTH + row * SIDE
    return context_shapes.outline(
        [
            (west, south),
            (west + wide * SIDE, south),
            (west + wide * SIDE, south + high * SIDE),
            (west, south + high * SIDE),
        ]
    )


def along(*points: tuple[float, float]) -> Shape:
    """A line through points of that town, each so many squares east and so many north."""
    return context_shapes.line(
        [(EAST + east * SIDE, NORTH + north * SIDE) for east, north in points]
    )


def _blob(shape: Shape) -> bytes:
    """A shape as a GeoPackage holds it: a header that names the National Grid, then the shape."""
    return b"GP" + bytes([0, 1]) + struct.pack("<i", 27700) + bytes(shape.wkb)


def geopackage(
    layers: Mapping[str, tuple[str, Sequence[str], Sequence[tuple[Sequence[object], Shape]]]],
    *,
    indexed: bool = True,
) -> bytes:
    """A GeoPackage of several layers. Each is its geometry column, its fields and its rows."""
    with tempfile.TemporaryDirectory(prefix="burro-made-up-") as folder:
        path = Path(folder) / "made-up.gpkg"
        database = sqlite3.connect(path)
        database.executescript(
            """
            CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY, data_type TEXT,
                identifier TEXT, srs_id INTEGER);
            CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT,
                geometry_type_name TEXT, srs_id INTEGER, z TINYINT, m TINYINT);
            """
        )
        # Every name in a statement below is written in a test.
        for layer, (column, fields, rows) in layers.items():
            named = ", ".join(f'"{name}"' for name in fields)
            database.execute(
                f'CREATE TABLE "{layer}" (fid INTEGER PRIMARY KEY, "{column}" BLOB, {named})'
            )
            database.execute(
                "INSERT INTO gpkg_contents VALUES (?, 'features', ?, 27700)", (layer, layer)
            )
            database.execute(
                "INSERT INTO gpkg_geometry_columns VALUES (?, ?, 'GEOMETRY', 27700, 0, 0)",
                (layer, column),
            )
            if indexed:
                database.execute(
                    f'CREATE VIRTUAL TABLE "rtree_{layer}_{column}" '
                    "USING rtree(id, minx, maxx, miny, maxy)"
                )
            marks = ", ".join("?" for _ in fields)
            for number, (values, shape) in enumerate(rows, start=1):
                database.execute(
                    f'INSERT INTO "{layer}" VALUES (?, ?, {marks})',  # noqa: S608
                    (number, _blob(shape), *values),
                )
                if indexed:
                    west, south, east, north = shape.bounds
                    database.execute(
                        f'INSERT INTO "rtree_{layer}_{column}" VALUES (?, ?, ?, ?, ?)',  # noqa: S608
                        (number, west, east, south, north),
                    )
        database.commit()
        database.close()
        return path.read_bytes()


def zipped(members: Mapping[str, bytes]) -> bytes:
    """A made-up zip, each member written at one time, so that it is always the same bytes."""
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        for name, content in members.items():
            archive.writestr(zipfile.ZipInfo(name, date_time=cells.WRITTEN), content)
    return packed.getvalue()


AREA_FIELDS = ("Name", "Census_Code", "Area_Code", "Area_Description")
WARDS = (
    (("Quillhaven West Ward", "E05999001", "LBW", "London Borough Ward"), above(0, 0, 2, 2)),
    (("Quillhaven East Ward", "E05999002", "LBW", "London Borough Ward"), above(0, 2, 2, 2)),
    (("Tallowgate Ward", "E05999003", "LBW", "London Borough Ward"), above(0, 4, 2, 2)),
    (("Made-up District Ward", "E05999901", "DIW", "District Ward"), above(0, 7, 2, 1)),
)
# The boroughs as the file of boundaries draws them: a row further south than the output
# areas, where the tide would be.
BOROUGHS = (
    (("Quillhaven London Boro", "E09000901", "LBO", "London Borough"), above(-3, 0, 5, 4)),
    (("Tallowgate London Boro", "E09000902", "LBO", "London Borough"), above(-3, 4, 5, 2)),
    (("Made-up District", "E07000901", "DIS", "District"), above(0, 7, 2, 1)),
)


def boundary_line() -> bytes:
    """The file of boundaries: a zip that holds one GeoPackage of several layers."""
    held = geopackage(
        {
            "district_borough_unitary_ward": ("geometry", AREA_FIELDS, WARDS),
            "district_borough_unitary": ("geometry", AREA_FIELDS, BOROUGHS),
        }
    )
    return zipped({"Data/bdline_gb.gpkg": held, "Doc/licence.txt": b"Made up for a test.\n"})


CENTRE_FIELDS = ("layerreference", "sitename", "classification", "easting", "northing")
CENTRES = (
    (
        ("SYN00000001", "Quillhaven Market", "District", EAST + 150.0, NORTH + 150.0),
        above(1.2, 1.2, 0.6, 0.6),
    ),
    (
        ("SYN00000002", "Tallowgate Cross", "Major", EAST + 450.0, NORTH + 50.0),
        above(0.2, 4.2, 0.6, 0.6),
    ),
)


def town_centres() -> bytes:
    return geopackage({"town_centres": ("geom", CENTRE_FIELDS, CENTRES)}, indexed=False)


ROAD_FIELDS = ("id", "road_classification", "road_function", "name_1", "road_classification_number")
ROADS = (
    (("syn-link-0001", "A Road", "A Road", "Tallowgate Row", "A9991"), along((0, 1), (3, 1))),
    (("syn-link-0002", "A Road", "A Road", "Tallowgate Row", "A9991"), along((3, 1), (6, 1))),
    (("syn-link-0003", "B Road", "B Road", "", "B9992"), along((2, 0), (2, 2))),
    (("syn-link-0004", "Unclassified", "Local Road", "Quillhaven Lane", ""), along((1, 0), (1, 2))),
    (("syn-link-0005", "A Road", "A Road", "Made-up Way", "A9993"), along((40, 0), (40, 2))),
)


def open_roads() -> bytes:
    held = geopackage({"road_link": ("geometry", ROAD_FIELDS, ROADS)})
    return zipped({"Data/oproad_gb.gpkg": held})


def name_row(
    record_id: str, name: str, of_type: str, kind: str, east: float, north: float
) -> dict[str, str]:
    return dict.fromkeys(NAMES_COLUMNS, "") | {
        "ID": record_id,
        "NAME1": name,
        "TYPE": of_type,
        "LOCAL_TYPE": kind,
        "GEOMETRY_X": str(round(EAST + east * SIDE)),
        "GEOMETRY_Y": str(round(NORTH + north * SIDE)),
        # A string found nowhere else, in a column that is not read.
        "POPULATED_PLACE": "Zzyzx Parva",
    }


NAMES = (
    name_row("syn0000000001", "Quillhaven Halt", "transportNetwork", "Railway Station", 1, 1),
    name_row("syn0000000002", "Tallowgate Water", "hydrography", "Inland Water", 5, 0.5),
    name_row("syn0000000003", "Quillhaven Copse", "landcover", "Woodland Or Forest", 2.5, 1.5),
    name_row("syn0000000004", "Quillhaven", "populatedPlace", "Suburban Area", 1, 1),
    name_row("ZZ99 9ZZ", "ZZ99 9ZZ", "other", "Postcode", 1, 1),
    name_row("syn0000000006", "Tallowgate Row", "transportNetwork", "Named Road", 3, 1),
    name_row("syn0000000007", "Made-up Halt", "transportNetwork", "Railway Station", 400, 1),
)


def open_names(
    rows: Sequence[Mapping[str, str]] = NAMES, columns: Sequence[str] = NAMES_COLUMNS
) -> bytes:
    """The file of names: a zip of tables with no header, and the header in a document."""

    def table(lines: Sequence[Sequence[str]]) -> bytes:
        text = io.StringIO(newline="")
        csv.writer(text, lineterminator="\r\n").writerows(lines)
        return b"\xef\xbb\xbf" + text.getvalue().encode()

    return zipped(
        {
            "Doc/OS_Open_Names_Header.csv": table([list(columns)]),
            "Doc/licence.txt": b"Made up for a test.\n",
            "Data/TA00.csv": table([[row.get(name, "") for name in columns] for row in rows]),
            "Data/TA02.csv": b"",
        }
    )


# Each file of the made-up build: its source, its name and its edition. The town centres
# have no receipt, as the real file has none.
FILES: Mapping[str, tuple[str, str, str]] = {
    "lookup": ("ons-oa21-lsoa21-msoa21-lad22-lookup", cells.LOOKUP_NAME, "V2"),
    "outlines": ("ons-output-areas-2021", cells.OUTLINES_NAME, "BGC V2"),
    "boundary_line": ("os-boundary-line", "bdline_gpkg_gb.zip", "2026-05"),
    "roads": ("os-open-roads", "oproad_gpkg_gb.zip", "2026-04"),
    "names": ("os-open-names", "opname_csv_gb.zip", "2026-07"),
    "centres": ("gla-town-centre-boundaries", "Town_Centres_Boundaries.gpkg", ""),
}


def contents() -> dict[str, bytes]:
    return {
        "lookup": cells.lookup_csv(),
        "outlines": cells.oa_outlines(),
        "boundary_line": boundary_line(),
        "roads": open_roads(),
        "names": open_names(),
        "centres": town_centres(),
    }


def inputs_of(folder: Path, files: Mapping[str, bytes], registry: Registry | None = None) -> Inputs:
    """The files of a build in a store of their own, each with a receipt but the town centres."""
    store = FolderStore(folder / "store")
    receipts: list[Receipt] = []
    for which, content in files.items():
        source_id, name, edition = FILES[which]
        given = folder / "given" / name
        given.parent.mkdir(parents=True, exist_ok=True)
        given.write_bytes(content)
        store.put(source_id, name, given)
        if edition:
            receipts.append(cells.receipt_of(source_id, Use.GAZETTEER, name, content, edition))
    return Inputs(registry or cells.registry(), receipts, store, folder / "work")


# A made-up draft of that town: the curated files, as a draft writes them

ALDERWICK, BRACKENHYTHE = area_id("A"), area_id("B")
AREAS = (
    "area_id",
    "slug",
    "name",
    "primary_borough",
    "seed_record",
    "review_state",
    "superseded_by",
)
GIVEN = ("oa21cd", "area_id", "basis", "evidence", "decided_by", "decided_on", "reason")
EVIDENCE = (
    *("area_id", "name", "role", "source_id", "record_id", "as_written", "field", "locates"),
    *("data_date", "retrieved_on", "snapshot_sha256", "checked", "chosen_by", "chosen_on"),
)
SEEDS = ("area_id", "name", "easting", "northing")


def table(folder: Path, name: str, columns: Sequence[str], rows: Sequence[Mapping[str, object]]):
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / name).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in columns} for row in rows)


def evidence(area: str, name: str, source: str, **more: str) -> dict[str, str]:
    return {
        "area_id": area,
        "name": name,
        "role": "primary",
        "source_id": source,
        "as_written": name,
        "checked": "true",
    } | more


def a_draft(folder: Path, **changed: Sequence[Mapping[str, object]]) -> Path:
    """A draft of the made-up town: Quillhaven is Alderwick, and Tallowgate is Brackenhythe."""
    units = sorted(cells.LONDON, key=lambda unit: unit.oa)
    rows: dict[str, Sequence[Mapping[str, object]]] = {
        "areas.csv": [
            {"area_id": ALDERWICK, "slug": "alderwick", "name": "Alderwick"},
            {"area_id": BRACKENHYTHE, "slug": "brackenhythe", "name": "Brackenhythe"},
            {"area_id": "syn-n0009", "name": "Cindermoor", "superseded_by": ALDERWICK},
        ],
        "oa_to_area.csv": [
            {
                "oa21cd": unit.oa,
                "area_id": ALDERWICK if unit.borough_name == "Quillhaven" else BRACKENHYTHE,
                "basis": "auto",
                "evidence": f"margin={3 * number};second={BRACKENHYTHE}",
            }
            for number, unit in enumerate(units)
        ],
        "name_evidence.csv": [
            evidence(ALDERWICK, "Alderwick", "os-open-names"),
            evidence(ALDERWICK, "Alderwick", "os-boundary-line"),
            evidence(BRACKENHYTHE, "Brackenhythe", "os-open-names"),
            evidence(BRACKENHYTHE, "Brackenhythe", "gla-town-centre-boundaries"),
            evidence(BRACKENHYTHE, "Brackenhythe", "ons-output-areas-2021", checked="false"),
            evidence(BRACKENHYTHE, "Brack", "ons-output-areas-2021", role="alias"),
        ],
        "seeds.csv": [
            {"area_id": ALDERWICK, "name": "Alderwick", "easting": 700_150, "northing": 400_100},
            {
                "area_id": BRACKENHYTHE,
                "name": "Brackenhythe",
                "easting": 700_500,
                "northing": 400_100,
            },
        ],
    } | changed
    columns = {
        "areas.csv": AREAS,
        "oa_to_area.csv": GIVEN,
        "name_evidence.csv": EVIDENCE,
        "seeds.csv": SEEDS,
    }
    for name, held_rows in rows.items():
        table(folder, name, columns[name], held_rows)
    return folder
