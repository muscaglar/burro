"""Main roads, from the publisher's network to a figure for each area.

Every file here is made up. The roads are laid out as the publisher lays out
its own: a zip that holds `Data/oproad_gb.gpkg` and two notes, a layer
`road_link` with the publisher's 22 columns, lines in two dimensions on the
National Grid, and an index of where each line lies. What it holds is made up:
a few straight roads in the North Sea, where the made-up town of the tests of
cells stands.

    northing
    400600                                     ......... an access road, class Unknown
    400400   --------------------------------- a B road
    400200   ................................. a local road
    400000   ================================= the A road, which ends at 702000
    399700   = = = = = = = = = = = = = = = = = an A road in a tunnel
             699000                  702000    703000: a motorway, north to south

The town is twelve output areas in three areas. Each test puts their centres
where it needs them, so that each figure can be worked out by hand.

    Quillhaven 001   homes 110, 120, 130, 140   500 in all
    Quillhaven 002   homes 150, 160, 170, 180   660 in all
    Tallowgate 001   homes 190, 200, 210, 220   820 in all
"""

import hashlib
import io
import math
import re
import sqlite3
import struct
import tempfile
import zipfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import cache
from itertools import pairwise
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import Dimension, FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import measures
from burro_pipeline.derive import road_major_exposure as roads
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.road_major_exposure import Exposure
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography, How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CENTRES_COLUMNS, FILES, LONDON, contents, held, receipt_of, registry

# A string found nowhere else. If a refusal repeats what a file holds, this shows up in it.
CANARY = "Zzyzx Parva"
ZIP_NAME, MEMBER = "oproad_gpkg_gb.zip", "Data/oproad_gb.gpkg"
EDITION, CHANGED = "2026-04", "2026-04-07T12:03:02.137Z"
# The columns of the publisher's layer, in its own order, each with its type.
FIELDS = (
    ("id", "TEXT"),
    ("fictitious", "BOOLEAN"),
    ("road_classification", "TEXT"),
    ("road_function", "TEXT"),
    ("form_of_way", "TEXT"),
    ("road_classification_number", "TEXT"),
    ("name_1", "TEXT"),
    ("name_1_lang", "TEXT"),
    ("name_2", "TEXT"),
    ("name_2_lang", "TEXT"),
    ("road_structure", "TEXT"),
    ("length", "REAL"),
    ("length_uom", "TEXT"),
    ("loop", "BOOLEAN"),
    ("primary_route", "BOOLEAN"),
    ("trunk_road", "BOOLEAN"),
    ("start_node", "TEXT"),
    ("end_node", "TEXT"),
    ("road_number_toid", "TEXT"),
    ("road_name_toid", "TEXT"),
)
# What the made-up file says its roads cover: the North Sea round the town.
COVERS = (690_000.0, 390_000.0, 710_000.0, 510_000.0)
CAN_INDEX = "ENABLE_RTREE" in {
    str(row[0]) for row in sqlite3.connect(":memory:").execute("PRAGMA compile_options")
}
needs_an_index = pytest.mark.skipif(not CAN_INDEX, reason="this SQLite cannot make an index")
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
OAS = tuple(unit.oa for unit in LONDON)

Place = tuple[float, float]


@dataclass(frozen=True)
class Road:
    """One made-up stretch of road."""

    kind: str
    line: tuple[Place, ...]
    structure: str | None = None
    fictitious: object = 0
    # What the file says it is long. With none, what its line is long, to a whole metre.
    length: object = None
    # The line as the file holds it, where a test needs bytes that are no line.
    blob: bytes | None = None
    # Whether the file holds no line for it at all.
    without_a_line: bool = False


def straight(kind: str, *line: Place, structure: str | None = None) -> Road:
    return Road(kind, line, structure)


A_ROAD = straight("A Road", (699_000, 400_000), (700_000, 400_000), (702_000, 400_000))
MOTORWAY = straight("Motorway", (703_000, 399_000), (703_000, 401_000))
B_ROAD = straight("B Road", (699_000, 400_400), (702_000, 400_400))
LOCAL = straight("Unclassified", (699_000, 400_200), (702_000, 400_200))
ACCESS = straight("Unknown", (702_000, 400_600), (703_000, 400_600))
TUNNEL = straight("A Road", (699_000, 399_700), (702_000, 399_700), structure="Road In Tunnel")
# An A road far from the town. It is in the file, and no build of the town reads it.
FAR_AWAY = straight("A Road", (699_000, 500_000), (702_000, 500_000))
# It ends three hundredths of a metre short of the box the roads are read in. The index
# holds a box a little wider than a line, so the index alone would give it.
JUST_OUTSIDE = straight("A Road", (699_800, 400_900), (699_849.97, 400_900))
ROADS = (A_ROAD, MOTORWAY, B_ROAD, LOCAL, ACCESS, TUNNEL, FAR_AWAY, JUST_OUTSIDE)

