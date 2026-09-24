"""Four shares of residents and households, worked out from the tables their publisher gave.

Every other test of the measures runs on a made-up table. These read the real
ones, and are skipped where the store of fetched files is not. The store is
named by BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

While a table has no receipt, one test holds that the step refuses it. Once it
has one, the others run, and hold the figures to what any such table must keep:
every area has a figure, a share is between nought and a hundred, the young and
the old of an area are no more than all of it, and what the areas add up to is
within 0.5 in 100 of the publisher's own count for London.

They hold the counts, two sums and three figures of each measure, so that a
publisher's file that changes is noticed. The three figures are London's
lowest, middle and highest. None is said of a named area or of a named borough.
Each was worked out on 2026-09-24, from the tables of Census 2021, and no
person has checked one.

One test reads a row that no step of a build reads: the publisher's own row
for London as a whole, in its table by region, for the columns a measure adds
up. It is kept as the step keeps a row: the four kinds of household with
dependent children as their one sum, and never four. Every figure is read from
the table by MSOA and from no other.

Nothing is written to the store. A file is copied out of it to be read.
"""

import csv
import os
import statistics
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import (
    census_msoa,
    households_dependent_children,
    households_one_person,
    residents_aged_20_34,
    residents_aged_65_over,
)
from burro_pipeline.derive.census_msoa import Of, Share, Table
from burro_pipeline.evidence.lock import LockError, read_receipts
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry
from .census_support import as_the_files_are_written, as_the_files_write_it, table_csv

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)
FOUR: tuple[Of, ...] = (
    residents_aged_20_34.MEASURE,
    residents_aged_65_over.MEASURE,
    households_dependent_children.MEASURE,
    households_one_person.MEASURE,
)
KEYS = [of.key for of in FOUR]
# The publisher's row for London as a whole, in its table by region.
LONDON = "E12000007"
# London's lowest, middle and highest figure of each measure, in percent.
FIGURES = {
    residents_aged_20_34.KEY: (9.9, 22.6, 58.9),
    residents_aged_65_over.KEY: (1.1, 11.2, 27.8),
    households_dependent_children.KEY: (7.8, 32.5, 52.2),
    households_one_person.KEY: (13.4, 28.35, 56.5),
}
# What the areas of London add up to: usual residents, and households.
RESIDENTS, HOUSEHOLDS = 8_799_692, 3_423_921
# The gate of the pipeline design for a total: within 0.5 in 100 of the publisher's own.
GATE = 0.005


def has_a_receipt(table: Table) -> bool:
    return RECEIPTS.is_dir() and any(
        receipt.source_id == census_msoa.SOURCE and table.is_the_table(receipt.publisher_file)
        for receipt in read_receipts(RECEIPTS)
    )


def both_have_a_receipt() -> bool:
    return all(has_a_receipt(table) for table in census_msoa.TABLES.values())


RECEIPTED = pytest.mark.skipif(not both_have_a_receipt(), reason="a table has no receipt")


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
def made(real: Inputs, found: Spine) -> dict[str, Share]:
    return {of.key: census_msoa.build(of, real, found) for of in FOUR}


def of_london(real: Inputs, table: Table) -> dict[str, int]:
    """The publisher's own counts for London as a whole, from its table by region.

    What is kept of the row is what the step keeps of a row by MSOA, and no more.
    """
    opened = real.open(census_msoa.SOURCE, Use.SCORING, named=table.is_the_table)
    member = table.member.replace("-msoa.csv", "-rgn.csv")
    # A table may write every name of its header between quotes, as the table of
    # households does: one of its names holds a comma. So the header is read as a row.
    with opened.text(member) as text:
        header = next(csv.reader(text))
    columns = census_msoa.columns_of(opened, table, header)
    with opened.text(member) as text:
        rows = [
            row
            for row in opened.rows(text, (census_msoa.CODE, *columns.values()))
            if row[census_msoa.CODE] == LONDON
        ]
    (row,) = rows
    return table.kept({key: int(row[name]) for key, name in columns.items()})


# With no receipt


@pytest.mark.parametrize("of", FOUR, ids=KEYS)
def test_a_table_is_not_read_while_it_has_no_receipt(tmp_path: Path, of: Of):
    if has_a_receipt(of.table):
        pytest.skip("it has a receipt")
    real = Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), tmp_path)
    found = spine.build(real)
    with pytest.raises(LockError) as stopped:
        census_msoa.build(of, real, found)
    assert (stopped.value.rule, stopped.value.subject) == (
        "input_has_one_receipt",
        census_msoa.SOURCE,
    )
    assert all(opened.receipt.source_id != census_msoa.SOURCE for opened in real.opened)


# The tables


