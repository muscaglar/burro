"""Five shares of land, worked out from the table its publisher gave.

Every other test of the measures runs on a made-up table. These read the real
one, and are skipped where the store of fetched files is not. The store is
named by BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the table to what the step `describe` gave of it before any figure
was read: where the names of its columns stand, and how many rows stand under
them. They hold the figures to what any table of land must keep: a share is
between nought and a hundred, five shares of one area add up to no more than
all of it, every figure is the one plain arithmetic gives, and the LSOAs of
London add up to the publisher's own row for London.

They hold the counts and, for each measure, London's lowest, middle and
highest figure, so that a publisher's file that changes is noticed. None is
said of a named area. Each was worked out on 2026-09-24, by a program. No
person has held any of them against a map.

Contains public sector information licensed under the Open Government Licence
v3.0. Source: Office for National Statistics licensed under the Open
Government Licence v.3.0.

Nothing is written to the store. A file is copied out of it to be read.
"""

import math
import os
import re
import statistics
from collections import Counter
from collections.abc import Mapping
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import pytest
from burro_core.ids import FeatureId
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import land_use
from burro_pipeline.derive.land_use import LandUse
from burro_pipeline.derive.land_use_sheet import read_table
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)
FIVE = tuple(sorted(land_use.MEASURES))
# What the step `describe` gave of the workbook on 2026-09-24. The names of the columns
# stand in row 6. 33,772 rows of the sheet hold something, and five of them are the title,
# the unit and the three rows of names.
HEADER_AT, UNDER_THE_NAMES = 6, 33_772 - 5
# The publisher's own row for London as a whole, by its code.
LONDON = re.compile("E12000007")
# The gate of the pipeline design for a total: within 0.5 in 100 of the publisher's own.
GATE = 0.005
# A hectare is kept to four decimal places, so it is a whole number of square metres.
SQUARE_METRES = 10_000
# What the first reading of the table counted, on 2026-09-24. A row for every LSOA of
# England, and under the names 12 rows more: England, 9 regions and two notes. No cell of
# a category holds the number nought: where an LSOA has none of a kind of land the cell
# holds a dash, in 373,063 cells of the rows of LSOAs.
ROWS, OTHERS, DASHES = 33_755, 12, 373_063
_F = FeatureId
# London's lowest, middle and highest figure of each measure, in 100 of an area's land, and
# how many of the 1,002 areas stand at nought.
AS_A_SHARE_OF_LAND = {
    _F.LAND_GARDENS: ((0.2, 27.1, 65.3), 0),
    _F.LAND_INDUSTRY: ((0.0, 0.1, 18.6), 451),
    _F.LAND_STORAGE: ((0.0, 0.0, 13.2), 536),
    _F.LAND_TRANSPORT_OTHER: ((0.0, 1.2, 52.6), 220),
    _F.LAND_WOODLAND: ((0.0, 1.3, 37.9), 154),
}
# The same of the other figure, the mean of an area's shares by homes, which joins no build.
BY_HOMES = {
    _F.LAND_GARDENS: ((0.5, 29.8, 64.8), 0),
    _F.LAND_INDUSTRY: ((0.0, 0.1, 9.1), 448),
    _F.LAND_STORAGE: ((0.0, 0.0, 8.0), 535),
    _F.LAND_TRANSPORT_OTHER: ((0.0, 1.2, 19.5), 218),
    _F.LAND_WOODLAND: ((0.0, 1.2, 31.1), 159),
}


def listing() -> dict[str, tuple[int, int]]:
    """Every file of the store, with its size and when it was last written."""
    return {
        path.relative_to(STORE).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(Path(STORE).rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def before() -> dict[str, tuple[int, int]]:
    return listing()


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory, before: dict[str, tuple[int, int]]) -> Inputs:
    work = tmp_path_factory.mktemp("real")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def measured(real: Inputs, found: Spine) -> Land:
    return land.build(real, found)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine, measured: Land) -> dict[FeatureId, LandUse]:
    return {feature: land_use.build(feature, real, found, measured) for feature in FIVE}


def counted(worked: Mapping[str, Worked]) -> tuple[tuple[float, float, float], int]:
    """London's lowest, middle and highest figure, and how many areas stand at nought."""
    values = sorted(one.value for one in worked.values() if one.value is not None)
    return (values[0], statistics.median(values), values[-1]), values.count(0.0)


# The table


def test_the_table_is_found_and_every_lsoa_of_london_has_a_row(
    made: dict[FeatureId, LandUse], found: Spine
):
    sheet = made[FIVE[0]].sheet
    assert all(lsoa in sheet.hectares or lsoa in sheet.without for lsoa in found.lsoas)
    assert sheet.rows >= len(found.lsoas)
    assert {one.geography for one in made.values()} == {Geography.LSOA21}


def test_the_totals_are_the_hectares_of_the_lsoas(made: dict[FeatureId, LandUse]):
    to_the_land = made[FIVE[0]].sheet.to_the_land
    assert to_the_land is not None and land_use.LEAST <= to_the_land <= land_use.MOST


