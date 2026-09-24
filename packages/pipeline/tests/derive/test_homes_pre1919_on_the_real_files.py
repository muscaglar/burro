"""Homes built before 1919, worked out from the files their publishers gave.

Every other test of the measure runs on a made-up table. These read the real
one, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts, one sum and three figures, so that a publisher's file
that changes is noticed. The three figures are London's lowest, middle and
highest. None is said of a named area or of a named borough. Each was worked
out on 2026-09-24, from the table as at 31 March 2025, and no person has
checked one.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import homes_pre1919
from burro_pipeline.derive.homes_pre1919 import Counted, Pre1919
from burro_pipeline.derive.methods import to_places
from burro_pipeline.derive.rounded_counts import disagrees
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .real_files import SKIPPED, lsoas_of_every_msoa, real_inputs, row_of_london, within_the_gate

pytestmark = SKIPPED
TABLE, LOOKUP = "f-c4e32565aeb1", "f-49321b95f212"


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def built(real: Inputs, found: Spine) -> Pre1919:
    return homes_pre1919.build(real, found)


def rows_of_london(built: Pre1919, found: Spine) -> list[Counted]:
    return [built.stock.of_msoa[area.code] for area in found.areas]


# The table


def test_the_table_holds_as_many_rows_and_areas_as_were_counted(built: Pre1919):
    stock = built.stock
    assert stock.rows == 392_014
    assert (len(stock.of_lsoa), len(stock.of_msoa)) == (35_672, 7_264)
    assert Counter(code[0] for code in stock.of_lsoa) == {"E": 33_755, "W": 1_917}
    assert Counter(code[0] for code in stock.of_msoa) == {"E": 6_856, "W": 408}
    assert stock.as_at == "2025-03-31"


def test_the_codes_of_the_table_are_those_of_the_census_of_2021(real: Inputs, built: Pre1919):
    """Neither the table nor its notes names a census, so it is held to the lookup of 2021.

    Every LSOA and MSOA of England in the table is in the lookup, and every one
    of the lookup is in the table. The lookup holds England alone.
    """
    of_2021 = lsoas_of_every_msoa(real)
    lsoas = {lsoa for held in of_2021.values() for lsoa in held}
    assert (len(of_2021), len(lsoas)) == (6_856, 33_755)
    assert {code for code in built.stock.of_lsoa if code.startswith("E")} == lsoas
    assert {code for code in built.stock.of_msoa if code.startswith("E")} == set(of_2021)
    assert built.geography is Geography.MSOA21


# What a dash means


def test_every_row_of_england_is_what_the_rows_of_its_lsoas_allow(real: Inputs, built: Pre1919):
    """The evidence that `0` is none and a dash is 1 to 4, from the file itself.

    Over every MSOA of England and each count that is read: where every LSOA
    has `0` the MSOA has `0`, where any LSOA has a dash or a number the MSOA
    does not have `0`, and where the MSOA has a dash no LSOA has a number and
    at most four have a dash. No row breaks a rule.
    """
    stock = built.stock
    broken: Counter[str] = Counter()
    for msoa, lsoas in lsoas_of_every_msoa(real).items():
        own = stock.of_msoa[msoa]
        parts = [stock.of_lsoa[lsoa] for lsoa in lsoas]
        for name in ("before_1900", "from_1900", "not_known", "homes"):
            words = disagrees(getattr(own, name), [getattr(part, name) for part in parts])
            broken[words or "none"] += 1
    assert broken == {"none": 4 * 6_856}
    assert built.rows_held == 1_002


def test_a_dash_is_as_common_in_the_rows_of_londons_areas_as_was_counted(
    built: Pre1919, found: Spine
):
    london = rows_of_london(built, found)
    assert sum(one.before_1900 is None for one in london) == 35
    assert sum(one.from_1900 is None for one in london) == 52
    assert sum(one.old_withheld for one in london) == 81
    assert sum(one.not_known is None for one in london) == 252
    assert sum(one.homes is None for one in london) == 0
    # Of the areas with no number for either period: a nought for both, or a dash.
    assert sum(one.before_1900 == 0 and one.from_1900 == 0 for one in london) == 21
    assert sum(one.old_withheld and one.before_1919 == 0 for one in london) == 23


# One sum


def test_the_homes_of_the_areas_add_up_to_the_publishers_own_count_for_london(
    real: Inputs, built: Pre1919, found: Spine
):
    """The gate of the design: within 0.5 in 100 of the publisher's own total."""
    opened = real.open(homes_pre1919.SOURCE, Use.SCORING, named=homes_pre1919.is_the_table)
    columns = (homes_pre1919.HOMES, *homes_pre1919.BEFORE_1919)
    published = row_of_london(opened, homes_pre1919.MEMBER, columns)
    london = rows_of_london(built, found)
    homes = sum(one.homes or 0 for one in london)
    assert homes == 3_837_870
    assert within_the_gate(homes, published[homes_pre1919.HOMES])
    assert within_the_gate(
        sum(one.before_1919 for one in london),
        sum(published[name] or 0 for name in homes_pre1919.BEFORE_1919),
    )


