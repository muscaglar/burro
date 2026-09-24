"""Homes built since 2000, worked out from the files their publishers gave.

Every other test of the measure runs on a made-up table. These read the real
one, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts, one sum and three figures, so that a publisher's file
that changes is noticed. The three figures are London's lowest, middle and
highest. None is said of a named area or of a named borough. Each was worked
out on 2026-09-24, from the table as at 31 March 2025, and no person has
checked one. Credit for the figures held here, in the words of the licence
registry: Contains public sector information licensed under the Open Government
Licence v3.0. Source: Office for National Statistics licensed under the Open
Government Licence v.3.0. Contains OS data © Crown copyright and database right
[year].

Nothing is written to the store. A file is copied out of it to be read.
"""

import csv
import statistics
from collections import Counter

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import homes_post2000, homes_pre1919
from burro_pipeline.derive.homes_post2000 import Counted, Post2000, counts_of
from burro_pipeline.derive.methods import to_places
from burro_pipeline.derive.rounded_counts import disagrees
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .real_files import SKIPPED, lsoas_of_every_msoa, real_inputs, row_of_london, within_the_gate
from .test_homes_post2000 import ADDED
from .test_homes_pre1919 import COLUMNS

pytestmark = SKIPPED
TABLE, LOOKUP = "f-c4e32565aeb1", "f-49321b95f212"


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def built(real: Inputs, found: Spine) -> Post2000:
    return homes_post2000.build(real, found)


def rows_of_london(built: Post2000, found: Spine) -> list[Counted]:
    return [built.stock.of_msoa[area.code] for area in found.areas]


# The table


def test_the_made_up_table_has_the_columns_of_the_real_one(real: Inputs):
    """The tests that run everywhere read a table laid out as this one is."""
    opened = real.open(homes_post2000.SOURCE, Use.SCORING, named=homes_post2000.is_the_table)
    with opened.text(homes_post2000.MEMBER) as text:
        assert tuple(next(csv.reader(text))) == COLUMNS


def test_the_table_holds_as_many_rows_and_areas_as_were_counted(built: Post2000):
    stock = built.stock
    assert stock.rows == 392_014
    assert (len(stock.of_lsoa), len(stock.of_msoa)) == (35_672, 7_264)
    assert stock.as_at == "2025-03-31"
    assert built.geography is Geography.MSOA21


def test_the_period_and_every_year_to_the_tables_own_are_added(built: Post2000):
    """One period of nine years, and a column for each of the 17 years from 2009 to 2025."""
    assert built.stock.added == ADDED
    assert (len(built.stock.added), built.stock.last_year) == (18, 2025)
    assert all(len(one.since_2000) == 18 for one in built.stock.of_msoa.values())


# What a dash means


def test_every_row_of_england_is_what_the_rows_of_its_lsoas_allow(real: Inputs, built: Post2000):
    """The evidence that `0` is none and a dash is 1 to 4, from the file itself.

    Over every MSOA of England and each of the 20 counts that are read: where
    every LSOA has `0` the MSOA has `0`, where any LSOA has a dash or a number
    the MSOA does not have `0`, and where the MSOA has a dash no LSOA has a
    number and at most four have a dash. No row breaks a rule.
    """
    stock = built.stock
    broken: Counter[str] = Counter()
    for msoa, lsoas in lsoas_of_every_msoa(real).items():
        own = counts_of(stock.of_msoa[msoa])
        parts = [counts_of(stock.of_lsoa[lsoa]) for lsoa in lsoas]
        for at, count in enumerate(own):
            broken[disagrees(count, [part[at] for part in parts]) or "none"] += 1
    assert broken == {"none": 20 * 6_856}
    assert built.rows_held == 1_002


def test_a_dash_is_as_common_in_the_rows_of_londons_areas_as_was_counted(
    built: Post2000, found: Spine
):
    """A year in which an area gained 1 to 4 homes is a dash, and most areas have had one."""
    london = rows_of_london(built, found)
    assert sum(one.dashes for one in london) == 4_576
    assert sum(one.new_withheld for one in london) == 962
    assert max(one.dashes for one in london) == 12
    assert statistics.median(one.dashes for one in london) == 4
    # The period of nine years is seldom too small to round, and a year often is.
    assert sum(one.since_2000[0] is None for one in london) == 18
    assert sum(one.since_2000[0] == 0 for one in london) == 4
    assert sum(one.homes is None for one in london) == 0
    # Of the areas with no number for the period or for any year: nought for each, or a dash.
    assert sum(one.new == 0 and not one.new_withheld for one in london) == 0
    assert sum(one.new == 0 and one.new_withheld for one in london) == 3


def test_the_dashes_of_an_area_hide_under_two_in_100_of_its_homes(built: Post2000, found: Spine):
    """Each dash hides 1 to 4 homes. How many that can be, as a share of the area's homes."""
    hidden = sorted(
        100 * one.hidden_at_most / one.dated for one in rows_of_london(built, found) if one.dated
    )
    assert round(statistics.median(hidden), 1) == 0.5
    assert 1.7 < hidden[-1] < 1.8


# One sum


