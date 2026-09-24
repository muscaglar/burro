"""The files of the first real build, as their publishers gave them.

Every other test of cells runs on made-up files. These read the real ones, and
are skipped where the store of fetched files is not. The store is named by BURRO_STORE_FOLDER,
and each file is read through its receipt in `data/receipts/`.

They hold the counts and a few sums, so that a publisher's file that changes is
noticed. A number here is a count or a sum over all of London, and never a row.
Each was counted on 2026-09-23.

Nothing is written to the store. A file is copied out of it to be read.
"""

import csv
import io
import math
import os
import zipfile
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, land, outline, shapes, spine
from burro_pipeline.cells.outline import Outline
from burro_pipeline.cells.spine import Spine
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch.kinds import read_only
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use
from burro_pipeline.release.write import canonical_json

from .support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)
VOA = "voa-council-tax-stock-of-properties"
AIR = "defra-pcm-background-air"


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    work = tmp_path_factory.mktemp("real")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def outlines(real: Inputs, found: Spine) -> dict[str, Outline]:
    return outline.build(real, found)


# The spine


def test_london_is_as_many_output_areas_lsoas_msoas_and_boroughs_as_the_design_expects(
    found: Spine,
):
    assert found.counts() == {
        "output_areas": 26_369,
        "lsoas": 4_994,
        "msoas": 1_002,
        "boroughs": 33,
        "areas": 1_002,
        "homes": 3_423_767,
    }


def test_every_area_has_homes_and_no_output_area_has_none(found: Spine):
    assert min(cell.homes for cell in found.cells) == 38
    homes = dict.fromkeys(found.weights.areas, 0)
    for cell in found.cells:
        homes[found.area_of[cell.oa]] += cell.homes
    assert (min(homes.values()), max(homes.values())) == (2_032, 6_000)


def test_every_code_is_a_code_of_the_census_of_2021(real: Inputs, found: Spine):
    """The boundaries, the centres and the table of homes hold every code of the lookup."""
    oas = {cell.oa for cell in found.cells}
    assert (
        set(outline.read(real.open(outline.BOUNDARIES, Use.CELLS, edition="BGC V2"), found)) == oas
    )
    assert set(land.build(real, found).of_lsoa) == set(found.lsoas)
    assert set(centres.build(real, found)) == oas


# The outlines


def test_every_area_has_an_outline_made_of_all_its_output_areas(outlines: dict[str, Outline]):
    assert len(outlines) == 1_002
    assert all(found.units_used == found.units_expected for found in outlines.values())
    assert sum(found.units_used for found in outlines.values()) == 26_369


def test_the_outlines_are_as_many_points_and_pieces_as_were_counted(
    outlines: dict[str, Outline],
):
    assert sum(found.points for found in outlines.values()) == 73_988
    assert sum(found.pieces for found in outlines.values()) == 1_027
    assert sum(found.pieces > 1 for found in outlines.values()) == 19
    written = canonical_json(outline.feature_collection(outlines))
    assert 1_700_000 < len(written) < 1_750_000