# The figures


def test_every_area_of_london_has_a_figure_or_a_reason(built: Pre1919):
    assert len(built.worked) == 1_002
    assert Counter(one.state for one in built.worked.values()) == {
        State.PRESENT: 764,
        State.PARTIAL: 215,
        State.SUPPRESSED: 23,
    }
    assert all(one.units_expected == 1 for one in built.worked.values())
    assert all((one.value is None) == (one.units_used == 0) for one in built.worked.values())


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(built: Pre1919):
    found = sorted(one.value for one in built.worked.values() if one.value is not None)
    assert len(found) == 979
    assert (found[0], statistics.median(found), found[-1]) == (0.0, 23.4, 97.2)
    assert all(0 <= value <= 100 for value in found)


def test_a_figure_of_nought_is_given_only_where_the_publisher_counted_none(
    built: Pre1919, found: Spine
):
    """A dash is a count that is not nought. No area whose row holds one reads 0.0."""
    rows = {area.area_id: built.stock.of_msoa[area.code] for area in found.areas}
    nought = [area for area, one in built.worked.items() if one.value == 0]
    assert len(nought) == 21
    assert all(rows[area].before_1900 == 0 and rows[area].from_1900 == 0 for area in nought)
    withheld = [area for area, one in built.worked.items() if one.state is State.SUPPRESSED]
    assert all(rows[area].old_withheld and rows[area].before_1919 == 0 for area in withheld)


def test_every_figure_is_the_publishers_own_row_for_the_area(built: Pre1919, found: Spine):
    """A reader who opens the publisher's table for the area finds these counts."""
    for area in found.areas:
        own, worked = built.stock.of_msoa[area.code], built.worked[area.area_id]
        if worked.value is not None:
            assert worked.value == to_places(100 * own.before_1919 / (own.dated or 0), 1)
            assert worked.weight_covered == round((own.dated or 0) / (own.homes or 1), 6)


def test_a_figure_is_marked_only_where_a_count_of_old_homes_is_a_dash(built: Pre1919, found: Spine):
    flags = Counter(flag for one in built.worked.values() for flag in one.flags)
    assert flags == {Flag.ROUNDED_IN_SOURCE: 1_002, Flag.SUPPRESSED_IN_SOURCE: 81}
    marked = {area for area, one in built.worked.items() if Flag.SUPPRESSED_IN_SOURCE in one.flags}
    assert marked == {
        area.area_id for area in found.areas if built.stock.of_msoa[area.code].old_withheld
    }


def test_the_least_covered_area_has_a_period_for_four_homes_in_five(built: Pre1919):
    """Coverage is the share of an area's homes that have a build period."""
    covered = sorted(one.weight_covered for one in built.worked.values() if one.units_used)
    assert len(covered) == 979
    assert 0.78 < covered[0] < 0.79
    assert sum(one < 0.95 for one in covered) == 21
    assert sum(one < 0.9 for one in covered) == 6


# The evidence, the name and the period


def test_every_figure_has_a_row_that_names_the_two_files_behind_it(built: Pre1919):
    assert [receipt.file_id for receipt in built.files] == [LOOKUP, TABLE]
    assert len(built.rows) == 1_002
    for row in built.rows:
        assert row.inputs == (LOOKUP, TABLE)
        assert row.derivation_id == "area_row_ratio@1"
        assert row.data_period == Period(start="2022-12-01", end="2025-03-31")
        assert row.retrieved_on == "2026-09-23"
    evidence = Evidence.of("lon-2026-09-23-01", built.files, homes_pre1919.METHODS, built.rows)
    assert len(evidence.rows) == 1_002


def test_the_measure_is_named_and_dated_as_the_table_is(built: Pre1919):
    metric = built.metric
    assert (metric.label, metric.unit, metric.vintage) == (
        "Homes built before 1919",
        "%",
        "2025-03-31",
    )
    assert metric.source_ids == (
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "voa-council-tax-stock-of-properties",
    )