def test_the_new_homes_of_the_areas_add_up_to_the_publishers_own_count_for_london(
    real: Inputs, built: Post2000, found: Spine
):
    """The gate of the design: within 0.5 in 100 of the publisher's own total.

    A dash adds nothing to an area and a year of 5 to 9 homes adds 10, so the
    areas add up to a little under the row for London, and within the gate.
    """
    opened = real.open(homes_post2000.SOURCE, Use.SCORING, named=homes_post2000.is_the_table)
    columns = (homes_pre1919.HOMES, *built.stock.added)
    published = row_of_london(opened, homes_post2000.MEMBER, columns)
    london = rows_of_london(built, found)
    homes = sum(one.homes or 0 for one in london)
    assert homes == 3_837_870
    assert within_the_gate(homes, published[homes_pre1919.HOMES])
    new, stated = (
        sum(one.new for one in london),
        sum(published[name] or 0 for name in built.stock.added),
    )
    assert (new, stated) == (684_610, 685_500)
    assert within_the_gate(new, stated)


# The figures


def test_every_area_of_london_has_a_figure_or_a_reason(built: Post2000):
    assert len(built.worked) == 1_002
    assert Counter(one.state for one in built.worked.values()) == {
        State.PRESENT: 785,
        State.PARTIAL: 214,
        State.SUPPRESSED: 3,
    }
    assert all(one.units_expected == 1 for one in built.worked.values())
    assert all((one.value is None) == (one.units_used == 0) for one in built.worked.values())


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(built: Post2000):
    found = sorted(one.value for one in built.worked.values() if one.value is not None)
    assert len(found) == 999
    assert (found[0], statistics.median(found), found[-1]) == (0.4, 10.6, 100.0)
    assert all(0 <= value <= 100 for value in found)
    assert len(set(found)) == 362


def test_no_area_reads_nought_and_none_is_given_nought_for_a_dash(built: Post2000, found: Spine):
    """A dash is a count that is not nought. No area whose new homes are all dashes reads 0.0."""
    rows = {area.area_id: built.stock.of_msoa[area.code] for area in found.areas}
    assert not [area for area, one in built.worked.items() if one.value == 0]
    withheld = [area for area, one in built.worked.items() if one.state is State.SUPPRESSED]
    assert len(withheld) == 3
    assert all(rows[area].new_withheld and rows[area].new == 0 for area in withheld)


def test_one_area_is_built_almost_wholly_since_2000_and_reads_the_whole(
    built: Post2000, found: Spine
):
    """Its counts come to 10 homes more than its homes with a period, which rounding allows."""
    rows = {area.area_id: built.stock.of_msoa[area.code] for area in found.areas}
    assert len(built.at_the_whole) == 1
    (area,) = built.at_the_whole
    assert built.worked[area].value == 100.0
    assert rows[area].over == 10 and rows[area].over <= rows[area].rounding_allows
    assert sum(one.value == 100.0 for one in built.worked.values()) == 1


def test_every_figure_is_the_publishers_own_row_for_the_area(built: Post2000, found: Spine):
    """A reader who opens the publisher's table for the area finds these counts."""
    for area in found.areas:
        own, worked = built.stock.of_msoa[area.code], built.worked[area.area_id]
        if worked.value is not None and area.area_id not in built.at_the_whole:
            assert worked.value == to_places(100 * own.new / (own.dated or 0), 1)
            assert worked.weight_covered == round((own.dated or 0) / (own.homes or 1), 6)


def test_a_figure_is_marked_only_where_a_count_of_new_homes_is_a_dash(
    built: Post2000, found: Spine
):
    flags = Counter(flag for one in built.worked.values() for flag in one.flags)
    assert flags == {Flag.ROUNDED_IN_SOURCE: 1_002, Flag.SUPPRESSED_IN_SOURCE: 962}
    marked = {area for area, one in built.worked.items() if Flag.SUPPRESSED_IN_SOURCE in one.flags}
    assert marked == {
        area.area_id for area in found.areas if built.stock.of_msoa[area.code].new_withheld
    }


def test_it_is_covered_as_homes_built_before_1919_are(real: Inputs, built: Post2000, found: Spine):
    """Both are shares of the homes that have a period, so both are covered alike."""
    old = homes_pre1919.build(real, found)
    for area, one in built.worked.items():
        if one.units_used and old.worked[area].units_used:
            assert one.weight_covered == old.worked[area].weight_covered
    covered = sorted(one.weight_covered for one in built.worked.values() if one.units_used)
    assert len(covered) == 999
    assert 0.78 < covered[0] < 0.79


# The evidence, the name and the period


def test_every_figure_has_a_row_that_names_the_two_files_behind_it(built: Post2000):
    assert [receipt.file_id for receipt in built.files] == [LOOKUP, TABLE]
    assert len(built.rows) == 1_002
    for row in built.rows:
        assert row.inputs == (LOOKUP, TABLE)
        assert row.derivation_id == "area_row_ratio@1"
        assert row.data_period == Period(start="2022-12-01", end="2025-03-31")
        assert row.retrieved_on == "2026-09-23"
    evidence = Evidence.of("lon-2026-09-23-01", built.files, homes_post2000.METHODS, built.rows)
    assert len(evidence.rows) == 1_002


def test_the_measure_is_named_and_dated_as_the_table_is(built: Post2000):
    metric = built.metric
    assert (metric.label, metric.unit, metric.vintage) == (
        "Homes built since 2000",
        "%",
        "2025-03-31",
    )
    assert metric.source_ids == (
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "voa-council-tax-stock-of-properties",
    )
    assert "from 2000 to 2025" in metric.definition
