"""What a home sells for, worked out from the workbook its publisher gave.

Every other test of the measure runs on a made-up workbook. These read the real
one, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts and the states, so that a publisher's file that changes is
noticed. They hold no figure. The founder decided on 2026-09-24 that a price
may be shown, and the licence registry allows it (ADR 0021). A test is still
given none: the lowest and the highest figure of London are each one cell of
the publisher's workbook, which is the figure of one area, and no tracked file
holds a figure of a named area. Each count was made on 2026-09-24, from the
workbook for the year ending March 2026, and no person has checked one.

The workbook gives no total, for London or for a borough. So no sum is held.
What is held in its place is what must be so of any medians: the median of all
the homes sold lies between the lowest and the highest median of the kinds of
home, wherever the publisher gives all four. And every figure is the
publisher's own cell for the area, which is read again and compared.

The workbook's own words for its source: "Source: Office for National
Statistics, HM Land Registry." and "These statistics were adapted from data
from the HM Land Registry licensed under the Open Government Licence v.3.0."

Nothing is written to the store. A file is copied out of it to be read.
"""

from collections import Counter

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import price
from burro_pipeline.derive.noise_sheet import read_sheet
from burro_pipeline.derive.price import Prices
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs

from .price_support import COLUMNS
from .real_files import SKIPPED, real_inputs

pytestmark = SKIPPED
WORKBOOK, LOOKUP = "f-545982134c5e", "f-49321b95f212"
ANY, DETACHED, SEMI, TERRACED, FLAT = (home.key for home in price.HOMES)


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Prices:
    return price.build(real, found)


# The workbook


def test_the_made_up_sheet_has_the_columns_of_the_real_one(real: Inputs):
    """The tests that run everywhere read a sheet laid out as this one is."""
    opened = real.open(price.SOURCE, price.USE, named=price.is_the_workbook)
    rows = read_sheet(opened, price.ALL.sheet, COLUMNS, header_at=price.HEADER_AT)
    assert len(rows) == 7_264
    with pytest.raises(LockError, match="the column Year ending Jun 2026 is missing"):
        read_sheet(opened, price.ALL.sheet, ("Year ending Jun 2026",), header_at=price.HEADER_AT)


def test_the_year_that_is_read_is_the_last_the_workbook_holds(made: Prices):
    year = made.workbook.year
    assert (year.column, year.said) == ("Year ending Mar 2026", "year ending March 2026")
    assert year.period == Period(start="2025-04", end="2026-03")


def test_each_sheet_holds_as_many_rows_as_were_counted(made: Prices):
    """A row is an MSOA of England or of Wales. A kind of home lacks a few."""
    assert {key: one.rows for key, one in made.workbook.sheets.items()} == {
        ANY: 7_264,
        DETACHED: 7_257,
        SEMI: 7_262,
        TERRACED: 7_264,
        FLAT: 7_261,
    }


def test_the_workbook_is_on_the_codes_of_the_census_of_2021(made: Prices, found: Spine):
    assert made.geography is Geography.MSOA21
    whole = made.workbook.sheets[ANY]
    assert all(area.code in whole.district for area in found.areas)
    assert all(whole.district[area.code] == area.borough_code for area in found.areas)


# The figures


def test_every_area_of_london_has_a_figure_for_a_home_of_any_kind(made: Prices):
    worked = made.of[ANY].worked
    assert len(worked) == 1_002
    assert Counter(one.state for one in worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in worked.values()} == {1.0}
    assert {(one.units_used, one.units_expected) for one in worked.values()} == {(1, 1)}
    assert {one.flags for one in worked.values()} == {()}


def test_the_areas_with_a_figure_for_each_kind_of_home_are_as_many_as_were_counted(made: Prices):
    """Where few homes of a kind are sold, the publisher gives no figure for most areas."""
    states = {
        key: Counter(one.state for one in priced.worked.values()) for key, priced in made.of.items()
    }
    assert states == {
        ANY: {State.PRESENT: 1_002},
        DETACHED: {State.PRESENT: 195, State.SUPPRESSED: 800, State.SOURCE_GAP: 7},
        SEMI: {State.PRESENT: 549, State.SUPPRESSED: 451, State.SOURCE_GAP: 2},
        TERRACED: {State.PRESENT: 873, State.SUPPRESSED: 129},
        FLAT: {State.PRESENT: 927, State.SUPPRESSED: 75},
    }
    for priced in made.of.values():
        for one in priced.worked.values():
            marked = (Flag.SUPPRESSED_IN_SOURCE,) if one.state is State.SUPPRESSED else ()
            assert one.flags == marked
            assert (one.value is None) == (one.state is not State.PRESENT)


def test_every_figure_is_a_price_in_whole_pounds_and_none_is_held_here(made: Prices):
    """What a figure is, and not how much: no tracked file holds the figure of an area."""
    values = [one.value for one in made.of[ANY].worked.values() if one.value is not None]
    assert len(values) == 1_002
    assert all(value > 0 and value == int(value) for value in values)
    assert len(set(values)) > 1


def test_every_figure_is_the_publishers_own_row_for_the_area(made: Prices, found: Spine):
    """A reader who opens the publisher's sheet for the area finds this number."""
    for key, priced in made.of.items():
        sheet = made.workbook.sheets[key]
        for area in found.areas:
            assert priced.worked[area.area_id].value == sheet.price.get(area.code)


def test_the_median_of_all_homes_lies_between_the_medians_of_the_kinds(made: Prices):
    """What stands in for a sum: it must be so, wherever all four kinds have a figure."""
    held = 0
    for area, whole in made.of[ANY].worked.items():
        kinds = [made.of[key].worked[area].value for key in (DETACHED, SEMI, TERRACED, FLAT)]
        known = [value for value in kinds if value is not None]
        if len(known) == len(kinds) and whole.value is not None:
            assert min(known) <= whole.value <= max(known)
            held += 1
    assert held == 160


# The evidence


def test_every_figure_rests_on_the_two_files_that_were_fetched(made: Prices):
    assert [receipt.file_id for receipt in made.files] == [LOOKUP, WORKBOOK]
    assert made.workbook.file_id == WORKBOOK
    rows = [row for priced in made.of.values() for row in priced.rows]
    assert len(rows) == 5 * 1_002
    assert all(row.inputs == (LOOKUP, WORKBOOK) for row in rows)
    assert all(row.derivation_id == "area_row_value@1" for row in rows)
    # From the lookup, which says which MSOA an area is, to the end of the year of sales.
    period = Period(start="2022-12-01", end="2026-03-31")
    assert all(row.data_period == period for row in rows)
    evidence = Evidence.of("lon-2026-09-24-01", made.files, price.METHODS, rows)
    assert len(evidence.rows) == 5 * 1_002


def test_the_period_and_the_sources_are_the_ones_the_receipts_give(made: Prices):
    for priced in made.of.values():
        assert priced.named.vintage == "2025-04 to 2026-03"
        assert "year ending March 2026" in priced.named.definition
        assert priced.named.source_ids == (
            "ons-median-house-prices-msoa",
            "ons-oa21-lsoa21-msoa21-lad22-lookup",
        )