@RECEIPTED
@pytest.mark.parametrize("table", census_msoa.TABLES.values(), ids=list(census_msoa.TABLES))
def test_the_made_up_table_has_the_header_of_the_real_one(real: Inputs, table: Table):
    """The tests that run everywhere read a table laid out as this one is, quotes and all."""
    opened = real.open(census_msoa.SOURCE, Use.SCORING, named=table.is_the_table)
    with opened.text(table.member) as text:
        first = text.readline()
    made_up = as_the_files_are_written(table, table_csv(table, named=as_the_files_write_it))
    assert first.encode() == made_up.split(b"\n", 1)[0] + b"\n"
    assert opened.member(table.member) == f"census2021-{table.code.lower()}-msoa.csv"


@RECEIPTED
def test_each_table_holds_as_many_rows_as_were_counted(made: dict[str, Share], found: Spine):
    """A row for every MSOA of England and of Wales, of which London's are 1,002."""
    for one in made.values():
        codes = list(one.counts.of_msoa)
        assert (one.counts.rows, len(codes)) == (7_264, 7_264)
        assert sum(code.startswith("E") for code in codes) == 6_856
        assert sum(code.startswith("W") for code in codes) == 408
    assert len(found.areas) == 1_002


@RECEIPTED
def test_the_categories_of_every_row_come_to_its_total_to_the_unit(made: dict[str, Share]):
    """The step allows 2 in 100 either way. The tables as fetched use none of it."""
    for one in made.values():
        assert one.counts.furthest_from_its_total == 0


@RECEIPTED
def test_no_count_of_one_kind_of_family_is_kept_of_the_real_table(made: dict[str, Share]):
    """The table of households is kept as three counts a row, and the table of age as 19."""
    kept = {
        one.counts.table.code: {frozenset(row) for row in one.counts.of_msoa.values()}
        for one in made.values()
    }
    assert kept["TS003"] == {frozenset({"total", "one_person", census_msoa.TOGETHER})}
    assert {len(keys) for keys in kept["TS007A"]} == {19}


@RECEIPTED
def test_every_area_of_london_has_a_row_in_each_table(made: dict[str, Share], found: Spine):
    for one in made.values():
        assert all(area.code in one.counts.of_msoa for area in found.areas)
        assert one.counts.rows >= len(found.areas)
        assert one.geography is Geography.MSOA21


@RECEIPTED
def test_what_the_areas_add_up_to_is_within_the_gate_of_the_publishers_count_for_london(
    real: Inputs, made: dict[str, Share], found: Spine
):
    """The statistics office changes each count a little, so the two are near and not the same."""
    for of in FOUR:
        published = of_london(real, of.table)
        counts = made[of.key].counts.of_msoa
        for key in ("total", *of.kept):
            added = sum(counts[area.code][key] for area in found.areas)
            assert abs(added - published[key]) <= GATE * published[key], (of.key, key)
    totals = {
        of.table.code: sum(made[of.key].counts.of_msoa[area.code]["total"] for area in found.areas)
        for of in FOUR
    }
    assert totals == {"TS007A": RESIDENTS, "TS003": HOUSEHOLDS}


# The figures


@RECEIPTED
def test_every_area_has_a_figure_and_none_is_outside_what_a_share_can_be(
    made: dict[str, Share], found: Spine
):
    for one in made.values():
        assert set(one.worked) == {area.area_id for area in found.areas}
        assert len(one.rows) == len(found.areas)
        assert {worked.state for worked in one.worked.values()} == {State.PRESENT}
        assert all(0.0 <= (worked.value or 0.0) <= 100.0 for worked in one.worked.values())


@RECEIPTED
@pytest.mark.parametrize("key", KEYS)
def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(
    made: dict[str, Share], key: str
):
    values = sorted(one.value for one in made[key].worked.values() if one.value is not None)
    assert len(values) == 1_002
    assert (values[0], statistics.median(values), values[-1]) == pytest.approx(FIGURES[key])


@RECEIPTED
def test_a_measure_tells_areas_apart(made: dict[str, Share]):
    for one in made.values():
        values = sorted(worked.value for worked in one.worked.values() if worked.value is not None)
        assert values[0] < values[len(values) // 2] < values[-1]


@RECEIPTED
def test_two_shares_of_one_whole_are_no_more_than_all_of_it(made: dict[str, Share], found: Spine):
    pairs = (
        (residents_aged_20_34.KEY, residents_aged_65_over.KEY),
        (households_dependent_children.KEY, households_one_person.KEY),
    )
    for first, second in pairs:
        for area in found.areas:
            shares = [made[key].worked[area.area_id].value or 0.0 for key in (first, second)]
            # Each share is rounded to a tenth, so two of them may be a tenth over.
            assert sum(shares) <= 100.0 + 0.1


# The evidence


@RECEIPTED
def test_every_source_a_figure_rests_on_is_registered_for_scoring(made: dict[str, Share]):
    for one in made.values():
        assert census_msoa.SOURCE in one.proposed.source_ids
        for source_id in one.proposed.source_ids:
            assert Use.SCORING in registry().get(source_id).uses
        assert {row.derivation_id for row in one.rows} == {"area_row_ratio@1"}
        assert all(row.value == one.worked[row.area_id].value for row in one.rows)


@RECEIPTED
def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: dict[str, Share], before: dict[str, tuple[int, int]]
):
    assert made and Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