def test_every_area_has_a_neighbour_and_each_names_the_other(outlines: dict[str, Outline]):
    beside = {area: found.neighbours for area, found in outlines.items()}
    assert all(area in beside[other] for area, others in beside.items() for other in others)
    counts = sorted(len(others) for others in beside.values())
    assert (counts[0], counts[len(counts) // 2], counts[-1]) == (2, 6, 13)


def test_every_outline_is_where_london_is(outlines: dict[str, Outline]):
    for found in outlines.values():
        longitude, latitude = found.centre
        assert -0.52 < longitude < 0.34 and 51.28 < latitude < 51.70


def test_a_point_is_turned_to_where_the_publisher_says_it_is(real: Inputs, found: Spine):
    """The boundaries give a point of each output area on the grid, and the same point as
    latitude and longitude. The fixed operation is held to within 3 metres of the second."""
    opened = real.open(outline.BOUNDARIES, Use.CELLS, edition="BGC V2")
    database = read_only(opened.path)
    try:
        rows = database.execute(
            'SELECT OA21CD, BNG_E, BNG_N, "LONG", LAT FROM OA_2021_EW_BGC_V2'
        ).fetchall()
    finally:
        database.close()
    apart = [
        shapes.metres_between(shapes.longitude_and_latitude(east, north), (longitude, latitude))
        for code, east, north, longitude, latitude in rows
        if code in found.area_of
    ]
    assert len(apart) == 26_369
    assert max(apart) < 3.0 and 1.5 < math.fsum(apart) / len(apart) < 2.5


# The land


def test_the_land_of_london_is_what_was_measured(real: Inputs, found: Spine):
    measured = land.build(real, found)
    assert round(math.fsum(measured.of_lsoa.values()), 1) == 157_333.6
    assert round(math.fsum(measured.of_area.values()), 1) == 157_333.6
    areas = sorted(measured.of_area.values())
    assert (round(areas[0], 1), round(areas[-1], 1)) == (29.4, 2_244.8)


# The three tables of homes by band, kind and age


def table(opened: Opened) -> tuple[list[str], int]:
    """The names of the columns of the one table in a zip, and how many rows stand under them."""
    with opened.text(".csv") as text:
        rows = csv.reader(text)
        return next(rows), sum(1 for _ in rows)


@pytest.mark.parametrize(
    ("named", "columns", "rows", "last"),
    [
        ("CTSOP1.1", 14, 43_296, "all_properties"),
        ("CTSOP3.1", 49, 392_014, "all_properties"),
        ("CTSOP4.1", 35, 392_014, "all_properties"),
    ],
)
def test_a_table_of_homes_is_the_shape_that_was_described(
    real: Inputs, named: str, columns: int, rows: int, last: str
):
    opened = real.open(VOA, Use.SCORING, named=lambda name: name.startswith(named))
    names, count = table(opened)
    assert names[:4] == ["geography", "ba_code", "ecode", "area_name"]
    assert (len(names), count, names[-1]) == (columns, rows, last)
    with zipfile.ZipFile(opened.path) as archive:
        inside = sorted(name for name in archive.namelist() if not name.endswith("/"))
    assert [Path(name).suffix for name in inside] == [".csv", ".xlsx"]


def test_the_tables_of_homes_are_on_the_lsoas_of_2021(real: Inputs, found: Spine):
    """Every LSOA of London is there once for each band, and none is left over."""
    opened = real.open(VOA, Use.SCORING, named=lambda name: name.startswith("CTSOP3.1"))
    codes: dict[str, int] = {}
    homes = 0
    with opened.text(".csv") as text:
        for row in opened.rows(text, ("geography", "ecode", "band", "all_properties")):
            if row["geography"] == "LSOA" and row["ecode"] in found.area_of_lsoa:
                codes[row["ecode"]] = codes.get(row["ecode"], 0) + 1
                homes += int(row["all_properties"]) if row["band"] == "All" else 0
    assert set(codes) == set(found.lsoas)
    assert set(codes.values()) == {9}
    assert homes == 3_840_040


# The grid of nitrogen dioxide


def test_the_grid_of_air_starts_with_five_lines_of_notes(real: Inputs, found: Spine):
    opened = real.open(AIR, Use.SCORING, named=lambda name: name.startswith("mapno2"))
    with opened.text() as text:
        lines = text.read().splitlines()
    assert [line.split(",")[0] for line in lines[:5]] == [
        "no2",
        "2024",
        "annual mean",
        "ug m-3",
        "",
    ]
    assert lines[5] == "gridcode,x,y,no22024"
    rows = list(csv.reader(io.StringIO("\n".join(lines[6:]))))
    assert len(rows) == 254_905
    # Each square is named by its middle, and the homes of London all stand on a square.
    assert all(int(x) % 1000 == 500 and int(y) % 1000 == 500 for _, x, y, _ in rows)
    squares = {(int(x) - 500, int(y) - 500) for _, x, y, value in rows if value != "MISSING"}
    points = centres.build(real, found)
    assert all(
        (math.floor(x / 1000) * 1000, math.floor(y / 1000) * 1000) in squares
        for x, y in points.values()
    )