# Where the centre of each output area stands, in the order of their codes.
PLACED: tuple[Place, ...] = (
    # Quillhaven 001: two near the A road, one of them at 100 metres exactly, and two far.
    (700_100, 400_060),
    (700_200, 400_100),
    (700_300, 400_100.5),
    (700_400, 400_300),
    # Quillhaven 002: two beside the tunnel and far from the A road, one near, one far.
    (701_100, 399_800),
    (701_200, 399_750),
    (701_300, 400_020),
    (701_400, 400_250),
    # Tallowgate 001: one near the motorway, one at 100 metres from the end of the A road,
    # one a metre further, and one near the access road alone.
    (702_950, 400_500),
    (702_060, 400_080),
    (702_061, 400_080),
    (702_500, 400_700),
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
    made: Sequence[Road] = ROADS,
    *,
    indexed: bool = CAN_INDEX,
    changed: str = CHANGED,
    fields: Sequence[tuple[str, str]] = FIELDS,
    lines: str = "LINESTRING",
    grid: int = 27700,
    z: int = 0,
    covers: Sequence[object] = COVERS,
    index_holds: int | None = None,
    layer: str = "road_link",
) -> bytes:
    """The roads as a GeoPackage with the publisher's layout. What it holds is made up."""
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
                "geometry" {lines}, {named});
            CREATE TABLE "road_node" ("fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                "geometry" POINT, "id" TEXT, "form_of_road_node" TEXT);
            INSERT INTO gpkg_spatial_ref_sys
                VALUES ('OSGB 1936 / British National Grid', 27700, 'EPSG', 27700, '', NULL);
            INSERT INTO gpkg_geometry_columns VALUES ('{layer}', 'geometry', '{lines}',
                {grid}, {z}, 0);
            INSERT INTO gpkg_geometry_columns VALUES ('road_node', 'geometry', 'POINT',
                27700, 0, 0);
            INSERT INTO gpkg_contents VALUES ('road_node', 'features', 'road_node', '',
                '{changed}', NULL, NULL, NULL, NULL, 27700);
            """  # noqa: S608
        )
        database.execute(
            "INSERT INTO gpkg_contents VALUES (?, 'features', ?, '', ?, ?, ?, ?, ?, ?)",
            (layer, layer, changed, *covers, grid),
        )
        if indexed:
            database.executescript(
                """
                CREATE VIRTUAL TABLE "rtree_road_link_geometry"
                    USING rtree(id, minx, maxx, miny, maxy);
                INSERT INTO gpkg_extensions VALUES ('road_link', 'geometry', 'gpkg_rtree_index',
                    'http://www.geopackage.org/spec120/#extension_rtree', 'write-only');
                """
            )
        held_by = {name for name, _ in fields}
        for number, road in enumerate(made, start=1):
            east, north = [x for x, _ in road.line], [y for _, y in road.line]
            shape = line_blob(road.line) if road.blob is None else road.blob
            row: dict[str, object] = {
                "geometry": None if road.without_a_line else shape,
                "id": f"made-up-{number}",
                "fictitious": road.fictitious,
                "road_classification": road.kind,
                "road_function": CANARY,
                "form_of_way": "Single Carriageway",
                "name_1": CANARY,
                "road_structure": road.structure,
                "length": round(drawn(road.line)) if road.length is None else road.length,
                "length_uom": "m",
            }
            kept = {name: value for name, value in row.items() if name in {"geometry", *held_by}}
            database.execute(
                f'INSERT INTO "{layer}" ({", ".join(kept)}) '  # noqa: S608
                f"VALUES ({', '.join('?' * len(kept))})",
                tuple(kept.values()),
            )
            if indexed and (index_holds is None or number <= index_holds) and road.line:
                database.execute(
                    'INSERT INTO "rtree_road_link_geometry" VALUES (?, ?, ?, ?, ?)',
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
            # A fixed day, so that the same roads are always the same bytes.
            archive.writestr(zipfile.ZipInfo(name, (2026, 4, 7, 12, 0, 0)), content)
    return packed.getvalue()


@cache
def the_roads() -> bytes:
    return zipped()


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


def roads_receipt(content: bytes, name: str = ZIP_NAME, edition: str = EDITION) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=roads.SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-23T21:51:17Z",
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
    packed = the_roads() if packed is None else packed
    files = contents() | {"centres": centres_at(on(*PLACED) if placed is None else placed)}
    receipts = [
        receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3])
        for which, content in files.items()
    ]
    every = [
        *zip(receipts, files.values(), strict=True),
        (roads_receipt(packed, edition=edition), packed),
        *more,
    ]
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")


def built(
    folder: Path, packed: bytes | None = None, placed: Mapping[str, Place] | None = None
) -> Exposure:
    inputs = inputs_of(folder, packed, placed)
    return roads.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Exposure:
    """The town with its roads, as most tests read it. It is built once."""
    return built(tmp_path_factory.mktemp("town"))


def refused(folder: Path, packed: bytes, edition: str = EDITION) -> LockError:
    """The refusal of a file, which names a rule and repeats nothing the file holds."""
    inputs = inputs_of(folder, packed, edition=edition)
    with pytest.raises(LockError) as stopped:
        roads.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


def with_one(road: Road) -> bytes:
    """The roads of the town, and one more."""
    return zipped(network((*ROADS, road)))


# The parser


def test_the_roads_round_the_homes_are_read_each_with_its_class(town: Exposure):
    found = town.roads
    assert (found.rows, len(found.links)) == (8, 6)
    assert found.by_class == {
        "Motorway": 1,
        "A Road": 2,
        "B Road": 1,
        "Classified Unnumbered": 0,
        "Unclassified": 1,
        "Not Classified": 0,
        "Unknown": 1,
    }
    assert (found.edition, found.covers) == (EDITION, COVERS)
    assert found.file_id == roads_receipt(the_roads()).file_id


def test_a_main_road_is_a_motorway_or_an_a_road_that_is_not_in_a_tunnel(town: Exposure):
    main = sorted(link.line for link in town.roads.links if link.main)
    assert main == [
        (699_000, 400_000, 700_000, 400_000, 702_000, 400_000),
        (703_000, 399_000, 703_000, 401_000),
    ]
    assert town.roads.in_tunnel == 1


def test_the_lines_add_up_to_what_the_file_says_they_are_long(town: Exposure):
    assert town.roads.metres_stated == 3_000 * 4 + 2_000 + 1_000
    assert town.roads.metres_drawn == town.roads.metres_stated


def test_a_road_far_from_every_home_is_not_read(town: Exposure):
    lines = {link.line for link in town.roads.links}
    assert not any(northing == 500_000 for line in lines for northing in line[1::2])


@pytest.mark.parametrize("order", ["<", ">"])
def test_a_line_is_read_in_either_byte_order(order: str):
    blob = line_blob(((1.5, 2.5), (3.5, 4.5), (5.5, 6.5)), order=order)
    assert roads.line_of(blob) == (1.5, 2.5, 3.5, 4.5, 5.5, 6.5)


@pytest.mark.parametrize(
    "blob",
    [
        b"",
        b"GP",
        line_blob(((1, 2), (3, 4)))[:-1],
        line_blob(((1, 2), (3, 4))) + b"\x00",
        line_blob(((1, 2),)),
        line_blob(((1, 2), (3, 4)), kind=1),
        line_blob(((1, 2), (3, 4)), kind=1002),
        line_blob(((1, 2), (3, 4)), grid=4326),
        line_blob(((1, 2), (math.nan, 4))),
        line_blob(((1, 2), (math.inf, 4))),
        b"XX" + line_blob(((1, 2), (3, 4)))[2:],
    ],
    ids=[
        "empty",
        "short",
        "cut",
        "long",
        "one_point",
        "point",
        "line_with_height",
        "another_grid",
        "nan",
        "inf",
        "not_a_geopackage",
    ],
)
def test_what_is_not_a_line_in_two_dimensions_on_the_grid_is_not_read(blob: bytes):
    with pytest.raises((ValueError, struct.error)):
        roads.line_of(blob)


@pytest.mark.parametrize("missing", roads.COLUMNS[1:])
def test_a_file_without_a_column_is_refused_and_the_column_is_named(tmp_path: Path, missing: str):
    fields = [(CANARY if name == missing else name, kind) for name, kind in FIELDS]
    stopped = refused(tmp_path, zipped(network(fields=fields)))
    assert f"the column {missing} is missing" in str(stopped)


def test_every_column_that_is_read_is_one_the_publishers_layer_holds():
    assert set(roads.COLUMNS) <= {"geometry", *(name for name, _ in FIELDS)}
    # No name of a road and no number of one is read.
    assert not {"name_1", "name_2", "road_classification_number"} & set(roads.COLUMNS)


@pytest.mark.parametrize(
    ("road", "words"),
    [
        (straight(CANARY, (700_000, 400_100), (700_100, 400_100)), "a class that is not known"),
        (straight("a road", (700_000, 400_100), (700_100, 400_100)), "a class that is not known"),
        (
            straight("A Road", (700_000, 400_100), (700_100, 400_100), structure=CANARY),
            "a structure that is not known",
        ),
        (replace(LOCAL, fictitious=1), "marked as fictitious"),
        (replace(LOCAL, fictitious=CANARY), "neither there nor not there"),
        (replace(LOCAL, length=-1), "a length is no length"),
        (replace(LOCAL, length=CANARY), "a length is no length"),
        (replace(LOCAL, length=30_000), "not as long as it says"),
        (replace(LOCAL, blob=CANARY.encode()), "not a line in two dimensions"),
        (replace(LOCAL, blob=line_blob(LOCAL.line, kind=1002)), "not a line in two dimensions"),
    ],
    ids=[
        "class",
        "class_in_another_case",
        "structure",
        "fictitious",
        "fictitious_is_no_mark",
        "length_below_nought",
        "length_is_words",
        "lengths_do_not_add_up",
        "line_is_words",
        "line_with_height",
    ],
)
def test_a_road_the_parser_has_not_met_stops_the_build(tmp_path: Path, road: Road, words: str):
    assert words in str(refused(tmp_path, with_one(road)))


def test_a_road_with_no_line_is_refused_wherever_in_the_file_it_is(tmp_path: Path):
    """The index holds no road that has no line, so such a road would never be seen."""
    nowhere = replace(FAR_AWAY, without_a_line=True)
    assert "a road has no line" in str(refused(tmp_path, with_one(nowhere)))


@pytest.mark.parametrize(
    ("made", "words"),
    [
        (lambda: network(layer="made_up_layer"), "no layer of roads"),
        (lambda: network(grid=4326), "no layer of roads"),
        (lambda: network(lines="MULTILINESTRING"), "not lines in two dimensions"),
        (lambda: network(lines="POINT"), "not lines in two dimensions"),
        (lambda: network(z=1), "not lines in two dimensions"),
        (lambda: network(changed="2025-10-07T12:03:02.137Z"), "not the month of its receipt"),
        (lambda: network(changed="2026-05-01T00:00:00.000Z"), "not the month of its receipt"),
        (lambda: network(changed=CANARY), "not the month of its receipt"),
        (lambda: network(covers=(None, None, None, None)), "does not say what it covers"),
        (
            lambda: network(covers=(710_000.0, 390_000.0, 690_000.0, 510_000.0)),
            "does not say what it covers",
        ),
        (
            lambda: network(covers=(CANARY, 390_000.0, 710_000.0, 510_000.0)),
            "does not say what it covers",
        ),
        (lambda: network(()), "it holds no road"),
    ],
    ids=[
        "no_layer",
        "layer_on_another_grid",
        "many_lines",
        "points",
        "lines_with_height",
        "an_earlier_edition",
        "a_later_month",
        "no_day",
        "no_box",
        "a_box_inside_out",
        "a_box_of_words",
        "no_road",
    ],
)
def test_a_file_that_is_not_laid_out_as_the_roads_are_is_refused(
    tmp_path: Path, made: Callable[[], bytes], words: str
):
    assert words in str(refused(tmp_path, zipped(made())))


def test_a_file_of_another_edition_than_its_receipt_says_is_refused(tmp_path: Path):
    """The period a figure is shown with is the receipt's, so the file must say the same."""
    assert "not the month of its receipt" in str(refused(tmp_path, the_roads(), "2026-10"))
    later = zipped(network(changed="2026-10-06T09:00:00.000Z"))
    inputs = inputs_of(tmp_path / "later", later, edition="2026-10")
    assert roads.build(inputs, spine.build(inputs)).metric.vintage == "2026-10"


@pytest.mark.parametrize(
    "packed",
    [
        CANARY.encode(),
        zipped(members=()),
        zipped(members=(MEMBER, "Data/made_up_too.gpkg")),
        zipped(CANARY.encode()),
    ],
    ids=["not_a_zip", "no_geopackage", "two_geopackages", "not_a_geopackage"],
)
def test_a_file_that_is_no_zip_of_one_geopackage_is_refused(tmp_path: Path, packed: bytes):
    refused(tmp_path, packed)


def test_a_column_the_measure_does_not_read_is_never_used(tmp_path: Path, town: Exposure):
    """A column beside the five changes nothing, whatever it holds."""
    wider = built(tmp_path, zipped(network(fields=(*FIELDS, ("made_up_note", "TEXT")))))
    assert wider.worked == town.worked


def test_the_order_of_the_rows_changes_nothing(tmp_path: Path, town: Exposure):
    turned = built(tmp_path, zipped(network(tuple(reversed(ROADS)))))
    assert turned.worked == town.worked
    assert turned.roads.links == town.roads.links


# The index


@needs_an_index
def test_the_files_own_index_is_used_where_it_has_one(town: Exposure):
    assert town.roads.indexed


def test_without_an_index_every_row_is_read_and_the_same_roads_are_kept(
    tmp_path: Path, town: Exposure
):
    plain = built(tmp_path, zipped(network(indexed=False)))
    assert not plain.roads.indexed
    assert plain.roads.links == town.roads.links
    assert plain.roads.by_class == town.roads.by_class
    assert plain.worked == town.worked


@needs_an_index
def test_a_road_just_outside_the_box_is_left_out_though_the_index_gives_it(town: Exposure):
    """The index holds a box a little wider than a line. The line itself decides."""
    assert JUST_OUTSIDE.line[1][0] < roads.around_of(PLACED)[0]
    assert not any(link.line[1] == 400_900 for link in town.roads.links)


@needs_an_index
def test_an_index_that_does_not_hold_every_road_is_refused(tmp_path: Path):
    """A road the index left out would be a main road that no home is near."""
    stopped = refused(tmp_path, zipped(network(index_holds=len(ROADS) - 1)))
    assert "its index does not hold every road" in str(stopped)


# The gate, the receipt and the store


def without_scoring() -> Registry:
    """The repository's registry, with the roads no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.GAZETTEER,)})
        if source.id == roads.SOURCE
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_the_roads_are_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=without_scoring())
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        roads.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    # Nothing more was handed over: not the roads, and not the centres.
    assert inputs.opened == before
    assert not (tmp_path / "work" / roads_receipt(the_roads()).file_id).exists()


def test_the_roads_are_registered_for_scoring_and_so_is_every_file_behind_a_figure(
    town: Exposure,
):
    for source_id in town.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_roads_are_told_from_another_file_of_their_source(tmp_path: Path, town: Exposure):
    """The publisher gives the roads in other formats too. One of those is not opened."""
    other = zipped(network((FAR_AWAY,)))
    inputs = inputs_of(tmp_path, more=[(roads_receipt(other, name="made_up_roads.zip"), other)])
    found = roads.build(inputs, spine.build(inputs))
    assert found.roads.file_id == roads_receipt(the_roads()).file_id
    assert found.worked == town.worked


def test_two_editions_of_the_roads_are_told_apart_by_the_one_that_is_asked_for(tmp_path: Path):
    later = zipped(network(changed="2026-10-06T09:00:00.000Z"))
    inputs = inputs_of(tmp_path, more=[(roads_receipt(later, edition="2026-10"), later)])
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        roads.build(inputs, found)
    assert stopped.value.rule == "input_has_one_receipt"
    assert roads.build(inputs, found, edition="2026-04").metric.vintage == "2026-04"
    assert roads.build(inputs, found, edition="2026-10").metric.vintage == "2026-10"


def test_nothing_is_written_to_the_store_and_the_unpacked_copy_is_removed(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    roads.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before
    assert [path.name for path in (tmp_path / "work").rglob("*.gpkg")] == []


def test_the_unpacked_copy_is_removed_when_the_file_is_refused(tmp_path: Path):
    refused(tmp_path, with_one(replace(LOCAL, fictitious=1)))
    assert [path.name for path in (tmp_path / "work").rglob("*.gpkg")] == []


# How far a home is from a road

LINE = (0.0, 0.0, 1_000.0, 0.0)
BENT = (0.0, 0.0, 1_000.0, 0.0, 1_000.0, 1_000.0)


@pytest.mark.parametrize(
    ("point", "within"),
    [
        ((500.0, 0.0), True),
        ((500.0, 99.9), True),
        ((500.0, 100.0), True),
        ((500.0, -100.0), True),
        ((500.0, 100.1), False),
        # Beyond the end of the line, the distance is to its end.
        ((1_060.0, 80.0), True),
        ((1_061.0, 80.0), False),
        ((-100.0, 0.0), True),
        ((-100.1, 0.0), False),
        ((-80.0, -60.0), True),
        # Off the end and to one side: 90 metres from the line drawn on, and 127 from its end.
        ((-90.0, -90.0), False),
        ((1_090.0, 90.0), False),
    ],
)
def test_a_point_is_near_a_line_within_a_hundred_metres_of_it(point: Place, within: bool):
    assert (roads.near({"home": point}, [LINE], 100) == {"home"}) is within


def test_a_point_is_near_a_road_where_it_is_near_any_stretch_of_it():
    points = {"beside_the_first": (500.0, 50.0), "beside_the_second": (950.0, 500.0)}
    assert roads.near(points, [BENT], 100) == set(points)
    assert roads.near({"inside_the_bend": (850.0, 150.0)}, [BENT], 100) == set()


def test_a_line_that_is_one_point_twice_is_a_point():
    assert roads.near({"home": (3.0, 4.0)}, [(0.0, 0.0, 0.0, 0.0)], 5) == {"home"}
    assert roads.near({"home": (3.0, 4.1)}, [(0.0, 0.0, 0.0, 0.0)], 5) == set()


def test_a_long_line_is_near_a_point_far_from_both_its_ends():
    assert roads.near({"home": (5_000.0, 80.0)}, [(0.0, 0.0, 10_000.0, 0.0)], 100) == {"home"}


def test_with_no_line_no_point_is_near():
    assert roads.near({"home": (0.0, 0.0)}, [], 100) == set()


def test_the_order_of_the_points_and_of_the_lines_changes_nothing():
    points = {f"home-{at}": (at * 37.0, (at % 7) * 41.0) for at in range(60)}
    lines = [LINE, BENT, (200.0, 300.0, 400.0, 250.0), (0.0, 120.0, 900.0, 260.0)]
    turned = dict(reversed(list(points.items())))
    found = roads.near(points, lines, 100)
    assert 0 < len(found) < len(points)
    assert roads.near(turned, list(reversed(lines)), 100) == found


def test_the_box_the_roads_are_read_in_reaches_as_far_as_a_road_is_looked_for():
    assert roads.REACH >= roads.METRES
    assert roads.around_of([(10.0, 20.0), (30.0, 5.0)]) == (-240.0, -245.0, 280.0, 270.0)


# The figure


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


def test_an_area_is_given_the_share_of_its_homes_that_are_near_a_main_road(town: Exposure):
    # 110 and 120 of the 500 homes are in an output area near the A road.
    assert (110 + 120) * 100 / 500 == 46.0
    assert town.worked[QUILLHAVEN_1] == Worked(46.0, 4, 4, 1.0, State.PRESENT)


def test_a_centre_at_a_hundred_metres_is_near_and_one_half_a_metre_on_is_not(town: Exposure):
    assert [town.near[oa] for oa in OAS[:4]] == [True, True, False, False]


def test_a_figure_is_given_to_one_decimal_place(town: Exposure):
    # 170 of 660 homes: 25.7575 and so on. 190 and 200 of 820: 47.5609 and so on.
    assert town.worked[QUILLHAVEN_2] == Worked(25.8, 4, 4, 1.0, State.PRESENT)
    assert town.worked[TALLOWGATE] == Worked(47.6, 4, 4, 1.0, State.PRESENT)


def test_a_road_in_a_tunnel_is_not_a_road_a_home_is_near(town: Exposure):
    """Two centres stand 100 and 50 metres from the A road in a tunnel, and far from any other."""
    assert [town.near[oa] for oa in OAS[4:6]] == [False, False]


def test_a_b_road_and_a_local_road_are_not_main_roads(town: Exposure):
    """The fourth centre is 100 metres from a B road and from a local road."""
    assert not town.near[OAS[3]]


def test_a_motorway_outside_the_box_of_the_homes_counts_where_a_home_is_near_it(town: Exposure):
    """A road beyond the edge of London is still a road beside a home at the edge."""
    assert max(east for east, _ in PLACED) < MOTORWAY.line[0][0]
    assert town.near[OAS[8]]


def test_the_end_of_a_road_is_as_near_as_the_road_runs(town: Exposure):
    """The A road ends 100 metres from the tenth centre, and 100.6 from the eleventh."""
    assert [town.near[oa] for oa in OAS[9:11]] == [True, False]


def test_an_area_with_no_home_near_a_main_road_is_at_nought_and_nought_is_a_figure(
    tmp_path: Path,
):
    far = on(*[(700_500.0, 400_250.0)] * 4, *PLACED[4:])
    assert built(tmp_path, placed=far).worked[QUILLHAVEN_1] == Worked(0.0, 4, 4, 1.0, State.PRESENT)


def test_an_output_area_with_no_centre_is_not_taken_to_be_far(tmp_path: Path):
    placed = {oa: place for oa, place in on(*PLACED).items() if oa != OAS[0]}
    found = built(tmp_path, placed=placed)
    # The first output area holds 110 of the area's 500 homes. 120 of the other 390 are near.
    assert OAS[0] not in found.near
    assert found.worked[QUILLHAVEN_1] == Worked(30.8, 3, 4, round(390 / 500, 6), State.PARTIAL)


def test_a_centre_outside_what_the_file_covers_has_no_verdict(tmp_path: Path):
    """The file says its roads reach no further east than 701000, so the rest is not known."""
    covers = (690_000.0, 390_000.0, 701_000.0, 510_000.0)
    found = built(tmp_path, zipped(network(covers=covers)))
    assert sorted(found.near) == list(OAS[:4])
    assert found.worked[QUILLHAVEN_1] == Worked(46.0, 4, 4, 1.0, State.PRESENT)
    assert found.worked[QUILLHAVEN_2] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert found.worked[TALLOWGATE] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)


def test_below_half_the_homes_no_figure_is_given(tmp_path: Path):
    placed = {oa: place for oa, place in on(*PLACED).items() if oa not in OAS[1:4]}
    found = built(tmp_path, placed=placed).worked[QUILLHAVEN_1]
    assert found == Worked(None, 1, 4, round(110 / 500, 6), State.BELOW_THRESHOLD)


def test_a_file_whose_roads_do_not_reach_the_homes_is_refused_and_no_nought_is_given(
    tmp_path: Path,
):
    """With no road of any class near, a share of nought would be a gap read as a figure."""
    stopped = refused(tmp_path, zipped(network((A_ROAD, MOTORWAY, B_ROAD, LOCAL, TUNNEL))))
    assert "its roads do not reach the homes of the build" in str(stopped)


def test_one_centre_far_from_every_road_is_counted_and_still_has_its_verdict(tmp_path: Path):
    """A centre may stand where no road is. More than 1 in 100 of them is a file with a hole."""
    many = {f"home-{at}": (700_000.0 + at, 400_050.0) for at in range(99)}
    lone = {"far": (700_000.0, 410_000.0)}
    found = built(tmp_path).roads
    verdicts, unreached = roads.verdicts(found, many | lone)
    assert (unreached, verdicts["far"]) == (1, False)
    assert sum(verdicts.values()) == 99
    with pytest.raises(LockError, match="do not reach"):
        roads.verdicts(found, dict(list(many.items())[:98]) | lone)


# The evidence


def test_every_area_has_a_row_of_evidence_that_holds_its_figure(town: Exposure):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/road_major_exposure" for area in (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
    ]
    assert [row.value for row in town.rows] == [46.0, 25.8, 47.6]
    assert [row.state for row in town.rows] == [State.PRESENT] * 3
    assert [(row.units_used, row.units_expected) for row in town.rows] == [(4, 4)] * 3


def test_an_area_with_no_figure_has_a_row_that_says_why(tmp_path: Path):
    placed = {oa: place for oa, place in on(*PLACED).items() if oa not in OAS[1:4]}
    row = built(tmp_path, placed=placed).rows[0]
    assert (row.value, row.state, row.has_a_value) == (None, State.BELOW_THRESHOLD, False)


def test_a_row_names_the_roads_the_centres_the_lookup_and_the_homes(town: Exposure):
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    assert sorted(by_source) == sorted([roads.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES])
    for row in town.rows:
        assert row.inputs == tuple(sorted(by_source.values()))
        assert row.derivation_id == "homes_within_100m@1"
        assert row.retrieved_on == "2026-09-23"
        # From the day of the census, which the weights are of, to the end of the roads' month.
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2026-04-30")


def test_the_figures_are_marked_as_measured_and_the_method_states_the_distance():
    assert roads.METHODS == (roads.METHOD,)
    assert roads.METHOD.kind is Kind.MEASURED
    assert roads.METHOD.parameters["metres"] == roads.METRES == 100


def test_the_measure_says_that_the_file_is_keyed_by_lines(town: Exposure):
    assert town.geography is Geography.LINE


def test_the_evidence_of_the_measure_has_no_loose_end(town: Exposure):
    """Every row names a method and files that the evidence of a release would hold."""
    evidence = Evidence.of("lon-2026-10-02-01", town.files, roads.METHODS, town.rows)
    assert len(evidence.rows) == 3


# The name, the unit and the sentences


def test_the_measure_is_cores_measure_of_main_roads_and_a_build_carries_it(town: Exposure):
    """Core gained the feature with the vibes, and the figure is what core defines.

    Core names it by a main road. The sentence of the measure says which roads
    are main, that the distance is a straight line, and that it is to the line
    the file draws along the road.
    """
    assert roads.FEATURE is FeatureId.ROAD_MAJOR_EXPOSURE
    carried = {measure.feature: measure for measure in measures.MEASURES}
    assert carried[roads.FEATURE].source == roads.SOURCE == "os-open-roads"
    assert carried[roads.FEATURE].waits_on == ()
    assert not carried[roads.FEATURE].in_squares
    assert says_what_core_says(town.metric)


def test_the_row_of_the_catalogue_says_what_core_says_of_the_measure(town: Exposure):
    metric, core = town.metric, FEATURES[FeatureId.ROAD_MAJOR_EXPOSURE]
    assert metric.feature_id is FeatureId.ROAD_MAJOR_EXPOSURE
    assert metric.label == core.label == "Share of homes within 100 m of a main road"
    assert (metric.unit, metric.polarity) == ("%", Polarity.LESS)
    assert metric.dimension is Dimension.AIR_NOISE
    # A home is placed at the centre of its output area, so the figure is of output areas.
    assert metric.native_resolution is core.native_resolution is NativeResolution.OA
    assert metric.vintage == "2026-04"
    assert metric.source_ids == tuple(sorted(metric.source_ids))
    assert len(metric.source_ids) == 4


def test_no_area_is_ranked_on_the_figure_by_itself(town: Exposure):
    """The row switches the measure off for ranking by itself. Its values are still shown.

    The design expects main roads to follow who lives somewhere. No audit of the figure
    has been run, and none is to be since 2026-09-25 (ADR 0006, as amended): whether an
    area is ranked on it alone is the founder's to say. A vibe still rests on it: core
    places a vibe on every part of its recipe that a release holds.
    """
    assert town.metric.rankable is False
    assert roads.RANKABLE is False


def test_the_definition_is_one_sentence_that_says_what_the_figure_is_and_is_not(town: Exposure):
    definition = town.metric.definition
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        "Ordnance Survey",
        "OS Open Roads of 2026-04",
        "within 100 metres",
        "a motorway or an A road",
        "centre of its census output area",
        "the census of 2021",
        "in a straight line",
        "a road in a tunnel is left out",
        "to 1 decimal place",
        "not a measure of traffic",
    ):
        assert words in definition
    # Every parameter of the method stands in it, as it stands in the method's own sentence.
    assert f"{roads.METHOD.parameters['metres']} metres" in definition


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Exposure):
    sentences = (town.metric.definition, town.metric.label, *roads.CANNOT_SEE)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(roads.CANNOT_SEE) == 2
    for sentence in roads.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)


def test_it_says_that_a_home_is_placed_at_a_centre_and_that_class_is_not_traffic():
    assert "not at its front door" in roads.CANNOT_SEE[0]
    assert "not how busy it is" in roads.CANNOT_SEE[1]
