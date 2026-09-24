"""Homes per hectare, worked out from the files their publishers gave.

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

import csv
import statistics
from collections import Counter

import pytest
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import homes_density
from burro_pipeline.derive.homes_density import Density
from burro_pipeline.derive.methods import to_places
from burro_pipeline.derive.rounded_counts import disagrees
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .real_files import SKIPPED, lsoas_of_every_msoa, real_inputs, row_of_london, within_the_gate
from .test_homes_density import COLUMNS

pytestmark = SKIPPED
TABLE, LOOKUP, BOUNDARIES = "f-e1979a4196e2", "f-49321b95f212", "f-9f549e33f46b"


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def measured(real: Inputs, found: Spine) -> Land:
    return land.build(real, found)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine, measured: Land) -> Density:
    return homes_density.build(real, found, measured)


# The table


def test_the_made_up_table_has_the_columns_of_the_real_one(real: Inputs):
    """The tests that run everywhere read a table laid out as this one is."""
    opened = real.open(homes_density.SOURCE, Use.SCORING, named=homes_density.is_the_table)
    with opened.text(homes_density.MEMBER) as text:
        first = text.readline()
    assert tuple(next(csv.reader([first]))) == COLUMNS
    # The publisher puts quotes round every cell, and the made-up table does too.
    assert first.count('"') == 2 * len(COLUMNS)
    assert opened.member(homes_density.MEMBER) == "CTSOP1.1/CTSOP1_1_2025_03_31.csv"


def test_the_table_holds_as_many_rows_and_areas_as_were_counted(made: Density):
    assert made.stock.rows == 43_296
    assert (len(made.stock.homes), len(made.stock.of_msoa)) == (35_672, 7_264)
    assert made.stock.withheld == frozenset()
    assert (made.stock.as_at, made.geography) == ("2025-03-31", Geography.MSOA21)


# What a dash means


def test_every_row_of_england_is_what_the_rows_of_its_lsoas_allow(real: Inputs, made: Density):
    """No count of all homes is a dash, and each MSOA is within rounding of its LSOAs."""
    stock = made.stock
    broken: Counter[str] = Counter()
    for msoa, lsoas in lsoas_of_every_msoa(real).items():
        words = disagrees(stock.of_msoa[msoa], [stock.homes.get(lsoa) for lsoa in lsoas])
        broken[words or "none"] += 1
    assert broken == {"none": 6_856}
    assert sum(count is None for count in stock.of_msoa.values()) == 0
    assert made.rows_held == 1_002


# One sum


def test_the_homes_of_the_areas_add_up_to_the_publishers_own_count_for_london(
    real: Inputs, made: Density, found: Spine
):
    """The gate of the design: within 0.5 in 100 of the publisher's own total."""
    opened = real.open(homes_density.SOURCE, Use.SCORING, named=homes_density.is_the_table)
    published = row_of_london(opened, homes_density.MEMBER, (homes_density.HOMES,), band=None)
    homes = sum(made.stock.of_msoa[area.code] or 0 for area in found.areas)
    assert homes == 3_837_870
    assert within_the_gate(homes, published[homes_density.HOMES])


# The figures


def test_every_area_of_london_has_a_figure(made: Density):
    assert len(made.worked) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {(one.units_used, one.units_expected) for one in made.worked.values()} == {(1, 1)}
    assert {one.flags for one in made.worked.values()} == {(Flag.ROUNDED_IN_SOURCE,)}


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(made: Density):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert len(values) == 1_002
    assert (values[0], statistics.median(values), values[-1]) == (1.3, 32.2, 154.8)


def test_every_figure_is_the_publishers_own_count_over_the_land_of_the_area(
    made: Density, found: Spine, measured: Land
):
    """A reader who opens the publisher's table for the area finds this count of homes."""
    for area in found.areas:
        homes, hectares = made.stock.of_msoa[area.code], measured.of_area[area.area_id]
        assert made.worked[area.area_id].value == to_places((homes or 0) / hectares, 1)


# The evidence


def test_every_figure_rests_on_the_three_files_that_were_fetched(made: Density):
    assert [receipt.file_id for receipt in made.files] == [LOOKUP, BOUNDARIES, TABLE]
    assert len(made.rows) == 1_002
    assert all(row.inputs == (LOOKUP, BOUNDARIES, TABLE) for row in made.rows)
    assert all(row.derivation_id == "area_row_ratio@1" for row in made.rows)
    # From the boundaries the land is measured on to the day of the table.
    period = Period(start="2021-12-01", end="2025-03-31")
    assert all(row.data_period == period for row in made.rows)
    evidence = Evidence.of("lon-2026-09-23-01", made.files, homes_density.METHODS, made.rows)
    assert len(evidence.rows) == 1_002


def test_the_period_and_the_sources_are_the_ones_the_receipts_give(made: Density):
    assert made.metric.vintage == "2025-03-31"
    assert "as at 2025-03-31" in made.metric.definition
    assert "as at 2021-12" in made.metric.definition
    assert made.metric.source_ids == (
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "voa-council-tax-stock-of-properties",
    )
