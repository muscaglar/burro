"""Transport noise, worked out from the workbook its publisher gave.

Every other test of the measure runs on a made-up workbook. These read the
real one, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

The workbook was stored on 2026-09-23 with no receipt, and fetched again that
day for its receipt to be written. Where the folder of receipts holds none
for it, the step must refuse it, and one test here holds that. Where it holds
one, the others run.

They hold the count of rows read, the count of areas with a figure, and three
figures: London's lowest, middle and highest. None is said of a named area.
Each was worked out on 2026-09-24. Every figure is also worked out a second
way, by plain arithmetic, and held to the one the step gives.

Contains public sector information licensed under the Open Government Licence
v3.0. Source: Office for National Statistics licensed under the Open
Government Licence v.3.0.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
import statistics
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import noise
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.noise import Noise
from burro_pipeline.evidence.lock import LockError, read_receipts
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, held, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)
# The workbook, the lookup and the table of homes, by the ids of their receipts.
WORKBOOK, LOOKUP, HOMES = "f-cbc9ba7072bd", "f-49321b95f212", "f-af7b512615ea"


def has_a_receipt() -> bool:
    return RECEIPTS.is_dir() and any(
        receipt.source_id == noise.SOURCE for receipt in read_receipts(RECEIPTS)
    )


RECEIPTED = pytest.mark.skipif(not has_a_receipt(), reason="the workbook has no receipt")


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
def made(real: Inputs, found: Spine) -> Noise:
    return noise.build(real, found)


def values_of(made: Noise) -> list[float]:
    return sorted(one.value for one in made.worked.values() if one.value is not None)


# With no receipt


@pytest.mark.skipif(has_a_receipt(), reason="it has a receipt")
def test_the_workbook_is_not_read_while_it_has_no_receipt(tmp_path: Path):
    real = Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), tmp_path)
    found = spine.build(real)
    with pytest.raises(LockError) as stopped:
        noise.build(real, found)
    assert (stopped.value.rule, stopped.value.subject) == ("input_has_one_receipt", noise.SOURCE)
    assert all(opened.receipt.source_id != noise.SOURCE for opened in real.opened)


# The workbook


@RECEIPTED
def test_the_sheet_holds_as_many_rows_as_were_counted_and_none_lacks_a_share(made: Noise):
    assert made.sheet.file_id == WORKBOOK
    assert (made.sheet.rows, len(made.sheet.share), made.sheet.without) == (33_755, 33_755, ())
    assert noise.is_rounded(made.sheet)


@RECEIPTED
def test_the_period_and_the_census_are_read_from_the_file_and_agree_with_its_receipt(
    real: Inputs, made: Noise
):
    assert (made.sheet.year, made.geography) == ("2021", Geography.LSOA21)
    (receipt,) = [one.receipt for one in real.opened if one.receipt.source_id == noise.SOURCE]
    assert (receipt.edition, receipt.data_period) == ("2025", Period(as_at="2021"))


@RECEIPTED
def test_every_lsoa_of_london_has_a_share(made: Noise, found: Spine):
    assert all(lsoa in made.sheet.share for lsoa in found.lsoas)
    assert sum(one.units_used for one in made.worked.values()) == len(found.lsoas)
    assert all(one.units_used == one.units_expected for one in made.worked.values())


# The figures


@RECEIPTED
def test_every_area_has_a_figure_and_is_wholly_covered(made: Noise):
    assert len(made.worked) == 1_002
    assert len(values_of(made)) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {one.flags for one in made.worked.values()} == {(Flag.ROUNDED_IN_SOURCE,)}


@RECEIPTED
def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(made: Noise):
    values = values_of(made)
    assert (values[0], values[-1]) == (15.1, 100.0)
    # The middle of 1,002 figures lies between two of them.
    assert statistics.median(values) == pytest.approx(50.45)


@RECEIPTED
def test_no_figure_is_outside_what_a_percentage_can_be(made: Noise):
    assert all(0.0 <= value <= 100.0 for value in values_of(made))


@RECEIPTED
def test_every_figure_is_the_one_plain_arithmetic_gives(made: Noise, found: Spine):
    """Worked out a second way: in whole fractions, from the homes and the share of each LSOA.

    The file holds no total and no row for a larger area, so there is nothing
    of the publisher's to hold a figure to. This holds it to the sum instead.
    """
    homes: dict[str, int] = {}
    lsoas: dict[str, set[str]] = {}
    for cell in found.cells:
        homes[cell.lsoa] = homes.get(cell.lsoa, 0) + cell.homes
        lsoas.setdefault(spine.area_id_of(cell.msoa), set()).add(cell.lsoa)
    step = Decimal(1).scaleb(-noise.DECIMALS)
    for area, one in made.worked.items():
        # A share is written to three decimal places, so it is a whole number of thousandths.
        top = sum(homes[lsoa] * round(made.sheet.share[lsoa] * 1000) for lsoa in lsoas[area])
        percent = Fraction(top, 10 * sum(homes[lsoa] for lsoa in lsoas[area]))
        exact = Decimal(percent.numerator) / Decimal(percent.denominator)
        again = float(exact.quantize(step, rounding=ROUND_HALF_UP))
        assert one.value == again
        # A mean lies between the lowest and the highest of what it is taken over.
        lowest = 100 * min(made.sheet.share[lsoa] for lsoa in lsoas[area])
        highest = 100 * max(made.sheet.share[lsoa] for lsoa in lsoas[area])
        assert lowest - 0.05 <= again <= highest + 0.05


# The evidence


@RECEIPTED
def test_every_figure_rests_on_the_three_files_and_the_mean_by_homes(made: Noise):
    assert len(made.rows) == 1_002
    assert {row.inputs for row in made.rows} == {tuple(sorted([WORKBOOK, LOOKUP, HOMES]))}
    assert {row.derivation_id for row in made.rows} == {"lsoa_value_by_homes@1"}
    # From the start of the indicator's year to the end of the month of the lookup.
    span = Period(start="2021-01-01", end="2022-12-31")
    assert all(row.data_period == span for row in made.rows)
    assert {row.retrieved_on for row in made.rows} == {"2026-09-23"}
    assert all(row.value == made.worked[row.area_id].value for row in made.rows)
    assert Evidence.of("lon-2026-10-02-01", made.files, noise.METHODS, made.rows)


@RECEIPTED
def test_the_row_of_the_catalogue_names_the_year_and_every_source(made: Noise):
    assert (made.metric.vintage, made.metric.unit) == ("2021", "%")
    assert made.metric.source_ids == (
        "mhclg-iod-2025-underlying-indicators",
        "ons-census-2021-housing-tables",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    for source_id in made.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


@RECEIPTED
def test_the_measure_is_carried_now_that_core_no_longer_calls_it_a_share_of_homes(made: Noise):
    """The file counts residents. Core's name says no homes, and the sentence says residents."""
    assert made.metric.label == noise.LABEL
    assert "residents" in made.metric.definition
    assert says_what_core_says(made.metric)


@RECEIPTED
def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: Noise, before: dict[str, tuple[int, int]]
):
    copies = held(real.work)
    assert sorted(Path(name).parts[0] for name in copies) == sorted([WORKBOOK, LOOKUP, HOMES])
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
