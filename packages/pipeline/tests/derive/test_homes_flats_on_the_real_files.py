"""Flats as a share of homes, worked out from the files their publishers gave.

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
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import homes_flats
from burro_pipeline.derive.homes_flats import Counted, Flats
from burro_pipeline.derive.methods import to_places
from burro_pipeline.derive.rounded_counts import disagrees
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .real_files import SKIPPED, lsoas_of_every_msoa, real_inputs, row_of_london, within_the_gate
from .test_homes_flats import COLUMNS

pytestmark = SKIPPED
TABLE, LOOKUP = "f-c8891afc8f10", "f-49321b95f212"


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Flats:
    return homes_flats.build(real, found)


def rows_of_london(made: Flats, found: Spine) -> list[Counted]:
    return [made.stock.of_msoa[area.code] for area in found.areas]


# The table


def test_the_made_up_table_has_the_columns_of_the_real_one(real: Inputs):
    """The tests that run everywhere read a table laid out as this one is."""
    opened = real.open(homes_flats.SOURCE, Use.SCORING, named=homes_flats.is_the_table)
    with opened.text(homes_flats.MEMBER) as text:
        first = text.readline()
    assert tuple(next(csv.reader([first]))) == COLUMNS
    assert opened.member(homes_flats.MEMBER) == "CTSOP3.1/CTSOP3_1_2025_03_31.csv"


def test_the_table_holds_as_many_rows_and_areas_as_were_counted(made: Flats):
    assert made.stock.rows == 392_014
    assert (len(made.stock.of_lsoa), len(made.stock.of_msoa)) == (35_672, 7_264)
    assert made.stock.as_at == "2025-03-31"


def test_the_table_is_on_the_codes_of_the_census_of_2021(made: Flats, found: Spine):
    assert made.geography is Geography.MSOA21
    assert all(lsoa in made.stock.of_lsoa for lsoa in found.lsoas)
    assert all(area.code in made.stock.of_msoa for area in found.areas)


# What a dash means


def test_every_row_of_england_is_what_the_rows_of_its_lsoas_allow(real: Inputs, made: Flats):
    """The evidence that `0` is none and a dash is 1 to 4, from the file itself.

    Over every MSOA of England and each count that is read: where every LSOA
    has `0` the MSOA has `0`, where any LSOA has a dash or a number the MSOA
    does not have `0`, and where the MSOA has a dash no LSOA has a number and
    at most four have a dash. No row breaks a rule.
    """
    stock = made.stock
    broken: Counter[str] = Counter()
    for msoa, lsoas in lsoas_of_every_msoa(real).items():
        own = stock.of_msoa[msoa]
        parts = [stock.of_lsoa[lsoa] for lsoa in lsoas]
        for name in ("flats", "not_known", "homes"):
            words = disagrees(getattr(own, name), [getattr(part, name) for part in parts])
            broken[words or "none"] += 1
    assert broken == {"none": 3 * 6_856}
    assert made.rows_held == 1_002


def test_no_area_of_london_has_a_dash_for_its_flats_or_for_its_homes(made: Flats, found: Spine):
    london = rows_of_london(made, found)
    assert sum(one.flats is None for one in london) == 0
    assert sum(one.homes is None for one in london) == 0
    assert sum(one.flats == 0 for one in london) == 0
    # A dash in the row of an LSOA is part of no figure. It is counted so that a change shows.
    lsoas = [made.stock.of_lsoa[lsoa] for lsoa in found.lsoas]
    assert sum(one.flats is None for one in lsoas) == 31


# One sum


def test_the_homes_of_the_areas_add_up_to_the_publishers_own_count_for_london(
    real: Inputs, made: Flats, found: Spine
):
    """The gate of the design: within 0.5 in 100 of the publisher's own total."""
    opened = real.open(homes_flats.SOURCE, Use.SCORING, named=homes_flats.is_the_table)
    columns = (homes_flats.HOMES, homes_flats.FLATS)
    published = row_of_london(opened, homes_flats.MEMBER, columns)
    london = rows_of_london(made, found)
    homes = sum(one.homes or 0 for one in london)
    assert homes == 3_837_870
    assert within_the_gate(homes, published[homes_flats.HOMES])
    assert within_the_gate(sum(one.flats or 0 for one in london), published[homes_flats.FLATS])


# The figures


def test_every_area_of_london_has_a_figure(made: Flats):
    assert len(made.worked) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {(one.units_used, one.units_expected) for one in made.worked.values()} == {(1, 1)}
    assert {one.flags for one in made.worked.values()} == {(Flag.ROUNDED_IN_SOURCE,)}


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(made: Flats):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert len(values) == 1_002
    assert (values[0], statistics.median(values), values[-1]) == (1.7, 53.5, 99.0)


def test_every_figure_is_the_publishers_own_row_for_the_area(made: Flats, found: Spine):
    """A reader who opens the publisher's table for the area finds these counts."""
    for area in found.areas:
        own, worked = made.stock.of_msoa[area.code], made.worked[area.area_id]
        assert worked.value == to_places(100 * (own.flats or 0) / (own.homes or 1), 1)


# The evidence


def test_every_figure_rests_on_the_two_files_that_were_fetched(made: Flats):
    assert [receipt.file_id for receipt in made.files] == [LOOKUP, TABLE]
    assert made.stock.file_id == TABLE
    assert len(made.rows) == 1_002
    assert all(row.inputs == (LOOKUP, TABLE) for row in made.rows)
    assert all(row.derivation_id == "area_row_ratio@1" for row in made.rows)
    # From the lookup, which says which MSOA an area is, to the day of the table.
    period = Period(start="2022-12-01", end="2025-03-31")
    assert all(row.data_period == period for row in made.rows)
    evidence = Evidence.of("lon-2026-09-23-01", made.files, homes_flats.METHODS, made.rows)
    assert len(evidence.rows) == 1_002


def test_the_period_and_the_sources_are_the_ones_the_receipts_give(made: Flats):
    assert made.metric.vintage == "2025-03-31"
    assert "as at 2025-03-31" in made.metric.definition
    assert made.metric.source_ids == (
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "voa-council-tax-stock-of-properties",
    )