def test_the_table_is_laid_out_as_it_was_seen_to_be(made: dict[FeatureId, LandUse]):
    sheet = made[FIVE[0]].sheet
    assert sheet.header_at == HEADER_AT
    assert sheet.rows + sheet.others == UNDER_THE_NAMES


def test_the_table_holds_the_rows_and_the_dashes_that_were_counted(
    made: dict[FeatureId, LandUse],
):
    sheet = made[FIVE[0]].sheet
    assert (sheet.rows, sheet.others, sheet.dashes) == (ROWS, OTHERS, DASHES)
    assert not sheet.without
    assert sheet.to_the_land == 1.0


def test_the_lsoas_of_london_add_up_to_the_publishers_own_row_for_london(
    real: Inputs, made: dict[FeatureId, LandUse], found: Spine
):
    """Each of the 28 categories, and all the land: within the gate, and what rounding allows."""
    opened = real.open(
        land_use.SOURCE, Use.SCORING, edition=land_use.EDITION, named=land_use.is_the_table
    )
    table = read_table(
        opened,
        land_use.COLUMNS,
        LONDON,
        over=land_use.OVER,
        total=land_use.TOTAL,
        unit=land_use.UNIT,
    )
    (row,) = table.rows
    sheet = made[FIVE[0]].sheet
    assert not sheet.without
    rounding = len(found.lsoas) * 0.5 * 10.0**-sheet.places
    for code, held in row.held.items():
        published = 0.0 if held == land_use.DASH else held
        assert isinstance(published, float), code
        added = math.fsum(
            sheet.total[lsoa] if code == land_use.ALL else sheet.hectares[lsoa][code]
            for lsoa in found.lsoas
        )
        assert abs(added - published) <= GATE * published + rounding, code


# The figures


@pytest.mark.parametrize("feature", FIVE)
def test_every_area_has_a_figure_and_london_is_as_it_was_counted(
    made: dict[FeatureId, LandUse], feature: FeatureId
):
    worked = made[feature].worked
    assert Counter(one.state for one in worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in worked.values()} == {1.0}
    assert counted(worked) == AS_A_SHARE_OF_LAND[feature]


@pytest.mark.parametrize("feature", FIVE)
def test_the_mean_of_shares_by_homes_is_as_it_was_counted(
    made: dict[FeatureId, LandUse], found: Spine, feature: FeatureId
):
    worked = land_use.figures_by_homes(feature, made[feature].sheet, found)
    assert Counter(one.state for one in worked.values()) == {State.PRESENT: 1_002}
    assert counted(worked) == BY_HOMES[feature]


def test_every_area_has_a_row_and_no_figure_is_outside_what_a_share_can_be(
    made: dict[FeatureId, LandUse], found: Spine
):
    for one in made.values():
        assert set(one.worked) == {area.area_id for area in found.areas}
        assert len(one.rows) == len(found.areas)
        for worked in one.worked.values():
            assert worked.value is None or 0.0 <= worked.value <= 100.0


def test_the_five_shares_of_an_area_add_up_to_no_more_than_all_of_it(
    made: dict[FeatureId, LandUse], found: Spine
):
    for area in found.areas:
        shares = [made[feature].worked[area.area_id].value for feature in FIVE]
        # Each share is rounded to a tenth, so five of them may be a quarter over.
        assert sum(share for share in shares if share is not None) <= 100.0 + 0.25


def test_every_figure_is_the_one_plain_arithmetic_gives(
    made: dict[FeatureId, LandUse], found: Spine
):
    """Worked out a second way: in whole square metres, from the rows of each area's LSOAs."""
    lsoas: dict[str, set[str]] = {}
    for cell in found.cells:
        lsoas.setdefault(spine.area_id_of(cell.msoa), set()).add(cell.lsoa)
    step = Decimal(1).scaleb(-land_use.DECIMALS)
    for feature, one in made.items():
        category, sheet = land_use.MEASURES[feature].category, one.sheet
        for area, worked in one.worked.items():
            used = sorted(lsoa for lsoa in lsoas[area] if lsoa in sheet.hectares)
            if worked.value is None:
                continue
            top = sum(round(sheet.hectares[lsoa][category] * SQUARE_METRES) for lsoa in used)
            bottom = sum(round(sheet.total[lsoa] * SQUARE_METRES) for lsoa in used)
            percent = Fraction(100 * top, bottom)
            exact = Decimal(percent.numerator) / Decimal(percent.denominator)
            assert worked.value == float(exact.quantize(step, rounding=ROUND_HALF_UP))


# The evidence


def test_every_source_a_figure_rests_on_is_registered_for_scoring(
    made: dict[FeatureId, LandUse],
):
    for one in made.values():
        assert one.metric.source_ids[0] == land_use.SOURCE
        for source_id in one.metric.source_ids:
            assert Use.SCORING in registry().get(source_id).uses
        assert {row.derivation_id for row in one.rows} == {"lsoa_ratio_by_homes@1"}
        assert all(row.value == one.worked[row.area_id].value for row in one.rows)


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: dict[FeatureId, LandUse], before: dict[str, tuple[int, int]]
):
    assert made and Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
